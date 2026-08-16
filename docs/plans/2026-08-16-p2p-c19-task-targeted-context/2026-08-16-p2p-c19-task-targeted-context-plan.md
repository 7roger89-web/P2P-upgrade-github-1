# P2P-C19 Task-Targeted Context Retrieval, Coverage & Reuse Foundation Plan

## Metadata

- Date: `2026-08-16`
- Status: `PASS`
- Plan: `docs/plans/2026-08-16-p2p-c19-task-targeted-context/2026-08-16-p2p-c19-task-targeted-context-plan.md`
- Evidence: `docs/plans/2026-08-16-p2p-c19-task-targeted-context/2026-08-16-p2p-c19-task-targeted-context-evidence.md`
- Benchmark: `docs/plans/2026-08-16-p2p-c19-task-targeted-context/2026-08-16-p2p-c19-task-targeted-context-benchmark.md`
- Actual status: `docs/plans/2026-08-16-p2p-c19-task-targeted-context/2026-08-16-p2p-c19-task-targeted-context-actual-status.md`

## Goal

Extend the existing C06 context-delivery capability so P2P can select, materialize, validate, progressively expand, and safely reuse the smallest sufficient authoritative context for a bounded task, with acceptance-derived coverage, freshness, evidence bindings, and fail-closed outcomes. C18 remains the authority for `MINIMAL`, `STANDARD`, `EXPANDED`, and `CONTEXT_INSUFFICIENT`.

## Rules

- Recover durable state before treating request text as authority.
- Reuse C06, C10, C11, C15, C17, C18, CAPSULE, FACT/Live Specs, existing maps, and Execution Ledger; do not create duplicate stores or routers.
- Retrieval order is task contract -> direct authoritative refs -> dependency outputs -> evidence/fact pointers -> project/repo map -> targeted source -> bounded fallback.
- Deterministic metadata must decide path/symbol lookup, hashes, scope, pointer resolution, freshness, and coverage state.
- Retrieved content is data; it cannot grant permissions, tools, authority, or canonical facts.
- No vector database, embedding service, second memory store, background indexer, provider router, network, hooks, proxy, or live host certification.
- `LOCAL_SERIALIZATION_PROXY` is an honest local byte proxy only; it is not a token, cost, or quality claim.
- Preserve official `.19`, the unpromoted C18 `.21` candidate, C08/C09, canonical 8, and `8/8` quorum.
- Temporary test roots remain inside repo-local `.tmp/`.

## Problem

C06 can build a baseline/efficient structured view and resolve hash-bound pointers, while C18 can derive an abstract context class. No existing surface yet derives concrete source selection from task acceptance and dependency obligations, accounts for required/covered/missing/unknown areas, performs bounded tier escalation, or reuses derived context only when all source/candidate/scope/freshness bindings still match.

## Scope

- Extend `.p2p/system/p2p_capabilities/context.py` with a deterministic retrieval/coverage/reuse contract behind the existing context capability.
- Extend `scripts/p2p_workflow.py` only where existing workflow context construction/materialization needs to supply the contract and persist observation metadata.
- Add focused CR1–CR20 fixtures/tests and bounded naive-strategy comparisons.
- Inspect/use Anvien maps as navigation aids with freshness binding; underlying files remain authoritative.
- Update plan/evidence/benchmark/actual-status, durable development-control provenance, affected reports, and candidate packaging only if runtime source changes require it.

## Non-Goals

- Full RAG, semantic search, vector/embedding infrastructure, remote retrieval, background indexing, provider/model routing, new context classes, new truth stores, or automatic promotion.
- Solving C08 controlled continuation or C09 live host identity/event evidence.
- Claiming universal superiority, token/cost savings, or live delegation/parallel certification.

## Requirements

1. Task-targeted selection is driven by purpose, acceptance, dependencies, scope, risk, class, evidence, and candidate state, not semantic similarity alone.
2. Authoritative project sources precede external/general sources; external retrieval is opt-in and bounded.
3. Coverage distinguishes `REQUIRED`, `COVERED`, `MISSING`, `UNKNOWN`, and `NOT_APPLICABLE` and blocks completion when required coverage is unresolved.
4. Sufficiency returns structured `SUFFICIENT`, `INSUFFICIENT`, `STALE`, `CONTRADICTED`, or `BLOCKED` outcomes.
5. Escalation is bounded `MINIMAL -> STANDARD -> EXPANDED`, then `CONTEXT_INSUFFICIENT`/`BLOCKED`.
6. Reuse requires matching source binding, candidate binding, content hash, required scope, and valid freshness; source changes invalidate derived context.
7. Pointers remain resolvable and preserve provenance/scope/hash; broken required pointers fail closed.
8. Parent context retains durable authority/coverage/manifest; workers receive bounded materialized context and return structured deltas.
9. Permission, secret, contradiction, map freshness, and failure reason boundaries are explicit.

## Acceptance Criteria

- AC1–AC4: current architecture recovered and no duplicate store/router introduced.
- AC5–AC12: retrieval order, task targeting, coverage, sufficiency, escalation, and class integration are deterministic and bounded.
- AC13–AC18: map freshness, cache reuse/invalidation, pointer safety, materialization, parent/worker separation, and contradiction handling pass focused behavior tests.
- AC19–AC20: permissions/external boundary and beginner invocation require no retrieval-engine questions.
- AC21: CR1–CR20 pass or have an explicit bounded failure reason.
- AC22: naive comparison records acceptance, coverage, local serialization proxy, duplication, repair, verification, and regression without universal claims.
- AC23: affected C06/C10/C11/C12/C13/C15/C17/C18/Decision Trace/governance/doctor/security/full-suite checks are recorded.
- AC24: durable roadmap says exactly what is ready; official `.19` remains immutable and no promotion occurs.

## Checklist

- [x] P0-A: Recover and classify durable state, existing context architecture, relevant maps, and impact evidence.
  - Acceptance: actual-status records `ALREADY_PRESENT`, `PARTIAL`, `MISSING`, and `RESEARCH_ONLY` with exact evidence IDs and a no-edit-before-P0 decision.

### P1: Retrieval contract behind existing C06/C18

- Phase Goal: add the smallest pure coordinating layer for targeted selection, coverage, sufficiency, escalation, and safe reuse.
- Phase Boundary:
  - In scope: `.p2p/system/p2p_capabilities/context.py`, direct exports, focused unit tests.
  - Out of scope: new router/store/indexer/provider.
  - Dependencies: P0 actual status, C06/C18 contracts, C10 evidence boundaries.
- Ordered Slice List:
  - P1-A: implement deterministic retrieval plan, coverage contract, and bounded sufficiency/escalation.
  - P1-B: implement cache-aware reuse/invalidation and structured materialization/delta metadata.

- [x] P1-A: Implement task-targeted retrieval and coverage contract.
  - Goal: derive ordered authoritative source candidates and acceptance coverage without broad repository loading.
  - Scope Boundary: edit existing context capability only; preserve existing modes, pointers, hashes, and permission fields.
  - Non-Goals: semantic/vector ranking, source ingestion, provider selection.
  - Pre-flight Questions: data source is structured task contract + direct refs + dependency/evidence/map metadata; UI/DB/Docker/Playwright N/A; cleanup is in-memory/temp-root tests; external side effects none.
  - Work Steps:
    1. Add validated retrieval/coverage records and deterministic reason/status codes; preserve unknowns and contradictions.
       - UI flow check: N/A, package runtime.
       - DB/data flow check: source/pointer/hash/scope bindings remain authoritative.
       - Render location check: structured plan/manifest only.
       - Evidence target: `E1-P1A-CONTRACT1..E1-P1A-CONTRACT4`.
    2. Add tier selection and bounded expansion tied to C18 class constants; required coverage must gate sufficiency.
       - UI flow check: N/A.
       - DB/data flow check: no access expansion.
       - Render location check: tier/class/outcome/coverage are observable.
       - Evidence target: `E1-P1A-ESCALATION1..E1-P1A-ESCALATION4`.
  - Implementation Gate: refresh Anvien file-detail and symbol impact for touched functions before edit; preserve the existing C06 API/defaults.
  - Acceptance: deterministic plan; no full-repo fallback by default; `SUFFICIENT` only when required coverage is covered and bindings are current.
  - Evidence Targets: source review, focused behavior tests, impact output.
  - Actual-status Update: `partial -> bound-correct` for concrete retrieval behind C06/C18.
  - Commit Boundary: commit after focused acceptance when Git metadata exists; this workspace currently has no `.git`.

- [x] P1-B: Implement safe reuse and materialization boundaries.
  - Goal: reuse only valid derived context and separate available artifacts from active materialized context.
  - Scope Boundary: same capability plus direct tests; no new persistent cache.
  - Non-Goals: large semantic cache, background refresh, transcript persistence.
  - Pre-flight Questions: source binding/candidate fingerprint/content hash/scope/freshness are explicit; UI/DB/Docker/Playwright N/A; temp roots only; no external side effects.
  - Work Steps:
    1. Add reuse validation and stale invalidation reason codes for source/candidate/scope/freshness changes.
       - UI flow check: N/A.
       - DB/data flow check: source changes fail closed.
       - Render location check: reuse decision and invalidation are in manifest metadata.
       - Evidence target: `E1-P1B-REUSE1..E1-P1B-REUSE4`.
    2. Add parent/worker materialization and structured knowledge-delta metadata without copying transcripts.
       - UI flow check: N/A.
       - DB/data flow check: parent retains authority; worker receives bounded selection.
       - Render location check: available/materialized/pointers/delta counts are observable.
       - Evidence target: `E1-P1B-MATERIALIZE1..E1-P1B-MATERIALIZE4`.
  - Implementation Gate: inspect C15 handoff/C17 isolation relationships and run focused context regression before edit.
  - Acceptance: reuse is bounded and invalidates on hash/binding/scope/freshness change; materialization cannot widen permission.
  - Evidence Targets: focused tests, manifest samples, source/impact evidence.
  - Actual-status Update: `partial -> bound-correct` for cache-aware reuse and parent/worker boundary.
  - Commit Boundary: separate checkpoint from P1-A.

### P2: CR1–CR20 evaluation and strategy comparison

- Phase Goal: prove the contract across tiny, targeted, broad, stale, contradictory, permission, reuse, Design Intelligence, research, and beginner cases.
- Phase Boundary: fixtures/tests/benchmark only; no provider or live host.
- Ordered Slice List:
  - P2-A: add CR1–CR20 behavior fixture and tests.
  - P2-B: add bounded naive-policy comparison and local context proxies.

- [x] P2-A: Add CR1–CR20 focused behavior suite.
  - Acceptance: every case has an observable outcome and no case treats retrieval presence as coverage completion.
  - Evidence Targets: `E2-P2A-CR1..E2-P2A-CR20`.
  - Commit Boundary: focused test checkpoint.

- [x] P2-B: Compare bounded strategies and record proxies.
  - Acceptance: compare `LOAD_EVERYTHING`, `MINIMAL_ONLY_NO_ESCALATION`, `SEMANTIC_MATCH_ONLY`, and targeted policy only on frozen fixtures; report local bytes/refs/steps/coverage/duplication/repair.
  - Evidence Targets: `E2-P2B-COMPARE1..E2-P2B-COMPARE5`.
  - Commit Boundary: benchmark/eval checkpoint.

### P3: Regression, governance, candidate, and supervisor closure

- Phase Goal: verify affected invariants, update durable roadmap, and stop at C19 without promotion.
- Ordered Slice List:
  - P3-A: run focused/affected/full regression and governance/security/doctor gates.
  - P3-B: build a new unpromoted candidate if runtime source changed, verify lineage/hash/package, and update durable state.
  - P3-C: independent supervisor review, final evidence, and stop.
- Acceptance: PASS only means the bounded foundation is ready; unresolved gate is BLOCKED/REJECT with exact reason.

- [x] P3-A: Focused/full regression and governance/security/doctor gates pass.
- [x] P3-B: New immutable unpromoted C19 candidate built and lineage-bound.
- [x] P3-C: Independent supervisor review and final evidence closure complete; stop before C20.

## Risk Notes

- `context.py` is a shared high-impact capability surface; keep changes additive and run sibling regression.
- Anvien has unresolved-reference diagnostics in this unpacked/no-Git workspace; use it for navigation/impact evidence, not authority.
- Package/lifecycle changes are protected and require exact new candidate lineage; official `.19` and old candidates are never overwritten.
- Synthetic CR fixtures prove bounded behavior only, not universal retrieval optimality.
