# P2P-C09 Supported Generic Host Identity and Route Observation Boundary Actual Status

Title: P2P-C09 Supported Generic Host Identity and Route Observation Boundary
Date: 2026-08-14
Status: BLOCKED — implementation, regression, and package gates complete; current host emitted no fresh generic/default or canonical official identity receipt.
Companion plan: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-plan.md`
Companion evidence: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-benchmark.md`

## Purpose

This file records the real current state before implementation and is refreshed
after each completed implementation slice. The plan cannot move past P0 until
each target has a classification, evidence IDs, relationship evidence where
applicable, and a concrete next action.

## Freshness / Refresh Rules

- P0 is the baseline before runtime editing.
- Refresh affected rows after every implementation slice and before the next phase.
- Keep prior classifications in the Status Refresh Log; do not erase history.
- Detailed command output remains in the companion evidence ledger.

## Scope

Target scope:

- Existing official host identity hook/config and existing live Execution Ledger/receipt boundary.
- Current route/capability semantics for C1-C12 and `p2p-uiux`.
- Minimum live proofs for standard/non-UI, normal UI, accessibility-heavy, and one canonical custom profile.

Out of scope:

- C08 scored trials and quality claims.
- Router redesign, new profiles/agents/ledgers, provider telemetry, protected release promotion, and protected artifact mutation.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.p2p/system/scripts/p2p_host_identity_hook.py` | `E0-P0A-GRAPH1`, `E3-P3A-ANVIEN1` | 1 indexed target; 9 linked flows; no cross-file inbound/outbound edges in current graph | 31 symbols, 21 local relationships, current/not stale; official hook/ledger parser | high parser risk; upstream blast radius 1 file, MEDIUM file warning, 1 affected process (`E3-P3A-ANVIEN1`) |
| `.p2p/system/p2p_capabilities/live_execution.py` | `E0-P0A-GRAPH1`, `E3-P3A-ANVIEN1` | 1 indexed target; 12 linked flows; no cross-file inbound/outbound edges in current graph | 116 symbols, 86 local relationships, current/not stale; live request/receipt boundary | high parser risk; upstream blast radius 1 file, MEDIUM file warning, 1 affected process (`E3-P3A-ANVIEN1`) |
| `.p2p/system/p2p_uiux/router.py` | `E0-P0A-GRAPH1` | 1 indexed target; 2 linked flows; no cross-file inbound/outbound edges in current graph | 43 symbols, 6 local relationships, 75 unresolved; single route decision function | high source risk; upstream blast radius 1 file/3 symbols, LOW file warning, 1 process hit (`E0-P0A-IMPACT3`); preserve-only |
| `.codex/config.toml` | N/A (TOML not in p2p-system Python graph) | 1 direct consumer | official SubagentStart matcher and command | editable only for explicit allow-list; no wildcard/profile creation |
| `.p2p/system/p2p_capabilities/capabilities.json` | N/A (JSON registry) | 1 registry | exact canonical/optional/skill declarations | correct; preserve-only |
| `tests/test_p2p_host_identity_receipt.py` | N/A (test graph not linked) | direct test surface | current AESTHETICA/default/missing/secret/dedup/config tests | partial; default positive must be updated to supported generic semantics and unknown must fail |
| `tests/test_p2p_live_execution.py` | N/A (test graph not linked) | direct test surface | current host receipt, proxy, stale, artifact, request, isolation tests | partial; route fields and explicit mismatch/session/turn taxonomy are missing |
| C07 historical receipts/reports | `E0-P0A-C07-1` | preserve-only evidence family | four accepted AESTHETICA-backed live proofs and historical `/1` receipts | correct historical evidence; never rewrite |
| Official `.15`, `.16-r2`, `.17` | `E0-P0A-ART1` | preserve-only artifacts | immutable release/candidate inputs | correct/preserve-only; hashes must be rechecked after work |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve; add evidence/tests only if needed. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing behavior. |
| `wrong` | Current behavior conflicts with the requirement. | Replace the exact conflicting contract. |
| `missing` | Required behavior does not exist. | Implement only the missing piece. |
| `unbound` | Surface exists but is not wired to the real source/flow. | Bind to the real source only. |
| `fake-or-stub` | Prototype/proxy is being used as real behavior. | Keep proxy false-only; add official evidence. |
| `blocked` | Authority/evidence is unavailable. | Stop and record the exact blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| C1-C12 route semantics | Frozen route observation exists; C2/C3 lexical UI hits are disclosed; C6 is `p2p-uiux`; C7 is the only AESTHETICA-eligible case | Current route/profile matrix recorded without redesign | correct/partial | N/A | `E0-P0A-SRC1` | preserve router; document map in final report |
| `p2p-uiux` semantic type | Registry/SPEC declare `TYPE=SKILL`, no Codex profile exists | logical capability can be recorded separately from host profile | correct | N/A | `E0-P0A-SPEC1`, `E0-P0A-REG1` | preserve; bind metadata in P1-B |
| Host hook | Existing official lifecycle/ledger path is now explicit and fail-closed for canonical, optional, and supported generic identities | allow-listed host types, secret rejection, backward-readable receipt | correct | 9 linked flows; 21 local relationships | `E1-P1A-HOOK1`, `E1-P1C-IDENTITYTEST1` | preserve; host emission remains a live blocker |
| Hook config | Matcher is explicit for `default`, canonical eight, and `p2p_aesthetica` | no wildcard and no `p2p-uiux` profile | correct | 1 direct consumer | `E1-P1A-CONFIG1` | preserve; host activation must be rechecked |
| Live execution receipt | Route/capability, requested/observed host identity, class, authority, session, and turn are recorded; mismatch/missing taxonomy is explicit | route/capability + requested/observed host identity and authority fields; exact mismatch/missing taxonomy | correct locally; live proof blocked | 12 flows; 86 local relationships | `E1-P1B-ROUTE1`, `E1-P1B-FAILCLOSED1`, `E1-P1C-LIVETEST1` | preserve; do not certify without fresh official receipt |
| Existing C07 AESTHETICA evidence | Four accepted live proofs and `/1` receipts exist | backward-readable and unchanged | correct | preserve-only | `E0-P0A-C07-1` | preserve; regression in P1-C |
| Normal UI without AESTHETICA | Router says `p2p-uiux` primary and `call_aesthetica=false`; real `default` probe completed without a fresh official receipt | live proof with actual host executor, no forced AESTHETICA | blocked | 0 accepted proofs | `E2-P2A-NORMALUI1`, `E2-HOST-BLOCKER1` | wait for current host receipt emission |
| Accessibility-heavy UI | Selective route policy and historical C07 AESTHETICA profile are correct; no fresh C09 proof was accepted | fresh route + host identity + optional status | partial / blocked | historical only | `E0-P0A-C07-1`, `E2-P2B-A11Y1` | preserve policy; do not relabel history |
| Canonical custom profile | Eight TOML profiles exist and matcher is configured; real `p2p_iris` probe completed without a fresh official receipt | exact host-owned canonical identity proof | blocked | 0 accepted proofs | `E2-P2B-CANONICAL1`, `E2-HOST-BLOCKER1` | wait for current host receipt emission |
| Proxy/live boundary | Local proxy correctly cannot promote to live | remains false-only | correct | 11 live flows | `E0-P0A-LIVE1`, `E0-P0A-C07-1` | preserve and rerun tests |
| Canonical quorum | Exact eight identities, denominator 8, full quorum 8/8 | unchanged | correct | N/A | `E0-P0A-REG1` | preserve-only |
| Protected artifacts | `.15`, `.16-r2`, `.17` are immutable inputs; `.18` is a new candidate | unchanged protected inputs; `.18` unpromoted | correct | `.18` SHA-256 recorded | `E0-P0A-ART1`, `E3-P3A-PACKAGE1` | preserve; no promotion |
| Git checkpoint | No `.git` directory exists | no fabricated diff/commit claim | blocked (environment) | N/A | `E0-P0A-GIT1` | record limitation; continue with hashes/reports |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | fresh `p2p-system` Anvien graph, current source/config/registry, frozen C08 observation, C07 report, protected hashes, no-Git check | full P0 scope | route map correct/partial; hook/config/live partial; router/registry/C07/artifacts correct; normal UI/canonical host unbound; Git checkpoint blocked by environment | `E0-P0A-SRC1`..`E0-P0A-GIT1` | P1-A edits hook/config; P1-B adds route/identity receipt contract; router remains preserve-only |
| R1 | 2026-08-14 | refreshed Anvien graphs, production changes, focused/affected/full tests, candidate `.18` package gates, two real host probes, ledger recheck, protected hash recheck, coder handoff | P1/P2/P3 | P1 correct; package/regression correct; standard/default, normal UI, and canonical live proofs blocked by absent fresh official receipts; historical C07 preserved; C08 remains zero | `E1-*`, `E2-*`, `E3-*`, coder report | stop at BLOCKED; next decision is to restore official host `SubagentStart` receipt emission for supported types |

## Post-implementation status update

P1-A, P1-B, and P1-C are complete. The hook/config and live receipt
contracts are implemented and directly tested. The router and capability
registry remain unchanged. Candidate `.18` is independently packaged and
verified, and the full suite is green.

P2 is blocked at the host boundary, not at the local contract: a real
`default` worker and a real `p2p_iris` worker both completed bounded read-only
probes, but the official ledger gained no fresh matching receipts. The ledger
still contains only the 18 historical AESTHETICA receipts. No identity was
inferred from the worker labels or prose.

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| host hook | `tests/test_p2p_host_identity_receipt.py` | direct behavior test | P1-A/P1-C | edit | `E0-P0A-HOOK1`, `E0-P0A-IMPACT1` | allow-list only; keep stdout empty |
| host config | `.codex/agents/*.toml` | host profile source/consumer | P1-A | inspect-only | `E0-P0A-HOOK1` | do not create `p2p-uiux`; matcher must be explicit |
| live boundary | `tests/test_p2p_live_execution.py` | direct behavior test | P1-B/P1-C | edit | `E0-P0A-LIVE1`, `E0-P0A-IMPACT2` | preserve artifact/context/proxy invariants |
| route router | `.p2p/system/p2p_uiux/router.py` | logical route source | P1-B/P2 | preserve-only / validate-only | `E0-P0A-SRC1`, `E0-P0A-IMPACT3` | no lexical routing redesign |
| capability registry | `.p2p/system/p2p_capabilities/capabilities.json` | skill/profile classification source | P1/P2 | preserve-only / validate-only | `E0-P0A-REG1` | canonical count remains 8 |
| C07 artifacts/reports | `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/*` | historical evidence | all phases | preserve-only | `E0-P0A-C07-1` | do not rewrite historical receipts |
| `.15/.16-r2/.17` | external ZIP/candidate paths | protected artifact inputs | P3 | do-not-touch | `E0-P0A-ART1` | new candidate only, no promotion |
| temporary live roots | `.tmp/p2p-c09-live-*` | isolated evidence output | P2/P3 | create/quarantine | plan rule | never use C08 scored roots or project source |

## Detailed Findings

### Route and capability semantics

Current state:

The frozen route observation and approved capability SPECs already distinguish
logical route/capability from host profile. `p2p-uiux` is a `SKILL`; C6 uses it
without AESTHETICA; C7 selectively makes AESTHETICA eligible; C2/C3 lexical
ambiguity is disclosed.

Required state:

```text
Keep routing unchanged; add passive receipt metadata that records intended route/capability separately from observed host identity.
```

Evidence:

- `E0-P0A-SRC1`: current C1-C12 route observation.
- `E0-P0A-SPEC1`: approved skill/optional-specialist/single-router contract.

Relationship and impact:

- Related file count: one router target plus current registry/config consumers.
- Relationship summary: router emits logical selection; host hook emits identity; live boundary joins them.
- Impact note: router is preserve-only; route metadata must not mutate route behavior.

Classification:

correct for routing semantics; partial for route-to-host evidence.

Allowed next action:

Add passive route observation fields in the existing live receipt boundary.

Forbidden next action:

Create a `p2p-uiux` profile or redesign C2/C3 routing.

### Official host identity path

Current state:

The hook is official and ledger-backed, but its config matcher only captures
`p2p_aesthetica` and the parser currently trusts any non-empty `agent_type`.

Required state:

```text
Allow-list exact supported host identities and classify custom versus host-default/generic without accepting arbitrary strings.
```

Evidence:

- `E0-P0A-HOOK1`: current source/config inspection.
- `E0-P0A-C07-1`: current limitation and C07 compatibility.
- `E0-P0A-GRAPH1`, `E0-P0A-IMPACT1`: fresh graph/impact evidence.

Relationship and impact:

- Related file count: one hook file plus direct config/test surfaces.
- Relationship summary: hook parses lifecycle payload and appends the existing ledger event.
- Impact note: source parser risk HIGH; graph file blast-radius LOW but identity authority is security-sensitive.

Classification:

partial.

Allowed next action:

Edit only allow-list/classification/secret validation and explicit matcher.

Forbidden next action:

Accept arbitrary `agent_type`, infer from prose, or replace the official hook.

### Live receipt boundary

Current state:

The live boundary correctly binds context, artifact, request, fresh host
receipt, output, and existing ledger, but lacks route metadata and explicit
requested-versus-observed mismatch codes.

Required state:

```text
Receipt contains route/capability intent plus observed host/session/turn/authority, and fails closed on missing/mismatch/stale evidence.
```

Evidence:

- `E0-P0A-LIVE1`: current source contract.
- `E0-P0A-GRAPH1`, `E0-P0A-IMPACT2`: fresh graph/impact evidence.

Relationship and impact:

- Related file count: one live boundary plus direct test surface.
- Relationship summary: `prepare_trial` writes request/manifest/fixture; `finalize_trial` validates host receipt, writes output/receipt, and appends live ledger event.
- Impact note: parser risk HIGH; preserve all current C06/C07 binding and proxy guards.

Classification:

partial.

Allowed next action:

Add schema-compatible metadata and exact failure taxonomy without changing mode/router behavior.

Forbidden next action:

Set `runtime_task_execution=true` from proxy or requested profile alone.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Hook/config now uses an explicit allow-list and secret rejection | complete; preserve and wait for host activation evidence |
| P1-B | Live receipt now records route/executor separation and exact mismatch/missing taxonomy | complete; preserve and require official host evidence for live certification |
| P1-C | Direct tests cover canonical/default/optional identity, route separation, fail-closed cases, and regressions | complete: focused 24/24, affected 54/54, full 111/111 |
| P2-A | Real default worker completed, but no fresh official default receipt was emitted | blocked; do not widen trust or accept prose |
| P2-B | Historical C07 AESTHETICA remains valid; fresh canonical probe had no official receipt | blocked; no fresh C09 proof accepted |
| P3-A | Candidate `.18`, package/lifecycle, doctor, drift, and full regression pass; no Git commit path exists | complete for executable gates, terminal Goal remains blocked on P2 |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable.
- [x] Phase Touch Map lists plan-relevant relationship files.
- [x] Phase Touch Map defines touch mode for every plan-relevant unit.
- [x] Correct parts are marked preserve-only.
- [x] Partial/unbound/blocked parts have exact next actions.
- [x] Blockers are recorded, including no Git metadata.
- [x] Next phase status assumptions and work steps are updated from P0 findings.
- [x] Status Refresh Log has an R0 baseline row.
- [x] After implementation begins, affected rows are refreshed from new evidence.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are ready.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. The current authority and evidence support a surgical
generalization of the existing official hook/live boundary. The route router,
capability registry, C07/C08 historical artifacts, and protected release
artifacts are preserve-only. The missing generic/default host identity must be
confirmed from the official host surface during P1/P2; if it cannot be
observed, this Goal must stop BLOCKED rather than widen trust.

## Final Goal Decision

- Result: `BLOCKED`.
- Mandatory gap: no fresh official host receipt for the supported generic/default
  worker or canonical `p2p_iris` worker.
- Completed: implementation, focused/full regression, candidate `.18` package
  verification, protected hash recheck, and independent review.
- Preserved: C08 scored trials `0`, historical C07 evidence, protected `.15`,
  `.16-r2`, `.17`, canonical denominator `8/8`, and one-router architecture.
- Resume condition: the current official host must emit a fresh allow-listed
  receipt with matching `agent_type`, `host_execution_id`, `session_id`, and
  `turn_id`; do not infer or widen the allow-list.
