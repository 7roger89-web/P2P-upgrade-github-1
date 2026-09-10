"""Observed logistics-work-desk data contracts for the Hermes read-only plugin.

Schema provenance (LOGISTICS_SCHEMA_OBSERVED):
    Observed contracts from 7roger89-web/logistics-work-desk main, supplied by
    the Owner on 2026-09-09 and extracted from the actual repository source
    (core/database.py normalization, add_task()/load_tasks() loaders,
    load_rate_cards() repository).
  * Rate cards: the STRUCTURED rate-card schema merged via logistics-work-desk
    PR #12 (merge commit 2eb2c343c10c2f909685f1f83cb77683197572f8, authoritative
    shape supplied by the Owner on 2026-09-10) adds ``structured_lookup_ready``
    plus a structured ``route`` object (origin, destination, equipment_type,
    container_size, transport_mode) and top-level ``currency``. The freight
    tool performs a deterministic structured lookup against those fields.
    ``route_name`` remains free text and is NEVER parsed for machine lookup,
    and no geographic aliases are invented (e.g. "HP" never becomes
    "Hải Phòng"). Legacy rate cards without the structured shape are excluded
    by the ``structured_lookup_ready == true`` filter.

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

# Personal-scope semantics for TODAY_WORK: tasks documents support assignee /
# assignee_user_id but there is NO identity binding (e.g. Telegram user ->
# Logistics assignee_user_id) in this task. When no assignee identity is
# supplied the result is explicitly TEAM-scoped and the model must not present
# it as the user's own personal tasks. A future bounded task may bind
# messaging identity -> Logistics assignee_user_id.
TODAY_WORK_TEAM_SCOPE_NOTE = (
    "No personal assignee identity was supplied; results may include open "
    "tasks for the whole team."
)

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
# rate_cards — STRUCTURED shape (logistics-work-desk PR #12, merge commit
# 2eb2c343c10c2f909685f1f83cb77683197572f8; authoritative shape supplied by
# the Owner on 2026-09-10):
#
#   {
#     "id": str,
#     "customer": str,
#     "route_name": str,                      # FREE TEXT — never machine-parsed
#     "route": {
#       "origin": str,
#       "destination": str,
#       "equipment_type": str,
#       "container_size": str,
#       "transport_mode": str,
#     },
#     "currency": str,
#     "structured_lookup_ready": bool,
#     "history": [
#       {"month": "MM/YYYY", "total_cost": number, "total_price": number,
#        "profit": number, "details": list, "updated_at": "YYYY-MM-DD"}
#     ],
#   }
#
# Lookup contract: only rate cards with structured_lookup_ready == true and
# is_deleted != true are queried. Matching uses the structured route.* fields
# only; route_name is descriptive free text and is never read by the matcher.
# There is deliberately NO geographic alias/normalization: origin/destination
# compare verbatim (stripped), so "HP" never silently becomes "Hải Phòng".
# The ONLY normalization permitted is the bounded deterministic container
# table below.
# --------------------------------------------------------------------------

RATE_CARD_READY_FLAG = "structured_lookup_ready"

# Active, structured-lookup-ready filter (plain field matches + $ne only, as
# enforced by the read-only connector's filter validator).
RATE_CARD_ACTIVE_FILTER = {
    RATE_CARD_READY_FLAG: True,
    "is_deleted": {"$ne": True},
}

# Structured field paths (Mongo dot-notation; every segment is a named key,
# unlike the shipments "0.0" section whose numeric segment needs Python reads).
RATE_CARD_ROUTE_ORIGIN = "route.origin"
RATE_CARD_ROUTE_DESTINATION = "route.destination"
RATE_CARD_ROUTE_EQUIPMENT_TYPE = "route.equipment_type"
RATE_CARD_ROUTE_CONTAINER_SIZE = "route.container_size"
RATE_CARD_ROUTE_TRANSPORT_MODE = "route.transport_mode"

RATE_CARD_VERIFIED_TOP_LEVEL_FIELDS = (
    "id", "customer", "route_name", "route", "currency",
    "structured_lookup_ready", "history",
)
RATE_CARD_VERIFIED_ROUTE_FIELDS = (
    "origin", "destination", "equipment_type", "container_size", "transport_mode",
)
RATE_CARD_VERIFIED_HISTORY_FIELDS = (
    "month", "total_cost", "total_price", "profit", "details", "updated_at",
)

# Freight lookup statuses. The old schema-gap fail-closed status was retired
# together with the pre-PR#12 free-text schema and must never be emitted;
# these four are the complete freight status surface.
FREIGHT_STATUS_OK = "OK"
FREIGHT_STATUS_NOT_FOUND = "NOT_FOUND"
FREIGHT_STATUS_AMBIGUOUS = "AMBIGUOUS"
FREIGHT_STATUS_HISTORY_NOT_FOUND = "RATE_HISTORY_NOT_FOUND"

# --------------------------------------------------------------------------
# Container-size normalization — the ONLY non-verbatim matcher normalization.
# Bounded, deterministic, and compatible with the Logistics structured schema.
# Unknown spellings pass through verbatim (never guessed, never expanded into
# a different equipment type).
# --------------------------------------------------------------------------

_CONTAINER_QUOTE_TRANSLATION = str.maketrans({"‘": "'", "’": "'", "′": "'", "´": "'"})


def _container_lookup_key(value) -> str:
    """Case/space/typographic-quote-insensitive container spelling key."""
    if value is None:
        return ""
    return (
        str(value)
        .strip()
        .upper()
        .translate(_CONTAINER_QUOTE_TRANSLATION)
        .replace(" ", "")
    )


# Explicit alias table ONLY (sourced from the lookup contract; no guessed
# variants are added). Canonical spellings are the Logistics schema forms.
_CONTAINER_SIZE_CANONICAL = {
    # 20' standard dry: 20 / 20FT / 20' -> 20'
    "20": "20'",
    "20FT": "20'",
    "20'": "20'",
    # 40' high cube: 40HQ / 40HC -> 40HC
    "40HQ": "40HC",
    "40HC": "40HC",
}


def canonical_container_size(value) -> "str | None":
    """Normalize a container-size spelling to the Logistics canonical form.

    Returns None for empty/None input; an unrecognized but non-empty spelling
    is returned in its cleaned (upper/trim/quote-unified) form so that equal
    spellings still match verbatim without inventing an alias.
    """
    key = _container_lookup_key(value)
    if not key:
        return None
    return _CONTAINER_SIZE_CANONICAL.get(key, key)


# --------------------------------------------------------------------------
# rate-card history (MM/YYYY months; array order must not be trusted)
# --------------------------------------------------------------------------

_RATE_MONTH_RE = re.compile(r"^(0[1-9]|1[0-2])/(\d{4})$")


def parse_rate_month(value) -> "tuple[int, int] | None":
    """Parse ``MM/YYYY`` into a comparable ``(year, month)`` tuple; else None."""
    if value is None:
        return None
    m = _RATE_MONTH_RE.fullmatch(str(value).strip())
    if not m:
        return None
    return int(m.group(2)), int(m.group(1))


def format_rate_month(year: int, month: int) -> str:
    return f"{month:02d}/{year:04d}"


def _valid_history_entries(history) -> "list[tuple[tuple[int, int], dict]]":
    """(parsed month, entry) pairs for well-formed history entries only."""
    out = []
    if isinstance(history, list):
        for entry in history:
            if not isinstance(entry, dict):
                continue
            parsed = parse_rate_month(entry.get("month"))
            if parsed is not None:
                out.append((parsed, entry))
    return out


def _updated_at_key(entry: dict):
    # updated_at is YYYY-MM-DD, so lexicographic ordering is chronological;
    # missing/unparseable values sort first (deterministic, no array trust).
    updated = entry.get("updated_at")
    return (str(updated),) if isinstance(updated, str) else ("",)


def select_rate_history(history, requested_month: "tuple[int, int] | None") -> "dict | None":
    """Pick the history entry for the requested month, or the LATEST valid one.

    ``requested_month`` is a parsed (year, month) tuple or None (latest).
    Latest is computed by parsing MM/YYYY — array order is never trusted.
    Returns None when no matching/valid entry exists (the tool then reports
    RATE_HISTORY_NOT_FOUND and never invents a price).
    """
    entries = _valid_history_entries(history)
    if requested_month is not None:
        matched = [entry for month, entry in entries if month == requested_month]
        if not matched:
            return None
        return max(matched, key=_updated_at_key)
    if not entries:
        return None
    latest_month = max(month for month, _ in entries)
    matched = [entry for month, entry in entries if month == latest_month]
    return max(matched, key=_updated_at_key)


def valid_rate_months(history) -> "list[str]":
    """Chronologically sorted, de-duplicated valid MM/YYYY months."""
    months = sorted({month for month, _ in _valid_history_entries(history)})
    return [format_rate_month(year, month) for year, month in months]


def rate_card_view(doc: dict) -> dict:
    """Bounded structured facts from a rate_cards document.

    Deliberately excludes route_name (free text, never used for lookup) and
    every monetary value (prices are attached only by the OK path from the
    selected history entry).
    """
    route = doc.get("route") if isinstance(doc.get("route"), dict) else {}
    return {
        "rate_card_id": _norm_str(doc.get("id")),
        "customer": _norm_str(doc.get("customer")),
        "route": {field: _norm_str(route.get(field)) for field in RATE_CARD_VERIFIED_ROUTE_FIELDS},
        "currency": _norm_str(doc.get("currency")),
    }

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
