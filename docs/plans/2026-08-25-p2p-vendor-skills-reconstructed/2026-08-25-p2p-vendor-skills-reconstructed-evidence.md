# P2P Vendor Skills — Reconstruct Candidate on Valid Git Authority Evidence Ledger

## Metadata

- Date: `2026-08-25`
- Plan: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-plan.md`
- Evidence: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-evidence.md`
- Benchmark: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-benchmark.md`
- Actual status: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-actual-status.md`

## Evidence Rules

Evidence is fresh for the reconstructed candidate and distinguishes source
authority, technical validation, inherited doctor findings, supervisor review,
and Owner approval/promotion. A report or green test is not authority by
itself. All command results below must be expanded with exact output and exit
status as the work proceeds.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`, `P1-A`

- `E0-P0A-AUTH1` — Broken-root Git inspection: root `.git` lacks usable
  `HEAD`, `config`, and `index`; root `status`, `rev-parse`, and `log` fail.
  Root remains read-only and is not used as a worktree.
- `E0-P0A-AUTH2` — Valid common repository inspection: supplied remote is
  `https://github.com/7roger89-web/P2P-upgrade-github-1.git`; local verified
  ref `557b502758581812a8845355ed6b426ba75372ec` has tree
  `2bd89d97f8877d372f0444218ec9c7339da14d7f` and parent
  `3f3ad28f7acb65f782c751bea78d039ebd59b5f2`. Fresh `git ls-remote --heads`
  and local ref ancestry checks did not prove a newer descendant owner-approved
  canonical/promoted base for this scope. `RECONSTRUCTION_BASE_REASON` is
  `USER_VERIFIED_CLEAN_REFERENCE; NO_NEWER_DESCENDANT_CANONICAL_OR_OWNER_PROMOTED_REF_PROVEN`.
- `E0-P0A-BASE1` — New candidate worktree:
  `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-vendor-skills-reconstructed-03`,
  branch `codex/p2p-vendor-skills-reconstructed-03`, HEAD `557b502…`, supplied
  remote, clean pre-change status. Separate detached baseline worktrees were
  used for C35 and doctors.
- `E0-P0A-HASH1` — Broken-root recheck matched all supplied values: registry
  `fd259d9e…cc10`, adapter `d469a15d…4490`, router `070c5e6b…2be2`, vendor
  test `2b5f0986…88b7`, foundation test `2e87eb5f…3884`, whiteboard tree
  `55dbed47…8742`, copywriter tree `5a02c082…2830`.
- `E0-P0A-C351` — Exact baseline command in detached clean base:
  `python -m unittest tests.test_p2p_c35_provider_neutral_runtime` => exit
  `0`, `Ran 57 tests`, `OK`.
- `E0-P0A-DOCTOR1` — Fresh clean-base doctor outputs: package doctor exit 1
  for portable-vs-development role mismatch; development doctor exit 1 for
  inherited governance drift while runtime/profile/foundation checks pass;
  capability doctor exit 0 `PASS`, registry `13`, canonical `8/8`, optional
  Aesthetica `RESOLVED` without execution/identity proof.
- `E0-P0A-ANV1` — Candidate graph refresh:
  `anvien analyze <candidate> --force --no-gitignore` exit 0, 922 files
  scanned, 165 parsed code, 0 failed, graph built.
- `E0-P0A-ANV2` — Anvien `file-detail`/impact attempts for hidden
  `.p2p/system/...` files returned `not found`; this is recorded as graph
  coverage limitation, not as source absence. Direct source diff and tests are
  required for those paths.

## E1 - P1 Evidence

Matching plan item(s): `P1-B`

- `E1-P1B-SCOPE1` — Baseline-vs-broken comparison identifies unrelated drift
  in profiles/configuration/role/model/C35 surfaces; these remain preserve-only.
- `E1-P1B-SCOPE2` — Frozen editable list: vendor trees, new `vendor_skill.py`,
  two vendor registry records, additive router projection, new vendor test,
  and only registry-count/adapter-boundary foundation expectations required by
  the added adapter/records.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-HASH1` — post-copy tree hashes are exact: whiteboard
  `55dbed4743cad90f80d1603ed639508c8e3a6e650a1abccfe7d4e8b2e148742c`,
  copywriter `5a02c082b531b6731dbdd6e55ccc8798ba2514bbb27df8e9c2ef74c88752830d`.
  Adapter and vendor-test source hashes remain the supplied values
  `d469a15d…4490` and `2b5f0986…88b7`.
- `E2-P2A-SRC1` — registry JSON parses and `load_registry` returns
  `valid=True`, `capability_count=15`, canonical denominator `8`, full quorum
  `8/8`; the two vendor records are `SKILL`, noncanonical, nonoptional.
- `E2-P2B-SRC1` — router diff is additive: vendor adapter import, repository
  root derivation, vendor readiness branch, and `vendor_skills` projection;
  existing UIUX/Aesthetica route logic remains unchanged.
- `E2-P2B-TEST1` — focused results: vendor integration `17/17 OK`, foundation
  `28/28 OK`, combined command `45/45 OK`. Discovery remains metadata-only;
  optional dependency probes remain blocked without install/network.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-TEST1` — `python -m compileall -q .p2p/system scripts tests` exits
  `0`; post-reconstruction C35 exits `0`, `Ran 57 tests`, `OK`; focused
  vendor/foundation suites exit `0` with `17/17`, `28/28`, combined `45/45`.
  Compile emits only the pre-existing `SyntaxWarning` at
  `tests/test_p2p_live_certification.py:179`.
- `E3-P3A-DOCTOR1` — candidate package doctor exits `1` only for the expected
  portable-vs-development role mismatch; development doctor exits `1` with the
  same inherited governance drift reported by the clean base; capability doctor
  exits `0` `PASS`, registry `15`, canonical denominator `8`, full quorum
  `8/8`, vendor records `HEALTHY`, and Aesthetica remains `RESOLVED` without
  execution/identity proof. No attributable candidate-only blocker is present.
- `E3-P3A-DIFF1` — supplied vendor adapter/test hashes and both snapshot tree
  hashes match exactly; integrated file hashes are allowed to differ because
  they were reapplied onto the verified base. C35 state file was restored after
  the test and is excluded from the candidate diff.
- `E3-P3B-GIT1` — valid Git status shows only the three intended tracked
  integration edits plus the new adapter, vendor snapshots, focused test, and
  plan artifacts. `git diff --stat` reports `262 insertions, 4 deletions` in
  the three tracked source files; no unrelated baseline/profile/role/model
  surface is changed.
- `E3-P3B-ANV1` — after the bounded final scope was staged, the fresh candidate
  graph registered as `p2p-vendor-reconstructed-03` was checked with
  `anvien detect-changes --repo p2p-vendor-reconstructed-03 --scope all --json`.
  It exits `0` and reports `changed_files=44`, `affected_files=6`,
  `changed_count=177`, `risk_level=low`; affected paths are the four plan
  ledgers and the two focused test files. The semantic projection includes
  text vendor files but does not fully model binary assets and some hidden
  `.p2p` paths; direct Git diff, hashes, and focused tests remain authoritative
  for the complete candidate scope.
- `E3-P3B-REPORT1` — coder report:
  `reports/coder/rp_coder_260825_134605_by_gpt-5-codex_p2p-vendor-skills-reconstructed.md`.
- `E3-P3B-COMMIT1` — checkpoint is recorded exactly as commit
  `d29801bd37a53207f81e89eaa295cbef0802b951`, tree
  `27bac22f1f2cba670425a28d050a566916d23265`, parent `557b502…`; closure
  worktree is clean. The pre-review to checkpoint implementation-subject
  result is `EXACT_MATCH`; no post-review source mutation exists. Ancestry is
  `ORIGIN_MAIN_ANCESTOR_OF_557B`.
- `E3-P3B-SUP1` — fresh independent supervisor report
  `reports/supervisor/rp_supervisor_260825_134605_by_gpt-5-codex_p2p-vendor-skills-reconstructed.md`
  records exactly `PASS` for this candidate and is preserved unchanged during
  this closure. Its PASS applies to the exact checkpoint because the
  implementation subject identity was proven.

- `E4-OWNER-APPROVAL1` — the current explicit Owner instruction approves the
  exact subject commit `d29801bd37a53207f81e89eaa295cbef0802b951` and tree
  `27bac22f1f2cba670425a28d050a566916d23265`. The approval is bound to both
  hashes; no approval CLI was executed and no approval was inferred from
  silence. This records Owner approval only, not promotion.
- `E4-HASH-CLOSURE1` — closure recheck preserved the implementation/vendor/test
  hashes: registry `36d74ff8…b5cb97e`, adapter `d469a15d…f4490`, router
  `9074d8b4…7f641`, foundation test `473936b8…a7eb`, vendor test
  `2b5f0986…88b7`, whiteboard tree `55dbed47…8742c`, and copywriter tree
  `5a02c082…2830d`. Existing Supervisor report blob remains
  `8cdd091b1763f3ab86c708ac79cff61064d3a47c1dadf2d29d32f95f32626e85`.

## Closure Evidence

The final closure records the exact checkpoint, clean worktree, subject identity,
ancestry, preserved Supervisor PASS, unchanged source/vendor/test hashes, and
explicit Owner approval. Technical PASS, Supervisor PASS, Owner approval, and
promotion remain separate states. No merge, push, release, deployment, or
promotion is performed by this plan.
