# Execution Target Pattern Research — Durable Provenance Artifact

**Artifact ID:** C30-RESEARCH-001
**Goal:** C30 — Composable Execution Target Foundation + Durable Provider-Neutral Architecture Intake
**Observed:** 2026-08-17 (C30 session, single agent, sandboxed)
**Method:** Public documentation and repository pages only. No source code was copied into the P2P repository; only architectural patterns, vocabulary, and design decisions were recorded as observations. Every claim below is attributed to a public URL and a retrieval date.
**Purpose:** This artifact durably records the provider-neutral execution architecture patterns found across the public agent ecosystem, so that C30's ledger reconciliation, charter deltas, and composable execution-target model are grounded in external evidence rather than session claims. It is the single durable intake artifact required by the C29 future-research preservation rule.

---

## 1. Research Sources

| # | Source | Type | URL | Key content used |
|---|--------|------|-----|------------------|
| 1 | OpenHands/software-agent-sdk | Docs | https://docs.openhands.dev/sdk/arch/overview | Four-package separation; provider-agnostic LLM interface; swappable workspaces; deployment modes; agent server |
| 2 | miuuyy/codex-chatgpt-web | README | https://github.com/miuuyy/codex-chatgpt-web | Provider-as-model seam; Effort tiers; fail-closed drift; failure-only diagnostics; MCP harness flow |
| 3 | All-Hands-AI/OpenHands (Agent Canvas) | README | https://github.com/All-Hands-AI/OpenHands | Multi-backend registry; ACP-compatible agent interchange; single frontend, many servers |
| 4 | anomalyco/opencode (docs + agents) | Docs | https://opencode.ai/docs/ and https://opencode.ai/docs/agents/ | Provider/model identity; Plan vs Build agents; permissions; max steps; agent profiles on disk; AGENTS.md init |
| 5 | cline/cline | README | https://github.com/cline/cline | One engine, four harnesses; provider matrix; headless JSON; worktree kanban; plugin SDK; MCP; cron; protocol connectors |
| 6 | BloopAI/vibe-kanban | README | https://github.com/BloopAI/vibe-kanban | 10+ agent switch; workspaces (branch+terminal+devserver); diff review loop; cleanup policy; **sunsetting announcement** |
| 7 | aaif-goose/goose | Docs | https://goose-docs.ai/docs/goose-architecture/ | Interface/Agent/Extensions triad; ACP duality; interactive loop; error feed-back; context revision |
| 8 | Aider-AI/aider | Docs | https://aider.chat/docs/repomap.html | Repository map; graph ranking; token budget; dynamic sizing; .aiderignore |
| 9 | arXiv:2604.18071 | Paper | https://arxiv.org/html/2604.18071v1 | "Agent harness" as non-LLM engineering layer; cross-project design bundles; "language determines architecture" rejected |

---

## 2. Observed Patterns (evidence-grounded)

### 2.1 Harness is not Provider, Model, or Protocol

OpenHands documents a **provider-agnostic LLM interface** as a core SDK package: the `LLM` component is a plug-in with retry and telemetry, while the agent loop, tools, events, and workspaces are independent packages. The same agent code runs with different workspace implementations (`LocalWorkspace`, `RemoteWorkspace`, `DockerWorkspace`) by swapping only configuration — deployment flexibility is a **configuration substitution**, not a behavioral re-certificate [1].

codex-chatgpt-web demonstrates the inverse seam in the wild: the **same harness (Codex)** keeps its task context, model picker, streaming, and tool lifecycle, while **a different provider (ChatGPT Web)** fills the model slot via a local bridge. The model picker lists web-tier "models" (Luna, Instant, Medium, High, Extra High, Pro) as interchangeable entries — horizontal substitution at the provider layer, with Codex still the source of truth for task history [2].

Cline ships **one engine across four harnesses** (CLI, VS Code extension, JetBrains plugin, Kanban board) and explicitly supports a provider matrix spanning Anthropic, OpenAI, Gemini, OpenRouter, Vercel AI Gateway, AWS Bedrock, Azure/GCP Vertex, Cerebras/Groq, Ollama, LM Studio, and "Any OpenAI-compatible API" [5]. An AI brand is not an execution architecture.

goose makes the protocol seam first-class: it speaks **ACP** both as a server (editors connect to it) and as a client to other **ACP agents acting as providers** — Claude Code and Codex can run "under" goose, with tool execution delegated to the external agent and extensions forwarded as MCP servers [7]. Protocol (ACP/MCP), harness (goose), and provider (Claude Code) are three independent substitution axes in one product.

> arXiv 2604.18071 formalizes this separation: across 70 agent projects, the "agent harness" — the non-LLM engineering layer of tool mediation, context handling, execution boundaries, and governance — is architecturally distinct from the model, and the assumption "language determines architecture" does not survive cross-project comparison [9].

### 2.2 Planner neutrality

OpenCode defines two built-in primary agents — **Plan** (restricted: `edit: deny`, `bash: deny`) and **Build** (all tools enabled) — each with its own model and permission block in the same config file. A cheaper or more deliberate model can run planning without the act agent ever seeing its outputs as authority. Subagents (General, Explore, Scout) add delegated specialist roles with read-only variants [4].

### 2.3 Verifier neutrality

OpenCode's **Explore** and **Scout** subagents are read-only: Explore cannot modify files; Scout researches external dependencies against a managed cache without changing the workspace [4]. Vibe-kanban's review loop lets a human (or any reviewing process) inspect diffs and feed inline comments back to the agent without the agent self-certifying [6]. Verification in the ecosystem is structurally separable from generation.

### 2.4 Workspace isolation

Cline Kanban gives **each card its own worktree** with auto-commits and dependency chains [5]. Vibe-kanban allocates **each workspace one branch, one terminal, and one dev server**, with an explicit worktree cleanup policy and an escape hatch (`DISABLE_WORKTREE_CLEANUP`) [6]. OpenHands formalizes `Workspace` as a swappable SDK base class with local and remote implementations [1]. Isolation is a provisioned artifact, not an ambient property of the host.

### 2.5 Token-bounded repository map

Aider's **repository map** is a concise, git-derived map of the whole repo: files, key symbols, and critical definition lines, delivered with every change request. The full map is treated as a graph (files as nodes, dependencies as edges); a **graph-ranking algorithm selects the most important portions within the active token budget** (`--map-tokens`, default 1k), resizing dynamically by chat state. The map is regenerated from the git working tree — it never inherits model claims [8]. OpenCode's `/init` produces an equivalent project-documentation artifact (`AGENTS.md`) [4].

### 2.6 Failure-focused diagnostics

codex-chatgpt-web saves **bounded JSON state at each checkpoint** and captures screenshots **only for stalled or failed turns**, explicitly so successful steps are not slowed by diagnostic capture. UI drift "produces explicit errors rather than silent fallbacks" [2]. goose feeds execution errors (invalid JSON, missing tools) back to the model as tool responses so the loop recovers instead of breaking [7]. The ecosystem norm is bounded, failure-triggered evidence, not continuous surveillance of every step.

### 2.7 Permission profiles

OpenCode permissions gate each tool (`read`, `edit`, `bash`, `grep`, `list`, `task`, `webfetch`, `websearch`, `lsp`, `skill`, `question`, `doom_loop`) with `ask | allow | deny`, support glob patterns, and support wildcards that deny whole MCP servers (`mymcp_*: false`) [4]. The permission profile is a stable, per-agent artifact that survives provider changes.

### 2.8 Model variants and effort tiers

Codex separates model selection from **Effort tiers** (Instant/Medium/High/Extra High/Pro) and Speed rows; the bridge enforces that changing Effort cannot silently change the selected browser model [2]. OpenCode assigns **per-agent temperature** with model-specific defaults (typically 0 for most models) [4]. Effort and temperature are **variant dimensions of a model identity**, not new models and not new providers.

### 2.9 Freshness budgets

goose's **context revision** removes old or irrelevant content, summarizes with a faster/smaller LLM, and uses find-and-replace plus output summarization to keep token cost bounded [7]. Aider resizes its repo map dynamically with chat state [8]. Freshness is a managed budget with deterministic machinery, not a promise of perfect recency.

### 2.10 Execution budgets

OpenCode's per-agent `steps` (max steps) forces the agent to respond with a text summary and remaining-task recommendations when the budget is exhausted [4]. Kanban dependency chains bound which work proceeds in parallel [5,6]. Budgets make execution measurable by the Owner without requiring the Owner to watch it.

### 2.11 Health and ownership

codex-chatgpt-web bundles a setup **smoke test, runtime health page, and `doctor` end-to-end check** in its launcher [2]. OpenHands Agent Server exposes health checking as an API feature [1]. Health state is checkable on demand; nothing observed implies continuous autonomous operation.

### 2.12 Quiesce and drain vocabulary

Ecosystem products carry the vocabulary in parts: codex-chatgpt-web offers "Cancel retained browser turn" to stop a stalled task's model work, and vibe-kanban has a workspace cleanup policy for retiring worktrees [2,6]. No unified, standard quiesce/drain contract was found — an honest **gap**: the semantics exist scattered, but P2P would define the first durable, deterministic version.

### 2.13 Structured headless execution

Cline runs `cline "prompt"` producing parseable JSON (events selectable with `jq`) for CI/CD; OpenHands documents headless deployment modes and an API server; OpenAI publishes Codex CLI headless/exec mode for CI [5,1]. Headless is a transport with a deterministic envelope (input, bounded output, exit state), independent of any interactive TUI.

### 2.14 Backend registry without routing authority

vibe-kanban lists **10+ switchable coding agents** and the Owner chooses; OpenHands Canvas connects to **multiple Agent Servers** and flips between them from one frontend [6,3]. The registry records and exposes options; it does not route, rank, or execute. Selection authority remains outside the registry — with the Owner.

### 2.15 Control plane vocabulary and permission widening

All nine sources separate a **control plane** (configuration, composition, and target declaration: which harness, provider, model, protocol, workspace, and permission set form a target) from an execution plane (actually running a task). No source allows composition to silently widen permissions or to grant a permission **bypass** to any component — permission elevation always requires an explicit, documented decision by the human owner, never an implicit grant by the composition machinery [1,4,7]. This validates the C30 invariant that the composable execution-target model is a read-only description of eligibility: it declares which compositions satisfy a task's requirements, and never executes, routes, or relaxes security controls.

---

## 3. What the Ecosystem Explicitly Does NOT Do (relevant to claim boundary)

Three patterns were searched for and found **absent** in all nine sources. Their absence is itself evidence supporting the C30 claim boundary. First, **no source implements automatic host or model routing** — every registry observed leaves selection to the human owner. Second, **no source treats a browser as a core transport**; browser automation appears only as an optional tool or bridge with explicit drift warnings [2]. Third, **no source claims provider-neutral AutoPilot**; planning assistance is mode-scoped (Plan mode) and always bounded by explicit approvals. Automatic fallback was also rejected by design: codex-chatgpt-web's own statement is that "drift fails explicitly instead of silently switching model or transport" [2].

## 4. Reconciliation Status

This artifact maps directly to the C30 ledger reconciliation (see `capability-index.json` provenance updates): patterns A–O from the research correspond to ledger record classifications recorded durably during C30. The artifact does not duplicate any code; every reference is to a public URL retrieved on the observation date.

## 5. Source Integrity Notes

vibe-kanban announced a **shutdown** (source [6] retains the announcement link) — included for the honest historical pattern record, not as a live dependency. codex-chatgpt-web is explicitly unofficial browser automation; its warnings about drift and transport boundaries are treated as design constraints, not capabilities. All URLs were retrieved 2026-08-17; any future URL rot is a freshness gap for a future Goal's review, not a C30 claim.
