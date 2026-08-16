# P2P Aesthetica Host Compatibility and Real Runtime Recovery Actual Status

Title: P2P Aesthetica Host Compatibility and Real Runtime Recovery
Date: 2026-08-13
Status: FINAL PASS; P0/P1/P2/P3/CLOSURE COMPLETE
Companion plan: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-plan.md`
Companion evidence: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-evidence.md`
Companion benchmark: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-benchmark.md`

## Purpose

This is the living current-state record. P0 must classify source, host, package, readiness, and real execution before implementation begins. It will be refreshed after each implementation slice.

## Scope

Target scope: development source `D:/AI/P2P_dev/P2P-8.4.6-C-Codex-Edition-v4`, isolated host probes, and any new candidate package.

Out of scope: verified `.6` artifact, v5 artifact, immutable baseline, App Game Truyện, Logistics, and all real user projects.

## Relationship / Impact Evidence

Anvien index refresh has completed with `--skip-git` because this development source has no `.git` directory. File-detail and symbol/file impact evidence will be recorded before any code edit.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.codex/agents/p2p-aesthetica.toml` | direct TOML audit; legacy keys confirmed | N/A | host profile packaged and consumed by doctors | medium; hidden path not in Anvien graph |
| `.p2p/system/p2p_capabilities/specialist.py` | direct source audit; execution-aware status confirmed | N/A | readiness/profile validator consumer | high; hidden path not in Anvien graph |
| `.p2p/system/p2p_capabilities/routing.py` / router | direct source audit; Aesthetica projection passes profile resolution as executable | N/A | readiness is consumed by routing | high; hidden path not in Anvien graph |
| `.p2p/system/scripts/p2p_capability_doctor.py` | direct source audit; same projection defect confirmed | N/A | installed/package foundation doctor | medium; hidden path not in Anvien graph |
| `scripts/doctor.py` / `doctor.ps1` | direct/package doctor audit; official schema and manifest classification checks confirmed | 14 affected symbols; 3 processes for Python package path | package doctor and Windows installer lifecycle | high file risk |
| `scripts/package_release.py` | Anvien file-detail; package producer and allowlisted release surface confirmed | 61 symbols; 33 local relationships | final artifact producer | high; unresolved analyzer gaps are non-actionable |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Aesthetica custom-agent schema | current profile uses official `developer_instructions` and `sandbox_mode = "read-only"`; P2P classification is manifest-owned | current official standalone-agent schema and read-only sandbox | correct | 0 legacy shapes | E1-P1A-SCHEMA2 / E1-P1A-HOST2 | preserve |
| All canonical profiles | eight profiles use current `developer_instructions` shape | preserve exact eight and read-only | correct | 8 | E0-P0A-SCHEMA1 | inspect-only |
| Project trust activation | persistent exact child trust is not edited; session-only diagnostic override activates project `agents` | legitimate trusted isolated project context | host boundary respected | 1 security boundary | E0-P0A-TRUST1 / E3-P3-TRUST1 | user may persist trust for normal sessions |
| Windows native sandbox | real child execution passes in both supported modes | supported native sandbox mode starts child | correct | 2 proven modes | E3-P3-UNELEVATED1 / E3-P3-ELEVATED1 | preserve |
| Aesthetica readiness | profile resolves to `RESOLVED` without execution proof; host evidence separately proves two child executions | `RESOLVED` until actual execute; `HEALTHY` only after bounded evidence | correct | 0 false positives after fix | E1-P1B-READINESS2 / E3-P3-MULTI1 | preserve |
| Canonical quorum | registry declares exact eight, denominator 8, full quorum 8/8 | unchanged | correct | 8 | E2-P2-DOCTOR1 |
| Optional specialist classification | manifest declares supporting, optional, noncanonical; host TOML contains no unknown classification keys | unchanged and never simulated | correct | 1 manifest entry | E1-P1A-SCHEMA2 / E2-P2-DOCTOR1 | preserve |
| Package `.6` | verified artifact exists and is preserve-only | never modify | correct | N/A | supplied baseline | preserve-only |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-13 | `.6` source and fresh P0 inspection | host compatibility and readiness surfaces | initial classifications pending reproduction | E0-P0A-* | P0 complete |
| R1 | 2026-08-13 | edited development source | official profile schema, readiness, routing projections, doctor checks | P1 fixes applied; foundation 25/25 | E1-P1A-SCHEMA2 / E1-P1B-READINESS2 / E1-P1-TEST2 | P2 package validation |
| R2 | 2026-08-13 | final v9 artifact and extracted package | package boundary, PowerShell doctor, install lifecycle | v9 package and lifecycle 2/2 pass | E2-P2-PACKAGE1 / E2-P2-LIFECYCLE1 | P3 host validation |
| R3 | 2026-08-13 | native Codex app-server | real child identity in elevated and unelevated modes | two host-selected Aesthetica children proven | E3-P3-UNELEVATED1 / E3-P3-ELEVATED1 | closure |
| R4 | 2026-08-13 | final source/package/reports | supervisor and scope closure | all required checks pass | E4-CLOSURE1 / E4-CLOSURE2 | stop |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| Aesthetica profile | package/archive manifest | source and packaged config | P1-A | edit | E1-P1A-SCHEMA2 | official keys only; manifest preserves classification |
| specialist validator | doctor/router/tests | readiness consumer | P1-B | edit | E1-P1B-READINESS2 | no new certification system |
| routing projection | router/tests | readiness consumer | P1-B | edit | E2-P2-ROUTE1 | single router only |
| package doctor | release builder | schema gate | P1-A | edit | E1-P1A-FIX2 / E2-P2-DOCTOR1 | no v5 or `.6` mutation |
| Windows PowerShell doctor | installer lifecycle | official schema + manifest classification | P1-A/P2-A | edit | E1-P1A-FIX2 / E2-P2-LIFECYCLE1 | no host trust mutation |
| host trust config | Codex user config | security boundary | P0/P3 | inspect-only | pending | never silently edit |
| Windows sandbox | Codex host | external runtime | P0/P3 | validate-only | pending | no bypass/full-access |

## Detailed Findings

### Host-compatible custom-agent profile

Current state: the Aesthetica profile uses the official host fields. Its
supporting/optional/noncanonical classification is intentionally stored in the
P2P manifest rather than duplicated in the host TOML.

Required state: `name`, `description`, `developer_instructions`, and explicit
`sandbox_mode = "read-only"`; P2P classification remains manifest-owned.

Evidence: `E1-P1A-SCHEMA2`, `E1-P1A-HOST2`.

Classification: correct; no extra host schema fields are required.

Allowed next action: preserve and certify through package/host checks.

Forbidden next action: add authority, change canonical quorum, or edit host/user trust silently.

### Readiness semantics

Current state: `validate_optional_specialist(..., execute_verified=False)` returns
`RESOLVED`; doctor/router projections do not treat profile presence as execution
proof. Separate host metadata proves actual execution when available.

Required state: profile presence/resolution is not runtime execution. `EXECUTABLE` requires actual execution verification; `HEALTHY` requires a bounded healthy run/evidence check.

Evidence: `E1-P1B-READINESS2`, `E2-P2-DOCTOR1`, and `E3-P3-MULTI1`.

Classification: correct.

Allowed next action: stop; do not simulate further readiness.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Official schema fix and PowerShell doctor compatibility complete | complete |
| P1-B | Readiness now requires explicit execution evidence | complete |
| P2-A/P2-B | v9 package, lifecycle, routing, Decision Trace, canonical, secret, and regression checks pass | complete |
| P3-A/P3-B | Two host-selected Aesthetica child threads proven in elevated and unelevated read-only modes | complete |
| Closure | supervisor review, final artifact, evidence, and scope checks pass | complete |

## Implementation Gate

- [x] P0 target scope listed and classified.
- [x] Fresh evidence IDs added for every P0 status row.
- [x] Anvien file-detail/impact evidence recorded for editable code.
- [x] Trust and sandbox blockers remain inspect-only.
- [x] R0 baseline finalized before implementation.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status and next action are updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note: P0 passed. The proven implementation defects were the legacy
Aesthetica host schema, readiness false-positive, and a shipped PowerShell doctor
check that still assumed removed TOML classification keys. All three were fixed
within scope. Trust is not auto-edited; the final runtime proof uses a
session-only exact-project trust diagnostic and supported read-only sandbox modes.

## Final Decision

`PASS`. All HC1–HC18 acceptance checks are satisfied. The final artifact is
`8.4.7-C-codex.9`; the verified `.6`/v5 artifacts and all user projects remain
unchanged.
