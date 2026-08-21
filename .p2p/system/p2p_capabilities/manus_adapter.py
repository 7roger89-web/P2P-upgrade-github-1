"""Manus API real-backend adapter (C34).

Concrete adapter for the official Manus REST API (https://api.manus.ai/v2).
No vendor-specific branching exists anywhere outside this module: every
observable fact is normalized into the P2P-side vocabulary defined by
backend_contract.py and the C30 PortableExecutionReceipt contract.

Hard security constraints enforced by this adapter (P2P policy, NOT Manus
defaults):

    - Foreground bounded execution only: a bounded poll loop with a hard
      maximum number of poll cycles and a hard per-poll HTTP timeout. If
      the remote task is still running after the budget, the adapter calls
      task.stop (or marks execution EXPIRED) — it never abandons a task
      running unbounded in the background.
    - Connector/skill enablement is explicit and minimal: the adapter
      supplies empty connectors/enable_skills/force_skills by default, so a
      task never inherits unbounded default skill access silently.
    - Provider profile is pinned per task contract (agent_profile); no
      silent fallback or profile switching.
    - Task artifacts are consumed ONLY as optional evidence pointers
      (task_url, message payload pointers, credit_usage) and are NEVER
      parsed into authoritative P2P state beyond the normalized
      BackendExecutionResult.
    - UNKNOWN fails closed: every unobserved identity/health/usage field
      carries an honest UNKNOWN.

Actual observed interface (probe 2026-08-17, live key):

    GET  /v2/task.list?limit=&order=       -> {"ok":true,"data":[...]} task registry
    POST /v2/task.create                   -> {"ok":true,"task_id","task_url",...}
    GET  /v2/task.detail?task_id=          -> {"ok":true,"task":{"status",...}}
    GET  /v2/task.listMessages?task_id=    -> {"ok":true,"messages":[events],...}

Observed status vocabulary: running, stopped, waiting, error.
Observed usage evidence: task.credit_usage (integer, may be absent until
consumed). Observed answer event: assistant_message.content.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .backend_contract import (
        AdapterHealthState,
        BackendAdapterIdentity,
        BackendContractError,
        BackendExecutionResult,
        normalize_adapter_error,
    )
except ImportError:
    from backend_contract import (
        AdapterHealthState,
        BackendAdapterIdentity,
        BackendContractError,
        BackendExecutionResult,
        normalize_adapter_error,
    )

MANUS_ADAPTER_ID = "manus-api"
MANUS_ADAPTER_VERSION = "0.1.0"
MANUS_BASE_URL = "https://api.manus.ai/v2"
DEFAULT_AGENT_PROFILE = "manus-1.6-lite"

HONEST_UNKNOWN = "UNKNOWN"

MANUS_STATUS_VALID = {"running", "stopped", "waiting", "error"}


def _manus_key() -> str | None:
    """Read-only load of the Manus API key. Caller decides policy."""
    import os
    from pathlib import Path as _P
    try:
        # Portability correction: use home directory instead of hardcoded /home/ubuntu
        key_path = _P(os.path.expanduser("~/.secrets/manus_api_key"))
        if key_path.exists():
            return key_path.read_text(encoding="utf-8").strip() or None
    except OSError:
        pass
    # Fallback to environment variable
    return os.environ.get("MANUS_API_KEY")


@dataclass(frozen=True)
class ManusProbeResult:
    """Result of a single real API probe run (raw wire evidence)."""

    probe_id: str
    at: str
    endpoint: str
    http_status: int
    body: dict[str, Any]


class ManusAdapter:
    """Manus REST API adapter implementing the C34 backend conformance
    contract. All execution is bounded; nothing starts work without an
    explicit execute() call; nothing persists past the session except the
    evidence pointers P2P explicitly writes."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else _manus_key()
        self._key_prefix: str | None = (
            self._api_key[:8] + "..." if self._api_key else None)

    # ---------------------------------------------------------------- identity

    def identity(self) -> BackendAdapterIdentity:
        has_key = bool(self._api_key)
        adapter_state = "ADAPTER_IMPLEMENTED" if has_key else "ARCHITECTURALLY_COMPATIBLE"
        harness, provider, model = self._observed_identities()
        return BackendAdapterIdentity(
            adapter_id=MANUS_ADAPTER_ID,
            adapter_version=MANUS_ADAPTER_VERSION,
            adapter_state=adapter_state,
            harness_identity=harness,
            provider_identity=provider,
            model_identity=model,
            protocol="HTTPS_REST",
            toolset_capabilities=tuple(self._probe_toolsets()),
            workspace_binding=HONEST_UNKNOWN,
            environment_binding="cloud:manus.im",
        )

    def _observed_identities(self) -> tuple[str | None, str | None, str | None]:
        """Best-effort identity discovery from a read-only list call."""
        if not self._api_key:
            return None, None, None
        try:
            body = self._request("GET", "/task.list", {"limit": "1", "order": "desc"})
            if isinstance(body, dict) and body.get("ok"):
                tasks = body.get("data") or []
                profiles = {t.get("agent_profile") for t in tasks if t.get("agent_profile")}
                harness = "manus-1.6" if profiles else None
                return harness, "manus-cloud", list(profiles)[0] if len(profiles) == 1 else "mixed" if profiles else None
        except (OSError, ValueError):
            pass
        return None, None, None

    def _probe_toolsets(self) -> list[str]:
        return ["terminal", "browser", "code", "files", "slides", "websites"]

    # ------------------------------------------------------------------ health

    def health(self) -> AdapterHealthState:
        if not self._api_key:
            return AdapterHealthState(
                healthy=False, auth_state="NO_CREDENTIALS",
                availability="UNAVAILABLE", freshness="UNKNOWN")
        try:
            body = self._request("GET", "/task.list", {"limit": "1", "order": "desc"})
            if isinstance(body, dict) and body.get("ok"):
                return AdapterHealthState(
                    healthy=True, auth_state="VALID",
                    availability="AVAILABLE", freshness="CURRENT",
                    last_observed_at=str(int(time.time())))
            return AdapterHealthState(
                healthy=False, auth_state="INVALID",
                availability="DEGRADED", freshness="UNKNOWN")
        except OSError as exc:
            return AdapterHealthState(
                healthy=False, auth_state="UNKNOWN",
                availability="UNREACHABLE", freshness="UNKNOWN",
                last_error=f"{exc}")

    # ------------------------------------------------------------ execution

    def execute(
        self,
        *,
        request_id: str,
        request_fingerprint: str,
        task_id: str,
        goal_id: str,
        prompt: str,
        max_turns: int = 25,
        timeout_seconds: int = 900,
        title: str | None = None,
        agent_profile: str | None = None,
        evidence_dir: str | None = None,
    ) -> BackendExecutionResult:
        """Bounded foreground execution: create task, poll within budget,
        stop if still running at expiry. No infinite loops; no detachment."""
        if not self._api_key:
            raise BackendContractError("AUTH_REQUIRED")
        self._validate_contract(prompt, max_turns, timeout_seconds)
        started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        title = title or f"p2p-{request_id}"
        profile = agent_profile or DEFAULT_AGENT_PROFILE
        create_body = {
            "message": {"content": [{"type": "text", "text": prompt}],
                        "connectors": [], "enable_skills": [], "force_skills": []},
            "hide_in_task_list": False, "share_visibility": "private",
            "agent_profile": profile, "title": title,
        }
        create = self._request("POST", "/task.create", None, json_payload=create_body)
        if not (isinstance(create, dict) and create.get("ok")):
            error_class = self._classify_api_error(create)
            return self._failed_result(
                request_id, request_fingerprint, task_id, goal_id,
                started, error_class=error_class)
        remote_task_id = str(create.get("task_id"))
        task_url = str(create.get("task_url") or HONEST_UNKNOWN)
        transcript_pointer = f"manus-task:{remote_task_id}" if remote_task_id else None
        evidence = Path(evidence_dir) if evidence_dir else None
        if evidence is not None:
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / f"{request_id}-create.json").write_text(
                json.dumps(create, indent=1), encoding="utf-8")
        started_ts = time.time()
        final_status = HONEST_UNKNOWN
        credit_usage: int | None = None
        answer_text: str | None = None
        error_message: dict[str, Any] | None = None
        poll_interval = 8.0
        budget_end = started_ts + timeout_seconds
        status_pointer = transcript_pointer
        while time.time() < budget_end:
            detail = self._request("GET", "/task.detail", {"task_id": remote_task_id})
            detail_task = (detail or {}).get("task") or {}
            if detail_task.get("status") in MANUS_STATUS_VALID:
                final_status = detail_task["status"]
                if detail_task.get("credit_usage") is not None:
                    credit_usage = int(detail_task["credit_usage"])
            else:
                final_status = HONEST_UNKNOWN
            if evidence is not None and isinstance(detail, dict):
                (evidence / f"{request_id}-detail.json").write_text(
                    json.dumps(detail, indent=1), encoding="utf-8")
            if final_status in ("stopped", "error"):
                break
            if time.time() + poll_interval * 2 >= budget_end:
                break
            time.sleep(poll_interval)
        # Budget expired while remote still active: attempt stop; then fail
        # closed rather than pretending success.
        expired = (final_status in (HONEST_UNKNOWN, "running", "waiting"))
        if expired:
            self._request("POST", "/task.stop", json_payload={"task_id": remote_task_id})
        messages = []
        try:
            msgs_body = self._request(
                "GET", "/task.listMessages",
                {"task_id": remote_task_id, "order": "asc", "limit": "200"})
            messages = (msgs_body or {}).get("messages") or []
            if evidence is not None and isinstance(msgs_body, dict):
                (evidence / f"{request_id}-messages.json").write_text(
                    json.dumps(msgs_body, indent=1), encoding="utf-8")
        except OSError:
            messages = []
        for event in messages:
            if event.get("type") == "assistant_message":
                answer_text = (event.get("assistant_message") or {}).get("content")
                if answer_text:
                    break
            if event.get("type") == "error_message":
                error_message = event.get("error_message")
        finished = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        return self._build_result(
            request_id=request_id, request_fingerprint=request_fingerprint,
            task_id=task_id, goal_id=goal_id, started_at=started,
            finished_at=finished, remote_task_id=remote_task_id,
            task_url=task_url, final_status=final_status,
            credit_usage=credit_usage, answer_text=answer_text,
            error_message=error_message, expired=expired,
            transcript_pointer=transcript_pointer,
            message_pointer=f"manus-messages:{remote_task_id}")

    # ------------------------------------------------------------- internals

    def _validate_contract(self, prompt: str, max_turns: int,
                           timeout_seconds: int) -> None:
        if not isinstance(prompt, str) or not prompt.strip():
            raise BackendContractError("PROMPT_REQUIRED")
        if not isinstance(max_turns, int) or max_turns < 1 or max_turns > 100:
            raise BackendContractError("MAX_TURNS_OUT_OF_RANGE")
        if not isinstance(timeout_seconds, int) or timeout_seconds < 1 or timeout_seconds > 3600:
            raise BackendContractError("TIMEOUT_OUT_OF_RANGE")

    def _request(self, method: str, path: str, params: dict[str, str] | None = None,
                 json_payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
        query = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        url = f"{MANUS_BASE_URL}{path}" + (f"?{query}" if query else "")
        body = None
        if json_payload is not None:
            body = json.dumps(json_payload).encode("utf-8")
            method = "POST" if method != "POST" else "POST"
        request = urllib.request.Request(url, data=body, method=method)
        request.add_header("Content-Type", "application/json")
        request.add_header("x-manus-api-key", self._api_key)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _classify_api_error(self, body: dict[str, Any] | None) -> str | None:
        if not isinstance(body, dict):
            return normalize_adapter_error(str(body))
        error = body.get("error") or {}
        code = str(error.get("code") or "").lower()
        message = str(error.get("message") or "").lower()
        if any(token in code or token in message
               for token in ("invalid_api_key", "unauthorized", "authentication", "401")):
            return "AUTH_INVALID"
        if any(token in code or token in message
               for token in ("forbidden", "access", "403")):
            return "AUTH_INVALID"
        if any(token in code or token in message for token in ("rate", "throttl", "429")):
            return "RATE_LIMIT"
        return "EXECUTION_FAILED"

    def _build_result(
        self,
        *,
        request_id: str, request_fingerprint: str, task_id: str, goal_id: str,
        started_at: str, finished_at: str, remote_task_id: str,
        task_url: str, final_status: str, credit_usage: int | None,
        answer_text: str | None, error_message: dict[str, Any] | None,
        expired: bool, transcript_pointer: str | None,
        message_pointer: str | None,
    ) -> BackendExecutionResult:
        artifact_pointers = tuple(filter(None, (transcript_pointer, message_pointer)))
        execution_status, error_class = self._map_terminal(
            final_status, expired, error_message)
        usage_evidence: dict[str, Any] = {}
        if credit_usage is not None:
            usage_evidence["credit_usage"] = credit_usage
            usage_evidence["units"] = "manus-credits"
            usage_evidence["source"] = "task.detail.credit_usage"
        output_pointers = (f"text://{answer_text}",) if answer_text else ()
        return BackendExecutionResult(
            request_id=request_id,
            request_fingerprint_hex=request_fingerprint,
            task_id=task_id,
            goal_id=goal_id,
            adapter_id=MANUS_ADAPTER_ID,
            execution_status=execution_status,
            verification_status="UNKNOWN",
            started_at=started_at,
            finished_at=finished_at,
            exit_status="EXPIRED" if expired else final_status,
            output_pointers=output_pointers,
            artifact_pointers=artifact_pointers,
            mutation_surface=HONEST_UNKNOWN,
            usage_evidence=usage_evidence,
            error_class=error_class,
            auth_state_after="VALID" if not error_class else "UNKNOWN",
            raw_backend_receipt_pointer=task_url,
            possible_mutation=False,
        )

    def _map_terminal(self, final_status: str, expired: bool,
                      error_message: dict[str, Any] | None
                      ) -> tuple[str, str | None]:
        if expired:
            return "UNKNOWN", "TIMEOUT"
        if final_status == "stopped":
            if error_message:
                return "FAILED", "EXECUTION_FAILED"
            return "SUCCEEDED", None
        if final_status == "error":
            return "FAILED", "EXECUTION_FAILED"
        return "UNKNOWN", "EXECUTION_FAILED"

    def _failed_result(self, request_id: str, request_fingerprint: str,
                       task_id: str, goal_id: str, started_at: str,
                       error_class: str | None) -> BackendExecutionResult:
        return BackendExecutionResult(
            request_id=request_id,
            request_fingerprint_hex=request_fingerprint,
            task_id=task_id,
            goal_id=goal_id,
            adapter_id=MANUS_ADAPTER_ID,
            execution_status="FAILED",
            verification_status="UNKNOWN",
            started_at=started_at,
            finished_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            exit_status="HTTP_ERROR",
            artifact_pointers=(),
            mutation_surface=HONEST_UNKNOWN,
            usage_evidence={},
            error_class=error_class,
            auth_state_after=self._api_key and "VALID" or "NO_CREDENTIALS",
            raw_backend_receipt_pointer=None,
            possible_mutation=False,
        )
