"""Focused non-secret tests for the Hermes Logistics read-only integration
(HERMES_LOGISTICS_READONLY_001).

Covers:
  1. TODAY_WORK — relevant item for target date returned, unrelated date
     excluded, done/deleted excluded, no-data case, undated handling.
  2. FREIGHT_RATE_LOOKUP — fail-closed with the VERIFIED finding
     RATE_CARD_SCHEMA_INSUFFICIENT_FOR_STRUCTURED_ROUTE_LOOKUP (never a
     guessed rate, no heuristic route_name parsing), NOT_FOUND when empty,
     config-missing envelope.
  3. SHIPMENT_STATUS — exact id returns correct state, status fallback via
     data["0.0"]["st"], unknown id NOT_FOUND, deleted/archived handling,
     financial payload never exposed, ambiguous multi-match.
  4. READ-ONLY SAFETY — public surface is find/find_one only, collection
     allowlist, limit clamping, filter/sort validation, and the fake client
     records no mutation-method access from any tool call.
  5. SECRET SAFETY — no Mongo credentials committed in the integration files,
     error envelopes never leak the URI.

No production credential is required: all data access runs against an
in-memory fake that mirrors the exact pymongo primitives the connector uses
(find / find_one with filter / projection / sort / limit).
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "deployments" / "hermes-dockhosting" / "plugins" / "logistics"
DEPLOYMENT_DIR = REPO_ROOT / "deployments" / "hermes-dockhosting"

if str(DEPLOYMENT_DIR) not in sys.path:  # not needed at runtime, kept for clarity
    pass


# ---------------------------------------------------------------------------
# Load the plugin package the same way the Hermes plugin loader does
# (package spec with submodule search locations; relative imports resolve).
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def plugin():
    spec = importlib.util.spec_from_file_location(
        "hermes_test_logistics",
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# In-memory read-only fake of the pymongo surface the connector uses
# ---------------------------------------------------------------------------


class AccessLog:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, str]] = []
        self.violations: List[str] = []

    def record(self, collection: str, method: str) -> None:
        self.calls.append((collection, method))

    def record_violation(self, collection: str, attribute: str) -> None:
        self.violations.append(f"{collection}.{attribute}")


def _matches(doc: dict, flt: dict) -> bool:
    for key, value in flt.items():
        if isinstance(value, dict) and "$ne" in value:
            if key in doc and doc[key] == value["$ne"]:
                return False
        else:
            if key not in doc or doc[key] != value:
                return False
    return True


def _sort_docs(docs: list, sort: list) -> list:
    out = list(docs)
    for field, direction in reversed(sort):
        out = sorted(
            out,
            key=lambda d: (d.get(field) is not None, d.get(field)),
            reverse=(direction == -1),
        )
    return out


class FakeCollection:
    """Implements ONLY the read primitives; any other attribute access is a
    recorded read-only violation and raises (so a mutation attempt can never
    succeed silently)."""

    def __init__(self, name: str, docs: list, log: AccessLog) -> None:
        self._name = name
        self._docs = docs
        self._log = log

    def find(self, filter=None, projection=None, sort=None, limit=0, **kwargs):
        self._log.record(self._name, "find")
        matched = [d for d in self._docs if _matches(d, filter or {})]
        if sort:
            matched = _sort_docs(matched, list(sort))
        if limit:
            matched = matched[:limit]
        return list(matched)

    def find_one(self, filter=None, projection=None, **kwargs):
        self._log.record(self._name, "find_one")
        for d in self._docs:
            if _matches(d, filter or {}):
                return dict(d)
        return None

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        self._log.record_violation(self._name, name)
        raise AttributeError(f"read-only violation attempt: {self._name}.{name}")


class FakeDatabase:
    def __init__(self, collections: Dict[str, list], log: AccessLog) -> None:
        self._collections = collections
        self._log = log

    def __getitem__(self, name: str) -> FakeCollection:
        return FakeCollection(name, self._collections.get(name, []), self._log)


class FakeMongoClient:
    def __init__(self, collections: Dict[str, list], log: AccessLog) -> None:
        self._collections = collections
        self._log = log
        self.closed = False

    def __getitem__(self, db_name: str) -> FakeDatabase:
        self._log.record(f"<db:{db_name}>", "get_collection")
        return FakeDatabase(self._collections, self._log)

    def close(self):
        self.closed = True


def fake_factory(collections: Dict[str, list], log: Optional[AccessLog] = None):
    log = log or AccessLog()

    def _factory(uri: str, **options: Any) -> FakeMongoClient:
        return FakeMongoClient(collections, log)

    return _factory, log


# ---------------------------------------------------------------------------
# Fixture data (shapes follow the observed logistics-work-desk contracts)
# ---------------------------------------------------------------------------

TODAY = dt.date(2026, 9, 9)


def _tasks_docs() -> list:
    return [
        {
            "task_id": "T-001",
            "content": "Chuẩn bị hồ sơ hải quan cho lô LK-1024",
            "assignee": "Minh",
            "assignee_user_id": "u-1",
            "deadline": dt.datetime(2026, 9, 9, 10, 0),
            "done": False,
            "created_at": dt.datetime(2026, 9, 7, 8, 0),
        },
        {
            "task_id": "T-002",
            "content": "Xác nhận booking với hãng tàu",
            "assignee": "Lan",
            "deadline": "09/09/2026",
            "done": False,
            "created_at": dt.datetime(2026, 9, 6, 9, 0),
        },
        {
            "task_id": "T-003",
            "content": "Việc của ngày mai",
            "assignee": "Minh",
            "deadline": dt.datetime(2026, 9, 10, 9, 0),
            "done": False,
            "created_at": dt.datetime(2026, 9, 6, 9, 0),
        },
        {
            "task_id": "T-004",
            "content": "Việc đã xong hôm nay",
            "assignee": "Minh",
            "deadline": dt.datetime(2026, 9, 9, 15, 0),
            "done": True,
            "created_at": dt.datetime(2026, 9, 5, 9, 0),
        },
        {
            "task_id": "T-005",
            "content": "Việc đã bị xóa",
            "assignee": "Minh",
            "deadline": dt.datetime(2026, 9, 9, 16, 0),
            "done": False,
            "is_deleted": True,
            "created_at": dt.datetime(2026, 9, 5, 9, 0),
        },
        {
            "task_id": "T-006",
            "content": "Việc chưa rõ hạn",
            "assignee": "Minh",
            "done": False,
            "created_at": dt.datetime(2026, 9, 4, 9, 0),
        },
    ]


def _shipments_docs() -> list:
    base_data = {
        "0.0": {"st": "in_transit", "mode": "sea", "incoterm": "FOB"},
        "1.2": {"booking_no": "BK-77", "mbl": "MBOL-88"},
        "2.4": {"customs_status": "cleared"},
        "2.7": {"is_delivered": False},
        "3.4": {"revenue_vnd": 999_999_999, "cost_vnd": 123_456_789},
    }
    return [
        {
            "id": "LK-1024",
            "shipment_id": "LK-1024",
            "customer": "Công ty ABC",
            "status": "in_transit",
            "version": 3,
            "created_at": dt.datetime(2026, 8, 30, 8, 0),
            "updated_at": dt.datetime(2026, 9, 8, 16, 0),
            "data": dict(base_data),
        },
        {
            "id": "LK-2000",
            "client": "Công ty XYZ",
            "version": 1,
            "created_at": dt.datetime(2026, 9, 1, 8, 0),
            "updated_at": dt.datetime(2026, 9, 2, 10, 0),
            "data": {"0.0": {"st": "pending_customs"}},
        },
        {
            "id": "LK-3000",
            "status": "delivered",
            "is_archived": True,
            "updated_at": dt.datetime(2026, 8, 1, 8, 0),
            "data": {"0.0": {"st": "delivered"}},
        },
        {
            "id": "LK-4000",
            "status": "cancelled",
            "is_deleted": True,
            "data": {"0.0": {"st": "cancelled"}},
        },
        {
            "id": "LK-5000",
            "status": "draft",
            "updated_at": dt.datetime(2026, 9, 3, 8, 0),
            "data": {"0.0": {"st": "draft"}},
        },
        {
            "id": "LK-5000",
            "status": "confirmed",
            "version": 2,
            "updated_at": dt.datetime(2026, 9, 4, 8, 0),
            "data": {"0.0": {"st": "confirmed"}},
        },
    ]


def _rate_cards_docs() -> list:
    # VERIFIED persisted shape (logistics-work-desk views/sales.py): id,
    # customer, route_name (free text), history[{month, total_cost,
    # total_price, profit, details[{name, cost, price}], updated_at}].
    # Values are realistic, but the tool must refuse to return any of them
    # as a rate while the schema has no structured route/equipment/currency
    # fields.
    return [
        {
            "id": "RC-1",
            "customer": "Công ty ABC",
            "route_name": "Hải Phòng - Hà Nội (Cont 40)",
            "history": [
                {
                    "month": "09/2026",
                    "total_cost": 3_500_000,
                    "total_price": 4_500_000,
                    "profit": 1_000_000,
                    "details": [{"name": "Vận chuyển", "cost": 3_500_000, "price": 4_500_000}],
                    "updated_at": "2026-09-01",
                }
            ],
            "is_deleted": False,
        },
        {"id": "RC-2", "customer": "x", "route_name": "y", "history": [], "is_deleted": True},
    ]


def _all_collections() -> Dict[str, list]:
    return {
        "tasks": _tasks_docs(),
        "shipments": _shipments_docs(),
        "rate_cards": _rate_cards_docs(),
    }


# ---------------------------------------------------------------------------
# Helpers to run handlers against the fake
# ---------------------------------------------------------------------------


@pytest.fixture()
def run_tool(plugin, monkeypatch):
    """Run a plugin handler with the fake Mongo injected via connect_from_env."""

    def _run(handler_name: str, args: Optional[dict], collections=None, log: Optional[AccessLog] = None):
        factory, log = fake_factory(collections if collections is not None else _all_collections(), log)
        monkeypatch.setenv("LOGISTICS_MONGO_URI_READONLY", "mongodb://ro:PLACEHOLDER@db.example.invalid/logistics")
        monkeypatch.setenv("LOGISTICS_MONGO_DB_NAME", "logistics_test")
        monkeypatch.setattr(plugin.tools, "connect_from_env", lambda: plugin.connector.LogisticsReadOnlyClient(
            "mongodb://ro:PLACEHOLDER@db.example.invalid/logistics", "logistics_test", client_factory=factory
        ))
        out = getattr(plugin.tools, handler_name)(args or {})
        return json.loads(out), log

    return _run


# ===========================================================================
# 1. TODAY_WORK
# ===========================================================================


class TestTodayWork:
    def test_relevant_items_for_target_date_returned(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-09"})
        assert result["status"] == "OK"
        refs = {i["ref"] for i in result["items"]}
        assert refs == {"T-001", "T-002"}
        item = next(i for i in result["items"] if i["ref"] == "T-001")
        assert item["due"] == "2026-09-09"
        assert item["kind"] == "TASK"
        assert item["source"] == "tasks"
        assert item["action"].startswith("Chuẩn bị hồ sơ")

    def test_unrelated_date_excluded(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-10"})
        assert result["status"] == "OK"
        assert [i["ref"] for i in result["items"]] == ["T-003"]

    def test_done_and_deleted_excluded(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-09"})
        refs = {i["ref"] for i in result["items"]}
        assert "T-004" not in refs  # done == True
        assert "T-005" not in refs  # is_deleted == True

    def test_no_data_case_returns_not_found(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-09"}, collections={"tasks": []})
        assert result["status"] == "NOT_FOUND"
        assert result["items"] == []
        assert "2026-09-09" in result["note"]

    def test_undated_skipped_by_default_but_counted(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-09"})
        assert all(i["ref"] != "T-006" for i in result["items"])
        assert result["counts"]["open_undated"] == 1

    def test_include_undated_appends_undated(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-11", "include_undated": True})
        refs = {i["ref"] for i in result["items"]}
        assert "T-006" in refs
        assert "T-003" not in refs  # deadline is 2026-09-10, not the 11th

    def test_default_date_uses_hcm_today(self, run_tool, plugin):
        result, _ = run_tool("handle_today_work", {"date": None})
        today = plugin.contracts.hcm_today().isoformat()
        assert result["date"] == today
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", result["date"])
        assert "Asia/Ho_Chi_Minh" in result["timezone"]
        # Whatever the real clock says, only items actually due that day appear.
        assert all(i.get("due") == today for i in result["items"])

    def test_assignee_filter(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-09", "assignee": "Lan"})
        assert [i["ref"] for i in result["items"]] == ["T-002"]

    def test_bad_date_is_bad_request(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "09/09/2026"})
        assert result["error_type"] == "logistics_bad_request"

    # -- explicit ASSIGNEE vs TEAM scope (no identity service in this task) --

    def test_team_scope_by_default(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-09"})
        assert result["scope"] == "TEAM"
        assert "scope_value" not in result
        assert "No personal assignee identity was supplied" in result["note"]
        assert "whole team" in result["note"]

    def test_assignee_scope_when_filtered_by_name(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-09", "assignee": "Lan"})
        assert result["scope"] == "ASSIGNEE"
        assert result["scope_value"] == "Lan"
        assert "No personal assignee" not in (result.get("note") or "")

    def test_assignee_scope_when_filtered_by_user_id(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-09", "assignee_user_id": "u-1"})
        assert result["scope"] == "ASSIGNEE"
        assert result["scope_value"] == "u-1"
        assert [i["ref"] for i in result["items"]] == ["T-001"]

    def test_assignee_scope_with_both_identity_parts(self, run_tool):
        result, _ = run_tool("handle_today_work", {
            "date": "2026-09-09", "assignee": "Minh", "assignee_user_id": "u-1"
        })
        assert result["scope"] == "ASSIGNEE"
        assert result["scope_value"] == "Minh (u-1)"

    def test_team_scope_note_present_also_on_not_found(self, run_tool):
        result, _ = run_tool("handle_today_work", {"date": "2026-09-09"}, collections={"tasks": []})
        assert result["scope"] == "TEAM"
        assert result["status"] == "NOT_FOUND"
        assert "No personal assignee identity was supplied" in result["note"]
        assert "Không có việc nào" in result["note"]


# ===========================================================================
# 2. FREIGHT_RATE_LOOKUP (fail closed)
# ===========================================================================


class TestFreightRate:
    def test_fail_closed_verified_schema_insufficient_never_returns_a_rate(self, run_tool):
        result, _ = run_tool("handle_freight_rate", {
            "origin": "Hải Phòng", "destination": "Hà Nội", "container_size": "20'"
        })
        assert result["status"] == "RATE_CARD_SCHEMA_INSUFFICIENT_FOR_STRUCTURED_ROUTE_LOOKUP"
        # No guessed monetary value anywhere in the payload: none of the
        # fixture's realistic money figures may leak out as an answer.
        text = json.dumps(result)
        assert "rate" not in result
        assert "4500000" not in text
        assert "3500000" not in text
        assert "1000000" not in text
        # Verified schema findings are reported, not guessed-field wording.
        vs = result["verified_schema"]
        assert set(vs["structured_fields_absent"]) == {
            "origin", "destination", "container_or_equipment", "currency"
        }
        assert "route_name" in vs["top_level_fields"]
        assert "history" in vs["top_level_fields"]
        assert "free text" in vs["route_name"]
        assert "follow-up Logistics schema task" in result["reason"]
        assert "Không đoán giá" in result["note"]
        # Evidence from a real read-only sample query (is_deleted doc excluded).
        assert result["sample_size"] == 1
        assert "route_name" in result["observed_top_level_keys"]
        assert "history" in result["observed_top_level_keys"]

    def test_route_name_descriptive_text_not_parsed_as_structured(self, run_tool):
        # route_name contains "(Cont 40)" descriptive text — it must NOT be
        # treated as authoritative structured data, and route_name VALUES are
        # not even echoed (that would invite heuristic parsing by the model).
        result, _ = run_tool("handle_freight_rate", {
            "origin": "Hải Phòng", "destination": "Hà Nội", "container_size": "40"
        })
        assert result["status"] == "RATE_CARD_SCHEMA_INSUFFICIENT_FOR_STRUCTURED_ROUTE_LOOKUP"
        assert "Hải Phòng - Hà Nội (Cont 40)" not in json.dumps(result)

    def test_not_found_when_no_rate_cards(self, run_tool):
        result, _ = run_tool(
            "handle_freight_rate",
            {"origin": "Hải Phòng", "destination": "Hà Nội"},
            collections={"rate_cards": []},
        )
        assert result["status"] == "NOT_FOUND"

    def test_missing_required_args(self, run_tool):
        result, _ = run_tool("handle_freight_rate", {"origin": "Hải Phòng"})
        assert result["error_type"] == "logistics_bad_request"

    def test_config_missing_lists_required_env(self, plugin, monkeypatch):
        monkeypatch.delenv("LOGISTICS_MONGO_URI_READONLY", raising=False)
        monkeypatch.delenv("LOGISTICS_MONGO_DB_NAME", raising=False)
        out = json.loads(plugin.tools.handle_freight_rate({"origin": "a", "destination": "b"}))
        assert out["error_type"] == "logistics_config_missing"
        assert out["required_env"] == ["LOGISTICS_MONGO_URI_READONLY", "LOGISTICS_MONGO_DB_NAME"]

    def test_requested_echoed_with_provenance(self, run_tool):
        result, _ = run_tool("handle_freight_rate", {
            "origin": "Hải Phòng", "destination": "Hà Nội", "vehicle_type": "xe tải"
        })
        assert result["requested"]["origin"] == "Hải Phòng"
        assert result["source"] == "rate_cards"
        assert result["queried_at"]


# ===========================================================================
# 3. SHIPMENT_STATUS
# ===========================================================================


class TestShipmentStatus:
    def test_exact_id_returns_current_state(self, run_tool):
        result, _ = run_tool("handle_shipment_status", {"shipment_id": "LK-1024"})
        assert result["status"] == "OK"
        s = result["shipment"]
        assert s["id"] == "LK-1024"
        assert s["status"] == "in_transit"
        assert s["status_source"] == "status"
        assert s["customer"] == "Công ty ABC"
        assert s["mode"] == "sea"
        assert s["booking_no"] == "BK-77"
        assert s["mbl"] == "MBOL-88"
        assert s["customs_status"] == "cleared"
        assert s["is_delivered"] is False
        assert result["record_id"] == "LK-1024"
        assert result["source"] == "shipments"

    def test_status_fallback_via_data_section(self, run_tool):
        result, _ = run_tool("handle_shipment_status", {"shipment_id": "LK-2000"})
        assert result["status"] == "OK"
        s = result["shipment"]
        assert s["status"] == "pending_customs"
        assert s["status_source"] == 'data["0.0"]["st"]'
        assert s["customer"] == "Công ty XYZ"  # client mirror fallback

    def test_unknown_id_not_found(self, run_tool):
        result, _ = run_tool("handle_shipment_status", {"shipment_id": "NOPE-1"})
        assert result["status"] == "NOT_FOUND"

    def test_deleted_shipment_excluded(self, run_tool):
        result, _ = run_tool("handle_shipment_status", {"shipment_id": "LK-4000"})
        assert result["status"] == "NOT_FOUND"

    def test_archived_excluded_unless_requested(self, run_tool):
        assert run_tool("handle_shipment_status", {"shipment_id": "LK-3000"})[0]["status"] == "NOT_FOUND"
        result, _ = run_tool("handle_shipment_status", {"shipment_id": "LK-3000", "include_archived": True})
        assert result["status"] == "OK"
        assert result["shipment"]["status"] == "delivered"

    def test_financial_payload_never_exposed(self, run_tool):
        result, _ = run_tool("handle_shipment_status", {"shipment_id": "LK-1024"})
        text = json.dumps(result)
        assert "999999999" not in text
        assert "123456789" not in text
        assert "3.4" not in text
        assert "revenue" not in text

    def test_multiple_active_matches_are_ambiguous_not_guessed(self, run_tool):
        result, _ = run_tool("handle_shipment_status", {"shipment_id": "LK-5000"})
        assert result["status"] == "AMBIGUOUS"
        assert len(result["matched"]) == 2
        assert "shipment" not in result  # no shipment facts on ambiguity


# ===========================================================================
# 4. READ-ONLY SAFETY
# ===========================================================================


class TestReadOnlySafety:
    def test_connector_public_surface_is_read_only(self, plugin):
        import inspect

        cls = plugin.connector.LogisticsReadOnlyClient
        public = {
            name
            for name, member in inspect.getmembers(cls)
            if not name.startswith("_")
            and (inspect.isfunction(member) or isinstance(member, property))
        }
        assert public == {"find", "find_one", "close", "allowed_collections", "db_name"}

    def test_connector_source_has_no_mutation_calls(self):
        src = (PLUGIN_DIR / "connector.py").read_text(encoding="utf-8")
        mutations = (
            "insert_one", "insert_many", "update_one", "update_many", "replace_one",
            "replace_many", "delete_one", "delete_many", "drop", "drop_database",
            "drop_index", "create_index", "createIndex", "bulk_write", "aggregate",
            "map_reduce", "find_and_modify", "rename", "distinct", "count_documents",
            "watch", "with_options",
        )
        for m in mutations:
            assert not re.search(rf"\.{m}\s*\(", src), f"forbidden call .{m}() in connector.py"

    def test_collection_allowlist(self, plugin):
        factory, _ = fake_factory({"tasks": []})
        client = plugin.connector.LogisticsReadOnlyClient(
            "mongodb://ro:PLACEHOLDER@db.example.invalid/logistics", "logistics_test", client_factory=factory
        )
        assert set(client.allowed_collections) == {"shipments", "tasks", "rate_cards"}
        for bad in ("customers", "contracts", "audit_logs", "$cmd", "admin"):
            with pytest.raises(plugin.connector.LogisticsReadOnlyError):
                client.find(bad, {})
        client.find("tasks", {})  # allowlisted collections still work

    def test_limit_is_clamped(self, plugin):
        docs = [{"task_id": f"T-{i}", "created_at": dt.datetime(2026, 9, 1)} for i in range(300)]
        factory, _ = fake_factory({"tasks": docs})
        client = plugin.connector.LogisticsReadOnlyClient(
            "mongodb://ro:PLACEHOLDER@db.example.invalid/logistics", "logistics_test", client_factory=factory
        )
        assert len(client.find("tasks", {}, limit=999999)) == 200  # MAX_LIMIT
        assert len(client.find("tasks", {}, limit=-5)) == 1

    def test_invalid_filter_and_sort_rejected(self, plugin):
        factory, _ = fake_factory({"tasks": []})
        client = plugin.connector.LogisticsReadOnlyClient(
            "mongodb://ro:PLACEHOLDER@db.example.invalid/logistics", "logistics_test", client_factory=factory
        )
        with pytest.raises(plugin.connector.LogisticsReadOnlyError):
            client.find("tasks", "not-a-dict")
        with pytest.raises(plugin.connector.LogisticsReadOnlyError):
            client.find("tasks", {"$where": "1"})
        with pytest.raises(plugin.connector.LogisticsReadOnlyError):
            client.find("tasks", {"x": {"$gt": 1}})
        with pytest.raises(plugin.connector.LogisticsReadOnlyError):
            client.find("tasks", {}, sort=[("created_at", 2)])
        with pytest.raises(plugin.connector.LogisticsReadOnlyError):
            client.find_one("tasks", 42)

    def test_tools_only_use_read_primitives(self, run_tool):
        _, log = run_tool("handle_today_work", {"date": "2026-09-09"})
        _, log = run_tool("handle_freight_rate", {"origin": "a", "destination": "b"}, log=log)
        _, log = run_tool("handle_shipment_status", {"shipment_id": "LK-1024"}, log=log)
        assert log.violations == []
        methods = {method for _, method in log.calls}
        assert methods <= {"find", "find_one", "get_collection"}

    def test_config_error_names_env_vars(self, plugin, monkeypatch):
        monkeypatch.delenv("LOGISTICS_MONGO_URI_READONLY", raising=False)
        monkeypatch.setenv("LOGISTICS_MONGO_DB_NAME", "x")
        with pytest.raises(plugin.connector.LogisticsConfigError) as excinfo:
            plugin.connector.connect_from_env()
        assert excinfo.value.required_env == ["LOGISTICS_MONGO_URI_READONLY"]


# ===========================================================================
# 5. SECRET SAFETY
# ===========================================================================


class TestSecretSafety:
    def _integration_files(self):
        files = sorted(PLUGIN_DIR.glob("*.py")) + [PLUGIN_DIR / "plugin.yaml"]
        files += sorted(DEPLOYMENT_DIR.glob("README*.md"))
        files.append(DEPLOYMENT_DIR / "Dockerfile")
        return [f for f in files if f.is_file()]

    def test_no_credentials_committed(self):
        pattern = re.compile(r"mongodb(\+srv)?://[^\s<\"']+:(?!<)[^\s\"'<>]+@")
        for f in self._integration_files():
            text = f.read_text(encoding="utf-8")
            assert not pattern.search(text), f"possible credential in {f.name}: {pattern.search(text)}"

    def test_no_real_secret_values_in_files(self):
        for f in self._integration_files():
            text = f.read_text(encoding="utf-8")
            for token in ("SECRETPW", "PLACEHOLDER@db.example.invalid"):
                # PLACEHOLDER URI is allowed to appear only as a non-secret test constant,
                # never as a committed credential; SECRETPW must never appear at all.
                if token == "SECRETPW":
                    assert token not in text, f"secret token in {f.name}"

    def test_error_output_never_leaks_uri(self, plugin, monkeypatch):
        secret_uri = "mongodb://ro:SECRETPW@db.example.invalid/logistics"
        monkeypatch.setenv("LOGISTICS_MONGO_URI_READONLY", secret_uri)
        monkeypatch.setenv("LOGISTICS_MONGO_DB_NAME", "logistics_test")

        def exploding_factory(uri, **options):
            raise RuntimeError(f"dial failed: {uri}")

        monkeypatch.setattr(
            plugin.tools, "connect_from_env",
            lambda: plugin.connector.LogisticsReadOnlyClient(
                secret_uri, "logistics_test", client_factory=exploding_factory
            ),
        )
        out = json.loads(plugin.tools.handle_shipment_status({"shipment_id": "LK-1024"}))
        assert out["error_type"] == "logistics_connector_error"
        assert "SECRETPW" not in json.dumps(out)
        assert "***" in out["error"]

    def test_sanitize_error_text(self, plugin):
        cleaned = plugin.connector.sanitize_error_text(
            "boom at mongodb://u:hunter2@h/db", "mongodb://u:hunter2@h/db"
        )
        assert "hunter2" not in cleaned


# ===========================================================================
# Plugin registration contract
# ===========================================================================


class TestPluginContract:
    def test_manifest_matches_registered_tools(self, plugin):
        import yaml

        manifest = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text(encoding="utf-8"))
        assert manifest["name"] == "logistics"
        assert manifest["kind"] == "backend"  # bundled auto-load, like other bundled integrations
        assert manifest["requires_env"] == ["LOGISTICS_MONGO_URI_READONLY", "LOGISTICS_MONGO_DB_NAME"]
        assert sorted(manifest["provides_tools"]) == sorted(
            t["name"] for t in plugin.tools.TOOL_REGISTRATIONS
        )

    def test_register_registers_three_tools(self, plugin):
        recorded = []

        class FakeCtx:
            def register_tool(self, **spec):
                recorded.append(spec)

        plugin.register(FakeCtx())
        assert [s["name"] for s in recorded] == [
            "logistics_today_work", "logistics_freight_rate", "logistics_shipment_status"
        ]
        for spec in recorded:
            assert spec["toolset"] == "logistics"
            assert callable(spec["handler"])
            assert callable(spec["check_fn"])
            assert spec["requires_env"] == ["LOGISTICS_MONGO_URI_READONLY", "LOGISTICS_MONGO_DB_NAME"]
            schema = spec["schema"]
            assert schema["name"] == spec["name"]
            assert schema["description"]
            assert schema["parameters"]["type"] == "object"
            assert isinstance(schema["parameters"]["properties"], dict)

    def test_check_fn_gates_on_env(self, plugin, monkeypatch):
        monkeypatch.delenv("LOGISTICS_MONGO_URI_READONLY", raising=False)
        monkeypatch.delenv("LOGISTICS_MONGO_DB_NAME", raising=False)
        assert plugin.tools._check_logistics_configured() is False
        monkeypatch.setenv("LOGISTICS_MONGO_URI_READONLY", "mongodb://ro:PLACEHOLDER@db.example.invalid/logistics")
        assert plugin.tools._check_logistics_configured() is False
        monkeypatch.setenv("LOGISTICS_MONGO_DB_NAME", "logistics_test")
        assert plugin.tools._check_logistics_configured() is True

    def test_plugin_never_imports_pymongo_at_registration(self, plugin, monkeypatch):
        for name in [n for n in sys.modules if n == "pymongo" or n.startswith("pymongo.")]:
            monkeypatch.delitem(sys.modules, name)
        plugin.register(_RecordingCtx())
        assert not any(n == "pymongo" or n.startswith("pymongo.") for n in sys.modules)


class _RecordingCtx:
    def register_tool(self, **spec):
        return None


# ===========================================================================
# Real-driver smoke (no credential, no server): bounded failure against an
# unreachable localhost port must produce a clean sanitized envelope.
# ===========================================================================


class TestRealPymongoErrorPath:
    def test_unreachable_server_fails_cleanly(self, plugin, monkeypatch):
        pymongo = pytest.importorskip("pymongo")
        monkeypatch.setenv("LOGISTICS_MONGO_URI_READONLY", "mongodb://ro:SECRETPW@127.0.0.1:1/logistics")
        monkeypatch.setenv("LOGISTICS_MONGO_DB_NAME", "logistics_test")
        out = json.loads(plugin.tools.handle_today_work({"date": "2026-09-09"}))
        assert out["error_type"] == "logistics_connector_error"
        assert "SECRETPW" not in json.dumps(out)
        assert "Logistics query failed" in out["error"]
