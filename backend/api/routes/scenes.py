"""Scene routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select

from database.session import get_session
from database.models.canonical import Scene, SceneArtifact
from services.artifact_service import run_artifact_service, run_projection_builder
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

    # Auto-trigger artifact pipeline if document was updated
    if data.document is not None:
        await run_artifact_service(db, scene)
        # Re-fetch to include artifact version
        await db.refresh(scene)

    return scene


@router.get("/{scene_id}/knowledge-status", response_model=dict)
async def get_knowledge_status(
    scene_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Check knowledge layer status: artifacts generated, stale, or missing."""
    scene = await crud.get_scene(db, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    art_result = await db.execute(
        sa_select(SceneArtifact).where(SceneArtifact.scene_id == scene_id)
    )
    artifact = art_result.scalar_one_or_none()

    if artifact is None:
        return {
            "scene_id": scene_id,
            "status": "not_generated",
            "scene_version": scene.version,
            "artifact_version": None,
        }

    is_stale = artifact.scene_version != scene.version

    return {
        "scene_id": scene_id,
        "status": "stale" if is_stale else "up_to_date",
        "scene_version": scene.version,
        "artifact_version": artifact.scene_version,
        "keyword_count": len(artifact.keywords or []),
        "entity_count": len(artifact.entities or []),
        "block_count": len(artifact.narrative_events or []),
    }


@router.get("", response_model=list[schemas.SceneRead])
async def list_scenes(chapter_id: str, db: AsyncSession = Depends(get_session)):
    return await crud.list_scenes(db, chapter_id)