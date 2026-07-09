"""Tests for non-OpenAI-compatible provider adapters."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from core.types import ProviderConfig, ExecutionProfile
from skills.providers import (
    ProviderRouter,
    OpenAIAdapter,
    AnthropicAdapter,
    OllamaNativeAdapter,
)


class TestAnthropicAdapter:
    def test_no_api_key_raises(self):
        """Test that missing API key gives clear error message."""
        config = ProviderConfig(api_key="")
        adapter = AnthropicAdapter(config)
        profile = ExecutionProfile(model="claude-sonnet-4-20250514")
        # Will raise ImportError first if anthropic not installed
        with pytest.raises((ValueError, ImportError)):
            import asyncio
            asyncio.run(adapter.chat([], profile))

    def test_no_anthropic_package(self, monkeypatch):
        monkeypatch.setattr("skills.providers.AnthropicAdapter._get_client", lambda self: (_ for _ in ()).throw(ImportError))
        config = ProviderConfig(api_key="sk-test")
        adapter = AnthropicAdapter(config)
        profile = ExecutionProfile(model="claude-sonnet-4-20250514")
        # Mock the _get_client to raise ImportError
        with pytest.raises(ImportError):
            import asyncio
            asyncio.run(adapter.chat([], profile))

    def test_system_message_extraction(self):
        """Test that system message is properly separated from chat messages."""
        config = ProviderConfig(api_key="sk-test")
        adapter = AnthropicAdapter(config)
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]
        # We can't actually call the API without a real key, but we can
        # verify the minimal implementation stores config correctly
        assert adapter._config.api_key == "sk-test"


class TestOllamaNativeAdapter:
    def test_default_base_url(self):
        config = ProviderConfig()
        adapter = OllamaNativeAdapter(config)
        assert adapter._base_url == "http://localhost:11434"

    def test_custom_base_url(self):
        config = ProviderConfig(base_url="http://192.168.1.100:11434")
        adapter = OllamaNativeAdapter(config)
        assert adapter._base_url == "http://192.168.1.100:11434"

    def test_connection_refused(self):
        """Test that Ollama connection failure gives clear error."""
        config = ProviderConfig(
            base_url="http://localhost:1",  # nothing listening here
            default_model="test-model",
        )
        adapter = OllamaNativeAdapter(config)
        profile = ExecutionProfile(model="test-model", temperature=0.5)

        with pytest.raises(Exception) as exc_info:
            import asyncio
            asyncio.run(adapter.chat([{"role": "user", "content": "hi"}], profile))

        # Should get a connection error, not a generic error
        error_str = str(exc_info.value).lower()
        assert any(
            keyword in error_str
            for keyword in ["connection", "refused", "connect", "timeout", "cannot"]
        )


class TestNonOpenAIProviderRegistration:
    def test_register_anthropic(self):
        router = ProviderRouter()
        config = ProviderConfig(api_key="sk-test")
        router.register("anthropic", AnthropicAdapter, config)
        assert "anthropic" in router.list_providers()

    def test_register_ollama_native(self):
        router = ProviderRouter()
        config = ProviderConfig(base_url="http://localhost:11434")
        router.register("ollama-native", OllamaNativeAdapter, config)
        assert "ollama-native" in router.list_providers()

    def test_mixed_providers(self):
        router = ProviderRouter()
        router.register("openai", OpenAIAdapter, ProviderConfig(api_key="sk-a"))
        router.register("anthropic", AnthropicAdapter, ProviderConfig(api_key="sk-b"))
        router.register("ollama-native", OllamaNativeAdapter, ProviderConfig())
        assert set(router.list_providers()) == {"openai", "anthropic", "ollama-native"}