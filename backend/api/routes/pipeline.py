"""
Artifact and data pipeline routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from database.models.canonical import Scene, SceneArtifact
from services.artifact_service import run_artifact_service, run_projection_builder

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/artifacts/{scene_id}")
async def generate_artifacts(
    scene_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Run artifact extraction on a scene."""
    scene = await db.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    artifact = await run_artifact_service(db, scene)
    return {
        "scene_id": scene.id,
        "scene_version": scene.version,
        "artifact_version": artifact.scene_version,
        "summary": artifact.summary,
        "keyword_count": len(artifact.keywords or []),
        "entity_count": len(artifact.entities or []),
    }


@router.post("/projections/{scene_id}")
async def build_projections(
    scene_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Rebuild projections from artifacts."""
    scene = await db.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    # Check artifact exists
    art_result = await db.execute(
        sa_select(SceneArtifact).where(SceneArtifact.scene_id == scene_id)
    )
    artifact = art_result.scalar_one_or_none()
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Artifacts not generated yet. POST /pipeline/artifacts/{scene_id} first",
        )

    await run_projection_builder(db, scene, artifact)
    return {"scene_id": scene.id, "status": "projections rebuilt"}


@router.post("/full/{scene_id}")
async def run_full_pipeline(scene_id: str, db: AsyncSession = Depends(get_session)):
    """Run artifact extraction + projection rebuild in one call."""
    scene = await db.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    artifact = await run_artifact_service(db, scene)
    await run_projection_builder(db, scene, artifact)

    return {
        "scene_id": scene.id,
        "status": "pipeline complete",
        "artifact_version": artifact.scene_version,
    }