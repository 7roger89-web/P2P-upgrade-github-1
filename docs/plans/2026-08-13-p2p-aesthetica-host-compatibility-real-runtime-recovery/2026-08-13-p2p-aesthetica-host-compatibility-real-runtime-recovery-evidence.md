# P2P Aesthetica Host Compatibility and Real Runtime Recovery Evidence Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-plan.md`
- Evidence: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-evidence.md`
- Benchmark: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-benchmark.md`
- Actual status: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-actual-status.md`

## Evidence Rules

Evidence is fresh, command-backed, and distinguishes source/profile resolution from real host execution. Historical reports are starting context only. No prompt role-play, static marker, or `simulated=false` declaration is accepted as identity proof.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SCHEMA1` — Fresh audit of all nine agent profiles found the eight canonical
  profiles using the official standalone-agent keys `name`, `description`,
  `developer_instructions`, and `sandbox_mode = "read-only"`. The optional
  `p2p_aesthetica` profile alone used legacy `instructions` and `read_only = true`,
  with no `developer_instructions` or `sandbox_mode` key.
- `E0-P0A-BASELINE1` — The preserve-only baseline artifact is
  `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v6.zip`, size `2,336,913` bytes,
  SHA-256 `b8689fb812a438f379fc1d84353f2e4e4c9c0c234c1e22539b2bc32fd15b8156`.
  It was read-only inspected and not modified.
- `E0-P0A-READINESS1` — A fresh direct call to
  `validate_optional_specialist(profile, execute_verified=False)` returned
  `status = EXECUTABLE`, `profile_resolved = true`, `identity_verified = false`,
  and `simulated = false`. This proves the P2P readiness projection treats profile
  resolution as execution proof.
- `E0-P0A-DOCTOR1` — Package doctor reported the Aesthetica profile as not read-only
  because it checks the legacy `instructions` key and found no official sandbox mode.
  Foundation doctor otherwise returned overall `PASS` while projecting Aesthetica as
  `EXECUTABLE` with no execution proof. This is a semantic false-positive, not a
  missing-profile condition.
- `E0-P0A-TRUST1` — Fresh app-server `config/read` from the exact development
  project path reported the project-local layer disabled until the exact child path
  is trusted. Effective `agents` was `null`; no user trust configuration was edited.
  The parent `D:\AI\P2P_dev` trust entry does not activate the child project layer.
- `E0-P0A-SANDBOX1` — Fresh native Windows `elevated` app-server probe started a
  read-only thread and completed a bounded read-only turn successfully. No
  `Access is denied` occurred on this coordinator path.
- `E0-P0A-SANDBOX2` — The same fresh probe under supported native `unelevated` mode
  also started and completed successfully. The historical nested-helper failure is
  therefore not yet a reproducible root cause on the simple coordinator path.
- `E0-P0A-CHILD1` — An authorized real child-thread attempt returned
  `HOST_EXECUTION_UNPROVEN` / `PROFILE_UNAVAILABLE`; no Aesthetica profile was
  observably selected or executed and no files or network were touched. This is
  evidence of absent observable profile execution, not identity proof.
- `E0-P0A-ANVIEN1` — Anvien graph refresh completed with `--skip-git`; 210 files were
  scanned, 22 parsed, and the graph was fresh. `scripts/doctor.py` file-detail and
  impact evidence were collected. Hidden managed `.codex`/`.p2p` paths were not
  indexed by Anvien, so those paths remain covered by direct source inspection and
  tests rather than graph evidence.

P0 decision: complete. Two P2P defects are proven and in scope for P1: the official
custom-agent schema mismatch and the readiness false-positive. Trust remains a host
security boundary and is not auto-edited. Native sandbox mode is not patched
speculatively; the real child path must be retested after P1.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SCHEMA2` — The current source profile `.codex/agents/p2p-aesthetica.toml`
  contains only the official host keys `name`, `description`,
  `developer_instructions`, and `sandbox_mode = "read-only"`. The former
  `profile_schema`, `classification`, `optional_specialist`, and
  `canonical_quorum_member` keys were removed because the Codex host rejected
  them. Supporting/optional/noncanonical classification remains in
  `.p2p/system/p2p.manifest.json` and `p2p_capabilities/capabilities.json`.
- `E1-P1A-HOST2` — A session-only exact-project trust override made
  `config/read` report `agents.enabled = true`; the official host parser emitted
  no unknown-field warning for the current profile. `thread/start` accepted the
  profile in both native Windows `elevated` and `unelevated` read-only modes.
  The persistent user trust file was inspected only; it was not edited.
- `E1-P1B-READINESS2` — `validate_optional_specialist(profile)` now returns
  `status = RESOLVED`, `execute_verified = false`, `health_verified = false`,
  and `identity_verified = false`. Explicit test-only execution projections
  still distinguish `EXECUTABLE` and `HEALTHY`; profile presence is not proof.
- `E1-P1-TEST2` — The Capability Foundation suite passed `25/25`, including the
  invalid legacy-shape fail-closed test. Source package doctor and foundation
  doctor checks passed for the official schema.
- `E1-P1A-REGRESSION1` — The first `.8` package lifecycle run exposed a
  remaining shipped PowerShell doctor check that still required the removed TOML
  classification keys. This was a real packaging defect, not hidden.
- `E1-P1A-FIX2` — `doctor.ps1` was corrected to validate the official TOML
  fields and read optional/noncanonical classification from the P2P manifest.
  The defect was then covered by the final fresh-install lifecycle test.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2-PACKAGE1` — Final candidate build passed with package version
  `8.4.7-C-codex.9`, artifact
  `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v9.zip`, size `2,370,637` bytes,
  SHA-256 `d17ba240cb754d1c7349f8f6273f4785dc778e16c395bf49166e904899f84420`,
  `397` content files, and `398` checksum entries. The immutable `.6` and v5
  artifacts were not written.
- `E2-P2-DOCTOR1` — Final v9 package verify, package doctor, foundation doctor,
  UI/UX doctor, governance validation/quorum, UI/UX drift, and secret scan all
  passed. Foundation doctor keeps Aesthetica at `RESOLVED` until real execution
  evidence is supplied.
- `E2-P2-LIFECYCLE1` — Release packaging tests passed `2/2`: fresh install,
  existing-project upgrade, same-version reinstall, preserved state/evidence,
  installer idempotence, and package/runtime boundaries.
- `E2-P2-REGRESSION1` — Full repository unittest suite passed `50/50`.
  Decision Trace evaluator passed `DT1–DT24` (`24/24`), including temporal,
  supersession, contradiction, reverse lookup, redaction, and canonical safety.
- `E2-P2-ROUTE1` — Final package routing selected `p2p-uiux` for a UI request,
  exposed the optional Aesthetica route without adding it to the quorum, and
  returned `call_aesthetica = false` for a backend/API/database request.
- `E2-P2-NEGATIVE1` — A deliberately legacy/invalid Aesthetica profile returned
  `PROFILE_INVALID`, `profile_resolved = false`, and `identity_verified = false`;
  no simulation or fallback identity was used.
- `E2-P2-POLICY1` — The native Decision Trace policy test passed exact logical
  references with Windows separators, legacy bare references, and an invalid
  path. Valid references resolved as `PRESENT`, legacy records remained
  readable, and the invalid reference remained `MISSING_REFERENCE`.
- `E2-P2-EVAL1` — The UI/UX evaluator's positive cases and DW1–DW11/DW15–DW18
  passed. DW12–DW14 intentionally fail on an unapproved material-drift fixture;
  this is the evaluator's required negative behavior, not a package doctor or
  lifecycle failure.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3-UNELEVATED1` — In native Windows `unelevated` read-only mode, parent
  thread `019ff95f-76f6-7552-8b68-ea0227282bf1` spawned child
  `019ff95f-e1ad-7663-9c48-976d6be2b277`. `thread/read` returned
  `source.subAgent.thread_spawn.agent_role = "p2p_aesthetica"`,
  `agentRole = "p2p_aesthetica"`, nickname `Descartes`, and a completed child
  recommendation to label the notification control and announce unread count.
  The child had no shell/file/network activity.
- `E3-P3-ELEVATED1` — In native Windows `elevated` read-only mode, parent
  thread `019ff960-b7d3-7011-81a8-fcce48f71c9c` spawned child
  `019ff961-0871-7c11-aeef-35347d6de440`. `thread/read` returned
  `source.subAgent.thread_spawn.agent_role = "p2p_aesthetica"`,
  `agentRole = "p2p_aesthetica"`, nickname `Nietzsche`, and a completed child
  recommendation to trap modal focus, provide a descriptive title, and support
  Escape. The child was read-only with network disabled.
- `E3-P3-MULTI1` — The two independent child IDs and distinct host metadata
  prove multiple-thread identity stability across both supported sandbox modes;
  the result was not inferred from prompt wording alone.
- `E3-P3-DOMAIN1` — Both child outputs stayed within accessibility/UI/UX
  reasoning. Backend routing remained negative, and the invalid-profile test
  remained fail-closed. No architecture, quorum, permissions, or project files
  were changed by a child.
- `E3-P3-TRUST1` — The runtime probes used a process/session-only exact-project
  trust override solely to diagnose the host boundary. No persistent
  `C:\Users\Admin\.codex\config.toml` edit or automatic trust action was made.

P3 decision: `PASS`. The host schema and session trust context were active, both
supported Windows modes completed real child execution, and host metadata proved
the selected `p2p_aesthetica` identity.

## Closure Evidence

- `E4-CLOSURE1` — Final source/runtime/package checks, fresh v9 artifact,
  lifecycle `2/2`, full unittest `50/50`, DT `24/24`, routing negatives,
  redaction/secret scan, and canonical governance all pass. The repository has
  no `.git` directory; Anvien's existing index was inspected and file-detail
  evidence was collected, while `detect-changes` is recorded as not applicable.
- `E4-CLOSURE2` — Supervisor review confirmed the final artifact, modified-file
  scope, identity evidence, package boundaries, and no user-project changes.

Final result: `PASS`, with exactly one residual-risk recommendation: persist
trust for the exact P2P development/project root in the Codex host before normal
user-facing sessions if the host has not already recorded that trust decision.
