"""FRAMEWORK-01 operating-loop guard.

Extends the existing context_loop_guard attempt machinery (attempt
fingerprinting, identical-attempt cap, oscillation window) to the whole
loop iteration, not only individual context retries.

Detects (Owner contract §22):
- repeated same task with no new evidence;
- alternating task cycle (A->B->A with no progress);
- repeated verifier failure;
- unchanged state across iterations;
- retry exhaustion;
- stale project revision;
- contradictory evidence.

On detection: STOP_FAIL_CLOSED with durable evidence. No endless autonomy.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

GUARD_SCHEMA = "p2p-loop-guard-fw01/1"

MAX_IDENTICAL_ATTEMPTS = 2            # same (goal, task, action, input, state)
MAX_OSCILLATION_WINDOW = 4            # back-and-forth without progress
MAX_VERIFIER_FAILURES = 3             # repeated verifier CONTRADICTED/INCOMPLETE
MAX_IDENTICAL_STATE_ITERATIONS = 3    # checkpoint fingerprint unchanged

STOP_CAUSES = (
    "IDENTICAL_ATTEMPT_LIMIT",
    "OSCILLATION_DETECTED",
    "VERIFIER_FAILURE_EXHAUSTED",
    "STATE_UNCHANGED_EXHAUSTED",
    "RETRY_EXHAUSTED",
    "PROJECT_REVISION_STALE",
    "EVIDENCE_CONTRADICTED",
    "UNKNOWN_FAILURE_CLASS",
)


def _sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


class IterationRecord:
    """Compact per-iteration record for the guard ledger."""
    __slots__ = ("iteration", "task_id", "action", "state_hash",
                 "attempt_hash", "verifier_status", "at", "extra")

    def __init__(self, *, iteration: int, task_id: str, action: str,
                 state_hash: str, attempt_hash: str,
                 verifier_status: str | None = None,
                 at: str | None = None,
                 extra: dict | None = None) -> None:
        self.iteration = iteration
        self.task_id = task_id
        self.action = action
        self.state_hash = state_hash
        self.attempt_hash = attempt_hash
        self.verifier_status = verifier_status
        self.at = at or datetime.now(timezone.utc).isoformat()
        self.extra = extra or {}


class LoopGuard:
    """Append-only guard ledger + detection logic."""

    def __init__(self, ledger_path: Path, *, expected_project_revision: str | None = None) -> None:
        self.ledger_path = ledger_path
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, Any]] = []
        self.expected_project_revision = expected_project_revision
        if ledger_path.exists():
            for line in ledger_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    self.records.append(json.loads(line))

    # ---- ledger ------------------------------------------------------------

    def append(self, record: IterationRecord) -> None:
        payload = {
            "schema": GUARD_SCHEMA,
            "iteration": record.iteration,
            "task_id": record.task_id,
            "action": record.action,
            "state_hash": record.state_hash,
            "attempt_hash": record.attempt_hash,
            "verifier_status": record.verifier_status,
            "at": record.at,
            "extra": record.extra,
        }
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False,
                                    sort_keys=True) + "\n")
        self.records.append(payload)

    def _tail(self, n: int) -> list[dict[str, Any]]:
        return self.records[-n:]

    # ---- detection ---------------------------------------------------------

    def stop_cause(self) -> str | None:
        """Re-evaluate all detection rules against the current ledger.
        Returns the first triggered stop cause, or None when safe."""
        for fn in (self._identical_attempt_limit,
                   self._oscillation_detected,
                   self._verifier_failure_exhausted,
                   self._state_unchanged_exhausted,
                   self._evidence_contradicted):
            cause = fn()
            if cause:
                return cause
        if self.expected_project_revision and self.records:
            live = (self._tail(1)[0].get("extra") or {}).get("project_revision")
            if live and live != self.expected_project_revision:
                return "PROJECT_REVISION_STALE"
        return None

    def _identical_attempt_limit(self) -> str | None:
        tail = self._tail(MAX_IDENTICAL_ATTEMPTS + 1)
        if len(tail) < MAX_IDENTICAL_ATTEMPTS + 1:
            return None
        last = tail[-1]
        window = tail[:MAX_IDENTICAL_ATTEMPTS]
        if all(rec.get("attempt_hash") == last.get("attempt_hash")
               for rec in window):
            return "IDENTICAL_ATTEMPT_LIMIT"
        return None

    def _oscillation_detected(self) -> str | None:
        tail = self._tail(MAX_OSCILLATION_WINDOW)
        if len(tail) < MAX_OSCILLATION_WINDOW:
            return None
        tasks = [r.get("task_id") for r in tail]
        state_hashes = [r.get("state_hash") for r in tail]
        # Alternating A/B/A/B while state never advances: oscillation.
        if len(set(tasks)) == 2 and tasks[-1] == tasks[-3] \
                and tasks[-2] == tasks[-4] and len(set(state_hashes)) == 1:
            return "OSCILLATION_DETECTED"
        return None

    def _verifier_failure_exhausted(self) -> str | None:
        failures = [r for r in self.records[-MAX_VERIFIER_FAILURES:]
                    if r.get("verifier_status")
                    in ("CONTRADICTED", "INCOMPLETE", "UNKNOWN")]
        if len(failures) >= MAX_VERIFIER_FAILURES:
            return "VERIFIER_FAILURE_EXHAUSTED"
        return None

    def _state_unchanged_exhausted(self) -> str | None:
        tail = self._tail(MAX_IDENTICAL_STATE_ITERATIONS)
        if len(tail) < MAX_IDENTICAL_STATE_ITERATIONS:
            return None
        if len({r.get("state_hash") for r in tail}) == 1:
            return "STATE_UNCHANGED_EXHAUSTED"
        return None

    def _evidence_contradicted(self) -> str | None:
        for rec in self._tail(1):
            if (rec.get("verifier_status") == "CONTRADICTED"
                    and (rec.get("extra") or {}).get("evidence_conflict")):
                return "EVIDENCE_CONTRADICTED"
        return None

    def project_revision_check(self, project_revision: str | None) -> str | None:
        if not project_revision or not self.expected_project_revision:
            return None
        if project_revision != self.expected_project_revision:
            return "PROJECT_REVISION_STALE"
        return None

    def failure_class(self, label: str) -> str:
        """Map a runtime failure label to the failure taxonomy.
        Unknown classes fail closed."""
        label = str(label or "").strip().upper()
        known = re.sub(r"[^A-Z_]", "_", label)
        if known in STOP_CAUSES or known in (
                "AUTH", "PERMISSION", "PROJECT_DRIFT", "STATE_CORRUPTION",
                "NO_ELIGIBLE_TARGET", "PRE_DISPATCH_FAILURE",
                "POST_DISPATCH_UNKNOWN", "VERIFICATION_FAILURE",
                "RETRY_EXHAUSTED", "OWNER_GATE", "MATERIAL_SCOPE_EXPANSION",
                "LOOP_DETECTED"):
            return known
        return "UNKNOWN_FAILURE_CLASS"


def main(argv: list[str] | None = None) -> int:
    """CLI: python3 p2p_loop_guard.py check <ledger> [--project-revision REV]"""
    import sys
    args = (argv or sys.argv[1:])
    if not args or args[0] != "check":
        print("usage: p2p_loop_guard.py check <ledger-path> "
              "[--project-revision REV]", file=sys.stderr)
        return 2
    rev = None
    if "--project-revision" in args:
        idx = args.index("--project-revision")
        if idx + 1 < len(args):
            rev = args[idx + 1]
    guard = LoopGuard(Path(args[1]), expected_project_revision=rev)
    print(json.dumps({"stop_cause": guard.stop_cause(),
                      "iterations": len(guard.records)},
                     ensure_ascii=False, indent=2))
    return 0 if guard.stop_cause() is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
