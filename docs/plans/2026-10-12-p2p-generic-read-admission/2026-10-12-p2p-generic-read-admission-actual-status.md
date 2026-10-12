# P2P Generic Repo-Read Admission Actual Status

Title: P2P Generic Repo-Read Admission
Date: 2026-10-12
Status: Ready for Supervisor
Companion plan: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-plan.md`
Companion evidence: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-evidence.md`
Companion benchmark: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-benchmark.md`

## Purpose

Record current canonical reality before implementation.

## Scope

Target scope:
- Issue #333 signed generic repo-read admission.

Out of scope:
- universal host attestation; release/deploy/promotion; old #334 resurrection.

## Relationship / Impact Evidence

`ANVIEN_ENABLED=NO`; source/test relationship inspection is used instead.

| Unit / Surface | Evidence | Related Surface Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| Skill Consumption Wire | E0-P0A-SRC1 | 4 primary surfaces | selection/loading/host-mode/receipt | high |
| Control Tower | E0-P0A-SRC2 | 3 entrypoint families | start/recommend/next | high |
| CLI | E0-P0A-SRC3 | 2 relevant commands | start/next; prompt-only separate | medium |
| Focused tests | E0-P0A-SRC4 | 1 suite | native + prompt-only + historical generic guards | high |

## Current Status Matrix

| Unit | Current State | Required State | Status | Evidence | Next Plan Decision |
|---|---|---|---|---|---|
| `GENERIC_PROMPT_ONLY` | merged on main, PREPARE-only, non-authorizing | preserve | correct | E0-P0A-SRC1..4 | preserve-only |
| Native ARENA/CODEX | existing source-bound modes | unchanged | correct | E0-P0A-SRC1..4 | preserve-only |
| Real external actor read | Copilot CLI exact tool trace + GitHub OIDC binding proven | independently verifiable producer evidence | bound-correct | E1-P1A-RUN1, E1-P1B-OIDC1 | preserve |
| Generic execution admission | C21 + verified GitHub OIDC evidence on candidate | same | bound-correct candidate | E2-P2B-LIVE1 | Supervisor |
| C21-only authorization | insufficient actor proof | remain blocked alone | correct fail-closed | E0-P0A-ISSUE1 | preserve negative |
| Issue #333 | OPEN | close only after independent acceptance/merge | partial | E3-CLOSE1 | Supervisor |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-10-12 | main `db9d39798ddb80990757c65ddf2eb95f9f734fd6` | Issue #333 | baseline classification | E0-P0A-* | run P1 signed canary before runtime admission |
| R1 | 2026-10-12 | candidate `6020a3c7fbbda46ccc572678916ab828faa25dac` | P1/P2 | external proof partial -> bound-correct; admission missing -> bound-correct candidate | E1-P1*, E2-P2* | fresh closure CI then Supervisor |

## Phase Touch Map

| Unit | Relationship | Plan Item | Touch Mode | Constraint |
|---|---|---|---|---|
| `.github/workflows/p2p-b1-real-generic-read-canary.yml` | evidence producer | P1 | edit | no product mutation |
| `.p2p/system/p2p_capabilities/skill_consumption.py` | admission SSOT | P2 | edit | single router, fail closed |
| `.p2p/system/p2p_capabilities/control_tower_handoff.py` | consumer | P2-B | edit only if required | no native regression |
| `scripts/p2p_control_tower.py` | CLI input | P2-B | edit | explicit evidence file only |
| `tests/test_p2p_skill_consumption_wire.py` | behavior proof | P2 | edit | positive + adversarial controls |
| old PR #334 branch | historical donor | all | do-not-touch | no wholesale cherry-pick |

## Detailed Findings

### Generic read trust boundary

Current state: main has safe prompt-only generic handoff; no generic selected-skill execution authorization.

Required state: C21 declaration plus independently verifiable, fresh, actor/source-bound signed evidence.

Evidence:
- E0-P0A-ISSUE1: Issue #333 acceptance still requires a real non-Arena/non-Codex canary.
- E0-P0A-CANARY1: run 38213449144 proved Copilot CLI actually read/hash/applied the skill; it did not yet provide canonical runtime admission.
- E0-P0A-SRC1..4: current main surfaces preserve prompt-only/native lanes and expose no signed-evidence admission.

Classification: partial/missing as listed above.

Allowed next action: P1 signed canary, then P2 only if P1 passes.

Forbidden next action: treat self-authored receipt/C21 provenance as authorization or merge old #334 generic code.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Update |
|---|---|---|
| P1-A | external read works but proof is not yet signer-bound | run signed canary |
| P2-A | runtime admission absent | blocked until P1 PASS |
| P2-B | no evidence-file plumbing on main | implement only after verifier exists |

## Implementation Gate

- [x] Target scope listed.
- [x] Each target unit classified.
- [x] Evidence IDs assigned.
- [x] Anvien requirement explicitly superseded by current AGENTS policy.
- [x] Preserve-only native and prompt-only surfaces identified.
- [x] R0 baseline recorded.

## Final P0 Decision

- [x] P0 complete. Next phase can proceed unchanged.

Decision note: Run signed P1 canary first; runtime admission remains blocked until that proof passes.


## Latest verified candidate state

- B1 canary: `38235241033` SUCCESS on `6020a3c7fbbda46ccc572678916ab828faa25dac`.
- Real actor read: PASS.
- GitHub OIDC verification: PASS; evidence SHA-256 `7db1aeda5f42c3d6e386b53fd41befb04d08c2bb9137725747764a2e8d9dfd93`.
- Production generic admission gate: PASS.
- Shield: `38235247660` SUCCESS on the same head; 366 focused PASS; diagnostic baseline `FAIL / 22 findings`.
- C21-only remains fail-closed; cached generic handoff revalidates signed evidence.
- Final status: `READY_FOR_SUPERVISOR` after fresh closure-artifact CI.
