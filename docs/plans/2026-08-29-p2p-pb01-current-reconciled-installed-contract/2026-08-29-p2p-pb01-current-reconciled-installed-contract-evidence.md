# P2P-PB01 Current Canonical Reconciliation and Installed Contract Fix Evidence Ledger

## Metadata

- Date: `2026-08-29`
- Plan: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-actual-status.md`

## Evidence Rules

- Fresh official remote/current-main evidence outranks historical candidate reports.
- The old PB01 subject is source material only.
- Current 02A paths are preserve-only.
- User explicitly capped verification at focused PB01/contract/package/compile/diff
  checks; no Anvien or broad regression evidence will be substituted.
- No evidence in this ledger authorizes promotion or live action.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-AUTH1`: Fresh `git ls-remote` against
  `https://github.com/7roger89-web/P2P-upgrade-github-1.git` returned
  `6cc7555246905fce7b2fec1d4e48f5e46bfaf57e` with exit `0` before candidate
  mutation.
- `E0-P0A-CLONE1`: Fresh isolated clone
  `.../.tmp/p2p-pb01-current-reconciled-20260829-01` is clean on `main` at
  `6cc7555246905fce7b2fec1d4e48f5e46bfaf57e`, tree
  `b308b9cf075aaeaef581a022202dcc428689b2ad`, with official HTTPS origin.
- `E0-P0A-OLD1`: Historical PB01 subject is
  `fa589490de7ad0f5eee63d1463bb06dded0fc799`, tree
  `e9bf66495c14a79bb03f9570e0b357a5a85b700c`, parent/base
  `9f5b91c9ab5178188aff6cc5520751b53b91dba7`.
- `E0-P0A-OVERLAP1`: Old-base-to-old-PB01 contains 9 paths; old-base-to-current
  main contains 47 paths; exact path intersection is empty (`0`).
- `E0-P0A-02A1`: Current-main-only paths include the 02A capability registry,
  vendor provenance/skills, external sources, 02A tests, and 02A reports; all
  are preserve-only and are not overwritten.
- `E0-P0A-SCOPE1`: No Anvien, graph/impact, broad tests, or benchmark
  regeneration was run, per the current user verification ceiling.

P0 decision: complete. The candidate may carry only the disjoint PB01 delta.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-CARRY1`: completed. The carry-forward changed only
  `scripts/p2p_bootstrap.py`, `install.ps1`, `install.sh`,
  `scripts/package_release.py`, and `tests/test_p2p_portable_bootstrap.py`;
  historical PB01 plan files were not copied.
- `E1-P1A-02A1`: completed. The old-base/current-main path intersection is `0`,
  and no current-main-only 02A path is changed by the candidate delta.
- `E1-P1B-FIX1`: completed. Added exactly one entry,
  `scripts/p2p_bootstrap.py`, to the existing `INSTALLED_REQUIRED_FILES`
  tuple. No validator or orchestration redesign was made.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`

- `E2-P2A-INSTALL1`: completed by
  `python -X utf8 -m unittest tests.test_p2p_portable_bootstrap -v`:
  `Ran 16 tests in 61.627s`, `OK`. The new regression accepts a valid installed
  runtime with the launcher and rejects a missing launcher with
  `INSTALLED_REQUIRED_FILE_MISSING`, preserving the project tree after the
  rejection.
- `E2-P2A-VERIFY1`: completed. The source/installed tuples and all three
  package/install copy surfaces contain `scripts/p2p_bootstrap.py`; compileall
  exited `0`; `git diff --check` exited `0` with only line-ending warnings.
- `E2-P2A-ID1`: pending the implementation checkpoint commit and exact tree.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-SUP1`: pending one fresh independent Supervisor review.
- `E3-P3B-CLOSE1`: pending unpromoted candidate closure.

## Closure Evidence

Focused checks are complete. Closure remains pending the implementation
checkpoint identity and one independent Supervisor review. No evidence here
authorizes promotion, release, deployment, or live activation.
