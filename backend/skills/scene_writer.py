"""
SceneWriter Skill — the first AI writing skill.

Generates a SceneDocument from context (characters, world, style, scene plan).
"""

from __future__ import annotations
import json
import time
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.types import SkillManifest, ExecutionProfile
from skills.base import Skill, registry
from skills.providers import router
from prompts.builder import render_template
from database.models.canonical import (
    Scene, Character, World, Style, Novel,
)
from api.crud import update_scene
from api.schemas import SceneUpdate, SceneDocument, SceneBlock


SCENE_WRITER_MANIFEST = SkillManifest(
    name="SceneWriter",
    role="scene-writer",
    requires=["scene_plan"],
    knowledge=["character_state", "world_state", "rewrite_samples"],
    template="scene_writer.jinja2",
    constraints=[
        "输出必须是合法的 JSON blocks 数组",
        "禁止总结情绪，用动作和对话呈现",
        "每个 block 包含 type 和 content 字段",
    ],
)

SCENE_WRITER_PROFILE = ExecutionProfile(
    provider="openai",
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2048,
)


class SceneWriterSkill(Skill):
    manifest = SCENE_WRITER_MANIFEST

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = render_template(self.manifest.template, context)

        messages = [
            {
                "role": "system",
                "content": "你是专业小说家，严格按 JSON 格式输出场景内容。不要包含任何额外说明文字。",
            },
            {"role": "user", "content": prompt},
        ]

        start = time.time()
        response = await router.execute(messages, SCENE_WRITER_PROFILE)
        elapsed_ms = int((time.time() - start) * 1000)

        # Parse JSON from response
        blocks = self._validate_blocks(self._parse_blocks(response))

        return {
            "document": {"blocks": blocks},
            "provenance": {
                "execution_role": self.manifest.role,
                "execution_profile": SCENE_WRITER_PROFILE.model,
                "provider": SCENE_WRITER_PROFILE.provider,
                "model": SCENE_WRITER_PROFILE.model,
                "temperature": SCENE_WRITER_PROFILE.temperature,
                "tokens": 0,
                "duration_ms": elapsed_ms,
                "version": "1",
                "status": "completed",
            },
        }

    def _parse_blocks(self, response: str) -> list[dict]:
        """Extract blocks from LLM response, handling JSON in markdown fences."""
        # Try to find JSON block
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()

        # Try parsing as {"blocks": [...]} first
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "blocks" in data:
                return data["blocks"]
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # Fallback: wrap entire response as a narration block
        return [{"type": "narration", "content": response.strip()}]

    def _validate_blocks(self, blocks: list[dict]) -> list[dict]:
        """Ensure each block has required fields and valid types."""
        valid_types = {
            "narration", "dialogue", "description", "inner_monologue",
            "emotion", "letter", "phone_message", "flashback", "system_message",
        }
        import uuid
        validated = []
        for b in blocks:
            if not isinstance(b, dict):
                continue
            block_type = b.get("type", "narration")
            if block_type not in valid_types:
                block_type = "narration"
            validated.append({
                "id": b.get("id", str(uuid.uuid4())),
                "type": block_type,
                "content": b.get("content", ""),
                "metadata": b.get("metadata", {}),
            })
        return validated


# Register the skill
scene_writer = SceneWriterSkill()
registry.register(scene_writer)


async def build_scene_writer_context(
    db: AsyncSession,
    scene: Scene,
) -> dict[str, Any]:
    """Assemble context for SceneWriter from the database."""
    context: dict[str, Any] = {}

    # Scene planning
    planning = scene.planning or {}
    context["goal"] = planning.get("goal", "")
    context["conflict"] = planning.get("conflict", "")
    context["stakes"] = planning.get("stakes", "")

    # Chapter's novel
    chapter = await db.execute(
        select(Scene).where(Scene.id == scene.id)
    )
    scene_with_chapter = await db.get(Scene, scene.id)
    if scene_with_chapter is None:
        return context

    # Get novel from chapter
    from database.models.canonical import Chapter
    chapter_obj = await db.get(Chapter, scene_with_chapter.chapter_id)
    if chapter_obj is None:
        return context

    novel_id = chapter_obj.novel_id

    # Characters
    chars_result = await db.execute(
        select(Character).where(Character.novel_id == novel_id)
    )
    characters = chars_result.scalars().all()
    context["characters"] = [
        {
            "name": c.name,
            "age": c.age,
            "personality": c.personality or [],
            "goal": c.goal,
            "speech_style": c.speech_style,
        }
        for c in characters
    ]

    # Worlds
    worlds_result = await db.execute(
        select(World).where(World.novel_id == novel_id)
    )
    worlds = worlds_result.scalars().all()
    world_parts = []
    for w in worlds:
        parts = [f"### {w.name}"]
        for key, val in (w.config or {}).items():
            parts.append(f"{key}: {val}")
        world_parts.append("\n".join(parts))
    context["world_context"] = "\n\n".join(world_parts) if world_parts else "现代都市"

    # Style
    styles_result = await db.execute(
        select(Style).where(Style.novel_id == novel_id)
    )
    styles = styles_result.scalars().all()
    if styles:
        context["style"] = json.dumps(styles[0].profile, ensure_ascii=False, indent=2)
    else:
        context["style"] = "现代网文风格，节奏明快"

    # Scene history (recent scenes from same chapter)
    scenes_result = await db.execute(
        select(Scene)
        .where(Scene.chapter_id == scene.chapter_id)
        .where(Scene.order < scene.order)
        .order_by(Scene.order.desc())
        .limit(3)
    )
    past_scenes = scenes_result.scalars().all()
    history_parts = []
    for ps in reversed(past_scenes):
        blocks = (ps.document or {}).get("blocks", [])
        summary = " ".join(b.get("content", "")[:100] for b in blocks[:3])
        if summary:
            history_parts.append(f"场景 {ps.order}: {summary}...")
    context["scene_history"] = "\n".join(history_parts) if history_parts else "这是第一个场景"

    # Rewrite samples (empty for now — will be populated in Phase 4)
    context["rewrite_samples"] = []

    return context