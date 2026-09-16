from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / ".p2p" / "system" / "p2p_capabilities" / "open_code_review_bridge.py"
spec = importlib.util.spec_from_file_location("open_code_review_bridge", MODULE)
ocr = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ocr)


class FakeRunner:
    def __init__(self, *, version: str = "open-code-review v1.12.4") -> None:
        self.version = version
        self.calls = []

    def __call__(self, invocation):
        self.calls.append(invocation)
        argv = invocation.argv
        if argv[1:] == ("version",):
            return subprocess.CompletedProcess(argv, 0, stdout=self.version, stderr="")
        if argv[1:3] == ("delegate", "preview"):
            payload = {
                "schema_version": "1",
                "mode": "range",
                "from": "main",
                "to": "feature",
                "merge_base": "abc123",
                "reviewable_files": [
                    {"path": "src/a.py", "status": "modified", "insertions": 10, "deletions": 2},
                    {"path": "src/b.py", "status": "added", "insertions": 20, "deletions": 0},
                ],
                "excluded_files": [{"path": "dist/app.js", "reason": "generated"}],
            }
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload), stderr="")
        if argv[1:3] == ("delegate", "rule"):
            payload = [{"files": ["src/a.py", "src/b.py"], "rule": "Check correctness and tests."}]
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload), stderr="")
        return subprocess.CompletedProcess(argv, 9, stdout="", stderr="unexpected command")


class OpenCodeReviewBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="p2p-ocr-")
        self.root = Path(self.temp.name)
        (self.root / ".git").mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def bridge(self, runner: FakeRunner | None = None):
        runner = runner or FakeRunner()
        return ocr.OpenCodeReviewDelegationBridge(runner=runner, which=lambda _: "/usr/bin/ocr"), runner

    def test_preview_requires_documented_review_gap(self) -> None:
        bridge, _ = self.bridge()
        with self.assertRaisesRegex(ocr.UnsafeOpenCodeReviewRequest, "OCR_REVIEW_GAP_REASON_REQUIRED"):
            bridge.build_preview_invocation(repo_root=self.root, gap_reason="tiny")

    def test_preview_rejects_conflicting_target_modes(self) -> None:
        bridge, _ = self.bridge()
        with self.assertRaisesRegex(ocr.UnsafeOpenCodeReviewRequest, "OCR_TARGET_MODE_CONFLICT"):
            bridge.build_preview_invocation(
                repo_root=self.root,
                gap_reason="large diff coverage needs deterministic file accounting",
                commit="deadbeef",
                from_ref="main",
                to_ref="feature",
            )

    def test_missing_binary_fails_without_installing_or_configuring_anything(self) -> None:
        bridge = ocr.OpenCodeReviewDelegationBridge(
            runner=FakeRunner(), which=lambda _: None
        )
        with self.assertRaisesRegex(ocr.OpenCodeReviewUnavailable, "OCR_NOT_INSTALLED"):
            bridge.preview(
                repo_root=self.root,
                gap_reason="large diff coverage needs deterministic file accounting",
                from_ref="main",
                to_ref="feature",
            )

    def test_old_cli_fails_closed_instead_of_silently_parsing_text(self) -> None:
        bridge, _ = self.bridge(FakeRunner(version="open-code-review v1.8.10"))
        with self.assertRaisesRegex(ocr.OpenCodeReviewUnavailable, "OCR_VERSION_TOO_OLD"):
            bridge.preview(
                repo_root=self.root,
                gap_reason="large diff coverage needs deterministic file accounting",
                from_ref="main",
                to_ref="feature",
            )

    def test_preview_is_delegation_only_non_authoritative_and_complete(self) -> None:
        bridge, runner = self.bridge()
        result = bridge.preview(
            repo_root=self.root,
            gap_reason="large diff coverage needs deterministic file accounting",
            from_ref="main",
            to_ref="feature",
            background="Preserve auth semantics and regression tests.",
        )
        self.assertEqual(result["classification"], "NON_AUTHORITATIVE_REVIEW_SCAFFOLD")
        self.assertFalse(result["acceptance_authority"])
        self.assertEqual(result["permission_effect"], "NONE")
        self.assertTrue(result["host_agent_must_review"])
        self.assertTrue(result["native_shield_still_required"])
        self.assertEqual([x["path"] for x in result["reviewable_files"]], ["src/a.py", "src/b.py"])
        preview_call = runner.calls[-1]
        self.assertEqual(preview_call.argv[:3], ("ocr", "delegate", "preview"))
        self.assertIn("--format", preview_call.argv)
        self.assertNotIn("review", preview_call.argv)
        self.assertNotIn("llm", preview_call.argv)

    def test_background_is_bounded_not_silently_truncated(self) -> None:
        bridge, _ = self.bridge()
        with self.assertRaisesRegex(ocr.UnsafeOpenCodeReviewRequest, "OCR_BACKGROUND_TOO_LARGE"):
            bridge.build_preview_invocation(
                repo_root=self.root,
                gap_reason="large diff coverage needs deterministic file accounting",
                background="x" * (ocr.MAX_BACKGROUND_CHARS + 1),
            )

    def test_rules_use_only_delegate_rule_and_return_no_authority(self) -> None:
        bridge, runner = self.bridge()
        result = bridge.rules(
            repo_root=self.root,
            paths=["src/a.py", "src/b.py"],
            gap_reason="rule targeting is not established by native review evidence",
        )
        self.assertFalse(result["acceptance_authority"])
        call = runner.calls[-1]
        self.assertEqual(call.argv[:3], ("ocr", "delegate", "rule"))
        self.assertNotIn("review", call.argv)
        self.assertNotIn("llm", call.argv)

    def test_host_contract_accounts_for_every_previewed_file(self) -> None:
        bridge, _ = self.bridge()
        preview = bridge.preview(
            repo_root=self.root,
            gap_reason="large diff coverage needs deterministic file accounting",
            from_ref="main",
            to_ref="feature",
        )
        rules = bridge.rules(
            repo_root=self.root,
            paths=["src/a.py", "src/b.py"],
            gap_reason="rule targeting is not established by native review evidence",
        )
        contract = ocr.build_host_review_contract(preview, rules)
        self.assertEqual(contract["total_files"], 2)
        self.assertEqual(contract["completion_invariant"], "EVERY_PREVIEWED_FILE_ACCOUNTED_FOR")
        self.assertTrue(contract["shield_and_acceptance_replay_still_required"])
        self.assertEqual(
            {(x["path"], x["status"]) for x in contract["checklist"]},
            {("src/a.py", "modified"), ("src/b.py", "added")},
        )


if __name__ == "__main__":
    unittest.main()
