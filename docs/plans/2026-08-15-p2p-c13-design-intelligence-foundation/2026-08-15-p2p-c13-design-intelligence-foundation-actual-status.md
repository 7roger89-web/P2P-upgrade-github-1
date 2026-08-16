# P2P-C13 Beginner-First Design Intelligence & NUI Faculty Routing Foundation Actual Status

Title: P2P-C13 Beginner-First Design Intelligence & NUI Faculty Routing Foundation
Date: 2026-08-15
Status: P4 validation complete / development-source PASS with limitations
Companion plan: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-plan.md`
Companion evidence: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-evidence.md`
Companion benchmark: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-benchmark.md`

## Purpose

This file records the real current state before implementation. It is a living status record and must be refreshed after each implementation slice.

## Freshness / Refresh Rules

- P0 is the baseline before implementation.
- After each slice, update only affected rows and append a refresh-log entry.
- Detailed command output belongs in the evidence ledger; this file stores classification, touch mode, and plan consequences.
- A high Anvien risk is a scope warning, not an automatic edit ban. Correct surfaces remain preserve-only.

## Scope

Target scope:

- `.p2p/system/p2p_uiux` Design Intelligence foundation, its sole-router integration, package/CLI projection, synthetic tests/fixtures, and plan/evidence/benchmark ledgers.
- Existing C10/C11/C12 contracts are inspected and projected to, not rewritten by default.

Out of scope:

- Real Logistics or App Game Truyện directories; release ZIP/v5/immutable baseline; C08; reopening C09; external NUI runtime; UI browser/Docker deployment; Git commit/publish/release.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `p2p_uiux/router.py` | `E0-P0A-IMPACT1` | 1 affected file; 6 local relationships; 2 linked flows | Sole current UI/UX classifier; calls materiality, foundation route, and profile availability | high file-risk warning; narrow additive edit only |
| `p2p_uiux/__init__.py` | `E0-P0A-IMPACT2` | 0 relationships | Package export boundary | low; additive export is safe after module tests |
| `p2p_uiux/contracts.py` | `E0-P0A-IMPACT2` | 2 local relationships | Existing Design Contract generator/validator | high; preserve-only unless output adapter requires a reference |
| `p2p_capabilities/task_state.py` | `E0-P0A-IMPACT3` | 35 inbound refs; 432 relationships | C11 durable task state/evidence authority | high; preserve-only, projection only |
| `p2p_capabilities/foreground_execution.py` | `E0-P0A-IMPACT3` | 360 relationships; 34 linked flows | C12 bounded foreground execution authority | high; preserve-only, projection only |
| `p2p_capabilities/decision_trace.py` | `E0-P0A-IMPACT3` | 69 relationships; 21 linked flows | C10 trace/provenance authority | high; preserve-only, projection only |
| NUI upstream graph | `E0-P0A-UP1..UP3` | external source | 174-faculty graph, 13 kernels, MIT, frozen revision | inspect-only evidence; no runtime network |
| Real product paths | `E0-P0A-SRC1` | do not inspect/mutate | Explicitly protected by request and AGENTS | do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing parts. |
| `wrong` | Current behavior conflicts with the requirement. | Replace the exact wrong part. |
| `missing` | Required behavior does not exist. | Implement only the missing piece. |
| `unbound` | Surface exists but is not wired to the real source/flow/contract. | Bind only to the real source. |
| `fake-or-stub` | Placeholder is being used as real behavior. | Remove or make the limitation explicit. |
| `blocked` | Required authority/evidence is unavailable. | Stop or record exact blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Sole UI/UX router | Existing `classify_request` now lazily adds validated C13 projection while preserving legacy/Aesthetica keys | Same router remains sole entry point | bound-correct | final file impact: 1 affected file; 6 local relationships; HIGH source warning | `E3-P3A-ROUTE1`, `E4-P4A-GATE4` | preserve additive projection |
| Materiality | Six material categories plus tiny-edit reduced path and omission reasons are implemented | Materiality-aware routing | correct | router/planner boundary | `E2-P2A-PROFILE1`, `E3-P3C-D1-D12` | preserve and extend only with new evidence |
| Task profile | Bounded normalized profile with raw/profile/route fingerprints and beginner-safe defaults | C13 profile and integrity boundary | correct | new planner surface | `E2-P2A-PROFILE1..PROFILE2` | consume through existing router/C11 caller |
| NUI registry | Frozen provenance-bound 174-entry metadata registry with 13 kernels, 9 rules, 0 cycles, zero body preload | Provenance-bound 174-entry metadata registry | correct | new registry surface | `E1-P1A-PROV1..VALID2` | no auto-update/body copy |
| Graph/provenance verifier | Revision/license/graph/registry hashes and fail-closed validation are implemented | Frozen provenance and drift rejection | correct | new planner/registry surface | `E1-P1A-PROV1..VALID1` | future drift requires comparison/approval |
| Route provenance/omission explanation | Activated/dependency/omission reasons and unknowns are emitted with profile/route fingerprints | Explainable profile-bound route provenance | correct | router/planner boundary | `E2-P2A-ROUTE3` | reuse C10 trace authority |
| Dispositions | Five-way disposition set is emitted and tested | Required/Expected/Optional/Excluded/Unknown | correct | new planner surface | `E2-P2B-DISP1` | preserve exact vocabulary |
| Workspace completeness | Task-aware professional workspace model is emitted with progressive disclosure | Full workspace obligation model | correct | new planner surface | `E2-P2B-DISP2` | no wholesale load |
| C10 Decision Trace | Existing trace schema/capture/validation is present | C13 references/reuses it; no second trace | bound-correct | 69 relationships; 21 flows | `E0-P0A-IMPACT3` | preserve-only; project in P3-B |
| C11 task state/evidence | Existing task plan, preflight, completion, evidence contracts | C13 obligations project to C11 without owning state | bound-correct | 432 relationships; 35 inbound | `E0-P0A-IMPACT3` | preserve-only; project in P3-B |
| C12 foreground execution | Existing synchronous bounded executor and verify-before-DONE path | C13 emits lifecycle sequence; C12 remains execution owner | bound-correct | 360 relationships; 34 flows | `E0-P0A-IMPACT3` | preserve-only; project in P3-B |
| Render evidence | Four-state preflight and evidence obligation are implemented; no public runtime exists for actual capture | Honest unknown/blocked behavior and render evidence when runtime permits | contract-correct / runtime unavailable | package boundary; no public runtime | `E2-P2B-LIFE2`, `E4-P4A-GATE3` | retain `RENDER_UNKNOWN` until runtime is mounted |
| Independent critique | Dimension-based independent critique and bounded correction contract are implemented | No self-certification or universal beauty score | correct | new planner surface | `E2-P2B-LIFE3..LIFE4` | require real evidence in future UI task |
| Beginner invocation | Beginner request returns route/profile with no technical/faculty questions | Beginner-safe inference and explicit unknowns | correct | router/planner/CLI | `E2-P2A-PROFILE1`, `E3-P3B-CLI1` | no clarification prompt for faculty/stack/permissions |
| Aesthetica | Optional manifest/profile validation exists | Remain optional, non-canonical, never simulated | correct | capability registry | `E0-P0A-STATE1` | preserve-only; regression test |
| Canonical identities | Exactly eight identity set exists | Preserve exact eight and 8/8 denominator | correct | capability model | `E0-P0A-STATE1` | preserve-only |
| C09 | Existing status is BLOCKED/EVENT_EVIDENCE_UNAVAILABLE | Preserve; no reopen | blocked | governance state | `E0-P0A-BLOCK1` | do-not-touch |
| C08 | Deferred | Remain deferred | blocked/deferred | governance scope | `E0-P0A-BLOCK1` | do-not-touch |
| C12 helper-linter | Separate blocker identified by attached request; not invoked by C13 | Identify separately; never bypass/confuse | blocked/unknown | workflow integration not yet proven | `E4-P4A-GATE5` | remain separate from C13 evidence |
| Git commit | Workspace is not a Git repository | Exact commit or explicit blocker | blocked | repository state | `E0-P0A-GRAPH1` | do not fabricate |
| Docker/Playwright | No public runtime contract in scope and no browser runtime was discovered | N/A unless runtime exists | N/A/unavailable | package boundary | `E0-P0A-BLOCK1`, `E4-P4A-GATE3` | package/CLI validation only |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-15 | baseline before P0 | P2P-C13 foundation | initial classifications above | `E0-P0A-SRC1..E0-P0A-BLOCK1` | P1 registry -> P2 planner -> P3 binding; preserve C10/C11/C12/Aesthetica/C09/C08 |
| R1 | 2026-08-15 | P1-P4 implementation and validation | registry, planner, router projection, CLI, synthetic fixtures, package gates, supervisor | registry/profile/provenance/dispositions/obligations/synthetic route rows moved to correct; render remains runtime-unavailable; Git/helper remain blocked | `E1-*`, `E2-*`, `E3-*`, `E4-*` | development-source PASS; no release/commit; future work requires a real UI runtime or separate helper-linter request |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `p2p_uiux/router.py` | `p2p_uiux/__init__.py` | package consumer/export | P3-A | edit | `E0-P0A-IMPACT1..2` | additive field; preserve legacy keys |
| `p2p_uiux/router.py` | `p2p_capabilities/routing.py` | parallel existing route contract | P3-A | preserve-only/inspect-only | `E0-P0A-STATE1` | no second router |
| `p2p_uiux` new registry/planner | `p2p_capabilities/model.py` | canonical safety precedent | P1/P2 | inspect-only | `E0-P0A-STATE1` | no identity/permission changes |
| `p2p_uiux` new adapter | `p2p_capabilities/decision_trace.py` | C10 authority consumer | P3-B | inspect-only/project | `E0-P0A-IMPACT3` | no second trace |
| `p2p_uiux` new adapter | `p2p_capabilities/task_state.py` | C11 authority consumer | P3-B | inspect-only/project | `E0-P0A-IMPACT3` | no second task state |
| `p2p_uiux` new adapter | `p2p_capabilities/foreground_execution.py` | C12 authority consumer | P3-B | inspect-only/project | `E0-P0A-IMPACT3` | no execution from planner |
| NUI upstream | local registry | external source evidence | P1 | inspect-only/snapshot metadata | `E0-P0A-UP1..UP3` | exact frozen revision/license/hash |
| real products/release/baseline | all | protected/out of scope | all | do-not-touch | `E0-P0A-SRC1` | never mutate |

## Detailed Findings

### Existing sole router (P0 baseline; superseded by R1)

Current state:

- `classify_request` detects UI/UX scope, mixed scope, tiny cosmetic edits, and material accessibility/dense workflow classes.
- `foundation_route` delegates capability readiness to the existing capability model and does not create another router.
- The router has HIGH risk warning, 6 local relationships, and 2 linked flows; its scope must remain narrow.

Required state:

```text
The same classify_request entry point returns a validated C13 design-intelligence projection, preserving existing result keys and optional specialist semantics.
```

Evidence:

- `E0-P0A-IMPACT1`: Anvien file-detail and impact evidence.
- `E0-P0A-STATE1`: canonical identity and optional-specialist rules.

Relationship and impact:

- Related file count: 1 affected file from file impact; 6 local relationships.
- Relationship summary: local classifier helpers and linked classification flows.
- Impact note: high source risk warning; additive lazy integration only.

Classification:

partial

Allowed next action:

Implement P1/P2 first, then one additive P3-A integration with focused compatibility tests.

Forbidden next action:

Do not replace the router, add an agent/router, change canonical denominator, or alter non-UI routes.

### Existing C10/C11/C12 authorities (P0 baseline; confirmed by R1)

Current state:

- C10 Decision Trace validates and stores material decisions through the existing execution ledger.
- C11 task state validates task dependencies, preflight, evidence, completion, checkpoints, and resume classification.
- C12 foreground execution records bounded synchronous intent/receipt/checkpoint and requires current verification before DONE.

Required state:

```text
C13 emits references/projections and obligations; C10/C11/C12 continue to own trace, durable state, and execution transitions.
```

Evidence:

- `E0-P0A-IMPACT3`: file-detail counts and linked flow evidence.
- `E0-P0A-SRC2`: local capability instructions/specs.

Relationship and impact:

- Related file counts are high (35 inbound/432 relationships for C11; 360 C12; 69 C10).
- Relationship summary: these are shared authorities with high blast radius.
- Impact note: preserve-only; no implementation edit planned.

Classification:

bound-correct

Allowed next action:

Project C13 obligation references and lifecycle sequence to existing schemas without writing state.

Forbidden next action:

Do not duplicate task state, trace, execution controller, permission gate, or agent identity.

### Upstream NUI evidence (P0 baseline; implemented by R1)

Current state:

- Current upstream revision and exact raw hashes are known; 174 faculty bodies and graph metadata were inspected directly.
- No local provenance-bound registry exists in `p2p_uiux`.

Required state:

```text
Add a lightweight local registry preserving 174 breadth and graph relationships with exact provenance, no body preload, and no runtime network/update.
```

Evidence:

- `E0-P0A-UP1..UP3`: direct upstream revision/license/hash/inventory evidence.

Relationship and impact:

- Related file count: new package surface; no existing symbol impact before addition.
- Relationship summary: external evidence becomes local source data through an explicit frozen boundary.
- Impact note: integration strategy must remain provenance-bound and drift-aware.

Classification:

missing

Allowed next action:

Implement P1-A/P1-B registry and strategy validation.

Forbidden next action:

Do not copy all `SKILL.md` bodies, auto-fetch, auto-update, or claim a faculty body is executable merely because metadata exists.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Frozen registry/provenance loader validates 174 entries, 13 kernels, 0 cycles, exact hashes, and zero body preload | preserve immutable snapshot; future upstream drift requires explicit comparison |
| P1-B | Six integration strategies and progressive disclosure are represented and tested | keep A/D adopted boundary; do not auto-update or vendor bodies |
| P2-A | Materiality/profile/fingerprint/route planner is deterministic and beginner-safe; mutation fails closed | consume through sole router; retain `ROUTING_PROFILE_MISMATCH` boundary |
| P2-B | Dispositions, workspace obligations, lifecycle, render preflight, critique, safety, and bounded correction are implemented | project to C10/C11/C12; do not duplicate their authorities |
| P3-A | Existing router is sole entry point with additive lazy C13 projection | preserve legacy keys and optional Aesthetica semantics |
| P3-B | Read-only CLI and C10/C11/C12 projection contract are implemented | caller may bind to existing authorities; C13 does not execute or persist |
| P3-C | Synthetic logistics/consumer fixtures and 15 focused tests cover D1-D12/F1-F26 intent | keep fixtures synthetic; add runtime evidence only in a future mounted UI task |
| P4-A | Package/full/regression/doctor/security/package-copy checks pass; Git, render, and helper limitations remain explicit | no release/commit; report helper timeout separately |
| P4-B/P4-C/P4-D | Supervisor PASS; dead-work review complete; closure recorded | development-source plan closed with explicit blockers and no release claim |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable.
- [x] Phase Touch Map lists plan-relevant relationship files and touch modes.
- [x] Correct parts are marked preserve-only.
- [x] Partial/missing/blocked parts have exact next actions.
- [x] Blockers are recorded.
- [x] Next phase status assumptions and work steps are updated from this file.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Affected rows refreshed after implementation begins.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. Upstream evidence was sufficiently frozen and local authority boundaries were clear, so P1-P4 proceeded with the scoped implementation and validation gates.

## Final C13 Decision

- Development-source implementation: `PASS`.
- Supervisor acceptance: `PASS`, recorded in `reports/supervisor/rp_supervisor_260815_010441_by_gpt-5-codex_p2p-c13-design-intelligence-foundation.md`.
- Workflow helper closure: `BLOCKED` after the explicit C13 run timed out; its result is not substituted with package tests.
- Git commit: `BLOCKED` because this is an unpacked workspace without Git metadata; no hash is fabricated.
- Render/browser/Docker evidence: unavailable/N/A because C13 has no mounted public UI runtime; preflight remains explicit and honest.
- C09 remains `BLOCKED/EVENT_EVIDENCE_UNAVAILABLE`; C08 remains deferred; canonical identities remain exactly eight with denominator 8 and full quorum 8/8.
- No release, deployment, merge, publish, connector, hook, proxy, or permission-grant action was taken.
