"""Focused tests for project-fit P2P capability provisioning."""

from __future__ import annotations

import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
