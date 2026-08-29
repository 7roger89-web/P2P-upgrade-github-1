# Coder Report — P2P-GAME-TOOLCHAIN-02A

Date: 2026-08-29
Task: `P2P-GAME-TOOLCHAIN-02A`
Scope: minimum safe Three.js game capability integration, Direction D
Candidate: `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\P2P-GAME-TOOLCHAIN-02A-20260829-0003`
Candidate commit: `deaff7dbd79af5a1beb1e7e6a07c0436a2b8362c`
Candidate tree: `8495c1fe0f2faa8ae8a7a00d7f99b6a37195c1f3`

## Result

The isolated candidate implements the selected MengTo gameplay spine, Majid's
unique Three.js QA surface, and the existing P2P capability/vendor adapter
boundary. img2threejs is preserved as exact pinned provenance only because the
current taxonomy does not cleanly represent an external executable tool. No
provider was activated, no external code was executed, and no promotion,
merge, push, deployment, or Owner-worktree mutation occurred.

The candidate is technically ready for the Owner gate with deferred
img2threejs binding.

## Authority reconciliation

- Previous base SHA: `34ece1d1b804d0b794c56d51acba649b2d4a88c5`
- Previous base tree: `b3f541df0ba2215a4d752e67aa3672a22e242acb`
- Fresh official `origin/main` SHA: `9f5b91c9ab5178188aff6cc5520751b53b91dba7`
- Fresh official `origin/main` tree: `75435057264d5e376d2306ea7e9e80135c172e58`
- `34ece1d...` is an ancestor of `9f5b91c...`; merge-base is the previous
  base and there are 3 commits between them.
- Exact intervening commits:
  1. `f735d437473ecb158d472928dc2454a0c7a56967` — reconcile beginner gateway
  2. `1012428798ed43027d24ba57b7551321ee5e15fe` — normalize candidate file endings
  3. `9f5b91c9ab5178188aff6cc5520751b53b91dba7` — close reconciled candidate at owner gate
- The 9 changed paths are limited to the beginner gateway, current-canonical
  reconciliation evidence, existing `scripts/p2p_workflow.py`, and its test.
- Relevant seam classification: capability registry, external manifest, vendor
  snapshot/adapter, host/project projection, pin/context, and routing are
  `UNCHANGED`; C18/C19 workflow bridge changes are `COMPATIBLE_UPDATE`.
  No `CONFLICTING` 02A surface change was found.

## Implemented surface

- Added 10 model-routable `SKILL` records for the selected MengTo gameplay
  spine:
  `build_isometric_arpg`, `camera_controls`, `mobile_controls`,
  `action_combat`, `enemy_systems`, `enemy_ai`, `encounters`, `hybrid_assets`,
  `rigged_assets`, and `performance`.
- Added one model-routable `SKILL` record for
  `game.majid.threejs_qa_release`.
- Registry is valid at 27 capabilities. The allowed six capability classes are
  unchanged; no new taxonomy, router, registry, quorum, provider, or council
  was introduced. Canonical denominator remains 8 and full quorum remains
  `8/8`.
- Added `vendor_path` to each new local-snapshot provenance record so the
  existing adapter can resolve the snapshot fail-closed.
- Tightened only two existing negative-trigger lists to prevent false routing:
  whiteboard is negative for browser/Three.js performance terms, and the GPT
  image style capability is negative for technical camera requests. Existing
  vendor tests remain green.
- Added focused 02A coverage in
  `tests/test_p2p_game_toolchain_02a.py` and updated the existing visual-vendor
  registry-count assertion for the valid 27-record registry.

## Exact upstream closure

### MengTo

- Repository: `https://github.com/MengTo/skills.git`
- Commit: `4c716b516b6b0143f3037631306b3730d2832344`
- Tree: `faadfe0963132fdecee0ed55e79c4ed43ebae7e1`
- License: MIT
- Snapshot: `.p2p/vendor/skill/mengto-gameplay-spine-4c716b5`
- Snapshot SHA-256: `1d395a2c57b57b2572f3d851bf9105038eee26b5ab2d68f1e1eb7b7aa62382fb`
- Closure: 26 exact files — 10 selected `SKILL.md` files, 10 matching
  `agents/openai.yaml` files, the five direct rigged-asset dependencies, and
  the root license.
- `build-game-monster-system`, unrelated skills, examples, and assets are
  excluded. No Tripo content is present in this snapshot.

### Majid

- Repository: `https://github.com/majidmanzarpour/threejs-game-skills.git`
- Commit: `7221c1f4a6d2ae189a4d85d058d24f3228499d46`
- Tree: `9add48693c42ab51915576e3b03ede9ad2f61480`
- License: MIT
- Snapshot: `.p2p/vendor/skill/majid-threejs-qa-release-7221c1f`
- Snapshot SHA-256: `94b65aa700ec7a1ad4f8734891902312a6112f0a7878bfa303c2478079d13db4`
- Closure: 13 exact files — the `threejs-qa-release` entrypoint, host metadata,
  nine declared references, the canvas inspector, and the root license.
- The inspector imports `@playwright/test` and `pngjs`; dependencies are not
  installed and the script is not executed. The registry records
  `EXTERNAL_RUNTIME_NOT_INSTALLED` and
  `NOT_EXECUTED_EXTERNAL_DEPENDENCIES_UNINSTALLED`.

### img2threejs boundary

- Repository: `https://github.com/img2threejs/img2threejs.git`
- Commit: `441af85a96523569511154b6321859b79f3592f5`
- Tree: `02e909630089bc21162f4ed3340b321b955291d8`
- License: Apache-2.0
- Exact provenance is preserved in
  `.p2p/vendor/provenance/p2p-game-toolchain-02a.json` and the additive
  `candidate_sources` manifest entry.
- Five audited upstream paths are recorded, but no img2threejs source/assets
  are vendored. `executable_available_in_upstream=true`,
  `executable_registered_in_p2p=false`, and `execution_status=NOT_EXECUTED`.
- Integration status is `EXECUTABLE_REGISTRATION_PENDING_OWNER_GATE`.
  The candidate therefore does not claim a seventh capability class or an
  executable external-tool binding.

### Existing style context

`game.mengto.hybrid_assets` points to the existing
`visual.gpt_image_2_style_library` capability without copying it:

- Commit: `9a7b2e9c39f816d6c699c2a133e11b6d8bfdc464`
- Tree: `56b103dad637a95b9ec366eb7215459f28feb73e`
- Snapshot SHA-256: `29121408bbfdd4994ec4738b6ee181c80ba123cb7554c297e8a07091faddc482`
- Rights/commercial clearance remains `UNKNOWN`; no promotion or re-vendoring
  was performed.

## Invariant closure

| Invariant | Evidence | Result |
|---|---|---|
| C18 sole orchestration authority | Existing `derive_orchestration_requirement` and focused workflow probes | PASS |
| C19 bounded context authority | Existing targeted-context tests and new record requirements/pointers | PASS |
| JIT selective loading | Discovery patched to reject content reads; hybrid loads only its selected entrypoint | PASS |
| One router / one registry | Existing `p2p_uiux.router.foundation_route`; route output `single_router=true`; no new control plane | PASS |
| Direct prompt composition | Camera prompt: `PROMPT_COMPOSITION`, `DIRECT`, `MINIMAL`, `LOW`, `DETERMINISTIC`, zero workers | PASS |
| Focused implementation route | Combat prompt selects `game.mengto.action_combat` and existing `p2p_tecton` only | PASS |
| Reference-grounded asset route | Sword prompt selects hybrid asset guidance plus Majid QA; existing style and pending img provenance are pointers | PASS |
| Performance isolation | Performance prompt selects `game.mengto.performance`; no whiteboard, combat, character, or img route | PASS |
| High-impact protection | Authoritative architecture replacement remains `HIGH_RISK`, Owner `REQUIRED`, C18 `BLOCKED` | PASS |
| External/runtime safety | No network runtime, credentials, installs, paid calls, provider activation, or upstream execution | PASS |

## Focused probe matrix

| Request | Capability route | C18 route / worker | Notes |
|---|---|---|---|
| `Write a precise Arena Agent prompt to improve the Three.js camera.` | `game.mengto.camera_controls` | `DIRECT`, 0 workers | No combat/enemy/QA/hybrid/rigged/performance/img selection |
| `Implement a local combat cooldown bug fix.` | `game.mengto.action_combat` | `ONE_WORKER`, `p2p_tecton` | Focused implementation |
| `Create a Three.js xianxia sword from an approved reference.` | `game.mengto.hybrid_assets`, `game.majid.threejs_qa_release` | `ONE_WORKER`, `p2p_tecton` | GPT style reused by pointer; img2threejs remains pending provenance |
| `Improve browser performance in the current Three.js scene.` | `game.mengto.performance` | `ONE_WORKER`, `p2p_datos` | No unrelated game or visual vendor route |
| `Replace P2P's authoritative game/world architecture.` | no executable vendor route | `BLOCKED`, Owner gate required | `ARCHITECTURE`, `HIGH_RISK`, no downgrade |

## Validation evidence

- `python -B -m unittest discover -s tests -p 'test_p2p_game_toolchain_02a.py' -v`: 11/11 PASS.
- `python -B -m unittest discover -s tests -p 'test_p2p_vendor_skill_integration.py' -v`: 22/22 PASS.
- `python -B -m unittest discover -s tests -p 'test_p2p_visual_vendor_integration.py' -v`: 10/10 PASS.
- `python -B -m unittest discover -s tests -p 'test_p2p_lightweight_fastpath.py' -v`: 18/18 PASS.
- Registry/provenance JSON load and `load_registry`: PASS, registry count 27.
- Static Python compilation of the new test and vendored manifest validator:
  PASS, no bytecode/cache write required.
- `git diff --check`: PASS.
- Fresh Anvien analysis after candidate files: 1004 files scanned, 179 code
  files parsed, 0 parse failures; 42,544 graph nodes and 49,179 relationships.
- Pre-commit `anvien detect-changes --repo p2p-game-toolchain-02a-20260829
  --scope all`: exit 0; 45 staged candidate files, no affected process, with
  high-risk warnings limited to test-file graph projections.
- Fresh remote recheck immediately before commit: `origin/main` and
  `ls-remote` both returned `9f5b91c9...`; tree returned
  `75435057264d5e376d2306ea7e9e80135c172e58`.
- Candidate status after commit: clean (`0` porcelain lines).

Package doctor note: `doctor.py --package .` defaults to role `portable` and
therefore rejects this development checkout. The correct
`doctor.py --package . --role development` invocation reaches validation but
reports pre-existing `governance-drift` inherited from current canonical main
(`scripts/p2p_workflow.py` and the 20260828 notes). Those current-main files
are outside this candidate commit and were not modified to hide the drift.

## Mutation and safety ledger

- Owner checkout `D:\AI\P2P_dev\P2P-canonical-runtime-01`: 0 mutations.
- Original path `D:\AI\P2P_dev\P2P-upgrade-github`: not used as a working
  checkout; 0 mutations by this task.
- Thiên Hạ/game repositories: 0 mutations.
- Merge: 0; push: 0; promote: 0; deploy: 0.
- Provider activation: 0; external execution: 0; dependency installation: 0.
- Generated game assets: 0; paid calls: 0; credentials/secrets: 0.

## Residual boundary

- img2threejs executable registration and execution remain pending Owner review.
- Majid browser/canvas runtime proof remains pending because its external
  runtime dependencies are intentionally absent.
- This candidate proves offline routing, provenance, adapter loading, and
  governance boundaries; it does not claim live game-browser certification,
  host certification, release, or promotion.
- Stop point is the Owner gate. No automatic follow-up action is authorized.

Coder result: `PASS_WITH_DEFERRED_IMG2THREEJS_BINDING` for the isolated 02A
technical candidate; not promoted.
