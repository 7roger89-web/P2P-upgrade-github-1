# P2P Native Decision Trace — Release / Install Integration Actual Status

Title: P2P Native Decision Trace — Release / Install Integration
Date: 2026-08-12
Status: P0–P4 Complete / PASS
Companion plan: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-plan.md`
Companion evidence: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-evidence.md`
Companion benchmark: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-benchmark.md`

## Purpose

This living file records the real package/install/runtime state before and
after each release integration slice. P0 was completed before any packaging
implementation edit.

## Freshness / Refresh Rules

Refresh affected rows after every implementation slice. Keep baseline facts in
the refresh log; do not silently rewrite the old `.4` release evidence.

## Scope

Target scope:

- full-release runtime payload;
- package builder, metadata, doctor and drift boundary;
- PowerShell/POSIX installer provisioning;
- fresh/upgrade/reinstall and installed Decision Trace certification;
- new local release candidate only.

Out of scope:

- old `.4` ZIP mutation;
- v5 artifact, App Game Truyện, Logistics, user projects, user home;
- Code-Impact, Anvien, Semantica, Brigade/Tideline, graph/RDF/MCP,
  external providers, specialist changes, UI redesign and public publication.

## Relationship / Impact Evidence

Anvien does not register the target path. `mcp__anvien__list_repos` returned
only unrelated `app_game_truyen`; `mcp__anvien__context` for the target failed
with `repository path is not registered`. Relationship counts are therefore
`unavailable`, not invented. Local `rg`, source reading, old ZIP extraction,
package doctor, and isolated lifecycle evidence are the bounded fallback.

| Unit / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `scripts/package_release.py` | `E0-P0A-PACKAGE1` | unavailable | explicit package allowlist and runtime staging | critical package producer |
| `scripts/doctor.py` | `E0-P0A-DOCTOR1` | unavailable | package/installed validation consumer | critical acceptance gate |
| `install.ps1`, `install.sh` | `E0-P0A-INSTALL1` | unavailable | runtime/system-state writer | critical lifecycle gate |
| `.p2p/system/p2p_capabilities/decision_trace.py` | native trace supervisor PASS | unavailable | verified runtime source | preserve semantics; package it |
| `.p2p/system/scripts/p2p_decision_trace.py` | native trace supervisor PASS | unavailable | verified CLI wrapper | package/install runtime |
| `manifest/*`, `.p2p/system/p2p.manifest.json`, `VERSION` | `E0-P0A-VERSION1` | unavailable | release/version authorities | advance `.4` to `.5` |
| `.p2p/state/*`, governance, old ZIP | `E0-P0A-STATE1`, `E0-P0A-BASELINE1` | N/A | protected state and artifact boundaries | preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|---|---|---|
| `correct` | Already satisfies the release contract. | Preserve and certify. |
| `partial` | Exists but misses a required lifecycle binding. | Edit only the missing binding. |
| `missing` | Required payload/check/flow is absent. | Implement the bounded piece. |
| `wrong` | Conflicts with the release or state-preservation contract. | Replace only with authority-backed behavior. |
| `fake-or-stub` | Simulated identity or unsupported evidence is used. | Remove claim; report evidence level. |
| `blocked` | Required evidence or runtime path cannot be obtained. | Stop downstream PASS claims and record blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| Baseline `.4` release artifact | Exists; extracted package doctor PASS; no Decision Trace members | unchanged old artifact | correct/preserve-only | N/A | `E0-P0A-BASELINE1`, `E0-P0A-GAP1` | rehash after new build |
| Version authority | `VERSION`, package manifest, runtime manifest, build report agree on `.4` | derive `.5` under same policy | correct baseline / pending update | unavailable | `E0-P0A-VERSION1` | P1-B |
| Native Decision Trace source | DT1–DT24 PASS; module and wrapper present in development source | same runtime semantics in ZIP | correct source / unbound package | unavailable | prior supervisor PASS, `E0-P0A-GAP1` | P1-A |
| Package builder | UIUX/Foundation runtime staging exists; trace not in runtime allowlist; current build drift-fails on excluded developer files | trace payload packaged; clean drift PASS | partial | unavailable | `E0-P0A-PACKAGE1` | P1-A/P1-B |
| Package doctor | old artifact PASS; source unpacked tree intentionally fails missing runtime payload; no trace check | actual new ZIP PASS and trace recognized | partial | unavailable | `E0-P0A-DOCTOR1` | P1-A |
| PowerShell installer | release-aware; UIUX/Foundation copies; no trace copy/requirement | automatic trace provisioning | partial | unavailable | `E0-P0A-INSTALL1` | P2-A |
| POSIX installer | release-aware; UIUX/Foundation copies; no trace copy/requirement | automatic trace provisioning | partial | unavailable | `E0-P0A-INSTALL1` | P2-A |
| Runtime manifest/provider metadata | UIUX/Foundation metadata, no Decision Trace entry | trace infrastructure metadata, `P2P_NATIVE`, no agent | partial | unavailable | `E0-P0A-VERSION1` | P1-A/P1-B |
| Project state / execution ledger | existing state outside system tree; trace source already uses ledger | byte-preserve on upgrade; append only after action | correct/preserve-only | N/A | `E0-P0A-STATE1` | P2-B |
| Canonical governance | exact eight, denominator 8, 8/8; Aesthetica optional | unchanged | correct/preserve-only | unavailable | `E0-P0A-GOV1` | certify only |
| UIUX/Foundation | verified `.4` artifact and source payload | regression preserved in `.5` | correct/preserve-only | unavailable | `E0-P0A-BASELINE1` | certify only |
| Anvien | target not registered | fallback recorded | blocked for Anvien only | N/A | `E0-P0A-ANVIEN1` | local inspection allowed |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-12 | pre-implementation source and old `.4` ZIP | version, payload, doctor, installers, lock, state boundary | initial classifications | `E0-P0A-*` | P1-A/P1-B implement missing package bindings |

## Phase Touch Map

| Unit / Surface | Relationship | Plan Item | Touch Mode | Constraint |
|---|---|---|---|---|
| package builder/allowlist | package producer | P1-A/P1-B | edit | runtime only; developer evaluator excluded |
| package/installed doctor | acceptance consumer | P1-A | edit | fail closed on missing trace payload |
| VERSION/manifests/release docs | release authority | P1-B | edit | `.4` -> `.5`; old artifact unchanged |
| installers | lifecycle writer | P2-A | edit | copy runtime; preserve project state |
| evaluator/tests/reports | certification evidence | P2-B/P2-C/P3 | edit/new | developer-only; temp fixtures only |
| native trace module/semantics | certified runtime | all | preserve-only | no semantic redesign |
| old ZIP/user projects/App Game Truyện/Logistics | protected boundary | all | do-not-touch | hash/state proof required |

## Implementation Gate

- [x] P0 target scope is listed in the Current Status Matrix.
- [x] Each target surface has a current status and evidence IDs.
- [x] Relationship count limitation is recorded with Anvien fallback.
- [x] Preserve-only, inspect-only, editable, generated, and do-not-touch modes are explicit.
- [x] Current package and installer gaps have exact next actions.
- [x] Old release hash and package doctor baseline are recorded.
- [x] P0 decision is complete before packaging implementation.

## Final P0 Decision

## Final status refresh — PASS

| Surface | Final state | Evidence |
|---|---|---|
| Version / package | 8.4.7-C-codex.5; 397 content files; 399 ZIP members | final artifact and boundary audit |
| Decision Trace payload | packaged, installed, doctor-recognized, existing-ledger bound | package doctor and runtime certification |
| PowerShell installer | fresh/upgrade/reinstall PASS | lifecycle fixture logs and reinstall report |
| POSIX installer | fresh install, capture, doctor PASS | POSIX fixture |
| Upgrade state | protected hashes and old ledger bytes preserved; old system backed up | upgrade verification reports |
| Beginner WHY | native trace captured; no Decision ID required; honest missing refs surfaced | WHY before/after report |
| UIUX / Foundation | DW1–DW18 and foundation regression PASS | UIUX/Foundation reports |
| Canonical governance | exactly 8, denominator 8, full quorum 8/8 | manifest, doctors, runtime report |
| Aesthetica | real profile resolved; execution/identity not proven; no simulation | capability doctor readiness chain |
| Boundary / secrets / drift | PASS; no forbidden members or secret findings | boundary, secret, drift reports |
| Supervisor | PASS | supervisor acceptance report |

The final artifact is a protected local release candidate. The source tree is
not Git-managed; commit evidence is N/A. The old .4 artifact remains
preserve-only and hash-identical.

The initial matrix above is the pre-implementation snapshot; the final status
refresh is authoritative for P1–P4 and records all previously partial package,
doctor, installer, and manifest surfaces as PASS/correct.

- [ ] P0 incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, actions, and work steps are updated.
- [ ] P0 complete. Scope is preserve-only.
- [ ] P0 blocked by missing authority.

Decision note:

The verified `.4` artifact is a valid preserve-only baseline but lacks native
Decision Trace. The new Goal may proceed with the smallest package/runtime,
installer, doctor, and certification bindings. No old artifact or user state
may be modified, and the final PASS must come from the new extracted ZIP
lifecycle.
