"""P2P-IMPECCABLE-01 (issue #44) focused proof.

Scope is deliberately narrow:
  - capability projection / registry record
  - routing eligibility through the EXISTING router
  - no default context loading, no global activation
  - deterministic detector proof on one bounded fixture pair
  - provenance / license boundary of the pinned vendor snapshot
  - non-regression of the existing UI capability catalog + profile routing
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
VENDOR_ROOT = REPO_ROOT / ".p2p" / "vendor" / "skill" / "pbakaus-impeccable-94b7f34"
PROVENANCE_PATH = REPO_ROOT / ".p2p" / "vendor" / "provenance" / "p2p-impeccable-01.json"
CATALOG_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "ui-game-threejs" / "capability-catalog.json"
ROUTING_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "ui-game-threejs" / "project-profile-routing.json"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "p2p-impeccable-design-quality"
BEFORE = FIXTURE_DIR / "before.html"
AFTER = FIXTURE_DIR / "after.html"

CAPABILITY_ID = "ui.design_quality"
UPSTREAM_COMMIT = "94b7f34f6e27b95bc32d8284a671601ed6ac1b2a"
UPSTREAM_TREE = "604c0d2d5f0c1c6bd1f3bd1cbc06bef637e24139"

# Deterministic categories that must be found on the BEFORE fixture in EVERY
# engine mode, including the zero-dependency regex mode.
REQUIRED_ANTIPATTERNS = {
    "gradient-text",        # generic/undesired gradient pattern
    "side-tab",             # generic AI accent-stripe card pattern
    "dark-glow",            # decorative chromatic glow
    "monotonous-spacing",   # spacing rhythm problem
    "flat-type-hierarchy",  # typography hierarchy problem
    "overused-font",        # typography/readability problem
}

sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import impeccable_design_quality as idq  # noqa: E402
from p2p_capabilities.model import load_registry  # noqa: E402
from p2p_capabilities.vendor_skill import (  # noqa: E402
    discover_vendor_skills,
    is_vendor_skill,
    load_vendor_skill,
    snapshot_tree_sha256,
)


def _registry_entry() -> dict:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return next(item for item in raw["capabilities"] if item["CAPABILITY_ID"] == CAPABILITY_ID)


def _route(request: str) -> dict:
    return discover_vendor_skills(request, registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)


def _classification(request: str) -> str:
    route = _route(request)
    result = next(
        item for item in route["route"]["results"] if item["capability_id"] == CAPABILITY_ID
    )
    return result["classification"]


class RegistryProjectionTests(unittest.TestCase):
    def test_record_is_noncanonical_discovered_vendor_skill(self) -> None:
        entry = _registry_entry()
        self.assertEqual(entry["TYPE"], "SKILL")
        self.assertEqual(entry["STATUS"], "DISCOVERED")
        self.assertEqual(entry["INVOCATION_CLASS"], "MODEL_ROUTABLE")
        self.assertFalse(entry["CANONICAL_QUORUM_MEMBER"])
        self.assertFalse(entry["OPTIONAL_SPECIALIST"])
        manifest = next(
            item for item in load_registry(REGISTRY_PATH)["parsed"] if item.capability_id == CAPABILITY_ID
        )
        self.assertTrue(is_vendor_skill(manifest))

    def test_projection_is_bounded_and_advisory(self) -> None:
        projection = _registry_entry()["UPSTREAM_PROVENANCE"]["capability_projection"]
        self.assertEqual(len(projection["projected_actions"]), 7)
        self.assertEqual(projection["executable_actions"], ["ui.design_quality.deterministic_check"])
        self.assertEqual(tuple(projection["projected_actions"]), idq.PROJECTED_ACTIONS)
        self.assertEqual(projection["law"], "AVAILABLE != LOADED != AUTHORIZED != EXECUTED")
        # Projection must be a strict subset of the discovered upstream surface.
        self.assertLess(len(projection["projected_actions"]), projection["upstream_commands_discovered"])
        self.assertNotIn("init", projection["projected_actions"])
        self.assertIn("live", projection["not_projected"])

    def test_no_global_activation_or_default_loading(self) -> None:
        entry = _registry_entry()
        integration = entry["UPSTREAM_PROVENANCE"]["integration"]
        self.assertEqual(integration["load_mode"], "ON_DEMAND")
        self.assertEqual(integration["install_mode"], "DISABLED")
        self.assertFalse(integration["network_runtime"])
        self.assertFalse(integration["credentials"])
        self.assertFalse(integration["browser_runtime"])
        self.assertFalse(integration["model_required"])
        for prohibition in ("default-context-loading", "global-activation", "own-implementation-decisions"):
            self.assertIn(prohibition, entry["PROHIBITED_ACTIONS"])

    def test_availability_is_metadata_only(self) -> None:
        report = idq.availability(registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)
        self.assertTrue(report["available"])
        self.assertFalse(report["content_loaded"])
        self.assertFalse(report["authorized"])
        self.assertFalse(report["executed"])
        self.assertFalse(report["default_context_loading"])
        self.assertFalse(report["global_activation"])


class RoutingEligibilityTests(unittest.TestCase):
    def test_design_quality_request_is_eligible(self) -> None:
        route = _route("Run a design critique on the settings screen and flag any anti-patterns.")
        self.assertIn(CAPABILITY_ID, route["route"]["selected"])
        self.assertNotEqual(
            _classification("Run a design critique on the settings screen and flag any anti-patterns."),
            "NOT_APPLICABLE",
        )

    def test_unrelated_requests_do_not_route(self) -> None:
        for request in (
            "Explain how to choose a PostgreSQL index.",
            "Implement the cultivation game UI in code.",
            "Design a cultivation game UI image prompt.",
            "Create a whiteboard animation from an SRT and render an MP4",
            "Write an advertising slogan and campaign headline for a new brand.",
        ):
            with self.subTest(request=request):
                self.assertEqual(_classification(request), "NOT_APPLICABLE")
                self.assertNotIn(CAPABILITY_ID, _route(request)["selected"])

    def test_discovery_never_loads_vendor_content(self) -> None:
        route = _route("design critique for the dashboard")
        self.assertFalse(route["content_loaded"])
        self.assertFalse(route["permission_grant"])
        for skill in route["skills"]:
            self.assertFalse(skill["content_loaded"])

    def test_explicit_load_is_separate_from_routing(self) -> None:
        loaded = load_vendor_skill(
            CAPABILITY_ID,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
            references=["skills/impeccable/reference/critique.md"],
        )
        self.assertTrue(loaded["content_loaded"])
        self.assertFalse(loaded["permission_grant"])
        self.assertFalse(loaded["network_used"])
        self.assertEqual(
            sorted(loaded["loaded_paths"]),
            ["skills/impeccable/SKILL.md", "skills/impeccable/reference/critique.md"],
        )


class AuthorizationLawTests(unittest.TestCase):
    def test_execution_requires_authorization(self) -> None:
        with self.assertRaises(idq.DesignQualityError):
            idq.deterministic_check([BEFORE], authorization={}, repository_root=REPO_ROOT, registry_path=REGISTRY_PATH)

    def test_advisory_action_cannot_execute(self) -> None:
        grant = idq.authorize(
            "ui.design_quality.critique",
            granted_by="P2P-IMPECCABLE-01-test",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertTrue(grant["advisory_only"])
        with self.assertRaises(idq.DesignQualityError):
            idq.deterministic_check([BEFORE], authorization=grant, repository_root=REPO_ROOT, registry_path=REGISTRY_PATH)

    def test_unknown_action_is_rejected(self) -> None:
        with self.assertRaises(idq.DesignQualityError):
            idq.authorize(
                "ui.design_quality.redesign_everything",
                granted_by="P2P-IMPECCABLE-01-test",
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            )

    def test_authorization_binds_verified_snapshot(self) -> None:
        grant = idq.authorize(
            "ui.design_quality.deterministic_check",
            granted_by="P2P-IMPECCABLE-01-test",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertTrue(grant["authorized"])
        self.assertFalse(grant["executed"])
        self.assertEqual(grant["upstream_commit"], UPSTREAM_COMMIT)
        self.assertEqual(grant["snapshot_sha256"], snapshot_tree_sha256(VENDOR_ROOT))
        self.assertEqual(grant["implementation_authority"], "P2P")


class DeterministicDetectorProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.grant = idq.authorize(
            "ui.design_quality.deterministic_check",
            granted_by="P2P-IMPECCABLE-01-test",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )

    def check(self, target: Path) -> dict:
        return idq.deterministic_check(
            [target],
            authorization=self.grant,
            repository_root=REPO_ROOT,
            registry_path=REGISTRY_PATH,
        )

    def test_before_fixture_reports_required_categories(self) -> None:
        report = self.check(BEFORE)
        if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(report["status"], "COMPLETED")
        found = set(report["antipattern_counts"])
        self.assertTrue(
            REQUIRED_ANTIPATTERNS.issubset(found),
            f"missing deterministic categories: {sorted(REQUIRED_ANTIPATTERNS - found)}",
        )
        self.assertGreaterEqual(report["finding_count"], len(REQUIRED_ANTIPATTERNS))

    def test_no_model_network_or_browser_is_used(self) -> None:
        report = self.check(BEFORE)
        if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertFalse(report["model_used"])
        self.assertFalse(report["network_used"])
        self.assertFalse(report["browser_used"])
        self.assertFalse(report["source_mutation"])
        self.assertIn(report["engine_mode"], {"REGEX_DEGRADED", "STATIC_HTML_FULL"})

    def test_findings_are_stable_across_repeat_runs(self) -> None:
        first = self.check(BEFORE)
        second = self.check(BEFORE)
        if first.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(first["engine_mode"], second["engine_mode"])
        self.assertEqual(first["findings"], second["findings"])
        self.assertEqual(
            hashlib.sha256(json.dumps(first["findings"], sort_keys=True).encode()).hexdigest(),
            hashlib.sha256(json.dumps(second["findings"], sort_keys=True).encode()).hexdigest(),
        )

    def test_minimum_correction_clears_the_findings(self) -> None:
        before = self.check(BEFORE)
        after = self.check(AFTER)
        if before.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(after["finding_count"], 0)
        delta = idq.diff_reports(before, after)
        self.assertEqual(delta["after_finding_count"], 0)
        self.assertEqual(delta["introduced_antipatterns"], [])
        self.assertTrue(REQUIRED_ANTIPATTERNS.issubset(set(delta["resolved_antipatterns"])))

    def test_targets_outside_the_repository_are_refused(self) -> None:
        with self.assertRaises(idq.DesignQualityError):
            idq.deterministic_check(
                [Path("/etc/hosts")],
                authorization=self.grant,
                repository_root=REPO_ROOT,
                registry_path=REGISTRY_PATH,
            )


class ProvenanceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
        cls.vendor = cls.record["vendors"][0]

    def test_upstream_pin_and_license_are_recorded(self) -> None:
        self.assertEqual(self.vendor["upstream_commit"], UPSTREAM_COMMIT)
        self.assertEqual(self.vendor["upstream_tree"], UPSTREAM_TREE)
        self.assertEqual(self.vendor["root_license"], "Apache-2.0")
        self.assertTrue((VENDOR_ROOT / "LICENSE").is_file())
        self.assertTrue((VENDOR_ROOT / "NOTICE.md").is_file())
        self.assertIn("Apache License", (VENDOR_ROOT / "LICENSE").read_text(encoding="utf-8")[:200])

    def test_every_vendored_file_is_hashed_and_unmodified(self) -> None:
        declared = {item["snapshot_path"]: item for item in self.vendor["files"]}
        present = {
            path.relative_to(REPO_ROOT).as_posix()
            for path in VENDOR_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(set(declared), present)
        self.assertEqual(len(present), self.vendor["snapshot_file_count"])
        for relative, item in declared.items():
            with self.subTest(file=relative):
                digest = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
                self.assertEqual(digest, item["sha256"])
                self.assertEqual(item["modification_status"], "UNMODIFIED")
                self.assertEqual(item["license"], "Apache-2.0")

    def test_snapshot_hash_matches_registry(self) -> None:
        entry = _registry_entry()["UPSTREAM_PROVENANCE"]
        self.assertEqual(entry["snapshot_sha256"], snapshot_tree_sha256(VENDOR_ROOT))
        self.assertEqual(entry["snapshot_sha256"], self.vendor["snapshot_sha256"])

    def test_no_runtime_cache_or_live_session_surface_was_imported(self) -> None:
        forbidden_names = {"package.json", "bun.lock", "skills-lock.json", "detect-antipatterns-browser.js"}
        forbidden_parts = {"node_modules", ".impeccable", "extension", "demos", "cli", "hooks", "live"}
        for path in VENDOR_ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(VENDOR_ROOT)
            self.assertNotIn(path.name, forbidden_names)
            self.assertFalse(forbidden_parts & set(relative.parts), f"forbidden surface: {relative}")
            self.assertNotIn("live-", path.name)


class CatalogNonRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.routing = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))

    def test_candidate_is_registered_without_global_install(self) -> None:
        candidate = next(c for c in self.catalog["candidates"] if c["candidate_id"] == "CAND-GAME-UI-019")
        self.assertFalse(candidate["global_install"])
        self.assertEqual(candidate["license"], "Apache-2.0")
        self.assertEqual(candidate["classification"], "CONDITIONAL")
        self.assertIn("ui.design_quality", candidate["capability_domains"])
        self.assertIn("ui.design_quality", self.catalog["domains"])
        self.assertIn(UPSTREAM_COMMIT, candidate["source_version_or_commit"])

    def test_design_quality_is_optional_in_every_profile(self) -> None:
        for name, profile in self.routing["profiles"].items():
            with self.subTest(profile=name):
                self.assertIn("ui.design_quality", profile["optional_capabilities"])
                self.assertNotIn("ui.design_quality", profile["required_capabilities"])
                self.assertNotIn("ui.design_quality", profile["excluded_capabilities"])

    def test_existing_profile_requirements_are_unchanged(self) -> None:
        expected = {
            "WEB_APP": ["ui.design", "ui.frontend"],
            "MOBILE_APP": ["ui.design", "ui.frontend"],
            "2D_GAME": ["ui.game_hud", "ui.design"],
            "THREEJS_GAME": ["game.three.visual", "game.three.asset", "ui.game_hud"],
            "R3F_GAME": ["game.three.visual", "game.three.asset", "ui.game_hud"],
        }
        for name, required in expected.items():
            with self.subTest(profile=name):
                self.assertEqual(self.routing["profiles"][name]["required_capabilities"], required)

    def test_review_authority_invariant_is_declared(self) -> None:
        invariants = " ".join(self.routing["projection_invariants"])
        self.assertIn("DESIGN_REVIEW_AUTHORITY != IMPLEMENTATION_AUTHORITY", invariants)
        self.assertIn("AVAILABLE != LOADED != AUTHORIZED != EXECUTED", invariants)


if __name__ == "__main__":
    unittest.main()
