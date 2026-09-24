# Hermes on DockHosting Free

This package runs Hermes Agent core on DockHosting Free with persistent state and a public health endpoint for UptimeRobot.

## Build source

- Base image: `nousresearch/hermes-agent:v2026.9.14` (Hermes Agent v0.21.3)
- Dockerfile path: `deployments/hermes-dockhosting/Dockerfile`
- Persistent volume mount: `/opt/data`
- Health check path: `/health`
- Runtime target: 1 GB RAM Free tier
- Keep Hermes Dashboard and local Chromium/browser automation off on this tier.

The mutable `:latest` tag is intentionally not used. Runtime compatibility for the pinned image is verified by `.github/workflows/hermes-runtime-compatibility.yml`.

For the richer local-only stack that adds Hermes Workspace, bounded Repomix/TokScale tooling, and opt-in Hindsight, use `deployments/hermes-essential-stack/` instead of widening this 1 GB hosted deployment.

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

## Personal AI behavior runtime

This P2P-specific image bundles and enables the `p2p-personal-behavior` Hermes plugin. It reuses the canonical behavior primitives from `.p2p/system/p2p_capabilities/personal_ai_behavior.py` rather than carrying a second behavior implementation.

The runtime bridge uses only documented Hermes plugin surfaces:

- `register_system_prompt_section(...)` for a cache-safe stable communication contract;
- `pre_llm_call` for explicit turn-local `serious`, `short`, and `deep` requests;
- `transform_llm_output` for report-only anti-slop detection before final delivery.

The bridge intentionally does **not** guess that a message requires research/tool use from keywords, rewrite final answers, auto-promote durable memory, or replace authoritative tool/data values. Existing Hermes/P2P tool, memory, and data layers keep those responsibilities.

The startup wrapper runs Hermes' idempotent `plugins enable p2p-personal-behavior`, so both a fresh config and an already-persisted `/opt/data/config.yaml` converge on the enabled plugin state.

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

Logistics read-only integration (see [README-logistics.md](README-logistics.md)):

```text
LOGISTICS_MONGO_URI_READONLY=<read-only MongoDB URI for the Logistics datastore>
LOGISTICS_MONGO_DB_NAME=<Logistics database name>
```

Use a dedicated MongoDB credential with read-only privileges. The three
Logistics tools (`logistics_today_work`, `logistics_freight_rate`,
`logistics_shipment_status`) stay hidden until both variables are set.

NotebookLM internal knowledge search (optional):

```text
NOTEBOOKLM_AUTH_JSON=<NotebookLM storage-state JSON; secret>
```

When this secret is absent, the NotebookLM plugin stays disabled and the
existing Hermes/Telegram runtime is unchanged. When present, Hermes enables the
read-only `notebooklm_domain_search` tool. It auto-routes staff questions to
the configured HS, Hóa chất, Bộ KH&CN, and Bộ TT&TT notebooks and retrieves
ranked source passages; it does not create/delete notebook content or use shared
NotebookLM chat history.

The connector is intentionally pinned to `notebooklm-py==0.8.2`. It uses
undocumented Google NotebookLM APIs, so upstream changes can break the
integration. Treat `NOTEBOOKLM_AUTH_JSON` as a full-account credential: use a
dedicated Google account that has access only to the notebooks needed by staff,
store the value only in DockHosting environment variables, and never commit or
log it.

Notebook matching uses the known titles by default. Exact IDs or alternate
titles can be supplied without code changes:

```text
NOTEBOOKLM_NOTEBOOKS_JSON={"HS":"...","CHEMICAL":"...","BKHCN":"...","BTTTT":"..."}
NOTEBOOKLM_NOTEBOOK_TITLES_JSON={"HS":"Tra mã HS","CHEMICAL":"Hóa chất","BKHCN":"Bộ khoa học công nghệ","BTTTT":"Bộ Thông Tin truyền thông"}
```

NotebookLM is an operational research layer, not final legal authority. Binding
legal conclusions must still be checked against VNLAW / official sources.

Do not commit real tokens or API keys to GitHub.

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
- P2P Personal AI behavior runtime bridge

Deferred until a host with at least 2 GB RAM is available:

- local Playwright/Chromium
- Hermes Dashboard
- Hermes Workspace
- heavy sidecars
- generalized observability