from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SYSTEM))

from p2p_capabilities.native_goal_bridge import (  # noqa: E402
    CLAUDE_CODE,
    CODEX_CLI,
    NativeGoalBridgeError,
    build_contract_replay_manifest,
    build_native_goal_projection,
)

WORKTREE_PATH = ROOT / "scripts" / "p2p_worktree_evidence.py"
spec = importlib.util.spec_from_file_location("p2p_worktree_evidence", WORKTREE_PATH)
assert spec and spec.loader
worktree = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worktree)


BASELINE = "a" * 40


def sample_goal() -> dict:
    return {
        "schema": "p2p-autopilot-goal/1",
        "goal_id": "goal-supergoal-adoption",
        "goal_version": "v1",
        "plan_task_ids": ["task-a", "task-b"],
        "status": "APPROVED",
    }


def _task(task_id: str, *, dependency: str | None = None) -> dict:
    required = f"evidence:{task_id}"
    return {
        "task_id": task_id,
        "goal_id": "goal-supergoal-adoption",
        "title": f"Title {task_id}",
        "purpose": f"Purpose {task_id}",
        "status": "READY",
        "dependencies": [dependency] if dependency else [],
        "scope": [f"scope:{task_id}"],
        "non_scope": [f"non-scope:{task_id}"],
        "acceptance_requirements": [f"accept:{task_id}"],
        "required_evidence": [required],
        "permission_needs": ["sandboxed-default"],
        "required_capabilities": [],
        "optional_capabilities": [],
        "context_refs": [],
        "output_refs": [],
        "requirement_refs": [],
        "decision_refs": [],
    }


def sample_tasks() -> dict:
    return {
        "schema": "p2p-task-plan/1",
        "goal_id": "goal-supergoal-adoption",
        "tasks": [_task("task-a"), _task("task-b", dependency="task-a")],
    }


class TestNativeGoalProjection(unittest.TestCase):
    def test_claude_projection_preserves_p2p_authority(self) -> None:
        result = build_native_goal_projection(
            CLAUDE_CODE, sample_goal(), sample_tasks(), baseline_ref=BASELINE
        )
        self.assertTrue(result["command"].startswith("/goal "))
        self.assertLessEqual(result["condition_chars"], 4000)
        semantics = result["host_semantics"]
        self.assertTrue(semantics["automatic_turn_continuation_documented"])
        self.assertTrue(semantics["separate_completion_evaluator_documented"])
        self.assertEqual(semantics["evaluator_observation_scope"], "TRANSCRIPT_ONLY")
        self.assertFalse(result["native_goal_evaluator_is_acceptance_authority"])
        replay = result["contract_replay"]
        self.assertIsNone(replay["fixed_retry_hard_stop"])
        self.assertEqual(replay["recovery_policy"], "P2P_ADAPTIVE_FAILURE_CLASSIFICATION")
        self.assertIn("do not use a fixed retry count", result["condition"])
        self.assertIn("scripts/p2p_worktree_evidence.py summary", result["condition"])

    def test_codex_projection_does_not_invent_claude_semantics(self) -> None:
        result = build_native_goal_projection(CODEX_CLI, sample_goal(), sample_tasks())
        semantics = result["host_semantics"]
        self.assertEqual(semantics["documented_semantics"], "PERSISTENT_ACTIVE_CHAT_OBJECTIVE")
        self.assertFalse(semantics["automatic_turn_continuation_documented"])
        self.assertFalse(semantics["separate_completion_evaluator_documented"])
        self.assertEqual(semantics["evaluator_observation_scope"], "NOT_CLAIMED")

    def test_contract_replay_preserves_original_order_and_boundaries(self) -> None:
        replay = build_contract_replay_manifest(sample_goal(), sample_tasks())
        self.assertEqual(replay["task_order"], ["task-a", "task-b"])
        self.assertEqual(replay["tasks"][0]["acceptance_requirements"], ["accept:task-a"])
        self.assertEqual(replay["tasks"][0]["required_evidence"], ["evidence:task-a"])
        self.assertEqual(replay["tasks"][1]["scope"], ["scope:task-b"])
        self.assertTrue(all(len(task["contract_fingerprint"]) == 64 for task in replay["tasks"]))
        self.assertTrue(replay["projection_only"])
        self.assertFalse(replay["native_goal_evaluator_is_authority"])

    def test_contract_replay_is_deterministic(self) -> None:
        first = build_contract_replay_manifest(sample_goal(), sample_tasks())
        second = build_contract_replay_manifest(sample_goal(), sample_tasks())
        self.assertEqual(first["manifest_fingerprint"], second["manifest_fingerprint"])
        self.assertEqual(
            [t["contract_fingerprint"] for t in first["tasks"]],
            [t["contract_fingerprint"] for t in second["tasks"]],
        )

    def test_goal_task_set_mismatch_fails_closed(self) -> None:
        tasks = sample_tasks()
        tasks["tasks"] = tasks["tasks"][:1]
        with self.assertRaisesRegex(NativeGoalBridgeError, "GOAL_TASK_SET_MISMATCH"):
            build_contract_replay_manifest(sample_goal(), tasks)

    def test_baseline_must_be_exact_full_git_oid(self) -> None:
        with self.assertRaisesRegex(NativeGoalBridgeError, "BASELINE_REF_MUST_BE_FULL_GIT_COMMIT_OID"):
            build_native_goal_projection(CLAUDE_CODE, sample_goal(), sample_tasks(), baseline_ref="HEAD~1")


class TestCompleteWorktreeEvidence(unittest.TestCase):
    def git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def build_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path, str]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        self.git(root, "init")
        self.git(root, "config", "user.email", "test@example.com")
        self.git(root, "config", "user.name", "P2P Test")
        (root / "unstaged.txt").write_text("one\n", encoding="utf-8")
        (root / "staged.txt").write_text("one\n", encoding="utf-8")
        (root / "deleted.txt").write_text("one\n", encoding="utf-8")
        (root / "unchanged.txt").write_text("one\n", encoding="utf-8")
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "baseline")
        baseline = self.git(root, "rev-parse", "HEAD")

        (root / "committed-after.txt").write_text("committed later\n", encoding="utf-8")
        self.git(root, "add", "committed-after.txt")
        self.git(root, "commit", "-m", "after baseline")

        (root / "unstaged.txt").write_text("two\n", encoding="utf-8")
        (root / "staged.txt").write_text("two\n", encoding="utf-8")
        self.git(root, "add", "staged.txt")
        (root / "deleted.txt").unlink()
        (root / "untracked.txt").write_text("new\n", encoding="utf-8")
        return td, root, baseline

    def test_summary_sees_complete_worktree_not_only_head(self) -> None:
        td, root, baseline = self.build_repo()
        try:
            result = worktree.complete_worktree_summary(root, baseline)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(
                set(result["changed_files"]),
                {
                    "committed-after.txt",
                    "unstaged.txt",
                    "staged.txt",
                    "deleted.txt",
                    "untracked.txt",
                },
            )
            self.assertEqual(result["changed_file_count"], 5)
            self.assertFalse(result["clean_vs_baseline"])
            self.assertFalse(result["working_tree_clean_now"])
            self.assertTrue(result["includes_committed_after_baseline"])
            self.assertTrue(result["includes_staged"])
            self.assertTrue(result["includes_unstaged"])
            self.assertTrue(result["includes_deleted_tracked"])
            self.assertTrue(result["includes_untracked"])
            self.assertFalse(result["file_contents_read"])
            self.assertFalse(result["repository_mutated"])
            self.assertFalse(result["acceptance_authority"])
        finally:
            td.cleanup()

    def test_deliverable_states_are_explicit(self) -> None:
        td, root, baseline = self.build_repo()
        try:
            self.assertEqual(
                worktree.deliverable_evidence(root, baseline, "untracked.txt")["state"],
                "UNTRACKED_NEW",
            )
            deleted = worktree.deliverable_evidence(root, baseline, "deleted.txt")
            self.assertEqual(deleted["state"], "DELETED_VS_BASELINE")
            self.assertFalse(deleted["present"])
            unchanged = worktree.deliverable_evidence(root, baseline, "unchanged.txt")
            self.assertEqual(unchanged["state"], "EXISTS_UNCHANGED")
            self.assertFalse(unchanged["produced_or_changed_since_baseline"])
            missing = worktree.deliverable_evidence(root, baseline, "missing.txt")
            self.assertEqual(missing["state"], "MISSING")
            self.assertFalse(missing["present"])
        finally:
            td.cleanup()

    def test_invalid_baseline_fails_closed(self) -> None:
        td, root, _baseline = self.build_repo()
        try:
            with self.assertRaisesRegex(worktree.WorktreeEvidenceError, "BASELINE_MUST_BE_FULL_GIT_COMMIT_OID"):
                worktree.complete_worktree_summary(root, "HEAD~1")
            with self.assertRaises(worktree.WorktreeEvidenceError):
                worktree.complete_worktree_summary(root, "f" * 40)
        finally:
            td.cleanup()

    def test_deliverable_rejects_path_escape(self) -> None:
        td, root, baseline = self.build_repo()
        try:
            with self.assertRaisesRegex(worktree.WorktreeEvidenceError, "PATH_MUST_BE_PROJECT_RELATIVE"):
                worktree.deliverable_evidence(root, baseline, "../outside.txt")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
