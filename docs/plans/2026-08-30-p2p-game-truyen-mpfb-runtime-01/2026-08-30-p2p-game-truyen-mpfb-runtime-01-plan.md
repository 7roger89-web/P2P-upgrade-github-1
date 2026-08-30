# P2P Game Truyen MPFB Runtime 01 Plan

## Metadata

- Date: `2026-08-30`
- Status: `P2 in progress; implementation-ready, exact-subject Supervisor pending`
- Plan: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-plan.md`
- Evidence: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-evidence.md`
- Benchmark: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-benchmark.md`
- Actual status: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-actual-status.md`

## Goal

Close only the two MPFB-SMOKE-01 implementation blockers in the exact
canonical adapter checkout: add a dedicated bounded Blender-side MPFB2 2.0.17
entrypoint using APIs verified from the pinned source, and enforce Windows
outbound network denial before Blender spawn with fail-closed setup and cleanup.
Leave Blender/MPFB execution, Golden Character creation, Game Truyen changes,
promotion, and visual proof downstream.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes; measurements belong in the benchmark ledger.
- Preserve `shell=False`, minimal environment, no secret inheritance, per-job
  workspace, output containment, reparse rejection, timeout, tree termination,
  `CORE_CC0_ONLY`, and third-party denial.
- Preserve `ADAPTER_PASS != EXECUTION_PASS != VISUAL_PASS`.
- Do not install or run Blender/MPFB2, create a Golden Character, modify Game
  Truyen, promote, publish, or enable a broader network path.
- Use only the exact MPFB2 source APIs inspected at
  `80919fa4682335c41847f761a4d79dcad4124732` / tree
  `189a1d6694515ecfbdc40067218c5024389b4e43`.
- Run Anvien detect-changes before every implementation-slice commit.
- Stop at implementation readiness; actual Blender execution remains NOT_RUN.

## Problem

The canonical parent builds an allowlisted Blender command but points it at a
module with no executable Blender body. It also records `--network deny` and
`NETWORK_POLICY=DENY` without an OS/process enforcement boundary. The smoke
receipt therefore reports `CANONICAL_ENTRYPOINT_NOT_EXECUTABLE` and
`NETWORK_DENY_NOT_ENFORCED`; Blender absence is downstream and out of scope.

## Scope

- `.p2p/system/p2p_capabilities/mpfb_adapter.py` parent/orchestrator changes.
- One dedicated Blender-side entrypoint with strict argument parsing.
- One Windows Firewall program-rule isolation helper bound to the exact
  Blender executable path, with receipt state and deterministic cleanup.
- Focused mock tests, compile/parse checks, diff check, candidate freeze, and
  fresh Supervisor review.
- Plan/evidence/benchmark/actual-status artifacts for this workstream.

## Non-Goals

- No Blender or MPFB2 installation, process spawn, model execution, GLB
  creation, visual QA, or Golden Character.
- No Game Truyen access or modification.
- No network isolation activation against the host during validation.
- No generic Python runner, `--python-expr`, arbitrary caller script, proxy-only
  control, release, promotion, push, or broad unrelated regression suite.

## Requirements

- Parent constructs exact argv for the dedicated entrypoint and rejects
  arbitrary script/expression inputs.
- Blender-side entrypoint accepts only `--recipe`, `--output-root`,
  `--mpfb-root`, `--mpfb-manifest`, `--character-id`, pinned version/SHA,
  `--asset-policy`, and `--network deny`; unknown or duplicate arguments fail.
- Entry point revalidates recipe/job binding, exact six-key provisioning
  manifest and root hash, `CORE_CC0_ONLY`, core-only asset IDs, and output
  directory state before using MPFB.
- The verified MPFB APIs are `HumanService.create_human`,
  `HumanService.set_character_skin`, and `HumanService.add_builtin_rig` with
  the actual standard GameEngine-compatible rig file selected by the recipe;
  no invented API is allowed. Blender's native glTF operator is the export
  boundary.
- Exactly `<character_id>.glb` and
  `<character_id>.asset-provenance.json` may remain in the output root.
- Windows isolation uses an exact-path outbound Windows Defender Firewall
  program rule, created and verified before `Popen`, with Administrator as the
  required privilege. Setup or verification failure prevents spawn.
- Cleanup runs on success, command failure, timeout, and setup failure after a
  rule was created; cleanup failure is surfaced as a security failure.
- Receipt data binds mechanism, rule identity, executable path, setup result,
  cleanup result, and enforcement result without secrets.

## Acceptance Criteria

- Focused tests prove exact argv, strict entrypoint rejection, recipe/pin
  binding, core-only policy, two-output allowlist, provenance binding, setup
  ordering, fail-closed isolation, no-spawn gates, and cleanup for success,
  failure, and timeout.
- Source compiles/parses and `git diff --check` passes.
- No Blender/MPFB process is spawned; `BLENDER_INSTALLED=NO`,
  `MPFB_EXECUTED=NO`, and `GLB_CREATED=NO` remain true.
- One candidate is frozen and Supervisor reviews the exact candidate SHA/tree.
- Supervisor verdict distinguishes `EXECUTABLE_RUNTIME_IMPLEMENTATION_READY`
  from `ACTUAL_BLENDER_EXECUTION_PROVEN=NO`.
- No promotion occurs; terminal state is
  `P2P_GAME_TRUYEN_MPFB_RUNTIME_01_READY_FOR_OWNER_GATE` only when every
  implementation gate passes.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish exact checkout, smoke blockers, source/API facts, and the protected touch map.
  - Work Steps: verify the target checkout is at `31647b2f...` / `c2154652...`; read the smoke receipt and current adapter; verify the pinned MPFB checkout; refresh Anvien; record hidden-file graph limits and preserve-only surfaces.
  - Implementation Gate: actual-status has a completed matrix, evidence IDs, touch modes, and a P0 decision before source edits.
  - Acceptance: P0 classifies the parent as partial, dedicated entrypoint as missing, network enforcement as wrong, exact MPFB source as verified, and Game Truyen as do-not-touch.

### P1: Runtime implementation

- Phase Goal: implement the missing Blender body and real Windows network boundary while keeping the parent bounded.
- Phase Boundary:
  - In scope: dedicated entrypoint, Windows isolation helper, parent integration, focused tests.
  - Out of scope: Blender/MPFB execution, model/asset provisioning, Game Truyen, promotion, and visual proof.
  - Dependencies: P0 complete; exact MPFB source API inspection; Windows Firewall Administrator requirement documented.
- Phase Implementation Rule: implement `P1-A`, `P1-B`, and `P1-C` as one coherent bounded slice because the child entrypoint, isolation lifecycle, and parent spawn gate are inseparable; verify and record the slice before the candidate commit.
- Ordered Slice List:
  - P1-A: Add the strict dedicated Blender-side MPFB entrypoint.
  - P1-B: Add Windows exact-path network isolation with fail-closed lifecycle.
  - P1-C: Bind the parent orchestrator, receipts, and focused mocks.

- [x] P1-A: Add the strict dedicated Blender-side MPFB entrypoint.
  - Goal: make the `--python` target an actual bounded Blender execution body without running it here.
  - Scope Boundary:
    - Editable: new `.p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py`, related parent constants only as needed.
    - Inspect-only: exact MPFB2 checkout and its source APIs.
    - Preserve-only: recipe/provenance schemas, Game Truyen, existing adapter security checks.
    - Out of scope: MPFB source edits, installation, execution, and any fallback generator.
  - Non-Goals: no generic runner and no caller-selected script path.
  - Pre-flight Questions:
    - Data source: validated `character.recipe.json` and pinned provisioning manifest.
    - Display permission: N/A; headless background execution only.
    - DB read flow: N/A; filesystem recipe read is the real input flow.
    - DB write flow: N/A; two declared files are the only output flow.
    - Render location: Blender background scene, then explicit GLB output root.
    - UI behavior flow: N/A; no UI is opened or validated.
    - Docker runtime: N/A; no container/runtime target in this workstream.
    - Playwright target: N/A; non-UI change and Blender is forbidden to run.
    - Behavior test: mocked Blender module/API boundary and strict parser tests.
    - Cleanup/quarantine: temporary test workspaces live under the checkout and are removed by test fixtures.
    - External side effects: none; no upstream network or host firewall activation.
    - N/A notes: actual MPFB execution remains downstream NOT_RUN.
  - Work Steps:
    1. Translate the verified `HumanService.create_human`, `set_character_skin`, and `add_builtin_rig` calls into the dedicated script, mapping `GAMEENGINE` to the actual supported built-in rig name and keeping material/asset selection core-only.
       - UI flow check: N/A; assert headless-only script behavior.
       - DB/data flow check: assert recipe -> normalized settings -> MPFB calls -> declared output paths.
       - Render location check: assert all files are under the bounded output root.
       - Evidence target: `E1-P1A-SRC1`, `E1-P1A-TEST1`.
    2. Add strict argv parsing, pin/manifest revalidation, pre/post output snapshots, GLB hash/provenance creation, and deterministic error codes without executing the script.
       - UI flow check: N/A.
       - DB/data flow check: assert recipe and provenance exact binding.
       - Render location check: assert only GLB and sidecar are permitted.
       - Evidence target: `E1-P1A-TEST2`, `E1-P1A-TEST3`.
  - Implementation Gate:
    - Before editing, exact MPFB source APIs and parent file impact evidence are recorded; no unsupported MPFB call is introduced.
  - Acceptance:
    - Source: dedicated entrypoint exists and is bound to the parent constant.
    - Runtime/UI: no runtime execution; parser and mocked API contract pass.
    - DB/data: N/A; filesystem recipe/provenance binding passes.
    - Behavior test: strict args, pin, core policy, two outputs, and provenance tests pass.
    - Cleanup/quarantine: test roots are temporary and cleaned.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-TEST3`.
    - Actual-status rows refreshed: dedicated entrypoint missing -> partial/implemented.
  - Evidence Targets: source API citations, parser tests, output/provenance tests, compile result.
  - Actual-status Update: record the entrypoint as implemented-but-unexecuted until Blender proof exists.
  - Commit Boundary: completed in the coherent P1 candidate slice after focused tests and compile pass.

- [x] P1-B: Add Windows exact-path network isolation with fail-closed lifecycle.
  - Goal: establish and release an enforceable outbound boundary before Blender spawn.
  - Scope Boundary:
    - Editable: new `.p2p/system/p2p_capabilities/windows_network_isolation.py` and its focused tests.
    - Inspect-only: Windows Firewall command semantics; no live rule is created in validation.
    - Preserve-only: `NETWORK_POLICY=DENY`, process-tree termination, Game Truyen.
    - Out of scope: proxy variables, OS-wide firewall policy changes, or real Blender.
  - Non-Goals: do not claim network denial was live-proven on this host.
  - Pre-flight Questions:
    - Data source: canonical Blender executable path from the execution plan.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A; receipt is in-memory parent evidence.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: mocked `netsh` runner and injected lifecycle hooks.
    - Cleanup/quarantine: no live firewall rule; mock identity only.
    - External side effects: none during validation.
    - N/A notes: Administrator is required for downstream real setup.
  - Work Steps:
    1. Implement exact-path rule identity, pre-existing-rule collision rejection, add/show verification, and Administrator/failure mapping using `shell=False`.
       - UI flow check: N/A.
       - DB/data flow check: assert executable path and enforcement identity are bound in the receipt.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-TEST1`, `E1-P1B-TEST2`.
    2. Implement context-managed cleanup and parent integration hooks so cleanup runs after success, failure, and timeout, and any unavailable enforcement blocks `Popen`.
       - UI flow check: N/A.
       - DB/data flow check: assert setup/cleanup/result transitions.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-TEST3`, `E1-P1B-TEST4`.
  - Implementation Gate:
    - The mechanism is exact-path Windows Firewall program blocking, not a flag or proxy; privilege requirement and fail-closed behavior are explicit.
  - Acceptance:
    - Source: helper has deterministic setup, verification, release, and receipt states.
    - Runtime/UI: no live rule creation; mocks prove ordering.
    - DB/data: N/A.
    - Behavior test: unavailable setup means no process spawn; all teardown paths are covered.
    - Cleanup/quarantine: mock rules are never installed; live activation is forbidden.
    - Evidence IDs: `E1-P1B-TEST1..E1-P1B-TEST4`.
    - Actual-status rows refreshed: network enforcement wrong -> implemented-but-live-proof pending.
  - Evidence Targets: isolation helper tests, privilege requirement, fail-closed and teardown traces.
  - Actual-status Update: classify as implementation-ready, not actual enforcement-proven.
  - Commit Boundary: completed in the coherent P1 candidate slice after focused tests and compile pass.

- [x] P1-C: Bind the parent orchestrator, receipts, and focused mocks.
  - Goal: make the parent spawn only after all gates and isolation setup pass, while preserving timeout and output validation.
  - Scope Boundary:
    - Editable: `mpfb_adapter.py` and focused test file.
    - Inspect-only: Game Truyen and upstream MPFB source.
    - Preserve-only: schemas, catalog, existing smoke artifacts, and user-owned untracked report.
    - Out of scope: broad regression, Blender execution, promotion.
  - Non-Goals: no actual subprocess spawn; mock `Popen` is the highest allowed boundary.
  - Pre-flight Questions:
    - Data source: `MpfbExecutionPlan` plus injected isolation factory.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: output root allowlist.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: exact argv, ordering, failure gates, timeout cleanup, and receipt tests.
    - Cleanup/quarantine: all test fixtures clean their per-job roots.
    - External side effects: none.
    - N/A notes: actual process remains prohibited.
  - Work Steps:
    1. Replace the parent `--python` target with the dedicated entrypoint, add output-root preflight, and expose isolated execution receipt data.
       - UI flow check: N/A.
       - DB/data flow check: assert plan fields and receipt identity.
       - Render location check: assert output root starts empty and ends with the exact two files.
       - Evidence target: `E1-P1C-TEST1`, `E1-P1C-TEST2`.
    2. Wire isolation context around `Popen`, preserving `shell=False`, minimal env, process-group flags, timeout tree kill, and no-spawn failures.
       - UI flow check: N/A.
       - DB/data flow check: assert cleanup for success/command failure/timeout.
       - Render location check: assert no validation occurs before isolation result.
       - Evidence target: `E1-P1C-TEST3`, `E1-P1C-TEST4`.
  - Implementation Gate:
    - P1-A and P1-B committed and their actual-status rows refreshed; parent impact evidence is recorded.
  - Acceptance:
    - Source: parent binds dedicated entrypoint and isolation lifecycle.
    - Runtime/UI: mock-only; no Blender process.
    - DB/data: N/A.
    - Behavior test: all requested focused cases pass.
    - Cleanup/quarantine: no live host state remains.
    - Evidence IDs: `E1-P1C-TEST1..E1-P1C-TEST4`.
    - Actual-status rows refreshed: parent partial -> implementation-ready.
  - Evidence Targets: focused test output, compile, diff check, no-spawn assertions.
  - Actual-status Update: mark implementation readiness separately from execution proof.
  - Commit Boundary: completed in the coherent P1 candidate slice when acceptance passed.

### P2: Verification and freeze

- Phase Goal: run only the focused validation ceiling, freeze one exact candidate, and obtain independent Supervisor review.
- Phase Boundary:
  - In scope: compile/parse, focused tests, diff check, detect-changes, candidate SHA/tree, Supervisor report.
  - Out of scope: Blender/MPFB execution, GLB, visual, Game Truyen, promotion, and broad unrelated suites.
  - Dependencies: P1 complete and worktree subject known.
- Phase Implementation Rule: validation is one bounded slice; no optional hardening after PASS.

- [ ] P2-A: Focused validation, candidate freeze, and Supervisor review.
  - Goal: prove the code contract and freeze an owner-gate-ready candidate without overstating runtime proof.
  - Scope Boundary:
    - Editable: plan/evidence/benchmark/actual-status and Supervisor report only.
    - Inspect-only: implementation diff and exact MPFB source snapshot.
    - Preserve-only: all external repositories and existing untracked user report.
    - Out of scope: any code changes after the validation ceiling unless Supervisor finds a scoped defect.
  - Non-Goals: no promotion or actual runtime certification.
  - Pre-flight Questions:
    - Data source: current candidate commit/tree and focused test artifacts.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: focused adapter/isolation suite only.
    - Cleanup/quarantine: verify no test workspace or live firewall rule remains.
    - External side effects: none.
    - N/A notes: Supervisor must state actual execution NOT_RUN.
  - Work Steps:
    1. Run focused tests, compile/parse, `git diff --check`, and Anvien detect-changes; record what each proves and refresh actual-status.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E2-P2A-TEST1..E2-P2A-CHANGE1`.
    2. Freeze exact candidate SHA/tree and run fresh Supervisor review against that exact subject.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E2-P2A-FREEZE1`, `E2-P2A-SUPERVISOR1`.
  - Implementation Gate:
    - All P1 slices pass; no Blender/MPFB process was started; candidate subject is unchanged during review.
  - Acceptance:
    - Source: focused implementation is reviewed at exact SHA/tree.
    - Runtime/UI: Supervisor says executable implementation ready only; actual Blender execution remains unproven.
    - DB/data: N/A.
    - Behavior test: focused suite and compile/diff checks pass.
    - Cleanup/quarantine: workspace and mock isolation state clean.
    - Evidence IDs: `E2-P2A-TEST1..E2-P2A-SUPERVISOR1`.
    - Actual-status rows refreshed: candidate frozen and owner gate ready.
  - Evidence Targets: final validation output, change detection, candidate identity, Supervisor verdict.
  - Actual-status Update: set implementation readiness from Supervisor, never set actual execution proven.
  - Commit Boundary: commit final evidence/status artifacts only after exact candidate review; do not promote.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the exact candidate and evidence.
  - Work Steps: review the full plan, evidence, benchmark, status, changed files, and validation; if failed, fix only the reported scoped defect and rerun.
  - Implementation Gate: P1 and P2-A are complete or explicitly blocked.
  - Acceptance: Supervisor passes the bounded implementation-readiness claim or records a blocker; no closure overclaim is made.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only accepted plan artifacts.
  - Work Steps: inspect plan-created artifacts, remove obsolete temporary/debug outputs, preserve the pre-existing user report, and rerun Supervisor if cleanup changes the subject.
  - Implementation Gate: only artifacts created by this plan are candidates for cleanup.
  - Acceptance: no dead plan-created artifact remains and preservation is recorded.
- [ ] Pn-C: Close the plan.
  - Goal: record final evidence, candidate identity, clean worktree state, and terminal verdict.
  - Work Steps: run final bounded checks, detect changes, record candidate SHA/tree and Supervisor exact-subject result, commit authorized work, and stop.
  - Implementation Gate: Pn-A and Pn-B pass or record a real blocker.
  - Acceptance: terminal report says READY_FOR_OWNER_GATE or BLOCKED, with `ACTUAL_EXECUTION_PROVEN=NO`.

## Risk Notes

- Windows Firewall program rules require Administrator and depend on Windows
  Defender Firewall being enabled; inability to establish or verify the exact
  rule is a hard no-spawn blocker.
- A program rule is bound to the executable path, not a single PID; the helper
  must reject collisions and record this scope honestly.
- MPFB source API names are high-risk integration facts; only the inspected
  2.0.17 source is authoritative for the entrypoint.
- The candidate can be implementation-ready while Blender execution, GLB
  creation, and visual quality remain unproven downstream.
