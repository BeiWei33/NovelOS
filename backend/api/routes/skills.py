"""Skill execution routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from database.models.canonical import Scene, Chapter
from skills.base import registry
from skills.scene_writer import build_scene_writer_context
from skills.consistency_checker import build_consistency_checker_context
from skills.story_planner import build_story_planner_context
from core.types import ScenePipelineResult
from api.crud import update_scene
from api.schemas import SceneUpdate, SceneDocument, ScenePlanningInput
from workflow.quality_pipeline import run_quality_pipeline, apply_patches
from workflow.chapter_workflow import run_chapter_workflow


router = APIRouter(prefix="/skills", tags=["skills"])


@router.post("/scene-writer/{scene_id}")
async def run_scene_writer(
    scene_id: str,
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
    scene.body_history["quality_issues"] = result.get("issues", [])
    scene.body_history["quality_patches_applied"] = len(patches)
    scene.body_history["quality_editor"] = result.get("editor_provenance", {})
    scene.body_history["quality_checker"] = result.get("checker_provenance", {})

    await db.commit()
    await db.refresh(scene)

    return {
        "scene_id": scene.id,
        "version": scene.version,
        "patches_applied": len(patches),
        "patches": patches,
        "issues": result.get("issues", []),
        "issues_count": len(result.get("issues", [])),
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


@router.post("/generate-chapter/{chapter_id}")
async def generate_chapter(
    chapter_id: str,
    data: ScenePlanningInput,
    db: AsyncSession = Depends(get_session),
):
    """Run full chapter workflow: plan → write scenes → quality → artifacts → summary."""
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