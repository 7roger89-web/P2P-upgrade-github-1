"""Focused non-secret tests for the Hermes NotebookLM knowledge plugin."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN_DIR = (
    REPO_ROOT
    / "deployments"
    / "hermes-dockhosting"
    / "plugins"
    / "notebooklm-knowledge"
)


def load_plugin():
    spec = importlib.util.spec_from_file_location(
        "hermes_test_notebooklm_knowledge",
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PLUGIN = load_plugin()


def call_handler(args):
    """Invoke the async tool handler from this synchronous test process."""
    return asyncio.run(PLUGIN.tools.handle_notebooklm_search(args))


class FakeNotebook:
    def __init__(self, notebook_id: str, title: str):
        self.id = notebook_id
        self.title = title


class FakeSource:
    def __init__(self, source_id: str, title: str):
        self.id = source_id
        self.title = title


class FakePassage:
    def __init__(
        self,
        source_id: str,
        text: str,
        rank: int = 1,
        start: int = 10,
        end: int = 40,
    ):
        self.source_id = source_id
        self.text = text
        self.rank = rank
        self.start = start
        self.end = end


class FakeNotebooks:
    async def list(self):
        return [
            FakeNotebook("nb-hs", "Tra mã HS"),
            FakeNotebook("nb-chem", "Hóa chất"),
            FakeNotebook("nb-khcn", "Bộ khoa học công nghệ"),
            FakeNotebook("nb-btttt", "Bộ Thông Tin truyền thông"),
        ]


class FakeSources:
    def __init__(self):
        self.search_calls = []

    async def list(self, notebook_id):
        return [FakeSource(f"src-{notebook_id}", f"Nguồn {notebook_id}")]

    async def search(self, notebook_id, query, source_ids=None, limit=10):
        self.search_calls.append(
            {
                "notebook_id": notebook_id,
                "query": query,
                "source_ids": source_ids,
                "limit": limit,
            }
        )
        return [
            FakePassage(
                f"src-{notebook_id}",
                f"Passage grounded for {notebook_id}: {query}",
            )
        ]


class FakeClient:
    last_instance = None

    def __init__(self):
        self.notebooks = FakeNotebooks()
        self.sources = FakeSources()
        type(self).last_instance = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeNotebookLMClient:
    @classmethod
    def from_storage(cls):
        return FakeClient()


class RaisingNotebooks:
    """Simulates an upstream failure whose message carries credential-like
    material; the handler must never echo that material back."""

    LEAKED = "SUPERSECRET_SID=abc123 FdrFJe=leakme"

    async def list(self):
        raise PermissionError(f"denied: cookie={self.LEAKED}")


class RaisingClient:
    async def __aenter__(self):
        self.notebooks = RaisingNotebooks()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class RaisingNotebookLMClient:
    @classmethod
    def from_storage(cls):
        return RaisingClient()


class RouterTests(unittest.TestCase):
    def test_wifi_routes_to_btttt(self):
        self.assertEqual(
            PLUGIN.tools.route_domains("Router WiFi công nghiệp 2.4/5GHz"),
            ("BTTTT",),
        )

    def test_chemical_plus_hs_is_multilabel(self):
        routed = PLUGIN.tools.route_domains(
            "Keo dán chứa Toluene 25%, CAS 108-88-3 thì mã HS nào?"
        )
        self.assertIn("CHEMICAL", routed)
        self.assertIn("HS", routed)

    def test_used_machine_quality_routes_bkhcn(self):
        routed = PLUGIN.tools.route_domains(
            "Máy móc cũ nhập khẩu có phải kiểm tra chất lượng không?"
        )
        self.assertEqual(routed[0], "BKHCN")

    def test_unknown_does_not_guess(self):
        self.assertEqual(
            PLUGIN.tools.route_domains("Khách gửi cái này, xem giúp em"),
            (),
        )


class HandlerTests(unittest.TestCase):
    @staticmethod
    def _fake_module():
        module = types.ModuleType("notebooklm")
        module.NotebookLMClient = FakeNotebookLMClient
        return module

    def test_read_only_ranked_search_resolves_notebook_by_title(self):
        with patch.dict(
            os.environ,
            {
                "NOTEBOOKLM_AUTH_JSON": '{"cookies":[]}',
                "NOTEBOOKLM_NOTEBOOKS_JSON": "{}",
            },
            clear=False,
        ), patch.dict(sys.modules, {"notebooklm": self._fake_module()}):
            payload = json.loads(
                call_handler(
                    {
                        "question": "Router WiFi công nghiệp có cần kiểm tra gì?",
                        "domains": ["BTTTT"],
                        "limit_per_domain": 4,
                    }
                )
            )

        self.assertEqual(payload["status"], "OK")
        self.assertEqual(payload["mode"], "READ_ONLY_RANKED_PASSAGE_SEARCH")
        self.assertFalse(payload["legal_authority"])
        self.assertEqual(payload["routed_domains"], ["BTTTT"])
        result = payload["results"][0]
        self.assertEqual(result["notebook_title"], "Bộ Thông Tin truyền thông")
        self.assertEqual(result["passages"][0]["source_title"], "Nguồn nb-btttt")
        self.assertIn("Passage grounded", result["passages"][0]["text"])
        calls = FakeClient.last_instance.sources.search_calls
        self.assertEqual(calls[0]["notebook_id"], "nb-btttt")
        self.assertEqual(calls[0]["limit"], 4)

    def test_id_override_avoids_title_dependency(self):
        with patch.dict(
            os.environ,
            {
                "NOTEBOOKLM_AUTH_JSON": '{"cookies":[]}',
                "NOTEBOOKLM_NOTEBOOKS_JSON": '{"HS":"nb-hs"}',
            },
            clear=False,
        ), patch.dict(sys.modules, {"notebooklm": self._fake_module()}):
            payload = json.loads(
                call_handler(
                    {"question": "mã HS nào?", "domains": ["HS"]}
                )
            )
        self.assertEqual(payload["status"], "OK")
        self.assertEqual(payload["results"][0]["domain"], "HS")

    def test_unknown_question_fails_closed_to_needs_more_detail(self):
        with patch.dict(
            os.environ,
            {"NOTEBOOKLM_AUTH_JSON": '{"cookies":[]}'},
            clear=False,
        ):
            payload = json.loads(
                call_handler(
                    {"question": "Khách gửi cái này, xem giúp em"}
                )
            )
        self.assertEqual(payload["status"], "NEEDS_MORE_DETAIL")
        self.assertEqual(payload["routed_domains"], [])
        self.assertNotIn("notebook_id", payload)

    def test_missing_auth_is_fail_closed(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NOTEBOOKLM_AUTH_JSON", None)
            payload = json.loads(
                call_handler(
                    {"question": "Router wifi?", "domains": ["BTTTT"]}
                )
            )
        self.assertEqual(payload["error_type"], "notebooklm_config_missing")
        self.assertNotIn("cookies", json.dumps(payload))

    def test_bad_auth_json_is_sanitized(self):
        secret = "TOP_SECRET_COOKIE_VALUE"
        with patch.dict(
            os.environ,
            {"NOTEBOOKLM_AUTH_JSON": secret},
            clear=False,
        ):
            payload = json.loads(
                call_handler(
                    {"question": "mã HS nào?", "domains": ["HS"]}
                )
            )
        self.assertEqual(payload["error_type"], "notebooklm_config_error")
        self.assertNotIn(secret, json.dumps(payload))

    def test_auth_json_wrong_shape_is_config_error(self):
        secret = "TOP_SECRET_SHAPE_VALUE"
        with patch.dict(
            os.environ,
            {"NOTEBOOKLM_AUTH_JSON": json.dumps({"foo": secret})},
            clear=False,
        ):
            payload = json.loads(
                call_handler(
                    {"question": "mã HS nào?", "domains": ["HS"]}
                )
            )
        self.assertEqual(payload["error_type"], "notebooklm_config_error")
        self.assertNotIn(secret, json.dumps(payload))

    def test_upstream_exception_is_sanitized(self):
        raising_module = types.ModuleType("notebooklm")
        raising_module.NotebookLMClient = RaisingNotebookLMClient
        with patch.dict(
            os.environ,
            {"NOTEBOOKLM_AUTH_JSON": '{"cookies":[]}'},
            clear=False,
        ), patch.dict(sys.modules, {"notebooklm": raising_module}):
            payload = json.loads(
                call_handler(
                    {"question": "Router wifi?", "domains": ["BTTTT"]}
                )
            )
        rendered = json.dumps(payload)
        self.assertEqual(payload["error_type"], "notebooklm_upstream_error")
        self.assertIn("PermissionError", payload["error"])
        self.assertNotIn(RaisingNotebooks.LEAKED, rendered)

    def test_limit_per_domain_is_bounded(self):
        for requested, expected in ((99, 6), (0, 1)):
            with patch.dict(
                os.environ,
                {"NOTEBOOKLM_AUTH_JSON": '{"cookies":[]}'},
                clear=False,
            ), patch.dict(sys.modules, {"notebooklm": self._fake_module()}):
                payload = json.loads(
                    call_handler(
                        {
                            "question": "Router wifi?",
                            "domains": ["BTTTT"],
                            "limit_per_domain": requested,
                        }
                    )
                )
            self.assertEqual(payload["status"], "OK")
            self.assertEqual(
                FakeClient.last_instance.sources.search_calls[-1]["limit"],
                expected,
            )

    def test_more_than_three_domains_rejected(self):
        with patch.dict(
            os.environ,
            {"NOTEBOOKLM_AUTH_JSON": '{"cookies":[]}'},
            clear=False,
        ):
            payload = json.loads(
                call_handler(
                    {
                        "question": "mã HS?",
                        "domains": ["HS", "CHEMICAL", "BKHCN", "BTTTT"],
                    }
                )
            )
        self.assertEqual(payload["error_type"], "notebooklm_bad_request")

    def test_unknown_domain_rejected(self):
        with patch.dict(
            os.environ,
            {"NOTEBOOKLM_AUTH_JSON": '{"cookies":[]}'},
            clear=False,
        ):
            payload = json.loads(
                call_handler(
                    {"question": "mã HS?", "domains": ["FOO"]}
                )
            )
        self.assertEqual(payload["error_type"], "notebooklm_bad_request")


class ImageWiringTests(unittest.TestCase):
    def test_both_dockerfiles_pin_plugin_and_dependency(self):
        for relative in ("Dockerfile", "deployments/hermes-dockhosting/Dockerfile"):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(
                "plugins/notebooklm-knowledge/ /opt/hermes/plugins/notebooklm-knowledge/",
                text,
            )
            self.assertIn("NOTEBOOKLM_PY_VERSION=0.8.2", text)
            self.assertIn(
                '"notebooklm-py==${NOTEBOOKLM_PY_VERSION}"',
                text,
            )

    def test_bootstrap_is_secret_gated(self):
        for relative in (
            "deployments/hermes-dockhosting/p2p-post-bootstrap-main.sh",
            "deployments/hermes-dockhosting/dockhosting-entrypoint.sh",
        ):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('NOTEBOOKLM_AUTH_JSON:-', text)
            self.assertIn("plugins enable notebooklm-knowledge", text)

    def test_workflow_verifies_discovery_gates_inside_image(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "hermes-runtime-compatibility.yml"
        ).read_text(encoding="utf-8")
        # Fail-closed: without auth the toolset must not be exposed.
        self.assertIn("NOTEBOOKLM_HIDDEN_WITHOUT_AUTH=PASS", text)
        # With a dummy auth state the plugin must load and expose the tool.
        self.assertIn("NOTEBOOKLM_ENABLED_WITH_AUTH=PASS", text)


if __name__ == "__main__":
    unittest.main()
