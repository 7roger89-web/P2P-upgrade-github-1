# P2P-SEC01 Security / Reverse Foundation and APKiD Proof Adapter Plan

## Metadata

- Date: `2026-08-29`
- Status: `P3 complete; stopped at Owner Gate`
- Plan: `docs/plans/2026-08-29-p2p-sec01-security-reverse-apkid/2026-08-29-p2p-sec01-security-reverse-apkid-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-sec01-security-reverse-apkid/2026-08-29-p2p-sec01-security-reverse-apkid-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-sec01-security-reverse-apkid/2026-08-29-p2p-sec01-security-reverse-apkid-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-sec01-security-reverse-apkid/2026-08-29-p2p-sec01-security-reverse-apkid-actual-status.md`

## Goal

Add the smallest security and reverse-engineering semantics to the existing
P2P capability registry/router/orchestration control plane and prove one
bounded `SAFE_READONLY` Android APKiD CLI adapter. Produce one isolated,
unpromoted candidate from fresh official `main`.

## Rules

- Fresh official `main` SHA/tree are the authority for this candidate.
- Preserve the existing six manifest classes, canonical eight, one router,
  EFF01 orchestration policy, evidence contracts, and provider-neutral seams.
- Add no second registry, router, orchestrator, risk engine, truth store, or
  verification framework.
- Keep security execution classes fail-closed: active or higher requires an
  authorized target and controlled test environment; offensive work also
  requires explicit task authority; destructive work is denied by default.
- APKiD is an external tool with a minimal local adapter. No auto-install,
  network, credentials, device/emulator, APK mutation, repack/sign, Frida,
  bypass, exploit, or production action.
- Decompilation is not source reconstruction. Insufficient reconstruction
  evidence is `UNKNOWN`; original-source recovery is never claimed.
- Do not modify the invalid root `.git`, dirty canonical/runtime worktree,
  release/v5/immutable baseline, or any user project.
- Verification is limited to the focused contract/adapter/boundary tests,
  directly affected registry/router/EFF01 tests, compile and diff checks. No
  Anvien, Council, broad regression, full security stack, or installation.
- Technical PASS remains separate from Owner approval, promotion, release,
  deployment, and live activation.

## Problem

The current official registry has the existing six P2P capability classes and
27 entries but no security/reverse capability semantics, execution-class
authorization gate, reverse evidence distinction, or APKiD adapter. Existing
C41/C42 records describe other release/pilot/framework lineages and are not a
security subject. The existing EFF01 policy has risk lanes and fail-closed
safety invariants but no security execution-class binding.

## Scope

- Fresh-main identity and C41/C42 lineage reconciliation.
- Optional `SEMANTIC_KIND` metadata beside the existing manifest `TYPE`, with
  validation that does not alter the six canonical manifest classes.
- The 12 requested security/reverse capability IDs, deduplicated against the
  current registry.
- Existing-router trigger/readiness compatibility.
- Existing EFF01 orchestration binding for five security execution classes and
  authorization decisions.
- Minimal reverse evidence result contract.
- Existing external-source catalog extension for the Phase 1 tool list; all
  entries remain non-vendored and non-executed.
- A local-only APKiD adapter for `android.protection.detect` and focused tests.
- One candidate commit lineage ending at an explicit Owner Gate.

## Non-Goals

- No APKiD installation or real external-tool execution unless an already
  available binary is discovered for an optional smoke check.
- No Apktool, JADX, bundletool, MobSF, Frida, Ghidra, native/managed
  decompiler, emulator, runtime instrumentation, network inspection, bypass,
  exploit, or full reconstruction engine.
- No source SPEC/Live Spec promotion, release artifact rebuild, deployment,
  remote push, canonical promotion, or live activation.
- No new security registry, risk engine, router, runner framework, or external
  dependency manager.

## Addendum — Monetization / Revenue Integrity extension seam

- Status: `PLANNED_CANONICAL_EXTENSION`; this is a record-only seam, not SEC01
  payment, ads, billing, ledger, or entitlement implementation.
- Ownership: an independent future P2P vertical owns monetization and revenue
  integrity. Android is an integration surface, not the domain owner.
- Boundary: reserve the future `monetization.*` semantic namespace without
  adding capability IDs or provider-specific code now.
- Reuse: future work must use this existing capability registry, the single
  router, EFF01 risk/orchestration policy, normalized evidence contract, and
  control plane. No monetization-specific router or truth store is introduced.
- Compatibility: the generic SEC01 seams leave room for future controlled tests
  of tampered client callbacks, replayed external transactions, patched client
  entitlement state, duplicate transaction submission, and hooked billing/ad
  callbacks. Static/local cases can remain in `SAFE_READONLY` or
  `ANALYSIS_LOCAL`; active or higher cases use the existing fail-closed
  authorization predicates. This is a compatibility boundary, not proof that
  those future tests have been implemented.
- Deferred future invariants: `CLIENT_IS_NOT_FINANCIAL_AUTHORITY`;
  `CLIENT_EVENT != VERIFIED_REVENUE_EVENT`;
  `CLIENT_PURCHASE_CALLBACK != VERIFIED_PURCHASE`;
  `PURCHASE_SUCCESS_UI != ENTITLEMENT_GRANTED`;
  `AD_CALLBACK != VERIFIED_HIGH_VALUE_REWARD`;
  `ONE_EXTERNAL_TRANSACTION -> MAXIMUM_ONE_LEDGER_EFFECT`;
  `ENTITLEMENT_STATE_IS_BACKEND_AUTHORITY`; `NO_PAYMENT_SECRET_IN_APK`;
  `PATCHED_CLIENT_MUST_NOT_MINT_UNVERIFIED_SERVER_VALUE`;
  `PLAY_INTEGRITY_IS_RISK_SIGNAL_NOT_PURCHASE_TRUTH`; `BALANCE != LEDGER`;
  `REAL_TIME_EVENT != COMPLETE_TRUTH`.
- Explicitly deferred: AdMob, BillingClient, Google APIs, RTDN, ledger
  databases, mediation, subscriptions, provider-specific integrations, and
  production telemetry. No new Owner Gate is created; the existing SEC01
  Owner Gate and validation ceiling remain unchanged.

## Addendum — Infrastructure / Backend Security extension seam

- Status: `INFRASTRUCTURE_BACKEND_SECURITY =
  PLANNED_CANONICAL_EXTENSION`; this is documentation/reconciliation only and
  does not reopen or expand SEC01 implementation.
- Ownership: Infrastructure / Backend Security is a shared P2P platform
  capability. It is not owned by Android, Security / Reverse Engineering, or
  Monetization.
- Reuse: future infrastructure capabilities must use the existing capability
  registry, single router, EFF01 orchestration/risk policy, evidence model,
  Task State/recovery, Control Tower, and Owner/release gates. No
  infrastructure-specific router, orchestrator, truth store, risk engine, or
  deployment control plane is introduced.
- Canonical classes: `SECURITY_LAB`, `APPLICATION_BACKEND`, and
  `PRODUCTION_SCALE_INFRASTRUCTURE`. Principles:
  `MINIMUM_INFRASTRUCTURE_FIRST` and `SCALE_ONLY_WHEN_EVIDENCE_JUSTIFIES`.
- Security Lab default: prefer `LOCAL`, `ISOLATED_DOCKER`, or
  `EPHEMERAL_RUNNER`. For the current APKiD proof, record conceptually
  `INFRASTRUCTURE_CLASS=SECURITY_LAB`, `EXECUTION_ENVIRONMENT=LOCAL_OK`, and
  `PUBLIC_SERVER_REQUIRED=false`; no APKiD adapter metadata or code is changed
  solely to encode these future fields.
- Backend authority: when client-side state controls material security or
  economic value, preserve `CLIENT != AUTHORITY` and require backend authority
  where materially needed. This does not imply `EVERY_PROJECT_REQUIRES_BACKEND`;
  an offline application may resolve `BACKEND_REQUIRED=NO`.
- Reserved future semantic coverage: `infrastructure.requirement.detect`,
  `infrastructure.plan`, `infrastructure.backend.select`,
  `infrastructure.database.select`, `infrastructure.security_boundary.design`,
  and `infrastructure.cost.estimate`. No executable registry entries are added
  for these names in SEC01.
- Deferred execution: `infrastructure.provision`,
  `infrastructure.observe`, `infrastructure.scale`,
  `infrastructure.backup`, and `infrastructure.recover`, including VPS,
  Kubernetes, microservices, Redis, Kafka, Terraform/Pulumi, production/cloud
  databases, cloud accounts, load balancers, multi-region, autoscaling,
  monitoring/secrets infrastructure, and deployment pipelines.
- Monetization binding remains `CLIENT -> APPLICATION_BACKEND -> PROVIDER
  VERIFICATION -> LEDGER / ENTITLEMENT`: infrastructure supplies the backend
  boundary, Monetization owns revenue semantics, and Security verifies that
  client tampering cannot mint unauthorized server-side value. These domains
  are not merged.
- Future environment seam only: generic security/reverse work may later express
  `LOCAL_OK`, `ISOLATED_RUNNER_REQUIRED`, `DEVICE_REQUIRED`, `NETWORK_REQUIRED`,
  `BACKEND_REQUIRED`, or `PRODUCTION_INFRA_REQUIRED` without requiring a new
  scheduler, runner manager, planner, or provisioning engine now.
- No canonical cloud provider is selected. Provider choice remains future
  work, based on real project requirements, current pricing/policy/region
  constraints, and available providers. The existing SEC01 Owner Gate and
  validation ceiling remain unchanged; no Infrastructure Owner Gate is added.
- Current-truth note: after the existing SEC01 candidate was prepared,
  `origin/main` advanced independently to `bc686845fbb5817e50958d91e0d382a72c219b78`
  (tree `68b16f0fd2116ec6e93bdb9dbecc31429a68ec6d`). This addendum does not
  merge or rebase the candidate onto that later AUTO01 lineage; the candidate
  remains explicitly based on the already-reviewed SEC01 base.

## Requirements

- Registry validation remains fail-closed and canonical denominator remains
  `8/8`.
- `SEMANTIC_KIND` accepts only `SKILL`, `TOOL`, `ADAPTER`, `VENDOR`,
  `EXTERNAL_RUNTIME`, and `KNOWLEDGE_SOURCE` when present.
- Desired IDs are present exactly once and APKiD is represented as an adapter
  capability without inventing a separate tool registry.
- APKiD accepts only an explicit local `.apk` file, hashes it before analysis,
  invokes one local CLI process with argument-list execution, and never writes
  to the artifact.
- Missing APKiD dependency returns an explicit unavailable/dependency result,
  never a PASS; non-zero/invalid output remains UNKNOWN or unavailable.
- Normalized findings preserve backend evidence for packer, protector,
  compiler, and obfuscator labels without inventing confidence.
- Active/offensive/destructive authorization tests prove the required
  fail-closed predicates in the existing orchestration policy.

## Acceptance Criteria

- Fresh candidate base is exactly `b8d09fc7a0e4a91e75db7f10dc8cfaea007ba37a`
  with tree `91012e41e67a956bbca311368dc51a45e8c0423b`.
- C41/C42 are documented as unrelated historical subjects; no identifier is
  reused as a security subject.
- Registry, router, orchestration, reverse contract, and APKiD focused tests
  pass; directly affected existing tests remain green.
- APKiD missing-dependency, normalization, artifact-binding, and readonly
  boundary cases are deterministic.
- Compile and `git diff --check` pass; no broad regression is run.
- One clean isolated candidate is created and remains unpromoted. Owner Gate
  is required; canonical promotion is false.

## Checklist

- [x] P0-A: Verify current authority and reconcile existing security/C41/C42
  scope.
  - Goal: bind fresh `main`, read the relevant approved SPEC cluster, inspect
    registry/router/EFF01/adapters/vendor policy, and classify historical IDs.
  - Work Steps: preserve invalid/dirty roots, clone official main under
    repo-local `.tmp`, verify SHA/tree/remote/status, read full relevant SPECs,
    inspect current source and records, and record the evidence matrix.
  - Implementation Gate: fresh clean checkout and disjoint lineage result.
  - Acceptance: base identity is exact, current security surface is known, and
    no C41/C42 security subject exists.

### P1: Foundation semantics and APKiD proof

- Phase Goal: implement only the minimum reusable security/reverse contracts
  and one safe local APKiD adapter.
- Phase Boundary:
  - In scope: capability metadata, requested IDs, existing-router triggers,
    EFF01 binding, reverse evidence contract, tool catalog, APKiD adapter, and
    focused tests.
  - Preserve-only: approved SPECs, canonical identities, existing control
    plane, C41/C42 history, release/v5/baseline, and unrelated capabilities.
  - Out of scope: external installation, live actions, remote writes, and
    broad regression.
- Phase Implementation Rule: code first for each slice, then add/update its
  focused tests, run the smallest acceptance checks, record evidence, and
  commit before the next slice.

- [x] P1-A: Add foundation semantics and registry/tool catalog entries.
  - Goal: distinguish the requested semantic kinds without changing the
    existing six manifest classes; bind security execution classes to EFF01;
    provide the minimal reverse evidence contract.
  - Scope Boundary:
    - Editable: capability model, orchestration policy, capability registry,
      existing external-source catalog, package exports, and foundation tests.
    - Inspect-only: approved SPEC files, current router implementation,
      C41/C42 records, dirty canonical/runtime worktree.
    - Out of scope: new router/risk engine, provider installation, release or
      promotion artifacts.
  - Non-Goals: no decompiler, no active runtime, no reconstruction engine.
  - Pre-flight Questions:
    - Data source: fresh `main`, current registry, approved capability SPEC
      cluster, existing EFF01 policy and external-source manifest.
    - Display permission: local source/evidence only; no secrets.
    - DB read/write flow: N/A; this slice uses JSON/Python source only.
    - DB write flow: N/A; no database is present or touched.
    - Render location: N/A; CLI/test evidence only.
    - UI behavior flow: N/A; no public UI is in scope.
    - Docker runtime: N/A; standard-library-only local code.
    - Playwright target: N/A.
    - Behavior test: class validation, exact IDs, single-router selection,
      reverse UNKNOWN, and active/offensive/destructive authorization.
    - Cleanup/quarantine: isolated clone and repo-local `.tmp` only; preserve
      all pre-existing roots.
    - External side effects: none.
    - N/A notes: Anvien and broad suites are explicitly excluded by the user.
  - Work Steps:
    1. Add optional semantic-kind validation and security/reverse contract
       constants/results without changing the six `TYPE` classes.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: structured Python result.
       - Mini QA: import and compile affected modules.
       - Evidence target: `E1-P1A-CONTRACT1`.
    2. Add the exact requested IDs, APKiD adapter capability metadata, trigger
       coverage, and non-vendored Phase 1 catalog to existing surfaces.
       - UI flow check: N/A; existing router output only.
       - DB/data flow check: N/A.
       - Render location check: registry/catalog JSON inspection.
       - Mini QA: registry validation and focused route test.
       - Evidence target: `E1-P1A-REGISTRY1`.
    3. Bind execution classes to the existing EFF01 lane and authorization
       policy; do not add another risk engine.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: policy result JSON.
       - Mini QA: fail-closed authorization cases.
       - Evidence target: `E1-P1A-RISK1`.
  - Implementation Gate: P0-A is complete and all protected boundaries are
    preserve-only.
  - Acceptance:
    - Source: semantic-kind, reverse evidence, and execution-class contracts
      are implemented in existing package surfaces.
    - Runtime/UI: N/A.
    - DB/data: no database or user data touched.
    - Behavior test: exact IDs and fail-closed policy cases pass.
    - Cleanup/quarantine: no external dependency installed or executed.
    - Evidence IDs: `E1-P1A-CONTRACT1`, `E1-P1A-REGISTRY1`, `E1-P1A-RISK1`.
    - Actual-status rows refreshed after verification.
    - Result: complete. The existing six `TYPE` classes and one router were
      preserved; 12 requested IDs, the semantic-kind vocabulary, reverse
      evidence contract, and EFF01 authorization binding are present.
  - Evidence Targets: `E1-P1A-CONTRACT1..E1-P1A-RISK1`.
  - Actual-status Update: record changed paths, registry count, and policy
    results.
  - Commit Boundary: commit after foundation-focused tests pass.

- [x] P1-B: Implement and prove the APKiD minimal adapter.
  - Goal: normalize bounded APKiD CLI evidence for one local APK while
    preserving readonly and dependency-unavailable boundaries.
  - Scope Boundary:
    - Editable: APKiD adapter module, package exports, and focused adapter
      tests.
    - Inspect-only: external tool catalog and existing backend contracts.
    - Preserve-only: all other adapters, routers, external sources, and
      production/user paths.
    - Out of scope: APKiD installation, network/device/runtime analysis,
      mutation, signing, bypass, and real target interaction.
  - Non-Goals: no general external process framework and no tool vendoring.
  - Pre-flight Questions:
    - Data source: explicit local APK fixture and controlled fake CLI output.
    - Display permission: fixture output and local artifact hash only.
    - DB read/write flow: N/A.
    - DB write flow: N/A.
    - Render location: normalized test result.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: unavailable dependency, normalized findings, invalid
      target rejection, hash binding, and no mutation.
    - Cleanup/quarantine: temporary fixture roots under clone `.tmp`; cleanup
      only test-created files.
    - External side effects: none; no real APKiD required.
    - N/A notes: optional smoke is recorded only if `apkid` already exists.
  - Work Steps:
    1. Implement a standard-library-only local APKiD adapter using an argument
       list, dependency probe, hash binding, timeout, and normalized output.
       - UI flow check: N/A.
       - DB/data flow check: artifact is read-only.
       - Render location check: adapter result contract.
       - Mini QA: compile and dependency-unavailable case.
       - Evidence target: `E1-P1B-ADAPTER1`.
    2. Run controlled fake-CLI normalization and readonly boundary tests; run
       optional real smoke only if the binary is already installed.
       - UI flow check: N/A.
       - DB/data flow check: fixture hash/mtime unchanged.
       - Render location check: normalized findings and status.
       - Mini QA: focused APKiD test module.
       - Evidence target: `E2-P1B-APKID1`.
  - Implementation Gate: P1-A foundation contracts and registry validation
    pass.
  - Acceptance:
    - Source: `android.protection.detect` maps to the minimal APKiD adapter.
    - Runtime/UI: no device/emulator or external target.
    - DB/data: local fixture only; no writes.
    - Behavior test: missing dependency is unavailable, successful fixture is
      normalized and hash-bound, invalid/mutating paths are rejected.
    - Cleanup/quarantine: all fixtures are isolated and removed safely.
    - Evidence IDs: `E1-P1B-ADAPTER1`, `E2-P1B-APKID1`.
    - Actual-status rows refreshed after verification.
    - Result: complete. APKiD is unavailable locally and was not installed;
      controlled fake-CLI evidence proves normalization, hash binding, and
      mutation rejection.
  - Evidence Targets: `E1-P1B-ADAPTER1`, `E2-P1B-APKID1`.
  - Actual-status Update: record dependency behavior and no-smoke/optional
    smoke result.
  - Commit Boundary: commit after adapter-focused tests pass.

### P2: Focused verification and candidate identity

- [x] P2-A: Run the verification ceiling and prepare candidate evidence.
  - Goal: run only the requested focused tests, compile/diff checks, and
    directly affected existing registry/router/EFF01 tests.
  - Work Steps: run tests, inspect statuses, verify optional APKiD binary
    without installing, compute final SHA/tree/base, and record all outcomes.
  - Implementation Gate: P1-A and P1-B pass.
  - Acceptance: all allowed checks are green or explicitly classified; broad
    regression is `NOT RUN` by user instruction.
  - Result: complete. SEC01 8/8, foundation 28/28, EFF01+adaptive 13/13,
    selective router 7/7, compile, registry, and diff checks pass. `apkid`
    is not available; no smoke/install was attempted.

### P3: Independent review and stop at Owner Gate

- [x] P3-A: Supervisor review.
  - Goal: independently review ancestry, scope, contracts, adapter safety,
    focused evidence, and no-promotion boundary.
  - Work Steps: review source/diff/reports without repair during review; record
    PASS or a truthful blocker.
  - Implementation Gate: P2-A evidence exists.
  - Acceptance: Supervisor PASS or explicit remediation/blocker.
  - Result: complete. Supervisor PASS_WITH_OWNER_GATE; no scoped defect and
    no repair during review.

- [x] P3-B: Close the unpromoted candidate.
  - Goal: record final candidate SHA/tree/base, clean status, Owner Gate
    requirement, and terminal verdict.
  - Work Steps: commit evidence/report updates, inspect final diff/status, and
    stop. Do not approve, promote, release, deploy, or live-activate.
  - Implementation Gate: P3-A PASS.
  - Acceptance: candidate is clean, descended from fresh main, unpromoted,
    and ready for a separately authorized Owner Gate.
  - Result: complete. Implementation candidate `1a2f458e...` is clean and
    descended from fresh main; the packet is unpromoted and stops at Owner
    Gate. No approval, promotion, release, deployment, or live activation was
    performed.

## Risk Notes

- The invalid root `.git` and dirty canonical runtime are authority hazards;
  the isolated fresh clone is the only editable subject.
- Adding new manifest metadata must not expand the six authoritative `TYPE`
  classes or create a second registry.
- APKiD output is backend evidence, not authority; unsupported confidence and
  insufficient reverse evidence remain `UNKNOWN`.
- A technical candidate PASS does not imply Owner approval or promotion.

## Current-canonical reconciliation addendum

- Fresh official main is the sole new candidate base. The old reviewed SEC01
  candidate is evidence for the coherent delta, not a replacement for current
  main.
- The overlap audit found only the notes decision log. Preserve current AUTO01
  content and append SEC01 reconciliation text; do not revert current-main
  behavior.
- Carry forward the non-overlapping SEC01 implementation and both planned
  extension seams. No new control-plane component is permitted.
- Because AUTO01 does not touch SEC01 production/control-plane paths, run only
  SEC01 adapter/foundation compatibility checks, registry/JSON parse,
  uniqueness, compile, and diff checks. Reuse unchanged prior evidence where
  valid; do not run broad regression, Anvien, Council, full security stack,
  provider installation, monetization tests, or infrastructure provisioning.
- Bind one fresh candidate from current main, keep the single existing Owner
  Gate, and stop unpromoted after sufficient evidence.
