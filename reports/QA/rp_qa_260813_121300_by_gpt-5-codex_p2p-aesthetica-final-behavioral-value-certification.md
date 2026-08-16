# QA Report

Scope: P2P AESTHETICA — Final Behavioral Value Certification, Phase 0 persistent-trust smoke
Runtime: Codex app-server 0.147.0 on Windows 10.0.19045, fresh app-server process
Browser: N/A — no product UI or browser flow was in scope before the trust gate
Build evidence: no build required; no production source or release artifact was changed
Anvien evidence: `anvien analyze --force --skip-git` completed for repository mapping only (`scanned=212`, `parsed_code=22`, `failed=0`)
No-fix boundary: QA reports only. No code, profile, prompt, release, or user-project fixes were made.

## Runtime Contexts

- persona: Codex coordinator / owner-authorized development workflow
- owner/app/scope: P2P development source at `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`
- role: host trust smoke; no P2P child role was executed
- shift/session/subscription: new app-server process; no session-only trust override
- dataset/fixture: exact project path and project-local `.codex` layer
- locale: host default; no user-facing UI
- viewport: N/A

## Inventory Summary

- visible surfaces: 0
- interactive elements: 0
- actions: 2 host checks (persistent config inspection, app-server config/read)
- data/source-of-truth checks: persistent `C:\Users\Admin\.codex\config.toml`, project `.codex\config.toml`, project agent profile inventory
- blocked: real child identity, A/B matrix, blinded review, value score, fallback, consistency, routing, and regressions
- out of scope: product UI, release installation, user projects, browser QA
- unverified: all downstream certification behavior by design

## Coverage Verdict

- Pass: 2/2 P0 trust checks observed and recorded
- Fail: exact persistent trust activation
- Blocked: all downstream certification flows
- N/A: visible browser/product UI
- 100% of declared scope: yes for P0 only; no claim for the full behavioral certification

## Action Ledger

| Surface | Route/flow | Control/action | Context | Expected | Actual | Verdict | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Host config | persistent project trust | read resolved project keys | exact development path | exact child path trusted | only parent `d:\\ai\\p2p_dev` is trusted | Fail | E0-P0A-TRUST1 |
| Host app-server | project config/read | start fresh process and read with exact `cwd` | no override | project `.codex` active, agents enabled | project layer present but disabled with explicit trust reason | Blocked | E0-P0A-HOST1, E0-P0A-HOST2 |
| P2P child runtime | specialist delegation | run bounded real Aesthetica child | exact project | child identity proven | not attempted after P0 failure | Blocked | E0-P0A-GATE1 |
| A/B certification | six scenarios | execute A and B | frozen context | comparable outputs | not attempted after P0 failure | Blocked | E0-P0A-GATE1 |

## Findings

### [HIGH] Exact project-local Codex layer is disabled

Classification: Confirmed runtime blocker
Confidence: high
Reproducibility: always in the fresh smoke
Persona/context/viewport: Codex coordinator / exact development source / N/A
Route/dialog/flow/control: app-server `config/read`
Expected: exact project path persistently trusted and project-local agents active
Actual: host returned `disabledReason` requiring `d:\\ai\\p2p_dev\\p2p-8.4.6-c-codex-edition-v4` to be added to `C:\\Users\\Admin\\.codex\\config.toml`
Repro steps:

1. Start `codex app-server --stdio` with the exact project as `cwd`.
2. Initialize a new session without a trust override.
3. Request `config/read` with `includeLayers=true`.
4. Observe the project layer and its explicit disabled reason.

Evidence: E0-P0A-TRUST1, E0-P0A-HOST1, E0-P0A-HOST2
Downstream blocked scope: all real Aesthetica, A/B, scoring, fallback, consistency, and regression certification
Suggested fix direction: owner persistently trusts the exact development folder in Codex and starts a new session; do not use a session-only override.

## Source-Of-Truth Checks

| Visible value/action | Runtime source/API/DB | Expected source state | Actual source state | Verdict | Evidence |
| --- | --- | --- | --- | --- | --- |
| exact trusted project | app-server-resolved `config.projects` | exact lower-case child key with trusted level | exact child key absent; parent key present | Fail | E0-P0A-TRUST1 |
| project-local agents | app-server `config/read.layers` | active project layer with agents enabled | config declares enabled, layer disabled | Blocked | E0-P0A-HOST1, E0-P0A-HOST2 |
| Aesthetica profile | project `.codex/agents` | profile discovered by active host | file exists; discovery not proven | Partial | E0-P0A-PROFILE1 |

## Console/Network/Runtime Evidence

- Runtime output was the app-server JSON-RPC response; it contained no network call by the test harness and no child execution.
- The disabled reason is direct host evidence, not an inference from source files.
- Targeted secret-pattern scan over the new reports/plan files returned no credential/key/token matches.

## Blockers And Unverified Scope

The exact project is not persistently trusted in the current host configuration. Per the Goal STOP RULE, no A/B or value certification was run. Prior HC baseline identity evidence is not reused as current-session proof for this Goal.

## Handoff

Handoff to supervisor - QA scope completed; awaiting acceptance decision.

## Final Decision

Blocked for the full certification scope; P0 trust smoke is complete and the downstream scope is intentionally blocked.
