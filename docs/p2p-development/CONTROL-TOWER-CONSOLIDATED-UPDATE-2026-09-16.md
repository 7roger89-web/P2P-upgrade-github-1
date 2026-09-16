# P2P Control Tower — Consolidated Update — 2026-09-16

Status: DURABLE_RECONCILIATION_UPDATE
Purpose: one-time reconciliation of recent P2P chat work against current durable GitHub state.

## 0. Authority and starting point

- Canonical repository: `7roger89-web/P2P-upgrade-github-1`
- Canonical branch: `main`
- Main at this update start: `cb17bda20a4a1a230a3c21f04f301bda27136039`
- Latest main rechecked for this addendum: `f61e9884c1d1fbfa9f4736d1425740dee11017e7`
- Canonical Supreme Law: `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`, section `P2P_SUPREME_OPERATING_LAW_V1`
- Durable GitHub state and canonical ledgers override chat recollection.
- Do not ask Owner to reconstruct old chat history. Fresh-check GitHub first.
- `GOAL PASS != PROMOTION`; deployment, secrets, spend, destructive changes, infrastructure and hard rollback remain Owner-gated.

## 1. Recently completed and merged work

### 1.1 Hermes essential tooling and runtime

Merged lineage:
- PR #153 — bounded Repomix/TokScale bridges.
- PR #158 — Hermes v0.21.3 runtime compatibility certification path.
- PR #159 — local opt-in Hermes essential stack closure.

Durable decisions:
- Repomix is bounded context tooling, not authority.
- TokScale is telemetry, not billing truth.
- Hindsight remains optional and bounded; automatic retain/recall are not canonical truth.
- Hermes Workspace is UI/workspace, not Control Tower authority.
- Mission Control is rejected as a second P2P control plane.
- No production/public deployment or secret-bearing Hindsight activation was authorized by these source merges.

### 1.2 Personal AI behavior lineage

Merged lineage:
- PR #152 — clean-room Personal AI Behavior Harness V1.
- PR #162 — Hermes runtime/plugin integration.
- PR #178 — bounded per-session interaction adaptation.

Durable boundary:
- no relationship score/stages, hormone/presence simulation, fake human state, autonomous durable-memory mutation, new DB/vector store/daemon/scheduler, or automatic proactive messaging authority.
- session adaptation remains bounded and evidence-sensitive; after correction of a false completion claim, fresh evidence is required before completion is claimed again.

### 1.3 Supergoal-pattern / native `/goal` lineage

Merged lineage:
- PR #169 — bounded Supergoal execution patterns only.
- PR #170 — transport through existing P2P runtime.
- PR #174 — portable AGENTS projection.
- PR #177 — deterministic auto-activation from durable P2P GoalPlan/TaskPlan state.

Durable decision:
- do not install or adopt Supergoal as a second roadmap/state/control plane.
- P2P remains authority; native host `/goal` is an execution surface, never acceptance authority.
- complete-worktree evidence and original-contract replay remain required before completion claims.

### 1.4 Opik / Graphiti

Merged lineage:
- PR #171 — bounded Opik observer for Hermes.
- PR #175 — distribution closure.

Durable decision:
- Opik is implemented but default OFF.
- default mode is metadata-only; content capture and real external telemetry remain separate privacy/secret gates.
- Graphiti remains RESEARCH_ONLY / not adopted into runtime because P2P durable truth remains authoritative and Hindsight already occupies the optional memory lane.

### 1.5 Reverse-Skill

- PR #173 merged: safe methodology/reference assimilation under the existing P2P security/reverse authority.
- PR #172 closed unmerged as superseded.
- no upstream bootstrap, auto-install, MCP registration, implicit offensive execution, or second router/control plane was adopted.

### 1.6 Prompt / Supreme-Law serialization and Shield applicability

Merged lineage:
- PR #163 — restore Supreme-Law + OE gate prompt serialization.
- PR #164 — runtime execution-prompt serialization closure.
- PR #176 — `SHIELD-CI-01` target-shape `NOT_APPLICABLE` semantics, fail-closed.
- PR #179 — bounded prompt authoring discipline; no parallel prompt framework.

### 1.7 Evidence-First verification

- PR #182 merged.
- Canonical subordinate profile: `docs/p2p-development/P2P-EVIDENCE-FIRST-VERIFICATION.md`.
- Core invariants include:
  - `AGENT_CLAIM_IS_NOT_EVIDENCE=YES`
  - `TEST_PASS_PROVES_ONLY_CHALLENGED_BEHAVIOR=YES`
  - `OUTPUT_PASS != ACCEPTANCE_PROVEN`
  - `GOAL_PASS != PROMOTION`
- Evidence packets distinguish intent, behavior proof, regression proof, test-quality proof, structural proof, environment proof, risk proof and provenance.
- Risk lanes remain the pre-existing FAST / STANDARD / STRICT / CRITICAL lanes; no second risk classifier was added.

### 1.8 GitHub research reconciliation and code intelligence

Merged lineage:
- PR #183 — reconciled `github research.txt` against durable implementation history and added a bounded optional external structural-evidence bridge.
- PR #184 — corrected policy to NATIVE_FIRST after discovering existing native Code-Impact capability.
- PR #185 — real-worktree native Code-Impact proof, including deletion-safe baseline+current graph semantics.
- PR #186 — distribution closure through the existing release/runtime path.

Durable decision:
- Native Code-Impact in `quality_intelligence.py` / `native_code_impact.py` is primary.
- `codebase-memory-mcp` is `OPTIONAL_EXTENSION / NATIVE_FIRST` only when a concrete residual native gap exists.
- no auto-install, index, daemon, watcher, UI, ADR mutation, arbitrary graph query, second truth store, registry or router.
- marker: `NEXT_CORE_SLICE=NO_NEW_CODE_INTELLIGENCE_INFRASTRUCTURE_UNTIL_NATIVE_GAP_OBSERVED`.

Research decisions reconciled in the appendix include:
- Complexity Optimizer: adapt principle only.
- finding-unknowns: assimilate as a planning heuristic only for material unknowns.
- HyperFrames: project candidate for `p2p-video-lab`, not P2P core.
- DeerFlow / broad alternate runtimes: reference only, not competing control planes.
- Graphiti / Supermemory as canonical memory: deferred/research-only.
- CubeSandbox: deferred until a measured gap exists.
- SkillsGate/AutoSkills-style surfaces: reference only; no second registry.
- Mission Control: rejected as second authority/control plane.

### 1.9 Evidence-grounded experience evolution

PR #188 merged on 2026-09-16.

Merge/main SHA after PR #188:
`cb17bda20a4a1a230a3c21f04f301bda27136039`

Canonical research/adoption lineage:
`RA-EXT-071`

Runtime module:
`.p2p/system/p2p_capabilities/experience_evolution.py`

Lifecycle:
`CANDIDATE -> VERIFIED -> ACTIVE -> SUPERSEDED | QUARANTINED`

Required activation proof:
`BEHAVIOR_PROOF + REGRESSION_PROOF + CHALLENGE_PROOF`

Boundaries:
- agent/model self-report cannot prove an experience.
- only bounded trigger-matched ACTIVE experience may be retrieved.
- active experience is `NON_AUTHORITATIVE_VERIFIED_EXPERIENCE`.
- future utility is recorded as `HELPED | NEUTRAL | HARMED`.
- harmful use requests review; it does not silently delete history.
- uses the existing execution ledger; no new memory DB, router, daemon, external memory provider, authority or permission widening.

Exact-head Shield evidence before merge:
- focused suite: 100/100 PASS.
- native Code-Impact: PASS / FULL.
- `impact_unknown=false`.
- `external_extension_recommended=false`.

No further Experience Evolution work is required unless real future use exposes retrieval failure, contradiction, `HARMED`, stale/superseded experience, or another measured gap.

## 2. Active / unmerged work — do not misreport as complete

### 2.1 PR #187 — evidence-bound native `/goal` invocation

State at latest reconciliation: OPEN / UNMERGED.

Current head observed:
`5995f2c07615ceea59b7e03eb26eeaecd4bc866e`

Fresh PR listing on 2026-09-16 reports `mergeable=false`; this must be reconciled against current main before any integration action.

Purpose:
- read-only Claude/Codex host capability probe;
- pre-invocation gate distinguishing `NOT_NEEDED / READY_TO_INVOKE / UNAVAILABLE`;
- durable `INVOKED/UNAVAILABLE` receipts in the existing execution ledger;
- host-native status proof required before an INVOKED receipt;
- no nested host launch merely to fake same-session activation.

Do not infer readiness from earlier branch evidence. Fresh exact-head reconciliation remains required.

### 2.2 PR #180 — Opportunity Lab market-validation pilot

State at latest reconciliation: OPEN / UNMERGED / CLEAN / MERGEABLE.

Current exact PR head:
`5ca5f6b042a16f261b2f0d351e41b1dd844111d8`

Current-main merge ref tested:
`e4f1e0a1f3f5187f6c2c8726743a8cc94e82b708`

Current main used by exact-head acceptance:
`f61e9884c1d1fbfa9f4736d1425740dee11017e7`

Market gate:
`VALIDATE`, not `BUILD`.

Opportunity Lab purpose:
- answer `SHOULD WE BUILD?` before normal P2P answers `HOW DO WE BUILD?`;
- preserve `BUILDABLE != VIABLE` and `GOAL PASS != MARKET PASS`;
- produce `KILL | RESEARCH_MORE | VALIDATE | BUILD` from evidence rather than Owner enthusiasm or agent optimism.

Current logistics pilot validation entrypoints:
- atomic quote: `src.validation_pipeline.compare_quotes_validated`;
- multi-equipment FCL: `src.portfolio_validation_pipeline.compare_fcl_portfolios_validated`.

Atomic order:
`explicit FX -> named-base percentage -> charge semantics -> deterministic core comparison`.

Current deterministic/internal checkpoint:
`FULL_DOMAIN_CI_READY + VALIDATED_GOLDEN_FIXTURE_READY + ORDER_INVARIANCE_READY + DIRTY_QUOTE_ADVERSARIAL_READY + DIRTY_COMMERCIAL_VALIDITY_READY + IDENTITY_INTEGRITY_READY`.

Exact-head acceptance:
- source compile: PASS;
- Opportunity Lab stdlib suite: **98/98 PASS** (`Ran 98 tests in 0.036s`, `OK`);
- focused run `35079951558`: SUCCESS;
- P2P Shield run `35079951531`: SUCCESS;
- PR #180 remains unmerged despite deterministic success because deterministic success is not market evidence.

Validated refusal/hardening coverage includes:
- mixed-currency direct FX with provenance/date and no silent inverse/triangulation;
- named-base percentage surcharges;
- minimum charge;
- scoped origin/main/destination charges;
- bundle/all-in semantics and double-count protection;
- explicit optional/add-on selection;
- multi-equipment FCL completeness;
- route/equipment alias provenance;
- charge-coverage completeness;
- quote validity and malformed-date refusal;
- unresolved `subject to` commercial terms;
- contradictory FX evidence refusal;
- missing percentage-base provenance refusal;
- input-order invariance;
- duplicate `quote_id` rejection before grouping/FX in both core and validated entrypoints.

Internal stop condition:
- do not broaden speculative pricing semantics merely to add features;
- further deterministic hardening should be triggered by real participant/real quote evidence exposing a concrete missing semantic.

Owner authorization from chat remains valid:
- outreach may target only the first three approved candidates.

Durable outreach truth:
- authenticated Reddit write/post action has still not been available in the working session;
- `sent=0`;
- `reply=0`;
- `opt_in=0`;
- therefore no candidate reply may be claimed yet.

External validation is now the highest-value next evidence:
`authorized outreach -> real quote set -> concierge comparison -> corrections/trust objections -> repeat use -> explicit WTP/payment -> market-gate re-evaluation`.

Do not convert prospect interest, praise, desk research, synthetic fixtures, deterministic tests, or repeat use alone into payment/WTP evidence. BUILD still requires observed real-world experiment success plus observed willingness-to-pay/payment evidence.

Do not merge PR #180 merely to compensate for the missing standalone-repository or Reddit-write capability. Standalone `p2p-opportunity-lab` remains tracked separately in Issue #181.

### 2.3 Project visibility into Control Tower

Projects MAY inspect durable Control Tower artifacts when those artifacts are available through the canonical P2P repository or an explicitly supplied handoff packet. This is a coordination/read-context capability, not authority inheritance.

Allowed:
- read durable Control Tower reconciliation files, successor packets, ReturnPackets, execution-ledger references and project-relevant routing context;
- use them to discover current project status, known blockers, pending Owner Gates and durable evidence references;
- use them to avoid asking the Owner to reconstruct previous chat history.

Not allowed:
- treating a Control Tower chat transcript, hidden conversation state or narrative recollection as canonical truth;
- using Control Tower state to override fresh project repository state, the Supreme Law, evidence authority, task state or existing ledgers;
- inheriting another project's permissions, Owner approvals, secrets, host lane or execution state merely because Control Tower mentions them;
- allowing a project to become a second Control Tower, second router, second ledger or second authority;
- mutating canonical Control Tower/project state through ad-hoc chat memory rather than the existing bounded return/ingest/ledger paths.

Required read rule for project executors:
`CONTROL_TOWER_CONTEXT -> REFERENCE_ONLY_UNTIL_RECONCILED`.

Before acting on material Control Tower information, a project must fresh-check its own durable repo/project state and the applicable canonical P2P law/evidence. If the Control Tower statement and fresh durable project truth differ, fresh durable truth wins and the mismatch is returned for reconciliation.

This preserves the intended direction:
`PROJECTS <-> CONTROL TOWER for coordination`, while `CANONICAL REPO + PROJECT STATE + EVIDENCE + GOVERNANCE` remain authority.

## 3. Control Tower instructions after this update

1. Fresh-check `main`, the Supreme Law, adoption ledger, research appendix and open PRs before acting.
2. Treat this file as a reconciliation pointer, not a replacement for canonical ledgers or live GitHub state.
3. Do not reopen or duplicate work already completed in Section 1 unless fresh evidence shows a regression or measured gap.
4. Do not silently activate deferred/research-only/project-candidate tools merely because they appear in `github research.txt` or this update.
5. For PR #187, reconcile current mergeability/drift with current main and require exact-head Evidence-First proof before merge.
6. For PR #180, preserve `VALIDATE`; internal deterministic hardening is sufficient for the current pilot and the next valuable evidence should come from real users/real quote sets rather than speculative feature breadth.
7. Keep Opportunity Lab separate from normal product implementation: Opportunity Lab decides `SHOULD WE BUILD?`; normal P2P build begins only after market evidence supports `BUILD`.
8. Project executors may read durable Control Tower artifacts for coordination, but must reconcile them with fresh project/canonical truth and may never inherit authority from Control Tower chat state.
9. Preserve native-first capability selection, single-router/single-ledger/single-authority rules, and Owner Gates.
10. Do not ask the Owner to reconstruct old chat history; use durable GitHub state and this reconciliation as the starting map.

## 4. Reconciliation markers

`CONTROL_TOWER_UPDATE_DATE=2026-09-16`

`CONTROL_TOWER_UPDATE_SCOPE=RECENT_P2P_RESEARCH_RUNTIME_EVIDENCE_EVOLUTION_PLUS_OPPORTUNITY_LAB`

`CONTROL_TOWER_LATEST_MAIN_CHECK=f61e9884c1d1fbfa9f4736d1425740dee11017e7`

`EXPERIENCE_EVOLUTION=MERGED_COMPLETE`

`EVIDENCE_FIRST=MERGED_IMPLEMENTED`

`NATIVE_CODE_IMPACT_REALPATH_PROVEN=YES`

`EXTERNAL_CODE_INTELLIGENCE_ROLE=OPTIONAL_EXTENSION_NATIVE_FIRST`

`OPIK=IMPLEMENTED_DEFAULT_OFF`

`GRAPHITI=RESEARCH_ONLY`

`MISSION_CONTROL=REJECTED_AS_SECOND_AUTHORITY`

`PR_187=OPEN_UNMERGED_RECONCILE_MERGEABILITY`

`PR_180=OPEN_UNMERGED_VALIDATE_NOT_BUILD`

`OPPORTUNITY_LAB_HEAD=5ca5f6b042a16f261b2f0d351e41b1dd844111d8`

`OPPORTUNITY_LAB_TESTS=98_OF_98_PASS`

`OPPORTUNITY_LAB_SHIELD=SUCCESS`

`OPPORTUNITY_INTERNAL_STOP=WAIT_FOR_REAL_EVIDENCE`

`OPPORTUNITY_OUTREACH_SENT=0`

`OPPORTUNITY_REPLY=0`

`PROJECT_CONTROL_TOWER_VISIBILITY=READ_DURABLE_CONTEXT_ALLOWED_RECONCILE_REQUIRED`

`CONTROL_TOWER_CHAT_IS_AUTHORITY=NO`

`OWNER_RECONSTRUCTION_REQUIRED=NO`
