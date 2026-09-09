# Hermes Logistics plugin (read-only)

A native Hermes plugin that gives the assistant three **read-only** Logistics
data capabilities. It runs real MongoDB queries against the Logistics
datastore using a **read-only credential**. It adds no HTTP API, no microservice,
no queue, no daemon, and no MCP server.

## Tools

| Tool | Purpose |
| --- | --- |
| `logistics_today_work` | List the actionable Logistics items for a target day (default today, `Asia/Ho_Chi_Minh`). Answers "Hôm nay tôi có việc gì?". |
| `logistics_freight_rate_lookup` | Current/recent freight rate from origin → destination for container/vehicle size. Answers "Cước Hải Phòng về Hà Nội container 20' bao nhiêu?". |
| `logistics_shipment_status` | Exact current status of a shipment by id/reference. Answers "Lô hàng \<ID\> hiện thế nào?". |

Each tool returns a normalized JSON result with `status`
(`FOUND` / `NOT_FOUND` / `AMBIGUOUS` / `SCHEMA_UNVERIFIED` / `NOT_CONFIGURED`),
the relevant facts, and provenance (`source`, `queried_at`,
`schema_status`). It never invents a rate, currency, route, status, or date.

## Security contract

* **Read-only by design.** `connector.ReadOnlyConnection` wraps the MongoDB
  client/database/collection and rejects every write operation
  (`insert_*`, `update_*`, `delete_*`, `drop_*`, `create_index`, ...) with
  `ReadOnlyViolation`. There is no write method anywhere on the public surface.
* **Read-only credential.** Set `LOGISTICS_MONGO_URI_READONLY` (never the
  production write URI) and `LOGISTICS_MONGO_DB_NAME`.
* **No secrets in code.** No URI/password/token appears in this repository.
* **Collection allowlist.** Only the collections named in `schema.yaml`
  (`shipments`, `rate_cards`, `review_queue`) are ever read.

### Required environment variables (for live data)

```text
LOGISTICS_MONGO_URI_READONLY=<read-only MongoDB connection string>
LOGISTICS_MONGO_DB_NAME=<Logistics database name>
LOGISTICS_SCHEMA_PATH=<optional path to a schema.yaml override>
```

If these are absent, the tools return `status = NOT_CONFIGURED` and name the
exact variables needed. They never guess.

## Schema contract (`schema.yaml`)

The physical collection + field names are defined in **`schema.yaml`**. The
shipped contract is `PROVISIONAL_UNVERIFIED` because the authoritative
Logistics application repository (`7roger89-web/logistics-work-desk`) was not
accessible at implementation time. The connector **fails closed**: it resolves
field candidates against a sampled document and matches by normalized equality,
so a wrong contract returns `NOT_FOUND` / `SCHEMA_UNVERIFIED` instead of a
wrong fact. Confirm the real collection/field names against the application and
update `schema.yaml` (data only — no code change required).

## Wiring

On DockHosting, the image build installs `pymongo` and copies this plugin into
`/opt/hermes-logistics`. The startup entrypoint copies it into
`HERMES_HOME/plugins/hermes-logistics` (`/opt/data/plugins/...`) and enables it
via `plugins.enabled` in the Hermes `config.yaml`, so it loads without a
separate install step.

## Testing

Focused, non-secret tests live in `tests/test_hermes_logistics_connector.py`.
They use an in-memory fake MongoDB (no production credential) and cover:
today's work (match / exclude / no data), freight rate (exact route +
container / most recent / NOT_FOUND / AMBIGUOUS), shipment status (exact id /
unknown id), read-only safety (write operations raise), and secret safety
(no credential in the tree).
