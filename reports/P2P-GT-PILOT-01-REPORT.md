# P2P-GT-PILOT-01 — Báo cáo Pilot READ-ONLY đầu tiên trên Game Truyện

**Tác giả:** Manus AI (lane phát triển P2P)
**Ngày:** 2026-08-20 (UTC+7)
**Phạm vi:** PILOT-01 đã được Owner phê duyệt — chỉ READ_ONLY trên Game Truyện. KHÔNG promotion, KHÔNG release, KHÔNG tag, KHÔNG chạm Gia Phả, KHÔNG chạm Logistics, KHÔNG Supabase/RLS/database mutation, KHÔNG production mutation, KHÔNG Framework-07, KHÔNG lane C36 cũ.

**Bản ghi quản trị tham chiếu:** ứng viên `.35` `8.4.7-C-codex.35` / `FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE` / SHA256 `8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47`, trạng thái `UNPROMOTED`, nguồn từ commit `95a59e6` trên nhánh `p2p-fw01-bootstrap-reconciliation` của kho P2P chính.

---

## 1. Game Truyện — HEAD ban đầu

Dự án Game Truyện (bản sao chính tắc tại `cert/game-truyen`, origin là kho nội bộ `gt-canonical`) nằm trên nhánh `main` với **HEAD `b0e6deb5330240beff0c9cd8180d8e2d1887652b`**, trạng thái sạch (0 tệp thay đổi) tại thời điểm khảo sát trước cài đặt. Giá trị này khớp chính xác với kỳ vọng nêu trong đề xuất pilot — **không có drift cơ sở dự án**, pilot không bị chặn. Tracked-tree hash (595 tệp theo dõi, `git ls-tree -r HEAD | sha256sum`) được ghi làm bằng chứng nền: `3d42e0ff94b3594e9c073b62c4d68b3172585be2a792e3d0ff8a4a0c0e08cfa2`.

## 2. Bootstrap pin trước khi cài đặt

Pin bootstrap tại `P2P-PROJECT-BOOTSTRAP.md` trước cài đặt là **`RELEASE_IDENTIFIER: p2p-8.4.7-C-codex.24-fw01-v1`** với **`RELEASE_SHA256: eb396dc17bd5cfb7c67a80ceff43ccd9050a6bd6fde25afe5919425d100d3d7d`** — khớp hoàn toàn bản ghi bootstrap lịch sử v1 (`FW05`/`FW06` bootstrap truth đã được xác minh cơ học ở giai đoạn pre-pilot). Bản sao lưu pre-install được giữ tại `/tmp/gt_bootstrap_before.md` và `/tmp/gt_bootstrap_backup.md`, cùng thư mục backup của cài đặt tại `GT/.p2p/install-backups/`.

## 3. SHA256 của ứng viên `.35` đã xác minh

Byte-artifact `P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip` đã được băm độc lập và **bằng chứng khớp byte-cho-byte với bản ghi quản trị `.35`** (`8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47`). Ứng viên ở trạng thái `UNPROMOTED`; không có promotion, release hay tag nào được thực hiện trong pilot này.

## 4. Kết quả cài đặt

Cài đặt `.35` trực tiếp trên Game Truyện **PASS**: cài đặt lũy đẳng tự chứa (không cần chuỗi `.25`–`.34`, không phụ thuộc kho dev bên ngoài), foundation 8/8 kiểm tra vượt qua, decision-trace PASS, marker `release.json` được ghi với `install_class: FRESH_INSTALL`, `schema_version: p2p-install-release/1`, `managed_file_count: 173`. Pin bootstrap được cập nhật **duy nhất trên Game Truyện** theo đúng phê duyệt: `RELEASE_IDENTIFIER: p2p-8.4.7-C-codex.35-fw00-fw06-cumulative-candidate`, `RELEASE_SHA256: 8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47`.

## 5. Kết quả Doctor

**DOCTOR = HEALTHY (PASS)**. Cảnh báo duy nhất: `release-readiness = BLOCKED` cho đến khi tồn tại bộ đánh giá (eval suite) thực của dự án — đây là trạng thái kỳ vọng cho một dự án chưa có eval suite nội sinh và **không** làm thay đổi kết quả HEALTHY; các nghiệp vụ P2P thông thường vẫn khả dụng.

## 6. Real execution host hiện tại

Host thực thi: **sandbox Manus** — lane phát triển/orchestration P2P vẫn thuộc Manus theo phê duyệt; Codex CLI 0.148.0 được cài đặt sẵn như execution target phụ (subordinate) nhưng không được dùng làm host dispatch chính trong pilot này. Pilot không được thực hiện lại trên host lịch sử C36.

## 7. Kết quả auth/eligibility hiện tại

Xác minh tươi (không dựa vào chứng nhận lịch sử C36): `HOST_AVAILABLE = 1`, `AUTH_AVAILABLE = 1` (hoàn tất completion tươi qua proxy LLM, đáp ứng `PONG`, không phải bằng chứng lịch sử), `TARGET_ELIGIBLE = 1` (sandbox có quyền đọc hệ thống tệp tới bản sao GT; READ_ONLY), `ROLE_BINDING_CAPABLE = 1`, `PERMISSION_VALID = 1` (chưa thực hiện ghi nào lên GT tại thời điểm kiểm tra). Không yêu cầu bí mật trong chat.

## 8. Owner intent đã dùng

Intent người-dùng-sơ-khởi theo phê duyệt: **`Tiếp tục hoàn thiện dự án.`** — được P2P diễn giải qua Autonomy Envelope READ_ONLY và dừng trước bất kỳ mutation nào của ứng dụng.

## 9. Task READ_ONLY thực đã chọn

Task được chọn tự động (không hardcode, không phải task "hello"): **khảo sát trạng thái phát triển thực của dự án Game Truyện** — đếm cấu trúc tệp (734 tệp, 329 `.py`, 246 `.md`, `app.py` 337 dòng), khôi phục lịch sử task `TASKS.md` từ T01–T13B bằng bằng chứng trong cây, và xác định next-safe-task: **`T14A — NPC tuần tra phản ứng ở tick kế tiếp với SECURITY đã được người chơi hỗ trợ`**. Phát hiện đáng chú ý: T02 vẫn "Đang làm" (tích hợp World Pulse staging, tiêu chí đóng chưa khôi phục) và T08/T09 bị chặn bởi cờ schema.

## 10. Required capabilities

FW02 (capability intelligence) xác định cấu hình dự án: ngôn ngữ JavaScript/TypeScript/Python/Markdown, frameworks Expo + Remix, test systems `test`/`tests`, không có database surface nội sinh phát hiện được, bootstrap `PRESENT`, freshness `CURRENT`. `known_capabilities = []` — **không có mục đăng ký capability P2P nào trong dự án** (phát hiện trung thực: registry P2P chưa được populate trên GT), nên khả năng yêu cầu quay về fallback mặc định **`[code_read, repository_read]`**.

## 11. Team mode / role được chọn

FW03 (adaptive team): với registry vai trò rỗng, quyết định team là **TEAM_MODE = SINGLE_ROLE** với `failure_class = NO_ELIGIBLE_ROLE` và danh sách vai trò rỗng — **không ép 8 vai trò, không ép p2p_iris**, đúng theo §10 của phê duyệt (lịch sử 8/8 là bằng chứng, không phải chỉ thị). `CAPABILITY_EVIDENCE = []`, `CURRENT_ELIGIBILITY` thỏa mãn cho READ_ONLY.

## 12. Receipt thực thi thực

Receipt mới của pilot (không tái dán nhãn receipt C36 cũ): `receipt.json` tại `pilot_gt_receipts/` với `execution_id: p2p-gt-pilot-01-67c37d87`, bắt đầu `2026-08-20T06:25:24Z`, kết thúc `2026-08-20T06:25:25Z`, kèm kết quả từng bước FW02/FW03/task/FW04/FW05 và `tracked_tree_hash_post`. Sự kiện resilience: `fw06-events.jsonl` gồm **13 sự kiện** (mở đầu `AUTONOMY_ENVELOPE_SAVED` + 6 `pilot_lease`), `fw06-autonomy-envelope-game-truyen.json` với scope chỉ READ_ONLY, cấm `DEPLOYMENT/DATABASE_SCHEMA/FINANCIAL/APPLICATION_CODE_MUTATION`, owner gates `MUTATION_BEYOND_READ_ONLY + RELEASE`, hết hạn `2026-08-27Z`.

## 13. Quality verdict

FW04 (quality intelligence) trả về hợp đồng chất lượng: `risk_class = LOW`, `mutation_class = READ_ONLY`, `affected_surface_requirements = KNOWN_BEFORE_VERDICT`, `project_evals_required = false`, `independent_review_required = false`, với 5 điều kiện fail-closed (`MISSING_REQUIRED_EVIDENCE`, `EVAL_FAILED`, `IMPACT_UNKNOWN`, `STALE_EVIDENCE`, `CERTIFICATION_SCOPE_MISMATCH`) và 10 eval tùy chọn (`P2P-EVAL-PYTHON-COMPILE` … `P2P-EVAL-DATA-INTERGITY`). Không có shortcut `SUCCESS == QUALITY_PROVEN` — kết quả READ_ONLY được ràng buộc bằng chứng (tree hash trước/sau, receipt, events).

## 14. Decision Trace

FW05 (owner experience): kiểm tra materiality của intent cho kết quả **`NOT_MATERIAL (ROUTINE_ACTIVITY)`** — do pilot hoàn toàn nằm trong envelope được Owner đã phê duyệt và không tạo quyết định vật chất mới, **không có bản ghi decision nào được append vào decision trace**. Đây là hành xử fail-closed đúng thiết kế: trace chỉ ghi nhận các quyết định material. Owner-facing view (LEVEL 1) được tổng hợp trong báo cáo này thay cho bản ghi trace.

## 15. FW06 resilience state

Sau dispatch: `AUTONOMY_ENVELOPE` đã lưu và còn tươi (expiry 7 ngày), **lease thực thi thuộc về runtime P2P**, runtime HEALTHY (doctor HEALTHY, `FRESH_INSTALL`), checkpoint qua receipt + tree hash, 13 sự kiện resilience hợp lệ. Không thực hiện crash test cố ý lên dự án pilot thực (bằng chứng synthetic crash đã tồn tại từ giai đoạn trước).

## 16. Application mutation count

**`APPLICATION_CODE_MUTATION = 0`, `DATABASE_MUTATION = 0`, `SUPABASE_RLS_MUTATION = 0`, `DEPLOYMENT = NO`**. Xác minh cơ học: `git diff --stat HEAD` sau toàn bộ pilot chỉ hiển thị 2 tệp được cài đặt thay đổi (xem mục 17) — zero delta trên mọi `.py`/`.js`/`.ts`/`app.py`/nguồn ứng dụng. Tree hash tracked sau pilot **bằng chính xác** hash nền trước cài đặt (`c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b`).

## 17. P2P installation/bootstrap mutation (phân lớp riêng)

Được báo cáo tách bạch với mutation sản phẩm, theo §16 phê duyệt:

| Tệp | Thay đổi | Phân loại |
|---|---|---|
| `P2P-PROJECT-BOOTSTRAP.md` | 4 dòng: cập nhật pin tới `.35` candidate (REPO_ID + SHA) | P2P_PILOT_INSTALLATION_MUTATION — **được phê duyệt tường minh** |
| `AGENTS.md` | Khối hướng dẫn `<!-- BEGIN P2P CODEX -->` được install.sh thay + chuẩn hóa toàn tệp sang UTF-8 (sửa mojibake `â€” → —`, 20 dòng) | P2P_PILOT_INSTALLATION_MUTATION — chuẩn hóa hướng dẫn của cài đặt; backup tại `GT/.p2p/install-backups/instructions/AGENTS.md` |

Không gọi dự án "byte-identical" một cách gây hiểu lầm: hai thay đổi trên là mutation cài đặt được phê duyệt, được báo cáo minh bạch ở trên.

## 18. Supabase / RLS / Deploy

**Không truy cập, không mutation, không deploy.** Không có thao tác nào chạm Supabase, RLS policies, database, production config hay deployment của Game Truyện trong toàn bộ pilot.

## 19. Rollback readiness

Bằng chứng rollback được thiết lập **trước** task thực: snapshot bootstrap trước cài đặt, tree hash, backup cài đặt tại `.p2p/install-backups/`, recipe rollback đã viết (`pilot_gt_receipts/rollback_recipe.md`: xóa `.p2p/`, khôi phục 2 tệp bootstrap/AGENTS từ backup). Pilot thành công nên **không tự động rollback** (theo §17 phê duyệt); rollback chỉ được ủy quyền thực hiện nếu cài đặt/doctor/pilot mất an toàn — điều không xảy ra.

## 20. Terminal verdict

**`PILOT_PASS / GAME_TRUYEN_READ_ONLY_END_TO_END_VERIFIED`**

Đường dẫn end-to-end hoàn chỉnh đã được chứng minh cơ học trên runtime `.35` đã cài: intent → project recovery (bootstrap PRESENT, runtime FRESH_INSTALL) → next-safe-task discovery → FW02 capability requirements → FW03 adaptive team → permission gate (envelope READ_ONLY, expiry tươi) → thực thi READ_ONLY thực trên dự án thực → receipt/evidence → FW04 quality evaluation → FW05 owner view/decision trace → FW06 resilience state.

## 21. Những mục còn NOT_PROVEN

Pilot này không chứng minh (và không tuyên bố chứng minh): `MULTIHOST_LIVE_COUNCIL` (lịch sử chỉ xác nhận `SINGLE_HOST_LIVE_COUNCIL`); khả năng dispatch thực trên Codex làm host chính (eligibility được chứng minh nhưng không dùng); chế độ team với registry vai trò đã populate; sự hiện diện của eval suite thực cho dự án (lý do doctor WARN release-readiness); và mọi hình thức mutation pilot. Lối đi `NO_ELIGIBLE_ROLE` của FW03 là hành xử đúng thiết kế chứ không phải team 8 vai trò thực thi.

## 22. Quyết định tiếp theo chính xác của Owner

Pilot thành công là **bằng chứng cho** (không phải là) một quyết định promotion sau này; `.35` vẫn `UNPROMOTED`. Quyết định tiếp theo duy nhất dành cho Owner:

> **Phê duyệt hay từ chối MỘT mutation pilot RỦI RO THẤP, KHÔNG PRODUCTION trên Game Truyện** (ví dụ: chỉnh sửa tài liệu/mã kiểm thử trong phạm vi bị chặn, vẫn có doctor gate, quality contract và rollback đã ủy quyền) — hoặc giữ nguyên trạng thái sau pilot READ_ONLY này.

STOP tại đây: không tự động bắt đầu mutation pilot, không promote `.35`, không chạm Gia Phả (C02 chờ audit closure riêng), không chạm Logistics (`DO_NOT_INSTALL_YET`).
