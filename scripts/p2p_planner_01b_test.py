#!/usr/bin/env python3
"""P2P-OWNER-SELECTED-CAPABILITY-INTAKE-CLOSURE-01 test harness (spec §11).
12 negative/property tests A-L for planner v3 intake-coverage gates.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

PLANNER = "/home/ubuntu/fw01_work/auth-f01/scripts/p2p_roadmap_planner.py"
BASELINE_VERSION = "8.4.7-C-codex.41"
BASELINE_SHA = "da835f8a48caf4536094ffdd82e3c65baa82da32aa9a7ae73714ee1f2e9c3d2d"


def new_root():
    root = tempfile.mkdtemp(prefix="planner01b_fix_")
    os.makedirs(f"{root}/governance", exist_ok=True)
    os.makedirs(f"{root}/docs/p2p-development/capability-ledger", exist_ok=True)
    return root


def dctl(**kw):
    d = {
        "official_baseline": {
            "version": BASELINE_VERSION, "artifact_sha256": BASELINE_SHA,
            "promotion_status": "PROMOTED_VERIFIED", "approval_reference":
                "P2P-APR-20260821T035410Z-c41-official-baseline-promotion"},
        "roadmap": {"items": []}, "candidates": [], "approvals": {"records": []},
        "architectural_invariants": [], "capabilities": [],
    }
    d.update(kw)
    return d


def rd_item(rid, status="PLANNED", priority=5, family="CONTEXT_AND_RETRIEVAL",
            source_research_ids=None, canonical_capability_ids=None, deps=None,
            defer_reason=""):
    return {"roadmap_id": rid, "title": f"item {rid}", "family": family,
            "status": status, "priority": priority,
            "dependencies": deps or [], "blockers": [],
            "source_research_ids": source_research_ids or [],
            "canonical_capability_ids": canonical_capability_ids or [],
            "defer_reason": defer_reason, "mutation_risk_class": "READ_ONLY",
            "project_impact": "NONE", "promotion_required": "NO"}


def ledger(**kw):
    d = {"records": [], "rejected_register": []}
    d.update(kw)
    return d


def intake(**kw):
    d = {"intake_records": [], "vocabulary": {}}
    d.update(kw)
    return d


def contract(**kw):
    d = {"schema": "p2p-intake-contract/1", "capability_family_alias_table": {},
         "capability_to_roadmap_enumeration_policy": ""}
    d.update(kw)
    return d


def capidx(**kw):
    d = {"capabilities": []}
    d.update(kw)
    return d


def write(root, obj, *parts):
    with open(os.path.join(root, *parts), "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)



def load_plan(root):
    tmp = os.path.join(root, "plan_output.json")
    r = subprocess.run(["python3", PLANNER, "--repo", root, "--output", tmp],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"planner exit {r.returncode}: {r.stderr[-2000:]}"
    return json.load(open(tmp)), r


def gate(plan):
    return plan["ROADMAP_COVERAGE_GATE"]


results = []
tmps = []


def check(name, cond, why=""):
    if not cond:
        print(f"FAIL {name}: {why}")
        results.append(1)
        return
    print(f"PASS {name}")
    results.append(0)


def base_root():
    root = new_root()
    items = [
        rd_item("RM-PRIORITY-CONTEXT", priority=3,
                source_research_ids=["RA-001"], canonical_capability_ids=["C19"]),
        rd_item("RM-PRIORITY-DESIGN", priority=1, status="PLANNED",
                deps=["RM-PRIORITY-LARGE-GOAL"]),
        rd_item("RM-PRIORITY-LARGE-GOAL", priority=2, status="PLANNED",
                defer_reason="completion required by Zero-to-Project dependency policy"),
    ]
    write(root, dctl(roadmap={"items": items}), "governance", "development-control.json")
    write(root, {"items": items, "schema": "p2p-framework/development-roadmap/1"},
          "governance", "p2p-development-roadmap.json")
    write(root, ledger(records=[{"research_id": "RA-001", "status": "SHIPPED",
                                 "source_name": "C19 context retrieval",
                                 "canonical_capability_ids": ["C19"]}]),
          "governance", "research-adoption-ledger.json")
    write(root, intake(), "governance", "research-intake-ledger.json")
    write(root, contract(), "governance", "intake-contract.json")
    write(root, capidx(capabilities=[{"capability_id": "C19",
                                      "family": "CONTEXT_AND_KNOWLEDGE",
                                      "status": "VERIFIED",
                                      "origin_type": "EVIDENCE"}]),
          "docs", "p2p-development", "capability-ledger", "capability-index.json")
    return root


def main():
    # A: accepted-intake orphan detection
    try:
        root = base_root()
        tmps.append(root)
        w = json.load(open(f"{root}/governance/research-intake-ledger.json"))
        w["intake_records"].append({"id": "RI-X1", "classification": "ACCEPTED",
                                    "subject": "New Orphan Capability Foo",
                                    "status": "PENDING", "source": "owner-chat",
                                    "scope": "architecture", "evidence_ref": "chat-memory",
                                    "instruction_ref": "none"})
        json.dump(w, open(f"{root}/governance/research-intake-ledger.json", "w"),
                  indent=2, ensure_ascii=False)
        p, r = load_plan(root)
        cg = gate(p)
        check("A", cg["ROADMAP_COVERAGE_GAP"] and p["RECOMMENDED_NEXT_GOAL"] is None
              and any(g["reason"] == "ACCEPTED_INTAKE_WITHOUT_ADOPTION_RECORD"
                      and g["intake_id"] == "RI-X1"
                      for g in p["ROADMAP_COVERAGE_GAPS"]),
              "accepted intake without adoption record did not trip the gap")
    finally:
        pass

    # B: material adoption without capability or roadmap consideration
    try:
        root = base_root()
        tmps.append(root)
        w = json.load(open(f"{root}/governance/research-adoption-ledger.json"))
        w["records"].append({"research_id": "RA-B1", "status": "PLANNED",
                             "source_name": "Material research B1",
                             "canonical_capability_ids": []})
        json.dump(w, open(f"{root}/governance/research-adoption-ledger.json", "w"),
                  indent=2, ensure_ascii=False)
        p, r = load_plan(root)
        cg = gate(p)
        check("B", cg["ROADMAP_COVERAGE_GAP"]
              and any(g["reason"] == "MATERIAL_ADOPTION_WITHOUT_CAPABILITY_OR_ROADMAP"
                      and g["research_id"] == "RA-B1"
                      for g in p["ROADMAP_COVERAGE_GAPS"]),
              "material adoption without capability or roadmap did not trip the gap")
    finally:
        pass

    # C: reverse coverage gap — material research without roadmap consideration
    try:
        root = base_root()
        tmps.append(root)
        w = json.load(open(f"{root}/governance/research-adoption-ledger.json"))
        w["records"].append({"research_id": "RA-C1", "status": "SELECTED",
                             "source_name": "Material selected research C1"})
        json.dump(w, open(f"{root}/governance/research-adoption-ledger.json", "w"),
                  indent=2, ensure_ascii=False)
        p, r = load_plan(root)
        cg = gate(p)
        check("C", cg["ROADMAP_COVERAGE_GAP"]
              and any(g["reason"] == "MATERIAL_RESEARCH_WITHOUT_ROADMAP_CONSIDERATION"
                      and g["research_id"] == "RA-C1"
                      for g in p["ROADMAP_COVERAGE_GAPS"])
              and p["RECOMMENDED_NEXT_GOAL"] is None,
              "reverse coverage gap not reported")
    finally:
        pass

    # D: exact missed-intake failure mode end-to-end (CRI-class case, spec §10)
    try:
        root = base_root()
        tmps.append(root)
        w = json.load(open(f"{root}/governance/research-intake-ledger.json"))
        w["intake_records"].append({"id": "RI-D1", "classification": "ACCEPTED",
                                    "subject": "Contextual Rule Intelligence / Domain Policy Packs",
                                    "status": "PENDING", "source": "owner-chat",
                                    "scope": "architecture", "evidence_ref": "chat-memory",
                                    "instruction_ref": "none"})
        json.dump(w, open(f"{root}/governance/research-intake-ledger.json", "w"),
                  indent=2, ensure_ascii=False)
        p, r = load_plan(root)
        cg = gate(p)
        check("D", p["PLANNING_STATUS"] == "BLOCKED / ROADMAP_COVERAGE_GAP"
              and p["PLAN_COMPLETE"] is False and p["RECOMMENDED_NEXT_GOAL"] is None
              and cg["ROADMAP_COVERAGE_GAP"] is True
              and any(g["reason"] == "ACCEPTED_INTAKE_WITHOUT_ADOPTION_RECORD"
                      and g["intake_id"] == "RI-D1"
                      for g in p["ROADMAP_COVERAGE_GAPS"]),
              "exact missed-intake mode did not fail closed")
    finally:
        pass

    # E: reactivity — completing the intake cycle clears the gap and restores plan
    try:
        root = base_root()
        tmps.append(root)
        li = json.load(open(f"{root}/governance/research-intake-ledger.json"))
        li["intake_records"].append({"id": "RI-E1", "classification": "ACCEPTED",
                                     "subject": "Contextual Rule Intelligence / Domain Policy Packs",
                                     "status": "PENDING", "source": "owner-chat",
                                     "scope": "architecture", "evidence_ref": "chat-memory",
                                     "instruction_ref": "none"})
        json.dump(li, open(f"{root}/governance/research-intake-ledger.json", "w"),
                  indent=2, ensure_ascii=False)
        ld = json.load(open(f"{root}/governance/research-adoption-ledger.json"))
        ld["records"].append({"research_id": "RA-EXT-099", "status": "PLANNED",
                              "source_name": "Contextual Rule Intelligence / Domain Policy Packs",
                              "intake_record": "RI-E1", "canonical_capability_ids": ["CRI"],
                              "roadmap_relation": "composition"})
        json.dump(ld, open(f"{root}/governance/research-adoption-ledger.json", "w"),
                  indent=2, ensure_ascii=False)
        # enumerate the adopted research into an existing roadmap item (option A:
        # add to the item's source_research_ids) — mirrors canonical reconciliation.
        rd = json.load(open(f"{root}/governance/p2p-development-roadmap.json"))
        rd["items"][0]["source_research_ids"].append("RA-EXT-099")
        json.dump(rd, open(f"{root}/governance/p2p-development-roadmap.json", "w"),
                  indent=2, ensure_ascii=False)
        dc = json.load(open(f"{root}/governance/development-control.json"))
        dc["roadmap"]["items"][0]["source_research_ids"].append("RA-EXT-099")
        json.dump(dc, open(f"{root}/governance/development-control.json", "w"),
                  indent=2, ensure_ascii=False)
        ci = json.load(open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json"))
        ci["capabilities"].append({"capability_id": "CRI",
                                   "family": "CONTEXT_AND_KNOWLEDGE",
                                   "status": "PLANNED",
                                   "origin_type": "OWNER_ACCEPTED_PROPOSAL",
                                   "notes": "defer pending roadmap enumeration"})
        # enumerate CRI into the CONTEXT roadmap item via composition_entries
        # (canonical option from INTAKE-CLOSURE-01), mirroring repo truth:
        rd2 = json.load(open(f"{root}/governance/p2p-development-roadmap.json"))
        ce = rd2["items"][0].setdefault("composition_entries", [])
        ce.append({"research_id": "RA-EXT-099", "capability": "CRI",
                   "note": "compose adopted CRI research into Context goal"})
        json.dump(rd2, open(f"{root}/governance/p2p-development-roadmap.json", "w"),
                  indent=2, ensure_ascii=False)
        dc2 = json.load(open(f"{root}/governance/development-control.json"))
        ce2 = dc2["roadmap"]["items"][0].setdefault("composition_entries", [])
        ce2.append({"research_id": "RA-EXT-099", "capability": "CRI",
                    "note": "compose adopted CRI research into Context goal"})
        json.dump(dc2, open(f"{root}/governance/development-control.json", "w"),
                  indent=2, ensure_ascii=False)
        json.dump(ci, open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json", "w"),
                  indent=2, ensure_ascii=False)
        p, r = load_plan(root)
        cg = gate(p)
        print("[DEBUG-E] gaps:", p["ROADMAP_COVERAGE_GAPS"], "REC:",
              p["RECOMMENDED_NEXT_GOAL"])
        check("E", not cg["ROADMAP_COVERAGE_GAP"] and cg["ORPHAN_OWNER_DECISIONS"] == []
              and p["PLAN_COMPLETE"] is True and p["RECOMMENDED_NEXT_GOAL"] is not None,
              "completing intake did not clear the gap / restore recommendation")
    finally:
        pass

    # F: registry-inventory caps never gate (spec §8)
    try:
        root = base_root()
        tmps.append(root)
        ci = json.load(open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json"))
        ci["capabilities"] += [
            {"capability_id": "LEG-P1", "family": "CONTEXT_AND_KNOWLEDGE",
             "status": "PARTIAL", "origin_type": "PROJECT_LEARNING",
             "notes": "registry inventory only"},
            {"capability_id": "LEG-P2", "family": "RECOVERY_AND_CONTINUATION",
             "status": "PLANNED", "origin_type": "RECOVERED_LEGACY",
             "notes": "registry inventory only"}]
        json.dump(ci, open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json", "w"),
                  indent=2, ensure_ascii=False)
        p, r = load_plan(root)
        cg = gate(p)
        flagged = [g["capability_id"] for g in p["ROADMAP_COVERAGE_GAPS"]
                   if g["reason"] == "FUTURE_WORK_CAPABILITY_WITHOUT_ROADMAP_CONSIDERATION"]
        check("F", "LEG-P1" not in flagged and "LEG-P2" not in flagged
              and not cg["ROADMAP_COVERAGE_GAP"],
              f"registry-inventory caps gated: {flagged}")
    finally:
        pass

    # G: family alias table satisfied (CONTEXT_AND_KNOWLEDGE <-> CONTEXT_AND_RETRIEVAL)
    try:
        root = base_root()
        tmps.append(root)
        ic = json.load(open(f"{root}/governance/intake-contract.json"))
        ic["capability_family_alias_table"] = {
            "CONTEXT_AND_KNOWLEDGE": {"roadmap_family": "CONTEXT_AND_RETRIEVAL",
                                      "note": "bound by INTAKE-CLOSURE-01"}}
        json.dump(ic, open(f"{root}/governance/intake-contract.json", "w"),
                  indent=2, ensure_ascii=False)
        ci = json.load(open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json"))
        ci["capabilities"].append({"capability_id": "SYM-RET",
                                   "family": "CONTEXT_AND_KNOWLEDGE",
                                   "status": "PLANNED",
                                   "origin_type": "OWNER_ACCEPTED_PROPOSAL"})
        json.dump(ci, open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json", "w"),
                  indent=2, ensure_ascii=False)
        # G (v4 semantics): family alias ALONE no longer satisfies — the item's
        # canonical_capability_ids must enumerate SYM-RET explicitly (option B).
        rd = json.load(open(f"{root}/governance/p2p-development-roadmap.json"))
        rd["items"][0]["canonical_capability_ids"].append("SYM-RET")
        json.dump(rd, open(f"{root}/governance/p2p-development-roadmap.json", "w"),
                  indent=2, ensure_ascii=False)
        dc = json.load(open(f"{root}/governance/development-control.json"))
        dc["roadmap"]["items"][0]["canonical_capability_ids"].append("SYM-RET")
        json.dump(dc, open(f"{root}/governance/development-control.json", "w"),
                  indent=2, ensure_ascii=False)
        p, r = load_plan(root)
        cg = gate(p)
        flagged = [g["capability_id"] for g in p["ROADMAP_COVERAGE_GAPS"]
                   if g["reason"] == "FUTURE_WORK_CAPABILITY_WITHOUT_ROADMAP_CONSIDERATION"]
        check("G", "SYM-RET" not in flagged and not cg["ROADMAP_COVERAGE_GAP"],
              f"explicit enumeration did not cover SYM-RET: {flagged}")
    finally:
        pass

    # H: explicit defer note satisfies coverage
    try:
        root = base_root()
        tmps.append(root)
        ci = json.load(open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json"))
        ci["capabilities"].append({"capability_id": "DEF-CAP", "family": "NEW_FAMILY_X",
                                   "status": "PLANNED",
                                   "origin_type": "OWNER_ACCEPTED_PROPOSAL",
                                   "roadmap_relation": "defer: Owner defers until lifecycle goal completes"})
        json.dump(ci, open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json", "w"),
                  indent=2, ensure_ascii=False)
        p, r = load_plan(root)
        cg = gate(p)
        flagged = [g["capability_id"] for g in p["ROADMAP_COVERAGE_GAPS"]
                   if g["reason"] == "FUTURE_WORK_CAPABILITY_WITHOUT_ROADMAP_CONSIDERATION"]
        check("H", "DEF-CAP" not in flagged and not cg["ROADMAP_COVERAGE_GAP"],
              f"defer note did not satisfy coverage: {flagged}")
    finally:
        pass

    # I: option-B enumeration (cap listed in roadmap item ids) satisfies coverage
    try:
        root = base_root()
        tmps.append(root)
        ci = json.load(open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json"))
        ci["capabilities"].append({"capability_id": "ENUM-CAP", "family": "NEW_FAMILY_Y",
                                   "status": "PLANNED",
                                   "origin_type": "OWNER_ACCEPTED_PROPOSAL",
                                   "notes": "enumerated into CONTEXT item"})
        json.dump(ci, open(f"{root}/docs/p2p-development/capability-ledger/capability-index.json", "w"),
                  indent=2, ensure_ascii=False)
        rd = json.load(open(f"{root}/governance/p2p-development-roadmap.json"))
        rd["items"][0]["canonical_capability_ids"].append("ENUM-CAP")
        dc = json.load(open(f"{root}/governance/development-control.json"))
        dc["roadmap"]["items"][0]["canonical_capability_ids"] = ["C19", "ENUM-CAP"]
        json.dump(rd, open(f"{root}/governance/p2p-development-roadmap.json", "w"),
                  indent=2, ensure_ascii=False)
        json.dump(dc, open(f"{root}/governance/development-control.json", "w"),
                  indent=2, ensure_ascii=False)
        p, r = load_plan(root)
        cg = gate(p)
        flagged = [g["capability_id"] for g in p["ROADMAP_COVERAGE_GAPS"]
                   if g["reason"] == "FUTURE_WORK_CAPABILITY_WITHOUT_ROADMAP_CONSIDERATION"]
        check("I", "ENUM-CAP" not in flagged and not cg["ROADMAP_COVERAGE_GAP"],
              f"option-B enumeration did not satisfy coverage: {flagged}")
    finally:
        pass

    # J: zero writes / zero execution / zero project mutation
    try:
        root = base_root()
        tmps.append(root)
        watch = f"{root}/docs/p2p-development/capability-ledger/capability-index.json"
        before = open(watch, "rb").read()
        p, r = load_plan(root)
        after = open(watch, "rb").read()
        check("J", before == after,
              "planner mutated an input file during planning")
    finally:
        pass

    # K: deterministic ranking + hash drift invalidates stale plan
    try:
        root = base_root()
        tmps.append(root)
        p1, _ = load_plan(root)
        p2, _ = load_plan(root)
        det = (p1["RECOMMENDED_NEXT_GOAL"] == p2["RECOMMENDED_NEXT_GOAL"]
               and p1["HASHES"]["research_adoption_ledger_json_sha256"] ==
               p2["HASHES"]["research_adoption_ledger_json_sha256"])
        w = json.load(open(f"{root}/governance/research-adoption-ledger.json"))
        w["records"].append({"research_id": "RA-DRIFT-1", "status": "SHIPPED",
                             "source_name": "drift probe",
                             "canonical_capability_ids": ["C19"]})
        json.dump(w, open(f"{root}/governance/research-adoption-ledger.json", "w"),
                  indent=2, ensure_ascii=False)
        p3, _ = load_plan(root)
        drift = (p3["HASHES"]["research_adoption_ledger_json_sha256"] !=
                 p1["HASHES"]["research_adoption_ledger_json_sha256"])
        check("K", det and drift, "determinism or hash drift failed")
    finally:
        pass

    # L: v3 hash binding includes intake contract + intake ledger SHAs
    try:
        root = base_root()
        tmps.append(root)
        p, r = load_plan(root)
        h = p["HASHES"]
        check("L", "intake_contract_json_sha256" in h
              and "research_intake_ledger_json_sha256" in h,
              f"v3 intake hashes not bound: {sorted(h.keys())}")
    finally:
        pass

    for t in tmps:
        shutil.rmtree(t, ignore_errors=True)

    passed = sum(1 for x in results if x == 0)
    print(f"\n=== {passed}/{len(results)} tests passed ===")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
