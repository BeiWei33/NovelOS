"""
Auto-Fix API Routes — REST endpoints for the auto-fix pipeline.

Issues #001-#005: Complete workflow endpoints.
"""

from __future__ import annotations
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from database.models.canonical import FrontendError
from workflow.error_analyzer import ErrorAnalyzer
from workflow.patch_generator import PatchGenerator
from workflow.git_operations import commit_patch, rollback_patch
from workflow.verification import verify_patch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auto-fix", tags=["auto-fix"])


# ─── Issue #001: Error Analysis ────────────────────────────────────────────────

@router.post("/analyze/{error_id}")
async def analyze_error(
    error_id: str,
    db: AsyncSession = Depends(get_session),
):
    """
    Analyze a single error and return fix decision.

    Returns:
    - can_fix: Whether auto-fix is possible
    - fix_type: Category of fix needed
    - risk_level: Estimated risk
    - fix_strategy: LLM-generated strategy
    - affected_files: Predicted file paths
    """
    # Fetch error from database
    result = await db.execute(
        select(FrontendError).where(FrontendError.id == error_id)
    )
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error {error_id} not found",
        )

    # Analyze error
    analyzer = ErrorAnalyzer()
    analysis = await analyzer.analyze(error)

    return {
        "error_id": error_id,
        "analysis": analysis,
    }


# ─── Issue #002: Patch Generation ──────────────────────────────────────────────

@router.post("/generate-patch")
async def generate_patch(
    error_id: str,
    db: AsyncSession = Depends(get_session),
):
    """
    Generate a code patch based on error analysis.

    Requires prior analysis (call /analyze first).
    Returns patch_id and list of modified files.
    """
    # Fetch error from database
    result = await db.execute(
        select(FrontendError).where(FrontendError.id == error_id)
    )
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error {error_id} not found",
        )

    # Analyze first if not done
    analyzer = ErrorAnalyzer()
    analysis = await analyzer.analyze(error)

    if not analysis["can_fix"]:
        return {
            "patch_id": None,
            "patch_applied": False,
            "reason": analysis["fix_strategy"],
        }

    if analysis["risk_level"] == "high":
        return {
            "patch_id": None,
            "patch_applied": False,
            "reason": "High risk error requires manual review",
        }

    # Generate patch
    generator = PatchGenerator()
    patch_result = await generator.generate_patch(
        fix_strategy=analysis["fix_strategy"],
        affected_files=analysis["affected_files"],
        error=error,
        db=db,
    )

    return patch_result


# ─── Issue #003: Git Commit ────────────────────────────────────────────────────

@router.post("/commit/{patch_id}")
async def commit_patch_endpoint(
    patch_id: str,
    db: AsyncSession = Depends(get_session),
    push: bool = False,
):
    """
    Commit a patch to Git.

    Creates an auto-fix/{patch_id} branch and commits changes.
    Optionally pushes to remote.
    """
    from database.models.auto_fix import AutoFixLog

    # Fetch log entry
    result = await db.execute(
        select(AutoFixLog).where(AutoFixLog.patch_id == patch_id)
    )
    log_entry = result.scalar_one_or_none()

    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patch {patch_id} not found",
        )

    # Get modified files
    modified_files = [
        f["path"] for f in (log_entry.modified_files or [])
    ]

    if not modified_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No modified files in patch",
        )

    # Commit
    result = await commit_patch(
        patch_id=patch_id,
        modified_files=modified_files,
        db=db,
        push=push,
    )

    return {
        "patch_id": patch_id,
        "commit_hash": result["commit_hash"],
        "push_status": result["push_status"],
    }


# ─── Issue #004: Rollback ──────────────────────────────────────────────────────

@router.post("/rollback/{patch_id}")
async def rollback_patch_endpoint(
    patch_id: str,
    db: AsyncSession = Depends(get_session),
):
    """
    Rollback a patch.

    Restores original file content and reverts Git state.
    """
    result = await rollback_patch(patch_id=patch_id, db=db)

    return {
        "patch_id": patch_id,
        "rolled_back": result["rolled_back"],
        "rollback_at": result["rollback_at"].isoformat() if result["rollback_at"] else None,
    }


# ─── Issue #005: Verification ──────────────────────────────────────────────────

@router.post("/verify/{patch_id}")
async def verify_patch_endpoint(
    patch_id: str,
    db: AsyncSession = Depends(get_session),
):
    """
    Verify a patch by running type checks, lint, and tests.

    If verification fails, automatically triggers rollback.
    """
    result = await verify_patch(patch_id=patch_id, db=db)

    return {
        "patch_id": patch_id,
        "verified": result["verified"],
        "results": result["results"],
    }


# ─── Complete Workflow ─────────────────────────────────────────────────────────

@router.post("/run/{error_id}")
async def run_auto_fix(
    error_id: str,
    db: AsyncSession = Depends(get_session),
    push: bool = False,
):
    """
    Run complete auto-fix workflow for an error.

    Steps:
    1. Analyze error
    2. Generate patch (if can_fix and not high risk)
    3. Apply patch (recorded in database)
    4. Verify patch (tsc, eslint, test)
    5. Rollback if verification fails
    6. Commit if verification passes

    Returns:
    {
        "success": bool,
        "patch_id": str | None,
        "status": str,
        "analysis": dict,
        "verification": dict | None,
    }
    """
    # 1. Fetch error
    result = await db.execute(
        select(FrontendError).where(FrontendError.id == error_id)
    )
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error {error_id} not found",
        )

    # 2. Analyze error
    analyzer = ErrorAnalyzer()
    analysis = await analyzer.analyze(error)

    if not analysis["can_fix"]:
        return {
            "success": False,
            "patch_id": None,
            "status": "cannot_fix",
            "analysis": analysis,
            "verification": None,
        }

    if analysis["risk_level"] == "high":
        return {
            "success": False,
            "patch_id": None,
            "status": "high_risk",
            "analysis": analysis,
            "verification": None,
        }

    # 3. Generate patch
    generator = PatchGenerator()
    patch_result = await generator.generate_patch(
        fix_strategy=analysis["fix_strategy"],
        affected_files=analysis["affected_files"],
        error=error,
        db=db,
    )

    if not patch_result["patch_applied"]:
        return {
            "success": False,
            "patch_id": patch_result["patch_id"],
            "status": "patch_failed",
            "analysis": analysis,
            "verification": None,
        }

    patch_id = patch_result["patch_id"]

    # 4. Verify patch
    verification = await verify_patch(patch_id=patch_id, db=db)

    if not verification["verified"]:
        return {
            "success": False,
            "patch_id": patch_id,
            "status": "verification_failed_rolled_back",
            "analysis": analysis,
            "verification": verification,
        }

    # 5. Commit patch
    modified_files = [
        f["path"] for f in patch_result["modified_files"]
    ]
    commit_result = await commit_patch(
        patch_id=patch_id,
        modified_files=modified_files,
        db=db,
        push=push,
    )

    return {
        "success": True,
        "patch_id": patch_id,
        "status": "committed",
        "commit_hash": commit_result["commit_hash"],
        "push_status": commit_result["push_status"],
        "analysis": analysis,
        "verification": verification,
    }
