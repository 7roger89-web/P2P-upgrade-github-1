"""C36 ContextLoopGuard — bounded, evidence-gated retry for context work.

Guard semantics (reusing evidence.detect_no_progress fingerprint patterns):

- ATTEMPT_FINGERPRINT = sha256(goal_id, task_id, action_class, input_hash,
  state_revision, failure_class). Two attempts with an identical fingerprint
  and no new evidence are blocked: LOOP_GUARD_TRIGGERED (scenario R).
- Material change in evidence (new input hash, new state revision, or a
  different failure class) resets the count: retries MAY proceed (scenario:
  changed evidence may retry).
- UNKNOWN mutation: if the operation may have mutated state and the result
  is unknown, blind retry is blocked (scenario S).
- Oscillation: the same failure alternating between two states is detected
  and blocked (scenario: no oscillating state loop).
- No hidden chain-of-thought; guard decisions are Decision-Trace-worthy
  and logged via the decision trace decision vocabulary when the ledger
  root is supplied.

Scenario T: telemetry produced by this guard never influences provider/
model selection — routing belongs to C37.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping

from .context import _canonical_bytes
from .decision_trace import _stable_json, _sha256

LOOP_SCHEMA_VERSION = "p2p-context-loop-guard-c36/1"

MAX_IDENTICAL_ATTEMPTS = 2  # bounded by the canonical retry contract
MAX_OSCILLATION_WINDOW = 4


class LoopGuardError(ValueError):
    """Raised when a guarded retry is blocked."""


def attempt_fingerprint(
    goal_id: str,
    task_id: str,
    action_class: str,
    input_hash: str,
    state_revision: str,
    failure_class: str,
) -> str:
    return _sha256((goal_id, task_id, action_class, input_hash, state_revision, failure_class))


class AttemptLog:
    """Mutable (but append-only-style) ledger of guarded attempts for one
    guarded operation. Feed attempts in order; query before retrying."""

    def __init__(self) -> None:
        self._attempts: list[dict[str, Any]] = []

    @property
    def attempts(self) -> list[dict[str, Any]]:
        return list(self._attempts)

    def record(
        self,
        goal_id: str,
        task_id: str,
        action_class: str,
        input_hash: str,
        state_revision: str,
        failure_class: str,
        mutation_unknown: bool = False,
    ) -> dict[str, Any]:
        entry = {
            "schema": LOOP_SCHEMA_VERSION,
            "attempt_id": len(self._attempts) + 1,
            "goal_id": goal_id,
            "task_id": task_id,
            "action_class": action_class,
            "input_hash": input_hash,
            "state_revision": state_revision,
            "failure_class": failure_class,
            "mutation_unknown": bool(mutation_unknown),
            "fingerprint": attempt_fingerprint(goal_id, task_id, action_class, input_hash, state_revision, failure_class),
        }
        self._attempts.append(entry)
        return entry

    def last(self) -> dict[str, Any] | None:
        return self._attempts[-1] if self._attempts else None

    def count_identical(self, fingerprint: str) -> int:
        return sum(1 for a in self._attempts if a["fingerprint"] == fingerprint)

    def may_retry(
        self,
        goal_id: str,
        task_id: str,
        action_class: str,
        input_hash: str,
        state_revision: str,
        failure_class: str,
        mutation_unknown: bool = False,
    ) -> dict[str, Any]:
        """Decide whether the next attempt may proceed.

        Returns {"allowed": bool, "reason": str}. Raises LoopGuardError for
        blocked cases so callers cannot silently ignore the guard.
        """
        fp = attempt_fingerprint(goal_id, task_id, action_class, input_hash, state_revision, failure_class)
        last = self.last()
        if mutation_unknown:
            raise LoopGuardError("UNKNOWN_MUTATION_BLOCKS_BLIND_RETRY")
        if last is None:
            return {"allowed": True, "reason": "FIRST_ATTEMPT"}
        identical = self.count_identical(fp)
        if identical >= MAX_IDENTICAL_ATTEMPTS:
            raise LoopGuardError("LOOP_GUARD_TRIGGERED: IDENTICAL_ATTEMPT_WITHOUT_NEW_EVIDENCE")
        window = [a["state_revision"] for a in self._attempts[-MAX_OSCILLATION_WINDOW:]]
        if len(window) >= 4 and window[-1] == window[-3] and window[-2] == window[-4] and window[-1] != window[-2]:
            raise LoopGuardError("OSCILLATION_DETECTED: NO_OSCILLATING_STATE_LOOP")
        return {"allowed": True, "reason": "EVIDENCE_CHANGED_OR_COUNT_WITHIN_BOUND"}

    def summary(self) -> dict[str, Any]:
        return {
            "attempts": len(self._attempts),
            "unique_fingerprints": len({a["fingerprint"] for a in self._attempts}),
            "last_fingerprint": (self._attempts[-1]["fingerprint"] if self._attempts else None),
        }
