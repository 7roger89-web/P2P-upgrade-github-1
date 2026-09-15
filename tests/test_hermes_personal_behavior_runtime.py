from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
PLUGIN_DIR = (
    REPO_ROOT
    / "deployments"
    / "hermes-dockhosting"
    / "plugins"
    / "p2p-personal-behavior"
)

if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))


def _load_plugin():
    name = "p2p_personal_behavior_runtime_test_plugin"
    spec = importlib.util.spec_from_file_location(
        name,
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Personal AI Hermes plugin")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


plugin = _load_plugin()


class FakePluginContext:
    def __init__(self) -> None:
        self.sections: list[tuple] = []
        self.hooks: dict[str, object] = {}

    def register_system_prompt_section(self, *args, **kwargs):
        self.sections.append((args, kwargs))

    def register_hook(self, name, callback):
        self.hooks[name] = callback


class HermesPersonalBehaviorRuntimeTests(unittest.TestCase):
    def test_manifest_declares_runtime_hooks(self) -> None:
        manifest = (PLUGIN_DIR / "plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("name: p2p-personal-behavior", manifest)
        self.assertIn("- pre_llm_call", manifest)
        self.assertIn("- transform_llm_output", manifest)

    def test_register_uses_documented_plugin_surfaces(self) -> None:
        ctx = FakePluginContext()
        plugin.register(ctx)
        self.assertEqual(len(ctx.sections), 1)
        args, kwargs = ctx.sections[0]
        self.assertEqual(args[0], "p2p-personal-behavior.voice")
        self.assertEqual(kwargs["position"], "after_memory")
        self.assertLessEqual(kwargs["max_chars"], 4000)
        self.assertEqual(set(ctx.hooks), {"pre_llm_call", "transform_llm_output"})

    def test_system_section_keeps_facts_above_style(self) -> None:
        text = plugin._system_prompt_section({"platform": "telegram"})
        self.assertIn("Factual correctness", text)
        self.assertIn("Never change amounts, currencies, units, routes, dates", text)
        self.assertIn("Do not claim research, tool use", text)
        self.assertIn("Do not end with a generic offer", text)

    def test_normal_turn_adds_no_ephemeral_context_tax(self) -> None:
        self.assertIsNone(plugin._pre_llm_call("Hôm nay có gì cần làm?"))

    def test_serious_override_disables_humor_for_that_turn(self) -> None:
        result = plugin._pre_llm_call("Trả lời nghiêm túc: phân tích rủi ro này.")
        self.assertIsInstance(result, dict)
        context = result["context"]
        self.assertIn("seriousness=1.00", context)
        self.assertIn("humor_allowed=false", context)
        self.assertIn("Serious-mode override", context)

    def test_short_and_deep_requests_map_to_existing_controller(self) -> None:
        short = plugin._pre_llm_call("Trả lời ngắn gọn giúp tao.")
        deep = plugin._pre_llm_call("Nghiên cứu sâu vấn đề này.")
        self.assertIn("depth=short", short["context"])
        self.assertIn("depth=deep", deep["context"])

    def test_deep_wins_if_message_contains_both_depth_phrases(self) -> None:
        result = plugin._pre_llm_call(
            "Tóm tắt ngắn gọn trước, rồi nghiên cứu sâu phần nguyên nhân."
        )
        self.assertIn("depth=deep", result["context"])

    def test_output_lint_is_report_only_and_logs_codes_not_excerpt(self) -> None:
        response = (
            "Câu hỏi rất hay. Tôi hoàn toàn hiểu. "
            "Nếu bạn muốn, tôi có thể làm thêm."
        )
        with self.assertLogs(plugin.logger.name, level="INFO") as captured:
            transformed = plugin._transform_llm_output(response)
        self.assertIsNone(transformed)
        log_text = "\n".join(captured.output)
        self.assertIn("SYCOPHANTIC_OPENER", log_text)
        self.assertIn("GENERIC_FOLLOWUP_OFFER", log_text)
        self.assertNotIn("Câu hỏi rất hay", log_text)

    def test_both_hosted_dockerfiles_bundle_plugin_and_canonical_module(self) -> None:
        expected_plugin = (
            "deployments/hermes-dockhosting/plugins/p2p-personal-behavior/ "
            "/opt/hermes/plugins/p2p-personal-behavior/"
        )
        expected_module = (
            ".p2p/system/p2p_capabilities/personal_ai_behavior.py "
            "/opt/hermes/plugins/p2p-personal-behavior/personal_ai_behavior.py"
        )
        for relative in ("Dockerfile", "deployments/hermes-dockhosting/Dockerfile"):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(expected_plugin, text, relative)
            self.assertIn(expected_module, text, relative)

    def test_entrypoint_enables_plugin_for_new_and_existing_config(self) -> None:
        entrypoint = (
            REPO_ROOT / "deployments" / "hermes-dockhosting" / "dockhosting-entrypoint.sh"
        ).read_text(encoding="utf-8")
        enable = "/opt/hermes/.venv/bin/hermes plugins enable p2p-personal-behavior"
        self.assertIn(enable, entrypoint)
        # The command must sit after the config-creation `fi`, so an already
        # persisted config is converged too rather than silently skipping it.
        self.assertGreater(entrypoint.index(enable), entrypoint.index("\nfi\n", entrypoint.index("config.yaml")))
        self.assertNotIn(enable + " || true", entrypoint)


if __name__ == "__main__":
    unittest.main()
