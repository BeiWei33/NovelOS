"""Tests for profile registry."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from core.types import ExecutionProfile
from skills.profile_registry import ProfileRegistry, DEFAULT_PROFILES


class TestProfileRegistry:
    def test_default_profiles_exist(self):
        registry = ProfileRegistry()
        assert "story-planner" in registry.list_profiles()
        assert "scene-writer" in registry.list_profiles()
        assert "scene-editor" in registry.list_profiles()
        assert "consistency-checker" in registry.list_profiles()

    def test_get_profile(self):
        registry = ProfileRegistry()
        profile = registry.get("scene-writer")
        assert profile.provider == "openai"
        assert profile.model == "gpt-4o"
        assert profile.temperature == 0.7
        assert profile.max_tokens == 2048

    def test_get_unknown_role_returns_default(self):
        registry = ProfileRegistry()
        profile = registry.get("nonexistent-role")
        assert profile.provider == "openai"  # default

    def test_register_custom(self):
        registry = ProfileRegistry()
        custom = ExecutionProfile(
            provider="glm",
            model="glm-4-plus",
            temperature=0.5,
            max_tokens=8192,
        )
        registry.register("custom-role", custom)
        retrieved = registry.get("custom-role")
        assert retrieved.provider == "glm"
        assert retrieved.model == "glm-4-plus"
        assert retrieved.max_tokens == 8192

    def test_load_from_yaml(self):
        yaml_content = """
profiles:
  scene-writer:
    provider: glm
    model: glm-4-plus
    temperature: 0.8
    max_tokens: 4096
  custom-role:
    provider: ollama
    model: llama3
    temperature: 0.5
    max_tokens: 2048
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            fpath = f.name
            f.write(yaml_content)
            f.flush()
            registry = ProfileRegistry()
            registry.load_from_yaml(fpath)

        os.unlink(fpath)

        # scene-writer should be overridden
        sw = registry.get("scene-writer")
        assert sw.provider == "glm"
        assert sw.model == "glm-4-plus"
        assert sw.temperature == 0.8
        assert sw.max_tokens == 4096

        # custom-role should be added
        custom = registry.get("custom-role")
        assert custom.provider == "ollama"
        assert custom.model == "llama3"

        # other defaults should remain
        planner = registry.get("story-planner")
        assert planner.provider == "openai"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("PROFILE_SCENE_WRITER_MODEL", "gpt-4o-mini")
        monkeypatch.setenv("PROFILE_SCENE_WRITER_TEMPERATURE", "0.5")

        registry = ProfileRegistry()
        registry.apply_env_overrides()

        profile = registry.get("scene-writer")
        assert profile.model == "gpt-4o-mini"
        assert profile.temperature == 0.5
        # non-overridden fields preserved
        assert profile.provider == "openai"
        assert profile.max_tokens == 2048

    def test_env_override_provider(self, monkeypatch):
        monkeypatch.setenv("PROFILE_SCENE_WRITER_PROVIDER", "glm")

        registry = ProfileRegistry()
        registry.apply_env_overrides()

        profile = registry.get("scene-writer")
        assert profile.provider == "glm"

    def test_missing_yaml_silent(self):
        registry = ProfileRegistry()
        registry.load_from_yaml("/nonexistent/path.yaml")
        # Should still have defaults
        assert "scene-writer" in registry.list_profiles()