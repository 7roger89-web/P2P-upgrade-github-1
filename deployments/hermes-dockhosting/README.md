# Hermes on DockHosting Free

This package runs Hermes Agent core on DockHosting Free with persistent state and a public health endpoint for UptimeRobot.

## Build source

- Base image: `nousresearch/hermes-agent:latest`
- Dockerfile path: `deployments/hermes-dockhosting/Dockerfile`
- Persistent volume mount: `/opt/data`
- Health check path: `/health`
- Runtime target: 1 GB RAM Free tier
- Keep Hermes Dashboard and local Chromium/browser automation off on this tier.

## Hermes patches

The image pins `hermes-patches==1.6.1` and applies this build-time set:

- `footer`
- `table`
- `db`
- `nostream`
- `clean-think`
- `smart-split`
- `terminal-cwd`
- `state-guard`

The Docker build verifies all eight selected patches before it succeeds.

Intentionally excluded initially:

- `tirith`: it changes approval behavior by auto-allowing LOW/INFO security findings.
- `menu`: Chinese Telegram menu localization is not useful for this deployment.

This keeps durability, Telegram formatting, anti-429 behavior, long-message splitting, terminal recovery, token footer, thinking-output cleanup, and state-database protection without weakening the approval boundary.

## Required runtime secrets / variables

Telegram:

```text
TELEGRAM_BOT_TOKEN=<BotFather token>
TELEGRAM_ALLOWED_USERS=<your Telegram numeric user ID>
GEMINI_API_KEY=<Google AI Studio API key>
```

Discord instead of Telegram:

```text
DISCORD_BOT_TOKEN=<Discord bot token>
DISCORD_ALLOWED_USERS=<your Discord numeric user ID>
GEMINI_API_KEY=<Google AI Studio API key>
```

Optional:

```text
HERMES_DEFAULT_MODEL=gemini-3.7-flash
```

Do not commit real tokens or API keys to GitHub.

## Read-only Logistics integration (Hermes plugin)

Hermes ships a native plugin (`plugins/hermes-logistics`) that exposes three
**read-only** Logistics data tools:

- `logistics_today_work` — "Hôm nay tôi có việc gì?"
- `logistics_freight_rate_lookup` — "Cước Hải Phòng về Hà Nội container 20' bao nhiêu?"
- `logistics_shipment_status` — "Lô hàng <ID> hiện thế nào?"

The plugin runs real MongoDB queries via `pymongo` (installed at image build
time) using a **read-only credential**. It adds no HTTP API, no microservice,
no queue, no daemon, and no MCP server. It is enabled automatically through
`plugins.enabled` in the Hermes config.

Required environment variables (read-only credential only — never the
production write URI):

```text
LOGISTICS_MONGO_URI_READONLY=<read-only MongoDB connection string>
LOGISTICS_MONGO_DB_NAME=<Logistics database name>
```

Optional:

```text
LOGISTICS_SCHEMA_PATH=<path to a schema.yaml override>
```

If these are absent, the tools return `status = NOT_CONFIGURED` and name the
exact variables needed; they never guess a rate, status, or business fact. The
plugin's schema contract (`schema.yaml`) is `PROVISIONAL_UNVERIFIED` and must be
confirmed against the real Logistics application before relying on live data.
See `plugins/hermes-logistics/README.md` for full detail and the focused
non-secret tests in `tests/test_hermes_logistics_connector.py`.

## DockHosting settings

```text
Branch: main
Dockerfile: deployments/hermes-dockhosting/Dockerfile
Persistent volume mount: /opt/data
Health path: /health
```

DockHosting supplies `PORT`; the startup wrapper maps Hermes' API server to that port automatically.

## UptimeRobot

After DockHosting assigns a public URL, monitor:

```text
https://<your-app-host>/health
```

Use an HTTPS monitor at the Free-plan interval.

If the Free platform still scales the container to zero despite incoming health traffic, or Hermes repeatedly OOMs at 1 GB, stop this route rather than adding more machinery.

## Resource policy

Targeted here:

- Telegram or Discord gateway
- Hermes memory and sessions
- skills
- cron
- terminal/files
- MCP where supported
- selected hermes-patches above

Deferred until a host with at least 2 GB RAM is available:

- local Playwright/Chromium
- Hermes Dashboard
- heavy sidecars
- generalized observability
