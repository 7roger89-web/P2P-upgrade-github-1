# Hermes Logistics Read-Only Integration (HERMES_LOGISTICS_READONLY_001)

First useful vertical slice connecting Hermes to the authoritative Logistics
datastore (`logistics-work-desk`, MongoDB). Hermes can answer three question
classes with REAL Logistics data — no invented facts:

| Question (example) | Tool | Source collection |
| --- | --- | --- |
| "Hôm nay tôi có việc gì?" | `logistics_today_work` | `tasks` |
| "Cước Hải Phòng về Hà Nội container 20' bao nhiêu?" | `logistics_freight_rate` | `rate_cards` (fail-closed, see below) |
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
  included with `include_undated=true`; nothing is invented.
- **shipments** — lookup by stable business id `shipments.id`; exclude
  `is_deleted == true`; exclude `is_archived == true` unless
  `include_archived=true`; `status` falls back to `data["0.0"]["st"]`;
  `customer`/`client` mirror each other; financial section `data["3.4"]` is
  never exposed for status requests. Note: the section key `"0.0"` contains a
  dot, so it is read in Python, never via Mongo dot-notation.
- **rate_cards** — stable `id`, soft-delete convention, `load_rate_cards()`
  repository. The route/container/rate/currency/effective-date field names
  could NOT be proven from the logistics-work-desk source, so
  `logistics_freight_rate` **fails closed**: it executes a real bounded
  read-only sample query and returns `SCHEMA_GAP_RATE_CARD_FIELDS` with the
  observed document keys and the exact missing fields. It never returns a
  guessed rate. Once the field mapping is verified against the real
  rate-card model/UI source, set `RATE_CARD_FIELD_MAP` in
  `plugins/logistics/contracts.py` (single extension point) and implement the
  conservative matcher in a follow-up task.

## Verification status

- Focused non-secret tests: `python3 -m pytest tests/test_hermes_logistics_readonly.py`
  (37 tests — today-work, freight fail-closed, shipment status, read-only
  safety, secret safety, plugin registration contract, real-driver error path).
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
2. **RATE_CARD_FIELD_VERIFICATION** — verify the rate-card business fields
   (origin, destination, container/vehicle, rate, currency, effective date)
   from the logistics-work-desk rate-card model/UI source and supply the
   mapping so the freight tool can be activated in a follow-up task.

## Out of scope (deliberately)

Voice/TTS, personas, Discord, weather, maps, cron, persistence repair,
Telegram webhook conversion, Logistics write actions, new services, RAG/vector
infrastructure.
