# P2P-C12 Bounded Foreground Task Execution Controller Benchmark

## Metadata

- Date: `2026-08-14`
- Status: `BLOCKED / technical measurements complete; workflow helper closure blocked`
- Plan: `docs/plans/2026-08-14-p2p-c12-bounded-foreground-execution/2026-08-14-p2p-c12-bounded-foreground-execution-plan.md`
- Benchmark root: `.tmp/p2p-c12/benchmarks/`

## Benchmark Rules

- Record measured values only; do not convert test duration into product
  performance claims.
- Use isolated repo-local temporary roots and the same fixture across variants.
- A benchmark is not proof of safety, evidence binding, or product quality.
- Do not benchmark or enable background work, delegation, network, or external
  providers; those are forbidden by this goal.

## Baseline Measurements

| Measurement | Command/source | Result | Interpretation |
|---|---|---|---|
| Root graph scan | `anvien analyze . --force --skip-git ... --json` | 334 files scanned; 33 code files parsed; 12,707 nodes; 14,434 relationships | Graph orientation only |
| System graph scan | `anvien analyze .p2p/system --force --skip-git ... --json` | 45 files scanned; 37 code files parsed; 5,499 nodes; 7,015 relationships | Runtime topology orientation |
| Workflow plan helper | `python scripts/p2p_workflow.py plan ... --json` | Timed out twice while scanning the unpacked tree | Orchestration limitation, not runtime evidence |
| Package impact | Anvien upstream impact | package functions LOW; doctor foundation paths CRITICAL | Scope warning for narrow edits |

## Measured C12 Results

| Measurement | Result | Evidence |
|---|---:|---|
| Focused controller tests | 20 passed / 20; 1.153 s | `python -m unittest -q tests.test_p2p_foreground_execution` |
| C11 + C06 regression slice | 36 passed / 36; 1.077 s | `tests.test_p2p_task_state tests.test_p2p_live_execution` |
| Full unittest suite | 159 passed / 159; 94.719 s | `python -m unittest discover -s tests -p 'test*.py'` |
| Isolated interruption/resume trials | 2 | focused test plus portable CLI smoke |
| Project eval pairs | 5 cases, 2 trials each | `p2p_eval.py gate`, PASS, delta 0.0 |
| Governance drift | PASS | `p2p_governance.py drift` |
| Secret scan | PASS, 0 findings | `secret_scan.py --source .p2p/system` |
| Candidate r3 size | 2,446,196 bytes | superseded by r4 after CLI fallback fix |
| Candidate r4 size | 2,446,204 bytes | package build output |
| Candidate r5 size | 2,446,240 bytes | superseded after owner-gate persistence correction |
| Candidate r6 size | 2,446,509 bytes | superseded; retained for immutable history |
| Candidate r7 size | 2,446,508 bytes | final package build output after runtime-lock refresh |
| Candidate r7 SHA-256 | `939f918875f57906112fcb50f7e145ef15187cbe29ae50c4cc15dd888709c522` | final unpromoted candidate |

The r6 correction durably records a missing mutation owner decision as C11
`WAITING_OWNER` and performs no action. r7 is the same corrected source rebuilt
after the protected runtime lock was refreshed. These are safety-state and
lifecycle measurements, not performance claims.

## Required Measurements

- Focused C12 test count, pass count, fail count, and elapsed time.
- At least two isolated interruption/resume trials with identical fixture and
  separate state roots.
- BFE/structural/beginner matrix counts by variant and result.
- Full unit/regression/doctor/governance/security/lifecycle elapsed times as
  validation evidence only.
- Candidate archive size and SHA-256 if a candidate is created.

## Variant Matrix

| Variant | Purpose | Required constraints |
|---|---|---|
| Direct success | One scoped action + independent verifier | one task, no retry, no child |
| Transient bounded retry | Verify finite retry boundary | exact retry budget, no background loop |
| Verification failure | Ensure action output is not DONE proof | task remains ACTIVE/NEEDS_RECHECK |
| Permission/owner gate | Verify fail-closed preflight | no action is invoked |
| Interrupted before verify | Verify fresh resume | read-only verifier only |
| Control-plane failure | Verify bounded stop | no spawn, no retry storm |
| Structural forbidden paths | Attempt scheduler/queue/worker/network/identity | all refused or absent |

## Benchmark Status

All required measurements are complete and backed by the evidence ledger and
final Supervisor report. The workflow-helper closure remains `BLOCKED` because
its linter split the combined implementation/verification request into
independent objectives; this is not a product-performance claim or controller
runtime failure.
