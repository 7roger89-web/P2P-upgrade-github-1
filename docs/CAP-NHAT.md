# Cập nhật khi tác giả phát hành bản P2P mới

## Quy tắc không được bỏ

- Không ghi đè release cũ; giữ ZIP, version, ngày và SHA-256 để rollback.
- Kiểm kê 100% ZIP mới. Cùng tên không có nghĩa là cùng nội dung.
- Đọc đầy đủ mọi file thêm/sửa/xóa/rename trước khi port ngữ nghĩa.
- Baseline 152 file, tài liệu sống và file bổ sung là ba phương trình riêng.
- Inventory PASS chỉ cho phép bắt đầu port, không phải phê duyệt release.
- Mọi ứng viên cuối phải qua FACT_LEDGER/Live Specs, eval dự án, RAG nếu bị
  ảnh hưởng, runtime drift, doctor, rollback và phê duyệt người dùng gắn hash.

## 1. Tạo báo cáo so sánh, chưa sửa runtime

```powershell
py .\scripts\update_from_release.py "<RELEASE_ZIP_PATH>" `
  --out ".\updates\ban-moi"
```

Công cụ sinh inventory, comparison CSV, `release-gates.json` schema 2 và hướng
dẫn bước tiếp theo. Nó không tự port, xóa lịch sử hoặc chuyển gate sang PASS.

## 2. Câu bàn giao cho một chat khác

```text
Đọc docs/AI-HANDOFF.md, manifest/external-sources.json và workbook master schema
2.4. Chạy UPDATE_MAP với ZIP mới; đối chiếu đủ 100% file và giữ baseline cũ.
Sau khi port, chạy LIVE_FACT_PHASE + EVAL_PHASE + RAG_PHASE nếu bị ảnh hưởng +
DRIFT_PHASE. Tạo rollback và technical report trước; không tự phê duyệt và không
release nếu final gate chưa PASS.
```

## 3. Thứ tự port

1. manifest/cấu trúc và file bị đổi;
2. tám agent và QUORUM;
3. router, alias Skill và workflow;
4. module/reference;
5. dữ kiện sống sau kiểm chứng;
6. hook, proxy, network, PXPIPE chỉ sau review bảo mật và yêu cầu riêng.

Giữ mã `P2P-FILE-xxxx` của file cũ. File mới nhận mã tiếp theo; không tái sử
dụng ID của file đã xóa.

## 4. Gate bắt buộc trước khi phát hành

1. semantic review đủ file thêm/sửa/xóa/rename;
2. FACT_LEDGER revision mới có preview kỹ thuật và approval promotion;
3. Live Specs sinh xác định, hash lock khớp;
4. rerun mọi eval bị ảnh hưởng; nếu RAG/source/index đổi, chạy đủ sáu lớp query;
5. dựng lại protected runtime manifest và chạy drift;
6. doctor PASS, lưu candidate cùng SHA-256 và rollback artifact;
7. `p2p_gate.py prepare` tạo technical report;
8. người dùng tự phê duyệt đúng request trong terminal;
9. `p2p_gate.py finalize` tính lại candidate hash;
10. chỉ khi final report PASS mới đổi `release_decision` thành `PASS`.

Không gate nào được ghi đè gate khác; người dùng cũng không thể duyệt bỏ qua một
gate kỹ thuật FAIL.
