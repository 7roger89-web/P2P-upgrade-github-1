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
    -> behavior controller
    -> persona / voice renderer
    -> anti-slop check
    -> text response and/or TTS voice response

The behavior controller decides response behavior before wording generation where possible: answer directly, research first, use a required tool, or ask only when ambiguity genuinely blocks completion. Style state is structured separately from factual state.

Canonical invariant:

```text
FACTS != STYLE
STYLE_MAY_CHANGE_WORDING
STYLE_MUST_NOT_CHANGE_LOCKED_FACTS
```

Detailed candidate contract:

`docs/SPEC/P2P-PERSONAL-AI-BEHAVIOR-HARNESS-V1.md`

Initial deterministic runtime slice:

`.p2p/system/p2p_capabilities/personal_ai_behavior.py`

## Behavior and communication state

The assistant should keep a small structured communication profile instead of relying only on one large prose prompt. Representative dimensions include language, familiarity, directness, humor, sarcasm, tolerance for corporate filler, mild profanity, and whether fresh Vietnamese associations are preferred.

Task-local state overrides the stable profile when appropriate. In particular, an explicit request for a serious tone disables jokes/sarcasm for that response without rewriting the stable profile.

Anti-slop checks should target strong generic chatbot markers first. They must not be allowed to rewrite or numerically alter locked factual content.

## Memory learning

Conversation reflection should produce memory candidates rather than directly editing durable memory.

Preferred boundary:

```text
conversation
    -> reflection/extraction
    -> candidate
       -> explicit Owner instruction: promotion-eligible
       -> uncertain inference: held separately
       -> repeated confirmed observation: review-eligible
       -> one-off impression: candidate only
    -> authorized durable-memory layer
```

Uncertain inferences must remain distinguishable from confirmed fact. Do not create a separate memory database when Hermes/platform memory already satisfies the real workflow.

## Open loops and agenda

Open loops such as a pending PR review, quote deadline, missing shipment data, promised follow-up, or watch condition are useful assistant state and should not be treated as ordinary chat history.

However, reuse existing cron/task/storage capability when available. Do not build a new agenda daemon or scheduler until a concrete workflow demonstrates the need.

## Human-likeness boundary

The assistant may communicate naturally and consistently, but the architecture does not require deceptive claims of being human. Personality should improve usefulness and continuity, not override factual honesty.

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
