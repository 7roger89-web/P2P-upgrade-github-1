# Real Context-Efficiency A/B Benchmark & Quality Non-Inferiority Certification Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-plan.md`
- Evidence: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-evidence.md`
- Benchmark: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-benchmark.md`
- Actual status: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-actual-status.md`

## Evidence Rules

- Evidence is current for the development checkout and current Codex host only.
- Historical proxy evidence is referenced as historical and is never relabeled as live.
- A path without the matching SHA-256 is not release or benchmark proof.
- No token, cache, cost, provider, wall-time, child-call, or tool-call value is inferred.
- No scored trial is valid unless `runtime_task_execution=true` is directly recorded.
- No runtime source change was authorized by this audit.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GOAL1`: The attached Goal requires a real paired Codex host/provider A/B benchmark and expressly blocks fake A/B if two executable conditions are absent.
- `E0-P0A-BASE1`: Official baseline is `8.4.7-C-codex.15`, artifact `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v15.zip`, SHA-256 `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- `E0-P0A-CAND1`: Candidate is `8.4.7-C-codex.16-r2`, artifact `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v16-r2.zip`, SHA-256 `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf`.
- `E0-P0A-CANON1`: The existing benchmark suite `.p2p/evals/2026-08-14-context-efficiency-ab-proxy-suite.json` is `p2p-codex-project-eval/2`, contains exactly 12 cases C1–C12, and reuses fixture `.p2p/evals/fixtures/2026-08-14-context-efficiency-cases.json` with SHA-256 `978f29fe493be5ce6e2d2b0fbd820945880df6303fb561f74bbe36127eeac166`; suite SHA-256 is `d2f47a9447645fc8495498d031df8a20f6253319eb0ae73417327ee34e64d0d3`; no second suite was created.
- `E0-P0A-CONDITION1`: The canonical condition labels are preserved exactly: A=`CURRENT_15_EXECUTION_CONTRACT`; B=`CANDIDATE_CONTEXT_EFFICIENT_CONTRACT`.
- `E0-P0A-PROXY1`: Existing evidence `reports/QA/rp_qa_20260814T011703_by_gpt-5-codex_context-efficiency-ab-proxy.json` (SHA-256 `de9b33f7b5f068d57a50aa8d6f83a7f2245fe63d805509c47f49d311c4d629b4`) records 12 scenarios and 48 proxy trials with `runtime_task_execution=false`, `provider_called=false`, `child_worker_called=false`, and `quality_claim_allowed=false`; it explicitly does not establish live quality, token, cache, provider-cost, wall-time, or worker-efficiency claims. Its historical byte proxies are A total `122260`, B total `109110`, and B-minus-A `-13150` bytes; these remain deterministic serialization proxies only.
- `E0-P0A-SAFETY1`: Repository instructions confirm the eight canonical identities, denominator 8, full quorum 8/8, optional/noncanonical AESTHETICA, protected releases, and no new router/agent architecture for this foundation work.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`

- `E1-P1A-SUITE1`: The canonical suite definition, schema version, trial contract, condition labels, and fixture/evidence hashes were inspected from the current checkout.
- `E1-P1A-HELPER1`: `scripts/p2p_eval.py` exposes `run` and `record`, but `run` dispatches to a fixed local `_case_command` oracle and records subprocess/filesystem evidence; the canonical C1–C12 IDs are not implemented by that oracle. The CLI `baseline`/`p2p` values are suite labels, not live .15/.16 provider-condition selectors. Its source surface is connected to two files (`scripts/p2p_eval.py` and `tests/test_p2p_project_eval.py`) with Anvien `file-detail` relationship count 2 and a HIGH scope warning; no edit was made.
- `E1-P1A-RUNTIME1`: Current repository/runtime inspection did not identify a callable path that accepts one canonical C1–C12 task and runs it under both the official .15 and candidate .16-r2 context/execution strategies with isolated provider execution. The package inventories for .15 and .16-r2 contain the same relevant local helper/runtime entry-point families (`scripts/p2p_eval.py`, `scripts/p2p_workflow.py`, `runtime/scripts/p2p_router.py`, and UI/UX evaluators), but no condition-switching provider executor.
- `E1-P1A-HOST1`: Current host tool inventory was inspected for thread/agent/model/provider/token/telemetry authority. The host exposes bounded agent-control tools, but no per-trial condition switch or authoritative provider input/cache/output/cost telemetry. The repository's host identity hook allow-lists only lifecycle identity/model fields and deliberately discards prompt/transcript/tool/environment fields; it is not token or cost telemetry.
- `E1-P1A-GATE1`: Because both executable conditions and `runtime_task_execution=true` evidence cannot be proven, the benchmark hard stop is `BLOCKED`; no synthetic trials were run and no runtime instrumentation was added.
- `E1-P1A-RUBRIC1`: Before any aggregate result was considered, the fixed 0–4 quality rubric and the pre-registered non-inferiority margin from the plan were recorded. They remain unapplied because no real paired outputs exist.
- `E1-P1A-UNKNOWN1`: Input tokens, cached input tokens, output tokens, total tokens, provider/model calls, child-agent invocations, per-trial tool calls, file reads, compaction events, provider wall time, retries, failures, raw tool output volume, main-context growth, and authoritative cost are UNKNOWN for this Goal.
- `E1-P1A-VALIDATE1`: Fresh `python scripts/p2p_eval.py validate`, `summary`, and `gate` runs all returned `PASS` for the existing suite, with 12 completed historical pairs, 2 baseline and 2 P2P proxy trials per case, proxy means 1.0/1.0, and zero proxy regressions. These commands validate the evaluator contract only.
- `E1-P1A-GRAPH1`: Fresh `anvien analyze --force --skip-git` completed with 286 scanned files, 28 parsed code files, 0 parse failures, and a current graph. `file-detail` for `scripts/p2p_eval.py` reported 2 related files and HIGH graph scope warning; no source edit followed.
- `E1-P1A-HASH1`: Fresh SHA-256 verification matched the supplied official .15 and candidate .16-r2 artifact hashes.
- `E1-P1A-RELEASE1`: No source/runtime behavior, official .15 artifact, candidate .16-r2 artifact, user project, or release state was modified.

## Closure Evidence

- `E-CLOSE-SUP1`: Independent supervisor review passed for the bounded BLOCKED determination. Report `reports/supervisor/rp_supervisor_260814_093316_by_gpt-5-codex_real-context-efficiency-ab-quality-noninferiority.md` has SHA-256 `bd99982f8287c48290a7105ffa8910339e17447bdfbea0db02c9f697cf80f2e9`.
- `E-CLOSE-FILES1`: Goal-created audit artifacts are this plan's four ledgers and the supervisor report. Anvien's mandated validation refresh also updated generated `.anvien/graph.json`, `.anvien/meta.json`, and `.anvien/lbug`; no runtime code, test, fixture, package, or release artifact was changed.
- `E-CLOSE-STATUS1`: Final Goal status is `BLOCKED` unless fresh evidence proves both real executable conditions and live paired execution.
