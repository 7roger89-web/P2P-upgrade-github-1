"""Focused acceptance tests — P2P-WORK-FACTORY-01 minimum durable work-item flow.

Acceptance: two non-overlapping fixture work items assigned to different
executors must (1) start from explicit base identity, (2) return independent
result packets, (3) retain provenance, (4) enter an integration queue without
ambiguity, and (5) preserve Owner/review gates. The system must detect or
refuse duplicate/conflicting identity, stale base, missing candidate identity,
and ambiguous project/workstream binding.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
for candidate in (str(SYSTEM_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    BindingError,
    ControlTowerHandoffError,
    SessionBinding,
    create_return_packet,
)
from p2p_capabilities.work_item_handoff import (  # noqa: E402
    UNKNOWN,
    WorkItemHandoff,
    WorkItemHandoffError,
)


BASE_SHA = "a" * 40
BASE_TREE = "b" * 40
ADVANCED_SHA = "c" * 40
ADVANCED_TREE = "d" * 40
CAND_A_SHA = "e" * 40
CAND_A_TREE = "f" * 40
CAND_B_SHA = "0" * 40
CAND_B_TREE = "1" * 40
PROJECT = "P2P"
WORKSTREAM = "P2P-WORK-FACTORY-01"
OWNER_GATE_A = {
    "GATE_ID": "OWNER_GATE_FIXTURE_ALPHA",
    "QUESTION": "Approve integration of fixture alpha?",
    "REQUIRED_ACTION": "OWNER_APPROVAL",
}


class WorkItemHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_parent = REPO_ROOT / ".tmp"
        temp_parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="work-item-01-", dir=str(temp_parent))
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def handoff(
        self,
        base_sha: str = BASE_SHA,
        base_tree: str = BASE_TREE,
    ) -> WorkItemHandoff:
        return WorkItemHandoff(
            self.root,
            current_canonical_base_sha=base_sha,
            current_canonical_base_tree=base_tree,
        )

    def register(
        self,
        handoff: WorkItemHandoff,
        work_item_id: str,
        executor: str,
        scope: tuple[str, ...],
        expected_output: str,
        *,
        dependencies: tuple[str, ...] = (),
        base_sha: str = BASE_SHA,
        base_tree: str = BASE_TREE,
        project: str = PROJECT,
        workstream: str = WORKSTREAM,
    ) -> dict:
        return handoff.register_work_item(
            work_item_id=work_item_id,
            project=project,
            workstream=workstream,
            base_sha=base_sha,
            base_tree=base_tree,
            executor=executor,
            scope=scope,
            dependencies=dependencies,
            expected_output=expected_output,
        )

    @staticmethod
    def marked_packet(
        item: dict,
        *,
        session_state: str = "COMPLETED",
        owner_gate: object = None,
        candidate_sha: str = CAND_A_SHA,
        base_sha: str = BASE_SHA,
        base_tree: str = BASE_TREE,
    ) -> str:
        packet = create_return_packet(
            SessionBinding(
                session_id=item["SESSION_ID"],
                host=item["EXECUTOR"],
                goal_id=item["WORKSTREAM"],
                goal=item["EXPECTED_OUTPUT"],
            ),
            session_state=session_state,
            canonical_base_sha=base_sha,
            canonical_base_tree=base_tree,
            canonical_relation="CURRENT",
            worktree="fixture-worktree",
            branch="fixture-branch",
            changes=["bounded-change"],
            test_results={"focused": "PASS"},
            evidence=("fixture-evidence",),
            candidate_or_checkpoint_sha=candidate_sha,
            owner_gate=owner_gate,
            blockers=(),
            next_recommended_action="Return this packet to the integration queue.",
        )
        return packet.to_marked_text()

    def entry(self, queue: dict, work_item_id: str) -> dict:
        return next(e for e in queue["ENTRIES"] if e["WORK_ITEM_ID"] == work_item_id)

    # ------------------------------------------------------------------
    # Acceptance: two parallel fixtures
    # ------------------------------------------------------------------

    def test_two_non_overlapping_work_items_complete_flow(self) -> None:
        handoff = self.handoff()
        alpha = self.register(
            handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable"
        )
        beta = self.register(
            handoff, "fixture-beta", "GEMINI", ("docs/beta",), "Beta fixture deliverable"
        )
        self.assertEqual(alpha["lane"], "CODEX")
        self.assertEqual(beta["lane"], "GEMINI")
        self.assertNotEqual(alpha["work_item"]["SESSION_ID"], beta["work_item"]["SESSION_ID"])

        lane_alpha = handoff.start_lane("fixture-alpha")
        lane_beta = handoff.start_lane("fixture-beta")
        self.assertFalse(lane_alpha["idempotent"])
        self.assertTrue(handoff.start_lane("fixture-alpha")["idempotent"])

        returned_alpha = handoff.ingest_return(
            self.marked_packet(alpha["work_item"], candidate_sha=CAND_A_SHA),
            candidate_sha=CAND_A_SHA,
            candidate_tree=CAND_A_TREE,
        )
        returned_beta = handoff.ingest_return(
            self.marked_packet(beta["work_item"], candidate_sha=CAND_B_SHA),
            candidate_sha=CAND_B_SHA,
            candidate_tree=CAND_B_TREE,
        )
        self.assertEqual(returned_alpha["work_item_status"], "QUEUED")
        self.assertEqual(returned_beta["work_item_status"], "QUEUED")
        self.assertEqual(returned_alpha["next_gate"], "VERIFY")
        self.assertNotEqual(
            returned_alpha["packet_fingerprint"], returned_beta["packet_fingerprint"]
        )

        queue = handoff.integration_queue()
        self.assertEqual(queue["INTEGRATION_QUEUE_STATUS"], "READY_FOR_OWNER_REVIEW")
        self.assertEqual(len(queue["ENTRIES"]), 2)
        self.assertEqual(
            queue["LANES"], {"CODEX": ["fixture-alpha"], "GEMINI": ["fixture-beta"]}
        )
        entry_alpha = self.entry(queue, "fixture-alpha")
        entry_beta = self.entry(queue, "fixture-beta")
        # No ambiguity: explicit, distinct bindings and provenance.
        for entry in (entry_alpha, entry_beta):
            self.assertEqual(entry["PROJECT"], PROJECT)
            self.assertEqual(entry["WORKSTREAM"], WORKSTREAM)
            self.assertEqual(entry["BASE_SHA"], BASE_SHA)
            self.assertEqual(entry["BASE_TREE"], BASE_TREE)
            self.assertNotEqual(entry["CANDIDATE_SHA"], UNKNOWN)
            self.assertNotEqual(entry["CANDIDATE_TREE"], UNKNOWN)
            self.assertNotEqual(entry["PACKET_FINGERPRINT"], UNKNOWN)
            self.assertNotEqual(entry["SESSION_ID"], UNKNOWN)
        self.assertEqual(entry_alpha["EXECUTOR"], "CODEX")
        self.assertEqual(entry_beta["EXECUTOR"], "GEMINI")
        self.assertEqual(entry_alpha["CANDIDATE_SHA"], CAND_A_SHA)
        self.assertEqual(entry_beta["CANDIDATE_SHA"], CAND_B_SHA)
        self.assertFalse(queue["PROMOTED"])
        self.assertFalse(queue["MERGED"])

        verify = handoff.verify_integration_queue()
        self.assertEqual(verify["INTEGRATION_QUEUE_STATUS"], "READY_FOR_OWNER_REVIEW")
        for result in verify["ENTRIES"]:
            self.assertEqual(result["VERIFY_STATUS"], "VERIFIED")
            self.assertEqual(result["NEXT_GATE"], "OWNER_REVIEW")
        self.assertTrue(verify["OWNER_GATES_PRESERVED"])
        self.assertFalse(verify["OWNER_GATE_EXECUTED"])
        self.assertFalse(verify["PROMOTED"])
        self.assertFalse(verify["MERGED"])
        self.assertFalse(verify["DEPLOYED"])
        self.assertFalse(verify["RELEASED"])

    def test_replay_is_durable_across_instances(self) -> None:
        handoff = self.handoff()
        alpha = self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        handoff.start_lane("fixture-alpha")
        handoff.ingest_return(
            self.marked_packet(alpha["work_item"], candidate_sha=CAND_A_SHA),
            candidate_sha=CAND_A_SHA,
            candidate_tree=CAND_A_TREE,
        )
        fresh = WorkItemHandoff(self.root, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        queue = fresh.integration_queue()
        self.assertEqual(len(queue["ENTRIES"]), 1)
        entry = self.entry(queue, "fixture-alpha")
        self.assertEqual(entry["STATUS"], "QUEUED")
        self.assertEqual(entry["CANDIDATE_SHA"], CAND_A_SHA)
        self.assertEqual(queue["INTEGRATION_QUEUE_STATUS"], "READY_FOR_OWNER_REVIEW")
        # The ledger is the existing Control Tower / task-state ledger.
        ledger = self.root / ".p2p" / "state" / "execution-ledger.jsonl"
        events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
        event_types = [event.get("event_type") for event in events]
        self.assertIn("CONTROL_TOWER_SESSION_STARTED", event_types)
        self.assertIn("CONTROL_TOWER_RETURN_PACKET", event_types)
        self.assertIn("WORK_ITEM_REGISTERED", event_types)
        self.assertIn("WORK_ITEM_LANE_STARTED", event_types)
        self.assertIn("WORK_ITEM_RETURN", event_types)
        # No second state store was created.
        self.assertFalse((self.root / ".p2p" / "state" / "work-item-store.json").exists())

    def test_owner_gate_preserved_through_queue_and_verify(self) -> None:
        handoff = self.handoff()
        alpha = self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        beta = self.register(handoff, "fixture-beta", "GEMINI", ("docs/beta",), "Beta fixture deliverable")
        handoff.start_lane("fixture-alpha")
        handoff.start_lane("fixture-beta")
        handoff.ingest_return(
            self.marked_packet(
                alpha["work_item"],
                session_state="WAITING_OWNER_GATE",
                owner_gate=OWNER_GATE_A,
                candidate_sha=CAND_A_SHA,
            ),
            candidate_sha=CAND_A_SHA,
            candidate_tree=CAND_A_TREE,
        )
        handoff.ingest_return(
            self.marked_packet(beta["work_item"], candidate_sha=CAND_B_SHA),
            candidate_sha=CAND_B_SHA,
            candidate_tree=CAND_B_TREE,
        )
        queue = handoff.integration_queue()
        self.assertEqual(self.entry(queue, "fixture-alpha")["STATUS"], "WAITING_OWNER_GATE")
        self.assertEqual(self.entry(queue, "fixture-beta")["STATUS"], "QUEUED")
        self.assertEqual(
            [gate["WORK_ITEM_ID"] for gate in queue["OWNER_GATES"]], ["fixture-alpha"]
        )
        self.assertEqual(
            queue["OWNER_GATES"][0]["OWNER_GATE"], OWNER_GATE_A,
            "the Owner Gate object must be preserved verbatim",
        )
        self.assertEqual(queue["INTEGRATION_QUEUE_STATUS"], "READY_FOR_OWNER_REVIEW")
        verify = handoff.verify_integration_queue()
        alpha_result = next(r for r in verify["ENTRIES"] if r["WORK_ITEM_ID"] == "fixture-alpha")
        beta_result = next(r for r in verify["ENTRIES"] if r["WORK_ITEM_ID"] == "fixture-beta")
        self.assertEqual(alpha_result["VERIFY_STATUS"], "WAITING_OWNER_GATE")
        self.assertEqual(alpha_result["NEXT_GATE"], "OWNER_GATE")
        self.assertIn("OWNER_GATE_PENDING", alpha_result["REASONS"])
        self.assertEqual(beta_result["VERIFY_STATUS"], "VERIFIED")
        self.assertEqual(beta_result["NEXT_GATE"], "OWNER_REVIEW")
        self.assertFalse(verify["OWNER_GATE_EXECUTED"])

    # ------------------------------------------------------------------
    # Fail-safe: identity, binding, scope
    # ------------------------------------------------------------------

    def test_duplicate_identity_is_idempotent_and_conflict_is_rejected(self) -> None:
        handoff = self.handoff()
        first = self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        again = self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        self.assertTrue(again["idempotent"])
        with self.assertRaises(WorkItemHandoffError) as context:
            self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Different expected output")
        self.assertIn("WORK_ITEM_IDENTITY_CONFLICT", str(context.exception))
        with self.assertRaises(WorkItemHandoffError) as context:
            self.register(handoff, "fixture-alpha", "GEMINI", ("docs/beta",), "Alpha fixture deliverable")
        self.assertIn("WORK_ITEM_IDENTITY_CONFLICT", str(context.exception))
        # Same deterministic session id through an explicit override.
        with self.assertRaises(WorkItemHandoffError) as context:
            handoff.register_work_item(
                work_item_id="fixture-beta",
                project=PROJECT,
                workstream=WORKSTREAM,
                base_sha=BASE_SHA,
                base_tree=BASE_TREE,
                executor="GEMINI",
                scope=("docs/beta",),
                expected_output="Beta fixture deliverable",
                session_id=first["work_item"]["SESSION_ID"],
            )
        self.assertIn("WORK_ITEM_SESSION_CONFLICT", str(context.exception))

    def test_ambiguous_project_workstream_binding_rejected(self) -> None:
        handoff = self.handoff()
        with self.assertRaises(WorkItemHandoffError) as context:
            self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable", project="UNKNOWN")
        self.assertIn("AMBIGUOUS_PROJECT_WORKSTREAM_BINDING", str(context.exception))
        with self.assertRaises(WorkItemHandoffError) as context:
            self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable", workstream="")
        self.assertIn("AMBIGUOUS_PROJECT_WORKSTREAM_BINDING", str(context.exception))
        # Missing base identity is also an ambiguous start.
        with self.assertRaises(WorkItemHandoffError) as context:
            handoff.register_work_item(
                work_item_id="fixture-alpha",
                project=PROJECT,
                workstream=WORKSTREAM,
                base_sha=UNKNOWN,
                base_tree=BASE_TREE,
                executor="CODEX",
                scope=("docs/alpha",),
                expected_output="Alpha fixture deliverable",
            )
        self.assertIn("BASE_SHA_MUST_BE_EXPLICIT", str(context.exception))

    def test_dependency_binding_rules(self) -> None:
        handoff = self.handoff()
        with self.assertRaises(WorkItemHandoffError) as context:
            self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable", dependencies=("fixture-missing",))
        self.assertIn("WORK_ITEM_DEPENDENCY_NOT_REGISTERED", str(context.exception))
        self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        with self.assertRaises(WorkItemHandoffError) as context:
            self.register(
                handoff,
                "fixture-beta",
                "GEMINI",
                ("docs/beta",),
                "Beta fixture deliverable",
                dependencies=("fixture-alpha",),
                workstream="P2P-OTHER-STREAM",
            )
        self.assertIn("WORK_ITEM_DEPENDENCY_CROSS_BINDING", str(context.exception))
        with self.assertRaises(WorkItemHandoffError) as context:
            handoff.register_work_item(
                work_item_id="fixture-gamma",
                project=PROJECT,
                workstream=WORKSTREAM,
                base_sha=BASE_SHA,
                base_tree=BASE_TREE,
                executor="CODEX",
                scope=("docs/gamma",),
                dependencies=("fixture-gamma",),
                expected_output="Gamma fixture deliverable",
            )
        self.assertIn("WORK_ITEM_DEPENDENCY_SELF", str(context.exception))

    def test_scope_overlap_within_same_binding_rejected(self) -> None:
        handoff = self.handoff()
        self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        with self.assertRaises(WorkItemHandoffError) as context:
            self.register(handoff, "fixture-beta", "GEMINI", ("docs/alpha/sub",), "Beta fixture deliverable")
        self.assertIn("WORK_ITEM_SCOPE_OVERLAP", str(context.exception))
        with self.assertRaises(WorkItemHandoffError) as context:
            self.register(handoff, "fixture-beta", "GEMINI", ("docs/*",), "Beta fixture deliverable")
        self.assertIn("WORK_ITEM_SCOPE_OVERLAP", str(context.exception))
        # The same scope in a different workstream is a different binding.
        self.register(
            handoff,
            "fixture-beta",
            "GEMINI",
            ("docs/alpha",),
            "Beta fixture deliverable",
            workstream="P2P-OTHER-STREAM",
        )

    # ------------------------------------------------------------------
    # Fail-safe: stale base, missing candidate, order, orphan
    # ------------------------------------------------------------------

    def test_stale_base_is_fail_safe(self) -> None:
        handoff = self.handoff()
        alpha = self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        handoff.start_lane("fixture-alpha")
        returned = handoff.ingest_return(
            self.marked_packet(alpha["work_item"], candidate_sha=CAND_A_SHA),
            candidate_sha=CAND_A_SHA,
            candidate_tree=CAND_A_TREE,
            current_canonical_base_sha=ADVANCED_SHA,
            current_canonical_base_tree=ADVANCED_TREE,
        )
        self.assertEqual(returned["work_item_status"], "STALE_BASE")
        self.assertEqual(returned["canonical_relation"], "STALE")
        self.assertEqual(returned["next_gate"], "RECONCILIATION")
        queue = handoff.integration_queue(
            current_canonical_base_sha=ADVANCED_SHA,
            current_canonical_base_tree=ADVANCED_TREE,
        )
        self.assertEqual(queue["INTEGRATION_QUEUE_STATUS"], "RECONCILIATION_REQUIRED")
        self.assertEqual(self.entry(queue, "fixture-alpha")["STATUS"], "STALE_BASE")
        verify = handoff.verify_integration_queue(
            current_canonical_base_sha=ADVANCED_SHA,
            current_canonical_base_tree=ADVANCED_TREE,
        )
        result = next(r for r in verify["ENTRIES"] if r["WORK_ITEM_ID"] == "fixture-alpha")
        self.assertEqual(result["VERIFY_STATUS"], "STALE_BASE")
        self.assertIn("CANONICAL_BASE_NOT_CURRENT", result["REASONS"])
        self.assertEqual(verify["INTEGRATION_QUEUE_STATUS"], "RECONCILIATION_REQUIRED")
        self.assertFalse(verify["PROMOTED"])

    def test_return_from_a_different_base_is_rejected(self) -> None:
        handoff = self.handoff()
        alpha = self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        handoff.start_lane("fixture-alpha")
        with self.assertRaises(WorkItemHandoffError) as context:
            handoff.ingest_return(
                self.marked_packet(
                    alpha["work_item"],
                    candidate_sha=CAND_A_SHA,
                    base_sha=ADVANCED_SHA,
                    base_tree=ADVANCED_TREE,
                ),
                candidate_sha=CAND_A_SHA,
                candidate_tree=CAND_A_TREE,
            )
        self.assertIn("WORK_ITEM_BASE_MISMATCH", str(context.exception))

    def test_missing_candidate_identity_rejected(self) -> None:
        handoff = self.handoff()
        alpha = self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        handoff.start_lane("fixture-alpha")
        with self.assertRaises(WorkItemHandoffError) as context:
            handoff.ingest_return(
                self.marked_packet(alpha["work_item"]),
                candidate_sha=UNKNOWN,
                candidate_tree=CAND_A_TREE,
            )
        self.assertIn("CANDIDATE_SHA_MUST_BE_EXPLICIT", str(context.exception))
        with self.assertRaises(WorkItemHandoffError) as context:
            handoff.ingest_return(
                self.marked_packet(alpha["work_item"], candidate_sha=CAND_B_SHA),
                candidate_sha=CAND_A_SHA,
                candidate_tree=CAND_A_TREE,
            )
        self.assertIn("WORK_ITEM_CANDIDATE_MISMATCH", str(context.exception))

    def test_lane_order_fail_closed(self) -> None:
        handoff = self.handoff()
        alpha = self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        with self.assertRaises(WorkItemHandoffError) as context:
            handoff.ingest_return(
                self.marked_packet(alpha["work_item"], candidate_sha=CAND_A_SHA),
                candidate_sha=CAND_A_SHA,
                candidate_tree=CAND_A_TREE,
            )
        self.assertIn("WORK_ITEM_RETURN_BEFORE_LANE_START", str(context.exception))
        handoff.start_lane("fixture-alpha")
        handoff.ingest_return(
            self.marked_packet(alpha["work_item"], candidate_sha=CAND_A_SHA),
            candidate_sha=CAND_A_SHA,
            candidate_tree=CAND_A_TREE,
        )
        with self.assertRaises(WorkItemHandoffError) as context:
            handoff.start_lane("fixture-alpha")
        self.assertIn("WORK_ITEM_LANE_START_AFTER_RETURN", str(context.exception))
        with self.assertRaises(WorkItemHandoffError) as context:
            handoff.start_lane("fixture-unknown")
        self.assertIn("WORK_ITEM_NOT_FOUND", str(context.exception))

    def test_orphan_return_rejected(self) -> None:
        handoff = self.handoff()
        orphan = {
            "SESSION_ID": "session-codex-orphan-000000000000",
            "EXECUTOR": "CODEX",
            "WORKSTREAM": WORKSTREAM,
            "EXPECTED_OUTPUT": "Orphan deliverable",
        }
        with self.assertRaises((BindingError, WorkItemHandoffError, ControlTowerHandoffError)):
            handoff.ingest_return(
                self.marked_packet(orphan, candidate_sha=CAND_A_SHA),
                candidate_sha=CAND_A_SHA,
                candidate_tree=CAND_A_TREE,
            )

    # ------------------------------------------------------------------
    # Dependencies and ordering
    # ------------------------------------------------------------------

    def test_dependency_ordering_and_verify(self) -> None:
        handoff = self.handoff()
        alpha = self.register(handoff, "fixture-alpha", "CODEX", ("docs/alpha",), "Alpha fixture deliverable")
        beta = self.register(
            handoff,
            "fixture-beta",
            "GEMINI",
            ("docs/beta",),
            "Beta fixture deliverable",
            dependencies=("fixture-alpha",),
        )
        handoff.start_lane("fixture-alpha")
        handoff.start_lane("fixture-beta")
        handoff.ingest_return(
            self.marked_packet(beta["work_item"], candidate_sha=CAND_B_SHA),
            candidate_sha=CAND_B_SHA,
            candidate_tree=CAND_B_TREE,
        )
        queue = handoff.integration_queue()
        order = [entry["WORK_ITEM_ID"] for entry in queue["ENTRIES"]]
        self.assertEqual(order, ["fixture-alpha", "fixture-beta"])
        verify = handoff.verify_integration_queue()
        beta_result = next(r for r in verify["ENTRIES"] if r["WORK_ITEM_ID"] == "fixture-beta")
        self.assertEqual(beta_result["VERIFY_STATUS"], "NOT_READY")
        self.assertIn("DEPENDENCY_NOT_VERIFIED:fixture-alpha", beta_result["REASONS"])
        self.assertEqual(verify["INTEGRATION_QUEUE_STATUS"], "IN_PROGRESS")
        handoff.ingest_return(
            self.marked_packet(alpha["work_item"], candidate_sha=CAND_A_SHA),
            candidate_sha=CAND_A_SHA,
            candidate_tree=CAND_A_TREE,
        )
        verify = handoff.verify_integration_queue()
        self.assertEqual(verify["INTEGRATION_QUEUE_STATUS"], "READY_FOR_OWNER_REVIEW")
        for result in verify["ENTRIES"]:
            self.assertEqual(result["VERIFY_STATUS"], "VERIFIED")

    # ------------------------------------------------------------------
    # CLI smoke
    # ------------------------------------------------------------------

    def _cli(self, *args: str) -> subprocess.CompletedProcess:
        command = [sys.executable, str(SCRIPTS_ROOT / "p2p_work_item.py"), "--root", str(self.root), *args]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def test_cli_register_lane_return_queue_verify_smoke(self) -> None:
        base = [
            "--current-canonical-base-sha", BASE_SHA,
            "--current-canonical-base-tree", BASE_TREE,
            "--json",
        ]
        for work_item_id, executor, scope, output in (
            ("fixture-alpha", "CODEX", "docs/alpha", "Alpha fixture deliverable"),
            ("fixture-beta", "GEMINI", "docs/beta", "Beta fixture deliverable"),
        ):
            result = self._cli(
                "register",
                "--work-item-id", work_item_id,
                "--project", PROJECT,
                "--workstream", WORKSTREAM,
                "--base-sha", BASE_SHA,
                "--base-tree", BASE_TREE,
                "--executor", executor,
                "--scope", scope,
                "--expected-output", output,
                *base,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["lane"], executor)
            self.assertEqual(payload["next_gate"], "LANE")
            result = self._cli("lane", "--work-item-id", work_item_id, *base)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["next_gate"], "RETURN_PACKET")

        alpha_payload = json.loads(
            self._cli(
                "register",
                "--work-item-id", "fixture-alpha",
                "--project", PROJECT,
                "--workstream", WORKSTREAM,
                "--base-sha", BASE_SHA,
                "--base-tree", BASE_TREE,
                "--executor", "CODEX",
                "--scope", "docs/alpha",
                "--expected-output", "Alpha fixture deliverable",
                *base,
            ).stdout
        )
        self.assertTrue(alpha_payload["idempotent"])
        alpha_item = alpha_payload["work_item"]
        beta_item = json.loads(
            self._cli(
                "register",
                "--work-item-id", "fixture-beta",
                "--project", PROJECT,
                "--workstream", WORKSTREAM,
                "--base-sha", BASE_SHA,
                "--base-tree", BASE_TREE,
                "--executor", "GEMINI",
                "--scope", "docs/beta",
                "--expected-output", "Beta fixture deliverable",
                *base,
            ).stdout
        )["work_item"]

        for item, candidate_sha, candidate_tree in (
            (alpha_item, CAND_A_SHA, CAND_A_TREE),
            (beta_item, CAND_B_SHA, CAND_B_TREE),
        ):
            packet_file = self.root / f"{item['WORK_ITEM_ID']}-return.txt"
            packet_file.write_text(self.marked_packet(item, candidate_sha=candidate_sha), encoding="utf-8")
            result = self._cli(
                "return",
                "--response-file", str(packet_file),
                "--candidate-sha", candidate_sha,
                "--candidate-tree", candidate_tree,
                *base,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["work_item_status"], "QUEUED")

        queue = json.loads(self._cli("queue", *base).stdout)
        self.assertEqual(queue["INTEGRATION_QUEUE_STATUS"], "READY_FOR_OWNER_REVIEW")
        self.assertEqual(len(queue["ENTRIES"]), 2)
        verify = json.loads(self._cli("verify", *base).stdout)
        self.assertEqual(verify["INTEGRATION_QUEUE_STATUS"], "READY_FOR_OWNER_REVIEW")
        self.assertTrue(verify["OWNER_GATES_PRESERVED"])


if __name__ == "__main__":
    unittest.main()
