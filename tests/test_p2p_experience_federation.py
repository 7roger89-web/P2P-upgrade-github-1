from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities import experience_evolution as ee  # noqa: E402
from p2p_capabilities import experience_federation as ef  # noqa: E402


def proof(kind: str, ref: str, role: str = "") -> dict[str, str]:
    return {"kind": kind, "ref": ref, "role": role, "verdict": "PROVEN"}


class ExperienceFederationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="p2p-exp-fed-")
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.target = self.base / "target"
        self.catalog = self.base / "shared_experience_catalog.json"
        self.source.mkdir()
        self.target.mkdir()
        self.catalog.write_text(
            json.dumps({
                "schema": ef.CATALOG_SCHEMA,
                "catalog_role": "CURATED_PROMOTED_EXPERIENCE_DISTRIBUTION",
                "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
                "records": [],
            }),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def active(self, *, kind: str = "PROCEDURAL") -> str:
        created = ee.create_candidate(
            self.source,
            task_id="LOGI-1",
            kind=kind,
            trigger_tokens=("mongo", "snapshot", "bson"),
            lesson="Preserve typed BSON fidelity before accepting a Mongo snapshot.",
            correction="Use a typed canonical round trip and compare the source before and after copy.",
            failure_class="DATA_FIDELITY",
            outcome="CORRECTED",
            source_revision="abc123",
            evidence=(proof("REAL_PATH", "evidence:source"),),
        )
        eid = created["experience_id"]
        ee.verify_candidate(
            self.source,
            eid,
            task_id="LOGI-1",
            verification_evidence=(
                proof("REAL_PATH", "evidence:behavior", "BEHAVIOR_PROOF"),
                proof("REGRESSION", "evidence:regression", "REGRESSION_PROOF"),
                proof("ADVERSARIAL", "evidence:challenge", "CHALLENGE_PROOF"),
            ),
        )
        ee.activate_verified(self.source, eid, task_id="LOGI-1")
        return eid

    def promotion(self, eid: str, *, scope: str = "CROSS_PROJECT", kind_inputs: bool = True):
        kwargs = {}
        if kind_inputs:
            kwargs = {
                "procedure": (
                    "Verify source and destination identity before mutation.",
                    "Run typed round-trip comparison and source immutability proof.",
                ),
                "inputs": ("source database", "destination database"),
                "outputs": ("verified snapshot", "evidence packet"),
            }
        return ef.build_promotion_proposal(
            self.source,
            eid,
            source_project="logistics-work-desk-arena",
            scope=scope,
            domain="data" if scope == "DOMAIN" else "",
            scope_evidence=(
                {"project": "another-mongo-project", "ref": "evidence:external-replay", "verdict": "PROVEN"},
            ),
            **kwargs,
        )

    def test_project_only_experience_stays_local(self) -> None:
        eid = self.active()
        result = ef.build_promotion_proposal(
            self.source,
            eid,
            source_project="logistics-work-desk-arena",
            scope="PROJECT_ONLY",
            scope_evidence=(),
        )
        self.assertEqual("KEEP_LOCAL", result["status"])
        self.assertFalse(result["promotable"])
        with self.assertRaisesRegex(ef.ExperienceFederationError, "NOT_PROMOTABLE"):
            ef.apply_promotion(result, catalog_path=self.catalog)

    def test_cross_project_promotion_requires_out_of_project_scope_proof(self) -> None:
        eid = self.active()
        with self.assertRaisesRegex(ef.ExperienceFederationError, "OUT_OF_PROJECT_SCOPE_PROOF_REQUIRED"):
            ef.build_promotion_proposal(
                self.source,
                eid,
                source_project="logistics-work-desk-arena",
                scope="CROSS_PROJECT",
                scope_evidence=(
                    {"project": "logistics-work-desk-arena", "ref": "evidence:same-project", "verdict": "PROVEN"},
                ),
            )

    def test_promoted_shared_experience_syncs_into_existing_local_ledger(self) -> None:
        eid = self.active()
        proposal = self.promotion(eid)
        promoted = ef.apply_promotion(proposal, catalog_path=self.catalog)
        self.assertEqual("PROMOTED", promoted["status"])
        synced = ef.sync_shared_catalog(self.target, catalog_path=self.catalog)
        self.assertEqual(1, synced["selected"])
        matches = ee.retrieve_active_experiences(self.target, "mongo bson snapshot", max_results=3)
        self.assertEqual(1, len(matches))
        self.assertEqual("ACTIVE", matches[0]["state"])
        self.assertEqual("NON_AUTHORITATIVE_VERIFIED_EXPERIENCE", matches[0]["authority"])

    def test_domain_record_only_syncs_for_matching_domain(self) -> None:
        eid = self.active()
        proposal = self.promotion(eid, scope="DOMAIN")
        ef.apply_promotion(proposal, catalog_path=self.catalog)
        skipped = ef.sync_shared_catalog(self.target, domain="legal", catalog_path=self.catalog)
        self.assertEqual(0, skipped["selected"])
        matched = ef.sync_shared_catalog(self.target, domain="data", catalog_path=self.catalog)
        self.assertEqual(1, matched["selected"])

    def test_local_quarantine_wins_over_shared_catalog_on_resync(self) -> None:
        eid = self.active()
        proposal = self.promotion(eid)
        ef.apply_promotion(proposal, catalog_path=self.catalog)
        ef.sync_shared_catalog(self.target, catalog_path=self.catalog)
        target_eid = ee.retrieve_active_experiences(self.target, "mongo bson snapshot")[0]["experience_id"]
        ee.quarantine_experience(
            self.target,
            target_eid,
            reason="Harmed current project after representative replay.",
            evidence=(proof("REAL_PATH", "evidence:harmed"),),
            task_id="TARGET-2",
        )
        second = ef.sync_shared_catalog(self.target, catalog_path=self.catalog)
        self.assertEqual(1, second["counts"]["QUARANTINED"])
        self.assertEqual("QUARANTINED", ee.derive_experiences(self.target)[target_eid]["state"])

    def test_skill_candidate_requires_cross_project_procedural_stable_io(self) -> None:
        eid = self.active()
        promoted = ef.apply_promotion(self.promotion(eid), catalog_path=self.catalog)
        candidate = ef.skill_candidate_from_catalog(promoted["record_id"], catalog_path=self.catalog)
        self.assertEqual("CANDIDATE", candidate["status"])
        self.assertEqual("NONE", candidate["activation_authority"])
        self.assertEqual("NO", candidate["registry_mutation"])
        self.assertEqual("NO", candidate["skill_file_created"])
        self.assertTrue(candidate["must_pass_existing_skill_eligibility"])
        self.assertFalse((self.target / "SKILL.md").exists())

    def test_skill_candidate_rejects_domain_only_and_missing_procedure(self) -> None:
        domain_eid = self.active()
        domain_record = ef.apply_promotion(self.promotion(domain_eid, scope="DOMAIN"), catalog_path=self.catalog)
        with self.assertRaisesRegex(ef.ExperienceFederationError, "CROSS_PROJECT"):
            ef.skill_candidate_from_catalog(domain_record["record_id"], catalog_path=self.catalog)

        # Isolate a second catalog to challenge missing stable workflow metadata.
        second_catalog = self.base / "second.json"
        second_catalog.write_text(json.dumps({
            "schema": ef.CATALOG_SCHEMA,
            "catalog_role": "CURATED_PROMOTED_EXPERIENCE_DISTRIBUTION",
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "records": [],
        }), encoding="utf-8")
        proposal = self.promotion(domain_eid, scope="CROSS_PROJECT", kind_inputs=False)
        record = ef.apply_promotion(proposal, catalog_path=second_catalog)
        with self.assertRaisesRegex(ef.ExperienceFederationError, "STABLE_IO_AND_PROCEDURE"):
            ef.skill_candidate_from_catalog(record["record_id"], catalog_path=second_catalog)

    def test_catalog_apply_is_idempotent_and_conflict_fail_closed(self) -> None:
        eid = self.active()
        proposal = self.promotion(eid)
        first = ef.apply_promotion(proposal, catalog_path=self.catalog)
        second = ef.apply_promotion(proposal, catalog_path=self.catalog)
        self.assertEqual("PROMOTED", first["status"])
        self.assertEqual("EXISTS", second["status"])
        catalog = ef.load_catalog(self.catalog)
        self.assertEqual(1, len(catalog["records"]))


if __name__ == "__main__":
    unittest.main()
