# P2P-GOVREC02 Governance Source Anchor Contract Correction Evidence Ledger

## Metadata

- Date: `2026-08-26`
- Plan: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-plan.md`
- Evidence: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-evidence.md`
- Benchmark: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-benchmark.md`
- Actual status: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-actual-status.md`

## Evidence Rules

This ledger records current source, graph, implementation, validation, and closure evidence for GOVREC02. Historical GOVREC01 reports remain historical evidence and are not rewritten as part of this ledger.

Evidence IDs use `E<phase>-<item>-<kind><n>`. Commands are run from the valid linked worktree `.tmp/p2p-govrec01-current-authority`; no root `.git` repair, remote write, promotion, or release action is allowed.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-CHK1`: Valid target worktree is `codex/p2p-govrec01-current-authority` at evidence-only closure HEAD `ad5ea25ed12caecb04dfd9230f3b53ad45adb843`; exact GOVREC01 subject object `6c860eea9332b3641d2b7806daf37043b4bf123d` and tree `8d0e0201593f6a849a57e8811fae9ebc2646daa1` exist. Subject paths are clean; 1,127 unrelated owner/line-ending dirty entries remain preserved.
- `E0-P0A-CHK2`: Fresh read-only Git observation reports local and remote `origin/main=2a71410afd1b29651016ef57a5d2da38938c3f68`; no canonical drift was introduced by this task.
- `E0-P0A-AUTH1`: Active authority currently contains `authority.current_promoted_source` with the 2a71410/3e6ab12 snapshot. GOVREC01P established that the field has no explicit anchor/latest-head contract and blocks promotion.
- `E0-P0A-AUTH2`: Owner decision in the current request selects anchor semantics: the active field must represent the exact promoted implementation source against which reconciliation was evaluated, not forever-current Git HEAD.
- `E0-P0A-AUTH3`: Historical `.19` official artifact authority, `.74` unpromoted successor, existing approval records, and source-binding machinery are distinct surfaces and remain preserve-only.
- `E0-P0A-SRC1`: `_validate_authority()` currently validates only canonical source/reference/trust-boundary invariants; `validate_control()` does not inspect the current source field. Existing runtime drift validates file manifests, not Git lineage.
- `E0-P0A-SRC2`: `tests/test_p2p_govrec01_reconciliation.py` asserts the old snapshot but has no post-promotion or diverged-lineage behavior test. The GOVREC01 plan's stale-authority acceptance claim is therefore not current proof.
- `E0-P0A-GRAPH1`: `anvien analyze --force` refreshed the target graph: 946 files scanned, 169 parsed code files, 0 parse failures, 39,380 nodes, 45,526 relationships; graph is current at `ad5ea25...`.
- `E0-P0A-GRAPH2`: `anvien file-detail scripts/p2p_development_control.py` reports 151 symbols, 1 inbound reference, 120 local relationships, 17 linked flows, 703 unresolved analyzer entries, `risk=high`, `changedSinceAnalyze=false`.
- `E0-P0A-GRAPH3`: `anvien impact` on `validate_control#4` reports `risk=CRITICAL`, 9 impacted symbols, 8 direct relationships, 1 affected module, and 8 affected processes. This is a scope warning requiring careful review, not an edit prohibition.
- `E0-P0A-GRAPH4`: `anvien file-detail tests/test_p2p_govrec01_reconciliation.py` reports 34 symbols, 7 outbound relationships, 16 local relationships, `risk=high`, and a current graph.
- `E0-P0A-GRAPH5`: `anvien file-detail governance/development-control.json` reports a parsed non-code source with 2 inbound references and `risk=low`; direct JSON/validator evidence remains authoritative for the contract.
- `E0-P0A-SCOPE1`: No provider, Manus, Council, SFI01, Manus R2, vendor source, remote write, push, merge, promotion, release, deployment, or project mutation was performed.

P0 decision: complete. P1 status assumptions are updated: the authority projection and validator are `partial/wrong` until the explicit anchor and dynamic lineage checks are implemented; historical receipts and official artifacts remain `preserve-only`.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-CONTRACT1`: `governance/development-control.json` now contains one `authority.promoted_source_anchor` object with `semantic_type=PROMOTED_IMPLEMENTATION_SOURCE_ANCHOR`, `source_kind=GIT_COMMIT_TREE`, explicit purpose, observed ref, anchor commit/tree, verification date, and descendant lineage policy. The active legacy key is absent.
- `E1-P1A-CONTRACT2`: Static `p2p_development_control` validation now rejects duplicate/legacy authority keys, historical-artifact-shaped anchors, malformed semantic/source-kind/purpose/date/SHA fields, and self-reference lineage policies with explicit `ControlError` reason codes. `py -3 -X utf8 -m py_compile scripts/p2p_development_control.py` passed and `scripts/p2p_development_control.py validate --json` returned `PASS` with `NOT_OBSERVED` dynamic fields.
- `E1-P1B-GIT1`: Dynamic validator now resolves the recorded anchor commit and tree, observes `HEAD` and `refs/remotes/origin/main`, and returns separate `HEAD_EQUALS_ANCHOR`/`HEAD_DESCENDS_FROM_ANCHOR` and `ORIGIN_MAIN_EQUALS_ANCHOR`/`ORIGIN_MAIN_DESCENDS_FROM_ANCHOR` relations. Divergence raises `AUTHORITY_LINEAGE_DIVERGED`; missing commit/tree and Git-object failures have stable reason codes.
- `E1-P1B-GIT2`: Real linked-worktree CLI validation passes with `HEAD_DESCENDS_FROM_ANCHOR` and `ORIGIN_MAIN_EQUALS_ANCHOR`; Git-less static `validate_control` remains `NOT_OBSERVED`, preserving package-stage compatibility. `validate --json`, `status --json`, and human `status` all passed without remote mutation.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-TEST1`: `tests.test_p2p_govrec02_source_anchor` passed `11/11`; active key/semantic fields, duplicate/legacy, artifact-shaped, self-reference, missing-anchor, wrong-tree, and status-projection behavior are covered.
- `E2-P2A-TEST2`: The focused suite passed BEFORE equality, current descendant, hypothetical post-promotion descendant (`6c860ee...`), and diverged-head simulations using existing Git objects and injected observations; no refs or remote state changed.
- `E2-P2B-DOC1`: Pending implementation: active evidence states that committed anchor data and external final promotion subject identity are separate.
- `E2-P2B-DOC2`: Pending implementation: active consumer search finds no duplicate authority truth; historical GOVREC01 references remain provenance-preserved.

## Closure Evidence

P1-A/P1-B/P2-A closure:

- `py -3 -X utf8 -m unittest tests.test_p2p_govrec01_reconciliation`: `9/9 PASS`.
- `py -3 -X utf8 -m unittest tests.test_p2p_govrec02_source_anchor`: `11/11 PASS`.
- `py -3 -X utf8 -m unittest tests.test_p2p_development_control`: `21 tests, 19 PASS and 2 expected skips`.
- `py -3 -X utf8 scripts/p2p_development_control.py validate --root . --json`: `PASS`; `HEAD_DESCENDS_FROM_ANCHOR` / `ORIGIN_MAIN_EQUALS_ANCHOR`.
- `py -3 -X utf8 scripts/p2p_development_control.py status --root . --json`: `PASS`; same dynamic relations are exposed in `validation.source_anchor`.
- Active legacy field check: `current_promoted_source` absent from active authority JSON.
- P1-A checkpoint commit: `9e8bced18387bf786fbd6ed306acce83ad911e9d`; it contains the explicit anchor contract, static validator, focused plan ledger, and GOVREC01 snapshot update.
- Post-P1-B/P2-A implementation checkpoint/detect-changes: pending until the dynamic validator and focused GOVREC02 test slice is committed.

To be filled as remaining implementation slices complete:

- Final Anvien detect-changes: pending.
- Final exact commit/tree/parent and anchor identity: pending.
- Final regression matrix and compileall: pending.
- Fresh exact-final-head Supervisor report: pending.
- Terminal verdict: pending.
