# QA Report

Scope: DT1-DT24 native Decision Trace behavior, material workflow capture,
beginner WHY, existing governance/quorum safety, and compatibility in the P2P
development source.
Runtime: standard-library CLI and project-local JSONL state; isolated temporary
roots for behavior tests.
Browser: N/A — no browser/UI route is in scope.
Build evidence: `python -m py_compile` passed for the native module, CLI,
evaluator, workflow, and installed wrapper. Docker/Playwright are N/A for this
CLI/state-only scope.
Anvien evidence: target is not registered; local source inspection was used as
the bounded fallback.
No-fix boundary: QA reports only. No code fixes were made in this QA lane.

## Runtime Contexts

- persona: beginner and P2P maintainer
- owner/app/scope: P2P development source only
- role: query decision WHY and inspect governed references
- shift/session/subscription: local isolated test session
- dataset/fixture: temporary synthetic project and ledger fixtures
- locale: Windows path semantics; Vietnamese WHY output tested
- viewport: N/A

## Inventory Summary

- visible surfaces: trace CLI `capture`, `query`, `export`, `doctor`,
  `materiality`; workflow report/status trace reference
- interactive elements: CLI arguments only
- actions: material capture, decision lookup, artifact lookup, JSON/Markdown
  export, doctor
- data/source-of-truth checks: existing execution ledger, Goal/status/report,
  FACT_LEDGER references, approval reference shape, canonical registry
- blocked: none in declared native-trace scope
- out of scope: release packaging/install/upgrade, graph/daemon/MCP, browser,
  Anvien, Semantica, user projects, real eight-thread quorum
- unverified: unpacked package doctor payload checks remain a known baseline
  limitation because this source tree is not a built release package

## Coverage Verdict

- Pass: DT1-DT24 `24/24`; focused trace tests `3/3`; full regression `48/48`;
  capability doctor, drift, and secret scan
- Fail: none in declared scope
- Blocked: none in declared scope
- N/A: browser, Docker, Playwright, external service, graph database, and
  unpacked release payload completeness
- 100% of declared scope: yes

## Action Ledger

| Surface | Route/flow | Control/action | Context | Expected | Actual | Verdict | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Native trace | capture -> ledger | material decision | temp project | one structured event | one event appended to existing ledger | PASS | E2-P2B-CAPTURE1 |
| Native trace | query -> WHY | decision lookup | D1/D2/D3 fixtures | source/basis/status links | deterministic reconstruction with uncertainty | PASS | E3-P3A-DT3, E3-P3A-DT14 |
| Native trace | artifact -> decision | artifact lookup | shared artifact ref | all linked decisions | D1 and D2 returned | PASS | E3-P3A-DT10 |
| Native trace | export | JSON/Markdown | fixed fixture | deterministic and safe | both exports PASS | PASS | E3-P3A-DT21, E3-P3A-DT22 |
| Governance | doctor/registry | canonical safety | source runtime | exact 8/8, Aesthetica separate | PASS; Aesthetica not simulated | PASS | E3-P3B-REG1 |
| Security | secret scan/redaction | trace output | secret fixture | no secret/private reasoning | zero scan findings; redaction PASS | PASS | E3-P3A-DT15, E3-P3B-REG1 |

## Findings

### [INFO] Unpacked package doctor payload limitation

Classification: known baseline/environment limitation  
Confidence: high  
Reproducibility: deterministic on this unpacked source tree  
Persona/context/viewport: maintainer; CLI source validation; N/A  
Route/dialog/flow/control: `scripts/doctor.py --package .`  
Expected: full package payload validation  
Actual: UIUX/foundation runtime payload paths are absent from the unpacked
development source; installed runtime capability doctor passes  
Repro steps: run `python scripts/doctor.py --package .`  
Evidence: command output; coder report; existing prior baseline limitation  
Downstream blocked scope: release/install packaging only, outside this Goal  
Suggested fix direction: separate release packaging/integration Goal; do not
modify or rebuild the verified release artifact in this Goal.

## Source-Of-Truth Checks

| Visible value/action | Runtime source/API/DB | Expected source state | Actual source state | Verdict | Evidence |
| --- | --- | --- | --- | --- | --- |
| trace event | `.p2p/state/execution-ledger.jsonl` | existing ledger is sole durable store | trace event appended; old events readable | PASS | E2-P2A-CORE1 |
| workflow trace ref | `.p2p/state/project-status.json` and report JSON/MD | ref points to actual decision ID | status/report contain the captured ID and WHY text | PASS | E2-P2B-CAPTURE1 |
| facts | `governance/fact-ledger.json` | trace references only | hash unchanged after trace capture | PASS | E3-P3A-DT4, E3-P3A-DT6 |
| canonical governance | `.p2p/system/p2p_capabilities/capabilities.json` | exact eight and 8/8 | capability doctor PASS | PASS | E3-P3B-REG1 |

## Console/Network/Runtime Evidence

- No network calls, MCP calls, external provider, daemon, or cloud memory were
  used.
- No browser console/network evidence applies.
- Secret scan returned zero findings.
- Protected runtime lock refresh returned `PASS` with 194 protected files.

## Blockers And Unverified Scope

- No blocker for the declared native Decision Trace scope.
- Anvien impact graph is unavailable for this unregistered target; local
  inspection is recorded instead.
- No real host eight-thread runtime quorum is claimed.
- Release/install/upgrade packaging remains unverified and intentionally out of
  scope.

## Final Decision

Pass for declared native Decision Trace scope only.

Handoff to supervisor - QA scope completed; awaiting acceptance decision.
