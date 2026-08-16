# QA Report - P2P Aesthetica Real Runtime Identity Certification

- Date: `2026-08-13`
- Scope: P2P development source, verified `.6` package, disposable install fixture, and Codex host capability checks
- QA mode: observational validation; no runtime/profile/package implementation changes were made
- Verdict: `BLOCKED` — source/package/install/profile resolution pass, but real custom-agent execution identity is not proven

## Runtime contexts

- Windows source tree and packaged runtime for `8.4.7-C-codex.6`
- Isolated fresh-install package/project fixture under the P2P development repository temporary area
- `codex-cli 0.147.0` CLI help and app-server protocol surface
- Direct app-server ephemeral probe using a read-only thread; no generic subagent was relabelled as Aesthetica

## Action ledger

| Flow | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|
| Source/package provenance | Aesthetica profile and capability metadata present | Profile, registry entry, package entries, and supplied SHA-256 match | PASS | `E1-P1A-PROV1..E1-P1A-PKG3` |
| Fresh `.6` install | Profile installs into clean fixture | Installer exited `0`, `FRESH_INSTALL`; package and project roots were correctly separated | PASS | `E1-P1B-INST1..E1-P1B-INST2` |
| Discovery/profile resolution | Installed runtime resolves exact profile | Foundation doctor `PASS`; `profile_resolved=true`; readiness stops at `AGENT_EXECUTION_NOT_PROVEN` | PASS, bounded | `E1-P1B-RES1..E1-P1B-RES3` |
| Real Aesthetica execution | Host selects and starts `p2p_aesthetica` | No host-selected profile provenance or Aesthetica child execution was produced | BLOCKED | `E2-P2A-HOST1..E2-P2A-EXEC4` |
| UI/UX positive route | UI/UX request may select UIUX + optional specialist | Package router returned `UI_UX`, `call_aesthetica=true`, but `identity_verified=false` remained honest | PASS for router; host runtime blocked | `E3-P3A-POS1` |
| Backend negative route | Backend/API/database request must not select Aesthetica | Package router returned `NON_UI`, `selected=[]`, `call_aesthetica=false` | PASS for router; host runtime blocked | `E3-P3A-NEG1` |
| Beginner route | Plain-language path remains safe | Existing beginner certification passed; fresh Aesthetica thread was not executable | PASS for regression; host runtime blocked | `E3-P3B-BEGIN1` |
| Multiple-thread identity | Independent real threads preserve identity | Host could not create a proven Aesthetica thread | BLOCKED | `E3-P3B-MULTI1` |
| Canonical safety | Aesthetica stays outside quorum | Exact eight, denominator `8`, full quorum `8/8`, optional excluded | PASS | `E3-P3B-CAN1..E3-P3B-CAN3` |
| Secret/redaction boundary | No secrets, CoT, or developer paths exposed | Extracted package secret scan `PASS`, zero findings; no private runtime content retained | PASS | `E4-P4A-REG4` |

## Regression

- Targeted unittest run: `32/32 PASS` covering Capability Foundation, Decision Trace/governance normalization, release packaging/install, and beginner certification.
- Release packaging test covered package verification, doctor, fresh install, upgrade, and same-version reinstall paths: `2/2 PASS` within that test class.
- Package UIUX secret scan: `status=PASS`, `findings=[]`.
- Canonical governance validation: `valid=true`, count `8`, denominator `8`, full quorum `8/8`.
- No source runtime file, `.6` release ZIP, App Game Truyện, Logistics, or real user project was modified.

## Host blocker

The host evidence is conclusive enough to block certification, not to manufacture a PASS:

1. CLI help and the generated app-server `ThreadStartParams` surface do not provide a project custom-agent selector; `--profile` is only a config-profile option.
2. Direct `config/read` for the target source showed the project `.codex` layer disabled because the project is not trusted; effective `agents=null`.
3. The Aesthetica file uses `instructions`; current official Codex custom-agent configuration requires `developer_instructions` for a custom agent profile ([official custom-agent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
4. A real ephemeral app-server probe emitted Windows sandbox helper `Access is denied` and produced no Aesthetica child/profile provenance.

These observations explain why the installed readiness state is `EXECUTABLE` in P2P metadata but not `HEALTHY` and not identity-verified. The metadata declaration `simulated=false` is not accepted as execution evidence.

## Cleanup and boundary

The Goal-owned disposable extraction/schema fixtures were moved, with exact-path containment checks, into `.tmp/aesthetica-cert-quarantine-20260813-01`; the original fixture paths were verified absent. The quarantine is recoverable and contains no user project.

## QA verdict

`BLOCKED`. AI1–AI5, AI8–AI10, AI12, AI14, AI16–AI20 are evidenced where applicable; AI6/AI7 and host-dependent AI11/AI13 cannot pass without a real host-selected `p2p_aesthetica` execution. No code change or release was created to bypass this boundary.

Exactly one residual-risk recommendation remains: create a separate host-profile compatibility repair Goal, then rerun this certification only after the host loads the trusted project-scoped profile with the official schema and the Windows sandbox helper is operational.

## R2 continuation refresh

The host was rechecked on the continuation turn. The parent `D:\AI\P2P_dev` trust entry exists, but the exact source project still has its `.codex` layer disabled; a session-only trust override did not change that result. CLI help still exposes only a user config `--profile`, and the current app thread has no attached terminal. The Computer Use skill was inspected, but its mandatory safety rules prohibit automating Codex Desktop/CLI, so no UI workaround was attempted. Verdict remains `BLOCKED` and no persistent configuration or runtime source was changed.

## R3 closure refresh

The exact current-state audit again found no trust entry for the source project, while the parent trust entry remains present. CLI help still reports only the user-config `--profile` layer; no custom-agent selector or attached app terminal is available. The `.6` artifact hash remains unchanged. This is the third consecutive confirmation of the same host impasse, so the Goal is formally `BLOCKED`.
