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

## E4 - P4 FW01/QI Execution-Status Contract Repair Evidence

Matching plan items: P4-A, P4-B, P4-C

- E4-P4A-SRC1: independent source/spec re-derivation proves that QI owns
  the canonical execution token SUCCESS. The live checkpoint predicate in
  quality_intelligence.py:786-787 requires execution_status == "SUCCESS" and
  quality_status == "QUALITY_VERIFIED". AutoPilot emits
  TASK_DONE_CONTINUE only after evidence.status == "VERIFIED" at
  autopilot_loop.py:484-491; this is a loop/control-flow state, not a backend
  execution outcome. The canonical host/backend execution vocabulary in
  host_executor.py:65-66 contains SUCCEEDED, FAILED, INTERRUPTED, UNKNOWN,
  BLOCKED, CANCELLED, and PARTIAL_MUTATION_UNKNOWN, but not
  TASK_DONE_CONTINUE. The role bridge also preserves the distinction between
  execution success and quality proof. Relevant execution/evidence SPECs
  require missing, stale, or conflicting evidence to fail closed.
- E4-P4A-RED1: RED commit
  36f6877c36292af3a6e5c40b03451289f14a1efe added an executable regression
  over the real FW01 -> AERG -> QI -> durable-checkpoint path. Before any
  production edit, the observed tuple was
  (TASK_DONE_CONTINUE, QUALITY_VERIFIED, False, SUPPORTED, VERIFIED, CURRENT,
  STOP_BLOCKED, QUALITY_REVIEW, BLOCKED). The test required
  (SUCCESS, QUALITY_VERIFIED, True, SUPPORTED, VERIFIED, CURRENT,
  TASK_DONE_CONTINUE, VERIFIED, CHECKPOINTED), so the pre-fix run was a
  genuine RED reproduction of the cross-subsystem status mismatch.
- E4-P4B-SRC1: production commit
  66657b31d76bddbd35998dd7a4f81c473e847115 changes only
  p2p_fw01_loop.py in the production surface. The helper
  _qi_execution_status_from_fw01() projects only SUCCESS, SUCCEEDED, and
  TASK_DONE_CONTINUE to canonical QI SUCCESS; all other values are normalized
  but preserved, so failed, blocked, review-required, not-run, unknown, and
  arbitrary values cannot become SUCCESS. No QI allowlist expansion was made.
  The source hashes for quality_intelligence.py, aerg_engine.py, and
  aerg_model.py remain unchanged for this continuation.
- E4-P4B-TEST1: mapping falsification commit
  c4c5fc96a1e5a5206ca5ef118e2cfede714a9a2a covers successful aliases and
  negative statuses including FAILED, BLOCKED, STOP_BLOCKED,
  QUALITY_REVIEW_REQUIRED, NOT_RUN, UNKNOWN, TASK_DONE, TASK_UNRECOGNIZED,
  an arbitrary value, and None. Test-fixture corrections in test-only commit
  a716a5066db4b213af8ef44a392afbf0e4329ce6 make the FW01 quality seam tests
  explicitly bind their intended mock/fixture behavior rather than relying on
  the old mismatch. No production file is changed by that commit.
- E4-P4C-TEST1: fresh authoritative results are: production fresh checkpoint
  regression 1/1; conservative mapping regression 1/1; AERG/QI/FW01
  boundary 10/10; QI 44 pass with 1 skip; AERG focused 17/17; freshness
  subset 5/5; independent A-Z reconstruction 26/26 plus the two primary
  freshness extensions; FW01 focused 6/6; full capability 362 tests, OK,
  6 skips, exit 0; C43/RF01 18/18; compile boundary exit 0. The full
  suite's first unqualified Windows invocation reported nine identical UTF-8
  decoding errors; the authoritative python -X utf8 rerun passed 362/362,
  so those were classified as runner encoding, not product failures.
- E4-P4C-PROBE1: an evidence-only isolated runtime probe exercised the real
  path. Fresh actual AERG SUPPORTED/VERIFIED/CURRENT produced QI
  QUALITY_VERIFIED, checkpoint_allowed=True, captured QI execution status
  SUCCESS, FW01 TASK_DONE_CONTINUE, and durable VERIFIED/CHECKPOINTED.
  Age-expired actual AERG produced STALE/INCOMPLETE/STALE, QI
  QUALITY_REJECTED with STALE_EVIDENCE, FW01 STOP_BLOCKED, and durable
  QUALITY_REVIEW/BLOCKED. Missing/insufficient evidence also remained
  QUALITY_REVIEW/BLOCKED. The temporary probe was removed and no runtime
  artifact remains.
- E4-P4C-PROOF1: Git independently binds the source/test subject to branch
  codex/p2p-post74-development-01, HEAD
  a716a5066db4b213af8ef44a392afbf0e4329ce6, with repair ancestry
  430c47d -> 11c3e9e -> a10be51 -> 5273133 -> 45ef5a2 ->
  ad39230 -> 6e53189 -> 7e6b29f -> 0ba5f39 -> ce641d6 -> cbf7af9 ->
  0910b18 -> b1fded1 -> 25cf498 -> 36f6877 -> 66657b3 -> c4c5fc9 ->
  a716a50. The production
  diff from b1fded1cc3bcfdf6e50923a457655af51b96e34d contains only
  p2p_fw01_loop.py; the remaining two scoped changes are tests. AERG
  engine/model/QI are unchanged. The broad owner-dirty worktree is preserved
  and exact-path staging is required for the final documentation commit.
  Anvien was refreshed, but its indexed projection still cannot resolve the
  hidden .p2p/system targets; file-detail/impact risk therefore remains
  UNKNOWN rather than being claimed low.
- E4-P4C-STATE1: protected governance remains .19=PROMOTED_VERIFIED,
  .74=SEALED_UNPROMOTED, promotion.allowed=false, CPT01-R2 remains
  host-capability blocked, and the current governance file SHA-256 is
  5820a855d52ae5d44c3fe30ce9d4b0a112f8ad75a44cfbd6c73126314e332029.
  RF01, C43, release/deployment state, Owner authority, and prior REJECT
  reports were not mutated. The prior REJECT report at 430c47d remains
  immutable audit evidence.
- E4-P4C-HANDOFF1: the continuation is ready only for the separately
  requested Supervisor review at terminal
  P2P_AERG_FW01_QI_STATUS_CONTRACT_REPAIR_READY_FOR_SUPERVISOR_REVIEW.
  This run performed no Supervisor review, independent verification, Owner
  approval, promotion, release, deployment, or host mutation.

### E4 Closure

The narrow contract mismatch is closed in source/test subject
a716a5066db4b213af8ef44a392afbf0e4329ce6: QI receives canonical SUCCESS for
the proven successful FW01 completion path, while the loop state
TASK_DONE_CONTINUE remains observable at FW01. Fresh legitimate checkpointing
is restored and all tested unsafe paths remain fail-closed. The final
artifact/report commit is a descendant containing no production source. This
is a coder handoff, not a Supervisor or independent verdict.

Bounded repair and handoff evidence are complete at HEAD `0910b18a215a4b8bae0c8b0d90da0f692067d5cb`. `NEW_TEST_FAILURES=0`, `NEW_RUNTIME_FINDINGS=0` within the repaired invariant, and `NEW_VALIDATOR_FAILURE_CLASSES=0`; validator debt remains exactly seven inherited classes. Supervisor review is explicitly out of scope for this plan execution.
