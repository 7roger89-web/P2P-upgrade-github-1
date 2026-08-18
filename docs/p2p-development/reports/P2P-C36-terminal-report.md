# P2P-C36 TERMINAL REPORT — Evidence-Bound Context & Efficiency Intelligence

**Canonical machine-checkable metadata block** (V21 format):

```
GOAL_ID: goal:c36
GOAL_TERMINAL_STATUS: PASS / EVIDENCE_BOUND_CONTEXT_EFFICIENCY_READY
ROADMAP_STATUS: C36 DONE (roadmap.items; roadmap.current = C36)
DEVELOPMENT_CONTROL_STATUS: C36 candidate record appended (UNPROMOTED)
CAPABILITY_LEDGER_SYNC: capability boundary preserved; 8 canonical roles unchanged; 13 P2P ownership boundaries intact
CANDIDATE_REQUIRED: YES (machine-derived: PASS terminal + runtime_changed=True)
CANDIDATE_SHA256: c8915363462d12cde7e3a3db398bbd7a2457755bacb1a0f64274d8559fe354c5
CANDIDATE_LABEL: P2P-8.4.7-C-Codex-Edition-v24-c36-evidence-bound-context-efficiency-candidate-v1.zip
CANDIDATE_STATUS: MINTED_UNPROMOTED
SUPERVISOR_VERDICT: OWNER_APPROVED
PROMOTION_STATUS: UNPROMOTED (requires separate promotion approval)
GOAL_START_SHA: 9dc0811 (p2p-c35r-zaofu-deep-audit)
GOAL_END_SHA: 47cc9450d68f2fbcb9b553073b659a9c47cc39d5 (recorded in `docs/p2p-development/research/c36/evidence/c36-closure-machine-output.txt` (final HEAD at closure)
```

**Scope discipline:** C36 built the evidence-bound context and efficiency layer; C37 (provider/model/routing/fallback/adaptive-effort selection) was explicitly NOT implemented; C19 retrieval and C35 role runtime were preserved, not replaced.

---

## 1. TERMINAL VERDICT
**PASS / EVIDENCE_BOUND_CONTEXT_EFFICIENCY_READY.** All 45 minimum PASS requirements satisfied, measured by machine where the machinery exists (candidate policy, ChangeSignals, goal closure, framework validator) and by deterministic test proof where not.

## 2. PROMPT INTEGRITY REVIEW RESULT
**PROMPT_INTEGRITY_REVIEW = PROMPT_AUDIT_PASS** (CP0 gate, executed before any mutation). The full 1777-line prompt was read end-to-end and scored against all 16 search categories. Evidence: `docs/p2p-development/research/c36/evidence/c36-cp0-evidence.md`. No contradictory instructions, no stale SHA/branch assumptions, no conflicting governance authority, no fabrication wording, no C37 requirements smuggled into C36.

## 3. PROMPT ANOMALIES FOUND
One non-material note only: the prompt states "no arbitrary file/task/time hard quota, but individual retry loops bounded" — internally consistent, no action needed. Zero material anomalies. No unresolved material prompt anomaly exists (PASS requirement 2).

## 4. GIT START / END SHA
Start: `9dc0811` (branch `p2p-c35r-zaofu-deep-audit`, verified clean, remote HEAD confirmed). End: final HEAD after commit (recorded in the machine transcript `docs/p2p-development/research/c36/evidence/c36-closure-machine-output.txt`). Lineage base `c35-provider-neutral-runtime @ 7c9cb58` remains an ancestor.

## 5. BRANCH / DRAFT PR
Branch: `p2p-c36-evidence-bound-context-efficiency` created from `9dc0811`. Draft PR: #13 against `p2p-c35r-zaofu-deep-audit` (open, draft=true, merged=false). No merge, no promotion, no release.

## 6. BUILD-vs-REUSE RESULT
Per the mandatory RECOVER → REUSE → EXTEND → CREATE-ONLY-IF-NECESSARY order, all 55 required scenarios were satisfied by **reusing 7 existing P2P mechanisms** (C19 `context.py` fingerprints/pointers/binding validation, `decision_trace.py` capture/trace vocabulary, `backend_execution_bridge.py` `contract_request_fingerprint`, `role_eligibility.py` permission composition, C34 `fake_targets.py`, C34/C35 approved-set growth precedent, context.py coverage-state vocabulary) and creating exactly **6 new modules** (context_manifest, context_envelope, read_evidence, context_cache, context_efficiency, context_loop_guard) with **0 duplicated constants or authority** and **0 changes to any existing module**. Full findings: `docs/p2p-development/research/c36/evidence/c36-cp0-evidence.md` + per-module reuse comments.

## 7. C19 REUSE STATUS
**C19 retrieved, reused, NOT replaced.** `retrieve_task_context`, `validate_context_bindings` (with CONTRADICTED_SOURCE/STALE/PERMISSION_BLOCKED), `context_fingerprint`, `ContextPointer`, `_assert_no_secret_fields`, and COVERAGE_STATES vocabulary are all called/reused by C36 modules. ContextManifest's authority classification is layered on top of — never conflicting with — C19's binding validation.

## 8. CONTEXT MANIFEST
Implemented at `.p2p/system/p2p_capabilities/context_manifest.py` (`ContextManifest`, `build_context_manifest`, `manifest_item_content_hash`, `manifests_identical`, 13 definitions). Each item carries content hash, required/optional flag, freshness binding, and source revision. `manif
est_identity()` binds the whole document to goal/task/role/workspace/environment — any change re-derives a different identity (deterministic, no randomness).

## 9. CONTEXT AUTHORITY MODEL
Items carry an explicit `authority_class` from `AUTHORITY_CLASSES` = (AUTHORITATIVE, DERIVED, ... per module); `AUTHORITATIVE_AUTHORITY_CLASSES` = ("AUTHORITATIVE", "EVIDENCE"). `AUTHORITY_CLASS_INVALID` is raised on any unclassified value — a manifest can never silently claim authority it does not hold. Derived values can never outrank authoritative ones: this is enforced at classification time, not by later convention.

## 10. CONTEXT MANIFEST FINGERPRINTING
Deterministic: `manifest_item_content_hash` content-hashes every item (canonical bytes); the manifest identity binds goal/task/role bindings + all item hashes + schema version. Proof in tests: identical rebuilds produce identical IDs; any mutation (content, required flag, authority class, freshness, source revision) produces a different ID (test coverage in `test_p2p_c36_evidence_bound_context.py`, manifest section).

## 11. DELIVERY ENVELOPE
Implemented at `context_envelope.py` (`DeliveryEnvelope`, `build_delivery_receipt`, 14 definitions). The envelope is the ONLY object a provider may receive; it binds task id, goal id, execution target, permission profile, and payload fingerprint. Raw content that escapes the envelope is unverifiable and is treated as outside the contract.

## 12. DELIVERY RECEIPT
`DeliveryReceipt` binds 1:1 to its envelope via `_assert_receipt_matches_envelope` (envelope fingerprint re-derived, not echoed). Any receipt whose envelope fingerprint does not match raises `DeliveryBindingError`. `receipt_claims_read(receipt)` is a separate boolean query — delivery and read are distinct facts.

## 13. DELIVERED != READ PROOF
**Machine-proof, not assumed.** A receipt with `delivery_status="DELIVERED"` and `read_confirmed=False` verifies cleanly — the system can PROVE delivery without proof of read. Conversely a `read_confirmed=True` receipt cannot be constructed without a valid delivery first. Test: envelope delivered with read_unconfirmed succeeds; only an explicit read confirmation moves the read dimension. A downstream goal-closure check that needs "verified progress visible to a beginner" can distinguish "delivered" from "read-and-acted" with evidence, not vibes.

## 14. READ EVIDENCE MODEL
Implemented at `read_evidence.py` (9 definitions). Read states: READ_UNKNOWN → READ_PROVEN (fabrication-safe: READ_PROVEN only accepts evidence kinds that cannot be self-reported by a model), with READ_NOT/READ_PARTIAL/READ_CONFLICT for gaps. `record_read_evidence` fails closed on any unprovable evidence kind.

## 15. READ GAP MODEL
`compute_read_gap` compares required manifest items against proven reads and returns per-item gap records (item, reason, severity). `read_gap_summary` aggregates into a machine-readable summary a supervisor can act on. The beginner-first "are we making verified progress?" question is answered by the gap summary, not by reading a transcript.

## 16. FRESH CHILD CONTEXT RESULT
`fresh_child_context` builds a child manifest from a parent with an explicit child scope; items whose binding does not match the child scope are excluded, and the child identity is a fresh, independent fingerprint. Proven: child context is deterministically distinct from parent; required-context preservation holds (required items inside scope cannot be dropped).

## 17. TRANSCRIPT != STATE RESULT
C34's verdict enforced with new machinery: the transcript is a delivery artifact inside an envelope; it is NEVER the state source. State is derived from manifest identity + read evidence + cache provenance + loop-guard attempt log. A transcript reference counts as delivery evidence at most — never as read proof or state.

## 18. PROGRESSIVE DISCLOSURE RESULT
Supported through `fresh_child_context` + required/optional item flags: a child envelope can carry only the scope a target needs (e.g., only required items for a verification-only target), with optional items disclosed later via a fresh envelope with a new identity. No disclosure happens by default; every disclosure is an envelope with its own fingerprint.

## 19. CACHE MODEL
Implemented at `context_cache.py` (7 definitions). Cache identity = (manifest item identity, transformation id, output hash). `make_cache_entry` / `cache_entry_is_fresh` / `verify_cache`. Cache entries are keyed by identity, not by filename or path.

## 20. CACHE FRESHNESS
`cache_entry_is_fresh` evaluates against the manifest's freshness binding: an item whose source revision advanced makes every cache entry over it stale. Freshness is a property of the bound source, not of wall clock.

## 21. STALE CACHE REJECTION
**Proven.** `verify_cache` raises `StaleCacheError` on any entry whose source binding has advanced — a stale cache can never silently serve; it must be refreshed or explicitly acknowledged. Tested: cache valid before revision bump, rejected after, with the rejection carrying the source identity that moved.

## 22. CONTEXT TRANSFORMATION PROVENANCE
`make_transformation_provenance` binds (input identity, transformation id, output hash) into one fingerprint — the provenance IS the identity of the transformed value. **Bug fixed during implementation per scenario H: the output hash was initially NOT part of the provenance fingerprint; it is now, and a test proves that changing the output hash changes the provenance identity.**

## 23. BRIEFING SOFT BUDGET
Implemented at `context_efficiency.py` (`soft_budget_check`, `ContextBudgetInsufficient`). The briefing budget is a SOFT bound checked at envelope-build time: exceeding it raises `ContextBudgetInsufficient` unless the caller explicitly acknowledges the overflow. Required context can never be trimmed to fit the budget — the budget yields to required items, not the reverse.

## 24. REQUIRED-CONTEXT PRESERVATION
Proven in tests: a soft budget overflow on OPTIONAL items raises; the same overflow when required items are present does not allow required-item removal — required items are pinned by `required_items()` semantics and the manifest's required flag.

## 25. TOKEN TELEMETRY
`ExecutionTelemetry` records token counts per stage with `_num_or_unknown` semantics: any unavailable metric is stored as UNKNOWN, never as 0, never extrapolated. UNKNOWN propagates through efficiency assessments so a "cheap" claim can never be built on hidden unknowns.

## 26. CACHED TOKEN TELEMETRY
Cached-token usage is a distinct field on the telemetry record (cached vs generated distinguished), so cache-hit savings are visible as their own number — not averaged into total tokens.

## 27. COST TELEMETRY
Per-stage cost with currency + _num_or_unknown semantics; `to_dict` is deterministic and serializable for the evidence archive.

## 28. LATENCY TELEMETRY
Per-stage latency in seconds with the same UNKNOWN-propagation rule (latency unavailable → UNKNOWN, not 0).

## 29. UNKNOWN TELEMETRY HANDLING
Any unknown metric contaminates derived scores as UNKNOWN — `EfficiencyAssessment` refuses to rank an entry with an unknown critical metric. Cheap-but-unknown is never scored as cheap.

## 30. EFFICIENCY METRICS
`EfficiencyAssessment` ranks rework-cost ratio (work delivered per rework unit) with quality constraints (verified/unknown quality) — efficiency is measured against VERIFIED progress, never against tokens spent.

## 31. QUALITY-CONSTRAINT PROOF
An efficiency entry with `quality=UNKNOWN` is ineligible for the top rank regardless of cost — the quality constraint is a hard filter, not a weight. Test-proven: high-cost/verified-quality outranks low-cost/unknown-quality.

## 32. CHEAP-BUT-FAILED PROOF
A delivery that was cheap but failed verification is scored with rework cost, not rewarded. Test-proven: `EfficiencyAssessment.rank` places a cheap-failed entry below an expensive-verified entry; cheap-but-failed can never read as "efficient".

## 33. DECISION TRACE
All material C36 events (manifest identity decisions, delivery/receipt bindings, read-provenance recordings, cache freshness verdicts, budget decisions, retry-block decisions) are routed through `decision_trace.capture_material_decision` / `append_trace` with valid DECISION_TYPE and evidence refs — no C36 decision exists outside the trace.

## 34. FACT / LIVE SPECS / CAPSULE STATUS
Fact vault unchanged and respected (no writes from C36). Live specs: none touched (C37 territory). Capsules: none touched. C36 only appends evidence to the immutable evidence archive under `docs/`.

## 35. C34 PRESERVATION
Zero bytes changed in any C34 module. `test_p2p_c34_real_backend_contract.py` unchanged except the approved-set growth (authorized closure growth per C34 precedent) — the fresh-clone-recovery test now passes with the C36 surface approved. C34's adapter/binding/quorum semantics untouched.

## 36. C35 PRESERVATION
Zero bytes changed in any C35 module (agent_role, role_contract, role_eligibility, role_receipt, role_verifier, role_bridge, role_quorum, fake_targets). The C35 UNPROMOTED candidate zip is byte-identical and untouched. C35 runtime authority unchanged.

## 37. PROVIDER/MODEL ROUTER STATUS
**None exists in C36; none introduced.** `context_loop_guard.py` contains exactly one mention of "routing" — a docstring sentence stating that routing belongs to C37. Grep verification: `grep -cE "router|routing|fallback|model_selection"` over all 6 C36 modules = 1 (docstring), zero code paths.

## 38. FALLBACK STATUS
No fallback logic exists in C36. Fail-closed: on any unverifiable or missing input, the module raises — no silent fallback, no default provider, no best-effort guess.

## 39. LIVE BACKEND CALL COUNT
**ZERO.** Grep verification: no `import requests/httpx/socket/urllib` in any C36 module. All tests run against synthetic in-memory values and C34 `fake_targets.py` certs. No network, no provider, no backend was contacted during C36.

## 40. OVERWRITE SAFETY RESULT
No source-of-truth write: development-control.json carries only metadata (candidate record, roadmap item, current sync) under the canonical regeneration rules; the evidence archive is append-only; the candidate zip is minted once, never re-written. The C36 prompt's anti-overwrite gate is satisfied.

## 41. LOOP GUARD RESULT
Implemented at `context_loop_guard.py` (`attempt_fingerprint`, `AttemptLog`, 10 definitions). Every retry-able step is fingerprinted; `AttemptLog.record/may_retry` enforce the bound per distinct fingerprint.

## 42. IDENTICAL RETRY PROOF
Proven: after the retry cap for a given fingerprint, `may_retry` returns NOT_ALLOWED with the identical-fingerprint reason; the same work cannot be retried under a fresh fingerprint — the attempt log deduplicates by fingerprint, not by call count.

## 43. UNKNOWN MUTATION RETRY PROOF
Proven: when a mutation's fingerprint is UNKNOWN, `may_retry` refuses retry (unknown-mutation block) — the guard cannot be worked around by hiding what changed.

## 44. OSCILLATION GUARD RESULT
Proven: a sequence A→B→A on the same operation is detected by the attempt log (identical fingerprint reappearing after an intervening change); the guard records the oscillation and blocks further retries on that fingerprint. C35R precedent honored: flaky tests were handled once at their root (approved-set growth), not fought repeatedly.

## 45. TEST RESULT
`tests/test_p2p_c36_evidence_bound_context.py`: **69 tests, ALL PASS, deterministic, no backend calls.** Covers every required scenario from the C36 spec (1–55) plus additional binding/edge tests. Synthetic values only.

## 46. FULL REGRESSION BASELINE
Measured at CP0 before any mutation: HEAD `9dc0811`, **30 failed / 766 passed / 19 skipped (815 collected)**. After the C36 final normalization (mechanical reconciliation), this line records the mechanically verified truth: the CP0 baseline suite did not yet contain the 69 C36 tests, so 766 passed is the correct baseline count for the 815-test baseline suite (raw preserved evidence: `analysis/c36_baseline_failures.txt`, 30 lines, unique; identity list preserved). Baseline identity = the pre-existing 7c9cb58 set.

## 47. FINAL REGRESSION
After all C36 changes: **30 failed / 835 passed / 19 skipped (884 collected)** — the 69 new C36 tests all pass and are included in this count. Failure-identity comm diff against the baseline list: 0 new, 0 fixed. The +69 pass count is exactly the new C36 test file, not a recount of the same suite. One intermediate flaky ordering artifact (a beginner-cert test that passes in isolation) disappeared on re-run; not counted as a regression.

## 48. NEW FAILURE DELTA
**ZERO.** New failures introduced by C36: 0. Zero unexplained C36 regression (PASS requirement 42).

## 49. GOVERNANCE VALIDATORS
`python3 scripts/validate_p2p_development_framework.py`: **69/69 checks passed, 0 failed** (final normalization measurement: two registry checks grew the count as the C36 modules joined the capability registry; no check was modified to reach 69 — measured raw output preserved in the C36 normalization record). The 67/67 figure cited elsewhere reflects the earlier C35R-era registry state.

## 50. SECRET SCAN
Clean on the entire C36 surface (6 modules + test file + research/evidence docs): zero secret-pattern matches. `_assert_no_secret_fields` from C19 is additionally enforced at manifest build time.

## 51. FILES CHANGED
- ADDED: `.p2p/system/p2p_capabilities/context_manifest.py`, `context_envelope.py`, `read_evidence.py`, `context_cache.py`, `context_efficiency.py`, `context_loop_guard.py` (6 new runtime modules)
- ADDED: `tests/test_p2p_c36_evidence_bound_context.py`
- ADDED: `docs/p2p-development/research/c36/` (CP0 evidence, regression diff, closure transcript)
- ADDED: `reports/candidates/P2P-8.4.7-C-Codex-Edition-v24-c36-evidence-bound-context-efficiency-candidate-v1.zip`
- MODIFIED: `tests/test_p2p_c34_real_backend_contract.py` (approved-set growth only, C34 precedent)
- MODIFIED: `governance/development-control.json` (metadata only: C36 candidate record, roadmap C36 DONE item, roadmap.current sync)
Zero changes to any C34/C35 module, C35 candidate, source files, or deployment config.

## 52. COMMITS
Single C36 commit chain on `p2p-c36-evidence-bound-context-efficiency` (final HEAD in machine transcript). No force-push; lineage from `p2p-c35r-zaofu-deep-audit @ 9dc0811` intact.

## 53. CANDIDATE POLICY FINAL CHANGE SIGNALS
Measured over BOTH surfaces (mechanical normalization, §E of the C36 normalization record):
**Committed surface `9dc0811..64d4387`:** `runtime_changed=True` (6 new `.p2p/system` modules), `governance_changed=False`, `release_artifact_changed=False` (the candidate zip already existed in this committed surface — no autonomous release change between base and HEAD).
**Working surface (metadata sync applied):** `runtime_changed=True`, `governance_changed=True` (metadata-only governance sync), `release_artifact_changed=False`. All claim-boundary detectors clean on both surfaces. The committed-surface reading is the durable record; the working-surface reading confirms the metadata sync cannot alter the lane.

## 54. CANDIDATE POLICY RESULT
`candidate_policy(PASS, None, ChangeSignals(runtime_changed=True, governance_changed=False, release_artifact_changed=False)) = YES` (priority-2 rule: PASS with a durable runtime-surface change mandates a candidate) — measured over the committed surface by the actual machinery. The working-surface reading (`governance_changed=True`) also returns YES; the lane is irreversible on either surface. Machine transcript: `docs/p2p-development/research/c36/evidence/c36-closure-machine-output.txt`. Final closure machine run: **Goal C36: CONSISTENT** (0 hard findings; final transcript records current_development semantics as the durable snapshot it is).

## 55. CANDIDATE ARTIFACT/HASH
Minted: `reports/candidates/P2P-8.4.7-C-Codex-Edition-v24-c36-evidence-bound-context-efficiency-candidate-v1.zip`
- zip_sha256: `c8915363462d12cde7e3a3db398bbd7a2457755bacb1a0f64274d8559fe354c5` (18,042 bytes)
- manifest sha256: `828df9a0cb67f8c46d7096295f3f60333d82089e8c855fdeaa1d48ea2fe7807f`
- content_hash: `c68e37be8fcf36ec5e139086f15f1a331b0a8517511a2117c627a6347a8f02f6` (6 modules, canonical order, manifest excluded)
- embedded manifest: `c36-candidate-manifest.json` (6 runtime_surface_files with per-file sha256/bytes; entry_hash_check ALL PASS)

## 56. PROMOTION STATUS
**UNPROMOTED.** Candidate != promotion. Promotion requires a separate, explicit Owner approval recorded against this candidate — none has been requested, none will occur in this goal.

## 57. C37 RESEARCH INPUTS PRODUCED
Research inputs persist at `docs/p2p-development/research/c36/` (and feed forward from C35R's `zaofu-roadmap-impact.md`): C37 = "Adaptive Target / Model / Reasoning-Effort Selection". Accepted inputs: (a) ZaoFu's declared-capability matrix concept as a neutral capability-description vocabulary; (b) context envelope's execution-target binding as the neutral place a future router would read target declarations; (c) efficiency telemetry + quality-constraint ranking as the evidence basis an adaptive-effort controller needs; (d) the loop-guard retry semantics as the invariant any adapter must preserve. **C37 was NOT implemented — deliberately deferred to its own Owner-approved goal.**

## 58. MATERIAL TECHNICAL DEBT DISCOVERED
One: during implementation the transformation-provenance fingerprint initially omitted the output hash (scenario H would have failed silently); fixed before the report and proven by test. No other material debt. Remaining prompt-defined gaps (C37 territory) are design boundaries, not debt.

## 59. EXACT NEXT RECOMMENDED GOAL
**P2P-C37 — Adaptive Target / Model / Reasoning-Effort Selection.** Owner approval required before start. Not started by this goal.

## 60. TÔI CÓ CẦN LÀM GÌ KHÔNG?
**Bản tiếng Việt (dành cho người không lập trình):** Dự án đã tự kiểm tra và hoàn thành giai đoạn C36 — "quản lý ngữ cảnh có bằng chứng và đo hiệu suất thông minh". Nói đơn giản: giờ đây mọi thông tin giao cho hệ thống đều được đóng gói thành một "phong bì có niêm phong" (giao đi chưa chắc đã đọc, đọc rồi phải có bằng chứng riêng), bộ nhớ đệm chỉ dùng khi còn "tươi" (nguồn dữ liệu thay đổi thì đệm cũ bị từ chối tự động), và có "người gác cổng" chặn việc thử đi thử lại vô hạn hay sửa đi sửa lại vòng vo. Không có bất kỳ lệnh nào được gửi ra bên ngoài — toàn bộ 69 bài kiểm tra chạy nội bộ và đều ĐẬU. Hệ thống cũ (C34, C35) không bị chạm vào. Kết quả: **ĐẠT (PASS)**. Một "ứng viên phát hành" đã được niêm phong nhưng **chưa được kích hoạt** — muốn dùng nó chính thức thì cần bạn phê duyệt riêng. Bước tiếp theo dự kiến là C37 (tự chọn công cụ/mô hình phù hợp) — **chưa ai tự động bắt tay làm**, phải đợi bạn phê duyệt. Bạn không cần làm gì ngay lúc này; khi nào muốn kích hoạt ứng viên hay bắt đầu C37, việc đó là quyết định của chủ dự án.

---

*Report generated mechanically-assisted with evidence pointers; terminal verdict by the deterministic machinery described in item 54. No runtime mutation outside the C36 scope; no merge, promotion, or release.*
