"""Beginner-first Design Intelligence over a bounded NUI metadata snapshot.

This module is deliberately a pure planning boundary.  It classifies a UI/UX
request, normalizes a task profile, routes a bounded faculty graph, and emits
obligations that existing P2P authorities can consume.  It does not execute a
faculty, create an agent, grant a permission, write a product, or persist a
second task/decision truth.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


SCHEMA = "p2p-design-intelligence/1"
PROFILE_SCHEMA = "p2p-ui-task-profile/1"
ROUTE_SCHEMA = "p2p-ui-design-route/1"
OBLIGATION_SCHEMA = "p2p-ui-obligation-plan/1"
DISPOSITIONS = ("REQUIRED", "EXPECTED", "OPTIONAL", "EXCLUDED", "UNKNOWN")
MATERIALITY_CATEGORIES = (
    "new_surface",
    "navigation",
    "visual_redesign",
    "design_system",
    "consequential_interaction",
    "high_fidelity",
    "tiny_local_edit",
)
RENDER_STATES = (
    "RENDER_AVAILABLE",
    "RENDER_UNAVAILABLE",
    "RENDER_BLOCKED_PERMISSION",
    "RENDER_UNKNOWN",
)
C12_PATH = ("READY", "PREFLIGHT", "ACTIVE", "EXECUTE", "VERIFY", "EVIDENCE", "DONE")
NUI_LIFECYCLE = (
    "INTAKE",
    "CONTRACTED",
    "ROUTED",
    "DISCOVERED",
    "ARCHITECTED",
    "DIVERGED",
    "DESIGN_SELECTED",
    "SYSTEMIZED",
    "SPECIFIED",
    "IMPLEMENTABLE",
    "RENDERED",
    "CRITIQUED",
    "VERIFIED",
    "RELEASED",
)
_REGISTRY_PATH = Path(__file__).with_name("nui_registry.json")
_REGISTRY_LOCK_PATH = Path(__file__).with_name("nui_registry.lock.json")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SECRET_FIELD_RE = re.compile(r"(?:secret|token|password|credential|api[_-]?key|private[_-]?key|authorization)", re.I)


class DesignIntelligenceError(ValueError):
    """Base error for a rejected profile, route, registry, or evidence packet."""


class RegistryIntegrityError(DesignIntelligenceError):
    """Raised when the frozen registry cannot be trusted."""


class ProfileIntegrityError(DesignIntelligenceError):
    """Raised when a task profile changes after it was fingerprinted."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _safe_input(value: Any, *, path: str = "input") -> Any:
    """Copy input while rejecting secret-shaped fields at the boundary."""

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if _SECRET_FIELD_RE.search(key_text):
                raise DesignIntelligenceError(f"{path}.{key_text}:SECRET_FIELD_REJECTED")
            result[key_text] = _safe_input(child, path=f"{path}.{key_text}")
        return result
    if isinstance(value, (list, tuple, set)):
        return [_safe_input(child, path=f"{path}[{index}]") for index, child in enumerate(value)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise DesignIntelligenceError(f"{path}:UNSUPPORTED_VALUE")


def registry_path() -> Path:
    """Return the package-local registry path without accessing the network."""

    return _REGISTRY_PATH


def _cycle_ids(skills: Mapping[str, Mapping[str, Any]]) -> list[str]:
    cycles: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(skill_id: str) -> None:
        if skill_id in visiting:
            cycles.append(skill_id)
            return
        if skill_id in visited:
            return
        visiting.add(skill_id)
        parent = skills.get(skill_id, {}).get("parent")
        if parent:
            visit(str(parent))
        visiting.remove(skill_id)
        visited.add(skill_id)

    for skill_id in skills:
        visit(str(skill_id))
    return sorted(set(cycles))


def validate_registry(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the graph snapshot and return compact deterministic metrics."""

    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return {"valid": False, "errors": ["REGISTRY_OBJECT_REQUIRED"]}
    if payload.get("schema") != "p2p-nui-registry/1":
        errors.append("REGISTRY_SCHEMA_INVALID")
    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping):
        errors.append("REGISTRY_PROVENANCE_REQUIRED")
    else:
        if provenance.get("upstream_license") != "MIT":
            errors.append("UPSTREAM_LICENSE_NOT_MIT")
        if not _SHA256_RE.fullmatch(str(provenance.get("graph_sha256", ""))):
            errors.append("UPSTREAM_GRAPH_SHA256_INVALID")
        if not re.fullmatch(r"[0-9a-f]{40}", str(provenance.get("upstream_revision", ""))):
            errors.append("UPSTREAM_REVISION_INVALID")
    skills = payload.get("skills")
    if not isinstance(skills, Mapping):
        errors.append("REGISTRY_SKILLS_REQUIRED")
        skills = {}
    if len(skills) != 174 or payload.get("canonical_faculty_count") != 174:
        errors.append("FACULTY_COUNT_MUST_BE_174")
    if payload.get("kernel_faculty_count") != 13:
        errors.append("KERNEL_COUNT_MUST_BE_13")
    for skill_id, entry in skills.items():
        if not isinstance(skill_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]+", skill_id):
            errors.append(f"SKILL_ID_INVALID:{skill_id}")
        if not isinstance(entry, Mapping) or not entry.get("family") or not entry.get("output"):
            errors.append(f"SKILL_ENTRY_INVALID:{skill_id}")
            continue
        parent = entry.get("parent")
        if parent is not None and parent not in skills:
            errors.append(f"PARENT_NOT_FOUND:{skill_id}:{parent}")
        if entry.get("source_state") != "UPSTREAM_PRESERVED":
            errors.append(f"SKILL_SOURCE_STATE_INVALID:{skill_id}")
        if any(_SECRET_FIELD_RE.search(str(key)) for key in entry):
            errors.append(f"SKILL_SECRET_FIELD:{skill_id}")
    cycles = _cycle_ids(skills)
    if cycles:
        errors.append("REGISTRY_CYCLE:" + ",".join(cycles))
    rules = payload.get("routing_rules")
    if not isinstance(rules, list) or not rules:
        errors.append("ROUTING_RULES_REQUIRED")
        rules = []
    rule_ids: set[str] = set()
    for rule in rules:
        if not isinstance(rule, Mapping):
            errors.append("ROUTING_RULE_INVALID")
            continue
        rule_id = str(rule.get("id", ""))
        if not rule_id or rule_id in rule_ids:
            errors.append(f"ROUTING_RULE_ID_INVALID:{rule_id}")
        rule_ids.add(rule_id)
        if rule.get("disposition") not in DISPOSITIONS:
            errors.append(f"ROUTING_RULE_DISPOSITION_INVALID:{rule_id}")
        if not isinstance(rule.get("any_signals"), list) or not rule.get("any_signals"):
            errors.append(f"ROUTING_RULE_SIGNALS_REQUIRED:{rule_id}")
        for skill_id in rule.get("skills", []):
            if skill_id not in skills:
                errors.append(f"ROUTING_SKILL_NOT_FOUND:{rule_id}:{skill_id}")
    extension = payload.get("p2p_extension")
    if not isinstance(extension, Mapping) or extension.get("canonical_quorum_denominator") != 8:
        errors.append("P2P_EXTENSION_CANONICAL_QUORUM_INVALID")
    return {
        "valid": not errors,
        "errors": errors,
        "faculty_count": len(skills),
        "kernel_count": sum(1 for item in skills.values() if isinstance(item, Mapping) and item.get("family") == "kernel"),
        "rule_count": len(rules),
        "cycle_count": len(cycles),
    }


def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate the local snapshot; never fetch or update it."""

    source = Path(path) if path else registry_path()
    if not source.is_file():
        raise RegistryIntegrityError("NUI_REGISTRY_MISSING")
    raw = source.read_bytes()
    lock_path = _REGISTRY_LOCK_PATH if path is None else source.with_name("nui_registry.lock.json")
    if not lock_path.is_file():
        raise RegistryIntegrityError("NUI_REGISTRY_LOCK_MISSING")
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryIntegrityError("NUI_REGISTRY_LOCK_INVALID") from exc
    if not isinstance(lock, Mapping) or lock.get("schema") != "p2p-nui-registry-lock/1":
        raise RegistryIntegrityError("NUI_REGISTRY_LOCK_SCHEMA_INVALID")
    raw_sha256 = _sha256_bytes(raw)
    if raw_sha256 != lock.get("registry_sha256"):
        raise RegistryIntegrityError("NUI_REGISTRY_FINGERPRINT_MISMATCH")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryIntegrityError("NUI_REGISTRY_JSON_INVALID") from exc
    validation = validate_registry(payload)
    if not validation["valid"]:
        raise RegistryIntegrityError("NUI_REGISTRY_INVALID:" + ";".join(validation["errors"]))
    provenance = payload.get("provenance", {})
    if provenance.get("upstream_revision") != lock.get("upstream_revision"):
        raise RegistryIntegrityError("NUI_REGISTRY_UPSTREAM_REVISION_MISMATCH")
    if provenance.get("graph_sha256") != lock.get("graph_sha256"):
        raise RegistryIntegrityError("NUI_REGISTRY_GRAPH_FINGERPRINT_MISMATCH")
    result = deepcopy(payload)
    result["validation"] = validation
    result["provenance"] = dict(result["provenance"])
    result["provenance"]["registry_sha256"] = raw_sha256
    result["provenance"]["registry_fingerprint"] = _sha256(payload)
    result["registry_path"] = str(source)
    return result


def _contains(text: str, *terms: str) -> bool:
    lowered = text.lower()
    return any(
        re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", lowered)
        for term in terms
    )


def classify_materiality(request: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Classify the design surface and declare reduced-path omissions."""

    context = dict(context or {})
    text = _text(request)
    categories: list[str] = []
    reasons: list[str] = []
    if _contains(text, "new screen", "new page", "new flow", "dashboard", "screen", "page", "màn hình", "giao diện"):
        categories.append("new_surface")
        reasons.append("new or changed user-visible surface signal")
    if _contains(text, "navigation", "hierarchy", "search", "find", "menu", "điều hướng", "khó tìm"):
        categories.append("navigation")
        reasons.append("navigation or information-retrieval signal")
    if _contains(text, "redesign", "visual", "style", "professional", "polished", "modern", "màu", "bố cục", "thiết kế"):
        categories.append("visual_redesign")
        reasons.append("visual direction or hierarchy signal")
    if _contains(text, "design system", "tokens", "component system", "reusable", "library", "hệ thống thiết kế"):
        categories.append("design_system")
        reasons.append("reusable system signal")
    if _contains(text, "financial", "payment", "checkout", "reconcile", "reconciliation", "destructive", "delete", "medical", "security", "privacy", "high impact", "consequential", "tài chính", "đối soát"):
        categories.append("consequential_interaction")
        reasons.append("consequence, privacy, security, or financial signal")
    if _contains(text, "pixel", "fidelity", "screenshot", "reference", "high fidelity", "exact", "theo ảnh"):
        categories.append("high_fidelity")
        reasons.append("high-fidelity or reference-bound signal")
    tiny = _contains(text, "padding", "spacing", "color", "icon", "pixel tweak", "khoảng cách", "màu", "đổi nút")
    material_terms = set(categories)
    explicit_materiality = _text(context.get("materiality")).lower()
    if explicit_materiality in MATERIALITY_CATEGORIES:
        material_terms.add(explicit_materiality)
        if explicit_materiality not in categories:
            categories.append(explicit_materiality)
    if tiny and not material_terms:
        categories.append("tiny_local_edit")
        reasons.append("small local visual edit without a broader flow or risk signal")
    if not categories and text:
        categories.append("new_surface")
        reasons.append("user-visible design request inferred from natural language")
    material = bool(set(categories) - {"tiny_local_edit"})
    if "tiny_local_edit" in categories and material:
        categories.remove("tiny_local_edit")
    if not material and "tiny_local_edit" not in categories:
        categories = ["tiny_local_edit"] if text else []
    omitted = []
    if "tiny_local_edit" in categories:
        omitted = [
            "full_information_architecture",
            "professional_workspace_completeness",
            "divergent_visual_directions",
            "full_product_scenario_coverage",
        ]
    return {
        "schema": "p2p-materiality/1",
        "categories": sorted(set(categories)),
        "material": material,
        "reduced_path": not material and bool(text),
        "reasons": sorted(set(reasons)),
        "omitted_concerns": omitted,
    }


def _infer_signals(text: str, materiality: Mapping[str, Any], context: Mapping[str, Any]) -> set[str]:
    lowered = text.lower()
    signals = set(_list(context.get("signals")))
    signals.update(str(item) for item in materiality.get("categories", []))
    if materiality.get("material"):
        signals.add("material")
    if _contains(text, "logistics", "shipment", "shipping", "warehouse", "operations", "dispatch", "manager", "quản lý", "vận đơn", "kho"):
        signals.update({"operational", "professional_workspace", "manager_visibility"})
    if _contains(text, "table", "dense", "many columns", "compare", "reconciliation", "exception", "review", "đối soát", "ngoại lệ", "duyệt"):
        signals.update({"dense_data", "exceptions", "reconciliation"})
    if _contains(text, "financial", "payment", "invoice", "price", "cost", "money", "tài chính", "thanh toán"):
        signals.update({"financial", "high_impact"})
    if _contains(text, "story", "narrative", "game", "gamepad", "controller", "consumer", "reader", "truyện"):
        signals.update({"consumer", "narrative"})
    if _contains(text, "gamepad", "controller", "tay cầm"):
        signals.add("gamepad")
    if _contains(text, "accessibility", "a11y", "keyboard", "screen reader", "low vision", "cognitive", "reduced motion", "truy cập", "bàn phím"):
        signals.add("accessibility_heavy")
    if _contains(text, "ai", "agent", "copilot", "streaming", "autonomous", "trí tuệ nhân tạo"):
        signals.update({"ai", "human_ai"})
    if _contains(text, "reference", "inspired by", "theo ảnh", "tham khảo") or context.get("references"):
        signals.update({"references", "named_reference"})
    if _contains(text, "professional", "redesign", "creative", "visual direction", "phong cách"):
        signals.add("visual_ambition_open")
    if context.get("runtime_render") or context.get("runtime_capabilities", {}).get("render_available"):
        signals.add("runtime_render")
    return {str(signal) for signal in signals if str(signal).strip()}


def _render_state(context: Mapping[str, Any]) -> str:
    runtime = context.get("runtime_capabilities")
    if not isinstance(runtime, Mapping):
        runtime = {}
    value = runtime.get("render_state") or context.get("render_state")
    if value in RENDER_STATES:
        return str(value)
    if runtime.get("render_blocked_permission") or context.get("render_blocked_permission"):
        return "RENDER_BLOCKED_PERMISSION"
    if runtime.get("render_available") is True or context.get("runtime_render") is True:
        return "RENDER_AVAILABLE"
    if runtime.get("render_available") is False:
        return "RENDER_UNAVAILABLE"
    return "RENDER_UNKNOWN"


def build_task_profile(request: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Create a beginner-safe, fingerprinted task profile."""

    safe_context = _safe_input(dict(context or {}), path="context")
    text = _text(request)
    raw_requirements = {"request": text, "context": safe_context}
    materiality = classify_materiality(text, safe_context)
    signals = sorted(_infer_signals(text, materiality, safe_context))
    surface = _text(safe_context.get("product_surface"))
    if not surface:
        if "operational" in signals:
            surface = "operational_workspace"
        elif "consumer" in signals or "narrative" in signals:
            surface = "consumer_or_narrative_surface"
        else:
            surface = "UNKNOWN"
    users = _list(safe_context.get("users") or safe_context.get("user_roles") or safe_context.get("users_roles"))
    job = _text(safe_context.get("job") or safe_context.get("primary_job") or safe_context.get("primary_flow")) or "UNKNOWN"
    workflow = _list(safe_context.get("workflow") or safe_context.get("workflows")) or ([job] if job != "UNKNOWN" else [])
    platforms = _list(safe_context.get("platforms") or safe_context.get("platform")) or ["UNKNOWN"]
    devices = _list(safe_context.get("devices") or safe_context.get("device_modalities")) or ["UNKNOWN"]
    modalities = _list(safe_context.get("modalities") or safe_context.get("input_modalities")) or ["pointer_or_touch"]
    risk = _text(safe_context.get("risk")) or ("HIGH" if "high_impact" in signals or "financial" in signals else "UNKNOWN")
    ambition = _text(safe_context.get("visual_ambition")) or ("OPEN" if "visual_ambition_open" in signals else "UNKNOWN")
    constraints = _list(safe_context.get("constraints"))
    existing_ds = safe_context.get("existing_design_system") or safe_context.get("design_system") or "UNKNOWN"
    references = _safe_input(safe_context.get("references", []), path="context.references")
    unknowns = _list(safe_context.get("unknowns"))
    for label, value in (
        ("product_surface", surface),
        ("users", users),
        ("job", job),
        ("platforms", platforms),
        ("risk", risk),
        ("visual_ambition", ambition),
        ("runtime_render", _render_state(safe_context)),
    ):
        if value in (None, "UNKNOWN", ["UNKNOWN"], []):
            unknowns.append(label)
    profile_body = {
        "schema": PROFILE_SCHEMA,
        "product_surface": surface,
        "users_roles": users,
        "job": job,
        "workflow": workflow,
        "platforms": platforms,
        "devices": devices,
        "modalities": modalities,
        "risk": risk,
        "visual_ambition": ambition,
        "constraints": constraints,
        "existing_design_system": existing_ds,
        "references": references,
        "runtime_capabilities": {
            "render_state": _render_state(safe_context),
            "browser_available": bool((safe_context.get("runtime_capabilities") or {}).get("browser_available", False)) if isinstance(safe_context.get("runtime_capabilities"), Mapping) else False,
            "accessibility_tools_available": bool((safe_context.get("runtime_capabilities") or {}).get("accessibility_tools_available", False)) if isinstance(safe_context.get("runtime_capabilities"), Mapping) else False,
        },
        "unknowns": sorted(set(unknowns)),
        "signals": signals,
        "materiality": materiality,
        "beginner_ready": True,
        "questions": [],
        "permission_requests": [],
        "recommendations_grant_permissions": False,
    }
    raw_fingerprint = _sha256(raw_requirements)
    profile_fingerprint = _sha256(profile_body)
    return {
        **profile_body,
        "raw_requirements_fingerprint": raw_fingerprint,
        "profile_fingerprint": profile_fingerprint,
    }


def _profile_body(profile: Mapping[str, Any]) -> dict[str, Any]:
    body = deepcopy(dict(profile))
    body.pop("profile_fingerprint", None)
    body.pop("raw_requirements_fingerprint", None)
    body.pop("route_fingerprint", None)
    return body


def validate_task_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(profile, Mapping) or profile.get("schema") != PROFILE_SCHEMA:
        raise ProfileIntegrityError("TASK_PROFILE_INVALID")
    stored = _text(profile.get("profile_fingerprint"))
    if not _SHA256_RE.fullmatch(stored):
        raise ProfileIntegrityError("TASK_PROFILE_FINGERPRINT_REQUIRED")
    actual = _sha256(_profile_body(profile))
    if stored != actual:
        raise ProfileIntegrityError("ROUTING_PROFILE_MISMATCH")
    if profile.get("permission_requests") != [] or profile.get("recommendations_grant_permissions") is not False:
        raise ProfileIntegrityError("PROFILE_PERMISSION_BOUNDARY_INVALID")
    return {"valid": True, "profile_fingerprint": stored, "raw_requirements_fingerprint": profile.get("raw_requirements_fingerprint")}


def _merge_disposition(existing: str | None, candidate: str) -> str:
    order = {"UNKNOWN": 0, "EXCLUDED": 1, "OPTIONAL": 2, "EXPECTED": 3, "REQUIRED": 4}
    return candidate if existing is None or order[candidate] > order[existing] else existing


def _expand_dependencies(skill_ids: Iterable[str], skills: Mapping[str, Mapping[str, Any]]) -> tuple[list[str], dict[str, str]]:
    activated: list[str] = []
    via: dict[str, str] = {}

    def add(skill_id: str, source: str) -> None:
        if skill_id not in skills:
            raise RegistryIntegrityError(f"ROUTING_SKILL_NOT_FOUND:{skill_id}")
        if skill_id in activated:
            return
        parent = skills[skill_id].get("parent")
        if parent:
            add(str(parent), skill_id)
        activated.append(skill_id)
        via[skill_id] = source

    for skill_id in skill_ids:
        add(str(skill_id), "RULE")
    return activated, via


def route_design_task(profile: Mapping[str, Any], registry: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Route the smallest rule/dependency-expanded graph for a valid profile."""

    validate_task_profile(profile)
    loaded = dict(registry or load_registry())
    validation = validate_registry(loaded)
    if not validation["valid"]:
        raise RegistryIntegrityError("NUI_REGISTRY_INVALID:" + ";".join(validation["errors"]))
    materiality = profile.get("materiality", {})
    signals = set(_list(profile.get("signals")))
    matched_rules: list[dict[str, Any]] = []
    requested_skills: list[str] = []
    dispositions: dict[str, str] = {}
    reasons: dict[str, list[str]] = {}
    for rule in loaded.get("routing_rules", []):
        rule_signals = set(_list(rule.get("any_signals")))
        matched = sorted(signals.intersection(rule_signals))
        if not matched:
            continue
        rule_id = str(rule["id"])
        matched_rules.append({"rule_id": rule_id, "matched_signals": matched, "reason": str(rule["reason"]), "disposition": rule["disposition"]})
        for skill_id in rule.get("skills", []):
            skill_id = str(skill_id)
            if skill_id not in requested_skills:
                requested_skills.append(skill_id)
            dispositions[skill_id] = _merge_disposition(dispositions.get(skill_id), str(rule["disposition"]))
            reasons.setdefault(skill_id, []).append(f"{rule_id}: {rule['reason']}")
    if materiality.get("reduced_path") and not requested_skills:
        requested_skills = ["modeling-product-intent", "modeling-users-and-tasks", "directing-visual-hierarchy", "verifying-runtime-ui-behavior"]
        for skill_id in requested_skills:
            dispositions[skill_id] = "REQUIRED"
            reasons[skill_id] = ["tiny_local_edit reduced path: preserve local intent and verify the changed surface"]
    if materiality.get("material") and not requested_skills:
        raise DesignIntelligenceError("MATERIAL_ROUTE_EMPTY")
    activated, via = _expand_dependencies(requested_skills, loaded["skills"])
    for skill_id in activated:
        dispositions.setdefault(skill_id, "EXPECTED" if via[skill_id] != "RULE" else "REQUIRED")
        reasons.setdefault(skill_id, [f"dependency of {via[skill_id]}"] if via[skill_id] != "RULE" else ["direct route activation"])
    activated_entries = []
    for skill_id in activated:
        entry = loaded["skills"][skill_id]
        activated_entries.append({
            "id": skill_id,
            "family": entry["family"],
            "parent": entry.get("parent"),
            "output": entry["output"],
            "disposition": dispositions[skill_id],
            "activation_reasons": sorted(set(reasons[skill_id])),
            "activation_kind": "DIRECT" if via[skill_id] == "RULE" else "DEPENDENCY",
        })
    selected_families = {str(item["family"]) for item in activated_entries}
    high_impact_omissions: list[dict[str, Any]] = []
    high_impact_families = ("transaction", "safety", "trust", "ai", "inclusive-specialist")
    for family in high_impact_families:
        if family not in selected_families:
            high_impact_omissions.append({
                "family": family,
                "disposition": "EXCLUDED" if family != "inclusive-specialist" else "UNKNOWN",
                "reason": f"No profile signal activated the {family} decision/failure class; retain UNKNOWN if the missing context is later supplied.",
            })
    if "accessibility_heavy" not in signals and "inclusive-specialist" not in selected_families:
        high_impact_omissions.append({"family": "inclusive-specialist", "disposition": "UNKNOWN", "reason": "Accessibility depth was not stated; automated checks cannot prove complete accessibility."})
    optional_specialist = {
        "id": "p2p_aesthetica",
        "disposition": "OPTIONAL",
        "eligible": "accessibility_heavy" in signals or "dense_data" in signals,
        "activated": False,
        "reason": "Optional specialist eligibility is reported only from the existing capability foundation; no profile is simulated or placed in the canonical denominator.",
    }
    unknowns = sorted(set(_list(profile.get("unknowns"))))
    if profile.get("runtime_capabilities", {}).get("render_state") == "RENDER_UNKNOWN":
        unknowns.append("runtime_render")
    workspace = {}
    workspace_signals = {"professional_workspace", "operational", "dense_data", "manager_visibility", "reconciliation"}
    for area in ("shell", "primary_work_surface", "navigation", "selection", "inspector", "search_commands", "history_audit", "status_progress", "persistence", "dense_data", "progressive_disclosure"):
        if area in {"dense_data", "history_audit", "status_progress", "persistence", "inspector", "search_commands"} and signals.intersection(workspace_signals):
            disposition = "EXPECTED"
        elif area in {"shell", "primary_work_surface", "navigation", "progressive_disclosure"} and materiality.get("material"):
            disposition = "REQUIRED"
        else:
            disposition = "OPTIONAL" if materiality.get("material") else "EXCLUDED"
        workspace[area] = {"disposition": disposition, "reason": "professional workspace model is task-aware; it is not loaded wholesale"}
    provenance_core = {
        "profile_fingerprint": profile["profile_fingerprint"],
        "raw_requirements_fingerprint": profile.get("raw_requirements_fingerprint"),
        "upstream_revision": loaded["provenance"]["upstream_revision"],
        "upstream_license": loaded["provenance"]["upstream_license"],
        "graph_sha256": loaded["provenance"]["graph_sha256"],
        "registry_sha256": loaded["provenance"]["registry_sha256"],
        "registry_fingerprint": loaded["provenance"]["registry_fingerprint"],
        "matched_rules": matched_rules,
        "activated_set": [item["id"] for item in activated_entries],
        "dependency_expansion": [item["id"] for item in activated_entries if item["activation_kind"] == "DEPENDENCY"],
        "high_impact_omissions": high_impact_omissions,
        "unknowns": sorted(set(unknowns)),
    }
    route_fingerprint = _sha256(provenance_core)
    return {
        "schema": ROUTE_SCHEMA,
        "status": "REDUCED_PATH" if materiality.get("reduced_path") else "ROUTED",
        "design_mode": "NUI_BACKED_DESIGN",
        "single_router": loaded["p2p_extension"]["single_router"],
        "profile_fingerprint": profile["profile_fingerprint"],
        "route_fingerprint": route_fingerprint,
        "materiality": dict(materiality),
        "signals": sorted(signals),
        "matched_rules": matched_rules,
        "activated_faculties": activated_entries,
        "activated_count": len(activated_entries),
        "registry_faculty_count": validation["faculty_count"],
        "loaded_faculty_content": [],
        "loaded_faculty_count": 0,
        "progressive_disclosure": {"registry_loaded": True, "bodies_preloaded": False, "deep_load_ids": [], "deep_load_status": "METADATA_ONLY"},
        "dispositions_supported": list(DISPOSITIONS),
        "optional_specialist": optional_specialist,
        "high_impact_omissions": high_impact_omissions,
        "unknowns": sorted(set(unknowns)),
        "workspace_completeness": workspace,
        "route_provenance": provenance_core,
        "permission_requests": [],
        "recommendations_grant_permissions": False,
        "agent_selection": [],
        "canonical_quorum": {"denominator": 8, "full_quorum": "8/8", "optional_specialists_counted": False},
    }


def _required_evidence(profile: Mapping[str, Any], route: Mapping[str, Any]) -> list[str]:
    required = ["task_profile", "route_provenance", "functional_closure", "independent_critique"]
    materiality = profile.get("materiality", {})
    if materiality.get("material") and not materiality.get("reduced_path"):
        required.extend(["rendered_ui", "accessibility_evidence", "responsive_or_platform_evidence"])
    if "high_impact" in route.get("signals", []) or "financial" in route.get("signals", []):
        required.extend(["decision_preview", "error_recovery_evidence"])
    return list(dict.fromkeys(required))


def build_obligation_plan(profile: Mapping[str, Any], route: Mapping[str, Any]) -> dict[str, Any]:
    """Build a lifecycle plan that projects to existing C10/C11/C12 owners."""

    validate_task_profile(profile)
    if route.get("profile_fingerprint") != profile.get("profile_fingerprint"):
        raise ProfileIntegrityError("ROUTING_PROFILE_MISMATCH")
    required_evidence = _required_evidence(profile, route)
    render_state = profile.get("runtime_capabilities", {}).get("render_state", "RENDER_UNKNOWN")
    material = bool(profile.get("materiality", {}).get("material"))
    render_required = material and not bool(profile.get("materiality", {}).get("reduced_path"))
    render_status = "NOT_REQUIRED" if not render_required else render_state
    if render_status == "RENDER_AVAILABLE":
        initial_done = "UNKNOWN"
        render_reason = "Runtime can render, but current rendered evidence has not been supplied."
    elif render_status == "RENDER_UNAVAILABLE":
        initial_done = "BLOCKED"
        render_reason = "Material UI requires render evidence when runtime allows; this runtime is unavailable."
    elif render_status == "RENDER_BLOCKED_PERMISSION":
        initial_done = "BLOCKED"
        render_reason = "Render is blocked by a host permission boundary; no permission is granted by recommendation."
    elif render_status == "RENDER_UNKNOWN":
        initial_done = "UNKNOWN"
        render_reason = "Render capability is unknown; do not invent a screenshot or claim UI completion."
    else:
        initial_done = "UNKNOWN"
        render_reason = "Render evidence is not yet bound."
    obligations = []
    for index, item in enumerate(route.get("activated_faculties", []), start=1):
        obligations.append({
            "obligation_id": f"design-{index:03d}-{item['id']}",
            "faculty_id": item["id"],
            "disposition": item["disposition"],
            "output": item["output"],
            "required_evidence": ["task_profile", "route_provenance"],
            "status": "PLANNED",
            "reason": item["activation_reasons"],
        })
    critique = {
        "independent": True,
        "generator_can_self_certify": False,
        "dimensions": ["hierarchy", "composition", "typography", "color", "interaction", "states", "accessibility", "responsive_or_platform_fit", "functional_completeness", "trust_and_uncertainty"],
        "findings": [],
        "missing_evidence_status": "UNKNOWN",
    }
    plan = {
        "schema": OBLIGATION_SCHEMA,
        "profile_fingerprint": profile["profile_fingerprint"],
        "route_fingerprint": route["route_fingerprint"],
        "design_lifecycle": list(NUI_LIFECYCLE),
        "exception_states": ["RECOVERY", "BLOCKED"],
        "obligations": obligations,
        "required_evidence": required_evidence,
        "c10_decision_trace": {"schema": "p2p-decision-trace/1", "authority": "C10", "reuse_existing_trace": True, "second_trace": False, "reference_only": True},
        "c11_task_projection": {"schema": "p2p-task-plan/1", "authority": "C11", "state_owner": "C11", "obligation_refs": [item["obligation_id"] for item in obligations], "required_evidence": required_evidence, "persist": False},
        "c12_execution_projection": {"schema": "p2p-foreground-execution-result/1", "authority": "C12", "state_path": list(C12_PATH), "execute": False, "persist": False},
        "render_preflight": {"state": render_status, "required": render_required, "reason": render_reason, "invented_capture_allowed": False},
        "render_evidence": {"status": "UNKNOWN" if render_required else "NOT_REQUIRED", "capture_matrix": [], "observations": []},
        "critique": critique,
        "generation_evaluation_separation": True,
        "correction_loop": {"max_iterations": 2, "iteration": 0, "bounded": True, "stop_on": ["PASS", "BLOCKED", "UNKNOWN", "NEEDS_OWNER"]},
        "ui_done": {"status": initial_done, "reason": render_reason, "build_is_not_ui_done": True},
        "accessibility_claim": {"automated_checks_are_not_complete_proof": True, "status": "UNKNOWN"},
        "responsive_claim": {"status": "UNKNOWN", "reauthoring_may_be_required": True},
        "native_residue_audit": {"status": "UNKNOWN", "required": "native_or_platform" in route.get("signals", [])},
        "permission_policy": {"permission_requests": [], "recommendations_grant_permissions": False, "authority": "C10_AND_HOST_GOVERNANCE"},
    }
    plan["plan_fingerprint"] = _sha256(plan)
    return plan


def evaluate_completion(plan: Mapping[str, Any], evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate a supplied evidence packet without claiming visual quality."""

    evidence = dict(evidence or {})
    required = list(plan.get("required_evidence", []))
    missing = [item for item in required if not evidence.get(item)]
    findings: list[str] = []
    render = plan.get("render_preflight", {})
    if render.get("required") and not evidence.get("rendered_ui"):
        missing.append("rendered_ui")
    critique = evidence.get("independent_critique")
    if critique and isinstance(critique, Mapping) and critique.get("producer") and critique.get("producer") == evidence.get("generator"):
        findings.append("CRITIQUE_NOT_INDEPENDENT")
    if findings:
        status = "BLOCKED"
    elif missing:
        status = "BLOCKED" if render.get("state") in {"RENDER_UNAVAILABLE", "RENDER_BLOCKED_PERMISSION"} else "UNKNOWN"
    else:
        status = "PASS"
    return {
        "schema": "p2p-ui-completion-evaluation/1",
        "status": status,
        "missing_evidence": sorted(set(missing)),
        "findings": findings,
        "claim": "BOUNDED_STRUCTURAL_COMPLETION" if status == "PASS" else "NO_COMPLETION_CLAIM",
        "ui_done": status == "PASS",
    }


def correction_loop(plan: Mapping[str, Any], findings: Iterable[Mapping[str, Any]] | None = None, iteration: int = 0) -> dict[str, Any]:
    """Return a bounded next step; it never loops or mutates plan state."""

    findings = list(findings or [])
    maximum = int(plan.get("correction_loop", {}).get("max_iterations", 2))
    if iteration >= maximum:
        return {"status": "BLOCKED", "reason": "CORRECTION_BUDGET_EXHAUSTED", "iteration": iteration, "max_iterations": maximum}
    if not findings:
        return {"status": "STOP", "reason": "NO_FINDINGS", "iteration": iteration, "max_iterations": maximum}
    return {"status": "CORRECT", "reason": "APPLY_BOUNDED_FINDINGS_AND_RECHECK", "iteration": iteration + 1, "max_iterations": maximum, "finding_count": len(findings)}


def design_intelligence_route(request: str, context: Mapping[str, Any] | None = None, registry_source: str | Path | None = None) -> dict[str, Any]:
    """Convenience boundary for beginner invocation and the existing router."""

    context = dict(context or {})
    profile = build_task_profile(request, context)
    if not profile["materiality"]["material"] and not profile["materiality"]["reduced_path"]:
        return {"schema": SCHEMA, "status": "NOT_APPLICABLE", "profile": profile, "reason": "NO_DESIGN_SURFACE"}
    try:
        registry = load_registry(registry_source)
    except (RegistryIntegrityError, OSError) as exc:
        return {
            "schema": SCHEMA,
            "status": "NUI_UNAVAILABLE",
            "design_mode": "P2P_NATIVE_DESIGN",
            "fallback": "P2P_NATIVE_DESIGN",
            "profile": profile,
            "reason": str(exc),
            "permission_requests": [],
            "recommendations_grant_permissions": False,
        }
    try:
        route = route_design_task(profile, registry)
        plan = build_obligation_plan(profile, route)
    except DesignIntelligenceError as exc:
        return {"schema": SCHEMA, "status": "REJECT", "profile": profile, "reason": str(exc)}
    return {"schema": SCHEMA, "status": "READY", "design_mode": "NUI_BACKED_DESIGN", "profile": profile, "route": route, "plan": plan}


__all__ = [
    "C12_PATH",
    "DISPOSITIONS",
    "MATERIALITY_CATEGORIES",
    "NUI_LIFECYCLE",
    "RENDER_STATES",
    "DesignIntelligenceError",
    "RegistryIntegrityError",
    "ProfileIntegrityError",
    "build_obligation_plan",
    "build_task_profile",
    "classify_materiality",
    "correction_loop",
    "design_intelligence_route",
    "evaluate_completion",
    "load_registry",
    "registry_path",
    "route_design_task",
    "validate_registry",
    "validate_task_profile",
]
