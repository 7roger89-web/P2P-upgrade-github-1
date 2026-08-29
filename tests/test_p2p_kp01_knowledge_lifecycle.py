from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import knowledge_lifecycle as knowledge  # noqa: E402
from p2p_capabilities.isolation import IsolationViolation  # noqa: E402


SCOPE = {"ORG": "ORG1", "PROJECT": "PROJ1", "WORKSTREAM": "WS1"}


def candidate(record_id: str, *, subject: str = "routing-boundary", statement: str = "Use the bounded current canonical primitive.", **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "record_id": record_id,
        "knowledge_type": "ARCHITECTURE_DECISION",
        "subject": subject,
        "statement": statement,
        "scope": SCOPE,
        "lifecycle": "CANDIDATE",
        "authority": {"origin": "MODEL_INFERENCE", "source": "focused-test", "evidence_bound": False},
        "evidence_refs": [f"evidence:{record_id}"],
        "provenance_refs": [f"provenance:{record_id}"],
        "created_at": "2026-08-29T00:00:00Z",
        "valid_from": "2026-08-29T00:00:00Z",
    }
    values.update(overrides)
    return knowledge.make_record(**values)


class KP01KnowledgeLifecycleTests(unittest.TestCase):
    def test_kp01_lifecycle_and_knowledge_types(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for kind in knowledge.KNOWLEDGE_TYPES:
                record = candidate(f"R-{kind}", knowledge_type=kind)
                self.assertEqual(knowledge.write_record(root, record)["status"], "APPENDED")
            loaded = knowledge.read_records(root)
            self.assertEqual(loaded["status"], "PASS")
            self.assertEqual({item["knowledge_type"] for item in loaded["records"]}, set(knowledge.KNOWLEDGE_TYPES))
            self.assertEqual({item["lifecycle"] for item in loaded["records"]}, {"CANDIDATE"})

    def test_current_query_is_not_verified_truth_and_as_of_respects_validity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            old = candidate("R-OLD", statement="old bounded rule", valid_from="2026-08-01T00:00:00Z", created_at="2026-08-01T00:00:00Z")
            new = candidate("R-NEW", statement="new bounded rule", valid_from="2026-08-20T00:00:00Z", created_at="2026-08-20T00:00:00Z")
            knowledge.write_record(root, old)
            knowledge.write_record(root, new)
            as_of = knowledge.query_as_of(root, subject="routing-boundary", as_of="2026-08-10T00:00:00Z", scope=SCOPE)
            current = knowledge.query_current(root, subject="routing-boundary", scope=SCOPE)
            self.assertEqual(as_of["results"][0]["record_id"], "R-OLD")
            self.assertEqual(current["results"][0]["record_id"], "R-NEW")
            self.assertFalse(current["verified_truth"])
            self.assertTrue(current["retrieved_knowledge"])

    def test_supersession_keeps_old_record_and_changes_current_projection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            old = candidate("R-SUPERSEDED", statement="old rule")
            new = candidate("R-SUCCESSOR", statement="successor rule", supersedes=["R-SUPERSEDED"], valid_from="2026-08-29T00:00:00Z", created_at="2026-08-29T00:00:00Z")
            knowledge.write_record(root, old)
            knowledge.write_record(root, new)
            current = knowledge.query_current(root, subject="routing-boundary", scope=SCOPE)
            self.assertEqual(current["results"][0]["record_id"], "R-SUCCESSOR")
            self.assertEqual(len(knowledge.read_records(root)["records"]), 2)
            self.assertEqual(knowledge.provenance_lookup(root, "R-SUPERSEDED")["status"], "PASS")

    def test_authority_conflict_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = candidate("R-CANON-1", statement="canonical A", lifecycle="CANONICAL", authority={"origin": "OWNER", "source": "owner-decision-A", "evidence_bound": True})
            second = candidate("R-CANON-2", statement="canonical B", lifecycle="CANONICAL", authority={"origin": "OFFICIAL_SOURCE", "source": "official-source-B", "evidence_bound": True})
            knowledge.write_record(root, first)
            knowledge.write_record(root, second)
            result = knowledge.query_current(root, subject="routing-boundary", scope=SCOPE)
            self.assertEqual(result["status"], "AUTHORITY_CONFLICT")
            self.assertTrue(result["authority_conflict"])
            self.assertFalse(result["verified_truth"])

    def test_scope_isolation_and_secret_private_reasoning_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            protected = root / "protected"
            record = candidate("R-ISOLATION")
            protected_record = knowledge._record_path(root, record)  # bounded contract target for the test
            with self.assertRaises(IsolationViolation):
                knowledge.write_record(root, record, protected_roots=[protected_record.parent])
            with self.assertRaises(knowledge.KnowledgeError):
                knowledge.make_record(
                    record_id="R-SECRET", knowledge_type="OWNER_DECISION", subject="secret", statement="password=topsecret",
                    scope=SCOPE, lifecycle="OBSERVATION", authority={"origin": "OWNER", "source": "owner"}, evidence_refs=[],
                )

    def test_control_tower_reads_canonical_only_and_never_grants_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            proposed = candidate("R-PROPOSED")
            knowledge.write_record(root, proposed)
            before = knowledge.reconstruct_control_tower(root, scope=SCOPE)
            self.assertEqual(before["status"], "NO_CANONICAL_KNOWLEDGE")
            canonical = knowledge.make_record(
                record_id="R-CANONICAL", knowledge_type="PROMOTION_RESULT", subject="routing-boundary",
                statement="Use the bounded current canonical primitive.", scope=SCOPE, lifecycle="CANONICAL",
                authority={"origin": "OWNER", "source": "owner-decision", "evidence_bound": True}, evidence_refs=["owner-evidence"],
            )
            knowledge.write_record(root, canonical)
            after = knowledge.reconstruct_control_tower(root, scope=SCOPE)
            self.assertEqual(after["status"], "PASS")
            self.assertEqual(after["source"], "CANONICAL_KNOWLEDGE_ONLY")
            self.assertEqual(after["execution_authorization"], "NOT_GRANTED")
            self.assertEqual(after["records"][0]["record_id"], "R-CANONICAL")

    def test_explicit_promotion_requires_authority_and_keeps_candidate_separate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            proposed = candidate("R-PROMOTE")
            knowledge.write_record(root, proposed)
            result = knowledge.promote_record(root, candidate_id="R-PROMOTE", owner_decision_ref="owner-decision", evidence_ref="promotion-evidence")
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["execution_authorization"], "NOT_GRANTED")
            records = knowledge.read_records(root)["records"]
            self.assertEqual({item["record_id"] for item in records}, {"R-PROMOTE", "R-PROMOTE-canonical"})
            self.assertEqual(next(item for item in records if item["record_id"] == "R-PROMOTE")["lifecycle"], "CANDIDATE")
            self.assertEqual(knowledge.reconstruct_control_tower(root, scope=SCOPE)["records"][0]["record_id"], "R-PROMOTE-canonical")


if __name__ == "__main__":
    unittest.main()
