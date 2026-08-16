from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

_SPEC = importlib.util.spec_from_file_location(
    "p2p_uiux_cli",
    SYSTEM_ROOT / "scripts" / "p2p_uiux.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_CLI = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CLI)


class P2PUIUXCLITests(unittest.TestCase):
    def test_long_inline_json_is_not_treated_as_a_filesystem_path(self) -> None:
        payload = {"request": "x" * 5000, "context": {"scope": "ui"}}
        inline = json.dumps(payload)
        self.assertEqual(_CLI._read_json(inline), payload)


if __name__ == "__main__":
    unittest.main()
