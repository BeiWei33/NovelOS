"""
Quality Pipeline — orchestrates SceneEditor + ConsistencyChecker.

在 SceneWriter 输出初稿后，串行执行两个质量步骤。
"""

from __future__ import annotations
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from skills.base import registry
from skills.scene_editor import SceneEditorSkill, DESLOP_RULES
from skills.consistency_checker import (
    ConsistencyCheckerSkill,
    build_consistency_checker_context,
)
from database.models.canonical import Scene


async def run_quality_pipeline(
    db: AsyncSession,
    scene: Scene,
) -> dict[str, Any]:
    """Run SceneEditor → ConsistencyChecker pipeline on a scene.

    Returns:
        {
            "patches": [...],        # From SceneEditor
            "issues": [...],         # From ConsistencyChecker
            "editor_provenance": {},
            "checker_provenance": {},
        }
    """
    result: dict[str, Any] = {
        "patches": [],
        "issues": [],
        "editor_provenance": {},
        "checker_provenance": {},
    }

    # Step 1: SceneEditor (去AI味)
    editor_skill = registry.get("SceneEditor")
    if editor_skill:
        document = scene.document or {"blocks": []}
        editor_context = {
            "document": document,
            "rules": DESLOP_RULES,
            "character_names": [],  # Will be populated if needed
        }
        editor_result = await editor_skill.execute(editor_context)
        result["patches"] = editor_result.get("patches", [])
        result["editor_provenance"] = editor_result.get("provenance", {})

    # Step 2: ConsistencyChecker
    checker_skill = registry.get("ConsistencyChecker")
    if checker_skill:
        checker_context = await build_consistency_checker_context(db, scene.id)
        checker_result = await checker_skill.execute(checker_context)
        result["issues"] = checker_result.get("issues", [])
        result["checker_provenance"] = checker_result.get("provenance", {})

    return result


def apply_patches(document: dict[str, Any], patches: list[dict]) -> dict[str, Any]:
    """Apply patches to a scene document.

    Args:
        document: SceneDocument with blocks
        patches: List of patch operations

    Returns:
        Modified document
    """
    blocks = list(document.get("blocks", []))

    for patch in patches:
        op = patch.get("op")
        block_index = patch.get("block_index")
        old_text = patch.get("old_text", "")
        new_text = patch.get("new_text", "")

        if block_index is None or block_index >= len(blocks):
            continue

        block = blocks[block_index]
        content = block.get("content", "")

        if op == "replace":
            # Replace old_text with new_text in block content
            if old_text and old_text in content:
                block["content"] = content.replace(old_text, new_text, 1)
        elif op == "delete":
            # Delete old_text from block content
            if old_text and old_text in content:
                block["content"] = content.replace(old_text, "", 1)
        elif op == "insert":
            # Insert new_text at position (after old_text or at end)
            if old_text and old_text in content:
                block["content"] = content.replace(old_text, old_text + new_text, 1)
            else:
                block["content"] = content + new_text

    return {"blocks": blocks}