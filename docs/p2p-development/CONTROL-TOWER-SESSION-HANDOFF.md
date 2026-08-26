# P2P-CT01 — Durable Control Tower Session Handoff

Status: FOUNDATION_READY candidate, UNPROMOTED

This document is the durable operator guide and return-contract index for P2P-CT01. It describes a short-lived AI execution session returning structured state to the durable P2P Control Tower. It does not grant permissions, certify a live provider, approve a release, or replace Task State, the execution ledger, evidence authority, or the sole P2P router.

## Beginner workflow

The user-facing workflow is intentionally small:

CREATE CHAT → PASTE PROMPT → COPY FINAL RESPONSE → PASTE TO CONTROL TOWER

The beginner does not need to reconstruct a transcript, choose a provider implementation, paste hidden context, or write a technical handoff. The prompt already binds the session to the Control Tower goal. The receiving Control Tower reconciles the return packet against fresh repository truth.

The exact action shown at the end of a generated prompt is:

USER_ACTION:
Copy nguyên toàn bộ phản hồi cuối này vào:
00 — P2P CONTROL TOWER

Không cần viết thêm nội dung bàn giao.

If the host returns a failure, blocked state, owner gate, stale base, or unknown base, copy that result unchanged. A failure is useful return state; it must not be rewritten as success.

## Durable Control Tower versus short-lived session

The Control Tower is the durable project-facing coordinator. It records the packet as proposed return/evidence data and routes it through existing goal, task, evidence, execution-ledger, approval, and drift controls.

The execution session is short-lived and host-bound. It must start from an explicit four-field binding:

| Field | Meaning |
|---|---|
| SESSION_ID | identity of this short-lived session |
| HOST | one explicit provider-neutral host label, such as CODEX, MANUS, CLAUDE, GEMINI, or a future label |
| GOAL_ID | durable P2P goal identity |
| GOAL | human-readable bounded goal |

HOST comes from the structured binding. It is never selected by parsing a sentence in the prompt or a pasted response. A host label is infrastructure identity, not a canonical P2P capability identity.

No implicit inheritance is allowed. Chat history, previous session state, hidden conversation identifiers, and unstated context are not part of the contract. Required context must be represented by durable project/evidence references and validated by the existing P2P boundaries.

## Return contract

The implementation path is .p2p/system/p2p_capabilities/control_tower_handoff.py. The reusable regression proof is tests/test_p2p_control_tower_session_handoff.py. The structured packet marker is CONTROL_TOWER_RETURN_PACKET with schema p2p-control-tower-return-packet/1.

Every terminal response carries these fields:

| Packet field | Required meaning |
|---|---|
| SESSION_ID, HOST, GOAL_ID, GOAL | exact session binding |
| SESSION_STATE | COMPLETED, READY, WAITING_OWNER_GATE, BLOCKED, FAILED, or ABORTED |
| CANONICAL_BASE_SHA, CANONICAL_BASE_TREE | base identity used by the session, or UNKNOWN |
| CANONICAL_RELATION | CURRENT, STALE, or UNKNOWN as reported/reconciled |
| WORKTREE, BRANCH | execution location, or UNKNOWN |
| CHANGES | structured observed changes |
| TEST_RESULTS | structured validation results |
| EVIDENCE | evidence references |
| CANDIDATE_OR_CHECKPOINT_SHA | candidate/checkpoint identity, or UNKNOWN |
| TERMINAL_VERDICT | must agree with SESSION_STATE |
| OWNER_GATE | explicit owner decision required, when applicable |
| BLOCKERS | truthful blockers, including failures |
| NEXT_RECOMMENDED_ACTION | one safe next action |

The packet contains PACKET_IS_CANONICAL_TRUTH: NO. It is not canonical repository truth, not approval, not a promotion record, and not a host-certification receipt. The packet can be serialized as an event for the existing execution-ledger writer through the module's to_execution_ledger_event function; the Control Tower module itself does not open a ledger file or create a second store.

## Attachment-aware terminal handoff

Every terminal response must declare `UPLOAD_REQUIRED: YES` or `UPLOAD_REQUIRED: NO` and include `CONTROL_TOWER_ATTACHMENT_MANIFEST`.

When `UPLOAD_REQUIRED: NO`, the response must state that the user only needs to copy the entire final response to `00 — P2P CONTROL TOWER`; no file upload is needed.

When `UPLOAD_REQUIRED: YES`, the manifest must identify the minimum one to three files using the exact filename, local path, purpose, why the Control Tower needs the file contents, and one of `REQUIRED`, `OPTIONAL`, or `DO_NOT_UPLOAD`. The user is not asked to decide which evidence matters. `REQUIRED` entries are the only files that must be uploaded; `OPTIONAL` entries are not required; `DO_NOT_UPLOAD` entries must not be uploaded.

The local path is only a locator. `LOCAL_PATH_ALONE_PROVES_CONTENTS_AVAILABLE: NO` and `CONTENTS_AVAILABLE_TO_CONTROL_TOWER: UNKNOWN` remain explicit until the user attaches the file. An attachment is evidence input only: `ATTACHMENT_IS_CANONICAL_TRUTH: NO`. An attachment cannot by itself prove promotion, deployment, live certification, or Owner approval. The Control Tower must reconcile attached evidence with fresh canonical repository and governance truth.

When a file is needed, prefer one artifact named `<SESSION_ID>-CONTROL-TOWER-HANDOFF.md` so the user can upload one clearly scoped handoff instead of searching through reports. The artifact remains noncanonical evidence and does not replace the packet, execution ledger, evidence chain, approval record, or fresh canonical checks.

The existing lifecycle vocabulary remains the authority boundary:

| CT01 state | Existing lifecycle mapping |
|---|---|
| COMPLETED | DONE |
| READY | READY |
| WAITING_OWNER_GATE | WAITING_OWNER |
| BLOCKED | BLOCKED |
| FAILED | BLOCKED, with failure preserved |
| ABORTED | CANCELLED |

## Reconciliation rules

1. The Control Tower compares both the packet base SHA and base tree with fresh current canonical values.
2. Exact equality yields CURRENT. A known mismatch yields STALE. Any unknown side yields UNKNOWN.
3. STALE and UNKNOWN both produce RECONCILIATION_REQUIRED.
4. Reconciliation never overwrites canonical state, promotes a candidate, merges a branch, or executes a protected action.
5. READY is a technical return state, not promotion.
6. WAITING_OWNER_GATE records the exact gate and stops at the owner boundary.
7. FAILED, BLOCKED, and ABORTED return to the Control Tower as terminal outcomes; they are not hidden, retried blindly, or converted to success.
8. Ingest updates only the lane named by the packet's explicit HOST. Narrative claims about another provider are ignored.

The ControlTowerState object is a serializable projection over these results. Persistence belongs to the existing execution-ledger and evidence callers. The module does not launch a worker, select a provider, or persist hidden chat state.

## Recursive continuation

The build_execution_prompt function emits a self-contained prompt with:

- the explicit four-field binding;
- the current worktree/branch and canonical base references;
- the bounded task and acceptance criteria;
- the terminal state vocabulary;
- every CONTROL_TOWER_RETURN_PACKET field;
- the `UPLOAD_REQUIRED` declaration and `CONTROL_TOWER_ATTACHMENT_MANIFEST` contract;
- the exact no-upload instruction or the minimum one-to-three-file attachment fields;
- the local-path/content-availability, evidence-only, and noncanonical attachment invariants;
- the preferred single `<SESSION_ID>-CONTROL-TOWER-HANDOFF.md` artifact;
- the explicit packet-is-not-canonical-truth marker;
- the exact USER_ACTION text.

The final response from the new host is copied in full to 00 — P2P CONTROL TOWER. The next session is created from the durable packet and fresh project evidence, not from the prior chat.

## Existing architecture binding

CT01 composes existing surfaces:

- host_executor.py supplies the provider-neutral request/receipt/handoff boundary and the no-chat-history/no-auto-start rule;
- task_state.py supplies durable task/checkpoint state and deliberately keeps session/host identity out of task identity;
- live_execution.py and read_evidence.py bind execution/evidence to the expected session and goal;
- p2p_evidence_chain.py binds evidence lineage;
- scripts/p2p_workflow.py supplies the existing Goal Contract, project status, and execution-ledger event path;
- the capability ledger and development charter provide discoverability and status only.

No second router, second truth store, nested certification system, simulated quorum, or provider-specific core is introduced.

## Discovery and operator paths

| Surface | Path |
|---|---|
| Return contract and implementation | .p2p/system/p2p_capabilities/control_tower_handoff.py |
| A-H behavior proof | tests/test_p2p_control_tower_session_handoff.py |
| Attachment-aware handoff artifact | `<SESSION_ID>-CONTROL-TOWER-HANDOFF.md` in the executor's scoped evidence directory |
| This operator guide | docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md |
| Planner/evidence trail | docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/ |
| Capability projection | docs/p2p-development/capability-ledger/capability-index.json |
| Derived roadmap projection | docs/p2p-development/current-roadmap.md |
| Project task/evidence persistence | existing .p2p/state and execution-ledger surfaces |
| Governance boundary | governance/development-control.json and P2P-DEVELOPMENT-CHARTER.md |

## Validation boundary and known gaps

The local development-source proof is the 22-case focused suite, including seven attachment-aware cases, plus relevant existing P2P tests and doctor/compile checks. It proves the protocol behavior in an isolated worktree. It does not prove a live Codex, Manus, Claude, Gemini, or future-host connection, live adapter certification, quorum, release readiness, owner approval, promotion, or deployment. Those remain UNKNOWN or unperformed until their existing independent evidence paths are satisfied.

P2P-CT01 terminal state for this candidate is FOUNDATION_READY / UNPROMOTED. CANONICAL_PROMOTED: NO. No remote write was performed.
