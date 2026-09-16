import unittest

from src.market_gate import evaluate_market_gate


def base_packet():
    return {
        "problem": "Teams waste time comparing inconsistent supplier quotes.",
        "target_user": "SME logistics operators",
        "hypothesis": "At least 3 target users will pay for automated quote normalization after a manual prototype proves value.",
        "evidence": [],
        "experiment": {"status": "NOT_STARTED"},
        "owner_preference": "BUILD",
    }


class MarketGateTests(unittest.TestCase):
    def test_desk_research_cannot_build(self):
        p = base_packet()
        p["evidence"] = [
            {"class": "USER_SAID", "signal": "PAIN"},
            {"class": "USER_SAID", "signal": "DEMAND"},
            {"class": "OBSERVED", "signal": "COMPETITOR"},
            {"class": "OBSERVED", "signal": "PRICING"},
        ]
        self.assertEqual(evaluate_market_gate(p).decision, "VALIDATE")

    def test_real_experiment_plus_money_can_build(self):
        p = base_packet()
        p["evidence"] = [
            {"class": "USER_SAID", "signal": "PAIN"},
            {"class": "OBSERVED", "signal": "DEMAND"},
            {"class": "OBSERVED", "signal": "PAYMENT"},
        ]
        p["experiment"] = {
            "status": "COMPLETED",
            "source_class": "OBSERVED",
            "success_threshold_reached": True,
            "failure_threshold_reached": False,
        }
        self.assertEqual(evaluate_market_gate(p).decision, "BUILD")

    def test_failed_real_world_experiment_kills(self):
        p = base_packet()
        p["evidence"] = [{"class": "USER_SAID", "signal": "PAIN"}]
        p["experiment"] = {
            "status": "COMPLETED",
            "source_class": "OBSERVED",
            "success_threshold_reached": False,
            "failure_threshold_reached": True,
        }
        self.assertEqual(evaluate_market_gate(p).decision, "KILL")

    def test_one_viral_anecdote_is_not_market(self):
        p = base_packet()
        p["evidence"] = [
            {"class": "USER_SAID", "signal": "PAIN", "source": "one viral forum thread"}
        ]
        self.assertEqual(evaluate_market_gate(p).decision, "RESEARCH_MORE")

    def test_owner_preference_does_not_override_fatal_counterevidence(self):
        p = base_packet()
        p["owner_preference"] = "BUILD"
        p["evidence"] = [
            {"class": "OBSERVED", "signal": "DEMAND"},
            {
                "class": "OBSERVED",
                "signal": "ECONOMICS",
                "direction": "CONTRADICTS",
                "severity": "FATAL",
                "resolved": False,
            },
        ]
        self.assertEqual(evaluate_market_gate(p).decision, "KILL")


if __name__ == "__main__":
    unittest.main()
