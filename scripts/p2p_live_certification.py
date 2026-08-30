#!/usr/bin/env python3
"""P2P live host execution certification machinery (C27).

Foreground-only, non-interactive certification of ONE bounded, deterministic,
non-destructive task against ONE real AI host through the P2P permission,
binding, evidence and verification boundaries. Reuses the C22 transport
(receipt binding), C23 continuation (continuation import) and C24 adapter
(host profile / conformance) contract vocabulary without introducing a host
router, model router, second executor, or background autonomy.

Exit codes: 0 success, 1 live failure (evidence recorded), 2 usage error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

_SYSTEM_ROOT = Path(__file__).resolve().parent.parent / ".p2p" / "system"
if str(_SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(_SYSTEM_ROOT))
from p2p_capabilities import fw06_operational_resilience as _fw06  # noqa: E402

SCHEMA_VERSION = "1"
CERTIFICATION_FRESHNESS_DAYS = 90
DEFAULT_TIMEOUT_S = 120
PROBE_MARK_PREFIX = "P2P-C27-PROBE-"

MUTATION_STATES = ("KNOWN_NONE", "KNOWN_OCCURRED", "UNKNOWN")
TIMEOUT_CLASSIFICATIONS = (
    "BEFORE_EXECUTION",
    "AFTER_EXECUTION_STARTED",
    "REMOTE_IN_FLIGHT",
    "CONTROL_PLANE_TIMEOUT",
    "PARTIAL_MUTATION_UNKNOWN",
)
CERT_STATUSES = ("UNCERTIFIED", "CERTIFIED", "STALE", "REVOKED")


class CertificationError(RuntimeError):
    pass


@dataclass
class LiveCertificationRecord:
    """Durable certification record scoped to version/environment/transport."""

    record_id: str
    schema_version: str = SCHEMA_VERSION
    capability_id: str = "HOST_LIVE_EXECUTION_CERTIFICATION"
    host_profile_id: str = ""
    adapter_id: str = ""
    transport: str = ""
    host_version: str = ""
    environment: dict = field(default_factory=dict)
    observed_at: str = ""
    goal_id: str = "C27"
    task_id: str = ""
    project_id: str = ""
    candidate_ref: str = ""
    environment_hash: str = ""
    request: dict = field(default_factory=dict)
    external_execution_id: str = ""
    result: dict = field(default_factory=dict)
    verification: dict = field(default_factory=dict)
    reconciliation: dict = field(default_factory=dict)
    scope: list = field(default_factory=list)
    certification_status: str = "UNCERTIFIED"
    valid_until: str = ""
    freshness_policy: str = f"C24_FRESHNESS:{CERTIFICATION_FRESHNESS_DAYS}D"
    raw_evidence_refs: list = field(default_factory=list)
    timeout_classification: str = ""
    mutation_state: str = ""
    cancellation_state: str = ""

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "record_id", "schema_version", "capability_id", "host_profile_id",
            "adapter_id", "transport", "host_version", "environment",
            "observed_at", "goal_id", "task_id", "project_id",
            "candidate_ref", "environment_hash", "request",
            "external_execution_id", "result", "verification",
            "reconciliation", "scope", "certification_status", "valid_until",
            "freshness_policy", "raw_evidence_refs", "timeout_classification",
            "mutation_state", "cancellation_state",
        )}

    @classmethod
    def from_dict(cls, data: dict) -> "LiveCertificationRecord":
        return cls(**{k: data.get(k, getattr(cls, k).default if hasattr(getattr(cls, k), "default") else "")
                      for k in (
                          "record_id", "schema_version", "capability_id", "host_profile_id",
                          "adapter_id", "transport", "host_version", "environment",
                          "observed_at", "goal_id", "task_id", "project_id",
                          "candidate_ref", "environment_hash", "request",
                          "external_execution_id", "result", "verification",
                          "reconciliation", "scope", "certification_status",
                          "valid_until", "freshness_policy", "raw_evidence_refs",
                          "timeout_classification", "mutation_state",
                          "cancellation_state")})


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _env_hash() -> str:
    return _sha256_bytes(
        "|".join((
            platform.platform(),
            platform.machine(),
            str(platform.python_version()),
            platform.node(),
        )).encode("utf-8")
    )


def _tree_snapshot(root: Path) -> dict[str, str]:
    """Hash every regular file under root (relative paths)."""
    out: dict[str, str] = {}
    if not root.is_dir():
        return out
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = _sha256_file(path)
    return out


def _tree_diff(before: dict, after: dict) -> dict:
    paths = set(before) | set(after)
    diff = {"added": [], "modified": [], "deleted": []}
    for p in sorted(paths):
        if p not in before:
            diff["added"].append(p)
        elif p not in after:
            diff["deleted"].append(p)
        elif before[p] != after[p]:
            diff["modified"].append(p)
    return diff


def _codex_available() -> bool:
    return shutil.which("codex") is not None


def _codex_version() -> str:
    try:
        result = subprocess.run(
            ["codex", "--version"], capture_output=True, text=True, timeout=30,
        )
        return (result.stdout or result.stderr).strip().splitlines()[-1].strip()
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return ""


def _run_probe(
    prompt: str,
    workspace: Path,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    model: str = "gpt-5-nano",
) -> dict:
    """Run the bounded codex CLI probe foreground-only. Returns evidence dict.

    Evidence shape reuses C22 transport vocabulary:
    source / evidence_ref / origin / observed_at / freshness / scope /
    source_binding / fingerprint.
    """
    if not _codex_available():
        raise CertificationError("codex CLI not available")
    workspace.mkdir(parents=True, exist_ok=True)
    fingerprint = _sha256_bytes(prompt.encode("utf-8"))[:16]
    started_at = _utcnow()
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": os.path.expanduser("~"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "OPENAI_BASE_URL": os.environ.get("OPENAI_BASE_URL", ""),
        "OPENAI_API_BASE": os.environ.get("OPENAI_API_BASE", ""),
    }
    before = _tree_snapshot(workspace)
    pid = ""
    return_code = None
    stdout = stderr = ""
    classification = ""
    try:
        proc = subprocess.Popen(
            [
                "codex", "exec", "--skip-git-repo-check",
                "-m", model,
                "-c", "approval_policy=never",
                "-s", "danger-full-access",
                prompt,
            ],
            cwd=str(workspace),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
        )
        pid = str(proc.pid)
        try:
            stdout_b, stderr_b = proc.communicate(timeout=timeout_s)
            stdout, stderr = stdout_b.decode("utf-8", "replace"), stderr_b.decode("utf-8", "replace")
            return_code = proc.returncode
            classification = "BEFORE_EXECUTION" if proc.returncode == -9 and not _any_output(stdout_b, stderr_b) else ""
        except subprocess.TimeoutExpired:
            proc.kill()
            classification = classify_timeout(proc, before, workspace)
            stdout_b, stderr_b = proc.communicate(timeout=10)
            stdout, stderr = stdout_b.decode("utf-8", "replace"), stderr_b.decode("utf-8", "replace")
            return_code = proc.returncode
    except FileNotFoundError as exc:
        raise CertificationError(f"codex executable missing: {exc}") from exc

    after = _tree_snapshot(workspace)
    diff = _tree_diff(before, after)
    mutation = (
        "KNOWN_NONE"
        if not (diff["added"] or diff["modified"] or diff["deleted"])
        else ("KNOWN_OCCURRED" if not classification else "UNKNOWN")
    )
    if classification == "PARTIAL_MUTATION_UNKNOWN":
        mutation = "UNKNOWN"
    return {
        "source": "codex CLI (local host process)",
        "evidence_ref": f"E27-PROBE-{fingerprint}",
        "origin": "RUNTIME_EVIDENCE",
        "observed_at": started_at,
        "freshness": "CURRENT",
        "scope": [str(workspace)],
        "source_binding": "foreground-cli-process-pid",
        "fingerprint": fingerprint,
        "external_execution_id": pid,
        "return_code": return_code,
        "stdout": stdout,
        "stderr": stderr,
        "tree_diff": diff,
        "mutation_state": mutation,
        "timeout_classification": classification,
    }


def _any_output(stdout_b: bytes, stderr_b: bytes) -> bool:
    return bool(stdout_b and stdout_b.strip()) or bool(stderr_b and stderr_b.strip())


def classify_timeout(proc: subprocess.Popen, before: dict, workspace: Path) -> str:
    """Classify a live timeout per C27 mutation-certainty rules."""
    try:
        after = _tree_snapshot(workspace)
    except OSError:
        return "PARTIAL_MUTATION_UNKNOWN"
    diff = _tree_diff(before, after)
    if not _any_output(*(b"" , b"")) and not (diff["added"] or diff["modified"] or diff["deleted"]):
        return "BEFORE_EXECUTION"
    if diff["added"] or diff["modified"] or diff["deleted"]:
        return "PARTIAL_MUTATION_UNKNOWN"
    return "CONTROL_PLANE_TIMEOUT"


def is_fresh(record: LiveCertificationRecord) -> bool:
    """Freshness/revalidation semantics: a certification is fresh only while
    valid_until has not elapsed. Stale certifications are never active."""
    if not record.valid_until:
        return False
    until = _dt.datetime.strptime(record.valid_until, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)
    return _dt.datetime.now(_dt.timezone.utc) < until


def verify_result(workspace: Path, fingerprint: str) -> dict:
    """Independent (host-free) deterministic verification of the probe result."""
    expected_marker = PROBE_MARK_PREFIX + fingerprint
    target = workspace / "p2p_result.txt"
    if not target.exists():
        return {
            "status": "FAIL",
            "method": "independent-deterministic-content-match",
            "detail": f"fixture file missing: {target}",
            "verifier_ref": "P2P verification (local, host-independent)",
            "expected_marker": expected_marker,
            "actual": None,
            "actual_sha256": None,
        }
    content = target.read_text(encoding="utf-8")
    actual_sha256 = _sha256_bytes(content.encode("utf-8"))
    ok = content == expected_marker
    return {
        "status": "PASS" if ok else "FAIL",
        "method": "independent-deterministic-content-match",
        "detail": "expected marker matched exactly" if ok else "content mismatch with expected marker",
        "verifier_ref": "P2P verification (local, host-independent)",
        "expected_marker": expected_marker,
        "actual": content,
        "actual_sha256": actual_sha256,
    }


def reconcile(
    workspace: Path,
    archive_dir: Path,
    record: LiveCertificationRecord,
    verification: dict,
    *,
    registry_root: Path | None = None,
) -> dict:
    """Archive evidence, then delegate disposal to the FW06 TMPGC path.

    A C27 record without a durable FW06 workspace identity is deliberately
    retained.  This seam never performs an unregistered physical deletion.
    """
    workspace_input = Path(workspace).expanduser()
    if not workspace_input.is_absolute():
        workspace_input = Path.cwd() / workspace_input
    workspace = workspace_input.resolve(strict=False)
    archive_dir = Path(archive_dir).expanduser().resolve(strict=False)
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = record.observed_at.replace(":", "-").replace("T", "_")
    host_dir = archive_dir / f"live-probe-{stamp[:16]}-{record.record_id[:8]}"
    host_dir.mkdir(parents=True, exist_ok=True)
    (host_dir / "record.json").write_text(
        json.dumps(record.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if record.raw_evidence_refs:
        shutil.copy2(Path(record.raw_evidence_refs[0].replace("raw:", "")), host_dir / "stdout-stderr.log", ) if False else None
    evidence = host_dir / "raw-evidence.json"
    evidence.write_text(json.dumps({
        "verification": verification,
        "observed_at": record.observed_at,
    }, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    archive_ref = f"raw:{host_dir}"
    if registry_root is None:
        return {
            "status": "COMPLETED_KEEP",
            "archive_ref": archive_ref,
            "workspace_removed": False,
            "disposal": "KEEP",
            "reason": "WORKSPACE_REGISTRY_ROOT_REQUIRED",
        }
    try:
        root = Path(registry_root).expanduser().resolve()
        policy = _fw06.load_tmp_gc_policy(root)
        rows = _fw06.list_all_workspaces(root)
        workspace_key = _fw06._path_key(workspace_input)
        match = next(
            (row for row in rows
             if _fw06._path_key(_fw06._rooted_path(
                 root, str(row.get("root_path", ""))
             )) == workspace_key),
            None,
        )
        if match is None:
            return {
                "status": "COMPLETED_KEEP",
                "archive_ref": archive_ref,
                "workspace_removed": False,
                "disposal": "KEEP",
                "reason": "WORKSPACE_REGISTRATION_NOT_FOUND",
            }
        workspace_id = str(match.get("workspace_id", ""))
        if not _fw06._workspace_registry_is_well_formed(root):
            return {
                "status": "COMPLETED_KEEP",
                "archive_ref": archive_ref,
                "workspace_id": workspace_id,
                "workspace_removed": False,
                "disposal": "KEEP",
                "reason": "WORKSPACE_REGISTRY_MALFORMED",
            }
        path_identity = _fw06._tmp_path_identity(
            root,
            workspace_input,
            policy,
            registered_non_temp=_fw06._registered_non_temp_worktrees(
                root, policy,
            ),
        )
        if not path_identity.get("ok"):
            return {
                "status": "COMPLETED_KEEP",
                "archive_ref": archive_ref,
                "workspace_id": workspace_id,
                "workspace_removed": False,
                "disposal": "KEEP",
                "reason": "WORKSPACE_PATH_NOT_SAFE:" + str(
                    path_identity.get("reason", "UNKNOWN")
                ),
            }
        existing_reasons = [
            reason for reason in match.get("protection_reasons", [])
            if str(reason).upper() != "ACTIVE_SESSION"
        ] if isinstance(match.get("protection_reasons"), list) else []
        completed = _fw06.mark_workspace_complete(
            root,
            workspace_id,
            policy=policy,
            protection_reasons=existing_reasons,
            evidence_status="DURABLE",
            evidence_pointers=[str(host_dir / "record.json"),
                               str(evidence)],
            reconciliation_ref=archive_ref,
        )
        gc = _fw06.apply_tmp_gc(
            root,
            {"workspaces": [{"workspace_id": workspace_id}]},
            policy=policy,
        )
        outcome = next(
            (item for item in gc.get("applied", [])
             if item.get("workspace_id") == workspace_id),
            None,
        )
        return {
            "status": "COMPLETED",
            "archive_ref": archive_ref,
            "workspace_id": workspace_id,
            "workspace_removed": bool(outcome and outcome.get("status") == "DELETED"),
            "disposal": "DELETED" if outcome and outcome.get("status") == "DELETED" else "KEEP",
            "gc": gc,
            "registry_lifecycle": completed.get("lifecycle_state"),
        }
    except (OSError, ValueError, _fw06.TmpGcError) as exc:
        return {
            "status": "COMPLETED_KEEP",
            "archive_ref": archive_ref,
            "workspace_removed": False,
            "disposal": "KEEP",
            "reason": "GC_CLASSIFICATION_UNAVAILABLE:" + str(exc),
        }


def build_record(
    prompt: str,
    workspace: Path,
    evidence: dict,
    verification: dict,
    project_id: str,
    candidate_ref: str = "",
) -> LiveCertificationRecord:
    now = _utcnow()
    valid_until = (
        _dt.datetime.strptime(now, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=_dt.timezone.utc) + _dt.timedelta(days=CERTIFICATION_FRESHNESS_DAYS)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    certified = verification["status"] == "PASS"
    return LiveCertificationRecord(
        record_id=f"C27-LIVE-{uuid.uuid4().hex[:12]}",
        capability_id="HOST_LIVE_EXECUTION_CERTIFICATION",
        host_profile_id="CODEX_CLI_0_147_0_LINUX",
        adapter_id="C24_LOCAL_CLI_ADAPTER_FAMILY",
        transport="LOCAL_CLI",
        host_version=_codex_version(),
        environment={
            "os": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "hostname": platform.node(),
        },
        observed_at=now,
        goal_id="C27",
        task_id="LIVE_PROBE_001",
        project_id=project_id,
        candidate_ref=candidate_ref,
        environment_hash=_env_hash(),
        request={
            "prompt": prompt,
            "prompt_fingerprint_sha256": _sha256_bytes(prompt.encode("utf-8")),
        },
        external_execution_id=evidence.get("external_execution_id", ""),
        result={
            "accepted": certified,
            "content_ref": f"file:{workspace / 'p2p_result.txt'}",
            "content_sha256": verification.get("actual_sha256"),
            "mutation_state": evidence.get("mutation_state", "UNKNOWN"),
        },
        verification=verification,
        reconciliation={"status": "PENDING"},
        scope=[
            _codex_version(),
            f"{platform.platform()}",
            "LOCAL_CLI",
            str(workspace),
        ],
        certification_status="CERTIFIED" if certified else "UNCERTIFIED",
        valid_until=valid_until,
        raw_evidence_refs=[],
        timeout_classification=evidence.get("timeout_classification", ""),
        mutation_state=evidence.get("mutation_state", "UNKNOWN"),
        cancellation_state="",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="C27 live certification machinery")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Execute the bounded live probe")
    run_p.add_argument("--workspace", required=True)
    run_p.add_argument("--project", required=True)
    run_p.add_argument("--model", default="gpt-5-nano")
    run_p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    run_p.add_argument("--prompt-file", help="path to exact probe prompt text")

    verify_p = sub.add_parser("verify", help="Independently verify a probe result")
    verify_p.add_argument("--workspace", required=True)
    verify_p.add_argument("--fingerprint", required=True)

    rec_p = sub.add_parser("record", help="Build + reconcile the certification record")
    rec_p.add_argument("--workspace", required=True)
    rec_p.add_argument("--project", required=True)
    rec_p.add_argument("--evidence", required=True)
    rec_p.add_argument("--verification", required=True)
    rec_p.add_argument("--archive", required=True)
    rec_p.add_argument("--candidate", default="")
    rec_p.add_argument(
        "--registry-root",
        help="project root containing the durable FW06 workspace registry",
    )

    expiry_p = sub.add_parser("expiry-check", help="Report freshness of a record")
    expiry_p.add_argument("--record", required=True)

    health_p = sub.add_parser("health", help="Zero-credit discovery health summary")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2

    if args.command == "health":
        summary = {
            "codex_available": _codex_available(),
            "codex_version": _codex_version(),
            "openai_key_present": bool(os.environ.get("OPENAI_API_KEY")),
            "openai_base_url_present": bool(os.environ.get("OPENAI_BASE_URL")),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "run":
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
        try:
            evidence = _run_probe(prompt, Path(args.workspace), args.timeout, args.model)
        except CertificationError as exc:
            print(json.dumps({"status": "PROBE_FAILED", "reason": str(exc)},
                             ensure_ascii=False, indent=2), file=sys.stderr)
            return 1
        evidence_path = Path(args.workspace) / ".p2p_c27_evidence.json"
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True),
                                 encoding="utf-8")
        print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "verify":
        verification = verify_result(Path(args.workspace), args.fingerprint)
        print(json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "record":
        evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
        verification = json.loads(Path(args.verification).read_text(encoding="utf-8"))
        prompt = evidence.get("request_prompt", "")
        fingerprint = evidence.get("fingerprint", "")
        record = build_record(
            prompt=prompt if prompt else f"<prompt-fingerprint {fingerprint}>",
            workspace=Path(args.workspace),
            evidence=evidence,
            verification=verification,
            project_id=args.project,
            candidate_ref=args.candidate,
        )
        if verification["status"] == "PASS":
            record.reconciliation = reconcile(
                Path(args.workspace), Path(args.archive), record, verification,
                registry_root=Path(args.registry_root) if args.registry_root else None,
            )
        else:
            record.reconciliation = {"status": "SKIPPED_VERIFICATION_FAILED"}
        record_path = Path(args.archive) / "live-certification-record.json"
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(json.dumps(record.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "expiry-check":
        data = json.loads(Path(args.record).read_text(encoding="utf-8"))
        valid_until = data.get("valid_until", "")
        now = _dt.datetime.now(_dt.timezone.utc)
        if not valid_until:
            print(json.dumps({"status": "NO_VALIDITY", "freshness": "STALE"}))
            return 0
        until = _dt.datetime.strptime(valid_until, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=_dt.timezone.utc)
        status = "CERTIFIED_FRESH" if now <= until else "STALE"
        print(json.dumps({
            "certification_status": data.get("certification_status"),
            "valid_until": valid_until,
            "checked_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "freshness": status,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
