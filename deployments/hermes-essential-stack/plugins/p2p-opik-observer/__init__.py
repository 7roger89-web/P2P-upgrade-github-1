"""Opt-in, fail-open Opik observer for Hermes/P2P.

The observer is deliberately not a control plane. It listens to documented
Hermes lifecycle hooks, buffers one turn in process memory, and sends a
finalized trace after the turn finishes. By default only operational metadata
is exported; prompts, tool arguments/results, subagent goals/summaries and
error-message bodies require the separate P2P_OPIK_CAPTURE_CONTENT=YES gate.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

_TRUE = {"1", "true", "yes", "on"}
_MAX_CONTENT_CHARS = 20_000
_SOURCE = "p2p-opik-observer"

_lock = threading.RLock()
_turns: dict[tuple[str, str], "TurnRecord"] = {}
_emitted: set[tuple[str, str]] = set()
_emitted_order: deque[tuple[str, str]] = deque(maxlen=2048)
_client = None
_client_failed = False


@dataclass
class SpanRecord:
    kind: str
    name: str
    started_at: datetime
    ended_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    usage: dict[str, int] | None = None
    model: str | None = None
    provider: str | None = None


@dataclass
class TurnRecord:
    session_id: str
    turn_id: str
    task_id: str = ""
    platform: str = ""
    model: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    status: str = "running"
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    spans: list[SpanRecord] = field(default_factory=list)
    open_api: dict[str, SpanRecord] = field(default_factory=dict)
    open_tools: dict[str, SpanRecord] = field(default_factory=dict)
    open_subagents: dict[str, SpanRecord] = field(default_factory=dict)


def _enabled() -> bool:
    return os.getenv("P2P_ENABLE_OPIK", "NO").strip().lower() in _TRUE


def _capture_content() -> bool:
    return (
        _enabled()
        and os.getenv("P2P_OPIK_CAPTURE_CONTENT", "NO").strip().lower() in _TRUE
    )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _dt(value: Any, fallback: datetime | None = None) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return fallback or _utcnow()


def _opaque(value: Any) -> str:
    text = "" if value is None else str(value)
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:24]


def _json_text(value: Any) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":"))
    except Exception:
        text = repr(value)
    if len(text) > _MAX_CONTENT_CHARS:
        return text[:_MAX_CONTENT_CHARS] + "...[truncated]"
    return text


def _content(label: str, value: Any) -> dict[str, Any] | None:
    if not _capture_content() or value is None:
        return None
    return {label: _json_text(value)}


def _turn_key(session_id: Any, turn_id: Any) -> tuple[str, str]:
    return (str(session_id or ""), str(turn_id or ""))


def _ensure_turn(
    *,
    session_id: Any = "",
    turn_id: Any = "",
    task_id: Any = "",
    platform: Any = "",
    model: Any = "",
) -> TurnRecord:
    key = _turn_key(session_id, turn_id)
    with _lock:
        record = _turns.get(key)
        if record is None:
            if len(_turns) >= 512:
                stale_key = next(iter(_turns))
                _turns.pop(stale_key, None)
                logger.warning("Opik observer evicted one unfinished turn buffer")
            record = TurnRecord(session_id=key[0], turn_id=key[1])
            _turns[key] = record
        if task_id:
            record.task_id = str(task_id)
        if platform:
            record.platform = str(platform)
        if model:
            record.model = str(model)
        return record


def _normalize_usage(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None

    def as_int(key: str) -> int | None:
        raw = value.get(key)
        if isinstance(raw, bool):
            return None
        if isinstance(raw, (int, float)) and raw >= 0:
            return int(raw)
        return None

    prompt = as_int("prompt_tokens")
    if prompt is None:
        prompt = as_int("input_tokens")
    completion = as_int("completion_tokens")
    if completion is None:
        completion = as_int("output_tokens")
    total = as_int("total_tokens")
    if total is None and (prompt is not None or completion is not None):
        total = (prompt or 0) + (completion or 0)

    result: dict[str, int] = {}
    if prompt is not None:
        result["prompt_tokens"] = prompt
    if completion is not None:
        result["completion_tokens"] = completion
    if total is not None:
        result["total_tokens"] = total
    return result or None


def _get_client():
    global _client, _client_failed
    if _client is not None:
        return _client
    if _client_failed or not _enabled():
        return None
    try:
        import opik  # imported lazily so disabled mode has no SDK side effects

        _client = opik.Opik(
            project_name=os.environ["OPIK_PROJECT_NAME"],
            workspace=os.environ["OPIK_WORKSPACE"],
            host=os.getenv("OPIK_URL_OVERRIDE", "https://www.comet.com/opik/api"),
            api_key=os.environ["OPIK_API_KEY"],
            batching=True,
        )
    except Exception as exc:  # observability must never break Hermes
        _client_failed = True
        logger.warning("Opik observer disabled after client init failure: %s", type(exc).__name__)
        return None
    return _client


def _span_metadata(span: SpanRecord) -> dict[str, Any]:
    metadata = {"source": _SOURCE, **span.metadata}
    return {key: value for key, value in metadata.items() if value is not None and value != ""}


def _emit(record: TurnRecord) -> bool:
    client = _get_client()
    if client is None:
        return False
    ended = record.ended_at or _utcnow()
    try:
        trace = client.trace(
            name="Hermes turn",
            start_time=record.started_at,
            end_time=ended,
            input=record.input,
            output=record.output,
            metadata={
                "source": _SOURCE,
                "session_id_hash": _opaque(record.session_id),
                "turn_id_hash": _opaque(record.turn_id),
                "task_id_hash": _opaque(record.task_id) if record.task_id else "",
                "platform": record.platform,
                "model": record.model,
                "status": record.status,
                "content_capture": _capture_content(),
                "authoritative": False,
            },
            tags=["p2p", "hermes", "opik-pilot"],
            thread_id=_opaque(record.session_id),
            project_name=os.environ["OPIK_PROJECT_NAME"],
            environment=os.getenv("OPIK_ENVIRONMENT", "development"),
        )
        for span in record.spans:
            span_end = span.ended_at or ended
            if span_end < span.started_at:
                span_end = span.started_at
            client.span(
                trace_id=trace.id,
                name=span.name,
                type=span.kind,
                start_time=span.started_at,
                end_time=span_end,
                metadata=_span_metadata(span),
                input=span.input,
                output=span.output,
                usage=span.usage,
                model=span.model,
                provider=span.provider,
                project_name=os.environ["OPIK_PROJECT_NAME"],
            )
        return True
    except Exception as exc:  # tracing is best-effort, never execution authority
        logger.warning("Opik observer dropped one Hermes turn: %s", type(exc).__name__)
        return False


def _complete_and_emit(key: tuple[str, str], *, status: str, output: dict[str, Any] | None = None) -> None:
    with _lock:
        if key in _emitted:
            return
        record = _turns.pop(key, None)
        if record is None:
            record = TurnRecord(session_id=key[0], turn_id=key[1])
        record.status = status
        record.ended_at = _utcnow()
        if output is not None:
            record.output = output
        now = record.ended_at
        for mapping in (record.open_api, record.open_tools, record.open_subagents):
            for span in mapping.values():
                if span.ended_at is None:
                    span.ended_at = now
                    span.metadata.setdefault("status", "incomplete")
            mapping.clear()
        if len(_emitted_order) == _emitted_order.maxlen:
            _emitted.discard(_emitted_order[0])
        _emitted_order.append(key)
        _emitted.add(key)
    _emit(record)


def _pre_llm_call(
    session_id: Any = "",
    turn_id: Any = "",
    task_id: Any = "",
    platform: Any = "",
    model: Any = "",
    user_message: Any = None,
    **_kwargs,
):
    record = _ensure_turn(
        session_id=session_id,
        turn_id=turn_id,
        task_id=task_id,
        platform=platform,
        model=model,
    )
    if record.input is None:
        record.input = _content("user_message", user_message)
    return None


def _pre_api_request(
    session_id: Any = "",
    turn_id: Any = "",
    task_id: Any = "",
    platform: Any = "",
    model: Any = "",
    provider: Any = "",
    api_request_id: Any = "",
    api_call_count: Any = None,
    retry_count: Any = None,
    started_at: Any = None,
    request: Any = None,
    **_kwargs,
):
    record = _ensure_turn(
        session_id=session_id,
        turn_id=turn_id,
        task_id=task_id,
        platform=platform,
        model=model,
    )
    request_key = str(api_request_id or f"api-{len(record.spans)}")
    span = SpanRecord(
        kind="llm",
        name="Hermes LLM request",
        started_at=_dt(started_at),
        metadata={
            "api_request_id_hash": _opaque(api_request_id),
            "api_call_count": api_call_count,
            "retry_count": retry_count,
            "status": "running",
        },
        input=_content("request", request),
        model=str(model or "") or None,
        provider=str(provider or "") or None,
    )
    with _lock:
        record.spans.append(span)
        record.open_api[request_key] = span
    return None


def _finish_api(
    *,
    status: str,
    session_id: Any = "",
    turn_id: Any = "",
    api_request_id: Any = "",
    ended_at: Any = None,
    api_duration: Any = None,
    finish_reason: Any = None,
    response: Any = None,
    usage: Any = None,
    error_type: Any = None,
    error_message: Any = None,
    model: Any = "",
    provider: Any = "",
    **_kwargs,
) -> None:
    record = _ensure_turn(session_id=session_id, turn_id=turn_id, model=model)
    request_key = str(api_request_id or "")
    with _lock:
        span = record.open_api.pop(request_key, None)
        if span is None:
            end = _dt(ended_at)
            duration_ms = api_duration if isinstance(api_duration, (int, float)) else 0
            span = SpanRecord(
                kind="llm",
                name="Hermes LLM request",
                started_at=end - timedelta(milliseconds=max(0, duration_ms)),
            )
            record.spans.append(span)
        span.ended_at = _dt(ended_at)
        span.metadata.update(
            {
                "status": status,
                "finish_reason": finish_reason,
                "error_type": str(error_type or "") or None,
                "has_error_message": bool(error_message),
            }
        )
        if _capture_content() and error_message:
            span.metadata["error_message"] = _json_text(error_message)
        span.output = _content("response", response)
        span.usage = _normalize_usage(usage)
        if model:
            span.model = str(model)
        if provider:
            span.provider = str(provider)


def _post_api_request(**kwargs):
    _finish_api(status="ok", **kwargs)
    return None


def _api_request_error(**kwargs):
    _finish_api(status="error", **kwargs)
    return None


def _pre_tool_call(
    session_id: Any = "",
    turn_id: Any = "",
    tool_call_id: Any = "",
    tool_name: Any = "",
    args: Any = None,
    **_kwargs,
):
    record = _ensure_turn(session_id=session_id, turn_id=turn_id)
    call_key = str(tool_call_id or f"tool-{len(record.spans)}")
    span = SpanRecord(
        kind="tool",
        name=f"Hermes tool: {tool_name or 'unknown'}",
        started_at=_utcnow(),
        metadata={
            "tool_name": str(tool_name or ""),
            "tool_call_id_hash": _opaque(tool_call_id),
            "status": "running",
        },
        input=_content("args", args),
    )
    with _lock:
        record.spans.append(span)
        record.open_tools[call_key] = span
    return None


def _post_tool_call(
    session_id: Any = "",
    turn_id: Any = "",
    tool_call_id: Any = "",
    tool_name: Any = "",
    result: Any = None,
    duration_ms: Any = None,
    status: Any = "",
    error_type: Any = None,
    error_message: Any = None,
    **_kwargs,
):
    record = _ensure_turn(session_id=session_id, turn_id=turn_id)
    call_key = str(tool_call_id or "")
    with _lock:
        span = record.open_tools.pop(call_key, None)
        if span is None:
            end = _utcnow()
            duration = duration_ms if isinstance(duration_ms, (int, float)) else 0
            span = SpanRecord(
                kind="tool",
                name=f"Hermes tool: {tool_name or 'unknown'}",
                started_at=end - timedelta(milliseconds=max(0, duration)),
            )
            record.spans.append(span)
        span.ended_at = _utcnow()
        span.metadata.update(
            {
                "tool_name": str(tool_name or ""),
                "status": str(status or "ok"),
                "duration_ms": duration_ms if isinstance(duration_ms, (int, float)) else None,
                "error_type": str(error_type or "") or None,
                "has_error_message": bool(error_message),
            }
        )
        if _capture_content() and error_message:
            span.metadata["error_message"] = _json_text(error_message)
        span.output = _content("result", result)
    return None


def _subagent_start(
    session_id: Any = "",
    turn_id: Any = "",
    parent_session_id: Any = "",
    parent_turn_id: Any = "",
    child_session_id: Any = "",
    child_subagent_id: Any = "",
    child_role: Any = "",
    child_goal: Any = None,
    **_kwargs,
):
    sid = parent_session_id or session_id
    tid = parent_turn_id or turn_id
    record = _ensure_turn(session_id=sid, turn_id=tid)
    child_key = str(child_session_id or child_subagent_id or f"subagent-{len(record.spans)}")
    span = SpanRecord(
        kind="general",
        name=f"Hermes subagent: {child_role or 'worker'}",
        started_at=_utcnow(),
        metadata={
            "child_session_id_hash": _opaque(child_session_id),
            "child_subagent_id_hash": _opaque(child_subagent_id),
            "child_role": str(child_role or ""),
            "status": "running",
        },
        input=_content("goal", child_goal),
    )
    with _lock:
        record.spans.append(span)
        record.open_subagents[child_key] = span
    return None


def _subagent_stop(
    session_id: Any = "",
    turn_id: Any = "",
    parent_session_id: Any = "",
    parent_turn_id: Any = "",
    child_session_id: Any = "",
    child_subagent_id: Any = "",
    child_role: Any = "",
    summary: Any = None,
    status: Any = "",
    duration: Any = None,
    **_kwargs,
):
    sid = parent_session_id or session_id
    tid = parent_turn_id or turn_id
    record = _ensure_turn(session_id=sid, turn_id=tid)
    child_key = str(child_session_id or child_subagent_id or "")
    with _lock:
        span = record.open_subagents.pop(child_key, None)
        if span is None:
            span = SpanRecord(
                kind="general",
                name=f"Hermes subagent: {child_role or 'worker'}",
                started_at=_utcnow(),
            )
            record.spans.append(span)
        span.ended_at = _utcnow()
        span.metadata.update(
            {
                "child_session_id_hash": _opaque(child_session_id),
                "child_subagent_id_hash": _opaque(child_subagent_id),
                "child_role": str(child_role or ""),
                "status": str(status or "finished"),
                "duration": duration if isinstance(duration, (int, float)) else None,
            }
        )
        span.output = _content("summary", summary)
    return None


def _post_llm_call(
    session_id: Any = "",
    turn_id: Any = "",
    assistant_response: Any = None,
    **_kwargs,
):
    key = _turn_key(session_id, turn_id)
    _complete_and_emit(
        key,
        status="completed",
        output=_content("assistant_response", assistant_response),
    )
    return None


def _on_session_end(
    session_id: Any = "",
    turn_id: Any = "",
    failed: Any = False,
    interrupted: Any = False,
    turn_exit_reason: Any = "",
    **_kwargs,
):
    # Successful turns are emitted by post_llm_call so the final response can
    # be included only when the explicit content gate is on. This hook is the
    # terminal fallback for failed/interrupted turns.
    if failed or interrupted:
        status = "failed" if failed else "interrupted"
        key = _turn_key(session_id, turn_id)
        record = _ensure_turn(session_id=session_id, turn_id=turn_id)
        if turn_exit_reason:
            record.output = (
                {"turn_exit_reason": _json_text(turn_exit_reason)}
                if _capture_content()
                else {"turn_exit_reason_present": True}
            )
        _complete_and_emit(key, status=status)
    return None


def _on_session_finalize(**_kwargs):
    client = _client
    if client is None:
        return None
    try:
        delivered = client.flush(timeout=2)
        if delivered is False:
            logger.warning("Opik observer flush ended with undelivered telemetry")
    except Exception as exc:
        logger.warning("Opik observer flush failure: %s", type(exc).__name__)
    return None


def register(ctx) -> None:
    """Register observer hooks only after the explicit local opt-in gate."""

    if not _enabled():
        return

    for hook_name, callback in (
        ("pre_llm_call", _pre_llm_call),
        ("pre_api_request", _pre_api_request),
        ("post_api_request", _post_api_request),
        ("api_request_error", _api_request_error),
        ("pre_tool_call", _pre_tool_call),
        ("post_tool_call", _post_tool_call),
        ("subagent_start", _subagent_start),
        ("subagent_stop", _subagent_stop),
        ("post_llm_call", _post_llm_call),
        ("on_session_end", _on_session_end),
        ("on_session_finalize", _on_session_finalize),
    ):
        ctx.register_hook(hook_name, callback)
