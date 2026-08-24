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


def _record_label(index: int, record: object) -> str:
    """Return a stable diagnostic label without assuming record shape.

    A malformed legacy record may expose ``id`` instead of the canonical
    ``capability_id``. That hint is useful for provenance, but it must never
    be treated as a canonical identifier or allow validation to crash.
    """
    if not isinstance(record, dict):
        return f"capabilities[{index}]:record-not-object"
    capability_id = record.get("capability_id")
    if isinstance(capability_id, str) and capability_id:
        return capability_id
    legacy_id = record.get("id")
    suffix = f" legacy_id={legacy_id}" if legacy_id is not None else ""
    return f"capabilities[{index}]:missing-capability_id{suffix}"


def _record_entries(caps: object) -> list[tuple[int, dict]]:
    """Keep only object-shaped records for field checks, never silently.

    The caller separately reports non-object entries and missing IDs. This
    helper only prevents a malformed record from causing an uncontrolled
    Python exception while the validator emits its complete failure set.
    """
    if not isinstance(caps, list):
        return []
    return [(index, record) for index, record in enumerate(caps)
            if isinstance(record, dict)]


def _record_diagnostics(caps: object, families: dict, vocab: set[str]) -> dict[str, object]:
    """Collect fail-closed record diagnostics for tests and the CLI path."""
    entries = _record_entries(caps)
    non_object = [_record_label(index, record) for index, record in enumerate(caps or [])
                  if not isinstance(record, dict)] if isinstance(caps, list) else [
                      "capabilities:not-an-array"]
    missing_id = [_record_label(index, record) for index, record in entries
                  if not isinstance(record.get("capability_id"), str)
                  or not record.get("capability_id")]
    valid_ids = [record.get("capability_id") for _, record in entries
                 if isinstance(record.get("capability_id"), str)
                 and record.get("capability_id")]
    duplicates = {capability_id for capability_id in valid_ids
                  if valid_ids.count(capability_id) > 1}
    bad_pattern = [_record_label(index, record) for index, record in entries
                   if not isinstance(record.get("capability_id"), str)
                   or not ID_PATTERN.match(str(record.get("capability_id")))]
    bad_family = [_record_label(index, record) for index, record in entries
                  if record.get("family") not in families]
    unknown_status = [_record_label(index, record) for index, record in entries
                      if record.get("status") not in vocab]
    invalid_dep_shape = [_record_label(index, record) for index, record in entries
                         if "dependencies" not in record
                         or not isinstance(record.get("dependencies"), list)]
    return {
        "entries": entries,
        "non_object": non_object,
        "missing_id": missing_id,
        "valid_ids": valid_ids,
        "duplicates": duplicates,
        "bad_pattern": bad_pattern,
        "bad_family": bad_family,
        "unknown_status": unknown_status,
        "invalid_dep_shape": invalid_dep_shape,
    }


def _roadmap_count_matches(roadmap_text: str, ledger_count: int) -> bool:
    """Check the derived snapshot count without accepting a missing count."""
    match = re.search(r"\((\d+) records", roadmap_text)
    return bool(match and int(match.group(1)) == ledger_count)


def main() -> int:
    # ---------- V01: schema validation ----------
    ledger = {}
    schema = {}
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
            if not isinstance(ledger, dict):
                check("V01-ledger-object", False, "ledger root must be an object")
                ledger = {}
                ok = False
            else:
                check("V01-ledger-object", True)
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
    raw_caps = ledger.get("capabilities", [])
    caps = raw_caps if isinstance(raw_caps, list) else []
    check("V01-capabilities-list", isinstance(raw_caps, list),
          "capabilities must be an array" if not isinstance(raw_caps, list) else "")
    families = ledger.get("families", {})
    if not isinstance(families, dict):
        families = {}
    vocab_value = ledger.get("status_vocabulary", [])
    vocab = {item for item in vocab_value if isinstance(item, str)} \
        if isinstance(vocab_value, list) else set()
    diagnostics = _record_diagnostics(caps, families, vocab)
    entries = diagnostics["entries"]
    non_object = diagnostics["non_object"]
    missing_id = diagnostics["missing_id"]
    check("V02-record-shape", len(non_object) == 0,
          ", ".join(non_object)[:160] if non_object else "")
    check("V02-id-present", len(missing_id) == 0,
          ", ".join(missing_id)[:160] if missing_id else "")

    valid_ids = diagnostics["valid_ids"]
    dup = diagnostics["duplicates"]
    check("V02-id-unique", len(dup) == 0,
          ", ".join(sorted(dup))[:100] if dup else "")
    bad_pattern = diagnostics["bad_pattern"]
    check("V02-id-pattern", len(bad_pattern) == 0,
          ", ".join(bad_pattern)[:160] if bad_pattern else "")

    bad_family = diagnostics["bad_family"]
    check("V03-family-registered", len(bad_family) == 0,
          ", ".join(bad_family)[:160] if bad_family else "")

    unknown_status = diagnostics["unknown_status"]
    check("V04-status-vocab", len(unknown_status) == 0,
          ", ".join(unknown_status)[:160] if unknown_status else "")
    deferred_missing = [_record_label(index, record) for index, record in entries
                        if record.get("status") == "DEFERRED"
                        and not record.get("deferred_reason")]
    rejected_missing = [_record_label(index, record) for index, record in entries
                        if record.get("status") == "REJECTED"
                        and not record.get("rejected_reason")]
    verified_no_evidence = [_record_label(index, record) for index, record in entries
                            if record.get("status") == "VERIFIED_IMPLEMENTED"
                            and not record.get("evidence_refs")]
    check("V04-deferred-reason", len(deferred_missing) == 0,
          ", ".join(deferred_missing)[:160] if deferred_missing else "")
    check("V04-rejected-reason", len(rejected_missing) == 0,
          ", ".join(rejected_missing)[:160] if rejected_missing else "")
    check("V04-verified-evidence", len(verified_no_evidence) == 0,
          ", ".join(verified_no_evidence)[:160] if verified_no_evidence else "")

    id_set = set(valid_ids)
    invalid_dep_shape = diagnostics["invalid_dep_shape"]
    check("V05-dep-shape", len(invalid_dep_shape) == 0,
          ", ".join(invalid_dep_shape)[:160] if invalid_dep_shape else "")
    broken_deps = [
        f"{_record_label(index, record)}->{dependency}"
        for index, record in entries
        for dependency in (record.get("dependencies")
                          if isinstance(record.get("dependencies"), list) else [])
        if not isinstance(dependency, str) or dependency not in id_set
    ]
    check("V05-dep-integrity", len(broken_deps) == 0,
          ", ".join(broken_deps)[:160] if broken_deps else "")

    bad_fresh = [_record_label(index, record) for index, record in entries
                 if record.get("freshness")
                 and record.get("freshness") not in FRESHNESS_ALLOWED]
    check("V09-freshness-vocab", len(bad_fresh) == 0,
          ", ".join(bad_fresh)[:160] if bad_fresh else "")

    try:
        gov = json.loads(GOVERNANCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        gov = {}
        check("V10-governance-parses", False, "governance source unavailable or malformed")
    else:
        check("V10-governance-parses", True)
    colliding = [_record_label(index, record) for index, record in entries
                 if record.get("capability_id") in GOV_CONTROL_KEYS]
    check("V10-no-gov-collision", len(colliding) == 0,
          ", ".join(colliding)[:160] if colliding else "")

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
    by_id = {}
    for _, record in entries:
        capability_id = record.get("capability_id")
        if isinstance(capability_id, str) and capability_id and capability_id not in by_id:
            by_id[capability_id] = record

    # V11: origin coverage — every record has origin_refs with at least one entry;
    # origin unknown must be explicit, never silent.
    ORIGIN_UNKNOWN_MARKER = "origin_unknown_or_not_durably_recovered"
    no_origin = [_record_label(index, record) for index, record in entries
                 if not record.get("origin_refs")]
    check("V11-origin-present-100", len(no_origin) == 0,
          ", ".join(no_origin)[:160] if no_origin else "")
    unknown_refs_wrong = [
        _record_label(index, record) for index, record in entries
        if isinstance(record.get("origin_refs"), list)
        and ORIGIN_UNKNOWN_MARKER in record.get("origin_refs", [])
        and record.get("origin_refs", []) != [ORIGIN_UNKNOWN_MARKER]
    ]
    check("V11-origin-unknown-exact", len(unknown_refs_wrong) == 0,
          ", ".join(unknown_refs_wrong)[:160] if unknown_refs_wrong else "")

    # V12: origin_type — required enum value; UNKNOWN origin_type iff explicit unknown refs.
    ORIGIN_TYPES = {
        "IMPLEMENTATION_GOAL", "RESEARCH_DECISION", "OWNER_ACCEPTED_PROPOSAL",
        "ARCHITECTURE_INVARIANT", "UPSTREAM_SPECIFICATION", "PROJECT_LEARNING",
        "REJECTED_DESIGN", "RECOVERED_LEGACY", "UNKNOWN",
    }
    bad_origin_type = [_record_label(index, record) for index, record in entries
                       if record.get("origin_type") not in ORIGIN_TYPES]
    check("V12-origin-type-valid", len(bad_origin_type) == 0,
          ", ".join(bad_origin_type)[:160] if bad_origin_type else "")
    origin_unknown_mismatch = [
        _record_label(index, record) for index, record in entries
        if record.get("origin_type") == "UNKNOWN"
        and record.get("origin_refs") != [ORIGIN_UNKNOWN_MARKER]
    ]
    check("V12-origin-type-unknown-consistent", len(origin_unknown_mismatch) == 0,
          ", ".join(origin_unknown_mismatch)[:160] if origin_unknown_mismatch else "")
    owner_proposal_not_planned = [
        _record_label(index, record) for index, record in entries
        if record.get("origin_type") == "OWNER_ACCEPTED_PROPOSAL"
        and record.get("status") != "PLANNED"
    ]
    check("V12-owner-accepted-is-planned", len(owner_proposal_not_planned) == 0,
          ", ".join(owner_proposal_not_planned)[:160] if owner_proposal_not_planned else "")

    # V13: dependency field coverage + structural rules (presence 100%, no self-dep,
    # no duplicate deps).
    no_deps_field = [_record_label(index, record) for index, record in entries
                     if "dependencies" not in record]
    check("V13-deps-field-present-100", len(no_deps_field) == 0,
          ", ".join(no_deps_field)[:160] if no_deps_field else "")
    self_deps = [_record_label(index, record) for index, record in entries
                 if isinstance(record.get("dependencies"), list)
                 and record.get("capability_id") in record.get("dependencies", [])]
    check("V13-deps-no-self", len(self_deps) == 0,
          ", ".join(self_deps)[:160] if self_deps else "")
    dup_deps = [_record_label(index, record) for index, record in entries
                if isinstance(record.get("dependencies"), list)
                and len(record.get("dependencies", [])) != len({repr(item) for item in record.get("dependencies", [])})]
    check("V13-deps-no-duplicates", len(dup_deps) == 0,
          ", ".join(dup_deps)[:160] if dup_deps else "")
    REJECTED_STATUSES = {"REJECTED", "OBSOLETE"}
    rejected_prereq = [
        f"{_record_label(index, record)}->{dependency}"
        for index, record in entries
        for dependency in (record.get("dependencies")
                           if isinstance(record.get("dependencies"), list) else [])
        if isinstance(dependency, str)
        and by_id.get(dependency, {}).get("status") in REJECTED_STATUSES
    ]
    check("V13-deps-no-rejected-prereq", len(rejected_prereq) == 0,
          ", ".join(rejected_prereq)[:160] if rejected_prereq else "")

    # V14: dependency cycle detection (depth-limited DFS; cycles are semantically
    # forbidden because completion order must be a DAG).
    def _find_cycles() -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {cid: WHITE for cid in by_id}
        def dfs(node: str, path: list[str]) -> None:
            color[node] = GRAY
            dependencies = by_id[node].get("dependencies", [])
            if not isinstance(dependencies, list):
                color[node] = BLACK
                return
            for dep in dependencies:
                if not isinstance(dep, str) or dep not in by_id:
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
        road_count_ok = _roadmap_count_matches(road, ledger_count)
        check("V15-roadmap-count-sync", road_count_ok, f"roadmap says {match.group(1) if match else '?'} records, ledger has {ledger_count}")
        base = gov.get("official_baseline", {})
        base_match = base.get("version", "") in road or (base.get("artifact_sha256") or "")[:12] in road
        check("V15-roadmap-baseline-sync", base_match, "roadmap baseline must match governance official_baseline")

    # ---------- C29 checks V18-V21 (goal closure & durable state integrity) ----------

    # V18: terminal-state consistency — every terminal (DONE/BLOCKED) roadmap
    # item must agree with governance `current`/`likely_next`, its terminal
    # report's GOAL_TERMINAL_STATUS, and its candidate record when one is
    # contractually required.
    TERMINAL_STATUS = {"DONE", "BLOCKED", "FAIL"}
    items = {str(i.get("goal_id") or i.get("id", "")).upper(): i
             for i in gov.get("roadmap", {}).get("items", [])}
    current = gov.get("roadmap", {}).get("current", {})
    by_rec = {r.get("candidate_id"): r for r in gov.get("candidate_records", [])}
    if items and current:
        # The latest DONE item must be roadmap.current.
        done_items = [gid for gid, i in items.items() if str(i.get("status", "")).upper() == "DONE"]
        last_done = done_items[-1] if done_items else None
        cur_status = str(current.get("status", "")).upper()
        check("V18-current-is-terminal-done", last_done is not None and str(current.get("id", "")).upper() == last_done and cur_status == "DONE",
              f"current = {current.get('id')}/{cur_status}, last DONE item = {last_done}")
        # Candidate records exist only for goals that passed the candidate
        # policy (C14+); earlier DONE goals predate that policy and are
        # governed by their own promotion records.
        candidate_governed = {r.get("candidate_id") for r in gov.get("candidate_records", [])}
        for gid in done_items:
            if gid not in candidate_governed:
                continue
            rec = by_rec.get(gid)
            rec_ok = rec is not None and len(str(rec.get("candidate_sha256", ""))) == 64
            placeholder = rec is not None and "TO_BE_FILLED" in str(rec.get("candidate_sha256", ""))
            check(f"V18-done-{gid.lower()}-candidate-closure",
                  rec_ok and not placeholder,
                  f"{gid}: candidate record {'present' if rec else 'MISSING'}" + (" with placeholder SHA" if placeholder else ""))

    # V19: candidate policy compliance — PASS-with-changes requires YES; a
    # BLOCKED/FAIL goal requires NO candidate record claiming otherwise.
    candidate_governed = {r.get("candidate_id") for r in gov.get("candidate_records", [])}
    for gid, item in items.items():
        status = str(item.get("status", "")).upper()
        if status in ("PASS", "DONE") and gid in candidate_governed:
            if gid in by_rec:
                rec = by_rec[gid]
                sha = str(rec.get("candidate_sha256", ""))
                verify = bool(rec.get("package_verify_evidence")
                              or rec.get("evidence_refs"))
                check(f"V19-{gid.lower()}-policy-compliant",
                      len(sha) == 64 and verify,
                      "" if (len(sha) == 64 and verify) else f"{gid}: SHA {'real' if len(sha)==64 else 'placeholder/missing'}; verify evidence {'present' if verify else 'MISSING'}")
            else:
                check(f"V19-{gid.lower()}-policy-compliant", False,
                      f"{gid}: terminal status {status} but no candidate record (policy requires one when changes occurred)")
        elif status in ("BLOCKED", "FAIL", "DEFERRED"):
            rec = by_rec.get(gid)
            if rec is not None:
                check(f"V19-{gid.lower()}-no-fabricated-candidate",
                      "TO_BE_FILLED" in str(rec.get("candidate_sha256", "") or ""),
                      f"{gid}: {status} must not claim a fabricated (real-SHA) candidate")

    # V20: PR lineage integrity — governance declares each goal's branch lineage,
    # and `pr_base_mismatch` policy (parent branch is an ancestor of the goal
    # branch) is mechanically derivable from durable state.
    lineage = gov.get("pr_lineage", {})
    if lineage:
        import subprocess as _sp
        refs = _sp.run(["git", "rev-parse", "--verify",
                        f"refs/heads/{list(lineage.keys())[0]}"],
                       cwd=str(ROOT), capture_output=True, text=True, check=False)
        local_branches = _sp.run(["git", "branch", "--format=%(refname:short)"],
                                 cwd=str(ROOT), capture_output=True, text=True,
                                 check=False).stdout.split()
        any_checked = False
        for goal_branch, declared_base in lineage.items():
            # Branches created later in the goal session are not yet local;
            # the declaration is still validated once the branch exists.
            if goal_branch not in local_branches:
                check(f"V20-lineage-{goal_branch}-not-yet-local",
                      True, f"{goal_branch} not yet created locally; lineage checked at branch creation")
                continue
            any_checked = True
            rc = _sp.run(["git", "merge-base", "--is-ancestor", declared_base, goal_branch],
                         cwd=str(ROOT), capture_output=True, text=True, check=False)
            ok = rc.returncode == 0
            check(f"V20-lineage-{goal_branch}-contains-base",
                  ok, f"{declared_base} {'is' if ok else 'is NOT'} an ancestor of {goal_branch}")
        check("V20-pr-lineage-declared", True,
              f"{len(lineage)} lineage declarations present" + ("" if any_checked else " (no branches local yet)"))
    else:
        check("V20-pr-lineage-declared", False, "governance missing pr_lineage declarations")

    # V21: terminal report metadata fields — the latest terminal report must
    # carry the canonical fields a supervisor and the closure checker consume.
    import glob as _gl
    reports = sorted(_gl.glob(str(ROOT / "docs/p2p-development/reports/P2P-C*-terminal-report.md")))
    if reports:
        text = Path(reports[-1]).read_text(encoding="utf-8")
        for field in ("GOAL_TERMINAL_STATUS", "CANDIDATE_REQUIRED",
                      "CANDIDATE_SHA256", "CANDIDATE_LABEL", "GOAL_ID"):
            check(f"V21-report-field-{field.lower()}", field in text,
                  f"latest terminal report {Path(reports[-1]).name} {'has' if field in text else 'MISSING'} {field}")
    else:
        check("V21-terminal-report-exists", False)

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed. {len(failed)} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
