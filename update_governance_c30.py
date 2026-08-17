#!/usr/bin/env python3
"""C30 governance update (idempotent).

Adds the C30 roadmap item (PLANNED), C30 capability_status entry,
moves current_development to C30 (IN_PROGRESS, source .24), and wires
pr_lineage + provenance entries for the C30 session. The candidate
record is filled with the real artifact SHA by fill_c30_candidate.py
after the candidate build (this script leaves a placeholder marker
only in the roadmap/capability surfaces, not in candidate_records —
per the candidate policy the record is created at packaging time).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
GOV_PATH = ROOT.joinpath("governance", "development-control.json")

NEW = "8.4.7-C-codex.24"
GOAL = "C30"
TITLE = ("Composable Execution Target Foundation + Durable Provider-Neutral "
         "Architecture Intake — ExecutionTarget composition model, eligibility "
         "evaluation, fingerprint/drift, backend registry, provider-neutral "
         "intake (no router, no autonomy, no real execution)")
OFFICIAL_VERSION = "8.4.7-C-codex.19"
OFFICIAL_SHA256 = "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8"


def main() -> int:
    gov = json.loads(GOV_PATH.read_text())

    # --- roadmap item -------------------------------------------------
    items = gov["roadmap"]["items"]
    if not any(i.get("id") == GOAL for i in items):
        items.append({
            "id": GOAL,
            "status": "PLANNED",
            "title": TITLE,
            "evidence_ref": "GOAL-C30",
            "notes": ("C30 PLANNED at goal declaration. Foundation machinery "
                      "(p2p_execution_target.py, ET1-ET60, ledger reconciliation, "
                      "research intake artifact) implemented in the C30 session; "
                      "terminal verdict PASS (machinery)."),
        })

    # --- roadmap current / likely_next --------------------------------
    # Terminal sentinel: roadmap.current remains C28/DONE (the last DONE goal).
    gov["roadmap"]["current"] = {"id": "C28", "status": "DONE",
                                 "title": items[0].get("title", "") if items else ""}
    gov["roadmap"]["likely_next"] = {
        "id": GOAL, "status": "PLANNED", "title": TITLE}

    # --- capability_status ---------------------------------------------
    cs = gov["capability_status"]
    if not any(c.get("id") == GOAL for c in cs):
        cs.append({
            "id": GOAL,
            "status": "IN_PROGRESS",
            "result": "MACHINERY_FOUNDATION_READY",
            "composable_execution_target_foundation": True,
            "provider_neutral_intake_recorded": True,
            "candidate_id": None,
            "candidate_version": None,
            "candidate_sha256": None,
            "promotion_status": None,
            "evidence_ref": "E0-C30-ET1-ET60",
        })

    # --- current_development -------------------------------------------
    cd = gov["current_development"]
    cd["development_goal"] = GOAL
    cd["status"] = "IN_PROGRESS"
    cd["source_version"] = NEW
    cd["source_version_status"] = "CANDIDATE_UNPROMOTED"
    cd["historical_maintenance_mode"] = False
    cd["based_on_official_version"] = OFFICIAL_VERSION
    cd["based_on_official_sha256"] = OFFICIAL_SHA256
    for k in ("candidate_id", "candidate_label", "candidate_sha256",
              "candidate_path", "promotion_status", "artifact_path"):
        cd.pop(k, None)

    # --- pr_lineage (branch -> parent branch) --------------------------
    lineage = gov.setdefault("pr_lineage", {})
    lineage["p2p-c30-composable-execution-target"] = (
        "p2p-c29-goal-closure-integrity")

    # --- provenance (list of entries) ----------------------------------
    prov = gov.setdefault("provenance", [])
    entry = {
        "change_id": "C30-IMPLEMENTATION-001",
        "goal": GOAL,
        "action": ("C30 goal declared; roadmap item PLANNED; "
                   "current_development moved to C30 (IN_PROGRESS, "
                   f"source {NEW}); research intake artifact durable; "
                   "candidate per C29 policy after packaging"),
        "evidence_ref": "docs/p2p-development/research/"
                        "execution-target-pattern-research.md",
    }
    if not any(p.get("change_id") == entry["change_id"] for p in prov):
        prov.append(entry)

    GOV_PATH.write_text(json.dumps(gov, indent=2, ensure_ascii=False) + "\n")
    print(f"governance updated: roadmap items={len(items)}, "
          f"capability_status={len(cs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
