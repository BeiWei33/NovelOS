"""
Provider adapters — bridge between Skill and LLM APIs.

Supports dynamic registration of multiple LLM providers via ProviderConfig,
YAML configuration files, and environment variables.
"""

from __future__ import annotations
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Type

import yaml
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
    """OpenAI-compatible chat completions.

    Works with any provider that exposes an OpenAI-compatible API endpoint,
    including OpenAI, GLM, Ollama, vLLM, and others.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            if not self._config.api_key:
                raise ValueError(
                    f"API key not configured for provider. "
                    "Set the appropriate environment variable."
                )
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


def _load_yaml_providers(yaml_path: str) -> dict[str, ProviderConfig]:
    """Load provider configurations from a YAML file."""
    if not os.path.exists(yaml_path):
        return {}

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "providers" not in data:
        return {}

    providers: dict[str, ProviderConfig] = {}
    for name, cfg in data["providers"].items():
        if not isinstance(cfg, dict):
            continue
        api_key = cfg.get("api_key", "")
        # Resolve ${VAR} references
        api_key = _resolve_env_ref(api_key)
        base_url = cfg.get("base_url", "")
        if not base_url:
            raise ValueError(f"Provider '{name}': base_url is required")
        providers[name] = ProviderConfig(
            api_key=api_key,
            base_url=base_url,
            default_model=cfg.get("default_model", "gpt-4o"),
            default_max_tokens=cfg.get("default_max_tokens", 2048),
        )
    return providers


def _load_env_providers() -> dict[str, ProviderConfig]:
    """Load provider configurations from environment variables.

    Looks for PROVIDER_<NAME>_BASE_URL, PROVIDER_<NAME>_API_KEY, etc.
    """
    providers: dict[str, ProviderConfig] = {}
    pattern = re.compile(r"^PROVIDER_([A-Z][A-Z0-9_]*)_BASE_URL$")

    for key, value in os.environ.items():
        m = pattern.match(key)
        if not m or not value:
            continue
        name = m.group(1).lower()
        api_key = os.environ.get(f"PROVIDER_{m.group(1)}_API_KEY", "")
        default_model = os.environ.get(
            f"PROVIDER_{m.group(1)}_DEFAULT_MODEL", "gpt-4o"
        )
        default_max_tokens = int(
            os.environ.get(f"PROVIDER_{m.group(1)}_DEFAULT_MAX_TOKENS", "2048")
        )
        providers[name] = ProviderConfig(
            api_key=api_key,
            base_url=value,
            default_model=default_model,
            default_max_tokens=default_max_tokens,
        )
    return providers


def _resolve_env_ref(value: str) -> str:
    """Resolve ${VAR} references in a string value."""
    pattern = re.compile(r"\$\{([^}]+)\}")
    return pattern.sub(lambda m: os.environ.get(m.group(1), m.group(0)), value)


def init_providers() -> None:
    """Initialize providers from environment variables and YAML config.

    Called once at application startup. Order of precedence:
    1. Hard-coded providers (OpenAI, GLM) from env vars
    2. YAML providers from providers.yaml
    3. Environment-driven providers (PROVIDER_<NAME>_BASE_URL)
    """
    from core.config import settings

    # 1. Register hard-coded providers from settings
    if settings.OPENAI_API_KEY:
        openai_config = ProviderConfig(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL or "",
            default_model="gpt-4o",
            default_max_tokens=2048,
        )
        router.register("openai", OpenAIAdapter, openai_config)

    if settings.GLM_API_KEY:
        glm_config = ProviderConfig(
            api_key=settings.GLM_API_KEY,
            base_url=settings.GLM_BASE_URL,
            default_model="glm-4-plus",
            default_max_tokens=4096,
        )
        router.register("glm", OpenAIAdapter, glm_config)

    # 2. Load YAML-configured providers
    yaml_path = os.environ.get(
        "PROVIDERS_YAML_PATH",
        os.path.join(os.path.dirname(__file__), "..", "providers.yaml"),
    )
    yaml_providers = _load_yaml_providers(yaml_path)
    for name, config in yaml_providers.items():
        if name not in router.list_providers():
            router.register(name, OpenAIAdapter, config)

    # 3. Load environment-driven providers
    env_providers = _load_env_providers()
    for name, config in env_providers.items():
        if name not in router.list_providers():
            router.register(name, OpenAIAdapter, config)