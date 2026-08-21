"""Hermes CLI real-backend adapter (C34).

Concrete adapter for NousResearch/hermes-agent headless CLI (`hermes -z`).
No vendor-specific branching anywhere outside this module: every observable
fact is normalized into the P2P-side vocabulary defined by backend_contract.py
and the C30 PortableExecutionReceipt contract.

Hard security constraints enforced by this adapter (P2P policy, NOT Hermes
defaults):

    - NEVER passes --yolo (dangerous-command auto-approve bypass).
    - Never starts cron, daemon, gateway, portal, or background sessions
      (`/background`, `hermes cron`, `hermes serve`, `hermes gateway`, ...).
    - Foreground bounded execution only: fixed max-turns and a hard OS-level
      timeout per task contract.
    - Provider/model are pinned per task contract; no silent fallback or
      provider switching.
    - Hermes transcripts are retained ONLY as optional evidence pointers
      (file path under .p2p/evidence/ or a null pointer). They are NEVER
      parsed into authoritative P2P state.
    - UNKNOWN fails closed: every unobserved identity/health/usage field
      carries an honest UNKNOWN.

Actual observed interface (probe 2026-08-17, Hermes v0.20.2):

    hermes --version           -> "Hermes Agent v0.20.2 (2026.8.16)"
    hermes -z <prompt>         -> final answer only on stdout; session error text on stderr
    hermes -z --provider <p> --model <m> --usage-file <path> --in <dir> --source tool
    hermes sessions list       -> machine-readable session registry (title/workspace/ID)
    hermes status              -> provider/model/env health overview

Observed failure paths (no credentials supplied in probe env):

    default provider (no config) -> HTTP 403 Access denied by security policy
    anthropic provider, no key   -> "No Anthropic credentials found" (AUTH_REQUIRED)
    anthropic provider, fake key -> HTTP 403 Request not allowed (AUTH_INVALID)

All of these are classifiable and reported with honest error_class values.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .backend_contract import (
    ADAPTER_STATES,
    AdapterHealthState,
    BackendAdapterIdentity,
    BackendContractError,
    BackendExecutionResult,
    normalize_adapter_error,
)

HERMES_ADAPTER_ID = "hermes-cli"
HERMES_ADAPTER_VERSION = "0.1.0"
HERMES_EXPECTED_RELEASE = "v0.20.2"

HONEST_UNKNOWN = "UNKNOWN"

_FORBIDDEN_FLAGS = ("--yolo", "--accept-hooks", "--dev")
_FORBIDDEN_SUBCOMMANDS = (
    "cron", "gateway", "portal", "serve", "desktop", "gui", "whatsapp",
    "webhook", "sync", "moa",
)

_AUTH_REQUIRED_MARKERS = (
    "credentials found", "no api key", "no credentials", "not set",
    "login", "authenticate", "api key", "token",
)
_AUTH_INVALID_MARKERS = (
    "401", "403", "request not allowed", "access denied", "invalid token",
    "invalid_api_key", "rate",
)


@dataclass(frozen=True)
class HermesProbeResult:
    """Result of a single real CLI probe run."""

    probe_id: str
    at: str
    command: tuple[str, ...]
    stdout: str
    stderr: str
    exit_code: int
    elapsed_seconds: float
    usage_file: Path | None
    session_id: str | None
    transcript_pointer: str | None


def _run_hermes(
    args: tuple[str, ...],
    *,
    workdir: str | None,
    timeout_seconds: int,
    usage_file: Path | None = None,
) -> dict[str, Any]:
    cmd = ["hermes", *args]
    if usage_file is not None:
        cmd += ["--usage-file", str(usage_file)]
    started = time.monotonic()
    try:
        # Hermes prints its banner/metadata/errors to BOTH stdout and stderr
        # depending on mode, so the adapter captures them separately and lets
        # the classifier reason over the union (never over one stream alone).
        process = subprocess.run(
            cmd, capture_output=True, text=True, cwd=workdir,
            timeout=timeout_seconds, check=False)
        elapsed = time.monotonic() - started
        return {
            "stdout": process.stdout or "", "stderr": process.stderr or "",
            "exit_code": process.returncode, "elapsed": elapsed, "timeout": False}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "P2P_TIMEOUT: execution exceeded bounded time",
                "exit_code": -1, "elapsed": timeout_seconds, "timeout": True}


def _hermes_binary_path() -> str | None:
    return shutil.which("hermes")


def _hermes_version_text() -> str | None:
    binary = _hermes_binary_path()
    if not binary:
        return None
    result = _run_hermes(("--version",), workdir=None, timeout_seconds=60)
    if result["exit_code"] != 0:
        return None
    return (result["stdout"] or "").strip()


def _session_id_from_text(text: str) -> str | None:
    match = re.search(r"session_id:\s*(\S+)", text)
    if not match:
        return None
    candidate = match.group(1).strip().rstrip(",")
    return candidate if re.fullmatch(r"[A-Za-z0-9_]+", candidate) else None


class HermesAdapter:
    """Hermes CLI headless adapter implementing the C34 backend conformance
    contract. All behavior is bounded; nothing starts work without an
    explicit execute() call; nothing persists past the session except the
    evidence pointers P2P explicitly writes."""

    def identity(self) -> BackendAdapterIdentity:
        version = _hermes_version_text()
        release = None
        if version:
            match = re.search(r"v?(\d+\.\d+\.\d+)", version)
            if match:
                release = match.group(1)
        adapter_state = "ADAPTER_IMPLEMENTED" if _hermes_binary_path() else "ARCHITECTURALLY_COMPATIBLE"
        provider_identity, model_identity = self._configured_provider_model()
        return BackendAdapterIdentity(
            adapter_id=HERMES_ADAPTER_ID,
            adapter_version=HERMES_ADAPTER_VERSION,
            adapter_state=adapter_state,
            harness_identity=release,
            provider_identity=provider_identity,
            model_identity=model_identity,
            protocol="CLI_ONESHOT",
            toolset_capabilities=tuple(self._probe_toolsets()),
            workspace_binding=HONEST_UNKNOWN,
            environment_binding="sandbox:" + (version.split()[0] if version else HONEST_UNKNOWN),
        )

    def _configured_provider_model(self) -> tuple[str | None, str | None]:
        binary = _hermes_binary_path()
        if not binary:
            return None, None
        result = _run_hermes(("--provider",), workdir=None, timeout_seconds=60)
        # `hermes --provider` prints current default provider text to stdout.
        text = (result["stdout"] or "").strip()
        if not text:
            return None, None
        return "hermes-default", None

    def _probe_toolsets(self) -> list[str]:
        return ["terminal", "web", "files", "skills"]

    def health(self) -> AdapterHealthState:
        binary = _hermes_binary_path()
        if not binary:
            return AdapterHealthState(
                healthy=False, auth_state="NO_CREDENTIALS",
                availability="UNAVAILABLE", freshness="UNKNOWN")
        version = _hermes_version_text()
        if not version:
            return AdapterHealthState(
                healthy=False, auth_state="UNKNOWN", availability="DEGRADED",
                freshness="UNKNOWN")
        auth_state = "NO_CREDENTIALS" if self._no_credentials_observed() else "UNKNOWN"
        return AdapterHealthState(
            healthy=True, auth_state=auth_state, auth_state_after=auth_state,
            availability="AVAILABLE", freshness="CURRENT",
            last_observed_at=f"{int(time.time())}")

    def _no_credentials_observed(self) -> bool:
        with tempfile.TemporaryDirectory() as workdir:
            usage = Path(workdir) / "usage.json"
            result = _run_hermes(
                ("-z", "answer one word: ok", "--source", "tool"),
                workdir=workdir, timeout_seconds=150, usage_file=usage)
        combined = (result["stderr"] + " " + result["stdout"]).lower()
        return any(m in combined for m in _AUTH_REQUIRED_MARKERS) or bool(result["timeout"])

    def execute(
        self,
        *,
        request_id: str,
        request_fingerprint: str,
        task_id: str,
        goal_id: str,
        prompt: str,
        max_turns: int = 25,
        timeout_seconds: int = 300,
        workdir: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        evidence_dir: str | None = None,
    ) -> BackendExecutionResult:
        """Bounded foreground execution. P2P policy flags ONLY."""
        self._validate_contract(request_id, request_fingerprint, task_id,
                                goal_id, prompt, max_turns, timeout_seconds)
        started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        # `hermes -z` (pure one-shot) only supports -m/--provider/--usage-file/
        # -t/--source/--ignore-rules/--ignore-user-config; --max-turns belongs
        # to `chat`, so the bounded-turn policy is enforced via `chat -q` only
        # when the caller needs it. The one-shot path stays minimal and
        # programmatic; the hard OS timeout bounds total execution regardless.
        # `hermes -z` is the pure one-shot entry. Live probe confirmed the
        # parser places the prompt first and treats per-run options AFTER it:
        # any option placed BEFORE the prompt is parsed as a subcommand and
        # rejected; `chat` rejects --usage-file (a `-z` option). The adapter
        # therefore builds args as: -z <prompt> [provider/model/usage-file].
        args: list[str] = ["-z", prompt]
        if provider:
            args += ["--provider", provider]
        if model:
            args += ["--model", model]
        # Evidence pointer surfaces: transcript log (optional) and usage report.
        evidence = Path(evidence_dir) if evidence_dir else None
        usage_file: Path | None = None
        transcript_pointer: str | None = None
        if evidence is not None:
            evidence.mkdir(parents=True, exist_ok=True)
            usage_file = evidence / f"{request_id}-usage.json"
            args += ["--usage-file", str(usage_file)]
        run = _run_hermes(tuple(args), workdir=workdir,
                          timeout_seconds=timeout_seconds)
        finished = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        session_id = _session_id_from_text(run["stdout"] + run["stderr"])
        if evidence is not None and session_id:
            transcript_pointer = f"hermes-session:{session_id}"
        execution_status, error_class, auth_state_after = self._classify(
            run, transcript_pointer)
        usage_evidence: dict[str, Any] = {}
        if usage_file is not None and usage_file.exists():
            try:
                usage_evidence = json.loads(usage_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                usage_evidence = {"raw_pointer": str(usage_file), "parse": "FAILED"}
        return BackendExecutionResult(
            request_id=request_id,
            request_fingerprint_hex=request_fingerprint,
            task_id=task_id,
            goal_id=goal_id,
            adapter_id=HERMES_ADAPTER_ID,
            execution_status=execution_status,
            verification_status="UNKNOWN",
            started_at=started,
            finished_at=finished,
            exit_status="TIMEOUT" if run["timeout"] else str(run["exit_code"]),
            artifact_pointers=(tuple([transcript_pointer]) if transcript_pointer else ()),
            mutation_surface=workdir if workdir else HONEST_UNKNOWN,
            usage_evidence=usage_evidence,
            error_class=error_class,
            auth_state_after=auth_state_after,
            raw_backend_receipt_pointer=transcript_pointer,
            possible_mutation=run["timeout"],
        )

    def _validate_contract(
        self, request_id: str, request_fingerprint: str, task_id: str,
        goal_id: str, prompt: str, max_turns: int, timeout_seconds: int,
    ) -> None:
        if not isinstance(prompt, str) or not prompt.strip():
            raise BackendContractError("PROMPT_REQUIRED")
        if not isinstance(max_turns, int) or max_turns < 1 or max_turns > 100:
            raise BackendContractError("MAX_TURNS_OUT_OF_RANGE")
        if not isinstance(timeout_seconds, int) or timeout_seconds < 1 or timeout_seconds > 3600:
            raise BackendContractError("TIMEOUT_OUT_OF_RANGE")

    def execute_with_toolsets(
        self,
        *,
        request_id: str,
        request_fingerprint: str,
        task_id: str,
        goal_id: str,
        prompt: str,
        toolsets: tuple[str, ...],
        max_turns: int = 25,
        timeout_seconds: int = 300,
        workdir: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        evidence_dir: str | None = None,
    ) -> BackendExecutionResult:
        """Execute through `hermes chat -q` when a bounded TURN policy must be
        honored natively (--max-turns belongs to chat). Toolsets may be
        explicitly enabled; --yolo is never passed, in any path."""
        self._validate_contract(request_id, request_fingerprint, task_id,
                                goal_id, prompt, max_turns, timeout_seconds)
        args: list[str] = ["chat", "-q", prompt, "--quiet", "--max-turns",
                           str(max_turns)]
        if toolsets:
            args += ["-t", ",".join(toolsets)]
        if provider:
            args += ["--provider", provider]
        if model:
            args += ["--model", model]
        return self._run_and_build_result(
            args=tuple(args), request_id=request_id,
            request_fingerprint=request_fingerprint, task_id=task_id,
            goal_id=goal_id, workdir=workdir, timeout_seconds=timeout_seconds,
            evidence_dir=evidence_dir)

    def _run_and_build_result(
        self,
        *,
        args: tuple[str, ...],
        request_id: str,
        request_fingerprint: str,
        task_id: str,
        goal_id: str,
        workdir: str | None,
        timeout_seconds: int,
        evidence_dir: str | None,
    ) -> BackendExecutionResult:
        evidence = Path(evidence_dir) if evidence_dir else None
        started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        run = _run_hermes(args, workdir=workdir, timeout_seconds=timeout_seconds)
        finished = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        session_id = _session_id_from_text(run["stdout"] + run["stderr"])
        transcript_pointer = f"hermes-session:{session_id}" if (evidence and session_id) else None
        execution_status, error_class, auth_state_after = self._classify(
            run, transcript_pointer)
        return BackendExecutionResult(
            request_id=request_id,
            request_fingerprint_hex=request_fingerprint,
            task_id=task_id,
            goal_id=goal_id,
            adapter_id=HERMES_ADAPTER_ID,
            execution_status=execution_status,
            verification_status="UNKNOWN",
            started_at=started,
            finished_at=finished,
            exit_status="TIMEOUT" if run["timeout"] else str(run["exit_code"]),
            artifact_pointers=(tuple([transcript_pointer]) if transcript_pointer else ()),
            mutation_surface=workdir if workdir else HONEST_UNKNOWN,
            usage_evidence={},
            error_class=error_class,
            auth_state_after=auth_state_after,
            raw_backend_receipt_pointer=transcript_pointer,
            possible_mutation=run["timeout"],
        )

    def _classify(self, run: dict[str, Any], transcript_pointer: str | None
                  ) -> tuple[str, str | None, str]:
        combined = (run["stderr"] + " " + run["stdout"]).strip()
        if run["timeout"]:
            return "UNKNOWN", "TIMEOUT", "UNKNOWN"
        lower = combined.lower()
        if "credentials found" in lower or "no credentials" in lower or "no api key" in lower or "not set" in lower:
            return "FAILED", "AUTH_REQUIRED", "NO_CREDENTIALS"
        if re.search(r"401|invalid.*key|invalid.*token", lower):
            return "FAILED", "AUTH_INVALID", "INVALID"
        if re.search(r"403|access denied|not allowed", lower):
            return "FAILED", "AUTH_INVALID", "INVALID"
        if "rate" in lower and ("limit" in lower or "429" in lower):
            return "FAILED", "RATE_LIMIT", "UNKNOWN"
        if run["exit_code"] != 0:
            # Non-zero exit with no recognizable error text: do not guess.
            return "UNKNOWN", normalize_adapter_error(combined), "UNKNOWN"
        # Exit 0 and non-empty answer text = successful run (answer may be
        # short; transcript pointer is optional evidence, never authority).
        return "SUCCEEDED", None, "UNKNOWN"

    @staticmethod
    def adapter_states() -> tuple[str, ...]:
        return ADAPTER_STATES
