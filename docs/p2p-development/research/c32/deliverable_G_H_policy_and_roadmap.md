<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# Deliverable G — Updated P2P Roadmap Proposal
# Deliverable H — Build-vs-Reuse Decision
# Plus: items 13 (provider-switching boundary), 10 (adaptive agent count), 11 (context strategy), 12 (recovery model), 14 (beginner experience)

---

## 13. Provider-Switching Boundary (what "provider-neutral" means)

Provider-neutral means: P2P represents, certifies, and *can* use any conformant execution backend — but P2P never silently switches because another provider merely exists. The boundary separates seven concerns that must not be conflated in one mechanism:

| Concern | Owner | Who decides | C30 anchor |
|---|---|---|---|
| **Registry** | List of known harness/provider/model profiles | P2P machinery (enumerate only) | `REGISTRY != ROUTER` (ET24–ET32) |
| **Eligibility** | Deterministic `ELIGIBLE/INELIGIBLE_*/UNKNOWN` per task requirements | Pure code | `evaluate_execution_target()` |
| **Certification** | Health ladder, fingerprint, drift state per target | Adapter + machinery, Owner-visible | drift fail-closed (ET26/ET36) |
| **Selection policy** | Which eligible target runs a task | P2P default = current certified target; Owner override | no ranking (ET24–ET32) |
| **Fallback policy** | What happens when the chosen target fails mid-task | Later, separately designed, governed, bounded, testable | deferred — NOT in this Goal |
| **Owner policy** | The Owner may always pin a specific target | Owner wins, always | beginner-first boundary |
| **Routing** | Automatic dynamic dispatch to the "best" provider | **Not present; explicitly rejected for this Goal** | C30 invariant |

Hermes's `relay_llm.py`/`relay_runtime.py` is the canonical example of what P2P rejects as a default: capability-based automatic fallback routing. The proposal: an AutoPilot-level *selection policy* may later be designed as its own goal (registry + eligibility + certification already exist in C30; only selection/fallback are new surfaces), with evidence-based triggers, Owner opt-in, and bounded trials. Until then: one deterministic rule — run on the current certified target, or gate to the Owner if none eligible.

## 10. Adaptive Agent Count (Task != Agent)

Hermes audit: one agent loop per task, optional subagents with independent budgets (50 default); Hermes has no quorum concept. P2P canonical agents (8, quorum 8/8: `p2p_iris, p2p_tecton, p2p_axiom, p2p_vector, p2p_datos, p2p_anon, p2p_architecton, p2p_helios`; `p2p_aesthetica` optional) are **governance/verification roles, not execution workers**. The audit confirms the hypothesis `Task != Agent` and `8 canonical agents != run all 8 for every task`:

| Task class | Execution count | Verification/quorum | Rationale |
|---|---|---|---|
| Simple deterministic task (doc, config, small refactor) | 1 executor | 1 verifier (deterministic checks) | Extra agents add cost, no evidence benefit |
| Material code change | 1 executor + 1 verifier agent | verifier + tests/lint/diff scope | Evidence value justifies cost |
| High-risk architecture/security task | executor + verifier + 1–2 named specialists (e.g. p2p_architecton for design, p2p_anon for security review) | broader quorum slice | Risk-weighted; only when evidence justifies |
| Anything else | default 1+1 | — | Evidence must justify scaling up; never down |

Policy rules: quorum participation is *evidence-driven* (triggered by risk class in the task contract), participation means a deterministic review pass over artifacts, not a live chat participant for trivial tasks; agent count is a task-contract field defaulted by the task classifier, overridable by Owner. No swarm behavior implemented this Goal.

## 11. Context Strategy (quality > token minimization)

Combine Hermes findings with C30/C32 invariants. The strategy removes waste without reducing correctness:

1. **Progressive disclosure** — sections enter context only when relevant (Hermes `context_engine.py` budgeting; P2P `PROJECT_MAP` token-bounded map).
2. **Filesystem/context offloading** — file contents live on disk, referenced by path pointers; never inlined wholesale. P2P invariant since C11.
3. **Project/repo map** — token-bounded index + relations + budget (C30 `PROJECT_MAP` ledger extension); refreshed per wave, not per turn.
4. **Task-targeted retrieval** — each task contract declares its relevant scopes; retrieval is scoped, not whole-repo.
5. **Evidence pointers over transcripts** — prior-task evidence refs (tool results, verifier outputs, diff summaries) replace raw chat history; transcripts may be kept as optional evidence-of-execution only.
6. **Child-result summaries** — subagent/child-task returns are structured summaries with artifact refs (`turn_summary.py` pattern adapted).
7. **Cache-aware context** — deterministic cache boundary markers for stable front-of-context material (Hermes `prompt_caching.py`); P2P adapter emits markers for backend providers that honor them.
8. **Freshness** — context slices stamped with observation time; stale slices trigger re-verification rather than silent use (pairs with `FRESHNESS` eligibility dimension).
9. **Deterministic-first checks** — any question answerable by deterministic code (tests, git, diff scope, schema validation) never enters the LLM context at all.

## 12. Failure / Recovery Model

| Failure | Detection | Response |
|---|---|---|
| Model call fails | Adapter exit/event observation; `error_classifier` pattern | Retry within retry budget → task FAILED beyond budget |
| Provider rate-limit | Adapter normalizes 429 events | Exponential backoff inside retry budget; budget controller pauses wave; never silent infinite retry |
| Executor crashes | Adapter heartbeat/exit-status; process absence | Task state stays `VERIFYING/UNKNOWN-NEEDS-REVIEW`; Goal state untouched; next reassessment re-verifies rather than resumes |
| Session closes | Adapter session-loss observation | Same as crash; transcript is not state (C11) — no data loss by construction |
| Computer restarts | Absence; Recovery Observer on boot | Re-reads Goal State Store; in-flight task → re-verify (snapshot + verifier), then continue/stop per gates |
| Context exhausted | Adapter reports compaction limit | Task re-granularized (split into subtasks with fresh sessions); scope preserved via evidence pointers |
| Child task fails | Verifier exit code | Retry budget → task FAILED; wave reassessment; Owner Gate only if blocking dependency |
| Verification fails | Verifier output | Never auto-retry on verification failure without new evidence; FAILED → Owner Gate if retried-then-failed |
| Target unhealthy | Health ladder tick < required | Target ineligible; selection rule finds no eligible target → Owner Gate (no automatic switch) |
| Authentication expires | Auth-state probe (C31 pattern; bounded-recheck freshness) | INELIGIBLE_AUTH; honest evidence persisted; Owner Gate with the exact outside-chat action |

Core guarantee: durable Goal/task state is written only at transaction boundaries (checkpointed transitions), so any executor/session failure leaves the ledger consistent; the system always resumes from state + verification, never from conversation history; no provider assumption in any branch (all probes are adapter-dispatched).

## 14. Beginner Experience

Target interaction: Owner says **"Tiếp tục hoàn thiện dự án Logistics."**

P2P replies only with product-level state, in this fixed shape:

> **Hoàn thành:** 3 task (mô tả sản phẩm).
> **Còn lại:** 12 task trong mục tiêu Logistics.
> **Đang dừng ở:** task 4 — chờ bạn chọn giữa A/B (mô tả ngắn bằng ngôn ngữ sản phẩm).
> **Cần bạn:** chọn A hoặc B; không cần hiểu về provider, model, hay kỹ thuật.

Rules: (1) routine provider/model/harness/context/retry details are hidden unless the Owner enters troubleshooting mode (`p2p chẩn đoán`); (2) every Owner Gate is phrased as a product decision with concrete options; (3) budget state shown as simple labels ("còn nhiều pin cho hôm nay" style) with technical detail opt-in; (4) the beginner never sees agents, quorums, or routes — agent-count policy and provider switching are entirely internal.

## G. Updated P2P Roadmap Proposal

**Recorded as a proposal only** — canonical roadmap unchanged per governance (§22/§23: roadmap edits require a goal; this research Goal is not authorized to rewrite it). The proposal is durable evidence for the next implementation Goal's Owner decision.

**Old sequence (current roadmap direction):** C32 beginner control center → C33 context/cache → cross-host → ...
**Proposed AutoPilot-first sequence:**

| # | Proposed goal | Why now | Depends on |
|---|---|---|---|
| 1 | **C33-AutoPilot core loop** (this report's architecture) | The single largest beginner-value capability; everything else (control center, context, cross-host) serves it; C30 machinery makes it buildable now | C30 (PASS), C31 evidence (BLOCKED, owner-condition documented) |
| 2 | **C34-first-backend adapter** (Hermes behind C30 contract) | `HERMES_BACKEND_PROMISING` (qualified); removes most engine build effort; validates the whole contract with a real harness | C33 |
| 3 | **C35 continue/owner-gate UX** (beginner control surface) | The "beginner control center" idea, now grounded in a real loop + real backend; strictly better built after the loop exists | C33, C34 |
| 4 | **C36 context/caching layer** (original C33 idea) | With a real backend, cache-aware context + wave-level repo map can be measured, not guessed | C34 |
| 5 | **C37 selection/fallback policy** (explicit goal, new governance surface) | Only after real multi-target evidence exists; governed, bounded, Owner opt-in | C34+, real evidence |
| 6 | Cross-host | Deferred; no beginner evidence need today | — |

Rationale: the old sequence front-loaded infrastructure and UI before a loop existed to use them. The proposed sequence builds the differentiating capability (bounded autonomous continuation) first on machinery that already exists (C11/C12/C25–C31/C30), then layers UI and optimization on measured reality. Risks of reordering: owner effort on C31 must still be a precondition for any Codex-path backend (kept as documented blocker); no capability in the old sequence is deleted, only re-sequenced.

## H. Build-vs-Reuse Decision

| Action | Components |
|---|---|
| **Build (P2P-owned)** | AutoPilot core loop (D), Goal State Store + task ledger, Continue Gate (E.1), Owner-Gate publisher (E.2), Budget Controller (9 dimensions), Verifier integration, Evidence Persister, Recovery Observer, task classifier + agent-count policy (10), context strategy (11), backend adapter interface (C30 contract extension) |
| **Reuse** | Hermes as execution backend candidate behind the adapter (terminal engine, tool registry, shell profiles, context management/compression, memory, skills loading, cancellation/ESTOP semantics, token accounting); C30 machinery already reused by design (eligible_targets, fingerprint, drift) |
| **Adapt (pattern-level)** | Subagent public-contract style (child task contracts), slide-window + summary compaction inside tasks, cache-boundary markers, pause-new-work semantics, error classification + bounded retry, lifecycle-guard style scheduling (if cron ever added) |
| **Defer** | Fallback/selection policy (C37), browser/web tools, messaging gateway, cron/background jobs, cross-host, quorum-at-scale |
| **Reject (this Goal and defaults)** | Implicit provider routing (`relay_llm`/`relay_runtime` pattern), transcript-as-durable-state resume, background daemon autonomy, unbounded execution, `--dangerously-skip-permissions`-style defeatable safety as a governance default, swarm behavior |

No Hermes code is copied into P2P in this Goal; all adoption is pattern/vocabulary level, consistent with the research-only constraint.
