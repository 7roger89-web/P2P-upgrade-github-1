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

Operational guidance to the beginner should end with:

```text
Không bị over engineering chứ? PASS/FAIL
```

The expected normal result is `PASS`. `FAIL` means the proposed process
itself should be simplified before execution.

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
    }
  ]
}
```

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
