# P2P-C07 Supported Live A/B Context Boundary Actual Status

Title: P2P-C07 Supported Live A/B Context Boundary
Date: 2026-08-14
Status: PASS — SUPPORTED_LIVE_AB_BOUNDARY_READY
Companion plan: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-plan.md`
Companion evidence: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-benchmark.md`

## Purpose

This file records the real current state before implementation. P0 confirms
the reviewed C06 source, the immutable artifact boundary, the supported host
surface, the existing proxy/identity paths, and the exact missing live link.

## Freshness / Refresh Rules

P0 is current as of 2026-08-14 and must be refreshed after each implementation
slice or any change to source, host configuration, artifact state, fixture
fingerprints, or receipt bindings. Historical reports are evidence pointers,
not replacements for fresh current receipts.

## Scope

Target scope:

- C06 source binding and immutable candidate packaging;
- supported native Codex host execution boundary;
- exact mode/fingerprint/manifest/fixture/artifact binding;
- live receipt, output capture, telemetry provenance, and isolation;
- C1 plus one non-trivial paired dry-run;
- affected regression and independent Supervisor review.

Out of scope:

- full 12-scenario live certification;
- quality/efficiency/token/cost claims;
- release promotion or publication;
- real business projects;
- new memory, DAG, scheduler, provider, or truth-store architecture.

## Relationship / Impact Evidence

The graph was refreshed with `anvien analyze --force --skip-git` because this
development workspace intentionally has no `.git`. Existing symbols that may
be touched must receive fresh file-detail and upstream impact evidence before
editing. New boundary files have no prior symbol impact; existing context and
host-hook symbols remain shared invariant surfaces.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `.p2p/system/p2p_capabilities/context.py` | `E4-P4A-GRAPH1` | 1 source file plus linked flows | deterministic C06 mode builder, fingerprint, manifest, stale binding | preserved; `build_context_view` upstream impact LOW/0 direct nodes |
| `tests/test_p2p_context_delivery.py` | `E0-P0A-SRC1` | N/A | 12-scenario C06 behavior and fixture helpers | direct behavior evidence; extend only after production behavior exists |
| `.p2p/system/scripts/p2p_host_identity_hook.py` | `E2-P2B-HOST1`, `E4-P4B-SUP1` | 2 direct test/config surfaces | official host identity receipt parser and ledger append path | preserved; four fresh receipts verified |
| `.p2p/system/p2p_capabilities/live_execution.py` | `E4-P4A-GRAPH1` | 1 source file; 100 parsed symbols; 11 linked flows | development-only live request/receipt boundary around existing context builder | parsed/current; `finalize_trial` CRITICAL scope warning with 1 direct file and 5 linked process edges; no resolution gaps |
| `tests/test_p2p_live_execution.py` | `E2-P2A-TEST1` | direct test file | fail-closed contract/isolation coverage | test-only; synthetic host evidence is not live proof |
| `.codex/config.toml` | `E0-P0A-HOST1` | N/A | official SubagentStart hook matcher and native agent settings | host/config boundary; no private bypass |
| `scripts/p2p_eval.py` | `E0-P0A-PROXY1` | N/A | deterministic local proxy evaluator | preserve-only; must remain `runtime_task_execution=false` |
| `scripts/package_release.py` | `E0-P0A-PACK1` | N/A | canonical version/artifact builder | preserve-only source; use isolated candidate copy |
| official `.15` ZIP | `E0-P0A-ART1` | N/A | immutable baseline artifact | preserve-only; hash-bound |
| existing `.16-r2` ZIP | `E0-P0A-ART2` | N/A | immutable pre-C06 candidate artifact | preserve-only; hash-bound |
| native Codex child/subagent surface | `E2-P2B-HOST1`, `E4-P4B-SUP1` | 4 accepted live trials | supported host execution tool available to current Codex session | bound-correct; one worker per trial; two missing-hook attempts discarded |

## Status Rules

| Status | Meaning | Allowed next action |
|---|---|---|
| `correct` / `bound-correct` | Current behavior satisfies this scope and is preserved. | Reuse and verify. |
| `partial` | Some behavior exists but the requested invariant is not closed. | Edit only the proven gap. |
| `missing` / `unbound` | Required surface or wiring is absent. | Implement only under the plan. |
| `fake-or-stub` | A proxy/demo exists but cannot prove live execution. | Keep proxy-only; never certify. |
| `blocked` | Required evidence or authority is unavailable. | Stop with the exact failure taxonomy. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| C06 development source | `BASELINE_COMPAT` default plus explicit experimental `CONTEXT_EFFICIENT_V1`; deterministic fingerprints/manifests; stale bindings fail closed | exact reviewed behavior preserved in immutable B state | bound-correct | N/A | `E0-P0A-SRC1` | freeze; do not rewrite |
| C06 focused suite | direct behavior tests cover exact modes, 12 scenarios, required fields, conflicts, pointers, stale data, secrets, workflow receipts | unchanged behavior remains passing | correct | N/A | `E0-P0A-SRC1` | rerun after any affected edit |
| official `.15` | ZIP SHA-256 `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195` | unchanged and preserve-only | correct | N/A | `E0-P0A-ART1` | never overwrite |
| `.16-r2` | ZIP SHA-256 `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf`; packaged context runtime has no C06 markers and is byte-identical to `.15` | unchanged, historical pre-C06 artifact | correct / pre-C06 | N/A | `E0-P0A-ART2` | never overwrite; new B candidate required |
| B immutable candidate | `8.4.7-C-codex.17` at `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v17.zip`; SHA-256 `50eb59740034fb724dfe23d19d7f700c8143cfb9efd07f6cdf0a33d0ed041197`; packaged C06 runtime matches source | immutable, unpromoted C06-bound candidate | bound-correct | N/A | `E1-P1B-PACK1` | use this candidate as B; do not rebuild or promote |
| local proxy evaluator | deterministic subprocess/fixture path; historical `runtime_task_execution=false` | remain proxy-only | correct / fake-or-stub for live claims | N/A | `E0-P0A-PROXY1` | no relabeling |
| host identity hook | existing allow-listed official `SubagentStart`/`SubagentStop` receipt path; historical receipts exist | reuse fresh host identity for live trials | correct but historical-only for C07 | 2 direct surfaces | `E0-P0A-HOST1` | obtain fresh receipt from supported child |
| supported live host surface | native `multi_agent_v1__spawn_agent`/`wait_agent` with `p2p_aesthetica` ran one worker per accepted trial; official hook receipts were fresh for four accepted trials | supported one-worker-per-trial path | bound-correct | 4 accepted | `E2-P2B-HOST1` | preserve supported surface; disclose two discarded capture failures |
| live executor/receipt | development-only boundary validated exact request/context/artifact bindings and issued four ledger-backed live receipts with captured outputs | smallest boundary with true-only-on-host proof | bound-correct | 4 | `E2-P2A-CONTRACT1`, `E2-P2B-BIND1`, `E3-P3A-LIVE1`, `E3-P3B-LIVE1`, `E4-P4B-SUP1` | accepted; stop live execution |
| A/B isolation | four opaque trial roots, four output pointers, distinct fixture/request/context fingerprints, no prior output in any request | separate roots, outputs, and no cross-condition preload | bound-correct | 4 | `E2-P2B-BIND1`, `E3-P3A-CONTEXT1`, `E3-P3B-CONTEXT1` | preserve; no further live scenarios |
| telemetry | receipt has allow-listed authority per candidate field; provider tokens/cost/model detail remain UNKNOWN unless host exposes them | every field labeled or `UNKNOWN` | correct for contract | N/A | `E2-P2A-CONTRACT1`, `E2-P2A-TEST1` | bind fresh host observations without estimates |
| canonical governance | exact eight identities, denominator 8, full quorum 8/8; Aesthetica supporting-only | unchanged | correct | N/A | `E0-P0A-GOV1` | preserve |
| production project safety | no C07 target uses App Game Truyện, Logistics_App_Copy, or another user project | safe fixture roots only | correct | N/A | `E0-P0A-ISO1` | preserve |
| Git state | no `.git` directory exists | no fabricated commit/diff claims | correct | N/A | `E0-P0A-GIT1` | use SHA/file/runtime locks |
| C1 paired live dry-run | A `BASELINE_COMPAT` and B `CONTEXT_EFFICIENT_V1` both live with distinct fingerprints and outputs | two live receipts with exact bindings | PASS | 2 | `E3-P3A-CONTEXT1`, `E3-P3A-LIVE1`, `E4-P4B-SUP1` | stop live execution |
| C7 paired live dry-run | accessibility-heavy read-only C7 A/B both live with distinct fingerprints and outputs; C12 owner boundary not used | one non-trivial paired live proof | PASS | 2 | `E3-P3B-CONTEXT1`, `E3-P3B-LIVE1`, `E4-P4B-SUP1` | stop live execution |
| P4 regression and independent review | focused/full regression, Decision Trace, package/lifecycle, governance, capability, doctor, source-drift, scoped security, artifact/isolation checks, and fresh Supervisor review | terminal supported-boundary decision | PASS | 101 tests / 24 DT cases / 1 Supervisor | `E4-P4A-TEST1`, `E4-P4A-GATE1`, `E4-P4B-REPORT1`, `E4-P4B-SUP1` | close at PASS; no optional hardening |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-14 | current development source, fresh Anvien graph, exact official ZIP hashes, extracted package members, current hook/config, prior supervisor boundary report | initial P0 | C06 source `correct`; `.15`/`.16-r2` `correct` preserve-only; B candidate `missing`; live adapter `missing`; host surface `partial/unbound`; proxy `fake-or-stub` for live claims | `E0-P0A-*` | P1-B must create a new candidate; P2 must implement and prove the live link |
| R1 | 2026-08-14 | isolated candidate source/package plus repository-local lifecycle fixture | P1-B | candidate `bound-correct`; fresh install, `.15` upgrade, and same-version reinstall PASS; official artifacts unchanged | `E1-P1B-PACK1`, `E1-P1B-LIFE1` | implement P2-A contract, then bind supported native host in P2-B |
| R2 | 2026-08-14 | new development-only boundary, direct tests, refreshed `p2p-system` graph | P2-A | live contract `partial/host-unbound`; proxy false-only, stale/security/isolation checks PASS; candidate `.17` unchanged | `E2-P2A-CONTRACT1`, `E2-P2A-TEST1` | use one supported native child per trial; require fresh official ledger receipt |
| R3 | 2026-08-14 | four accepted native-host receipts, four captured outputs, paired-live aggregate, and two discarded hook-capture attempts | P2-B/P3 | host path and live boundary `bound-correct`; C1 and C7 pairs PASS; provider tokens/cost remain UNKNOWN; no production mutation | `E2-P2B-HOST1`, `E2-P2B-BIND1`, `E3-P3A-*`, `E3-P3B-*` | run full affected regression, gates, coder report, and Supervisor review |
| R4 | 2026-08-14 | fresh Anvien graphs, independent receipt/artifact check, focused/full regression, package/build/doctor/lifecycle/governance/capability/security/source-drift gates, coder handoff, and fresh Supervisor review | P4/Pn | all bounded acceptance criteria PASS; no Git diff available by environment; no optional hardening or extra live scenarios | `E4-P4A-*`, `E4-P4B-*` | close terminal PASS and stop |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| C06 context builder | `tests/test_p2p_context_delivery.py` | source of actual A/B payload | P2-A | preserve/import; edit only if needed | `E0-P0A-SRC1` | no third mode; baseline remains default |
| host identity hook | `tests/test_p2p_host_identity_receipt.py`, `.codex/config.toml` | host-owned identity authority | P2-B | preserve/minimal config only | `E0-P0A-HOST1` | no self-report or private API |
| local evaluator | `.p2p/evals/2026-08-14-context-efficiency-ab-proxy-suite.json` | proxy comparison | P2-A | preserve-only | `E0-P0A-PROXY1` | must remain false |
| package builder | `scripts/package_release.py` | candidate creation | P1-B | preserve; invoke on isolated copy | `E0-P0A-PACK1` | output path must be new |
| official ZIPs | external artifact paths | immutable bindings | P1-A/P1-B | preserve-only | `E0-P0A-ART1`, `E0-P0A-ART2` | no overwrite/promotion |
| `.p2p/state/execution-ledger.jsonl` | existing workflow/host receipts | durable evidence store | P2/P3/P4 | append only through existing conventions | `E0-P0A-HOST1` | no second ledger |
| `.tmp` fixture roots | tests and live outputs | isolation boundary | P2/P3 | temporary/quarantine | `E0-P0A-ISO1` | repository-local only |

## Detailed Findings

### C06 source and artifact comparison

The current development source contains the reviewed C06 context module with
exactly two modes and the focused 12-scenario suite. The official `.15` ZIP is
`2,385,951` bytes and hashes to
`af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`. The
existing `.16-r2` ZIP is `2,387,476` bytes and hashes to
`410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf`.

Extracted package comparison under
`.tmp/p2p-c07-artifact-inspection/` shows the packaged
`runtime/p2p_capabilities/context.py` is `2470` bytes with the same SHA-256
`34e385c3f316c53e59039b2dccf85dd851840a7ebcfc2b2578808f06a17e9e59` in both
`.15` and `.16-r2`, and it contains no C06 mode markers. Therefore `.16-r2`
does not contain the reviewed C06 behavior and must not be labeled as B.

### Supported host boundary

The current Codex host exposes supported native child/subagent tools. Existing
project configuration records host-owned subagent identity through the
standard-library hook `.p2p/system/scripts/p2p_host_identity_hook.py`, which
appends allow-listed identity fields to the existing Execution Ledger. The
historical ledger receipts are valid historical identity evidence but not fresh
C07 trial proof. No private AgentControl, undocumented RPC, patched binary,
credential interception, or UI scraping is permitted.

### Proxy boundary

The existing local evaluator and workflow helper can produce deterministic
context manifests and local serialized-byte measurements. They do not perform a
real host/model execution and must continue to emit `runtime_task_execution` as
false. A C07 boundary must consume the actual context view rather than attach a
mode label to an unrelated prompt.

### Isolation and security

The existing C06 context builder rejects secret fields and unsafe ancestor paths.
The new live boundary must add trial-root, output, receipt, stale-binding, and
telemetry-field checks without persisting raw prompts, transcripts, credentials,
environment dumps, or hidden reasoning. Live output is observational benchmark
data, not project memory or a canonical fact.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | `.16-r2` is pre-C06 | complete inspection and freeze exact hashes |
| P1-B | candidate `.17` exists and passed package/doctor/drift/lifecycle gates | complete; use `.17` as immutable B state and do not rebuild during live trials |
| P2-A | contract/receipt/isolation boundary exists and six direct tests pass | complete; do not infer live execution from synthetic tests |
| P2-B | supported host exists and four accepted receipts are ledger-backed; two attempts lacked receipts and were discarded | complete; preserve the failure taxonomy and do not infer missing identity |
| P3-A/P3-B | C1 and selected C7 paired live receipts/output hashes are current and distinct | complete; do not run the remaining scenarios |
| P4 | fresh regression, gate, coder, and Supervisor evidence exists; Supervisor verdict is PASS for C07 | complete; close at terminal PASS |

## Implementation Gate

- [x] Target scope is listed in the Current Status Matrix.
- [x] Each target has a current classification and evidence ID.
- [x] Official `.15` and `.16-r2` hashes are recorded.
- [x] C06 source is identified as correct and preserve-only.
- [x] `.16-r2` is proven pre-C06 and preserve-only.
- [x] Supported native host surface is identified without using a private bypass.
- [x] Proxy path is labeled non-live.
- [x] Canonical eight/quorum and Aesthetica optional status are preserved.
- [x] Temporary inspection root is inside the repository `.tmp` directory.
- [x] No existing production symbol was edited; new boundary file-detail is
      parsed and existing `build_context_view` impact is LOW/0 direct nodes.
- [x] Fresh Anvien file-detail and impact evidence for every existing symbol
      touched by an implementation slice; no existing production symbol was
      edited, and the final graph records new-module detail plus the
      `build_context_view` LOW/0-direct and `finalize_trial` CRITICAL scope
      results.
- [x] Four accepted live receipts bind official host identity, context mode,
      context fingerprint, request fingerprint, output hash, and ledger event.
- [x] C1 and C7 pairs are complete; no additional live scenarios are allowed.

## Final P0 Decision

- [ ] P0 actual-status incomplete.
- [x] P0 complete. Next phase status, next action, and work steps are updated.
- [x] Candidate creation is required because `.16-r2` predates C06.
- [x] Implementation may proceed only after the per-slice Anvien impact gate.
- [x] Candidate `.17` package and lifecycle gates pass; C1/C7 live pairs pass.
- [x] P4 focused/full regression and independent Supervisor review pass; coder
      and Supervisor reports are hash-bound in `E4-P4B-*`.

Decision note:

P0, P1-B, P2-A, P2-B, P3, P4, and the plan closure steps are complete. C06 is
present and correct in development source, absent from `.16-r2`, and bound to
the new unpromoted `.17` candidate. The official `.15` and existing `.16-r2`
artifacts remain hash-identical. A supported native Codex host surface
produced four fresh ledger-backed live receipts for C1 and C7; two attempts
without official hook capture were correctly discarded. Focused/full
regression, package/lifecycle, Decision Trace, governance, capability, doctor,
scoped security, source-drift, artifact/isolation, and independent Supervisor
review all support terminal `PASS`. This closes only
`SUPPORTED_LIVE_AB_BOUNDARY_READY`; it makes no quality, efficiency, token,
cost, provider, release, deployment, or full-12-scenario claim.
