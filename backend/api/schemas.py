"""
Pydantic schemas for API request/response serialization.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ─── Novel ────────────────────────────────────────────────────────────────────

class NovelCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class NovelRead(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NovelList(BaseModel):
    novels: list[NovelRead]


# ─── Chapter ──────────────────────────────────────────────────────────────────

class ChapterCreate(BaseModel):
    novel_id: str
    order: int
    title: str = Field(..., min_length=1, max_length=255)
    planning: dict[str, Any] = Field(default_factory=dict)


class ChapterRead(BaseModel):
    id: str
    novel_id: str
    order: int
    title: str
    planning: dict[str, Any]
    summary: dict[str, Any]
    consistency: dict[str, Any]
    chapter_facts: dict[str, Any]
    metadata_: dict[str, Any] = Field(alias="metadata")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


# ─── Scene ────────────────────────────────────────────────────────────────────

class SceneBlock(BaseModel):
    id: str = ""
    type: str = "narration"  # narration, dialogue, description, inner_monologue, emotion, ...
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SceneDocument(BaseModel):
    blocks: list[SceneBlock] = Field(default_factory=list)


class SceneCreate(BaseModel):
    chapter_id: str
    order: int
    planning: dict[str, Any] = Field(default_factory=dict)
    document: SceneDocument = Field(default_factory=SceneDocument)


class SceneRead(BaseModel):
    id: str
    chapter_id: str
    order: int
    version: int
    planning: dict[str, Any]
    document: dict[str, Any]
    body_history: dict[str, Any]
    provenance: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SceneUpdate(BaseModel):
    document: Optional[SceneDocument] = None
    planning: Optional[dict[str, Any]] = None


# ─── Character ────────────────────────────────────────────────────────────────

class CharacterCreate(BaseModel):
    novel_id: str
    name: str = Field(..., min_length=1, max_length=255)
    age: Optional[int] = None
    occupation: Optional[str] = None
    personality: list[str] = Field(default_factory=list)
    goal: Optional[str] = None
    fear: Optional[str] = None
    habit: list[str] = Field(default_factory=list)
    speech_style: Optional[str] = None


class CharacterRead(BaseModel):
    id: str
    novel_id: str
    name: str
    age: Optional[int]
    occupation: Optional[str]
    personality: list[str]
    goal: Optional[str]
    fear: Optional[str]
    habit: list[str]
    speech_style: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── World ────────────────────────────────────────────────────────────────────

class WorldCreate(BaseModel):
    novel_id: str
    name: str = Field(..., min_length=1, max_length=255)
    config: dict[str, Any] = Field(default_factory=dict)


class WorldRead(BaseModel):
    id: str
    novel_id: str
    name: str
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Style ────────────────────────────────────────────────────────────────────

class StyleCreate(BaseModel):
    novel_id: str
    name: str = Field(..., min_length=1, max_length=255)
    profile: dict[str, Any] = Field(default_factory=dict)


class StyleRead(BaseModel):
    id: str
    novel_id: str
    name: str
    profile: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Planning ───────────────────────────────────────────────────────────────────

class ScenePlanningInput(BaseModel):
    goal: str = ""
    theme: str = ""