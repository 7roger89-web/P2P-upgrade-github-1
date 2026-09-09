"""Observed logistics-work-desk data contracts for the Hermes read-only plugin.

Schema provenance (LOGISTICS_SCHEMA_OBSERVED):
    Observed contracts from 7roger89-web/logistics-work-desk main, supplied by
    the Owner on 2026-09-09 and extracted from the actual repository source
    (core/database.py normalization, add_task()/load_tasks() loaders,
    load_rate_cards() repository). These constants are NOT guesses from
    collection names; where a field mapping could not be proven from source
    (rate_cards business fields) the plugin fails closed instead.

This module is pure Python (stdlib only): no pymongo import, no I/O, so it is
unit-testable anywhere and safe to import at plugin-registration time.
"""

from __future__ import annotations

import datetime as _dt
import re

# --------------------------------------------------------------------------
# Configuration (no secrets ever live in this repository)
# --------------------------------------------------------------------------

MONGO_URI_ENV = "LOGISTICS_MONGO_URI_READONLY"
MONGO_DB_NAME_ENV = "LOGISTICS_MONGO_DB_NAME"
REQUIRED_ENV_VARS = (MONGO_URI_ENV, MONGO_DB_NAME_ENV)

# --------------------------------------------------------------------------
# Collections (read allowlist — the connector refuses anything else)
# --------------------------------------------------------------------------

SHIPMENTS = "shipments"
TASKS = "tasks"
RATE_CARDS = "rate_cards"

ALLOWED_COLLECTIONS = (SHIPMENTS, TASKS, RATE_CARDS)

# --------------------------------------------------------------------------
# tasks (observed from add_task() / load_tasks())
# --------------------------------------------------------------------------

# load_tasks() canonical filter: db.tasks.find({"is_deleted": {"$ne": True}})
#   .sort("created_at", -1)
# "Today's work" additionally excludes completed tasks (done != true).
TASK_OPEN_FILTER = {"is_deleted": {"$ne": True}, "done": {"$ne": True}}
TASK_SORT = [("created_at", -1)]

# --------------------------------------------------------------------------
# shipments (observed from core/database.py normalization)
# --------------------------------------------------------------------------

# Primary stable business ID for lookups: shipments.id
SHIPMENT_ID_FIELD = "id"

# Soft-delete / archive conventions:
#   - always exclude is_deleted == true
#   - exclude is_archived == true unless the caller explicitly asks
def shipment_active_filter(include_archived: bool = False) -> dict:
    flt = {"is_deleted": {"$ne": True}}
    if not include_archived:
        flt["is_archived"] = {"$ne": True}
    return flt


# --------------------------------------------------------------------------
# rate_cards — FIELD MAPPING UNRESOLVED (fail closed)
# --------------------------------------------------------------------------
# Observed facts only: documents have a stable "id", soft-delete convention
# is_deleted != true, unique id index, load_rate_cards() repository.
#
# The route / container / rate / currency / effective-date field names could
# NOT be proven from the logistics-work-desk source. Per the fact-integrity
# rule the freight-rate tool therefore NEVER returns a rate: it reports
# SCHEMA_GAP_RATE_CARD_FIELDS with the exact missing fields instead. Once the
# mapping is verified against the real rate-card model/UI source, set
# RATE_CARD_FIELD_MAP below to the verified field names (this is the single,
# clearly-marked extension point; no matching logic is shipped unverified).
RATE_CARD_ACTIVE_FILTER = {"is_deleted": {"$ne": True}}

RATE_CARD_FIELD_MAP = None  # e.g. {"origin": ..., "destination": ..., "equipment": ..., "rate": ..., "currency": ..., "effective_date": ...}

RATE_CARD_MISSING_FIELDS = (
    "origin_field: field holding the route origin (e.g. Hai Phong)",
    "destination_field: field holding the route destination (e.g. Hanoi)",
    "equipment_field: field holding container size or vehicle type",
    "rate_amount_field: field holding the numeric freight rate",
    "currency_field: field holding the rate currency",
    "effective_date_field: effective/updated date used to pick the most recent applicable rate",
)

# --------------------------------------------------------------------------
# Timezone
# --------------------------------------------------------------------------
# Asia/Ho_Chi_Minh is UTC+07:00 year-round (no DST since 1975), so a fixed
# offset reproduces the zone exactly without a tzdata dependency.
HCM_UTC_OFFSET = _dt.timedelta(hours=7)
HCM_TZ = _dt.timezone(HCM_UTC_OFFSET, name="Asia/Ho_Chi_Minh")


def hcm_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc).astimezone(HCM_TZ)


def hcm_today() -> _dt.date:
    return hcm_now().date()


def parse_hcm_date(value, *, field: str = "date") -> _dt.date:
    """Parse a ``YYYY-MM-DD`` date argument (the tool-facing date format).

    ``None``/empty means "today in Asia/Ho_Chi_Minh".
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return hcm_today()
    if isinstance(value, _dt.datetime):
        return value.astimezone(HCM_TZ).date() if value.tzinfo else value.date()
    if isinstance(value, _dt.date):
        return value
    text = str(value or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if not m:
        raise ValueError(f"{field} must be YYYY-MM-DD (got {text!r})")
    return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


# --------------------------------------------------------------------------
# Deadline parsing (client-side: deadline format is not fixed by the schema)
# --------------------------------------------------------------------------
# Deadline values are parsed "when parseable". Naive datetimes are treated as
# already-local (HCM) dates; tz-aware datetimes are converted to HCM first.
_DEADLINE_PATTERNS = (
    ("%Y-%m-%d", False),
    ("%Y-%m-%dT%H:%M", False),
    ("%Y-%m-%dT%H:%M:%S", False),
    ("%Y-%m-%d %H:%M", False),
    ("%Y-%m-%d %H:%M:%S", False),
    ("%d/%m/%Y", False),
    ("%d/%m/%Y %H:%M", False),
    ("%d-%m-%Y", False),
    ("%d/%m/%y", False),
)


def parse_deadline(value) -> "_dt.date | None":
    """Best-effort deadline -> date. ``None`` when missing or unparseable."""
    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        return value.astimezone(HCM_TZ).date() if value.tzinfo else value.date()
    if isinstance(value, _dt.date):
        return value
    text = str(value).strip()
    if not text:
        return None
    # ISO 8601 with explicit offset / Z
    if text.endswith(("Z", "+00:00")) or re.search(r"[+-]\d{2}:\d{2}$", text):
        try:
            parsed = _dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed.astimezone(HCM_TZ).date()
        except ValueError:
            return None
    for fmt, _ in _DEADLINE_PATTERNS:
        try:
            return _dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


# --------------------------------------------------------------------------
# Bounded output shaping
# --------------------------------------------------------------------------

_MAX_TEXT_CHARS = 240


def truncate(text, limit: int = _MAX_TEXT_CHARS):
    if text is None:
        return None
    s = str(text)
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _norm_str(value):
    return None if value is None else str(value)


def task_item(doc: dict) -> dict:
    """Bounded today-work item from a tasks document (source label: TASK)."""
    return {
        "ref": _norm_str(doc.get("task_id")),
        "kind": "TASK",
        "source": TASKS,
        "action": truncate(doc.get("content")),
        "assignee": _norm_str(doc.get("assignee")),
        "assignee_user_id": _norm_str(doc.get("assignee_user_id")),
        "deadline_raw": (
            None if doc.get("deadline") is None else str(doc["deadline"])
        ),
        "created_at": (
            None if doc.get("created_at") is None else str(doc["created_at"])
        ),
    }


def shipment_summary(doc: dict) -> dict:
    """Bounded shipment status view. Never includes the raw ``data`` payload.

    Observed normalization (core/database.py):
      - shipment_id defaults to id
      - customer/client mirror each other
      - status defaults from data["0.0"]["st"] when the top-level field is absent
      - data sections observed: "0.0", "1.2", "2.4", "2.6", "2.7", "3.4", "entrustment"

    NOTE: the section key "0.0" contains a dot, so it CANNOT be addressed with
    Mongo dot-notation (numeric segments are read as array indexes). All
    section extraction is therefore done in Python on the fetched document.
    Financial data (data["3.4"]) is deliberately not extracted here; a simple
    status request must not expose it.
    """
    data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
    sec_00 = data.get("0.0") if isinstance(data.get("0.0"), dict) else {}
    sec_12 = data.get("1.2") if isinstance(data.get("1.2"), dict) else {}
    sec_24 = data.get("2.4") if isinstance(data.get("2.4"), dict) else {}
    sec_27 = data.get("2.7") if isinstance(data.get("2.7"), dict) else {}

    status = doc.get("status")
    status_source = "status"
    if status is None or str(status).strip() == "":
        status = sec_00.get("st")
        status_source = 'data["0.0"]["st"]'
    customer = doc.get("customer")
    if customer is None:
        customer = doc.get("client")

    out = {
        "id": _norm_str(doc.get("id")),
        "shipment_id": _norm_str(doc.get("shipment_id") or doc.get("id")),
        "status": _norm_str(status),
        "status_source": status_source,
        "customer": _norm_str(customer),
    }
    # Key current stage / operational flags, only when actually present.
    for key, section, source_key in (
        ("mode", sec_00, "mode"),
        ("incoterm", sec_00, "incoterm"),
        ("booking_no", sec_12, "booking_no"),
        ("mbl", sec_12, "mbl"),
        ("customs_status", sec_24, "customs_status"),
    ):
        if source_key in section and section[source_key] is not None:
            out[key] = _norm_str(section[source_key])
    if "is_delivered" in sec_27:
        out["is_delivered"] = bool(sec_27["is_delivered"])
    if doc.get("version") is not None:
        out["version"] = doc["version"]
    if doc.get("created_at") is not None:
        out["created_at"] = str(doc["created_at"])
    if doc.get("updated_at") is not None:
        out["updated_at"] = str(doc["updated_at"])
    return out
