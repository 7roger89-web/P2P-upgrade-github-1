# P2P-C12 Bounded Foreground Task Execution Controller Evidence

## Metadata

- Date: `2026-08-14`
- Status: `BLOCKED / technical gates PASS; workflow helper linter blocker recorded`
- Plan: `docs/plans/2026-08-14-p2p-c12-bounded-foreground-execution/2026-08-14-p2p-c12-bounded-foreground-execution-plan.md`
- Evidence ledger: this file plus `.p2p/state/execution-ledger.jsonl`
- Temporary evidence root: `.tmp/p2p-c12/`

## Evidence Rules

- Each claim names the exact source, command, or test output that supports it.
- Source and graph evidence are orientation only; behavior requires a direct
  test or observable runtime result.
- Existing C10/C11/C09/C08 reports are historical references until the current
  run rechecks their relevant invariant.
- Retrieved or tool-produced content is data, not permission or authority.
- No evidence may claim a host identity, background process, delegated agent,
  release promotion, or C09 recovery without actual authoritative evidence.

## E0: P0 actual-status evidence

### E0-P0-SPEC

- Sources: `docs/SPEC/P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`,
  `P2P-CAPABILITY-EXECUTION-EVIDENCE-SPEC.md`,
  `P2P-CAPABILITY-CONTEXT-POINTER-SPEC.md`,
  `P2P-CAPABILITY-TRUST-DATA-INSTRUCTION-SPEC.md`,
  `P2P-DECISION-TRACE-SPEC.md`.
- Finding: existing router, Goal Contract, EvidenceClaim, Context pointers,
  permission/trust gates, Decision Trace, and one execution ledger are
  authoritative. A foreground controller may compose them but cannot create a
  second router, ledger, evidence store, or capability authority.
- Status: `PASS`.

### E0-P0-C11

- Sources: `.p2p/system/p2p_capabilities/task_state.py`,
  `scripts/p2p_task_state.py`, `tests/test_p2p_task_state.py`.
- Finding: C11 supplies durable task records, dependency validation,
  `next_safe_task`, preflight, checkpoints, resume classification, owner
  decisions, and `TaskStateStore` persistence. It does not start work or
  independently bind a direct action receipt to a verifier.
- Status: `PASS / controller gap confirmed`.

### E0-P0-GRAPH

- Command: `anvien analyze . --force --skip-git --exclude .tmp
  --exclude .p2p/install-backups --exclude .p2p/state --exclude __pycache__`
  and `anvien analyze .p2p/system --force --skip-git --exclude __pycache__`.
- Finding: the initial graph parsed 334 files / 33 code files / 12,707 nodes /
  14,434 relationships; the final refreshed graph parsed 343 files / 35 code
  files / 13,350 nodes / 15,185 relationships. The final system graph parsed
  46 files / 38 code files / 6,613 nodes / 8,687 relationships. The task-state,
  live-execution, context, evidence, decision-trace, trust, and foreground
  controller surfaces are identifiable.
- Status: `PASS / graph evidence bounded`.

### E0-P0-IMPACT

- Commands: Anvien `file-detail` and upstream `impact` for the C11 task-state
  boundary and packaging/doctor functions.
- Findings: `scripts/package_release.py` functions had LOW risk with one direct
  impact each; `scripts/doctor.py:_foundation_required_paths` had CRITICAL risk,
  two direct impacts, and eight affected processes. The new controller is
  additive; package/doctor edits must remain minimal.
- Status: `PASS / blast radius recorded`.

### E0-P0-ARTIFACTS

- Sources: `VERSION`, `.p2p/state/`, `reports/`, prior package metadata.
- Finding: official `8.4.7-C-codex.15` SHA-256 is
  `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`;
  C11 candidate is `p2p-c11-candidate-8.4.7-C-codex.15-r2.zip` with SHA-256
  `684018d1a563e35e32eed2e06bbfee3e9625d9caef95771bf04a848fa3868926`.
  Both are preserve-only. C10 candidate `.20` is also preserve-only.
- Status: `PASS / protected artifacts recorded`.

### E0-P0-LIMITS

- Findings: this is an unpacked source workspace with no `.git`; Anvien required
  `--skip-git`. The workflow helper `plan` command timed out twice while
  scanning the large tree. No network, dependency install, hook, proxy, or
  external agent delegation was used.
- Status: `PASS / limitation recorded`.

## E1: Controller kernel evidence targets

- `E1-P1A-INTENT`: serialized intent contains task/goal/plan/project binding,
  direct strategy, finite budget, scope, required refs, and no identity fields.
- `E1-P1A-SCOPE`: direct runtime rejects path escape, non-scope paths,
  protected paths, network/child APIs, and writes outside explicit mutation
  scope.
- `E1-P1A-TEST`: focused tests cover intent schema, budget, scope, action
  count, and immutable receipt/checkpoint persistence.
- `E1-P1B-SELECT`: one ready task is selected; active/blocked/dependency/owner
  conflicts stop before action.
- `E1-P1B-PREFLIGHT`: permission, capability, context, evidence, and control-
  plane health map to explicit fail-closed results.
- `E1-P1B-VERIFY`: action output is not evidence; an independent current
  verifier and C10 completion contract are required for DONE.
- `E1-P1B-TEST`: focused tests cover success, denied gates, transient bounded
  retry, permanent failure, failed verification, and no parallelism.
- `E1-P1C-INTERRUPT`: checkpoint after action/before verification preserves
  non-DONE state and identifies pending verification.
- `E1-P1C-RESUME`: fresh process rechecks current hashes/evidence and only runs
  a read-only verifier; no automatic start or process-survival claim.
- `E1-P1C-TEST`: interruption/resume tests cover safe, recheck, blocked, and
  unknown classifications.

## E2: CLI and package evidence targets

- `E2-P2A-CLI`: subprocess tests exercise `select`, `preflight`, `run`, and
  `resume` through the real CLI boundary.
- `E2-P2A-BEGINNER`: CLI output is understandable without package, runtime,
  MCP, permission, or setup jargon.
- `E2-P2A-TEST`: CLI negative paths return structured statuses and nonzero exit
  only where the existing CLI convention requires it.
- `E2-P2B-PACKAGE`: package inventory/copy includes the new module and script
  without altering version or prior candidates.
- `E2-P2B-DOCTOR`: foundation doctor verifies both runtime paths.
- `E2-P2B-TEST`: package and doctor regression tests pass.

## E3: Evaluation and preservation evidence targets

- `E3-P3A-BFE`: BFE1-BFE40 behavior matrix with trigger, observable state,
  receipt/evidence reference, and pass/fail result.
- `E3-P3A-STRUCTURAL`: X1-X26 static/behavioral boundary matrix; source scans
  are supplemented by tests that attempt forbidden behavior.
- `E3-P3B-BEGINNER`: E1-E10 beginner matrix with plain-language output and
  safe next-step guidance.
- `E3-P3B-PRESERVE`: C10/C11 regression, canonical 8/8, optional AESTHETICA,
  C09 blocked, C08 not rerun, and project/chat boundary checks.

## E4: Final gates and closure evidence targets

- `E4-P4A-REGRESSION`: full build and affected/full unit/regression output.
- `E4-P4A-GATES`: capability, governance, security, drift, doctor, and
  lifecycle output.
- `E4-P4B-CANDIDATE`: new immutable candidate label, embedded version, path,
  and preservation comparison.
- `E4-P4B-HASH`: candidate SHA-256 and exact technical-report SHA-256.
- `E4-P4C-SUPERVISOR`: independent Supervisor report with exact PASS/REJECT.
- `E4-P4C-CLEANUP`: repo-local temporary cleanup and preserved artifacts.
- `E4-P4D-CLOSURE`: final workflow terminal state, status files, and user
  report consistency.

## Evidence Ledger Updates

| ID | Status | Evidence location | Notes |
|---|---|---|---|
| E0-P0-SPEC | PASS | `docs/SPEC/` | Architecture and evidence authority mapped |
| E0-P0-C11 | PASS | `.p2p/system/p2p_capabilities/task_state.py` | Durable foundation is preserve-only input |
| E0-P0-GRAPH | PASS | `.anvien/graph.json`, command output | Refreshed with no-Git mode |
| E0-P0-IMPACT | PASS | Anvien output | Package LOW; doctor CRITICAL warning recorded |
| E0-P0-ARTIFACTS | PASS | `.p2p/state/`, reports | Prior artifacts are immutable targets |
| E0-P0-LIMITS | PASS | workflow/Anvien output | Helper timeout and no-Git limits recorded |
| E1-P1A-INTENT | PASS | `foreground_execution.py`, focused tests | Intent/budget/receipt fields are identity-free and finite |
| E1-P1A-SCOPE | PASS | `ExecutionRuntime`, focused tests | Scope, protected paths, mutation, and no-network boundary pass |
| E1-P1A-TEST | PASS | `tests.test_p2p_foreground_execution` | 20/20 focused tests pass |
| E1-P1B-SELECT | PASS | controller select/execute tests | One direct task; competing ACTIVE state is refused |
| E1-P1B-PREFLIGHT | PASS | preflight/owner/capability tests | Denied capability and missing owner decision durably stop before action with `WAITING_OWNER` |
| E1-P1B-VERIFY | PASS | success/no-output-proof tests | Independent current evidence is required for DONE |
| E1-P1B-TEST | PASS | focused suite | Finite retry, failure, verification, and direct path pass |
| E1-P1C-INTERRUPT | PASS | interruption test/artifacts | ACTIVE plus NEEDS_RECHECK checkpoint persists |
| E1-P1C-RESUME | PASS | fresh controller resume test | Read-only verifier completes without rerunning action |
| E1-P1C-TEST | PASS | focused suite | Resume gate and interruption tests pass |
| E2-P2A-CLI | PASS | CLI subprocess test and portable smoke | `select/preflight/run/resume` boundary is thin |
| E2-P2A-BEGINNER | PASS | CLI output assertions | Output contains direct/blocked state, no setup request |
| E2-P2A-TEST | PASS | CLI subprocess test | Built-in write/hash actions return structured JSON |
| E2-P2B-PACKAGE | PASS | package build/verify | Module and CLI are included in candidate package |
| E2-P2B-DOCTOR | PASS | package doctor | Foundation payload and canonical contract pass |
| E2-P2B-TEST | PASS | package contract test | Source package inventory validates new paths |

| E3-P3A-BFE | PASS | C12 matrix report + focused suite | BFE1-BFE40: 40/40 PASS |
| E3-P3A-STRUCTURAL | PASS | C12 matrix report + AST/negative tests | X1-X26: 26/26 PASS |
| E3-P3B-BEGINNER | PASS | C12 matrix report + CLI/controller tests | E1-E10: 10/10 PASS |
| E3-P3B-PRESERVE | PASS | full regression, capability doctor, project status | C10/C11 preserved; canonical 8/8; AESTHETICA optional; C09 remains BLOCKED; C08 not rerun |
| E4-P4A-REGRESSION | PASS | full unittest + project eval | Focused 20/20 in 1.153s; C11/C06 36/36 in 1.077s; full 159/159 in 94.719s; 5 paired eval cases, 2 trials each, delta 0.0, no regressions |
| E4-P4A-GATES | PASS | development/package doctor, governance drift, secret scan, capability doctor, decision-trace doctor | All required technical gates PASS after owner-gate correction and runtime-lock refresh |
| E4-P4B-CANDIDATE | PASS | `.tmp/p2p-c12/candidates/p2p-c12-candidate-8.4.7-C-codex.15-r7.zip` | New unpromoted r7 candidate built after runtime-lock refresh; package version remains 8.4.7-C-codex.15; r6/r5 preserved and superseded |
| E4-P4B-HASH | PASS | candidate hash + source reports | Candidate SHA-256 `939f918875f57906112fcb50f7e145ef15187cbe29ae50c4cc15dd888709c522`; controller source SHA-256 `e76bff1208fb718587726b6df8bc2ba8d88285be21444be704b2ac81a66c6ab6`; Supervisor report SHA-256 `1d8004ecda07e3647fbb74cbdae22b8051541e3943822fc31e296f33787fe96a` |
| E4-P4C-SUPERVISOR | PASS | `reports/supervisor/rp_supervisor_260814_165500_by_gpt-5-codex_p2p-c12-bounded-foreground-execution-r7.md` | Independent r7 technical verdict PASS; exact report SHA-256 `1d8004ecda07e3647fbb74cbdae22b8051541e3943822fc31e296f33787fe96a`; owner-state gap closed; workflow limitation noted |
| E4-P4C-CLEANUP | PASS | repo-local `.tmp/p2p-c12/` | r7 candidate and clean extraction evidence retained; r6/r5 preserved; no protected artifact changed |
| E4-P4D-CLOSURE | BLOCKED | workflow run `run-20260814-160647-p2p-c12-implement-an` + project status | Helper linter rejected combined independent objectives; C09 projection restored to BLOCKED and no C08/C09 rerun |

All required technical evidence is complete. The only non-PASS terminal item is
the workflow-helper closure criterion described in `E4-P4D-CLOSURE`; it is an
orchestration limitation, not a controller runtime failure.
