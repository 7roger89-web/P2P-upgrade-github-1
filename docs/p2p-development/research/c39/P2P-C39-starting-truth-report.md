# P2P-C39 — Starting-Truth Gate Report (Prompt 1/2)

**Mode:** READ-FIRST · EVIDENCE-FIRST · PROVIDER-NEUTRAL · BEGINNER-FIRST · FAIL-CLOSED
**Scope:** Recovery / Starting-Truth Gate only. C39 is NOT implemented. No code written, no evidence regenerated, no backend dispatch, no candidate, no merge/promote/release.

---

## 1. RECOVERY VERDICT

**READY_FOR_C39 — conditional on one Owner credential action** (Auth Gate §8). Git truth, C38 terminal truth, and all C30–C38 machinery are verified and intact. Two genuine constraints are recorded up front and neither is silently repaired:

1. **Manus API key đã hết hạn** (expired — xác minh live, không in secret). Hermes × Gemini còn hiệu lực.
2. C39's falsifiable question (Stage C–D live proofs) requires **two currently-eligible certified backends**. Historically certified does not equal currently eligible.

## 2. REPOSITORY / BRANCH / HEAD

| Attribute | Verified value |
|---|---|
| Repository | `7roger89-web/P2P-upgrade-github-1` (matches expected identity) |
| Current branch | `p2p-c38-live-role-certification` |
| Local HEAD | `8982ed4b4a85cefa3938006a7b99bd6b1cf06097` |
| Remote HEAD | `8982ed4b4a85cefa3938006a7b99bd6b1cf06097` (local = remote) |
| Working tree | clean (dirty = 0) |
| PR #15 | open, tip `8982ed4`, base C37 `4e5ef54`, draft |

**PROJECT_TRUTH_MISMATCH = NO.** The expected C38 checkpoint matches byte-for-byte.

## 3. C38 TERMINAL TRUTH — preserved

`PASS / LIVE_MULTI_BACKEND_ROLE_CERTIFIED` as recorded. Stage B (`p2p_iris` × Manus API v2) VERIFIED; Stage C (`p2p_iris` × Hermes CLI × gemini-2.5-flash) VERIFIED; Stage D `FRESH_EXECUTION_CAPSULE_RECOVERY = VERIFIED`, `SESSION_DEATH_RECOVERY = NOT_PROVEN` (not reinterpreted); `CANDIDATE_REQUIRED = NO`, NOT_MINTED (machine-derived, both CASE A and CASE B paths converge); NONE promotion. Evidence blobs in `docs/p2p-development/research/c38/evidence/` and Stage harnesses in `docs/p2p-development/research/c38/harness/` are intact at HEAD. C38 remains terminal and immutable in meaning.

## 4. C37 SELECTOR TRUTH

Selector machinery from C37 (`selection_target`, `selection_request`, `selection_filter`, `selection_policy`, `selection_quality`, `selection_receipt`, `selection_trace`, `selection_risk` in `.p2p/system/p2p_capabilities/`, plus `selection/*.py` modules and the C37 branch-head surface) is fully recoverable. Canonical C37 truths verified: suite 88/88 framework PASS at `4e5ef54`, closure CONSISTENT (0 hard, 1 EXPLAINED), candidate C37 UNPROMOTED at recorded SHA256, goal "Adaptive Target/Model/Effort Selection" closed DONE in governance roadmap. The selector is a **selection** authority: it produces an ordered eligible-target receipt, never a dispatch decision — registry ≠ router, selection ≠ execution, both preserved.

## 5. EXISTING LIVE BACKENDS

| Backend | Adapter | Certification |
|---|---|---|
| Manus API v2 | `manus_adapter.py` | C34 LIVE_VALIDATED, C38 Stage B VERIFIED |
| Hermes CLI (hermes-agent 0.20.4 installed in this sandbox) | `hermes_adapter.py` | C38 Stage C VERIFIED |
| Codex | `codex_adapter.py` (exists from C34/C35 work) | never live-certified; historically HTTP 401 |

## 6. CURRENT AUTH STATES (checked NOW, live probes, no secret values exposed)

| Backend | Current state | Evidence |
|---|---|---|
| Manus | **AUTH_INVALID — expired** | `api.manus.ai/v2/task.list` → HTTP 401 `{"code":"unauthenticated","message":"api key has expired"}` (also rejected on `api.manus.im/v1/tasks`) |
| Hermes × Gemini | **AUTH_VALID** | `hermes -z "capital of Vietnam?" --provider gemini --model gemini-2.5-flash` → `Hanoi`, exit 0 |
| Codex | **AUTH_ABSENT** | no binary, no credential |

The Manus key supplied during C38 Stage A/B has **expired since C38** (API-side revocation, not a sandbox artifact). Recorded as truth. The Gemini credential is current and live.

## 7. CURRENT ELIGIBILITY STATES (machine-level, fail-closed)

Per `selection_risk` + `backend_contract` semantics: UNKNOWN/INVALID auth fails closed → not eligible. **Manus = INELIGIBLE (current)** despite historical C38 LIVE_CERTIFIED. **Hermes × Gemini = CURRENTLY_ELIGIBLE** (auth VALID + C38-certified). **Codex = INELIGIBLE** (absent + never certified). Exactly one certified live backend is currently usable: C39's two-backend live proof cannot begin until the Manus credential is refreshed — this is the single Auth Gate.

## 8. BUILD-vs-REUSE MAP

| C39 requirement | Classification |
|---|---|
| Target registry / eligibility / fingerprint-drift (C30) | **REUSE** |
| AutoPilot loop, Continue Gate, budget, durable state (C33) | **REUSE** |
| BackendExecutionBridge, adapters, backend contract (C34) | **REUSE** |
| RoleExecutionContract, role bridge, verifier, canonical roles (C35) | **REUSE** |
| Context manifest/envelope/cache, LoopGuard, read evidence (C36) | **REUSE** (Stage F) |
| Target/model/effort selector, receipts, quality ordering (C37) | **REUSE** |
| C38 live receipts + capsule evidence | **REUSE** (Stage F identity carry) |
| Error-class → action taxonomy (AUTH_DRIFT/TARGET_DRIFT/TIMEOUT/RATE_LIMIT etc.) | **EXTEND** (`selection_risk` risk derivation; taxonomy already present in `backend_contract`) |
| Dispatch-boundary + mutation knowledge for unsafe-state handling | **EXTEND** (execution_status `PARTIAL_MUTATION_UNKNOWN` exists; the decision machine over it does not) |
| Failover-boundary decision machine (UNKNOWN → STOP_FAIL_CLOSED; unsafe → DO NOT FAILOVER) | **CREATE_ONLY_IF_NECESSARY** — exactly one new module, and only because no existing authority emits `RETRY_SAME_TARGET / RESELECT_TARGET / OWNER_GATE / STOP_FAIL_CLOSED` as a unified fail-closed surface |
| Anything resembling a second selector/router/AutoPilot/verifier/registry/permission authority | **REJECT_DUPLICATION** |

No authority collision: selection decides targets, the bridge executes them, the verifier certifies them, gates bound budgets — four distinct authorities with no overlap, preserved as-is.

## 9. DUPLICATION RISKS

Zero new selector/router/verifier is created. The single CREATE_ONLY_IF_NECESSARY module consumes the existing selector receipt (it reselects *from* the C37-ordered receipt via the bridge, never against it) and the existing verifier (failover success is proven through the same role verifier, not a second one). Vendor-specific core branching is rejected: failover policy is vendor-neutral, keyed by error classes, not provider names.

## 10. FAILOVER SAFETY GAPS (honest assessment)

Machinery already distinguishes PRE/POST-dispatch failure (via dispatch-ordering of task identity), AUTH drift (auth_state_after + EXPIRED/INVALID states), target drift (fingerprints), network/rate-limit/timeout (adapter error mapping), verification failure (verifier fail-closed), and MUTATION_UNKNOWN/RESULT_UNKNOWN (`PARTIAL_MUTATION_UNKNOWN` status). What is **missing**: (a) an explicit pre-dispatch revalidation step (health + auth re-check before dispatch), (b) the unified decision machine mapping each failure class to `RETRY_SAME_TARGET / RESELECT_TARGET / OWNER_GATE / STOP_FAIL_CLOSED` with UNKNOWN never silently becoming RESELECT, and (c) an enforced STOP_FAIL_CLOSED rule for any mutation-unknown/timeout-after-write state. These are precisely the C39 B/D/E scope — all built as EXTEND/CREATE_ONLY_IF_NECESSARY over existing contracts, fail-closed by construction.

## 11. PROVISIONAL C39 TASK GRAPH

Stages A–H as specified, no split/merge required. Reasons: recovery (A) and build-vs-reuse (B) are complete in this report; C (governed live target selection) uses the existing selector over the current eligible set with a selection receipt; D (pre-dispatch drift) needs the refreshed Manus key; E (post-dispatch safety) proves unsafe states stop fail-closed; F (capsule/context preservation across backend change) reuses C36 envelopes and the C38 capsule pattern; G (independent verification + regression, baseline `8982ed4`, expected validator 71/71, delta 0); H (candidate policy via the committed `candidate_policy` machine, both CASE A and CASE B paths evaluated, and closure machine).

## 12. EXPECTED RUNTIME SURFACE

One new module (`failover_boundary.py`-class, CREATE_ONLY_IF_NECESSARY) consuming existing selector/bridge/contract artifacts; possible small EXTEND to `selection_risk` (failover-risk class). **No** second selector, router, verifier, bridge, registry, or permission authority. No vendor-specific branching.

## 13. EXPECTED TEST SURFACE

New unit suite for the fail-closed decision machine (failure-class → action table, UNKNOWN→STOP cases); selection-regression suite over C37 fixtures; reuse of existing role-verifier and adapter contract tests. Framework validator expected at 71/71 with zero new hard findings beyond explainable ones.

## 14. EXPECTED LIVE-PROOF STRATEGY

Bounded non-mutating tasks only. Stage C: selection receipt over the eligible set → execute through the bridge → independent verifier receipt (same schema as C38). Stage D: pre-dispatch revalidation with an artificially expired/invalid target → safe reselection without duplicate execution. Stage E: dispatch with failure injection → unsafe-state STOP_FAIL_CLOSED. Stage F: capsule carries role/context/evidence identity across the backend change; the fresh task reads only the capsule. All answers read independently via backend-native read paths (Manus `task.listMessages` / Hermes raw stdout capture), never from self-claims.

## 15. AUTH / BEGINNER-FIRST GATE (the only ask)

**Bạn cần làm đúng 1 việc: lấy một API key Manus mới** (key cũ đã hết hạn trên phía Manus, tôi không thể tự khôi phục).

1. Vào trang Manus (manus.im), đăng nhập tài khoản của bạn.
2. Ở menu cài đặt, mở mục **"API Integration"** (hoặc "API Keys").
3. Bấm **"Create API Key"**, đặt tên gợi ý `p2p-c39-live-target-selection`. Key hiện ra trên màn hình **chỉ một lần**.
4. Lưu key vào máy bạn: mở Notepad → dán key → lưu thành file `manus_key_new.txt`.
5. Gửi file đó cho tôi trong chat như một file đính kèm (giống lần key GitHub và Manus trước). Tôi sẽ lưu an toàn ngoài Git và không in ra.
6. Sau khi xong, nhắn đúng 1 câu: **"Đã xong."** — tôi tự động chạy tiếp từ Stage B. (Riêng tư hơn: đừng dán key vào chat; sau này bạn có thể xóa key cũ ở trang API Integration.)

## 16. EXPECTED C39 END STATE (if PASS)

`PASS / GOVERNED_LIVE_TARGET_SELECTION_AND_SAFE_BOUNDED_FAILOVER` with `CANDIDATE_REQUIRED` machine-derived (both paths), NO merge/promote/release — matching the stated roadmap where C40 owns project-usable release + fresh install/upgrade/rollback + pilot (Game Truyện first, then Gia Phả, then Logistics).

## 17. REPRODUCTION EVIDENCE

All probes: `docs/p2p-development/research/c39/evidence/c39-auth-preflight.py` + `c39-auth-preflight.json` + this report. Git snapshots at HEAD `8982ed4`. Nothing regenerated, no history rewritten, no runtime touched.

---

**START CONDITION: READY_FOR_C39 — pending the single Auth Gate (§15).**
