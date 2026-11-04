from __future__ import annotations

"""Read-only context budget audit over an existing P2P context view.

This module does not select context, mutate task state, infer host loading
behavior, or drop authority-bearing material. It measures the context view P2P
already built and reports which preloaded items are required versus optional,
which items are already deferred behind pointers, and whether an explicit
caller-supplied byte budget is exceeded.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPORT_SCHEMA = "p2p-context-budget-report/1"
CAPABILITY_ID = "P2P_CONTEXT_BUDGET_01"
CONTEXT_VIEW_SCHEMA = "p2p-context-view/1"
LOCAL_SERIALIZATION_PROXY = "LOCAL_SERIALIZATION_PROXY"

_REQUIRED_CATEGORIES = {
    "relevant_facts",
    "relevant_decisions",
    "direct_dependencies",
}
_REQUIRED_FLAGS = (
    "required",
    "must_include",
    "direct",
    "directly_referenced",
    "include_in_context",
    "relevant",
)
_HOST_RE = re.compile(r"^[A-Z0-9_.:/-]{1,64}$")


class ContextBudgetError(ValueError):
    """Raised when a context view cannot be audited safely."""


def _canonical_size(value: Any) -> int:
    try:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContextBudgetError("CONTEXT_BUDGET_VALUE_NOT_JSON_SERIALIZABLE") from exc
    return len(payload)


def _normalise_host(value: str | None) -> str:
    if value is None or not str(value).strip():
        return "UNKNOWN"
    host = str(value).strip().upper().replace(" ", "_")
    if not _HOST_RE.fullmatch(host):
        raise ContextBudgetError("HOST_LABEL_INVALID")
    return host


def _is_required(category: str, item: Mapping[str, Any]) -> bool:
    if category in _REQUIRED_CATEGORIES:
        return True
    return any(bool(item.get(flag)) for flag in _REQUIRED_FLAGS)


def _validate_view(view: Mapping[str, Any]) -> tuple[Mapping[str, Any], list[Any], int, str]:
    if not isinstance(view, Mapping):
        raise ContextBudgetError("CONTEXT_VIEW_MUST_BE_OBJECT")
    if str(view.get("schema")) != CONTEXT_VIEW_SCHEMA:
        raise ContextBudgetError("CONTEXT_VIEW_SCHEMA_INVALID")

    preloaded = view.get("preloaded")
    if not isinstance(preloaded, Mapping):
        raise ContextBudgetError("CONTEXT_VIEW_PRELOADED_MUST_BE_OBJECT")

    deferred = view.get("deferred_or_omitted", [])
    if not isinstance(deferred, list):
        raise ContextBudgetError("CONTEXT_VIEW_DEFERRED_MUST_BE_LIST")

    serialized = view.get("serialized_size")
    if not isinstance(serialized, Mapping):
        raise ContextBudgetError("CONTEXT_VIEW_SERIALIZED_SIZE_REQUIRED")
    total = serialized.get("bytes")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ContextBudgetError("CONTEXT_VIEW_SERIALIZED_BYTES_INVALID")
    label = str(serialized.get("label") or LOCAL_SERIALIZATION_PROXY)
    return preloaded, deferred, total, label


def audit_context_budget(
    view: Mapping[str, Any],
    *,
    host: str | None = None,
    budget_bytes: int | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Return a metadata-only budget report for one already-built context view.

    budget_bytes is deliberately caller-supplied. P2P does not invent one
    universal context ceiling because host/model limits differ. The report never
    removes content; it only identifies optional preloaded items as review
    candidates when the explicit budget is exceeded.
    """

    if budget_bytes is not None:
        if isinstance(budget_bytes, bool) or not isinstance(budget_bytes, int) or budget_bytes <= 0:
            raise ContextBudgetError("BUDGET_BYTES_MUST_BE_POSITIVE_INTEGER")
    if isinstance(top_n, bool) or not isinstance(top_n, int) or not 1 <= top_n <= 50:
        raise ContextBudgetError("TOP_N_OUT_OF_RANGE")

    preloaded, deferred, total_bytes, measurement_label = _validate_view(view)

    must_load: list[dict[str, Any]] = []
    optional_preloaded: list[dict[str, Any]] = []

    for raw_category, raw_items in preloaded.items():
        category = str(raw_category)
        if not isinstance(raw_items, list):
            raise ContextBudgetError(f"PRELOADED_CATEGORY_MUST_BE_LIST:{category}")
        for index, raw_item in enumerate(raw_items):
            if not isinstance(raw_item, Mapping):
                raise ContextBudgetError(f"PRELOADED_ITEM_MUST_BE_OBJECT:{category}:{index}")
            required = _is_required(category, raw_item)
            record = {
                "category": category,
                "item_id": str(raw_item.get("item_id") or f"{category}:{index}"),
                "bytes": _canonical_size(raw_item),
                "classification": "MUST_LOAD" if required else "PRELOADED_OPTIONAL",
            }
            (must_load if required else optional_preloaded).append(record)

    on_demand: list[dict[str, Any]] = []
    for index, raw_ref in enumerate(deferred):
        if not isinstance(raw_ref, Mapping):
            raise ContextBudgetError(f"DEFERRED_ITEM_MUST_BE_OBJECT:{index}")
        on_demand.append(
            {
                "category": str(raw_ref.get("category") or "UNKNOWN"),
                "item_id": str(raw_ref.get("item_id") or f"deferred:{index}"),
                "pointer_id": str(raw_ref.get("pointer_id") or "UNKNOWN"),
                "reference_bytes": _canonical_size(raw_ref),
                "classification": "ON_DEMAND",
            }
        )

    required_bytes = sum(item["bytes"] for item in must_load)
    optional_bytes = sum(item["bytes"] for item in optional_preloaded)
    deferred_reference_bytes = sum(item["reference_bytes"] for item in on_demand)

    if budget_bytes is None:
        budget_status = "UNBOUNDED"
        headroom_bytes = None
    else:
        headroom_bytes = budget_bytes - total_bytes
        budget_status = "PASS" if headroom_bytes >= 0 else "OVER_BUDGET"

    ranked = sorted(
        [*optional_preloaded, *must_load],
        key=lambda item: (
            item["classification"] != "PRELOADED_OPTIONAL",
            -int(item["bytes"]),
            item["category"],
            item["item_id"],
        ),
    )[:top_n]

    if budget_status == "OVER_BUDGET" and optional_preloaded:
        recommendation = "REVIEW_PRELOADED_OPTIONAL_FIRST"
    elif budget_status == "OVER_BUDGET":
        recommendation = "REQUIRED_CONTEXT_EXCEEDS_BUDGET_DO_NOT_DROP_AUTHORITY"
    else:
        recommendation = "NO_CHANGE_REQUIRED"

    return {
        "schema": REPORT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "host": _normalise_host(host),
        "read_only": True,
        "measurement": {
            "label": measurement_label,
            "total_context_bytes": total_bytes,
            "required_item_bytes": required_bytes,
            "optional_preloaded_item_bytes": optional_bytes,
            "deferred_reference_bytes": deferred_reference_bytes,
            "budget_bytes": budget_bytes,
            "headroom_bytes": headroom_bytes,
            "budget_status": budget_status,
        },
        "classification": {
            "MUST_LOAD": {
                "count": len(must_load),
                "bytes": required_bytes,
                "items": sorted(must_load, key=lambda item: (item["category"], item["item_id"])),
            },
            "PRELOADED_OPTIONAL": {
                "count": len(optional_preloaded),
                "bytes": optional_bytes,
                "items": sorted(optional_preloaded, key=lambda item: (item["category"], item["item_id"])),
            },
            "ON_DEMAND": {
                "count": len(on_demand),
                "reference_bytes": deferred_reference_bytes,
                "items": sorted(on_demand, key=lambda item: (item["category"], item["item_id"])),
            },
            "DO_NOT_LOAD": {
                "count": 0,
                "items": [],
                "reason": "NOT_INFERRED_WITHOUT_EXPLICIT_POLICY",
            },
        },
        "top_bloat": ranked,
        "recommendation": recommendation,
        "safety": {
            "drops_context": False,
            "changes_routing": False,
            "changes_authority": False,
            "raw_item_content_in_report": False,
            "note": "Optional preloaded items are review candidates only; this report never removes them.",
        },
    }


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextBudgetError(f"CONTEXT_VIEW_READ_FAILED:{path}") from exc
    if not isinstance(payload, Mapping):
        raise ContextBudgetError("CONTEXT_VIEW_MUST_BE_OBJECT")
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("view", type=Path, help="JSON output from the existing P2P context-view builder")
    parser.add_argument("--host", default="UNKNOWN", help="metadata label only; no host behavior is inferred")
    parser.add_argument("--budget-bytes", type=int, default=None, help="explicit audit ceiling; omitted means UNBOUNDED")
    parser.add_argument("--top", type=int, default=5, help="number of largest preloaded items to report (1-50)")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = audit_context_budget(
            _read_json(args.view),
            host=args.host,
            budget_bytes=args.budget_bytes,
            top_n=args.top,
        )
    except ContextBudgetError as exc:
        print(f"p2p_context_budget: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
