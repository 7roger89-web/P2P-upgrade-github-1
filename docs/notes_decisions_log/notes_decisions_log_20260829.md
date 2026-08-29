# Notes and decisions — P2P-GAME-TOOLCHAIN-02A

## Authority and isolation

- Current canonical main was freshly verified from the official remote at
  `9f5b91c9ab5178188aff6cc5520751b53b91dba7` with tree
  `75435057264d5e376d2306ea7e9e80135c172e58`.
- Previous base `34ece1d1b804d0b794c56d51acba649b2d4a88c5` is an ancestor;
  the three intervening commits are compatible with 02A seams.
- Work is isolated to `.tmp/P2P-GAME-TOOLCHAIN-02A-20260829-0003`.
  The owner checkout, the prior working checkout, and all game repositories
  remain unmodified.

## Direction D decisions

- Vendored only the selected MengTo gameplay spine and its direct rigged-asset
  closure: 26 exact files at the pinned MIT commit.
- Vendored only Majid's unique `threejs-qa-release` QA surface: 13 exact files
  at the pinned MIT commit. Its Playwright/PNG runtime remains uninstalled and
  unexecuted.
- Added 11 model-routable `SKILL` records to the existing registry. No new
  capability class, router, registry, quorum, provider, or taxonomy was added.
- img2threejs remains an Apache-2.0 provenance-only candidate at its pinned
  commit/tree. No source or asset is vendored, no executable is registered,
  and no upstream code is run.
- The existing GPT image style capability is referenced as an existing context
  pointer only; its unresolved rights status is not promoted or re-vendored.
- C18 remains the orchestration authority and C19 remains the bounded context
  authority. Vendor content is selected and loaded JIT through the existing
  router/adapter only.

## Evidence state

- Initial route probes are focused on camera, combat, sword/reference, browser
  performance, and high-impact architecture replacement.
- Focused validation and the final coder/supervisor reports are recorded after
  the candidate commit; no merge, push, promotion, deployment, provider
  activation, dependency installation, or paid external call is permitted.
