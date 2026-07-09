"""
ConsistencyChecker Skill — 检查场景内容的一致性。

检查人物年龄/名字/标签是否错误、时间线是否冲突、世界观规则是否违反。
输出 issues 列表 + 自动修复建议。
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
from database.models.canonical import Character, World


CONSISTENCY_CHECKER_MANIFEST = SkillManifest(
    name="ConsistencyChecker",
    role="consistency-checker",
    requires=["scene_document"],
    knowledge=["character_state", "timeline", "facts"],
    template="consistency_checker.jinja2",
    constraints=[
        "输出必须是 issues 列表",
        "每个 issue 包含 type、severity、description、location、fix_suggestion",
        "severity: error（必须修复）/ warning（建议修复）",
    ],
)


class ConsistencyCheckerSkill(Skill):
    manifest = CONSISTENCY_CHECKER_MANIFEST

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        profile = profile_registry.get(self.manifest.role)
        prompt = render_template(self.manifest.template, {
            "document": json.dumps(context.get("document", {"blocks": []}), ensure_ascii=False),
            "characters": context.get("characters", []),
            "world_rules": context.get("world_rules", []),
            "timeline": context.get("timeline", []),
        })

        messages = [
            {
                "role": "system",
                "content": "你是小说一致性审核员，检查人物、时间线、世界观的一致性。输出问题列表，每项含严重程度和修复建议。",
            },
            {"role": "user", "content": prompt},
        ]

        start = time.time()
        response = await router.execute(messages, profile)
        elapsed_ms = int((time.time() - start) * 1000)

        issues = parse_list_from_response(response, "issues")

        return {
            "issues": issues,
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
consistency_checker = ConsistencyCheckerSkill()
registry.register(consistency_checker)


async def build_consistency_checker_context(
    db: AsyncSession,
    scene_id: str,
) -> dict[str, Any]:
    """Assemble context for ConsistencyChecker from database."""
    from database.models.canonical import Scene, Chapter

    context: dict[str, Any] = {}

    # Get scene
    scene = await db.get(Scene, scene_id)
    if scene is None:
        return context

    context["document"] = scene.document or {"blocks": []}

    # Get chapter -> novel_id
    chapter = await db.get(Chapter, scene.chapter_id)
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
            "age": c.age,
            "occupation": c.occupation,
            "personality": c.personality or [],
        }
        for c in characters
    ]
    context["character_names"] = [c.name for c in characters]

    # World rules
    worlds_result = await db.execute(
        select(World).where(World.novel_id == novel_id)
    )
    worlds = worlds_result.scalars().all()
    rules = []
    for w in worlds:
        config = w.config or {}
        if "rules" in config:
            rules.extend(config["rules"])
    context["world_rules"] = rules

    # Timeline (simplified — from earlier scenes)
    scenes_result = await db.execute(
        select(Scene)
        .where(Scene.chapter_id == scene.chapter_id)
        .where(Scene.order < scene.order)
        .order_by(Scene.order.desc())
        .limit(5)
    )
    past_scenes = scenes_result.scalars().all()
    timeline = []
    for ps in reversed(past_scenes):
        doc = ps.document or {}
        blocks = doc.get("blocks", [])
        if blocks:
            first_content = blocks[0].get("content", "")[:100]
            timeline.append(f"场景 {ps.order}: {first_content}")
    context["timeline"] = timeline

    return context