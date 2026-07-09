"""Tests for chapter summarizer skill."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from skills.chapter_summarizer import ChapterSummarizerSkill, CHAPTER_SUMMARIZER_MANIFEST
from workflow.consistency_score import (
    calculate_consistency_score,
    get_consistency_level,
    get_consistency_color,
)


class TestChapterSummarizerManifest:
    def test_manifest_name(self):
        assert CHAPTER_SUMMARIZER_MANIFEST.name == "ChapterSummarizer"

    def test_manifest_role(self):
        assert CHAPTER_SUMMARIZER_MANIFEST.role == "chapter-summarizer"

    def test_manifest_requires(self):
        assert "scenes" in CHAPTER_SUMMARIZER_MANIFEST.requires


class TestChapterSummarizerSkill:
    def test_truncate_short_text(self):
        skill = ChapterSummarizerSkill()
        text = "这是一段短文本"
        result = skill._truncate(text, 50)
        assert result == text

    def test_truncate_long_text(self):
        skill = ChapterSummarizerSkill()
        text = "这是一段很长的文本" * 20
        result = skill._truncate(text, 50)
        assert len(result) <= 50

    def test_truncate_preserves_sentence(self):
        skill = ChapterSummarizerSkill()
        text = "第一句话。第二句话。第三句话。第四句话。"
        result = skill._truncate(text, 20)
        # Should truncate at sentence boundary if possible
        assert result.endswith("。")


class TestConsistencyScore:
    def test_no_issues_perfect_score(self):
        score = calculate_consistency_score([])
        assert score == 100

    def test_error_deducts_20(self):
        issues = [{"id": "1", "severity": "error", "message": "test error"}]
        score = calculate_consistency_score(issues)
        assert score == 80

    def test_warning_deducts_5(self):
        issues = [{"id": "1", "severity": "warning", "message": "test warning"}]
        score = calculate_consistency_score(issues)
        assert score == 95

    def test_multiple_errors(self):
        issues = [
            {"id": "1", "severity": "error"},
            {"id": "2", "severity": "error"},
        ]
        score = calculate_consistency_score(issues)
        assert score == 60

    def test_mixed_issues(self):
        issues = [
            {"id": "1", "severity": "error"},
            {"id": "2", "severity": "warning"},
            {"id": "3", "severity": "warning"},
        ]
        score = calculate_consistency_score(issues)
        assert score == 70  # 100 - 20 - 5 - 5

    def test_score_floor(self):
        issues = [
            {"id": "1", "severity": "error"},
            {"id": "2", "severity": "error"},
            {"id": "3", "severity": "error"},
            {"id": "4", "severity": "error"},
            {"id": "5", "severity": "error"},
            {"id": "6", "severity": "error"},
        ]
        score = calculate_consistency_score(issues)
        assert score == 0  # 100 - 120 = -20, floored at 0

    def test_fixed_issues_not_counted(self):
        issues = [
            {"id": "1", "severity": "error"},
            {"id": "2", "severity": "warning"},
        ]
        fixed = [{"id": "1", "severity": "error"}]
        score = calculate_consistency_score(issues, fixed)
        assert score == 95  # Only warning counted

    def test_unknown_severity_not_deducted(self):
        """Unknown severity levels (like 'info') don't affect score."""
        issues = [{"id": "1", "severity": "info"}]
        score = calculate_consistency_score(issues)
        assert score == 100  # info doesn't deduct


class TestConsistencyLevel:
    def test_good_level(self):
        assert get_consistency_level(100) == "good"
        assert get_consistency_level(80) == "good"
        assert get_consistency_level(90) == "good"

    def test_warning_level(self):
        assert get_consistency_level(79) == "warning"
        assert get_consistency_level(50) == "warning"
        assert get_consistency_level(60) == "warning"

    def test_error_level(self):
        assert get_consistency_level(49) == "error"
        assert get_consistency_level(0) == "error"
        assert get_consistency_level(25) == "error"


class TestConsistencyColor:
    def test_green_for_good(self):
        color = get_consistency_color(100)
        assert color == "#22c55e"

    def test_yellow_for_warning(self):
        color = get_consistency_color(60)
        assert color == "#eab308"

    def test_red_for_error(self):
        color = get_consistency_color(30)
        assert color == "#ef4444"