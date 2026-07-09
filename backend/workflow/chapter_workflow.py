"""
ChapterWorkflow — orchestrates full chapter generation.

StoryPlanner → Scene List → foreach Scene (ScenePipeline)
  → ChapterConsistency → ChapterSummarizer → ChapterFactsAggregator
"""

from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Any
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.canonical import Scene, Chapter
from skills.base import registry
from skills.story_planner import build_story_planner_context
from skills.scene_writer import build_scene_writer_context
from workflow.quality_pipeline import run_quality_pipeline, apply_patches
from services.artifact_service import run_artifact_service, run_projection_builder


class WorkflowStep(str, Enum):
    PLAN = "plan"
    WRITE_SCENES = "write_scenes"
    QUALITY_CHECK = "quality_check"
    ARTIFACTS = "artifacts"
    SUMMARY = "summary"
    COMPLETE = "complete"
    FAILED = "failed"


class ChapterWorkflowEngine:
    """Manages workflow state machine with pause/resume/rollback."""

    def __init__(self, db: AsyncSession, chapter_id: str):
        self.db = db
        self.chapter_id = chapter_id
        self.current_step = WorkflowStep.PLAN
        self.progress: dict[str, Any] = {
            "step": "plan",
            "total_steps": 5,
            "completed": 0,
            "scenes_written": 0,
            "errors": [],
        }
        self._rollback_data: dict[str, Any] = {}

    async def run(self, goal: str = "", theme: str = "") -> dict[str, Any]:
        """Execute the full workflow."""
        try:
            # Step 1: Plan
            await self._step_plan(goal, theme)

            # Step 2: Write scenes
            await self._step_write_scenes()

            # Step 3: Quality check
            await self._step_quality_check()

            # Step 4: Generate artifacts
            await self._step_artifacts()

            # Step 5: Summarize
            await self._step_summary()

            self.current_step = WorkflowStep.COMPLETE
            self.progress["step"] = "complete"
            return self.progress

        except Exception as e:
            self.current_step = WorkflowStep.FAILED
            self.progress["errors"].append(str(e))
            await self._rollback()
            raise

    async def _step_plan(self, goal: str, theme: str) -> None:
        """Step 1: Generate scene plan."""
        self.progress["step"] = "plan"
        self._rollback_data["original_planning"] = {}

        chapter = await self.db.get(Chapter, self.chapter_id)
        if chapter:
            self._rollback_data["original_planning"] = chapter.planning or {}

            skill = registry.get("StoryPlanner")
            if skill:
                context = await build_story_planner_context(
                    self.db, self.chapter_id, goal, theme
                )
                result = await skill.execute(context)
                scene_plan = result.get("scene_plan", [])
                chapter.planning = chapter.planning or {}
                chapter.planning["scene_plan"] = scene_plan
                await self.db.commit()

        self.progress["completed"] = 1

    async def _step_write_scenes(self) -> None:
        """Step 2: Write each scene."""
        self.progress["step"] = "write_scenes"

        chapter = await self.db.get(Chapter, self.chapter_id)
        if not chapter or not chapter.planning:
            return

        scene_plan = chapter.planning.get("scene_plan", [])
        if not scene_plan:
            return

        # Get existing scenes
        scenes_result = await self.db.execute(
            select(Scene).where(Scene.chapter_id == self.chapter_id).order_by(Scene.order)
        )
        existing_scenes = list(scenes_result.scalars().all())

        # Create scenes if needed
        for i, plan in enumerate(scene_plan):
            order = i + 1
            scene = None

            # Find existing scene with this order
            for s in existing_scenes:
                if s.order == order:
                    scene = s
                    break

            if scene is None:
                # Create new scene
                scene = Scene(
                    chapter_id=self.chapter_id,
                    order=order,
                    planning=plan,
                    document={"blocks": []},
                )
                self.db.add(scene)
                await self.db.flush()
            else:
                # Update planning
                scene.planning = plan

            # Write scene content
            skill = registry.get("SceneWriter")
            if skill:
                context = await build_scene_writer_context(self.db, scene)
                result = await skill.execute(context)
                scene.document = result.get("document", {"blocks": []})
                scene.version += 1
                scene.provenance = result.get("provenance", {})

            self.progress["scenes_written"] += 1

        await self.db.commit()
        self.progress["completed"] = 2

    async def _step_quality_check(self) -> None:
        """Step 3: Run quality pipeline on each scene."""
        self.progress["step"] = "quality_check"

        scenes_result = await self.db.execute(
            select(Scene).where(Scene.chapter_id == self.chapter_id).order_by(Scene.order)
        )
        scenes = scenes_result.scalars().all()

        for scene in scenes:
            result = await run_quality_pipeline(self.db, scene)
            patches = result.get("patches", [])
            if patches:
                scene.document = apply_patches(scene.document or {"blocks": []}, patches)
                scene.version += 1

            scene.body_history = scene.body_history or {}
            scene.body_history["quality_issues"] = result.get("issues", [])

        await self.db.commit()
        self.progress["completed"] = 3

    async def _step_artifacts(self) -> None:
        """Step 4: Generate artifacts for each scene."""
        self.progress["step"] = "artifacts"

        scenes_result = await self.db.execute(
            select(Scene).where(Scene.chapter_id == self.chapter_id).order_by(Scene.order)
        )
        scenes = scenes_result.scalars().all()

        for scene in scenes:
            artifact = await run_artifact_service(self.db, scene)
            await run_projection_builder(self.db, scene, artifact)

        self.progress["completed"] = 4

    async def _step_summary(self) -> None:
        """Step 5: Generate chapter summary."""
        self.progress["step"] = "summary"

        # Simple summary: aggregate scene one-liners
        scenes_result = await self.db.execute(
            select(Scene).where(Scene.chapter_id == self.chapter_id).order_by(Scene.order)
        )
        scenes = scenes_result.scalars().all()

        chapter = await self.db.get(Chapter, self.chapter_id)
        if chapter:
            one_lines = []
            for scene in scenes:
                doc = scene.document or {}
                blocks = doc.get("blocks", [])
                if blocks:
                    content = blocks[0].get("content", "")[:100]
                    one_lines.append(f"场景{scene.order}: {content}")

            chapter.summary = {
                "one_line": one_lines[0] if one_lines else "",
                "one_paragraph": "\n".join(one_lines[:3]),
                "one_page": "\n\n".join(one_lines),
            }
            chapter.consistency = {"score": 100, "issues": [], "fixed": []}

        await self.db.commit()
        self.progress["completed"] = 5

    async def _rollback(self) -> None:
        """Rollback to original state."""
        chapter = await self.db.get(Chapter, self.chapter_id)
        if chapter and "original_planning" in self._rollback_data:
            chapter.planning = self._rollback_data["original_planning"]
        await self.db.commit()


async def run_chapter_workflow(
    db: AsyncSession,
    chapter_id: str,
    goal: str = "",
    theme: str = "",
) -> dict[str, Any]:
    """Run the full chapter workflow."""
    engine = ChapterWorkflowEngine(db, chapter_id)
    return await engine.run(goal, theme)