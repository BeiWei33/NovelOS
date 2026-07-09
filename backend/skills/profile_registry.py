"""
Profile Registry — loads ExecutionProfile from YAML config.

Enables "switch models by changing YAML only" for all skills.
"""

from __future__ import annotations
import logging
import os
from dataclasses import replace
from typing import Optional

import yaml

from core.types import ExecutionProfile


logger = logging.getLogger(__name__)


# Default profiles matching original hardcoded values
DEFAULT_PROFILES: dict[str, ExecutionProfile] = {
    "story-planner": ExecutionProfile(
        provider="openai",
        model="gpt-4o",
        temperature=0.7,
        max_tokens=2048,
    ),
    "scene-writer": ExecutionProfile(
        provider="openai",
        model="gpt-4o",
        temperature=0.7,
        max_tokens=2048,
    ),
    "scene-editor": ExecutionProfile(
        provider="openai",
        model="gpt-4o",
        temperature=0.3,
        max_tokens=1024,
    ),
    "consistency-checker": ExecutionProfile(
        provider="openai",
        model="gpt-4o",
        temperature=0.2,
        max_tokens=1024,
    ),
}


class ProfileRegistry:
    """Registry for skill execution profiles loaded from config."""

    def __init__(self):
        self._profiles: dict[str, ExecutionProfile] = dict(DEFAULT_PROFILES)

    def load_from_yaml(self, path: str) -> None:
        """Load profiles from a YAML file."""
        if not os.path.exists(path):
            return

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "profiles" not in data:
            return

        for name, cfg in data["profiles"].items():
            if not isinstance(cfg, dict):
                continue
            self._profiles[name] = ExecutionProfile(
                provider=cfg.get("provider", "openai"),
                model=cfg.get("model", "gpt-4o"),
                temperature=cfg.get("temperature", 0.7),
                max_tokens=cfg.get("max_tokens", 2048),
            )

    def apply_env_overrides(self) -> None:
        """Apply environment variable overrides.

        Format: PROFILE_<ROLE>_<FIELD>=value
        Example: PROFILE_SCENE_WRITER_MODEL=gpt-4o-mini
        """
        for role in list(self._profiles.keys()):
            env_prefix = f"PROFILE_{role.upper().replace('-', '_')}_"
            profile = self._profiles[role]

            overrides = {}
            if f"{env_prefix}PROVIDER" in os.environ:
                overrides["provider"] = os.environ[f"{env_prefix}PROVIDER"]
            if f"{env_prefix}MODEL" in os.environ:
                overrides["model"] = os.environ[f"{env_prefix}MODEL"]
            if f"{env_prefix}TEMPERATURE" in os.environ:
                overrides["temperature"] = float(os.environ[f"{env_prefix}TEMPERATURE"])
            if f"{env_prefix}MAX_TOKENS" in os.environ:
                overrides["max_tokens"] = int(os.environ[f"{env_prefix}MAX_TOKENS"])

            if overrides:
                self._profiles[role] = replace(profile, **overrides)

    def get(self, role: str) -> ExecutionProfile:
        """Get execution profile for a skill role.

        Returns the profile if defined, otherwise a default profile.
        Logs a warning for unknown roles.
        """
        if role in self._profiles:
            return self._profiles[role]
        # Log warning for unknown roles
        logger.warning(
            f"Unknown profile role '{role}'. Returning default profile. "
            f"Available roles: {', '.join(self.list_profiles())}"
        )
        return ExecutionProfile()

    def list_profiles(self) -> list[str]:
        """Return list of registered profile names."""
        return list(self._profiles.keys())

    def register(self, role: str, profile: ExecutionProfile) -> None:
        """Register or update a profile."""
        self._profiles[role] = profile


# Global registry instance
profile_registry = ProfileRegistry()


def init_profiles() -> None:
    """Initialize profiles from YAML and environment variables.

    Called once at application startup.
    """
    yaml_path = os.environ.get(
        "PROFILES_YAML_PATH",
        os.path.join(os.path.dirname(__file__), "..", "profiles.yaml"),
    )
    profile_registry.load_from_yaml(yaml_path)
    profile_registry.apply_env_overrides()
