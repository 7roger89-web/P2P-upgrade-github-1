# Supervisor Report: Real Context-Efficiency A/B Benchmark Eligibility

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260814_093316_by_gpt-5-codex_real-context-efficiency-ab-quality-noninferiority.md`
- Review time: `260814 093316 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: blocked Goal evidence package for `Real Context-Efficiency A/B Benchmark & Quality Non-Inferiority Certification`
- Claim reviewed: the correct result is `BLOCKED` because the current repository/host cannot prove two genuinely executable equivalent A/B conditions with live runtime evidence; the historical proxy suite must not be treated as certification.
- Authority used: attached user Goal, repository `AGENTS.md`, current source/runtime, canonical suite, frozen fixture/evidence hashes, current host tool surface, and current governance output.
- Related artifacts: the four plan ledgers under `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/`, canonical proxy suite, historical proxy QA evidence, official .15 artifact, candidate .16-r2 artifact, and the validation-generated Anvien graph refresh (`.anvien/graph.json`, `.anvien/meta.json`, `.anvien/lbug`).

## Executive Summary

- Problem: the existing 12-scenario/48-trial evidence is contract-proxy evidence, not real Codex host/provider execution.
- Decision: PASS for the bounded supervisor claim that the Goal must stop as `BLOCKED`; no live quality or efficiency certification is accepted.
- Required outcome: preserve the current runtime and rerun only after a separately authorized observation/execution boundary can prove both conditions and `runtime_task_execution=true` without materially changing behavior.

## Source-Level Clearance Notes

- `scripts/p2p_eval.py`: clear as inspect-only. Lines 550–592 define fixed local command oracles and raise when no oracle exists; the canonical C1–C12 IDs are not among those cases. Lines 634–715 execute subprocess/filesystem oracles and record local evidence, not a model/provider task. Lines 1137–1145 expose `baseline`/`p2p` labels and local-runner metadata, not .15/.16 provider switching. Anvien file-detail reports 2 related files and a HIGH scope warning; no production edit was made.
- `tests/test_p2p_project_eval.py`: clear as validation-only. It checks parser/schema/gate behavior and does not establish provider execution or token telemetry.
- `.p2p/system/scripts/p2p_host_identity_hook.py`: clear as identity-only. Its allow-list contains lifecycle/model/permission identity fields and intentionally excludes prompt, transcript, tool, environment, token, and cost data.
- `.p2p/evals/2026-08-14-context-efficiency-ab-proxy-suite.json`: clear as preserve-only canonical historical proxy contract; it explicitly records `runtime_task_execution=false` and `quality_noninferiority=UNKNOWN`.
- Release artifacts .15 and .16-r2: clear as preserve-only; their supplied SHA-256 values were independently rechecked and no artifact was modified.

## Evidence Checked

Passed:

- Fresh canonical suite `validate`, `summary`, and `gate`: `PASS`; 12 cases, 2 historical baseline proxy trials and 2 historical P2P proxy trials per case, proxy means 1.0/1.0, zero proxy regressions.
- Canonical suite source metadata: A=`CURRENT_15_EXECUTION_CONTRACT`; B=`CANDIDATE_CONTEXT_EFFICIENT_CONTRACT`; design method=`frozen_synthetic_contract_proxy`.
- Historical QA evidence: `runtime_task_executed=false`, `provider_called=false`, `child_worker_called=false`, `quality_claim_allowed=false`; this directly supports the blocker rather than live certification.
- Fresh Anvien graph refresh and file-detail inspection: graph current; `scripts/p2p_eval.py` related-file count 2; HIGH is a blast-radius warning only and no edit was attempted.
- Fresh official artifact checksums: .15=`af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`; .16-r2=`410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf`.
- Fresh governance validation: canonical count 8, denominator 8, full quorum 8/8, AESTHETICA excluded from denominator.
- Fresh secret scan of the new audit artifacts: `PASS`, no findings.
- The broad source-tree secret scan was attempted but timed out; it is not used as evidence. The targeted audit-artifact scan is the only security scan claimed here.
- Fresh Git check: no usable Git metadata; full working-state semantics are `NOT_APPLICABLE`, not invented.

Failed:

- The required live A/B eligibility gate is not satisfied: no callable paired provider executor, no `runtime_task_execution=true` evidence, and no authoritative per-trial provider token/cache/cost telemetry are available. This is the reason for the Goal `BLOCKED` state.

Not run:

- No real C1–C12 provider trials, blinded output review, quality aggregate, non-inferiority calculation, or live efficiency comparison. Running them without the condition gate would violate the attached Goal.
- Full source regression suite and release lifecycle tests. No runtime/package source changed in this Goal, so these are not evidence for or against the blocked conclusion.

## Invariant Closure

- affected invariant: benchmark validity, evidence honesty, source-of-truth preservation, permission boundaries, and canonical quorum safety.
- sibling surfaces checked: canonical suite/fixture/evidence, evaluation helper, helper tests, host identity hook, package entry-point inventory, governance validator, candidate hashes, and audit artifacts.
- residual unverified same-invariant surfaces: live provider execution and host telemetry remain intentionally unverified because the required executor/authority is absent; this is the explicit blocker, not an unreported assumption.

## Overall Evaluation

The audit package is acceptable as an honest blocked result. The existing evaluator contract is valid and useful for proxy structure, but it cannot answer the requested quality or efficiency questions. The evidence does not overclaim, does not invent telemetry, does not create a second benchmark or memory source, does not expand permissions, and does not modify runtime or release artifacts. `PASS` here approves the blocker determination and evidence discipline; it does not certify Condition B or promote .16-r2.
