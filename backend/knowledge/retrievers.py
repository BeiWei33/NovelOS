"""
Knowledge Layer — Retrievers that read from Projection tables.

Each Retriever returns a list of KnowledgeObject (type + payload + confidence).
"""

from __future__ import annotations
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from core.types import KnowledgeObject
from database.models.projections import (
    FactProjection,
    CharacterStateProjection,
    RelationshipProjection,
    TimelineProjection,
    RetrievalProjection,
)


class SceneRetriever:
    """Retrieve similar scenes by embedding similarity (pgvector)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(
        self,
        query_embedding: list[float] | None = None,
        novel_id: str | None = None,
        limit: int = 5,
    ) -> list[KnowledgeObject]:
        """Retrieve scenes. Falls back to latest if no embedding available."""
        if query_embedding and novel_id:
            # pgvector similarity search
            embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
            stmt = text("""
                SELECT rp.scene_id, rp.one_line, rp.keywords, rp.block_types,
                       sa.embedding <=> :embedding AS distance
                FROM retrieval_projection rp
                LEFT JOIN scene_artifact sa ON rp.scene_id = sa.scene_id
                JOIN scene s ON rp.scene_id = s.id
                JOIN chapter c ON s.chapter_id = c.id
                WHERE c.novel_id = :novel_id
                ORDER BY distance
                LIMIT :limit
            """)
            result = await self.db.execute(
                stmt,
                {"embedding": embedding_str, "novel_id": novel_id, "limit": limit},
            )
            rows = result.fetchall()
        else:
            # Fallback: latest scenes
            result = await self.db.execute(
                select(RetrievalProjection)
                .order_by(RetrievalProjection.scene_id.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
            return [
                KnowledgeObject(
                    type="scene",
                    payload={
                        "scene_id": r.scene_id,
                        "one_line": r.one_line,
                        "keywords": r.keywords,
                        "block_types": r.block_types,
                    },
                    confidence=1.0,
                )
                for r in rows
            ]

        return [
            KnowledgeObject(
                type="scene",
                payload={
                    "scene_id": row.scene_id,
                    "one_line": row.one_line,
                    "keywords": row.keywords,
                    "block_types": row.block_types,
                },
                confidence=max(0.0, 1.0 - float(row.distance)),
            )
            for row in rows
        ]


class FactRetriever:
    """Retrieve facts from the fact_projection table."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(
        self,
        actor: str | None = None,
        fact_type: str | None = None,
        limit: int = 10,
    ) -> list[KnowledgeObject]:
        query = select(FactProjection)

        if actor:
            query = query.where(FactProjection.actor == actor)
        if fact_type:
            query = query.where(FactProjection.fact_type == fact_type)

        query = query.order_by(FactProjection.sequence.desc()).limit(limit)
        result = await self.db.execute(query)
        facts = result.scalars().all()

        return [
            KnowledgeObject(
                type="fact",
                payload={
                    "fact_type": f.fact_type,
                    "actor": f.actor,
                    "target": f.target,
                    "content": f.payload.get("content_preview", ""),
                },
                confidence=f.confidence,
            )
            for f in facts
        ]


class CharacterRetriever:
    """Retrieve character state from projection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(
        self,
        novel_id: str,
        character_name: str | None = None,
    ) -> list[KnowledgeObject]:
        query = select(CharacterStateProjection).where(
            CharacterStateProjection.novel_id == novel_id
        )
        if character_name:
            query = query.where(
                CharacterStateProjection.character_id == character_name
            )

        query = query.order_by(CharacterStateProjection.updated_at.desc()).limit(10)
        result = await self.db.execute(query)
        states = result.scalars().all()

        return [
            KnowledgeObject(
                type="character_state",
                payload={
                    "character": s.character_id,
                    "state": s.state,
                    "arc": s.arc_summary,
                },
                confidence=1.0,
            )
            for s in states
        ]


class RelationshipRetriever:
    """Retrieve relationship data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(
        self,
        novel_id: str,
        character_a: str | None = None,
    ) -> list[KnowledgeObject]:
        query = select(RelationshipProjection).where(
            RelationshipProjection.novel_id == novel_id
        )
        if character_a:
            query = query.where(
                (RelationshipProjection.character_a == character_a)
                | (RelationshipProjection.character_b == character_a)
            )

        result = await self.db.execute(query)
        rels = result.scalars().all()

        return [
            KnowledgeObject(
                type="relationship",
                payload={
                    "character_a": r.character_a,
                    "character_b": r.character_b,
                    "trust": r.trust,
                    "affection": r.affection,
                    "fear": r.fear,
                    "status": r.status,
                },
                confidence=1.0,
            )
            for r in rels
        ]


class TimelineRetriever:
    """Retrieve timeline events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(
        self,
        chapter_id: str | None = None,
        limit: int = 20,
    ) -> list[KnowledgeObject]:
        query = select(TimelineProjection).order_by(
            TimelineProjection.chapter_id,
            TimelineProjection.scene_id,
            TimelineProjection.sequence,
        )
        if chapter_id:
            query = query.where(TimelineProjection.chapter_id == chapter_id)

        query = query.limit(limit)
        result = await self.db.execute(query)
        events = result.scalars().all()

        return [
            KnowledgeObject(
                type="timeline",
                payload={
                    "chapter": e.chapter_id,
                    "scene": e.scene_id,
                    "time": e.narrative_time,
                    "event": e.event_summary,
                    "characters": e.characters,
                },
                confidence=1.0,
            )
            for e in events
        ]


class KnowledgeEngine:
    """Orchestrates retrievers for a given skill's knowledge requirements."""

    RETRIEVER_MAP: dict[str, type] = {
        "scene_history": SceneRetriever,
        "character_state": CharacterRetriever,
        "relationship_state": RelationshipRetriever,
        "timeline": TimelineRetriever,
        "facts": FactRetriever,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(
        self,
        knowledge_types: list[str],
        **filters: Any,
    ) -> dict[str, list[KnowledgeObject]]:
        """Fetch context slices for requested knowledge types."""
        results: dict[str, list[KnowledgeObject]] = {}

        for kt in knowledge_types:
            cls = self.RETRIEVER_MAP.get(kt)
            if cls is None:
                continue

            retriever = cls(self.db)

            if kt == "scene_history":
                results[kt] = await retriever.retrieve(
                    query_embedding=None,
                    novel_id=filters.get("novel_id"),
                )
            elif kt == "character_state":
                results[kt] = await retriever.retrieve(
                    novel_id=filters.get("novel_id", ""),
                    character_name=filters.get("character_name"),
                )
            elif kt == "relationship_state":
                results[kt] = await retriever.retrieve(
                    novel_id=filters.get("novel_id", ""),
                )
            elif kt == "timeline":
                results[kt] = await retriever.retrieve(
                    chapter_id=filters.get("chapter_id"),
                )
            elif kt == "facts":
                results[kt] = await retriever.retrieve(
                    actor=filters.get("actor"),
                )
            else:
                results[kt] = await retriever.retrieve()

        return results