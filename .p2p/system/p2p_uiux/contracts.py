"""Adaptive Design Contract generation and validation."""

import json
from pathlib import Path

from .recommendation import build_recommendation


LARGE_FIELDS = (
    "objective",
    "target_user",
    "primary_user_flow",
    "visual_direction",
    "ux_acceptance_criteria",
    "accessibility_requirements",
    "responsive_requirements",
    "implementation_constraints",
    "done_when",
    "out_of_scope",
)
SMALL_FIELDS = (
    "objective",
    "target_user",
    "primary_user_flow",
    "ux_acceptance_criteria",
    "implementation_constraints",
    "done_when",
    "out_of_scope",
)


def contract_requirements(scope="large"):
    return list(SMALL_FIELDS if str(scope).lower() == "small" else LARGE_FIELDS)


def generate_contract(context, scope="large"):
    recommendation = build_recommendation(context)
    level = "small" if str(scope).lower() == "small" else "large"
    contract = {
        "schema": "p2p-design-contract/1",
        "level": level,
        "project_name": recommendation["project_name"],
        "objective": str(context.get("objective") or f"Create a coherent {recommendation['product_label']} experience for the primary flow."),
        "target_user": "; ".join(recommendation["target_users"]),
        "primary_user_flow": recommendation["primary_flow"],
        "visual_direction": recommendation["visual_direction"],
        "ux_acceptance_criteria": [
            "The primary user can understand the next action without guesswork.",
            "The interface preserves the product-specific hierarchy and decision chain.",
            "Errors, loading, empty, and success states are explicit and recoverable.",
        ],
        "accessibility_requirements": list(recommendation["accessibility_rules"].values()),
        "responsive_requirements": [recommendation["responsive"], "Reading order and primary task remain usable at supported widths."],
        "implementation_constraints": recommendation["constraints"] + [recommendation["stack_adaptation"]["guidance"]],
        "done_when": [
            "Design System and Contract are reviewed for the stated scope.",
            "Accessibility evidence is supplied or explicitly marked NEEDS_EVIDENCE.",
            "No unapproved material Design Drift remains.",
        ],
        "out_of_scope": ["Unapproved rebrand or destructive redesign", "Unrelated backend or infrastructure changes"],
        "approval_boundary": "Owner approval is required for material visual identity, core tokens, primary navigation, or destructive redesign.",
    }
    if level == "small":
        contract["accessibility_requirements"] = [
            recommendation["accessibility_rules"]["contrast"],
            recommendation["accessibility_rules"]["focus"],
            recommendation["accessibility_rules"]["target_size"],
            recommendation["accessibility_rules"]["responsive_reading"],
        ]
        contract["responsive_requirements"] = [recommendation["responsive"]]
    validate_contract(contract)
    return contract


def validate_contract(contract):
    if contract.get("schema") != "p2p-design-contract/1":
        raise ValueError("Unsupported Design Contract schema")
    required = contract_requirements(contract.get("level", "large"))
    missing = [field for field in required if not contract.get(field)]
    if missing:
        raise ValueError("Design Contract missing required fields: " + ", ".join(missing))
    return {"valid": True, "level": contract.get("level"), "required_fields": required}


def write_contract(project_root, contract, force=False):
    project_root = Path(project_root).resolve()
    path = project_root / ".p2p" / "design" / "DESIGN_CONTRACT.json"
    if path.exists() and not force:
        raise FileExistsError("Design Contract already exists; review or explicitly replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)
