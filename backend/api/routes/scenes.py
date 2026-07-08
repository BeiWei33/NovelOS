"""Scene routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from api import schemas, crud

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("", response_model=schemas.SceneRead, status_code=status.HTTP_201_CREATED)
async def create_scene(data: schemas.SceneCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_scene(db, data)


@router.get("/{scene_id}", response_model=schemas.SceneRead)
async def get_scene(scene_id: str, db: AsyncSession = Depends(get_session)):
    scene = await crud.get_scene(db, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    return scene


@router.put("/{scene_id}", response_model=schemas.SceneRead)
async def update_scene(
    scene_id: str,
    data: schemas.SceneUpdate,
    db: AsyncSession = Depends(get_session),
):
    scene = await crud.update_scene(db, scene_id, data)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    return scene


@router.get("", response_model=list[schemas.SceneRead])
async def list_scenes(chapter_id: str, db: AsyncSession = Depends(get_session)):
    return await crud.list_scenes(db, chapter_id)