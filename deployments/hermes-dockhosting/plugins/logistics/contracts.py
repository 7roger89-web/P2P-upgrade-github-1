"""Observed logistics-work-desk data contracts for the Hermes read-only plugin.

Schema provenance (LOGISTICS_SCHEMA_OBSERVED):
    Observed contracts from 7roger89-web/logistics-work-desk main, supplied by
    the Owner and extracted from the actual repository source (core/database.py
    normalization, add_task()/load_tasks() loaders, load_rate_cards()
    repository). The STRUCTURED rate-card shape below comes from logistics-work-
    desk PR #12 (merge commit 2eb2c343c10c2f909685f1f83cb77683197572f8), which
    added the structured ``route`` object, ``currency`` and
    ``structured_lookup_ready`` fields. These constants are NOT guesses from
    collection names.

Rate-card lookup contract (HERMES_LOGISTICS_FREIGHT_LOOKUP_002):
    * Only rate cards with ``structured_lookup_ready == true`` and
      ``is_deleted != true`` are queried; legacy free-text rate cards are
      therefore excluded by the query filter itself, not by post-filtering.
    * Matching uses ONLY the structured fields ``route.origin``,
      ``route.destination`` and (when supplied) ``route.equipment_type``,
      ``route.container_size``, ``route.transport_mode``.
    * ``route_name`` is a human label and is NEVER parsed, echoed, or used for
      matching. No geographic alias table exists: "HP" does not become
      "Hải Phòng".
    * Price semantics are preserved: ``total_price`` is the customer quoted
      rate (returned as ``selling_price``), ``total_cost`` stays
      ``internal_cost``, ``profit`` stays ``profit``.
    * ``history.month`` is ``MM/YYYY``. The latest month is chosen by PARSING
      MM/YYYY (never by trusting array order); an absent month returns
      RATE_HISTORY_NOT_FOUND instead of an invented price.
    * Multiple customer-specific matches return AMBIGUOUS; one is never
      silently chosen.
    * Status values: OK / NOT_FOUND / AMBIGUOUS / RATE_HISTORY_NOT_FOUND. The
      obsolete fail-closed schema-gap status (added when the rate-card schema
      had no structured route fields) is gone: PR #12 supplied the structured
      schema, so it must never be returned again.

This module is pure Python (stdlib only): no pymongo import, no I/O, so it is
unit-testable anywhere and safe to import at plugin-registration time.
"""

from __future__ import annotations

import datetime as _dt
import re
import unicodedata

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
# rate_cards — STRUCTURED Rate Card schema (logistics-work-desk PR #12,
# merge commit 2eb2c343c10c2f909685f1f83cb77683197572f8)
# --------------------------------------------------------------------------
# Authoritative persisted shape:
#   {
#     "id": str,
#     "customer": str,
#     "route_name": str,          # HUMAN LABEL ONLY — never machine-parsed
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
#        "profit": number, "details": [...], "updated_at": "YYYY-MM-DD"}
#     ]
#   }
#
# The query filter below selects ONLY structured, non-deleted rate cards, so
# legacy free-text rate cards (no structured_lookup_ready / no route object)
# never reach the matcher.

# Status contract. The obsolete fail-closed schema-gap status was removed once
# PR #12 supplied the structured route fields; it must never be returned again.
RATE_CARD_STATUS_OK = "OK"
RATE_CARD_STATUS_NOT_FOUND = "NOT_FOUND"
RATE_CARD_STATUS_AMBIGUOUS = "AMBIGUOUS"
RATE_CARD_STATUS_HISTORY_NOT_FOUND = "RATE_HISTORY_NOT_FOUND"
RATE_CARD_STATUSES = (
    RATE_CARD_STATUS_OK,
    RATE_CARD_STATUS_NOT_FOUND,
    RATE_CARD_STATUS_AMBIGUOUS,
    RATE_CARD_STATUS_HISTORY_NOT_FOUND,
)

# Server-side (Mongo) pre-filter for freight lookup: structured_lookup_ready
# must be true and the card must not be soft-deleted.
RATE_CARD_ACTIVE_FILTER = {"structured_lookup_ready": True, "is_deleted": {"$ne": True}}

# Bounded scan of structured rate cards (equals the connector MAX_LIMIT).
RATE_CARD_SCAN_LIMIT = 200

RATE_CARD_ROUTE_FIELDS = (
    "origin", "destination", "equipment_type", "container_size", "transport_mode",
)
RATE_CARD_HISTORY_FIELDS = (
    "month", "total_cost", "total_price", "profit", "details", "updated_at",
)

# Business meaning of the money fields — never mix these up.
PRICE_SEMANTICS = {
    "selling_price": (
        "total_price — customer quoted rate; this is the answer to "
        "'Cước X về Y bao nhiêu?'"
    ),
    "internal_cost": (
        "total_cost — internal cost; must NEVER be presented as the customer "
        "freight rate"
    ),
    "profit": "profit — internal margin",
}

# --- deterministic container normalization ---------------------------------
# Only safe, deterministic container aliases that are already compatible with
# the Logistics schema. Anything not listed falls through unchanged (compared
# literally), so no container size is ever guessed.
_CONTAINER_CANONICAL = {
    "20": "20'",
    "20'": "20'",
    "20FT": "20'",
    "40": "40'",
    "40'": "40'",
    "40FT": "40'",
    "40HC": "40HC",
    "40HQ": "40HC",
}
_CONTAINER_QUOTES = {"\u2019": "'", "\u2032": "'", "\u02bc": "'", "\u0060": "'"}


def normalize_container_size(value):
    """Canonicalize a container size deterministically (20/20FT/20' -> 20', 40HQ/40HC -> 40HC).

    Unknown values are returned in a compacted uppercase form and are therefore
    only ever compared literally — never mapped to a different container.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for bad, good in _CONTAINER_QUOTES.items():
        text = text.replace(bad, good)
    key = re.sub(r"[\s_-]+", "", text).upper()
    return _CONTAINER_CANONICAL.get(key, key)


def normalize_text(value):
    """Deterministic text normalization for structured field matching.

    Unicode NFC -> whitespace collapse -> accent folding -> casefold. This is
    text normalization, NOT geographic matching: there is no alias table, no
    abbreviation expansion ("HP" never becomes "Hải Phòng"), no substring,
    prefix, edit-distance or fuzzy matching.
    """
    if value is None:
        return None
    text = unicodedata.normalize("NFC", str(value)).strip()
    if not text:
        return None
    text = re.sub(r"\s+", " ", text)
    folded = "".join(
        ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch)
    )
    return unicodedata.normalize("NFC", folded).casefold()


def values_match(requested, stored) -> bool:
    """True when ``requested`` is not supplied, or equals ``stored`` after normalization."""
    if requested is None or (isinstance(requested, str) and not requested.strip()):
        return True
    return normalize_text(requested) == normalize_text(stored)


def container_matches(requested, stored) -> bool:
    """Container comparison with deterministic alias normalization."""
    if requested is None or (isinstance(requested, str) and not requested.strip()):
        return True
    return normalize_container_size(requested) == normalize_container_size(stored)


def rate_card_route(doc: dict) -> dict:
    """The structured ``route`` object of a rate card ({} when absent)."""
    route = doc.get("route") if isinstance(doc, dict) else None
    return dict(route) if isinstance(route, dict) else {}


def match_rate_card(
    doc: dict,
    *,
    origin,
    destination,
    container_size=None,
    equipment_type=None,
    transport_mode=None,
    customer=None,
) -> bool:
    """Structured deterministic match on the rate-card schema.

    ``route_name`` is deliberately never read: it is a free-text human label.
    A supplied argument acts as a filter; an omitted argument matches anything.
    """
    route = rate_card_route(doc)
    if not values_match(origin, route.get("origin")):
        return False
    if not values_match(destination, route.get("destination")):
        return False
    if not container_matches(container_size, route.get("container_size")):
        return False
    if not values_match(equipment_type, route.get("equipment_type")):
        return False
    if not values_match(transport_mode, route.get("transport_mode")):
        return False
    if not values_match(customer, doc.get("customer")):
        return False
    return True


# --- history / MM/YYYY month handling --------------------------------------

_MONTH_RE = re.compile(r"^(\d{1,2})/(\d{4})$")


def parse_month(value):
    """Parse an ``MM/YYYY`` month. Returns ``(year, month)`` or ``None``."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    m = _MONTH_RE.match(text)
    if not m:
        return None
    month, year = int(m.group(1)), int(m.group(2))
    if not 1 <= month <= 12:
        return None
    return (year, month)


def canonical_month(value):
    """``MM/YYYY`` canonical form of a month value (``None`` when unparseable)."""
    parsed = parse_month(value)
    if parsed is None:
        return None
    year, month = parsed
    return f"{month:02d}/{year:04d}"


def month_from_date(value) -> "str | None":
    """``MM/YYYY`` for a ``YYYY-MM-DD`` date value (``None`` when unparseable)."""
    if value is None:
        return None
    try:
        day = parse_hcm_date(value, field="date")
    except (ValueError, TypeError):
        return None
    return f"{day.month:02d}/{day.year:04d}"


def history_entries(doc: dict) -> list:
    """The ``history`` list entries that are dicts ([] when absent)."""
    history = doc.get("history") if isinstance(doc, dict) else None
    if not isinstance(history, list):
        return []
    return [entry for entry in history if isinstance(entry, dict)]


def available_months(doc: dict) -> list:
    """Sorted canonical ``MM/YYYY`` months present in a rate card's history."""
    months = []
    for entry in history_entries(doc):
        month = canonical_month(entry.get("month"))
        if month is not None and month not in months:
            months.append(month)
    return sorted(months, key=lambda m: parse_month(m))


def select_latest_history(doc: dict):
    """Latest history entry by PARSED ``MM/YYYY`` (never by array order).

    Returns ``(entry, "MM/YYYY")``; ``(None, None)`` when the rate card has no
    history entry with a valid month. Ties are resolved deterministically by
    ``updated_at`` and then by array index.
    """
    best = None
    for index, entry in enumerate(history_entries(doc)):
        parsed = parse_month(entry.get("month"))
        if parsed is None:
            continue  # unparseable month: never trusted, never guessed
        key = (parsed, str(entry.get("updated_at") or ""), index)
        if best is None or key > best[0]:
            best = (key, entry)
    if best is None:
        return None, None
    entry = best[1]
    return entry, canonical_month(entry.get("month"))


def select_history_for_month(doc: dict, month):
    """History entry for an explicitly requested month.

    Returns ``(entry, "MM/YYYY")``; ``(None, None)`` when that month is absent
    (the caller must report RATE_HISTORY_NOT_FOUND, never invent a price).
    """
    target = parse_month(month)
    if target is None:
        return None, None
    best = None
    for index, entry in enumerate(history_entries(doc)):
        if parse_month(entry.get("month")) != target:
            continue
        key = (str(entry.get("updated_at") or ""), index)
        if best is None or key > best[0]:
            best = (key, entry)
    if best is None:
        return None, None
    entry = best[1]
    return entry, canonical_month(entry.get("month"))


def rate_card_candidate(doc: dict, entry=None, month=None) -> dict:
    """Bounded facts about one matching rate card (safe for AMBIGUOUS output).

    Contains only: rate_card_id, customer, route (origin/destination/equipment/
    container/mode), month, selling_price, currency. Internal cost and profit
    are deliberately NOT part of a candidate.
    """
    route = rate_card_route(doc)
    return {
        "rate_card_id": _norm_str(doc.get("id")),
        "customer": _norm_str(doc.get("customer")),
        "route": {
            "origin": _norm_str(route.get("origin")),
            "destination": _norm_str(route.get("destination")),
            "equipment_type": _norm_str(route.get("equipment_type")),
            "container_size": _norm_str(route.get("container_size")),
            "transport_mode": _norm_str(route.get("transport_mode")),
        },
        "month": month,
        "selling_price": entry.get("total_price") if isinstance(entry, dict) else None,
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
