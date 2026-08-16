# QA Report

Scope: P2P AESTHETICA — Final Behavioral Value Certification, resumed Phase 0 trust smoke
Runtime: fresh Codex app-server 0.147.0 process on Windows 10.0.19045
Browser: N/A — downstream product UI remains gated
Build evidence: no build; this was a read-only host trust recheck
Anvien evidence: prior current graph retained; no graph command was needed for this host-only recheck
No-fix boundary: QA reports only. No trust, code, profile, release, or user-project changes were made.

## Runtime Contexts

- persona: Codex coordinator
- owner/app/scope: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`
- role: host trust smoke; no child role
- shift/session/subscription: resumed Goal turn, new app-server process, no trust override
- dataset/fixture: exact project path and `.codex` layer
- locale: host default
- viewport: N/A

## Inventory Summary

- visible surfaces: 0
- interactive elements: 0
- actions: persistent config resolution and fresh `config/read`
- data/source-of-truth checks: user Codex config and app-server resolved layers
- blocked: real child, A/B, blinded review, scoring, fallback, consistency, routing, regression
- out of scope: product/browser UI and user projects
- unverified: all downstream behavior

## Coverage Verdict

- Pass: fresh P0 recheck executed
- Fail: exact project trust remains absent
- Blocked: all downstream certification
- N/A: visible UI
- 100% of declared scope: yes for the resumed P0 smoke only

## Action Ledger

| Surface | Route/flow | Control/action | Context | Expected | Actual | Verdict | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Host config | project trust resolution | read exact project key | no override | exact child trusted | exact child absent; parent trusted | Fail | E0-P0A-TRUST2 |
| App-server | `config/read` | inspect project layer | fresh process | local `.codex` active | layer disabled with same trust reason | Blocked | E0-P0A-HOST3 |
| P2P runtime | bounded child | delegate Aesthetica | exact project | real identity | not attempted by STOP RULE | Blocked | E0-P0A-GATE2 |

## Findings

### [HIGH] Persistent exact-project trust is still missing

Classification: Confirmed runtime blocker
Confidence: high
Reproducibility: repeated across fresh app-server checks
Persona/context/viewport: Codex coordinator / exact development source / N/A
Route/dialog/flow/control: app-server `config/read`
Expected: exact project key trusted and local layer active
Actual: exact key is null; only parent `d:\\ai\\p2p_dev` is trusted; host reports the project layer disabled
Repro steps: start a fresh app-server with exact `cwd`, initialize without override, request `config/read` with layers, inspect `projects` and project layer.
Evidence: E0-P0A-TRUST2, E0-P0A-HOST3
Downstream blocked scope: complete value certification
Suggested fix direction: owner persists trust for the exact folder and starts a new Codex session.

## Source-Of-Truth Checks

| Visible value/action | Runtime source/API/DB | Expected source state | Actual source state | Verdict | Evidence |
| --- | --- | --- | --- | --- | --- |
| exact project trust | app-server config projects | trusted exact key | absent | Fail | E0-P0A-TRUST2 |
| local agents | project layer | active | disabled | Blocked | E0-P0A-HOST3 |

## Console/Network/Runtime Evidence

The host response repeated the same explicit disabled reason. No child process was started and no network or product-project mutation occurred.

## Blockers And Unverified Scope

The same host trust condition persists. This is the second fresh P0 observation; it is not yet converted to Goal status `blocked` because the required three-consecutive-turn threshold has not been reached.

## Handoff

Handoff to supervisor - QA scope completed; awaiting acceptance decision.

## Final Decision

Blocked for the full certification scope; resumed P0 smoke completed without a trust change.
