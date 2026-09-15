from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PLUGIN = (
    ROOT
    / "deployments"
    / "hermes-essential-stack"
    / "plugins"
    / "p2p-opik-observer"
)
TRANSPORT_REL = (
    Path("p2p_capabilities")
    / "hermes_plugins"
    / "p2p-opik-observer"
)
TRANSPORT_PLUGIN = ROOT / ".p2p" / "system" / TRANSPORT_REL
PACKAGE_RELEASE = ROOT / "scripts" / "package_release.py"

spec = importlib.util.spec_from_file_location("p2p_package_release", PACKAGE_RELEASE)
assert spec and spec.loader
package_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package_release)


class TestP2POpikDistribution(unittest.TestCase):
    def test_transport_projection_is_byte_identical_to_canonical_plugin(self) -> None:
        for name in ("__init__.py", "plugin.yaml"):
            canonical = CANONICAL_PLUGIN / name
            transport = TRANSPORT_PLUGIN / name
            self.assertTrue(canonical.is_file(), canonical)
            self.assertTrue(transport.is_file(), transport)
            self.assertEqual(canonical.read_bytes(), transport.read_bytes(), name)

    def test_release_runtime_carries_opik_transport_projection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            stage = Path(td)
            package_release.copy_foundation_runtime(ROOT, stage)
            staged = stage / "runtime" / TRANSPORT_REL
            for name in ("__init__.py", "plugin.yaml"):
                self.assertTrue((staged / name).is_file(), staged / name)
                self.assertEqual(
                    (TRANSPORT_PLUGIN / name).read_bytes(),
                    (staged / name).read_bytes(),
                    name,
                )

    def test_installers_recursively_project_foundation_runtime_into_projects(self) -> None:
        shell = (ROOT / "install.sh").read_text(encoding="utf-8")
        powershell = (ROOT / "install.ps1").read_text(encoding="utf-8")
        self.assertIn(
            'cp -a "$uiux_runtime/p2p_capabilities/." "$system_destination/p2p_capabilities/"',
            shell,
        )
        self.assertIn(
            'Copy-Item -Path (Join-Path $UiUxRuntime "p2p_capabilities\\*") -Destination $FoundationDestination -Recurse -Force',
            powershell,
        )


if __name__ == "__main__":
    unittest.main()
