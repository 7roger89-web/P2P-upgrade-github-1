# Notes and Decisions Log — 2026-08-14

## P2P Eval Helper Boundary Alignment

- Scope: align the existing project-eval v2 helper discovery and package/runtime doctor role boundary; no context-efficiency runtime or orchestration implementation.
- Root cause: development path order selected the UI/UX-only `.p2p/system/scripts/p2p_eval.py` for a project-eval v2 `design` call; package doctor also treated a development checkout as a portable package.
- Decision: use the existing project-eval v2 CLI contract as the resolver authority and make doctor role-aware (`development`, `portable`, `installed`) without weakening strict portable checks.
- Coder report: `reports/coder/rp_coder_260814_084611_by_gpt-5-codex_p2p-eval-helper-boundary-alignment.md`
- Verification: focused tests 9/9, full unit suite 81/81, governance drift PASS, Decision Trace PASS, capability doctor PASS, changed-surface secret scans PASS, official `.15` unchanged, current `.16-r2` lifecycle A–E PASS.
- Post-review correction: installed-root helper resolution no longer falls back to an ancestor development package; the corrected candidate is immutable and separate from the first `.16` artifact.
- Release boundary: candidate `8.4.7-C-codex.16` (`v16-r2`) created but not promoted; real worker/provider A/B benchmark remains a later Goal.

## P2P-C11 Durable Task Foundation

- Scope: add the minimum Goal-scoped durable task contract, dependency/state kernel, EvidenceClaim-bound completion, capability/permission/owner gates, checkpoint/resume classification, direct dependency handoff, explicit foreground CLI, and package wiring.
- Decision: keep task state as a projection under `.p2p/state/task-state.json` and append task references to the existing `execution-ledger.jsonl`; do not create a TaskDB, second ledger, scheduler, worker pool, or new canonical agent.
- Verification: focused T1-T20 matrix 20/20, full unit suite 139/139, Decision Trace 24/24, project eval gate PASS, capability/governance/security/doctor PASS, and package lifecycle PASS.
- Candidate boundary: final new unpromoted `.tmp/p2p-c11-candidate-8.4.7-C-codex.15-r2.zip`, SHA-256 `684018d1a563e35e32eed2e06bbfee3e9625d9caef95771bf04a848fa3868926`; embedded `VERSION` remains `8.4.7-C-codex.15`. No promotion or release approval.
- Preservation: official `.15`, C10 `.20`, C09 `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`, C08 deferred, canonical 8/8, and optional/noncanonical AESTHETICA remain unchanged. Workflow helper `plan/run` timeout and no-Git detection are reported limitations.
- Reports: C11 plan/evidence/benchmark/actual-status ledgers plus coder and Supervisor re-review reports under `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/`, `reports/coder/`, and `reports/supervisor/`.
