from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import p2p_governance  # noqa: E402


class P2PGovernanceDriftTests(unittest.TestCase):
    def test_drift_findings_are_exact_path_scoped_and_classified(self) -> None:
        governance = REPO_ROOT / "governance"
        policy = json.loads((governance / "drift-policy.json").read_text(encoding="utf-8"))
        scoped = policy["scoped_volatile_paths"]
        self.assertEqual(len(scoped), 10)
        self.assertTrue(all(not key.endswith("/") for key in scoped))
        claims = json.loads((governance / "fact-ledger.json").read_text(encoding="utf-8"))["claims"]
        claims_by_id = {claim["claim_id"]: claim for claim in claims}
        references: list[dict[str, object]] = []
        findings = p2p_governance.scan_volatile(
            REPO_ROOT,
            governance,
            claims_by_id,
            date(2026, 8, 13),
            14,
            references,
        )
        self.assertEqual(findings, [])
        self.assertEqual(len(references), 35)
        self.assertEqual(
            {item["classification"] for item in references},
            {"C", "D"},
        )
        self.assertEqual(
            sum(item["classification"] == "C" for item in references),
            4,
        )
        self.assertEqual(
            sum(item["classification"] == "D" for item in references),
            31,
        )


if __name__ == "__main__":
    unittest.main()
