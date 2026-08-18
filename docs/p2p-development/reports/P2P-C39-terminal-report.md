# P2P-C39 — TERMINAL REPORT

**GOAL_ID:** P2P-C39
**GOAL_TITLE:** Governed Live Target Selection & Safe Failover (failover-boundary decision machine; 4 proofs live + deterministic; regression clean; candidate UNPROMOTED)
**GOAL_TERMINAL_STATUS:** **PASS / GOVERNED_LIVE_FAILOVER_READY**
**CANDIDATE_REQUIRED:** YES (deterministic — machine-derived `candidate_policy(PASS, None, ChangeSignals(runtime_changed=True)) = YES`)
**CANDIDATE_STATUS:** MINTED, UNPROMOTED — 1 candidate duy nhất
**CANDIDATE_SHA256:** a999552538adb98332c039af8bb117a13fad3991605c543668034a89da4eb387
**CANDIDATE_LABEL:** P2P-8.4.7-C-Codex-Edition-v24-c39-governed-live-failover-candidate-v1.zip
**PROMOTION_STATUS:** NONE (no merge / promote / release)
**ROADMAP_STATUS:** DONE (`roadmap.current.id = C39`, `status = DONE`)
**DEVELOPMENT_CONTROL_STATUS:** `current_development` retained as C31/BLOCKED_TERMINAL historical snapshot — explained semantics per C35R/C38 precedent; closure machine CONSISTENT, 0 hard findings
**CAPABILITY_LEDGER_SYNC:** no capability promotion (failover boundary verified, not promoted)
**GOAL_BASE_COMMIT:** `8b751f6` (C39 starting-truth commit)
**GOAL_BRANCH:** `p2p-c39-governed-live-failover`
**CURRENT_FINAL_HEAD:** `41b8e22bbddb19aa73caddb2e58543c0661af822` (machinery commit; working tree contains closeout docs-only changes)
**FRAMEWORK_VALIDATOR:** 71/71 PASS (V21 fields đầy đủ trong báo cáo mới nhất này)
**REGRESSION_DELTA:** 0 (`NEW_UNEXPLAINED_FAILURES = 0`; 46 baseline failures predate C39, identical failure-identity set vs baseline `41b8e22`)
**SECRET_SCAN:** clean (all secrets outside repo, mode 0600 in `/home/ubuntu/.secrets/`; no secret values printed or committed)
**LIVE_BACKEND_CALLS:** Proof 1 + Proof 2 + Proof 3 capsule = 3 live Manus tasks + 1 live Hermes×Gemini execution; Proof 4 = deterministic, zero backend calls

---

## 1. Tóm tắt cho Owner (tiếng Việt, đơn giản)

**C39 đã PASS.** Hệ thống P2P giờ có một "cổng an toàn" duy nhất quyết định khi nào được phép chuyển (failover) từ backend đang dùng sang backend khác, và cổng này luôn **đóng-khi-lỗi** (fail-closed): nếu không chắc chắn an toàn, nó chặn mọi hành động thay vì tự động chuyển.

- **Backend nào chạy thật:** Manus (API v2) chạy thật 3 nhiệm vụ; Hermes CLI × Gemini chạy thật 1 nhiệm vụ.
- **Failover có chạy thật không:** CÓ. Proof 2 tạo tình trạng "mất xác thực" một cách an toàn và đảo ngược được (không đụng vào key thật), cổng failover tự phát hiện và quyết định chuyển sang Hermes×Gemini — Hermes trả lời đúng "Hanoi". Đây là failover thật, trên hai backend thật.
- **Khi nào P2P KHÔNG được phép đổi backend:** Sau khi một tác vụ đã được gửi đi (dispatch), nếu kết quả/biến đổi (mutation) không xác định được, hệ thống TUYỆT ĐỐI KHÔNG được tự chuyển backend hay chạy tiếp — nó phải dừng đóng (STOP_FAIL_CLOSED) và chờ người xác nhận. Đây là nguyên tắc bất di bất dịch của C39.
- **Regression:** Sạch. Không có test nào hỏng mới do C39.
- **Candidate:** Máy chính sách yêu cầu 1 candidate → đã mint đúng 1, trạng thái UNPROMOTED (chưa thăng hạng), không merge/promote/release.
- **Đủ điều kiện sang C40 không:** CÓ — nhưng C40 là nhiệm vụ tiếp theo, cần Owner xác nhận, không tự bắt đầu.

---

## 2. Mục tiêu và phạm vi C39

C39 xây dựng **failover-boundary decision surface** duy nhất (nguyên tắc CREATE_ONLY_IF_NECESSARY) cho toàn runtime P2P, với:

- **33 failure classes** được phân loại (AUTH_INVALID, AUTH_DRIFT, MUTATION_UNKNOWN, RESULT_UNKNOWN, HEALTH_UNREACHABLE, …);
- **5 decisions**: `RETRY_SAME_TARGET`, `RESELECT_TARGET`, `REVERIFY_REQUIRED`, `OWNER_GATE`, `STOP_FAIL_CLOSED`;
- **Fail-closed semantics**: trạng thái không xác định (UNKNOWN) không bao giờ âm thầm trở thành RESELECT_TARGET; SELECTION ≠ EXECUTION; REGISTRY ≠ ROUTER; FAILOVER ≠ RETRY; FAILOVER ≠ SILENT FALLBACK — tất cả được bảo toàn.

**Auth gate:** Manus = AUTH_VALID (key mới `sk-EJRrJ…`, tệp `/home/ubuntu/.secrets/manus_api_key_new`, không trùng key C38 đã hết hạn); Hermes×Gemini = AUTH_VALID (`GEMINI_API_KEY`); Codex = AUTH_ABSENT (tuyên bố minh bạch, không che giấu).

## 3. Máy quyết định failover (CREATE_ONLY_IF_NECESSARY)

Tệp `.p2p/system/p2p_capabilities/failover_boundary.py` chứa hàm `decide_next_action` với thứ tự quy tắc được kiểm duyệt:

| # | Quy tắc | Điều kiện | Quyết định |
|---|---------|-----------|------------|
| 1 | Không lỗi + chưa dispatch + eligibility an toàn | `failure_class is None`, `dispatched=False`, target đủ điều kiện; nhường cho chủ gate nếu `owner_action_needed=True` | `RETRY_SAME_TARGET` (cấp phép dispatch bình thường); OWNER_GATE nếu có việc chờ Owner |
| 2 | Owner gate | `owner_action_needed=True` với drift/failure nghiêm trọng | `OWNER_GATE` |
| 3 | Auth drift trước dispatch | `failure_class=AUTH_DRIFT/AUTH_INVALID`, `dispatched=False` | `RESELECT_TARGET` |
| 4 | Lỗi nhẹ có thể thử lại | `dispatched=False`, failure class có retry-plan | `RETRY_SAME_TARGET` (bounded retry) |
| 5 | Mutation/Result UNKNOWN sau dispatch | `dispatched=True`, `mutation_status/RESULT` unknown | `STOP_FAIL_CLOSED` |
| 6 | Không có hành động an toàn nào | không quy tắc nào áp dụng | `STOP_FAIL_CLOSED` với lý do `NO_KNOWN_SAFE_ACTION` |

Quan trọng: trong quá trình thực thi Proof 1, một lỗi logic đã bị phát hiện và sửa — khi không có lỗi và chưa dispatch, máy rơi xuống `STOP_FAIL_CLOSED` (quy tắc 6) thay vì cấp phép dispatch bình thường. Máy đã được bổ sung **Rule 1** (cấp phép dispatch khi không có lỗi, với guard nhường quyền cho Owner gate), kèm 2 test mới; 104/104 test đơn vị deterministic đều PASS. 102 test gốc vẫn giữ nguyên hành vi.

## 4. Bằng chứng 4 Proof

| Proof | Nội dung | Backend | Kết quả |
|-------|----------|---------|---------|
| 1 | Lựa chọn live bình thường: probe eligibility → failover gate cấp phép (RETRY_SAME_TARGET) → dispatch Manus → câu trả lời quan sát độc lập | Manus API v2 | **PASS** — task `4wRTkQZvRd5hxBe2ZkWM29`, trả lời "Hanoi", xác nhận độc lập qua `task.listMessages` (không tin self-claim); verifier độc lập `verify_role_execution_receipt` = VERIFIED; `answer_is_capital_of_vietnam = True` |
| 2 | Drift xác thực TRƯỚC dispatch (reversible — chỉ bỏ biến môi trường `MANUS_API_KEY`, KHÔNG đụng key thật, sau đó khôi phục): probe trả `eligible=False, failure_class=AUTH_INVALID` → gate quyết định `RESELECT_TARGET` → thực thi trên Hermes CLI × Gemini → quan sát độc lập | Hermes×Gemini | **PASS** — task `2HX2kPL6PFiUphu6NybjNw`, trả lời "Hanoi", chấp nhận TRUE |
| 3 | Capsule continuity (nối tiếp bối cảnh): task Manus mới chỉ nhận capsule trạng thái C39 (không nhận transcript) → tái dựng đúng 11/11 trường (bao gồm challenge_hash, proofs_bound) | Manus API v2 | **PASS** — 11/11 kiểm tra khớp chính xác; `capsule_integrity_ok = True` |
| 4 | Unsafe post-dispatch (deterministic, KHÔNG gọi backend nào): 5 trường hợp MUTATION_UNKNOWN / RESULT_UNKNOWN sau dispatch | Không có | **PASS** — 5/5 trả về `STOP_FAIL_CLOSED`; Backend B không thực thi khi UNKNOWN |

Mọi câu trả lời đều được **quan sát độc lập** qua API (không phải self-claim của executor).

## 5. Regression & Framework Validator

- **Framework validator:** `71/71 PASS` (sau khi báo cáo này — báo cáo mới nhất — mang đủ 5 trường V21). Hai lỗi V21 còn tồn tại ở báo cáo C38 là lỗi có sẵn (báo cáo C38 được viết trước khi trường V21 ra đời; truth C38 bị đóng băng, không được sửa lại). **Semantics V21 đã được xác minh từ code** (evidence `c39-v21-semantics-verification.json`): V21 chỉ quét báo cáo terminal MỚI NHẤT theo glob `P2P-C*-terminal-report.md` (duy nhất 1 điểm glob, không quét các báo cáo trước). Việc C39 trở thành báo cáo mới nhất và mang đủ 5 trường là đúng semantics — không che lỗi C38.
- **Full regression differential:** baseline worktree tại `41b8e22` = 46f/1017p/11s; hiện tại = 46f/1019p/11s; **NEW_UNEXPLAINED_FAILURES = 0**. Một test tạm hỏng (test_fresh_clone_recovery của C34, tập chấp thuận cũ bị stale do C38/C39 thêm artifact hợp pháp) đã được xử lý bằng mở rộng tập chấp thuận đúng theo tiền lệ C34/C35R/C36/C37 — test PASS lại, không đổi hành vi máy. 46 test hỏng còn lại đều có sẵn từ baseline (môi trường/API, không liên quan C39).
- **Secret scan:** sạch — mọi key nằm ngoài repo (`/home/ubuntu/.secrets/`, mode 0600); không có giá trị bí mật nào được in ra hay commit.

## 13. CANDIDATE POLICY (đường máy chính xác)

| Kiểm tra | Bề mặt | Tín hiệu | `candidate_policy(PASS, None, signals)` | Ghi chú |
|----------|--------|----------|------------------------------------------|----------|
| A. Pre-metadata sync | 3 tệp vs base C39 `8b751f6` | runtime=T (failover_boundary.py), governance=F, release=F | **YES** (quy tắc ưu tiên: PASS terminal + thay đổi runtime bền vững bắt buộc có candidate) | — |
| B. Terminal declaration | tuyên bố qua máy (không khai báo trong contract) | — | — | machine-derived |
| C. Final surface | cùng bề mặt + governance closeout (docs-only) | runtime=T | **YES** | khai báo NO không tồn tại để ưu tiên |

**CLASSIFICATION: `CASE_A_RUNTIME_CHANGE_PATH`** (tương đương tiền lệ C36: có thay đổi runtime → candidate bắt buộc, không cần priority-path dispute). `CANDIDATE_REQUIRED = YES` là deterministic và policy-correct.

**Minting:** đúng 1 candidate — `P2P-8.4.7-C-Codex-Edition-v24-c39-governed-live-failover-candidate-v1.zip`, SHA256 `a9995525…`, trạng thái `UNPROMOTED`, promotion `NONE`. Package verification: `ARTIFACT_VERIFY_PASS` (zip SHA khớp, entry_hash_check ALL PASS cho failover_boundary.py, manifest hợp lệ). Không promotion, không release.

## 14. GOAL CLOSURE MACHINE

`goal_closure_verdict` (canonical, qua `load_governance` + `terminal_from_report`): **CONSISTENT** — 0 hard findings; 1 finding `CURRENT_DEVELOPMENT_SEMANTICS` ở mức `explained` (C31/BLOCKED_TERMINAL vs roadmap.current = C39 — tiền lệ C35R/C38: vị trí phát triển trực tiếp vs snapshot lịch sử, đúng semantics); ROADMAP_ITEM_EXISTS ok; PASS_WITH_DONE_ROADMAP ok; PASS_CURRENT_IS_DONE ok; CANDIDATE_REQUIRED_PRESENT ok; CANDIDATE_SHA_IMPLIES_ARTIFACT ok; CANDIDATE_VERIFY_EVIDENCE ok; cả 5 CLAIM_BOUNDARY PASS (ROUTER/CONTEXT_CONTROLLER/AUTH_ACTION/SECOND_EXECUTOR/BACKGROUND_AUTONOMY — không đưa vào).

## 15. PROJECT-USE ASSESSMENT (đánh giá riêng theo yêu cầu; không cài P2P vào project nào trong C39)

| Project | Assessment | Lý do |
|---------|------------|-------|
| Game Truyện | **PILOT_ONLY** | Nhiệm vụ tương tác phiến biến (bounded prompts), rủi ro thấp; là pilot đầu tiên theo thứ tự Owner — nhưng bản thân C39 chưa có gói cài đặt/rollback, pilot phải chờ C40 |
| Gia Phả | **PILOT_ONLY** | Dữ liệu cấu trúc genealogy, nguy cơ thấp, tận dụng capsule continuity; vẫn cần rollback + owner promotion gate của C40 trước |
| Logistics | **DO_NOT_INSTALL_YET** | Dữ liệu tài chính nhạy cảm; tuyệt đối chưa cài cho đến khi C40 chứng minh rollback/compatibility và Owner mở cổng promotion |

Thứ tự pilot đã tuân theo yêu cầu Owner: Game Truyện → Gia Phả → Logistics (Logistics cuối vì dữ liệu tài chính).

## 16. TERMINAL VERDICTS & BOUNDS

`C39_TERMINAL = PASS / GOVERNED_LIVE_FAILOVER_READY` · `VALIDATOR = 71/71` · `REGRESSION = NEW_UNEXPLAINED_FAILURES=0` · `SECRET_SCAN = CLEAN` · `CANDIDATE = MINTED (1, UNPROMOTED)` · `PROMOTION = NONE` · `CLOSURE = CONSISTENT (0 hard, 1 explained)` · `NO_MERGE_NO_PROMOTION_NO_RELEASE_NO_DEPLOY`.

Bốn truth ngữ nghĩa bất biến được duy trì: UNKNOWN không bao giờ âm thầm thành RESELECT_TARGET; FAILOVER ≠ RETRY; FAILOVER ≠ SILENT FALLBACK; Backend B KHÔNG được thực thi khi mutation/result UNKNOWN sau dispatch.

## 17. KHUYẾN NGHỊ SAU C39

Khuyến nghị goal kế tiếp: **`P2P-C40 — PROJECT-USABLE RELEASE & PILOT INSTALLATION`**. C40 chịu trách nhiệm: installable package, fresh install proof, upgrade proof, doctor/health, rollback, compatibility, real-project pilot (Game Truyện trước), Owner promotion gate.

Không tự bắt đầu C40. Không merge. Không promotion. Không release. Không deploy. Không cài P2P vào bất kỳ project nào. Sự tiếp tục duy nhất được phép: Owner xác nhận, rồi mở cổng C40.

---

*Báo cáo này là báo cáo terminal mới nhất của framework (bắt buộc bởi V21). Mọi evidence nằm tại `docs/p2p-development/research/c39/evidence/`; harness tại `docs/p2p-development/research/c39/harness/`.*
