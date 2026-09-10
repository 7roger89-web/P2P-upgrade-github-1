# Personal AI Assistant Vision

Status: Long-term product direction for the user's personal AI assistants.

## Core goal

Build one or more personal AI assistants that can be reached from Telegram and Discord and can later expand to other personal workflows.

## Interaction

- Text input and text response.
- Voice input through Telegram/Discord.
- Voice response through TTS.
- Persona/style switching per session or command.
- Keep factual content stable while only changing the wording and voice style.

Example persona families:
- normal
- master/servant
- emperor/palace attendant
- 19th-century merchant
- wuxia
- TVB-style martial-arts drama
- palace intrigue
- xianxia/cultivation
- modern rap battle
- Vietnamese folk/luc-bat
- playful/comedic
- dramatic Vietnamese storyteller-style (without depending on exact impersonation of a real person)

## Factual-data rule

Personal/business facts must come from an authoritative data layer rather than being improvised by the model.

Examples:
- logistics rates
- origin/destination pairs
- container/vehicle types
- customs and handling fees
- exchange rates
- formulas
- company procedures
- uploaded PDFs/Excel/Markdown/reference documents

Persona and TTS layers may alter style, tone, vocabulary and delivery, but MUST NOT alter:
- amounts
- currencies
- units
- route
- vehicle/container type
- dates/effective periods
- business conditions

If a requested fact is not in the authoritative data source, the assistant should say it is not found instead of inventing a value.

## Target architecture

Telegram / Discord
    -> Hermes gateway
    -> STT when input is voice
    -> intent + context
    -> authoritative data / tools / documents
    -> fact lock
    -> persona renderer
    -> text response and/or TTS voice response

## Hermes target capabilities

Prefer Full Hermes where practical:
- persistent memory/sessions
- skills
- cron
- terminal/files
- MCP
- subagents
- Telegram/Discord gateway
- voice input/output
- tool use and automation

On low-memory hosts, defer local Chromium, dashboard, local Whisper and other heavy components rather than rewriting Hermes into a separate lite system.

## Hosting strategy

Current experiment: DockHosting Free.

Goal:
- no credit card
- official Hermes Docker image
- persistent state at /opt/data
- health endpoint
- UptimeRobot keepalive experiment
- Telegram first; Discord after core runtime is proven

If the free host cannot remain stable within its resource limit, pivot to a 2–4 GB host or an Android/other existing device rather than building unnecessary infrastructure.

## Expansion

Future assistants may cover multiple areas beyond Logistics. Add each new assistant/domain only when it has a concrete user need, data source and useful action path.
