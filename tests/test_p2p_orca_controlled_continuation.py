from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import fw06_operational_resilience as fw06  # noqa: E402
from p2p_capabilities.bounded_delegation import PermissionEnvelope  # noqa: E402
from p2p_capabilities.evidence import EvidenceClaim  # noqa: E402
from p2p_capabilities.foreground_execution import (  # noqa: E402
    ExecutionBudget,
    ForegroundExecutionController,
    ForegroundPermissionError,
)
from p2p_capabilities import orca_candidate_fanout as orca  # noqa: E402
from p2p_capabilities.task_state import TaskPlan, TaskStateStore  # noqa: E402


NOW = "2026-10-03T00:00:00+00:00"
WRITE_PERMISSION = {"WRITE": {"status": "GRANTED", "source_ref": "owner/issue-295-test"}}


class OrcaControlledContinuationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(
            prefix="orca-c08-controlled-continuation-", dir=REPO_ROOT
        )
        self.root = Path(self._temporary.name)
        self.source_repo = self.root / "source-repo"
        self.source_repo.mkdir()
        self._git("init", "--initial-branch=main", str(self.source_repo))
        self._git("-C", str(self.source_repo), "config", "user.name", "ORCA C08 test")
        self._git("-C", str(self.source_repo), "config", "user.email", "orca-c08@example.invalid")
        (self.source_repo / "README.md").write_text("synthetic C08 composition fixture\n", encoding="utf-8")
        self._git("-C", str(self.source_repo), "add", "README.md")
        self._git("-C", str(self.source_repo), "commit", "-m", "synthetic C08 composition fixture")
        self.base_revision = self._git("-C", str(self.source_repo), "rev-parse", "HEAD").stdout.strip()
        self.fw06_root = self.root / "fw06-state"
        self.worktree_parent = self.root / "candidate-worktrees"

    def tearDown(self) -> None:
        self._temporary.cleanup()

    @staticmethod
    def _git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True
        )

    @staticmethod
    def _goal(goal_id: str) -> dict[str, object]:
        return {
            "goal_id": goal_id,
            "scope": ["output.txt"],
            "out_of_scope": [".p2p/state", "network", "release", "promotion"],
            "completion_criteria": [
                {"criterion_id": "candidate-output-verified", "description": "Scoped candidate output is verified."}
            ],
        }

    def _controller(self, root: Path, candidate_name: str) -> ForegroundExecutionController:
        goal_id = "goal-orca-c08-composition"
        task_id = f"candidate-{candidate_name}"
        plan = TaskPlan.from_goal(
            self._goal(goal_id),
            [{
                "task_id": task_id,
                "title": f"Synthetic ORCA candidate {candidate_name}",
                "purpose": "Exercise bounded C12 continuation in one isolated candidate worktree.",
                "scope": ["output.txt"],
                "acceptance_requirements": [f"acceptance-{candidate_name}"],
                "required_evidence": [f"evidence-{candidate_name}"],
                "permission_needs": ["WRITE"],
            }],
            now=NOW,
        )
        TaskStateStore(root).initialize(plan, at=NOW)
        return ForegroundExecutionController(root)

    @staticmethod
    def _claim(task_name: str, output_path: Path) -> EvidenceClaim:
        output_fingerprint = hashlib.sha256(output_path.read_bytes()).hexdigest()
        evidence_ref = f"evidence-{task_name}"
        return EvidenceClaim(
            claim="Independent read-only verification confirmed the scoped synthetic output.",
            required_evidence=(evidence_ref,),
            actual_evidence=(
                {
                    "source": "tests/test_p2p_orca_controlled_continuation.py",
                    "evidence_ref": evidence_ref,
                    "origin": "RUNTIME_EVIDENCE",
                    "observed_at": NOW,
                    "freshness": "CURRENT",
                    "scope": ["output.txt"],
                    "source_binding": f"synthetic-candidate-{task_name}",
                    "fingerprint": output_fingerprint,
                },
            ),
            status="VERIFIED",
        )

    def test_completed_candidate_is_untouched_while_interrupted_candidate_resumes_from_durable_state(self) -> None:
        parent_permission = PermissionEnvelope(
            grants=("READ", "WRITE"), scope=("output.txt",)
        )
        permission_a = PermissionEnvelope(grants=("WRITE",), scope=("output.txt",))
        permission_b = PermissionEnvelope(grants=("WRITE",), scope=("output.txt",))
        candidate_a = orca.CandidateSpec(
            spec_ref="candidate/a",
            base_revision=self.base_revision,
            permission_fingerprint=orca.permission_fingerprint(permission_a),
            candidate_ordinal=0,
            acceptance_fingerprint="acceptance-a",
            permission=permission_a,
        )
        candidate_b = orca.CandidateSpec(
            spec_ref="candidate/b",
            base_revision=self.base_revision,
            permission_fingerprint=orca.permission_fingerprint(permission_b),
            candidate_ordinal=1,
            acceptance_fingerprint="acceptance-b",
            permission=permission_b,
        )
        permission_fp_a_before = orca.permission_fingerprint(candidate_a.permission)
        permission_fp_b_before = orca.permission_fingerprint(candidate_b.permission)
        self.assertTrue(candidate_a.permission.subset_of(parent_permission))
        self.assertTrue(candidate_b.permission.subset_of(parent_permission))

        binding_a, binding_b = orca.create_candidate_workspace_bindings(
            [candidate_a, candidate_b],
            parent_permission,
            root=self.fw06_root,
            repo_path=self.source_repo,
            worktree_parent=self.worktree_parent,
            project_id="project-orca-c08-proof",
            owner_task_id="task-orca-c08-proof",
            creator="orca-c08-composition-test",
        )
        rows = {
            row["workspace_id"]: row
            for row in fw06.list_all_workspaces(self.fw06_root, "project-orca-c08-proof")
        }
        self.assertEqual(rows[binding_a.workspace_id]["mutation_policy"], "SYNTHETIC_ONLY")
        self.assertEqual(rows[binding_b.workspace_id]["mutation_policy"], "SYNTHETIC_ONLY")

        root_a = Path(binding_a.worktree_path)
        root_b = Path(binding_b.worktree_path)
        action_a_calls: list[str] = []

        def action_a(runtime):
            action_a_calls.append("A")
            runtime.write_text("output.txt", "candidate-A-completed")
            return {"status": "SUCCEEDED", "summary": "Candidate A completed in its isolated worktree."}

        def verify_a(runtime):
            self.assertEqual(runtime.read_text("output.txt"), "candidate-A-completed")
            return {
                "status": "VERIFIED",
                "evidence_claims": [self._claim("a", root_a / "output.txt")],
            }

        result_a = self._controller(root_a, "a").execute(
            action_a,
            verify_a,
            owner_gate={"status": "APPROVED", "source_ref": "owner/issue-295-c08-proof"},
            permission_state=WRITE_PERMISSION,
            budget=ExecutionBudget(allow_mutation=True),
        )
        self.assertEqual(result_a["status"], "DONE")
        self.assertEqual(action_a_calls, ["A"])
        self.assertEqual(TaskStateStore(root_a).require().tasks["candidate-a"].status, "DONE")
        completed_fresh_read = ForegroundExecutionController(root_a).resume(
            permission_state=WRITE_PERMISSION
        )
        self.assertEqual(completed_fresh_read["status"], "NO_ACTIVE_TASK")
        self.assertFalse(completed_fresh_read["automatic_start"])
        self.assertEqual(action_a_calls, ["A"], "a fresh read must not rerun a completed candidate")

        a_c12_receipt_ref = result_a["receipt_refs"][-1]
        a_c12_receipt_path = root_a / a_c12_receipt_ref
        a_c12_receipt_bytes_before = a_c12_receipt_path.read_bytes()
        a_c12_receipt = json.loads(a_c12_receipt_bytes_before)
        self.assertEqual(a_c12_receipt["status"], "DONE")
        self.assertEqual(a_c12_receipt["phase"], "VERIFIED")
        self.assertTrue(a_c12_receipt["candidate_binding"])
        receipt_a = orca.CandidateExecutionReceipt(
            candidate_id=candidate_a.candidate_id,
            spec_ref=candidate_a.spec_ref,
            owner_task_id=binding_a.owner_task_id,
            base_revision=candidate_a.base_revision,
            workspace_id=binding_a.workspace_id,
            permission_fingerprint=candidate_a.permission_fingerprint,
            acceptance_fingerprint=candidate_a.acceptance_fingerprint,
            execution_status="COMPLETED",
            verification_status="PASS",
            output_refs=("output.txt",),
            evidence_refs=(a_c12_receipt_ref, "evidence-a"),
        )
        receipt_a_payload_before = receipt_a.to_dict()
        validated_receipt_a = orca.validate_candidate_receipt(
            receipt_a,
            candidate_a,
            binding_a,
            root=self.fw06_root,
            parent_permission=parent_permission,
        )
        self.assertEqual(validated_receipt_a, receipt_a)

        action_b_calls: list[str] = []

        def action_b(runtime):
            action_b_calls.append("B")
            runtime.write_text("output.txt", "candidate-B-interrupted")
            runtime.interrupt()

        interrupted_b = self._controller(root_b, "b").execute(
            action_b,
            None,
            owner_gate={"status": "APPROVED", "source_ref": "owner/issue-295-c08-proof"},
            permission_state=WRITE_PERMISSION,
            budget=ExecutionBudget(allow_mutation=True),
        )
        self.assertEqual(interrupted_b["status"], "INTERRUPTED")
        self.assertEqual(action_b_calls, ["B"])
        self.assertEqual(
            TaskStateStore(root_b).require().tasks["candidate-b"].status, "ACTIVE"
        )

        checkpoint_ref = interrupted_b["checkpoint_ref"]
        checkpoint_path = root_b / checkpoint_ref
        durable_checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        latest_b_receipt = json.loads(
            (root_b / interrupted_b["receipt_refs"][-1]).read_text(encoding="utf-8")
        )
        durable_task = TaskStateStore(root_b).require().tasks["candidate-b"]
        self.assertEqual(durable_task.status, "ACTIVE")
        self.assertEqual(durable_task.checkpoint["checkpoint_ref"], checkpoint_ref)
        self.assertEqual(durable_checkpoint["recovery_classification"], "NEEDS_RECHECK")
        self.assertIn("INDEPENDENT_VERIFICATION", durable_checkpoint["pending_refs"])
        self.assertEqual(latest_b_receipt["phase"], "INTERRUPTED_OR_PARTIAL")
        self.assertEqual(latest_b_receipt["status"], "NEEDS_RECHECK")

        # A fresh controller reads the durable checkpoint and rejects a changed
        # candidate snapshot until a read-only verifier is explicitly supplied.
        (root_b / "output.txt").write_text("tampered candidate B", encoding="utf-8")
        stale_recheck = ForegroundExecutionController(root_b).resume(
            permission_state=WRITE_PERMISSION
        )
        self.assertEqual(stale_recheck["status"], "NEEDS_RECHECK")
        self.assertEqual(stale_recheck["resume"]["reason"], "STATE_FINGERPRINT_CHANGED")
        self.assertFalse(stale_recheck["automatic_start"])
        self.assertEqual(TaskStateStore(root_b).require().tasks["candidate-b"].status, "ACTIVE")
        self.assertEqual(action_b_calls, ["B"])

        # Restore only the fixture artifact to the interrupted checkpoint state;
        # resume below still uses a new controller and must not call action_b.
        (root_b / "output.txt").write_text("candidate-B-interrupted", encoding="utf-8")
        verifier_calls: list[str] = []

        def verify_b(runtime):
            verifier_calls.append("B_READ_ONLY_VERIFY")
            self.assertTrue(runtime.read_only)
            self.assertFalse(runtime.intent.budget.allow_mutation)
            self.assertEqual(runtime.read_text("output.txt"), "candidate-B-interrupted")
            with self.assertRaises(ForegroundPermissionError):
                runtime.write_text("output.txt", "verifier-must-not-write")
            return {
                "status": "VERIFIED",
                "evidence_claims": [self._claim("b", root_b / "output.txt")],
            }

        resumed_b = ForegroundExecutionController(root_b).resume(
            verify_b, permission_state=WRITE_PERMISSION
        )
        self.assertEqual(resumed_b["status"], "DONE")
        self.assertEqual(resumed_b["resume"]["resume_classification"], "NEEDS_RECHECK")
        self.assertEqual(verifier_calls, ["B_READ_ONLY_VERIFY"])
        self.assertEqual(action_b_calls, ["B"], "resume must not rerun Candidate B's original action")
        self.assertEqual(TaskStateStore(root_b).require().tasks["candidate-b"].status, "DONE")

        # Candidate A's source-bound receipt and durable C12 receipt are unchanged.
        self.assertEqual(action_a_calls, ["A"], "completed Candidate A is not rerun")
        self.assertEqual(a_c12_receipt_path.read_bytes(), a_c12_receipt_bytes_before)
        self.assertEqual(receipt_a.to_dict(), receipt_a_payload_before)
        self.assertEqual(receipt_a.receipt_fingerprint, receipt_a_payload_before["receipt_fingerprint"])
        self.assertEqual(
            orca.validate_candidate_receipt(
                receipt_a,
                candidate_a,
                binding_a,
                root=self.fw06_root,
                parent_permission=parent_permission,
            ),
            receipt_a,
        )
        self.assertEqual(permission_fp_a_before, orca.permission_fingerprint(candidate_a.permission))
        self.assertEqual(permission_fp_b_before, orca.permission_fingerprint(candidate_b.permission))
        self.assertTrue(candidate_b.permission.subset_of(parent_permission))

        # No candidate output is applied to the source project; no merge,
        # promotion, release, or auto-apply path is exercised by this proof.
        self.assertEqual((root_a / "output.txt").read_text(encoding="utf-8"), "candidate-A-completed")
        self.assertEqual((root_b / "output.txt").read_text(encoding="utf-8"), "candidate-B-interrupted")
        self.assertFalse((self.source_repo / "output.txt").exists())
        self.assertEqual(self._git("-C", str(self.source_repo), "rev-parse", "HEAD").stdout.strip(), self.base_revision)
        self.assertEqual(self._git("-C", str(self.source_repo), "status", "--porcelain").stdout, "")
        self.assertEqual(self._git("-C", str(self.source_repo), "tag", "--list").stdout, "")


if __name__ == "__main__":
    unittest.main()
