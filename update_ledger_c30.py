#!/usr/bin/env python3
"""C30 ledger reconciliation.

Idempotent: appends each NEW record only if its capability_id is absent, and
updates EXTEND_EXISTING records with a deterministic C30 note + implementation
reference + dependency only when not already present. Classification follows
the C30 instruction §7 plan (c30-state.md).

Counts (pre): 136 records. Post: 136 + 17 new = 153 records.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"
MODULE = "scripts/p2p_execution_target.py"
RESEARCH = "docs/p2p-development/research/execution-target-pattern-research.md"
ET_SUITE = "tests/test_p2p_execution_target.py"

NOW = "2026-08-17"

NEW_RECORDS = [
    # --- CREATE_NEW: FOUNDATION_READY (durable module implements them) ---
    dict(
        capability_id="COMPOSABLE_EXECUTION_TARGET",
        name="Composable Execution Target",
        family="EXECUTION_AND_ORCHESTRATION",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "Task execution requirements, the harness that runs them, the model "
            "provider behind the model, and the protocol surface are checked as "
            "one honest composition instead of one assumed promise, so a beginner "
            "never gets an execution environment that merely looks capable."
        ),
        principle="COMPOSITION_HONESTY",
        origin_refs=[RESEARCH, "C30 terminal report"],
        dependencies=["PERMISSION_ENVELOPE", "DRIFT_GATE", "PORTABLE_EXECUTION_ENVELOPE"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=["Runtime wiring to an actual harness provider is deliberately out of scope (no router, no real execution)."],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="MODEL_PROVIDER_ABSTRACTION",
        name="Model Provider Abstraction",
        family="MULTI_AI_INTEROPERABILITY",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "The model's provider is a separate identity from the model itself, "
            "so switching providers never silently changes what the model claims "
            "to be able to do."
        ),
        principle="PROVIDER_NEUTRALITY",
        origin_refs=[RESEARCH],
        dependencies=["PORTABLE_EXECUTION_ENVELOPE"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=["Endpoint identity recorded; no live endpoint discovery."],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="MODEL_PROFILE",
        name="Model Profile",
        family="MULTI_AI_INTEROPERABILITY",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "Each model's tool-calling, structured output, and freshness state are "
            "recorded explicitly, so an undocumented model behavior is treated as "
            "unknown, never as supported."
        ),
        principle="EVIDENCE_HONESTY",
        origin_refs=[RESEARCH],
        dependencies=["MODEL_PROVIDER_ABSTRACTION"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=[],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="EFFECTIVE_CAPABILITY_COMPOSITION",
        name="Effective Capability Composition",
        family="EXECUTION_AND_ORCHESTRATION",
        status="FOUNDATION_READY",
        origin_type="ARCHITECTURE_INVARIANT",
        beginner_value=(
            "A capability is only supported when every component that owns it says "
            "so; one 'no' outvotes many 'yes', so claimed ability is never assumed."
        ),
        principle="INTERSECTION_CONSENSUS",
        origin_refs=[RESEARCH],
        dependencies=["COMPOSABLE_EXECUTION_TARGET"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=[],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="EXECUTION_BACKEND_REGISTRY",
        name="Execution Backend Registry",
        family="EXECUTION_AND_ORCHESTRATION",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "Known harnesses, providers, models, and protocols are enumerated in a "
            "neutral registry that never picks, ranks, or routes — the beginner "
            "sees the landscape without the tool making silent choices for them."
        ),
        principle="NEUTRAL_ENUMERATION",
        origin_refs=[RESEARCH],
        dependencies=["COMPOSABLE_EXECUTION_TARGET", "MODEL_PROVIDER_ABSTRACTION"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=["Distinct from the Capability Ledger by design; no task state is stored."],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="TASK_WORKSPACE_ISOLATION",
        name="Task Workspace Isolation (modeled)",
        family="EXECUTION_AND_ORCHESTRATION",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "The workspace class a task needs (sandbox, current repo, read-only) is "
            "declared and checked before execution, so a task never silently runs in "
            "the wrong place."
        ),
        principle="ISOLATION_BY_CONTRACT",
        origin_refs=[RESEARCH],
        dependencies=["COMPOSABLE_EXECUTION_TARGET", "PERMISSION_ENVELOPE"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=["Profile/eligibility only; actual isolation runtime is a later goal."],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="STRUCTURED_HEADLESS_EXECUTION",
        name="Structured Headless Execution (contract)",
        family="EXECUTION_AND_ORCHESTRATION",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "Execution is a structured request/lifecycle/result/receipt contract "
            "rather than UI scraping, so every run produces the same honest "
            "evidence shape regardless of surface."
        ),
        principle="STRUCTURED_RESULT_CONTRACT",
        origin_refs=[RESEARCH],
        dependencies=["COMPOSABLE_EXECUTION_TARGET"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=[],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="FAILURE_ONLY_DIAGNOSTICS",
        name="Failure-Only Diagnostics",
        family="OUTCOME_LEARNING",
        status="FOUNDATION_READY",
        origin_type="ARCHITECTURE_INVARIANT",
        beginner_value=(
            "Success produces minimal structured evidence and failure produces "
            "richer bounded diagnostics, so the beginner is never flooded with "
            "noise when things go right and never left guessing when they fail."
        ),
        principle="FAILURE_DIAGNOSTICS_BUDGET",
        origin_refs=[RESEARCH],
        dependencies=["COMPOSABLE_EXECUTION_TARGET"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=[],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="HARNESS_AUTH_PROFILE",
        name="Harness Auth Profile",
        family="MULTI_AI_INTEROPERABILITY",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "The harness credential reference is kept separate from the provider "
            "credential reference, and neither value is stored, so the beginner's "
            "accounts never leak into the data model."
        ),
        principle="SECRET_NEVER_STORED",
        origin_refs=[RESEARCH],
        dependencies=["COMPOSABLE_EXECUTION_TARGET"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=[],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="MODEL_PROVIDER_AUTH_PROFILE",
        name="Model Provider Auth Profile",
        family="MULTI_AI_INTEROPERABILITY",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "Provider auth is a separate state from harness auth and presence is "
            "never promoted to validity, so a stored but unverified key never "
            "pretends to work."
        ),
        principle="AUTH_PRESENCE_HONESTY",
        origin_refs=[RESEARCH],
        dependencies=["MODEL_PROVIDER_ABSTRACTION", "HARNESS_AUTH_PROFILE"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=[],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="PROTOCOL_CAPABILITY_PROFILE",
        name="Protocol Capability Profile",
        family="MULTI_AI_INTEROPERABILITY",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "Tool-protocol support is declared as a distinct profile that can "
            "never satisfy an execution-capability requirement on its own, so "
            "protocol compatibility is never mistaken for real execution power."
        ),
        principle="COMPATIBILITY_NEVER_CERTIFICATION",
        origin_refs=[RESEARCH],
        dependencies=["EXECUTION_BACKEND_REGISTRY"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=[],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="TARGET_FINGERPRINT_DRIFT",
        name="Target Fingerprint and Contract Drift",
        family="TRUTH_AND_GOVERNANCE",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "Every execution target gets a stable fingerprint that changes on "
            "material change, and an old certification can never silently stay "
            "current, so nothing drifts into being trusted by accident."
        ),
        principle="MATERIAL_CHANGE_INVALIDATES_CERTIFICATION",
        origin_refs=[RESEARCH],
        dependencies=["DRIFT_GATE", "COMPOSABLE_EXECUTION_TARGET"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=[],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="HEALTH_OWNERSHIP_LADDER",
        name="Health and Ownership Ladder",
        family="EXECUTION_AND_ORCHESTRATION",
        status="FOUNDATION_READY",
        origin_type="IMPLEMENTATION_GOAL",
        beginner_value=(
            "A process being healthy is not the same as belonging to P2P: health "
            "and ownership are separate rungs on one ladder, so a borrowed healthy "
            "process is never claimed as the project's own."
        ),
        principle="HEALTHY_NOT_OWNED",
        origin_refs=[RESEARCH],
        dependencies=["HOST_FALLBACK"],
        implementation_refs=[MODULE],
        evidence_refs=[ET_SUITE],
        known_gaps=["Probe mechanics are a later goal; the vocabulary is the durable part."],
        freshness="verified_against_filesystem",
        last_reviewed=NOW,
    ),
    # --- CREATE_NEW: PLANNED (recorded-not-implemented; honesty) ---
    dict(
        capability_id="SAFE_QUIESCE_AND_DRAIN",
        name="Safe Quiesce and Drain",
        family="EXECUTION_AND_ORCHESTRATION",
        status="PLANNED",
        origin_type="OWNER_ACCEPTED_PROPOSAL",
        beginner_value=(
            "Work can be drained and the executor quiesced before a "
            "destructive lifecycle change, with unknown states failing closed, "
            "so nothing mid-task is silently killed."
        ),
        principle="DRAIN_BEFORE_DESTRUCT",
        origin_refs=[RESEARCH, "C30 terminal report"],
        dependencies=["COMPOSABLE_EXECUTION_TARGET", "QUINCESCE_VOCABULARY"],
        implementation_refs=[],
        evidence_refs=["docs/p2p-development/research/execution-target-pattern-research.md (pattern J)"],
        known_gaps=["Implementation is a later goal; vocabulary + fail-closed semantics only so far."],
        freshness="from_governance_record",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="PROVIDER_NEUTRAL_AUTOPILOT",
        name="Provider-Neutral Autopilot (intent only)",
        family="MULTI_AI_INTEROPERABILITY",
        status="PLANNED",
        origin_type="OWNER_ACCEPTED_PROPOSAL",
        beginner_value=(
            "Autopilot intent is recorded as a neutral capability, not tied to "
            "any vendor's autopilot feature, so the beginner's autonomy level is "
            "chosen by policy and never inherited from a product default."
        ),
        principle="RECORDED_NOT_IMPLEMENTED",
        origin_refs=[RESEARCH, "C30 terminal report"],
        dependencies=[],
        implementation_refs=[],
        evidence_refs=[],
        known_gaps=["Explicitly recorded-not-implemented; no autopilot behavior exists in the codebase."],
        freshness="from_governance_record",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="PLANNER_PROVIDER_NEUTRALITY",
        name="Planner Provider Neutrality",
        family="MULTI_AI_INTEROPERABILITY",
        status="PLANNED",
        origin_type="OWNER_ACCEPTED_PROPOSAL",
        beginner_value=(
            "Planning logic does not assume any specific provider's planning "
            "surface, so a planning skill portable across providers is possible "
            "without vendor lock-in."
        ),
        principle="PROVIDER_NEUTRALITY",
        origin_refs=[RESEARCH],
        dependencies=["MODEL_PROVIDER_ABSTRACTION"],
        implementation_refs=[],
        evidence_refs=[],
        known_gaps=["Recorded intent; implementation deferred to a later goal."],
        freshness="from_governance_record",
        last_reviewed=NOW,
    ),
    dict(
        capability_id="MODEL_PROVIDER_SWAP_WITHOUT_CORE_CHANGE",
        name="Model Provider Swap Without Core Change",
        family="MULTI_AI_INTEROPERABILITY",
        status="PLANNED",
        origin_type="OWNER_ACCEPTED_PROPOSAL",
        beginner_value=(
            "The core execution contract does not encode any provider, so "
            "swapping the provider later does not force a rewrite of the "
            "project's core."
        ),
        principle="PROVIDER_NEUTRALITY",
        origin_refs=[RESEARCH],
        dependencies=["MODEL_PROVIDER_ABSTRACTION", "EXECUTION_BACKEND_REGISTRY"],
        implementation_refs=[],
        evidence_refs=[],
        known_gaps=["Foundation (profiles) exists; full swap mechanics deferred."],
        freshness="from_governance_record",
        last_reviewed=NOW,
    ),
]

# --- EXTEND_EXISTING: append C30 dependency + deterministic note ---
EXTEND = [
    ("DRIFT_GATE", "TARGET_FINGERPRINT_DRIFT",
     "C30: contract-identity drift and target fingerprinting build on the drift gate."),
    ("HOST_FALLBACK", "HEALTH_OWNERSHIP_LADDER",
     "C30: health/ownership ladder extends host fallback with an honesty vocabulary."),
    ("PORTABLE_EXECUTION_ENVELOPE", "COMPOSABLE_EXECUTION_TARGET",
     "C30: execution target composition extends the portable execution envelope."),
    ("PROJECT_MAP", "TOKEN_BOUNDED_REPO_MAP",
     "C30: token-bounded repo map recorded as index+relations+budget, not a full graph."),
]


def main() -> None:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    existing = {c["capability_id"] for c in data["capabilities"]}

    added = []
    for rec in NEW_RECORDS:
        if rec["capability_id"] in existing:
            continue
        data["capabilities"].append(rec)
        existing.add(rec["capability_id"])
        added.append(rec["capability_id"])

    for base_id, new_dep, note in EXTEND:
        if new_dep in existing:
            for c in data["capabilities"]:
                if c["capability_id"] == base_id:
                    if new_dep not in c.get("dependencies", []):
                        c["dependencies"].append(new_dep)
                    if note not in c.get("notes", ""):
                        c["notes"] = (c.get("notes") or "").rstrip(";. ").rstrip()
                        if c["notes"]:
                            c["notes"] += f". {note}"
                        else:
                            c["notes"] = note
                    if "C30-LEDGER-RECONCILE-001" not in c.get("evidence_refs", []):
                        c.setdefault("evidence_refs", []).append("C30-LEDGER-RECONCILE-001")

    LEDGER.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"added {len(added)} new records: {added}")
    print(f"total records now: {len(data['capabilities'])}")


if __name__ == "__main__":
    main()
