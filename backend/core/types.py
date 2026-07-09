"""NovelOS plugin protocol — shared types for Skill manifests and workflow."""

from __future__ import annotations
from typing import Any, Protocol
from dataclasses import dataclass, field


# ─── Domain AST Block Types ───────────────────────────────────────────────────

DOMAIN_BLOCK_TYPES = [
    "narration",
    "dialogue",
    "description",
    "inner_monologue",
    "emotion",
    "letter",
    "phone_message",
    "flashback",
    "system_message",
]


# ─── Skill Manifest ───────────────────────────────────────────────────────────

@dataclass
class SkillManifest:
    """Plugin protocol for all skills.

    Each skill declares its role, required knowledge slices, and constraints.
    The system reads this to wire up providers, templates, and context.
    """
    name: str
    role: str
    requires: list[str] = field(default_factory=list)   # context slices needed
    knowledge: list[str] = field(default_factory=list)   # knowledge types needed
    template: str = ""                                    # prompt template name
    constraints: list[str] = field(default_factory=list)  # behavioral constraints


# ─── Knowledge Objects ────────────────────────────────────────────────────────

@dataclass
class KnowledgeObject:
    """Result from a Retriever — domain objects, not DB records."""
    type: str
    payload: dict[str, Any]
    confidence: float = 1.0


# ─── Provider Config ──────────────────────────────────────────────────────────

@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider.

    Instead of reading global settings directly, each adapter receives a
    ProviderConfig with the fields it needs.
    """
    api_key: str = ""
    base_url: str = ""
    default_model: str = "gpt-4o"
    default_max_tokens: int = 2048


# ─── Execution Profile ────────────────────────────────────────────────────────

@dataclass
class ExecutionProfile:
    """Model selection config — switched by changing YAML."""
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048


# ─── Narrative Event ──────────────────────────────────────────────────────────

@dataclass
class NarrativeEvent:
    type: str
    actor: str | None = None
    target: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    sequence: int = 0


# ─── Scene Pipeline Result ────────────────────────────────────────────────────

@dataclass
class ScenePipelineResult:
    scene_id: str
    document: dict[str, Any]
    provenance: dict[str, Any]
    artifacts_generated: bool = False
    projections_updated: bool = False