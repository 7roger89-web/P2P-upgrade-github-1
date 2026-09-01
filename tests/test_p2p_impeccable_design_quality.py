"""P2P-IMPECCABLE-01 (issue #44) focused proof.

Scope is deliberately narrow:
  - capability projection / registry record
  - routing eligibility through the EXISTING router
  - no default context loading, no global activation
  - the real risk surface of a READ_ONLY_LOCAL_DETERMINISTIC_CHECK:
    explicit repository-local targets and pinned vendor artifact identity,
    re-proved immediately before the subprocess is launched
  - deterministic detector proof on one bounded fixture pair
  - provenance / license boundary of the pinned vendor snapshot
  - non-regression of the existing UI capability catalog + profile routing

This capability makes no runtime permission-authority claim, so nothing here
tries to prove one.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

VENDOR_RELATIVE = VENDOR_ROOT.relative_to(REPO_ROOT)
DRIFT_TARGET = (
    VENDOR_RELATIVE / "skills" / "impeccable" / "scripts" / "detector" / "registry" / "antipatterns.mjs"
)


def _registry_entry() -> dict:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return next(item for item in raw["capabilities"] if item["CAPABILITY_ID"] == CAPABILITY_ID)


def _mirror_repository(destination: Path) -> Path:
    """Copy only what the adapter needs into a throwaway root.

    Vendor-drift proofs run against this mirror; canonical vendored source is
    never mutated by the test suite.
    """

    for relative in (
        ".p2p/system/p2p_capabilities/capabilities.json",
        ".p2p/system/p2p_capabilities/impeccable_detector_runner.mjs",
        "tests/fixtures/p2p-impeccable-design-quality/before.html",
        "tests/fixtures/p2p-impeccable-design-quality/after.html",
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)
    shutil.copytree(VENDOR_ROOT, destination / VENDOR_RELATIVE)
    return destination


def _mutate_vendor(root: Path) -> None:
    drifted = root / DRIFT_TARGET
    drifted.write_text(
        drifted.read_text(encoding="utf-8") + "\n// injected before launch\n", encoding="utf-8"
    )


def _route(request: str) -> dict:
    return discover_vendor_skills(request, registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)


def _classification(request: str) -> str:
    route = _route(request)
    result = next(
        item for item in route["route"]["results"] if item["capability_id"] == CAPABILITY_ID
    )
    return result["classification"]


def _check(target, root=REPO_ROOT, registry=REGISTRY_PATH, **kwargs) -> dict:
    return idq.deterministic_check(
        [target], repository_root=root, registry_path=registry, **kwargs
    )


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
        self.assertEqual(projection["law"], "AVAILABLE != LOADED != SELECTED != EXECUTED")
        self.assertEqual(projection["execution_class"], "READ_ONLY_LOCAL_DETERMINISTIC_CHECK")
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
        self.assertFalse(report["selected"])
        self.assertEqual(report["execution_class"], "READ_ONLY_LOCAL_DETERMINISTIC_CHECK")
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


class ReadOnlyExecutionBoundaryTests(unittest.TestCase):
    """The real risk surface of a read-only local deterministic check.

    There is no permission model to prove here: the capability claims none.
    What must hold is explicit targets, repository-local targets, and pinned
    vendor artifact identity that is still true at the moment of launch.
    """

    def test_execution_model_is_declared_truthfully(self) -> None:
        self.assertEqual(idq.EXECUTION_CLASS, "READ_ONLY_LOCAL_DETERMINISTIC_CHECK")
        self.assertEqual(idq.RUNTIME_PERMISSION_AUTHORITY_CLAIM, "NONE")
        selection = idq.select_action(
            "ui.design_quality.deterministic_check",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertTrue(selection["selected"])
        self.assertFalse(selection["executed"])
        self.assertEqual(selection["runtime_permission_authority_claim"], "NONE")
        self.assertFalse(selection["owner_gate_required_for_read_only_check"])
        self.assertTrue(selection["owner_gate_required_for_promotion"])
        # No grant, token, fingerprint or authority metadata is emitted.
        for forbidden in ("request", "request_fingerprint", "granted_by", "authority_surface",
                          "permission_binding", "permission_authority_surface", "authorized"):
            self.assertNotIn(forbidden, selection)

    def test_adapter_declares_no_authority_surface(self) -> None:
        source = Path(idq.__file__).read_text(encoding="utf-8")
        for forbidden in ("TaskStateStore", "evaluate_task_preflight", "_ISSUED_GRANTS",
                          "PortableExecutionRequest", "granted_permissions", "permission_binding"):
            self.assertNotIn(forbidden, source, f"rejected machinery still present: {forbidden}")

    # --- A: no targets ------------------------------------------------------
    def test_a_no_targets_fails_closed(self) -> None:
        with mock.patch.object(idq.subprocess, "run") as spawned:
            with self.assertRaises(idq.DesignQualityError) as caught:
                idq.deterministic_check([], repository_root=REPO_ROOT, registry_path=REGISTRY_PATH)
            spawned.assert_not_called()
        self.assertEqual(str(caught.exception), "NO_TARGET_SUPPLIED")

    # --- B: target outside the repository -----------------------------------
    def test_b_target_outside_repository_fails_closed(self) -> None:
        for target in (Path("/etc/hosts"), Path("../../etc/hosts")):
            with self.subTest(target=str(target)):
                with mock.patch.object(idq.subprocess, "run") as spawned:
                    with self.assertRaises(idq.DesignQualityError) as caught:
                        _check(target)
                    spawned.assert_not_called()
                self.assertIn(
                    str(caught.exception), {"TARGET_OUTSIDE_REPOSITORY", "TARGET_NOT_A_FILE"}
                )

    def test_b2_directory_target_is_not_a_filesystem_crawl(self) -> None:
        with mock.patch.object(idq.subprocess, "run") as spawned:
            with self.assertRaises(idq.DesignQualityError) as caught:
                _check(FIXTURE_DIR)
            spawned.assert_not_called()
        self.assertEqual(str(caught.exception), "TARGET_NOT_A_FILE")

    def test_b3_advisory_action_cannot_execute(self) -> None:
        selection = idq.select_action(
            "ui.design_quality.critique", registry_path=REGISTRY_PATH, repository_root=REPO_ROOT
        )
        self.assertTrue(selection["advisory_only"])
        with mock.patch.object(idq.subprocess, "run") as spawned:
            with self.assertRaises(idq.DesignQualityError) as caught:
                _check(BEFORE, selection=selection)
            spawned.assert_not_called()
        self.assertEqual(str(caught.exception), "ACTION_NOT_EXECUTABLE")

    # --- C: vendor snapshot changed before execution ------------------------
    def test_c_vendor_drift_before_execution_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror = _mirror_repository(Path(raw).resolve())
            registry = mirror / ".p2p/system/p2p_capabilities/capabilities.json"
            target = mirror / "tests/fixtures/p2p-impeccable-design-quality/before.html"
            _mutate_vendor(mirror)
            with mock.patch.object(idq.subprocess, "run") as spawned:
                with self.assertRaises(idq.DesignQualityVendorIdentityError) as caught:
                    _check(target, root=mirror, registry=registry)
                spawned.assert_not_called()
            self.assertEqual(str(caught.exception), "VENDOR_SNAPSHOT_HASH_MISMATCH")

        # Canonical vendored source is untouched by this proof.
        self.assertEqual(
            _registry_entry()["UPSTREAM_PROVENANCE"]["snapshot_sha256"],
            snapshot_tree_sha256(VENDOR_ROOT),
        )

    def test_c2_vendor_snapshot_removed_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror = _mirror_repository(Path(raw).resolve())
            registry = mirror / ".p2p/system/p2p_capabilities/capabilities.json"
            target = mirror / "tests/fixtures/p2p-impeccable-design-quality/before.html"
            shutil.rmtree(mirror / VENDOR_RELATIVE)
            with mock.patch.object(idq.subprocess, "run") as spawned:
                with self.assertRaises(idq.DesignQualityVendorIdentityError) as caught:
                    _check(target, root=mirror, registry=registry)
                spawned.assert_not_called()
            self.assertEqual(str(caught.exception), "VENDOR_SNAPSHOT_MISSING")

    # --- D: drift AFTER preparation, BEFORE launch --------------------------
    def test_d_last_moment_vendor_drift_is_caught_by_the_final_gate(self) -> None:
        """The mutation lands after target resolution and the runtime lookup.

        ``shutil.which`` is the last piece of preparation before the launch
        sequence, so mutating the vendor mirror there proves the earlier check
        had already passed and the FINAL gate is what fails closed.
        """

        with tempfile.TemporaryDirectory() as raw:
            mirror = _mirror_repository(Path(raw).resolve())
            registry = mirror / ".p2p/system/p2p_capabilities/capabilities.json"
            target = mirror / "tests/fixtures/p2p-impeccable-design-quality/before.html"

            gates: list[str] = []
            real_identity = idq._resolve_identity
            real_gate = idq._final_vendor_identity_gate
            real_which = idq.shutil.which

            def recording_identity(*args, **kwargs):
                result = real_identity(*args, **kwargs)
                gates.append("EARLY_OK")
                return result

            def drifting_which(name):
                _mutate_vendor(mirror)
                return real_which(name)

            def recording_gate(*args, **kwargs):
                gates.append("FINAL_CALLED")
                return real_gate(*args, **kwargs)

            with mock.patch.object(idq, "_resolve_identity", recording_identity):
                with mock.patch.object(idq, "_final_vendor_identity_gate", recording_gate):
                    with mock.patch.object(idq.shutil, "which", drifting_which):
                        with mock.patch.object(idq.subprocess, "run") as spawned:
                            with self.assertRaises(idq.DesignQualityVendorIdentityError) as caught:
                                _check(target, root=mirror, registry=registry)
                            spawned.assert_not_called()

            self.assertEqual(gates[0], "EARLY_OK")
            self.assertIn("FINAL_CALLED", gates)
            self.assertEqual(str(caught.exception), "VENDOR_SNAPSHOT_HASH_MISMATCH")

    def test_d2_final_gate_is_the_statement_before_subprocess(self) -> None:
        """Source-level proof: nothing unrelated sits between gate and launch."""

        source = Path(idq.__file__).read_text(encoding="utf-8")
        marker = "identity = _final_vendor_identity_gate(registry, root, runner)"
        self.assertIn(marker, source)
        head = source.split(marker, 1)[1].split("subprocess.run(", 1)[0]
        statements = [
            line.strip() for line in head.splitlines() if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(
            statements,
            ['command = [node, str(runner), "--root", str(root), *absolute]', "completed ="],
        )

    # --- E: valid explicit repository-local target --------------------------
    def test_e_valid_local_target_runs(self) -> None:
        report = _check(BEFORE)
        if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(report["status"], "COMPLETED")
        self.assertTrue(report["executed"])
        self.assertEqual(report["execution_class"], "READ_ONLY_LOCAL_DETERMINISTIC_CHECK")
        self.assertEqual(report["runtime_permission_authority_claim"], "NONE")
        self.assertTrue(report["vendor_identity_revalidated_immediately_before_subprocess"])
        self.assertEqual(report["snapshot_sha256"], snapshot_tree_sha256(VENDOR_ROOT))
        self.assertEqual(report["upstream_commit"], UPSTREAM_COMMIT)

    def test_e2_relative_target_and_selection_record_run(self) -> None:
        selection = idq.select_action(
            "ui.design_quality.deterministic_check",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        report = _check(BEFORE.relative_to(REPO_ROOT), selection=selection)
        if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(report["status"], "COMPLETED")

    # --- I: the bounded fixture is the only surface touched -----------------
    def test_i_no_project_or_game_truyen_source_is_mutated(self) -> None:
        fixtures = {path: path.read_bytes() for path in FIXTURE_DIR.rglob("*") if path.is_file()}
        vendor_before = snapshot_tree_sha256(VENDOR_ROOT)
        report = _check(BEFORE)
        if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertFalse(report["source_mutation"])
        self.assertEqual({path: path.read_bytes() for path in fixtures}, fixtures)
        self.assertEqual(snapshot_tree_sha256(VENDOR_ROOT), vendor_before)
        for finding in report["findings"]:
            self.assertTrue(str(finding["file"]).startswith("tests/fixtures/p2p-impeccable-design-quality/"))


class DeterministicDetectorProofTests(unittest.TestCase):
    def check(self, target: Path) -> dict:
        return _check(target)

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
