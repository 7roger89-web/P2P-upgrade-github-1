# Hermes Logistics Read-Only Integration (HERMES_LOGISTICS_READONLY_001)

First useful vertical slice connecting Hermes to the authoritative Logistics
datastore (`logistics-work-desk`, MongoDB). Hermes can answer three question
classes with REAL Logistics data — no invented facts:

| Question (example) | Tool | Source collection |
| --- | --- | --- |
| "Hôm nay tôi có việc gì?" | `logistics_today_work` | `tasks` (explicit ASSIGNEE/TEAM scope) |
| "Cước Hải Phòng về Hà Nội container 20' bao nhiêu?" | `logistics_freight_rate` | `rate_cards` (fail-closed: verified schema insufficient, see below) |
| "Lô hàng LK-1024 hiện thế nào?" | `logistics_shipment_status` | `shipments` |

## Architecture

```text
Telegram
  -> Hermes gateway (existing deployment)
  -> Hermes plugin "logistics" (bundled backend plugin, 3 tools)
  -> Logistics MongoDB via READ-ONLY credential
  -> normalized factual result with provenance
  -> Hermes response
```

No new service, database, queue, daemon, or API server: the plugin runs inside
the existing Hermes runtime and queries MongoDB directly, exactly like other
bundled Hermes integrations.

## Installation (already part of the Dockerfile)

The plugin is copied to `/opt/hermes/plugins/logistics/` at image build time
and `pymongo==<PYMONGO_VERSION>` is installed into the sealed image venv.
Bundled backend plugins auto-load, so no `/opt/data` config state is needed
(this deliberately avoids the currently-unreliable local persistence).

## Required runtime configuration (secrets — never commit these)

```text
LOGISTICS_MONGO_URI_READONLY=<a MongoDB URI whose credential has READ-ONLY privileges on the Logistics database>
LOGISTICS_MONGO_DB_NAME=<Logistics database name, e.g. logistics>
```

Use a dedicated read-only MongoDB user/role. Do NOT reuse a production write
credential.

Until both variables are set, the three tools are hidden from the model
(`check_fn` gates tool schema exposure) and every handler fails closed with a
`logistics_config_missing` error naming the required variables.

## Read-only enforcement

The connector (`plugins/logistics/connector.py`) is read-only by design:

- public surface is exactly `find` / `find_one` / `close` (+ `allowed_collections`, `db_name`);
- collection allowlist: `shipments`, `tasks`, `rate_cards` only;
- filters accept plain field matches and `$ne` only — no top-level operators;
- limit clamped (1..200), bounded client timeouts (5 s server selection);
- no insert/update/delete/replace/drop/createIndex/bulk_write/aggregate anywhere;
- the URI is never echoed into tool output (sanitized from all error text).

Tests assert each of these properties (`tests/test_hermes_logistics_readonly.py`).

## Data contracts (observed from logistics-work-desk main, supplied 2026-09-09)

- **tasks** — `task_id`, `content`, `assignee`, `assignee_user_id`, `deadline`,
  `done`, `created_at`, soft-delete via `is_deleted`; canonical loader sorts
  `created_at` descending. "Today's work" = open (not deleted, not done) tasks
  whose parseable deadline matches the requested day (Asia/Ho_Chi_Minh,
  UTC+07:00). Open tasks without a parseable deadline are counted and can be
  included with `include_undated=true`; nothing is invented. Scope is explicit:
  `ASSIGNEE` (with `scope_value`) when `assignee`/`assignee_user_id` is
  supplied, otherwise `TEAM` with a note that no personal identity was
  supplied — TEAM results must never be presented as the user's own personal
  tasks. There is no identity service in this task; a future bounded task may
  bind messaging identity (e.g. Telegram user) to Logistics `assignee_user_id`.
- **shipments** — lookup by stable business id `shipments.id`; exclude
  `is_deleted == true`; exclude `is_archived == true` unless
  `include_archived=true`; `status` falls back to `data["0.0"]["st"]`;
  `customer`/`client` mirror each other; financial section `data["3.4"]` is
  never exposed for status requests. Note: the section key `"0.0"` contains a
  dot, so it is read in Python, never via Mongo dot-notation.
- **rate_cards** — VERIFIED persisted shape (logistics-work-desk
  `views/sales.py`, independently verified by Control Tower 2026-09-09):
  `{id, customer, route_name, history[{month, total_cost, total_price,
  profit, details[{name, cost, price}], updated_at}]}`. **origin, destination,
  container/equipment and currency are NOT structured fields**; `route_name`
  is free text (may contain descriptive hints such as "(Cont 40)") and is
  never heuristically parsed as authoritative structured data. A structured
  route lookup (X → Y, container Z) therefore cannot be answered from the
  current schema, so `logistics_freight_rate` **fails closed** with
  `RATE_CARD_SCHEMA_INSUFFICIENT_FOR_STRUCTURED_ROUTE_LOOKUP`: it executes a
  real bounded read-only sample query (key names only — route_name values are
  not echoed), reports the verified schema finding, and never returns a rate.
  No new collection is created to work around this; a follow-up Logistics
  schema task (structured route/equipment/currency fields or a normalized
  rate model) is required before a matcher can be implemented.

## Verification status

- Focused non-secret tests: `python3 -m pytest tests/test_hermes_logistics_readonly.py`
  (43 tests — today-work incl. ASSIGNEE/TEAM scope, freight fail-closed with
  the verified schema finding, shipment status, read-only safety, secret
  safety, plugin registration contract, real-driver error path).
- Plugin load verified against the real hermes-agent plugin loader (bundled
  backend auto-load; toolset `logistics` on by default for telegram/api_server;
  tools hidden without env, exposed with env).
- `LIVE_MONGO_VERIFIED=NO` — no read-only credential was available in the
  execution environment, so no live MongoDB query was executed. This is an
  Owner Gate (see below), not a claimed pass.

## Owner gates

1. **READ_ONLY_MONGO_CREDENTIAL** — create a MongoDB user with read-only
   privileges on the Logistics database, then set on DockHosting:
   `LOGISTICS_MONGO_URI_READONLY`, `LOGISTICS_MONGO_DB_NAME`. Then ask Hermes
   the three questions and confirm answers match the Logistics app.
2. **LOGISTICS_RATE_CARD_SCHEMA_TASK** — the verified rate-card schema has no
   structured origin/destination/container/currency fields (route_name is free
   text), so structured freight-rate lookup requires a follow-up bounded task
   in logistics-work-desk to add structured fields (or a normalized rate
   model). Only after that schema exists should the freight matcher be
   implemented in a follow-up Hermes task.
3. **IDENTITY_BINDING** (future, optional) — bind messaging identity (e.g.
   Telegram user) to Logistics `assignee_user_id` so "Hôm nay TÔI có việc gì?"
   can default to ASSIGNEE scope instead of TEAM scope.

## Out of scope (deliberately)

Voice/TTS, personas, Discord, weather, maps, cron, persistence repair,
Telegram webhook conversion, Logistics write actions, new services, RAG/vector
infrastructure.
