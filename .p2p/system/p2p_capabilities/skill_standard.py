"""Adaptive skill contract validation with a lightweight path for small work."""

from __future__ import annotations

from typing import Any, Mapping


ADAPTIVE_SKILL_FIELDS = (
    "PURPOSE",
    "TRIGGERS",
    "NEGATIVE_TRIGGERS",
    "WHEN_NOT_TO_USE",
    "INPUTS",
    "WORKFLOW",
    "DEPENDENCIES",
    "CONTEXT",
    "APPROVAL_BOUNDARY",
    "FAILURE_MODES",
    "RED_FLAGS",
    "EVIDENCE_REQUIRED",
    "DONE_WHEN",
    "EVAL_REFERENCES",
    "PROVENANCE",
)


def validate_skill_contract(contract: Mapping[str, Any], *, lightweight: bool = False) -> dict[str, Any]:
    required = set(ADAPTIVE_SKILL_FIELDS)
    missing = sorted(required - set(contract))
    if lightweight:
        missing = [item for item in missing if item not in {"EVAL_REFERENCES", "RED_FLAGS"}]
    invalid = [field for field in required - set(missing) if field in contract and not contract[field]]
    return {
        "schema": "p2p-adaptive-skill-contract/1",
        "valid": not missing and not invalid,
        "lightweight": lightweight,
        "required_fields": list(ADAPTIVE_SKILL_FIELDS),
        "missing": missing,
        "empty": sorted(invalid),
        "ceremony": "LIGHTWEIGHT" if lightweight else "FULL",
    }


def default_uiux_contract() -> dict[str, Any]:
    return {
        "PURPOSE": "Guide reusable UI/UX product and accessibility decisions.",
        "TRIGGERS": ["ui", "ux", "design", "screen", "accessibility"],
        "NEGATIVE_TRIGGERS": ["backend", "database", "infrastructure"],
        "WHEN_NOT_TO_USE": ["pure backend", "data-only", "non-visual task"],
        "INPUTS": ["product context", "user need", "constraints", "stack"],
        "WORKFLOW": ["context", "design direction", "verification"],
        "DEPENDENCIES": ["existing P2P router", "approved governance"],
        "CONTEXT": ["project domain", "design system", "accessibility"],
        "APPROVAL_BOUNDARY": ["material brand", "primary navigation", "protected design system"],
        "FAILURE_MODES": ["unknown stack", "missing evidence", "profile unavailable"],
        "RED_FLAGS": ["generic style", "unverified compliance", "silent overwrite"],
        "EVIDENCE_REQUIRED": ["design contract", "a11y evidence", "drift result"],
        "DONE_WHEN": ["recommendation is scoped", "evidence is fresh"],
        "EVAL_REFERENCES": ["CF16", "CF17", "existing UIUX eval"],
        "PROVENANCE": {"source": "local p2p-uiux skill", "network_runtime": False},
    }
