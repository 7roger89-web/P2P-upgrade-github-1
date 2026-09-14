from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCTOR = REPO_ROOT / "scripts" / "doctor.py"
INSTALLED_SYSTEM = REPO_ROOT / ".p2p" / "system"
ALIAS_PACKAGE = "p2p_installed_p2p_capabilities"


class P2PDoctorRoleTests(unittest.TestCase):
    def test_development_checkout_is_not_inferred_as_portable(self) -> None:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import doctor  # noqa: PLC0415

        self.assertEqual(doctor.infer_role(REPO_ROOT), "development")

    def test_installed_project_pin_resolves_from_installed_runtime_only(self) -> None:
        """The Doctor validator must come from <target>/.p2p/system, never elsewhere."""

        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import doctor  # noqa: PLC0415

        saved_path = list(sys.path)
        saved_modules = {
            name: sys.modules[name]
            for name in list(sys.modules)
            if name == "p2p_capabilities"
            or name.startswith("p2p_capabilities.")
            or name == ALIAS_PACKAGE
            or name.startswith(f"{ALIAS_PACKAGE}.")
        }
        try:
            with tempfile.TemporaryDirectory(prefix="p2p-doctor-decoy-") as raw:
                decoy_package = Path(raw) / "p2p_capabilities"
                decoy_package.mkdir(parents=True)
                (decoy_package / "__init__.py").write_text("SENTINEL = 'decoy'\n", encoding="utf-8")
                (decoy_package / "project_pin.py").write_text(
                    "SENTINEL = 'decoy'\n\n\ndef validate_pin(*args, **kwargs):\n"
                    "    raise AssertionError('decoy validator must never run')\n",
                    encoding="utf-8",
                )
                # Worst case: the decoy package shadows the installed runtime on
                # PYTHONPATH and is already cached in sys.modules.
                sys.path.insert(0, raw)
                import p2p_capabilities  # noqa: PLC0415

                self.assertEqual(p2p_capabilities.SENTINEL, "decoy")

                module, expected = doctor._load_installed_project_pin(INSTALLED_SYSTEM)

                self.assertIsNotNone(module)
                self.assertEqual(Path(module.__file__).resolve(), expected.resolve())
                self.assertEqual(
                    expected.resolve(),
                    (INSTALLED_SYSTEM / "p2p_capabilities" / "project_pin.py").resolve(),
                )
                self.assertEqual(module.__package__, ALIAS_PACKAGE)
                self.assertFalse(hasattr(module, "SENTINEL"))
                self.assertTrue(callable(module.validate_pin))
        finally:
            sys.path[:] = saved_path
            for name in list(sys.modules):
                if name == "p2p_capabilities" or name.startswith(
                    ("p2p_capabilities.", f"{ALIAS_PACKAGE}.")
                ) or name == ALIAS_PACKAGE:
                    del sys.modules[name]
            sys.modules.update(saved_modules)

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
