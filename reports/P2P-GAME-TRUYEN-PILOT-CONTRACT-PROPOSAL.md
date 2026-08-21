# Đề xuất hợp đồng Pilot có kiểm soát — Game Truyện (TÀI LIỆU ĐỀ XUẤT, KHÔNG THI HÀNH)

Tài liệu này là **hợp đồng pilot đề xuất** cho Game Truyện theo §21 của mục tiêu PRE-PILOT. Nó chỉ mô tả điều khoản; **không thi hành bất kỳ bước nào** và mọi thay đổi chỉ xảy ra sau khi Chủ sở hữu phê duyệt tại cổng OWNER_GAME_TRUYEN_PILOT_APPROVAL_GATE.

## 1. Ứng viên

| Trường | Giá trị |
|---|---|
| Ứng viên | `8.4.7-C-codex.35` — FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE |
| SHA256 artifact | `8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47` |
| Artifact | `reports/candidates/P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip` (20.670.642 byte, 1873 tệp, UNACCOUNTED = 0) |
| Lineage anchor | `.34` FW06 (`21df4a3f…` — SHA đầu của bản ghi `.34` trong `development-control.json`) |
| Nguồn | Branch `p2p-fw01-bootstrap-reconciliation`, commit triển khai cuối `871baa1` + các tệp mới bổ sung (governance, capabilities, runtime-manifest.lock, sha256sums, scripts, zip) |
| Trạng thái | UNPROMOTED — không phát hành, không gắn tag |

## 2. Cập nhật bootstrap

Trước pilot, cập nhật `P2P-PROJECT-BOOTSTRAP.md` của Game Truyện (hiện đang pin):

```
RELEASE_IDENTIFIER: p2p-8.4.7-C-codex.24-fw01-v1
RELEASE_SHA256: eb396dc17bd5cfb7c67a80ceff43ccd9050a6bd6fde25afe5919425d100d3d7d
```

thành pin đề xuất:

```
RELEASE_IDENTIFIER: p2p-8.4.7-C-codex.35-fw00-fw06-cumulative-candidate
RELEASE_SHA256: 8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47
```

Lưu ý: pin hiện tại của cả GT và GP là **v1** (`p2p-8.4.7-C-codex.24-fw01-v1`), không phải v2; vì `.35` là một phiên bản khác nên `GT_BOOTSTRAP_UPDATE_REQUIRED = YES`, `GP_BOOTSTRAP_UPDATE_REQUIRED = YES` — nhưng việc cập nhật chỉ xảy ra sau khi Chủ sở hữu phê duyệt.

## 3. Bước cài đặt

```bash
unzip -q P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip -d /tmp/p2p-pkg
cd /tmp/p2p-pkg && ./install.sh project <thư-mục-gốc-Game-Truyện>
```

`install.sh` tạo bảo đảm: `.p2p/approvals/{requests,records}`, `.p2p/gates`, `.p2p/state` (runtime), sao chép foundation + UI/UX runtime + toàn bộ cây hệ thống FW00–FW06, khóa runtime qua `p2p_governance.py lock-runtime`, rồi chạy doctor bắt buộc trước khi ghi `release.json`. Không có bước nào trong hợp đồng này đọc thông tin đăng nhập, tiền, hay Supabase.

## 4. Cổng doctor

Ngay sau cài đặt, bắt buộc:

```bash
python3 <root>/.p2p/system/scripts/doctor.py --root <root>
```

Yêu cầu `RESULT: PASS` với toàn bộ bộ cổng (lineage, stage verification, drift, package integrity). Bác bỏ (`RESULT != PASS`) → dừng, không tiến hành bất kỳ task nào.

## 5. SHA / hash gốc dự án khởi điểm

Game Truyện: HEAD `b0e6deb5330240beff0c9cd8180d8e2d1887652b` tại thời điểm ghi hợp đồng. Trước bất kỳ task pilot nào, ghi lại hash cây toàn bộ (`git hash-object` toàn bộ tệp theo dõi hoặc hash SHA256 cây) làm giá trị gốc so sánh rollback.

## 6. Lớp đột biến được phép

Pilot đầu tiên ưu tiên `READ_ONLY` hoặc `LOW-RISK NON-PRODUCTION`. Cụ thể trong envelope pilot:

- **Được phép:** `READ_ONLY`, `TEST_ONLY`, `DOCUMENTATION`.
- **Cấm tuyệt đối:** `DEPLOYMENT`, `FINANCIAL`, `DATABASE_SCHEMA`, `PRODUCTION_SECRETS`, bất kỳ đột biến nào vào Supabase/RLS, dữ liệu thanh toán, nội dung truyện người dùng.

## 7. Phạm vi bị cấm

Toàn bộ cơ sở dữ liệu Supabase và chính sách RLS; dữ liệu tài chính/thanh toán; nội dung truyện và tài khoản người dùng; mọi nhánh `main`/production của Logistics (`DO_NOT_INSTALL_YET`); Gia Phả (chưa pin `.35`); các tệp bootstrap sau khi đã pin.

## 8. Envelope tự chủ

FW06 autonomy envelope được tải bằng `fw06.save_envelope`/`load_envelope` với:

```python
dict(authorized_scope=["docs", "tests"], non_scope=["prod", "supabase"],
     allowed_mutation_classes=["READ_ONLY", "TEST_ONLY"],
     prohibited_mutation_classes=["DEPLOYMENT", "DATABASE_SCHEMA", "FINANCIAL"],
     owner_gates=["RELEASE", "MUTATION_BEYOND_READ_ONLY"],
     max_parallelism=1,
     retry_policy={"max_retries": 2, "retryable_classes": ["TARGET_UNAVAILABLE"]},
     resource_budget={"attempts": 3})
```

`safe_continuation_decision` trả về bất kỳ giá trị nào không phải tiếp tục an toàn → dừng task, ghi decision trace, chuyển sang Owner.

## 9. Yêu cầu bằng chứng backend thực thi

Mọi task pilot phải xuất `TaskVerifier` receipt (execution_id, outcome, impact classes, evidence_pointers). Task có tác động không xác định (`IMPACT_UNKNOWN`) không được coi là đạt chất lượng.

## 10. Ranh giới cho phép

Quyền chỉ được cấp qua FW01 permission gate; không tác nhân nào tự cấp quyền. FW05 decision record với `owner_decision_required=True` bắt buộc trước mọi đột biến ngoài `READ_ONLY` — dù kết quả quality verdict là `VERIFIED`.

## 11. Hợp đồng chất lượng

Trước khi commit bất kỳ đột biến nào (kể cả `TEST_ONLY`), Quality Contract bắt buộc: impact analysis (changed files/symbols, direct dependents, callers/callees), regression suite cục bộ `PASS` trên vùng bị ảnh hưởng, freshness hiện tại (`CURRENT_COMMIT == INDEXED_COMMIT`), quality verdict `QUALITY_VERIFIED`. Thiếu bất kỳ yếu tố nào → `QUALITY_UNKNOWN` → checkpoint `QUALITY_REVIEW`, không commit.

## 12. Rollback

Nếu pilot thất bại hoặc bị thu hồi: xóa thư mục `<root>/.p2p/` được sao lưu bởi `install.sh` (backup timestamp tại `.p2p/install-backups/`), khôi phục `project-policy.json` từ backup, hoàn nguyên `P2P-PROJECT-BOOTSTRAP.md` về pin cũ. Không rollback cần thiết cho dữ liệu vì không có đột biến sản xuất.

## 13. Cổng Chủ sở hữu

Mọi đột biến vượt `READ_ONLY` yêu cầu `fw05.build_owner_inbox_item` + `fw05.make_decision_record` (`decision_type = OWNER_GATE`) và chờ `resolve_owner_answer` — trong môi trường pilot ban đầu, hành động mặc định an toàn là `WAIT_OWNER`. Pilot không bao giờ tự phê duyệt.

## 14. Phán quyết pilot cuối cùng

Kết thúc pilot, xuất một bản ghi đóng: số task, lớp đột biến đã dùng, verdict quality, decision traces, hash cây cuối so với gốc, kết luận `PILOT_PASS / PILOT_FAIL / PILOT_BLOCKED`, khuyến nghị pin `.35` hoặc không pin. Kết luận này là đầu vào duy nhất cho quyết định promotion/release sau này của Chủ sở hữu.
