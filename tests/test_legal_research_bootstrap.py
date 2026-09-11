from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "research" / "legal-vn" / "upstreams.json"
SCRIPT = ROOT / "scripts" / "bootstrap_legal_research.py"

spec = importlib.util.spec_from_file_location("bootstrap_legal_research", SCRIPT)
assert spec and spec.loader
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class LegalResearchCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_catalog_schema_and_unique_ids(self) -> None:
        self.assertEqual(self.catalog["schema_version"], "p2p-legal-vn/upstreams/1")
        ids = [source["id"] for source in self.catalog["sources"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_clone_targets_are_separate_and_safe(self) -> None:
        dirs = []
        for source in bootstrap.cloneable_sources(self.catalog):
            local_dir = Path(source["local_dir"])
            self.assertFalse(local_dir.is_absolute())
            self.assertNotIn("..", local_dir.parts)
            self.assertTrue(source["url"].startswith("https://github.com/"))
            dirs.append(source["local_dir"])
        self.assertEqual(len(dirs), len(set(dirs)))

    def test_unclear_license_is_research_only(self) -> None:
        unclear = {"VERIFY_BEFORE_REUSE", "NOASSERTION", "NONE_DETECTED_BY_GITHUB"}
        for source in self.catalog["sources"]:
            if source["license_signal"] in unclear:
                self.assertIn("RESEARCH_ONLY", source["reuse_policy"])

    def test_refuses_to_overwrite_nonempty_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "repo"
            target.mkdir()
            (target / "marker.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                bootstrap.ensure_target_is_safe(target)

    def test_clone_command_is_shallow_and_uses_double_dash(self) -> None:
        source = bootstrap.cloneable_sources(self.catalog)[0]
        command = bootstrap.build_clone_command(source, Path("/tmp/example"))
        self.assertEqual(command[:5], ["git", "clone", "--depth", "1", "--"])
        self.assertEqual(command[5], source["url"])


if __name__ == "__main__":
    unittest.main()
