#!/usr/bin/env python3
"""Compare a new P2P ZIP with the immutable 8.4.6-C source inventory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> str:
    value = name.replace("\\", "/")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise ValueError(f"unsafe ZIP path: {name!r}")
    return str(pure)


def inventory_zip(path: Path) -> tuple[list[dict], str]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows: list[dict] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = safe_name(info.filename)
            data = archive.read(info)
            rows.append(
                {
                    "path": name,
                    "size": len(data),
                    "crc32": f"{info.CRC:08X}",
                    "sha256": sha256_bytes(data),
                }
            )
    rows.sort(key=lambda item: item["path"])
    return rows, digest


def load_baseline(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value:
        raise ValueError("baseline inventory must be a non-empty JSON array")
    required = {"stable_id", "path", "sha256", "size", "crc32"}
    for index, row in enumerate(value, start=1):
        if not isinstance(row, dict) or not required.issubset(row):
            raise ValueError(f"baseline row {index} is missing required fields")
    return value


def compare(baseline: list[dict], current: list[dict]) -> list[dict]:
    old_by_path = {row["path"]: row for row in baseline}
    new_by_path = {row["path"]: row for row in current}
    old_missing = [row for path, row in old_by_path.items() if path not in new_by_path]
    new_missing = [row for path, row in new_by_path.items() if path not in old_by_path]
    old_hashes: dict[str, list[dict]] = defaultdict(list)
    new_hashes: dict[str, list[dict]] = defaultdict(list)
    for row in old_missing:
        old_hashes[row["sha256"]].append(row)
    for row in new_missing:
        new_hashes[row["sha256"]].append(row)
    renamed_old: set[str] = set()
    renamed_new: set[str] = set()
    rows: list[dict] = []
    for path in sorted(old_by_path.keys() & new_by_path.keys()):
        old = old_by_path[path]
        new = new_by_path[path]
        change = "unchanged" if old["sha256"] == new["sha256"] else "modified"
        rows.append(
            {
                "stable_id": old["stable_id"],
                "change": change,
                "old_path": path,
                "new_path": path,
                "old_sha256": old["sha256"],
                "new_sha256": new["sha256"],
                "old_size": old["size"],
                "new_size": new["size"],
                "review_required": change == "modified",
            }
        )
    for digest in sorted(old_hashes.keys() & new_hashes.keys()):
        olds = old_hashes[digest]
        news = new_hashes[digest]
        for old, new in zip(olds, news):
            renamed_old.add(old["path"])
            renamed_new.add(new["path"])
            rows.append(
                {
                    "stable_id": old["stable_id"],
                    "change": "renamed_or_moved",
                    "old_path": old["path"],
                    "new_path": new["path"],
                    "old_sha256": digest,
                    "new_sha256": digest,
                    "old_size": old["size"],
                    "new_size": new["size"],
                    "review_required": False,
                }
            )
    for old in old_missing:
        if old["path"] in renamed_old:
            continue
        rows.append(
            {
                "stable_id": old["stable_id"],
                "change": "removed",
                "old_path": old["path"],
                "new_path": "",
                "old_sha256": old["sha256"],
                "new_sha256": "",
                "old_size": old["size"],
                "new_size": "",
                "review_required": True,
            }
        )
    next_id = max(int(str(row["stable_id"]).rsplit("-", 1)[-1]) for row in baseline) + 1
    for new in new_missing:
        if new["path"] in renamed_new:
            continue
        rows.append(
            {
                "stable_id": f"P2P-FILE-{next_id:04d}",
                "change": "added",
                "old_path": "",
                "new_path": new["path"],
                "old_sha256": "",
                "new_sha256": new["sha256"],
                "old_size": "",
                "new_size": new["size"],
                "review_required": True,
            }
        )
        next_id += 1
    order = {"modified": 0, "added": 1, "removed": 2, "renamed_or_moved": 3, "unchanged": 4}
    rows.sort(key=lambda row: (order[row["change"]], row["old_path"] or row["new_path"]))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", help="New P2P release ZIP")
    parser.add_argument(
        "--baseline",
        default=str(Path(__file__).resolve().parents[1] / "manifest" / "source-inventory.json"),
        help="Baseline source-inventory.json",
    )
    parser.add_argument("--out", required=True, help="New output directory; must not already contain reports")
    args = parser.parse_args()
    zip_path = Path(args.zip).expanduser().resolve()
    baseline_path = Path(args.baseline).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    if not zip_path.is_file():
        raise SystemExit(f"ZIP not found: {zip_path}")
    if not baseline_path.is_file():
        raise SystemExit(f"Baseline inventory not found: {baseline_path}")
    out.mkdir(parents=True, exist_ok=True)
    targets = [out / "update-summary.json", out / "update-comparison.csv", out / "release-gates.json", out / "AI-NEXT-STEPS.md"]
    if any(path.exists() for path in targets):
        raise SystemExit("Output reports already exist; choose a new directory to preserve history")
    baseline = load_baseline(baseline_path)
    current, zip_digest = inventory_zip(zip_path)
    rows = compare(baseline, current)
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["change"]] += 1
    baseline_total = len(baseline)
    new_total = len(current)
    baseline_reconciled = counts["unchanged"] + counts["modified"] + counts["renamed_or_moved"] + counts["removed"]
    new_reconciled = counts["unchanged"] + counts["modified"] + counts["renamed_or_moved"] + counts["added"]
    gate = baseline_reconciled == baseline_total and new_reconciled == new_total
    summary = {
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "new_zip": str(zip_path),
        "new_zip_sha256": zip_digest,
        "baseline_total": baseline_total,
        "new_total": new_total,
        "counts": dict(counts),
        "baseline_reconciled": baseline_reconciled,
        "new_reconciled": new_reconciled,
        "inventory_gate": "PASS" if gate else "FAIL",
        "port_status": "BLOCKED_PENDING_SEMANTIC_GATES" if gate else "BLOCKED_INVENTORY_FAILED",
        "required_next_gates": [
            "READ_ALL_MODIFIED_ADDED_AND_REMOVED_CAPABILITIES",
            "FACT_LEDGER_REVIEW",
            "FACT_LEDGER_TECHNICAL_PREVIEW",
            "FACT_LEDGER_USER_APPROVAL_BOUND_TO_PREVIEW",
            "LIVE_SPECS_REBUILD_AND_LOCK",
            "AFFECTED_PROJECT_EVALS",
            "RAG_RETRIEVAL_CHECKS_IF_AFFECTED",
            "PROTECTED_RUNTIME_MANIFEST_LOCK",
            "ACTIVE_RUNTIME_DRIFT_GATE",
            "ROLLBACK_ARTIFACT",
            "PACKAGE_DOCTOR",
            "FINAL_USER_APPROVAL_BOUND_TO_CANDIDATE_AND_REPORT_HASH",
            "FINAL_GATE_REPORT",
        ],
    }
    (out / "update-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = [
        "stable_id",
        "change",
        "old_path",
        "new_path",
        "old_sha256",
        "new_sha256",
        "old_size",
        "new_size",
        "review_required",
    ]
    with (out / "update-comparison.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    release_gates = {
        "schema_version": "p2p-codex-release-gates/2",
        "release_zip_sha256": zip_digest,
        "inventory": "PASS" if gate else "FAIL",
        "semantic_source_review": "NOT_STARTED",
        "fact_ledger_review": "NOT_STARTED",
        "fact_ledger_technical_preview": "NOT_STARTED",
        "fact_ledger_user_approval": "NOT_STARTED",
        "live_specs_sync": "NOT_STARTED",
        "project_evals": "NOT_STARTED",
        "rag_retrieval_checks": "NOT_APPLICABLE_OR_NOT_STARTED",
        "active_runtime_drift": "NOT_STARTED",
        "protected_runtime_manifest": "NOT_STARTED",
        "rollback_artifact": "NOT_STARTED",
        "package_doctor": "NOT_STARTED",
        "technical_gate_report": "NOT_STARTED",
        "final_user_approval": "NOT_STARTED",
        "candidate_hash_recheck": "NOT_STARTED",
        "final_gate_report": "NOT_STARTED",
        "release_decision": "BLOCKED",
    }
    (out / "release-gates.json").write_text(json.dumps(release_gates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    instructions = f"""# AI next steps

- Inventory gate: {summary['inventory_gate']}
- Baseline reconciled: {baseline_reconciled}/{baseline_total}
- New release reconciled: {new_reconciled}/{new_total}
- Modified: {counts['modified']}
- Added: {counts['added']}
- Removed: {counts['removed']}
- Renamed/moved: {counts['renamed_or_moved']}

Read every modified and added file in full. Review removed capabilities and all
renames. Update the Excel master and append release history. Then review volatile
claims in FACT_LEDGER, create the deterministic technical preview, obtain
approval for both the exact ledger and preview hashes, rebuild and lock Live
Specs, rerun affected project evals and RAG retrieval checks, rebuild
the protected-runtime manifest, run drift, preserve a rollback artifact, and run
the package doctor. Then create a technical gate report, request final user
approval bound to both the report hash and unchanged candidate hash, and run the
final gate. Update release-gates.json with evidence for each gate. Do not claim
that the Codex runtime was ported: this report is inventory and change detection
only. Stop if inventory is not PASS. Approval cannot override any NOT_STARTED or
FAIL gate, and any candidate change invalidates the approval.
"""
    (out / "AI-NEXT-STEPS.md").write_text(instructions, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if gate else 2


if __name__ == "__main__":
    sys.exit(main())
