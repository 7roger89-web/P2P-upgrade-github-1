"""Canonical identity and adaptive quorum validation."""

import json
import re
from pathlib import Path


CANONICAL_AGENTS = (
    "p2p_iris",
    "p2p_tecton",
    "p2p_axiom",
    "p2p_vector",
    "p2p_datos",
    "p2p_anon",
    "p2p_architecton",
    "p2p_helios",
)
OPTIONAL_AESTHETICA = "p2p_aesthetica"


def load_manifest(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _profile_name(path):
    text = Path(path).read_text(encoding="utf-8")
    match = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    return match.group(1) if match else None


def validate_manifest(manifest, profile_dir=None):
    errors = []
    canonical = list(manifest.get("canonical_agents", []))
    quorum = manifest.get("quorum", {})
    if canonical != list(CANONICAL_AGENTS):
        errors.append({"code": "CANONICAL_IDENTITY_SET_INVALID", "expected": list(CANONICAL_AGENTS), "actual": canonical})
    if len(canonical) != 8 or len(set(canonical)) != 8:
        errors.append({"code": "CANONICAL_COUNT_INVALID", "expected": 8, "actual": len(canonical)})
    if quorum.get("canonical_denominator") != 8 or quorum.get("full_quorum") != "8/8":
        errors.append({"code": "QUORUM_INVARIANT_INVALID", "expected": {"denominator": 8, "full": "8/8"}, "actual": quorum})
    specialists = manifest.get("optional_specialists", [])
    matches = [item for item in specialists if item.get("name") == OPTIONAL_AESTHETICA]
    if len(matches) != 1:
        errors.append({"code": "AESTHETICA_OPTIONAL_PROFILE_INVALID", "actual": matches})
    else:
        item = matches[0]
        if item.get("classification") != "SUPPORTING / OPTIONAL DOMAIN SPECIALIST" or item.get("optional_specialist") is not True or item.get("canonical_quorum_member") is not False:
            errors.append({"code": "AESTHETICA_CLASSIFICATION_INVALID", "actual": item})
    profile_names = {}
    if profile_dir:
        profile_dir = Path(profile_dir)
        for path in sorted(profile_dir.glob("p2p-*.toml")):
            name = _profile_name(path)
            if name:
                profile_names.setdefault(name, []).append(path.name)
        for identity in CANONICAL_AGENTS:
            if identity not in profile_names:
                errors.append({"code": "CANONICAL_PROFILE_MISSING", "identity": identity})
        if OPTIONAL_AESTHETICA not in profile_names:
            errors.append({"code": "AESTHETICA_PROFILE_MISSING", "identity": OPTIONAL_AESTHETICA})
        if len(profile_names.get(OPTIONAL_AESTHETICA, [])) != 1:
            errors.append({"code": "AESTHETICA_PROFILE_DUPLICATE_OR_MISSING", "files": profile_names.get(OPTIONAL_AESTHETICA, [])})
    return {
        "schema": "p2p-governance-validation/1",
        "valid": not errors,
        "canonical_agents": list(CANONICAL_AGENTS),
        "canonical_count": 8,
        "canonical_denominator": 8,
        "full_quorum": "8/8",
        "optional_specialist": OPTIONAL_AESTHETICA,
        "optional_excluded_from_denominator": True,
        "profile_names": profile_names,
        "errors": errors,
    }


def validate_quorum(active_agents=None, optional_specialists=None):
    active_agents = list(active_agents if active_agents is not None else CANONICAL_AGENTS)
    optional_specialists = list(optional_specialists or [])
    canonical_present = sorted(set(active_agents) & set(CANONICAL_AGENTS))
    unexpected = sorted(set(active_agents) - set(CANONICAL_AGENTS))
    missing = sorted(set(CANONICAL_AGENTS) - set(canonical_present))
    return {
        "schema": "p2p-quorum-result/1",
        "canonical_present": canonical_present,
        "canonical_missing": missing,
        "unexpected_active_agents": unexpected,
        "supporting_specialists": sorted(set(optional_specialists)),
        "canonical_denominator": 8,
        "canonical_count": len(canonical_present),
        "full_quorum": f"{len(canonical_present)}/8",
        "full_quorum_pass": len(canonical_present) == 8 and not missing,
        "supporting_specialists_counted": False,
    }
