"""Read-only Logistics query connector for Hermes.

This is the authoritative read-only bridge between Hermes and the Logistics
MongoDB datastore. It exposes exactly three read-only capabilities:

* ``today_work(date)``           -> items to act on for a target day
* ``freight_rate_lookup(...)``   -> current/recent freight rate for a route
* ``shipment_status(id)``        -> current status for a shipment reference

Design invariants
-----------------
READ-ONLY BY DESIGN
    The public surface exposes no mutation operations. ``ReadOnlyClient`` /
    ``ReadOnlyDatabase`` / ``ReadOnlyCollection`` wrap a ``pymongo``
    client/database/collection and raise
    ``ReadOnlyViolation`` for every attribute that is not an explicit read
    method (``find``, ``find_one``, ``count_documents``, ``aggregate``,
    ``distinct``, ``list_collection_names``). This blocks insert / update /
    delete / drop / create_index and friends at the code surface. At the
    network layer the runtime uses a read-only credential via
    ``LOGISTICS_MONGO_URI_READONLY``.

NO SECRETS IN CODE
    The Mongo URI and database name come from environment variables
    (``LOGISTICS_MONGO_URI_READONLY`` / ``LOGISTICS_MONGO_DB_NAME``), never
    from the repository or this source tree.

FACT INTEGRITY
    This module never fabricates a rate, currency, route, shipment status,
    date, container type, or business fact. When data is absent it returns
    ``NOT_FOUND``. When the schema contract cannot be satisfied it returns
    ``SCHEMA_UNVERIFIED``. It never synthesizes a plausible value.

SCHEMA-DRIVEN
    Collection + field resolution comes from a schema contract file
    (``schema.yaml``) loaded by :func:`load_schema`. The shipped default is
    PROVISIONAL and must be confirmed against the Logistics application
    (``7roger89-web/logistics-work-desk``). Because resolution is
    data-driven (fields are inferred from a sampled document and matched by
    normalized equality in Python), a wrong contract produces ``NOT_FOUND``
    rather than a wrong fact.
"""

from __future__ import annotations

import datetime
import json
import os
import re
from zoneinfo import ZoneInfo

__all__ = [
    "LOGISTICS_TZ",
    "ReadOnlyViolation",
    "ReadOnlyCollection",
    "ReadOnlyDatabase",
    "ReadOnlyClient",
    "make_read_only_connection",
    "load_schema",
    "LogisticsConnector",
    "today_work",
    "freight_rate_lookup",
    "shipment_status",
]

LOGISTICS_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# Bounded scan for client-side normalized matching. Rate cards are small; we
# never scan an unbounded collection.
DEFAULT_SCAN_LIMIT = 2000


# ---------------------------------------------------------------------------
# Read-only enforcement
# ---------------------------------------------------------------------------
class ReadOnlyViolation(RuntimeError):
    """Raised when a write operation is attempted through a read-only surface."""


class ReadOnlyCollection:
    """Read-only view of a ``pymongo`` collection.

    Only read operations are reachable. Any other attribute access that could
    correspond to a mutation (``insert_one``, ``update_many``, ``delete_one``,
    ``create_index``, ...) raises :class:`ReadOnlyViolation`.
    """

    _ALLOWED = frozenset(
        {
            "find",
            "find_one",
            "count_documents",
            "aggregate",
            "distinct",
            "estimated_document_count",
            "name",
            "full_name",
        }
    )

    def __init__(self, collection):
        self._collection = collection

    def find(self, *args, **kwargs):
        return self._collection.find(*args, **kwargs)

    def find_one(self, *args, **kwargs):
        return self._collection.find_one(*args, **kwargs)

    def count_documents(self, *args, **kwargs):
        return self._collection.count_documents(*args, **kwargs)

    def aggregate(self, *args, **kwargs):
        return self._collection.aggregate(*args, **kwargs)

    def distinct(self, *args, **kwargs):
        return self._collection.distinct(*args, **kwargs)

    def estimated_document_count(self, *args, **kwargs):
        return self._collection.estimated_document_count(*args, **kwargs)

    @property
    def name(self):
        return self._collection.name

    @property
    def full_name(self):
        return self._collection.full_name

    def __getattr__(self, item):
        if item in self._ALLOWED:
            return getattr(self._collection, item)
        raise ReadOnlyViolation(
            f"Read-only connection: access to collection operation '{item}' is "
            "forbidden. The Logistics connector exposes no mutation operations."
        )

    def __repr__(self):  # pragma: no cover - debug aid
        return f"<ReadOnlyCollection {self.name}>"


class ReadOnlyDatabase:
    """Read-only view of a ``pymongo`` database."""

    _ALLOWED = frozenset(
        {
            "get_collection",
            "__getitem__",
            "list_collection_names",
            "list_collections",
            "collection_names",
            "__iter__",
        }
    )

    def __init__(self, database):
        self._database = database

    def get_collection(self, name, *args, **kwargs):
        return ReadOnlyCollection(self._database.get_collection(name, *args, **kwargs))

    def __getitem__(self, name):
        return ReadOnlyCollection(self._database[name])

    def list_collection_names(self, *args, **kwargs):
        return self._database.list_collection_names(*args, **kwargs)

    def list_collections(self, *args, **kwargs):
        return self._database.list_collections(*args, **kwargs)

    def collection_names(self, *args, **kwargs):
        return self._database.list_collection_names(*args, **kwargs)

    def __iter__(self):
        return iter(list(self._database.list_collection_names()))

    def __getattr__(self, item):
        if item in self._ALLOWED:
            return getattr(self._database, item)
        raise ReadOnlyViolation(
            f"Read-only connection: access to database operation '{item}' is "
            "forbidden. The Logistics connector exposes no mutation operations."
        )


class ReadOnlyClient:
    """Read-only view of a ``pymongo`` client (blocks ``drop_database`` etc.)."""

    _ALLOWED = frozenset({"get_database", "__getitem__", "get_default_database"})

    def __init__(self, client):
        self._client = client

    def get_database(self, name=None, *args, **kwargs):
        return ReadOnlyDatabase(self._client.get_database(name, *args, **kwargs))

    def get_default_database(self, *args, **kwargs):
        return ReadOnlyDatabase(self._client.get_default_database(*args, **kwargs))

    def __getitem__(self, name):
        return ReadOnlyDatabase(self._client[name])

    def __getattr__(self, item):
        if item in self._ALLOWED:
            return getattr(self._client, item)
        raise ReadOnlyViolation(
            f"Read-only connection: access to client operation '{item}' is "
            "forbidden. The Logistics connector exposes no mutation operations."
        )


def make_read_only_connection(uri: str, db_name: str) -> ReadOnlyDatabase:
    """Build a read-only MongoDB connection from env-style configuration.

    ``uri`` must be the *read-only* credential URI
    (``LOGISTICS_MONGO_URI_READONLY``). The returned object surfaces only read
    operations; writes are rejected by :class:`ReadOnlyViolation`.
    """
    import pymongo

    client = pymongo.MongoClient(uri, connectTimeoutMS=10_000, serverSelectionTimeoutMS=15_000)
    return ReadOnlyClient(client).get_database(db_name)


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------
def load_schema(path: str) -> dict:
    """Load a schema contract file (JSON or YAML) into a dict.

    Prefers JSON for a zero-dependency default; falls back to YAML when PyYAML
    is available (Hermes's runtime always has it). Unknown formats raise.
    """
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    if path.lower().endswith(".json"):
        return json.loads(text)

    # Prefer YAML if available (Hermes ships PyYAML in the runtime venv).
    if path.lower().endswith((".yaml", ".yml")):
        try:
            import yaml
        except ImportError:  # pragma: no cover - Hermes runtime has PyYAML
            raise RuntimeError(
                "PyYAML is required to load the YAML schema contract; "
                "install pyyaml or use a JSON schema file."
            ) from None
        return yaml.safe_load(text)

    # Try YAML (most common), then JSON as a fallback for unlabeled files.
    try:
        import yaml

        return yaml.safe_load(text)
    except ImportError:
        return json.loads(text)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
_WS_RE = re.compile(r"\s+")


def normalize(value, fallback="") -> str:
    """Normalize a free-text value for conservative matching.

    Lowercases, strips, and collapses whitespace. Deliberately does NOT strip
    Vietnamese diacritics — doing so could silently match a different route or
    place and yield a wrong fact. Fact integrity wins over fuzzy recall.
    """
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return fallback
    return _WS_RE.sub(" ", str(value)).strip().lower()


def resolve_field(doc: dict, candidates) -> tuple:
    """Return ``(value, matched_name)`` for the first candidate present in doc.

    ``candidates`` is a list of physical field names. Returns ``(None, None)``
    when none of the candidates are present on the document.
    """
    for name in candidates or []:
        if name in doc and doc[name] is not None:
            return doc[name], name
    return None, None


def coerce_date(value):
    """Best-effort conversion to ``datetime.date``.

    Accepts ``date``, ``datetime``, ISO-8601 strings, and unix-ish numbers.
    Returns ``None`` when the value cannot be interpreted. Never invents a date.
    """
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc).date()
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        try:
            iso = datetime.datetime.fromisoformat(s)
            if iso.tzinfo is None:
                iso = iso.replace(tzinfo=datetime.timezone.utc)
            return iso.date()
        except (ValueError, TypeError):
            return None
    return None


def _queried_at() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _result(status, source, queried_at=None, **extra):
    """Build a normalized factual result with provenance."""
    payload = {
        "status": status,
        "source": source,
        "queried_at": queried_at or _queried_at(),
        "schema_status": "PROVISIONAL_UNVERIFIED",
    }
    payload.update(extra)
    return payload


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------
def _collection(db, name) -> object:
    return db[name]


def _collection_exists(db, name) -> bool:
    names = list(db.list_collection_names())
    return name in names


def _infer_field(doc, candidates):
    """Return the first physical field name present on a sampled doc."""
    if not doc:
        return None
    for name in candidates or []:
        if name in doc:
            return name
    return None


# ---------------------------------------------------------------------------
# Capability 1: TODAY_WORK
# ---------------------------------------------------------------------------
def today_work(connector, target_date: datetime.date) -> dict:
    """Read actionable Logistics items for ``target_date``.

    The source(s) of "Việc Cần Xử Lý" (today's work) come from the schema
    contract's ``today_work.sources``. If a source has no resolvable date
    field, it is reported as a schema gap rather than silently skipped.
    """
    queried_at = _queried_at()
    schema = connector.schema
    sources = (schema.get("today_work") or {}).get("sources") or []
    limit = int(connector.scan_limit or DEFAULT_SCAN_LIMIT)
    max_items = int((schema.get("today_work") or {}).get("max_items", 20))

    start = target_date
    end = start + datetime.timedelta(days=1)

    items = []
    gaps = []
    consulted = []

    for src in sources:
        coll_name = src.get("collection")
        if not coll_name or not _collection_exists(connector.db, coll_name):
            gaps.append({"collection": coll_name, "reason": "collection_not_found"})
            continue

        collection = _collection(connector.db, coll_name)
        sample = collection.find_one({})
        date_field = _infer_field(sample, src.get("date_field", []))
        id_field = _infer_field(sample, src.get("id_field", []))
        title_field = _infer_field(sample, src.get("title_field", []))
        status_field = _infer_field(sample, src.get("status_field", []))

        if date_field is None:
            gaps.append({"collection": coll_name, "reason": "no_resolvable_date_field"})
            continue

        consulted.append(coll_name)
        query = {date_field: {"$gte": start, "$lt": end}}
        # Bound the scan; sort by date range; return matching documents.
        docs = list(collection.find(query).limit(limit))

        for doc in docs:
            date_val, _ = resolve_field(doc, [date_field])
            if coerce_date(date_val) != target_date:
                continue
            item_id, _ = resolve_field(doc, [id_field] if id_field else [])
            title, _ = resolve_field(doc, [title_field] if title_field else [])
            status, _ = resolve_field(doc, [status_field] if status_field else [])
            items.append(
                {
                    "id": str(item_id) if item_id is not None else None,
                    "action_or_status": status or title,
                    "reference_type": coll_name,
                    "date": date_val.isoformat() if hasattr(date_val, "isoformat") else str(date_val),
                }
            )

    # A source that actually exists and has a resolvable date field "counts" as
    # consulted. If we consulted at least one source and found no items, the
    # truthful answer is NOT_FOUND (the data was there, nothing on that day). An
    # absent/unresolvable source is a schema note, not a reason to call the
    # answer unverifiable. Only when NO source could be consulted is the result
    # SCHEMA_UNVERIFIED.
    if items:
        status = "FOUND"
    elif consulted:
        status = "NOT_FOUND"
    else:
        status = "SCHEMA_UNVERIFIED"

    extra = {
        "count": len(items),
        "items": items[:max_items],
        "date": target_date.isoformat(),
        "sources_consulted": consulted,
    }
    if items:
        extra.pop("message", None)
    else:
        extra["message"] = "Không tìm thấy việc cần xử lý cho ngày này trong dữ liệu hiện tại."
    if gaps:
        extra["schema_gaps"] = gaps

    return _result(status, "logistics_mongodb" if consulted else "logistics_schema", queried_at, **extra)


# ---------------------------------------------------------------------------
# Capability 2: FREIGHT_RATE_LOOKUP
# ---------------------------------------------------------------------------
def freight_rate_lookup(connector, origin, destination, container, date=None) -> dict:
    """Look up the current/recent freight rate for a route + container/vehicle.

    Matching is conservative: origin, destination, and container size are all
    normalized and must match. When several rows share the most recent
    effective date with different values, the result is AMBIGUOUS rather than a
    silently chosen wrong rate.
    """
    queried_at = _queried_at()
    schema = connector.schema
    cfg = schema.get("rate_lookup") or {}
    coll_name = cfg.get("collection") or "rate_cards"
    scan_limit = int(connector.scan_limit or DEFAULT_SCAN_LIMIT)
    history_limit = int(cfg.get("history_limit", 5))

    if not _collection_exists(connector.db, coll_name):
        return _result(
            "NOT_FOUND",
            "logistics_schema",
            queried_at,
            message="Chưa có dữ liệu bảng cước trong cơ sở dữ liệu Logistics hiện tại.",
        )

    collection = _collection(connector.db, coll_name)
    sample = collection.find_one({})
    origin_field = _infer_field(sample, schema["collections"].get("rate_cards", {}).get("origin_field", []))
    dest_field = _infer_field(
        sample, schema["collections"].get("rate_cards", {}).get("destination_field", [])
    )
    size_field = _infer_field(sample, schema["collections"].get("rate_cards", {}).get("size_field", []))
    rate_field = _infer_field(sample, schema["collections"].get("rate_cards", {}).get("rate_field", []))
    currency_field = _infer_field(
        sample, schema["collections"].get("rate_cards", {}).get("currency_field", [])
    )
    effective_field = _infer_field(
        sample, schema["collections"].get("rate_cards", {}).get("effective_date_field", [])
    )

    if None in (origin_field, dest_field, size_field, rate_field):
        return _result(
            "SCHEMA_UNVERIFIED",
            "logistics_schema",
            queried_at,
            message=(
                "Không thể xác định cấu trúc bảng cước trong dữ liệu hiện tại. "
                "Cần xác nhận tên trường (origin/destination/size/rate) với ứng dụng Logistics."
            ),
        )

    q_origin = normalize(origin)
    q_dest = normalize(destination)
    q_size = normalize(container)

    docs = list(collection.find({}).limit(scan_limit))

    matches = []
    for doc in docs:
        o, _ = resolve_field(doc, [origin_field] if origin_field else [])
        d, _ = resolve_field(doc, [dest_field] if dest_field else [])
        s, _ = resolve_field(doc, [size_field] if size_field else [])
        if (
            q_origin != ""
            and q_dest != ""
            and q_size != ""
            and normalize(o) == q_origin
            and normalize(d) == q_dest
            and normalize(s) == q_size
        ):
            rate, _ = resolve_field(doc, [rate_field])
            currency, _ = resolve_field(doc, [currency_field] if currency_field else [])
            eff_val, _ = resolve_field(doc, [effective_field] if effective_field else [])
            eff = coerce_date(eff_val) or datetime.date.min
            matches.append(
                {
                    "rate": rate,
                    "currency": currency,
                    "origin": o,
                    "destination": d,
                    "container": s,
                    "effective_date": getattr(eff_val, "isoformat", lambda: str(eff_val))()
                    if eff_val is not None and eff != datetime.date.min
                    else None,
                    "row_effective": eff,
                    "_id": str(doc.get("_id")) if doc.get("_id") is not None else None,
                }
            )

    if not matches:
        return _result(
            "NOT_FOUND",
            f"logistics_mongodb:{coll_name}",
            queried_at,
            rate=None,
            currency=None,
            origin=origin,
            destination=destination,
            container=container,
            effective_date=None,
            recent_history=[],
            message=(
                "Chưa có mức cước " + origin + " → " + destination + " container " + container
                + " trong dữ liệu hiện tại."
            ),
        )

    # If a date was requested, only rates effective on/before that date apply;
    # if none apply on/before the date, that date is a truthful NOT_FOUND.
    if date is not None:
        target_date = coerce_date(date)
        if target_date is not None:
            applicable = [m for m in matches if m["row_effective"] <= target_date]
            if not applicable:
                return _result(
                    "NOT_FOUND",
                    f"logistics_mongodb:{coll_name}",
                    queried_at,
                    rate=None,
                    currency=None,
                    origin=origin,
                    destination=destination,
                    container=container,
                    effective_date=None,
                    recent_history=[],
                    message=(
                        "Chưa có mức cước áp dụng cho ngày "
                        + target_date.isoformat() + " trên tuyến " + origin + " → "
                        + destination + " container " + container + "."
                    ),
                )
            matches = applicable

    matches.sort(key=lambda r: r["row_effective"], reverse=True)

    # Determine ambiguity: if the most-recent rows carry different rate values
    # they are ambiguous; we do not silently choose one.
    top_eff = matches[0]["row_effective"]
    top_group = [r for r in matches if r["row_effective"] == top_eff]
    distinct_rates = {str(r["rate"]) for r in top_group if r["rate"] is not None}
    ambiguous = len(distinct_rates) > 1

    latest = matches[0]
    history = [
        {
            "rate": r["rate"],
            "currency": r["currency"],
            "effective_date": r["effective_date"],
            "origin": r["origin"],
            "destination": r["destination"],
            "container": r["container"],
        }
        for r in matches[:history_limit]
    ]

    if ambiguous:
        status = "AMBIGUOUS"
        rate_value = None
        message = (
            "Có nhiều mức cước khác nhau cùng hiệu lực cho tuyến này; cần xác nhận "
            "mức cước chính xác với nguồn dữ liệu."
        )
    else:
        status = "FOUND"
        rate_value = latest["rate"]
        message = None

    return _result(
        status,
        f"logistics_mongodb:{coll_name}",
        queried_at,
        rate=rate_value,
        currency=latest["currency"],
        origin=latest["origin"],
        destination=latest["destination"],
        container=latest["container"],
        effective_date=latest["effective_date"],
        recent_history=history,
        message=message,
    )


# ---------------------------------------------------------------------------
# Capability 3: SHIPMENT_STATUS
# ---------------------------------------------------------------------------
def shipment_status(connector, shipment_id) -> dict:
    """Read the exact current status of a shipment by its id/reference.

    Returns only the fields the user asked about (status, current stage/action,
    customer/reference when available, updated_at) — never broad financial or
    private document payloads.
    """
    queried_at = _queried_at()
    schema = connector.schema
    cfg = schema.get("shipment_status") or {}
    coll_name = cfg.get("collection") or "shipments"

    if not _collection_exists(connector.db, coll_name):
        return _result(
            "NOT_FOUND", "logistics_schema", queried_at,
            message="Chưa có dữ liệu lô hàng trong cơ sở dữ liệu Logistics hiện tại.",
        )

    collection = _collection(connector.db, coll_name)
    sample = collection.find_one({})
    id_field = _infer_field(sample, schema["collections"].get("shipments", {}).get("id_field", []))
    status_field = _infer_field(
        sample, schema["collections"].get("shipments", {}).get("status_field", [])
    )
    customer_field = _infer_field(
        sample, schema["collections"].get("shipments", {}).get("customer_field", [])
    )
    updated_field = _infer_field(
        sample, schema["collections"].get("shipments", {}).get("updated_field", [])
    )
    title_field = _infer_field(
        sample, schema["collections"].get("shipments", {}).get("title_field", [])
    )

    if id_field is None or status_field is None:
        return _result(
            "SCHEMA_UNVERIFIED",
            "logistics_schema",
            queried_at,
            message=(
                "Không thể xác định cấu trúc lô hàng trong dữ liệu hiện tại. "
                "Cần xác nhận tên trường (id/status) với ứng dụng Logistics."
            ),
        )

    doc = _find_shipment(collection, id_field, shipment_id, sample)

    if doc is None:
        return _result(
            "NOT_FOUND",
            f"logistics_mongodb:{coll_name}",
            queried_at,
            shipment_id=str(shipment_id),
            message="Không tìm thấy lô hàng " + str(shipment_id) + " trong dữ liệu hiện tại.",
        )

    status, _ = resolve_field(doc, [status_field])
    customer, _ = resolve_field(doc, [customer_field] if customer_field else [])
    updated, _ = resolve_field(doc, [updated_field] if updated_field else [])
    title, _ = resolve_field(doc, [title_field] if title_field else [])
    ref_val, _ = resolve_field(doc, [id_field])

    return _result(
        "FOUND",
        f"logistics_mongodb:{coll_name}",
        queried_at,
        shipment_id=str(shipment_id),
        shipment_reference=str(ref_val) if ref_val is not None else str(shipment_id),
        current_status=str(status),
        current_action=title or status,
        customer=str(customer) if customer is not None else None,
        updated_at=str(updated) if updated is not None else None,
        record_id=str(doc.get("_id")) if doc.get("_id") is not None else None,
    )


def _find_shipment(collection, id_field, shipment_id, sample):
    """Locate a shipment document by its id/reference (multiple attempts)."""
    target = str(shipment_id).strip()

    # Exact string match first.
    doc = collection.find_one({id_field: target})
    if doc:
        return doc

    num_value = _as_number(target)
    if num_value is not None:
        doc = collection.find_one({id_field: num_value})
        if doc:
            return doc

    # ObjectId match (when the reference targets a Mongo ObjectId field).
    try:
        from bson import ObjectId  # type: ignore

        if ObjectId.is_valid(target):
            for query in ({id_field: ObjectId(target)}, {"_id": ObjectId(target)}):
                doc = collection.find_one(query)
                if doc:
                    return doc
    except Exception:
        pass

    return None


def _as_number(value):
    try:
        if "." in value:
            return float(value)
        return int(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Public connector object
# ---------------------------------------------------------------------------
class LogisticsConnector:
    """Injected database + schema wrapper that owns the three capabilities.

    ``db`` is any read-only database-like object exposing ``get_collection`` /
    ``__getitem__`` / ``list_collection_names`` and whose returned collections
    expose ``find`` / ``find_one``. In production it is built from
    :func:`make_read_only_connection`. In tests it is a non-secret in-memory
    fake, so no production credential is required.
    """

    def __init__(self, db, schema, scan_limit=DEFAULT_SCAN_LIMIT):
        self.db = db
        self.schema = schema
        self.scan_limit = scan_limit

    def today_work(self, target_date: datetime.date) -> dict:
        return today_work(self, target_date)

    def freight_rate_lookup(self, origin, destination, container, date=None) -> dict:
        return freight_rate_lookup(self, origin, destination, container, date=date)

    def shipment_status(self, shipment_id) -> dict:
        return shipment_status(self, shipment_id)


# ---------------------------------------------------------------------------
# Convenience helper used by tool handlers / tests
# ---------------------------------------------------------------------------
def default_schema_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))
