from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / ".p2p" / "system" / "p2p_capabilities" / "experience_evolution.py"
spec = importlib.util.spec_from_file_location("experience_evolution", MODULE)
ee = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ee)


def proving(ref: str = "tests:pass", role: str = "") -> dict[str, str]:
    return {"kind": "DETERMINISTIC_TEST", "ref": ref, "role": role, "verdict": "PROVEN"}


class ExperienceEvolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="p2p-exp-evolution-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def candidate(self, **overrides):
        kwargs = dict(
            task_id="TASK-1", kind="PROCEDURAL",
            trigger_tokens=("atlas", "mongodb", "pilot"),
            lesson="Verify the source database read-only before creating a pilot copy.",
            evidence=(proving("probe:source-readonly"),), outcome="CORRECTED",
            failure_class="SOURCE_AUTHORITY_UNCERTAIN",
            correction="Read source metadata first; never mutate the authority database.",
            source_revision="abc123",
        )
        kwargs.update(overrides)
        return ee.create_candidate(self.root, **kwargs)

    def verify_and_activate(self, eid: str):
        ee.verify_candidate(
            self.root, eid, task_id="VERIFY-1",
            verification_evidence=(
                proving("behavior:test", "BEHAVIOR_PROOF"),
                proving("regression:test", "REGRESSION_PROOF"),
                proving("challenge:test", "CHALLENGE_PROOF"),
            ),
        )
        return ee.activate_verified(self.root, eid, task_id="VERIFY-1")

    def test_self_report_cannot_create_candidate(self) -> None:
        with self.assertRaisesRegex(ee.ExperienceEvolutionError, "INDEPENDENT_EVIDENCE_REQUIRED"):
            self.candidate(evidence=({"kind": "MODEL_SELF_REPORT", "ref": "agent says fixed", "verdict": "PROVEN"},))

    def test_candidate_is_not_reused_until_verified_and_active(self) -> None:
        created = self.candidate()
        self.assertEqual(created["state"], "CANDIDATE")
        self.assertEqual(ee.retrieve_active_experiences(self.root, "mongodb atlas pilot"), ())
        with self.assertRaisesRegex(ee.ExperienceEvolutionError, "VERIFICATION_ROLE_MISSING"):
            ee.verify_candidate(self.root, created["experience_id"], task_id="VERIFY-1",
                                verification_evidence=(proving("behavior:test", "BEHAVIOR_PROOF"),))
        self.verify_and_activate(created["experience_id"])
        matches = ee.retrieve_active_experiences(self.root, {"title": "Prepare MongoDB Atlas pilot", "scope": ("pilot",)})
        self.assertEqual(len(matches), 1)
        self.assertFalse(matches[0]["acceptance_authority"])
        self.assertEqual(matches[0]["permission_effect"], "NONE")
        self.assertTrue(matches[0]["must_revalidate_against_current_state"])

    def test_irrelevant_active_experience_is_not_preloaded(self) -> None:
        created = self.candidate(); self.verify_and_activate(created["experience_id"])
        self.assertEqual(ee.retrieve_active_experiences(self.root, {"title": "Fix responsive typography", "tags": ("ui",)}), ())

    def test_quarantine_preserves_history_but_removes_reuse(self) -> None:
        created = self.candidate(); eid = created["experience_id"]; self.verify_and_activate(eid)
        ee.quarantine_experience(self.root, eid,
                                 reason="Current provider semantics contradict the old procedure.",
                                 evidence=(proving("provider-doc:new-contract"),), task_id="TASK-2")
        state = ee.derive_experiences(self.root)[eid]
        self.assertEqual(state["state"], "QUARANTINED")
        self.assertIn(ee.EVENT_ACTIVATED, state["history"])
        self.assertIn(ee.EVENT_QUARANTINED, state["history"])
        self.assertEqual(ee.retrieve_active_experiences(self.root, "mongodb atlas pilot"), ())

    def test_supersede_requires_active_verified_successor(self) -> None:
        old = self.candidate(); self.verify_and_activate(old["experience_id"])
        new = self.candidate(task_id="TASK-NEW",
                             lesson="Verify source read-only, snapshot exact revision, then create the pilot copy.",
                             evidence=(proving("probe:new-sequence"),), correction="Bind source revision before copy.")
        with self.assertRaisesRegex(ee.ExperienceEvolutionError, "SUPERSEDE_REQUIRES_ACTIVE_PAIR"):
            ee.supersede_experience(self.root, old["experience_id"], new["experience_id"], evidence=(proving("compare:new-better"),))
        self.verify_and_activate(new["experience_id"])
        ee.supersede_experience(self.root, old["experience_id"], new["experience_id"], evidence=(proving("compare:new-better"),), task_id="TASK-NEW")
        active = ee.retrieve_active_experiences(self.root, "mongodb atlas pilot")
        self.assertEqual([x["experience_id"] for x in active], [new["experience_id"]])
        self.assertEqual(ee.derive_experiences(self.root)[old["experience_id"]]["state"], "SUPERSEDED")

    def test_harmed_use_requests_review_but_does_not_auto_delete(self) -> None:
        created = self.candidate(); eid = created["experience_id"]; self.verify_and_activate(eid)
        result = ee.record_use_result(self.root, eid, task_id="TASK-3", outcome="HARMED", evidence_ref="tests:future-regression")
        self.assertTrue(result["review_recommended"])
        self.assertFalse(result["auto_quarantined"])
        self.assertEqual(ee.derive_experiences(self.root)[eid]["state"], "ACTIVE")

    def test_existing_execution_ledger_is_only_persistent_store(self) -> None:
        created = self.candidate()
        ledger = self.root / ".p2p" / "state" / "execution-ledger.jsonl"
        self.assertTrue(ledger.is_file())
        self.assertEqual([p for p in self.root.rglob("*") if p.is_file() and p != ledger], [])
        first = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(first["schema_version"], "p2p-execution-event/1")
        self.assertEqual(first["event_type"], ee.EVENT_CANDIDATE)
        self.assertEqual(first["experience"]["experience_id"], created["experience_id"])

    def test_cli_lifecycle_is_usable_by_future_agents(self) -> None:
        evidence = json.dumps([proving("probe:cli-candidate")])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = ee.main(["--root", str(self.root), "candidate", "--task-id", "CLI-1", "--kind", "PROCEDURAL",
                          "--trigger", "mongodb", "--trigger", "atlas",
                          "--lesson", "Verify the source database read-only before creating a pilot copy.",
                          "--evidence-json", evidence, "--outcome", "CORRECTED"])
        self.assertEqual(rc, 0); eid = json.loads(out.getvalue())["experience_id"]
        verification = json.dumps([
            proving("behavior:cli", "BEHAVIOR_PROOF"), proving("regression:cli", "REGRESSION_PROOF"),
            proving("challenge:cli", "CHALLENGE_PROOF"),
        ])
        for argv in (["--root", str(self.root), "verify", "--experience-id", eid, "--task-id", "CLI-VERIFY", "--evidence-json", verification],
                     ["--root", str(self.root), "activate", "--experience-id", eid, "--task-id", "CLI-VERIFY"]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ee.main(argv), 0)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ee.main(["--root", str(self.root), "retrieve", "--task-text", "mongodb atlas pilot"]), 0)
        retrieved = json.loads(out.getvalue())
        self.assertEqual(retrieved["decision"], "USE_ACTIVE_EXPERIENCE")
        self.assertEqual(retrieved["experiences"][0]["experience_id"], eid)

    def test_activation_summary_is_read_only_and_active_only(self) -> None:
        created = self.candidate(); ledger = self.root / ".p2p" / "state" / "execution-ledger.jsonl"
        before = ledger.read_bytes(); summary = ee.activation_summary(self.root, "atlas mongodb pilot"); after = ledger.read_bytes()
        self.assertEqual(summary["decision"], "NO_MATCH"); self.assertFalse(summary["mutated"]); self.assertEqual(before, after)
        self.verify_and_activate(created["experience_id"])
        summary = ee.activation_summary(self.root, "atlas mongodb pilot")
        self.assertEqual(summary["decision"], "USE_ACTIVE_EXPERIENCE")
        self.assertTrue(summary["current_state_wins"]); self.assertTrue(summary["law_and_task_contract_win"])
        self.assertFalse(summary["acceptance_authority"])

    def test_repo_scoped_portable_experience_retrieval_without_system_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            remote = Path(temp) / "remote_project"
            remote.mkdir()
            portable_dir = remote / ".p2p" / "portable"
            portable_dir.mkdir(parents=True)
            self.assertFalse((remote / ".p2p" / "system").exists())

            capsule = {
                "schema": "p2p-portable-experience-capsule/1",
                "generated": True,
                "canonical_source": "p2p_capabilities.shared_experience_catalog",
                "source_content_sha256": "a" * 64,
                "package_version": "1.0.0",
                "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
                "current_state_wins": True,
                "law_and_task_contract_win": True,
                "permission_effect": "NONE",
                "acceptance_authority": False,
                "records": [
                    {
                        "source_experience_id": "exp-test-01",
                        "record_id": "shared-exp-test-01",
                        "kind": "PROCEDURAL",
                        "state": "ACTIVE",
                        "scope": "CROSS_PROJECT",
                        "trigger_tokens": ["portable", "distribution", "consumption"],
                        "lesson": "A portable lesson",
                        "correction": "A portable correction",
                        "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
                        "permission_effect": "NONE",
                        "acceptance_authority": False,
                    }
                ],
            }
            capsule_text = json.dumps(capsule, indent=2, sort_keys=True)
            capsule_file = portable_dir / "P2P-EXPERIENCE-CAPSULE.json"
            capsule_file.write_text(capsule_text, encoding="utf-8")
            capsule_sha = hashlib.sha256(capsule_text.encode("utf-8")).hexdigest()

            notebook_file = portable_dir / "P2P-OPERATIONS-NOTEBOOK.md"
            notebook_file.write_text(
                f"<!--\nPORTABLE_EXPERIENCE_CONTENT_SHA256={capsule_sha}\n-->\n\nLAW\n",
                encoding="utf-8",
            )

            # 1. Valid retrieval
            res = ee.retrieve_portable_experience(remote, "task with distribution and consumption")
            self.assertEqual("USE_ACTIVE_EXPERIENCE", res["decision"])
            self.assertEqual(1, len(res["experiences"]))
            self.assertEqual("shared-exp-test-01", res["experiences"][0]["record_id"])

            # 2. Adversarial challenge: mutate record/lesson while leaving transport sha untouched
            tampered_capsule = capsule_text.replace("A portable lesson", "TAMPERED LESSON")
            capsule_file.write_text(tampered_capsule, encoding="utf-8")
            tampered_res = ee.retrieve_portable_experience(remote, "task with distribution and consumption")
            self.assertEqual("UNAVAILABLE", tampered_res["decision"])
            self.assertEqual("PORTABLE_EXPERIENCE_TRANSPORT_HASH_MISMATCH", tampered_res.get("reason"))

            # 3. Adversarial challenge: inject unauthorized/non-ACTIVE record
            capsule_file.write_text(capsule_text, encoding="utf-8")
            bad_capsule = json.loads(capsule_text)
            bad_capsule["records"][0]["state"] = "PENDING"
            bad_text = json.dumps(bad_capsule)
            capsule_file.write_text(bad_text, encoding="utf-8")
            notebook_file.write_text(
                f"<!--\nPORTABLE_EXPERIENCE_CONTENT_SHA256={hashlib.sha256(bad_text.encode('utf-8')).hexdigest()}\n-->\n\nLAW\n",
                encoding="utf-8",
            )
            bad_res = ee.retrieve_portable_experience(remote, "task with distribution and consumption")
            self.assertEqual("UNAVAILABLE", bad_res["decision"])
            self.assertEqual("CAPSULE_RECORD_NOT_ACTIVE", bad_res.get("reason"))


if __name__ == "__main__":
    unittest.main()
