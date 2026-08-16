from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import p2p_workflow  # noqa: E402

from p2p_capabilities.context import (  # noqa: E402
    BASELINE_COMPAT,
    CONTEXT_EFFICIENT_V1,
    CONTEXT_MODES,
    LOCAL_SERIALIZATION_PROXY,
    ContextBindingError,
    ContextModeError,
    ContextSafetyError,
    StaleContextError,
    build_context_view,
    context_fingerprint,
    resolve_context_pointer,
    select_context_mode,
    validate_context_bindings,
)


def _source(source_id: str, content: object, path: str) -> tuple[dict[str, object], dict[str, object]]:
    digest = context_fingerprint(content)
    binding = {"source_id": source_id, "path": path, "source_hash": digest, "required": source_id == "goal"}
    catalog = {"source_id": source_id, "path": path, "source_hash": digest, "content": content}
    return binding, catalog


def _context(scenario: str, *, facts: list[dict[str, object]] | None = None, extra: dict[str, object] | None = None) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    goal_binding, goal_source = _source("goal", {"scenario": scenario, "goal": "execute the bounded task"}, f"fixtures/{scenario}/goal.json")
    history_value = "historical detail that is reachable but not needed to start this task " * 40
    history_binding, history_source = _source("history", {"scenario": scenario, "detail": history_value}, f"fixtures/{scenario}/history.json")
    source_bindings = [goal_binding, history_binding]
    catalog = {"goal": goal_source, "history": history_source}
    value: dict[str, object] = {
        "goal_id": f"goal-{scenario}",
        "task_or_goal": f"{scenario}: execute the requested P2P task",
        "scope": ["current-task"],
        "non_scope": ["unrelated-history", "provider-experiment"],
        "acceptance": [
            {"item_id": "acceptance-main", "value": "the explicit acceptance requirement", "required": True},
        ],
        "relevant_facts": facts or [{"item_id": "fact-direct", "value": "directly referenced project fact", "required": True}],
        "relevant_decisions": [{"item_id": "decision-invariant", "value": "preserve the canonical invariant", "required": True}],
        "direct_dependencies": [{"item_id": "dependency-contract", "value": "the direct dependency result", "required": True}],
        "history": [
            {
                "item_id": "history-unrelated",
                "value": history_value,
                "defer": True,
                "pointer_id": "pointer-history",
                "source_binding": "history",
            }
        ],
        "evidence_pointers": [
            {
                "pointer_id": "pointer-history",
                "label": "authoritative historical source",
                "authority": "FACT_LEDGER",
                "scope": ["current-task"],
                "freshness": "CURRENT",
                "provenance": "fixture-source",
                "content_class": "EVIDENCE",
                "source_binding": "history",
            }
        ],
        "capability_constraints": ["same-tools", "same-capability-scope"],
        "permission_constraints": ["READ != WRITE", "owner approval remains explicit"],
        "source_bindings": source_bindings,
        "access_contract": {"tools": ["read", "write"], "source_catalog": "fixture-authoritative-sources"},
    }
    if extra:
        value.update(extra)
    return value, catalog


def _scenarios() -> list[tuple[str, dict[str, object], dict[str, dict[str, object]]]]:
    scenarios: list[tuple[str, dict[str, object], dict[str, dict[str, object]]]] = []
    base, catalog = _context("C1-tiny-configuration-edit")
    scenarios.append(("C1", base, catalog))
    for name, label in (
        ("C2", "bug-diagnosis"),
        ("C3", "multi-file-feature"),
        ("C4", "architecture-decision"),
        ("C5", "backend-contract"),
        ("C6", "normal-uiux-without-aesthetica"),
        ("C8", "research-evidence"),
    ):
        value, source_catalog = _context(f"{name}-{label}")
        scenarios.append((name, value, source_catalog))

    value, source_catalog = _context(
        "C7-accessibility-heavy-ui",
        extra={
            "acceptance": [
                {"item_id": "accessibility-constraints", "value": "keyboard access, focus order, labels, contrast", "required": True},
            ]
        },
    )
    scenarios.append(("C7", value, source_catalog))

    conflicting = [
        {"item_id": "fact-deployment-a", "fact_key": "deployment-target", "conflict_group": "deployment-target", "status": "CONFLICT", "value": "target A", "relevant": True},
        {"item_id": "fact-deployment-b", "fact_key": "deployment-target", "conflict_group": "deployment-target", "status": "CONFLICT", "value": "target B", "relevant": True},
    ]
    value, source_catalog = _context("C9-conflicting-project-fact", facts=conflicting)
    scenarios.append(("C9", value, source_catalog))

    value, source_catalog = _context(
        "C10-missing-optional-capability",
        extra={"capability_constraints": ["optional capability: missing; keep this state representable"]},
    )
    scenarios.append(("C10", value, source_catalog))

    value, source_catalog = _context(
        "C11-interrupted-resume",
        extra={
            "direct_dependencies": [
                {"item_id": "resume-critical-state", "value": "resume from the last authoritative checkpoint", "required": True},
            ]
        },
    )
    scenarios.append(("C11", value, source_catalog))

    value, source_catalog = _context(
        "C12-owner-approval-boundary",
        extra={"permission_constraints": ["owner approval required before protected action", "INTENT != PERMISSION"]},
    )
    scenarios.append(("C12", value, source_catalog))
    return scenarios


class ContextDeliveryTests(unittest.TestCase):
    def test_exact_modes_and_fail_closed_selection(self) -> None:
        self.assertEqual(CONTEXT_MODES, (BASELINE_COMPAT, CONTEXT_EFFICIENT_V1))
        self.assertEqual(select_context_mode(), BASELINE_COMPAT)
        self.assertEqual(select_context_mode(BASELINE_COMPAT), BASELINE_COMPAT)
        self.assertEqual(select_context_mode(CONTEXT_EFFICIENT_V1), CONTEXT_EFFICIENT_V1)
        with self.assertRaises(ContextModeError):
            select_context_mode("CONTEXT_EFFICIENT_V2")
        with self.assertRaises(ContextModeError):
            select_context_mode("")

    def test_all_twelve_scenarios_have_real_difference_and_fair_access(self) -> None:
        self.assertEqual(len(_scenarios()), 12)
        for scenario_id, context, catalog in _scenarios():
            with self.subTest(scenario=scenario_id):
                baseline = build_context_view(context, BASELINE_COMPAT)
                efficient = build_context_view(context, CONTEXT_EFFICIENT_V1)
                self.assertNotEqual(baseline["context_fingerprint"], efficient["context_fingerprint"])
                self.assertEqual(baseline["source_bindings"], efficient["source_bindings"])
                self.assertEqual(baseline["access_contract"], efficient["access_contract"])
                self.assertEqual(validate_context_bindings(efficient, catalog)["status"], "CURRENT")
                self.assertEqual(efficient["serialized_size"]["label"], LOCAL_SERIALIZATION_PROXY)
                self.assertLess(efficient["serialized_size"]["bytes"], baseline["serialized_size"]["bytes"])
                self.assertTrue(efficient["context_manifest"]["context_fingerprint"])

    def test_default_is_baseline_and_construction_is_deterministic(self) -> None:
        context, _ = _context("deterministic")
        first = build_context_view(context)
        second = build_context_view(context)
        self.assertEqual(first, second)
        self.assertEqual(first["context_mode"], BASELINE_COMPAT)
        self.assertFalse(first["experimental"])

    def test_required_acceptance_constraints_and_dependencies_are_retained(self) -> None:
        context, _ = _context(
            "required-fields",
            extra={
                "acceptance": [{"item_id": "protected-acceptance", "value": "owner approval and security boundary", "required": True}],
                "permission_constraints": ["protected-area constraint", "security boundary", "owner approval required"],
                "capability_constraints": ["canonical invariant: 8 agents; 8/8 quorum"],
                "direct_dependencies": [{"item_id": "direct-contract", "value": "dependency result", "required": True}],
            },
        )
        efficient = build_context_view(context, CONTEXT_EFFICIENT_V1)
        self.assertIn("protected-acceptance", {item["item_id"] for item in efficient["acceptance"]})
        self.assertIn("security boundary", efficient["permission_constraints"])
        self.assertIn("owner approval required", efficient["permission_constraints"])
        self.assertIn("canonical invariant: 8 agents; 8/8 quorum", efficient["capability_constraints"])
        self.assertIn("direct-contract", {item["item_id"] for item in efficient["direct_dependencies"]})

    def test_conflicting_facts_remain_conflicting(self) -> None:
        scenario = next(item for item in _scenarios() if item[0] == "C9")
        efficient = build_context_view(scenario[1], CONTEXT_EFFICIENT_V1)
        facts = {item["item_id"]: item for item in efficient["relevant_facts"]}
        self.assertEqual(facts["fact-deployment-a"]["status"], "CONFLICT")
        self.assertEqual(facts["fact-deployment-b"]["status"], "CONFLICT")
        self.assertNotEqual(facts["fact-deployment-a"]["value"], facts["fact-deployment-b"]["value"])

    def test_pointer_resolves_and_stale_binding_is_rejected(self) -> None:
        context, catalog = _context("pointer-resolution")
        efficient = build_context_view(context, CONTEXT_EFFICIENT_V1)
        resolved = resolve_context_pointer(efficient, "pointer-history", catalog)
        self.assertTrue(resolved["authoritative"])
        self.assertEqual(resolved["status"], "RESOLVED")
        stale_catalog = dict(catalog)
        stale_catalog["history"] = {**catalog["history"], "content": {"changed": True}}
        with self.assertRaises(StaleContextError):
            validate_context_bindings(efficient, stale_catalog)
        self.assertEqual(resolve_context_pointer(efficient, "pointer-history", iter(catalog.values()))["status"], "RESOLVED")

    def test_pointer_hash_must_match_its_source_binding(self) -> None:
        context, _ = _context("pointer-hash-mismatch")
        context["evidence_pointers"][0]["source_hash"] = "0" * 64
        with self.assertRaises(ContextBindingError):
            build_context_view(context, CONTEXT_EFFICIENT_V1)

    def test_deferred_detail_requires_a_pointer(self) -> None:
        context, _ = _context("missing-pointer")
        context["history"] = [{"item_id": "unreachable", "value": "detail", "defer": True}]
        with self.assertRaises(ContextSafetyError):
            build_context_view(context, CONTEXT_EFFICIENT_V1)

    def test_ambiguous_relevance_is_included_not_silently_dropped(self) -> None:
        context, _ = _context("ambiguous")
        context["history"] = [{"item_id": "ambiguous-detail", "value": "unknown relevance", "defer": True, "ambiguous": True, "pointer_id": "pointer-history"}]
        efficient = build_context_view(context, CONTEXT_EFFICIENT_V1)
        self.assertIn("ambiguous-detail", {item["item_id"] for item in efficient["preloaded"]["history"]})
        self.assertTrue(efficient["selection_warnings"])

    def test_no_secret_fields_or_path_leakage_in_manifest(self) -> None:
        context, _ = _context("secrets")
        context["permission_constraints"] = {"api_token": "do-not-copy"}
        with self.assertRaises(ContextSafetyError):
            build_context_view(context, CONTEXT_EFFICIENT_V1)
        context, _ = _context("ancestor-path")
        context["source_bindings"] = [{"source_id": "bad", "path": "../outside.json", "source_hash": "0" * 64}]
        with self.assertRaises(ContextSafetyError):
            build_context_view(context, CONTEXT_EFFICIENT_V1)

    def test_pointer_binding_must_be_in_authoritative_source_bindings(self) -> None:
        context, _ = _context("unbound-pointer")
        context["evidence_pointers"][0]["source_binding"] = "missing-source"
        with self.assertRaises(ContextBindingError):
            build_context_view(context, CONTEXT_EFFICIENT_V1)

    def test_context_manifest_is_observation_metadata_not_access_expansion(self) -> None:
        context, _ = _context("access-boundary")
        view = build_context_view(context, CONTEXT_EFFICIENT_V1)
        self.assertEqual(view["permission_constraints"], context["permission_constraints"])
        self.assertEqual(view["capability_constraints"], context["capability_constraints"])
        self.assertEqual(view["access_contract"], context["access_contract"])
        self.assertNotIn("source_catalog_content", view["context_manifest"])
        self.assertNotIn("credentials", view["context_manifest"])

    def test_workflow_receipts_expose_both_modes_without_changing_quorum(self) -> None:
        fixture = REPO_ROOT / "tests" / "fixtures" / "new-project"
        temp_parent = REPO_ROOT / ".tmp"
        temp_parent.mkdir(parents=True, exist_ok=True)

        def run_fixture(mode: str | None) -> tuple[Path, dict[str, object]]:
            handle = tempfile.TemporaryDirectory(dir=temp_parent, prefix="p2p-context-workflow-")
            project = Path(handle.name)
            for source_file in fixture.iterdir():
                if not source_file.is_file():
                    continue
                shutil.copy2(source_file, project / source_file.name)
            result = p2p_workflow.run_workflow(
                project,
                "Build and finish this small application and make sure it is ready.",
                package_hint=str(REPO_ROOT),
                acceptance=True,
                context_mode=mode,
            )
            # Keep the isolated project alive long enough for assertions; the
            # caller owns cleanup through the returned handle attached below.
            result["_temp_handle"] = handle
            return project, result

        baseline_project, baseline = run_fixture(None)
        efficient_project, efficient = run_fixture(CONTEXT_EFFICIENT_V1)
        try:
            self.assertEqual(baseline["status"], "PASS")
            self.assertEqual(efficient["status"], "PASS")
            self.assertEqual(baseline["context_mode"], BASELINE_COMPAT)
            self.assertEqual(efficient["context_mode"], CONTEXT_EFFICIENT_V1)
            self.assertEqual(baseline["selected_agents"], efficient["selected_agents"])
            self.assertEqual(baseline["quorum_size"], efficient["quorum_size"])
            self.assertEqual(baseline["full_quorum_used"], efficient["full_quorum_used"])
            self.assertEqual(baseline["context_serialized_size"]["label"], LOCAL_SERIALIZATION_PROXY)
            self.assertEqual(efficient["context_serialized_size"]["label"], LOCAL_SERIALIZATION_PROXY)
            self.assertLess(efficient["context_serialized_size"]["bytes"], baseline["context_serialized_size"]["bytes"])

            for project, result in ((baseline_project, baseline), (efficient_project, efficient)):
                manifest_path = project / str(result["context_manifest_pointer"])
                report_path = project / str(result["report_json"])
                capsule_path = project / str(result["capsule"])
                status_path = project / ".p2p" / "state" / "project-status.json"
                self.assertTrue(manifest_path.is_file())
                self.assertTrue(report_path.is_file())
                self.assertTrue(capsule_path.is_file())
                self.assertTrue(status_path.is_file())
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                report = json.loads(report_path.read_text(encoding="utf-8"))
                status = json.loads(status_path.read_text(encoding="utf-8"))
                self.assertEqual(manifest["context_mode"], result["context_mode"])
                self.assertEqual(manifest["context_fingerprint"], result["context_fingerprint"])
                self.assertIn("task_targeted_context", manifest)
                self.assertIn(manifest["task_targeted_context"].get("status"), {"SUFFICIENT", "INSUFFICIENT", "STALE", "CONTRADICTED", "BLOCKED"})
                self.assertEqual(report["context_manifest_pointer"], result["context_manifest_pointer"])
                self.assertEqual(status["context_mode"], result["context_mode"])
                events = [json.loads(line) for line in (project / ".p2p" / "state" / "execution-ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
                self.assertTrue(any(event.get("event") == "run_started" and event.get("context_mode") == result["context_mode"] for event in events))
                self.assertTrue(any(event.get("event") == "terminal" and event.get("context_fingerprint") == result["context_fingerprint"] for event in events))
        finally:
            baseline["_temp_handle"].cleanup()
            efficient["_temp_handle"].cleanup()

    def test_workflow_rejects_unknown_context_mode(self) -> None:
        temp_parent = REPO_ROOT / ".tmp"
        temp_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_parent, prefix="p2p-context-invalid-") as raw:
            project = Path(raw)
            (project / "app.py").write_text("READY_FOR_DEMO = True\n", encoding="utf-8")
            with self.assertRaises(ContextModeError):
                p2p_workflow.run_workflow(
                    project,
                    "Prepare this small application for a bounded baseline.",
                    package_hint=str(REPO_ROOT),
                    acceptance=True,
                    context_mode="CONTEXT_EFFICIENT_V2",
                )


if __name__ == "__main__":
    unittest.main()
