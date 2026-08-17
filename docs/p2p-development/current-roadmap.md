# P2P Current Development Roadmap

> **Canonical source declaration.** This document is a **derived, human-readable projection**. It must never be edited as a source of truth.
> - Goal/development governance truth: `governance/development-control.json` (`current_development`, `candidate_records`, `roadmap`, `capability_status`, `research_decisions`).
> - Capability knowledge truth: `docs/p2p-development/capability-ledger/capability-index.json` (this directory).
> - Charter truth: `docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md`.
> If this file disagrees with any canonical source, the canonical source wins. Regenerate this file whenever governance or the ledger changes.

**Generated:** 2026-08-17 by the P2P-C26/C27 durable development session (derived, not authored-by-hand as a decision document).

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
| **C27** | **BLOCKED** (`LIVE_HOST_EVIDENCE_UNAVAILABLE`) | Certification machinery delivered (`scripts/p2p_live_certification.py`, LH1–LH35) | NOT_CERTIFIED — see honesty record §2a |
| **C28** | **PLANNED** (machinery `FOUNDATION_READY`; no live certification claimed) | Connection & credential onboarding machinery (`scripts/p2p_secure_onboarding.py`, HO1–HO50) | FOUNDATION_READY — see §3d |

> **Honesty note on C22–C24 (updated 2026-08-17).** The C25 handoff prompt expected C24 = DONE/PASS with candidate `P2P-8-4-7-C-codex-24-evidence-backed-multi-host-adapter-conformance-candidate-v1.zip` (SHA `6c5b3b29fbaaab6df0b9f0c8a2f88ff579390b3b060c5c0d2f076cadec37d879`). That candidate did not exist in this copy of the project at C25 time and the C22–C24 progression was marked not-recovered. During C26, the owner supplied the C23 and C24 candidate packages, and their SHA-256 values **verified against the expected digests** (C24 matches the handoff digest exactly; C23 is verified against the governance record in the C23 package). The C22 package was **not** supplied and remains unrecovered. Per the reconciliation rule, history is not rewritten: `C22_C24_ADAPTER_LIVE_CERTIFICATION` keeps status `UNKNOWN` with the recovered package references added as `RECOVERED_LEGACY` provenance. Package contents were never durably certified against the original implementations, so **no live certification claim is made**.

## 3. Capability landscape snapshot (from the ledger)

Counts per family in `capability-index.json` at generation time (131 records, 12 families):

| Family | Count | Dominant statuses |
| --- | --- | --- |
| Truth & Governance | 14 | VERIFIED_IMPLEMENTED |
| Durable Project Intelligence | 10 | mix, incl. rejected-pattern preservation |
| Context & Knowledge | 35 | VERIFIED_IMPLEMENTED + FOUNDATION_READY + 20 owner-accepted PLANNED intakes |
| Skill & Learning | 5 | VERIFIED_IMPLEMENTED |
| Execution & Orchestration | 15 | VERIFIED_IMPLEMENTED + rejected patterns |
| Design & Product Intelligence | 6 | VERIFIED_IMPLEMENTED |
| Multi-AI Interoperability | 21 | FOUNDATION_READY + UNKNOWN (C22–C24 gap + C27 machinery) + C28 onboarding |
| Routing & Cognitive Economy | 4 | mix |
| Verification & Evaluation | 6 | VERIFIED_IMPLEMENTED |
| Recovery & Continuation | 5 | mix |
| Beginner Lifecycle | 7 | mix |
| Outcome Learning | 3 | mix |

Status vocabulary used by the ledger: `VERIFIED_IMPLEMENTED`, `FOUNDATION_READY`, `PARTIAL`, `PLANNED`, `DEFERRED`, `REJECTED`, `OBSOLETE`, `UNKNOWN`.

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

## 5. Recommended next goals (ordered, NOT auto-started)

Ordering follows the ledger's dependency graph and governance's `research_decisions`. Starting any goal still requires a new chat, an owner prompt, and that goal's own evidence contract. No goal starts automatically.

1. **C27/C28 completion — live host certification with real credentials (BLOCKED, awaiting owner action).** The largest remaining evidence gap: live certification of a real AI host (Codex CLI target; also Manus/Codex adapters). The C27 session delivered the certification machinery and an honest host-by-host blocked record; the C28 session delivered the secure connection onboarding layer that makes resuming cheap and beginner-safe. Resuming requires only one irreducible Owner action performed outside chat: sign in to Codex (`codex login` with a real account) or configure the Manus API connector — then say "continue" and P2P re-verifies automatically (zero new technical burden). Resolves the `C22_C24_ADAPTER_LIVE_CERTIFICATION`, `REAL_HOST_EXECUTION_CERTIFICATION`, and Codex `AUTH_INVALID` records.
2. **C29 — Live delegation and parallel execution certification.** Depends on C27 evidence. Upgrades `DELEGATION` and `PARALLEL_EXECUTION` from `FOUNDATION_READY`.
3. **C30 — Cross-host continuation and round-trip binding.** Depends on C27/C28. Upgrades `CROSS_HOST_CONTINUATION_CONTRACT`, `ROUND_TRIP_BINDING`, `CROSS_HOST_RESUME`.
4. **C31 — Beginner control center view layer.** Depends on nothing new; beginner-friendly dashboard for status/decisions (control center, health views, decision inbox).
5. **C32 — Context/session/cache efficiency implementation (first batch).** Owner-accepted intakes (§3a); pick the batch with the strongest beginner value and dependency readiness, with one primary objective per goal contract.
6. **Roadmap hygiene (ongoing):** reconcile the recovered C23/C24 packages' internals against the original implementations, and search for the C22 package in other copies the owner may hold, before claiming progression beyond recovery-level provenance.

## 6. Regeneration rule

Any session that changes `development-control.json`, `capability-index.json`, or the charter must regenerate this file so that the projection never drifts from its sources.
