"""Consistency score calculator."""

from typing import Any


def calculate_consistency_score(
    issues: list[dict[str, Any]],
    fixed_issues: list[dict[str, Any]] | None = None,
) -> int:
    """Calculate consistency score based on issues.

    Args:
        issues: List of issues from ConsistencyChecker
        fixed_issues: List of issues that were fixed (optional)

    Returns:
        Score from 0-100
    """
    if fixed_issues is None:
        fixed_issues = []

    # Create set of fixed issue IDs for quick lookup
    fixed_ids = set()
    for issue in fixed_issues:
        if "id" in issue:
            fixed_ids.add(issue["id"])

    base_score = 100
    for issue in issues:
        # Skip fixed issues
        if issue.get("id") in fixed_ids:
            continue

        severity = issue.get("severity", "warning").lower()
        if severity == "error":
            base_score -= 20
        elif severity == "warning":
            base_score -= 5

    return max(0, min(100, base_score))


def get_consistency_level(score: int) -> str:
    """Get consistency level label based on score.

    Args:
        score: Score from 0-100

    Returns:
        Level label: "good", "warning", or "error"
    """
    if score >= 80:
        return "good"
    elif score >= 50:
        return "warning"
    else:
        return "error"


def get_consistency_color(score: int) -> str:
    """Get CSS color for consistency score display.

    Args:
        score: Score from 0-100

    Returns:
        CSS color string
    """
    if score >= 80:
        return "#22c55e"  # green
    elif score >= 50:
        return "#eab308"  # yellow
    else:
        return "#ef4444"  # red