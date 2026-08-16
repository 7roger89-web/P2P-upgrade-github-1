# P2P Aesthetica — Real Runtime Identity Certification Evidence Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-actual-status.md`

## Evidence Rules

The evidence ledger records observable facts, commands, safe outputs, failures, and final closure. It never treats prompt wording as profile provenance and never stores private chain-of-thought, credentials, or unnecessary local paths.

### Evidence ID Naming

Use stable IDs in the form `E<phase>-<item>-<kind><n>`, where the phase matches the plan phase and the item matches its checklist item. Exact IDs, not broad section labels, are referenced by actual status and benchmark ledgers.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1` — Source profile exists at the repository-relative path `.codex/agents/p2p-aesthetica.toml`; safe fields show `name = p2p_aesthetica`, `read_only = true`, classification `SUPPORTING / OPTIONAL DOMAIN SPECIALIST`, `optional_specialist = true`, and `canonical_quorum_member = false`.
- `E0-P0A-CAP1` — Capability registry entry `p2p_aesthetica` is `OPTIONAL_SPECIALIST`, `MODEL_ROUTABLE`, `CANONICAL_QUORUM_MEMBER = false`, `OPTIONAL_SPECIALIST = true`, with UI/UX authority and backend/database/API negative triggers. Its provenance marks `simulated = false` but this is a declaration, not runtime execution proof.
- `E0-P0A-PKG1` — Baseline artifact exists with size `2,336,913` bytes and SHA-256 `b8689fb812a438f379fc1d84353f2e4e4c9c0c234c1e22539b2bc32fd15b8156`.
- `E0-P0A-PKG2` — ZIP inventory contains `.codex/agents/p2p-aesthetica.toml`, `doctor.ps1`, `install.ps1`, and `runtime/p2p_capabilities/capabilities.json`.
- `E0-P0A-HOST1` — Host reports `codex-cli 0.147.0`; `codex --help` and `codex exec --help` expose a config `--profile` option but no custom-agent selector in the inspected help surface. A config profile is not accepted as custom-agent identity evidence.
- `E0-P0A-HOST2` — `codex_app__read_thread_terminal` reports no terminal session attached to this thread. Direct `/agent` interaction is therefore not yet proven available from the current host surface.
- `E0-P0A-CAN1` — Source profile inventory contains the eight canonical identities plus Aesthetica; no ninth canonical identity is introduced by the inspected metadata.

P0 decision: source/package metadata is `correct`; real host execution is `unproven` and remains the critical next check. No runtime source edit is authorized.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-PROV1` — Source and packaged Aesthetica metadata match the supplied `.6` baseline: `name=p2p_aesthetica`, supporting/optional classification, optional=true, canonical_quorum_member=false; no profile edit was made.
- `E1-P1A-PROV2` — Capability registry provenance is present and consistent: `OPTIONAL_SPECIALIST`, `MODEL_ROUTABLE`, UI/UX authority, backend/database/API negative triggers, and `simulated=false` declaration. The declaration is not treated as execution proof.
- `E1-P1A-PROV3` — Baseline recheck passed: `.6` artifact size `2,336,913` bytes and SHA-256 `b8689fb812a438f379fc1d84353f2e4e4c9c0c234c1e22539b2bc32fd15b8156`.
- `E1-P1A-PROV4` — Preserve-only boundary passed: no runtime source/profile/package file was edited for this validation Goal.
- `E1-P1A-PKG1` — Package inventory contains the profile, `doctor.ps1`, `install.ps1`, and `runtime/p2p_capabilities/capabilities.json`.
- `E1-P1A-PKG2` — Package and installed-runtime scans found zero `C:\Users\Admin` or `D:\AI\P2P_dev` developer-absolute-path references in required runtime content.
- `E1-P1A-PKG3` — Required runtime resources are present at the package boundary and are consumed by the isolated install fixture.
- `E1-P1B-INST1` — Correctly separated disposable package/project fixture `aesthetica-cert-*-20260813-03` was extracted with .NET ZIP extraction; fresh project install exited `0` and reported `FRESH_INSTALL`.
- `E1-P1B-INST2` — Installed profile inventory contains `p2p_aesthetica.toml` with supporting/optional/noncanonical fields; canonical inventory remains exactly eight.
- `E1-P1B-INST3` — After report capture, the five Goal-owned extraction/schema fixtures were moved with exact containment checks into `.tmp/aesthetica-cert-quarantine-20260813-01`; original paths were verified absent. Quarantine is recoverable.
- `E1-P1B-RES1` — Package doctor and installed-project doctor returned `RESULT: PASS`; the installed doctor emitted only a pre-existing warning that the Aesthetica file does not use the canonical `sandbox_mode` field.
- `E1-P1B-RES2` — Installed Capability Foundation doctor returned `status=PASS`; profile discovery and runtime profile resolution are true.
- `E1-P1B-RES3` — Installed readiness is deterministic but stops at `AGENT_EXECUTION_NOT_PROVEN -> IDENTITY_NOT_VERIFIED`; state is `EXECUTABLE`, not `HEALTHY`.
- `E1-P1B-RES4` — Installed package secret scan returned `status=PASS` with no findings; required resource and developer-path checks passed.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`

- `E2-P2A-HOST1` — `codex-cli 0.147.0`, CLI help, and app-server `ThreadStartParams` expose no project custom-agent selector; `--profile` is a config-profile flag and is not accepted as custom-agent identity proof.
- `E2-P2A-HOST2` — Prior app-server child metadata showed `agentRole` values but `agent_path=null`; role text is therefore not sufficient evidence that a project profile was loaded.
- `E2-P2A-HOST3` — Direct `config/read` for the target source reports the project `.codex` layer disabled because the project is not trusted; effective `agents=null`. A real ephemeral app-server probe also emitted Windows sandbox helper `Access is denied` and produced no custom-agent child provenance.
- `E2-P2A-EXEC1` — No real `p2p_aesthetica` custom-agent execution was proven. The ephemeral coordinator turn completed, but no host-selected Aesthetica profile or child execution evidence existed.
- `E2-P2A-EXEC2` — Not executable: no host-selected Aesthetica execution, so optional/noncanonical identity cannot be attributed to a real runtime response.
- `E2-P2A-EXEC3` — Not executable: the UI/UX boundary can be checked at the package router, but not certified as Aesthetica runtime behavior without P2 execution proof.
- `E2-P2A-EXEC4` — No private reasoning or credentials were retained; the ephemeral probe had no persisted rollout available for identity evidence. P2 is `BLOCKED`, not simulated.
- `E2-P2A-HOST4` — R2 host recheck: `C:\Users\Admin\.codex\config.toml` trusts the parent project key `d:\ai\p2p_dev`, but has no exact child source key for `p2p-8.4.6-c-codex-edition-v4`; app-server again reports the target `.codex` layer disabled. A session-only trust override also left the layer disabled. No persistent config was changed.
- `E2-P2A-HOST5` — R2 CLI/app surface recheck: `codex --help` confirms `--profile` layers a user config file and is not a custom-agent selector; the current app thread still has no attached terminal. The Computer Use skill was inspected and its mandatory safety boundary prohibits automating Codex Desktop/CLI, so no invalid UI workaround was used.
- `E2-P2A-EXEC5` — R2 repeated the same host capability boundary; no native selector/profile provenance became available, so no second generic execution was started and no identity was fabricated.
- `E2-P2A-HOST6` — R3 exact audit: no exact trust key exists for the source project while the parent P2P trust key exists; `codex-cli 0.147.0` exposes no custom-agent selector; the current app terminal is unattached. The `.6` artifact hash remains the verified baseline.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-POS1` — Package/installed router positive case passed with `scope=UI_UX`, `use_skill=true`, `call_aesthetica=true`, and readiness still honestly `identity_verified=false`; this is routing evidence, not real-agent identity proof. Host-runtime positive probe is blocked by P2.
- `E3-P3A-NEG1` — Package/installed router backend case passed with `scope=NON_UI`, `selected=[]`, `call_aesthetica=false`, `use_skill=false`; real-agent domain behavior remains blocked by P2.
- `E3-P3B-BEGIN1` — Existing beginner certification regression passed and installed workflow classification remained plain-language/product-focused; a fresh real Aesthetica beginner thread was not executable because P2 is blocked.
- `E3-P3B-MULTI1` — Independent multiple-thread Aesthetica identity proof is blocked by the same host boundary; no threads were simulated.
- `E3-P3B-CAN1` — Before/available source and installed snapshots list exactly the eight canonical identities.
- `E3-P3B-CAN2` — After package/router probes, no source or registry mutation occurred; canonical snapshot remains unchanged.
- `E3-P3B-CAN3` — Governance validation returned `canonical_count=8`, `canonical_denominator=8`, `full_quorum=8/8`, `optional_excluded_from_denominator=true`, and `valid=true`.

## E4 - P4 Evidence

Matching plan item(s): `P4-A`

- `E4-P4A-REG1` — Targeted regression passed: Decision Trace/governance normalization and beginner certification tests, including invalid-reference honesty and canonical safety, are `OK`.
- `E4-P4A-REG2` — Capability Foundation regression passed; all 20 foundation tests are `OK`, including UIUX/Aesthetica separation and backend negative routing.
- `E4-P4A-REG3` — Release packaging regression passed: package manifest/doctor, fresh install, upgrade, and same-version reinstall test paths are `OK` in the supported Windows fixture suite.
- `E4-P4A-REG4` — Extracted `.6` package UIUX secret scan returned `status=PASS` and `findings=[]`; no private chain-of-thought, credentials, or secrets were retained in the certification evidence.
- `E4-P4A-SCOPE1` — Release ZIP hash and source/package runtime content remained unchanged; no new release was created.
- `E4-P4A-SCOPE2` — No App Game Truyện, Logistics, or real user project was used as a write target; only disposable fixtures under the P2P development repository `.tmp` were used.
- `E4-P4A-SCOPE3` — Goal-owned temporary fixtures are quarantined after report capture; exact source paths are absent and the recoverable quarantine is recorded in the QA report.

## Closure Evidence

- Supervisor report: created after independent review; verdict `BLOCKED/REJECT` because the required real custom-agent execution proof is absent.
- Final result: `BLOCKED`; source/package/install/profile resolution pass, but AI6/AI7 cannot pass without host-selected execution.
- R2 refresh: the same trust/selector boundary was independently re-observed on the continuation turn; no persistent host configuration or runtime source was changed.
- R3 refresh: exact current-state audit reports `ExactTargetTrustPresent=false`, parent trust present, `codex-cli 0.147.0`, no custom-agent selector in CLI help, no attached app terminal, and unchanged `.6` SHA-256. The same host blocker has now repeated across three Goal turns; no runtime/config mutation was made.
- Commit hash: N/A unless a separately authorized source implementation is required; this Goal is validation-only.
- Residual-risk recommendation: exactly one — create a separate host-profile compatibility repair Goal, then rerun this certification only after the host loads a trusted project-scoped profile with the official custom-agent schema and the Windows sandbox helper is operational.
