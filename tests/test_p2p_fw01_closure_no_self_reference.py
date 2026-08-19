"""P2P-FRAMEWORK-01 closure self-reference guard regression test.

A closure/cleanup script must never embed a reference to the commit it is
currently amending: that is a self-referential git ancestry loop that cannot
stabilize (proven incident in FW01 development, 2026-08-19).

Deterministic checks:
- fill script reads its target SHA from an external lineage file, never from
  git rev-parse HEAD;
- if the target SHA equals current HEAD, the script exits non-zero
  (SELF_REFERENCE_GUARD) and mutates NOTHING;
- lineage files must reference an ancestor commit (parent or older), never
  HEAD itself.
"""
import subprocess
import unittest

import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
FILL_SCRIPT = REPO / ".tmp" / "fw01_fill_report.py"
LINEAGE_FILE = REPO / ".tmp" / "fw01_lineage_sha.txt"
HEAD_FILE = REPO / ".tmp" / "fw01_head_sha.txt"


def git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()


def git_parent(depth: int = 1) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"HEAD~{depth}"], cwd=REPO).decode().strip()


class ClosureSelfReferenceGuardTests(unittest.TestCase):
    """Guard: closure write targets must never equal the commit being amended."""

    def setUp(self) -> None:
        self.head = git_sha()
        self.parent = git_parent(1)

    def _run_fill(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(FILL_SCRIPT)], cwd=REPO,
            capture_output=True, text=True)

    def test_lineage_file_referencing_head_is_rejected(self) -> None:
        """Embedding the amended commit's own SHA must be rejected."""
        LINEAGE_FILE.write_text(self.head, encoding="utf-8")
        HEAD_FILE.write_text(self.head, encoding="utf-8")
        result = self._run_fill()
        self.assertNotEqual(result.returncode, 0,
                            "self-reference must be rejected (non-zero exit)")
        self.assertIn("SELF_REFERENCE_GUARD",
                      (result.stderr or "") + (result.stdout or ""))

    def test_lineage_file_referencing_invalid_sha_is_rejected(self) -> None:
        LINEAGE_FILE.write_text("not-a-sha", encoding="utf-8")
        HEAD_FILE.write_text(self.head, encoding="utf-8")
        result = self._run_fill()
        self.assertNotEqual(result.returncode, 0)

    def test_lineage_file_referencing_ancestor_is_accepted(self) -> None:
        """A non-self-referential ancestor SHA must be accepted."""
        LINEAGE_FILE.write_text(self.parent, encoding="utf-8")
        HEAD_FILE.write_text(self.head, encoding="utf-8")
        result = self._run_fill()
        self.assertEqual(result.returncode, 0,
                         msg=(result.stdout or "") + (result.stderr or ""))
        self.assertIn(self.parent,
                      REPO.joinpath("governance/development-control.json")
                      .read_text(encoding="utf-8"))
        self.assertIn(self.parent,
                      REPO.joinpath(
                          "docs/p2p-development/reports/"
                          "P2P-FRAMEWORK-01-terminal-report.md")
                      .read_text(encoding="utf-8"))

    def test_fill_script_never_calls_rev_parse_head(self) -> None:
        """The fill script must not derive the target SHA from HEAD."""
        src = FILL_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("rev-parse", src,
                         "fill script must read lineage from an external file, "
                         "never from git rev-parse HEAD")
        self.assertNotIn("git_sha", src)


if __name__ == "__main__":
    unittest.main()
