"""Tests for provider fallback mechanism."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from core.types import ProviderConfig, ExecutionProfile
from skills.providers import ProviderRouter, OpenAIAdapter, ProviderAdapter


class MockFailingAdapter(ProviderAdapter):
    """Adapter that always fails with specified error."""

    def __init__(self, config: ProviderConfig, error: Exception):
        super().__init__(config)
        self._error = error

    async def chat(self, messages, profile):
        raise self._error


class MockSuccessAdapter(ProviderAdapter):
    """Adapter that returns fixed response."""

    def __init__(self, config: ProviderConfig, response: str = "default-response"):
        super().__init__(config)
        self._response = response

    async def chat(self, messages, profile):
        return self._response


def register_mock_adapter(router: ProviderRouter, name: str, error=None, response=None):
    """Helper to register mock adapters."""
    config = ProviderConfig(api_key="sk-test", default_model="test")
    if error:
        adapter = MockFailingAdapter(config, error)
        router._adapters[name] = adapter
        router._configs[name] = config
    else:
        adapter = MockSuccessAdapter(config, response or "")
        router._adapters[name] = adapter
        router._configs[name] = config


class TestProviderFallback:
    def test_fallback_success_on_first_try(self):
        """No fallback needed when primary provider works."""
        router = ProviderRouter()
        register_mock_adapter(router, "primary", response="success")

        profile = ExecutionProfile(provider="primary", model="test")

        import asyncio
        response, actual = asyncio.run(
            router.execute_with_fallback([], profile, ["primary"])
        )
        assert response == "success"
        assert actual == "primary"

    def test_fallback_on_timeout(self):
        """Timeout error triggers fallback to next provider."""
        router = ProviderRouter()
        register_mock_adapter(router, "failing", error=TimeoutError("Connection timeout"))
        register_mock_adapter(router, "backup", response="backup-response")

        profile = ExecutionProfile(provider="failing", model="test")

        import asyncio
        response, actual = asyncio.run(
            router.execute_with_fallback([], profile, ["failing", "backup"])
        )
        assert actual == "backup"
        assert response == "backup-response"

    def test_fallback_on_rate_limit(self):
        """Rate limit error triggers fallback."""
        router = ProviderRouter()

        class RateLimitError(Exception):
            pass

        register_mock_adapter(router, "primary", error=RateLimitError("Rate limit exceeded (429)"))
        register_mock_adapter(router, "backup", response="success")

        profile = ExecutionProfile(provider="primary", model="test")

        import asyncio
        response, actual = asyncio.run(
            router.execute_with_fallback([], profile, ["primary", "backup"])
        )
        assert actual == "backup"
        assert response == "success"

    def test_auth_error_no_fallback(self):
        """Authentication errors are raised immediately without fallback."""
        router = ProviderRouter()

        class AuthError(Exception):
            pass

        register_mock_adapter(router, "failing", error=AuthError("Invalid API key (401 unauthorized)"))
        register_mock_adapter(router, "backup", response="should not reach")

        profile = ExecutionProfile(provider="failing", model="test")

        import asyncio
        with pytest.raises(AuthError):
            asyncio.run(
                router.execute_with_fallback([], profile, ["failing", "backup"])
            )

    def test_all_providers_fail(self):
        """When all providers fail, the last error is raised."""
        router = ProviderRouter()

        register_mock_adapter(router, "a", error=TimeoutError("timeout a"))
        register_mock_adapter(router, "b", error=TimeoutError("timeout b"))

        profile = ExecutionProfile(provider="a", model="test")

        import asyncio
        with pytest.raises(TimeoutError, match="timeout b"):
            asyncio.run(router.execute_with_fallback([], profile, ["a", "b"]))

    def test_provider_not_in_chain_skipped(self):
        """Providers not in chain are skipped."""
        router = ProviderRouter()
        register_mock_adapter(router, "a", response="from-a")

        profile = ExecutionProfile(provider="a", model="test")

        import asyncio
        response, actual = asyncio.run(
            router.execute_with_fallback([], profile, ["b", "a"])
        )
        # Should use 'a' since 'b' is not registered (logs warning and skips)
        assert actual == "a"

    def test_empty_chain_raises(self):
        """Empty fallback chain raises error."""
        router = ProviderRouter()
        profile = ExecutionProfile(provider="missing", model="test")

        import asyncio
        with pytest.raises(RuntimeError, match="No providers available"):
            asyncio.run(router.execute_with_fallback([], profile, []))