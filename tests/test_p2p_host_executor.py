from __future__ import annotations

import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.bounded_delegation import PermissionEnvelope  # noqa: E402
from p2p_capabilities.foreground_execution import ExecutionBudget, ExecutionIntent  # noqa: E402
from p2p_capabilities.host_executor import (  # noqa: E402
    CAPABILITY_DIMENSIONS,
    HostCapabilityProfile,
    PortableExecutionReceipt,
    PortableExecutionRequest,
    SUPPORTED,
    UNKNOWN,
    build_portable_handoff,
    beginner_handoff_instruction,
    evaluate_host_preflight,
    governance_projection,
    import_artifact,
    normalize_host_error,
    reconcile_receipt,
    select_compatible_executor,
    validate_binding,
)


TASK_FINGERPRINT = "a" * 64


class P2PHostExecutorFoundationTests(unittest.TestCase):
    def profile(self, *, adapter_class="GenericHostAdapter", environment="LOCAL_PROJECT", host_label=None, provider=None, model=None, **capabilities):
        return HostCapabilityProfile(
            adapter_class=adapter_class,
            environment=environment,
            host_label=host_label,
            provider=provider,
            model=model,
            capabilities=capabilities,
        )

    def request(self, **overrides):
        values = {
            "request_id": "req-001",
            "task_id": "task-001",
            "goal_id": "C20",
            "task_fingerprint": TASK_FINGERPRINT,
            "project_binding": "project-sha-001",
            "candidate_binding": "candidate-sha-001",
            "purpose": "bounded verification",
            "scope": ("tests",),
            "required_capabilities": ("can_read_files",),
            "permission_needs": ("READ",),
            "granted_permissions": ("READ",),
            "context_refs": ("ctx-pointer-1",),
            "context_materialization_refs": ("ctx-materialization-1",),
            "acceptance_criteria": ("independent verification",),
            "verification_expectations": ("receipt-bound evidence",),
            "execution_budget": {"max_actions": 4, "background_execution": False},
        }
        values.update(overrides)
        return PortableExecutionRequest(**values)

    def test_hn01_core_state_has_no_codex_only_identity(self):
        request = self.request()
        encoded = request.to_dict()
        self.assertNotIn("codex", repr(encoded).lower())
        self.assertNotIn("host_label", encoded["purpose"])
        self.assertEqual(encoded["schema"], "p2p-portable-execution-request/1")

    def test_hn02_read_execute_without_write_is_ready(self):
        request = self.request(
            required_capabilities=("can_read_files", "can_execute_commands"),
            permission_needs=("READ", "EXECUTE"),
            granted_permissions=("READ", "EXECUTE"),
        )
        profile = self.profile(can_read_files=SUPPORTED, can_execute_commands=SUPPORTED, can_write_files="UNSUPPORTED")
        self.assertEqual(evaluate_host_preflight(profile, request)["status"], "READY")
        self.assertFalse(request.mutation_requested)

    def test_hn03_write_capability_without_write_permission_blocks(self):
        request = self.request(permission_needs=("WRITE",), granted_permissions=())
        profile = self.profile(can_read_files=SUPPORTED, can_write_files=SUPPORTED)
        result = evaluate_host_preflight(profile, request)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "PERMISSION_BLOCKED")

    def test_hn04_missing_authoritative_execution_id_can_be_verified_when_not_required(self):
        request = self.request(identity_required=False)
        profile = self.profile(can_read_files=SUPPORTED)
        receipt = PortableExecutionReceipt.from_host_result(
            request,
            profile,
            {"status": "SUCCEEDED", "verification_status": "VERIFIED", "evidence_refs": ["evidence-1"]},
        )
        self.assertIsNone(receipt.authoritative_execution_id)
        self.assertEqual(receipt.completion_status, "DONE")

    def test_hn05_identity_required_without_evidence_blocks(self):
        request = self.request(identity_required=True)
        profile = self.profile(can_read_files=SUPPORTED, can_return_authoritative_execution_id=UNKNOWN)
        result = evaluate_host_preflight(profile, request)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "IDENTITY_EVIDENCE_UNAVAILABLE")

    def test_hn06_done_text_without_acceptance_verification_is_not_done(self):
        request = self.request()
        receipt = PortableExecutionReceipt.from_host_result(
            request,
            self.profile(can_read_files=SUPPORTED),
            {"status": "DONE", "verification_status": "FAILED"},
        )
        self.assertEqual(receipt.execution_status, "SUCCEEDED")
        self.assertEqual(receipt.completion_status, "NOT_DONE")

    def test_hn07_host_unavailable_before_mutation_is_recoverable(self):
        request = self.request()
        receipt = PortableExecutionReceipt.from_host_result(
            request,
            self.profile(can_read_files=SUPPORTED),
            {"status": "UNKNOWN", "error": "host unavailable", "possible_mutation": False},
        )
        result = reconcile_receipt(receipt, current_project_binding=request.project_binding, current_candidate_binding=request.candidate_binding)
        self.assertEqual(result["status"], "RECOVERABLE_HOST_FAILURE")
        self.assertTrue(result["retry_allowed"])

    def test_hn08_possible_mutation_unknown_requires_recheck_without_retry(self):
        request = self.request()
        receipt = PortableExecutionReceipt.from_host_result(
            request,
            self.profile(can_read_files=SUPPORTED),
            {"status": "UNKNOWN", "error": "result unknown", "possible_mutation": True},
        )
        self.assertEqual(receipt.completion_status, "NEEDS_RECHECK")
        result = reconcile_receipt(receipt, current_project_binding=request.project_binding, current_candidate_binding=request.candidate_binding)
        self.assertEqual(result["status"], "NEEDS_RECHECK")
        self.assertFalse(result["retry_allowed"])

    def test_hn09_cross_host_continuation_uses_checkpoint_without_chat(self):
        handoff = build_portable_handoff(
            self.request(),
            checkpoint_ref=".p2p/state/checkpoint-1.json",
            next_step="verify checkpoint then continue unfinished safe work",
            verification_required=("project fingerprint", "candidate binding"),
            unfinished_safe_work=("run bounded verification",),
        )
        encoded = handoff.to_dict()
        self.assertFalse(encoded["chat_history_required"])
        self.assertEqual(encoded["request_fingerprint"], handoff.request.fingerprint)

    def test_hn10_changed_project_fingerprint_rejects_stale_request(self):
        result = validate_binding(request=self.request(), current_project_binding="changed", current_candidate_binding="candidate-sha-001")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "STALE_REQUEST")

    def test_hn11_network_capability_does_not_grant_network_permission(self):
        request = self.request(permission_needs=(), granted_permissions=())
        profile = self.profile(can_read_files=SUPPORTED, can_use_network=SUPPORTED)
        self.assertEqual(evaluate_host_preflight(profile, request)["status"], "READY")
        self.assertNotIn("NETWORK", request.granted_permissions)

    def test_hn12_cloud_copy_cannot_satisfy_local_authority_silently(self):
        request = self.request(expected_environment="LOCAL_PROJECT")
        profile = self.profile(environment="CLOUD_SANDBOX", can_read_files=SUPPORTED)
        result = evaluate_host_preflight(profile, request)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "RECONCILIATION_REQUIRED")

    def test_hn13_codex_adapter_remains_compatible_as_thin_adapter(self):
        request = self.request()
        profile = self.profile(adapter_class="CodexHostAdapter", can_read_files=SUPPORTED)
        self.assertEqual(evaluate_host_preflight(profile, request)["status"], "READY")
        self.assertEqual(profile.adapter_class, "CodexHostAdapter")

    def test_hn14_manus_like_host_needs_no_manus_specific_fields(self):
        profile = self.profile(adapter_class="ExternalHostAdapter", host_label=None, can_read_files=SUPPORTED)
        encoded = profile.to_dict()
        self.assertEqual(encoded["adapter_class"], "ExternalHostAdapter")
        self.assertNotIn("manus_task_id", encoded)
        self.assertEqual(encoded["provider_status"], "UNKNOWN")

    def test_hn15_unknown_future_host_capability_is_explicit(self):
        profile = self.profile(adapter_class="FutureHostAdapter")
        self.assertEqual(profile.state("can_resume"), UNKNOWN)
        self.assertEqual(profile.state("unlisted_capability"), UNKNOWN)

    def test_hn16_unknown_provider_model_are_not_fabricated(self):
        profile = self.profile(can_read_files=SUPPORTED)
        encoded = profile.to_dict()
        self.assertIsNone(encoded["provider"])
        self.assertIsNone(encoded["model"])
        self.assertEqual(encoded["provider_status"], UNKNOWN)
        self.assertEqual(encoded["model_status"], UNKNOWN)

    def test_hn17_missing_authoritative_telemetry_is_unknown(self):
        receipt = PortableExecutionReceipt.from_host_result(self.request(), self.profile(can_read_files=SUPPORTED), {"status": "SUCCEEDED"})
        self.assertEqual(receipt.telemetry_status, UNKNOWN)
        self.assertEqual(receipt.to_dict()["telemetry_status"], UNKNOWN)

    def test_hn18_host_cannot_self_authorize_permission_expansion(self):
        request = self.request(permission_needs=("WRITE",), granted_permissions=("WRITE",))
        profile = self.profile(can_read_files=SUPPORTED, can_write_files=SUPPORTED)
        parent = PermissionEnvelope(grants=("READ",), scope=("tests",))
        result = evaluate_host_preflight(profile, request, parent_permission_grants=parent)
        self.assertEqual(result["reason"], "PERMISSION_BLOCKED")
        self.assertEqual(result["permission_source"], "PARENT_ENVELOPE")

    def test_portability_comparison_neutral_request_works_for_codex_and_generic_profiles(self):
        request = self.request()
        codex = self.profile(adapter_class="CodexHostAdapter", can_read_files=SUPPORTED)
        generic = self.profile(adapter_class="GenericHostAdapter", can_read_files=SUPPORTED)
        self.assertEqual(evaluate_host_preflight(codex, request)["status"], "READY")
        self.assertEqual(evaluate_host_preflight(generic, request)["status"], "READY")
        self.assertNotIn("if host", repr(request.to_dict()).lower())

    def test_c20_request_factory_reuses_c12_execution_intent(self):
        intent = ExecutionIntent(
            execution_id="fg-c20-intent",
            task_id="task-001",
            goal_id="C20",
            plan_hash=TASK_FINGERPRINT,
            plan_revision=1,
            project_binding="project-sha-001",
            action_name="bounded verification",
            scope=("tests",),
            non_scope=("production",),
            required_capabilities=("can_read_files",),
            permission_needs=("READ",),
            context_refs=("ctx-pointer-1",),
            acceptance_requirements=("independent verification",),
            required_evidence=("receipt-bound evidence",),
            budget=ExecutionBudget(),
        )
        request = PortableExecutionRequest.from_foreground_intent(
            intent,
            request_id="req-from-c12",
            candidate_binding="candidate-sha-001",
        )
        self.assertEqual(request.task_id, intent.task_id)
        self.assertEqual(request.project_binding, intent.project_binding)
        self.assertEqual(request.context_refs, intent.context_refs)

    def test_hn19_two_hosts_do_not_trigger_both(self):
        request = self.request()
        profiles = [self.profile(adapter_class="HostA", can_read_files=SUPPORTED), self.profile(adapter_class="HostB", can_read_files=SUPPORTED)]
        result = select_compatible_executor(profiles, request)
        self.assertEqual(result["status"], "MULTIPLE_HOSTS_AVAILABLE")
        self.assertEqual(result["called_hosts"], 0)

    def test_hn20_beginner_instruction_hides_host_choices(self):
        instruction = beginner_handoff_instruction()
        self.assertNotIn("Codex", instruction)
        self.assertNotIn("Manus", instruction)
        self.assertNotIn("Claude", instruction)

    def test_hn21_mismatched_artifact_binding_fails_closed(self):
        result = import_artifact(PortableExecutionReceipt.from_host_result(self.request(), self.profile(can_read_files=SUPPORTED), {"status": "SUCCEEDED"}), current_candidate_binding="candidate-a", artifact_candidate_binding="candidate-b")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(result["reconciliation_required"])

    def test_hn22_c19_context_refs_are_bounded_materialization_refs(self):
        request = self.request(context_refs=("c19-pointer-1",), context_materialization_refs=("c19-materialized-1",))
        encoded = request.to_dict()
        self.assertEqual(encoded["context_refs"], ["c19-pointer-1"])
        self.assertEqual(encoded["context_materialization_refs"], ["c19-materialized-1"])
        self.assertNotIn("chat_history", encoded)

    def test_hn23_host_error_is_normalized_to_bounded_semantic_class(self):
        self.assertEqual(normalize_host_error("control plane timeout"), "CONTROL_PLANE_FAILURE")
        self.assertEqual(normalize_host_error("partial mutation unknown"), "PARTIAL_MUTATION_UNKNOWN")
        self.assertEqual(normalize_host_error("permission denied"), "PERMISSION_BLOCKED")

    def test_hn24_host_count_does_not_change_canonical_governance(self):
        projection = governance_projection(tuple(f"agent-{index}" for index in range(8)))
        self.assertEqual(projection["canonical_count"], 8)
        self.assertEqual(projection["denominator"], 8)
        self.assertEqual(projection["full_quorum"], "8/8")
        self.assertTrue(projection["host_is_not_agent"])


if __name__ == "__main__":
    unittest.main()
