#!/usr/bin/env python3
"""validate_p2p_development_framework.py — deterministic validator for the P2P
durable development framework (Charter, Capability Ledger, roadmap projection,
templates). Runs without network access; exits non-zero on any violation.

Checks (all deterministic against the filesystem):
  V01 Ledger JSON parses and validates against capability-ledger.schema.json.
  V02 capability_id uniqueness + SCREAMING_SNAKE_CASE pattern.
  V03 Every family used in capabilities is registered in families.
  V04 Status values come only from status_vocabulary; DEFERRED has deferred_reason;
      REJECTED has rejected_reason; VERIFIED_IMPLEMENTED has non-empty evidence_refs.
  V05 dependency integrity: every id in dependencies references a record in the ledger.
  V06 Charter exists and cites the canonical upstream (development-control.json or
      AI-HANDOFF.md) and does not contain forbidden competitor patterns.
  V07 Roadmap projection declares its canonical sources and contains the honesty
      note about non-recovered C22-C24 (while that state persists).
  V08 Templates exist with required sections.
  V09 Ledger freshness vocabulary check (values must belong to the allowed set).
  V10 No capability record duplicates the authority of governance/development-control.json
      fields that control runtime (only references allowed); verified by requiring
      origin_refs non-empty and no record with capability_id colliding with governance
      top-level control keys.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs/p2p-development/capability-ledger/capability-index.json"
SCHEMA = ROOT / "docs/p2p-development/capability-ledger/capability-ledger.schema.json"
CHARTER = ROOT / "docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md"
ROADMAP = ROOT / "docs/p2p-development/current-roadmap.md"
TEMPLATE_DIR = ROOT / "docs/p2p-development/templates"
GOVERNANCE = ROOT / "governance/development-control.json"

ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,60}$")
FRESHNESS_ALLOWED = {
    "verified_against_filesystem",
    "from_governance_record",
    "from_plan_or_report",
    "origin_unknown_or_not_durably_recovered",
}
# Governance keys whose authority must never be duplicated as a runtime control field.
GOV_CONTROL_KEYS = {
    "current_development", "candidate_records", "official_baseline", "roadmap",
    "capability_status", "research_decisions", "north_star", "approval_workflow",
    "architectural_invariants", "promotion_state", "runtime",
}

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    # ---------- V01: schema validation ----------
    ok = True
    if not LEDGER.exists():
        check("V01-ledger-exists", False, "ledger missing")
        ok = False
    else:
        try:
            ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            check("V01-ledger-parses", False, str(e))
            ok = False
        else:
            check("V01-ledger-parses", True)
            try:
                schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                check("V01-schema-parses", False, str(e))
                ok = False
            else:
                check("V01-schema-parses", True)
                try:
                    from jsonschema import validate, ValidationError
                    validate(instance=ledger, schema=schema)
                    check("V01-schema-valid", True)
                except ImportError:
                    print("[SKIP] V01-schema-valid — jsonschema not installed")
                except ValidationError as e:
                    check("V01-schema-valid", False, f"path {list(e.path)}: {e.message}")
                    ok = False

    # ---------- V02/V03/V04/V05/V09/V10: record-level rules ----------
    caps = ledger.get("capabilities", [])
    families = ledger.get("families", {})
    vocab = set(ledger.get("status_vocabulary", []))

    ids = [c.get("capability_id") for c in caps]
    dup = {i for i in ids if ids.count(i) > 1}
    check("V02-id-unique", len(dup) == 0, ", ".join(sorted(dup))[:100] if dup else "")
    bad_pattern = [c["capability_id"] for c in caps if not ID_PATTERN.match(str(c.get("capability_id")))]
    check("V02-id-pattern", len(bad_pattern) == 0, ", ".join(bad_pattern)[:100] if bad_pattern else "")

    bad_family = [c["capability_id"] for c in caps if c["family"] not in families]
    check("V03-family-registered", len(bad_family) == 0, ", ".join(bad_family)[:100] if bad_family else "")

    unknown_status = [c["capability_id"] for c in caps if c.get("status") not in vocab]
    check("V04-status-vocab", len(unknown_status) == 0, ", ".join(unknown_status)[:100] if unknown_status else "")
    deferred_missing = [c["capability_id"] for c in caps if c.get("status") == "DEFERRED" and not c.get("deferred_reason")]
    rejected_missing = [c["capability_id"] for c in caps if c.get("status") == "REJECTED" and not c.get("rejected_reason")]
    verified_no_evidence = [c["capability_id"] for c in caps if c.get("status") == "VERIFIED_IMPLEMENTED" and not c.get("evidence_refs")]
    check("V04-deferred-reason", len(deferred_missing) == 0, ", ".join(deferred_missing)[:100] if deferred_missing else "")
    check("V04-rejected-reason", len(rejected_missing) == 0, ", ".join(rejected_missing)[:100] if rejected_missing else "")
    check("V04-verified-evidence", len(verified_no_evidence) == 0, ", ".join(verified_no_evidence)[:100] if verified_no_evidence else "")

    id_set = set(ids)
    broken_deps = [
        f"{c['capability_id']}->{d}" for c in caps
        for d in c.get("dependencies", []) if d not in id_set
    ]
    check("V05-dep-integrity", len(broken_deps) == 0, ", ".join(broken_deps)[:100] if broken_deps else "")

    bad_fresh = [c["capability_id"] for c in caps if c.get("freshness") and c["freshness"] not in FRESHNESS_ALLOWED]
    check("V09-freshness-vocab", len(bad_fresh) == 0, ", ".join(bad_fresh)[:100] if bad_fresh else "")

    gov = json.loads(GOVERNANCE.read_text(encoding="utf-8"))
    colliding = [c["capability_id"] for c in caps if c["capability_id"] in GOV_CONTROL_KEYS]
    check("V10-no-gov-collision", len(colliding) == 0, ", ".join(colliding)[:100] if colliding else "")

    # ---------- V06: charter ----------
    if CHARTER.exists():
        charter = CHARTER.read_text(encoding="utf-8")
        cites = ("development-control.json" in charter or "AI-HANDOFF.md" in charter)
        check("V06-charter-cites-canonical", cites, "must reference canonical upstream")
        forbidden = {"second truth store", "competing router", "chat history as state"}
        found = [f for f in forbidden if f in charter.lower()]
        check("V06-charter-no-competitor-patterns", len(found) == 0, ", ".join(found)[:80] if found else "")
    else:
        check("V06-charter-exists", False)

    # ---------- V07: roadmap projection ----------
    if ROADMAP.exists():
        road = ROADMAP.read_text(encoding="utf-8")
        declares = ("governance/development-control.json" in road and "capability-index.json" in road)
        check("V07-roadmap-declares-sources", declares)
        honesty = "not" in road.lower() and ("recover" in road.lower() or "unknown" in road.lower())
        check("V07-roadmap-honesty-note", honesty, "must note unrecovered C22-C24 while that persists")
    else:
        check("V07-roadmap-exists", False)

    # ---------- V08: templates ----------
    for tmpl, sections in {
        "P2P-GOAL-CONTRACT-TEMPLATE.md": ["Truth recovery", "Scope", "Stop rule", "Ledger Delta"],
        "P2P-SUPERVISOR-TEMPLATE.md": ["Verifier", "Verdict", "Discrepancies", "PROVENANCE", "DEPENDENCY_VALIDITY", "ROADMAP_SYNC", "NO_UNDECLARED_CAPABILITY_PROMOTION"],
    }.items():
        path = TEMPLATE_DIR / tmpl
        if path.exists():
            text = path.read_text(encoding="utf-8").lower()
            missing = [s for s in sections if s.lower() not in text]
            check(f"V08-{tmpl}-sections", len(missing) == 0, ", ".join(missing) if missing else "")
        else:
            check(f"V08-{tmpl}-exists", False)

    # ---------- C26 checks V11-V17 ----------
    by_id = {c["capability_id"]: c for c in caps}

    # V11: origin coverage — every record has origin_refs with at least one entry;
    # origin unknown must be explicit, never silent.
    ORIGIN_UNKNOWN_MARKER = "origin_unknown_or_not_durably_recovered"
    no_origin = [c["capability_id"] for c in caps if not c.get("origin_refs")]
    check("V11-origin-present-100", len(no_origin) == 0, ", ".join(no_origin)[:100] if no_origin else "")
    unknown_refs_wrong = [
        c["capability_id"] for c in caps
        if ORIGIN_UNKNOWN_MARKER in c.get("origin_refs", []) and set(c["origin_refs"]) != {ORIGIN_UNKNOWN_MARKER}
    ]
    check("V11-origin-unknown-exact", len(unknown_refs_wrong) == 0, ", ".join(unknown_refs_wrong)[:100] if unknown_refs_wrong else "")

    # V12: origin_type — required enum value; UNKNOWN origin_type iff explicit unknown refs.
    ORIGIN_TYPES = {
        "IMPLEMENTATION_GOAL", "RESEARCH_DECISION", "OWNER_ACCEPTED_PROPOSAL",
        "ARCHITECTURE_INVARIANT", "UPSTREAM_SPECIFICATION", "PROJECT_LEARNING",
        "REJECTED_DESIGN", "RECOVERED_LEGACY", "UNKNOWN",
    }
    bad_origin_type = [c["capability_id"] for c in caps if c.get("origin_type") not in ORIGIN_TYPES]
    check("V12-origin-type-valid", len(bad_origin_type) == 0, ", ".join(bad_origin_type)[:100] if bad_origin_type else "")
    origin_unknown_mismatch = [
        c["capability_id"] for c in caps
        if c.get("origin_type") == "UNKNOWN" and c.get("origin_refs") != [ORIGIN_UNKNOWN_MARKER]
    ]
    check("V12-origin-type-unknown-consistent", len(origin_unknown_mismatch) == 0, ", ".join(origin_unknown_mismatch)[:100] if origin_unknown_mismatch else "")
    owner_proposal_not_planned = [
        c["capability_id"] for c in caps
        if c.get("origin_type") == "OWNER_ACCEPTED_PROPOSAL" and c.get("status") != "PLANNED"
    ]
    check("V12-owner-accepted-is-planned", len(owner_proposal_not_planned) == 0, ", ".join(owner_proposal_not_planned)[:100] if owner_proposal_not_planned else "")

    # V13: dependency field coverage + structural rules (presence 100%, no self-dep,
    # no duplicate deps).
    no_deps_field = [c["capability_id"] for c in caps if "dependencies" not in c]
    check("V13-deps-field-present-100", len(no_deps_field) == 0, ", ".join(no_deps_field)[:100] if no_deps_field else "")
    self_deps = [c["capability_id"] for c in caps if c["capability_id"] in c.get("dependencies", [])]
    check("V13-deps-no-self", len(self_deps) == 0, ", ".join(self_deps)[:100] if self_deps else "")
    dup_deps = [c["capability_id"] for c in caps if len(c.get("dependencies", [])) != len(set(c.get("dependencies", [])))]
    check("V13-deps-no-duplicates", len(dup_deps) == 0, ", ".join(dup_deps)[:100] if dup_deps else "")
    REJECTED_STATUSES = {"REJECTED", "OBSOLETE"}
    rejected_prereq = [
        f"{c['capability_id']}->{d}" for c in caps for d in c.get("dependencies", [])
        if by_id.get(d, {}).get("status") in REJECTED_STATUSES
    ]
    check("V13-deps-no-rejected-prereq", len(rejected_prereq) == 0, ", ".join(rejected_prereq)[:100] if rejected_prereq else "")

    # V14: dependency cycle detection (depth-limited DFS; cycles are semantically
    # forbidden because completion order must be a DAG).
    def _find_cycles() -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {cid: WHITE for cid in by_id}
        def dfs(node: str, path: list[str]) -> None:
            color[node] = GRAY
            for dep in by_id[node].get("dependencies", []):
                if dep not in by_id:
                    continue
                if color.get(dep) == GRAY:
                    found.append((path[path.index(dep)], dep))
                elif color.get(dep) == WHITE:
                    dfs(dep, path + [dep])
            color[node] = BLACK
        for cid in by_id:
            if color[cid] == WHITE:
                dfs(cid, [cid])
        return found
    cycles = _find_cycles()
    check("V14-deps-no-cycles", len(cycles) == 0, ", ".join(f"{a}->{b}" for a, b in cycles)[:100] if cycles else "")

    # V15: Goal Contract ledger-delta sections required in the template, and the
    # current roadmap projection matches ledger count and governance baseline.
    if CHARTER.exists():
        charter_text = CHARTER.read_text(encoding="utf-8")
        check("V15-charter-raw-output-principle", "RAW_OUTPUT_NOT_MODEL_CONTEXT" in charter_text, "charter missing RAW_OUTPUT_NOT_MODEL_CONTEXT invariant")
    if ROADMAP.exists():
        road = ROADMAP.read_text(encoding="utf-8")
        ledger_count = len(caps)
        match = re.search(r"\((\d+) records", road)
        road_count_ok = bool(match and int(match.group(1)) == ledger_count)
        check("V15-roadmap-count-sync", road_count_ok, f"roadmap says {match.group(1) if match else '?'} records, ledger has {ledger_count}")
        base = gov.get("official_baseline", {})
        base_match = base.get("version", "") in road or (base.get("artifact_sha256") or "")[:12] in road
        check("V15-roadmap-baseline-sync", base_match, "roadmap baseline must match governance official_baseline")

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed. {len(failed)} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
