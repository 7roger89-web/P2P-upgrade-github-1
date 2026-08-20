# P2P-GT-PILOT-HARDENING-01 — Báo cáo nghiệm thu tiếng Việt (22 mục)

**Phạm vi:** Sửa biên pilot (không phải toàn framework) — khép cổng team-gate canonical + xác minh READ_ONLY trên Game Truyện.
**Tác giả:** Manus AI — 20/08/2026
**Chế độ:** ONE BOUNDED P2P FIX + READ_ONLY VERIFICATION. Không chạm Gia Phả, Logistics, Supabase; không khởi động FW07; không promote/release `.35`; không khởi động mutation pilot; không phục sinh C36; không tái thiết kế FW01–FW06; không rerun Council 8/8.

---

## Verdict

`PASS / GAME_TRUYEN_CANONICAL_TEAM_GATE_HARD_STOP_VERIFIED`

Cổng đội canonical **bắt buộc dừng cứng** khi `participant_roles` rỗng (`NO_ELIGIBLE_ROLE` → HARD STOP); fallback thực thi ngoài canonical **đã loại bỏ** (`EXTERNAL_FALLBACK_CANNOT_PRODUCE_PILOT_PASS = PASS`); xác minh READ_ONLY trên Game Truyện cho kết quả **không mutation** (`APPLICATION_TASK_MUTATION = 0`, `H1 == H2`). Dispatch vai trò thật với receipt canonical **không xảy ra** — đây là kết quả fail-closed trung thực: không vai trò canonical nào đạt đủ bằng chứng phủ năng lực (`CAPABILITY COVERAGE`) cho yêu cầu thuộc danh tính vai trò, và không có chứng nhận năng lực nào có thể cấp cho danh tính vai trò theo thiết kế hiện hành. Positive control chứng minh cỗ máy dispatch hoạt động đúng khi yêu cầu thuộc phạm vi chứng nhận (certifiable scope) → `ELIGIBLE`.

---

## 1. P2P HEAD khởi điểm

- Khởi điểm: `95a59e6` (HEAD local = remote, branch `p2p-fw01-bootstrap-reconciliation`).
- Kết thúc: `0396f39` (push origin, không force-push, không viết lại lịch sử; baseline lịch sử `871baa1`).
- Ứng viên `.35` tại `95a59e6`: `FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE`, `8.4.7-C-codex.35`, SHA256 `8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47` — **không thay đổi** trong toàn chiến dịch.

## 2. Khiếm khuyết chính xác

Orchestrator pilot cũ (trước hardening): sau khi FW03 trả về `failure_class = NO_ELIGIBLE_ROLE`, nó **vẫn thực thi task** qua Python subprocess thuần (đọc dự án, khảo sát trạng thái) bên ngoài luồng dispatch canonical FW01. Đồng thời nó truyền `registry_records=[]` (nguồn sai) và tự đặt `required_capabilities=['code_read','repository_read']` — tên không thuộc từ vựng canonical P2P.

## 3. Canonical FW01 bypass?

**NO.** Mã runtime canonical không bypass cổng: `p2p_fw01_loop.py` chặn dispatch khi `dispatch_allowed=False` với `CAPABILITY_COVERAGE_BLOCKED`. Khiếm khuyết nằm ở lớp orchestrator (harness pilot), không phải package `.35`.

## 4. Bản sửa pilot harness

- `NO_ELIGIBLE_ROLE` (hoặc `participant_roles=[]`) → **HARD STOP**: không bước nào tiếp theo chạy, báo cáo vẫn được phát hành.
- Loại bỏ toàn bộ nhánh fallback thực thi ngoài canonical (không subprocess thô, không inspection trực tiếp làm verdict pilot). Inspection chẩn đoán read-only còn lại được phân lớp rõ `TOOLING/DIAGNOSTIC`.
- Nạp **registry canonical đóng gói** qua `team_intelligence.load_registry()` — không tạo registry thứ hai.
- Yêu cầu năng lực dùng từ vựng canonical (kiểm tra phủ theo bằng chứng vai trò), không tên tự đặt.

## 5. Vì sao registry "trống"

**A + D (xác định duy nhất).** Registry canonical 8 vai trò vẫn nguyên vẹn trong `.35` (11 bản ghi năng lực trong `capabilities.json`, bao gồm 8 vai trò canonical). Orchestrator cũ truyền `registry_records=[]` (nguồn sai/empty) thay vì `load_registry()`, và dùng hai tên năng lực tự đặt (`code_read`, `repository_read`) không tồn tại trong từ vựng canonical — từ vựng này không chứa ánh xạ nào cho hai tên đó. **C** (không ánh xạ canonical) cũng đúng một phần với riêng hai tên tự đặt đó, nhưng nguyên nhân hành vi là A: nguồn sai của lớp tích hợp.

## 6. Nguồn thẩm quyền registry

`capabilities.json` đóng gói — registry năng lực canonical (11 bản ghi, STATUS=ACTIVE, VERSION=1.0.0). **Không tạo registry thứ hai**, không sửa bản ghi.

## 7. Năng lực yêu cầu

- Chuỗi kiểm tra canonical: `required_capabilities = ('p2p_iris',)` — năng lực danh tính vai trò canonical, yêu cầu bằng chứng phủ vai trò.
- Positive control: phạm vi chứng nhận được (`NON_MUTATING_TASK`, `SYNTHETIC_TEXT_EXECUTION`, trạng thái `LIVE_CERTIFIED_FOR_CAPABILITY`) cho bộ điều hợp compliant.

## 8. Vai trò/đội được chọn

`SINGLE_ROLE`, `participant_roles=[]`, `failure_class=NO_ELIGIBLE_ROLE` — **fail-closed**. Không vai trò nào đạt đủ bằng chứng phủ (vai trò chỉ tự phủ danh tính; danh tính vai trò không phải phạm vi chứng nhận backend). Positive control `ELIGIBLE` chứng minh đường mở chỉ tồn tại khi yêu cầu là phạm vi chứng nhận.

## 9. Bằng chứng năng lực

`role_capability_evidence`: mỗi vai trò cung cấp chính danh tính của mình; bộ điều hợp Manus với chứng nhận phạm vi đạt `eligible=True`/`ELIGIBLE` cho phạm vi chứng nhận; nhưng `target_compatibility` yêu cầu yêu cầu năng lực vai trò được thỏa — với `p2p_iris` (danh tính) điều đó không thể — → hàng rào đóng. Không chế tạo chứng nhận (`ROLE_EXECUTION_BINDING != ROLE_CAPABILITY_CERTIFICATION` được bảo toàn).

## 10. Target eligibility hiện tại

- Vai trò thực tế (`p2p_iris`): **không có vai trò hợp lệ** → `NO_ELIGIBLE_ROLE` kể cả với bộ điều hợp compliant — đóng ở tầng phủ, chưa tới tầng eligibility vai trò.
- Positive control (phạm vi chứng nhận): `ELIGIBLE` (permission valid, quorum valid, evidence valid, auth `CONFIGURED`, `LOCAL_PROJECT`).

## 11. Target thực thi thật

Không có dispatch thực tế trong chiến dịch này (cổng đóng). Bộ điều hợp thực thi thật **tiềm năng** đã chuẩn bị theo hợp đồng: `p2p-manus-orchestration` (Manus orchestrator, adapter đăng ký rõ qua `register_explicit_adapter` kèm host attestation) — sẵn sàng cho pilot phê duyệt tiếp theo; không cần Codex.

## 12. Execution ID

`hardening-read-only-canonical-dispatch-002` (run id ghi trong trace yêu cầu; không phải receipt thực thi — không có thực thi).

## 13. Receipt vai trò canonical

**KHÔNG PHÁT HÀNH — theo thiết kế fail-closed.** Không vai trò nào được dispatch → không có `RoleExecutionReceipt` thật. Đây là hành vi đúng chuẩn (receipt chỉ phát hành cho thực thi qua hợp đồng thực thi vai trò). Positive control chứng minh luồng cấp chứng nhận hoạt động về mặt cấu trúc.

## 14. Host attestation

Không attestation tươi nào phát hành (không thực thi thật). Bằng chứng historical `LIVE_CERTIFICATION_RECORD` (C33-era) được bảo toàn nguyên trạng, không được sử dụng lại làm attestation hiện hành.

## 15. FW04 chất lượng

Không chạy — **đúng chuẩn** (`EXECUTION_SUCCESS != QUALITY_PROVEN`): không có thực thi thì không có hợp đồng chất lượng. Không shortcut nào được áp dụng.

## 16. FW05/FW06 trạng thái

- **FW05:** yêu cầu trace về hard-stop được phân loại `NOT_MATERIAL` → **không ghi decision** — fail-closed đúng; không decision rỗng nào được chèn (`captured=False`, lý do đã ghi).
- **FW06:** autonomy envelope `game-truyen` tải thành công; event `canonical-dispatch-verification` được nối vào `fw06-events.jsonl` (id ổn định, lũy đẳng); lease cũ của pilot 01 giữ nguyên; runtime health HEALTHY.

## 17. H1/H2

`H1 = H2 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b` (tree hash tracked, tính lại cơ học sau xác minh; khớp nguyên văn receipt pilot 01). H0 (pre-install) = `3d42e0ff…` — khác vì cài đặt được phê duyệt (pin bootstrap + chuẩn hóa AGENTS.md).

## 18. Application mutation

`APPLICATION_TASK_MUTATION = 0`, `DATABASE_MUTATION = 0`, `SUPABASE_RLS_MUTATION = 0`, `DEPLOYMENT = NO`. Thay đổi duy nhất trong cây GT kể từ cài đặt = 2 thay đổi cài đặt được phê duyệt (không đổi từ pilot 01); các tệp mới do hardening tạo (`canonical-dispatch-verify.json`, `hardening-01-report.json`, `fw06-events.jsonl`, envelope) nằm trong `.p2p/state` (gitignored, runtime state, không phải application code).

## 19. Tests mới

`scripts/pilot_harness_hardened.py` — 10 failure tests cơ học **A–J = PASS**:
registry authority (A), coverage gate closed on empty registry (B), empty registry ≠ eligible (C), ineligible target (D), hard-stop invariant `participant_roles=[] → no dispatch` (E), certifiable scope positive control (F), receipt not optional when dispatch open (G), coverage ≠ historical 8/8 binding (H), hard stop blocks all downstream (I), zero application mutation post-verification (J).

## 20. Regression

240/240 baseline tests PASS (`.p2p/system`); validator 78/78 PASS; `development-control` PASS; gitleaks 0 findings thật trên tệp mới. Gia Phả nguyên trạng; Logistics nguyên trạng.

## 21. Tác động ứng viên

**KHÔNG.** `.35` không đổi (artifact + bản ghi quản trị nguyên SHA); không mint ứng viên mới — khiếm khuyết thuộc lớp orchestrator/integration (chưa phải runtime đóng gói), do đó không thuộc phạm vi sửa package. Hardening script cam kết như `scripts/pilot_harness_hardened.py`.

## 22. Hành động P2P tiếp theo chính xác

Chủ sở hữu quyết định một trong hai hướng:

- **(a) Pilot với phạm vi chứng nhận:** phê duyệt một mutation pilot rủi ro thấp, không production, trên Game Truyện **với yêu cầu năng lực thuộc phạm vi chứng nhận** (ví dụ `NON_MUTATING_TASK`) và adapter `p2p-manus-orchestration` đăng ký chính thức + chứng nhận năng lực tươi → khi đó dispatch canonical có thể mở cổng và phát hành receipt vai trò thật.
- **(b) Giữ trạng thái fail-closed hiện hành** — không mở pilot nào cho đến khi có đường chứng nhận năng lực canonical được Chủ sở hữu phê duyệt.

Tôi **không tự động** bắt đầu hướng nào.

---

## Tuyên bố chuẩn hóa

`GAME_TRUYEN_CANONICAL_READ_ONLY_PILOT = VERIFIED` **có điều kiện:** cỗ máy cổng đội canonical + hard stop + zero mutation + H1==H2 đã được xác minh; dispatch vai trò thật với receipt **chưa đạt** vì không vai trò nào có đủ bằng chứng phủ năng lực theo registry hiện hành — đây là trạng thái fail-closed đúng chuẩn, không phải lỗi chưa sửa. Không cấp quyền tự động cho mutation pilot.
