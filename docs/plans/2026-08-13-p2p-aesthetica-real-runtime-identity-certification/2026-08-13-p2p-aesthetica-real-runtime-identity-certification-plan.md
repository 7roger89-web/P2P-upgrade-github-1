# P2P Aesthetica — Real Runtime Identity Certification Plan

## Metadata

- Date: `2026-08-13`
- Status: `blocked`
- Plan: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-actual-status.md`

## Goal

Certify whether the packaged P2P capability `p2p_aesthetica` can be discovered, resolved, and executed by the real Codex custom-agent runtime while preserving its supporting/noncanonical identity and UI/UX-only domain boundary. This is a validation-only Goal unless a separately approved defect is discovered; a prompt-based role-play is never evidence of real identity.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or validation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving the phase goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For public runtime or UI-facing changes, validate the real user-visible runtime with browser or Playwright evidence.
- This Goal has no application UI/Docker deliverable. Codex host runtime and packaged installer evidence are the authoritative runtime surfaces; Docker/Playwright requirements are `N/A` unless the tested host exposes a real browser surface.
- Never claim `p2p_aesthetica` identity from a system prompt, response wording, or a generic subagent whose profile was not selected and verified by the host.
- If the host cannot start a real custom-agent execution, record the exact capability boundary and stop at `BLOCKED`; do not modify source to manufacture a PASS.
- Keep the canonical eight exactly unchanged: `p2p_iris`, `p2p_tecton`, `p2p_axiom`, `p2p_vector`, `p2p_datos`, `p2p_anon`, `p2p_architecton`, `p2p_helios`.
- No App Game Truyện, Logistics, or other user project may be read for modification or changed.

## Problem

The current `.6` source and package contain a declared Aesthetica profile and capability record, but previous work did not prove the final ladder step: a real Codex custom-agent runtime selected and executed that profile. Without host execution evidence, `p2p_aesthetica` must remain runtime readiness `UNPROVEN` even though its source and package metadata are present.

## Scope

- Inspect the source profile, capability registry, manifests, installer, doctor, and `.6` package boundary.
- Perform an isolated fresh install from `.6` into a disposable fixture under the P2P development repository's temporary area.
- Verify discovery and profile resolution from installed state.
- Use the real Codex host Subagents UI or `/agent` surface when available to select `p2p_aesthetica`; record host-level evidence of selected profile and returned identity-safe evidence.
- Test UI/UX domain behavior, negative backend routing, beginner routing, optional specialist classification, canonical quorum exclusion, fail-closed behavior, and multiple-thread identity only where the host supports it.
- Run scoped regressions and produce a supervisor review/report.
- Add only plan/report/evidence artifacts required by this Goal; no runtime source edits are authorized by this plan.

## Non-Goals

- No redesign or implementation of Decision Trace, UIUX, discovery, governance, packaging architecture, or quorum semantics.
- No new agent, specialist, external integration, MCP/graph/RDF dependency, or backend routing redesign.
- No simulation of Aesthetica execution or identity.
- No upgrade, reinstall, or modification of App Game Truyện, Logistics, or any real user project.
- No private chain-of-thought capture; only identity, classification, domain-boundary, and safe observable evidence may be retained.

## Requirements

1. Baseline is `8.4.7-C-codex.6`, artifact `P2P-8.4.7-C-Codex-Edition-v6.zip`, SHA-256 `b8689fb812a438f379fc1d84353f2e4e4c9c0c234c1e22539b2bc32fd15b8156`.
2. Source, package, install, discovery, profile resolution, and real custom-agent execution must be assessed separately.
3. Real execution evidence must show host-selected `p2p_aesthetica`, not merely a prompt asking a generic model to act as Aesthetica.
4. Aesthetica remains `SUPPORTING / OPTIONAL DOMAIN SPECIALIST`, `optional_specialist=true`, `canonical_quorum_member=false`.
5. Valid UI/UX requests may be handled by Aesthetica; backend/database/API/infrastructure/governance-only requests must not be silently routed to it.
6. Failure to spawn or resolve a real custom agent is a visible `BLOCKED`/unproven result, not a simulated success.
7. Evidence must exclude local absolute paths, credentials, secrets, and private chain-of-thought.

## Acceptance Criteria

- AI1–AI4: source/package/install/discovery/profile-resolution ladder is evidenced.
- AI5–AI8: a real custom-agent execution is evidenced, or the exact host blocker is recorded and the Goal is `BLOCKED`.
- AI9–AI12: identity, UI/UX boundary, negative backend routing, beginner routing, and fail-closed behavior are evidenced where host capability permits.
- AI13–AI15: multiple-thread identity and canonical/quorum safety are evidenced; unavailable host capability remains explicit.
- AI16–AI18: runtime readiness states and relevant regressions are recorded without changing out-of-scope systems.
- AI19: only safe reports/evidence are retained; no source fix is made merely to obtain PASS.
- AI20: exactly one evidence-backed residual-risk recommendation is produced, or STOP after a genuine PASS.

## Checklist

- [ ] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state of source, package, installer, host runtime, profile resolution, and canonical safety.
  - Work Steps: inspect source-of-truth files; verify package hash and entries; inspect host CLI/UI capability; classify every ladder step; record evidence IDs; update downstream slices before any edit.
  - Implementation Gate: no runtime source editing or certification claim starts until `2026-08-13-p2p-aesthetica-real-runtime-identity-certification-actual-status.md` has a P0 decision.
  - Acceptance: each surface is `correct`, `partial`, `missing`, `unbound`, `fake-or-stub`, or `blocked` with exact evidence IDs and a touch mode.

### P1: Source, package, install, discovery, and profile resolution

- Phase Goal: prove the non-execution ladder from development source through an isolated installed fixture.
- Phase Boundary:
  - In scope: source profile, capability registry, manifest/package entries, installer/doctor, isolated `.tmp` fixture, discovery and profile resolution.
  - Out of scope: real-agent execution, source redesign, user projects, old release artifact.
  - Dependencies: P0 complete; `.6` artifact hash verified.
- Phase Implementation Rule: this is validation-only. Do not implement `P1` directly; complete `P1-A`, refresh actual status/evidence, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Verify source/package provenance and package boundary.
  - P1-B: Fresh-install fixture and resolve the installed profile.

- [x] P1-A: Verify source/package provenance and package boundary. PASS.
  - Goal: prove the declared profile and capability metadata are present and consistent in source and `.6` without editing them.
  - Scope Boundary:
    - Editable: plan/evidence/benchmark/actual-status/report files only.
    - Inspect-only: `.codex/agents/p2p-aesthetica.toml`, capability registry, manifest, installer, doctor, release notes.
    - Preserve-only: all runtime source and `.6` artifact.
    - Out of scope: old artifacts, user projects, profile content changes.
  - Non-Goals: no profile rewrite, no package rebuild, no identity simulation.
  - Pre-flight Questions:
    - Data source: source profile, capability registry, manifest, `.6` ZIP.
    - Display permission: safe metadata only; no private prompt/CoT export.
    - DB read flow: N/A; no database is involved.
    - DB write flow: N/A; no persistent application data is written.
    - Render location: evidence ledger/report only.
    - UI behavior flow: N/A; host UI is tested in P2/P3 if available.
    - Docker runtime: N/A; this is Codex host/package validation.
    - Playwright target: N/A unless the host exposes a real browser surface.
    - Behavior test: profile/capability/package consistency checks.
    - Cleanup/quarantine: no writes outside plan/report files.
    - External side effects: none.
    - N/A notes: package is preserve-only because `.6` is the verified baseline.
  - Work Steps:
    1. Hash the `.6` ZIP and inspect source/package entries and identity fields.
       - UI flow check: N/A; host UI is not changed.
       - DB/data flow check: N/A; no DB.
       - Render location check: evidence IDs record only safe metadata.
       - Mini QA for each completed implementation slice (MUST): N/A because this slice performs no implementation and no browser surface exists.
       - Evidence target: `E1-P1A-PROV1..E1-P1A-PROV4`.
    2. Confirm no package entry points to developer-only runtime data required for profile resolution.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: package-entry inventory is recorded in evidence.
       - Mini QA for each completed implementation slice (MUST): N/A; validation-only slice.
       - Evidence target: `E1-P1A-PKG1..E1-P1A-PKG3`.
  - Implementation Gate:
    - Before editing any target file, run Anvien file-detail/impact for the target; no source editing is expected, so preserve-only mode is the gate.
    - `.6` hash and profile/capability fields must match the baseline before proceeding.
  - Acceptance:
    - Source: profile and capability fields are consistent.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: source/package consistency passes.
    - Cleanup/quarantine: no runtime source changes.
    - Evidence IDs: `E1-P1A-PROV1..E1-P1A-PKG3`.
    - Actual-status rows refreshed: source, package, canonical metadata.
  - Evidence Targets: source profile, capability record, package hash, package entries, package boundary.
  - Actual-status Update: mark source/package metadata `correct` if all fields match; otherwise stop and classify the exact mismatch.
  - Commit Boundary: no source commit; plan/report artifacts are retained in the working tree.

- [x] P1-B: Fresh-install fixture and resolve the installed profile. PASS through profile resolution; execution remains unproven.
  - Goal: prove the installer places the profile and required capability metadata into a clean isolated fixture and doctor/discovery resolves it.
  - Scope Boundary:
    - Editable: disposable `.tmp` fixture and evidence/report files; fixture must be removed or quarantined after capture.
    - Inspect-only: installer/doctor behavior and installed files.
    - Preserve-only: source tree, `.6` ZIP, user projects.
    - Out of scope: release rebuild, upgrade, reinstall mutation of any user project.
  - Non-Goals: this does not prove actual custom-agent execution.
  - Pre-flight Questions:
    - Data source: `.6` ZIP and install/doctor scripts.
    - Display permission: safe installed paths relative to fixture only.
    - DB read flow: N/A.
    - DB write flow: installer ledger/manifest only inside fixture; inspect and clean up.
    - Render location: evidence/report.
    - UI behavior flow: N/A unless install is driven through host UI.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: clean install -> discovery -> profile resolution -> doctor.
    - Cleanup/quarantine: remove only the exact fixture under repo `.tmp` after evidence capture.
    - External side effects: none.
    - N/A notes: no source edit or package overwrite.
  - Work Steps:
    1. Create a uniquely named fixture under `.tmp`, install `.6`, and inventory installed profile/capability paths.
       - UI flow check: N/A.
       - DB/data flow check: inspect only fixture-local install state.
       - Render location check: use fixture-relative paths in reports.
       - Mini QA for each completed implementation slice (MUST): N/A; no implementation.
       - Evidence target: `E1-P1B-INST1..E1-P1B-INST3`.
    2. Run doctor/discovery/profile-resolution checks from the installed fixture and record deterministic success/failure.
       - UI flow check: N/A.
       - DB/data flow check: N/A beyond fixture-local manifest.
       - Render location check: redact machine-specific paths from user-facing evidence.
       - Mini QA for each completed implementation slice (MUST): N/A; validation-only.
       - Evidence target: `E1-P1B-RES1..E1-P1B-RES4`.
  - Implementation Gate:
    - Proceed only if the fixture is isolated and no source/user-project path is a write target.
    - A resolved profile is not accepted as real execution evidence.
  - Acceptance:
    - Source: unchanged.
    - Runtime/UI: installed discovery/profile resolution is deterministic.
    - DB/data: fixture-local state preserved only long enough for validation.
    - Behavior test: clean install and doctor pass or exact failure is recorded.
    - Cleanup/quarantine: fixture removed/quarantined and path not exposed.
    - Evidence IDs: `E1-P1B-INST1..E1-P1B-RES4`.
    - Actual-status rows refreshed: installed profile, discovery, resolution.
  - Evidence Targets: install log, installed file inventory, doctor result, resolution result, cleanup result.
  - Actual-status Update: mark installed ladder steps `correct`, `partial`, or `blocked` based on direct evidence.
  - Commit Boundary: no source commit.

### P2: Real custom-agent runtime execution and identity

- Phase Goal: prove the final runtime step with the actual Codex custom-agent selector, or establish a genuine host limitation.
- Phase Boundary:
  - In scope: host Subagents UI or `/agent` runtime, explicit profile selection, safe identity/domain probe, host execution evidence.
  - Out of scope: generic subagents, prompt-only role-play, profile edits, quorum changes.
  - Dependencies: P1 profile resolution passes; host must expose a real profile-selection mechanism.
- Phase Implementation Rule: no code implementation is allowed. If the host cannot select/start the profile, record `BLOCKED` and do not substitute a generic agent.

- [x] P2-A: Start one real `p2p_aesthetica` custom-agent execution. BLOCKED: host did not provide host-selected profile provenance or a real Aesthetica child execution.
  - Goal: show that the host selected and started the intended profile and return only safe evidence.
  - Scope Boundary:
    - Editable: evidence/report files only.
    - Inspect-only: host runtime state and generated response.
    - Preserve-only: profile and runtime source.
    - Out of scope: generic real subagent, simulated identity, source patch.
  - Non-Goals: no private reasoning capture and no quorum participation.
  - Pre-flight Questions:
    - Data source: host-selected profile indicator, runtime metadata, safe response envelope.
    - Display permission: identity/classification/domain result only.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: host panel/terminal plus evidence report.
    - UI behavior flow: select profile -> submit probe -> inspect execution identity.
    - Docker runtime: N/A.
    - Playwright target: host runtime if exposed; otherwise N/A.
    - Behavior test: real start -> response -> identity evidence.
    - Cleanup/quarantine: close the real thread after capture; retain safe trace only.
    - External side effects: none.
    - N/A notes: host capability is the acceptance dependency.
  - Work Steps:
    1. Use the host's actual Subagents UI or `/agent` selector; capture the selected profile name and runtime/thread identifier without private content.
       - UI flow check: selection must be host-originated, not inferred from prompt text.
       - DB/data flow check: N/A.
       - Render location check: record a redacted host panel/terminal result if available.
       - Mini QA for each completed implementation slice (MUST): use the host control surface; no substitute is valid.
       - Evidence target: `E2-P2A-HOST1..E2-P2A-HOST3`.
    2. Submit a minimal UI/UX probe requiring the profile to state safe identity/classification/domain facts, then verify the execution response against the declared profile.
       - UI flow check: valid UI/UX request only; no code or governance action.
       - DB/data flow check: N/A.
       - Render location check: retain only safe observable output.
       - Mini QA for each completed implementation slice (MUST): verify the real execution result and close the thread.
       - Evidence target: `E2-P2A-EXEC1..E2-P2A-EXEC4`.
  - Implementation Gate:
    - A host-selected profile indicator or equivalent runtime provenance must exist before any identity claim.
    - If no profile selector exists, classify the exact host boundary as blocked; do not type "you are p2p_aesthetica" into a generic thread.
  - Acceptance:
    - Source: unchanged.
    - Runtime/UI: one real custom-agent execution is proven, or exact blocker is captured.
    - DB/data: N/A.
    - Behavior test: identity and classification are returned from the real execution.
    - Cleanup/quarantine: no private prompt/CoT retained.
    - Evidence IDs: `E2-P2A-HOST1..E2-P2A-EXEC4`.
    - Actual-status rows refreshed: real execution, identity, readiness.
  - Evidence Targets: host selector, profile provenance, safe execution envelope, blocker if applicable.
  - Actual-status Update: `missing/unproven -> correct` only after host proof; otherwise `blocked` with exact capability limitation.
  - Commit Boundary: no source commit.

### P3: Domain routing, fail-closed behavior, and canonical safety

- Phase Goal: test the safe boundary around a real Aesthetica runtime without changing routing or quorum semantics.
- Phase Boundary:
  - In scope: UI/UX probe, backend negative probe, beginner-language probe, optional specialist identity, multiple-thread check if host supports it, canonical before/after snapshots.
  - Out of scope: routing redesign, specialist implementation, quorum changes, user projects.
  - Dependencies: P2-A real execution PASS; if P2-A is blocked, mark dependent tests not executable rather than simulating.
- Phase Implementation Rule: validation-only; each probe must be labelled executable, blocked-by-host, or not-applicable with evidence.

- [x] P3-A: Verify UI/UX domain boundary and negative backend routing. Package-router evidence PASS; host-runtime behavior BLOCKED by P2-A.
  - Goal: confirm valid UI/UX requests stay within Aesthetica's authority and backend/database/API requests are not routed to it as a backend agent.
  - Scope Boundary:
    - Editable: evidence/report only.
    - Inspect-only: host routing result and safe response.
    - Preserve-only: routing registry and capability metadata.
    - Out of scope: any routing fix.
  - Non-Goals: no implementation, no backend work.
  - Pre-flight Questions:
    - Data source: real custom-agent runtime and capability registry.
    - Display permission: route/classification/result only.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: host response/evidence.
    - UI behavior flow: UI/UX probe then backend negative probe.
    - Docker runtime: N/A.
    - Playwright target: N/A unless host exposes a real UI.
    - Behavior test: positive boundary and negative boundary.
    - Cleanup/quarantine: close test threads.
    - External side effects: none.
    - N/A notes: dependent on P2-A.
  - Work Steps:
    1. Run a valid UI/UX request and record the domain-safe result.
       - UI flow check: request maps to UI/UX authority.
       - DB/data flow check: N/A.
       - Render location check: response metadata only.
       - Mini QA for each completed implementation slice (MUST): real host execution.
       - Evidence target: `E3-P3A-POS1`.
    2. Run a backend/database/API-only request and verify Aesthetica is not treated as the backend authority; any refusal or reroute must be visible.
       - UI flow check: negative route is visible and fail-closed.
       - DB/data flow check: no backend write.
       - Render location check: safe result only.
       - Mini QA for each completed implementation slice (MUST): real host execution or explicit blocked-by-host.
       - Evidence target: `E3-P3A-NEG1`.
  - Implementation Gate:
    - P2-A must have proven the real profile; otherwise mark both tests `not executable` and preserve BLOCKED.
  - Acceptance:
    - Source: unchanged.
    - Runtime/UI: positive boundary passes and negative route is not silently accepted.
    - DB/data: no backend data mutation.
    - Behavior test: both boundary outcomes are honest.
    - Cleanup/quarantine: test threads closed.
    - Evidence IDs: `E3-P3A-POS1`, `E3-P3A-NEG1`.
    - Actual-status rows refreshed: domain boundary and negative routing.
  - Evidence Targets: positive and negative route outcomes.
  - Actual-status Update: mark boundaries `correct`, `partial`, or `blocked-by-host`.
  - Commit Boundary: no source commit.

- [x] P3-B: Verify beginner-language routing, optional identity, multiple-thread identity, and canonical exclusion. Existing regression/canonical evidence PASS; host-dependent identity checks BLOCKED by P2-A.
  - Goal: confirm beginner UI/UX wording routes safely, identity remains optional/noncanonical across threads, and canonical snapshots remain unchanged.
  - Scope Boundary:
    - Editable: evidence/report only.
    - Inspect-only: host runtime, routing, quorum snapshot.
    - Preserve-only: canonical profiles and denominator.
    - Out of scope: quorum redesign or simulated threads.
  - Non-Goals: no changes to beginner discovery or canonical governance.
  - Pre-flight Questions:
    - Data source: real host execution and canonical registry.
    - Display permission: plain-language safe evidence only.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: host response/report.
    - UI behavior flow: beginner WHY request -> routing -> safe answer.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: one beginner probe; second independent thread only if host can select the same profile again.
    - Cleanup/quarantine: close all test threads.
    - External side effects: none.
    - N/A notes: multiple-thread check is explicitly host-capability dependent.
  - Work Steps:
    1. Run the beginner UI/UX probe and verify no technical IDs or false canonical claim are exposed.
       - UI flow check: plain-language question is answered in plain language.
       - DB/data flow check: N/A.
       - Render location check: safe output only.
       - Mini QA for each completed implementation slice (MUST): real host execution.
       - Evidence target: `E3-P3B-BEGIN1`.
    2. If supported, run two independently created Aesthetica threads and compare safe identity/classification; snapshot canonical identities/count/denominator before and after.
       - UI flow check: independent host threads, not copied prompts in one thread.
       - DB/data flow check: N/A.
       - Render location check: no private reasoning.
       - Mini QA for each completed implementation slice (MUST): host thread provenance check.
       - Evidence target: `E3-P3B-MULTI1`, `E3-P3B-CAN1..E3-P3B-CAN3`.
  - Implementation Gate:
    - No canonical count may be inferred from a specialist response; use source/registry snapshot.
  - Acceptance:
    - Source: canonical and specialist metadata unchanged.
    - Runtime/UI: beginner route and optional identity are honest.
    - DB/data: N/A.
    - Behavior test: multiple-thread proof or explicit host limitation.
    - Cleanup/quarantine: threads closed.
    - Evidence IDs: `E3-P3B-BEGIN1`, `E3-P3B-MULTI1`, `E3-P3B-CAN1..E3-P3B-CAN3`.
    - Actual-status rows refreshed: beginner routing, multiple-thread, canonical safety.
  - Evidence Targets: beginner result, optional identity, canonical snapshot.
  - Actual-status Update: retain `blocked-by-host` for unsupported multiple-thread checks without treating it as a source defect.
  - Commit Boundary: no source commit.

### P4: Regression, security, supervisor review, and closure

- Phase Goal: close the certification with regression, safe evidence, one residual-risk recommendation, and an independent supervisor verdict.
- Phase Boundary:
  - In scope: Aesthetica-relevant regressions, secret/redaction scan, report inventory, supervisor review, final status.
  - Out of scope: all unrelated improvements and all user-project changes.
  - Dependencies: P1–P3 evidence complete or explicitly blocked.
- Phase Implementation Rule: no source implementation; a blocked runtime certification cannot be upgraded to PASS by packaging changes.

- [x] P4-A: Run scoped regressions and security checks. PASS: 32 targeted tests, package secret scan, and preserve-only scope.
  - Goal: verify Aesthetica validation did not change Decision Trace, UIUX, canonical, installer, or other previously passing surfaces.
  - Scope Boundary:
    - Editable: report/evidence files only.
    - Inspect-only: regression scripts and results.
    - Preserve-only: runtime source and release artifact.
    - Out of scope: fixing unrelated failures.
  - Non-Goals: no code changes.
  - Pre-flight Questions:
    - Data source: existing regression suite and safe scan output.
    - Display permission: pass/fail/counts only.
    - DB read flow: N/A.
    - DB write flow: tests use isolated fixtures and clean up.
    - Render location: evidence/report.
    - UI behavior flow: N/A unless existing UI regression is runnable.
    - Docker runtime: N/A unless an existing application runtime is explicitly in scope.
    - Playwright target: N/A.
    - Behavior test: Decision Trace, beginner WHY, UIUX, canonical, install/doctor smoke checks.
    - Cleanup/quarantine: remove exact test fixtures.
    - External side effects: none.
    - N/A notes: no package rebuild unless a real source defect is independently authorized.
  - Work Steps:
    1. Run relevant regression and secret/redaction checks; record raw pass/fail summaries and preserve failure evidence.
       - UI flow check: N/A.
       - DB/data flow check: fixture cleanup verified.
       - Render location check: safe output only.
       - Mini QA for each completed implementation slice (MUST): N/A; validation-only.
       - Evidence target: `E4-P4A-REG1..E4-P4A-REG4`.
    2. Confirm no source, release ZIP, App Game Truyện, Logistics, or real user project changed.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: changed-file inventory is safe.
       - Mini QA for each completed implementation slice (MUST): N/A.
       - Evidence target: `E4-P4A-SCOPE1..E4-P4A-SCOPE3`.
  - Implementation Gate:
    - If any unrelated source mutation is found, stop and preserve it for review; do not clean user changes destructively.
  - Acceptance:
    - Source: no unauthorized runtime source edits.
    - Runtime/UI: relevant regressions pass or exact blockers are recorded.
    - DB/data: fixtures cleaned.
    - Behavior test: no regression claim without command/result evidence.
    - Cleanup/quarantine: confirmed.
    - Evidence IDs: `E4-P4A-REG1..E4-P4A-SCOPE3`.
    - Actual-status rows refreshed: regression and security.
  - Evidence Targets: regression summary, secret scan, scope-diff, fixture cleanup.
  - Actual-status Update: update only affected statuses from direct results.
  - Commit Boundary: no source commit.

- [x] Pn-A: Call supervisor for the completed-plan acceptance loop. BLOCKED/REJECT because real custom-agent execution is not proven.
  - Goal: independently verify the final claim against source, package, runtime evidence, actual status, benchmark, and reports.
  - Work Steps:
    1. Call the supervisor skill to inspect the full completed plan work.
    2. If supervisor rejects, record the exact missing proof; do not fix unrelated code.
    3. Re-run only the failed validation if the host state changes.
  - Implementation Gate: all executable phases are complete or explicitly blocked.
  - Acceptance: supervisor returns PASS only when real custom-agent execution is proven; otherwise returns REJECT/BLOCKED with evidence.
- [x] Pn-B: Remove dead work created during this plan. Exact Goal-owned fixtures were moved to a recoverable quarantine after evidence capture; original paths verified absent.
  - Goal: retain only relevant plan/report/evidence artifacts.
  - Work Steps: review plan-created files, remove stale temporary fixtures and rejected outputs, verify no runtime source was touched, and have supervisor review cleanup.
  - Implementation Gate: remove only artifacts created by this Goal.
  - Acceptance: no dead fixture/output remains; cleanup is evidenced.
- [x] Pn-C: Close the plan. Final result BLOCKED with exactly one residual-risk recommendation.
  - Goal: record final status and exactly one residual-risk recommendation.
  - Work Steps: final validation, update all ledgers/status, record artifact facts, record no commit if none, and stop according to PASS/BLOCKED rule.
  - Implementation Gate: Pn-A and Pn-B pass or record genuine blockers.
  - Acceptance: final report has the exact 21 required sections and does not claim PASS without real execution proof.

## Risk Notes

- The primary risk is host capability: the source/package profile may be correct while this Codex surface exposes no real custom-agent selector.
- A generic real subagent is not equivalent to a selected Aesthetica profile and must not be relabelled.
- Host terminal/UI availability may vary; record the exact unavailable surface and do not infer identity from output text.
- The `.6` release artifact is a preserve-only baseline. No new release is justified unless a separately authorized runtime source change is required and proven.
- Evidence must remain safe: no absolute developer paths, credentials, secrets, or private chain-of-thought.
