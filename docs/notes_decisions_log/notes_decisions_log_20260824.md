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

## AERG/FW01 Compatibility Verdict Shape Repair — 2026-08-25

- Root cause: the legacy compatibility QI seam copied malformed verdicts into
  a mapping and used truthiness for `checkpoint_allowed`; an otherwise safe
  AERG run could therefore persist malformed `QUALITY_VERIFIED` output as
  `VERIFIED / CHECKPOINTED`.
- Test-first: `1b22745527fb31e6299a65cc631f14ab4c754502` is the separate RED
  test-only checkpoint. The exact real-loop malformed case failed before the
  fix with `TASK_DONE_CONTINUE != STOP_BLOCKED`.
- Production: `6c1746d6716bcfe9042ae82b37bf319eda50ea1a` adds only FW01
  verdict-shape validation and strict canonical checkpoint authorization.
  Valid authorization requires recognized QI status, tuple failure shape,
  literal boolean `True`, canonical `QUALITY_VERIFIED`, safe AERG, and the
  existing execution requirements. QI/AERG source was not modified.
- Runtime: 18 malformed subcases all persist `QUALITY_REVIEW / BLOCKED`;
  fresh valid compatibility still persists `VERIFIED / CHECKPOINTED`; stale
  actual AERG remains blocked. The focused module is 15/15, full capability
  under `python -X utf8` is 367 pass / 6 skip, C43/RF01 is 18/18, and compile
  passes.
- Validator: remains 52/59 with exactly inherited V01, V03, V05, V09, V06,
  V12, V20; no validator repair or whole-framework PASS claim.
- Protection: `.19 PROMOTED_VERIFIED`, `.74 SEALED_UNPROMOTED`,
  `promotion.allowed=false`, CPT01-R2 host limitation, RF01, C43,
  release/deployment state, Owner authority, owner-dirty files, and prior
  REJECT report blobs were preserved.
- Handoff: coder report
  `reports/coder/rp_coder_260825_000534_by_gpt-5-codex_aerg-fw01-compatibility-verdict-shape-repair.md`.
- Stop: `P2P_AERG_COMPAT_VERDICT_SHAPE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`.
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
