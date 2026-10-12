# Issue 333 OIDC Generic Admission Actual Status

Title: Issue 333 OIDC Generic Admission
Date: 2026-10-12
Status: P0 Complete
Companion plan: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-plan.md`
Companion evidence: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-evidence.md`
Companion benchmark: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-benchmark.md`

## Purpose

Record the real state before implementing trusted generic execution admission.

## Freshness / Refresh Rules

Refresh after each implementation slice and before the next slice if repo or provider evidence changes.

## Scope

Target scope:
- trusted GitHub-OIDC-bound admission from existing PROMPT_ONLY to GENERIC_EXACT_REPO_READ.

Out of scope:
- provider-specific Claude/Grok/Manus adapters, deployment, release, promotion, unrelated governance.

## Relationship / Impact Evidence

Anvien is disabled by current Owner policy; relationship-count evidence is N/A. Direct source inspection and tests define the bounded touch map.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| skill_consumption.py | E0-P0A-MAIN1 / direct source | N/A | single router + PROMPT_ONLY serialization/receipt validation | high |
| control_tower_handoff.py | direct source | N/A | session prompt + existing execution ledger | high |
| scripts/p2p_control_tower.py | direct source | N/A | CLI transport only | medium |
| host_selection.py / host_executor.py | E0-P0A-C201 | N/A | C20/C21 declarative host evidence | preserve/consume |
| host_attestation.py | E0-P0A-C361 | N/A | C36 local host evidence | inspect-only |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| correct | Already behaves as required. | Preserve. |
| partial | Some behavior exists, gaps remain. | Change only missing parts. |
| missing | Required behavior absent. | Implement bounded missing piece. |
| blocked | Cannot proceed safely. | Stop until evidence/authority resolves. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| PROMPT_ONLY | merged, source-bound, PREPARE-only, non-authorizing | unchanged first phase | correct | N/A | E0-P0A-MAIN1 | preserve |
| Real external actor read/apply | Copilot CLI Actions run proves exact read/hash/apply | at least one real actor proof | correct | N/A | E0-P0A-CANARY1 | consume |
| Trusted evidence signature | GitHub OIDC RS256 + evidence-digest audience proven | runtime-verifiable evidence issuer | partial | N/A | E0-P0A-CANARY2 | implement P1-A verifier |
| Artifact attestation | unavailable for this private user-owned repo | not required if OIDC path works | blocked / discarded | N/A | E0-P0A-PROVIDER1 | do not use |
| C20/C21 | declarative discovery exists | cross-check availability/environment/project, not certification | correct | N/A | E0-P0A-C201 | preserve/consume |
| C36 | local host attestation exists | must not substitute for external actor proof | partial for this scope | N/A | E0-P0A-C361 | inspect-only |
| Generic execution authorization | absent on canonical main | PASS only after trusted evidence | missing | N/A | E0-P0A-MAIN1 | implement P1-A/P1-B |
| Control Tower generic source-bound handoff | generic host session lacks trusted skill handoff | attach only verified generic PASS handoff | missing | N/A | direct source | implement P1-B |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-10-12 | main 3cc481a + canary run 38217565828 | Issue #333 B1 trust boundary | external actor proof missing -> correct; signed binding missing -> partial/proven OIDC; generic admission remains missing | E0-P0A-* | proceed P1-A |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| skill_consumption.py | capabilities.json / skill SKILL.md files | router/source binding | P1-A | edit | E0-P0A-MAIN1 | preserve one router/max-3/source hashes |
| new evidence verifier | GitHub OIDC JWKS | trusted evidence issuer | P1-A | edit | E0-P0A-CANARY2 | stdlib only; fail closed |
| host_selection.py | host_executor.py | C20/C21 | P1-A | preserve-only/consume | E0-P0A-C201 | discovery != certification |
| control_tower_handoff.py | existing ledger + build_execution_prompt | prompt/session consumer | P1-B | edit | direct source | no second store |
| scripts/p2p_control_tower.py | ControlTower API | CLI consumer | P1-B | edit | direct source | bounded file inputs |
| Arena/Codex lanes | prepare_skill_handoff | native regression | P1-A/P1-B | preserve-only | E0-P0A-MAIN1 | unchanged modes |

## Detailed Findings

### Trusted generic admission

Current state:

PROMPT_ONLY can select and freeze exact skills for a generic host but intentionally sets EXECUTION_AUTHORIZED=NO. A real external actor and a GitHub-signed OIDC evidence binding have now been proven outside canonical main.

Required state:

```text
PREPARED + current C21 discovery + GitHub-signed exact evidence + exact task/handoff binding
=> SKILL_CHECK=PASS
=> SKILL_HOST_MODE=GENERIC_EXACT_REPO_READ
=> PERMISSION_WIDENED=NO
otherwise BLOCKED
```

Evidence:
- E0-P0A-CANARY1: real Copilot CLI read/apply trace.
- E0-P0A-CANARY2: GitHub OIDC signature/evidence binding.

Relationship and impact:
- Related file count: N/A (Anvien disabled).
- Relationship summary: single router -> PROMPT_ONLY -> verifier -> existing Control Tower prompt/ledger.
- Impact note: high; this is an execution authorization boundary.

Classification:

missing

Allowed next action:

Implement only P1-A verifier/authorization primitive, then refresh status before P1-B.

Forbidden next action:

Trust C21 provenance strings, receipt JSON, or local C36 machine identity alone; resurrect #334 wholesale; widen provider permissions.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | OIDC proof is viable and artifact attestation is unavailable | implement OIDC verifier only; remove artifact-attestation idea |
| P1-B | generic admission absent | wait for P1-A PASS, then wire existing Control Tower/CLI |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Relationship count N/A is justified by ANVIEN_ENABLED=NO.
- [x] Phase Touch Map lists plan-relevant units.
- [x] Touch modes are defined.
- [x] Correct parts are preserve-only.
- [x] Missing/partial parts have exact next actions.
- [x] Blocked artifact-attestation path is recorded.
- [x] Next phase work reflects current evidence.
- [x] Status Refresh Log has R0.

## Final P0 Decision

- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.

Decision note:

Proceed with P1-A using GitHub OIDC evidence binding. Do not implement artifact-attestation persistence and do not start P1-B until P1-A verifier/negative controls pass.
