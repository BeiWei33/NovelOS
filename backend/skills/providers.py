"""
Provider adapters — bridge between Skill and LLM APIs.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from openai import AsyncOpenAI

from core.config import settings
from core.types import ExecutionProfile


class ProviderAdapter(ABC):
    """Abstract LLM provider."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        profile: ExecutionProfile,
    ) -> str:
        ...


class OpenAIAdapter(ProviderAdapter):
    """OpenAI-compatible chat completions."""

    def __init__(self):
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            kwargs = {}
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        profile: ExecutionProfile,
    ) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=profile.model,
            messages=messages,
            temperature=profile.temperature,
            max_tokens=profile.max_tokens,
        )
        return response.choices[0].message.content or ""


class ProviderRouter:
    """Routes skill execution to the right provider based on profile."""

    def __init__(self):
        self._adapters: dict[str, ProviderAdapter] = {
            "openai": OpenAIAdapter(),
        }

    def execute(
        self,
        messages: list[dict[str, str]],
        profile: ExecutionProfile,
    ) -> str:
        adapter = self._adapters.get(profile.provider)
        if adapter is None:
            raise ValueError(f"Unknown provider: {profile.provider}")
        return adapter.chat(messages, profile)


router = ProviderRouter()