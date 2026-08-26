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
    ControlTower,
    ControlTowerReturnPacket,
    SessionBinding,
    create_return_packet,
    parse_return_packet,
)
from p2p_capabilities.task_state import TaskPlan, TaskStateStore  # noqa: E402


BASE_SHA = "a" * 40
BASE_TREE = "b" * 40
STALE_SHA = "c" * 40
STALE_TREE = "d" * 40


class DurableControlTowerTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_parent = REPO_ROOT / ".tmp"
        temp_parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="ct01-durable-", dir=str(temp_parent))
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def binding(self, host: str = "CODEX", goal_id: str = "P2P-CT01") -> SessionBinding:
        return SessionBinding(
            session_id=f"ct01-{host.lower()}-{goal_id.lower()}-session",
            host=host,
            goal_id=goal_id,
            goal="Durable Control Tower Session Handoff Integration",
        )

    def packet(
        self,
        binding: SessionBinding,
        state: str = "READY",
        *,
        base_sha: str = BASE_SHA,
        base_tree: str = BASE_TREE,
        changes: object = ("bounded-change",),
        owner_gate: object = None,
        blockers: tuple[str, ...] = (),
        next_action: str = "Run the next bounded verification.",
    ) -> ControlTowerReturnPacket:
        return create_return_packet(
            binding,
            session_state=state,
            canonical_base_sha=base_sha,
            canonical_base_tree=base_tree,
            canonical_relation="CURRENT",
            worktree="fixture-worktree",
            branch="fixture-branch",
            changes=changes,
            test_results={"focused": "PASS"},
            evidence=("fixture-evidence",),
            candidate_or_checkpoint_sha="UNKNOWN",
            owner_gate=owner_gate,
            blockers=blockers,
            next_recommended_action=next_action,
        )

    def tower(self) -> ControlTower:
        return ControlTower(
            self.root,
            current_canonical_base_sha=BASE_SHA,
            current_canonical_base_tree=BASE_TREE,
        )

    def register(self, binding: SessionBinding) -> None:
        result = self.tower().start_session(
            binding,
            task_id="CT01-TASK",
            worktree="fixture-worktree",
            branch="fixture-branch",
            canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE,
            acceptance_criteria=("Focused proof passes.",),
        )
        self.assertEqual("PASS", result["status"])

    def test_git_sha1_packet_round_trip_and_markers_are_supported(self) -> None:
        binding = self.binding()
        packet = self.packet(binding)
        restored = ControlTowerReturnPacket.from_mapping(packet.to_dict())
        marked = packet.to_marked_text()
        self.assertEqual(BASE_SHA, restored.canonical_base_sha)
        self.assertEqual(BASE_TREE, restored.canonical_base_tree)
        self.assertEqual(packet, parse_return_packet(marked))

    def test_session_registration_replays_from_existing_ledger(self) -> None:
        binding = self.binding()
        self.register(binding)
        ledger = self.root / ".p2p" / "state" / "execution-ledger.jsonl"
        lines = ledger.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertEqual("CONTROL_TOWER_SESSION_STARTED", json.loads(lines[0])["event_type"])
        snapshot = self.tower().snapshot()
        self.assertEqual("ACTIVE", snapshot["HOST_LANES"]["CODEX"]["CONTROL_TOWER_STATUS"])
        self.assertEqual("NO", snapshot["PERSISTENCE"]["SECOND_STORE_CREATED"])
        self.assertFalse((self.root / ".p2p" / "state" / "control-tower.json").exists())

    def test_replay_is_idempotent_and_raw_response_is_not_persisted(self) -> None:
        binding = self.binding()
        self.register(binding)
        packet = self.packet(binding)
        first = self.tower().ingest_packet(packet)
        ledger = self.root / ".p2p" / "state" / "execution-ledger.jsonl"
        first_raw = ledger.read_text(encoding="utf-8")
        response = "UNIQUE RAW EXECUTOR TRANSCRIPT\n" + packet.to_marked_text()
        second = self.tower().ingest_response(
            response,
            current_canonical_base_sha=BASE_SHA,
            current_canonical_base_tree=BASE_TREE,
        )
        second_raw = ledger.read_text(encoding="utf-8")
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first_raw, second_raw)
        self.assertNotIn("UNIQUE RAW EXECUTOR TRANSCRIPT", second_raw)

    def test_binding_conflict_and_different_replay_fail_closed(self) -> None:
        binding = self.binding()
        self.register(binding)
        packet = self.packet(binding)
        self.tower().ingest_packet(packet)
        wrong_mapping = packet.to_dict()
        wrong_mapping["HOST"] = "MANUS"
        wrong = ControlTowerReturnPacket.from_mapping(wrong_mapping)
        with self.assertRaises(BindingError):
            self.tower().ingest_packet(wrong)
        with self.assertRaises(BindingError):
            self.tower().ingest_packet(self.packet(binding, changes=("different-change",)))

    def test_host_lanes_stale_base_and_promotion_claim_remain_bounded(self) -> None:
        codex = self.binding("CODEX", "P2P-CT01-CODEX")
        manus = self.binding("MANUS", "P2P-CT01-MANUS")
        self.register(codex)
        self.register(manus)
        tower = self.tower()
        tower.ingest_packet(self.packet(codex, changes=("executor says promoted",)))
        stale = tower.ingest_packet(
            self.packet(manus, base_sha=STALE_SHA, base_tree=STALE_TREE, state="READY")
        )
        self.assertEqual("STALE", stale["reconciliation"]["CANONICAL_RELATION"])
        self.assertEqual("RECONCILIATION_REQUIRED", stale["reconciliation"]["CONTROL_TOWER_STATUS"])
        snapshot = stale["snapshot"]
        self.assertEqual("READY", snapshot["HOST_LANES"]["CODEX"]["SESSION_STATE"])
        self.assertEqual("RECONCILIATION_REQUIRED", snapshot["HOST_LANES"]["MANUS"]["CONTROL_TOWER_STATUS"])
        self.assertFalse(snapshot["PROMOTION"]["PROMOTED"])
        self.assertTrue(snapshot["HOST_LANES"]["CODEX"]["PROMOTION_CLAIM_DETECTED"])

    def test_waiting_owner_and_failed_sessions_are_preserved(self) -> None:
        waiting = self.binding("CODEX", "P2P-CT01-OWNER")
        failed = self.binding("GEMINI", "P2P-CT01-FAILED")
        self.register(waiting)
        self.register(failed)
        tower = self.tower()
        owner_result = tower.ingest_packet(
            self.packet(
                waiting,
                state="WAITING_OWNER_GATE",
                owner_gate={"GATE_ID": "OWNER-CT01", "STATUS": "PENDING"},
                next_action="Wait for the Owner decision.",
            )
        )
        failed_result = tower.ingest_packet(
            self.packet(
                failed,
                state="FAILED",
                blockers=("Executor failed before completion.",),
                next_action="Review the failure before retry.",
            )
        )
        self.assertEqual("WAITING_OWNER_GATE", owner_result["snapshot"]["HOST_LANES"]["CODEX"]["SESSION_STATE"])
        self.assertEqual("FAILED", failed_result["snapshot"]["HOST_LANES"]["GEMINI"]["SESSION_STATE"])
        self.assertEqual("REVIEW_FAILURE_AND_RECONCILE_BEFORE_RETRY", failed_result["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])
        self.assertFalse(failed_result["snapshot"]["PROMOTION"]["PROMOTED"])

    def test_cli_start_and_ingest_smoke(self) -> None:
        script = REPO_ROOT / "scripts" / "p2p_control_tower.py"
        binding = self.binding("CODEX", "P2P-CT01-CLI")
        start = subprocess.run(
            [
                sys.executable,
                str(script),
                "--root",
                str(self.root),
                "--json",
                "start",
                "--host",
                binding.host,
                "--goal-id",
                binding.goal_id,
                "--goal",
                binding.goal,
                "--session-id",
                binding.session_id,
                "--canonical-base-sha",
                BASE_SHA,
                "--canonical-base-tree",
                BASE_TREE,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, start.returncode, start.stderr)
        self.assertEqual("PASS", json.loads(start.stdout)["status"])
        response_path = self.root / "executor-response.txt"
        response_path.write_text(self.packet(binding).to_marked_text(), encoding="utf-8")
        ingest = subprocess.run(
            [
                sys.executable,
                str(script),
                "--root",
                str(self.root),
                "--current-canonical-base-sha",
                BASE_SHA,
                "--current-canonical-base-tree",
                BASE_TREE,
                "--json",
                "ingest",
                "--response-file",
                str(response_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, ingest.returncode, ingest.stderr)
        ingested = json.loads(ingest.stdout)
        self.assertEqual("PASS", ingested["status"])
        self.assertEqual("READY", ingested["snapshot"]["HOST_LANES"]["CODEX"]["SESSION_STATE"])

    def test_next_discovery_is_unknown_without_task_state(self) -> None:
        result = ControlTower(self.root).recommend_next_session("CODEX")
        self.assertEqual("UNKNOWN", result["status"])
        self.assertEqual("TASK_STATE_NOT_INITIALIZED", result["reason"])
        self.assertFalse((self.root / ".p2p" / "state" / "control-tower.json").exists())

    def test_next_discovery_uses_task_state_without_automatic_start(self) -> None:
        now = "2026-08-26T00:00:00+00:00"
        plan = TaskPlan.from_goal(
            {
                "goal_id": "goal-ct01",
                "scope": ["bounded Control Tower verification"],
                "out_of_scope": ["promotion and deployment"],
            },
            [
                {
                    "task_id": "ct01-ready",
                    "title": "Run CT01 verification",
                    "purpose": "Run the bounded Control Tower verification.",
                    "status": "READY",
                    "scope": ["bounded Control Tower verification"],
                    "acceptance_requirements": ["Focused proof passes."],
                    "required_evidence": ["focused-proof"],
                }
            ],
            now=now,
        )
        TaskStateStore(self.root).initialize(plan, at=now)
        tower = ControlTower(self.root)
        recommendation = tower.recommend_next_session("MANUS", worktree="fixture-worktree", branch="fixture-branch")
        self.assertEqual("PASS", recommendation["status"])
        self.assertEqual("ct01-ready", recommendation["task_id"])
        self.assertFalse((self.root / ".p2p" / "state" / "control-tower.json").exists())
        started = tower.start_next_session("MANUS", worktree="fixture-worktree", branch="fixture-branch")
        self.assertEqual("PASS", started["status"])
        self.assertEqual("ct01-ready", started["task_id"])
        self.assertIn("Focused proof passes.", started["recommendation"]["PROMPT"])


if __name__ == "__main__":
    unittest.main()
