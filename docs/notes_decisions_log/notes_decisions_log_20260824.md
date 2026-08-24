# Notes and Decisions Log — 2026-08-24

## AERG QI/FW01 Fail-Closed Repair

- Decision: repair only the two confirmed production seams: QI required-status
  classification and the FW01 compatibility/checkpoint safety boundary.
- RED: `0ba5f39` reproduced 13 failing assertions across the required-status
  fall-through and the stale/missing-AERG compatibility bypass.
- Production: `ce641d6` repaired QI classification; `cbf7af9` added the narrow
  actual-AERG safety clamp and preserved fresh compatibility behavior.
- Regression: `0910b18` added direct current-QI actual-AERG mapping coverage.
- Validation: boundary `8/8`; AERG `17/17`; freshness `5/5`; independent A-Z
  `26/26` plus freshness `2/2`; QI `44 pass/1 skip`; FW01 `6/6`; C43/RF01
  `18/18`; full capability `360 pass/6 skip`; compile PASS.
- Framework debt: validator remains `52/59` with exactly seven inherited
  classes (`V01`, `V03`, `V05`, `V09`, `V06`, `V12`, `V20`); no debt repair or
  whole-framework PASS claim.
- Protection: `.19 PROMOTED_VERIFIED`, `.74 SEALED_UNPROMOTED`,
  `promotion.allowed=false`, CPT01-R2 host limitation preserved, prior REJECT
  reports unchanged.
- Handoff: coder report
  `reports/coder/rp_coder_260824_195641_by_gpt-5-codex_aerg-qi-fw01-fail-closed-repair.md`
  and problem report
  `reports/problem/pb_coder_260824_195641_by_gpt-5-codex_aerg-qi-fw01-fail-closed-repair.md`.
- Stop: `P2P_AERG_QI_FW01_FAIL_CLOSED_REPAIR_READY_FOR_SUPERVISOR_REVIEW`.
  Supervisor review, independent verification, Owner approval, promotion,
  release, deployment, and host mutation remain unperformed.

## AERG/FW01/QI Fresh-Checkpoint Status Contract Repair

- Contract finding: QI checkpoint eligibility canonically requires execution
  status SUCCESS; TASK_DONE_CONTINUE is an AutoPilot/FW01 loop-control result
  emitted after verified completion, not a second QI execution vocabulary.
- RED: 36f6877 reproduced the real production FW01 -> AERG -> QI ->
  durable-checkpoint mismatch: QUALITY_VERIFIED with checkpoint_allowed=False
  and durable QUALITY_REVIEW/BLOCKED.
- Production: 66657b3 adds only the narrow FW01 projection of explicit
  successful completion states to QI SUCCESS. Failed, blocked, not-run,
  unknown, and arbitrary statuses remain non-success. QI, AERG engine, and
  AERG model are unchanged in this continuation.
- Regression: c4c5fc9 falsifies unsafe mappings; a716a50 corrects only the
  test fixtures that had relied on the old mismatch. Fresh runtime reaches
  VERIFIED/CHECKPOINTED; stale, contradicted, subject-mismatch, insufficient,
  malformed, required-status, and compatibility safety cases remain blocked.
- Validation: fresh checkpoint 1/1; mapping 1/1; boundary 10/10; AERG 17/17;
  freshness 5/5; QI 44 pass/1 skip; FW01 6/6; A-Z 26/26 plus two primary
  freshness extensions; full capability 362 pass/6 skip; C43/RF01 18/18;
  compile PASS; validator 52/59 with exactly seven inherited classes.
- Protection: .19 PROMOTED_VERIFIED, .74 SEALED_UNPROMOTED,
  promotion.allowed=false, CPT01-R2 host limitation, RF01, C43, release and
  deployment state, Owner authority, owner-dirty files, and prior REJECT
  reports are preserved.
- Handoff: coder report
  reports/coder/rp_coder_260824_223656_by_gpt-5-codex_aerg-fw01-qi-status-contract-repair.md
  and problem report
  reports/problem/pb_coder_260824_223656_by_gpt-5-codex_aerg-fw01-qi-status-contract-repair.md.
- Stop: P2P_AERG_FW01_QI_STATUS_CONTRACT_REPAIR_READY_FOR_SUPERVISOR_REVIEW.
  Supervisor review, independent verification, Owner approval, promotion,
  release, deployment, and host mutation remain unperformed.
