# P2P AERG QI/FW01 Fail-Closed Repair Evidence Ledger

## Metadata

- Date: `2026-08-24`
- Plan: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-plan.md`
- Evidence: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-evidence.md`
- Benchmark: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-benchmark.md`
- Actual status: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-actual-status.md`

## Evidence Rules

- Git/source/runtime truth outranks reports and claimed test counts.
- Each evidence ID identifies one reproducible fact or command result.
- RED evidence must precede production repair commits.
- Protected state, inherited validator debt, and prior REJECT reports are preserve-only.
- No evidence in this ledger authorizes Supervisor review, Owner approval, promotion, release, deployment, publication, or host mutation.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GIT1`: current branch `codex/p2p-post74-development-01`, HEAD `0910b18a215a4b8bae0c8b0d90da0f692067d5cb`; required chain is `430c47d -> 11c3e9e -> a10be51 -> 5273133 -> 45ef5a2 -> ad39230 -> 6e53189 -> 7e6b29f -> 0ba5f39 -> ce641d6 -> cbf7af9 -> 0910b18`.
- `E0-P0A-SRC1`: current source inspection identifies the required QI loop at `quality_intelligence.py:697-769` and the FW01 compatibility dispatch/checkpoint path at `p2p_fw01_loop.py:914-1038`.
- `E0-P0A-SPEC1`: relevant execution/evidence, foundation architecture, and test/eval SPECs require missing/stale/conflicting evidence to remain incomplete/contradicted and prohibit duplicate certification systems.
- `E0-P0A-GRAPH1`: final pre-handoff Anvien refresh completed from the Git worktree with `scanned=907`, `parsed_code=164`, `failed=0`, `documents=544`, graph `37628` nodes / `43443` relationships. Duplicate repository names and hidden target path projection prevented exact file-detail/impact resolution; this is a tooling limitation, not a low-impact claim.
- `E0-P0A-REPORT1`: current independent REJECT is preserved at `reports/supervisor/rp_supervisor_260824_184807_by_gpt-5-codex_aerg-independent-verification-after-repair.md`; prior REJECT at `reports/supervisor/rp_supervisor_260824_165924_by_gpt-5-codex_p2p-aerg-independent-verification.md` remains preserve-only.
- `E0-P0A-STATE1`: protected governance inspection remains `.19 PROMOTED_VERIFIED`, `.74 SEALED_UNPROMOTED`, `promotion.allowed=false`, CPT01-R2 host-capability blocked; no protected path is editable.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-TEST1`: the committed test matrix covers 3 explicit proof statuses, 12 required non-proof/unknown statuses, one optional-WARN control, and four actual-AERG-to-QI mapping cases. The pre-repair target run executed 7 test methods and produced 13 failing assertions with 0 errors, including the required-status fall-through and compatibility bypass.
- `E1-P1A-RED1`: RED checkpoint commit `0ba5f39aea82f1d7f9ed0c8a04c92bff2f81c3c9`; required `STALE`, `EXPIRED`, `WARN`, `WARNING`, `UNKNOWN`, `NOT_RUN`, `SKIPPED`, `INCOMPLETE`, `NOT_VERIFIED`, and unrecognized statuses reached the unsafe QI result before repair. Existing unavailable mappings were already blocking and remained unchanged.
- `E1-P1B-SRC1`: QI repair commit `ce641d641cccfb8f02aea498cccb22cddb56126e` adds `_required_eval_failure()` and an explicit proof-status allowlist inside the existing required-evaluation loop. Optional evaluation handling and the existing AERG mapping vocabulary are unchanged; no second QI engine was added.
- `E1-P1B-TEST1`: the repaired boundary test is `8/8`, exit `0`; the full QI-focused suite is `44` tests, `1` skip, exit `0`. Actual AERG results independently map `STALE -> QUALITY_UNKNOWN/STALE_EVIDENCE`, `CONTRADICTED -> QUALITY_REJECTED/QUALITY_CONFLICT`, `SUBJECT_MISMATCH -> QUALITY_UNKNOWN/CERTIFICATION_SCOPE_MISMATCH`, and `INSUFFICIENT -> QUALITY_REJECTED/MISSING_REQUIRED_EVIDENCE`.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-RED1`: the pre-repair real `Fw01Loop.step()` compatibility callable omitted `aerg_result`; stale actual AERG and missing actual-AERG cases returned `TASK_DONE_CONTINUE` with durable `VERIFIED/CHECKPOINTED` instead of stopping. This is preserved by the RED commit and was not repaired through test-only behavior.
- `E2-P2A-TEST1`: the green compatibility matrix covers fresh allow, stale block, missing-AERG block, and direct actual `STALE`, `CONTRADICTED`, `SUBJECT_MISMATCH`, and `INSUFFICIENT` shapes. All unsafe cases are blocked and no unsafe checkpoint is accepted.
- `E2-P2B-SRC1`: FW01 repair commit `cbf7af9590d4cfb2e68eaa028298d989aa6e0945` adds one post-QI AERG safety clamp requiring `SUPPORTED/VERIFIED/CURRENT`, bound subject/provenance, mechanical or independent authority, and explicit contract support. It reuses current QI failure vocabulary and does not add a verifier/state machine. Observation timestamp ordering was corrected so a valid fresh observation is not made microscopically future-dated relative to the AERG engine clock.
- `E2-P2B-TEST1`: repaired AERG/QI/FW01 boundary test is `8/8`, exit `0`; existing FW01 focused suite is `6/6`, exit `0`, including fresh compatibility behavior. Fresh compatibility returns `TASK_DONE_CONTINUE` with durable `VERIFIED/CHECKPOINTED`; stale/missing/unsafe actual AERG results return `STOP_BLOCKED` with `QUALITY_REVIEW_REQUIRED` and `QUALITY_REVIEW/BLOCKED` checkpoint state.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-TEST1`: final measured results are: full capability `360 tests`, `6 skipped`, exit `0`; AERG focused `17/17`, exit `0`; freshness subset `5/5`, exit `0`; independent A-Z reconstruction `26/26` plus two freshness extensions `2/2`; QI `44 tests`, `1 skipped`, exit `0`; FW01 `6/6`, exit `0`; C43/RF01 `18/18`, exit `0`; compile boundary exit `0`; validator `52/59`, exit `1` with exactly the seven inherited classes.
- `E3-P3A-PROOF1`: current HEAD/branch and ancestry were re-derived from Git; production diff from `5273133` contains only `quality_intelligence.py` and `p2p_fw01_loop.py`, plus the bounded regression test. `aerg_engine.py` and `aerg_model.py` remain unchanged. Both prior REJECT artifacts compare unchanged from their respective commits. Protected governance remains `.19 PROMOTED_VERIFIED`, `.74 SEALED_UNPROMOTED`, `promotion.allowed=false`, and CPT01-R2 host-capability blocked. Final Anvien `detect-changes` saw only the six documentation handoff paths plus the pre-existing owner-dirty `adapter_registry.json`; no new production source change was present.
- `E3-P3B-REPORT1`: coder/problem reports and the 2026-08-24 notes-log entry are prepared in the final evidence commit; they link this ledger and preserve the prior report artifacts without overwriting them.
- `E3-P3B-HANDOFF1`: final repair/test commits are `ce641d6`, `cbf7af9`, and `0910b18`; final handoff terminal is `P2P_AERG_QI_FW01_FAIL_CLOSED_REPAIR_READY_FOR_SUPERVISOR_REVIEW`. No Supervisor review, independent verification, Owner approval, promotion, release, deployment, or host action was run.

## Closure Evidence

Bounded repair and handoff evidence are complete at HEAD `0910b18a215a4b8bae0c8b0d90da0f692067d5cb`. `NEW_TEST_FAILURES=0`, `NEW_RUNTIME_FINDINGS=0` within the repaired invariant, and `NEW_VALIDATOR_FAILURE_CLASSES=0`; validator debt remains exactly seven inherited classes. Supervisor review is explicitly out of scope for this plan execution.
