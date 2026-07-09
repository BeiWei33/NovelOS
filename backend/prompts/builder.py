"""Prompt template engine — renders Jinja2 templates with context."""

from __future__ import annotations
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def render_template(
    name: str,
    context: dict[str, Any],
    debug_mode: bool = False,
) -> str:
    """Render a Jinja2 template with the given context.

    Args:
        name: Template file name (e.g. "scene_writer.jinja2").
        context: Flat dict with values for template variables.
        debug_mode: If True, print per-context-slice token estimates.

    Returns:
        Rendered template string.
    """
    template = _env.get_template(name)

    if debug_mode:
        # Estimate tokens per context slice (rough: ~4 chars per token)
        for key, value in context.items():
            if isinstance(value, str) and value:
                char_count = len(value)
                est_tokens = char_count // 4
                print(f"[PromptBuilder] {key}: ~{char_count} chars / ~{est_tokens} tokens")

    rendered = template.render(**context)
    return rendered