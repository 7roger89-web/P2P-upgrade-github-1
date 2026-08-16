# P2P Eval Helper Boundary Alignment — Prerequisite for Real Context-Efficiency Benchmark Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-actual-status.md`

## Evidence Rules

- Record runtime/source evidence, not inferred contract behavior.
- Keep proxy evidence distinct from real worker/provider evidence.
- Use stable IDs matching the plan phases and cite exact command/output locations.
- Record unavailable metrics as `UNKNOWN`, never as invented token, cost, cache, or wall-time values.
- Record failures and blockers explicitly; do not hide them with fallback language.
- Keep all temporary lifecycle fixtures under repo-local `.tmp`; never package or resolve them.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-FAIL1`: `python scripts/p2p_workflow.py bootstrap ... --json` selected `.p2p/system/scripts/p2p_eval.py` and failed with `unrecognized arguments: design ...`.
- `E0-P0A-FAIL2`: `python scripts/doctor.py --package .` on the development checkout reported `uiux-runtime-payload` and `foundation-runtime-payload` missing root payload groups.
- `E0-P0A-SRC1`: `scripts/p2p_workflow.py` candidate order currently prefers `.p2p/system/scripts/p2p_eval.py` before root `scripts/p2p_eval.py`.
- `E0-P0A-SRC2`: root `scripts/p2p_eval.py --help` exposes project-eval v2 subcommands including `design`; installed `.p2p/system/scripts/p2p_eval.py --help` exposes UI/UX evaluator flags only.
- `E0-P0A-SRC3`: capability foundation files exist under development `.p2p/system/p2p_capabilities` and `.p2p/system/scripts`, proving the package-only doctor assumption is not a development-checkout invariant.
- `E0-P0A-PREV1`: prior context-efficiency proxy artifacts remain the frozen evidence set and are preserved unchanged.
- `E0-P0A-GRAPH1`: fresh Anvien graph after plan creation reports 279 files, 10,702 nodes, and 12,168 relationships; `scripts/p2p_workflow.py` has 263 symbols, 39 inbound references, 145 local relationships, 46 linked flows, and high scope risk.
- `E0-P0A-GRAPH2`: fresh Anvien file-detail for `scripts/doctor.py` reports 104 symbols, 3 inbound references, 74 local relationships, 13 linked flows, and high scope risk.
- `E0-P0A-GRAPH3`: Anvien file impact is a scope warning, not an edit prohibition: workflow direct impact 25 symbols/1 file/1 flow; doctor direct impact 15 symbols/1 file/1 flow.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-CONTRACT1`: root `scripts/p2p_eval.py design --help` exposes `--goal-contract` and `--profile`; it is the project eval v2 helper.
- `E1-P1A-CONTRACT2`: development `.p2p/system/scripts/p2p_eval.py design --help` returns the UI/UX-only `--source/--output` contract and cannot satisfy project eval v2.
- `E1-P1A-CONTRACT3`: extracted official `.15/scripts/p2p_eval.py design --help` exposes the project eval v2 contract.
- `E1-P1A-RESOLVE1`: pre-change candidate order selected `.p2p/system/scripts/p2p_eval.py` before the root project helper.
- `E1-P1A-RESOLVE2`: after the focused change, development resolution returns only the compatible root `scripts/p2p_eval.py`; the incompatible UI/UX helper is excluded.
- `E1-P1A-RESOLVE3`: the resolver probes `design --help` and requires the existing `--goal-contract` and `--profile` flags; it does not invoke a mutating eval operation.
- `E1-P1B-PACKAGE1`: official `.15` artifact SHA-256 is `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- `E1-P1B-PACKAGE2`: clean extraction of official `.15` passes `package_release.py verify` with 398 content files and 399 checksums.
- `E1-P1B-PACKAGE3`: clean extraction of official `.15` passes its portable package doctor; no source or ZIP mutation occurred.
- `E1-P1B-PACKAGE4`: source-owned `package_release.validate_uiux_runtime` and `validate_foundation_runtime` both pass against development `.p2p/system`.
- `E1-P1B-PACKAGE5`: installer source copies root project-eval `scripts/p2p_eval.py` into installed `.p2p/system/scripts/p2p_eval.py`; runtime UI/UX helper is copied under namespaced output names, so ownership is distinct.
- `E1-P1B-LIFECYCLE1`: development, portable, and installed roles are now explicit in `scripts/doctor.py`; the old `--package .` development invocation reports a single role mismatch instead of misleading missing-payload groups.
- `E1-P1B-LIFECYCLE2`: development role doctor passes after the generated runtime lock is refreshed; portable role doctor passes on clean official `.15` extraction.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-CODE1`: `scripts/p2p_workflow.py` now uses `helper_supports_project_eval` and `helper_path_is_transient`; no evaluator, router, worker, or second memory system was added.
- `E2-P2A-TEST1`: focused workflow suite passes 7/7 tests, including installed-root ancestor-fallback isolation.
- `E2-P2A-TEST2`: focused doctor-role suite passes 2/2 tests.
- `E2-P2A-TEST3`: the real development bootstrap command now returns `project_eval` status `REUSED`, `validation: PASS`; the original `unrecognized arguments: design` failure is gone.
- `E2-P2A-TEST4`: full repository unit/regression suite passes 81/81.
- `E2-P2B-CODE1`: `scripts/doctor.py` now infers/validates `development`, `portable`, and `installed` roles; development checks reuse the package builder's source contracts and installed foundation checks.
- `E2-P2B-TEST1`: development doctor auto and explicit role both return `ok=True`, zero FAIL checks.
- `E2-P2B-TEST2`: `--package` against development checkout returns one `role` failure with detected role `development`; no fake portable payload diagnosis is emitted.
- `E2-P2B-TEST3`: candidate source package build passes with 398 content files and 399 checksums.
- `E2-P2B-TEST4`: governance lock refresh reports 828 protected files and drift `PASS`; generated lock is development/candidate state, not official `.15`.
- `E2-P2B-TEST5`: canonical foundation doctor remains `PASS` with denominator 8 and full quorum 8/8.
- `E2-P2B-TEST6`: candidate `8.4.7-C-codex.16` portable doctor returns `ok=True`, role `portable`.
- `E2-P2A-TEST5`: current resolver accepts a canonical installed helper under an isolated `.tmp` root and rejects fallback to the ancestor development package when the installed helper is incompatible; no development-only path leaks.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-LIFE1`: candidate `.16` portable verify and role-aware doctor pass.
- `E3-P3A-LIFE2`: candidate `.16` fresh install fixture reports `FRESH_INSTALL` and `RESULT: PASS`; installed role doctor passes; installed workflow returns `PASS`.
- `E3-P3A-LIFE3`: upgrading an isolated fixture installed from official `.15` reports `UPGRADE_FROM_8.4.7-C-codex.15`, candidate version `.16`, helper hash matches candidate root helper, and installed doctor passes.
- `E3-P3A-LIFE4`: same-version reinstall reports `SAME_VERSION_REINSTALL` and preserves the backup inventory.
- `E3-P3A-LIFE5`: lifecycle fixtures use only repo-local `.tmp` roots; official `.15` ZIP remains unchanged.
- `E3-P3A-REG1`: full unit/regression suite is 81/81 PASS after the installed-root isolation correction.
- `E3-P3A-REG2`: development governance drift is PASS after the generated candidate lock refresh.
- `E3-P3A-REG3`: candidate package build/verify is PASS; no forbidden package paths are present in the built archive.
- `E3-P3A-REG4`: capability doctor and native Decision Trace doctor remain PASS with no external provider dependency.
- `E3-P3A-REG5`: canonical identities remain the exact eight named identities; denominator is 8 and full quorum is 8/8; Aesthetica is optional/noncanonical.
- `E3-P3A-REG6`: changed-surface secret scans pass; whole-repo secret findings remain separate and are not suppressed.
- `E3-P3A-REG7`: current project-eval v2 suite `validate` and `gate` both return `PASS`; the preserved 12-case context-efficiency proxy suite also returns `PASS` for its deterministic contract-proxy policy.
- `E3-P3A-REG8`: fresh changed-surface scans pass for `.p2p/system`, `scripts`, and candidate `.16/runtime`; the fresh whole-repo scan returns 7 pre-existing/reference `github-token` findings in bundled documentation and repo-local candidate/source snapshots, so secret hygiene remains a separate goal.
- `E3-P3A-PKG7`: clean official `.15` and candidate `.16` extractions each pass `package_release.py verify` with 398 content files and 399 checksum entries; official and candidate package doctor checks both return `ok: true` for their respective portable roles.
- `E3-P3A-HASH1`: fresh SHA-256 verification confirms official `.15` is unchanged at `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`; candidate `.16` is `afc3057de33c55e2d88b7d81ab641ffe172e9f5ba499249785635ef55401c2b8`.
- `E3-P3A-LIFE6`: post-review candidate artifact `P2P-8.4.7-C-Codex-Edition-v16-r2.zip` (package version `.16`) passes verify/portable doctor/secret scan; fresh install runs the installed workflow with the canonical installed helper; upgrade from official `.15` reports `UPGRADE_FROM_8.4.7-C-codex.15`; same-version reinstall reports `SAME_VERSION_REINSTALL` with unchanged backup inventory.
- `E3-P3A-HASH2`: the current unpromoted `.16` rebuild is immutable at `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf`; the prior `.16` artifact remains preserved and is not overwritten.
- `E3-P3B-PROXY1`: prior 12-scenario/48-trial context-efficiency proxy artifacts are preserved and unchanged; they remain proxy evidence only.
- `E3-P3B-PROXY2`: no real worker/provider execution, token totals, cache totals, or provider cost was inferred from this Goal.
- `E3-P3B-PROXY3`: current preserved proxy hashes are suite `d2f47a9447645fc8495498d031df8a20f6253319eb0ae73417327ee34e64d0d3`, QA evidence `de9b33f7b5f068d57a50aa8d6f83a7f2245fe63d805509c47f49d311c4d629b4`, and frozen fixture `978f29fe493be5ce6e2d2b0fbd820945880df6303fb561f74bbe36127eeac166`; gate metadata remains proxy-only with quality non-inferiority `UNKNOWN`.
- `E3-P3B-READY1`: `REAL_AB_BENCHMARK_READY=YES` for a separately scoped future benchmark against the current unpromoted `.16-r2` lifecycle infrastructure; this is not a claim that the benchmark has run or that quality/efficiency has been proven.

## Closure Evidence

- `E4-P4A-SUPERVISOR1`: independent Supervisor Review report `reports/supervisor/rp_supervisor_260814_090926_by_gpt-5-codex_p2p-eval-helper-boundary-alignment.md` returns exactly `PASS` for the bounded helper/package/runtime invariant; it explicitly excludes the later real worker/provider benchmark.
- `E4-P4B-CHANGE1`: final `anvien detect-changes --repo P2P-8.4.6-C-Codex-Edition-v4 --scope all --json` returns `Git diff failed: exit status 129`; no usable Git diff baseline or commit operation is available in this workspace, so commit status is `UNKNOWN/UNAVAILABLE`, not a test failure.
- `E4-P4A-GRAPH1`: final fresh Anvien analysis (with `--skip-git` because the workspace is not a Git repository) reports 281 files, 10,743 nodes, and 12,212 relationships; workflow file detail is 267 symbols/40 inbound/145 local/46 linked flows/high risk and doctor file detail is 104 symbols/3 inbound/74 local/13 linked flows/high risk; both are current and non-stale.
