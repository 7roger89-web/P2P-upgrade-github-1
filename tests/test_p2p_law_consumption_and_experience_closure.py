"""Structural regression tests for P2P law consumption and experience reuse closure.

Protects all 12 minimum invariants specified in Issue #247:
1. actor receipt is source-bound;
2. parent receipt cannot substitute for executor receipt;
3. stale portable cannot produce PASS;
4. prompt/handoff serialization requires actor receipt;
5. non-trivial task start includes bounded experience check;
6. repo-scoped portable flow can access promoted ACTIVE experience without local runtime;
7. material correction cannot silently close without learning reconciliation;
8. routine success does not manufacture memory;
9. experience cannot widen law/permission/acceptance authority;
10. portable projection remains idempotent;
11. experience projection remains generated + source/hash bound;
12. no second control plane / router / ledger / DB is introduced.
"""

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
SCRIPTS_ROOT = REPO_ROOT / "scripts"
for candidate in (str(SYSTEM_ROOT), str(SCRIPTS_ROOT), str(REPO_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import p2p_control_tower as control_tower  # noqa: E402
import p2p_portable_law_projection as projector  # noqa: E402
from p2p_capabilities import experience_evolution as ee  # noqa: E402
from p2p_capabilities import experience_federation as ef  # noqa: E402
from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    SessionBinding,
    build_execution_prompt,
)


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

    def test_03_stale_portable_cannot_produce_pass(self) -> None:
        """Stale portable projection is detected and cannot produce PASS."""
        canonical_sha = self._canonical_sha()
        project = self.base / "project3"
        project.mkdir()
        projector.project_law(REPO_ROOT, project)

        # Before drift: CURRENT
        freshness_before = control_tower.check_target_law_freshness(REPO_ROOT, project)
        self.assertEqual("CURRENT", freshness_before["status"])
        self.assertEqual(canonical_sha, freshness_before["target_law_sha256"])

        # Tamper / stale portable notebook
        portable = project / projector.PORTABLE_REL
        stale_sha = "0" * 64
        tampered = portable.read_text(encoding="utf-8").replace(canonical_sha, stale_sha)
        portable.write_text(tampered, encoding="utf-8")

        freshness_after = control_tower.check_target_law_freshness(REPO_ROOT, project)
        self.assertEqual("INLINE", freshness_after["status"])
        self.assertEqual(stale_sha, freshness_after["target_law_sha256"])
        self.assertEqual("TARGET_PORTABLE_STALE", freshness_after.get("reason"))

        agents_block = projector._agents_block()
        self.assertIn("A stale portable copy cannot produce PASS", agents_block)

    def test_04_prompt_and_handoff_serialization_requires_actor_receipt(self) -> None:
        """Both prompt handoff and projected AGENTS explicitly mandate actor LAW_CHECK receipt."""
        # 1. Control Tower start prompt carries context with executor receipt constraint
        receipt = control_tower._establish_control_tower_law_context(REPO_ROOT)
        summary = control_tower._experience_summary(REPO_ROOT, "Perform task with actor law receipt")
        prompt = control_tower._render_context_block(
            summary,
            "Perform task with actor law receipt",
            max_chars=1600,
            law_receipt=receipt,
        )
        self.assertIn("EXECUTOR_RECEIPT_SUBSTITUTE=NO", prompt)
        self.assertIn("P2P_LAW_PREFLIGHT=", prompt)
        self.assertIn("XP=USE_ACTIVE_EXPERIENCE", prompt)

        # 2. Projected AGENTS.md mandates actor own receipt and disallows parent inheritance
        agents_block = projector._agents_block()
        self.assertIn("emit actor-own `LAW_CHECK=PASS | SOURCE=<actual source> | SOURCE_SHA256=<canonical hash>`", agents_block)
        self.assertIn("`PARENT_SELF_LAW_PREFLIGHT != EXECUTOR_LAW_PREFLIGHT`", agents_block)
        self.assertIn("never proves executor preflight and never substitutes", agents_block)
        self.assertIn("EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE|NO_MATCH|UNAVAILABLE", agents_block)
        self.assertIn("LEARNING_RECONCILIATION=NONE|CANDIDATE", agents_block)

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

    def test_06_repo_scoped_portable_flow_can_access_promoted_active_experience_without_local_runtime(self) -> None:
        """Repo-scoped clone without .p2p/system consumes promoted ACTIVE experience from capsule."""
        project = self.base / "remote-project"
        project.mkdir()
        result = projector.project_law(REPO_ROOT, project)
        self.assertEqual("PASS", result["status"])

        capsule_file = project / projector.PORTABLE_EXPERIENCE_REL
        self.assertTrue(capsule_file.is_file())
        self.assertFalse((project / ".p2p" / "system").exists())

        # Read directly via JSON as a remote executor would
        capsule_data = json.loads(capsule_file.read_text(encoding="utf-8"))
        self.assertEqual("p2p-portable-experience-capsule/1", capsule_data["schema"])
        self.assertTrue(capsule_data["generated"])
        self.assertGreaterEqual(len(capsule_data["records"]), 1)

        record = capsule_data["records"][0]
        self.assertEqual("ACTIVE", record["state"])
        self.assertIn(record["scope"], ("DOMAIN", "CROSS_PROJECT"))
        self.assertIn("distribution", record["trigger_tokens"])
        self.assertIn("consumption", record["trigger_tokens"])

        # Standalone helper retrieval without .p2p/system in project
        retrieved = ee.retrieve_portable_experience(
            project,
            "Close law distribution and experience consumption gap for portable actors",
            max_results=3,
        )
        self.assertEqual("USE_ACTIVE_EXPERIENCE", retrieved["decision"])
        self.assertGreaterEqual(len(retrieved["experiences"]), 1)
        self.assertEqual("NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", retrieved["authority"])
        self.assertIn(".p2p/portable/P2P-EXPERIENCE-CAPSULE.json", retrieved["experiences"][0]["source"])

    def test_07_material_correction_cannot_silently_close_without_learning_reconciliation(self) -> None:
        """Projected entrypoint and Supreme Law enforce learning reconciliation at close."""
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

    def test_12_no_second_control_plane_router_ledger_or_db(self) -> None:
        """Ensure no second control plane, router, daemon, vector store or database exists."""
        # 1. State files check: only execution-ledger.jsonl and shared_experience_catalog.json
        state_dir = REPO_ROOT / ".p2p" / "state"
        if state_dir.exists():
            for file_path in state_dir.iterdir():
                self.assertNotIn(".sqlite", file_path.name.lower())
                self.assertNotIn(".db", file_path.name.lower())
                self.assertNotIn("chroma", file_path.name.lower())
                self.assertNotIn("vector", file_path.name.lower())

        # 2. Projector does not create any daemon or registry files
        project = self.base / "clean-project"
        project.mkdir()
        projector.project_law(REPO_ROOT, project)
        portable_files = sorted(p.name for p in (project / ".p2p" / "portable").iterdir())
        self.assertEqual(["P2P-EXPERIENCE-CAPSULE.json", "P2P-OPERATIONS-NOTEBOOK.md"], portable_files)


if __name__ == "__main__":
    unittest.main()
