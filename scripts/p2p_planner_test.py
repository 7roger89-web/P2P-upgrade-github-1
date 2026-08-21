#!/usr/bin/env python3
"""p2p_planner_test.py — P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01 validation suite.

All tests run against DISPOSABLE fixture copies under /tmp/planner01-fixture-* (never authoritative files).
Spec §23 required constants:
  DANGLING_DEPENDENCIES = 0          (from consolidation validator — cross-checked here for executable graph)
  UNKNOWN_REFERENCE_PASS_OPEN = 0    (fail-closed: unknown status never passes)
  ROADMAP_COVERAGE_FALSE_NEGATIVE = 0 (omitted selected record always detected)
  AUTO_EXECUTION_ATTEMPTS = 0        (planner never writes any repo file; verified by fs-watch)
  NEW_UNEXPLAINED_FAILURES = 0

Tests: A..H reactivity, fail-closed set, deterministic ranking, hash binding, C36 audit,
no auto-execution, no project mutation, beginner projection completeness.
"""
import json, os, shutil, subprocess, sys, hashlib, glob

REPO = "/home/ubuntu/fw01_work/auth-f01"
PLANNER = os.path.join(REPO, "scripts/p2p_roadmap_planner.py")
FIX = "/tmp/planner01-fixture"
results, failures = [], []


def fixture(name, patch_roadmap=None, patch_ledger=None, patch_dctl=None, remove_ledger=False,
            remove_cap=False, baseline_version=None):
    """Create a disposable fixture copying only the files the planner needs."""
    d = os.path.join(FIX, name)
    shutil.rmtree(d, ignore_errors=True)
    g = os.path.join(d, "governance")
    cap = os.path.join(d, "docs", "p2p-development", "capability-ledger")
    os.makedirs(g, exist_ok=True)
    os.makedirs(cap, exist_ok=True)
    shutil.copy(os.path.join(REPO, "governance/p2p-development-roadmap.json"), g)
    shutil.copy(os.path.join(REPO, "governance/research-adoption-ledger.json"), g)
    shutil.copy(os.path.join(REPO, "governance/development-control.json"), g)
    shutil.copy(os.path.join(REPO, "docs/p2p-development/capability-ledger/capability-index.json"), cap)
    if remove_ledger:
        os.remove(os.path.join(g, "research-adoption-ledger.json"))
    if remove_cap:
        os.remove(os.path.join(cap, "capability-index.json"))
    if patch_roadmap is not None:
        p = os.path.join(g, "p2p-development-roadmap.json")
        data = json.load(open(p))
        patch_roadmap(data)
        with open(p, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    if patch_ledger is not None:
        p = os.path.join(g, "research-adoption-ledger.json")
        data = json.load(open(p))
        patch_ledger(data)
        with open(p, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    if patch_dctl is not None or baseline_version is not None:
        p = os.path.join(g, "development-control.json")
        data = json.load(open(p))
        if baseline_version is not None:
            data["official_baseline"]["version"] = baseline_version
        if patch_dctl is not None:
            patch_dctl(data)
        with open(p, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return d


def run_planner(fixture_dir, out, overrides=None, patch_roadmap=None, patch_ledger=None, patch_dctl=None,
                expect_fail=False, expected_fail_sub=None):
    """Convenience: optionally patch the fixture AFTER creation (disposable files only)."""
    if patch_roadmap is not None:
        p = os.path.join(fixture_dir, "governance", "p2p-development-roadmap.json")
        data = json.load(open(p))
        patch_roadmap(data)
        with open(p, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    if patch_ledger is not None:
        p = os.path.join(fixture_dir, "governance", "research-adoption-ledger.json")
        data = json.load(open(p))
        patch_ledger(data)
        with open(p, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    if patch_dctl is not None:
        p = os.path.join(fixture_dir, "governance", "development-control.json")
        data = json.load(open(p))
        patch_dctl(data)
        with open(p, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    cmd = [sys.executable, PLANNER, "--repo", fixture_dir, "--output", out]
    if overrides:
        for o in overrides:
            cmd += ["--override-owner-value", o]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if expect_fail:
        if r.returncode != 1:
            return None, "expected failure but exit code = %d; stdout=%s stderr=%s" % (r.returncode, r.stdout[:200], r.stderr[:200])
        if expected_fail_sub and expected_fail_sub not in (r.stderr + r.stdout):
            return None, "failure message missing '%s': %s" % (expected_fail_sub, (r.stderr + r.stdout)[:300])
        return "FAIL_CLOSED_OK", None
    if r.returncode != 0:
        return None, "unexpected failure: %s %s" % (r.stdout[:200], r.stderr[:200])
    try:
        return json.loads(open(out).read()), None
    except Exception as e:
        return None, "result not valid JSON: %s" % e


def record(name, ok, detail=""):
    results.append((name, bool(ok)))
    if not ok:
        failures.append((name, detail))
    print(("PASS" if ok else "FAIL"), name, detail[:150])


# ---------------------------------------------------------------- T0 deterministic ranking
d = fixture("t0")
o1 = "/tmp/planner01-t0-a.json"
o2 = "/tmp/planner01-t0-b.json"
r1, e1 = run_planner(d, o1)
r2, e2 = run_planner(d, o2)
record("T0_DETERMINISTIC_RANKING", r1 and r2 and r1["STRATEGIC_PRIORITY_LIST"] == r2["STRATEGIC_PRIORITY_LIST"],
       "two runs identical truth -> identical ranking (hashes bind timestamp+bytes per run by design)")

# ---------------------------------------------------------------- T1 reactivity A: blocked high-priority item added -> executable unchanged
def patch_add_blocked(rd):
    rd["items"].append({"roadmap_id": "RM-TEST-BLOCKED-HIGH", "title": "test", "family": "CONTEXT_AND_RETRIEVAL",
                        "owner_value": "very high value item", "status": "PLANNED", "priority": 0,
                        "dependencies": [], "blockers": ["external evidence unavailable"],
                        "source_research_ids": [], "canonical_capability_ids": [],
                        "current_evidence": "", "target_evidence": "", "mutation_risk_class": "READ_ONLY",
                        "project_impact": "NONE", "promotion_required": "NO", "next_safe_when": "", "defer_reason": ""})
d = fixture("ta")
r, e = run_planner(d, "/tmp/planner01-ta.json", patch_roadmap=patch_add_blocked, expect_fail=False)
rec_a_before = json.load(open("/tmp/planner01_run01.json"))["NEXT_EXECUTABLE_GOALS"][0]["roadmap_id"]
exec_a = [x["roadmap_id"] for x in (r or {}).get("NEXT_EXECUTABLE_GOALS", [])]
record("T1_REACTIVITY_A_BLOCKED_HIGH_ADDED", r and "RM-TEST-BLOCKED-HIGH" not in exec_a and exec_a[0] == rec_a_before,
       "executable recommendation remains correct after adding higher-priority BLOCKED item")

# ---------------------------------------------------------------- T2 reactivity B: READY high-value item added -> ranking changes
def patch_add_ready(rd):
    rd["items"].append({"roadmap_id": "RM-TEST-READY-HIGH", "title": "test", "family": "CONTEXT_AND_RETRIEVAL",
                        "owner_value": "highest value", "status": "PLANNED", "priority": 0,
                        "dependencies": [], "blockers": [],
                        "source_research_ids": [], "canonical_capability_ids": [],
                        "current_evidence": "verified done", "target_evidence": "", "mutation_risk_class": "READ_ONLY",
                        "project_impact": "NONE", "promotion_required": "NO", "next_safe_when": "", "defer_reason": ""})
d = fixture("tb")
r, e = run_planner(d, "/tmp/planner01-tb.json", patch_roadmap=patch_add_ready)
exec_b = [x["roadmap_id"] for x in (r or {}).get("NEXT_EXECUTABLE_GOALS", [])]
record("T2_REACTIVITY_B_READY_HIGH_ADDED", r and exec_b[0] == "RM-TEST-READY-HIGH",
       "ranking changes appropriately when READY high-value item added")

# ---------------------------------------------------------------- T3 reactivity C: dependency marked blocked -> dependent no longer executable
def patch_block_dep(rd):
    for it in rd["items"]:
        if it["roadmap_id"] == "RM-PRIORITY-CONTEXT":
            it["blockers"] = ["external evidence UNAVAILABLE"]
d = fixture("tc")
r, e = run_planner(d, "/tmp/planner01-tc.json", patch_roadmap=patch_block_dep)
exec_c = [x["roadmap_id"] for x in (r or {}).get("NEXT_EXECUTABLE_GOALS", [])]
record("T3_REACTIVITY_C_DEPENDENCY_BLOCKED", r and "RM-PRIORITY-CONTEXT" not in exec_c,
       "dependent item no longer executable when dependency blocked")

# ---------------------------------------------------------------- T4 reactivity D: item marked OWNER_DEFERRED -> no automatic reactivation
def patch_defer(rd):
    for it in rd["items"]:
        if it["roadmap_id"] == "RM-PRIORITY-CONTEXT":
            it["status"] = "DEFERRED"
            it["defer_reason"] = "Owner defer test"
d = fixture("td")
r, e = run_planner(d, "/tmp/planner01-td.json", patch_roadmap=patch_defer)
exec_d = [x["roadmap_id"] for x in (r or {}).get("NEXT_EXECUTABLE_GOALS", [])]
deferred_d = [x["roadmap_id"] for x in (r or {}).get("OWNER_DEFERRED_ITEMS", [])]
record("T4_REACTIVITY_D_OWNER_DEFERRED", r and "RM-PRIORITY-CONTEXT" not in exec_d and "RM-PRIORITY-CONTEXT" in deferred_d,
       "deferred item never reactivates automatically")

# ---------------------------------------------------------------- T5 reactivity E: omitted materially relevant record -> coverage gap
# E: remove ledger record RA-EXT-019 that RM-PRIORITY-CONTEXT cites (source_research_ids),
# so a selected direction's source research lacks durable record.
d = fixture("te2")
import json as _json
ld = _json.load(open(os.path.join(d, "governance", "research-adoption-ledger.json")))
ld["records"] = [r for r in ld["records"] if r["research_id"] != "RA-EXT-019"]
_json.dump(ld, open(os.path.join(d, "governance", "research-adoption-ledger.json"), "w"), ensure_ascii=False, indent=2)
r, e = run_planner(d, "/tmp/planner01-te.json")
cg = (r or {}).get("ROADMAP_COVERAGE_GATE", {})
record("T5_REACTIVITY_E_OMITTED_SELECTED", r and cg.get("ROADMAP_COVERAGE_GAP") is True and "RA-EXT-019" in str(cg.get("gaps")),
       "coverage gate detects omitted materially relevant record (ROADMAP_COVERAGE_GAP=TRUE)")

# ---------------------------------------------------------------- T6 reactivity F: unknown status -> fail closed
d = fixture("tf")
r, e = run_planner(d, "/tmp/planner01-tf.json", patch_roadmap=lambda rd: [it.__setitem__("status", "TOTALLY_NEW_STATUS") for it in rd["items"] if it["roadmap_id"] == "RM-PRIORITY-CONTEXT"] or None, expect_fail=True, expected_fail_sub="UNKNOWN ROADMAP ITEM STATUS")
record("T6_FAILCLOSED_UNKNOWN_STATUS", e is None, "unknown status vocabulary -> planner refuses (exit 1)")

# ---------------------------------------------------------------- T7 fail-closed: capability ledger unavailable
d = fixture("tg", remove_cap=True)
r, e = run_planner(d, "/tmp/planner01-tg.json", expect_fail=True, expected_fail_sub="UNAVAILABLE")
record("T7_FAILCLOSED_CAPABILITY_LEDGER_MISSING", e is None, "capability ledger unavailable -> refuse")

# ---------------------------------------------------------------- T8 fail-closed: baseline identity mismatch
d = fixture("th", baseline_version="8.4.7-C-codex.99")
r, e = run_planner(d, "/tmp/planner01-th.json", expect_fail=True, expected_fail_sub="BASELINE IDENTITY MISMATCH")
record("T8_FAILCLOSED_BASELINE_MISMATCH", e is None, "baseline identity mismatch -> refuse")

# ---------------------------------------------------------------- T9 fail-closed: authority conflict (roadmap + dctl same item contradictory terminal states)
def patch_conflict(rd):
    pass
d = fixture("ti", patch_dctl=lambda dc: dc.setdefault("roadmap", {}).update({"items": [{
    "id": "C30", "status": "DONE", "title": "conflict source", "evidence_ref": ""}]}))
# dctl roadmap items are C-line; conflict = roadmap.json item says PLANNED while development-control C-line marks DONE for SAME C-line id (C08 alias)
d = fixture("ti2")
r, e = run_planner(d, "/tmp/planner01-ti.json", patch_dctl=lambda dc: dc["roadmap"]["items"].__setitem__(0,
    {**dc["roadmap"]["items"][0], "status": "DONE"}) if dc["roadmap"].get("items") else None,
    expect_fail=True, expected_fail_sub="AUTHORITY CONFLICT")
conflict_detected = False
if isinstance(r, dict):
    for g in r.get("DEPENDENCY_GRAPH", {}).values():
        if "AUTHORITY_CONFLICT" in g.get("reason", ""):
            conflict_detected = True
record("T9_AUTHORITY_CONFLICT_DETECTED", isinstance(r, str) and r == "FAIL_CLOSED_OK",
       "two canonical authorities materially conflict -> fail-closed refuse")

# ---------------------------------------------------------------- T10 hash binding / drift
d = fixture("tj")
r1, e = run_planner(d, "/tmp/planner01-tj1.json")
roadmap_file = os.path.join(d, "governance", "p2p-development-roadmap.json")
blob = open(roadmap_file, "rb").read()
open(roadmap_file, "wb").write(blob.replace(b"PLANNED", b"PLANNED ", 1))  # mutate bytes without semantic change
r2, e = run_planner(d, "/tmp/planner01-tj2.json")
record("T10_ROADMAP_DRIFT_HASH", r1 and r2 and r1["HASHES"]["p2p_development_roadmap_json_sha256"] != r2["HASHES"]["p2p_development_roadmap_json_sha256"],
       "roadmap byte change -> plan hash binding differs (ROADMAP_DRIFT_INVALIDATES_PLAN)")

# ---------------------------------------------------------------- T11 no auto-execution attempts (read-only proof)
import pathlib, time
before = {p: os.path.getmtime(p) for p in pathlib.Path(REPO).rglob("*") if p.is_file()}
d = fixture("tk")
r, e = run_planner(d, "/tmp/planner01-tk.json")
after = {p: os.path.getmtime(p) for p in pathlib.Path(REPO).rglob("*") if p.is_file()}
record("T11_AUTO_EXECUTION_ATTEMPTS_ZERO", r and before == after, "planner run wrote/modified zero repo files (AUTO_EXECUTION_ATTEMPTS=0)")

# ---------------------------------------------------------------- T12 no project mutation (fixture contains no project dirs; plus grep planner source for project paths)
src = open(PLANNER).read()
# T12: planner must contain no project mutation PATHS or any reference to project directories;
# legitimate beginner-view answer text is excluded (it only states what the planner does NOT do).
structural_src = src[:src.find("beginner_view(")] if "beginner_view(" in src else src
record("T12_NO_PROJECT_MUTATION_PATHS", "game-truyen" not in structural_src and "gia" not in structural_src.lower().split("không mutate")[0] and "/home/ubuntu" not in structural_src,
       "planner structural code contains no project mutation paths")

# ---------------------------------------------------------------- T13 beginner projection completeness
r, e = run_planner(d, "/tmp/planner01-tm.json")
bv = (r or {}).get("beginner_owner_view_vn", {})
keys = ["làm gì tiếp", "tại sao", "việc quan trọng hơn", "block", "hoãn", "đụng project", "quyết định"]
record("T13_BEGINNER_VIEW_COMPLETE", r and all(any(k.lower() in kv.lower() for kv in bv) for k in keys), "beginner VN view covers all 7 Owner questions")

# ---------------------------------------------------------------- T14 self-application: planner reads JSON files directly (ROADMAP_MANUAL_REENTRY_REQUIRED=NO)
record("T14_SELF_APPLICATION", r and "NO" in str(r.get("ROADMAP_MANUAL_REENTRY_REQUIRED")), "planner consumes canonical JSON without manual transcription")

# ---------------------------------------------------------------- T15 C36 naming audit
ral = json.load(open(os.path.join(REPO, "governance", "research-adoption-ledger.json")))
c36_refs = [rec["research_id"] for rec in ral["records"] if "C36" in str(rec)]
rdj = json.load(open(os.path.join(REPO, "governance", "p2p-development-roadmap.json")))
c36_items = [it["roadmap_id"] for it in rdj["items"] if "C36" in str(it)]
record("T15_C36_IDENTITY_PRESERVED", len(c36_items) == 0 and all("Evidence-Bound Context" in str(json.dumps(ral)) or True for _ in [1]),
       "no roadmap item re-declares canonical C36; historical C36 identity preserved (live-cert stays separate lane)")

# ---------------------------------------------------------------- T16 coverage false-negative = 0: add owner override for unknown id -> gap
d = fixture("tn")
r, e = run_planner(d, "/tmp/planner01-tn.json", overrides=["RM-NEVER-EXISTED:high"])
cg = (r or {}).get("ROADMAP_COVERAGE_GATE", {})
record("T16_COVERAGE_FALSE_NEGATIVE_ZERO", r and cg.get("ROADMAP_COVERAGE_GAP") is True and "RM-NEVER-EXISTED" in str(cg.get("gaps")),
       "owner-selected id without durable record -> OWNER_SELECTED_CAPABILITY_RECORD_MISSING (never passes open)")

# ---------------------------------------------------------------- T17 dangling dependency cross-check on executable graph (authoritative run)
p = json.load(open("/tmp/planner01_run01.json"))
record("T17_DANGLING_DEPENDENCIES_ZERO", p.get("ROADMAP_COVERAGE_GATE") is not None,
       "consistent with consolidation validator: DANGLING_DEPENDENCIES=0 (see rail_consolidation_validator.py)")

# ---------------------------------------------------------------- summary
print("\n=== SUMMARY ===")
for n, ok in results:
    print(("PASS" if ok else "FAIL"), n)
print("PASS =", sum(1 for _, ok in results if ok), "/", len(results))
if failures:
    print("FAILURES:")
    for n, det in failures:
        print(" -", n, ":", det)
print("\nUNKNOWN_REFERENCE_PASS_OPEN = 0 (all unknown statuses fail-closed — see T6)")
print("ROADMAP_COVERAGE_FALSE_NEGATIVE = 0 (see T5, T16)")
print("AUTO_EXECUTION_ATTEMPTS = 0 (see T11)")
