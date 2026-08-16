# P2P-C07 Supported Live A/B Context Boundary Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-actual-status.md`

## Evidence Rules

- Evidence is fresh, traceable, and specific to the current P2P-C07 scope.
- A test or report cannot promote a proxy to live without fresh supported host
  evidence and actual captured output.
- Exact artifact, source, fixture, context, request, and output hashes are the
  binding mechanism because the workspace has no `.git`.
- The existing Execution Ledger remains the only durable event store.
- Raw prompts, transcripts, secrets, credentials, environment dumps, and hidden
  reasoning are never persisted as evidence.
- `UNKNOWN` is a valid result for provider-owned telemetry when its authority is
  unavailable; estimates are not evidence.

Evidence IDs use the required phase/item/kind/sequence format.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`, `P1-A`

- `E0-P0A-SRC1`: Current C06 development source inspection. `.p2p/system/p2p_capabilities/context.py` contains exactly `BASELINE_COMPAT` and experimental `CONTEXT_EFFICIENT_V1`; the focused test file covers deterministic fingerprints, manifests, source bindings, stale rejection, required fields, conflicts, and 12 scenarios.
- `E0-P0A-ART1`: Official `.15` ZIP exists at `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v15.zip`; size `2,385,951`; SHA-256 `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- `E0-P0A-ART2`: Existing `.16-r2` ZIP exists at `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v16-r2.zip`; size `2,387,476`; SHA-256 `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf`.
- `E0-P0A-ART3`: Extracted package comparison under `.tmp/p2p-c07-artifact-inspection/` shows `runtime/p2p_capabilities/context.py` is 2,470 bytes with SHA-256 `34e385c3f316c53e59039b2dccf85dd851840a7ebcfc2b2578808f06a17e9e59` in both `.15` and `.16-r2`, with no C06 mode markers; `.16-r2` is pre-C06.
- `E0-P0A-HOST1`: Existing `.p2p/system/scripts/p2p_host_identity_hook.py`, `tests/test_p2p_host_identity_receipt.py`, and `.codex/config.toml` define an allow-listed official host identity receipt path backed by the existing Execution Ledger.
- `E0-P0A-HOST2`: Current Codex host exposes supported native child/subagent execution tools. The project has historical official host receipts but no fresh C07 live receipt or context-to-host adapter.
- `E0-P0A-PROXY1`: Existing local evaluator/proxy records `runtime_task_execution=false` and local serialization metrics; it is preserve-only and cannot prove live execution.
- `E0-P0A-LIVE1`: No current `execute_live_context_trial`, live output capture, stale live receipt binding, or telemetry-authority implementation exists in the development source; this is the scoped missing boundary.
- `E0-P0A-ISO1`: No C07 target uses App Game Truyện, Logistics_App_Copy, or another user production project; inspection/temp roots are under the repository `.tmp` directory.
- `E0-P0A-GOV1`: Current governance evidence preserves the canonical identities exactly as eight, denominator `8`, full quorum `8/8`, with `p2p_aesthetica` optional/noncanonical.
- `E0-P0A-GIT1`: `.git` is absent from the development workspace; no commit or Git diff evidence will be claimed.
- `E0-P0A-GRAPH1`: `anvien analyze --force --skip-git` completed successfully and rebuilt `.anvien/graph.json`; file-detail and upstream impact remain mandatory before editing existing symbols.

P0 conclusion: PASS for plan readiness; candidate creation is required; live
implementation remains pending the per-slice impact gate.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1B-PACK1`: Isolated candidate source copy under `.tmp/p2p-c07-candidate-source` was versioned only in the copy (`8.4.7-C-codex.17`) and built to `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v17.zip`. The artifact is `2,395,280` bytes with SHA-256 `50eb59740034fb724dfe23d19d7f700c8143cfb9efd07f6cdf0a33d0ed041197`; package verification reports 398 files/399 checksums PASS; extracted `runtime/p2p_capabilities/context.py` is 23,250 bytes with SHA-256 `978c859637a4f5c5ba0b2470dd5131d49dccc6215fa3b3698767bf9f9d59e3e6`, matching the current C06 source. Package doctor and governance drift both PASS. Official `.15` and `.16-r2` hashes remained unchanged.
- `E1-P1B-LIFE1`: Repository-local fixture run under `.tmp/p2p-c07-lifecycle-20260814-c/lifecycle-result.json` passed `FRESH_INSTALL` for `.17`, `UPGRADE_FROM_8.4.7-C-codex.15` to `.17`, and `SAME_VERSION_REINSTALL` for `.17`. All installer outputs contained `RESULT: PASS`; protected project state remained unchanged on upgrade/reinstall, the foundation tree remained unchanged on same-version reinstall, and post-install doctor/drift both passed.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-CONTRACT1`: New standard-library-only `.p2p/system/p2p_capabilities/live_execution.py` (`34,713` bytes; SHA-256 `bc88e7b13642c55e9ae1da9c51c3e732e41217763715445b704aee3ea62d3d94`) exposes `prepare_trial`, `finalize_trial`, and `execute_live_context_trial`. It reconstructs the actual context view, validates C06 mode/manifest/source bindings, binds the `.17` artifact and fixture, writes request/manifest/output pointers under a new repository-local `.tmp` root, and appends only the safe receipt to the existing Execution Ledger. The receipt contains requested/observed host settings, source version/artifact hash, condition/mode/fingerprint, host/session/turn fields, output hash/pointer, completion status, and authority-labeled telemetry. Anvien refreshed the `p2p-system` graph; new-file detail is parsed, and the existing `build_context_view` upstream impact is LOW/0 direct impacted nodes with analyzer resolution gaps. No existing production symbol or host hook was edited.
- `E2-P2A-TEST1`: `python -m unittest tests.test_p2p_live_execution -v` passed 6/6 tests. Coverage includes real A/B payload difference, official-ledger identity requirement and output capture, proxy false-only, unknown/stale/artifact fail-closed behavior, request/root/secret safety, stale receipt rejection, and no recursive delegation. Synthetic host receipts in this unit suite are test fixtures only and are not live proof.
- `E2-P2B-HOST1`: The supported native `multi_agent_v1__spawn_agent`/`wait_agent` surface ran one bounded `p2p_aesthetica` worker per accepted trial with no child workers or repository writes. Fresh official `codex_official_hook` `SubagentStart` receipts were found in `.p2p/state/execution-ledger.jsonl` for host IDs `019ffeb7-706e-7750-b0ca-75bd6d98e8d8`, `019ffebb-52fd-77f2-b49a-191f026dafa0`, `019ffebc-9629-7dd1-a108-cfc424f169e1`, and `019ffebe-c895-74d2-951f-5229e6639430`; each observed model was `gpt-5.6-luna` (FACT_REF: P2P-FACT-0002), observed permission was `bypassPermissions`, and provider/reasoning telemetry remained UNKNOWN. Two completed attempts (`019ffeb9-a2c1-7393-aa54-79acc1b9c630`, `019ffebd-c84a-78b0-8bb9-4544103fc860`) had no matching official receipt and were not certified.
- `E2-P2B-BIND1`: `.tmp/p2p-c07-live-20260814/paired-live-summary.json` validates four live chains: scenario -> mode -> context fingerprint -> request fingerprint -> supplied host request -> official host ID/session/turn -> output hash. All four receipts set `runtime_task_execution=true`, `execution_authority=HOST`, and `ledger_event_status=RECORDED`; all four bind source version `8.4.7-C-codex.17` and artifact SHA-256 `50eb59740034fb724dfe23d19d7f700c8143cfb9efd07f6cdf0a33d0ed041197`.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-CONTEXT1`: C1-A `BASELINE_COMPAT` fingerprint `6ded437b1b8887851a08b08e82fc1752bc1cdc9bd082433e0cd5ea90b4126e82`, request fingerprint `18991c7d4a1aa321368ced13d9fce996b4f0ebea6c478f444fe7893ac69d313b`, fixture fingerprint `edc8f7ee60ef042a0ac7298ee60e926c0ca1c24ea96f4b7902e50e7882f7c386`; C1-B `CONTEXT_EFFICIENT_V1` fingerprint `cff7951a4ac7e340d29030eab5a17ad06f53aab36ab780574024308cf85fa4af`, request fingerprint `87d3808cc2b4e0bc8ad81a66e188ec9273292c945da294c6bdc4783c43e21bef`, fixture fingerprint `74674eebfb929f36cd74f80474193f78f643874ed7cd0011bc1528de31048895`. The supplied context views differ and the requested execution fingerprints are equal within the pair.
- `E3-P3A-LIVE1`: C1-A receipt `.tmp/p2p-c07-live-20260814/trial-bfcdf53f1699452cbd286fa3b9b4d623/receipt.json`, host `019ffeb7-706e-7750-b0ca-75bd6d98e8d8`, session `019ffe87-6842-7db3-9a4d-13d33689eb0e`, turn `019ffeb7-7292-7330-b4da-c72b5ce1024f`, output SHA-256 `bde88007d13c3c7978b4552145ed199eeec4337b4937bff02a0424759403e409`, wall `105625.0 ms`; C1-B receipt `.tmp/p2p-c07-live-20260814/trial-75a9a4c7153647bcbf22263ced76e75a/receipt.json`, host `019ffebb-52fd-77f2-b49a-191f026dafa0`, session same, turn `019ffebb-535e-72b1-8516-bc9cb4d7f348`, output SHA-256 `323feae169e25a4844eec602b53d7715f717b29c7c9c4471e33a0a9f9c1cf411`, wall `51625.0 ms`; both live and ledger-recorded.
- `E3-P3B-CONTEXT1`: C7 was selected as the non-trivial existing read-only accessibility-heavy UI scenario without the C12 owner boundary. C7-A `BASELINE_COMPAT` fingerprint `461357dd257ca11cb78683897896d1394b02953c6ef7e958aef29ac2e143eb27`, request fingerprint `ec4b6192188918d2cb54025468d0827f9fe09e757e2860ca333e64ca3781a75d`, fixture fingerprint `19cfb5a4e0808436700d86ca51b83f2ff72a191652297b94e028b403978ae53b`; C7-B `CONTEXT_EFFICIENT_V1` fingerprint `3a31f24dffb3da515f5eb4faf2adc3dfb953dd81044854163b14fbc9f9413704`, request fingerprint `12a94f1ee96a7e0342e955014093088ea3d4d2f4dfb0aa5559247d2478d15a43`, fixture fingerprint `3ab65faceff368c9131dbfe469264a82e6692691b1b16498d686d4fd09ddfff6`. Requested execution fingerprints and artifact bindings are equal within the pair.
- `E3-P3B-LIVE1`: C7-A receipt `.tmp/p2p-c07-live-20260814/trial-ed3e428fe1f64053901e9780e3922f5e/receipt.json`, host `019ffebc-9629-7dd1-a108-cfc424f169e1`, turn `019ffebc-9688-71f2-9a98-f4140ccc3dc3`, output SHA-256 `4812493c94c262b6849899b9ebb43e917ca4460de9118c09897d41f12598e58a`, wall `52781.0 ms`; C7-B receipt `.tmp/p2p-c07-live-20260814/trial-0aabd5f092324e42842451b9ae2a6e5b/receipt.json`, host `019ffebe-c895-74d2-951f-5229e6639430`, turn `019ffebe-c8ee-7fc0-a473-a1c1cbd50f73`, output SHA-256 `1c75f89f99a7f29b20d8aeac0de0dfaa2b5b844b42f948e254f5276f418fc5bb`, wall `56234.0 ms`; both live and ledger-recorded. Provider tokens/cost remain `UNKNOWN` with explicit authority.

## E4 - P4 Evidence

Matching plan item(s): `P4-A`, `P4-B`

- `E4-P4A-TEST1`: Focused C07/context/identity command `python -m unittest tests.test_p2p_live_execution tests.test_p2p_context_delivery tests.test_p2p_host_identity_receipt -v` passed 28/28. Full command `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p "test_*.py"` passed 101 tests in 173.397 seconds. `scripts/p2p_decision_trace_eval.py --root .` passed DT1-DT24, 24/24; the separate repository-local-temp rerun is retained as a harness-location diagnostic because its existing CF15 test rejects a target inside the preserve-only repository root and therefore marks DT24 BLOCKED without exposing a C07 failure. Capability doctor, extracted-package doctor, candidate lifecycle, and source drift also passed.
- `E4-P4A-GATE1`: Corrected full build check created `.tmp/p2p-c07-build-check-20260814.zip` with SHA-256 `8c5cfaf60e71d16dea72e4079c4afb1ff433a65d831efba8963292d019e3337d` and 399 files/400 checksums; extracted verification and doctor PASS. Candidate `.17` remains `50eb59740034fb724dfe23d19d7f700c8143cfb9efd07f6cdf0a33d0ed041197`; official `.15` and `.16-r2` remain `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195` and `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf`. Governance drift PASS after the observed-host-model `FACT_REF`; scoped secret scans PASS; broad inherited scan only reports two documented marketplace placeholders. Independent receipt/artifact check PASS: four accepted receipts, four live ledger events, four true runtime flags, C1/C7 pair isolation, official host identity, output hashes, and UNKNOWN provider tokens/cost. Anvien detect-changes is unavailable because no `.git` exists (`Git diff failed: exit status 129`); no commit is claimed.
- `E4-P4B-REPORT1`: Coder handoff `reports/coder/rp_coder_260814_125000_by_gpt-5-codex_p2p-c07-live-ab-boundary.md`, SHA-256 `4ac29135eab04880c12e9125dbaefc170c80e0f8d33fd905a21d3a02192c0c91`, contains the invariant family map, Anvien blast radius, sibling surfaces, fallback status, gates, and residual unverified scope.
- `E4-P4B-SUP1`: Independent Supervisor report `reports/supervisor/rp_supervisor_260814_130000_by_gpt-5-codex_p2p-c07-live-ab-boundary.md`, SHA-256 `5e465033fb7dd6b2a0fc05ea0ed044abdc61b38824c8a82de5de3c624efd21d5`, contains exactly `Verdict: PASS` for the bounded C07 claim. It independently inspected the new source, immutable hashes, current live receipts/output, ledger, tests, gates, Anvien evidence, inherited limitations, and the previous blocker report.

## Closure Evidence

Closure is `PASS` for `SUPPORTED_LIVE_AB_BOUNDARY_READY`. The final
actual-status refresh, exact candidate/live receipt/output hashes, affected
regression results, no-Git detect-changes result, coder handoff, and fresh
Supervisor report are recorded above. No fabricated Git commit is claimed, and
no release or optional hardening work follows this terminal state.
