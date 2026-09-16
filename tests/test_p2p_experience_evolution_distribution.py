from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "scripts" / "package_release.py"


class ExperienceEvolutionDistributionTests(unittest.TestCase):
    def test_existing_release_runtime_transports_experience_evolution(self) -> None:
        spec = importlib.util.spec_from_file_location("package_release", PACKAGE)
        package = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(package)
        with tempfile.TemporaryDirectory(prefix="p2p-exp-release-") as td:
            stage = Path(td) / "stage"
            stage.mkdir()
            package.copy_foundation_runtime(ROOT, stage)
            runtime = stage / "runtime" / "p2p_capabilities"
            self.assertTrue((runtime / "experience_evolution.py").is_file())
            self.assertTrue((runtime / "experience_federation.py").is_file())
            self.assertTrue((runtime / "shared_experience_catalog.json").is_file())
            self.assertTrue((runtime / "capability_intelligence.py").is_file())
            self.assertFalse(any(runtime.glob("test_*.py")))


if __name__ == "__main__":
    unittest.main()
