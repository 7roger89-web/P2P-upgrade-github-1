"""Hermes Logistics read-only tools (HERMES_LOGISTICS_READONLY_001).

Three capability surfaces, all reading the authoritative Logistics MongoDB
through the find/find_one-only connector:

  logistics_today_work     — "Hôm nay tôi có việc gì?" (tasks collection,
                             explicit ASSIGNEE vs TEAM scope)
  logistics_freight_rate   — "Cước X về Y container Z?" (rate_cards;
                             deterministic structured lookup of the PR #12
                             rate-card schema: route.origin/destination plus
                             optional equipment_type/container_size/
                             transport_mode; returns the selling_price)
  logistics_shipment_status— "Lô hàng <ID> hiện thế nào?" (shipments by id)

FACT INTEGRITY: results carry provenance (source collection, record id,
queried_at, status). Values are never synthesized; absent data returns
NOT_FOUND, a missing requested month returns RATE_HISTORY_NOT_FOUND, and the
rate tool only returns prices actually stored on a uniquely matched rate
card — it never guesses a rate, a currency, a geographic alias, or a month.
Natural-language presentation stays with the model; this module only returns
normalized facts.

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
    "Look up a customer freight rate for a structured route in the Logistics "
    "rate_cards collection. Only rate cards flagged structured_lookup_ready=true "
    "(and not deleted) are considered. Matching is EXACT on route.origin and "
    "route.destination and, when supplied, on route.equipment_type, "
    "route.container_size (deterministic aliases only: 20/20FT/20' mean 20'; "
    "40HQ/40HC mean 40HC) and route.transport_mode. route_name is free text and "
    "is never parsed, and there are NO geographic aliases — pass exact place "
    "names (e.g. 'HP' does NOT match 'Hải Phòng'). When no month is supplied the "
    "latest valid MM/YYYY history entry is used (array order is not trusted); a "
    "requested month that has no entry returns RATE_HISTORY_NOT_FOUND. Multiple "
    "matching customer rate cards return AMBIGUOUS instead of a guessed pick. "
    "Statuses: OK, NOT_FOUND, AMBIGUOUS, RATE_HISTORY_NOT_FOUND. On OK, answer "
    "'Cước X về Y bao nhiêu?' with 'selling_price' (the customer quoted rate from "
    "history.total_price) and its explicit currency; 'internal_cost' "
    "(history.total_cost) is internal cost and must NEVER be presented as the "
    "customer freight rate. NEVER invent or estimate a rate, currency, route or "
    "month. The user may ask in Vietnamese, e.g. 'Cước Hải Phòng về Hà Nội "
    "container 20' bao nhiêu?'.",
    {
        "origin": {"type": "string", "description": "Exact route.origin, e.g. 'Hải Phòng' (no alias expansion)"},
        "destination": {"type": "string", "description": "Exact route.destination, e.g. 'Hà Nội' (no alias expansion)"},
        "container_size": {"type": "string", "description": "Optional route.container_size, e.g. \"20'\", '20FT', '40HC', '40HQ'"},
        "equipment_type": {"type": "string", "description": "Optional route.equipment_type, matched exactly"},
        "transport_mode": {"type": "string", "description": "Optional route.transport_mode, matched exactly"},
        "month": {"type": "string", "description": "Optional history month as MM/YYYY (e.g. '09/2026'); default is the latest valid month"},
        "date": {"type": "string", "description": "Optional YYYY-MM-DD date; its month/year is used when 'month' is omitted"},
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
_RATE_LOOKUP_LIMIT = 200  # bounded rate_cards scan for a structured lookup


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
# B. FREIGHT_RATE_LOOKUP (structured PR #12 rate-card schema; deterministic
#    matching only — no route_name parsing, no geographic aliases, no guessed
#    prices or months)
# --------------------------------------------------------------------------


def _strip_arg(args: dict, key: str) -> "str | None":
    raw = args.get(key)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _freight_rate(client: LogisticsReadOnlyClient, args: dict) -> dict:
    origin = _strip_arg(args, "origin")
    destination = _strip_arg(args, "destination")
    if not origin or not destination:
        raise _BadRequest("origin and destination are required")

    equipment_type = _strip_arg(args, "equipment_type")
    transport_mode = _strip_arg(args, "transport_mode")
    container_size_raw = _strip_arg(args, "container_size")
    date_raw = _strip_arg(args, "date")
    month_raw = _strip_arg(args, "month")

    # Resolve the requested history month: explicit MM/YYYY wins; otherwise a
    # YYYY-MM-DD date contributes its month/year; otherwise latest valid month.
    requested_month = None
    if month_raw:
        requested_month = contracts.parse_rate_month(month_raw)
        if requested_month is None:
            raise _BadRequest("month must be MM/YYYY (e.g. '09/2026')")
    if date_raw:
        try:
            target_date = contracts.parse_hcm_date(date_raw, field="date")
        except ValueError as exc:
            raise _BadRequest(str(exc))
        if requested_month is None:
            requested_month = (target_date.year, target_date.month)

    requested_container = (
        contracts.canonical_container_size(container_size_raw)
        if container_size_raw
        else None
    )

    requested = {
        "origin": origin,
        "destination": destination,
        "equipment_type": equipment_type,
        "container_size": container_size_raw,
        "container_size_normalized": requested_container,
        "transport_mode": transport_mode,
        "month": contracts.format_rate_month(*requested_month) if requested_month else None,
        "date": date_raw,
    }
    base = {
        "requested": requested,
        "source": contracts.RATE_CARDS,
        "queried_at": iso_now(),
    }

    # Mongo-side filter: readiness/delete gates plus the exact structured
    # fields (plain field matches and $ne only — connector-validated). The
    # container check is finalized in Python so the bounded alias table
    # applies to both the query value and the stored spelling.
    flt = dict(contracts.RATE_CARD_ACTIVE_FILTER)
    flt[contracts.RATE_CARD_ROUTE_ORIGIN] = origin
    flt[contracts.RATE_CARD_ROUTE_DESTINATION] = destination
    if equipment_type:
        flt[contracts.RATE_CARD_ROUTE_EQUIPMENT_TYPE] = equipment_type
    if transport_mode:
        flt[contracts.RATE_CARD_ROUTE_TRANSPORT_MODE] = transport_mode

    docs = client.find(contracts.RATE_CARDS, flt, limit=_RATE_LOOKUP_LIMIT)
    lookup_truncated = len(docs) >= _RATE_LOOKUP_LIMIT

    # Defensive in-Python re-verification (also applies container aliases and
    # whitespace stripping on the stored side). route_name is never consulted.
    candidates: List[dict] = []
    for doc in docs:
        if doc.get("is_deleted") is True:
            continue
        if doc.get(contracts.RATE_CARD_READY_FLAG) is not True:
            continue
        route = doc.get("route")
        if not isinstance(route, dict):
            continue
        if str(route.get("origin") or "").strip() != origin:
            continue
        if str(route.get("destination") or "").strip() != destination:
            continue
        if equipment_type and str(route.get("equipment_type") or "").strip() != equipment_type:
            continue
        if transport_mode and str(route.get("transport_mode") or "").strip() != transport_mode:
            continue
        if requested_container is not None:
            if contracts.canonical_container_size(route.get("container_size")) != requested_container:
                continue
        candidates.append(doc)

    if not candidates:
        return {
            **base,
            "status": contracts.FREIGHT_STATUS_NOT_FOUND,
            "lookup_truncated": lookup_truncated,
            "note": (
                f"Không tìm thấy rate card sẵn sàng tra cứu (structured_lookup_ready=true) "
                f"cho tuyến {origin} → {destination} khớp các tiêu chí đã nêu. Không suy "
                f"diễn tên địa danh (ví dụ 'HP' không tự thành 'Hải Phòng') và không đoán giá."
            ),
        }

    if len(candidates) > 1:
        # Multiple customer-specific rate cards match: never silently pick one.
        # Candidate facts are bounded (no prices — a quote must wait for
        # disambiguation).
        return {
            **base,
            "status": contracts.FREIGHT_STATUS_AMBIGUOUS,
            "match_count": len(candidates),
            "lookup_truncated": lookup_truncated,
            "candidates": [contracts.rate_card_view(doc) for doc in candidates],
            "note": (
                f"Có {len(candidates)} rate card khác nhau khớp tuyến "
                f"{origin} → {destination}; cần làm rõ khách hàng / loại thiết bị / "
                f"kích cỡ container / phương thức vận chuyển trước khi báo giá."
            ),
        }

    card = candidates[0]
    view = contracts.rate_card_view(card)
    selected = contracts.select_rate_history(card.get("history"), requested_month)
    if selected is None:
        return {
            **base,
            "status": contracts.FREIGHT_STATUS_HISTORY_NOT_FOUND,
            **view,
            "requested_month": contracts.format_rate_month(*requested_month) if requested_month else None,
            "available_months": contracts.valid_rate_months(card.get("history")),
            "note": (
                "Rate card không có dữ liệu giá cho tháng được yêu cầu (tháng phải có "
                "dạng MM/YYYY). Không bịa giá lịch sử."
            ),
        }

    # PRICE SEMANTICS: history.total_price is the customer quoted rate and is
    # exposed as selling_price (the answer to "Cước X về Y bao nhiêu?");
    # history.total_cost stays internal_cost and is never presented as the
    # customer freight rate; history.profit stays profit. Currency is the
    # explicit rate-card currency, never assumed.
    return {
        **base,
        "status": contracts.FREIGHT_STATUS_OK,
        **view,
        "month": str(selected.get("month")),
        "selling_price": selected.get("total_price"),
        "internal_cost": selected.get("total_cost"),
        "profit": selected.get("profit"),
        "history_updated_at": (
            str(selected.get("updated_at")) if selected.get("updated_at") is not None else None
        ),
        "price_meaning": {
            "selling_price": "history.total_price — giá bán / giá cước báo khách (customer quoted rate)",
            "internal_cost": "history.total_cost — chi phí nội bộ; KHÔNG PHẢI giá cước báo khách",
            "profit": "history.profit",
        },
        "note": (
            f"Giá cước báo khách là selling_price "
            f"({selected.get('total_price')!r} {view.get('currency') or ''}). "
            f"internal_cost là chi phí nội bộ, không phải giá cước trả lời khách."
        ),
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
