"""Focused non-secret tests for NotebookLM -> VNLAW cross-check."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import pathlib
import sys
import unittest
from unittest.mock import patch
import urllib.error

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
        "hermes_test_notebooklm_vnlaw",
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PLUGIN = load_plugin()
BRIDGE = PLUGIN.tools._vnlaw_bridge


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self._raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=-1):
        return self._raw if limit < 0 else self._raw[:limit]


class CrossCheckTests(unittest.TestCase):
    def _env(self):
        return {
            "VNLAW_API_TOKEN": "test-token-not-secret",
            "VNLAW_API_URL": "https://vnlaw.example.test",
        }

    def test_verified_query_contract_and_projection(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["authorization"] = request.get_header("Authorization")
            captured["timeout"] = timeout
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse(
                {
                    "query": "router wifi",
                    "as_of_date": "2026-09-24",
                    "top_k": 5,
                    "legal_hits": [
                        {
                            "authority_tier": "VERIFIED_LEGAL_AUTHORITY",
                            "rank": 1,
                            "score": 1.0,
                            "matched_terms": ["router"],
                            "dossier_anchor": "doc#1",
                            "chunk": {
                                "document_number": "02/2024/TT-BTTTT",
                                "provision_id": "p1",
                                "version_id": "v1",
                                "breadcrumb": "Phụ lục",
                                "text": "Nội dung pháp lý đã xác minh",
                                "force": "in_force",
                                "valid_from": "2024-05-15",
                                "valid_to": None,
                                "source_url": "https://example.gov.vn/doc",
                                "source_locator": "Phụ lục I",
                            },
                        }
                    ],
                    "technical_hits": [],
                    "guidance_hits": [],
                    "dossier_anchors": ["doc#1"],
                }
            )

        with patch.dict(os.environ, self._env(), clear=False), patch.object(
            BRIDGE.urllib.request, "urlopen", fake_urlopen
        ):
            result = asyncio.run(
                BRIDGE.cross_check(
                    "Router WiFi công nghiệp",
                    as_of_date="2026-09-24",
                    source_titles=["02_2024_TT-BTTTT.docx"],
                )
            )

        self.assertEqual(result["status"], "VERIFIED_EVIDENCE_FOUND")
        self.assertTrue(result["verified_authority_evidence"])
        self.assertEqual(captured["url"], "https://vnlaw.example.test/verified-query")
        self.assertEqual(captured["authorization"], "Bearer test-token-not-secret")
        self.assertEqual(captured["timeout"], 15)
        self.assertEqual(captured["body"]["scope"], "verified")
        self.assertEqual(captured["body"]["as_of_date"], "2026-09-24")
        self.assertIn("02_2024_TT-BTTTT.docx", captured["body"]["query"])
        self.assertEqual(
            result["legal_hits"][0]["document_number"],
            "02/2024/TT-BTTTT",
        )
        self.assertNotIn("test-token-not-secret", json.dumps(result))

    def test_zero_hits_is_not_a_negative_legal_conclusion(self):
        def fake_urlopen(request, timeout):
            return FakeResponse(
                {
                    "query": "unknown",
                    "as_of_date": "2026-09-24",
                    "top_k": 5,
                    "legal_hits": [],
                    "technical_hits": [],
                    "guidance_hits": [],
                    "dossier_anchors": [],
                }
            )

        with patch.dict(os.environ, self._env(), clear=False), patch.object(
            BRIDGE.urllib.request, "urlopen", fake_urlopen
        ):
            result = asyncio.run(
                BRIDGE.cross_check("unknown", as_of_date="2026-09-24")
            )

        self.assertEqual(result["status"], "NO_VERIFIED_EVIDENCE")
        self.assertFalse(result["verified_authority_evidence"])
        self.assertIn("not 'legally false'", result["scope_notice"])

    def test_missing_token_is_bounded_config_status(self):
        with patch.dict(os.environ, {}, clear=True):
            result = asyncio.run(
                BRIDGE.cross_check("router", as_of_date="2026-09-24")
            )
        self.assertEqual(result["status"], "CONFIG_MISSING")
        self.assertFalse(result["verified_authority_evidence"])

    def test_unauthorized_is_sanitized_service_error(self):
        def fake_urlopen(request, timeout):
            raise urllib.error.HTTPError(
                request.full_url,
                401,
                "Unauthorized",
                hdrs=None,
                fp=None,
            )

        with patch.dict(os.environ, self._env(), clear=False), patch.object(
            BRIDGE.urllib.request, "urlopen", fake_urlopen
        ):
            result = asyncio.run(
                BRIDGE.cross_check("router", as_of_date="2026-09-24")
            )
        rendered = json.dumps(result)
        self.assertEqual(result["status"], "SERVICE_ERROR")
        self.assertIn("authentication failed", result["error"])
        self.assertNotIn("test-token-not-secret", rendered)

    def test_non_https_url_fails_closed(self):
        with patch.dict(
            os.environ,
            {
                "VNLAW_API_TOKEN": "test-token-not-secret",
                "VNLAW_API_URL": "http://unsafe.example.test",
            },
            clear=False,
        ):
            result = asyncio.run(
                BRIDGE.cross_check("router", as_of_date="2026-09-24")
            )
        self.assertEqual(result["status"], "CONFIG_MISSING")
        self.assertIn("HTTPS", result["error"])


class GroundingContractTests(unittest.TestCase):
    def test_prompt_requires_separate_vnlaw_rendering(self):
        class FakeCtx:
            def __init__(self):
                self.sections = []

            def register_tool(self, **_spec):
                pass

            def register_system_prompt_section(self, *args, **kwargs):
                self.sections.append((args, kwargs))

        ctx = FakeCtx()
        PLUGIN.register(ctx)
        rendered = ctx.sections[0][0][1]()
        self.assertIn("vnlaw_cross_check", rendered)
        self.assertIn("VNLAW xác minh", rendered)
        self.assertIn("NO_VERIFIED_EVIDENCE", rendered)
        self.assertIn("Never interpret no VNLAW hit", rendered)


if __name__ == "__main__":
    unittest.main()
