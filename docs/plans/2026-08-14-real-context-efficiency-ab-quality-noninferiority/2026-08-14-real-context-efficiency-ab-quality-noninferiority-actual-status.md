# Real Context-Efficiency A/B Benchmark & Quality Non-Inferiority Certification Actual Status

Title: Real Context-Efficiency A/B Benchmark & Quality Non-Inferiority Certification
Date: 2026-08-14
Status: Blocked
Companion plan: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-plan.md`
Companion evidence: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-benchmark.md`

## Purpose

This file records the real current state before any implementation or live benchmark execution. The central gate is whether two executable, equivalent A/B conditions and authoritative runtime observation exist.

## Freshness / Refresh Rules

P0 records the current checkout and host state at the beginning of this Goal. No runtime implementation began, so no implementation refresh transition exists. Any future host/runtime change must refresh this file before a rerun.

## Scope

Target scope:

- Existing canonical eval suite and fixtures.
- Existing eval helper/runtime execution surfaces.
- Current Codex host/provider execution and telemetry authority.
- Candidate .16-r2 binding and safety/quorum invariants.

Out of scope:

- Runtime implementation, new architecture, provider integration, user projects, release promotion, and synthetic A/B execution.

## Relationship / Impact Evidence

No production source file is authorized for editing. The relevant surfaces are inspect-only or preserve-only. A future runtime instrumentation change would require a new plan and fresh impact review.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `scripts/p2p_eval.py` | E1-P1A-HELPER1 | 2 | evaluation validation/recording surface; related test `tests/test_p2p_project_eval.py` | inspect-only; HIGH graph scope warning |
| `.p2p/evals/2026-08-14-context-efficiency-ab-proxy-suite.json` | E0-P0A-CANON1 | N/A (data contract) | canonical suite and condition metadata | preserve-only |
| `.p2p/evals/fixtures/2026-08-14-context-efficiency-cases.json` | E0-P0A-CANON1 | N/A (fixture) | frozen scenario inputs | preserve-only |
| current Codex host tool surface | E1-P1A-HOST1 | N/A (host authority) | possible live executor/telemetry source | blocked/missing |
| official .15 and candidate .16-r2 artifacts | E0-P0A-BASE1; E0-P0A-CAND1 | N/A (release artifacts) | immutable baseline/candidate identity | preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing parts in a separately authorized goal. |
| `wrong` | Current behavior or contract conflicts with the requirement. | Record the exact reason; do not silently patch during measurement. |
| `missing` | Required behavior or source does not exist. | Implement only under a separately authorized goal. |
| `unbound` | Surface exists but is not wired to the real flow. | Bind only under a separately authorized goal. |
| `fake-or-stub` | Proxy, mock, or placeholder is being treated as real. | Keep labeled as proxy; do not certify live behavior. |
| `blocked` | Required authority or evidence is unavailable. | Stop. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Canonical suite | Existing 12-scenario schema-v2 suite with frozen fixtures and historical 48 proxy trials | Reuse unchanged | correct | N/A | E0-P0A-CANON1; E0-P0A-PROXY1 | preserve |
| Historical proxy trials | Contract-exerciser runs with `runtime_task_execution=false` | Live host/provider trials | fake-or-stub | N/A | E0-P0A-PROXY1 | never relabel; block live certification |
| Condition A | Baseline label exists in suite metadata, but no current callable live task executor is bound | Executable baseline path | unbound/missing | N/A | E1-P1A-RUNTIME1 | block |
| Condition B | Candidate label exists in suite metadata, but no current callable live context-efficient task executor is bound | Executable candidate path | unbound/missing | N/A | E1-P1A-RUNTIME1 | block |
| `runtime_task_execution=true` proof | Absent for this Goal | Required for every scored trial | missing | N/A | E1-P1A-GATE1 | block |
| Host/provider token/cache telemetry | Not exposed in the callable local surface | Exact authority where available | blocked | N/A | E1-P1A-HOST1; E1-P1A-UNKNOWN1 | mark UNKNOWN |
| Candidate binding | .16-r2 identity and SHA are known and preserved | Exact binding in any future trial | correct | N/A | E0-P0A-CAND1 | preserve |
| Permission boundary | No measurement-specific permission expansion | unchanged | correct | N/A | E0-P0A-SAFETY1; E1-P1A-RELEASE1 | preserve |
| Canonical identities/quorum | Eight canonical identities; 8 denominator; 8/8 quorum | unchanged | correct | N/A | E0-P0A-SAFETY1 | preserve |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | current development checkout and current host | canonical benchmark and live A/B eligibility | initial classification; proxy-only and unbound live conditions identified | E0-P0A-CANON1..E1-P1A-GATE1 | P1 is blocked; no runtime editing or trial execution |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `scripts/p2p_eval.py` | `.p2p/evals/*.json` | validator/recorder consumer | P1-A | inspect-only | E1-P1A-HELPER1 | no live executor inferred from validator |
| canonical suite | frozen fixture/evidence files | source-of-truth benchmark contract | P1-A | preserve-only | E0-P0A-CANON1 | no duplicate or silent redefinition |
| host tool surface | none in repo | external execution authority | P1-A | block | E1-P1A-HOST1 | no telemetry/API authority available |
| release artifacts | runtime manifest/report references | candidate identity | P1-A | preserve-only | E0-P0A-BASE1; E0-P0A-CAND1 | no rebuild, promotion, or overwrite |

## Detailed Findings

### Canonical benchmark

Current state:

The existing canonical suite is present and remains the only benchmark definition. Its historical trials are explicitly proxy-only.

Required state:

```text
Reuse the suite unchanged and bind any live trial to the exact candidate/environment state.
```

Evidence:

- E0-P0A-CANON1: canonical suite and fixture located.
- E0-P0A-PROXY1: historical runtime flag is false.

Relationship and impact:

- Related file count: N/A for the fixture contract; no edit scope.
- Relationship summary: suite, frozen fixture, evidence, and helper contract.
- Impact note: preserve-only.

Classification:

correct for evaluator contract; fake-or-stub for live execution.

Allowed next action:

Reuse unchanged; report historical proxy limitations.

Forbidden next action:

Do not count proxy output as live model/provider evidence.

### Executable A/B conditions

Current state:

The suite labels baseline and candidate conditions, but current repository/host inspection does not prove separately callable live execution paths for them.

Required state:

```text
Condition A and Condition B each execute the same task under controlled, observable host/provider execution.
```

Evidence:

- E1-P1A-RUNTIME1: no callable paired live executor identified.
- E1-P1A-GATE1: hard-stop rule applied.

Relationship and impact:

- Related file count: 2 for the helper surface; no edit scope.
- Relationship summary: metadata labels are not executable behavior.
- Impact note: blocked.

Classification:

missing/unbound.

Allowed next action:

Create a separate, explicitly authorized instrumentation/runtime goal only if the owner wants the missing observation boundary built.

Forbidden next action:

Do not implement the missing executor inside this measurement Goal or fake outputs using the current assistant context.

### Telemetry authority

Current state:

The local callable surface does not expose authoritative per-trial model/provider token, cache, cost, timing, child-call, or tool-call values.

Required state:

```text
Capture exact host/provider telemetry where exposed and label all else UNKNOWN.
```

Evidence:

- E1-P1A-HOST1: host/tool inventory result.
- E1-P1A-UNKNOWN1: unavailable metric classification.

Relationship and impact:

- Related file count: N/A; host surface not editable from this repo audit.
- Relationship summary: external telemetry authority is not bound.
- Impact note: blocked for live efficiency certification.

Classification:

blocked.

Allowed next action:

Record UNKNOWN and stop; revisit only with an approved observation surface.

Forbidden next action:

Do not convert character/byte counts, shell duration, or conversation impressions into provider token/cost claims.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | A/B labels exist but live executors and `runtime_task_execution=true` proof are missing; host telemetry is unavailable | block P1; do not execute trials or edit runtime |
| Pn-A | Plan is blocked by a hard scientific gate, not by an untested hypothesis | supervisor reviews the blocker and evidence sufficiency |
| Pn-B/Pn-C | No runtime implementation or benchmark result exists | remove only dead plan artifacts if any; close as BLOCKED with no release impact |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable; no production file is an edit target.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blockers are recorded.
- [x] Next phase status assumptions, next action, and work steps were updated from this status file.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Implementation did not start; no refresh transition is required.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [x] P0 complete. Implementation is blocked by missing executable conditions and telemetry authority.

Decision note:

P0 is complete. The canonical benchmark can be reused, but the required real A/B experiment cannot start: the current suite is proxy-only, the repository does not expose two callable live conditions, and the current host surface does not expose the required per-trial provider/runtime authority. The correct action is to stop as `BLOCKED`, not to create a second runner or infer metrics.
