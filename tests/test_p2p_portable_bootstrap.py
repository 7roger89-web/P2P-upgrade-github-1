"""Behavior tests for the portable PB01 bootstrap boundary."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "p2p_bootstrap.py"
TMP_ROOT = REPO_ROOT / ".tmp"
OUTER_TMP_ROOT = REPO_ROOT.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import p2p_bootstrap as bootstrap  # noqa: E402


class P2PPortableBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def _root(self, prefix: str) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(dir=TMP_ROOT, prefix=prefix)

    @staticmethod
    def _tree_hashes(root: Path) -> dict[str, str]:
        return {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    @staticmethod
    def _gateway_events(root: Path) -> int:
        ledger = root / ".p2p" / "state" / "execution-ledger.jsonl"
        if not ledger.is_file():
            return 0
        return sum(
            1
            for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip() and json.loads(line).get("event") == "beginner_gateway_ingested"
        )

    def _fresh(self, request: str | None = None, *, package: Path = REPO_ROOT) -> tuple[Path, dict]:
        context = self._root("p2p-pb01-fresh-")
        project = Path(context.name)
        result = bootstrap.bootstrap(project, request, str(package))
        # Keep the TemporaryDirectory alive by attaching it to the result only
        # for this helper's callers that consume the result immediately.
        result["_test_context"] = context
        return project, result

    def _make_installed_runtime(self, project: Path) -> None:
        system = project / ".p2p" / "system"
        shutil.copytree(REPO_ROOT / ".p2p" / "system", system)
        shutil.copytree(REPO_ROOT / "governance", system / "governance")
        installed_scripts = system / "scripts"
        installed_scripts.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "scripts" / "p2p_bootstrap.py", installed_scripts / "p2p_bootstrap.py")
        version = (system / "VERSION").read_text(encoding="utf-8").strip()
        (system / "p2p-install-manifest.json").write_text(
            json.dumps(
                {
                    "schema": "p2p-install-manifest/1",
                    "package_version": version,
                    "managed_file_count": 1,
                }
            ),
            encoding="utf-8",
        )
        (system / "release.json").write_text(
            json.dumps(
                {
                    "schema": "p2p-install-release/1",
                    "package_version": version,
                    "managed_file_count": 1,
                }
            ),
            encoding="utf-8",
        )

    def _make_source_marker_fixture(self, root: Path, version: str) -> None:
        for relative in bootstrap.SOURCE_REQUIRED_FILES:
            source = REPO_ROOT / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        (root / "VERSION").write_text(version + "\n", encoding="utf-8")
        (root / "manifest").mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": bootstrap.SOURCE_MANIFEST_SCHEMA,
            "name": "isolated PB01 source fixture",
            "version": version,
        }
        (root / "manifest" / "package.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        system_manifest = {
            "manifest_schema": bootstrap.SYSTEM_MANIFEST_SCHEMA,
            "package_name": "isolated PB01 source fixture",
            "package_version": version,
        }
        (root / ".p2p" / "system" / "p2p.manifest.json").write_text(
            json.dumps(system_manifest), encoding="utf-8"
        )
        (root / ".p2p" / "system" / "VERSION").write_text(version + "\n", encoding="utf-8")

    def test_fresh_local_environment_reaches_beginner_gateway(self) -> None:
        with self._root("p2p-pb01-fresh-") as raw:
            project = Path(raw)
            result = bootstrap.bootstrap(
                project,
                "Build a small genealogy app for older adults.",
                str(REPO_ROOT),
            )
            self.assertEqual(result["status"], bootstrap.STATUS_READY)
            self.assertEqual(result["beginner_gateway"]["status"], "BOUND")
            self.assertEqual(result["state_initialization"]["status"], "CREATED")
            self.assertTrue(result["beginner_gateway"]["saved_for_resume"])
            for relative in (
                ".p2p/state/goal-contract.json",
                ".p2p/state/task-state.json",
                ".p2p/state/execution-ledger.jsonl",
                ".p2p/evals/suite.json",
            ):
                self.assertTrue((project / relative).is_file(), relative)

    def test_single_beginner_action_has_no_internal_topology(self) -> None:
        with self._root("p2p-pb01-beginner-") as raw:
            project = Path(raw)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    "--project",
                    str(project),
                    "--package",
                    str(REPO_ROOT),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            public = json.loads(completed.stdout)
            self.assertIn(public["status"], {bootstrap.STATUS_READY, bootstrap.STATUS_NEEDS_DECISION})
            self.assertEqual(public["beginner_gateway"], "BOUND")
            self.assertTrue(public["safe_next_action"])
            self.assertNotIn("advanced", public)
            public_text = json.dumps(public, ensure_ascii=False).casefold()
            for forbidden in (
                "git",
                "sha",
                "branch",
                "worktree",
                "provider",
                "model",
                "skill",
                "quorum",
                "governance",
            ):
                self.assertNotIn(forbidden, public_text)

    def test_valid_initialized_environment_is_reused_without_runtime_replacement(self) -> None:
        with self._root("p2p-pb01-installed-") as raw:
            project = Path(raw)
            self._make_installed_runtime(project)
            runtime_before = self._tree_hashes(project / ".p2p" / "system")
            request = "Build a small genealogy app for older adults."
            first = bootstrap.bootstrap(project, request)
            before_second = self._tree_hashes(project)
            second = bootstrap.bootstrap(project, request)
            after_second = self._tree_hashes(project)
            self.assertEqual(first["status"], bootstrap.STATUS_READY)
            self.assertEqual(second["status"], bootstrap.STATUS_READY)
            self.assertEqual(first["details"]["environment"]["mode"], "INSTALLED_PROJECT")
            self.assertEqual(second["state_initialization"]["status"], "REUSED")
            self.assertEqual(runtime_before, self._tree_hashes(project / ".p2p" / "system"))
            self.assertEqual(before_second, after_second)

    def test_installed_bootstrap_launcher_is_required_and_missing_launcher_is_rejected(self) -> None:
        with self._root("p2p-pb01-installed-launcher-contract-") as raw:
            project = Path(raw)
            self._make_installed_runtime(project)
            request = "Build a small genealogy app for older adults."

            accepted = bootstrap.bootstrap(project, request)
            self.assertEqual(accepted["status"], bootstrap.STATUS_READY)
            self.assertEqual(accepted["details"]["environment"]["mode"], "INSTALLED_PROJECT")

            launcher = project / ".p2p" / "system" / "scripts" / "p2p_bootstrap.py"
            self.assertTrue(launcher.is_file())
            launcher.unlink()
            before_rejected = self._tree_hashes(project)

            rejected = bootstrap.bootstrap(project, request)
            self.assertEqual(rejected["status"], bootstrap.STATUS_BLOCKED)
            self.assertEqual(rejected["details"]["code"], "INSTALLED_REQUIRED_FILE_MISSING")
            self.assertEqual(rejected["details"]["missing"], ["scripts/p2p_bootstrap.py"])
            self.assertEqual(before_rejected, self._tree_hashes(project))
            self.assertTrue(rejected["safe_next_action"])

    def test_standalone_installed_entrypoint_works_without_source_checkout(self) -> None:
        with tempfile.TemporaryDirectory(dir=OUTER_TMP_ROOT, prefix="p2p-pb01-standalone-") as raw:
            project = Path(raw)
            self._make_installed_runtime(project)
            installed_scripts = project / ".p2p" / "system" / "scripts"
            shutil.copy2(REPO_ROOT / "scripts" / "p2p_bootstrap.py", installed_scripts / "p2p_bootstrap.py")
            shutil.copy2(REPO_ROOT / "scripts" / "p2p_workflow.py", installed_scripts / "p2p_workflow.py")
            shutil.copy2(REPO_ROOT / "scripts" / "p2p_eval.py", installed_scripts / "p2p_eval.py")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(installed_scripts / "p2p_bootstrap.py"),
                    "--project",
                    str(project),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=project,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            public = json.loads(completed.stdout)
            self.assertEqual(public["status"], bootstrap.STATUS_READY)
            self.assertEqual(public["beginner_gateway"], "BOUND")
            self.assertTrue(public["safe_next_action"])

    def test_bootstrap_twice_is_byte_idempotent_and_does_not_duplicate_gateway_event(self) -> None:
        with self._root("p2p-pb01-idempotent-") as raw:
            project = Path(raw)
            request = "Build a small genealogy app for older adults."
            first = bootstrap.bootstrap(project, request, str(REPO_ROOT))
            before = self._tree_hashes(project)
            first_events = self._gateway_events(project)
            second = bootstrap.bootstrap(project, request, str(REPO_ROOT))
            after = self._tree_hashes(project)
            second_events = self._gateway_events(project)
            self.assertEqual(first["status"], bootstrap.STATUS_READY)
            self.assertEqual(second["status"], bootstrap.STATUS_READY)
            self.assertEqual(first_events, 1)
            self.assertEqual(second_events, 1)
            self.assertEqual(before, after)
            self.assertEqual(second["idempotency"]["duplicate_event_added"], 0)

    def test_non_default_project_path_and_explicit_package_work(self) -> None:
        with self._root("p2p-pb01-non-default-parent-") as raw:
            project = Path(raw) / "A project with spaces" / "nested"
            project.mkdir(parents=True)
            package = Path(raw) / "P2P install with spaces"
            shutil.copytree(
                REPO_ROOT,
                package,
                ignore=shutil.ignore_patterns(".git", ".tmp", ".anvien", "__pycache__"),
            )
            result = bootstrap.bootstrap(
                project,
                "Build a small genealogy app for older adults.",
                str(package),
            )
            self.assertEqual(result["status"], bootstrap.STATUS_READY)
            self.assertEqual(result["details"]["environment"]["root"].resolve(), package.resolve())
            self.assertEqual(result["details"]["binding"]["binding"]["locator"]["kind"], "RELATIVE_PACKAGE")
            self.assertNotIn(str(project.drive), json.dumps(result["details"]["binding"]["binding"]))

    def test_advanced_projection_is_json_serializable_and_opt_in(self) -> None:
        with self._root("p2p-pb01-advanced-") as raw:
            project = Path(raw)
            result = bootstrap.bootstrap(
                project,
                "Build a small genealogy app for older adults.",
                str(REPO_ROOT),
            )
            public = bootstrap.public_result(result)
            advanced = bootstrap.public_result(result, advanced=True)
            self.assertNotIn("advanced", public)
            self.assertIn("advanced", advanced)
            encoded = json.dumps(advanced, ensure_ascii=False)
            decoded = json.loads(encoded)
            self.assertIsInstance(decoded["advanced"]["details"]["environment"]["root"], str)
            self.assertTrue(decoded["advanced"]["details"]["environment"]["root"])

    def test_ambiguous_authority_fails_closed_without_project_writes(self) -> None:
        with self._root("p2p-pb01-ambiguous-") as raw:
            parent = Path(raw)
            project = parent / "project"
            project.mkdir()
            package_a = parent / "package-a"
            package_b = parent / "package-b"
            package_a.mkdir()
            package_b.mkdir()
            self._make_source_marker_fixture(package_a, "8.4.7-C-codex.test-a")
            self._make_source_marker_fixture(package_b, "8.4.7-C-codex.test-b")
            before = self._tree_hashes(project)
            result = bootstrap.bootstrap(
                project,
                "Build a small genealogy app for older adults.",
                candidate_roots=[package_a, package_b],
            )
            self.assertEqual(result["status"], bootstrap.STATUS_NEEDS_DECISION)
            self.assertEqual(result["details"]["code"], "MULTIPLE_VALID_PACKAGES")
            self.assertTrue(result["safe_next_action"])
            self.assertEqual(before, self._tree_hashes(project))

    def test_explicit_invalid_package_fails_closed_without_project_writes(self) -> None:
        with self._root("p2p-pb01-invalid-package-") as raw:
            parent = Path(raw)
            project = parent / "project"
            project.mkdir()
            invalid = parent / "not-p2p"
            invalid.mkdir()
            (invalid / "VERSION").write_text("wrong\n", encoding="utf-8")
            before = self._tree_hashes(project)
            result = bootstrap.bootstrap(
                project,
                "Build a small genealogy app for older adults.",
                str(invalid),
            )
            self.assertEqual(result["status"], bootstrap.STATUS_BLOCKED)
            self.assertEqual(result["details"]["code"], "EXPLICIT_PACKAGE_INVALID")
            self.assertEqual(before, self._tree_hashes(project))

    def test_malformed_existing_state_is_not_replaced(self) -> None:
        with self._root("p2p-pb01-malformed-state-") as raw:
            project = Path(raw)
            state = project / ".p2p" / "state"
            state.mkdir(parents=True)
            goal = state / "goal-contract.json"
            goal.write_text("{not-json", encoding="utf-8")
            before = self._tree_hashes(project)
            result = bootstrap.bootstrap(
                project,
                "Build a small genealogy app for older adults.",
                str(REPO_ROOT),
            )
            self.assertEqual(result["status"], bootstrap.STATUS_BLOCKED)
            self.assertEqual(result["details"]["code"], "GOAL_CONTRACT_UNREADABLE")
            self.assertEqual(before, self._tree_hashes(project))
            self.assertFalse((state / "task-state.json").exists())

    def test_malformed_existing_ledger_is_not_replaced(self) -> None:
        with self._root("p2p-pb01-malformed-ledger-") as raw:
            project = Path(raw)
            ledger = project / ".p2p" / "state" / "execution-ledger.jsonl"
            ledger.parent.mkdir(parents=True)
            ledger.write_text("{not-json\n", encoding="utf-8")
            before = self._tree_hashes(project)
            result = bootstrap.bootstrap(
                project,
                "Build a small genealogy app for older adults.",
                str(REPO_ROOT),
            )
            self.assertEqual(result["status"], bootstrap.STATUS_BLOCKED)
            self.assertEqual(result["details"]["code"], "EXECUTION_LEDGER_INVALID")
            self.assertEqual(before, self._tree_hashes(project))
            self.assertEqual(ledger.read_text(encoding="utf-8"), "{not-json\n")
            self.assertFalse((project / ".p2p" / "state" / "goal-contract.json").exists())

    def test_conflicting_existing_goal_requires_decision_and_preserves_bytes(self) -> None:
        with self._root("p2p-pb01-goal-conflict-") as raw:
            project = Path(raw)
            first_request = "Build a small genealogy app for older adults."
            bootstrap.bootstrap(project, first_request, str(REPO_ROOT))
            goal = project / ".p2p" / "state" / "goal-contract.json"
            before = self._tree_hashes(project)
            result = bootstrap.bootstrap(
                project,
                "Improve this existing project's navigation.",
                str(REPO_ROOT),
            )
            self.assertEqual(result["status"], bootstrap.STATUS_NEEDS_DECISION)
            self.assertEqual(result["details"]["code"], "EXISTING_GOAL_REQUIRES_RECONCILIATION")
            self.assertTrue(result["safe_next_action"])
            self.assertEqual(before, self._tree_hashes(project))
            self.assertIn(first_request, goal.read_text(encoding="utf-8"))

    def test_unmarked_installed_system_is_blocked_and_preserved(self) -> None:
        with self._root("p2p-pb01-runtime-conflict-") as raw:
            project = Path(raw)
            system = project / ".p2p" / "system"
            system.mkdir(parents=True)
            sentinel = system / "owner-data.txt"
            sentinel.write_text("keep this byte", encoding="utf-8")
            before = self._tree_hashes(project)
            result = bootstrap.bootstrap(
                project,
                "Build a small genealogy app for older adults.",
                str(REPO_ROOT),
            )
            self.assertEqual(result["status"], bootstrap.STATUS_BLOCKED)
            self.assertEqual(result["details"]["code"], "INSTALLED_MARKER_SET_INCOMPLETE")
            self.assertEqual(before, self._tree_hashes(project))
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep this byte")

    def test_package_and_project_same_root_never_bootstraps_the_package(self) -> None:
        state = REPO_ROOT / ".p2p" / "state"
        before_exists = state.exists()
        result = bootstrap.bootstrap(
            REPO_ROOT,
            "Build a small genealogy app for older adults.",
            str(REPO_ROOT),
        )
        self.assertEqual(result["status"], bootstrap.STATUS_NEEDS_DECISION)
        self.assertEqual(result["details"]["code"], "PACKAGE_AND_PROJECT_ARE_SAME")
        self.assertEqual(state.exists(), before_exists)

    def test_adapter_delegates_existing_control_plane_and_preserves_safety(self) -> None:
        with self._root("p2p-pb01-delegation-") as raw:
            project = Path(raw)
            result = bootstrap.bootstrap(
                project,
                "Build a small genealogy app for older adults.",
                str(REPO_ROOT),
            )
            self.assertEqual(result["delegation"]["orchestrator"], "existing p2p_workflow")
            self.assertEqual(result["delegation"]["gateway"], "existing BG01 beginner_gateway")
            self.assertFalse(result["delegation"]["execution_started"])
            self.assertFalse(result["safety"]["automatic_host_start"])
            self.assertFalse(result["safety"]["promote"])
            self.assertFalse(result["safety"]["release"])
            self.assertFalse(result["safety"]["deploy"])
            self.assertFalse(result["safety"]["permission_expansion"])


if __name__ == "__main__":
    unittest.main()
