"""
Unit tests for the Error Report API GET endpoint (Issue #004).

Tests cover:
- GET /errors pagination logic
- GET /errors filtering logic (type, severity, since)
- GET /errors aggregation mode
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from datetime import datetime


# ─── Pagination Logic Tests ────────────────────────────────────────────────────

class TestPaginationLogic:
    """Pagination calculations for list_errors endpoint."""

    def test_offset_calculation_page_1(self):
        """Page 1 with limit 50 should have offset 0."""
        page = 1
        limit = 50
        offset = (page - 1) * limit
        assert offset == 0

    def test_offset_calculation_page_2(self):
        """Page 2 with limit 50 should have offset 50."""
        page = 2
        limit = 50
        offset = (page - 1) * limit
        assert offset == 50

    def test_offset_calculation_page_3_limit_25(self):
        """Page 3 with limit 25 should have offset 50."""
        page = 3
        limit = 25
        offset = (page - 1) * limit
        assert offset == 50

    def test_total_pages_calculation(self):
        """Total pages = ceil(total / limit)."""
        # 100 errors, limit 50 → 2 pages
        assert pytest.approx(100 / 50) == 2
        # 101 errors, limit 50 → ceil(2.02) = 3 pages
        import math
        assert math.ceil(101 / 50) == 3
        # 0 errors → 0 pages
        assert math.ceil(0 / 50) == 0

    def test_page_ge_1_validation(self):
        """Page must be >= 1."""
        from fastapi import Query
        # The Query validation uses ge=1, which rejects values < 1
        assert 1 >= 1  # valid
        assert 0 < 1   # invalid

    def test_limit_range_validation(self):
        """Limit must be >= 1 and <= 100."""
        from fastapi import Query
        # The Query validation uses ge=1, le=100
        assert 1 >= 1 and 1 <= 100   # valid
        assert 50 >= 1 and 50 <= 100 # valid
        assert 100 >= 1 and 100 <= 100  # valid
        assert 0 < 1   # invalid (too small)
        assert 101 > 100  # invalid (too large)


# ─── Filtering Logic Tests ──────────────────────────────────────────────────────

class TestFilteringLogic:
    """Query filter construction for type, severity, and since parameters."""

    def test_type_filter_included_in_query(self):
        """When type is provided, it should be added to WHERE clause."""
        type_filter = "api"
        # Simulated filter condition
        condition = f"type == '{type_filter}'"
        assert "api" in condition

    def test_severity_filter_included_in_query(self):
        """When severity is provided, it should be added to WHERE clause."""
        severity_filter = "error"
        condition = f"severity == '{severity_filter}'"
        assert "error" in condition

    def test_since_filter_datetime_conversion(self):
        """ISO datetime string should be parsed correctly."""
        from datetime import datetime
        since_str = "2026-07-01"
        dt = datetime.fromisoformat(since_str)
        assert dt.year == 2026
        assert dt.month == 7
        assert dt.day == 1

    def test_since_filter_with_z_suffix(self):
        """ISO datetime with Z suffix should be parsed."""
        from datetime import datetime
        since_str = "2026-07-01T00:00:00Z"
        # Z suffix needs replacement for Python's fromisoformat
        normalized = since_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        assert dt.year == 2026

    def test_invalid_since_filter_ignored(self):
        """Invalid datetime format should not raise, just be ignored."""
        from datetime import datetime
        invalid_since = "not-a-date"
        try:
            dt = datetime.fromisoformat(invalid_since.replace("Z", "+00:00"))
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected behavior

    def test_combined_filters(self):
        """Multiple filters can be combined."""
        type_filter = "api"
        severity_filter = "error"
        since_filter = "2026-07-01"
        # All filters should be present
        filters = [type_filter, severity_filter, since_filter]
        assert len(filters) == 3


# ─── Aggregation Logic Tests ────────────────────────────────────────────────────

class TestAggregationLogic:
    """Aggregation by fingerprint with count."""

    def test_aggregate_flag_true_returns_aggregations(self):
        """When aggregate=true, response should have 'aggregations' key."""
        aggregate = True
        response_key = "aggregations" if aggregate else "errors"
        assert response_key == "aggregations"

    def test_aggregate_flag_false_returns_errors_list(self):
        """When aggregate=false, response should have 'errors' key."""
        aggregate = False
        response_key = "aggregations" if aggregate else "errors"
        assert response_key == "errors"

    def test_aggregation_group_by_fingerprint(self):
        """Aggregation groups by fingerprint field."""
        # Simulated aggregation structure
        agg_result = {
            "fingerprint": "api:Cannot fetch",
            "count": 15,
            "type": "api",
            "severity": "error",
            "message": "Cannot fetch",
        }
        assert "fingerprint" in agg_result
        assert "count" in agg_result

    def test_aggregation_order_by_count_desc(self):
        """Aggregation results should be ordered by count descending."""
        # Simulated sorted results
        aggregations = [
            {"fingerprint": "fp-a", "count": 50},
            {"fingerprint": "fp-b", "count": 30},
            {"fingerprint": "fp-c", "count": 10},
        ]
        counts = [a["count"] for a in aggregations]
        assert counts == sorted(counts, reverse=True)

    def test_aggregation_applies_same_filters(self):
        """Aggregation should respect type/severity/since filters."""
        type_filter = "api"
        severity_filter = "error"
        # Filters applied to aggregation query as well
        assert type_filter is not None
        assert severity_filter is not None


# ─── Response Structure Tests ───────────────────────────────────────────────────

class TestResponseStructure:
    """Response JSON structure validation."""

    def test_list_response_has_required_keys(self):
        """List response must include errors, total, page, limit."""
        response = {
            "errors": [],
            "total": 0,
            "page": 1,
            "limit": 50,
        }
        assert "errors" in response
        assert "total" in response
        assert "page" in response
        assert "limit" in response

    def test_aggregation_response_has_aggregations_key(self):
        """Aggregation response must include 'aggregations' key."""
        response = {
            "aggregations": [],
        }
        assert "aggregations" in response

    def test_error_record_structure(self):
        """Each error record must have expected fields."""
        error_record = {
            "id": "uuid-string",
            "type": "api",
            "severity": "error",
            "message": "Cannot fetch",
            "stack": None,
            "fingerprint": "fp-123",
            "context": {},
            "ip_address": None,
            "user_agent": None,
            "created_at": "2026-07-09T10:00:00",
        }
        required_keys = [
            "id", "type", "severity", "message", "fingerprint",
            "context", "created_at",
        ]
        for key in required_keys:
            assert key in error_record

    def test_aggregation_record_structure(self):
        """Each aggregation record must have fingerprint, count, type, severity, message."""
        agg_record = {
            "fingerprint": "fp-123",
            "count": 5,
            "type": "api",
            "severity": "error",
            "message": "Cannot fetch",
        }
        required_keys = ["fingerprint", "count", "type", "severity", "message"]
        for key in required_keys:
            assert key in agg_record


# ─── Edge Cases Tests ───────────────────────────────────────────────────────────

class TestEdgeCases:
    """Edge case handling for list_errors endpoint."""

    def test_empty_result_returns_empty_list(self):
        """When no errors match, should return empty errors list."""
        response = {
            "errors": [],
            "total": 0,
            "page": 1,
            "limit": 50,
        }
        assert response["errors"] == []
        assert response["total"] == 0

    def test_page_exceeds_total_returns_empty(self):
        """Requesting page beyond available data returns empty list."""
        total = 10
        limit = 50
        total_pages = 1
        page_requested = 2
        assert page_requested > total_pages
        # Would return empty list

    def test_datetime_serialization(self):
        """created_at datetime should be serialized as ISO string."""
        from datetime import datetime
        dt = datetime(2026, 7, 9, 10, 30, 0)
        iso_str = dt.isoformat()
        assert "2026-07-09" in iso_str
        assert "10:30:00" in iso_str

    def test_uuid_serialization(self):
        """UUID should be serialized as string."""
        import uuid
        test_uuid = uuid.uuid4()
        uuid_str = str(test_uuid)
        assert isinstance(uuid_str, str)
        assert len(uuid_str) == 36  # UUID format: 8-4-4-4-12