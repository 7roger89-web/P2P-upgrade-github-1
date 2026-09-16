from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.native_code_impact import native_code_impact_summary  # noqa: E402


class NativeCodeImpactRealWorktreeTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def _write(self, root: Path, relative: str, text: str) -> None:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def _baseline_repo(self, root: Path) -> str:
        self._git(root, "init", "-q")
        self._git(root, "config", "user.email", "p2p-test@example.invalid")
        self._git(root, "config", "user.name", "P2P Test")
        self._write(
            root,
            "src/core.py",
            "def calculate_total(value):\n    return value * 2\n",
        )
        self._write(
            root,
            "src/orders.py",
            "import src.core\n\ndef order_total(value):\n    return src.core.calculate_total(value)\n",
        )
        self._write(
            root,
            "tests/test_orders.py",
            "import src.orders\n\ndef test_order_total():\n    assert src.orders.order_total(2) == 4\n",
        )
        self._write(root, "docs/readme.md", "baseline\n")
        self._git(root, "add", ".")
        self._git(root, "commit", "-qm", "baseline")
        return self._git(root, "rev-parse", "HEAD")

    def test_modified_python_file_captures_dependents_tests_and_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = self._baseline_repo(root)
            self._write(
                root,
                "src/core.py",
                "def calculate_total(value):\n    return value * 3\n",
            )

            evidence = native_code_impact_summary(root, baseline)

            self.assertEqual(evidence["status"], "PASS")
            self.assertEqual(evidence["native_scope_status"], "FULL")
            self.assertFalse(evidence["external_extension_recommended"])
            self.assertIn(
                "src/orders",
                evidence["impact"]["direct_dependents"].get("src/core", ()),
            )
            self.assertIn("tests/test_orders", evidence["impact"]["tests_affected"])
            symbol_rows = {
                row["path"]: row["symbols"] for row in evidence["changed_symbols"]
            }
            self.assertIn("calculate_total", symbol_rows["src/core.py"])
            self.assertFalse(evidence["repository_mutated"])

    def test_deleted_python_file_keeps_baseline_dependents_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = self._baseline_repo(root)
            (root / "src/core.py").unlink()

            evidence = native_code_impact_summary(root, baseline)

            self.assertEqual(evidence["status"], "PASS")
            self.assertEqual(
                evidence["graph_semantics"],
                "BASELINE_UNION_CURRENT_NATIVE_AST",
            )
            self.assertIn(
                "src/orders",
                evidence["impact"]["direct_dependents"].get("src/core", ()),
            )
            self.assertIn("tests/test_orders", evidence["impact"]["tests_affected"])
            symbol_rows = {
                row["path"]: row["symbols"] for row in evidence["changed_symbols"]
            }
            self.assertIn("calculate_total", symbol_rows["src/core.py"])

    def test_unsupported_code_language_surfaces_native_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = self._baseline_repo(root)
            self._write(root, "web/app.ts", "export const answer = 42;\n")

            evidence = native_code_impact_summary(root, baseline)

            self.assertEqual(evidence["status"], "PARTIAL")
            self.assertEqual(evidence["native_scope_status"], "PARTIAL")
            self.assertEqual(evidence["unsupported_code_files"], ["web/app.ts"])
            self.assertTrue(evidence["external_extension_recommended"])
            self.assertIn("web/app.ts", evidence["native_gap_reason"])

    def test_docs_only_change_is_not_applicable_to_code_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = self._baseline_repo(root)
            self._write(root, "docs/readme.md", "changed docs only\n")

            evidence = native_code_impact_summary(root, baseline)

            self.assertEqual(evidence["status"], "NOT_APPLICABLE")
            self.assertEqual(evidence["native_scope_status"], "NOT_APPLICABLE")
            self.assertIsNone(evidence["impact"])
            self.assertFalse(evidence["external_extension_recommended"])

    def test_release_runtime_transports_native_and_optional_code_intelligence(self) -> None:
        package_path = REPO_ROOT / "scripts" / "package_release.py"
        spec = importlib.util.spec_from_file_location("p2p_package_release", package_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        package = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(package)

        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp) / "stage"
            stage.mkdir()
            package.copy_foundation_runtime(REPO_ROOT, stage)
            runtime = stage / "runtime" / "p2p_capabilities"

            self.assertTrue((runtime / "quality_intelligence.py").is_file())
            self.assertTrue((runtime / "native_code_impact.py").is_file())
            self.assertTrue((runtime / "code_intelligence_bridge.py").is_file())
            self.assertFalse((runtime / "tests").exists())


if __name__ == "__main__":
    unittest.main()
