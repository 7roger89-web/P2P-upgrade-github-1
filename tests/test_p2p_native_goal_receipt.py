from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities.native_goal_bridge import CLAUDE_CODE, CODEX_CLI  # noqa: E402
from p2p_capabilities.native_goal_receipt import (  # noqa: E402
    INVOKED,
    LEDGER_EVENT,
    UNAVAILABLE,
    append_receipt,
    build_receipt,
    read_receipts,
    validate_receipt,
)


class TestNativeGoalInvocationReceipt(unittest.TestCase):
    def test_claude_invoked_requires_goal_status_view(self) -> None:
        receipt = build_receipt(
            host_kind=CLAUDE_CODE,
            goal_id="goal-1",
            state=INVOKED,
            proof_kind="CLAUDE_GOAL_STATUS_VIEW",
            reason="active goal status observed in current Claude Code session",
            observed_at="2026-09-16T06:00:00+00:00",
        )
        self.assertTrue(validate_receipt(receipt))
        self.assertFalse(receipt["raw_goal_stored"])
        self.assertFalse(receipt["raw_command_stored"])
        self.assertFalse(receipt["acceptance_authority"])

    def test_codex_invoked_requires_codex_status_view(self) -> None:
        receipt = build_receipt(
            host_kind=CODEX_CLI,
            goal_id="goal-2",
            state=INVOKED,
            proof_kind="CODEX_GOAL_STATUS_VIEW",
            reason="active goal status observed in current Codex CLI thread",
        )
        self.assertTrue(validate_receipt(receipt))

    def test_activation_decision_or_probe_cannot_fake_invoked(self) -> None:
        with self.assertRaisesRegex(ValueError, "INVOKED_REQUIRES_HOST_GOAL_STATUS_VIEW"):
            build_receipt(
                host_kind=CLAUDE_CODE,
                goal_id="goal-3",
                state=INVOKED,
                proof_kind="HOST_PROBE",
                reason="probe says ready",
            )

    def test_unavailable_can_record_probe_failure(self) -> None:
        receipt = build_receipt(
            host_kind=CODEX_CLI,
            goal_id="goal-4",
            state=UNAVAILABLE,
            proof_kind="HOST_PROBE",
            reason="CODEX_GOALS_DISABLED",
        )
        self.assertTrue(validate_receipt(receipt))

    def test_receipt_appends_to_existing_execution_ledger_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt = build_receipt(
                host_kind=CLAUDE_CODE,
                goal_id="goal-5",
                state=INVOKED,
                proof_kind="CLAUDE_GOAL_STATUS_VIEW",
                reason="active goal status observed",
                observed_at="2026-09-16T06:00:00+00:00",
            )
            result = append_receipt(receipt, root)
            self.assertEqual(result["status"], "RECORDED")
            ledger = root / ".p2p" / "state" / "execution-ledger.jsonl"
            event = json.loads(ledger.read_text(encoding="utf-8").strip())
            self.assertEqual(event["schema_version"], "p2p-execution-event/1")
            self.assertEqual(event["event"], LEDGER_EVENT)
            self.assertEqual(event["receipt"]["goal_id"], "goal-5")
            serialized = ledger.read_text(encoding="utf-8")
            self.assertNotIn("/goal ", serialized)
            self.assertNotIn("Complete P2P goal", serialized)

    def test_exact_receipt_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            receipt = build_receipt(
                host_kind=CODEX_CLI,
                goal_id="goal-6",
                state=UNAVAILABLE,
                proof_kind="HOST_NATIVE_REJECTION",
                reason="native goal command rejected by current host surface",
                observed_at="2026-09-16T06:00:00+00:00",
            )
            first = append_receipt(receipt, temp)
            second = append_receipt(receipt, temp)
            self.assertEqual(first["status"], "RECORDED")
            self.assertEqual(second["status"], "DUPLICATE")
            self.assertEqual(len(read_receipts(temp)), 1)

    def test_secret_like_reason_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "REASON_INVALID"):
            build_receipt(
                host_kind=CODEX_CLI,
                goal_id="goal-7",
                state=UNAVAILABLE,
                proof_kind="HOST_PROBE",
                reason="token=supersecretvalue",
            )


if __name__ == "__main__":
    unittest.main()
