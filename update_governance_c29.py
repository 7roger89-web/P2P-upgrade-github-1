# -*- coding: utf-8 -*-
"""C29 governance + ledger + roadmap update.

Applies the closure reconciliation truthfully:
1. C28 roadmap item PLANNED -> DONE (terminal PASS verified by machinery:
   module green, 70 HO tests, 31/31 validator, secret scan 0).
2. C27 BLOCKED item keeps status; add reopen_condition metadata (no execution).
3. current_development semantic sync: roadmap.current = C28/DONE,
   likely_next = C28/DONE (terminal sentinel), current_development updated.
4. C28 candidate record (UNPROMOTED) — deterministic policy: PASS + runtime +
   governance changed -> REQUIRED. SHA filled by the caller (packaging step).
5. C27 machinery record UNKNOWN -> FOUNDATION_READY (evidence-based audit):
   machinery implemented + LH1-LH35 green + 4 real Codex invocations executed
   and classified with real pre-model contacts. Full successful path never
   exercised -> NOT VERIFIED_IMPLEMENTED.
6. New C29 ledger records (standard v2 delta, honest status).
7. Provenance entries for the C29 reconciliation and the C27 audit.
Idempotent on repeated runs (checks before writing).
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
GOV = ROOT / "governance" / "development-control.json"
LEDGER = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"
ROADMAP = ROOT / "docs" / "p2p-development" / "current-roadmap.md"

NOW = "2026-08-17T02:40:00Z"


def load(path):
    return json.loads(path.read_text())


def save(path, obj):
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


def main() -> None:
    activate = "--activate" in sys.argv[1:]

    # ---- governance ----
    g = load(GOV)
    road = g.setdefault("roadmap", {})
    items = road.setdefault("items", [])

    # 1. C28 roadmap item -> DONE
    for i in items:
        if i.get("id") == "C28":
            if i.get("status") != "DONE":
                i["status"] = "DONE"
                i["notes"] = (
                    "C28 terminal state: PASS (machinery). Full provider-neutral "
                    "connection + credential onboarding layer implemented and "
                    "verified (70 HO tests, 31/31 validator, secret scan 0). "
                    "No host claimed live-certified; owner action codex login / "
                    "Manus connector remains the irreducible next step."
                )
            break

    # 2. C27 reopen_condition metadata (no auto-execution)
    for i in items:
        if i.get("id") == "C27":
            if "reopen_condition" not in i:
                i["reopen_condition"] = (
                    "at least one real host reaches connection_status "
                    "AUTH_REQUIRED or stronger (live probe eligible); "
                    "metadata only, never auto-executed"
                )
                i["reopen_executes"] = "no"
            break

    # 3. roadmap.current / likely_next terminal sentinel
    current = road.setdefault("current", {})
    if current.get("id") != "C28":
        road["current"] = {
            "id": "C28", "status": "DONE",
            "title": "Secure Host Connection & Credential Onboarding "
                     "- determine required auth, verify safely, minimal Owner action outside chat",
        }
    likely = road.setdefault("likely_next", {})
    if likely.get("id") != "C28" or str(likely.get("status", "")).upper() != "DONE":
        road["likely_next"] = {"id": "C28", "status": "DONE", "title": road["current"]["title"]}

    # current_development semantic sync (no second state store)
    cd = g.get("current_development", {})
    if cd.get("development_goal") != "C28":
        cd["development_goal"] = "C28"
        cd["status"] = "CANDIDATE_UNPROMOTED"
        cd["source_version"] = "8.4.7-C-codex.22"
        cd["source_version_status"] = "CANDIDATE_UNPROMOTED"
        cd["based_on_official_version"] = "8.4.7-C-codex.19"
        cd["owner_action_required"] = (
            "C28 onboarding machinery FOUNDATION_READY; live certification needs one "
            "Owner action outside chat (codex login or Manus API connector); "
            "candidates remain UNPROMOTED; no automatic host routing claimed."
        )
        cd["automatic_host_routing_ready"] = False
        cd["live_manus_adapter_certified"] = False
        cd["portable_execution_envelope_ready"] = True
        cd["portable_result_receipt_ready"] = True
        cd["cross_host_continuation_contract_ready"] = True
        cd["host_requirement_profile_ready"] = True
        cd["host_capability_discovery_foundation_ready"] = True
        cd["foundation_status"] = "ONBOARDING_MACHINERY_FOUNDATION_READY"

    # 4. C28 candidate record (UNPROMOTED) - SHA filled by packaging step if absent
    records = g.setdefault("candidate_records", [])
    if not any(r.get("candidate_id") == "C28" for r in records):
        records.append({
            "candidate_id": "C28",
            "candidate_label": "P2P-8.4.7-C-Codex-Edition-v22-c28-secure-host-"
                               "connection-credential-onboarding-candidate-v1.zip",
            "candidate_sha256": "TO_BE_FILLED_BY_PACKAGING",
            "artifact_path": "reports/candidates/P2P-8.4.7-C-Codex-Edition-v22-"
                             "c28-secure-host-connection-credential-onboarding-candidate-v1.zip",
            "promotion_status": "UNPROMOTED",
            "based_on_official_version": "8.4.7-C-codex.19",
            "evidence_refs": [
                "docs/p2p-development/reports/P2P-C28-terminal-report.md",
                "P2P-C28 intake; terminal PASS reconciled under C29 closure policy",
            ],
        })

    # 7a. provenance: C29 closure reconciliation
    prov = g.setdefault("provenance_log", [])
    last = prov[-1] if prov else None
    if last is None or last.get("change_id") != "C29-2026T08T17T02T40T00Z":
        prov.append({
            "goal": "C29",
            "change_id": "C29-2026T08T17T02T40T00Z",
            "changed_at": NOW,
            "what_changed": (
                "Goal closure integrity: terminal verdict reconciled across roadmap, "
                "development-control, ledger, candidate policy; C28 roadmap DONE; "
                "terminal likely_next sentinel C28/DONE; candidate policy applied "
                "deterministically (C28 candidate required and recorded UNPROMOTED); "
                "C27 reopen_condition metadata added; C27 machinery status audited "
                "to FOUNDATION_READY with real-execution evidence"
            ),
            "why": (
                "C29 specification: terminal verdict must be semantically consistent "
                "with all durable surfaces; the C28 terminal-time candidate exemption "
                "was an AI judgment and was corrected by deterministic policy"
            ),
            "evidence_refs": [
                "docs/p2p-development/reports/P2P-C29-terminal-report.md",
                "scripts/p2p_goal_closure.py (deterministic closure policy)",
                "CHANGE-DIFF-PR5",
            ],
        })

    save(GOV, g)
    print("governance updated")

    # ---- ledger ----
    d = load(LEDGER)
    caps = d.get("capabilities", [])
    by_id = {c["capability_id"]: c for c in caps}

    # 5. C27 machinery UNKNOWN -> FOUNDATION_READY
    mach = by_id.get("REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY")
    if mach is not None and mach.get("status") == "UNKNOWN":
        mach["status"] = "FOUNDATION_READY"
        mach["notes"] = (
            "C29 evidence-based audit: machinery implemented and exercised against "
            "the real Codex CLI binary (4 probe invocations, pre-model 401 "
            "classified as AUTH_TARGET_MISMATCH/AUTH_INVALID with durable evidence); "
            "LH1-LH35 green. The FULL successful execution path "
            "(execute -> result -> independent verification -> reconciliation PASS) "
            "has never occurred, so VERIFIED_IMPLEMENTED is not truthful. "
            "Outcome capability REAL_HOST_EXECUTION_CERTIFICATION stays UNKNOWN."
        )
        mach["origin_refs"] = [
            "docs/p2p-development/reports/P2P-C27-terminal-report.md",
            "docs/p2p-development/reports/P2P-C29-terminal-report.md",
            "LH1-LH35 real machinery exercise",
        ]

    if activate:
        # 6. C29 ledger records (added only when C29 artifacts exist - caller controls)
        new = []
        for c in (
            {
                "capability_id": "GOAL_CLOSURE_INTEGRITY_CHECK",
                "title": "Deterministic goal closure consistency checker: terminal "
                         "verdict verified against roadmap, development-control, "
                         "candidate policy, capability/goal separation",
                "status": "FOUNDATION_READY",
                "family": "TRUTH_AND_GOVERNANCE",
                "origin_type": "IMPLEMENTATION_GOAL",
                "beginner_value": "Every terminal verdict (PASS/BLOCKED/FAIL) is verified deterministically against the roadmap, governance, candidate records and capability/goal separation, so a ghost inconsistency (roadmap DONE but no candidate) can never silently recur.",
                "principle": "TERMINAL_VERDICT_IS_RECONCILED",
                "origin_refs": [
                    "docs/p2p-development/reports/P2P-C29-terminal-report.md",
                    "GC1-GC50 real test execution",
                ],
                "dependencies": [
                    "GOAL_CANDIDATE_RELEASE_PROMOTION_LIFECYCLE",
                    "C22_C24_ADAPTER_LIVE_CERTIFICATION",
                ],
                "freshness": "from_plan_or_report",
            },
            {
                "capability_id": "DETERMINISTIC_CANDIDATE_REQUIREMENT_POLICY",
                "title": "Candidate requirement is a deterministic policy (contract "
                         "declaration + artifact-change signals), never AI judgment "
                         "at terminal time",
                "status": "FOUNDATION_READY",
                "family": "TRUTH_AND_GOVERNANCE",
                "origin_type": "IMPLEMENTATION_GOAL",
                "beginner_value": "Whether a candidate is required is decided by deterministic contract declarations and artifact-change signals, never by AI judgment at terminal time, so the beginner always sees the same answer on every surface.",
                "principle": "CANDIDATE_REQUIREMENT_IS_POLICY_NOT_JUDGMENT",
                "origin_refs": [
                    "docs/p2p-development/reports/P2P-C29-terminal-report.md",
                    "GC module real exercise on C27/C28 closure",
                ],
                "dependencies": [
                    "GOAL_CANDIDATE_RELEASE_PROMOTION_LIFECYCLE",
                    "GOAL_CLOSURE_INTEGRITY_CHECK",
                ],
                "freshness": "from_plan_or_report",
            },
        ):
            if c["capability_id"] not in by_id:
                new.append(c)
                caps.append(c)
        for n in new:
            print("ledger +", n["capability_id"])

        save(LEDGER, d)

    print("C28 candidate sha256 in governance:",
          next((r["candidate_sha256"] for r in g["candidate_records"]
                if r.get("candidate_id") == "C28"), None))


if __name__ == "__main__":
    main()
