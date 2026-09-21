from __future__ import annotations

import inspect
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
BRIDGE_PATH = SYSTEM_ROOT / "p2p_capabilities" / "web_reverse_reference.py"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.model import CANONICAL_IDENTITIES, load_registry  # noqa: E402
from p2p_capabilities import web_reverse_reference as bridge_module  # noqa: E402
from p2p_capabilities import reverse_skill_reference as reverse_module  # noqa: E402
from p2p_capabilities.web_reverse_reference import (  # noqa: E402
    DEFERRED_TRAFFIC_CANDIDATES,
    EXCLUDED_RUNTIME_BEHAVIORS,
    WebReverseReferenceError,
    web_reverse_reference_for,
    web_reverse_reference_ids,
)
from p2p_capabilities.routing import classify_capabilities  # noqa: E402
from p2p_capabilities.security_contract import (  # noqa: E402
    SECURITY_EXECUTION_CLASSES,
    authorize_security_execution,
)


# Fresh-verified 2026-09-21 upstream HEADs (Issue #224); re-verified via the
# GitHub API before this implementation and recorded exactly.
EXPECTED_PINS = {
    "web.browser.evidence": (
        "https://github.com/ChromeDevTools/chrome-devtools-mcp",
        "61780c7498a447771127d1fd3b2454fc4ae4ba28",
        "Apache-2.0",
    ),
    "web.js.reverse": (
        "https://github.com/vmoranv/jshookmcp",
        "33983e58cddc998af88a2ed46484364e5425cc86",
        "AGPL-3.0",
    ),
    "web.endpoint.discover": (
        "https://github.com/projectdiscovery/katana",
        "c1de26dbe69764a92dfa9a142eb64035e5d05a9d",
        "MIT",
    ),
    "web.public.reconstruct": (
        "https://github.com/xnl-h4ck3r/waymore",
        "4e02de512fd6b110be92dc8bffb3002edfebcb6c",
        "MIT",
    ),
}
EXPECTED_JSLUICE = (
    "https://github.com/BishopFox/jsluice",
    "0ddfab153e060a9eeaded4d8669233f7c071e7e4",
    "MIT",
)
EXPECTED_CEILINGS = {
    "web.browser.evidence": "ACTIVE_TEST_AUTHORIZED",
    "web.js.reverse": "ACTIVE_TEST_AUTHORIZED",
    "web.endpoint.discover": "ACTIVE_TEST_AUTHORIZED",
    "web.public.reconstruct": "ANALYSIS_LOCAL",
}

# One request per Volza-proven route; each must select exactly one new ID as
# PRIMARY through the sole existing P2P router, with no project label.
ROUTE_REQUESTS = {
    "web.browser.evidence": "Collect browser evidence and DOM evidence for this public site page",
    "web.js.reverse": "Use js reverse and javascript runtime trace to follow page behavior",
    "web.endpoint.discover": "Run web endpoint discovery and js endpoint enumeration for the scoped target",
    "web.public.reconstruct": "Perform archive reconstruction and historical url discovery from public sources",
}


class P2PWebReverseFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.registry_ids = set(cls.registry["identities"])
        cls.parsed = {item.capability_id: item for item in cls.registry["parsed"]}
        cls.raw = {
            item["CAPABILITY_ID"]: item
            for item in json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["capabilities"]
        }

    def route(self, request: str) -> dict:
        return classify_capabilities(request, self.registry["parsed"])

    # -- registry: SEC01 extension, canonical quorum unchanged ---------------

    def test_01_registry_valid_and_canonical_quorum_unchanged(self) -> None:
        self.assertTrue(self.registry["valid"])
        self.assertEqual(set(web_reverse_reference_ids()), set(EXPECTED_PINS))
        self.assertTrue(set(EXPECTED_PINS) <= self.registry_ids)
        self.assertEqual(tuple(self.registry["canonical_identities"]), CANONICAL_IDENTITIES)
        self.assertEqual(self.registry["canonical_denominator"], 8)
        self.assertEqual(self.registry["full_quorum"], "8/8")
        self.assertEqual(len(self.registry["identities"]), len(self.registry_ids))

    def test_02_new_ids_follow_sec01_registry_conventions(self) -> None:
        for capability_id in EXPECTED_PINS:
            with self.subTest(capability_id=capability_id):
                manifest = self.parsed[capability_id]
                self.assertEqual(manifest.type, "SKILL")
                self.assertEqual(manifest.semantic_kind, "TOOL")
                self.assertEqual(manifest.invocation_class, "MODEL_ROUTABLE")
                self.assertFalse(manifest.canonical_quorum_member)
                self.assertFalse(manifest.optional_specialist)
                self.assertEqual(manifest.status, "DISCOVERED")
                self.assertEqual(manifest.trust_level, "HOST_CODE")
                self.assertEqual(manifest.version, "web-reverse-foundation-1")
                self.assertIn("existing-p2p-router", manifest.authority)
                self.assertIn("existing-p2p-router", manifest.requires)
                self.assertIn("security-reverse-evidence-contract", manifest.requires)
                self.assertIn("p2p-security-reverse-foundation", manifest.context_pointers)

    # -- provenance: exact pins, licenses, disabled runtime -------------------

    def test_03_capability_provenance_is_exact_and_runtime_disabled(self) -> None:
        for capability_id, (repo, commit, license_kind) in EXPECTED_PINS.items():
            with self.subTest(capability_id=capability_id):
                provenance = self.raw[capability_id]["UPSTREAM_PROVENANCE"]
                self.assertEqual(provenance["upstream_repository"], repo)
                self.assertEqual(provenance["upstream_commit"], commit)
                self.assertEqual(provenance["license"], license_kind)
                self.assertEqual(provenance["install_mode"], "DISABLED")
                self.assertFalse(provenance["network_runtime"])
                self.assertFalse(provenance["credentials"])
                self.assertFalse(provenance["vendor_snapshot"])
                self.assertEqual(provenance["execution_status"], "NOT_EXECUTED")
                self.assertEqual(provenance["runtime_activation"], "DISABLED_IN_THIS_FOUNDATION")

    def test_04_agpl_boundary_and_subordinate_reference_are_explicit(self) -> None:
        js_provenance = self.raw["web.js.reverse"]["UPSTREAM_PROVENANCE"]
        self.assertEqual(js_provenance["mode"], "OPTIONAL_EXTERNAL_BACKEND_ONLY")
        self.assertIn("AGPL-3.0", js_provenance["license_boundary"])
        self.assertIn("no vendor snapshot", js_provenance["license_boundary"].lower())
        self.assertIn("agpl-external-only-no-vendor-no-link", self.raw["web.js.reverse"]["APPROVAL_BOUNDARY"])
        self.assertIn("vendor-or-link-agpl-backend", self.raw["web.js.reverse"]["PROHIBITED_ACTIONS"])

        subordinate = self.raw["web.endpoint.discover"]["UPSTREAM_PROVENANCE"]["subordinate_reference"]
        self.assertEqual(subordinate["repository"], EXPECTED_JSLUICE[0])
        self.assertEqual(subordinate["commit"], EXPECTED_JSLUICE[1])
        self.assertEqual(subordinate["license"], EXPECTED_JSLUICE[2])
        self.assertEqual(subordinate["role"], "SUBORDINATE_PARSER_REFERENCE_NOT_A_SEPARATE_P2P_AUTHORITY")

    def test_05_deferred_traffic_stacks_are_not_adopted(self) -> None:
        by_repo = {entry["repository"]: entry for entry in DEFERRED_TRAFFIC_CANDIDATES}
        self.assertEqual(
            by_repo["https://github.com/Mouseww/anything-analyzer"]["commit"],
            "1da6b5c9acc024e987d41e4b9c88676ffea0da0c",
        )
        self.assertEqual(by_repo["https://github.com/Mouseww/anything-analyzer"]["status"], "DEFERRED_NOT_ADOPTED")
        self.assertEqual(
            by_repo["https://github.com/Reqable/reqable-mcp-server"]["commit"],
            "2df174f982e9ab481a457ab96e065aac22829a51",
        )
        self.assertEqual(by_repo["https://github.com/Reqable/reqable-mcp-server"]["status"], "NOT_ADOPTED_LICENSE_UNRESOLVED")
        blob = json.dumps(self.raw)
        self.assertNotIn("anything-analyzer", blob)
        self.assertNotIn("reqable-mcp-server", blob)
        for capability_id in web_reverse_reference_ids():
            self.assertNotIn("anything-analyzer", json.dumps(web_reverse_reference_for(capability_id)["reference"]))
            self.assertNotIn("reqable-mcp-server", json.dumps(web_reverse_reference_for(capability_id)["reference"]))

    # -- routing: sole P2P router, distinct routes, no fake project label -----

    def test_06_single_router_selects_each_web_route_without_project_label(self) -> None:
        for capability_id, request in ROUTE_REQUESTS.items():
            with self.subTest(capability_id=capability_id):
                result = self.route(request)
                self.assertTrue(result["single_router"])
                self.assertNotIn("project:", request)
                by_id = {item["capability_id"]: item for item in result["results"]}
                self.assertEqual(by_id[capability_id]["classification"], "PRIMARY")
                self.assertIn(capability_id, result["selected"])
                self.assertFalse(by_id[capability_id]["collision"])
                others = [other for other in EXPECTED_PINS if other != capability_id]
                for other in others:
                    self.assertEqual(by_id[other]["classification"], "NOT_APPLICABLE")
                    self.assertNotIn(other, result["selected"])

    def test_07_first_line_deep_and_archive_routes_stay_distinguished(self) -> None:
        result = self.route("Collect browser evidence with archive reconstruction")
        by_id = {item["capability_id"]: item for item in result["results"]}
        for capability_id in EXPECTED_PINS:
            with self.subTest(capability_id=capability_id):
                # A mixed-route request must not silently pick one web route;
                # negative triggers keep the family fail-closed and explicit.
                self.assertEqual(by_id[capability_id]["classification"], "NOT_APPLICABLE")
                self.assertNotIn(capability_id, result["selected"])

    # -- bridge: post-route reference only, sole router, fail closed ----------

    def test_08_bridge_pins_licenses_ceilings_and_deny_flags(self) -> None:
        for capability_id, (repo, commit, license_kind) in EXPECTED_PINS.items():
            with self.subTest(capability_id=capability_id):
                result = web_reverse_reference_for(capability_id)
                self.assertEqual(result["capability_id"], capability_id)
                self.assertEqual(result["adoption_mode"], "PINNED_METHODOLOGY_REFERENCE_ONLY")
                self.assertEqual(result["p2p_router_authority"], "SOLE")
                self.assertEqual(result["upstream_router_authority"], "NONE")
                self.assertFalse(result["bootstrap_allowed"])
                self.assertFalse(result["auto_install_allowed"])
                self.assertFalse(result["mcp_registration_allowed"])
                self.assertFalse(result["network_runtime_allowed"])
                self.assertFalse(result["external_execution_authorized"])
                reference = result["reference"]
                self.assertEqual(reference["upstream_repository"], repo)
                self.assertEqual(reference["upstream_commit"], commit)
                self.assertEqual(reference["license"], license_kind)
                self.assertEqual(reference["execution_class_ceiling"], EXPECTED_CEILINGS[capability_id])
                self.assertIn(reference["execution_class_ceiling"], SECURITY_EXECUTION_CLASSES)
                self.assertIn("credential-or-authenticated-session-use", result["excluded_runtime_behaviors"])
                self.assertIn("mcp-auto-registration", result["excluded_runtime_behaviors"])
        self.assertIn("AGPL-3.0", web_reverse_reference_for("web.js.reverse")["reference"]["license_boundary"])
        subordinate = web_reverse_reference_for("web.endpoint.discover")["reference"]["subordinate_reference"]
        self.assertEqual(subordinate["commit"], EXPECTED_JSLUICE[1])
        self.assertTrue(set(EXCLUDED_RUNTIME_BEHAVIORS) >= {
            "tool-installation",
            "unscoped-live-target-interaction",
            "bypass-or-exploit-execution",
        })

    def test_09_bridge_is_disjoint_from_reverse_skill_and_not_a_router(self) -> None:
        self.assertTrue(set(web_reverse_reference_ids()).isdisjoint(reverse_module.reverse_skill_reference_ids()))
        # The Reverse-Skill pin is unchanged and current; this foundation
        # claims no drift and performs no re-pinning.
        self.assertEqual(reverse_module.REVERSE_SKILL_COMMIT, "7e2097fd90d25c2f976f6eba26d6c00aa88051df")
        source = inspect.getsource(bridge_module)
        for forbidden in (
            "classify_capabilities(",
            "validate_registry(",
            "load_registry(",
            "master-route",
            "task_text",
            "request:",
        ):
            self.assertNotIn(forbidden, source)

    def test_10_bridge_contains_no_execution_or_install_primitives(self) -> None:
        source = inspect.getsource(bridge_module).lower()
        for forbidden in (
            "subprocess.run(",
            "subprocess.popen(",
            "os.system(",
            "requests.get(",
            "urllib.request",
            "pip install",
            "npm install",
            "curl |",
            "invoke-webrequest",
        ):
            self.assertNotIn(forbidden, source)

    def test_11_unknown_capability_and_unauthorized_execution_fail_closed(self) -> None:
        with self.assertRaisesRegex(WebReverseReferenceError, "UNMAPPED_P2P_CAPABILITY"):
            web_reverse_reference_for("web.not-real")
        with self.assertRaisesRegex(WebReverseReferenceError, "UNMAPPED_P2P_CAPABILITY"):
            web_reverse_reference_for("reverse.identify")
        blocked = authorize_security_execution("ACTIVE_TEST_AUTHORIZED")
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertFalse(blocked["allowed"])
        self.assertTrue(blocked["fail_closed"])
        allowed = authorize_security_execution(
            "ACTIVE_TEST_AUTHORIZED",
            target_authorized=True,
            controlled_test_environment=True,
        )
        self.assertTrue(allowed["allowed"])
        # The bridge grants nothing: even ACTIVE-ceiling references deny
        # external execution; the existing SEC01 gate owns authorization.
        for capability_id in web_reverse_reference_ids():
            self.assertFalse(web_reverse_reference_for(capability_id)["external_execution_authorized"])

    # -- projection parity: install/project payloads follow the registry ------

    def test_12_install_and_project_projection_parity(self) -> None:
        self.assertTrue(BRIDGE_PATH.is_file())
        self.assertTrue(REGISTRY_PATH.is_file())
        install_sh = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        install_ps1 = (REPO_ROOT / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("p2p_capabilities/.", install_sh)
        self.assertIn("p2p_capabilities\\*", install_ps1)
        self.assertIn("p2p_capabilities/capabilities.json", install_sh)
        package_source = (REPO_ROOT / "scripts" / "package_release.py").read_text(encoding="utf-8")
        self.assertIn("shutil.copytree", package_source)
        self.assertIn('"p2p_capabilities"', package_source)
        self.assertIn("FOUNDATION_RUNTIME_FILES", package_source)


if __name__ == "__main__":
    unittest.main()
