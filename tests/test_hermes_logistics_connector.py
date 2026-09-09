"""Focused, non-secret tests for the read-only Logistics connector.

These tests never require a production credential: they use an in-memory fake
MongoDB that mimics the read-only surface used by ``connector.LogisticsConnector``
(``list_collection_names``, ``find``, ``find_one``). They cover:

* TODAY_WORK: target-day match, unrelated-day exclusion, no-data case
* FREIGHT_RATE_LOOKUP: exact route+container, most recent value, NOT_FOUND,
  ambiguous (never silently wrong)
* SHIPMENT_STATUS: exact id, unknown id NOT_FOUND
* READ-ONLY SAFETY: write operations raise, no credential required
* SECRET SAFETY: no credentials present in the repository tree
"""

import datetime
import importlib.util
import re
import sys
from pathlib import Path

import pytest

PLUGIN_DIR = (
    Path(__file__).resolve().parent.parent
    / "deployments"
    / "hermes-dockhosting"
    / "plugins"
    / "hermes-logistics"
)
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

import connector  # noqa: E402

SCHEMA_PATH = str(PLUGIN_DIR / "schema.yaml")
SCHEMA = connector.load_schema(SCHEMA_PATH)


# ---------------------------------------------------------------------------
# In-memory fake MongoDB (read-only surface used by the connector)
# ---------------------------------------------------------------------------
def _norm_cmp(value):
    if isinstance(value, datetime.datetime):
        return value.date()
    return value


class _FakeCursor(list):
    def limit(self, n):
        return _FakeCursor(self[:n])

    def sort(self, *a, **k):
        return self


def _match(doc, filt):
    if not filt:
        return True
    for field, expected in filt.items():
        if not isinstance(expected, dict):
            if doc.get(field) != expected:
                return False
            continue
        # operator filters: $gte/$lte/$gt/$lt/$ne/$in/$exists
        val = doc.get(field)
        for op, operand in expected.items():
            if op == "$exists":
                if (field in doc) != operand:
                    return False
            elif op == "$in":
                if val not in operand:
                    return False
            elif op == "$ne":
                if _norm_cmp(val) == _norm_cmp(operand):
                    return False
            elif op == "$gte":
                if not (_norm_cmp(val) >= _norm_cmp(operand)):
                    return False
            elif op == "$lte":
                if not (_norm_cmp(val) <= _norm_cmp(operand)):
                    return False
            elif op == "$gt":
                if not (_norm_cmp(val) > _norm_cmp(operand)):
                    return False
            elif op == "$lt":
                if not (_norm_cmp(val) < _norm_cmp(operand)):
                    return False
            else:
                raise AssertionError(f"unsupported fake op {op}")
    return True


class _FakeCollection:
    def __init__(self, name, docs):
        self.name = name
        self.docs = docs

    def find(self, filt=None, *a, **k):
        filt = filt or {}
        return _FakeCursor([d for d in self.docs if _match(d, filt)])

    def find_one(self, filt=None, *a, **k):
        filt = filt or {}
        for d in self.docs:
            if _match(d, filt):
                return d
        return None

    def count_documents(self, filt=None, *a, **k):
        return len(self._docs_for(filt or {}))

    def _docs_for(self, filt):
        return [d for d in self.docs if _match(d, filt)]

    def aggregate(self, *a, **k):
        raise NotImplementedError

    def distinct(self, key, *a, **k):
        return list({d.get(key) for d in self.docs if d.get(key) is not None})

    def estimated_document_count(self, *a, **k):
        return len(self.docs)


class _FakeDatabase:
    def __init__(self, collections):
        self._collections = collections

    def list_collection_names(self):
        return list(self._collections.keys())

    def get_collection(self, name):
        return self._collections[name]

    def __getitem__(self, name):
        return self._collections[name]


def _make_db(shipments=(), rate_cards=(), review_queue=()):
    cols = {}
    if shipments:
        cols["shipments"] = _FakeCollection("shipments", list(shipments))
    if rate_cards:
        cols["rate_cards"] = _FakeCollection("rate_cards", list(rate_cards))
    if review_queue:
        cols["review_queue"] = _FakeCollection("review_queue", list(review_queue))
    return _FakeDatabase(cols)


# ---------------------------------------------------------------------------
# TODAY_WORK
# ---------------------------------------------------------------------------
def test_today_work_returns_item_for_target_date():
    day = datetime.date(2026, 9, 9)
    db = _make_db(
        shipments=[
            {"_id": 1, "shipment_id": "LOHANG-001", "date": day, "status": "Đang về kho", "title": "Giao Hà Nội"},
            {"_id": 2, "shipment_id": "LOHANG-002", "date": datetime.date(2026, 9, 10), "status": "Chờ hàng"},
        ]
    )
    conn = connector.LogisticsConnector(db, SCHEMA)
    result = conn.today_work(day)

    assert result["status"] == "FOUND"
    ids = [item["id"] for item in result["items"]]
    assert "LOHANG-001" in ids
    assert "LOHANG-002" not in ids  # unrelated date excluded
    assert result["date"] == "2026-09-09"
    assert result["source"].startswith("logistics_mongodb")


def test_today_work_excludes_unrelated_date():
    day = datetime.date(2026, 9, 9)
    db = _make_db(
        shipments=[
            {"_id": 1, "shipment_id": "LOHANG-003", "date": datetime.date(2026, 9, 11), "status": "Mới"},
        ]
    )
    conn = connector.LogisticsConnector(db, SCHEMA)
    result = conn.today_work(day)
    assert result["status"] == "NOT_FOUND"
    assert result["count"] == 0


def test_today_work_no_data_returns_not_found():
    db = _make_db()  # no collections at all
    conn = connector.LogisticsConnector(db, SCHEMA)
    result = conn.today_work(datetime.date(2026, 9, 9))
    assert result["status"] == "SCHEMA_UNVERIFIED"  # sources missing
    assert result["count"] == 0


# ---------------------------------------------------------------------------
# FREIGHT_RATE_LOOKUP
# ---------------------------------------------------------------------------
def test_freight_rate_exact_route_and_container():
    db = _make_db(
        rate_cards=[
            {
                "_id": 1,
                "origin": "Hải Phòng",
                "destination": "Hà Nội",
                "container_size": "20'",
                "rate": 4_500_000,
                "currency": "VND",
                "effective_date": datetime.date(2026, 9, 1),
            },
            {
                "_id": 2,
                "origin": "Hải Phòng",
                "destination": "Hà Nội",
                "container_size": "40'",
                "rate": 7_200_000,
                "currency": "VND",
                "effective_date": datetime.date(2026, 9, 1),
            },
        ]
    )
    conn = connector.LogisticsConnector(db, SCHEMA)
    result = conn.freight_rate_lookup("Hải Phòng", "Hà Nội", "20'")
    assert result["status"] == "FOUND"
    assert result["rate"] == 4_500_000
    assert result["currency"] == "VND"
    assert result["origin"] == "Hải Phòng"
    assert result["destination"] == "Hà Nội"
    assert result["container"] == "20'"


def test_freight_rate_most_recent_applicable_value():
    db = _make_db(
        rate_cards=[
            {"_id": 1, "origin": "Hải Phòng", "destination": "Hà Nội", "container_size": "20'",
             "rate": 5_000_000, "currency": "VND", "effective_date": datetime.date(2026, 8, 15)},
            {"_id": 2, "origin": "Hải Phòng", "destination": "Hà Nội", "container_size": "20'",
             "rate": 4_500_000, "currency": "VND", "effective_date": datetime.date(2026, 9, 1)},
        ]
    )
    conn = connector.LogisticsConnector(db, SCHEMA)
    result = conn.freight_rate_lookup("Hải Phòng", "Hà Nội", "20'")
    assert result["status"] == "FOUND"
    assert result["rate"] == 4_500_000  # most recent (2026-09-01) wins
    assert result["effective_date"] == "2026-09-01"


def test_freight_rate_respects_requested_date():
    db = _make_db(
        rate_cards=[
            {"_id": 1, "origin": "Hải Phòng", "destination": "Hà Nội", "container_size": "20'",
             "rate": 4_000_000, "currency": "VND", "effective_date": datetime.date(2026, 7, 1)},
            {"_id": 2, "origin": "Hải Phòng", "destination": "Hà Nội", "container_size": "20'",
             "rate": 4_500_000, "currency": "VND", "effective_date": datetime.date(2026, 9, 1)},
        ]
    )
    conn = connector.LogisticsConnector(db, SCHEMA)
    # On 2026-08-15 the September rate is not yet in effect -> July rate applies.
    result = conn.freight_rate_lookup("Hải Phòng", "Hà Nội", "20'", date="2026-08-15")
    assert result["status"] == "FOUND"
    assert result["rate"] == 4_000_000
    # On 2026-09-10 the September rate applies.
    result2 = conn.freight_rate_lookup("Hải Phòng", "Hà Nội", "20'", date="2026-09-10")
    assert result2["rate"] == 4_500_000


def test_freight_rate_not_found():
    db = _make_db(
        rate_cards=[
            {"_id": 1, "origin": "Đà Nẵng", "destination": "Huế", "container_size": "20'",
             "rate": 2_000_000, "currency": "VND", "effective_date": datetime.date(2026, 9, 1)},
        ]
    )
    conn = connector.LogisticsConnector(db, SCHEMA)
    result = conn.freight_rate_lookup("Hải Phòng", "Hà Nội", "20'")
    assert result["status"] == "NOT_FOUND"
    assert result["rate"] is None


def test_freight_rate_ambiguous_does_not_pick_wrong_rate():
    db = _make_db(
        rate_cards=[
            {"_id": 1, "origin": "Hải Phòng", "destination": "Hà Nội", "container_size": "20'",
             "rate": 4_500_000, "currency": "VND", "effective_date": datetime.date(2026, 9, 1)},
            {"_id": 2, "origin": "Hải Phòng", "destination": "Hà Nội", "container_size": "20'",
             "rate": 4_800_000, "currency": "VND", "effective_date": datetime.date(2026, 9, 1)},
        ]
    )
    conn = connector.LogisticsConnector(db, SCHEMA)
    result = conn.freight_rate_lookup("Hải Phòng", "Hà Nội", "20'")
    assert result["status"] == "AMBIGUOUS"
    assert result["rate"] is None  # never silently returns a wrong rate


# ---------------------------------------------------------------------------
# SHIPMENT_STATUS
# ---------------------------------------------------------------------------
def test_shipment_status_exact_id():
    db = _make_db(
        shipments=[
            {"_id": "a", "shipment_id": "LOHANG-100", "status": "Đang vận chuyển",
             "customer": "Công ty A", "updated_at": "2026-09-08T10:00:00"},
        ]
    )
    conn = connector.LogisticsConnector(db, SCHEMA)
    result = conn.shipment_status("LOHANG-100")
    assert result["status"] == "FOUND"
    assert result["shipment_reference"] == "LOHANG-100"
    assert result["current_status"] == "Đang vận chuyển"
    assert result["customer"] == "Công ty A"


def test_shipment_status_unknown_id_not_found():
    db = _make_db(
        shipments=[
            {"_id": "a", "shipment_id": "LOHANG-100", "status": "Đang vận chuyển"},
        ]
    )
    conn = connector.LogisticsConnector(db, SCHEMA)
    result = conn.shipment_status("LOHANG-NOPE")
    assert result["status"] == "NOT_FOUND"
    assert "message" in result


# ---------------------------------------------------------------------------
# READ-ONLY SAFETY
# ---------------------------------------------------------------------------
def test_readonly_connection_rejects_write_operations():
    from unittest import mock

    # Fake underlying pymongo-style objects.
    fake_collection = mock.MagicMock()
    fake_db = mock.MagicMock()
    fake_db.get_collection.return_value = fake_collection
    fake_client = mock.MagicMock()
    fake_client.get_database.return_value = fake_db
    fake_client.__getitem__.return_value = fake_db

    conn = connector.ReadOnlyClient(fake_client)
    db = conn.get_database("logistics")
    col = db.get_collection("shipments")

    # Reads are reachable.
    with mock.patch.object(col._collection, "find_one", return_value={}):
        assert col.find_one({}) == {}
    assert col.name  # property passthrough works

    # Writes are blocked.
    for op in ("insert_one", "update_one", "delete_one", "delete_many", "create_index", "drop"):
        with pytest.raises(connector.ReadOnlyViolation):
            getattr(col, op)


def test_connector_exposes_no_mutation_capabilities():
    # The public capabilities are exactly the three read-only functions.
    assert callable(connector.today_work)
    assert callable(connector.freight_rate_lookup)
    assert callable(connector.shipment_status)
    # No mutation helpers exist on the module surface.
    mutation_names = {
        name for name in dir(connector) if any(
            token in name.lower() for token in ("insert", "update", "delete", "drop", "create_index")
        )
    }
    assert not mutation_names


# ---------------------------------------------------------------------------
# HERMES PLUGIN WIRING
# ---------------------------------------------------------------------------
def test_plugin_registers_three_tools():
    # Load the plugin's __init__.py by file path (it uses plain sibling imports,
    # so it must be importable with the plugin dir on sys.path).
    init_file = PLUGIN_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location("hermes_logistics_plugin", init_file)
    plugin = importlib.util.module_from_spec(spec)
    sys.modules["hermes_logistics_plugin"] = plugin
    spec.loader.exec_module(plugin)

    registered = {}

    class FakeCtx:
        def register_tool(self, name, toolset, schema, handler):
            registered[name] = {"toolset": toolset, "schema": schema, "handler": handler}

    ctx = FakeCtx()
    plugin.register(ctx)

    assert set(registered) == {
        "logistics_today_work",
        "logistics_freight_rate_lookup",
        "logistics_shipment_status",
    }
    assert registered["logistics_today_work"]["toolset"] == "logistics"
    assert registered["logistics_freight_rate_lookup"]["schema"]["parameters"]["required"] == [
        "origin",
        "destination",
        "container",
    ]
    assert registered["logistics_shipment_status"]["schema"]["parameters"]["required"] == [
        "shipment_id",
    ]


# ---------------------------------------------------------------------------
# SECRET SAFETY
# ---------------------------------------------------------------------------
PLACEHOLDER_RE = re.compile(r"^[<{\[].*[>}\]]$|^x{3,}$|^\*+$|^\.\.\.$", re.I)


def _has_credential_uri(text):
    """A Mongo driver URI with embedded userinfo is a real credential.

    ``mongodb://user:pass@host`` or ``mongodb+srv://user:pass@host`` — the part
    before ``@`` holds credentials. Env-var *names* like
    ``LOGISTICS_MONGO_URI_READONLY`` never match this.
    """
    import re

    return re.search(r"mongodb(\+srv)?://[^\s\"'<>]+@[^\s\"'<>]+", text) is not None


def _has_secret_assignment(text):
    """A ``password``/``token``/``key``/``secret`` set to a non-placeholder value."""
    import re

    for m in re.finditer(
        r"(?i)\b(?:password|passwd|api[_-]?key|secret|auth_token|bot_token|access_key)\b"
        r"\s*[=:]\s*[\"']?([^\s\"'#,}]+)",
        text,
    ):
        value = m.group(1)
        if value and not PLACEHOLDER_RE.match(value.strip()):
            return True
    return False


def test_no_mongo_credentials_committed():
    repo_root = Path(__file__).resolve().parent.parent
    # Scan only the files added/changed by this integration. Exclude the test
    # file itself (it contains the scanner needles as literals).
    body_files = [
        PLUGIN_DIR / "connector.py",
        PLUGIN_DIR / "schema.yaml",
        PLUGIN_DIR / "schemas.py",
        PLUGIN_DIR / "tools.py",
        PLUGIN_DIR / "__init__.py",
        PLUGIN_DIR / "plugin.yaml",
        PLUGIN_DIR / "requirements.txt",
        PLUGIN_DIR / "README.md",
        repo_root / "deployments/hermes-dockhosting/Dockerfile",
        repo_root / "deployments/hermes-dockhosting/dockhosting-entrypoint.sh",
        repo_root / "deployments/hermes-dockhosting/README.md",
    ]
    bad = []
    scanned = 0
    for path in body_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        if _has_credential_uri(text):
            bad.append((str(path.relative_to(repo_root)), "credential_uri"))
        if _has_secret_assignment(text):
            bad.append((str(path.relative_to(repo_root)), "secret_assignment"))

    # The connector must read the URI/db name from the environment, never
    # hard-code them. The env reads live in tools.py; the connector accepts a
    # read-only connection as a parameter.
    tools_src = (PLUGIN_DIR / "tools.py").read_text(encoding="utf-8")
    assert "LOGISTICS_MONGO_URI_READONLY" in tools_src
    assert "LOGISTICS_MONGO_DB_NAME" in tools_src
    assert "os.environ.get" in tools_src
    connector_src = (PLUGIN_DIR / "connector.py").read_text(encoding="utf-8")
    assert "mongodb+srv://" not in connector_src
    assert "mongodb://" not in connector_src

    assert scanned == len(body_files), "did not scan all touched files"
    assert not bad, f"possible credential material committed: {bad}"
