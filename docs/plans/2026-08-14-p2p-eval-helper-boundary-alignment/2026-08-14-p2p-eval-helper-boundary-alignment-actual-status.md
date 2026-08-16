# P2P Eval Helper Boundary Alignment — Prerequisite for Real Context-Efficiency Benchmark Actual Status

Title: P2P Eval Helper Boundary Alignment — Prerequisite for Real Context-Efficiency Benchmark
Date: 2026-08-14
Status: Complete / PASS
Companion plan: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-plan.md`
Companion evidence: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-benchmark.md`

## Purpose

This file records the real current state before implementation. P0 is complete only for the bounded helper/doctor/package boundary described by this Goal. It does not certify real worker execution or context-efficiency improvement.

## Freshness / Refresh Rules

Refresh after each implementation slice and before the next phase. Preserve the initial P0 classification in the refresh log; record transitions explicitly.

## Scope

Target scope:

- `scripts/p2p_workflow.py` helper discovery and bootstrap contract.
- `scripts/p2p_eval.py` project eval v2 ownership.
- `.p2p/system/scripts/p2p_eval.py` installed UI/UX evaluator ownership.
- `scripts/doctor.py`, installed doctor, package builder, manifest, installer, and focused tests.
- Isolated lifecycle fixtures and existing proxy artifact integrity.

Out of scope:

- Context-efficiency runtime, workers, Capsule/Knowledge Delta, providers, scheduler/queue/DAG, App Game Truyện, AESTHETICA research, and whole-repo secret cleanup.

## Relationship / Impact Evidence

Anvien baseline before implementation:

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `scripts/p2p_workflow.py` | E0-P0A-GRAPH1 | 39 inbound refs / 263 symbols / 145 local relationships | workflow consumer of governance, eval, state, and package helpers | high scope warning; resolver-only edit completed |
| `scripts/doctor.py` | E0-P0A-GRAPH2 | 3 inbound refs / 104 symbols / 74 local relationships | package and installed health checks | high scope warning; role boundary edit completed |
| `scripts/package_release.py` | E0-P0A-GRAPH3 | inspected source contract; no source edit | package stage/manifest/verify path | preserve-only; candidate build passed |
| `install.ps1` / `install.sh` | E0-P0A-GRAPH4 | inspected copy contract; no source edit | installed helper/runtime copy and release marker | preserve-only; lifecycle passed |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve and verify. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Current behavior/contract is incorrect. | Replace exact wrong boundary. |
| `missing` | Required behavior does not exist. | Implement only required piece. |
| `unbound` | Surface exists but is not wired to real source/role. | Bind to real source. |
| `fake-or-stub` | Placeholder is used as real behavior. | Remove/replace truthful behavior. |
| `blocked` | Required authority/evidence is unavailable. | Stop and report blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Project eval v2 helper | Root `scripts/p2p_eval.py` accepts `design`; resolver now probes the actual contract before selecting. | One role-appropriate helper with v2 contract. | correct | 39 inbound / 46 flows | E1-P1A-CONTRACT1; E1-P1A-RESOLVE2; E2-P2A-TEST3 | preserve and verify |
| Installed UI/UX helper | `.p2p/system/scripts/p2p_eval.py` accepts UI/UX flags only in the development checkout. | Remain UI/UX-only and never satisfy project eval v2 discovery. | correct | included in workflow graph | E1-P1A-CONTRACT2; E2-P2A-TEST1 | preserve-only |
| Development package doctor | `--package .` now returns an explicit role mismatch; `--root .` auto-detects development and passes after drift lock refresh. | Role-aware development check; no misleading portable payload report. | correct | 3 inbound / 13 flows | E1-P1B-LIFECYCLE1..2; E2-P2B-TEST1..2 | preserve and verify |
| Portable package doctor | Official `.15` passes; candidate `.16` passes strict package validation. | Strict fail-closed portable validation. | correct | package gate | E1-P1B-PACKAGE2..3; E2-P2B-TEST6; E3-P3A-LIFE1 | preserve-only |
| Capability foundation payload | Present in development `.p2p/system`, candidate runtime, and installed lifecycle fixtures. | Correct role/package location and doctor coverage. | correct | package/runtime contract | E1-P1B-PACKAGE4; E2-P2B-TEST5; E3-P3A-REG4 | preserve-only |
| Package manifest/builder | Builder validators and candidate package verify agree; candidate `.16` contains 398 content files/399 checksums. | Manifest, stage, doctor agree. | correct | package gate | E1-P1B-PACKAGE4; E2-P2B-TEST3; E3-P3A-REG3 | preserve-only |
| Installer | Candidate copies project eval helper to installed path and preserves lifecycle state. | Fresh/upgrade/reinstall preserve one compatible helper. | correct | lifecycle | E1-P1B-PACKAGE5; E3-P3A-LIFE2..E3-P3A-LIFE4 | preserve-only |
| `.tmp`/quarantine exclusion | Resolver rejects implicit transient helper paths; explicit package fixtures are allowed only as test package hints. | No transient path enters production discovery/package. | correct | resolver/test boundary | E2-P2A-TEST2; E3-P3A-REG3 | preserve-only |
| Prior proxy evidence | 12 frozen scenarios and 48 structural/proxy trials exist. | Preserve and label as proxy only. | correct | N/A | E0-P0A-PREV1 | preserve-only |
| Whole-repo secret hygiene | Existing findings are outside this Goal. | Separate follow-up; no silent cleanup. | blocked/out of scope | N/A | E0-P0A-PREV1 | report separate goal |
| Canonical quorum | Eight canonical identities; Aesthetica optional/noncanonical. | exactly 8, denominator 8, full quorum 8/8. | correct | N/A | E0-P0A-PREV1 | preserve-only |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | bootstrap and doctor baseline before source edit | helper, doctor, package boundary | initial classifications above | E0-P0A-FAIL1..E0-P0A-PREV1 | P1-A/P1-B inspect-only; P2 implementation awaits ownership map |
| R1 | 2026-08-14 | after P2-A/P2-B and candidate lifecycle | resolver, doctor, package, installer | unbound/wrong -> correct; partial -> correct; candidate `.16` created | E2-P2A-CODE1..E2-P2B-TEST6; E3-P3A-LIFE1..E3-P3A-LIFE5 | P3 regression and independent review only |
| R2 | 2026-08-14 | after final regression, package, proxy, security, governance, and change-detection checks | evidence closure and release boundary | P3 complete; official `.15` unchanged; current candidate `.16-r2` verified; whole-repo secret hygiene remains separate; Git change detection unavailable | E2-P2A-TEST5; E3-P3A-REG1..E3-P3A-HASH2; E3-P3B-PROXY1..E3-P3B-READY1; E4-P4B-CHANGE1 | independent supervisor review and close |
| R3 | 2026-08-14 | after independent source review found and closed installed-root ancestor fallback | resolver role isolation, focused/full regression, rebuilt candidate, lifecycle rerun | installed canonical helper accepted under isolated `.tmp`; ancestor development package suppressed; `.16-r2` rebuilt and A–E rerun | E2-P2A-TEST1..E2-P2A-TEST5; E3-P3A-LIFE6; E3-P3A-HASH2 | independent supervisor review and close |
| R4 | 2026-08-14 | after independent Supervisor Review and final closure | full bounded Goal | Supervisor `PASS`; no residual same-invariant gaps; no release promotion; stop rule applied | E4-P4A-SUPERVISOR1; E4-P4B-CHANGE1 | stop; next Goal is separately authorized |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `scripts/p2p_workflow.py` | `scripts/p2p_eval.py` | consumer/source contract | P2-A | edit | E1-P1A-CONTRACT1; E2-P2A-CODE1 | no new evaluator |
| `scripts/p2p_workflow.py` | `.p2p/system/scripts/p2p_eval.py` | incompatible sibling contract | P2-A | preserve-only | E0-P0A-SRC2 | never select for `design` |
| `scripts/doctor.py` | `.p2p/system/p2p_capabilities` | package/development payload relationship | P2-B | edit/validate | E1-P1B-LIFECYCLE1; E2-P2B-CODE1 | strict portable checks stay fail-closed |
| `scripts/package_release.py` | `manifest/package.json` | package source/manifest | P1-B/P2-B | preserve-only/validate | E1-P1B-PACKAGE2; E2-P2B-TEST3 | no `.15` overwrite |
| `install.ps1` / `install.sh` | `.p2p/system/scripts` | installed copy target | P1-B/P2-B | preserve-only/validate | E1-P1B-PACKAGE5; E3-P3A-LIFE2..E3-P3A-LIFE4 | isolated fixtures only |
| prior proxy artifacts | `docs/plans/2026-08-14-context-efficient-execution-quality-audit` | preserved evidence | P3-B | preserve-only | E0-P0A-PREV1 | never relabel as real |

## Detailed Findings

### Helper ownership and resolution

Current state:

The workflow's first candidate is an installed UI/UX evaluator while bootstrap invokes the project-eval v2 `design` contract. The mismatch is directly reproduced by the bootstrap command.

Required state:

```text
Resolve a helper only when its declared/verified CLI contract matches the requested operation and role. Reject .tmp/quarantine/snapshot paths.
```

Evidence:

- E0-P0A-FAIL1: actual bootstrap failure.
- E0-P0A-SRC1..E0-P0A-SRC2: source and help contract mismatch.

Relationship and impact:

- Related file count: `scripts/p2p_workflow.py` has 39 inbound references and 46 linked flows in the refreshed Anvien snapshot.
- Relationship summary: central workflow consumer of state, governance, eval, and package helpers.
- Impact note: high scope warning; keep edit to candidate contract and tests.

Classification:

`unbound` / `wrong candidate selection`

Allowed next action:

Preserve the contract-aware resolver and use only the candidate `.16` lifecycle path for the later real benchmark.

Forbidden next action:

Do not create a new router/meta-agent/eval system or merge the two helper implementations.

### Doctor role boundary

Current state:

The package doctor is being run against a development checkout and reports root portable payload groups missing, although development payloads exist below `.p2p/system`.

Required state:

```text
Development, extracted portable package, and installed project inputs have explicit role semantics. Portable validation remains strict; development validation does not pretend to be a portable root.
```

Evidence:

- E0-P0A-FAIL2: two missing groups from actual doctor output.
- E0-P0A-SRC3: development payload locations.

Relationship and impact:

- Related file count: 3 inbound references, 104 symbols, and 13 linked flows in refreshed Anvien evidence.
- Relationship summary: doctor/package/manifest/installer boundary.
- Impact note: edit only after ownership map.

Classification:

`wrong` for implicit role assumption; `partial` for portable validation.

Allowed next action:

Preserve strict portable checks and role-aware development/installed checks; no further doctor redesign in this Goal.

Forbidden next action:

Do not weaken or remove required portable payload checks.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Helper candidate order was incompatible with `design`; ownership is now explicit. | completed; preserve resolver |
| P1-B | Doctor invocation conflated development and portable roles; package/installer ownership is aligned. | completed; preserve strict package checks |
| P2-A | Resolver probes the existing project eval v2 CLI contract and excludes transient implicit paths. | completed; no more implementation |
| P2-B | Doctor has explicit role semantics; generated lock and lifecycle checks pass. | completed; proceed to P3/P4 only |
| P3 | Real benchmark remains explicitly out of scope. | lifecycle readiness only |
| P4 | P2 implementation and candidate lifecycle pass. | independent supervisor review and closure only |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Phase Touch Map lists plan-relevant relationship units.
- [x] Phase Touch Map defines initial touch mode.
- [x] Correct parts are marked preserve-only.
- [x] Partial/wrong/unbound/unknown parts have exact next actions.
- [x] Exact Anvien file-detail counts for primary P2 target files recorded.
- [x] No implementation has started before P0 completion.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Next-phase status assumptions and work boundaries are explicit.
- [x] Affected status rows were refreshed after implementation and lifecycle evidence.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are defined before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 was complete before implementation. The bounded Goal is complete: source helper resolution, installed-root isolation, role-aware doctor behavior, package build, isolated candidate lifecycle, regression, package, proxy-preservation, security-scope, governance, canonical evidence, and independent Supervisor `PASS` are recorded. The separate real A/B benchmark must not start in this Goal.
