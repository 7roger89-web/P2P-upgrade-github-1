"""Contract: the documented installed-project Doctor command is executable.

``AGENTS.md`` documents the installed-project validation lane as
``.p2p/system/scripts/doctor.py``. That relative path names two different
programs depending on the filesystem being validated:

* in a P2P-installed project root, the installers place the package doctor
  there (``--root`` / ``--role``), which is what the documented lane means; and
* in this development/source checkout, the same path holds the UI/UX runtime
  doctor (``--source``), which is why the lane must be root-scoped.

These assertions keep the documented command bound to the installer mapping so
the lane cannot drift back into an invocation that is not executable.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS = REPO_ROOT / "AGENTS.md"
PACKAGE_DOCTOR = REPO_ROOT / "scripts" / "doctor.py"
DEV_RUNTIME_DOCTOR = REPO_ROOT / ".p2p" / "system" / "scripts" / "doctor.py"
PACKAGE_RELEASE = REPO_ROOT / "scripts" / "package_release.py"
INSTALL_SH = REPO_ROOT / "install.sh"
INSTALL_PS1 = REPO_ROOT / "install.ps1"
INSTALLED_LANE = "- Installed project validation:"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )


class P2PDoctorInstalledCommandContractTests(unittest.TestCase):
    def validation_section(self) -> str:
        text = AGENTS.read_text(encoding="utf-8")
        section = text.split("## Validation", 1)[1]
        return section.split("\n## ", 1)[0]

    def test_documented_installed_lane_uses_root_and_installed_role(self) -> None:
        section = self.validation_section()
        lanes = [line for line in section.splitlines() if line.startswith(INSTALLED_LANE)]
        self.assertEqual(len(lanes), 1, f"expected exactly one installed-validation lane in {AGENTS.name}")
        lane = lanes[0]
        self.assertIn(".p2p/system/scripts/doctor.py", lane)
        self.assertIn("--root .", lane)
        self.assertIn("--role installed", lane)
        # The UI/UX runtime doctor belongs to the runtime payload, not to this lane.
        self.assertNotIn("--source", lane)

    def test_documented_lane_is_scoped_to_an_installed_project_root(self) -> None:
        section = self.validation_section()
        self.assertIn("P2P-installed project", section)
        # The source checkout keeps the same path with the UI/UX runtime semantics.
        self.assertIn("--source .p2p/system", section)

    def test_installers_place_the_package_doctor_at_the_documented_path(self) -> None:
        shell = INSTALL_SH.read_text(encoding="utf-8")
        self.assertIn('"$package_root/scripts/doctor.py"', shell)
        self.assertIn('"$system_destination/scripts/"', shell)
        powershell = INSTALL_PS1.read_text(encoding="utf-8")
        self.assertIn('"doctor.py"', powershell)
        self.assertIn('("scripts\\" + $ScriptName)', powershell)
        self.assertIn('Join-Path $SystemDestination ("scripts\\" + $ScriptName)', powershell)

    def test_package_doctor_accepts_the_documented_flags(self) -> None:
        result = run([sys.executable, str(PACKAGE_DOCTOR), "--root", str(REPO_ROOT), "--role", "installed"])
        output = f"{result.stdout}{result.stderr}"
        self.assertNotIn("unrecognized arguments", output)
        # This repository is the development source, so the role contract rejects
        # the installed lane here instead of validating the wrong filesystem.
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match detected role", output)

    def test_development_checkout_path_holds_the_uiux_runtime_doctor(self) -> None:
        result = run([sys.executable, str(DEV_RUNTIME_DOCTOR), "--root", "."])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments: --root", f"{result.stdout}{result.stderr}")
        mapping = PACKAGE_RELEASE.read_text(encoding="utf-8")
        block = re.search(r"UIUX_RUNTIME_SCRIPT_MAP = \((.*?)\n\)", mapping, re.DOTALL)
        self.assertIsNotNone(block, "UIUX_RUNTIME_SCRIPT_MAP not found in scripts/package_release.py")
        self.assertIn('("doctor.py", "p2p_uiux_doctor.py")', block.group(1))


if __name__ == "__main__":
    unittest.main()
