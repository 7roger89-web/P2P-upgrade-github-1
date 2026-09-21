"""Focused tests for project-fit P2P capability provisioning."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PROFILE_SCRIPT = ROOT / "scripts" / "p2p_skill_profile.py"
PACKAGE_SCRIPT = ROOT / "scripts" / "package_release.py"
INSTALL_SH = ROOT / "install.sh"
INSTALL_PS1 = ROOT / "install.ps1"

spec = importlib.util.spec_from_file_location("p2p_skill_profile", PROFILE_SCRIPT)
assert spec and spec.loader
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)

package_spec = importlib.util.spec_from_file_location("p2p_package_release", PACKAGE_SCRIPT)
assert package_spec and package_spec.loader
package_release = importlib.util.module_from_spec(package_spec)
package_spec.loader.exec_module(package_release)

import doctor as p2p_doctor


class ProjectFitDetectionTests(unittest.TestCase):
    def test_backend_or_empty_project_gets_core_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements.txt").write_text("flask==3.1.0\n", encoding="utf-8")
            detected, evidence = profile.detect_profile(root)
            self.assertEqual(detected, profile.PROFILE_CORE)
            self.assertEqual(evidence, ["no-supported-frontend-marker"])

    def test_static_web_gets_generic_frontend_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text("<!doctype html>\n", encoding="utf-8")
            detected, evidence = profile.detect_profile(root)
            self.assertEqual(detected, profile.PROFILE_FRONTEND_GENERIC)
            self.assertIn("file:index.html", evidence)

    def test_streamlit_gets_generic_frontend_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements.txt").write_text("streamlit==1.49.0\n", encoding="utf-8")
            detected, evidence = profile.detect_profile(root)
            self.assertEqual(detected, profile.PROFILE_FRONTEND_GENERIC)
            self.assertIn("python:streamlit", evidence)

    def test_vue_gets_generic_frontend_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"vue": "^3.5.0"}}),
                encoding="utf-8",
            )
            detected, evidence = profile.detect_profile(root)
            self.assertEqual(detected, profile.PROFILE_FRONTEND_GENERIC)
            self.assertIn("package:vue", evidence)

    def test_react_gets_full_react_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"react": "^19.0.0", "next": "^16.0.0"}}),
                encoding="utf-8",
            )
            detected, evidence = profile.detect_profile(root)
            self.assertEqual(detected, profile.PROFILE_FRONTEND_REACT)
            self.assertIn("package:react", evidence)
            self.assertIn("package:next", evidence)


class SkillSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.all_skills = {
            "p2p",
            "p2p-uiux",
            "frontend-design",
            "frontend-development",
            "baseline-ui",
            "react-best-practices",
            "composition-patterns",
            "frontend-code-review",
            "react-doctor",
        }

    def test_core_excludes_frontend_specialists(self) -> None:
        selected = profile.expected_skills_for_profile(
            self.all_skills, profile.PROFILE_CORE
        )
        self.assertEqual(selected, {"p2p", "p2p-uiux"})

    def test_generic_adds_only_stack_neutral_frontend_skills(self) -> None:
        selected = profile.expected_skills_for_profile(
            self.all_skills, profile.PROFILE_FRONTEND_GENERIC
        )
        self.assertTrue(profile.FRONTEND_GENERIC_SKILLS <= selected)
        self.assertFalse(profile.FRONTEND_REACT_SKILLS & selected)

    def test_react_adds_full_curated_frontend_pack(self) -> None:
        selected = profile.expected_skills_for_profile(
            self.all_skills, profile.PROFILE_FRONTEND_REACT
        )
        self.assertEqual(selected, self.all_skills)

    def test_all_scope_preserves_user_install_behavior(self) -> None:
        selected = profile.expected_skills_for_profile(
            self.all_skills, profile.PROFILE_ALL
        )
        self.assertEqual(selected, self.all_skills)


class PackagingAndInstallerContractTests(unittest.TestCase):
    def test_release_ships_profile_selector(self) -> None:
        self.assertIn("scripts/p2p_skill_profile.py", package_release.SCRIPT_FILES)

    def test_both_installers_write_profile_receipt_and_select_skills(self) -> None:
        for path in (INSTALL_SH, INSTALL_PS1):
            text = path.read_text(encoding="utf-8")
            self.assertIn("p2p_skill_profile.py", text, path.name)
            self.assertIn("capability-profile.json", text, path.name)
            self.assertIn("Capability profile", text, path.name)

        sh_text = INSTALL_SH.read_text(encoding="utf-8")
        ps_text = INSTALL_PS1.read_text(encoding="utf-8")
        self.assertNotIn('for source in "$package_root"/.agents/skills/*; do', sh_text)
        self.assertNotIn(
            'foreach ($Skill in Get-ChildItem -LiteralPath $SkillsSource -Directory)',
            ps_text,
        )

    def test_unix_installer_parses(self) -> None:
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash unavailable")
        result = subprocess.run(
            [bash, "-n", str(INSTALL_SH)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_windows_installer_parses_when_pwsh_is_available(self) -> None:
        pwsh = shutil.which("pwsh")
        if pwsh is None:
            self.skipTest("pwsh unavailable")
        command = (
            "[scriptblock]::Create((Get-Content -LiteralPath '"
            + str(INSTALL_PS1).replace("'", "''")
            + "' -Raw)) | Out-Null"
        )
        result = subprocess.run(
            [pwsh, "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_receipt_is_deterministic_and_contains_no_absolute_project_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            skills = Path(tmp) / "skills"
            root.mkdir()
            for name in ("p2p", "frontend-design", "frontend-development", "baseline-ui"):
                entry = skills / name
                entry.mkdir(parents=True)
                (entry / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: test\n---\n",
                    encoding="utf-8",
                )
            (root / "index.html").write_text("<html></html>\n", encoding="utf-8")
            receipt = profile.build_receipt(root, skills)
            self.assertEqual(receipt["schema_version"], "p2p-capability-profile/1")
            self.assertEqual(receipt["profile"], profile.PROFILE_FRONTEND_GENERIC)
            self.assertNotIn(str(root), json.dumps(receipt))


class DoctorProfileReceiptTests(unittest.TestCase):
    def _make_installed_root(self, tmp: str, profile_name: str) -> tuple[Path, set[str]]:
        root = Path(tmp) / "project"
        system = root / ".p2p" / "system"
        system.mkdir(parents=True)
        expected = profile.expected_skills_for_profile(
            p2p_doctor.EXPECTED_SKILLS, profile_name
        )
        aliases = {
            "react-best-practices": "vercel-react-best-practices",
            "composition-patterns": "vercel-composition-patterns",
            "frontend-development": "frontend-dev-guidelines",
        }
        for name in expected:
            entry = root / ".agents" / "skills" / name
            entry.mkdir(parents=True, exist_ok=True)
            frontmatter_name = aliases.get(name, name)
            (entry / "SKILL.md").write_text(
                f"---\nname: {frontmatter_name}\ndescription: test skill\n---\n",
                encoding="utf-8",
            )
        receipt = {
            "schema_version": profile.SCHEMA_VERSION,
            "profile": profile_name,
            "detection_evidence": ["fixture"],
            "selected_skills": sorted(expected),
            "excluded_pack_skills": [],
            "preserve_existing_unselected_skills": True,
        }
        (system / "capability-profile.json").write_text(
            json.dumps(receipt) + "\n", encoding="utf-8"
        )
        return root, expected

    def test_doctor_accepts_matching_generic_profile_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self._make_installed_root(tmp, profile.PROFILE_FRONTEND_GENERIC)
            (root / "index.html").write_text("<html></html>\n", encoding="utf-8")
            report = p2p_doctor.Report()
            p2p_doctor.check_skills(root, report)
            failures = [item for item in report.items if item["level"] == "FAIL"]
            self.assertEqual(failures, [])
            self.assertTrue(
                any(
                    item["check"] == "capability-profile" and item["level"] == "PASS"
                    for item in report.items
                )
            )

    def test_doctor_rejects_stale_profile_after_stack_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self._make_installed_root(tmp, profile.PROFILE_CORE)
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"react": "^19.0.0"}}),
                encoding="utf-8",
            )
            report = p2p_doctor.Report()
            p2p_doctor.check_skills(root, report)
            self.assertTrue(
                any(
                    item["check"] == "capability-profile"
                    and item["level"] == "FAIL"
                    and "stale" in item["message"]
                    for item in report.items
                )
            )

    def test_doctor_rejects_tampered_selected_skill_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, expected = self._make_installed_root(tmp, profile.PROFILE_CORE)
            receipt_path = root / ".p2p" / "system" / "capability-profile.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["selected_skills"] = sorted(expected - {"p2p"})
            receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
            report = p2p_doctor.Report()
            p2p_doctor.check_skills(root, report)
            self.assertTrue(
                any(
                    item["check"] == "capability-profile" and item["level"] == "FAIL"
                    for item in report.items
                )
            )


SH_PROFILE_MODE_RE = re.compile(
    r'profile_mode="(?P<default>[A-Z_]+)"\s*\n'
    r'if \[\[ "\$scope" == "(?P<user_scope>[^"]+)" \]\]; then\s*\n'
    r'\s*profile_mode="(?P<user_mode>[A-Z_]+)"'
)
PS_PROFILE_MODE_RE = re.compile(
    r'\$ProfileMode = if \(\$Scope -eq "(?P<user_scope>[^"]+)"\)'
    r' \{ "(?P<user_mode>[A-Z_]+)" \} else \{ "(?P<default>[A-Z_]+)" \}'
)

PACK_SKILLS = (
    "p2p",
    "p2p-uiux",
    "frontend-design",
    "frontend-development",
    "baseline-ui",
    "react-best-practices",
    "composition-patterns",
    "frontend-code-review",
    "react-doctor",
)


def _make_pack(base: Path) -> Path:
    skills = base / "pack"
    for name in PACK_SKILLS:
        entry = skills / name
        entry.mkdir(parents=True)
        (entry / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: packaged skill\n---\n",
            encoding="utf-8",
        )
    return skills


def _run_selector(mode: str, root: Path, skills_dir: Path, output_format: str) -> str:
    result = subprocess.run(
        [
            sys.executable,
            str(PROFILE_SCRIPT),
            "--root", str(root),
            "--skills-dir", str(skills_dir),
            "--profile", mode,
            "--format", output_format,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


class InstallerProfileParityTests(unittest.TestCase):
    """SAME_PROJECT_FACTS -> SAME_PROFILE on the Unix and Windows code paths."""

    def test_installers_map_scope_to_the_same_profile_mode(self) -> None:
        sh_match = SH_PROFILE_MODE_RE.search(INSTALL_SH.read_text(encoding="utf-8"))
        ps_match = PS_PROFILE_MODE_RE.search(INSTALL_PS1.read_text(encoding="utf-8"))
        self.assertIsNotNone(sh_match, "install.sh profile-mode mapping not found")
        self.assertIsNotNone(ps_match, "install.ps1 profile-mode mapping not found")
        assert sh_match is not None and ps_match is not None
        self.assertEqual(sh_match.group("user_scope").lower(), ps_match.group("user_scope").lower())
        self.assertEqual(sh_match.group("user_scope").lower(), "user")
        self.assertEqual(sh_match.group("user_mode"), ps_match.group("user_mode"))
        self.assertEqual(sh_match.group("user_mode"), profile.PROFILE_ALL)
        self.assertEqual(sh_match.group("default"), ps_match.group("default"))
        self.assertEqual(sh_match.group("default"), profile.PROFILE_AUTO)

    def test_installers_keep_no_independent_stack_detector(self) -> None:
        for path in (INSTALL_SH, INSTALL_PS1):
            text = path.read_text(encoding="utf-8")
            for marker in (
                "package.json",
                "next.config",
                "requirements.txt",
                "streamlit",
                "angular.json",
                "vite.config",
            ):
                self.assertNotIn(marker, text, f"{path.name} detects {marker} itself")

    def test_same_project_facts_select_the_same_profile_for_both_platforms(self) -> None:
        fixtures = {
            profile.PROFILE_CORE: {"files": {}, "package": None},
            profile.PROFILE_FRONTEND_GENERIC: {
                "files": {},
                "package": {"dependencies": {"vue": "^3.5.0"}},
            },
            profile.PROFILE_FRONTEND_REACT: {
                "files": {},
                "package": {"dependencies": {"react": "^19.0.0", "next": "^16.0.0"}},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            skills = _make_pack(base)
            for index, (expected_profile, fixture) in enumerate(fixtures.items()):
                root = base / f"project-{index}"
                root.mkdir()
                for name, body in fixture["files"].items():
                    (root / name).write_text(body, encoding="utf-8")
                if fixture["package"] is not None:
                    (root / "package.json").write_text(
                        json.dumps(fixture["package"]), encoding="utf-8"
                    )
                # Both installers resolve project scope to the same mode, so both
                # invocations below are what install.sh and install.ps1 execute.
                unix_profile = _run_selector("AUTO", root, skills, "profile").strip()
                windows_profile = _run_selector("AUTO", root, skills, "profile").strip()
                self.assertEqual(unix_profile, expected_profile)
                self.assertEqual(windows_profile, unix_profile)
                unix_lines = _run_selector("AUTO", root, skills, "lines")
                windows_lines = _run_selector("AUTO", root, skills, "lines")
                self.assertEqual(unix_lines, windows_lines)

    def test_user_scope_maps_to_all_on_both_platforms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            skills = _make_pack(base)
            root = base / "project"
            root.mkdir()
            (root / "requirements.txt").write_text("flask==3.1.0\n", encoding="utf-8")
            self.assertEqual(
                _run_selector("ALL", root, skills, "profile").strip(), profile.PROFILE_ALL
            )
            self.assertEqual(
                sorted(
                    _run_selector("ALL", root, skills, "lines").split()
                ),
                sorted(PACK_SKILLS),
            )


class ReinstallIdempotencyTests(unittest.TestCase):
    def test_receipt_and_selection_are_deterministic_across_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            skills = _make_pack(base)
            root = base / "project"
            root.mkdir()
            (root / "index.html").write_text("<html></html>\n", encoding="utf-8")
            first = _run_selector("AUTO", root, skills, "json")
            second = _run_selector("AUTO", root, skills, "json")
            self.assertEqual(first, second)
            self.assertEqual(
                _run_selector("AUTO", root, skills, "lines"),
                _run_selector("AUTO", root, skills, "lines"),
            )
            receipt = json.loads(first)
            self.assertEqual(receipt["profile"], profile.PROFILE_FRONTEND_GENERIC)
            self.assertIs(receipt["preserve_existing_unselected_skills"], True)

    def test_installers_never_delete_unselected_skills(self) -> None:
        sh_text = INSTALL_SH.read_text(encoding="utf-8")
        ps_text = INSTALL_PS1.read_text(encoding="utf-8")
        for path, text in ((INSTALL_SH, sh_text), (INSTALL_PS1, ps_text)):
            self.assertIn("SAME_VERSION_REINSTALL", text, path.name)
            self.assertNotIn("rm -rf", text, f"{path.name} deletes files outright")
        # Only a destination that is about to be replaced is moved to backup; the
        # skill loop iterates the selected profile list, so unselected installed
        # skills are never enumerated and never removed.
        self.assertIn('mv "$destination" "$backup_root/skills/$name"', sh_text)

    def test_reinstall_of_the_same_facts_reselects_the_same_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            skills = _make_pack(base)
            root = base / "project"
            root.mkdir()
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"react": "^19.0.0"}}), encoding="utf-8"
            )
            installed = {
                name
                for name in _run_selector("AUTO", root, skills, "lines").split()
                if name
            }
            reinstalled = {
                name
                for name in _run_selector("AUTO", root, skills, "lines").split()
                if name
            }
            self.assertEqual(installed, reinstalled)
            self.assertEqual(
                installed,
                profile.expected_skills_for_profile(
                    set(PACK_SKILLS), profile.PROFILE_FRONTEND_REACT
                ),
            )

    def test_narrower_detection_never_revokes_installed_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            skills = _make_pack(base)
            root = base / "project"
            root.mkdir()
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"react": "^19.0.0"}}), encoding="utf-8"
            )
            react_selection = {
                name
                for name in _run_selector("AUTO", root, skills, "lines").split()
                if name
            }
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"vue": "^3.5.0"}}), encoding="utf-8"
            )
            narrowed_selection = {
                name
                for name in _run_selector("AUTO", root, skills, "lines").split()
                if name
            }
            self.assertTrue(narrowed_selection < react_selection)
            # Newly justified skills are added; nothing already installed is
            # enumerated for removal by the installers.
            receipt = json.loads(_run_selector("AUTO", root, skills, "json"))
            self.assertEqual(receipt["profile"], profile.PROFILE_FRONTEND_GENERIC)
            self.assertIs(receipt["preserve_existing_unselected_skills"], True)


class DoctorProfileSubsetTests(unittest.TestCase):
    def _install(self, root: Path, profile_name: str) -> set[str]:
        system = root / ".p2p" / "system"
        system.mkdir(parents=True)
        expected = profile.expected_skills_for_profile(
            p2p_doctor.EXPECTED_SKILLS, profile_name
        )
        for name in expected:
            entry = root / ".agents" / "skills" / name
            entry.mkdir(parents=True, exist_ok=True)
            (entry / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: test skill\n---\n",
                encoding="utf-8",
            )
        receipt = {
            "schema_version": profile.SCHEMA_VERSION,
            "profile": profile_name,
            "detection_evidence": ["fixture"],
            "selected_skills": sorted(expected),
            "excluded_pack_skills": sorted(
                set(p2p_doctor.EXPECTED_SKILLS) - expected
            ),
            "preserve_existing_unselected_skills": True,
        }
        (system / "capability-profile.json").write_text(
            json.dumps(receipt) + "\n", encoding="utf-8"
        )
        return expected

    def test_core_install_passes_without_any_frontend_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "requirements.txt").write_text("flask==3.1.0\n", encoding="utf-8")
            expected = self._install(root, profile.PROFILE_CORE)
            self.assertFalse(expected & profile.FRONTEND_SPECIALIST_SKILLS)
            report = p2p_doctor.Report()
            p2p_doctor.check_skills(root, report)
            self.assertEqual(
                [item for item in report.items if item["level"] == "FAIL"], []
            )

    def test_missing_required_profile_skill_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "requirements.txt").write_text("flask==3.1.0\n", encoding="utf-8")
            self._install(root, profile.PROFILE_CORE)
            shutil.rmtree(root / ".agents" / "skills" / "p2p-eval")
            report = p2p_doctor.Report()
            p2p_doctor.check_skills(root, report)
            self.assertTrue(
                any(
                    item["check"] == "skills-count"
                    and item["level"] == "FAIL"
                    and "p2p-eval" in item["message"]
                    for item in report.items
                )
            )

    def test_fallback_import_branch_exposes_detect_profile(self) -> None:
        """Regression: the ModuleNotFoundError fallback must import every symbol."""
        code = (
            "import importlib.util, json, sys, tempfile\n"
            "from pathlib import Path\n"
            f"ROOT = Path({str(ROOT)!r})\n"
            "sys.path = [p for p in sys.path if Path(p or '.').resolve() != (ROOT / 'scripts').resolve()]\n"
            "spec = importlib.util.spec_from_file_location('doctor_probe', ROOT / 'scripts' / 'doctor.py')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "assert str(ROOT / 'scripts') in sys.path, 'fallback branch did not run'\n"
            "assert callable(mod.detect_profile), 'detect_profile missing from fallback import'\n"
            "tmp = Path(tempfile.mkdtemp())\n"
            "expected = mod.expected_skills_for_profile(mod.EXPECTED_SKILLS, 'CORE')\n"
            "for name in expected:\n"
            "    entry = tmp / '.agents' / 'skills' / name\n"
            "    entry.mkdir(parents=True, exist_ok=True)\n"
            "    (entry / 'SKILL.md').write_text('---\\nname: %s\\ndescription: x\\n---\\n' % name)\n"
            "(tmp / '.p2p' / 'system').mkdir(parents=True)\n"
            "(tmp / '.p2p' / 'system' / 'capability-profile.json').write_text(json.dumps({\n"
            "    'schema_version': mod.CAPABILITY_PROFILE_SCHEMA,\n"
            "    'profile': 'CORE',\n"
            "    'detection_evidence': ['no-supported-frontend-marker'],\n"
            "    'selected_skills': sorted(expected),\n"
            "    'excluded_pack_skills': [],\n"
            "    'preserve_existing_unselected_skills': True,\n"
            "}))\n"
            "report = mod.Report()\n"
            "resolved = mod.expected_skills_for_root(tmp, report)\n"
            "assert resolved == expected, resolved\n"
            "assert any(i['check'] == 'capability-profile' and i['level'] == 'PASS' for i in report.items)\n"
            "print('FALLBACK_OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FALLBACK_OK", result.stdout)


class Pr223InteroperabilityProofTests(unittest.TestCase):
    """Install-time profile selection coexists with #223 task-time selection."""

    def setUp(self) -> None:
        system_root = ROOT / ".p2p" / "system"
        if str(system_root) not in sys.path:
            sys.path.insert(0, str(system_root))

    def test_install_profile_and_domain_source_selection_are_independent(self) -> None:
        from p2p_capabilities import select_domain_sources

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements.txt").write_text("flask==3.1.0\n", encoding="utf-8")
            install_profile, evidence = profile.detect_profile(root)
        self.assertEqual(install_profile, profile.PROFILE_CORE)
        self.assertEqual(evidence, ["no-supported-frontend-marker"])

        # The same project keeps full #223 task-time domain source selection:
        # a Ziwei methodology task resolves its authoritative source even though
        # the install-time profile is CORE.
        receipt = select_domain_sources(
            {
                "task_id": "TASK-INTEROP-01",
                "desired_outcome": (
                    "Lập lá số Tử Vi Đẩu Số theo phái Trung Châu và an sao Tứ Hóa"
                ),
            }
        )
        self.assertEqual(receipt.domain, "metaphysics.ziwei")
        self.assertEqual(receipt.selection_status, "SATISFIED")
        self.assertGreater(len(receipt.selected_sources), 0)

    def test_selector_is_not_a_second_router_or_registry(self) -> None:
        source = PROFILE_SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "p2p_capabilities",
            "select_domain_sources",
            "SOURCE_ROLES",
            "build_domain_source_catalog",
            "DomainSourceRecord",
        ):
            self.assertNotIn(forbidden, source)
        # #214 owns packaged local skills only; it exposes no domain/authority
        # vocabulary of its own.
        self.assertNotIn("authority", source.lower())
        self.assertNotIn("provenance", source.lower())
        self.assertEqual(
            set(profile.PROFILES),
            {
                profile.PROFILE_ALL,
                profile.PROFILE_CORE,
                profile.PROFILE_FRONTEND_GENERIC,
                profile.PROFILE_FRONTEND_REACT,
            },
        )


if __name__ == "__main__":
    unittest.main()
