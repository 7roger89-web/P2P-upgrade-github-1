# P2P C74 Successor Evaluator Lifecycle Evidence Ledger

## Metadata

- Date: `2026-08-22`
- Plan: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-plan.md`
- Evidence: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-evidence.md`
- Benchmark: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-benchmark.md`
- Actual status: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct.

It should contain:

- metadata and companion files;
- evidence rules or evidence template;
- evidence sections such as `E0`, `E1`, or sections by phase/task;
- user report or problem evidence;
- source inspection, codebase facts, and document facts;
- commands run and pass/fail result;
- impact or blast-radius evidence when code/graph behavior changes;
- implementation evidence: files changed and behavior changed;
- validation evidence: build, tests, e2e, screenshots, or traces;
- failures encountered and how they were handled;
- detect-changes before commit;
- commit hash and closure evidence.

Evidence can reference short metric traces, but long metric tables belong in the benchmark file.

### Evidence ID Naming

Use stable, phase-scoped evidence IDs so `plan.md`, `actual-status.md`, `benchmark.md`, and later agents can reference exact proof without ambiguity.

Format:

```text
E<phase>-<item>-<kind><n>
```

Rules:

- `E<phase>` matches the plan phase number: `E0` for `P0`, `E1` for `P1`, `E2` for `P2`, and so on.
- `<item>` matches the checklist item without the dash: `P0A`, `P1A`, `P2B`.
- `<kind>` is plan-local. Choose a short uppercase token that is meaningful for this plan.
- `<n>` is a 1-based sequence number within that phase item and kind.
- Keep the same `<kind>` meaning stable inside one plan.
- Do not reuse an evidence ID for different facts.
- Reference exact evidence IDs from `actual-status.md` and `benchmark.md`; avoid referencing only broad section IDs such as `E1`.
- Use ranges such as `E0-P0A-FD1..E0-P0A-FD17` only for compact inventory summaries; use exact IDs when a specific status decision depends on a specific fact.

Evidence sections must follow the plan phases:

- `E0` corresponds to `P0`.
- `E1` corresponds to `P1`.
- `E2` corresponds to `P2`.
- Use exact evidence IDs inside each section, not broad section IDs as proof.
- Each evidence section must name the plan phase or checklist item it supports.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-REQ1`: User-provided C73 successor request requires one promotion-blocking lifecycle fix, a fresh successor, AC-01..AC-10, and an exact terminal handoff; all approval/promotion/release/deployment/C43/AERG/multi-AI actions are forbidden.
- `E0-P0A-C73FAIL1`: Independent C73 report `P2P_73_PROMOTION_READINESS_REVIEW_FAIL` records four completion attempts (`baseline:1`, `baseline:2`, `p2p:1`, `p2p:2`) exiting `2`, zero trial records, eval gate failure, strict Doctor failure, and technical prepare blocked before approval.
- `E0-P0A-AUTH1`: Fresh target worktree is `codex/p2p-c74-successor-eval-lifecycle-01` at base `93201a382af779d6c1017455a62dc13561161bba`; root owner worktree is not used for edits.
- `E0-P0A-SEAL1`: Read-only hash checks preserve `.73` as `72bfbef935a41b68ebe3c7fc5464d99d2a47e849cb77e85507ceb90cdf19ef1a` and `.72` as `70613080d2ddbb92a52d2d79186e125439ec7f5ba8a6fa87bda9208d1b39d872`; official `.19` remains governed by the existing development-control baseline.
- `E0-P0A-SRC1`: `scripts/p2p_eval.py` uses `target_root/scripts/p2p_eval.py` for `completion-contract`, while `_runtime_root` resolves an installed consumer to `target_root/.p2p/system`; the source path is therefore wrong for an installed consumer.
- `E0-P0A-SRC2`: The installed `.p2p/system/scripts/p2p_eval.py` in the development checkout is UI/UX-only and does not support project-eval v2 `design`; it is not a valid development-root fallback. The packaged ZIP contains root `scripts/p2p_eval.py` and `runtime/scripts/p2p_uiux_eval_impl.py`, while canonical installers copy root `scripts/p2p_eval.py` into the consumer runtime scripts.
- `E0-P0A-CONTRACT1`: Bootstrap/adoption docs invoke `.p2p/system/scripts/p2p_eval.py` for installed project suite lifecycle and explicitly require normal setup rather than hand-written evidence. This supports Option B: installed runtime helper is the canonical consumer evaluator; unpacked package root helper is package validation only.
- `E0-P0A-WORKFLOW1`: `scripts/p2p_workflow.py` already filters the UI/UX-only development helper and accepts an installed helper only when it supports the project-eval contract; no competing evaluator authority is introduced.
- `E0-P0A-GRAPH1`: `anvien analyze --force` completed in the target worktree: 857 files scanned, 160 code files parsed, 0 parse failures, 499 indexed documents, 36,567 graph nodes, 42,272 relationships, stale=false.
- `E0-P0A-FD1`: Anvien file-detail for `scripts/p2p_eval.py` reports 175 symbols, inboundRefCount 4, localRelationshipCount 51, linkedFlowCount 24, unresolved 832, risk high, changedSinceAnalyze false; the inbound related file is `tests/test_p2p_project_eval.py`.
- `E0-P0A-IMPACT1`: Anvien impact for `_case_command` reports risk `CRITICAL`, 1 direct affected symbol, 1 module, and 6 affected processes. This is a scope warning; the edit remains limited to the path branch and its direct behavior tests.
- `E0-P0A-FD2`: Anvien file-detail for `tests/test_p2p_workflow.py` reports 25 symbols, 12 outbound references, 8 local relationships, risk high, changedSinceAnalyze false; it remains inspect/preserve-only for this task.
- `E0-P0A-STATUS1`: Target initially has newline-only Git status noise across tracked text files due the Windows autocrlf checkout; `git diff --ignore-space-at-eol` is empty for sampled files. These paths are excluded from all staging and are not treated as implementation changes.

P0 decision: `E0-P0A-CONTRACT1` resolves the A/B choice to Option B. Implementation may proceed only in the new successor worktree, with installed helper ownership explicit and no source fallback for an installed root.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-ROUTE1`: `_project_eval_path` now selects the packaged root helper only for an unpacked package/development root and selects `runtime_root/scripts/p2p_eval.py` for an installed consumer. `_case_command` uses that single resolver for `completion-contract`.
- `E1-P1A-SYNTAX1`: direct `compile()` syntax check returned `P2P_EVAL_SYNTAX_PASS`, exit `0`.
- `E1-P1A-ANALYZE1`: post-edit `anvien analyze --force` completed with 861 files scanned, 160 parsed code files, 0 failures, 36,674 nodes, and 42,392 relationships; stale=false.
- `E1-P1A-IMPACT1`: post-edit Anvien file-detail reports 177 symbols, 7 inbound references, 52 local relationships, and 24 linked flows; `_case_command` remains CRITICAL with 4 direct affected symbols, 2 modules, and 6 processes. The new branch is intentionally within this warning.
- `E1-P1A-DETECT1`: post-edit `anvien detect-changes --repo <C74-worktree> --scope all` reports exactly two intended changed source/test files in the affected file layer (`scripts/p2p_eval.py`, `tests/test_p2p_project_eval.py`); the full output also discloses pre-existing tracked EOL noise and analyzer gaps.
- `E1-P1A-STATUS1`: actual-status R1 records `wrong -> correct` for the completion resolver; package/source mode and UIUX helper remain preserve/validation-only.
- `E1-P1B-TEST1`: three direct target-layout tests pass: installed runtime wins, unpacked package uses its source helper, and installed absence does not fall back to a root source helper.
- `E1-P1B-TEST2`: `python -m unittest discover -s tests -p 'test_p2p_project_eval.py' -v` returned `OK`, 5 tests run, 0 failures/errors after a disposable source-local suite was created through the existing evaluator lifecycle.
- `E1-P1B-TEST3`: the source-local disposable suite executed 5 cases x 2 modes x 2 trials = 20 case-oracle executions; all `run` and `record` commands returned exit `0`, suite validation returned exit `0`, and the execution receipts reported `unexpected_writes=0`. This is only source-local test validation, not clean installed-consumer proof; P2 must repeat it from the sealed successor package.
- `E1-P1B-FULL1`: repository-wide target run completed with 703 tests, 15 failures, 25 errors, and 3 skips. A clean parent worktree at `93201a3` completed 700 tests with 14 failures, 27 errors, and 3 skips. The failing/erroring names are the existing FW01/C27-C28/governance/registry/task-state/workflow baseline family; the changed project-eval file is green in C74 and had the expected empty-suite error in the unprepared parent. Repository-wide suite is therefore disclosed as pre-existing non-green evidence, not claimed as a full regression pass.
- `E1-P1B-DETECT1`: commit-boundary `anvien detect-changes --repo <C74-worktree> --scope all` completed before the P1-B test commit. It reports the intended test/docs slice; the only implementation-layer file is `tests/test_p2p_project_eval.py` with the known high test-file risk and analyzer resolution gaps. No uncommitted production-source change remains because `scripts/p2p_eval.py` is already in commit `2fc5d43`.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

The source successor, clean consumer, and candidate are now sealed for handoff. No approval, promotion, finalize, release, deployment, merge, tag, or external action was performed.

- `E2-P2A-PACKAGE1`: candidate `reports/candidates/P2P-8.4.7-C-Codex-Edition-v74.zip` was minted once at 2,899,886 bytes with SHA-256 `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`. Exact package extraction and `package_release.py verify` returned PASS: package `.74`, source commit `4eafc3ccb6de52f2b5f9b9b75b754c9d9a2a9b53`, source tree `064d52121cd6220602fbd455614bccc0c3b3dd2b`, 493 total members, 493 accounted, no unsafe/duplicate/unaccounted members, and official `.19` binding preserved. The build wrapper emitted a Windows Unicode encoding error after writing the artifact; the exact artifact was not rebuilt or overwritten, and independent extraction/verification passed.
- `E2-P2A-INSTALL1`: exact `.74` artifact and exact hash were installed with the normal `install.ps1 -Scope Project` lifecycle into disposable consumer `D:/AI/P2P_dev/P2P-upgrade-github/.tmp/p2p-c74-successor-eval-lifecycle-20260822/.tmp/p2p-c74-final-fresh-consumer-20260822`. Install returned PASS/FRESH_INSTALL, no root `scripts/p2p_eval.py` exists in the consumer, `.p2p/system/scripts/p2p_eval.py` exists, project pin matches the artifact, and strict installed Doctor returned `ok=true`.
- `E2-P2A-EVAL1`: normal installed bootstrap created the project-owned `.p2p/evals/suite.json` with 5 cases. The installed helper executed baseline trials 1–2 and P2P trials 1–2, each with 5 attempted/passed, 0 failed, `record_status=RECORDED`, and `unexpected_writes=0`: 20 case executions across 10 required trial slots. Suite validation and summary both passed; baseline mean and P2P mean were `1.0`, delta `0.0`, and every case had 2 trials per variant with spread `0.0`.
- `E2-P2A-GATE1`: installed `p2p_eval gate` returned PASS with zero case regressions and policy thresholds intact. `p2p_gate prepare` returned `TECHNICAL_GATES_PASS_USER_APPROVAL_REQUIRED`; subject SHA was `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`, rollback `.72` SHA was `70613080d2ddbb92a52d2d79186e125439ec7f5ba8a6fa87bda9208d1b39d872`, technical report SHA was `1e1cd20068d69072f0ffc0091328c67a402f148979dbd16a76942b63d53871f5`, and no approval decision or finalize/approve action was performed.
- `E2-P2B-REG1`: relevant regression gates passed: runtime capability suite `335/335` with 6 declared skips; C35 `57/57`; bounded `94/94`; FW05/A–Z `29/29` with 1 declared skip; focused evaluator `5/5`; security unit `2/2`; and MAP-before-work plus MAP-freshness suites PASS. The repository-wide suite remains a disclosed non-green baseline: C74 `703 tests, 15 failures, 25 errors, 3 skips` versus clean parent `700 tests, 14 failures, 27 errors, 3 skips`, with the same legacy failure families. The focused workflow file retains one known pre-existing `transient_helper_paths` failure, and two historical supervisor scripts are not Windows-portable; neither was used as a successor PASS claim.
- `E2-P2B-SEC1`: package and extracted-runtime secret scans returned PASS with zero findings; security unit returned `2/2`. Mutation audit restored only disposable capability-test state and confirmed no root owner, C72, C73, official `.19`, or unrelated project mutation. Sealed `.72` and `.73` byte hashes remained exact before and after.
- `E2-P2B-DETECT1`: after `anvien analyze --force`, final `anvien detect-changes --repo <C74-worktree> --scope all` returned exit `0`; graph was fresh with 864 files scanned, 160 parsed code files, 0 parse failures, 36,692 nodes, and 42,410 relationships. Detect reported 6 changed files, 4 affected files, and low file-layer risk; no source implementation change was made after commit `4eafc3c`. Post-seal changes are limited to governance-derived lock state, candidate identity, plan ledgers, reports, and the candidate ZIP.
- `E2-P2B-SEAL1`: `reports/reconciliation/p2p-c74-successor-eval-lifecycle-01-candidate-identity.json` binds the candidate to the frozen source and exact artifact, sets `MINTED_UNPROMOTED_CANDIDATE`, records `promotion_performed=false`, and leaves approval as a pending technical handoff only. Final coder and supervisor-style evidence reports are prepared; the latter explicitly does not claim independent review by the same executor.

## Closure Evidence

Final closure is recorded in the coder/supervisor reports and the final commit. The local supervisor-style gate is `PASS_FOR_HANDOFF_NOT_PROMOTION`; an external independent review remains the next authority boundary. Approval/promotion/finalize remain unperformed. Terminal handoff token: `P2P_EVAL_LIFECYCLE_SUCCESSOR_HANDOFF_SEALED_READY_FOR_INDEPENDENT_REVIEW`.
