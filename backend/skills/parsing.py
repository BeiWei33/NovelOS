"""Shared utilities for parsing LLM JSON responses."""

from __future__ import annotations
import json
from typing import Any


def parse_json_from_markdown(response: str) -> dict[str, Any] | list[Any]:
    """Extract and parse JSON from LLM response, handling markdown fences.

    Args:
        response: Raw LLM response text

    Returns:
        Parsed JSON object or list, or empty dict/list on failure
    """
    json_str = response.strip()

    # Try to extract from markdown fence
    if "```json" in response:
        json_str = response.split("```json")[1].split("```")[0].strip()
    elif "```" in response:
        json_str = response.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {}


def parse_list_from_response(response: str, key: str | None = None) -> list[dict[str, Any]]:
    """Parse a list from LLM response, optionally extracting from a key.

    Args:
        response: Raw LLM response text
        key: Optional key to extract from (e.g., "patches", "issues")

    Returns:
        List of dicts, or empty list on failure
    """
    data = parse_json_from_markdown(response)

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and key and key in data:
        result = data[key]
        if isinstance(result, list):
            return result

    return []