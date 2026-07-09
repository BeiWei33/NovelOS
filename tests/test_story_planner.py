"""Tests for StoryPlanner skill — context building and knowledge injection."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from core.types import SkillManifest
from skills.story_planner import (
    StoryPlannerSkill,
    STORY_PLANNER_MANIFEST,
    build_story_planner_context,
)


class TestStoryPlannerManifest:
    """Manifest declares skill requirements correctly."""

    def test_manifest_name(self):
        assert STORY_PLANNER_MANIFEST.name == "StoryPlanner"

    def test_manifest_role(self):
        assert STORY_PLANNER_MANIFEST.role == "story-planner"

    def test_manifest_requires(self):
        assert "goal" in STORY_PLANNER_MANIFEST.requires
        assert "theme" in STORY_PLANNER_MANIFEST.requires

    def test_manifest_knowledge(self):
        assert "character_state" in STORY_PLANNER_MANIFEST.knowledge
        assert "world_state" in STORY_PLANNER_MANIFEST.knowledge
        assert "scene_history" in STORY_PLANNER_MANIFEST.knowledge

    def test_manifest_template(self):
        assert STORY_PLANNER_MANIFEST.template == "story_planner.jinja2"

    def test_manifest_constraints(self):
        assert len(STORY_PLANNER_MANIFEST.constraints) == 3


class TestBuildStoryPlannerContext:
    """Context building returns correct structure."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def mock_chapter(self):
        """Create a mock Chapter object."""
        chapter = MagicMock()
        chapter.id = "chapter-001"
        chapter.novel_id = "novel-001"
        chapter.planning = {"goal": "测试章节目标"}
        chapter.summary = {"one_paragraph": "测试摘要", "one_line": "测试一行摘要"}
        return chapter

    @pytest.fixture
    def mock_characters(self):
        """Create mock Character objects."""
        c1 = MagicMock()
        c1.name = "林川"
        c1.goal = "成为强者"
        c1.fear = "失去亲人"

        c2 = MagicMock()
        c2.name = "苏婉"
        c2.goal = "复仇"
        c2.fear = "被遗忘"

        return [c1, c2]

    @pytest.fixture
    def mock_worlds(self):
        """Create mock World objects."""
        w1 = MagicMock()
        w1.name = "修仙界"
        w1.config = {"势力": "三大宗门", "等级": "练气筑基金丹"}

        return [w1]

    @pytest.fixture
    def mock_scenes(self):
        """Create mock Scene objects."""
        s1 = MagicMock()
        s1.id = "scene-001"
        s1.order = 1
        s1.planning = {"goal": "开场场景"}

        s2 = MagicMock()
        s2.id = "scene-002"
        s2.order = 2
        s2.planning = {"goal": "冲突场景"}

        return [s1, s2]

    @pytest.fixture
    def mock_narrative_events(self):
        """Create mock NarrativeEvent objects."""
        e1 = MagicMock()
        e1.type = "relationship_change"
        e1.actor = "林川"
        e1.payload = {"content_preview": "林川遇见了苏婉"}

        e2 = MagicMock()
        e2.type = "reveal"
        e2.actor = "苏婉"
        e2.payload = {"content_preview": "苏婉透露了身世"}

        return [e1, e2]

    @pytest.mark.asyncio
    async def test_returns_goal_and_theme_passthrough(self, mock_db, mock_chapter):
        """Goal and theme should be passed through unchanged."""
        mock_db.get = AsyncMock(return_value=mock_chapter)

        # Mock execute to return proper result structure
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(return_value={"character_state": []})
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db,
                chapter_id="chapter-001",
                goal="主角觉醒",
                theme="成长与选择",
            )

        assert context["goal"] == "主角觉醒"
        assert context["theme"] == "成长与选择"

    @pytest.mark.asyncio
    async def test_returns_chapter_summary(
        self, mock_db, mock_chapter, mock_characters, mock_worlds, mock_scenes
    ):
        """Context should include chapter_summary field."""
        mock_db.get = AsyncMock(return_value=mock_chapter)

        # Mock execute for characters, worlds, scenes
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(return_value={"character_state": []})
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db, chapter_id="chapter-001"
            )

        assert "chapter_summary" in context
        assert context["chapter_summary"] == "测试摘要"

    @pytest.mark.asyncio
    async def test_returns_characters_list(
        self, mock_db, mock_chapter, mock_characters, mock_worlds, mock_scenes
    ):
        """Context should include characters list with name, state, arc_summary."""
        mock_db.get = AsyncMock(return_value=mock_chapter)

        # Create a more sophisticated mock that returns different results
        call_count = [0]

        async def mock_execute(query):
            result = MagicMock()
            if call_count[0] == 0:  # Characters query
                result.scalars.return_value.all.return_value = mock_characters
            elif call_count[0] == 1:  # Worlds query
                result.scalars.return_value.all.return_value = mock_worlds
            else:  # Scenes query
                result.scalars.return_value.all.return_value = mock_scenes
            call_count[0] += 1
            return result

        mock_db.execute = mock_execute

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(
                return_value={
                    "character_state": [
                        MagicMock(
                            payload={"character": "林川", "state": {"emotion": "坚定"}, "arc": "从懦弱到坚强"}
                        ),
                        MagicMock(
                            payload={"character": "苏婉", "state": {"emotion": "仇恨"}, "arc": "复仇之路"}
                        ),
                    ]
                }
            )
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db, chapter_id="chapter-001"
            )

        assert "characters" in context
        assert isinstance(context["characters"], list)
        assert len(context["characters"]) == 2

        # Check character structure
        for char in context["characters"]:
            assert "name" in char
            assert "state" in char
            assert "arc_summary" in char

        # Verify specific characters
        names = [c["name"] for c in context["characters"]]
        assert "林川" in names
        assert "苏婉" in names

    @pytest.mark.asyncio
    async def test_returns_world_state(
        self, mock_db, mock_chapter, mock_characters, mock_worlds, mock_scenes
    ):
        """Context should include world_state as list of key facts."""
        mock_db.get = AsyncMock(return_value=mock_chapter)

        call_count = [0]

        async def mock_execute(query):
            result = MagicMock()
            if call_count[0] == 0:
                result.scalars.return_value.all.return_value = mock_characters
            elif call_count[0] == 1:
                result.scalars.return_value.all.return_value = mock_worlds
            else:
                result.scalars.return_value.all.return_value = mock_scenes
            call_count[0] += 1
            return result

        mock_db.execute = mock_execute

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(return_value={"character_state": []})
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db, chapter_id="chapter-001"
            )

        assert "world_state" in context
        assert isinstance(context["world_state"], list)

        # Check world fact structure
        if context["world_state"]:
            fact = context["world_state"][0]
            assert "key" in fact or "world" in fact

    @pytest.mark.asyncio
    async def test_returns_recent_events(
        self, mock_db, mock_chapter, mock_characters, mock_worlds, mock_scenes, mock_narrative_events
    ):
        """Context should include recent_events with type, actor, summary."""
        mock_db.get = AsyncMock(return_value=mock_chapter)

        call_count = [0]

        async def mock_execute(query):
            result = MagicMock()
            if call_count[0] == 0:
                result.scalars.return_value.all.return_value = mock_characters
            elif call_count[0] == 1:
                result.scalars.return_value.all.return_value = mock_worlds
            elif call_count[0] == 2:
                result.scalars.return_value.all.return_value = mock_scenes
            else:
                result.scalars.return_value.all.return_value = mock_narrative_events
            call_count[0] += 1
            return result

        mock_db.execute = mock_execute

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(return_value={"character_state": []})
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db, chapter_id="chapter-001"
            )

        assert "recent_events" in context
        assert isinstance(context["recent_events"], list)

    @pytest.mark.asyncio
    async def test_calls_knowledge_engine_for_character_state(
        self, mock_db, mock_chapter, mock_characters
    ):
        """Should call KnowledgeEngine.retrieve with character_state."""
        mock_db.get = AsyncMock(return_value=mock_chapter)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_characters
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(return_value={"character_state": []})
            MockEngine.return_value = mock_engine

            await build_story_planner_context(mock_db, chapter_id="chapter-001")

            # Verify KnowledgeEngine was instantiated with db
            MockEngine.assert_called_once_with(mock_db)

            # Verify retrieve was called with character_state
            mock_engine.retrieve.assert_called()
            call_args = mock_engine.retrieve.call_args
            assert "character_state" in call_args[1]["knowledge_types"]

    @pytest.mark.asyncio
    async def test_handles_missing_chapter(self, mock_db):
        """Should return minimal context when chapter not found."""
        mock_db.get = AsyncMock(return_value=None)

        context = await build_story_planner_context(
            mock_db,
            chapter_id="nonexistent",
            goal="测试目标",
            theme="测试主题",
        )

        assert context["goal"] == "测试目标"
        assert context["theme"] == "测试主题"
        # Other fields may be missing
        assert "characters" not in context or context.get("characters") is None or context.get("characters") == []

    @pytest.mark.asyncio
    async def test_existing_scenes_structure(
        self, mock_db, mock_chapter, mock_characters, mock_worlds, mock_scenes
    ):
        """Context should include existing_scenes with order and goal."""
        mock_db.get = AsyncMock(return_value=mock_chapter)

        call_count = [0]

        async def mock_execute(query):
            result = MagicMock()
            if call_count[0] == 0:
                result.scalars.return_value.all.return_value = mock_characters
            elif call_count[0] == 1:
                result.scalars.return_value.all.return_value = mock_worlds
            else:
                result.scalars.return_value.all.return_value = mock_scenes
            call_count[0] += 1
            return result

        mock_db.execute = mock_execute

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(return_value={"character_state": []})
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db, chapter_id="chapter-001"
            )

        assert "existing_scenes" in context
        assert context["existing_scene_count"] == 2
        for scene in context["existing_scenes"]:
            assert "order" in scene
            assert "goal" in scene


class TestStoryPlannerContextStructure:
    """Test the full context structure matches requirements."""

    @pytest.mark.asyncio
    async def test_context_has_all_required_fields(self):
        """Context should have: goal, theme, chapter_summary, characters, world_state, recent_events."""
        # This is a structural test that verifies the keys exist
        expected_fields = [
            "goal",
            "theme",
            "chapter_summary",
            "characters",
            "world_state",
            "recent_events",
        ]

        mock_db = AsyncMock()
        mock_chapter = MagicMock()
        mock_chapter.id = "chapter-001"
        mock_chapter.novel_id = "novel-001"
        mock_chapter.planning = {}
        mock_chapter.summary = {}

        mock_db.get = AsyncMock(return_value=mock_chapter)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(return_value={"character_state": []})
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db, chapter_id="chapter-001", goal="g", theme="t"
            )

        for field in expected_fields:
            assert field in context, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_characters_have_required_subfields(self):
        """Each character should have: name, state, arc_summary."""
        mock_db = AsyncMock()
        mock_chapter = MagicMock()
        mock_chapter.id = "chapter-001"
        mock_chapter.novel_id = "novel-001"
        mock_chapter.planning = {}
        mock_chapter.summary = {}

        mock_character = MagicMock()
        mock_character.name = "测试角色"

        mock_db.get = AsyncMock(return_value=mock_chapter)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_character]
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(
                return_value={
                    "character_state": [
                        MagicMock(
                            payload={"character": "测试角色", "state": {"emotion": "平静"}, "arc": "测试弧线"}
                        )
                    ]
                }
            )
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db, chapter_id="chapter-001"
            )

        if context["characters"]:
            char = context["characters"][0]
            assert "name" in char
            assert "state" in char
            assert "arc_summary" in char

    @pytest.mark.asyncio
    async def test_world_state_is_list_of_dicts(self):
        """world_state should be a list of dicts with key/value pairs."""
        mock_db = AsyncMock()
        mock_chapter = MagicMock()
        mock_chapter.id = "chapter-001"
        mock_chapter.novel_id = "novel-001"
        mock_chapter.planning = {}
        mock_chapter.summary = {}

        mock_world = MagicMock()
        mock_world.name = "测试世界"
        mock_world.config = {"时间": "古代", "地点": "京城"}

        mock_db.get = AsyncMock(return_value=mock_chapter)

        call_count = [0]

        async def mock_execute(query):
            result = MagicMock()
            if call_count[0] == 0:
                result.scalars.return_value.all.return_value = []
            else:
                result.scalars.return_value.all.return_value = [mock_world]
            call_count[0] += 1
            return result

        mock_db.execute = mock_execute

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(return_value={"character_state": []})
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db, chapter_id="chapter-001"
            )

        assert isinstance(context["world_state"], list)
        # Should have facts extracted from world config
        assert len(context["world_state"]) > 0

    @pytest.mark.asyncio
    async def test_recent_events_structure(self):
        """Each recent_event should have: type, actor, summary."""
        mock_db = AsyncMock()
        mock_chapter = MagicMock()
        mock_chapter.id = "chapter-001"
        mock_chapter.novel_id = "novel-001"
        mock_chapter.planning = {}
        mock_chapter.summary = {}

        mock_scene = MagicMock()
        mock_scene.id = "scene-001"
        mock_scene.order = 1
        mock_scene.planning = {}

        mock_event = MagicMock()
        mock_event.type = "test_event"
        mock_event.actor = "测试角色"
        mock_event.payload = {"content_preview": "测试事件摘要"}

        mock_db.get = AsyncMock(return_value=mock_chapter)

        call_count = [0]

        async def mock_execute(query):
            result = MagicMock()
            if call_count[0] == 0:
                result.scalars.return_value.all.return_value = []
            elif call_count[0] == 1:
                result.scalars.return_value.all.return_value = []
            elif call_count[0] == 2:
                result.scalars.return_value.all.return_value = [mock_scene]
            else:
                result.scalars.return_value.all.return_value = [mock_event]
            call_count[0] += 1
            return result

        mock_db.execute = mock_execute

        with patch("skills.story_planner.KnowledgeEngine") as MockEngine:
            mock_engine = AsyncMock()
            mock_engine.retrieve = AsyncMock(return_value={"character_state": []})
            MockEngine.return_value = mock_engine

            context = await build_story_planner_context(
                mock_db, chapter_id="chapter-001"
            )

        if context["recent_events"]:
            event = context["recent_events"][0]
            assert "type" in event
            assert "actor" in event
            assert "summary" in event
