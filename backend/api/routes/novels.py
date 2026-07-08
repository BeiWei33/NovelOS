"""Novel routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from api import schemas, crud

router = APIRouter(prefix="/novels", tags=["novels"])


@router.post("", response_model=schemas.NovelRead, status_code=status.HTTP_201_CREATED)
async def create_novel(data: schemas.NovelCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_novel(db, data)


@router.get("", response_model=schemas.NovelList)
async def list_novels(db: AsyncSession = Depends(get_session)):
    novels = await crud.list_novels(db)
    return schemas.NovelList(novels=novels)


@router.get("/{novel_id}", response_model=schemas.NovelRead)
async def get_novel(novel_id: str, db: AsyncSession = Depends(get_session)):
    novel = await crud.get_novel(db, novel_id)
    if novel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")
    return novel


@router.delete("/{novel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_novel(novel_id: str, db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_novel(db, novel_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")