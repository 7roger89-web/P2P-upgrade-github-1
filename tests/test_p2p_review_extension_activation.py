from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities import review_extension_activation as activation  # noqa: E402


class ReviewExtensionActivationTests(unittest.TestCase):
    def test_generic_review_without_runtime_gap_stays_off(self) -> None:
        decision = activation.review_gap_decision(
            "Review code",
            runtime_evidence={"signals": [], "read_only": True},
        )
        self.assertEqual("NO_REVIEW_GAP", decision["decision"])
        self.assertEqual([], decision["matched_signals"])

    def test_explicit_review_gap_still_activates(self) -> None:
        decision = activation.review_gap_decision(
            "This is the second repair round after omitted changed files",
            runtime_evidence={"signals": [], "read_only": True},
        )
        self.assertEqual("USE_OCR_DELEGATION", decision["decision"])
        self.assertIn("MISSED_FILE", decision["matched_signals"])
        self.assertIn("REPEATED_REPAIR", decision["matched_signals"])

    def test_failed_durable_session_activates_without_magic_words(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            ledger = root / activation.LEDGER_RELATIVE_PATH
            ledger.parent.mkdir(parents=True)
            ledger.write_text('{"SESSION_STATE":"FAILED"}\n', encoding="utf-8")
            before = ledger.read_bytes()

            decision = activation.review_gap_decision("Review code", root=root)

            self.assertEqual(before, ledger.read_bytes())
            self.assertEqual("USE_OCR_DELEGATION", decision["decision"])
            self.assertIn("RECENT_FAILED_OR_BLOCKED_SESSION", decision["matched_signals"])
            self.assertTrue(decision["runtime_evidence"]["read_only"])

    def test_host_cli_root_is_discovered_without_control_tower_coupling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            ledger = root / activation.LEDGER_RELATIVE_PATH
            ledger.parent.mkdir(parents=True)
            ledger.write_text('{"SESSION_STATE":"BLOCKED"}\n', encoding="utf-8")
            argv = ["p2p_control_tower.py", "--root", str(root), "start", "--host", "ARENA"]
            with mock.patch.object(sys, "argv", argv):
                decision = activation.review_gap_decision("Review code")
            self.assertEqual(root.resolve().as_posix(), decision["runtime_evidence"]["repo_root"])
            self.assertIn("RECENT_FAILED_OR_BLOCKED_SESSION", decision["matched_signals"])

    def test_large_real_worktree_diff_activates_from_git_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-b", "main", str(root)], check=True, capture_output=True, text=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "P2P Test"], check=True)
            (root / "seed.txt").write_text("seed\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "seed.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-m", "seed"], check=True, capture_output=True, text=True)
            for index in range(activation.LARGE_DIFF_FILE_THRESHOLD):
                (root / f"changed-{index:02d}.py").write_text(f"VALUE = {index}\n", encoding="utf-8")

            evidence = activation.runtime_review_evidence(root)
            decision = activation.review_gap_decision("Review code", runtime_evidence=evidence)

            self.assertGreaterEqual(evidence["changed_file_count"], activation.LARGE_DIFF_FILE_THRESHOLD)
            self.assertIn("LARGE_DIFF_RUNTIME", evidence["signals"])
            self.assertEqual("USE_OCR_DELEGATION", decision["decision"])
            self.assertIn("LARGE_DIFF_RUNTIME", decision["matched_signals"])

    def test_guidance_preserves_non_authority_and_native_fallback(self) -> None:
        guidance = activation.render_review_guidance(
            "Review code",
            runtime_evidence={"signals": ["LARGE_DIFF_RUNTIME"], "read_only": True},
        )
        self.assertIn("OPEN_CODE_REVIEW_DELEGATION=USE_IF_AVAILABLE", guidance)
        self.assertIn("NONAUTHORITATIVE", guidance)
        self.assertIn("NATIVE_REVIEW_FALLBACK", guidance)
        self.assertIn("never PASS-by-absence", guidance)


if __name__ == "__main__":
    unittest.main()
