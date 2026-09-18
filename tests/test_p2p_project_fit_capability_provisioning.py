"""Focused tests for project-fit P2P capability provisioning."""

from __future__ import annotations

import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
