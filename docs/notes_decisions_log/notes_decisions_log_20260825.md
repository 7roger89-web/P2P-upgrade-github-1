# P2P Vendor Skills Reconstruction — 2026-08-25

- Authority: reconstructed only in valid worktree
  `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-vendor-skills-reconstructed-03`,
  branch `codex/p2p-vendor-skills-reconstructed-03`, from
  `557b502758581812a8845355ed6b426ba75372ec` / tree
  `2bd89d97f8877d372f0444218ec9c7339da14d7f`.
- Decision: use the smallest vendor seam. Do not copy the broken snapshot's
  unrelated role, model, profile, config, or C35 changes; keep the broken root
  `.git` read-only.
- Validation: vendor `17/17`, foundation `28/28`, combined `45/45`, C35
  `57/57`, compileall exit `0`, vendor tree hashes unchanged, capability doctor
  PASS with canonical `8/8`.
- Differential: package role mismatch and development governance drift are
  inherited/expected from the clean base. Anvien detect-changes exits `0` under
  unique alias `p2p-vendor-reconstructed-03`, with direct Git diff retained as
  authority for hidden `.p2p` and untracked vendor paths.
- Boundary: no promotion, merge, push, release, deployment, approval execution,
  dependency installation, or external renderer/network operation.
