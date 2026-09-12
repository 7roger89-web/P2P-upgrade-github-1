import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "free_model_probe.py"
SPEC = importlib.util.spec_from_file_location("free_model_probe", MODULE_PATH)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


class FreeModelProbeTests(unittest.TestCase):
    def test_extract_model_ids_ignores_invalid_items(self) -> None:
        payload = {"data": [{"id": "A"}, {"id": "B"}, {"name": "ignored"}, "bad"]}
        self.assertEqual(probe.extract_model_ids(payload), ["A", "B"])

    def test_candidate_models_keep_allowlist_order_and_skip_missing(self) -> None:
        available = ["some-paid-model", "HY3", "mimo-v2.5"]
        self.assertEqual(
            probe.candidate_models(probe.PRESETS["bai"], available, {}),
            ["mimo-v2.5", "HY3"],
        )

    def test_choose_model_prefers_first_current_free_candidate(self) -> None:
        available = ["glm-5.3-flash", "hy3", "mimo-v2.5"]
        self.assertEqual(
            probe.choose_model(probe.PRESETS["bai"], available, {}),
            "mimo-v2.5",
        )

    def test_explicit_model_must_exist_when_discovery_is_available(self) -> None:
        available = ["mimo-v2.5"]
        self.assertIsNone(
            probe.choose_model(
                probe.PRESETS["bai"], available, {"BAI_MODEL": "not-present"}
            )
        )

    def test_cline_uses_documented_free_candidate_without_discovery(self) -> None:
        self.assertEqual(
            probe.choose_model(probe.PRESETS["cline"], None, {}),
            "minimax/minimax-m2.5",
        )

    def test_extract_chat_text_is_defensive(self) -> None:
        self.assertEqual(
            probe.extract_chat_text({"choices": [{"message": {"content": "ok"}}]}),
            "ok",
        )
        self.assertEqual(probe.extract_chat_text({"choices": []}), "")

    def test_extract_responses_text_skips_reasoning_and_joins_output_text(self) -> None:
        payload = {
            "output": [
                {"type": "reasoning", "summary": []},
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "P2P_"},
                        {"type": "refusal", "refusal": "ignored"},
                        {"type": "output_text", "text": "PROBE_OK"},
                    ],
                },
            ]
        }
        self.assertEqual(probe.extract_responses_text(payload), "P2P_PROBE_OK")

    def test_protocol_capability_is_explicit(self) -> None:
        self.assertIn("responses", probe.PRESETS["bai"].protocols)
        self.assertNotIn("responses", probe.PRESETS["cline"].protocols)
        self.assertNotIn("responses", probe.PRESETS["amd"].protocols)


if __name__ == "__main__":
    unittest.main()
