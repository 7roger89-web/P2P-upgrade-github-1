"""Read-only MongoDB connector for the Logistics (logistics-work-desk) datastore.

READ-ONLY ENFORCEMENT (by design, not by convention):
  * The public surface is exactly ``find`` / ``find_one`` / ``close`` plus the
    ``allowed_collections`` property. There is no insert, update, delete,
    replace, drop, createIndex, bulk write, aggregate, or any other method.
  * Only the three allowlisted collections (shipments, tasks, rate_cards) can
    be queried; anything else raises ``LogisticsReadOnlyError``.
  * Only the two read primitives are ever invoked on the underlying pymongo
    collection objects (``find`` / ``find_one``), with dict filters, optional
    projection, bounded sort and clamped limit.
  * The deployment must additionally supply a MongoDB credential that only has
    read privileges on the Logistics database (LOGISTICS_MONGO_URI_READONLY).

pymongo is imported lazily so plugin registration never requires it and the
module stays importable in test environments without the dependency.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import contracts

# Bounded timeouts so a tool call can never hang an agent turn on an
# unreachable MongoDB server.
_CLIENT_OPTIONS = {
    "serverSelectionTimeoutMS": 5000,
    "connectTimeoutMS": 5000,
    "socketTimeoutMS": 15000,
}

MAX_LIMIT = 200
_MIN_LIMIT = 1


class LogisticsReadOnlyError(Exception):
    """Base error for the Logistics read-only connector."""


class LogisticsConfigError(LogisticsReadOnlyError):
    """Required environment variables are not set."""

    def __init__(self, message: str, required_env: Sequence[str]):
        super().__init__(message)
        self.required_env = list(required_env)


class LogisticsDependencyError(LogisticsReadOnlyError):
    """pymongo is unavailable in this runtime."""


class LogisticsReadOnlyClient:
    """Allowlisted find/find_one-only view over the Logistics MongoDB."""

    def __init__(self, uri: str, db_name: str, *, client_factory: Optional[Callable[..., Any]] = None):
        if not uri or not str(uri).strip():
            raise LogisticsConfigError("Logistics MongoDB URI is empty.", contracts.REQUIRED_ENV_VARS)
        if not db_name or not str(db_name).strip():
            raise LogisticsConfigError("Logistics MongoDB database name is empty.", contracts.REQUIRED_ENV_VARS)
        self._uri = str(uri)
        self._db_name = str(db_name)
        factory = client_factory or _default_client_factory
        # The raw client handle is deliberately private; nothing public exposes it.
        self._client = factory(self._uri, **dict(_CLIENT_OPTIONS))

    # -- configuration surface ------------------------------------------------
    @property
    def allowed_collections(self) -> Tuple[str, ...]:
        return tuple(contracts.ALLOWED_COLLECTIONS)

    @property
    def db_name(self) -> str:
        return self._db_name

    # -- read surface (the ONLY data access) ----------------------------------
    def find(
        self,
        collection: str,
        filter: Optional[dict] = None,
        *,
        projection: Optional[dict] = None,
        sort: Optional[Sequence[Tuple[str, int]]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        coll = self._readable_collection(collection)
        filter = _validate_filter(filter)
        projection = _validate_projection(projection)
        sort = _validate_sort(sort)
        limit = _validate_limit(limit, default=MAX_LIMIT)
        cursor = coll.find(filter, projection=projection, sort=sort, limit=limit)
        return [dict(doc) for doc in cursor]

    def find_one(
        self,
        collection: str,
        filter: Optional[dict] = None,
        *,
        projection: Optional[dict] = None,
    ) -> Optional[Dict[str, Any]]:
        coll = self._readable_collection(collection)
        filter = _validate_filter(filter)
        projection = _validate_projection(projection)
        doc = coll.find_one(filter, projection=projection)
        return dict(doc) if doc is not None else None

    def close(self) -> None:
        closer = getattr(self._client, "close", None)
        if callable(closer):
            closer()

    # -- internals -------------------------------------------------------------
    def _readable_collection(self, collection: str):
        if collection not in contracts.ALLOWED_COLLECTIONS:
            raise LogisticsReadOnlyError(
                f"Collection {collection!r} is not in the Logistics read allowlist "
                f"{list(contracts.ALLOWED_COLLECTIONS)}."
            )
        return self._client[self._db_name][collection]


def _default_client_factory(uri: str, **options: Any) -> Any:
    try:
        from pymongo import MongoClient  # lazy: registration and tests never need it
    except ImportError as exc:
        raise LogisticsDependencyError(
            "pymongo is not installed in this Hermes image. "
            "Add it to deployments/hermes-dockhosting/Dockerfile (ARG PYMONGO_VERSION)."
        ) from exc
    return MongoClient(uri, **options)


def connect_from_env(env: Optional[Dict[str, str]] = None) -> LogisticsReadOnlyClient:
    """Build a client from LOGISTICS_MONGO_URI_READONLY / LOGISTICS_MONGO_DB_NAME."""
    import os

    source = env if env is not None else os.environ
    uri = source.get(contracts.MONGO_URI_ENV, "") or ""
    db_name = source.get(contracts.MONGO_DB_NAME_ENV, "") or ""
    missing = [
        name
        for name, value in (
            (contracts.MONGO_URI_ENV, uri),
            (contracts.MONGO_DB_NAME_ENV, db_name),
        )
        if not str(value).strip()
    ]
    if missing:
        raise LogisticsConfigError(
            "Logistics read-only MongoDB is not configured.", missing
        )
    return LogisticsReadOnlyClient(uri.strip(), db_name.strip())


# --------------------------------------------------------------------------
# Argument validation (fail closed on anything unexpected)
# --------------------------------------------------------------------------

def _validate_filter(filter: Optional[dict]) -> dict:
    if filter is None:
        return {}
    if not isinstance(filter, dict):
        raise LogisticsReadOnlyError("Filter must be a dict.")
    for key, value in filter.items():
        if not isinstance(key, str) or not key:
            raise LogisticsReadOnlyError("Filter keys must be non-empty strings.")
        if key.startswith("$"):
            raise LogisticsReadOnlyError(
                f"Top-level query operator {key!r} is not permitted; only plain field matches are supported."
            )
        if isinstance(value, dict) and any(k.startswith("$") for k in value):

            allowed = {"$ne"}
            bad = sorted(set(value) - allowed)
            if bad:
                raise LogisticsReadOnlyError(
                    f"Filter operator(s) {bad} are not permitted; only {sorted(allowed)} are supported."
                )
    return filter


def _validate_projection(projection: Optional[dict]) -> Optional[dict]:
    if projection is None:
        return None
    if not isinstance(projection, dict):
        raise LogisticsReadOnlyError("Projection must be a dict.")
    return projection


def _validate_sort(sort: Optional[Sequence[Tuple[str, int]]]) -> Optional[list]:
    if sort is None:
        return None
    if not isinstance(sort, (list, tuple)):
        raise LogisticsReadOnlyError("Sort must be a list of (field, 1|-1) pairs.")
    cleaned = []
    for item in sort:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise LogisticsReadOnlyError("Sort must be a list of (field, 1|-1) pairs.")
        field, direction = item
        if not isinstance(field, str) or not field:
            raise LogisticsReadOnlyError("Sort field must be a non-empty string.")
        if direction not in (1, -1):
            raise LogisticsReadOnlyError("Sort direction must be 1 or -1.")
        cleaned.append((field, direction))
    return cleaned or None


def _validate_limit(limit: Optional[int], *, default: int) -> int:
    if limit is None:
        return default
    try:
        value = int(limit)
    except (TypeError, ValueError):
        raise LogisticsReadOnlyError("Limit must be an integer.")
    return max(_MIN_LIMIT, min(value, MAX_LIMIT))


# --------------------------------------------------------------------------
# Secret hygiene: never let the URI (which may embed a password) leak into
# tool output through exception text.
# --------------------------------------------------------------------------

def sanitize_error_text(text: str, uri: str) -> str:
    cleaned = str(text)
    if uri:
        cleaned = cleaned.replace(uri, "***LOGISTICS_MONGO_URI_READONLY***")
        # Also mask user:password@ fragments in case the driver reformats the URI.
        import re

        cleaned = re.sub(
            r"(\w+://[^/@:\s]+):([^@/\s]+)@", r"\1:***@", cleaned
        )
    return cleaned


def iso_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
