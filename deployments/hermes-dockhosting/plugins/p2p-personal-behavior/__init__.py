"""Hermes runtime bridge for the P2P Personal AI behavior harness.

The bridge deliberately stays thin:

- a cache-safe system-prompt section carries stable communication policy;
- pre_llm_call injects only explicit per-turn serious/short/deep overrides;
- transform_llm_output runs the report-only anti-slop linter and never rewrites
  the assistant response.

Authoritative facts, tool execution, durable memory and scheduling remain owned
by their existing Hermes/P2P surfaces. This plugin never claims tool/research
work happened merely because a message sounds like it might need it.
"""

from __future__ import annotations

import logging
import re

try:
    # Repository/test path: use the canonical P2P source directly.
    from p2p_capabilities.personal_ai_behavior import (
        ResponseSignals,
        VoiceProfile,
        lint_response,
        select_response_policy,
    )
except ImportError:  # pragma: no cover - exercised in the built Hermes image.
    # Image path: Docker copies the same canonical source beside this plugin.
    from .personal_ai_behavior import (  # type: ignore
        ResponseSignals,
        VoiceProfile,
        lint_response,
        select_response_policy,
    )


logger = logging.getLogger(__name__)
PROFILE = VoiceProfile()

_SERIOUS = re.compile(
    r"(?:^|[.!?\n]\s*)(?:hãy\s+)?(?:trả lời\s+)?nghiêm túc\b|\bserious mode\b",
    re.IGNORECASE,
)
_SHORT = re.compile(
    r"\b(?:trả lời\s+ngắn gọn|ngắn gọn\s+thôi|tóm tắt\s+(?:ngắn gọn|lại)|brief answer)\b",
    re.IGNORECASE,
)
_DEEP = re.compile(
    r"\b(?:phân tích sâu|nghiên cứu sâu|đào sâu|trả lời chi tiết|deep dive)\b",
    re.IGNORECASE,
)


def _signals_from_user_message(user_message: str) -> ResponseSignals:
    """Map only explicit wording requests into the existing controller.

    Tool/research/ambiguity requirements are intentionally NOT guessed here.
    Hermes and the surrounding P2P task/tool layer retain authority for those
    decisions; keyword heuristics would be a fake routing oracle.
    """

    text = user_message or ""
    deep = bool(_DEEP.search(text))
    short = bool(_SHORT.search(text)) and not deep
    return ResponseSignals(
        explicit_serious=bool(_SERIOUS.search(text)),
        user_requested_short=short,
        user_requested_deep=deep,
    )


def _system_prompt_section(_session_info=None) -> str:
    """Stable, cache-safe Personal AI communication contract for new sessions."""

    policy = select_response_policy(PROFILE, ResponseSignals())
    directives = "\n".join(f"- {item}" for item in policy.style_directives)
    return (
        "P2P Personal AI behavior contract (V1 runtime bridge).\n"
        "Factual correctness and authoritative tool/data values outrank style. "
        "Never change amounts, currencies, units, routes, dates, vehicle/container "
        "types, business conditions, or other authoritative values merely to fit voice.\n"
        "Do not claim research, tool use, retrieval, memory writes, or actions unless "
        "they actually occurred in the active Hermes/P2P workflow.\n"
        "Keep the answer useful and direct; ask only when ambiguity genuinely blocks "
        "the requested outcome.\n"
        "Default communication directives:\n"
        f"{directives}"
    )


def _pre_llm_call(user_message: str = "", **_kwargs):
    """Inject an ephemeral override only when the user explicitly asks for one."""

    signals = _signals_from_user_message(user_message)
    if not (
        signals.explicit_serious
        or signals.user_requested_short
        or signals.user_requested_deep
    ):
        return None

    policy = select_response_policy(PROFILE, signals)
    directives = "\n".join(f"- {item}" for item in policy.style_directives)
    return {
        "context": (
            "P2P turn-level communication override (applies to this turn only):\n"
            f"- depth={policy.depth}\n"
            f"- seriousness={policy.seriousness:.2f}\n"
            f"- humor_allowed={str(policy.humor_allowed).lower()}\n"
            f"{directives}"
        )
    }


def _transform_llm_output(response_text: str = "", **_kwargs):
    """Run report-only anti-slop linting; never replace the final response."""

    findings = lint_response(response_text or "", PROFILE)
    if findings:
        # Log only codes, never response excerpts, to avoid copying user/model
        # content into an additional persistence surface.
        logger.info(
            "P2P Personal AI anti-slop findings: %s",
            ",".join(finding.code for finding in findings),
        )
    return None


def register(ctx) -> None:
    """Register only documented Hermes plugin surfaces; no core monkey-patching."""

    ctx.register_system_prompt_section(
        "p2p-personal-behavior.voice",
        _system_prompt_section,
        position="after_memory",
        max_chars=3000,
    )
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("transform_llm_output", _transform_llm_output)
