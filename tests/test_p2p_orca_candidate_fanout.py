"""Focused ORCA candidate isolation and bounded receipt tests (Issue #295).

Covers the narrow composition seam in
``.p2p/system/p2p_capabilities/orca_candidate_fanout.py``:

- deterministic candidate identity and hard fanout admission;
- C15 permission/scope no-widen fail-closed reuse;
- FW06-backed candidate workspace/worktree binding; and
- immutable, source-bound execution receipt validation.

These tests do not run candidate work, compare/select results, or promote state.
The FW06 worktree fixture is synthetic local-Git evidence, not a general live-
runtime claim.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.bounded_delegation import (  # noqa: E402
    DelegationPermissionError,
    PermissionEnvelope,
)
from p2p_capabilities.parallel_execution import MAX_PARALLEL_CHILDREN  # noqa: E402
from p2p_capabilities import fw06_operational_resilience as fw06  # noqa: E402
from p2p_capabilities import orca_candidate_fanout as orca  # noqa: E402


BASE_A = "a" * 40
BASE_B = "b" * 40

PARENT = PermissionEnvelope(
    grants=("READ",),
    scope=("src/a.py", "src/b.py", "src/c.py"),
)


def permission(grants=("READ",), scope=("src/a.py",)):
    return PermissionEnvelope(grants=tuple(grants), scope=tuple(scope))


def candidate(
    *,
    ordinal: int = 0,
    variant: str = "",
    spec_ref: str = "src/a.py",
    base_revision: str = BASE_A,
    permission_envelope: PermissionEnvelope | None = None,
    permission_fp: str | None = None,
    acceptance_fp: str = "acceptance-fp-1",
) -> orca.CandidateSpec:
    envelope = permission() if permission_envelope is None else permission_envelope
    return orca.CandidateSpec(
        spec_ref=spec_ref,
        base_revision=base_revision,
        permission_fingerprint=orca.permission_fingerprint(envelope) if permission_fp is None else permission_fp,
        candidate_ordinal=ordinal,
        acceptance_fingerprint=acceptance_fp,
        permission=envelope,
        variant=variant,
    )


class CandidateIdentityTests(unittest.TestCase):
    def test_deterministic_candidate_id_for_same_inputs(self) -> None:
        first = candidate(ordinal=1, variant="alpha")
        second = candidate(ordinal=1, variant="alpha")
        self.assertEqual(first.candidate_id, second.candidate_id)
        self.assertEqual(first.candidate_id, first.candidate_id)
        self.assertEqual(first.identity_payload, second.identity_payload)
        self.assertRegex(first.candidate_id, r"^orca-candidate-[0-9a-f]{32}$")

    def test_spec_ref_change_changes_id(self) -> None:
        self.assertNotEqual(
            candidate(spec_ref="src/a.py").candidate_id,
            candidate(spec_ref="src/b.py").candidate_id,
        )

    def test_base_change_changes_id(self) -> None:
        self.assertNotEqual(
            candidate(base_revision=BASE_A).candidate_id,
            candidate(base_revision=BASE_B).candidate_id,
        )

    def test_permission_fingerprint_change_changes_id(self) -> None:
        packed = orca.permission_fingerprint(permission(scope=("src/a.py", "src/b.py")))
        self.assertNotEqual(
            candidate(permission_fp="fp-narrow-1").candidate_id,
            candidate(permission_fp=packed).candidate_id,
        )

    def test_ordinal_change_changes_id(self) -> None:
        self.assertNotEqual(
            candidate(ordinal=0).candidate_id,
            candidate(ordinal=1).candidate_id,
        )

    def test_variant_change_changes_id(self) -> None:
        self.assertNotEqual(
            candidate(variant="alpha").candidate_id,
            candidate(variant="beta").candidate_id,
        )

    def test_acceptance_fingerprint_change_changes_id(self) -> None:
        self.assertNotEqual(
            candidate(acceptance_fp="acceptance-fp-1").candidate_id,
            candidate(acceptance_fp="acceptance-fp-2").candidate_id,
        )

    def test_candidate_spec_is_immutable(self) -> None:
        spec = candidate()
        with self.assertRaises(FrozenInstanceError):
            spec.spec_ref = "src/z.py"  # type: ignore[misc]

    def test_permission_fingerprint_helper_is_deterministic_and_type_bound(self) -> None:
        self.assertEqual(orca.permission_fingerprint(PARENT), orca.permission_fingerprint(PARENT))
        self.assertNotEqual(
            orca.permission_fingerprint(permission(scope=("src/a.py",))),
            orca.permission_fingerprint(permission(scope=("src/a.py", "src/b.py"))),
        )
        with self.assertRaises(orca.OrcaPermissionBoundaryError) as ctx:
            orca.permission_fingerprint({"grants": ["READ"]})  # type: ignore[arg-type]
        self.assertEqual(ctx.exception.code, orca.ERROR_PERMISSION_ENVELOPE_INVALID)


class HardFanoutTests(unittest.TestCase):
    def test_hard_fanout_cap_never_widens_c17(self) -> None:
        self.assertEqual(orca.HARD_FANOUT_CAP, 2)
        self.assertEqual(orca.C17_PARALLEL_CEILING, MAX_PARALLEL_CHILDREN)
        self.assertLessEqual(orca.HARD_FANOUT_CAP, MAX_PARALLEL_CHILDREN)

    def test_one_candidate_accepted(self) -> None:
        plan = orca.plan_candidate_fanout([candidate(ordinal=0)], PARENT)
        self.assertEqual(plan.planned_count, 1)
        self.assertEqual(plan.candidate_ids, (candidate(ordinal=0).candidate_id,))
        self.assertEqual(plan.hard_fanout_cap, orca.HARD_FANOUT_CAP)

    def test_two_candidates_accepted(self) -> None:
        first = candidate(ordinal=0, spec_ref="src/a.py")
        second = candidate(ordinal=1, spec_ref="src/b.py")
        plan = orca.plan_candidate_fanout([first, second], PARENT)
        self.assertEqual(plan.planned_count, 2)
        self.assertEqual(plan.candidate_ids, (first.candidate_id, second.candidate_id))

    def test_third_candidate_rejected_without_truncation(self) -> None:
        requested = [
            candidate(ordinal=0, spec_ref="src/a.py"),
            candidate(ordinal=1, spec_ref="src/b.py"),
            candidate(ordinal=2, spec_ref="src/c.py"),
        ]
        with self.assertRaises(orca.OrcaFanoutError) as ctx:
            orca.plan_candidate_fanout(requested, PARENT)
        self.assertEqual(ctx.exception.code, orca.ERROR_FANOUT_CAP_EXCEEDED)
        self.assertIn("NO_TRUNCATION", str(ctx.exception))

    def test_four_candidates_rejected(self) -> None:
        requested = [
            candidate(ordinal=index, spec_ref=f"src/{name}.py")
            for index, name in enumerate(("a", "b", "c", "d"))
        ]
        with self.assertRaises(orca.OrcaFanoutError) as ctx:
            orca.plan_candidate_fanout(requested, PARENT)
        self.assertEqual(ctx.exception.code, orca.ERROR_FANOUT_CAP_EXCEEDED)

    def test_zero_candidates_rejected(self) -> None:
        for empty in ([], ()):
            with self.assertRaises(orca.OrcaFanoutError) as ctx:
                orca.plan_candidate_fanout(empty, PARENT)
            self.assertEqual(ctx.exception.code, orca.ERROR_FANOUT_EMPTY)

    def test_duplicate_candidate_rejected(self) -> None:
        spec = candidate(ordinal=0)
        with self.assertRaises(orca.OrcaCandidateError) as ctx:
            orca.plan_candidate_fanout([spec, spec], PARENT)
        self.assertEqual(ctx.exception.code, orca.ERROR_CANDIDATE_DUPLICATE)

    def test_equivalent_but_distinct_candidate_instances_rejected_as_duplicate(self) -> None:
        with self.assertRaises(orca.OrcaCandidateError) as ctx:
            orca.plan_candidate_fanout(
                [candidate(ordinal=0, variant="alpha"), candidate(ordinal=0, variant="alpha")],
                PARENT,
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_CANDIDATE_DUPLICATE)

    def test_same_ordinal_with_different_identity_is_admitted(self) -> None:
        plan = orca.plan_candidate_fanout(
            [candidate(ordinal=0, spec_ref="src/a.py"), candidate(ordinal=0, spec_ref="src/b.py")],
            PARENT,
        )
        self.assertEqual(plan.planned_count, 2)

    def test_invalid_candidate_objects_rejected(self) -> None:
        for invalid in (None, {}, "src/a.py", 42, ["src/a.py"]):
            with self.assertRaises(orca.OrcaCandidateError) as ctx:
                orca.plan_candidate_fanout([invalid], PARENT)  # type: ignore[list-item]
            self.assertEqual(ctx.exception.code, orca.ERROR_CANDIDATE_INVALID)

    def test_non_sequence_input_rejected(self) -> None:
        for invalid in ({candidate()}, (item for item in [candidate()]), "src/a.py"):
            with self.assertRaises(orca.OrcaFanoutError) as ctx:
                orca.plan_candidate_fanout(invalid, PARENT)  # type: ignore[arg-type]
            self.assertEqual(ctx.exception.code, orca.ERROR_FANOUT_INPUT_INVALID)

    def test_plan_dict_is_deterministic_and_serializable(self) -> None:
        plan = orca.plan_candidate_fanout([candidate(ordinal=0), candidate(ordinal=1, spec_ref="src/b.py")], PARENT)
        payload = plan.to_dict()
        self.assertEqual(payload["planned_count"], 2)
        self.assertEqual(payload["hard_fanout_cap"], 2)
        self.assertEqual(payload["c17_parallel_ceiling"], MAX_PARALLEL_CHILDREN)
        self.assertEqual(len({item["candidate_id"] for item in payload["candidates"]}), 2)
        self.assertEqual(payload, plan.to_dict())


class PermissionBoundaryTests(unittest.TestCase):
    def test_equal_permission_accepted(self) -> None:
        envelope = permission(grants=("READ",), scope=("src/a.py", "src/b.py"))
        plan_fanout = orca.plan_candidate_fanout([candidate(permission_envelope=envelope)], PARENT)
        self.assertEqual(plan_fanout.planned_count, 1)

    def test_narrower_permission_accepted(self) -> None:
        narrow = permission(grants=("READ",), scope=("src/a.py",))
        self.assertTrue(narrow.subset_of(PARENT))
        plan_fanout = orca.plan_candidate_fanout([candidate(permission_envelope=narrow)], PARENT)
        self.assertEqual(plan_fanout.planned_count, 1)

    def test_permission_widening_rejected(self) -> None:
        widened = permission(grants=("READ", "WRITE"), scope=("src/a.py",))
        with self.assertRaises(orca.OrcaPermissionBoundaryError) as ctx:
            orca.plan_candidate_fanout([candidate(permission_envelope=widened)], PARENT)
        self.assertEqual(ctx.exception.code, orca.ERROR_PERMISSION_WIDENED)

    def test_scope_widening_rejected(self) -> None:
        widened = permission(grants=("READ",), scope=("src/a.py", "src/outside.py"))
        with self.assertRaises(orca.OrcaPermissionBoundaryError) as ctx:
            orca.plan_candidate_fanout([candidate(permission_envelope=widened)], PARENT)
        self.assertEqual(ctx.exception.code, orca.ERROR_SCOPE_WIDENED)

    def test_candidate_without_explicit_scope_fails_closed(self) -> None:
        unscoped = PermissionEnvelope(grants=("READ",), scope=())
        with self.assertRaises(orca.OrcaPermissionBoundaryError) as ctx:
            orca.plan_candidate_fanout([candidate(permission_envelope=unscoped)], PARENT)
        self.assertEqual(ctx.exception.code, orca.ERROR_PERMISSION_SCOPE_MISSING)

    def test_invalid_parent_permission_fails_closed(self) -> None:
        for invalid in (None, {"grants": ["READ"], "scope": ["src/a.py"]}, "READ"):
            with self.assertRaises(orca.OrcaPermissionBoundaryError) as ctx:
                orca.plan_candidate_fanout([candidate()], invalid)  # type: ignore[arg-type]
            self.assertEqual(ctx.exception.code, orca.ERROR_PARENT_PERMISSION_INVALID)

    def test_c15_delegation_boundary_is_reused_not_reimplemented(self) -> None:
        with self.assertRaises(DelegationPermissionError):
            PermissionEnvelope(grants=("READ",), scope=("src/a.py",), delegate_allowed=True)
        with self.assertRaises(DelegationPermissionError):
            PermissionEnvelope.from_value({"grants": ["READ"], "scope": ["src/a.py"], "allow_delegate": True})

    def test_mismatched_permission_fingerprint_fails_before_plan_or_workspace(self) -> None:
        invalid = candidate(permission_fp="caller-supplied-mismatched-fingerprint")
        with self.assertRaises(orca.OrcaPermissionBoundaryError) as ctx:
            orca.plan_candidate_fanout([invalid], PARENT)
        self.assertEqual(ctx.exception.code, orca.ERROR_PERMISSION_FINGERPRINT_MISMATCH)

        with patch.object(fw06, "create_isolated_worktree") as create_worktree:
            with self.assertRaises(orca.OrcaPermissionBoundaryError) as workspace_ctx:
                orca.create_candidate_workspace_bindings(
                    [invalid],
                    PARENT,
                    root=REPO_ROOT / ".test-orca-rejected-fw06",
                    repo_path=REPO_ROOT / ".test-orca-missing-repository",
                    worktree_parent=REPO_ROOT / ".test-orca-rejected-worktrees",
                    project_id="p2p-orca-rejected-tests",
                    owner_task_id="task-rejected",
                )
            self.assertEqual(
                workspace_ctx.exception.code, orca.ERROR_PERMISSION_FINGERPRINT_MISMATCH
            )
            create_worktree.assert_not_called()

    def test_invalid_spec_identity_fields_rejected(self) -> None:
        for bad_ref in ("", " ", "/abs/src/a.py", "src\\a.py"):
            with self.assertRaises(orca.OrcaCandidateError) as ctx:
                candidate(spec_ref=bad_ref)
            self.assertEqual(ctx.exception.code, orca.ERROR_CANDIDATE_INVALID)
        for bad_ordinal in (True, -1, "0", 1.5):
            with self.assertRaises(orca.OrcaCandidateError):
                candidate(ordinal=bad_ordinal)  # type: ignore[arg-type]

    def test_module_remains_a_narrow_seam(self) -> None:
        """Composition is bounded; ORCA still is not an execution framework."""

        public = {name.lower() for name in orca.__all__}
        for forbidden in ("runner", "executor", "scheduler", "queue", "promote", "ledger", "router", "store", "judge", "scorer"):
            self.assertFalse(
                any(forbidden in name for name in public),
                f"ORCA slice must not expose {forbidden}",
            )
        self.assertIn("create_candidate_workspace_bindings", public)
        self.assertIn("validate_candidate_receipt", public)
        self.assertIn("compare_validated_candidate_receipts", public)


class CandidateIsolationAndReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Synthetic local repository only: FW06's existing worktree primitive
        # is exercised without claiming live-runtime readiness.
        cls._temporary = tempfile.TemporaryDirectory(
            prefix="orca-fw06-fixture-", dir=REPO_ROOT
        )
        cls.temp_root = Path(cls._temporary.name)
        cls.repo_path = cls.temp_root / "source-repo"
        cls.repo_path.mkdir()
        subprocess.run(
            ["git", "init", "--initial-branch=main", str(cls.repo_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(cls.repo_path), "config", "user.name", "ORCA test"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(cls.repo_path), "config", "user.email", "orca-test@example.invalid"],
            check=True,
            capture_output=True,
            text=True,
        )
        (cls.repo_path / "README.md").write_text("synthetic FW06 fixture\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(cls.repo_path), "add", "README.md"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(cls.repo_path), "commit", "-m", "synthetic FW06 fixture"],
            check=True,
            capture_output=True,
            text=True,
        )
        cls.base_revision = subprocess.run(
            ["git", "-C", str(cls.repo_path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        cls.fw06_root = cls.temp_root / "fw06-state"
        cls.worktree_parent = cls.temp_root / "candidate-worktrees"
        cls.first_candidate = candidate(
            ordinal=0,
            spec_ref="src/a.py",
            base_revision=cls.base_revision,
            permission_envelope=permission(scope=("src/a.py",)),
        )
        cls.second_candidate = candidate(
            ordinal=1,
            spec_ref="src/b.py",
            base_revision=cls.base_revision,
            permission_envelope=permission(scope=("src/b.py",)),
        )
        cls.bindings = orca.create_candidate_workspace_bindings(
            [cls.first_candidate, cls.second_candidate],
            PARENT,
            root=cls.fw06_root,
            repo_path=cls.repo_path,
            worktree_parent=cls.worktree_parent,
            project_id="p2p-orca-tests",
            owner_task_id="task-295",
            goal_id="goal-orca-295",
            session_id="session-test",
            creator="orca-unittest",
        )
        cls.first_binding, cls.second_binding = cls.bindings

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    @staticmethod
    def _git_head(path: str | Path) -> str:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    @staticmethod
    def _receipt(
        spec: orca.CandidateSpec,
        binding: orca.CandidateWorkspaceBinding,
        **overrides,
    ) -> orca.CandidateExecutionReceipt:
        payload = {
            "candidate_id": spec.candidate_id,
            "spec_ref": spec.spec_ref,
            "owner_task_id": binding.owner_task_id,
            "base_revision": spec.base_revision,
            "workspace_id": binding.workspace_id,
            "permission_fingerprint": spec.permission_fingerprint,
            "acceptance_fingerprint": spec.acceptance_fingerprint,
            "execution_status": "COMPLETED",
            "verification_status": "PASS",
            "output_refs": ("output:sha256:" + "0" * 64,),
            "evidence_refs": (
                "tests/test_p2p_orca_candidate_fanout.py::focused",
                "comparison:AC-1",
            ),
        }
        payload.update(overrides)
        return orca.CandidateExecutionReceipt(**payload)

    def _compare(self, receipts, *, comparison_evidence=None):
        specs = {
            self.first_candidate.candidate_id: self.first_candidate,
            self.second_candidate.candidate_id: self.second_candidate,
        }
        bindings = {
            self.first_candidate.candidate_id: self.first_binding,
            self.second_candidate.candidate_id: self.second_binding,
        }
        ids = [receipt.candidate_id for receipt in receipts]
        if comparison_evidence is None:
            comparison_evidence = {
                candidate_id: {
                    "satisfied_acceptance_criteria": ("AC-1",),
                    "evidence_complete": True,
                    "evidence_refs": ("comparison:AC-1",),
                }
                for candidate_id in ids
            }
        return orca.compare_validated_candidate_receipts(
            receipts,
            candidate_specs={candidate_id: specs[candidate_id] for candidate_id in set(ids)},
            workspace_bindings={candidate_id: bindings[candidate_id] for candidate_id in set(ids)},
            root=self.fw06_root,
            parent_permission=PARENT,
            required_acceptance_criteria=("AC-1",),
            required_evidence_refs=("comparison:AC-1",),
            comparison_evidence=comparison_evidence,
        )

    def test_two_candidate_workspaces_are_distinct_and_fw06_backed(self) -> None:
        first, second = self.bindings
        self.assertNotEqual(first.workspace_id, second.workspace_id)
        self.assertNotEqual(first.worktree_path, second.worktree_path)
        self.assertEqual(first.candidate_id, self.first_candidate.candidate_id)
        self.assertEqual(second.candidate_id, self.second_candidate.candidate_id)
        self.assertEqual(first.owner_task_id, "task-295")
        self.assertEqual(second.owner_task_id, "task-295")
        self.assertEqual(first.lifecycle_state, "ACTIVE")
        self.assertEqual(second.lifecycle_state, "ACTIVE")
        rows = {
            row["workspace_id"]: row
            for row in fw06.list_all_workspaces(self.fw06_root, "p2p-orca-tests")
        }
        self.assertEqual(
            rows[first.workspace_id]["purpose"],
            f"orca_candidate:{first.candidate_id}:{self.first_candidate.spec_ref}",
        )
        self.assertEqual(
            rows[second.workspace_id]["purpose"],
            f"orca_candidate:{second.candidate_id}:{self.second_candidate.spec_ref}",
        )
        self.assertEqual(rows[first.workspace_id]["root_path"], first.worktree_path)
        self.assertEqual(rows[second.workspace_id]["root_path"], second.worktree_path)
        self.assertEqual(rows[first.workspace_id]["mutation_policy"], "SYNTHETIC_ONLY")
        self.assertEqual(rows[second.workspace_id]["mutation_policy"], "SYNTHETIC_ONLY")

    def test_exact_same_base_revision_is_allowed_for_both_candidates(self) -> None:
        self.assertEqual(self.first_binding.base_revision, self.base_revision)
        self.assertEqual(self.second_binding.base_revision, self.base_revision)
        self.assertEqual(self._git_head(self.first_binding.worktree_path), self.base_revision)
        self.assertEqual(self._git_head(self.second_binding.worktree_path), self.base_revision)

    def test_candidate_workspace_swap_is_rejected(self) -> None:
        with self.assertRaises(orca.OrcaWorkspaceError) as ctx:
            orca.validate_candidate_workspace(
                self.second_candidate,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_WORKSPACE_CANDIDATE_MISMATCH)

    def test_workspace_base_mismatch_fails_closed(self) -> None:
        changed_base = candidate(
            ordinal=0,
            spec_ref="src/a.py",
            base_revision="b" * 40,
            permission_envelope=self.first_candidate.permission,
        )
        with self.assertRaises(orca.OrcaWorkspaceError) as ctx:
            orca.validate_candidate_workspace(
                changed_base,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_WORKSPACE_BASE_MISMATCH)

    def test_same_relative_file_path_remains_isolated_by_worktree_root(self) -> None:
        relative = Path("src/shared.txt")
        first_file = Path(self.first_binding.worktree_path) / relative
        second_file = Path(self.second_binding.worktree_path) / relative
        first_file.parent.mkdir(parents=True, exist_ok=True)
        second_file.parent.mkdir(parents=True, exist_ok=True)
        first_file.write_text("candidate A", encoding="utf-8")
        second_file.write_text("candidate B", encoding="utf-8")
        self.assertNotEqual(first_file.resolve(), second_file.resolve())
        self.assertEqual(first_file.read_text(encoding="utf-8"), "candidate A")
        self.assertEqual(second_file.read_text(encoding="utf-8"), "candidate B")

    def test_valid_receipt_is_accepted_deterministically(self) -> None:
        receipt = self._receipt(self.first_candidate, self.first_binding)
        first = orca.validate_candidate_receipt(
            receipt,
            self.first_candidate,
            self.first_binding,
            root=self.fw06_root,
            parent_permission=PARENT,
        )
        second = orca.validate_candidate_receipt(
            receipt.to_dict(),
            self.first_candidate,
            self.first_binding,
            root=self.fw06_root,
            parent_permission=PARENT,
        )
        self.assertEqual(first, receipt)
        self.assertEqual(second.receipt_fingerprint, receipt.receipt_fingerprint)
        self.assertEqual(receipt.to_dict(), receipt.to_dict())

    def test_receipt_for_wrong_candidate_is_rejected(self) -> None:
        receipt_b = self._receipt(self.second_candidate, self.second_binding)
        with self.assertRaises(orca.OrcaReceiptError) as ctx:
            orca.validate_candidate_receipt(
                receipt_b,
                self.first_candidate,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_RECEIPT_CANDIDATE_MISMATCH)

    def test_receipt_permission_fingerprint_mismatch_is_rejected(self) -> None:
        receipt = self._receipt(
            self.first_candidate,
            self.first_binding,
            permission_fingerprint="0" * 64,
        )
        with self.assertRaises(orca.OrcaReceiptError) as ctx:
            orca.validate_candidate_receipt(
                receipt,
                self.first_candidate,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_RECEIPT_PERMISSION_MISMATCH)

    def test_receipt_workspace_mismatch_is_rejected(self) -> None:
        receipt = self._receipt(
            self.first_candidate,
            self.first_binding,
            workspace_id=self.second_binding.workspace_id,
        )
        with self.assertRaises(orca.OrcaReceiptError) as ctx:
            orca.validate_candidate_receipt(
                receipt,
                self.first_candidate,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_RECEIPT_WORKSPACE_MISMATCH)

    def test_receipt_acceptance_fingerprint_mismatch_is_rejected(self) -> None:
        receipt = self._receipt(
            self.first_candidate,
            self.first_binding,
            acceptance_fingerprint="acceptance-fp-stale",
        )
        with self.assertRaises(orca.OrcaReceiptError) as ctx:
            orca.validate_candidate_receipt(
                receipt,
                self.first_candidate,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_RECEIPT_ACCEPTANCE_MISMATCH)

    def test_receipt_base_mismatch_is_rejected(self) -> None:
        receipt = self._receipt(
            self.first_candidate,
            self.first_binding,
            base_revision="b" * 40,
        )
        with self.assertRaises(orca.OrcaReceiptError) as ctx:
            orca.validate_candidate_receipt(
                receipt,
                self.first_candidate,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_RECEIPT_BASE_MISMATCH)

    def test_missing_verification_state_is_rejected(self) -> None:
        payload = self._receipt(self.first_candidate, self.first_binding).to_dict()
        del payload["verification_status"]
        with self.assertRaises(orca.OrcaReceiptError) as ctx:
            orca.validate_candidate_receipt(
                payload,
                self.first_candidate,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_RECEIPT_MALFORMED)

    def test_malformed_and_stale_receipts_are_rejected(self) -> None:
        with self.assertRaises(orca.OrcaReceiptError) as malformed:
            orca.validate_candidate_receipt(
                {"schema": orca.ORCA_RECEIPT_SCHEMA},
                self.first_candidate,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(malformed.exception.code, orca.ERROR_RECEIPT_MALFORMED)

        stale = self._receipt(self.first_candidate, self.first_binding).to_dict()
        stale["output_refs"] = ["output:sha256:" + "1" * 64]
        with self.assertRaises(orca.OrcaReceiptError) as stale_ctx:
            orca.validate_candidate_receipt(
                stale,
                self.first_candidate,
                self.first_binding,
                root=self.fw06_root,
                parent_permission=PARENT,
            )
        self.assertEqual(stale_ctx.exception.code, orca.ERROR_RECEIPT_FINGERPRINT_MISMATCH)

    def test_failed_or_unverified_receipt_is_not_comparator_eligible(self) -> None:
        for changes, error_code in (
            ({"execution_status": "FAILED"}, orca.ERROR_RECEIPT_EXECUTION_INVALID),
            ({"verification_status": "NOT_VERIFIED"}, orca.ERROR_RECEIPT_VERIFICATION_INVALID),
        ):
            receipt = self._receipt(self.first_candidate, self.first_binding, **changes)
            with self.assertRaises(orca.OrcaReceiptError) as ctx:
                orca.validate_candidate_receipt(
                    receipt,
                    self.first_candidate,
                    self.first_binding,
                    root=self.fw06_root,
                    parent_permission=PARENT,
                )
            self.assertEqual(ctx.exception.code, error_code)

    def test_receipt_evidence_references_are_bounded(self) -> None:
        with self.assertRaises(orca.OrcaReceiptError) as ctx:
            self._receipt(
                self.first_candidate,
                self.first_binding,
                evidence_refs=tuple(f"evidence:{index}" for index in range(9)),
            )
        self.assertEqual(ctx.exception.code, orca.ERROR_RECEIPT_MALFORMED)

    def test_partial_workspace_failure_is_contained_and_durable(self) -> None:
        project_id = "p2p-orca-partial-tests"
        owner_task_id = "task-295-partial"
        partial_root = self.temp_root / "partial-fw06-state"
        partial_worktrees = self.temp_root / "partial-worktrees"
        partial_a = candidate(
            ordinal=10,
            spec_ref="src/a.py",
            base_revision=self.base_revision,
            permission_envelope=permission(scope=("src/a.py",)),
        )
        partial_b = candidate(
            ordinal=11,
            spec_ref="src/b.py",
            base_revision=self.base_revision,
            permission_envelope=permission(scope=("src/b.py",)),
        )
        calls: list[str] = []
        real_create = fw06.create_isolated_worktree
        fail_purpose = f"orca_candidate:{partial_b.candidate_id}:{partial_b.spec_ref}"

        def create_then_fail_candidate_b(root, **kwargs):
            calls.append(kwargs["workspace_id"])
            if kwargs["purpose"] == fail_purpose:
                raise RuntimeError("injected candidate B worktree failure")
            return real_create(root, **kwargs)

        with patch.object(fw06, "create_isolated_worktree", side_effect=create_then_fail_candidate_b):
            with self.assertRaises(orca.OrcaWorkspacePartialFailure) as ctx:
                orca.create_candidate_workspace_bindings(
                    [partial_a, partial_b],
                    PARENT,
                    root=partial_root,
                    repo_path=self.repo_path,
                    worktree_parent=partial_worktrees,
                    project_id=project_id,
                    owner_task_id=owner_task_id,
                    creator="orca-partial-test",
                )

        failure = ctx.exception
        self.assertEqual(failure.code, orca.ERROR_WORKSPACE_PARTIAL_FAILURE)
        self.assertEqual(failure.created_workspace_ids, (calls[0],))
        self.assertEqual(failure.failed_candidate_id, partial_b.candidate_id)
        self.assertEqual(failure.failed_candidate_index, 1)
        self.assertEqual(failure.failure_code, "FW06_RUNTIMEERROR")
        self.assertTrue(failure.lease_released)
        self.assertTrue(failure.durable_partial_recorded)
        self.assertEqual(failure.marked_workspace_ids, failure.created_workspace_ids)
        self.assertEqual(len(calls), 2, "no retry or rescue candidate may be created")
        self.assertIn(calls[0], str(failure))
        self.assertIn(partial_b.candidate_id, str(failure))

        rows = fw06.list_all_workspaces(partial_root, project_id)
        self.assertEqual(len(rows), 1, "candidate B must not be silently substituted")
        row = rows[0]
        self.assertEqual(row["workspace_id"], calls[0])
        self.assertTrue(Path(row["root_path"]).is_dir(), "ambiguous worktree is kept")
        self.assertEqual(row["status"], "CONFLICT")
        self.assertEqual(row["lifecycle_state"], "ACTIVE")
        self.assertEqual(row["mutation_policy"], "SYNTHETIC_ONLY")
        self.assertIn("UNKNOWN", row["protection_reasons"])
        self.assertEqual(row["orca_partial_failure"]["failed_candidate_id"], partial_b.candidate_id)
        self.assertEqual(row["orca_partial_failure"]["created_workspace_ids"], [calls[0]])

        lease_rows = fw06.read_leases(partial_root, project_id=project_id, task_id=owner_task_id)
        latest_lease = [row for row in lease_rows if row["lease_id"] == failure.lease_id][-1]
        self.assertEqual(latest_lease["status"], "RELEASED")
        events = fw06.read_fw06_events(
            partial_root, project_id=project_id,
            event_type="ORCA_CANDIDATE_FANOUT_PARTIAL_FAILURE",
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["payload"]["failed_candidate_id"], partial_b.candidate_id)
        self.assertTrue(events[0]["payload"]["lease_released"])

        self.assertEqual((self.repo_path / "README.md").read_text(encoding="utf-8"), "synthetic FW06 fixture\n")
        source_status = subprocess.run(
            ["git", "-C", str(self.repo_path), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(source_status, "", "workspace setup must not mutate project source")

    def test_one_valid_receipt_can_be_selected_deterministically(self) -> None:
        receipt = self._receipt(self.first_candidate, self.first_binding)
        result = self._compare([receipt])
        self.assertEqual(result["verdict"], "SELECT_CANDIDATE")
        self.assertEqual(result["selected_candidate_id"], self.first_candidate.candidate_id)
        self.assertEqual(result["candidate_ids_considered"], [self.first_candidate.candidate_id])
        self.assertEqual(result["reason_codes"], ["UNIQUE_ACCEPTANCE_CRITERIA_WINNER"])
        self.assertIn("comparison:AC-1", result["evidence_refs_used"])

    def test_invalid_or_unverified_candidate_abstains(self) -> None:
        receipt = self._receipt(
            self.first_candidate, self.first_binding, verification_status="NOT_VERIFIED"
        )
        result = self._compare([receipt])
        self.assertEqual(result["verdict"], "ABSTAIN")
        self.assertIsNone(result["selected_candidate_id"])
        self.assertEqual(result["reason_codes"], ["RECEIPT_VALIDATION_FAILED"])

    def test_two_candidates_with_unique_acceptance_winner_select(self) -> None:
        receipts = [
            self._receipt(self.first_candidate, self.first_binding),
            self._receipt(self.second_candidate, self.second_binding),
        ]
        facts = {
            self.first_candidate.candidate_id: {
                "satisfied_acceptance_criteria": ("AC-1",),
                "evidence_complete": True,
                "evidence_refs": ("comparison:AC-1",),
            },
            self.second_candidate.candidate_id: {
                "satisfied_acceptance_criteria": (),
                "evidence_complete": True,
                "evidence_refs": ("comparison:AC-1",),
            },
        }
        result = self._compare(receipts, comparison_evidence=facts)
        self.assertEqual(result["verdict"], "SELECT_CANDIDATE")
        self.assertEqual(result["selected_candidate_id"], self.first_candidate.candidate_id)

    def test_two_candidate_tie_abstains(self) -> None:
        receipts = [
            self._receipt(self.first_candidate, self.first_binding),
            self._receipt(self.second_candidate, self.second_binding),
        ]
        result = self._compare(receipts)
        self.assertEqual(result["verdict"], "ABSTAIN")
        self.assertIsNone(result["selected_candidate_id"])
        self.assertEqual(result["reason_codes"], ["ACCEPTANCE_CRITERIA_TIE"])

    def test_incomparable_criteria_abstain(self) -> None:
        receipt = self._receipt(self.first_candidate, self.first_binding)
        facts = {
            self.first_candidate.candidate_id: {
                "satisfied_acceptance_criteria": ("AC-OTHER",),
                "evidence_complete": True,
                "evidence_refs": ("comparison:AC-1",),
            },
        }
        result = self._compare([receipt], comparison_evidence=facts)
        self.assertEqual(result["verdict"], "ABSTAIN")
        self.assertEqual(result["reason_codes"], ["INCOMPARABLE_CRITERIA"])

    def test_missing_comparison_evidence_abstains(self) -> None:
        receipts = [
            self._receipt(self.first_candidate, self.first_binding),
            self._receipt(self.second_candidate, self.second_binding),
        ]
        facts = {
            self.first_candidate.candidate_id: {
                "satisfied_acceptance_criteria": ("AC-1",),
                "evidence_complete": True,
                "evidence_refs": ("comparison:AC-1",),
            },
        }
        result = self._compare(receipts, comparison_evidence=facts)
        self.assertEqual(result["verdict"], "ABSTAIN")
        self.assertEqual(result["reason_codes"], ["COMPARISON_EVIDENCE_MISSING"])

        receipt_without_required_ref = self._receipt(
            self.first_candidate,
            self.first_binding,
            evidence_refs=("tests/test_p2p_orca_candidate_fanout.py::focused",),
        )
        receipt_result = self._compare([receipt_without_required_ref])
        self.assertEqual(receipt_result["verdict"], "ABSTAIN")
        self.assertEqual(receipt_result["reason_codes"], ["COMPARISON_EVIDENCE_MISSING"])

    def test_reversing_receipt_order_does_not_change_result(self) -> None:
        first = self._receipt(self.first_candidate, self.first_binding)
        second = self._receipt(self.second_candidate, self.second_binding)
        facts = {
            self.first_candidate.candidate_id: {
                "satisfied_acceptance_criteria": ("AC-1",),
                "evidence_complete": True,
                "evidence_refs": ("comparison:AC-1",),
            },
            self.second_candidate.candidate_id: {
                "satisfied_acceptance_criteria": (),
                "evidence_complete": True,
                "evidence_refs": ("comparison:AC-1",),
            },
        }
        self.assertEqual(
            self._compare([first, second], comparison_evidence=facts),
            self._compare([second, first], comparison_evidence=facts),
        )

    def test_mismatched_workspace_receipt_cannot_win(self) -> None:
        stale = self._receipt(
            self.first_candidate,
            self.first_binding,
            workspace_id=self.second_binding.workspace_id,
        )
        result = self._compare([stale])
        self.assertEqual(result["verdict"], "ABSTAIN")
        self.assertIsNone(result["selected_candidate_id"])
        self.assertEqual(result["reason_codes"], ["RECEIPT_VALIDATION_FAILED"])

    def test_comparator_does_not_mutate_fw06_or_project_state(self) -> None:
        receipt = self._receipt(self.first_candidate, self.first_binding)
        workspaces_before = fw06.list_all_workspaces(self.fw06_root, "p2p-orca-tests")
        events_before = fw06.read_fw06_events(self.fw06_root, project_id="p2p-orca-tests")
        leases_before = fw06.read_leases(self.fw06_root, project_id="p2p-orca-tests")
        source_before = subprocess.run(
            ["git", "-C", str(self.repo_path), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        result = self._compare([receipt])
        self.assertEqual(result["verdict"], "SELECT_CANDIDATE")
        self.assertEqual(fw06.list_all_workspaces(self.fw06_root, "p2p-orca-tests"), workspaces_before)
        self.assertEqual(fw06.read_fw06_events(self.fw06_root, project_id="p2p-orca-tests"), events_before)
        self.assertEqual(fw06.read_leases(self.fw06_root, project_id="p2p-orca-tests"), leases_before)
        source_after = subprocess.run(
            ["git", "-C", str(self.repo_path), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(source_after, source_before)

    def test_z_fw06_completion_lifecycle_is_reflected_and_receipt_stays_valid(self) -> None:
        completed = fw06.mark_workspace_complete(
            self.fw06_root, self.second_binding.workspace_id
        )
        self.assertEqual(completed["status"], "QUIESCED")
        self.assertEqual(completed["lifecycle_state"], "COMPLETE")
        refreshed = orca.validate_candidate_workspace(
            self.second_candidate,
            self.second_binding,
            root=self.fw06_root,
            parent_permission=PARENT,
        )
        self.assertEqual(refreshed.status, "QUIESCED")
        self.assertEqual(refreshed.lifecycle_state, "COMPLETE")
        receipt = self._receipt(self.second_candidate, refreshed)
        self.assertEqual(
            orca.validate_candidate_receipt(
                receipt,
                self.second_candidate,
                refreshed,
                root=self.fw06_root,
                parent_permission=PARENT,
            ),
            receipt,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
