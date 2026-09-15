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
        self.assertFalse(result["geniex_enabled"])
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

    def test_geniex_requires_explicit_gate_local_url_and_model(self) -> None:
        rendered = mod.render_env(mod.ENV_EXAMPLE_PATH.read_text(encoding="utf-8"))
        enabled = rendered.replace("P2P_ENABLE_GENIEX=NO", "P2P_ENABLE_GENIEX=YES")
        with self.assertRaisesRegex(mod.StackContractError, "ENV_GENIEX_BASE_URL_REQUIRED_WHEN_ENABLED"):
            mod.validate_env(enabled)

        with_url = enabled.replace(
            "GENIEX_BASE_URL=",
            "GENIEX_BASE_URL=http://host.docker.internal:18181/v1",
        )
        with self.assertRaisesRegex(mod.StackContractError, "ENV_GENIEX_MODEL_REQUIRED_WHEN_ENABLED"):
            mod.validate_env(with_url)

        ready = with_url.replace(
            "GENIEX_MODEL=",
            "GENIEX_MODEL=ai-hub-models/Qwen3-4B-Instruct-2507",
        )
        self.assertTrue(mod.validate_env(ready)["geniex_enabled"])

    def test_geniex_rejects_remote_or_non_v1_endpoint(self) -> None:
        rendered = mod.render_env(mod.ENV_EXAMPLE_PATH.read_text(encoding="utf-8"))
        base = rendered.replace("P2P_ENABLE_GENIEX=NO", "P2P_ENABLE_GENIEX=YES").replace(
            "GENIEX_MODEL=",
            "GENIEX_MODEL=ai-hub-models/Qwen3-4B-Instruct-2507",
        )
        remote = base.replace("GENIEX_BASE_URL=", "GENIEX_BASE_URL=https://example.com/v1")
        with self.assertRaisesRegex(mod.StackContractError, "ENV_GENIEX_BASE_URL_MUST_BE_LOCAL_HTTP"):
            mod.validate_env(remote)

        wrong_path = base.replace(
            "GENIEX_BASE_URL=",
            "GENIEX_BASE_URL=http://127.0.0.1:18181/api",
        )
        with self.assertRaisesRegex(mod.StackContractError, "ENV_GENIEX_BASE_URL_MUST_END_IN_V1"):
            mod.validate_env(wrong_path)

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
        self.assertTrue(result["geniex_named_provider_only"])
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

    def test_compose_rejects_geniex_main_model_takeover(self) -> None:
        text = mod.COMPOSE_PATH.read_text(encoding="utf-8")
        bad = text.replace(
            '/opt/hermes/.venv/bin/hermes config set providers.geniex.api "$${GENIEX_BASE_URL}";',
            '/opt/hermes/.venv/bin/hermes config set model.provider custom;',
        )
        with self.assertRaises(mod.StackContractError):
            mod.validate_compose(bad)


if __name__ == "__main__":
    unittest.main()