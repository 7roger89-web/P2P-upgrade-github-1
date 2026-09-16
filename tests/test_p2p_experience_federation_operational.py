from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities import experience_evolution as ee  # noqa: E402
from p2p_capabilities import experience_federation as ef  # noqa: E402
from p2p_capabilities import experience_promotion as ep  # noqa: E402


def proof(kind: str, ref: str, role: str = "") -> dict[str, str]:
    return {"kind": kind, "ref": ref, "role": role, "verdict": "PROVEN"}


class ExperienceFederationOperationalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="p2p-exp-fed-op-")
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.target = self.base / "target"
        self.catalog = self.base / "catalog.json"
        self.source.mkdir()
        self.target.mkdir()
        self.catalog.write_text(json.dumps({
            "schema": ef.CATALOG_SCHEMA,
            "catalog_role": "CURATED_PROMOTED_EXPERIENCE_DISTRIBUTION",
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "records": [],
        }), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def active_source(self) -> str:
        created = ee.create_candidate(
            self.source,
            task_id="SRC-1",
            kind="PROCEDURAL",
            trigger_tokens=("mongo", "snapshot", "bson"),
            lesson="Preserve typed BSON fidelity before accepting a Mongo snapshot.",
            correction="Use a typed canonical round trip and prove source immutability.",
            evidence=(proof("REAL_PATH", "evidence:source"),),
            outcome="CORRECTED",
            failure_class="DATA_FIDELITY",
            source_revision="abc123",
        )
        eid = created["experience_id"]
        ee.verify_candidate(
            self.source,
            eid,
            task_id="SRC-1",
            verification_evidence=(
                proof("REAL_PATH", "evidence:behavior", "BEHAVIOR_PROOF"),
                proof("REGRESSION", "evidence:regression", "REGRESSION_PROOF"),
                proof("ADVERSARIAL", "evidence:challenge", "CHALLENGE_PROOF"),
            ),
        )
        ee.activate_verified(self.source, eid, task_id="SRC-1")
        return eid

    def promote(self) -> tuple[str, str]:
        eid = self.active_source()
        proposal = ef.build_promotion_proposal(
            self.source,
            eid,
            source_project="logistics-work-desk-arena",
            scope="CROSS_PROJECT",
            scope_evidence=(
                {"project": "another-mongo-project", "ref": "evidence:external", "verdict": "PROVEN"},
            ),
            procedure=(
                "Verify source and destination identity before mutation.",
                "Run typed round-trip comparison and source immutability proof.",
            ),
            inputs=("source database", "destination database"),
            outputs=("verified snapshot", "evidence packet"),
        )
        record = ef.apply_promotion(proposal, catalog_path=self.catalog)
        return eid, record["record_id"]

    def test_activation_summary_reads_shared_catalog_without_mutating_project_ledger(self) -> None:
        _, record_id = self.promote()
        ledger = self.target / ".p2p" / "state" / "execution-ledger.jsonl"
        self.assertFalse(ledger.exists())
        with mock.patch.object(ef, "default_catalog_path", return_value=self.catalog):
            result = ee.activation_summary(self.target, "mongo bson snapshot", max_results=3)
        self.assertEqual("USE_ACTIVE_EXPERIENCE", result["decision"])
        self.assertEqual(0, result["local_match_count"])
        self.assertEqual(1, result["shared_match_count"])
        self.assertEqual("P2P_SHARED_PROMOTED_CATALOG", result["experiences"][0]["source"])
        self.assertEqual(record_id, result["experiences"][0]["shared_record_id"])
        self.assertFalse(result["mutated"])
        self.assertFalse(ledger.exists())

    def test_local_active_experience_precedes_matching_shared_record(self) -> None:
        eid, _ = self.promote()
        # Recreate the same deterministic experience in the target and activate it.
        source_state = ee.derive_experiences(self.source)[eid]
        created = ee.create_candidate(
            self.target,
            task_id="TARGET-1",
            kind=source_state["kind"],
            trigger_tokens=source_state["trigger_tokens"],
            lesson=source_state["lesson"],
            correction=source_state["correction"],
            failure_class=source_state["failure_class"],
            outcome=source_state["outcome"],
            evidence=source_state["evidence"],
        )
        ee.verify_candidate(
            self.target,
            created["experience_id"],
            task_id="TARGET-1",
            verification_evidence=source_state["verification_evidence"],
        )
        ee.activate_verified(self.target, created["experience_id"], task_id="TARGET-1")
        with mock.patch.object(ef, "default_catalog_path", return_value=self.catalog):
            result = ee.activation_summary(self.target, "mongo bson snapshot", max_results=3)
        self.assertEqual(1, result["local_match_count"])
        self.assertEqual(0, result["shared_match_count"])
        self.assertEqual("PROJECT_LOCAL_LEDGER", result["experiences"][0]["source"])

    def test_promotion_cli_builds_proposal_but_never_applies_catalog(self) -> None:
        eid = self.active_source()
        before = self.catalog.read_text(encoding="utf-8")
        proposal = ep.build_from_spec(self.source, eid, {
            "source_project": "logistics-work-desk-arena",
            "scope": "CROSS_PROJECT",
            "scope_evidence": [
                {"project": "another-mongo-project", "ref": "evidence:external", "verdict": "PROVEN"}
            ],
            "procedure": ["Verify source identity.", "Verify typed round trip."],
            "inputs": ["source database"],
            "outputs": ["evidence packet"],
        })
        self.assertEqual("PROMOTION_CANDIDATE", proposal["status"])
        self.assertEqual(before, self.catalog.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ef.ExperienceFederationError, "SOURCE_PROJECT_REQUIRED"):
            ep.build_from_spec(self.source, eid, {"scope": "PROJECT_ONLY"})

    def test_installed_agent_contract_requires_automatic_reconciliation_and_skill_gate(self) -> None:
        text = (ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("The Owner must not have to request periodic experience harvesting", text)
        self.assertIn("PROJECT_ONLY | DOMAIN | CROSS_PROJECT", text)
        self.assertIn("experience_promotion.py", text)
        self.assertIn("shared_experience_catalog.json", text)
        self.assertIn("SKILL_CANDIDATE", text)
        self.assertIn("creates no `SKILL.md`", text)
        self.assertIn("existing P2P skill eligibility", text)


if __name__ == "__main__":
    unittest.main()
