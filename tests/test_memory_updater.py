"""
Unit tests for ChapterMemoryUpdater — no DB, no LLM required.

Tests cover:
- Empty chapter_facts → LLM is not called
- Return value format when LLM is called
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_chapter(facts: dict):
    """Return a minimal mock Chapter with chapter_facts set."""
    chapter = MagicMock()
    chapter.chapter_facts = facts
    return chapter


def _make_db(chapter):
    """Return a minimal async mock DB session."""
    db = AsyncMock()
    db.get = AsyncMock(return_value=chapter)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ─── Tests: empty facts → skip LLM ───────────────────────────────────────────

class TestEmptyFacts:
    """run_memory_updater skips the LLM when chapter_facts contains no items."""

    @pytest.mark.asyncio
    async def test_none_chapter_facts_skips_llm(self):
        """chapter_facts is None → LLM not called, returns {}."""
        chapter = _make_chapter(None)
        db = _make_db(chapter)

        with patch("workflow.memory_updater.provider_router.execute") as mock_llm:
            from workflow.memory_updater import run_memory_updater
            result = await run_memory_updater(db, "chapter-1")

        mock_llm.assert_not_called()
        assert result == {}

    @pytest.mark.asyncio
    async def test_empty_dict_chapter_facts_skips_llm(self):
        """chapter_facts is {} → LLM not called."""
        chapter = _make_chapter({})
        db = _make_db(chapter)

        with patch("workflow.memory_updater.provider_router.execute") as mock_llm:
            from workflow.memory_updater import run_memory_updater
            result = await run_memory_updater(db, "chapter-1")

        mock_llm.assert_not_called()
        assert result == {}

    @pytest.mark.asyncio
    async def test_all_empty_lists_skips_llm(self):
        """chapter_facts has all four keys but all are empty lists → LLM not called."""
        chapter = _make_chapter({
            "relationship_changes": [],
            "world_changes": [],
            "timeline_changes": [],
            "new_information": [],
        })
        db = _make_db(chapter)

        with patch("workflow.memory_updater.provider_router.execute") as mock_llm:
            from workflow.memory_updater import run_memory_updater
            result = await run_memory_updater(db, "chapter-1")

        mock_llm.assert_not_called()
        assert result == {}

    @pytest.mark.asyncio
    async def test_chapter_not_found_returns_empty(self):
        """If chapter does not exist in DB, returns {} without error."""
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        with patch("workflow.memory_updater.provider_router.execute") as mock_llm:
            from workflow.memory_updater import run_memory_updater
            result = await run_memory_updater(db, "nonexistent-id")

        mock_llm.assert_not_called()
        assert result == {}


# ─── Tests: non-empty facts → LLM called, result validated ───────────────────

_SAMPLE_LLM_RESPONSE = """```json
{
  "relationship_changes": "Alice 与 Bob 的关系由盟友转为对立。",
  "world_changes": "北方城市被摧毁，战争阴云笼罩全国。",
  "timeline_changes": "故事时间推进了三天，进入第七章节。",
  "new_information": "Bob 被揭露为卧底特工。"
}
```"""


class TestReturnValueFormat:
    """When LLM is called, return value has the four expected summary keys."""

    @pytest.mark.asyncio
    async def test_returns_four_summary_keys(self):
        """Result dict contains all four summary keys."""
        chapter = _make_chapter({
            "relationship_changes": [{"actor": "Alice", "target": "Bob", "fact_type": "relationship_changes"}],
        })
        db = _make_db(chapter)

        with patch("workflow.memory_updater.provider_router.execute", new_callable=AsyncMock) as mock_llm, \
             patch("workflow.memory_updater.render_template", return_value="prompt text"):
            mock_llm.return_value = _SAMPLE_LLM_RESPONSE
            from workflow.memory_updater import run_memory_updater
            result = await run_memory_updater(db, "chapter-42")

        assert "relationship_changes" in result
        assert "world_changes" in result
        assert "timeline_changes" in result
        assert "new_information" in result

    @pytest.mark.asyncio
    async def test_summary_values_are_strings(self):
        """Every summary value is a string (not None or other type)."""
        chapter = _make_chapter({
            "new_information": [{"actor": "Bob", "target": "", "fact_type": "new_information"}],
        })
        db = _make_db(chapter)

        with patch("workflow.memory_updater.provider_router.execute", new_callable=AsyncMock) as mock_llm, \
             patch("workflow.memory_updater.render_template", return_value="prompt text"):
            mock_llm.return_value = _SAMPLE_LLM_RESPONSE
            from workflow.memory_updater import run_memory_updater
            result = await run_memory_updater(db, "chapter-42")

        for key in [
            "relationship_changes",
            "world_changes",
            "timeline_changes",
            "new_information",
        ]:
            assert isinstance(result[key], str), f"{key} should be str, got {type(result[key])}"

    @pytest.mark.asyncio
    async def test_llm_called_exactly_once(self):
        """LLM execute() is called exactly once per invocation."""
        chapter = _make_chapter({
            "world_changes": [{"actor": "city", "target": "", "fact_type": "world_changes"}],
        })
        db = _make_db(chapter)

        with patch("workflow.memory_updater.provider_router.execute", new_callable=AsyncMock) as mock_llm, \
             patch("workflow.memory_updater.render_template", return_value="prompt"):
            mock_llm.return_value = _SAMPLE_LLM_RESPONSE
            from workflow.memory_updater import run_memory_updater
            await run_memory_updater(db, "chapter-99")

        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_chapter_facts_updated_in_db(self):
        """The chapter.chapter_facts dict is updated with the new summaries."""
        raw_facts = {
            "relationship_changes": [{"actor": "A", "target": "B", "fact_type": "relationship_changes"}],
            "world_changes": [],
            "timeline_changes": [],
            "new_information": [],
        }
        chapter = _make_chapter(raw_facts)
        db = _make_db(chapter)

        with patch("workflow.memory_updater.provider_router.execute", new_callable=AsyncMock) as mock_llm, \
             patch("workflow.memory_updater.render_template", return_value="prompt"):
            mock_llm.return_value = _SAMPLE_LLM_RESPONSE
            from workflow.memory_updater import run_memory_updater
            await run_memory_updater(db, "chapter-1")

        # chapter.chapter_facts should have been updated with summaries (same key names)
        assert "relationship_changes" in chapter.chapter_facts
        # The raw list should be replaced with summary string
        assert isinstance(chapter.chapter_facts["relationship_changes"], str)

    @pytest.mark.asyncio
    async def test_missing_summary_keys_default_to_empty_string(self):
        """If LLM omits some summary keys, they default to empty string."""
        incomplete_response = '{"relationship_changes": "some summary"}'
        chapter = _make_chapter({
            "relationship_changes": [{"actor": "X", "target": "Y", "fact_type": "relationship_changes"}],
        })
        db = _make_db(chapter)

        with patch("workflow.memory_updater.provider_router.execute", new_callable=AsyncMock) as mock_llm, \
             patch("workflow.memory_updater.render_template", return_value="prompt"):
            mock_llm.return_value = incomplete_response
            from workflow.memory_updater import run_memory_updater
            result = await run_memory_updater(db, "chapter-1")

        assert result["relationship_changes"] == "some summary"
        assert result["world_changes"] == ""
        assert result["timeline_changes"] == ""
        assert result["new_information"] == ""
