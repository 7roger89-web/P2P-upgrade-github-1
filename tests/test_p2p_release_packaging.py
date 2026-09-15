from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT = REPO_ROOT.parent / "P2P-8.4.7-C-Codex-Edition-v18.zip"
OLD_ARTIFACT = REPO_ROOT.parent / "P2P-8.4.7-C-Codex-Edition-v3.zip"
BEGINNER_REQUEST = "Hoàn thiện dự án này giúp tôi và chỉ dừng khi thực sự xong."
FORBIDDEN_ARCHIVE_FRAGMENTS = ("/.tmp/", "/reports/", "/docs/plans/", "/experimental/", "/.p2p/")
FORBIDDEN_EXTERNAL_PATHS = (
    "/semantica/",
    "/anvien/",
    "/brigade/",
    "/tideline/",
    "/superpowers/",
    "/agent-skills/",
    "/agency-agents/",
)
SHIELD_PORTABLE_PAYLOAD = (
    "shield/__init__.py",
    "shield/runner.py",
    "shield/profile.py",
    "shield/profiles/SHIELD-BASE.json",
    "shield/controls/SHIELD-SECRET-01.json",
    "shield/controls/SHIELD-DEPENDENCY-01.json",
    "shield/controls/SHIELD-CI-01.json",
    "shield/providers/gitleaks-8.18.4.json",
    "shield/providers/osv-scanner-2.4.0.json",
    "shield/providers/zizmor-1.29.0.json",
)
INSTALLED_SHIELD_SURFACE = (
    "shield/__init__.py",
    "shield/profile.py",
    "shield/runner.py",
    "shield/profiles/SHIELD-BASE.json",
)
# Directories inside the packaged Shield payload; an installer that copies a
# directory into an existing directory can nest these on upgrade/reinstall.
SHIELD_SUBDIRECTORIES = ("controls", "profiles", "providers")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_fixture(name: str, destination: Path) -> None:
    shutil.copytree(REPO_ROOT / "tests" / "fixtures" / name, destination)


def extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as handle:
        for member in handle.infolist():
            relative = Path(member.filename)
            if relative.is_absolute() or ".." in relative.parts:
                raise AssertionError(f"Unsafe archive member: {member.filename}")
        handle.extractall(destination)


def run_command(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )
    if result.returncode:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def powershell_executable() -> str:
    for name in ("powershell", "pwsh"):
        executable = shutil.which(name)
        if executable:
            return executable
    raise unittest.SkipTest("PowerShell is required for the supported Windows installer path")


def install(installer: Path, project: Path) -> str:
    result = run_command(
        [
            powershell_executable(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(installer),
            "-Scope",
            "Project",
            "-ProjectPath",
            str(project),
        ]
    )
    return result.stdout + result.stderr


def installed_shield_probe(project: Path) -> dict[str, str]:
    """Import the installed Shield runtime with PYTHONPATH=<project>/.p2p/system."""

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project / ".p2p" / "system")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, shield, shield.profile as profile;"
            "print(json.dumps({'module': shield.__file__,"
            " 'profile_id': profile.PROFILE['profile_id'],"
            " 'profile_version': profile.PROFILE['profile_version']}))",
        ],
        cwd=str(project),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )
    if result.returncode:
        raise AssertionError(
            f"Installed Shield import failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return json.loads(result.stdout.strip().splitlines()[-1])


def assert_installed_shield(case: unittest.TestCase, project: Path) -> dict[str, str]:
    """Prove a supported install produced a runnable, non-nested Shield payload."""

    system = project / ".p2p" / "system"
    for relative in INSTALLED_SHIELD_SURFACE:
        case.assertTrue(
            (system / Path(relative)).is_file(), f"installed Shield file is missing: {relative}"
        )
    nesting_candidates = [system / "shield" / "shield"]
    nesting_candidates.extend(system / "shield" / name / name for name in SHIELD_SUBDIRECTORIES)
    nested = [str(path.relative_to(system)) for path in nesting_candidates if path.exists()]
    case.assertEqual(nested, [], "supported installer nested the Shield payload")
    probe = installed_shield_probe(project)
    case.assertEqual(probe["profile_id"], "SHIELD-BASE")
    case.assertEqual(probe["profile_version"], "0.3.0")
    case.assertTrue(
        probe["module"].startswith(str(system)),
        f"Shield resolved outside the installed system: {probe['module']}",
    )
    return probe


def file_snapshot(root: Path, relative_roots: tuple[str, ...]) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for relative_root in relative_roots:
        path = root / relative_root
        if path.is_file():
            snapshot[relative_root.replace("\\", "/")] = sha256(path)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    snapshot[child.relative_to(root).as_posix()] = sha256(child)
    return snapshot


def seed_existing_project_state(project: Path) -> None:
    policy_path = project / ".p2p" / "project-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["fixture_sentinel"] = "preserve-project-policy"
    policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state = project / ".p2p" / "state"
    (state / "project-fact-ledger.json").write_text(
        json.dumps(
            {
                "schema_version": "fixture-project-fact-ledger/1",
                "claim": "preserve this project fact ledger",
                "fixture_sentinel": "preserve-fact-ledger",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (state / "project-live-specs.json").write_text(
        json.dumps(
            {
                "schema_version": "fixture-project-live-specs/1",
                "projection": "preserve this project live spec",
                "fixture_sentinel": "preserve-live-specs",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    approval = project / ".p2p" / "approvals" / "records" / "existing-project-approval.json"
    approval.write_text(
        json.dumps(
            {
                "request_id": "fixture-existing-project-approval",
                "decision": "APPROVED",
                "fixture_sentinel": "preserve-approval-history",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    capsule = state / "capsules" / "existing-project-capsule.md"
    capsule.parent.mkdir(parents=True, exist_ok=True)
    capsule.write_text("# Existing project CAPSULE\n\nfixture_sentinel: preserve-capsule\n", encoding="utf-8")

    design = project / ".p2p" / "design"
    design.mkdir(parents=True, exist_ok=True)
    (design / "MASTER_DESIGN_SYSTEM.json").write_text(
        json.dumps(
            {
                "schema": "p2p-design-system/1",
                "project_name": "Existing approved design fixture",
                "status": "APPROVED",
                "fixture_sentinel": "preserve-approved-design-system",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (design / "MASTER_DESIGN_SYSTEM.md").write_text(
        "# Existing approved Design System\n\nfixture_sentinel: preserve-approved-design-system\n",
        encoding="utf-8",
    )
    (project / "user-file-sentinel.txt").write_text("preserve-user-file\n", encoding="utf-8")

    for relative in ("project-status.json", "goal-contract.json"):
        path = state / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        value["fixture_sentinel"] = f"preserve-{relative}"
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class P2PReleasePackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = Path(os.environ.get("P2P_RELEASE_ARTIFACT", str(DEFAULT_ARTIFACT))).expanduser().resolve()
        if not cls.artifact.is_file():
            raise unittest.SkipTest(f"Release artifact is missing: {cls.artifact}")
        if not OLD_ARTIFACT.is_file():
            raise unittest.SkipTest(f"Older supported release artifact is missing: {OLD_ARTIFACT}")

    def test_archive_manifest_checksum_and_exclusions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-release-archive-") as raw:
            extracted = Path(raw) / "package"
            extract_archive(self.artifact, extracted)
            members = []
            with zipfile.ZipFile(self.artifact) as handle:
                members = [name.rstrip("/") for name in handle.namelist() if name.rstrip("/")]
            self.assertIn("release-manifest.json", members)
            self.assertIn("RELEASE-SHA256SUMS.txt", members)
            self.assertIn("runtime/p2p_uiux/__init__.py", members)
            self.assertIn("runtime/p2p.manifest.json", members)
            self.assertIn("runtime/p2p_capabilities/capabilities.json", members)
            self.assertIn("runtime/p2p_capabilities/model.py", members)
            self.assertIn("runtime/scripts/p2p_capability_doctor.py", members)
            self.assertIn("runtime/scripts/p2p_host_identity_hook.py", members)
            self.assertIn("runtime/docs/evals/p2p-uiux-eval-suite.json", members)
            self.assertIn("runtime/scripts/p2p_uiux_eval.py", members)
            self.assertIn("runtime/scripts/p2p_uiux_eval_impl.py", members)
            self.assertIn("shield/__init__.py", members)
            self.assertIn("shield/profiles/SHIELD-BASE.json", members)
            self.assertIn("shield/providers/gitleaks-8.18.4.json", members)
            self.assertTrue(all(not any(fragment in f"/{name}" for fragment in FORBIDDEN_ARCHIVE_FRAGMENTS) for name in members))
            self.assertTrue(all(not any(fragment in f"/{name.lower()}" for fragment in FORBIDDEN_EXTERNAL_PATHS) for name in members))
            self.assertTrue(all(not name.endswith((".pyc", ".pyo")) for name in members))
            self.assertTrue(all("Logistics_App_Copy" not in name for name in members))
            verify = run_command([sys.executable, str(REPO_ROOT / "scripts" / "package_release.py"), "--root", str(extracted), "verify"])
            self.assertIn('"status": "PASS"', verify.stdout)
            package_doctor = run_command(
                [
                    sys.executable,
                    str(extracted / "scripts" / "doctor.py"),
                    "--package",
                    str(extracted),
                ]
            )
            self.assertIn("RESULT: PASS", package_doctor.stdout)
            manifest = json.loads((extracted / "release-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["package_version"], (extracted / "VERSION").read_text(encoding="utf-8").strip())
            self.assertEqual(manifest["file_count"] + 2, len(members))
            self.assertIn("runtime/", manifest["selected_roots"])
            runtime_manifest = json.loads((extracted / "runtime" / "p2p.manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(runtime_manifest["package_version"], manifest["package_version"])
            self.assertEqual(runtime_manifest["capability_foundation"]["canonical_denominator"], 8)
            self.assertFalse(runtime_manifest["capability_foundation"]["external_providers_required"])
            self.assertIn("abb7f2fd5a083fa1ff55c326a963ff0d95c33f99", (extracted / "runtime" / "references" / "UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md").read_text(encoding="utf-8"))
            standalone_doctor = run_command(
                [
                    sys.executable,
                    str(extracted / "runtime" / "scripts" / "p2p_uiux_doctor.py"),
                    "--source",
                    str(extracted / "runtime"),
                ]
            )
            self.assertIn('"status": "PASS"', standalone_doctor.stdout)
            foundation_doctor = run_command(
                [
                    sys.executable,
                    str(extracted / "runtime" / "scripts" / "p2p_capability_doctor.py"),
                    "--source",
                    str(extracted / "runtime"),
                    "--profile-root",
                    str(extracted / ".codex" / "agents"),
                    "--json",
                ]
            )
            foundation_result = json.loads(foundation_doctor.stdout)
            self.assertEqual(foundation_result["status"], "PASS")
            self.assertEqual(foundation_result["registry"]["canonical_denominator"], 8)
            self.assertFalse(foundation_result["optional_specialist"]["simulated"])

    def test_supported_installer_fresh_upgrade_and_same_version_reinstall(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-release-install-") as raw:
            sandbox = Path(raw)
            package_root = sandbox / "release"
            extract_archive(self.artifact, package_root)
            old_root = sandbox / "old-release"
            extract_archive(OLD_ARTIFACT, old_root)
            package_version = (package_root / "VERSION").read_text(encoding="utf-8").strip()

            fresh = sandbox / "fresh-project"
            copy_fixture("new-project", fresh)
            fresh_output = install(package_root / "install.ps1", fresh)
            self.assertIn("Install class: FRESH_INSTALL", fresh_output)
            self.assertIn("RESULT: PASS", fresh_output)
            fresh_marker = json.loads((fresh / ".p2p" / "system" / "release.json").read_text(encoding="utf-8"))
            self.assertEqual(fresh_marker["package_version"], package_version)
            self.assertEqual(fresh_marker["install_class"], "FRESH_INSTALL")
            self.assertTrue((fresh / ".agents" / "skills" / "p2p-uiux" / "SKILL.md").is_file())
            self.assertTrue((fresh / ".codex" / "agents" / "p2p-aesthetica.toml").is_file())
            self.assertTrue((fresh / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json").is_file())
            self.assertTrue((fresh / ".p2p" / "system" / "scripts" / "p2p_capability_doctor.py").is_file())
            self.assertTrue((fresh / ".p2p" / "system" / "scripts" / "p2p_host_identity_hook.py").is_file())
            fresh_config = (fresh / ".codex" / "config.toml").read_text(encoding="utf-8")
            package_config = (package_root / ".codex" / "config.toml").read_text(encoding="utf-8")
            self.assertEqual(fresh_config.count("p2p_host_identity_hook.py"), package_config.count("p2p_host_identity_hook.py"))
            self.assertIn(
                'matcher = "^(?:default|p2p_(?:iris|tecton|axiom|vector|datos|anon|architecton|helios|aesthetica))$"',
                fresh_config,
            )
            self.assertTrue((fresh / ".p2p" / "system" / "p2p_uiux" / "recommendation.py").is_file())
            self.assertTrue((fresh / ".p2p" / "system" / "docs" / "evals" / "p2p-uiux-eval-suite.json").is_file())
            assert_installed_shield(self, fresh)
            fresh_foundation = json.loads(
                run_command(
                    [
                        sys.executable,
                        str(fresh / ".p2p" / "system" / "scripts" / "p2p_capability_doctor.py"),
                        "--source",
                        str(fresh / ".p2p" / "system"),
                        "--profile-root",
                        str(fresh / ".codex" / "agents"),
                        "--json",
                    ]
                ).stdout
            )
            self.assertEqual(fresh_foundation["status"], "PASS")
            self.assertEqual(fresh_foundation["registry"]["canonical_denominator"], 8)
            self.assertEqual(fresh_foundation["registry"]["full_quorum"], "8/8")
            self.assertEqual(fresh_foundation["beginner"]["mode"], "DISCOVERY")
            self.assertEqual(fresh_foundation["beginner"]["technical_questions"], [])
            self.assertFalse(fresh_foundation["optional_specialist"]["simulated"])
            self.assertTrue(all(value["core_usable"] for value in fresh_foundation["providers"].values()))
            self.assertTrue(all(not value["provider_installed"] for value in fresh_foundation["providers"].values()))
            governance = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_uiux_governance.py"),
                    "validate",
                ]
            )
            governance_result = json.loads(governance.stdout)
            self.assertTrue(governance_result["valid"])
            self.assertEqual(governance_result["canonical_denominator"], 8)
            self.assertEqual(
                sha256(fresh / ".p2p" / "system" / "scripts" / "p2p_governance.py"),
                sha256(package_root / "scripts" / "p2p_governance.py"),
            )
            self.assertEqual(
                sha256(fresh / ".p2p" / "system" / "scripts" / "p2p_eval.py"),
                sha256(package_root / "scripts" / "p2p_eval.py"),
            )
            ui_route = json.loads(
                run_command(
                    [
                        sys.executable,
                        str(fresh / ".p2p" / "system" / "scripts" / "p2p_router.py"),
                        "route",
                        "--request",
                        "Design a multi-step logistics receiving workflow form with validation dependencies and exception handling",
                    ]
                ).stdout
            )
            self.assertEqual(ui_route["scope"], "UI_UX")
            self.assertTrue(ui_route["use_skill"])
            self.assertTrue(ui_route["call_aesthetica"])
            backend_route = json.loads(
                run_command(
                    [
                        sys.executable,
                        str(fresh / ".p2p" / "system" / "scripts" / "p2p_router.py"),
                        "route",
                        "--request",
                        "Add a backend API endpoint and database index; no interface changes",
                    ]
                ).stdout
            )
            self.assertEqual(backend_route["scope"], "NON_UI")
            self.assertFalse(backend_route["call_aesthetica"])
            request_path = fresh / ".tmp" / "uiux-request.json"
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(
                json.dumps(
                    {
                        "project_name": "Fresh full-release fixture",
                        "product_type": "logistics",
                        "primary_flow": "dispatch shipment",
                        "target_users": ["dispatchers"],
                        "stack": "react",
                        "objective": "Dispatch shipments with clear state and recovery",
                    }
                ),
                encoding="utf-8",
            )
            design_system = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_uiux.py"),
                    "design-system",
                    "--input",
                    str(request_path),
                    "--project",
                    str(fresh),
                    "--approve",
                    "--approved-by",
                    "test-owner",
                ]
            )
            self.assertIn('"status": "APPROVED"', design_system.stdout)
            contract = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_uiux.py"),
                    "contract",
                    "--input",
                    str(request_path),
                    "--project",
                    str(fresh),
                    "--scope",
                    "large",
                ]
            )
            self.assertIn('"valid": true', contract.stdout)
            drift = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_uiux.py"),
                    "drift",
                    "--baseline",
                    str(fresh / ".p2p" / "design" / "MASTER_DESIGN_SYSTEM.json"),
                    "--candidate",
                    str(fresh / ".p2p" / "design" / "MASTER_DESIGN_SYSTEM.json"),
                ]
            )
            self.assertIn('"status": "NO_MATERIAL_DRIFT"', drift.stdout)
            installed_eval = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_uiux_eval.py"),
                    "--source",
                    str(fresh / ".p2p" / "system"),
                ]
            )
            installed_eval_result = json.loads(installed_eval.stdout)
            self.assertEqual(installed_eval_result["status"], "PASS")
            self.assertTrue(all(value == "PASS" for value in installed_eval_result["gates"].values()))
            uiux_doctor = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_uiux_doctor.py"),
                    "--source",
                    str(fresh / ".p2p" / "system"),
                ]
            )
            self.assertIn('"status": "PASS"', uiux_doctor.stdout)
            uiux_drift = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_uiux_drift_check.py"),
                    "--source",
                    str(fresh / ".p2p" / "system"),
                ]
            )
            self.assertIn('"status": "PASS"', uiux_drift.stdout)
            uiux_secret = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_uiux_secret_scan.py"),
                    "--source",
                    str(fresh / ".p2p" / "system"),
                ]
            )
            self.assertIn('"status": "PASS"', uiux_secret.stdout)

            classify = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_workflow.py"),
                    "classify",
                    "--project",
                    str(fresh),
                    "--package",
                    str(package_root),
                    "--request",
                    BEGINNER_REQUEST,
                    "--json",
                ]
            )
            classification = json.loads(classify.stdout)
            self.assertEqual(classification["classification"], "PLAN FIRST")
            self.assertTrue(classification["bounded_interpretation_required"])
            workflow = run_command(
                [
                    sys.executable,
                    str(fresh / ".p2p" / "system" / "scripts" / "p2p_workflow.py"),
                    "run",
                    "--project",
                    str(fresh),
                    "--package",
                    str(package_root),
                    "--request",
                    BEGINNER_REQUEST,
                    "--acceptance",
                ]
            )
            self.assertIn("\nPASS\n", workflow.stdout)
            self.assertTrue((fresh / ".p2p" / "state" / "goal-contract.json").is_file())
            self.assertTrue((fresh / ".p2p" / "state" / "execution-ledger.jsonl").is_file())
            self.assertTrue((fresh / ".p2p" / "state" / "capsules").is_dir())

            existing = sandbox / "existing-project"
            copy_fixture("existing-project", existing)
            install(old_root / "install.ps1", existing)
            old_marker = existing / ".p2p" / "system" / "release.json"
            old_marker.write_text(
                json.dumps(
                    {
                        "schema_version": "p2p-install-release/1",
                        "package_version": "8.4.7-C-codex.3",
                        "install_class": "FRESH_INSTALL",
                        "scope": "Project",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            old_eval = existing / ".p2p" / "system" / "scripts" / "p2p_eval.py"
            quarantined_old_eval = old_eval.with_name("p2p_eval.py.fixture-old")
            old_eval.rename(quarantined_old_eval)
            try:
                old_workflow = run_command(
                    [
                        sys.executable,
                        str(REPO_ROOT / "scripts" / "p2p_workflow.py"),
                        "run",
                        "--project",
                        str(existing),
                        "--package",
                        str(REPO_ROOT),
                        "--request",
                        "Prepare this small application for a bounded baseline.",
                        "--acceptance",
                    ]
                )
            finally:
                quarantined_old_eval.rename(old_eval)
            self.assertIn("\nPASS\n", old_workflow.stdout)
            seed_existing_project_state(existing)
            protected_before_upgrade = file_snapshot(existing, (".p2p/project-policy.json", ".p2p/evals", ".p2p/approvals", ".p2p/state", ".p2p/design", "user-file-sentinel.txt"))
            old_system_workflow = existing / ".p2p" / "system" / "scripts" / "p2p_workflow.py"
            self.assertTrue(old_system_workflow.exists())
            self.assertFalse((existing / ".p2p" / "system" / "p2p_capabilities").exists())

            upgrade_output = install(package_root / "install.ps1", existing)
            self.assertIn("Install class: UPGRADE_FROM_8.4.7-C-codex.3", upgrade_output)
            self.assertIn("RESULT: PASS", upgrade_output)
            protected_after_upgrade = file_snapshot(existing, (".p2p/project-policy.json", ".p2p/evals", ".p2p/approvals", ".p2p/state", ".p2p/design", "user-file-sentinel.txt"))
            self.assertEqual(protected_after_upgrade, protected_before_upgrade)
            upgraded_marker = json.loads((existing / ".p2p" / "system" / "release.json").read_text(encoding="utf-8"))
            self.assertEqual(upgraded_marker["package_version"], package_version)
            self.assertEqual(upgraded_marker["install_class"], "UPGRADE_FROM_8.4.7-C-codex.3")
            assert_installed_shield(self, existing)
            self.assertEqual(
                sha256(existing / ".p2p" / "system" / "scripts" / "p2p_workflow.py"),
                sha256(package_root / "scripts" / "p2p_workflow.py"),
            )
            self.assertEqual(
                sha256(existing / ".p2p" / "system" / "scripts" / "p2p_governance.py"),
                sha256(package_root / "scripts" / "p2p_governance.py"),
            )
            self.assertEqual(
                sha256(existing / ".p2p" / "system" / "scripts" / "p2p_eval.py"),
                sha256(package_root / "scripts" / "p2p_eval.py"),
            )
            self.assertEqual(len(list((existing / ".p2p" / "system").glob("governance"))), 1)
            self.assertFalse((existing / ".p2p" / "system" / "governance" / "governance").exists())
            self.assertTrue((existing / ".agents" / "skills" / "p2p-uiux" / "SKILL.md").is_file())
            self.assertTrue((existing / ".codex" / "agents" / "p2p-aesthetica.toml").is_file())
            self.assertTrue((existing / ".p2p" / "system" / "p2p_uiux" / "recommendation.py").is_file())
            self.assertTrue((existing / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json").is_file())
            self.assertTrue((existing / ".p2p" / "system" / "scripts" / "p2p_capability_doctor.py").is_file())
            upgraded_config = (existing / ".codex" / "config.toml").read_text(encoding="utf-8")
            self.assertEqual(upgraded_config.count("p2p_host_identity_hook.py"), package_config.count("p2p_host_identity_hook.py"))
            self.assertEqual(
                sorted(path.name for path in (existing / ".codex" / "agents").glob("p2p-*.toml")),
                sorted(path.name for path in (package_root / ".codex" / "agents").glob("p2p-*.toml")),
            )
            reused_plan = run_command(
                [
                    sys.executable,
                    str(existing / ".p2p" / "system" / "scripts" / "p2p_workflow.py"),
                    "plan",
                    "--project",
                    str(existing),
                    "--package",
                    str(package_root),
                    "--request",
                    "Update the small application's greeting and finish this scoped change.",
                    "--json",
                ]
            )
            plan = json.loads(reused_plan.stdout)
            self.assertIn("project_eval", plan["evidence_plan"]["reused_controls"])
            self.assertNotIn("project_eval", plan["evidence_plan"]["rerun_controls"])
            self.assertIn("drift_gate", plan["evidence_plan"]["rerun_controls"])

            protected_before_reinstall = file_snapshot(existing, (".p2p/project-policy.json", ".p2p/evals", ".p2p/approvals", ".p2p/state", ".p2p/design", "user-file-sentinel.txt"))
            foundation_before_reinstall = file_snapshot(existing, (".p2p/system/p2p_capabilities",))
            backups_before_reinstall = sorted(path.name for path in (existing / ".p2p" / "install-backups").iterdir())
            reinstall_output = install(package_root / "install.ps1", existing)
            self.assertIn("Install class: SAME_VERSION_REINSTALL", reinstall_output)
            self.assertIn("RESULT: PASS", reinstall_output)
            assert_installed_shield(self, existing)
            protected_after_reinstall = file_snapshot(existing, (".p2p/project-policy.json", ".p2p/evals", ".p2p/approvals", ".p2p/state", ".p2p/design", "user-file-sentinel.txt"))
            self.assertEqual(protected_after_reinstall, protected_before_reinstall)
            self.assertEqual(file_snapshot(existing, (".p2p/system/p2p_capabilities",)), foundation_before_reinstall)
            self.assertEqual(sorted(path.name for path in (existing / ".p2p" / "install-backups").iterdir()), backups_before_reinstall)
            self.assertEqual(len(list((existing / ".p2p" / "system").glob("governance"))), 1)
            self.assertFalse((existing / ".p2p" / "system" / "governance" / "governance").exists())

            doctor = run_command([powershell_executable(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(package_root / "doctor.ps1"), "-Root", str(existing)])
            self.assertIn("RESULT: PASS", doctor.stdout)
            drift = run_command(
                [
                    sys.executable,
                    str(existing / ".p2p" / "system" / "scripts" / "p2p_governance.py"),
                    "drift",
                    "--root",
                    str(existing),
                    "--governance",
                    str(existing / ".p2p" / "system" / "governance"),
                ]
            )
            self.assertIn('"status": "PASS"', drift.stdout)


def release_contract():
    """Load the source-owned release contract exactly like ``doctor.py`` does."""

    script = REPO_ROOT / "scripts" / "package_release.py"
    scripts_root = str(script.parent)
    if scripts_root not in sys.path:
        sys.path.insert(0, scripts_root)
    spec = importlib.util.spec_from_file_location("p2p_release_packaging_contract", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ShieldPortableSurfaceTests(unittest.TestCase):
    """The already-built Shield runtime must travel through the normal release."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = release_contract()

    def test_release_selection_includes_existing_shield_runtime(self) -> None:
        selected = self.contract.selected_paths(REPO_ROOT)
        self.assertIn("shield/", selected)
        for relative in SHIELD_PORTABLE_PAYLOAD:
            self.assertTrue((REPO_ROOT / relative).is_file(), f"missing Shield source file: {relative}")

    def test_supported_installers_copy_packaged_shield_into_p2p_system(self) -> None:
        """Both supported installers must land .p2p/system/shield without nesting.

        ``install.sh`` is executed directly by the Linux acceptance evidence.
        PowerShell is unavailable in this sandbox, so ``install.ps1`` copy
        semantics are pinned by contract here and executed by the supported
        installer acceptance test on a PowerShell host.
        """

        shell = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn('shield_source="$package_root/shield"', shell)
        self.assertIn('if [[ ! -d "$shield_source" ]]; then', shell)
        self.assertIn('mkdir -p "$system_destination/shield"', shell)
        self.assertIn('cp -a "$shield_source/." "$system_destination/shield/"', shell)

        powershell = (REPO_ROOT / "install.ps1").read_text(encoding="utf-8")
        self.assertIn('$ShieldSource = Join-Path $PackageRoot "shield"', powershell)
        self.assertIn(
            "if (-not (Test-Path -LiteralPath $ShieldSource -PathType Container)) {", powershell
        )
        self.assertIn('$ShieldDestination = Join-Path $SystemDestination "shield"', powershell)
        self.assertIn(
            "Get-ChildItem -LiteralPath $ShieldSource -Recurse -Force -File", powershell
        )
        self.assertIn("$_.FullName.Substring($ShieldSource.Length)", powershell)
        # Copying the packaged directory into an already existing destination
        # directory is what nests shield/shield on upgrade, so it must not be
        # the copy form used here.
        self.assertNotIn(
            "Copy-Item -LiteralPath $ShieldSource -Destination $ShieldDestination", powershell
        )

    def test_staged_shield_payload_is_complete_and_free_of_transient_files(self) -> None:
        source_files = sorted(
            path.relative_to(REPO_ROOT).as_posix()
            for path in (REPO_ROOT / "shield").rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
        for relative in SHIELD_PORTABLE_PAYLOAD:
            self.assertIn(relative, source_files)
        with tempfile.TemporaryDirectory(prefix="p2p-shield-stage-") as raw:
            stage = Path(raw) / "stage"
            stage.mkdir()
            self.contract.copy_selected(REPO_ROOT, stage)
            staged = sorted(
                path.relative_to(stage).as_posix()
                for path in (stage / "shield").rglob("*")
                if path.is_file()
            )
            self.assertEqual(staged, source_files)
            transient = [
                name
                for name in staged
                if "__pycache__" in name or name.endswith((".pyc", ".pyo", ".coverage"))
            ]
            self.assertEqual(transient, [])


if __name__ == "__main__":
    unittest.main()
