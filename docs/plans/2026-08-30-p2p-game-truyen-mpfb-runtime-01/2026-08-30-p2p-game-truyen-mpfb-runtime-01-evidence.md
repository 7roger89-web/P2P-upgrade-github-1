# P2P Game Truyen MPFB Runtime 01 Evidence Ledger

## Metadata

- Date: `2026-08-30`
- Plan: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-plan.md`
- Evidence: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-evidence.md`
- Benchmark: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-benchmark.md`
- Actual status: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-actual-status.md`

## Evidence Rules

This ledger distinguishes source/API inspection, contract tests, implementation
readiness, and actual Blender execution. No test in this workstream may claim
that Blender or MPFB2 ran.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GIT1`: exact working checkout is detached at
  `31647b2f7ff6a60225fb922e876326b825ccbc1a`, tree
  `c215465260c6838efeb17bb52b6491d65bac82a9`; pre-existing untracked
  Supervisor promotion report is preserved.
- `E0-P0A-SMOKE1`: MPFB-SMOKE-01 receipt reports
  `CANONICAL_ENTRYPOINT_NOT_EXECUTABLE`, `NETWORK_DENY_NOT_ENFORCED`, and
  downstream `BLENDER_MISSING`; no process, GLB, or provenance was created.
- `E0-P0A-SRC1`: current parent builds Blender `--background --python` argv but
  has no Blender body, no `main`, no `bpy`, and only declarative network deny.
- `E0-P0A-MPFB1`: local pinned source checkout is exact MPFB2 commit
  `80919fa4682335c41847f761a4d79dcad4124732`, tree
  `189a1d6694515ecfbdc40067218c5024389b4e43`; source remains inspect-only.
- `E0-P0A-API1`: source inspection identifies supported calls
  `HumanService.create_human`, `HumanService.set_character_skin`, and
  `HumanService.add_builtin_rig`; native Blender glTF export is the export
  boundary. Exact rig-name mapping remains a P1 implementation fact to bind to
  the source's standard rig files.
- `E0-P0A-GRAPH1`: Anvien refresh completed for the target checkout with 1,074
  scanned files, 191 parsed code files, zero parse failures, and 46,966 nodes.
- `E0-P0A-IMPACT1`: Anvien could not resolve the hidden `.p2p` source file as a
  file node; symbol impact requests resolved to unresolved test references.
  This is recorded as a graph coverage limitation, not as zero blast radius.
- `E0-P0A-WORKFLOW1`: P2P workflow classification marked the request as
  separate objectives and its generated Goal Contract as blocked; this does not
  expand or cancel the explicit user-authorized bounded implementation scope.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`, `P1-C`

- `E1-P1A-SRC1`: exact pinned MPFB2 source inspection binds `mpfb.register()`,
  `HumanService.create_human(...)`, `HumanService.add_builtin_rig(...,
  "game_engine", import_weights=True)`, and
  `HumanService.set_character_skin(..., skin_type="GAMEENGINE")`. The script
  does not invent a generic runner or caller-selected script path.
- `E1-P1A-SRC2`: the exact source contains `rig.game_engine.json` and
  `weights.game_engine.json`; the entrypoint uses the supported
  `add_builtin_rig` file-fragment API and the native Blender glTF operator.
- `E1-P1A-SRC3`: the dedicated body and parent both require MPFB2 2.0.17,
  release SHA `80919fa4682335c41847f761a4d79dcad4124732`, release tree
  `189a1d6694515ecfbdc40067218c5024389b4e43`, `CORE_CC0_ONLY`, and an exact
  `core_assets` manifest map.
- `E1-P1A-TEST1`: strict child argv parser accepts only the bounded recipe,
  output, MPFB root, manifest, character, pin, asset-policy, and network
  fields; unknown flags, duplicates, positional values, arbitrary script
  paths, and arbitrary Python are rejected.
- `E1-P1A-TEST2`: recipe/job binding, pin/root/core-asset hash verification,
  equal-proportion representability, pre/post two-output allowlist, and GLB
  plus provenance binding are covered by synthetic mocks.
- `E1-P1A-TEST3`: dedicated body is importable without Blender by delaying
  `bpy` import until execution; it binds the checked-in `.p2p/system` package
  root before importing P2P helpers; no Blender or MPFB2 execution occurred.
- `E1-P1B-TEST1`: Windows helper derives a deterministic identity from the
  exact executable path and job identity, creates an exact program-bound
  outbound Defender Firewall block, and verifies profiles/rule/application
  filter with `shell=False` command execution.
- `E1-P1B-TEST2`: disabled firewall profiles, rule collisions, path mismatch,
  and unavailable command setup fail closed before process spawn.
- `E1-P1B-TEST3`: context-managed release is tested after success, command
  failure, and timeout; cleanup failure is surfaced rather than hidden.
- `E1-P1B-TEST4`: the receipt records enforcement identity, exact executable,
  mechanism, privilege requirement, setup/enforcement/cleanup results, and
  rule-created state. No live host rule was created.
- `E1-P1C-TEST1`: parent argv points to the dedicated entrypoint and rejects
  `--python-expr`, `-c`, arbitrary script paths, and any mismatch in the
  bound recipe/output/manifest/job/pin/policy fields.
- `E1-P1C-TEST2`: parent revalidates recipe, manifest, root hash, and empty
  output root before spawn; changed recipe/manifest and undeclared outputs are
  rejected.
- `E1-P1C-TEST3`: isolation setup is entered before the injected Popen; if
  setup cannot be established, Popen is never called.
- `E1-P1C-TEST4`: shell-free process invocation, timeout tree termination,
  command-failure cleanup, success cleanup, and receipt propagation pass.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`

- `E2-P2A-TEST1`: focused suite
  `python -m unittest tests.test_p2p_game_truyen_mpfb_adapter_01` passes
  `30/30`; all Blender/MPFB/process/output behavior is synthetic or mocked.
- `E2-P2A-TEST2`: targeted `py_compile` passes for the parent, dedicated body,
  network helper, and focused test; full `compileall` is the final ceiling
  check and does not execute Blender/MPFB2.
- `E2-P2A-TEST3`: `git diff --check` passes with no whitespace errors.
- `E2-P2A-CHANGE1`: fresh Anvien graph refresh after implementation reports
  1,079 scanned files, 191 parsed code files, zero parse failures, 47,325
  nodes, and 54,650 relationships. Staged `detect-changes` reports 9 changed
  files, 6 affected files, low aggregate risk, and no affected processes.
  Hidden `.p2p` source remains outside
  reliable file-detail/symbol-impact coverage; this is recorded as a graph
  limitation, not zero impact.
- `E2-P2A-FREEZE1`: candidate SHA/tree are recorded in the final return after
  the implementation/evidence commit; the pre-existing untracked promotion
  report remains preserved.
- `E2-P2A-SUPERVISOR1`: fresh Supervisor review is required on that exact
  candidate and must issue only an implementation-readiness verdict. It must
  explicitly retain `ACTUAL_EXECUTION_PROVEN=NO`.

## Closure Evidence

Final closure is pending only the change-detection output, candidate commit,
and fresh exact-subject Supervisor report. Runtime execution remains
intentionally NOT_RUN.
