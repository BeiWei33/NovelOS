"""
Base Skill class and registry.

Each Skill:
1. Declares a SkillManifest (role, knowledge requirements, constraints)
2. Receives context via ContextAssembler
3. Renders a prompt via Template
4. Calls an LLM via ProviderAdapter
5. Returns structured output
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from core.types import SkillManifest, ExecutionProfile, ScenePipelineResult


class Skill(ABC):
    """Base class for all NovelOS skills."""

    manifest: SkillManifest

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> Any:
        """Execute the skill with the given context dict.

        Context keys vary by skill but typically include:
        - scene, characters, worlds, styles, rewrite_samples, etc.
        """
        ...


class SkillRegistry:
    """Registry of all available skills."""

    def __init__(self):
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.manifest.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list(self) -> list[str]:
        return list(self._skills.keys())

    def get_by_role(self, role: str) -> list[Skill]:
        return [s for s in self._skills.values() if s.manifest.role == role]


# Global registry
registry = SkillRegistry()