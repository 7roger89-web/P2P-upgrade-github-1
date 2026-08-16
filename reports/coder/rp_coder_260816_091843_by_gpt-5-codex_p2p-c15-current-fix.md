# Coder Report — P2P-C15 Current Fix and Field Evidence

## Scope

This report covers the bounded C15 follow-up only:

- make the semantic handoff contract fingerprint stable across equivalent
  fresh runs while excluding volatile preflight/run metadata;
- make the C15 decision trace identity stable across volatile decision time;
- add the missing-candidate boundary test;
- add a reusable project-style local field harness and an 18-case evaluation
  matrix;
- refresh evidence without changing C11/C12, Logistics, the official `.19`
  artifact, or release state.

No second task store, executor, router, ledger, worker runtime, scheduler,
parallel path, background process, host identity simulation, or external
connector was introduced.

## Authority and recovered state

- User C15 brief from the attached pasted-text file.
- Project `AGENTS.md` and the existing C11/C12/C15 plan/evidence ledgers.
- Existing C11 durable task state, C12 foreground execution, C10 evidence and
  Decision Trace are the source-of-truth surfaces.
- Official promoted baseline remains
  `8.4.7-C-codex.19`, SHA-256
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Development source remains `.15`; it was not promoted or rewritten to
  `.19`.

## Invariant family map

| Family | Source of truth | C15 proof |
|---|---|---|
| DIRECT/DELEGATE/BLOCKED | `bounded_delegation.py` | strategy tests and field A/B |
| Handoff identity | `WorkerHandoff` plus semantic plan fingerprint | fingerprint regression and field B |
| Permission/scope/depth | C15 permission envelope and handoff/result contracts | focused tests and field E |
| Durable owner/completion | existing C11 `TaskStateStore` | parent verification and field D |
| Evidence/trace | existing C10 evidence and Decision Trace | focused trace test and doctor trace check |
| Recovery | C11 checkpoint/resume plus bounded retry/fallback | focused tests and field F |
| Runtime/package boundary | existing CLI/package/doctor allowlists | full suite and development checks |

## Changes inspected

- `.p2p/system/p2p_capabilities/bounded_delegation.py`
  - `_plan_contract_fingerprint` at line 1027 hashes only immutable semantic
    plan/task handoff inputs.
  - `_record_decision_trace` at line 1445 derives the trace ID without
    `decided_at`.
  - `_build_handoff` at line 1493 binds the semantic fingerprint, not the
    volatile full plan serialization.
- `tests/test_p2p_bounded_delegation.py`
  - added `test_missing_candidate_state_blocks_before_delegation` at line 161.
- `scripts/p2p_c15_field_test.py`
  - reusable repo-local disposable fixture runner for A-F.
- C15 field evidence and evaluation matrix docs.

C11/C12 production source files were not changed by this follow-up. No file
under `D:\Logistics_App_Copy` was changed.

## End-to-end evidence

The verified local path is:

`request -> existing C11 preflight -> C15 strategy -> bounded handoff -> one
foreground callback -> persisted proposal receipt -> fresh parent verification
-> existing C11 completion/checkpoint`

Observed outcomes:

- field A: direct bounded action reaches `DONE`;
- field B/D: delegated callback returns proposal-only output and parent reaches
  `DONE` only after current-candidate/evidence verification;
- field C: incomplete verification remains `VERIFICATION_FAILED`;
- field E: attempted child delegation is rejected as
  `CHILD_DELEGATION_FORBIDDEN`;
- field F: callback interruption leaves durable `ACTIVE` plus
  `SAFE_TO_RESUME`; resume does not auto-start.

## Verification

- Focused C15: `24/24 PASS`.
- Affected C15+C11+C12: `64/64 PASS`.
- Full repository suite: `218/218 PASS`.
- Project-style field harness: A-F `all_checks_pass=true`; JSON SHA-256
  `69fa8143c065d6960ec0ae4540aabcbc0ad8f4df8bffd05011ed024023437dc0`.
- Fresh Anvien root/system analysis: parse failures `0`; C15 file is
  `stale=false`, 283 symbols, 607 local relationships, 832 unresolved
  references, high graph warning.
- File-level impact reports 69 contained/impacted symbols in the additive C15
  module. Symbol-level lookup for the two edited methods is unresolved by the
  current graph index; this is recorded as an Anvien resolution limitation,
  not treated as zero runtime impact.
- `anvien detect-changes` cannot produce a diff because the project has no
  `.git`; no repository was initialized.

## Governance and release boundaries

- Official `.19` hash rechecked unchanged.
- Development doctor found the C15 runtime, canonical 8/8, optional Aesthetica
  separation, package metadata `.15`, installed foundation, and decision-trace
  checks healthy. Its overall result is `FAIL` only because the existing
  protected notes log is already drifted outside this C15 source change.
- Governance drift independently reports the same protected notes-log drift;
  it was not suppressed, deleted, or repaired in this task.
- A fresh package build is intentionally blocked by the existing lineage guard:
  development `.15` is below promoted `.19`. No promotion or release claim is
  made.

## Residual unverified surfaces

- Live host child callback/identity receipt is not available in this repository;
  the field harness uses only the supported local foreground callback and does
  not simulate host identity.
- Official release/promotion and deployment were not attempted.
- The protected notes-log drift and missing Git checkpoint remain outside the
  bounded C15 implementation and are preserved as risks.

## Handoff

Local bounded C15 work is ready for independent supervisor review. The correct
terminal claim is `PASS / BOUNDED_DELEGATION_FOUNDATION_READY` for the local
callback-backed contract, with the explicit host/release/governance limits
above. No commit is claimed because `.git` is absent.
