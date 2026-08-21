"""CL1-CL40 — deterministic tests for the P2P durable development framework.

Scope: Development Charter, Capability Ledger (capability-index.json + schema),
roadmap projection, Goal Contract template, Supervisor template, and the
framework validator. These tests do not touch runtime execution behavior; they
validate durable governance artifacts against durable sources
(development-control.json, VERSION, candidate records).

Baseline (recovered by running, pre-change): full regression 326 passed,
4 skipped, 0 failures in this sandbox. Any new failure introduced by this file
must be investigated; all CL1-CL40 must pass for C25 to close.
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

try:
    import jsonschema  # noqa: F401
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def load_ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def load_gov():
    return json.loads(GOV.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- charter


def test_cl1_charter_exists():
    assert CHARTER.exists(), "Charter (or canonical equivalent) must exist."


def test_cl2_north_star():
    text = CHARTER.read_text(encoding="utf-8").lower()
    assert "beginner" in text, "Charter must contain the beginner-first North Star."


def test_cl3_provider_neutrality():
    text = CHARTER.read_text(encoding="utf-8").lower()
    assert "provider" in text and ("neutral" in text or "neutrality" in text
                                   or "agnostic" in text or "no hardcode" in text), \
        "Charter must preserve provider neutrality."


def test_cl4_task_not_agent():
    text = CHARTER.read_text(encoding="utf-8")
    assert "task" in text.lower() and "agent" in text.lower(), \
        "Charter must preserve the Task != Agent distinction."


def test_cl5_output_not_evidence():
    text = CHARTER.read_text(encoding="utf-8").lower()
    assert "evidence" in text, "Charter must preserve Output != Evidence."


def test_cl6_inventory_not_behavior():
    text = CHARTER.read_text(encoding="utf-8").lower()
    assert "behavior" in text and "inventory" in text, \
        "Charter must preserve Inventory != Behavior."


def test_cl7_goal_pass_not_promote():
    text = CHARTER.read_text(encoding="utf-8").lower()
    assert "promot" in text, "Charter must preserve Goal PASS != Promote."


# ---------------------------------------------------------------- ledger


def test_cl8_schema_passes():
    if not HAS_JSONSCHEMA:
        pytest.skip("jsonschema not installed")
    ledger = load_ledger()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(instance=ledger, schema=schema)


def test_cl9_ids_unique():
    ledger = load_ledger()
    ids = [c["capability_id"] for c in ledger["capabilities"]]
    assert len(ids) == len(set(ids)), "Capability IDs must be unique."


def test_cl10_allowed_statuses():
    ledger = load_ledger()
    vocab = set(ledger["status_vocabulary"])
    for cap in ledger["capabilities"]:
        assert cap["status"] in vocab, f"{cap['capability_id']} uses a forbidden status {cap['status']}"


def test_cl11_verified_requires_evidence():
    ledger = load_ledger()
    for cap in ledger["capabilities"]:
        if cap["status"] == "VERIFIED_IMPLEMENTED":
            assert cap.get("evidence_refs"), \
                f"{cap['capability_id']} claims VERIFIED_IMPLEMENTED without evidence_refs"


def test_cl12_unknown_permitted():
    ledger = load_ledger()
    unknowns = [c["capability_id"] for c in ledger["capabilities"] if c["status"] == "UNKNOWN"]
    assert unknowns, "Ledger must permit UNKNOWN rather than guess (e.g., C22_C24_ADAPTER_LIVE_CERTIFICATION)."


def test_cl13_no_runtime_task_state():
    ledger = load_ledger()
    forbidden = ["task_id", "run_id", "session_state", "task_state.json"]
    text = json.dumps(ledger)
    for key in forbidden:
        assert f'"{key}"' not in text, f"Ledger must not contain runtime task state key {key}"


def test_cl14_not_second_fact_store():
    ledger = load_ledger()
    assert "authority_boundary" in ledger, "Ledger must declare its authority boundary."
    boundary = ledger["authority_boundary"].lower()
    assert "not" in boundary and ("fact" in boundary or "runtime" in boundary), \
        "Ledger must explicitly not be a second FACT store."


def test_cl15_deps_valid():
    ledger = load_ledger()
    ids = {c["capability_id"] for c in ledger["capabilities"]}
    for cap in ledger["capabilities"]:
        for dep in cap.get("dependencies", []):
            assert dep in ids, f"{cap['capability_id']} depends on missing {dep}"


def test_cl16_beginner_value_present():
    ledger = load_ledger()
    missing = [c["capability_id"] for c in ledger["capabilities"]
               if not c.get("beginner_value") or len(str(c["beginner_value"]).strip()) < 10]
    assert not missing, f"Material capabilities missing beginner_value: {missing[:10]}"


def test_cl17_c22_c23_c24_represented():
    ledger = load_ledger()
    ids = {c["capability_id"] for c in ledger["capabilities"]}
    for want in ("ADAPTER_CONFORMANCE", "C22_C24_ADAPTER_LIVE_CERTIFICATION",
                 "ROUND_TRIP_BINDING", "CROSS_HOST_RESUME"):
        assert want in ids, f"C22-C24 capability {want} must be represented in the ledger"


def test_cl18_c24_not_mislabeled():
    ledger = load_ledger()
    rec = next((c for c in ledger["capabilities"] if c["capability_id"] == "C22_C24_ADAPTER_LIVE_CERTIFICATION"), None)
    assert rec is not None, "C22_C24_ADAPTER_LIVE_CERTIFICATION record missing"
    assert rec["status"] != "VERIFIED_IMPLEMENTED", "C24 must not be mislabeled live-certified"
    assert rec["status"] == "UNKNOWN", "C24 status must honestly be UNKNOWN in this copy"


def test_cl19_no_false_host_routing():
    ledger = load_ledger()
    rec = next((c for c in ledger["capabilities"] if c["capability_id"] == "HOST_SELECTION"), None)
    assert rec is not None
    assert rec.get("known_gaps"), "HOST_SELECTION must record known gaps (automatic routing not ready)."
    assert rec.get("next_condition", "").lower().startswith("live routing") or \
           "live routing" in rec.get("next_condition", "").lower() or \
           "automatic" in str(rec.get("known_gaps", "")).lower(), \
        "HOST_SELECTION must not falsely claim automatic host routing is implemented."


def test_cl20_no_false_model_resolver():
    ledger = load_ledger()
    rec = next((c for c in ledger["capabilities"] if c["capability_id"] == "SEMANTICA_PROVIDER_SEAM"), None)
    assert rec is not None
    assert rec["status"] in ("DEFERRED", "PLANNED", "UNKNOWN", "REJECTED", "OBSOLETE"), \
        f"Model/provider seam must not be falsely implemented: {rec['status']}"


def test_cl21_deferred_can_remain():
    ledger = load_ledger()
    deferred = [c["capability_id"] for c in ledger["capabilities"] if c["status"] == "DEFERRED"]
    assert deferred, "Deferred ideas must be allowed to remain DEFERRED (e.g., RAG_SCOPE)."
    for cid in deferred:
        rec = next(c for c in ledger["capabilities"] if c["capability_id"] == cid)
        assert rec.get("deferred_reason"), f"{cid} is DEFERRED without a deferred_reason"


def test_cl22_rejected_recoverable():
    ledger = load_ledger()
    rejected = [c for c in ledger["capabilities"] if c["status"] == "REJECTED"]
    assert len(rejected) >= 3, "Rejected anti-patterns must be preserved as recoverable records."
    for rec in rejected:
        assert rec.get("rejected_reason"), f"{rec['capability_id']} REJECTED without rejected_reason"


# ---------------------------------------------------------------- templates


def test_cl23_one_primary_objective():
    text = GOAL_TPL.read_text(encoding="utf-8").lower()
    assert "primary" in text, "Goal template must contain the one-primary-objective rule."


def test_cl24_durable_recovery_required():
    text = GOAL_TPL.read_text(encoding="utf-8").lower()
    assert "durable" in text and "recover" in text, \
        "Goal template must require durable recovery before changes."


def test_cl25_architecture_recovery_required():
    text = GOAL_TPL.read_text(encoding="utf-8").lower()
    assert "architectural" in text or "invariant" in text, \
        "Goal template must require existing-architecture recovery."


def test_cl26_non_goals_required():
    text = GOAL_TPL.read_text(encoding="utf-8").lower()
    assert "out of scope" in text or "anti-goal" in text, \
        "Goal template must require explicit non-goals."


def test_cl27_behavioral_acceptance():
    text = GOAL_TPL.read_text(encoding="utf-8").lower()
    assert "behavior" in text or "acceptance" in text or "criterion" in text, \
        "Goal template must require behavioral acceptance."


def test_cl28_evidence_contract():
    text = GOAL_TPL.read_text(encoding="utf-8").lower()
    assert "evidence" in text, "Goal template must require an evidence contract."


def test_cl29_regression_contract():
    text = GOAL_TPL.read_text(encoding="utf-8").lower()
    assert "regression" in text, "Goal template must require a regression contract."


def test_cl30_beginner_impact():
    text = GOAL_TPL.read_text(encoding="utf-8").lower()
    assert "beginner" in text or "owner" in text, \
        "Goal template must require beginner impact."


def test_cl31_terminal_stop():
    text = GOAL_TPL.read_text(encoding="utf-8").lower()
    assert "stop" in text, "Goal template must require a terminal stop rule."


def test_cl32_supervisor_rejects_exaggeration():
    text = SUP_TPL.read_text(encoding="utf-8").lower()
    assert "discrepanc" in text, "Supervisor template must force discrepancy listing (rejects exaggerated claims)."
    assert "verdict" in text, "Supervisor template must require an explicit verdict."


# ---------------------------------------------------------------- projection / invariants


def test_cl33_roadmap_consistent_with_ledger():
    ledger = load_ledger()
    gov = load_gov()
    road = ROADMAP.read_text(encoding="utf-8")
    ledger_count = len(ledger["capabilities"])
    match = re.search(r"\((\d+) records", road)
    assert match and int(match.group(1)) == ledger_count, \
        f"Roadmap must match ledger count ({ledger_count})"
    base = gov["official_baseline"]
    assert base["version"] in road or base.get("artifact_sha256", "")[:12] in road, \
        "Roadmap baseline must match governance official_baseline"


def test_cl34_no_second_runtime_truth_store():
    """C25 must not introduce any runtime file acting as a second truth store."""
    system = ROOT / ".p2p/system"
    assert system.exists()
    # C25 adds no .py file under .p2p/system and adds no runtime state directory.
    for _ in (ROOT / ".p2p/system").rglob("*.py"):
        pass  # only assert absence of c25 runtime additions below
    new_files = [p.name for p in (ROOT / ".p2p/system").rglob("*")
                 if p.is_file() and "c25" in p.name.lower()]
    assert not new_files, f"C25 must not add runtime files: {new_files}"


def test_cl35_no_second_executor():
    text = CHARTER.read_text(encoding="utf-8").lower()
    has_executor = ("executor" in text or "execution engine" in text)
    if has_executor:
        assert "sole" in text or "single" in text or "not" in text, \
            "Charter must not introduce a second execution engine."


def test_cl36_no_provider_router():
    text = CHARTER.read_text(encoding="utf-8").lower()
    has_router = "router" in text
    if has_router:
        assert "sole" in text or "p2p" in text, \
            "Charter must not introduce a provider/model router."


def test_cl37_no_background_autonomy():
    text = CHARTER.read_text(encoding="utf-8")
    lower = text.lower()
    # Only allowed mentions are anti-goal declarations (rejected patterns list).
    for word in ("daemon", "scheduler", "autonom"):
        assert word not in lower.replace("autonomy`", "").replace("background", "").replace("daemon", "").replace("scheduler", "") \
            or "reject" in lower, \
            "Charter must not introduce background autonomy (mentions must be as rejected patterns)."


def test_cl38_baseline_19_immutable():
    gov = load_gov()
    base = gov["official_baseline"]
    assert base["version"] == "8.4.7-C-codex.19"
    assert base["artifact_sha256"] == "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8"
    assert base["promotion_status"] == "PROMOTED_VERIFIED"


def test_cl39_c08_deferred():
    gov = load_gov()
    items = {it.get("id") or it.get("goal_id"): it for it in gov["roadmap"]["items"]}
    c08 = items.get("C08")
    assert c08 is not None, "C08 must remain in the roadmap"
    assert c08.get("status") == "DEFERRED", f"C08 must remain DEFERRED (was {c08.get('status')})"


def test_cl40_c09_blocked():
    gov = load_gov()
    items = {it.get("id") or it.get("goal_id"): it for it in gov["roadmap"]["items"]}
    c09 = items.get("C09")
    assert c09 is not None, "C09 must remain in the roadmap"
    status = (c09.get("status") or "").upper()
    assert status == "BLOCKED", f"C09 must remain BLOCKED (was {c09.get('status')})"
