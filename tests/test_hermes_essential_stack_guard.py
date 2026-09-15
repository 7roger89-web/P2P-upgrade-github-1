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
        self.assertFalse(result["opik_enabled"])
        self.assertFalse(result["opik_capture_content"])
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

    def test_opik_requires_explicit_gate_and_cloud_identity(self) -> None:
        rendered = mod.render_env(mod.ENV_EXAMPLE_PATH.read_text(encoding="utf-8"))
        enabled = rendered.replace("P2P_ENABLE_OPIK=NO", "P2P_ENABLE_OPIK=YES")
        with self.assertRaisesRegex(mod.StackContractError, "ENV_OPIK_KEY_REQUIRED_WHEN_ENABLED"):
            mod.validate_env(enabled)

        with_key = enabled.replace("OPIK_API_KEY=", "OPIK_API_KEY=test-opik-key")
        with self.assertRaisesRegex(mod.StackContractError, "ENV_OPIK_WORKSPACE_REQUIRED_WHEN_ENABLED"):
            mod.validate_env(with_key)

        ready = with_key.replace("OPIK_WORKSPACE=", "OPIK_WORKSPACE=test-workspace")
        result = mod.validate_env(ready)
        self.assertTrue(result["opik_enabled"])
        self.assertFalse(result["opik_capture_content"])

    def test_opik_content_capture_requires_enabled_observer(self) -> None:
        rendered = mod.render_env(mod.ENV_EXAMPLE_PATH.read_text(encoding="utf-8"))
        bad = rendered.replace("P2P_OPIK_CAPTURE_CONTENT=NO", "P2P_OPIK_CAPTURE_CONTENT=YES")
        with self.assertRaisesRegex(mod.StackContractError, "ENV_OPIK_CONTENT_CAPTURE_REQUIRES_ENABLE"):
            mod.validate_env(bad)

    def test_opik_pilot_rejects_custom_endpoint_and_analytics(self) -> None:
        rendered = mod.render_env(mod.ENV_EXAMPLE_PATH.read_text(encoding="utf-8"))
        ready = (
            rendered.replace("P2P_ENABLE_OPIK=NO", "P2P_ENABLE_OPIK=YES")
            .replace("OPIK_API_KEY=", "OPIK_API_KEY=test-opik-key")
            .replace("OPIK_WORKSPACE=", "OPIK_WORKSPACE=test-workspace")
        )
        custom = ready.replace(
            "OPIK_URL_OVERRIDE=https://www.comet.com/opik/api",
            "OPIK_URL_OVERRIDE=https://example.com/opik/api",
        )
        with self.assertRaisesRegex(mod.StackContractError, "ENV_OPIK_PILOT_URL_MUST_BE_COMET_CLOUD"):
            mod.validate_env(custom)

        analytics = ready.replace("OPIK_ANALYTICS_ENABLE=false", "OPIK_ANALYTICS_ENABLE=true")
        with self.assertRaisesRegex(mod.StackContractError, "ENV_OPIK_ANALYTICS_MUST_BE_DISABLED"):
            mod.validate_env(analytics)

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
        self.assertTrue(result["opik_cloud_only"])
        self.assertFalse(result["opik_second_control_plane"])
        self.assertFalse(result["mission_control_authority"])

    def test_workspace_wrapper_is_exact_commit_and_pnpm_pinned(self) -> None:
        text = mod.WORKSPACE_DOCKERFILE_PATH.read_text(encoding="utf-8")
        result = mod.validate_workspace_dockerfile(text)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["commit"], mod.WORKSPACE_COMMIT)
        self.assertEqual(result["pnpm"], mod.WORKSPACE_PNPM)

    def test_runtime_opik_dependency_is_exact_and_default_off(self) -> None:
        text = mod.RUNTIME_DOCKERFILE_PATH.read_text(encoding="utf-8")
        result = mod.validate_runtime_dockerfile(text)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["opik"], "opik==2.2.59")
        self.assertFalse(result["default_installed"])

    def test_post_bootstrap_requires_explicit_opik_gate(self) -> None:
        text = mod.POST_BOOTSTRAP_PATH.read_text(encoding="utf-8")
        result = mod.validate_post_bootstrap(text)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["opik_explicit_gate"])

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

    def test_compose_rejects_full_opik_self_host_infrastructure(self) -> None:
        text = mod.COMPOSE_PATH.read_text(encoding="utf-8")
        bad = text + "\nservices:\n  clickhouse:\n    image: clickhouse/clickhouse-server\n"
        with self.assertRaisesRegex(mod.StackContractError, "COMPOSE_FORBIDDEN_FRAGMENT:clickhouse:"):
            mod.validate_compose(bad)


if __name__ == "__main__":
    unittest.main()
