#!/usr/bin/env python3
"""Replace the .35 candidate governance record with a schema-complete one
(additive field set matching .33/.34 records — other records untouched)."""
import json
import sys
from pathlib import Path

REPO = Path("/home/ubuntu/fw01_work/auth-f01")
CTRL = REPO / "governance" / "development-control.json"

ARTIFACT = (REPO / "reports" / "candidates"
            / "P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip")
ARTIFACT_SHA256 = "8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47"
ANCHOR_SHA256 = "607e722d22db519aeee9f803814432fcd13e73157db7e6d6d4e5afcbebeca7fa"

BASELINE_VERSION = "8.4.7-C-codex.19"
BASELINE_SHA256 = "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8"


def main() -> int:
    assert ARTIFACT.is_file(), ARTIFACT
    actual_sha = sha256(ARTIFACT)
    assert actual_sha == ARTIFACT_SHA256, f"artifact SHA mismatch {actual_sha}"

    ctrl = json.loads(CTRL.read_text(encoding="utf-8"))
    records = ctrl["candidate_records"]
    assert isinstance(records, list)
    versions = [r.get("candidate_version") for r in records if isinstance(r, dict)]
    assert versions[-1] == "8.4.7-C-codex.35", f"expected .35 tail, got {versions[-3:]}"

    record = {
        "candidate_version": "8.4.7-C-codex.35",
        "candidate_label": "fw00-fw06-cumulative-production-package",
        "candidate_sha256": ARTIFACT_SHA256,
        "candidate_artifact": str(ARTIFACT.relative_to(REPO)),
        "candidate_built_at_utc": "2026-08-20T06:21:00Z",
        "embedded_version": "8.4.7-C-codex.35",
        "based_on_official_version": BASELINE_VERSION,
        "based_on_official_sha256": BASELINE_SHA256,
        "development_goal": "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE",
        "promotion_status": "UNPROMOTED",
        "built": True,
        "lineage_anchor_sha256": ANCHOR_SHA256,
        "lineage_anchor_note": (
            "Cumulative self-contained FW00-FW06 production package (lineage anchor .34 "
            "FW06 operational resilience). NOT a new orchestrator: a packaging milestone "
            "containing the canonical FW01-era release machinery (v24 artifact: "
            "install.sh/install.ps1/doctor.ps1/runtime/foundation/source/docs/governance/.agents) "
            "PLUS the full tracked .p2p/system capability tree (FW02-FW06 modules, tests, "
            "decision trace, owner inbox, resilience surfaces). Installable and self-contained; "
            "evidence: package_release.py canonical build gates PASS (doctor --package, drift, "
            "verify twice), Stage-B verification PASS (manifest/checksum cross-check), "
            "governance sanity PASS. No promotion, no release, pilot not executed (owner gate)."),
        "surface_scope": [
            "release-manifest.json: cumulative_scope + cumulative_system_file_count + system/ bundle entries",
            "RELEASE-SHA256SUMS.txt: full checksum set incl. system/ bundle",
            "system/: full tracked .p2p/system capability tree (FW02-FW06 modules, tests, traces)",
            "governance/development-control.json: candidate lineage record (this record)",
        ],
        "candidate_id": "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE",
    }

    # Replace the minimal record added earlier (appenditive fix of the same .35 slot)
    records[-1] = record
    ctrl["candidate_records"] = records
    CTRL.write_text(json.dumps(ctrl, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

    ids = [r.get("candidate_id") for r in records
           if isinstance(r, dict) and r.get("candidate_id")]
    assert len(ids) == len(set(ids)), "duplicate candidate_id"
    loaded = json.loads(CTRL.read_text(encoding="utf-8"))
    last = loaded["candidate_records"][-1]
    assert last["candidate_version"] == "8.4.7-C-codex.35"
    assert last["candidate_id"] == "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE"
    assert last["promotion_status"] == "UNPROMOTED"
    assert last["lineage_anchor_sha256"] == ANCHOR_SHA256
    print("GOVERNANCE .35 RECORD COMPLETE:", last["candidate_id"], last["candidate_sha256"])
    return 0


def sha256(path: Path) -> str:
    import hashlib
    d = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            d.update(block)
    return d.hexdigest()


if __name__ == "__main__":
    sys.exit(main())
