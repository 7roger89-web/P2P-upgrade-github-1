# P2P_OPERATIONS_NOTEBOOK

Status: `CANONICAL_IN_DEVELOPMENT_SOURCE` (candidate, `UNPROMOTED`)
`CANONICAL_PROMOTED: NO`

This is the **single canonical operations notebook** for how a human
beginner, Control Tower, Arena Writer, Arena Supervisor, Codex, Manus, or
another supported executor operates a P2P-installed project. It is the
durable operating memory for P2P operations.

This document is documentation/operations-memory only. It does not grant
permissions, certify a live provider, approve a release, or replace Task
State, the execution ledger, evidence authority, the sole P2P router, or any
existing governance surface.

The mandatory execution discipline above this operations memory is the
[P2P Supreme Operating Law](P2P-SUPREME-OPERATING-LAW.md). Control Tower and
any prompt writer must read that law before writing each executor prompt.
Every P2P executor must read the installed law before execution, or receive
the exact canonical law text when the executor cannot access repository files.
This is a read preflight, not a compliance-reporting ceremony.
If this notebook or an older P2P operating rule conflicts with the current
Supreme Operating Law, the Supreme Operating Law controls that operating
decision unless a higher platform/safety/domain rule or explicit Owner
authority controls it.

## 1. Canonical status and authority shape

There is exactly one canonical logical artifact: `P2P_OPERATIONS_NOTEBOOK`.
No parallel operations notebook, manual, or handoff framework may be created
alongside it. When another artifact needs operating rules, it references this
notebook or the existing surfaces below; it does not maintain a divergent
copy.

```text
P2P_OPERATIONS_NOTEBOOK (this file)
        |
        +--> Control Tower operating guidance
        |      docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md
        |
        +--> Arena Writer/Supervisor operation
        |      docs/ARENA_AGENT_MODE_PROTOCOL.md
        |
        +--> installed-project entrypoint
               AGENTS.md (P2P block projected by installers)
```

The Arena-specific session contract lives in
`docs/ARENA_AGENT_MODE_PROTOCOL.md`; the Control Tower return/rotation
contract lives in `docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md`;
the installed-project digest lives in the `AGENTS.md` P2P block. This
notebook is the operations memory above them; it does not duplicate their
contracts.

## 2. Install inheritance law

```text
P2P_INSTALL => P2P_OPERATIONS_NOTEBOOK_ACTIVE_BY_DEFAULT
```

Every project receiving a normal P2P installation must receive/discover
these operating rules automatically. The existing installation surface is the
projection mechanism; nothing new is required:

- `install.sh` / `install.ps1` project the package `AGENTS.md` into the
  target project as the `<!-- BEGIN P2P CODEX --> ... <!-- END P2P CODEX -->`
  entrypoint block (`P2P-PROJECT-BOOTSTRAP.md` documents this entry
  contract). The inherited digest in that block names this notebook and the
  P2P_BEGINNER_OPERATIONS_UX_V1 / RULE_ASSIMILATION_GATE_V1 rule sets, so
  every installed project discovers them.
- Release packages ship the full notebook via
  `scripts/package_release.py` (`DOC_FILES`), so the canonical text travels
  with the release.
- Release packages also ship `P2P-SUPREME-OPERATING-LAW.md`; installers
  copy it to `.p2p/system/docs/P2P-SUPREME-OPERATING-LAW.md`. Missing the law
  is a fail-closed install condition.
- Example projects (APP GAME TRUYỆN, LOGISTICS, GIA PHẢ, future projects)
  are examples only. Nothing in this notebook or any runtime hard-codes
  them.

If the installed digest and this notebook ever differ, the notebook wins.

## 3. P2P_BEGINNER_OPERATIONS_UX_V1

Canonical beginner-safe operational rules. Every operational instruction
produced for a beginner must conform to these rules.

### RULE 01 — EXPLICIT_DESTINATION

Every operational instruction must explicitly identify:

- destination/tool
- `NEW CHAT` or `SAME CHAT`
- role where applicable

Examples:

```text
ARENA AI — CHAT MỚI — WRITER
ARENA AI — CHAT MỚI — SUPERVISOR
CODEX WINDOWS — SAME CHAT
00 — P2P CONTROL TOWER
```

The beginner must never infer where a prompt should go.

### RULE 02 — CHAT_TITLE_REQUIRED

Every new execution chat gets a recognizable title. Default shape:

```text
PROJECT | PR-or-TASK | ROLE | SHORT-GOAL
```

### RULE 03 — SAME_CHAT_MUST_NAME_CHAT

When instructing `SAME CHAT`, name the exact existing chat whenever known.
Do not merely say "go back to the old chat".

### RULE 04 — GITHUB_IS_DURABLE_CHECKPOINT

Chat/session state is temporary. GitHub/durable project state is the
execution checkpoint. Work identity is based on:

```text
REPOSITORY
+ WORKSTREAM
+ PR_HEAD_SHA
+ PR_HEAD_TREE
```

Do not use chat position or PR number alone as authority.

### RULE 05 — SESSION_OR_QUOTA_RECOVERY

If Arena/Codex/another executor loses context, resets sandbox, hits quota,
or a user changes account:

1. Do NOT restart the task blindly.
2. Return to Control Tower.
3. Inspect the current durable branch/PR/head.
4. Continue from the exact verified checkpoint where possible.

### RULE 06 — NO_DUPLICATE_PR

Before creating a PR for a workstream, inspect whether an active PR/branch
already represents that work. Same goal + usable open PR => continue it where
technically possible. Do not create duplicate PRs merely because the
execution chat changed.

### RULE 07 — WRITER_BOUNDARY

Normal Arena Writer unit:

```text
1 bounded goal -> 1 branch -> 1 PR
```

A new workstream or a closed PR normally requires a new Writer chat.

### RULE 08 — INDEPENDENT_SUPERVISOR

Supervisor review must be independent from Writer implementation. Default:

```text
NEW CHAT — SUPERVISOR
read/review only
no implementation edits
```

A bounded re-review of a corrected head may reuse the same Supervisor chat.

### RULE 09 — ONE_ACTION_NOW_FOR_BEGINNER

Beginner-facing instructions must clearly separate `LÀM BÂY GIỜ` (do now)
from later workflow, and give the user one immediate action — never force
them to choose between internal workflow alternatives.

### RULE 10 — SUCCESS_SIGNAL_AND_RETURN

Every execution instruction must state:

- what success looks like; and
- exactly what output/ReturnPacket the user must paste back to Control Tower.

The return contract fields are canonical in
`docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md`.

### RULE 11 — OWNER_GATE_ONLY_WHEN_REAL

Do not ask the Owner for routine technical decisions. Owner Gate is reserved
for meaningful authority boundaries such as:

- canonical merge/promotion
- production deployment
- destructive deletion
- secrets/credentials
- major paid infrastructure/spending
- hard rollback
- equivalent high-risk authority changes

`OWNER_MICRO_LOOP_SUPPRESSION` (assimilated from Issue #42,
CONTEXT_HYGIENE_01): a bounded finding and the repairs it directly induces —
fixture repair, focused test repair, evidence-count correction, remote-sync
correction — belong to the SAME bounded Writer repair loop. Do not relay each
micro-fix through the Owner. Escalate to the Owner only for the real Owner
Gates listed above, secrets, destructive actions, major spend/infrastructure,
hard rollback, or a genuine scope-changing blocker. This suppression
never removes or weakens a real Owner Gate; it only stops routine
micro-repair relays. Machine-readable classification:
`orchestration_policy.py` (`classify_owner_escalation`).

### RULE 12 — MINIMUM_SUFFICIENT_WORK

Default operating laws:

```text
MINIMUM_RELEVANT_CONTEXT
MINIMUM_SUFFICIENT_WORK
RISK_PROPORTIONAL_VERIFICATION
PROGRESS_REPORTING=EXCEPTIONS_ONLY
STOP_WHEN_EVIDENCE_SUFFICIENT
ANTI_OVER_ENGINEERING
CONTEXT_IS_CAPACITY_NOT_BUDGET
```

Do not expand a bounded task merely because more investigation is possible.
These laws are canonically stated in the `AGENTS.md` "Prompt and effort
efficiency" section and enforced by `orchestration_policy.py`
(P2P-EFF01); this notebook references them, it does not copy their full
semantics.

### RULE 13 — CONTROL_TOWER_STATE_RESPONSIBILITY

Control Tower, not the beginner Owner, tracks:

- current workstream
- branch
- PR
- SHA/tree
- review state
- Owner Gate
- next action

Do not make the beginner memorize internal Git state.

### RULE 14 — OVER_ENGINEERING_CHECK

Overengineering assessment is a decision rule, not a terminal ritual.

Before opening a new branch of work with meaningful cost, require one concrete
reason that the branch is needed for the current outcome, adequate verification,
or a material safety/recovery risk. If a simpler valid route reaches the same
required outcome with comparable acceptable risk, use the simpler route.

```text
UNPROVEN_SUPPORTING_INFRASTRUCTURE => DEFER
CEREMONY_THAT_DOES_NOT_CHANGE_A_DECISION_OR_PROTECT_A_REAL_REQUIREMENT => REMOVE
AUTO_OVERENGINEERING_PASS => FORBIDDEN
```

Do not end every beginner message with `Không bị over engineering chứ? PASS`
and do not treat `PASS` as the expected answer. If the proposed work is
unnecessary, say that it is overengineering and skip or simplify it.

### RULE 15 — ARENA_TASK_COMPLETION_DIALOG

When the beginner is asked "Was this task successful?" (Yes / No / Keep
working), the mapping is canonical:

```text
YES
= The Arena execution unit has reached the requested terminal state and
  returned the required result/ReturnPacket, and no more work is currently
  required in that same chat.
```

Important: `YES` does NOT mean the technical outcome must be PASS. An honest
`BLOCKED` / fail-closed result can still be `YES` if Arena correctly
performed the bounded task, stopped at the required boundary, and returned
the required evidence.

```text
KEEP WORKING
= Use when Control Tower explicitly requires more work in the SAME CHAT,
  or the current bounded task has not yet reached its required terminal
  state.
```

```text
NO
= Use only when Arena materially failed the execution itself, for example:
  - wrong task
  - wrong repository/workstream
  - unusable result
  - ignored required scope
  - premature/incorrect termination
```

Do NOT select `NO` merely because the bounded technical outcome is
`BLOCKED`.

Canonical beginner mnemonic:

```text
XONG ĐÚNG PHẠM VI + ĐÃ TRẢ KẾT QUẢ       -> YES
CÒN TIẾP TỤC CHÍNH CHAT NÀY             -> KEEP WORKING
ARENA LÀM SAI / KẾT QUẢ KHÔNG DÙNG ĐƯỢC  -> NO
```

### RULE 16 — CONTEXT_HYGIENE_AND_PLAN_LIFECYCLE

Session context is not authority. Durable task authority comes only from the
active task state, the canonical specs, and explicit Owner/Governance
decisions:

```text
SESSION_CONTEXT != AUTHORITY
DEFAULT_RETRIEVAL = ACTIVE_TASK + REQUIRED_CANONICAL_SPECS
HISTORICAL / SUPERSEDED / CLOSED MATERIAL = RETAINED, EXPLICITLY
    RETRIEVABLE, EXCLUDED FROM DEFAULT ACTIVE RETRIEVAL
EXACT DURABLE IDENTITY (REPOSITORY + WORKSTREAM + CURRENT DURABLE
    SUBJECT + GIT COMMIT/TREE OID / PR WHERE APPLICABLE) OUTRANKS SEMANTIC
    TEXT SIMILARITY
CLOSED OR SUPERSEDED PLANS LOSE ACTIVE AUTHORITY AND CANNOT SILENTLY
    REGAIN IT; CONTINUATION IS A NEW PLAN THAT REFERENCES THE CLOSED ONE
EVIDENCE IS DURABLE AND QUERYABLE, NEVER INSTRUCTION AUTHORITY MERELY
    BECAUSE ITS TEXT IS RELEVANT
NO_BLIND_DELETE_AFTER_MERGE = YES
```

Runtime enforcement (existing machinery, no new subsystem):

- `task_state.py` — plan lifecycle (`ACTIVE` / `CLOSED` / `SUPERSEDED`),
  one-shot durable `PlanIdentity` binding, `resolve_authoritative_plan`
  (exact identity beats text similarity), and fail-closed mutation guards on
  non-active plans.
- `context.py` — lifecycle-aware default retrieval: active/canonical sources
  are selected by default; `HISTORICAL` / `SUPERSEDED` / `CLOSED` /
  `ARCHIVED` sources are retained and retrievable via explicit
  `include_historical=True`; evidence sources are flagged
  `instruction_authority: false`.
- `orchestration_policy.py` — `classify_owner_escalation` under
  OWNER_MICRO_LOOP_SUPPRESSION (RULE 11).

### RULE 17 — UPSTREAM_FIRST_REFERENCE_PRESERVATION

For a bounded project outcome, P2P is the control-plane orchestrator. Select
and execute the best working upstream or reference implementation before
inventing a P2P abstraction, then adapt only the smallest project delta and
prove the real project result. This is an operating policy over existing P2P
surfaces; it creates no new runtime, registry, router, or upstream framework.

The durable policy is:

```text
UPSTREAM_FIRST=YES
REFERENCE_IMPLEMENTATION_FIRST=YES
EXECUTION_FIRST=YES
ABSTRACTION_LATER=YES
P2P_ROLE=CONTROL_PLANE_ORCHESTRATOR
```

The core execution law is:

```text
USER_GOAL
→ SELECT_BEST_UPSTREAM_OR_REFERENCE
→ INSPECT_COMPLETE_IMPLEMENTATION_WHERE_RELEVANT
→ EXECUTE_OR_REUSE_UPSTREAM_NATIVE_FIRST
→ ADAPT_SMALLEST_PROJECT_DELTA
→ PROVE_REAL_PROJECT_RESULT
→ STOP_WHEN_SUFFICIENT
```

A P2P wrapper, adapter, capability, or registry entry is not a prerequisite
for using a working upstream. When
`UPSTREAM_EXECUTABLE=YES` and `P2P_WRAPPER_EXECUTABLE=NO`, the required
decision is `USE_UPSTREAM_DIRECTLY=YES`.

For rich implementation sources — including Three.js games, cameras, combat,
enemy systems, VFX, shaders, game feel, UI systems, character systems, and
visual reference implementations — preserve the complete reference
implementation and its interactions while adapting it.
`SOURCE_CLASS=REFERENCE_IMPLEMENTATION` is metadata/semantics only; it must not
trigger a new capability ID, registry, router, or infrastructure.

`CAPABILITY_REGISTERED=PASS` is not sufficient evidence of success. For game,
UI, and visual work, acceptance prioritizes:

```text
PROJECT_RESULT_VISIBLE
UPSTREAM_NATIVE_EXECUTION (where applicable)
QUALITY_COMPARABLE_TO_REFERENCE (where applicable)
INTERACTION_FEELS_GOOD (where applicable)
```

If P2P abstraction materially degrades upstream quality,
`P2P_INTEGRATION=FAIL`, even when structural tests pass. Generalization follows
actual reuse: first success uses the upstream directly; repeated success may
record a lightweight execution recipe; only multiple real reuses justify a
generic capability abstraction.

Useful upstream repositories may live in a dedicated local upstream pool or
cache, preserve-first and effectively read-only. Full upstream repositories do
not normally enter canonical P2P Git; retain only minimal source
identity/provenance metadata when useful. Do not rewrite upstream repositories
for P2P conformity.

This rule does not authorize network access, installation, authentication,
vendoring, or project mutation by itself. Existing approval, security,
provenance, scope, and evidence boundaries still apply. It also does not
authorize a second router, second registry, generic upstream framework,
repository-ingestion framework, synchronization daemon, universal wrapper, new
database/service/runtime, bulk capability migration, whole-repository
vendoring, or additional Game/Three.js capabilities merely because useful
repositories exist.

For APP GAME TRUYỆN, the default remains:

```text
UPSTREAM_REFERENCE
→ PROJECT_EXECUTION
→ VISUAL_PLAYABLE_PROOF
→ ABSTRACTION_DECISION_LATER
```

### RULE 18 — OWNER_OBSERVABILITY_AND_CHALLENGE

P2P may automatically select a technical executor, capability, or verification
surface so the beginner Owner is not forced to choose internal A/B options.
That convenience must never become opaque execution.

```text
AUTO_ROUTE != OPAQUE_EXECUTION
AI_IS_TOOL
OWNER_RETAINS_AUTHORITY
```

At a material routing, mutation, cost, risk, or terminal decision, explain only
what the Owner needs to understand and challenge:

- the result or action that matters;
- why this path is appropriate when the reason is not obvious;
- the evidence or important limitation;
- the one next action or genuine Owner Gate, when one exists.

Do not force a fixed `OWNER_CHALLENGE_SUMMARY`, alternatives list,
falsifier field, or `OVER_ENGINEERING_CHECK` into every terminal response.
Those are optional explanatory tools when a disputed or consequential decision
needs them, not required ceremony.

Routine micro-fixes may still auto-continue under RULE 11
(OWNER_MICRO_LOOP_SUPPRESSION). The Owner may ask "tại sao làm thế?",
"đã cân nhắc cách nào khác?", or "bằng chứng đâu?" at any time; answer from
durable evidence and explicit decision rationale without exposing or fabricating
private chain-of-thought.

This rule does not create a new router, database, explainability framework,
audit service, or per-step narration requirement.

### RULE 19 — REALITY_FIRST_CAPABILITY_PROBE

P2P must prefer verified reality over a cosmetically successful result.

Canonical law:

```text
VERIFIED_BLOCKED > UNVERIFIED_PASS
CONTRADICTORY_EVIDENCE => STOP_AND_RECONCILE
UNCERTAIN_CAPABILITY => SMALLEST_REPRESENTATIVE_PROBE_FIRST
PROBE_PASS != PROMOTED_CAPABILITY
```

Use this rule when success depends materially on an external runtime, model,
provider, browser, GPU path, file format, third-party tool, or other capability
that has not yet been proven for the exact bounded use case.

Execution order:

1. **Define the uncertainty.** State the one capability claim that is not yet
   proven. Do not expand the probe into a general benchmark.
2. **Choose the smallest representative probe.** Reuse the actual project
   input/state when safe. Minimize spend, mutations, runtime, dependencies, and
   setup. A probe must be large enough to answer the capability question but no
   larger.
3. **Respect Owner Gates.** Secrets, paid/GPU spend, production mutation,
   deployment, merge/promotion, destructive actions, and infrastructure
   commitments still require the existing Owner Gate.
4. **Fail closed on contradictions.** If logs, hashes, runtime output, visual
   evidence, reports, or ReturnPackets disagree on a material fact, Control
   Tower must not select the convenient source and declare PASS. Suspend the
   affected conclusion until the contradiction is reconciled or classify the
   task as `BLOCKED`.
5. **Promote only the proved claim.** A successful probe proves only the tested
   capability under the tested conditions. It does not silently authorize a
   framework, production rollout, broad integration, or generalized support.
6. **Stop when the question is answered.** Do not add a metric stack, second
   executor, generalized harness, repeated seed ladder, broad benchmark, or
   architecture layer unless the probe exposes a specific blocker that
   requires it.

Routing guidance:

- If the capability is already proven for the same bounded conditions, reuse
  the proven path instead of probing again.
- If the failure is deterministic and locally reproducible, debug the root
  cause directly; do not create a capability experiment merely for ceremony.
- If the uncertainty is external or probabilistic, a one-shot or minimal fixed
  sample is preferred before full execution. Expand the sample only when the
  first probe establishes that further evidence will materially change the
  decision.
- Test artifacts remain candidate evidence. They do not become production or
  canonical authority without the normal P2P promotion rules.

Beginner-facing explanation at a material capability probe must say, in plain
language:

```text
WHAT_IS_UNPROVEN=
WHAT_SMALL_TEST_WILL_BE_RUN=
WHY_THIS_TEST_IS_ENOUGH_FOR_NOW=
WHAT_IT_COSTS_OR_CHANGES=
WHAT_COUNTS_AS_PASS_FAIL_BLOCKED=
WHAT_HAPPENS_AFTER_THE_RESULT=
OWNER_ACTION_NOW=
```

This rule is an independent P2P operational abstraction. It does not import an
external instruction architecture, mandatory per-turn metadata system,
complexity scoring formula, autonomous baton loop, or monolithic prompt core.

## 4. RULE_ASSIMILATION_GATE_V1

### 4.1 Failure mode fixed

"We will add this rule/update to a related task later" must NEVER be an
untracked promise.

### 4.2 Durable semantics

When Control Tower accepts an enduring rule/update but intentionally defers
implementation into a related task:

```text
RULE_ASSIMILATION_STATUS=PENDING
```

`PENDING` remains open until ALL of the following are true:

- **A.** A later Writer task explicitly lists that rule/update as a required
  deliverable.
- **B.** Writer ReturnPacket identifies the exact canonical artifact/section
  changed and reports `RULE_ASSIMILATED=YES`.
- **C.** Control Tower independently verifies the exact PR head/tree contains
  that rule/update.

Only then:

```text
RULE_ASSIMILATION_STATUS=VERIFIED
```

If the supposed related task closes without the update:

```text
RULE_ASSIMILATION_STATUS=RULE_ASSIMILATION_MISSED
```

A `MISSED` item must be surfaced, never silently dropped. This gate is a
lightweight status convention; it does not add a ticketing subsystem. The
machine-readable ledger below is the durable record.

### 4.3 RULE_ASSIMILATION_LEDGER (machine-readable)

```json
{
  "schema": "p2p-rule-assimilation-ledger/1",
  "gate": "RULE_ASSIMILATION_GATE_V1",
  "entries": [
    {
      "id": "BACKLOG_A",
      "item": "BEGINNER_SAFE_ROUTING",
      "status": "VERIFIED",
      "evidence": [
        "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md (RULE 01, RULE 02, RULE 03, RULE 09)",
        "docs/ARENA_AGENT_MODE_PROTOCOL.md section 6 (DESTINATION / SESSION_ACTION / SESSION_GOAL / PR_EXPECTATION)",
        "tests/test_p2p_beginner_routing.py"
      ]
    },
    {
      "id": "BACKLOG_B",
      "item": "ARENA_CONTINUITY",
      "status": "VERIFIED",
      "evidence": [
        "docs/ARENA_AGENT_MODE_PROTOCOL.md sections 1-4 (GITHUB_PROJECT_STATE_IS_CANONICAL, ONE_SESSION_ONE_PR, session rotation)",
        "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md (RULE 04, RULE 05, RULE 06)"
      ]
    },
    {
      "id": "BACKLOG_C",
      "item": "BEGINNER_RETURN_CONTRACT",
      "status": "VERIFIED",
      "evidence": [
        "docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md (Return contract, USER_ACTION)",
        "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md (RULE 09, RULE 10)"
      ]
    },
    {
      "id": "BACKLOG_D",
      "item": "PROMPT_CEREMONY_EFFICIENCY",
      "status": "VERIFIED",
      "evidence": [
        "AGENTS.md (Prompt and effort efficiency section, PR #27 P2P-PROMPT-EFFICIENCY-POLICY-01)",
        ".p2p/system/p2p_capabilities/orchestration_policy.py (P2P-EFF01)",
        "tests/test_p2p_eff01_execution_efficiency.py",
        "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md (RULE 12, RULE 14)"
      ]
    },
    {
      "id": "BACKLOG_E",
      "item": "DURABLE_CONTROL_TOWER_SESSION_HANDOFF",
      "status": "VERIFIED",
      "evidence": [
        "docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md (canonical, referenced not recreated)",
        ".p2p/system/p2p_capabilities/control_tower_handoff.py",
        "tests/test_p2p_control_tower_session_handoff.py",
        "tests/test_p2p_control_tower_durable.py"
      ]
    },
    {
      "id": "BACKLOG_F",
      "item": "QUICK_PROMPT_ARENA_PROMPT_BUILDER",
      "status": "PENDING",
      "evidence": [
        "No canonical P2P Arena quick-prompt/prompt-builder artifact exists",
        "Nearest existing surface: .p2p/system/p2p_capabilities/control_tower_handoff.py build_execution_prompt (Control Tower-bound prompt builder, not an Arena quick-prompt product)",
        "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md (RULE 01, RULE 02, RULE 03 shape the future prompt-builder output)"
      ]
    },
    {
      "id": "BACKLOG_G",
      "item": "LIGHTWEIGHT_ORCHESTRATION_CONTEXT_INTEGRATION",
      "status": "VERIFIED",
      "evidence": [
        "C18 canonical runtime: .p2p/system/p2p_capabilities/orchestration_policy.py + tests/test_p2p_adaptive_orchestration.py",
        "C19 canonical runtime: .p2p/system/p2p_capabilities/context.py, context_envelope.py, context_cache.py, context_manifest.py + tests/test_p2p_task_targeted_context.py",
        "governance/development-control.json roadmap records C18/C19 DONE",
        "No unrelated runtime wiring was performed by the notebook task; unresolved sub-items remain PENDING under this same ledger"
      ]
    },
    {
      "id": "BACKLOG_H",
      "item": "ARENA_TASK_COMPLETION_DIALOG",
      "status": "VERIFIED",
      "evidence": [
        "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md (RULE 15 — ARENA_TASK_COMPLETION_DIALOG)",
        "docs/ARENA_AGENT_MODE_PROTOCOL.md section 11 (completion-dialog handling references notebook RULE 15)",
        "tests/test_p2p_operations_notebook.py (RULE 15 semantics checks)"
      ]
    },
    {
      "id": "BACKLOG_I",
      "item": "CONTEXT_HYGIENE_01",
      "status": "PENDING",
      "evidence": [
        "Issue #42 P2P-CONTEXT-HYGIENE-01 (bounded goal, required laws, OWNER_MICRO_LOOP_SUPPRESSION)",
        "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md (RULE 11 OWNER_MICRO_LOOP_SUPPRESSION, RULE 16 CONTEXT_HYGIENE_AND_PLAN_LIFECYCLE)",
        ".p2p/system/p2p_capabilities/task_state.py (plan lifecycle, PlanIdentity binding, resolve_authoritative_plan)",
        ".p2p/system/p2p_capabilities/context.py (lifecycle-aware default retrieval, evidence non-instructional)",
        ".p2p/system/p2p_capabilities/orchestration_policy.py (classify_owner_escalation)",
        "governance/development-control.json (session-context-is-not-authority invariant)",
        "tests/test_p2p_context_hygiene.py"
      ]
    }
  ]
}
```

`BACKLOG_I` stays `PENDING` until Control Tower independently verifies the
exact PR head/tree for Issue #42 under RULE_ASSIMILATION_GATE_V1.

## 5. ASSIMILATION_BACKLOG — previously promised items

Truthful reconciliation. Implementation is NOT claimed merely because an
idea was previously discussed; each item carries the status recorded in
section 4.3.

- **A. Beginner-safe routing** — `VERIFIED`. Exact destination, NEW CHAT vs
  SAME CHAT, and exact chat naming are canonical (RULE 01-03, RULE 09 above;
  Arena routing fields in `docs/ARENA_AGENT_MODE_PROTOCOL.md` section 6).
- **B. Arena continuity** — `VERIFIED`. GitHub as checkpoint, quota/session
  recovery, no duplicate PR (RULE 04-06 above;
  `docs/ARENA_AGENT_MODE_PROTOCOL.md` sections 1-4).
- **C. Beginner return contract** — `VERIFIED`. One immediate next step,
  success signal, exact ReturnPacket destination (RULE 09-10 above;
  `docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md`).
- **D. Prompt/ceremony efficiency** — `VERIFIED`. Minimum sufficient work,
  risk-proportional verification, stop when evidence sufficient,
  exceptions-only progress, anti-over-engineering (`AGENTS.md` "Prompt and
  effort efficiency"; `orchestration_policy.py`; RULE 12/14 above).
- **E. Durable Control Tower session handoff** — `VERIFIED` (already
  canonical, referenced, not recreated). `CONTROL-TOWER-SESSION-HANDOFF.md`
  + `control_tower_handoff.py` + focused tests.
- **F. Quick prompt / Arena prompt-builder concept** — `PENDING`. No
  canonical artifact exists; the concept is not claimed as implemented. The
  nearest surface is `control_tower_handoff.py build_execution_prompt`
  (Control Tower-bound). A future Writer task must list F as a required
  deliverable before it can become `VERIFIED` under
  RULE_ASSIMILATION_GATE_V1.
- **G. Lightweight orchestration/context integration items** — `VERIFIED`
  for the canonical C18/C19 runtime surfaces (referenced above); no
  unrelated runtime wiring is performed by this task, and any still-unresolved
  sub-items remain `PENDING` under the same ledger instead of disappearing.
- **H. Arena task completion dialog (Yes / No / Keep working)** — `VERIFIED`
  (RULE 15 above, accepted by the Owner after the original PR38
  implementation and assimilated under RULE_ASSIMILATION_GATE_V1 before PR38
  closes).
- **I. Context hygiene / plan lifecycle (CONTEXT_HYGIENE_01)** — `PENDING`.
  Issue #42 PR candidate: RULE 11 OWNER_MICRO_LOOP_SUPPRESSION + RULE 16
  CONTEXT_HYGIENE_AND_PLAN_LIFECYCLE above, runtime enforcement in
  `task_state.py` / `context.py` / `orchestration_policy.py`, focused tests
  in `tests/test_p2p_context_hygiene.py`. Flips to `VERIFIED` only after
  Control Tower verifies the exact PR head/tree.

## 6. Discovery and operator paths

| Operator | Discover | Canonical surface |
| --- | --- | --- |
| Beginner | `AGENTS.md` P2P block of the installed project | this notebook digest + Control Tower |
| Control Tower | this notebook + `CONTROL-TOWER-SESSION-HANDOFF.md` | docs/p2p-development/ |
| Arena Writer / Supervisor | `AGENTS.md` → `ARENA_AGENT_MODE_PROTOCOL.md` → this notebook | docs/ARENA_AGENT_MODE_PROTOCOL.md |
| Codex / Manus / other executors | installed `AGENTS.md` P2P block + this notebook | this notebook |
| This notebook (canonical source) | P2P development source | `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` |

## 7. Validation boundary

- This notebook is operations memory and guidance, not runtime logic.
- It grants no permissions, executes no host, and changes no routing.
- It does not add a router, scheduler, orchestrator, memory framework,
  ticketing system, or second handoff framework.
- Verification is structural: presence of the canonical rule sets, the
  assimilation gate, the machine-readable ledger, install-inheritance via the
  `AGENTS.md` entrypoint, and Arena/Control Tower linkage (see
  `tests/test_p2p_operations_notebook.py`).
- Promotion/deployment of anything in this notebook remains subject to the
  existing Owner Gate and governance surfaces.

## 8. Change discipline

1. Control Tower accepts an enduring rule/update and defers implementation:
   record it here under `RULE_ASSIMILATION_STATUS=PENDING`.
2. A later Writer task lists the item as a required deliverable.
3. The Writer ReturnPacket names the exact artifact/section changed and
   reports `RULE_ASSIMILATED=YES`.
4. Control Tower independently verifies the exact PR head/tree contains the
   change.
5. Only then the entry flips to `VERIFIED`. A closed task without the update
   flips to `RULE_ASSIMILATION_MISSED` and is surfaced.

Updates to this notebook are themselves subject to the same gate.
