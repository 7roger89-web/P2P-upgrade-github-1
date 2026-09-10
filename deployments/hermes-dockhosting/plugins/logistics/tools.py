"""Hermes Logistics read-only tools (HERMES_LOGISTICS_READONLY_001).

Three capability surfaces, all reading the authoritative Logistics MongoDB
through the find/find_one-only connector:

  logistics_today_work     — "Hôm nay tôi có việc gì?" (tasks collection,
                             explicit ASSIGNEE vs TEAM scope)
  logistics_freight_rate   — "Cước X về Y container Z?" (rate_cards;
                             structured route lookup on
                             route.origin/route.destination plus the optional
                             equipment/container/mode fields; route_name is
                             never parsed)
  logistics_shipment_status— "Lô hàng <ID> hiện thế nào?" (shipments by id)

FACT INTEGRITY: results carry provenance (source collection, record id,
queried_at, status). Values are never synthesized; absent data returns
NOT_FOUND, an absent history month returns RATE_HISTORY_NOT_FOUND, and several
customer-specific matches return AMBIGUOUS instead of one being silently
chosen. Freight answers expose ``selling_price`` (total_price, the customer
quoted rate); ``total_cost`` stays ``internal_cost`` and is never returned as
the customer freight rate. Natural-language presentation stays with the model;
this module only returns normalized facts.

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
    "short action, assignee and deadline, plus provenance. Scope is explicit in the "
    "result: ASSIGNEE when assignee/assignee_user_id was supplied, otherwise TEAM. "
    "NEVER present TEAM-scope results as the user's own personal tasks — when no "
    "identity is bound, say the list is team-wide or ask for the user's assignee "
    "identity. Report status and values exactly as returned; never invent tasks, "
    "deadlines or statuses. The user may ask in Vietnamese, e.g. 'Hôm nay tôi có "
    "việc gì?'.",
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
    "Look up the freight rate from an origin to a destination from the Logistics "
    "rate_cards collection, using the STRUCTURED route fields (route.origin / "
    "route.destination, plus equipment_type / container_size / transport_mode when "
    "supplied) on rate cards marked structured_lookup_ready. Status is one of OK, "
    "NOT_FOUND, AMBIGUOUS, RATE_HISTORY_NOT_FOUND. selling_price (total_price) is the "
    "customer quoted rate — that is the answer to 'Cước X về Y bao nhiêu?'. "
    "internal_cost (total_cost) and profit are internal and must NEVER be presented "
    "as the customer freight rate. month uses MM/YYYY: when omitted the LATEST valid "
    "month is used, and a month with no history entry returns RATE_HISTORY_NOT_FOUND. "
    "Multiple customer-specific rate cards return AMBIGUOUS with bounded candidates — "
    "never pick one silently. NEVER invent, estimate or round a rate, currency, route "
    "or month, never parse route_name, and never expand a geographic abbreviation "
    "(\"HP\" is not \"Hải Phòng\"). The user may ask in Vietnamese, e.g. 'Cước Hải "
    "Phòng về Hà Nội container 20' bao nhiêu?'.",
    {
        "origin": {"type": "string", "description": "Structured route origin, e.g. 'Hải Phòng'"},
        "destination": {"type": "string", "description": "Structured route destination, e.g. 'Hà Nội'"},
        "container_size": {
            "type": "string",
            "description": "Container size; deterministic aliases accepted (20 / 20FT / 20' -> 20', 40HQ / 40HC -> 40HC)",
        },
        "equipment_type": {"type": "string", "description": "Structured route equipment type, e.g. 'container'"},
        "transport_mode": {"type": "string", "description": "Structured route transport mode, e.g. 'road', 'sea'"},
        "vehicle_type": {"type": "string", "description": "Deprecated alias of equipment_type, e.g. 'xe tải', 'container'"},
        "customer": {"type": "string", "description": "Optional customer name, used to disambiguate multiple rate cards"},
        "month": {"type": "string", "description": "Requested month as MM/YYYY (default: latest valid month in history)"},
        "date": {"type": "string", "description": "Optional date as YYYY-MM-DD; its MM/YYYY month is used when 'month' is omitted"},
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

    # Explicit personal vs team scope (no identity service in this task: the
    # caller must supply the Logistics assignee identity, if known).
    if assignee and assignee_user_id:
        scope_value = f"{assignee} ({assignee_user_id})"
    elif assignee_user_id:
        scope_value = assignee_user_id
    elif assignee:
        scope_value = assignee
    else:
        scope_value = None
    scope = "ASSIGNEE" if scope_value else "TEAM"

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

    notes: List[str] = []
    if scope == "TEAM":
        notes.append(contracts.TODAY_WORK_TEAM_SCOPE_NOTE)
    if not items:
        notes.append(
            f"Không có việc nào cho ngày {target.isoformat()} trong dữ liệu Logistics hiện tại."
        )
        if not include_undated and undated:
            notes.append(
                f"(Có {len(undated)} việc chưa xử lý chưa rõ hạn — dùng include_undated=true để xem.)"
            )

    result: Dict[str, Any] = {
        "date": target.isoformat(),
        "timezone": "Asia/Ho_Chi_Minh (UTC+07:00)",
        "scope": scope,
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
    if scope == "ASSIGNEE":
        result["scope_value"] = scope_value
    if items:
        result["status"] = "OK"
        result["items"] = items
    else:
        result["status"] = "NOT_FOUND"
        result["items"] = []
    if notes:
        result["note"] = " ".join(notes)
    return result


# --------------------------------------------------------------------------
# B. FREIGHT_RATE_LOOKUP (structured route lookup; route_name is never parsed)
# --------------------------------------------------------------------------


def _opt_str(value):
    text = "" if value is None else str(value).strip()
    return text or None


def _freight_rate(client: LogisticsReadOnlyClient, args: dict) -> dict:
    origin = str(args.get("origin") or "").strip()
    destination = str(args.get("destination") or "").strip()
    if not origin or not destination:
        raise _BadRequest("origin and destination are required")
    container_size = _opt_str(args.get("container_size"))
    equipment_type = _opt_str(args.get("equipment_type")) or _opt_str(args.get("vehicle_type"))
    transport_mode = _opt_str(args.get("transport_mode"))
    customer = _opt_str(args.get("customer"))

    # month (MM/YYYY) wins; a YYYY-MM-DD date falls back to its own month.
    month = _opt_str(args.get("month"))
    date_arg = _opt_str(args.get("date"))
    if date_arg:
        try:
            contracts.parse_hcm_date(date_arg, field="date")
        except ValueError as exc:
            raise _BadRequest(str(exc))
    if month is None and date_arg is not None:
        month = contracts.month_from_date(date_arg)
    if month is not None and contracts.parse_month(month) is None:
        raise _BadRequest("month must be MM/YYYY")
    month = contracts.canonical_month(month) if month is not None else None

    requested = {
        "origin": origin,
        "destination": destination,
        "container_size": container_size,
        "equipment_type": equipment_type,
        "transport_mode": transport_mode,
        "customer": customer,
        "month": month,
        "date": date_arg,
    }
    base = {
        "requested": requested,
        "source": contracts.RATE_CARDS,
        "queried_at": iso_now(),
    }

    # Bounded read-only query over structured, non-deleted rate cards only.
    # Legacy free-text rate cards (no structured_lookup_ready) never come back.
    docs = client.find(
        contracts.RATE_CARDS,
        dict(contracts.RATE_CARD_ACTIVE_FILTER),
        limit=contracts.RATE_CARD_SCAN_LIMIT,
    )
    matches = [
        doc
        for doc in docs
        if contracts.match_rate_card(
            doc,
            origin=origin,
            destination=destination,
            container_size=container_size,
            equipment_type=equipment_type,
            transport_mode=transport_mode,
            customer=customer,
        )
    ]

    if not matches:
        return {
            **base,
            "status": contracts.RATE_CARD_STATUS_NOT_FOUND,
            "note": (
                "Không có rate card nào trong dữ liệu Logistics khớp tuyến / thiết bị "
                "này (chỉ xét rate card có cấu trúc và chưa xóa). Không đoán giá."
            ),
        }

    if len(matches) > 1:
        # Multiple customer-specific rate cards: bounded candidates only, never
        # one silently chosen.
        candidates = []
        for doc in matches:
            entry, entry_month = contracts.select_latest_history(doc)
            candidates.append(contracts.rate_card_candidate(doc, entry, entry_month))
        return {
            **base,
            "status": contracts.RATE_CARD_STATUS_AMBIGUOUS,
            "match_count": len(matches),
            "candidates": candidates,
            "note": (
                f"Có {len(matches)} rate card khớp cùng tuyến/thiết bị; cần làm rõ "
                "(khách hàng, thiết bị, tháng) trước khi trả mức cước."
            ),
        }

    doc = matches[0]
    if month is not None:
        entry, entry_month = contracts.select_history_for_month(doc, month)
    else:
        entry, entry_month = contracts.select_latest_history(doc)

    if entry is None or entry_month is None:
        missing_history = {
            **base,
            "status": contracts.RATE_CARD_STATUS_HISTORY_NOT_FOUND,
            "rate_card_id": _norm(doc.get("id")),
            "customer": _norm(doc.get("customer")),
            "route": _route_view(doc),
            "currency": _norm(doc.get("currency")),
            "requested_month": month,  # None means "latest valid month"
            "available_months": contracts.available_months(doc),
        }
        if month is None:
            missing_history["note"] = (
                "Rate card khớp tuyến nhưng không có tháng MM/YYYY hợp lệ trong "
                "lịch sử giá. Không đoán giá."
            )
        else:
            missing_history["note"] = (
                f"Rate card khớp tuyến nhưng không có giá cho tháng {month}. "
                "Không đoán giá."
            )
        return missing_history

    result = {
        **base,
        "status": contracts.RATE_CARD_STATUS_OK,
        "rate_card_id": _norm(doc.get("id")),
        "customer": _norm(doc.get("customer")),
        "route": _route_view(doc),
        "month": entry_month,
        "currency": _norm(doc.get("currency")),
        # total_price = the customer quoted rate (the answer to "Cước ... bao nhiêu?").
        "selling_price": entry.get("total_price"),
        # total_cost = internal_cost; profit = profit. Internal figures only.
        "internal": {
            "internal_cost": entry.get("total_cost"),
            "profit": entry.get("profit"),
        },
        "updated_at": _norm(entry.get("updated_at")),
        "price_semantics": dict(contracts.PRICE_SEMANTICS),
        "available_months": contracts.available_months(doc),
    }
    if month is None:
        result["month_selection"] = "latest_valid_month"
    else:
        result["month_selection"] = "requested_month"
    result["note"] = (
        "selling_price là giá bán / cước báo khách (total_price). internal_cost "
        "(total_cost) và profit là dữ liệu nội bộ, KHÔNG được trình bày như cước "
        "báo khách."
    )
    return result


def _norm(value):
    return None if value is None else str(value)


def _route_view(doc: dict) -> dict:
    """Bounded structured route view (route_name is intentionally absent)."""
    route = contracts.rate_card_route(doc)
    return {
        "origin": _norm(route.get("origin")),
        "destination": _norm(route.get("destination")),
        "equipment_type": _norm(route.get("equipment_type")),
        "container_size": _norm(route.get("container_size")),
        "transport_mode": _norm(route.get("transport_mode")),
    }


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
