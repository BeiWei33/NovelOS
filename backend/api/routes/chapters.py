"""Chapter routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from api import schemas, crud

router = APIRouter(prefix="/chapters", tags=["chapters"])


@router.post("", response_model=schemas.ChapterRead, status_code=status.HTTP_201_CREATED)
async def create_chapter(data: schemas.ChapterCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_chapter(db, data)


@router.get("/{chapter_id}", response_model=schemas.ChapterRead)
async def get_chapter(chapter_id: str, db: AsyncSession = Depends(get_session)):
    chapter = await crud.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return chapter


@router.get("", response_model=list[schemas.ChapterRead])
async def list_chapters(novel_id: str, db: AsyncSession = Depends(get_session)):
    return await crud.list_chapters(db, novel_id)


@router.put("/{chapter_id}", response_model=schemas.ChapterRead)
async def update_chapter(chapter_id: str, data: schemas.ChapterUpdate, db: AsyncSession = Depends(get_session)):
    chapter = await crud.update_chapter(db, chapter_id, data)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return chapter


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(chapter_id: str, db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_chapter(db, chapter_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")