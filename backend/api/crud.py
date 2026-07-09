"""
CRUD operations for Canonical Layer models.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.canonical import (
    Novel, Chapter, Scene, Character, World, Style, NarrativeEvent,
)
from api import schemas


# ─── Novel ────────────────────────────────────────────────────────────────────

async def create_novel(db: AsyncSession, data: schemas.NovelCreate) -> Novel:
    novel = Novel(title=data.title)
    db.add(novel)
    await db.commit()
    await db.refresh(novel)
    return novel


async def get_novel(db: AsyncSession, novel_id: str) -> Optional[Novel]:
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    return result.scalar_one_or_none()


async def list_novels(db: AsyncSession) -> list[Novel]:
    result = await db.execute(select(Novel).order_by(Novel.updated_at.desc()))
    return list(result.scalars().all())


async def delete_novel(db: AsyncSession, novel_id: str) -> bool:
    novel = await get_novel(db, novel_id)
    if novel is None:
        return False
    await db.delete(novel)
    await db.commit()
    return True


# ─── Chapter ──────────────────────────────────────────────────────────────────

async def create_chapter(db: AsyncSession, data: schemas.ChapterCreate) -> Chapter:
    chapter = Chapter(
        novel_id=data.novel_id,
        order=data.order,
        title=data.title,
        planning=data.planning,
    )
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    return chapter


async def get_chapter(db: AsyncSession, chapter_id: str) -> Optional[Chapter]:
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    return result.scalar_one_or_none()


async def list_chapters(db: AsyncSession, novel_id: str) -> list[Chapter]:
    result = await db.execute(
        select(Chapter)
        .where(Chapter.novel_id == novel_id)
        .order_by(Chapter.order)
    )
    return list(result.scalars().all())


async def delete_chapter(db: AsyncSession, chapter_id: str) -> bool:
    chapter = await get_chapter(db, chapter_id)
    if chapter is None:
        return False
    await db.delete(chapter)
    await db.commit()
    return True


# ─── Scene ────────────────────────────────────────────────────────────────────

async def create_scene(db: AsyncSession, data: schemas.SceneCreate) -> Scene:
    doc = data.document.model_dump() if data.document else {"blocks": []}
    scene = Scene(
        chapter_id=data.chapter_id,
        order=data.order,
        planning=data.planning,
        document=doc,
    )
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return scene


async def get_scene(db: AsyncSession, scene_id: str) -> Optional[Scene]:
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    return result.scalar_one_or_none()


async def list_scenes(db: AsyncSession, chapter_id: str) -> list[Scene]:
    result = await db.execute(
        select(Scene)
        .where(Scene.chapter_id == chapter_id)
        .order_by(Scene.order)
    )
    return list(result.scalars().all())


async def update_scene(
    db: AsyncSession,
    scene_id: str,
    data: schemas.SceneUpdate,
) -> Optional[Scene]:
    scene = await get_scene(db, scene_id)
    if scene is None:
        return None

    if data.document is not None:
        scene.document = data.document.model_dump()
        scene.version += 1
        scene.body_history = scene.body_history or {}
        scene.body_history["edited"] = scene.document
        scene.updated_at = datetime.utcnow()

    if data.planning is not None:
        scene.planning = data.planning
        scene.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(scene)
    return scene


# ─── Character ────────────────────────────────────────────────────────────────

async def create_character(db: AsyncSession, data: schemas.CharacterCreate) -> Character:
    char = Character(
        novel_id=data.novel_id,
        name=data.name,
        age=data.age,
        occupation=data.occupation,
        personality=data.personality,
        goal=data.goal,
        fear=data.fear,
        habit=data.habit,
        speech_style=data.speech_style,
    )
    db.add(char)
    await db.commit()
    await db.refresh(char)
    return char


async def list_characters(db: AsyncSession, novel_id: str) -> list[Character]:
    result = await db.execute(
        select(Character).where(Character.novel_id == novel_id)
    )
    return list(result.scalars().all())


async def delete_character(db: AsyncSession, character_id: str) -> bool:
    char = await db.execute(select(Character).where(Character.id == character_id))
    char = char.scalar_one_or_none()
    if char is None:
        return False
    await db.delete(char)
    await db.commit()
    return True


async def update_character(
    db: AsyncSession,
    character_id: str,
    data: schemas.CharacterUpdate,
) -> Optional[Character]:
    char = await db.execute(select(Character).where(Character.id == character_id))
    char = char.scalar_one_or_none()
    if char is None:
        return None

    if data.name is not None:
        char.name = data.name
    if data.age is not None:
        char.age = data.age
    if data.occupation is not None:
        char.occupation = data.occupation
    if data.personality is not None:
        char.personality = data.personality
    if data.goal is not None:
        char.goal = data.goal
    if data.fear is not None:
        char.fear = data.fear
    if data.habit is not None:
        char.habit = data.habit
    if data.speech_style is not None:
        char.speech_style = data.speech_style
    char.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(char)
    return char


# ─── World ────────────────────────────────────────────────────────────────────

async def create_world(db: AsyncSession, data: schemas.WorldCreate) -> World:
    world = World(novel_id=data.novel_id, name=data.name, config=data.config)
    db.add(world)
    await db.commit()
    await db.refresh(world)
    return world


async def list_worlds(db: AsyncSession, novel_id: str) -> list[World]:
    result = await db.execute(
        select(World).where(World.novel_id == novel_id)
    )
    return list(result.scalars().all())


async def delete_world(db: AsyncSession, world_id: str) -> bool:
    world = await db.execute(select(World).where(World.id == world_id))
    world = world.scalar_one_or_none()
    if world is None:
        return False
    await db.delete(world)
    await db.commit()
    return True


async def update_world(
    db: AsyncSession,
    world_id: str,
    data: schemas.WorldUpdate,
) -> Optional[World]:
    world = await db.execute(select(World).where(World.id == world_id))
    world = world.scalar_one_or_none()
    if world is None:
        return None

    if data.name is not None:
        world.name = data.name
    if data.config is not None:
        world.config = data.config
    world.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(world)
    return world


# ─── Style ────────────────────────────────────────────────────────────────────

async def create_style(db: AsyncSession, data: schemas.StyleCreate) -> Style:
    style = Style(novel_id=data.novel_id, name=data.name, profile=data.profile)
    db.add(style)
    await db.commit()
    await db.refresh(style)
    return style


async def list_styles(db: AsyncSession, novel_id: str) -> list[Style]:
    result = await db.execute(
        select(Style).where(Style.novel_id == novel_id)
    )
    return list(result.scalars().all())


async def delete_style(db: AsyncSession, style_id: str) -> bool:
    style = await db.execute(select(Style).where(Style.id == style_id))
    style = style.scalar_one_or_none()
    if style is None:
        return False
    await db.delete(style)
    await db.commit()
    return True


async def update_style(
    db: AsyncSession,
    style_id: str,
    data: schemas.StyleUpdate,
) -> Optional[Style]:
    style = await db.execute(select(Style).where(Style.id == style_id))
    style = style.scalar_one_or_none()
    if style is None:
        return None

    if data.name is not None:
        style.name = data.name
    if data.profile is not None:
        style.profile = data.profile
    style.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(style)
    return style