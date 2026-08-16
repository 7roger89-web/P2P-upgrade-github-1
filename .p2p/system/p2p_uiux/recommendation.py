"""Product-aware recommendation composition."""

from .catalog import ACCESSIBILITY_RULES, UPSTREAM_REFERENCE, get_pattern, normalize_product_type, stack_adaptation


def _as_list(value, fallback):
    if value is None:
        return list(fallback)
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def build_recommendation(context):
    context = dict(context or {})
    product_type = normalize_product_type(context.get("product_type"))
    pattern = get_pattern(product_type)
    target_users = _as_list(context.get("target_users"), ["Primary user to be confirmed"])
    primary_flow = str(context.get("primary_flow") or "Complete the primary task with clear feedback and recovery.")
    requested_direction = str(context.get("visual_direction") or "").strip()
    if requested_direction:
        visual_direction = requested_direction
    else:
        visual_direction = pattern["visual_direction"]
    chain = []
    for principle in pattern["ux_principles"]:
        chain.append({
            "user_need": pattern["user_need"],
            "ux_principle": principle,
            "design_decision": "Use the product-specific hierarchy and component language to make this principle visible.",
            "implementation_consequence": "Preserve the decision in semantic tokens, component rules, responsive behavior, and verification evidence.",
        })
    return {
        "schema": "p2p-uiux-recommendation/1",
        "project_name": str(context.get("project_name") or "Untitled project"),
        "product_type": product_type,
        "product_label": pattern["label"],
        "target_users": target_users,
        "primary_flow": primary_flow,
        "user_need": pattern["user_need"],
        "ux_objectives": pattern["ux_principles"],
        "information_architecture": pattern["information_architecture"],
        "visual_direction": visual_direction,
        "typography": pattern["typography"],
        "color_tokens": pattern["palette"],
        "spacing": pattern["spacing"],
        "navigation": pattern["navigation"],
        "component_language": pattern["components"],
        "responsive": pattern["responsive"],
        "motion": pattern["motion"],
        "accessibility_rules": dict(ACCESSIBILITY_RULES),
        "do": pattern["do"],
        "dont": pattern["dont"],
        "decision_chain": chain,
        "stack_adaptation": stack_adaptation(context.get("stack")),
        "assertion_tags": pattern["assertion_tags"],
        "upstream_basis": dict(UPSTREAM_REFERENCE),
        "constraints": _as_list(context.get("constraints"), ["Preserve existing product behavior and approved project state."]),
    }
