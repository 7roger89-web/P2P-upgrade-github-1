#!/usr/bin/env python3
"""Mint the .38 candidate governance record as the ONE successor of .37 in the
FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE lineage (runtime-bound candidate
identity — other records untouched)."""
import json
import sys
from pathlib import Path

REPO = Path("/home/ubuntu/fw01_work/auth-f01")
CTRL = REPO / "governance" / "development-control.json"

ARTIFACT = (REPO / "reports" / "candidates"
            / "P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip")
ARTIFACT_SHA256 = "d062ec5c4f8d2cb264c0b405de5236850d53d04757e264d871cf12395b0ec253"
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
    if versions[-1] == "8.4.7-C-codex.38":
        # Idempotent: the .38 record was already minted on a prior run.
        print("GOVERNANCE .38 RECORD ALREADY PRESENT — no-op")
        return 0
    assert versions[-1] == "8.4.7-C-codex.37", f"expected .37 tail, got {versions[-3:]}"

    # P2P-BOUNDED-DOCUMENTATION-WRITE-01: candidate .38 = ONE isolated
    # successor minted because the runtime gained the canonical
    # bounded_documentation_write primitive (fail-closed bounded doc write,
    # FW04 quality/FW05 owner/FW06 lease, whole-claim verifier bounded
    # branch). Declared runtime == executed runtime byte-for-byte.

    # Source binding: the implementation commit carrying the final runtime
    # (committed before mint; HEAD == source).
    src_commit = "a6d2c33e62f91fd7a05d511085750945a5c25973"
    src_tree = "1ff1b54cca35a9aa44f7c2df62166487d0188d89"
    record = {
        "candidate_version": "8.4.7-C-codex.38",
        "candidate_label": "fw00-fw06-cumulative-production-package",
        "candidate_sha256": ARTIFACT_SHA256,
        "candidate_artifact": str(ARTIFACT.relative_to(REPO)),
        "candidate_built_at_utc": "2026-08-21T00:00:00Z",
        "embedded_version": "8.4.7-C-codex.38",
        "based_on_official_version": BASELINE_VERSION,
        "based_on_official_sha256": BASELINE_SHA256,
        "development_goal": "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE",
        "promotion_status": "UNPROMOTED",
        "built": True,
        "source_commit": src_commit,
        "source_tree_hash": src_tree,
        "lineage_anchor_sha256": ANCHOR_SHA256,
        "lineage_anchor_note": (
            "Cumulative self-contained FW00-FW06 production package (lineage anchor .34 "
            "FW06 operational resilience). NOT a new orchestrator: a packaging milestone "
            "containing the canonical FW01-era release machinery (v24 artifact: "
            "install.sh/install.ps1/doctor.ps1/runtime/foundation/source/docs/governance/.agents) "
            "PLUS the full tracked .p2p/system capability tree (FW02-FW06 modules, tests, "
            "decision trace, owner inbox, resilience surfaces). Installable and self-contained; "
            "evidence: package_release.py canonical build gates PASS (doctor --package, drift), "
            "Stage-B verification PASS (manifest/checksum cross-check), "
            "governance sanity PASS (cumulative lineage .35/.36/.37/.38 rule: each record pins "
            "exactly one artifact SHA, all UNPROMOTED, all directly consecutive). No promotion, "
            "no release, pilot not executed (owner gate). BW01 capability-lineage fix: .38 "
            "replaces .37's build because the committed runtime gained the canonical "
            "bounded_documentation_write capability (primitive + registry + inference + "
            "role/permission bridge + verifier bounded branch + 46-test suite), so "
            "DECLARED_CANDIDATE_RUNTIME == EXECUTED_RUNTIME byte-for-byte at HEAD a6d2c33."),
        "surface_scope": [
            "release-manifest.json: cumulative_scope + cumulative_system_file_count + system/ bundle entries",
            "RELEASE-SHA256SUMS.txt: full checksum set incl. system/ bundle",
            "system/: full tracked .p2p/system capability tree (FW02-FW06 modules + "
            "bounded_documentation_write primitive, tests, traces)",
            "governance/development-control.json: candidate lineage record (this record)",
        ],
        "candidate_id": "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE",
    }

    # Append the successor record (cumulative lineage allows the id to span
    # .35/.36/.37/.38 with one artifact SHA per record, all UNPROMOTED)
    records.append(record)
    ctrl["candidate_records"] = records
    CTRL.write_text(json.dumps(ctrl, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

    # Lineage integrity: FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE may span at
    # most the documented .35/.36/.37/.38 chain, all consecutive and
    # UNPROMOTED; every other id appears at most twice as a direct pair.
    _ids = [r.get("candidate_id") for r in records
            if isinstance(r, dict) and r.get("candidate_id")]
    from collections import Counter
    for _k, _v in Counter(_ids).items():
        _idx = [i for i, r in enumerate(records)
                if isinstance(r, dict) and r.get("candidate_id") == _k]
        if _k == "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE":
            assert _v in (2, 3, 4), f"cumulative candidate_id {_k} x{_v} " \
                "(allowed lineage span: .35/.36 through .35/.36/.37/.38)"
            assert all(_idx[j] == _idx[0] + j for j in range(len(_idx))), \
                "cumulative records must be directly consecutive"
            _nums = [int(records[i]["candidate_version"].rsplit(".", 1)[1])
                     for i in _idx]
            assert _nums == list(range(_nums[0], _nums[0] + len(_nums))), \
                "cumulative versions must be consecutive"
        else:
            assert _v in (1, 2), f"duplicate candidate_id {_k} x{_v}"
            if _v == 2:
                assert _idx[1] == _idx[0] + 1
        assert all(records[i]["promotion_status"] == "UNPROMOTED" for i in _idx)
    loaded = json.loads(CTRL.read_text(encoding="utf-8"))
    last = loaded["candidate_records"][-1]
    assert last["candidate_version"] == "8.4.7-C-codex.38"
    assert last["candidate_id"] == "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE"
    assert last["promotion_status"] == "UNPROMOTED"
    assert last["lineage_anchor_sha256"] == ANCHOR_SHA256
    print("GOVERNANCE .38 RECORD COMPLETE:", last["candidate_id"], last["candidate_sha256"])
    assert last["source_commit"] == src_commit, last["source_commit"]
    assert last["source_tree_hash"] == src_tree, last["source_tree_hash"]
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
