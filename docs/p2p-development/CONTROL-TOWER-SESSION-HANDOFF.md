# P2P-CT01 — Durable Control Tower Session Handoff

Status: FOUNDATION_READY candidate, UNPROMOTED
ROTATABLE_CONTROL_TOWER_STATUS: INCLUDED_AND_TESTED

This document is the durable operator guide and return-contract index for P2P-CT01. It describes a short-lived AI execution session returning structured state to a rotatable Control Tower while the durable P2P repository, evidence, checkpoints, and governance remain the long-lived source of truth. It does not grant permissions, certify a live provider, approve a release, or replace Task State, the execution ledger, evidence authority, or the sole P2P router.

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

### Foreground CLI

The optional CLI is a thin operator surface over the same contract:

```text
python scripts/p2p_control_tower.py start --host CODEX --goal-id P2P-CT01 --goal "Durable Control Tower Session Handoff Integration"
python scripts/p2p_control_tower.py snapshot
python scripts/p2p_control_tower.py ingest --response-file <utf8-final-response.txt> --current-canonical-base-sha <sha> --current-canonical-base-tree <tree>
python scripts/p2p_control_tower.py next --host CODEX
```

`start` and `next` register only an explicit foreground session. `ingest` requires both fresh canonical base values when it is used for reconciliation; absent values remain `UNKNOWN` and fail closed. `next` reads the existing task-state surface and returns `UNKNOWN` when it is not initialized. No command launches a host, changes task state, promotes, deploys, releases, or writes remotely.

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

## Three-layer lifecycle and Control Tower rotation

P2P-CT01 keeps three layers distinct:

1. The bounded execution session is short-lived and remains bound to one explicit host lane.
2. The Control Tower chat is a replaceable coordination instance (`CT001`, `CT002`, ...), not canonical truth.
3. The durable P2P repository, evidence/checkpoints, and governance records are the long-lived authority.

When the Owner says `Prepare Control Tower rotation`, the current instance emits one compact `P2P_CONTROL_TOWER_SUCCESSOR_PACKET`. It contains the current instance ID, proposed successor ID, latest snapshot sequence, canonical claim/confidence, host lanes, confirmed active execution, Owner Gates, pending work, recently closed material work, blockers/risks, critical invariants, next safe action, durable evidence/checkpoint refs, unresolved `CHAT_ONLY_NOT_CANONICAL`, and the existing attachment manifest.

The packet is bootstrap/coordination data, not canonical truth. CT002 must reconcile material claims with durable P2P evidence and the current snapshot before accepting them. A stale or unknown canonical claim/snapshot yields `RECONCILIATION_REQUIRED`. CT002 must preserve an active Manus execution as Manus, leave Owner Gates unexecuted, avoid inheriting approval, avoid inventing execution, and never transfer a host lane because the chat rotated.

### Beginner rotation workflow

1. Say: `Prepare Control Tower rotation.`
2. Copy the complete successor response, including `ROTATION_USER_ACTION` and the nested `P2P_CONTROL_TOWER_SUCCESSOR_PACKET`.
3. Rename the old chat to the exact emitted name, normally `90 — P2P CONTROL TOWER — CT001 — ARCHIVE`.
4. Create the exact emitted successor chat, normally `00 — P2P CONTROL TOWER — CT002`.
5. Paste the complete successor packet into CT002.
6. Upload only the explicitly listed `REQUIRED` attachment when `UPLOAD_REQUIRED=YES`; with `NO`, copy the final response and upload nothing.
7. Let CT002 reconcile against durable evidence and continue from `NEXT_SAFE_ACTION`.

The user does not summarize CT001 or reproduce the full chat history. Rotation is qualitative: use it when the current Control Tower becomes unwieldy, loses continuity, or the Owner wants a clean coordination surface. A soft recommendation after roughly 10–20 material handoffs may be useful, but it is not a rigid trigger and never closes active execution.

### Context-budget compaction and thin successor handoff

RULE 16 in the canonical operations notebook defines the context-budget policy.
This guide reuses the existing successor packet and rotation wrapper; it does
not create a second compaction format.

Operational defaults are `SOFT_CONTEXT_LIMIT = 70000` tokens and
`ROTATION_CONTEXT_LIMIT = 100000` tokens. They are heuristics, not model hard
limits, and exact token measurement is not required. Near the soft limit,
prefer targeted retrieval and stop carrying obsolete logs/diffs or duplicated
durable material. At the rotation limit, or when equivalent qualitative
context exhaustion is visible, rotate before substantial new work.

`P2P_CONTROL_TOWER_SUCCESSOR_PACKET` is the compact durable handoff. Populate
it with live state only: active/pending work, Owner Gates, blockers/risks,
critical live decisions, active evidence/checkpoint references, next safe
action, acceptance/stop conditions when relevant, and the authoritative
references the successor must rehydrate from. `FULL_CHAT_HISTORY_INCLUDED=NO`
remains mandatory.

Do not carry forward old full diffs, obsolete terminal logs, superseded plans,
dead-end exploration, already-merged code blobs, copied governance text, prior
reasoning history, or entire executor conversations after their outcome is
durably represented. Never drop unresolved blockers or evidence that still
affects acceptance.

The successor rehydrates from the active law, current durable task/project
state, exact relevant docs/source paths, and exact PR/commit/receipt references.
Mutable claims such as main SHA, PR HEAD, branch state, mergeability, and test
status must be freshly verified where practical before they drive a decision.
The successor packet is coordination data, not canonical truth.

### GitHub-connected Arena Agent Mode boundary

The Arena-specific session contract is canonical in
`docs/ARENA_AGENT_MODE_PROTOCOL.md`. For one Arena development pass, the
bounded unit is:

```text
ONE ARENA CHAT SESSION
    -> ONE BOUNDED DEVELOPMENT GOAL
    -> ONE WORKING BRANCH
    -> ONE PR
```

Arena conversation state is ephemeral; GitHub project state is canonical. For
`START_NEW_SESSION`, the Owner-facing prompt must start with one concise,
human-readable first-line task title (normally `<PROJECT> — <bounded task/outcome>`)
before any routing boilerplate, and `CHAT_TITLE` must repeat that exact title.
Do not start a new Arena prompt with `GỬI CHO:`, `DESTINATION=`, `TASK_ID=`, a
code fence, or a generic `P2P` prefix. After the title, the prompt must state
`DESTINATION=ARENA AI`, an explicit `SESSION_ACTION`, `CHAT_TITLE`,
`SESSION_GOAL`, and `PR_EXPECTATION`. For `CONTINUE_CURRENT_SESSION`, preserve
the exact existing chat title. Continue the current session only for the same
open PR and healthy context; start a new one for a new PR or goal, merged/closed
PR, context exhaustion, or persistent tool confusion. Prompt count is not a
rotation trigger.

Arena executors also discover the single canonical operations notebook.
For Supreme Law authority,
`TASK_BRANCH != LAW_AUTHORITY` and `TARGET_PROJECT != LAW_SOURCE`.
When accessible, the active source is
`7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`;
an installed project's `AGENTS.md` and
`.p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md` are local projections, not
independent authority. P2P-generated prompts carry `SUPREME_LAW_CAPSULE` when
the canonical repository cannot be read.

Before Control Tower writes any executor prompt, it MUST read
`P2P_SUPREME_OPERATING_LAW_V1` from the active canonical notebook and use that law
to choose the bounded outcome, authority boundary, next useful action,
verification scope, retry behavior, and stop condition. This is a prompt-write
preflight, not a new planning phase. If the receiving executor cannot read the
repository notebook, the generated prompt must include the compact
`SUPREME_LAW_CAPSULE` instead of pretending the file was read.

Before merge or promotion, applicable implementation, tests/QA evidence,
screenshots, reports, handoff material, current-state/session-index files, and
candidate-SHA-pinned visual evidence must already be on the candidate branch.
After `PR MERGED OR CLOSED`,
`OLD_SESSION_GITHUB_WRITE_CAPABILITY=TERMINATED`; the old Arena session is
never reused for GitHub writes.

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

The packet contains PACKET_IS_CANONICAL_TRUTH: NO. It is not canonical repository truth, not approval, not a promotion record, and not a host-certification receipt. The packet can be serialized as an event for the existing execution-ledger writer through the module's to_execution_ledger_event function; the module never creates a second store.

The foreground coordinator in the same module adds `ControlTower.start_session`, `ControlTower.snapshot`, `ControlTower.ingest_response`, and `ControlTower.ingest_packet`. These methods persist only structured session-start and return events through the existing `.p2p/state/execution-ledger.jsonl` writer; they never persist the raw executor response and never create `control-tower.json` or another task/event store. `PACKET_FINGERPRINT` makes an identical replay idempotent and a different second terminal packet fail closed. The optional CLI is `scripts/p2p_control_tower.py`; it exposes `start`, `snapshot`, `ingest`, and task-state-backed `next` in the foreground only.

The rotation wrapper is `CONTROL_TOWER_ROTATION_HANDOFF` with schema `p2p-control-tower-rotation-handoff/1`; the nested successor packet uses `p2p-control-tower-successor-packet/1`. Both are compact, JSON-safe, and explicitly mark `SUCCESSOR_PACKET_IS_CANONICAL_TRUTH: NO` and `FULL_CHAT_HISTORY_INCLUDED: NO`.

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

The ControlTowerState object is a serializable projection over these results. The coordinator replays only structured CT01 events from the existing execution ledger; it does not launch a worker, select a provider, or persist hidden chat state. If task-state is absent or invalid, `next` returns `UNKNOWN` or a bounded blocker and does not invent a session.

## Recursive continuation

The build_execution_prompt function emits a self-contained prompt with:

- the mandatory `P2P_SUPREME_OPERATING_LAW_V1` preflight plus compact
  `SUPREME_LAW_CAPSULE` fallback for executors that cannot read the repo;
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
- the rotatable three-layer lifecycle and `P2P_CONTROL_TOWER_SUCCESSOR_PACKET` contract;
- the exact CT001 archive / CT002 successor-chat workflow and reconciliation boundary;
- the exact USER_ACTION text.

The final response from the new host is copied in full to 00 — P2P CONTROL TOWER. The next session is created from the durable packet and fresh project evidence, not from the prior chat.

## Arena FAST_CANARY runtime enforcement (MODEL_CANARY_GATE_V1)

The canonical gate in the operations notebook is policy. This surface makes the
same gate executable inside the existing prompt/session lifecycle, with no
second Control Tower, router, daemon, scheduler, benchmark service, score
database, telemetry platform, project registry, or parallel state store.

Trigger is derived from three inputs only: the explicit `HOST` label, an
explicit Control Tower `LOW_RISK_MECHANICAL` declaration, and durable session
quality replayed from the existing execution ledger. Task text is never
risk-classified: the free-text `start` and Owner `/goal` seams carry no
structured task profile, so everything that is not explicitly declared
low-risk/mechanical fails closed into `MEDIUM_OR_HIGH_RISK`.

```text
HOST=ARENA + NEW session + not declared LOW_RISK_MECHANICAL + SESSION_QUALITY=UNKNOWN
  -> first turn: FIRST_SAFE_REAL_TASK_SLICE -> CANARY_EVIDENCE_PACKET_V1 -> STOP
  -> Control Tower ingests the evidence-only return and grades externally
     (GREEN|YELLOW|ORANGE|RED|UNVERIFIED)
  -> OWNER_CONTINUATION_GATE_V1
  -> GREEN + explicit Owner continuation resumes the ORIGINAL task in the SAME
     session; only then does RULE 20 AUTONOMOUS_UNTIL_TERMINAL apply
```

One first-turn return contract. A triggered canary prompt carries
`FIRST_TURN_RETURN_CONTRACT=CANARY_EVIDENCE_PACKET_V1_THEN_STOP` and no
`CONTROL_TOWER_RETURN_PACKET` markers or terminal-packet instructions. The
executor returns exactly the canonical shape:

```text
CANARY_EVIDENCE_PACKET_V1
P2P_LAW_SOURCE=... CURRENT_STATE=... FACTS=... DECISIVE_CHECK=... CHECK_RESULT=...
ERRORS_ENCOUNTERED=... RECOVERY_ACTIONS=... DURABLE_MUTATION_CREATED=NO MODEL_IDENTITY=UNKNOWN

CONTINUATION_CHECKPOINT=READY
OWNER_ACTION_REQUIRED=YES
NATIVE_ACTION_HINT=KEEP_WORKING_IF_APPROVED
FALLBACK_OWNER_REPLY=Tiếp tục công việc
```

That evidence-only response carries no packet binding, so the Control Tower
names the session it registered: `ingest --response-file <file> --session-id
<SESSION_ID>`. The resumed ORIGINAL task receives the full terminal
`CONTROL_TOWER_RETURN_PACKET` contract in the continuation prompt, and its
terminal return is ingested for the SAME session. Before the Owner continuation
is recorded, any further return for a triggered canary session is graded as the
canary turn or rejected fail-closed; a terminal conclusion in the canary turn is
RED even when evidence is attached.

The Owner `/goal` Arena packet follows the same rule: for
`FAST_CANARY_REQUIRED=YES` it serializes `EXECUTION_MODE=FAST_CANARY_FIRST_SAFE_SLICE_THEN_STOP`
as the only active mode. RULE 20, branch/PR creation, and the ReturnPacket spec
travel only inside the bounded `RESUMED_TASK_CONTRACT ... END_RESUMED_TASK_CONTRACT`
section (`RESUMED_TASK_MODE=AUTONOMOUS_UNTIL_TERMINAL`), which applies after
external GREEN + explicit Owner continuation. The canary block comes last, so
the final active instruction is STOP.

Bypass is fail-closed and explicit: `NON_ARENA_EXECUTOR`,
`LOW_RISK_MECHANICAL_ARENA_TASK` (only via `start --low-risk-mechanical`),
`EXISTING_SESSION_CONTINUATION`, and `SESSION_QUALITY_ALREADY_ESTABLISHED` all
yield `FAST_CANARY_REQUIRED=NO`.

Required canary context is never silently truncated or evicted. The prompt
budget is derived from `CANARY_PROMPT_BUDGET_GUARD_CHARS`; when the required
canary context cannot fit, generation fails closed with
`CONTROL_TOWER_CANARY_CONTEXT_DID_NOT_FIT` instead of emitting a degraded
prompt.

Durable state stays inside the existing execution ledger: the canary directive
rides on the existing `CONTROL_TOWER_SESSION_STARTED` event, the externally
graded canary turn is one `CONTROL_TOWER_CANARY_EVIDENCE` event (canonical
evidence fields, checkpoint presence, optional executor-packet summary, grade),
and the Owner decision is one `CONTROL_TOWER_CANARY_CONTINUATION` event. The
`CONTROL_TOWER_RETURN_PACKET` slot stays reserved for the resumed task's
terminal return. Replay is idempotent and the raw executor transcript is never
persisted. Canary evidence passes the same ledger-safety validation as replay
before it is written; secret-like or oversized evidence fails closed with
`CANARY_EVIDENCE_UNSAFE_FOR_LEDGER` instead of poisoning later replays.

Managed projects inherit the path through the normal release: the CLI ships in
`SCRIPT_FILES` and both installers place it at
`.p2p/system/scripts/p2p_control_tower.py`; run from the managed project it
defaults `--root` to that project and reads the installed law projection.

| Operator surface | Command / symbol |
|---|---|
| Triggered prompt generation | `scripts/p2p_control_tower.py start --host ARENA ... [--low-risk-mechanical]` |
| Canary ingest + external grade | `scripts/p2p_control_tower.py ingest --response-file ... --session-id ...` |
| Owner continuation | `scripts/p2p_control_tower.py continue --session-id ... [--owner-continuation YES] [--owner-reply "Tiếp tục công việc"]` |
| Managed-project CLI | `.p2p/system/scripts/p2p_control_tower.py` (installed by `install.sh` / `install.ps1`) |
| Decision / serialization | `canary_requirement`, `CanaryDirective`, `canary_prompt_lines` |
| Evidence parse + grade | `parse_canary_evidence_packet`, `classify_canary_evidence`, `ControlTower.ingest_canary_evidence` |
| Session quality | `ControlTower.session_quality(goal_id, session_id)` |
| Executable proof | tests/test_p2p_arena_canary_runtime.py, tests/test_p2p_arena_canary_baseline_gap.py, tests/test_p2p_arena_canary_install_inheritance.py |

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
| A-H and ROTATION A-F behavior proof | tests/test_p2p_control_tower_session_handoff.py |
| Arena FAST_CANARY runtime proof | tests/test_p2p_arena_canary_runtime.py, tests/test_p2p_arena_canary_install_inheritance.py |
| Durable coordinator/CLI behavior proof | tests/test_p2p_control_tower_durable.py |
| Foreground coordinator CLI | scripts/p2p_control_tower.py |
| Successor packet/reconciliation API | `ControlTowerSuccessorPacket`, `ControlTowerRotationHandoff`, `reconcile_control_tower_successor` in the implementation module |
| Attachment-aware handoff artifact | `<SESSION_ID>-CONTROL-TOWER-HANDOFF.md` in the executor's scoped evidence directory |
| This operator guide | docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md |
| Arena Agent Mode protocol | docs/ARENA_AGENT_MODE_PROTOCOL.md |
| P2P operations notebook | docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md |
| Planner/evidence trail | docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/ |
| Capability projection | docs/p2p-development/capability-ledger/capability-index.json |
| Derived roadmap projection | docs/p2p-development/current-roadmap.md |
| Project task/evidence persistence | existing .p2p/state and execution-ledger surfaces |
| Governance boundary | governance/development-control.json and P2P-DEVELOPMENT-CHARTER.md |

## Validation boundary and known gaps

The local development-source proof is the 37-case focused suite: the original 28 CT01 cases, including seven attachment-aware and six `ROTATION A-F` cases, plus nine durable coordinator/CLI/discovery cases. It proves the protocol, compact successor reconciliation, existing-ledger replay, fail-closed binding, and foreground CLI behavior in an isolated worktree. It does not prove a live Codex, Manus, Claude, Gemini, or future-host connection, live adapter certification, quorum, release readiness, owner approval, promotion, or deployment. Those remain UNKNOWN or unperformed until their existing independent evidence paths are satisfied.

P2P-CT01 terminal state for this candidate is FOUNDATION_READY / UNPROMOTED. `ROTATABLE_CONTROL_TOWER_STATUS: INCLUDED_AND_TESTED`. `CANONICAL_PROMOTED: NO`. No remote write was performed.
