"""Hermes NotebookLM knowledge-search plugin."""

from __future__ import annotations

from . import tools as _tools


def register(ctx) -> None:
    """Register one read-only NotebookLM search tool."""
    for spec in _tools.TOOL_REGISTRATIONS:
        ctx.register_tool(**spec)
