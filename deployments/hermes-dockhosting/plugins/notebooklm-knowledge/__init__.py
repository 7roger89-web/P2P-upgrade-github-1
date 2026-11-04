"""Hermes NotebookLM knowledge-search plugin."""

from __future__ import annotations

from . import tools as _tools


def _system_prompt_section(_session_info=None) -> str:
    return (
        "Trường Thành Logistics NotebookLM + VNLAW grounding contract.\n"
        "For staff questions about HS classification, chemicals, Bộ KH&CN / "
        "quality-regulation topics, Bộ TT&TT / telecom-radio topics, or Bộ Y tế, "
        "you MUST call notebooklm_domain_search before giving a substantive answer. "
        "Do not answer those domain questions from model memory alone. "
        "The tool automatically returns two evidence lanes: NotebookLM operational "
        "research and vnlaw_cross_check verified legal evidence. "
        "Always show which NotebookLM notebook(s) were used and list returned "
        "source_title values. Then show a separate 'VNLAW xác minh' section. "
        "If vnlaw_cross_check.status is VERIFIED_EVIDENCE_FOUND, only describe "
        "legal conclusions actually supported by its returned legal/technical/"
        "guidance evidence and cite source_url/source_locator when available. "
        "If status is NO_VERIFIED_EVIDENCE, explicitly say VNLAW has not verified "
        "the legal claim in its bounded corpus; do NOT convert NotebookLM research "
        "into a verified legal conclusion. If status is CONFIG_MISSING or "
        "SERVICE_ERROR, explicitly say the legal cross-check is unavailable. "
        "Never interpret no VNLAW hit as proof that a product is unregulated. "
        "NotebookLM remains operational research; VNLAW is the verification lane."
    )


def register(ctx) -> None:
    """Register one read-only NotebookLM search tool plus its grounding rule."""
    for spec in _tools.TOOL_REGISTRATIONS:
        ctx.register_tool(**spec)
    ctx.register_system_prompt_section(
        "notebooklm-knowledge.grounding",
        _system_prompt_section,
        position="after_memory",
        max_chars=2800,
    )
