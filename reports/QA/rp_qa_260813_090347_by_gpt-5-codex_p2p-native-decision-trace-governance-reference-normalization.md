# QA Report - P2P Native Decision Trace Governance Reference Normalization

- Date: `2026-08-13`
- Scope: P2P development source and isolated candidate fixtures only
- Browser/UI automation: N/A; this Goal is CLI/state/package behavior
- Network/external services: not used
- QA boundary: observational verification; no code fixes were made during
  the QA pass

## Runtime contexts

- Windows development source and packaged runtime
- PowerShell fresh install, upgrade, and same-version reinstall
- WSL/POSIX query against the installed candidate
- Fresh synthetic project, copied `.5` legacy project, and isolated negative
  reference project
- Beginner WHY output, Decision Trace JSON links, ledger bytes, policy files,
  release markers, package manifests, and security scans

## Reproduction and action ledger

| Flow | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|
| `.5` exact WHY reproduction | 9 present + 2 honest missing | `approval-policy.json` and `drift-policy.json` were `MISSING_REFERENCE` | PASS | E0-P0A-REPRO1 |
| Fresh `.6` install + same workflow | valid policy refs resolve | 11 links resolved; query `PASS`; both canonical policy refs `PRESENT` | PASS | E2-P2B-FRESH1 |
| Legacy `.5` trace after upgrade | old trace readable, no rewrite | ledger hash unchanged; bare refs resolve with `NORMALIZED_REF` | PASS | E2-P2B-UPGRADE1 |
| Same-version reinstall | no state churn | ledger/policy/trace/backup snapshots unchanged | PASS | E2-P2B-REINSTALL1 |
| Windows separators | exact normalization | `governance\\drift-policy.json` resolves `PRESENT` as `governance/drift-policy.json` | PASS | E2-P2C-PORTNEG1 |
| WSL/POSIX query | location-independent logical ref | query `PASS`; both policy refs `PRESENT` | PASS | E2-P2C-PORTNEG1 |
| Deliberately invalid policy | remain visibly missing | `governance/does-not-exist.json` -> `MISSING_REFERENCE`; query `PARTIAL` | PASS | E2-P2C-PORTNEG1 |
| Temporal/supersession/contradiction | preserve existing semantics | DT9-DT11 and installed trace queries pass | PASS | E2-P2C-REGRESS1 |
| Beginner WHY | plain-language, no technical IDs required | valid links resolved; no local machine path exposed | PASS | E2-P2B-FRESH1 |

## Regression and security

- Full unittest discovery: `49/49 PASS`.
- Native DT1-DT24: `24/24 PASS`.
- Installed UIUX `DW1-DW18`: PASS.
- Capability Foundation doctor: PASS; canonical identities exact eight;
  denominator `8`; full quorum `8/8`.
- Installed Decision Trace doctor: PASS; no external dependencies.
- Package doctor, package verify, governance drift: PASS.
- Secret scan: PASS, zero findings.
- Direct ZIP boundary: 399 members, zero `.tmp`, reports, plan, `.p2p`,
  `__pycache__`, `.pyc/.pyo`, forbidden integration, or user-project members.
- Redaction and integrity checks remain PASS; no credentials, local absolute
  paths, or private chain-of-thought appear in beginner-facing output.

## Aesthetica and quorum

`p2p_aesthetica` remains `SUPPORTING / OPTIONAL DOMAIN SPECIALIST`,
`canonical_quorum_member=false`, and `simulated=false`. The capability doctor
reports profile resolution but correctly stops before execution identity proof.
No identity was fabricated.

## N/A and known boundaries

Browser, Playwright, Docker, live external provider, real host eight-thread
execution quorum, and user-project installation are N/A or out of scope. The
target has no Git metadata; Anvien analysis is the topology evidence and
commit reference is `N/A`. One and only one fresh residual-risk recommendation
is retained: verify real Aesthetica execution identity in a separate Goal when
real execution evidence exists.

## QA verdict

PASS for the declared governance-reference normalization scope. Valid
references resolve deterministically; deliberately invalid references remain
honestly missing.
