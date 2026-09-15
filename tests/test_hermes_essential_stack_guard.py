from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "hermes_essential_stack_guard.py"
spec = importlib.util.spec_from_file_location("hermes_essential_stack_guard", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestHermesEssentialStackGuard(unittest.TestCase):
    def test_example_is_complete_but_placeholder_gated(self) -> None:
        text = mod.ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
        result = mod.validate_env(text, allow_placeholders=True)
        self.assertEqual(result["status"], "PASS")
        with self.assertRaises(mod.StackContractError):
            mod.validate_env(text, allow_placeholders=False)

    def test_rendered_env_has_distinct_strong_secrets(self) -> None:
        rendered = mod.render_env(mod.ENV_EXAMPLE_PATH.read_text(encoding="utf-8"))
        env = mod.parse_env(rendered)
        result = mod.validate_env(rendered)
        self.assertEqual(result["status"], "PASS")
        values = [env[key] for key in mod.SECRET_KEYS]
        self.assertEqual(len(values), len(set(values)))
        self.assertTrue(all(len(value) >= 32 for value in values))

    def test_hindsight_requires_explicit_gate_and_key(self) -> None:
        rendered = mod.render_env(mod.ENV_EXAMPLE_PATH.read_text(encoding="utf-8"))
        enabled_without_key = rendered.replace("P2P_ENABLE_HINDSIGHT=NO", "P2P_ENABLE_HINDSIGHT=YES")
        with self.assertRaises(mod.StackContractError):
            mod.validate_env(enabled_without_key)
        enabled = enabled_without_key.replace("HINDSIGHT_API_KEY=", "HINDSIGHT_API_KEY=test-key")
        self.assertTrue(mod.validate_env(enabled)["hindsight_enabled"])

    def test_init_refuses_to_overwrite_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / ".env"
            first = mod.init_env(path)
            self.assertEqual(first["status"], "CREATED")
            with self.assertRaises(mod.StackContractError):
                mod.init_env(path)

    def test_compose_contract_is_local_pinned_and_no_second_control_plane(self) -> None:
        text = mod.COMPOSE_PATH.read_text(encoding="utf-8")
        result = mod.validate_compose(text)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["mission_control_authority"])

    def test_workspace_wrapper_is_exact_commit_and_pnpm_pinned(self) -> None:
        text = mod.WORKSPACE_DOCKERFILE_PATH.read_text(encoding="utf-8")
        result = mod.validate_workspace_dockerfile(text)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["commit"], mod.WORKSPACE_COMMIT)
        self.assertEqual(result["pnpm"], mod.WORKSPACE_PNPM)

    def test_compose_rejects_public_workspace_bind(self) -> None:
        text = mod.COMPOSE_PATH.read_text(encoding="utf-8")
        bad = text.replace("127.0.0.1:3000:3000", "0.0.0.0:3000:3000")
        with self.assertRaises(mod.StackContractError):
            mod.validate_compose(bad)

    def test_compose_rejects_tokscale_submit(self) -> None:
        text = mod.COMPOSE_PATH.read_text(encoding="utf-8")
        bad = text.replace('tokscale@4.16.0", "--json"', 'tokscale@4.16.0", "submit", "--json"')
        with self.assertRaises(mod.StackContractError):
            mod.validate_compose(bad)


if __name__ == "__main__":
    unittest.main()
