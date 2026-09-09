# Hermes on DockHosting Free

Goal: run Hermes Agent core on DockHosting Free (1 GB RAM) with Telegram/Discord, persistent state, and a public liveness endpoint for UptimeRobot.

## DockHosting settings

- Plan: Free
- Dockerfile path: `deployments/hermes-dockhosting/Dockerfile`
- Persistent volume mount: `/opt/data`
- Health check path: `/health`
- RAM: 1 GB
- Do not enable Hermes Dashboard or local Chromium/browser on this tier.

DockHosting supplies `PORT`; the runtime maps Hermes API/health to that port automatically.

## Required secrets / variables

For Telegram:

```text
TELEGRAM_BOT_TOKEN=<BotFather token>
TELEGRAM_ALLOWED_USERS=540737263
GEMINI_API_KEY=<Google AI Studio API key>
```

For Discord instead of Telegram:

```text
DISCORD_BOT_TOKEN=<Discord bot token>
DISCORD_ALLOWED_USERS=<your Discord numeric user ID>
GEMINI_API_KEY=<Google AI Studio API key>
```

Optional:

```text
HERMES_DEFAULT_MODEL=gemini-3-flash-preview
```

The API server bearer key is generated automatically on first boot and persisted under `/opt/data`. The public `/health` endpoint exposes only liveness and is intended for DockHosting health checks / UptimeRobot.

## UptimeRobot

After DockHosting assigns a public URL, monitor:

```text
https://<app>.dockhosting.dev/health
```

Use an HTTP(S) monitor at the Free-plan interval. This is an experiment: DockHosting documents that Free apps scale to zero and that long-running bots are not their ideal Free-plan workload. Consistent incoming traffic may keep an app warm, but this is not an always-on guarantee.

## Resource policy

This deployment intentionally targets Hermes core functionality:

- Telegram / Discord gateway
- memory / sessions
- skills
- cron
- terminal / files / MCP where supported by the container

Deferred on the 1 GB Free tier:

- Hermes Dashboard
- local Playwright / Chromium
- heavy sidecars
- generalized monitoring stack

If the container repeatedly OOMs or still sleeps despite the health monitor, stop this route rather than adding more machinery.
