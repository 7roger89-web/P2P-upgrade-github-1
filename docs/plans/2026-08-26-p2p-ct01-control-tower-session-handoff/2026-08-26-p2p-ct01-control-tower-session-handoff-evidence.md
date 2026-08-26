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

## E3 - Owner Scope Addendum Evidence — Attachment-Aware Handoff

Matching plan item(s): A1-P1 through A1-P4

- E3-P2A-SCOPE1: the Owner-approved CT01 clarification was kept inside the existing bounded scope. No Large Goal, promotion, deployment, live action, remote write, second store, router, worker, quorum, or certification system was opened.
- E3-P2A-IMPL1: `.p2p/system/p2p_capabilities/control_tower_handoff.py` adds `CONTROL_TOWER_ATTACHMENT_MANIFEST`, `UPLOAD_REQUIRED`, validated attachment entries, packet round-trip, execution-ledger event projection, and recursive prompt instructions. Implementation/test checkpoint is `13ccb8910cf2c845acc450b9e354f9d32c5f90a1`, tree `d1182567f44b05346361eeb9eeb97ad1cbbc2a00`.
- E3-P2A-TEST1: `python -m pytest -q tests/test_p2p_control_tower_session_handoff.py` returned `22 passed in 0.29s`, exit 0. The seven added cases cover `UPLOAD_REQUIRED=NO`, `UPLOAD_REQUIRED=YES`, required/optional/do-not-upload classification, local path versus contents availability, attachment versus canonical truth, recursive prompt preservation, and ambiguous manifest rejection.
- E3-P2A-COMPILE1: `python -m py_compile .p2p/system/p2p_capabilities/control_tower_handoff.py` and `python -m compileall -q .p2p/system/p2p_capabilities scripts tests/test_p2p_control_tower_session_handoff.py` both exited 0.
- E3-P2A-EVAL1: `python scripts/p2p_eval.py validate --suite .p2p/evals/suite.json` returned `status=PASS`, exit 0.
- E3-P2A-LEDGER1: custom capability-ledger check returned `CAPABILITY_LEDGER_CHECK=PASS records=176 multi_ai=32 ct01_evidence=22+7`; the CT01 record points to the single REQUIRED handoff artifact and does not promote the capability.
- E3-P2A-DOC1: the durable operator guide and derived roadmap explicitly document the `YES/NO` contract, exact manifest fields, local-path/content distinction, evidence-only attachment semantics, and the preferred one-file artifact. The roadmap projection records 22 focused cases including seven attachment-aware cases.
- E3-P2A-ARTIFACT1: `.tmp/p2p-ct01-control-tower/p2p-ct01-codex-20260826-isolated-CONTROL-TOWER-HANDOFF.md` exists as the one minimum REQUIRED upload. It states `LOCAL_PATH_ALONE_PROVES_CONTENTS_AVAILABLE: NO`, `ATTACHMENT_IS_CANONICAL_TRUTH: NO`, and that attachment contents do not prove promotion, deployment, live certification, or Owner approval.
- E3-P2A-CODER1: `reports/coder/rp_coder_260826_153339_by_gpt-5-codex_p2p-ct01-attachment-aware-handoff.md` records technical addendum PASS, full-session BLOCKED, and the exact residual authority boundary.
- E3-P2A-GRAPH1: final Anvien refresh before change detection returned stale=false, scanned=960, parsed_code=171, failed=0, nodes=40033, relationships=46299. Hidden `.p2p/system` graph file-detail remains unavailable; direct source inspection is retained as the authority for that hidden path.
- E3-P2A-BASELINE1: the framework validator returned 52/59 with the same seven inherited failures previously observed on the clean canonical baseline; no addendum-specific validator failure was introduced.
- E3-P2B-SUP1: `reports/supervisor/rp_supervisor_260826_153823_by_gpt-5-codex_p2p-ct01-attachment-aware-handoff.md` is the fresh zero-trust review. It accepts the addendum technical slice, records `INCLUDED_AND_TESTED`, and rejects full-session closure because inherited validator/doctor/live-host gates remain unresolved.
- E3-P2B-COMMIT1: documentation/artifact checkpoint `4d7beb797bd6b359191f08d3497540f2e3785f45` with tree `81ea11fbdbf97870f71a4fec1ca4aae81060d83d` contains the guide, ledger/roadmap projection, planner updates, one REQUIRED handoff artifact, and coder report. The subsequent Supervisor report is reviewed against this checkpoint; no remote write occurred.
- E3-P2B-DETECT1: fresh staged Anvien detect-changes after the Supervisor slice returned `affected_count=0`, `affected_files=5`, `changed_count=20`, `changed_files=5`, `affected_processes=0`, and `risk_level=low`; the five files are planner actual-status/evidence/plan, the handoff artifact, and the Supervisor report.
- E3-P2B-CLOSURE1: final addendum candidate checkpoint `fa5e3d0d4e915bb6839b1775f6d203a127a1c383` with tree `10ba008610cfb657878865ce27d2e46f7552d89c` contains the fresh Supervisor report and plan closure metadata. The handoff artifact records this checkpoint for Control Tower reconciliation; a later docs-only closure commit may change the tree, so the terminal packet remains the final subject identity.
- E3-P2B-CLOSURE2: final staged Anvien detect-changes before the docs-only closure returned `affected_count=0`, `affected_files=3`, `changed_count=6`, `changed_files=3`, `affected_processes=0`, and `risk_level=low`; only the final planner/evidence/artifact closure bookkeeping was staged.

## Closure Evidence

- CT01 technical implementation is PASS; the full session is BLOCKED because the clean canonical baseline and candidate retain inherited framework/doctor gates and no live-host certification exists.
- E2-P2B-DETECT1 records the final scoped change graph: nine intended changed files, zero affected processes, and low aggregate Anvien risk.
- E2-P2B-SUP1 records the Supervisor REJECT and preserves the no-repair boundary.
- `ATTACHMENT_AWARE_HANDOFF_STATUS: INCLUDED_AND_TESTED`: the addendum is integrated across packet, ledger event, recursive prompt, guide, ledger/roadmap projections, artifact, and seven regression cases.
- `UPLOAD_REQUIRED: YES`: the terminal response selects exactly one REQUIRED artifact; no OPTIONAL or DO_NOT_UPLOAD file is needed for Control Tower content access.
- The artifact is evidence input only. A local path alone does not make its contents available to the Control Tower, and an uploaded artifact is not canonical truth or proof of promotion, deployment, live certification, or Owner approval.
- E2-P2B-COMMIT1: closure commit 76a9a9449927838eb3965448aefe732ed39e55ee with tree 9b876b4dba86bc1bb21358acb881843fb926f0a6; it is four commits ahead of the bound base, retains the promoted anchor as an ancestor, and has no remote write.
- Protected root, canonical main, remote, runtime lock, release surfaces, promotion, deployment, approval, and live host were not touched.
- CANONICAL_PROMOTED: NO; no remote write occurred.
