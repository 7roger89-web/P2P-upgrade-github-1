# P2P-CT01 Durable Control Tower Session Handoff Evidence Ledger

## Metadata

- Date: 2026-08-26
- Plan: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-plan.md
- Evidence: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-evidence.md
- Benchmark: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-benchmark.md
- Actual status: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-actual-status.md

## Evidence Rules

Record exact commands, paths, results, and boundaries. A packet, local test, or generated prompt is evidence of the candidate only; it is not canonical truth, owner approval, host certification, promotion, or release evidence. Use one stable ID per fact.

## E0 - P0 Evidence

Matching plan item(s): P0-A

- E0-P0A-SRC1: requested root had no valid HEAD/config; git failed there; root was not repaired.
- E0-P0A-SRC2: fresh canonical origin fetch matched remote, expected HEAD 28a3ecd9c04d36511269e44c384bff6e11677b93, expected tree cae63e055edd164fbd969f6dbae0d992a4d0efed, origin/main, and zero ahead/behind.
- E0-P0A-SRC3: isolated branch codex/p2p-ct01-control-tower starts at the matched commit.
- E0-P0A-GRAPH1: anvien analyze --force completed with stale=false, 951 scanned files, 170 parsed code files, 0 failed parses, 39,653 nodes, and 45,846 relationships.
- E0-P0A-GRAPH2: file-detail/impact ran for scripts/p2p_task_state.py, scripts/p2p_foreground_execution.py, and scripts/p2p_workflow.py; high-risk workflow/task surfaces remain inspect-only.
- E0-P0A-GRAPH3: hidden .p2p files were unavailable to Anvien file-detail; this is a recorded graph limitation, not fabricated evidence.
- E0-P0A-ARCH1: existing host executor, task state, live execution, evidence chain, workflow ledger, specs, charter, and capability ledger were directly inspected.
- E0-P0A-ARCH2: no CT01 packet, recursive prompt, exact beginner action, or dedicated operator guide was found.
- E0-P0A-WF1: scripts/p2p_workflow.py goal/bootstrap/plan preflight created isolated Goal Contract/project/eval/trusted-evidence/execution-ledger state.
- E0-P0A-ENV1: worktree broad modifications are line-ending-only noise under core.autocrlf=true and remain unstaged.

## E1 - P1 Evidence

Matching plan item(s): P1-A and P1-B

P1-A completed before test implementation:

- E1-P1A-SRC1: added .p2p/system/p2p_capabilities/control_tower_handoff.py as a stdlib-only composition seam. python -m py_compile exited 0 and direct import/smoke exited 0.
- E1-P1A-SRC2: smoke created an explicit CODEX binding, serialized and deserialized a READY packet, built the recursive prompt, and returned READY with mapped lifecycle READY.
- E1-P1A-BOUNDARY1: smoke result showed host=CODEX and promoted=False; source has no file opening, subprocess, network, router, approval, or canonical-write path. Packet serialization includes PACKET_IS_CANONICAL_TRUTH=NO.
- E1-P1A-GRAPH1: fresh anvien analyze --force after the source addition completed with stale=false, scanned=955, parsed_code=170, failed=0, nodes=39,702, relationships=45,895. detect-changes reported no tracked changes because the new source was still untracked at that point; this is recorded as a limitation, not as a claim that the source was absent.

P1-B pending:

- E1-P1B-TEST1 through E1-P1B-TEST8: required A-H cases.
- E1-P1B-TEST9 through E1-P1B-TEST11: invalid binding, no-inheritance, and round-trip/discovery cases.
- E1-P1B-TEST1 through E1-P1B-TEST8: required A-H cases.
- E1-P1B-TEST9 through E1-P1B-TEST11: invalid binding, no-inheritance, and round-trip/discovery cases.

## E2 - P2 Evidence

Matching plan item(s): P2-A and P2-B

Append:

- E2-P2A-DOC1: operator guide, charter cross-reference, exact beginner workflow, and discovery paths.
- E2-P2A-LEDGER1: capability ledger schema/dependency/uniqueness validation.
- E2-P2A-ROADMAP1: derived roadmap count/family projection validation.
- E2-P2B-TEST1: focused CT01 test command and exit code.
- E2-P2B-TEST2: relevant existing P2P test command and exit code.
- E2-P2B-TEST3: development-source doctor/validation and exit code.
- E2-P2B-TEST4: compile/import/diff-check command and exit code.
- E2-P2B-DETECT1: Anvien detect-changes before final implementation commit.
- E2-P2B-COMMIT1: final candidate commit and exact HEAD/tree.
- E2-P2B-SUP1: supervisor report and verdict.

## Closure Evidence

Pending. Closure must state final candidate SHA/tree, report paths, supervisor verdict, protected surfaces not changed, and explicit no-promotion/no-remote-write result.
