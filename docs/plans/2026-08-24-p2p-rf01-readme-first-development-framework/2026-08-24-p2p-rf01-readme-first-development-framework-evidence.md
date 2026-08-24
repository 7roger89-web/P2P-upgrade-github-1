# RF01 README-First Project Orientation + Development Framework Revision Evidence Ledger

## Metadata

- Date: `2026-08-24`
- Plan: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-plan.md`
- Evidence: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-evidence.md`
- Benchmark: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-benchmark.md`
- Actual status: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-actual-status.md`

## Evidence Rules

- Evidence is fresh, inspectable, and tied to an exact command, file, hash, test, or commit.
- The sealed `.74` candidate, its branch, and CPT01-R2 are evidence inputs and preserve-only targets.
- A local document or test can prove local implementation behavior; it cannot prove host authority, promotion, canonical status, or independent certification.
- `PASS` is used only for an observed check. Missing, stale, contradictory, or host-limited claims remain `UNKNOWN`, `INCOMPLETE`, `BLOCKED`, or the exact blocker label.
- No release ZIP is built and no promotion action is run in this plan.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: In the recovery Git repository, `git cat-file -t` confirms source commit `4eafc3ccb6de52f2b5f9b9b75b754c9d9a2a9b53` and closure commit `54d15cb02b04a0fea35fb7d2fd0af1fd564bb264` are commits; closure is the direct child of source and `git merge-base --is-ancestor` exits `0`.
- `E0-P0A-SRC2`: Exact sealed `.74` artifact at `.tmp/c74-review2-20260822/reports/candidates/P2P-8.4.7-C-Codex-Edition-v74.zip` hashes to `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`; three local copies match this SHA-256.
- `E0-P0A-SRC3`: New editable worktree `.tmp/p2p-post74-development-01` is on branch `codex/p2p-post74-development-01` at `54d15cb02b04a0fea35fb7d2fd0af1fd564bb264` with no tracked or untracked implementation changes before P0 plan creation.
- `E0-P0A-GIT1`: Source-to-closure diff contains lifecycle/governance/evidence and sealed candidate material only; no product implementation change was imported into the RF01 base.
- `E0-P0A-GR1`: `anvien analyze --force` from the RF01 worktree: 864 files scanned, 160 parsed code files, 0 parse failures, 36,692 graph nodes, 42,410 relationships; graph is at the exact closure commit and not stale.
- `E0-P0A-GR2`: `anvien file-detail scripts/p2p_workflow.py` reports 301 symbols, 43 inbound refs, 156 local relationships, 48 linked flows, 1,344 unresolved references, HIGH risk; `anvien impact file` identifies 38 impacted symbols and affected process data. This file is preserve-only.
- `E0-P0A-GR3`: `anvien file-detail scripts/p2p_development_control.py` reports 151 symbols, 1 inbound ref, 120 local relationships, 17 linked flows, 703 unresolved references, HIGH risk. This file is preserve-only.
- `E0-P0A-GR4`: `anvien file-detail scripts/package_release.py` reports 92 symbols, 1 inbound ref, 36 local relationships, 7 linked flows, 430 unresolved references, HIGH risk; impact identifies 13 impacted symbols and two affected process records. P1-C is list-only.
- `E0-P0A-GR5`: `anvien file-detail install.ps1` and `install.sh` report parsed shell surfaces with zero symbols, zero inbound/outbound relationships, and LOW risk; existing installer behavior is inspect-only/preserve except the explicit helper list entry.
- `E0-P0A-SPEC1`: Full relevant SPEC cluster read: foundation architecture, execution evidence, routing/readiness, trust/data-instruction, and decision trace. These confirm single-router, no second authority/certification, evidence discipline, explicit UNKNOWN, standard-library/local boundary, and no new platform.
- `E0-P0A-DOC1`: Existing charter/framework/governance docs are present and partial for RF01; root `README.md` and orientation helper are missing. Historical `source/8.4.6-C/README.md` and `README.en.md` are present but preserve-only.
- `E0-P0A-WF1`: Read-only `scripts/p2p_workflow.py ... inspect --json` identifies the target as an automation project with P2P installed/policy present and no existing project profile/eval; no Goal state was created or mutated.
- `E0-P0A-AUTH1`: Current `governance/development-control.json` preserves official baseline `.19` and its SHA, current `.74` unpromoted lineage-repair candidate binding, and existing validator-compatible C-line status. RF01 must be an additive noncanonical development-plane projection, not a replacement.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`, `P1-C`

Implementation evidence will be appended with exact IDs after each slice:

- `E1-P1A-ORIENT1..E1-P1A-TEST4`: helper behavior, README projection, marker safety, and focused tests.
- `E1-P1B-DOC1..E1-P1B-TEST3`: charter/framework/governance projection, JSON preservation, and framework/charter checks.
- `E1-P1C-PKG1..E1-P1C-INSTALL3`: package allowlist and installer-preservation checks without a release build or install.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`, `P2-C`

Closure evidence will be appended with exact IDs after verification:

- `E2-P2A-TEST1..E2-P2A-IMMUTABLE3`: focused tests, framework validation, syntax/diff checks, and sealed subject rechecks.
- `E2-P2A-ANV1..E2-P2A-DETECT1`: final Anvien graph and detect-changes evidence.
- `E2-P2B-SUP1`: supervisor review report and verdict.
- `E2-P2C-CLOSE1..E2-P2C-CLOSE3`: final worktree, commit, report, and terminal boundary evidence.

## Closure Evidence

Pending until P1/P2 implementation and supervisor review. No release artifact, promotion mutation, host configuration mutation, or external communication is authorized by this plan.
