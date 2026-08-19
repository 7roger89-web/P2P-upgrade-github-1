# P2P-FW01 v2 — Exact Artifact Binding, Nguồn Bất Biến & Đóng Vòng Lắp Đặt An Toàn

**Terminal Verdict: `PASS/FW01_V2_EXACT_ARTIFACT_RELEASE_READY`**
**Trạng thái cổng: DỪNG TẠI `OWNER_PATCH_RELEASE_GATE` — chờ quyết định của chủ sở hữu bản vá**

Tác giả: Manus AI · Ngày: 2026-08-19 · Chuỗi công việc: `P2P-upgrade` (dự án P2P-upgrade gcvNpF6ibfpY8pJ8PPQUw3)

---

## Xác nhận kết luận

Khóa thẩm định cuối cùng đóng với kết luận **duy nhất và quyết định**: `PASS/FW01_V2_EXACT_ARTIFACT_RELEASE_READY`. Không có trạng thái trung gian nào còn mở: chứng minh máy-mới chính xác đã đạt khớp SHA byte-đối-byte với candidate v2 cuối cùng, liên kết nguồn bất biến đã được xác nhận, AGENTS.md của GT đã được phân loại an toàn, fresh-clone cuối cùng của cả GT lẫn GP đạt `UNEXPECTED_TRACKED_PROJECT_MUTATION=0`, bộ kiểm định đầy đủ đạt `78/78 PASS`, bộ âm đạt `10/10 PASS`, và v1 được bảo toàn nguyên vẹn. Toàn bộ tiến trình dừng tại cổng chủ sở hữu — **không publish, không promote, không push lên remote GT/GP sản xuất, không FRAMEWORK-02, không thao tác Supabase**.

---

## 23 mục kiểm định (yêu cầu → kết quả)

**Mục 1 — Byte candidate chính xác.** Artifact cuối cùng `P2P-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip` (2.728.740 byte tại `auth-f01/reports/candidates/`) có SHA-256 thực tế xác nhận đúng `2a42e815ca44fbecce4d8f35a641529e8cad028f07dccc5800bae00e3f509e61` — khớp hoàn toàn giá trị kỳ vọng từ Phase 1, được đo lại sau mọi commit và sau mỗi lần build thử nghiệm mà không lần nào thay đổi.

**Mục 2 — Giải mâu thuẫn evidence a7f2cd83.** Giá trị artifact cũ trong `fresh-machine-simulation.json` (`a7f2cd83...`) được truy nguyên bằng máy: nó là **artifact của bản rebuild** (`test_patch_mint.py` rebuild zip ở dấu thời gian khác, tạo SHA khác), không phải candidate cuối cùng. Evidence cũ được giữ nguyên làm lịch sử (`contradiction-reproduction.json` ghi lại cơ chế tái hiện), không chỉnh sửa.

**Mục 3 — Chứng minh máy-mới chính xác với SHA khớp.** Evidence `fw01-v2-exact-fresh-machine-proof.json`: `expected_candidate_sha256 == observed_artifact_sha256 == 2a42e815...`, `sha_match: true`, `canonical_install_rc: 0`, `canonical_install_pass: true`, `doctor_health: HEALTHY`, `external_dev_path_dependency: 0`, `no_p2p_repo_dependency: true`, `no_pythonpath: true`, `status: PASS`. Môi trường sạch, không phụ thuộc path phát triển bên ngoài.

**Mục 4 — Nguồn bất biến, liên kết verified.** Commit dòng thẩm quyền `a5f2997` (bề mặt nguồn cuối cùng, trước 3 commit evidence) đã phục hồi `p2p_fw01_live.py` bản di động (env-first key resolution, không hardcode `/home/ubuntu`). Evidence `fw01-v2-source-binding.json`: `CANDIDATE_PAYLOAD_SURFACE_BINDING=VERIFIED`, `expected_vs_observed_match: true`, 463 file: 363 khớp đường dẫn cây chính xác, 86 module runtime remap có tài liệu (`.p2p/system/`), 5 module legacy đóng gói ổn định, 7 file toàn vẹn do mint sinh đã được đồng bộ về cây, chỉ 2 file self-referencing mint (`RELEASE-SHA256SUMS.txt`, `release-manifest.json`) là delta-by-design. Không re-mint, không replacement.

**Mục 5 — AGENTS.md GT phân loại A–D, không sửa ngầm.** Evidence `fw01-v2-agents-safety-review.json`: GT được xếp **hạng B** — installer merge khối `BEGIN/END P2P CODEX` (backup-then-merge), nội dung xung quanh nguyên vẹn; sửa UTF-8 trong khối là hệ quả không tránh khỏi của luồng merge lên byte không sạch (mojibake có sẵn trong cây GT). Owner có quyền từ chối bằng cách bỏ qua `install.sh` và áp diff dry-run thủ công; bản diff đề xuất được ghi nhận **trước** khi áp dụng, đúng semantics owner-gate. GP xếp hạng A (installer tạo mới, không có AGENTS.md trong cây). Không side-effect hạng C/D.

**Mục 6 — Fresh-clone GT cuối cùng.** Evidence `fw01-v2-fresh-clone-gt.jsonl`: harness đầy đủ (discover→verify-sha→detect-runtime→install→doctor→idempotent→rollback→reinstall) `rc=0` mọi bước; doctor `HEALTHY`; thay đổi tracked duy nhất = `AGENTS.md` — merge khối P2P CODEX của installer, đã khai báo trước, hạng B; `unexpected_tracked_project_mutation: 0`.

**Mục 7 — Fresh-clone GP cuối cùng.** Evidence `fw01-v2-fresh-clone-gp.jsonl`: toàn bộ harness `rc=0`; doctor `HEALTHY`; `tracked_changes_excluding_untracked: 0`; `SUPABASE_MUTATION: 0`; `RLS_WEAKENING: 0`. Thư mục Supabase nguyên vẹn, không giao dịch nào.

**Mục 8 — UNEXPECTED_TRACKED_PROJECT_MUTATION=0.** Đạt ở cả GT và GP. Thay đổi AGENTS.md của GT là hành vi của installer đã tài liệu hóa (hạng B), không phải đột biến bất ngờ — evidence ghi nhận minh bạch cả hai khái niệm.

**Mục 9 — SHA thống nhất 9 vị trí.** Candidate zip, mint record (`fw01-v2-patch-candidate-mint.json`), evidence liên kết nguồn, evidence fresh-machine, evidence fresh-clone GT, evidence fresh-clone GP, manifest GT (`561777f`), manifest GP (`08aa6aa`) — tất cả 8 vị trí vật lý + báo cáo này đều trỏ `2a42e815...`. Không drift.

**Mục 10 — Determinism rebuild.** `DETERMINISTIC_REBUILD=PASS` (cấp content, có khai báo): rebuild từ bản sao tạm của cây nguồn cuối bằng luồng build chính tắc cho layout **đồng nhất 463/463 thành viên**, 459 thành viên byte-đồng-nhất; 4 file metadata integrity (`release-manifest.json`, `RELEASE-SHA256SUMS.txt`, `manifest/sha256sums.txt`, `runtime-manifest.lock.json`) là biến thể khai báo rõ: `generated_at`, self-digest, và lock tái sinh mỗi lần mint. Zip được chuẩn hóa (date_time cố định 2010-01-01, duyệt thành viên theo thứ tự). Bytes candidate cuối không đổi, không re-mint.

**Mục 11 — Bộ kiểm định đầy đủ.** `validate_p2p_development_framework.py`: **78/78 PASS, 0 FAIL** sau tất cả commit evidence. `p2p_development_control.py validate`: PASS.

**Mục 12 — Bộ kiểm tra âm.** `05b_negative_tests_v2.sh`: **10/10 PASS** gồm fail-closed đúng mã lỗi (T1–T6, T9), chứng minh v1 artifact bị chặn (T7 `rc=7`), determinism nhất quán (T8), và install-doctor dương tính v2 (T10).

**Mục 13 — Kiểm tra path, inventory, va chạm installer.** Harness `detect-runtime` + `p2p_governance` vượt qua kiểm tra không hardcode path phát triển (`external_dev_path_dependency: 0`); inventory nguồn khớp payload (152/152 tại gate source-hashes); va chạm `AGENTS.md` cài đặt thuộc hạng B đã tài liệu hóa, không ghi đè ngầm nội dung khác của dự án.

**Mục 14 — Secret scan.** Gitleaks 8.21.2 quét evidence và cây: **CLEAN — no leaks found**. Không có credential, token hay secret nào trong artifact hoặc evidence.

**Mục 15 — Closure guard & regression.** Không có lỗi mới không giải thích được (`NEW_UNEXPLAINED_FAILURES=0`); hồi quy sau các commit evidence được xác nhận bằng validator 78/78 lặp lại; doctor trên cây phát triển chỉ còn fail drift đã tài liệu hóa (khóa mint cũ vs cây đang phát triển) — đồng nhất với hành vi tại chứng minh máy-mới.

**Mục 16 — v1 bảo toàn nguyên vẹn.** Tag từ xa `p2p-8.4.7-C-codex.24-fw01-v1` tại `a91e115` không bị viết đè, không bị merge/rebase; release GitHub v1 (asset 520387867) nguyên trạng lịch sử; candidate v2 bytes riêng biệt, không kế thừa artifact v1.

**Mục 17 — Không publish/promote.** Candidate v2 vẫn **UNPROMOTED, UNPUBLISHED**: không release GitHub, không push nhánh, không thao tác remote GT/GP sản xuất, không FRAMEWORK-02, không Council/Gate J.

**Mục 18 — Không thao tác Supabase.** `SUPABASE_MUTATION=0`, `RLS_WEAKENING=0`; không ghi Supabase trong toàn chuỗi; key resolution là env-first, không tạo connection nào.

**Mục 19 — Evidence lịch sử không bị sửa.** `fresh-machine-simulation.json` (a7f2cd83) và `preview-presence-test.json` giữ byte-nguyên; mâu thuẫn được giải bằng evidence mới riêng (`fw01-v2-exact-fresh-machine-proof.json`) và cơ chế tái hiện được ghi lại (`contradiction-reproduction.json`).

**Mục 20 — Tính di động của runtime.** `p2p_fw01_live.py` (env-first key resolution) đã phục hồi vào cây thẩm quyền từ payload candidate; doctor chứng minh chạy đúng không cần PYTHONPATH và không phụ thuộc repo P2P bên ngoài.

**Mục 21 — Đồng bộ bề mặt cây–payload.** Sau 3 commit MINT-INTEGRITY ALIGNMENT (5 file integrity + technical-preview + supplemental-checksums), bề mặt cây cam kết byte-khớp payload candidate v2; doctor trên cây thẩm quyền đạt PASS drift cho bề mặt đã khóa; 4 file self-referencing mint còn lại là delta-by-design đã khai báo.

**Mục 22 — Minh bạch khai báo (disclosure).** Mọi biến thể được khai báo rõ: lock tái sinh mỗi mint, `generated_at` metadata, checksums tree-level tham chiếu 760 đường dẫn .agents trong khi đóng gói 129 (hành vi thiết kế đã có, đồng nhất cả hai artifact), và doctor bare-tree fail drift do khóa mint cũ. Không có trường hợp che giấu.

**Mục 23 — Terminal verdict duy nhất & cổng chủ sở hữu.** Verdict: **`PASS/FW01_V2_EXACT_ARTIFACT_RELEASE_READY`**. Mọi điều kiện tiền-khóa đã đạt; bản vá sẵn sàng để chủ sở hữu thẩm định và kích hoạt release. **Dừng tại `OWNER_PATCH_RELEASE_GATE`** — không bước nào tiếp theo được thực hiện cho đến khi chủ sở hữu phê duyệt minh bạch.

---

## Bảng tổng hợp evidence

| # | Evidence | Kết quả then chốt |
|---|----------|------------------|
| 1 | `fw01-v2-exact-fresh-machine-proof.json` | SHA_MATCH=true · install PASS · DOCTOR HEALTHY · ext-dep=0 |
| 2 | `fw01-v2-source-binding.json` | BINDING=VERIFIED · final source a5f2997 · no re-mint |
| 3 | `fw01-v2-agents-safety-review.json` | GT hạng B (P2P block only) · GP hạng A · không C/D |
| 4 | `fw01-v2-fresh-clone-gt.jsonl` | harness đầy đủ PASS · UNEXPECTED=0 (AGENTS.md khai báo) |
| 5 | `fw01-v2-fresh-clone-gp.jsonl` | harness đầy đủ PASS · tracked=0 · Supabase=0 · RLS=0 |
| 6 | `fw01-v2-determinism-proof.json` | DETERMINISTIC_REBUILD=PASS content · 459/463 byte-đồng-nhất |
| 7 | `contradiction-reproduction.json` + `fresh-machine-simulation.json` | a7f2cd83 = rebuild artifact, lịch sử giữ nguyên |

## Chuỗi commit thẩm quyền (nhánh p2p-fw01-bootstrap-reconciliation)

`5626339` (phục hồi portable runtime) → `05f3a82` (evidence Phase 4–6) → `38a3e59` (5 file integrity) → `1161dc5` (technical preview) → `a5f2997` (supplemental checksums) → `806abf4` (determinism proof) → `e0c3152` (sửa cú pháp evidence). Candidate zip bytes **không đổi xuyên suốt**: `2a42e815...509e61`. PR #19 (head `ad5c39d`) mở trên upstream, chưa push gì thêm.

## Ràng buộc được tôn trọng

Không publish, không promote, không push; v1 tag `a91e115` nguyên vẹn; candidate v2 duy nhất và bất biến; Supabase không chạm; FRAMEWORK-02 không xuất hiện; quyết định cuối thuộc về chủ sở hữu bản vá tại `OWNER_PATCH_RELEASE_GATE`.
