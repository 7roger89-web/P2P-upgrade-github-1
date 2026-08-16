# P2P-C09 Supported Generic Host Identity and Route Observation Boundary Plan

## Metadata

- Date: `2026-08-14`
- Status: `BLOCKED` — implementation and validation complete; the current host emitted no fresh generic/default or canonical official identity receipt.
- Plan: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-actual-status.md`

## Goal

Close the C08 host-observation blocker by extending the existing official Codex
hook and live Execution Ledger boundary to prove supported host executor
identity for standard/non-UI, normal `p2p-uiux`, accessibility-heavy, and at
least one canonical custom-profile route. Receipts must preserve the
distinction between logical route/capability and the host executor that
actually ran, while remaining fail-closed and backward-readable for C07.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed; this environment has no `.git`, so record the unavailable result and do not fabricate commits.
- Do not modify or overwrite official `.15`, `.16-r2`, or current `.17`; if packaging is affected, create a new immutable candidate only through the existing mechanism.
- Do not rerun or score the frozen C08 benchmark; do not alter its preregistration, treatment, order, rubric, or non-inferiority margin.
- Use the existing hook, Execution Ledger, live receipt, router, and capability contracts. Do not create a second router, identity subsystem, ledger, agent, or quorum.
- Do not treat requested profile, prompt text, child prose, output style, private RPC, UI scraping, or proxy output as host identity evidence.
- Preserve `READ != WRITE`, `READ != LOG`, `READ != PERSIST`, `READ != EGRESS`, `INTENT != PERMISSION`; observe permission mode without expanding it.
- Keep all temporary verification roots under the repository `.tmp` directory.

## Problem

The existing official `SubagentStart` hook is configured with the matcher
`^p2p_aesthetica$`, and the hook accepts arbitrary non-empty `agent_type`
strings. C07 therefore proved only AESTHETICA-backed receipts. The live
boundary already requires a fresh official receipt, but its request/receipt
contract is profile-centric and does not record logical route/capability or
explicitly classify requested-versus-observed identity mismatches.

## Scope

- Recover and document the actual C1-C12 route semantics and current host path.
- Generalize the existing hook with an explicit allow-list for the eight canonical identities, `p2p_aesthetica`, and the supported host default identity discovered from the official host surface.
- Generalize the existing config matcher without adding `p2p-uiux` as an agent profile.
- Extend the existing live request/receipt fields with route/capability and host-observation fields, preserving old C07 receipt reading.
- Add fail-closed taxonomy and tests for missing, stale, wrong-session/turn, mismatched, unknown, secret-bearing, and proxy evidence.
- Run the minimum live probes: one standard/non-UI, one normal UI without AESTHETICA, one accessibility-heavy route using current selective semantics, and one canonical custom profile where supported.
- Run affected regression, package/lifecycle verification if runtime files changed, governance/doctor/security checks, and an independent Supervisor review.

## Non-Goals

- No C08 scored trials, quality scoring, blind review, A/B analysis, context-efficiency claim, cost claim, or non-inferiority claim.
- No routing-quality redesign for C2/C3 lexical ambiguity.
- No new `p2p-uiux`/`p2p_uiux` Codex profile, ninth canonical identity, host-observer agent, router agent, meta-agent, recursive delegation, scheduler, DAG, memory system, or provider integration.
- No promotion, release, deployment, merge, external communication, permission expansion, network enablement, hook framework replacement, or modification of protected artifacts.

## Requirements

- Logical route/capability and host executor identity are separate receipt values.
- Route evidence contains `logical_route`, `logical_capability`, and `requested_profile_if_any`.
- Host evidence contains `observed_host_agent_type`, `host_execution_id`, `session_id`, `turn_id`, and `identity_authority`.
- Host identity authority is an official Codex-owned hook/host surface, not worker self-identification.
- Canonical identities remain exactly eight with denominator `8` and full quorum `8/8`; AESTHETICA remains optional/noncanonical.
- Supported generic/default host identity is allow-listed and classified as `HOST_DEFAULT / GENERIC`; custom identities are classified as `CUSTOM_PROFILE`.
- Missing official host evidence yields `HOST_EVIDENCE_CAPTURE_FAILURE`.
- Supported requested/observed identity mismatch yields `HOST_IDENTITY_MISMATCH`; stale, wrong-session/turn, wrong execution ID, wrong artifact, tampered request, unknown identity, secret, and proxy cases fail closed.
- Existing C07 AESTHETICA receipts remain readable and valid.
- Observation does not select routes, add capabilities, change prompts/context/permissions, retry, or mutate routing.

## Acceptance Criteria

- Route/profile semantics for C1-C12 are recorded from current router/frozen C08 evidence, with C2/C3 ambiguity disclosed rather than redesigned.
- `p2p-uiux` is proven to be a `SKILL`, not a Codex custom profile.
- Existing AESTHETICA identity tests and historical C07 receipt semantics remain valid.
- Focused tests cover allow-listed canonical/custom/default identities, unknown identity rejection, route/profile separation, mismatch/missing/stale/session/turn failure, proxy non-promotion, secret rejection, no route mutation, no permission expansion, and canonical 8 safety.
- Live evidence contains true official host receipts, captured output, `runtime_task_execution=true`, matching request/artifact/context bindings, and no forced AESTHETICA for normal UI.
- Full affected regression and required package/lifecycle/doctor/governance/security checks pass, or a specific real blocker is recorded.
- `.15`, `.16-r2`, and `.17` hashes remain unchanged; any new candidate is immutable, hashed, unpromoted, and reported.
- Supervisor independently returns PASS for `SUPPORTED_ROUTE_WIDE_HOST_IDENTITY_READY`, or the final result is BLOCKED/REJECT with the exact evidence gap.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current route, host, artifact, and graph state.
  - Work Steps: inspect the frozen C08 route observation, C07 report/receipts, relevant SPEC cluster, hook/config/live boundary, canonical registry, agent profiles, artifact hashes, and no-Git environment; record classifications and next-phase decisions in actual-status.
  - Implementation Gate: no runtime or test editing starts until actual-status records evidence IDs, relationship counts, impact warnings, preserve-only paths, and a final P0 decision.
  - Acceptance: current route semantics, `p2p-uiux` type, host limitation, invariant family, and exact editable/preserve-only scope are evidenced.

### P1: Official identity and route-observation contract

- Phase Goal: extend the existing official host hook/live receipt boundary without changing routing or creating a second identity system.
- Phase Boundary:
  - In scope: `.p2p/system/scripts/p2p_host_identity_hook.py`, `.codex/config.toml`, `.p2p/system/p2p_capabilities/live_execution.py`, focused tests for those contracts.
  - Out of scope: router lexical behavior, C08 benchmark execution, protected artifacts, new profiles, new ledgers, and provider telemetry.
  - Dependencies: P0-A complete; current C07 live boundary and capability SPECs remain authoritative.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, then `P1-B`, then `P1-C`.
- Ordered Slice List:
  - P1-A: Allow-listed official host identities and matcher
  - P1-B: Route/executor observation fields and mismatch taxonomy
  - P1-C: Focused behavior and security regression tests

- [x] P1-A: Allow-listed official host identities and matcher
  - Goal: preserve AESTHETICA while capturing supported canonical custom profiles and the actual supported generic/default worker identity through the same official hook.
  - Scope Boundary:
    - Editable: `.p2p/system/scripts/p2p_host_identity_hook.py`, `.codex/config.toml`.
    - Inspect-only: `.codex/agents/*.toml`, host tool schema, historical C07 receipts.
    - Preserve-only: `.15`, `.16-r2`, `.17`, router implementation, permission settings, existing ledger lines.
    - Out of scope: arbitrary agent-type acceptance, profile creation, prompt/self-identification, routing decisions.
  - Non-Goals: no hook output, no retry, no child control, no secret capture, no live benchmark.
  - Pre-flight Questions:
    - Data source: official hook payload and host-supported agent-type surface only.
    - Display permission: N/A; receipt persistence is an audit boundary, not UI.
    - DB read flow: N/A; append/read existing JSONL Execution Ledger.
    - DB write flow: hook appends only the existing allow-listed receipt event.
    - Render location: N/A; JSONL receipt and tests.
    - UI behavior flow: N/A; normal UI semantics are recorded in P1-B/P2.
    - Docker runtime: N/A; non-UI standard-library runtime.
    - Playwright target: N/A; no public UI is changed.
    - Behavior test: hook payload -> allow-list -> receipt/ledger or ignored failure.
    - Cleanup/quarantine: synthetic ledgers under repo `.tmp`; never the project ledger for tests.
    - External side effects: none; live host probes are bounded and read-only.
    - N/A notes: package/lifecycle is deferred to P3 if runtime source changes.
  - Work Steps:
    1. Add explicit canonical, optional, and supported generic/default identity sets and identity-class helper; reject unknown arbitrary `agent_type` and secret-like allowed values while preserving old receipt schema readability.
       - UI flow check: N/A.
       - DB/data flow check: synthetic JSONL contains only valid official receipt fields.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): run the direct hook unit tests and CLI no-stdout check against repo-local temporary roots.
       - Evidence target: `E1-P1A-HOOK1`.
    2. Broaden the official matcher only to the explicit supported identities and verify no `p2p-uiux` profile or wildcard matcher is introduced.
       - UI flow check: N/A.
       - DB/data flow check: config remains observation-only and points to the existing hook.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): parse TOML and exercise matcher/config assertions.
       - Evidence target: `E1-P1A-CONFIG1`.
  - Implementation Gate:
    - Before editing target files, run the relevant Anvien file-detail and impact evidence already refreshed for the hook; record the high file-risk warning and low upstream blast-radius summary.
    - `P0-A` actual-status is complete and the supported default identity is confirmed from the official host surface before adding it.
  - Acceptance:
    - Source: hook allow-list is explicit and historical AESTHETICA receipts remain valid.
    - Runtime/UI: official hook still emits no stdout and never changes child execution.
    - DB/data: only allow-listed receipt fields are persisted; unknown/secret payloads produce no receipt.
    - Behavior test: positive AESTHETICA/custom/default and negative unknown/secret cases pass.
    - Cleanup/quarantine: all synthetic ledgers are repo-local and removed/quarantined.
    - Evidence IDs: `E1-P1A-HOOK1`, `E1-P1A-CONFIG1`.
    - Actual-status rows refreshed: hook/config transition `partial -> correct` if tests prove it.
  - Evidence Targets: allow-list source lines, config matcher, focused test output, secret scan.
  - Actual-status Update: refresh hook/config rows before P1-B.
  - Commit Boundary: commit after this slice when acceptance passes; if Git remains unavailable, record the exact Anvien/Git limitation and do not claim a commit.

- [x] P1-B: Route/executor observation fields and mismatch taxonomy
  - Goal: make the existing live receipt distinguish intended logical route/capability from observed official host executor identity and fail closed on mismatch or stale evidence.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/live_execution.py` and its direct test file only as required after production behavior exists.
    - Inspect-only: `.p2p/system/p2p_capabilities/context.py`, router source, historical C07 receipt artifacts.
    - Preserve-only: C06 mode semantics, C07 schema compatibility, artifact binding, context binding, output/ledger integration.
    - Out of scope: route selection, provider telemetry, context-mode redesign, new ledger.
  - Non-Goals: no inference from prose/output and no fallback from missing host receipt to proxy/live.
  - Pre-flight Questions:
    - Data source: explicit route observation supplied by the existing live caller plus official hook receipt.
    - Display permission: N/A.
    - DB read flow: read existing host identity JSONL; append existing live receipt event.
    - DB write flow: add only schema-compatible fields to existing request/receipt artifacts.
    - Render location: existing trial `request.json`, `receipt.json`, `output.txt`, and Execution Ledger.
    - UI behavior flow: normal UI route is metadata only; router output remains unchanged.
    - Docker runtime: N/A; standard-library development runtime.
    - Playwright target: N/A.
    - Behavior test: prepared route -> official receipt -> output/live receipt or exact fail-closed error.
    - Cleanup/quarantine: each test creates a new repo-local `.tmp` project/trial root and removes it.
    - External side effects: one bounded host handoff per live probe later; no external network.
    - N/A notes: no database or public app surface.
  - Work Steps:
    1. Add validated route observation metadata with logical route, logical capability, supporting capability data where needed, requested profile-if-any, and executor class; preserve defaults for historical callers.
       - UI flow check: N/A; verify router output is byte/shape-equivalent for unchanged requests.
       - DB/data flow check: request and receipt bind the metadata without storing prompts/secrets.
       - Render location check: inspect trial request/receipt JSON fields.
       - Mini QA for each completed implementation slice (MUST): run direct preparation/finalization tests for standard, UI, accessibility, and custom metadata.
       - Evidence target: `E1-P1B-ROUTE1`.
    2. Match host execution ID and optional session/turn values against a fresh allow-listed official receipt; emit `HOST_IDENTITY_MISMATCH` or `HOST_EVIDENCE_CAPTURE_FAILURE` instead of generic missing proof, while retaining stale/request/artifact failure paths.
       - UI flow check: N/A.
       - DB/data flow check: top-level receipt records requested and observed identities, host/session/turn IDs, and identity authority.
       - Render location check: `receipt.json` and live ledger event are inspected independently.
       - Mini QA for each completed implementation slice (MUST): run positive, mismatch, missing, stale, wrong-session/turn, wrong-ID, proxy, and tamper cases.
       - Evidence target: `E1-P1B-FAILCLOSED1`.
  - Implementation Gate:
    - Before editing `live_execution.py`, use its refreshed Anvien file-detail/impact evidence; treat the high parser risk and 28-symbol upstream blast-radius result as a scope warning requiring narrow edits.
    - Do not change `CONDITION_MODES`, `SUPPORTED_SCENARIOS`, `runtime_task_execution`, artifact binding, context reconstruction, or proxy semantics except to add route/identity evidence.
  - Acceptance:
    - Source: existing live boundary remains the only receipt/ledger integration.
    - Runtime/UI: route metadata never changes `classify_request` or permissions.
    - DB/data: request/receipt carries both intended and observed identity with official authority.
    - Behavior test: missing/mismatch/stale/session/turn/unknown/proxy paths fail closed.
    - Cleanup/quarantine: no test writes the real project ledger or protected artifacts.
    - Evidence IDs: `E1-P1B-ROUTE1`, `E1-P1B-FAILCLOSED1`.
    - Actual-status rows refreshed: live boundary transition `partial -> correct` only after direct tests pass.
  - Evidence Targets: source diff, Anvien impact, focused test output, receipt fixtures and hashes.
  - Actual-status Update: refresh live boundary and C07 compatibility rows before P1-C.
  - Commit Boundary: commit after this slice when acceptance passes; record no-Git limitation if applicable.

- [x] P1-C: Focused behavior and security regression tests
  - Goal: prove the implemented invariant family across positive, negative, compatibility, routing, permission, and security cases.
  - Scope Boundary:
    - Editable: `tests/test_p2p_host_identity_receipt.py`, `tests/test_p2p_live_execution.py`, and a narrowly scoped route/registry test only if required.
    - Inspect-only: production sources after P1-A/P1-B behavior is complete.
    - Preserve-only: frozen C08 fixtures and benchmark artifacts.
    - Out of scope: benchmark quality scoring and unrelated suite cleanup.
  - Non-Goals: no static-only proof; tests must exercise trigger -> processing -> observable receipt/error.
  - Pre-flight Questions:
    - Data source: production hook/live boundary and current router/registry.
    - Display permission: N/A.
    - DB read flow: synthetic ledger read/write in isolated temp roots.
    - DB write flow: test-only fixture ledgers; cleanup in tearDown.
    - Render location: N/A.
    - UI behavior flow: route output comparison only.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: direct runtime tests are the primary evidence.
    - Cleanup/quarantine: existing test temp-root convention under `.tmp`.
    - External side effects: none.
    - N/A notes: package lifecycle later.
  - Work Steps:
    1. Update/add tests only after production behavior is verified, covering allow-list, identity class, exact matcher, historical AESTHETICA, canonical custom, generic/default, unknown, secret, no stdout, and no routing/permission mutation.
       - UI flow check: N/A.
       - DB/data flow check: receipt/ledger fields and absence cases are asserted.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): focused unittest command.
       - Evidence target: `E1-P1C-IDENTITYTEST1`.
    2. Add route/host separation and fail-closed live tests, then run the entire affected focused command.
       - UI flow check: normal UI does not call AESTHETICA and is not assigned a fake profile.
       - DB/data flow check: route metadata and observed host receipt remain distinct.
       - Render location check: request/receipt JSON inspected.
       - Mini QA for each completed implementation slice (MUST): focused unittest command plus config/registry checks.
       - Evidence target: `E1-P1C-LIVETEST1`.
  - Implementation Gate:
    - Production behavior from P1-A/P1-B exists and no test is being used as a substitute for implementation.
  - Acceptance:
    - Source: direct tests name the affected behavior and failure codes.
    - Runtime/UI: current router policy matrix remains unchanged.
    - DB/data: isolation and secret absence are proven.
    - Behavior test: focused suite passes.
    - Cleanup/quarantine: temp roots are cleaned.
    - Evidence IDs: `E1-P1C-IDENTITYTEST1`, `E1-P1C-LIVETEST1`.
    - Actual-status rows refreshed: focused coverage is complete.
  - Evidence Targets: test names/files/results, route matrix, secret scan.
  - Actual-status Update: mark P1 complete only after all focused tests pass.
  - Commit Boundary: commit after this slice when acceptance passes; record no-Git limitation if applicable.

### P2: Minimum live host proofs

- Phase Goal: prove supported host-owned identity at the real native boundary for the minimum route classes without scoring C08.
- Phase Boundary:
  - In scope: bounded read-only/synthetic live probes and isolated evidence under `.tmp/p2p-c09-live-*` plus route/receipt summaries.
  - Out of scope: C08 A/B trials, quality scoring, provider telemetry, extra canonical workers, route redesign, or recursive delegation.
  - Dependencies: P1 focused tests pass; official host tool supports the selected worker/profile; no protected artifact mutation.
- Phase Implementation Rule: do not multiply provider calls; reuse one evidence record only where the route/identity semantics are genuinely identical.
- Ordered Slice List:
  - P2-A: Standard/non-UI and normal `p2p-uiux` default-worker proofs
  - P2-B: Accessibility-heavy AESTHETICA and canonical custom-profile proof

- [blocked] P2-A: Standard/non-UI and normal `p2p-uiux` default-worker proofs
  - Goal: prove a supported generic/default host executor for C1-class standard work and C6-class normal UI without AESTHETICA.
  - Scope Boundary:
    - Editable: new evidence files only under a new repo-local `.tmp` probe root.
    - Inspect-only: current runtime and host receipts.
    - Preserve-only: project state, release artifacts, C08 preregistration.
    - Out of scope: scored A/B trials and permanent state mutation.
  - Non-Goals: no profile invention; no claim that default is a ninth P2P identity.
  - Pre-flight Questions:
    - Data source: actual official host hook receipt, host execution output, route metadata, and request/receipt hashes.
    - Display permission: read-only host worker only.
    - DB read flow: existing project Execution Ledger read; new live evidence append is bounded and reversible/quarantined.
    - DB write flow: isolated trial artifacts only; no project source writes.
    - Render location: `.tmp/p2p-c09-live-*` JSON/text evidence.
    - UI behavior flow: normal UI route records `p2p-uiux` skill with no AESTHETICA call/profile.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: real host output plus official receipt and `runtime_task_execution=true`.
    - Cleanup/quarantine: preserve evidence root for audit, outside source-of-truth; do not reuse trial IDs.
    - External side effects: one bounded host worker call per distinct route class.
    - N/A notes: no benchmark scoring.
  - Work Steps:
    1. Run one read-only standard/non-UI probe with the supported generic/default worker and explicit `logical_route=standard-p2p`.
       - UI flow check: N/A.
       - DB/data flow check: official receipt matches host execution ID and route receipt is ledger-bound.
       - Render location check: inspect output and receipt.
       - Mini QA for each completed implementation slice (MUST): independent receipt/hash check.
       - Evidence target: `E2-P2A-NONUI1`.
    2. Run one normal UI probe with `logical_route=p2p-uiux`, `logical_capability=p2p-uiux`, no requested custom profile, and default host executor; verify `call_aesthetica=false`/no AESTHETICA identity.
       - UI flow check: route decision remains p2p-uiux primary.
       - DB/data flow check: receipt says intended skill route versus observed default host identity.
       - Render location check: inspect route decision, output, receipt, and ledger.
       - Mini QA for each completed implementation slice (MUST): independent route/identity check.
       - Evidence target: `E2-P2A-NORMALUI1`.
  - Implementation Gate:
    - P1 tests pass; host hook matcher captures the actual supported default identity; no AESTHETICA is forced.
  - Acceptance:
    - Source: no permanent source files are edited by the probes.
    - Runtime/UI: both real host executions complete read-only.
    - DB/data: official host receipt, route metadata, output hash, and true runtime flag are present.
    - Behavior test: default identity is host-owned and distinct from logical route/capability.
    - Cleanup/quarantine: new isolated evidence roots are preserved and not reused.
    - Evidence IDs: `E2-P2A-NONUI1`, `E2-P2A-NORMALUI1`.
    - Actual-status rows refreshed: generic/default and normal UI proof become correct.
  - Evidence Targets: live receipt/ledger/output hashes, host/session/turn IDs, route decision.
  - Actual-status Update: refresh P2 live proof rows before P2-B.
  - Commit Boundary: evidence-only; no code commit. Record no-Git environment if the overall plan needs a checkpoint.

- [blocked] P2-B: Accessibility-heavy AESTHETICA and canonical custom-profile proof
  - Goal: preserve selective AESTHETICA semantics for C7 and prove one exact canonical custom profile where the host supports it.
  - Scope Boundary:
    - Editable: new evidence files only under a new repo-local `.tmp` probe root.
    - Inspect-only: router/registry/profile definitions and current C07 receipts.
    - Preserve-only: C07 historical evidence and selective route policy.
    - Out of scope: all-eight ceremony and C08 scoring.
  - Non-Goals: no canonical denominator change and no p2p-uiux profile.
  - Pre-flight Questions:
    - Data source: official host hook receipts and current route policy.
    - Display permission: AESTHETICA profile remains read-only; canonical profile task remains synthetic/read-only.
    - DB read flow: existing ledger plus isolated evidence.
    - DB write flow: isolated probe artifacts only.
    - Render location: `.tmp/p2p-c09-live-*`.
    - UI behavior flow: C7 route is p2p-uiux primary with optional AESTHETICA supporting eligibility.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: exact observed host type and class match requested profile.
    - Cleanup/quarantine: preserve new evidence, no reuse.
    - External side effects: one AESTHETICA and one canonical worker call at most.
    - N/A notes: no quality score.
  - Work Steps:
    1. Run one C7-class read-only accessibility-heavy probe using the current router policy and exact `p2p_aesthetica` host profile; record optional/noncanonical status.
       - UI flow check: AESTHETICA is selected only because the router marks `ACCESSIBILITY_HEAVY`.
       - DB/data flow check: route and supporting capability remain distinct from observed profile.
       - Render location check: inspect receipt/output/ledger.
       - Mini QA for each completed implementation slice (MUST): independent receipt/hash check.
       - Evidence target: `E2-P2B-A11Y1`.
    2. Run one safe canonical custom-profile probe, preferably `p2p_iris`, and require exact host-owned `agent_type` equality.
       - UI flow check: N/A.
       - DB/data flow check: `requested_profile_if_any` and `observed_host_agent_type` match exactly; canonical count remains eight.
       - Render location check: inspect output/receipt/ledger.
       - Mini QA for each completed implementation slice (MUST): independent identity-class/quorum check.
       - Evidence target: `E2-P2B-CANONICAL1`.
  - Implementation Gate:
    - AESTHETICA profile is current/validated; canonical profile is present and host-resolvable; no extra worker is required.
  - Acceptance:
    - Source: no permanent source files are edited by probes.
    - Runtime/UI: C7 is selective and canonical proof is exact.
    - DB/data: fresh official receipt and output binding exist for both.
    - Behavior test: AESTHETICA is optional/noncanonical; canonical identity is exact.
    - Cleanup/quarantine: isolated evidence roots are preserved and not reused.
    - Evidence IDs: `E2-P2B-A11Y1`, `E2-P2B-CANONICAL1`.
    - Actual-status rows refreshed: AESTHETICA compatibility and canonical proof become correct.
  - Evidence Targets: route decision, receipt class, official authority, host/session/turn IDs, output hashes.
  - Actual-status Update: refresh all live coverage rows before P3.
  - Commit Boundary: evidence-only; no code commit.

### P3: Regression, lifecycle, and independent review

- Phase Goal: verify the full affected development-source package boundary and produce a terminal honest result.
- Phase Boundary:
  - In scope: focused/full tests, Decision Trace, governance drift, capability validation, doctor, security/secret scans, package/lifecycle if runtime changed, C07 compatibility, Supervisor report.
  - Out of scope: release promotion, user approval execution, C08 benchmark, optional hardening after PASS.
  - Dependencies: P1 and minimum P2 evidence complete.
- Phase Implementation Rule: close only at PASS, BLOCKED, or REJECT; do not continue after PASS.
- Ordered Slice List:
  - P3-A: Affected regression and package/lifecycle gates
  - P3-B: Supervisor review and terminal closure

- [blocked] P3-A: Affected regression and package/lifecycle gates
  - Goal: prove no regression across the affected invariant family and create a new immutable candidate only if runtime/package source changed.
  - Scope Boundary:
    - Editable: repo-local test/evidence outputs and a new candidate path through the canonical packaging script if required.
    - Inspect-only: protected `.15`, `.16-r2`, `.17` artifacts and frozen C08 material.
    - Preserve-only: all historical C07 evidence and current treatment.
    - Out of scope: promotion, deployment, merge, or release approval.
  - Non-Goals: no benchmark quality or cost analysis.
  - Pre-flight Questions:
    - Data source: source tests, package checksums, lifecycle fixtures, governance reports.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: lifecycle fixtures must use temporary roots and cleanup/quarantine.
    - Render location: `.tmp` logs and plan evidence.
    - UI behavior flow: N/A.
    - Docker runtime: N/A unless a project-native build requires it; this package is standard-library Python.
    - Playwright target: N/A.
    - Behavior test: full suite and nearest real boundaries.
    - Cleanup/quarantine: all temporary package/lifecycle roots under `.tmp`.
    - External side effects: none.
    - N/A notes: package hash is benchmark evidence if candidate is produced.
  - Work Steps:
    1. Run focused tests, full unittest suite, Decision Trace, capability/doctor/governance/drift/security scans, and inspect exact results.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: inspect reports/logs.
       - Mini QA for each completed implementation slice (MUST): nearest real boundary commands.
       - Evidence target: `E3-P3A-REGRESSION1`.
    2. If runtime/package files changed, create a new immutable candidate with existing version/hash rules, then run package verify, portable doctor, fresh install, upgrade from `.15`, and same-version reinstall without promotion.
       - UI flow check: N/A.
       - DB/data flow check: lifecycle isolation and rollback/quarantine.
       - Render location check: candidate manifest/hash and lifecycle result.
       - Mini QA for each completed implementation slice (MUST): independent artifact hash check.
       - Evidence target: `E3-P3A-PACKAGE1`.
  - Implementation Gate:
    - All required focused/live evidence exists; protected artifact hashes are recorded before any candidate build.
  - Acceptance:
    - Source: regression passes or real blocker is recorded.
    - Runtime/UI: nearest real runtime boundaries are checked.
    - DB/data: no protected root is mutated.
    - Behavior test: full affected suite passes.
    - Cleanup/quarantine: temporary outputs are confined to `.tmp`.
    - Evidence IDs: `E3-P3A-REGRESSION1`, `E3-P3A-PACKAGE1` when applicable.
    - Actual-status rows refreshed: all P3 gates have explicit statuses.
  - Evidence Targets: commands/results, scans, package/lifecycle hashes, immutable artifact checks.
  - Actual-status Update: update final gate matrix before Supervisor.
  - Commit Boundary: run Anvien detect-changes before any claimed commit; no Git means no commit claim.

- [x] P3-B: Supervisor review and terminal closure
  - Goal: independently decide whether `SUPPORTED_ROUTE_WIDE_HOST_IDENTITY_READY` is proven.
  - Scope Boundary:
    - Editable: review report and plan evidence/status files only.
    - Inspect-only: all production changes, receipts, ledger events, artifacts, tests, and reports.
    - Preserve-only: protected releases and C08 experiment.
    - Out of scope: implementation repair during review and optional hardening.
  - Non-Goals: no release approval and no C08 rerun.
  - Pre-flight Questions:
    - Data source: current source, fresh Anvien evidence, live artifacts, tests, and gate reports.
    - Display permission: N/A.
    - DB read flow: inspect existing ledger; no writes during review.
    - DB write flow: review report only.
    - Render location: `reports/supervisor/` and plan evidence.
    - UI behavior flow: verify normal UI route does not force AESTHETICA.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: independent review against every HI condition.
    - Cleanup/quarantine: no review temp mutation.
    - External side effects: none.
    - N/A notes: final result is PASS/BLOCKED/REJECT only.
  - Work Steps:
    1. Review source/diff, invariant family, route/profile distinction, official authority, fail-closed cases, security, historical compatibility, package hashes, and no-C08-contamination evidence.
       - UI flow check: verify C6/C7 selective route claims.
       - DB/data flow check: verify ledger/receipt provenance and IDs.
       - Render location check: review report path and status.
       - Mini QA for each completed implementation slice (MUST): supervisor evidence protocol.
       - Evidence target: `E3-P3B-SUPERVISOR1`.
    2. Write the terminal result, refresh actual-status/evidence/benchmark, run the workflow report, and stop.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: final report is traceable.
       - Mini QA for each completed implementation slice (MUST): final status/hash check.
       - Evidence target: `E3-P3B-CLOSURE1`.
  - Implementation Gate:
    - P3-A complete or explicitly blocked; all mandatory evidence is fresh and source-inspected.
  - Acceptance:
    - Source: Supervisor verdict is exactly PASS or an evidence-backed REJECT/BLOCKED result.
    - Runtime/UI: all minimum route classes are covered or blocker is explicit.
    - DB/data: receipt/ledger provenance is independently cleared.
    - Behavior test: no residual same-invariant unverified surface remains for PASS.
    - Cleanup/quarantine: plan artifacts and evidence are consistent.
    - Evidence IDs: `E3-P3B-SUPERVISOR1`, `E3-P3B-CLOSURE1`.
    - Actual-status rows refreshed: final status and next Goal recorded.
  - Evidence Targets: Supervisor report, workflow terminal report, final hashes/status.
  - Actual-status Update: mark terminal state and stop rule.
  - Commit Boundary: no further implementation after terminal PASS/BLOCKED/REJECT.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow/skill for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: supervisor review passes, or the plan records a blocker with evidence and no closure is performed.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted plan.
  - Work Steps:
    1. Review files, reports, temporary outputs, and plan artifacts created or modified during this plan.
    2. Remove or rewrite only plan-created dead artifacts; preserve historical C07/C08 evidence.
    3. Verify no rejected approach or stale placeholder remains in the final plan scope.
    4. Call supervisor to review the cleanup.
  - Implementation Gate: only plan-created artifacts are candidates for cleanup.
  - Acceptance: final evidence contains no dead plan-created artifacts and cleanup is independently reviewed.
- [x] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, candidate hash, and terminal status.
  - Work Steps:
    1. Run required final validation and package/lifecycle checks when applicable.
    2. Run Anvien detect-changes; record no-Git limitation if it cannot run.
    3. Record final evidence, benchmark measurements, Supervisor verdict, and workflow terminal report.
    4. Stop after PASS, BLOCKED, or REJECT.
  - Implementation Gate: Pn-A and Pn-B pass or record a real blocker.
  - Acceptance: final evidence is complete, protected hashes are unchanged, and the terminal state is known.

## Risk Notes

- Anvien reports high parser/file risk for the hook, live boundary, and router; file-level upstream blast radius is currently low but the invariant is cross-file and must be verified behaviorally.
- The environment has no `.git`; no commit or diff claim may be fabricated. Existing C07 precedent records this limitation.
- The actual generic host string must come from the supported host surface/live receipt. If it is not observable or not stable enough, stop with BLOCKED rather than widening the allow-list.
- Historical C07 receipts are `/1` and must remain readable; new fields must be optional or versioned cleanly.
- C2/C3 lexical routing ambiguity is a disclosed out-of-scope issue; changing it would be routing redesign and invalidate this Goal boundary.
- A new candidate may be required because runtime/package source changes; promotion is out of scope and requires separate protected gates.

## Terminal status

`BLOCKED`. P0 and all local implementation/regression/package work are
complete. The two real supported-host probes completed without fresh official
ledger receipts (`default` and `p2p_iris`), so P2 minimum live proof and the
route-wide readiness claim cannot pass. The next run must begin by restoring
the host-owned `SubagentStart` emission/config path and then re-run only the
missing bounded proofs; it must not widen the allow-list, infer identity from
worker prose, or rerun C08.
