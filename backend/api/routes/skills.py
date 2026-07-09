"""Skill execution routes."""

from dataclasses import replace

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from database.models.canonical import Scene, Chapter
from skills.base import registry
from skills.scene_writer import build_scene_writer_context
from skills.consistency_checker import build_consistency_checker_context
from skills.story_planner import build_story_planner_context
from skills.providers import router as provider_router
from skills.profile_registry import profile_registry
from core.types import ScenePipelineResult, ExecutionProfile
from api.crud import update_scene
from api.schemas import (
    SceneUpdate, SceneDocument, ScenePlanningInput,
    ProfileOverride, ProviderInfo, ProfileInfo,
)
from workflow.quality_pipeline import run_quality_pipeline, apply_patches
from workflow.chapter_workflow import run_chapter_workflow
from workflow.facts_aggregator import run_facts_aggregator
from workflow.memory_updater import run_memory_updater


router = APIRouter(prefix="/skills", tags=["skills"])


def _apply_profile_override(role: str, override: ProfileOverride) -> ExecutionProfile:
    """Create a profile with runtime overrides applied.

    Returns a new ExecutionProfile without mutating global state.
    """
    base_profile = profile_registry.get(role)
    overrides = {}
    if override.provider is not None:
        overrides["provider"] = override.provider
    if override.model is not None:
        overrides["model"] = override.model
    if override.temperature is not None:
        overrides["temperature"] = override.temperature
    if override.max_tokens is not None:
        overrides["max_tokens"] = override.max_tokens
    if overrides:
        return replace(base_profile, **overrides)
    return base_profile


@router.get("/providers")
async def list_providers():
    """List all registered LLM providers."""
    providers = []
    for name in provider_router.list_providers():
        config = provider_router.get_config(name)
        if config:
            providers.append(ProviderInfo(
                name=name,
                default_model=config.default_model,
                default_max_tokens=config.default_max_tokens,
            ))
    return {"providers": providers}


@router.get("/profiles")
async def list_profiles():
    """List all execution profiles."""
    profiles = []
    for role in profile_registry.list_profiles():
        profile = profile_registry.get(role)
        profiles.append(ProfileInfo(
            role=role,
            provider=profile.provider,
            model=profile.model,
            temperature=profile.temperature,
            max_tokens=profile.max_tokens,
        ))
    return {"profiles": profiles}


@router.post("/scene-writer/{scene_id}")
async def run_scene_writer(
    scene_id: str,
    profile_override: ProfileOverride | None = None,
    db: AsyncSession = Depends(get_session),
):
    """Execute SceneWriter skill on a scene. Assembles context, calls LLM, writes result."""
    # Get scene
    scene = await db.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    # Get skill
    skill = registry.get("SceneWriter")
    if skill is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SceneWriter skill not registered")

    # Apply profile override if provided
    if profile_override:
        context["_profile_override"] = _apply_profile_override(
            skill.manifest.role, profile_override
        )

    # Build context
    context = await build_scene_writer_context(db, scene)

    # Execute
    result = await skill.execute(context)

    # Write result back to scene
    document = result.get("document", {"blocks": []})
    provenance = result.get("provenance", {})

    scene.document = document
    scene.version += 1
    scene.provenance = provenance
    scene.body_history = scene.body_history or {}
    scene.body_history["edited"] = document

    await db.commit()
    await db.refresh(scene)

    return {
        "scene_id": scene.id,
        "version": scene.version,
        "document": scene.document,
        "provenance": scene.provenance,
    }


@router.post("/polish/{scene_id}")
async def run_polish(
    scene_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Execute quality pipeline: SceneEditor (去AI味) → ConsistencyChecker."""
    from workflow.consistency_score import calculate_consistency_score, get_consistency_level

    scene = await db.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    # Run the quality pipeline
    result = await run_quality_pipeline(db, scene)

    # Apply patches to document
    patches = result.get("patches", [])
    if patches:
        updated_doc = apply_patches(scene.document or {"blocks": []}, patches)
        scene.document = updated_doc
        scene.version += 1
        scene.body_history = scene.body_history or {}
        scene.body_history["polished"] = updated_doc

    # Store quality check results in scene
    scene.body_history = scene.body_history or {}
    issues = result.get("issues", [])
    scene.body_history["quality_issues"] = issues
    scene.body_history["quality_patches_applied"] = len(patches)
    scene.body_history["quality_editor"] = result.get("editor_provenance", {})
    scene.body_history["quality_checker"] = result.get("checker_provenance", {})

    # Calculate consistency score
    score = calculate_consistency_score(issues)
    scene.body_history["consistency_score"] = score

    await db.commit()
    await db.refresh(scene)

    return {
        "scene_id": scene.id,
        "version": scene.version,
        "patches_applied": len(patches),
        "patches": patches,
        "issues": issues,
        "issues_count": len(issues),
        "consistency_score": score,
    }


@router.post("/plan-scene/{scene_id}")
async def plan_single_scene(
    scene_id: str,
    data: ScenePlanningInput,
    db: AsyncSession = Depends(get_session),
):
    """Plan a single scene using StoryPlanner."""
    scene = await db.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    skill = registry.get("StoryPlanner")
    if skill is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="StoryPlanner not registered")

    context = await build_story_planner_context(
        db,
        scene.chapter_id,
        goal=data.goal or "",
        theme=data.theme or "",
    )

    result = await skill.execute(context)
    scene_plan = result.get("scene_plan", [])

    # Apply first plan to scene's planning field
    if scene_plan:
        plan = scene_plan[0]
        scene.planning = {
            "goal": plan.get("goal", ""),
            "conflict": plan.get("conflict", ""),
            "stakes": plan.get("stakes", ""),
            "turning_point": plan.get("turning_point", ""),
            "ending": plan.get("ending", ""),
            "foreshadow": plan.get("foreshadow", ""),
        }
        await db.commit()
        await db.refresh(scene)

    return {
        "scene_id": scene.id,
        "scene_plan": scene_plan,
        "applied": len(scene_plan) > 0,
        "provenance": result.get("provenance", {}),
    }


@router.post("/plan-chapter/{chapter_id}")
async def plan_chapter(
    chapter_id: str,
    data: ScenePlanningInput,
    db: AsyncSession = Depends(get_session),
):
    """Plan all scenes for a chapter using StoryPlanner."""
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    skill = registry.get("StoryPlanner")
    if skill is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="StoryPlanner not registered")

    context = await build_story_planner_context(
        db,
        chapter_id,
        goal=data.goal or "",
        theme=data.theme or "",
    )

    result = await skill.execute(context)
    scene_plan = result.get("scene_plan", [])

    # Store in chapter's planning
    chapter.planning = chapter.planning or {}
    chapter.planning["scene_plan"] = scene_plan
    chapter.planning["goal"] = data.goal or ""
    chapter.planning["theme"] = data.theme or ""

    await db.commit()
    await db.refresh(chapter)

    return {
        "chapter_id": chapter.id,
        "scene_count": len(scene_plan),
        "scene_plan": scene_plan,
        "provenance": result.get("provenance", {}),
    }


@router.post("/summarize-chapter/{chapter_id}")
async def summarize_chapter(
    chapter_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Regenerate chapter summary using LLM."""
    from skills.chapter_summarizer import build_chapter_summarizer_context

    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    skill = registry.get("ChapterSummarizer")
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ChapterSummarizer not registered"
        )

    context = await build_chapter_summarizer_context(db, chapter)
    result = await skill.execute(context)

    chapter.summary = result.get("summary", {})
    await db.commit()
    await db.refresh(chapter)

    return {
        "chapter_id": chapter.id,
        "summary": chapter.summary,
        "provenance": result.get("provenance", {}),
    }


@router.post("/generate-chapter/{chapter_id}")
async def generate_chapter(
    chapter_id: str,
    data: ScenePlanningInput,
    db: AsyncSession = Depends(get_session),
):
    """Run full chapter workflow: plan → write scenes → quality → artifacts → facts → summary."""
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    result = await run_chapter_workflow(db, chapter_id, data.goal or "", data.theme or "")

    await db.refresh(chapter)

    return {
        "chapter_id": chapter.id,
        "title": chapter.title,
        "workflow": result,
        "summary": chapter.summary,
        "scene_count": len(chapter.scenes) if hasattr(chapter, "scenes") else 0,
        "planning": chapter.planning,
    }


@router.post("/aggregate-facts/{chapter_id}")
async def aggregate_facts(
    chapter_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Aggregate facts from all scene artifacts in a chapter.

    Reads scene_artifact.facts for each scene, groups by fact_type,
    deduplicates by (actor, target), and writes to chapter.chapter_facts.
    """
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    facts = await run_facts_aggregator(db, chapter_id)

    await db.refresh(chapter)

    return {
        "chapter_id": chapter_id,
        "chapter_facts": facts,
        "counts": {
            fact_type: len(items)
            for fact_type, items in facts.items()
        },
    }


@router.post("/update-memory/{chapter_id}")
async def update_memory(
    chapter_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Compress aggregated chapter facts into readable summaries via LLM.

    Reads chapter.chapter_facts (populated by aggregate-facts), calls the
    memory-updater LLM profile to produce four summary strings, and writes
    them back into chapter.chapter_facts.  If chapter_facts is empty the
    LLM is skipped and an empty result is returned.
    """
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    summaries = await run_memory_updater(db, chapter_id)

    await db.refresh(chapter)

    return {
        "chapter_id": chapter_id,
        "summaries": summaries,
        "skipped": len(summaries) == 0,
    }