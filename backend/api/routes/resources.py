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


# ─── Worlds ───────────────────────────────────────────────────────────────────

@router.post("/worlds", response_model=schemas.WorldRead, status_code=status.HTTP_201_CREATED)
async def create_world(data: schemas.WorldCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_world(db, data)


@router.get("/worlds", response_model=list[schemas.WorldRead])
async def list_worlds(novel_id: str, db: AsyncSession = Depends(get_session)):
    return await crud.list_worlds(db, novel_id)


# ─── Styles ───────────────────────────────────────────────────────────────────

@router.post("/styles", response_model=schemas.StyleRead, status_code=status.HTTP_201_CREATED)
async def create_style(data: schemas.StyleCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_style(db, data)


@router.get("/styles", response_model=list[schemas.StyleRead])
async def list_styles(novel_id: str, db: AsyncSession = Depends(get_session)):
    return await crud.list_styles(db, novel_id)