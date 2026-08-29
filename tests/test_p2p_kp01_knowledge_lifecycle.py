from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import knowledge_lifecycle as knowledge  # noqa: E402
from p2p_capabilities.isolation import IsolationViolation  # noqa: E402


ORG_SCOPE = {"ORG": "ORG1"}
PROJECT_SCOPE = {"ORG": "ORG1", "PROJECT": "PROJ1"}
WORKSTREAM_SCOPE = {"ORG": "ORG1", "PROJECT": "PROJ1", "WORKSTREAM": "WS1"}


def make_proposal(
    record_id: str,
    *,
    statement: str = "Use the bounded current canonical primitive.",
    scope: dict[str, str] = WORKSTREAM_SCOPE,
    lifecycle: str = "CANDIDATE",
    authority: dict[str, object] | None = None,
    knowledge_type: str = "ARCHITECTURE_DECISION",
    valid_from: str = "2026-08-01T00:00:00Z",
) -> dict[str, object]:
    return knowledge.make_record(
        record_id=record_id,
        knowledge_type=knowledge_type,
        subject="routing-boundary",
        statement=statement,
        scope=scope,
        lifecycle=lifecycle,
        authority=authority or {"origin": "MODEL_INFERENCE", "source": "focused-test", "evidence_bound": False},
        evidence_refs=[f"evidence:{record_id}"],
        provenance_refs=[f"provenance:{record_id}"],
        created_at=valid_from,
        valid_from=valid_from,
    )


def make_verified(record_id: str, *, statement: str = "Use the bounded current canonical primitive.", scope: dict[str, str] = WORKSTREAM_SCOPE, knowledge_type: str = "ARCHITECTURE_DECISION", origin: str = "RUNTIME_EVIDENCE") -> dict[str, object]:
    return make_proposal(
        record_id,
        statement=statement,
        scope=scope,
        lifecycle="VERIFIED",
        knowledge_type=knowledge_type,
        authority={"origin": origin, "source": f"verified-source:{record_id}", "evidence_bound": True},
    )


def promote(root: Path, record_id: str, *, approval_origin: str = "OWNER", knowledge_type: str = "ARCHITECTURE_DECISION", statement: str = "Use the bounded current canonical primitive.", scope: dict[str, str] = WORKSTREAM_SCOPE) -> dict[str, object]:
    verified = make_verified(record_id, statement=statement, scope=scope, knowledge_type=knowledge_type)
    knowledge.write_record(root, verified)
    kwargs: dict[str, object] = {
        "candidate_id": record_id,
        "evidence_ref": f"promotion-evidence:{record_id}",
        "approved_by": approval_origin,
    }
    if approval_origin == "GOVERNANCE":
        kwargs["governance_decision_ref"] = f"governance-decision:{record_id}"
    else:
        kwargs["owner_decision_ref"] = f"owner-decision:{record_id}"
    return knowledge.promote_record(root, **kwargs)


class KP01ContractDriftRepairTests(unittest.TestCase):
    def test_a_official_source_cannot_authorize_canonical_promotion(self) -> None:
        with self.assertRaises(knowledge.KnowledgeError):
            make_proposal("R-OFFICIAL", lifecycle="CANONICAL", authority={"origin": "OFFICIAL_SOURCE", "source": "official", "evidence_bound": True})
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            verified = make_verified("R-OFFICIAL-PROMOTION", origin="OFFICIAL_SOURCE")
            knowledge.write_record(root, verified)
            with self.assertRaises(knowledge.KnowledgeError):
                knowledge.promote_record(root, candidate_id="R-OFFICIAL-PROMOTION", evidence_ref="evidence", approved_by="OFFICIAL_SOURCE", owner_decision_ref="owner")

    def test_b_runtime_evidence_cannot_authorize_canonical_promotion(self) -> None:
        with self.assertRaises(knowledge.KnowledgeError):
            make_proposal("R-RUNTIME", lifecycle="CANONICAL", authority={"origin": "RUNTIME_EVIDENCE", "source": "runtime", "evidence_bound": True})
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            verified = make_verified("R-RUNTIME-PROMOTION", origin="RUNTIME_EVIDENCE")
            knowledge.write_record(root, verified)
            with self.assertRaises(knowledge.KnowledgeError):
                knowledge.promote_record(root, candidate_id="R-RUNTIME-PROMOTION", evidence_ref="evidence", approved_by="RUNTIME_EVIDENCE", owner_decision_ref="owner")

    def test_c_generic_direct_canonical_construction_is_rejected(self) -> None:
        with self.assertRaisesRegex(knowledge.KnowledgeError, "DIRECT_CANONICAL_CONSTRUCTION_REJECTED"):
            make_proposal("R-DIRECT", lifecycle="CANONICAL", authority={"origin": "OWNER", "source": "owner", "evidence_bound": True})

    def test_d_candidate_direct_promotion_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            knowledge.write_record(root, make_proposal("R-CANDIDATE"))
            with self.assertRaisesRegex(knowledge.KnowledgeError, "VERIFIED_ONLY_PROMOTION_REQUIRED"):
                knowledge.promote_record(root, candidate_id="R-CANDIDATE", owner_decision_ref="owner", evidence_ref="evidence")

    def test_e_verified_owner_approval_succeeds_and_preserves_type(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result = promote(root, "R-OWNER", knowledge_type="OWNER_DECISION")
            self.assertEqual(result["status"], "PASS")
            canonical = next(item for item in knowledge.read_records(root)["records"] if item["lifecycle"] == "CANONICAL")
            self.assertEqual(canonical["knowledge_type"], "OWNER_DECISION")
            self.assertEqual(canonical["authority"]["origin"], "OWNER")

    def test_f_verified_governance_approval_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result = promote(root, "R-GOVERNANCE", approval_origin="GOVERNANCE")
            self.assertEqual(result["status"], "PASS")
            canonical = next(item for item in knowledge.read_records(root)["records"] if item["lifecycle"] == "CANONICAL")
            self.assertEqual(canonical["authority"]["origin"], "GOVERNANCE")

    def test_g_org_scope_works_without_project_or_workstream(self) -> None:
        record = make_proposal("R-ORG", scope=ORG_SCOPE)
        self.assertEqual(record["scope_level"], "ORG")
        self.assertEqual(record["scope"], ORG_SCOPE)

    def test_h_project_scope_works_without_workstream(self) -> None:
        record = make_proposal("R-PROJECT", scope=PROJECT_SCOPE)
        self.assertEqual(record["scope_level"], "PROJECT")
        self.assertEqual(record["scope"], PROJECT_SCOPE)

    def test_i_workstream_scope_remains_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            ws1 = make_proposal("R-WS1", scope={"ORG": "ORG1", "PROJECT": "PROJ1", "WORKSTREAM": "WS1"})
            ws2 = make_proposal("R-WS2", scope={"ORG": "ORG1", "PROJECT": "PROJ1", "WORKSTREAM": "WS2"}, statement="isolated workstream rule")
            knowledge.write_record(root, ws1)
            knowledge.write_record(root, ws2)
            result = knowledge.query_as_of(root, subject="routing-boundary", as_of="2026-08-29T00:00:00Z", scope=ws1["scope"])
            self.assertEqual([item["record_id"] for item in result["results"]], ["R-WS1"])

    def test_j_promoted_architecture_decision_preserves_knowledge_type(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            promote(root, "R-ARCH", knowledge_type="ARCHITECTURE_DECISION")
            canonical = next(item for item in knowledge.read_records(root)["records"] if item["lifecycle"] == "CANONICAL")
            self.assertEqual(canonical["knowledge_type"], "ARCHITECTURE_DECISION")
            self.assertNotEqual(canonical["knowledge_type"], "PROMOTION_RESULT")

    def test_k_supersession_transitions_old_canonical_and_retains_it(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            promote(root, "R-OLD", statement="old canonical rule")
            promote(root, "R-NEW", statement="new canonical rule")
            result = knowledge.supersede_records(root, old_record_id="R-OLD-canonical", new_record_id="R-NEW-canonical", supersession_at="2026-09-01T00:00:00Z")
            self.assertEqual(result["status"], "PASS")
            records = {item["record_id"]: item for item in knowledge.read_records(root)["records"]}
            self.assertEqual(records["R-OLD-canonical"]["lifecycle"], "SUPERSEDED")
            self.assertEqual(records["R-OLD-canonical"]["valid_until"], "2026-09-01T00:00:00Z")
            self.assertEqual(records["R-OLD-canonical"]["superseded_by"], ["R-NEW-canonical"])
            self.assertEqual(records["R-NEW-canonical"]["supersedes"], ["R-OLD-canonical"])
            self.assertEqual(len(records), 4)

    def test_l_exact_supersession_timestamp_is_half_open(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            promote(root, "R-OLD", statement="old canonical rule")
            promote(root, "R-NEW", statement="new canonical rule")
            knowledge.supersede_records(root, old_record_id="R-OLD-canonical", new_record_id="R-NEW-canonical", supersession_at="2026-09-01T00:00:00Z")
            before = knowledge.query_as_of(root, subject="routing-boundary", as_of="2026-08-31T23:59:59Z", scope=WORKSTREAM_SCOPE)
            exact = knowledge.query_as_of(root, subject="routing-boundary", as_of="2026-09-01T00:00:00Z", scope=WORKSTREAM_SCOPE)
            self.assertEqual(before["results"][0]["record_id"], "R-OLD-canonical")
            self.assertEqual(exact["results"][0]["record_id"], "R-NEW-canonical")

    def test_m_control_tower_reads_canonical_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            knowledge.write_record(root, make_proposal("R-PROPOSED"))
            self.assertEqual(knowledge.reconstruct_control_tower(root, scope=WORKSTREAM_SCOPE)["status"], "NO_CANONICAL_KNOWLEDGE")
            promote(root, "R-CANONICAL")
            tower = knowledge.reconstruct_control_tower(root, scope=WORKSTREAM_SCOPE)
            self.assertEqual(tower["status"], "PASS")
            self.assertTrue(all(item["lifecycle"] == "CANONICAL" for item in tower["records"]))
            self.assertNotIn("R-PROPOSED", {item["record_id"] for item in tower["records"]})

    def test_n_execution_authorization_stays_not_granted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result = promote(root, "R-AUTH")
            self.assertEqual(result["execution_authorization"], "NOT_GRANTED")
            self.assertEqual(knowledge.reconstruct_control_tower(root, scope=WORKSTREAM_SCOPE)["execution_authorization"], "NOT_GRANTED")

    def test_o_candidate_or_newer_observation_never_overrides_canonical_truth(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            promote(root, "R-CANON", statement="canonical truth")
            newer = make_proposal("R-NEWER", statement="newer but noncanonical", lifecycle="OBSERVATION", valid_from="2026-12-01T00:00:00Z")
            knowledge.write_record(root, newer)
            result = knowledge.query_as_of(root, subject="routing-boundary", as_of="2026-12-15T00:00:00Z", scope=WORKSTREAM_SCOPE)
            self.assertEqual(result["results"][0]["record_id"], "R-CANON-canonical")
            self.assertTrue(result["verified_truth"])
            self.assertEqual(result["results"][0]["statement"], "canonical truth")

    def test_preserved_immutable_collision_isolation_and_secret_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            record = make_proposal("R-SAFE")
            knowledge.write_record(root, record)
            self.assertEqual(knowledge.write_record(root, record)["status"], "ALREADY_PRESENT")
            altered = dict(record)
            altered["statement"] = "different statement"
            with self.assertRaises(knowledge.KnowledgeError):
                knowledge.write_record(root, altered)
            target = knowledge._record_path(root, record)
            with self.assertRaises(IsolationViolation):
                knowledge.write_record(root, make_proposal("R-ISOLATED"), protected_roots=[target.parent])
            with self.assertRaises(knowledge.KnowledgeError):
                make_proposal("R-SECRET", statement="password=topsecret")


if __name__ == "__main__":
    unittest.main()
