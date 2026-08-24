# P2P AERG Reconciliation — Benchmark Record

This task is primarily correctness/evidence work. No product performance claim is authorized. Timings below are validation telemetry only and do not prove reliability.

## Benchmark policy

- Record each benchmarkable validation slice after it completes.
- Use fresh process execution and `py -X utf8` on Windows.
- Do not treat `LOCAL_SERIALIZATION_PROXY` or test wall-clock time as provider quality, cost, or reliability evidence.
- A missing timing is `NOT_RUN`, not PASS.

## Required measurements

| Measurement ID | Scope | Command / method | Baseline | Current | Status |
| --- | --- | --- | --- | --- | --- |
| `B0-QI` | Existing QI suite | `py -X utf8 -m unittest discover -s .p2p/system/p2p_capabilities/tests -p test_quality_intelligence.py` | 0.241 s, 44 tests, 1 skip | — | BASELINE_ONLY |
| `B1-AERG` | AERG A–Z suite | Fresh-process focused unittest invocation | — | 0.039 s, 12 tests; explicit no-mutation assertions | OBSERVED |
| `B2-QI-FW01` | QI/FW01 integration | Fresh-process focused regression invocation | — | QI 0.187 s; checkpoint 90.692 s; C43+RF01 1.701 s | OBSERVED |
| `B3-FULL` | Full build/compile boundary | Repository-native full build or equivalent compile boundary | — | full hidden suite 181.319 s; compileall exit 0 | OBSERVED |
| `B4-ANVIEN` | Graph refresh | `anvien analyze --force` | — | 891 files scanned, 164 parsed, 0 failures; final `detect-changes --scope all` exit 0 | OBSERVED |

The current column must be filled with observed output after the corresponding slice; no target or expected value may be substituted.
