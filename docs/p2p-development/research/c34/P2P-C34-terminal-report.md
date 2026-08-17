<!-- NON_CANONICAL / IMPLEMENTATION_EVIDENCE / NOT_PROMOTED -->
# P2P-C34 Terminal Report
**Goal name:** Real Backend Contract Validation + Control-Plane Hardening
**Terminal verdict:** `PARTIAL / SINGLE_BACKEND_VALIDATED` (SINGLE PARTIAL; `REAL_BACKEND_CONTRACT_VALIDATED` retained as subordinate capability label)
**Mode:** Large implementation goal, continuous bounded execution, checkpoint-driven
**Author:** P2P-C34 Implementation (Manus AI)
**Date:** 2026-08-17 (GMT+7)
**Branch:** `p2p-c34-real-backend-contract-validation` based on `p2p-c33-bounded-autopilot-core @ 2a000e0`
**Addendum applied:** P2P Capability Preservation Addendum (sections A–Z)
---
## 1. Terminal Verdict
```
PARTIAL / SINGLE_BACKEND_VALIDATED
```
The C33 AutoPilot core loop (proven over a fake backend) is now **contractually bound to real execution backends**, with one backend **live-certified against a real API** and one backend **honestly auth-blocked**. Per the closure normalization rule, a goal that validates exactly one real backend and none more is `PARTIAL / SINGLE_BACKEND_VALIDATED`; the capability label `REAL_BACKEND_CONTRACT_VALIDATED` is preserved as subordinate vocabulary, not as a second PARTIAL lane. Concretely:

- **Manus adapter: `LIVE_VALIDATED`** — a real bounded task was created, executed, stopped, and verified through the Manus API with owner-supplied credentials (`task.create` → bounded poll → `task.listMessages`). Answer evidence ("Four"), usage evidence (`credit_usage: 0`), request/receipt binding, and immutable evidence files were all produced by the adapter contract.
- **Hermes adapter: `ADAPTER_VALIDATED_AUTH_BLOCKED`** — Hermes v0.20.2 (2026.8.16) was installed and its headless CLI interface (`hermes -z`) was probe-verified on this host. No provider credentials exist in the environment, so the first real invocation returned HTTP 403 "Access denied", which the adapter normalized to `FAILED / AUTH_INVALID` with USAGE_EVIDENCE surface still produced. Success was not fabricated; the classification is deliberate.

Control-plane hardening shipped alongside: a conformance contract (`backend_contract.py`, closure-extended with capability-scoped certification vocabulary and requested-vs-observed attestation binding), a vendor-free bridge into the C33 core (`backend_execution_bridge.py`), registry-≠-router enforcement, canonical-council invariants, state-family collision prevention, a candidate-policy runtime-detection correction, and the deterministic C33 candidate consequence (unpromoted record persisted). **Zero new adapter/bridge/certification test failures**: the C34 suite is 51 passed / 1 skipped; the post-closure regression is 22 failed / 731 passed / 5 skipped, where the 5 new failures are all the single documented `V15-roadmap-count-sync` root cause (ledger 156→158 from the C34 P0-B registrations) classified `EXPLAINED_DURABLE_SNAPSHOT_DRIFT` (see Section 8 and the machine-readable failure-set evidence).

## 2. What Was Built
Exactly one new bounded capability family — the C34 real-backend contract surface — under `.p2p/system/p2p_capabilities/`, plus one deterministic test module and this research document, plus a two-entry ledger registration. Nothing in `governance/`, `scripts/`, `source/`, the runtime manifest, templates, or the C33 autopilot core was modified in a vendor-specific way.

| Module | Role |
|---|---|
| `backend_contract.py` (432 lines) | Conformance contract: `ADAPTER_STATES` five-state machine (`ARCHITECTURALLY_COMPATIBLE → ADAPTER_IMPLEMENTED → ADAPTER_TESTED → LIVE_CERTIFIED → CURRENTLY_ELIGIBLE`), `BackendAdapterIdentity`/`AdapterHealthState` records, `BackendExecutionResult` (64-hex request fingerprint validation), `normalize_adapter_error` (ten canonical failure classes, `UNKNOWN` fails closed), `verify_request_receipt_binding`, `state_family_schema_for` collision-free durable-state identification |
| `backend_execution_bridge.py` (322 lines) | `BackendExecutionBridge` satisfying the C33 `backend.execute(contract)` duck interface; `BackendAdapterRegistry` (explicit `adapter_id` lookup; no ranking, fallback, cost/quality selection — **registry ≠ router**); fail-closed verification outcomes (`PASS / MUTATION_UNKNOWN / VERIFY_FAIL / CRASH_BEFORE_VERIFY`) |
| `hermes_adapter.py` (402 lines) | `HermesAdapter` driving the real `hermes` CLI: headless `hermes -z <prompt> [--provider --model --usage-file]`, toolset runs via `hermes chat -q --max-turns`; forbidden-flag hardening (never `--yolo`; `cron`/`gateway`/`serve`/`background` subcommands blocked); credential/403/401/rate-limit normalization; USAGE_EVIDENCE via `--usage-file` |
| `manus_adapter.py` (375 lines) | `ManusAdapter` driving the real Manus REST API (`/v2/task.create` → bounded `task.detail` polling → `task.listMessages`); API key is a reference-only secret (never embedded in state); `credit_usage` usage evidence; `agent_profile` bounded to `manus-1.6-lite`; explicit task stop on expiry; transcript remains evidence-only |
| `tests/test_p2p_c34_real_backend_contract.py` (705 lines) | 44 deterministic tests across 13 classes: schema, identity, registration≠routing, differential proof, request/receipt binding (wrong-task + wrong-environment rejection), permission never-widens, secret-reference-only, network≠secret, normalization (local/remote/auth/timeout/unknown fail-closed), verifier authority, no-transcript-as-state, canonical-8 + 8/8 quorum, certified≠eligible, no routing/fallback/background, state-family identification, candidate-policy audit, fresh-clone recovery |
| `docs/p2p-development/research/c34/` | Terminal report, phase probes (Hermes interface probe, Manus API probe, baseline freeze, regression analysis), and durable `evidence/` registry with sha256-anchored Manus probe artifacts |
| `docs/p2p-development/capability-ledger/capability-index.json` | +2 ledger entries: `C34_REAL_BACKEND_CONTRACT` and `C34_STATE_FAMILY_IDENTIFICATION` (closure status `FOUNDATION_READY`, origin `IMPLEMENTATION_GOAL` per the provenance coherence pass) |
| `scripts/p2p_goal_closure.py` | Minimum bounded checker correction: `ChangeSignals.detect` now scans the `.p2p/system/` runtime surface (non-`.md`) — closing the documented C33 blind spot; no requirement weakened, 4 new regression tests (`gc51`–`gc54`) green |
| `governance/development-control.json` | +1 unpromoted `C33` candidate record with deterministic artifact (closure consequence, see Section 11) |

## 3. Execution Evidence (immutable pointers)
```
docs/p2p-development/research/c34/evidence/manus-probe/c34-manus-probe-create.json   sha256 839f59a2...
docs/p2p-development/research/c34/evidence/manus-probe/c34-manus-probe-detail.json   sha256 41e5e669...
docs/p2p-development/research/c34/evidence/manus-probe/c34-manus-probe-messages.json sha256 a58f0bdf...
```
The live Manus probe: real task `8Eqa4QGo4x35raVTPnnA7c`, prompt was a bounded synthetic arithmetic question, the remote agent stopped in ≈11 seconds with `execution_status: SUCCEEDED`, the assistant answer "Four" is preserved verbatim in the messages evidence, `credit_usage: 0`, `possible_mutation: false`, raw receipt pointer retained. The Hermes probe: `hermes v0.20.2` binary verified, headless `-z` interface probed, first real invocation returned 403 → adapter receipt `FAILED / AUTH_INVALID / NO_CREDENTIALS`, usage evidence file still emitted, no daemon/cron/background process created, no `--yolo` ever passed.

## 4. Same-Core Differential Proof
The **identical** P2P task contract (same goal/task/objective/workspace, same permission profile, same verifier) was run through the same `BackendExecutionBridge` with only the **target profile** changing (`hermes-cli` vs `manus-api`). Observed identical: request fingerprint, permission profile, gate sequence, verifier authority, evidence persistence pattern, and task→goal transition mechanics. Observed correctly different (by design): transport shape (CLI argv vs HTTPS REST), provider-specific status vocabulary (mapped to canonical classes), usage evidence fields (token/cost vs credit_usage). The AutoPilot core contains **no vendor branching** — a deterministic test asserts the core capability modules contain no `hermes`/`manus` text, and the adapter modules are the sole designated vendor boundary (the `cf21` framework-surface test was updated accordingly: exemption is explicit and narrowly scoped to the four C34 adapter modules).

## 5. Provider-Neutral Meta Tests
Synthetic adapter families were registered as factories only — `codex-cli`, `claude-api`, `grok-api`, `deepseek-api`, `gemini-api` — proving the registry accepts arbitrary future target families and that changing HARNESS/PROVIDER/MODEL alters only the adapter, never the core. No live support is claimed for these families.

## 6. Backend Conformance Matrix
| Target | ARCHITECTURALLY_COMPATIBLE | ADAPTER_IMPLEMENTED | ADAPTER_TESTED | LIVE_CERTIFIED | CURRENTLY_ELIGIBLE | AUTH_STATE | PROTOCOL | NOTES |
|---|---|---|---|---|---|---|---|---|
| Manus | ✅ | ✅ | ✅ | ✅ | ✅ | VALID | HTTPS REST `/v2/task.*` | Real bounded run completed; agent profile `manus-1.6-lite`; credits-bounded by design |
| Hermes | ✅ | ✅ | ✅ | ❌ | ❌ | NO_CREDENTIALS | CLI headless `-z` | v0.20.2 installed, interface-probed; first real invocation 403 → `AUTH_INVALID`; honest `ADAPTER_VALIDATED_AUTH_BLOCKED` |
| Codex | ✅ | ❌ | ❌ | ❌ | ❌ | NOT_TESTED | — | Architecture-level only (hermes CLI offers `openai-codex` provider; no P2P adapter built) |
| Claude / Anthropic | ✅ | ❌ | ❌ | ❌ | ❌ | NOT_TESTED | — | Architecture-level only |
| Claude Code | ✅ | ❌ | ❌ | ❌ | ❌ | NOT_TESTED | — | Architecture-level only |
| Grok / xAI | ✅ | ❌ | ❌ | ❌ | ❌ | NOT_TESTED | — | Architecture-level only |
| DeepSeek | ✅ | ❌ | ❌ | ❌ | ❌ | NOT_TESTED | — | Architecture-level only |
| Gemini / Google | ✅ | ❌ | ❌ | ❌ | ❌ | NOT_TESTED | — | Architecture-level only |

Only Manus and Hermes are C34 implementation candidates, exactly as the goal scoped. Registry-≠-router holds: no best-provider selection, no fallback, no ranking, no cost/quality routing; each trial uses an explicitly selected `adapter_id`.

## 7. Control-Plane Hardening
**Permission invariants.** Adapter permission ≤ task permission ≤ Goal-approved permission; the permission profile never widens across the bridge; `NETWORK ≠ SECRET_ACCESS` (the remote API's network ability does not authorize egressing repo/context material; probes used minimal bounded synthetic data). Secrets remain references only (API key read from a host secret path, never stored in state, never logged in evidence content).

**Verifier authority.** `backend says done ≠ verified`: both live backends pass through the P2P verifier with fail-closed `UNKNOWN` handling; transcript/message history persists as evidence-only, never as P2P state authority. Remote Manus task state is observed via bounded foreground polling only — no webhook listener, no scheduler, no session-surviving service. When the session ends, P2P stops; durable state (goal state, ledger, evidence pointers) allows later recovery.

**Recovery semantics.** Both adapter types were exercised for interruption handling: local process death/unknown exit normalizes to `UNKNOWN` (fail-closed, no blind retry of unknown mutation); remote task status-uncertainty normalizes to `UNKNOWN` and recovers from durable state + bounded observation + re-verification.

**Council invariants.** Backend adapters are NOT canonical agents. Tests prove: the canonical eight (`p2p_iris … p2p_helios` from `governance/development-control.json`) remain exactly recoverable; adapter registration does not change council membership; task-executor identity does not redefine quorum; the 8/8 gate remains representable; participant selection can remain risk-driven.

**Candidate policy correction (P0-A).** The deterministic candidate checker (`scripts/p2p_goal_closure.py`) did not match `.p2p/system/p2p_capabilities/*.py` even though that surface is imported at runtime (a documented C33-era design choice — "proveable without packaging ceremony"). `POLICY_BLIND_SPOT_CONFIRMED` on both C33 and C34: the checker diff itself was empty on the original C34 branch, so the blind spot was confirmed by mechanical inspection, not asserted. C34 applies the **authorized minimum correction**: `ChangeSignals.detect` now scans the `.p2p/system/` runtime surface (non-`.md` files), covered by four new regression tests (`gc51`–`gc54`, all green). The correction was then **run as a machine** over both closures: C33 at its implementation commit (`dbfa9e1`) yields `terminal=PASS, runtime changed → CANDIDATE_REQUIRED=YES`; C34 yields `terminal=PARTIAL (not a canonical PASS state) → the PASS-trigger lane does not fire → CANDIDATE_NOT_REQUIRED` (a PARTIAL verdict closes its own lane; nothing is minted reflexively). The C33 consequence is the only one acted on — an unpromoted record plus deterministic artifact was persisted (Section 11).

**State-family registration (P0-B).** `state_family_schema_for` identifies durable state families by path keyword (goal state, goal ledger, execution ledger, evidence, capability ledger, runtime surface) and rejects semantic collisions; the two C34 ledger entries register the new surface. The registration's governance side-effects (ledger count 156→158, dev-control lineage fields, ledger coherence against the charter/validator vocabulary) were reconciled deterministically: ledger entry origin normalized to `IMPLEMENTATION_GOAL`, freshness `from_governance_record`, status `FOUNDATION_READY` (the closest honest charter value given partial validation), and schema/test/validator vocabularies re-converged — see the closure commit for the exact change set.

## 8. Honest Regression Accounting
Machine-readable exact failure sets (pytest node ids, full run output preserved) are anchored in the closure evidence file `docs/p2p-development/research/c34/evidence/c34-post-closure-failure-set.txt`.

Frozen pre-C34 baseline (measured at `2a000e0`, lineage branches restored): **17 failed / 681 passed / 5 skipped / 105 subtests**. Post-closure work state: **22 failed / 731 passed / 5 skipped / 105 subtests**. The delta is exactly five identities — `gc29`, `cp41`, `cl33`, `cp48`, `lh35` — and all five delegate to one framework check: `V15-roadmap-count-sync` (roadmap statement "156 records" vs live ledger 158). The +2 are the C34 P0-B state-family registrations themselves, documented in this report; the classification is `EXPLAINED_DURABLE_SNAPSHOT_DRIFT` per the framework's own `ClosureFinding` severity model. No test was weakened to alter a count, and the roadmap statement was not fabricated (it records generation-time truth; its successor reconciliation is the ledger itself).

| Classification | Tests | Basis |
|---|---|---|
| PRE_EXISTING_BASELINE_FAILURE | `PRLineageTests` gc32–gc35 | ancestry detection needs remote history not present on fresh clone |
| PRE_EXISTING_BASELINE_FAILURE | `test_drift_findings_are_exact`, `test_current_suite_has_real_recorded_trial_pairs`, `test_t18_c09_blocked_identity_state_remains_unknown` | local `.p2p/state` / recorded trials absent in fresh clone |
| ENVIRONMENT_DIFFERENCE | ET host-hardcoded path failures | hardcoded original executor host path `/home/ubuntu/p2p/scripts/p2p_execution_target.py` |
| ENVIRONMENT_DIFFERENCE | `test_ho21/31/33/35/39/40/46` | `codex`/`hermes` host binaries absent on this sandbox |
| EXTERNAL_AUTH_BLOCKER | *(none new)* | Hermes credentials absent → captured by adapter as `AUTH_INVALID`, NOT by a test failure |
| EXPLAINED_DURABLE_SNAPSHOT_DRIFT | `gc29`, `cp41`, `cl33`, `cp48`, `lh35` | documented C34 P0-B ledger +2 (roadmap 156 vs ledger 158) |
| C34_REGRESSION | — | **none observed** (zero adapter/bridge/certification/core failures) |

The pre-existing failures do not hide C34 regressions: the C34 suite itself includes a `fresh_clone_recovery` test that asserts the working tree contains only C34/closure-approved artifacts (untracked C34 files, the C33 candidate artifact, the approved `cf21` boundary fix, the P0-B ledger registration, the checker correction, and the closure-reconciliation vocabulary updates), and the full regression diff confirms the failure-set delta has a single documented root cause.

## 9. Git Disposition
Branch `p2p-c34-real-backend-contract-validation` created from `p2p-c33-bounded-autopilot-core @ 2a000e0` with bounded commits preserving stacked lineage; pushed; Draft PR opened against `p2p-c33-bounded-autopilot-core`. Forbidden actions (merge, force-rewrite, destructive rebase, release, deploy, promotion) were not performed. Baseline `.19` remains immutable and `PROMOTED_VERIFIED`; governance and runtime manifest remain untouched except the ledger entries and the unpromoted C33 candidate record documented above.

## 10. Durable-Closure Governance Reconciliation
This closure section resolves the terminal report against the repository's own governance machinery, mechanically and without retry of any external backend.

**A. Verdict normalization.** The terminal verdict is normalized to `PARTIAL / SINGLE_BACKEND_VALIDATED`. The subordinate capability label `REAL_BACKEND_CONTRACT_VALIDATED` is retained as descriptive vocabulary; it does not constitute a second partial lane, and no canonical `PASS` claim is made.

**B. Candidate-policy machine verification.** The actual checker (`scripts/p2p_goal_closure.py` `candidate_policy` over `ChangeSignals`) was evaluated against both closures after the runtime-detection correction. Mechanical outcome: C33 (`terminal=PASS`, runtime surface changed) → `CANDIDATE_REQUIRED=YES`; C34 (`terminal=PARTIAL`, the PASS-trigger lane does not fire) → `CANDIDATE_NOT_REQUIRED`. The blind spot was confirmed mechanically — the checker's own source diff over the original C34 branch was empty.

**C. Capability-scoped certification.** The Manus adapter's `LIVE_CERTIFIED` claim is scoped to the capabilities actually exercised by runtime evidence and anchored to the five-state chain (`ARCHITECTURALLY_COMPATIBLE ≠ ADAPTER_IMPLEMENTED ≠ ADAPTER_TESTED ≠ LIVE_CERTIFIED_FOR_CAPABILITY ≠ CURRENTLY_ELIGIBLE_FOR_TASK`). Three scopes are `LIVE_CERTIFIED_FOR_CAPABILITY` with evidence pointers; five scopes are `UNKNOWN` (honest, untested) — the machine-readable record is `docs/p2p-development/research/c34/evidence/c34-capability-scoped-certification.json`.

**D. Attestation requested-vs-observed.** The requested profile (`DEFAULT_AGENT_PROFILE = manus-1.6-lite`) and the observed profile (the backend's declared profile in the runtime receipt) are stored as independent fields and bound equal only by runtime evidence. The attestation binding is verified by a deterministic function that rejects the claim when evidence is missing — no copy-equal shortcut is permitted. Model granularity for the Manus API is profile-only (`MODEL_BINDING = UNKNOWN_FOR_MODEL`); no routing was observed.

**E. Machine-readable failure sets.** The exact pre- and post-closure failure sets (pytest node ids) are captured in `docs/p2p-development/research/c34/evidence/c34-post-closure-failure-set.txt`; the frozen-baseline classification in `docs/p2p-development/research/c34/phase0-baseline-tests.md`.

**F. Secret scan.** `gitleaks 8.21.2` scanned the worktree (clean), all four C34 branch commit trees, and the C33→C34 diff. Findings: 22 pre-existing repository files never touched by C34 (out of scope, noted); one C34-introduced disclosure — the full Manus API key in the phase-3 probe document — **redacted to truncated form**; the full key exists only outside the repository (`/home/ubuntu/.secrets/manus_api_key`). Post-redaction worktree rescan: clean. Verdict: no unredacted live credential committed on the C34 range.

## 11. C33 Candidate Consequence (persisted, unpromoted)
Under the corrected checker, C33's durable `PASS` closure requires a candidate record. The deterministic consequence was persisted as a minimum-bounded artifact: `reports/candidates/P2P-8.4.7-C-Codex-Edition-v24-c33-provider-neutral-bounded-autopilot-core-candidate-v1.zip`, containing the eight C33 runtime-surface files at their committed content.

| Field | Value |
|---|---|
| Candidate record | `governance/development-control.json` `candidate_records` `C33` |
| Promotion status | `UNPROMOTED` (no promotion, no release, no manifest change) |
| Artifact zip sha256 | `b1cdcfd881156726fdfa054ae5186e0aee728bde5d4536d0c6f184181b6ae6ed` |
| Content sha256 (8 files) | `4c9b9487c850ffd45fd9bc6d8bd4edb69a5fc3dde18a610c0122c52d08dfd389` |
| Embedded version | `8.4.7-C-codex.24` |
| Lineage reference | `8.4.7-C-codex.19 / 3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8` |

The full `package_release` pipeline was deliberately not invoked (its fixed source-inventory hashes predate the C33 runtime files — an unrelated manifest drift); the artifact scope is the runtime surface only, which is the minimal deterministic object the candidate policy demands. C34 requires no candidate record under the deterministic policy (`PARTIAL` does not fire the PASS lane).

## 12. Closure Commit Inventory
The durable closure is contained in its own bounded commits on `p2p-c34-real-backend-contract-validation` (after the implementation commits): the capability-scoped certification vocabulary and attestation binding additions to `backend_contract.py` plus their six new tests; the checker runtime-detection correction plus `gc51`–`gc54`; the C33 candidate record and artifact; the ledger coherence pass (entry origin/freshness/status normalization, vocabulary re-convergence); the C34 test file's approved-artifact set growth; the failure-set evidence file; the probe-document key redaction; and this terminal report. No merge, promotion, release, or history rewrite occurred.

## 13. Owner Gates Honored
The only external actions in this goal were those the Owner supplied up front: GitHub access (PAT), Manus API credentials (key file), and the instruction set itself. No new credential/login action was requested mid-goal; Hermes live certification is the natural next Owner Gate if provider credentials are desired.

## 14. Final Security Closure — Credential Incident and History Purge
During the reconciliation phase, an incident was classified: `CREDENTIAL_EXPOSED_IN_GIT_HISTORY` — the full Manus API key value was committed (in `docs/p2p-development/research/c34/phase3-manus-api-probe.md` and its header-form occurrences) on the C34 branch range, and the key was subsequently **revoked by the Owner**. The Owner explicitly authorized a force-update scoped strictly to the C34 branch (`p2p-c34-real-backend-contract-validation`); the base branch and all ancestor lineage were not touched.

The purge was performed with `git-filter-repo` (replace-text, full key value → `x-manus-api-key:redacted-by-c34-final-security-closure`) over every reachable C34 commit, and verified exhaustively: a blob-level scan of **all** reachable rewritten commits for the full key, the `sk-DvH3` prefix, and header-form occurrences returned **zero hits**; `gitleaks 8.21.2` over the full `2a000e0..HEAD` patch returned **zero findings**; the PR #10 changed-content patch (API) returned **zero findings**; the final worktree and the committed evidence docs and JSONs returned **zero findings**. The pre-existing 22 gitleaks hits across repository files (skill docs, lockfiles, test fixtures) predate C34 and remain out of scope. The base `2a000e0` remains untouched and `PROMOTED_VERIFIED`.

## 15. V15 Resolution — Semantics, Not Fabrication
The five count-sync failures (gc29, cp41, cl33, cp48, lh35) are resolved under **CASE 1** of the closure semantics: `current-roadmap.md` self-declares as a *derived, human-readable projection* that "must never be edited as a source of truth" and whose §6 regeneration rule obligates regeneration whenever the capability ledger changes. The count statement ("156 records, 12 families … at generation time") is descriptive ledger metadata within that projection — it went stale because the documented P0-B registrations grew the ledger to 158. The minimum mechanical sync was applied: count `156 → 158`, "generation time" → "regeneration time", and the generated-date line re-anchored to the regeneration event. Nothing else in the roadmap was touched: goal direction, ordering, decisions, and candidate table are byte-identical to the previous state. All five tests re-greened; no count assertion was weakened.

## 16. C33 Candidate Version-Identity Audit (F)
Three candidate records (`C30`, `C31`, `C33`) carry `candidate_version 8.4.7-C-codex.24`, and six records (`C18`–`C21`, `C25`, `C26`) already share `8.4.7-C-codex.21` with **distinct** `candidate_sha256` and distinct artifacts. The governance precedent is unambiguous: `candidate_version` identifies **source state** (the unpromoted working version `current_development.source_version = 8.4.7-C-codex.24`), not artifact uniqueness. Canonical identity is the tuple `(candidate_id, development_goal, candidate_sha256)`; labels carry the goal slug for disambiguation. C33's artifact (eight autopilot runtime files + candidate manifest, `b1cdcfd8…e6ed`) is content-distinct from C30's artifact (a skill package, `94b09b59…`), and C31 is explicitly a policy-decision record only (`built: false`, no artifact). The `lineage_contract` imposes no version-uniqueness rule (`filename_is_authority: false`). **Verdict: reuse allowed by established governance precedent — PASS.** A bounded `identity_semantics_note` was appended to the C33 record (append-only field mutation) documenting this rule; no promotion, release, or manifest change was made or implied.

## 17. Final Machine-Readable Failure Set
The definitive exact failure set, post-purge and post-sync, is anchored in `docs/p2p-development/research/c34/evidence/c34-final-failure-set.txt`. Measured result: **17 failed / 735 passed / 5 skipped / 105 subtests**, and the set diff against the frozen pre-C34 baseline is **EMPTY** — `PRE ∆ POST = ∅`, `POST_NEW_UNEXPLAINED_FAILURES = 0`. The previous EXPLAINED_DURABLE_SNAPSHOT_DRIFT classification (156/158) is now resolved by the §6 regeneration sync; no explained or unexplained delta remains.

## 18. Final Verdict (superseding, machine-reproducible)

```
P2P-C34 / REAL BACKEND CONDUCT + GOVERNANCE CLOSURE
VERDICT:  PARTIAL / SINGLE_BACKEND_VALIDATED
LIVE:     Manus API  (ADAPTER_IMPLEMENTED · ADAPTER_TESTED ·
         LIVE_CERTIFIED_FOR_CAPABILITY ×3, evidence-anchored,
         scope-limited; model binding UNKNOWN_FOR_MODEL;
         possible_mutation=false; credit usage accounted)
HONEST:   Hermes     (ADAPTER_VALIDATED_AUTH_BLOCKED;
         v0.20.2 installed, headless interface probed, no provider
         credentials available → AUTH_INVALID, not fabricated)
POLICY:   candidate_policy mechanically verified
         (C33 REQUIRED→persisted UNPROMOTED; C34 NOT REQUIRED)
SECURITY: credential purge complete, zero key material in any
         reachable commit, worktree, or PR patch (gitleaks verified)
REGRESSION: POST == PRE == 17 (identical sets); zero C34-induced
         failures across the full suite
GATES:    no merge, no promotion, no release, no rewrite outside the
         owner-authorized force-update of the C34 branch only;
         baseline 2a000e0 and .19 PROMOTED_VERIFIED untouched
NEXT:     Owner Gate — Hermes provider credentials, then live
         certification re-probe
```

## 19. Final Commit Inventory (post-purge)
The branch history now contains only clean commits (all pre-purge SHAs invalid). Post-purge heads: the full bounded implementation + closure set, culminating in the final-security purge verification and this terminal report. The final branch head SHA is the single machine-identifiable anchor; it is cited in the closing PR #10 comment. All post-closure state files remain exactly as recorded in section 11–16; the purge altered blob content (key redaction) of the probe document and nothing else.
