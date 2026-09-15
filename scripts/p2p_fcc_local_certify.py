#!/usr/bin/env python3
"""Live, read-only certification for P2P's FCC strict local bus.

The command deliberately starts an ISOLATED temporary FCC server bound to
127.0.0.1. It does not reuse or modify the user's normal FCC server/config.

The temporary FCC runtime has:
- one selected local primary model;
- MODEL_FALLBACKS empty;
- only loopback local provider URLs;
- a temporary auth token;
- no inherited proxy variables or cloud provider credentials.

It then invokes the existing P2P fcc-claude adapter in plan mode, verifies a
read-only marker, terminates the temporary FCC server, and leaves only evidence.

Exit codes:
  0 = strict loopback path executed successfully
  2 = blocked/not ready (safe failure)
  1 = unexpected local tooling error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
P2P_SYSTEM = REPO_ROOT / ".p2p" / "system"
if str(P2P_SYSTEM) not in sys.path:
    sys.path.insert(0, str(P2P_SYSTEM))

from p2p_capabilities.fcc_claude_adapter import FccClaudeAdapter  # noqa: E402
from p2p_capabilities.fcc_local_bus import (  # noqa: E402
    LOCAL_PROVIDER_DEFAULTS,
    assess_local_only_runtime,
    discover_local_models,
    fetch_running_fcc_admin_config,
    provider_urls_from_admin,
    select_best_local_model,
)

MARKER = "P2P_FCC_LOCAL_OK"

_SAFE_ENV_KEYS = {
    "PATH",
    "PATHEXT",
    "SystemRoot",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "TEMP",
    "TMP",
    "TMPDIR",
    "USERPROFILE",
    "HOME",
    "LOCALAPPDATA",
    "APPDATA",
    "PROGRAMDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "PROGRAMW6432",
    "USERNAME",
    "USERDOMAIN",
    "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE",
    "LANG",
    "LC_ALL",
    "TERM",
    "SHELL",
    # Preserve an explicit local Claude binary override, but no provider creds.
    "CLAUDE_CLI_BIN",
}


def _write_report(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _health_ready(port: int, *, timeout_seconds: float = 20.0) -> bool:
    import urllib.error
    import urllib.request

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with opener.open(url, timeout=1.0) as response:
                payload = json.loads(response.read(100_000).decode("utf-8"))
            if isinstance(payload, dict) and payload.get("status") == "healthy":
                return True
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            time.sleep(0.2)
    return False


def _safe_child_env(
    *,
    config_path: Path,
    port: int,
    auth_token: str,
    selected_model: str,
    provider_urls: Mapping[str, str],
) -> dict[str, str]:
    child = {
        key: value
        for key, value in os.environ.items()
        if key in _SAFE_ENV_KEYS and isinstance(value, str)
    }
    child.update(
        {
            "FCC_ENV_FILE": str(config_path),
            "HOST": "127.0.0.1",
            "PORT": str(port),
            "FCC_OPEN_BROWSER": "false",
            "MESSAGING_PLATFORM": "none",
            "MODEL": selected_model,
            "MODEL_FALLBACKS": "",
            "PROXY_AUTH_ENABLED": "true",
            "ANTHROPIC_AUTH_TOKEN": auth_token,
            "NO_PROXY": "127.0.0.1,localhost,::1",
            "no_proxy": "127.0.0.1,localhost,::1",
            "OLLAMA_BASE_URL": provider_urls["ollama"],
            "LM_STUDIO_BASE_URL": provider_urls["lmstudio"],
            "LLAMACPP_BASE_URL": provider_urls["llamacpp"],
        }
    )
    # Intentionally absent: HTTP_PROXY/HTTPS_PROXY/ALL_PROXY and every cloud
    # provider credential. The child receives only the whitelist above.
    return child


def _write_isolated_env(
    path: Path,
    *,
    port: int,
    auth_token: str,
    selected_model: str,
    provider_urls: Mapping[str, str],
) -> None:
    # This file lives only in TemporaryDirectory and is removed in finally.
    lines = [
        "FCC_CONFIG_SCHEMA=1",
        "HOST=127.0.0.1",
        f"PORT={port}",
        "FCC_OPEN_BROWSER=false",
        "MESSAGING_PLATFORM=none",
        f"MODEL={selected_model}",
        "MODEL_FALLBACKS=",
        "PROXY_AUTH_ENABLED=true",
        f"ANTHROPIC_AUTH_TOKEN={auth_token}",
        f"OLLAMA_BASE_URL={provider_urls['ollama']}",
        f"LM_STUDIO_BASE_URL={provider_urls['lmstudio']}",
        f"LLAMACPP_BASE_URL={provider_urls['llamacpp']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@contextmanager
def _temporary_process_env(values: Mapping[str, str]) -> Iterator[None]:
    previous = dict(os.environ)
    try:
        os.environ.clear()
        os.environ.update(values)
        yield
    finally:
        os.environ.clear()
        os.environ.update(previous)


def _stop_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Certify an isolated strict-loopback FCC local-model lane."
    )
    parser.add_argument("--workdir", default=str(REPO_ROOT), help="Read-only task workspace.")
    parser.add_argument(
        "--evidence-dir",
        default=str(REPO_ROOT / ".p2p" / "evidence" / "fcc-local"),
    )
    parser.add_argument("--report", default="", help="Optional JSON report path.")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-turns", type=int, default=8)
    parser.add_argument("--probe-timeout", type=float, default=2.0)
    parser.add_argument("--server-start-timeout", type=float, default=20.0)
    parser.add_argument("--model", default="", help="Optional exact local FCC model ref.")
    parser.add_argument("--ollama-url", default=os.environ.get("OLLAMA_BASE_URL", LOCAL_PROVIDER_DEFAULTS["ollama"]))
    parser.add_argument("--lmstudio-url", default=os.environ.get("LM_STUDIO_BASE_URL", LOCAL_PROVIDER_DEFAULTS["lmstudio"]))
    parser.add_argument("--llamacpp-url", default=os.environ.get("LLAMACPP_BASE_URL", LOCAL_PROVIDER_DEFAULTS["llamacpp"]))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = Path(args.report) if args.report else None
    evidence_dir_path = Path(args.evidence_dir).resolve()
    evidence_dir_path.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "schema": "p2p-fcc-local-certification/2",
        "status": "STARTED",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mutation_surface": "NONE_PLANNING_MODE",
        "network_policy": "ISOLATED_FCC_LOOPBACK_LOCAL_PROVIDERS_ONLY",
    }

    fcc_server = shutil.which("fcc-server")
    fcc_claude = shutil.which("fcc-claude")
    if not fcc_server or not fcc_claude:
        report.update(
            status="BLOCKED_FCC_BINARIES_MISSING",
            fcc_server=bool(fcc_server),
            fcc_claude=bool(fcc_claude),
        )
        _write_report(report_path, report)
        _emit(report)
        return 2

    provider_urls = {
        "ollama": str(args.ollama_url).strip(),
        "lmstudio": str(args.lmstudio_url).strip(),
        "llamacpp": str(args.llamacpp_url).strip(),
    }
    candidates, observations = discover_local_models(
        provider_urls=provider_urls, timeout=args.probe_timeout
    )
    report["provider_observations"] = observations

    if args.model:
        selected = next((item for item in candidates if item.model_ref == args.model), None)
        if selected is None:
            report.update(
                status="BLOCKED_REQUESTED_LOCAL_MODEL_NOT_DISCOVERED",
                requested_model=args.model,
            )
            _write_report(report_path, report)
            _emit(report)
            return 2
    else:
        selected = select_best_local_model(candidates)

    if selected is None:
        report.update(status="BLOCKED_NO_LOCAL_MODEL")
        _write_report(report_path, report)
        _emit(report)
        return 2

    report["selected_model"] = selected.model_ref
    report["selected_provider"] = selected.provider

    port = _reserve_loopback_port()
    auth_token = "p2p-" + secrets.token_urlsafe(24)
    server_log = evidence_dir_path / f"fcc-isolated-server-{int(time.time())}.log"
    process: subprocess.Popen[Any] | None = None

    try:
        with tempfile.TemporaryDirectory(prefix="p2p-fcc-local-") as temp_dir:
            config_path = Path(temp_dir) / ".env"
            _write_isolated_env(
                config_path,
                port=port,
                auth_token=auth_token,
                selected_model=selected.model_ref,
                provider_urls=provider_urls,
            )
            child_env = _safe_child_env(
                config_path=config_path,
                port=port,
                auth_token=auth_token,
                selected_model=selected.model_ref,
                provider_urls=provider_urls,
            )

            with server_log.open("w", encoding="utf-8") as log_handle:
                process = subprocess.Popen(
                    [fcc_server],
                    env=child_env,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

            report["isolated_fcc"] = {
                "port": port,
                "pid": process.pid,
                "server_log": str(server_log),
                "config_scope": "TEMPORARY_ISOLATED",
            }

            if not _health_ready(port, timeout_seconds=args.server_start_timeout):
                report.update(
                    status="BLOCKED_ISOLATED_FCC_SERVER_START_FAILED",
                    server_exit_code=process.poll(),
                )
                _write_report(report_path, report)
                _emit(report)
                return 2

            # Ask the running isolated server for EFFECTIVE config. This binds
            # the proof to runtime state rather than trusting our temp file.
            with _temporary_process_env(child_env):
                admin = fetch_running_fcc_admin_config(
                    port=port, timeout=args.probe_timeout
                )
            effective_urls = provider_urls_from_admin(admin)
            gate = assess_local_only_runtime(
                selected_model_ref=selected.model_ref,
                admin_payload=admin,
            )
            report["local_only_gate"] = gate.to_dict()
            report["effective_provider_urls"] = effective_urls
            if not gate.safe:
                report.update(status=f"BLOCKED_{gate.status}")
                _write_report(report_path, report)
                _emit(report)
                return 2

            adapter = FccClaudeAdapter()
            with _temporary_process_env(child_env):
                health = adapter.health()
            report["adapter_health"] = {
                "healthy": health.healthy,
                "availability": health.availability,
                "auth_state": health.auth_state,
            }
            if health.healthy is not True:
                report.update(status="BLOCKED_FCC_CLAUDE_NOT_READY")
                _write_report(report_path, report)
                _emit(report)
                return 2

            workdir = str(Path(args.workdir).resolve())
            prompt = (
                "READ-ONLY CERTIFICATION. Do not edit, create, delete, rename, "
                "execute, or commit files. Inspect README.md in the current workspace. "
                "If it is readable, return the exact marker "
                f"{MARKER} followed by one short sentence describing what repository "
                "this is. If README.md is unavailable, state that and do nothing else."
            )
            request_fingerprint = _fingerprint(
                json.dumps(
                    {
                        "model": selected.model_ref,
                        "workdir": workdir,
                        "prompt": prompt,
                        "permission_mode": "plan",
                        "network_policy": report["network_policy"],
                    },
                    sort_keys=True,
                )
            )

            with _temporary_process_env(child_env):
                result = adapter.execute(
                    request_id=f"fcc-local-{int(time.time())}",
                    request_fingerprint=request_fingerprint,
                    task_id="P2P_FCC_LOCAL_LIVE_CERT_01",
                    goal_id="P2P_FCC_LOCAL_BUS",
                    prompt=prompt,
                    max_turns=args.max_turns,
                    timeout_seconds=args.timeout,
                    workdir=workdir,
                    provider=selected.provider,
                    model=selected.model_ref,
                    evidence_dir=str(evidence_dir_path),
                )

            report["execution"] = {
                "status": result.execution_status,
                "verification_status": result.verification_status,
                "error_class": result.error_class,
                "exit_status": result.exit_status,
                "evidence": list(result.artifact_pointers),
                "usage_evidence": dict(result.usage_evidence),
                "possible_mutation": result.possible_mutation,
            }

            marker_seen = False
            for pointer in result.artifact_pointers:
                try:
                    evidence = json.loads(Path(pointer).read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                marker_seen = MARKER in str(evidence.get("stdout", ""))

            report["marker_seen"] = marker_seen
            report["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            if (
                result.execution_status == "SUCCEEDED"
                and marker_seen
                and not result.possible_mutation
            ):
                report["status"] = "PASS_LOCAL_ONLY_READ_ANALYZE"
                _write_report(report_path, report)
                _emit(report)
                return 0

            report["status"] = "BLOCKED_LIVE_TASK_NOT_VERIFIED"
            _write_report(report_path, report)
            _emit(report)
            return 2
    except Exception as exc:
        report.update(
            status="BLOCKED_LOCAL_CERTIFIER_ERROR",
            detail=f"{type(exc).__name__}: {exc}",
        )
        _write_report(report_path, report)
        _emit(report)
        return 2
    finally:
        if process is not None:
            _stop_process(process)


if __name__ == "__main__":
    raise SystemExit(main())
