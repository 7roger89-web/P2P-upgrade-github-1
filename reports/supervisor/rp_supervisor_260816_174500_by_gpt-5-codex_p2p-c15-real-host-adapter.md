# Supervisor Report: P2P-C15 Real Host Adapter and `.19 + C15` Candidate

Verdict: REJECT

## Metadata

- Report file: `rp_supervisor_260816_174500_by_gpt-5-codex_p2p-c15-real-host-adapter.md`
- Review time: 2026-08-16 17:45 Asia/Saigon
- Reviewer: gpt-5-codex
- Repo/project: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: current P2P-C15 host-adapter hardening and temporary official
  `.19 + C15` candidate
- Claim reviewed: C15 can be certified as native real-host delegated execution
  and official `.19 + C15` integration can be verified.
- Authority used: latest P2P-C15 owner request, AGENTS.md, C09/C10/C11/C12
  runtime contracts, official ZIP hash, current source, fresh tests, and
  candidate doctor output.
- Related artifacts: coder report, C15 field proof, lineage comparison,
  `.tmp/p2p-c15-combined-candidate-20260816`, official ZIP.

## Executive Summary

- Problem: the stronger C15 request required a real host invocation/receipt
  bound through the existing C15 controller and a proven official `.19 + C15`
  candidate.
- Decision: the local adapter contract is implemented and fail-closed, but the
  project runtime has no callable bridge from the desktop `multi_agent_v1`
  surface; the real worker receipt was not written to the project ledger. The
  combined candidate passes portable doctor/import checks but is not canonical
  release-integrated.
- Required outcome: keep C15 blocked for real-host certification and do not open
  C16. A future re-review needs a supported host callback with an official
  receipt plus a canonical lineage/package path.

## Blocking Findings

### [BLOCKER] Native C15 host invocation and receipt binding are not proven

File: `.p2p/system/p2p_capabilities/bounded_delegation.py:1063-1222`

Issue: `CodexHostAdapter` correctly requires a host executor callback and a
fresh official C09 receipt, but the project has no callable bridge that invokes
the desktop `multi_agent_v1` tool from this Python runtime. The actual worker
`01a008ca-1c74-7592-a316-4e45894027ce` completed outside the adapter. The
project ledger check found 18 host identity receipts and no matching receipt
for that worker.

Evidence: source inspection, fresh adapter tests `26/26 PASS`, real host wait
receipt, and ledger scan with `has_real_worker_receipt=false`.

Why this blocks acceptance: without the host-owned receipt bound to the
persisted handoff, C15 cannot prove `handoff -> host run -> result` or claim
the C11 DONE transition was caused by a real host run. Using a replayed result
or manually writing a receipt would violate the owner request and fail-closed
boundary.

Fix direction: expose a supported host-owned callback/receipt bridge to the
project runtime, or provide an equivalent official integration surface. The
bridge must return the structured worker result and allow the adapter to match
fresh identity/run evidence without synthetic fields.

Re-review evidence required: one real read-only delegated task invoked through
`CodexHostAdapter`, raw official receipt, normalized C15 receipt, independent
parent verification, C11 `DONE`, and a rejection run using the same adapter.

### [BLOCKER] Official `.19 + C15` canonical integration is not proven

File: `scripts/p2p_development_control.py:335-358`; `scripts/package_release.py:397-469`

Issue: the development tree is `8.4.7-C-codex.15`, below promoted `.19`, and
the development package builder rejects it with `LINEAGE_REGRESSION`. The
temporary candidate uses official `.19` content plus five controlled C15
delta files and passes portable doctor/import checks, but the canonical package
builder cannot run because the copied builder depends on the development-control
module absent from official `.19`.

Evidence: official ZIP SHA-256
`3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`,
`403 mapped / 390 exact / 13 mismatched / 0 missing` comparison, temporary
candidate tree/ZIP hashes, candidate doctor PASS, current builder
`LINEAGE_REGRESSION`, and candidate builder missing-module failure.

Why this blocks acceptance: changing VERSION or copying development governance
would not establish canonical `.19` provenance and could silently alter the
official Design Intelligence/runtime guarantees. The candidate is therefore a
verification fixture, not an integration-verified package.

Fix direction: use the official P2P update/rebase/release mechanism to port the
explicit C15 delta onto `.19`, resolve all 13 mismatches, regenerate governed
metadata, and rerun package/doctor/regression gates without promotion.

Re-review evidence required: canonical candidate manifest/provenance, all 13
mismatch resolutions, candidate package build PASS, C10-C15 regression PASS,
and confirmation the official ZIP was unchanged.

## Source-Level Clearance Notes

- `.p2p/system/p2p_capabilities/bounded_delegation.py`: partial/blocked for
  the requested claim. The adapter, receipt allow-list, provenance fields,
  proposal-only enforcement, unified plan fingerprint, and one-child checks
  are present; the host callback remains an external seam.
- `.p2p/system/p2p_capabilities/__init__.py`: clear additive export only;
  existing barrel preserved.
- `tests/test_p2p_bounded_delegation.py`: clear local contract coverage;
  tests use controlled fixtures and do not prove a real host run.
- `.p2p/system/scripts/p2p_host_identity_hook.py`: clear and preserved as the
  official receipt authority; no receipt was fabricated.
- `scripts/package_release.py` / `scripts/doctor.py`: candidate wiring is
  partial because official `.19` and development-control lineage are not
  reconciled.
- C10/C11/C12/C13/C14 files: no unintended production edits observed;
  affected regression evidence is green.

## Evidence Checked

Passed:

- `tests.test_p2p_bounded_delegation` -> `26/26 PASS`.
- `tests.test_p2p_live_execution` -> `16/16 PASS`.
- C11/C12/Decision Trace -> `44/44 PASS`.
- host receipt/context/capability/beginner routing -> `61/61 PASS`.
- release packaging tests -> `2/2 PASS`.
- C15 field harness -> `all_checks_pass=true`.
- current development doctor -> `ok=true`.
- temporary candidate doctor and runtime import/compile -> PASS.
- Anvien graph refreshed; target source parsed with `changedSinceAnalyze=false`
  after refresh. File-level C15 risk is high; this is a blast-radius warning,
  not a permission expansion.
- PRE-EXISTING/ENVIRONMENT DRIFT: the full beginner certification evaluator
  returned `harness_status=FAIL` and `beginner_readiness=NOT_CERTIFIED` because
  its protected runtime-tree snapshot reported
  `protected_paths_unchanged=false`. Scenario isolation, canonical 8/8,
  machine schema, user-project writes, and external-integration checks remained
  green. This was recorded separately and not changed to force a green result.

Failed / blocked:

- Native C15 real-host end-to-end proof -> NOT PROVEN because no project ledger
  receipt matched the real worker.
- Current package build -> `LINEAGE_REGRESSION` (`.15 < .19`).
- Temporary candidate canonical package build -> missing
  `p2p_development_control` in the official base.
- Anvien `detect-changes` -> Git exit 129 because the repo has no `.git`.

Not run:

- C16 implementation and certification: intentionally not run by owner scope.
- Production release/deployment/promotion: intentionally not run.
- Logistics project runtime/UI: intentionally not touched.

## Invariant Closure

- affected invariant: C15 host identity/result binding, proposal-only evidence,
  parent verification, C11 completion, official lineage, and package provenance.
- sibling surfaces checked: C09 receipt parser/hook, C10 trace/evidence, C11
  task store, C12 live execution, C13/C14 capability/context/beginner tests,
  C15 controller/CLI/tests, doctor/package scripts, official ZIP, and temporary
  candidate.
- residual unverified same-invariant surfaces: native host callback/receipt
  bridge and canonical `.19 + C15` package lineage remain open blockers.

## Required Fix List For Resubmission

1. Obtain or expose the official host-owned callback/receipt bridge; run one
   real bounded read-only C15 delegation through the adapter.
2. Preserve raw and normalized receipts, prove parent verification and C11
   `DONE`, and prove the same-path invalid result remains non-DONE.
3. Rebase/port only the reviewed C15 delta onto official `.19` through the
   canonical mechanism; classify all 13 mismatches and build the temporary
   candidate with package/doctor PASS.
4. Re-run C10-C15 regression and verify the official ZIP hash is unchanged.

## Overall Evaluation

Implementation quality is bounded and fail-closed, and local regression is
strong. Evidence quality is insufficient for the stronger requested
certification because the real host invocation is not connected to the
project-owned C15 handoff/ledger path and official lineage is not integrated.
Verdict remains REJECT for real-host certification and `.19 + C15`
integration. C15 local foundation remains valid; C16 must remain closed.
