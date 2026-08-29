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

## Final checkpoint

- Candidate implementation commit: `deaff7dbd79af5a1beb1e7e6a07c0436a2b8362c`;
  tree: `8495c1fe0f2faa8ae8a7a00d7f99b6a37195c1f3`.
- Coder report: `reports/coder/rp_coder_260829_075037_by_gpt-5-codex_p2p-game-toolchain-02a.md`.
- Independent supervisor report:
  `reports/supervisor/rp_supervisor_260829_075037_by_gpt-5-codex_p2p-game-toolchain-02a.md`.
- Technical stop: Owner gate, with img2threejs executable binding deferred.

## P2P-AUTO01 current-canonical reconciliation — 2026-08-29

### Authority and isolation

- Fresh official `refs/heads/main` resolved to
  `b8d09fc7a0e4a91e75db7f10dc8cfaea007ba37a` with tree
  `91012e41e67a956bbca311368dc51a45e8c0423b`.
- Historical AUTO01 `ba1ae9df6603925871a6de788c74eb635019e20f` / tree
  `c5feb0a442bed5172e69cba0f00ddeccce408046` was treated as implementation
  evidence only.
- Work is isolated to `.tmp/p2p-auto01-current-recon-20260829`; current
  canonical checkout, owner worktrees, and remote refs were not modified.

### Overlap and resolution

- The exact old-base delta overlap was only this notes file. The primary
  AUTO01 gateway/workflow paths were unchanged in current canonical, so their
  behavior was carried through existing seams rather than overwritten.
- Current PB01 and 02A commits remain ancestors. AUTO01 retains the existing
  Goal Contract, TaskStateStore, execution ledger, Control Tower, beginner /
  advanced projection, material-question policy, bounded workstreams, real
  dependencies, five-workstream limit, and `automatic_start=false`.
- The only new conflict was PB01 byte idempotency when the runtime hint changed
  from source package to installed project. Repeated identical requests now
  reuse the accepted gateway and refresh only Task State continuity.

### Evidence and stop

- AUTO01 `7/7`, BG01 `8/8`, PB01 `16/16`, and 02A `11/11` plus four subtests
  passed; targeted compile and diff checks passed.
- No Anvien, broad regression, benchmark regeneration, promotion, push,
  deployment, or live activation was run.
- Candidate implementation checkpoint:
  `366c9826200fadbd170e4d07e37fdd10bc3bbdfb` / tree
  `d332b858bf1f68c836f1500f6061906d24034fd0`.
- Candidate evidence checkpoint before closure-note binding:
  `72ac8bb864ff69372324371f3842e18b0967b154` / tree
  `5a12b0de2d4391592dc418fdf5592b0f7b27c633`; base
  `b8d09fc7a0e4a91e75db7f10dc8cfaea007ba37a`.
- Coder report:
  `reports/coder/rp_coder_260829_121800_by_gpt-5-codex_p2p-auto01-current-canonical-reconciliation.md`.
- Independent Supervisor report:
  `reports/supervisor/rp_supervisor_260829_122500_by_gpt-5-codex_p2p-auto01-current-canonical-reconciliation.md`.
- Technical stop is Owner gate only; canonical remains unpromoted.

## P2P-SEC01 current-canonical reconciliation — 2026-08-29

### Authority and isolation

- Fresh official `refs/heads/main` was resolved to
  `bc686845fbb5817e50958d91e0d382a72c219b78` with tree
  `68b16f0fd2116ec6e93bdb9dbecc31429a68ec6d`.
- The old reviewed SEC01 candidate is
  `bb30ca0a343b0902759a1a07a42cc8220c4ac260` with tree
  `63b5093567929f45aad997414a85355c0f434c5d`, based on
  `b8d09fc7a0e4a91e75db7f10dc8cfaea007ba37a`.
- The new candidate is isolated in
  `.tmp/p2p-sec01-current-canonical`; owner/canonical worktrees and the
  existing SEC01 candidate were not modified.

### Overlap and resolution

- The exact overlap between `b8d09fc... -> bb30ca0...` and
  `b8d09fc... -> current main` is only
  `docs/notes_decisions_log/notes_decisions_log_20260829.md`.
- The overlap is append-only documentation. Current AUTO01 content is
  preserved verbatim; the SEC01 reconciliation is appended after it. No
  AUTO01 production/control-plane path is overwritten or reverted.
- The remaining 17 SEC01 paths are carried forward as the coherent SEC01
  delta. No second registry, router, orchestrator, risk engine, truth store,
  or deployment control plane is introduced.

### Preservation and stop boundary

- The optional `SEMANTIC_KIND` model, 12 security/reverse IDs, five EFF01
  execution classes and fail-closed authorization, reverse evidence contract,
  APKiD readonly/dependency-unavailable behavior, canonical `8/8`, and both
  planned extension seams are preserved.
- `AUTO01_PRESERVED=YES`; `SEC01_IMPLEMENTATION_PRESERVED=YES`;
  `MONETIZATION_SEAM_PRESERVED=YES`; `INFRASTRUCTURE_SEAM_PRESERVED=YES`.
- Verification remains the focused SEC01 compatibility ceiling. No broad
  regression, Anvien, Council, full security stack, provider installation,
  monetization test, infrastructure provisioning, promotion, release,
  deployment, or live activation is permitted.
- One fresh candidate will be bound to current main after focused evidence;
  the single existing SEC01 Owner Gate remains required and canonical
  promotion remains false.
