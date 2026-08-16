"""Design System generation and protected project artifact writing."""

import json
from pathlib import Path

from .recommendation import build_recommendation


MATERIAL_FIELDS = (
    "product_type",
    "target_users",
    "primary_flow",
    "ux_objectives",
    "visual_direction",
    "color_tokens",
    "typography",
    "spacing",
    "navigation",
    "component_language",
    "interaction_philosophy",
    "responsive",
    "accessibility_baseline",
    "stack_adaptation",
)


def generate_design_system(context, approved=False, approved_by=None):
    recommendation = build_recommendation(context)
    status = "APPROVED" if approved else "DRAFT"
    material = {
        "product_type": recommendation["product_type"],
        "target_users": recommendation["target_users"],
        "primary_flow": recommendation["primary_flow"],
        "ux_objectives": recommendation["ux_objectives"],
        "visual_direction": recommendation["visual_direction"],
        "color_tokens": recommendation["color_tokens"],
        "typography": recommendation["typography"],
        "spacing": recommendation["spacing"],
        "navigation": recommendation["navigation"],
        "component_language": recommendation["component_language"],
        "interaction_philosophy": {"motion": recommendation["motion"], "feedback": "Every primary action exposes progress, success, failure, and recovery."},
        "responsive": recommendation["responsive"],
        "accessibility_baseline": recommendation["accessibility_rules"],
        "stack_adaptation": recommendation["stack_adaptation"],
        "do": recommendation["do"],
        "dont": recommendation["dont"],
    }
    evidence_checks = {
        "contrast": None,
        "typography_readability": None,
        "focus": None,
        "keyboard": None,
        "target_size": None,
        "motion": None,
        "semantic_structure": None,
        "form_errors": None,
        "color_only": None,
        "responsive_reading": None,
    }
    return {
        "schema": "p2p-design-system/1",
        "project_name": recommendation["project_name"],
        "status": status,
        "approval": {"approved_by": str(approved_by) if approved_by else None, "owner_approval_required_for_material_change": True},
        "source": {
            "generator": "p2p-uiux",
            "upstream_basis": recommendation["upstream_basis"],
            "integration_mode": "local deterministic adapter",
        },
        "material": material,
        "accessibility_evidence": {
            "status": "NEEDS_EVIDENCE",
            "checks": evidence_checks,
            "claims": ["No WCAG conformance claim is made without supplied verification evidence."],
        },
        "decision_chain": recommendation["decision_chain"],
        "constraints": recommendation["constraints"],
        "approved_exceptions": [],
        "expected_changes": [],
        "notes": "Project owner must review material visual identity, primary navigation, and token changes.",
    }


def load_design_system(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if value.get("schema") != "p2p-design-system/1":
        raise ValueError("Unsupported Design System schema")
    return value


def _md_list(values):
    return "\n".join("- " + str(value) for value in values) if values else "- None recorded"


def render_design_system_markdown(design_system):
    material = design_system["material"]
    approval = design_system.get("approval", {})
    source = design_system.get("source", {}).get("upstream_basis", {})
    evidence = design_system.get("accessibility_evidence", {})
    lines = [
        "# MASTER DESIGN SYSTEM",
        "",
        f"Project: {design_system.get('project_name', 'Untitled project')}",
        f"Status: {design_system.get('status', 'DRAFT')}",
        f"Approved by: {approval.get('approved_by') or 'OWNER REVIEW REQUIRED'}",
        "",
        "## Product identity and users",
        f"- Product type: {material.get('product_type')}",
        f"- Primary flow: {material.get('primary_flow')}",
        "- Target users:",
        _md_list(material.get("target_users", [])),
        "",
        "## UX objectives and information architecture",
        "- UX objectives:",
        _md_list(material.get("ux_objectives", [])),
        f"- Navigation: {material.get('navigation')}",
        "",
        "## Visual direction and tokens",
        f"- Visual direction: {material.get('visual_direction')}",
        f"- Typography: `{json.dumps(material.get('typography', {}), sort_keys=True)}`",
        f"- Color tokens: `{json.dumps(material.get('color_tokens', {}), sort_keys=True)}`",
        f"- Spacing: `{json.dumps(material.get('spacing', {}), sort_keys=True)}`",
        "",
        "## Component and interaction rules",
        "- Component language:",
        _md_list(material.get("component_language", [])),
        f"- Interaction philosophy: `{json.dumps(material.get('interaction_philosophy', {}), sort_keys=True)}`",
        f"- Responsive: {material.get('responsive')}",
        "",
        "## Accessibility",
        f"- Evidence status: {evidence.get('status', 'NEEDS_EVIDENCE')}",
        f"- Baseline: `{json.dumps(material.get('accessibility_baseline', {}), sort_keys=True)}`",
        "- No WCAG conformance claim is made without supplied evidence.",
        "",
        "## Stack adaptation",
        f"- `{json.dumps(material.get('stack_adaptation', {}), sort_keys=True)}`",
        "",
        "## Decision chain",
    ]
    for decision in design_system.get("decision_chain", []):
        lines.extend([
            f"- USER NEED: {decision['user_need']}",
            f"  - UX PRINCIPLE: {decision['ux_principle']}",
            f"  - DESIGN DECISION: {decision['design_decision']}",
            f"  - IMPLEMENTATION CONSEQUENCE: {decision['implementation_consequence']}",
        ])
    lines.extend([
        "",
        "## Do / Don't",
        "- Do:",
        _md_list(design_system.get("material", {}).get("do", [])),
        "- Don't:",
        _md_list(design_system.get("material", {}).get("dont", [])),
        "",
        "## Provenance",
        f"- Upstream: {source.get('name')} commit `{source.get('commit')}`; metadata `{source.get('skill_metadata_version')}`; observed tag `{source.get('observed_tag_at_commit')}`; license `{source.get('license')}`.",
        "- Material changes require owner review; this artifact is project-owned after approval.",
        "",
    ])
    return "\n".join(lines)


def write_design_system(project_root, design_system, force=False):
    project_root = Path(project_root).resolve()
    design_dir = project_root / ".p2p" / "design"
    json_path = design_dir / "MASTER_DESIGN_SYSTEM.json"
    md_path = design_dir / "MASTER_DESIGN_SYSTEM.md"
    if (json_path.exists() or md_path.exists()) and not force:
        raise FileExistsError("Design System already exists; review or explicitly replace it")
    design_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(design_system, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_design_system_markdown(design_system), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "status": design_system.get("status")}
