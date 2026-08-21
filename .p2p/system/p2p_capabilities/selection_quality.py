"""C37 Selection Quality Gate.

Enforces the QUALITY FLOOR as a HARD constraint: any target whose quality
evidence sits below the floor is EXCLUDED with a recorded reason; selection
never "hopes" a weak target will succeed. Reuses C36 efficiency evidence
shapes (rank verdicts: winner / disqualified / incomparable / verdict text)
so failed attempts already penalized in C36 carry through here.

Quality classes (canonical): VERIFIED_HIGH, VERIFIED, MIXED, UNKNOWN,
FAILED. Ordering: VERIFIED_HIGH > VERIFIED > MIXED > UNKNOWN; FAILED is
never selectable and always excluded.

The floor acts on quality CLASS, not on opaque scores. Cheaper-but-failed
history always loses against verified history (scenario W): this module
cannot rank a FAILED candidate above a VERIFIED one no matter what its
cost story is.
"""

from __future__ import annotations

from typing import Any, Iterable

from .selection_request import UNKNOWN

QUALITY_CLASSES = ("VERIFIED_HIGH", "VERIFIED", "MIXED", UNKNOWN, "FAILED")

QUALITY_RANK = {
    "VERIFIED_HIGH": 3,
    "VERIFIED": 2,
    "MIXED": 1,
    UNKNOWN: 0,
    "FAILED": -1,
}

QUALITY_GATE_SCHEMA = "p2p-selection-quality-c37/1"


class QualityGateError(ValueError):
    """A safe, user-facing quality-gate contract error."""


def canonical_quality_class(value: Any) -> str:
    """Coerce a raw quality value to the canonical class. None/empty/invalid
    shapes become UNKNOWN, not FAILURE: UNKNOWN is handled by fail-closed
    gates downstream."""
    if value is None:
        return UNKNOWN
    text = str(value).upper().strip()
    if text in QUALITY_CLASSES:
        return text
    if text in ("PASS", "PASSED", "SUCCESS"):
        return "VERIFIED"
    if text in ("FAIL", "FAILED"):
        return "FAILED"
    if text in ("PARTIAL",):
        return "MIXED"
    return UNKNOWN


def quality_floor_violated(quality_class: str, floor: str) -> bool:
    """A floor violation occurs when quality evidence exists but sits below
    the floor, OR when the floor is known and quality is unknown (fail
    closed). FAILED violates every floor. A floor of UNKNOWN cannot exclude
    anything by itself; eligibility gates handle unknown floors."""
    if floor == UNKNOWN:
        return quality_class == "FAILED"
    if quality_class == "FAILED":
        return True
    if quality_class == UNKNOWN:
        return True
    quality_score = QUALITY_RANK.get(quality_class, -1)
    floor_score = QUALITY_RANK.get(floor, 0)
    return quality_score < floor_score


def quality_order(quality_class: str) -> int:
    """Deterministic quality ordering for the selection pipeline. UNKNOWN
    sorts below every verified class; FAILED sorts lowest and is excluded
    by is_selectable regardless."""
    return QUALITY_RANK.get(quality_class, -1)


def quality_explanation(quality_class: str, floor: str) -> str:
    """Human-readable, reason-only explanation of a floor decision. No
    hidden reasoning text; the decision is fully reproducible from the
    inputs."""
    if quality_class == "FAILED":
        return "QUALITY_FAILED: prior evidence shows failure; target excluded"
    if floor == UNKNOWN:
        return "QUALITY_FLOOR_UNKNOWN: floor not asserted; quality accepted as-is"
    if quality_class == UNKNOWN:
        return f"QUALITY_UNKNOWN_BELOW_FLOOR_{floor}: no verified quality evidence"
    if quality_order(quality_class) < quality_order(floor):
        return (f"QUALITY_BELOW_FLOOR: {quality_class} ranked below "
                f"required floor {floor}")
    return f"QUALITY_MEETS_FLOOR: {quality_class} at or above {floor}"


def cheapest_failed_penalty() -> str:
    """Deterministic penalty statement reused by the pipeline ordering:
    any failed verification record attaches a hard cost multiplier that can
    never be overcome by a low price. This is why scenario W (quality first)
    is structural, not a tuning constant."""
    return "FAILED_VERIFICATION_HARD_COST_MULTIPLIER"


__all__ = [
    "QUALITY_CLASSES",
    "QUALITY_RANK",
    "QUALITY_GATE_SCHEMA",
    "QualityGateError",
    "canonical_quality_class",
    "quality_floor_violated",
    "quality_order",
    "quality_explanation",
    "cheapest_failed_penalty",
]
