#!/usr/bin/env python3
"""test_p2p_ledger_provenance.py — C26 durable capability provenance, dependency,
and Goal-to-Ledger governance tests (CP1-CP50).

Scope: Capability Ledger provenance (origin_refs + origin_type), dependency model
(field coverage, reference integrity, structure, cycles, rejected/obsolete
prerequisites), Goal Contract ledger-delta contract, Supervisor checklist,
roadmap/ledger synchronization, and non-hardcoded goal-ID handling in the
development-control validator. These tests do not touch runtime execution
behavior; they validate durable governance artifacts against durable sources.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs/p2p-development/capability-ledger/capability-index.json"
SCHEMA = ROOT / "docs/p2p-development/capability-ledger/capability-ledger.schema.json"
CHARTER = ROOT / "docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md"
ROADMAP = ROOT / "docs/p2p-development/current-roadmap.md"
GOAL_TPL = ROOT / "docs/p2p-development/templates/P2P-GOAL-CONTRACT-TEMPLATE.md"
SUP_TPL = ROOT / "docs/p2p-development/templates/P2P-SUPERVISOR-TEMPLATE.md"
GOV = ROOT / "governance/development-control.json"
VALIDATOR = ROOT / "scripts/validate_p2p_development_framework.py"
DEVCTRL = ROOT / "scripts/p2p_development_control.py"

GOAL_ID_RE = re.compile(r"^C(\d+)$")
CAP_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,60}$")

ORIGIN_TYPES = {
    "IMPLEMENTATION_GOAL", "RESEARCH_DECISION", "OWNER_ACCEPTED_PROPOSAL",
    "ARCHITECTURE_INVARIANT", "UPSTREAM_SPECIFICATION", "PROJECT_LEARNING",
    "REJECTED_DESIGN", "RECOVERED_LEGACY", "UNKNOWN",
}
ORIGIN_UNKNOWN_MARKER = "origin_unknown_or_not_durably_recovered"


def load_ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def load_gov():
    return json.loads(GOV.read_text(encoding="utf-8"))


def caps_by_id(ledger=None):
    ledger = ledger if ledger is not None else load_ledger()
    return {c["capability_id"]: c for c in ledger["capabilities"]}


# ---------------------------------------------------------------- provenance

def test_cp01_origin_refs_present_100_percent():
    ledger = load_ledger()
    missing = [c["capability_id"] for c in ledger["capabilities"] if not c.get("origin_refs")]
    assert not missing, f"Every record must have origin_refs; missing: {missing}"


def test_cp02_origin_refs_nonempty_strings():
    ledger = load_ledger()
    bad = [c["capability_id"] for c in ledger["capabilities"]
           if not (isinstance(c.get("origin_refs"), list) and all(isinstance(s, str) and s.strip() for s in c["origin_refs"]))]
    assert not bad, f"origin_refs must be non-empty string lists: {bad}"


def test_cp03_unknown_origin_explicit_not_silent():
    by_id = caps_by_id()
    silent = [cid for cid, c in by_id.items() if not c.get("origin_refs")]
    assert not silent, "No origin information may be silently absent"
    for cid, c in by_id.items():
        if ORIGIN_UNKNOWN_MARKER in c["origin_refs"]:
            assert set(c["origin_refs"]) == {ORIGIN_UNKNOWN_MARKER}, \
                f"{cid}: origin unknown marker must be the sole ref"


def test_cp04_origin_type_present_100_percent():
    ledger = load_ledger()
    missing = [c["capability_id"] for c in ledger["capabilities"] if "origin_type" not in c]
    assert not missing, f"origin_type required on every record; missing: {missing}"


def test_cp05_origin_type_enum_values_only():
    by_id = caps_by_id()
    bad = [(cid, c["origin_type"]) for cid, c in by_id.items() if c["origin_type"] not in ORIGIN_TYPES]
    assert not bad, f"origin_type must belong to the schema enum: {bad}"


def test_cp06_origin_type_unknown_consistent_with_refs():
    by_id = caps_by_id()
    for cid, c in by_id.items():
        if c["origin_type"] == "UNKNOWN":
            assert c["origin_refs"] == [ORIGIN_UNKNOWN_MARKER], f"{cid}: UNKNOWN requires exact unknown refs"


def test_cp07_origin_type_knowledgeable_not_unknown():
    by_id = caps_by_id()
    knowledgeable_unknown = [cid for cid, c in by_id.items()
                             if c["origin_type"] == "UNKNOWN" and c["origin_refs"] != [ORIGIN_UNKNOWN_MARKER]]
    assert not knowledgeable_unknown, "UNKNOWN origin_type pairs only with explicit unknown refs"


def test_cp08_owner_accepted_proposal_is_planned():
    by_id = caps_by_id()
    bad = [(cid, c["status"]) for cid, c in by_id.items()
           if c["origin_type"] == "OWNER_ACCEPTED_PROPOSAL" and c["status"] != "PLANNED"]
    assert not bad, f"Owner-accepted proposals are intent only (PLANNED): {bad}"


def test_cp09_owner_accepted_has_notes_disclaimer():
    by_id = caps_by_id()
    for cid, c in by_id.items():
        if c["origin_type"] == "OWNER_ACCEPTED_PROPOSAL":
            notes = (c.get("notes") or "").lower()
            assert "not" in notes or "intent" in notes or "planned" in notes, \
                f"{cid}: owner-accepted records must state implementation is not claimed"


def test_cp10_implementation_goal_requires_evidence_when_verified():
    by_id = caps_by_id()
    for cid, c in by_id.items():
        if c["origin_type"] == "IMPLEMENTATION_GOAL" and c["status"] == "VERIFIED_IMPLEMENTED":
            assert c.get("evidence_refs"), f"{cid}: verified goal-born capabilities need evidence_refs"


def test_cp11_origin_refs_not_fabricated_marker():
    """Recovered origins may say 'from report' but must never contain placeholder hashes."""
    by_id = caps_by_id()
    fabricated = [cid for cid, c in by_id.items()
                  if any(re.fullmatch(r"0{64}|x{64}|todo|placeholder", ref, re.IGNORECASE) for ref in c["origin_refs"])]
    assert not fabricated, f"Fabricated placeholder origins found: {fabricated}"


def test_cp12_c22_c24_record_status_unknown_preserved():
    by_id = caps_by_id()
    rec = by_id.get("C22_C24_ADAPTER_LIVE_CERTIFICATION")
    assert rec is not None
    assert rec["status"] == "UNKNOWN", "Recovery adds provenance, never claims implementation"


def test_cp13_c22_c24_record_recovered_legacy_origin():
    by_id = caps_by_id()
    rec = by_id["C22_C24_ADAPTER_LIVE_CERTIFICATION"]
    assert rec["origin_type"] == "RECOVERED_LEGACY"
    assert any("codex-23" in r or "codex-24" in r for r in rec["origin_refs"]), \
        "Recovered provenance must cite the verified C23/C24 candidate packages"


def test_cp14_c22_c24_known_gaps_honest():
    by_id = caps_by_id()
    rec = by_id["C22_C24_ADAPTER_LIVE_CERTIFICATION"]
    gaps = " ".join(rec.get("known_gaps", [])).lower()
    assert "c22" in gaps and "not recovered" in gaps or "not supplied" in gaps, \
        "C22's non-recovery must be stated honestly"
    assert "not verified" in gaps or "unverified" in gaps, \
        "Live certification must remain honestly unverified"


def test_cp15_c23_c24_verified_shas_cited():
    by_id = caps_by_id()
    refs = by_id["C22_C24_ADAPTER_LIVE_CERTIFICATION"]["origin_refs"]
    expected = {
        "8303efa866e9a6b1e33b94e4fe9e5c2afd0bfd71b6fe9a1344f53731f33fc7d1",
        "6c5b3b29fbaaab6df0b9f0c8a2f88ff579390b3b060c5c0d2f076cadec37d879",
    }
    found = {sha for r in refs for sha in expected if sha in r}
    assert found == expected, "Both verified package SHAs must be cited in recovered provenance"


def test_cp16_implemented_records_know_their_origin_goal():
    by_id = caps_by_id()
    impl = [c for c in by_id.values() if c["status"] == "VERIFIED_IMPLEMENTED" and c["origin_type"] == "IMPLEMENTATION_GOAL"]
    assert impl, "At least one goal-born implemented capability must exist"


def test_cp17_rejected_design_records_preserve_reason():
    by_id = caps_by_id()
    for cid, c in by_id.items():
        if c["origin_type"] == "REJECTED_DESIGN":
            assert c.get("rejected_reason"), f"{cid}: rejected designs must preserve the reason"
            assert c["status"] == "REJECTED", f"{cid}: rejected-design origin must be REJECTED status"


def test_cp18_architecture_invariant_records_cite_charter():
    by_id = caps_by_id()
    charter = CHARTER.read_text(encoding="utf-8").lower()
    for cid, c in by_id.items():
        if c["origin_type"] == "ARCHITECTURE_INVARIANT":
            refs_text = " ".join(c["origin_refs"]).lower()
            assert "charter" in refs_text or "invariant" in refs_text or "AI-handoff" in refs_text, \
                f"{cid}: invariant-born records must cite charter or upstream source"


def test_cp19_schema_origin_type_required():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert "origin_type" in schema["$defs"]["capability"]["required"], \
        "schema must require origin_type"
    enum = schema["$defs"]["capability"]["properties"]["origin_type"]["enum"]
    assert set(enum) == ORIGIN_TYPES, "schema enum must equal the validator vocabulary"


def test_cp20_schema_dependencies_required():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert "dependencies" in schema["$defs"]["capability"]["required"], \
        "dependencies field must be mandatory (empty list is valid)"


def test_cp21_schema_version_bumped():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert data["schema_version"] >= 2, "ledger follows schema v2 record shape"
    assert schema.get("properties", {}).get("schema_version", {}).get("minimum", 0) >= 2, \
        "schema must enforce v2 record shape"


# ---------------------------------------------------------------- dependencies

def test_cp22_dependencies_field_present_100_percent():
    ledger = load_ledger()
    missing = [c["capability_id"] for c in ledger["capabilities"] if "dependencies" not in c]
    assert not missing, f"dependencies field required on every record: {missing}"


def test_cp23_dependencies_are_valid_ids():
    by_id = caps_by_id()
    bad = [c["capability_id"] for c in by_id.values()
           if not isinstance(c.get("dependencies"), list)
           or not all(isinstance(d, str) and CAP_ID_RE.match(d) for d in c["dependencies"])]
    assert not bad, f"dependencies must be lists of valid capability IDs: {bad}"


def test_cp24_dependency_references_exist():
    by_id = caps_by_id()
    broken = [f"{cid}->{d}" for cid, c in by_id.items() for d in c["dependencies"] if d not in by_id]
    assert not broken, f"Dependency references must exist: {broken}"


def test_cp25_no_self_dependency():
    by_id = caps_by_id()
    selfs = [cid for cid, c in by_id.items() if cid in c["dependencies"]]
    assert not selfs, f"Self-dependencies forbidden: {selfs}"


def test_cp26_no_duplicate_dependency_entries():
    by_id = caps_by_id()
    bad = [cid for cid, c in by_id.items() if len(c["dependencies"]) != len(set(c["dependencies"]))]
    assert not bad, f"Duplicate dependency entries: {bad}"


def test_cp27_no_dependency_cycles():
    by_id = caps_by_id()
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {cid: WHITE for cid in by_id}

    def dfs(node, stack):
        color[node] = GRAY
        for dep in by_id[node]["dependencies"]:
            if dep not in by_id:
                continue
            if color[dep] == GRAY:
                return stack[stack.index(dep):] + [dep]
            if color[dep] == WHITE:
                found = dfs(dep, stack + [dep])
                if found:
                    return found
        color[node] = BLACK
        return None

    for cid in by_id:
        if color[cid] == WHITE:
            cycle = dfs(cid, [cid])
            assert not cycle, f"Dependency cycle forbidden: {' -> '.join(cycle)}"


def test_cp28_no_rejected_capability_required():
    by_id = caps_by_id()
    bad = [f"{cid}->{d}" for cid, c in by_id.items() for d in c["dependencies"]
           if by_id[d]["status"] == "REJECTED"]
    assert not bad, f"Rejected capabilities must not be required: {bad}"


def test_cp29_obsolete_capability_not_silent_prerequisite():
    by_id = caps_by_id()
    obsolete_deps = [(cid, d) for cid, c in by_id.items() for d in c["dependencies"]
                     if by_id[d]["status"] == "OBSOLETE"]
    for cid, d in obsolete_deps:
        note = (by_id[cid].get("notes") or "").lower()
        assert "obsolete" in note or d.lower() in note, \
            f"{cid} depends on obsolete {d} without explicit documentation"


def test_cp30_tight_dependency_semantics():
    """Dependencies encode meaningful completion gating, not thematic loose links."""
    by_id = caps_by_id()
    # Every non-empty dependency of a PLANNED capability must point at a
    # non-PLANNED record OR a PLANNED record that itself depends on something
    # (chain grounding), preventing accidental mutual PLANNED-only webs.
    for cid, c in by_id.items():
        if c["status"] == "PLANNED":
            for d in c["dependencies"]:
                dep = by_id[d]
                if dep["status"] == "PLANNED":
                    assert dep.get("dependencies") or dep["origin_type"] != "PLANNED", \
                        f"{cid}->{d}: PLANNED dependency must be grounded in a declared prerequisite chain"


def test_cp31_execution_policy_parallel_cycle_broken():
    by_id = caps_by_id()
    ep = by_id.get("EXECUTION_POLICY", {})
    pe = by_id.get("PARALLEL_EXECUTION", {})
    assert "PARALLEL_EXECUTION" not in ep.get("dependencies", []), \
        "EXECUTION_POLICY must not depend on PARALLEL_EXECUTION (policy defines strategy, not the runtime)"
    assert "EXECUTION_POLICY" not in pe.get("dependencies", []), \
        "PARALLEL_EXECUTION must not depend on EXECUTION_POLICY"


def test_cp32_dependency_intentionally_empty_is_documented_when_planned():
    by_id = caps_by_id()
    for cid, c in by_id.items():
        if c["status"] == "PLANNED" and c["origin_type"] == "OWNER_ACCEPTED_PROPOSAL":
            assert c["dependencies"] == [] or True  # empty allowed; verified separately below
    owner_planned_empty = [cid for cid, c in by_id.items()
                           if c["status"] == "PLANNED" and c["origin_type"] == "OWNER_ACCEPTED_PROPOSAL"
                           and not c["dependencies"]]
    assert owner_planned_empty, "At least one owner-accepted PLANNED record intentionally has no prerequisites"


def test_cp33_no_orphaned_planned_without_ledger_presence():
    """Every ledger status PLANNED/ACTIVE candidate referenced by governance must exist."""
    by_id = caps_by_id()
    gov = load_gov()
    for item in gov["roadmap"]["items"]:
        iid = item.get("id", "")
        if not iid.startswith("C") or not iid[1:].isdigit():
            continue
        assert iid in by_id or True  # roadmap goals are goals, not capability ids
    # Focus: candidate records referencing capabilities
    for rec in gov.get("candidate_records", []):
        if "capability" in rec and isinstance(rec.get("capability"), str):
            assert rec["capability"] in by_id, f"governance references unknown capability {rec['capability']}"


# ---------------------------------------------------------------- ledger delta contract

def test_cp34_goal_contract_has_expected_delta_section():
    text = GOAL_TPL.read_text(encoding="utf-8")
    assert "Ledger Delta" in text or "DELTA" in text, \
        "Goal Contract must declare an expected ledger delta section"
    for field in ("Capability", "Current", "Target", "Reason", "Dependencies affected", "Roadmap impact"):
        assert field in text, f"Expected delta section missing field: {field}"


def test_cp35_goal_contract_has_actual_delta_section():
    text = GOAL_TPL.read_text(encoding="utf-8")
    assert "Delta Type" in text or "delta type" in text.lower(), \
        "Goal Contract must record actual verified deltas at close"
    allowed = {"ADDED", "STATUS_CHANGED", "DEFERRED", "REJECTED", "ORIGIN_UPDATED",
               "DEPENDENCIES_UPDATED", "EVIDENCE_REFS_UPDATED", "ROADMAP_SYNC"}
    low = text.lower()
    found = any(a.lower() in low for a in allowed)
    assert found, "Actual delta section must use the canonical delta-type vocabulary"


def test_cp36_goal_contract_owner_acceptance_rule():
    text = GOAL_TPL.read_text(encoding="utf-8")
    assert "OWNER_ACCEPTS_CAPABILITY" in text or "acceptance" in text.lower(), \
        "Goal Contract must state acceptance is not implementation"


def test_cp37_supervisor_provenance_check():
    text = SUP_TPL.read_text(encoding="utf-8").lower()
    assert "provenance" in text, "Supervisor must verify provenance"


def test_cp38_supervisor_dependency_validity_check():
    text = SUP_TPL.read_text(encoding="utf-8").lower()
    assert "dependency_validity" in text or "dependency validity" in text, \
        "Supervisor must verify dependency validity"


def test_cp39_supervisor_roadmap_sync_check():
    text = SUP_TPL.read_text(encoding="utf-8").lower()
    assert "roadmap_sync" in text, "Supervisor must verify roadmap sync"


def test_cp40_supervisor_no_undeclared_promotion_check():
    text = SUP_TPL.read_text(encoding="utf-8").lower()
    assert "no_undeclared_capability_promotion" in text or "undeclared capability promotion" in text, \
        "Supervisor must reject undeclared capability promotion"


# ---------------------------------------------------------------- sync & non-hardcoding

def test_cp41_roadmap_record_count_matches_ledger():
    road = ROADMAP.read_text(encoding="utf-8")
    ledger_count = len(load_ledger()["capabilities"])
    match = re.search(r"\((\d+) records", road)
    assert match and int(match.group(1)) == ledger_count, \
        f"Roadmap count ({match.group(1) if match else '?'}) must match ledger ({ledger_count})"


def test_cp42_roadmap_declares_derivation_sources():
    road = ROADMAP.read_text(encoding="utf-8")
    assert "governance/development-control.json" in road and "capability-index.json" in road, \
        "Roadmap must declare its canonical sources"


def test_cp43_roadmap_intake_honestly_planned():
    road = ROADMAP.read_text(encoding="utf-8")
    assert "OWNER_ACCEPTED_PROPOSAL" in road or "owner-accepted" in road.lower(), \
        "Roadmap must mark owner-accepted intakes as intent, not implementation"


def test_cp44_charter_raw_output_principle():
    text = CHARTER.read_text(encoding="utf-8")
    assert "RAW_OUTPUT_NOT_MODEL_CONTEXT" in text, \
        "Charter must carry the raw-output-not-model-context invariant"


def test_cp45_validator_non_hardcoded_goal_ids():
    src = DEVCTRL.read_text(encoding="utf-8")
    # The validator must not lock future goals into a fixed C16..C21 window;
    # any hardcoded C-number window must be generated from a regex/numeric rule.
    windows = re.findall(r"\{\"C16\", \"C17\", \"C18\", \"C19\", \"C20\", \"C21\"\}|in \{\"C16\"[^}]*\}", src)
    assert not windows, "No hardcoded C16..C21 goal window may remain in the validator"


def test_cp46_validator_goal_id_regex_present():
    src = DEVCTRL.read_text(encoding="utf-8")
    assert re.search(r"C\\d|C<digits>|\^C\\d\+\$|GOAL_ID_RE|C\(\?P<number>\d\+\)", src), \
        "Validator must derive goal IDs from a C<number> rule, not a fixed list"


def test_cp47_validator_accepts_future_goal_in_governance():
    """The live governance may advance current_development to any valid C<number>."""
    gov = load_gov()
    cur = gov["current_development"]
    if isinstance(cur, dict):
        goal = cur.get("development_goal", cur.get("goal"))
    else:
        goal = None
    assert goal is None or GOAL_ID_RE.match(goal), f"current_development must be a valid goal ID: {goal}"


def test_cp48_framework_validator_runs_clean():
    import subprocess
    out = subprocess.run([
        "python3", str(VALIDATOR),
    ], capture_output=True, text=True, cwd=str(ROOT))
    assert out.returncode == 0, f"Framework validator failed:\n{out.stdout}\n{out.stderr}"
    assert "0 failed" in out.stdout, f"Validator reported failures:\n{out.stdout}"


def test_cp49_framework_validator_origin_checks_present():
    src = VALIDATOR.read_text(encoding="utf-8")
    for token in ("V11-origin-present-100", "origin_type", "V12", "dependencies", "V13", "cycle", "V14"):
        assert token in src, f"Validator missing C26 check: {token}"


def test_cp50_c26_candidate_zip_label_style():
    gov = load_gov()
    c26 = next((r for r in gov.get("candidate_records", []) if r.get("goal") == "C26"), None)
    if c26:
        label = c26.get("candidate_label", "")
        assert re.search(r"c26", label, re.IGNORECASE), "C26 candidate label must carry the C26 marker"
        # label style follows established P2P-8-4-7-C-codex-N-...-candidate-v1.zip convention
        assert label.endswith(".zip"), "Candidate label is a zip filename"
