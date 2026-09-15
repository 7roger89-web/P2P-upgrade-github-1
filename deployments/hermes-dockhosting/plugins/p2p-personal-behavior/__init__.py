"""Hermes runtime bridge for the P2P Personal AI behavior harness.

The bridge deliberately stays thin:

- a cache-safe system-prompt section carries stable communication policy;
- pre_llm_call injects explicit turn overrides plus bounded session adaptation;
- post_llm_call reflects coarse completion/open-loop evidence;
- session reset/finalize hooks clear ephemeral state; and
- transform_llm_output runs the report-only anti-slop linter and never rewrites
  the assistant response.

Authoritative facts, tool execution, durable memory and scheduling remain owned
by their existing Hermes/P2P surfaces. Session state here models interaction
handling only; it is not relationship simulation or a claim of human emotion.
"""

from __future__ import annotations

from collections import OrderedDict
import logging
import re
from threading import RLock

try:
    # Repository/test path: use the canonical P2P source directly.
    from p2p_capabilities.personal_ai_behavior import (
        InteractionSignals,
        InteractionState,
        ResponseSignals,
        VoiceProfile,
        advance_interaction_state,
        build_interaction_directives,
        lint_response,
        reflect_assistant_outcome,
        select_response_policy,
    )
except ImportError:  # pragma: no cover - exercised in the built Hermes image.
    # Image path: Docker copies the same canonical source beside this plugin.
    from .personal_ai_behavior import (  # type: ignore
        InteractionSignals,
        InteractionState,
        ResponseSignals,
        VoiceProfile,
        advance_interaction_state,
        build_interaction_directives,
        lint_response,
        reflect_assistant_outcome,
        select_response_policy,
    )


logger = logging.getLogger(__name__)
PROFILE = VoiceProfile()

_SESSION_STATE_LIMIT = 128
_SESSION_STATES: OrderedDict[str, InteractionState] = OrderedDict()
_SESSION_STATE_LOCK = RLock()

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
_CORRECTION = re.compile(
    r"\b(?:sai|fail|lại\s+fail|lại\s+lỗi|không\s+đúng|chưa\s+được|vẫn\s+lỗi|không\s+chạy|hỏng)\b",
    re.IGNORECASE,
)
_POSITIVE = re.compile(
    r"\b(?:ok|ổn\s+rồi|được\s+rồi|chuẩn|hoạt\s+động\s+được|ngon\s+rồi|pass)\b",
    re.IGNORECASE,
)
_PLAYFUL = re.compile(
    r"(?::\)+|😂|🤣|\bhaha+\b|\blol\b|\bcon\s+ch[oó]a\b|\bđm\b)",
    re.IGNORECASE,
)
_CONTINUATION = re.compile(
    r"\b(?:tiếp\s+tục|làm\s+tiếp|làm\s+nốt|xử\s+tiếp|tiếp\s+đi|triển\s+khai\s+đi|cứ\s+làm|xong\s+chưa|còn\s+gì)\b",
    re.IGNORECASE,
)
_ACK_ONLY = re.compile(
    r"\s*(?:ok|ừ|uh|được|chuẩn|rồi|done|xong)\s*[.!?…]*\s*",
    re.IGNORECASE,
)
_ASSISTANT_COMPLETE = re.compile(
    r"\b(?:XONG|đã\s+xong|đã\s+hoàn\s+tất|đã\s+hoàn\s+thành)\b",
    re.IGNORECASE,
)
_ASSISTANT_UNRESOLVED = re.compile(
    r"\b(?:BLOCKED|blocker|chưa\s+xong|vẫn\s+còn|đang\s+chờ|cần\s+(?:mày|bạn|owner))\b",
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


def _interaction_signals_from_user_message(
    user_message: str,
    response_signals: ResponseSignals,
) -> InteractionSignals:
    text = (user_message or "").strip()
    correction = bool(_CORRECTION.search(text))
    return InteractionSignals(
        explicit_serious=response_signals.explicit_serious,
        correction=correction,
        positive=bool(_POSITIVE.search(text)) and not correction,
        playful=bool(_PLAYFUL.search(text)),
        continuation=bool(_CONTINUATION.search(text)),
        substantive=bool(text) and _ACK_ONLY.fullmatch(text) is None,
    )


def _session_key(session_id: object = "") -> str:
    return str(session_id or "").strip()


def _get_session_state(session_id: object = "") -> InteractionState:
    key = _session_key(session_id)
    if not key:
        return InteractionState()
    with _SESSION_STATE_LOCK:
        state = _SESSION_STATES.get(key, InteractionState())
        if key in _SESSION_STATES:
            _SESSION_STATES.move_to_end(key)
        return state


def _store_session_state(session_id: object, state: InteractionState) -> None:
    key = _session_key(session_id)
    if not key:
        return
    with _SESSION_STATE_LOCK:
        _SESSION_STATES[key] = state
        _SESSION_STATES.move_to_end(key)
        while len(_SESSION_STATES) > _SESSION_STATE_LIMIT:
            _SESSION_STATES.popitem(last=False)


def _clear_session_state(
    session_id: object = "",
    old_session_id: object = "",
    new_session_id: object = "",
    **_kwargs,
):
    """Drop ephemeral state at Hermes session lifecycle boundaries."""

    keys = {
        _session_key(session_id),
        _session_key(old_session_id),
        _session_key(new_session_id),
    }
    keys.discard("")
    with _SESSION_STATE_LOCK:
        for key in keys:
            _SESSION_STATES.pop(key, None)
    return None


def _system_prompt_section(_session_info=None) -> str:
    """Stable, cache-safe Personal AI communication contract for new sessions."""

    policy = select_response_policy(PROFILE, ResponseSignals())
    directives = "\n".join(f"- {item}" for item in policy.style_directives)
    return (
        "P2P Personal AI behavior contract (V2 runtime bridge).\n"
        "Factual correctness and authoritative tool/data values outrank style. "
        "Never change amounts, currencies, units, routes, dates, vehicle/container "
        "types, business conditions, or other authoritative values merely to fit voice.\n"
        "Do not claim research, tool use, retrieval, memory writes, or actions unless "
        "they actually occurred in the active Hermes/P2P workflow.\n"
        "Ephemeral session adaptation may change conversational mode and continuation "
        "handling, but must never be described as human emotion, relationship scoring, "
        "biological state, sleep, or a hidden personal life.\n"
        "Keep the answer useful and direct; ask only when ambiguity genuinely blocks "
        "the requested outcome.\n"
        "Default communication directives:\n"
        f"{directives}"
    )


def _pre_llm_call(user_message: str = "", session_id: object = "", **_kwargs):
    """Inject explicit turn overrides plus bounded state-aware guidance."""

    response_signals = _signals_from_user_message(user_message)
    interaction_signals = _interaction_signals_from_user_message(
        user_message,
        response_signals,
    )

    state = advance_interaction_state(
        _get_session_state(session_id),
        interaction_signals,
    )
    _store_session_state(session_id, state)

    context_parts: list[str] = []

    if (
        response_signals.explicit_serious
        or response_signals.user_requested_short
        or response_signals.user_requested_deep
    ):
        policy = select_response_policy(PROFILE, response_signals)
        directives = "\n".join(f"- {item}" for item in policy.style_directives)
        context_parts.append(
            "P2P turn-level communication override (applies to this turn only):\n"
            f"- depth={policy.depth}\n"
            f"- seriousness={policy.seriousness:.2f}\n"
            f"- humor_allowed={str(policy.humor_allowed).lower()}\n"
            f"{directives}"
        )

    interaction_directives = build_interaction_directives(
        state,
        continuation=interaction_signals.continuation,
    )
    if interaction_directives:
        context_parts.append(
            "P2P ephemeral session adaptation (interaction handling only):\n"
            + "\n".join(f"- {item}" for item in interaction_directives)
        )

    if not context_parts:
        return None
    return {"context": "\n\n".join(context_parts)}


def _post_llm_call(
    assistant_response: str = "",
    session_id: object = "",
    **_kwargs,
):
    """Reflect coarse completion/open-loop evidence without durable writes."""

    key = _session_key(session_id)
    if not key:
        return None

    response = assistant_response or ""
    unresolved = bool(_ASSISTANT_UNRESOLVED.search(response))
    claimed_complete = bool(_ASSISTANT_COMPLETE.search(response)) and not unresolved
    state = reflect_assistant_outcome(
        _get_session_state(key),
        claimed_complete=claimed_complete,
        unresolved=unresolved,
    )
    _store_session_state(key, state)
    return None


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
        max_chars=3600,
    )
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_llm_call", _post_llm_call)
    ctx.register_hook("transform_llm_output", _transform_llm_output)
    ctx.register_hook("on_session_finalize", _clear_session_state)
    ctx.register_hook("on_session_reset", _clear_session_state)
