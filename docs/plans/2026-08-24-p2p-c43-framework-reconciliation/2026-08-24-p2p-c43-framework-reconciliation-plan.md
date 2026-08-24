# P2P C43 Framework Reconciliation Plan

## Metadata

- Date: `2026-08-24`
- Status: `P2 complete; supervisor review pending`
- Plan: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-actual-status.md`

## Goal

Reconcile inherited development-framework drift in the capability ledger, its derived roadmap projection, and the framework validator on `codex/p2p-post74-development-01`, while preserving canonical `.19`, sealed noncanonical `.74`, RF01 orientation, provenance, and the no-promotion boundary.

## Rules

- This is development-plane reconciliation only. It is not promotion, release, deployment, publication, host repair, or product-feature implementation.
- The capability ledger schema and capability-index authority define the allowed record shape and lifecycle vocabulary. Roadmaps, reports, and research-adoption ledgers remain separate projections or evidence sources.
- Every changed record must retain a traceable origin and must not be silently deleted, renamed, or counted away. Duplicate records may be merged only with explicit provenance and independent membership evidence.
- `UNKNOWN` is acceptable when authority or implementation evidence is insufficient; an invalid or ambiguous record must fail closed.
- The known drift must be classified as malformed data, stale projection, stale vocabulary, duplicate record, missing authority binding, historical migration defect, or other before editing.
- No new framework family, scheduler, router, OXP, AERG implementation, release machinery, host capability, promotion record, or remote mutation is in scope.
- For this documentation/governance slice, Docker, browser, UI, and persistent application-DB flows are `N/A`: the real boundary is JSON schema, validator, tests, and the filesystem/Git evidence chain.
- Run Anvien file-detail and impact before changing code/contracts, run change detection before each implementation-slice commit, and preserve unrelated dirty owner worktree changes.

## Problem

The inherited capability ledger is not a safe source for downstream validation. The current state contains compact records without `capability_id`/required fields, a capability status outside the ledger vocabulary, duplicate lineage for context capabilities, a legacy status alias, and a roadmap snapshot whose count does not match the ledger. The validator then raises an uncontrolled `KeyError`/`TypeError` instead of reporting a bounded failure. History identifies the compact tail as a migration defect introduced by the RM-CONTEXT reconciliation line, but current authority must still decide whether later records are merges, upgrades, or separate memberships.

## Scope

- Read-only authority and provenance reconciliation for the capability-index tail and related context capabilities.
- Canonical schema-valid record repair without inventing IDs or silently discarding historical membership.
- Reconciliation of the capability-ledger lifecycle vocabulary, including the `VERIFIED` alias only where current ledger evidence proves the canonical replacement.
- Correction of the derived `current-roadmap.md` count only after final ledger membership is independently established.
- Fail-closed validator behavior for malformed records, duplicate IDs, unsupported lifecycle values, stale roadmap counts, and missing required fields.
- Focused negative tests and relevant charter/framework regression tests.
- C43 evidence, benchmark, actual-status, coder, and supervisor reports needed for independent review handoff.

## Non-Goals

- No `.19` baseline mutation and no rebuild or modification of the sealed `.74` artifact/worktree.
- No release, promotion, deployment, remote-host ACL/ruleset change, GitHub write, or CPT01-R2 remediation.
- No new capability family, framework module, router, scheduler, executor, OXP/AERG implementation, or provider integration.
- No conversion of report claims, research-adoption statuses, or owner proposals into runtime authority without the ledger contract and fresh evidence.
- No broad cleanup of unrelated legacy ledger errors unless the exact C43 acceptance gate proves that the change is necessary and authority-backed; residual inherited failures must be reported explicitly.

## Requirements

1. Establish the authoritative expected shape, lifecycle vocabulary, membership count, and provenance for every touched capability.
2. Classify each known and newly observed drift:
   - missing required fields / compact tail: `F HISTORICAL_MIGRATION_DEFECT` with any duplicate component also marked `D DUPLICATED_RECORD`;
   - `SYMBOL_AWARE_RETRIEVAL` invalid `SHIPPED`: `C STALE_VOCABULARY` and/or `B STALE_PROJECTION` only if later implementation evidence is authoritative;
   - `VERIFIED` alias: `C STALE_VOCABULARY` / `F HISTORICAL_MIGRATION_DEFECT`;
   - roadmap count mismatch: `B STALE_PROJECTION`;
   - unresolved owner/implementation conflict: `E MISSING_AUTHORITY_BINDING` and stop that decision closed.
3. Preserve one canonical record per capability ID and retain historical lineage in supported provenance fields or an explicit reconciliation note.
4. Make validator failures deterministic and bounded: no uncontrolled `KeyError`, `TypeError`, or silent filtering when a record is malformed.
5. Add or update tests for the seven required negative cases plus RF01 orientation and `.74` immutability.
6. Report `NEW_FAILURE`, `INHERITED_FAILURE`, and `RESOLVED_INHERITED_FAILURE` separately.

## Acceptance Criteria

- The final capability-index is schema-valid, has unique canonical IDs, uses only its declared lifecycle vocabulary, and has no unexplained touched-record loss.
- The final roadmap count exactly matches the final ledger membership count and remains labeled as a derived projection.
- The validator returns bounded, explicit failures for malformed fixtures and passes its focused valid-ledger checks without uncontrolled exceptions.
- Required negative tests prove missing IDs, duplicate IDs, unsupported statuses, stale roadmap counts, malformed records, no silent discard, RF01 orientation preservation, and `.74` sealing.
- Relevant charter/framework tests run with each result classified; no default/zero-discovery result is treated as proof.
- `.19` and `.74` hashes/refs remain unchanged, RF01 orientation remains unchanged, and no promotion/release/deployment surface changes.
- A coder evidence report and a separate supervisor review report are written under the project report conventions. The terminal C43 verdict is one of the allowed strings and the workflow hard-stops after it.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect source-of-truth files, history/provenance, exact schema and validator, and Anvien graph/impact evidence; record classifications and boundary decisions in `actual-status.md`.
  - Implementation Gate: complete; no implementation started before the P0 decision.
  - Acceptance: actual status identifies correct, partial, wrong, missing, unbound, fake/stub, and blocked surfaces for this scope.

### P1: Canonical ledger and derived projection reconciliation

- Phase Goal: establish and apply the smallest authority-backed membership/record correction.
- Phase Boundary:
  - In scope: `capability-index.json`, touched canonical ledger records, supported provenance notes, and the derived capability-count line in `current-roadmap.md`.
  - Out of scope: unrelated legacy records, research-adoption vocabulary, governance promotion state, `.19`, `.74`, and runtime feature code.
  - Dependencies: P0 source-of-truth and provenance review; direct behavior evidence for any claim upgraded to implementation status.
- Phase Implementation Rule: do not implement P1 directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, and commit when required; then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Reconstruct and reconcile canonical capability membership.
  - P1-B: Synchronize the derived roadmap count after ledger closure.

- [x] P1-A: Reconstruct and reconcile canonical capability membership
  - Goal: convert the inherited compact/duplicate/status-drift records into schema-valid, uniquely identified records only where authority and fresh evidence support the decision.
  - Scope Boundary:
    - Editable: exact affected capability records and narrowly required reconciliation metadata in `capability-index.json`.
    - Inspect-only: SPEC files, charter, owner decisions, research-adoption ledger, RM-CONTEXT reports, module implementations, Git history, `.19`, and `.74`.
    - Preserve-only: all unrelated ledger records, RF01 orientation, canonical baseline, sealed candidate, and external lifecycle vocabularies.
    - Out of scope: new capabilities, family invention, runtime implementation, and broad legacy normalization.
  - Non-Goals: do not make the ledger green by adding arbitrary fields, deleting duplicates, or translating `SHIPPED` without a source-backed semantic decision.
  - Pre-flight Questions:
    - Data source: capability-ledger schema, capability-index authority, SPEC/charter, and current source/history evidence.
    - Display permission: N/A; this is a machine-readable development ledger.
    - DB read flow: N/A; no application database is touched.
    - DB write flow: N/A; file writes are limited to the exact ledger records.
    - Render location: N/A; downstream validator and roadmap projection consume the ledger.
    - UI behavior flow: N/A; no UI/runtime behavior is changed.
    - Docker runtime: N/A; this is not an app/runtime slice.
    - Playwright target: N/A; no browser surface exists.
    - Behavior test: isolated JSON/schema/validator fixtures plus direct context-module contract checks where status depends on implementation evidence.
    - Cleanup/quarantine: all fixtures under `.tmp\p2p-c43-framework-reconciliation-*`; remove or preserve only cited evidence after validation.
    - External side effects: none; network, hooks, proxy, connectors, and remote writes remain disabled.
    - N/A notes: product/source modules are inspect-only unless their direct behavior is needed to establish an existing capability claim.
  - Work Steps:
    1. Freeze the before fingerprint and recheck every candidate record against schema, vocabulary, membership, and history.
       - UI flow check: N/A.
       - DB/data flow check: verify JSON parse, schema path, duplicate-ID map, origin/dependency references, and count before editing.
       - Render location check: verify all downstream consumers remain ledger/roadmap/validator only.
       - Mini QA: run focused read-only fixture checks and record exact before hashes/counts.
       - Evidence target: `E1-P1A-SRC*`, `E1-P1A-PROV*`, `E1-P1A-BEFORE*`.
    2. Apply only authority-backed record reconstruction/merge/status repairs and prove no historical membership is silently discarded.
       - UI flow check: N/A.
       - DB/data flow check: reparse, validate, compare pre/post ID lineage, and inspect touched record diffs.
       - Render location check: verify the projection still declares itself derived and has not become a second fact store.
       - Mini QA: run the focused ledger/schema checks before committing.
       - Evidence target: `E1-P1A-AFTER*`, `E1-P1A-DIFF*`, `E1-P1A-TEST*`.
  - Implementation Gate:
    - Existing Anvien file-detail/impact evidence is recorded for the ledger and validator; refresh it if the touched symbol/contract surface changes.
    - If CRI or any capability membership remains semantically ambiguous, stop with `P2P_C43_BLOCKED_MISSING_AUTHORITY_BINDING` instead of guessing.
  - Acceptance:
    - Source: every touched record is schema-valid, uniquely identified, vocabulary-valid, and provenance-preserving.
    - Runtime/UI: N/A; no runtime claim is made from ledger repair alone.
    - DB/data: no persistent DB touched; isolated fixtures are quarantined.
    - Behavior test: focused valid/invalid ledger fixtures pass with bounded failures.
    - Cleanup/quarantine: temporary fixtures are removed or their hashes are recorded as evidence-only artifacts.
    - Evidence IDs: recorded in `evidence.md` before commit.
    - Actual-status rows refreshed: ledger records, validator contract, and downstream roadmap projection.
  - Evidence Targets: exact before/after hashes, schema error inventory, history commits, record-level provenance table, test output, and `.19`/`.74` proof.
  - Actual-status Update: transition only affected rows after the slice; append an R1 refresh.
  - Commit Boundary: targeted commit after acceptance and `anvien detect-changes`.

- [x] P1-B: Synchronize the derived roadmap count after ledger closure
  - Goal: make `current-roadmap.md` reflect the independently established final ledger membership count without changing roadmap authority.
  - Scope Boundary:
    - Editable: the exact stale capability-count projection line and generated-date/provenance note if required by the existing format.
    - Inspect-only: capability-index source records and governance roadmap authority.
    - Preserve-only: roadmap goals, statuses, RF01 orientation, and all unrelated prose.
    - Out of scope: roadmap redesign, capability membership decisions, or governance status changes.
  - Non-Goals: do not force the count to 176 or any other value before P1-A closes membership.
  - Pre-flight Questions:
    - Data source: final validated `capability-index.json` count.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: derived Markdown snapshot only.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: roadmap/ledger count equality and stale-count fixture.
    - Cleanup/quarantine: N/A beyond isolated fixture files.
    - External side effects: none.
    - N/A notes: no generator is invoked unless its source/projection contract is first verified.
  - Work Steps:
    1. Compare the final ledger count with every count assertion in the roadmap and validator.
       - UI flow check: N/A.
       - DB/data flow check: N/A; compare JSON membership to projection text.
       - Render location check: verify the derived-source header remains intact.
       - Mini QA: run a stale-count fixture before editing.
       - Evidence target: `E1-P1B-BEFORE*`.
    2. Update only the derived count/provenance line and rerun count synchronization checks.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: inspect the exact diff for projection-only scope.
       - Mini QA: run roadmap/ledger and charter count tests.
       - Evidence target: `E1-P1B-AFTER*`, `E1-P1B-TEST*`.
  - Implementation Gate:
    - P1-A must have a final count and no unresolved membership ambiguity.
    - No roadmap edit may be made merely to silence a validator while the source ledger remains invalid.
  - Acceptance:
    - Source: count equals final ledger membership exactly.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: stale roadmap count fails closed; synchronized count passes.
    - Cleanup/quarantine: isolated fixtures are removed or cited.
    - Evidence IDs: recorded in `evidence.md`.
    - Actual-status rows refreshed: roadmap projection and validator count gate.
  - Evidence Targets: exact count comparison, minimal diff, test output, and final hashes.
  - Actual-status Update: append an R2 refresh.
  - Commit Boundary: targeted commit after acceptance and `anvien detect-changes`.

### P2: Validator hardening and negative/regression evidence

- Phase Goal: make the contract fail closed and prove the reconciliation did not weaken RF01 or sealed-candidate boundaries.
- Phase Boundary:
  - In scope: `scripts/validate_p2p_development_framework.py`, focused tests, and narrowly required charter assertions.
  - Out of scope: production feature/runtime code, release validation, host evidence, and unrelated legacy data repair.
  - Dependencies: final P1 ledger/projection membership.
- Phase Implementation Rule: implement `P2-A` before `P2-B`; do not accept the validator from a single happy-path run.
- Ordered Slice List:
  - P2-A: Harden malformed-ledger handling and add the required negative fixtures.
  - P2-B: Run framework/charter regression and boundary validation.

- [x] P2-A: Harden malformed-ledger handling and add the required negative fixtures
  - Goal: report structured failures for malformed records without uncontrolled exceptions or silent record filtering.
  - Scope Boundary:
    - Editable: validator and focused test file(s); exact charter tests only if a contract assertion is wrong.
    - Inspect-only: ledger/schema/roadmap after P1; RF01 and `.74` evidence.
    - Preserve-only: existing check IDs and valid-ledger semantics unless a narrowly documented contract correction is required.
    - Out of scope: changing the source data to hide negative fixtures.
  - Non-Goals: no validator bypass, skip-on-error, default status, or fallback record.
  - Pre-flight Questions:
    - Data source: temporary mutated ledger/roadmap fixtures copied from current source.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: validator stdout/exit status and test assertions.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: seven required negative cases plus valid control.
    - Cleanup/quarantine: fixtures stay inside repo `.tmp` and are removed after evidence capture.
    - External side effects: none.
    - N/A notes: no application runtime is involved.
  - Work Steps:
    1. Refactor only the validator's record-normalization/reporting path so malformed input becomes explicit failure evidence before any field indexing.
       - UI flow check: N/A.
       - DB/data flow check: N/A; fixture file flow is input -> validation report -> exit code.
       - Render location check: stdout/report check labels remain deterministic.
       - Mini QA: run the missing-ID and malformed-record fixtures first.
       - Evidence target: `E2-P2A-CODE*`, `E2-P2A-NEG1..E2-P2A-NEG5`.
    2. Add the duplicate, unsupported status, stale count, no-discard, RF01, and `.74` boundary assertions without weakening valid-path checks.
       - UI flow check: N/A.
       - DB/data flow check: verify fixture isolation and mutation scope.
       - Render location check: verify explicit failure output and exit code.
       - Mini QA: run the full focused negative matrix.
       - Evidence target: `E2-P2A-NEG6..E2-P2A-NEG8`, `E2-P2A-TEST*`.
  - Implementation Gate:
    - Re-run Anvien file-detail/impact for the validator/test files before editing; the validator is a high-risk source surface and must remain scoped.
    - Tests must prove input -> validator -> observable bounded result, not helper internals alone.
  - Acceptance:
    - Source: malformed records never produce uncontrolled `KeyError`/`TypeError`.
    - Runtime/UI: N/A.
    - DB/data: isolated fixture state only; no owner DB.
    - Behavior test: all required negative cases and a valid control are observed and classified.
    - Cleanup/quarantine: no fixture mutation escapes `.tmp`.
    - Evidence IDs: recorded in `evidence.md`.
    - Actual-status rows refreshed: validator and negative-test contract.
  - Evidence Targets: diff, command output, exit codes, fixture hashes, and classification table.
  - Actual-status Update: append an R3 refresh.
  - Commit Boundary: targeted commit after acceptance and `anvien detect-changes`.

- [x] P2-B: Run framework/charter regression and boundary validation
  - Goal: independently verify C43 closure conditions and explicitly separate resolved inherited failures from residual inherited failures.
  - Scope Boundary:
    - Editable: none unless P2-A exposes a directly attributable contract defect.
    - Inspect-only: all source, reports, RF01 orientation, `.19`, `.74`, and final C43 diff.
    - Preserve-only: all approved artifacts and external authorities.
    - Out of scope: optional hardening after PASS.
  - Non-Goals: no release candidate, no promotion request, and no new development goal after C43.
  - Pre-flight Questions:
    - Data source: final Git tree, focused test outputs, schema output, and hash evidence.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: reports and test output only.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: focused ledger/validator/charter/schema/syntax/regression commands.
    - Cleanup/quarantine: verify only intended C43 artifacts remain.
    - External side effects: none.
    - N/A notes: no browser or application build is applicable.
  - Work Steps:
    1. Run focused validation, charter tests, schema checks, syntax checks, and regression tests; record each exit code and result classification.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: report paths and stdout are readable.
       - Mini QA: verify no pass-by-default or zero-discovery result is counted.
       - Evidence target: `E3-P2B-TEST*`.
    2. Recheck `.19`/`.74` fingerprints, RF01 orientation, exact changed paths, and final Anvien change detection before handoff.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: final report includes exact boundary status.
       - Mini QA: supervisor-ready evidence review.
       - Evidence target: `E3-P2B-BOUNDARY*`, `E3-P2B-DETECT*`.
  - Implementation Gate:
    - All required C43 checks have real output; residual inherited failures are named and not relabeled as pass.
  - Acceptance:
    - Source: changed paths are exactly within approved C43 scope.
    - Runtime/UI: N/A.
    - DB/data: no owner data changes.
    - Behavior test: result matrix is complete.
    - Cleanup/quarantine: no unintended temporary artifacts or source changes.
    - Evidence IDs: complete in `evidence.md`.
    - Actual-status rows refreshed: final C43 state.
  - Evidence Targets: validation matrix, hashes, status classification, detect-changes, commit IDs, and reports.
  - Actual-status Update: append an R4/final refresh and set status to `P2 Complete` or precise blocker.
  - Commit Boundary: no new implementation commit after validation unless a scoped fix is required; then return to P2-A.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed C43 work against the plan, actual status, evidence, benchmark, changed files, and validation results.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return only to the responsible C43 slice.
    3. Re-run supervisor review after any fix.
  - Implementation Gate: all C43 slices are complete or explicitly blocked.
  - Acceptance: supervisor passes or records a precise blocker; no closure is claimed without review.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only accepted C43 artifacts.
  - Work Steps: inspect plan-created files, temporary fixtures, reports, and generated outputs; remove only dead artifacts created by this plan; re-run supervisor if cleanup changes acceptance scope.
  - Implementation Gate: do not touch unrelated owner changes.
  - Acceptance: final status/diff has no dead C43 artifacts.
- [ ] Pn-C: Close the plan.
  - Goal: record final evidence, detect-changes, commits, and the single allowed C43 verdict, then hard-stop.
  - Work Steps: finish reports, verify hashes, classify residual failures, and stop without beginning the next Goal.
  - Implementation Gate: supervisor result and boundary proof are present.
  - Acceptance: exact C43 verdict is recorded and no promotion/release/deployment action occurs.

## Risk Notes

- The ledger contains more schema errors than the four initially reported. Broad cleanup is intentionally not implied; residual inherited failures will remain visible unless they are directly in the C43 acceptance contract and authority-backed.
- The RM-CONTEXT owner-accepted architecture note and later implementation/adoption evidence may not be the same authority. If they cannot be reconciled without an explicit owner decision, C43 must stop with a missing-authority-binding blocker.
- `SHIPPED` is valid in separate research-adoption/governance ledgers but is not valid in the capability-index schema. Cross-ledger vocabulary translation must not be automatic.
- The working tree contains unrelated pre-existing Windows/stat-noise changes and RF01 evidence. Only exact C43 paths may be staged or committed.
