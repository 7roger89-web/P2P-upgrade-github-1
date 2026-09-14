from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM_ROOT = os.path.join(REPO_ROOT, ".p2p", "system")
if SYSTEM_ROOT not in sys.path:
    sys.path.insert(0, SYSTEM_ROOT)

from p2p_capabilities.hermes_tool_bridges import (  # noqa: E402
    EPHEMERAL_CONTEXT_ARTIFACT,
    NON_AUTHORITATIVE_TELEMETRY,
    ExternalToolExecutionFailed,
    ExternalToolUnavailable,
    RepomixContextBridge,
    TokScaleTelemetryBridge,
    UnsafeBridgeRequest,
)


class TestRepomixContextBridge(unittest.TestCase):
    def test_command_is_bounded_and_pack_is_ephemeral(self):
        calls = []
        with tempfile.TemporaryDirectory() as target, tempfile.TemporaryDirectory() as outside:
            output = Path(outside) / "context.md"

            def runner(invocation):
                calls.append(invocation)
                output.write_text("packed context", encoding="utf-8")
                return subprocess.CompletedProcess(invocation.argv, 0, "ok", "")

            bridge = RepomixContextBridge(runner=runner, which=lambda _: "/fake/repomix")
            result = bridge.pack(
                root=target,
                output_path=output,
                token_budget=12000,
                compress=True,
                include=("src/**", "docs/**"),
                ignore=("dist/**",),
            )

        argv = calls[0].argv
        self.assertIn("--token-budget", argv)
        self.assertIn("12000", argv)
        self.assertIn("--compress", argv)
        self.assertNotIn("--remote", argv)
        self.assertNotIn("--remote-branch", argv)
        self.assertNotIn("--no-security-check", argv)
        self.assertEqual(result["classification"], EPHEMERAL_CONTEXT_ARTIFACT)
        self.assertFalse(result["authoritative_state"])
        self.assertEqual(len(result["sha256"]), 64)

    def test_output_inside_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as target:
            bridge = RepomixContextBridge(which=lambda _: "/fake/repomix")
            with self.assertRaisesRegex(UnsafeBridgeRequest, "OUTPUT_MUST_BE_OUTSIDE_TARGET"):
                bridge.build_invocation(
                    root=target,
                    output_path=Path(target) / "repomix-output.md",
                    token_budget=1000,
                )

    def test_token_budget_is_mandatory(self):
        with tempfile.TemporaryDirectory() as target, tempfile.TemporaryDirectory() as outside:
            bridge = RepomixContextBridge(which=lambda _: "/fake/repomix")
            with self.assertRaisesRegex(UnsafeBridgeRequest, "TOKEN_BUDGET_REQUIRED"):
                bridge.build_invocation(
                    root=target,
                    output_path=Path(outside) / "out.md",
                    token_budget=0,
                )

    def test_missing_binary_fails_honestly(self):
        bridge = RepomixContextBridge(which=lambda _: None)
        with self.assertRaisesRegex(ExternalToolUnavailable, "NOT_INSTALLED"):
            bridge.pack(root=".", output_path="/tmp/out.md", token_budget=1000)


class TestTokScaleTelemetryBridge(unittest.TestCase):
    def test_summary_is_json_read_only_telemetry(self):
        calls = []

        def runner(invocation):
            calls.append(invocation)
            return subprocess.CompletedProcess(
                invocation.argv, 0, '{"total_tokens":123,"cost_usd":0.45}', ""
            )

        bridge = TokScaleTelemetryBridge(runner=runner, which=lambda _: "/fake/tokscale")
        result = bridge.snapshot()
        self.assertEqual(calls[0].argv, ("tokscale", "--json"))
        self.assertEqual(result["classification"], NON_AUTHORITATIVE_TELEMETRY)
        self.assertFalse(result["authoritative_state"])
        self.assertEqual(result["payload"]["total_tokens"], 123)
        self.assertNotIn("submit", calls[0].argv)

    def test_supported_scopes_never_submit(self):
        bridge = TokScaleTelemetryBridge(which=lambda _: "/fake/tokscale")
        self.assertEqual(bridge.build_invocation(scope="models").argv, ("tokscale", "models", "--json"))
        self.assertEqual(bridge.build_invocation(scope="monthly").argv, ("tokscale", "monthly", "--json"))
        with self.assertRaisesRegex(UnsafeBridgeRequest, "SCOPE_UNSUPPORTED"):
            bridge.build_invocation(scope="submit")

    def test_invalid_json_fails_closed(self):
        def runner(invocation):
            return subprocess.CompletedProcess(invocation.argv, 0, "not-json", "")

        bridge = TokScaleTelemetryBridge(runner=runner, which=lambda _: "/fake/tokscale")
        with self.assertRaisesRegex(ExternalToolExecutionFailed, "JSON_INVALID"):
            bridge.snapshot()

    def test_missing_binary_fails_honestly(self):
        bridge = TokScaleTelemetryBridge(which=lambda _: None)
        with self.assertRaisesRegex(ExternalToolUnavailable, "NOT_INSTALLED"):
            bridge.snapshot()


if __name__ == "__main__":
    unittest.main()
