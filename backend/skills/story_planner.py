"""
StoryPlanner Skill — plans scene structure before writing.

输入：goal + theme
输出：scene_plan: [{goal, conflict, stakes, turning_point, ending, foreshadow}]
"""

from __future__ import annotations
import json
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.types import SkillManifest
from skills.base import Skill, registry
from skills.providers import router
from skills.profile_registry import profile_registry
from skills.parsing import parse_list_from_response
from prompts.builder import render_template
from database.models.canonical import (
    Scene, Character, World, Style, Chapter, NarrativeEvent,
)
from knowledge.retrievers import KnowledgeEngine


STORY_PLANNER_MANIFEST = SkillManifest(
    name="StoryPlanner",
    role="story-planner",
    requires=["goal", "theme"],
    knowledge=["character_state", "world_state", "scene_history"],
    template="story_planner.jinja2",
    constraints=[
        "输出必须是 scene_plan 数组",
        "每个 scene 包含 goal, conflict, stakes, turning_point, ending, foreshadow",
        "场景数不超过 10 个",
    ],
)


class StoryPlannerSkill(Skill):
    manifest = STORY_PLANNER_MANIFEST

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        profile = profile_registry.get(self.manifest.role)
        prompt = render_template(self.manifest.template, context)

        messages = [
            {
                "role": "system",
                "content": "你是资深小说结构师，擅长设计场景节奏和情节点。输出 JSON 格式的场景规划。",
            },
            {"role": "user", "content": prompt},
        ]

        start = time.time()
        response = await router.execute(messages, profile)
        elapsed_ms = int((time.time() - start) * 1000)

        scene_plan = parse_list_from_response(response, "scene_plan")

        return {
            "scene_plan": scene_plan,
            "provenance": {
                "execution_role": self.manifest.role,
                "provider": profile.provider,
                "model": profile.model,
                "temperature": profile.temperature,
                "tokens": 0,
                "duration_ms": elapsed_ms,
            },
        }


# Register
story_planner = StoryPlannerSkill()
registry.register(story_planner)


async def build_story_planner_context(
    db: AsyncSession,
    chapter_id: str,
    goal: str = "",
    theme: str = "",
) -> dict[str, Any]:
    """Assemble context for StoryPlanner.

    Returns a standardized context dict with:
      goal, theme, chapter_summary, characters, world_state, recent_events
    """
    context: dict[str, Any] = {
        "goal": goal,
        "theme": theme,
    }

    # Get chapter
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        return context

    novel_id = chapter.novel_id

    # Chapter summary from planning / summary fields
    planning = chapter.planning or {}
    summary = chapter.summary or {}
    context["chapter_summary"] = (
        summary.get("one_paragraph", "")
        or summary.get("one_line", "")
        or planning.get("goal", "")
        or ""
    )

    # ── Characters: canonical data + Knowledge Layer projections ──
    chars_result = await db.execute(
        select(Character).where(Character.novel_id == novel_id)
    )
    characters = chars_result.scalars().all()

    # Fetch character_state from Knowledge Layer
    engine = KnowledgeEngine(db)
    char_knowledge = await engine.retrieve(
        knowledge_types=["character_state"],
        novel_id=novel_id,
    )
    # Build lookup: character_id -> {state, arc_summary}
    char_state_map: dict[str, dict[str, Any]] = {}
    for obj in char_knowledge.get("character_state", []):
        cid = obj.payload.get("character", "")
        char_state_map[cid] = {
            "state": obj.payload.get("state", {}),
            "arc_summary": obj.payload.get("arc", ""),
        }

    context["characters"] = [
        {
            "name": c.name,
            "state": char_state_map.get(c.name, {}).get("state", {}),
            "arc_summary": char_state_map.get(c.name, {}).get("arc_summary", ""),
        }
        for c in characters
    ]

    # ── World state: canonical data as structured key facts ──
    worlds_result = await db.execute(
        select(World).where(World.novel_id == novel_id)
    )
    worlds = worlds_result.scalars().all()
    world_facts: list[dict[str, Any]] = []
    for w in worlds:
        config = w.config or {}
        for key, val in config.items():
            world_facts.append({"world": w.name, "key": key, "value": val})
    context["world_state"] = world_facts if world_facts else [{"key": "default", "value": "现代都市"}]

    # ── Recent events: NarrativeEvent from scenes in this chapter ──
    scenes_result = await db.execute(
        select(Scene).where(Scene.chapter_id == chapter_id).order_by(Scene.order)
    )
    chapter_scenes = scenes_result.scalars().all()
    scene_ids = [s.id for s in chapter_scenes]

    recent_events: list[dict[str, Any]] = []
    if scene_ids:
        events_result = await db.execute(
            select(NarrativeEvent)
            .where(NarrativeEvent.scene_id.in_(scene_ids))
            .order_by(NarrativeEvent.sequence)
            .limit(20)
        )
        events = events_result.scalars().all()
        recent_events = [
            {
                "type": e.type,
                "actor": e.actor,
                "summary": (e.payload or {}).get("content_preview", ""),
            }
            for e in events
        ]
    context["recent_events"] = recent_events

    # ── Existing scenes in chapter (for template) ──
    context["existing_scene_count"] = len(chapter_scenes)
    context["existing_scenes"] = [
        {"order": s.order, "goal": (s.planning or {}).get("goal", "")}
        for s in chapter_scenes
        if s.planning
    ]

    return context