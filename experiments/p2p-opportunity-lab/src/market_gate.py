from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

VALID_EVIDENCE_CLASSES = {"OBSERVED", "USER_SAID", "INFERRED", "ASSUMED"}


@dataclass(frozen=True)
class GateResult:
    decision: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"decision": self.decision, "reasons": list(self.reasons)}


def _evidence(packet: dict[str, Any]) -> list[dict[str, Any]]:
    items = packet.get("evidence", [])
    if not isinstance(items, list):
        raise ValueError("evidence must be a list")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each evidence item must be an object")
        cls = item.get("class")
        if cls not in VALID_EVIDENCE_CLASSES:
            raise ValueError(f"invalid evidence class: {cls!r}")
    return items


def _has(items: Iterable[dict[str, Any]], predicate) -> bool:
    return any(predicate(item) for item in items)


def evaluate_market_gate(packet: dict[str, Any]) -> GateResult:
    """Return an evidence-gated decision without using owner preference as evidence.

    BUILD is intentionally hard to reach: desk research alone is insufficient.
    The gate needs an observed real-world experiment result plus an observed
    money/willingness-to-pay signal and no unresolved fatal contradiction.
    """
    items = _evidence(packet)
    experiment = packet.get("experiment") or {}
    if not isinstance(experiment, dict):
        raise ValueError("experiment must be an object")

    if not packet.get("problem") or not packet.get("target_user"):
        return GateResult("RESEARCH_MORE", ("problem_or_target_user_missing",))

    if not packet.get("hypothesis"):
        return GateResult("RESEARCH_MORE", ("falsifiable_hypothesis_missing",))

    fatal_contradiction = _has(
        items,
        lambda x: x.get("direction") == "CONTRADICTS"
        and x.get("severity") == "FATAL"
        and x.get("resolved") is not True,
    )
    if fatal_contradiction:
        return GateResult("KILL", ("unresolved_fatal_counterevidence",))

    failure_reached = (
        experiment.get("status") == "COMPLETED"
        and experiment.get("failure_threshold_reached") is True
    )
    if failure_reached:
        return GateResult("KILL", ("real_world_failure_threshold_reached",))

    direct_pain = _has(
        items,
        lambda x: x.get("class") in {"OBSERVED", "USER_SAID"}
        and x.get("signal") == "PAIN",
    )
    demand = _has(
        items,
        lambda x: x.get("class") in {"OBSERVED", "USER_SAID"}
        and x.get("signal") == "DEMAND",
    )
    competitor_or_workaround = _has(
        items, lambda x: x.get("signal") in {"COMPETITOR", "WORKAROUND"}
    )

    experiment_observed = (
        experiment.get("status") == "COMPLETED"
        and experiment.get("source_class") == "OBSERVED"
        and experiment.get("success_threshold_reached") is True
    )
    money_signal = _has(
        items,
        lambda x: x.get("class") == "OBSERVED"
        and x.get("signal") in {"PAYMENT", "WILLINGNESS_TO_PAY"},
    )

    if experiment_observed and money_signal and direct_pain and demand:
        return GateResult(
            "BUILD",
            (
                "observed_experiment_passed",
                "observed_money_signal",
                "direct_pain_and_demand",
            ),
        )

    desk_signal_count = sum(
        1
        for x in items
        if x.get("class") in {"OBSERVED", "USER_SAID"}
        and x.get("signal")
        in {"PAIN", "DEMAND", "COMPETITOR", "WORKAROUND", "PRICING"}
    )

    if direct_pain and demand and competitor_or_workaround and desk_signal_count >= 3:
        if experiment.get("status") in {None, "NOT_STARTED", "DESIGNED"}:
            return GateResult(
                "VALIDATE",
                (
                    "desk_evidence_supports_test",
                    "real_world_validation_not_yet_passed",
                ),
            )

    return GateResult("RESEARCH_MORE", ("evidence_not_yet_decision_sufficient",))
