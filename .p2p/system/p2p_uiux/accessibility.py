"""Evidence-based accessibility audit with no unsupported conformance claim."""

import json
import re
from pathlib import Path

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
CHECK_NAMES = (
    "contrast",
    "typography_readability",
    "focus",
    "keyboard",
    "target_size",
    "motion",
    "semantic_structure",
    "form_errors",
    "color_only",
    "responsive_reading",
)


def _channel(value):
    value = value / 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(color):
    if not HEX.match(str(color or "")):
        raise ValueError(f"Expected #RRGGBB color, got {color!r}")
    rgb = [int(color[index:index + 2], 16) for index in (1, 3, 5)]
    return 0.2126 * _channel(rgb[0]) + 0.7152 * _channel(rgb[1]) + 0.0722 * _channel(rgb[2])


def contrast_ratio(foreground, background):
    first = _luminance(foreground)
    second = _luminance(background)
    return round((max(first, second) + 0.05) / (min(first, second) + 0.05), 2)


def audit_design_system(design_system):
    if isinstance(design_system, (str, Path)):
        with Path(design_system).open("r", encoding="utf-8") as handle:
            design_system = json.load(handle)
    material = design_system.get("material", {})
    colors = material.get("color_tokens", {})
    evidence = design_system.get("accessibility_evidence", {})
    supplied = evidence.get("checks", {})
    failures = []
    ratio = None
    try:
        ratio = contrast_ratio(colors.get("text"), colors.get("background"))
        if ratio < 4.5:
            failures.append({"check": "contrast", "reason": f"measured ratio {ratio} is below 4.5:1"})
    except ValueError as exc:
        failures.append({"check": "contrast", "reason": str(exc)})
    missing_evidence = [name for name in CHECK_NAMES if supplied.get(name) is not True]
    for name in missing_evidence:
        failures.append({"check": name, "reason": "verification evidence is not true/supplied"})
    status = "PASS" if not failures else "NEEDS_EVIDENCE"
    return {
        "schema": "p2p-accessibility-audit/1",
        "status": status,
        "wcag_conformance_claim": False,
        "measured_text_background_ratio": ratio,
        "required_checks": list(CHECK_NAMES),
        "failures": failures,
        "evidence_status": evidence.get("status", "NEEDS_EVIDENCE"),
    }
