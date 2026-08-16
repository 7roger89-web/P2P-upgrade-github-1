# P2P Beginner UI/UX Routing and Native AESTHETICA Release Closure Benchmarks

Record a row when the corresponding slice is completed. `N/A` is valid for
Docker/browser metrics because this scope is a local routing/CLI contract and
does not change an application runtime.

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Evidence |
|---|---|---:|---:|---:|---:|---:|---|
| P0 | Anvien graph nodes | nodes | 9,123 | 9,474 | 9,474 | refreshed | `E0-P0-ANV1` |
| P0 | Anvien graph relationships | relationships | 10,424 | 10,823 | 10,823 | refreshed | `E0-P0-ANV1` |
| P0 | Canonical denominator | identities | 8 | 8 | 8 | 8 | `E0-P0-CANON1` |
| P0 | Existing native receipt evidence | receipts | 1 | 2 | 2 | preserve | `E0-P0-HOST1`; no fresh receipt in `E3-P3-FIRST1` |
| P0 | Technical gate failures before fix | failures | 2 | 2 | 2 | 0 or classified blocker | `E0-P0-GATE1`, `E2-P2-DRIFT1` |
| P1 | Beginner routing cases | cases | 0 | 40 | 40 | >=30 | `E1-P1-EVAL1` |
| P1 | Vietnamese/English case coverage | languages | 0 | 2 | 2 | both, all categories | `E1-P1-EVAL1` |
| P1 | Focused routing tests | tests | 0 | 6 | 6 PASS | all boundary assertions | `E1-P1-TEST1` |
| P1 | Trivial UI cases invoking AESTHETICA | cases | 0 | 0 | 0 | 0 | `E1-P1-TEST1` |
| P2 | Project eval suite cases | cases | 0 | 5 | 5 | >=5, schema v2 | `E2-P2-SUITE1` |
| P2 | Project eval trials per variant | trials | 0 | 0 | 0 | >=2 | `E2-P2-SUITE1` |
| P2 | Project eval gate | verdict | not_run | FAIL | FAIL | PASS | `E2-P2-SUITE1`, final technical report |
| P3 | UIUX DW gates | gates | 0 | 18/18 | 18/18 | 18/18 | `E3-P3-PKG1`, `E3-P3-LIFE1` |
| P3 | Canonical quorum | ratio | 8/8 | 8/8 | 8/8 | 8/8 | `E0-P0-CANON1` |
| P3 | Lifecycle paths passing | scenario groups | 0 | PASS | PASS | fresh + upgrades + reinstall | `E3-P3-LIFE1` |
| P3 | Exact first-try route | verdict | not_run | PARTIAL | PARTIAL | clean UIUX-first planning with no owner correction | `E3-P3-FIRST1` |
| P3 | Candidate archive | SHA-256 | n/a | `7250b586…f2437cfb` | `7250b586…f2437cfb` | immutable/hash-recorded | `E3-P3-PKG1` |
| P4 | Full regression tests | tests | 0 | 64/64 | 64/64 | no new failures | `E4-P4-REG1` |
| P4 | Supervisor verdict | verdict | not_run | REJECT | REJECT | PASS or precise BLOCKED/REJECT | `E4-P4-SUP1` |

## Non-benchmarkable notes

- Intent precedence, source-of-truth selection, official receipt authority,
  and protected-scope decisions are qualitative evidence.
- No Git commit count can be measured in this checkout because `.git` is not
  present; the final report must say so explicitly.
- No package is promoted or published by this plan.
