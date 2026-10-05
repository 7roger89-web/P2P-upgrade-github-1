"""Focused tests for the bounded web/browser reverse evidence foundation.

Covers Issue #224 acceptance: one router/registry, first-line browser evidence
distinguished from deep JS reverse and public/archive reconstruction, exact and
license-aware upstream provenance, no auto-install / MCP registration / network
runtime / credential grant, fail-closed behaviour for unknown or unauthorized
lookups, unchanged canonical quorum, and installed-runtime projection parity.
Read-only: no browser, network, crawler, archive or MCP action is executed.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
PACKAGE_RELEASE = REPO_ROOT / "scripts" / "package_release.py"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import reverse_skill_reference as existing_bridge  # noqa: E402
from p2p_capabilities import web_reverse_reference as web  # noqa: E402
from p2p_capabilities.model import CANONICAL_IDENTITIES, load_registry  # noqa: E402
from p2p_capabilities.routing import classify_capabilities  # noqa: E402
from p2p_capabilities.security_contract import (  # noqa: E402
    ACTIVE_TEST_AUTHORIZED,
    ANALYSIS_LOCAL,
    SAFE_READONLY,
    SECURITY_EXECUTION_CLASSES,
    authorize_security_execution,
)

spec = importlib.util.spec_from_file_location("p2p_package_release", PACKAGE_RELEASE)
assert spec and spec.loader
package_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package_release)

NEW_IDS = (
    "web.browser.evidence",
    "web.js.reverse",
    "web.endpoint.discovery",
    "web.public.reconstruction",
)

# Exact pins verified fresh from upstream on 2026-09-21 (each equalled HEAD).
EXPECTED_PINS = {
    "https://github.com/ChromeDevTools/chrome-devtools-mcp": (
        "61780c7498a447771127d1fd3b2454fc4ae4ba28",
        "Apache-2.0",
    ),
    "https://github.com/vmoranv/jshookmcp": (
        "33983e58cddc998af88a2ed46484364e5425cc86",
        "AGPL-3.0",
    ),
    "https://github.com/projectdiscovery/katana": (
        "c1de26dbe69764a92dfa9a142eb64035e5d05a9d",
        "MIT",
    ),
    "https://github.com/BishopFox/jsluice": (
        "0ddfab153e060a9eeaded4d8669233f7c071e7e4",
        "MIT",
    ),
    "https://github.com/xnl-h4ck3r/waymore": (
        "4e02de512fd6b110be92dc8bffb3002edfebcb6c",
        "MIT",
    ),
    "https://github.com/Mouseww/anything-analyzer": (
        "1da6b5c9acc024e987d41e4b9c88676ffea0da0c",
        "Apache-2.0",
    ),
    "https://github.com/Reqable/reqable-mcp-server": (
        "2df174f982e9ab481a457ab96e065aac22829a51",
        "NO_SPDX",
    ),
}

EXISTING_SEC01_IDS = {
    "android.protection.detect",
    "android.artifact.decode",
    "security.mobile.static.assess",
    "android.runtime.instrument",
    "android.network.inspect",
    "reverse.identify",
    "reverse.decompile.managed",
    "reverse.decompile.native",
    "reverse.deobfuscate",
    "reverse.callgraph",
    "reverse.semantic_reconstruct",
}

VENDOR_MARKERS = (
    "chrome-devtools",
    "jshookmcp",
    "katana",
    "jsluice",
    "waymore",
    "anything-analyzer",
    "reqable",
)

BROWSER_EVIDENCE_REQUEST = (
    "Use first-line browser evidence on the public Volza site to decide whether the "
    "masked contact field is client-hidden or server-redacted, including the observed "
    "network request evidence."
)


class P2PWebReverseFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.registry_ids = set(cls.registry["identities"])
        cls.raw_entries = {
            item["CAPABILITY_ID"]: item
            for item in json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["capabilities"]
        }
        cls.manifests = {item.capability_id: item for item in cls.registry["parsed"]}

    def test_01_exact_pins_and_license_boundaries_are_license_aware(self) -> None:
        observed: dict[str, tuple[str, str]] = {}
        adopted = {
            candidate["repository"]: (candidate["commit"], candidate["license"])
            for candidate in (
                web.web_reverse_upstream_candidate(key)
                for key in (
                    "chrome-devtools-mcp",
                    "vmoranv-jshookmcp",
                    "projectdiscovery-katana",
                    "bishopfox-jsluice",
                    "xnl-h4ck3r-waymore",
                )
            )
        }
        non_adopted = {
            item["repository"]: (item["commit"], item["license"])
            for item in web.NON_ADOPTED_UPSTREAMS.values()
        }
        observed.update(adopted)
        observed.update(non_adopted)
        self.assertEqual(observed, EXPECTED_PINS)
        self.assertEqual(web.PIN_VERIFIED_AT, "2026-09-21")

        for repository, (_, license_kind) in EXPECTED_PINS.items():
            self.assertIn(license_kind, web.LICENSE_BOUNDARIES, repository)

        agpl = web.web_reverse_upstream_candidate("vmoranv-jshookmcp")
        self.assertEqual(agpl["license"], "AGPL-3.0")
        self.assertIn("COPYLEFT", agpl["license_boundary"])
        self.assertFalse(agpl["agpl_boundary"]["vendoring_allowed"])
        self.assertFalse(agpl["agpl_boundary"]["linking_allowed"])
        self.assertFalse(agpl["agpl_boundary"]["redistribution_with_p2p_allowed"])
        self.assertEqual(
            agpl["agpl_boundary"]["requirement_before_any_use"],
            "SEPARATE_OWNER_ACTIVATION_AND_AGPL_COMPLIANCE_REVIEW",
        )

        unresolved = web.NON_ADOPTED_UPSTREAMS["reqable-mcp-server"]
        self.assertEqual(unresolved["license"], "NO_SPDX")
        self.assertEqual(unresolved["reason_code"], "LICENSE_UNRESOLVED")
        self.assertIn("ADOPTION_PROHIBITED", web.LICENSE_BOUNDARIES["NO_SPDX"])

    def test_02_registry_gains_only_the_web_family_and_keeps_canonical_quorum(self) -> None:
        self.assertTrue(self.registry["valid"])
        # Historical exact-count assertions go stale whenever a later,
        # independently admitted capability is added.  The durable invariant
        # is registry self-consistency + uniqueness, while NEW_IDS below
        # preserves this test's web-family scope.
        self.assertEqual(
            self.registry["capability_count"],
            len(self.registry["identities"]),
        )
        self.assertTrue(set(NEW_IDS) <= self.registry_ids)
        self.assertTrue(EXISTING_SEC01_IDS <= self.registry_ids)
        self.assertEqual(tuple(self.registry["canonical_identities"]), CANONICAL_IDENTITIES)
        self.assertEqual(self.registry["canonical_denominator"], 8)
        self.assertEqual(self.registry["full_quorum"], "8/8")
        self.assertEqual(len(self.registry["identities"]), len(set(self.registry["identities"])))

        for capability_id in NEW_IDS:
            manifest = self.manifests[capability_id]
            self.assertEqual(manifest.type, "SKILL")
            self.assertFalse(manifest.canonical_quorum_member)
            self.assertFalse(manifest.optional_specialist)
            self.assertEqual(manifest.status, "DISCOVERED")
            self.assertEqual(manifest.invocation_class, "MODEL_ROUTABLE")
            self.assertIn("existing-p2p-router", manifest.requires)

    def test_03_existing_routes_are_reconciled_before_new_ids_are_added(self) -> None:
        reconciliation = web.EXISTING_ROUTE_RECONCILIATION
        self.assertTrue(set(reconciliation) <= self.registry_ids)
        self.assertTrue(EXISTING_SEC01_IDS <= set(reconciliation))
        for capability_id, record in reconciliation.items():
            with self.subTest(capability_id=capability_id):
                self.assertIn("existing_scope", record)
                self.assertIn("not_sufficient_for", record)
                self.assertNotIn(capability_id, NEW_IDS)

        # The existing Reverse-Skill bridge stays exactly as adopted: its pin is
        # current upstream HEAD, not stale, and no mapped ID was rewritten.
        self.assertEqual(existing_bridge.REVERSE_SKILL_COMMIT, web.EXISTING_REVERSE_SKILL_PIN)
        self.assertEqual(
            existing_bridge.REVERSE_SKILL_COMMIT,
            "7e2097fd90d25c2f976f6eba26d6c00aa88051df",
        )
        self.assertEqual(web.EXISTING_REVERSE_SKILL_PIN_STATUS, "CURRENT_UPSTREAM_HEAD_AT_VERIFICATION")
        self.assertEqual(web.EXISTING_REVERSE_SKILL_RECONCILIATION, "UNCHANGED_NO_DRIFT_CLAIMED")
        self.assertEqual(set(existing_bridge.reverse_skill_reference_ids()), EXISTING_SEC01_IDS)
        for capability_id in NEW_IDS:
            self.assertNotIn(capability_id, existing_bridge.reverse_skill_reference_ids())

    def test_04_registry_provenance_matches_the_bridge_pins(self) -> None:
        for capability_id in NEW_IDS:
            provenance = self.raw_entries[capability_id]["UPSTREAM_PROVENANCE"]
            with self.subTest(capability_id=capability_id):
                self.assertEqual(provenance["mode"], "PINNED_REFERENCE_RUNTIME_DISABLED")
                self.assertEqual(provenance["reference_contract"], web.WEB_REVERSE_REFERENCE_MODULE)
                self.assertEqual(provenance["pin_verified_at"], "2026-09-21")
                self.assertIs(provenance["pin_equals_upstream_head_at_verification"], True)
                self.assertEqual(provenance["install_mode"], "DISABLED")
                self.assertEqual(provenance["execution_status"], "NOT_EXECUTED")
                for flag in (
                    "auto_install",
                    "mcp_auto_registration",
                    "browser_runtime",
                    "network_runtime",
                    "credentials",
                    "vendor_snapshot",
                ):
                    self.assertIs(provenance[flag], False, f"{capability_id}:{flag}")
                candidate = EXPECTED_PINS[provenance["upstream_repository"]]
                self.assertEqual((provenance["upstream_commit"], provenance["license"]), candidate)
                self.assertIn(provenance["license"], web.LICENSE_BOUNDARIES)

    def test_05_single_router_expresses_the_route_without_a_fake_project_label(self) -> None:
        result = classify_capabilities(BROWSER_EVIDENCE_REQUEST, self.registry["parsed"])
        self.assertTrue(result["single_router"])
        self.assertIn("web.browser.evidence", result["selected"])
        browser = next(
            item for item in result["results"] if item["capability_id"] == "web.browser.evidence"
        )
        self.assertEqual(browser["classification"], "PRIMARY")
        self.assertFalse(browser["collision"])
        self.assertEqual(
            [item["capability_id"] for item in result["results"] if item["collision"]], []
        )
        self.assertNotIn("router-agent", json.dumps(result))
        self.assertEqual(result["adaptive_quorum"]["canonical_denominator"], 8)

        # No UI/specialist/project label is involved in selecting this route.
        from p2p_uiux.router import classify_request

        routed = classify_request(BROWSER_EVIDENCE_REQUEST)
        self.assertEqual(routed["scope"], "NON_UI")
        self.assertFalse(routed["use_skill"])
        self.assertFalse(routed["call_aesthetica"])
        self.assertTrue(routed["foundation"]["single_router"])
        self.assertIn("web.browser.evidence", routed["foundation"]["selected"])
        self.assertEqual(
            [item["capability_id"] for item in routed["foundation"]["results"] if item["classification"] == "PRIMARY"],
            ["web.browser.evidence"],
        )

    def test_06_browser_evidence_is_distinct_from_deeper_routes(self) -> None:
        cases = {
            "web.browser.evidence": BROWSER_EVIDENCE_REQUEST,
            "web.js.reverse": (
                "Perform javascript runtime tracing and client function tracing to find which "
                "client function produced the observed runtime value."
            ),
            "web.endpoint.discovery": (
                "Do endpoint discovery and client bundle endpoint discovery over the static "
                "asset scope to list the referenced endpoints."
            ),
            "web.public.reconstruction": (
                "Do public archive reconstruction and historical url discovery for that page, "
                "using archive index lookup only."
            ),
        }
        for expected, request in cases.items():
            with self.subTest(expected=expected):
                result = classify_capabilities(request, self.registry["parsed"])
                selected_web = sorted(set(result["selected"]) & set(NEW_IDS))
                self.assertEqual(selected_web, [expected])

        flow = web.WEB_REVERSE_FAMILY_FLOW
        self.assertEqual(flow, NEW_IDS)
        self.assertEqual(web.web_reverse_reference_ids(), NEW_IDS)
        self.assertEqual(
            web.web_reverse_reference_for("web.js.reverse")["reference"]["escalation_preconditions"],
            ("web.browser.evidence",),
        )
        self.assertEqual(
            web.web_reverse_reference_for("web.browser.evidence")["reference"]["family_position"], 1
        )
        self.assertEqual(
            web.web_reverse_reference_for("web.public.reconstruction")["reference"]["family_position"],
            4,
        )
        self.assertEqual(
            web.web_reverse_reference_for("web.public.reconstruction")["reference"]["truth_source"],
            "PUBLIC_ARCHIVE_INDEX_AND_SEARCH_SOURCES",
        )

    def test_07_live_target_work_is_never_declared_as_a_bounded_local_class(self) -> None:
        self.assertEqual(
            SECURITY_EXECUTION_CLASSES,
            (
                "SAFE_READONLY",
                "ANALYSIS_LOCAL",
                "ACTIVE_TEST_AUTHORIZED",
                "OFFENSIVE_HIGH_RISK",
                "DESTRUCTIVE_OR_INTRUSIVE",
            ),
        )
        for capability_id in NEW_IDS:
            reference = web.web_reverse_reference_for(capability_id)["reference"]
            with self.subTest(capability_id=capability_id):
                self.assertTrue(reference["external_interaction_possible"])
                self.assertEqual(reference["execution_class_ceiling"], ACTIVE_TEST_AUTHORIZED)
                self.assertIn(reference["execution_class_ceiling"], SECURITY_EXECUTION_CLASSES)
                self.assertEqual(reference["local_artifact_floor"], ANALYSIS_LOCAL)
                self.assertNotIn(reference["execution_class_ceiling"], web.BOUNDED_LOCAL_CLASSES)
                self.assertFalse(
                    web.execution_class_is_truthful(
                        SAFE_READONLY, external_interaction=reference["external_interaction_possible"]
                    )
                )
                self.assertFalse(
                    web.execution_class_is_truthful(
                        ANALYSIS_LOCAL, external_interaction=reference["external_interaction_possible"]
                    )
                )

            decision = authorize_security_execution(reference["execution_class_ceiling"])
            self.assertFalse(decision["allowed"])
            self.assertEqual(decision["status"], "BLOCKED")
            self.assertIn("TARGET_AUTHORIZATION_REQUIRED", decision["reason_codes"])
            self.assertTrue(decision["required"]["target_authorized"])
            self.assertTrue(decision["required"]["controlled_test_environment"])
            self.assertTrue(decision["fail_closed"])
            self.assertFalse(
                web.web_reverse_reference_for(capability_id)["external_execution_authorized"]
            )
            self.assertFalse(
                web.web_reverse_reference_for(capability_id)["network_runtime_allowed"]
            )

    def test_08_no_install_registration_network_or_credential_grant(self) -> None:
        for capability_id in NEW_IDS:
            reference = web.web_reverse_reference_for(capability_id)
            with self.subTest(capability_id=capability_id):
                self.assertFalse(reference["bootstrap_allowed"])
                self.assertFalse(reference["auto_install_allowed"])
                self.assertFalse(reference["mcp_registration_allowed"])
                self.assertFalse(reference["browser_runtime_allowed"])
                self.assertFalse(reference["network_runtime_allowed"])
                self.assertFalse(reference["credential_use_allowed"])
                self.assertFalse(reference["vendoring_allowed"])
                self.assertTrue(reference["activation_requires_separate_bounded_task"])
                self.assertEqual(reference["p2p_router_authority"], "SOLE")
                self.assertEqual(reference["upstream_router_authority"], "NONE")
                for candidate in reference["backend_candidates"]:
                    self.assertFalse(candidate["vendored"])
                    self.assertEqual(candidate["p2p_install"], "DISABLED")
                    self.assertEqual(candidate["p2p_runtime_activation"], "DISABLED")
                    self.assertEqual(candidate["mcp_registration"], "NOT_PERFORMED")
                    self.assertFalse(candidate["credentials"])

        prohibited = self.raw_entries["web.browser.evidence"]["PROHIBITED_ACTIONS"]
        for marker in ("auto-install-browser-or-runtime", "mcp-auto-registration", "credential-or-authenticated-session-use"):
            self.assertIn(marker, prohibited)

        source = Path(web.__file__).read_text(encoding="utf-8").lower()
        for forbidden in (
            "subprocess.run(",
            "subprocess.popen(",
            "os.system(",
            "requests.get(",
            "urllib.request",
            "pip install",
            "npm install",
            "npx ",
            "playwright",
            "puppeteer",
            "selenium",
            "webdriver",
            "mcp add",
            ".mcp.json",
            "invoke-webrequest",
        ):
            self.assertNotIn(forbidden, source)

    def test_09_unknown_and_non_adopted_lookups_fail_closed(self) -> None:
        with self.assertRaisesRegex(web.WebReverseReferenceError, "UNMAPPED_P2P_CAPABILITY"):
            web.web_reverse_reference_for("web.not-a-real-route")
        with self.assertRaisesRegex(web.WebReverseReferenceError, "UNMAPPED_P2P_CAPABILITY"):
            web.web_reverse_reference_for("")
        with self.assertRaisesRegex(web.WebReverseReferenceError, "NON_ADOPTED_UPSTREAM"):
            web.web_reverse_upstream_candidate("reqable-mcp-server")
        with self.assertRaisesRegex(web.WebReverseReferenceError, "UNKNOWN_UPSTREAM_CANDIDATE"):
            web.web_reverse_upstream_candidate("chrome-devtools-mcp-not-real")

        untruthful = {
            "web.browser.evidence": {
                "execution_class_ceiling": ANALYSIS_LOCAL,
                "external_interaction_possible": True,
                "backend_candidates": ("chrome-devtools-mcp",),
                "non_adopted_candidates": (),
            }
        }
        with self.assertRaisesRegex(web.WebReverseReferenceError, "UNTRUTHFUL_EXECUTION_CLASS"):
            web.validate_reference_declarations(untruthful)
        with self.assertRaisesRegex(web.WebReverseReferenceError, "UNKNOWN_BACKEND_CANDIDATE"):
            web.validate_reference_declarations(
                {
                    "web.browser.evidence": {
                        "execution_class_ceiling": ACTIVE_TEST_AUTHORIZED,
                        "external_interaction_possible": True,
                        "backend_candidates": ("unknown-candidate",),
                        "non_adopted_candidates": (),
                    }
                }
            )
        vendored = {
            "katana": {
                "license": "MIT",
                "vendored": True,
                "p2p_install": "DISABLED",
                "p2p_runtime_activation": "DISABLED",
            }
        }
        vendored_references = {
            "web.browser.evidence": {
                "execution_class_ceiling": ACTIVE_TEST_AUTHORIZED,
                "external_interaction_possible": True,
                "backend_candidates": ("katana",),
                "non_adopted_candidates": (),
            }
        }
        with self.assertRaisesRegex(web.WebReverseReferenceError, "CANDIDATE_MUST_STAY_DISABLED"):
            web.validate_reference_declarations(vendored_references, candidates=vendored)
        activated = {
            "katana": {
                "license": "MIT",
                "vendored": False,
                "p2p_install": "DISABLED",
                "p2p_runtime_activation": "ENABLED",
            }
        }
        with self.assertRaisesRegex(web.WebReverseReferenceError, "CANDIDATE_RUNTIME_MUST_STAY_DISABLED"):
            web.validate_reference_declarations(vendored_references, candidates=activated)
        with self.assertRaisesRegex(web.WebReverseReferenceError, "UNKNOWN_LICENSE_KIND"):
            web.validate_reference_declarations(
                vendored_references,
                candidates={
                    "katana": {
                        "license": "UNKNOWN-LICENSE",
                        "vendored": False,
                        "p2p_install": "DISABLED",
                        "p2p_runtime_activation": "DISABLED",
                    }
                },
            )

    def test_10_no_upstream_repository_is_vendored_or_submoduled(self) -> None:
        vendor_root = REPO_ROOT / ".p2p" / "vendor"
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path in vendor_root.rglob("*")
            if any(marker in path.name.lower() for marker in VENDOR_MARKERS)
        ]
        self.assertEqual(offenders, [])
        modules = (REPO_ROOT / ".gitmodules").read_text(encoding="utf-8").lower()
        for marker in VENDOR_MARKERS:
            self.assertNotIn(marker, modules)

    def test_11_installed_runtime_projection_keeps_parity(self) -> None:
        self.assertIn("p2p_capabilities/capabilities.json", package_release.FOUNDATION_RUNTIME_FILES)
        self.assertIn("web_reverse_reference.py", package_release.FOUNDATION_RUNTIME_MODULES)

        source_registry = REGISTRY_PATH.read_bytes()
        source_module = (SYSTEM_ROOT / "p2p_capabilities" / "web_reverse_reference.py").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp) / "stage"
            stage.mkdir()
            package_release.copy_foundation_runtime(REPO_ROOT, stage)
            projected = stage / "runtime" / "p2p_capabilities"
            self.assertEqual((projected / "capabilities.json").read_bytes(), source_registry)
            self.assertEqual((projected / "web_reverse_reference.py").read_bytes(), source_module)
            projected_registry = load_registry(projected / "capabilities.json")
            self.assertEqual(projected_registry["identities"], self.registry["identities"])
            self.assertEqual(projected_registry["canonical_identities"], list(CANONICAL_IDENTITIES))
            self.assertEqual(projected_registry["full_quorum"], "8/8")
            self.assertTrue(set(NEW_IDS) <= set(projected_registry["identities"]))

    def test_12_bridge_is_post_route_only_and_contains_no_classifier(self) -> None:
        source = Path(web.__file__).read_text(encoding="utf-8")
        self.assertNotIn("classify_capabilities(", source)
        self.assertNotIn("task_text", source)
        self.assertNotIn("master-route", source.lower())
        self.assertNotIn("from .routing import", source)
        self.assertNotIn("p2p_uiux", source)
        router_source = (SYSTEM_ROOT / "p2p_uiux" / "router.py").read_text(encoding="utf-8")
        self.assertNotIn("web_reverse_reference", router_source)


if __name__ == "__main__":
    unittest.main()
