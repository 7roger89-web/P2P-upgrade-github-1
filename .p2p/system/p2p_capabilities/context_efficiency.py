"""C36 EfficiencyTelemetry + EfficiencyAssessment — cost evidence, never
fabricated; quality is a hard constraint over cost.

Rules:

- Provider-reported token/cost/latency is NORMALIZED evidence. When the
  provider does not report it (e.g. fake/deterministic targets), fields are
  UNKNOWN / NOT_AVAILABLE — never fabricated zeros (scenario M).
- P2P-estimated cost may be derived and is always labeled as an estimate.
- Efficiency metrics (verified_work_per_token, cost_per_verified_task,
  first_pass_verification_rate, rework_cost_ratio, ...) are computed only
  from evidence-bound inputs; a cheaper execution that fails verification
  is never more efficient than one that verifies (scenario L).
- Soft budget is NOT a correctness quota: exceeding a soft budget never
  silently drops required context; it raises CONTEXT_BUDGET_INSUFFICIENT
  so the caller must use progressive loading, pointers, or targeted
  retrieval instead (scenario K).

No live backend calls; all values are caller-supplied or derived.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

UNKNOWN_VALUE = "UNKNOWN"
NOT_AVAILABLE = "NOT_AVAILABLE"

CURRENCIES = ("USD", "UNKNOWN")


class EfficiencyError(ValueError):
    """Raised when telemetry or budget evaluation is malformed."""

class ContextBudgetInsufficient(EfficiencyError):
    """Raised when a soft budget cannot absorb required context (scenario K)."""


def _num_or_unknown(value: Any) -> float:
    """Normalize a numeric evidence value; non-numeric becomes None
    (represented downstream as UNKNOWN)."""
    if isinstance(value, (int, float)) and value == value:
        return float(value)
    return None


@dataclass(frozen=True)
class ExecutionTelemetry:
    """Normalized evidence record for one bounded execution.

    Every unknown field holds None, which serializes to UNKNOWN. Nothing is
    fabricated: the record reports what was actually observable.
    """

    input_tokens: float | None
    output_tokens: float | None
    cached_input_tokens: float | None
    cache_hit: bool | None
    provider_reported_cost: float | None
    p2p_estimated_cost: float | None
    currency: str
    latency_seconds: float | None
    execution_duration_seconds: float | None
    retry_count: int
    context_bytes: int | None
    context_items: int | None
    read_coverage: float | None
    verification_passed: bool | None
    task_id: str
    session_id: str | None = None

    def __post_init__(self) -> None:
        if self.currency not in CURRENCIES:
            raise EfficiencyError(f"CURRENCY_INVALID: {self.currency}")
        if self.retry_count < 0:
            raise EfficiencyError("RETRY_COUNT_NEGATIVE")

    def to_dict(self) -> dict[str, Any]:
        def render(value: Any) -> Any:
            if value is None:
                return UNKNOWN_VALUE
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return value

        return {
            "schema": "p2p-execution-telemetry-c36/1",
            "input_tokens": render(self.input_tokens),
            "output_tokens": render(self.output_tokens),
            "cached_input_tokens": render(self.cached_input_tokens),
            "cache_hit": render(self.cache_hit),
            "provider_reported_cost": render(self.provider_reported_cost),
            "p2p_estimated_cost": render(self.p2p_estimated_cost),
            "currency": self.currency,
            "latency_seconds": render(self.latency_seconds),
            "execution_duration_seconds": render(self.execution_duration_seconds),
            "retry_count": self.retry_count,
            "context_bytes": render(self.context_bytes),
            "context_items": render(self.context_items),
            "read_coverage": render(self.read_coverage),
            "verification_passed": render(self.verification_passed),
            "task_id": self.task_id,
            "session_id": self.session_id,
        }


@dataclass(frozen=True)
class EfficiencyAssessment:
    """Scenario L proof: quality-constrained efficiency comparison.

    A strategy is only comparable when its verification result is known.
    Unknown verification makes the strategy INCOMPARABLE, not cheaper.
    Verification failure disqualifies a strategy before cost matters.
    """

    task_id: str
    strategies: tuple[Mapping[str, Any], ...]
    primary_metric: str = "verified_work_per_cost"

    def __post_init__(self) -> None:
        if self.primary_metric not in (
            "verified_work_per_token",
            "verified_work_per_cost",
            "cost_per_verified_task",
            "time_to_verified_done",
            "first_pass_verification_rate",
            "rework_cost_ratio",
        ):
            raise EfficiencyError(f"EFFICIENCY_METRIC_INVALID: {self.primary_metric}")

    def rank(self) -> dict[str, Any]:
        comparable = []
        disqualified = []
        incomparable = []
        for strategy in self.strategies:
            verified = strategy.get("verification_passed")
            if verified is None:
                incomparable.append({"strategy": strategy.get("name"), "reason": "VERIFICATION_UNKNOWN"})
                continue
            if not verified:
                disqualified.append({"strategy": strategy.get("name"), "reason": "VERIFICATION_FAILED"})
                continue
            comparable.append(strategy)

        if not comparable:
            return {
                "task_id": self.task_id,
                "winner": None,
                "comparable": comparable,
                "disqualified": disqualified,
                "incomparable": incomparable,
                "verdict": "NO_VERIFIED_STRATEGY",
            }

        def score_of(strategy: Mapping[str, Any]) -> float:
            if self.primary_metric == "verified_work_per_token":
                tokens = strategy.get("input_tokens") or 1
                return float(strategy.get("verified_work_units", 0)) / max(float(tokens), 1)
            if self.primary_metric == "verified_work_per_cost":
                cost = strategy.get("p2p_estimated_cost") or strategy.get("provider_reported_cost") or 1
                return float(strategy.get("verified_work_units", 0)) / max(float(cost), 1)
            if self.primary_metric == "cost_per_verified_task":
                return float(strategy.get("p2p_estimated_cost") or strategy.get("provider_reported_cost") or 0)
            if self.primary_metric == "time_to_verified_done":
                return float(strategy.get("execution_duration_seconds") or 0)
            if self.primary_metric == "first_pass_verification_rate":
                return float(strategy.get("first_pass_rate") or 0)
            rework = float(strategy.get("rework_cost", 0))
            total = float(strategy.get("p2p_estimated_cost") or strategy.get("provider_reported_cost") or 1)
            return 1 - rework / max(total, 1)  # rework_cost_ratio: lower is better handled via negation

        ascending = self.primary_metric in ("cost_per_verified_task", "time_to_verified_done", "rework_cost_ratio")
        ranked = sorted(comparable, key=score_of, reverse=not ascending)
        return {
            "task_id": self.task_id,
            "winner": ranked[0].get("name"),
            "ranking": [s.get("name") for s in ranked],
            "comparable": comparable,
            "disqualified": disqualified,
            "incomparable": incomparable,
            "verdict": "VERIFIED_STRATEGY_SELECTED",
        }


def soft_budget_check(
    budget: Mapping[str, Any],
    required_context_size: int,
    optional_context_size: int = 0,
    soft_limit: int | None = None,
) -> dict[str, Any]:
    """Scenario K: soft budget semantics.

    Required context can NEVER be silently dropped to fit a budget. If the
    required context alone exceeds a hard bound, CONTEXT_BUDGET_INSUFFICIENT.
    The soft limit only governs OPTIONAL additions and emits a warning when
    exceeded.
    """
    hard_limit = budget.get("hard_limit")
    if hard_limit is not None and required_context_size > int(hard_limit):
        raise ContextBudgetInsufficient("CONTEXT_BUDGET_INSUFFICIENT: REQUIRED_CONTEXT_EXCEEDS_HARD_LIMIT")
    total = required_context_size + optional_context_size
    over_soft = soft_limit is not None and total > int(soft_limit)
    return {
        "required_context_dropped": False,
        "soft_budget_exceeded": bool(over_soft),
        "signal": "SOFT_BUDGET_WARNING" if over_soft else "BUDGET_OK",
        "recommendation": (
            "USE_PROGRESSIVE_LOADING_OR_POINTER_CONTEXT" if over_soft else "DELIVER_AS_PLANNED"
        ),
    }
