# Notes and decisions — P2P-GAME-TRUYEN-MPFB-ADAPTER-01

## Authority and isolation

- Fresh canonical `origin/main` was fetched to SHA
  `7763ded3476b51acc09bccdfc6cb0c1720f28ba2` with tree
  `6a4f7dba5ffb86a6e5da6659ba3a0ae09b1a443b`.
- The requested root has incomplete `.git` metadata and was not treated as
  authority. Work is isolated to the repo-local candidate worktree
  `.tmp/p2p-game-truyen-mpfb-adapter-01-20260830`.
- The dirty canonical owner checkout and the separate Game Truyen repository
  remain untouched.

## Exact upstream and rights decision

- MPFB2 `v2.0.17` is bound to release SHA
  `80919fa4682335c41847f761a4d79dcad4124732` and tree
  `189a1d6694515ecfbdc40067218c5024389b4e43`.
- MPFB2 tool code and bundled graphical assets remain separate legal objects:
  code is GPL-3.0-or-later and bundled core assets are CC0-1.0.
- This lane enforces `CORE_CC0_ONLY`; third-party assets default to DENY and
  user-supplied custom assets require a separate rights gate.

## Adapter decision

- The existing `game.character.generate` capability remains the sole P2P
  identity and existing THREEJS_GAME/R3F_GAME routing remains the projection.
- The executable boundary is a strict parametric recipe, not raw images. The
  six-view pack is review-only and cannot be used as automatic reconstruction
  input.
- Forge execution is separate from provisioning and remains unauthorized.
  Static tests use synthetic recipes, manifests, and GLB fixtures only.
- Structural GLB readiness, downstream GLTFLoader readiness, visual match, and
  Golden Character readiness remain separate claims.

# Notes and decisions — P2P-FASTPATH-WIRE-01

## Authority and isolation

- Fresh canonical `origin/main` matched the expected SHA
  `d661654746f090136f37370f76578ee345b74994` (tree
  `92895a93a560221bdcd4664992ab16a4e8ec8cb4`). No drift; edited directly on the
  session branch `arena/01a051d5-p2p-upgrade-github-1`.
- MPFB, TMPGC, Game Truyen, local Windows execution, Blender, firewall, and TMP
  cleanup were not touched.

## Smallest useful wiring

- The C18 orchestration policy already computes `execution_lane`,
  `execution_policy` (minimum-sufficient-work / risk-proportional),
  `test_ceiling`, and `stop_rule`. The workflow's result-exposure seam
  (`orchestration_result_fields` + `verification_surface_for` in
  `scripts/p2p_workflow.py`) dropped those fields.
- Fix: forward the already-computed values as read-only result metadata. No new
  router/ontology/context system/council/framework was created; no lane is
  recomputed in the workflow.

## Verification

- Focused: `tests.test_p2p_lightweight_fastpath` 21/21 PASS (18 preserved + 3
  new). Adjacent shared-file suites green: workflow 7/7, EFF01 7/7, projection
  bundle 17/17.
- Pre-existing/out-of-scope: `tests.test_p2p_game_toolchain_02a` has 2 failures
  + 1 error at the unmodified baseline (fixture hash mismatches), not caused by
  this change.
