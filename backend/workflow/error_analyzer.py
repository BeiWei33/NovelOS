"""
ErrorAnalyzer — AI-driven error analysis for auto-fix pipeline (Issue #001).

Analyzes frontend errors and determines:
- Whether the error can be auto-fixed
- The type of fix required (frontend, backend, config)
- Risk level of the fix
- Strategy and affected files
"""

from __future__ import annotations
import json
import logging
from typing import Any

from core.types import ExecutionProfile
from skills.providers import router
from skills.profile_registry import profile_registry
from database.models.canonical import FrontendError

logger = logging.getLogger(__name__)

# Error types we can handle
HANDLED_ERROR_TYPES = {"api", "render"}

# Error patterns that are too risky to auto-fix
HIGH_RISK_PATTERNS = [
    "migration",
    "auth",
    "password",
    "token",
    "credential",
    "secret",
    "permission",
    "security",
    "database schema",
    "ddl",
]

# Maximum number of files a single fix can modify
MAX_AFFECTED_FILES = 5


class ErrorAnalyzer:
    """AI-driven error analyzer for the auto-fix pipeline."""

    def __init__(self, profile: ExecutionProfile | None = None):
        """Initialize with optional profile override."""
        self.profile = profile or profile_registry.get("error-analyzer")

    async def analyze(self, error: FrontendError) -> dict[str, Any]:
        """
        Analyze a single frontend error and return fix decision.

        Args:
            error: FrontendError record from database

        Returns:
            {
                "can_fix": bool,
                "fix_type": "frontend" | "backend" | "config" | "unknown",
                "risk_level": "low" | "medium" | "high",
                "fix_strategy": str,  # LLM-generated strategy
                "affected_files": list[str],  # predicted file paths
            }
        """
        # Pre-filter: only handle certain error types
        error_type = self._extract_error_type(error)
        if error_type not in HANDLED_ERROR_TYPES:
            return self._cannot_fix_response(
                f"Error type '{error_type}' not supported. "
                f"Supported types: {HANDLED_ERROR_TYPES}"
            )

        # Pre-filter: check for high-risk patterns
        error_text = self._build_error_text(error)
        if self._contains_high_risk_patterns(error_text):
            return {
                "can_fix": False,
                "fix_type": "unknown",
                "risk_level": "high",
                "fix_strategy": "Error involves high-risk area (auth, security, or database). Manual review required.",
                "affected_files": [],
            }

        # Use LLM to analyze the error
        try:
            analysis = await self._llm_analyze(error)
            return analysis
        except Exception as e:
            logger.error(f"ErrorAnalyzer: LLM analysis failed: {e}")
            return self._cannot_fix_response(f"Analysis failed: {str(e)}")

    def _extract_error_type(self, error: FrontendError) -> str:
        """Extract error type category from FrontendError."""
        # Check context for explicit type
        ctx = error.context or {}
        if "type" in ctx:
            return ctx["type"].lower()

        # Infer from error message/type
        msg = (error.message or "").lower()
        err_type = (error.type or "").lower()

        # API errors
        if "api" in msg or "fetch" in msg or "request" in msg or "axios" in msg:
            return "api"
        if "api" in err_type:
            return "api"

        # Render errors
        if "render" in msg or "component" in msg or "undefined" in msg or "null" in msg:
            return "render"
        if "render" in err_type or "typeerror" in err_type or "referenceerror" in err_type:
            return "render"

        # Default to unknown
        return "unknown"

    def _build_error_text(self, error: FrontendError) -> str:
        """Build comprehensive error text for analysis."""
        parts = [
            f"Type: {error.type}",
            f"Severity: {error.severity}",
            f"Message: {error.message}",
        ]
        if error.stack:
            parts.append(f"Stack: {error.stack}")
        if error.context:
            parts.append(f"Context: {json.dumps(error.context, ensure_ascii=False)}")
        return "\n".join(parts)

    def _contains_high_risk_patterns(self, text: str) -> bool:
        """Check if error text contains high-risk patterns."""
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in HIGH_RISK_PATTERNS)

    async def _llm_analyze(self, error: FrontendError) -> dict[str, Any]:
        """Use LLM to analyze the error and generate fix strategy."""
        error_text = self._build_error_text(error)

        prompt = f"""Analyze this frontend error and determine if it can be auto-fixed.

Error Details:
{error_text}

Respond in JSON format:
{{
    "can_fix": true/false,
    "fix_type": "frontend" | "backend" | "config" | "unknown",
    "risk_level": "low" | "medium" | "high",
    "fix_strategy": "Brief description of how to fix",
    "affected_files": ["list of file paths that need changes"]
}}

Rules:
- can_fix=false if error involves database migrations, authentication, security, or permissions
- risk_level="high" if the fix could break other functionality
- fix_type="frontend" for UI/component issues
- fix_type="backend" for API issues
- fix_type="config" for configuration issues
- Maximum {MAX_AFFECTED_FILES} files can be affected
- Only suggest fixes for TypeScript/JavaScript files (.ts, .tsx, .js, .jsx)"""

        messages = [
            {
                "role": "system",
                "content": "You are an expert code analyst. Respond only with valid JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        response = await router.execute(messages, self.profile)

        # Parse LLM response
        try:
            # Try to extract JSON from response
            result = self._parse_json_response(response)

            # Validate and clamp values
            can_fix = bool(result.get("can_fix", False))
            fix_type = result.get("fix_type", "unknown")
            if fix_type not in ("frontend", "backend", "config", "unknown"):
                fix_type = "unknown"

            risk_level = result.get("risk_level", "medium")
            if risk_level not in ("low", "medium", "high"):
                risk_level = "medium"

            affected_files = result.get("affected_files", [])
            if not isinstance(affected_files, list):
                affected_files = []
            # Clamp to max files
            affected_files = affected_files[:MAX_AFFECTED_FILES]

            return {
                "can_fix": can_fix and risk_level != "high",
                "fix_type": fix_type,
                "risk_level": risk_level,
                "fix_strategy": str(result.get("fix_strategy", "")),
                "affected_files": affected_files,
            }
        except json.JSONDecodeError:
            logger.error(f"ErrorAnalyzer: Failed to parse LLM response: {response}")
            return self._cannot_fix_response("Failed to parse analysis response")

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from LLM response, handling markdown fences."""
        # Try to find JSON block
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()

        return json.loads(json_str)

    def _cannot_fix_response(self, reason: str) -> dict[str, Any]:
        """Return a cannot-fix response with reason."""
        return {
            "can_fix": False,
            "fix_type": "unknown",
            "risk_level": "high",
            "fix_strategy": reason,
            "affected_files": [],
        }
