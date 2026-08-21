#!/usr/bin/env python3
"""Validate and project the durable P2P development-control record.

The record is a compact cross-session projection of existing project state. It
does not replace the execution ledger, FACT_LEDGER, Live Specs, approvals,
drift reports, Goal contracts, or evaluation evidence.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "p2p-development-control/1"
STATUS_SCHEMA = "p2p-development-control-status/1"
DEFAULT_CONTROL_RELATIVE = Path("governance") / "development-control.json"
OFFICIAL_BASELINE_VERSION = "8.4.7-C-codex.19"
OFFICIAL_BASELINE_SHA256 = "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8"
C15_CANDIDATE_VERSION = "8.4.7-C-codex.15"
C15_CANDIDATE_SHA256 = "ae39b78972c03ca17855e0cc86e18fbd997f1eb4d62116e909674abc86d90b1e"
C17_DEVELOPMENT_VERSION = "8.4.7-C-codex.20"
C18_DEVELOPMENT_VERSION = "8.4.7-C-codex.21"
LINEAGE_REPAIR_GOAL_ID = "P2P-CANONICAL-LINEAGE-REPAIR-01"
CANONICAL_CAPABILITIES = (
    "p2p_iris",
    "p2p_tecton",
    "p2p_axiom",
    "p2p_vector",
    "p2p_datos",
    "p2p_anon",
    "p2p_architecton",
    "p2p_helios",
)
ROADMAP_STATUSES = frozenset({"DONE", "ACTIVE", "PLANNED", "DEFERRED", "BLOCKED", "REJECTED"})
GOAL_ID_RE = re.compile(r"^C(?P<number>[1-9][0-9]{0,6})$")
MIN_GOAL_NUMBER = 8  # C08 is the earliest historically recorded Goal on this lineage.
def _goal_ids_in_order(by_id: dict[str, dict[str, Any]]) -> list[str]:
    """Return roadmap goal IDs (C<number>) sorted by numeric goal number, ascending."""
    goal_ids: dict[int, str] = {}
    for identifier in by_id:
        match = GOAL_ID_RE.match(identifier)
        if match is None:
            continue
        goal_ids[int(match.group("number"))] = identifier
    return [goal_ids[number] for number in sorted(goal_ids)]
def _expected_current_goal(goal_ids: list[str], by_id: dict[str, dict[str, Any]]) -> tuple[str, str]:
    """Deterministically derive the expected current roadmap item when no Goal is ACTIVE: the DONE goal immediately before the likely next goal, or the likely next goal itself if nothing is DONE yet."""
    next_id, next_status = _likely_next_goal(goal_ids, by_id)
    index = goal_ids.index(next_id)
    while index > 0:
        index -= 1
        previous_id = goal_ids[index]
        if by_id[previous_id].get("status") == "DONE":
            return (previous_id, "DONE")
    return (next_id, next_status)

def _likely_next_goal(goal_ids: list[str], by_id: dict[str, dict[str, Any]]) -> tuple[str, str]:
    """Deterministically derive the likely next roadmap Goal: the lowest-numbered non-DONE Goal at or after the current ACTIVE item; if no Goal is ACTIVE, the lowest-numbered non-DONE Goal after the last DONE Goal."""
    if not goal_ids:
        return ("C17", "PLANNED")
    start_index = 0
    active_seen = False
    for index, identifier in enumerate(goal_ids):
        status = by_id[identifier].get("status")
        if status == "ACTIVE":
            start_index = index + 1  # likely next is after the currently active goal
            active_seen = True
            break
        if status == "DONE":
            start_index = index + 1
        elif not active_seen:
            break  # first non-DONE, non-ACTIVE goal encountered while nothing is ACTIVE is the likely next
    for identifier in goal_ids[start_index:]:
        status = by_id[identifier].get("status", "PLANNED")
        if status in ("PLANNED", "ACTIVE"):
            return (identifier, status)
    tail = by_id[goal_ids[-1]]
    return (goal_ids[-1], tail.get("status", "DONE"))
RESEARCH_STATUSES = frozenset({"ADAPTED", "DEFERRED", "RESEARCH_ONLY", "EXCLUDED"})
_VERSION_RE = re.compile(r"^(?P<base>.+-codex)\.(?P<revision>[0-9]+)$")


class ControlError(ValueError):
    """A deterministic, user-actionable control-record validation error."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise ControlError(code, message)


def _object(value: Any, label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), "CONTROL_SHAPE", f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    _require(isinstance(value, list), "CONTROL_SHAPE", f"{label} must be a list")
    return value


def _nonempty_string(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), "CONTROL_SHAPE", f"{label} must be non-empty text")
    return value


def _version_key(version: Any, label: str = "version") -> tuple[str, int]:
    value = _nonempty_string(version, label)
    match = _VERSION_RE.fullmatch(value)
    _require(match is not None, "VERSION_FORMAT", f"{label} must use <release>-codex.<revision>: {value}")
    return match.group("base"), int(match.group("revision"))


def version_is_at_least(version: str, minimum: str = OFFICIAL_BASELINE_VERSION) -> bool:
    """Compare release lineage by explicit version fields, never filenames."""

    version_base, version_revision = _version_key(version)
    minimum_base, minimum_revision = _version_key(minimum, "minimum version")
    return version_base == minimum_base and version_revision >= minimum_revision


def load_control(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ControlError("CONTROL_MISSING", f"development-control record is missing: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlError("CONTROL_UNREADABLE", f"cannot read development-control record: {path}: {exc}") from exc
    return _object(value, str(path))


def _validate_authority(control: dict[str, Any]) -> None:
    authority = _object(control.get("authority"), "authority")
    _require(
        authority.get("canonical_source") == "governance/development-control.json",
        "AUTHORITY_SOURCE",
        "canonical_source must be governance/development-control.json",
    )
    refs = _list(authority.get("existing_authority_refs"), "authority.existing_authority_refs")
    required_refs = {
        ".p2p/state/goal-contract.json",
        ".p2p/state/project-status.json",
        ".p2p/state/execution-ledger.jsonl",
        "governance/fact-ledger.json",
        "governance/live-specs.json",
    }
    _require(required_refs.issubset(set(refs)), "AUTHORITY_REFS", "existing P2P authority references are incomplete")
    _require(authority.get("is_replacement_for_existing_state") is False, "SECOND_TRUTH_STORE", "control record cannot replace existing state")
    _require(authority.get("retrieved_content_is_data") is True, "TRUST_BOUNDARY", "retrieved content must remain data")


def _validate_official_baseline(control: dict[str, Any]) -> dict[str, Any]:
    baseline = _object(control.get("official_baseline"), "official_baseline")
    _require(
        baseline.get("version") == OFFICIAL_BASELINE_VERSION,
        "OFFICIAL_VERSION_MISMATCH",
        f"official baseline must be {OFFICIAL_BASELINE_VERSION}",
    )
    _require(
        baseline.get("artifact_sha256") == OFFICIAL_BASELINE_SHA256,
        "OFFICIAL_HASH_MISMATCH",
        "official baseline SHA-256 does not match the promoted artifact",
    )
    _require(baseline.get("promotion_status") == "PROMOTED_VERIFIED", "OFFICIAL_NOT_PROMOTED", "official baseline is not PROMOTED_VERIFIED")
    _nonempty_string(baseline.get("promotion_report"), "official_baseline.promotion_report")
    _nonempty_string(baseline.get("approval_reference"), "official_baseline.approval_reference")
    _nonempty_string(baseline.get("artifact_path"), "official_baseline.artifact_path")
    _version_key(baseline.get("version"), "official_baseline.version")
    return baseline


def _validate_lineage_contract(control: dict[str, Any], baseline: dict[str, Any]) -> None:
    contract = _object(control.get("lineage_contract"), "lineage_contract")
    required = _list(contract.get("required_candidate_fields"), "lineage_contract.required_candidate_fields")
    expected = {
        "based_on_official_version",
        "based_on_official_sha256",
        "development_goal",
        "candidate_version",
        "candidate_label",
        "candidate_sha256",
        "embedded_version",
        "promotion_status",
    }
    _require(expected.issubset(set(required)), "LINEAGE_SCHEMA", "candidate lineage required fields are incomplete")
    _require(contract.get("filename_is_authority") is False, "FILENAME_AUTHORITY", "artifact filenames cannot establish authority")
    policy = _object(contract.get("build_policy"), "lineage_contract.build_policy")
    _require(policy.get("minimum_source_version") == baseline.get("version"), "LINEAGE_POLICY", "build minimum must equal official baseline")
    _require(policy.get("below_minimum") == "BLOCK", "LINEAGE_POLICY", "below-minimum source policy must be BLOCK")
    maintenance = _object(policy.get("historical_maintenance_workflow"), "historical_maintenance_workflow")
    _require(maintenance.get("enabled") is False, "HISTORICAL_MODE", "historical maintenance mode must remain disabled")


def _validate_candidates(control: dict[str, Any], baseline: dict[str, Any]) -> None:
    candidates = _list(control.get("candidate_records"), "candidate_records")
    _require(bool(candidates), "LINEAGE_RECORDS", "at least one candidate lineage record is required")
    required = {
        "based_on_official_version",
        "based_on_official_sha256",
        "development_goal",
        "candidate_version",
        "candidate_label",
        "candidate_sha256",
        "embedded_version",
        "promotion_status",
    }
    ids: set[str] = set()
    _seen_ids: dict[str, int] = {}
    for index, raw in enumerate(candidates):
        candidate = _object(raw, f"candidate_records[{index}]")
        candidate_id = _nonempty_string(candidate.get("candidate_id"), f"candidate_records[{index}].candidate_id")
        # GATE-01B identity repair: a candidate_id may repeat EXACTLY twice
        # as a direct successor pair (.35 -> .36), both UNPROMOTED.
        if candidate_id in ids:
            _prev_idx = _seen_ids[candidate_id]
            _prev = _object(candidates[_prev_idx], f"candidate_records[{_prev_idx}]")
            _require(index == _prev_idx + 1, "LINEAGE_RECORDS",
                     f"successor candidate_id {candidate_id} must follow the "
                     f"original immediately")
            _prev_v = _nonempty_string(_prev.get("candidate_version"), f"candidate_records[{_prev_idx}].candidate_version")
            _cur_v = _nonempty_string(candidate.get("candidate_version"), f"candidate_records[{index}].candidate_version")
            _require(_cur_v.split(".")[-1].isdigit() and _prev_v.split(".")[-1].isdigit()
                     and int(_cur_v.split(".")[-1]) == int(_prev_v.split(".")[-1]) + 1,
                     "LINEAGE_RECORDS",
                     f"successor {candidate_id} must be the next canonical "
                     f"version ({_prev_v} -> {_cur_v})")
            _require(candidate.get("promotion_status") == "UNPROMOTED" and _prev.get("promotion_status") == "UNPROMOTED",
                     "LINEAGE_RECORDS",
                     f"identity-repair successor pair {candidate_id} must be UNPROMOTED")
        ids.add(candidate_id)
        _seen_ids[candidate_id] = index
        _require(required.issubset(candidate), "LINEAGE_SCHEMA", f"candidate {candidate_id} is missing required lineage fields")
        _require(candidate.get("based_on_official_version") == baseline.get("version"), "LINEAGE_BASELINE_MISMATCH", f"candidate {candidate_id} does not name the official version")
        _require(candidate.get("based_on_official_sha256") == baseline.get("artifact_sha256"), "LINEAGE_BASELINE_MISMATCH", f"candidate {candidate_id} does not name the official SHA-256")
        candidate_version = _nonempty_string(candidate.get("candidate_version"), f"candidate {candidate_id}.candidate_version")
        embedded_version = _nonempty_string(candidate.get("embedded_version"), f"candidate {candidate_id}.embedded_version")
        _version_key(candidate_version, f"candidate {candidate_id}.candidate_version")
        _version_key(embedded_version, f"candidate {candidate_id}.embedded_version")
        _candidate_sha = str(candidate.get("candidate_sha256") or "")
        _never_built = candidate.get("built") is False
        _anchor = candidate.get("lineage_anchor_sha256")
        _sha_valid = bool(re.fullmatch(r"[0-9a-f]{64}", _candidate_sha))
        _placeholder_ok = _never_built and _candidate_sha == "TO_BE_FILLED" and isinstance(_anchor, str) and bool(re.fullmatch(r"[0-9a-f]{64}", _anchor))
        _require(_sha_valid or _placeholder_ok, "LINEAGE_HASH", f"candidate {candidate_id} SHA-256 is invalid (real digest required; TO_BE_FILLED only for never-built records with a lineage_anchor_sha256)")

        _require(candidate.get("promotion_status") in {"UNPROMOTED", "PROMOTED_VERIFIED", "PROMOTED_OWNER_VERIFIED", "REJECTED"}, "LINEAGE_STATUS", f"candidate {candidate_id} has an invalid promotion status")
        _anchor_sha = candidate.get("lineage_anchor_sha256")
        if _anchor_sha is not None:
            _require(isinstance(_anchor_sha, str) and bool(re.fullmatch(r"[0-9a-f]{64}", _anchor_sha)), "LINEAGE_ANCHOR", f"candidate {candidate_id} lineage_anchor_sha256 must be a 64-hex digest")
            _anchor_note = candidate.get("lineage_anchor_note")
            _require(isinstance(_anchor_note, str) and len(_anchor_note) > 0, "LINEAGE_ANCHOR", f"candidate {candidate_id} has an anchor without a note")
        if candidate.get("promotion_status") == "PROMOTED_OWNER_VERIFIED":
            _history = candidate.get("promotion_history")
            _require(isinstance(_history, list) and len(_history) > 0, "OWNER_PROMOTION", f"promoted-by-owner candidate {candidate_id} requires a non-empty promotion_history")
            _pa_sha = candidate.get("promoted_artifact_sha256")
            _require(isinstance(_pa_sha, str) and bool(re.fullmatch(r"[0-9a-f]{64}", _pa_sha)), "OWNER_PROMOTION", f"promoted-by-owner candidate {candidate_id} promoted_artifact_sha256 must be a 64-hex digest")
            _event = _history[0]
            _approval = _event.get("approval_record")
            _require(isinstance(_approval, str) and _approval.startswith("approvals/"), "OWNER_PROMOTION", f"promoted-by-owner candidate {candidate_id} first promotion event must reference a governance approval record")

        if candidate.get("promotion_status") == "PROMOTED_VERIFIED":
            _require(candidate_version == baseline.get("version"), "PROMOTION_LINEAGE", f"promoted candidate {candidate_id} is not the official version")
            _require(embedded_version == baseline.get("version"), "PROMOTION_LINEAGE", f"promoted candidate {candidate_id} has a mismatched embedded version")
            _require(candidate.get("candidate_sha256") == baseline.get("artifact_sha256"), "PROMOTION_LINEAGE", f"promoted candidate {candidate_id} has a mismatched SHA-256")
        if candidate_id == "C15":
            _require(candidate_version == C15_CANDIDATE_VERSION, "C15_LINEAGE", "C15 candidate version does not match the recorded unpromoted candidate")
            _require(embedded_version == C15_CANDIDATE_VERSION, "C15_LINEAGE", "C15 embedded version does not match the recorded candidate")
            _require(candidate.get("candidate_sha256") == C15_CANDIDATE_SHA256, "C15_LINEAGE", "C15 candidate SHA-256 does not match the recorded unpromoted candidate")
            _require(candidate.get("promotion_status") == "UNPROMOTED", "C15_LINEAGE", "C15 candidate must remain UNPROMOTED")
            _require(candidate.get("lineage_status") == "LINEAGE_REGRESSION_BLOCKED", "C15_LINEAGE", "C15 candidate must remain lineage-blocked")
    _require("C15" in ids, "LINEAGE_RECORDS", "C15 candidate lineage is required for the current roadmap state")


def _validate_capabilities(control: dict[str, Any]) -> dict[str, dict[str, Any]]:
    capabilities = _list(control.get("capability_status"), "capability_status")
    by_id: dict[str, dict[str, Any]] = {}
    for raw in capabilities:
        item = _object(raw, "capability_status item")
        identifier = _nonempty_string(item.get("id"), "capability_status.id")
        _require(identifier not in by_id, "CAPABILITY_STATUS", f"duplicate capability: {identifier}")
        by_id[identifier] = item
    for identifier in ("C10", "C11", "C12", "C13", "C14", "C15", "C08", "C09"):
        _require(identifier in by_id, "CAPABILITY_STATUS", f"missing capability status: {identifier}")
    for identifier in ("C10", "C11", "C12", "C13"):
        _require(by_id[identifier].get("status") == "DONE" and by_id[identifier].get("result") == "PASS", "CAPABILITY_STATUS", f"{identifier} must be DONE/PASS")
    _require(by_id["C14"].get("status") == "DONE" and by_id["C14"].get("result") == "PROMOTED_VERIFIED", "CAPABILITY_STATUS", "C14 must remain PROMOTED_VERIFIED")
    c15 = by_id["C15"]
    _require(c15.get("status") == "DONE" and c15.get("result") == "PASS", "CAPABILITY_STATUS", "C15 must remain PASS/DONE")
    _require(c15.get("foundation_status") == "BOUNDED_DELEGATION_FOUNDATION_READY", "CAPABILITY_STATUS", "C15 foundation status is missing")
    _require(c15.get("live_delegation_certified") is False and c15.get("live_delegation_status") == "NOT_CERTIFIED", "CAPABILITY_STATUS", "C15 live delegation must remain uncertified")
    c17 = by_id.get("C17")
    if c17 is not None:
        _require(c17.get("status") == "DONE" and c17.get("result") == "PASS", "CAPABILITY_STATUS", "C17 must be DONE/PASS")
        _require(c17.get("foundation_status") == "PARALLEL_EXECUTION_FOUNDATION_READY", "CAPABILITY_STATUS", "C17 foundation status is missing")
        _require(c17.get("live_parallel_execution_certified") is False and c17.get("live_parallel_execution_status") == "NOT_CERTIFIED", "CAPABILITY_STATUS", "C17 live parallel execution must remain uncertified")
        _require(type(c17.get("cognitive_economy_parallel_orchestration_evaluated")) is bool, "CAPABILITY_STATUS", "C17 cognitive economy evaluation must be explicit")
        _require(c17.get("cognitive_economy_status") in {"NOT_EVALUATED", "EVALUATED_BOUNDED_PARALLEL_SLICE"}, "CAPABILITY_STATUS", "C17 cognitive economy status is invalid")
    c18 = by_id.get("C18")
    if c18 is not None:
        _require(c18.get("status") == "DONE" and c18.get("result") == "PASS", "CAPABILITY_STATUS", "C18 must be DONE/PASS")
        _require(c18.get("foundation_status") == "ADAPTIVE_ORCHESTRATION_POLICY_FOUNDATION_READY", "CAPABILITY_STATUS", "C18 foundation status is missing")
    c19 = by_id.get("C19")
    if c19 is not None:
        _require(c19.get("status") == "DONE" and c19.get("result") == "PASS", "CAPABILITY_STATUS", "C19 must be DONE/PASS")
        _require(c19.get("foundation_status") == "TASK_TARGETED_CONTEXT_RETRIEVAL_FOUNDATION_READY", "CAPABILITY_STATUS", "C19 foundation status is missing")
        _require(c19.get("candidate_id") == "C19", "CAPABILITY_STATUS", "C19 candidate identity is missing")
    c20 = by_id.get("C20")
    if c20 is not None:
        _require(c20.get("status") == "DONE" and c20.get("result") == "PASS", "CAPABILITY_STATUS", "C20 must be DONE/PASS")
        _require(c20.get("foundation_status") == "HOST_EXECUTOR_NEUTRALITY_FOUNDATION_READY", "CAPABILITY_STATUS", "C20 foundation status is missing")
        _require(c20.get("candidate_id") == "C20", "CAPABILITY_STATUS", "C20 candidate identity is missing")
        _require(c20.get("portable_execution_envelope_ready") is True, "CAPABILITY_STATUS", "C20 portable envelope status is missing")
        _require(c20.get("portable_result_receipt_ready") is True, "CAPABILITY_STATUS", "C20 receipt status is missing")
        _require(c20.get("cross_host_continuation_contract_ready") is True, "CAPABILITY_STATUS", "C20 continuation status is missing")
        _require(c20.get("automatic_host_routing_ready") is False, "CAPABILITY_STATUS", "C20 must not claim automatic routing")
        _require(c20.get("live_manus_adapter_certified") is False, "CAPABILITY_STATUS", "C20 live Manus adapter must remain uncertified")
    c21 = by_id.get("C21")
    if c21 is not None:
        _require(c21.get("status") == "DONE" and c21.get("result") == "PASS", "CAPABILITY_STATUS", "C21 must be DONE/PASS")
        _require(c21.get("foundation_status") == "HOST_SELECTION_POLICY_FOUNDATION_READY", "CAPABILITY_STATUS", "C21 foundation status is missing")
        _require(c21.get("candidate_id") == "C21", "CAPABILITY_STATUS", "C21 candidate identity is missing")
        _require(c21.get("host_requirement_profile_ready") is True, "CAPABILITY_STATUS", "C21 requirement profile status is missing")
        _require(c21.get("host_capability_discovery_foundation_ready") is True, "CAPABILITY_STATUS", "C21 discovery status is missing")
        _require(c21.get("automatic_host_routing_ready") is False, "CAPABILITY_STATUS", "C21 must not claim automatic routing")
        _require(c21.get("live_manus_adapter_certified") is False, "CAPABILITY_STATUS", "C21 live Manus adapter must remain uncertified")
    _require(by_id["C08"].get("status") == "DEFERRED", "CAPABILITY_STATUS", "C08 must remain DEFERRED")
    _require(by_id["C09"].get("status") == "BLOCKED" and by_id["C09"].get("blocker") == "EVENT_EVIDENCE_UNAVAILABLE", "CAPABILITY_STATUS", "C09 must remain BLOCKED/EVENT_EVIDENCE_UNAVAILABLE")
    return by_id


def _validate_design_and_canonical(control: dict[str, Any]) -> None:
    design = _object(control.get("design_intelligence"), "design_intelligence")
    _require(design.get("metadata_faculties") == 174, "DESIGN_METADATA", "design-intelligence metadata faculty count must be 174")
    _require(design.get("primary_router") == "p2p-uiux", "DESIGN_ROUTER", "p2p-uiux must remain the primary router")
    _require(design.get("aesthetica") == "OPTIONAL_NONCANONICAL", "DESIGN_ROUTER", "Aesthetica must remain optional/noncanonical")
    canonical = _object(control.get("canonical_capability_set"), "canonical_capability_set")
    _require(canonical.get("denominator") == 8, "CANONICAL_DENOMINATOR", "canonical denominator must be 8")
    _require(canonical.get("members") == list(CANONICAL_CAPABILITIES), "CANONICAL_MEMBERS", "canonical capability members are not the approved eight")
    _require(canonical.get("quorum") == "8/8", "CANONICAL_QUORUM", "canonical quorum must be 8/8")


def _validate_roadmap(control: dict[str, Any]) -> dict[str, dict[str, Any]]:
    roadmap = _object(control.get("roadmap"), "roadmap")
    _require(roadmap.get("allowed_statuses") == sorted(ROADMAP_STATUSES), "ROADMAP_ENUM", "roadmap allowed statuses are not the fixed enum")
    items = _list(roadmap.get("items"), "roadmap.items")
    by_id: dict[str, dict[str, Any]] = {}
    for raw in items:
        item = _object(raw, "roadmap item")
        identifier = _nonempty_string(item.get("id"), "roadmap item.id")
        _require(identifier not in by_id, "ROADMAP_ITEMS", f"duplicate roadmap item: {identifier}")
        _require(item.get("status") in ROADMAP_STATUSES, "ROADMAP_STATUS", f"invalid roadmap status for {identifier}")
        by_id[identifier] = item
    expected = {"C08", "C09", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18"}
    _require(expected.issubset(by_id), "ROADMAP_ITEMS", "C08-C17 roadmap coverage is incomplete")
    goal_ids = _goal_ids_in_order(by_id)
    _require(by_id["C08"]["status"] == "DEFERRED", "ROADMAP_STATUS", "C08 must be DEFERRED")
    _require(by_id["C09"]["status"] == "BLOCKED", "ROADMAP_STATUS", "C09 must be BLOCKED")
    for identifier in ("C10", "C11", "C12", "C13", "C14", "C15"):
        _require(by_id[identifier]["status"] == "DONE", "ROADMAP_STATUS", f"{identifier} must be DONE")
    c16_status = by_id["C16"]["status"]
    c17_status = by_id["C17"]["status"]
    c18_status = by_id["C18"]["status"]
    _require(
        (c16_status, c17_status) in {("ACTIVE", "PLANNED"), ("DONE", "ACTIVE"), ("DONE", "DONE")},
        "ROADMAP_STATUS",
        "C16/C17 must follow the bounded C17 transition sequence",
    )
    for index, identifier in enumerate(goal_ids):
        if identifier in {"C08", "C09", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17"}:
            continue
        status = by_id[identifier]["status"]
        _require(
            status in {"PLANNED", "ACTIVE", "DONE", "BLOCKED"},
            "ROADMAP_STATUS",
            f"{identifier} must be PLANNED, ACTIVE, DONE, or BLOCKED (C09 precedent)",
        )
        if index > 0:
            previous_status = by_id[goal_ids[index - 1]]["status"]
            if status in ("PLANNED", "BLOCKED") and previous_status in ("PLANNED", "BLOCKED"):
                continue  # consecutive PLANNED/BLOCKED states are the normal pre-implementation projection
            if status == "DONE" and previous_status == "BLOCKED":
                continue  # C09->C10 precedent: a blocked predecessor does not gate independent completion
            _require(
                previous_status == "DONE",
                "ROADMAP_STATUS",
                f"{identifier} requires the previous roadmap Goal to be DONE",
            )
    c21_status = by_id.get("C21", {}).get("status")
    c20_status = by_id.get("C20", {}).get("status")
    c19_status = by_id.get("C19", {}).get("status")
    current = _object(roadmap.get("current"), "roadmap.current")
    expected_current = ("C16", "ACTIVE") if c16_status == "ACTIVE" else _expected_current_goal(goal_ids, by_id)
    current_pair = (current.get("id"), current.get("status"))
    advanced_terminal = (
        current.get("id") == goal_ids[-1]
        and by_id[goal_ids[-1]]["status"] == "DONE"
    )
    _require(
        current_pair == expected_current or (advanced_terminal and current_pair[0] == goal_ids[-1]),
        "ROADMAP_CURRENT",
        f"current roadmap item must be {expected_current[0]}/{expected_current[1]}",
    )
    next_item = _object(roadmap.get("likely_next"), "roadmap.likely_next")
    expected_next = _likely_next_goal(goal_ids, by_id)
    _require(next_item.get("id") == expected_next[0], "ROADMAP_NEXT", f"likely next roadmap item must be {expected_next[0]}")
    _require(next_item.get("status") == expected_next[1], "ROADMAP_NEXT", "likely next roadmap status must match current roadmap state")
    _nonempty_string(next_item.get("title"), "roadmap.likely_next.title")
    return by_id


def _validate_research_and_invariants(control: dict[str, Any]) -> None:
    decisions = _list(control.get("research_decisions"), "research_decisions")
    names = {_nonempty_string(_object(raw, "research decision").get("name"), "research decision.name") for raw in decisions}
    required_names = {"Comp AI CRM", "Semantica", "TencentDB Agent Memory", "Zimster", "Agent TaskGraph Protocol", "DeepSeek Harness", "Nolane UI Intelligence", "Superlearn"}
    _require(required_names.issubset(names), "RESEARCH_REGISTRY", "research registry is missing a required decision")
    for raw in decisions:
        decision = _object(raw, "research decision")
        _require(decision.get("status") in RESEARCH_STATUSES, "RESEARCH_REGISTRY", f"invalid research status for {decision.get('name')}")
        _require(decision.get("vendored") is False, "RESEARCH_REGISTRY", f"research source is unexpectedly vendored: {decision.get('name')}")
    principles = _list(control.get("superlearn_principles"), "superlearn_principles")
    required_principles = {
        "research-before-plan",
        "explicit-coverage-checklist",
        "one-bounded-subtask-per-worker",
        "filesystem-context-offloading",
        "durable-evidence-trail",
        "parent-reviews-worker-artifacts",
        "deterministic-validation-before-completion",
    }
    _require(required_principles.issubset(set(principles)), "SUPERLEARN_PRINCIPLES", "Superlearn principles are incomplete")
    invariants = _list(control.get("architectural_invariants"), "architectural_invariants")
    invariant_ids = {_nonempty_string(_object(raw, "architectural invariant").get("id"), "architectural invariant.id") for raw in invariants}
    required_invariants = {"task-is-not-agent", "goal-pass-is-not-promotion", "worker-output-is-not-evidence", "p2p-is-sole-orchestrator", "unknown-remains-unknown"}
    _require(required_invariants.issubset(invariant_ids), "INVARIANTS", "required architectural invariants are incomplete")


def validate_control(control: dict[str, Any], *, expected_official_version: str = OFFICIAL_BASELINE_VERSION, expected_official_sha256: str = OFFICIAL_BASELINE_SHA256) -> dict[str, Any]:
    """Validate one control record and return a small deterministic summary."""

    _require(control.get("schema_version") == SCHEMA, "CONTROL_SCHEMA", f"schema_version must be {SCHEMA}")
    _require(expected_official_version == OFFICIAL_BASELINE_VERSION and expected_official_sha256 == OFFICIAL_BASELINE_SHA256, "VALIDATOR_POLICY", "official validator constants cannot be overridden")
    _validate_authority(control)
    baseline = _validate_official_baseline(control)
    _validate_lineage_contract(control, baseline)
    _validate_candidates(control, baseline)
    capabilities = _validate_capabilities(control)
    _validate_design_and_canonical(control)
    roadmap = _validate_roadmap(control)
    _validate_research_and_invariants(control)
    provenance = _list(control.get("provenance_log"), "provenance_log")
    _require(bool(provenance), "PROVENANCE", "provenance_log must not be empty")
    for entry in provenance:
        item = _object(entry, "provenance entry")
        _nonempty_string(item.get("change_id"), "provenance.change_id")
        _nonempty_string(item.get("changed_at"), "provenance.changed_at")
        _nonempty_string(item.get("what_changed"), "provenance.what_changed")
        _nonempty_string(item.get("why"), "provenance.why")
        _list(item.get("evidence_refs"), "provenance.evidence_refs")
    current = _object(control.get("current_development"), "current_development")
    current_goal = current.get("development_goal")
    goal_match = GOAL_ID_RE.match(str(current_goal)) if isinstance(current_goal, str) else None
    if current_goal == LINEAGE_REPAIR_GOAL_ID:
        _require(
            current.get("goal_kind") == "RECONCILIATION_NOT_PRODUCT_GOAL",
            "CURRENT_DEVELOPMENT",
            "lineage repair goal must be explicitly classified as non-product reconciliation",
        )
    else:
        _require(
            goal_match is not None and int(goal_match.group("number")) >= 16,
            "CURRENT_DEVELOPMENT",
            "current development goal must be a valid C<number> Goal at or after C16 or the explicit lineage repair goal",
        )
    _nonempty_string(current.get("source_version"), "current_development.source_version")
    _require(
        current.get("source_version_status") in {"STALE_BLOCKED_BELOW_OFFICIAL", "LINEAGE_RECONCILED", "ACTIVE_UNPROMOTED", "CANDIDATE_UNPROMOTED"},
        "CURRENT_DEVELOPMENT",
        "current source must carry an explicit lineage status",
    )
    _require(current.get("based_on_official_version") == baseline.get("version"), "CURRENT_DEVELOPMENT", "current development must name the official version")
    _require(current.get("based_on_official_sha256") == baseline.get("artifact_sha256"), "CURRENT_DEVELOPMENT", "current development must name the official SHA-256")
    if current.get("source_version_status") == "STALE_BLOCKED_BELOW_OFFICIAL":
        _require(not version_is_at_least(current["source_version"]), "CURRENT_DEVELOPMENT", "stale blocked status may only be used below the official baseline")
    else:
        _require(version_is_at_least(current["source_version"]), "CURRENT_DEVELOPMENT", "reconciled source must meet the official baseline")
    return {
        "status": "PASS",
        "schema_version": SCHEMA,
        "official_baseline": baseline["version"],
        "official_baseline_sha256": baseline["artifact_sha256"],
        "capabilities": {identifier: capabilities[identifier].get("status") for identifier in sorted(capabilities)},
        "roadmap": {identifier: roadmap[identifier].get("status") for identifier in sorted(roadmap)},
        "provenance_entries": len(provenance),
    }


def control_path(root: Path, explicit: str | None = None) -> Path:
    return (Path(explicit).expanduser() if explicit else root / DEFAULT_CONTROL_RELATIVE).resolve()


def validate_path(path: Path) -> dict[str, Any]:
    control = load_control(path)
    result = validate_control(control)
    result["control_path"] = str(path)
    return result


def validate_lineage_for_build(root: Path, version: str | None = None, *, control_file: Path | None = None) -> dict[str, Any]:
    """Validate build ancestry before package-release side effects occur."""

    root = root.resolve()
    path = (control_file or root / DEFAULT_CONTROL_RELATIVE).resolve()
    control = load_control(path)
    validation = validate_control(control)
    root_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    requested_version = version or root_version
    _require(requested_version == root_version, "LINEAGE_VERSION_MISMATCH", "requested package version differs from root VERSION")
    manifest_path = root / "manifest" / "package.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlError("LINEAGE_MANIFEST", f"cannot read manifest/package.json: {exc}") from exc
    _require(isinstance(manifest, dict) and manifest.get("version") == root_version, "LINEAGE_MANIFEST", "VERSION and manifest/package.json version differ")
    current = _object(control.get("current_development"), "current_development")
    _require(current.get("source_version") == root_version, "LINEAGE_SOURCE_UNREGISTERED", "root VERSION is not registered in current_development")
    _require(current.get("based_on_official_version") == OFFICIAL_BASELINE_VERSION, "LINEAGE_BASELINE_MISMATCH", "current development does not name the official version")
    _require(current.get("based_on_official_sha256") == OFFICIAL_BASELINE_SHA256, "LINEAGE_BASELINE_MISMATCH", "current development does not name the official SHA-256")
    if not version_is_at_least(root_version):
        raise ControlError(
            "LINEAGE_REGRESSION",
            f"development source {root_version} is below promoted baseline {OFFICIAL_BASELINE_VERSION}; update source metadata and lineage before packaging",
        )
    return {
        "status": "PASS",
        "package_version": root_version,
        "official_baseline": OFFICIAL_BASELINE_VERSION,
        "official_baseline_sha256": OFFICIAL_BASELINE_SHA256,
        "control_path": str(path),
        "control_validation": validation,
    }


def status_projection(control: dict[str, Any]) -> dict[str, Any]:
    """Derive a fresh-session status projection without copying authority."""

    validation = validate_control(control)
    capabilities = {item["id"]: item for item in _list(control["capability_status"], "capability_status")}
    roadmap = {item["id"]: item for item in _list(control["roadmap"]["items"], "roadmap.items")}
    current = _object(control["roadmap"].get("current"), "roadmap.current")
    next_item = _object(control["roadmap"].get("likely_next"), "roadmap.likely_next")
    return {
        "status": "PASS",
        "schema_version": STATUS_SCHEMA,
        "north_star": control["north_star"],
        "official_baseline": {
            "version": control["official_baseline"]["version"],
            "artifact_sha256": control["official_baseline"]["artifact_sha256"],
            "promotion_status": control["official_baseline"]["promotion_status"],
        },
        "completed": [identifier for identifier in ("C10", "C11", "C12", "C13", "C14", "C15", "C17", "C18", "C19") if identifier in capabilities and (capabilities[identifier].get("status") == "DONE" or roadmap.get(identifier, {}).get("status") == "DONE")],
        "blocked": ["C09"] if capabilities["C09"]["status"] == "BLOCKED" else [],
        "deferred": ["C08"] if capabilities["C08"]["status"] == "DEFERRED" else [],
        "current": {"id": current["id"], "status": current["status"], "title": current["title"]},
        "likely_next": {"id": next_item["id"], "status": next_item["status"], "title": next_item["title"]},
        "live_delegation": {
            "foundation_status": capabilities["C15"]["foundation_status"],
            "certified": capabilities["C15"]["live_delegation_certified"],
            "status": capabilities["C15"]["live_delegation_status"],
        },
        "parallel_execution": {
            "foundation_status": capabilities.get("C17", {}).get("foundation_status", "NOT_STARTED"),
            "certified": capabilities.get("C17", {}).get("live_parallel_execution_certified", False),
            "status": capabilities.get("C17", {}).get("live_parallel_execution_status", "NOT_CERTIFIED"),
        },
        "cognitive_economy": {
            "evaluated": capabilities.get("C17", {}).get("cognitive_economy_parallel_orchestration_evaluated", False),
            "status": capabilities.get("C17", {}).get("cognitive_economy_status", "NOT_EVALUATED"),
        },
        "design_intelligence": {
            "metadata_faculties": control["design_intelligence"]["metadata_faculties"],
            "primary_router": control["design_intelligence"]["primary_router"],
            "aesthetica": control["design_intelligence"]["aesthetica"],
        },
        "canonical_capability_count": control["canonical_capability_set"]["denominator"],
        "validation": {"official_baseline": validation["official_baseline"], "provenance_entries": validation["provenance_entries"]},
    }


def render_status(projection: dict[str, Any]) -> str:
    lines = [
        "P2P DEVELOPMENT STATUS: PASS",
        f"Official baseline: {projection['official_baseline']['version']} ({projection['official_baseline']['promotion_status']})",
        "Completed: " + ", ".join(projection["completed"]),
        "Blocked: " + (", ".join(projection["blocked"]) or "none"),
        "Deferred: " + (", ".join(projection["deferred"]) or "none"),
        f"Current: {projection['current']['id']} {projection['current']['status']} — {projection['current']['title']}",
        f"Likely next: {projection['likely_next']['id']} {projection['likely_next']['status']} — {projection['likely_next']['title']}",
        f"C15 live delegation: {projection['live_delegation']['status']} (certified={projection['live_delegation']['certified']})",
        f"C17 parallel execution: {projection['parallel_execution']['status']} (certified={projection['parallel_execution']['certified']})",
        f"C17 cognitive economy: {projection['cognitive_economy']['status']} (evaluated={projection['cognitive_economy']['evaluated']})",
        f"Canonical capability set: {projection['canonical_capability_count']}/8",
    ]
    return "\n".join(lines)


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _replace_active_version(path: Path, old_version: str, new_version: str) -> bytes:
    """Return an active metadata payload after one exact version replacement."""

    original = path.read_bytes()
    text = original.decode("utf-8")
    count = text.count(old_version)
    _require(count == 1, "LINEAGE_METADATA", f"expected one active version in {path}, found {count}")
    return text.replace(old_version, new_version).encode("utf-8")


def _write_bytes_atomic(path: Path, payload: bytes, suffix: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + suffix)
    temporary.write_bytes(payload)
    temporary.replace(path)


def reconcile_development_lineage(
    root: Path,
    target_version: str = C17_DEVELOPMENT_VERSION,
    evidence_refs: list[str] | None = None,
    *,
    control_file: Path | None = None,
    changed_at: str | None = None,
    changed_by: str = "p2p-c17-lineage-reconciliation",
) -> dict[str, Any]:
    """Reconcile active source metadata to a post-official development version.

    This is intentionally a guarded source operation. It updates only active
    version surfaces that still name the stale source version, keeps the
    promoted artifact untouched, validates the resulting control record before
    writing, and restores every changed file if one atomic replacement fails.
    """

    root = root.resolve()
    path = (control_file or root / DEFAULT_CONTROL_RELATIVE).resolve()
    refs = evidence_refs or []
    _require(isinstance(refs, list) and all(isinstance(item, str) and item.strip() for item in refs), "PROVENANCE", "evidence_refs must be a list of non-empty strings")
    _nonempty_string(changed_by, "changed_by")
    _version_key(target_version, "target_version")
    _require(version_is_at_least(target_version), "LINEAGE_REGRESSION", "target development version must meet the official baseline")
    _require(target_version != OFFICIAL_BASELINE_VERSION, "LINEAGE_TARGET", "target development version must remain an unpromoted candidate, not the official version")

    control = load_control(path)
    validate_control(control)
    current = _object(control.get("current_development"), "current_development")
    old_version = _nonempty_string(current.get("source_version"), "current_development.source_version")
    _require(current.get("source_version_status") == "STALE_BLOCKED_BELOW_OFFICIAL", "LINEAGE_RECONCILIATION_STATE", "reconciliation requires the explicitly stale source state")
    _require(not version_is_at_least(old_version), "LINEAGE_RECONCILIATION_STATE", "reconciliation source must be below the official baseline")
    _require(current.get("based_on_official_version") == OFFICIAL_BASELINE_VERSION, "LINEAGE_BASELINE_MISMATCH", "current development does not name the official version")
    _require(current.get("based_on_official_sha256") == OFFICIAL_BASELINE_SHA256, "LINEAGE_BASELINE_MISMATCH", "current development does not name the official SHA-256")

    version_path = root / "VERSION"
    manifest_path = root / "manifest" / "package.json"
    _require(version_path.is_file() and manifest_path.is_file(), "LINEAGE_METADATA", "VERSION and manifest/package.json are required for reconciliation")
    _require(version_path.read_text(encoding="utf-8").strip() == old_version, "LINEAGE_METADATA", "root VERSION does not match current_development.source_version")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlError("LINEAGE_MANIFEST", f"cannot read manifest/package.json: {exc}") from exc
    _require(isinstance(manifest, dict) and manifest.get("version") == old_version, "LINEAGE_METADATA", "manifest/package.json does not match current source version")

    metadata_paths = [
        version_path,
        manifest_path,
        root / ".p2p" / "system" / "VERSION",
        root / ".p2p" / "system" / "p2p.manifest.json",
        root / ".p2p" / "system" / "p2p_uiux" / "__init__.py",
        root / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json",
        root / "RELEASE-NOTES.md",
    ]
    metadata_payloads: dict[Path, bytes] = {}
    for metadata_path in metadata_paths:
        if not metadata_path.exists():
            continue
        metadata_payloads[metadata_path] = _replace_active_version(metadata_path, old_version, target_version)

    updated = copy.deepcopy(control)
    updated_current = _object(updated.get("current_development"), "current_development")
    updated_current.update(
        {
            "source_version": target_version,
            "source_version_status": "LINEAGE_RECONCILED",
            "source_drift_classification": {
                "primary": "RECONCILED_TO_PROMOTED_BASELINE",
                "contributors": ["C17_LINEAGE_RECONCILIATION"],
                "implementation_bug": False,
                "evidence_refs": refs,
            },
            "owner_action_required": "Continue C17 implementation and validation; promotion remains a separate protected action.",
            "lineage_reconciliation": {
                "from_source_version": old_version,
                "to_source_version": target_version,
                "based_on_official_version": OFFICIAL_BASELINE_VERSION,
                "based_on_official_sha256": OFFICIAL_BASELINE_SHA256,
                "evidence_refs": refs,
            },
        }
    )
    stamp = changed_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    _nonempty_string(stamp, "changed_at")
    provenance = _list(updated.get("provenance_log"), "provenance_log")
    provenance.append(
        {
            "change_id": f"C17-LINEAGE-{len(provenance) + 1:03d}",
            "changed_at": stamp,
            "changed_by": changed_by,
            "what_changed": f"active development metadata: {old_version} -> {target_version}; official .19 ancestry retained",
            "why": "C17 requires a coherent development line after the promoted .19 baseline while preserving the cumulative C10-C16 source.",
            "evidence_refs": refs,
        }
    )
    validate_control(updated)

    originals = {candidate: candidate.read_bytes() for candidate in metadata_payloads}
    originals[path] = path.read_bytes()
    try:
        for metadata_path, payload in metadata_payloads.items():
            _write_bytes_atomic(metadata_path, payload, ".c17-lineage.tmp")
        _write_json_atomic(path, updated)
    except (OSError, ValueError, ControlError) as exc:
        for original_path, payload in originals.items():
            try:
                _write_bytes_atomic(original_path, payload, ".c17-lineage.rollback.tmp")
            except OSError:
                pass
        if isinstance(exc, ControlError):
            raise
        raise ControlError("LINEAGE_RECONCILIATION_FAILED", f"atomic metadata reconciliation failed: {exc}") from exc

    return {
        "status": "PASS",
        "from_source_version": old_version,
        "source_version": target_version,
        "official_baseline": OFFICIAL_BASELINE_VERSION,
        "official_baseline_sha256": OFFICIAL_BASELINE_SHA256,
        "metadata_paths": [str(candidate) for candidate in metadata_payloads],
        "control_path": str(path),
    }


def record_c17_completion(
    path: Path,
    *,
    candidate_sha256: str,
    candidate_label: str,
    candidate_artifact_path: str,
    evidence_refs: list[str],
    changed_at: str | None = None,
    changed_by: str = "p2p-c17",
) -> dict[str, Any]:
    """Record C17 PASS/foundation readiness without promoting its artifact."""

    _require(re.fullmatch(r"[0-9a-f]{64}", candidate_sha256 or "") is not None, "LINEAGE_HASH", "C17 candidate SHA-256 is invalid")
    _nonempty_string(candidate_label, "candidate_label")
    _nonempty_string(candidate_artifact_path, "candidate_artifact_path")
    _require(isinstance(evidence_refs, list) and all(isinstance(item, str) and item.strip() for item in evidence_refs), "PROVENANCE", "evidence_refs must be a list of non-empty strings")
    control = load_control(path)
    validate_control(control)
    current = _object(control.get("current_development"), "current_development")
    _require(current.get("source_version") == C17_DEVELOPMENT_VERSION, "C17_LINEAGE", "C17 completion requires the reconciled .20 source")
    updated = copy.deepcopy(control)
    updated_current = _object(updated.get("current_development"), "current_development")
    updated_current.update(
        {
            "development_goal": "C17",
            "status": "PASS",
            "source_version_status": "CANDIDATE_UNPROMOTED",
            "owner_action_required": "C17 foundation PASS; candidate remains UNPROMOTED and live parallel execution is NOT_CERTIFIED.",
        }
    )
    roadmap = _object(updated.get("roadmap"), "roadmap")
    items = _list(roadmap.get("items"), "roadmap.items")
    by_id = {item.get("id"): item for item in items if isinstance(item, dict)}
    _require(by_id.get("C16", {}).get("status") == "ACTIVE" and by_id.get("C17", {}).get("status") == "PLANNED", "C17_ROADMAP", "C17 completion requires the C16 ACTIVE/C17 PLANNED state")
    by_id["C16"]["status"] = "DONE"
    by_id["C17"].update({"status": "DONE", "evidence_ref": evidence_refs[0] if evidence_refs else "C17 PASS"})
    roadmap["current"] = {"id": "C17", "status": "DONE", "title": by_id["C17"].get("title", "Safe bounded parallel foreground execution")}
    next_goal_id, next_goal_status = _likely_next_goal(_goal_ids_in_order(by_id), by_id)
    roadmap["likely_next"] = {"id": next_goal_id, "status": next_goal_status, "title": by_id.get(next_goal_id, {}).get("title", "")}
    roadmap["stop_rule"] = "After C17 foundation and validation verify PASS, stop before any optional hardening or promotion."
    capabilities = _list(updated.get("capability_status"), "capability_status")
    c17 = next((item for item in capabilities if isinstance(item, dict) and item.get("id") == "C17"), None)
    if c17 is None:
        c17 = {"id": "C17"}
        capabilities.append(c17)
    c17.update(
        {
            "status": "DONE",
            "result": "PASS",
            "foundation_status": "PARALLEL_EXECUTION_FOUNDATION_READY",
            "live_parallel_execution_certified": False,
            "live_parallel_execution_status": "NOT_CERTIFIED",
            "candidate_id": "C17",
            "evidence_ref": evidence_refs[0] if evidence_refs else "C17 PASS",
            "cognitive_economy_parallel_orchestration_evaluated": bool(c17.get("cognitive_economy_parallel_orchestration_evaluated", False)),
            "cognitive_economy_status": c17.get("cognitive_economy_status", "NOT_EVALUATED"),
        }
    )
    candidates = _list(updated.get("candidate_records"), "candidate_records")
    _require(not any(isinstance(item, dict) and item.get("candidate_id") == "C17" for item in candidates), "C17_LINEAGE", "C17 candidate lineage is already recorded")
    candidates.append(
        {
            "candidate_id": "C17",
            "based_on_official_version": OFFICIAL_BASELINE_VERSION,
            "based_on_official_sha256": OFFICIAL_BASELINE_SHA256,
            "development_goal": "C17",
            "candidate_version": C17_DEVELOPMENT_VERSION,
            "candidate_label": candidate_label,
            "candidate_sha256": candidate_sha256,
            "embedded_version": C17_DEVELOPMENT_VERSION,
            "promotion_status": "UNPROMOTED",
            "lineage_status": "LINEAGE_RECONCILED",
            "artifact_path": candidate_artifact_path,
            "evidence_refs": evidence_refs,
        }
    )
    stamp = changed_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    provenance = _list(updated.get("provenance_log"), "provenance_log")
    provenance.append(
        {
            "change_id": f"C17-COMPLETION-{len(provenance) + 1:03d}",
            "changed_at": stamp,
            "changed_by": changed_by,
            "what_changed": "C17 recorded DONE/PASS with parallel foundation ready and live certification NOT_CERTIFIED; candidate remains UNPROMOTED.",
            "why": "C17 validation and supervisor evidence completed without changing promoted authority.",
            "evidence_refs": evidence_refs,
        }
    )
    validate_control(updated)
    _write_json_atomic(path, updated)
    return {"status": "PASS", "candidate_id": "C17", "candidate_sha256": candidate_sha256, "control_path": str(path)}


def refresh_c17_candidate_artifact(
    path: Path,
    *,
    candidate_sha256: str,
    candidate_label: str,
    candidate_artifact_path: str,
    evidence_refs: list[str],
    changed_at: str | None = None,
    changed_by: str = "p2p-c17-candidate-refresh",
) -> dict[str, Any]:
    """Bind a rebuilt unpromoted C17 artifact to the existing candidate record."""

    _require(re.fullmatch(r"[0-9a-f]{64}", candidate_sha256 or "") is not None, "LINEAGE_HASH", "C17 candidate SHA-256 is invalid")
    _nonempty_string(candidate_label, "candidate_label")
    _nonempty_string(candidate_artifact_path, "candidate_artifact_path")
    _require(isinstance(evidence_refs, list) and all(isinstance(item, str) and item.strip() for item in evidence_refs), "PROVENANCE", "evidence_refs must be a list of non-empty strings")
    control = load_control(path)
    validate_control(control)
    current = _object(control.get("current_development"), "current_development")
    _require(current.get("development_goal") == "C17" and current.get("status") == "PASS", "C17_STATE", "candidate refresh requires C17 PASS state")
    roadmap = _object(control.get("roadmap"), "roadmap")
    _require(roadmap.get("current", {}).get("id") == "C17" and roadmap.get("current", {}).get("status") == "DONE", "C17_ROADMAP", "candidate refresh requires C17 DONE roadmap state")
    updated = copy.deepcopy(control)
    candidates = _list(updated.get("candidate_records"), "candidate_records")
    candidate = next((item for item in candidates if isinstance(item, dict) and item.get("candidate_id") == "C17"), None)
    _require(candidate is not None, "C17_LINEAGE", "C17 candidate lineage is missing")
    previous_artifact = {
        "candidate_label": candidate.get("candidate_label"),
        "candidate_sha256": candidate.get("candidate_sha256"),
        "artifact_path": candidate.get("artifact_path"),
        "promotion_status": candidate.get("promotion_status"),
    }
    history = candidate.setdefault("historical_artifacts", [])
    if previous_artifact.get("candidate_sha256") and previous_artifact.get("candidate_sha256") != candidate_sha256:
        history.append(previous_artifact)
    candidate.update(
        {
            "candidate_label": candidate_label,
            "candidate_sha256": candidate_sha256,
            "artifact_path": candidate_artifact_path,
            "promotion_status": "UNPROMOTED",
            "evidence_refs": evidence_refs,
        }
    )
    stamp = changed_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    provenance = _list(updated.get("provenance_log"), "provenance_log")
    provenance.append(
        {
            "change_id": f"C17-CANDIDATE-{len(provenance) + 1:03d}",
            "changed_at": stamp,
            "changed_by": changed_by,
            "what_changed": "C17 candidate record rebound to the final rebuilt unpromoted artifact.",
            "why": "The new candidate carries the bounded cognitive-economy slice; the prior candidate remains recorded as historical and unpromoted.",
            "evidence_refs": evidence_refs,
            "previous_candidate": previous_artifact,
            "new_candidate_sha256": candidate_sha256,
        }
    )
    validate_control(updated)
    _write_json_atomic(path, updated)
    return {"status": "PASS", "candidate_id": "C17", "candidate_sha256": candidate_sha256, "control_path": str(path)}


def record_c17_cognitive_economy_evaluation(
    path: Path,
    *,
    evidence_refs: list[str],
    changed_at: str | None = None,
    changed_by: str = "p2p-c17-cognitive-economy",
) -> dict[str, Any]:
    """Record the bounded cognitive-economy evaluation without promotion."""

    _require(isinstance(evidence_refs, list) and all(isinstance(item, str) and item.strip() for item in evidence_refs), "PROVENANCE", "evidence_refs must be a list of non-empty strings")
    control = load_control(path)
    validate_control(control)
    current = _object(control.get("current_development"), "current_development")
    _require(current.get("development_goal") == "C17" and current.get("status") == "PASS", "C17_STATE", "cognitive economy evaluation requires C17 PASS state")
    updated = copy.deepcopy(control)
    updated_current = _object(updated.get("current_development"), "current_development")
    updated_current["cognitive_economy_status"] = "EVALUATED_BOUNDED_PARALLEL_SLICE"
    updated_current["owner_action_required"] = "C17 foundation PASS; cognitive economy evaluated; candidate remains UNPROMOTED and live parallel execution is NOT_CERTIFIED."
    capabilities = _list(updated.get("capability_status"), "capability_status")
    c17 = next((item for item in capabilities if isinstance(item, dict) and item.get("id") == "C17"), None)
    _require(c17 is not None, "C17_STATE", "C17 capability status is missing")
    c17["cognitive_economy_parallel_orchestration_evaluated"] = True
    c17["cognitive_economy_status"] = "EVALUATED_BOUNDED_PARALLEL_SLICE"
    c17["cognitive_economy_evidence_ref"] = evidence_refs[0] if evidence_refs else "C17 cognitive economy evaluation"
    stamp = changed_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    provenance = _list(updated.get("provenance_log"), "provenance_log")
    provenance.append(
        {
            "change_id": f"C17-COGNITIVE-ECONOMY-{len(provenance) + 1:03d}",
            "changed_at": stamp,
            "changed_by": changed_by,
            "what_changed": "C17 cognitive economy status recorded as an evaluated bounded parallel orchestration slice.",
            "why": "CE1-CE10 and focused quality/non-regression evidence cover economy gates while preserving the existing C17 safety foundation and unpromoted candidate boundary.",
            "evidence_refs": evidence_refs,
        }
    )
    validate_control(updated)
    _write_json_atomic(path, updated)
    return {"status": "PASS", "cognitive_economy_status": c17["cognitive_economy_status"], "control_path": str(path)}


def record_roadmap_mutation(path: Path, item_id: str, status: str, reason: str, evidence_refs: list[str], *, changed_at: str | None = None, changed_by: str = "p2p") -> dict[str, Any]:
    """Apply one explicit roadmap mutation and append its provenance entry."""

    _require(status in ROADMAP_STATUSES, "ROADMAP_STATUS", f"unknown roadmap status: {status}")
    _nonempty_string(item_id, "item_id")
    _nonempty_string(reason, "reason")
    _require(isinstance(evidence_refs, list) and all(isinstance(item, str) and item.strip() for item in evidence_refs), "PROVENANCE", "evidence_refs must be a list of non-empty strings")
    control = load_control(path)
    validate_control(control)
    items = _list(_object(control.get("roadmap"), "roadmap").get("items"), "roadmap.items")
    target = next((item for item in items if isinstance(item, dict) and item.get("id") == item_id), None)
    _require(target is not None, "ROADMAP_ITEM_MISSING", f"roadmap item is missing: {item_id}")
    previous_status = target.get("status")
    target["status"] = status
    roadmap = _object(control["roadmap"], "roadmap")
    if item_id == "C16":
        roadmap["current"] = {"id": item_id, "status": status, "title": target.get("title", "")}
    stamp = changed_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    _nonempty_string(stamp, "changed_at")
    _nonempty_string(changed_by, "changed_by")
    provenance = _list(control.get("provenance_log"), "provenance_log")
    change_number = len(provenance) + 1
    provenance.append(
        {
            "change_id": f"C16-ROADMAP-{change_number:03d}",
            "changed_at": stamp,
            "changed_by": changed_by,
            "what_changed": f"roadmap.{item_id}.status: {previous_status} -> {status}",
            "why": reason,
            "evidence_refs": evidence_refs,
        }
    )
    validate_control(control)
    _write_json_atomic(path, control)
    return {"status": "PASS", "item_id": item_id, "previous_status": previous_status, "status_after": status, "provenance_entry": provenance[-1], "control_path": str(path)}


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(command: argparse.ArgumentParser) -> None:
        command.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
        command.add_argument("--control")
        command.add_argument("--json", action="store_true")

    validate = sub.add_parser("validate", help="Validate the durable control record")
    add_common(validate)
    status = sub.add_parser("status", help="Render a fresh-session status projection")
    add_common(status)
    mutate = sub.add_parser("record-roadmap", help="Record one explicit roadmap status mutation")
    add_common(mutate)
    mutate.add_argument("--item-id", required=True)
    mutate.add_argument("--status", required=True)
    mutate.add_argument("--reason", required=True)
    mutate.add_argument("--evidence-ref", action="append", default=[])
    mutate.add_argument("--changed-at")
    mutate.add_argument("--changed-by", default="p2p")
    reconcile = sub.add_parser("reconcile-lineage", help="Reconcile stale active source metadata to a post-official development version")
    add_common(reconcile)
    reconcile.add_argument("--target-version", default=C17_DEVELOPMENT_VERSION)
    reconcile.add_argument("--evidence-ref", action="append", default=[])
    reconcile.add_argument("--changed-at")
    reconcile.add_argument("--changed-by", default="p2p-c17-lineage-reconciliation")
    complete = sub.add_parser("record-c17-completion", help="Record C17 PASS/foundation readiness without promotion")
    add_common(complete)
    complete.add_argument("--candidate-sha256", required=True)
    complete.add_argument("--candidate-label", required=True)
    complete.add_argument("--candidate-artifact-path", required=True)
    complete.add_argument("--evidence-ref", action="append", default=[])
    complete.add_argument("--changed-at")
    complete.add_argument("--changed-by", default="p2p-c17")
    refresh = sub.add_parser("refresh-c17-candidate", help="Bind a rebuilt unpromoted C17 artifact to its durable candidate record")
    add_common(refresh)
    refresh.add_argument("--candidate-sha256", required=True)
    refresh.add_argument("--candidate-label", required=True)
    refresh.add_argument("--candidate-artifact-path", required=True)
    refresh.add_argument("--evidence-ref", action="append", default=[])
    refresh.add_argument("--changed-at")
    refresh.add_argument("--changed-by", default="p2p-c17-candidate-refresh")
    economy = sub.add_parser("record-c17-cognitive-economy", help="Record the bounded C17 cognitive-economy evaluation without promotion")
    add_common(economy)
    economy.add_argument("--evidence-ref", action="append", default=[])
    economy.add_argument("--changed-at")
    economy.add_argument("--changed-by", default="p2p-c17-cognitive-economy")
    return parser


def main(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    path = control_path(root, args.control)
    if args.command == "validate":
        result = validate_path(path)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"PASS: {path}")
        return 0
    if args.command == "status":
        projection = status_projection(load_control(path))
        print(json.dumps(projection, ensure_ascii=False, indent=2) if args.json else render_status(projection))
        return 0
    if args.command == "reconcile-lineage":
        result = reconcile_development_lineage(root, args.target_version, args.evidence_ref, control_file=path, changed_at=args.changed_at, changed_by=args.changed_by)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"PASS: lineage reconciled to {args.target_version}")
        return 0
    if args.command == "record-c17-completion":
        result = record_c17_completion(
            path,
            candidate_sha256=args.candidate_sha256,
            candidate_label=args.candidate_label,
            candidate_artifact_path=args.candidate_artifact_path,
            evidence_refs=args.evidence_ref,
            changed_at=args.changed_at,
            changed_by=args.changed_by,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else "PASS: C17 recorded DONE/PASS without promotion")
        return 0
    if args.command == "refresh-c17-candidate":
        result = refresh_c17_candidate_artifact(
            path,
            candidate_sha256=args.candidate_sha256,
            candidate_label=args.candidate_label,
            candidate_artifact_path=args.candidate_artifact_path,
            evidence_refs=args.evidence_ref,
            changed_at=args.changed_at,
            changed_by=args.changed_by,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else "PASS: C17 candidate artifact refreshed without promotion")
        return 0
    if args.command == "record-c17-cognitive-economy":
        result = record_c17_cognitive_economy_evaluation(
            path,
            evidence_refs=args.evidence_ref,
            changed_at=args.changed_at,
            changed_by=args.changed_by,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else "PASS: C17 cognitive economy evaluation recorded without promotion")
        return 0
    result = record_roadmap_mutation(path, args.item_id, args.status, args.reason, args.evidence_ref, changed_at=args.changed_at, changed_by=args.changed_by)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"PASS: roadmap {args.item_id} -> {args.status}")
    return 0


if __name__ == "__main__":
    parsed = parser().parse_args()
    try:
        raise SystemExit(main(parsed))
    except ControlError as exc:
        if getattr(parsed, "json", False):
            print(json.dumps({"status": "BLOCKED", "error": {"code": exc.code, "message": exc.message}}, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR [{exc.code}]: {exc.message}", file=sys.stderr)
        raise SystemExit(2) from exc
    except (OSError, ValueError, RuntimeError) as exc:
        if getattr(parsed, "json", False):
            print(json.dumps({"status": "BLOCKED", "error": {"code": "UNEXPECTED", "message": str(exc)}}, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
