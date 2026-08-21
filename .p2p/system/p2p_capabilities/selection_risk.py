"""C37 Selection Risk Classification.

Derives a bounded risk class strictly from the C18 TaskProfile vocabulary.
No free-form scores, no vendor data, no opaque weights. Every derivation
decision is recorded with the vocabulary fields that drove it, so a human
or machine can reproduce it byte-for-byte.

RISK_CLASSES: LOW | MATERIAL | HIGH | UNKNOWN (UNKNOWN fails closed —
SelectionPolicy excludes any request holding UNKNOWN risk class at the
request contract itself; this module only produces UNKNOWN when the input
profile is malformed or missing.)

Derivation ladder (applied top-down, first match wins):
1. HIGH    — any of: network_or_secret, financial, production,
             owner_gate required, mutation_risk HIGH, reversibility IRREVERSIBLE.
2. MATERIAL— any of: migration, mutation_risk MATERIAL, task_size LARGE,
             ambiguity HIGH, acceptance_clarity AMBIGUOUS,
             evidence_availability INCOMPLETE, shared_resource_risk.
3. LOW     — everything else within the valid vocabulary.
4. UNKNOWN — invalid/missing profile.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .orchestration_policy import TaskProfile

from .selection_request import (
    ALLOWED_RISK_SOURCES,
    RISK_CLASSES,
    UNKNOWN,
    SelectionRequestError,
)

RISK_DERIVATION_SCHEMA = "p2p-selection-risk-c37/1"


class RiskClassificationError(ValueError):
    """A safe, user-facing risk-classification contract error."""


def classify_task_risk(profile: Mapping[str, Any] | TaskProfile) -> dict[str, Any]:
    """Deterministic risk classification from a C18 TaskProfile. Never asks
    any external system; never consults vendor data.

    Returns: {"risk_class": str, "derived_from": dict, "reasons": tuple[str],
              "decision_id": str}
    """
    if profile is None:
        raise RiskClassificationError("PROFILE_REQUIRED")
    if isinstance(profile, TaskProfile):
        source = profile.to_dict()
    elif isinstance(profile, Mapping):
        source = dict(profile)
    else:
        raise RiskClassificationError("PROFILE_MUST_BE_TASK_PROFILE_OR_MAPPING")

    def truth(field: str) -> bool:
        value = source.get(field)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.upper() not in ("", "FALSE", "NO", "NONE", "LOW",
                                         "REVERSIBLE", "CLEAR", "COMPLETE",
                                         "SMALL")
        return False

    def enum_upper(field: str) -> str:
        value = source.get(field, "")
        return str(value).upper().strip()

    reasons: list[str] = []
    derived_from: dict[str, Any] = {
        field: source.get(field) for field in ALLOWED_RISK_SOURCES
        if field in source
    }

    high_signals = (
        ("network_or_secret", truth("network_or_secret")),
        ("financial", truth("financial")),
        ("production", truth("production")),
        ("owner_gate_required", enum_upper("owner_gate") not in ("", "NOT_REQUIRED")),
        ("mutation_risk_high", enum_upper("mutation_risk") in ("HIGH", "DESTRUCTIVE")),
        ("irreversible", enum_upper("reversibility") == "IRREVERSIBLE"),
    )
    for name, active in high_signals:
        if active:
            reasons.append(f"HIGH:{name}")
    if any(active for _, active in high_signals):
        return {
            "schema": RISK_DERIVATION_SCHEMA,
            "risk_class": "HIGH",
            "derived_from": derived_from,
            "reasons": tuple(reasons),
            "decision_id": None,
        }

    material_signals = (
        ("migration", truth("migration")),
        ("mutation_risk_material", enum_upper("mutation_risk") in ("LOW",)),
        ("task_size_large", enum_upper("task_size") == "LARGE"),
        ("ambiguity_high", enum_upper("ambiguity") == "HIGH"),
        ("acceptance_ambiguous", enum_upper("acceptance_clarity") in ("PARTIAL", "MISSING")),
        ("evidence_incomplete", enum_upper("evidence_availability") in ("PARTIAL", "MISSING", "UNKNOWN")),
        ("shared_resource_risk", truth("shared_resource_risk")),
    )
    for name, active in material_signals:
        if active:
            reasons.append(f"MATERIAL:{name}")
    if any(active for _, active in material_signals):
        return {
            "schema": RISK_DERIVATION_SCHEMA,
            "risk_class": "MATERIAL",
            "derived_from": derived_from,
            "reasons": tuple(reasons),
            "decision_id": None,
        }

    return {
        "schema": RISK_DERIVATION_SCHEMA,
        "risk_class": "LOW",
        "derived_from": derived_from,
        "reasons": tuple(reasons),
        "decision_id": None,
    }


def as_risk_class(value: Any) -> str:
    """Coerce an arbitrary value to a canonical risk class. Unknown shapes
    become UNKNOWN so callers can fail closed deliberately."""
    if value is None:
        return UNKNOWN
    text = str(value).upper().strip()
    return text if text in RISK_CLASSES else UNKNOWN


def risk_is_rejectable(risk_class: str, at_least: str) -> bool:
    """Whether a selection with `risk_class` satisfies a minimum-risk gate.
    Gates never accept UNKNOWN; UNKNOWN fails closed."""
    if risk_class == UNKNOWN:
        return False
    order = {"LOW": 0, "MATERIAL": 1, "HIGH": 2}
    return order.get(risk_class, -1) >= order.get(at_least, 0)


__all__ = [
    "RISK_DERIVATION_SCHEMA",
    "RiskClassificationError",
    "classify_task_risk",
    "as_risk_class",
    "risk_is_rejectable",
]
