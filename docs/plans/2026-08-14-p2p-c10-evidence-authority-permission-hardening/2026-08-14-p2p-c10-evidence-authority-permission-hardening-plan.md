# P2P-C10 Evidence Authority and Permission Hardening Plan

## Metadata

- Date: `2026-08-14`
- Status: `P2 Complete — PASS`
- Plan: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-actual-status.md`

## Goal

Harden existing evidence and live read-only execution contracts so authority, provenance, freshness, binding, and permission boundaries are explicit and fail closed, while preserving the promoted `.15` baseline, candidate `.18`, C09 `UNKNOWN/BLOCKED`, canonical 8/8 governance, existing FACT_LEDGER, Live Specs, Decision Trace, Context, and Execution Ledger authority.

## Rules

- No promotion, release approval, C08 rerun, host-identity inference, or owner approval is performed in this Goal.
- Do not create a second truth store, ledger, router, scheduler, orchestration layer, or certification system.
- Retrieved content, model inference, tool output, and specialist opinion remain non-authoritative for protected writes.
- Use existing authority vocabulary and existing append-only Execution Ledger surfaces.
- Run Anvien file-detail and impact before editing shared runtime contracts, then detect-changes before any implementation checkpoint.
- Full build and affected regression are required before closure; no Git commit is claimed because this workspace has no `.git` directory.

## Problem

The existing evidence dataclass can accept `VERIFIED` evidence without enforcing a source reference, observation time, freshness, scope, or binding. The live execution request validates its field set but does not constrain permission, network, or task-mode values to the read-only context-trial contract. These are narrow authority-boundary gaps, not evidence that C09 host identity is available.

## Scope

- Map the current FACT_LEDGER, Live Specs, Goal Contract, Context, Decision Trace, approvals, capability manifests, runtime/source manifests, governance/drift gates, candidate hashes, and existing permission representations.
- Extend the existing `EvidenceClaim` contract with deterministic provenance/binding validation sufficient to prevent unsupported `VERIFIED` claims.
- Extend the existing live execution request/receipt binding with an explicit read-only permission contract and strict accepted values for the bounded trial.
- Keep the existing high-confidence secret scanner fail-closed while excluding only its proven all-`x` documentation placeholder false positive.
- Add focused positive/negative tests and run the affected foundation, context, decision-trace, live-execution, governance, doctor, security, and full regression checks.

## Non-Goals

- No changes to FACT_LEDGER authority/promotion semantics, Live Specs generation, Decision Trace storage, context source authority, capability denominator, router selection, host identity hook, C09 evidence, C08 scoring, package promotion, release, deployment, external I/O, memory, or orchestration.

## Requirements

1. A `VERIFIED` evidence claim must carry safe source, observed-at, freshness, scope, and binding metadata; missing or malformed metadata yields an honest incomplete result.
2. The read-only live trial must explicitly grant only the read capability required by its fixture and deny write, delete, execute, log, persist, egress, network, secret access, delegation, release/deploy, and owner-approval actions.
3. Requested execution values must be fixed to the existing bounded contract; host receipts remain observations and cannot widen authority.
4. Existing valid receipts and legacy C07 semantics remain readable where the current contract permits them; C09 stays `EVENT_EVIDENCE_UNAVAILABLE`.
5. Secret-like values are rejected and no hidden reasoning or secrets are persisted.

## Acceptance Criteria

- Focused tests prove valid provenance/binding, missing/stale/tampered evidence rejection, explicit permission denial, available-but-unauthorized rejection, network/delegation fail-closed behavior, secret redaction, and no regression of existing receipts.
- Existing Decision Trace, FACT/Live, context binding, capability foundation, governance drift, doctor, package/lifecycle, and full regression checks pass or record a precise environment blocker.
- No protected baseline hash changes; no release/promotion approval is requested.
- Final status is `PASS`, `PARTIAL`, or `BLOCKED` based on observed evidence; no unsupported host claim is made.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the current authority graph and exact editable gaps.
  - Work Steps: inspect the authority specs and runtime modules, refresh Anvien, inspect C09 status, record preserve-only and editable surfaces, and update the phase decisions.
  - Implementation Gate: actual status identifies the existing sources of truth, writers/readers, authority, freshness, conflict behavior, and gaps.
  - Acceptance: P0 is complete and implementation is limited to P1-A and P1-B.

### P1: Minimal contract hardening

- Phase Goal: close the two proven fail-open contract gaps without expanding architecture.
- Phase Boundary:
   - In scope: `.p2p/system/p2p_capabilities/evidence.py`, `.p2p/system/p2p_capabilities/trust.py`, `.p2p/system/p2p_capabilities/live_execution.py`, `.p2p/system/p2p_uiux/security.py`, and direct tests.
  - Out of scope: all governance sources, routers, host hooks, candidate promotion, and C09/C08.
  - Dependencies: P0 actual status, existing specs, and Anvien impact evidence.
- Phase Implementation Rule: implement P1-A, verify it, refresh actual status, then implement P1-B.
- Ordered Slice List:
  - P1-A: Enforce evidence provenance and binding metadata.
  - P1-B: Enforce the bounded live permission envelope.

- [x] P1-A: Enforce evidence and protected-fact provenance/binding metadata
  - Goal: prevent unsupported `VERIFIED` evidence or protected-fact writes while preserving contradiction and incomplete semantics.
  - Scope Boundary:
    - Editable: existing evidence/trust contracts and their direct tests.
    - Inspect-only: FACT_LEDGER, Live Specs, Decision Trace, and context source authority.
    - Preserve-only: existing evidence status vocabulary and no-progress behavior.
    - Out of scope: second evidence storage or generic confidence scoring.
  - Non-Goals: no new truth source or authority hierarchy.
  - Pre-flight Questions:
    - Data source: existing `ACTUAL_EVIDENCE` entries and their caller-supplied references.
    - Display permission: not applicable; this is a runtime contract.
    - DB read flow: existing in-memory contract and existing workflow/ledger references.
    - DB write flow: none beyond existing caller-owned evidence records.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; no UI or service deployment is in scope.
    - Playwright target: N/A.
    - Behavior test: `tests/test_p2p_capability_foundation.py` evidence cases.
    - Cleanup/quarantine: test fixtures are ephemeral and repo-local where possible.
    - External side effects: none.
    - N/A notes: this is a standard-library runtime contract.
  - Work Steps:
    1. Add structured validation using existing provenance vocabulary and safe deterministic fields.
       - UI flow check: N/A.
       - DB/data flow check: preserve existing evidence references; reject unbound verification.
       - Render location check: N/A.
       - Evidence target: `E1-P1A-EVID1`.
    2. Add positive and negative behavior tests, then run the direct and foundation suites.
       - UI flow check: N/A.
       - DB/data flow check: verify no store or ledger is added.
       - Render location check: N/A.
       - Evidence target: `E1-P1A-TEST1`.
  - Implementation Gate:
    - Run Anvien file-detail/impact for the nearest indexed owner and record the graph limitation for `.p2p/system` if applicable; source behavior and SPEC alignment must be confirmed.
  - Acceptance:
    - Source: evidence contract rejects missing, stale, mismatched, or unsafe provenance.
    - Runtime/UI: N/A.
    - DB/data: no second store and existing statuses remain compatible where metadata is valid.
    - Behavior test: direct positive, incomplete, contradicted, and tamper cases pass.
    - Cleanup/quarantine: no persistent fixture remains.
    - Evidence IDs: `E1-P1A-EVID1`, `E1-P1A-TEST1`.
    - Actual-status rows refreshed: evidence contract partial -> bound-correct.
  - Evidence Targets: direct test output, file-detail/impact, and change detection.
  - Actual-status Update: evidence and protected-fact contracts are now bound-correct; keep actual FACT_LEDGER and approval files preserve-only.
  - Commit Boundary: commit after the slice when Git is available; otherwise record the no-Git limitation.

- [x] P1-B: Enforce the bounded live permission envelope
  - Goal: make intent, availability, authorization, and observable host permission distinct for the existing read-only trial.
  - Scope Boundary:
    - Editable: existing live execution request validation, receipt binding, and direct live tests.
    - Inspect-only: routing/readiness and host identity hook.
    - Preserve-only: C09 host evidence taxonomy, proxy non-promotion, artifact/context bindings, and existing ledger.
    - Out of scope: general scheduler, permissions service, or host adapter.
  - Non-Goals: no attempt to prove unavailable host identity and no owner approval.
  - Pre-flight Questions:
    - Data source: existing requested execution object and official host receipt.
    - Display permission: N/A.
    - DB read flow: existing request/receipt files and Execution Ledger event.
    - DB write flow: existing trial output/receipt only.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: `tests/test_p2p_live_execution.py` and host receipt tests.
    - Cleanup/quarantine: existing test tear-down under repo-local `.tmp`.
    - External side effects: none; live mode is not invoked.
    - N/A notes: test host receipts remain synthetic evidence and do not change C09.
  - Work Steps:
    1. Add an explicit permission envelope to the existing request and require the fixed read-only values, including no network, delegation, secret access, persistence, or release actions.
       - UI flow check: N/A.
       - DB/data flow check: bind the envelope into request/receipt fingerprints without adding a store.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-PERM1`.
    2. Add hostile perturbation tests for altered permissions, network, task mode, and host permission observations, then run the live suite.
       - UI flow check: N/A.
       - DB/data flow check: verify rejected requests do not write trial artifacts beyond the guarded new root.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-EDGE1`.
  - Implementation Gate:
    - Run Anvien file-detail/impact for the live wrapper/owner, confirm C09 preservation, and keep the exact `.15`/`.18` artifact hashes unchanged.
  - Acceptance:
    - Source: permission values are explicit and validated before host handoff.
    - Runtime/UI: N/A; proxy/live semantics remain unchanged.
    - DB/data: request/receipt are hash-bound and no second ledger exists.
    - Behavior test: positive read-only flow and negative permission/network/delegation/secret cases pass.
    - Cleanup/quarantine: all test roots are removed.
    - Evidence IDs: `E1-P1B-PERM1`, `E1-P1B-EDGE1`.
    - Actual-status rows refreshed: live permission boundary partial -> bound-correct.
  - Evidence Targets: direct runtime tests, edge perturbation output, package/doctor/drift results.
  - Actual-status Update: local read-only boundary is bound-correct; keep C09 host evidence blocked.
  - Commit Boundary: commit after the slice when Git is available; otherwise record the no-Git limitation.

### P2: Verification and handoff

- [x] P2-A: Run focused, regression, governance, doctor, security, and candidate checks.
  - Goal: prove the changes at the nearest real boundaries and detect drift.
  - Work Steps: run direct suites, full build, Anvien detect-changes, package/installed doctor, governance drift, decision trace, secret scans, and existing project evals; create a new unpromoted candidate only if all package gates pass. A minimal scanner false-positive correction was included because the global doctor gate was blocked by an all-`x` documentation placeholder.
  - Implementation Gate: P1 slices are locally green.
  - Acceptance: every executed check has a recorded result; failures remain explicit. Final checks: full suite `119/119`, Decision Trace `24/24`, development/package doctor PASS, capability doctor PASS, governance drift PASS, and package verify PASS.
- [x] P2-B: Supervisor review.
  - Goal: independently review claims, diff, artifacts, C09 preservation, and evidence quality.
  - Work Steps: use the supervisor skill, fix only evidenced defects, rerun affected checks, and repeat review if needed.
  - Implementation Gate: P2-A evidence is complete.
  - Acceptance: Supervisor returned PASS in `reports/supervisor/rp_supervisor_260814_191500_by_gpt-5-codex_p2p-c10-evidence-permission-hardening.md`.
- [x] P2-C: Close the plan.
  - Goal: refresh actual status, evidence, benchmark, workflow state, and final result.
  - Work Steps: update companion files, run final validation, record no-Git limitation, and stop at PASS/PARTIAL/BLOCKED.
  - Implementation Gate: P2-A and P2-B are complete or explicitly blocked.
  - Acceptance: no release/promotion claim is made; the final report is self-contained; C09 remains blocked/unknown and candidate `.20` remains unpromoted.

## Risk Notes

- The installed runtime is copied into release packages; a material runtime change requires a new immutable unpromoted candidate only after gates pass.
- C09 host receipts remain unavailable for generic/default and canonical probes; this is an external evidence boundary and must not be “fixed” by accepting worker labels or prose.
- The workspace has no `.git`; required commit checkpoints cannot be honestly completed.
