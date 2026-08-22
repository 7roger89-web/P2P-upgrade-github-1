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
- `E1-P1B-TEST2`: the focused test command for the three new route tests returned `OK`, 3 tests run, 0 failures/errors. The existing recorded-suite test is not yet rerun because the fresh C74 worktree's ignored `.p2p/evals/suite.json` has no trial records; that environment fixture is deferred to lifecycle evidence and is not used as successor proof.
- `E1-P1B-DETECT1`: pending until the test slice is committed after its full focused validation.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

Pending until the source successor is implemented and a fresh candidate is built. Expected evidence IDs:

- `E2-P2A-PACKAGE1`: fresh candidate build, package verify, inventory, source/tree binding, and exact ZIP hash.
- `E2-P2A-INSTALL1`: normal packaged install/adoption into a fresh consumer, canonical installed helper path, pin, and strict Doctor.
- `E2-P2A-EVAL1`: suite setup, ten trial slots, record files, summary, and zero unexpected writes.
- `E2-P2A-GATE1`: `p2p_eval gate` and technical `p2p_gate prepare` with exact subject/rollback hashes and no approval request.
- `E2-P2B-REG1`: full capability/unit, provider-neutral, bounded/FW05, negative, and MAP/regression evidence.
- `E2-P2B-SEC1`: candidate/extraction security scan and mutation audit.
- `E2-P2B-DETECT1`: final Anvien detect-changes and change-scope evidence.
- `E2-P2B-SEAL1`: successor candidate identity, unpromoted state, seal/hash comparison for `.72/.73`, and final handoff report.

## Closure Evidence

Pending. Final closure must include coder report, independent supervisor report, final validation commands/results, exact commit hashes, final clean intended-path status, and the exact terminal handoff token. Approval/promotion/finalize remain unperformed.
