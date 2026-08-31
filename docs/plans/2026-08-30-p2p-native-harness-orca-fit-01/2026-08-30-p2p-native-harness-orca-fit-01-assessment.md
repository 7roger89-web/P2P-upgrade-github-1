# Assessment — P2P-NATIVE-HARNESS-ORCA-FIT-01: Orca as an optional native-harness execution adapter

Status: ASSESSMENT ONLY — no code changed, no Orca/Dely installed, no Blender, no assets, no second orchestrator
Date: 2026-08-30
Workstream: `P2P-NATIVE-HARNESS-ORCA-FIT-01`
Baseline: `origin/main` = `1c9eea39ce6aa0b721d67fa6b7130918357eea4d` (tree `0fab3c59bd34094219693ca8ac5e7e80e2200723`)
Supervisor: `P2P_ORCA_FIT_PR29_SUPERVISOR_PASS` — aligned against `EXACT_REVIEWED_HEAD`
`dbae22fe7c4b38d5783f693bf8eaf6d554554387` (fix-only documentation pass on the same PR #29)

### Supervisor alignment (applied in this revision)

| Classification | Result | Effect on this document |
| --- | --- | --- |
| `PHASE_MODEL_EFFORT_CLASSIFICATION` | `ALREADY_EXPRESSIBLE` | Any recommendation to add `MODEL`/`EFFORT`/`PHASE` to `WorkItem` is **removed and explicitly rejected**. Selection reuses the existing execution envelope / selection profile, `BackendAdapterIdentity`, and existing routing/adapter metadata. **No `WorkItem` schema growth is authorized.** |
| `REMEDIATION_POLICY_CLASSIFICATION` | `ALREADY_EXPRESSIBLE` | No new subsystem or primitive proposed. "One remediation pass → REPLAN" is stated as a **bounded policy rule only**, expressible through existing execution policy / retry controls. |
| `WORKTREE_FIELD_CLASSIFICATION` | `NECESSARY_SMALL_ADDITION` | Retained as the **single** concrete small addition: populate the existing `ControlTowerReturnPacket.worktree` slot from execution evidence/receipt where the adapter can prove it. **No new worktree schema or store.** |
| `RA_EXT_011_IDENTITY` | `UNVERIFIED` | Preserved as unverified. Not reconciled to `stablyai/orca` / `onorca.dev`; ledger not modified. Runtime/identity probe remains the separate `P2P-NATIVE-HARNESS-ORCA-PROBE-01`. |

Preserved unchanged from the reviewed head: Orca optional adapter only; Dely install NOT recommended;
P2P Control Tower retains authority; Work Factory retains orchestration; `BackendExecutionBridge` is
the integration seam; Git remains candidate truth; the existing `ReturnPacket` remains the normalized
handoff; local runtime verification still required.

## Question

Can Orca serve as an **optional** native-harness execution adapter *beneath* the existing canonical
P2P Work Factory, so Arena/P2P can route work to native harnesses (Codex, Claude, Gemini, Kiro,
Cursor, …) without the Owner copying prompts by hand — **without** Orca or Dely becoming the
orchestrator or the authority?

## Verdict in one line

**Yes, as an optional adapter — and no new orchestrator, ontology, or store is required, because the
seam already exists.** P2P already has a provider-neutral adapter registry whose own docstring
anticipates exactly this: *"any C34 backend-contract adapter (hermes-cli, manus-api, **or a future
registered adapter**)"* and *"Adding a new adapter requires registering its factory in a
caller-supplied registry; nothing in the AutoPilot core changes."*
(`.p2p/system/p2p_capabilities/backend_execution_bridge.py`, lines 1–22)

**Dely install: NOT recommended.** Dely would install a *second control protocol* with its own
approval boundary, its own two human gates, its own design-contract artifact, and its own release
step — every one of which P2P already owns canonically — and it makes Orca a **required** execution
plane, which inverts the optional-adapter requirement.

---

## Evidence base

### Repository facts (verified by tool in this session)

| Fact | Where |
| --- | --- |
| Adapter registry + bridge, provider-neutral, factory-registered | `backend_execution_bridge.py` — `BackendAdapterRegistry.register/resolve/summary`, `BackendExecutionBridge.execute`, `AdapterFactory = Callable[[], Any]` |
| Adapter identity surface already carries harness/model/protocol/workspace/environment | `backend_contract.py` `BackendAdapterIdentity`: `adapter_id, adapter_version, adapter_state, harness_identity, provider_identity, model_identity, protocol, toolset_capabilities, workspace_binding, environment_binding` |
| Honest 5-state adapter chain; `LIVE_CERTIFIED` is capability-scoped, `CURRENTLY_ELIGIBLE` never pre-declared | `backend_contract.py` lines 87–114 |
| Existing adapters are the precedent: `HermesAdapter` (CLI), `ManusAdapter` (API) | `hermes_adapter.py`, `manus_adapter.py`; adapter surface = `identity()`, `health()`, `execute()`, `adapter_states()`; `identity.protocol == "CLI_ONESHOT"` |
| Work Factory flow is durable and fail-closed | `work_item_handoff.py` — `WORK_ITEM_SCHEMA = "p2p-work-item/1"`; events `WORK_ITEM_REGISTERED` / `WORK_ITEM_LANE_STARTED` / `WORK_ITEM_RETURN`; `register_work_item`, `start_lane`, `ingest_return`, `integration_queue`, `verify_integration_queue` |
| Executor == existing Control Tower host lane | `work_item_handoff.py:233` `normalize_host(self.executor)`; `WORK_ITEM_LANE_MUST_BE_EXECUTOR`; `WORK_ITEM_EXECUTOR_MISMATCH` |
| ReturnPacket + Owner Gate are canonical and never executed here | `control_tower_handoff.py` `ControlTowerReturnPacket` raises `OWNER_GATE_MUST_BE_OBJECT` / `OWNER_GATE_REQUIRED`; `WAITING_OWNER_GATE` lifecycle |
| Work Factory already **records** a worktree binding but never provisions one | `control_tower_handoff.py:877` `worktree: str = "UNKNOWN"`; only recording sites exist — no worktree creation anywhere in `p2p_capabilities/` |
| `isolation.py` is a path guard, not worktree isolation | `isolation.py` = `assert_isolated_target()` only |
| Concurrency/split-brain is already owned by P2P | `fw06_operational_resilience.py` §33–35 execution leases: `LEASE_FIELDS`, `LEASE_CONFLICT`, `STALE_LEASE`, `WORKSPACE_CONFLICT`, `DEFAULT_LEASE_TTL_SECONDS = 60` |
| Bounded retry exists; a replan trigger exists | FW06 §10 `max_retries`, `ENVELOPE_RETRY_POLICY_MISSING_MAX_RETRIES`; `foreground_execution.py:54` `SCOPE_EXPANSION_REQUIRES_REPLAN` |
| Risk-proportional gates exist | `selection_risk.py` `classify_task_risk`, `risk_is_rejectable`; `governance/approval-policy.json` (`technical_gates_run_before_approval`, `approval_cannot_override_failed_gate`, `subject_change_invalidates_approval`, `agent_may_self_approve: false`, `manual_cli_is_preferred_for_release_or_deploy`) |
| Model/effort exist as ceilings but are **not** on the work item | `live_execution.py` `requested_reasoning_effort`; `selection_filter.py` `reasoning_effort_class`. `WorkItem` fields (verified, lines 208–253) are `work_item_id, project, workstream, base_sha, base_tree, executor, scope, dependencies, expected_output, session_id` — **no model, effort, or phase field** |
| Adapter output may never become authority | `docs/SPEC/P2P-PROVIDER-ABSTRACTION-SPEC.md`: provider output "cannot select the canonical quorum, grant permissions, approve facts, or change the router's one-owner boundary" |
| No quota/account-aware selection exists today | Only *reactive* `RATE_LIMIT` classification (`backend_contract.py:541`, `manus_adapter.py:315`). No proactive account/quota-aware picker |
| External research intake is Owner-gated and append-only | `governance/research-adoption-ledger.json`: 68 records (last `RA-EXT-068`); "append-and-reconcile only: historical records are never rewritten"; intake requires an Owner-accepted direction |
| An Orca record already exists; its identity is **UNVERIFIED** | `RA-EXT-011` "Orca AI Orchestrator", `status: SHIPPED`, concepts adopted into C17/FW06. Its `source_reference` is *"orchestration concepts researched in C17/FW06 goals"* — it does **not** name `stablyai/orca` or `onorca.dev`, so the record is **not** reconciled to the Orca assessed here. Identity is left `UNVERIFIED` and the ledger is not modified |

Baseline test run (this session, after `pip install pytest --break-system-packages` to unblock the
C34 suite which imports pytest):

```
python3 -m unittest tests.test_p2p_work_item_handoff \
                    tests.test_p2p_c34_real_backend_contract \
                    tests.test_p2p_control_tower_session_handoff \
                    tests.test_p2p_parallel_execution \
                    tests.test_p2p_c35_provider_neutral_runtime
Ran 113 tests in 3.339s — OK
```

### External facts (fetched this session)

**Orca** = `stablyai/orca` (onorca.dev), Stably's "Agent Development Environment": an Electron
**desktop app** (macOS / Windows / Linux + mobile companion) that runs Claude Code, Codex, OpenCode,
Grok, Gemini, Cursor, GitHub Copilot, Amp, Kiro, Qwen Code and "any CLI agent" side by side in real
git worktrees. 57.2k stars, 9,547 commits, actively developed.

Its CLI orchestration surface (`onorca.dev/docs/cli/orchestration`) maps almost one-to-one onto the
requested capabilities:

| Requested capability | Orca surface |
| --- | --- |
| native harness launch | `orca orchestration worker-start --task <id> --worktree current\|new-child\|new-top-level --agent codex\|claude\|cursor …` |
| model / harness selection | `--agent`, `--model <opaque provider model ID>` (Claude/Codex/Cursor), `--effort high` (requires `--model`) |
| isolated session / worktree | `--worktree new-child --name <n> --setup run`; `orca worktree create --name <n> --agent codex` |
| run status | `worker-show --dispatch <id>`, `worker-read --dispatch <id>`, `task-list --json`, `dispatch-show --task <id>`; task states `pending/ready/dispatched/completed/failed/blocked` |
| handoff / result capture | `orca orchestration check --wait --types worker_done,escalation,question --timeout-ms … --json`; worker sends `worker_done --outcome succeeded\|failed --files-modified …` exactly once, with `--task-id` + `--dispatch-id` |
| cancellation / retry | `worker-stop --dispatch <id>`, `worker-release`, `worker-retain`; retry is explicit and does **not** inherit placement: `worker-start --task <id> --retry-of <dispatchId> --worktree current --agent codex` |
| blocking question / gate | `orca orchestration ask --question … --options …`; `gate-create` / `gate-resolve` |
| account/quota-aware selection | **NOT VERIFIED.** The desktop UI shows per-account 5h/7d usage; I found no CLI verb exposing it. Treat as unavailable until probed. |

Constraints that decide the shape of the fit:

- The CLI **talks to a running Orca runtime** — "`orca status --json` should succeed first". Orca is
  GUI-first; there is no evidence here of a GUI-less orchestration runtime.
- Orchestration is **experimental** — "Enable orchestration under Settings → Experimental before
  using these commands."
- `orca orchestration reset` "affects runtime-global orchestration state."
- Retired and now no-op: `orchestration run`, `run-stop`, `coordinator-start`, `coordinator-stop`.

**Dely** = `hieuphung97/dely`, "a cross-harness delivery workflow for coding agents", shipped as a
plugin for Claude Code / Codex CLI / Grok Build / Antigravity CLI / Cursor Agent CLI (+ Kiro CLI via
`npx skills`). It explicitly **requires Orca** as "the required, constant execution plane that
launches and supervises the per-phase worker TUIs", and `dely:delivery` "preflights Orca and stops
when the CLI is missing". Dely's own ownership statement: "Orca owns dispatch… Git owns the
candidate. CI and the forge own release state. Durable facts come from those stores; Dely does not
keep a second copy."

> Disambiguation: `orcastrator.dev` ("orca/v1 · observable agent lanes"), `VirtusLab/orca`, and
> `ORCA — Open Runtime for Capable Agents` are **different projects**. They were excluded from this
> assessment; only `stablyai/orca` / onorca.dev evidence is used.

---

## Requested-shape fit

```
P2P CONTROL TOWER  →  P2P WORK FACTORY  →  executor routing
   →  optional Orca launch adapter  →  native harness
   →  RETURN_PACKET  →  P2P integration/review  →  OWNER GATE
```

This shape is supported **as long as Orca is confined to the "launch adapter" box**. The three
decisive reasons it fits:

1. `BackendAdapterIdentity` already has `harness_identity`, `model_identity`, `protocol`,
   `workspace_binding`, `environment_binding` — the exact fields an Orca adapter must report. No
   schema invention.
2. `ControlTowerReturnPacket` already has a `WORKTREE` field that today defaults to `"UNKNOWN"`.
   Orca's worktree provisioning **fills an existing slot** rather than adding one.
3. The bridge already fails closed on `UNKNOWN` and binds every receipt to
   `goal_id`/`task_id`/`request_fingerprint`, so an Orca receipt cannot bind to the wrong work item.

The three reasons it must stay **optional**:

1. Orca's runtime is a desktop GUI process. A hard dependency on it would make P2P unrunnable
   headless and would couple P2P availability to a third-party Electron app.
2. Orca orchestration is self-declared **experimental** and has already retired core verbs
   (`orchestration run`, `coordinator-start`). Its CLI surface is not stable enough to be canonical.
3. `orca orchestration reset` is runtime-global. P2P's ledger must be reconstructible without it.

---

## Dely concept classification

| # | Dely concept | Classification | Basis (verified) |
| --- | --- | --- | --- |
| 1 | Control does not implement/review | **ALREADY_CANONICAL** | Work Factory `VERIFY` is "pure fail-closed projection; never executes a protected action"; `approval-policy.json` sets `agent_may_self_approve: false`, `technical_gates_run_before_approval: true` |
| 2 | implement/review use separate workers | **ALREADY_CANONICAL** | `role_contract.py` / `role_eligibility.py` / `role_quorum.py` / `role_verifier.py` + independent role verifier; Work Factory enforces one lane per executor (`WORK_ITEM_LANE_MUST_BE_EXECUTOR`) and `WORK_ITEM_EXECUTOR_MISMATCH` |
| 3 | one remediation pass, then REPLAN | **ALREADY_EXPRESSIBLE** | Fully expressible through **existing** execution policy and retry controls — no new subsystem, primitive, or store. FW06 §10 `bounded_retry_decision(failure_class, current_retries, max_retries, task_unchanged, permissions_unchanged, target_compatible, mutation_state_known, cooldown_elapsed)` already gates every retry, `ENVELOPE_FIELDS` already carries `retry_policy`, and `NO_RETRY_CLASSES` already refuses retry for `SCOPE_DRIFT` / `QUALITY_BLOCKED` / `RETRY_EXHAUSTED` / `OWNER_GATE_REQUIRED`. "One remediation pass then REPLAN" is therefore a **bounded policy rule only**: `retry_policy.max_retries = 1`, with review-driven remediation classified so that a second pass falls into `RETRY_EXHAUSTED` and routes to replan. The one clarification worth recording is vocabulary, not machinery: a *remediation* is not a *retry*, and a *failed* worker (non-zero exit, exhausted quota, auth error) is neither |
| 4 | Git/forge owns candidate/release truth | **ALREADY_CANONICAL** | Work Factory requires explicit `BASE_SHA`/`BASE_TREE`/`CANDIDATE_SHA`/`CANDIDATE_TREE`, fails closed on `STALE_BASE` / `CANDIDATE_SHA_MUST_BE_EXPLICIT`, and always reports `PROMOTED/MERGED/DEPLOYED/RELEASED = NO`; `manual_cli_is_preferred_for_release_or_deploy: true` |
| 5 | human gates are risk-proportional | **ALREADY_CANONICAL** | `classify_task_risk` / `risk_is_rejectable` (C37); per-protected-action `required_technical_gates` + TTL in `approval-policy.json`; `subject_change_invalidates_approval` |
| 6 | harness/model/effort selected per phase | **ALREADY_EXPRESSIBLE** | Reuses existing selection/adapter metadata — **no `WorkItem` schema growth is authorized or needed.** The existing surfaces already carry every element: `SelectionCandidateEvidence.target_kind` enumerates `harness \| provider \| model \| protocol \| tool_set \| workspace \| reasoning_effort \| execution_target` with `model_id` and `reasoning_effort_classes`; `selection_request.py` defines `REASONING_EFFORT_CLASSES = (LOW, MEDIUM, HIGH, VERY_HIGH, UNKNOWN)` and `OwnerConstraints.maximum_reasoning_effort`; `live_execution.default_execution_request()` is a **closed, validated** schema (`_validate_execution_request` requires `set(value) == allowed`) that already contains `profile`, `model`, `provider`, `reasoning_effort`, `service_tier`; and `BackendAdapterIdentity` already carries `harness_identity` / `model_identity` / `protocol`. A *phase* is not a field — it is a distinct work item dispatched on its own lane with its own selection profile, which the Work Factory already enforces (one lane per executor). **Explicitly rejected: adding `MODEL`/`EFFORT`/`PHASE` to `WorkItem`.** `WorkItem` is durable identity and binding; harness/model/effort are dispatch-time selection data. Putting them in the work-item schema would duplicate the selection profile and create a second, drift-prone copy of routing truth |

**DO_NOT_DUPLICATE**

- Orca as a second orchestrator/coordinator — its `Run` / `Task` DAG / `Message` / decision-gate
  layer overlaps Control Tower + Work Factory + FW06 leases. Use `worker-start`/`worker-read`, not
  Orca's Run namespace, as the authority surface.
- Orca decision gates (`gate-create`/`gate-resolve`) as an authority — P2P Owner Gate +
  `approval-policy.json` are canonical. Map Orca `question`/`escalation` **into** a P2P approval
  request; never let the adapter resolve one.
- Dely's Control protocol, its two human gates, and its design-contract artifact — P2P already owns
  the approval boundary, gates, and intake contract (`governance/intake-contract.json`).
- Dely's release step — release/promote/merge is out of P2P scope and Owner-gated.
- Dely's handoff block as a second ReturnPacket — `ControlTowerReturnPacket` is canonical; Dely's
  `END OF HANDOFF` framing is a good *transport* check, not a second schema.
- Dely's "instrument must discriminate" discipline as new machinery — P2P already encodes it as
  `STATIC_REASONING != EXECUTION_EVIDENCE` plus `mechanical:` evidence prefixes in
  `EXECUTION_CLAIM_REQUIREMENTS`.
- Worktree provisioning as a source of truth — P2P records `WORKTREE` and owns concurrency via
  leases. Orca may *create* worktrees; it may not *own* their identity. Equally: **no new worktree
  schema, field, or store** — the existing `ControlTowerReturnPacket.worktree` slot is reused.
- `MODEL`/`EFFORT`/`PHASE` fields on `WorkItem` — rejected as duplicate routing truth already held by
  the selection profile and `BackendAdapterIdentity`.
- A second research-ledger record duplicating `RA-EXT-011`.

---

## Minimum integration seam

**One registered adapter factory. Nothing else.**

```
Arena/P2P ── WORK_ITEM (register_work_item)
          ── executor/harness/model/effort selection
          ── BackendAdapterRegistry.resolve("orca-native-harness")
          ── BackendExecutionBridge.execute(contract)
                 └─ OrcaAdapter.execute()
                      orca status --json                    → health / fail closed
                      orca orchestration task-create        → taskId
                      orca orchestration worker-start
                        --task <id> --agent <harness>
                        --model <id> --effort <lvl>
                        --worktree new-child --setup run    → dispatchId + worktree
                      orca orchestration check --wait
                        --types worker_done,escalation,question
                      orca orchestration worker-read        → transcript = EVIDENCE POINTER ONLY
                      orca orchestration worker-stop        → on timeout / cancel
          ── BackendExecutionResult (p2p-backend-execution-result/1)
          ── ControlTower.ingest_response → ControlTowerReturnPacket
          ── WorkItemHandoff.ingest_return → integration_queue → verify
          ── OWNER GATE (carried verbatim, never resolved by the adapter)
```

Concrete minimum surface (to be built in a **future, separately gated** goal — not here):

- `.p2p/system/p2p_capabilities/orca_adapter.py` implementing the existing four-method adapter
  surface: `identity()`, `health()`, `execute()`, `adapter_states()`.
  - `identity()` → `adapter_id="orca-native-harness"`, `protocol="CLI_SUPERVISED"`,
    `harness_identity=<codex|claude|cursor|…>`, `provider_identity="orca-runtime"`,
    `model_identity=<opaque id or UNKNOWN>`, `workspace_binding=<worktree path>`,
    `environment_binding=<host>`, `adapter_state="ARCHITECTURALLY_COMPATIBLE"` (see honesty note).
  - `health()` → runs `orca status --json`; unreachable runtime ⇒ `usable = False` and an honest
    `UNKNOWN` auth state; never a silent fallback to another harness.
  - `execute()` → the verbs above; maps `worker_done --outcome succeeded|failed` and
    `--files-modified` into `BackendExecutionResult`; `worker-stop` ⇒ `ERROR_TIMEOUT` /
    `ERROR_INTERRUPTED`; `question`/`escalation` ⇒ `ERROR_PERMISSION_DENIED` /
    `ERROR_CONTRACT_REJECTED`; quota/429 ⇒ `ERROR_RATE_LIMIT` (already in
    `CANONICAL_ERROR_CLASSES`). Transcripts stay evidence pointers, never authority.
- **The one and only concrete small addition — reuse an existing field, add no schema:** populate the
  `ControlTowerReturnPacket.worktree` field that already exists (`control_tower_handoff.py:877`,
  default `"UNKNOWN"`) from execution evidence / the adapter receipt, wherever the adapter can prove
  the worktree the native harness actually ran in. This is a **value** change to an existing slot, not
  a new field, not a new schema, and not a new worktree store. Where the adapter cannot prove it, the
  field stays honestly `"UNKNOWN"` — it is never synthesized.
- **No `WorkItem` schema growth.** Harness/model/effort/phase selection reuses the existing execution
  envelope / selection profile (`live_execution` `requested_execution`, `selection_request` /
  `selection_target`), `BackendAdapterIdentity` (`harness_identity` / `model_identity` / `protocol`),
  and existing routing/adapter metadata (`target_registry.json`: `adapter_id`, `scope_certifications`,
  `environment_binding`). Orca's `worker-start --agent --model --effort` is supplied from those
  existing sources at dispatch time.
- No new event type, no new store, no new ontology, no new architecture layer.

### Adapter-state honesty (binding)

Per `backend_contract.py` lines 87–114, `LIVE_CERTIFIED` is never a blanket property and
`CURRENTLY_ELIGIBLE` is never pre-declared. Because this task explicitly forbids installing Orca, an
Orca adapter today may claim **only `ARCHITECTURALLY_COMPATIBLE`**. It cannot be registered as
eligible for any mutating task without a bounded live probe.

---

## STATE_OWNERSHIP

| Owner | Owns |
| --- | --- |
| Orca (disposable) | worker pane lifecycle, worktree *creation*, runtime-local `Run`/`Task`/`Dispatch`/`Message` state, transcripts |
| P2P (durable) | `WORK_ITEM` identity + ledger events, `BASE_*`/`CANDIDATE_*` SHA+TREE, ReturnPacket binding + fingerprint, integration queue, verify projection, FW06 leases/split-brain, approval policy, Owner Gate |
| Git / forge | candidate and release truth |

Invariant: **Orca state is reconstructible-loss.** If the Orca runtime is closed, reset, or
upgraded, P2P must still reconstruct work-item state from its own ledger plus git. No P2P fact may
live only in Orca.

## AUTHORITY_OWNERSHIP

P2P, exclusively. Orca never grants permission, never widens the permission envelope, never resolves
a gate, never promotes/merges/releases, never selects the canonical quorum. This is the existing
provider boundary restated for an execution adapter: adapter output is *data or proposed evidence*.
Dely is rejected precisely because it places a second approval boundary inside the harness session.

## ARENA_TO_NATIVE_HARNESS_FLOW

1. Arena/P2P registers a `WORK_ITEM` with explicit `PROJECT`/`WORKSTREAM`/`BASE_SHA`/`BASE_TREE`,
   `EXECUTOR` (host lane), `SCOPE`, `EXPECTED_OUTPUT`. The work-item schema is **unchanged** —
   harness/model/effort are *not* work-item fields; they are resolved at dispatch (step 3) from the
   existing selection profile and adapter identity. One phase = one work item on one lane.
2. `WorkItemHandoff.start_lane` opens the lane on that executor's existing Control Tower host lane.
3. Routing resolves an adapter by **explicit target profile only** — no provider heuristics, no
   silent fallback. If the Orca adapter is unregistered or its runtime is unreachable, the work item
   fails closed rather than switching harness.
4. `BackendExecutionBridge.execute(contract)` dispatches through `OrcaAdapter`; the Orca worker runs
   in its own worktree and reports `worker_done` once with task + dispatch IDs.
5. The adapter normalizes the receipt into `BackendExecutionResult` bound to
   `goal_id`/`task_id`/`request_fingerprint`; the bridge rejects any receipt bound elsewhere.
6. `ControlTower.ingest_response` enforces binding, idempotent replay, and stale-base reconciliation
   → `ControlTowerReturnPacket`.
7. `WorkItemHandoff.ingest_return` binds explicit candidate identity → `integration_queue` →
   `verify_integration_queue` (projection only).
8. `OWNER_GATE` is carried verbatim and resolved only by the Owner.

## CODEX_LOCAL_ROLE

The Windows Codex host stays the Owner-attended interactive lane — and, practically, the only place
`orca status --json` can succeed, since Orca's orchestration needs a running desktop runtime. It is
**not** required for this assessment and must **not** be required for P2P correctness: with the Orca
adapter unregistered, every existing suite and flow must behave exactly as it does today. The adapter
is additive and fails closed when absent.

## LOCAL_RUNTIME_VERIFICATION_REQUIRED

**YES** — before the adapter may advance past `ARCHITECTURALLY_COMPATIBLE`. Open questions that only
a live probe can answer:

1. Exact `orca status --json` shape, and whether the experimental orchestration toggle is per-user or
   per-runtime (and whether it survives upgrade).
2. Whether `--model` opaque IDs are enumerable, or must be pinned blindly.
3. Whether account/quota usage is CLI-readable at all (UI shows 5h/7d; no verb found). If not,
   quota-aware selection stays out of scope.
4. Windows behaviour: worktree paths, batch/`.cmd` harness spawn, ACL handling on userData.
5. Whether `orca orchestration check --wait` composes with P2P's foreground-bounded execution policy
   (fixed max-turns + hard OS timeout) without becoming an unbounded wait.
6. Stability risk from Orca's experimental layer and its retired verbs.

---

## Return

```
FRESH_MAIN_SHA=1c9eea39ce6aa0b721d67fa6b7130918357eea4d
FRESH_MAIN_TREE=0fab3c59bd34094219693ca8ac5e7e80e2200723

ORCA_AS_EXECUTION_ADAPTER_FIT=FIT_CONDITIONAL_OPTIONAL_ADAPTER
  - Fits beneath the canonical Work Factory with no new orchestrator/ontology/store.
  - Honest adapter state today: ARCHITECTURALLY_COMPATIBLE only.
  - Constraints: GUI-runtime-bound CLI; orchestration is EXPERIMENTAL; reset is runtime-global.
  - Provides: harness launch, model/harness/effort selection, worktree isolation, run status,
    worker_done result capture, stop/retry, blocking question escalation.
  - Does NOT verifiably provide: account/quota-aware selection (no CLI verb found).

ORCA_OPTIONAL_ONLY=YES
  Orca is an optional execution adapter and never the required execution plane. P2P must remain
  fully functional with the adapter unregistered or its runtime unreachable; in that case the work
  item fails closed rather than switching harness. This is the specific property Dely inverts, and
  the reason Dely is declined.

DELY_INSTALL_RECOMMENDED=NO
  - Installs a second control protocol (own approval boundary, own two gates, own design contract,
    own release step) — all already canonical in P2P.
  - Makes Orca a REQUIRED execution plane, inverting the optional-adapter requirement.
  - Read it for concepts; 6 of 6 are already canonical or already expressible.

SUPERVISOR_ALIGNMENT=P2P_ORCA_FIT_PR29_SUPERVISOR_PASS (EXACT_REVIEWED_HEAD dbae22fe)
  PHASE_MODEL_EFFORT_CLASSIFICATION=ALREADY_EXPRESSIBLE
  REMEDIATION_POLICY_CLASSIFICATION=ALREADY_EXPRESSIBLE
  WORKTREE_FIELD_CLASSIFICATION=NECESSARY_SMALL_ADDITION

ALREADY_CANONICAL=
  1. Control does not implement/review
  2. implement/review use separate workers
  4. Git/forge owns candidate/release truth
  5. human gates are risk-proportional
  + adapter registry/bridge, receipt fingerprint binding, fail-closed UNKNOWN,
    bounded retry, leases/split-brain, Owner Gate, STATIC_REASONING != EXECUTION_EVIDENCE

ALREADY_EXPRESSIBLE=  (no new subsystem, primitive, schema, or store)
  3. one remediation pass then REPLAN -- a bounded POLICY RULE only, via existing
     FW06 bounded_retry_decision / ENVELOPE_FIELDS.retry_policy / NO_RETRY_CLASSES
     (max_retries=1; second pass -> RETRY_EXHAUSTED -> replan). Vocabulary clarification only:
     remediation != retry, and a failed worker is neither.
  6. harness/model/effort/phase selection -- reuses existing execution envelope / selection
     profile (requested_execution: profile/model/provider/reasoning_effort/service_tier;
     SelectionCandidateEvidence.target_kind harness|provider|model|protocol|tool_set|workspace|
     reasoning_effort|execution_target; REASONING_EFFORT_CLASSES;
     OwnerConstraints.maximum_reasoning_effort), BackendAdapterIdentity (harness_identity/
     model_identity/protocol), and existing routing/adapter metadata (target_registry.json).
     A phase = a distinct work item on its own lane, not a field.

USEFUL_SMALL_ADDITIONS=
  ONLY ONE, and it reuses an existing field:
  + populate the existing ControlTowerReturnPacket.worktree slot
    (control_tower_handoff.py:877, default "UNKNOWN") from execution evidence / adapter receipt
    where the adapter can prove it; otherwise it stays honestly "UNKNOWN".
    No new worktree schema, no new field, no new worktree store.
  + (deferred, probe-gated) quota-aware selection IF a CLI surface is ever found

WORKITEM_SCHEMA_GROWTH_PROPOSED=NO
  Explicitly REJECTED: adding MODEL / EFFORT / PHASE to WorkItem. WorkItem is durable identity and
  binding; harness/model/effort are dispatch-time selection data already held by the selection
  profile and BackendAdapterIdentity. Adding them would duplicate routing truth.

REMEDIATION_NEW_SUBSYSTEM_PROPOSED=NO
  Expressed only as a bounded policy rule over existing FW06 retry controls
  (bounded_retry_decision / retry_policy.max_retries / NO_RETRY_CLASSES). No new subsystem,
  primitive, schema, or store.

EXISTING_WORKTREE_FIELD_REUSE=YES
  The single small addition populates the existing ControlTowerReturnPacket.worktree slot
  (control_tower_handoff.py:877) from execution evidence/receipt where the adapter can prove it.
  No new worktree schema, field, or store.

DO_NOT_DUPLICATE=
  Orca Run/Task DAG/message layer as authority; Orca decision gates as authority;
  Dely Control protocol + two gates + design contract + release step; Dely handoff as a second
  ReturnPacket; worktree provisioning as identity truth; a new worktree schema/store;
  MODEL/EFFORT/PHASE fields on WorkItem; a second research-ledger record duplicating
  RA-EXT-011; any second orchestrator or architecture layer.

MINIMUM_INTEGRATION_SEAM=
  One BackendAdapter factory registered in a caller-supplied BackendAdapterRegistry
  ("orca-native-harness", protocol CLI_SUPERVISED) implementing identity()/health()/execute()/
  adapter_states(); dispatched via BackendExecutionBridge.execute(contract).
  Harness/model/effort/phase come from the EXISTING execution envelope / selection profile /
  BackendAdapterIdentity / routing metadata -- no WorkItem schema growth.
  The only additive change is populating the existing WORKTREE slot from the receipt.
  No new event type, no new store, no new ontology, no new layer, no AutoPilot-core change.

STATE_OWNERSHIP=Orca runtime state is disposable; P2P ledger + git are durable and reconstructible
  without Orca. No P2P fact may live only in Orca.

AUTHORITY_OWNERSHIP=P2P exclusively. Orca grants no permission, resolves no gate, widens no
  envelope, promotes/merges/releases nothing, selects no canonical quorum.

ARENA_TO_NATIVE_HARNESS_FLOW=WORK_ITEM -> start_lane -> explicit-profile adapter resolve ->
  BackendExecutionBridge.execute -> OrcaAdapter (worker-start/check/worker-read/worker-stop) ->
  BackendExecutionResult (fingerprint-bound) -> ControlTower.ingest_response -> ReturnPacket ->
  ingest_return -> integration_queue -> verify (projection only) -> OWNER_GATE (verbatim).

CODEX_LOCAL_ROLE=Owner-attended interactive lane and the only place the Orca desktop runtime can run.
  Not required for P2P correctness; adapter is additive and fails closed when absent.

LOCAL_RUNTIME_VERIFICATION_REQUIRED=YES
  6 open questions (status shape, experimental toggle scope, model-id enumerability,
  quota CLI readability, Windows path/spawn/ACL, check --wait vs bounded foreground policy).

IMPLEMENTATION_REQUIRED=NO (assessment only; seam deliberately not implemented)

RA_EXT_011_IDENTITY=UNVERIFIED (deliberately, and preserved as such)
  RA-EXT-011 "Orca AI Orchestrator" is NOT reconciled to stablyai/orca or onorca.dev. Its
  source_reference names neither, so the identity link is unproven and stays unproven. The
  research-adoption ledger is NOT modified by this workstream.

NEXT_BOUNDED_GOAL=P2P-NATIVE-HARNESS-ORCA-PROBE-01 (SEPARATE goal, not part of this assessment) —
  read-only runtime probe on the Windows Codex host: `orca status --json`,
  `orca orchestration task-list --json`, `orca worktree ps --json`.
  No mutation, no dispatch, no worktree creation. Its purpose is to answer the 6 open runtime
  questions and to establish Orca identity from observed runtime evidence rather than by editing a
  historical ledger record. Only after that probe may an adapter goal be opened.

FILES_CHANGED=docs/plans/2026-08-30-p2p-native-harness-orca-fit-01/ (2 files: assessment + status)
CODE_CHANGED=NO
LEDGER_CHANGED=NO
DIFF_CHECK=PASS — 2 markdown files only; no `.py`, no `governance/`, no `.p2p/`, no `scripts/`,
  no `tests/`; WorkItem schema untouched.
CANDIDATE_SHA=<filled after commit>
CANDIDATE_TREE=<filled after commit>
PR_NUMBER=<filled after push>
OWNER_ACTION_REQUIRED=YES — 3 decisions:
  (a) accept Orca as an OPTIONAL execution adapter (not required, not authority);
  (b) decline Dely install;
  (c) authorize the separate read-only probe goal P2P-NATIVE-HARNESS-ORCA-PROBE-01.
  No ledger change is requested here: RA-EXT-011 identity stays UNVERIFIED and
  governance/research-adoption-ledger.json is not modified.

OVER_ENGINEERING_CHECK=PASS
  - No code written; no adapter implemented; no schema invented; no WorkItem schema growth.
  - The seam already existed and was found, not built.
  - 6 of 6 Dely concepts resolved to ALREADY_CANONICAL or ALREADY_EXPRESSIBLE; exactly ONE small
    addition remains, and it reuses an existing field rather than adding one.
  - Governance ledger left untouched (Owner-gated) instead of edited for convenience;
    RA-EXT-011 deliberately left UNVERIFIED rather than reconciled by inference.
  - Quota-aware selection deferred as unverified rather than assumed.

TERMINAL_VERDICT=SUPPORTED_AS_OPTIONAL_ADAPTER — P2P Control Tower retains authority, Work Factory
  retains orchestration, BackendExecutionBridge is the integration seam, Git remains candidate truth,
  the existing ReturnPacket remains the normalized handoff, Orca is an optional execution adapter
  only, native harnesses stay native, Dely not installed, local runtime verification still required.
  Assessment complete; no implementation performed.
```

## Unchecked / honest gaps

- No Orca or Dely binary was executed. Every Orca CLI claim comes from published docs
  (`onorca.dev/docs`, `onorca.dev/docs/cli/orchestration`), not from a local run.
- `RA_EXT_011_IDENTITY = UNVERIFIED`, and it stays that way by decision. Whether `RA-EXT-011`
  "Orca AI Orchestrator" *is* `stablyai/orca` is **not provable from the record**: its
  `source_reference` names neither the repo nor the site. The concepts match, but that is an
  inference, not a verified identity link — so no reconciliation is performed and
  `governance/research-adoption-ledger.json` is not modified. Establishing identity from observed
  runtime evidence belongs to the separate `P2P-NATIVE-HARNESS-ORCA-PROBE-01` goal.
- Account/quota CLI readability was not found and is recorded as unavailable, not as absent.
- Orca headless / self-hosted-server orchestration behaviour was not examined in depth; the
  GUI-runtime dependency above is based on the orchestration doc's "the CLI talks to the running
  Orca runtime" statement.
