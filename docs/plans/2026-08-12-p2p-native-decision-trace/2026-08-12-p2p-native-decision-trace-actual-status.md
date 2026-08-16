# P2P Native Decision Trace Actual Status

Title: P2P Native Decision Trace
Date: 2026-08-12
Status: P4 Complete
Companion plan: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-plan.md`
Companion evidence: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-evidence.md`
Companion benchmark: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-benchmark.md`

## Purpose

This is the completed P0 classification before implementation. It records the
real baseline and the exact touch mode for the next phase.

## Freshness / Refresh Rules

Refresh after every implementation slice. Keep historical classifications in
the Status Refresh Log; do not silently rewrite the baseline.

## Scope

Target scope:

- Native structured decision trace in the P2P development source.
- Existing Goal/evidence/approval/FACT_LEDGER/Live Specs/execution-ledger
  boundaries and beginner WHY behavior.

Out of scope:

- Release/v5 artifacts, App Game Truyện, Logistics, user projects, packaging,
  installation, upgrade, Semantica, Anvien integration, new specialist,
  Code-Impact, UI/browser/service runtime.

## Relationship / Impact Evidence

Anvien `context`/`file-detail` cannot be used for this target because the P2P
repository is not registered. The relationship count is therefore recorded as
`unknown (Anvien unavailable)` rather than invented. Local `rg`, file inventory,
and source reading are the bounded fallback.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `docs/SPEC/*` family | E0-P0A-SRC1 | unknown | authority documents and copied hard rules | high; review before code |
| `.p2p/state/execution-ledger.jsonl` | E0-P0A-LEDGER1 | unknown | existing append-only workflow event source | high; preserve old lines |
| `scripts/p2p_workflow.py` | E0-P0A-GAP1 | unknown | writes Goal/status/report/ledger artifacts | high; narrow binding |
| `.p2p/system/p2p_capabilities/*` | E0-P0A-SAFE1 | unknown | native capability contracts and canonical registry | critical; preserve 8/8 |
| `governance/*` | E0-P0A-SAFE1 | unknown | FACT_LEDGER, Live Specs, approval, drift | critical; inspect-only |
| verified release/v5/user paths | E0-P0A-BOUNDARY1 | N/A | protected preserve-only targets | critical; do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. Add evidence or tests only if needed. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing parts. Preserve correct parts. |
| `wrong` | Current behavior, source, or contract is incorrect. | Replace with required behavior. Record the exact reason. |
| `missing` | Required behavior, source, or contract does not exist. | Implement the missing piece only. |
| `unbound` | Surface exists but is not wired to the real source, flow, or contract. | Bind to the real source only. Preserve approved surface. |
| `fake-or-stub` | Prototype, demo, mock, fallback, or placeholder data is being used as real behavior. | Remove fake behavior or replace it with an approved truthful state. |
| `blocked` | Source, authority, contract, or required evidence is unclear. | Stop. Do not implement until resolved. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Existing Goal/report/evidence/ledger chain | Distributed and inspectable; no unified native trace | Deterministic native reconstruction | partial | unknown | E0-P0A-GAP1 | edit P1/P2 |
| Decision Trace SPEC | New authority reviewed and approved; additive reference projection | Approved production-safe authority | correct | unknown | E0-P0A-SRC1, E1-P1A-SPEC1, E1-P1A-ARCH1 | proceed P2-A |
| Existing execution ledger | Append-only JSONL already used by workflow | Sole durable trace event source | correct | unknown | E0-P0A-LEDGER1 | preserve in P2 |
| Materiality auto-capture | Workflow now captures material decisions only; routine test remains unrecorded | Capture material decisions only | correct | unknown | E2-P2B-CAPTURE1 | preserve |
| Query/export/WHY surface | Native query, JSON/Markdown export, redaction, integrity, and WHY are bound to existing ledger | CLI/internal API plus JSON/Markdown | correct | unknown | E2-P2A-CORE1, E2-P2A-EXPORT1 | preserve |
| FACT_LEDGER/Live Specs/approval/trust | Existing governance authority | Reference only; no overwrite | correct | unknown | E0-P0A-SAFE1 | preserve |
| Canonical registry/quorum | Exact 8, denominator 8, full 8/8 | unchanged | correct | unknown | E0-P0A-SAFE1 | preserve |
| Aesthetica | Optional/noncanonical; identity not verified | supporting only, never fabricated | correct | unknown | E0-P0A-SAFE1 | preserve |
| Release/v5/user projects | Outside target | unchanged | correct/preserve-only | N/A | E0-P0A-BOUNDARY1 | do not touch |
| Anvien impact service | Target unregistered | limitation recorded; local fallback | blocked for Anvien only | N/A | E0-P0A-ANVIEN1 | proceed with local inspection |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-12 | baseline before P0 | Decision Trace and related authorities | initial classification | E0-P0A-SRC1..E0-P0A-ANVIEN1 | P1-A must author SPEC before code |
| R1 | 2026-08-12 | after P1-A SPEC authoring and Architect Review | Decision Trace authority | missing -> correct | E1-P1A-SPEC1, E1-P1A-ARCH1 | P2-A may implement only the approved contract |
| R2 | 2026-08-12 | after P2-A/P2-B implementation and focused smoke tests | native trace/query/export/workflow binding | missing -> correct; unbound -> bound-correct | E2-P2A-CORE1, E2-P2A-EXPORT1, E2-P2B-CAPTURE1, E2-P2B-SAFETY1 | run DT eval |
| R3 | 2026-08-12 | after P3-A/P3-B certification and regression | DT evaluator and compatibility gates | missing -> correct | E3-P3A-DT1..DT24, E3-P3A-WHY1, E3-P3B-REG1 | supervisor closure |
| R4 | 2026-08-12 | after supervisor acceptance and final closure checks | full Goal closure | pending -> complete | E4-P4A-SUP1, E4-P4B-CLEAN1, E4-P4C-CLOSE1 | hand off PASS; next Goal only for packaging if desired |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `docs/SPEC/P2P-DECISION-TRACE-SPEC.md` | existing capability SPEC family | authority extension | P1-A | edit | E0-P0A-SRC1 | no function/variable names |
| `scripts/p2p_workflow.py` | `.p2p/state/execution-ledger.jsonl` | producer/consumer | P2-B | edit | E0-P0A-GAP1 | narrow binding only |
| `.p2p/system/p2p_capabilities/` | `.p2p/system/scripts/` | runtime contract/CLI | P2-A | edit | E0-P0A-SAFE1 | no new capability identity |
| `governance/*` | `scripts/p2p_governance.py` | policy/drift validator | P3-B | validate-only | E0-P0A-SAFE1 | no FACT/Live mutation |
| release/v5/user targets | all local source | protected boundary | all | do-not-touch | E0-P0A-BOUNDARY1 | unchanged |

## Detailed Findings

### Existing distributed WHY chain

Current state:

The beginner certification proves Goal, report, execution ledger, and trusted
evidence references exist, but its WHY/audit dimension is PARTIAL because no
single native trace record joins them.

Required state:

```text
One structured trace record can be queried from source/fact/evidence through
decision, governance/approval, change, and artifact, with explicit uncertainty.
```

Evidence:

- E0-P0A-GAP1: historical certification states the native trace is absent.
- E0-P0A-LEDGER1: existing ledger is the correct durable source to extend.

Relationship and impact:

- Related file count: unknown because Anvien is unavailable for this repo.
- Relationship summary: workflow emits state and report artifacts consumed by
  beginner-facing output and governance checks.
- Impact note: high; preserve current contracts and append only compatible events.

Classification:

partial

Allowed next action:

Author the SPEC, then add only the missing trace/query/binding behavior.

Forbidden next action:

Do not add a competing ledger, graph store, router, provider, or backfill that
pretends old history had trace records.

### Authority and safety family

Current state:

Existing capability/trust/routing/provider/optional-specialist SPECs and AGENTS
rules are approved and protect canonical 8/8, data-instruction boundaries,
approval, and development-source isolation.

Required state:

```text
Decision Trace is a reference projection over existing authority, not a new
authority or certification system.
```

Evidence:

- E0-P0A-SAFE1: capability doctor and drift are PASS.

Relationship and impact:

- Related file count: unknown; local inspection is the fallback.
- Relationship summary: existing contracts are preserved and trace references
  them without changing semantics.
- Impact note: critical; all code slices require focused regression.

Classification:

correct; the new trace authority is now implemented additively and remains
under the existing governance boundaries.

Allowed next action:

Proceed to supervisor closure after the DT1-DT24 and regression evidence.

Forbidden next action:

Do not alter canonical identities, denominator, Aesthetica readiness, approval,
FACT_LEDGER, or provider installation.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Decision Trace authority is now approved and Architect Review is PASS | complete P1-A; proceed P2-A |
| P2-A | Native query/export/runtime contract is correct and tested | complete P2-A |
| P2-B | Material workflow auto-capture is bound; routine trace spam is absent | complete P2-B |
| P3-A | DT1-DT24 evaluator and focused tests all pass | complete P3-A |
| P3-B | Existing 48-test regression, drift, secret, and capability doctor checks pass | complete P3-B |
| P4 | Supervisor PASS; dead-work review complete; final closure evidence recorded | complete P4; hand off PASS |
## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable, or the Anvien limitation is recorded.
- [x] Phase Touch Map lists plan-relevant relationship files.
- [x] Phase Touch Map defines touch mode for every affected relationship unit.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blocker is recorded: Anvien is unavailable only for impact inspection; local fallback is allowed.
- [x] Next phase status assumptions and work steps are updated from this status file.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected Current Status Matrix rows have been refreshed from latest evidence.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps must be updated before implementation.
- [ ] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

 P0 through P4 are complete. The baseline gap is closed by fresh behavior
 evidence: material workflow decisions are traceable from the existing ledger,
 and DT1-DT24 plus regression/security/drift checks pass. Supervisor acceptance
 is PASS; preserve all existing authority and state.
