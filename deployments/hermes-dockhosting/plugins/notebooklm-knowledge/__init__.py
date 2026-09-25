"""Hermes NotebookLM knowledge-search plugin."""

from __future__ import annotations

from . import tools as _tools


def _system_prompt_section(_session_info=None) -> str:
    return (
        "Trường Thành Logistics NotebookLM grounding contract.\n"
        "For staff questions about HS classification, chemicals, Bộ KH&CN / "
        "quality-regulation topics, Bộ TT&TT / telecom-radio topics, or Bộ Y tế, "
        "you MUST call notebooklm_domain_search before giving a substantive answer. "
        "Do not answer those domain questions from model memory alone. "
        "If the tool is unavailable or returns an error, say NotebookLM is currently "
        "unavailable and ask the user to retry or provide more detail; do not fabricate "
        "a fallback answer. Ground every substantive claim only in returned passages. "
        "In the final answer, explicitly state which NotebookLM notebook(s) were used "
        "and list the returned source_title values so the user can verify retrieval. "
        "NotebookLM is operational research, not binding legal authority; legal "
        "conclusions still require VNLAW / official-source verification."
    )


def register(ctx) -> None:
    """Register one read-only NotebookLM search tool plus its grounding rule."""
    for spec in _tools.TOOL_REGISTRATIONS:
        ctx.register_tool(**spec)
    ctx.register_system_prompt_section(
        "notebooklm-knowledge.grounding",
        _system_prompt_section,
        position="after_memory",
        max_chars=2200,
    )
