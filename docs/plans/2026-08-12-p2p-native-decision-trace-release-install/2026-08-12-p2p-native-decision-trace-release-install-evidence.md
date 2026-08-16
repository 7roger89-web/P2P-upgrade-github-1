# P2P Native Decision Trace — Release / Install Integration Evidence Ledger

## Metadata

- Date: `2026-08-12`
- Plan: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-plan.md`
- Evidence: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-evidence.md`
- Benchmark: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-benchmark.md`
- Actual status: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-actual-status.md`

## Evidence Rules

- Actual package/install/runtime evidence is required; source tests alone are
  insufficient for PASS.
- The `.4` ZIP is preserve-only and its SHA-256 is rechecked before and after.
- All lifecycle fixtures and extracted artifacts are under repository-local
  `.tmp`; no real project or user home is touched.
- Historical legacy state is not rewritten or backfilled.
- Developer-only evaluator/tests/reports are evidence tooling, not runtime
  package content.
- Anvien is used for mapping when registered; target registration failure is
  recorded explicitly and replaced with bounded local inspection.
- Evidence IDs are stable and phase-scoped.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-VERSION1`: current `VERSION`, `manifest/package.json`, runtime
  manifest, and build report identify `8.4.7-C-codex.4`; next revision is
  derived as `.5` from the existing policy.
- `E0-P0A-BASELINE1`: verified old artifact exists at
  `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v4.zip` with SHA-256
  `1d1d00913b215e513a2441f194125b96e9e7999a0659ae713d3e10d2de4dcccb`;
  extracted package doctor PASSes.
- `E0-P0A-GAP1`: old `.4` ZIP has no `decision_trace` runtime or CLI member;
  the native development Goal report and source module/wrapper are present.
- `E0-P0A-PACKAGE1`: package builder stages UIUX/Foundation payload but has no
  Decision Trace runtime allowlist entry; its first current build fails the
  package drift gate because developer-only files are locked but intentionally
  excluded from the clean package.
- `E0-P0A-INSTALL1`: both installers copy generic runtime scripts and UIUX/
  Foundation payload but do not copy or require Decision Trace runtime files.
- `E0-P0A-DOCTOR1`: package and installed doctor paths validate UIUX/Foundation
  but do not recognize Decision Trace.
- `E0-P0A-STATE1`: project state outside `.p2p/system` is preserve-only,
  including FACT/Live/eval/approval/Goal/status/CAPSULE/user files and the
  existing `.p2p/state/execution-ledger.jsonl`.
- `E0-P0A-GOV1`: canonical registry remains exact eight, denominator `8`,
  full quorum `8/8`; Aesthetica is optional/noncanonical/non-simulated.
- `E0-P0A-ANVIEN1`: Anvien lists only unrelated `app_game_truyen`; context for
  this target returns `repository path is not registered`. Local source and
  artifact inspection is the bounded fallback; App Game Truyện is not touched.

P0 decision: complete. P1 may edit only the packaging/runtime integration
surfaces listed in the plan; old release and project-state surfaces remain
preserve-only.

## E1 - P1 Evidence — PASS

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-PAYLOAD1`: pending runtime payload implementation and package build.
- `E1-P1A-DOCTOR1`: pending positive/negative package and installed doctor
  evidence for Decision Trace payload presence.
- `E1-P1B-META1`: pending `.5` version metadata consistency evidence.
- `E1-P1B-PACKAGE1`: pending new full ZIP verify/doctor/drift/inventory evidence.

## E2 - P2 Evidence — PASS

Matching plan item(s): `P2-A`, `P2-B`, `P2-C`

- `E2-P2A-INSTALL1`: pending installer provisioning evidence.
- `E2-P2A-IDEMPOTENCE1`: pending same-version reinstall state/backup proof.
- `E2-P2B-FRESH1`: pending fresh install and beginner WHY evidence.
- `E2-P2B-UPGRADE1`: pending legacy upgrade/ledger preservation evidence.
- `E2-P2B-REINSTALL1`: pending post-upgrade same-version reinstall evidence.
- `E2-P2C-TRACE1`: pending installed trace behavior matrix.
- `E2-P2C-REGRESSION1`: pending installed UIUX/Foundation/core regression.

## E3 - P3 Evidence — PASS

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-ARTIFACT1`: pending final release metadata and SHA-256 inventory.
- `E3-P3A-RI1`: pending RI-DT1–RI-DT34 machine-readable certification.
- `E3-P3B-CLOSURE1`: pending final package boundary, old hash, doctor/drift/
  secret, and regression recheck.
- `E3-P3B-NEXT1`: pending one residual-risk-based next Goal or STOP decision.

## E4 - P4 Evidence — PASS

Matching plan item(s): `P4-A`, `P4-B`, `P4-C`

- `E4-P4A-SUP1`: pending independent supervisor report.
- `E4-P4B-CLEAN1`: pending dead-work and `.tmp` cleanup review.
- `E4-P4C-CLOSE1`: pending final plan status, artifact handoff, and exact
  31-section response evidence.

## Closure Evidence

The target is not a Git worktree; commit evidence is `N/A`. Final closure must
contain the new artifact path/version/hash/size/member counts, unchanged old
artifact hash, actual package doctor PASS, fresh/upgrade/reinstall runtime
evidence, installed trace behavior, full regression, drift/secret checks,
supervisor verdict, and exactly one evidence-backed next Goal.

## Final certification refresh

All pending E1–E4 evidence rows are resolved by the actual artifact lifecycle.

- E1: the final ZIP contains the Decision Trace module and CLI; package doctor, manifest, and runtime doctor PASS; release metadata is .5 and the clean package drift gate PASSes.
- E2: PowerShell and Bash/WSL fresh installs PASS; .4 to .5 upgrade preserves protected state and ledger bytes; post-upgrade trace appends only after a real action; same-version reinstall is idempotent.
- E3: final artifact is D:/AI/P2P_dev/P2P-8.4.7-C-Codex-Edition-v5.zip, SHA-256 f88dbf706c4ac85a8aadf38960923cdc8e4ba6e415b83f3f1726692fb3ad8dda, 2,329,263 bytes, 397 content files, 399 ZIP members; old .4 hash is unchanged.
- E4: independent supervisor audit and report PASS; no developer-only payload or out-of-scope project data is in the ZIP; plan closure is ready.
