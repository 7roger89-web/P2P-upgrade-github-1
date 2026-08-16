"""Material Design System drift classification."""

import json
from pathlib import Path

from .design_system import MATERIAL_FIELDS, load_design_system


def _walk_diff(left, right, prefix=""):
    differences = []
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            child = f"{prefix}.{key}" if prefix else key
            if key not in left:
                differences.append((child, None, right[key]))
            elif key not in right:
                differences.append((child, left[key], None))
            else:
                differences.extend(_walk_diff(left[key], right[key], child))
    elif isinstance(left, list) and isinstance(right, list):
        if left != right:
            differences.append((prefix, left, right))
    elif left != right:
        differences.append((prefix, left, right))
    return differences


def _material_path(path):
    return path == "material" or path.startswith("material.") and path.split(".")[1] in MATERIAL_FIELDS


def compare_design_systems(baseline, candidate):
    baseline = load_design_system(baseline) if isinstance(baseline, (str, Path)) else baseline
    candidate = load_design_system(candidate) if isinstance(candidate, (str, Path)) else candidate
    if baseline.get("status") != "APPROVED":
        return {
            "schema": "p2p-design-drift/1",
            "status": "UNKNOWN",
            "gate_pass": False,
            "reason": "APPROVED_BASELINE_REQUIRED",
            "changes": [],
        }
    approved = set(baseline.get("approved_exceptions", [])) | set(candidate.get("approved_exceptions", []))
    expected = set(baseline.get("expected_changes", [])) | set(candidate.get("expected_changes", []))
    material_changes = []
    ignored_changes = []
    for path, old, new in _walk_diff(baseline, candidate):
        if not _material_path(path):
            ignored_changes.append({"path": path, "classification": "COSMETIC_IGNORED", "old": old, "new": new})
            continue
        if path in approved:
            classification = "APPROVED"
        elif path in expected:
            classification = "EXPECTED"
        else:
            classification = "UNAPPROVED"
        material_changes.append({"path": path, "classification": classification, "old": old, "new": new})
    unapproved = [item for item in material_changes if item["classification"] == "UNAPPROVED"]
    if unapproved:
        status = "UNAPPROVED"
    elif material_changes:
        status = "APPROVED_OR_EXPECTED"
    else:
        status = "NO_MATERIAL_DRIFT"
    return {
        "schema": "p2p-design-drift/1",
        "status": status,
        "gate_pass": not unapproved,
        "material_changes": material_changes,
        "ignored_changes": ignored_changes,
        "summary": {"material_count": len(material_changes), "unapproved_count": len(unapproved), "ignored_count": len(ignored_changes)},
    }
