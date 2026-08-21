#!/usr/bin/env python3
"""P2P-OWNER-CAPABILITY-INTAKE-STRICT-BINDING-01 — negative test matrix A–R.

All tests run planner v4 in disposable fixture roots built from the canonical
governance truth. A–N probe each seam; O–R probe restored canonical behavior,
determinism, zero input mutation, and zero project mutation.

Usage:  python3 p2p_planner_strictbind_test.py
Exit 0 when ALL PASS, non-zero otherwise.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = "/home/ubuntu/fw01_work/auth-f01"
PLANNER = os.path.join(REPO, "scripts", "p2p_roadmap_planner.py")
SYSROOT = "/tmp/strictbind_tests"
GT_DIR = os.path.expanduser("~/fw01_work/game-truyen")

shutil.rmtree(SYSROOT, ignore_errors=True)
os.makedirs(SYSROOT)

PLANNER_VERSION_EXPECTED = "4"

# ---------------------------------------------------------------- helpers


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_root():
    """Fixture root = canonical governance + capability index, copied bytewise."""
    root = tempfile.mkdtemp(prefix="sb_", dir=SYSROOT)
    os.makedirs(os.path.join(root, "governance"))
    for name in ("development-control.json", "research-adoption-ledger.json",
                 "p2p-development-roadmap.json", "research-intake-ledger.json",
                 "intake-contract.json"):
        shutil.copy(os.path.join(REPO, "governance", name),
                    os.path.join(root, "governance", name))
    cap_dir = os.path.join(root, "docs", "p2p-development", "capability-ledger")
    os.makedirs(cap_dir)
    shutil.copy(os.path.join(REPO, "docs", "p2p-development", "capability-ledger",
                             "capability-index.json"),
                os.path.join(cap_dir, "capability-index.json"))
    return root


def run_planner(root):
    out = os.path.join(root, "plan_output.json")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(REPO, "scripts")
    r = subprocess.run([sys.executable, PLANNER, "--repo", root,
                        "--output", out], capture_output=True, text=True, env=env)
    if r.returncode != 0:
        return None, r.returncode, r.stderr[-1200:]
    with open(out) as f:
        return json.load(f), 0, ""


def gate(plan):
    return (plan or {}).get("ROADMAP_COVERAGE_GATE", {})


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}" if detail else f"[{status}] {name}")
    return ok


results = []

# ------------------------------------------------------ A: UNKNOWN classification

root = build_root()
il = os.path.join(root, "governance", "research-intake-ledger.json")
d = json.load(open(il))
d["intake_records"].append({"id": "RI-X1", "classification": "UNKNOWN",
                            "subject": "Unknown classification seam test"})
json.dump(d, open(il, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is True
      and any(x.get("reason") == "UNKNOWN_INTAKE_CLASSIFICATION"
              for x in g.get("gaps", []))
      and p.get("RECOMMENDED_NEXT_GOAL") is None)
results.append(check("A-UNKNOWN_INTAKE_CLASSIFICATION_BLOCKS", ok,
                     "gap=True, recommendation=null" if ok else f"RC={rc}, plan={json.dumps(g)[:120]}, err={err[:120]}"))

# --------------------------------------------------- B: invalid vocabulary value

root = build_root()
il = os.path.join(root, "governance", "research-intake-ledger.json")
d = json.load(open(il))
d["intake_records"].append({"id": "RI-X2", "classification": "MYSTERY",
                            "subject": "Invalid vocabulary seam test"})
json.dump(d, open(il, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is True
      and any(x.get("reason") == "UNKNOWN_INTAKE_CLASSIFICATION"
              for x in g.get("gaps", [])))
results.append(check("B-INVALID_VOCABULARY_BLOCKS", ok,
                     "gap=True" if ok else f"RC={rc}, err={err[:120]}"))

# ----------------------------------------------- C: missing classification field

root = build_root()
il = os.path.join(root, "governance", "research-intake-ledger.json")
d = json.load(open(il))
d["intake_records"].append({"id": "RI-X3", "subject": "Missing classification seam test"})
json.dump(d, open(il, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is True
      and any(x.get("reason") == "UNKNOWN_INTAKE_CLASSIFICATION"
              for x in g.get("gaps", [])))
results.append(check("C-MISSING_CLASSIFICATION_BLOCKS", ok,
                     "gap=True" if ok else f"RC={rc}, err={err[:120]}"))

# ----------------------------------------- D: ACCEPTED intake + UNKNOWN adoption

root = build_root()
il = os.path.join(root, "governance", "research-intake-ledger.json")
d = json.load(open(il))
d["intake_records"].append({"id": "RI-X4", "classification": "ACCEPTED",
                            "subject": "Material capability seam (UNKNOWN adoption)"})
json.dump(d, open(il, "w"), indent=2)
al = os.path.join(root, "governance", "research-adoption-ledger.json")
d = json.load(open(al))
d["records"].append({"research_id": "RA-EXT-X4", "source_name": "Material capability seam (UNKNOWN adoption)",
                     "source_type": "owner_accepted_proposal",
                     "canonical_capability_ids": [],
                     "status": "UNKNOWN", "intake_record": "RI-X4"})
json.dump(d, open(al, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is True
      and any(x.get("reason") == "ACCEPTED_INTAKE_ADOPTION_NOT_MATERIAL"
              for x in g.get("gaps", [])))
results.append(check("D-ACCEPTED_INTAKE_UNKNOWN_ADOPTION_BLOCKS", ok,
                     "gap=True" if ok else f"gaps={[x.get('reason') for x in g.get('gaps', [])]} err={err[:120]}"))

# ---------------------------------- E: ACCEPTED intake + DISCOVERED-only adoption

root = build_root()
il = os.path.join(root, "governance", "research-intake-ledger.json")
d = json.load(open(il))
d["intake_records"].append({"id": "RI-X5", "classification": "ACCEPTED",
                            "subject": "Material capability seam (DISCOVERED adoption)"})
json.dump(d, open(il, "w"), indent=2)
al = os.path.join(root, "governance", "research-adoption-ledger.json")
d = json.load(open(al))
d["records"].append({"research_id": "RA-EXT-X5", "source_name": "Material capability seam (DISCOVERED adoption)",
                     "source_type": "owner_accepted_proposal",
                     "canonical_capability_ids": [],
                     "status": "DISCOVERED", "intake_record": "RI-X5"})
json.dump(d, open(al, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is True
      and any(x.get("reason") == "ACCEPTED_INTAKE_ADOPTION_NOT_MATERIAL"
              for x in g.get("gaps", [])))
results.append(check("E-ACCEPTED_INTAKE_DISCOVERED_ONLY_BLOCKS", ok,
                     "gap=True" if ok else f"gaps={[x.get('reason') for x in g.get('gaps', [])]} err={err[:120]}"))

# ----------------------------------------------- F: ACCEPTED + PLANNED binding

root = build_root()
il = os.path.join(root, "governance", "research-intake-ledger.json")
d = json.load(open(il))
d["intake_records"].append({"id": "RI-X6", "classification": "ACCEPTED",
                            "subject": "Material capability seam (PLANNED adoption)"})
json.dump(d, open(il, "w"), indent=2)
al = os.path.join(root, "governance", "research-adoption-ledger.json")
d = json.load(open(al))
d["records"].append({"research_id": "RA-EXT-X6", "source_name": "Material capability seam (PLANNED adoption)",
                     "source_type": "owner_accepted_proposal",
                     "canonical_capability_ids": [],
                     "status": "PLANNED", "intake_record": "RI-X6"})
json.dump(d, open(al, "w"), indent=2)
road = os.path.join(root, "governance", "p2p-development-roadmap.json")
d = json.load(open(road))
for item in d["items"]:
    if item["roadmap_id"] == "RM-PRIORITY-CONTEXT":
        item.setdefault("source_research_ids", []).append("RA-EXT-X6")
json.dump(d, open(road, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is False
      and not any(x.get("reason") in (
          "ACCEPTED_INTAKE_WITHOUT_ADOPTION_RECORD",
          "ACCEPTED_INTAKE_ADOPTION_NOT_MATERIAL") for x in g.get("gaps", [])))
results.append(check("F-ACCEPTED_INTAKE_PLANNED_BINDING_PASSES", ok,
                     "gap=False" if ok else f"gaps={[x.get('reason') for x in g.get('gaps', [])]} err={err[:120]}"))

# ---------------------------------- G: fuzzy tokens WITHOUT explicit ID binding

root = build_root()
il = os.path.join(root, "governance", "research-intake-ledger.json")
d = json.load(open(il))
d["intake_records"].append({"id": "RI-X7", "classification": "ACCEPTED",
                            "subject": "Contextual Rule Intelligence New Capability"})
json.dump(d, open(il, "w"), indent=2)
al = os.path.join(root, "governance", "research-adoption-ledger.json")
d = json.load(open(al))
d["records"].append({"research_id": "RA-EXT-X7",
                     "source_name": "Contextual Rule Engine Historical Research",
                     "canonical_capability_ids": []})
json.dump(d, open(al, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is True
      and any(x.get("reason") == "ACCEPTED_INTAKE_WITHOUT_ADOPTION_RECORD"
              for x in g.get("gaps", []))
      and g.get("FUZZY_AUTHORITY_MATCHING") == "DISABLED")
results.append(check("G-FUZZY_TOKEN_OVERLAP_NEVER_BINDS", ok,
                     "gap=True, fuzzy authority DISABLED" if ok
                     else f"gaps={[x.get('reason') for x in g.get('gaps', [])]} err={err[:120]}"))

# -------------------------------------------- H: explicit ID binding passes

root = build_root()
il = os.path.join(root, "governance", "research-intake-ledger.json")
d = json.load(open(il))
d["intake_records"].append({"id": "RI-X8", "classification": "ACCEPTED",
                            "subject": "Contextual Rule Intelligence New Capability"})
json.dump(d, open(il, "w"), indent=2)
al = os.path.join(root, "governance", "research-adoption-ledger.json")
d = json.load(open(al))
d["records"].append({"research_id": "RA-EXT-X8",
                     "source_name": "Some unrelated research subject name",
                     "canonical_capability_ids": [],
                     "status": "PLANNED", "intake_record": "RI-X8"})
json.dump(d, open(al, "w"), indent=2)
road = os.path.join(root, "governance", "p2p-development-roadmap.json")
d = json.load(open(road))
for item in d["items"]:
    if item["roadmap_id"] == "RM-PRIORITY-CONTEXT":
        item.setdefault("source_research_ids", []).append("RA-EXT-X8")
json.dump(d, open(road, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is False
      and not any(x.get("reason") == "ACCEPTED_INTAKE_WITHOUT_ADOPTION_RECORD"
                  for x in g.get("gaps", []))
      and g.get("EXPLICIT_INTAKE_BINDINGS", 0) >= 1)
results.append(check("H-EXPLICIT_ID_BINDING_SATISFIES", ok,
                     "gap=False, explicit bindings>=1" if ok
                     else f"gaps={[x.get('reason') for x in g.get('gaps', [])]} err={err[:120]}"))

# --------------------------- I: OWNER_ACCEPTED same-family cap WITHOUT enumeration

root = build_root()
cap = os.path.join(root, "docs", "p2p-development", "capability-ledger",
                   "capability-index.json")
d = json.load(open(cap))
d["capabilities"].append({
    "id": "SEAM_X9", "capability_id": "SEAM_X9", "status": "PLANNED",
    "family": "CONTEXT_AND_KNOWLEDGE",
    "origin_type": "OWNER_ACCEPTED_PROPOSAL"})
json.dump(d, open(cap, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
fam_gap = [x for x in g.get("gaps", [])
           if x.get("reason") == "FUTURE_WORK_CAPABILITY_WITHOUT_ROADMAP_CONSIDERATION"
           and x.get("capability_id") == "SEAM_X9"]
ok = (rc == 0 and p is not None and bool(fam_gap))
results.append(check("I-SAME_FAMILY_ALIAS_NEVER_SATISFIES", ok,
                     "capability gap reported" if ok
                     else f"gaps={[x.get('capability_id') for x in g.get('gaps', [])]} err={err[:120]}"))

# -------------------------- J: cap ID in canonical_capability_ids passes

root = build_root()
cap = os.path.join(root, "docs", "p2p-development", "capability-ledger",
                   "capability-index.json")
d = json.load(open(cap))
d["capabilities"].append({
    "id": "SEAM_X10", "capability_id": "SEAM_X10", "status": "PLANNED",
    "family": "CACHE_AND_EFFICIENCY",
    "origin_type": "OWNER_ACCEPTED_PROPOSAL"})
json.dump(d, open(cap, "w"), indent=2)
road = os.path.join(root, "governance", "p2p-development-roadmap.json")
d = json.load(open(road))
for item in d["items"]:
    if item["roadmap_id"] == "RM-PRIORITY-CONTEXT":
        item.setdefault("canonical_capability_ids", []).append("SEAM_X10")
json.dump(d, open(road, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
gap = [x for x in g.get("gaps", []) if x.get("capability_id") == "SEAM_X10"]
ok = (rc == 0 and p is not None and not gap
      and "SEAM_X10" in (g.get("EXPLICITLY_ROADMAPPED_CAPABILITIES") or []))
results.append(check("J-CAP_ID_IN_CANONICAL_LIST_SATISFIES", ok,
                     "no capability gap" if ok
                     else f"gaps={[x.get('capability_id') for x in g.get('gaps', [])]} err={err[:120]}"))

# ------------------------------ K: composition entry satisfies enumeration

root = build_root()
cap = os.path.join(root, "docs", "p2p-development", "capability-ledger",
                   "capability-index.json")
d = json.load(open(cap))
d["capabilities"].append({
    "id": "SEAM_X11", "capability_id": "SEAM_X11", "status": "PARTIAL",
    "family": "SECURITY_ISOLATION",
    "origin_type": "OWNER_ACCEPTED_PROPOSAL"})
json.dump(d, open(cap, "w"), indent=2)
road = os.path.join(root, "governance", "p2p-development-roadmap.json")
d = json.load(open(road))
for item in d["items"]:
    if item["roadmap_id"] == "RM-PRIORITY-CONTEXT":
        item.setdefault("composition_entries", []).append(
            {"capability": "SEAM_X11", "research_record": "RA-EXT-X11",
             "intake_record": "RI-X11", "mode": "B_explicit_composition",
             "note": "Test K explicit composition"})
json.dump(d, open(road, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
gap = [x for x in g.get("gaps", []) if x.get("capability_id") == "SEAM_X11"]
ok = (rc == 0 and p is not None and not gap
      and "SEAM_X11" in (g.get("EXPLICITLY_ROADMAPPED_CAPABILITIES") or []))
results.append(check("K-COMPOSITION_ENTRY_SATISFIES_ENUMERATION", ok,
                     "no capability gap" if ok
                     else f"gaps={[x.get('capability_id') for x in g.get('gaps', [])]} err={err[:120]}"))

# ------------------------------ L: explicit DEFER with reason passes

root = build_root()
cap = os.path.join(root, "docs", "p2p-development", "capability-ledger",
                   "capability-index.json")
d = json.load(open(cap))
d["capabilities"].append({
    "id": "SEAM_X12", "capability_id": "SEAM_X12", "status": "PLANNED",
    "family": "UNKNOWN_FAMILY_X",
    "origin_type": "OWNER_ACCEPTED_PROPOSAL",
    "roadmap_relation": "defer: Owner defers this direction until lifecycle goal completes"})
json.dump(d, open(cap, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
gap = [x for x in g.get("gaps", []) if x.get("capability_id") == "SEAM_X12"]
ok = (rc == 0 and p is not None and not gap)
results.append(check("L-EXPLICIT_DEFER_WITH_REASON_SATISFIES", ok,
                     "no capability gap" if ok
                     else f"gaps={[x.get('capability_id') for x in g.get('gaps', [])]} err={err[:120]}"))

# ----------------------------- M: material cap with UNKNOWN status blocks

root = build_root()
cap = os.path.join(root, "docs", "p2p-development", "capability-ledger",
                   "capability-index.json")
d = json.load(open(cap))
d["capabilities"].append({
    "id": "SEAM_X13", "capability_id": "SEAM_X13", "status": "",
    "family": "CONTEXT_AND_KNOWLEDGE",
    "origin_type": "OWNER_ACCEPTED_PROPOSAL"})
json.dump(d, open(cap, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
gap = [x for x in g.get("gaps", [])
       if x.get("reason") == "CAPABILITY_STATUS_UNKNOWN_MATERIAL"
       and x.get("capability_id") == "SEAM_X13"]
ok = (rc == 0 and p is not None and bool(gap))
results.append(check("M-UNKNOWN_CAPABILITY_STATUS_BLOCKS", ok,
                     "status-unknown gap" if ok
                     else f"gaps={[x.get('reason') for x in g.get('gaps', [])]} err={err[:120]}"))

# ----------------------------- N: forward dangling research ref blocks

root = build_root()
road = os.path.join(root, "governance", "p2p-development-roadmap.json")
d = json.load(open(road))
for item in d["items"]:
    if item["roadmap_id"] == "RM-PRIORITY-CONTEXT":
        item.setdefault("source_research_ids", []).append("RA-EXT-NEVER-EXISTS")
json.dump(d, open(road, "w"), indent=2)
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is True
      and any(x.get("reason") == "SOURCE_RESEARCH_ID_MISSING_FROM_LEDGER"
              for x in g.get("gaps", [])))
results.append(check("N-FORWARD_DANGLING_RESEARCH_REF_BLOCKS", ok,
                     "gap=True" if ok
                     else f"gaps={[x.get('reason') for x in g.get('gaps', [])]} err={err[:120]}"))

# ------------------------- O: full canonical truth restores planning complete

root = build_root()
p, rc, err = run_planner(root)
g = gate(p)
ok = (rc == 0 and p is not None and g.get("ROADMAP_COVERAGE_GAP") is False
      and p.get("PLAN_COMPLETE") is True
      and p.get("RECOMMENDED_NEXT_GOAL") is not None
      and g.get("FUZZY_MATCHES_USED_FOR_AUTHORITY") == 0
      and g.get("INTAKE_UNKNOWN_RECORDS") == []
      and g.get("UNKNOWN_ADOPTION_RECORDS") == []
      and str(p.get("version")) == PLANNER_VERSION_EXPECTED)
results.append(check("O-CANONICAL_TRUTH_RESTORED", ok,
                     "GAP=false, COMPLETE=true, rec=%s" % (
                         p.get("RECOMMENDED_NEXT_GOAL") if p else None) if ok
                     else f"gaps={[x.get('reason') for x in g.get('gaps', [])]} err={err[:120]}"))

# -------------------------------------------- P: deterministic re-run identity

root = build_root()
p1, _, _ = run_planner(root)
p2, _, _ = run_planner(root)
stripped1 = json.dumps(p1, sort_keys=True)
stripped2 = json.dumps(p2, sort_keys=True)
# timestamps differ by design; compare structural determinism via goal + gaps + counters
ok = (p1 is not None and p2 is not None
      and p1.get("RECOMMENDED_NEXT_GOAL") == p2.get("RECOMMENDED_NEXT_GOAL")
      and gate(p1).get("gaps") == gate(p2).get("gaps")
      and gate(p1).get("FUZZY_MATCHES_USED_FOR_AUTHORITY")
      == gate(p2).get("FUZZY_MATCHES_USED_FOR_AUTHORITY"))
results.append(check("P-DETERMINISTIC_RE_RUN_IDENTITY", ok))

# ------------------------ Q: planner never mutates any governance input files

root = build_root()
before = {}
for dirpath, _, files in os.walk(root):
    for fn in files:
        full = os.path.join(dirpath, fn)
        before[full] = sha256(full)
run_planner(root)
after = {f: sha256(f) for f in before}
mutated = [f for f in before if after.get(f) != before[f]]
ok = (len(before) == len(after) and not mutated)
results.append(check("Q-ZERO_INPUT_MUTATION", ok,
                     "%d files, 0 mutated" % len(before) if ok
                     else "mutated: %s" % mutated[:5]))

# ---- R: planner never touches the authoritative Game Truyện working tree

gt_before = {}
gt_watch = []
if os.path.isdir(GT_DIR):
    for rel in ("README.md",):
        full = os.path.join(GT_DIR, rel)
        if os.path.exists(full):
            gt_before[full] = sha256(full)
            gt_watch.append(full)
root = build_root()
run_planner(root)
gt_after = {f: sha256(f) for f in gt_before}
changed = [f for f in gt_watch if gt_after.get(f) != gt_before.get(f)]
ok = (not os.path.isdir(GT_DIR)) or (len(gt_watch) == 0) or not changed
results.append(check("R-ZERO_PROJECT_MUTATION",
                     ok, "Game Truyện files unchanged" if ok else "changed: %s" % changed[:5]))

# ---------------------------------------------------------------- summary
n_pass = sum(1 for r in results if r)
print("\n%s / %d PASS" % (n_pass, len(results)))
sys.exit(0 if n_pass == len(results) else 1)
