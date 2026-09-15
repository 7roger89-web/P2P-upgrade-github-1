"""Bounded Free Claude Code -> Claude Code backend adapter for P2P.

This module deliberately reuses the C34 backend adapter seam.  It is NOT a
second P2P router and it does not mutate FCC's global provider/model config.
P2P chooses this adapter explicitly; FCC remains a subordinate proxy/runtime.

Safety and truthfulness boundaries for the first slice:

- foreground one-shot execution only via ``fcc-claude -p``;
- Claude Code permission mode is pinned to ``plan`` (non-mutating slice);
- session persistence is disabled and turns/time are bounded;
- no ``--dangerously-skip-permissions`` or equivalent bypass is ever passed;
- the requested model may be pinned per task through Claude Code ``--model``;
- the optional ``provider`` argument is evidence metadata only.  FCC provider
  selection/fallback is owned by FCC's runtime configuration, not by this
  adapter;
- unless an execution receipt proves the serving provider/model, the adapter
  records them as UNKNOWN.  A configured free-tier model is an intent, never a
  guarantee that a request cost zero or that no fallback consumed quota;
- raw stdout/stderr may be retained as evidence pointers only.  They never
  become authoritative P2P state.

The first slice intentionally certifies no mutation capability.  Code edits,
tests, Git writes, browser execution, and long-horizon autonomy require their
own representative proof before any later capability certification.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
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

FCC_CLAUDE_ADAPTER_ID = "fcc-claude-cli"
FCC_CLAUDE_ADAPTER_VERSION = "0.1.0"
FCC_CLAUDE_BINARY = "fcc-claude"
FCC_PROTOCOL = "CLAUDE_CODE_PRINT_VIA_FCC"
HONEST_UNKNOWN = "UNKNOWN"

_FORBIDDEN_FLAGS = (
    "--dangerously-skip-permissions",
    "--allow-dangerously-skip-permissions",
)


def _fcc_binary_path() -> str | None:
    return shutil.which(FCC_CLAUDE_BINARY)


def _run_fcc(
    args: tuple[str, ...],
    *,
    workdir: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Run one bounded foreground FCC Claude invocation."""
    binary = _fcc_binary_path()
    if binary is None:
        return {
            "stdout": "",
            "stderr": f"{FCC_CLAUDE_BINARY} not found",
            "exit_code": -1,
            "elapsed": 0.0,
            "timeout": False,
            "spawn_error": True,
        }

    command = [binary, *args]
    started = time.monotonic()
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "stdout": str(exc.stdout or ""),
            "stderr": str(exc.stderr or "") + "\nP2P_TIMEOUT: FCC execution exceeded bounded time",
            "exit_code": -1,
            "elapsed": float(timeout_seconds),
            "timeout": True,
            "spawn_error": False,
        }
    except OSError as exc:
        return {
            "stdout": "",
            "stderr": f"FCC_SPAWN_ERROR: {exc}",
            "exit_code": -1,
            "elapsed": time.monotonic() - started,
            "timeout": False,
            "spawn_error": True,
        }

    return {
        "stdout": process.stdout or "",
        "stderr": process.stderr or "",
        "exit_code": process.returncode,
        "elapsed": time.monotonic() - started,
        "timeout": False,
        "spawn_error": False,
    }


def _version_text() -> str | None:
    if _fcc_binary_path() is None:
        return None
    run = _run_fcc(("--version",), workdir=None, timeout_seconds=60)
    if run["exit_code"] != 0:
        return None
    text = (run["stdout"] or run["stderr"] or "").strip()
    return text[:240] or None


def _json_payload(stdout: str) -> dict[str, Any]:
    """Best-effort parse of Claude Code JSON output; evidence only."""
    text = str(stdout or "").strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _bounded_usage_evidence(
    *,
    payload: dict[str, Any],
    requested_model: str | None,
    provider_hint: str | None,
    elapsed: float,
) -> dict[str, Any]:
    """Expose useful cost/route evidence without inventing serving identity."""
    evidence: dict[str, Any] = {
        "transport": FCC_CLAUDE_BINARY,
        "requested_model": requested_model or "FCC_SERVER_DEFAULT",
        "requested_provider_hint": provider_hint or "UNSPECIFIED",
        "fallback_policy_source": "FCC_SERVER_CONFIG",
        "actual_provider": HONEST_UNKNOWN,
        "actual_model": HONEST_UNKNOWN,
        "fallback_observed": HONEST_UNKNOWN,
        "free_tier_guaranteed": False,
        "elapsed_seconds": round(float(elapsed), 6),
    }

    # Claude Code JSON output may expose usage/cost fields.  They are useful as
    # bounded evidence but do not prove which FCC provider actually served the
    # request, so provider/model identity remains UNKNOWN here.
    for key in ("usage", "total_cost_usd", "duration_ms", "num_turns", "session_id"):
        if key in payload:
            evidence[key] = payload[key]
    return evidence


class FccClaudeAdapter:
    """C34-compatible, non-mutating Claude Code execution through FCC."""

    def identity(self) -> BackendAdapterIdentity:
        version = _version_text()
        installed = _fcc_binary_path() is not None
        return BackendAdapterIdentity(
            adapter_id=FCC_CLAUDE_ADAPTER_ID,
            adapter_version=FCC_CLAUDE_ADAPTER_VERSION,
            adapter_state=(
                "ADAPTER_IMPLEMENTED" if installed else "ARCHITECTURALLY_COMPATIBLE"
            ),
            harness_identity=version or "claude-code-via-fcc",
            provider_identity="fcc-proxy",
            model_identity=None,
            protocol=FCC_PROTOCOL,
            toolset_capabilities=("REPO_READ", "REPO_SEARCH", "STATIC_ANALYSIS"),
            workspace_binding=HONEST_UNKNOWN,
            environment_binding="foreground-local",
        )

    def health(self) -> AdapterHealthState:
        if _fcc_binary_path() is None:
            return AdapterHealthState(
                healthy=False,
                auth_state="UNKNOWN",
                auth_state_after="UNKNOWN",
                availability="UNAVAILABLE",
                freshness="UNKNOWN",
            )
        version = _version_text()
        if version is None:
            return AdapterHealthState(
                healthy=False,
                auth_state="UNKNOWN",
                auth_state_after="UNKNOWN",
                availability="DEGRADED",
                freshness="UNKNOWN",
            )
        # Launcher presence/version proves the harness is callable, not that a
        # provider credential or free quota is valid.  Keep auth UNKNOWN until
        # an actual bounded request supplies evidence.
        return AdapterHealthState(
            healthy=True,
            auth_state="UNKNOWN",
            auth_state_after="UNKNOWN",
            availability="AVAILABLE",
            freshness="CURRENT",
            last_observed_at=str(int(time.time())),
        )

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
        self._validate_contract(prompt, max_turns, timeout_seconds, provider, model)

        args: list[str] = [
            "-p",
            prompt,
            "--output-format",
            "json",
            "--permission-mode",
            "plan",
            "--no-session-persistence",
            "--max-turns",
            str(max_turns),
        ]
        if model:
            args += ["--model", model]
        self._assert_safe_command(args)

        started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        run = _run_fcc(
            tuple(args),
            workdir=workdir,
            timeout_seconds=timeout_seconds,
        )
        finished = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        payload = _json_payload(run["stdout"])

        evidence_pointer = self._write_evidence(
            evidence_dir=evidence_dir,
            request_id=request_id,
            args=args,
            stdout=run["stdout"],
            stderr=run["stderr"],
            exit_code=run["exit_code"],
            payload=payload,
            provider=provider,
            model=model,
        )
        execution_status, error_class, auth_state_after = self._classify(run)
        usage = _bounded_usage_evidence(
            payload=payload,
            requested_model=model,
            provider_hint=provider,
            elapsed=run["elapsed"],
        )

        pointers = (evidence_pointer,) if evidence_pointer else ()
        output_pointers = pointers if execution_status == "SUCCEEDED" else ()
        possible_mutation = bool(run["timeout"] or execution_status == "UNKNOWN")

        return BackendExecutionResult(
            request_id=request_id,
            request_fingerprint_hex=request_fingerprint,
            task_id=task_id,
            goal_id=goal_id,
            adapter_id=FCC_CLAUDE_ADAPTER_ID,
            execution_status=execution_status,
            verification_status="UNKNOWN",
            started_at=started,
            finished_at=finished,
            exit_status="TIMEOUT" if run["timeout"] else str(run["exit_code"]),
            output_pointers=output_pointers,
            artifact_pointers=pointers,
            mutation_surface="NONE_PLANNING_MODE",
            usage_evidence=usage,
            error_class=error_class,
            auth_state_after=auth_state_after,
            raw_backend_receipt_pointer=evidence_pointer,
            possible_mutation=possible_mutation,
        )

    @staticmethod
    def _validate_contract(
        prompt: str,
        max_turns: int,
        timeout_seconds: int,
        provider: str | None,
        model: str | None,
    ) -> None:
        if not isinstance(prompt, str) or not prompt.strip():
            raise BackendContractError("PROMPT_REQUIRED")
        if not isinstance(max_turns, int) or max_turns < 1 or max_turns > 100:
            raise BackendContractError("MAX_TURNS_OUT_OF_RANGE")
        if not isinstance(timeout_seconds, int) or timeout_seconds < 1 or timeout_seconds > 3600:
            raise BackendContractError("TIMEOUT_OUT_OF_RANGE")
        for name, value in (("provider", provider), ("model", model)):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise BackendContractError(f"{name.upper()}_INVALID")

    @staticmethod
    def _assert_safe_command(args: list[str]) -> None:
        values = set(args)
        if any(flag in values for flag in _FORBIDDEN_FLAGS):
            raise BackendContractError("FCC_PERMISSION_BYPASS_FORBIDDEN")
        try:
            mode = args[args.index("--permission-mode") + 1]
        except (ValueError, IndexError) as exc:
            raise BackendContractError("FCC_PERMISSION_MODE_REQUIRED") from exc
        if mode != "plan":
            raise BackendContractError("FCC_NON_MUTATING_MODE_REQUIRED")

    @staticmethod
    def _classify(run: dict[str, Any]) -> tuple[str, str | None, str]:
        if run["timeout"]:
            return "FAILED", "TIMEOUT", "UNKNOWN"
        if run["spawn_error"]:
            return "FAILED", "UNAVAILABLE", "UNKNOWN"

        combined = f"{run['stderr']}\n{run['stdout']}".strip()
        if run["exit_code"] == 0 and str(run["stdout"] or "").strip():
            # Successful transport proves the configured FCC path was usable,
            # but not which fallback/provider served it.
            return "SUCCEEDED", None, "CONFIGURED"

        error_class = normalize_adapter_error(combined)
        if error_class is None:
            return "UNKNOWN", None, "UNKNOWN"
        auth_after = "INVALID" if error_class == "AUTH_INVALID" else "UNKNOWN"
        if error_class == "AUTH_REQUIRED":
            auth_after = "NO_CREDENTIALS"
        return "FAILED", error_class, auth_after

    @staticmethod
    def _write_evidence(
        *,
        evidence_dir: str | None,
        request_id: str,
        args: list[str],
        stdout: str,
        stderr: str,
        exit_code: int,
        payload: dict[str, Any],
        provider: str | None,
        model: str | None,
    ) -> str | None:
        if not evidence_dir:
            return None
        directory = Path(evidence_dir)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{request_id}-fcc-claude.json"
        # The prompt itself is intentionally not duplicated into evidence here.
        # Record the safe execution shape and outputs, not task secrets.
        safe_args = ["<PROMPT>" if i == 1 and args and args[0] == "-p" else value
                     for i, value in enumerate(args)]
        record = {
            "schema": "p2p-fcc-claude-evidence/1",
            "adapter_id": FCC_CLAUDE_ADAPTER_ID,
            "command_args": safe_args,
            "requested_provider_hint": provider or "UNSPECIFIED",
            "requested_model": model or "FCC_SERVER_DEFAULT",
            "actual_provider": HONEST_UNKNOWN,
            "actual_model": HONEST_UNKNOWN,
            "fallback_observed": HONEST_UNKNOWN,
            "free_tier_guaranteed": False,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "parsed_json": payload,
        }
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return str(path)

    @staticmethod
    def adapter_states() -> tuple[str, ...]:
        return ADAPTER_STATES
