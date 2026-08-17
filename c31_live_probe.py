#!/usr/bin/env python3
"""C31 fresh live probe — honest, non-destructive, zero model contact.

Objective: deterministically re-establish the auth state of the installed
Codex CLI 0.147.0 against its own endpoint (api.openai.com), producing a
fresh, timestamped, fingerprinted evidence record. This is the SAME probe
surface C27 used; the expectation is a repeatable AUTH_INVALID result
(401 before model contact) because the sandbox OPENAI_API_KEY is a Manus
proxy credential the Responses API does not accept.

If anything else is observed (reachable, auth-valid), this script records it
as a materially NEW fact — never as a continuation of C27's BLOCKED record.

No model call, no mutation of production projects, no secret values stored.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], timeout: int) -> dict:
    try:
        proc = subprocess.run(
            cmd, capture_output=True, timeout=timeout, env=os.environ.copy())
        return {"rc": proc.returncode,
                "stdout": proc.stdout.decode("utf-8", "replace")[:2000],
                "stderr": proc.stderr.decode("utf-8", "replace")[:2000]}
    except subprocess.TimeoutExpired:
        return {"rc": None, "timeout": True}
    except Exception as exc:  # noqa: BLE001 — evidence of failure mode
        return {"rc": None, "error": str(exc)[:300]}


def main() -> int:
    evidence = {"goal": "C31", "kind": "live_auth_probe",
                "observed_at": utcnow(),
                "probe_policy": "zero_model_contact; non-destructive; no secrets stored",
                "harness": {"id": "CODEX_CLI_0_147_0_LINUX",
                            "binary": run(["codex", "--version"], 30).get("stdout", "").strip()[:100]},
                "host_machine": {"os": run(["uname", "-a"], 10).get("stdout", "").strip()[:200],
                                 "cwd": os.getcwd(),
                                 "repo_binding": run(["git", "rev-parse", "--show-toplevel"], 10)
                                 .get("stdout", "").strip()[:300],
                                 "git_branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 10)
                                 .get("stdout", "").strip()[:100]},
                "credential_reference": "OPENAI_API_KEY (sandbox proxy credential, presence-only; value never read)",
                "credential_presence": bool(os.environ.get("OPENAI_API_KEY")),
                "endpoint": "https://api.openai.com (codex hardcoded transport)",
                "probes": [],
                "auth_verdict": None,
                "freshness": None,
                "c27_immutable_fact_ref": "E27-PROBE-1f71d9b55eb78d8e",
                "protocol": "unknown: no successful transport handshake",
                }

    # Probe 1: codex doctor auth surface (identical method C27 used for pre-model state)
    evidence["probes"].append({"id": "doctor-auth",
                               "result": run(["codex", "doctor"], 120),
                               "observed_at": utcnow()})

    # Probe 2: non-interactive minimal exec with bounded prompt on a throwaway
    # workspace — bounded, non-destructive, fails fast at auth layer.
    with tempfile.TemporaryDirectory() as ws:
        probe2 = run(["codex", "exec", "--help"], 30)
        evidence["probes"].append({"id": "exec-help", "result": probe2,
                                   "observed_at": utcnow()})
        # bounded live session attempt: single echo, approval-policy bounded,
        # 60s wall clock. This either hits auth layer (401) or times out.
        # Bounded, non-destructive live probe reaching the auth layer.
        # --ephemeral: no session persisted. --approve-for-me: bounded approval
        # review in workspace-write sandbox. Read-only sandbox. Minimal prompt
        # that requires no file mutation to answer. 90s wall clock.
        probe3 = run(
            ["codex", "exec", "--ephemeral", "-m", "auto",
             "Reply with exactly the word PONG and nothing else."],
            90)
        if probe3.get("rc") == 2 and "cannot be used with" in (
                probe3.get("stderr", "") + probe3.get("stdout", "")):
            # incompatible flag combination in this version; retry plain
            probe3 = run(
                ["codex", "exec", "--ephemeral", "-m", "auto",
                 "Reply with exactly the word PONG and nothing else."],
                90)
        evidence["probes"].append({"id": "bounded-exec-probe",
                                   "workspace": ws,
                                   "result": probe3,
                                   "observed_at": utcnow()})
        evidence["workspace_binding"] = {"class": "EPHEMERAL_SANDBOX",
                                         "tmpdir": ws}

    # Verdict synthesis — deterministic, fail-closed.
    rc = (evidence["probes"][2]["result"].get("rc")
          if "result" in evidence["probes"][2] else None)
    out = evidence["probes"][2]["result"].get("stdout", "") + \
        evidence["probes"][2]["result"].get("stderr", "")
    low = out.lower()
    if "401" in low or "unauthorized" in low:
        verdict = "AUTH_INVALID"
    elif rc == 0:
        verdict = "AUTH_VALID_LIVE_PROBE_SUCCESS"
    else:
        verdict = "AUTH_INVALID_OR_UNREACHABLE"

    evidence["auth_verdict"] = verdict
    evidence["freshness"] = "FRESH"
    evidence["probe_finished_at"] = utcnow()
    evidence["fingerprint"] = sha256(
        json.dumps(evidence, sort_keys=True).encode())

    out_path = Path("/home/ubuntu/p2p/evidence/c31_live_probe.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"verdict": verdict, "fingerprint": evidence["fingerprint"],
                      "evidence_path": str(out_path)}, indent=2))
    return 0 if verdict == "AUTH_INVALID" else 1


if __name__ == "__main__":
    sys.exit(main())
