#!/usr/bin/env python3
"""P2P-FRAMEWORK-06 candidate mint (8.4.7-C-codex.34).
Deterministic normalized zip of the FW06 OPERATIONAL RESILIENCE & BOUNDED
PRODUCTION AUTONOMY surface, consistent with the .30-.33 candidate packaging
convention (fixed mtime 2010-01-01, sorted member order, DEFLATED(9)).
This script MINTS the candidate record only — it never promotes or releases
anything.
"""
from __future__ import annotations
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMBERS = [
    ".p2p/system/p2p_capabilities/fw06_operational_resilience.py",
    ".p2p/system/p2p_capabilities/tests/test_fw06_operational_resilience.py",
    ".p2p/system/p2p_capabilities/p2p_fw01_loop.py",
    "scripts/fw06_supervisor.py",
]
ZIP_NAME = "reports/candidates/fw06-operational-resilience-candidate.zip"
VERSION = "8.4.7-C-codex.34"
LABEL = "fw06-operational-resilience"
BASELINE_VERSION = "8.4.7-C-codex.19"
BASELINE_SHA256 = "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8"
LINEAGE_ANCHOR_VERSION = "8.4.7-C-codex.33"
LINEAGE_ANCHOR_SHA256 = "a4c3161b711a1c9dae6870401f8135e0e77b445c7703ac7fa0ed9c983a06bbb9"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    zip_path = ROOT / ZIP_NAME
    missing = [m for m in MEMBERS if not (ROOT / m).is_file()]
    if missing:
        raise SystemExit(f"Missing members: {missing}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for member in sorted(MEMBERS):
            path = ROOT / member
            info = zipfile.ZipInfo(member, date_time=(2010, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())
    candidate_sha256 = sha256_of(zip_path)
    print(f"CANDIDATE_ZIP: {zip_path.relative_to(ROOT)}")
    print(f"CANDIDATE_SHA256: {candidate_sha256}")
    control = ROOT / "governance" / "development-control.json"
    spec = json.loads(control.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    spec["candidate_records"].append({
        "candidate_version": VERSION,
        "candidate_label": LABEL,
        "candidate_sha256": candidate_sha256,
        "candidate_artifact": str(zip_path.relative_to(ROOT)),
        "candidate_built_at_utc": now,
        "embedded_version": VERSION,
        "based_on_official_version": BASELINE_VERSION,
        "based_on_official_sha256": BASELINE_SHA256,
        "development_goal": "FW06_PRODUCTION_AUTONOMY_RESILIENCE",
        "promotion_status": "UNPROMOTED",
        "built": True,
        "lineage_anchor_sha256": LINEAGE_ANCHOR_SHA256,
        "lineage_anchor_note": (
            "FW06 production autonomy & resilience candidate (lineage anchor "
            ".33 FW05 owner experience). FW06 is NOT a new orchestrator: a "
            "bounded runtime-contract layer over the existing P2P control "
            "plane; FW01 remains the sole operating loop. New surface: "
            "p2p_capabilities/fw06_operational_resilience.py implementing "
            "the Autonomy Envelope (authorized scope / mutation classes / "
            "owner gates / max parallelism / retry policy / resource budget "
            "/ quality requirements / recovery policy / expiry; fresh-only "
            "envelope required), the Safe Continuation Policy (per-gate "
            "fail-closed continuation decision), failure classification "
            "(UNKNOWN_MUTATION_STATE fail-closed for unrecognized states), "
            "bounded retry, execution leases (append-only, split-brain "
            "blocked; reclaim fail-closed while owner process observable "
            "via heartbeat TTL), crash/session-death recovery with "
            "evidence-point failure analysis (A-G failure points; "
            "RETRY_BOUNDED/VERIFY_ONLY/BLOCK/PAUSE only; never blind "
            "re-execution), quiesce/drain lifecycle, FAILOVER != RETRY "
            "deterministic failover decision, tiered runtime health, "
            "pause/resume (durable), workspace ownership + parallel-worktree "
            "conflict detection (deterministic), cleanup fail-closed until "
            "all guards satisfied, multi-project isolation + read-only "
            "multi-project view, append-only idempotent event log (no "
            "secrets, no chain-of-thought), and auditability. Read-only "
            "facade invariant: all view surfaces never create project state "
            "directories (mkdirs=False default). FW01 loop receives an "
            "info-only enrichment hook (fw06_resilience field on step() "
            "outcomes) that never affects control flow. Evidence over "
            "claims: test_fw06_operational_resilience.py 37 cases PASS "
            "(chaos matrix A-G cold-process recovery via real subprocess, "
            "two-process lease split-brain, lease reclaim, pause/resume "
            "durability, fail-closed classifications, deterministic "
            "failover, tiered health, worktree parallel proof, conflict "
            "detection, cleanup guards, GT/GP READ-ONLY shadow eval "
            "byte-identical before/after) + full regression 240/240 PASS "
            "(NEW_UNEXPLAINED_FAILURES=0) + independent supervisor 16/16 "
            "PASS over real code/data paths (incl. read-only facade proof "
            "over GT/GP and diff-based zero-mutation probe). No promotion, "
            "no release, FW07 not started (owner gate)."),
        "surface_scope": [
            "fw06_operational_resilience.py: autonomy envelope, safe "
            "continuation policy, failure classification, bounded retry, "
            "execution leases, crash/session-death recovery, quiesce/drain, "
            "failover decision, runtime health, pause/resume, workspace "
            "ownership/conflict/cleanup, multi-project isolation/view, "
            "event log, audit (all views read-only: never create state "
            "dirs)",
            "test_fw06_operational_resilience.py: 37 cases — A-Z chaos "
            "matrix, cold-process subprocess proofs, two-process lease "
            "boundary, fail-closed negatives, GT/GP read-only shadow",
            "p2p_fw01_loop.py: info-only fw06_resilience enrichment field "
            "appended to step() outcomes; no control-flow change",
            "scripts/fw06_supervisor.py: independent 16-check red-team "
            "supervisor over real code/data paths",
            "governance/development-control.json: candidate lineage record "
            "(this record)",
        ],
    })
    control.write_text(json.dumps(spec, ensure_ascii=False, indent=2)
                       + "\n", encoding="utf-8")
    print(f"GOVERNANCE: candidate record {VERSION} appended (UNPROMOTED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
