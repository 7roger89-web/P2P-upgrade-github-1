from __future__ import annotations

import sys
import unittest
from pathlib import Path


SYSTEM_ROOT = Path(__file__).resolve().parents[1] / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_uiux.security import scan_text  # noqa: E402


class SecretScanTests(unittest.TestCase):
    def test_documentation_placeholder_is_not_a_secret_finding(self) -> None:
        self.assertEqual(scan_text("export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx", "fixture.md"), [])

    def test_real_github_token_shape_remains_blocked(self) -> None:
        findings = scan_text("export GITHUB_TOKEN=ghp_12345678901234567890", "fixture.md")
        self.assertEqual(findings[0]["type"], "github-token")
        self.assertEqual(findings[0]["line"], 1)


if __name__ == "__main__":
    unittest.main()
