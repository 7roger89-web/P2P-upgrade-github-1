from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCTOR = REPO_ROOT / "scripts" / "doctor.py"


class P2PDoctorRoleTests(unittest.TestCase):
    def test_development_checkout_is_not_inferred_as_portable(self) -> None:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import doctor  # noqa: PLC0415

        self.assertEqual(doctor.infer_role(REPO_ROOT), "development")

    def test_package_mode_reports_role_mismatch_instead_of_payload_noise(self) -> None:
        result = subprocess.run(
            [sys.executable, str(DOCTOR), "--package", str(REPO_ROOT), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["role"], "portable")
        self.assertEqual(payload["detected_role"], "development")
        self.assertEqual([item["check"] for item in payload["checks"]], ["role"])


if __name__ == "__main__":
    unittest.main()
