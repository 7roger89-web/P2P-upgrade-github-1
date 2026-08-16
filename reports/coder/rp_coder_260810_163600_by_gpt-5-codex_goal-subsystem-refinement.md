# Coder Report: P2P Goal subsystem refinement

## Scope

Focused refinement from the attached Goal request: eligibility before Goal creation, oracle-backed Goal Linter, mandatory/optional/out-of-scope policy, work type, exploration/iteration limits, mutation classification, and resumable capsule/ledger state.

## Invariant Family Map

| Family | Authority / SSOT | Sibling surfaces checked | Forbidden fallback | Verification |
|---|---|---|---|---|
| Goal eligibility and bounded objective | `scripts/p2p_workflow.py`, `.agents/skills/p2p/SKILL.md` | inspect/classify/goal/plan/run/update entrypoints | always creating a Goal or combining independent objectives | 10 Goal cases, CLI smoke |
| Oracle-backed completion | Goal Contract plus `lint_goal_contract` | criteria result, reports, status, capsule, existing workflow tests | subjective DONE text without a proof method | invalid-oracle fail-closed test and 17-test suite |
| Work/iteration discipline | Goal Contract, exploration policy, append-only ledger | approach command, status, capsule, PASS terminal path | speculative third lane, retry after PASS, wall-clock-only failure | approach persistence/PASS-stop tests |
| Scope mutation | `classify_goal_update` and active contract | update CLI, run contract history, ledger/status/capsule | silent expansion of active Goal | mutation/separate-objective tests |
| Existing governance continuity | existing FACT/Live/Approval/Drift/Eval/Quorum/doctor | package/fresh installer, doctor, drift, source baseline | duplicate gate or modified passing governance | package/fresh doctor and drift PASS |

## Source-level implementation

- `scripts/p2p_workflow.py`: added eligibility classifier, Goal Linter/oracles, context/protected decision/evidence reuse fields, item/work/lane/mutation classifiers, approach ledger recorder, capsule/status wiring, `classify`/`update`/`approach` commands, and ten-case acceptance output.
- `.agents/skills/p2p/SKILL.md`: normal entry now classifies before Goal creation and describes linter/work-type/lane/mutation discipline.
- `.agents/skills/p2p/references/state-schema.md`: documents new Goal/status fields.
- `.agents/skills/p2p-capsule/SKILL.md`: documents compact Goal capsule fields.
- `.agents/skills/p2p-scope/SKILL.md`: documents eligibility, oracle, item-class, lane, and mutation rules.
- `manifest/package.json`: exposes the new helper command surfaces.
- `tests/test_p2p_goal_subsystem.py`: 13 direct behavior tests for the new Goal invariant.

Legacy fallback status: no alternate Goal/governance subsystem was added; existing helper, eval, approval, drift, quorum, and ledger paths remain the authority.

## Verification

E2E Verification:

  [PASS] Compiled: `python -m py_compile scripts/p2p_workflow.py scripts/p2p_eval.py scripts/doctor.py`.
  [PASS] Runtime: fresh installed helper `classify` and `run --acceptance` in `.tmp/fresh-goal-refinement-project-1`.
  [PASS] Happy path: clear long-running request -> `GOAL`, oracle-backed contract, terminal PASS.
  [PASS] Edge case: vague/open-ended -> `PLAN FIRST`; malformed oracle -> Goal Linter BLOCKED; post-PASS approach -> PASS_STOPPED.

Behavior tests:

- `tests/test_p2p_goal_subsystem.py:20-128`: 13 tests PASS — eligibility (`20,25,32`), scope (`37`), lane/failure (`40,48`), work type (`65`), linter (`68`), reuse/stop (`78`), blocker (`89`), mutation/separate (`93`), capsule persistence (`99`), and ten-case summary (`128`).
- `tests/test_p2p_workflow.py:22,35,41,64`: 4 existing workflow regression tests PASS.
- `tests/test_p2p_workflow.py`: 4 regression tests PASS.
- Combined discovery: 17 tests PASS.
- `python scripts/p2p_workflow.py acceptance --package .`: PASS; all ten Goal cases and prior new/existing workflow fixtures PASS.
- `python scripts/doctor.py --package .`: PASS.
- `python scripts/p2p_governance.py drift --root . --governance governance`: PASS.
- Fresh installer/doctor: PASS; expected release-readiness warning remains because fixture has no real project eval trials.

Docker/Playwright: N/A; this is a Python CLI/state-only subsystem with no public UI, database, or container runtime.

## Scope and closure notes

- Anvien list/query/context/detect-changes was attempted; the package path is not registered, so local source/runtime evidence is the fallback.
- The package has no `.git` metadata; no checkpoint commit exists and no Git repository was initialized.
- Residual unverified surfaces: none within the requested package/fixture invariant. Real project-quality eval and live eight-thread runtime remain explicitly out of scope.
