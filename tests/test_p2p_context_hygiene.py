"""P2P-CONTEXT-HYGIENE-01 (Issue #42): focused acceptance evidence.

Proves the required laws on existing machinery only:

A. ACTIVE/canonical content is selected by default.
B. HISTORICAL/SUPERSEDED content is excluded by default (retained, not deleted).
C. Explicit historical retrieval still succeeds.
D. A closed plan cannot regain active authority (no silent re-activation).
E. Exact workstream/SHA binding beats a highly text-similar stale record.
F. Evidence remains non-instructional.
G. OWNER_MICRO_LOOP_SUPPRESSION preserves real Owner Gates while
   suppressing micro-repair relays.
H. Existing Operations Notebook / Task State / governance authority intact.
I. No duplicate infrastructure introduced.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.context import (  # noqa: E402
    MINIMAL,
    STANDARD,
    SOURCE_LIFECYCLES,
    materialize_task_context,
    retrieve_task_context,
)
from p2p_capabilities.orchestration_policy import (  # noqa: E402
    OWNER_GATE_CLASSES,
    OWNER_MICRO_LOOP_SUPPRESSION,
    OWNER_MICRO_REPAIR_CLASSES,
    OrchestrationPolicyError,
    classify_owner_escalation,
)
from p2p_capabilities.task_state import (  # noqa: E402
    PlanIdentity,
    TaskContractError,
    TaskLifecycleError,
    TaskPlan,
    TaskStateStore,
    checkpoint_task,
    is_active_authority,
    next_safe_task,
    request_owner_decision,
    resolve_authoritative_plan,
)


NOW = "2026-09-01T00:00:00+00:00"
# Real-format 40-character Git object IDs (lowercase hex).
COMMIT_A = "39a1573457cc257eb96bbaf862e6ef59608b5939"  # actual main commit
TREE_A = "5c71fa23be7648956e8d57ac52cbff6503540d17"  # actual main tree
COMMIT_B = "b" * 40  # stale synthetic commit OID
COMMIT_C = "c" * 40  # sibling synthetic commit OID
# SHA-256 fingerprint: a separate concept (checkpoint state fingerprint), not
# a Git object ID.
FINGERPRINT_A = "a" * 64
REPOSITORY = "7roger89-web/P2P-upgrade-github-1"
WORKSTREAM = "P2P-CONTEXT-HYGIENE-01"
SUBJECT = "authority-aware active-context lifecycle"

NOTEBOOK = REPO_ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
GOVERNANCE = REPO_ROOT / "governance" / "development-control.json"
TASK_STATE_MODULE = SYSTEM_ROOT / "p2p_capabilities" / "task_state.py"
CONTEXT_MODULE = SYSTEM_ROOT / "p2p_capabilities" / "context.py"
POLICY_MODULE = SYSTEM_ROOT / "p2p_capabilities" / "orchestration_policy.py"


def goal(goal_id: str = "goal-hygiene") -> dict[str, object]:
    return {
        "goal_id": goal_id,
        "scope": ["bounded context-hygiene work"],
        "out_of_scope": ["scheduler", "background worker", "second router"],
        "completion_criteria": [],
    }


def task(task_id: str, **extra: object) -> dict[str, object]:
    return {
        "task_id": task_id,
        "title": f"Task {task_id}",
        "purpose": f"Bounded purpose for {task_id}",
        "dependencies": [],
        "scope": ["bounded work"],
        "acceptance_requirements": [f"acceptance-{task_id}"],
        "required_evidence": [f"evidence-{task_id}"],
        **extra,
    }


def source(source_id: str, role: str = "DIRECT", *, coverage=(), content=None, **extra) -> dict[str, object]:
    value = {
        "source_id": source_id,
        "path": source_id,
        "source_class": "AUTHORITATIVE_PROJECT_SOURCE",
        "retrieval_role": role,
        "coverage_ids": list(coverage),
        "scope": ["current-task"],
        "content": content if content is not None else {"source": source_id},
    }
    value.update(extra)
    return value


def direct_task(*refs: str, acceptance_refs=None, purpose="bounded task") -> dict[str, object]:
    return {
        "task_purpose": purpose,
        "scope": ["current-task"],
        "direct_authoritative_refs": list(refs),
        "acceptance": [
            {"coverage_id": f"acceptance-{index}", "source_refs": [ref], "required": True}
            for index, ref in enumerate(acceptance_refs or refs)
        ],
    }


def make_plan(goal_id: str = "goal-hygiene", **identity: object) -> TaskPlan:
    plan_identity = None
    if identity:
        plan_identity = PlanIdentity(
            repository=str(identity.get("repository", REPOSITORY)),
            workstream=str(identity.get("workstream", WORKSTREAM)),
            subject=str(identity.get("subject", SUBJECT)),
            source_commit=str(identity.get("source_commit", "")),
            source_tree=str(identity.get("source_tree", "")),
            pr=str(identity.get("pr", "")),
        )
    return TaskPlan.from_goal(
        goal(goal_id),
        [task("one")],
        now=NOW,
        plan_identity=plan_identity,
    )


class A_ActiveCanonicalSelectedByDefaultTests(unittest.TestCase):
    """A. ACTIVE/canonical content selected by default."""

    CATALOG = {
        "spec-current": source("spec-current", "DIRECT", coverage=["req-1"]),
        "spec-legacy": source("spec-legacy", "DIRECT", coverage=["req-1"], lifecycle="HISTORICAL"),
    }

    def test_active_source_selected_by_default(self) -> None:
        plan = retrieve_task_context(
            direct_task("spec-current", acceptance_refs=["spec-current"]),
            self.CATALOG,
            context_class=MINIMAL,
        )
        self.assertEqual(plan["status"], "SUFFICIENT")
        self.assertIn("spec-current", plan["selected_source_ids"])
        binding = next(item for item in plan["source_bindings"] if item["source_id"] == "spec-current")
        self.assertEqual(binding["lifecycle"], "CURRENT")
        self.assertTrue(binding["instruction_authority"])
        self.assertFalse(plan["include_historical"])

    def test_active_plan_is_active_authority(self) -> None:
        plan = make_plan()
        self.assertTrue(is_active_authority(plan))
        self.assertEqual(plan.plan_lifecycle, "ACTIVE")


class B_HistoricalExcludedByDefaultTests(unittest.TestCase):
    """B. HISTORICAL/SUPERSEDED content excluded by default (and retained)."""

    CATALOG = {
        "spec-current": source("spec-current", "DIRECT", coverage=["req-1"]),
        "spec-legacy": source("spec-legacy", "DIRECT", coverage=["req-1"], lifecycle="HISTORICAL"),
        "plan-old": source("plan-old", "DIRECT", coverage=["req-1"], lifecycle="SUPERSEDED"),
        "session-stale": source("session-stale", "DIRECT", coverage=["req-1"], lifecycle="CLOSED"),
        "archive-old": source("archive-old", "DIRECT", coverage=["req-1"], lifecycle="ARCHIVED"),
    }

    def test_non_current_lifecycles_excluded_with_explicit_reason(self) -> None:
        plan = retrieve_task_context(
            direct_task("spec-current", "spec-legacy", "plan-old", "session-stale", "archive-old", acceptance_refs=["spec-current"]),
            self.CATALOG,
            context_class=MINIMAL,
        )
        self.assertEqual(plan["status"], "SUFFICIENT", plan)
        self.assertEqual(plan["selected_source_ids"], ["spec-current"])
        excluded = {item["source_id"]: item["reason"] for item in plan["excluded"]}
        for stale_id in ("spec-legacy", "plan-old", "session-stale", "archive-old"):
            self.assertEqual(excluded[stale_id], "HISTORICAL_EXCLUDED_BY_DEFAULT", stale_id)
        # Exclusion is a retention decision, not a failure of the plan.
        self.assertFalse(any(reason.startswith("STALE") or reason == "BROKEN_POINTER" for reason in plan["failure_reasons"]))

    def test_lifecycle_vocabulary_is_durable_and_small(self) -> None:
        self.assertEqual(SOURCE_LIFECYCLES, ("CURRENT", "HISTORICAL", "SUPERSEDED", "CLOSED", "ARCHIVED"))


class C_ExplicitHistoricalRetrievalTests(unittest.TestCase):
    """C. Explicit historical retrieval still succeeds."""

    CATALOG = {
        "spec-current": source("spec-current", "DIRECT", coverage=["req-1"]),
        "spec-legacy": source("spec-legacy", "DIRECT", coverage=["req-1"], lifecycle="HISTORICAL"),
    }

    def test_explicit_inclusion_selects_historical_source(self) -> None:
        plan = retrieve_task_context(
            direct_task("spec-legacy", acceptance_refs=["spec-legacy"]),
            self.CATALOG,
            context_class=MINIMAL,
            include_historical=True,
        )
        self.assertEqual(plan["status"], "SUFFICIENT", plan)
        self.assertIn("spec-legacy", plan["selected_source_ids"])
        binding = next(item for item in plan["source_bindings"] if item["source_id"] == "spec-legacy")
        self.assertEqual(binding["lifecycle"], "HISTORICAL")
        self.assertTrue(plan["include_historical"])

    def test_default_vs_explicit_for_history_only_obligation(self) -> None:
        task_contract = direct_task("spec-legacy", acceptance_refs=["spec-legacy"])
        default_plan = retrieve_task_context(task_contract, self.CATALOG, context_class=MINIMAL)
        self.assertNotIn("spec-legacy", default_plan["selected_source_ids"])
        self.assertEqual(default_plan["status"], "INSUFFICIENT")
        explicit_plan = retrieve_task_context(task_contract, self.CATALOG, context_class=MINIMAL, include_historical=True)
        self.assertEqual(explicit_plan["status"], "SUFFICIENT")
        self.assertIn("spec-legacy", explicit_plan["selected_source_ids"])


class D_ClosedPlanAuthorityBlockedTests(unittest.TestCase):
    """D. Closed plan cannot regain active authority."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="p2p-ch01-store-", dir=str(REPO_ROOT / ".tmp"))
        self.project = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def store(self) -> TaskStateStore:
        return TaskStateStore(self.project)

    def _initialize_closed_store(self) -> TaskStateStore:
        store = self.store()
        store.initialize(make_plan(goal_id="goal-closed"), at=NOW)
        store.close_plan("work closed by control tower", source_refs=["issue/42"], at="2026-09-01T01:00:00+00:00")
        return store

    def test_closed_plan_rejects_all_mutations(self) -> None:
        store = self._initialize_closed_store()
        plan = store.require()
        self.assertFalse(is_active_authority(plan))
        with self.assertRaises(TaskLifecycleError):
            store.transition("one", "READY", now="2026-09-01T02:00:00+00:00")
        with self.assertRaises(TaskLifecycleError):
            store.preflight("one", now="2026-09-01T02:00:00+00:00")
        with self.assertRaises(TaskLifecycleError):
            store.revise(task_updates={"one": {"purpose": "stale rewrite"}}, reason="must fail")
        with self.assertRaises(TaskLifecycleError):
            checkpoint_task(plan, "one", {
                "checkpoint_ref": "checkpoint/stale",
                "state_fingerprint": FINGERPRINT_A,
                "recovery_classification": "SAFE_TO_RESUME",
                "next_safe_step": "stale",
                "captured_at": "2026-09-01T02:00:00+00:00",
            })
        with self.assertRaises(TaskLifecycleError):
            request_owner_decision(plan, "one", "stale question", options=["a", "b"])
        self.assertIsNone(next_safe_task(plan))

    def test_reload_and_reinstantiate_stay_closed(self) -> None:
        store = self._initialize_closed_store()
        # Fresh process-style reload: lifecycle survives persistence.
        reloaded = TaskStateStore(self.project).require()
        self.assertEqual(reloaded.plan_lifecycle, "CLOSED")
        self.assertFalse(is_active_authority(reloaded))
        with self.assertRaises(TaskLifecycleError):
            reloaded.transition("one", "READY", now="2026-09-01T03:00:00+00:00")
        # Re-instantiation from raw JSON cannot manufacture ACTIVE authority.
        raw = json.loads((self.project / ".p2p/state/task-state.json").read_text(encoding="utf-8"))
        rebuilt = TaskPlan.from_mapping(raw["plan"])
        self.assertEqual(rebuilt.plan_lifecycle, "CLOSED")
        with self.assertRaises(TaskLifecycleError):
            rebuilt.refresh_ready(now="2026-09-01T03:00:00+00:00")

    def test_closure_event_is_retained_and_queryable(self) -> None:
        store = self._initialize_closed_store()
        plan = store.require()
        self.assertEqual(len(plan.plan_lifecycle_events), 1)
        event = plan.plan_lifecycle_events[0]
        self.assertEqual(event["from_state"], "ACTIVE")
        self.assertEqual(event["to_state"], "CLOSED")
        self.assertIn("issue/42", event["source_refs"])
        events = store.read_events()
        self.assertEqual(events["status"], "PASS")
        names = [item["event"] for item in events["events"]]
        self.assertIn("task_plan_closed", names)

    def test_superseded_plan_also_loses_authority_with_successor_ref(self) -> None:
        store = self.store()
        store.initialize(make_plan(goal_id="goal-superseded"), at=NOW)
        updated = store.supersede_plan(
            "goal/next-plan", "replaced by successor plan", source_refs=["issue/42"], at="2026-09-01T01:00:00+00:00"
        )
        self.assertEqual(updated.plan_lifecycle, "SUPERSEDED")
        self.assertEqual(updated.plan_lifecycle_events[0]["successor_ref"], "goal/next-plan")
        reloaded = TaskStateStore(self.project).require()
        self.assertEqual(reloaded.plan_lifecycle, "SUPERSEDED")
        with self.assertRaises(TaskLifecycleError):
            reloaded.transition("one", "READY", now="2026-09-01T02:00:00+00:00")

    def test_closed_plan_cannot_be_closed_or_superseded_again(self) -> None:
        store = self._initialize_closed_store()
        with self.assertRaises(TaskLifecycleError):
            store.close_plan("double close")
        with self.assertRaises(TaskLifecycleError):
            store.supersede_plan("goal/x", "double close")

    def test_no_reopen_path_exists_on_plan_or_store(self) -> None:
        # The only legal lifecycle transitions are ACTIVE -> CLOSED/SUPERSEDED;
        # there is no API that moves a plan back to ACTIVE.
        self.assertNotIn("reopen_plan", dir(TaskPlan))
        self.assertNotIn("reopen", dir(TaskStateStore))
        plan = make_plan()
        closed = plan.close_plan("closed")
        with self.assertRaises(TaskLifecycleError):
            closed.close_plan("again")
        # An ACTIVE lifecycle can never be constructed with lifecycle events.
        with self.assertRaises(TaskContractError):
            TaskPlan.from_mapping({**closed.to_dict(), "plan_lifecycle": "ACTIVE"})

    def test_legacy_state_without_lifecycle_defaults_to_active(self) -> None:
        plan = make_plan(goal_id="goal-legacy")
        payload = plan.to_dict()
        del payload["plan_lifecycle"]
        del payload["plan_lifecycle_events"]
        del payload["plan_identity"]
        rebuilt = TaskPlan.from_mapping(payload)
        self.assertEqual(rebuilt.plan_lifecycle, "ACTIVE")
        self.assertTrue(is_active_authority(rebuilt))


class E_ExactBindingBeatsTextSimilarityTests(unittest.TestCase):
    """E. Exact workstream/SHA binding beats a highly text-similar stale record."""

    def _candidates(self) -> dict[str, TaskPlan]:
        # Current authoritative plan: exact identity binding with SHA/tree/PR.
        current = make_plan(goal_id="goal-current", source_commit=COMMIT_A, source_tree=TREE_A, pr="43")
        # Stale record: same repo/workstream/subject, stale SHA, and text that
        # is deliberately MORE similar to the current subject wording.
        stale = make_plan(
            goal_id="goal-stale",
            subject=SUBJECT,
            source_commit=COMMIT_B,
        )
        stale = self._retitle(stale, "authority-aware active-context lifecycle (current wording)")
        # Text-similar but different workstream.
        sibling = make_plan(goal_id="goal-sibling", subject=SUBJECT, workstream="P2P-CONTEXT-HYGIENE-00", source_commit=COMMIT_C)
        # Unbound plan with identical text.
        unbound = make_plan(goal_id="goal-unbound")
        return {"current": current, "stale": stale, "sibling": sibling, "unbound": unbound}

    @staticmethod
    def _retitle(plan: TaskPlan, title: str) -> TaskPlan:
        tasks = dict(plan.tasks)
        from dataclasses import replace

        tasks["one"] = replace(plan.tasks["one"], title=title)
        return replace(plan, tasks=tasks)

    def test_exact_binding_wins_over_text_similar_stale_record(self) -> None:
        candidates = self._candidates()
        result = resolve_authoritative_plan(
            [candidates["stale"], candidates["sibling"], candidates["unbound"], candidates["current"]],
            {"repository": REPOSITORY, "workstream": WORKSTREAM, "subject": SUBJECT, "source_commit": COMMIT_A, "source_tree": TREE_A, "pr": "43"},
        )
        self.assertEqual(result["status"], "PASS", result)
        self.assertFalse(result["similarity_used"])
        self.assertEqual(result["selected_plan"]["goal_id"], "goal-current")
        by_status = {item["candidate"]: item["status"] for item in result["candidates"]}
        self.assertEqual(by_status["candidate-0"], "BINDING_FIELD_MISMATCH")  # stale SHA loses
        self.assertEqual(by_status["candidate-1"], "IDENTITY_MISMATCH")  # wrong workstream loses
        self.assertEqual(by_status["candidate-2"], "UNBOUND")  # unbound never wins
        self.assertEqual(by_status["candidate-3"], "ELIGIBLE")

    def test_binding_without_sha_fails_closed_on_conflict(self) -> None:
        candidates = self._candidates()
        result = resolve_authoritative_plan(
            [candidates["current"], candidates["stale"]],
            {"repository": REPOSITORY, "workstream": WORKSTREAM, "subject": SUBJECT},
        )
        # Both plans match repo+workstream+subject and the binding does not
        # pin a SHA: no silent winner is invented.
        self.assertEqual(result["status"], "AUTHORITY_CONFLICT")
        self.assertNotIn("selected_plan", result)

    def test_closed_exact_match_cannot_win(self) -> None:
        candidates = self._candidates()
        closed_current = candidates["current"].close_plan("closed", now="2026-09-01T01:00:00+00:00")
        result = resolve_authoritative_plan(
            [closed_current, candidates["stale"]],
            {"repository": REPOSITORY, "workstream": WORKSTREAM, "subject": SUBJECT, "source_commit": COMMIT_A, "source_tree": TREE_A, "pr": "43"},
        )
        self.assertEqual(result["status"], "NOT_FOUND")
        by_status = {item["candidate"]: item["status"] for item in result["candidates"]}
        self.assertEqual(by_status["candidate-0"], "PLAN_NOT_ACTIVE:CLOSED")

    def test_identity_is_one_shot_and_not_rebindable(self) -> None:
        plan = make_plan(goal_id="goal-once", source_commit=COMMIT_A)
        with self.assertRaises(TaskContractError):
            plan.bind_plan_identity(PlanIdentity(repository=REPOSITORY, workstream=WORKSTREAM, subject=SUBJECT, source_commit=COMMIT_B), now="2026-09-01T01:00:00+00:00")
        closed = make_plan(goal_id="goal-once-closed", source_commit=COMMIT_A).close_plan("closed", now="2026-09-01T01:00:00+00:00")
        with self.assertRaises(TaskLifecycleError):
            closed.bind_plan_identity(PlanIdentity(repository=REPOSITORY, workstream=WORKSTREAM, subject=SUBJECT), now="2026-09-01T02:00:00+00:00")


class E2_GitObjectIdentityTests(unittest.TestCase):
    """E2. PlanIdentity carries real Git commit/tree object IDs, not SHA-256."""

    def test_real_repository_commit_and_tree_oids_accepted(self) -> None:
        # COMMIT_A / TREE_A are the actual main commit and tree object IDs of
        # this repository (verified via git rev-parse).
        self.assertEqual(len(COMMIT_A), 40)
        self.assertEqual(len(TREE_A), 40)
        identity = PlanIdentity(
            repository=REPOSITORY,
            workstream=WORKSTREAM,
            subject=SUBJECT,
            source_commit=COMMIT_A,
            source_tree=TREE_A,
            pr="43",
        )
        self.assertEqual(identity.source_commit, COMMIT_A)
        self.assertEqual(identity.source_tree, TREE_A)
        payload = identity.to_dict()
        self.assertEqual(payload["source_commit"], COMMIT_A)
        self.assertEqual(payload["source_tree"], TREE_A)
        self.assertNotIn("source_sha256", payload)
        rebuilt = PlanIdentity.from_mapping(payload)
        self.assertEqual(rebuilt.source_commit, COMMIT_A)
        self.assertEqual(rebuilt.source_tree, TREE_A)

    def test_real_oid_plan_resolves_as_authoritative(self) -> None:
        plan = make_plan(goal_id="goal-real", source_commit=COMMIT_A, source_tree=TREE_A, pr="43")
        result = resolve_authoritative_plan(
            [plan],
            {"repository": REPOSITORY, "workstream": WORKSTREAM, "subject": SUBJECT, "source_commit": COMMIT_A, "source_tree": TREE_A, "pr": "43"},
        )
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["selected_plan"]["plan_identity"]["source_commit"], COMMIT_A)
        self.assertEqual(result["selected_plan"]["plan_identity"]["source_tree"], TREE_A)

    def test_malformed_git_oids_rejected(self) -> None:
        base = dict(repository=REPOSITORY, workstream=WORKSTREAM, subject=SUBJECT)
        malformed_commits = (
            "a" * 64,  # a SHA-256 digest is not a Git object ID
            "a" * 39,  # one character short
            "a" * 41,  # one character long
            "g" * 40,  # non-hex character
            COMMIT_A.upper(),  # uppercase is not the canonical lowercase form
            COMMIT_A + " ",  # trailing whitespace
            "39a1573457cc257eb96bbaf862e6ef59608b593",  # 39 hex chars
        )
        for bad in malformed_commits:
            with self.assertRaises(TaskContractError, msg=repr(bad)):
                PlanIdentity(source_commit=bad, **base)
        for bad in malformed_commits:
            with self.assertRaises(TaskContractError, msg=repr(bad)):
                PlanIdentity(source_tree=bad, **base)

    def test_sha256_field_name_is_not_accepted(self) -> None:
        # The SHA-256 concept stays separate: the identity schema rejects a
        # source_sha256 key instead of silently mapping it to a Git OID.
        with self.assertRaises(TaskContractError):
            PlanIdentity.from_mapping(
                {**base_identity(), "source_sha256": "a" * 64}
            )

    def test_optional_oid_fields_may_be_absent(self) -> None:
        identity = PlanIdentity(**base_identity())
        self.assertEqual(identity.source_commit, "")
        self.assertEqual(identity.source_tree, "")
        self.assertEqual(identity.pr, "")


def base_identity() -> dict[str, str]:
    return {"repository": REPOSITORY, "workstream": WORKSTREAM, "subject": SUBJECT}


class F_EvidenceNonInstructionalTests(unittest.TestCase):
    """F. Evidence remains non-instructional even when textually relevant."""

    CATALOG = {
        "spec-current": source("spec-current", "DIRECT", coverage=["req-1"]),
        "evidence-past": source(
            "evidence-past",
            "EVIDENCE",
            coverage=["req-1"],
            source_class="EVIDENCE",
            content={"note": "evidence text highly similar to the task purpose"},
        ),
    }

    def test_evidence_selected_but_flagged_data_only(self) -> None:
        # STANDARD tier selects the KNOWN_EVIDENCE role (the evidence source).
        plan = retrieve_task_context(
            direct_task("spec-current", "evidence-past", acceptance_refs=["spec-current"]),
            self.CATALOG,
            context_class=STANDARD,
        )
        self.assertEqual(plan["status"], "SUFFICIENT")
        bindings = {item["source_id"]: item for item in plan["source_bindings"]}
        self.assertFalse(bindings["evidence-past"]["instruction_authority"])
        self.assertTrue(bindings["spec-current"]["instruction_authority"])
        self.assertEqual(plan["evidence_authority_guarantee"], "EVIDENCE_NEVER_INSTRUCTION_AUTHORITY")

    def test_materialized_evidence_stays_non_instructional(self) -> None:
        plan = retrieve_task_context(
            direct_task("spec-current", "evidence-past", acceptance_refs=["spec-current"]),
            self.CATALOG,
            context_class=STANDARD,
        )
        materialized = materialize_task_context(plan, self.CATALOG, role="WORKER")
        items = {item["source_id"]: item for item in materialized["materialized_context"]["items"]}
        self.assertFalse(items["evidence-past"]["instruction_authority"])
        self.assertTrue(items["spec-current"]["instruction_authority"])

    def test_retrieval_relevance_never_upgrades_evidence(self) -> None:
        # The evidence source is the only candidate matching a required
        # obligation; it is still materialized as data, not instruction.
        plan = retrieve_task_context(
            direct_task("evidence-past", acceptance_refs=["evidence-past"]),
            self.CATALOG,
            context_class=STANDARD,
        )
        self.assertEqual(plan["status"], "SUFFICIENT")
        binding = plan["source_bindings"][0]
        self.assertEqual(binding["source_id"], "evidence-past")
        self.assertFalse(binding["instruction_authority"])


class G_OwnerMicroLoopSuppressionTests(unittest.TestCase):
    """G. OWNER_MICRO_LOOP_SUPPRESSION: micro-repair relays suppressed, real gates intact."""

    def test_real_owner_gates_always_route_to_owner(self) -> None:
        for gate in OWNER_GATE_CLASSES:
            result = classify_owner_escalation(gate)
            self.assertEqual(result["route"], "OWNER_GATE", gate)
            self.assertTrue(result["owner_gate_required"])
            self.assertTrue(result["real_owner_gates_preserved"])
            self.assertEqual(result["policy"], OWNER_MICRO_LOOP_SUPPRESSION)

    def test_micro_repairs_stay_in_writer_repair_loop(self) -> None:
        for action in OWNER_MICRO_REPAIR_CLASSES:
            result = classify_owner_escalation(action, finding_ref="finding/1")
            self.assertEqual(result["route"], "WRITER_REPAIR_LOOP", action)
            self.assertFalse(result["owner_gate_required"])
            self.assertTrue(result["suppressed_owner_relay"])
            self.assertEqual(result["finding_ref"], "finding/1")

    def test_gate_and_micro_vocabulary_is_exact(self) -> None:
        self.assertEqual(set(OWNER_GATE_CLASSES), {
            "MERGE_PROMOTION",
            "PRODUCTION_DEPLOY",
            "DESTRUCTIVE_MUTATION",
            "SECRETS",
            "MAJOR_SPEND_INFRASTRUCTURE",
            "HARD_ROLLBACK",
            "SCOPE_CHANGING_BLOCKER",
        })
        self.assertEqual(set(OWNER_MICRO_REPAIR_CLASSES), {
            "FINDING",
            "FIXTURE_REPAIR",
            "FOCUSED_TEST_REPAIR",
            "EVIDENCE_COUNT_CORRECTION",
            "REMOTE_SYNC_CORRECTION",
        })

    def test_unknown_action_fails_closed(self) -> None:
        with self.assertRaises(OrchestrationPolicyError):
            classify_owner_escalation("VAGUE_REQUEST")

    def test_suppression_is_documented_with_real_gates_preserved(self) -> None:
        text = NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("OWNER_MICRO_LOOP_SUPPRESSION", text)
        self.assertIn("never removes or weakens a real Owner Gate", text)


class H_ExistingAuthoritySurfacesIntactTests(unittest.TestCase):
    """H. Existing Operations Notebook / Task State / governance authority intact."""

    def test_notebook_rule_set_and_gate_intact(self) -> None:
        text = NOTEBOOK.read_text(encoding="utf-8")
        for heading in (
            "RULE 01 — EXPLICIT_DESTINATION",
            "RULE 04 — GITHUB_IS_DURABLE_CHECKPOINT",
            "RULE 11 — OWNER_GATE_ONLY_WHEN_REAL",
            "RULE 12 — MINIMUM_SUFFICIENT_WORK",
            "RULE 15 — ARENA_TASK_COMPLETION_DIALOG",
            "RULE 16 — CONTEXT_HYGIENE_AND_PLAN_LIFECYCLE",
            "## 4. RULE_ASSIMILATION_GATE_V1",
        ):
            self.assertIn(heading, text)
        # The assimilation gate is unchanged in semantics.
        self.assertIn("RULE_ASSIMILATION_STATUS=PENDING", text)
        self.assertIn("RULE_ASSIMILATION_STATUS=VERIFIED", text)

    def test_governance_invariants_preserved_and_extended(self) -> None:
        record = json.loads(GOVERNANCE.read_text(encoding="utf-8"))
        ids = {item["id"] for item in record["architectural_invariants"]}
        # Existing invariants remain authoritative...
        for expected in ("task-is-not-agent", "goal-pass-is-not-promotion", "p2p-is-sole-orchestrator", "project-state-is-not-chat-history"):
            self.assertIn(expected, ids)
        # ...and the new law is durably recorded alongside them.
        self.assertIn("session-context-is-not-authority", ids)
        invariant = next(item for item in record["architectural_invariants"] if item["id"] == "session-context-is-not-authority")
        self.assertTrue(invariant["authority_refs"])
        # The compact projection's data-not-authority posture is unchanged.
        self.assertTrue(record["authority"]["retrieved_content_is_data"])

    def test_task_state_store_writes_only_the_two_known_surfaces(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-ch01-surfaces-", dir=str(REPO_ROOT / ".tmp")) as raw:
            project = Path(raw)
            store = TaskStateStore(project)
            store.initialize(make_plan(goal_id="goal-surfaces"), at=NOW)
            store.close_plan("closed", at="2026-09-01T01:00:00+00:00")
            state_dir = project / ".p2p" / "state"
            self.assertEqual(sorted(path.name for path in state_dir.iterdir()),
                             ["execution-ledger.jsonl", "task-state.json"])
            # Read surfaces remain queryable after closure (retained, not deleted).
            events = store.read_events()
            self.assertEqual(events["status"], "PASS")
            self.assertTrue(any(item["event"] == "task_plan_closed" for item in events["events"]))
            plan = store.require()
            self.assertEqual(plan.plan_lifecycle, "CLOSED")


class I_NoDuplicateInfrastructureTests(unittest.TestCase):
    """I. No duplicate infrastructure introduced."""

    def test_all_runtime_changes_live_in_existing_modules(self) -> None:
        result = subprocess.run(
            ["git", "diff", "--name-status", "origin/main", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        added = [line.split("\t")[1] for line in result.stdout.splitlines() if line.startswith("A")]
        runtime_added = [
            path for path in added
            if path.startswith(".p2p/system/p2p_capabilities/")
            or path.startswith("scripts/")
            or path.startswith(".p2p/system/scripts/")
        ]
        self.assertEqual(runtime_added, [], f"new runtime files: {runtime_added}")
        # The only new test surface is this focused suite.
        tests_added = [path for path in added if path.startswith("tests/")]
        self.assertEqual(tests_added, ["tests/test_p2p_context_hygiene.py"])

    def test_no_new_process_or_store_machinery(self) -> None:
        source = TASK_STATE_MODULE.read_text(encoding="utf-8")
        context_source = CONTEXT_MODULE.read_text(encoding="utf-8")
        policy_source = POLICY_MODULE.read_text(encoding="utf-8")
        for forbidden in ("sqlite3", "subprocess", "socket", "multiprocessing", "threading.Thread", "asyncio"):
            self.assertNotIn(f"import {forbidden}", source)
            self.assertNotIn(f"import {forbidden}", context_source)
            self.assertNotIn(f"import {forbidden}", policy_source)
        # task_state remains the single state store; no second ledger path.
        self.assertEqual(source.count("class TaskStateStore"), 1)
        self.assertNotIn("class ContextStore", context_source)
        self.assertNotIn("class Scheduler", source)

    def test_session_context_law_is_documented_not_reimplemented(self) -> None:
        # The durable identity law already lives in the notebook (RULE 04);
        # RULE 16 references existing modules instead of creating new ones.
        text = NOTEBOOK.read_text(encoding="utf-8")
        flat = re.sub(r"\s+", " ", text)
        self.assertIn("existing machinery, no new subsystem", flat)


if __name__ == "__main__":
    unittest.main()
