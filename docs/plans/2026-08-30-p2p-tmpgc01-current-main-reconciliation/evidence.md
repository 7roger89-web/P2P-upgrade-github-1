# P2P-TMPGC01 Current Main Reconciliation Evidence Ledger

## Metadata

- Date: `2026-08-30`
- Plan: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/plan.md`
- Evidence: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/evidence.md`
- Benchmark: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/benchmark.md`
- Actual status: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/actual-status.md`

## Evidence Rules

Evidence is fresh for this isolated worktree. Historical reports and the prior
candidate are evidence pointers only. Exact Git objects, source inspection,
focused behavior tests, compile/static checks, and final diff/path checks are
required for acceptance. No test or report authorizes push, promotion, deletion,
or scheduling activation.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GIT1`: Fresh clone from the canonical URL was fetched with an explicit
  `refs/heads/main -> refs/remotes/origin/main` refspec.
- `E0-P0A-GIT2`: Fresh `origin/main` is
  `d661654746f090136f37370f76578ee345b74994`, tree
  `92895a93a560221bdcd4664992ab16a4e8ec8cb4`; expected SHA matched.
- `E0-P0A-GIT3`: Supplied previous candidate
  `dab3e858dcace307f4bd77fdb43145df70e75da2` resolves to supplied tree
  `d9ab934f16a9517dccee3e847362795ec66f719b`.
- `E0-P0A-SRC1`: Fresh main has the existing FW06 and C27 sibling files but no
  `scripts/p2p_tmp_gc.py`, `tests/test_p2p_tmp_gc.py`, or
  `governance/p2p-tmp-gc-policy.json`.
- `E0-P0A-SRC2`: Previous candidate TMPGC implementation is limited to the
  FW06 source, CLI, C27 sibling changes, policy, and focused test family; its
  broader merge contains unrelated historical paths that are excluded.
- `E0-P0A-TOOL1`: Full Anvien refresh crashed in its native graph loader with
  Windows access violation `0xc0000005`; narrowed refresh then reported
  `lbug_database_init failed with state 1`. No registry/index repair was run.
- `E0-P0A-SAFE1`: Work is in repo-local `.tmp/P2P-TMPGC01-current-main-worktree-20260830`;
  the designated dirty owner checkout was not edited.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SRC1`: The selected production/policy delta applies cleanly to fresh
  main. The resulting four production blobs match the supplied previous
  candidate exactly: FW06 `f424887fdefeb7ddb654ca7d240f8353c21a72d9`, C27
  `ca4f805c1cebfd7618541bbe6a59f9c57a02538b`, policy
  `4caf4610698c297afb0f7b789de7dce511284d3b`, and CLI
  `aa3d8aa463934b6006a9615e2e54120477810e69`.
- `E1-P1A-SRC2`: Direct source inspection confirms the reviewed FW06 writer
  guard, final revalidation, lifecycle identity audit check, and C27
  archive-first delegation remain intact. No redesign or new authority was
  introduced.
- `E1-P1A-DIFF1`: The source slice was committed as
  `6b13123f92cd8f9090d138afc8a56f8b271f7273`, whose parent is the exact fresh
  main SHA. No push or canonical mutation occurred.
- `E1-P1A-DIFF2`: Before the test slice, the changed paths were limited to the
  four TMPGC production/policy paths and the four bounded reconciliation plan
  artifacts.
- `E1-P1A-DIFF3`: `git diff --check` and changed-file `py_compile` passed for
  the source slice.
- `E1-P1B-TEST1`: The exact reviewed `tests/test_p2p_tmp_gc.py` was added;
  its fixtures are repo-local `.tmp` roots and do not target owner or
  historical workspaces. Its two counterfactual source commits were fetched
  as test-only Git objects into the isolated clone; no source tree or ref was
  changed by that preparation.
- `E1-P1B-TEST2`: Full focused suite passed: `67 passed in 38.65s`.
- `E1-P1B-TEST3`: Changed Python files, including the focused test, passed
  `python -X utf8 -m py_compile`.
- `E1-P1B-TEST4`: AST parsing and policy/static invariant assertions passed:
  `AST_JSON_STATIC_PASS` and `STATIC_VALIDATION_PASS`.
- `E1-P1B-TEST5`: The exact reviewed protection family and lifecycle markers
  are present; policy schedule is `OWNER_GATED`, and CLI schedule output is
  preview-only.
- `E1-P1B-TEST6`: Anvien `detect-changes` was attempted after implementation
  and returned `repository "." is not registered`; no index repair was run.
  Direct Git/source/AST fallback remains the evidence boundary.
- `E1-P1B-TEST7`: No production deletion, schedule activation, auto-GC,
  push, or promotion was run. Test fixture deletion, where exercised by the
  focused suite, stayed inside repo-local temporary fixtures.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

`E2-P2A-SUPERVISOR1`: Supervisor PASS for exact functional subject
`2ec61632c1bfe78a685cb575eaf8495c658fa46b`, tree
`051faf6438f24dd206d5401b78965215e5fa9dfb`, with report at
`reports/supervisor/rp_supervisor_260830_044500_by_gpt-5-codex_p2p-tmpgc01-current-main-reconciliation.md`.

`E2-P2B-CLOSURE1`: Closure is limited to these ledgers and the Supervisor
report; final rebind must prove the five functional TMPGC blobs and all fresh-
main paths outside the allowlist remain unchanged.

## Closure Evidence

Final SHA/tree, exact path allowlist, focused outputs, detect-changes
limitation, Supervisor PASS, and the no-push/no-promotion/no-delete boundary
are recorded by the final handoff checks. The functional subject remains the
exact reviewed SHA/tree above; any later commit is evidence-only.
