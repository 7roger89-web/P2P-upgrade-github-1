<!-- NON_CANONICAL / IMPLEMENTATION_EVIDENCE / NOT_PROMOTED -->
# P2P-C34 Terminal Report
**Goal name:** Real Backend Contract Validation + Control-Plane Hardening
**Terminal verdict:** `PARTIAL / REAL_BACKEND_CONTRACT_VALIDATED` (SINGLE PARTIAL)
**Mode:** Large implementation goal, continuous bounded execution, checkpoint-driven
**Author:** P2P-C34 Implementation (Manus AI)
**Date:** 2026-08-17 (GMT+7)
**Branch:** `p2p-c34-real-backend-contract-validation` based on `p2p-c33-bounded-autopilot-core @ 2a000e0`
**Addendum applied:** P2P Capability Preservation Addendum (sections A–Z)
---
## 1. Terminal Verdict
```
PARTIAL / REAL_BACKEND_CONTRACT_VALIDATED
```
The C33 AutoPilot core loop (proven over a fake backend) is now **contractually bound to real execution backends**, with one backend **live-certified against a real API** and one backend **honestly auth-blocked**. Concretely:

- **Manus adapter: `LIVE_VALIDATED`** — a real bounded task was created, executed, stopped, and verified through the Manus API with owner-supplied credentials (`task.create` → bounded poll → `task.listMessages`). Answer evidence ("Four"), usage evidence (`credit_usage: 0`), request/receipt binding, and immutable evidence files were all produced by the adapter contract.
- **Hermes adapter: `ADAPTER_VALIDATED_AUTH_BLOCKED`** — Hermes v0.20.2 (2026.8.16) was installed and its headless CLI interface (`hermes -z`) was probe-verified on this host. No provider credentials exist in the environment, so the first real invocation returned HTTP 403 "Access denied", which the adapter normalized to `FAILED / AUTH_INVALID` with USAGE_EVIDENCE surface still produced. Success was not fabricated; the classification is deliberate.

Control-plane hardening shipped alongside: a conformance contract (`backend_contract.py`), a vendor-free bridge into the C33 core (`backend_execution_bridge.py`), registry-≠-router enforcement, canonical-council invariants, state-family collision prevention, and a corrected candidate-policy surface audit. **Zero new test failures**: the full regression suite ends 17 failed / 725 passed / 6 skipped, with the failure set byte-identical to the frozen pre-C34 baseline.

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
| `docs/p2p-development/capability-ledger/capability-index.json` | +2 ledger entries: `C34_REAL_BACKEND_CONTRACT` (VALIDATED, live-certified for Manus adapter, adapter-validated for Hermes) and `C34_STATE_FAMILY_IDENTIFICATION` (VALIDATED) |

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

**Candidate policy correction (P0-A).** The deterministic candidate checker (`scripts/p2p_goal_closure.py`) does not match `.p2p/system/p2p_capabilities/*.py` even though that surface is imported at runtime (a documented C33-era design choice — "proveable without packaging ceremony"). C34 applies the corrected semantics: the C34 contract surface is registered in the capability ledger as a runtime-visible family, and the audit tests enforce that future additions to this surface remain candidate-policy-visible. No candidate was minted or avoided reflexively; the corrected policy was followed.

**State-family registration (P0-B).** `state_family_schema_for` identifies durable state families by path keyword (goal state, goal ledger, execution ledger, evidence, capability ledger, runtime surface) and rejects semantic collisions; the two C34 ledger entries register the new surface.

## 8. Honest Regression Accounting
Frozen pre-C34 baseline (host `2a000e0`, lineage branches restored): **17 failed / 681 passed / 5 skipped**. Final freeze: **17 failed / 725 passed / 6 skipped**. The failure set is identical; every failure is classified:

| Classification | Tests | Basis |
|---|---|---|
| PRE_EXISTING_BASELINE_FAILURE | `PRLineageTests` gc32–gc35 | ancestry detection needs remote history not present on fresh clone |
| PRE_EXISTING_BASELINE_FAILURE | `test_drift_findings_are_exact`, `test_current_suite_has_real_recorded_trial_pairs`, `test_t18_c09_blocked_identity_state_remains_unknown` | local `.p2p/state` / recorded trials absent in fresh clone |
| ENVIRONMENT_DIFFERENCE | `test_et38/40`, `test_et45–49` | hardcoded original executor host path `/home/ubuntu/p2p/scripts/p2p_execution_target.py` |
| ENVIRONMENT_DIFFERENCE | `test_ho21/31/33/35/39/40/46` | `codex`/`hermes` host binaries absent on this sandbox |
| EXTERNAL_AUTH_BLOCKER | *(none new)* | Hermes credentials absent → captured by adapter as `AUTH_INVALID`, NOT by a test failure |
| C34_REGRESSION | — | **none observed** |

The pre-existing failures do not hide C34 regressions: the C34 suite itself includes a `fresh_clone_recovery` test that asserts the working tree contains only C34-approved artifacts (untracked C34 files, the approved `cf21` boundary fix, and the approved P0-B ledger registration), and the full regression diff confirms byte-identical failure sets before/after.

## 9. Git Disposition
Branch `p2p-c34-real-backend-contract-validation` created from `p2p-c33-bounded-autopilot-core @ 2a000e0` with bounded commits preserving stacked lineage; pushed; Draft PR opened against `p2p-c33-bounded-autopilot-core`. Forbidden actions (merge, force-rewrite, destructive rebase, release, deploy, promotion) were not performed. Baseline `.19` remains immutable and `PROMOTED_VERIFIED`; governance and runtime manifest remain untouched except the ledger entries documented above.

## 10. Owner Gates Honored
The only external actions in this goal were those the Owner supplied up front: GitHub access (PAT), Manus API credentials (key file), and the instruction set itself. No new credential/login action was requested mid-goal; Hermes live certification is the natural next Owner Gate if provider credentials are desired.
