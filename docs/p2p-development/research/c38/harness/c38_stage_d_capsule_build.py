"""C38 Stage D — build the minimal continuation capsule and C36 delivery envelope.

Capsule design per Stage-D instruction §4:
- ONLY durable verified state from Stage B; NO Stage-B Manus transcript;
  NO natural-language conversation history. TRANSCRIPT != STATE.
- Fresh unpredictable NON-SECRET CAPSULE_CHALLENGE_ID (random hex token,
  no credential, no authority; exists only to prove capsule receipt).
- Deterministic SHA-based checksum over non-secret capsule field for
  the required transformation (§6).
- Capsule + envelope are written to evidence; nothing secret is read
  into any file (key stays out-of-repo at all times).
"""
from __future__ import annotations

import dataclasses
import json
import secrets
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / ".p2p" / "system"))

from p2p_capabilities.context_envelope import (  # noqa: E402
    DeliveryEnvelope, build_delivery_receipt, _fingerprint)
from p2p_capabilities.context_manifest import ContextManifest  # noqa: E402

EVIDENCE = REPO / "docs" / "p2p-development" / "research" / "c38" / "evidence"

# ---------- Stage-B durable verified state (recovered from checkpoint) ----------
STAGE_B = {
    "role_id": "p2p_iris",
    "role_spec_hash": "1c0ea4d2196d59493001dc43bec50c31845a6681f8171409322fe569b172b4b2",
    "backend_id": "manus-rest-api-v2",
    "previous_receipt_pointer": "manus-task:NWnoWkrrJeQiYWZMv8jCS5",
    "role_verdict": "VERIFIED",
    "mutation_state": "NO_MUTATION_OBSERVED",
}

GIT_START_REVISION = "2a371777438c88867138203e0b0bcc04283d8bed"  # Stage-B terminal report HEAD
PROJECT_ID = "P2P-upgrade-github-1"
GOAL_ID = "C38"
NEXT_TASK_ID = "c38-stage-d-fresh-session-capsule-proof"

# ---------- Fresh non-secret challenge ----------
CAPSULE_CHALLENGE_ID = "challenge-" + secrets.token_hex(8)  # 16 hex chars
assert "challenge-" in CAPSULE_CHALLENGE_ID and len(CAPSULE_CHALLENGE_ID.split("-")[1]) == 16

# ---------- Minimal continuation capsule (§4 fields) ----------
capsule = {
    "schema": "p2p-continuation-capsule/1",
    "capsule_id": CAPSULE_CHALLENGE_ID,
    "project_id": PROJECT_ID,
    "goal_id": GOAL_ID,
    "current_stage": "D",
    "previous_verified_stage": "B",
    "current_verified_git_revision": GIT_START_REVISION,
    "role_id": STAGE_B["role_id"],
    "role_spec_hash": STAGE_B["role_spec_hash"],
    "previous_backend_id": STAGE_B["backend_id"],
    "previous_receipt_pointer": STAGE_B["previous_receipt_pointer"],
    "mutation_state": STAGE_B["mutation_state"],
    "current_owner_gate": "SECOND_BACKEND_AUTH_REQUIRED",
    "next_task_id": NEXT_TASK_ID,
    "verification_rule": (
        "Fresh execution must return a structured result containing: "
        "project_id, goal_id, current_stage, role_id, "
        "current_verified_git_revision, capsule_id, next_owner_gate, "
        "plus challenge_hash = sha256(capsule_id) exactly. "
        "Acceptance: exact string equality for every field; accidental "
        "success probability <= 2^-128 on the challenge hash."
    ),
    "challenge_hash_source_field": "capsule_id",
    "source_evidence_pointers": [
        "docs/p2p-development/research/c38/evidence/c38-stage-b-role-contract.json",
        "docs/p2p-development/research/c38/evidence/c38-stage-b-live-receipt.json",
        "docs/p2p-development/research/c38/evidence/c38-stage-b-role-receipt.json",
        "docs/p2p-development/research/c38/evidence/c38-stage-b-messages-observed.json",
        "docs/p2p-development/research/c38/c38-task-graph-revision.md",
    ],
    "notes": {
        "transcript_excluded": True,
        "conversation_history_excluded": True,
        "no_credential_data": True,
    },
}

# Deterministic transformation: SHA256 of capsule_id (non-secret field)
challenge_hash = _fingerprint(capsule["capsule_id"])
capsule["challenge_hash_expected"] = challenge_hash

capsule_path = EVIDENCE / "c38-stage-d-continuation-capsule.json"
capsule_path.write_text(json.dumps(capsule, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------- C36 context manifest + delivery envelope + receipt ----------
manifest_item = {
    "item_id": "continuation-capsule:stage-d",
    "source_pointer": str(capsule_path),
    "source_type": "p2p-continuation-capsule/1",
    "authority_class": "EVIDENCE",
    "content_hash": _fingerprint(capsule),
    "required": "REQUIRED",
    "delta_allowed": False,
    "freshness": "CURRENT",
    "relevance_reason": "Stage-D fresh-session recovery from durable capsule",
    "scope_binding": "NON_MUTATING_TASK",
    "permission_class": "NON_MUTATING",
    "expected_use": "Bounded structured recovery task; transcript explicitly excluded",
}
manifest = ContextManifest(
    goal_id=GOAL_ID,
    task_id=NEXT_TASK_ID,
    project_binding=PROJECT_ID,
    workspace_binding=PROJECT_ID,
    environment_binding="LOCAL_PROJECT",
    source_revision=GIT_START_REVISION,
    context_requirement_revision="p2p-c38-stage-d/1",
    items=(manifest_item,),
    role_id=capsule["role_id"],
)
ROLE_SPEC_HASH = capsule["role_spec_hash"]
target_payload = {
    "execution_target": "manus-api-v2",
    "task_id": NEXT_TASK_ID,
    "role_id": capsule["role_id"],
}
target_fp = _fingerprint(target_payload)
request_fp = _fingerprint({"task_id": NEXT_TASK_ID, "goal_id": GOAL_ID,
                           "capsule_id": capsule["capsule_id"]})
envelope = DeliveryEnvelope(
    manifest_id="p2p-c38-stage-d-capsule-manifest",
    manifest_hash=_fingerprint({"capsule": capsule_path.name,
                                "schema": capsule["schema"],
                                "items": sorted(capsule.keys())}),
    goal_id=GOAL_ID,
    task_id=NEXT_TASK_ID,
    execution_target="manus-api-v2",
    target_fingerprint=target_fp,
    workspace=PROJECT_ID,
    environment="LOCAL_PROJECT",
    permission_profile=("NON_MUTATING_TASK",),
    items_selected=("continuation-capsule:stage-d",),
    delivery_order=("continuation-capsule:stage-d",),
    delivery_format="json-inline",
    compression_record=(),
    delivery_budget="bounded-single-request",
    request_fingerprint=request_fp,
    role_id=capsule["role_id"],
)
receipt = build_delivery_receipt(
    manifest=manifest,
    envelope=envelope,
    items_delivered=(),  # nothing delivered yet; DELIVERED at task.submit time
    delivery_status="PARTIAL",  # SELECTED but not yet delivered — honest status per scenario D
)

receipt_path = EVIDENCE / "c38-stage-d-delivery-receipt.json"
receipt_path.write_text(json.dumps(dataclasses.asdict(receipt), indent=2, ensure_ascii=False), encoding="utf-8")

print("CAPSULE_ID:", capsule["capsule_id"])
print("CHALLENGE_HASH:", challenge_hash)
print("ENVELOPE_IDENTITY:", envelope.identity())
print("RECEIPT_STATUS:", receipt["delivery_status"] if isinstance(receipt, dict) else receipt.delivery_status)
print("CAPSULE_FILE:", capsule_path)
print("RECEIPT_FILE:", receipt_path)
print("NOTE: capsule carries NO transcript, NO conversation history, NO credentials.")
