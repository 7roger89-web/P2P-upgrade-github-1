import json
import unittest
from copy import deepcopy
from pathlib import Path

from src.concierge_engine import compare_quotes
from src.validation_pipeline import compare_quotes_validated


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "pilots"
    / "logistics-quote-comparison"
    / "fixtures"
    / "synthetic-validated-quote-set-02.json"
)


class IdentityIntegrityTests(unittest.TestCase):
    def test_validated_pipeline_rejects_duplicate_quote_ids_before_resolution(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        dirty = deepcopy(data)
        dirty["quotes"][1]["quote_id"] = dirty["quotes"][0]["quote_id"]

        with self.assertRaisesRegex(ValueError, r"duplicate quote_id 'VAL-A'"):
            compare_quotes_validated(dirty["quotes"], dirty["context"])

    def test_core_engine_rejects_duplicate_quote_ids_before_grouping(self):
        quotes = [
            {
                "quote_id": "DUP-1",
                "currency": "USD",
                "route": {"origin": "Shanghai", "destination": "Hai Phong"},
                "equipment": "40HC",
                "charges": [
                    {
                        "name": "Ocean Freight",
                        "amount": 1000,
                        "basis": "PER_CONTAINER",
                        "source_ref": "q1:r1",
                    }
                ],
            },
            {
                "quote_id": "DUP-1",
                "currency": "USD",
                "route": {"origin": "Shanghai", "destination": "Hai Phong"},
                "equipment": "40HC",
                "charges": [
                    {
                        "name": "Ocean Freight",
                        "amount": 900,
                        "basis": "PER_CONTAINER",
                        "source_ref": "q2:r1",
                    }
                ],
            },
        ]
        context = {"containers": 1, "shipments": 1, "bl_count": 1, "weight_kg": 0, "cbm": 0}

        with self.assertRaisesRegex(ValueError, r"duplicate quote_id 'DUP-1'"):
            compare_quotes(quotes, context)


if __name__ == "__main__":
    unittest.main()
