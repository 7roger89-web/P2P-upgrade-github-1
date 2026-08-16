# P2P reusable release packaging Actual Status

Title: P2P reusable release packaging
Date: 2026-08-10
Status: COMPLETE — supervisor PASS
Companion plan: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-plan.md`
Companion evidence: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-evidence.md`
Companion benchmark: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-benchmark.md`

## Purpose

This is the current-state record after release packaging and installer acceptance. The
completed Goal subsystem and existing P2P governance/workflow remain trusted and
preserve-only.

## Freshness / Refresh Rules

Refresh affected rows after each packaging/install slice. Keep detailed command output in
`evidence.md`; this file records classification, evidence IDs, touch mode, and next phase decisions.

## Scope

Target scope:

- release identity and metadata;
- clean package selection and artifact integrity;
- beginner guide and concise release notes;
- fresh/upgrade/reinstall installer safety;
- package acceptance and preservation fixtures.

Out of scope:

- Goal hardening, workflow redesign, and governance architecture;
- application code, network, hooks, connectors, deployment, and external publication;
- immutable source baseline changes;
- real project-quality eval and live eight-thread runtime claims.

## Relationship / Impact Evidence

Anvien target registration is unavailable, so related-file counts are recorded as unavailable with local source fallback evidence.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `VERSION`, `manifest/package.json` | `E0-P0A-META1`, `E0-P0A-ANV1` | unavailable | release identity and entrypoint metadata | medium |
| `scripts/package.ps1`, `scripts/package.sh` | `E0-P0A-PKG1`, `E0-P0A-ANV1` | unavailable | distributable archive producer | high within release scope |
| `install.ps1`, `install.sh` | `E0-P0A-INSTALL1`, `E0-P0A-ANV1` | unavailable | fresh/upgrade/reinstall system-state writer | critical within install scope |
| package doctor/manifest/lock/governance | `E0-P0A-PASS1` | unavailable | preserve-only integrity consumers | preserve-only |
| Goal/workflow/runtime state | `E0-P0A-STATE1`, `E0-P0A-PASS1` | unavailable | project-state boundary that installer must not overwrite | preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|---|---|---|
| `correct` | Already works and should be preserved. | Preserve and validate. |
| `partial` | Works partly but misses release requirement. | Edit only missing behavior. |
| `missing` | Required release behavior is absent. | Implement bounded behavior. |
| `blocked` | Required authority/evidence unavailable. | Record fallback or stop if acceptance cannot be proven. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| Release identity | Metadata, build report, handoff/docs, and final manifest agree on `codex.5` | Next distinguishable `codex.5` identity | correct | unavailable | `E0-P0A-META1`, `E1-P1A-META1`, Closure | closed |
| Clean package builder | Shared allowlist/checksum/verification helper built final ZIP with 342 content files | Explicit reusable allowlist with exclusions and verified ZIP | correct | unavailable | `E1-P1B-CODE1`, `E2` Closure | closed |
| Installer state classification | Both installers classify release state and write marker after doctor PASS | Fresh/same-version/upgrade/already-initialized explicit and safe | correct | unavailable | `E2-P2A-INSTALL1`, `E2-P2B-*` | closed |
| Project-state preservation | Nine protected state categories/paths retained byte-for-byte across upgrade/reinstall | Preserve FACT/Live/Eval/policy/approval/ledger/CAPSULE/status/Goal | correct | unavailable | `E2-P2A-INSTALL2`, `E2-P2B-UPGRADE1`, `E2-P2B-REINSTALL1` | closed |
| Package doctor/manifest/drift | Final ZIP verify, package doctor, root doctor, and drift PASS | Remains PASS for candidate artifact | correct | unavailable | `E2` Closure, supervisor PASS | closed |
| Goal subsystem | Completed PASS | Preserve; no further hardening | correct | unavailable | `E0-P0A-PASS1` | preserve-only |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-10 | current development tree before release work | metadata, package scripts, installers, state boundary | release identity/package/install are partial; Goal/governance correct | `E0-P0A-META1`, `E0-P0A-PKG1`, `E0-P0A-INSTALL1`, `E0-P0A-STATE1`, `E0-P0A-PASS1` | implement P1-A/P1-B, then P2-A/P2-B |
| R1 | 2026-08-10 | final local artifact and isolated fixtures | release identity, clean archive, installer classification, state preservation, fresh/upgrade/reinstall | all mandatory release rows are correct; supervisor review ready | `E1-*`, `E2-*`, Closure | supervisor acceptance and close |
| R2 | 2026-08-10 | fresh final extraction and supervisor rerun | final artifact, package doctor, drift, 19-test regression, shell/PowerShell fixtures | independent supervisor verdict PASS; plan closed | supervisor report | stop; future work only on reproducible real-project failure |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| `VERSION`, `manifest/package.json`, docs | `BAT-DAU.md`, `docs/SU-DUNG.md` | source-of-truth/consumer | P1-A | edit | `E0-P0A-META1` | only release identity and user-facing guidance |
| package scripts | doctor/manifest/lock | producer/validator | P1-B | edit | `E0-P0A-PKG1`, `E0-P0A-PASS1` | explicit allowlist; refuse overwrite |
| installers | `.p2p/system`, `.p2p` project state | state writer/consumer | P2-A | edit | `E0-P0A-INSTALL1`, `E0-P0A-STATE1` | never replace project state with templates |
| Goal/workflow/governance | package scripts/installers | runtime dependency | all | preserve-only | `E0-P0A-PASS1` | no hardening or redesign |

## Detailed Findings

### Release identity

Current state: `VERSION`, package manifest, build report, handoff, release notes, and final archive agree on `8.4.6-C-codex.5`.

Required state: a single next convention value `8.4.6-C-codex.5` in required release metadata.

Classification: correct.

Allowed next action: preserve; supervisor verifies and closes.

Forbidden next action: invent a new versioning scheme or alter immutable upstream baseline identity.

### Package and installer boundary

Current state: the final package uses an explicit allowlist/checksum manifest; installers classify release state, back up reusable system files, and write a marker only after doctor PASS.

Required state: deterministic clean artifact and explicit safe state classification/preservation.

Classification: correct.

Allowed next action: preserve; supervisor verifies and closes.

Forbidden next action: overwrite or migrate project-specific state without schema evidence.

### Existing passing subsystem

Current state: Goal subsystem, doctor, drift, regression, source inventory, and eight named agents are already PASS.

Required state: remain unchanged and PASS in the release artifact.

Classification: correct / preserve-only.

Allowed next action: validate through package and installer acceptance.

Forbidden next action: further Goal hardening or broad architecture audit.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | metadata/docs implementation and checks PASS | complete; preserve |
| P1-B | final allowlist artifact has 342 content files, checksums, manifest, doctor, and drift PASS | complete; preserve |
| P2-A | both installers classify release state and preserve protected project state | complete; preserve |
| P2-B | final artifact fresh/upgrade/reinstall fixtures and shell path PASS | complete; supervisor review |
| Pn-A | supervisor independently reviewed source/artifact/fixtures and returned PASS | complete; preserve |
| Pn-B | shipped package contains no plan/report/cache/project-state paths; staging remains quarantined under `.tmp` | complete; preserve |
| Pn-C | final path/hash, doctor/drift/regressions, no-Git exception, and status are recorded | complete; stop |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Relationship counts are recorded unavailable with Anvien fallback evidence.
- [x] Phase Touch Map defines edit/preserve-only modes.
- [x] Correct Goal/governance parts are preserve-only.
- [x] Partial surfaces have exact next actions.
- [x] Anvien unavailability is recorded as tooling fallback, not a release blocker.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Downstream phase assumptions and work steps reflect current reality.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, and work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

Release packaging and installer acceptance are complete. Supervisor review is the only remaining
closure action. The Goal subsystem and existing P2P governance/workflow remain trusted and
preserve-only.
