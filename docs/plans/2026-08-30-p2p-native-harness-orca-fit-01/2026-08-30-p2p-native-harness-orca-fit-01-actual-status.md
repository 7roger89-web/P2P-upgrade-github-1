# Actual status — P2P-NATIVE-HARNESS-ORCA-FIT-01: bounded architecture fit assessment

## Authority and isolation

- Fresh canonical `origin/main` = `1c9eea39ce6aa0b721d67fa6b7130918357eea4d`, tree
  `0fab3c59bd34094219693ca8ac5e7e80e2200723`. `HEAD`, `origin/main`, and the merge base were all
  identical at start (`git rev-list --left-right --count origin/main...HEAD` → `0  0`). No drift.
- Work stayed on the session branch `arena/01a05381-p2p-upgrade-github-1`. One branch, one PR, no
  merge.
- No code changed. No Orca installed. No Dely installed. No Blender run. No assets generated. No
  second orchestrator created. No Windows Codex host required or contacted.

## What was produced

- `docs/plans/2026-08-30-p2p-native-harness-orca-fit-01/2026-08-30-p2p-native-harness-orca-fit-01-assessment.md`
  — the bounded fit assessment, with the requested classification and return block.
- This status file.

Documentation only. `.p2p/`, `governance/`, `source/`, `scripts/`, and `tests/` were not modified.
`governance/research-adoption-ledger.json` was deliberately **left untouched**: it is
append-and-reconcile only and its intake rule requires an Owner-accepted direction. No append was
made and no existing record was edited. `RA_EXT_011_IDENTITY` stays `UNVERIFIED` and is **not**
reconciled to `stablyai/orca` / `onorca.dev`; establishing that identity from observed runtime
evidence belongs to the separate `P2P-NATIVE-HARNESS-ORCA-PROBE-01` goal.

## What was verified, and how

Repository facts were read from source, not recalled:

- `backend_execution_bridge.py` docstring names "hermes-cli, manus-api, **or a future registered
  adapter**" and "nothing in the AutoPilot core changes" — the seam already exists.
- `BackendAdapterIdentity` field list read directly (`backend_contract.py`), confirming
  `harness_identity` / `model_identity` / `protocol` / `workspace_binding` / `environment_binding`
  already exist.
- `WorkItem` field list read directly (`work_item_handoff.py` lines 208–253), confirming there is
  **no** `MODEL`/`EFFORT`/`PHASE` field. This observation now supports the *opposite* of schema
  growth: `WorkItem` is durable identity and binding, so harness/model/effort belong at dispatch.
  Adding them would duplicate routing truth already held by the selection profile and
  `BackendAdapterIdentity`. No `WorkItem` schema growth is proposed.
- The existing selection/execution surfaces were read directly and already carry this data, which is
  what makes `PHASE_MODEL_EFFORT_CLASSIFICATION = ALREADY_EXPRESSIBLE` true rather than asserted:
  `selection_target.py:85` `target_kind` enumerates
  `harness | provider | model | protocol | tool_set | workspace | reasoning_effort | execution_target`
  with `model_id` and `reasoning_effort_classes`; `selection_request.py:36`
  `REASONING_EFFORT_CLASSES = (LOW, MEDIUM, HIGH, VERY_HIGH, UNKNOWN)` and
  `OwnerConstraints.maximum_reasoning_effort`; `live_execution.py` `default_execution_request()`
  returns a closed set including `profile`, `model`, `provider`, `reasoning_effort`, `service_tier`,
  and `_validate_execution_request` enforces `set(value) == allowed` (a closed, validated schema);
  `target_registry.json` carries `adapter_id`, `scope_certifications`, `environment_binding`.
- `fw06_operational_resilience.py` §10 read directly: `bounded_retry_decision(...)` takes
  `failure_class, current_retries, max_retries, task_unchanged, permissions_unchanged,
  target_compatible, mutation_state_known, cooldown_elapsed`, `ENVELOPE_FIELDS` includes
  `retry_policy`, and `NO_RETRY_CLASSES` already refuses retry for `SCOPE_DRIFT` / `QUALITY_BLOCKED` /
  `RETRY_EXHAUSTED` / `OWNER_GATE_REQUIRED`. This is what makes
  `REMEDIATION_POLICY_CLASSIFICATION = ALREADY_EXPRESSIBLE` true: "one remediation pass then REPLAN"
  is a bounded policy rule over existing controls, not a new primitive.
- `control_tower_handoff.py:877` `worktree: str = "UNKNOWN"` confirms P2P records a worktree binding
  but never provisions one; a grep for `worktree` across `p2p_capabilities/` returned only recording
  sites.
- `isolation.py` is `assert_isolated_target()` only — a path guard, not worktree isolation.
- `fw06_operational_resilience.py` §33–35 confirms P2P already owns leases/split-brain.
- `governance/research-adoption-ledger.json` parsed with `json`: 68 records, last `RA-EXT-068`;
  `RA-EXT-011` exists with `status: SHIPPED` and a `source_reference` that names neither
  `stablyai/orca` nor `onorca.dev`.

External facts were fetched this session from `github.com/hieuphung97/dely`,
`raw.githubusercontent.com/hieuphung97/dely/main/README.md`, `www.onorca.dev`,
`www.onorca.dev/docs`, and `www.onorca.dev/docs/cli/orchestration`. Three unrelated projects also
named "orca" (`orcastrator.dev`, `VirtusLab/orca`, `gfernandf/agent-skills`) were identified and
excluded.

## Test result

`tests.test_p2p_c34_real_backend_contract` — the suite that exercises the very registry/bridge seam
this assessment identifies — failed to import on a bare checkout with
`ModuleNotFoundError: No module named 'pytest'`. Rather than skip it, pytest was installed
(`pip install pytest --break-system-packages`, pytest 9.1.1) and the suite was run:

```
python3 -m unittest tests.test_p2p_work_item_handoff \
                    tests.test_p2p_c34_real_backend_contract \
                    tests.test_p2p_control_tower_session_handoff \
                    tests.test_p2p_parallel_execution \
                    tests.test_p2p_c35_provider_neutral_runtime

Ran 113 tests in 3.339s — OK
```

These suites execute the code paths the assessment reasons about: `BackendAdapterRegistry` /
`BackendExecutionBridge` / `HermesAdapter` / `ManusAdapter` conformance (C34), the Work Factory
`register_work_item` → `start_lane` → `ingest_return` → `integration_queue` →
`verify_integration_queue` flow, Control Tower return-packet binding, bounded parallel execution,
and provider-neutral runtime selection. All green at baseline, with no repository modification.

Note: the pytest dependency is a pre-existing environment gap in this checkout, not something this
change introduced; nothing was added to the repo to fix it.

Observed side effect, reverted: running `tests.test_p2p_c34_real_backend_contract` **appends** to the
tracked file `.p2p/system/.p2p/state/adapter_registry.json` (`git diff --stat` → 2960 insertions,
records such as `adapter_id: "adapter-fake-manus"` with `registered_at` at run time). The working
tree was restored with `git checkout --` so this change ships documentation only. Two consequences
for the seam design:

- The registry is an **append-log of registrations, not a durable authority record** — it already
  accumulates one entry per registration attempt. An Orca adapter must not be treated as certified
  merely because it appears there.
- A future adapter goal should either point the suite at a temporary registry or accept the append
  behaviour explicitly; it should not silently grow a tracked state file on every test run.

## What was not checked

- No Orca or Dely binary was executed; all Orca CLI claims come from published documentation.
- Whether `RA-EXT-011` "Orca AI Orchestrator" is the same project as `stablyai/orca` is an inference
  from matching concepts, not a verified identity link — the ledger record names neither the repo
  nor the site.
- Account/quota-aware selection: no CLI surface was found, so it is recorded as unavailable, not as
  confirmed absent.
- Orca headless / self-hosted-server orchestration was not examined in depth.

## Supervisor alignment pass (this revision)

Fix-only documentation pass on the **same** PR #29, aligning the assessment with the independent
Supervisor's final classification.

- `SUPERVISOR_VERDICT` = `P2P_ORCA_FIT_PR29_SUPERVISOR_PASS`
- `EXACT_REVIEWED_HEAD` = `dbae22fe7c4b38d5783f693bf8eaf6d554554387` — this revision is a direct
  descendant of that exact head; no rebase, no history rewrite, no new PR.
- Scope: documentation wording only. No code, no `WorkItem` schema, no ledger, no new architecture
  layer, no adapter implementation, no Orca/Dely install.

Corrections applied:

1. **`WorkItem` schema growth removed and explicitly rejected.**
   `PHASE_MODEL_EFFORT_CLASSIFICATION = ALREADY_EXPRESSIBLE`. Dely concept 6 was reclassified from
   `USEFUL_SMALL_ADDITION` to `ALREADY_EXPRESSIBLE`, and the earlier recommendation to "add three
   optional fields (`MODEL`, `EFFORT`, `PHASE`) to the work-item envelope" was deleted. The canonical
   conclusion now states that harness/model/effort/phase selection reuses the existing execution
   envelope / selection profile, `BackendAdapterIdentity`, and existing routing/adapter metadata.
   `WORKITEM_SCHEMA_GROWTH_PROPOSED = NO`.
2. **Remediation: no new subsystem or primitive.**
   `REMEDIATION_POLICY_CLASSIFICATION = ALREADY_EXPRESSIBLE`. Dely concept 3 was reclassified to
   `ALREADY_EXPRESSIBLE` and is now stated purely as a bounded policy rule over existing FW06 retry
   controls. `REMEDIATION_NEW_SUBSYSTEM_PROPOSED = NO`.
3. **Worktree retained as the single small addition, reusing an existing field.**
   `WORKTREE_FIELD_CLASSIFICATION = NECESSARY_SMALL_ADDITION`. The wording was tightened to make
   explicit that this populates the *existing* `ControlTowerReturnPacket.worktree` slot from execution
   evidence/receipt where the adapter can prove it, and that no new worktree schema, field, or store
   is added. `EXISTING_WORKTREE_FIELD_REUSE = YES`.
4. **`RA-EXT-011` identity preserved as `UNVERIFIED`.** The earlier proposal to "reconcile
   `RA-EXT-011`'s vague `source_reference`" and to append `RA-EXT-069` was removed from the next-goal
   and owner-action text. `governance/research-adoption-ledger.json` is unmodified. Identity/runtime
   probing remains the separate `P2P-NATIVE-HARNESS-ORCA-PROBE-01`.

Preserved unchanged: Orca optional adapter only; Dely install NOT recommended; P2P Control Tower
retains authority; Work Factory retains orchestration; `BackendExecutionBridge` is the integration
seam; Git remains candidate truth; the existing `ReturnPacket` remains the normalized handoff; local
runtime verification still required.

### Environment note: local clone had lost the reviewed head

At the start of this pass, local `HEAD` was `1c9eea39…` (the old `main`) and the two assessment files
existed only as **untracked** files; `git cat-file -t dbae22fe…` returned
`could not get object info`. The reviewed head existed only on the remote
(`git ls-remote origin` → `dbae22fe…  refs/heads/arena/01a05381-p2p-upgrade-github-1`, matching
PR #29's head). The files were backed up to `/tmp`, the branch was fetched and reset to `FETCH_HEAD`,
and the restored files were confirmed byte-identical to the backup (`diff -q`, matching md5
`91e964a6…` / `d309a4de…`) before any edit was made. This revision therefore sits on top of the exact
reviewed head rather than on a reconstructed copy.

## Terminal state

Assessment complete and Supervisor-aligned. Verdict: Orca **fits as an optional execution adapter**
beneath the canonical Work Factory with no new orchestrator, ontology, store, or schema growth; Dely
install is **not recommended**. No implementation performed, no promotion, no merge, no release, no
Owner Gate executed.

`SUCCESS = P2P_ORCA_FIT_PR29_SUPERVISOR_ALIGNMENT_READY`
