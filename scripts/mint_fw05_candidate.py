#!/usr/bin/env python3
"""P2P-FRAMEWORK-05 candidate mint (8.4.7-C-codex.33).
Deterministic normalized zip of the FW05 OWNER EXPERIENCE & DECISION TRACE
surface, consistent with the .30/.31/.32 candidate packaging convention
(fixed mtime 2010-01-01, sorted member order, DEFLATED(9)).
This script MINTS the candidate record candidate only — it never promotes
or releases anything.
"""
from __future__ import annotations
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMBERS = [
    ".p2p/system/p2p_capabilities/fw05_owner_experience.py",
    ".p2p/system/p2p_capabilities/tests/test_fw05_owner_experience.py",
    ".p2p/system/p2p_capabilities/p2p_fw01_loop.py",
    "scripts/fw05_supervisor.py",
]
ZIP_NAME = "reports/candidates/fw05-owner-experience-decision-trace-candidate.zip"
VERSION = "8.4.7-C-codex.33"
LABEL = "fw05-owner-experience-decision-trace"
BASELINE_VERSION = "8.4.7-C-codex.19"
BASELINE_SHA256 = "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8"
LINEAGE_ANCHOR_VERSION = "8.4.7-C-codex.32"
LINEAGE_ANCHOR_SHA256 = "5985e0e5dc5bdae143ebe42746226f7649f93fdaa705c8b0ec5e9b951cc376f6"


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
        "development_goal": "FW05_OWNER_EXPERIENCE_DECISION_TRACE",
        "promotion_status": "UNPROMOTED",
        "built": True,
        "lineage_anchor_sha256": LINEAGE_ANCHOR_SHA256,
        "lineage_anchor_note": (
            "FW05 owner experience + decision trace candidate (lineage "
            "anchor .32 quality-stop hardening). FW05 is NOT a new "
            "orchestrator: a read-only owner-facing facade over canonical "
            "durable state (FW01 remains the sole operating loop). New "
            "surface: p2p_capabilities/fw05_owner_experience.py (~1.5k "
            "lines) implementing the structured decision-trace contract "
            "(DECISION_ID, GOAL_ID, TASK_ID, DECISION_TYPE, TIMESTAMP, "
            "INPUT_FACTS, APPLIED_POLICY_OR_RULE, SELECTED_ACTION, "
            "MATERIAL_ALTERNATIVES, "
            "REJECTED_ALTERNATIVES_WITH_REASON, EVIDENCE_POINTERS, "
            "EVIDENCE_VERSION, UNKNOWN_OR_GAPS, OWNER_DECISION_REQUIRED, "
            "DECISION_STATUS, SCOPE), the durable Owner Decision Inbox "
            "(append-only .p2p/state/owner-inbox.jsonl with deterministic "
            "DECISION_ID hashing for cross-process deduplication; exactly "
            "one unresolved item per blocking cause+scope+evidence "
            "version), the Owner Answer Contract "
            "(parse_owner_response/resolve_owner_answer: validate against "
            "DECISION_ID + evidence version + option; invalid/stale/"
            "already-resolved answers fail closed; raw transcript never "
            "becomes state; ONE_TIME narrow scope, auto_grants_nothing), "
            "progressive disclosure L1/L2/L3 derived from the same "
            "durable truth, project status view with Goal Pass vs "
            "Promotion distinction, and durable QUALITY_REVIEW triage "
            "(technical-resolvable routed without an inbox item; "
            "owner-owned creates exactly one item). FW01 loop receives an "
            "info-only enrichment hook (fw05_owner_experience field on "
            "step() outcomes) that never affects control flow. Evidence "
            "over claims: test_fw05_owner_experience.py 29 cases PASS "
            "(full A-Z matrix incl. dedup K/L, cold-process boundary "
            "recovery M/N via real subprocess restart, owner answer "
            "contract O-S, decision resume U/V with no duplicate "
            "execution, progressive disclosure W, Goal Pass vs Promotion "
            "X, evidence-not-CoT Y, FW01-FW04 regression Z) + full "
            "regression 203/203 PASS (NEW_UNEXPLAINED_FAILURES=0) + "
            "independent supervisor 16/16 PASS over real code/data paths + "
            "shadow evaluation READ-ONLY over the GT/GP cert trees "
            "(byte-identical before/after). DECISION_TRACE stores "
            "structured evidence, never private reasoning; OWNER_MESSAGE "
            "never equals DURABLE_DECISION; OWNER_APPROVAL is narrowly "
            "scoped (single decision, single task, one-time). Minted per "
            "candidate_policy: runtime behavior changed (FW01 step() "
            "output enriched + new durable inbox + new module) -> YES. "
            "No promotion, no release, FW06 not started (owner gate)."),
        "surface_scope": [
            "fw05_owner_experience.py: decision-trace record contract, "
            "owner inbox (append-only JSONL, stable DECISION_ID, dedup), "
            "owner answer contract (fail-closed: invalid/stale/resolved), "
            "progressive disclosure L1/L2/L3, project status snapshot "
            "(blocker, next action, open decisions, goal-pass vs "
            "promotion), quality review integration (owner-owned -> "
            "exactly 1 inbox item; technical -> no item)",
            "test_fw05_owner_experience.py: 29 cases — matrix A-Z, "
            "cold-process boundary recovery (real subprocess), decision "
            "resume, fail-closed answer contract, GT/GP read-only shadow",
            "p2p_fw01_loop.py: info-only fw05_owner_experience enrichment "
            "field appended to step() outcomes at all exit points; no "
            "control-flow change",
            "scripts/fw05_supervisor.py: independent 16-check supervisor "
            "over real code/data paths",
            "governance/development-control.json: candidate lineage "
            "record (this record)",
        ],
    })
    control.write_text(json.dumps(spec, ensure_ascii=False, indent=2)
                       + "\n", encoding="utf-8")
    print(f"GOVERNANCE: candidate record {VERSION} appended (UNPROMOTED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
