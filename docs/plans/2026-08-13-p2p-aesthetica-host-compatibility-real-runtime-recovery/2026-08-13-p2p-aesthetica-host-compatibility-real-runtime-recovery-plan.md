# P2P Aesthetica Host Compatibility and Real Runtime Recovery Plan

## Metadata

- Date: `2026-08-13`
- Status: `complete`
- Plan: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-plan.md`
- Evidence: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-evidence.md`
- Benchmark: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-benchmark.md`
- Actual status: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-actual-status.md`

## Goal

Recover and certify the real host path for the optional supporting `p2p_aesthetica` custom agent, starting from the verified `8.4.7-C-codex.6` baseline, while preserving the exact canonical eight-agent 8/8 governance contract.

## Rules

- Complete P0 actual status before implementation.
- Reproduce schema, project-trust, and Windows-sandbox failures independently; do not conflate them.
- Use only official Codex custom-agent schema and supported native Windows sandbox modes.
- Do not edit user projects, App Game Truyen, Logistics, the v5 artifact, or the verified `.6` artifact.
- A real child thread with host-selected profile provenance is required for identity PASS; profile text, prompt role-play, or metadata is not proof.
- `p2p_aesthetica` remains supporting/optional and excluded from canonical denominator.
- Do not use full-access/bypass modes or auto-trust arbitrary projects.
- Use narrow implementation slices, direct behavior tests, and fresh runtime evidence.

## Problem

The `.6` source contains an Aesthetica profile that uses the legacy `instructions` key rather than the current `developer_instructions` key, and the P2P readiness adapter currently promotes profile resolution to `EXECUTABLE` even when no actual child execution has been verified. The host also reports that the exact project `.codex` layer is disabled by trust policy and that the native Windows sandbox helper cannot launch with `Access is denied`. The previous Goal stopped honestly before claiming identity.

## Scope

- P2P development source at `D:/AI/P2P_dev/P2P-8.4.6-C-Codex-Edition-v4`.
- Official profile-schema compatibility for Aesthetica and the package/installed foundation checks that consume it.
- Readiness semantics needed to distinguish `RESOLVED`, `EXECUTABLE`, and `HEALTHY` honestly.
- Isolated, read-only host compatibility probes and real normal subagent delegation by name/instruction.
- Fresh package candidate only if shipped P2P files change.

## Non-Goals

- No new agent, specialist, router, quorum semantics, provider, dependency, Anvien/Semantica/Brigade integration, Code-Impact, UIUX redesign, Decision Trace redesign, discovery fix, or user-project install.
- No trust bypass, arbitrary auto-trust, sandbox bypass, full-access mode, or simulated Aesthetica identity.
- No modification of the verified `.6` ZIP or v5 artifact.

## Requirements

- Baseline: `8.4.7-C-codex.6`, artifact SHA-256 `b8689fb812a438f379fc1d84353f2e4e4c9c0c234c1e22539b2bc32fd15b8156`.
- Official custom agent fields: `name`, `description`, `developer_instructions`; supported `sandbox_mode = "read-only"`.
- Native Windows modes: try preferred `elevated`, then supported `unelevated`; never `danger-full-access`.
- Real execution evidence must show a child thread, host-selected `p2p_aesthetica`, identity-safe output, and UI/UX-only boundary.
- Backend/database requests must not invoke Aesthetica; unavailable identity must fail closed.
- Canonical identities and denominator stay exactly 8 and 8/8.

## Acceptance Criteria

- HC1–HC3: schema, trust, and sandbox blockers independently reproduced and root-caused.
- HC4–HC6: only minimal compatible P2P source changes; all profiles audited; readiness semantics are honest.
- HC7–HC10: source/package/install/config discovery and beginner/UI routing pass without simulation.
- HC11–HC14: real child identity/domain-boundary tests, multiple-thread identity stability, and fail-closed behavior pass; or supported host blocker is recorded.
- HC15–HC18: canonical 8/8, security/no bypass, regression, and packaging/install checks pass when applicable.

## Checklist

- [x] P0-A: complete actual-status baseline and reproduce each independent blocker.
  - Goal: establish current source, package, host config, trust, and sandbox reality before edits.
  - Acceptance: actual-status has stable evidence IDs and a final P0 decision.

### P1: Minimal source compatibility and readiness semantics

- Phase Goal: make the shipped profile and P2P readiness adapter match the official host contract without expanding scope.
- Phase Boundary:
  - In scope: Aesthetica TOML, profile validation, readiness projection, package doctor, direct tests.
  - Out of scope: host trust settings, Codex binaries, user projects, routing redesign.
  - Dependencies: P0 complete; Anvien file/impact evidence before code edits.
- Ordered Slice List:
  - P1-A: migrate Aesthetica profile and validators to official schema.
  - P1-B: require actual execution evidence for `EXECUTABLE`/`HEALTHY` projection.

- [x] P1-A: migrate Aesthetica profile and validators to the official schema.
  - Goal: replace the legacy field and remove the doctor warning while preserving the specialist boundary.
  - Scope Boundary: edit only profile/validators/package checks and their direct tests; preserve registry and router authority.
  - Pre-flight Questions: confirm profile source-of-truth, package copy path, exact validator consumers, and no user-project target.
  - Work Steps: inspect Anvien file/impact; edit source; run TOML/doctor/unit tests; record evidence and refresh actual status.
  - Implementation Gate: P0 complete and Anvien impact recorded.
  - Acceptance: all P2P profiles parse; Aesthetica has current keys and read-only sandbox; package/installed doctors pass their schema checks.
  - Evidence Targets: E1-P1A-SCHEMA, E1-P1A-IMPACT, E1-P1A-TEST.
  - Commit Boundary: no Git repository; record `N/A` checkpoint.

- [x] P1-B: make readiness execution-aware.
  - Goal: profile resolution alone cannot report `EXECUTABLE` or `HEALTHY`.
  - Scope Boundary: specialist validator, foundation doctor/router projection, direct tests only.
  - Work Steps: define the smallest backward-compatible `execute_verified` projection; test false/true paths; verify fail-closed unavailable behavior.
  - Implementation Gate: P1-A passes and the readiness impact is recorded.
  - Acceptance: `execute_verified=False` ends before `EXECUTABLE`; only bounded real execution evidence can promote it.
  - Evidence Targets: E1-P1B-READINESS, E1-P1B-TEST.
  - Commit Boundary: no Git repository; record `N/A` checkpoint.

### P2: Source/package/install and regression validation

- [x] P2-A: rebuild an isolated candidate and validate package/install boundaries.
  - Goal: prove the changed shipped files are present without touching `.6` or v5.
  - Acceptance: package doctor, install, upgrade, reinstall, secret/redaction, and drift checks pass; package-boundary paths contain no developer-only required references.
- [x] P2-B: run routing, beginner, canonical, trust, Decision Trace, temporal, supersession, contradiction, and reverse-lookup regression checks.
  - Goal: prove no adjacent behavior changed.
  - Acceptance: direct regression matrix passes; Aesthetica remains noncanonical and no provider is installed.

### P3: Real host execution certification

- [x] P3-A: perform legitimate trusted isolated project activation and normal subagent delegation.
  - Goal: obtain real child-thread provenance for `p2p_aesthetica`.
  - Acceptance: host-selected profile, child thread, identity-safe bounded UI/UX result, multiple-thread stability, backend negative route, and fail-closed unavailable profile pass.
- [x] P3-B: retest both supported native Windows modes and classify the host result.
  - Acceptance: both modes completed bounded read-only child execution; no bypass or simulated identity was used.

### Closure

- [x] Pn-A: supervisor reviews source, evidence, reports, artifacts, and scope.
- [x] Pn-B: preserve recoverable diagnostic evidence and immutable superseded candidates.
- [x] Pn-C: finalize evidence, benchmark, actual status, release metadata, and the exact 25-section final response.

## Final Decision

`PASS`. The official host-schema defect, P2P readiness false-positive, and the
packaged PowerShell doctor compatibility defect were fixed minimally. Native
`elevated` and `unelevated` read-only probes both produced host-selected
`p2p_aesthetica` child-thread identity evidence. The final release is
`8.4.7-C-codex.9`; the verified `.6`, v5 artifact, and user projects were not
modified.

## Risk Notes

- The exact project trust setting is a host security boundary and must not be silently edited.
- Native Windows sandbox setup may be blocked by administrator policy or logon rights; supported elevated/unelevated evidence decides whether the blocker is environmental.
- A generic subagent response without host-selected profile provenance is not identity evidence.
- Existing P2P tests and reports may contain historical `.6` assumptions; every current PASS claim must use fresh evidence.
