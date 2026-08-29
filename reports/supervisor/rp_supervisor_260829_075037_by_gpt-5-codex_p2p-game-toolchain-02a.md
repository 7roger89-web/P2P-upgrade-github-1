# Supervisor Report — P2P-GAME-TOOLCHAIN-02A

Review date: 2026-08-29
Review scope: isolated 02A candidate, authority reconciliation, selective
vendor closure, routing/JIT boundaries, and proportional verification
Candidate: `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\P2P-GAME-TOOLCHAIN-02A-20260829-0003`
Candidate implementation checkpoint: `deaff7dbd79af5a1beb1e7e6a07c0436a2b8362c`
Candidate tree: `8495c1fe0f2faa8ae8a7a00d7f99b6a37195c1f3`
Canonical base: `9f5b91c9ab5178188aff6cc5520751b53b91dba7`
Canonical tree: `75435057264d5e376d2306ea7e9e80135c172e58`

## Independent verdict

PASS for the bounded offline 02A technical candidate, with the img2threejs
executable binding explicitly deferred to the Owner gate.

The candidate is isolated, clean, and based on the freshly verified official
main. It adds only the approved MengTo/Majid surfaces, retains exact upstream
pins and hashes, routes through the existing single router, and leaves C18/C19
as the authoritative orchestration/context primitives. No Owner decision,
promotion, merge, push, deployment, provider activation, or live external
execution is implied by this PASS.

## Authority and lineage checks

- Fresh official remote `refs/heads/main` returned
  `9f5b91c9ab5178188aff6cc5520751b53b91dba7`.
- Fresh current-main tree returned
  `75435057264d5e376d2306ea7e9e80135c172e58`.
- Previous base `34ece1d1b804d0b794c56d51acba649b2d4a88c5` is an ancestor;
  merge-base equals that previous base and the count is 3.
- Candidate parent is the current main, and candidate `HEAD` is a descendant
  of the current-main SHA.
- Current-main changes since the previous base touch only the reconciled
  beginner gateway, its evidence, existing workflow bridge, and its test.
  Registry, external manifest, vendor adapter, host/project projections,
  routing, and pin/context seams are unchanged; C18/C19 bridge changes are
  compatible. No conflicting 02A surface change was found.

## Diff and scope review

The implementation commit contains exactly 45 files: the capability registry,
provenance sidecar, 39 selected vendor files, additive external candidate
metadata, two focused test surfaces, and the dated decisions log. Independent
comparison of `HEAD^..HEAD` found:

- 0 changes to `scripts/p2p_workflow.py`;
- 0 changes to governance, router, C18, C19, canonical agent profiles, or
  Owner state;
- 0 Tripo paths, 0 `node_modules`, and 0 package/lock files in the new vendor
  snapshots;
- 10 MengTo records plus exactly one Majid QA record, all `TYPE=SKILL`,
  `STATUS=DISCOVERED`, noncanonical, and nonoptional;
- no img2threejs capability ID and no new capability class.

The two modified existing negative-trigger lists are narrow compatibility
guards: technical camera prompts no longer select the GPT image-style vendor,
and browser performance prompts no longer select the whiteboard vendor. The
existing visual/vendor regression suite passes with the new registry count.

## Provenance and closure review

MengTo is pinned to commit
`4c716b516b6b0143f3037631306b3730d2832344`, tree
`faadfe0963132fdecee0ed55e79c4ed43ebae7e1`, MIT, snapshot
`1d395a2c57b57b2572f3d851bf9105038eee26b5ab2d68f1e1eb7b7aa62382fb`, with 26
exact files. The selected set contains the ten requested skill entrypoints,
all ten matching host metadata files, the five direct rigged-asset
dependencies, and the root license. The excluded monster-system and
unrelated material is absent.

Majid is pinned to commit `7221c1f4a6d2ae189a4d85d058d24f3228499d46`, tree
`9add48693c42ab51915576e3b03ede9ad2f61480`, MIT, snapshot
`94b65aa700ec7a1ad4f8734891902312a6112f0a7878bfa303c2478079d13db4`, with 13
exact files for `threejs-qa-release`. Its inspector's `@playwright/test` and
`pngjs` dependencies are not installed; execute status is blocked without
installation and network use is false.

img2threejs is pinned in both the candidate manifest and provenance sidecar to
commit `441af85a96523569511154b6321859b79f3592f5`, tree
`02e909630089bc21162f4ed3340b321b955291d8`, Apache-2.0. Five audit paths are
recorded as not vendored. Executable availability is recorded as true, but
registration is false and execution is `NOT_EXECUTED`; this is the correct
pending Owner-gate boundary for the current taxonomy.

The hybrid record references the existing GPT style capability rather than
copying it. Its existing pin/tree/snapshot and unresolved commercial-rights
state remain unchanged.

## Behavioral evidence

Fresh focused probes and regression suites independently returned:

- camera prompt: `game.mengto.camera_controls`; C18 `DIRECT`, minimal/low/
  deterministic, zero workers;
- local combat cooldown: `game.mengto.action_combat`; one existing
  `p2p_tecton` worker;
- approved-reference sword: `game.mengto.hybrid_assets` plus Majid QA; existing
  style pointer and pending img provenance are visible, without Tripo;
- browser performance: `game.mengto.performance`; unrelated whiteboard,
  combat, character, and img routes absent;
- authoritative game/world replacement: C18 `ARCHITECTURE`, Owner `REQUIRED`,
  `HIGH_RISK`, `BLOCKED`, zero workers.

Test results:

- 11/11 `tests/test_p2p_game_toolchain_02a.py`;
- 22/22 `tests/test_p2p_vendor_skill_integration.py`;
- 10/10 `tests/test_p2p_visual_vendor_integration.py`;
- 18/18 `tests/test_p2p_lightweight_fastpath.py`;
- registry/provenance JSON load, exact snapshot hashes, static compilation,
  and `git diff --check`: PASS;
- Anvien refresh: 1004 files scanned, 179 code files parsed, 0 parse failures;
  pre-commit detect-changes: exit 0 with 45 staged files and no affected
  process.

## Boundary and residual risk

- There is no live Three.js game browser/runtime in this repository candidate;
  this review does not claim live playtest or host certification.
- Majid's browser inspector is statically vendored only; dependency installation
  and script execution remain deliberately blocked.
- Package doctor with the default `portable` role rejects this development
  checkout. With the correct `development` role, it reaches governance
  validation but reports drift inherited from the freshly accepted canonical
  main (`scripts/p2p_workflow.py` and the 20260828 decisions log). The
  candidate did not alter those upstream files or suppress that report.
- The canonical checkout had pre-existing dirty state; this review only read
  it and did not modify it. The original noncanonical path is not a git
  checkout and was not used for candidate mutations.

## Safety closure

- Candidate status after implementation commit: clean.
- Owner checkout mutations: 0.
- Original P2P path mutations: 0.
- Thiên Hạ/game repository mutations: 0.
- Merge/push/promote/deploy: 0.
- Provider activation, external execution, installs, paid calls, and secrets: 0.

No finding requires a code correction within the assigned 02A scope. Stop at
the Owner gate.

Supervisor verdict: `PASS` for the isolated technical candidate, with
img2threejs binding deferred and no promotion authority.
