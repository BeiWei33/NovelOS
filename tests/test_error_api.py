"""
Unit tests for the Error Report API (Issue #002 & #003).

Tests cover:
- FrontendErrorCreate schema validation
- Sensitive field filtering (_filter_sensitive)
- Fingerprint rate-limiting (_is_rate_limited)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
import time


# ─── Schema validation ────────────────────────────────────────────────────────

class TestFrontendErrorCreateSchema:
    """FrontendErrorCreate Pydantic schema validates input correctly."""

    def test_valid_minimal_payload(self):
        from api.schemas import FrontendErrorCreate
        err = FrontendErrorCreate(
            type="TypeError",
            severity="error",
            message="Cannot read property of undefined",
            fingerprint="abc123",
        )
        assert err.type == "TypeError"
        assert err.severity == "error"
        assert err.stack is None
        assert err.context == {}
        assert err.user_agent is None

    def test_valid_full_payload(self):
        from api.schemas import FrontendErrorCreate
        err = FrontendErrorCreate(
            type="ReferenceError",
            severity="warning",
            message="x is not defined",
            stack="ReferenceError: x is not defined\n  at foo.js:10",
            fingerprint="fp-xyz-001",
            context={"page": "/home", "userId": "u-42"},
            user_agent="Mozilla/5.0",
        )
        assert err.stack is not None
        assert err.context["page"] == "/home"
        assert err.user_agent == "Mozilla/5.0"

    def test_type_too_long_raises(self):
        from pydantic import ValidationError
        from api.schemas import FrontendErrorCreate
        with pytest.raises(ValidationError):
            FrontendErrorCreate(
                type="x" * 51,      # max 50
                severity="error",
                message="msg",
                fingerprint="fp1",
            )

    def test_severity_too_long_raises(self):
        from pydantic import ValidationError
        from api.schemas import FrontendErrorCreate
        with pytest.raises(ValidationError):
            FrontendErrorCreate(
                type="TypeError",
                severity="x" * 21,  # max 20
                message="msg",
                fingerprint="fp1",
            )

    def test_fingerprint_too_long_raises(self):
        from pydantic import ValidationError
        from api.schemas import FrontendErrorCreate
        with pytest.raises(ValidationError):
            FrontendErrorCreate(
                type="TypeError",
                severity="error",
                message="msg",
                fingerprint="f" * 65,  # max 64
            )

    def test_missing_required_field_raises(self):
        from pydantic import ValidationError
        from api.schemas import FrontendErrorCreate
        with pytest.raises(ValidationError):
            # 'fingerprint' is required
            FrontendErrorCreate(
                type="TypeError",
                severity="error",
                message="msg",
            )

    def test_context_defaults_to_empty_dict(self):
        from api.schemas import FrontendErrorCreate
        err = FrontendErrorCreate(
            type="TypeError",
            severity="error",
            message="msg",
            fingerprint="fp1",
        )
        assert err.context == {}

    def test_empty_type_raises(self):
        from pydantic import ValidationError
        from api.schemas import FrontendErrorCreate
        with pytest.raises(ValidationError):
            FrontendErrorCreate(
                type="",
                severity="error",
                message="msg",
                fingerprint="fp1",
            )


# ─── Sensitive-field filter ───────────────────────────────────────────────────

class TestFilterSensitive:
    """_filter_sensitive removes keys containing sensitive keywords."""

    def _filter(self, obj):
        from api.routes.errors import _filter_sensitive
        return _filter_sensitive(obj)

    def test_password_key_is_removed(self):
        result = self._filter({"password": "secret123", "username": "alice"})
        assert "password" not in result
        assert "username" in result

    def test_token_key_is_removed(self):
        result = self._filter({"auth_token": "Bearer xyz", "page": 1})
        assert "auth_token" not in result
        assert "page" in result

    def test_api_key_key_is_removed(self):
        result = self._filter({"api_key": "sk-abc", "model": "gpt-4"})
        assert "api_key" not in result
        assert "model" in result

    def test_secret_key_is_removed(self):
        result = self._filter({"client_secret": "shh", "client_id": "app"})
        assert "client_secret" not in result
        assert "client_id" in result

    def test_case_insensitive_matching(self):
        result = self._filter({"Password": "pwd", "TOKEN": "tok", "API_KEY": "key"})
        assert "Password" not in result
        assert "TOKEN" not in result
        assert "API_KEY" not in result

    def test_non_sensitive_keys_are_preserved(self):
        result = self._filter({"page": "/home", "userId": "u-1", "locale": "zh-CN"})
        assert result == {"page": "/home", "userId": "u-1", "locale": "zh-CN"}

    def test_empty_dict_returns_empty_dict(self):
        assert self._filter({}) == {}

    def test_nested_dict_sensitive_keys_removed(self):
        obj = {
            "request": {
                "password": "secret",
                "url": "/api/data",
            }
        }
        result = self._filter(obj)
        assert "password" not in result["request"]
        assert result["request"]["url"] == "/api/data"

    def test_list_values_are_recursed(self):
        obj = {
            "items": [
                {"password": "x", "name": "a"},
                {"token": "y", "name": "b"},
            ]
        }
        result = self._filter(obj)
        for item in result["items"]:
            assert "password" not in item
            assert "token" not in item
        assert result["items"][0]["name"] == "a"

    def test_scalar_value_returned_unchanged(self):
        assert self._filter("hello") == "hello"
        assert self._filter(42) == 42
        assert self._filter(None) is None

    def test_partial_key_match_removes_key(self):
        """Key 'reset_password_url' contains 'password' → removed."""
        result = self._filter({"reset_password_url": "http://...", "username": "bob"})
        assert "reset_password_url" not in result
        assert "username" in result


# ─── Rate limiter ─────────────────────────────────────────────────────────────

class TestIsRateLimited:
    """_is_rate_limited enforces max 10 hits per fingerprint per 60 seconds."""

    def setup_method(self):
        """Clear the rate cache before each test to avoid cross-test pollution."""
        from api.routes import errors as errors_module
        errors_module._rate_cache.clear()

    def _limited(self, fp: str) -> bool:
        from api.routes.errors import _is_rate_limited
        return _is_rate_limited(fp)

    def test_first_request_is_not_limited(self):
        assert self._limited("fp-a") is False

    def test_tenth_request_is_not_limited(self):
        """Exactly 10 requests → not limited (limit is exceeded at 11)."""
        for _ in range(10):
            result = self._limited("fp-b")
        assert result is False

    def test_eleventh_request_is_limited(self):
        for _ in range(10):
            self._limited("fp-c")
        assert self._limited("fp-c") is True

    def test_twelfth_request_is_also_limited(self):
        for _ in range(12):
            result = self._limited("fp-d")
        assert result is True

    def test_different_fingerprints_are_independent(self):
        """Rate limit is per fingerprint — one fp's count doesn't affect another."""
        for _ in range(11):
            self._limited("fp-e")
        # A different fingerprint should still be allowed
        assert self._limited("fp-f") is False

    def test_old_timestamps_expire_from_window(self):
        """Timestamps older than 60 s are pruned and don't count toward the limit."""
        from api.routes import errors as errors_module
        # Seed cache with 10 entries that are 61 seconds old (outside the window)
        old_time = time.monotonic() - 61
        errors_module._rate_cache["fp-g"] = [old_time] * 10
        # The next request should NOT be rate-limited (old entries were pruned)
        assert self._limited("fp-g") is False

    def test_mixed_old_and_fresh_timestamps(self):
        """Old entries are pruned; only recent ones count."""
        from api.routes import errors as errors_module
        old_time = time.monotonic() - 61
        # 5 old + 5 fresh entries already in cache (not yet counted for this call)
        fresh_times = [time.monotonic()] * 5
        errors_module._rate_cache["fp-h"] = [old_time] * 5 + fresh_times
        # Next call adds the 6th fresh entry → total = 6, still under 10
        assert self._limited("fp-h") is False

    def test_empty_fingerprint_tracked_independently(self):
        """Empty string fingerprint is a valid cache key."""
        for _ in range(11):
            self._limited("")
        assert self._limited("") is True
