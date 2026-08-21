#!/usr/bin/env python3
"""p2p_roadmap_planner.py — Canonical roadmap-aware development planner (v2, hardened).

P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01A — fail-closed coverage + canonical blocker +
ranking semantics closure. Preserves the v1 foundation (spec 01A: do not redesign).

Hardening over v1 (01A seams):
  S1  ROADMAP_COVERAGE_GAP == TRUE  ->  RECOMMENDED_NEXT_GOAL = null,
      PLAN_COMPLETE = false, planning_status = "BLOCKED / ROADMAP_COVERAGE_GAP"
  S2  Coverage gate counts SELECTED, PLANNED, PARTIAL as materially relevant
      (explicit status translation between Research Adoption Ledger and Roadmap).
      UNKNOWN never silently satisfies coverage.
  S3  BLOCKED / BLOCKED_TERMINAL item statuses are classified deterministically by
      blocker/evidence semantics (BLOCKED_BY_EXTERNAL_EVIDENCE / BLOCKED_BY_DEPENDENCY);
      UNKNOWN only for genuinely unrecognized/ambiguous status.
      KNOWN_BLOCKED != UNKNOWN; UNKNOWN != SUPPORTED; UNKNOWN != READY_NOW.
  S4  dependency_necessity weight is actually consumed — real graph leverage:
      dependent-high-value-unblocked count, terminal-prerequisite bonus, blocking-edge
      removal — deterministic, documented, testable, derived from canonical graph.
  S5  beginner view derives from the ACTUALLY selected roadmap item
      (title, owner_value, mutation risk, project impact, promotion requirement,
      dependencies/blockers) — no stale hardcoded wording.
  S6  WHY_THIS_GOAL is evidence-bound with per-factor SCORE_BREAKDOWN; generic
      "blocks/leverages higher-strategic-value items below it" removed unless graph
      edges support it.

Authority precedence (spec 01 §2), unchanged:
  1. official baseline / C-line historical status  -> development-control.json
  2. future roadmap item/family organization       -> p2p-development-roadmap.json
  3. research adoption/provenance                  -> research-adoption-ledger.json
  4. capability existence/status                   -> capability-index.json
  5. Owner explicit current decision               -> Owner input model
  6. external research                             -> provenance ONLY (via ledger), never authority
"""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

VERSION = "3"
SPEC_GOAL = "P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01A"

STATUS_VOCAB = {
    "READY_NOW", "BLOCKED_BY_DEPENDENCY", "BLOCKED_BY_EXTERNAL_EVIDENCE",
    "OWNER_DEFERRED", "NOT_YET_SAFE", "SUPERSEDED", "DONE", "SHIPPED",
    "VERIFIED", "PLANNED", "PARTIAL", "DEFERRED", "REJECTED", "UNKNOWN",
}
DEP_GRAPH_CLASSES = {
    "READY_NOW", "BLOCKED_BY_DEPENDENCY", "BLOCKED_BY_EXTERNAL_EVIDENCE",
    "OWNER_DEFERRED", "NOT_YET_SAFE", "SUPERSEDED", "DONE_SHIPPED_VERIFIED", "UNKNOWN",
}
# Item statuses in roadmap.json that map to terminal evidence states
TERMINAL_STATUSES = {"DONE", "SHIPPED", "VERIFIED"}
# Vocabulary defined in development roadmap + ledger + capability index (allowed union)
ALLOWED_ROADMAP_ITEM_STATUS = {"DONE", "PLANNED", "DEFERRED", "PARTIAL", "VERIFIED", "REJECTED", "SHIPPED",
                               "BLOCKED", "BLOCKED_TERMINAL", "ACTIVE_UNPROMOTED"}

# Research Adoption Ledger status translation (spec 01A §3, explicit):
#   SELECTED / PLANNED / PARTIAL  -> materially relevant; must have durable roadmap consideration
#   SHIPPED / VERIFIED / IMPLEMENTED -> adopted (coverage satisfied)
#   DEFERRED / REJECTED / SUPERSEDED -> excluded, reason documented
#   DISCOVERED / RESEARCHED         -> not yet selected (not gaps, not counted)
#   UNKNOWN                         -> NEVER satisfies coverage (fail-closed)
LEDGER_MATERIAL_STATUSES = {"SELECTED", "PLANNED", "PARTIAL"}
LEDGER_ADOPTED_STATUSES = {"SHIPPED", "VERIFIED", "IMPLEMENTED"}
LEDGER_EXCLUDED_STATUSES = {"DEFERRED", "REJECTED", "SUPERSEDED"}

WEIGHTS = {"owner_value": 3.0, "dependency_necessity": 2.0, "safety_maturity": 1.5,
           "evidence_gap": 1.0, "architectural_leverage": 1.5}
WEIGHT_SUM = sum(WEIGHTS.values())

BASELINE_EXPECTED = "8.4.7-C-codex.41"
BASELINE_SHA_EXPECTED = "da835f8a48caf4536094ffdd82e3c65baa82da32aa9a7ae73714ee1f2e9c3d2d"


class PlannerError(Exception):
    """Fail-closed explicit refusal — never raised silently, always with cause."""
    pass


# ---------------------------------------------------------------- readers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path, label):
    if not os.path.exists(path):
        raise PlannerError(f"{label}: CANONICAL SOURCE UNAVAILABLE — {path}")
    with open(path) as f:
        raw = f.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise PlannerError(f"{label}: CANONICAL JSON PARSE FAILED — {e}")


# ---------------------------------------------------------------- input model
def build_input_model(repo, override_owner_value):
    """Spec §3 input contract — all fields populated from canonical durable files."""
    dctl = load_json(os.path.join(repo, "governance", "development-control.json"), "development-control")
    roadmap = load_json(os.path.join(repo, "governance", "p2p-development-roadmap.json"), "p2p-development-roadmap")
    ledger = load_json(os.path.join(repo, "governance", "research-adoption-ledger.json"), "research-adoption-ledger")
    cap = load_json(os.path.join(repo, "docs", "p2p-development", "capability-ledger", "capability-index.json"), "capability-index")
    intake = {}
    intake_path = os.path.join(repo, "governance", "research-intake-ledger.json")
    if os.path.exists(intake_path):
        intake = load_json(intake_path, "research-intake-ledger")
    intake_contract = {}
    ic_path = os.path.join(repo, "governance", "intake-contract.json")
    if os.path.exists(ic_path):
        intake_contract = load_json(ic_path, "intake-contract")

    # §13 fail-closed: two canonical authorities materially conflict detection
    dctl_items = {it.get("id"): it for it in dctl.get("roadmap", {}).get("items", [])}
    for it in roadmap.get("items", []):
        cid = re.sub(r"^RM-", "", it.get("roadmap_id", ""))
        dctl_it = dctl_items.get(cid)
        if dctl_it and dctl_it.get("status") in ("DONE",) and it.get("status") not in TERMINAL_STATUSES:
            raise PlannerError(f"AUTHORITY CONFLICT — development-control C-line status for {cid} is {dctl_it.get('status')} "
                               f"while p2p-development-roadmap status is {it.get('status')}; canonical authorities materially conflict")

    ob = dctl.get("official_baseline")
    if not ob or ob.get("version") != BASELINE_EXPECTED or ob.get("artifact_sha256") != BASELINE_SHA_EXPECTED:
        raise PlannerError(f"BASELINE IDENTITY MISMATCH — expected {BASELINE_EXPECTED}@{BASELINE_SHA_EXPECTED[:16]}..., got {json.dumps(ob)}")

    authority = {
        "official_baseline": "development-control",
        "c_line_historical_status": "development-control",
        "future_roadmap_item_family": "p2p-development-roadmap",
        "research_adoption_provenance": "research-adoption-ledger",
        "capability_existence_status": "capability-index",
        "owner_current_intent": "OWNER_INPUT_MODEL",
        "external_research": "PROVENANCE_ONLY_NEVER_AUTHORITY",
    }

    overrides = dict(ov.split(":", 1) for ov in override_owner_value) if override_owner_value else {}

    return {
        "OFFICIAL_BASELINE": {"version": ob["version"], "artifact_sha256": ob["artifact_sha256"],
                              "promotion_status": ob.get("promotion_status"), "approval_reference": ob.get("approval_reference")},
        "OWNER_CURRENT_INTENT": {"source": "planning invocation", "explicit_value_overrides": overrides,
                                 "note": "No Owner-intent record exists for this run beyond overrides; Owner Gates are never overridden."},
        "RESEARCH_ADOPTION_RECORDS": ledger["records"],
        "ROADMAP_ITEMS": roadmap["items"],
        "CAPABILITY_RECORDS": [c for c in cap["capabilities"] if isinstance(c, dict)],
        "INTAKE_RECORDS": intake.get("intake_records", []),
        "INTAKE_CLASSIFICATIONS": {r["id"]: r.get("classification", "") for r in intake.get("intake_records", [])},
        "INTAKE_VOCABULARY": intake.get("vocabulary", {}),
        "INTAKE_CONTRACT": intake_contract,
        "CURRENT_EVIDENCE": {i["roadmap_id"]: i.get("current_evidence", "") for i in roadmap["items"]},
        "DEPENDENCIES": {i["roadmap_id"]: i.get("dependencies", []) for i in roadmap["items"]},
        "BLOCKERS": {i["roadmap_id"]: i.get("blockers", []) for i in roadmap["items"]},
        "STATUS": {i["roadmap_id"]: i.get("status") for i in roadmap["items"]},
        "PRIORITY": {i["roadmap_id"]: i.get("priority") for i in roadmap["items"]},
        "OWNER_VALUE": {i["roadmap_id"]: i.get("owner_value", "") for i in roadmap["items"]},
        "SAFETY_MATURITY": {i["roadmap_id"]: i.get("mutation_risk_class", "UNKNOWN") for i in roadmap["items"]},
        "EVIDENCE_GAPS": {i["roadmap_id"]: i.get("target_evidence", "") for i in roadmap["items"]},
        "ARCHITECTURAL_LEVERAGE": {i["roadmap_id"]: i.get("family", "") for i in roadmap["items"]},
        "PROJECT_IMPACT": {i["roadmap_id"]: i.get("project_impact", "UNKNOWN") for i in roadmap["items"]},
        "MUTATION_RISK": {i["roadmap_id"]: i.get("promotion_required", "UNKNOWN") for i in roadmap["items"]},
        "PROMOTION_REQUIREMENT": {i["roadmap_id"]: i.get("promotion_required", "UNKNOWN") for i in roadmap["items"]},
        "NOT_PROVEN": {i["roadmap_id"]: [b for b in i.get("blockers", []) if "NOT_PROVEN" in str(b)] for i in roadmap["items"]},
        "DEFER_REASON": {i["roadmap_id"]: i.get("defer_reason", "") for i in roadmap["items"]},
        "AUTHORITY_ORDER": authority,
        "HASHES": {},  # filled below
    }


# ---------------------------------------------------------------- hash binding
def bind_hashes(inp, repo):
    """Spec §19: bind every canonical source + baseline; stale plan cannot survive drift."""
    h = inp["HASHES"]
    h["p2p_development_roadmap_json_sha256"] = sha256_file(os.path.join(repo, "governance", "p2p-development-roadmap.json"))
    h["p2p_development_roadmap_schema_version"] = "p2p-framework/development-roadmap/1"
    h["research_adoption_ledger_json_sha256"] = sha256_file(os.path.join(repo, "governance", "research-adoption-ledger.json"))
    h["research_adoption_ledger_schema_version"] = "p2p-framework/research-adoption-ledger/1"
    h["capability_index_json_sha256"] = sha256_file(os.path.join(repo, "docs", "p2p-development", "capability-ledger", "capability-index.json"))
    h["development_control_json_sha256"] = sha256_file(os.path.join(repo, "governance", "development-control.json"))
    icp = os.path.join(repo, "governance", "intake-contract.json")
    if os.path.exists(icp):
        h["intake_contract_json_sha256"] = sha256_file(icp)
    ilp = os.path.join(repo, "governance", "research-intake-ledger.json")
    if os.path.exists(ilp):
        h["research_intake_ledger_json_sha256"] = sha256_file(ilp)
    h["official_baseline_version"] = BASELINE_EXPECTED
    h["official_baseline_artifact_sha256"] = BASELINE_SHA_EXPECTED
    h["planning_timestamp_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- coverage gate
def coverage_gate(inp, dctl):
    """Spec §4 (hardened 01A): ROADMAP_COVERAGE_GAP.

    Coverage semantics (status translation, explicit):
      Ledger SELECTED/PLANNED/PARTIAL  -> materially relevant; needs roadmap consideration.
      Ledger SHIPPED/VERIFIED/IMPLEMENTED -> adopted; coverage satisfied.
      Ledger DEFERRED/REJECTED/SUPERSEDED -> excluded with documented reason.
      Ledger DISCOVERED/RESEARCHED        -> not yet selected; not a gap, not counted.
      Ledger UNKNOWN                      -> NEVER satisfies coverage.
      Roadmap PLANNED/PARTIAL items       -> materially relevant candidates.

    v3 additions (INTAKE-CLOSURE-01 spec §§7-9):
      G1 RESEARCH_TO_ROADMAP_REVERSE_COVERAGE
      G2 CAPABILITY_TO_ROADMAP_COVERAGE
      G3 ORPHAN_OWNER_DECISION_DETECTION
      G4 forward check preserved (existing)
    """
    gaps = []
    # ---------------- v3 G1: research -> roadmap reverse coverage ----------
    # Material ledger records (SELECTED/PLANNED/PARTIAL) must have one of:
    #   * explicit reference from a roadmap item (source_research_ids)
    #   * explicit composition into an existing roadmap item (composition_entries)
    #   * explicit DEFER reason attached to the record
    #   * explicit REJECTED/SUPERSEDED state (excluded with documented reason)
    roadmap_id_set = {i["roadmap_id"] for i in inp["ROADMAP_ITEMS"]}
    roadmapped_research = set()
    composed_research = set()
    for i in inp["ROADMAP_ITEMS"]:
        for s in i.get("source_research_ids", []):
            roadmapped_research.add(s)
        for ce in i.get("composition_entries", []) or []:
            rr = ce.get("research_record")
            if rr:
                composed_research.add(rr)
    cap_ids_by_item = set()
    for i in inp["ROADMAP_ITEMS"]:
        for c in i.get("canonical_capability_ids", []) or []:
            cap_ids_by_item.add(c)
    for rec in inp["RESEARCH_ADOPTION_RECORDS"]:
        st = rec.get("status")
        rid = rec["research_id"]
        if st not in LEDGER_MATERIAL_STATUSES:
            continue  # adopted/excluded/non-material records do not need future consideration
        composed = rid in roadmapped_research or rid in composed_research
        defer_ok = bool(rec.get("defer_reason") or rec.get("roadmap_relation", "").startswith("defer"))
        excluded = st in LEDGER_EXCLUDED_STATUSES
        if not composed and not defer_ok and not excluded:
            gaps.append({"reason": "MATERIAL_RESEARCH_WITHOUT_ROADMAP_CONSIDERATION",
                         "research_id": rid, "status": st})
    # ---------------- v3 G2: capability -> roadmap coverage ---------------
    # Spec §8: only capabilities whose state means future work is MATERIALLY
    # INTENDED are gated (not every historical registry entry):
    #   (a) origin_type == OWNER_ACCEPTED_PROPOSAL  (Owner accepted)
    #   (b) cited by a MATERIAL adoption record (canonical_capability_ids)
    # Other PLANNED/PARTIAL caps are documented registry inventory and are
    # logged in registry_entries_excluded_from_gate (explicitly not a gap).
    CAP_FUTURE_WORK_STATES = {"PLANNED", "PARTIAL", "FOUNDATION_READY_WITH_GAP", "OWNER_ACCEPTED_PROPOSAL"}
    adopted_cap_ids = set()
    for r in inp["RESEARCH_ADOPTION_RECORDS"]:
        if r.get("status") in LEDGER_MATERIAL_STATUSES:
            for c in r.get("canonical_capability_ids", []) or []:
                adopted_cap_ids.add(c)
    planned_item_families = {i.get("family") for i in inp["ROADMAP_ITEMS"]
                             if i.get("status") in ("PLANNED", "PARTIAL")}
    # Alias resolution (INTAKE-CLOSURE-01 intake contract): a capability family
    # may be declared equivalent to a roadmap family via the alias table.
    _alias_table = (inp.get("INTAKE_CONTRACT") or {}).get(
        "capability_family_alias_table", {}) or {}
    def effective_families(fam):
        eff = {fam}
        rf = (_alias_table.get(fam) or {}).get("roadmap_family")
        if rf:
            eff.add(rf)
        return eff
    planned_families_expanded = set(planned_item_families)
    for k, v in _alias_table.items():
        if (v or {}).get("roadmap_family") in planned_item_families:
            planned_families_expanded.add(k)
    registry_excluded = []
    for c in inp["CAPABILITY_RECORDS"]:
        cid = c.get("capability_id") or c.get("id") or ""
        st = c.get("status", "")
        if st not in CAP_FUTURE_WORK_STATES:
            continue
        materially_intended = (c.get("origin_type") == "OWNER_ACCEPTED_PROPOSAL") or (cid in adopted_cap_ids)
        if not materially_intended:
            registry_excluded.append(cid)
            continue
        in_item = cid in cap_ids_by_item
        same_family_umbrella = bool(effective_families(c.get("family") or "")
                                    & planned_families_expanded)
        deferral_note = any("defer" in str(v).lower() for v in (
            c.get("roadmap_relation"), c.get("known_gap"), c.get("notes"), ""))
        rejection_note = any(kw in str(v).lower() for kw in ("reject", "superseded") for v in (
            c.get("roadmap_relation"), c.get("known_gap"), c.get("notes"), ""))
        if not (in_item or same_family_umbrella or deferral_note or rejection_note):
            gaps.append({"reason": "FUTURE_WORK_CAPABILITY_WITHOUT_ROADMAP_CONSIDERATION",
                         "capability_id": cid, "status": st})
    # ---------------- v3 G3: orphan accepted-decision detection -----------
    # An ACCEPTED intake record without a matching adoption record is an orphan.
    # An accepted adoption record without a capability record (or roadmapped
    # capability) and without explicit defer/reject is an orphan stage.
    intake_accepted = {r["id"]: r for r in inp["INTAKE_RECORDS"]
                       if r.get("classification", "").upper() == "ACCEPTED"}
    adoption_ids = {r["research_id"] for r in inp["RESEARCH_ADOPTION_RECORDS"]}
    capability_ids = {c.get("capability_id") or c.get("id") or "" for c in inp["CAPABILITY_RECORDS"]}
    for iid, r in intake_accepted.items():
        # matching adoption record: explicit intake_record id reference, or
        # token overlap >= 2 between intake subject and adoption source_name
        subj = (r.get("subject", "") or "").lower()
        subj_tokens = set(t for t in re.split(r"[^a-z0-9]+", subj) if len(t) > 3)
        matched = False
        for a in inp["RESEARCH_ADOPTION_RECORDS"]:
            if a.get("intake_record") == iid:
                matched = True
                break
            aname = (a.get("source_name", "") or "").lower()
            aname_tokens = set(t for t in re.split(r"[^a-z0-9]+", aname) if len(t) > 3)
            if len(subj_tokens & aname_tokens) >= 2:
                matched = True
                break
        if not matched:
            gaps.append({"reason": "ACCEPTED_INTAKE_WITHOUT_ADOPTION_RECORD",
                         "intake_id": iid, "subject": r.get("subject", "")})
    for a in inp["RESEARCH_ADOPTION_RECORDS"]:
        if a.get("status") not in LEDGER_MATERIAL_STATUSES:
            continue
        caps = a.get("canonical_capability_ids", []) or []
        has_cap = any(c in capability_ids for c in caps)
        roadmapped = a["research_id"] in roadmapped_research or a["research_id"] in composed_research
        deferred = bool(a.get("defer_reason") or str(a.get("roadmap_relation", "")).startswith("defer"))
        excluded = a.get("status") in LEDGER_EXCLUDED_STATUSES
        if not has_cap and not roadmapped and not deferred and not excluded:
            gaps.append({"reason": "MATERIAL_ADOPTION_WITHOUT_CAPABILITY_OR_ROADMAP",
                         "research_id": a["research_id"]})
    owner_selected = []
    for item in inp["ROADMAP_ITEMS"]:
        if item.get("status") in ("PLANNED", "PARTIAL"):
            owner_selected.append(item["roadmap_id"])
    for rec in inp["RESEARCH_ADOPTION_RECORDS"]:
        st = rec.get("status")
        if st in LEDGER_MATERIAL_STATUSES:
            owner_selected.append(rec["research_id"])
        elif st not in LEDGER_ADOPTED_STATUSES and st not in LEDGER_EXCLUDED_STATUSES and st != "UNKNOWN":
            # DISCOVERED/RESEARCHED: not material yet (documented, not a gap)
            pass
        # UNKNOWN explicitly never satisfies — it is silently ignored only as non-evidence,
        # and a UNKNOWN ledger record cannot be the reason a selected direction is dropped:
        # owner-selected candidates must still have a durable record (checked below).
    # every candidate is present in at least one canonical plan input -> no silent forgetting
    missing_records = []
    for oid, _ in inp["OWNER_CURRENT_INTENT"]["explicit_value_overrides"].items():
        known = {i["roadmap_id"] for i in inp["ROADMAP_ITEMS"]} | {r["research_id"] for r in inp["RESEARCH_ADOPTION_RECORDS"]}
        if oid not in known:
            missing_records.append(oid)
    if missing_records:
        gaps.append({"reason": "OWNER_SELECTED_CAPABILITY_RECORD_MISSING", "ids": missing_records})
    # forward-reference check: roadmap items citing research ids absent from the ledger
    ledger_ids = {r["research_id"] for r in inp["RESEARCH_ADOPTION_RECORDS"]}
    dangling_refs = {}
    for i in inp["ROADMAP_ITEMS"]:
        for s in i.get("source_research_ids", []):
            if s not in ledger_ids:
                dangling_refs.setdefault(i["roadmap_id"], []).append(s)
    if dangling_refs:
        gaps.append({"reason": "SOURCE_RESEARCH_ID_MISSING_FROM_LEDGER", "refs": dangling_refs})
    return {
        "ROADMAP_COVERAGE_GAP": len(gaps) > 0,
        "gaps": gaps,
        "owner_selected_candidates": owner_selected,
        "status_translation": {
            "ledger_material": sorted(LEDGER_MATERIAL_STATUSES),
            "ledger_adopted": sorted(LEDGER_ADOPTED_STATUSES),
            "ledger_excluded_with_reason": sorted(LEDGER_EXCLUDED_STATUSES),
            "unknown_never_satisfies": True,
        },
        "RESEARCH_TO_ROADMAP_REVERSE_COVERAGE": all(
            g["reason"] != "MATERIAL_RESEARCH_WITHOUT_ROADMAP_CONSIDERATION" for g in gaps),
        "CAPABILITY_TO_ROADMAP_COVERAGE": all(
            g["reason"] != "FUTURE_WORK_CAPABILITY_WITHOUT_ROADMAP_CONSIDERATION" for g in gaps),
        "CAPABILITY_REGISTRY_ENTRIES_EXCLUDED_FROM_GATE": registry_excluded,
        "ORPHAN_OWNER_DECISIONS": [g for g in gaps if "ACCEPTED_INTAKE_WITHOUT_ADOPTION_RECORD" == g["reason"]
                                   or "MATERIAL_ADOPTION_WITHOUT_CAPABILITY_OR_ROADMAP" == g["reason"]],
        "INTAKE_RECORDS_CONSUMED": len(inp["INTAKE_RECORDS"]),
        "INTAKE_CONTRACT_BOUND": bool(inp.get("INTAKE_CONTRACT")),
    }


# ---------------------------------------------------------------- dependency graph
def classify_dependencies(inp):
    """Spec §6: per-item dependency graph class with justification (hardened 01A §4).

    Deterministic mapping for known blocked statuses:
      BLOCKED  + blocker mentions evidence/availability/NOT_PROVEN
               -> BLOCKED_BY_EXTERNAL_EVIDENCE
      BLOCKED  + otherwise (or unsatisfied dependency references)
               -> BLOCKED_BY_DEPENDENCY
      BLOCKED_TERMINAL -> same mapping, reason tagged terminal
      genuinely unrecognized/ambiguous status -> UNKNOWN (fail-closed elsewhere)
    KNOWN_BLOCKED != UNKNOWN: a blocked item with a deterministically classifiable cause
    is never returned as UNKNOWN.
    """
    status = inp["STATUS"]
    ids = list(status.keys())
    name_to_id = {}
    for i in inp["ROADMAP_ITEMS"]:
        name_to_id[i["roadmap_id"]] = i["roadmap_id"]
        alias = re.sub(r"^RM-", "", i["roadmap_id"])
        if alias.startswith("C") and alias not in name_to_id:
            name_to_id[alias] = i["roadmap_id"]

    ext_ev_re = re.compile(r"EVIDENCE|UNAVAILABLE|NOT_PROVEN|MISSING.*EVIDENCE|NOT_AVAILABLE", re.IGNORECASE)

    def resolve_dep_class(dep_text):
        """Recursively check whether a dependency reference is satisfied (terminal) or not."""
        for token in re.split(r"[,;+]|\sor\s", dep_text):
            for frag in re.findall(r"[A-Za-z0-9._-]+", token):
                rid = name_to_id.get(frag)
                if rid is None:
                    continue
                dst = status.get(rid)
                if dst in TERMINAL_STATUSES:
                    continue
                if dst == "DEFERRED":
                    return "OWNER_DEFERRED", f"depends on Owner-deferred {rid}"
                if dst is None or dst not in TERMINAL_STATUSES:
                    bl = inp["BLOCKERS"].get(rid, [])
                    if bl and ext_ev_re.search("; ".join(str(b) for b in bl)):
                        return ("BLOCKED_BY_EXTERNAL_EVIDENCE", f"depends on {rid}: " + "; ".join(str(b) for b in bl)[:200])
                    return "BLOCKED_BY_DEPENDENCY", f"depends on {rid} (status {dst}, not terminal)"
        return None, None

    def classify_blocked(rid, terminal=False):
        blockers = [str(b) for b in inp["BLOCKERS"].get(rid, [])]
        ext_blocked = [b for b in blockers if ext_ev_re.search(b)]
        if ext_blocked:
            cls = "BLOCKED_BY_EXTERNAL_EVIDENCE"
            why = "; ".join(ext_blocked)[:300]
        else:
            # unsatisfied dependency references classify the block too
            dep_class, dep_why = resolve_dep_class(" ".join(inp["DEPENDENCIES"].get(rid, [])))
            if dep_class and dep_class not in ("DONE_SHIPPED_VERIFIED", "UNKNOWN"):
                cls, why = dep_class, dep_why
            else:
                cls = "BLOCKED_BY_DEPENDENCY"
                why = "; ".join(blockers)[:300] or "status BLOCKED without resolvable blockers"
        if terminal:
            cls = cls + "_TERMINAL_PATTERN" if False else cls  # classification kept deterministic; terminality carried in reason
            why = "(terminal) " + why
        return cls, why

    graph = {}
    for rid in ids:
        st = status[rid]
        if st in TERMINAL_STATUSES:
            cls, why = "DONE_SHIPPED_VERIFIED", f"terminal status {st}"
        elif st == "DEFERRED":
            cls, why = "OWNER_DEFERRED", inp["DEFER_REASON"].get(rid, "explicit Owner deferral")
        elif st == "REJECTED":
            cls, why = "SUPERSEDED", "rejected pattern — permanent"
        elif st in ("BLOCKED", "BLOCKED_TERMINAL"):
            cls, why = classify_blocked(rid, terminal=(st == "BLOCKED_TERMINAL"))
        elif st == "PARTIAL":
            cls, why = "READY_NOW", "partial evidence progress; no blocker; continuation candidate"
        elif st != "PLANNED":
            cls, why = "UNKNOWN", f"status {st} not in deterministic vocab"
        else:
            blockers = [str(b) for b in inp["BLOCKERS"].get(rid, [])]
            not_proven = [b for b in blockers if "NOT_PROVEN" in str(b)]
            ext_blocked = [b for b in blockers if ext_ev_re.search(b)]
            if ext_blocked:
                cls, why = "BLOCKED_BY_EXTERNAL_EVIDENCE", "; ".join(ext_blocked)[:300]
            elif blockers:
                cls, why = "BLOCKED_BY_DEPENDENCY", "; ".join(blockers)[:300]
            elif not_proven:
                cls, why = "BLOCKED_BY_EXTERNAL_EVIDENCE", "; ".join(not_proven)[:300]
            else:
                dep_class, dep_why = resolve_dep_class(" ".join(inp["DEPENDENCIES"].get(rid, [])))
                if dep_class and dep_class not in ("DONE_SHIPPED_VERIFIED", "UNKNOWN"):
                    cls, why = dep_class, dep_why
                else:
                    cls, why = "READY_NOW", inp.get("PROJECT_IMPACT", {}).get(rid, "") or "no blockers"
        graph[rid] = {"class": cls, "reason": why, "status": st}
    return graph


# ---------------------------------------------------------------- ranking
def owner_value_bucket(text, oid):
    """Spec §7: deterministic bucket from durable text. Explicit priority field scales it."""
    t = (text or "").lower()
    score = 1.0
    if "giá trị" in t or "value" in t and ("cao" in t or "high" in t) or "mọi mục tiêu" in t or "bắt đầu" in t or "first" in t:
        score = 3.0
    elif "zero-to-project" in t or "z2p" in t or "todo" in t or "project" in t and ("tạo dự án" in t or "intent" in t):
        score = 3.0
    elif "bị block" in t or "blocked" in t or "unavailable" in t:
        score = 0.5
    return score


def dependency_necessity_factors(inp, graph):
    """Spec 01A §7: real graph-leverage signals, deterministic, documented, testable,
    derived solely from the canonical dependency graph. Returns per-item dict of
    normalized factors whose sum is the dependency_necessity component (max 2.0).

    Signals (no double counting with owner_value):
      1. blocked_dependents_ratio — share of non-terminal roadmap items that (directly or
         transitively) cannot proceed without this item, weighted by their strategic class.
         Only items currently blocked/deferred by this item count (removing this item's
         unblock removes their blocking edge).
      2. terminal_prerequisite_bonus — 1.0 if the item is a stated prerequisite of any
         terminal North-Star direction (Z2P/Large-Goal) or of multiple other items.
      3. blocking_edge_depth — length of the longest chain of blocked items downstream.
    Factor values in [0, 1]; component = 2.0 * normalized sum.
    """
    ids = [i["roadmap_id"] for i in inp["ROADMAP_ITEMS"]]
    name_to_id = {}
    for i in inp["ROADMAP_ITEMS"]:
        name_to_id[i["roadmap_id"]] = i["roadmap_id"]
        alias = re.sub(r"^RM-", "", i["roadmap_id"])
        if alias.startswith("C") and alias not in name_to_id:
            name_to_id[alias] = i["roadmap_id"]

    def mentioned_deps(rid):
        out = []
        for dep_text in inp["DEPENDENCIES"].get(rid, []):
            for frag in re.findall(r"[A-Za-z0-9._-]+", dep_text):
                r = name_to_id.get(frag)
                if r is not None and r != rid:
                    out.append(r)
        return out

    # direct + transitive downstream (items that depend on rid)
    dependents = {rid: [] for rid in ids}
    for rid in ids:
        for dep in mentioned_deps(rid):
            dependents.setdefault(dep, []).append(rid)

    def transitive_downstream(rid, seen=None):
        seen = seen or set()
        for d in dependents.get(rid, []):
            if d in seen:
                continue
            seen.add(d)
            transitive_downstream(d, seen)
        return seen

    # strategic weight of a downstream item: blocked high-value ones count more
    def downstream_weight(dep_rid):
        cls = graph.get(dep_rid, {}).get("class", "")
        if cls in ("BLOCKED_BY_DEPENDENCY", "BLOCKED_BY_EXTERNAL_EVIDENCE"):
            return 1.0
        if cls == "OWNER_DEFERRED":
            return 0.5
        return 0.0

    north_star = {"RM-Z2P", "RM-PRIORITY-LARGE-GOAL"}

    factors = {}
    for rid in ids:
        ds = transitive_downstream(rid)
        blocked_ds = [d for d in ds if downstream_weight(d) > 0]
        # 1. blocked_dependents_ratio: items unblockable without rid, relative to all non-terminal
        non_terminal = [i for i in ids if graph.get(i, {}).get("class") not in
                        ("DONE_SHIPPED_VERIFIED", "SUPERSEDED") and i != rid]
        ratio = len(blocked_ds) / max(len(non_terminal), 1)
        # 2. terminal_prerequisite_bonus: direct prerequisite of North-Star or 2+ items
        term_bonus = 1.0 if (set(dependents.get(rid, [])) & north_star) else 0.0
        if len(dependents.get(rid, [])) >= 2:
            term_bonus = max(term_bonus, 0.5)
        # 3. blocking_edge_depth: longest blocked chain downstream
        depth = 0
        frontier = [rid]
        visited = {rid}
        while frontier:
            nxt = []
            for f in frontier:
                for d in dependents.get(f, []):
                    if d not in visited and graph.get(d, {}).get("class") not in (
                            "DONE_SHIPPED_VERIFIED", "SUPERSEDED"):
                        visited.add(d)
                        nxt.append(d)
                        depth += 1
            frontier = nxt
        depth_norm = min(depth / 3.0, 1.0)
        factors[rid] = {
            "blocked_dependents_ratio": ratio,
            "terminal_prerequisite_bonus": term_bonus,
            "blocking_edge_depth": depth,
            "raw": 0.5 * ratio + term_bonus + 0.5 * depth_norm,
        }
    raw_max = max((f["raw"] for f in factors.values()), default=1.0)
    if raw_max <= 0:
        raw_max = 1.0
    return {rid: min(1.0, f["raw"] / raw_max) for rid, f in factors.items()}


def rank_items(inp, graph):
    """Spec §7 (hardened 01A): deterministic ranking on ALL five canonical factors.

    Score = w_owner*bucket + w_dep*necessity + w_safety*maturity + w_ev*gap + w_lever*leverage
    All five weights in WEIGHTS are consumed. Identical truth -> identical order (id tiebreak).
    """
    dep = dependency_necessity_factors(inp, graph)
    scored = []
    for item in inp["ROADMAP_ITEMS"]:
        rid = item["roadmap_id"]
        ov = owner_value_bucket(inp["OWNER_VALUE"].get(rid, ""), rid)
        safety = 2.0 if inp["SAFETY_MATURITY"].get(rid) == "READ_ONLY" else 1.0
        ev = (inp["CURRENT_EVIDENCE"].get(rid, "") or "").lower()
        gap = 1.0 if "done" in ev and "verified" in ev else (0.5 if "done" in ev else 0.0)
        fam = (inp["ARCHITECTURAL_LEVERAGE"].get(rid, "") or "").lower()
        leverage = 1.5 if "context" in fam or "owner_intent" in fam or "execution" in fam else 1.0
        nec = dep[rid]
        score = (WEIGHTS["owner_value"] * ov + WEIGHTS["dependency_necessity"] * nec +
                 WEIGHTS["safety_maturity"] * safety +
                 WEIGHTS["evidence_gap"] * gap + WEIGHTS["architectural_leverage"] * leverage)
        scored.append((round(score, 8), rid, {"owner_value": ov, "dependency_necessity": nec,
                                              "safety_maturity": safety, "evidence_gap": gap,
                                              "architectural_leverage": leverage}))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored


# ---------------------------------------------------------------- plan output
def build_plan(inp, graph, scored, coverage, dctl):
    strategic = [{"rank": r + 1, "roadmap_id": rid, "score": round(sc, 4)} for r, (sc, rid, _) in enumerate(scored)]
    executable = []
    for (sc, rid, comps) in scored:
        if graph[rid]["class"] == "READY_NOW":
            executable.append({"roadmap_id": rid, "score": round(sc, 4), "graph_class": "READY_NOW"})
    blocked_high_value = [
        {"roadmap_id": rid, "class": g["class"], "reason": g["reason"]}
        for (sc, rid, comps) in scored
        if (g := graph[rid])["class"] in ("BLOCKED_BY_DEPENDENCY", "BLOCKED_BY_EXTERNAL_EVIDENCE")
    ]
    deferred = [{"roadmap_id": rid, "defer_reason": inp["DEFER_REASON"].get(rid, "")}
                for (sc, rid, _) in scored if graph[rid]["class"] == "OWNER_DEFERRED"]
    unknown_items = [{"roadmap_id": rid, "status": graph[rid]["status"], "reason": graph[rid]["reason"]}
                     for (sc, rid, _) in scored if graph[rid]["class"] == "UNKNOWN"]
    partials = [i["roadmap_id"] for i in inp["ROADMAP_ITEMS"] if inp["STATUS"].get(i["roadmap_id"]) == "PARTIAL"]

    # 01A §11: recommendation forbidden while coverage admits a material omission
    plan_complete = not coverage["ROADMAP_COVERAGE_GAP"]
    rec = executable[0] if executable and plan_complete else None

    # WHY analysis (evidence-bound, with score decomposition)
    score_by_id = {rid: (sc, comps) for sc, rid, comps in scored}
    why_this = []
    score_breakdown = None
    why_not = []
    if rec:
        rid = rec["roadmap_id"]
        sc, comps = score_by_id[rid]
        score_breakdown = {
            "formula": "SCORE = 3.0*owner_value_bucket + 2.0*dependency_necessity + 1.5*safety_maturity + 1.0*evidence_gap + 1.5*architectural_leverage",
            "weights": {k: v for k, v in WEIGHTS.items()},
            "contributions": {
                "owner_value": round(WEIGHTS["owner_value"] * comps["owner_value"], 4),
                "dependency_necessity": round(WEIGHTS["dependency_necessity"] * comps["dependency_necessity"], 4),
                "safety_maturity": round(WEIGHTS["safety_maturity"] * comps["safety_maturity"], 4),
                "evidence_gap": round(WEIGHTS["evidence_gap"] * comps["evidence_gap"], 4),
                "architectural_leverage": round(WEIGHTS["architectural_leverage"] * comps["architectural_leverage"], 4),
            },
            "total": round(sc, 4),
        }
        why_this = [
            f"score {score_breakdown['total']:.4f} highest among READY_NOW items",
            f"owner_value contribution {score_breakdown['contributions']['owner_value']:.4f} (bucket {comps['owner_value']}) from durable text: {(inp['OWNER_VALUE'].get(rid) or '')[:140]}",
            f"dependency_necessity contribution {score_breakdown['contributions']['dependency_necessity']:.4f} (normalized factor {comps['dependency_necessity']:.4f})",
            f"safety_maturity contribution {score_breakdown['contributions']['safety_maturity']:.4f} (mutation_risk_class={inp['SAFETY_MATURITY'].get(rid)})",
            f"evidence_gap contribution {score_breakdown['contributions']['evidence_gap']:.4f}",
            f"architectural_leverage contribution {score_breakdown['contributions']['architectural_leverage']:.4f} (family={inp['ARCHITECTURAL_LEVERAGE'].get(rid)})",
            f"graph_class={graph[rid]['class']}; project_impact={inp['PROJECT_IMPACT'].get(rid)}; promotion_required={inp['PROMOTION_REQUIREMENT'].get(rid)}",
        ]
        # only cite blockage/leverage of specific items when graph edges prove it
        for (sc2, other, comps2) in scored:
            if other == rid or graph[other]["class"] != "READY_NOW":
                continue
            if sc2 > sc:
                why_not.append(f"{other}: higher score but class={graph[other]['class']} ({graph[other]['reason'][:150]})")
        for top_strategic in strategic[:2]:
            tsr = top_strategic["roadmap_id"]
            if tsr != rid and graph[tsr]["class"] != "READY_NOW":
                why_not.append(f"{tsr}: STRATEGIC_PRIORITY #{top_strategic['rank']} but {graph[tsr]['class']} ({graph[tsr]['reason'][:150]})")
    else:
        score_breakdown = None
        why_this = ["no executable READY_NOW recommendation — planner refuses definitive next-goal recommendation"]
        why_not = ["no READY_NOW item exists or coverage gap blocks planning"]

    status = "PLANNING_COMPLETE" if plan_complete and rec else (
        "BLOCKED / ROADMAP_COVERAGE_GAP" if coverage["ROADMAP_COVERAGE_GAP"] else
        "NO_EXECUTABLE_GOAL")

    plan = {
        "planner": "p2p_roadmap_planner",
        "version": VERSION,
        "spec_goal": SPEC_GOAL,
        "OFFICIAL_BASELINE": inp["OFFICIAL_BASELINE"],
        "HASHES": inp["HASHES"],
        "AUTHORITY_ORDER": inp["AUTHORITY_ORDER"],
        "PLANNING_STATUS": status,
        "PLAN_COMPLETE": plan_complete,
        "ROADMAP_COVERAGE_GATE": coverage,
        "DEPENDENCY_GRAPH": graph,
        "STRATEGIC_PRIORITY_LIST": strategic,
        "NEXT_EXECUTABLE_GOALS": executable,
        "BLOCKED_HIGH_VALUE_GOALS": blocked_high_value,
        "OWNER_DEFERRED_ITEMS": deferred,
        "UNKNOWN_STATUS_ITEMS": unknown_items,
        "RELEVANT_PARTIAL_CAPABILITIES": partials,
        "ROADMAP_COVERAGE_GAPS": coverage["gaps"],
        "NOT_PROVEN_DEPENDENCIES": inp["NOT_PROVEN"],
        "RECOMMENDED_NEXT_GOAL": rec["roadmap_id"] if rec else None,
        "SCORE_BREAKDOWN": score_breakdown,
        "WHY_THIS_GOAL": why_this,
        "WHY_NOT_HIGHER_PRIORITY_ITEMS": why_not,
        "REQUIRED_OWNER_DECISION": ("Approve or reject the planner-recommended next P2P development Goal." if rec else
                                    "No executable Goal — Owner must unblock or defer; planner refuses auto-start."),
        "EVIDENCE_POINTERS": [i.get("current_evidence", "")[:200] for i in inp["ROADMAP_ITEMS"] if i.get("current_evidence")][:10],
        "PLANNER_SELECTION_DOES_NOT_AUTO_EXECUTE": True,
        "ROADMAP_MANUAL_REENTRY_REQUIRED": "NO — planner reads canonical JSON files directly; no transcription into prompt",
    }
    return plan


# ---------------------------------------------------------------- beginner view
def beginner_view(plan, inp):
    """Spec 01A §10: beginner view bound to the ACTUALLY selected roadmap item —
    title, owner value, mutation risk, project impact, promotion requirement,
    dependencies/blockers. No stale hardcoded planner wording."""
    rec = plan["RECOMMENDED_NEXT_GOAL"]
    item = None
    if rec:
        for i in inp["ROADMAP_ITEMS"]:
            if i["roadmap_id"] == rec:
                item = i
                break
    impact_answer = (
        f"KHÔNG mutate dự án — goal này là {item.get('title') if item else ''}; "
        f"project_impact={item.get('project_impact', 'UNKNOWN') if item else 'UNKNOWN'}, "
        f"mutation_risk_class={item.get('mutation_risk_class', 'UNKNOWN') if item else 'UNKNOWN'}, "
        "không chạm Game Truyện / Gia Phả / Logistics ở giai đoạn lập kế hoạch."
    )
    if not item:
        impact_answer = "KHÔNG — không có Goal nào được đề xuất; planner chỉ đọc, không mutate Game Truyện, Gia Phả, Logistics."
    deps_blockers = ""
    if item:
        d = "; ".join(item.get("dependencies", []) or ["không có"])
        b = "; ".join(item.get("blockers", []) or ["không có"])
        deps_blockers = f"dependencies: {d}; blockers: {b}"
    answer_goal = (f"{item.get('title')} ({item.get('roadmap_id')}) — {deps_blockers}"
                   if item else plan["REQUIRED_OWNER_DECISION"])
    answer_why = "; ".join(plan["WHY_THIS_GOAL"][:3]) if (plan["WHY_THIS_GOAL"] and item) else plan["REQUIRED_OWNER_DECISION"]
    rows = [
        ("P2P muốn làm gì tiếp?", rec if rec else "Không có Goal nào an toàn để bắt đầu ngay."),
        ("Goal đó là gì?", answer_goal),
        ("Tại sao (điểm từng yếu tố)?", answer_why),
        ("Rủi ro đột biến / đụng project?", impact_answer),
        ("Yêu cầu promotion cho goal này?",
         f"promotion_required={item.get('promotion_required', 'UNKNOWN') if item else 'UNKNOWN'}"),
        ("Việc quan trọng hơn nào chưa làm được ngay?",
         "; ".join(f"{b['roadmap_id']} ({b['class']})" for b in plan["BLOCKED_HIGH_VALUE_GOALS"][:5]) or "không có"),
        ("Cái gì đang bị block?",
         "; ".join(f"{b['roadmap_id']}: {b['reason'][:120]}" for b in plan["BLOCKED_HIGH_VALUE_GOALS"]) or "không có"),
        ("Cái gì Owner đã hoãn?",
         "; ".join(f"{d['roadmap_id']}" for d in plan["OWNER_DEFERRED_ITEMS"]) or "không có"),
        ("Owner cần quyết định gì?", plan["REQUIRED_OWNER_DECISION"]),
    ]
    return {"beginner_owner_view_vn": {q: a for q, a in rows}}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--planning-input", default=None, help="optional Owner intent input model JSON (path)")
    ap.add_argument("--override-owner-value", action="append", default=[],
                    help="owner-value overrides: RM-ID:<high|medium|low> (repeatable)")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    # fail-closed: refuse when any roadmap item has a status outside the deterministic vocab
    tmp_inp = build_input_model(args.repo, args.override_owner_value)
    for i in tmp_inp["ROADMAP_ITEMS"]:
        if i.get("status") not in ALLOWED_ROADMAP_ITEM_STATUS:
            raise PlannerError(f"UNKNOWN ROADMAP ITEM STATUS — {i.get('roadmap_id')}: {i.get('status')} not in canonical vocab")
    inp = tmp_inp
    if args.planning_input and os.path.exists(args.planning_input):
        extra = json.load(open(args.planning_input))
        if isinstance(extra, dict):
            inp["OWNER_CURRENT_INTENT"].update(extra)

    bind_hashes(inp, args.repo)

    dctl = load_json(os.path.join(args.repo, "governance", "development-control.json"), "development-control")
    coverage = coverage_gate(inp, dctl)

    graph = classify_dependencies(inp)
    scored = rank_items(inp, graph)
    plan = build_plan(inp, graph, scored, coverage, dctl)
    plan.update(beginner_view(plan, inp))

    out = args.output or os.path.join(args.repo, "reports", "planner", "P2P-PLANNER-RUN-02.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
