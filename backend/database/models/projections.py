"""
Projection Layer models — read models optimized for query patterns.
All are reconstructible from Artifacts.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import relationship

from database.session import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


# ─── Fact Projection ──────────────────────────────────────────────────────────

class FactProjection(Base):
    """who knows what, what happened"""

    __tablename__ = "fact_projection"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    scene_id = Column(UUID(as_uuid=False), nullable=False)
    fact_type = Column(String(100), nullable=False)
    actor = Column(String(255))
    target = Column(String(255))
    payload = Column(JSONB, default=dict, nullable=False)
    confidence = Column(Float, default=1.0)
    sequence = Column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_fact_projection_scene", "scene_id"),
        Index("ix_fact_projection_actor", "actor"),
    )


# ─── Character State Projection ───────────────────────────────────────────────

class CharacterStateProjection(Base):
    """character arcs + current state"""

    __tablename__ = "character_state_projection"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    character_id = Column(UUID(as_uuid=False), nullable=False)
    novel_id = Column(UUID(as_uuid=False), nullable=False)
    chapter_id = Column(UUID(as_uuid=False))
    scene_id = Column(UUID(as_uuid=False))

    # state: {emotion, goals, secrets_known}
    state = Column(JSONB, default=dict, nullable=False)

    arc_summary = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_character_state_char", "character_id"),
        Index("ix_character_state_novel", "novel_id"),
    )


# ─── Relationship Projection ──────────────────────────────────────────────────

class RelationshipProjection(Base):
    """relationship graph edges"""

    __tablename__ = "relationship_projection"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    character_a = Column(String(255), nullable=False)
    character_b = Column(String(255), nullable=False)
    novel_id = Column(UUID(as_uuid=False), nullable=False)

    # numeric scores -100..100
    trust = Column(Float, default=0.0)
    affection = Column(Float, default=0.0)
    fear = Column(Float, default=0.0)

    # "estranged", "close", "conflict"
    status = Column(String(50), default="neutral")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_relationship_novel", "novel_id"),
        Index("ix_relationship_pair", "character_a", "character_b"),
    )


# ─── Timeline Projection ──────────────────────────────────────────────────────

class TimelineProjection(Base):
    """chronological narrative events"""

    __tablename__ = "timeline_projection"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    chapter_id = Column(UUID(as_uuid=False), nullable=False)
    scene_id = Column(UUID(as_uuid=False), nullable=False)
    sequence = Column(Integer, nullable=False)

    # e.g. "day 3, evening"
    narrative_time = Column(String(100))
    event_type = Column(String(100))
    event_summary = Column(Text)
    characters = Column(ARRAY(Text), default=list)

    __table_args__ = (
        Index("ix_timeline_chapter", "chapter_id", "scene_id", "sequence"),
    )


# ─── Retrieval Projection ─────────────────────────────────────────────────────

class RetrievalProjection(Base):
    """for RAG"""

    __tablename__ = "retrieval_projection"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    scene_id = Column(UUID(as_uuid=False), nullable=False, unique=True)
    chapter_id = Column(UUID(as_uuid=False), nullable=False)
    one_line = Column(Text)
    keywords = Column(ARRAY(Text), default=list)
    block_types = Column(ARRAY(Text), default=list)  # which block types appear

    __table_args__ = (
        Index("ix_retrieval_scene", "scene_id"),
    )