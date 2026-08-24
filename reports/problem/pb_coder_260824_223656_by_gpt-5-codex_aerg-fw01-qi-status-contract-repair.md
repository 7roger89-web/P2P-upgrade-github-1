# Problem Report — AERG/FW01/QI Fresh-Checkpoint Status Contract Repair

## Classification

CROSS-SUBSYSTEM_STATUS_CONTRACT_MISMATCH

Safety was fail-closed, but the legitimate fresh FW01 progression was blocked.
This was not an AERG freshness defect, QI fail-open defect, compatibility
bypass, or release/promotion defect.

## Evidence-backed meaning of the statuses

QI checkpoint eligibility accepts canonical execution status SUCCESS.
TASK_DONE_CONTINUE is emitted by AutoPilot after verified task completion and is
an FW01 loop/control-flow state. The backend execution-status vocabulary does
not include it. The two values cannot be collapsed at the QI boundary.

## Exact failure

Before the repair, real FW01 execution supplied TASK_DONE_CONTINUE to QI while
the actual AERG result was SUPPORTED/VERIFIED/CURRENT. QI returned
QUALITY_VERIFIED but checkpoint_allowed=False, and FW01 persisted
QUALITY_REVIEW/BLOCKED.

RED commit:
36f6877c36292af3a6e5c40b03451289f14a1efe

## Repair

Production commit:
66657b31d76bddbd35998dd7a4f81c473e847115

FW01 now projects only explicit successful completion states
SUCCESS, SUCCEEDED, and TASK_DONE_CONTINUE into canonical QI SUCCESS. Failed,
blocked, review-required, not-run, unknown, and arbitrary values remain
non-success. QI was not widened.

## Safety preservation

The existing AERG clamp and QI required-status fail-closed classifier remain
active. Fresh actual AERG evidence now reaches VERIFIED/CHECKPOINTED. Stale,
contradicted, subject-mismatch, insufficient, malformed, provenance/authority,
compatibility, fixture/mock/live, self-verification, and required-status cases
remain blocked. Serialization and durable checkpoint observations preserve the
unsafe truth.

## Regression summary

- Fresh checkpoint: 1/1.
- Unsafe status mappings: 1/1.
- AERG/QI/FW01 boundary: 10/10.
- AERG: 17/17; freshness: 5/5; QI: 44 pass/1 skip; FW01: 6/6.
- A-Z: 26/26 plus two primary freshness extensions.
- Full capability: 362 pass/6 skip.
- C43/RF01: 18/18.
- Compile: PASS.
- Validator: 52/59 with exactly seven inherited classes, no new class.

The first unqualified Windows full-suite run failed in nine tests due to the
same text-decoding invocation issue. The UTF-8 rerun passed all 362 tests and
is the authoritative result.

## Scope

Production scope is one file: p2p_fw01_loop.py. QI, AERG engine, and AERG
model are unchanged for this continuation. Test-only fixture corrections are
isolated to the FW01 test surface. No new state machine, verifier, queue,
scheduler, router, database, promotion path, release path, or deployment path
was introduced.

## Status

No unresolved defect was found in the repaired invariant under the executed
checks. The branch is ready for a separate Supervisor review:

P2P_AERG_FW01_QI_STATUS_CONTRACT_REPAIR_READY_FOR_SUPERVISOR_REVIEW

This report does not perform or authorize Supervisor review, independent
verification, Owner approval, promotion, release, deployment, or host action.
