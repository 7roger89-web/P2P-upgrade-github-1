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

Supervisor review 5306294879 showed that the first iteration's canary helper
silently appended a full CONTROL_TOWER_RETURN_PACKET to every canary response,
hiding that the canonical evidence-only return was not ingestible. Every canary
turn below therefore uses ONLY the canonical executor-visible shape:

    CANARY_EVIDENCE_PACKET_V1 + neutral checkpoint metadata, then STOP.

A CONTROL_TOWER_RETURN_PACKET appears only where the scenario is explicitly the
live-regression shape (an executor that ran past the canary boundary) or the
resumed ORIGINAL task after external GREEN + explicit Owner continuation.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
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
    ControlTowerHandoffError,
    ProjectionError,
    SessionBinding,
    build_execution_prompt,
    canary_requirement,
    classify_canary_evidence,
    create_return_packet,
    parse_canary_evidence_packet,
)
from p2p_capabilities.evidence import EvidenceClaim  # noqa: E402
from p2p_capabilities.task_state import (  # noqa: E402
    PlanIdentity,
    TaskPlan,
    TaskStateStore,
    complete_task,
    request_owner_decision,
)

BASE_SHA = "a" * 40
BASE_TREE = "b" * 40
EXPECTED_CANONICAL_LAW_SHA = hashlib.sha256(
    (REPO_ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md").read_bytes()
).hexdigest()
LEDGER_RELATIVE = Path(".p2p") / "state" / "execution-ledger.jsonl"

# The real bounded task shape observed in the 2026-09-24 blind test.
BLIND_TEST_TASK = (
    "Repair the Control Tower runtime so a new medium/high-risk Arena session "
    "stops at the FAST_CANARY boundary, mutating runtime prompt generation, "
    "ledger events and gates"
)
# Looks mechanical, but nothing explicitly declares it LOW_RISK_MECHANICAL.
MECHANICAL_LOOKING_TASK = "Fix a typo in the README changelog label"

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
CANONICAL_EVIDENCE_KEYS = (
    "P2P_LAW_SOURCE",
    "LAW_CHECK",
    "EXPERIENCE_CHECK",
    "CURRENT_STATE",
    "FACTS",
    "DECISIVE_CHECK",
    "CHECK_RESULT",
    "ERRORS_ENCOUNTERED",
    "RECOVERY_ACTIONS",
    "DURABLE_MUTATION_CREATED",
    "MODEL_IDENTITY",
)
# Any of these in a first-turn canary prompt is a second, contradictory return
# contract (Supervisor review 5306294879, BLOCKER 2).
TERMINAL_RETURN_CONTRACT_MARKERS = (
    "CONTROL_TOWER_RETURN_PACKET_BEGIN",
    "CONTROL_TOWER_RETURN_PACKET_END",
    "Finish with one structured CONTROL_TOWER_RETURN_PACKET",
    "Return a truthful terminal packet",
    "Every terminal response must declare UPLOAD_REQUIRED",
)
FIRST_TURN_RETURN_CONTRACT_LINE = "FIRST_TURN_RETURN_CONTRACT=CANARY_EVIDENCE_PACKET_V1_THEN_STOP"
CANARY_FIRST_TURN_MODE_LINE = "EXECUTION_MODE=FAST_CANARY_FIRST_SAFE_SLICE_THEN_STOP"
CANARY_FIRST_TURN_FLOW_LINE = "FIRST_TURN_FLOW=FIRST_SAFE_REAL_TASK_SLICE -> CANARY_EVIDENCE_PACKET_V1 -> STOP"
RESUMED_TASK_BEGIN_PREFIX = "RESUMED_TASK_CONTRACT"
RESUMED_TASK_END = "END_RESUMED_TASK_CONTRACT"


def canary_evidence_block(
    *,
    law_source: str = "7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md",
    current_state: str = "arena/canary @ 3cb8049921805dbd963a091d9b37ae06a3a9fd61",
    facts: str = "runtime has no FAST_CANARY token; only structural policy tests exist",
    decisive_check: str = "grep -c FAST_CANARY scripts/p2p_control_tower.py",
    check_result: str = "exit=0; 0 matches in runtime",
    errors: str = "NONE",
    recovery: str = "NONE",
    durable_mutation: str = "NO",
    model_identity: str = "UNKNOWN",
    extra_lines: tuple[str, ...] = (),
    law_check: str | None = None,
    experience_check: str | None = None,
) -> str:
    """Return exactly the canonical CANARY_EVIDENCE_PACKET_V1 block."""

    lines = [
        "CANARY_EVIDENCE_PACKET_V1",
        f"P2P_LAW_SOURCE={law_source}",
        *([law_check if law_check is not None else (
            f"LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256={EXPECTED_CANONICAL_LAW_SHA}"
        )] if (law_check is None or law_check) else []),
        *([experience_check if experience_check is not None else "EXPERIENCE_CHECK=UNAVAILABLE"]
          if (experience_check is None or experience_check) else []),
        f"CURRENT_STATE={current_state}",
        f"FACTS={facts}",
        f"DECISIVE_CHECK={decisive_check}",
        f"CHECK_RESULT={check_result}",
        f"ERRORS_ENCOUNTERED={errors}",
        f"RECOVERY_ACTIONS={recovery}",
        f"DURABLE_MUTATION_CREATED={durable_mutation}",
        f"MODEL_IDENTITY={model_identity}",
        *extra_lines,
    ]
    return "\n".join(lines)


def canary_evidence_response(
    *,
    preface: str = "",
    checkpoint: tuple[str, ...] = CHECKPOINT_TOKENS,
    **evidence: object,
) -> str:
    """Return the canonical executor-visible canary turn and nothing else.

    CANARY_EVIDENCE_PACKET_V1, a blank line, then the neutral checkpoint
    metadata. No CONTROL_TOWER_RETURN_PACKET is ever added here.
    """

    block = canary_evidence_block(**evidence)  # type: ignore[arg-type]
    return f"{preface}{block}\n\n" + "\n".join(checkpoint) + "\n"


def terminal_return_packet(binding: SessionBinding, *, session_state: str = "COMPLETED") -> str:
    """A conforming full terminal packet for the same binding."""

    packet = create_return_packet(
        binding,
        session_state=session_state,
        canonical_base_sha=BASE_SHA,
        canonical_base_tree=BASE_TREE,
        canonical_relation="CURRENT",
        worktree="fixture-worktree",
        branch="fixture-branch",
        changes=("scripts/p2p_control_tower.py",),
        test_results={"focused": "PASS"},
        evidence=("focused-tests",),
        candidate_or_checkpoint_sha="c" * 40,
        blockers=(),
        next_recommended_action="Request independent exact-head review.",
        law_check={
            "status": "PASS",
            "source": "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md",
            "source_sha256": EXPECTED_CANONICAL_LAW_SHA,
        },
        experience_check={
            "decision": "UNAVAILABLE",
            "ids": [],
            "reason": "fixture has no active experience expectation",
        },
        learning_reconciliation={
            "type": "NONE",
            "reason": "routine fixture success",
        },
    )
    return packet.to_marked_text()


def split_first_turn_packet(text: str) -> tuple[list[str], list[str]]:
    """Split a /goal Arena packet into ACTIVE (this turn) and DEFERRED lines."""

    lines = text.splitlines()
    begins = [index for index, line in enumerate(lines) if line.startswith(RESUMED_TASK_BEGIN_PREFIX)]
    ends = [index for index, line in enumerate(lines) if line.strip() == RESUMED_TASK_END]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        raise AssertionError(
            f"expected exactly one deferred RESUMED_TASK_CONTRACT section; begins={begins} ends={ends}"
        )
    deferred = lines[begins[0] : ends[0] + 1]
    active = lines[: begins[0]] + lines[ends[0] + 1 :]
    return active, deferred


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
        )

    def start_canary(self, session_id: str = "session-arena-canary-0001") -> SessionBinding:
        binding = self.binding(session_id)
        self.tower().start_session(
            binding,
            task_id="TASK-CANARY-1",
            worktree="fixture-worktree",
            branch="fixture-branch",
            canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE,
            expected_law_sha=EXPECTED_CANONICAL_LAW_SHA,
            expected_experience_ids=(),
            canary_directive=self.directive(session_id),
        )
        return binding

    def start_expected_receipt_canary(
        self,
        session_id: str,
        expected_id: str = "shared-exp-parser-expected",
    ) -> tuple[SessionBinding, str]:
        binding = self.binding(session_id)
        self.tower().start_session(
            binding,
            expected_law_sha=EXPECTED_CANONICAL_LAW_SHA,
            expected_experience_ids=(expected_id,),
            canary_directive=self.directive(session_id),
        )
        return binding, expected_id

    def assert_receipt_response_fails_closed(
        self,
        session_id: str,
        response: str,
        expected_reason: str,
    ) -> None:
        binding, _ = self.start_expected_receipt_canary(session_id)
        result = self.ingest_canary(binding, response)
        self.assertNotEqual("GREEN", result["canary_grade"]["CLASSIFICATION"])
        self.assertTrue(
            any(expected_reason in reason for reason in result["canary_grade"]["REASONS"]),
            result["canary_grade"],
        )

    def _run_cli(self, args: list[str], *, expect: int = 0, global_args: tuple[str, ...] = ()) -> str:
        buffer = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(errors):
            code = control_tower.main(["--root", str(self.root), *global_args, *args])
        self.assertEqual(expect, code, buffer.getvalue() + errors.getvalue())
        return buffer.getvalue() + errors.getvalue()

    def start_cli(
        self,
        *,
        host: str = "ARENA",
        goal: str = BLIND_TEST_TASK,
        goal_id: str = "P2P-CT01-CANARY",
        session_id: str = "s1",
        extra: tuple[str, ...] = (),
    ) -> dict:
        output = self._run_cli(
            [
                "start",
                "--host",
                host,
                "--goal-id",
                goal_id,
                "--task-id",
                "TASK-CANARY-1",
                "--session-id",
                session_id,
                "--goal",
                goal,
                *extra,
                "--json",
            ]
        )
        return json.loads(output)

    def ingest_cli(self, response: str, *, session_id: str | None = None) -> dict:
        response_path = self.root / "response.txt"
        response_path.write_text(response, encoding="utf-8")
        args = ["ingest", "--response-file", str(response_path)]
        if session_id is not None:
            args.extend(["--session-id", session_id])
        observed_base = ("--current-canonical-base-sha", BASE_SHA, "--current-canonical-base-tree", BASE_TREE)
        return json.loads(self._run_cli([*args, "--json"], global_args=observed_base))

    def ingest_canary(self, binding: SessionBinding, response: str | None = None) -> dict:
        return self.tower().ingest_response(
            response if response is not None else canary_evidence_response(),
            session_id=binding.session_id,
        )

    def ledger_events(self) -> list[dict]:
        ledger = self.root / LEDGER_RELATIVE
        return [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]

    # --- T01 runtime trigger ---------------------------------------------
    def test_t01_new_arena_medium_high_risk_session_triggers_canary_in_runtime(self) -> None:
        result = self.start_cli()
        prompt = result["recommendation"]["PROMPT"]
        self.assertIn("FAST_CANARY_REQUIRED=YES", prompt)
        self.assertIn("CANARY_EVIDENCE_PACKET_V1", prompt)
        self.assertEqual("YES", result["recommendation"]["CANARY"]["FAST_CANARY_REQUIRED"])
        # The decision is derived at runtime, not from the task text mentioning
        # FAST_CANARY.
        blind = self.start_cli(
            goal="Investigate why the Logistics shipment status endpoint regressed and repair it",
            session_id="s-blind",
        )
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
        for key in CANONICAL_EVIDENCE_KEYS:
            self.assertIn(f"{key}=", prompt)
        self.assertIn("OWNER_CONTINUATION_GATE=OWNER_CONTINUATION_GATE_V1", prompt)
        self.assertIn("CANARY_CLASSIFIER=CONTROL_TOWER_OR_INDEPENDENT_VERIFIER", prompt)
        self.assertIn(BLIND_TEST_TASK, prompt)
        # The original task is preserved for continuation, not dropped.
        self.assertIn("ORIGINAL_REAL_TASK", prompt)
        self.assertIn("LAW_CHECK=PASS | SOURCE=<actual source>", prompt)
        self.assertIn("INLINE_SUPREME_LAW_CAPSULE allowed", prompt)
        self.assertIn("Inline capsule => PASS with that canonical SHA256", prompt)
        self.assertIn("EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=<experience_id,...>", prompt)
        self.assertIn("EXPERIENCE_CHECK=NO_MATCH", prompt)
        self.assertIn("EXPERIENCE_CHECK=UNAVAILABLE", prompt)

    def test_t02_inline_capsule_actor_receipt_can_grade_green_with_canonical_provenance_sha(self) -> None:
        prompt = self.start_cli(session_id="inline-law-fallback")["recommendation"]["PROMPT"]
        self.assertIn("P2P_LAW_SOURCE=<actual source; INLINE_SUPREME_LAW_CAPSULE allowed>", prompt)
        self.assertIn(
            "SOURCE_SHA256=<canonical SHA256 from CONTROL_TOWER_SELF_LAW_RECEIPT>",
            prompt,
        )

        binding = self.start_canary("inline-law-fallback-ingest")
        response = canary_evidence_response(
            law_source="INLINE_SUPREME_LAW_CAPSULE",
            law_check=(
                "LAW_CHECK=PASS | SOURCE=INLINE_SUPREME_LAW_CAPSULE | SOURCE_SHA256="
                + EXPECTED_CANONICAL_LAW_SHA
            ),
            check_result="PASS",
            errors="NONE",
            recovery="NONE",
        )
        result = self.ingest_canary(binding, response)
        self.assertEqual("GREEN", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual([], result["snapshot"]["ACTIVE_EXECUTION"][0]["ACTOR_RECEIPT_BLOCKERS"])

    def test_t02b_arena_generated_prompt_title_and_recommendation_metadata_match(self) -> None:
        result = self.start_cli(session_id="title-proof")
        recommendation = result["recommendation"]
        prompt = recommendation["PROMPT"]
        lines = prompt.splitlines()
        title = next(line for line in lines if line.strip())
        self.assertEqual(title, lines[0])
        self.assertEqual(recommendation["CHAT_TITLE"], title)
        self.assertEqual(recommendation["CHAT_NAME"], title)
        self.assertEqual("GỬI CHO: ARENA AI", lines[1])
        self.assertEqual("PROJECT=P2P-CT01-CANARY", lines[2])
        self.assertEqual("CHAT_MODE=NEW_CHAT", lines[3])
        self.assertEqual(f"CHAT_TITLE={title}", lines[4])
        self.assertEqual(f"CHAT_NAME={title}", lines[5])
        self.assertEqual("NO_FORMAL_PLAN", lines[6].removeprefix("PLAN_REFERENCE="))
        self.assertEqual("NONE_RECORDED", lines[7].removeprefix("ALREADY_COMPLETED="))
        self.assertIn("EXECUTION_PROGRESS=NONE_RECORDED", lines[8])
        self.assertEqual("BLOCKER_OR_OWNER_GATE=NONE_RECORDED", lines[9])
        self.assertTrue(lines[10].startswith("NEXT_BOUNDED_STEP="))
        self.assertNotIn("CONTROL_TOWER_EXECUTION_PROMPT:", title)
        self.assertNotIn("DESTINATION=", title)
        self.assertFalse(prompt.startswith("GỬI CHO:"))

        codex = self.start_cli(host="CODEX", session_id="codex-title")["recommendation"]
        self.assertTrue(codex["PROMPT"].splitlines()[0].startswith("CONTROL_TOWER_EXECUTION_PROMPT:"))
        self.assertNotIn("CHAT_TITLE", codex)
        self.assertEqual("CODEX — P2P-CT01-CANARY — " + BLIND_TEST_TASK, codex["CHAT_NAME"])

        # Digest captured after the shared terminal-contract repair in Issue #272.
        # Future Arena-only routing/checkpoint changes must not alter these bytes.
        non_arena = SessionBinding(
            session_id="non-arena-byte-stable",
            host="CODEX",
            goal_id="WORKSTREAM-42",
            goal="Implement deterministic checkpoint routing",
        )
        non_arena_prompt = build_execution_prompt(non_arena, "Perform one focused serialization repair.")
        self.assertEqual(
            "2c4eb0dfc62a8c60439c8f70ca8f928524f8c26fb3c8c6604ca413f3c52db505",
            hashlib.sha256(non_arena_prompt.encode("utf-8")).hexdigest(),
        )

        unknown_identity = SessionBinding(
            session_id="unknown-project-identity",
            host="ARENA",
            goal_id="UNKNOWN",
            goal="Record an honest unknown identity checkpoint",
        )
        unknown_prompt = build_execution_prompt(unknown_identity, "Do not invent an identity or progress.")
        self.assertIn("PROJECT=NONE_RECORDED", unknown_prompt)
        self.assertIn("TASK_ID=NONE_RECORDED; EXECUTION_PROGRESS=NONE_RECORDED", unknown_prompt)

    def test_t02c_available_task_plan_drives_project_and_fresh_checkpoint(self) -> None:
        now = "2026-09-30T00:00:00+00:00"
        goal_id = "goal-route-repair"
        plan = TaskPlan.from_goal(
            {
                "goal_id": goal_id,
                "scope": ["route prompts from existing task state"],
                "out_of_scope": ["new plan storage"],
            },
            [
                {
                    "task_id": "foundation",
                    "title": "Record verified task state",
                    "purpose": "Prove the existing state can be resumed.",
                    "scope": ["task-state fixture"],
                    "acceptance_requirements": ["Current task is bound to the recorded plan."],
                    "required_evidence": ["foundation-proof"],
                },
                {
                    "task_id": "route-prompt",
                    "title": "Serialize Arena routing metadata",
                    "purpose": "Emit the routing and current checkpoint from durable task state.",
                    "dependencies": ["foundation"],
                    "scope": ["Control Tower prompt"],
                    "acceptance_requirements": ["The generated prompt reflects current TaskRecord state."],
                    "required_evidence": ["route-prompt-proof"],
                },
            ],
            now=now,
            plan_identity=PlanIdentity(
                repository="acme/queue-service",
                workstream="release-readiness",
                subject="Prompt routing contract",
                pr="273",
            ),
        )
        plan = plan.refresh_ready(now="2026-09-30T00:01:00+00:00")
        plan = plan.transition("foundation", "ACTIVE", now="2026-09-30T00:02:00+00:00")
        evidence = EvidenceClaim(
            claim="The prerequisite task completed with current evidence.",
            required_evidence=("foundation-proof",),
            actual_evidence=(
                {
                    "source": "tests/test_p2p_arena_canary_runtime.py",
                    "evidence_ref": "foundation-proof",
                    "origin": "RUNTIME_EVIDENCE",
                    "observed_at": now,
                    "freshness": "CURRENT",
                    "scope": ["task-state fixture"],
                    "source_binding": "focused-test",
                    "fingerprint": "a" * 64,
                },
            ),
            status="VERIFIED",
        )
        plan = complete_task(
            plan,
            "foundation",
            [evidence],
            {"verified": "yes"},
            now="2026-09-30T00:03:00+00:00",
        ).refresh_ready(now="2026-09-30T00:04:00+00:00")
        TaskStateStore(self.root).initialize(plan, at="2026-09-30T00:04:00+00:00")

        recommendation = self.tower().recommend_next_session(
            "ARENA",
            session_id="plan-routing-proof",
        )["recommendation"]
        prompt = recommendation["PROMPT"]
        lines = prompt.splitlines()
        self.assertTrue(lines[0].startswith("acme/queue service / release readiness —"), lines[0])
        self.assertEqual(recommendation["CHAT_TITLE"], lines[0])
        self.assertEqual("acme/queue-service / release-readiness", lines[2].removeprefix("PROJECT="))
        self.assertIn("Prompt routing contract", lines[6])
        self.assertIn("plan_hash=", lines[6])
        self.assertEqual("foundation", lines[7].removeprefix("ALREADY_COMPLETED="))
        self.assertIn("TASK_ID=route-prompt; STATUS=READY", lines[8])
        self.assertEqual("BLOCKER_OR_OWNER_GATE=NONE_RECORDED", lines[9])
        self.assertIn("current TaskRecord state.", lines[10])
        self.assertNotIn("PROJECT=P2P", lines[2])

    def test_t02d_pending_task_owner_gate_is_serialized_from_task_state(self) -> None:
        now = "2026-09-30T00:00:00+00:00"
        goal_id = "goal-owner-gate"
        plan = TaskPlan.from_goal(
            {"goal_id": goal_id, "scope": ["WORKSTREAM:owner-gate-routing"]},
            [
                {
                    "task_id": "owner-task",
                    "title": "Wait for the recorded Owner decision",
                    "purpose": "Serialize the current Owner gate without bypassing it.",
                    "scope": ["Control Tower prompt"],
                    "acceptance_requirements": ["The Owner decision remains pending."],
                    "required_evidence": ["owner-gate-proof"],
                }
            ],
            now=now,
        ).refresh_ready(now="2026-09-30T00:01:00+00:00")
        plan = request_owner_decision(
            plan,
            "owner-task",
            question="May the task resume?",
            options=("Continue", "Stop"),
            now="2026-09-30T00:02:00+00:00",
        )
        TaskStateStore(self.root).initialize(plan, at="2026-09-30T00:02:00+00:00")

        recommendation = self.tower().start_session(
            SessionBinding("owner-gate-routing", "ARENA", goal_id, "Owner-gated routing"),
            task_id="owner-task",
            task_prompt="Wait for the recorded Owner decision.",
        )["recommendation"]
        lines = recommendation["PROMPT"].splitlines()
        self.assertIn("STATUS=WAITING_OWNER", lines[8])
        self.assertEqual("BLOCKER_OR_OWNER_GATE=OWNER_GATE=PENDING: May the task resume?", lines[9])
        self.assertIn("Resolve the recorded blocker or Owner Gate", lines[10])

    def test_t02e_arena_prompt_fails_closed_for_unreadable_plan_and_budget(self) -> None:
        state_dir = self.root / ".p2p" / "state"
        state_dir.mkdir(parents=True)
        (state_dir / "task-state.json").write_text("{broken", encoding="utf-8")
        with self.assertRaises(ProjectionError):
            self.tower().start_session(
                self.binding("unreadable-plan"),
                task_id="TASK-CANARY-1",
                task_prompt=BLIND_TEST_TASK,
            )

        with self.assertRaisesRegex(BindingError, "ARENA_ROUTING_CONTEXT_DID_NOT_FIT"):
            build_execution_prompt(
                self.binding("budget-proof"),
                BLIND_TEST_TASK,
                max_prompt_chars=100,
            )
        with self.assertRaisesRegex(BindingError, "ARENA_ROUTING_CONTEXT_DID_NOT_FIT"):
            build_execution_prompt(self.binding("default-budget-proof"), "x" * 11500)

    # --- T03 stop boundary + one first-turn contract -----------------------
    def test_t03_canary_turn_must_stop_after_one_first_safe_probe(self) -> None:
        prompt = self.start_cli()["recommendation"]["PROMPT"]
        self.assertIn("STOP_AFTER_CANARY=YES", prompt)
        self.assertIn("Stop after that one decisive probe.", prompt)
        self.assertIn("Do not continue the original task in this turn.", prompt)
        self.assertIn("CONTINUATION_CHECKPOINT=READY", prompt)

    def test_t03b_stop_boundary_violation_is_classified_red(self) -> None:
        # Evidence returned, but the neutral checkpoint that ends the turn is missing.
        response = canary_evidence_response(checkpoint=CHECKPOINT_TOKENS[1:])
        grade = classify_canary_evidence(parse_canary_evidence_packet(response), response_text=response)
        self.assertEqual("RED", grade["CLASSIFICATION"])
        self.assertIn("CANARY_STOP_BOUNDARY_VIOLATION", grade["REASONS"][0])

    def test_t03c_control_tower_canary_prompt_has_one_unambiguous_first_turn_return_contract(self) -> None:
        """CONTROL_TOWER_CANARY_PROMPT_CONFLICT_TEST (Supervisor BLOCKER 2)."""

        prompt = self.start_cli()["recommendation"]["PROMPT"]
        for marker in TERMINAL_RETURN_CONTRACT_MARKERS:
            self.assertNotIn(marker, prompt, f"contradictory terminal return contract in canary turn: {marker}")
        self.assertEqual(1, prompt.count(FIRST_TURN_RETURN_CONTRACT_LINE))
        self.assertIn("return exactly this shape, then stop", prompt)
        # Any remaining mention of the terminal packet must be an explicit
        # prohibition/deferral for this turn, never an instruction to emit it.
        for line in prompt.splitlines():
            if "CONTROL_TOWER_RETURN_PACKET" in line:
                upper = line.upper()
                self.assertTrue(
                    "DO NOT" in upper or "NOT PART OF THIS TURN" in upper,
                    f"active terminal-packet instruction in canary turn: {line}",
                )
        # Control: a non-canary session keeps the full terminal return contract.
        codex = self.start_cli(host="CODEX", session_id="codex-contract")["recommendation"]["PROMPT"]
        self.assertIn(handoff.PACKET_BEGIN, codex)
        self.assertIn("Finish with one structured CONTROL_TOWER_RETURN_PACKET.", codex)
        self.assertNotIn(FIRST_TURN_RETURN_CONTRACT_LINE, codex)

    def test_t03d_owner_goal_canary_prompt_has_no_active_continue_until_terminal_instruction(self) -> None:
        """OWNER_GOAL_CANARY_PROMPT_CONFLICT_TEST (Supervisor BLOCKER 3).

        Uses the real Owner /goal intake, and checks both executor-visible
        packets: the compact Arena handoff and the beginner packet the Owner
        actually pastes into Arena.
        """

        intake = owner_goal.build_owner_goal_intake(
            self.root,
            "/goal Hoàn thiện workflow hợp đồng logistics, dùng Arena",
        )
        arena = intake["arena_handoff"]
        self.assertIsNotNone(arena, intake.get("arena_handoff_error"))
        self.assertEqual("YES", arena["fast_canary_required"])
        self.assertEqual("FAST_CANARY_FIRST_SAFE_SLICE_THEN_STOP", arena["execution_mode"])
        self.assertEqual("FAST_CANARY_FIRST_SAFE_SLICE_THEN_STOP", intake["execution_mode"])
        self.assertEqual("AUTONOMOUS_UNTIL_TERMINAL", arena["resumed_task_mode"])
        beginner = intake["beginner_arena_handoff"]["packet_text"]
        for label, text in (("arena_handoff", arena["packet_text"]), ("beginner_packet", beginner)):
            active, deferred = split_first_turn_packet(text)
            active_text = "\n".join(active)
            mode_lines = [line for line in active if line.startswith("EXECUTION_MODE=")]
            self.assertEqual([CANARY_FIRST_TURN_MODE_LINE], mode_lines, label)
            self.assertIn(CANARY_FIRST_TURN_FLOW_LINE, active, label)
            for forbidden in (
                "AUTONOMOUS_UNTIL_TERMINAL",
                "RULE20",
                "create exactly one bounded branch",
                "terminal ReturnPacket produced",
            ):
                self.assertNotIn(forbidden, active_text, f"{label}: active {forbidden!r}")
            for prefix in ("PR_EXPECTATION", "RETURN_PACKET:", "RETURN:", "IMPLEMENT:"):
                self.assertFalse(
                    any(line.startswith(prefix) for line in active),
                    f"{label}: active {prefix} line in first canary turn",
                )
            for token in (*CANARY_TOKENS, "CANARY_EVIDENCE_PACKET_V1", *CHECKPOINT_TOKENS):
                self.assertIn(token, active_text, f"{label}: {token}")
            deferred_text = "\n".join(deferred)
            self.assertIn("external GREEN", deferred[0])
            self.assertIn("Owner continuation", deferred[0])
            self.assertIn("RESUMED_TASK_MODE=AUTONOMOUS_UNTIL_TERMINAL", deferred_text)
            self.assertIn("RULE20 AUTONOMOUS_UNTIL_TERMINAL", deferred_text)
            self.assertIn("create exactly one bounded branch", deferred_text)
            self.assertIn("RETURN_PACKET:", deferred_text)
        # The compact handoff ends on the canary STOP instruction.
        active, _ = split_first_turn_packet(arena["packet_text"])
        self.assertEqual(
            "the Owner decides continuation. Do not continue the original task in this turn.",
            [line for line in active if line.strip()][-1],
        )
        # Control: an existing-session continuation (no canary) keeps RULE20 active.
        resumed = owner_goal.build_arena_handoff(
            self.root,
            {"goal_id": "HERMES-LOGISTICS-01", "objective": BLIND_TEST_TASK},
            None,
            "ARENA",
            reuse=True,
        )
        self.assertEqual("NO", resumed["fast_canary_required"])
        self.assertEqual("AUTONOMOUS_UNTIL_TERMINAL", resumed["execution_mode"])
        self.assertIn("EXECUTION_MODE=AUTONOMOUS_UNTIL_TERMINAL", resumed["packet_text"].splitlines())
        self.assertNotIn(RESUMED_TASK_END, resumed["packet_text"])

    # --- T04 executor self-grade forbidden --------------------------------
    def test_t04_executor_self_classification_is_forbidden_and_rejected(self) -> None:
        prompt = self.start_cli()["recommendation"]["PROMPT"]
        self.assertIn("EXECUTOR_SELF_CLASSIFICATION=FORBIDDEN", prompt)
        self.assertIn("You MUST NOT emit GREEN, YELLOW, ORANGE, RED, KEEP_SESSION", prompt)
        response = canary_evidence_response(
            extra_lines=("SELF_CLASSIFICATION=GREEN", "SESSION_POLICY=KEEP_SESSION")
        )
        grade = classify_canary_evidence(parse_canary_evidence_packet(response), response_text=response)
        self.assertEqual("RED", grade["CLASSIFICATION"])
        self.assertTrue(
            any(reason.startswith("EXECUTOR_SELF_CLASSIFICATION_FORBIDDEN") for reason in grade["REASONS"])
        )

    def test_t04b_arena_never_authoritatively_self_emits_grade_or_policy(self) -> None:
        prompt = self.start_cli()["recommendation"]["PROMPT"]
        for token in ("KEEP_SESSION=YES", "LIMIT_SESSION=YES", "REROLL=YES", "SESSION_GRADE=GREEN"):
            self.assertNotIn(token, prompt)
        self.assertIn("CANARY_CLASSIFIER=CONTROL_TOWER_OR_INDEPENDENT_VERIFIER", prompt)

    # --- T05 canary ingest ------------------------------------------------
    def test_t05_pure_canary_evidence_only_response_is_ingested_and_externally_graded(self) -> None:
        """PURE_CANARY_EVIDENCE_ONLY_INGEST_TEST (Supervisor BLOCKER 2).

        The input is ONLY CANARY_EVIDENCE_PACKET_V1 + checkpoint metadata. No
        CONTROL_TOWER_RETURN_PACKET is present; the Control Tower binds the
        response to the session it registered.
        """

        self.start_cli(session_id="pure-1")
        response = canary_evidence_response()
        self.assertNotIn("CONTROL_TOWER_RETURN_PACKET", response)
        self.assertNotIn(handoff.PACKET_BEGIN, response)
        self.assertNotIn(handoff.PACKET_END, response)
        keys = [line.split("=", 1)[0] for line in response.splitlines() if "=" in line]
        self.assertEqual(
            [*CANONICAL_EVIDENCE_KEYS, *(token.split("=", 1)[0] for token in CHECKPOINT_TOKENS)],
            keys,
        )
        self.assertEqual("CANARY_EVIDENCE_PACKET_V1", response.splitlines()[0])

        result = self.ingest_cli(response, session_id="pure-1")
        self.assertEqual("PASS", result["status"])
        self.assertFalse(result["idempotent"])
        grade = result["canary_grade"]
        self.assertEqual("GREEN", grade["CLASSIFICATION"])
        self.assertEqual("KEEP_SESSION", grade["SESSION_POLICY"])
        self.assertEqual("CONTROL_TOWER_OR_INDEPENDENT_VERIFIER", grade["CANARY_CLASSIFIER"])
        self.assertEqual("YES", grade["OWNER_CONTINUATION_REQUIRED"])
        snapshot = result["snapshot"]
        self.assertEqual("WAIT_FOR_OWNER_CONTINUATION", snapshot["NEXT_SAFE_ACTION"]["ACTION"])
        self.assertEqual("GREEN", snapshot["CANARY_GATES"][0]["CLASSIFICATION"])
        self.assertEqual([], snapshot["ACTIVE_EXECUTION"])

        events = self.ledger_events()
        self.assertEqual(
            ["CONTROL_TOWER_SESSION_STARTED", "CONTROL_TOWER_CANARY_EVIDENCE"],
            [event["event_type"] for event in events],
        )
        evidence_event = events[1]
        self.assertEqual("pure-1", evidence_event["SESSION_BINDING"]["SESSION_ID"])
        self.assertEqual("GREEN", evidence_event["CONTROL_TOWER_CANARY"]["CLASSIFICATION"])
        self.assertEqual(
            "grep -c FAST_CANARY scripts/p2p_control_tower.py",
            evidence_event["CANARY_EVIDENCE"]["DECISIVE_CHECK"],
        )
        self.assertIsNone(evidence_event["EXECUTOR_RETURN_PACKET"])
        self.assertEqual("NO", evidence_event["RAW_EXECUTOR_RESPONSE_PERSISTED"])

        # The same evidence-only shape is genuinely graded, not rubber-stamped.
        self.start_cli(session_id="pure-2")
        red = self.ingest_cli(canary_evidence_response(durable_mutation="YES"), session_id="pure-2")
        self.assertEqual("RED", red["canary_grade"]["CLASSIFICATION"])
        self.assertIn("CANARY_DURABLE_MUTATION_BOUNDARY_VIOLATED", red["canary_grade"]["REASONS"])

    def test_t05_receipts_fail_closed_for_missing_invalid_contradictory_and_mismatched_inputs(self) -> None:
        cases = (
            (
                "missing",
                canary_evidence_response(law_check="", experience_check=""),
                "EXECUTOR_LAW_CHECK_MISSING",
            ),
            (
                "malformed-law-and-experience",
                canary_evidence_response(
                    law_check="LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256=bad",
                    experience_check="EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=",
                ),
                "EXECUTOR_LAW_CHECK_INVALID",
            ),
            (
                "blocked-law",
                canary_evidence_response(
                    law_check="LAW_CHECK=BLOCKED | REASON=canonical law unavailable",
                    experience_check="EXPERIENCE_CHECK=UNAVAILABLE",
                ),
                "EXECUTOR_LAW_CHECK_BLOCKED",
            ),
            (
                "blocked-experience",
                canary_evidence_response(
                    experience_check="EXPERIENCE_CHECK=BLOCKED | REASON=lookup failed",
                ),
                "EXPERIENCE_CHECK_BLOCKED",
            ),
            (
                "contradictory",
                canary_evidence_response(
                    experience_check="EXPERIENCE_CHECK=UNAVAILABLE",
                    extra_lines=("EXPERIENCE_CHECK=NO_MATCH",),
                ),
                "EXPERIENCE_CHECK_CONTRADICTORY",
            ),
        )
        for suffix, response, expected_blocker in cases:
            with self.subTest(case=suffix):
                session_id = f"receipt-{suffix}"
                self.start_cli(session_id=session_id)
                result = self.ingest_cli(response, session_id=session_id)
                self.assertNotEqual("GREEN", result["canary_grade"]["CLASSIFICATION"])
                self.assertTrue(
                    any(expected_blocker in reason for reason in result["canary_grade"]["REASONS"]),
                    result["canary_grade"],
                )
                event = self.ledger_events()[-1]
                self.assertIn(expected_blocker, event["ACTOR_RECEIPT_BLOCKERS"])
                if suffix == "malformed-law-and-experience":
                    self.assertIn("EXPERIENCE_CHECK_INVALID", event["ACTOR_RECEIPT_BLOCKERS"])

        # Correctly shaped receipts with a wrong law SHA and wrong active ID also fail closed.
        mismatch_cases = (
            (
                "wrong-sha",
                canary_evidence_response(
                    law_check="LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256=" + "0" * 64,
                    experience_check="EXPERIENCE_CHECK=UNAVAILABLE",
                ),
                "EXECUTOR_LAW_HASH_MISMATCH",
            ),
            (
                "wrong-experience",
                canary_evidence_response(
                    experience_check="EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=not-the-active-id",
                ),
                "EXPERIENCE_CHECK_IDS_MISMATCH",
            ),
            (
                "inconsistent-no-match",
                canary_evidence_response(experience_check="EXPERIENCE_CHECK=NO_MATCH"),
                "EXPERIENCE_CHECK_INCONSISTENT_WITH_ACTIVE_EXPECTATION",
            ),
        )
        for suffix, response, expected_blocker in mismatch_cases:
            with self.subTest(case=suffix):
                session_id = f"receipt-{suffix}"
                expected_id = "shared-exp-expected-for-mismatch"
                binding = self.binding(session_id)
                self.tower().start_session(
                    binding,
                    expected_law_sha=EXPECTED_CANONICAL_LAW_SHA,
                    expected_experience_ids=(expected_id,),
                    canary_directive=self.directive(session_id),
                )
                self.assertEqual([expected_id], self.ledger_events()[-1]["EXPECTED_EXPERIENCE_IDS"])
                result = self.ingest_cli(response, session_id=session_id)
                self.assertNotEqual("GREEN", result["canary_grade"]["CLASSIFICATION"])
                self.assertTrue(
                    any(expected_blocker in reason for reason in result["canary_grade"]["REASONS"]),
                    result["canary_grade"],
                )

    def test_t05e_expected_law_sha_with_trailing_hex_character_cannot_grade_green(self) -> None:
        malformed_sha = EXPECTED_CANONICAL_LAW_SHA + "a"
        response = canary_evidence_response(
            law_check=(
                "LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md "
                f"| SOURCE_SHA256={malformed_sha}"
            ),
            experience_check="EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-parser-expected",
        )
        self.assert_receipt_response_fails_closed(
            "receipt-trailing-sha", response, "EXECUTOR_LAW_CHECK_INVALID"
        )

    def test_t05f_duplicate_law_sha_fields_cannot_grade_green(self) -> None:
        response = canary_evidence_response(
            law_check=(
                "LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md "
                f"| SOURCE_SHA256={EXPECTED_CANONICAL_LAW_SHA} | SOURCE_SHA256={'0' * 64}"
            ),
            experience_check="EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-parser-expected",
        )
        self.assert_receipt_response_fails_closed(
            "receipt-duplicate-law-sha", response, "EXECUTOR_LAW_CHECK_INVALID"
        )

    def test_t05g_duplicate_law_source_fields_cannot_grade_green(self) -> None:
        response = canary_evidence_response(
            law_check=(
                "LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md "
                f"| SOURCE=attacker-controlled.md | SOURCE_SHA256={EXPECTED_CANONICAL_LAW_SHA}"
            ),
            experience_check="EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-parser-expected",
        )
        self.assert_receipt_response_fails_closed(
            "receipt-duplicate-law-source", response, "EXECUTOR_LAW_CHECK_INVALID"
        )

    def test_t05h_repeated_experience_directives_cannot_grade_green(self) -> None:
        matching_law = (
            "LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md "
            f"| SOURCE_SHA256={EXPECTED_CANONICAL_LAW_SHA}"
        )
        cases = (
            (
                "repeated-lines",
                canary_evidence_response(
                    law_check=matching_law,
                    experience_check="EXPERIENCE_CHECK=UNAVAILABLE",
                    extra_lines=("EXPERIENCE_CHECK=UNAVAILABLE",),
                ),
                "EXPERIENCE_CHECK_CONTRADICTORY",
            ),
            (
                "repeated-same-line",
                canary_evidence_response(
                    law_check=matching_law,
                    experience_check="EXPERIENCE_CHECK=UNAVAILABLE | EXPERIENCE_CHECK=UNAVAILABLE",
                ),
                "EXPERIENCE_CHECK_INVALID",
            ),
        )
        for suffix, response, expected_reason in cases:
            with self.subTest(case=suffix):
                self.assert_receipt_response_fails_closed(
                    f"receipt-repeat-experience-{suffix}",
                    response,
                    expected_reason,
                )

    def test_t05i_duplicate_experience_ids_cannot_hide_conflicting_value(self) -> None:
        matching_law = (
            "LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md "
            f"| SOURCE_SHA256={EXPECTED_CANONICAL_LAW_SHA}"
        )
        response = canary_evidence_response(
            law_check=matching_law,
            experience_check=(
                "EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE "
                "| IDS=shared-exp-parser-expected | IDS=conflicting-exp-id"
            ),
        )
        self.assert_receipt_response_fails_closed(
            "receipt-duplicate-experience-ids", response, "EXPERIENCE_CHECK_INVALID"
        )

    def test_t05_valid_actor_receipts_matching_session_expectations_allow_green(self) -> None:
        binding = self.binding("receipt-valid-expected")
        expected_id = "shared-exp-expected-receipt"
        self.tower().start_session(
            binding,
            task_id="TASK-CANARY-RECEIPTS",
            expected_law_sha=EXPECTED_CANONICAL_LAW_SHA,
            expected_experience_ids=(expected_id,),
            canary_directive=self.directive(binding.session_id),
        )
        response = canary_evidence_response(
            experience_check=f"EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS={expected_id}",
        )
        result = self.ingest_canary(binding, response)
        self.assertEqual("GREEN", result["canary_grade"]["CLASSIFICATION"])
        event = self.ledger_events()[-1]
        self.assertEqual("PASS", event["ACTOR_RECEIPTS"]["LAW_CHECK"]["status"])
        self.assertEqual("USE_ACTIVE_EXPERIENCE", event["ACTOR_RECEIPTS"]["EXPERIENCE_CHECK"]["decision"])
        self.assertEqual([], event["ACTOR_RECEIPT_BLOCKERS"])

    def test_t05b_replay_is_idempotent_and_raw_transcript_is_not_persisted(self) -> None:
        binding = self.start_canary()
        response = canary_evidence_response(preface="UNIQUE RAW EXECUTOR TRANSCRIPT\n\n")
        first = self.ingest_canary(binding, response)
        ledger = self.root / LEDGER_RELATIVE
        first_raw = ledger.read_text(encoding="utf-8")
        second = self.ingest_canary(binding, response)
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first_raw, ledger.read_text(encoding="utf-8"))
        self.assertNotIn("UNIQUE RAW EXECUTOR TRANSCRIPT", ledger.read_text(encoding="utf-8"))
        # A fresh tower replays the durable grade without re-grading.
        snapshot = self.tower().snapshot()
        gate = snapshot["CANARY_GATES"][0]
        self.assertEqual("GREEN", gate["CLASSIFICATION"])
        self.assertEqual("KEEP_SESSION", gate["SESSION_POLICY"])
        self.assertEqual("CONTROL_TOWER_DURABLE_STATE", gate["ORIGINAL_TASK_SOURCE"])
        # A different canary response for the same graded session fails closed.
        with self.assertRaises(ControlTowerHandoffError) as ctx:
            self.ingest_canary(binding, canary_evidence_response(facts="a different story"))
        self.assertIn("CANARY_SESSION_ALREADY_GRADED", str(ctx.exception))

    def test_t05c_evidence_only_ingest_is_bound_explicitly_and_only_to_triggered_canary_sessions(self) -> None:
        self.start_canary()
        response = canary_evidence_response()
        with self.assertRaises(ControlTowerHandoffError) as missing:
            self.tower().ingest_response(response)
        self.assertIn("CANARY_EVIDENCE_SESSION_ID_REQUIRED", str(missing.exception))
        with self.assertRaises(ControlTowerHandoffError) as unknown:
            self.tower().ingest_response(response, session_id="never-registered")
        self.assertIn("SESSION_ID_NOT_REGISTERED", str(unknown.exception))
        # A non-canary session still requires the full terminal packet.
        codex = SessionBinding(session_id="codex-1", host="CODEX", goal_id="G", goal=BLIND_TEST_TASK)
        self.tower().start_session(codex, canonical_base_sha=BASE_SHA, canonical_base_tree=BASE_TREE)
        with self.assertRaises(ControlTowerHandoffError) as not_canary:
            self.tower().ingest_response(response, session_id="codex-1")
        self.assertIn("CANARY_EVIDENCE_REQUIRES_TRIGGERED_CANARY_SESSION", str(not_canary.exception))
        accepted = self.tower().ingest_response(terminal_return_packet(codex))
        self.assertEqual("PASS", accepted["status"])
        self.assertNotIn("canary_grade", accepted)

    def test_t05d_unsafe_canary_evidence_is_rejected_before_it_can_poison_the_ledger(self) -> None:
        binding = self.start_canary()
        with self.assertRaises(ControlTowerHandoffError) as ctx:
            self.ingest_canary(binding, canary_evidence_response(facts="found token=abc123 in env"))
        self.assertIn("CANARY_EVIDENCE_UNSAFE_FOR_LEDGER", str(ctx.exception))
        # Nothing was written, replay still works, and a clean retry is graded.
        self.assertEqual(["CONTROL_TOWER_SESSION_STARTED"], [event["event_type"] for event in self.ledger_events()])
        snapshot = self.tower().snapshot()
        self.assertEqual("UNVERIFIED", snapshot["CANARY_GATES"][0]["CLASSIFICATION"])
        self.assertEqual("session-arena-canary-0001", snapshot["ACTIVE_EXECUTION"][0]["SESSION_ID"])
        self.assertEqual("GREEN", self.ingest_canary(binding)["canary_grade"]["CLASSIFICATION"])

    # --- T06 external grading --------------------------------------------
    def test_t06_external_grade_routing_table_is_deterministic(self) -> None:
        cases = {
            "GREEN": canary_evidence_response(),
            "YELLOW": canary_evidence_response(
                check_result="exit=1; focused probe failed",
                errors="one command error",
                recovery="re-ran with corrected path",
            ),
            "ORANGE": canary_evidence_response(check_result="UNKNOWN"),
            "RED": canary_evidence_response(durable_mutation="YES"),
        }
        for expected, response in cases.items():
            grade = classify_canary_evidence(parse_canary_evidence_packet(response), response_text=response)
            self.assertEqual(expected, grade["CLASSIFICATION"], response)
        expected_policies = {
            "GREEN": "KEEP_SESSION",
            "YELLOW": "LIMIT_SESSION",
            "ORANGE": "ADVISORY_OR_LOW_RISK_ONLY",
            "RED": "REROLL_OR_SWITCH_EXECUTOR",
            "UNVERIFIED": "NO_DEFAULT_CONTINUATION",
        }
        for classification, policy in expected_policies.items():
            self.assertEqual(policy, handoff.CANARY_SESSION_POLICIES[classification])

    def test_t06b_unverified_is_not_implicit_green(self) -> None:
        incomplete = "\n".join(
            line for line in canary_evidence_response().splitlines() if not line.startswith("DECISIVE_CHECK=")
        )
        grade = classify_canary_evidence(parse_canary_evidence_packet(incomplete), response_text=incomplete)
        self.assertEqual("UNVERIFIED", grade["CLASSIFICATION"])
        self.assertEqual("NO_DEFAULT_CONTINUATION", grade["SESSION_POLICY"])

    def test_t06c_red_rerolls_without_keep_working(self) -> None:
        binding = self.start_canary()
        result = self.ingest_canary(
            binding,
            canary_evidence_response(
                check_result="exit=1; decisive probe failed",
                errors="command failed",
                recovery="NONE",
            ),
        )
        self.assertEqual("RED", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("REROLL_OR_SWITCH_EXECUTOR", result["canary_grade"]["SESSION_POLICY"])
        self.assertIn("CANARY_CHECK_FAILED_WITHOUT_RECOVERY", result["canary_grade"]["REASONS"])
        self.assertEqual("REROLL_OR_SWITCH_EXECUTOR", result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])

    # --- T07 Owner continuation gate --------------------------------------
    def test_t07_owner_continuation_before_external_green_is_blocked(self) -> None:
        binding = self.start_canary()
        with self.assertRaises(BindingError) as before_grade:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertIn("CANARY_OWNER_CONTINUATION_BLOCKED:UNVERIFIED", str(before_grade.exception))
        self.ingest_canary(binding)
        with self.assertRaises(BindingError) as without_owner:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="NO")
        self.assertIn("CANARY_OWNER_CONTINUATION_REQUIRED", str(without_owner.exception))

    def test_t07b_owner_continuation_without_green_is_blocked(self) -> None:
        binding = self.start_canary()
        self.ingest_canary(binding, canary_evidence_response(durable_mutation="YES"))
        with self.assertRaises(BindingError) as ctx:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertIn("CANARY_OWNER_CONTINUATION_BLOCKED:RED", str(ctx.exception))

    def test_t07c_resumed_return_before_owner_continuation_is_rejected(self) -> None:
        binding = self.start_canary()
        self.ingest_canary(binding)
        with self.assertRaises(ControlTowerHandoffError) as ctx:
            self.tower().ingest_response(terminal_return_packet(binding))
        self.assertIn("CANARY_OWNER_CONTINUATION_REQUIRED", str(ctx.exception))
        # Nothing but the session start and the canary grade is durable.
        self.assertEqual(
            ["CONTROL_TOWER_SESSION_STARTED", "CONTROL_TOWER_CANARY_EVIDENCE"],
            [event["event_type"] for event in self.ledger_events()],
        )

    # --- T08 GREEN + Owner continuation resumes original task -------------
    def test_t08_green_plus_owner_continuation_resumes_original_task_same_session(self) -> None:
        binding = self.start_canary()
        initial_title = self.ledger_events()[0]["RECOMMENDED_NEW_CHAT"]["CHAT_TITLE"]
        self.ingest_canary(binding)
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
        self.assertEqual(initial_title, recommendation["CHAT_TITLE"])
        self.assertEqual("ARENA", recommendation["HOST"])
        self.assertEqual("CONTROL_TOWER_DURABLE_STATE", recommendation["ORIGINAL_TASK_SOURCE"])
        self.assertEqual("RESUME_ORIGINAL_TASK_IN_SAME_SESSION", recommendation["CONTINUATION_MODE"])
        self.assertEqual("NO", recommendation["CANARY_REPEAT"])
        prompt = recommendation["PROMPT"]
        self.assertIn(BLIND_TEST_TASK, prompt)
        self.assertEqual("GỬI CHO: ARENA AI", prompt.splitlines()[1])
        self.assertEqual("CHAT_MODE=SAME_CHAT", prompt.splitlines()[3])
        self.assertEqual(f"CHAT_TITLE={recommendation['CHAT_TITLE']}", prompt.splitlines()[4])
        self.assertEqual("NO_FORMAL_PLAN", prompt.splitlines()[6].removeprefix("PLAN_REFERENCE="))
        self.assertNotIn("SESSION_START", prompt.splitlines()[8])
        self.assertIn(f"SESSION_ID={binding.session_id}", prompt.splitlines()[8])
        self.assertIn("CANARY_GRADE=GREEN; OWNER_CONTINUATION=YES", prompt.splitlines()[8])
        self.assertEqual("BLOCKER_OR_OWNER_GATE=NONE_RECORDED", prompt.splitlines()[9])
        # Continuation does not repeat the canary; the resumed ORIGINAL task
        # now carries the full terminal return contract.
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", prompt)
        self.assertNotIn(FIRST_TURN_RETURN_CONTRACT_LINE, prompt)
        self.assertIn(handoff.PACKET_BEGIN, prompt)
        self.assertIn("Finish with one structured CONTROL_TOWER_RETURN_PACKET.", prompt)
        self.assertIn(
            '"schema":"p2p-control-tower-return-packet/1"',
            prompt,
        )
        self.assertIn('"CONTROL_TOWER_RETURN_PACKET":true', prompt)
        self.assertIn("LAW_CHECK", prompt)
        self.assertIn("EXPERIENCE_CHECK", prompt)
        self.assertIn("LEARNING_RECONCILIATION", prompt)

        # Idempotent replay of the Owner decision.
        again = self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertTrue(again["idempotent"])
        self.assertEqual(prompt, again["recommendation"]["PROMPT"])

        # The resumed ORIGINAL task's terminal return is ingested for the SAME session.
        final = self.ingest_cli(terminal_return_packet(binding))
        self.assertEqual("PASS", final["status"])
        self.assertFalse(final["idempotent"])
        self.assertEqual("CURRENT", final["reconciliation"]["CANONICAL_RELATION"])
        self.assertTrue(self.ingest_cli(terminal_return_packet(binding))["idempotent"])
        self.assertEqual(
            [
                "CONTROL_TOWER_SESSION_STARTED",
                "CONTROL_TOWER_CANARY_EVIDENCE",
                "CONTROL_TOWER_CANARY_CONTINUATION",
                "CONTROL_TOWER_RETURN_PACKET",
            ],
            [event["event_type"] for event in self.ledger_events()],
        )
        snapshot = self.tower().snapshot()
        closed = [record for record in snapshot["RECENTLY_CLOSED"] if record["SESSION_ID"] == binding.session_id]
        self.assertEqual("COMPLETED", closed[0]["SESSION_STATE"])
        self.assertEqual("GREEN", snapshot["CANARY_GATES"][0]["CLASSIFICATION"])
        self.assertEqual("YES", snapshot["CANARY_GATES"][0]["OWNER_CONTINUATION_RECORDED"])

    def test_t08b_fallback_owner_reply_is_accepted(self) -> None:
        binding = self.start_canary()
        self.ingest_canary(binding)
        result = self.tower().continue_canary_session(
            binding.session_id,
            owner_continuation="NO",
            owner_reply="Tiếp tục công việc",
        )
        self.assertEqual("PASS", result["status"])
        self.assertIn(BLIND_TEST_TASK, result["recommendation"]["PROMPT"])

    # --- T09 same-session no repeat ---------------------------------------
    def test_t09_same_green_session_same_goal_does_not_recanary(self) -> None:
        binding = self.start_canary()
        self.ingest_canary(binding)
        self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        again = self.tower().start_session(binding, task_prompt=BLIND_TEST_TASK)
        self.assertTrue(again["idempotent"])
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", again["recommendation"]["PROMPT"])
        self.assertEqual("NO", again["recommendation"]["CANARY_REPEAT"])
        self.assertEqual("ESTABLISHED", self.tower().session_quality(binding.goal_id, binding.session_id))

    # --- T10 new session re-canaries --------------------------------------
    def test_t10_new_arena_session_recanaries(self) -> None:
        binding = self.start_canary("session-arena-canary-0001")
        self.ingest_canary(binding)
        self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        fresh = self.binding("session-arena-canary-0002")
        result = self.tower().start_session(fresh, canary_directive=self.directive("session-arena-canary-0002"))
        self.assertFalse(result["idempotent"])
        self.assertIn("FAST_CANARY_REQUIRED=YES", result["recommendation"]["PROMPT"])
        self.assertEqual("UNKNOWN", self.tower().session_quality(fresh.goal_id, fresh.session_id))
        # The CLI derives the same decision from durable state for a new session id.
        cli = self.start_cli(session_id="session-arena-canary-0003")
        self.assertEqual("YES", cli["recommendation"]["FAST_CANARY_REQUIRED"])

    # --- T11 low-risk bypass (explicit declaration only) ------------------
    def test_t11_low_risk_mechanical_arena_task_bypasses_canary_only_by_explicit_declaration(self) -> None:
        declared = canary_requirement("ARENA", low_risk_mechanical=True)
        self.assertEqual("NO", declared["FAST_CANARY_REQUIRED"])
        self.assertEqual("LOW_RISK_MECHANICAL_ARENA_TASK", declared["REASON"])
        self.assertEqual("LOW_RISK_MECHANICAL", declared["RISK_CLASS"])
        result = self.start_cli(goal=MECHANICAL_LOOKING_TASK, session_id="low-risk-1", extra=("--low-risk-mechanical",))
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", result["recommendation"]["PROMPT"])
        self.assertNotIn("CANARY_EVIDENCE_PACKET_V1", result["recommendation"]["PROMPT"])
        self.assertIn(handoff.PACKET_BEGIN, result["recommendation"]["PROMPT"])
        # Without the explicit declaration the same text fails closed into canary.
        undeclared = self.start_cli(goal=MECHANICAL_LOOKING_TASK, session_id="low-risk-2")
        self.assertIn("FAST_CANARY_REQUIRED=YES", undeclared["recommendation"]["PROMPT"])

    # --- T12 non-Arena bypass ---------------------------------------------
    def test_t12_non_arena_executor_bypasses_arena_canary(self) -> None:
        decision = canary_requirement("CODEX")
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
            build_execution_prompt(binding, BLIND_TEST_TASK, canary_directive=directive, max_prompt_chars=2000)
        self.assertIn("CONTROL_TOWER_CANARY_CONTEXT_DID_NOT_FIT", str(ctx.exception))
        prompt = build_execution_prompt(
            binding,
            BLIND_TEST_TASK,
            canary_directive=directive,
            max_prompt_chars=control_tower.PROMPT_GUARD_CHARS,
        )
        for token in (*CANARY_TOKENS, *CHECKPOINT_TOKENS, FIRST_TURN_RETURN_CONTRACT_LINE):
            self.assertIn(token, prompt)

    # --- T14 live blind-test regression shape -----------------------------
    def test_t14_live_blind_test_terminal_conclusion_without_evidence_is_red(self) -> None:
        binding = self.start_canary()
        blind = "SUSPECTED DEFECT FALSIFIED after broad investigation and budget sweeps.\n\n"
        result = self.tower().ingest_response(blind + terminal_return_packet(binding, session_state="COMPLETED"))
        grade = result["canary_grade"]
        self.assertEqual("RED", grade["CLASSIFICATION"])
        self.assertEqual("REROLL_OR_SWITCH_EXECUTOR", grade["SESSION_POLICY"])
        self.assertIn("CANARY_EVIDENCE_PACKET_MISSING_AFTER_TERMINAL_CONCLUSION", grade["REASONS"])
        self.assertEqual("REROLL_OR_SWITCH_EXECUTOR", result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])
        # The canary turn is graded as a canary turn; it never becomes the
        # session's terminal return.
        events = self.ledger_events()
        self.assertEqual("CONTROL_TOWER_CANARY_EVIDENCE", events[-1]["event_type"])
        self.assertEqual("COMPLETED", events[-1]["EXECUTOR_RETURN_PACKET"]["SESSION_STATE"])
        with self.assertRaises(BindingError) as ctx:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertIn("CANARY_OWNER_CONTINUATION_BLOCKED:RED", str(ctx.exception))

    def test_t14b_non_terminal_missing_evidence_is_unverified_not_green(self) -> None:
        binding = self.start_canary()
        result = self.tower().ingest_response(terminal_return_packet(binding, session_state="READY"))
        self.assertEqual("UNVERIFIED", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("NO_DEFAULT_CONTINUATION", result["canary_grade"]["SESSION_POLICY"])
        self.assertEqual("NO_DEFAULT_CONTINUATION", result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])

    def test_t14c_terminal_conclusion_in_canary_turn_is_red_even_with_evidence(self) -> None:
        binding = self.start_canary()
        response = canary_evidence_response() + "\n" + terminal_return_packet(binding, session_state="COMPLETED")
        result = self.tower().ingest_response(response)
        self.assertEqual("RED", result["canary_grade"]["CLASSIFICATION"])
        self.assertIn(
            "CANARY_STOP_BOUNDARY_VIOLATION:TERMINAL_CONCLUSION_IN_CANARY_TURN",
            result["canary_grade"]["REASONS"],
        )

    # --- T15 durable mutation boundary ------------------------------------
    def test_t15_canary_forbids_durable_mutation_and_flags_violation(self) -> None:
        prompt = self.start_cli()["recommendation"]["PROMPT"]
        self.assertIn("CANARY_DURABLE_MUTATION_ALLOWED=NO", prompt)
        self.assertIn("Do not create durable commits, branches, PRs, remote writes", prompt)
        binding = self.start_canary()
        result = self.ingest_canary(binding, canary_evidence_response(durable_mutation="YES"))
        self.assertEqual("RED", result["canary_grade"]["CLASSIFICATION"])
        self.assertIn("CANARY_DURABLE_MUTATION_BOUNDARY_VIOLATED", result["canary_grade"]["REASONS"])

    # --- T16 Logistics PR112 regression shape -----------------------------
    def test_t16_logistics_pr112_canary_regression_stops_at_first_safe_boundary(self) -> None:
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
        active, _ = split_first_turn_packet(handoff_packet["packet_text"])
        for token in CANARY_TOKENS:
            self.assertIn(token, "\n".join(active))
        self.assertIn(goal, handoff_packet["packet_text"])

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
        )
        self.tower().start_session(
            binding,
            task_id="HERMES-LOGISTICS-01-T1",
            worktree="fixture-worktree",
            branch="arena/hermes-logistics-01",
            canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE,
            expected_law_sha=EXPECTED_CANONICAL_LAW_SHA,
            expected_experience_ids=(),
            canary_directive=directive,
        )
        response = canary_evidence_response(
            current_state="arena/hermes-logistics-01 @ 3cb8049921805dbd963a091d9b37ae06a3a9fd61",
            facts="read-only endpoint missing; route handler has no status branch",
            decisive_check="grep -n shipment_status deployments/hermes-dockhosting/plugins/logistics/__init__.py",
            check_result="exit=0; 0 matches",
        )
        self.assertNotIn("CONTROL_TOWER_RETURN_PACKET", response)
        result = self.ingest_cli(response, session_id=binding.session_id)
        self.assertEqual("GREEN", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("UNKNOWN", result["canary_grade"]["MODEL_IDENTITY"])
        # The first safe probe is evidence only; the real PR work still waits.
        self.assertEqual("WAIT_FOR_OWNER_CONTINUATION", result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])
        with self.assertRaises(BindingError):
            self.tower().continue_canary_session(binding.session_id, owner_continuation="NO")
        resumed = self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertEqual("NO", resumed["recommendation"]["CANARY_REPEAT"])
        self.assertIn(goal, resumed["recommendation"]["PROMPT"])
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", resumed["recommendation"]["PROMPT"])

    # --- T17 YELLOW bounded continuation ----------------------------------
    def test_t17_yellow_allows_only_bounded_limited_continuation(self) -> None:
        binding = self.start_canary()
        result = self.ingest_canary(
            binding,
            canary_evidence_response(
                check_result="exit=1; focused probe failed on first attempt",
                errors="one command error",
                recovery="re-ran with corrected path and passed",
            ),
        )
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
        binding = self.start_canary()
        result = self.ingest_canary(binding, canary_evidence_response(check_result="UNKNOWN"))
        self.assertEqual("ORANGE", result["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("ADVISORY_OR_LOW_RISK_ONLY", result["canary_grade"]["SESSION_POLICY"])
        self.assertEqual("ADVISORY_OR_LOW_RISK_ONLY", result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])
        with self.assertRaises(BindingError) as ctx:
            self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        self.assertIn("CANARY_OWNER_CONTINUATION_BLOCKED:ORANGE", str(ctx.exception))

    # T19 (managed-project package/install inheritance) lives in
    # tests/test_p2p_arena_canary_install_inheritance.py because it builds and
    # installs the real release.

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
        binding = self.start_canary()
        self.ingest_canary(binding)
        self.tower().continue_canary_session(binding.session_id, owner_continuation="YES")
        state_dir = self.root / ".p2p" / "state"
        self.assertEqual(["execution-ledger.jsonl"], sorted(path.name for path in state_dir.iterdir()))
        self.assertTrue(
            {event["event_type"] for event in self.ledger_events()} <= set(handoff.CONTROL_TOWER_EVENT_TYPES)
        )

    def test_oe_risk_decision_is_explicit_bypass_or_fail_closed_without_parallel_taxonomy(self) -> None:
        """OE challenge: no regex task-text risk taxonomy at this seam."""

        self.assertEqual(("LOW_RISK_MECHANICAL", "MEDIUM_OR_HIGH_RISK"), handoff.RISK_CLASSES)
        self.assertFalse(hasattr(handoff, "classify_task_risk_class"))
        for name in ("_HIGH_RISK_PATTERNS", "_MEDIUM_RISK_PATTERN", "_LOW_RISK_MECHANICAL_PHRASE"):
            self.assertFalse(hasattr(handoff, name), name)
        fail_closed = canary_requirement("ARENA")
        self.assertEqual("YES", fail_closed["FAST_CANARY_REQUIRED"])
        self.assertEqual("MEDIUM_OR_HIGH_RISK", fail_closed["RISK_CLASS"])
        # Owner /goal has no explicit low-risk declaration input, so even a
        # mechanical-looking objective fails closed into canary.
        mechanical = owner_goal.build_arena_handoff(
            self.root,
            {"goal_id": "DOCS-01", "objective": MECHANICAL_LOOKING_TASK},
            None,
            "ARENA",
        )
        self.assertEqual("YES", mechanical["fast_canary_required"])


if __name__ == "__main__":
    unittest.main()
