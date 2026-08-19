# P2P Development Charter

> **Durable project truth.** This file records what P2P is trying to become, the principles that may not drift, and the boundary between development knowledge and runtime authority. It is derived from, and subordinate to, `governance/development-control.json` (architectural invariants, roadmap, candidate records) and `docs/AI-HANDOFF.md`. Future AI of any host — ChatGPT, Codex, Manus, Claude, Gemini, Cursor, Copilot — reads this file routinely; detailed capability knowledge lives in `docs/p2p-development/capability-ledger/capability-index.json` and is retrieved only when relevant.

**Version:** C25-initial · **Source of authority:** `governance/development-control.json` · **Canonical ledger:** `docs/p2p-development/capability-ledger/capability-index.json` · **Roadmap projection:** `docs/p2p-development/current-roadmap.md` (derived from the ledger)

---

## 1. North Star — Beginner First

P2P exists so that a person who does not code can say **"Tiếp tục hoàn thiện dự án."** and have P2P carry the technical complexity: recover project truth, understand the goal, determine the next safe work, retrieve sufficient context, choose an execution strategy and a suitable AI/tool where evidence permits, execute bounded work, test, independently verify, persist evidence and state, and ask the owner only when genuinely required.

The owner must not have to choose agents, providers, models, hosts, transports, reasoning levels, context budgets, test commands, retry strategies, quorum, permission implementation, or technical routing. **This charter does not build those capabilities; it ensures the roadmap to build them is never lost or drifted between AIs.**

## 2. Core Identity

P2P is a **provider-neutral self-developing software system**. The host that runs P2P is a host, not the agent, not the model, and not the provider. A task is bounded work performed on one host; the canonical capability identity is the P2P project state, which survives any single host or session. The goal of every development pass is a terminal, evidence-backed result that a fresh AI can fully recover from files alone.

## 3. Invariants (may not drift)

These are the enduring invariants. The canonical machine-readable form is `architectural_invariants` in `governance/development-control.json`; this list is the human-readable projection and must stay consistent with it.

| Invariant | Meaning |
| --- | --- |
| `BEGINNER_FIRST` | Every goal must justify what technical burden it removes from a non-coder. |
| `PROJECT_STATE_NOT_CHAT_HISTORY` | Fresh sessions recover from durable project state, not transcript memory. |
| `P2P_CORE_PROVIDER_NEUTRAL` | Core design assumes no specific provider, model, or host. |
| `HOST_NOT_AGENT` / `HOST_NOT_MODEL` | The host is infrastructure; capability identity is the P2P state. |
| `MODEL_NOT_PROVIDER` | Model choice is never conflated with provider choice. |
| `TRANSPORT_NOT_PERMISSION` | A transport channel never grants permissions by itself. |
| `TASK_NOT_AGENT` | A bounded task is not a capability identity and never becomes an agent by naming. |
| `OUTPUT_NOT_EVIDENCE` | A worker's output is proposed until verified against authoritative evidence. |
| `INVENTORY_NOT_BEHAVIOR` | A file, class, registry entry, or skill existing is not proof of behavior. |
| `GENERATION_NOT_RUNTIME_USE` | Files generated as reference differ from runtime-executed code. |
| `DETERMINISTIC_FIRST` | Deterministic checks come before AI inference wherever sufficient. |
| `PROGRESSIVE_DISCLOSURE` | Load only the context a task needs; small index, deep detail on retrieval. |
| `CORRECTNESS_OVER_TOKEN_SAVING` | Correctness always outranks token or credit economy. |
| `RAW_OUTPUT_NOT_MODEL_CONTEXT` | Raw outputs (filesystem artifacts, logs, test results, terminal output) are durable evidence, not disposable model context; they must be preserved on disk and never silently discarded to save context, and they are never treated as verified without deterministic checking (`DETERMINISTIC_FIRST`). |
| `NO_SECOND_TRUTH_STORE` | No second runtime truth store competes with development-control, Task State, or FACT/Evidence. |
| `NO_SECOND_EXECUTOR` | No execution engine competes with the bounded foreground model. |
| `NO_COMPETING_ROUTER` | P2P remains the sole orchestrator; no second router. |
| `NO_SWARM_FOR_ITS_OWN_SAKE` | Parallelism is bounded and justified by evidence, never decorative. |
| `NO_UNBOUNDED_BACKGROUND_AUTONOMY` | Durable state never grants background execution or scheduler behavior. |
| `NO_BLIND_RETRY` | Retries require mutation certainty and safety classification. |
| `UNKNOWN_IS_NOT_SUPPORTED` | What cannot be verified remains UNKNOWN; UNKNOWN is not "supported". |
| `GOAL_PASS_NOT_PROMOTION` | Goal PASS, candidate verification, release readiness, and promotion are separate states. |
| `OWNER_ONLY_FOR_GENUINE_OWNER_DECISIONS` | Ask the owner only for material decisions that cannot safely be resolved technically. |
| `COMPONENT_IS_NOT_INTERCHANGEABLE` | Harness, provider, model, protocol, and workspace are distinct composition dimensions; the identity of one is never a proxy for the capability or auth state of another. |
| `COMPATIBILITY_IS_NOT_CERTIFICATION` | Transport or API compatibility never implies behavioral certification; certification requires the live-certification path, never a declaration. |
| `PERMISSION_ENVELOPE_NEVER_WIDENS` | Composing permission envelopes can only narrow or preserve the allowed set; composition never produces a permission neither side allowed. |
| `DRIFT_FAIL_CLOSED` | Unknown contract or quiesce states fail closed for destructive lifecycle changes; an old certification never silently remains current. |
| `REGISTRY_IS_NOT_ROUTER` | A neutral execution backend registry enumerates; it never ranks, selects, routes, or auto-falls-back for a task. |

## 4. Owner Gate — what P2P asks the owner about

P2P asks the owner only for: product/business intent, real-world business data, destructive actions, secrets/credentials authorization, material expenditure, production deployment, release/promotion where approval is required, and irreducible ambiguity with material consequences. P2P must **not** ask the owner to choose implementation mechanics that P2P can determine from evidence.

## 5. Authority Boundary — what this charter is and is not

| Authority | What it controls |
| --- | --- |
| `governance/development-control.json` | Goal/development governance: baseline, candidate records, promotion, roadmap. |
| Task State (`.p2p/state`) | Runtime task authority for the current task. |
| FACT / Evidence (`governance/fact-ledger.json`, `governance/live-specs.json`, evidence files) | Factual and evidence authority. |
| **This charter + Capability Ledger** | **Capability knowledge, status, and development intent only.** Never runtime task completion, never task state, never a second FACT store. |
| `docs/p2p-development/framework/` | Derived product memory (architecture, master roadmap, capability & skill map). References, never duplicates, governance and ledger truth; on conflict the canonical sources win. |

The ledger references governance and evidence files; it never copies their full contents. Derived artifacts (templates, roadmap projection) declare their source in a header. If the charter, schema, ledger, and projection ever silently contradict, that is a defect to be fixed by reconciliation against the canonical sources — never by editing a derived copy to match another derived copy.

## 6. How the next Goal is chosen

The next goal is never chosen because the previous goal number was C24. It is chosen by weighing beginner value, the current capability gap, dependency readiness, evidence readiness, risk reduction, and implementation minimality — all of which the Capability Ledger makes inspectable. The Goal Contract template (`docs/p2p-development/templates/P2P-GOAL-CONTRACT-TEMPLATE.md`) requires one primary objective stated as **what becomes TRUE after this goal that was not TRUE before**, explicit non-goals, existing-architecture-first recovery, behavioral acceptance over inventory, an evidence contract, a regression contract, beginner-impact and cognitive-economy reviews, and a terminal stop. If the beginner value cannot be answered convincingly, DEFER is a valid and encouraged outcome.

## 7. What must never be reintroduced

`TASK_AS_AGENT`, `SECOND_TASK_TRUTH_STORE`, `SECOND_EXECUTOR`, `COMPETING_ROUTER`, `UNBOUNDED_SWARM`, `FULL_CONTEXT_PRELOAD`, `FULL_CHAT_AS_PROJECT_STATE`, `BLIND_RETRY`, `HOST_OUTPUT_AS_FINAL_EVIDENCE`, `AUTO_PROMOTION_AFTER_GOAL_PASS`, `174_NUI_FACULTIES_AS_AGENTS`, `HOSTS_AS_CANONICAL_AGENTS`, `PROVIDER_HARDCODE_IN_CORE`, `BACKGROUND_DAEMON_WITHOUT_SEPARATE_GOAL`. These appear in the Capability Ledger with status REJECTED and a preserved reason; future goals must recover and respect them.
