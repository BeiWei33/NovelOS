"""Character, World, Style routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from api import schemas, crud

router = APIRouter(tags=["resources"])


# ─── Characters ───────────────────────────────────────────────────────────────

@router.post("/characters", response_model=schemas.CharacterRead, status_code=status.HTTP_201_CREATED)
async def create_character(data: schemas.CharacterCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_character(db, data)


@router.get("/characters", response_model=list[schemas.CharacterRead])
async def list_characters(novel_id: str, db: AsyncSession = Depends(get_session)):
    return await crud.list_characters(db, novel_id)


@router.get("/characters/{character_id}", response_model=schemas.CharacterRead)
async def get_character(character_id: str, db: AsyncSession = Depends(get_session)):
    char = await crud.get_character(db, character_id)
    if char is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return char


@router.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(character_id: str, db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_character(db, character_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")


@router.put("/characters/{character_id}", response_model=schemas.CharacterRead)
async def update_character(character_id: str, data: schemas.CharacterUpdate, db: AsyncSession = Depends(get_session)):
    char = await crud.update_character(db, character_id, data)
    if char is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return char


# ─── Worlds ───────────────────────────────────────────────────────────────────

@router.post("/worlds", response_model=schemas.WorldRead, status_code=status.HTTP_201_CREATED)
async def create_world(data: schemas.WorldCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_world(db, data)


@router.get("/worlds", response_model=list[schemas.WorldRead])
async def list_worlds(novel_id: str, db: AsyncSession = Depends(get_session)):
    return await crud.list_worlds(db, novel_id)


@router.delete("/worlds/{world_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_world(world_id: str, db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_world(db, world_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")


@router.put("/worlds/{world_id}", response_model=schemas.WorldRead)
async def update_world(world_id: str, data: schemas.WorldUpdate, db: AsyncSession = Depends(get_session)):
    world = await crud.update_world(db, world_id, data)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return world


# ─── Styles ───────────────────────────────────────────────────────────────────

@router.post("/styles", response_model=schemas.StyleRead, status_code=status.HTTP_201_CREATED)
async def create_style(data: schemas.StyleCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_style(db, data)


@router.get("/styles", response_model=list[schemas.StyleRead])
async def list_styles(novel_id: str, db: AsyncSession = Depends(get_session)):
    return await crud.list_styles(db, novel_id)


@router.delete("/styles/{style_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_style(style_id: str, db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_style(db, style_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style not found")


@router.put("/styles/{style_id}", response_model=schemas.StyleRead)
async def update_style(style_id: str, data: schemas.StyleUpdate, db: AsyncSession = Depends(get_session)):
    style = await crud.update_style(db, style_id, data)
    if style is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style not found")
    return style