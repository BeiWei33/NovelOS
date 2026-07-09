"""
Verification module for Auto-Fix Pipeline (Issue #005).

Runs validation checks on patched code:
- TypeScript type checking (tsc --noEmit)
- ESLint checking (npm run lint)
- Unit tests (npm run test)

Automatically triggers rollback if verification fails.
"""

from __future__ import annotations
import asyncio
import logging
import os
import subprocess
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.auto_fix import AutoFixLog
from workflow.git_operations import rollback_patch

logger = logging.getLogger(__name__)

# Verification timeout in seconds
VERIFICATION_TIMEOUT = 300  # 5 minutes

# Commands to run for verification
TSC_COMMAND = ["npx", "tsc", "--noEmit"]
ESLINT_COMMAND = ["npm", "run", "lint"]
TEST_COMMAND = ["npm", "run", "test"]


async def verify_patch(
    patch_id: str,
    db: AsyncSession,
    frontend_dir: str | None = None,
) -> dict[str, Any]:
    """
    Run verification checks on a patch.

    Runs:
    1. TypeScript type checking
    2. ESLint checking
    3. Unit tests

    If any check fails, triggers automatic rollback.

    Args:
        patch_id: UUID of the patch to verify
        db: Database session
        frontend_dir: Path to frontend directory (auto-detected if not provided)

    Returns:
        {
            "verified": bool,
            "results": {
                "tsc": {"passed": bool, "output": str},
                "eslint": {"passed": bool, "output": str},
                "test": {"passed": bool, "output": str},
            }
        }
    """
    results = {
        "tsc": {"passed": False, "output": ""},
        "eslint": {"passed": False, "output": ""},
        "test": {"passed": False, "output": ""},
    }

    # Find frontend directory
    if not frontend_dir:
        frontend_dir = _find_frontend_dir()
    if not frontend_dir:
        logger.error("verify_patch: Could not find frontend directory")
        results["error"] = "Frontend directory not found"
        return {"verified": False, "results": results}

    # Fetch log entry
    result = await db.execute(
        select(AutoFixLog).where(AutoFixLog.patch_id == patch_id)
    )
    log_entry = result.scalar_one_or_none()

    if not log_entry:
        logger.error(f"verify_patch: No log entry found for patch_id {patch_id}")
        return {"verified": False, "results": results}

    # Run verification checks
    try:
        # TypeScript check
        results["tsc"] = await _run_command_async(
            TSC_COMMAND,
            frontend_dir,
            timeout=120,
        )

        # ESLint check
        results["eslint"] = await _run_command_async(
            ESLINT_COMMAND,
            frontend_dir,
            timeout=120,
        )

        # Unit tests
        results["test"] = await _run_command_async(
            TEST_COMMAND,
            frontend_dir,
            timeout=180,
        )

    except asyncio.TimeoutError:
        logger.error("verify_patch: Verification timeout")
        results["error"] = "Verification timeout"

    # Determine overall verification status
    all_passed = (
        results["tsc"]["passed"]
        and results["eslint"]["passed"]
        and results["test"]["passed"]
    )

    # Update log entry
    log_entry.verified = {
        "tsc": results["tsc"]["passed"],
        "eslint": results["eslint"]["passed"],
        "test": results["test"]["passed"],
        "timestamp": datetime.utcnow().isoformat(),
    }

    if all_passed:
        log_entry.status = "verified"
        await db.commit()
        return {"verified": True, "results": results}
    else:
        # Verification failed - trigger rollback
        logger.warning(f"verify_patch: Verification failed for patch {patch_id}. Triggering rollback.")

        rollback_result = await rollback_patch(
            patch_id=patch_id,
            db=db,
            rollback_reason="verification_failed",
        )

        log_entry.status = "rolled_back"
        log_entry.rollback_at = datetime.utcnow()
        await db.commit()

        results["rollback"] = rollback_result
        return {"verified": False, "results": results}


async def _run_command_async(
    command: list[str],
    cwd: str,
    timeout: int = 60,
) -> dict[str, Any]:
    """
    Run a command asynchronously with timeout.

    Args:
        command: Command and arguments as list
        cwd: Working directory
        timeout: Timeout in seconds

    Returns:
        {"passed": bool, "output": str}
    """
    loop = asyncio.get_event_loop()

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )

        output = (stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")).strip()
        passed = process.returncode == 0

        return {"passed": passed, "output": output[-2000:]}  # Truncate output

    except asyncio.TimeoutError:
        return {"passed": False, "output": f"Command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"passed": False, "output": f"Command not found: {command[0]}"}
    except Exception as e:
        return {"passed": False, "output": str(e)}


def _find_frontend_dir() -> str | None:
    """Find the frontend directory in the project."""
    # Start from git root or current directory
    current = os.getcwd()

    # Walk up to find project root (contains frontend/ or package.json)
    while current:
        # Check for frontend directory
        frontend_path = os.path.join(current, "frontend")
        if os.path.isdir(frontend_path):
            return frontend_path

        # Check if this is a frontend directory
        if os.path.exists(os.path.join(current, "package.json")):
            return current

        # Check for package.json in parent directories
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return None
