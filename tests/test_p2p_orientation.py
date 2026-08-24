"""Behavior tests for the RF01 managed README orientation contract."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.p2p_orientation import (
    BEGIN_MARKER,
    END_MARKER,
    OrientationError,
    extract_managed_block,
    render_managed_block,
    update_readme,
)


ROOT = Path(__file__).resolve().parent.parent
ORIENTATION = ROOT / "README.md"
MANAGED_CONTENT = "## Managed\n\nstate: UNKNOWN\n"


class OrientationTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture_parent = ROOT / ".tmp"
        fixture_parent.mkdir(parents=True, exist_ok=True)
        self.fixture_root = Path(
            tempfile.mkdtemp(prefix="rf01-orientation-", dir=fixture_parent)
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.fixture_root, ignore_errors=True)

    def test_append_when_markers_absent_preserves_owner_prefix(self) -> None:
        readme = self.fixture_root / "README.md"
        owner_prefix = "# Owner text\r\n\r\nKeep this exactly.\r\n"
        readme.write_bytes(owner_prefix.encode("utf-8"))

        result = update_readme(readme, MANAGED_CONTENT)

        self.assertTrue(result.changed)
        self.assertFalse(result.created)
        updated = readme.read_bytes()
        self.assertTrue(updated.startswith(owner_prefix.encode("utf-8")))
        self.assertEqual(updated.count(BEGIN_MARKER.encode()), 1)
        self.assertEqual(updated.count(END_MARKER.encode()), 1)

    def test_replacement_preserves_prefix_and_suffix_bytes(self) -> None:
        prefix = b"# Owner\r\n\r\n"
        old_block = (
            BEGIN_MARKER.encode()
            + b"\r\nold\r\n"
            + END_MARKER.encode()
        )
        suffix = b"\r\n\r\n## Owner tail\r\n"
        readme = self.fixture_root / "README.md"
        readme.write_bytes(prefix + old_block + suffix)

        result = update_readme(readme, MANAGED_CONTENT)

        self.assertTrue(result.changed)
        updated = readme.read_bytes()
        begin = updated.index(BEGIN_MARKER.encode())
        end = updated.index(END_MARKER.encode()) + len(END_MARKER)
        self.assertEqual(updated[: len(prefix)], prefix)
        self.assertEqual(updated[-len(suffix) :], suffix)
        self.assertEqual(updated[begin:end], render_managed_block(MANAGED_CONTENT).encode())

    def test_second_update_is_idempotent(self) -> None:
        readme = self.fixture_root / "README.md"
        update_readme(readme, MANAGED_CONTENT)
        first = readme.read_bytes()

        result = update_readme(readme, MANAGED_CONTENT)

        self.assertFalse(result.changed)
        self.assertEqual(readme.read_bytes(), first)

    def test_ambiguous_markers_fail_closed_without_write(self) -> None:
        readme = self.fixture_root / "README.md"
        original = (
            f"{BEGIN_MARKER}\nold\n{END_MARKER}\n"
            f"{BEGIN_MARKER}\nsecond\n{END_MARKER}\n"
        ).encode("utf-8")
        readme.write_bytes(original)

        with self.assertRaises(OrientationError):
            update_readme(readme, MANAGED_CONTENT)

        self.assertEqual(readme.read_bytes(), original)

    def test_one_sided_marker_and_marker_in_content_fail_closed(self) -> None:
        readme = self.fixture_root / "README.md"
        readme.write_text(f"{BEGIN_MARKER}\nmissing end\n", encoding="utf-8")
        with self.assertRaises(OrientationError):
            update_readme(readme, MANAGED_CONTENT)

        fresh = self.fixture_root / "fresh.md"
        with self.assertRaises(OrientationError):
            update_readme(fresh, f"text\n{BEGIN_MARKER}")
        self.assertFalse(fresh.exists())

    def test_root_readme_is_compact_and_routes_to_deep_surfaces(self) -> None:
        text = ORIENTATION.read_text(encoding="utf-8")
        self.assertEqual(text.count(BEGIN_MARKER), 1)
        self.assertEqual(text.count(END_MARKER), 1)
        self.assertLessEqual(text.count("\n"), 300)
        self.assertIn("OFFICIAL_CANONICAL_BASELINE=.19", text)
        self.assertIn("EXTERNAL_HOST_CAPABILITY_LIMITATION", text)
        self.assertIn("NORMAL FEATURE", text)
        self.assertIn("AUTHORITY / RELEASE", text)
        self.assertIn("UNKNOWN", text)
        self.assertIn("docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md", text)
        self.assertIn("GOAL PASS != PROMOTED", text)

    def test_extract_reports_absence_and_valid_block(self) -> None:
        self.assertIsNone(extract_managed_block("# owner\n"))
        block = render_managed_block(MANAGED_CONTENT)
        self.assertEqual(extract_managed_block(block), block)


if __name__ == "__main__":
    unittest.main()
