"""
Frontend Error Report API — receives structured error reports from the frontend
and provides a listing endpoint with pagination, filtering, and aggregation.

Features:
- Sensitive field filtering (password, token, api_key, secret)
- In-memory rate limiting: same fingerprint max 10 times per minute
- Best-effort DB persistence (logs on failure, never raises to caller)
- GET /errors with pagination, type/severity/since filtering, fingerprint aggregation
"""

from __future__ import annotations
import logging
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import FrontendErrorCreate
from database.session import get_session
from database.models.canonical import FrontendError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/errors", tags=["errors"])

# ─── Sensitive-field filter ──────────────────────────────────────────────────

_SENSITIVE_KEYS = {"password", "token", "api_key", "secret"}


def _filter_sensitive(obj: Any) -> Any:
    """Recursively remove keys that match any sensitive keyword from a dict.

    The match is case-insensitive substring: a key containing "password",
    "token", "api_key", or "secret" anywhere in its name is removed.
    """
    if isinstance(obj, dict):
        cleaned: dict[str, Any] = {}
        for k, v in obj.items():
            key_lower = k.lower()
            if any(sensitive in key_lower for sensitive in _SENSITIVE_KEYS):
                continue  # drop this field
            cleaned[k] = _filter_sensitive(v)
        return cleaned
    if isinstance(obj, list):
        return [_filter_sensitive(item) for item in obj]
    return obj


# ─── Rate limiter ─────────────────────────────────────────────────────────────

# {fingerprint: [timestamp, ...]} — stores arrival times in the last 60 s
_rate_cache: dict[str, list[float]] = {}
_RATE_WINDOW_SECS = 60
_RATE_MAX_HITS = 10


def _is_rate_limited(fingerprint: str) -> bool:
    """Return True if this fingerprint has exceeded the rate limit.

    Sliding window: keep only timestamps within the last 60 seconds, then
    check whether the count reaches the maximum.  The new timestamp is
    recorded regardless (to count the current request).
    """
    now = time.monotonic()
    window_start = now - _RATE_WINDOW_SECS

    hits = _rate_cache.get(fingerprint, [])
    # Prune old entries
    hits = [t for t in hits if t >= window_start]
    hits.append(now)
    _rate_cache[fingerprint] = hits

    # Exceeded if we have *more than* the allowed maximum before this request
    # i.e. the list (including current request) exceeds the limit
    return len(hits) > _RATE_MAX_HITS


# ─── Route ────────────────────────────────────────────────────────────────────

@router.post("")
async def report_error(
    payload: FrontendErrorCreate,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    """Accept a structured error report from the frontend.

    Sensitive fields in ``context`` are stripped before storage.
    Repeated reports with the same fingerprint (> 10 per minute) are
    silently discarded to prevent log flooding.

    Returns ``{"received": true, "id": "<uuid>"}`` on success, or
    ``{"received": true, "id": null}`` when rate-limited or DB is
    unavailable.
    """
    # Rate-limit check
    if _is_rate_limited(payload.fingerprint):
        logger.debug(
            "ErrorAPI: rate-limited fingerprint=%s", payload.fingerprint
        )
        return {"received": True, "id": None}

    # Strip sensitive fields from context
    clean_context = _filter_sensitive(payload.context)

    # Extract IP address
    ip_address: str | None = None
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    elif request.client:
        ip_address = request.client.host

    # Persist to DB — best effort
    error_id: str | None = None
    try:
        record = FrontendError(
            type=payload.type,
            severity=payload.severity,
            message=payload.message,
            stack=payload.stack,
            fingerprint=payload.fingerprint,
            context=clean_context,
            ip_address=ip_address,
            user_agent=payload.user_agent,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        error_id = record.id
        logger.info(
            "ErrorAPI: stored error id=%s fingerprint=%s severity=%s",
            error_id,
            payload.fingerprint,
            payload.severity,
        )
    except Exception as exc:
        logger.error(
            "ErrorAPI: failed to persist error fingerprint=%s: %s",
            payload.fingerprint,
            exc,
        )
        await db.rollback()

    return {"received": True, "id": error_id}


# ─── GET Endpoint: List errors ─────────────────────────────────────────────────

@router.get("")
async def list_errors(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    type: str | None = Query(None, description="Filter by error type"),
    severity: str | None = Query(None, description="Filter by severity"),
    since: str | None = Query(None, description="Filter errors since ISO datetime"),
    aggregate: bool = Query(False, description="Group by fingerprint and count"),
    db: AsyncSession = Depends(get_session),
):
    """List frontend errors with pagination and filtering.

    When aggregate=true, returns errors grouped by fingerprint with counts:
        { aggregations: [{fingerprint, count, type, severity, message}], ... }

    Otherwise returns a paginated list:
        { errors: [...], total: int, page: int, limit: int }
    """
    # Build base query with filters
    base_query = select(FrontendError)

    if type:
        base_query = base_query.where(FrontendError.type == type)
    if severity:
        base_query = base_query.where(FrontendError.severity == severity)
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            base_query = base_query.where(FrontendError.created_at >= since_dt)
        except ValueError:
            pass  # Invalid date format, ignore filter

    if aggregate:
        # Group by fingerprint and count
        agg_query = (
            select(
                FrontendError.fingerprint,
                func.count(FrontendError.id).label("count"),
                FrontendError.type,
                FrontendError.severity,
                FrontendError.message,
            )
            .group_by(
                FrontendError.fingerprint,
                FrontendError.type,
                FrontendError.severity,
                FrontendError.message,
            )
            .order_by(func.count(FrontendError.id).desc())
        )

        # Apply same filters to aggregation query
        if type:
            agg_query = agg_query.where(FrontendError.type == type)
        if severity:
            agg_query = agg_query.where(FrontendError.severity == severity)
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                agg_query = agg_query.where(FrontendError.created_at >= since_dt)
            except ValueError:
                pass

        result = await db.execute(agg_query)
        rows = result.all()

        aggregations = [
            {
                "fingerprint": row.fingerprint,
                "count": row.count,
                "type": row.type,
                "severity": row.severity,
                "message": row.message,
            }
            for row in rows
        ]

        return {"aggregations": aggregations}

    # Count total matching records
    count_query = select(func.count(FrontendError.id))
    if type:
        count_query = count_query.where(FrontendError.type == type)
    if severity:
        count_query = count_query.where(FrontendError.severity == severity)
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            count_query = count_query.where(FrontendError.created_at >= since_dt)
        except ValueError:
            pass

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginated query (most recent first)
    offset = (page - 1) * limit
    paginated_query = (
        base_query
        .order_by(FrontendError.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(paginated_query)
    errors = result.scalars().all()

    return {
        "errors": [
            {
                "id": str(e.id),
                "type": e.type,
                "severity": e.severity,
                "message": e.message,
                "stack": e.stack,
                "fingerprint": e.fingerprint,
                "context": e.context,
                "ip_address": e.ip_address,
                "user_agent": e.user_agent,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in errors
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }
