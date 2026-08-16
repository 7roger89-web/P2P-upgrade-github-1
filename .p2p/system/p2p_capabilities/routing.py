"""Single-router compatible routing and readiness decisions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from .model import CapabilityManifest, READINESS_STATES


ROUTE_CLASSES = ("PRIMARY", "SECONDARY", "SUPPORTING", "NOT_APPLICABLE")


def _hits(request: str, terms: Iterable[str]) -> list[str]:
    lowered = str(request).lower()
    return sorted(term for term in terms if re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", lowered))


def readiness_snapshot(manifest: CapabilityManifest, *, installed: bool = True, discovered: bool | None = None, eligible: bool | None = None, resolved: bool | None = None, executable: bool | None = None, healthy: bool | None = None, reasons: list[str] | None = None) -> dict[str, Any]:
    discovered = installed if discovered is None else bool(discovered)
    eligible = discovered if eligible is None else bool(eligible)
    resolved = eligible if resolved is None else bool(resolved)
    executable = resolved if executable is None else bool(executable)
    healthy = executable if healthy is None else bool(healthy)
    values = (installed, discovered, eligible, resolved, executable, healthy)
    names = READINESS_STATES
    highest = "NOT_READY"
    for flag, name in zip(values, names):
        if flag:
            highest = name
        else:
            break
    return {
        "capability_id": manifest.capability_id,
        "state": highest,
        "states": {name: bool(flag) for name, flag in zip(names, values)},
        "reasons": list(reasons or []),
        "profile_presence_is_runtime_proof": False,
    }


def _manifest_hits(request: str, terms: Iterable[str]) -> list[str]:
    return _hits(request, terms)


def _class_for(score: int, *, primary: bool = False, supporting: bool = False) -> str:
    if score <= 0:
        return "NOT_APPLICABLE"
    if supporting:
        return "SUPPORTING"
    if primary:
        return "PRIMARY"
    return "SECONDARY"


def classify_capabilities(request: str, manifests: Iterable[CapabilityManifest], *, readiness: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    text = str(request or "").strip()
    readiness = readiness or {}
    results: list[dict[str, Any]] = []
    for manifest in manifests:
        positive = _manifest_hits(text, manifest.triggers)
        negative = _manifest_hits(text, manifest.negative_triggers)
        is_aesthetica = manifest.capability_id == "p2p_aesthetica"
        if manifest.capability_id in readiness:
            snapshot = dict(readiness[manifest.capability_id])
        elif is_aesthetica:
            snapshot = readiness_snapshot(
                manifest,
                executable=False,
                healthy=False,
                reasons=["PROFILE_UNAVAILABLE"],
            )
        else:
            snapshot = readiness_snapshot(manifest)
        eligible = bool(snapshot.get("states", {}).get("ELIGIBLE")) and not negative
        executable = bool(snapshot.get("states", {}).get("EXECUTABLE"))
        value = len(positive) - (len(negative) * 3)
        is_uiux = manifest.capability_id == "p2p-uiux"
        primary = bool(positive) and (is_uiux or value >= 2)
        supporting = is_aesthetica and bool(positive) and eligible and executable
        if is_aesthetica and not executable:
            classification = "NOT_APPLICABLE"
        else:
            classification = _class_for(value if eligible else 0, primary=primary, supporting=supporting)
        reasons: list[str] = []
        if positive:
            reasons.append("TRIGGER_MATCH")
        if negative:
            reasons.append("NEGATIVE_TRIGGER_MATCH")
        if not snapshot.get("states", {}).get("INSTALLED", False):
            reasons.append("NOT_INSTALLED")
        if is_aesthetica and positive and not executable:
            reasons.append("PROFILE_UNAVAILABLE")
        if not positive:
            reasons.append("NO_VALUE")
        results.append({
            "capability_id": manifest.capability_id,
            "classification": classification,
            "invocation_class": manifest.invocation_class,
            "positive_triggers": positive,
            "negative_triggers": negative,
            "readiness": snapshot,
            "eligible": eligible,
            "executable": executable,
            "reason_codes": reasons,
            "value": value,
            "collision": False,
        })
    selected = [item for item in results if item["classification"] != "NOT_APPLICABLE"]
    primary_count = sum(item["classification"] == "PRIMARY" for item in selected)
    if primary_count > 1:
        for item in selected:
            if item["classification"] == "PRIMARY":
                item["collision"] = True
                item["reason_codes"].append("SCOPE_COLLISION_RECORDED")
    return {
        "schema": "p2p-capability-route/1",
        "request": text,
        "results": results,
        "selected": [item["capability_id"] for item in selected],
        "single_router": True,
        "adaptive_quorum": {"canonical_denominator": 8, "full_quorum": "8/8", "supporting_specialists_counted": False},
    }
