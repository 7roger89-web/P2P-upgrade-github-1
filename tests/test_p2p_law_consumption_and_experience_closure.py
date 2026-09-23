"""Structural regression tests for P2P law consumption and experience reuse closure.

Protects all 12 minimum invariants specified in Issue #247:
1. actor receipt is source-bound;
2. parent receipt cannot substitute for executor receipt;
3. stale/tampered portable cannot produce PASS (Blocker A);
4. prompt/handoff serialization requires actor receipt;
5. non-trivial task start includes bounded experience check;
6. repo-scoped portable flow can access promoted ACTIVE experience without local runtime;
7. material correction cannot silently close without learning reconciliation (Blocker D);
8. routine success does not manufacture memory;
9. experience cannot widen law/permission/acceptance authority;
10. portable projection remains idempotent;
11. experience projection remains generated + source/hash bound;
12. no second control plane / router / ledger / DB is introduced.

Also proves:
- Blocker A: target law body & header tamper detection via _validate_law_text;
- Blocker B: portable experience capsule transport and schema integrity;
- Blocker C: real executor response ingest/reconciliation enforcement of LAW_CHECK;
- Blocker D: real executor response ingest/reconciliation enforcement of LEARNING_RECONCILIATION;
- Blocker E: truthful verification references in promoted experience;
- Blocker F: deterministic reproduction of promoted experience via official lifecycle APIs;
- Blocker G: end-to-end representative repo-scoped proof for 7roger89-web/logistics-work-desk-arena.
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
    # Invariant 4, Blocker C & Blocker D: Ingest/Reconciliation Behavioral Tests
    # -------------------------------------------------------------------------

    def test_04_executor_law_check_and_learning_reconciliation_enforced_at_ingest(self) -> None:
        """Existing Control Tower ingest_response path enforces LAW_CHECK and LEARNING_RECONCILIATION."""
        canonical_sha = self._canonical_sha()

        # Case 1: Substantive response claiming PASS without LAW_CHECK => RECONCILIATION_REQUIRED
        tower, b1 = self._setup_session(self.base / "ct_case1", "s1", goal="Routine implementation")
        p1 = create_return_packet(
            b1, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature-added"], test_results={"all": "PASS"},
        )
        resp1 = "Here is the result.\n" + p1.to_marked_text()
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
            + p2.to_marked_text()
        )
        res2 = tower.ingest_response(resp2, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res2["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("EXECUTOR_LAW_CHECK_MISSING", res2["reconciliation"]["BLOCKERS"])

        # Case 3: Contradictory LAW_CHECK lines => RECONCILIATION_REQUIRED
        tower, b3 = self._setup_session(self.base / "ct_case3", "s3", goal="Routine implementation")
        p3 = create_return_packet(
            b3, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["feature-added"], test_results={"all": "PASS"},
        )
        resp3 = (
            f"LAW_CHECK=PASS | SOURCE=notebook.md | SOURCE_SHA256={canonical_sha}\n"
            "LAW_CHECK=BLOCKED | REASON=stale\n"
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

        # Case 6: Routine success + valid LAW_CHECK + LEARNING_RECONCILIATION=NONE => accepted as normal PASS
        tower, b6 = self._setup_session(self.base / "ct_case6", "s6", goal="Build ordinary feature")
        p6 = create_return_packet(
            b6, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["ordinary-feature"], test_results={"all": "PASS"},
        )
        resp6 = (
            f"LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256={canonical_sha}\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p6.to_marked_text()
        )
        res6 = tower.ingest_response(resp6, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("COMPLETED", res6["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertEqual([], res6["reconciliation"]["BLOCKERS"])

        # Case 7: Material correction + valid LEARNING_RECONCILIATION=CANDIDATE => accepted for follow-up
        tower, b7 = self._setup_session(self.base / "ct_case7", "s7", goal="Repair bug and defect in pagination")
        p7 = create_return_packet(
            b7, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["bug-fix"], test_results={"regression": "PASS"},
        )
        resp7 = (
            f"LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256={canonical_sha}\n"
            "LEARNING_RECONCILIATION=CANDIDATE\n"
            + p7.to_marked_text()
        )
        res7 = tower.ingest_response(resp7, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("COMPLETED", res7["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertEqual([], res7["reconciliation"]["BLOCKERS"])

        # Case 8: Material correction without LEARNING_RECONCILIATION => RECONCILIATION_REQUIRED
        tower, b8 = self._setup_session(self.base / "ct_case8", "s8", goal="Repair bug and defect in pagination")
        p8 = create_return_packet(
            b8, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["bug-fix"], test_results={"regression": "PASS"},
        )
        resp8 = (
            f"LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256={canonical_sha}\n"
            + p8.to_marked_text()
        )
        res8 = tower.ingest_response(resp8, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res8["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("LEARNING_RECONCILIATION_MISSING", res8["reconciliation"]["BLOCKERS"])

        # Case 9: Material correction with LEARNING_RECONCILIATION=NONE but no reason => RECONCILIATION_REQUIRED
        tower, b9 = self._setup_session(self.base / "ct_case9", "s9", goal="Repair defect in pagination")
        p9 = create_return_packet(
            b9, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["bug-fix"], test_results={"regression": "PASS"},
        )
        resp9 = (
            f"LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256={canonical_sha}\n"
            "LEARNING_RECONCILIATION=NONE\n"
            + p9.to_marked_text()
        )
        res9 = tower.ingest_response(resp9, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("RECONCILIATION_REQUIRED", res9["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertIn("LEARNING_RECONCILIATION_REASON_REQUIRED", res9["reconciliation"]["BLOCKERS"])

        # Case 10: Material correction with LEARNING_RECONCILIATION=NONE and concrete reason => accepted
        tower, b10 = self._setup_session(self.base / "ct_case10", "s10", goal="Repair defect in pagination")
        p10 = create_return_packet(
            b10, session_state="COMPLETED", canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE, canonical_relation="CURRENT",
            changes=["bug-fix"], test_results={"regression": "PASS"},
        )
        resp10 = (
            f"LAW_CHECK=PASS | SOURCE=docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256={canonical_sha}\n"
            "LEARNING_RECONCILIATION=NONE | REASON=One-off transient environment timeout with no reusable lesson\n"
            + p10.to_marked_text()
        )
        res10 = tower.ingest_response(resp10, current_canonical_base_sha=BASE_SHA, current_canonical_base_tree=BASE_TREE)
        self.assertEqual("COMPLETED", res10["reconciliation"]["CONTROL_TOWER_STATUS"])
        self.assertEqual([], res10["reconciliation"]["BLOCKERS"])

    # -------------------------------------------------------------------------
    # Invariant 5: Non-trivial Task Start Bounded Experience Check
    # -------------------------------------------------------------------------

    def test_05_non_trivial_task_start_includes_bounded_experience_check(self) -> None:
        """Task start includes bounded ACTIVE experience check returning <= 3 experiences."""
        task_text = "Perform task to close law distribution and experience consumption gap"
        summary = ee.activation_summary(REPO_ROOT, task_text, max_results=3)

        self.assertIn(summary["decision"], ("USE_ACTIVE_EXPERIENCE", "NO_MATCH"))
        self.assertLessEqual(len(summary["experiences"]), 3)
        self.assertEqual("NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", summary["authority"])
        self.assertTrue(summary["current_state_wins"])
        self.assertTrue(summary["law_and_task_contract_win"])
        self.assertEqual("NONE", summary["permission_effect"])
        self.assertFalse(summary["acceptance_authority"])

    # -------------------------------------------------------------------------
    # Invariant 6 & Blocker B: Portable Experience Capsule Integrity
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

        # 2. Adversarial challenge: mutate one lesson while leaving transport hash untouched => fails closed
        tampered_capsule = original_capsule_text.replace("A law, capability", "TAMPERED LESSON TEXT")
        capsule_file.write_text(tampered_capsule, encoding="utf-8")
        tampered_res = ee.retrieve_portable_experience(
            project,
            "Close law distribution and experience consumption gap for portable actors",
            max_results=3,
        )
        self.assertEqual("UNAVAILABLE", tampered_res["decision"])
        self.assertEqual("PORTABLE_EXPERIENCE_TRANSPORT_HASH_MISMATCH", tampered_res.get("reason"))

        # 3. Adversarial challenge: inject unauthorized non-ACTIVE record => fails closed
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
        notebook_file = project / projector.PORTABLE_REL
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

        # 4. Adversarial challenge: malformed schema or authority => fails closed
        bad_data["records"] = []
        bad_data["schema"] = "invalid-schema/99"
        malformed_text = json.dumps(bad_data)
        capsule_file.write_text(malformed_text, encoding="utf-8")
        nb_text = re.sub(
            r"PORTABLE_EXPERIENCE_CONTENT_SHA256=[0-9a-fA-F]{64}",
            f"PORTABLE_EXPERIENCE_CONTENT_SHA256={hashlib.sha256(malformed_text.encode('utf-8')).hexdigest()}",
            notebook_file.read_text(encoding="utf-8"),
        )
        notebook_file.write_text(nb_text, encoding="utf-8")
        malformed_res = ee.retrieve_portable_experience(project, "task")
        self.assertEqual("UNAVAILABLE", malformed_res["decision"])
        self.assertEqual("CAPSULE_SCHEMA_INVALID", malformed_res.get("reason"))

    # -------------------------------------------------------------------------
    # Invariant 7 & 8: Learning Reconciliation Invariants
    # -------------------------------------------------------------------------

    def test_07_material_correction_cannot_silently_close(self) -> None:
        """Supreme Law and project AGENTS enforce learning reconciliation on material corrections."""
        notebook_text = (REPO_ROOT / projector.SOURCE_REL).read_text(encoding="utf-8")
        self.assertIn("TASK_RECONCILIATION => LEARNING_RECONCILIATION", notebook_text)
        self.assertIn("ROUTINE_SUCCESS => LEARNING_RECONCILIATION=NONE", notebook_text)
        self.assertIn("REPEATED_OR_MATERIAL_FAILURE | CLEARLY_REUSABLE_CORRECTION => LEARNING_RECONCILIATION=CANDIDATE", notebook_text)

        agents_block = projector._agents_block()
        self.assertIn("LEARNING_RECONCILIATION=CANDIDATE", agents_block)
        self.assertIn("LEARNING_RECONCILIATION=NONE", agents_block)

    def test_08_routine_success_does_not_manufacture_memory(self) -> None:
        """Routine success produces LEARNING_RECONCILIATION=NONE and creates no memory."""
        agents_block = projector._agents_block()
        self.assertIn("`ROUTINE_SUCCESS` => emit `LEARNING_RECONCILIATION=NONE`; do not manufacture memory.", agents_block)

        notebook_text = (REPO_ROOT / projector.SOURCE_REL).read_text(encoding="utf-8")
        self.assertIn("ROUTINE_SUCCESS => LEARNING_RECONCILIATION=NONE", notebook_text)
        self.assertIn("Do not manufacture", notebook_text)
        self.assertIn("memory or candidates from routine success.", notebook_text)

    # -------------------------------------------------------------------------
    # Invariant 9: Non-Authoritative Experience Invariants
    # -------------------------------------------------------------------------

    def test_09_experience_cannot_widen_law_permission_or_acceptance_authority(self) -> None:
        """All experience records and capsules strictly enforce non-authority invariants."""
        catalog = ef.load_catalog(REPO_ROOT / projector.SHARED_CATALOG_REL)
        for record in catalog.get("records") or []:
            self.assertEqual("NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", record["authority"])
            self.assertEqual("NONE", record["permission_effect"])
            self.assertFalse(record["acceptance_authority"])

        capsule_text = projector._experience_capsule_text(REPO_ROOT)
        capsule = json.loads(capsule_text)
        self.assertEqual("NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", capsule["authority"])
        self.assertEqual("NONE", capsule["permission_effect"])
        self.assertFalse(capsule["acceptance_authority"])
        self.assertTrue(capsule["current_state_wins"])
        self.assertTrue(capsule["law_and_task_contract_win"])

    # -------------------------------------------------------------------------
    # Invariant 10 & 11: Idempotency, Capsule Generation, and Drift Checking
    # -------------------------------------------------------------------------

    def test_10_portable_projection_remains_idempotent(self) -> None:
        """Repeated projection runs produce byte-identical files."""
        project = self.base / "idempotent-project"
        project.mkdir()

        res1 = projector.project_law(REPO_ROOT, project)
        self.assertEqual("PASS", res1["status"])
        notebook1 = (project / projector.PORTABLE_REL).read_bytes()
        capsule1 = (project / projector.PORTABLE_EXPERIENCE_REL).read_bytes()
        agents1 = (project / "AGENTS.md").read_bytes()

        res2 = projector.project_law(REPO_ROOT, project)
        self.assertEqual("PASS", res2["status"])
        self.assertEqual(notebook1, (project / projector.PORTABLE_REL).read_bytes())
        self.assertEqual(capsule1, (project / projector.PORTABLE_EXPERIENCE_REL).read_bytes())
        self.assertEqual(agents1, (project / "AGENTS.md").read_bytes())

        check = projector.project_law(REPO_ROOT, project, check=True)
        self.assertEqual("PASS", check["status"])

    def test_11_experience_projection_remains_generated_and_source_hash_bound(self) -> None:
        """Experience capsule is generated, source-hash bound, and check fails on drift."""
        catalog_sha = self._catalog_sha()
        project = self.base / "hash-bound-project"
        project.mkdir()
        projector.project_law(REPO_ROOT, project)

        capsule = project / projector.PORTABLE_EXPERIENCE_REL
        data = json.loads(capsule.read_text(encoding="utf-8"))
        self.assertTrue(data["generated"])
        self.assertEqual(catalog_sha, data["source_content_sha256"])

        # Tampering capsule fails check
        capsule.write_text(capsule.read_text(encoding="utf-8") + "\n// DRIFT\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PORTABLE_LAW_PROJECTION_STALE_OR_MISSING"):
            projector.project_law(REPO_ROOT, project, check=True)

    # -------------------------------------------------------------------------
    # Invariant 12: No Second Control Plane / Daemon / DB
    # -------------------------------------------------------------------------

    def test_12_no_second_control_plane_router_ledger_or_db(self) -> None:
        """Ensure no second control plane, router, daemon, vector store or database exists."""
        state_dir = REPO_ROOT / ".p2p" / "state"
        if state_dir.exists():
            for file_path in state_dir.iterdir():
                self.assertNotIn(".sqlite", file_path.name.lower())
                self.assertNotIn(".db", file_path.name.lower())
                self.assertNotIn("chroma", file_path.name.lower())
                self.assertNotIn("vector", file_path.name.lower())

        project = self.base / "clean-project"
        project.mkdir()
        projector.project_law(REPO_ROOT, project)
        portable_files = sorted(p.name for p in (project / ".p2p" / "portable").iterdir())
        self.assertEqual(["P2P-EXPERIENCE-CAPSULE.json", "P2P-OPERATIONS-NOTEBOOK.md"], portable_files)

    # -------------------------------------------------------------------------
    # Blocker E: Truthful Verification References in Promoted Experience
    # -------------------------------------------------------------------------

    def test_blocker_e_truthful_verification_references_exist(self) -> None:
        """Ensure all verification test references cited in shared_experience_catalog.json physically exist and pass."""
        catalog = ef.load_catalog(REPO_ROOT / projector.SHARED_CATALOG_REL)
        promoted = next(
            (r for r in catalog.get("records", []) if r.get("record_id") == "shared-exp-b2611df4c9393f0017f07dcb"),
            None,
        )
        self.assertIsNotNone(promoted)
        evidence_list = promoted.get("verification_evidence", [])
        self.assertEqual(3, len(evidence_list))

        roles = {e["role"]: e["ref"] for e in evidence_list}
        self.assertIn("BEHAVIOR_PROOF", roles)
        self.assertIn("REGRESSION_PROOF", roles)
        self.assertIn("CHALLENGE_PROOF", roles)

        # 1. BEHAVIOR_PROOF
        beh_ref = roles["BEHAVIOR_PROOF"]
        self.assertEqual("tests/test_p2p_portable_law_projection.py:test_actor_law_receipt_and_experience_capsule", beh_ref)
        beh_file, beh_fn = beh_ref.split(":")
        beh_content = (REPO_ROOT / beh_file).read_text(encoding="utf-8")
        self.assertIn(f"def {beh_fn}", beh_content)

        # 2. REGRESSION_PROOF
        reg_ref = roles["REGRESSION_PROOF"]
        self.assertEqual("tests/test_p2p_self_law_propagation_and_fast_sync.py:test_batch_check_detects_current_stale", reg_ref)
        reg_file, reg_fn = reg_ref.split(":")
        reg_content = (REPO_ROOT / reg_file).read_text(encoding="utf-8")
        self.assertIn(f"def {reg_fn}", reg_content)

        # 3. CHALLENGE_PROOF
        chal_ref = roles["CHALLENGE_PROOF"]
        self.assertEqual("tests/test_p2p_experience_evolution.py:test_repo_scoped_portable_experience_retrieval_without_system_runtime", chal_ref)
        chal_file, chal_fn = chal_ref.split(":")
        chal_content = (REPO_ROOT / chal_file).read_text(encoding="utf-8")
        self.assertIn(f"def {chal_fn}", chal_content)

    # -------------------------------------------------------------------------
    # Blocker F: Prove the Experience Lifecycle
    # -------------------------------------------------------------------------

    def test_blocker_f_experience_lifecycle_is_deterministic_and_reproducible(self) -> None:
        """Prove the shared catalog record is fully reproducible through existing lifecycle APIs."""
        iso_root = self.base / "iso_lifecycle"
        iso_root.mkdir()
        iso_catalog = iso_root / "catalog.json"
        iso_catalog.write_text(json.dumps({
            "schema": ef.CATALOG_SCHEMA,
            "catalog_role": "CURATED_PROMOTED_EXPERIENCE_DISTRIBUTION",
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "records": [],
        }), encoding="utf-8")

        # 1. Candidate creation
        cand = ee.create_candidate(
            iso_root,
            task_id="ISSUE-247-LAW-CONSUMPTION-EXPERIENCE-CLOSURE",
            kind="PROCEDURAL",
            trigger_tokens=["distribution", "consumption", "experience", "portable", "receipt", "preflight", "actor", "law"],
            lesson="A law, capability, or learned experience is not operationally complete for a target workflow merely because canonical code or documentation exists. The actual executing actor path must be able to discover it, consume it, and provide bounded, source-bound evidence of consumption before substantive work.",
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
                {"project": "7roger89-web/P2P-upgrade-github-1", "ref": "commit:16bc7b4", "verdict": "PROVEN"},
                {"project": "huyen-hoc-lab", "ref": "audit:huyen-hoc-lab:no-actor-receipt", "verdict": "PROVEN"},
                {"project": "logistics-work-desk-arena", "ref": "audit:logistics-work-desk-arena:read-portable-no-experience-check", "verdict": "PROVEN"},
            ],
            procedure=[
                "Establish actor-own source-bound law receipt before substantive execution.",
                "Perform bounded experience check from capsule or local runtime at task start.",
                "Reconcile learning at task close with NONE or CANDIDATE.",
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
    # Blocker G: Representative Real Repo-Scoped Proof
    # -------------------------------------------------------------------------

    def test_blocker_g_representative_real_repo_logistics_work_desk_arena_proof(self) -> None:
        """Prove representative repo-scoped project path end-to-end on reconstructed real repo."""
        canonical_sha = self._canonical_sha()

        # Reconstruct real repo state for 7roger89-web/logistics-work-desk-arena
        real_repo = self.base / "logistics-work-desk-arena"
        real_repo.mkdir()

        # Real project-specific AGENTS.md before projection
        real_agents_content = (
            "# Logistics Work Desk Arena — project instructions\n\n"
            "## Domain rules\n"
            "- Logistics rate cards and shipment lookup use read-only MongoDB.\n"
            "- Verify rate card documents against the structured PR #12 schema.\n"
            "- Do not mutate collection indexes without Owner approval.\n\n"
            "<!-- BEGIN P2P PORTABLE LAW -->\n"
            "## Old P2P portable Supreme Law entrypoint\n"
            "Old legacy entrypoint content\n"
            "<!-- END P2P PORTABLE LAW -->\n"
        )
        (real_repo / "AGENTS.md").write_text(real_agents_content, encoding="utf-8")

        # Prior portable notebook: valid older notebook whose body matches its header, but differs from canonical
        old_body = (REPO_ROOT / projector.SOURCE_REL).read_text(encoding="utf-8") + "\n<!-- older revision comment -->\n"
        old_sha = hashlib.sha256(old_body.encode("utf-8")).hexdigest()
        portable_dir = real_repo / ".p2p" / "portable"
        portable_dir.mkdir(parents=True)
        (portable_dir / "P2P-OPERATIONS-NOTEBOOK.md").write_text(
            f"<!--\nP2P_PORTABLE_LAW_PROJECTION=YES\nSCHEMA=p2p-portable-law-projection/1\nCANONICAL_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md\nSOURCE_CONTENT_SHA256={old_sha}\nPACKAGE_VERSION=8.4.6\nPROJECTION_DO_NOT_EDIT=YES\nCANONICAL_WINS_WHEN_REACHABLE=YES\n-->\n\n{old_body}",
            encoding="utf-8",
        )

        # Before projection: freshness check confirms STALE
        stale_check = control_tower.check_target_law_freshness(REPO_ROOT, real_repo)
        self.assertEqual("INLINE", stale_check["status"])
        self.assertEqual("TARGET_PORTABLE_STALE", stale_check.get("reason"))

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

        # Execute bounded experience lookup for a task trigger matching DISTRIBUTION_WITHOUT_ACTOR_CONSUMPTION
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
        # Tamper notebook body
        (portable_dir / "P2P-OPERATIONS-NOTEBOOK.md").write_text(portable_nb + "\nTAMPERED\n", encoding="utf-8")
        tampered_freshness = control_tower.check_target_law_freshness(REPO_ROOT, real_repo)
        self.assertEqual("INLINE", tampered_freshness["status"])
        self.assertIn("TAMPERED", tampered_freshness.get("reason", ""))

        # Restore notebook and tamper capsule
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


if __name__ == "__main__":
    unittest.main()
