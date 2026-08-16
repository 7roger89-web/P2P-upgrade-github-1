# P2P reusable release packaging Evidence Ledger

## Metadata

- Date: `2026-08-10`
- Plan: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-actual-status.md`

## Evidence Rules

- The previous Goal/workflow PASS is trusted and preserve-only.
- Package acceptance must use the real supported packaging and installer paths.
- Project state is compared by explicit snapshots/hashes; templates never replace it.
- Safe fixtures prove packaging/install behavior only, not real project quality or live eight-thread runtime.
- Anvien target registration is unavailable; local source and runtime evidence is documented as fallback.
- No Git metadata exists; no commit is claimed.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-META1`: `VERSION` and `manifest/package.json` both identify `8.4.6-C-codex.4`; no newer release metadata exists. Existing convention supports a `.5` increment for this verified development build.
- `E0-P0A-PKG1`: `scripts/package.ps1` and `scripts/package.sh` archive the entire root, so `.tmp`, reports, plans, experimental scratch, and transient files would ship.
- `E0-P0A-INSTALL1`: installers back up `.p2p/system`, skills, agents, config, and instructions, but do not record package release identity or explicitly classify fresh/same-version/upgrade/already-initialized state.
- `E0-P0A-STATE1`: existing project state is outside `.p2p/system` and must remain preserve-only: project policy, eval, approvals, gates, Goal/status/capsule, trusted evidence, and Execution Ledger.
- `E0-P0A-ANV1`: Anvien lists only unrelated `app_game_truyen`; target package path is not registered, so query/detect-changes graph evidence is unavailable.
- `E0-P0A-PASS1`: current package doctor, drift, regression, Goal acceptance, and eight-agent/source inventory are trusted preserve-only evidence from the completed Goal refinement.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-META1`: `VERSION`, `manifest/package.json`, and `manifest/build-report.json` now agree on `8.4.6-C-codex.5`; the existing `.4` convention was incremented without changing the upstream `8.4.6-C` baseline.
- `E1-P1A-DOC1`: `RELEASE-NOTES.md`, `BAT-DAU.md`, and `docs/AI-HANDOFF.md` now describe the reusable release and beginner natural-language workflow; manifest exposes `release_notes` and `release_builder`.
- `E1-P1B-CODE1`: `scripts/package_release.py` defines an explicit reusable-content allowlist, forbidden transient/project-state fragments, release manifest, checksum inventory, extracted-package verification, and package doctor/drift gates.
- `E1-P1B-CODE2`: `scripts/package.ps1` and `scripts/package.sh` now delegate to the shared integrity-checked builder; `governance/drift-policy.json` excludes development plans/reports from protected package-lock contents so clean releases can omit them safely.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-INSTALL1`: `install.ps1` and `install.sh` read `VERSION`, classify
  `FRESH_INSTALL`, `ALREADY_INITIALIZED_PROJECT`, `LEGACY_SYSTEM_UPGRADE`,
  `UPGRADE_FROM_<version>`, and `SAME_VERSION_REINSTALL`, keep system backups,
  preserve project state outside `.p2p/system`, and write `release.json` only
  after doctor PASS.
- `E2-P2A-INSTALL2`: the existing-project fixture carried a seeded supported
  `8.4.6-C-codex.4` marker plus project FACT_LEDGER/Live Specs fixture files,
  policy, eval suite, approvals, Execution Ledger, CAPSULE, status, Goal, and
  trusted evidence. The upgrade preserved every protected file hash, installed
  the new workflow helper, and left one active governance tree.
- `E2-P2B-FRESH1`: final artifact PowerShell fixture installed cleanly as
  `FRESH_INSTALL`; the exact beginner request classified as `PLAN FIRST`, then
  the installed workflow initialized project state, Goal/eval/CAPSULE/ledger
  paths, and returned terminal `PASS`.
- `E2-P2B-UPGRADE1`: final artifact upgraded the supported fixture as
  `UPGRADE_FROM_8.4.6-C-codex.4`; state hashes remained identical, the new
  system helper was present, `project_eval` evidence was reused, and only the
  affected `drift_gate` was scheduled for rerun.
- `E2-P2B-REINSTALL1`: the same final artifact returned
  `SAME_VERSION_REINSTALL`; project state remained byte-for-byte unchanged,
  active agents/skills/governance were not duplicated, doctor PASSed, and drift
  PASSed.
- `E2-P2B-SHELL1`: WSL/Bash executed the packaged `install.sh` fresh path and
  completed install, package doctor, and installed drift with PASS.

## Closure Evidence

- Final artifact: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v5.zip`.
- Final version: `8.4.6-C-codex.5`.
- Final artifact SHA-256: `0c5db0f90480c4668db9bf1c2a7226e86b039bc10281e93619e193ea6e0be44b`.
- Final artifact size: `2,217,368` bytes; `342` content files; `343` checksum
  entries; `344` archive entries including release metadata.
- `package_release.py verify`, package doctor, extracted drift, root doctor, and
  root drift all PASS; archive exclusions and secret scan PASS.
- Regression discovery: `19/19 PASS`; no Goal implementation files changed.
- No Git metadata exists; no commit or external publication is claimed.
- Anvien is not available for this local package path; local runtime/artifact
  evidence is the explicit fallback.
- Supervisor report `reports/supervisor/rp_supervisor_260810_174000_by_gpt-5-codex_p2p-release-packaging.md` independently reviewed the source, final ZIP, fresh extraction, installer fixtures, doctor, drift, exclusion scan, and 19-test regression suite: `PASS`.
