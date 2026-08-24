"""Static package/install checks for the RF01 orientation helper."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class OrientationPackagingTests(unittest.TestCase):
    def test_package_allowlists_include_readme_and_helper(self) -> None:
        text = (ROOT / "scripts/package_release.py").read_text(encoding="utf-8")
        root_block = re.search(r"ROOT_FILES\s*=\s*\((.*?)\)\n", text, re.DOTALL)
        script_block = re.search(r"SCRIPT_FILES\s*=\s*\((.*?)\)\n", text, re.DOTALL)
        self.assertIsNotNone(root_block)
        self.assertIsNotNone(script_block)
        assert root_block is not None
        assert script_block is not None
        self.assertIn('"README.md"', root_block.group(1))
        self.assertIn('"scripts/p2p_orientation.py"', script_block.group(1))

    def test_installers_copy_helper_but_do_not_write_project_readme(self) -> None:
        ps1 = (ROOT / "install.ps1").read_text(encoding="utf-8")
        sh = (ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn('"p2p_orientation.py"', ps1)
        self.assertIn('"$package_root/scripts/p2p_orientation.py"', sh)
        self.assertNotRegex(ps1, r"Copy-Item[^\r\n]*README\.md")
        self.assertNotRegex(sh, r"(?:cp|mv)[^\r\n]*README\.md")


if __name__ == "__main__":
    unittest.main()
