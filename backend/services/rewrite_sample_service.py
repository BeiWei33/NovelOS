"""
RewriteSample CRUD and embedding service.
"""

from __future__ import annotations
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.rewrite_sample import RewriteSample


async def create_rewrite_sample(
    db: AsyncSession,
    input_text: str,
    output_text: str,
    tags: list[str] | None = None,
    style_tags: list[str] | None = None,
    novel_id: str | None = None,
) -> RewriteSample:
    """Create a new rewrite sample."""
    sample = RewriteSample(
        novel_id=novel_id,
        input_text=input_text,
        output_text=output_text,
        tags=tags or [],
        style_tags=style_tags or [],
    )
    db.add(sample)
    await db.commit()
    await db.refresh(sample)
    return sample


async def list_rewrite_samples(
    db: AsyncSession,
    novel_id: str | None = None,
    tag: str | None = None,
) -> list[RewriteSample]:
    """List rewrite samples, optionally filtered."""
    query = select(RewriteSample)

    if novel_id:
        query = query.where(RewriteSample.novel_id == novel_id)
    if tag:
        query = query.where(RewriteSample.tags.contains([tag]))

    query = query.order_by(RewriteSample.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def delete_rewrite_sample(
    db: AsyncSession,
    sample_id: str,
) -> bool:
    """Delete a rewrite sample."""
    sample = await db.get(RewriteSample, sample_id)
    if sample is None:
        return False
    await db.delete(sample)
    await db.commit()
    return True


async def search_similar_samples(
    db: AsyncSession,
    query_embedding: list[float],
    novel_id: str | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Find similar samples by embedding similarity.

    Simple implementation using cosine similarity.
    For production, use pgvector.
    """
    samples = await list_rewrite_samples(db, novel_id)

    # Compute similarity scores
    scored = []
    for sample in samples:
        if sample.embedding:
            sim = _cosine_similarity(query_embedding, sample.embedding)
            scored.append((sample, sim))

    # Sort by similarity, return top N
    scored.sort(key=lambda x: x[1], reverse=True)
    return [
        {
            "id": s.id,
            "input": s.input_text,
            "output": s.output_text,
            "tags": s.tags,
            "similarity": score,
        }
        for s, score in scored[:limit]
    ]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)