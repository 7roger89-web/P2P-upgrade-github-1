"""Minimal executable regression for the Issue #254 live blind-test gap.

This module deliberately uses only Control Tower surfaces that already existed
before the repair (``scripts/p2p_control_tower.py start`` and
``owner_goal.build_arena_handoff``). It therefore runs unchanged against the
pre-repair baseline, where it FAILS, and against the repaired runtime, where it
PASSES. That is the encoded form of the live defect:

a fresh Arena session received a real medium/high-risk task without manually
mentioning FAST_CANARY, and the generated execution context contained no canary
trigger, no stop boundary, and no external-grade/Owner-continuation handoff.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
for candidate in (str(SYSTEM_ROOT), str(SCRIPTS_ROOT), str(REPO_ROOT)):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import p2p_control_tower as control_tower  # noqa: E402
from p2p_capabilities import owner_goal  # noqa: E402

BLIND_TEST_TASK = (
    "Repair the Control Tower runtime so a new medium/high-risk Arena session "
    "stops at the FAST_CANARY boundary, mutating runtime prompt generation, "
    "ledger events and gates"
)
LOW_RISK_TASK = "Update the typo in the README changelog label"
REQUIRED_TOKENS = (
    "FAST_CANARY_REQUIRED=YES",
    "REAL_TASK_FIRST_SLICE=CANARY",
    "CANARY_DURABLE_MUTATION_ALLOWED=NO",
    "STOP_AFTER_CANARY=YES",
    "EXECUTOR_SELF_CLASSIFICATION=FORBIDDEN",
    "MODEL_IDENTITY=UNKNOWN",
    "CANARY_EVIDENCE_PACKET_V1",
    "CONTINUATION_CHECKPOINT=READY",
    "OWNER_ACTION_REQUIRED=YES",
    "NATIVE_ACTION_HINT=KEEP_WORKING_IF_APPROVED",
    "FALLBACK_OWNER_REPLY=Tiếp tục công việc",
)


class ArenaCanaryBaselineGapTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="p2p-canary-gap-")
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _start(self, *, host: str, goal: str, session_id: str) -> str:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = control_tower.main(
                [
                    "--root",
                    str(self.root),
                    "start",
                    "--host",
                    host,
                    "--goal-id",
                    "P2P-CT01-CANARY",
                    "--task-id",
                    "TASK-CANARY-1",
                    "--session-id",
                    session_id,
                    "--goal",
                    goal,
                    "--json",
                ]
            )
        self.assertEqual(0, code, buffer.getvalue())
        return json.loads(buffer.getvalue())["recommendation"]["PROMPT"]

    def test_control_tower_start_injects_fast_canary_for_new_arena_session(self) -> None:
        prompt = self._start(host="ARENA", goal=BLIND_TEST_TASK, session_id="gap-arena-1")
        for token in REQUIRED_TOKENS:
            self.assertIn(token, prompt)
        # The original real task must be preserved, not replaced by the canary.
        self.assertIn(BLIND_TEST_TASK, prompt)
        # Existing mandatory runtime context must survive.
        self.assertIn(control_tower.CONTEXT_MARKER, prompt)
        self.assertIn("OE_GATE=", prompt)
        self.assertIn("SUPREME_LAW_CAPSULE:", prompt)

    def test_owner_goal_arena_handoff_injects_fast_canary(self) -> None:
        handoff = owner_goal.build_arena_handoff(
            self.root,
            {"goal_id": "P2P-CT01-CANARY", "objective": BLIND_TEST_TASK},
            None,
            "ARENA",
            reuse=False,
        )
        for token in REQUIRED_TOKENS:
            self.assertIn(token, handoff["packet_text"])

    def test_low_risk_and_non_arena_sessions_still_bypass(self) -> None:
        low_risk = self._start(host="ARENA", goal=LOW_RISK_TASK, session_id="gap-low-risk")
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", low_risk)
        non_arena = self._start(host="CODEX", goal=BLIND_TEST_TASK, session_id="gap-codex")
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", non_arena)


if __name__ == "__main__":
    unittest.main()
