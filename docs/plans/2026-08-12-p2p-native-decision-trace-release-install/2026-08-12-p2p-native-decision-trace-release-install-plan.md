# P2P Native Decision Trace — Release / Install Integration Plan

## Metadata

- Date: `2026-08-12`
+ Status: `complete`
- Plan: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-plan.md`
- Evidence: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-evidence.md`
- Benchmark: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-benchmark.md`
- Actual status: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-actual-status.md`

## Goal

Integrate the verified native Decision Trace into the normal P2P package,
fresh install, upgrade, same-version reinstall, runtime, beginner WHY, doctor,
and release-certification lifecycle, then produce one new full P2P release
candidate without changing the verified `.4` artifact or any user project.

## Rules

- Baseline release is `8.4.7-C-codex.4`; preserve its ZIP and SHA-256 exactly.
- Derive the new release identity from the existing `codex.4` policy; do not
  invent a version from the development directory name.
- Package the verified Decision Trace runtime automatically; no separate
  registration, setup, package install, database, MCP, or provider is allowed.
- Keep the existing execution ledger as the only durable trace store and keep
  FACT_LEDGER, Live Specs, approval, trust/RAG, Goal, and quorum authority
  unchanged.
- Preserve exactly the canonical eight and denominator `8`; full quorum is
  `8/8`; Aesthetica remains optional/supporting and is never simulated.
- Keep Decision Trace infrastructure-only, not an agent or capability identity.
- Developer-only evaluator/tests/reports remain outside the shipped runtime
  unless an existing package contract explicitly requires them.
- Never modify the verified old release, v5 artifact, App Game Truyện,
  Logistics, or any real user project. All lifecycle fixtures live under
  repository-local `.tmp` and are disposable.
- No Code-Impact, Anvien, Semantica, Brigade/Tideline, graph DB, RDF, MCP,
  external dependency, specialist, UI redesign, public publication, or live
  user-home installation is in scope.
- Package PASS requires the actual packaged artifact to pass package doctor;
  the earlier unpacked-source limitation cannot be waived for the new ZIP.
- Record evidence and benchmark values after each slice. The target is not a
  Git worktree; commit evidence is `N/A` unless the repository state proves
  otherwise.
- Anvien is attempted for impact mapping; if the target remains unregistered,
  record local static/artifact/runtime inspection as the bounded fallback.

## Problem

The verified `.4` full release passes package doctor and UI/UX/Foundation
release checks but contains no Decision Trace runtime. The development source
has the native module and CLI wrapper, while the package builder's runtime
allowlist, installer copy lists, doctor checks, and release metadata do not
yet bind them. The current source lock also contains developer-only files that
the clean package intentionally excludes, so a package build fails its own
drift gate until that boundary is made explicit.

## Scope

- Inspect and preserve the existing package, installer, doctor, governance,
  runtime-lock, and project-state architecture.
- Add the Decision Trace runtime module/CLI to the full-release payload and
  expose a bounded package/installed doctor check.
- Advance only the existing P2P release revision from `.4` to `.5` and align
  source metadata, runtime manifest, release notes, and build report.
- Make PowerShell and POSIX installers provision the trace runtime in the
  normal lifecycle and record no duplicate state on same-version reinstall.
- Add a release certification harness and focused regression coverage for
  fresh install, beginner WHY, upgrade, ledger preservation, legacy history,
  post-upgrade trace, reinstall, materiality, references, relationships,
  temporal behavior, exports, redaction, integrity, UIUX/Foundation, doctor,
  drift, secrets, and package boundaries.
- Build a new full ZIP, extract it into an isolated temporary root, and run
  the actual package/install/runtime lifecycle against controlled fixtures.

## Non-Goals

- No change to native Decision Trace semantics already certified DT1–DT24.
- No historical trace backfill, second ledger, graph model, RDF export, or
  regulatory-compliance claim.
- No change to UI/UX design, routing policy, beginner discovery, Code-Impact,
  Anvien integration, or external provider seams.
- No upgrade of App Game Truyện, Logistics, or any user project.
- No mutation or replacement of `P2P-8.4.7-C-Codex-Edition-v4.zip`.
- No public publication or interactive user approval execution.

## Requirements

- New full release contains runtime Decision Trace module, CLI, workflow
  binding, metadata, and doctor recognition.
- Fresh install automatically provisions the trace runtime and supports a
  material decision plus beginner-language WHY without a Decision ID.
- Upgrade preserves old project state and old execution-ledger bytes; only a
  legitimate post-upgrade material action may append a new trace event.
- Legacy projects remain `LEGACY`/`PARTIAL`/`NO_NATIVE_TRACE` when queried;
  no historical provenance is invented.
- Same-version reinstall is idempotent, creates no duplicate runtime,
  declarations, profiles, ledger records, relationship edges, or backup churn.
- Installed runtime preserves `SUPPORTS`, `CONTRADICTS`, `UNKNOWN`,
  supersession, temporal distinction, missing-reference honesty, approval
  evidence rules, reverse artifact lookup, redaction, tamper-evident SHA-256,
  and deterministic JSON/Markdown export.
- Actual packaged artifact passes package verify, package doctor, drift,
  secret scan, capability doctor, UIUX regression, and affected full tests.
- New artifact metadata records version, absolute path, filename, size,
  content-file count, ZIP member count, and SHA-256.

## Acceptance Criteria

RI-DT1–RI-DT35 from the user Goal all pass with fresh artifact lifecycle
evidence. In particular, package/install/runtime behavior must be proven from
the new extracted ZIP, not from source tests alone. Exactly one evidence-backed
next Goal is selected from the post-certification residual-risk evidence.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: classify version authority, old artifact boundary, native trace
    state, package builder, installer, doctor, lock, and protected project
    state from current evidence.
  - Work Steps: inspect the old ZIP and extracted doctor result; inspect the
    source runtime and package allowlist; inspect both installers and doctor;
    attempt Anvien; record missing/partial/correct surfaces and downstream
    decisions in actual-status.
  - Implementation Gate: actual-status has evidence IDs, invariant-family
    map, touch modes, and a final P0 decision.
  - Acceptance: all packaging gaps are bounded, preserve-only surfaces are
    identified, and P1 work is executable without changing old release/user
    state.

### P1: Package/runtime integration

- Phase Goal: bind Decision Trace to the normal full-release payload, version
  authority, runtime manifest, doctor, and clean-package drift model.
- Phase Boundary:
  - In scope: package builder, release metadata, runtime manifest, doctor,
    drift-policy boundary, and exact runtime files.
  - Out of scope: installer execution and lifecycle certification beyond
    package-level checks.
  - Dependencies: P0-A and approved native Decision Trace SPEC.
- Phase Implementation Rule: implement P1-A, verify and refresh status, then
  P1-B; do not implement the phase as one broad edit.
- Ordered Slice List:
  - P1-A: Add Decision Trace runtime payload and doctor/manifest checks.
  - P1-B: Advance release metadata and make clean-package drift consistent.

+ [x] P1-A: Add Decision Trace runtime payload and doctor/manifest checks.
  - Goal: make the actual full package contain and recognize the native trace.
  - Scope Boundary:
    - Editable: package builder, `scripts/doctor.py`, runtime manifest, and
      package-facing CLI/runtime lists.
    - Inspect-only: native trace semantics, existing UIUX/Foundation runtime,
      FACT_LEDGER, and execution-ledger authority.
    - Preserve-only: old ZIP, v5 artifact, user/project state.
    - Out of scope: evaluator shipping, UI redesign, new capability identity.
  - Non-Goals: no second runtime store or trace schema.
  - Pre-flight Questions:
    - Data source: `.p2p/system/p2p_capabilities/decision_trace.py`, existing
      CLI wrapper, package allowlist, runtime manifest.
    - Display permission: package/installed doctor output only.
    - DB read flow: N/A; file payload and JSONL runtime state.
    - DB write flow: N/A for package build; installed trace writes only the
      existing project execution ledger through the certified runtime.
    - Render location: `runtime/` in the ZIP and `.p2p/system/` after install.
    - UI behavior flow: N/A; CLI/state-only.
    - Docker runtime: N/A; no service/container.
    - Playwright target: N/A; no browser surface.
    - Behavior test: package member, doctor, manifest, and installed runtime
      smoke checks.
    - Cleanup/quarantine: staging and extraction under `.tmp` only.
    - External side effects: none; no publication.
    - N/A notes: Anvien target is not registered; local inspection is recorded.
  - Work Steps:
    1. Add runtime module/CLI to package builder and runtime manifest metadata;
       add package and installed doctor checks.
       - UI flow check: N/A.
       - DB/data flow check: verify only the existing JSONL path is referenced.
       - Render location check: assert `runtime/p2p_capabilities/decision_trace.py`
         and `runtime/scripts/p2p_decision_trace.py` are present.
       - Mini QA: compile and run package-payload smoke on a temporary stage.
       - Evidence target: `E1-P1A-PAYLOAD1`.
    2. Verify the old `.4` artifact is untouched and the package doctor check
       fails closed when the trace payload is removed from a synthetic stage.
       - UI flow check: N/A.
       - DB/data flow check: no project state is touched.
       - Render location check: doctor reports a named Decision Trace payload
         failure, not a generic success.
       - Mini QA: run positive and negative package doctor cases.
       - Evidence target: `E1-P1A-DOCTOR1`.
  - Implementation Gate:
    - Anvien impact/file-detail was attempted and unavailable for this target;
      source sibling map is recorded in P0 evidence.
    - Existing native trace DT1–DT24 PASS remains the behavior authority.
  - Acceptance:
    - Source: runtime and package checks are explicit and narrow.
    - Runtime/UI: actual staged payload is discoverable by doctor.
    - DB/data: no second ledger or authority path is introduced.
    - Behavior test: positive and negative package payload checks PASS.
    - Cleanup/quarantine: only `.tmp` fixtures are written.
    - Evidence IDs: `E1-P1A-PAYLOAD1`, `E1-P1A-DOCTOR1`.
    - Actual-status rows refreshed: package/runtime/doctor.
  - Evidence Targets: source-level file inventory, package doctor output,
    manifest metadata, protected old-artifact hash.
  - Actual-status Update: `missing -> bound-correct` for package Decision Trace.
  - Commit Boundary: repository is not Git; record `N/A` and file hashes.

+ [x] P1-B: Advance release metadata and make clean-package drift consistent.
  - Goal: derive the new `.5` release and ensure the package builder can pass
    its own drift gate while excluding developer-only evaluator material.
  - Scope Boundary:
    - Editable: `VERSION`, package/runtime manifests, build report, release
      notes/guides, package allowlist, drift policy.
    - Inspect-only: baseline source inventory and old artifact.
    - Preserve-only: native Decision Trace code semantics and UIUX behavior.
    - Out of scope: installer state writes.
  - Non-Goals: no new version scheme or baseline rewrite.
  - Pre-flight Questions:
    - Data source: current `.4` metadata and previous `.4` artifact.
    - Display permission: release metadata and beginner docs.
    - DB read/write flow: N/A.
    - Render location: release root and `runtime/p2p.manifest.json`.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: metadata consistency, lock, package build.
    - Cleanup/quarantine: generated ZIP only at explicit parent path.
    - External side effects: no publication.
    - N/A notes: no user approval action is executed.
  - Work Steps:
    1. Advance `.4` to `.5` in canonical metadata and add Decision Trace
       runtime/provider information without adding a capability/agent.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: package/runtime manifest agrees with VERSION.
       - Mini QA: parse all metadata and run drift.
       - Evidence target: `E1-P1B-META1`.
    2. Exclude only developer-only files from package runtime lock coverage,
       build the candidate ZIP, and run package verify/doctor/drift.
       - UI flow check: N/A.
       - DB/data flow check: trace runtime remains in the lock/package.
       - Render location check: ZIP has no reports/plans/temp/project state.
       - Mini QA: archive inventory and SHA-256 checks.
       - Evidence target: `E1-P1B-PACKAGE1`.
  - Implementation Gate:
    - P1-A is PASS and old artifact SHA is unchanged.
  - Acceptance:
    - Source: all version authorities agree on `.5`.
    - Runtime/UI: actual package doctor/drift PASS.
    - DB/data: no project state in ZIP.
    - Behavior test: package build and artifact integrity PASS.
    - Cleanup/quarantine: developer-only evaluator/tests/reports excluded.
    - Evidence IDs: `E1-P1B-META1`, `E1-P1B-PACKAGE1`.
    - Actual-status rows refreshed: release identity and artifact.
  - Evidence Targets: new ZIP path/hash/size/counts, old ZIP hash, package
    manifest/checksum, doctor/drift output.
  - Actual-status Update: `partial -> correct` for release metadata/package.
  - Commit Boundary: candidate artifact is a protected local output; no public
    release approval or Git commit is performed.

### P2: Installer and lifecycle certification

- Phase Goal: provision and certify Decision Trace across fresh install,
  upgrade, post-upgrade activity, and same-version reinstall.
- Phase Boundary:
  - In scope: PowerShell/POSIX installer runtime copy lists, release-aware
    marker behavior, isolated lifecycle harness and controlled fixtures.
  - Out of scope: real user home, application project, public publication.
  - Dependencies: P1 candidate artifact and package doctor PASS.
- Phase Implementation Rule: implement P2-A, verify fresh; then P2-B upgrade/
  reinstall; then P2-C trace behavior matrix.
- Ordered Slice List:
  - P2-A: Add installer provisioning and idempotence assertions.
  - P2-B: Add fresh/upgrade/reinstall fixture harness.
  - P2-C: Add installed Decision Trace behavioral certification.

+ [x] P2-A: Add installer provisioning and idempotence assertions.
  - Goal: normal installers provision the trace runtime automatically without
    a separate setup step or duplicate declarations.
  - Scope Boundary:
    - Editable: `install.ps1`, `install.sh`, focused release test harness.
    - Inspect-only: project state schemas and existing backup/marker semantics.
    - Preserve-only: FACT/Live/eval/approval/Goal/status/CAPSULE/ledger/user files.
    - Out of scope: live user-home installation.
  - Non-Goals: no migration system or destructive reset.
  - Pre-flight Questions:
    - Data source: ZIP runtime payload and VERSION/release marker.
    - Display permission: installer class and doctor output.
    - DB read flow: N/A; filesystem state.
    - DB write flow: `.p2p/system` runtime only; project state protected.
    - Render location: installed runtime and release marker.
    - UI behavior flow: terminal installer flow.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: actual PowerShell lifecycle plus shell syntax/fixture.
    - Cleanup/quarantine: isolated `.tmp` roots and retained fixture backups.
    - External side effects: none.
    - N/A notes: POSIX run depends on available Bash/WSL; otherwise report exact evidence level.
  - Work Steps:
    1. Add Decision Trace runtime files to both installer copy/required lists.
       - UI flow check: installer output remains beginner-readable.
       - DB/data flow check: no state path moves during same-version reinstall.
       - Render location check: installed `.p2p/system/scripts` exposes CLI.
       - Mini QA: fresh PowerShell install and installed doctor.
       - Evidence target: `E2-P2A-INSTALL1`.
    2. Assert same-version reinstall does not duplicate runtime or backup state.
       - UI flow check: class is `SAME_VERSION_REINSTALL`.
       - DB/data flow check: protected state and ledger bytes are unchanged.
       - Render location check: one runtime tree and one profile set remain.
       - Mini QA: repeat actual installer against the same fixture.
       - Evidence target: `E2-P2A-IDEMPOTENCE1`.
  - Implementation Gate: candidate package doctor PASS and fixture targets are
    inside `.tmp`; no protected target path is resolved.
  - Acceptance:
    - Source: both installers include the same runtime contract.
    - Runtime/UI: fresh and reinstall output is correct.
    - DB/data: protected state unchanged.
    - Behavior test: idempotence PASS.
    - Cleanup/quarantine: fixture-only writes.
    - Evidence IDs: `E2-P2A-INSTALL1`, `E2-P2A-IDEMPOTENCE1`.
    - Actual-status rows refreshed: installer provisioning/idempotence.
  - Evidence Targets: installer output, file snapshots, marker, doctor/drift.
  - Actual-status Update: `missing -> correct` for trace installer provisioning.
  - Commit Boundary: no Git; record artifact/source hashes.

+ [x] P2-B: Add fresh/upgrade/reinstall fixture harness.
  - Goal: prove the full lifecycle from the actual `.5` ZIP and preserve old
    history byte-for-byte.
  - Scope Boundary:
    - Editable: new developer-only evaluator/tests under `scripts/` and `tests/`.
    - Inspect-only: extracted package and old `.4` artifact.
    - Preserve-only: release artifacts and real projects.
    - Out of scope: evaluator shipping in the runtime payload.
  - Non-Goals: no synthetic eight-agent quorum claim.
  - Pre-flight Questions:
    - Data source: new ZIP, old ZIP, temporary fresh/legacy fixtures.
    - Display permission: machine-readable release evidence and QA report.
    - DB read flow: N/A; file/hash readback.
    - DB write flow: fixture installation and synthetic ledger activity.
    - Render location: `.tmp` fixtures and `reports/QA`.
    - UI behavior flow: N/A; CLI/installer lifecycle.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: RI-DT1–RI-DT15, RI-DT24–RI-DT35 subset.
    - Cleanup/quarantine: context-managed temporary roots.
    - External side effects: none.
    - N/A notes: real user project and public release excluded.
  - Work Steps:
    1. Fresh-install the actual candidate into a new fixture and run package,
       capability, UIUX, trace doctor, workflow, and beginner WHY checks.
       - UI flow check: N/A.
       - DB/data flow check: new project state and trace ledger readback.
       - Render location check: status/report/WHY references exist.
       - Mini QA: run fresh fixture and record command output.
       - Evidence target: `E2-P2B-FRESH1`.
    2. Install old `.4` into a seeded legacy fixture, snapshot protected state
       and ledger bytes, upgrade with `.5`, and repeat a material decision.
       - UI flow check: N/A.
       - DB/data flow check: old bytes unchanged; new trace appended only after action.
       - Render location check: legacy query is honest and new query is native.
       - Mini QA: upgrade fixture with hash/ledger assertions.
       - Evidence target: `E2-P2B-UPGRADE1`.
    3. Reinstall `.5` and compare runtime/state/relationship/backup snapshots.
       - UI flow check: N/A.
       - DB/data flow check: no duplicate trace or relationship records.
       - Render location check: doctor/drift remain PASS.
       - Mini QA: actual same-version reinstall.
       - Evidence target: `E2-P2B-REINSTALL1`.
  - Implementation Gate: fresh install PASS before upgrade/reinstall.
  - Acceptance:
    - Source: harness uses actual supported package/install entrypoints.
    - Runtime/UI: beginner workflow reaches terminal state and WHY is usable.
    - DB/data: protected state and ledger preservation PASS.
    - Behavior test: fresh/upgrade/reinstall PASS.
    - Cleanup/quarantine: no temp fixture escapes.
    - Evidence IDs: `E2-P2B-FRESH1`, `E2-P2B-UPGRADE1`, `E2-P2B-REINSTALL1`.
    - Actual-status rows refreshed: lifecycle rows.
  - Evidence Targets: fixture snapshots, marker classes, ledger bytes, doctor,
    drift, trace queries, and artifact hash.
  - Actual-status Update: lifecycle rows become `correct` or an explicit
    evidence-backed blocker.
  - Commit Boundary: no Git; reports/artifact remain local.

+ [x] P2-C: Add installed Decision Trace behavioral certification.
  - Goal: prove installed runtime preserves the certified trace semantics.
  - Scope Boundary:
    - Editable: developer-only evaluator/tests/reports.
    - Inspect-only: native runtime semantics except fixes required by a failing
      release binding.
    - Preserve-only: UIUX/Foundation and governance authority.
    - Out of scope: Code-Impact and new capabilities.
  - Non-Goals: no false regulatory/compliance claim.
  - Pre-flight Questions:
    - Data source: installed `.p2p/system`, synthetic project ledger/facts.
    - Display permission: safe trace output/export.
    - DB read flow: existing JSONL and synthetic governance refs.
    - DB write flow: append-only legitimate trace events.
    - Render location: query JSON/Markdown and beginner WHY.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: RI-DT4–RI-DT23, RI-DT27–RI-DT31.
    - Cleanup/quarantine: temporary fixture roots only.
    - External side effects: none.
    - N/A notes: no real quorum execution is claimed.
  - Work Steps:
    1. Exercise material/routine capture, approval/no-approval, source/fact/
       evidence, contradiction, supersession, temporal, missing refs, reverse
       artifact lookup, redaction, tamper evidence, and deterministic exports.
       - UI flow check: N/A.
       - DB/data flow check: inspect ledger bytes and reference status.
       - Render location check: beginner WHY contains honest uncertainty.
       - Mini QA: run installed evaluator and focused tests.
       - Evidence target: `E2-P2C-TRACE1`.
    2. Re-run UIUX/Foundation and core regression after installation, then
       measure WHY before/after and inspect maintenance residual risk.
       - UI flow check: UIUX routing/design/accessibility evidence is CLI/state scope.
       - DB/data flow check: FACT authority and lock remain unchanged.
       - Render location check: reports record measurable comparison.
       - Mini QA: package/lifecycle regression suite.
       - Evidence target: `E2-P2C-REGRESSION1`.
  - Implementation Gate: P2-B actual installed runtime exists and is doctor PASS.
  - Acceptance:
    - Source: evaluator is developer-only and does not alter shipped runtime.
    - Runtime/UI: all installed trace behaviors pass.
    - DB/data: no authority overwrite or false history.
    - Behavior test: installed evaluator and regressions PASS.
    - Cleanup/quarantine: fixture-only writes.
    - Evidence IDs: `E2-P2C-TRACE1`, `E2-P2C-REGRESSION1`.
    - Actual-status rows refreshed: installed trace and regression.
  - Evidence Targets: RI-DT matrix, WHY before/after, residual risk, full tests.
  - Actual-status Update: installed trace semantics `unbound -> bound-correct`.
  - Commit Boundary: no Git; retain evidence reports.

### P3: Release certification

- Phase Goal: run RI-DT1–RI-DT35 against the actual new ZIP and produce final
  artifact/hash/boundary evidence.
- Phase Boundary:
  - In scope: full regression, package boundary, old artifact hash, package
    doctor, drift, secret, UIUX/Foundation, maintenance residual risk, release
    counts, and certification report.
  - Out of scope: public publication and unrelated capability work.
  - Dependencies: P2 complete.
- Phase Implementation Rule: run P3-A artifact certification, then P3-B
  independent QA review; do not claim PASS from source tests alone.
- Ordered Slice List:
  - P3-A: Run full artifact certification and write QA evidence.
  - P3-B: Re-run fresh closure checks and select exactly one next Goal.

+ [x] P3-A: Run full artifact certification and write QA evidence.
  - Goal: establish all RI-DT1–RI-DT34 facts from actual package lifecycle.
  - Scope Boundary: actual new ZIP, temporary fixtures, developer-only reports.
  - Non-Goals: no artifact publication.
  - Pre-flight Questions: CLI/state-only; Docker/browser/Playwright are N/A.
  - Work Steps:
    1. Build ZIP and record version/path/filename/size/content count/member
       count/SHA-256; verify package doctor and exclusions.
       - Evidence target: `E3-P3A-ARTIFACT1`.
    2. Run the lifecycle evaluator, full unittest, capability/UIUX/trace
       doctors, drift and secret scans; write QA report.
       - Evidence target: `E3-P3A-RI1`.
  - Implementation Gate: artifact is new and old `.4` hash is unchanged.
  - Acceptance: RI-DT1–RI-DT34 are individually evidenced with no unsupported
    PASS claim.
  - Actual-status Update: certification rows become measured.
  - Commit Boundary: local artifact only; no public release.

+ [x] P3-B: Re-run fresh closure checks and select exactly one next Goal.
  - Goal: independently confirm final package boundary and residual risk.
  - Scope Boundary: supervisor/QA evidence and plan closure only.
  - Non-Goals: no implementation of the selected next Goal.
  - Pre-flight Questions: N/A for UI/DB/Docker; source/artifact/readback only.
  - Work Steps:
    1. Re-run package verify/doctor/drift/secret, old hash, artifact inventory,
       and core regression after the final report changes.
       - Evidence target: `E3-P3B-CLOSURE1`.
    2. Classify the largest residual maintenance risk and record exactly one
       next Goal or STOP.
       - Evidence target: `E3-P3B-NEXT1`.
  - Implementation Gate: P3-A has fresh RI evidence.
  - Acceptance: RI-DT35 is satisfied by one evidence-backed recommendation.
  - Actual-status Update: P3 complete only after supervisor review.
  - Commit Boundary: no Git; final artifact hash is the release boundary.

### P4: Supervisor acceptance and handoff

+ [x] P4-A: Call supervisor for the completed-plan acceptance loop.
  - Goal: independently verify source, actual ZIP, installer lifecycle, runtime
    behavior, state preservation, package boundary, and all RI evidence.
  - Work Steps: inspect source and reports; extract the actual ZIP; rerun the
    strongest lifecycle checks; write exactly one PASS or REJECT report; if
    rejected, return only the failed scope to coder and re-review.
  - Implementation Gate: P1–P3 complete or explicitly blocked.
  - Acceptance: supervisor PASS with no unverified same-invariant surface.

+ [x] P4-B: Remove dead work created during this plan.
  - Goal: keep developer evaluator/reports out of the shipped ZIP and remove
    only plan-created temporary artifacts from source `.tmp`.
  - Work Steps: inspect ZIP inventory and `.tmp`; preserve required evidence;
    remove/quarantine only disposable plan-created outputs; rerun boundary scan.
  - Implementation Gate: only plan-created files are candidates.
  - Acceptance: no dead package content or escaped temporary state remains.

+ [x] P4-C: Close the plan.
  - Goal: record final evidence, benchmark, hash, no-Git status, one next Goal,
    and final response with the exact 31 requested sections.
  - Work Steps: refresh lock if required; update all four plan files; run final
    source/artifact checks; mark plan complete only after supervisor PASS.
  - Implementation Gate: P4-A and P4-B PASS.
  - Acceptance: RI-DT1–RI-DT35 status is known and no required work remains.

## Risk Notes

- Current source is an unpacked development tree; package doctor failure there
  is expected, but the new actual ZIP must pass.
- PowerShell is the primary host path. POSIX installer evidence is run when a
  supported Bash/WSL executable is available; otherwise the exact evidence
  level is recorded and not overstated.
- The existing `.4` artifact must remain byte-identical; the new `.5` artifact
  is a separate output.

## Final closure

Status: PASS. RI-DT1–RI-DT35 are evidenced by the actual extracted `.5` ZIP
lifecycle and independent supervisor audit. The final release boundary is
the local artifact at D:/AI/P2P_dev/P2P-8.4.7-C-Codex-Edition-v5.zip with
SHA-256 f88dbf706c4ac85a8aadf38960923cdc8e4ba6e415b83f3f1726692fb3ad8dda.
Exactly one next Goal is recommended: normalize installed workflow
policy-reference paths for Native Decision Trace. It is not implemented in
this Goal.
- No Git metadata exists. Reports, hashes, runtime lock, and artifact manifest
  provide local auditability.
- A real host eight-thread quorum and Aesthetica identity execution probe may
  not be available. Report the maximum real evidence level; never simulate.
