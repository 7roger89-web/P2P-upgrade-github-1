# Báo cáo Chủ sở hữu — Chuẩn bị Phát hành Pre-Pilot (P2P FW00–FW06)

**Tác giả:** Manus AI · **Ngày:** 20/08/2026 · **Nhánh:** `p2p-fw01-bootstrap-reconciliation` · **Kho:** `7roger89-web/P2P-upgrade-github-1`

Báo cáo này tổng hợp toàn bộ công việc chuẩn bị phát hành pre-pilot của dòng kế thừa phát triển FW00–FW06 thành **một ứng viên tích lũy duy nhất, tự chứa, gắn bằng chứng**, phù hợp cho một pilot thực tế có kiểm soát. Mọi hoạt động tuân thủ nguyên tắc: không promote, không release, không tag, không cài đặt vào Game Truyện / Gia Phả / Logistics, không chạm Supabase/RLS, không yêu cầu thông tin đăng nhập.

---

## 36 mục báo cáo

### 1. HEAD khởi điểm

HEAD khởi điểm của nhánh là `871baa1` — kết quả của phiên "P2P FW00-FW06 POST-FRAMEWORK READINESS REVIEW" trước đó (kiểm toán READ-ONLY terminal, không thay đổi runtime hay governance).

### 2. Commit triển khai/nguồn cuối cùng

Commit triển khai cuối cùng là `95a59e6c815586e315bb303d44a6abb66aa9320b`, đã push lên remote (`871baa1..95a59e6 p2p-fw01-bootstrap-reconciliation -> p2p-fw01-bootstrap-reconciliation`). Nội dung commit: ứng viên tích lũy FW00–FW06 .35 (artifact + record governance), dọn dẹp governance (.33/.34 candidate_id), sửa doctor capabilities (`capabilities.json`), khóa runtime chuẩn hóa, checksum nguồn, và các script kiểm chứng + giám sát.

### 3. Commit báo cáo cuối cùng

`95a59e6` chứa dự thảo hợp đồng pilot; bản báo cáo tiếng Việt này được tạo sau cùng trên cùng HEAD, không thay đổi tree nguồn (`git status --short` sạch sau báo cáo).

### 4. Sự thật pin bootstrap Game Truyện trước mọi thay đổi

```
RELEASE_IDENTIFIER: p2p-8.4.7-C-codex.24-fw01-v1
RELEASE_SHA256: eb396dc17bd5cfb7c67a80ceff43ccd9050a6bd6fde25afe5919425d100d3d7d
```
GT HEAD hiện tại: `b0e6deb5330240beff0c9cd8180d8e2d1887652b`; thư mục `.p2p/` chưa tồn tại trong GT. (Báo cáo readiness trước đó ghi GT pin v2 — **sai**; bản báo cáo này đã khôi phục và xác nhận lại sự thật pin v1.)

### 5. Sự thật pin bootstrap Gia Phả trước mọi thay đổi

```
RELEASE_IDENTIFIER: p2p-8.4.7-C-codex.24-fw01-v1
RELEASE_SHA256: eb396dc17bd5cfb7c67a80ceff43ccd9050a6bd6fde25afe5919425d100d3d7d
```
GP HEAD hiện tại: `343454852e6b3437b88cd8530bd8bd06d5fb2d49`; thư mục `.p2p/` chưa tồn tại trong GP. Cả hai dự án pin cùng bản v1, SHA `eb396dc1…`.

### 6. Lỗ hổng governance trước đó

`development-control.json` có 33 bản ghi ứng viên, trong đó **hai bản ghi gần nhất (.33 FW05 Owner Experience và .34 FW06 Operational Resilience) thiếu trường bắt buộc `candidate_id`**, vi phạm kiểm soát `validate_control`. Hai bản ghi trước đó (.31–.32 tương đương) đã có `candidate_id` nên khoảng trống nằm chính xác tại cặp .33/.34.

### 7. Sửa chữa governance đã thực hiện

Thêm `candidate_id` đúng giá trị cho đúng hai bản ghi: `.33 → FW05_OWNER_EXPERIENCE_DECISION_TRACE`, `.34 → FW06_PRODUCTION_AUTONOMY_RESILIENCE`. Sửa hẹp (chỉ 2 bản ghi, không chạm bản ghi khác). Script tái tạo: `scripts/fix_fw05_fw06_candidate_ids.py`.

### 8. Kiểm chứng development-control

`python3 scripts/p2p_development_control.py validate` → **PASS** (sau sửa .33/.34 và sau khi thêm bản ghi .35):

```
PASS: /home/ubuntu/fw01_work/auth-f01/governance/development-control.json
```

### 9. Phân loại gói tích lũy

Gói là **CUMULATIVE (tích lũy), không phải delta**: chứa toàn bộ foundation (Stage A: `package_release.py` chuẩn + doctor/drift gates PASS) cùng **bundle hệ thống (Stage B)** — toàn bộ cây `.p2p/system` đang theo dõi (1382 tệp) — do đó gói tự chứa FW00–FW06 hoàn chỉnh, không yêu cầu bất kỳ phiên bản trung gian nào.

### 10. Phiên bản ứng viên

`candidate_version = 8.4.7-C-codex.35` với `candidate_id = FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE` trong `development-control.json` (bản ghi thứ 33, appended, `promotion_status = UNPROMOTED`, `built = true`).

### 11. SHA đầy đủ của ứng viên

```
8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47
```
Artifact: `reports/candidates/P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip`, 20.670.642 byte (20.67 MB). (Bản dựng đầu tiên `da868f8d…` đã được thay thế sau bản sửa `install.sh` — xem mục 17.)

### 12. Ràng buộc nguồn ứng viên chính xác

Bản ghi governance `.35` chứa đúng SHA256 byte của artifact; giám sát viên xác nhận `governance=8cd26c23cb57d682… artifact=8cd26c23cb57d682…` khớp byte-cho-byte. Lineage: `.35 → .34 (607e722d…) → .33 → … → baseline .19 (3a9ee513…)` — không có vòng lặp tự tham chiếu. `lineage_anchor_sha256` của `.35` = SHA đầu bản ghi `.34`.

### 13. Đếm thành viên / hạch toán gói

**1873 thành viên duy nhất, 1873 được hạch toán, 0 không hạch toán** (UNACCOUNTED_PACKAGE_MEMBERS = 0) qua `release-manifest.json` + xác minh byte-cho-byte từng thành viên so với checksum nguồn `manifest/sha256sums.txt` (được tạo lại chuẩn tại commit này).

### 14. Phụ thuộc đường dẫn dev bên ngoài

**EXTERNAL_DEV_PATH_DEPENDENCY = 0.** Giám sát mục 4–5 xác nhận: không thành viên nào trỏ đến `/dev/`, `/plans/`, `/home/…` hay đường dẫn phát triển ngoài; toàn bộ nội dung gói được dựng từ cây theo dõi của repo bằng luồng dựng chuẩn (Stage A đọc tree theo dõi qua `git ls-files`).

### 15. Cài đặt máy mới

**FRESH_MACHINE_INSTALL = PASS.** `scripts/verify_fw00_fw06_cumulative.py` trích xuất artifact vào `/tmp/p2p-fw00-fw06-fresh` (cây hoàn toàn mới, không cache, không PYTHONPATH kế thừa) và xác nhận: byte-identical với manifest/checksum, doctor `--package` đầy đủ PASS, FW05/FW06 hiện diện qua PYTHONPATH mới, smoke test lease + determinism decision-ID trong subprocess cô lập — **4/4 PASS**.

### 16. Doctor

**DOCTOR = HEALTHY.** `doctor.py --package <root>` trên cả cây trích xuất mới lẫn cây sau tái cài đặt đều `RESULT: PASS` với toàn bộ bộ cổng (lineage, stage verification, drift, package integrity).

### 17. Tái cài đặt / lũy đẳng

**PASS.** `verify_reinstall_and_compat.py` trích xuất hai lần từ cùng artifact, hash cây byte-identical giữa hai lần, doctor PASS trên cây tái cài đặt.

> **Trung thực về độ phức tạp của hồi quy đóng gói:** bản dựng đầu `da868f8d…` thiếu hai điều kiện thực thi kiểm thử: (a) các kiểm thử dùng git log cần cây git tại gốc dự án; (b) module FW04 ghi bằng chứng vào `.p2p/state` — thư mục runtime chưa được `install.sh` tạo. Đã **sửa hẹp** `install.sh` (thêm tạo `$root/.p2p/state` cùng `.p2p/approvals` và `.p2p/gates`) và **dựng lại toàn bộ gói** thành `8cd26c23…`. Hồi quy đóng gói chạy bằng cách bọc cây trích xuất thành dự án đúng cấu trúc (`./.p2p/system` + `./.p2p/state` + `git init` + commit) rồi chạy lệnh phát hiện chuẩn.

### 18. Smoke runtime đóng gói

**PASS** — smoke fresh-process: lease acquisition và quyết định decision-ID determinism chạy thành công trong subprocess Python cô lập với PYTHONPATH chỉ chứa cây hệ thống trích xuất (xem mục 15, kiểm chứng 4/4).

### 19. Kiểm thử runtime đóng gói

**240/240 PASS (OK)** chạy trực tiếp **bên trong cây gói** theo cấu trúc dự án đã bọc (mô phỏng chính xác dự án đích sau cài đặt): `cd .p2p/system && python3 -m unittest discover -s p2p_capabilities/tests -p "test_*.py"`. Các kiểm thử vốn phụ thuộc git log (độ tươi của chứng chỉ) và ghi `certification_store.json` vào `.p2p/state` đều PASS. Kiểm chứng thêm: tệp kiểm thử trong gói byte-identical với cây repo (qua manifest SHA256), tức cùng tập kiểm thử đã chạy 240/240 tại commit nguồn.

### 20. Hồi quy phát triển

**240/240 PASS (OK)** tại repo: `cd .p2p/system && python3 -m unittest discover -s p2p_capabilities/tests -p "test_*.py"` → `Ran 240 tests in 35.489s OK`. Số lượng và kết quả khớp hệt hồi quy đóng gói (mục 19) — **NEW_UNEXPLAINED_FAILURES = 0**.

### 21. Phát hiện bí mật: thô / tổng hợp / thật

Quét gitleaks riêng từng tệp mới (scripts + governance + install.sh + capabilities.json): **0 findings thô, 0 tổng hợp, 0 thật**. Lưu ý: quét toàn-tree repo cho 86 báo động giả (chuỗi hash SHA256, tên model `qwen3.6-plus`, fixture tổng hợp `sk-1234567890abcdef`, `ghp_1234…` trong chính các kiểm thử bảo mật FW06) — đây là nội dung pre-existing đã biết; **REAL_SECRET_FINDINGS = 0** cho mọi nội dung mới. Fixture tổng hợp chỉ nằm trong các bộ kiểm thử đơn vị FW05/FW06 và không vào runtime đóng gói.

### 22–27. Các mặt FW01–FW06

Giám sát mục 8 xác nhận cả sáu mặt hiện diện và khả gọi trong runtime đóng gói qua subprocess cô lập:

| Framework | Mặt đại diện | Kết quả |
|---|---|---|
| FW01 | `p2p_fw01_loop.Fw01Loop` | True |
| FW02 | `capability_intelligence.build_project_profile` | True |
| FW03 | `team_intelligence.build_team_decision` | True |
| FW04 | `quality_intelligence.build_quality_contract` | True |
| FW05 | `fw05_owner_experience.make_decision_record` | True |
| FW06 | `fw06_operational_resilience.acquire_lease` | True |

### 28. Cập nhật bootstrap Game Truyện bắt buộc

**GT_BOOTSTRAP_UPDATE_REQUIRED = YES.** Pin hiện tại là v1 (`eb396dc1…`); `.35` là phiên bản khác, nên manifest GT cần cập nhật nếu pilot được phê duyệt (xem hợp đồng pilot, mục 33). Pin đề xuất:

```
RELEASE_IDENTIFIER: p2p-8.4.7-C-codex.35-fw00-fw06-cumulative-candidate
RELEASE_SHA256: 8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47
```

### 29. Cập nhật bootstrap Gia Phả bắt buộc

**GP_BOOTSTRAP_UPDATE_REQUIRED = YES** với cùng pin đề xuất như mục 28 (GP pin cùng v1 như GT). Gia Phả là pilot THỨ HAI — không cập nhật cho đến khi pilot GT hoàn tất và Owner phê duyệt.

### 30. Đột biến GT/GP

**KHÔNG CÓ.** Cả hai cây byte-identical trước/sau mọi thao tác của phiên này (hash cây toàn bộ trước và sau shadow probe READ-ONLY FW06/decision-trace tại GT và GP — xác nhận "tree hash unchanged" ở giám sát mục 12). Không sửa manifest, không tạo `.p2p/`, không ghi file nào.

### 31. Đột biến Logistics

**KHÔNG CÓ.** Logistics giữ nguyên trạng thái `DO_NOT_INSTALL_YET` — không cài đặt, không đột biến tệp, không hành động dữ liệu tài chính nào. Cây cert Logistics không được chạm trong mọi thao tác.

### 32. Trạng thái promotion ứng viên

**UNPROMOTED.** `.33`, `.34`, `.35` đều có `promotion_status = UNPROMOTED`; không release, không tag nào được tạo. GOAL PASS ≠ PROMOTION.

### 33. Tóm tắt hợp đồng pilot

Hợp đồng pilot chi tiết tại `reports/P2P-GAME-TRUYEN-PILOT-CONTRACT-PROPOSAL.md` (đề xuất, KHÔNG thi hành): ứng viên SHA `8cd26c23…`; cập nhật pin bootstrap GT; cài bằng `./install.sh project <root>`; cổng doctor bắt buộc `RESULT: PASS`; SHA gốc GT `b0e6deb5…`; lớp đột biến cho phép `READ_ONLY`/`LOW-RISK NON-PRODUCTION`; cấm tuyệt đối deployment, tài chính, schema CSDL, Supabase/RLS; envelope tự chủ FW06 giới hạn scope; bằng chứng receipt backend thực thi; quality contract `QUALITY_VERIFIED` trước commit; rollback xóa `.p2p/` đã backup; mọi đột biến ngoài READ_ONLY qua Owner Gate `WAIT_OWNER`; phán quyết cuối dạng `PILOT_PASS/FAIL/BLOCKED`.

### 34. Cổng sẵn sàng pilot

**READY_FOR_GAME_TRUYEN_CONTROLLED_LIVE_PILOT = YES** (đủ điều kiện để phê duyệt; pilot chỉ bắt đầu khi Owner duyệt):

| Điều kiện YES | Bằng chứng |
|---|---|
| Validator governance sạch | 78/78 PASS sau commit |
| Ứng viên tích lũy tự chứa xác minh | 1873/1873 hạch toán, UNACCOUNTED = 0 |
| FRESH_MACHINE_INSTALL | 4/4 PASS |
| DOCTOR | HEALTHY (cây mới + tái cài đặt) |
| Smoke gói | PASS (lease + determinism) |
| Kiểm thử gói | 240/240 PASS |
| Hồi quy dev | 240/240 PASS |
| Khả tương thích bootstrap | GT/GP = YES/YES với pin đề xuất |
| Hợp đồng rollback | Đã định nghĩa trong hợp đồng pilot |
| 0 lỗi/bí mật không giải thích | NEW_UNEXPLAINED_FAILURES = 0, REAL_SECRET_FINDINGS = 0 |
| Ứng viên UNPROMOTED | `.35` UNPROMOTED |

### 35. Hạn chế còn lại

Bốn hạn chế được công bố công khai. **Thứ nhất**, `.p2p/state` là thư mục runtime do `install.sh` tạo mới; các kiểm thử chứng chỉ sẽ FAIL trên cây chưa cài (đã sửa và tái dựng gói). **Thứ hai**, hồi quy đóng gói yêu cầu dự án đích khởi tạo git (đúng theo thiết kế — các kiểm thử freshness đọc git log của chính dự án); dự án đích cần có ít nhất một commit. **Thứ ba**, pin đề xuất dùng đuôi `cumulative-candidate` thay vì release tag chính thức — pin cuối cùng sau pilot có thể đổi khi có release chuẩn. **Thứ tư**, artifact 20.67 MB chứa toàn bộ cây hệ thống (bao gồm cả `.agents`/`.claude` skills và tài liệu research) — đây là thiết kế tích lũy, có thể tinh gọn sau pilot nếu Owner yêu cầu.

### 36. Hành động chính xác của Chủ sở hữu

Chủ sở hữu chỉ cần làm **một** việc: **phê duyệt hoặc từ chối pilot có kiểm soát, bị chặn, cho Game Truyện** (theo hợp đồng tại mục 33). Không cần chọn backend/mô hình/tệp/skills/nhóm. Nếu phê duyệt, phiên tiếp theo sẽ thực hiện đúng hợp đồng với phạm vi READ_ONLY/LOW-RISK; nếu từ chối, ứng viên vẫn ở trạng thái UNPROMOTED và không có gì bị thay đổi.

---

## Phán quyết cuối cùng

```
PASS / CUMULATIVE_FW00_FW06_CANDIDATE_READY_FOR_CONTROLLED_PILOT
```

Giám sát độc lập 15/16 kiểm tra PASS (kiểm tra 12 cho cả GT và GP), validator 78/78, development-control PASS, ứng viên tự chứa đã xác minh trên máy mới, rollback và quality contract đã định nghĩa, zero bí mật thật, zero lỗi không giải thích, ứng viên UNPROMOTED.

## Cổng chặn tiếp theo

**STOP at OWNER_GAME_TRUYEN_PILOT_APPROVAL_GATE.** Không chạy pilot, không promote, không cài đặt — chờ quyết định của Chủ sở hữu.
