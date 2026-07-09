"""Tests for provider adapter layer."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from core.types import ProviderConfig, ExecutionProfile
from skills.providers import ProviderRouter, OpenAIAdapter


class TestProviderConfig:
    def test_default_values(self):
        config = ProviderConfig()
        assert config.api_key == ""
        assert config.base_url == ""
        assert config.default_model == "gpt-4o"
        assert config.default_max_tokens == 2048

    def test_custom_values(self):
        config = ProviderConfig(
            api_key="sk-test",
            base_url="https://api.example.com/v1",
            default_model="test-model",
            default_max_tokens=4096,
        )
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.example.com/v1"
        assert config.default_model == "test-model"
        assert config.default_max_tokens == 4096


class TestProviderRouter:
    def test_register_and_list(self):
        router = ProviderRouter()
        assert router.list_providers() == []

        config = ProviderConfig(api_key="sk-test")
        router.register("test", OpenAIAdapter, config)
        assert router.list_providers() == ["test"]

    def test_register_multiple(self):
        router = ProviderRouter()
        cfg_a = ProviderConfig(api_key="sk-a")
        cfg_b = ProviderConfig(api_key="sk-b")
        router.register("a", OpenAIAdapter, cfg_a)
        router.register("b", OpenAIAdapter, cfg_b)
        assert set(router.list_providers()) == {"a", "b"}

    def test_get_config(self):
        router = ProviderRouter()
        config = ProviderConfig(api_key="sk-test")
        router.register("test", OpenAIAdapter, config)
        retrieved = router.get_config("test")
        assert retrieved is not None
        assert retrieved.api_key == "sk-test"

    def test_get_config_unknown(self):
        router = ProviderRouter()
        assert router.get_config("nonexistent") is None

    def test_execute_unknown_provider(self):
        router = ProviderRouter()
        profile = ExecutionProfile(provider="nonexistent", model="test")
        with pytest.raises(ValueError, match="Unknown provider"):
            import asyncio
            asyncio.run(router.execute([], profile))

    def test_execute_no_api_key(self):
        router = ProviderRouter()
        config = ProviderConfig(api_key="")
        router.register("empty", OpenAIAdapter, config)
        profile = ExecutionProfile(provider="empty", model="test")
        with pytest.raises(ValueError, match="API key not configured"):
            import asyncio
            asyncio.run(router.execute([], profile))


class TestExecutionProfile:
    def test_default_values(self):
        profile = ExecutionProfile()
        assert profile.provider == "openai"
        assert profile.model == "gpt-4o"
        assert profile.temperature == 0.7
        assert profile.max_tokens == 2048

    def test_custom_values(self):
        profile = ExecutionProfile(
            provider="glm",
            model="glm-4-plus",
            temperature=0.3,
            max_tokens=4096,
        )
        assert profile.provider == "glm"
        assert profile.model == "glm-4-plus"
        assert profile.temperature == 0.3
        assert profile.max_tokens == 4096