"""
Canonical Layer models — the single source of truth.

These tables are append-only for versions.
Only Chapter and Scene are user-editable.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, ForeignKey, DateTime, Text, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from database.session import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.utcnow()


# ─── Novel ────────────────────────────────────────────────────────────────────

class Novel(Base):
    __tablename__ = "novel"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    chapters = relationship("Chapter", back_populates="novel", order_by="Chapter.order")
    characters = relationship("Character", back_populates="novel")
    worlds = relationship("World", back_populates="novel")
    styles = relationship("Style", back_populates="novel")


# ─── Chapter ──────────────────────────────────────────────────────────────────

class Chapter(Base):
    __tablename__ = "chapter"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    novel_id = Column(UUID(as_uuid=False), ForeignKey("novel.id"), nullable=False)
    order = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)

    # planning: {goal, theme, scene_plan: []}
    planning = Column(JSONB, default=dict, nullable=False)

    # summary: {one_page, one_paragraph, one_line}
    summary = Column(JSONB, default=dict, nullable=False)

    # consistency: {score, issues, fixed, warnings}
    consistency = Column(JSONB, default=dict, nullable=False)

    # chapter_facts: {relationship_changes, world_changes, timeline_changes, new_information}
    chapter_facts = Column(JSONB, default=dict, nullable=False)

    # metadata: {status: "draft" | "written" | "edited" | "frozen"}
    metadata_ = Column("metadata", JSONB, default=lambda: {"status": "draft"}, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    novel = relationship("Novel", back_populates="chapters")
    scenes = relationship("Scene", back_populates="chapter", order_by="Scene.order")

    __table_args__ = (
        Index("ix_chapter_novel_order", "novel_id", "order", unique=True),
    )


# ─── Scene ────────────────────────────────────────────────────────────────────

class Scene(Base):
    """The sole transaction boundary — an indivisible narrative transaction."""

    __tablename__ = "scene"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    chapter_id = Column(UUID(as_uuid=False), ForeignKey("chapter.id"), nullable=False)
    order = Column(Integer, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # planning: {goal, conflict, stakes, turning_point, ending, foreshadow}
    planning = Column(JSONB, default=dict, nullable=False)

    # document: SceneDocument (Domain AST) — JSONB
    #   blocks: [{id, type, content, metadata}]
    document = Column(JSONB, default=lambda: {"blocks": []}, nullable=False)

    # body_history: {draft, edited, published}
    body_history = Column(JSONB, default=dict, nullable=False)

    # provenance: {execution_role, execution_profile, provider, model, temperature, tokens, duration_ms, version, status}
    provenance = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    chapter = relationship("Chapter", back_populates="scenes")
    artifacts = relationship("SceneArtifact", back_populates="scene", uselist=False)
    narrative_events = relationship("NarrativeEvent", back_populates="scene")

    __table_args__ = (
        Index("ix_scene_chapter_order", "chapter_id", "order", unique=True),
    )


# ─── Character ────────────────────────────────────────────────────────────────

class Character(Base):
    __tablename__ = "character"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    novel_id = Column(UUID(as_uuid=False), ForeignKey("novel.id"), nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(Integer)
    occupation = Column(String(255))

    # personality: [trait1, trait2, ...]
    personality = Column(JSONB, default=list, nullable=False)

    goal = Column(Text)
    fear = Column(Text)

    # habit: [description1, description2, ...]
    habit = Column(JSONB, default=list, nullable=False)

    speech_style = Column(Text)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    novel = relationship("Novel", back_populates="characters")


# ─── World ────────────────────────────────────────────────────────────────────

class World(Base):
    __tablename__ = "world"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    novel_id = Column(UUID(as_uuid=False), ForeignKey("novel.id"), nullable=False)
    name = Column(String(255), nullable=False)

    # config: hierarchical world data (locations, organizations, nations, timeline, rules)
    config = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    novel = relationship("Novel", back_populates="worlds")


# ─── Style ────────────────────────────────────────────────────────────────────

class Style(Base):
    __tablename__ = "style"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    novel_id = Column(UUID(as_uuid=False), ForeignKey("novel.id"), nullable=False)
    name = Column(String(255), nullable=False)

    # profile: {dialog_ratio, emotion, sentence, description, psychology, humor, pace, ...}
    profile = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    novel = relationship("Novel", back_populates="styles")


# ─── NarrativeEvent ───────────────────────────────────────────────────────────

class NarrativeEvent(Base):
    """Single source of truth for character state, relationships, consistency."""

    __tablename__ = "narrative_event"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    scene_id = Column(UUID(as_uuid=False), ForeignKey("scene.id"), nullable=False)
    type = Column(String(100), nullable=False)       # e.g. "relationship_change", "reveal", "conflict"
    actor = Column(String(255))                       # character name or entity
    target = Column(String(255))                      # affected character/entity
    payload = Column(JSONB, default=dict, nullable=False)
    sequence = Column(Integer, nullable=False)         # chronological order within scene

    scene = relationship("Scene", back_populates="narrative_events")


# ─── Artifact Layer ───────────────────────────────────────────────────────────

class SceneArtifact(Base):
    """Derived structured knowledge. Regeneratable."""

    __tablename__ = "scene_artifact"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    scene_id = Column(UUID(as_uuid=False), ForeignKey("scene.id"), nullable=False, unique=True)
    scene_version = Column(Integer, nullable=False)

    facts = Column(JSONB, default=dict, nullable=False)
    narrative_events = Column(JSONB, default=list, nullable=False)
    summary = Column(JSONB, default=dict, nullable=False)
    keywords = Column(JSONB, default=list, nullable=False)
    emotion_profile = Column(JSONB, default=dict, nullable=False)
    entities = Column(JSONB, default=list, nullable=False)
    foreshadow_hints = Column(JSONB, default=list, nullable=False)
    timeline_deltas = Column(JSONB, default=list, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)

    scene = relationship("Scene", back_populates="artifacts")


class ChapterArtifact(Base):
    __tablename__ = "chapter_artifact"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    chapter_id = Column(UUID(as_uuid=False), ForeignKey("chapter.id"), nullable=False, unique=True)

    summary = Column(JSONB, default=dict, nullable=False)
    facts = Column(JSONB, default=dict, nullable=False)
    consistency = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)


# ─── FrontendError ────────────────────────────────────────────────────────────

class FrontendError(Base):
    """Structured error reports received from the frontend application."""

    __tablename__ = "frontend_error"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    stack = Column(Text, nullable=True)
    fingerprint = Column(String(64), nullable=False)
    context = Column(JSONB, default=dict, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    analysis_result = Column(JSONB, nullable=True)  # LLM analysis result
    created_at = Column(DateTime, default=utcnow, nullable=False)
