# P2P-CT01 Control Tower Handoff Artifact

CONTROL_TOWER_HANDOFF_ARTIFACT: TRUE
ATTACHMENT_MANIFEST_SCHEMA: p2p-control-tower-attachment-manifest/1
SESSION_ID: p2p-ct01-codex-20260826-isolated
HOST: CODEX
GOAL_ID: P2P-CT01
GOAL: Establish a durable provider-neutral Control Tower session handoff protocol in the isolated canonical worktree.

## Attachment manifest

UPLOAD_REQUIRED: YES

This artifact is the one minimum required upload for this terminal response.

| Field | Value |
|---|---|
| FILENAME | p2p-ct01-codex-20260826-isolated-CONTROL-TOWER-HANDOFF.md |
| LOCAL_PATH | D:\AI\P2P_dev\P2P-canonical-runtime-01\.tmp\p2p-ct01-control-tower\p2p-ct01-codex-20260826-isolated-CONTROL-TOWER-HANDOFF.md |
| PURPOSE | Carry the bounded CT01 result and attachment-aware handoff contract into the durable Control Tower. |
| WHY_CONTROL_TOWER_NEEDS_CONTENTS | The Control Tower may not be able to read executor-local reports from a path alone; this single file contains the scoped result, evidence pointers, blockers, and explicit attachment semantics. |
| CLASSIFICATION | REQUIRED |

OPTIONAL_ATTACHMENTS: NONE
DO_NOT_UPLOAD_ATTACHMENTS: NONE
LOCAL_PATH_ALONE_PROVES_CONTENTS_AVAILABLE: NO
CONTENTS_AVAILABLE_TO_CONTROL_TOWER: UNKNOWN_UNTIL_ATTACHED
ATTACHMENT_IS_EVIDENCE_INPUT_ONLY: YES
ATTACHMENT_IS_CANONICAL_TRUTH: NO
ATTACHMENT_PROVES_PROMOTION: NO
ATTACHMENT_PROVES_DEPLOYMENT: NO
ATTACHMENT_PROVES_LIVE_CERTIFICATION: NO
ATTACHMENT_PROVES_OWNER_APPROVAL: NO

The user must copy the entire terminal final response to `00 — P2P CONTROL TOWER` and upload only this REQUIRED artifact. The user does not need to choose other reports.

## Session and candidate boundary

SESSION_STATE: BLOCKED
TECHNICAL_CT01_RESULT: PASS
ATTACHMENT_AWARE_HANDOFF_STATUS: INCLUDED_AND_TESTED
ROTATABLE_CONTROL_TOWER_STATUS: INCLUDED_AND_TESTED
TERMINAL_VERDICT: BLOCKED
CANONICAL_PROMOTED: NO
OWNER_APPROVAL: NOT_REQUESTED
PROMOTION: NOT_PERFORMED
DEPLOYMENT: NOT_PERFORMED
LIVE_CERTIFICATION: NOT_PERFORMED
REMOTE_WRITE: NOT_PERFORMED

WORKTREE: D:\AI\P2P_dev\P2P-canonical-runtime-01\.tmp\p2p-ct01-control-tower
BRANCH: codex/p2p-ct01-control-tower
BOUND_BASE_SHA: 28a3ecd9c04d36511269e44c384bff6e11677b93
BOUND_BASE_TREE: cae63e055edd164fbd969f6dbae0d992a4d0efed
IMPLEMENTATION_CHECKPOINT_SHA: 13ccb8910cf2c845acc450b9e354f9d32c5f90a1
IMPLEMENTATION_CHECKPOINT_TREE: d1182567f44b05346361eeb9eeb97ad1cbbc2a00
DOCUMENTATION_HANDOFF_CHECKPOINT_SHA: 4d7beb797bd6b359191f08d3497540f2e3785f45
DOCUMENTATION_HANDOFF_CHECKPOINT_TREE: 81ea11fbdbf97870f71a4fec1ca4aae81060d83d
CANDIDATE_CHECKPOINT_SHA: fa5e3d0d4e915bb6839b1775f6d203a127a1c383
CANDIDATE_CHECKPOINT_TREE: 10ba008610cfb657878865ce27d2e46f7552d89c

## Included scope

The addendum extends the existing CT01 packet, execution-ledger event projection, recursive continuation prompt, operator guide, and isolated regression suite with:

- explicit `UPLOAD_REQUIRED: YES | NO` on every terminal response;
- a structured `CONTROL_TOWER_ATTACHMENT_MANIFEST`;
- exact no-upload copy-back instruction for `NO`;
- exact one-to-three-file manifest entries for `YES`, including filename, local path, purpose, why contents are needed, and REQUIRED / OPTIONAL / DO_NOT_UPLOAD classification;
- fail-closed distinction between a local path and readable file contents;
- explicit evidence-only and noncanonical attachment semantics;
- recursive next-session prompt preservation;
- preference for this one SESSION_ID-CONTROL-TOWER-HANDOFF.md artifact.

## Rotatable Control Tower addendum

The same CT01 boundary now preserves three layers:

1. short-lived bounded execution session on one explicit host lane;
2. replaceable Control Tower instances such as CT001 and CT002;
3. durable P2P repository/evidence/checkpoints/governance as long-lived source of truth.

The implementation emits a compact `P2P_CONTROL_TOWER_SUCCESSOR_PACKET` for rotation and a read-only reconciliation result. The packet carries the current/proposed instance IDs, snapshot sequence, canonical claim/confidence, host lanes, confirmed active execution, Owner Gates, pending work, recently closed material work, blockers/risks, critical invariants, next safe action, durable refs, and unresolved `CHAT_ONLY_NOT_CANONICAL`.

The beginner contract emits exact names from the supplied instance IDs, for example:

- old archive: `90 — P2P CONTROL TOWER — CT001 — ARCHIVE`;
- new chat: `00 — P2P CONTROL TOWER — CT002`.

The successor packet is bootstrap data, not canonical truth. Reconciliation fails closed for stale/unknown canonical claim or snapshot; it does not execute Owner Gates, inherit approval, close or move active execution, reassign host lanes, invent execution, or promote/deploy/live.

## Evidence available in the executor worktree

- Focused protocol tests: `tests/test_p2p_control_tower_session_handoff.py` — 28 passed, including 7 attachment-aware cases and ROTATION A-F.
- Source compile: `python -m py_compile .p2p/system/p2p_capabilities/control_tower_handoff.py` — PASS.
- Rotatable API import smoke: successor packet, rotation wrapper, and reconciliation APIs — PASS.
- Existing project eval validation: `python scripts/p2p_eval.py validate --suite .p2p/evals/suite.json` — PASS.
- Anvien refresh after implementation: stale=false, scanned=960, parsed_code=171, failed=0, nodes=40033, relationships=46299.
- Implementation checkpoint: `b8861c3a68a948634b5d490c6a52a10125fe31a6`, tree `6a555464245cf1f8116ce7fb9668dbcd6df6678e`; hidden `.p2p/system` graph file-detail remains unavailable and is recorded as a tooling limitation.
- The durable technical evidence, fresh coder/Supervisor reports, and remaining full-session blockers are recorded under `docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/` and `reports/` in the executor worktree. The Control Tower cannot read those files from their local paths unless separately attached; this artifact is the selected minimum attachment.

SUPERVISOR_REVIEW_PATH: reports/supervisor/rp_supervisor_260826_161127_by_gpt-5-codex_p2p-ct01-rotatable-control-tower.md
SUPERVISOR_VERDICT: REJECT_FOR_FULL_SESSION; TECHNICAL_ROTATABLE_ADDENDUM_PASS

## Blockers and authority boundary

The full CT01 session remains BLOCKED because inherited framework/doctor gates and absence of independent live-host certification remain unresolved. Those pre-existing gates were observed on the clean canonical baseline and were not repaired in this bounded addendum. No local test, packet, report, or attachment authorizes promotion, deployment, live certification, or Owner approval.

The Control Tower must treat this artifact as proposed evidence input, verify its contents and hashes against fresh canonical repository truth, and keep `PACKET_IS_CANONICAL_TRUTH: NO` and `ATTACHMENT_IS_CANONICAL_TRUTH: NO`.

## Safe next action

Reconcile this attached artifact with the fresh canonical CT01 candidate and existing governance evidence. For a future rotation, CT002 must reconcile the successor packet against durable P2P evidence before accepting material claims. Preserve the BLOCKED terminal state unless independent authority and all required gates are freshly satisfied in a separately authorized action.
