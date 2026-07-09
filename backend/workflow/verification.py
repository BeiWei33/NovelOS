"""
Verification module for Auto-Fix Pipeline (Issue #005).

Runs validation checks on patched code:
- TypeScript type checking (tsc --noEmit)
- ESLint checking (npm run lint)
- Unit tests (npm run test)
- Frontend build (npm run build)

Automatically triggers rollback if verification fails.

Configurable:
- Skip specific verification steps
- Custom timeout for each step
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

# Default verification timeout in seconds
DEFAULT_VERIFICATION_TIMEOUT = 300  # 5 minutes

# Default timeouts for individual commands
DEFAULT_TSC_TIMEOUT = 120
DEFAULT_ESLINT_TIMEOUT = 120
DEFAULT_TEST_TIMEOUT = 180
DEFAULT_BUILD_TIMEOUT = 180

# Commands to run for verification
TSC_COMMAND = ["npx", "tsc", "--noEmit"]
ESLINT_COMMAND = ["npm", "run", "lint"]
TEST_COMMAND = ["npm", "run", "test"]
BUILD_COMMAND = ["npm", "run", "build"]


class VerificationConfig:
    """Configuration for verification steps."""

    def __init__(
        self,
        skip_tsc: bool = False,
        skip_eslint: bool = False,
        skip_test: bool = False,
        skip_build: bool = True,  # Build is skipped by default
        tsc_timeout: int = DEFAULT_TSC_TIMEOUT,
        eslint_timeout: int = DEFAULT_ESLINT_TIMEOUT,
        test_timeout: int = DEFAULT_TEST_TIMEOUT,
        build_timeout: int = DEFAULT_BUILD_TIMEOUT,
        overall_timeout: int = DEFAULT_VERIFICATION_TIMEOUT,
    ):
        self.skip_tsc = skip_tsc
        self.skip_eslint = skip_eslint
        self.skip_test = skip_test
        self.skip_build = skip_build
        self.tsc_timeout = tsc_timeout
        self.eslint_timeout = eslint_timeout
        self.test_timeout = test_timeout
        self.build_timeout = build_timeout
        self.overall_timeout = overall_timeout


async def verify_patch(
    patch_id: str,
    db: AsyncSession,
    frontend_dir: str | None = None,
    config: VerificationConfig | None = None,
) -> dict[str, Any]:
    """
    Run verification checks on a patch.

    Runs:
    1. TypeScript type checking (configurable)
    2. ESLint checking (configurable)
    3. Unit tests (configurable)
    4. Frontend build (configurable, skipped by default)

    If any check fails, triggers automatic rollback.

    Args:
        patch_id: UUID of the patch to verify
        db: Database session
        frontend_dir: Path to frontend directory (auto-detected if not provided)
        config: VerificationConfig to customize which steps to run and timeouts

    Returns:
        {
            "verified": bool,
            "results": {
                "tsc": {"passed": bool, "output": str, "skipped": bool},
                "eslint": {"passed": bool, "output": str, "skipped": bool},
                "test": {"passed": bool, "output": str, "skipped": bool},
                "build": {"passed": bool, "output": str, "skipped": bool},
            }
        }
    """
    if config is None:
        config = VerificationConfig()

    results = {
        "tsc": {"passed": False, "output": "", "skipped": config.skip_tsc},
        "eslint": {"passed": False, "output": "", "skipped": config.skip_eslint},
        "test": {"passed": False, "output": "", "skipped": config.skip_test},
        "build": {"passed": False, "output": "", "skipped": config.skip_build},
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

    # Run verification checks with overall timeout
    try:
        async with asyncio.timeout(config.overall_timeout):
            # TypeScript check
            if not config.skip_tsc:
                results["tsc"] = await _run_command_async(
                    TSC_COMMAND,
                    frontend_dir,
                    timeout=config.tsc_timeout,
                )
                results["tsc"]["skipped"] = False
            else:
                results["tsc"]["passed"] = True
                results["tsc"]["skipped"] = True

            # ESLint check
            if not config.skip_eslint:
                results["eslint"] = await _run_command_async(
                    ESLINT_COMMAND,
                    frontend_dir,
                    timeout=config.eslint_timeout,
                )
                results["eslint"]["skipped"] = False
            else:
                results["eslint"]["passed"] = True
                results["eslint"]["skipped"] = True

            # Unit tests
            if not config.skip_test:
                results["test"] = await _run_command_async(
                    TEST_COMMAND,
                    frontend_dir,
                    timeout=config.test_timeout,
                )
                results["test"]["skipped"] = False
            else:
                results["test"]["passed"] = True
                results["test"]["skipped"] = True

            # Frontend build
            if not config.skip_build:
                results["build"] = await _run_command_async(
                    BUILD_COMMAND,
                    frontend_dir,
                    timeout=config.build_timeout,
                )
                results["build"]["skipped"] = False
            else:
                results["build"]["passed"] = True
                results["build"]["skipped"] = True

    except asyncio.TimeoutError:
        logger.error("verify_patch: Overall verification timeout")
        results["error"] = f"Verification timeout after {config.overall_timeout}s"

    # Determine overall verification status (only consider non-skipped steps)
    all_passed = True
    for step in ["tsc", "eslint", "test", "build"]:
        if not results[step]["skipped"] and not results[step]["passed"]:
            all_passed = False
            break

    # Update log entry
    log_entry.verified = {
        "tsc": results["tsc"]["passed"],
        "tsc_skipped": results["tsc"]["skipped"],
        "eslint": results["eslint"]["passed"],
        "eslint_skipped": results["eslint"]["skipped"],
        "test": results["test"]["passed"],
        "test_skipped": results["test"]["skipped"],
        "build": results["build"]["passed"],
        "build_skipped": results["build"]["skipped"],
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
