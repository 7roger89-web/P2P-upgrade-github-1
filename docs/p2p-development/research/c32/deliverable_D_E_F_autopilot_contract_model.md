<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# Deliverable D — Bounded AutoPilot Architecture (provider-neutral)
# Deliverable E — Continue / Stop / Owner-Gate Contract
# Deliverable F — Large-Goal Execution Model (300 EP / one large request)

Built on: C11 durable task state, C12 bounded foreground execution, C25–C31 governance, C30 composable execution targets + headless contract + task workspace isolation + contract-drift fail-closed, and the Hermes audit evidence (source: `v2026.8.16`, commit `df4b6514`).

---

## D. Bounded AutoPilot Architecture

### D.1 Principle
AutoPilot is **not an agent**. It is a deterministic orchestration layer with an LLM-backed execution backend behind the C30 contract. The only AI in the loop executes *individual bounded tasks*; all selection, gating, and transition logic is pure code over durable state. This preserves P2P's invariants: no router, no silent provider switching, state ≠ chat history, UNKNOWN fails closed.

### D.2 Components
1. **Goal State Store** (`p2p_autopilot_state.json` + append-only `task-ledger.jsonl`, mirroring C11's atomic fail-closed store): one approved Goal record (id, scope statement, owner-approved task plan or dynamically decomposed plan, budgets, status, resume pointer to current task). Survives executor, session, and computer failure because the executor reads and writes it only through checkpointed transitions.
2. **Task Planner (bounded)** — invoked at Goal approval and at each reassessment: decomposes the approved Goal into the next wave of candidate tasks using the existing project map + durable evidence. Planner output is always validated against scope (no scope expansion without Owner Gate).
3. **Continue Gate** — pure function over state (see E).
4. **Preflight Runner** — reuses C31/C28 machinery: eligibility `evaluate_execution_target()` per C30, health ladder, freshness, auth state, budget headroom.
5. **Target Selector** — deterministic precedence over `eligible_targets`: current-certified target first; no ranking heuristics, no fallback chains (REGISTRY != ROUTER). If no target eligible → Owner Gate.
6. **Contract Builder** — assembles the structured headless contract: task spec, allowed ToolSet, workspace binding, snapshot requirement, verification command, budget injection, permission profile.
7. **Backend Adapter** — per `HERMES_BACKEND_PROMISING` (qualified), a harness adapter (e.g. Hermes CLI) implements the execution contract; P2P core stays backend-agnostic. Adapter normalizes events, enforces adapter-level budgets, forwards cancellation, harvests artifacts.
8. **Verifier** — runs the task-declared verification command + deterministic checks (tests, lint, diff scope, evidence integrity). Verification failure is a task state transition, not an AutoPilot crash.
9. **Evidence Persister** — writes evidence refs (tool-result bundles, exit code, verifier output, fingerprint deltas) into the ledger; transcripts optional as *evidence-of-execution*, never state.
10. **Budget Controller** — thread-safe consumption of all budget dimensions (F); blocks new tasks when any dimension exhausted → bounded stop.
11. **Owner-Gate Publisher** — emits the exact human-readable ask from E.2; AutoPilot is quiescent (ESTOP-style pause-new-work) until response.
12. **Recovery Observer** — on restart, re-reads Goal State Store; in-flight task marked `VERIFYING` or `UNKNOWN-NEEDS-REVIEW`; never blindly resumed (transcript resume rejected).

### D.3 Core loop
```
DURABLE GOAL STATE
→ SELECT NEXT SAFE TASK        (planner wave + dependency ordering)
→ CHECK DEPENDENCIES           (task ledger: predecessors DONE with acceptable evidence)
→ PREFLIGHT                    (C30 eligibility, health, freshness, auth, budget headroom)
→ SELECT/VALIDATE EXECUTION TARGET  (eligible, non-ranked, drift-checked)
→ BUILD EXECUTION CONTRACT     (spec, ToolSet, workspace snapshot, verify cmd, budget)
→ EXECUTE                      (backend adapter; bounded; cancellable; ESTOP-able)
→ VERIFY                       (declared verification + deterministic checks)
→ PERSIST EVIDENCE             (ledger append; evidence refs; fingerprint deltas)
→ TRANSITION TASK STATE        (atomic fail-closed state update)
→ REASSESS                     (remaining tasks, budgets, gates)
→ CONTINUE OR STOP             (see E)
```
Stop states: DONE (all tasks done), BLOCKED (any gate fails with no owner-remediable path documented), BUDGET_BOUNDARY, OWNER_GATE, FAILURE (unrecoverable error; logged, quiescent).

---

## E. Continue / Stop / Owner-Gate Contract

### E.1 Machine-readable direction (schema sketch)
```json
{
  "decision": "CONTINUE | STOP | OWNER_GATE | VERIFYING | BUDGET_BOUNDARY",
  "direction_version": 1,
  "continue_conditions": [
    {"gate": "TASK_IN_APPROVED_GOAL", "pass": true},
    {"gate": "DEPENDENCIES_SATISFIED", "pass": true},
    {"gate": "PRIOR_TASK_EVIDENCE_ACCEPTABLE", "pass": true},
    {"gate": "NEXT_TASK_ACTIONABLE", "pass": true},
    {"gate": "PERMISSION_SUFFICIENT", "pass": true},
    {"gate": "TARGET_ELIGIBLE", "pass": true},
    {"gate": "NO_UNRESOLVED_OWNER_DECISION", "pass": true},
    {"gate": "NO_SCOPE_EXPANSION", "pass": true},
    {"gate": "NO_DESTRUCTIVE_PRODUCTION_ACTION", "pass": true},
    {"gate": "NO_MERGE_RELEASE_DEPLOY_PROMOTION", "pass": true},
    {"gate": "NO_SECRET_LOGIN_DEPENDENCY", "pass": true},
    {"gate": "NO_EVIDENCE_CONFLICT", "pass": true},
    {"gate": "BUDGET_REMAINING", "pass": true},
    {"gate": "RETRY_LIMITS_REMAINING", "pass": true}
  ],
  "stop_reason": null,
  "owner_gate": {
    "reason_class": null,
    "question": null,
    "options": null,
    "defaults": null,
    "blocking": false
  }
}
```
Rule: `decision = CONTINUE` iff **all 14 gates `pass`**. No partial truth, no "soft" continue. If all gates pass, P2P must NOT ask "Do you want to continue?" — it continues. Asking when all gates pass is itself a governance defect (it transfers a technical decision to the Owner).

### E.2 Owner Gate reasons (stop and ask — exactly these)
1. **Product/business choice** — feature direction, naming, prioritization not derivable from approved scope.
2. **Real-world fact unavailable** — account numbers, vendor choices, third-party facts P2P cannot verify from repo/evidence.
3. **Credential/login** — anything requiring owner action outside chat (per C31 pattern: never paste keys into chat; C31's AUTH_INVALID/401 evidence pattern must not be retried silently).
4. **Permission elevation** — new tool/capability class beyond the Goal-approved permission profile (ET16 never-widens).
5. **Destructive production action** — data deletion, irreversible infra change.
6. **Payment/financial commitment**.
7. **Merge / release / deploy / promotion** — four hard gates, each separately declared, each requiring Owner response (matches P2P candidate policy).
8. **Major scope change** — plan deviation beyond declared `scope_statement` tolerance.
9. **Conflicting evidence** — evidence refs contradict; no deterministic resolution.
10. **Architecture choice with no defensible default** — only when no evidence-based default exists; technical choices *with* sufficient evidence remain internal.

Human-readable Owner message format: what was completed, what is next, why the gate exists, the exact question, the concrete options, what happens on each answer. Never mentions providers/models/context/retry unless troubleshooting requires it.

---

## F. Large-Goal Execution Model (300 EP / one large request)

### F.1 Why a single LLM session cannot hold a 300-task goal
Hermes audit evidence: main-loop budgets (500 iterations) and compaction (`context_compressor.py` 7858 ln, `conversation_compression.py`) mitigate but do not eliminate late-session quality decay — summaries compress away detail, drift compounds, and repetition guards are heuristics. P2P's answer is structural, not prompt-level: **the Goal never lives in one context**.

### F.2 Model
1. **Goal record is small and durable.** The Goal is a scope statement + task plan (explicit or wave-by-wave decomposed) stored in the Goal State Store. Its "context" is a set of evidence pointers, never a transcript.
2. **Task granularity is the context unit.** Each task is one bounded execution contract; the backend session for a task starts fresh (or from its own task session), sized to the task, not the Goal. Task-level context uses: progressive disclosure, filesystem offload, project/repo map (token-bounded, C30 `PROJECT_MAP`), task-targeted retrieval, evidence pointers instead of transcripts, child-result summaries.
3. **Waves, not a queue into oblivion.** The planner emits *waves* (e.g. dependency-bounded batches). Between waves, AutoPilot re-verifies scope/budgets — this is where a 300-task Goal is continuously re-grounded instead of drift-carrying.
4. **Child-task isolation mirrors Hermes subagent semantics without the baggage.** Each task runs with its own workspace snapshot and budget; failure isolates to the task (task → FAILED, retry budget applies); the Goal state is untouched.
5. **State kept outside the LLM context:** durable task state (C11), evidence ledger, verifier outputs, budget counters, file snapshots. The LLM always re-reads what it needs from pointers.
6. **Cost/token accounting per task** (Hermes `usage_pricing.py`/`credits_tracker.py` pattern) feeds the per-wave budget controller; the Owner sees aggregate cost in the beginner UI, not per-token streams.
7. **Quality guardrails:** per-task verifier (tests/lint/diff-scope), post-wave evidence consistency checks, repetition/evidence-conflict gates → Owner Gate when evidence conflicts. Resumption is always from durable state + verification, never from "continuing the old conversation."
8. **Bounded by default:** even a 300-task Goal executes within the execution budget (default bounds in G); running out of budget produces an honest BLOCKED/BUDGET_BOUNDARY state with a precise resume point — the Owner's "Tiếp tục hoàn thiện dự án." continues from there.

### F.3 Mapping of Hermes mechanisms → P2P usage
| Hermes mechanism | P2P AutoPilot use |
|---|---|
| `IterationBudget` per agent (500/50) | Per-task + per-wave budget dimensions (G) |
| `context_compressor`/`conversation_compression` | Task-scoped context build (11) — compression inside tasks, never across the Goal |
| `subagent_lifecycle` contract | Child-task isolation + summary returns (evidence-carrying payloads) |
| `coding_context` profile budgets | Progressive disclosure + offload per task |
| `prompt_caching` deterministic markers | Cache-aware context (11) inside backend adapter |
| `repetition_guard` | Evidence-based duplicate-action gate in continue policy |
| `error_classifier` + bounded retry | Failure/recovery model (12) |
| `estop.py` pause-new-work | Owner stop/pause semantics — quiescent, not killed |
| `credits_tracker`/`usage_pricing` | Budget-evidence inputs |
| Transcript resume | **Explicitly rejected** — C11 state + verifier re-grounds every restart |
