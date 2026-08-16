# P2P Beginner Lifecycle Behavioral Certification Actual Status

Title: P2P Beginner Lifecycle Behavioral Certification
Date: 2026-08-12
Status: Complete; supervisor-pass
Companion plan: `docs/plans/2026-08-12-p2p-beginner-lifecycle-certification/2026-08-12-p2p-beginner-lifecycle-certification-plan.md`
Companion evidence: `docs/plans/2026-08-12-p2p-beginner-lifecycle-certification/2026-08-12-p2p-beginner-lifecycle-certification-evidence.md`
Companion benchmark: `docs/plans/2026-08-12-p2p-beginner-lifecycle-certification/2026-08-12-p2p-beginner-lifecycle-certification-benchmark.md`

## Purpose

This living file records the current state before and during implementation. The corrected baseline run is authoritative; the earlier failed fixture-copy setup is recorded as harness setup evidence only and is excluded from product conclusions.

## Scope

Target scope: isolated behavioral certification harness, machine-readable result, persistent QA/certification report, and direct behavior tests.

Out of scope: P2P runtime repair, release/v5/immutable source, App Game Truyện, Logistics, all user projects, external providers/catalogs, new specialists, new governance systems, and release publishing.

## Relationship / Impact Evidence

Anvien is not registered for this unpacked P2P package; local source inspection, existing regression, hashes, and CLI evidence are the fallback. The target is not a Git worktree.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `scripts/p2p_beginner_certification.py` | `E0-P0A-SRC1` | local inventory | new evaluator calls existing public CLI/contracts | medium |
| `tests/test_p2p_beginner_certification.py` | `E0-P0A-SRC1` | local inventory | direct behavior/schema coverage for new evaluator | low |
| `scripts/p2p_workflow.py` | `E0-P0A-RUN1..E0-P0A-RUN4` | existing consumers | measured black-box subject; preserve-only | critical preserve warning |
| capability registry/router/doctor | `E0-P0A-INV1`, `E0-P0A-ROUTE1`, `E0-P0A-DOCTOR1` | existing consumers | invariant/readiness subjects; preserve-only | critical preserve warning |
| release artifact and `source/` | `E0-P0A-BOUNDARY1` | protected inventory | release/source boundary; preserve-only | critical |
| reports/QA and plan artifacts | `E0-P0A-SRC1` | new output surfaces | persistent evidence output | low |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| Beginner certification harness | standard-library-only driver executes actual CLI and public contracts | isolated black-box evaluator with BC1–BC29 coverage | correct | local | `E1-P1A-RUN1..E1-P1C-TEST4` | preserve |
| Four project shapes | A–D plus A same-root journey executed with 205 machine rows | four synthetic projects with one same-root journey | correct | local | `E2-P2A-CERT1..E2-P2A-CERT6` | preserve |
| Beginner discovery | public beginner discovery returns product questions, but workflow Goal contract has no questions and Vietnamese prompts classify DIRECT TASK | product questions surfaced without technical offload | partial | existing runtime | `E0-P0A-BEGINNER1` | evaluator records gap; no runtime repair |
| Technical-choice shielding | no `technical_questions` property and no unnecessary technical question observed | hide implementation choices; surface only owner decisions | partial | existing runtime | `E0-P0A-RUN1..E0-P0A-RUN4` | evaluator measures both shield and missing discovery |
| Owner-decision boundary | `decision_required` null for baseline product prompts | product/privacy/destructive choices identified when material | partial | existing runtime | `E0-P0A-RUN1..E0-P0A-RUN4` | evaluator pressure case |
| Lifecycle continuity | four scenarios and one longitudinal run now have stage records | staged evidence across lifecycle | correct for evaluator; runtime coverage remains partial | existing runtime | `E2-P2A-CERT4..E2-P2A-CERT5` | preserve; report limitation |
| Debug/recovery | blocked fixture remains BLOCKED; controlled repair is rechecked; diagnosis remains generic | blocked evidence, recovery, and honest completion | partial | existing runtime | `E1-P1B-EVAL5`, `E2-P2A-CERT4` | future runtime gap only |
| Retrieved instruction/trust | public trust boundary and FACT/RAG contracts are present | content cannot grant authority; conflict visible | correct for contract baseline; behavioral coverage absent | existing runtime | `E0-P0A-TRUST1` | supplement P1-B |
| UI/UX routing | route mismatches observed for generic internal/mobile/content prompts; tiny UI path is lightweight | UIUX adapts by project type and Aesthetica is never simulated | partial | existing router | `E0-P0A-ROUTE1..E0-P0A-ROUTE4` | evaluator records gap |
| Security/data boundary | high-risk route selects a bounded set; no owner approval behavior proven | security/data choices and approval boundary visible | partial | existing runtime | `E0-P0A-SEC1` | evaluator pressure case |
| Deployment readiness | no real deploy was attempted; fixture PASS can be returned | unsupported deployment never reported successful | partial | existing runtime | `E0-P0A-DEPLOY1` | classify as limitation |
| Maintenance/upgrade | no same-project maintenance/upgrade behavioral run | state continuity and honest upgrade/migration evidence | missing | local | `E0-P0A-RUN1..E0-P0A-RUN4` | edit P1-A/P2-A |
| WHY/audit | distributed Goal/report/ledger artifacts exist | reconstructable evidence chain without CoT | partial | existing runtime | `E0-P0A-AUDIT1` | supplement P1-B |
| Persistent report/machine result | QA Markdown/JSON report with 205 valid rows and required fields exists | required fields and minimum rows | correct | local | `E2-P2A-CERT1..E2-P2A-CERT6` | preserve |
| Direct evaluator tests | two direct tests cover full behavior, schema, false-PASS, and isolation guards | black-box behavior and false-PASS guards | correct | local | `E1-P1C-TEST1..E1-P1C-TEST4`, `E2-P2B-REG1` | preserve |
| Canonical 8 / denominator | exact 8 and 8/8 confirmed by doctor | unchanged exact invariant | correct / preserve-only | registry | `E0-P0A-DOCTOR1` | preserve |
| Aesthetica | optional/supporting, executable but not healthy/identity-verified; no simulation observed | optional only; never in denominator or simulated | correct / preserve-only | manifest/profile | `E0-P0A-DOCTOR1`, `E0-P0A-ROUTE1` | preserve |
| p2p-uiux | healthy and present | preserved and independently routed | correct / preserve-only | capability registry | `E0-P0A-DOCTOR1` | preserve |
| Existing regression | prior 43/43 PASS | rerun after harness change | correct baseline | tests/gates | `E0-P0A-REG1` | run P2-B |
| Release/source boundary | release SHA and source inventory known; target is development source | unchanged | correct / preserve-only | protected paths | `E0-P0A-BOUNDARY1` | compare after run |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-12 | approved SPEC inspection and corrected isolated baseline | all target surfaces | initial classification | `E0-P0A-SRC1..E0-P0A-BOUNDARY1` | implement only missing evaluator/report/test surfaces |
| R1 | 2026-08-12 | P1 harness implementation and direct behavior tests | evaluator/report/test surfaces | missing -> correct; runtime readiness gaps preserved as partial | `E1-P1A-RUN1..E1-P1C-TEST4` | execute certification and regression |
| R2 | 2026-08-12 | final certification, 45/45 regression, doctor, drift, hash and secret checks | all target surfaces | P1/P2 complete; canonical/release/user boundaries unchanged | `E2-P2A-CERT1..E2-P2B-REG8`, `CLOSE-SUPERVISOR1` | close plan |

## Phase Touch Map

| Unit / File / Surface | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|
| `scripts/p2p_beginner_certification.py` | P1-A/P1-B | edit | `E0-P0A-SRC1` | new evaluator only; no runtime mutation |
| `tests/test_p2p_beginner_certification.py` | P1-C | edit | `E0-P0A-SRC1` | behavior tests, not static-only tests |
| existing workflow/router/doctor/contracts | P1/P2 | inspect-only | `E0-P0A-RUN1..E0-P0A-DOCTOR1` | no runtime repair |
| `reports/QA/**` | P2-A | generate | `E0-P0A-SRC1` | development source only; no secrets/CoT |
| `source/**`, release/v5/immutable artifacts | all | preserve-only | `E0-P0A-BOUNDARY1` | do not touch |
| user projects/App Game Truyện/Logistics | all | do-not-touch | `E0-P0A-BOUNDARY1` | no writes or upgrade |

## Detailed Findings

### Baseline runtime

Current state: the corrected baseline runs all four prompts to `PASS` on deterministic fixtures, but classifies them as `DIRECT TASK`, does not expose Goal questions, and uses quorum 1 for ordinary prompts. This is useful evidence of workflow execution, not proof of beginner lifecycle readiness.

Required state: an evaluator must expose those gaps stage by stage without changing the runtime.

Evidence: `E0-P0A-RUN1..E0-P0A-RUN4`.

Classification: partial.

Allowed next action: implement the isolated evaluator.

Forbidden next action: silently add questions or change routing in the runtime under this Goal.

### Protected invariants

Current state: capability doctor reports exact canonical 8, denominator 8, full quorum 8/8, Aesthetica optional/non-simulated, and p2p-uiux healthy.

Required state: unchanged after harness work.

Evidence: `E0-P0A-DOCTOR1`, `E0-P0A-BOUNDARY1`.

Classification: correct / preserve-only.

Allowed next action: rerun after implementation.

Forbidden next action: add Aesthetica to quorum or simulate its output.

## Implementation Gate

- [x] Target scope is listed in the matrix.
- [x] Each target unit has a status and evidence IDs.
- [x] Preserve-only surfaces are named.
- [x] Corrected baseline is distinguished from failed setup attempt.
- [x] P0 refresh row exists.
- [x] Next phase decisions are bounded by current evidence.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps may proceed as written.
- [x] P0 complete. Existing runtime, release/source, and user-project surfaces are preserve-only.

## Final Status Decision

- [x] Harness implementation correct and independently verified.
- [x] Beginner readiness is `CERTIFIED_WITH_LIMITATIONS`, not unconditional certification.
- [x] Runtime gaps remain explicitly recorded; no runtime repair was hidden in this Goal.
- [x] Exactly one next Goal is recommended: `P2P Native Decision Trace`.
- [x] No release artifact, v5 artifact, source baseline, or user project was modified.

Decision note: supervisor PASS applies to the evaluator and evidence package. The readiness limitation is real and comes from observed behavior: discovery questions are not persisted in Goal contracts, some normal beginner prompts are blocked by current Goal classification, deployment is unproven, upgrade is synthetic-state-only, and WHY is distributed rather than a single trace.

Decision note: the missing work is an evaluator/report/test surface. The runtime gaps are intentionally carried as measured residual risk; no runtime repair is authorized by this Goal.
