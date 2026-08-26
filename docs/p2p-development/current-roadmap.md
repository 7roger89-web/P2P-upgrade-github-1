# P2P Current Development Roadmap

> **Canonical source declaration.** This document is a **derived, human-readable projection**. It must never be edited as a source of truth.
> - Goal/development governance truth: `governance/development-control.json` (`current_development`, `candidate_records`, `roadmap`, `capability_status`, `research_decisions`).
> - Capability knowledge truth: `docs/p2p-development/capability-ledger/capability-index.json` (this directory).
> - Charter truth: `docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md`.
> If this file disagrees with any canonical source, the canonical source wins. Regenerate this file whenever governance or the ledger changes.

**Generated:** 2026-08-26 (P2P-CT01 ledger projection refresh; derived, not authored-by-hand as a decision document).

## 6. Framework goals (FW series)

**FW01 — Durable Project Bootstrap & Fresh-Clone Certification.** The v1 release `p2p-8.4.7-C-codex.24-fw01-v1` (tag `p2p-8.4.7-C-codex.24-fw01-v1`, asset SHA `eb396dc1…3d7d`) was reconciled mechanically: `DOCTOR_PATH_RESOLUTION_BUG` (failure class E) plus a package-layout inventory defect (152/152 `source-inventory.json` mismatches, supplemental catalog and EXT-0002 hash failures) make it not self-validating on a genuinely fresh machine (`EXTERNAL_DEV_PATH_DEPENDENCY` cannot be certified 0; the mint-time `doctor_canonical` gate passed only against staged source). Both defects are closed in exactly one unpromoted candidate built through the canonical candidate machinery: `P2P-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip` (SHA-256 `2a42e815ca44fbecce4d8f35a641529e8cad028f07dccc5800bae00e3f509e61`), which achieves `CANONICAL_INSTALL=PASS`, `DOCTOR=HEALTHY`, `EXTERNAL_DEV_PATH_DEPENDENCY=0` on a fresh machine and is certified on Game Truyện and Gia Phả fresh clones (mutation 0 for GP; GT's only tracked change is the installer-owned `AGENTS.md` merge surface). The reusable bootstrap design (`docs/p2p-development/P2P-PROJECT-BOOTSTRAP.md` + `scripts/p2p-bootstrap.sh`) was recreated on this lineage. Gates remaining: **OWNER_PATCH_RELEASE_GATE** (publish tag/release of candidate v2, bind GT/GP production manifests) and the earlier GT/GP integration-push gate. Negative suite 10/10 (v1 stays BLOCKED, rc 7), validator 78/78, `validate_control` PASS, gitleaks clean, `NEW_UNEXPLAINED_FAILURES=0`. No FRAMEWORK-02 opened; no push, no promotion.

## 1. Official baseline

| Item | Value |
| --- | --- |
| Official baseline version | `8.4.7-C-codex.19` |
| Baseline SHA-256 | `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8` |
| Promotion status | `PROMOTED_VERIFIED` |
| Source version (working tree) | `8.4.7-C-codex.21` |

## 2. Candidate lineage (from `development-control.json`)

| Goal | Status in governance | Candidate artifact | Promotion |
| --- | --- | --- | --- |
| C07 | DONE | — | — |
| C08 | **DEFERRED** | — | — |
| C09 | **BLOCKED** (`EVENT_EVIDENCE_UNAVAILABLE`) | — | — |
| C10 | DONE | — | — |
| C11 | DONE | — | — |
| C12 | DONE | — | — |
| C13 | DONE | — | — |
| C14 | DONE | — | `PROMOTED_VERIFIED` (baseline 8.4.7-C-codex.19) |
| C15 | DONE | — | — |
| C16 | DONE | — | — |
| C17 | DONE | — | — |
| C18 | DONE | — | — |
| C19 | DONE | `P2P-8.4.7-C-Codex-Edition-v21-c19-cross-platform-reconciled-final-candidate.zip` | **UNPROMOTED** (PASS) |
| C20 | DONE (foundation) | `P2P-8.4.7-C-Codex-Edition-v21-c20-host-executor-neutrality-foundation-final-candidate.zip` | UNPROMOTED |
| C21 | DONE (foundation) | `P2P-8.4.7-C-Codex-Edition-v21-c21-compatible-host-discovery-selection-foundation-final-candidate-v2.zip` | UNPROMOTED (`HOST_SELECTION_POLICY_FOUNDATION_READY`) |
| C22 | NOT RECORDED in this copy; package not recovered | No candidate found in `reports/candidates/` | Not recovered |
| C23 | DONE in governance lineage (record recovered) | `P2P-8-4-7-C-codex-23-c23-portable-ai-continuation-round-trip-candidate-v1.zip` (owner-supplied, SHA-256 verified: `8303efa866e9a6b1e33b94e4fe9e5c2afd0bfd71b6fe9a1344f53731f33fc7d1`) | UNPROMOTED — recovery did not durably certify implementation |
| C24 | DONE in governance lineage (record recovered) | `P2P-8-4-7-C-codex-24-c24-evidence-backed-multi-host-adapter-conformance-candidate-v1.zip` (owner-supplied, SHA-256 verified: `6c5b3b29fbaaab6df0b9f0c8a2f88ff579390b3b060c5c0d2f076cadec37d879`) | UNPROMOTED — recovery did not durably certify implementation |
| **C25** | DONE | `P2P-8.4.7-C-Codex-Edition-v21-c25-durable-development-charter-ledger-framework-candidate.zip` | UNPROMOTED |
| **C26** | **DONE** — candidate built and verified | `P2P-8.4.7-C-Codex-Edition-v21-c26-durable-capability-provenance-goal-ledger-dependency-governance-candidate-v1.zip` (verify PASS) | UNPROMOTED |
| **C27** | **BLOCKED** (`LIVE_HOST_EVIDENCE_UNAVAILABLE`) + reopen_condition metadata | Certification machinery delivered (`scripts/p2p_live_certification.py`, LH1–LH35); status audited to FOUNDATION_READY by C29 with real-execution evidence | NOT_CERTIFIED — see honesty record §2a |
| **C28** | **DONE** (terminal PASS — machinery; no live certification claimed) | `P2P-8.4.7-C-Codex-Edition-v22-c28-secure-host-connection-credential-onboarding-candidate-v1.zip` (built + verify PASS; SHA-256 recorded in governance) | UNPROMOTED — see §2a |
| **C29** | **DONE** (terminal PASS — goal closure & durable state integrity) | Closure checker `scripts/p2p_goal_closure.py` (GC1–GC50), validator extensions V18–V21, templates v3; candidate `P2P-8.4.7-C-Codex-Edition-v23-c29-goal-closure-durable-state-integrity-candidate-v1.zip` | UNPROMOTED — no further goal auto-started (stop after PASS) |

> **Honesty note on C22–C24 (updated 2026-08-17).** The C25 handoff prompt expected C24 = DONE/PASS with candidate `P2P-8-4-7-C-codex-24-evidence-backed-multi-host-adapter-conformance-candidate-v1.zip` (SHA `6c5b3b29fbaaab6df0b9f0c8a2f88ff579390b3b060c5c0d2f076cadec37d879`). That candidate did not exist in this copy of the project at C25 time and the C22–C24 progression was marked not-recovered. During C26, the owner supplied the C23 and C24 candidate packages, and their SHA-256 values **verified against the expected digests** (C24 matches the handoff digest exactly; C23 is verified against the governance record in the C23 package). The C22 package was **not** supplied and remains unrecovered. Per the reconciliation rule, history is not rewritten: `C22_C24_ADAPTER_LIVE_CERTIFICATION` keeps status `UNKNOWN` with the recovered package references added as `RECOVERED_LEGACY` provenance. Package contents were never durably certified against the original implementations, so **no live certification claim is made**.

### 2a. C28 candidate record (deterministic policy application)

| Field | Value |
| --- | --- |
| Candidate ID | `C28` |
| Label | `P2P-8.4.7-C-Codex-Edition-v22-c28-secure-host-connection-credential-onboarding-candidate-v1.zip` |
| Based on official version / SHA-256 | `8.4.7-C-codex.19` / official baseline digest named |
| Candidate version / embedded | `8.4.7-C-codex.22` |
| Promotion status | `UNPROMOTED` |
| Lineage status | verify PASS; full lineage verify pending owner action (`codex login` / Manus connector) |

The record exists because the candidate requirement is a **deterministic policy**: the C28 contract declared a candidate required on PASS with governance/runtime changes, and those signals were present. The record was created mechanically, not by terminal-time AI judgment, and the closure checker reports the same answer on every surface.


## 3. Capability landscape snapshot (from the ledger)

Counts per family in `capability-index.json` at regeneration time (176 records, 12 registered families; 3 residual records use unregistered legacy family labels):
| Family | Count | Dominant statuses |
| --- | --- | --- |
| Truth & Governance | 22 | VERIFIED_IMPLEMENTED + FOUNDATION_READY |
| Durable Project Intelligence | 12 | VERIFIED_IMPLEMENTED + FOUNDATION_READY |
| Context & Knowledge | 39 | PLANNED + VERIFIED_IMPLEMENTED |
| Skill & Learning | 5 | VERIFIED_IMPLEMENTED + PARTIAL |
| Execution & Orchestration | 28 | VERIFIED_IMPLEMENTED + FOUNDATION_READY |
| Design & Product Intelligence | 7 | VERIFIED_IMPLEMENTED + REJECTED |
| Multi-AI Interoperability | 32 | FOUNDATION_READY + REJECTED |
| Routing & Cognitive Economy | 4 | FOUNDATION_READY + VERIFIED_IMPLEMENTED |
| Verification & Evaluation | 7 | VERIFIED_IMPLEMENTED + FOUNDATION_READY |
| Recovery & Continuation | 6 | FOUNDATION_READY + VERIFIED_IMPLEMENTED |
| Beginner Lifecycle | 7 | VERIFIED_IMPLEMENTED + PARTIAL |
| Outcome Learning | 4 | VERIFIED_IMPLEMENTED + FOUNDATION_READY |
Status vocabulary used by the ledger: `VERIFIED_IMPLEMENTED`, `FOUNDATION_READY`, `PARTIAL`, `PLANNED`, `DEFERRED`, `REJECTED`, `OBSOLETE`, `UNKNOWN`.

Registered-family subtotal is 172 records. Three inherited records remain visible under the unregistered legacy family labels `RELEASE_INSTALL_PROJECT_LIFECYCLE`, `SAFETY_AUTHORITY_PERMISSIONS`, and `OBSOLESCENCE_CAPABILITY_DRIFT`; C43 reports them as residual schema drift rather than silently moving or deleting them.


### 3a. Owner-accepted context/session capability intake (C26, 20 records, all `PLANNED`)

These are owner-accepted proposals recorded on 2026-08-17 with `origin_type: OWNER_ACCEPTED_PROPOSAL`. They represent roadmap intent only — acceptance in chat is **never** equivalent to implementation (`OWNER_ACCEPTS_CAPABILITY != CAPABILITY_IMPLEMENTED`). Runtime work for any of them is out of scope for C26 and would require its own goal with its own evidence contract.

`TASK_SESSION_BOUNDARY_MANAGEMENT`, `SESSION_REUSE_DECISION`, `SESSION_CONFIGURATION_STABILITY`, `CACHE_AFFECTING_CONFIGURATION_FINGERPRINT`, `CACHE_HIT_TELEMETRY`, `CONTEXT_PRESSURE_MONITORING`, `SAFE_CONTEXT_COMPACTION`, `DURABLE_PRE_COMPACTION_CHECKPOINT`, `BOUNDED_TOOL_OUTPUT`, `RAW_OUTPUT_ARTIFACT_OFFLOADING`, `VERBOSE_WORK_CONTEXT_ISOLATION`, `SUBAGENT_CONTEXT_ISOLATION`, `TASK_TARGETED_TOOL_LOADING`, `TASK_TARGETED_MCP_LOADING`, `TASK_TARGETED_SKILL_LOADING`, `CODE_INTELLIGENCE_FIRST_NAVIGATION`, `SYMBOL_AWARE_RETRIEVAL`, `CONTEXT_COST_TELEMETRY`, `QUALITY_ADJUSTED_CONTEXT_OPTIMIZATION`, `CACHE_AWARE_MODEL_EFFORT_STABILITY`.

No record was created where the ledger already covers the concept (`CACHE_AWARE_CONTEXT_REUSE`-adjacent records, `PROGRESSIVE_DISCLOSURE`-family, `BOUNDED_EXECUTION` for bounded tool output behavior), and `do_not_duplicate_with` cross-references are recorded on the relevant records.

### 3d. C28 secure host connection & credential onboarding

C28 delivered the minimum provider-neutral connection/onboarding layer required to turn a discovered-but-unusable host into a securely connected, verified, **live-probe-eligible** host candidate — without exposing secrets, inventing authentication, or retrying C27 automatically. The state model preserves the full boundary `HOST_EXISTS → AUTH REQUIREMENT KNOWN → SECRET SAFELY CONFIGURED OUTSIDE CHAT → AUTH VERIFIED → PERMISSION VERIFIED → CONNECTION READY → LIVE PROBE ELIGIBLE`; the credential model stores only references (type/source/reference/presence/verification), never secret values; endpoint binding detects `AUTH_CONFIG_PRESENT`-but-`AUTH_TARGET_MISMATCH` (the exact failure mode C27 encountered with Codex); verification uses the cheapest safe method (zero model calls in this session); a beginner owner-action model emits exactly one minimal external action per host (`codex login`, no API keys in chat); drift degrades `CONNECTION_READY → AUTH_VERIFICATION_REQUIRED`; and the machine-readable doctor exposes all of this for future goals. Result: **PASS (machinery only)** — `SECURE_HOST_CONNECTION_ONBOARDING = FOUNDATION_READY`; no host reached `LIVE_PROBE_ELIGIBLE` because no real auth session exists in this environment (Codex remains `AUTH_INVALID` per the durable C27 evidence).

### 3b. C27 honesty record (live host certification)

C27 required proving control of a **real** AI host (bounded non-destructive probe, execution binding, independent result verification, reconciliation). Host-by-host discovery: OpenAI **Codex CLI 0.147.0 installed but unreachable** — every probe attempt hits `api.openai.com` 401 Unauthorized (the sandbox `OPENAI_API_KEY` is a Manus proxy credential the Responses API does not accept; default/never-approval/danger-sandbox/local-provider configurations all failed **pre-model-contact**, mutation `KNOWN_NONE`, quarantined). Claude Code, Gemini CLI, Cursor ACP, and Copilot CLI are not installed and have no credentials; the Manus API connector is not configured in this session; the own proxy runtime is excluded by rule (self-referential, not an externally controlled host). Result: **BLOCKED / NOT_CERTIFIED** — no fabricated PASS (`unknown-remains-unknown`). The machinery is the certified pathway (`REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY` on the ledger) for a future session with accepted credentials.

### 3c. Dependency-aware gaps

The ledger now makes prerequisite reasoning explicit: every record declares `dependencies` (100% field presence; empty list means none). Verified-implementation candidates remain gated on prerequisites, e.g. the C22–C24 adapter/delegation gap gates `DELEGATION`, `PARALLEL_EXECUTION`, `CROSS_HOST_CONTINUATION_CONTRACT`, and `ROUND_TRIP_BINDING` upgrades; `C22_C24_ADAPTER_LIVE_CERTIFICATION` (`UNKNOWN`) is a prerequisite dependency of several execution-family records and is flagged by the validator as a blocked prerequisite.

## 4. Ready-now foundations (declared ready by governance)

- `TASK_TARGETED_CONTEXT_RETRIEVAL_FOUNDATION_READY` (C19)
- `CONTEXT_COVERAGE_ACCOUNTING_READY` (C19)
- `CACHE_AWARE_CONTEXT_REUSE_FOUNDATION_READY` (C19)
- `PORTABLE_EXECUTION_ENVELOPE_READY`, `PORTABLE_RESULT_RECEIPT_READY`, `CROSS_HOST_CONTINUATION_CONTRACT_READY` (C20)
- `HOST_REQUIREMENT_PROFILE_READY`, `HOST_CAPABILITY_DISCOVERY_FOUNDATION_READY` (C21)
- `HOST_SELECTION_POLICY_FOUNDATION_READY` (C21)
- `TASK_TARGETED_STATE_ARCHITECTURE_FOUNDATION_READY`, `RECOVERY_TESTABILITY_FOUNDATION_READY`, `TASK_STATE_RECOVERY_IMPLEMENTED` (C13/C19 lineage)
- `DURABLE_PROJECT_TRUTH_PACKAGING_FOUNDATION_READY` (C25)
- `AI_EXECUTION_RELIABILITY_GUARD` (AERG reconciliation foundation; evidence/assurance only, not release authority)

- CONTROL_TOWER_SESSION_HANDOFF_FOUNDATION_READY (P2P-CT01 local technical proof; UNPROMOTED)

### P2P-CT01 durable Control Tower session handoff foundation

P2P-CT01 adds a provider-neutral, explicit session binding and structured return packet over the existing host executor, task state, evidence, and execution-ledger boundaries. The packet supports terminal returns, stale/unknown-base reconciliation, owner-gate recording, failure return, host-lane isolation, attachment-aware `UPLOAD_REQUIRED` manifests, and recursive copy/paste continuation. It does not launch hosts, infer authority from prose, inherit chat history, treat a local path as readable contents, treat an attachment as canonical truth, overwrite canonical state, promote, release, or certify a live provider. Local proof is 22 focused tests, including 7 attachment-aware cases; the capability remains FOUNDATION_READY and UNPROMOTED.

### 3e. C30 composable execution target foundation (2026-08-17)
C30 delivered the **provider-neutral, deterministic composable execution target foundation** — `scripts/p2p_execution_target.py` — with 60 passing tests (`tests/test_p2p_execution_target.py` ET1..ET60) and a durable research intake artifact (`docs/p2p-development/research/execution-target-pattern-research.md`, nine source repositories, patterns A–O, no code copied). The module models execution as an honest composition of a harness, a provider, a model, a protocol, a toolset, a workspace, an environment, auth (harness and provider kept separate), and a permission envelope; `UNKNOWN` and stale evidence fail closed, protocol compatibility is never certification, permission composition never widens, and the registry enumerates but never routes. Honest gaps are durably recorded: no router, no autopilot, no background autonomy, no real execution, no second executor, and no secrets stored. Terminal state: **PASS (foundation)**, candidate UNPROMOTED per the C29 deterministic policy.

### 3e. C30 composable execution target foundation (2026-08-17)
C30 delivered the **provider-neutral, deterministic composable execution target foundation** — `scripts/p2p_execution_target.py` — with 60 passing tests (`tests/test_p2p_execution_target.py` ET1..ET60) and a durable research intake artifact (`docs/p2p-development/research/execution-target-pattern-research.md`, nine source repositories, patterns A–O, no code copied). The module models execution as an honest composition of a harness, a provider, a model, a protocol, a toolset, a workspace, an environment, auth (harness and provider kept separate), and a permission envelope; `UNKNOWN` and stale evidence fail closed, protocol compatibility is never certification, permission composition never widens, and the registry enumerates but never routes. Honest gaps are durably recorded: no router, no autopilot, no background autonomy, no real execution, no second executor, and no secrets stored. Terminal state: **PASS (foundation)**, candidate UNPROMOTED per the C29 deterministic policy.

### 3e. C30 composable execution target foundation (2026-08-17)
C30 delivered the **provider-neutral, deterministic composable execution target foundation** — `scripts/p2p_execution_target.py` — with 60 passing tests (`tests/test_p2p_execution_target.py` ET1..ET60) and a durable research intake artifact (`docs/p2p-development/research/execution-target-pattern-research.md`, nine source repositories, patterns A–O, no code copied). The module models execution as an honest composition of a harness, a provider, a model, a protocol, a toolset, a workspace, an environment, auth (harness and provider kept separate), and a permission envelope; `UNKNOWN` and stale evidence fail closed, protocol compatibility is never certification, permission composition never widens, and the registry enumerates but never routes. Honest gaps are durably recorded: no router, no autopilot, no background autonomy, no real execution, no second executor, and no secrets stored. Terminal state: **PASS (foundation)**, candidate UNPROMOTED per the C29 deterministic policy.

## 5. Recommended next goals (ordered, NOT auto-started)

Ordering follows the ledger's dependency graph and governance's `research_decisions`. Starting any goal still requires a new chat, an owner prompt, and that goal's own evidence contract. No goal starts automatically.

1. **C27/C28 completion — live host certification with real credentials (reopen condition, metadata only, never auto-executed).** The largest remaining evidence gap: live certification of a real AI host (Codex CLI target; also Manus/Codex adapters). The C27 session delivered the certification machinery and an honest host-by-host blocked record; the C28 session delivered the secure connection onboarding layer that makes resuming cheap and beginner-safe. Reopen condition (durably recorded on the C27 roadmap item): at least one real host reaches `connection_status AUTH_REQUIRED` or stronger (live probe eligible). Meeting it still requires one irreducible Owner action performed outside chat — sign in to Codex (`codex login` with a real account) or configure the Manus API connector — then say "continue" in a new chat and P2P re-verifies automatically. Resolves the `C22_C24_ADAPTER_LIVE_CERTIFICATION`, `REAL_HOST_EXECUTION_CERTIFICATION`, and Codex `AUTH_INVALID` records.
2. **C31 — Cross-host continuation and round-trip binding.** Depends on C27/C28. Upgrades `CROSS_HOST_CONTINUATION_CONTRACT`, `ROUND_TRIP_BINDING`, `CROSS_HOST_RESUME`.
3. **C32 — Beginner control center view layer.** Depends on nothing new; beginner-friendly dashboard for status/decisions (control center, health views, decision inbox).
4. **C33 — Context/session/cache efficiency implementation (first batch).** Owner-accepted intakes (§3a); pick the batch with the strongest beginner value and dependency readiness, with one primary objective per goal contract.
5. **Roadmap hygiene (ongoing):** reconcile the recovered C23/C24 packages' internals against the original implementations, and search for the C22 package in other copies the owner may hold, before claiming progression beyond recovery-level provenance.

## 6. Regeneration rule

Any session that changes `development-control.json`, `capability-index.json`, or the charter must regenerate this file so that the projection never drifts from its sources.

### 3f. C31 live host certification — honest BLOCKED (2026-08-17)

C31 attempted to close the highest-priority evidence gap left after C30: an honest **live** certification of one real execution path using the generic C30 execution-target contract and the existing C27/C28 machinery (no parallel certification system, no vendor-specific core). The environment was inspected from observable evidence only: Codex CLI 0.147.0 is installed; the sandbox `OPENAI_API_KEY` is a Manus proxy credential; **no** Manus project connector is enabled; Claude/Gemini/Cursor/Copilot are absent (confirming C27 evidence). A fresh, non-destructive, zero-model-contact probe (`evidence/c31_live_probe.json`, fingerprint `5e3364ee…854b`) reached Codex's own auth layer and returned **HTTP 401 Unauthorized before model contact** — verdict `AUTH_INVALID`. The Manus connector path is `AUTH_CONFIG_ABSENT`. Terminal verdict: **BLOCKED / OWNER_ACTION_REQUIRED**. The smallest owner actions are a real `codex login` (outside chat, no secrets in chat) or enabling the Manus project connector in session configuration; certification reopens only when a fresh probe returns `AUTH_REQUIRED` or stronger on a supported host. Per the honesty boundary, no live certification record was fabricated: ledger and governance carry only the honest BLOCKED state, and no candidate release artifact was minted (`NOT_APPLICABLE_BLOCKED`). `AUTHENTICATED != CERTIFIED`; `UNKNOWN != SUPPORTED`; `GOAL PASS != PROMOTION`.
