"""Focused proof for the reasoning/execution decoupling gap patch.

These tests exercise the existing C34/C35 contract, certification, receipt,
eligibility, and independent verifier surfaces.  They intentionally use
synthetic in-memory target records: no provider, network, MCP server, or
filesystem mutation is part of this proof.
"""
from __future__ import annotations

import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM_ROOT = os.path.join(REPO_ROOT, ".p2p", "system")
if SYSTEM_ROOT not in sys.path:
    sys.path.insert(0, SYSTEM_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from p2p_capabilities.agent_role import (  # noqa: E402
    CANONICAL_ROLE_DENOMINATOR,
    CANONICAL_ROLES,
    build_role_spec,
)
from p2p_capabilities.backend_contract import (  # noqa: E402
    EXECUTION_CLAIM_REQUIREMENTS,
    OPERATIONAL_CAPABILITIES,
    STATIC_REASONING_EXECUTION_EVIDENCE_INVARIANT,
    BackendCapabilityCertification,
    BackendExecutionResult,
)
from p2p_capabilities.fake_targets import (  # noqa: E402
    fake_target_certification_record,
    fake_target_fingerprint,
)
from p2p_capabilities.role_contract import (  # noqa: E402
    build_role_execution_contract,
)
from p2p_capabilities.role_eligibility import (  # noqa: E402
    evaluate_role_target_eligibility,
)
from p2p_capabilities.role_receipt import (  # noqa: E402
    RoleExecutionReceipt,
    new_role_receipt,
)
from p2p_capabilities.role_verifier import (  # noqa: E402
    permission_profile_fingerprint,
    verify_role_execution_receipt,
)


TARGET_ID = "fake-codex"
ADAPTER_ID = "adapter-fake-codex"
PROJECT = "P2P-upgrade-github-1"
TARGET_FINGERPRINT = fake_target_fingerprint(TARGET_ID)
TASK_FINGERPRINT = "b" * 64
NOW = "2026-08-29T00:00:00Z"


def _contract(
    *,
    task_caps=(),
    acceptance=(),
    reasoning_provider="",
):
    return build_role_execution_contract(
        build_role_spec("p2p_anon"),
        goal_id="goal:reasoning-execution",
        task_id="task:reasoning-execution",
        task_objective="Prove the bounded reasoning/execution contract.",
        project_binding=PROJECT,
        environment_binding="LOCAL_PROJECT",
        workspace_binding="synthetic-workspace",
        permission_profile=("READ",),
        acceptance_criteria=acceptance,
        task_required_capabilities=task_caps,
        explicit_execution_target=TARGET_ID,
        target_fingerprint=TARGET_FINGERPRINT,
        reasoning_provider_id=reasoning_provider,
    )


def _eligibility(contract, scopes):
    target = fake_target_certification_record(
        TARGET_ID,
        certified_scopes=tuple(scopes),
        current_auth_state="VALID",
    )
    return evaluate_role_target_eligibility(
        role_required_capabilities=contract.required_capabilities,
        role_permission_ceiling=("READ",),
        role_quorum_semantics="CANONICAL_QUORUM_MEMBER",
        required_evidence=contract.required_evidence,
        task_permission_profile=contract.permission_profile,
        goal_permission_envelope=("READ",),
        target=target,
        environment_binding=contract.environment_binding,
        workspace_binding=contract.workspace_binding,
    )


def _execution_artifacts(contract, *, evidence=(), result_adapter=ADAPTER_ID,
                         receipt_observed=ADAPTER_ID,
                         result_target_fingerprint=TARGET_FINGERPRINT):
    evidence = tuple(evidence)
    receipt = RoleExecutionReceipt(new_role_receipt(
        role_id=contract.role_id,
        role_spec_hash=contract.role_spec_hash,
        goal_id=contract.goal_id,
        task_id=contract.task_id,
        project_binding=contract.project_binding,
        environment_binding=contract.environment_binding,
        context_digest=contract.context_digest,
        permission_profile=contract.permission_profile,
        permission_profile_fingerprint=permission_profile_fingerprint(
            contract.permission_profile),
        request_fingerprint=contract.request_fingerprint,
        task_fingerprint=TASK_FINGERPRINT,
        reasoning_provider_id=contract.reasoning_provider_id,
        requested_target=contract.explicit_execution_target,
        observed_target=receipt_observed,
        target_attestation_status="PROFILE_BOUND",
        target_fingerprint=contract.target_fingerprint,
        execution_status="SUCCEEDED",
        evidence_pointers=(
            "evidence:claim",
            "evidence:boundary-evidence",
            "target-observation:" + receipt_observed,
        ) + evidence,
        execution_evidence_pointers=evidence,
        verifier_result="VERIFIED",
        mutation_state="NO_MUTATION_OBSERVED",
        failure_class="NONE",
        timestamps={
            "executed_at": NOW,
            "finished_at": NOW,
            "verified_at": NOW,
        },
        raw_backend_receipt_pointer="raw-backend:reasoning-execution",
    ))
    backend_result = BackendExecutionResult(
        request_id="request:reasoning-execution",
        request_fingerprint_hex=TASK_FINGERPRINT,
        task_id=contract.task_id,
        goal_id=contract.goal_id,
        adapter_id=result_adapter,
        execution_status="SUCCEEDED",
        verification_status="VERIFIED",
        started_at=NOW,
        finished_at=NOW,
        target_fingerprint=result_target_fingerprint,
        artifact_pointers=("artifact:reasoning-execution",),
        execution_evidence_pointers=evidence,
        auth_state_after="VALID",
        raw_backend_receipt_pointer="raw-backend:reasoning-execution",
    )
    return receipt, backend_result


def _verify(contract, *, scopes, evidence=(), result_adapter=ADAPTER_ID,
            receipt_observed=ADAPTER_ID,
            result_target_fingerprint=TARGET_FINGERPRINT):
    receipt, backend_result = _execution_artifacts(
        contract,
        evidence=evidence,
        result_adapter=result_adapter,
        receipt_observed=receipt_observed,
        result_target_fingerprint=result_target_fingerprint,
    )
    record = fake_target_certification_record(
        receipt_observed.removeprefix("adapter-"),
        certified_scopes=tuple(scopes),
        current_auth_state="VALID",
    )
    return verify_role_execution_receipt(
        receipt=receipt,
        expected_contract=contract,
        expected_role_spec_hash=contract.role_spec_hash,
        expected_permission_profile=contract.permission_profile,
        backend_result=backend_result,
        required_evidence=contract.required_evidence,
        observed_target_evidence_pointers=(
            "target-observation:" + receipt_observed,),
        certification_records=record.scope_certifications,
    )


def test_operational_vocabulary_is_exactly_one_certification_scope_set():
    assert OPERATIONAL_CAPABILITIES == (
        "REPO_READ", "REPO_SEARCH", "STATIC_ANALYSIS", "CODE_GENERATE",
        "CODE_PATCH", "FILESYSTEM_READ", "FILESYSTEM_WRITE",
        "TERMINAL_EXECUTE", "TEST_EXECUTE", "BUILD_EXECUTE",
        "BROWSER_EXECUTE", "DATABASE_SANDBOX", "GIT_WRITE", "REMOTE_PUSH",
    )
    assert len(OPERATIONAL_CAPABILITIES) == 14
    for capability in OPERATIONAL_CAPABILITIES:
        cert = BackendCapabilityCertification(
            adapter_id=ADAPTER_ID,
            scope=capability,
            status="LIVE_CERTIFIED_FOR_CAPABILITY",
            evidence_pointers=("certification:" + capability,),
            certified_at=NOW,
        )
        assert cert.scope == capability


def test_reasoning_only_target_can_perform_repo_static_reasoning():
    contract = _contract(
        task_caps=("REPO_READ", "REPO_SEARCH", "STATIC_ANALYSIS"),
        acceptance=("role-objective-done",),
        reasoning_provider="provider-a",
    )
    result = _eligibility(contract, contract.required_capabilities)
    assert result["decision"] == "ELIGIBLE"
    assert result["fail_closed"] is False
    assert contract.execution_claims == ()
    assert "TEST_EXECUTE" not in contract.required_capabilities


def test_reasoning_only_target_cannot_claim_test_pass_without_test_execute():
    contract = _contract(acceptance=("TEST_PASS",))
    result = _eligibility(contract, ("REPO_READ", "STATIC_ANALYSIS"))
    assert "TEST_EXECUTE" in contract.required_capabilities
    assert result["decision"] == "INELIGIBLE"
    assert result["fail_closed"] is True

    verified = _verify(
        contract,
        scopes=("REPO_READ", "STATIC_ANALYSIS"),
        evidence=("mechanical:TEST_EXECUTE:test-1",),
    )
    assert verified["verdict"] == "REJECTED"
    assert verified["execution_claim_status"] == "NOT_PROVEN"
    assert verified["execution_claims"]["TEST_PASS"]["status"] == "NOT_PROVEN"


def test_execution_claim_without_mechanical_evidence_is_not_proven():
    contract = _contract(acceptance=("TEST_PASS",))
    verified = _verify(
        contract,
        scopes=("TEST_EXECUTE",),
        evidence=("reasoning:static-analysis:looks-green",),
    )
    assert verified["verdict"] == "REJECTED"
    assert verified["execution_claim_status"] == "NOT_PROVEN"
    claim = verified["execution_claims"]["TEST_PASS"]
    assert claim["mechanical_evidence"] is False
    assert claim["status"] == "NOT_PROVEN"


def test_reasoning_provider_a_and_execution_target_b_are_independent_bindings():
    contract = _contract(
        acceptance=("TEST_PASS",),
        reasoning_provider="provider-a",
    )
    verified = _verify(
        contract,
        scopes=("TEST_EXECUTE",),
        evidence=("mechanical:TEST_EXECUTE:test-2",),
    )
    assert verified["verdict"] == "VERIFIED"
    assert verified["execution_claims"]["TEST_PASS"]["status"] == "VERIFIED"
    assert contract.reasoning_provider_id == "provider-a"
    assert contract.reasoning_provider == "provider-a"
    assert ADAPTER_ID != contract.reasoning_provider_id


def test_capability_mismatch_fails_closed():
    contract = _contract(task_caps=("BUILD_EXECUTE",))
    result = _eligibility(contract, ("TEST_EXECUTE",))
    assert result["decision"] == "INELIGIBLE"
    assert any("BUILD_EXECUTE" in reason for reason in result["reasons"])

    verified = _verify(
        contract,
        scopes=("TEST_EXECUTE",),
    )
    assert verified["verdict"] == "REJECTED"
    assert "UNSUPPORTED_OR_UNCERTIFIED_CAPABILITY:BUILD_EXECUTE" in verified[
        "reasons"]


def test_code_generate_does_not_grant_code_patch():
    contract = _contract(task_caps=("CODE_PATCH",))
    result = _eligibility(contract, ("CODE_GENERATE",))
    assert result["decision"] == "INELIGIBLE"
    assert result["capability_results"]["CODE_PATCH"] != \
        "LIVE_CERTIFIED_FOR_CAPABILITY"


def test_test_execute_does_not_grant_remote_push():
    contract = _contract(acceptance=("REMOTE_PUSHED",))
    result = _eligibility(contract, ("TEST_EXECUTE",))
    assert result["decision"] == "INELIGIBLE"
    assert "REMOTE_PUSH" in contract.required_capabilities

    git_only = _eligibility(contract, ("GIT_WRITE",))
    assert git_only["decision"] == "INELIGIBLE"

    verified = _verify(
        contract,
        scopes=("TEST_EXECUTE",),
        evidence=(
            "mechanical:REMOTE_PUSH:push-1",
            "remote-observation:origin/main:push-1",
        ),
    )
    assert verified["verdict"] == "REJECTED"
    assert verified["execution_claims"]["REMOTE_PUSHED"]["status"] == \
        "NOT_PROVEN"


def test_repo_read_does_not_grant_filesystem_write():
    contract = _contract(task_caps=("FILESYSTEM_WRITE",))
    result = _eligibility(contract, ("REPO_READ",))
    assert result["decision"] == "INELIGIBLE"
    assert "FILESYSTEM_WRITE" in contract.required_capabilities


def test_remote_push_requires_remote_observation_in_addition_to_push_evidence():
    contract = _contract(acceptance=("REMOTE_PUSHED",))
    verified = _verify(
        contract,
        scopes=("REMOTE_PUSH",),
        evidence=("mechanical:REMOTE_PUSH:push-3",),
    )
    assert verified["verdict"] == "REJECTED"
    claim = verified["execution_claims"]["REMOTE_PUSHED"]
    assert claim["mechanical_evidence"] is True
    assert claim["remote_observation"] is False
    assert claim["status"] == "NOT_PROVEN"


def test_execution_receipt_binds_actual_observed_execution_target():
    contract = _contract(acceptance=("TEST_PASS",))
    verified = _verify(
        contract,
        scopes=("TEST_EXECUTE",),
        evidence=("mechanical:TEST_EXECUTE:test-3",),
        result_adapter="adapter-fake-manus",
    )
    assert verified["verdict"] == "REJECTED"
    assert "BACKEND_RESULT_TARGET_MISMATCH" in verified["reasons"]


@pytest.mark.parametrize(
    ("claim", "capability", "evidence"),
    (
        ("TEST_PASS", "TEST_EXECUTE", "mechanical:TEST_EXECUTE:test-4"),
        ("BUILD_PASS", "BUILD_EXECUTE", "mechanical:BUILD_EXECUTE:build-1"),
        ("BROWSER_PASS", "BROWSER_EXECUTE", "mechanical:BROWSER_EXECUTE:browser-1"),
        ("DATABASE_PASS", "DATABASE_SANDBOX", "mechanical:DATABASE_SANDBOX:db-1"),
        ("REMOTE_PUSHED", "REMOTE_PUSH", "mechanical:REMOTE_PUSH:push-2"),
    ),
)
def test_execution_claim_requires_mechanical_evidence(claim, capability, evidence):
    contract = _contract(acceptance=(claim,))
    evidence_pointers = (evidence,)
    if claim == "REMOTE_PUSHED":
        evidence_pointers += ("remote-observation:origin/main:push-2",)
    verified = _verify(
        contract,
        scopes=(capability,),
        evidence=evidence_pointers,
    )
    assert verified["verdict"] == "VERIFIED"
    assert verified["execution_claims"][claim]["status"] == "VERIFIED"


def test_c35_provider_neutral_and_owner_gate_invariants_remain_intact():
    assert CANONICAL_ROLE_DENOMINATOR == 8
    assert len(CANONICAL_ROLES) == 8
    assert STATIC_REASONING_EXECUTION_EVIDENCE_INVARIANT == (
        "STATIC_REASONING != EXECUTION_EVIDENCE")
    assert set(EXECUTION_CLAIM_REQUIREMENTS) == {
        "TEST_PASS", "BUILD_PASS", "BROWSER_PASS", "DATABASE_PASS",
        "REMOTE_PUSHED",
    }
    # The patch uses existing role/provider-neutral contract fields; it does
    # not introduce a provider-specific capability identity.
    contract = _contract(
        task_caps=("REPO_READ",),
        reasoning_provider="provider-a",
    )
    assert contract.explicit_execution_target == TARGET_ID
    assert contract.reasoning_provider_id != contract.explicit_execution_target
