#!/usr/bin/env python3
"""Finalize governance for C26 after a successful verify (zip already at the
canonical candidate path). Adds the C26 candidate record, flips
current_development to C26, and records the provenance log entry."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOV = ROOT / "governance" / "development-control.json"
CANONICAL = (ROOT / "reports" / "candidates"
             / "P2P-8.4.7-C-Codex-Edition-v21-c26-durable-capability-provenance-goal-ledger-dependency-governance-candidate-v1.zip")

OFFICIAL_SHA256 = "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8"
LABEL = CANONICAL.name


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    assert CANONICAL.is_file(), f"canonical candidate missing: {CANONICAL}"
    digest = sha256_of(CANONICAL)
    print(f"candidate SHA-256: {digest}")

    gov = json.loads(GOV.read_text(encoding="utf-8"))
    records = gov["candidate_records"]

    record = {
        "candidate_id": "C26",
        "based_on_official_version": "8.4.7-C-codex.19",
        "based_on_official_sha256": OFFICIAL_SHA256,
        "development_goal": "C26",
        "candidate_version": "8.4.7-C-codex.21",
        "candidate_label": LABEL,
        "candidate_sha256": digest,
        "embedded_version": "8.4.7-C-codex.21",
        "promotion_status": "UNPROMOTED",
        "lineage_status": "LINEAGE_RECONCILED",
        "artifact_path": f"reports/candidates/{LABEL}",
        "evidence_refs": [
            "CP1-CP50 PASS (tests/test_p2p_ledger_provenance.py)",
            "framework validator 31/31 PASS (scripts/validate_p2p_development_framework.py; V11-V17 added)",
            "E3-P3-C26-PACKAGE (package_release.py verify PASS on candidate)",
            "capability-index.json schema v2 with 129 records; origin + dependency coverage 100%",
            "EXECUTION_POLICY<->PARALLEL_EXECUTION dependency cycle broken and documented",
        ],
    }
    if not any(r.get("candidate_id") == "C26" for r in records):
        records.append(record)
        gov["candidate_records"] = records

    cd_ = gov["current_development"]
    cd_["development_goal"] = "C26"
    cd_["status"] = "CANDIDATE_UNPROMOTED"
    cd_["candidate_id"] = "C26"
    cd_["candidate_label"] = LABEL
    cd_["candidate_sha256"] = digest
    cd_["artifact_path"] = f"reports/candidates/{LABEL}"
    cd_["promotion_status"] = "UNPROMOTED"

    gov["roadmap"]["current"] = {
        "id": "C26",
        "status": "ACTIVE",
        "title": "Durable capability provenance, dependency & goal-to-ledger governance",
    }
    for item in gov["roadmap"]["items"]:
        if item.get("id") == "C26":
            item["status"] = "DONE"
    ln = gov["roadmap"].get("likely_next")
    if isinstance(ln, dict) and ln.get("id") == "C26":
        ln["status"] = "DONE"

    prov = gov.setdefault("provenance_log", [])
    if prov and any(p.get("change_id") == "P2P-C26-CANDIDATE" for p in prov):
        GOV.write_text(json.dumps(gov, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("provenance entry already present; governance unchanged")
        return 0

    prov.append({
        "change_id": "P2P-C26-CANDIDATE",
        "changed_at": "2026-08-17T00:00:00Z",
        "what_changed": f"C26 candidate built and verified (package_release verify PASS): {LABEL}",
        "why": "Goal C26 reached terminal state with a verified candidate package; governance advanced current_development to C26",
        "evidence_refs": [
            "CP1-CP50 PASS (tests/test_p2p_ledger_provenance.py)",
            "framework validator 31/31 PASS (scripts/validate_p2p_development_framework.py; V11-V17 added)",
            "E3-P3-C26-PACKAGE (package_release.py verify PASS on candidate)",
            "capability-index.json schema v2 with 129 records; origin + dependency coverage 100%",
        ],
        "artifact": f"reports/candidates/{LABEL}",
        "artifact_sha256": digest,
    })

    GOV.write_text(json.dumps(gov, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("governance finalized: current_development=C26, candidate record added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
