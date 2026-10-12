# Issue 333 OIDC Generic Admission Plan

## Metadata

- Date: `2026-10-12`
- Status: `active`
- Plan: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-plan.md`
- Evidence: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-evidence.md`
- Benchmark: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-benchmark.md`
- Actual status: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-actual-status.md`

## Goal

Close the remaining Issue #333 trust gap with the smallest durable path: keep merged `GENERIC_PROMPT_ONLY` as the non-authorizing first phase, then allow `GENERIC_EXACT_REPO_READ` only after a real non-Arena/non-Codex actor produces GitHub-OIDC-signed, source-bound evidence that it read and applied the exact frozen repo-native skill for the exact task.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes and benchmarkable counts when measured.
- Preserve `PROMPT_ONLY != EXECUTION_AUTHORIZATION`.
- Reuse the existing skill router and C20/C21 host contracts; do not add another router, registry, daemon, vector DB, background scanner, or Claude/Grok/Manus adapter.
- GitHub OIDC is an evidence issuer, not a model/provider allowlist.
- Any missing, stale, malformed, mismatched, self-hosted, wrong-repo, wrong-revision, wrong-task, wrong-skill, wrong-host, or unverifiable evidence fails closed.
- `ANVIEN_ENABLED=NO` in current `AGENTS.md`; planner/coder Anvien steps are superseded and recorded as N/A.
- No UI/DB/Docker/Playwright surface exists in this scope; those checks are N/A.
- Independent Supervisor exact-head review is required before merge.

## Problem

Issue #333 has a real external actor canary now: GitHub Copilot CLI on GitHub-hosted Actions read the exact `scope-reality-check` skill, hashed it, applied it, and returned a source-bound receipt. A second run additionally bound the canonical evidence file digest into a GitHub-signed OIDC token and independently verified the RS256 signature and repository/run/workflow claims. Canonical main still only ships PREPARE-only PROMPT_ONLY; it has no trusted evidence admission path that can convert this observation into an executable generic skill handoff.

## Scope

- Add a bounded GitHub OIDC evidence verifier using existing runtime dependencies only.
- Bind evidence to exact repo revision, generic host, task digest, frozen PROMPT_ONLY handoff, skill paths/hashes, GitHub-hosted runner, workflow identity, run ID, and token lifetime.
- Cross-check a current C21 `HostDiscoveryRecord` without treating that declarative record as certification.
- Add a two-phase authorization function that upgrades one verified PROMPT_ONLY handoff to `SKILL_CHECK=PASS / GENERIC_EXACT_REPO_READ`.
- Wire the authorized handoff into Control Tower session start / CLI without changing Arena/Codex native lanes.
- Extend the real GitHub Copilot Actions canary to exercise the authorization path on exact PR head.

## Non-Goals

- Universal proof for Claude, Grok, or Manus.
- Provider-specific model adapters.
- Release, deployment, promotion, branch deletion, or closing Issue #333 before independent review.
- Reusing closed PR #334 as a merge unit.
- Treating C21 provenance strings, self-authored receipts, or local hashes alone as trusted actor proof.

## Requirements

1. Evidence schema is bounded and deterministic; evidence bytes are hashed exactly.
2. OIDC audience equals `p2p-generic-repo-read:<sha256(evidence bytes)>`.
3. RS256 token signature is verified against GitHub OIDC JWKS; issuer, token time bounds, repository, run_id, workflow identity/SHA, runner environment, and audience must match.
4. Current task text and frozen PROMPT_ONLY handoff fingerprint must match the evidence.
5. C21 discovery host identity, availability, transport, repo-bound environment, `can_read_files=SUPPORTED`, project binding, and freshness must match the verified actor.
6. The verified skill path/hash set must equal the frozen handoff and current repo files.
7. Success returns `SKILL_CHECK=PASS`, `SKILL_HOST_MODE=GENERIC_EXACT_REPO_READ`, `PERMISSION_WIDENED=NO`; it does not widen task scope or Owner permissions.
8. Arena/Codex routing remains byte/behavior compatible.
9. Generic active-session reuse revalidates or uses only still-valid evidence; stale proof cannot silently keep authorizing.
10. Exact-head Shield + live GitHub Copilot Actions canary must pass before Supervisor handoff.

## Acceptance Criteria

- Positive: a fresh GitHub-hosted Copilot CLI run on exact repo head, using the frozen task/skill handoff, reaches an executable generic handoff and Control Tower prompt with exact skill path/hash.
- Negative: forged signature, wrong kid/audience/repo/head/workflow/run/host/task/skill, expired/future token, self-hosted runner, altered evidence bytes, stale/mismatched C21 record, or missing evidence => BLOCKED.
- Native Arena/Codex regressions remain green.
- No second router/trust registry/provider adapter is introduced.
- Issue #333 B1 real read-and-apply proof remains source-bound and externally inspectable.
- Independent Supervisor returns PASS on exact final PR head before merge.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect canonical main, Issue #333, merged PROMPT_ONLY, closed #334, live Copilot canary, C20/C21/C36 surfaces, and GitHub OIDC behavior; classify each surface and set the next implementation slices.
  - Implementation Gate: no production implementation starts until `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-actual-status.md` records the P0 decision.
  - Acceptance: current status distinguishes correct, partial, missing, blocked, and preserve-only surfaces.

### P1: Trusted external repo-read admission

- Phase Goal: turn the proven external read-and-apply event into a fail-closed executable generic handoff without weakening PROMPT_ONLY.
- Phase Boundary:
  - In scope: OIDC evidence verification, C21 cross-check, frozen-handoff/task binding, Control Tower/CLI wiring, tests, live canary.
  - Out of scope: provider-specific adapters, release/deploy/promotion, unrelated governance.
  - Dependencies: current main `3cc481a...`, GitHub OIDC issuer/JWKS, existing C20/C21 and PROMPT_ONLY contracts.
- Phase Implementation Rule: implement P1-A then P1-B; verify and commit each slice.

- Ordered Slice List:
  - P1-A: Implement GitHub-OIDC-bound evidence verifier and authorization primitive.
  - P1-B: Wire verified generic handoff into Control Tower/CLI and run exact-head live canary.

- [ ] P1-A: Implement GitHub-OIDC-bound evidence verifier and authorization primitive.
  - Goal: mechanically distinguish a GitHub-signed real actor observation from caller-authored JSON.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/skill_consumption.py`, one small evidence-verifier module, focused tests.
    - Inspect-only: C20/C21 host contracts, current PROMPT_ONLY builder, C36 host attestation.
    - Preserve-only: Arena/Codex modes and PROMPT_ONLY non-authorization behavior.
    - Out of scope: session persistence and CLI wiring (P1-B).
  - Non-Goals: generalized OIDC framework or cloud-provider abstraction.
  - Pre-flight Questions:
    - Data source: GitHub-signed OIDC JWT + canonical evidence JSON + current C21 discovery record.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A — library/CLI governance code only.
    - Playwright target: N/A.
    - Behavior test: focused unit tests plus live canary later.
    - Cleanup/quarantine: temp evidence files remain workflow-local.
    - External side effects: JWKS HTTPS read only; fail closed on unavailability.
    - N/A notes: no UI/DB.
  - Work Steps:
    1. Add strict OIDC/evidence verification and frozen handoff/task/C21 cross-check.
       - UI flow check: N/A.
       - DB/data flow check: canonical JSON bytes -> SHA-256 audience -> JWT verification -> handoff binding.
       - Render location check: N/A.
       - Mini QA: focused unit tests.
       - Evidence target: forged/mismatch/freshness matrix.
    2. Return a source-bound `GENERIC_EXACT_REPO_READ` PASS handoff only after all gates.
       - UI flow check: N/A.
       - DB/data flow check: verified PROMPT_ONLY handoff -> authorized generic handoff; no permission widening.
       - Render location check: N/A.
       - Mini QA: positive + negative handoff tests.
       - Evidence target: exact selected skill path/hash preserved.
  - Implementation Gate:
    - Anvien: N/A because current `AGENTS.md` sets `ANVIEN_ENABLED=NO`.
    - Existing PROMPT_ONLY P1/P2/P3 guards must remain unchanged.
  - Acceptance:
    - Source: verifier has no fail-open branch.
    - Runtime/UI: N/A.
    - DB/data: no new store; evidence is input-only and existing Control Tower ledger remains canonical.
    - Behavior test: positive trusted OIDC evidence passes; negative matrix blocks.
    - Cleanup/quarantine: no persistent temp evidence.
    - Evidence IDs: E1-P1A-*.
    - Actual-status rows refreshed: trusted evidence verifier; generic authorization primitive.
  - Evidence Targets: source diff, focused tests, live OIDC proof.
  - Actual-status Update: missing -> correct for evidence verification primitive.
  - Commit Boundary: commit after P1-A acceptance passes.

- [ ] P1-B: Wire verified generic handoff into Control Tower/CLI and exact-head canary.
  - Goal: make the trusted evidence useful without bypassing the existing single router.
  - Scope Boundary:
    - Editable: Control Tower handoff, CLI, focused tests, canary workflow.
    - Inspect-only: P1-A verifier and existing ledger/prompt serializer.
    - Preserve-only: Arena/Codex and owner/deploy/promotion boundaries.
    - Out of scope: release or universal executor certification.
  - Non-Goals: auto-launching a remote provider.
  - Pre-flight Questions:
    - Data source: authorized handoff from P1-A.
    - Display permission: N/A.
    - DB read/write: existing execution ledger only.
    - Render location: generated execution prompt.
    - UI behavior: N/A.
    - Docker/Playwright: N/A.
    - Behavior test: exact-head Control Tower + live Copilot Actions canary.
    - Cleanup/quarantine: workflow temp files only.
    - External side effects: one GitHub Actions canary.
    - N/A notes: no UI.
  - Work Steps:
    1. Accept only a verified generic handoff in session start/recommendation and preserve it in the existing ledger.
       - UI flow check: N/A.
       - DB/data flow check: no second store; event SKILL_HANDOFF remains canonical session evidence.
       - Render location check: generated prompt contains exact source-bound generic handoff.
       - Mini QA: focused Control Tower regressions.
       - Evidence target: no stale/cross-host replay.
    2. Add CLI file inputs for evidence/JWT/C21 record and execute the live exact-head canary.
       - UI flow check: N/A.
       - DB/data flow check: bounded files -> verifier -> existing Control Tower path.
       - Render location check: CLI JSON output and Actions transcript.
       - Mini QA: Shield + live canary.
       - Evidence target: external actor read, OIDC verified, generic session authorized, exact path/hash present.
  - Implementation Gate:
    - P1-A acceptance must be PASS.
  - Acceptance:
    - Source: only the verified generic lane changes.
    - Runtime/UI: exact-head GitHub Actions canary PASS.
    - DB/data: existing ledger only.
    - Behavior test: native regressions + generic positive/negative suite.
    - Cleanup/quarantine: no extra state store.
    - Evidence IDs: E1-P1B-*.
    - Actual-status rows refreshed: Control Tower generic lane and CLI.
  - Evidence Targets: exact-head Shield and canary run IDs.
  - Actual-status Update: generic execution admission missing -> bound-correct if proven.
  - Commit Boundary: commit after P1-B acceptance passes.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independent exact-head acceptance.
  - Work Steps: fresh Supervisor review source/diff, prior blockers, tests, Shield, and live canary; fix only rejected scope and re-review.
  - Implementation Gate: P1-A/P1-B complete or explicitly blocked.
  - Acceptance: Supervisor PASS or evidence-bound blocker.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: final diff contains only the trusted admission path and required evidence/docs.
  - Work Steps: remove failed artifact-attestation experiment from production branch, stale helpers, and unused tests; Supervisor checks cleanup.
  - Implementation Gate: implementation finished.
  - Acceptance: no dead plan-created artifacts.
- [ ] Pn-C: Close the plan.
  - Goal: record final validation, commits, exact-head state and handoff.
  - Work Steps: run required tests/Shield/canary, record evidence/benchmark, verify branch diff, and hand to Supervisor.
  - Implementation Gate: Pn-A/Pn-B complete or blocked.
  - Acceptance: exact-head evidence is complete and no merge occurs before Supervisor PASS.

## Risk Notes

- GitHub OIDC proves the workflow identity and binds evidence bytes; it does not magically prove arbitrary Claude/Grok/Manus product identity.
- The workflow itself is authorization code. Admission must bind to the expected workflow path/revision and GitHub-hosted runner.
- JWT expiry is an intended freshness gate, not a nuisance to bypass.
- Network/JWKS failure must BLOCK rather than fall back to self-report.
