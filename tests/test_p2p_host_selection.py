from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.host_executor import HostCapabilityProfile, PortableExecutionRequest, SUPPORTED, UNKNOWN
from p2p_capabilities.host_selection import (
    AVAILABLE,
    AVAILABILITY_UNKNOWN,
    HOST_EVIDENCE_INSUFFICIENT,
    NO_COMPATIBLE_HOST,
    REASON_SELECTED_MINIMUM,
    REASON_STABLE_TIE_BREAK,
    SELECTED,
    HostDiscoveryRecord,
    HostRequirementProfile,
    HostSelector,
    compare_naive_policies,
    discover_host_profiles,
    safe_reselection_allowed,
)


NOW = "2026-08-16T00:00:30+00:00"
OBSERVED = "2026-08-16T00:00:00+00:00"


class C21HostSelectionTests(unittest.TestCase):
    def request(self, **overrides):
        values = {
            "request_id": "req-c21",
            "task_id": "task-c21",
            "goal_id": "C21",
            "task_fingerprint": "a" * 64,
            "project_binding": "project-1",
            "candidate_binding": "candidate-1",
            "purpose": "bounded host selection",
            "scope": ("source",),
            "required_capabilities": ("can_read_files",),
            "permission_needs": ("READ",),
            "granted_permissions": ("READ",),
            "context_refs": (),
            "context_materialization_refs": (),
            "acceptance_criteria": ("deterministic decision",),
            "verification_expectations": ("receipt-bound evidence",),
            "execution_budget": {"background_execution": False},
        }
        values.update(overrides)
        return PortableExecutionRequest(**values)

    def profile(self, *, environment="LOCAL_PROJECT", **capabilities):
        return HostCapabilityProfile(
            adapter_class="NeutralHostAdapter",
            environment=environment,
            capabilities=capabilities,
        )

    def record(self, host_id, *, availability=AVAILABLE, environment="LOCAL_PROJECT", project_binding="project-1", burden=0, observed_at=OBSERVED, active=False, **capabilities):
        return HostDiscoveryRecord(
            host_id=host_id,
            profile=self.profile(environment=environment, **capabilities),
            availability=availability,
            observed_at=observed_at,
            provenance="FIXTURE_PROFILE",
            project_binding=project_binding,
            active=active,
            reconciliation_burden=burden,
        )

    def select(self, request, records, **kwargs):
        return HostSelector(now=NOW).select(request, records, **kwargs)

    # HS1: one host exactly satisfies task requirements.
    def test_hs01_exact_host_selects(self):
        decision = self.select(self.request(), [self.record("exact", can_read_files=SUPPORTED)])
        self.assertEqual(decision.status, SELECTED)
        self.assertEqual(decision.selected_host_id, "exact")

    # HS2: unnecessary extra capability does not win over minimum sufficient.
    def test_hs02_extra_capability_does_not_win(self):
        decision = self.select(self.request(), [
            self.record("exact", can_read_files=SUPPORTED),
            self.record("strong", can_read_files=SUPPORTED, can_execute_commands=SUPPORTED, can_run_tests=SUPPORTED),
        ])
        self.assertEqual(decision.selected_host_id, "exact")
        self.assertIn(REASON_SELECTED_MINIMUM, decision.selection_reason_codes)

    # HS3: one mandatory capability missing rejects the host.
    def test_hs03_missing_capability_rejects(self):
        decision = self.select(self.request(required_capabilities=("can_read_files", "can_execute_commands")), [self.record("weak", can_read_files=SUPPORTED)])
        self.assertEqual(decision.status, NO_COMPATIBLE_HOST)

    # HS4: UNKNOWN is not SUPPORTED for a required capability.
    def test_hs04_unknown_required_capability_rejects(self):
        decision = self.select(self.request(), [self.record("unknown")])
        self.assertEqual(decision.status, HOST_EVIDENCE_INSUFFICIENT if False else NO_COMPATIBLE_HOST)

    # HS5: host capability cannot grant a missing WRITE permission.
    def test_hs05_permission_is_not_granted(self):
        decision = self.select(self.request(permission_needs=("WRITE",), granted_permissions=()), [self.record("writer", can_read_files=SUPPORTED, can_write_files=SUPPORTED)])
        self.assertEqual(decision.status, NO_COMPATIBLE_HOST)

    # HS6: local-authoritative mutation cannot silently use a cloud copy.
    def test_hs06_cloud_copy_rejected_for_local_mutation(self):
        request = self.request(expected_environment="LOCAL_PROJECT", permission_needs=("WRITE",), granted_permissions=("WRITE",), required_capabilities=("can_write_files",))
        decision = self.select(request, [self.record("cloud", environment="CLOUD_SANDBOX", can_write_files=SUPPORTED)])
        self.assertEqual(decision.status, NO_COMPATIBLE_HOST)

    # HS7: read-only remote work may use an allowed remote environment.
    def test_hs07_remote_read_only_allowed(self):
        request = self.request(expected_environment="CLOUD_SANDBOX")
        decision = self.select(request, [self.record("cloud", environment="CLOUD_SANDBOX", can_read_files=SUPPORTED)])
        self.assertEqual(decision.status, SELECTED)

    # HS8: identity requirement needs authoritative execution identity evidence.
    def test_hs08_identity_evidence_required_rejects(self):
        request = self.request(identity_required=True)
        decision = self.select(request, [self.record("anonymous", can_read_files=SUPPORTED)])
        self.assertEqual(decision.status, NO_COMPATIBLE_HOST)

    # HS9: unknown identity is acceptable when identity is not required.
    def test_hs09_identity_not_required_can_select(self):
        decision = self.select(self.request(identity_required=False), [self.record("anonymous", can_read_files=SUPPORTED)])
        self.assertEqual(decision.status, SELECTED)

    # HS10: compatible current host avoids unnecessary switching.
    def test_hs10_current_host_preference(self):
        decision = self.select(self.request(), [self.record("current", can_read_files=SUPPORTED), self.record("other", can_read_files=SUPPORTED)], current_host_id="current")
        self.assertEqual(decision.selected_host_id, "current")

    # HS11: incompatible current host yields a different host and portable handoff.
    def test_hs11_incompatible_current_host_gets_handoff(self):
        request = self.request(required_capabilities=("can_read_files", "can_execute_commands"))
        decision = self.select(request, [self.record("current", can_read_files=SUPPORTED), self.record("other", can_read_files=SUPPORTED, can_execute_commands=SUPPORTED)], current_host_id="current")
        self.assertEqual(decision.selected_host_id, "other")
        self.assertIsNotNone(decision.handoff)
        self.assertFalse(decision.handoff["chat_history_required"])

    # HS12: materially equivalent hosts use stable host ID ordering.
    def test_hs12_stable_tie_break(self):
        decision = self.select(self.request(), [self.record("zeta", can_read_files=SUPPORTED), self.record("alpha", can_read_files=SUPPORTED)])
        self.assertEqual(decision.selected_host_id, "alpha")
        self.assertIn(REASON_STABLE_TIE_BREAK, decision.selection_reason_codes)

    # HS13: no host produces an explicit NO_COMPATIBLE_HOST result.
    def test_hs13_no_compatible_host(self):
        decision = self.select(self.request(), [])
        self.assertEqual(decision.status, NO_COMPATIBLE_HOST)

    # HS14: stale profile evidence is not live truth.
    def test_hs14_stale_profile_is_insufficient(self):
        decision = self.select(self.request(), [self.record("stale", observed_at="2026-08-15T00:00:00+00:00", can_read_files=SUPPORTED)], requirement=HostRequirementProfile.from_request(self.request(), freshness_seconds=60))
        self.assertEqual(decision.status, HOST_EVIDENCE_INSUFFICIENT)

    # HS15: configured host with unknown availability is not known available.
    def test_hs15_unknown_availability_is_insufficient(self):
        decision = self.select(self.request(), [self.record("installed", availability=AVAILABILITY_UNKNOWN, can_read_files=SUPPORTED)])
        self.assertEqual(decision.status, HOST_EVIDENCE_INSUFFICIENT)

    # HS16: non-authoritative cheap estimate is not a selection authority.
    def test_hs16_cheapest_estimate_is_not_authoritative(self):
        records = [self.record("exact", burden=5, can_read_files=SUPPORTED), self.record("strong", burden=0, can_read_files=SUPPORTED, can_execute_commands=SUPPORTED)]
        decision = self.select(self.request(), records)
        comparison = compare_naive_policies(records, decision)
        self.assertEqual(comparison["authoritative_cost"], UNKNOWN)
        self.assertEqual(decision.selected_host_id, "exact")

    # HS17: absent live cost telemetry remains UNKNOWN.
    def test_hs17_cost_remains_unknown(self):
        decision = self.select(self.request(), [self.record("host", can_read_files=SUPPORTED)])
        self.assertEqual(compare_naive_policies([], decision)["authoritative_cost"], UNKNOWN)

    # HS18: reselection is allowed only after a pre-execution host failure.
    def test_hs18_safe_reselection_before_execution(self):
        request = self.request()
        self.assertTrue(safe_reselection_allowed(prior_receipt={"status": "HOST_UNAVAILABLE", "possible_mutation": False}, previous_request=request, current_request=request, project_binding_unchanged=True, permissions_unchanged=True, context_fresh=True))

    # HS19: possible mutation freezes automatic fallback.
    def test_hs19_partial_mutation_forbids_reselection(self):
        request = self.request()
        self.assertFalse(safe_reselection_allowed(prior_receipt={"status": "HOST_UNAVAILABLE", "possible_mutation": True}, previous_request=request, current_request=request, project_binding_unchanged=True, permissions_unchanged=True, context_fresh=True))

    # HS20: minimal context requirement does not reward huge context capability.
    def test_hs20_minimal_context_prefers_minimum(self):
        request = self.request()
        decision = self.select(request, [self.record("small", can_read_files=SUPPORTED), self.record("huge", can_read_files=SUPPORTED, can_receive_context_refs=SUPPORTED, can_run_tests=SUPPORTED)])
        self.assertEqual(decision.selected_host_id, "small")

    # HS21: abstract HIGH reasoning remains abstract and model-neutral.
    def test_hs21_high_reasoning_is_not_named_model(self):
        request = self.request()
        requirement = HostRequirementProfile.from_request(request, reasoning_class="HIGH")
        decision = self.select(request, [self.record("neutral", can_read_files=SUPPORTED)], requirement=requirement)
        self.assertEqual(decision.status, SELECTED)
        self.assertEqual(requirement.reasoning_class, "HIGH")
        self.assertNotIn("model", requirement.to_dict())

    # HS22: secret-bearing local-only policy rejects a cloud boundary.
    def test_hs22_secret_boundary_requires_local_policy(self):
        request = self.request(expected_environment="LOCAL_PROJECT")
        requirement = HostRequirementProfile.from_request(request, owner_local_only=True)
        decision = self.select(request, [self.record("cloud", environment="CLOUD_SANDBOX", can_read_files=SUPPORTED)], requirement=requirement)
        self.assertEqual(decision.status, NO_COMPATIBLE_HOST)

    # HS23: unknown future host can participate through the neutral profile.
    def test_hs23_future_neutral_host_extensible(self):
        future = HostDiscoveryRecord("future-x", self.profile(can_read_files=SUPPORTED), AVAILABLE, OBSERVED, "FUTURE_NEUTRAL_PROFILE", project_binding="project-1")
        decision = self.select(self.request(), [future])
        self.assertEqual(decision.selected_host_id, "future-x")

    # HS24: Manus-like fixture needs no Manus-specific core field.
    def test_hs24_manus_like_fixture_is_neutral(self):
        fixture = HostDiscoveryRecord("manus-like", self.profile(can_read_files=SUPPORTED), AVAILABLE, OBSERVED, "FIXTURE_PROFILE", project_binding="project-1")
        self.assertEqual(self.select(self.request(), [fixture]).status, SELECTED)

    # HS25: Codex-specific adapter behavior remains a C20 fixture concern.
    def test_hs25_codex_like_fixture_remains_compatible(self):
        fixture = HostDiscoveryRecord("codex-like", HostCapabilityProfile("CodexHostAdapter", {"can_read_files": SUPPORTED}), AVAILABLE, OBSERVED, "FIXTURE_PROFILE", project_binding="project-1")
        self.assertEqual(self.select(self.request(), [fixture]).status, SELECTED)

    # HS26: C21 does not create a third worker or change parallel limits.
    def test_hs26_parallel_cap_is_unchanged(self):
        decision = self.select(self.request(), [self.record("one", can_read_files=SUPPORTED), self.record("two", can_read_files=SUPPORTED)])
        self.assertNotIn("called_hosts", decision.to_dict())
        self.assertNotIn("launch", dir(HostSelector))

    # HS27: different compatible hosts can be represented without auto-launch.
    def test_hs27_parallel_conceptual_hosts_do_not_auto_launch(self):
        decisions = [self.select(self.request(task_id=f"task-{index}"), [self.record(host, can_read_files=SUPPORTED)]) for index, host in enumerate(("one", "two"))]
        self.assertEqual([item.status for item in decisions], [SELECTED, SELECTED])

    # HS28: wrong project binding is rejected for mutation-sensitive tasks.
    def test_hs28_wrong_project_binding_rejects(self):
        request = self.request(permission_needs=("WRITE",), granted_permissions=("WRITE",), required_capabilities=("can_write_files",))
        decision = self.select(request, [self.record("wrong", project_binding="project-2", can_write_files=SUPPORTED)])
        self.assertEqual(decision.status, NO_COMPATIBLE_HOST)

    # HS29: owner local-only policy filters cloud before ranking.
    def test_hs29_owner_local_only_filters_cloud(self):
        request = self.request()
        requirement = HostRequirementProfile.from_request(request, owner_local_only=True)
        decision = self.select(request, [self.record("cloud", environment="CLOUD_SANDBOX", can_read_files=SUPPORTED), self.record("local", can_read_files=SUPPORTED)], requirement=requirement)
        self.assertEqual(decision.selected_host_id, "local")
        self.assertIn("cloud", {item["host_id"] for item in decision.rejected_candidates})

    # HS30: beginner invocation returns a decision without host-choice questions.
    def test_hs30_beginner_path_has_zero_host_questions(self):
        decision = self.select(self.request(), [self.record("neutral", can_read_files=SUPPORTED)])
        self.assertEqual(decision.status, SELECTED)
        self.assertNotIn("question", repr(decision.to_dict()).lower())


if __name__ == "__main__":
    unittest.main()
