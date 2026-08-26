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

P1-B completed:

- E1-P1B-TEST1: A READY packet is accepted as READY and remains non-promoted.
- E1-P1B-TEST2: a BLOCKED MANUS packet updates only the MANUS lane and cannot become success.
- E1-P1B-TEST3: explicit CODEX binding wins over a narrative MANUS claim.
- E1-P1B-TEST4: stale base SHA/tree produces RECONCILIATION_REQUIRED without canonical overwrite.
- E1-P1B-TEST5: WAITING_OWNER_GATE records the owner gate without protected action.
- E1-P1B-TEST6: FAILED is returned and recorded with mapped BLOCKED lifecycle and no false success.
- E1-P1B-TEST7: recursive prompt contains the full return packet field list, NO canonical-truth marker, and exact user action.
- E1-P1B-TEST8: only the authoritative GEMINI lane changes when narrative prose names CLAUDE.
- E1-P1B-TEST9: missing/invalid binding and implicit inherited state fail closed.
- E1-P1B-TEST10: WAITING_OWNER_GATE without an owner gate is rejected.
- E1-P1B-TEST11: UNKNOWN canonical base is not treated as CURRENT.
- E1-P1B-TEST12: packet round-trip, ledger event, and state projection are JSON safe.
- E1-P1B-TEST13: future provider-neutral labels normalize without provider-specific routing logic.
- E1-P1B-TEST14: temporary test worktree paths stay under the repository .tmp boundary.
- E1-P1B-TEST15: the structured return event is accepted by the existing scripts/p2p_workflow.py append_event writer and is durable JSONL with the canonical-truth marker NO.
- E1-P1B-FIX1: first test run exposed only a missing repo-local .tmp fixture directory (13 passed, 1 fixture failure); the fixture was corrected and the final focused run passed 15 cases.
- E1-P1B-TEST1 through E1-P1B-TEST8: required A-H cases.
- E1-P1B-TEST9 through E1-P1B-TEST11: invalid binding, no-inheritance, and round-trip/discovery cases.

## E2 - P2 Evidence

Matching plan item(s): P2-A and P2-B

P2-A completed:

- E2-P2A-DOC1: added docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md with the exact beginner workflow, exact USER_ACTION, packet field contract, reconciliation rules, architecture binding, discovery paths, and explicit UNPROMOTED boundary; added the charter 3A cross-reference.
- E2-P2A-LEDGER1: custom JSON/schema/dependency check passed for CONTROL_TOWER_SESSION_HANDOFF; ledger count is 176, MULTI_AI_INTEROPERABILITY count is 32, the new record is schema-valid, unique, registered-family, and all six dependencies resolve.
- E2-P2A-ROADMAP1: current-roadmap.md projection records 176 total capabilities and 32 Multi-AI records and names CONTROL_TOWER_SESSION_HANDOFF_FOUNDATION_READY as local technical proof only.
- E2-P2A-BASELINE1: scripts/validate_p2p_development_framework.py on the CT01 worktree remains 52/59 with the same seven failures observed on the fresh canonical clone: nine historical records missing origin_type, legacy family/dependency/freshness entries, charter competitor-pattern scan, and governance pr_lineage. No new CT01-specific failure was added; those existing failures remain out of scope and are a P2-B validation blocker.

P2-B validation:

- E2-P2B-TEST1: python -m pytest -q tests/test_p2p_control_tower_session_handoff.py returned 15 passed in 0.51s, exit 0.
- E2-P2B-TEST2: fresh canonical related suite returned 68 passed and 1 inherited fixture failure; CT01 did not modify any of those existing sources.
- E2-P2B-TEST3: compileall exit 0; project eval validate exit 0; development doctor passed on the clean canonical clone and failed on CT01 only for expected candidate governance drift.
- E2-P2B-TEST4: framework validator returned 52/59 on both clean canonical and CT01; the same seven inherited failures were observed. Portable doctor role mismatch is expected for a development-source tree.
- E2-P2B-CODER1: coder report written at reports/coder/rp_coder_260826_150226_by_gpt-5-codex_p2p-ct01-control-tower-session-handoff.md; technical implementation PASS, full session BLOCKED.
- E2-P2B-DETECT1: final staged anvien detect-changes --repo isolated-worktree --scope all --json returned affected_count=0, affected_files=8, changed_count=53, changed_files=9, affected_processes=0, and risk_level=low. The nine changed paths are the CT01 module/test, operator guide, capability ledger, three planner artifacts, coder report, and supervisor report; no process was affected.
- E2-P2B-SUP1: reports/supervisor/rp_supervisor_260826_150424_by_gpt-5-codex_p2p-ct01-control-tower-session-handoff.md is the fresh exact-scope review. Verdict is REJECT for full-plan closure, with CT01 technical implementation PASS and the full session terminal state BLOCKED.

## Closure Evidence

- CT01 technical implementation is PASS; the full session is BLOCKED because the clean canonical baseline and candidate retain inherited framework/doctor gates and no live-host certification exists.
- E2-P2B-DETECT1 records the final scoped change graph: nine intended changed files, zero affected processes, and low aggregate Anvien risk.
- E2-P2B-SUP1 records the Supervisor REJECT and preserves the no-repair boundary.
- E2-P2B-COMMIT1: closure commit 76a9a9449927838eb3965448aefe732ed39e55ee with tree 9b876b4dba86bc1bb21358acb881843fb926f0a6; it is four commits ahead of the bound base, retains the promoted anchor as an ancestor, and has no remote write.
- Protected root, canonical main, remote, runtime lock, release surfaces, promotion, deployment, approval, and live host were not touched.
- CANONICAL_PROMOTED: NO; no remote write occurred.
