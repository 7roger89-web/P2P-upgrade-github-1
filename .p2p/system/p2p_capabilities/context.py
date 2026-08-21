"""Deterministic context pointers and the minimal Context-Efficient view.

The module deliberately stays a pure structured-data boundary.  It does not
call a model, persist a truth store, discover tools, or grant permissions.
``BASELINE_COMPAT`` keeps every supplied structured item in the initial view;
``CONTEXT_EFFICIENT_V1`` keeps required/direct items and replaces explicitly
deferred detail with authoritative pointers.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping

from orchestration_policy import (
    CONTEXT_CLASSES,
    CONTEXT_INSUFFICIENT,
    EXPANDED,
    MINIMAL,
    STANDARD,
)


CONTENT_CLASSES = ("CONTENT", "INSTRUCTION_AUTHORITY", "EVIDENCE", "SCHEMA", "UNKNOWN")
BASELINE_COMPAT = "BASELINE_COMPAT"
CONTEXT_EFFICIENT_V1 = "CONTEXT_EFFICIENT_V1"
CONTEXT_MODES = (BASELINE_COMPAT, CONTEXT_EFFICIENT_V1)
CONTEXT_VIEW_SCHEMA = "p2p-context-view/1"
CONTEXT_MANIFEST_SCHEMA = "p2p-context-manifest/1"
LOCAL_SERIALIZATION_PROXY = "LOCAL_SERIALIZATION_PROXY"
TASK_CONTEXT_SCHEMA = "p2p-task-targeted-context/1"
CONTEXT_REUSE_SCHEMA = "p2p-context-reuse/1"
KNOWLEDGE_DELTA_SCHEMA = "p2p-knowledge-delta/1"
RETRIEVAL_TIERS = (MINIMAL, STANDARD, EXPANDED)
COVERAGE_STATES = ("REQUIRED", "COVERED", "MISSING", "UNKNOWN", "NOT_APPLICABLE")
SUFFICIENCY_STATUSES = ("SUFFICIENT", "INSUFFICIENT", "STALE", "CONTRADICTED", "BLOCKED")
RETRIEVAL_FAILURES = (
    "NO_MATCH",
    "INSUFFICIENT_COVERAGE",
    "STALE_INDEX",
    "BROKEN_POINTER",
    "CONTRADICTED_SOURCE",
    "PERMISSION_BLOCKED",
    "CAPABILITY_UNAVAILABLE",
    "CONTROL_PLANE_FAILURE",
)
RETRIEVAL_ORDER = (
    "TASK_CONTRACT",
    "DIRECT_AUTHORITATIVE_REFS",
    "DEPENDENCY_OUTPUTS",
    "KNOWN_EVIDENCE",
    "PROJECT_REPO_MAP",
    "TARGETED_SOURCE",
)

ITEM_CATEGORIES = (
    "relevant_facts",
    "relevant_decisions",
    "direct_dependencies",
    "history",
    "plans",
    "archives",
    "agent_logs",
    "retrieval_inputs",
    "full_evidence",
    "documentation",
    "additional_context",
)
REQUIRED_CATEGORIES = {
    "relevant_facts",
    "relevant_decisions",
    "direct_dependencies",
}
SECRET_KEY_PARTS = (
    "secret",
    "token",
    "password",
    "credential",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "authorization",
    "env_vars",
    "environment_variables",
)
SECRET_KEY_RE = re.compile("(?:" + "|".join(re.escape(part) for part in SECRET_KEY_PARTS) + ")", re.IGNORECASE)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContextModeError(ValueError):
    """Raised when a caller requests a mode outside the two-mode contract."""


class ContextSafetyError(ValueError):
    """Raised when a compact view would drop required or authoritative data."""


class ContextBindingError(ValueError):
    """Raised when a pointer/source binding cannot be resolved safely."""


class StaleContextError(ContextBindingError):
    """Raised when a source hash no longer matches the context view."""


@dataclass(frozen=True)
class ContextPointer:
    pointer_id: str
    label: str
    relevance: tuple[str, ...]
    authority: str
    scope: tuple[str, ...]
    freshness: str
    provenance: str
    content_class: str
    load_policy: str = "ON_RESOLVE"
    sensitive: bool = False
    source_binding: str | None = None
    source_hash: str | None = None

    def __post_init__(self) -> None:
        if self.content_class not in CONTENT_CLASSES:
            raise ValueError("CONTENT_CLASS_INVALID")
        if not self.pointer_id or not self.provenance or not self.scope:
            raise ValueError("CONTEXT_POINTER_REQUIRED_FIELD")

    def metadata(self) -> dict[str, Any]:
        return asdict(self)


def select_context_mode(mode: str | None = None) -> str:
    """Return an explicitly requested mode, defaulting only to baseline.

    ``None`` is the normal-use default.  Empty or unknown strings fail closed
    so a receipt can never claim that an unrecognized mode executed.
    """

    if mode is None:
        return BASELINE_COMPAT
    if mode not in CONTEXT_MODES:
        raise ContextModeError(f"CONTEXT_MODE_INVALID: {mode}")
    return mode


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def context_fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def serialize_context(value: Any) -> bytes:
    """Serialize a view deterministically for local structural comparison."""

    return _canonical_bytes(value)


def _assert_no_secret_fields(value: Any, path: str = "context") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if SECRET_KEY_RE.search(key_text):
                raise ContextSafetyError(f"SECRET_FIELD_FORBIDDEN: {path}.{key_text}")
            _assert_no_secret_fields(child, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_no_secret_fields(child, f"{path}[{index}]")


def _safe_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        result = {str(key): _safe_value(child) for key, child in value.items()}
        _assert_no_secret_fields(result)
        return result
    if isinstance(value, tuple):
        return [_safe_value(child) for child in value]
    if isinstance(value, list):
        return [_safe_value(child) for child in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _relative_source_path(value: Any) -> str | None:
    if value is None or value == "":
        return None
    path = str(value).replace("\\", "/")
    if path.startswith("/") or re.match(r"^[A-Za-z]:/", path):
        raise ContextSafetyError("SOURCE_PATH_MUST_BE_PROJECT_RELATIVE")
    parts = PurePosixPath(path).parts
    if ".." in parts:
        raise ContextSafetyError("SOURCE_PATH_ANCESTOR_LEAK")
    return path


def _source_hash(value: Mapping[str, Any]) -> str:
    # When a catalog carries both content and a recorded hash, derive the
    # current value from content.  This makes stale-source detection work even
    # when a caller forgot to refresh the catalog's cached hash.
    if "content" in value:
        digest = context_fingerprint(value.get("content"))
    else:
        candidate = value.get("source_hash") or value.get("sha256") or value.get("fingerprint")
        if not candidate:
            raise ContextBindingError("SOURCE_HASH_REQUIRED")
        digest = str(candidate).lower()
    if not SHA256_RE.fullmatch(digest):
        raise ContextBindingError("SOURCE_HASH_INVALID")
    return digest


def _normalise_source_bindings(values: Any) -> list[dict[str, Any]]:
    if values is None:
        return []
    if not isinstance(values, (list, tuple)):
        raise ContextBindingError("SOURCE_BINDINGS_MUST_BE_LIST")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(values):
        if not isinstance(raw, Mapping):
            raise ContextBindingError("SOURCE_BINDING_MUST_BE_MAPPING")
        source_id = str(raw.get("source_id") or raw.get("id") or f"source:{index}")
        if source_id in seen:
            raise ContextBindingError(f"SOURCE_BINDING_DUPLICATE: {source_id}")
        seen.add(source_id)
        item = {
            "source_id": source_id,
            "path": _relative_source_path(raw.get("path")),
            "source_hash": _source_hash(raw),
            "source_class": str(raw.get("source_class") or raw.get("class") or "AUTHORITATIVE_SOURCE"),
            "required": bool(raw.get("required", False)),
        }
        result.append(item)
    return sorted(result, key=lambda item: item["source_id"])


def _normalise_pointer(raw: Any, index: int) -> dict[str, Any]:
    if isinstance(raw, ContextPointer):
        raw = raw.metadata()
    if not isinstance(raw, Mapping):
        raise ContextBindingError("EVIDENCE_POINTER_MUST_BE_MAPPING")
    pointer_id = str(raw.get("pointer_id") or raw.get("id") or f"pointer:{index}")
    item = {
        "pointer_id": pointer_id,
        "label": str(raw.get("label") or pointer_id),
        "relevance": _safe_value(raw.get("relevance") or []),
        "authority": str(raw.get("authority") or "AUTHORITATIVE_SOURCE"),
        "scope": _safe_value(raw.get("scope") or ["*"]),
        "freshness": str(raw.get("freshness") or "CURRENT"),
        "provenance": str(raw.get("provenance") or "EXPLICIT_SOURCE_REFERENCE"),
        "content_class": str(raw.get("content_class") or "EVIDENCE"),
        "load_policy": str(raw.get("load_policy") or "ON_RESOLVE"),
        "sensitive": bool(raw.get("sensitive", False)),
        "source_binding": raw.get("source_binding") or raw.get("source_id"),
        "source_hash": raw.get("source_hash") or raw.get("sha256"),
    }
    if item["content_class"] not in CONTENT_CLASSES:
        raise ContextBindingError("CONTENT_CLASS_INVALID")
    if item["source_binding"] is not None:
        item["source_binding"] = str(item["source_binding"])
    if item["source_hash"] is not None:
        item["source_hash"] = str(item["source_hash"]).lower()
    _assert_no_secret_fields(item)
    return item


def _normalise_pointers(values: Any) -> list[dict[str, Any]]:
    if values is None:
        return []
    if not isinstance(values, (list, tuple)):
        raise ContextBindingError("EVIDENCE_POINTERS_MUST_BE_LIST")
    result = [_normalise_pointer(raw, index) for index, raw in enumerate(values)]
    if len({item["pointer_id"] for item in result}) != len(result):
        raise ContextBindingError("EVIDENCE_POINTER_DUPLICATE")
    return sorted(result, key=lambda item: item["pointer_id"])


def _normalise_items(category: str, value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    values = value if isinstance(value, (list, tuple)) else [value]
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(values):
        if isinstance(raw, Mapping):
            item = {str(key): _safe_value(child) for key, child in raw.items()}
            item_id = str(item.get("item_id") or item.get("id") or f"{category}:{index}")
        else:
            item = {"value": _safe_value(raw)}
            item_id = f"{category}:{index}"
        item["item_id"] = item_id
        item["category"] = category
        item.setdefault("source_binding", None)
        item.setdefault("pointer_id", None)
        item.setdefault("required", False)
        _assert_no_secret_fields(item)
        result.append(item)
    return result


def _item_is_required(category: str, item: Mapping[str, Any]) -> bool:
    return category in REQUIRED_CATEGORIES or any(bool(item.get(key)) for key in ("required", "must_include", "direct", "directly_referenced", "include_in_context", "relevant"))


def _item_is_explicitly_deferred(item: Mapping[str, Any]) -> bool:
    return bool(item.get("defer") or item.get("deferred") or item.get("load_policy") == "ON_RESOLVE")


def _conflict_group(item: Mapping[str, Any]) -> str | None:
    value = item.get("conflict_group") or item.get("conflict_id")
    if value is not None:
        return str(value)
    if item.get("status") in {"CONFLICT", "CONTRADICTED"} and item.get("fact_key"):
        return str(item["fact_key"])
    return None


def _deferred_reference(category: str, item: Mapping[str, Any], pointers: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    pointer_id = item.get("pointer_id") or item.get("evidence_pointer")
    if pointer_id is None and item.get("source_binding"):
        matching = [key for key, pointer in pointers.items() if pointer.get("source_binding") == item.get("source_binding")]
        pointer_id = matching[0] if len(matching) == 1 else None
    if pointer_id is None or str(pointer_id) not in pointers:
        raise ContextSafetyError(f"DEFERRED_ITEM_POINTER_REQUIRED: {category}:{item.get('item_id')}")
    pointer = pointers[str(pointer_id)]
    if not pointer.get("source_binding"):
        raise ContextSafetyError(f"POINTER_SOURCE_BINDING_REQUIRED: {pointer_id}")
    return {
        "category": category,
        "item_id": str(item.get("item_id")),
        "pointer_id": str(pointer_id),
        "source_binding": str(pointer["source_binding"]),
    }


def _base_context(context: Mapping[str, Any], mode: str, preloaded: Mapping[str, list[dict[str, Any]]], deferred: list[dict[str, Any]], pointers: list[dict[str, Any]], sources: list[dict[str, Any]]) -> dict[str, Any]:
    access_contract = context.get("access_contract")
    if access_contract is None:
        access_contract = {
            "tools": _safe_value(context.get("tools", [])),
            "source_catalog": str(context.get("source_catalog") or "EXISTING_PROJECT_SOURCES"),
        }
    access_contract = _safe_value(access_contract)
    return {
        "schema": CONTEXT_VIEW_SCHEMA,
        "context_mode": mode,
        "experimental": mode == CONTEXT_EFFICIENT_V1,
        "default_context_mode": BASELINE_COMPAT,
        "goal_id": _safe_value(context.get("goal_id")),
        "task_or_goal": _safe_value(context.get("task_or_goal")),
        "scope": _safe_value(context.get("scope", [])),
        "non_scope": _safe_value(context.get("non_scope", [])),
        "acceptance": _safe_value(context.get("acceptance", [])),
        "relevant_facts": preloaded.get("relevant_facts", []),
        "relevant_decisions": preloaded.get("relevant_decisions", []),
        "direct_dependencies": preloaded.get("direct_dependencies", []),
        "evidence_pointers": pointers,
        "capability_constraints": _safe_value(context.get("capability_constraints", [])),
        "permission_constraints": _safe_value(context.get("permission_constraints", [])),
        "source_bindings": sources,
        "preloaded": {category: preloaded.get(category, []) for category in ITEM_CATEGORIES},
        "deferred_or_omitted": deferred,
        "task_targeted_context": _safe_value(context.get("task_targeted_context") or {}),
        "access_contract": access_contract,
    }


def build_context_view(context: Mapping[str, Any], mode: str | None = None) -> dict[str, Any]:
    """Build the deterministic initial context view for one explicit mode."""

    if not isinstance(context, Mapping):
        raise ContextSafetyError("CONTEXT_INPUT_MUST_BE_MAPPING")
    selected_mode = select_context_mode(mode)
    sources = _normalise_source_bindings(context.get("source_bindings", []))
    pointers = _normalise_pointers(context.get("evidence_pointers", []))
    pointer_map = {item["pointer_id"]: item for item in pointers}
    source_by_id = {item["source_id"]: item for item in sources}
    source_ids = set(source_by_id)
    for pointer in pointers:
        if pointer.get("source_binding") and str(pointer["source_binding"]) not in source_ids:
            raise ContextBindingError(f"POINTER_SOURCE_NOT_BOUND: {pointer['pointer_id']}")
        source_binding = str(pointer["source_binding"]) if pointer.get("source_binding") else None
        pointer_hash = str(pointer["source_hash"]).lower() if pointer.get("source_hash") else None
        if source_binding and pointer_hash and pointer_hash != str(source_by_id[source_binding]["source_hash"]).lower():
            raise ContextBindingError(f"POINTER_SOURCE_HASH_MISMATCH: {pointer['pointer_id']}")
    categories = {
        category: _normalise_items(category, context.get(category))
        for category in ITEM_CATEGORIES
    }

    preloaded: dict[str, list[dict[str, Any]]] = {}
    deferred: list[dict[str, Any]] = []
    included_ids: list[str] = []
    omitted_ids: list[str] = []
    selection_warnings: list[str] = []

    for category in ITEM_CATEGORIES:
        items = categories[category]
        if selected_mode == BASELINE_COMPAT:
            chosen = list(items)
        else:
            chosen = []
            for item in items:
                include = _item_is_required(category, item) or not _item_is_explicitly_deferred(item)
                if item.get("ambiguous") and not _item_is_required(category, item):
                    include = True
                    selection_warnings.append(f"AMBIGUOUS_INCLUDE:{category}:{item['item_id']}")
                if include:
                    chosen.append(item)
                else:
                    omitted_ids.append(f"{category}:{item['item_id']}")

            selected_groups = {
                group for item in chosen if (group := _conflict_group(item))
            }
            for item in items:
                group = _conflict_group(item)
                if group and group in selected_groups and item not in chosen:
                    chosen.append(item)
                    omitted_ids = [value for value in omitted_ids if value != f"{category}:{item['item_id']}"]

        preloaded[category] = chosen
        included_ids.extend(f"{category}:{item['item_id']}" for item in chosen)
        if selected_mode == CONTEXT_EFFICIENT_V1:
            for item in items:
                if item not in chosen:
                    reference = _deferred_reference(category, item, pointer_map)
                    deferred.append(reference)

    # Required fields are always carried as structured top-level fields.  A
    # required mapping must not become a silent omitted pointer.
    core = _base_context(context, selected_mode, preloaded, deferred, pointers, sources)
    core["selection_policy"] = (
        "CURRENT_WORKFLOW_STRUCTURED_CONTEXT" if selected_mode == BASELINE_COMPAT else "EXPLICIT_REQUIRED_DIRECT_OR_POINTER"
    )
    core["selection_warnings"] = sorted(set(selection_warnings))
    core["compatibility_limitations"] = [
        "Exact official .15 byte/order parity is not established; compatibility is with the current structured workflow contract."
    ]
    core["included_item_ids"] = included_ids
    core["excluded_item_ids"] = omitted_ids
    core["deferred_pointer_ids"] = [item["pointer_id"] for item in deferred]
    _assert_no_secret_fields(core)

    fingerprint_payload = dict(core)
    fingerprint = context_fingerprint(fingerprint_payload)
    serialized_size = len(serialize_context(fingerprint_payload))
    manifest = {
        "schema": CONTEXT_MANIFEST_SCHEMA,
        "context_mode": selected_mode,
        "included_items": included_ids,
        "excluded_or_deferred_categories": sorted({item["category"] for item in deferred}),
        "excluded_or_deferred_items": deferred,
        "source_bindings": sources,
        "pointer_bindings": [
            {
                "pointer_id": item["pointer_id"],
                "source_binding": item.get("source_binding"),
                "source_hash": item.get("source_hash"),
            }
            for item in pointers
        ],
        "relevant_source_fingerprints": [
            {"source_id": item["source_id"], "source_hash": item["source_hash"]}
            for item in sources
            if item.get("required") or item["source_id"] in {str(ref.get("source_binding")) for ref in deferred}
        ],
        "task_targeted_context": _safe_value(context.get("task_targeted_context") or {}),
        "context_fingerprint": fingerprint,
        "serialized_size": {"label": LOCAL_SERIALIZATION_PROXY, "bytes": serialized_size},
    }
    _assert_no_secret_fields(manifest)
    return {
        **core,
        "context_fingerprint": fingerprint,
        "context_manifest": manifest,
        "serialized_size": {"label": LOCAL_SERIALIZATION_PROXY, "bytes": serialized_size},
    }


def _catalog_by_id(source_catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    if isinstance(source_catalog, Mapping):
        result = {}
        for key, value in source_catalog.items():
            if not isinstance(value, Mapping):
                raise ContextBindingError(f"SOURCE_CATALOG_ENTRY_INVALID: {key}")
            result[str(key)] = value
        return result
    result = {}
    for value in source_catalog:
        if not isinstance(value, Mapping):
            raise ContextBindingError("SOURCE_CATALOG_ENTRY_INVALID")
        source_id = str(value.get("source_id") or value.get("id") or "")
        if not source_id:
            raise ContextBindingError("SOURCE_CATALOG_ID_REQUIRED")
        result[source_id] = value
    return result


def validate_context_bindings(view: Mapping[str, Any], source_catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Reject a view when any bound authoritative source is missing or stale."""

    catalog = _catalog_by_id(source_catalog)
    checked: list[str] = []
    for binding in view.get("source_bindings", []):
        source_id = str(binding.get("source_id"))
        source = catalog.get(source_id)
        if source is None:
            raise ContextBindingError(f"SOURCE_NOT_FOUND: {source_id}")
        actual = _source_hash(source)
        if actual != str(binding.get("source_hash", "")).lower():
            raise StaleContextError(f"CONTEXT_SOURCE_STALE: {source_id}")
        checked.append(source_id)
    return {"status": "CURRENT", "checked_source_bindings": sorted(checked)}


def resolve_context_pointer(view: Mapping[str, Any], pointer_id: str, source_catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Resolve a compact pointer to its current authoritative source record."""

    catalog = _catalog_by_id(source_catalog)
    validate_context_bindings(view, catalog)
    pointers = list(view.get("evidence_pointers", []))
    pointers.extend(
        {
            "pointer_id": item.get("pointer_id"),
            "source_binding": item.get("source_binding"),
        }
        for item in view.get("deferred_or_omitted", [])
    )
    pointer = next((item for item in pointers if str(item.get("pointer_id")) == str(pointer_id)), None)
    if pointer is None:
        raise ContextBindingError(f"POINTER_NOT_FOUND: {pointer_id}")
    source_id = pointer.get("source_binding")
    if not source_id:
        raise ContextBindingError(f"POINTER_SOURCE_BINDING_REQUIRED: {pointer_id}")
    source = catalog.get(str(source_id))
    if source is None:
        raise ContextBindingError(f"SOURCE_NOT_FOUND: {source_id}")
    safe_source = _safe_value(source)
    _assert_no_secret_fields(safe_source)
    return {
        "status": "RESOLVED",
        "pointer_id": str(pointer_id),
        "source_binding": str(source_id),
        "source": safe_source,
        "authoritative": True,
    }


def _matches(pointer: ContextPointer, request: str, scope: str | None) -> bool:
    lowered = request.lower()
    relevance = any(term.lower() in lowered for term in pointer.relevance)
    in_scope = scope is None or scope in pointer.scope or "*" in pointer.scope
    return relevance and in_scope


def resolve_context(pointers: Iterable[ContextPointer], request: str, *, scope: str | None = None, now: str | None = None) -> dict[str, Any]:
    """Resolve legacy pointer metadata without changing its existing contract."""

    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for pointer in pointers:
        item = pointer.metadata()
        if not _matches(pointer, request, scope):
            item["status"] = "NOT_RELEVANT"
            excluded.append(item)
            continue
        if pointer.content_class == "UNKNOWN" or not pointer.provenance:
            item["status"] = "UNKNOWN"
            excluded.append(item)
            continue
        if pointer.freshness.upper() in {"EXPIRED", "STALE"}:
            item["status"] = "STALE"
            excluded.append(item)
            continue
        item["status"] = "RESOLVED"
        item["loaded"] = pointer.load_policy == "ON_DISCOVERY"
        item["resolved_at"] = now or datetime.now(timezone.utc).isoformat()
        selected.append(item)
    return {
        "schema": "p2p-context-resolution/1",
        "request": request,
        "scope": scope,
        "selected": selected,
        "excluded": excluded,
        "progressive_disclosure": True,
        "content_grants_permissions": False,
    }


# C19 extends the C06 capability below.  These helpers intentionally remain
# pure structured-data operations: callers own persistence and may choose to
# write the returned manifest through the existing workflow/ledger surfaces.


def _string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple, set)):
        raise ContextSafetyError(f"{field.upper()}_MUST_BE_LIST")
    result = [str(item).strip() for item in value if str(item).strip()]
    if len(result) != len(set(result)):
        raise ContextSafetyError(f"{field.upper()}_DUPLICATE")
    return result


def _reference_id(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("source_id") or value.get("id") or value.get("pointer_id") or value.get("path") or "").strip()
    return str(value).strip()


def _source_records(source_catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    raw_values = source_catalog.values() if isinstance(source_catalog, Mapping) else source_catalog
    records: dict[str, dict[str, Any]] = {}
    for raw in raw_values:
        if not isinstance(raw, Mapping):
            raise ContextBindingError("SOURCE_CATALOG_ENTRY_INVALID")
        source_id = str(raw.get("source_id") or raw.get("id") or "").strip()
        if not source_id or source_id in records:
            raise ContextBindingError("SOURCE_CATALOG_ID_REQUIRED_OR_DUPLICATE")
        record = {str(key): _safe_value(value) for key, value in raw.items()}
        record["source_id"] = source_id
        if record.get("path") is not None:
            record["path"] = _relative_source_path(record.get("path"))
        declared = record.get("source_hash") or record.get("sha256") or record.get("fingerprint")
        current = context_fingerprint(record.get("content")) if "content" in record else declared
        if not current or not SHA256_RE.fullmatch(str(current).lower()):
            raise ContextBindingError(f"SOURCE_HASH_REQUIRED_OR_INVALID: {source_id}")
        record["source_hash"] = str(current).lower()
        record["source_class"] = str(record.get("source_class") or record.get("class") or "AUTHORITATIVE_PROJECT_SOURCE")
        record["retrieval_role"] = str(record.get("retrieval_role") or record.get("role") or "TARGETED_SOURCE")
        record["scope"] = _string_list(record.get("scope") or ["*"], f"source_scope:{source_id}")
        record["coverage_ids"] = _string_list(record.get("coverage_ids") or record.get("coverage") or [], f"coverage_ids:{source_id}")
        record["readable"] = bool(record.get("readable", True))
        records[source_id] = record
    return records


def _task_refs(task: Mapping[str, Any], *names: str) -> list[str]:
    refs: list[str] = []
    for name in names:
        values = task.get(name, [])
        if isinstance(values, Mapping):
            values = [values]
        if values is None:
            continue
        if not isinstance(values, (list, tuple, set)):
            values = [values]
        refs.extend(reference for raw in values if (reference := _reference_id(raw)) and reference not in refs)
    return refs


def _acceptance_obligations(task: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_values = task.get("acceptance") or task.get("coverage_requirements") or []
    if not isinstance(raw_values, (list, tuple)):
        raise ContextSafetyError("ACCEPTANCE_MUST_BE_LIST")
    obligations: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_values):
        if isinstance(raw, Mapping):
            item = {str(key): _safe_value(value) for key, value in raw.items()}
        else:
            item = {"description": _safe_value(raw)}
        coverage_id = str(item.get("coverage_id") or item.get("id") or item.get("item_id") or f"acceptance:{index}")
        applicable = bool(item.get("applicable", True))
        required = bool(item.get("required", True))
        refs = _string_list(
            item.get("source_ids")
            or item.get("source_refs")
            or item.get("authoritative_refs")
            or item.get("refs")
            or [],
            f"acceptance_refs:{coverage_id}",
        )
        obligations.append(
            {
                "coverage_id": coverage_id,
                "description": str(item.get("description") or item.get("name") or coverage_id),
                "required": required,
                "applicable": applicable,
                "source_refs": refs,
                "scope": _string_list(item.get("scope") or ["*"], f"acceptance_scope:{coverage_id}"),
                "authority": str(item.get("authority") or "AUTHORITATIVE_PROJECT_SOURCE"),
            }
        )
    return obligations


def _tier_roles(context_class: str) -> tuple[str, ...]:
    if context_class == MINIMAL:
        return ("DIRECT_AUTHORITATIVE_REFS",)
    if context_class == STANDARD:
        return ("DIRECT_AUTHORITATIVE_REFS", "DEPENDENCY_OUTPUTS", "KNOWN_EVIDENCE")
    if context_class == EXPANDED:
        return ("DIRECT_AUTHORITATIVE_REFS", "DEPENDENCY_OUTPUTS", "KNOWN_EVIDENCE", "PROJECT_REPO_MAP", "TARGETED_SOURCE")
    raise ContextSafetyError(f"CONTEXT_CLASS_INVALID: {context_class}")


def _source_role(record: Mapping[str, Any]) -> str:
    role = str(record.get("retrieval_role") or record.get("role") or "TARGETED_SOURCE").upper()
    aliases = {
        "DIRECT": "DIRECT_AUTHORITATIVE_REFS",
        "DIRECT_REF": "DIRECT_AUTHORITATIVE_REFS",
        "DEPENDENCY": "DEPENDENCY_OUTPUTS",
        "EVIDENCE": "KNOWN_EVIDENCE",
        "MAP": "PROJECT_REPO_MAP",
        "TARGET": "TARGETED_SOURCE",
    }
    return aliases.get(role, role)


def _source_matches_ref(record: Mapping[str, Any], refs: set[str]) -> bool:
    if not refs:
        return False
    values = {str(record.get("source_id", "")), str(record.get("path", ""))}
    symbols = record.get("symbols", [])
    if isinstance(symbols, (list, tuple)):
        values.update(str(item) for item in symbols)
    return bool(values & refs)


def _source_is_stale(record: Mapping[str, Any], candidate_binding: str | None) -> str | None:
    if str(record.get("freshness", "CURRENT")).upper() in {"STALE", "EXPIRED"}:
        return "STALE_INDEX" if _source_role(record) == "PROJECT_REPO_MAP" else "STALE_SOURCE"
    if not bool(record.get("readable", True)) or str(record.get("permission", "ALLOWED")).upper() in {"DENIED", "BLOCKED"}:
        return "PERMISSION_BLOCKED"
    if candidate_binding and record.get("candidate_binding") and str(record.get("candidate_binding")) != candidate_binding:
        return "STALE_CANDIDATE_BINDING"
    declared = record.get("declared_source_hash")
    if declared and str(declared).lower() != str(record.get("source_hash")).lower():
        return "STALE_SOURCE"
    if _source_role(record) == "PROJECT_REPO_MAP" and record.get("map_fingerprint") and record.get("candidate_fingerprint"):
        if candidate_binding and str(record.get("candidate_fingerprint")) != candidate_binding:
            return "STALE_INDEX"
    return None


def _coverage_for_source(obligation: Mapping[str, Any], record: Mapping[str, Any]) -> bool:
    refs = set(str(item) for item in obligation.get("source_refs", []))
    if _source_matches_ref(record, refs):
        return True
    coverage_ids = set(str(item) for item in record.get("coverage_ids", []))
    if str(obligation.get("coverage_id")) in coverage_ids:
        return True
    source_scope = set(str(item) for item in record.get("scope", ["*"]))
    obligation_scope = set(str(item) for item in obligation.get("scope", ["*"]))
    return "*" in source_scope and not refs and not coverage_ids and "*" in obligation_scope and bool(record.get("covers_all", False))


def _next_context_class(context_class: str) -> str | None:
    if context_class == MINIMAL:
        return STANDARD
    if context_class == STANDARD:
        return EXPANDED
    return None


def _coverage_summary(coverage: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {state: 0 for state in COVERAGE_STATES}
    for item in coverage:
        requirement_state = str(item.get("requirement_state") or "UNKNOWN")
        if requirement_state in counts:
            counts[requirement_state] += 1
        status = str(item.get("status") or "UNKNOWN")
        if status in counts:
            counts[status] += 1
    required = [item for item in coverage if item.get("required") and item.get("status") != "NOT_APPLICABLE"]
    covered = [item for item in required if item.get("status") == "COVERED"]
    return {
        "counts": counts,
        "required_count": len(required),
        "covered_required_count": len(covered),
        "required_coverage_ratio": (len(covered) / len(required)) if required else 1.0,
        "required_complete": len(required) == len(covered),
    }


def retrieve_task_context(
    task: Mapping[str, Any],
    source_catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    *,
    context_class: str = MINIMAL,
    candidate_binding: str | None = None,
    allow_external: bool = False,
) -> dict[str, Any]:
    """Select a bounded, authoritative context plan from explicit task metadata.

    Selection is deterministic and reference/coverage driven.  It never treats
    generic similarity, model confidence, or the existence of related files as
    proof that an acceptance obligation is covered.
    """

    if not isinstance(task, Mapping):
        raise ContextSafetyError("TASK_CONTRACT_MUST_BE_MAPPING")
    if context_class not in CONTEXT_CLASSES:
        raise ContextSafetyError(f"CONTEXT_CLASS_INVALID: {context_class}")
    if context_class == CONTEXT_INSUFFICIENT:
        return {
            "schema": TASK_CONTEXT_SCHEMA,
            "context_class": CONTEXT_INSUFFICIENT,
            "status": "BLOCKED",
            "failure_reasons": ["CONTEXT_INSUFFICIENT"],
            "coverage": [],
            "coverage_summary": _coverage_summary([]),
            "retrieval_order": list(RETRIEVAL_ORDER),
        }

    records = _source_records(source_catalog)
    obligations = _acceptance_obligations(task)
    roles = _tier_roles(context_class)
    refs_by_role = {
        "DIRECT_AUTHORITATIVE_REFS": _task_refs(task, "direct_authoritative_refs", "direct_refs"),
        "DEPENDENCY_OUTPUTS": _task_refs(task, "dependency_outputs", "dependency_refs", "dependencies"),
        "KNOWN_EVIDENCE": _task_refs(task, "known_evidence", "evidence_refs", "fact_refs"),
        "PROJECT_REPO_MAP": _task_refs(task, "project_repo_map", "project_map_refs", "repo_map_refs"),
        "TARGETED_SOURCE": _task_refs(task, "targeted_source_refs", "targeted_sources", "source_refs"),
    }
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    failure_reasons: list[str] = []
    seen: set[str] = set()
    for role in roles:
        explicit_refs = set(refs_by_role.get(role, []))
        candidates = [
            record
            for record in records.values()
            if _source_role(record) == role
            and (not explicit_refs or _source_matches_ref(record, explicit_refs))
        ]
        for record in sorted(candidates, key=lambda item: (str(item.get("source_class")), str(item.get("source_id")))):
            source_id = str(record["source_id"])
            if source_id in seen:
                continue
            if str(record.get("source_class", "")).upper() == "EXTERNAL" and not allow_external:
                excluded.append({"source_id": source_id, "reason": "EXTERNAL_RETRIEVAL_NOT_AUTHORIZED"})
                continue
            stale_reason = _source_is_stale(record, candidate_binding)
            if stale_reason:
                excluded.append({"source_id": source_id, "reason": stale_reason})
                if stale_reason == "PERMISSION_BLOCKED":
                    failure_reasons.append("PERMISSION_BLOCKED")
                elif stale_reason in {"STALE_INDEX", "STALE_SOURCE", "STALE_CANDIDATE_BINDING"}:
                    failure_reasons.append(stale_reason)
                continue
            selected.append(
                {
                    "source_id": source_id,
                    "source_hash": record["source_hash"],
                    "path": record.get("path"),
                    "source_class": record.get("source_class"),
                    "retrieval_role": role,
                    "pointer_id": record.get("pointer_id") or f"pointer-{source_id}",
                    "scope": record.get("scope", ["*"]),
                }
            )
            seen.add(source_id)

    coverage: list[dict[str, Any]] = []
    for obligation in obligations:
        if not obligation["applicable"]:
            status = "NOT_APPLICABLE"
            matched: list[str] = []
        else:
            matched = [item["source_id"] for item in selected if _coverage_for_source(obligation, records[item["source_id"]])]
            if matched:
                status = "COVERED"
            elif obligation["source_refs"] and not (set(obligation["source_refs"]) & set(records)):
                status = "MISSING"
                failure_reasons.append("BROKEN_POINTER")
            elif not obligation["source_refs"] and not any(_coverage_for_source(obligation, record) for record in records.values()):
                status = "UNKNOWN"
            else:
                status = "MISSING"
        coverage.append(
            {
                "coverage_id": obligation["coverage_id"],
                "description": obligation["description"],
                "required": obligation["required"],
                "requirement_state": "REQUIRED" if obligation["required"] else "NOT_APPLICABLE",
                "status": status,
                "source_ids": sorted(matched),
            }
        )

    selected_records = [records[item["source_id"]] for item in selected]
    conflict_groups: dict[str, list[dict[str, Any]]] = {}
    for record in selected_records:
        group = record.get("conflict_group") or record.get("conflict_id")
        if group:
            conflict_groups.setdefault(str(group), []).append(record)
    contradictions = sorted(group for group, items in conflict_groups.items() if len(items) > 1 and not any(bool(item.get("resolved")) for item in items))
    if contradictions:
        failure_reasons.append("CONTRADICTED_SOURCE")

    summary = _coverage_summary(coverage)
    required_unresolved = not bool(summary["required_complete"])
    next_class = _next_context_class(context_class) if required_unresolved else None
    if contradictions:
        status = "CONTRADICTED"
    elif any(reason in {"PERMISSION_BLOCKED", "BROKEN_POINTER"} for reason in failure_reasons):
        status = "BLOCKED"
    elif any(reason in {"STALE_INDEX", "STALE_SOURCE", "STALE_CANDIDATE_BINDING"} for reason in failure_reasons):
        status = "STALE"
    elif required_unresolved:
        status = "INSUFFICIENT"
    else:
        status = "SUFFICIENT"

    if status == "INSUFFICIENT" and context_class == EXPANDED:
        effective_class = CONTEXT_INSUFFICIENT
        failure_reasons.append("INSUFFICIENT_COVERAGE")
    else:
        effective_class = context_class
    source_bindings = [
        {"source_id": item["source_id"], "source_hash": item["source_hash"], "scope": item["scope"]}
        for item in selected
    ]
    manifest = {
        "schema": TASK_CONTEXT_SCHEMA,
        "context_class": effective_class,
        "requested_context_class": context_class,
        "task_purpose": str(task.get("task_purpose") or task.get("purpose") or task.get("task_or_goal") or ""),
        "scope": _string_list(task.get("scope") or ["current-task"], "task_scope"),
        "candidate_binding": candidate_binding,
        "retrieval_order": list(RETRIEVAL_ORDER),
        "selected_source_ids": [item["source_id"] for item in selected],
        "source_bindings": source_bindings,
        "coverage": coverage,
        "coverage_summary": summary,
        "excluded": excluded,
        "failure_reasons": sorted(set(failure_reasons)),
        "contradictions": contradictions,
        "materialization": {"available_source_count": len(records), "selected_source_count": len(selected)},
    }
    manifest["context_fingerprint"] = context_fingerprint(manifest)
    return {
        **manifest,
        "status": status,
        "sufficiency_status": status,
        "next_context_class": next_class,
        "context_class": effective_class,
        "bounded_escalation": {"current": context_class, "next": next_class, "max_class": EXPANDED},
        "available_context": {"source_ids": sorted(records), "count": len(records)},
        "materialized_context": {"source_ids": [item["source_id"] for item in selected], "count": len(selected)},
        "local_serialization_proxy": {"label": LOCAL_SERIALIZATION_PROXY, "bytes": len(serialize_context(manifest))},
    }


def escalate_task_context(
    task: Mapping[str, Any],
    source_catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    prior_plan: Mapping[str, Any],
    *,
    candidate_binding: str | None = None,
    allow_external: bool = False,
) -> dict[str, Any]:
    """Perform at most one bounded tier expansion from a prior plan."""

    current = str(prior_plan.get("requested_context_class") or prior_plan.get("context_class") or MINIMAL)
    if current not in RETRIEVAL_TIERS:
        raise ContextSafetyError("CONTEXT_ESCALATION_STATE_INVALID")
    next_class = _next_context_class(current)
    if not next_class:
        return {
            "schema": TASK_CONTEXT_SCHEMA,
            "status": "INSUFFICIENT",
            "sufficiency_status": "INSUFFICIENT",
            "context_class": CONTEXT_INSUFFICIENT,
            "requested_context_class": EXPANDED,
            "next_context_class": None,
            "failure_reasons": ["INSUFFICIENT_COVERAGE"],
            "coverage": list(prior_plan.get("coverage", [])),
            "coverage_summary": prior_plan.get("coverage_summary", _coverage_summary([])),
        }
    return retrieve_task_context(
        task,
        source_catalog,
        context_class=next_class,
        candidate_binding=candidate_binding if candidate_binding is not None else prior_plan.get("candidate_binding"),
        allow_external=allow_external,
    )


def validate_context_reuse(
    cached_context: Mapping[str, Any],
    source_catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    *,
    candidate_binding: str | None,
    required_scope: Iterable[str],
) -> dict[str, Any]:
    """Validate a derived context artifact against current authoritative inputs."""

    if not isinstance(cached_context, Mapping):
        raise ContextSafetyError("CACHED_CONTEXT_MUST_BE_MAPPING")
    records = _source_records(source_catalog)
    expected_scope = sorted(set(str(item) for item in required_scope))
    cached_scope = sorted(set(str(item) for item in cached_context.get("scope") or cached_context.get("required_scope") or []))
    cached_candidate = cached_context.get("candidate_binding")
    reasons: list[str] = []
    for binding in cached_context.get("source_bindings", []):
        if not isinstance(binding, Mapping):
            reasons.append("BROKEN_POINTER")
            continue
        source_id = str(binding.get("source_id") or "")
        record = records.get(source_id)
        if record is None:
            reasons.append("BROKEN_POINTER")
            continue
        if str(binding.get("source_hash", "")).lower() != str(record.get("source_hash", "")).lower():
            reasons.append("STALE_SOURCE")
        stale_reason = _source_is_stale(record, candidate_binding)
        if stale_reason:
            reasons.append(stale_reason)
    if cached_candidate != candidate_binding:
        reasons.append("STALE_CANDIDATE_BINDING")
    if cached_scope != expected_scope:
        reasons.append("REQUIRED_SCOPE_MISMATCH")
    if str(cached_context.get("freshness", "CURRENT")).upper() in {"STALE", "EXPIRED"}:
        reasons.append("STALE_SOURCE")
    reusable = not reasons
    return {
        "schema": CONTEXT_REUSE_SCHEMA,
        "status": "REUSABLE" if reusable else "STALE",
        "reusable": reusable,
        "reason_codes": sorted(set(reasons)),
        "candidate_binding": candidate_binding,
        "required_scope": expected_scope,
        "checked_source_ids": sorted(str(item.get("source_id")) for item in cached_context.get("source_bindings", []) if isinstance(item, Mapping)),
        "authority": "CURRENT_AUTHORITATIVE_SOURCE_BINDINGS",
    }


def materialize_task_context(
    plan: Mapping[str, Any],
    source_catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    *,
    role: str = "PARENT",
) -> dict[str, Any]:
    """Separate known artifacts from the bounded context materialized to a role."""

    role = str(role).upper()
    if role not in {"PARENT", "WORKER"}:
        raise ContextSafetyError("MATERIALIZATION_ROLE_INVALID")
    records = _source_records(source_catalog)
    selected_ids = [str(item) for item in plan.get("selected_source_ids", [])]
    selected = [records[item] for item in selected_ids if item in records]
    available = {
        "source_ids": sorted(records),
        "count": len(records),
        "pointer_count": len(plan.get("source_bindings", [])),
    }
    authority_manifest = {
        "context_fingerprint": plan.get("context_fingerprint"),
        "context_class": plan.get("context_class"),
        "coverage": plan.get("coverage", []),
        "source_bindings": plan.get("source_bindings", []),
        "candidate_binding": plan.get("candidate_binding"),
    }
    materialized: list[dict[str, Any]] = []
    if role == "WORKER":
        for record in selected:
            item = {
                "source_id": record["source_id"],
                "path": record.get("path"),
                "source_hash": record["source_hash"],
                "scope": record.get("scope", ["*"]),
            }
            if "content" in record:
                item["content"] = _safe_value(record["content"])
            materialized.append(item)
    return {
        "schema": TASK_CONTEXT_SCHEMA,
        "role": role,
        "available_context": available,
        "materialized_context": {
            "source_ids": [item["source_id"] for item in materialized],
            "items": materialized,
            "count": len(materialized),
            "label": LOCAL_SERIALIZATION_PROXY,
            "bytes": len(serialize_context(materialized)),
        },
        "authority_manifest": authority_manifest,
        "permission_expansion": False,
        "parent_history_included": False,
    }


def build_knowledge_delta(
    discovered_sources: Iterable[Mapping[str, Any]],
    *,
    coverage_updates: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Return references/deltas only; never persist or copy a worker transcript."""

    records = _source_records(list(discovered_sources))
    bindings = [
        {"source_id": record["source_id"], "source_hash": record["source_hash"], "scope": record.get("scope", ["*"])}
        for record in sorted(records.values(), key=lambda item: item["source_id"])
    ]
    updates = [_safe_value(item) for item in coverage_updates if isinstance(item, Mapping)]
    return {
        "schema": KNOWLEDGE_DELTA_SCHEMA,
        "new_source_bindings": bindings,
        "coverage_updates": updates,
        "transcript_included": False,
        "authority": "PARENT_MUST_REVALIDATE_AGAINST_CURRENT_SOURCES",
    }
