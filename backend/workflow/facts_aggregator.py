"""
ChapterFactsAggregator — aggregates facts from all scenes in a chapter.

Reads scene_artifact.facts for each scene, groups by fact_type,
deduplicates by (actor, target), and writes to chapter.chapter_facts.
"""

from __future__ import annotations
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.canonical import Scene, SceneArtifact, Chapter


# Canonical fact types
FACT_TYPES = [
    "relationship_changes",
    "world_changes",
    "timeline_changes",
    "new_information",
]


def aggregate_facts(all_facts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Aggregate facts by type and deduplicate by (actor, target).

    Args:
        all_facts: List of fact dicts ordered by scene order (latest last).
                   Each fact should have: fact_type, actor, target, and other fields.

    Returns:
        Dict with keys: relationship_changes, world_changes, timeline_changes, new_information.
        Each value is a list of unique facts (deduplicated by actor+target).

    Deduplication logic:
        - Within each fact_type group, facts with same (actor, target) are deduplicated
        - Later facts (from later scenes) overwrite earlier ones
        - This ensures the aggregated facts reflect the latest state
    """
    # Initialize grouped dict with empty dicts for deduplication
    grouped: dict[str, dict[tuple[str, str], dict[str, Any]]] = {
        ft: {} for ft in FACT_TYPES
    }

    for fact in all_facts:
        fact_type = fact.get("fact_type", "new_information")

        # Default unknown types to "new_information"
        if fact_type not in grouped:
            fact_type = "new_information"

        actor = fact.get("actor") or ""
        target = fact.get("target") or ""
        key = (actor, target)

        # Later facts overwrite earlier ones (keep latest)
        grouped[fact_type][key] = fact

    # Convert deduplication dicts to lists
    return {
        ft: list(grouped[ft].values())
        for ft in FACT_TYPES
    }


async def run_facts_aggregator(
    db: AsyncSession,
    chapter_id: str,
) -> dict[str, list[dict[str, Any]]]:
    """Run facts aggregation for a chapter.

    Reads all scene artifacts in scene order, aggregates their facts,
    and writes the result to chapter.chapter_facts.

    Args:
        db: Database session
        chapter_id: Chapter ID

    Returns:
        Aggregated facts dict with keys: relationship_changes, world_changes,
        timeline_changes, new_information.
    """
    # Get chapter
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        return {ft: [] for ft in FACT_TYPES}

    # Get all scenes for this chapter, ordered by scene order
    scenes_result = await db.execute(
        select(Scene)
        .where(Scene.chapter_id == chapter_id)
        .order_by(Scene.order)
    )
    scenes = list(scenes_result.scalars().all())

    if not scenes:
        return {ft: [] for ft in FACT_TYPES}

    # Collect all facts from scene artifacts in order
    all_facts: list[dict[str, Any]] = []

    for scene in scenes:
        # Get scene artifact
        artifact_result = await db.execute(
            select(SceneArtifact).where(SceneArtifact.scene_id == scene.id)
        )
        artifact = artifact_result.scalar_one_or_none()

        if artifact and artifact.facts:
            # artifact.facts can be a dict or a list depending on structure
            # Handle both cases
            if isinstance(artifact.facts, dict):
                # If it's already grouped by fact_type
                for fact_type in FACT_TYPES:
                    facts_of_type = artifact.facts.get(fact_type, [])
                    if isinstance(facts_of_type, list):
                        all_facts.extend(facts_of_type)
            elif isinstance(artifact.facts, list):
                # If it's a flat list of facts
                all_facts.extend(artifact.facts)

    # Aggregate
    aggregated = aggregate_facts(all_facts)

    # Write to chapter.chapter_facts
    chapter.chapter_facts = aggregated
    await db.commit()
    await db.refresh(chapter)

    return aggregated
