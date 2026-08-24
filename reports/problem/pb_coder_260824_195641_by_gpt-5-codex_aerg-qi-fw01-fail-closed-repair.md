# Problem Report — AERG QI/FW01 Fail-Closed Repair

## Classification

Two confirmed production defects were repaired in the bounded AERG -> QI ->
FW01 checkpoint invariant. No new unresolved defect was found in that
invariant after the repair suite and full capability suite.

## Root causes

1. `quality_intelligence.py::build_quality_verdict()` accepted required values
   outside its explicit failure list as if they were proof. This made stale,
   warning, unknown, skipped, incomplete, and unrecognized required results
   eligible for `QUALITY_VERIFIED` and checkpointing.
2. `p2p_fw01_loop.py::Fw01Loop.step()` used signature compatibility to omit
   `aerg_result` from a legacy QI callable, then trusted the callable's
   affirmative result. The actual stale AERG result was therefore not enforced
   at the checkpoint boundary.

## Repair

- `ce641d6`: explicit proof-status allowlist plus fail-closed required-status
  classifier; optional-evaluation behavior preserved.
- `cbf7af9`: one FW01 post-QI clamp over the actual AERG result, reusing current
  QI failure vocabulary and preserving fresh behavior; observation timestamp
  ordering corrected for the fresh predicate.
- `0910b18`: direct regression for actual AERG result mappings in current QI.

## Evidence

The coder report contains the RED checkpoint, focused/full results, source
scope, inherited validator matrix, protected-state proof, and audit-history
preservation:

`reports/coder/rp_coder_260824_195641_by_gpt-5-codex_aerg-qi-fw01-fail-closed-repair.md`

Terminal: `P2P_AERG_QI_FW01_FAIL_CLOSED_REPAIR_READY_FOR_SUPERVISOR_REVIEW`.
This report does not authorize or perform Supervisor review, independent
verification, Owner approval, promotion, release, deployment, or host action.
