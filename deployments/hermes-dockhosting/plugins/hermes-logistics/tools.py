"""Hermes tool handlers for the read-only Logistics connector.

Each handler:
  * receives the LLM-supplied ``params`` dict,
  * resolves the read-only Logistics connection from environment variables,
  * runs a real, read-only MongoDB query via :mod:`connector`,
  * returns a JSON string (Hermes tool contract).

If the required environment variables are absent, the handlers return a
``NOT_CONFIGURED`` JSON result naming exactly which variables are needed —
this is the honest Owner Gate for live verification, never a synthesized fact.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone

# Ensure sibling modules are importable whether Hermes loads this dir as a
# package or by file path (the directory name contains a hyphen).
_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

import connector  # noqa: E402

_URI_ENV = "LOGISTICS_MONGO_URI_READONLY"
_DB_ENV = "LOGISTICS_MONGO_DB_NAME"
_SCHEMA_ENV = "LOGISTICS_SCHEMA_PATH"

_connector_cache = None


def _schema_path() -> str:
    override = os.environ.get(_SCHEMA_ENV)
    if override:
        return override
    return os.path.join(_PLUGIN_DIR, "schema.yaml")


def _connector():
    """Return a cached read-only connector, or ``None`` when not configured."""
    global _connector_cache
    if _connector_cache is not None:
        return _connector_cache

    uri = os.environ.get(_URI_ENV)
    db_name = os.environ.get(_DB_ENV)
    if not uri or not db_name:
        return None

    db = connector.make_read_only_connection(uri, db_name)
    schema = connector.load_schema(_schema_path())
    _connector_cache = connector.LogisticsConnector(db, schema)
    return _connector_cache


def _not_configured(message=None) -> str:
    return json.dumps(
        {
            "status": "NOT_CONFIGURED",
            "source": "logistics_config",
            "queried_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "message": message
            or (
                "Hermes chưa được cấu hình đọc dữ liệu Logistics. Cần cung cấp biến "
                f"môi trường read-only: {_URI_ENV} và {_DB_ENV}."
            ),
            "required_env_vars": [_URI_ENV, _DB_ENV],
        },
        ensure_ascii=False,
    )


def _error(message) -> str:
    return json.dumps(
        {
            "status": "ERROR",
            "source": "logistics_connector",
            "error": message,
        },
        ensure_ascii=False,
    )


def _parse_date(value):
    # Default target day is today in Asia/Ho_Chi_Minh (the business timezone),
    # not the host's local date.
    if value in (None, ""):
        return datetime.now(connector.LOGISTICS_TZ).date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except (ValueError, TypeError):
        # Fall back to date-only parsing.
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            return None


def handle_today_work(params, **kwargs):
    del kwargs
    conn = _connector()
    if conn is None:
        return _not_configured()
    target = _parse_date(params.get("date"))
    if target is None:
        return _error("date phải ở định dạng ISO YYYY-MM-DD.")
    try:
        result = conn.today_work(target)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as exc:  # noqa: BLE001 - surface as a tool result
        return _error(f"today_work failed: {exc}")


def handle_freight_rate_lookup(params, **kwargs):
    del kwargs
    conn = _connector()
    if conn is None:
        return _not_configured()
    origin = params.get("origin")
    destination = params.get("destination")
    container = params.get("container")
    if not (origin and destination and container):
        return _error("origin, destination và container là bắt buộc.")
    try:
        result = conn.freight_rate_lookup(
            origin, destination, container, date=params.get("date")
        )
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as exc:  # noqa: BLE001
        return _error(f"freight_rate_lookup failed: {exc}")


def handle_shipment_status(params, **kwargs):
    del kwargs
    conn = _connector()
    if conn is None:
        return _not_configured()
    shipment_id = params.get("shipment_id")
    if not shipment_id:
        return _error("shipment_id là bắt buộc.")
    try:
        result = conn.shipment_status(shipment_id)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as exc:  # noqa: BLE001
        return _error(f"shipment_status failed: {exc}")


HANDLERS = {
    "logistics_today_work": handle_today_work,
    "logistics_freight_rate_lookup": handle_freight_rate_lookup,
    "logistics_shipment_status": handle_shipment_status,
}
