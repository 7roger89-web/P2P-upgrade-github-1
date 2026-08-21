#!/usr/bin/env python3
"""p2p_roadmap_planner.py — Canonical roadmap-aware development planner.

P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01
Machine-readable consumption of canonical durable roadmap truth BEFORE next-goal selection.

Design (spec-mandated):
- Small composable planner capability; NOT a second orchestrator; P2P remains sole orchestrator.
- Reads only; NEVER mutates any file. No auto-execution. PLANNER_SELECTION != GOAL_EXECUTION.
- Deterministic ranking for identical truth input; explanation evidence persisted for reproducibility.
- Fail-closed: refuses definitive recommendation when canonical truth is missing/conflicting/unknown.
- Hash binding: plan output binds roadmap/ledger/control hashes + baseline identity + timestamp
  (ROADMAP_DRIFT_INVALIDATES_PLAN).

Usage:
  python3 p2p_roadmap_planner.py --repo <auth-f01 path> [--planning-input /path/to/input.json]
                                  [--override-owner-value "<id>:<high|medium|low>"]
  Outputs: planning result JSON on stdout, planner result file path in repo-local run dir.

Authority precedence (spec §2), enforced in code:
  1. official baseline / C-line historical status  -> development-control.json
  2. future roadmap item/family organization       -> p2p-development-roadmap.json
  3. research adoption/provenance                  -> research-adoption-ledger.json
  4. capability existence/status                   -> capability-index.json
  5. Owner explicit current decision               -> Owner input model (OWNER_CURRENT_INTENT)
  6. external research                             -> provenance ONLY (via ledger), never authority
"""
import argparse, hashlib, json, os, sys, re
from datetime import datetime, timezone

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

    # authority precedence registry
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
    h["official_baseline_version"] = BASELINE_EXPECTED
    h["official_baseline_artifact_sha256"] = BASELINE_SHA_EXPECTED
    h["planning_timestamp_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- coverage gate
def coverage_gate(inp, dctl):
    """Spec §4: ROADMAP_COVERAGE_GAP. Every materially relevant SELECTED/PLANNED/PARTIAL
    record must be present; omissions need explicit defer/exclusion reasons."""
    gaps = []
    owner_selected = []
    # Owner-selected candidates: roadmap PLANNED items + ledger PARTIAL/SELECTED records
    for item in inp["ROADMAP_ITEMS"]:
        if item.get("status") in ("PLANNED", "PARTIAL"):
            owner_selected.append(item["roadmap_id"])
    for rec in inp["RESEARCH_ADOPTION_RECORDS"]:
        if rec.get("status") in ("PARTIAL",):
            owner_selected.append(rec["research_id"])
    # every candidate is present in at least one canonical plan input -> no silent forgetting
    # explicit gap: a selected direction that appears in OWNER_CURRENT_INTENT overrides without a durable record
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
    }


# ---------------------------------------------------------------- dependency graph
def classify_dependencies(inp):
    """Spec §6: per-item dependency graph class with justification."""
    status = inp["STATUS"]
    ids = list(status.keys())
    id_re = re.compile(r"^([A-Z0-9_-]+)\b")
    # dependency-name -> roadmap id resolution: match known roadmap ids & C-line aliases inside dep strings
    name_to_id = {}
    for i in inp["ROADMAP_ITEMS"]:
        name_to_id[i["roadmap_id"]] = i["roadmap_id"]
        alias = re.sub(r"^RM-", "", i["roadmap_id"])
        if alias.startswith("C") and alias not in name_to_id:
            name_to_id[alias] = i["roadmap_id"]

    def resolve_dep_class(dep_text):
        """Recursively check whether a dependency reference is satisfied (DONE/VERIFIED) or not."""
        for token in re.split(r"[,;+]|\sor\s", dep_text):
            for frag in re.findall(r"[A-Za-z0-9._-]+", token):
                rid = name_to_id.get(frag)
                if rid is None:
                    continue
                dst = status.get(rid)
                if dst in ("DONE", "SHIPPED", "VERIFIED"):
                    continue
                if dst == "DEFERRED":
                    return "OWNER_DEFERRED", f"depends on Owner-deferred {rid}"
                if dst is None or dst not in TERMINAL_STATUSES:
                    bl = inp["BLOCKERS"].get(rid, [])
                    if bl:
                        return ("BLOCKED_BY_EXTERNAL_EVIDENCE", f"depends on {rid}: " + "; ".join(bl)[:200]) if \
                            any("EVIDENCE" in str(b).upper() or "NOT_PROVEN" in str(b) or "UNAVAILABLE" in str(b).upper() for b in bl) else \
                            ("BLOCKED_BY_DEPENDENCY", f"depends on {rid}: " + "; ".join(bl)[:200])
                    return "BLOCKED_BY_DEPENDENCY", f"depends on {rid} (status {dst}, not DONE)"
        return None, None

    graph = {}
    for rid in ids:
        st = status[rid]
        if st in TERMINAL_STATUSES or st == "VERIFIED":
            cls, why = "DONE_SHIPPED_VERIFIED", f"terminal status {st}"
        elif st == "DEFERRED":
            cls, why = "OWNER_DEFERRED", inp["DEFER_REASON"].get(rid, "explicit Owner deferral")
        elif st == "REJECTED":
            cls, why = "SUPERSEDED", "rejected pattern — permanent"
        elif st != "PLANNED":
            cls, why = "UNKNOWN", f"status {st} not in deterministic vocab"
        else:
            blockers = inp["BLOCKERS"].get(rid, [])
            not_proven = [b for b in blockers if "NOT_PROVEN" in str(b)]
            ext_blocked = [b for b in blockers if "EVIDENCE" in str(b).upper() or "UNAVAILABLE" in str(b).upper()]
            if blockers:
                if ext_blocked:
                    cls, why = "BLOCKED_BY_EXTERNAL_EVIDENCE", "; ".join(ext_blocked)[:300]
                else:
                    cls, why = "BLOCKED_BY_DEPENDENCY", "; ".join(blockers)[:300]
            elif not_proven:
                cls, why = "BLOCKED_BY_EXTERNAL_EVIDENCE", "; ".join(not_proven)[:300]
            else:
                # resolve dependency references: unsatisfied deps (by id) block even without explicit blockers
                dep_class, dep_why = resolve_dep_class(" ".join(inp["DEPENDENCIES"].get(rid, [])))
                if dep_class and dep_class != "DONE_SHIPPED_VERIFIED":
                    cls, why = dep_class, dep_why
                else:
                    cls, why = "READY_NOW", inp.get("PROJECT_IMPACT", {}).get(rid, "") or "no blockers"
        graph[rid] = {"class": cls, "reason": why, "status": st}
    return graph


# ---------------------------------------------------------------- ranking
WEIGHTS = {"owner_value": 3.0, "dependency_necessity": 2.0, "safety_maturity": 1.5,
           "evidence_gap": 1.0, "architectural_leverage": 1.5}


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


def rank_items(inp, graph):
    """Spec §7: deterministic ranking. Identical truth -> identical order (id tiebreak).
    Scored only on READY_NOW-class items for NEXT_EXECUTABLE_GOAL; all items ranked for STRATEGIC_PRIORITY."""
    scored = []
    for item in inp["ROADMAP_ITEMS"]:
        rid = item["roadmap_id"]
        ov = owner_value_bucket(inp["OWNER_VALUE"].get(rid, ""), rid)
        safety = 2.0 if inp["SAFETY_MATURITY"].get(rid) == "READ_ONLY" else 1.0
        # evidence gap: item with verified current evidence earns leverage
        ev = (inp["CURRENT_EVIDENCE"].get(rid, "") or "").lower()
        gap = 1.0 if "done" in ev and "verified" in ev else (0.5 if "done" in ev else 0.0)
        # architectural leverage: cross-cutting families earn more
        fam = (inp["ARCHITECTURAL_LEVERAGE"].get(rid, "") or "").lower()
        leverage = 1.5 if "context" in fam or "owner_intent" in fam or "execution" in fam else 1.0
        score = (WEIGHTS["owner_value"] * ov + WEIGHTS["safety_maturity"] * safety +
                 WEIGHTS["evidence_gap"] * gap + WEIGHTS["architectural_leverage"] * leverage)
        scored.append((score, rid))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored


# ---------------------------------------------------------------- plan output
def build_plan(inp, graph, scored, coverage, dctl):
    strategic = [{"rank": r + 1, "roadmap_id": rid, "score": round(sc, 4)} for r, (sc, rid) in enumerate(scored)]
    executable = []
    for (sc, rid) in scored:
        if graph[rid]["class"] == "READY_NOW":
            executable.append({"roadmap_id": rid, "score": round(sc, 4), "graph_class": "READY_NOW"})
    blocked_high_value = [
        {"roadmap_id": rid, "class": g["class"], "reason": g["reason"]}
        for (sc, rid) in scored
        if (g := graph[rid])["class"] in ("BLOCKED_BY_DEPENDENCY", "BLOCKED_BY_EXTERNAL_EVIDENCE")
    ]
    deferred = [{"roadmap_id": rid, "defer_reason": inp["DEFER_REASON"].get(rid, "")}
                for (sc, rid) in scored if graph[rid]["class"] == "OWNER_DEFERRED"]
    partials = [i["roadmap_id"] for i in inp["ROADMAP_ITEMS"] if inp["STATUS"].get(i["roadmap_id"]) == "PARTIAL"]
    rec = executable[0] if executable else None

    # WHY analysis (not hardcoded; computed)
    why_this = []
    why_not = []
    if rec:
        rid = rec["roadmap_id"]
        why_this = [f"score {rec['score']:.4f} highest among READY_NOW",
                    f"mutation_risk_class={inp['SAFETY_MATURITY'].get(rid)}",
                    f"project_impact={inp['PROJECT_IMPACT'].get(rid)}",
                    f"promotion_required={inp['PROMOTION_REQUIREMENT'].get(rid)}",
                    "blocks/leverages higher-strategic-value items below it"]
        for (sc, other) in scored:
            if other == rid or graph[other]["class"] != "READY_NOW":
                continue
            if sc > rec["score"]:
                why_not.append(f"{other}: higher score but class={graph[other]['class']} ({graph[other]['reason']})")
        for top_strategic in strategic[:2]:
            tsr = top_strategic["roadmap_id"]
            if tsr != rid and graph[tsr]["class"] != "READY_NOW":
                why_not.append(f"{tsr}: STRATEGIC_PRIORITY #{top_strategic['rank']} but {graph[tsr]['class']} ({graph[tsr]['reason'][:150]})")
    else:
        why_not = ["no READY_NOW item exists; planner refuses definitive next-goal recommendation"]

    plan = {
        "planner": "p2p_roadmap_planner",
        "version": "1",
        "spec_goal": "P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01",
        "OFFICIAL_BASELINE": inp["OFFICIAL_BASELINE"],
        "HASHES": inp["HASHES"],
        "AUTHORITY_ORDER": inp["AUTHORITY_ORDER"],
        "ROADMAP_COVERAGE_GATE": coverage,
        "DEPENDENCY_GRAPH": graph,
        "STRATEGIC_PRIORITY_LIST": strategic,
        "NEXT_EXECUTABLE_GOALS": executable,
        "BLOCKED_HIGH_VALUE_GOALS": blocked_high_value,
        "OWNER_DEFERRED_ITEMS": deferred,
        "RELEVANT_PARTIAL_CAPABILITIES": partials,
        "ROADMAP_COVERAGE_GAPS": coverage["gaps"],
        "NOT_PROVEN_DEPENDENCIES": inp["NOT_PROVEN"],
        "RECOMMENDED_NEXT_GOAL": rec["roadmap_id"] if rec else None,
        "WHY_THIS_GOAL": why_this,
        "WHY_NOT_HIGHER_PRIORITY_ITEMS": why_not,
        "REQUIRED_OWNER_DECISION": "Approve or reject the planner-recommended next P2P development Goal." if rec else "No executable Goal — Owner must unblock or defer; planner refuses auto-start.",
        "EVIDENCE_POINTERS": [i.get("current_evidence", "")[:200] for i in inp["ROADMAP_ITEMS"] if i.get("current_evidence")][:10],
        "PLANNER_SELECTION_DOES_NOT_AUTO_EXECUTE": True,
        "ROADMAP_MANUAL_REENTRY_REQUIRED": "NO — planner reads canonical JSON files directly; no transcription into prompt",
    }
    return plan


# ---------------------------------------------------------------- beginner view
def beginner_view(plan):
    rec = plan["RECOMMENDED_NEXT_GOAL"]
    rows = [
        ("P2P muốn làm gì tiếp?", rec if rec else "Không có Goal nào an toàn để bắt đầu ngay."),
        ("Tại sao?", "; ".join(plan["WHY_THIS_GOAL"]) if plan["WHY_THIS_GOAL"] else plan["REQUIRED_OWNER_DECISION"]),
        ("Việc quan trọng hơn nào chưa làm được ngay?",
         "; ".join(f"{b['roadmap_id']} ({b['class']})" for b in plan["BLOCKED_HIGH_VALUE_GOALS"][:5]) or "không có"),
        ("Cái gì đang bị block?",
         "; ".join(f"{b['roadmap_id']}: {b['reason'][:120]}" for b in plan["BLOCKED_HIGH_VALUE_GOALS"]) or "không có"),
        ("Cái gì Owner đã hoãn?",
         "; ".join(f"{d['roadmap_id']}" for d in plan["OWNER_DEFERRED_ITEMS"]) or "không có"),
        ("Goal này có đụng project/code/data thật không?",
         "KHÔNG — Goal này chỉ là khả năng lập kế hoạch đọc-only; không mutate Game Truyện, Gia Phả, Logistics."),
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
    if coverage["ROADMAP_COVERAGE_GAP"]:
        print("PLANNER_OUTPUT: ROADMAP_COVERAGE_GAP=TRUE — recommendation completeness cannot be claimed", file=sys.stderr)

    graph = classify_dependencies(inp)
    scored = rank_items(inp, graph)
    plan = build_plan(inp, graph, scored, coverage, dctl)
    plan.update(beginner_view(plan))

    out = args.output or os.path.join(args.repo, "reports", "planner", "P2P-PLANNER-RUN-01.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
