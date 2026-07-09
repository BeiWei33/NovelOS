"""RewriteSample API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from database.models.rewrite_sample import RewriteSample
from services.rewrite_sample_service import (
    create_rewrite_sample,
    list_rewrite_samples,
    delete_rewrite_sample,
)

router = APIRouter(prefix="/samples", tags=["samples"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sample(
    novel_id: str | None = None,
    input_text: str = "",
    output_text: str = "",
    tags: list[str] = [],
    style_tags: list[str] = [],
    db: AsyncSession = Depends(get_session),
):
    """Create a new rewrite sample."""
    if not input_text or not output_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="input_text and output_text required")

    sample = await create_rewrite_sample(db, input_text, output_text, tags, style_tags, novel_id)
    return {
        "id": sample.id,
        "input": sample.input_text,
        "output": sample.output_text,
        "tags": sample.tags,
        "style_tags": sample.style_tags,
    }


@router.get("")
async def list_samples(
    novel_id: str | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """List rewrite samples."""
    samples = await list_rewrite_samples(db, novel_id, tag)
    return [
        {
            "id": s.id,
            "input": s.input_text,
            "output": s.output_text,
            "tags": s.tags,
            "style_tags": s.style_tags,
        }
        for s in samples
    ]


@router.delete("/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sample(
    sample_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a rewrite sample."""
    deleted = await delete_rewrite_sample(db, sample_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")