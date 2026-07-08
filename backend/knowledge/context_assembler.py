"""
ContextAssembler — the bridge between Skills and Knowledge Layer.

Reads a Skill's Manifest, determines what knowledge it needs,
calls the KnowledgeEngine, and assembles context slices into
a flat dict ready for Template rendering.
"""

from __future__ import annotations
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.types import SkillManifest, KnowledgeObject
from knowledge.retrievers import KnowledgeEngine


class ContextAssembler:
    """Assembles context for a skill based on its manifest."""

    def __init__(self, db: AsyncSession):
        self._engine = KnowledgeEngine(db)

    async def assemble(
        self,
        manifest: SkillManifest,
        **filters: Any,
    ) -> dict[str, Any]:
        """Build context dict from manifest's knowledge requirements.

        Args:
            manifest: The skill's manifest declaring knowledge needs.
            **filters: Contextual filters (novel_id, chapter_id, etc.)

        Returns:
            A flat dict with string values for template rendering.
        """
        context: dict[str, Any] = {}

        # Fetch knowledge from the engine
        knowledge = await self._engine.retrieve(
            knowledge_types=manifest.knowledge,
            **filters,
        )

        # Convert KnowledgeObjects to template-friendly strings
        for kt, objects in knowledge.items():
            context[kt] = self._serialize(kt, objects)

        # Required fields from the manifest
        for req in manifest.requires:
            if req in filters:
                context[req] = filters[req]

        return context

    def _serialize(
        self,
        knowledge_type: str,
        objects: list[KnowledgeObject],
    ) -> str:
        """Serialize a list of KnowledgeObjects to a string for template."""
        if not objects:
            return ""

        parts = []
        for obj in objects[:5]:  # Limit to top 5 per type
            payload = obj.payload
            if knowledge_type == "scene_history":
                parts.append(
                    f"- 场景 {payload.get('scene_id', '?')}: "
                    f"{payload.get('one_line', '')}"
                )
            elif knowledge_type == "character_state":
                parts.append(
                    f"- {payload.get('character', '?')}: "
                    f"{payload.get('arc', '')}"
                )
            elif knowledge_type == "relationship_state":
                parts.append(
                    f"- {payload.get('character_a', '?')} ↔ "
                    f"{payload.get('character_b', '?')}: "
                    f"{payload.get('status', 'neutral')} "
                    f"(信任:{payload.get('trust', 0)}, "
                    f"情感:{payload.get('affection', 0)})"
                )
            elif knowledge_type == "timeline":
                parts.append(
                    f"- [{payload.get('time', '?')}] "
                    f"{payload.get('event', '')}"
                )
            elif knowledge_type == "facts":
                parts.append(
                    f"- {payload.get('content', '')}"
                )
            else:
                parts.append(f"- {payload}")

        return "\n".join(parts)