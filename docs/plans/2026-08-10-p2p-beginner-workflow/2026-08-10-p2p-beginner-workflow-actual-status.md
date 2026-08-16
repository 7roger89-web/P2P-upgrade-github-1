# P2P beginner workflow Actual Status

Title: P2P beginner workflow
Date: 2026-08-10
Status: PASS. P0, P1, P2, supervisor review, and closure evidence complete.
Companion plan: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-plan.md`
Companion evidence: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-evidence.md`
Companion benchmark: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-benchmark.md`

## Scope

Target scope: orchestration and reuse around the existing canonical P2P Codex runtime.

Out of scope: immutable source snapshot, unrelated application work, replacement governance systems, PXPIPE/network/hooks/connectors, release/publish.

## Relationship / impact evidence

Anvien was queried for the target repository and reported that the path is not registered; its only indexed repository is unrelated. Local `rg`, package doctor, and direct file inspection are the fallback evidence for this unpacked package.

| Unit / file / surface | File detail evidence | Related count | Relationship summary | Impact note |
|---|---|---:|---|---|
| `scripts/p2p_workflow.py` | `E0-P0A-ANV1` unavailable; local inventory `E0-P0A-SRC1` | local package path | new orchestration helper consumed by entry skill/installer/doctor | medium |
| `scripts/p2p_eval.py` | `E0-P0A-ANV1` unavailable; local inventory `E0-P0A-SRC1` | local package path | suite design and gate consumer | medium |
| `.agents/skills/p2p/SKILL.md` | `E0-P0A-ANV1` unavailable; local inventory `E0-P0A-SRC1` | local package path | normal natural-language dispatcher | high |
| `scripts/doctor.py`, installers, runtime lock | `E0-P0A-ANV1` unavailable; local inventory `E0-P0A-SRC1` | local package path | distribution and protected-runtime validation | high |
| `source/8.4.6-C/` | local count/hash evidence `E0-P0A-GATE1` | 152 immutable files | historical baseline only | preserve-only |

## Current status matrix

| Unit | Current state | Required state | Status | Evidence | Next plan decision |
|---|---|---|---|---|---|
| Goal/dispatcher | one helper is wired from the main skill and creates a bounded Goal Contract | bounded contract + automatic bounded run | correct | `E1-P1A-CODE1`, `E1-P1B-DIST1` | final gates |
| Project bootstrap | helper creates/reuses profile, policy reference, state dirs, contract, status, evidence, ledger, and eval suite | idempotent project bootstrap with references | correct | `E1-P1A-CODE1`, `E1-P1A-ACCEPT1` | final gates |
| Agent selection | helper selects the smallest relevant exact named-agent set and preserves explicit full-quorum intent | smallest automatic named-agent selection for ordinary goals | correct | `E1-P1A-CODE1`, `E1-P1A-TEST1` | final gates |
| Project eval design | `p2p_eval.py design` creates five bounded project-specific cases and reuses valid suites | minimal goal/project-derived suite with reuse | correct | `E1-P1A-CODE2`, `E1-P1A-TEST1` | final gates |
| Scope/terminal guard | helper persists finite scope/out-of-scope, affected controls, evidence reuse, and PASS/BLOCKED/REJECT stop rules | PASS/BLOCKED/REJECT plus bounded work/evidence reuse | correct | `E1-P1A-CODE1`, `E1-P1A-ACCEPT1` | final gates |
| CAPSULE/status | each run writes project status, a compact CAPSULE reference, report, and JSONL execution events | status references authoritative artifacts and resumes | correct | `E1-P1A-CODE1`, `E1-P1A-ACCEPT1` | final gates |
| Execution Ledger | one project-local JSONL ledger records bootstrap, verification, reuse, and terminal events | one persistent project-local ledger for workflow runs | correct | `E1-P1A-CODE1`, `E1-P1A-ACCEPT1` | final gates |
| Existing governance | FACT_LEDGER, Live Specs, Approval, Drift, Eval/RAG helpers pass package baseline | preserve and reference unchanged controls | correct | `E0-P0A-GATE1` | preserve-only |
| Named agents | eight TOML profiles parse and identities are present | remain valid and never simulated | correct | `E0-P0A-GATE1` | preserve-only |
| Source baseline | 152/152 source inventory and hashes pass | remain immutable | correct | `E0-P0A-GATE1` | preserve-only |

## Phase touch map

| Unit | Plan item | Touch mode | Constraint |
|---|---|---|---|
| `scripts/p2p_workflow.py` | P1-A | edit | single orchestration helper; no second governance system |
| `scripts/p2p_eval.py` | P1-A | edit | preserve v2 gate and existing suite behavior |
| `.agents/skills/p2p/SKILL.md` | P1-B | edit | add default workflow only; preserve existing modes |
| `.agents/skills/p2p-scope`, `p2p-eval`, `p2p-capsule`, `p2p-quorum` | P1-B | edit | guidance only, no new runtime gates |
| `install.ps1`, `install.sh`, `scripts/doctor.py` | P1-B | edit | distribute/check the one helper |
| `manifest/package.json`, `governance/runtime-manifest.lock.json` | P1-B | regenerate/edit | lock must be generated after final protected changes |
| `source/8.4.6-C/**` | all | preserve-only | immutable 152-file baseline |

## Status refresh log

| Refresh | Date | Basis | Status changes | Evidence | Next phase update |
|---|---|---|---|---|---|
| R0 | 2026-08-10 | package inspection before implementation | initial matrix recorded | `E0-P0A-SRC1`, `E0-P0A-GATE1`, `E0-P0A-ANV1` | P1 edits limited to missing/partial rows |
| R1 | 2026-08-10 | implementation, unit tests, deterministic acceptance, and installed-fixture smoke checks | seven-command helper, five-case eval design, selective reuse, beginner report, and distribution wiring are now correct; final lock/doctor/drift/supervisor remain | `E1-P1A-CODE1`, `E1-P1A-CODE2`, `E1-P1A-TEST1`, `E1-P1A-ACCEPT1`, `E1-P1B-DIST1`, `E1-P1B-INSTALL1` | refresh protected lock, run final gates, supervisor review |
| R2 | 2026-08-10 | final runtime lock, package doctor/drift, fresh installed-project-5 verification, and independent supervisor review | protected lock PASS (178 files), package doctor PASS, package drift PASS, fresh installer/doctor/helper PASS; only expected real-project-eval readiness warning remains; supervisor PASS | `E2-P2A-LOCK1`, `E2-P2A-PACKAGE1`, `E2-P2A-DRIFT1`, `E2-P2A-FRESH1`, `E2-P2A-WORKFLOW1`, `CLOSE-SUPERVISOR1` | close complete |

## Detailed findings

### Existing governance

Current state: package doctor reports PASS for 22 skills, eight agents, FACT_LEDGER/Live Specs/Drift/Approval integrity, source 152/152, source hashes, conversion map, and package manifest.

Required state: unchanged controls remain authoritative and are called only when relevant.

Classification: correct / preserve-only.

Forbidden next action: creating parallel FACT, Drift, Approval, RAG, or Ledger systems.

### Implemented orchestration

Current state: the main skill delegates ordinary natural-language build/finish requests to `scripts/p2p_workflow.py`; the helper persists the Goal Contract, project profile/policy references, status, trusted evidence, execution ledger, capsule, report, selective update flow, and terminal state.

Required state: one helper creates those artifacts idempotently and the skill tells Codex to use it for ordinary natural-language build/finish requests.

Classification: correct; final artifact and gate verification is closed by the supervisor PASS review.

Allowed next action: refresh the protected-runtime lock, run package/fresh-install gates, complete supervisor review, and close the plan.

## Implementation gate

- [x] Target scope is listed in the matrix.
- [x] Each target unit has a status and evidence IDs.
- [x] Anvien availability and local fallback are recorded.
- [x] Phase touch map defines edit/preserve-only boundaries.
- [x] Existing correct governance/source/agent surfaces are preserve-only.
- [x] P0 refresh row exists.
- [x] Next phase decisions reflect actual status.

## Final P0 decision

- [x] P0 complete. Next phase status, next action, and work steps are bounded by the matrix.

Decision note: the package doctor baseline is already PASS. Only the usability/orchestration gaps named in the user request are editable.

## Final gate status

- [x] Direct source compilation and four workflow unit tests pass.
- [x] Safe new-project and existing-project acceptance fixtures pass.
- [x] Package doctor passes with 22 skills, eight agents, source 152/152, and helper distribution.
- [x] Fresh installed fixture doctor and installed helper run pass; expected release-readiness warning is documented as an absent real project eval, not a package failure.
- [x] Final protected-runtime lock and governance drift pass.
- [x] Supervisor review and closure report.
