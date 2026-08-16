# P2P Eval Helper Boundary Alignment — Prerequisite for Real Context-Efficiency Benchmark Plan

## Metadata

- Date: `2026-08-14`
- Status: `complete — independent supervisor PASS; bounded Goal closed`
- Plan: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-actual-status.md`

## Goal

Align the existing P2P eval-helper and package/runtime boundary so project eval v2 has one deterministic helper contract, package doctor checks the role it is actually given, and isolated lifecycle fixtures can prove development, portable, fresh-install, upgrade, and same-version reinstall behavior before a later real context-efficiency benchmark.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Do not modify the official `.15` artifact or prior proxy evidence.
- Do not run or claim the real context-efficiency A/B benchmark in this Goal.
- Do not implement workers, orchestration, Capsule 2.0, Knowledge Delta, scheduler, queue, or a second eval system.
- Preserve the existing project-eval v2 schema and bind new behavior to existing FACT/evidence/governance state.
- Use repo-local `.tmp` only for isolated fixtures; never treat `.tmp`, quarantine, or preserved source snapshots as production helper sources.
- Run Anvien file-detail and impact evidence before editing code; run detect-changes before a commit attempt.
- No Docker/browser validation applies: this is a Python CLI/package boundary change, not a public UI/runtime change. Record that N/A decision in evidence.

## Problem

The current workflow discovers helpers by path order. In the development checkout, the first candidate is `.p2p/system/scripts/p2p_eval.py`, whose contract is a UI/UX evaluator and does not implement project-eval v2 `design`. The workflow therefore sends the wrong CLI contract and blocks during bootstrap. Separately, `scripts/doctor.py --package .` treats the development checkout as an unpacked portable package and reports portable payload paths missing even though the capability/runtime payload exists under development-owned `.p2p/system` paths. The helper and doctor boundaries are not role-aware or self-consistent.

## Scope

- Reproduce the current helper mismatch and doctor failure from runtime commands.
- Map ownership of project eval v2, UI/UX eval, capability foundation, package manifest, installer, and installed doctor.
- Define deterministic helper resolution for development checkout, extracted portable package, and installed project roles.
- Implement the smallest role/contract-aware correction needed to prevent the wrong helper from being selected.
- Make package doctor role-aware or otherwise enforce its documented input contract without weakening fail-closed package checks.
- Add focused regression coverage and isolated lifecycle fixtures for A development checkout, B extracted package, C fresh install, D upgrade from `.15`, and E same-version reinstall where the existing installer/package contract supports them.
- Preserve prior 12-scenario proxy artifacts and report their status separately from real-worker readiness.
- Record whole-repo secret findings as a separate hygiene goal; do not delete or whitelist existing evidence.

## Non-Goals

- No real worker/provider execution or token/cost certification.
- No context-efficiency runtime implementation, Capsule refinement, Knowledge Delta runtime, preflight redesign, execution-budget redesign, mode router, parallel scheduler, worker pool, queue, DAG, leases, daemon, external integration, or App Game Truyện mutation.
- No reopening of AESTHETICA research or canonical identity policy.
- No release promotion, publication, or overwrite of `8.4.7-C-codex.15`.
- No second project-eval or project-memory source of truth.

## Requirements

1. The current failure is reproduced from actual runtime commands and classified with evidence.
2. Every candidate helper has an explicit contract/role check; path order alone cannot select a semantically incompatible helper.
3. Development, portable, and installed ownership are documented and deterministic.
4. Package doctor distinguishes development checkout, portable package, and installed project input, or rejects an invalid role explicitly.
5. Manifest/package/installer paths agree with the selected helper and doctor role.
6. Temporary/quarantine paths are excluded from production resolution and package manifests.
7. Existing proxy artifacts remain unchanged and are not relabeled as real execution.
8. Lifecycle checks use isolated repo-local fixtures and do not mutate the official artifact, baseline, or user projects.
9. Canonical identity count remains 8, denominator 8, full quorum 8/8; Aesthetica remains optional/noncanonical.

## Acceptance Criteria

- [x] EH1 current doctor failure reproduced and original failing checks recorded.
- [x] EH2 root cause identifies the exact helper mismatch and doctor-role mismatch from runtime/source evidence.
- [x] EH3 missing/incorrect payload groups are identified and classified.
- [x] EH4 ownership of development, portable, and installed helpers is explicit.
- [x] EH5 no duplicate eval system is introduced; resolution is deterministic and contract-aware.
- [x] EH6 `.tmp`/quarantine/preserved snapshots are excluded from production helper resolution.
- [x] EH7 package manifest and installer ownership are aligned with the resolver/doctor contract.
- [x] EH8 doctor is role-aware and remains fail-closed for invalid portable packages.
- [x] EH9 prior proxy artifacts remain preserved and correctly labeled.
- [x] EH10 real benchmark readiness is reported YES only if the helper/lifecycle boundary is actually executable; otherwise NO with blocker.
- [x] EH11 development checkout lifecycle check passes.
- [x] EH12 extracted official `.15` package is checked without modification.
- [x] EH13 fresh-install fixture is checked in an isolated root.
- [x] EH14 upgrade-from-`.15` fixture is checked or explicitly blocked by a real installer limitation.
- [x] EH15 same-version reinstall fixture is checked or explicitly blocked by a real installer limitation.
- [x] EH16 path leakage and stale helper selection checks pass.
- [x] EH17 existing suite/eval v2 and governance checks pass.
- [x] EH18 relevant regression tests pass.
- [x] EH19 full package build/verification path is checked where source packaging supports it.
- [x] EH20 whole-repo secret findings are separately reported, with no silent cleanup.
- [x] EH21 canonical identities remain exactly 8; denominator 8; full quorum 8/8.
- [x] EH22 no second source of truth is created.
- [x] EH23 no durable orchestration or new router/meta-agent is created.
- [x] EH24 beginner-facing command burden does not increase.
- [x] EH25 independent supervisor verdict is recorded.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state of helper ownership, doctor assumptions, package contents, and lifecycle tooling.
  - Work Steps: reproduce bootstrap and doctor failures; inspect source/manifest/installer/package artifacts; run Anvien graph evidence for target files; record correct, partial, wrong, missing, unbound, and blocked surfaces.
  - Implementation Gate: no source implementation starts until actual-status has a P0 decision and evidence IDs.
  - Acceptance: actual-status identifies the exact helper mismatch, two missing doctor groups, ownership boundary, and lifecycle feasibility.

### P1: Boundary and ownership map

- Phase Goal: define one truthful source/contract map before editing.
- Phase Boundary:
  - In scope: helper identities, role detection, doctor inputs, package manifest, installer copy rules, and lifecycle fixture entry points.
  - Out of scope: context-efficiency behavior, workers, providers, scheduler, and unrelated secret hygiene.
  - Dependencies: P0-A evidence and existing `.15` artifact hash.
- Phase Implementation Rule: do not implement `P1` directly; complete P1-A and P1-B as inspect-only slices, record evidence, refresh actual-status, then continue.
- Ordered Slice List:
  - P1-A: Map helper contracts and deterministic resolution candidates.
  - P1-B: Map package/installer/doctor role and lifecycle ownership.

- [x] P1-A: Map helper contracts and deterministic resolution candidates
  - Goal: prove which files implement project eval v2 versus UI/UX evaluation and define the safe candidate contract.
  - Scope Boundary:
    - Editable: none; inspect-only.
    - Inspect-only: `scripts/p2p_workflow.py`, `scripts/p2p_eval.py`, `.p2p/system/scripts/p2p_eval.py`, related tests.
    - Preserve-only: existing eval v2 suite, UI/UX evaluator, prior proxy artifacts.
    - Out of scope: renaming or merging helpers.
  - Non-Goals: no runtime optimization and no new evaluator.
  - Pre-flight Questions:
    - Data source: source files and actual `--help` output.
    - Display permission: N/A; no UI.
    - DB read flow: N/A; filesystem/CLI only.
    - DB write flow: N/A; no persistent product data.
    - Render location: N/A; CLI JSON/report output.
    - UI behavior flow: N/A; terminal contract.
    - Docker runtime: N/A; no app runtime.
    - Playwright target: N/A; no browser surface.
    - Behavior test: bootstrap must select a helper that accepts `design`.
    - Cleanup/quarantine: all temporary fixture roots remain under repo `.tmp` and are excluded from candidates.
    - External side effects: none; no network/provider calls.
    - N/A notes: lifecycle source inspection substitutes for UI checks.
  - Work Steps:
    1. Inspect helper source, CLI help, call sites, and tests; record contract fingerprints.
       - UI flow check: N/A — CLI only.
       - DB/data flow check: N/A — no DB.
       - Render location check: N/A — evidence ledger and JSON output.
       - Evidence target: E1-P1A-CONTRACT1..E1-P1A-CONTRACT4.
    2. Define candidate selection invariants and test oracle before implementation.
       - UI flow check: N/A — CLI only.
       - DB/data flow check: N/A — no DB.
       - Render location check: N/A — resolver result.
       - Evidence target: E1-P1A-RESOLVE1..E1-P1A-RESOLVE3.
  - Implementation Gate:
    - Inspect-only; no code edit is allowed in this slice.
    - Record Anvien file-detail/impact evidence for the eventual target files.
  - Acceptance:
    - Source: project eval v2 and UI/UX evaluator are distinct and named.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: incompatible helper cannot be selected for `design`.
    - Cleanup/quarantine: candidate roots exclude `.tmp`, quarantine, and source snapshots.
    - Evidence IDs: E1-P1A-CONTRACT1..E1-P1A-RESOLVE3.
    - Actual-status rows refreshed: helper ownership and resolver.
  - Evidence Targets: source excerpts, `--help` outputs, graph relation counts, resolver acceptance oracle.
  - Actual-status Update: classify helper resolution as wrong/partial and set P2-A implementation boundary.
  - Commit Boundary: no commit; inspect-only.

- [x] P1-B: Map package/installer/doctor role and lifecycle ownership
  - Goal: prove package root, development checkout, and installed project contracts without mutating `.15`.
  - Scope Boundary:
    - Editable: none; inspect-only.
    - Inspect-only: `scripts/doctor.py`, `.p2p/system/scripts/doctor.py`, `scripts/package_release.py`, `install.ps1`, `install.sh`, manifests, packaging tests.
    - Preserve-only: official `.15` ZIP and source release snapshots.
    - Out of scope: installer redesign beyond a missing boundary correction.
  - Non-Goals: no release promotion.
  - Pre-flight Questions:
    - Data source: official ZIP hash, package contents, installer source, manifest.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: isolated temporary fixture only if installer supports it.
    - Render location: doctor JSON and lifecycle report.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: role-appropriate doctor command passes/fails as designed.
    - Cleanup/quarantine: fixture roots are repo-local and disposable; official ZIP is read-only.
    - External side effects: none.
    - N/A notes: no UI and no external service.
  - Work Steps:
    1. Inspect package archive listing, package builder, manifest, and installer copy/backup rules.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: lifecycle evidence ledger.
       - Evidence target: E1-P1B-PACKAGE1..E1-P1B-PACKAGE5.
    2. Run role matrix against development checkout and extracted `.15` package; inspect fresh/upgrade/reinstall entry points.
       - UI flow check: N/A.
       - DB/data flow check: isolated filesystem only.
       - Render location check: doctor/install JSON and report.
       - Evidence target: E1-P1B-LIFECYCLE1..E1-P1B-LIFECYCLE5.
  - Implementation Gate:
    - No edit until source ownership and lifecycle target paths are explicit.
    - Record Anvien file-detail/impact evidence for doctor/package/installer targets.
  - Acceptance:
    - Source: package and installed helper ownership is unambiguous.
    - Runtime/UI: N/A.
    - DB/data: no user project or official artifact mutation.
    - Behavior test: extracted package and development root are not conflated.
    - Cleanup/quarantine: no temporary path enters manifest/resolution.
    - Evidence IDs: E1-P1B-PACKAGE1..E1-P1B-LIFECYCLE5.
    - Actual-status rows refreshed: doctor, manifest, installer, lifecycle.
  - Evidence Targets: archive listing, SHA-256 check, manifest/installer source, doctor results.
  - Actual-status Update: set P2-A/P2-B scope and identify any installer limitation as a blocker rather than hiding it.
  - Commit Boundary: no commit; inspect-only.

### P2: Small boundary correction

- Phase Goal: correct only the proven helper/doctor boundary and add direct regression coverage.
- Phase Boundary:
  - In scope: role/contract-aware resolver, role-aware doctor semantics, package metadata/copy rule only where required, and focused tests.
  - Out of scope: all context-efficiency and orchestration runtime changes.
  - Dependencies: P0 and P1 evidence; Anvien impact before edits.
- Phase Implementation Rule: complete P2-A then P2-B independently; code first, focused tests immediately after each slice, refresh actual-status.
- Ordered Slice List:
  - P2-A: Correct deterministic eval-helper resolution.
  - P2-B: Align doctor/package role checks and lifecycle test entry points.

- [x] P2-A: Correct deterministic eval-helper resolution
  - Goal: prevent a UI/UX helper from satisfying project eval v2 discovery and make failure explicit when no compatible helper exists.
  - Scope Boundary:
    - Editable: `scripts/p2p_workflow.py` and its focused tests only.
    - Inspect-only: helper implementations and manifest unless tests prove a source change is required.
    - Preserve-only: `scripts/p2p_eval.py` project eval v2 interface and `.p2p/system/scripts/p2p_eval.py` UI/UX interface.
    - Out of scope: adding a new router/agent/evaluator.
  - Non-Goals: no hidden fallback and no raw-output/token instrumentation.
  - Pre-flight Questions:
    - Data source: helper CLI contract and role markers.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: workflow JSON/error output.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: bootstrap selects the project eval v2 helper in development and reports a bounded missing-helper error otherwise.
    - Cleanup/quarantine: resolver rejects paths under `.tmp`, quarantine, and preserved source snapshots.
    - External side effects: none.
    - N/A notes: CLI-only change.
  - Work Steps:
    1. Implement the smallest contract-aware candidate filter/role selection.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: resolver result and workflow report.
       - Evidence target: E2-P2A-CODE1.
    2. Run focused helper-resolution/bootstrap tests and record the original failure no longer occurs.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: test output and JSON.
       - Evidence target: E2-P2A-TEST1..E2-P2A-TEST3.
  - Implementation Gate:
    - Run Anvien file-detail and impact for `scripts/p2p_workflow.py` and affected symbols before edit.
    - Keep one canonical project eval v2 helper; do not copy or create a parallel helper.
  - Acceptance:
    - Source: resolver contract is explicit and deterministic.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: the reproduced `unrecognized arguments: design` path is eliminated for the development checkout.
    - Cleanup/quarantine: temporary/snapshot paths are rejected.
    - Evidence IDs: E2-P2A-CODE1..E2-P2A-TEST3.
    - Actual-status rows refreshed: helper resolution.
  - Evidence Targets: diff, focused tests, bootstrap JSON, resolver path classification.
  - Actual-status Update: helper resolution transitions wrong -> correct/blocked with precise residual boundary.
  - Commit Boundary: commit after acceptance when repository version control is available; otherwise record unavailable.

- [x] P2-B: Align doctor/package role checks and lifecycle test entry points
  - Goal: make development, portable, and installed doctor checks truthful and fail closed without hiding missing package payloads.
  - Scope Boundary:
    - Editable: exact doctor/package/installer file(s) proven by P1, plus focused tests.
    - Inspect-only: official `.15` artifact and user project paths.
    - Preserve-only: package payload validation, manifest hash rules, and fail-closed behavior for invalid packages.
    - Out of scope: release promotion or broad security architecture.
  - Non-Goals: no installer feature expansion beyond role/path alignment.
  - Pre-flight Questions:
    - Data source: source/package manifests and role markers.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: isolated fixture only.
    - Render location: doctor/lifecycle reports.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: dev role does not demand portable-only root payload; portable role still demands all payloads.
    - Cleanup/quarantine: fresh/upgrade/reinstall roots under repo `.tmp` only.
    - External side effects: none.
    - N/A notes: package lifecycle is filesystem/CLI behavior.
  - Work Steps:
    1. Implement role-aware doctor/package boundary or correct the existing role invocation, preserving strict portable checks.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: doctor JSON.
       - Evidence target: E2-P2B-CODE1.
    2. Add focused lifecycle fixture assertions for package contents, installer ownership, path leakage, and role-specific doctor result.
       - UI flow check: N/A.
       - DB/data flow check: isolated filesystem state is cleaned/quarantined under `.tmp`.
       - Render location check: lifecycle matrix report.
       - Evidence target: E2-P2B-TEST1..E2-P2B-TEST5.
  - Implementation Gate:
    - Run Anvien file-detail and impact for each exact target before edit.
    - Run code-first focused tests, then package build/verify checks.
  - Acceptance:
    - Source: manifest, installer, doctor, and resolver agree on ownership.
    - Runtime/UI: N/A.
    - DB/data: no protected root mutation.
    - Behavior test: invalid portable package remains FAIL; valid role-specific roots are truthful.
    - Cleanup/quarantine: no fixture or `.tmp` path is packaged/resolved.
    - Evidence IDs: E2-P2B-CODE1..E2-P2B-TEST5.
    - Actual-status rows refreshed: doctor/package/installer.
  - Evidence Targets: code diff, focused tests, package verify output, lifecycle matrix.
  - Actual-status Update: role/doctor boundary transitions partial/wrong -> correct or blocked with exact installer constraint.
  - Commit Boundary: commit after acceptance when repository version control is available; otherwise record unavailable.

### P3: Verification and lifecycle matrix

- Phase Goal: prove the boundary with isolated evidence and preserve the prior proxy artifacts.
- Phase Boundary:
  - In scope: full relevant Python tests, package build/verify, lifecycle A-E, secret scans for changed surfaces, canonical checks, and proxy artifact integrity.
  - Out of scope: real A/B worker benchmark and unrelated whole-repo secret cleanup.
  - Dependencies: P2-A/P2-B.
- Phase Implementation Rule: execute only affected checks; do not start optional benchmark work.
- Ordered Slice List:
  - P3-A: Run regression/package/lifecycle checks.
  - P3-B: Validate evidence integrity and readiness boundary.

- [x] P3-A: Run regression/package/lifecycle checks
  - Goal: execute the required CLI/package validation matrix against isolated roots.
  - Scope Boundary: tests, package verify/build, lifecycle fixtures, governance/decision trace, and secret scans; no code edits unless a mandatory test exposes a scoped defect.
  - Non-Goals: no context-efficiency benchmark.
  - Pre-flight Questions: all UI/DB/Docker/Playwright checks are N/A for this CLI-only scope; cleanup is repo-local `.tmp` quarantine.
  - Work Steps:
    1. Run A development checkout, B extracted `.15`, C fresh install, D upgrade, and E same-version reinstall checks.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: lifecycle JSON/Markdown evidence.
       - Evidence target: E3-P3A-LIFE1..E3-P3A-LIFE5.
    2. Run regression, package verify, governance, decision trace, secret scans, and canonical checks.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: command evidence and reports.
       - Evidence target: E3-P3A-REG1..E3-P3A-REG6.
  - Implementation Gate: no unbounded retry; classify unavailable host/package capability as UNKNOWN/BLOCKED.
  - Acceptance: EH11–EH21 have evidence or a precise blocker.
  - Evidence Targets: test output, package hash, lifecycle report, scans.
  - Actual-status Update: refresh all affected rows.
  - Commit Boundary: final validation boundary; no commit if Git is unavailable.

- [x] P3-B: Validate evidence integrity and readiness boundary
  - Goal: demonstrate that existing proxy evidence remains proxy evidence and decide whether the separate real benchmark can start.
  - Scope Boundary: inspect unchanged prior artifacts, compare hashes/metadata, and write explicit YES/NO readiness result.
  - Non-Goals: no real worker execution.
  - Pre-flight Questions: UI/DB/Docker/Playwright N/A; evidence source is prior proxy suite and new lifecycle reports.
  - Work Steps:
    1. Verify proxy artifacts are preserved and not relabeled.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: artifact metadata and hashes.
       - Evidence target: E3-P3B-PROXY1..E3-P3B-PROXY3.
    2. Produce `REAL_AB_BENCHMARK_READY=YES|NO` with the exact remaining boundary condition.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: final report and supervisor input.
       - Evidence target: E3-P3B-READY1.
  - Implementation Gate: readiness cannot be inferred from proxy byte deltas or model confidence.
  - Acceptance: EH9/EH10 and EH22–EH24 are explicit.
  - Evidence Targets: proxy artifact hashes, readiness decision.
  - Actual-status Update: final current state before supervisor.
  - Commit Boundary: no further implementation after PASS.

- [x] P4-A: Call supervisor for independent acceptance review.
  - Goal: independent review of source, boundary evidence, lifecycle results, and final claims.
  - Work Steps:
    1. Use the supervisor skill to inspect the completed plan, actual status, evidence, benchmark, changed files, tests, and lifecycle matrix.
    2. If rejected, fix only the failed scoped item, rerun affected checks, and repeat review.
  - Implementation Gate: P0–P3 complete or precisely blocked.
  - Acceptance: one explicit PASS/REJECT verdict is recorded; no self-certification.

- [x] P4-B: Close and stop.
  - Goal: record files changed, regression, canonical/security status, release impact, and next Goal without starting it.
  - Work Steps: run final status inspection, record commit unavailability if applicable, update all ledgers, and stop at PASS/BLOCKED/REJECT.
  - Implementation Gate: supervisor verdict exists.
  - Acceptance: no durable orchestration or real benchmark starts after closure.

## Risk Notes

- The development checkout and installed `.p2p/system` currently contain same-named but semantically different `p2p_eval.py` files; an incomplete fix could hide a missing project-eval helper. Fail closed with a clear contract error.
- The official `.15` ZIP is immutable evidence. All extraction/install fixtures must be under this repository's `.tmp` directory.
- The whole-repo secret scan has pre-existing findings outside this Goal's boundary. Report them separately; do not suppress them to obtain a local PASS.
- A valid helper/package boundary does not prove real worker/provider execution or token/cost telemetry. The readiness result must preserve that distinction.
