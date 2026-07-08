"""Skill execution routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from database.models.canonical import Scene
from skills.base import registry
from skills.scene_writer import build_scene_writer_context
from api.crud import update_scene
from api.schemas import SceneUpdate, SceneDocument


router = APIRouter(prefix="/skills", tags=["skills"])


@router.post("/scene-writer/{scene_id}")
async def run_scene_writer(
    scene_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Execute SceneWriter skill on a scene. Assembles context, calls LLM, writes result."""
    # Get scene
    scene = await db.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    # Get skill
    skill = registry.get("SceneWriter")
    if skill is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SceneWriter skill not registered")

    # Build context
    context = await build_scene_writer_context(db, scene)

    # Execute
    result = await skill.execute(context)

    # Write result back to scene
    document = result.get("document", {"blocks": []})
    provenance = result.get("provenance", {})

    scene.document = document
    scene.version += 1
    scene.provenance = provenance
    scene.body_history = scene.body_history or {}
    scene.body_history["edited"] = document

    await db.commit()
    await db.refresh(scene)

    return {
        "scene_id": scene.id,
        "version": scene.version,
        "document": scene.document,
        "provenance": scene.provenance,
    }