# Coder Report — AERG QI/FW01 Fail-Closed Repair

## Terminal

`P2P_AERG_QI_FW01_FAIL_CLOSED_REPAIR_READY_FOR_SUPERVISOR_REVIEW`

This is a coder handoff only. Supervisor review, independent verification,
Owner approval, promotion, release, deployment, and host mutation were not
performed.

## Exact subject binding

- Worktree: `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-post74-development-01`
- Branch: `codex/p2p-post74-development-01`
- Production/test subject before handoff artifacts: `0910b18a215a4b8bae0c8b0d90da0f692067d5cb`
- Current implementation ancestry:
  `430c47d -> 11c3e9e -> a10be51 -> 5273133 -> 45ef5a29ff549199293ad0ea389abba91460caf0 -> ad39230 -> 6e53189 -> 7e6b29f -> 0ba5f39 -> ce641d6 -> cbf7af9 -> 0910b18`
- Prior independent REJECT `6e53189` remains an ancestor and its report is unchanged.

The broad worktree remains owner-dirty in pre-existing paths. Only the scoped
repair/test/report paths listed below were touched by this task.

## Invariant Family Map

| Family | Source of truth | Required invariant | Result |
|---|---|---|---|
| AERG freshness and contradiction | `aerg_engine.py`, AERG model | stale remains stale; contradiction precedence remains observable | preserved and regressed |
| AERG serialization | AERG result `to_dict`/quality input | serialized stale truth cannot become current/verified | preserved and regressed |
| QI required-evaluation proof | `quality_intelligence.py::build_quality_verdict` | only explicit proof statuses can satisfy required evaluations | repaired |
| QI actual AERG mapping | existing `aerg_result` mapping in QI | stale/contradicted/scope/insufficient use existing failure vocabulary | preserved and regressed with actual results |
| FW01 compatibility/checkpoint | `p2p_fw01_loop.py::Fw01Loop.step` | compatibility signature cannot erase actual AERG safety | repaired |
| provenance/authority | AERG result fields and FW01 gate | subject/provenance binding and mechanical/independent authority remain required | enforced by clamp |
| protected/audit state | Git and `governance/development-control.json` | prior reports, `.19`, `.74`, CPT01-R2 and promotion state remain unchanged | preserved |

## Root causes and bounded repairs

1. QI required-status fall-through: the prior loop recognized selected failure
   and unavailable values but implicitly treated other required values as proof.
   `ce641d6` adds an explicit proof-status allowlist and a fail-closed classifier;
   unknown values become `MISSING_REQUIRED_EVIDENCE`.
2. FW01 compatibility bypass: signature compatibility omitted `aerg_result`
   for a callable that did not accept it, then trusted the callable's affirmative
   verdict. `cbf7af9` adds a single post-QI safety clamp over the actual AERG
   result. It requires `SUPPORTED`, `VERIFIED`, `CURRENT`, bound subject,
   bound provenance, permitted authority, and explicit contract support before
   checkpoint acceptance.
3. Fresh observation ordering: the observation timestamp is captured before
   the AERG engine clock is instantiated, preventing a valid fresh result from
   being made microscopically future-dated by the compatibility safety check.

The legacy compatibility API shape remains supported. Its omitted parameter is
not treated as permission to omit the actual AERG safety proof. No second QI
engine, verifier, state machine, persistence layer, scheduler, router,
promotion path, release path, or deployment path was introduced.

## Test-first evidence

- RED commit: `0ba5f39aea82f1d7f9ed0c8a04c92bff2f81c3c9`.
- Before production repair, the targeted test executed 7 methods and produced
  13 failing assertions with 0 errors: required non-proof values reached the
  unsafe QI result, and stale/missing-AERG compatibility cases reached
  `TASK_DONE_CONTINUE` with `VERIFIED/CHECKPOINTED`.
- QI/FW01 boundary test after repair: `8/8`, exit `0`.
- The direct actual-AERG QI regression covers `STALE`, `CONTRADICTED`,
  `SUBJECT_MISMATCH`, and `INSUFFICIENT` with the existing QI failure classes.

## Validation results

| Check | Fresh result | Exit |
|---|---:|---:|
| AERG focused | 17/17 | 0 |
| Freshness subset | 5/5 | 0 |
| Independent A-Z reconstruction | 26/26 | 0 |
| Freshness extensions | 2/2 | 0 |
| QI focused | 44 pass / 1 skip | 0 |
| FW01 existing focused | 6/6 | 0 |
| AERG/QI/FW01 boundary | 8/8 | 0 |
| C43/RF01 | 18/18 | 0 |
| Full capability | 360 pass / 6 skip | 0 |
| Compile boundary | PASS | 0 |
| Framework validator | 52/59; 7 inherited failures | 1 |

Full capability emitted pre-existing `ResourceWarning` messages from
`test_bounded_documentation_write.py`; there were no test failures or errors.

The independent A-Z reconstruction re-derived semantics rather than trusting
the stored count: `26/26`, plus age-only expiry `2/2` freshness extensions.

## FW01 end-to-end boundary

The real isolated path exercised execution -> durable observation -> AERG -> QI
-> checkpoint. A compatibility QI callable without `aerg_result` could not
checkpoint stale, missing, contradicted, subject-mismatched, or insufficient
actual AERG evidence. Fresh subject-correct evidence retained
`TASK_DONE_CONTINUE` and durable `VERIFIED/CHECKPOINTED` behavior.

## Source and scope proof

Production changes are limited to:

- `.p2p/system/p2p_capabilities/quality_intelligence.py`
- `.p2p/system/p2p_capabilities/p2p_fw01_loop.py`

The bounded regression is:

- `.p2p/system/p2p_capabilities/tests/test_aerg_qi_fw01_fail_closed.py`

From `5273133..0910b18`, the changed capability paths are exactly those two
production files plus the bounded regression test. `aerg_engine.py`,
`aerg_model.py`, and the protected governance/release surfaces are unchanged.

Anvien was refreshed from the correct Git worktree: `scanned=907`,
`parsed_code=164`, `failed=0`, `documents=544`, graph `37628` nodes /
`43443` relationships. The indexed registry has duplicate repository names
and does not resolve the hidden `.p2p/system` target paths for exact
file-detail/impact; this is reported as an evidence limitation, not a low-risk
claim. Direct source, Git diff, and runtime evidence were used instead.

## Inherited framework debt

The validator remains `52/59` with exactly these seven inherited classes:

- `V01-schema-valid`
- `V03-family-registered`
- `V05-dep-integrity`
- `V09-freshness-vocab`
- `V06-charter-no-competitor-patterns`
- `V12-origin-type-valid`
- `V20-pr-lineage-declared`

No validator debt was repaired and no whole-framework PASS is claimed.

## Protected state and audit preservation

- Official `.19`: `PROMOTED_VERIFIED`, SHA-256
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Development `.74`: `SEALED_UNPROMOTED`, SHA-256
  `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`.
- `promotion.allowed=false`.
- CPT01-R2 remains `HOST_CAPABILITY_BLOCKED` with preserved host-protection
  limitation.
- Prior REJECT report at
  `reports/supervisor/rp_supervisor_260824_165924_by_gpt-5-codex_p2p-aerg-independent-verification.md`
  remains unchanged and still records
  `P2P_AERG_REJECTED_EXPIRED_EVIDENCE_RETURNS_SUPPORTED`.
- Current REJECT report at
  `reports/supervisor/rp_supervisor_260824_184807_by_gpt-5-codex_aerg-independent-verification-after-repair.md`
  remains unchanged and still records the FW01 compatibility bypass.

## Handoff artifacts

- Plan/evidence/benchmark/status:
  `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/`
- Problem report:
  `reports/problem/pb_coder_260824_195641_by_gpt-5-codex_aerg-qi-fw01-fail-closed-repair.md`
- Notes log:
  `docs/notes_decisions_log/notes_decisions_log_20260824.md`

`NEW_TEST_FAILURES=0`, `NEW_RUNTIME_FINDINGS=0` within the repaired invariant,
and `NEW_VALIDATOR_FAILURE_CLASSES=0`. The implementation is ready for a
separate Supervisor review and stops here.
