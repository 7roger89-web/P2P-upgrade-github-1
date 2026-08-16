# QA Report - P2P Aesthetica Host Compatibility and Real Runtime Recovery

- Date: `2026-08-13`
- Scope: P2P development source, final v9 package, disposable install fixtures, and native Codex app-server probes
- QA mode: observational and behavioral validation; no user project, App Game Truyen, Logistics, v5, or verified `.6` artifact was modified
- Verdict: `PASS`

## Baseline and final subject

- Baseline: `8.4.7-C-codex.6`, `2,336,913` bytes,
  SHA-256 `b8689fb812a438f379fc1d84353f2e4e4c9c0c234c1e22539b2bc32fd15b8156`.
- Final: `8.4.7-C-codex.9`, artifact
  `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v9.zip`, `2,370,637` bytes,
  SHA-256 `d17ba240cb754d1c7349f8f6273f4785dc778e16c395bf49166e904899f84420`.
- The v5 SHA-256 remained `f88dbf706c4ac85a8aadf38960923cdc8e4ba6e415b83f3f1726692fb3ad8dda`.

## Action ledger

| Flow | Expected | Actual | Verdict |
|---|---|---|---|
| Official profile schema | Official custom-agent keys only | `name`, `description`, `developer_instructions`, `sandbox_mode="read-only"`; no host parser warnings | PASS |
| P2P classification | Supporting/optional/noncanonical | Preserved in P2P manifest; not duplicated as unknown TOML keys | PASS |
| Readiness | Profile presence must not prove execution | Fresh doctor reports Aesthetica `RESOLVED`, execution/identity false until evidence | PASS |
| Package boundary | Required runtime resources present | Package verify, package doctor, UI/UX doctor, foundation doctor all PASS | PASS |
| Fresh install | Install cleanly and doctor passes | `FRESH_INSTALL`, PowerShell doctor and all release checks PASS | PASS |
| Upgrade | Preserve existing state and evidence | Existing-project upgrade passed | PASS |
| Same-version reinstall | Idempotent and no churn | Reinstall passed with preserved state/evidence | PASS |
| UI route | UI request may route to UIUX/Aesthetica | `UI_UX`, `call_aesthetica=true`, canonical denominator unchanged | PASS |
| Backend negative route | Backend/API/database must not invoke Aesthetica | `NON_UI`, `call_aesthetica=false`, selected set empty | PASS |
| Invalid profile | Must fail closed | Legacy-shaped profile returned `PROFILE_INVALID` and no identity | PASS |
| Real child identity | Host-selected profile and child metadata required | Elevated child `Nietzsche` and unelevated child `Descartes` both reported `agent_role=p2p_aesthetica` via `thread/read` | PASS |
| Domain boundary | UI/UX-only bounded work | Accessibility recommendations only; no shell, file, network, architecture, or permission work | PASS |
| Canonical safety | Exactly eight, full quorum 8/8 | Eight identities, denominator 8, Aesthetica excluded | PASS |
| Security/redaction | No secrets, absolute paths, or private reasoning in exports | Secret scan empty; DT redaction and no-CoT tests PASS | PASS |

## Regression and negative behavior

- Full unittest suite: `50/50 PASS`.
- Release packaging/lifecycle test: `2/2 PASS`.
- Decision Trace: `DT1–DT24 PASS` (`24/24`), including temporal, supersession, contradiction, reverse lookup, valid/legacy policy references, and honest `MISSING_REFERENCE` for invalid references.
- UI/UX doctor, governance/quorum, drift, and secret scan: PASS.
- The UI/UX evaluator's DW12–DW14 failures are intentional unapproved-material-drift fixtures; positive cases and DW1–DW11/DW15–DW18 pass.
- The first `.8` lifecycle attempt exposed a stale PowerShell doctor check. That finding was fixed in `doctor.ps1`; `.8` is superseded and v9 is the tested final artifact.

## Host evidence

- `config/read` under a process/session-only exact-project trust override reported `agents.enabled=true`.
- Native `elevated` and `unelevated` used read-only sandbox policy with network disabled; no full-access or trust bypass was used.
- Unelevated child: `019ff95f-e1ad-7663-9c48-976d6be2b277`, role `p2p_aesthetica`, nickname `Descartes`.
- Elevated child: `019ff961-0871-7c11-aeef-35347d6de440`, role `p2p_aesthetica`, nickname `Nietzsche`.
- No persistent user trust configuration was edited.

## QA verdict

`PASS`. Valid host schema, package, install, routing, readiness, real identity, domain boundary, negative behavior, and governance invariants are all evidenced. Exactly one residual-risk recommendation remains: persist trust for the exact P2P development/project root before ordinary user-facing sessions if Codex has not already recorded that host decision.
