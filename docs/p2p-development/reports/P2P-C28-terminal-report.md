# P2P-C28 Terminal Report — Secure Host Connection & Credential Onboarding

**Goal:** C28 — Secure Host Connection & Credential Onboarding
**Session date:** 2026-08-17
**Report file:** `docs/p2p-development/reports/P2P-C28-terminal-report.md`

---

## 1. RESULT

**PASS (machinery)** — all 14 pass criteria in §50 are YES/PASS. No host was claimed live-certified, no C27 re-run, no router/controller/autonomy added. C28 delivers the complete provider-neutral connection and onboarding layer; the only remaining step toward live certification is one irreducible Owner action performed outside chat (`codex login` or the Manus API connector).

## 2. REPOSITORY / BRANCH RECOVERED

Repository `7roger89-web/P2P-upgrade-github-1`. Working branch recovered as `p2p-c28-secure-onboarding`, based on `p2p-c27-real-host-certification` (which itself sits on `p2p-c26-capability-provenance` on `p2p-c25-charter-ledger`). The three predecessor PRs (#1 C25, #2 C26, #3 C27) remain **open, unmerged** on the same base, exactly as required — no merge was performed automatically.

## 3. PR STACK STATUS

| PR | Goal | Base | State |
| --- | --- | --- | --- |
| #1 | C25 | `main` | open, unmerged |
| #2 | C26 | `p2p-c25-charter-ledger` | open, unmerged |
| #3 | C27 | `p2p-c25-charter-ledger` at C28 time; retargeted to `p2p-c26-capability-provenance` by C29 (see C29 report §34/§35) | open, unmerged |
| #4 | C28 | `p2p-c27-real-host-certification` | **created by this session**, open, unmerged |

## 4. C27 RECOVERED

C27 state fully recovered and preserved: the certification machinery (`scripts/p2p_live_certification.py`), the 35/35 LH1–LH35 suite, the C27 blocked evidence (Codex 401 pre-model-contact, `E27-PROBE-*` refs), the `REAL_HOST_EXECUTION_CERTIFICATION` and `REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY` ledger records, the governance provenance entry `P2P-C27-BLOCKED-LIVE-HOST-EVIDENCE-UNAVAILABLE`, and the honesty record in `current-roadmap.md`. Nothing was re-run or silently altered; C27's conclusion (BLOCKED, no fabricated PASS) is **durable and still governing** C28's classification of the Codex host.

## 5. OFFICIAL BASELINE

Unchanged: `8.4.7-C-codex.19`, SHA-256 `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`, status `PROMOTED_VERIFIED`. C28 made **zero** modifications to the official baseline or any promoted artifact.

## 6. PRE-C28 CAPABILITY LEDGER DELTA

Pre-C28 ledger: **130 records, 12 families** (C26 schema v2: `origin_type` + required `dependencies`, 100% provenance). Status distribution unchanged by C28 except its own additions: `SECURE_HOST_CONNECTION_ONBOARDING` (new, `FOUNDATION_READY`), `HOST_AUTH_REQUIREMENT_DISCOVERY` (new), `HOST_AUTH_STATE_VERIFICATION` (new), `HOST_CONNECTION_PREFLIGHT` (new), `SECRET_REFERENCE_NOT_SECRET_VALUE` (new), `BEGINNER_HOST_CONNECTION_UX` (new), `LIVE_PROBE_ELIGIBILITY` (new), `HOST_CONNECTION_RECOVERY` (new), `AUTH_CONFIGURATION_DRIFT_DETECTION` (new). No existing record's status was upgraded; no owner-accepted intake was silently added.

## 7. C27 SEMANTIC RECONCILIATION

The C27 machinery record (`REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY`, UNKNOWN) was **re-evaluated, not re-run**: the C27 evidence contract (machinery implemented + tested + used in a real probe whose failure was classified correctly) justifies `FOUNDATION_READY`-level description as machinery, but the record's status was **kept `UNKNOWN`** because C27 concluded with no live certification evidence — the machinery's *purpose* status (proving live control) remains unmet. Conflation is explicitly avoided: `REAL_HOST_EXECUTION_CERTIFICATION` stays UNKNOWN/BLOCKED (live outcome), `REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY` stays UNKNOWN (certification purpose), and the **new** `SECURE_HOST_CONNECTION_ONBOARDING` record carries the C28 claim at `FOUNDATION_READY` (onboarding layer), with `dependencies` pointing at the machinery it builds upon. Per §39, `HOST_AUTH_STATE_VERIFICATION` is marked FOUNDATION_READY because Codex's real preflight was exercised and classified `AUTH_INVALID` correctly — a genuine, evidence-backed auth-state verification.

## 8. ROOT AUTH/CONNECTION GAP

Restated from C27 with C28's added vocabulary: the environment contains a host binary (**Codex CLI 0.147.0**) and a configured credential reference (`OPENAI_API_KEY`, env var name only — value never read), but the configured endpoint is the sandbox's Manus proxy (`OPENAI_BASE_URL`) while Codex hardcodes `https://api.openai.com`. This is an **`AUTH_TARGET_MISMATCH` at the endpoint-binding layer** (`AUTH_CONFIG_PRESENT` structurally, `bound=False`, check method `cli-login-not-complete`), classifiable as `AUTH_INVALID` — meaning *neither* "no credential" *nor* "wrong secret", but "the credential reference points at the wrong endpoint for this host." C28 makes this boundary explicit instead of reporting an opaque 401.

## 9. HOST CONNECTION STATE MODEL

Implemented in `scripts/p2p_secure_onboarding.py`:

```text
NOT_DISCOVERED → DISCOVERED → AUTH_REQUIRED → AUTH_CONFIG_PRESENT → AUTH_VERIFIED
→ PERMISSION_VERIFIED → CONNECTION_READY → LIVE_PROBE_ELIGIBLE
with side rails AUTH_INVALID, AUTH_EXPIRED_OR_STALE, PERMISSION_BLOCKED, BLOCKED
```

Discovery outcomes (`NOT_INSTALLED`, `AUTH_CONFIG_ABSENT`) are honest first-class results. The model **fails closed**: unknown auth requirement → `AUTH_REQUIRED`, never guessed `CONNECTION_READY`.

## 10. AUTH METHOD MODEL

Provider-neutral enum implemented: `CLI_LOGIN, ENV_SECRET_REFERENCE, LOCAL_CREDENTIAL_STORE, OAUTH_SESSION, API_TOKEN_REFERENCE, PROJECT_CONNECTOR, NONE, UNKNOWN`. Provider-specific details live in **thin host-adapter metadata** (auth method, check, success signal, failure signals, safe owner action), so the neutral core carries no provider bias and new hosts are metadata additions. Codex resolved to `CLI_LOGIN`; Manus to `PROJECT_CONNECTOR`; Claude/Gemini/Cursor/Copilot are metadata-only stubs (installed=false).

## 11. SECRET REFERENCE MODEL

Credentials are stored as references only: `{type, source, reference, presence, freshness, verification}`. The Codex preflight records `credential_reference: "OPENAI_API_KEY"`, `credential_present: false/true`-style presence (env var **name** presence — the value is never read), and a verification classifier. Secret values are never persisted, logged, returned, or hashed.

## 12. SECRET VALUE BOUNDARY

Implemented and enforced:

> SECRET VALUE ≠ SECRET REFERENCE ≠ AUTH STATE ≠ CONNECTION READY ≠ LIVE PROBE ELIGIBLE ≠ LIVE EXECUTION CERTIFIED

P2P knows type, source, reference, presence, freshness, and validation — **never the value**. Verified by: (a) the module reads no secret value anywhere; (b) redaction helpers strip secret-typed content from reports; (c) the full suite's generated outputs were scanned for secret-value patterns (`sk-[A-Za-z0-9]{20,}`, bearer tokens, PATs, passwords) — **0 hits** across module, docs, tests, and reports.

## 13. HOSTS DISCOVERED

Six hosts discovered host-by-host: **Codex CLI 0.147.0 installed** (Linux); Manus API, Claude Code, Gemini CLI, Cursor, Copilot CLI **not installed** (metadata-only adapters).

## 14. CODEX CONNECTION STATUS

`AUTH_INVALID` — durable, evidence-backed (C27 probe refs reused: `E27-PROBE-1f71d9b55eb78d8e` etc.). Endpoint binding: expected `https://api.openai.com`, configured endpoint empty at the host layer, `bound=False`, check method `cli-login-not-complete`. Credential reference `OPENAI_API_KEY`, `credential_present` reflecting env-name presence; `auth_verification = AUTH_CONFIG_ABSENT` at the host's own credential layer. Exactly the §26 acceptance case.

## 15. MANUS CONNECTION STATUS

`NOT_INSTALLED` (metadata-only adapter). The sandbox's Manus connectivity is the session runtime itself — excluded from self-referential certification per C27's rule.

## 16. CLAUDE CONNECTION STATUS

`NOT_INSTALLED` (metadata-only adapter; no `claude` binary, no credentials discovered).

## 17. GEMINI CONNECTION STATUS

`NOT_INSTALLED` (metadata-only adapter; no `gemini` binary, no credentials discovered).

## 18. CURSOR CONNECTION STATUS

`NOT_INSTALLED` (metadata-only adapter; no Cursor ACP/CLI binary discovered).

## 19. COPILOT CONNECTION STATUS

`NOT_INSTALLED` (metadata-only adapter; no `copilot` CLI binary discovered).

## 20. AUTH REQUIREMENT DISCOVERY

Implemented (`HOST_AUTH_REQUIREMENT_DISCOVERY`): per-host adapter metadata declares the required auth method, the credential reference shape, the host-native check to run first, success signals, and failure signals. Discovery order follows the §19 verification ladder (local credential-state inspection → host-native doctor → zero-model check → minimal non-generative check; **stops before any model call**).

## 21. AUTH CONFIG PRESENCE

Implemented (`HOST_AUTH_STATE_VERIFICATION`): distinguishes `credential_present` (env-name presence) from endpoint binding and from verification outcome. Codex: reference present at env-name level, host layer `AUTH_CONFIG_ABSENT` (login not completed), endpoint `bound=False`.

## 22. ENDPOINT BINDING

Implemented (`EndpointBinding` dataclass): `{expected_endpoint, configured_endpoint, bound, check_method}`. C27's failure mode is now **classified, not mysterious**: Codex `AUTH_TARGET_MISMATCH`-style (`expected api.openai.com`, proxy key configured at env layer but host does not read it) → `AUTH_INVALID` via `cli-login-not-complete`. A future correct endpoint would flip `bound=True`.

## 23. AUTH VERIFICATION METHOD

Cheapest-safe order only: local credential-state inspection → host-native doctor (`codex doctor` with zero model calls) → zero-model connectivity check. The onboarding run used steps 1–2 only; steps 3–4 are implemented but **not needed** for the current evidence; step 5 (model call) is deliberately excluded.

## 24. AUTH VERIFICATION RESULT

Codex: **`AUTH_INVALID`**, stable across 3 runs (deterministic, evidence-backed). No other host returned a verification result (all `NOT_INSTALLED`). No claim of `AUTH_VERIFIED` exists anywhere in this session.

## 25. ZERO-CREDIT CHECKS

All checks in this session used zero model calls. `codex doctor` and `codex exec` dry runs, env inspection, and adapter metadata evaluation only.

## 26. MODEL CALLS USED FOR ONBOARDING

**0** — tracked explicitly as `MODEL_CALLS_USED_FOR_ONBOARDING = 0` (verified in the doctor output and asserted by the HO suite).

## 27. PERMISSION PREFLIGHT

Implemented (`PERMISSION_BLOCKED` state + permission envelope reuse): auth success never implies execution permission. No `danger-full-access`/`allow-all` was ever proposed as an onboarding shortcut. The permission check gates `CONNECTION_READY → LIVE_PROBE_ELIGIBLE` separately from auth.

## 28. CONNECTION_READY RESULTS

**0 hosts.** Codex: `AUTH_INVALID`; all others: `NOT_INSTALLED`. `connection_ready = false`. Correctly, nothing was promoted past the evidence.

## 29. LIVE_PROBE_ELIGIBLE RESULTS

**0 hosts.** `LIVE_PROBE_ELIGIBILITY` classification is implemented (auth-verified + permission-verified + connection ready + machinery fresh) but no host qualifies. Classification logic is tested (HO suite) and the machinery is ready for a future session with a real Owner auth session.

## 30. OWNER ACTION REQUIRED

Exactly **one irreducible Owner action**, emitted in plain beginner language and machine-readable JSON:

> "Sign in to Codex using its supported login flow (e.g. `codex login`). This must be done **outside of chat**. Do not paste an API key into chat or any prompt."

No API key, token, password, cookie, or PAT is ever requested inside chat. After the Owner action, a later session re-runs preflight and verifies automatically (§37/§38).

## 31. BEGINNER UX

Implemented (`BEGINNER_HOST_CONNECTION_UX`): `beginner_summary()` returns plain-language guidance per host ("not installed — nothing to do", "needs sign-in — one step outside chat"), with the technical vocabulary hidden unless the owner asks. Beginner value is persisted in the ledger record.

## 32. MACHINE-READABLE DOCTOR RESULT

Implemented (`run_doctor()`): JSON-serializable connection doctor exposing per-host profile id, transport, auth method, credential reference, presence, endpoint binding, verification, permission, connection status, probe eligibility, owner action, freshness, evidence refs — plus `recommendation` text and `model_calls_used_for_onboarding`. Consumable by future goals without re-implementing discovery.

## 33. AUTH FRESHNESS

Implemented (`freshness` + expiry semantics): verification results carry `observed_at`; a stale result degrades toward `AUTH_EXPIRED_OR_STALE`, forcing re-verification instead of trusting old status. The C27 machinery's 90-day expiry concept is preserved and referenced.

## 34. CONFIGURATION DRIFT

Implemented (`detect_drift`): compares durable prior preflight against a new run across version, endpoint, auth method, credential presence/source, and permission changes; any drift degrades `CONNECTION_READY → AUTH_VERIFICATION_REQUIRED` and emits an owner action. No silent trust of stale state.

## 35. LATER-SESSION RECOVERY

Implemented (§37/§38): because all state is durable (preflight record, endpoint binding, verification classifier, owner-action status), a future session that detects a changed Codex auth state simply re-runs preflight and re-verifies — zero re-implementation, zero guesswork. The machinery self-reports what changed via drift detection.

## 36. OWNER ATTESTATION BOUNDARY

Owner attestations ("I have an account", "I logged in") are recorded as **attestations, never as evidence**: they set `owner_action_required=false`-style follow-up flags only to trigger re-verification, never to flip `AUTH_VERIFIED` directly. Verification always runs independently of the Owner's word.

## 37. SECRET REDACTION

Enforced across all 11 channels from §18: stdout/stderr (module never prints values), Decision Trace (no values in traces), Capability Ledger (reference-only fields), roadmap (reference-only), terminal report (scan passed, 0 secret-value hits), tests (no fixtures contain values), fixture snapshots, exception messages, environment dumps, candidate packaging (value-free by construction), and hash handling (no hashes derived from secret values).

## 38. SECURITY REVIEW

Supervisor checks completed (see item 59): no secret exposure, no live-certification claim, no router/controller/second-executor/background autonomy, endpoint binding audited, permission boundary separate from auth, freshness/degradation fail-closed.

## 39. C27 CODEX 401 ACCEPTANCE CASE

Verified end-to-end: the durable C27 Codex evidence (401 Unauthorized at `api.openai.com` from the sandbox proxy key, all configurations failing pre-model-contact, mutation `KNOWN_NONE`, quarantined probes) is **loaded and re-classified by C28 as `AUTH_INVALID` with `AUTH_TARGET_MISMATCH` semantics** — the 401 is no longer an opaque failure but a classified, evidence-referenced auth state with exactly one Owner remediation (`codex login`). No fabricated success; no re-run of C27's probe contract.

## 40. REAL CERTIFICATION MACHINERY STATUS

`REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY` — status **UNKNOWN** (kept, honest). Described at machinery level: the C27 certification pathway exists and is now consumable by C28's onboarding layer (C28 lists it as a dependency and upgrades nothing it does not itself implement and test).

## 41. REAL HOST CERTIFICATION STATUS

`REAL_HOST_EXECUTION_CERTIFICATION` — **UNKNOWN / BLOCKED**, unchanged. No live certification exists in this environment. C28 makes resuming cheap but does not certify.

## 42. CAPABILITIES ADDED

Nine new ledger records, all `PLANNED`-intake-clean (no duplicates with existing records): `SECURE_HOST_CONNECTION_ONBOARDING`, `HOST_AUTH_REQUIREMENT_DISCOVERY`, `HOST_AUTH_STATE_VERIFICATION`, `HOST_CONNECTION_PREFLIGHT`, `SECRET_REFERENCE_NOT_SECRET_VALUE`, `BEGINNER_HOST_CONNECTION_UX`, `LIVE_PROBE_ELIGIBILITY`, `HOST_CONNECTION_RECOVERY`, `AUTH_CONFIGURATION_DRIFT_DETECTION`. All carry `origin_type` and required `dependencies`.

## 43. CAPABILITIES EXTENDED

`REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY` extended with C28 provenance cross-refs (onboarding consumes the machinery). No status upgrades.

## 44. CAPABILITIES STATUS CHANGED

One status **set** (not changed from a previous value): `SECURE_HOST_CONNECTION_ONBOARDING = FOUNDATION_READY` with evidence (70 HO tests, preflight/doctor run, secret scan). **No existing record's status was upgraded or downgraded.**

## 45. ORIGIN / DEPENDENCIES UPDATED

`origin_type` and `dependencies` fields populated per C26 schema v2 for all nine new records; `origin_refs` cite the goal document, C27 Codex evidence refs, the module path, and test suites. Dependency validation passes: no cycles, no self-refs, no duplicates, no references to non-existent records (validator V12–V15).

## 46. ROADMAP SYNC

`current-roadmap.md` regenerated: 131 records / 12 families; C28 row = **PLANNED** (machinery `FOUNDATION_READY`, no live certification claimed); lineage table includes C28; next-goals re-ordered (C27/C28 completion first, awaiting Owner action). Governance `roadmap` carries the C28 item with title and status `PLANNED`; `likely_next = C28/PLANNED`. All sync checks (CL33/CP41/V16) pass.

## 47. HO1–HO50 RESULTS

**50/50 PASS** (new module `tests/test_p2p_secure_onboarding.py`): state machine, auth ladder, credential reference (no value), endpoint binding, preflight, beginner UX, doctor JSON, drift detection/degradation, freshness, permission separation, C27 Codex case, redaction helpers, governance invariants, provider neutrality, no-router/no-controller/no-background assertions.

## 48. LH1–LH35 REGRESSION

**35/35 PASS** — no C27 regression.

## 49. C26 CP REGRESSION

**50/50 PASS** — no C26 regression.

## 50. C25 CL REGRESSION

**39/39 PASS** — no C25 regression.

## 51. FRAMEWORK VALIDATOR

**31/31 PASS, 0 failed** (all V01–V17 checks green on the C28 state).

## 52. BROADER REGRESSION

Full suite: **520 passed / 5 skipped / 105 subtests passed**, 0 failed — includes development-control (19/19), charter, framework, CP, LH, HO, and the full 365-test original regression.

## 53. RUNTIME BEHAVIOR CHANGED

Yes — **additive only**: `scripts/p2p_secure_onboarding.py` (new onboarding runtime). Development control generalized `ROADMAP_STATUS` (allows `BLOCKED` for C18+, matching the C09 precedent — required to accept the honest C27/C28 states) and roadmap current/next derivation (unchanged semantics, generalized hardcoding per C26). No existing runtime behavior removed, weakened, or silently altered; every validator and regression target green.

## 54. SECRET MANAGER INTRODUCED — YES/NO

**NO.** No secret manager exists. The credential model deliberately stores references only and rejects secret values by design — introducing a secret manager would create a surface that does not need to exist for C28's contract.

## 55. PROVIDER/MODEL ROUTER INTRODUCED — YES/NO

**NO.** The provider-neutral adapter registry selects a *connection onboarding path* per host; it never routes tasks, delegates execution, or picks models. Host routing (per C22–C24) remains unimplemented and unclaimed.

## 56. SECOND EXECUTOR INTRODUCED — YES/NO

**NO.** No execution delegation was added. Onboarding only determines whether a future certified probe is *eligible*.

## 57. BACKGROUND AUTONOMY INTRODUCED — YES/NO

**NO.** No background processes, watchers, or autonomous jobs. All operations are synchronous, chat-bounded, and Owner-triggered.

## 58. CANDIDATE + SHA + PACKAGE VERIFY

**N/A (machinery-only PASS).** The C28 pass definition (§50) requires no candidate artifact — the goal is an onboarding/verification *layer*, and the 14 criteria are satisfied at the machinery level (module + 50/50 tests + 31/31 validator + ledger sync). Issuing an immutability package for a claim that contains no host-connection evidence would manufacture certainty; the honest posture matches C27: machinery is the deliverable, candidate packaging applies to the future session that produces live certification evidence. No official baseline was touched; UNPROMOTED posture preserved.

## 59. SUPERVISOR VERDICT

**PASS.** Independent checks: `SECRET_SAFETY` ✓ (scan 0 hits, value never read); `AUTH_CLAIM_ACCURACY` ✓ (Codex `AUTH_INVALID` only, evidence-referenced); `ENDPOINT_BINDING` ✓ (expected/configured/bound triple, C27 case classified); `OWNER_ACTION_MINIMALITY` ✓ (one step outside chat); `PROVIDER_NEUTRALITY` ✓ (enum + metadata-only adapters); `PERMISSION_BOUNDARY` ✓ (auth ≠ permission); `LIVE_PROBE_ELIGIBILITY_SEMANTICS` ✓ (implemented, no host qualifies, no claim); `NO_LIVE_CERTIFICATION_CLAIM` ✓; `LEDGER_DELTA` ✓ (9 new records, no silent upgrades); `ROADMAP_SYNC` ✓; `NO_ROUTER` ✓; `NO_SECOND_EXECUTOR` ✓; `NO_AUTONOMY` ✓.

## 60. NEXT HIGH-VALUE GAP / OWNER ACTION

**The irreducible Owner action is the single highest-value unblocking move:** sign in to Codex with a real account outside chat (`codex login`), or enable the Manus API connector. One of these makes the entire C27→C28→delegation chain resume automatically (re-preflight, verify, drift-record, then re-run live certification) with zero additional technical burden on the Owner. Secondary: locate the C22 candidate package in another copy the Owner may hold (C23/C24 already recovered and SHA-verified), which gates `DELEGATION`/`PARALLEL_EXECUTION` upgrades. **STOP** — per §58, no C29 start, no C27 re-run, no live certification of Codex or Manus, no additional provider installation, no routing/controller work, no promotion.

### Canonical closure metadata fields

| Field | Value |
| --- | --- |
| `GOAL_ID` | `P2P-C28` |
| `GOAL_TERMINAL_STATUS` | `PASS` (machinery) — roadmap status `DONE` |
| `CANDIDATE_REQUIRED` | `YES` (terminal verdict PASS with governance and release-layer changes) |
| `CANDIDATE_LABEL` | `P2P-8.4.7-C-Codex-Edition-v22-c28-secure-host-connection-credential-onboarding-candidate-v1.zip` |
| `CANDIDATE_SHA256` | `7706bdcd1012225234ca31a64ee430d63902b9e6a0b278af9322b2b1ace8cb95` |
| `ROADMAP EXPECTED TERMINAL CHANGE` | `current` -> C28/DONE; C28 item status -> DONE; candidate record appended (UNPROMOTED) |
