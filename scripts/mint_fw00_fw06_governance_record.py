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
ARTIFACT_SHA256 = "f775ac15bbca691fb734acb8c97aedc7635c48688b2a8c63abb1e83d35cdf8cd"
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
    assert versions[-1] == "8.4.7-C-codex.36", f"expected .36 tail, got {versions[-3:]}"

    record = {
        "candidate_version": "8.4.7-C-codex.36",
        "candidate_label": "fw00-fw06-cumulative-production-package",
        "candidate_sha256": ARTIFACT_SHA256,
        "candidate_artifact": str(ARTIFACT.relative_to(REPO)),
        "candidate_built_at_utc": "2026-08-20T10:00:00Z",
        "embedded_version": "8.4.7-C-codex.36",
        "based_on_official_version": BASELINE_VERSION,
        "based_on_official_sha256": BASELINE_SHA256,
        "development_goal": "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE",
        "promotion_status": "UNPROMOTED",
        "built": True,
        "source_commit": "4063c4ba7acc5098ab544fa2fb0a5c94aa1b4226",
        "source_tree_hash": "d9990c6a6b2778abf9c7d92b1f2db3ae6e60b03c",
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
            "governance sanity PASS. No promotion, no release, pilot not executed (owner gate). "
            "GATE-01B identity repair: .36 is the ONE immutable successor of .35 (identity-collision "
            "fix — same candidate_id FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE now pins one artifact SHA)."),
        "surface_scope": [
            "release-manifest.json: cumulative_scope + cumulative_system_file_count + system/ bundle entries",
            "RELEASE-SHA256SUMS.txt: full checksum set incl. system/ bundle",
            "system/: full tracked .p2p/system capability tree (FW02-FW06 modules, tests, traces)",
            "governance/development-control.json: candidate lineage record (this record)",
        ],
        "candidate_id": "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE",
    }

    # Replace the minimal record added earlier (appenditive fix of the same .36 slot)
    records[-1] = record
    ctrl["candidate_records"] = records
    CTRL.write_text(json.dumps(ctrl, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

    # GATE-01B identity repair: one direct successor pair allowed
    # (.35/.36 share FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE, both UNPROMOTED)
    _ids = [r.get("candidate_id") for r in records
            if isinstance(r, dict) and r.get("candidate_id")]
    from collections import Counter
    for _k, _v in Counter(_ids).items():
        assert _v in (1, 2), f"duplicate candidate_id {_k} x{_v}"
        if _v == 2:
            _idx = [i for i, r in enumerate(records)
                    if isinstance(r, dict) and r.get("candidate_id") == _k]
            assert _idx[1] == _idx[0] + 1
            assert all(records[i]["promotion_status"] == "UNPROMOTED"
                       for i in _idx)
    loaded = json.loads(CTRL.read_text(encoding="utf-8"))
    last = loaded["candidate_records"][-1]
    assert last["candidate_version"] == "8.4.7-C-codex.36"
    assert last["candidate_id"] == "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE"
    assert last["promotion_status"] == "UNPROMOTED"
    assert last["lineage_anchor_sha256"] == ANCHOR_SHA256
    print("GOVERNANCE .36 RECORD COMPLETE:", last["candidate_id"], last["candidate_sha256"])
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
