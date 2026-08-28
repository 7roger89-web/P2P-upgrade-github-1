# Notes and Decisions Log — 2026-08-28

## P2P-EFF01 — Execution Efficiency Canonicalization

- Authority: live `origin/main` at
  `23076954e89dec58dbcf0f14bdce15843226acbc`; implementation is isolated on
  `codex/p2p-eff01-execution-efficiency`.
- Decision: extend the existing C18 `orchestration_policy.py` root with
  material-evidence lane selection and additive JIT/test/baseline/stop/safety
  projections. Do not add a router, executor, skill system, truth store, or
  provider/model resolver.
- Evidence: EFF01 A-F matrix `7/7`, AO1-AO20 `6/6`, C37 `88/88`, targeted
  context consumers `34/34`; full compile exit `0` with one unrelated existing
  warning classified as baseline.
- Boundary: candidate readiness remains distinct from Owner approval,
  promotion, deployment, live activation, and force push.
