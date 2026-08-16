# P2P Native Decision Trace Plan

## Metadata

- Date: `2026-08-12`
- Status: `complete`
- Plan: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-plan.md`
- Evidence: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-evidence.md`
- Benchmark: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-benchmark.md`
- Actual status: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-actual-status.md`

## Goal

Add the smallest P2P-native structured decision trace that reconstructs
`SOURCE/FACT -> EVIDENCE -> DECISION -> APPROVAL/GOVERNANCE -> CHANGE -> ARTIFACT`
from project-local governed state, including contradiction, supersession,
temporal validity, materiality, beginner WHY, export, redaction, and missing
reference behavior.

## Rules

- Complete P0 actual status before implementation work.
- Keep the existing execution ledger as the only durable event store; do not add a second ledger, graph database, daemon, MCP, provider, router, agent, or memory system.
- FACT_LEDGER, Live Specs, existing Goal, approval policy, execution ledger, and RAG/trust boundaries remain authoritative; the trace only references them.
- Preserve exactly eight canonical identities, denominator `8`, and full quorum `8/8`; Aesthetica remains optional/supporting and is never fabricated or counted.
- Store concise structured decision basis only; never store chain-of-thought, raw private prompts, credentials, API keys, or environment secrets.
- Development source only. Do not modify the verified release artifact, v5 artifact, immutable baseline, App Game Truyện, Logistics, or any user project.
- Do not install or vendor Semantica; keep only a future provider seam label if the existing architecture requires it.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- Anvien is unavailable for this target because the repository is not indexed; use bounded local inspection and record that limitation.
- This scope is CLI/state-only; browser, Playwright, Docker, and UI visual evidence are `N/A` with a reason.

## Problem

The beginner lifecycle certification found that WHY evidence is distributed
across Goal, project status, reports, trusted evidence, and the execution
ledger. A user can inspect those artifacts, but P2P cannot deterministically
answer which facts, evidence, policy, approval, change, and artifact caused a
material governed decision without manual searching.

## Scope

- Author a production-ready Decision Trace SPEC and architecture review.
- Reuse the existing execution-ledger JSONL as the project-local storage.
- Add a native structured trace contract, validation, redaction, minimal
  SHA-256 payload integrity, reference resolution, contradiction and
  supersession traversal, temporal checks, beginner WHY rendering, JSON/
  Markdown export, and a Windows-safe CLI/internal API.
- Auto-capture only material workflow decisions; do not emit line-of-code
  trace spam.
- Wire workflow reports/status to the trace reference without changing Goal,
  approval, FACT_LEDGER, RAG, or quorum semantics.
- Add DT1-DT24 behavior tests and fresh beginner WHY evidence.

## Non-Goals

- No Semantica installation, adapter, graph database, RDF/PROV-O dependency,
  blockchain, daemon, MCP, external service, or second router/ledger.
- No discovery-to-Goal redesign, Code-Impact capability, Anvien integration,
  Brigade/Tideline, UIUX routing work, new specialist/catalog, deployment
  automation, release packaging, install/upgrade migration, or release v5
  rebuild.
- No synthetic eight-agent quorum and no simulated Aesthetica identity.
- No historical backfill that pretends old decisions had trace records.

## Requirements

- Trace records contain the required decision, goal, basis, reference,
  governance, change, artifact, temporal, relationship, redaction, and
  integrity fields.
- Missing, stale, invalid, or contradictory references produce explicit
  `UNKNOWN`, `PARTIAL`, `MISSING_REFERENCE`, or `CONTRADICTED` state and do not
  take ordinary P2P unavailable unless an existing policy requires blocking.
- Existing projects without trace records continue safely and initialize
  without overwriting valid state.
- Owner approval references actual approval evidence; a bare boolean is never
  accepted as approval proof.
- Canonical review references contain only actual participating canonical
  identities; supporting specialists are separate and non-authoritative.
- Query supports decision-to-artifact and artifact-to-decision reconstruction,
  supersession, contradiction, temporal validity, and a plain-language WHY.
- Export is deterministic and portable on Windows.

## Acceptance Criteria

- DT1-DT24 all pass with fresh machine-readable and human-readable evidence.
- The new behavior test proves a material workflow creates a trace and the
  WHY query reconstructs its linked basis; the baseline proves no trace was
  previously present in the certification evidence.
- Existing tests, capability doctor, governance drift, secret scan, and
  canonical safety remain passing.
- No external dependency is added; release/v5 and user-project paths remain
  unchanged.
- Supervisor independently verifies source, runtime behavior, artifacts, and
  the final PASS claim.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect the current SPEC family, Goal/evidence/approval/ledger/state surfaces, canonical registry, release boundaries, and prior WHY evidence; classify each surface in actual-status and update later phase assumptions.
  - Implementation Gate: no implementation or editing starts until `2026-08-12-p2p-native-decision-trace-actual-status.md` has a final P0 decision.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope.

### P1: Architecture authority and SPEC review

- Phase Goal: create one coherent, production-safe Decision Trace SPEC before code.
- Phase Boundary:
  - In scope: `docs/SPEC`, architecture report, authority/invariant review.
  - Out of scope: runtime code, release packaging, and implementation choreography.
  - Dependencies: P0 complete; existing capability, trust, execution/evidence, approval, and provider SPECs read.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, then continue to P2.
- Ordered Slice List:
  - P1-A: Author and review the Decision Trace SPEC.
  - P1-B: `N/A` — no second architecture artifact is required until the SPEC review identifies a real boundary gap.

- [x] P1-A: Author and review the Decision Trace SPEC.
  - Goal: define the contract, ownership, lifecycle, security, storage, query, export, and evaluation boundaries without prescribing helper names or file choreography.
  - Scope Boundary:
    - Editable: new Decision Trace SPEC and architecture review artifacts.
    - Inspect-only: existing SPEC family, AGENTS.md, reports, governance policy.
    - Preserve-only: release/v5/immutable/user-project paths.
    - Out of scope: source implementation and release packaging.
  - Non-Goals: no code-level API names, no graph/daemon/provider implementation, no owner decision unless a true architecture-changing boundary appears.
  - Pre-flight Questions:
    - Data source: existing Goal, FACT_LEDGER/Live Specs, evidence, approval, change, artifact, and execution-ledger references.
    - Display permission: governed project-local artifacts only; beginner WHY may render safe summaries and references.
    - DB read flow: N/A; existing JSONL is the state source.
    - DB write flow: N/A; append-only event record in the existing execution ledger.
    - Render location: CLI JSON/Markdown and workflow report/status references.
    - UI behavior flow: N/A; CLI/state-only scope.
    - Docker runtime: N/A; no service or app runtime is changed.
    - Playwright target: N/A; no browser surface.
    - Behavior test: SPEC review plus DT contract cases.
    - Cleanup/quarantine: no persistent fixture writes; use temporary roots for tests.
    - External side effects: none; no network or provider.
    - N/A notes: Anvien is not registered for the target; local static inspection is recorded.
  - Work Steps:
    1. Draft the SPEC around existing authority and explicit invariants.
       - UI flow check: N/A — CLI/state-only.
       - DB/data flow check: confirm reuse of execution-ledger JSONL and no second ledger.
       - Render location check: define CLI/internal API and export contract.
       - Mini QA for each completed implementation slice (MUST): N/A for architecture-only slice; validate document structure and authority references.
       - Evidence target: `E1-P1A-SPEC1`.
    2. Run Architect Review in SPEC-only mode, resolve findings, and mark the SPEC approved for implementation only after the family is coherent.
       - UI flow check: N/A — CLI/state-only.
       - DB/data flow check: verify no database/graph dependency was introduced.
       - Render location check: verify beginner WHY and audit export are bounded.
       - Mini QA for each completed implementation slice (MUST): N/A — no user runtime changed.
       - Evidence target: `E1-P1A-ARCH1`.
  - Implementation Gate:
    - Before editing target files, inspect the complete related SPEC family and record the authority decision.
    - The SPEC must not require a function name, variable name, or exact file decomposition.
  - Acceptance:
    - Source: new SPEC is coherent with AGENTS.md and existing SPECs.
    - Runtime/UI: N/A.
    - DB/data: existing execution-ledger ownership is explicit.
    - Behavior test: DT acceptance contract is fully defined.
    - Cleanup/quarantine: no temp artifact remains in source.
    - Evidence IDs: `E1-P1A-SPEC1`, `E1-P1A-ARCH1`.
    - Actual-status rows refreshed: SPEC missing -> correct/approved.
  - Evidence Targets: SPEC hash, review report, authority/invariant matrix.
  - Actual-status Update: record the approved SPEC as the authority for P2 implementation.
  - Commit Boundary: repository is not Git; record `N/A` and preserve timestamp/hash evidence.

### P2: Native trace implementation and workflow binding

- Phase Goal: implement the smallest native trace surface on existing P2P state.
- Phase Boundary:
  - In scope: runtime contract, CLI/internal API, existing ledger event capture, report/status references.
  - Out of scope: packaging/release/install/upgrade and unrelated workflow redesign.
  - Dependencies: approved Decision Trace SPEC.
- Phase Implementation Rule: do not implement `P2` directly. Implement `P2-A`, verify and refresh actual-status, then `P2-B`.
- Ordered Slice List:
  - P2-A: Implement trace contract, storage, references, queries, export, redaction, and integrity.
  - P2-B: Auto-capture material workflow decisions and expose trace references in reports/status.

- [x] P2-A: Implement trace contract, storage, references, queries, export, redaction, and integrity.
  - Goal: make structured trace records queryable from the existing project-local execution ledger.
  - Scope Boundary:
    - Editable: native trace module and CLI wrappers.
    - Inspect-only: existing ledger semantics and governance records.
    - Preserve-only: old ledger events and existing runtime contracts.
    - Out of scope: release manifest and installer.
  - Non-Goals: no graph database, second ledger, external provider, or historical fabrication.
  - Pre-flight Questions:
    - Data source: existing JSONL event store and local governance/state references.
    - Display permission: safe redacted structured summaries only.
    - DB read flow: N/A; JSONL scan/index in memory.
    - DB write flow: append one trace event to existing ledger; exports are derived.
    - Render location: CLI JSON/Markdown.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: direct API and CLI query/export cases.
    - Cleanup/quarantine: temporary project roots only.
    - External side effects: none.
    - N/A notes: local file writes are bounded to the supplied project root.
  - Work Steps:
    1. Add the schema validator, append/read path, relationship resolver, materiality filter, redaction, and integrity checks.
       - UI flow check: N/A.
       - DB/data flow check: verify append-only reuse of `.p2p/state/execution-ledger.jsonl`.
       - Render location check: verify machine-readable query shape.
       - Mini QA for each completed implementation slice (MUST): run direct behavior tests in temporary roots.
       - Evidence target: `E2-P2A-CORE1`.
    2. Add deterministic JSON/Markdown export and beginner WHY rendering.
       - UI flow check: N/A.
       - DB/data flow check: export reads, never mutates, the ledger.
       - Render location check: verify plain-language WHY has uncertainty and approval caveats.
       - Mini QA for each completed implementation slice (MUST): run CLI query/export against fixture traces.
       - Evidence target: `E2-P2A-EXPORT1`.
  - Implementation Gate:
    - Approved SPEC exists; local impact inventory is complete; test roots cannot resolve to protected targets.
    - No code path writes secrets, raw prompts, or a second durable ledger.
  - Acceptance:
    - Source: core module and CLI pass syntax/static checks.
    - Runtime/UI: CLI query/export returns deterministic output.
    - DB/data: old execution-ledger lines remain readable; trace event is append-only.
    - Behavior test: references, contradiction, supersession, temporal, redaction, and missing-reference cases pass.
    - Cleanup/quarantine: test roots are temporary and removed by context manager.
    - Evidence IDs: `E2-P2A-CORE1`, `E2-P2A-EXPORT1`.
    - Actual-status rows refreshed: query/export missing -> bound-correct.
  - Evidence Targets: test output, trace JSON, WHY Markdown, export hash.
  - Actual-status Update: mark native contract/query/export as bound-correct.
  - Commit Boundary: repository is not Git; record `N/A` and runtime hashes.

- [x] P2-B: Auto-capture material workflow decisions and expose trace references in reports/status.
  - Goal: remove manual recording for material P2P workflow decisions while keeping trace capture bounded and honest.
  - Scope Boundary:
    - Editable: existing workflow/report/status wiring and focused tests.
    - Inspect-only: Goal, approval, FACT_LEDGER, RAG, and quorum authority.
    - Preserve-only: non-material requests and existing terminal semantics.
    - Out of scope: discovery redesign, full-quorum execution, and provider work.
  - Non-Goals: no trace for every line or every routine event; no fabricated canonical review.
  - Pre-flight Questions:
    - Data source: request, Goal contract, selected route, evidence refs, changes, and report/artifact refs.
    - Display permission: reference and safe summary only.
    - DB read flow: N/A.
    - DB write flow: append one material trace event to existing ledger.
    - Render location: workflow report/status and `why` CLI.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: material vs routine capture and beginner WHY.
    - Cleanup/quarantine: temporary roots.
    - External side effects: none.
    - N/A notes: no actual canonical review is claimed unless a real review ref is supplied.
  - Work Steps:
    1. Capture a structured trace only for material decision categories and link it to the actual run/report/artifact refs.
       - UI flow check: N/A.
       - DB/data flow check: verify one trace event and no parallel storage.
       - Render location check: verify report/status reference the trace.
       - Mini QA for each completed implementation slice (MUST): run workflow behavior test on isolated new/existing fixtures.
       - Evidence target: `E2-P2B-CAPTURE1`.
    2. Preserve adaptive quorum and approval behavior, including explicit unknown/pending states.
       - UI flow check: N/A.
       - DB/data flow check: verify no FACT_LEDGER or approval mutation.
       - Render location check: verify missing review/approval is visible rather than fabricated.
       - Mini QA for each completed implementation slice (MUST): rerun canonical and optional-specialist safety checks.
       - Evidence target: `E2-P2B-SAFETY1`.
  - Implementation Gate:
    - P2-A behavior passes and the affected workflow functions are inspected before edits.
    - No protected action is executed by the trace capture.
  - Acceptance:
    - Source: focused workflow diff contains only trace binding.
    - Runtime/UI: material workflow visibly exposes a WHY trace ref; routine workflow does not create trace spam.
    - DB/data: existing ledger and project state remain compatible.
    - Behavior test: DT materiality, capture, approval, and canonical/Aesthetica cases pass.
    - Cleanup/quarantine: isolated fixtures removed.
    - Evidence IDs: `E2-P2B-CAPTURE1`, `E2-P2B-SAFETY1`.
    - Actual-status rows refreshed: workflow binding unbound -> bound-correct.
  - Evidence Targets: before/after workflow output, trace ref, unchanged governance hashes.
  - Actual-status Update: record material auto-capture and report binding as correct.
  - Commit Boundary: repository is not Git; record `N/A` and runtime hashes.

### P3: DT1-DT24 behavioral certification and regression

- Phase Goal: prove the WHY gap improved through fresh behavior, not schema existence.
- Phase Boundary:
  - In scope: DT1-DT24 evaluator/tests, baseline/after comparison, canonical/regression/secret/drift checks.
  - Out of scope: release packaging and unrelated lifecycle gaps.
  - Dependencies: P2 complete.
- Phase Implementation Rule: do not implement `P3` directly. Implement `P3-A`, verify it, then run P3-B.
- Ordered Slice List:
  - P3-A: Add direct DT1-DT24 behavior tests and machine-readable evidence.
  - P3-B: Run existing regression and safety gates; record fresh WHY before/after evidence.

- [x] P3-A: Add direct DT1-DT24 behavior tests and machine-readable evidence.
  - Goal: exercise every required trace behavior and expose truthful partial/unknown outcomes.
  - Scope Boundary:
    - Editable: new focused tests/evaluator only.
    - Inspect-only: existing regression suites.
    - Preserve-only: production source after P2 acceptance.
    - Out of scope: feature expansion.
  - Non-Goals: no synthetic quorum or deployment claim.
  - Pre-flight Questions:
    - Data source: temporary fixture ledger plus source baseline report.
    - Display permission: test artifacts only.
    - DB read flow: N/A.
    - DB write flow: temporary ledger only.
    - Render location: test report under `reports/QA`.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: DT1-DT24.
    - Cleanup/quarantine: temporary roots and output report only.
    - External side effects: none.
    - N/A notes: no browser/service is involved.
  - Work Steps:
    1. Add deterministic test cases for schema, reconstruction, contradiction, supersession, temporal, materiality, approvals, quorum identity, secrets, missing refs, and regression.
       - UI flow check: N/A.
       - DB/data flow check: use temporary JSONL roots.
       - Render location check: inspect JSON and WHY output.
       - Mini QA for each completed implementation slice (MUST): run the focused unittest module.
       - Evidence target: `E3-P3A-DT1` through `E3-P3A-DT24`.
    2. Record baseline and after behavior without rewriting the historical baseline report.
       - UI flow check: N/A.
       - DB/data flow check: compare only the relevant WHY/audit dimension.
       - Render location check: verify the new single native trace is linked.
       - Mini QA for each completed implementation slice (MUST): validate JSON schema and no-CoT/secret assertions.
       - Evidence target: `E3-P3A-WHY1`.
  - Implementation Gate:
    - DT behavior cases are isolated and cannot write protected paths.
    - Baseline limitation is preserved as historical evidence.
  - Acceptance:
    - Source: tests are behavior-focused and standard-library-only.
    - Runtime/UI: N/A.
    - DB/data: temporary fixtures only.
    - Behavior test: DT1-DT24 all PASS.
    - Cleanup/quarantine: no fixture leakage.
    - Evidence IDs: `E3-P3A-DT1` through `E3-P3A-DT24`, `E3-P3A-WHY1`.
    - Actual-status rows refreshed: tests missing -> correct.
  - Evidence Targets: test JSON, command output, baseline/after WHY reconstruction.
  - Actual-status Update: certify behavior, not merely schema.
  - Commit Boundary: repository is not Git; record `N/A`.

- [x] P3-B: Run existing regression and safety gates; record fresh WHY before/after evidence.
  - Goal: show compatibility with existing P2P foundation and governance.
  - Scope Boundary:
    - Editable: QA/supervisor reports only.
    - Inspect-only: all production sources after P2.
    - Preserve-only: release/v5 hashes and user paths.
    - Out of scope: packaging, upgrade, or unrelated repairs.
  - Non-Goals: no full eight-thread claim unless real threads run.
  - Pre-flight Questions:
    - Data source: existing tests, capability doctor, drift, secret scan, and trace eval.
    - Display permission: QA report.
    - DB read flow: N/A.
    - DB write flow: reports only.
    - Render location: QA/supervisor Markdown and JSON.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: full relevant regression.
    - Cleanup/quarantine: temporary outputs.
    - External side effects: none.
    - N/A notes: CLI/state-only scope.
  - Work Steps:
    1. Run focused, existing, canonical, governance, secret, and drift checks.
       - UI flow check: N/A.
       - DB/data flow check: verify FACT_LEDGER/Live Specs and approvals are unchanged.
       - Render location check: inspect reports.
       - Mini QA for each completed implementation slice (MUST): QA lane is read-only and reports failures without fixing.
       - Evidence target: `E3-P3B-REG1`.
    2. Run supervisor acceptance against source and fresh evidence.
       - UI flow check: N/A.
       - DB/data flow check: verify no hidden parallel state.
       - Render location check: verify the final 24-section handoff can be supported.
       - Mini QA for each completed implementation slice (MUST): supervisor lane only.
       - Evidence target: `E4-P4A-SUP1`.
  - Implementation Gate:
    - All DT cases are complete; no unresolved implementation failure remains.
  - Acceptance:
    - Source: supervisor verifies actual source and runtime outputs.
    - Runtime/UI: N/A.
    - DB/data: governance continuity passes.
    - Behavior test: regression passes or a real blocker is recorded.
    - Cleanup/quarantine: reports are the only persistent outputs.
    - Evidence IDs: `E3-P3B-REG1`, `E4-P4A-SUP1`.
    - Actual-status rows refreshed: regression remains correct.
  - Evidence Targets: regression result, lock/drift/secret result, supervisor report.
  - Actual-status Update: final state becomes PASS only after independent review.
  - Commit Boundary: repository is not Git; record `N/A`.

### P4: Closure and handoff

- [x] P4-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow/skill for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: supervisor review passes, or the plan records a blocker with evidence and no closure is performed.
- [x] P4-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted plan.
  - Work Steps:
    1. Review only files and artifacts created by this plan.
    2. Quarantine or remove dead temporary artifacts without touching unrelated user data.
    3. Re-run supervisor review of the cleanup.
  - Implementation Gate: only plan-created artifacts are candidates.
  - Acceptance: no dead plan-created artifact remains and the cleanup is evidenced.
- [x] P4-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, runtime lock/drift, and final status.
  - Work Steps:
    1. Run all required CLI/state validation and secret checks.
    2. Refresh generated lock/report artifacts when source policy requires it.
    3. Record final evidence, benchmark, limitation, and non-Git closure.
  - Implementation Gate: P4-A and P4-B pass or record blockers.
  - Acceptance: evidence is complete, DT1-DT24 status is known, supervisor verdict is known, and no unsupported PASS claim remains.

## Risk Notes

- The repository is an unpacked non-Git development source; commit requirements
  are recorded as `N/A`, while runtime hashes and reports provide auditability.
- The existing `execution-ledger.jsonl` is append-only but not a general graph;
  query scans are intentionally bounded and may return `PARTIAL` on malformed
  or missing references.
- Existing historical runs have no trace records. The implementation must not
  backfill or imply a provenance record that did not exist.
- No real eight-thread quorum is claimed by deterministic local tests.
- Release/install/upgrade integration remains a separate next Goal if fresh
  evidence shows the development-source capability is ready for packaging.
