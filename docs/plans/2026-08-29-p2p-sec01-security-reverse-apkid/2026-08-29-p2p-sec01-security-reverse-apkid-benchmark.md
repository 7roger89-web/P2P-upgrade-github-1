# P2P-SEC01 Benchmark Record

## B0 — Benchmarkability decision

- This task is primarily a contract, registry, authorization, and bounded
  adapter proof. It does not change measured product performance, capacity,
  startup/package size, graph/DB throughput, or production runtime capacity.
- No benchmark run is required by the user's verification ceiling.

## B1 — Allowed measurements

| Measurement | Status | Note |
|---|---|---|
| Registry entry count / duplicate count | PASS | 39 unique entries; structural acceptance evidence, not a performance benchmark. |
| Focused test counts and exit codes | PASS | 56 focused tests PASS across SEC01/foundation/EFF01/adaptive/router modules; validation evidence, not a benchmark. |
| APKiD fixture parse result | PASS | Controlled fixture normalized five findings; deterministic adapter behavior, not a performance claim. |
| APKiD real-tool timing | NOT RUN | No installation or real smoke required. |

## B2 — Non-benchmarkable / deliberately not run

- No full security-stack benchmark.
- No MobSF, Frida, emulator, device, external-target, or broad repository
  performance run.
- No Anvien graph benchmark or graph refresh; the user explicitly prohibited
  Anvien by default for this bounded task.
