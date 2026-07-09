"""
Chapter Summarizer Skill — generates three-level summaries via LLM.

Replaces simple concatenation with intelligent summarization.
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
from skills.profile_registry import profile_registry
from prompts.builder import render_template
from database.models.canonical import Scene, Chapter
from skills.parsing import parse_json_from_markdown


CHAPTER_SUMMARIZER_MANIFEST = SkillManifest(
    name="ChapterSummarizer",
    role="chapter-summarizer",
    requires=["scenes"],
    knowledge=[],
    template="chapter_summarizer.jinja2",
    constraints=[
        "输出必须是合法的 JSON 对象",
        "one_line: 20-50 字的一句话概括",
        "one_paragraph: 100-200 字的一段话概述",
        "one_page: 500-800 字的完整章节摘要",
    ],
)


class ChapterSummarizerSkill(Skill):
    manifest = CHAPTER_SUMMARIZER_MANIFEST

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        # Check for runtime profile override
        if "_profile_override" in context:
            profile = context["_profile_override"]
        else:
            profile = profile_registry.get(self.manifest.role)

        prompt = render_template(self.manifest.template, context)

        messages = [
            {
                "role": "system",
                "content": "你是专业小说编辑，擅长提炼章节精华。严格按 JSON 格式输出。",
            },
            {"role": "user", "content": prompt},
        ]

        start = time.time()
        response = await router.execute(messages, profile)
        elapsed_ms = int((time.time() - start) * 1000)

        # Parse JSON from response
        summary = parse_json_from_markdown(response)

        # Validate and normalize output
        result = {
            "one_line": self._truncate(summary.get("one_line", ""), 50),
            "one_paragraph": self._truncate(summary.get("one_paragraph", ""), 200),
            "one_page": self._truncate(summary.get("one_page", ""), 800),
        }

        return {
            "summary": result,
            "provenance": {
                "execution_role": self.manifest.role,
                "provider": profile.provider,
                "model": profile.model,
                "temperature": profile.temperature,
                "tokens": 0,
                "duration_ms": elapsed_ms,
            },
        }

    def _truncate(self, text: str, max_chars: int) -> str:
        """Truncate text to max characters, preserving word boundaries."""
        if len(text) <= max_chars:
            return text
        # Try to truncate at a sentence boundary
        truncated = text[:max_chars]
        last_period = truncated.rfind("。")
        last_exclaim = truncated.rfind("！")
        last_question = truncated.rfind("？")
        last_sentence = max(last_period, last_exclaim, last_question)
        if last_sentence > max_chars * 0.7:
            return truncated[: last_sentence + 1]
        return truncated


def build_chapter_summarizer_context(
    db: AsyncSession,
    chapter: Chapter,
) -> dict[str, Any]:
    """Build context for ChapterSummarizer skill."""
    # Get all scenes for the chapter
    scenes_result = db.execute(
        select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.order)
    )
    scenes = list(scenes_result.scalars().all())

    # Build scene summaries
    scene_summaries = []
    for scene in scenes:
        doc = scene.document or {}
        blocks = doc.get("blocks", [])
        content_parts = []
        for block in blocks:
            content = block.get("content", "")
            if content:
                content_parts.append(content)

        scene_summaries.append({
            "order": scene.order,
            "planning": scene.planning or {},
            "content": "\n".join(content_parts)[:2000],  # Limit per-scene content
        })

    return {
        "chapter_title": chapter.title,
        "scene_count": len(scenes),
        "scenes": scene_summaries,
    }


# Register skill
registry.register(ChapterSummarizerSkill())