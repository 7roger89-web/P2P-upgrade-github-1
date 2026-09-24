"""Executable regression matrix for Arena FAST_CANARY runtime enforcement.

Issue #254 proved that a NEW Arena medium/high-risk session was NOT stopped at
the FAST_CANARY boundary: the executor investigated broadly, returned a terminal
technical conclusion, emitted no ``CANARY_EVIDENCE_PACKET_V1``, and bypassed the
external grade plus Owner continuation. The external session-quality grade for
that blind test was RED.

These tests encode that live defect as an executable regression and prove the
smallest repair inside the existing Control Tower prompt/session lifecycle:

    existing MODEL_CANARY_GATE_V1
    + existing OWNER_CONTINUATION_GATE_V1
    + existing execution ledger
    + existing prompt assembly

They deliberately assert runtime behavior (generated prompts, ledger events,
ingest, external grading, continuation) instead of documentation-string
presence. No second router, daemon, scheduler, benchmark service, score
database, telemetry platform, or project registry is created.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
for candidate in (str(SYSTEM_ROOT), str(SCRIPTS_ROOT), str(REPO_ROOT)):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import p2p_control_tower as control_tower  # noqa: E402
from p2p_capabilities import control_tower_handoff as handoff  # noqa: E402
from p2p_capabilities import owner_goal  # noqa: E402
from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    BindingError,
    CanaryDirective,
    ControlTower,
    SessionBinding,
    build_execution_prompt,
    canary_prompt_lines,
    canary_requirement,
    classify_canary_evidence,
    classify_task_risk_class,
    create_return_packet,
    parse_canary_evidence_packet,
)

BASE_SHA = "a" * 40
BASE_TREE = "b" * 40

# The real bounded task shape observed in the 2026-09-24 blind test.
BLIND_TEST_TASK = (
    "Repair the Control Tower runtime so a new medium/high-risk Arena session "
    "stops at the FAST_CANARY boundary, mutating runtime prompt generation, "
    "ledger events and gates"
)
LOW_RISK_TASK = "Update the typo in the README changelog label"

CANARY_TOKENS = (
    "FAST_CANARY_REQUIRED=YES",
    "REAL_TASK_FIRST_SLICE=CANARY",
    "CANARY_DURABLE_MUTATION_ALLOWED=NO",
    "STOP_AFTER_CANARY=YES",
    "EXECUTOR_SELF_CLASSIFICATION=FORBIDDEN",
    "MODEL_IDENTITY=UNKNOWN",
)
CHECKPOINT_TOKENS = (
    "CONTINUATION_CHECKPOINT=READY",
    "OWNER_ACTION_REQUIRED=YES",
    "NATIVE_ACTION_HINT=KEEP_WORKING_IF_APPROVED",
    "FALLBACK_OWNER_REPLY=Tiếp tục công việc",
)


def canary_evidence_block(
    *,
    law_source: str = "7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md",
    current_state: str = "arena/canary @ 6adfa3b85658e4c0670ccfc22eb22e19e6395879",
    facts: str = "runtime has no FAST_CANARY token; only structural policy tests exist",
    decisive_check: str = "grep -c FAST_CANARY scripts/p2p_control_tower.py",
    check_result: str = "exit=0; 0 matches in runtime",
    errors: str = "NONE",
    recovery: str = "NONE",
    durable_mutation: str = "NO",
    model_identity: str = "UNKNOWN",
    extra_lines: tuple[str, ...] = (),
) -> str:
    lines = [
        "CANARY_EVIDENCE_PACKET_V1",
        f"P2P_LAW_SOURCE={law_source}",
        f"CURRENT_STATE={current_state}",
        f"FACTS={facts}",
        f"DECISIVE_CHECK={decisive_check}",
        f"CHECK_RESULT={check_result}",
        f"ERRORS_ENCOUNTERED={errors}",
        f"RECOVERY_ACTIONS={recovery}",
        f"DURABLE_MUTATION_CREATED={durable_mutation}",
        f"MODEL_IDENTITY={model_identity}",
        *CHECKPOINT_TOKENS,
        *extra_lines,
    ]
    return "\n".join(lines)


def canary_response(
    binding: SessionBinding,
    *,
    evidence_block: str | None = None,
    session_state: str = "READY",
    base_sha: str = BASE_SHA,
    base_tree: str = BASE_TREE,
) -> str:
    """Build one complete executor response for a canary turn."""

    packet = create_return_packet(
        binding,
        session_state=session_state,
        canonical_base_sha=base_sha,
        canonical_base_tree=base_tree,
        canonical_relation="CURRENT",
        worktree="fixture-worktree",
        branch="fixture-branch",
        changes=(),
        test_results={"canary": "EVIDENCE_ONLY"},
        evidence=("canary-evidence-only",),
        candidate_or_checkpoint_sha="UNKNOWN",
        blockers=(),
        next_recommended_action="Wait for external canary grade and Owner continuation.",
        law_check={
            "status": "PASS",
            "source": "7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md",
            "source_sha256": "0" * 64,
        },
        experience_check={"decision": "NO_MATCH"},
    )
    prefix = evidence_block if evidence_block is not None else canary_evidence_block()
    return f"{prefix}\n\n{packet.to_marked_text()}"


class ArenaCanaryRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="p2p-arena-canary-")
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    # --- helpers ---------------------------------------------------------
    def tower(self) -> ControlTower:
        return ControlTower(
            self.root,
            current_canonical_base_sha=BASE_SHA,
            current_canonical_base_tree=BASE_TREE,
        )

    def binding(self, session_id: str = "session-arena-canary-0001") -> SessionBinding:
        return SessionBinding(
            session_id=session_id,
            host="ARENA",
            goal_id="P2P-CT01-CANARY",
            goal=BLIND_TEST_TASK,
        )

    def directive(self, session_id: str = "session-arena-canary-0001") -> CanaryDirective:
        return CanaryDirective(
            host="ARENA",
            session_id=session_id,
            goal_id="P2P-CT01-CANARY",
            goal=BLIND_TEST_TASK,
            original_task=BLIND_TEST_TASK,
            risk_class=classify_task_risk_class(BLIND_TEST_TASK),
        )

    def start_cli(self, *, host: str = "ARENA", goal: str = BLIND_TEST_TASK, session_id: str = "s1") -> dict:
        output = self._run_cli(
            [
                "start",
                "--host",
                host,
                "--goal-id",
                "P2P-CT01-CANARY",
                "--task-id",
                "TASK-CANARY-1",
                "--session-id",
                session_id,
                "--goal",
                goal,
                "--json",
            ]
        )
        return json.loads(output)

    def _run_cli(self, args: list[str]) -> str:
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = control_tower.main(["--root", str(self.root), *args])
        self.assertEqual(0, code, buffer.getvalue())
        return buffer.getvalue()

    def ingest_response(self, response: str) -> dict:
        response_path = self.root / "response.txt"
        response_path.write_text(response, encoding="utf-8")
        return json.loads(self._run_cli(["ingest", "--response-file", str(response_path), "--json"]))

    # --- T01 runtime trigger ---------------------------------------------
    def test_t01_new_arena_medium_high_risk_session_triggers_canary_in_runtime(self) -> None:
        result = self.start_cli()
        prompt = result["recommendation"]["PROMPT"]
        self.assertIn("FAST_CANARY_REQUIRED=YES", prompt)
        self.assertIn("CANARY_EVIDENCE_PACKET_V1", prompt)
        self.assertEqual("YES", result["recommendation"]["CANARY"]["FAST_CANARY_REQUIRED"])
        # The decision is derived at runtime, not from the task text mentioning
        # FAST_CANARY.
        blind = self.start_cli(goal="Investigate why the Logistics shipment status endpoint regressed and repair it", session_id="s-blind")
        self.assertIn("FAST_CANARY_REQUIRED=YES", blind["recommendation"]["PROMPT"])

    def test_t01b_owner_goal_arena_handoff_triggers_canary(self) -> None:
        handoff_packet = owner_goal.build_arena_handoff(
            self.root,
            {"goal_id": "HERMES-LOGISTICS-01", "objective": BLIND_TEST_TASK},
            None,
            "ARENA",
            reuse=False,
        )
        self.assertEqual("YES", handoff_packet["fast_canary_required"])
        self.assertIn("FAST_CANARY_REQUIRED=YES", handoff_packet["packet_text"])
        self.assertIn("CANARY_EVIDENCE_PACKET_V1", handoff_packet["packet_text"])

    # --- T02 prompt serialization ----------------------------------------
    def test_t02_generated_prompt_serializes_full_canary_contract(self) -> None:
        prompt = self.start_cli()["recommendation"]["PROMPT"]
        for token in CANARY_TOKENS:
            self.assertIn(token, prompt)
        for token in CHECKPOINT_TOKENS:
            self.assertIn(token, prompt)
        self.assertIn("OWNER_CONTINUATION_GATE=OWNER_CONTINUATION_GATE_V1", prompt)
        self.assertIn("CANARY_CLASSIFIER=CONTROL_TOWER_OR_INDEPENDENT_VERIFIER", prompt)
        self.assertIn(BLIND_TEST_TASK, prompt)
        # The original task is preserved for continuation, not dropped.
        self.assertIn("ORIGINAL_REAL_TASK", prompt)

    # --- T03 stop boundary ------------------------------------------------
    def test_t03_canary_turn_must_stop_after_one_first_safe_probe(self) -> None:
        prompt = self.start_cli()["recommendation"]["PROMPT"]
        self.assertIn("STOP_AFTER_CANARY=YES", prompt)
        self.assertIn("Stop after that one decisive probe.", prompt)
        self.assertIn("Do not continue the original task in this turn.", prompt)
        self.assertIn("CONTINUATION_CHECKPOINT=READY", prompt)

    def test_t03b_stop_boundary_violation_is_classified_red(self) -> None:
        # Executor returned evidence but ran past the checkpoint boundary.
        evidence = canary_evidence_block(extra_lines=("SELF_ASSESSMENT=looks fine",))
        evidence = "\n".join(
            line for line in evidence.splitlines() if not line.startswith("CONTINUATION_CHECKPOINT=")
        )
        grade = classify_canary_evidence(
            parse_canary_evidence_packet(evidence),
            response_text=evidence,
        )
        self.assertEqual("RED", grade["CLASSIFICATION"])
        self.assertIn("CANARY_STOP_BOUNDARY_VIOLATION", grade["REASONS"][0])

    # --- T04 executor self-grade forbidden --------------------------------
    def test_t04_executor_self_classification_is_forbidden_and_rejected(self) -> None:
        prompt = self.start_cli()["recommendation"]["PROMPT"]
        self.assertIn("EXECUTOR_SELF_CLASSIFICATION=FORBIDDEN", prompt)
        self.assertIn("You MUST NOT emit GREEN, YELLOW, ORANGE, RED, KEEP_SESSION", prompt)
        evidence = canary_evidence_block(
            extra_lines=("SELF_CLASSIFICATION=GREEN", "SESSION_POLICY=KEEP_SESSION")
        )
        grade = classify_canary_evidence(parse_canary_evidence_packet(evidence), response_text=evidence)
        self.assertEqual("RED", grade["CLASSIFICATION"])
        self.assertTrue(
            any(reason.startswith("EXECUTOR_SELF_CLASSIFICATION_FORBIDDEN") for reason in grade["REASONS"])
        )

    def test_t04b_arena_never_authoritatively_self_emits_grade_or_policy(self) -> None:
        prompt = self.start_cli()["recommendation"]["PROMPT"]
        # The prompt must not instruct the executor to emit an authoritative
        # session grade or policy token of its own.
        for token in ("KEEP_SESSION=YES", "LIMIT_SESSION=YES", "REROLL=YES", "SESSION_GRADE=GREEN"):
            self.assertNotIn(token, prompt)
        self.assertIn("CANARY_CLASSIFIER=CONTROL_TOWER_OR_INDEPENDENT_VERIFIER", prompt)

    # --- T05 canary ingest ------------------------------------------------
    def test_t05_canary_evidence_is_ingested_into_existing_execution_ledger(self) -> None:
        binding = self.binding()
        started = self.tower().start_session(
            binding,
            task_id="TASK-CANARY-1",
            worktree="fixture-worktree",
            branch="fixture-branch",
            canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE,
            acceptance_criteria=("Return evidence only and stop.",),
            canary_directive=self.directive(),
        )
        self.assertEqual("PASS", started["status"])
        result = self.ingest_response(canary_response(binding))
        self.assertEqual("GREEN", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("KEEP_SESSION", result["canary_grade"]["SESSION_POLICY"])

        ledger = self.root / ".p2p" / "state" / "execution-ledger.jsonl"
        events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(2, len(events))
        self.assertEqual("CONTROL_TOWER_SESSION_STARTED", events[0]["event_type"])
        self.assertEqual("YES", events[0]["CANARY"]["FAST_CANARY_REQUIRED"])
        self.assertEqual(BLIND_TEST_TASK, events[0]["CANARY"]["ORIGINAL_TASK"])
        self.assertEqual("CONTROL_TOWER_RETURN_PACKET", events[1]["event_type"])
        self.assertEqual("GREEN", events[1]["CONTROL_TOWER_CANARY"]["CLASSIFICATION"])
        # No second state store is created.
        self.assertFalse((self.root / ".p2p" / "state" / "control-tower.json").exists())
        self.assertFalse((self.root / ".p2p" / "state" / "canary.json").exists())

    def test_t05b_replay_is_idempotent_and_raw_transcript_is_not_persisted(self) -> None:
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        response = "UNIQUE RAW EXECUTOR TRANSCRIPT\n" + canary_response(binding)
        first = self.tower().ingest_response(response)
        ledger = self.root / ".p2p" / "state" / "execution-ledger.jsonl"
        first_raw = ledger.read_text(encoding="utf-8")
        second = self.tower().ingest_response(response)
        self.assertTrue(first["idempotent"] is False)
        self.assertTrue(second["idempotent"])
        self.assertEqual(first_raw, ledger.read_text(encoding="utf-8"))
        self.assertNotIn("UNIQUE RAW EXECUTOR TRANSCRIPT", ledger.read_text(encoding="utf-8"))
        # A fresh tower replays the durable grade without re-grading.
        snapshot = self.tower().snapshot()
        gate = snapshot["CANARY_GATES"][0]
        self.assertEqual("GREEN", gate["CLASSIFICATION"])
        self.assertEqual("KEEP_SESSION", gate["SESSION_POLICY"])
        self.assertEqual("CONTROL_TOWER_DURABLE_STATE", gate["ORIGINAL_TASK_SOURCE"])

    # --- T06 external grading --------------------------------------------
    def test_t06_external_grade_routing_table_is_deterministic(self) -> None:
        cases = {
            "GREEN": canary_evidence_block(),
            "YELLOW": canary_evidence_block(
                check_result="exit=1; focused probe failed",
                errors="one command error",
                recovery="re-ran with corrected path",
            ),
            "ORANGE": canary_evidence_block(check_result="UNKNOWN"),
            "RED": canary_evidence_block(durable_mutation="YES"),
        }
        for expected, evidence in cases.items():
            grade = classify_canary_evidence(parse_canary_evidence_packet(evidence), response_text=evidence)
            self.assertEqual(expected, grade["CLASSIFICATION"], evidence)
        expected_policies = {
            "GREEN": "KEEP_SESSION",
            "YELLOW": "LIMIT_SESSION",
            "ORANGE": "ADVISORY_OR_LOW_RISK_ONLY",
            "RED": "REROLL_OR_SWITCH_EXECUTOR",
        }
        for classification, policy in expected_policies.items():
            self.assertEqual(policy, handoff.CANARY_SESSION_POLICIES[classification])

    def test_t06b_unverified_is_not_implicit_green(self) -> None:
        incomplete = canary_evidence_block()
        incomplete = "\n".join(
            line for line in incomplete.splitlines() if not line.startswith("DECISIVE_CHECK=")
        )
        grade = classify_canary_evidence(parse_canary_evidence_packet(incomplete), response_text=incomplete)
        self.assertEqual("UNVERIFIED", grade["CLASSIFICATION"])
        self.assertEqual("NO_DEFAULT_CONTINUATION", grade["SESSION_POLICY"])

    # --- T07 Owner continuation gate --------------------------------------
    def test_t07_owner_continuation_before_external_green_is_blocked(self) -> None:
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        self.ingest_response(canary_response(binding))
        with self.assertRaises(BindingError) as ctx:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="NO")
        self.assertIn("CANARY_OWNER_CONTINUATION_REQUIRED", str(ctx.exception))

    def test_t07b_owner_continuation_without_green_is_blocked(self) -> None:
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        red = canary_response(binding)
        red = red.replace("DURABLE_MUTATION_CREATED=NO", "DURABLE_MUTATION_CREATED=YES")
        self.ingest_response(red)
        with self.assertRaises(BindingError) as ctx:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertIn("CANARY_OWNER_CONTINUATION_BLOCKED:RED", str(ctx.exception))

    # --- T08 GREEN + Owner continuation resumes original task -------------
    def test_t08_green_plus_owner_continuation_resumes_original_task_same_session(self) -> None:
        binding = self.binding()
        self.tower().start_session(
            binding,
            task_id="TASK-CANARY-1",
            worktree="fixture-worktree",
            branch="fixture-branch",
            canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE,
            acceptance_criteria=("Return evidence only and stop.",),
            canary_directive=self.directive(),
        )
        self.ingest_response(canary_response(binding))
        result = self.tower().continue_canary_session(
            binding.session_id,
            owner_continuation="YES",
            owner_reply="Tiếp tục công việc",
        )
        recommendation = result["recommendation"]
        self.assertEqual("PASS", result["status"])
        self.assertFalse(result["idempotent"])
        # Same Arena session, restored from durable state.
        self.assertEqual(binding.session_id, recommendation["SESSION_ID"])
        self.assertEqual("ARENA", recommendation["HOST"])
        self.assertEqual("CONTROL_TOWER_DURABLE_STATE", recommendation["ORIGINAL_TASK_SOURCE"])
        self.assertEqual("RESUME_ORIGINAL_TASK_IN_SAME_SESSION", recommendation["CONTINUATION_MODE"])
        self.assertEqual("NO", recommendation["CANARY_REPEAT"])
        self.assertIn(BLIND_TEST_TASK, recommendation["PROMPT"])
        # Continuation does not repeat the canary.
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", recommendation["PROMPT"])
        self.assertIn("CONTROL_TOWER_EXECUTION_PROMPT", recommendation["PROMPT"])

        # Idempotent replay of the Owner decision.
        again = self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertTrue(again["idempotent"])
        self.assertEqual(recommendation["PROMPT"], again["recommendation"]["PROMPT"])

    def test_t08b_fallback_owner_reply_is_accepted(self) -> None:
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        self.ingest_response(canary_response(binding))
        result = self.tower().continue_canary_session(
            binding.session_id,
            owner_continuation="NO",
            owner_reply="Tiếp tục công việc",
        )
        self.assertEqual("PASS", result["status"])
        self.assertIn(BLIND_TEST_TASK, result["recommendation"]["PROMPT"])

    # --- T09 same-session no repeat ---------------------------------------
    def test_t09_same_green_session_same_goal_does_not_recanary(self) -> None:
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        self.ingest_response(canary_response(binding))
        self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        # Re-registering the same session returns the stored continuation
        # recommendation instead of a fresh canary.
        again = self.tower().start_session(binding, task_prompt=BLIND_TEST_TASK)
        self.assertTrue(again["idempotent"])
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", again["recommendation"]["PROMPT"])
        self.assertEqual("NO", again["recommendation"]["CANARY_REPEAT"])
        self.assertEqual(
            "ESTABLISHED",
            self.tower().session_quality(binding.goal_id, binding.session_id),
        )

    # --- T10 new session re-canaries --------------------------------------
    def test_t10_new_arena_session_recanaries(self) -> None:
        binding = self.binding("session-arena-canary-0001")
        self.tower().start_session(binding, canary_directive=self.directive("session-arena-canary-0001"))
        self.ingest_response(canary_response(binding))
        self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")

        fresh = self.binding("session-arena-canary-0002")
        result = self.tower().start_session(
            fresh,
            canary_directive=self.directive("session-arena-canary-0002"),
        )
        self.assertFalse(result["idempotent"])
        self.assertIn("FAST_CANARY_REQUIRED=YES", result["recommendation"]["PROMPT"])
        self.assertEqual(
            "UNKNOWN",
            self.tower().session_quality(fresh.goal_id, fresh.session_id),
        )

    # --- T11 low-risk bypass ----------------------------------------------
    def test_t11_low_risk_mechanical_arena_task_bypasses_canary(self) -> None:
        decision = canary_requirement("ARENA", LOW_RISK_TASK)
        self.assertEqual("NO", decision["FAST_CANARY_REQUIRED"])
        self.assertEqual("LOW_RISK_MECHANICAL_ARENA_TASK", decision["REASON"])
        self.assertEqual("LOW", decision["RISK_CLASS"])
        result = self.start_cli(goal=LOW_RISK_TASK, session_id="low-risk-1")
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", result["recommendation"]["PROMPT"])
        self.assertNotIn("CANARY_EVIDENCE_PACKET_V1", result["recommendation"]["PROMPT"])

    # --- T12 non-Arena bypass ---------------------------------------------
    def test_t12_non_arena_executor_bypasses_arena_canary(self) -> None:
        decision = canary_requirement("CODEX", BLIND_TEST_TASK)
        self.assertEqual("NO", decision["FAST_CANARY_REQUIRED"])
        self.assertEqual("NON_ARENA_EXECUTOR", decision["REASON"])
        result = self.start_cli(host="CODEX", session_id="codex-1")
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", result["recommendation"]["PROMPT"])
        self.assertNotIn("CANARY_EVIDENCE_PACKET_V1", result["recommendation"]["PROMPT"])

    # --- T13 prompt budget fail closed ------------------------------------
    def test_t13_prompt_budget_fails_closed_instead_of_truncating_canary(self) -> None:
        binding = self.binding()
        directive = self.directive()
        with self.assertRaises(BindingError) as ctx:
            build_execution_prompt(
                binding,
                BLIND_TEST_TASK,
                canary_directive=directive,
                max_prompt_chars=2000,
            )
        self.assertIn("CONTROL_TOWER_CANARY_CONTEXT_DID_NOT_FIT", str(ctx.exception))
        # Required canary context is never silently shortened.
        prompt = build_execution_prompt(
            binding,
            BLIND_TEST_TASK,
            canary_directive=directive,
            max_prompt_chars=control_tower.PROMPT_GUARD_CHARS,
        )
        for token in CANARY_TOKENS:
            self.assertIn(token, prompt)

    def test_t13b_oversized_task_fails_closed_in_control_tower_runtime(self) -> None:
        oversized = "Repair the runtime gate " + ("x" * 11000)
        with self.assertRaises(BindingError) as ctx:
            control_tower._contextual_task_and_expectations_for_session(
                self.root,
                self.binding(),
                oversized,
                law_receipt=control_tower._establish_control_tower_law_context(self.root),
            )
        self.assertIn("CONTROL_TOWER_CANARY_CONTEXT_DID_NOT_FIT", str(ctx.exception))

    # --- T14 live regression shape ----------------------------------------
    def test_t14_live_blind_test_regression_is_classified_red_and_blocked(self) -> None:
        """The 2026-09-24 blind test: broad investigation, terminal conclusion.

        The session never returned CANARY_EVIDENCE_PACKET_V1 and never stopped at
        CONTINUATION_CHECKPOINT. Control Tower must classify that externally and
        must not unlock full execution.
        """

        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        blind = canary_response(binding, evidence_block=None, session_state="COMPLETED")
        blind = blind.replace(canary_evidence_block(), "")
        result = self.ingest_response(blind)
        self.assertEqual("RED", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("REROLL_OR_SWITCH_EXECUTOR", result["canary_grade"]["SESSION_POLICY"])
        self.assertIn(
            "CANARY_EVIDENCE_PACKET_MISSING_AFTER_TERMINAL_CONCLUSION",
            result["canary_grade"]["REASONS"],
        )
        snapshot = result["snapshot"]
        self.assertEqual("REROLL_OR_SWITCH_EXECUTOR", snapshot["NEXT_SAFE_ACTION"]["ACTION"])
        self.assertEqual("REROLL_OR_SWITCH_EXECUTOR", snapshot["CANARY_GATES"][0]["SESSION_POLICY"])
        with self.assertRaises(BindingError) as ctx:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertIn("CANARY_OWNER_CONTINUATION_BLOCKED:RED", str(ctx.exception))

    def test_t14b_non_terminal_missing_evidence_is_unverified_not_green(self) -> None:
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        response = canary_response(binding, evidence_block=None)
        response = response.replace(canary_evidence_block(), "")
        result = self.ingest_response(response)
        self.assertEqual("UNVERIFIED", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("NO_DEFAULT_CONTINUATION", result["canary_grade"]["SESSION_POLICY"])
        self.assertEqual("NO_DEFAULT_CONTINUATION", result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])

    # --- T15 durable mutation boundary ------------------------------------
    def test_t15_canary_forbids_durable_mutation_and_flags_violation(self) -> None:
        prompt = self.start_cli()["recommendation"]["PROMPT"]
        self.assertIn("CANARY_DURABLE_MUTATION_ALLOWED=NO", prompt)
        self.assertIn("Do not create durable commits, branches, PRs, remote writes", prompt)
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        mutated = canary_response(binding).replace("DURABLE_MUTATION_CREATED=NO", "DURABLE_MUTATION_CREATED=YES")
        result = self.ingest_response(mutated)
        self.assertEqual("RED", result["canary_grade"]["CLASSIFICATION"])
        self.assertIn("CANARY_DURABLE_MUTATION_BOUNDARY_VIOLATED", result["canary_grade"]["REASONS"])

    # --- T17 YELLOW bounded continuation ----------------------------------
    def test_t17_yellow_allows_only_bounded_limited_continuation(self) -> None:
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        yellow = canary_response(
            binding,
            evidence_block=canary_evidence_block(
                check_result="exit=1; focused probe failed on first attempt",
                errors="one command error",
                recovery="re-ran with corrected path and passed",
            ),
        )
        result = self.ingest_response(yellow)
        self.assertEqual("YELLOW", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("LIMIT_SESSION", result["canary_grade"]["SESSION_POLICY"])
        self.assertEqual(
            "CONTINUE_LIMITED_WITH_DECLARED_VERIFICATION_BOUND",
            result["canary_grade"]["CONTINUATION_RECOMMENDATION"],
        )
        self.assertEqual("LIMIT_SESSION", result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])
        with self.assertRaises(BindingError) as ctx:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertIn("CANARY_OWNER_CONTINUATION_BLOCKED:YELLOW", str(ctx.exception))

    # --- T18 ORANGE advisory only -----------------------------------------
    def test_t18_orange_is_advisory_or_low_risk_only(self) -> None:
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        orange = canary_response(
            binding,
            evidence_block=canary_evidence_block(check_result="UNKNOWN"),
        )
        result = self.ingest_response(orange)
        self.assertEqual("ORANGE", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("ADVISORY_OR_LOW_RISK_ONLY", result["canary_grade"]["SESSION_POLICY"])
        self.assertEqual("ADVISORY_OR_LOW_RISK_ONLY", result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])
        with self.assertRaises(BindingError) as ctx:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertIn("CANARY_OWNER_CONTINUATION_BLOCKED:ORANGE", str(ctx.exception))

    # --- T19 RED reroll ---------------------------------------------------
    def test_t19_red_rerolls_without_keep_working(self) -> None:
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        red = canary_response(
            binding,
            evidence_block=canary_evidence_block(
                check_result="exit=1; decisive probe failed",
                errors="command failed",
                recovery="NONE",
            ),
        )
        result = self.ingest_response(red)
        self.assertEqual("RED", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("REROLL_OR_SWITCH_EXECUTOR", result["canary_grade"]["SESSION_POLICY"])
        self.assertIn("CANARY_CHECK_FAILED_WITHOUT_RECOVERY", result["canary_grade"]["REASONS"])

    # --- T20 existing context preserved + OE guard ------------------------
    def test_t20_existing_law_oe_and_experience_context_survive_canary(self) -> None:
        result = self.start_cli(goal="GitHub merge exact head for the Arena canary runtime repair")
        prompt = result["recommendation"]["PROMPT"]
        self.assertIn(control_tower.CONTEXT_MARKER, prompt)
        self.assertIn("P2P_LAW_PREFLIGHT=", prompt)
        self.assertIn("OE_GATE=", prompt)
        self.assertIn("CONTROL_TOWER_SELF_LAW_RECEIPT=", prompt)
        self.assertIn("SUPREME_LAW_CAPSULE:", prompt)
        self.assertIn("EXPERIENCE=", prompt)
        self.assertLessEqual(len(prompt), control_tower.PROMPT_GUARD_CHARS)

    def test_t20b_no_second_control_tower_or_parallel_state_store(self) -> None:
        source = (SYSTEM_ROOT / "p2p_capabilities" / "control_tower_handoff.py").read_text(encoding="utf-8")
        for forbidden in ("class Router", "class TaskRegistry", "class StateDB", "class Scheduler"):
            self.assertNotIn(forbidden, source)
        self.assertIn("CONTROL_TOWER_LEDGER_RELATIVE_PATH", source)
        binding = self.binding()
        self.tower().start_session(binding, canary_directive=self.directive())
        state_dir = self.root / ".p2p" / "state"
        self.assertEqual(
            ["execution-ledger.jsonl"],
            sorted(path.name for path in state_dir.iterdir()),
        )

    # --- Logistics PR112 regression shape ---------------------------------
    def test_logistics_pr112_canary_regression_stops_at_first_safe_boundary(self) -> None:
        goal = (
            "Logistics PR112: ship the read-only shipment-status endpoint and wire "
            "the Telegram route handler with durable state changes"
        )
        handoff_packet = owner_goal.build_arena_handoff(
            self.root,
            {"goal_id": "HERMES-LOGISTICS-01", "objective": goal},
            None,
            "ARENA",
            reuse=False,
        )
        self.assertEqual("YES", handoff_packet["fast_canary_required"])
        packet_text = handoff_packet["packet_text"]
        for token in CANARY_TOKENS:
            self.assertIn(token, packet_text)
        self.assertIn(goal, packet_text)

        binding = SessionBinding(
            session_id="session-arena-logistics-pr112",
            host="ARENA",
            goal_id="HERMES-LOGISTICS-01",
            goal=goal,
        )
        directive = CanaryDirective(
            host="ARENA",
            session_id=binding.session_id,
            goal_id="HERMES-LOGISTICS-01",
            goal=goal,
            original_task=goal,
            risk_class=classify_task_risk_class(goal),
        )
        self.tower().start_session(
            binding,
            task_id="HERMES-LOGISTICS-01-T1",
            worktree="fixture-worktree",
            branch="arena/hermes-logistics-01",
            canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE,
            canary_directive=directive,
        )
        evidence = canary_evidence_block(
            current_state="arena/hermes-logistics-01 @ 6adfa3b85658e4c0670ccfc22eb22e19e6395879",
            facts="read-only endpoint missing; route handler has no status branch",
            decisive_check="grep -n shipment_status deployments/hermes-dockhosting/plugins/logistics/__init__.py",
            check_result="exit=0; 0 matches",
        )
        result = self.ingest_response(
            canary_response(binding, evidence_block=evidence, base_sha=BASE_SHA, base_tree=BASE_TREE)
        )
        self.assertEqual("GREEN", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("UNKNOWN", result["canary_grade"]["MODEL_IDENTITY"])
        # The first safe probe is evidence only; the real PR work still waits.
        self.assertEqual(
            "WAIT_FOR_OWNER_CONTINUATION",
            result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"],
        )
        with self.assertRaises(BindingError):
            self.tower().continue_canary_session(binding.session_id, owner_continuation="NO")
        resumed = self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertEqual("NO", resumed["recommendation"]["CANARY_REPEAT"])
        self.assertIn(goal, resumed["recommendation"]["PROMPT"])
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", resumed["recommendation"]["PROMPT"])


if __name__ == "__main__":
    unittest.main()
