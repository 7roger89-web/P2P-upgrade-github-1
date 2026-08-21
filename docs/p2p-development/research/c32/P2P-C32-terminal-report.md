<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# P2P-C32 Terminal Report — Hermes Deep Architecture Audit + Bounded AutoPilot Architecture Intake

**Goal ID:** P2P-C32 · **Mode:** LARGE RESEARCH + ARCHITECTURE · **Terminal verdict: PASS / AUTOPILOT_ARCHITECTURE_READY**

Prepared 2026-08-17 (sandbox, GMT+7). Research-only Goal: no implementation, no Hermes integration, no merge, no promotion, no deploy, no C31 retry. All research artifacts live in `/home/ubuntu/c32_research/` and the research branch `p2p-c32-hermes-audit` (created at `40d9441`, nothing pushed).

---

## 1. Recovered P2P state

Recovered from Git evidence in a fresh authenticated clone of the authoritative repository (`7roger89-web/P2P-upgrade-github-1`, private; user `7roger89-web`; pushable). Stacked lineage verified commit-by-commit: `main` (bda3e22) → `p2p-c25-charter-ledger` (20867a4) → `p2p-c26-capability-provenance` (1739b72) → `p2p-c27-real-host-certification` (32e002d) → `p2p-c28-secure-onboarding` (5f9bc6f) → `p2p-c29-goal-closure-integrity` (90df897) → `p2p-c30-composable-execution-target` (2eaceeb) → `p2p-c31-live-host-certification` (40d9441). All eight goals have open, unmerged PRs (#1–#7; #6 = C30, #7 = C31), so no state was lost — the stack simply remains unmerged.

## 2. C31 blocker preserved

C31 head commit `40d9441` carries an **honest BLOCKED / OWNER_ACTION_REQUIRED** verdict; the durable probe evidence `evidence/c31_live_probe.json` (fresh, zero-model-contact, 2026-08-17T06:14Z) records Codex CLI 0.147.0 returning **HTTP 401 before model contact (AUTH_INVALID)** against its hardcoded `api.openai.com` endpoint, and the Manus path as **AUTH_CONFIG_ABSENT**. The blocker is durably evidenced, not UNKNOWN. C31 was **not** retried; no `codex login` was requested, per instruction.

## 3. Hermes upstream SHA/version

NousResearch/hermes-agent, tag **`v2026.8.16`** (release **v0.20.2**, "chore: release v0.20.2 (2026.8.16)"), commit **`df4b65147d7ddd74dd449f9067aabbca5aef0ec7`** (2026-08-16T17:24:30Z). Repository HEAD at retrieval was `8f97ae9a` (2026-08-17T07:27Z); the pinned tag was chosen as the auditable release point. Retrieved 2026-08-17T07:41Z via the GitHub API tarball (git transport was rate-limited at 429; a user-supplied PAT succeeded).

## 4. License

**MIT License**, Copyright (c) 2025 Nous Research (`LICENSE` at repo root). MIT permits reuse; this Goal deliberately adopted only patterns/vocabulary/contract observations and copied **no implementation code** into P2P, so license exposure is negligible. Runtime dependencies of Hermes (Python/Node ecosystem: provider SDKs, Playwright for browser tools, optional MCP servers) remain Hermes's problem, not P2P's canonical surfaces.

## 5. Source areas inspected

Real source inspection (not README): `agent/conversation_loop.py` (8125 ln), `agent/agent_init.py` (2934), `agent/tool_executor.py` (2683), `agent/moa_loop.py` (2453), `agent/prompt_builder.py` (2452), `agent/conversation_compression.py` (4329), `agent/context_compressor.py` (7858), `agent/context_engine.py` (489), `agent/subagent_lifecycle.py` (540), `agent/codex_runtime.py` (1572), `agent/relay_runtime.py` (1622), `agent/background_review.py` (1376), `agent/memory_manager.py` (1291), `agent/estop.py`, `agent/iteration_budget.py`, `agent/retry_utils.py`, `agent/trajectory.py`, `agent/oneshot.py`, `agent/coding_context.py`, `agent/file_safety.py`, `agent/redact.py`, `agent/think_scrubber.py`, `agent/usage_pricing.py`, `agent/credits_tracker.py`, `agent/model_metadata.py`, `agent/transports/{base,anthropic,chat_completions,bedrock,codex,codex_responses,gemini_native,vertex,azure_identity,plugin_llm,lmstudio_reasoning,relay_llm,moonshot}.py`, `agent/monitoring/{emitter,events,otlp_exporter,redaction}.py`, `agent/secret_sources/`, `cron/{scheduler,jobs,lifecycle_guard,monitor}.py`, `acp_adapter/{server,permissions,edit_approval,provenance}.py`, `cli.py`, `batch_runner.py`, plus grep-verified evidence at cited line numbers (`conversation_loop.py:1830`, etc.). No claim below rests on marketing text.

## 6. Architecture findings

Hermes is a mature, single-session-first harness: one large `ConversationLoop` with iteration/time budgets (default 500; subagent default 50, per `iteration_budget.py`); session dirs with append-only `messages.jsonl` transcripts as its durable artifact; an abstract transport layer (`transports/base.py`) with 13 provider implementations; a typed subagent lifecycle contract v1 (HMAC-signed launch requests, explicit state enum, compacted summaries); a massive context-compression subsystem with deterministic prompt-cache markers; credential-reference-only secret handling with no secrets in prompts; an approval permission model with an escape-hatch flag (`--dangerously-skip-permissions`); a pause-new-work ESTOP sentinel; structured JSON event streams; live token/cost accounting; and a cron system with lifecycle guards. Critically for P2P: its provider-fallback chain (`relay_llm.py`/`relay_runtime.py`) is implicit automatic routing, and its resume model is transcript-based — both conflict with P2P invariants and were classified accordingly.

## 7. Hermes → P2P capability matrix summary

Full 36-row matrix in deliverable B (`deliverable_B_C_matrix_and_feasibility.md`). Summary counts: **ALREADY_COVERED (concept)** 11 (memory, skills, progressive disclosure, provider/model abstraction, MCP separation ET8, file ops, tool registry concept); **P2P_SHOULD_OWN** 6 (loop orchestration, terminal execution, workspace contract, safety governance, task state, provider abstraction semantics); **ADAPT_PATTERN** 14 (subagent contract, summaries, budgets/retry, compaction, cache markers, ESTOP semantics, error classification, observability, cost tracking, lifecycle guard, approval model, progressive disclosure implementation, context budgets); **REJECT** 6 (implicit routing/relay, transcript-as-state resume, skip-permissions default, unrestricted git mutation, background daemon autonomy, transcript resume); **GAP (design target)** 10; **FUTURE_OPTION** 4 (browser, cron, messaging, gateway); **REUSE_AS_BACKEND** 1 (headless/CLI surface, qualifying Hermes as a backend candidate).

## 8. Features P2P should own

The complete control plane: durable Goal/task state and ledger, the AutoPilot loop itself, continue/owner-gate policy, all budgets, the verifier, evidence persistence, target eligibility/fingerprint/drift/certification machinery, the registry boundary, and governance. P2P's state must never be a transcript, and its gates must never depend on harness-optional safety.

## 9. Features P2P should reuse

The execution engine behind the C30 contract: terminal/shell execution, tool registry, shell profiles, context management and compression, memory store, skills loading, browser tools, cancellation/ESTOP patterns, token/cost accounting — all of it accessed through a harness adapter that implements the structured headless contract. `HERMES_BACKEND_PROMISING` (qualified) — see item 12.

## 10. Patterns to adapt

Child-task contract style from `subagent_lifecycle.py` (typed launch request, state enum, artifact-carrying summary); slide-window + summary retention compaction scoped to individual tasks; deterministic prompt-cache markers emitted by the adapter; pause-new-work ESTOP semantics for owner stop/pause; error classification with bounded retry; per-task budget injection; evidence-pointer-first context rebuilding on any restart.

## 11. Rejected patterns

Implicit provider routing (`relay_llm`/`relay_runtime` fallback chains — the exact pattern behind P2P's REGISTRY != ROUTER invariant); transcript-based resume (P2P resumes from durable state + verification); unbounded/background autonomy (daemon gateway, cron-for-autonomy, background review as autonomy); `--dangerously-skip-permissions`-style single-flag safety defeatability as a governance default; swarm behavior; unverified git mutation without scope gates.

## 12. Hermes backend feasibility

**`HERMES_BACKEND_PROMISING`** (qualified). P2P can call Hermes through its CLI/headless surface (`cli.py -p`, event stream, exit status, session identity, workspace binding, permission config, model selection, SIGINT cancellation, `IterationBudget` bounds) with zero Hermes-specific logic in P2P core. The minimal adapter: one harness profile + one module translating the C30 execution contract to a CLI invocation, normalizing JSON events into P2P evidence, injecting and enforcing budgets, forwarding cancellation, and harvesting artifacts. C30 fields Hermes provides directly: harness/provider/model identity, protocol, toolset enumeration, workspace identity, permission policy, health probe, exit status, structured events — enough for `fingerprint()` today. Adapter-derived: capability evidence honesty, auth-state evidence (via P2P's own C31 model — keeping the C31 blocker honest), health ladder, freshness, drift detection. It materially reduces engine build effort while keeping every governance surface P2P-owned. Risks: fast upstream churn (pin + re-certify), routing temptation, transcript-state seduction, optional safety, MIT-license pattern discipline (honored — no code copied). Secondary candidates: Codex CLI and Manus remain blocked by the preserved C31 evidence; other open-source harnesses are future candidates behind the same contract.

## 13. Proposed minimal adapter boundary

`HermesExecutionBackendAdapter` (design only): (1) contract→CLI invocation; (2) event-stream normalization; (3) exit-status mapping; (4) cancellation/pause forwarding; (5) adapter-layer budget enforcement; (6) artifact harvesting for verification. Estimated surface: one profile record + one module; no core change. Full detail in deliverable C.

## 14. Bounded AutoPilot architecture

Twelve components (D.2): Goal State Store (C11-style atomic fail-closed), bounded Task Planner, Continue Gate (pure function), Preflight Runner (C30 eligibility), deterministic Target Selector (no ranking), Contract Builder, Backend Adapter, Verifier, Evidence Persister, Budget Controller, Owner-Gate Publisher (ESTOP-style quiescence), Recovery Observer. The core loop: DURABLE GOAL STATE → SELECT NEXT SAFE TASK → CHECK DEPENDENCIES → PREFLIGHT → SELECT/VALIDATE EXECUTION TARGET → BUILD EXECUTION CONTRACT → EXECUTE → VERIFY → PERSIST EVIDENCE → TRANSITION TASK STATE → REASSESS → CONTINUE OR STOP, with stop states DONE/BLOCKED/BUDGET_BOUNDARY/OWNER_GATE/FAILURE. The only AI in the loop executes individual bounded tasks; all gating is pure code over durable state — chat/session history is never the durable state. Full detail in deliverable D.

## 15. Next-safe-task semantics

A task is next-safe when: it belongs to the approved Goal's plan (scope-checked), its predecessors are DONE with acceptable evidence, it is actionable under current permissions and eligible targets, it introduces no scope expansion, no destructive production action, no merge/release/deploy/promotion, no secret/login dependency, no evidence conflict — and budget and retry limits remain. If all hold, continue; if any fail with an owner-remediable path, Owner Gate; if none exists, BLOCKED.

## 16. Continue policy

Fourteen deterministic gates (machine-readable schema, version 1, in deliverable E.1): TASK_IN_APPROVED_GOAL, DEPENDENCIES_SATISFIED, PRIOR_TASK_EVIDENCE_ACCEPTABLE, NEXT_TASK_ACTIONABLE, PERMISSION_SUFFICIENT, TARGET_ELIGIBLE, NO_UNRESOLVED_OWNER_DECISION, NO_SCOPE_EXPANSION, NO_DESTRUCTIVE_PRODUCTION_ACTION, NO_MERGE_RELEASE_DEPLOY_PROMOTION, NO_SECRET_LOGIN_DEPENDENCY, NO_EVIDENCE_CONFLICT, BUDGET_REMAINING, RETRY_LIMITS_REMAINING. **CONTINUE iff all 14 pass.** When all pass, P2P must not ask "Do you want to continue?" — asking in that state is itself a governance defect.

## 17. Owner Gate policy

Exactly ten reason classes (deliverable E.2): product/business choice; real-world facts unavailable to P2P; credential/login (never keys in chat, per C31 pattern); permission elevation (ET16 never-widens); destructive production action; payment/financial commitment; merge; release; deploy; promotion (four hard gates, separately declared); major scope change; conflicting evidence; architecture choice with no defensible default. Technical choices with sufficient evidence remain internal to P2P. Every gate message is product-level: what completed, what is next, why the gate exists, exact question, concrete options.

## 18. Execution budgets

Nine dimensions with auto-chosen beginner defaults (owner-opt-in for tuning): max internal tasks per run (wave-based, e.g. dependency-bounded waves of 5–10 with a per-run ceiling), wall-clock budget, retry budget (per-task, e.g. 3 bounded attempts), model/token/cost budget (adapter-supplied accounting, aggregate beginner-visible), changed-file/workspace scope per task, dependency depth, concurrent agents (default 1 executor + 1 verifier; risk-class scaling per item 19), verification budget (verify-command cost ceiling). Budget exhaustion → honest BUDGET_BOUNDARY with a precise resume point.

## 19. Adaptive agent/quorum recommendation

`Task != Agent` and `8 canonical agents != run all 8 for every task` — confirmed by the audit (Hermes has no quorum concept; its delegation is budget-scoped subagents). Policy: simple deterministic task → 1 executor; material code change → executor + 1 verifier agent; high-risk architecture/security → executor + verifier + 1–2 named specialists (e.g. `p2p_architecton`, `p2p_anon`) with a broader quorum slice; agent count is a task-contract field defaulted by the task classifier, evidence-driven, Owner-overridable, never scaled down by cost without Owner input. Quorum participation means a deterministic evidence-review pass, not a live chat seat on trivial tasks. No swarm behavior this Goal.

## 20. Context strategy

Nine elements (deliverable, item 11): progressive disclosure with section budgets; filesystem/context offloading with path pointers; token-bounded project/repo map refreshed per wave; task-targeted retrieval from contract-declared scopes; evidence pointers instead of transcripts; child-result summaries with artifact refs; deterministic cache-boundary markers emitted by the adapter; freshness-stamped slices that re-verify instead of silently using stale data; deterministic-first checks that never enter the LLM at all. Quality over token minimization: remove waste, never correctness.

## 21. Recovery semantics

Any failure (model call, rate limit, executor crash, session close, restart, context exhaustion, child failure, verification failure, target unhealthy, auth expiry) maps to a classified response table (deliverable, item 12): retry within budgets, wave pause on rate limits, task → `VERIFYING/UNKNOWN-NEEDS-REVIEW` (never auto-resume) on crashes/restarts, task re-granularization on context exhaustion, FAILED transitions on retried-then-failed verification, Owner Gate on blocking dependencies or INELIGIBLE_AUTH. Durable Goal/task state is written only at checkpointed transaction boundaries, so the ledger is always consistent after any executor or session failure; resumption is always from state + verification, never from conversation history; every branch is provider-agnostic (all probes adapter-dispatched).

## 22. Provider-switching boundary

Provider-neutral = represent/certify/use any conformant backend, never silently switch. Seven separated concerns: registry (enumerate only), eligibility (deterministic code), certification (health/fingerprint/drift, Owner-visible), selection policy (default = current certified target; Owner override wins), fallback policy (deferred — new governed goal), Owner policy (pin any target, always), routing (explicitly rejected this Goal). Hermes's `relay_llm`/`relay_runtime` is the exhibited counter-example. Until a governed selection goal exists, the rule is one deterministic line: run the current certified target or gate to the Owner if none eligible.

## 23. Beginner impact

The Owner eventually says "Tiếp tục hoàn thiện dự án Logistics." and receives only product-level state: what completed, what remains, where P2P stopped, and whether input is required — with concrete, non-technical options at every Owner Gate. Providers, models, harnesses, context, retries, agents, and quorums are invisible unless troubleshooting is requested. Budget shown as simple labels with technical detail opt-in. The research shows this experience is now architecturally buildable on existing C30 machinery plus one adapter.

## 24. Roadmap redesign

Recorded as a **proposal** (canonical roadmap unchanged; roadmap edits require a goal, and this research Goal is not authorized to rewrite it). Old sequence: C32 beginner control center → C33 context/cache → cross-host → … Proposed AutoPilot-first sequence: C33 AutoPilot core loop → C34 first-backend adapter (Hermes behind C30 contract) → C35 continue/owner-gate beginner UX → C36 context/caching layer (measured against a real backend) → C37 governed selection/fallback policy → cross-host deferred. Rationale: the beginner control center and cache work both serve the loop; building the differentiating capability first on machinery that already exists (C11/C12/C25–C31/C30) and layering UI/optimization on measured reality is strictly better sequencing. The preserved C31 blocker (Codex AUTH_INVALID 401; Manus AUTH_CONFIG_ABSENT) remains a documented precondition for any Codex-path backend.

## 25. Tests/validators

Focused governance suite at C31 head (`40d9441`): **83 passed, 2 skipped** (development_control, goal_closure, c31_live_certification). Full suite: 635 passed / 9 failed / 5 skipped / 105 subtests — the 9 failures are classified as environment/fixture artifacts, not regressions: seven secure-onboarding tests fail only because this sandbox has no `codex` binary (the C31 session's sandbox had codex 0.147.0; machinery correctly reports NOT_INSTALLED/AUTH_CONFIG_ABSENT with the durable state preserved — reproduced and verified as correct per contract); two tests (`test_t18`, `test_current_suite_has_real_recorded_trial_pairs`) reference fixture files missing on **every** branch in the lineage (pre-existing fixture gap). Closure checker on C31 head: `Goal C28: CONSISTENT`, all claim boundaries PASS. No tests weakened; no new tests fabricated for research-only changes.

## 26. Governance/ledger delta

**None.** No governance file, ledger record, roadmap item, or manifest was created, modified, or deleted in the P2P repository. The working tree is clean (`git status`: 0 changes); the research branch `p2p-c32-hermes-audit` exists locally only, unpushed, containing no committed research artifacts (research outputs live outside the canonical surface, in `/home/ubuntu/c32_research/`). The roadmap redesign and all proposals are durable research artifacts for the next implementation Goal's Owner decision, not canonical changes.

## 27. Candidate policy result

Per the deterministic candidate policy self-applied: no release candidate was fabricated — research-only changes produced no code delta to candidate, and existing policy requires a candidate only for code/promotion changes. Official promoted baseline remains immutable: **8.4.7-C-codex.19** (SHA `3a9ee513…`, `PROMOTED_VERIFIED`, approval `P2P-APR-20260815T013545Z-0068b3047f`), verified directly from `governance/development-control.json`; the C30 candidate `.24` remains **UNPROMOTED** (`C30 → UNPROMOTED` in candidate records; `8.4.7-C-codex.24` appears only as the current-development VERSION on the C30 lineage). No promotion of any kind occurred.

## 28. Exact next implementation Goal recommendation

**P2P-C33: Bounded AutoPilot core loop.** Build the D.2 component set as research-derived machinery: Goal State Store + task ledger (extending C11's store), Continue Gate with the 14-gate contract, Owner-Gate publisher, Budget Controller (9 dimensions), Task Planner (wave-based, scope-checked), Verifier integration, Evidence Persister, Recovery Observer — with a **non-runtime interface probe** (adapter design validation against the real Hermes CLI contract, e.g. a dry-run invocation proving event normalization and budget injection) as the only prototyping allowed. Exit criteria: loop runs end-to-end on a synthetic task plan with zero Owner-visible technical leakage, all 14 gates verifiable by tests, no router, no silent switching, transcript never state. C31 unblocking (Owner action: Codex login outside chat, or Manus connector enablement) is a parallel owner-condition for any Codex-path backend but is **not** a dependency for the C33 loop itself, which is provider-neutral by construction.

---

## Terminal rule

After PASS: **STOP.** The AutoPilot was not implemented; Hermes was not integrated; the next Goal was not started; C31 was not retried; nothing was merged, promoted, or deployed. Awaiting Owner review.
