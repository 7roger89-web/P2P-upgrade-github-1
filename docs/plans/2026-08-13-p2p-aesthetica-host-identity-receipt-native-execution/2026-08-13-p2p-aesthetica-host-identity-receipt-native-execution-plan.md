# P2P Aesthetica — Host Identity Receipt and Native Execution Completion Plan

## Metadata

- Date: `2026-08-13`
- Status: `blocked`
- Plan: `docs/plans/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution-actual-status.md`

## Goal

Establish a truthful, host-owned identity receipt for Codex 0.147.0 native
subagent lifecycle hooks, reuse the existing P2P execution ledger, prove one
real native `p2p_aesthetica` delegation when the Desktop coordinator can expose
it, and condition P2P UI/UX specialist routing on that receipt. The result must
either be a certified native path, a limited routing certification, a precise
named-delegation failure, or a host-hook blocker; it must never infer identity
from a profile, child self-report, nickname, or simulated test.

## Rules

- Complete P0 actual status before implementation work.
- Keep the eight canonical identities and `8/8` denominator unchanged.
- Keep `p2p_aesthetica` optional/supporting and excluded from the denominator.
- Reuse `.p2p/state/execution-ledger.jsonl`; do not create a second ledger,
  router, FACT authority, or Decision Trace system.
- Accept only official `SubagentStart`/`SubagentStop` lifecycle fields. Do not
  use AgentControl, private APIs, undocumented spawn RPCs, source/binary
  patching, generic impersonation, or child self-identification.
- The hook is standard-library-only, local, fail-closed for receipt creation,
  emits no prompt/reasoning/transcript/environment data, and exits successfully
  so malformed or unexpected input cannot alter child execution.
- Synthetic parser tests prove parsing and safety only; they are never host
  identity proof.
- Do not touch the immutable baseline, v5 artifact, App Game Truyện,
  Logistics, or any user project.
- Use only repo-local `.tmp` paths for temporary data. No hook network, cloud
  memory, connector, dependency install, proxy, or external download.
- Run Anvien `file-detail` and impact evidence before editing applicable
  visible code; hidden `.p2p/system` paths are direct-inspection-only because
  the current index excludes them. Run change detection before closure; there
  is no Git repository in this checkout, so commit evidence may be `N/A` with
  the exact error recorded.
- Full build means the project’s applicable release/package validation. Docker
  and browser evidence are `N/A` because this is a local hook/CLI contract, not
  an application runtime; no dev-server substitute is allowed.

## Problem

The project already has an official-schema `p2p_aesthetica` profile, a single
P2P UI/UX router, readiness states, and a native execution ledger. Its current
optional-specialist readiness can reach `RESOLVED` from profile presence and
test-projected booleans, but it has no receipt proving that the Codex host
actually launched the child with `agent_type = "p2p_aesthetica"`. The current
`.codex/config.toml` also has no project hook. Existing `.9` recovery evidence
proves thread metadata in historical runs, not the requested official hook
receipt.

## Scope

- Verify official hook support and source-level `agent_type` provenance on the
  installed Codex version.
- Add one minimal stdlib hook/parser contract under the installed runtime and
  configure the trusted project’s `.codex` layer.
- Record only a minimal `p2p-host-subagent-identity/1` receipt inside the
  existing execution ledger with deterministic duplicate handling.
- Add synthetic parser/security tests A–F and a host-proof validator requiring
  an exact receipt with `agent_type == "p2p_aesthetica"`.
- Attempt one real native Desktop delegation through the current coordinator;
  accept only the official receipt and exact child ID/type/source.
- Audit the existing `p2p-uiux` route and, only after a real identity pass,
  make the smallest instruction change needed to say “Have
  `p2p_aesthetica` perform the bounded specialist review. Wait for completion.”
- Exercise Vietnamese beginner UI, backend negative, small UI restraint, and
  unavailable fallback behavior; verify readiness, security, canonical quorum,
  optional exclusion, and no duplicate governance system.
- Prepare a new package only if changed runtime/config/instruction files make
  it necessary, subject to the project’s technical gates and user approval.

## Non-Goals

- No ninth canonical agent, no quorum denominator change, and no Aesthetica vote.
- No automatic installation of packages, hooks, MCP, runtimes, or connectors.
- No edits to existing user projects or release/v5/immutable-baseline artifacts.
- No broad refactor of `p2p_uiux`, readiness, workflow, or Decision Trace.
- No external network request from the hook or test fixture.
- No release promotion, deployment, merge, publish, or approval self-action.
- No claim of native certification if the Desktop coordinator cannot produce an
  official hook receipt.

## Requirements

1. Host gate: local `codex --version` is `0.147.0`; official docs and exact
   `rust-v0.147.0` source establish `SubagentStart`/`SubagentStop`, matcher
   `agent_type`, and `ThreadSpawn.agent_role -> agent_type` provenance.
2. Receipt contract: schema, lifecycle event, timestamp, session/turn/agent
   IDs, exact agent type, permission mode, model, cwd, and source are present;
   transcript contents, prompts, reasoning, secrets, and environment are not.
3. Parser gate: A exact Aesthetica passes; B default role, C missing type, D
   malformed JSON, E sensitive fields, and F duplicate receipt behave exactly
   as specified in the attachment.
4. Proof gate: only a persisted official receipt with exact
   `agent_type == "p2p_aesthetica"` proves identity; a missing, mismatched,
   malformed, or self-authored result falls back safely.
5. Routing gate: the existing single router remains authoritative; Aesthetica
   is never counted in `8/8`, and absence of host proof yields
   `PROFILE_UNAVAILABLE`/limited fallback rather than simulation.
6. Packaging gate: if runtime/config/instruction files change, run clean build,
   fresh install, upgrade, reinstall, doctor, drift, manifest/lock checks, and
   applicable regression; do not silently repair unrelated stale metadata.

## Acceptance Criteria

- The final classification is exactly one of:
  `NATIVE_P2P_EXECUTION_PATH_CERTIFIED`,
  `NATIVE_IDENTITY_CERTIFIED_P2P_ROUTING_LIMITED`,
  `NAMED_DELEGATION_NOT_VERIFIED`, or
  `BLOCKED_HOST_HOOK_UNAVAILABLE`.
- The final report contains the 31 requested fields from the attachment,
  including source references, exact receipt evidence, truth-table outcomes,
  readiness, security, package status, and user action.
- No “proof” relies on a profile file, nickname, child text, synthetic input,
  or historical thread metadata alone.
- Every changed slice has direct behavior evidence, actual-status refresh,
  security check, and Anvien/change-detection evidence where applicable.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect official host support, project config, ledger, router,
    specialist readiness, packaging, tests, and Anvien relationship evidence.
  - Implementation Gate: complete in `actual-status.md` before source edits.
  - Acceptance: each target surface is classified with evidence IDs.

### P1: Host receipt contract and trusted project hook

- Phase Goal: implement one minimal, safe, ledger-backed receipt path without
  changing P2P routing or claiming host proof.
- Phase Boundary:
  - In scope: new stdlib receipt/hook runtime, `.codex/config.toml` hook entry,
    parser/security unit tests, existing ledger append/dedupe contract.
  - Out of scope: real delegation, routing instruction, release artifact,
    Decision Trace changes, and user projects.
  - Dependencies: P0 complete; official hook schema/source evidence.
- Phase Implementation Rule: implement slices in order and refresh status after
  each slice.
- Ordered Slice List:
  - P1-A: Add receipt parser/validator and ledger append contract.
  - P1-B: Configure the trusted project hook and synthetic A–F tests.

- [x] P1-A: Add receipt parser/validator and ledger append contract.
  - Goal: create a single importable stdlib module that accepts one official
    lifecycle JSON object, sanitizes by allow-list, validates IDs/types, and
    appends deterministic receipt events to the existing execution ledger.
  - Scope Boundary:
    - Editable: `.p2p/system/scripts/p2p_host_identity_hook.py` and its focused
      test surface.
    - Inspect-only: `scripts/p2p_workflow.py`, `decision_trace.py`, ledger
      consumers, and official Codex source.
    - Preserve-only: existing ledger schema, Decision Trace schema, canonical
      registry, and profile.
    - Out of scope: hook config and router skill text until P1-B/P2 gates.
  - Non-Goals: no prompt/transcript storage, no network, no imports from
    third-party packages, no child behavior control.
  - Pre-flight Questions:
    - Data source: one JSON object on stdin from official Codex hooks.
    - Display permission: local ledger/audit only; no user-facing raw payload.
    - DB read flow: N/A; JSONL ledger read/dedupe flow.
    - DB write flow: allow-listed receipt -> existing `.p2p/state/execution-ledger.jsonl`.
    - Render location: N/A; CLI/test JSON summary only.
    - UI behavior flow: N/A; hook lifecycle.
    - Docker runtime: N/A; no application runtime.
    - Playwright target: N/A; no browser surface.
    - Behavior test: parser cases A–F and exact receipt validator.
    - Cleanup/quarantine: all tests use repo-local `.tmp` temporary roots and
      delete/quarantine their fixture ledgers.
    - External side effects: none beyond the explicitly scoped local ledger.
    - N/A notes: host proof is deferred to P2-B.
  - Work Steps:
    1. Implement the allow-list parser, exact event/type validation, redaction
       policy, receipt schema, deterministic key, and append/dedupe behavior.
       - UI flow check: N/A.
       - DB/data flow check: prove one ledger line per unique lifecycle key.
       - Render location check: N/A.
       - Evidence target: source inspection and focused parser test output.
    2. Expose a proof function that returns true only for a persisted official
       receipt whose exact `agent_type` is `p2p_aesthetica`.
       - UI flow check: N/A.
       - DB/data flow check: missing/mismatch/unknown source returns false.
       - Render location check: N/A.
       - Evidence target: truth-table tests and security scan.
  - Implementation Gate:
    - Before editing, retain P0 Anvien evidence and direct hidden-runtime
      inspection. The hidden path is not indexed; do not expand scope to the
      high-risk workflow or Decision Trace file.
    - No code can call a spawn API or trust child-authored content.
  - Acceptance:
    - Source: module is stdlib-only and imports cleanly.
    - Runtime/UI: hook summary is quiet/safe; no UI runtime applies.
    - DB/data: receipt lines use the existing `p2p-execution-event/1` ledger and
      repeated keys do not duplicate.
    - Behavior test: A–F pass with explicit invalid/no-write outcomes.
    - Cleanup/quarantine: no persistent test fixture remains outside `.tmp`.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-TEST2`.
    - Actual-status rows refreshed: receipt path and ledger transition to
      `missing -> correct`; host proof remains `unverified`.
  - Evidence Targets: module path, AST/import check, focused test output,
    ledger line shape, secret absence, and duplicate count.
  - Actual-status Update: mark the receipt contract correct only after all A–F
    synthetic tests pass.
  - Commit Boundary: commit after this slice when acceptance passes; Git is
    unavailable in the current checkout, so record `N/A` if unchanged.

- [x] P1-B: Configure the trusted project hook and synthetic A–F tests.
  - Goal: bind `SubagentStart` (and parser support for `SubagentStop`) to the
    project-local hook without machine-specific paths or child interruption.
  - Scope Boundary:
    - Editable: `.codex/config.toml`, focused tests, and hook entry only.
    - Inspect-only: user/global `C:\Users\Admin\.codex\config.toml`.
    - Preserve-only: existing agent TOML and all unrelated config.
    - Out of scope: real native child and P2P skill text.
  - Non-Goals: no `--dangerously-bypass-hook-trust`, global hook install, or
    secret/environment pass-through.
  - Pre-flight Questions:
    - Data source: Codex official hook stdin contract.
    - Display permission: trusted local project only.
    - DB read flow: hook reads/dedupes the existing project ledger.
    - DB write flow: hook appends minimal receipts only.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: config parse plus subprocess stdin fixtures.
    - Cleanup/quarantine: `.tmp` roots and isolated ledgers.
    - External side effects: local config and ledger only.
    - N/A notes: the hook cannot independently establish that Codex invoked it.
  - Work Steps:
    1. Add the project-local `SubagentStart` command using a portable relative
       command and verify TOML shape against the official config schema.
       - UI flow check: N/A.
       - DB/data flow check: isolated ledger only.
       - Render location check: N/A.
       - Evidence target: config parse and hook subprocess output/exit code.
    2. Add cases A–F, including default/missing type, malformed JSON, injected
       sensitive fields, and exact duplicate replay.
       - UI flow check: N/A.
       - DB/data flow check: no sensitive field is persisted.
       - Render location check: N/A.
       - Evidence target: focused test report.
  - Implementation Gate: only after P1-A source and impact evidence; no hook
    output may become developer context or expose raw payload.
  - Acceptance:
    - Source: project config is valid and only the named project changes.
    - Runtime/UI: hook exits 0 for valid/invalid input and never blocks child.
    - DB/data: all synthetic writes are isolated; real project ledger remains
      unchanged until native delegation.
    - Behavior test: A–F pass; synthetic result is explicitly not host proof.
    - Cleanup/quarantine: test roots removed or retained only under `.tmp`.
    - Evidence IDs: `E1-P1B-CFG1..E1-P1B-TEST3`.
    - Actual-status rows refreshed: hook binding `missing -> correct`; native
      proof remains `unverified`.
  - Evidence Targets: TOML parse, hook behavior, no secret persistence, no
    network/dependency use, and deterministic duplicate count.
  - Actual-status Update: mark project hook configured; do not mark execution
    verified until P2-B.
  - Commit Boundary: commit after this slice when acceptance passes; otherwise
    record the no-Git blocker.

### P2: Real native identity proof

- Phase Goal: verify the official hook receives a real child lifecycle event and
  record exact host-owned identity evidence.
- Phase Boundary:
  - In scope: one current Desktop native delegation, receipt inspection, exact
    child ID/type/source, optional default-agent control, host failure class.
  - Out of scope: manual spawn tool calls, simulated receipts, routing changes,
    packaging, and unrelated agent work.
  - Dependencies: P1-B passes and trusted project hook is loaded.
- Ordered Slice List:
  - P2-A: Prepare native delegation gate and receipt inspection.
  - P2-B: Execute one real native Aesthetica delegation.

- [x] P2-A: Prepare native delegation gate and receipt inspection.
  - Goal: define the exact child task and acceptance query before execution.
  - Scope Boundary:
    - Editable: plan/evidence/temporary fixture only.
    - Inspect-only: current Desktop coordinator/tool surface and project ledger.
    - Preserve-only: source and hook implementation.
    - Out of scope: any manual spawn or host bypass.
  - Non-Goals: no identity claim from a child response.
  - Pre-flight Questions:
    - Data source: current native coordinator and official hook receipt.
    - Display permission: local evidence only.
    - DB read flow: read the project ledger after child completion.
    - DB write flow: host hook only.
    - Render location: N/A.
    - UI behavior flow: bounded synthetic warehouse dashboard description.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: exact receipt query.
    - Cleanup/quarantine: no synthetic receipt inserted into the real ledger.
    - External side effects: one bounded native child only.
    - N/A notes: no external service or user project.
  - Work Steps:
    1. Give the current coordinator the semantic instruction to have
       `p2p_aesthetica` review the self-contained synthetic warehouse dashboard
       and wait for completion, without manually calling spawn tools.
       - UI flow check: bounded synthetic UI description only.
       - DB/data flow check: host ledger receipt after completion.
       - Render location check: N/A.
       - Evidence target: delegation instruction and host lifecycle result.
    2. Query the ledger for the newest receipt and compare exact agent ID,
       `agent_type`, event, and `source`.
       - UI flow check: N/A.
       - DB/data flow check: no receipt injection or modification.
       - Render location check: N/A.
       - Evidence target: redacted receipt excerpt and hash/line reference.
  - Implementation Gate: if the host does not expose a receipt, stop at
    `BLOCKED_HOST_HOOK_UNAVAILABLE`/`NAMED_DELEGATION_NOT_VERIFIED`; never
    synthesize one.
  - Acceptance:
    - Source: no source change.
    - Runtime/UI: real Desktop native child lifecycle observed or precisely
      blocked.
    - DB/data: official receipt contains exact child ID/type/source.
    - Behavior test: `is_verified_for("p2p_aesthetica")` is true only on exact
      receipt.
    - Cleanup/quarantine: no artificial receipt in real ledger.
    - Evidence IDs: `E2-P2A-HOST1..E2-P2A-HOST3`.
    - Actual-status rows refreshed: native proof `unverified -> verified` only
      if gate passes; otherwise retain `unverified` and set final blocker.
  - Evidence Targets: host event, ledger query, exact fields, and failure class.
  - Actual-status Update: update P2-B and P3 assumptions from actual host result.
  - Commit Boundary: no code commit; record host evidence.

- [x] P2-B: Execute one real native Aesthetica delegation.
  - Goal: complete the sole real identity gate under the current coordinator.
  - Scope Boundary:
    - Editable: none in product source.
    - Inspect-only: receipt and child response.
    - Preserve-only: all project sources and user projects.
    - Out of scope: identity simulation or retry loops that create ambiguity.
  - Non-Goals: no claim based on a name in child prose.
  - Pre-flight Questions: same as P2-A; all UI/data/render checks are N/A
    except the bounded synthetic task and ledger receipt.
  - Work Steps:
    1. Run the one bounded native delegation.
       - UI flow check: child reviews description only.
       - DB/data flow check: hook writes receipt.
       - Render location check: N/A.
       - Evidence target: native coordinator/thread evidence.
    2. Classify exact result and freeze the gate.
       - UI flow check: N/A.
       - DB/data flow check: receipt source and type exact.
       - Render location check: N/A.
       - Evidence target: final identity classification.
  - Implementation Gate: no continuation to P3 native routing unless exact
    receipt passes.
  - Acceptance: one of certified, limited, not verified, or host unavailable;
    never “pass” with synthetic evidence.
  - Evidence Targets: `E2-P2B-REAL1..E2-P2B-REAL4`.
  - Actual-status Update: refresh host proof, package decision, and final report.
  - Commit Boundary: no code commit.
  - Outcome: the current trusted Desktop coordinator returned `BLOCKED` without
    spawning a child. The project ledger remained empty, so the exact receipt
    gate failed safely and the final classification is
    `NAMED_DELEGATION_NOT_VERIFIED`.

### P3: Minimal routing/instruction completion after real proof

- Phase Goal: only if P2 exact identity passes, bind the existing p2p-uiux path
  to a clear native delegation instruction and receipt gate; otherwise preserve
  the current fallback and report limited/not-verified status.
- Phase Boundary:
  - In scope: smallest existing P2P/p2p-uiux instruction or routing change,
    four behavior tests, readiness/security/canonical regression.
  - Out of scope: new router, second ledger, new governance, broad UI redesign.
  - Dependencies: P2-B exact receipt pass; otherwise phase is preserve-only.
- Ordered Slice List:
  - P3-A: Audit route instruction gap and choose preserve/edit.
  - P3-B: Add minimal native delegation wording and receipt gate.
  - P3-C: Run routing truth-table and safety regression.

- [ ] P3-A: Audit route instruction gap and choose preserve/edit.
  - Goal: compare existing route output and skill instructions with the
    required native delegation sentence and fallback semantics.
  - Scope Boundary: inspect-only until P2-B passes; preserve existing router.
  - Acceptance: explicit `edit` or `preserve-only` decision in actual status.

- [ ] P3-B: Add minimal native delegation wording and receipt gate.
  - Goal: ensure a material UI request can instruct the current coordinator to
    delegate to the exact named profile and wait, while missing/mismatched
    receipt falls back without simulation.
  - Scope Boundary:
    - Editable: the existing p2p/p2p-uiux instruction source only if P2 passes,
      plus focused tests.
    - Inspect-only: router implementation unless a receipt input is strictly
      required by the existing contract.
    - Preserve-only: single-router result shape, capability registry, Decision
      Trace, canonical identities, and optional classification.
    - Out of scope: new agent or route.
  - Non-Goals: no direct API spawn, no child prompt injection, no Aesthetica
    quorum participation.
  - Pre-flight Questions: data is the existing route plus host receipt; no DB,
    browser, Docker, or UI render applies; tests use isolated ledgers.
  - Work Steps:
    1. Add only the required instruction/gate text if it is absent.
       - UI flow check: semantic UI request -> current coordinator instruction.
       - DB/data flow check: receipt gate before “verified”.
       - Render location check: N/A.
       - Evidence target: diff/source inspection and route output.
    2. Keep negative/back-end/unavailable paths unchanged except for explicit
       truthful fallback labels.
       - UI flow check: four request classes.
       - DB/data flow check: no receipt -> no specialist proof.
       - Render location check: N/A.
       - Evidence target: truth-table regression.
  - Implementation Gate: run Anvien impact/file-detail for any visible skill,
    test, or packaging file before edit; hidden runtime direct inspection only.
  - Acceptance: wording is exact/semantically equivalent, router remains the
    sole router, and Aesthetica remains outside `8/8`.
  - Evidence Targets: `E3-P3B-ROUTE1..E3-P3B-SEC2`.
  - Actual-status Update: routing `partial -> correct` only if host proof and
    instruction gate both pass.
  - Commit Boundary: one narrow implementation slice; no release commit.

- [ ] P3-C: Run routing truth-table and safety regression.
  - Goal: prove Vietnamese beginner UI triggers UIUX without technical setup,
    backend work does not trigger Aesthetica, small UI stays restrained, and
    unavailable specialist reports visible fallback.
  - Scope Boundary: tests and evidence only; no user project.
  - Acceptance: all four outcomes and readiness/security/quorum checks pass.
  - Evidence Targets: `E3-P3C-TEST1..E3-P3C-TEST5`.

### P4: Regression, packaging, and release decision

- Phase Goal: validate the final source/config/runtime set and prepare a fresh
  package only when technically required and approval-bound.
- Phase Boundary:
  - In scope: full relevant build/doctor/drift/regression, fresh/upgrade/
    reinstall if package is changed, DW1–DW18 only if release metadata is
    touched, manifest/lock/hash evidence, supervisor review.
  - Out of scope: deployment/publish/final approval self-action.
  - Dependencies: P1/P2 and conditional P3 result.
- Ordered Slice List:
  - P4-A: Run full relevant regression and integrity gates.
  - P4-B: Prepare candidate package or preserve prior `.9` artifact.

- [x] P4-A: Run full relevant regression and integrity gates.
  - Goal: verify source, hook, registry, routing, security, no second system,
    no protected-target mutation, and current package metadata.
  - Scope Boundary: validation-only except generated artifacts explicitly
    required by the package workflow.
  - Acceptance: evidence records each command and precise pass/fail.

- [x] P4-B: Prepare candidate package or preserve prior `.9` artifact.
  - Goal: package changed runtime/config/instruction files after technical gates
    only, or explicitly preserve `.9` when no package path is needed.
  - Scope Boundary: no release promotion/deployment/publish; user approval is
    required before protected finalization.
  - Acceptance: fresh artifact has clean inventory and hash, or blocker records
    why packaging could not be completed.

- [x] Pn-A: Call supervisor for implemented-plan acceptance.
  - Goal: zero-trust review of source, receipt evidence, tests, packaging, and
    final classification.
  - Acceptance: supervisor PASS or explicit blocker; no unsupported closure.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: retain only useful plan/evidence/tests/runtime changes; no temporary
    receipts or rejected artifacts.
  - Acceptance: no dead plan-created artifact remains.
- [ ] Pn-C: Close the plan.
  - Goal: final validation, Anvien detect-changes, actual-status refresh, and
    concise 31-field handoff.
  - Acceptance: final status is PASS/limited/not-verified/blocked and all
    remaining user action is explicit.

## Risk Notes

- Host hook support is product/runtime behavior and must remain source-backed;
  absence of a callable native coordinator is a real blocker, not a test
  failure to work around.
- The project has no `.git` directory, so required commit checkpoints and Git
  diff evidence cannot be produced; this is recorded as an environment risk.
- The installed project’s `.p2p/system/release.json` is historical `.3` metadata
  while prior recovery work produced a `.9` artifact. Do not silently repair or
  release it without the package gate.
- The P2P workflow helper currently has a pre-existing `p2p_eval.py` argument
  mismatch during bootstrap; it is evidence of helper compatibility risk and
  is out of scope unless it directly blocks the requested receipt gates.

## Closure Decision

- Overall result: `BLOCKED` for the native identity completion goal.
- Final classification: `NAMED_DELEGATION_NOT_VERIFIED`.
- P3 routing/instruction work was not run because the exact host receipt gate
  did not pass; the existing single-router behavior remains unchanged.
- The `.10` candidate is technically packaged and lifecycle-tested, but the
  release gate remains blocked by current-root drift findings and the missing
  project eval suite. No approval or promotion was performed.
- Repo-local validation and superseded candidate artifacts remain under
  `.tmp/package-validation-final`, `.tmp/package-candidates/`, and
  `.tmp/gates/` because the host rejected the recursive cleanup command. They
  are not runtime receipts or release artifacts and must be removed in a later
  cleanup-only action before this plan can be marked closed.
