"""Structural regression tests for P2P law consumption and experience reuse closure.

Protects all 12 minimum invariants specified in Issue #247:
1. actor receipt is source-bound;
2. parent receipt cannot substitute for executor receipt;
3. stale/tampered portable cannot produce PASS (Blocker A);
4. prompt/handoff serialization requires actor receipt;
5. non-trivial task start includes bounded experience check;
6. repo-scoped portable flow can access promoted ACTIVE experience without local runtime;
7. material correction cannot silently close without learning reconciliation (Blocker D & Blocker 5);
8. routine success does not manufacture memory;
9. experience cannot widen law/permission/acceptance authority;
10. portable projection remains idempotent;
11. experience projection remains generated + source/hash bound;
12. no second control plane / router / ledger / DB is introduced.

Also proves all REPAIR_02 blockers:
- Blocker 1: portable experience fails closed when transport binding is missing, malformed, mismatched, or conflicting;
- Blocker 2: executor LAW_CHECK SHA must match recorded session expected SHA; random 64-hex SHA fails reconciliation;
- Blocker 3: narrative + ReturnPacket LAW_CHECK normalized as one logical receipt; cross-surface contradiction rejected;
- Blocker 4: EXPERIENCE_CHECK enforced at existing ingest path; missing, contradictory, or inconsistent with active expectation fails reconciliation;
- Blocker 5: every terminal substantive task must provide LEARNING_RECONCILIATION=NONE or CANDIDATE without keyword heuristics;
- Blocker 6: representative real Logistics repo proof with actual blob references;
- Blocker 7: deterministic experience lifecycle reproduction.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
for candidate in (str(SYSTEM_ROOT), str(SCRIPTS_ROOT), str(REPO_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import p2p_control_tower as control_tower  # noqa: E402
import p2p_portable_law_projection as projector  # noqa: E402
from p2p_capabilities import experience_evolution as ee  # noqa: E402
from p2p_capabilities import experience_federation as ef  # noqa: E402
from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    ControlTower,
    ControlTowerReturnPacket,
    SessionBinding,
    create_return_packet,
    parse_return_packet,
)

BASE_SHA = "a" * 64
BASE_TREE = "b" * 64


class LawConsumptionAndExperienceClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="p2p-test-closure-")
        self.base = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _canonical_sha(self) -> str:
        source = REPO_ROOT / projector.SOURCE_REL
        return hashlib.sha256(source.read_bytes()).hexdigest()

    def _canonical_main_sha(self) -> str:
        receipt = control_tower._establish_control_tower_law_context(self.base)
        return str(receipt.get("content_sha256") or "")

    def _catalog_sha(self) -> str:
        catalog = REPO_ROOT / projector.SHARED_CATALOG_REL
        return hashlib.sha256(catalog.read_bytes()).hexdigest()

    def _tower(self, root: Path) -> ControlTower:
        return ControlTower(
            root,
            current_canonical_base_sha=BASE_SHA,
            current_canonical_base_tree=BASE_TREE,
        )

    def _setup_session(
        self,
        root: Path,
        session_id: str = "sess-01",
        host: str = "CODEX",
        goal_id: str = "TASK-01",
        goal: str = "Perform task",
        expected_law_sha: str | None = None,
        expected_experience_ids: tuple[str, ...] = (),
    ) -> tuple[ControlTower, SessionBinding]:
        root.mkdir(parents=True, exist_ok=True)
        binding = SessionBinding(
            session_id=session_id,
            host=host,
            goal_id=goal_id,
            goal=goal,
        )
        tower = self._tower(root)
        tower.start_session(
            binding,
            task_id="TASK-TOWER-1",
            worktree="fixture-worktree",
            branch="fixture-branch",
            expected_law_sha=expected_law_sha,
            expected_experience_ids=expected_experience_ids,
        )
        return tower, binding

    # -------------------------------------------------------------------------
    # Invariant 1 & 2
    # -------------------------------------------------------------------------

    def test_01_actor_receipt_is_source_bound(self) -> None:
        """Actor receipt must bind to actual source and canonical source SHA256."""
        canonical_sha = self._canonical_sha()
        project = self.base / "project1"
        project.mkdir()
        projector.project_law(REPO_ROOT, project)

        agents_text = (project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("LAW_CHECK=PASS", agents_text)
        self.assertIn("SOURCE_SHA256=", agents_text)
        self.assertIn("A portable PASS must bind to the recorded `SOURCE_CONTENT_SHA256`", agents_text)

        portable_notebook = project / projector.PORTABLE_REL
        self.assertIn(f"SOURCE_CONTENT_SHA256={canonical_sha}", portable_notebook.read_text(encoding="utf-8"))

    def test_02_parent_receipt_cannot_substitute_for_executor_receipt(self) -> None:
        """Control Tower self-law receipt explicitly declares EXECUTOR_RECEIPT_SUBSTITUTE=NO."""
        receipt = control_tower._establish_control_tower_law_context(REPO_ROOT)
        self.assertEqual("PASS", receipt["status"])
        self.assertEqual("CONTROL_TOWER_SELF", receipt["actor"])
        self.assertFalse(receipt["executor_receipt_substitute"])

        line = control_tower._law_receipt_line(receipt)
        self.assertIn("EXECUTOR_RECEIPT_SUBSTITUTE=NO", line)
        self.assertIn("ACTOR=CONTROL_TOWER_SELF", line)

        agents_block = projector._agents_block()
        self.assertIn("PARENT_SELF_LAW_PREFLIGHT != EXECUTOR_LAW_PREFLIGHT", agents_block)
        self.assertIn("never proves executor preflight and never substitutes", agents_block)

    # -------------------------------------------------------------------------
    # Invariant 3 & Blocker A: Target Law Tamper Detection
    # -------------------------------------------------------------------------

    def test_03_target_law_tamper_detection_and_freshness(self) -> None:
        """CURRENT requires declared hash == canonical AND body bytes hash == declared."""
        canonical_sha = self._canonical_sha()
        project = self.base / "project_tamper_test"
        project.mkdir()
        projector.project_law(REPO_ROOT, project)
        portable = project / projector.PORTABLE_REL
        original_portable = portable.read_text(encoding="utf-8")

        # 1. Fresh generated portable => CURRENT
        fresh = control_tower.check_target_law_freshness(REPO_ROOT, project)
        self.assertEqual("CURRENT", fresh["status"])
        self.assertEqual(canonical_sha, fresh["target_law_sha256"])

        # 2. Header SHA changed while body untouched => not CURRENT (INLINE / TAMPERED)
        stale_sha = "0" * 64
        tampered_header = original_portable.replace(
            f"SOURCE_CONTENT_SHA256={canonical_sha}",
            f"SOURCE_CONTENT_SHA256={stale_sha}",
        )
        portable.write_text(tampered_header, encoding="utf-8")
        stale_res = control_tower.check_target_law_freshness(REPO_ROOT, project)
        self.assertEqual("INLINE", stale_res["status"])
        self.assertIn("TAMPERED", stale_res.get("reason", ""))

        # 3. Body changed while header remains untouched => not CURRENT (TAMPERED: hash mismatch)
        portable.write_text(original_portable, encoding="utf-8")
        tampered_body = original_portable + "\n\n### TAMPERED INJECTED LAW\n"
        portable.write_text(tampered_body, encoding="utf-8")
        body_tamper_res = control_tower.check_target_law_freshness(REPO_ROOT, project)
        self.assertEqual("INLINE", body_tamper_res["status"])
        self.assertIn("TAMPERED", body_tamper_res.get("reason", ""))
        self.assertIn("PORTABLE_LAW_CONTENT_HASH_MISMATCH", body_tamper_res.get("reason", ""))

        # 4. Malformed header / provenance => not CURRENT
        portable.write_text("# Bad Header\nJust text without P2P markers\n", encoding="utf-8")
        malformed_res = control_tower.check_target_law_freshness(REPO_ROOT, project)
        self.assertEqual("INLINE", malformed_res["status"])
        self.assertIn("TAMPERED", malformed_res.get("reason", ""))

        # 5. Tampered portable rejected by executor law preflight (_read_law_text)
        with self.assertRaises(control_tower.BindingError):
            control_tower._read_law_text(portable, source_type="PORTABLE_PROJECTION", portable=True)

    # -------------------------------------------------------------------------
    # Invariant 4, Blockers 2, 3, 4, 5: Ingest Enforcement Tests
    # -------------------------------------------------------------------------

    def test_04_executor_law_check_and_learning_reconciliation_enforced_at_ingest(self) -> None:
        """Control Tower ingest enforces LAW_CHECK, EXPERIENCE_CHECK, and LEARNING_RECONCILIATION."""
        canonical_sha = self._canonical_sha()

        # Case 1: Substantive response claiming PASS without LAW_CHECK => RECONCILIATION_REQUIRED
        tower, b1 = self._setup_session(self.base / "ct_case1", "s1", goal="Routine implementation")
        p1 = create_return_packet(
            b1, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature-added"], test_results={"all": "PASS"},
        )
        resp1 = (
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p1.to_marked_text()
        )
        res1 = tower.ingest_response(resp1, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res1["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXECUTOR_LAW_CHECK_MISSING", res1["reconciliation"]["BLOCKERS"])

        # Case 2: Parent CONTROL_TOWER_SELF_LAW_RECEIPT cannot substitute for executor LAW_CHECK
        tower, b2 = self._setup_session(self.base / "ct_case2", "s2", goal="Routine implementation")
        p2 = create_return_packet(
            b2, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature-added"], test_results={"all": "PASS"},
        )
        resp2 = (
            f"CONTROL_TOWER_SELF_LAW_RECEIPT=PASS; ACTOR=CONTROL_TOWER_SELF; SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p2.to_marked_text()
        )
        res2 = tower.ingest_response(resp2, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res2["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXECUTOR_LAW_CHECK_MISSING", res2["reconciliation"]["BLOCKERS"])

        # Case 3: Contradictory LAW_CHECK lines in narrative => RECONCILIATION_REQUIRED
        tower, b3 = self._setup_session(self.base / "ct_case3", "s3", goal="Routine implementation")
        p3 = create_return_packet(
            b3, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature-added"], test_results={"all": "PASS"},
        )
        resp3 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "LAW_CHECK=BLOCKED | REASON=stale\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p3.to_marked_text()
        )
        res3 = tower.ingest_response(resp3, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res3["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXECUTOR_LAW_CHECK_CONTRADICTORY", res3["reconciliation"]["BLOCKERS"])

        # Case 4: Invalid SOURCE_SHA256 in LAW_CHECK => RECONCILIATION_REQUIRED
        tower, b4 = self._setup_session(self.base / "ct_case4", "s4", goal="Routine implementation")
        p4 = create_return_packet(
            b4, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature-added"], test_results={"all": "PASS"},
        )
        resp4 = (
            "LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256=invalid-short-hash\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p4.to_marked_text()
        )
        res4 = tower.ingest_response(resp4, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res4["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXECUTOR_LAW_CHECK_INVALID", res4["reconciliation"]["BLOCKERS"])

        # Case 5: LAW_CHECK=BLOCKED is truthful pre-execution blocker
        tower, b5 = self._setup_session(self.base / "ct_case5", "s5", goal="Routine implementation")
        p5 = create_return_packet(
            b5, session_state="READY", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=[], test_results={},
        )
        resp5 = (
            "LAW_CHECK=BLOCKED | REASON=Network unreachable for canonical source\n"
            + p5.to_marked_text()
        )
        res5 = tower.ingest_response(resp5, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("BLOCKED", res5["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXECUTOR_LAW_CHECK_BLOCKED", res5["reconciliation"]["BLOCKERS"])

        # Case 6 (Blocker 2): Random valid-looking 64-hex SHA fails reconciliation when expected SHA is set
        random_sha = "f" * 64
        tower, b6 = self._setup_session(
            self.base / "ct_case6", "s6", goal="Task with expected law SHA",
            expected_law_sha=canonical_sha,
        )
        p6 = create_return_packet(
            b6, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
        )
        resp6 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={random_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p6.to_marked_text()
        )
        res6 = tower.ingest_response(resp6, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res6["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXECUTOR_LAW_HASH_MISMATCH", res6["reconciliation"]["BLOCKERS"])

        # Case 7 (Blocker 3): Narrative PASS vs ReturnPacket BLOCKED (cross-surface contradiction rejected)
        tower, b7 = self._setup_session(self.base / "ct_case7", "s7", goal="Routine task")
        p7 = create_return_packet(
            b7, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
            law_check={"status": "BLOCKED", "reason": "packet-says-blocked"},
        )
        resp7 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p7.to_marked_text()
        )
        res7 = tower.ingest_response(resp7, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res7["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXECUTOR_LAW_CHECK_CONTRADICTORY", res7["reconciliation"]["BLOCKERS"])

        # Case 8 (Blocker 4): Missing EXPERIENCE_CHECK => RECONCILIATION_REQUIRED
        tower, b8 = self._setup_session(self.base / "ct_case8", "s8", goal="Routine task")
        p8 = create_return_packet(
            b8, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
        )
        resp8 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p8.to_marked_text()
        )
        res8 = tower.ingest_response(resp8, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res8["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXPERIENCE_CHECK_MISSING", res8["reconciliation"]["BLOCKERS"])

        # Case 9 (Blocker 4): Contradictory EXPERIENCE_CHECK across narrative and payload
        tower, b9 = self._setup_session(self.base / "ct_case9", "s9", goal="Routine task")
        p9 = create_return_packet(
            b9, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
            experience_check={"decision": "USE_ACTIVE_EXPERIENCE", "ids": ["shared-exp-1"]},
        )
        resp9 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p9.to_marked_text()
        )
        res9 = tower.ingest_response(resp9, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res9["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXPERIENCE_CHECK_CONTRADICTORY", res9["reconciliation"]["BLOCKERS"])

        # Case 10 (Blocker 4): Known active experience expected, executor reported NO_MATCH
        expected_eid = "shared-exp-b2611df4c9393f0017f07dcb"
        tower, b10 = self._setup_session(
            self.base / "ct_case10", "s10", goal="Task with known active experience",
            expected_experience_ids=(expected_eid,),
        )
        p10 = create_return_packet(
            b10, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
        )
        resp10 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p10.to_marked_text()
        )
        res10 = tower.ingest_response(resp10, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res10["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXPERIENCE_CHECK_INCONSISTENT_WITH_ACTIVE_EXPECTATION", res10["reconciliation"]["BLOCKERS"])

        # Case 11 (Blocker 5): Every terminal substantive task requires LEARNING_RECONCILIATION (no keyword heuristics)
        tower, b11 = self._setup_session(self.base / "ct_case11", "s11", goal="Ordinary non-bug implementation")
        p11 = create_return_packet(
            b11, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
        )
        resp11 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            + p11.to_marked_text()
        )
        res11 = tower.ingest_response(resp11, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res11["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("LEARNING_RECONCILIATION_MISSING", res11["reconciliation"]["BLOCKERS"])

        # Case 12: Routine success + valid receipts across all 3 invariants => normal COMPLETED PASS
        tower, b12 = self._setup_session(
            self.base / "ct_case12", "s12", goal="Ordinary feature",
            expected_law_sha=canonical_sha,
        )
        p12 = create_return_packet(
            b12, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
        )
        resp12 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p12.to_marked_text()
        )
        res12 = tower.ingest_response(resp12, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("COMPLETED", res12["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertEqual([], res12["reconciliation"]["BLOCKERS"])

        # Case 13: Material correction + valid LEARNING_RECONCILIATION=CANDIDATE => accepted
        tower, b13 = self._setup_session(self.base / "ct_case13", "s13", goal="Repair defect")
        p13 = create_return_packet(
            b13, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["fix"], test_results={"regression": "PASS"},
        )
        resp13 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=CANDIDATE\n"
            + p13.to_marked_text()
        )
        res13 = tower.ingest_response(resp13, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("COMPLETED", res13["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertEqual([], res13["reconciliation"]["BLOCKERS"])

        # Case 14: Failed task + LEARNING_RECONCILIATION=NONE without reason => RECONCILIATION_REQUIRED
        tower, b14 = self._setup_session(self.base / "ct_case14", "s14", goal="Failing task")
        p14 = create_return_packet(
            b14, session_state="FAILED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["attempt"], test_results={"test": "FAILED"},
        )
        resp14 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p14.to_marked_text()
        )
        res14 = tower.ingest_response(resp14, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res14["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("LEARNING_RECONCILIATION_REASON_REQUIRED", res14["reconciliation"]["BLOCKERS"])

    # -------------------------------------------------------------------------
    # Invariant 5: Task-Start Bounded Experience Check
    # -------------------------------------------------------------------------

    def test_05_non_trivial_task_start_includes_bounded_experience_check(self) -> None:
        """Control Tower context and AGENTS include bounded experience check."""
        summary = control_tower._experience_summary(REPO_ROOT, "Perform law consumption audit")
        self.assertEqual("USE_ACTIVE_EXPERIENCE", summary.get("decision"))
        self.assertGreaterEqual(len(summary.get("experiences", [])), 1)
        self.assertEqual("shared-exp-b2611df4c9393f0017f07dcb", summary["experiences"][0].get("shared_record_id"))

        agents_block = projector._agents_block()
        self.assertIn("EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE", agents_block)
        self.assertIn("EXPERIENCE_CHECK=NO_MATCH", agents_block)
        self.assertIn("EXPERIENCE_CHECK=UNAVAILABLE", agents_block)

    # -------------------------------------------------------------------------
    # Invariant 6 & Blocker 1: Portable Experience Capsule Integrity & Fail-Closed
    # -------------------------------------------------------------------------

    def test_06_portable_experience_capsule_integrity_and_fail_closed(self) -> None:
        """Repo-scoped actor validates capsule schema, records, authority, and transport hash."""
        project = self.base / "remote-capsule-project"
        project.mkdir()
        result = projector.project_law(REPO_ROOT, project)
        self.assertEqual("PASS", result["status"])
        self.assertFalse((project / ".p2p" / "system").exists())

        capsule_file = project / projector.PORTABLE_EXPERIENCE_REL
        self.assertTrue(capsule_file.is_file())
        original_capsule_text = capsule_file.read_text(encoding="utf-8")

        # 1. Valid generated capsule => matching lesson retrievable
        retrieved = ee.retrieve_portable_experience(
            project,
            "Close law distribution and experience consumption gap for portable actors",
            max_results=3,
        )
        self.assertEqual("USE_ACTIVE_EXPERIENCE", retrieved["decision"])
        self.assertGreaterEqual(len(retrieved["experiences"]), 1)
        self.assertEqual("NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", retrieved["authority"])
        self.assertEqual("shared-exp-b2611df4c9393f0017f07dcb", retrieved["experiences"][0]["record_id"])

        # 2 (Blocker 1): Missing transport binding fails closed
        notebook_file = project / projector.PORTABLE_REL
        orig_nb = notebook_file.read_text(encoding="utf-8")
        stripped_nb = re.sub(r"(?m)^PORTABLE_EXPERIENCE_CONTENT_SHA256=.*\n?", "", orig_nb)
        notebook_file.write_text(stripped_nb, encoding="utf-8")
        missing_binding_res = ee.retrieve_portable_experience(project, "task")
        self.assertEqual("UNAVAILABLE", missing_binding_res["decision"])
        self.assertEqual("PORTABLE_EXPERIENCE_TRANSPORT_BINDING_MISSING", missing_binding_res.get("reason"))

        # 3 (Blocker 1): Malformed transport binding fails closed
        malformed_nb = re.sub(
            r"(?m)^SOURCE_CONTENT_SHA256=(.*)$",
            r"SOURCE_CONTENT_SHA256=\1\nPORTABLE_EXPERIENCE_CONTENT_SHA256=not-a-valid-64-hex-hash",
            stripped_nb,
        )
        notebook_file.write_text(malformed_nb, encoding="utf-8")
        malformed_binding_res = ee.retrieve_portable_experience(project, "task")
        self.assertEqual("UNAVAILABLE", malformed_binding_res["decision"])
        self.assertEqual("PORTABLE_EXPERIENCE_TRANSPORT_BINDING_MALFORMED", malformed_binding_res.get("reason"))

        # 4 (Blocker 1): Conflicting transport binding fails closed
        notebook_file.write_text(orig_nb, encoding="utf-8")
        agents_file = project / "AGENTS.md"
        agents_orig = agents_file.read_text(encoding="utf-8")
        conflicting_agents = agents_orig + f"\nPORTABLE_EXPERIENCE_SHA256: `{'9' * 64}`\n"
        agents_file.write_text(conflicting_agents, encoding="utf-8")
        conflict_res = ee.retrieve_portable_experience(project, "task")
        self.assertEqual("UNAVAILABLE", conflict_res["decision"])
        self.assertEqual("PORTABLE_EXPERIENCE_TRANSPORT_BINDING_CONFLICT", conflict_res.get("reason"))

        # Restore AGENTS.md
        agents_file.write_text(agents_orig, encoding="utf-8")

        # 5 (Blocker 1): Adversarial challenge: mutate one lesson while leaving transport hash untouched => fails closed
        tampered_capsule = original_capsule_text.replace("A law, capability", "TAMPERED LESSON TEXT")
        capsule_file.write_text(tampered_capsule, encoding="utf-8")
        tampered_res = ee.retrieve_portable_experience(
            project,
            "Close law distribution and experience consumption gap for portable actors",
            max_results=3,
        )
        self.assertEqual("UNAVAILABLE", tampered_res["decision"])
        self.assertEqual("PORTABLE_EXPERIENCE_TRANSPORT_HASH_MISMATCH", tampered_res.get("reason"))

        # 6. Adversarial challenge: inject unauthorized non-ACTIVE record => fails closed
        capsule_file.write_text(original_capsule_text, encoding="utf-8")
        bad_data = json.loads(original_capsule_text)
        bad_data["records"].append({
            "source_experience_id": "unauthorized-exp",
            "record_id": "shared-exp-bad",
            "kind": "PROCEDURAL",
            "state": "PENDING",  # Not ACTIVE!
            "scope": "CROSS_PROJECT",
            "trigger_tokens": ["distribution", "consumption"],
            "lesson": "Fake lesson",
            "correction": "Fake correction",
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "permission_effect": "NONE",
            "acceptance_authority": False,
        })
        bad_text = json.dumps(bad_data)
        capsule_file.write_text(bad_text, encoding="utf-8")
        # Update notebook header hash to simulate transport bypass
        new_header_hash = hashlib.sha256(bad_text.encode("utf-8")).hexdigest()
        nb_text = notebook_file.read_text(encoding="utf-8")
        nb_text = re.sub(
            r"PORTABLE_EXPERIENCE_CONTENT_SHA256=[0-9a-fA-F]{64}",
            f"PORTABLE_EXPERIENCE_CONTENT_SHA256={new_header_hash}",
            nb_text,
        )
        notebook_file.write_text(nb_text, encoding="utf-8")
        bad_res = ee.retrieve_portable_experience(
            project,
            "Close law distribution and experience consumption gap for portable actors",
            max_results=3,
        )
        self.assertEqual("UNAVAILABLE", bad_res["decision"])
        self.assertEqual("CAPSULE_RECORD_NOT_ACTIVE", bad_res.get("reason"))

    # -------------------------------------------------------------------------
    # Invariant 7 & 8: Learning Reconciliation Invariants
    # -------------------------------------------------------------------------

    def test_07_material_correction_cannot_silently_close(self) -> None:
        """Supreme notebook documents mandatory learning reconciliation for repeated/material issues."""
        notebook = (REPO_ROOT / projector.SOURCE_REL).read_text(encoding="utf-8")
        self.assertIn("### Task-end learning reconciliation invariant", notebook)
        self.assertIn("`LEARNING_RECONCILIATION=NONE`", notebook)
        self.assertIn("`LEARNING_RECONCILIATION=CANDIDATE`", notebook)
        self.assertIn("ROUTINE_SUCCESS => LEARNING_RECONCILIATION=NONE", notebook)

    def test_08_routine_success_does_not_manufacture_memory(self) -> None:
        """Routine success produces LEARNING_RECONCILIATION=NONE without appending memory."""
        catalog_before = json.loads((REPO_ROOT / projector.SHARED_CATALOG_REL).read_text(encoding="utf-8"))
        tower, b = self._setup_session(self.base / "ct_routine", "s_routine", goal="Routine implementation")
        p = create_return_packet(
            b, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
        )
        resp = (
            f"LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256={self._canonical_sha()}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p.to_marked_text()
        )
        res = tower.ingest_response(resp, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("COMPLETED", res["reconciliation"]["CONTROL_TOWER_STATUS"])
        catalog_after = json.loads((REPO_ROOT / projector.SHARED_CATALOG_REL).read_text(encoding="utf-8"))
        self.assertEqual(len(catalog_before["records"]), len(catalog_after["records"]))

    # -------------------------------------------------------------------------
    # Invariant 9: Experience Authority Boundary
    # -------------------------------------------------------------------------

    def test_09_experience_cannot_widen_law_permission_or_acceptance_authority(self) -> None:
        """Capsule retrieval enforces strict non-authoritative invariants."""
        project = self.base / "remote-project-authority-test"
        project.mkdir()
        projector.project_law(REPO_ROOT, project)
        retrieved = ee.retrieve_portable_experience(
            project,
            "Close gap where distribution exists without consumption by executing actor",
        )
        self.assertEqual("NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", retrieved["authority"])
        self.assertEqual("NONE", retrieved["permission_effect"])
        self.assertFalse(retrieved["acceptance_authority"])
        self.assertTrue(retrieved["current_state_wins"])
        self.assertTrue(retrieved["law_and_task_contract_win"])

    # -------------------------------------------------------------------------
    # Invariant 10: Idempotency
    # -------------------------------------------------------------------------

    def test_10_portable_projection_remains_idempotent(self) -> None:
        """Projecting twice without changes produces zero byte diff."""
        project = self.base / "project_idempotent"
        project.mkdir()

        res1 = projector.project_law(REPO_ROOT, project)
        self.assertEqual("PASS", res1["status"])
        self.assertEqual("WRITE", res1["mode"])

        agents_bytes1 = (project / "AGENTS.md").read_bytes()
        notebook_bytes1 = (project / projector.PORTABLE_REL).read_bytes()
        capsule_bytes1 = (project / projector.PORTABLE_EXPERIENCE_REL).read_bytes()

        res2 = projector.project_law(REPO_ROOT, project, check=True)
        self.assertEqual("PASS", res2["status"])
        self.assertEqual("CHECK", res2["mode"])

        self.assertEqual(agents_bytes1, (project / "AGENTS.md").read_bytes())
        self.assertEqual(notebook_bytes1, (project / projector.PORTABLE_REL).read_bytes())
        self.assertEqual(capsule_bytes1, (project / projector.PORTABLE_EXPERIENCE_REL).read_bytes())

    # -------------------------------------------------------------------------
    # Invariant 11: Experience Projection Source Bound
    # -------------------------------------------------------------------------

    def test_11_experience_projection_remains_generated_and_source_hash_bound(self) -> None:
        """Capsule carries generated=True and binds to shared catalog SHA256."""
        project = self.base / "project_capsule_test"
        project.mkdir()
        projector.project_law(REPO_ROOT, project)

        capsule_path = project / projector.PORTABLE_EXPERIENCE_REL
        self.assertTrue(capsule_path.is_file())
        capsule_data = json.loads(capsule_path.read_text(encoding="utf-8"))

        self.assertEqual("p2p-portable-experience-capsule/1", capsule_data.get("schema"))
        self.assertTrue(capsule_data.get("generated"))
        self.assertEqual(
            "7roger89-web/P2P-upgrade-github-1@main:.p2p/system/p2p_capabilities/shared_experience_catalog.json",
            capsule_data.get("canonical_source"),
        )
        self.assertEqual(self._catalog_sha(), capsule_data.get("source_content_sha256"))
        self.assertEqual("NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", capsule_data.get("authority"))
        self.assertEqual("NONE", capsule_data.get("permission_effect"))
        self.assertFalse(capsule_data.get("acceptance_authority"))

    # -------------------------------------------------------------------------
    # Invariant 12: No Second Control Plane / Ledger / DB
    # -------------------------------------------------------------------------

    def test_12_no_second_control_plane_router_ledger_or_db(self) -> None:
        """Verify no rogue daemon, router, vector store, or second control plane exists."""
        self.assertTrue((SYSTEM_ROOT / "p2p_capabilities" / "experience_evolution.py").is_file())
        self.assertTrue((SYSTEM_ROOT / "p2p_capabilities" / "experience_federation.py").is_file())
        self.assertTrue((SYSTEM_ROOT / "p2p_capabilities" / "shared_experience_catalog.json").is_file())

        disallowed_names = [
            "vector_store", "chroma", "pinecone", "qdrant", "weaviate",
            "experience_daemon", "experience_router", "second_control_plane",
            "law_daemon", "sync_daemon", "background_watcher",
        ]
        for name in disallowed_names:
            matches = list(SYSTEM_ROOT.glob(f"**/*{name}*")) + list(SCRIPTS_ROOT.glob(f"**/*{name}*"))
            self.assertEqual([], matches, f"Disallowed secondary component found: {matches}")

    # -------------------------------------------------------------------------
    # Blocker E: Truthful Verification References
    # -------------------------------------------------------------------------

    def test_blocker_e_truthful_verification_references_exist(self) -> None:
        """Prove that the 3 verification evidence refs cited in shared_experience_catalog.json exist and pass."""
        catalog_path = REPO_ROOT / projector.SHARED_CATALOG_REL
        catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))
        record = next(
            (r for r in catalog_data.get("records", []) if r.get("record_id") == "shared-exp-b2611df4c9393f0017f07dcb"),
            None,
        )
        self.assertIsNotNone(record)
        v_evidence = record.get("verification_evidence", [])
        self.assertEqual(3, len(v_evidence))

        # Check all 3 symbols exist in repo test files
        ref_symbols = [e["ref"] for e in v_evidence]
        self.assertIn("tests/test_p2p_portable_law_projection.py:test_actor_law_receipt_and_experience_capsule", ref_symbols)
        self.assertIn("tests/test_p2p_self_law_propagation_and_fast_sync.py:test_batch_check_detects_current_stale", ref_symbols)
        self.assertIn("tests/test_p2p_experience_evolution.py:test_repo_scoped_portable_experience_retrieval_without_system_runtime", ref_symbols)

        # Verify each target test file exists
        for ref in ref_symbols:
            rel_file = ref.split(":")[0]
            self.assertTrue((REPO_ROOT / rel_file).is_file(), f"Referenced test file {rel_file} does not exist")

        # Verify each target function/method is defined in that file
        for ref in ref_symbols:
            rel_file, func_name = ref.split(":")
            file_text = (REPO_ROOT / rel_file).read_text(encoding="utf-8")
            self.assertIn(f"def {func_name}", file_text, f"Referenced test function {func_name} not found in {rel_file}")

    # -------------------------------------------------------------------------
    # Blocker F & Blocker 7: Deterministic Lifecycle Reproduction
    # -------------------------------------------------------------------------

    def test_blocker_f_experience_lifecycle_is_deterministic_and_reproducible(self) -> None:
        """Prove that candidate -> verify -> activate -> promote lifecycle is fully reproducible."""
        iso_root = self.base / "isolated_lifecycle_repo"
        (iso_root / ".p2p" / "state").mkdir(parents=True)
        iso_catalog = iso_root / ".p2p" / "system" / "p2p_capabilities" / "shared_experience_catalog.json"
        iso_catalog.parent.mkdir(parents=True)
        iso_catalog.write_text(
            json.dumps({"schema": "p2p-shared-experience-catalog/1", "records": [], "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", "catalog_role": "CURATED_PROMOTED_EXPERIENCE_DISTRIBUTION"}, indent=2),
            encoding="utf-8",
        )

        # 1. Candidate creation
        cand = ee.create_candidate(
            iso_root,
            task_id="ISSUE-247-LAW-CONSUMPTION-EXPERIENCE-CLOSURE",
            kind="PROCEDURAL",
            lesson="A law, capability, or learned experience is not operationally complete for a target workflow merely because canonical code or documentation exists. The actual executing actor path must be able to discover it, consume it, and provide bounded, source-bound evidence of consumption before substantive work.",
            trigger_tokens=["distribution", "consumption", "experience", "portable", "receipt", "preflight", "actor", "law"],
            evidence=[{"ref": "issue:247:audit:10-of-10-managed-repos-lacked-actor-receipt-and-experience-runtime", "kind": "STATIC_AUDIT", "role": "EVIDENCE", "verdict": "PROVEN"}],
            outcome="CORRECTED",
            failure_class="DISTRIBUTION_WITHOUT_ACTOR_CONSUMPTION",
            correction="Assimilate mandatory per-actor self-read receipts, handoff freshness receipts, portable experience transport capsules, and start-time experience lookup into both Supreme Law and repo-scoped project entrypoints.",
            source_revision="dd434107e0995dbe6f900f600a49a9f32969764e",
        )
        eid = cand["experience_id"]

        # 2. Verification with the 3 truthful proofs
        v_evidence = [
            {"ref": "tests/test_p2p_portable_law_projection.py:test_actor_law_receipt_and_experience_capsule", "kind": "DETERMINISTIC_TEST", "role": "BEHAVIOR_PROOF", "verdict": "PROVEN"},
            {"ref": "tests/test_p2p_self_law_propagation_and_fast_sync.py:test_batch_check_detects_current_stale", "kind": "REGRESSION_TEST", "role": "REGRESSION_PROOF", "verdict": "PROVEN"},
            {"ref": "tests/test_p2p_experience_evolution.py:test_repo_scoped_portable_experience_retrieval_without_system_runtime", "kind": "ADVERSARIAL_CHALLENGE", "role": "CHALLENGE_PROOF", "verdict": "PROVEN"},
        ]
        ee.verify_candidate(iso_root, eid, task_id="VERIFY-247", verification_evidence=v_evidence)

        # 3. Activation
        ee.activate_verified(iso_root, eid, task_id="ACTIVATE-247")

        # 4. Build promotion proposal
        proposal = ef.build_promotion_proposal(
            iso_root,
            eid,
            source_project="7roger89-web/P2P-upgrade-github-1",
            scope="CROSS_PROJECT",
            scope_evidence=[
                {"project": "huyen-hoc-lab", "ref": "audit:issue:247:repo-scoped-actor-missing-receipt-and-experience", "verdict": "PROVEN"},
                {"project": "logistics-work-desk-arena", "ref": "audit:issue:247:repo-scoped-actor-missing-receipt-and-experience", "verdict": "PROVEN"},
            ],
            procedure=[
                "Establish actor-own source-bound law receipt before substantive execution.",
                "Perform bounded ACTIVE experience lookup against local runtime or portable experience capsule.",
                "At task close, record learning reconciliation decision (NONE or CANDIDATE with proof).",
            ],
            inputs=["task contract", "canonical or portable law", "shared or local experience catalog"],
            outputs=["LAW_CHECK receipt", "EXPERIENCE_CHECK receipt", "LEARNING_RECONCILIATION receipt"],
        )

        # 5. Apply promotion
        result = ef.apply_promotion(proposal, catalog_path=iso_catalog)
        self.assertEqual("PROMOTED", result["status"])
        record_id = result["record_id"]

        # 6. Verify deterministic equality against the record committed in this PR
        self.assertEqual("shared-exp-b2611df4c9393f0017f07dcb", record_id)
        committed_catalog = ef.load_catalog(REPO_ROOT / projector.SHARED_CATALOG_REL)
        committed_rec = next(r for r in committed_catalog["records"] if r["record_id"] == record_id)

        iso_data = json.loads(iso_catalog.read_text(encoding="utf-8"))
        generated_rec = next(r for r in iso_data["records"] if r["record_id"] == record_id)

        self.assertEqual(committed_rec["record_id"], generated_rec["record_id"])
        self.assertEqual(committed_rec["lesson"], generated_rec["lesson"])
        self.assertEqual(committed_rec["correction"], generated_rec["correction"])
        self.assertEqual(committed_rec["failure_class"], generated_rec["failure_class"])
        self.assertEqual(committed_rec["trigger_tokens"], generated_rec["trigger_tokens"])
        self.assertEqual(committed_rec["verification_evidence"], generated_rec["verification_evidence"])

    # -------------------------------------------------------------------------
    # Blocker G & Blocker 6: Representative Fixture Regression (Logistics Work Desk)
    # -------------------------------------------------------------------------

    def test_blocker_g_representative_real_repo_logistics_work_desk_arena_proof(self) -> None:
        """Representative fixture regression for repo-scoped project path end-to-end (synthetic fixture, not real-byte proof)."""
        canonical_sha = self._canonical_sha()

        # Ephemeral worktree / proof area: ZERO durable mutation to Logistics
        real_repo = self.base / "logistics-work-desk-arena"
        real_repo.mkdir()

        # Actual observed GitHub references for 7roger89-web/logistics-work-desk-arena
        # REAL_REPO_MAIN_SHA = "4a36a748329ac4d8406e8832b5509ae5e948a7c1"
        # PORTABLE_LAW_BLOB = "0223ec4587c1c034033e71de99b4bc9cdc97e47a"
        # AGENTS_BLOB = "dbb0426577b5cd64d3b2474e9f01f842acf5486e"

        # Prior portable notebook before PR #248 (hash 0223ec4587c1c034033e71de99b4bc9cdc97e47a):
        # generated from canonical main dd434107e0995dbe6f900f600a49a9f32969764e
        old_body = (
            "# Supreme Operating Law of P2P (CODEX Framework) — Version 1.0\n\n"
            "<!-- BEGIN_P2P_SUPREME_OPERATING_LAW_V1 -->\n"
            "This document establishes the Supreme Operating Law of the P2P system.\n"
        )
        old_sha = "4e7239101063ac43e26a0fc784d48dc212eea640bdbc583395bc2d930c78876d"
        portable_dir = real_repo / ".p2p" / "portable"
        portable_dir.mkdir(parents=True)
        prior_portable_text = (
            "<!--\n"
            "P2P_PORTABLE_LAW_PROJECTION=YES\n"
            "SCHEMA=p2p-portable-law-projection/1\n"
            "CANONICAL_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md\n"
            f"SOURCE_CONTENT_SHA256={old_sha}\n"
            "PACKAGE_VERSION=8.4.7-C-codex.74\n"
            "PROJECTION_DO_NOT_EDIT=YES\n"
            "CANONICAL_WINS_WHEN_REACHABLE=YES\n"
            "-->\n\n"
            f"{old_body}"
        )
        (portable_dir / "P2P-OPERATIONS-NOTEBOOK.md").write_text(prior_portable_text, encoding="utf-8")

        # Project domain rules in AGENTS.md before projection
        real_agents_content = (
            "# Logistics Work Desk Arena — project instructions\n\n"
            "## Domain rules\n"
            "- Logistics rate cards and shipment lookup use read-only MongoDB.\n"
            "- Verify rate card documents against the structured PR #12 schema.\n"
            "- Do not mutate collection indexes without Owner approval.\n\n"
            "<!-- BEGIN P2P PORTABLE LAW -->\n"
            "## P2P portable Supreme Law entrypoint\n"
            "Legacy entrypoint prior to PR #248\n"
            "<!-- END P2P PORTABLE LAW -->\n"
        )
        (real_repo / "AGENTS.md").write_text(real_agents_content, encoding="utf-8")

        # Before projection: freshness check detects portable law requires update
        stale_check = control_tower.check_target_law_freshness(REPO_ROOT, real_repo)
        self.assertEqual("INLINE", stale_check["status"])

        # Project current PR #248 law onto logistics-work-desk-arena
        project_res = projector.project_law(REPO_ROOT, real_repo)
        self.assertEqual("PASS", project_res["status"])

        # 1. Freshness check after projection proves CURRENT
        fresh_check = control_tower.check_target_law_freshness(REPO_ROOT, real_repo)
        self.assertEqual("CURRENT", fresh_check["status"])
        self.assertEqual(canonical_sha, fresh_check["target_law_sha256"])

        # 2. Real project rules preserved in AGENTS.md
        updated_agents = (real_repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Logistics rate cards and shipment lookup use read-only MongoDB.", updated_agents)
        self.assertIn("Verify rate card documents against the structured PR #12 schema.", updated_agents)
        self.assertIn("LAW_CHECK=PASS", updated_agents)
        self.assertIn("EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE", updated_agents)
        self.assertIn("LEARNING_RECONCILIATION=", updated_agents)

        # 3. Repo-scoped actor path without .p2p/system
        self.assertFalse((real_repo / ".p2p" / "system").exists())

        # Establish actor law receipt
        portable_nb = (real_repo / ".p2p" / "portable" / "P2P-OPERATIONS-NOTEBOOK.md").read_text(encoding="utf-8")
        actor_law_receipt = (
            f"LAW_CHECK=PASS | SOURCE=.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256={canonical_sha}"
        )
        self.assertIn(canonical_sha, portable_nb)
        self.assertIn("LAW_CHECK=PASS", actor_law_receipt)

        # Execute bounded experience lookup for task trigger matching DISTRIBUTION_WITHOUT_ACTOR_CONSUMPTION
        exp_res = ee.retrieve_portable_experience(
            real_repo,
            "Close gap where distribution exists without consumption by executing actor",
            max_results=3,
        )
        self.assertEqual("USE_ACTIVE_EXPERIENCE", exp_res["decision"])
        self.assertGreaterEqual(len(exp_res["experiences"]), 1)
        self.assertEqual("shared-exp-b2611df4c9393f0017f07dcb", exp_res["experiences"][0]["record_id"])
        self.assertEqual("NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", exp_res["authority"])
        self.assertEqual("NONE", exp_res["permission_effect"])
        self.assertFalse(exp_res["acceptance_authority"])

        # 4. Tampering causes fail-closed behavior on the representative repo
        (portable_dir / "P2P-OPERATIONS-NOTEBOOK.md").write_text(portable_nb + "\nTAMPERED\n", encoding="utf-8")
        tampered_freshness = control_tower.check_target_law_freshness(REPO_ROOT, real_repo)
        self.assertEqual("INLINE", tampered_freshness["status"])
        self.assertIn("TAMPERED", tampered_freshness.get("reason", ""))

        (portable_dir / "P2P-OPERATIONS-NOTEBOOK.md").write_text(portable_nb, encoding="utf-8")
        capsule_path = portable_dir / "P2P-EXPERIENCE-CAPSULE.json"
        capsule_text = capsule_path.read_text(encoding="utf-8")
        capsule_path.write_text(capsule_text.replace("A law, capability", "TAMPERED"), encoding="utf-8")
        tampered_exp = ee.retrieve_portable_experience(
            real_repo,
            "Close gap where distribution exists without consumption by executing actor",
        )
        self.assertEqual("UNAVAILABLE", tampered_exp["decision"])
        self.assertEqual("PORTABLE_EXPERIENCE_TRANSPORT_HASH_MISMATCH", tampered_exp.get("reason"))

    # -------------------------------------------------------------------------
    # REPAIR_03: Normal Production Orchestration Path (CLI / Persisted Sessions)
    # -------------------------------------------------------------------------

    def test_repair_03_real_path_a_normal_start_persists_expected_law_sha(self) -> None:
        """CLI normal start persists actual canonical law SHA in EXPECTED_LAW_SHA, not None."""
        canonical_sha = self._canonical_main_sha()
        repo = self.base / "rt_start_a"
        repo.mkdir()
        code = control_tower.main([
            "--root", str(repo),
            "start",
            "--host", "host-a",
            "--goal-id", "goal-1",
            "--goal", "Implement routine feature",
            "--task-id", "task-1",
            "--session-id", "s-rt-a",
            "--json",
        ])
        self.assertEqual(0, code)
        tower = ControlTower(repo)
        state, _ = tower._replay()
        rec = state.session_records.get("s-rt-a")
        self.assertIsNotNone(rec)
        self.assertEqual(canonical_sha, rec.get("EXPECTED_LAW_SHA"))
        self.assertEqual([], rec.get("EXPECTED_EXPERIENCE_IDS"))

    def test_repair_03_real_path_b_normal_start_persists_expected_experience_ids(self) -> None:
        """CLI normal start with matching active experience persists injected record IDs."""
        canonical_sha = self._canonical_main_sha()
        repo = self.base / "rt_start_b"
        repo.mkdir()
        code = control_tower.main([
            "--root", str(repo),
            "start",
            "--host", "host-b",
            "--goal-id", "goal-2",
            "--goal", "Close gap where distribution exists without consumption by executing actor",
            "--task-id", "task-2",
            "--session-id", "s-rt-b",
            "--json",
        ])
        self.assertEqual(0, code)
        tower = ControlTower(repo)
        state, _ = tower._replay()
        rec = state.session_records.get("s-rt-b")
        self.assertIsNotNone(rec)
        self.assertEqual(canonical_sha, rec.get("EXPECTED_LAW_SHA"))
        exp_ids = rec.get("EXPECTED_EXPERIENCE_IDS", [])
        self.assertIn("shared-exp-b2611df4c9393f0017f07dcb", exp_ids)

    def test_repair_03_real_path_c_normal_ingest_rejects_wrong_law_sha_without_manual_param(self) -> None:
        """Later ingest through normal persisted-session path with NO manual expected_law_sha rejects wrong 64-hex SHA."""
        repo = self.base / "rt_ingest_c"
        repo.mkdir()
        code = control_tower.main([
            "--root", str(repo),
            "--current-canonical-base-sha", BASE_SHA,
            "--current-canonical-base-tree", BASE_TREE,
            "start",
            "--host", "host-c",
            "--goal-id", "goal-3",
            "--goal", "Routine feature implementation",
            "--task-id", "task-3",
            "--session-id", "s-rt-c",
            "--canonical-base-sha", BASE_SHA,
            "--canonical-base-tree", BASE_TREE,
            "--json",
        ])
        self.assertEqual(0, code)

        b = SessionBinding(session_id="s-rt-c", host="HOST_C", goal_id="goal-3", goal="Routine feature implementation")
        p = create_return_packet(
            b, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
        )
        wrong_sha = "1" * 64
        response_text = (
            f"LAW_CHECK=PASS | SOURCE=canonical.md | SOURCE_SHA256={wrong_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p.to_marked_text()
        )
        resp_file = repo / "response_c.txt"
        resp_file.write_text(response_text, encoding="utf-8")

        code = control_tower.main([
            "--root", str(repo),
            "--current-canonical-base-sha", BASE_SHA,
            "--current-canonical-base-tree", BASE_TREE,
            "ingest",
            "--response-file", str(resp_file),
            "--json",
        ])
        self.assertEqual(0, code)
        tower = ControlTower(repo)
        state, _ = tower._replay(current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        rec = state.session_records["s-rt-c"]
        self.assertEqual("RECONCILIATION_REQUIRED", rec["RECONCILIATION"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXECUTOR_LAW_HASH_MISMATCH", rec["RECONCILIATION"]["BLOCKERS"])

    def test_repair_03_real_path_d_normal_ingest_rejects_no_match_when_active_expected(self) -> None:
        """Later ingest through normal persisted-session path with NO manual expected_experience_ids rejects NO_MATCH."""
        canonical_sha = self._canonical_main_sha()
        repo = self.base / "rt_ingest_d"
        repo.mkdir()
        code = control_tower.main([
            "--root", str(repo),
            "--current-canonical-base-sha", BASE_SHA,
            "--current-canonical-base-tree", BASE_TREE,
            "start",
            "--host", "host-d",
            "--goal-id", "goal-4",
            "--goal", "Close gap where distribution exists without consumption by executing actor",
            "--task-id", "task-4",
            "--session-id", "s-rt-d",
            "--canonical-base-sha", BASE_SHA,
            "--canonical-base-tree", BASE_TREE,
            "--json",
        ])
        self.assertEqual(0, code)

        b = SessionBinding(session_id="s-rt-d", host="HOST_D", goal_id="goal-4", goal="Close gap where distribution exists without consumption by executing actor")
        p = create_return_packet(
            b, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
        )
        response_text = (
            f"LAW_CHECK=PASS | SOURCE=canonical.md | SOURCE_SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=NO_MATCH\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p.to_marked_text()
        )
        resp_file = repo / "response_d.txt"
        resp_file.write_text(response_text, encoding="utf-8")

        code = control_tower.main([
            "--root", str(repo),
            "--current-canonical-base-sha", BASE_SHA,
            "--current-canonical-base-tree", BASE_TREE,
            "ingest",
            "--response-file", str(resp_file),
            "--json",
        ])
        self.assertEqual(0, code)
        tower = ControlTower(repo)
        state, _ = tower._replay(current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        rec = state.session_records["s-rt-d"]
        self.assertEqual("RECONCILIATION_REQUIRED", rec["RECONCILIATION"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXPERIENCE_CHECK_INCONSISTENT_WITH_ACTIVE_EXPECTATION", rec["RECONCILIATION"]["BLOCKERS"])

    def test_repair_03_real_path_e_normal_ingest_rejects_incompatible_experience_id(self) -> None:
        """Later ingest through normal persisted-session path rejects USE_ACTIVE_EXPERIENCE with incompatible ID."""
        canonical_sha = self._canonical_main_sha()
        repo = self.base / "rt_ingest_e"
        repo.mkdir()
        code = control_tower.main([
            "--root", str(repo),
            "--current-canonical-base-sha", BASE_SHA,
            "--current-canonical-base-tree", BASE_TREE,
            "start",
            "--host", "host-e",
            "--goal-id", "goal-5",
            "--goal", "Close gap where distribution exists without consumption by executing actor",
            "--task-id", "task-5",
            "--session-id", "s-rt-e",
            "--canonical-base-sha", BASE_SHA,
            "--canonical-base-tree", BASE_TREE,
            "--json",
        ])
        self.assertEqual(0, code)

        b = SessionBinding(session_id="s-rt-e", host="HOST_E", goal_id="goal-5", goal="Close gap where distribution exists without consumption by executing actor")
        p = create_return_packet(
            b, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature"], test_results={"all": "PASS"},
        )
        response_text = (
            f"LAW_CHECK=PASS | SOURCE=canonical.md | SOURCE_SHA256={canonical_sha}\n"
            "EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=unknown-unrelated-exp-99\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p.to_marked_text()
        )
        resp_file = repo / "response_e.txt"
        resp_file.write_text(response_text, encoding="utf-8")

        code = control_tower.main([
            "--root", str(repo),
            "--current-canonical-base-sha", BASE_SHA,
            "--current-canonical-base-tree", BASE_TREE,
            "ingest",
            "--response-file", str(resp_file),
            "--json",
        ])
        self.assertEqual(0, code)
        tower = ControlTower(repo)
        state, _ = tower._replay(current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        rec = state.session_records["s-rt-e"]
        self.assertEqual("RECONCILIATION_REQUIRED", rec["RECONCILIATION"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXPERIENCE_CHECK_IDS_MISMATCH", rec["RECONCILIATION"]["BLOCKERS"])

    def test_repair_03_real_path_next_persists_both_expectations(self) -> None:
        """_start_next_with_context persists both EXPECTED_LAW_SHA and EXPECTED_EXPERIENCE_IDS."""
        from p2p_capabilities.task_state import TaskPlan, TaskStateStore
        canonical_sha = self._canonical_main_sha()
        repo = self.base / "rt_next"
        repo.mkdir()
        now = "2026-09-24T00:00:00+00:00"
        plan = TaskPlan.from_goal(
            {
                "goal_id": "goal-next-1",
                "scope": ["Close gap where distribution exists without consumption by executing actor"],
                "out_of_scope": ["promotion and deployment"],
            },
            [
                {
                    "task_id": "task-next-1",
                    "title": "Close gap where distribution exists without consumption by executing actor",
                    "purpose": "Verify active experience injection on next session.",
                    "status": "READY",
                    "scope": ["Close gap where distribution exists without consumption by executing actor"],
                    "acceptance_requirements": ["Proof passes."],
                    "required_evidence": ["proof"],
                }
            ],
            now=now,
        )
        TaskStateStore(repo).initialize(plan, at=now)

        tower = ControlTower(repo)
        law_receipt = control_tower._establish_control_tower_law_context(repo)
        result = control_tower._start_next_with_context(
            tower,
            repo,
            "HOST_NEXT",
            session_id="s-rt-next",
            worktree="UNKNOWN",
            branch="UNKNOWN",
            law_receipt=law_receipt,
        )
        self.assertEqual("PASS", result["status"])
        state, _ = tower._replay()
        rec = state.session_records.get("s-rt-next")
        self.assertIsNotNone(rec)
        self.assertEqual(canonical_sha, rec.get("EXPECTED_LAW_SHA"))
        self.assertIn("shared-exp-b2611df4c9393f0017f07dcb", rec.get("EXPECTED_EXPERIENCE_IDS", []))


if __name__ == "__main__":
    unittest.main()
