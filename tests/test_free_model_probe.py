import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "free_model_probe.py"
SPEC = importlib.util.spec_from_file_location("free_model_probe", MODULE_PATH)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class FreeModelProbeTests(unittest.TestCase):
    def test_extract_model_ids_ignores_invalid_items(self) -> None:
        payload = {"data": [{"id": "A"}, {"id": "B"}, {"name": "ignored"}, "bad"]}
        self.assertEqual(probe.extract_model_ids(payload), ["A", "B"])

    def test_choose_model_prefers_first_allowlisted_available_model(self) -> None:
        available = ["some-paid-model", "GLM-5.3-FLASH", "mimo-v2.5"]
        self.assertEqual(
            probe.choose_model(probe.PRESETS["bai"], available, {}),
            "GLM-5.3-FLASH",
        )

    def test_explicit_model_must_exist_when_discovery_is_available(self) -> None:
        available = ["glm-5.3-flash"]
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


if __name__ == "__main__":
    unittest.main()
