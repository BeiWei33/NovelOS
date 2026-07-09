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

from core.types import SkillManifest, ExecutionProfile
from skills.base import Skill, registry
from skills.providers import router
from prompts.builder import render_template
from database.models.canonical import Scene, Character, World, Style, Chapter


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

STORY_PLANNER_PROFILE = ExecutionProfile(
    provider="openai",
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2048,
)


class StoryPlannerSkill(Skill):
    manifest = STORY_PLANNER_MANIFEST

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = render_template(self.manifest.template, context)

        messages = [
            {
                "role": "system",
                "content": "你是资深小说结构师，擅长设计场景节奏和情节点。输出 JSON 格式的场景规划。",
            },
            {"role": "user", "content": prompt},
        ]

        start = time.time()
        response = await router.execute(messages, STORY_PLANNER_PROFILE)
        elapsed_ms = int((time.time() - start) * 1000)

        scene_plan = self._parse_scene_plan(response)

        return {
            "scene_plan": scene_plan,
            "provenance": {
                "execution_role": self.manifest.role,
                "provider": STORY_PLANNER_PROFILE.provider,
                "model": STORY_PLANNER_PROFILE.model,
                "temperature": STORY_PLANNER_PROFILE.temperature,
                "tokens": 0,
                "duration_ms": elapsed_ms,
            },
        }

    def _parse_scene_plan(self, response: str) -> list[dict]:
        """Parse scene plan from LLM response."""
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()

        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "scene_plan" in data:
                return data["scene_plan"]
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        return []


# Register
story_planner = StoryPlannerSkill()
registry.register(story_planner)


async def build_story_planner_context(
    db: AsyncSession,
    chapter_id: str,
    goal: str = "",
    theme: str = "",
) -> dict[str, Any]:
    """Assemble context for StoryPlanner."""
    context: dict[str, Any] = {
        "goal": goal,
        "theme": theme,
    }

    # Get chapter
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        return context

    novel_id = chapter.novel_id

    # Characters
    chars_result = await db.execute(
        select(Character).where(Character.novel_id == novel_id)
    )
    characters = chars_result.scalars().all()
    context["characters"] = [
        {
            "name": c.name,
            "goal": c.goal,
            "fear": c.fear,
        }
        for c in characters
    ]

    # World
    worlds_result = await db.execute(
        select(World).where(World.novel_id == novel_id)
    )
    worlds = worlds_result.scalars().all()
    world_parts = []
    for w in worlds:
        world_parts.append(f"{w.name}: {json.dumps(w.config, ensure_ascii=False)}")
    context["world_state"] = "\n".join(world_parts) if world_parts else "现代都市"

    # Existing scenes in chapter
    scenes_result = await db.execute(
        select(Scene).where(Scene.chapter_id == chapter_id).order_by(Scene.order)
    )
    existing_scenes = scenes_result.scalars().all()
    context["existing_scene_count"] = len(existing_scenes)
    context["existing_scenes"] = [
        {"order": s.order, "goal": s.planning.get("goal", "")}
        for s in existing_scenes
        if s.planning
    ]

    return context