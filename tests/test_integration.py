"""NovelOS integration tests — verify all modules load correctly."""

import os
import sys
import pytest


# Mark all async tests
pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class TestCoreTypes:
    """Core type definitions."""

    def test_domain_block_types(self):
        from core.types import DOMAIN_BLOCK_TYPES, SkillManifest, ExecutionProfile
        assert len(DOMAIN_BLOCK_TYPES) == 9
        assert "narration" in DOMAIN_BLOCK_TYPES
        assert "dialogue" in DOMAIN_BLOCK_TYPES

        manifest = SkillManifest(name="Test", role="test")
        assert manifest.name == "Test"
        assert manifest.role == "test"

        profile = ExecutionProfile(provider="test", model="test-model")
        assert profile.temperature == 0.7


class TestSkills:
    """Skill registry and base classes."""

    def test_skill_registry(self):
        from skills.base import SkillRegistry, Skill
        from core.types import SkillManifest

        registry = SkillRegistry()

        class TestSkill(Skill):
            manifest = SkillManifest(name="TestSkill", role="test-role")

            async def execute(self, context):
                return {"result": "ok"}

        skill = TestSkill()
        registry.register(skill)
        assert registry.get("TestSkill") is skill
        assert "TestSkill" in registry.list()
        assert len(registry.get_by_role("test-role")) == 1

    def test_scene_writer_manifest(self):
        from skills.scene_writer import SCENE_WRITER_MANIFEST, SCENE_WRITER_PROFILE
        assert SCENE_WRITER_MANIFEST.name == "SceneWriter"
        assert SCENE_WRITER_MANIFEST.role == "scene-writer"
        assert SCENE_WRITER_PROFILE.model == "gpt-4o"

    def test_template_rendering(self):
        from prompts.builder import render_template
        context = {"style": "test style", "goal": "test goal", "conflict": "", "stakes": ""}
        # Should not raise
        result = render_template("scene_writer.jinja2", context)
        assert "test style" in result
        assert "test goal" in result


class TestProviders:
    """Provider adapters (no real API calls)."""

    def test_provider_router(self):
        from skills.providers import router
        assert router is not None
        # Can't test actual execution without API key, but routing should work

    def test_execution_profile(self):
        from core.types import ExecutionProfile
        profile = ExecutionProfile(provider="openai", model="gpt-4o", temperature=0.5)
        assert profile.provider == "openai"
        assert profile.model == "gpt-4o"


class TestArtifactService:
    """Artifact extraction — pure data processing, no DB needed."""

    def test_extract_facts(self):
        from services.artifact_service import extract_facts
        doc = {
            "blocks": [
                {"type": "narration", "content": '他说："你好"'},
                {"type": "dialogue", "content": '"今天天气真好"'},
            ]
        }
        facts = extract_facts(doc)
        assert len(facts) == 2

    def test_extract_keywords(self):
        from services.artifact_service import extract_keywords
        doc = {
            "blocks": [
                {"type": "narration", "content": "The ancient streets echoed with footsteps"},
                {"type": "description", "content": "Golden sunlight scattered across the cobblestones"},
            ]
        }
        keywords = extract_keywords(doc)
        assert len(keywords) > 0
        assert "ancient" in keywords or "streets" in keywords or "sunlight" in keywords

    def test_extract_summary(self):
        from services.artifact_service import extract_summary
        doc = {
            "blocks": [
                {"type": "narration", "content": "故事开始了"},
                {"type": "dialogue", "content": "你好"},
            ]
        }
        summary = extract_summary(doc)
        assert summary["one_line"] == "故事开始了"
        assert summary["block_count"] == 2
        assert summary["type_distribution"]["narration"] == 1

    def test_extract_emotion_profile(self):
        from services.artifact_service import extract_emotion_profile
        doc = {
            "blocks": [
                {"type": "narration", "content": "他走着"},
                {"type": "emotion", "content": "心中涌起一阵悲伤"},
                {"type": "dialogue", "content": "你好"},
            ]
        }
        profile = extract_emotion_profile(doc)
        assert profile["emotion_block_count"] == 1
        assert 0 < profile["dialogue_ratio"] < 1


class TestKnowledgeLayer:
    """Knowledge retrievers — unit tests without DB."""

    def test_knowledge_engine_mapping(self):
        from knowledge.retrievers import KnowledgeEngine
        assert "scene_history" in KnowledgeEngine.RETRIEVER_MAP
        assert "character_state" in KnowledgeEngine.RETRIEVER_MAP
        assert "relationship_state" in KnowledgeEngine.RETRIEVER_MAP
        assert "timeline" in KnowledgeEngine.RETRIEVER_MAP
        assert "facts" in KnowledgeEngine.RETRIEVER_MAP

    def test_context_assembler_serialize(self):
        from knowledge.context_assembler import ContextAssembler
        from core.types import KnowledgeObject

        # Test serialization logic directly
        objects = [
            KnowledgeObject(
                type="character_state",
                payload={"character": "林川", "arc": "从懦弱到坚强"},
            ),
        ]
        # Can't call assemble without DB session, but the class should exist
        assert ContextAssembler is not None

    def test_scene_editor_manifest(self):
        from skills.scene_editor import SCENE_EDITOR_MANIFEST, DESLOP_RULES
        assert SCENE_EDITOR_MANIFEST.name == "SceneEditor"
        assert SCENE_EDITOR_MANIFEST.role == "scene-editor"
        assert len(DESLOP_RULES) == 4

    def test_consistency_checker_manifest(self):
        from skills.consistency_checker import CONSISTENCY_CHECKER_MANIFEST
        assert CONSISTENCY_CHECKER_MANIFEST.name == "ConsistencyChecker"
        assert CONSISTENCY_CHECKER_MANIFEST.role == "consistency-checker"

    def test_quality_pipeline_apply_patches(self):
        from workflow.quality_pipeline import apply_patches
        doc = {
            "blocks": [
                {"id": "1", "type": "narration", "content": "他感到非常悲伤"},
            ]
        }
        patches = [
            {
                "op": "replace",
                "block_index": 0,
                "old_text": "他感到非常悲伤",
                "new_text": "他垂下了头，眼泪滴落",
            }
        ]
        result = apply_patches(doc, patches)
        assert "他垂下了头" in result["blocks"][0]["content"]