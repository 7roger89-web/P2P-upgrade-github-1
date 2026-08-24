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

- `E1-P1A-ORIENT1`: `scripts/p2p_orientation.py` implements explicit-content marker rendering, exact slice replacement, append-on-absent, idempotence, UTF-8 handling, and fail-closed ambiguity checks.
- `E1-P1A-ORIENT2`: `README.md` has exactly one begin/end marker pair, 132 lines, required `.19`/`.74`/host-blocked state, task-to-files routing, deep links, and the exact report disclaimer.
- `E1-P1A-TEST1`: focused unittest command `python -m unittest discover -s tests -p "test_p2p_orientation.py" -v` passed 7/7 tests.
- `E1-P1A-TEST2`: tests prove CRLF/LF owner-prefix/suffix byte preservation, no-write on malformed markers, and second-update idempotence using quarantine fixtures under the worktree `.tmp`.
- `E1-P1A-COMMIT1`: slice commit `579a711643415fee87647be278cc40fe098e35f0` contains exactly `README.md`, `scripts/p2p_orientation.py`, and `tests/test_p2p_orientation.py`.
- `E1-P1B-DOC1`: charter §5A, product architecture RF01 boundary, and master roadmap RF01 section now distinguish PRODUCT FAST LOOP from ASSURANCE / RELEASE LOOP, record lifecycle states, OXP, measurable human outcome, risk-proportional assurance, one-capable-agent-first execution, and anti-overengineering limits.
- `E1-P1B-GOV1`: `governance/development-control.json` parses and contains an additive `development_plane` for RF01; existing `current_development`, `.19`, `.74`, and C-line fields remain untouched.
- `E1-P1B-GOV2`: scoped assertions pass for RF01 goal/status, exact `.19` baseline, exact `.74` artifact SHA, CPT01-R2 blocker, and exact report disclaimer.
- `E1-P1B-ANV1`: after target-only generated-index recovery (`anvien clean --force` on this worktree only), fresh `anvien analyze --force` reports 871 files, 162 parsed code files, 0 failures, 36,994 nodes, and 42,767 relationships.
- `E1-P1B-GR1`: fresh `anvien file-detail governance/development-control.json` reports 2 inbound references, low risk, parsed, no unresolved references; impact reports no affected upstream files/processes.
- `E1-P1B-DETECT1`: fresh `anvien detect-changes --repo <RF01 worktree> --scope all` reports 4 changed files, 3 affected doc files, low risk, no affected processes, and no resolution-gap delta.
- `E1-P1B-SCOPE1`: `git diff --cached --name-only` before the P1-B commit is exactly the three intended framework/charter documents plus `governance/development-control.json`.
- `E1-P1B-BASELINE1`: full framework validator and full `tests/test_p2p_development_charter.py` remain blocked by the pre-existing capability ledger: parent commit `f92264b` already has `capabilities[175]` with legacy `id`/missing `capability_id`; current baseline also contains `SHIPPED` outside the allowed status vocabulary and roadmap count drift. RF01 does not edit that ledger.
- `E1-P1C-PKG1`: `scripts/package_release.py` now includes `README.md` in `ROOT_FILES` and `scripts/p2p_orientation.py` in `SCRIPT_FILES`; the edits are list-only.
- `E1-P1C-PKG2`: `tests/test_p2p_orientation_packaging.py::test_package_allowlists_include_readme_and_helper` passes; the package builder was not executed and no release artifact was generated.
- `E1-P1C-INSTALL1`: `install.ps1` and `install.sh` now copy `p2p_orientation.py` through their existing system-script lists.
- `E1-P1C-INSTALL2`: `tests/test_p2p_orientation_packaging.py::test_installers_copy_helper_but_do_not_write_project_readme` passes; static scan finds no installer README write path.
- `E1-P1C-INSTALL3`: focused orientation/packaging tests pass 9/9; Python compile, PowerShell AST parse, LF-normalized `bash -n`, and `git diff --check` pass. Raw `bash -n` on the Windows `core.autocrlf=true` working copy is not treated as source failure because the normalized content and HEAD blob parse successfully.
- `E1-P1C-ANV1`: fresh target-only `anvien analyze --force` reports 872 scanned files, 163 parsed code files, 0 failures, 37,029 graph nodes, and 42,804 relationships.
- `E1-P1C-GR1`: refreshed `anvien file-detail` for `scripts/package_release.py` reports 92 symbols, 1 inbound reference, 36 local relationships, 7 linked flows, 430 unresolved references, HIGH risk; impact reports 13 impacted symbols and two affected process records. The change remains list-only.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`, `P2-C`

Closure evidence will be appended with exact IDs after verification:

- `E2-P2A-TEST1..E2-P2A-IMMUTABLE3`: focused tests, framework validation, syntax/diff checks, and sealed subject rechecks.
- `E2-P2A-ANV1..E2-P2A-DETECT1`: final Anvien graph and detect-changes evidence.
- `E2-P2B-SUP1`: supervisor review report and verdict.
- `E2-P2C-CLOSE1..E2-P2C-CLOSE3`: final worktree, commit, report, and terminal boundary evidence.

## Closure Evidence

Pending until P1/P2 implementation and supervisor review. No release artifact, promotion mutation, host configuration mutation, or external communication is authorized by this plan.
