"""Explainable adaptive UI/UX routing."""

import re
from pathlib import Path

UI_TERMS = {
    "ui", "ux", "interface", "screen", "page", "dashboard", "layout", "component", "design", "visual", "style",
    "workflow", "story", "narrative", "ecommerce", "consumer", "product page", "design system", "visual direction",
    "typography", "color", "palette", "spacing", "navigation", "responsive", "mobile", "accessibility", "a11y",
    "button", "form", "flow", "validation", "exception", "user experience", "landing", "checkout", "game scene", "reader", "interaction",
    "giao di\u1ec7n", "m\u00e0n h\u00ecnh", "b\u1ed1 c\u1ee5c", "quy tr\u00ecnh", "kh\u00f3 d\u00f9ng", "d\u1ec5 d\u00f9ng", "kh\u00f3 t\u00ecm", "d\u1ec5 \u0111\u1ecdc", "kh\u00f3 \u0111\u1ecdc", "r\u1ed1i", "\u0111i\u1ec7n tho\u1ea1i",
    "thiết kế", "dễ nhìn", "quản lý", "nút", "padding",
}
UI_EXTRA_TERMS = {"trang", "h\u00ecnh \u1ea3nh", "ki\u1ec3u ch\u1eef", "bi\u1ec3u m\u1eabu"}
NON_UI_TERMS = {
    "backend", "api", "database", "db", "migration", "infrastructure", "docker", "queue", "webhook", "endpoint",
    "schema", "server", "cron", "secret", "deployment", "index", "repository", "worker",
}
# Retained only as historical vocabulary; materiality uses the bounded classes below.
LEGACY_SPECIALIST_TERMS = {
    "giao di\u1ec7n", "m\u00e0n h\u00ecnh", "b\u1ed1 c\u1ee5c", "quy tr\u00ecnh", "kh\u00f3 t\u00ecm", "\u0111i\u1ec7n tho\u1ea1i",
    "persona", "user need", "visual direction", "design system", "ux", "ui", "interface", "screen", "navigation",
    "typography", "palette", "accessibility", "responsive", "interaction", "component", "layout", "flow", "design",
    "dashboard", "logistics", "ecommerce", "finance", "mobile", "game", "landing", "giao di\u1ec7n", "m\u00e0n h\u00ecnh", "b\u1ed1 c\u1ee5c", "kh\u00f3 t\u00ecm", "\u0111i\u1ec7n tho\u1ea1i", "thiết kế", "dễ nhìn", "quản lý",
}


ACCESSIBILITY_STRONG_TERMS = {
    "accessibility", "a11y", "keyboard", "keyboard-only", "screen reader", "screen-reader",
    "assistive technology", "aria", "semantic", "focus", "focus management", "focus restoration",
    "focus order", "keyboard navigation", "b\u00e0n ph\u00edm", "tr\u00ecnh \u0111\u1ecdc m\u00e0n h\u00ecnh",
    "c\u00f4ng ngh\u1ec7 h\u1ed7 tr\u1ee3", "kh\u1ea3 n\u0103ng truy c\u1eadp", "qu\u1ea3n l\u00fd focus",
    "kh\u00f4i ph\u1ee5c focus", "th\u1ee9 t\u1ef1 focus", "nh\u00e3n truy c\u1eadp",
}
ACCESSIBILITY_COMPLEXITY_TERMS = {
    "multiple states", "multiple screens", "dialog", "dialogs", "drawer", "drawers", "modal", "modals",
    "workflow", "form", "states", "across screens", "nhi\u1ec1u tr\u1ea1ng th\u00e1i", "h\u1ed9p tho\u1ea1i",
    "ng\u0103n k\u00e9o", "c\u1eeda s\u1ed5", "quy tr\u00ecnh", "bi\u1ec3u m\u1eabu",
}
DENSE_WORKFLOW_TERMS = {
    "multi-step", "multi step", "multi-step form", "complex workflow", "workflow form", "dense workflow",
    "dense form", "validation dependencies", "dependent fields", "exception handling", "exception states",
    "many related actions", "many states", "operational workflow", "information entry", "review and exception",
    "nhi\u1ec1u b\u01b0\u1edbc", "quy tr\u00ecnh nhi\u1ec1u b\u01b0\u1edbc", "quy tr\u00ecnh ph\u1ee9c t\u1ea1p",
    "bi\u1ec3u m\u1eabu d\u00e0y", "ph\u1ee5 thu\u1ed9c", "ngo\u1ea1i l\u1ec7", "nhi\u1ec1u h\u00e0nh \u0111\u1ed9ng",
    "nh\u1eadp li\u1ec7u", "duy\u1ec7t ngo\u1ea1i l\u1ec7", "tr\u1ea1ng th\u00e1i ngo\u1ea1i l\u1ec7",
}


def _material_specialist_classes(request):
    accessibility_hits = _hits(request, ACCESSIBILITY_STRONG_TERMS)
    accessibility_complexity_hits = _hits(request, ACCESSIBILITY_COMPLEXITY_TERMS)
    dense_hits = _hits(request, DENSE_WORKFLOW_TERMS)
    lowered = str(request or "").lower()
    explicit_accessibility = bool(
        re.search(r"\baccessibility[_ -]heavy\b|\bcomplex accessibility\b|\bmaterial accessibility\b", lowered)
    )
    explicit_dense = bool(
        re.search(r"\bdense[_ -](?:workflow|form)\b|\bcomplex (?:workflow|form)\b", lowered)
    )
    accessibility_heavy = (
        explicit_accessibility
        or len(accessibility_hits) >= 2
        or (bool(accessibility_hits) and bool(accessibility_complexity_hits))
    )
    dense_workflow = explicit_dense or len(dense_hits) >= 2
    classes = []
    if accessibility_heavy:
        classes.append("ACCESSIBILITY_HEAVY")
    if dense_workflow:
        classes.append("DENSE_WORKFLOW_FORM")
    return {
        "classes": classes,
        "accessibility_hits": accessibility_hits,
        "accessibility_complexity_hits": accessibility_complexity_hits,
        "dense_hits": dense_hits,
    }


def _foundation_paths(profile_root=None):
    """Return the development foundation registry and optional profile path."""
    from p2p_capabilities.specialist import validate_optional_specialist

    here = Path(__file__).resolve()
    system_root = here.parents[1]
    registry = system_root / "p2p_capabilities" / "capabilities.json"
    if profile_root:
        profile_dir = Path(profile_root)
    else:
        profile_dir = here.parents[3] / ".codex" / "agents"
    return registry, profile_dir, validate_optional_specialist(profile_dir / "p2p-aesthetica.toml")


def foundation_route(request, profile_root=None):
    """Use the same UIUX router with the reusable capability foundation."""
    try:
        from p2p_capabilities.model import load_registry
        from p2p_capabilities.routing import classify_capabilities, readiness_snapshot
        from p2p_capabilities.vendor_skill import (
            is_vendor_skill,
            project_vendor_route,
            vendor_readiness_snapshot,
        )
        registry, profile_dir, specialist = _foundation_paths(profile_root)
    except ModuleNotFoundError as exc:
        return {
            "schema": "p2p-capability-route/1",
            "status": "NOT_APPLICABLE",
            "reason": "FOUNDATION_RUNTIME_UNAVAILABLE",
            "missing_module": exc.name,
            "single_router": True,
        }
    if not registry.is_file():
        return {"schema": "p2p-capability-route/1", "status": "NOT_APPLICABLE", "reason": "FOUNDATION_REGISTRY_MISSING", "single_router": True}
    loaded = load_registry(registry)
    manifests = loaded["parsed"]
    repository_root = registry.resolve().parents[3]
    readiness = {}
    for manifest in manifests:
        if manifest.capability_id == "p2p_aesthetica":
            readiness[manifest.capability_id] = readiness_snapshot(
                manifest,
                installed=profile_dir.is_dir(),
                discovered=specialist.get("profile_resolved", False),
                eligible=specialist.get("profile_resolved", False),
                resolved=specialist.get("profile_resolved", False),
                executable=specialist.get("execute_verified", False),
                healthy=specialist.get("health_verified", False),
                reasons=[specialist.get("status", "PROFILE_UNAVAILABLE")],
            )
        elif is_vendor_skill(manifest):
            readiness[manifest.capability_id] = vendor_readiness_snapshot(
                manifest,
                repository_root=repository_root,
                registry_path=registry,
            )
        else:
            readiness[manifest.capability_id] = readiness_snapshot(manifest)
    result = classify_capabilities(request, manifests, readiness=readiness)
    result["registry_hash"] = loaded["registry_hash"]
    result["aesthetica_profile"] = specialist
    result["vendor_skills"] = project_vendor_route(
        request,
        manifests,
        result,
        registry_path=registry,
        repository_root=repository_root,
    )
    return result


def _hits(request, terms):
    lowered = request.lower()
    return sorted(term for term in terms if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", lowered))


def profile_available(profile_root=None):
    if profile_root:
        roots = [Path(profile_root)]
    else:
        file_path = Path(__file__).resolve()
        roots = [
            file_path.parents[1] / ".codex" / "agents",
            file_path.parents[2] / ".codex" / "agents",
            file_path.parents[3] / ".codex" / "agents" if len(file_path.parents) > 3 else file_path.parents[2] / ".codex" / "agents",
            Path.cwd() / ".codex" / "agents",
        ]
    root = next((candidate for candidate in roots if candidate.exists()), roots[0])
    from p2p_capabilities.specialist import validate_optional_specialist

    for path in root.glob("p2p-aesthetica.toml"):
        if validate_optional_specialist(path).get("profile_resolved"):
            return True
    return False


def classify_request(request, profile_root=None, force_profile_available=None, context=None):
    request = str(request or "").strip()
    ui_hits = _hits(request, UI_TERMS | UI_EXTRA_TERMS)
    non_ui_hits = _hits(request, NON_UI_TERMS)
    materiality = _material_specialist_classes(request)
    specialist_classes = materiality["classes"]
    specialist_hits = sorted(
        set(
            materiality["accessibility_hits"]
            + materiality["accessibility_complexity_hits"]
            + materiality["dense_hits"]
        )
    )
    lowered = request.lower()
    negated_interface = bool(
        re.search(r"\b(?:no|without|not)\s+(?:a\s+|an\s+|the\s+)?(?:ui|ux|interface|visual|screen)\b", lowered)
        or re.search(
            r"\bkh\u00f4ng\s+(?:(?:c\u00f3|s\u1eeda|thay \u0111\u1ed5i|ch\u1ec9nh)\s+)?(?:giao di\u1ec7n|m\u00e0n h\u00ecnh|ui|ux|interface)\b",
            lowered,
        )
    )
    if negated_interface:
        ui_hits = [
            hit
            for hit in ui_hits
            if hit not in {"ui", "ux", "interface", "visual", "screen", "giao di\u1ec7n", "m\u00e0n h\u00ecnh"}
        ]
    governance_only = bool(re.search(r"\b(?:release|certification|quorum|governance)\b", lowered)) and not bool(
        re.search(r"\b(?:design|build|create|review|screen|page|layout|visual|interaction|accessibility)\b", lowered)
    )
    if governance_only:
        ui_hits = []
    ui_scope = bool(ui_hits)
    non_ui_scope = bool(non_ui_hits)
    if ui_scope and non_ui_scope:
        scope = "MIXED"
    elif ui_scope:
        scope = "UI_UX"
    else:
        scope = "NON_UI"
    use_skill = scope in {"UI_UX", "MIXED"}
    trivial_cosmetic = (
        bool(
            re.search(r"\b(?:padding|spacing|color|icon|pixel|pixels)\b", lowered)
            or re.search(r"(?:kho\u1ea3ng c\u00e1ch|m\u00e0u|n\u00fat)", lowered)
        )
        and not bool(
            re.search(
                r"\b(?:redesign|accessibility|responsive|navigation|hierarchy|flow|design system|visual direction)\b",
                lowered,
            )
            or re.search(r"(?:truy c\u1eadp|kh\u00f3 d\u00f9ng|kh\u00f3 t\u00ecm|b\u1ed1 c\u1ee5c)", lowered)
        )
        and not specialist_classes
    )
    needs_specialist = use_skill and bool(specialist_classes) and not trivial_cosmetic
    available = profile_available(profile_root) if force_profile_available is None else bool(force_profile_available)
    call_aesthetica = needs_specialist and available
    if not use_skill:
        reason = "No visual/UI/UX signal; preserve normal P2P route."
    elif not needs_specialist:
        reason = "p2p-uiux remains primary; no evidence-backed material specialist class is present."
    elif available:
        reason = "AESTHETICA is conditionally eligible for material accessibility/workflow complexity; the real optional profile is present."
    else:
        reason = "PROFILE_UNAVAILABLE: an evidence-backed specialist class is eligible, but the real optional profile is unavailable; no simulation."
    result = {
        "schema": "p2p-route-decision/1",
        "scope": scope,
        "use_skill": use_skill,
        "call_aesthetica": call_aesthetica,
        "aesthetica_available": available,
        "specialist_eligible": needs_specialist,
        "specialist_classes": specialist_classes,
        "reason": reason,
        "ui_hits": ui_hits,
        "non_ui_hits": non_ui_hits,
        "specialist_hits": specialist_hits,
        "materiality": materiality,
        "trivial_cosmetic": trivial_cosmetic,
        "adaptive_quorum": {
            "canonical_denominator": 8,
            "full_quorum": "8/8",
            "supporting_specialists_in_denominator": False,
        },
    }
    if force_profile_available is None:
        result["foundation"] = foundation_route(request, profile_root=profile_root)
    if use_skill:
        try:
            from .design_intelligence import design_intelligence_route

            result["design_intelligence"] = design_intelligence_route(request, context=context)
        except ModuleNotFoundError as exc:
            result["design_intelligence"] = {
                "schema": "p2p-design-intelligence/1",
                "status": "NUI_UNAVAILABLE",
                "design_mode": "P2P_NATIVE_DESIGN",
                "fallback": "P2P_NATIVE_DESIGN",
                "reason": "DESIGN_INTELLIGENCE_MODULE_UNAVAILABLE",
                "missing_module": exc.name,
                "permission_requests": [],
                "recommendations_grant_permissions": False,
            }
    return result
