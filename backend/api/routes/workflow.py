"""
Workflow pause/resume routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from database.models.canonical import Chapter

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get("/status/{chapter_id}")
async def get_workflow_status(
    chapter_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Return the persisted workflow state for a chapter, or {} if not started."""
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    planning = chapter.planning or {}
    return planning.get("_workflow_state", {})


@router.post("/pause/{chapter_id}")
async def pause_workflow(
    chapter_id: str,
    db: AsyncSession = Depends(get_session),
):
    """
    Request a pause for the running workflow.

    Writes {"_pause_requested": True} into chapter.planning so the next step
    check can detect it. The engine polls this flag at each step boundary.
    """
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    chapter.planning = chapter.planning or {}
    chapter.planning["_pause_requested"] = True
    await db.commit()

    return {"chapter_id": chapter_id, "pause_requested": True}


@router.post("/resume/{chapter_id}")
async def resume_workflow(
    chapter_id: str,
    db: AsyncSession = Depends(get_session),
):
    """
    Resume a paused workflow from its last checkpoint.

    Clears _pause_requested and returns the current workflow state so the
    caller can re-run the workflow starting from the stored step.
    """
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    planning = chapter.planning or {}
    if not planning.get("_pause_requested"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No pause was requested for this chapter",
        )

    # Clear the pause flag so the re-running engine will not pause immediately
    planning.pop("_pause_requested", None)
    chapter.planning = planning
    await db.commit()

    workflow_state = planning.get("_workflow_state", {})
    return {
        "chapter_id": chapter_id,
        "resumed": True,
        "checkpoint": workflow_state.get("step"),
        "completed_steps": workflow_state.get("completed", 0),
    }
