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
append-and-reconcile only and its intake rule requires an Owner-accepted direction, so the
`RA-EXT-069` append and the `RA-EXT-011` provenance reconciliation are recorded as Owner-gated next
steps rather than performed here.

## What was verified, and how

Repository facts were read from source, not recalled:

- `backend_execution_bridge.py` docstring names "hermes-cli, manus-api, **or a future registered
  adapter**" and "nothing in the AutoPilot core changes" — the seam already exists.
- `BackendAdapterIdentity` field list read directly (`backend_contract.py`), confirming
  `harness_identity` / `model_identity` / `protocol` / `workspace_binding` / `environment_binding`
  already exist.
- `WorkItem` field list read directly (`work_item_handoff.py` lines 208–253), confirming there is
  **no** `MODEL`/`EFFORT`/`PHASE` field — the basis for classifying Dely concept 6 as an addition.
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

## Terminal state

Assessment complete. Verdict: Orca **fits as an optional execution adapter** beneath the canonical
Work Factory with no new orchestrator, ontology, or store; Dely install is **not recommended**.
No implementation performed, no promotion, no merge, no release, no Owner Gate executed.
