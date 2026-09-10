# Hermes Logistics Read-Only Integration (HERMES_LOGISTICS_READONLY_001)

First useful vertical slice connecting Hermes to the authoritative Logistics
datastore (`logistics-work-desk`, MongoDB). Hermes can answer three question
classes with REAL Logistics data — no invented facts:

| Question (example) | Tool | Source collection |
| --- | --- | --- |
| "Hôm nay tôi có việc gì?" | `logistics_today_work` | `tasks` (explicit ASSIGNEE/TEAM scope) |
| "Cước Hải Phòng về Hà Nội container 20' bao nhiêu?" | `logistics_freight_rate` | `rate_cards` (structured lookup of the PR #12 rate-card schema) |
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
- **rate_cards** — STRUCTURED shape (logistics-work-desk PR #12, merge commit
  `2eb2c343c10c2f909685f1f83cb77683197572f8`):
  `{id, customer, route_name, route{origin, destination, equipment_type,
  container_size, transport_mode}, currency, structured_lookup_ready,
  history[{month "MM/YYYY", total_cost, total_price, profit, details,
  updated_at}]}`. `logistics_freight_rate` queries ONLY cards where
  `structured_lookup_ready == true` and `is_deleted != true` (legacy free-text
  cards and not-ready cards are excluded), and matches the structured
  `route.origin` / `route.destination` fields exactly, plus
  `route.equipment_type` / `route.container_size` / `route.transport_mode`
  when supplied.
  - `route_name` stays free text and is NEVER used for machine lookup or even
    echoed in the result; there is NO geographic alias/normalization — exact
    place names are required, so `"HP"` never silently becomes
    `"Hải Phòng"`.
  - The ONLY non-verbatim matcher normalization is a bounded deterministic
    container-size table compatible with the Logistics schema:
    `20` / `20FT` / `20'` → `20'`; `40HQ` / `40HC` → `40HC` (case, spacing
    and typographic quotes folded; unknown spellings pass through verbatim
    and are never guessed).
  - Month handling: without a `month` (`MM/YYYY`) the LATEST valid history
    month is selected by parsing `MM/YYYY` — array order is not trusted; an
    explicit month with no history entry returns `RATE_HISTORY_NOT_FOUND`
    (plus the available months); no historical price is ever invented.
  - Statuses are exactly `OK`, `NOT_FOUND`, `AMBIGUOUS`,
    `RATE_HISTORY_NOT_FOUND`. More than one matching customer-specific rate
    card returns `AMBIGUOUS` with bounded candidate facts
    (`rate_card_id`, `customer`, `route`, `currency`) — the tool never
    silently picks one and never quotes a price until disambiguated.
  - Price semantics (business meaning is preserved): `selling_price` =
    `history.total_price` (the selling/customer quoted rate — this answers
    "Cước X về Y bao nhiêu?"); `internal_cost` = `history.total_cost`
    (internal only, NEVER presented as the customer freight rate);
    `profit` = `history.profit`; the explicit card `currency` is always
    preserved and never assumed.

## Verification status

- Focused non-secret tests: `python3 -m pytest tests/test_hermes_logistics_readonly.py`
  (today-work incl. ASSIGNEE/TEAM scope; structured freight lookup — exact
  20' match, 20FT/40HQ aliases, legacy/not-ready/deleted exclusion, wrong
  route/container NOT_FOUND, latest MM/YYYY selection, requested month,
  RATE_HISTORY_NOT_FOUND, selling_price/internal_cost semantics, currency,
  AMBIGUOUS, no route_name parsing, no geographic aliases, contract helper
  unit tests and removal of the obsolete schema-gap status; shipment status;
  read-only safety; secret safety; plugin registration contract; real-driver
  error path).
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
2. **RATE_CARD_DATA_QUALITY (operational, not a schema task)** — the
   structured rate-card schema now exists (logistics-work-desk PR #12, merge
   `2eb2c343c10c2f909685f1f83cb77683197572f8`) and the freight tool queries it
   directly. Legacy cards without `structured_lookup_ready=true` (or with it
   explicitly false) are excluded from lookup by design; populate/migrate the
   structured `route` fields and flag cards ready within Logistics if a card
   should become answerable. No schema gap remains on the Hermes side.
3. **IDENTITY_BINDING** (future, optional) — bind messaging identity (e.g.
   Telegram user) to Logistics `assignee_user_id` so "Hôm nay TÔI có việc gì?"
   can default to ASSIGNEE scope instead of TEAM scope.

## Out of scope (deliberately)

Voice/TTS, personas, Discord, weather, maps, cron, persistence repair,
Telegram webhook conversion, Logistics write actions, new services, RAG/vector
infrastructure.
