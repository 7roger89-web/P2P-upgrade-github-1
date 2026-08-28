# P2P-VISUAL-01B Benchmark Record

## Measurement policy

Only measured values are recorded. Estimates, stale reports, and synthetic values are not performance evidence. This task is primarily a bounded capability integration; benchmarkable metrics are inventory counts, graph capacity, disk impact, and any measured package/runtime boundary. Test duration is validation evidence, not a product benchmark.

## Baseline measurements

| ID | Metric | Measurement | Command/source | Status |
|---|---|---:|---|---|
| B0-REG | Existing registry capability count | 15 | JSON parse in clean base | measured |
| B0-CANON | Existing canonical identity count | 8 | JSON/model validation | measured |
| B0-QUORUM | Existing quorum denominator | 8/8 | foundation contract | measured |
| B0-ANV-NODES | Graph nodes after refresh | 40727 | `anvien analyze --force` | measured |
| B0-ANV-RELS | Graph relationships after refresh | 47091 | `anvien analyze --force` | measured |
| B0-ANV-SCAN | Files scanned | 975 | `anvien analyze --force` | measured |
| B0-DISK | Free D: space before execution | 9380552704 bytes | `Get-PSDrive D` | measured |

## Candidate measurements

| ID | Metric | Measurement | Command/source | Status |
|---|---|---:|---|---|
| B1-SNAPSHOT-FILES | Allowlisted vendored files | 5 | exact inventory | measured |
| B1-SNAPSHOT-BYTES | Allowlisted snapshot bytes | 32877 | filesystem byte sum | measured |
| B1-REG | Candidate registry capability count | 16 | JSON parse | measured |
| B1-CANON | Candidate canonical identity count | 8 | JSON/model validation | measured |
| B1-QUORUM | Candidate quorum denominator | 8/8 | foundation validation | measured |
| B1-ANV-NODES | Graph nodes after candidate refresh | 41004 | `anvien analyze --force` | measured |
| B1-ANV-RELS | Graph relationships after candidate refresh | 47380 | `anvien analyze --force` | measured |
| B1-DISK | Free D: space after cleanup | TBD | `Get-PSDrive D` | pending |
| B1-SPACE-FREED | Actual net space delta | TBD | before/after byte subtraction | pending |

## Interpretation rules

- A registry count of 16 is an inventory result only; it is not a live activation claim.
- The PNG is excluded, so its bytes must not appear in the candidate runtime snapshot total.
- Candidate graph counts can change because the plan, tests, and reports are new files; that change is recorded, not treated as a product-performance improvement.
- Negative `B1-SPACE-FREED` is possible because the candidate clone and evidence are retained; report the measured delta honestly.
