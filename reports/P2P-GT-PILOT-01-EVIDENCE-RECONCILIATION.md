# P2P-GT-PILOT-01 — Canonical Execution + Hash Baseline Reconciliation

**Tác giả:** Manus AI (lane phát triển P2P)
**Ngày:** 2026-08-20 (UTC+7)
**Chế độ:** ONE TINY EVIDENCE RECONCILIATION — chỉ khôi phục bằng chứng cơ học từ receipts/state đã tồn tại. Không chạy lại pilot, không sửa runtime, không chạm Gia Phả, không promotion `.35`, không khởi động FW07, không lane C36 cũ.

> Nguyên tắc đã áp dụng: **NO_ELIGIBLE_ROLE ≠ CANONICAL_ROLE_DISPATCH_ALLOWED**. Quyết định `NO_ELIGIBLE_ROLE` của FW03 không được biểu diễn thành thực thi team canonical thành công.

---

## 1. FW03 exact decision (khôi phục cơ học từ receipt)

`TeamDecision` được ghi nguyên văn trong receipt (`execution_id: p2p-gt-pilot-01-67c37d87`):

> `team_mode = SINGLE_ROLE`, `participant_roles = []`, `required_capabilities = [code_read, repository_read]`, `selected_capability_sources = []`, `provided_capabilities = []`, `failure_class = NO_ELIGIBLE_ROLE`, `mode_reason = "no eligible role for required capabilities"`, `decision_trace = [REQUIRED_SET step duy nhất]`, `escalation_factors = []`, `role_capability_evidence = []`.

Nguồn gốc: `FW02.known_capabilities = []` (không có mục capability nào đăng ký trong registry P2P của dự án), registry vai trò rỗng → FW03 (`team_intelligence.py`, khối `elif not eligible_roles and reqs`) trả về `failure_class = NO_ELIGIBLE_ROLE` theo đúng thiết kế fail-closed — **không có vai trò canonical nào được chọn**.

## 2. Vì sao thực thi vẫn tiếp diễn sau NO_ELIGIBLE_ROLE

Khảo sát mã xác nhận cơ học: `p2p_fw01_loop.py` (canonical dispatch loop) **thực sự chặn** — tại checkpoint `dispatch_allowed` của FW02, nếu coverage không thỏa mãn, loop trả về `{"status": "CAPABILITY_COVERAGE_BLOCKED", "failure_class": ...}` và **không phát đi task** (dòng `if not _fw02.dispatch_allowed: return …`). Không tồn tại bypass im lặng trong đường dispatch canonical.

Tuy nhiên, task READ_ONLY trong pilot **không đi qua FW01 loop canonical**: orchestrator `pilot_run.py` chỉ gọi FW03 để **ghi lại bằng chứng quyết định**, sau đó tự thực thi task qua một Python subprocess thuần (đọc cây tệp bằng `Path.rglob` + đọc `TASKS.md`). Cổng duy nhất được kiểm tra là envelope FW06 (READ_ONLY được phép, expiry còn tươi) — đây là cổng của orchestrator, không phải chuỗi composition FW01/FW02/FW03 canonical. Thực thi tiếp diễn vì **orchestrator của pilot coi `NO_ELIGIBLE_ROLE` là thông tin ghi nhận thay vì điểm dừng cứng** — một khiếm khuyết thiết kế ở lớp orchestrator pilot, không phải lỗi bypass trong runtime P2P.

## 3. Canonical role được chọn? — **KHÔNG**

`participant_roles = []`, `selected_capability_sources = []`, `provided_capabilities = []`. Không vai trò canonical nào được chọn vì không có vai trò eligible nào tồn tại trong registry (registry chưa được populate trên Game Truyện).

## 4. Role receipt tồn tại? — **KHÔNG**

Chỉ tồn tại receipt orchestration của pilot (step outputs FW02/FW03/task/FW04/FW05) và receipt FW06 (`fw06-events.jsonl` 13 sự kiện, `AUTONOMY_ENVELOPE_SAVED` + `pilot_lease`). Theo §11 phê duyệt pilot: không tái dán nhãn receipt C36 lịch sử làm receipt pilot — đúng như đã tuân thủ, nhưng đồng nghĩa **không có role execution receipt canonical** nào tồn tại.

## 5. Host / adapter identity

| Trường | Giá trị |
|---|---|
| EXECUTION_HOST | Manus sandbox (`87cd0e940adf`, user `root`) |
| EXECUTION_ADAPTER | **NONE / NOT_APPLICABLE** (subprocess Python thuần; không adapter canonical nào được gọi) |
| CANONICAL_ROLE_ID | **NONE** |
| ROLE_EXECUTION_CONTRACT | **NOT_APPLICABLE** |
| HOST_ATTESTATION | **NONE** (không có luồng attestation canonical nào được kích hoạt; năng lực proxy "PONG" không phải role binding receipt) |
| ROLE_RECEIPT | **NONE** |
| CURRENT_ELIGIBILITY_EVIDENCE | FW06 envelope (READ_ONLY only, prohibited: DEPLOYMENT/DATABASE_SCHEMA/FINANCIAL/APPLICATION_CODE_MUTATION, owner gates MUTATION_BEYOND_READ_ONLY + RELEASE, expiry 2026-08-27Z) + 13 FW06 events hợp lệ |

## 6. Phạm vi tuyên bố pilot chính xác hiện nay

Phân loại: **Trường hợp B — `READ_ONLY_EXTERNAL_EXECUTION_FALLBACK = VERIFIED_BOUNDED`**. Không phải A (không có path canonical role nào xảy ra; quyết định NO_ELIGIBLE_ROLE là thật, receipt không misrepresent), không phải C (không có bypass cổng team canonical trong runtime — loop chặn đúng; thực thi xảy ra ngoài loop). Tuyên bố cuối cùng được phép (theo §5 phê duyệt):

> **`GAME_TRUYEN_READ_ONLY_PROJECT_INTEGRATION_VERIFIED`** với: project recovery = VERIFIED; FW02 profile = VERIFIED; FW03 fail-closed detection = VERIFIED; canonical role dispatch = **NOT_PROVEN**; READ_ONLY external bounded execution = VERIFIED; FW04 quality contract = VERIFIED; FW05 owner surface = VERIFIED; FW06 envelope/lease = VERIFIED; application mutation = 0.

**Không gọi** đây là "full canonical end-to-end" — cụm `END_TO_END_VERIFIED` trong verdict pilot trước đó được hiệu chỉnh ở đây.

## 7. H0 — pre-install tracked-tree hash

`H0 = 3d42e0ff94b3594e9c073b62c4d68b3172585be2a792e3d0ff8a4a0c0e08cfa2` (595 tệp theo dõi, ghi nhận cơ học trước cài đặt). Đây là cây tại HEAD `b0e6deb…` với pin v1 và `AGENTS.md` nguyên gốc (có mojibake).

## 8. H1 — post-install / pre-task tracked-tree hash

`H1 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b` (ghi trong receipt `tracked_tree_hash_post` ở bước cuối orchestrator; tái tính hiện tại cho kết quả **y hệt**: `git ls-tree -r HEAD | sha256sum = c35a8d1b…`).

## 9. H2 — post-task tracked-tree hash

`H2 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b` (tái tính hiện tại, HEAD không đổi kể từ cài đặt). **H1 == H2** → `APPLICATION_TASK_MUTATION = 0` được chứng minh cơ học. **H0 != H1** là kỳ vọng: cài đặt P2P được phê duyệt đã thay đổi 2 tệp theo dõi (pin bootstrap + chuẩn hóa UTF-8 `AGENTS.md`). Lưu ý hiệu chỉnh: báo cáo pilot trước đó ghi "tree hash sau pilot bằng hash nền trước cài" là **không chính xác về ngữ nghĩa** — đẳng thức đúng là H1 == H2; H0 khác H1 do mutation cài đặt được phê duyệt.

## 10. P2P setup mutations (tách bạch)

| Hạng mục | Nội dung | Lớp |
|---|---|---|
| Bootstrap pin | `P2P-PROJECT-BOOTSTRAP.md`, 4 dòng → pin `.35` candidate | P2P_SETUP_MUTATION (được phê duyệt) |
| AGENTS normalization | `AGENTS.md`, khối `<!-- BEGIN P2P CODEX -->` thay + chuẩn hóa UTF-8, backup tại `.p2p/install-backups/` | P2P_SETUP_MUTATION |
| Runtime | Thư mục `.p2p/` cài đặt đầy đủ (gitignored, 173 tệp được quản lý, `release.json` FRESH_INSTALL) | P2P_SETUP_MUTATION |

## 11. Application-task mutations

**APPLICATION_TASK_MUTATION = 0** — đúng về cơ học: `git diff --stat HEAD` hiện tại chỉ hiển thị đúng 2 tệp setup (14 dòng thêm / 14 dòng bớt, toàn bộ thuộc bootstrap + AGENTS); zero delta trên `.py`/`.js`/`.ts`/nguồn ứng dụng; H1 == H2 như mục 9.

## 12. Pilot có cần chạy lại không? — **KHÔNG**

Evidence hiện có đủ để phân biệt rõ A/B/C: receipt FW03 nguyên văn, mã canonical block xác nhận bằng dòng lệnh, provenance dispatch của orchestrator đọc được. Mọi rerun chỉ để "đẹp hơn bằng chứng" — bị loại trừ bởi §8 phê duyệt. Pilot READ_ONLY giữ nguyên trạng thái, không rerun.

## 13. Có bug runtime không? — **KHÔNG có bypass runtime; CÓ khiếm khuyết orchestrator**

Runtime canonical (FW01 loop + FW03) fail-closed đúng: loop trả về `CAPABILITY_COVERAGE_BLOCKED` khi `dispatch_allowed` sai; FW03 ghi `NO_ELIGIBLE_ROLE` không tạo dispatch. Điểm yếu nằm ở **orchestrator pilot** `pilot_run.py`: nó đọc kết quả FW03 rồi vẫn tự thực thi task thay vì dừng với trạng thái BLOCKED. Không sửa runtime trong reconciliation này (§3); khiếm khuyết orchestrator thuộc phạm vi một lane fix riêng có chặn (bounded fix) — chờ phê duyệt Owner.

## 14. Trạng thái promotion của `.35`

**`UNPROMOTED`** — không đổi. Không promotion, không release, không tag đã được thực hiện; bản ghi quản trị `.35` trong `development-control.json` vẫn giữ `promotion_status = UNPROMOTED`, SHA `8cd26c23…`.

## 15. Hành động tiếp theo chính xác

Theo phê duyệt reconciliation: với PARTIAL/PASS không bypass runtime, hành động tiếp theo là **`GIA PHẢ C02 CURRENT-LINEAGE CLOSURE AUDIT`** — không tự động khởi động audit này. Mọi việc khác dừng lại: không mutation pilot, không promotion, không FW07, không C36.

---

## Terminal verdict

**`PARTIAL / GT_PROJECT_INTEGRATION_VERIFIED_CANONICAL_ROLE_DISPATCH_NOT_PROVEN`**

Bằng chứng pilot READ_ONLY là thật và được kiểm chứng: tích hợp dự án Game Truyện với runtime `.35` hoạt động đúng, FW02/FW04/FW05/FW06/permission-gate đều verified, zero application mutation (H1 == H2). Tuy nhiên đường dispatch vai trò canonical **không được chứng minh** — FW03 fail-closed đúng thiết kế (`NO_ELIGIBLE_ROLE`), và task đã chạy như fallback READ_ONLY ngoại vi bị chặn bởi envelope FW06. Tuyên bố pilot được hạ cấp về phạm vi từ "end-to-end canonical" xuống "project integration + bounded external execution".
