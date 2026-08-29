# P2P Projection Contract 01D Fresh-Main Reconciliation Evidence Ledger

## Metadata

- Date: `2026-08-29`
- Plan: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-actual-status.md`

## Evidence Rules

Only fresh command output, direct source inspection, focused test output,
exact Git object identity, and independent Supervisor evidence count. Prior
01C evidence is source/intended-behavior input, not current-main proof. A
PASS label without actual output is not evidence. Protected-state mutations
are checked from isolated paths and not inferred.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-REMOTE1`: isolated workspace created from a valid Git object store;
  origin set to `https://github.com/7roger89-web/P2P-upgrade-github-1.git`.
- `E0-P0A-REMOTE2`: fresh direct fetch of `refs/heads/main` and direct
  `ls-remote` returned
  `1c84bc41421dcbe502d40b71fead5022231d0541`.
- `E0-P0A-REMOTE3`: `refs/remotes/origin/main` tree is
  `a11a44b676401d8a424db8ed05632c8d22952d26`.
- `E0-P0A-INT1`: `76901b24f30988159ebc1b96076512623d09eabd` actual paths are
  SEC01 capability/security adapter/registry/orchestration/tests; classified
  `COMPATIBLE_ADJACENT_CHANGE`, not dropped.
- `E0-P0A-INT2`: `61d51e16628ebdfe156b750a54ca8759b45634a7` changes only SEC01
  decision/evidence documents; classified `UNRELATED` to implementation.
- `E0-P0A-INT3`: `1c84bc41421dcbe502d40b71fead5022231d0541` adds only a SEC01
  Supervisor report; classified `UNRELATED` to implementation.
- `E0-P0A-SRC1`: fresh main `project_pin.py` is v1-only; old 01C source hash
  differs and contains reviewed v2 mode/binding validation.
- `E0-P0A-SRC2`: fresh main `project_context.py` has existing v1 readiness;
  old 01C adds explicit v2 `PROJECTION_ONLY` dispatch while preserving v1.
- `E0-P0A-SRC3`: fresh main `host_projection.py` remains the pure-plan
  surface; no materializer or runtime copy is present.
- `E0-P0A-SRC4`: current relevant SPEC cluster was read in full in declared
  dependency order; repository contains no `SPEC-MAP.md`, so that absence is
  recorded rather than invented.
- `E0-P0A-SRC5`: old reviewed 01C has the projection-only SPEC and bounded
  materializer; these are inspect-only behavior evidence, not copied blindly.
- `E0-P0A-SRC6`: old reviewed 01C focused test module covers v2/security
  contract; fresh main lacks it.
- `E0-P0A-SRC7`: current C18, C19, FASTPATH, host projection, AUTO, and
  workflow tests are present on fresh main and are preserve/validate targets.
- `E0-P0A-ANV1`: `anvien analyze --force ...` failed while writing isolated
  `.anvien/analyze.tmp/csv/relations.csv` with `There is not enough space on
  the disk`; graph/file-detail/impact counts are therefore UNKNOWN.
- `E0-P0A-ISO1`: only the new isolated workspace was inspected/used; no Owner,
  old 01C, Thiên Hạ, or unrelated worktree path was targeted.
- `E0-P0A-BOUND1`: no command or source change invoked img2threejs, Tripo,
  providers, secrets, or Thiên Hạ; required counters remain zero.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SRC1`: `project_pin.py` working-tree blob is exactly
  `f82d7b2176b8b23f20c1237cade352eb5751ae6a`, the reviewed 01C source blob.
- `E1-P1A-SRC2`: `project_context.py` working-tree blob is exactly
  `b595022e2d3f91c5eda5fd1e1e537a67882c2bf9`, the reviewed 01C source blob.
- `E1-P1A-SRC3`: new `project_materialization.py` working-tree blob is exactly
  `ff5088011f09e4f8820298529e79b77beaa5d612`, the reviewed 01C source blob.
- `E1-P1A-SRC4`: direct diff against fresh `origin/main` contains only the
  intended two modifications and one addition for P1-A; SEC01 paths have
  `SEC01_PRESERVATION_DIFF=NONE`.
- `E1-P1A-SRC5`: import smoke passed for project pin, project context, and
  materializer; v1/v2 schema and mode constants were observable.
- `E1-P1A-VAL1`: BOM-aware no-write Python compile passed for 244 files in
  `.p2p/system/p2p_capabilities`, `scripts`, and `tests`; one pre-existing
  SyntaxWarning remains in `tests/test_p2p_live_certification.py:179`.
- `E1-P1A-VAL2`: `git diff --check` passed for the P1-A working tree.
- `E1-P1A-VAL3`: `anvien detect-changes --scope all --json` returned
  `Repository not found. Run: anvien analyze`; no graph change claim is made.
- P1-A source acceptance is complete. P1-B behavioral SPEC/test work remains
  pending; no final candidate freeze has occurred.
- `E1-P1B-SRC1`: projection-only SPEC and focused projection contract test
  were added from the reviewed 01C behavior source; old reports/plans were not
  copied.
- `E1-P1B-SRC2`: P1-B diff is limited to the new SPEC and
  `tests/test_p2p_projection_contract.py`; current-main SEC01 preservation
  remains `NONE`.
- `E1-P1B-TEST1`: projection/security contract unittest passed `15/15`.
- `E1-P1B-TEST2`: pin lifecycle script passed with `negative_cases=5` and
  `map_gate=FAIL_CLOSED`.
- `E1-P1B-TEST3`: host projection passed `30/30` after supplying the three
  existing read-only vendor snapshots as 98 hardlinks in the isolated test
  workspace; links were removed and no source checkout changed.
- `E1-P1B-TEST4`: workflow passed `7/7` in a dedicated validation clone whose
  root was outside `.tmp`. A direct run rooted under `.tmp` produced one
  setup/environment false negative because `helper_path_is_transient` sees
  the workspace ancestor; the source function is unchanged and canonical-root
  validation passed.
- `E1-P1B-TEST5`: C18 `6/6`, C19 plus comparison `20/20`, FASTPATH `18/18`,
  and AUTO `7/7` passed on the candidate source.
- `E1-P1B-TEST6`: BOM-aware no-write compile already passed for 244 Python
  files; the pre-existing `tests/test_p2p_live_certification.py:179`
  SyntaxWarning remains non-fatal.
- `E1-P1B-TEST7`: `git diff --check` passed after P1-B test/spec additions.
- P1-B acceptance is complete. P2 focused validation and exact candidate
  freeze remain; no Supervisor review or push has happened.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-TEST1`: projection/security contract passed `15/15` on the current
  candidate HEAD.
- `E2-P2A-TEST2`: pin lifecycle passed with `negative_cases=5` and
  `map_gate=FAIL_CLOSED`.
- `E2-P2A-TEST3`: C18 passed `6/6`; C19 plus comparison passed `20/20`.
- `E2-P2A-TEST4`: FASTPATH passed `18/18`; AUTO passed `7/7`.
- `E2-P2A-TEST5`: host projection passed `30/30` with 98 read-only hardlinked
  snapshot fixture files; links were removed before candidate status was
  checked.
- `E2-P2A-TEST6`: workflow passed `7/7` in a dedicated validation clone
  outside `.tmp`; the clone and test-created state were removed.
- `E2-P2A-TEST7`: BOM-aware no-write compile passed for `245` Python files;
  the only observed warning is the pre-existing
  `tests/test_p2p_live_certification.py:179` SyntaxWarning.
- `E2-P2A-TEST8`: full candidate-range `git diff --check` passed; SEC01
  preservation diff is `NONE`.
- `E2-P2A-ID1`: fresh main is an ancestor of the candidate HEAD;
  `git rev-list --left-right --count origin/main...HEAD` is `0 3` and the
  candidate range contains no merge commits.
- `E2-P2A-ID2`: candidate diff allowlist is exactly two existing projection
  files, one materializer, one projection SPEC, one focused test, and the four
  01D planner artifacts; no SEC01 path is changed.
- `E2-P2A-ID3`: exact final SHA/tree will be recorded out-of-tree immediately
  after the last pre-freeze commit; no post-freeze evidence commit is allowed.
- Focused validation is PASS. No Council, provider, secret, runtime, game, or
  Thiên Hạ action was performed. Candidate is ready to freeze after this
  evidence update and one final docs-only commit.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`

Pending until post-review fresh remote check. A drift or topology failure is a
hard stop and must be recorded without mutating the frozen candidate.

## Closure Evidence

Pending. Reports and closure evidence must be written outside the frozen
candidate subject, or before the final candidate commit; no post-review report
commit may be appended to the promoted candidate.
