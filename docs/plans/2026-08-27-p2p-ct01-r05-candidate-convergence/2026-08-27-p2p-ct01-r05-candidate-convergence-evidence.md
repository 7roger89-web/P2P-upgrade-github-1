# P2P-CT01 R05 Durable Control Tower Candidate Convergence Evidence Ledger

## Metadata

- Date: 2026-08-27
- Plan: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-plan.md
- Evidence: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-evidence.md
- Benchmark: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-benchmark.md
- Actual status: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-actual-status.md

## Evidence Rules

Evidence IDs are stable and phase-scoped. Each claim below names its command,
source, or exact Git object basis. Fresh candidate results will be appended
without rewriting historical A/B evidence. A report claim is not treated as
proof unless the underlying command or file evidence is recorded.

## E0 - P0 Evidence

Matching plan item(s): P0-A

- E0-P0A-AUTH1: fresh ls-remote for origin refs/heads/main resolves to
  28a3ecd9c04d36511269e44c384bff6e11677b93.
- E0-P0A-AUTH2: canonical main tree is
  cae63e055edd164fbd969f6dbae0d992a4d0efed.
- E0-P0A-AUTH3: origin URL is
  https://github.com/7roger89-web/P2P-upgrade-github-1.git.
- E0-P0A-AUTH4: existing execution ledger and governance verifier are present
  in the valid repository; no new authority path is required.
- E0-P0A-AUTH5: user contract explicitly forbids promotion, deployment, live
  runtime action, approval inheritance, and second truth stores.
- E0-P0A-ISO1: R05 candidate worktree is
  D:\AI\P2P_dev\P2P-canonical-runtime-01\.tmp\ct-r05-convergence-7c3d1a92.
- E0-P0A-ISO2: R05 branch is
  codex/p2p-ct01-r05-candidate-convergence-7c3d1a92 and started at A with
  zero status rows before this plan.
- E0-P0A-A1: Subject A exact SHA/tree:
  f479cc97b31f62f0d006e8465b26ef568e242998 /
  edab113b058478fee4fdd253eec254c18b1e342b.
- E0-P0A-A2: A parent is eedf16cc8bec89200656768e60cb9de0c1a579ad and A's
  merge-base delta contains the durable source, CLI, durable test, docs, and
  governance lock changes.
- E0-P0A-A3: A durable test has nine top-level cases covering packet round
  trip, existing-ledger replay, idempotency, binding/host boundaries,
  waiting/failed preservation, CLI smoke, TaskState, and next-safe-task.
- E0-P0A-A4: existing session-handoff test has 26 top-level cases covering
  attachments, rotation, Owner Gate, recursive continuation, and fail-closed
  behavior.
- E0-P0A-A5: A source docstring and inspected symbols state no host launch,
  provider selection, chat inheritance, canonical truth, approval, or transfer
  authority; only the existing execution ledger is written.
- E0-P0A-A6: Subject A reported 37/37 focused CT tests, attachment 7/7,
  rotation 6/6, CLI smoke, compile, P2P eval, and development-control; all
  must be freshly re-run on the final candidate.
- E0-P0A-B1: Subject B exact SHA/tree:
  9086ca4be9874fb256195d26655022907665208f /
  91d1b467483fdb65b87d9459d3792a5253cdae68.
- E0-P0A-B2: B parent is 03954ea339e4775bafe22ce80f0e6f42ccaaba1d and B adds
  governance plan/evidence/benchmark/status docs, drift policy, runtime lock,
  and the governance reconciliation test.
- E0-P0A-B3: B lock contains 1180 protected files and 2 virtual hashes,
  including the hidden module hash and exact handoff guide hash.
- E0-P0A-B4: A/B path comparison shows B deletes A's durable module/CLI/test
  while adding only its governance test and governance artifacts in that
  slice; B does not contain A's functional superset.
- E0-P0A-REL1: merge base is
  57c4cfc2fd3bbad2c52e40b66be730aeb7ff7f47.
- E0-P0A-REL2: git rev-list --left-right --count A...B is 3 3.
- E0-P0A-REL3: neither A is an ancestor of B nor B an ancestor of A;
  exact relation is DIVERGED.
- E0-P0A-MAT1: base-to-A diff has 13 paths, 1706 insertions, and 14
  deletions, including A's source/CLI/durable test and governance lock.
- E0-P0A-MAT2: base-to-B diff has 7 paths, 783 insertions, and 8 deletions,
  including the exact governance test and policy/lock.
- E0-P0A-MAT3: A-to-B diff has 19 paths, with A-only durable source/CLI/test
  deleted and B-only governance test/plans added.
- E0-P0A-MAT4: B policy differs from A only by adding the hidden module to
  package_protected_paths and installed_protected_paths.
- E0-P0A-L1: A runtime lock has 1180 protected files and 2 virtual hashes but
  does not cover all A-added protected source/CLI state.
- E0-P0A-L2: existing p2p_governance runtime_manifest selects package versus
  installed protected paths and verify_runtime_manifest fails on missing,
  added, changed, or virtual-hash drift.
- E0-P0A-L3: B runtime lock is generated through the same mechanism and
  covers the hidden module but not A's missing functionality.
- E0-P0A-GR1: refreshed Anvien context indexes scripts/p2p_control_tower.py
  with 18 symbols, 3 local relationships, 0 inbound/outbound, stale=false,
  and high unresolved-reference count.
- E0-P0A-GR2: refreshed Anvien context does not find the hidden handoff module;
  direct file/Git inspection is therefore required for that file.
- E0-P0A-GR3: refreshed Anvien context for scripts/p2p_governance.py identifies
  the existing high-risk governance generator/verifier and its consumers.
- E0-P0A-GR4: an Anvien analyze --force refresh completed with 969 files
  scanned, 173 parsed code files, 596 documents, 190 metadata records,
  40585 graph nodes, and 46925 relationships.
- E0-P0A-TEST1: existing session-handoff test is preserve-only and candidate
  validation target.
- E0-P0A-TEST2: A durable test is A-only and candidate validation target.
- E0-P0A-TEST3: B governance test is B-only before porting; it will not be
  executed in the B worktree.
- E0-P0A-GATE1: A has explicit READY_FOR_OWNER_GATE versus PROMOTED
  separation.
- E0-P0A-GATE2: no approval or credential inheritance is present in the
  inspected A source.
- E0-P0A-GATE3: user contract forbids any promotion, deployment, or live
  action in this session.
- E0-P0A-LOCUS1: original user cwd is the historical broken Locus B root and
  is not the valid Git authority.
- E0-P0A-LOCUS2: prior evidence explicitly forbids Git repair, initialization,
  copying .git, Subject B tests, and second truth stores there.
- E0-P0A-LOCUS3: all R05 mutation is isolated under the valid repository's
  .tmp directory.
- E0-P0A-SPEC1: dedicated P2P-CONTROL-TOWER-SESSION-HANDOFF-SPEC.md is absent
  from the valid repository at the searched locations.
- E0-P0A-SPEC2: present Decision Trace, Capability Execution Evidence,
  Capability Manifest, Trust/Data/Instruction, and Routing/Readiness specs
  define the existing authority and UNKNOWN boundaries.
- E0-P0A-SPEC3: the current user contract is the authoritative R05-specific
  handoff contract; no invented replacement SPEC is added.
- E0-P0A-NOISE1: canonical checkout reports 1127 status rows caused by
  EOL/stat-cache behavior, while raw content path diff is empty.
- E0-P0A-NOISE2: semantic diff ignoring space-at-EOL is empty; this noise is
  preserved and not treated as candidate content drift.

## E1 - P1 Evidence

Matching plan item(s): P1-A, P1-B, P1-C

P1-A completed before P1-B:

- E1-P1A-GOV1: Python JSON parse and assertions returned
  policy-json=PASS exact-package-installed=PASS no-broad-whitelist=PASS.
- E1-P1A-GOV2: direct diff shows exactly two additions, one in
  package_protected_paths and one in installed_protected_paths; no broad
  .p2p/system or capability-directory entry was added.
- E1-P1A-GOV3: the path
  .p2p/system/p2p_capabilities/control_tower_handoff.py occurs exactly once
  in each required array.
- E1-P1A-STATUS1: after the policy patch, Anvien analyze --force refreshed
  975 files, 174 parsed code files, 40724 graph nodes, and 47088
  relationships. detect_changes with the exact candidate path reported one
  changed file, governance/drift-policy.json, low risk, zero affected files,
  and no changed symbols.
- E1-P1B-TEST1: pending candidate governance test add.
- E1-P1B-TEST2: pending candidate test compile.
- E1-P1B-TEST3: pending isolated fixture review.
- E1-P1C-LOCK1: pending existing lock-runtime command.
- E1-P1C-LOCK2: pending generated lock inventory and hidden-module hash.
- E1-P1C-LOCK3: pending verifier output.

## E2 - P2 Evidence

Matching plan item(s): P2-A, P2-B, P2-C, Pn-A, Pn-B, Pn-C

Pending until the final candidate is sealed.

- E2-P2A-TEST1: pending focused CT suite.
- E2-P2A-TEST2: pending attachment results.
- E2-P2A-TEST3: pending rotation results.
- E2-P2A-TEST4: pending CLI smoke and compile.
- E2-P2A-TEST5: pending P2P eval where applicable.
- E2-P2A-TEST6: pending development-control.
- E2-P2A-TEST7: pending governance drift and doctor.
- E2-P2A-TEST8: pending report/changed-path inventory.
- E2-P2B-BASE1: pending fresh baseline validator.
- E2-P2B-BASE2: pending fresh candidate validator.
- E2-P2B-BASE3: pending exit-code/count comparison.
- E2-P2B-ATTR1: pending four-way failure attribution.
- E2-P2B-ATTR2: pending terminal-state recommendation.
- E2-P2C-FAIL1: pending fail-closed mutation proofs.
- E2-P2C-DIFF1: pending final changed-path inventory.
- E2-P2C-DIFF2: pending no-promotion/no-live-action proof.
- E2-P2C-SEAL1: pending Anvien detect-changes.
- E2-P2C-SEAL2: pending implementation SHA/tree.
- E2-P2C-SEAL3: pending implementation commit status.
- E2-P2C-CLOSURE1: pending coder and Supervisor reports.
- E2-P2C-HANDOFF1: pending durable handoff creation.
- E2-P2C-HANDOFF2: pending handoff SHA256 and manifest.
- E2-P2C-HANDOFF3: pending packet completeness inspection.

## Closure Evidence

Pending. This section will record:

- implementation commit SHA/tree;
- evidence closure commit SHA/tree;
- final detect-changes and worktree state;
- Supervisor report and exact verdict;
- handoff filename, local path, SHA256, packet completeness, and upload
  decision.
