# Controlled Execution Canonical Candidate Benchmark Ledger

Counts are measurements from candidate-03 only. Historical feature counts are
not acceptance evidence.

| Phase | Metric | Result | Evidence |
|---|---|---|---|
| P0 | canonical commit/tree | `b26189daf33afadbf6fe3eeef4f773f1373ea751` / `a8a048b8c70a49c21d7653d92835df6494be4aa0` | E0-P0A-GIT1 |
| P0 | Anvien scan/parse/relationships | 914 / 165 / 43,990; 0 parse failures | E0-P0A-ANV1 |
| P1 | C11 focused tests | 57/57 hardening/delegation/host + 6/6 checkpoint | E1-P1A-TEST1 |
| P1 | authority/lease focused tests | 54/54 foreground/adaptive/context | E1-P1B-TEST1 |
| P2 | affected suites | 223/227; four inherited failures | E2-P2A-TEST1 |
| P2 | broad suite | 223/227; no candidate-introduced failure | E2-P2A-TEST1 |
| P2 | validator observation | FAIL on candidate and clean base with identical inherited governance drift | E2-P2A-CLASS1 |
| P2 | frozen candidate tree | pending | E2-P2B-FREEZE1 |

No UI, Docker, browser, network, release, deployment, or host benchmark applies
to this local standard-library candidate.
