"""Prompt template engine — renders Jinja2 templates with context."""

from __future__ import annotations
from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).parent / "templates"


def render_template(name: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 template with the given context.

    For now, this reads the template file and does simple {{ var }} replacement.
    Jinja2 will be added as a dependency later; the template format is designed
    to be compatible.
    """
    path = TEMPLATES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {name}")

    template = path.read_text(encoding="utf-8")

    # Simple variable substitution
    result = template
    for key, value in context.items():
        placeholder = "{{ " + key + " }}"
        if placeholder in result and isinstance(value, str):
            result = result.replace(placeholder, value)

    return result