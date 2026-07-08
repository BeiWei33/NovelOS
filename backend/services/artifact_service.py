"""
ArtifactService — extracts structured knowledge from SceneDocument.

This is a pure data-processing service. No LLM calls.
Run after scene is frozen (or after any edit that changes version).
"""

from __future__ import annotations
import re
import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.canonical import Scene, SceneArtifact, NarrativeEvent
from database.models.projections import (
    FactProjection,
    CharacterStateProjection,
    RelationshipProjection,
    TimelineProjection,
    RetrievalProjection,
)


def extract_facts(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract factual statements from blocks."""
    facts = []
    blocks = document.get("blocks", [])
    for i, block in enumerate(blocks):
        content = block.get("content", "")
        block_type = block.get("type", "")

        # Extract named entities mentioned in the text
        # Simple heuristic: find quoted names and capitalized phrases
        names = re.findall(r'"([^"]*)"', content)

        fact = {
            "source_block": i,
            "block_type": block_type,
            "content_preview": content[:200],
            "mentioned_names": names,
            "type": block_type,
        }
        facts.append(fact)
    return facts


def extract_narrative_events(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract narrative events from blocks."""
    events = []
    blocks = document.get("blocks", [])
    for i, block in enumerate(blocks):
        content = block.get("content", "")
        block_type = block.get("type", "")

        event = {
            "sequence": i,
            "type": "narrative_action" if block_type == "narration" else block_type,
            "actor": None,
            "target": None,
            "payload": {"content_preview": content[:200]},
        }
        events.append(event)
    return events


def extract_summary(document: dict[str, Any]) -> dict[str, str]:
    """Generate a simple summary of the scene."""
    blocks = document.get("blocks", [])
    block_count = len(blocks)
    types = [b.get("type", "unknown") for b in blocks]
    type_counts = {}
    for t in types:
        type_counts[t] = type_counts.get(t, 0) + 1

    # First block content as a brief summary
    first_content = blocks[0].get("content", "")[:100] if blocks else ""

    return {
        "one_line": first_content,
        "block_count": block_count,
        "type_distribution": type_counts,
    }


def extract_keywords(document: dict[str, Any]) -> list[str]:
    """Extract keywords from block content."""
    blocks = document.get("blocks", [])
    words = []
    # Simple keyword extraction: unique non-stop words
    stop_words = {
        "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都",
        "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
        "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
        "们", "那", "什么", "怎么", "为什么", "因为", "所以", "但是",
        "the", "a", "an", "is", "was", "were", "are", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "it", "he", "she", "they",
    }
    for block in blocks:
        content = block.get("content", "")
        # Split on whitespace and punctuation
        found = re.findall(r'[\w一-鿿]+', content)
        for w in found:
            if len(w) > 1 and w.lower() not in stop_words:
                words.append(w)
    # Deduplicate and limit
    seen = set()
    unique = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:30]


def extract_entities(document: dict[str, Any]) -> list[dict[str, str]]:
    """Extract entity names from blocks."""
    entities = []
    blocks = document.get("blocks", [])
    seen = set()
    for block in blocks:
        content = block.get("content", "")
        # Find quoted names
        names = re.findall(r'"([^"]*)"', content)
        for name in names:
            if name not in seen and len(name) <= 20:
                seen.add(name)
                entities.append({"name": name, "type": "mentioned"})
    return entities


def extract_emotion_profile(document: dict[str, Any]) -> dict[str, Any]:
    """Extract emotion-related indicators."""
    blocks = document.get("blocks", [])
    emotion_blocks = [b for b in blocks if b.get("type") == "emotion"]
    dialogue_blocks = [b for b in blocks if b.get("type") == "dialogue"]

    return {
        "emotion_block_count": len(emotion_blocks),
        "dialogue_ratio": len(dialogue_blocks) / max(len(blocks), 1),
        "total_blocks": len(blocks),
    }


def extract_foreshadow_hints(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract potential foreshadowing hints."""
    hints = []
    blocks = document.get("blocks", [])
    for i, block in enumerate(blocks):
        content = block.get("content", "")
        # Look for foreshadowing markers
        markers = ["突然", "似乎", "好像", "隐约", "有一天", "之后", "后来"]
        for marker in markers:
            if marker in content:
                hints.append({
                    "block_index": i,
                    "marker": marker,
                    "content_preview": content[:100],
                })
    return hints


def extract_timeline_deltas(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract time-related information."""
    deltas = []
    blocks = document.get("blocks", [])
    time_patterns = [
        r'(?:早上|中午|下午|晚上|清晨|黄昏|深夜|凌晨)',
        r'(?:第[一二三四五六七八九十\d]+天)',
        r'(?:[\d]+[年月日号])',
        r'(?:昨天|今天|明天|后天|三天后|一周后)',
    ]
    for i, block in enumerate(blocks):
        content = block.get("content", "")
        for pattern in time_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                deltas.append({
                    "block_index": i,
                    "time_reference": m,
                })
    return deltas


async def run_artifact_service(
    db: AsyncSession,
    scene: Scene,
) -> SceneArtifact:
    """Run artifact extraction on a scene. Creates or updates SceneArtifact."""
    document = scene.document or {"blocks": []}

    # Check if artifact exists
    existing = await db.execute(
        select(SceneArtifact).where(SceneArtifact.scene_id == scene.id)
    )
    artifact = existing.scalar_one_or_none()

    if artifact is None:
        artifact = SceneArtifact(scene_id=scene.id)
        db.add(artifact)

    # Extract
    artifact.scene_version = scene.version
    artifact.facts = extract_facts(document)
    artifact.narrative_events = extract_narrative_events(document)
    artifact.summary = extract_summary(document)
    artifact.keywords = extract_keywords(document)
    artifact.emotion_profile = extract_emotion_profile(document)
    artifact.entities = extract_entities(document)
    artifact.foreshadow_hints = extract_foreshadow_hints(document)
    artifact.timeline_deltas = extract_timeline_deltas(document)
    artifact.created_at = datetime.utcnow()

    await db.commit()
    await db.refresh(artifact)
    return artifact


async def run_projection_builder(
    db: AsyncSession,
    scene: Scene,
    artifact: SceneArtifact,
) -> None:
    """Rebuild projections from artifacts."""
    # Get chapter for novel_id
    from database.models.canonical import Chapter
    chapter = await db.get(Chapter, scene.chapter_id)
    if chapter is None:
        return

    novel_id = chapter.novel_id

    # 1. Fact projections
    facts = artifact.facts or []
    for fact in facts:
        proj = FactProjection(
            scene_id=scene.id,
            fact_type=fact.get("type", "unknown"),
            actor=fact.get("actor"),
            target=fact.get("target"),
            payload=fact,
            sequence=fact.get("source_block", 0),
        )
        db.add(proj)

    # 2. Character state projections (from mentioned names)
    entities = artifact.entities or []
    for entity in entities:
        state = CharacterStateProjection(
            character_id=entity.get("name", "unknown"),
            novel_id=novel_id,
            chapter_id=scene.chapter_id,
            scene_id=scene.id,
            state={"last_seen_in_scene": scene.id, "summary": entity.get("name", "")},
            arc_summary=f"出现在场景 {scene.order}",
            updated_at=datetime.utcnow(),
        )
        db.add(state)

    # 3. Timeline projections
    deltas = artifact.timeline_deltas or []
    for i, delta in enumerate(deltas):
        tl = TimelineProjection(
            chapter_id=scene.chapter_id,
            scene_id=scene.id,
            sequence=i,
            narrative_time=delta.get("time_reference", ""),
            event_type="narrative_time",
            event_summary=delta.get("time_reference", ""),
            characters=[],
        )
        db.add(tl)

    # 4. Retrieval projection
    ret = RetrievalProjection(
        scene_id=scene.id,
        chapter_id=scene.chapter_id,
        one_line=artifact.summary.get("one_line", "") if artifact.summary else "",
        keywords=artifact.keywords or [],
        block_types=list(set(
            b.get("type", "") for b in (scene.document or {}).get("blocks", [])
        )),
    )
    db.add(ret)

    await db.commit()