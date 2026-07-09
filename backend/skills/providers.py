"""
Provider adapters — bridge between Skill and LLM APIs.

Supports dynamic registration of multiple LLM providers via ProviderConfig.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Type

from openai import AsyncOpenAI

from core.types import ExecutionProfile, ProviderConfig


class ProviderAdapter(ABC):
    """Abstract LLM provider."""

    def __init__(self, config: ProviderConfig):
        self._config = config

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        profile: ExecutionProfile,
    ) -> str:
        ...


class OpenAIAdapter(ProviderAdapter):
    """OpenAI-compatible chat completions."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            kwargs = {"api_key": self._config.api_key}
            if self._config.base_url:
                kwargs["base_url"] = self._config.base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        profile: ExecutionProfile,
    ) -> str:
        if not self._config.api_key:
            raise ValueError(
                f"API key not configured for provider. "
                "Set OPENAI_API_KEY environment variable."
            )

        client = self._get_client()
        model = profile.model or self._config.default_model
        max_tokens = profile.max_tokens or self._config.default_max_tokens

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=profile.temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


class ProviderRouter:
    """Routes skill execution to the right provider based on profile."""

    def __init__(self):
        self._adapters: dict[str, ProviderAdapter] = {}
        self._configs: dict[str, ProviderConfig] = {}

    def register(
        self,
        name: str,
        adapter_cls: Type[ProviderAdapter],
        config: ProviderConfig,
    ) -> None:
        """Register a provider with its configuration."""
        self._configs[name] = config
        self._adapters[name] = adapter_cls(config)

    def get_config(self, name: str) -> ProviderConfig | None:
        """Get the configuration for a provider."""
        return self._configs.get(name)

    def list_providers(self) -> list[str]:
        """Return list of registered provider names."""
        return list(self._adapters.keys())

    async def execute(
        self,
        messages: list[dict[str, str]],
        profile: ExecutionProfile,
    ) -> str:
        adapter = self._adapters.get(profile.provider)
        if adapter is None:
            available = ", ".join(self.list_providers()) or "none"
            raise ValueError(
                f"Unknown provider: {profile.provider}. "
                f"Available providers: {available}"
            )
        return await adapter.chat(messages, profile)


# Global router instance
router = ProviderRouter()


def init_providers() -> None:
    """Initialize providers from environment variables.

    Called once at application startup.
    """
    from core.config import settings

    # Register OpenAI provider
    if settings.OPENAI_API_KEY:
        openai_config = ProviderConfig(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL or "",
            default_model="gpt-4o",
            default_max_tokens=2048,
        )
        router.register("openai", OpenAIAdapter, openai_config)

    # Register GLM-5.2 provider (GLM API compatible)
    if settings.GLM_API_KEY:
        glm_config = ProviderConfig(
            api_key=settings.GLM_API_KEY,
            base_url=settings.GLM_BASE_URL,
            default_model="glm-4-plus",
            default_max_tokens=4096,
        )
        router.register("glm", OpenAIAdapter, glm_config)
