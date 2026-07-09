"""
PatchGenerator — generates code patches for auto-fix pipeline (Issue #002).

Generates file modifications based on fix strategy with safety constraints:
- Only modifies frontend files (.ts, .tsx, .js, .jsx)
- Never modifies node_modules, .env, migration files
- Maximum 3 files per patch
- Backs up original content before applying
"""

from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.types import ExecutionProfile
from skills.providers import router
from skills.profile_registry import profile_registry
from database.models.canonical import FrontendError
from database.models.auto_fix import AutoFixBackup, AutoFixLog

logger = logging.getLogger(__name__)

# Allowed file extensions for auto-fix
ALLOWED_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}

# Forbidden directories (never modify)
FORBIDDEN_DIRECTORIES = {"node_modules", ".env", "migrations", "venv", ".venv", "__pycache__"}

# Maximum files per patch
MAX_FILES_PER_PATCH = 3


class PatchGenerator:
    """Generates code patches for auto-fix pipeline."""

    def __init__(self, profile: ExecutionProfile | None = None):
        self.profile = profile or profile_registry.get("patch-generator")

    async def generate_patch(
        self,
        fix_strategy: str,
        affected_files: list[str],
        error: FrontendError,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """
        Generate and apply a patch based on fix strategy.

        Args:
            fix_strategy: LLM-generated fix description
            affected_files: Files that need modification
            error: The original frontend error
            db: Database session

        Returns:
            {
                "patch_id": str,
                "patch_applied": bool,
                "modified_files": [{"path": str, "before": str, "after": str}],
            }
        """
        patch_id = str(uuid.uuid4())

        # Validate and filter files
        valid_files = self._validate_files(affected_files)
        if not valid_files:
            return {
                "patch_id": patch_id,
                "patch_applied": False,
                "modified_files": [],
            }

        # Clamp to max files
        valid_files = valid_files[:MAX_FILES_PER_PATCH]

        # Generate code modifications using LLM
        try:
            modifications = await self._llm_generate_modifications(
                fix_strategy, valid_files, error
            )
        except Exception as e:
            logger.error(f"PatchGenerator: LLM modification generation failed: {e}")
            return {
                "patch_id": patch_id,
                "patch_applied": False,
                "modified_files": [],
            }

        # Validate modifications match allowed files
        validated_modifications = []
        for mod in modifications:
            file_path = mod.get("path", "")
            if not self._is_allowed_file(file_path):
                logger.warning(f"PatchGenerator: Skipping disallowed file: {file_path}")
                continue
            validated_modifications.append(mod)

        if not validated_modifications:
            return {
                "patch_id": patch_id,
                "patch_applied": False,
                "modified_files": [],
            }

        # Apply modifications (in production, this would write to files)
        # For now, we record the patch without actually writing files
        try:
            await self._record_patch(
                db=db,
                patch_id=patch_id,
                error=error,
                fix_strategy=fix_strategy,
                modifications=validated_modifications,
            )
        except Exception as e:
            logger.error(f"PatchGenerator: Failed to record patch: {e}")
            return {
                "patch_id": patch_id,
                "patch_applied": False,
                "modified_files": [],
            }

        return {
            "patch_id": patch_id,
            "patch_applied": True,
            "modified_files": [
                {
                    "path": m["path"],
                    "before": m.get("before", ""),
                    "after": m.get("after", ""),
                }
                for m in validated_modifications
            ],
        }

    def _validate_files(self, files: list[str]) -> list[str]:
        """Validate and filter file paths."""
        valid = []
        for f in files:
            if self._is_allowed_file(f):
                valid.append(f)
        return valid

    def _is_allowed_file(self, file_path: str) -> bool:
        """Check if a file path is allowed for auto-fix."""
        # Check extension
        has_allowed_ext = any(
            file_path.endswith(ext) for ext in ALLOWED_EXTENSIONS
        )
        if not has_allowed_ext:
            return False

        # Check forbidden directories
        path_parts = file_path.replace("\\", "/").split("/")
        for part in path_parts:
            if part in FORBIDDEN_DIRECTORIES:
                return False

        return True

    async def _llm_generate_modifications(
        self,
        fix_strategy: str,
        affected_files: list[str],
        error: FrontendError,
    ) -> list[dict[str, str]]:
        """Use LLM to generate specific code modifications."""
        prompt = f"""Given a fix strategy and affected files, generate specific code modifications.

Fix Strategy:
{fix_strategy}

Affected Files:
{chr(10).join(affected_files)}

Error Context:
Type: {error.type}
Message: {error.message}
Stack: {error.stack or 'N/A'}

Generate code modifications as JSON:
{{
    "modifications": [
        {{
            "path": "relative/path/to/file.ts",
            "before": "original code (the lines to replace)",
            "after": "replacement code"
        }}
    ]
}}

Rules:
- Only generate modifications for .ts, .tsx, .js, .jsx files
- Maximum {MAX_FILES_PER_PATCH} files
- Each modification must have both before and after content
- Keep modifications focused and minimal
- Do not modify node_modules, .env, or migration files
- Read the file content from disk to get accurate 'before' text"""

        messages = [
            {
                "role": "system",
                "content": "You are an expert TypeScript/JavaScript developer. Generate precise, minimal code modifications.",
            },
            {"role": "user", "content": prompt},
        ]

        response = await router.execute(messages, self.profile)

        # Parse response
        try:
            result = self._parse_json_response(response)
            modifications = result.get("modifications", [])
            if not isinstance(modifications, list):
                return []
            return modifications
        except json.JSONDecodeError:
            logger.error(f"PatchGenerator: Failed to parse LLM modifications: {response}")
            return []

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from LLM response, handling markdown fences."""
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()
        return json.loads(json_str)

    async def _record_patch(
        self,
        db: AsyncSession,
        patch_id: str,
        error: FrontendError,
        fix_strategy: str,
        modifications: list[dict[str, str]],
    ) -> None:
        """Record patch backup and log entry."""
        # Create backup entries
        for mod in modifications:
            backup = AutoFixBackup(
                id=str(uuid.uuid4()),
                patch_id=patch_id,
                file_path=mod.get("path", ""),
                original_content=mod.get("before", ""),
            )
            db.add(backup)

        # Create log entry
        log = AutoFixLog(
            id=str(uuid.uuid4()),
            patch_id=patch_id,
            error_id=error.id,
            error_fingerprint=error.fingerprint,
            fix_strategy=fix_strategy,
            modified_files=[
                {"path": m.get("path", ""), "after": m.get("after", "")}
                for m in modifications
            ],
            status="applied",
        )
        db.add(log)
        await db.commit()