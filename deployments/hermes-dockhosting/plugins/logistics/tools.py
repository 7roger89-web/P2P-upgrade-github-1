"""Hermes Logistics read-only tools (HERMES_LOGISTICS_READONLY_001).

Three capability surfaces, all reading the authoritative Logistics MongoDB
through the find/find_one-only connector:

  logistics_today_work     — "Hôm nay tôi có việc gì?" (tasks collection)
  logistics_freight_rate   — "Cước X về Y container Z?" (rate_cards; fails
                             closed with SCHEMA_GAP_RATE_CARD_FIELDS until
                             the rate-card field mapping is verified)
  logistics_shipment_status— "Lô hàng <ID> hiện thế nào?" (shipments by id)

FACT INTEGRITY: results carry provenance (source collection, record id,
queried_at, status). Values are never synthesized; absent data returns
NOT_FOUND and the rate tool reports its schema gap instead of a plausible
rate. Natural-language presentation stays with the model; this module only
returns normalized facts.

Module imports are stdlib-only so plugin registration is safe in any Hermes
runtime (pymongo is imported lazily by the connector).
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any, Callable, Dict, List, Optional

from . import contracts, connector as _connector_module
from .connector import (
    LogisticsConfigError,
    LogisticsDependencyError,
    LogisticsReadOnlyClient,
    LogisticsReadOnlyError,
    connect_from_env,
    iso_now,
    sanitize_error_text,
)

TOOLSET = "logistics"

# --------------------------------------------------------------------------
# Result helpers (same envelope semantics as tools.registry.tool_result /
# tool_error, kept local so the plugin has no import-time Hermes dependency)
# --------------------------------------------------------------------------


def _json_default(value):
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.isoformat()
    return str(value)


def tool_result(data) -> str:
    return json.dumps(data, ensure_ascii=False, default=_json_default)


def tool_error(message: str, **extra) -> str:
    return json.dumps({"error": message, **extra}, ensure_ascii=False, default=_json_default)


# --------------------------------------------------------------------------
# Availability gate (cheap env check; no pymongo import, never raises)
# --------------------------------------------------------------------------


def _check_logistics_configured() -> bool:
    import os

    return bool(
        os.environ.get(contracts.MONGO_URI_ENV, "").strip()
        and os.environ.get(contracts.MONGO_DB_NAME_ENV, "").strip()
    )


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

_STR = {"type": "string"}
_BOOL = {"type": "boolean"}
_INT = {"type": "integer"}


def _schema(name: str, description: str, properties: dict, required: tuple = ()) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": list(required),
        },
    }


TODAY_WORK_SCHEMA = _schema(
    "logistics_today_work",
    "List actionable Logistics work for one day (default: today, Asia/Ho_Chi_Minh) "
    "from the Logistics tasks collection. Returns bounded items with reference id, "
    "short action, assignee and deadline, plus provenance. Report status and values "
    "exactly as returned; never invent tasks, deadlines or statuses. The user may "
    "ask in Vietnamese, e.g. 'Hôm nay tôi có việc gì?'.",
    {
        "date": {"type": "string", "description": "Target day as YYYY-MM-DD (default: today in Asia/Ho_Chi_Minh)"},
        "include_undated": {"type": "boolean", "description": "Also include open tasks with no parseable deadline (default false; they are counted either way)"},
        "assignee": _STR,
        "assignee_user_id": _STR,
        "limit": {"type": "integer", "description": "Max items to return (default 25)"},
    },
)

FREIGHT_RATE_SCHEMA = _schema(
    "logistics_freight_rate",
    "Look up the current/recent freight rate from an origin to a destination for a "
    "container size or vehicle type, from the Logistics rate_cards collection. "
    "Only verified field mappings are used; if the rate-card schema cannot be "
    "established this returns SCHEMA_GAP_RATE_CARD_FIELDS, and if no rate exists it "
    "returns NOT_FOUND. NEVER invent or estimate a rate, currency or route; report "
    "the returned status as-is. The user may ask in Vietnamese, e.g. 'Cước Hải "
    "Phòng về Hà Nội container 20' bao nhiêu?'.",
    {
        "origin": _STR,
        "destination": _STR,
        "container_size": {"type": "string", "description": "e.g. \"20'\", '40HC'"},
        "vehicle_type": {"type": "string", "description": "e.g. 'xe tải', 'container'"},
        "date": {"type": "string", "description": "Optional date as YYYY-MM-DD"},
    },
    required=("origin", "destination"),
)

SHIPMENT_STATUS_SCHEMA = _schema(
    "logistics_shipment_status",
    "Get the current status of one Logistics shipment by its business id "
    "(shipments.id). Returns status, customer, key operational flags and "
    "updated_at with provenance; financial details are not exposed. Report the "
    "returned status exactly; never invent a status or date. The user may ask in "
    "Vietnamese, e.g. 'Lô hàng LK-1024 hiện thế nào?'.",
    {
        "shipment_id": _STR,
        "include_archived": {"type": "boolean", "description": "Also consider archived (is_archived) records (default false)"},
    },
    required=("shipment_id",),
)

# --------------------------------------------------------------------------
# Handler internals
# --------------------------------------------------------------------------

_DEFAULT_ITEM_LIMIT = 25
_SCAN_LIMIT = 500  # bounded scan of open tasks (newest first)
_RATE_SAMPLE_LIMIT = 5  # bounded rate_cards sample for schema-gap reporting


def _with_connector(fn: Callable[[LogisticsReadOnlyClient, dict], dict]) -> Callable[[dict], str]:
    """Wrap a handler body: config/dependency/connector errors -> JSON envelope."""

    def handler(args: Optional[dict], **kw) -> str:
        args = args or {}

        def _uri_from_env() -> str:
            import os

            return os.environ.get(contracts.MONGO_URI_ENV, "") or ""

        try:
            client = connect_from_env()
        except LogisticsConfigError as exc:
            return tool_error(
                str(exc),
                error_type="logistics_config_missing",
                required_env=list(contracts.REQUIRED_ENV_VARS),
                note=(
                    "Cần cấu hình biến môi trường với credential MongoDB CHỈ CÓ QUYỀN READ "
                    "trên database Logistics."
                ),
            )
        except LogisticsDependencyError as exc:
            return tool_error(str(exc), error_type="logistics_dependency_missing")
        except Exception as exc:  # driver/construction failure: sanitize, never leak the URI
            return tool_error(
                "Logistics connection failed: "
                f"{type(exc).__name__}: {sanitize_error_text(str(exc), _uri_from_env())}",
                error_type="logistics_connector_error",
            )
        try:
            return tool_result(fn(client, args))
        except _BadRequest as exc:
            return tool_error(str(exc), error_type="logistics_bad_request")
        except LogisticsReadOnlyError as exc:
            return tool_error(str(exc), error_type="logistics_readonly_violation")
        except Exception as exc:  # connector/driver failure: sanitize, never leak the URI
            return tool_error(
                "Logistics query failed: "
                f"{type(exc).__name__}: {sanitize_error_text(str(exc), _uri_from_env())}",
                error_type="logistics_connector_error",
            )
        finally:
            try:
                client.close()
            except Exception:
                pass

    return handler


class _BadRequest(Exception):
    pass


def _bounded_int(args: dict, key: str, default: int, maximum: int) -> int:
    raw = args.get(key)
    if raw is None:
        return default
    try:
        return max(1, min(int(raw), maximum))
    except (TypeError, ValueError):
        raise _BadRequest(f"{key} must be an integer")


# --------------------------------------------------------------------------
# A. TODAY_WORK
# --------------------------------------------------------------------------


def _today_work(client: LogisticsReadOnlyClient, args: dict) -> dict:
    try:
        target = contracts.parse_hcm_date(args.get("date") or None, field="date")
    except ValueError as exc:
        raise _BadRequest(str(exc))
    include_undated = bool(args.get("include_undated", False))
    limit = _bounded_int(args, "limit", _DEFAULT_ITEM_LIMIT, _DEFAULT_ITEM_LIMIT)
    assignee = (args.get("assignee") or "").strip() or None
    assignee_user_id = (args.get("assignee_user_id") or "").strip() or None

    docs = client.find(
        contracts.TASKS,
        dict(contracts.TASK_OPEN_FILTER),
        sort=list(contracts.TASK_SORT),
        limit=_SCAN_LIMIT,
    )
    scan_truncated = len(docs) >= _SCAN_LIMIT

    dated: List[dict] = []
    undated: List[dict] = []
    for doc in docs:
        item = contracts.task_item(doc)
        if assignee and (item.get("assignee") or "") != assignee:
            continue
        if assignee_user_id and (item.get("assignee_user_id") or "") != assignee_user_id:
            continue
        due = contracts.parse_deadline(doc.get("deadline"))
        if due is None:
            undated.append(item)
        elif due == target:
            item["due"] = due.isoformat()
            dated.append(item)

    items = dated[:limit]
    if include_undated:
        remaining = limit - len(items)
        items = items + undated[: max(0, remaining)]

    result: Dict[str, Any] = {
        "date": target.isoformat(),
        "timezone": "Asia/Ho_Chi_Minh (UTC+07:00)",
        "source": contracts.TASKS,
        "queried_at": iso_now(),
        "counts": {
            "returned": len(items),
            "matched_date": len(dated),
            "open_undated": len(undated),
            "open_scan_limit": _SCAN_LIMIT,
            "scan_truncated": scan_truncated,
        },
    }
    if items:
        result["status"] = "OK"
        result["items"] = items
    else:
        result["status"] = "NOT_FOUND"
        result["items"] = []
        result["note"] = (
            f"Không có việc nào cho ngày {target.isoformat()} trong dữ liệu Logistics hiện tại."
        )
        if not include_undated and undated:
            result["note"] += f" (Có {len(undated)} việc chưa xử lý chưa rõ hạn — dùng include_undated=true để xem.)"
    return result


# --------------------------------------------------------------------------
# B. FREIGHT_RATE_LOOKUP (fail closed pending verified rate-card fields)
# --------------------------------------------------------------------------


def _freight_rate(client: LogisticsReadOnlyClient, args: dict) -> dict:
    origin = (str(args.get("origin") or "").strip())
    destination = (str(args.get("destination") or "").strip())
    if not origin or not destination:
        raise _BadRequest("origin and destination are required")
    if args.get("date"):
        try:
            contracts.parse_hcm_date(args.get("date"), field="date")
        except ValueError as exc:
            raise _BadRequest(str(exc))

    requested = {
        "origin": origin,
        "destination": destination,
        "container_size": args.get("container_size") or None,
        "vehicle_type": args.get("vehicle_type") or None,
        "date": args.get("date") or None,
    }
    base = {
        "requested": requested,
        "source": contracts.RATE_CARDS,
        "queried_at": iso_now(),
    }

    if contracts.RATE_CARD_FIELD_MAP is None:
        # Read a bounded sample of active rate cards so the schema gap report is
        # evidence-backed (observed keys) rather than a guess. A real read-only
        # query is executed; no rate value is ever returned in this state.
        sample = client.find(
            contracts.RATE_CARDS,
            dict(contracts.RATE_CARD_ACTIVE_FILTER),
            sort=[("updated_at", -1)],
            limit=_RATE_SAMPLE_LIMIT,
        )
        if not sample:
            return {
                **base,
                "status": "NOT_FOUND",
                "note": "Chưa có rate card nào trong dữ liệu Logistics hiện tại.",
            }
        observed: List[str] = []
        for doc in sample:
            for key in doc.keys():
                if key != "_id" and key not in observed:
                    observed.append(key)
        return {
            **base,
            "status": "SCHEMA_GAP_RATE_CARD_FIELDS",
            "missing_fields": list(contracts.RATE_CARD_MISSING_FIELDS),
            "observed_top_level_keys": observed,
            "sample_size": len(sample),
            "note": (
                "Chưa xác minh được trường dữ liệu cước (tuyến, container/xe, giá, "
                "tiền tệ, ngày hiệu lực) trong rate_cards nên chưa thể trả mức cước. "
                "Không đoán giá. Cần xác minh mapping trường từ mã nguồn "
                "logistics-work-desk."
            ),
        }

    # A verified field map is required before any rate can be returned. This
    # branch intentionally does not exist yet: activating it without a
    # source-verified mapping would violate the fact-integrity rule.
    raise LogisticsReadOnlyError(
        "Verified rate-card field map is set but no matching implementation exists; "
        "refusing to return unverified rates."
    )


# --------------------------------------------------------------------------
# C. SHIPMENT_STATUS
# --------------------------------------------------------------------------


def _shipment_status(client: LogisticsReadOnlyClient, args: dict) -> dict:
    shipment_id = str(args.get("shipment_id") or "").strip()
    if not shipment_id:
        raise _BadRequest("shipment_id is required")
    include_archived = bool(args.get("include_archived", False))

    flt = {contracts.SHIPMENT_ID_FIELD: shipment_id}
    flt.update(contracts.shipment_active_filter(include_archived=include_archived))
    matches = client.find(contracts.SHIPMENTS, flt, limit=3)

    base = {
        "query": {"id": shipment_id, "include_archived": include_archived},
        "source": contracts.SHIPMENTS,
        "queried_at": iso_now(),
    }
    if not matches:
        return {
            **base,
            "status": "NOT_FOUND",
            "note": f"Không tìm thấy lô hàng {shipment_id!r} trong dữ liệu Logistics hiện tại.",
        }
    if len(matches) > 1:
        return {
            **base,
            "status": "AMBIGUOUS",
            "matched": [
                {
                    "id": str(m.get("id")),
                    "version": m.get("version"),
                    "updated_at": str(m.get("updated_at")) if m.get("updated_at") is not None else None,
                }
                for m in matches
            ],
            "note": f"Nhiều bản ghi hoạt động cùng id {shipment_id!r}; cần làm rõ trước khi trả lời.",
        }
    doc = matches[0]
    summary = contracts.shipment_summary(doc)
    return {
        **base,
        "status": "OK",
        "shipment": summary,
        "record_id": summary.get("id"),
    }


# --------------------------------------------------------------------------
# Registration table (consumed by __init__.register)
# --------------------------------------------------------------------------

handle_today_work = _with_connector(_today_work)
handle_freight_rate = _with_connector(_freight_rate)
handle_shipment_status = _with_connector(_shipment_status)

TOOL_REGISTRATIONS = (
    {
        "name": "logistics_today_work",
        "toolset": TOOLSET,
        "schema": TODAY_WORK_SCHEMA,
        "handler": handle_today_work,
        "check_fn": _check_logistics_configured,
        "requires_env": list(contracts.REQUIRED_ENV_VARS),
        "emoji": "📋",
    },
    {
        "name": "logistics_freight_rate",
        "toolset": TOOLSET,
        "schema": FREIGHT_RATE_SCHEMA,
        "handler": handle_freight_rate,
        "check_fn": _check_logistics_configured,
        "requires_env": list(contracts.REQUIRED_ENV_VARS),
        "emoji": "💰",
    },
    {
        "name": "logistics_shipment_status",
        "toolset": TOOLSET,
        "schema": SHIPMENT_STATUS_SCHEMA,
        "handler": handle_shipment_status,
        "check_fn": _check_logistics_configured,
        "requires_env": list(contracts.REQUIRED_ENV_VARS),
        "emoji": "📦",
    },
)
