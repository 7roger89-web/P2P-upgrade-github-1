import unittest

from src.experiment_tracker import summarize_observations


class ExperimentTrackerTests(unittest.TestCase):
    def test_contact_only_does_not_count_submission_or_money(self):
        summary = summarize_observations(
            [{"participant_id": "p1", "status": "CONTACTED", "observed_at": "x"}],
            target_contacts=5,
            submission_success=3,
            repeat_or_wtp_success=2,
        )
        self.assertEqual(summary["submitted"], 0)
        self.assertEqual(summary["money_evidence"], [])
        self.assertFalse(summary["success_threshold_reached"])

    def test_repeat_request_counts_retention_not_money(self):
        summary = summarize_observations(
            [{"participant_id": "p1", "status": "REPEAT_REQUEST", "observed_at": "x"}],
            target_contacts=5,
            submission_success=3,
            repeat_or_wtp_success=2,
        )
        self.assertEqual(summary["repeat_or_wtp"], 1)
        self.assertEqual(summary["money_evidence"], [])

    def test_wtp_requires_explicit_amount(self):
        with self.assertRaises(ValueError):
            summarize_observations(
                [{"participant_id": "p1", "status": "WTP_SIGNAL", "observed_at": "x"}],
                target_contacts=5,
                submission_success=3,
                repeat_or_wtp_success=2,
            )

    def test_success_threshold_creates_only_observed_money_evidence(self):
        rows = [
            {"participant_id": "p1", "status": "SUBMITTED", "observed_at": "x"},
            {"participant_id": "p1", "status": "REPEAT_REQUEST", "observed_at": "x"},
            {"participant_id": "p2", "status": "SUBMITTED", "observed_at": "x"},
            {
                "participant_id": "p2",
                "status": "WTP_SIGNAL",
                "wtp_amount": 30,
                "wtp_currency": "USD",
                "observed_at": "x",
            },
            {"participant_id": "p3", "status": "SUBMITTED", "observed_at": "x"},
        ]
        summary = summarize_observations(
            rows,
            target_contacts=5,
            submission_success=3,
            repeat_or_wtp_success=2,
        )
        self.assertTrue(summary["success_threshold_reached"])
        self.assertEqual(summary["status"], "COMPLETED")
        self.assertEqual(summary["money_evidence"][0]["signal"], "WILLINGNESS_TO_PAY")

    def test_failure_only_after_contact_target_reached(self):
        rows = [
            {"participant_id": f"p{i}", "status": "CONTACTED", "observed_at": "x"}
            for i in range(1, 6)
        ]
        summary = summarize_observations(
            rows,
            target_contacts=5,
            submission_success=3,
            repeat_or_wtp_success=2,
        )
        self.assertTrue(summary["failure_threshold_reached"])
        self.assertEqual(summary["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
