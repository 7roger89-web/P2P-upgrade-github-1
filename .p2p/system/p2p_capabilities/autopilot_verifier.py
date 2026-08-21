"""Minimal deterministic verifier for synthetic C33 AutoPilot proofs.

Verification authority remains OUTSIDE executor self-claims: an executor
returning "done"/PASS only yields a `verdict_hint`. A task becomes DONE
only after acceptable verifier evidence. Verification failure transitions
into an explicit verifier state; PASS is never inferred from backend exit
codes or hints alone.

Reuses the canonical evidence vocabulary (.p2p.system.p2p_capabilities.evidence
statuses VERIFIED/INCOMPLETE/CONTRADICTED/NOT_APPLICABLE and freshness
CURRENT/FRESH) for normalized verifier outcomes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

VERIFIER_SCHEMA = "p2p-autopilot-verifier/1"

VERDICT_ACCEPTABLE = "ACCEPTABLE"
VERDICT_UNACCEPTABLE = "UNACCEPTABLE"
VERDICT_UNKNOWN = "UNKNOWN"
VERIFIER_VERDICTS = (VERDICT_ACCEPTABLE, VERDICT_UNACCEPTABLE, VERDICT_UNKNOWN)

EVIDENCE_VERIFIED = "VERIFIED"
EVIDENCE_INCOMPLETE = "INCOMPLETE"
EVIDENCE_CONTRADICTED = "CONTRADICTED"


def verdict_to_evidence_status(verdict: str, *, backend_outcome_acceptable: bool) -> str:
    if verdict == VERDICT_ACCEPTABLE and backend_outcome_acceptable:
        return EVIDENCE_VERIFIED
    if verdict == VERDICT_UNACCEPTABLE or not backend_outcome_acceptable:
        return EVIDENCE_CONTRADICTED
    return EVIDENCE_INCOMPLETE


class TaskVerifier:
    """Deterministic verifier. Verdict fixtures are keyed by task_id and
    consumed in registration order; empty registry yields UNACCEPTABLE for
    any backend PASS (fail-closed: done is never assumed).
    """

    def __init__(self) -> None:
        self._fixtures: dict[str, list[str]] = {}
        self._log: list[Mapping[str, Any]] = []

    def set_fixtures(self, fixtures: Mapping[str, Iterable[str]]) -> None:
        bad = [v for values in fixtures.values() for v in values if v not in VERIFIER_VERDICTS]
        if bad:
            raise ValueError(f"INVALID_VERDICT_FIXTURE:{bad[0]}")
        self._fixtures = {str(k): list(v) for k, v in fixtures.items()}

    def verify(self, execution_result: Mapping[str, Any], verify_spec: Iterable[str]) -> Mapping[str, Any]:
        task_id = str(execution_result.get("task_id", ""))
        spec = tuple(verify_spec)
        verdict = VERDICT_UNACCEPTABLE  # fail-closed default
        fixtures = self._fixtures.get(task_id)
        if fixtures:
            verdict = fixtures.pop(0)

        acceptable = bool(execution_result.get("outcome") == "PASS") and verdict == VERDICT_ACCEPTABLE
        status = verdict_to_evidence_status(verdict, backend_outcome_acceptable=acceptable)

        now = datetime.now(timezone.utc).isoformat()
        evidence = {
            "schema": "p2p-evidence-claim/1",
            "evidence_ref": hashlib.sha256(json.dumps({
                "task": task_id, "outcome": execution_result.get("outcome"),
                "verdict": verdict, "spec": spec, "received_at": now,
            }, sort_keys=True).encode()).hexdigest(),
            "source": "autopilot-verifier",
            "origin": "RUNTIME_EVIDENCE",
            "observed_at": now,
            "freshness": "CURRENT",
            "status": status,
            "claim": f"verify:{task_id}:{status}",
            "bindings": {"goal": execution_result.get("goal_id"),
                         "task": task_id,
                         "request_fingerprint": execution_result.get("request_fingerprint"),
                         "verification_spec": spec,
                         "verdict": verdict},
        }
        self._log.append(evidence)
        return evidence

    @property
    def log(self) -> list[Mapping[str, Any]]:
        return list(self._log)

    def reset(self) -> None:
        self._fixtures = {}
        self._log = []
