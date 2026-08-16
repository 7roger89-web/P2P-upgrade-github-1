from __future__ import annotations

import hashlib
import json
import shutil
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.context import (  # noqa: E402
    BASELINE_COMPAT,
    CONTEXT_EFFICIENT_V1,
    context_fingerprint,
    build_context_view,
)
from p2p_capabilities.live_execution import (  # noqa: E402
    CUSTOM_PROFILE_EXECUTOR_CLASS,
    HOST_EXECUTION_SOURCE,
    HOST_DEFAULT_EXECUTOR_CLASS,
    LiveBindingError,
    LiveHostEvidenceError,
    LiveIsolationError,
    LOCAL_PROXY_SOURCE,
    default_execution_request,
    finalize_trial,
    prepare_trial,
)


class LiveExecutionBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = REPO_ROOT / ".tmp"
        self.tmp_root.mkdir(parents=True, exist_ok=True)
        self.project = self.tmp_root / f"p2p-live-test-{uuid.uuid4().hex}"
        self.project.mkdir()
        (self.project / ".p2p" / "state").mkdir(parents=True)
        (self.project / ".codex").mkdir(parents=True)
        (self.project / ".codex" / "config.toml").write_text("[agents]\nenabled = true\n", encoding="utf-8")
        self.ledger = self.project / ".p2p" / "state" / "execution-ledger.jsonl"
        self.ledger.write_text("", encoding="utf-8")
        self.artifact = self.project / ".tmp" / "candidate.bin"
        self.artifact.parent.mkdir(parents=True)
        self.artifact.write_bytes(b"immutable-candidate-v17")
        self.artifact_binding = {
            "package_version": "8.4.7-C-codex.17",
            "artifact_path": str(self.artifact),
            "artifact_sha256": hashlib.sha256(self.artifact.read_bytes()).hexdigest(),
        }

    def tearDown(self) -> None:
        if self.project.is_dir() and self.project.is_relative_to(self.tmp_root):
            shutil.rmtree(self.project)

    def _context(self, scenario_id: str = "C1") -> tuple[dict[str, object], dict[str, dict[str, object]]]:
        goal_content = {"scenario": scenario_id, "goal": "execute a bounded read-only trial"}
        history_content = {"scenario": scenario_id, "detail": "historical detail " * 12}
        goal_hash = context_fingerprint(goal_content)
        history_hash = context_fingerprint(history_content)
        context: dict[str, object] = {
            "goal_id": f"goal-{scenario_id}",
            "task_or_goal": f"{scenario_id}: execute the bounded task",
            "scope": ["current-task"],
            "non_scope": ["provider-experiment", "unrelated-history"],
            "acceptance": [{"item_id": "acceptance-main", "value": "observe the supplied context", "required": True}],
            "relevant_facts": [{"item_id": "fact-direct", "value": "direct fact", "required": True}],
            "relevant_decisions": [{"item_id": "decision-invariant", "value": "preserve invariants", "required": True}],
            "direct_dependencies": [{"item_id": "dependency-contract", "value": "direct dependency", "required": True}],
            "history": [{"item_id": "history-unrelated", "value": history_content["detail"], "defer": True, "pointer_id": "pointer-history", "source_binding": "history"}],
            "evidence_pointers": [{
                "pointer_id": "pointer-history",
                "label": "authoritative history",
                "authority": "FACT_LEDGER",
                "scope": ["current-task"],
                "freshness": "CURRENT",
                "provenance": "fixture-source",
                "content_class": "EVIDENCE",
                "source_binding": "history",
            }],
            "capability_constraints": ["same-tools", "same-capability-scope"],
            "permission_constraints": ["READ != WRITE", "owner approval remains explicit"],
            "source_bindings": [
                {"source_id": "goal", "path": f"fixtures/{scenario_id}/goal.json", "source_hash": goal_hash, "required": True},
                {"source_id": "history", "path": f"fixtures/{scenario_id}/history.json", "source_hash": history_hash},
            ],
            "access_contract": {"tools": ["read"], "source_catalog": "fixture-authoritative-sources"},
        }
        if scenario_id == "C7":
            context["acceptance"] = [
                {"item_id": "acceptance-main", "value": "observe the supplied context", "required": True},
                {"item_id": "accessibility-constraints", "value": "keyboard access, focus order, labels, contrast", "required": True},
            ]
        catalog = {
            "goal": {"source_id": "goal", "path": f"fixtures/{scenario_id}/goal.json", "content": goal_content},
            "history": {"source_id": "history", "path": f"fixtures/{scenario_id}/history.json", "content": history_content},
        }
        return context, catalog

    def _route(
        self,
        *,
        profile: str,
        logical_route: str,
        logical_capability: str | None = None,
        supporting_capabilities: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "schema": "p2p-route-host-observation/1",
            "logical_route": logical_route,
            "logical_capability": logical_capability,
            "supporting_capabilities": supporting_capabilities or [],
            "requested_profile_if_any": None if profile == "default" else profile,
            "executor_class": HOST_DEFAULT_EXECUTOR_CLASS if profile == "default" else CUSTOM_PROFILE_EXECUTOR_CLASS,
        }

    def _prepare(
        self,
        condition: str,
        scenario_id: str = "C1",
        *,
        profile: str = "p2p_aesthetica",
        route_observation: dict[str, object] | None = None,
    ) -> dict[str, object]:
        context, catalog = self._context(scenario_id)
        mode = BASELINE_COMPAT if condition == "A" else CONTEXT_EFFICIENT_V1
        view = build_context_view(context, mode)
        return prepare_trial(
            trial_id=f"{scenario_id}-{condition}-{uuid.uuid4().hex[:8]}",
            condition=condition,
            scenario_id=scenario_id,
            context_input=context,
            context_view=view,
            source_catalog=catalog,
            fixture={"fixture_id": f"{scenario_id}-fixture", "scenario_id": scenario_id, "condition": condition, "read_only": True, "seed": "fixed"},
            artifact_binding=self.artifact_binding,
            requested_execution=default_execution_request(profile),
            route_observation=route_observation,
            trial_root=self.project / ".tmp" / uuid.uuid4().hex,
            project_root=self.project,
        )

    def _record_host_start(
        self,
        prepared: dict[str, object],
        *,
        timestamp: str | None = None,
        agent_id: str = "agent-live-1",
        agent_type: str = "p2p_aesthetica",
        session_id: str = "session-live-1",
        turn_id: str = "turn-live-1",
        permission_mode: str = "read-only",
    ) -> None:
        receipt = {
            "schema": "p2p-host-subagent-identity/1",
            "event": "SubagentStart",
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "turn_id": turn_id,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "permission_mode": permission_mode,
            "model": "gpt-host-observed",
            "cwd": str(self.project),
            "source": "codex_official_hook",
        }
        event = {"schema_version": "p2p-execution-event/1", "event": "host_subagent_identity_receipt", "receipt": receipt}
        with self.ledger.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    def _host_result(
        self,
        prepared: dict[str, object],
        *,
        agent_id: str = "agent-live-1",
        session_id: str | None = None,
        turn_id: str | None = None,
        **overrides: object,
    ) -> dict[str, object]:
        result: dict[str, object] = {
            "execution_source": HOST_EXECUTION_SOURCE,
            "host_execution_id": agent_id,
            "execution_completed": True,
            "child_count": 0,
            "delegation_depth": 0,
            "output": f"Observed supplied context fingerprint {prepared['context_fingerprint']} with no file changes.",
        }
        if session_id is not None:
            result["session_id"] = session_id
        if turn_id is not None:
            result["turn_id"] = turn_id
        result.update(overrides)
        return result

    def test_ab_preparation_uses_real_mode_and_payload_differences(self) -> None:
        baseline = self._prepare("A", "C1")
        efficient = self._prepare("B", "C1")
        self.assertEqual(baseline["context_mode"], BASELINE_COMPAT)
        self.assertEqual(efficient["context_mode"], CONTEXT_EFFICIENT_V1)
        self.assertNotEqual(baseline["context_fingerprint"], efficient["context_fingerprint"])
        self.assertNotEqual(baseline["request_fingerprint"], efficient["request_fingerprint"])
        self.assertNotEqual(
            json.loads((self.project / baseline["request_pointer"]).read_text(encoding="utf-8"))["context_view"],
            json.loads((self.project / efficient["request_pointer"]).read_text(encoding="utf-8"))["context_view"],
        )

    def test_live_receipt_requires_official_ledger_identity_and_captures_output(self) -> None:
        prepared = self._prepare("B", "C7")
        self._record_host_start(prepared)
        receipt = finalize_trial(prepared, self._host_result(prepared), ledger_path=self.ledger)
        self.assertTrue(receipt["runtime_task_execution"])
        self.assertEqual(receipt["execution_authority"], "HOST")
        self.assertEqual(receipt["host_execution_id"], "agent-live-1")
        self.assertTrue(receipt["output_sha256"])
        self.assertIn("output.txt", receipt["output_pointer"])
        self.assertNotIn("Observed supplied", json.dumps(receipt))
        self.assertEqual(receipt["telemetry"]["provider"]["value"], "UNKNOWN")
        self.assertEqual(receipt["telemetry"]["provider_tokens"]["authority"], "UNKNOWN")
        self.assertTrue(receipt["permission_envelope"]["READ"])
        self.assertFalse(receipt["permission_envelope"]["WRITE"])
        self.assertFalse(receipt["permission_envelope"]["PERSIST"])
        self.assertEqual(receipt["permission_observation"]["status"], "VERIFIED")
        ledger_text = self.ledger.read_text(encoding="utf-8")
        self.assertIn("live_context_trial_receipt", ledger_text)

    def test_route_observation_separates_normal_ui_from_generic_host_executor(self) -> None:
        prepared = self._prepare(
            "A",
            "C6",
            profile="default",
            route_observation=self._route(
                profile="default",
                logical_route="p2p-uiux",
                logical_capability="p2p-uiux",
            ),
        )
        self._record_host_start(
            prepared,
            agent_type="default",
            session_id="session-c6",
            turn_id="turn-c6",
        )
        receipt = finalize_trial(
            prepared,
            self._host_result(prepared, session_id="session-c6", turn_id="turn-c6"),
            ledger_path=self.ledger,
        )
        self.assertEqual(receipt["logical_route"], "p2p-uiux")
        self.assertEqual(receipt["logical_capability"], "p2p-uiux")
        self.assertIsNone(receipt["requested_profile_if_any"])
        self.assertEqual(receipt["observed_host_agent_type"], "default")
        self.assertEqual(receipt["observed_host_executor_class"], HOST_DEFAULT_EXECUTOR_CLASS)
        self.assertEqual(receipt["identity_authority"], "codex_official_hook")
        self.assertEqual(receipt["session_id"], "session-c6")
        self.assertEqual(receipt["turn_id"], "turn-c6")

    def test_accessibility_route_keeps_optional_profile_explicit(self) -> None:
        prepared = self._prepare(
            "B",
            "C7",
            profile="p2p_aesthetica",
            route_observation=self._route(
                profile="p2p_aesthetica",
                logical_route="p2p-uiux",
                logical_capability="p2p-uiux",
                supporting_capabilities=["p2p_aesthetica"],
            ),
        )
        self._record_host_start(prepared, agent_type="p2p_aesthetica")
        receipt = finalize_trial(prepared, self._host_result(prepared), ledger_path=self.ledger)
        self.assertEqual(receipt["logical_route"], "p2p-uiux")
        self.assertEqual(receipt["requested_profile_if_any"], "p2p_aesthetica")
        self.assertEqual(receipt["observed_host_agent_type"], "p2p_aesthetica")
        self.assertEqual(receipt["observed_host_executor_class"], CUSTOM_PROFILE_EXECUTOR_CLASS)

    def test_canonical_profile_is_distinct_from_logical_capability(self) -> None:
        prepared = self._prepare(
            "A",
            "C1",
            profile="p2p_iris",
            route_observation=self._route(
                profile="p2p_iris",
                logical_route="canonical-governance",
                logical_capability="p2p_iris",
            ),
        )
        self._record_host_start(prepared, agent_type="p2p_iris")
        receipt = finalize_trial(prepared, self._host_result(prepared), ledger_path=self.ledger)
        self.assertEqual(receipt["logical_capability"], "p2p_iris")
        self.assertEqual(receipt["requested_profile_if_any"], "p2p_iris")
        self.assertEqual(receipt["observed_host_agent_type"], "p2p_iris")

    def test_unknown_requested_profile_is_rejected_without_router_expansion(self) -> None:
        with self.assertRaises(LiveBindingError) as raised:
            self._prepare("A", profile="p2p-uiux")
        self.assertEqual(str(raised.exception), "REQUESTED_PROFILE_UNSUPPORTED")

    def test_requested_permission_network_and_task_modes_are_fixed_before_trial_creation(self) -> None:
        for field, invalid in (
            ("permission_mode", "FULL_ACCESS"),
            ("network_policy", "ALLOW"),
            ("task_mode", "WRITE_PROJECT"),
        ):
            context, catalog = self._context("C1")
            trial_root = self.project / ".tmp" / f"invalid-{field}-{uuid.uuid4().hex}"
            request = default_execution_request()
            request[field] = invalid
            with self.subTest(field=field), self.assertRaises(LiveBindingError) as raised:
                prepare_trial(
                    trial_id=f"invalid-{field}-{uuid.uuid4().hex[:8]}",
                    condition="A",
                    scenario_id="C1",
                    context_input=context,
                    context_view=build_context_view(context, BASELINE_COMPAT),
                    source_catalog=catalog,
                    fixture={"read_only": True},
                    artifact_binding=self.artifact_binding,
                    requested_execution=request,
                    trial_root=trial_root,
                    project_root=self.project,
                )
            self.assertEqual(str(raised.exception), f"REQUESTED_{field.upper()}_INVALID")
            self.assertFalse(trial_root.exists())

    def test_permission_envelope_rejects_available_but_unauthorized_actions(self) -> None:
        context, catalog = self._context("C1")
        trial_root = self.project / ".tmp" / f"unauthorized-{uuid.uuid4().hex}"
        request = default_execution_request()
        request["permission_envelope"]["WRITE"] = True
        with self.assertRaises(LiveBindingError) as raised:
            prepare_trial(
                trial_id=f"unauthorized-{uuid.uuid4().hex[:8]}",
                condition="A",
                scenario_id="C1",
                context_input=context,
                context_view=build_context_view(context, BASELINE_COMPAT),
                source_catalog=catalog,
                fixture={"read_only": True},
                artifact_binding=self.artifact_binding,
                requested_execution=request,
                trial_root=trial_root,
                project_root=self.project,
            )
        self.assertEqual(str(raised.exception), "PERMISSION_ENVELOPE_NOT_READ_ONLY")
        self.assertFalse(trial_root.exists())

    def test_non_read_only_host_observation_cannot_finalize_live_trial(self) -> None:
        prepared = self._prepare("A")
        self._record_host_start(prepared, permission_mode="default")
        with self.assertRaises(LiveHostEvidenceError) as raised:
            finalize_trial(prepared, self._host_result(prepared), ledger_path=self.ledger)
        self.assertEqual(str(raised.exception), "HOST_PERMISSION_BOUNDARY_UNPROVEN")
        self.assertFalse((self.project / prepared["trial_root"]).joinpath("output.txt").exists())

    def test_observed_host_identity_mismatch_fails_closed(self) -> None:
        prepared = self._prepare(
            "A",
            profile="p2p_iris",
            route_observation=self._route(profile="p2p_iris", logical_route="canonical-governance", logical_capability="p2p_iris"),
        )
        self._record_host_start(prepared, agent_type="p2p_tecton")
        with self.assertRaises(LiveHostEvidenceError) as raised:
            finalize_trial(prepared, self._host_result(prepared), ledger_path=self.ledger)
        self.assertEqual(str(raised.exception), "HOST_IDENTITY_MISMATCH")

    def test_observed_host_session_and_turn_mismatch_fail_closed(self) -> None:
        prepared = self._prepare("A")
        self._record_host_start(prepared)
        with self.assertRaises(LiveHostEvidenceError) as raised:
            finalize_trial(
                prepared,
                self._host_result(prepared, session_id="wrong-session"),
                ledger_path=self.ledger,
            )
        self.assertEqual(str(raised.exception), "HOST_SESSION_ID_MISMATCH")

    def test_missing_host_receipt_is_capture_failure(self) -> None:
        prepared = self._prepare("A")
        with self.assertRaises(LiveHostEvidenceError) as raised:
            finalize_trial(prepared, self._host_result(prepared), ledger_path=self.ledger)
        self.assertEqual(str(raised.exception), "HOST_EVIDENCE_CAPTURE_FAILURE")

    def test_proxy_is_explicitly_non_live_and_cannot_promote(self) -> None:
        prepared = self._prepare("A")
        with self.assertRaises(LiveHostEvidenceError):
            finalize_trial(prepared, {"execution_source": LOCAL_PROXY_SOURCE, "output": "local proxy only"})
        prepared = self._prepare("A")
        receipt = finalize_trial(
            prepared,
            {"execution_source": LOCAL_PROXY_SOURCE, "output": "local proxy only"},
            require_live=False,
        )
        self.assertFalse(receipt["runtime_task_execution"])
        self.assertEqual(receipt["execution_authority"], "LOCAL_PROXY")
        self.assertEqual(receipt["ledger_event_status"], "NOT_REQUIRED")

    def test_unknown_condition_stale_source_and_artifact_fail_closed(self) -> None:
        context, catalog = self._context("C1")
        with self.assertRaises(LiveBindingError):
            prepare_trial(
                trial_id="invalid-condition",
                condition="X",
                scenario_id="C1",
                context_input=context,
                context_view=build_context_view(context, BASELINE_COMPAT),
                source_catalog=catalog,
                fixture={"read_only": True},
                artifact_binding=self.artifact_binding,
                requested_execution=default_execution_request(),
                trial_root=self.project / ".tmp" / "invalid-condition",
                project_root=self.project,
            )
        stale_catalog = dict(catalog)
        stale_catalog["history"] = {**catalog["history"], "content": {"changed": True}}
        with self.assertRaises(LiveBindingError):
            prepare_trial(
                trial_id="stale-source",
                condition="B",
                scenario_id="C1",
                context_input=context,
                context_view=build_context_view(context, CONTEXT_EFFICIENT_V1),
                source_catalog=stale_catalog,
                fixture={"read_only": True},
                artifact_binding=self.artifact_binding,
                requested_execution=default_execution_request(),
                trial_root=self.project / ".tmp" / "stale-source",
                project_root=self.project,
            )
        with self.assertRaises(LiveBindingError):
            bad_artifact = {**self.artifact_binding, "artifact_sha256": "0" * 64}
            self._prepare_with_artifact("A", bad_artifact)

    def _prepare_with_artifact(self, condition: str, artifact_binding: dict[str, object]) -> dict[str, object]:
        context, catalog = self._context("C1")
        return prepare_trial(
            trial_id=f"artifact-{condition}-{uuid.uuid4().hex[:8]}",
            condition=condition,
            scenario_id="C1",
            context_input=context,
            context_view=build_context_view(context, BASELINE_COMPAT if condition == "A" else CONTEXT_EFFICIENT_V1),
            source_catalog=catalog,
            fixture={"read_only": True},
            artifact_binding=artifact_binding,
            requested_execution=default_execution_request(),
            trial_root=self.project / ".tmp" / uuid.uuid4().hex,
            project_root=self.project,
        )

    def test_tampered_request_unsafe_root_and_secret_output_are_rejected(self) -> None:
        prepared = self._prepare("B")
        request_path = self.project / prepared["request_pointer"]
        request = json.loads(request_path.read_text(encoding="utf-8"))
        request["context_fingerprint"] = "0" * 64
        request_path.write_text(json.dumps(request), encoding="utf-8")
        with self.assertRaises(LiveBindingError):
            finalize_trial(prepared, {"execution_source": LOCAL_PROXY_SOURCE, "output": "proxy"}, require_live=False)
        context, catalog = self._context("C1")
        with self.assertRaises(LiveIsolationError):
            prepare_trial(
                trial_id="outside-root",
                condition="A",
                scenario_id="C1",
                context_input=context,
                context_view=build_context_view(context, BASELINE_COMPAT),
                source_catalog=catalog,
                fixture={"read_only": True},
                artifact_binding=self.artifact_binding,
                requested_execution=default_execution_request(),
                trial_root=self.project.parent / "outside-live-root",
                project_root=self.project,
            )
        prepared = self._prepare("A")
        with self.assertRaises(LiveHostEvidenceError):
            finalize_trial(
                prepared,
                {"execution_source": LOCAL_PROXY_SOURCE, "output": "password: leaked-value"},
                require_live=False,
            )

    def test_fresh_host_receipt_and_no_recursive_delegation_are_required(self) -> None:
        prepared = self._prepare("A")
        self._record_host_start(prepared, timestamp=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat())
        with self.assertRaises(LiveHostEvidenceError):
            finalize_trial(prepared, self._host_result(prepared), ledger_path=self.ledger)
        prepared = self._prepare("A")
        self._record_host_start(prepared)
        with self.assertRaises(LiveHostEvidenceError):
            finalize_trial(prepared, self._host_result(prepared, child_count=1), ledger_path=self.ledger)


if __name__ == "__main__":
    unittest.main()
