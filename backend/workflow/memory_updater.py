"""
ChapterMemoryUpdater — compresses raw chapter facts into readable summaries via LLM.

Reads chapter.chapter_facts (populated by FactsAggregator), calls the LLM to
compress the four raw-fact categories into human-readable summary strings, then
writes those summaries back into chapter.chapter_facts.
"""

from __future__ import annotations
import logging
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.canonical import Chapter
from skills.providers import router as provider_router
from skills.profile_registry import profile_registry
from skills.parsing import parse_json_from_markdown
from prompts.builder import render_template

logger = logging.getLogger(__name__)

# Fact categories aggregated by FactsAggregator
FACT_TYPES = [
    "relationship_changes",
    "world_changes",
    "timeline_changes",
    "new_information",
]

# Keys written back into chapter.chapter_facts (same as fact types per spec)
SUMMARY_KEYS = [
    "relationship_changes",
    "world_changes",
    "timeline_changes",
    "new_information",
]


async def run_memory_updater(
    db: AsyncSession,
    chapter_id: str,
) -> dict[str, Any]:
    """Run the memory updater for a chapter.

    If chapter_facts is empty (no raw facts), this function returns early
    without calling the LLM. Otherwise, it calls the LLM to compress the
    four fact categories into readable summaries and writes them back to
    chapter.chapter_facts.

    Args:
        db: Database session.
        chapter_id: ID of the chapter to process.

    Returns:
        Dict with the four summary keys, or an empty dict if skipped.
    """
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        logger.warning("MemoryUpdater: chapter %s not found", chapter_id)
        return {}

    facts: dict[str, Any] = chapter.chapter_facts or {}

    # Check if there are any raw facts to process
    has_facts = any(
        bool(facts.get(ft))
        for ft in FACT_TYPES
    )
    if not has_facts:
        logger.info(
            "MemoryUpdater: chapter %s has no facts — skipping LLM call", chapter_id
        )
        return {}

    # Build template context
    context = {
        "chapter_id": chapter_id,
        "relationship_changes": facts.get("relationship_changes", []),
        "world_changes": facts.get("world_changes", []),
        "timeline_changes": facts.get("timeline_changes", []),
        "new_information": facts.get("new_information", []),
    }

    prompt = render_template("memory_updater.jinja2", context)

    messages = [
        {
            "role": "system",
            "content": (
                "你是专业小说编辑，负责将原始事实条目压缩为简洁可读的中文摘要。"
                "严格按 JSON 格式输出，不要包含任何额外说明文字。"
            ),
        },
        {"role": "user", "content": prompt},
    ]

    profile = profile_registry.get("memory-updater")

    start = time.time()
    response = await provider_router.execute(messages, profile)
    elapsed_ms = int((time.time() - start) * 1000)

    logger.info(
        "MemoryUpdater: chapter %s LLM responded in %d ms",
        chapter_id,
        elapsed_ms,
    )

    # Parse the JSON response
    parsed = parse_json_from_markdown(response)

    summaries: dict[str, str] = {}
    for key in SUMMARY_KEYS:
        summaries[key] = str(parsed.get(key, ""))

    # Merge summaries back into chapter.chapter_facts
    updated_facts = dict(facts)
    updated_facts.update(summaries)
    chapter.chapter_facts = updated_facts

    await db.commit()
    await db.refresh(chapter)

    return summaries
