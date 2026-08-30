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
