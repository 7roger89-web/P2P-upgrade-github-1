# P2P Mandatory Required Read: AI Execution Reliability Guard (AERG)

## 1. Mục đích và Phạm vi
Tài liệu này định nghĩa các nguyên tắc và cơ chế thực thi của năng lực **AI Execution Reliability Guard (AERG)**. Năng lực này được thiết kế để bảo vệ tính toàn vẹn của dự án P2P bằng cách ngăn chặn việc tin tưởng mù quáng vào các xác nhận tự thân của AI (AI self-reports) mà không có bằng chứng xác thực độc lập. AERG hoạt động như một lớp bảo vệ trung lập với nhà cung cấp (provider-neutral), không phụ thuộc vào các nhãn an toàn hoặc độ tin cậy của bất kỳ mô hình ngôn ngữ cụ thể nào.

## 2. Các Nguyên tắc Cốt lõi
*   **CLAIM != EVIDENCE**: Mọi tuyên bố của AI về trạng thái dự án, kết quả kiểm tra hoặc tính an toàn của mã nguồn đều bị coi là một "Claim" (tuyên bố) chưa được xác thực cho đến khi có bằng chứng đi kèm.
*   **DETERMINISTIC_FIRST**: Bằng chứng phải có tính xác định (deterministic) và có thể kiểm chứng lại bởi các công cụ hệ thống hoặc Owner.
*   **FAIL_CLOSED_ON_CONTRADICTION**: Nếu có bất kỳ mâu thuẫn nào giữa tuyên bố của AI và bằng chứng thực tế, hệ thống phải ngay lập tức chuyển sang trạng thái Fail-Closed và yêu cầu sự can thiệp của Owner.
*   **PROVIDER_NEUTRALITY**: Các cơ chế bảo vệ không được dựa vào các tính năng hoặc nhãn đặc thù của nhà cung cấp (ví dụ: "safety_filter: pass").

## 3. Mô hình Xác nhận Bằng chứng (Evidence Claim Model)
Mọi hành động thực thi quan trọng phải tuân theo cấu trúc xác nhận:
1.  **Subject Binding**: Xác định đối tượng bị tác động (ví dụ: file SHA, process ID).
2.  **Claim Statement**: Tuyên bố của AI về đối tượng đó.
3.  **Evidence Link**: Liên kết đến bằng chứng xác thực (ví dụ: file log, kết quả lệnh shell).
4.  **Freshness Check**: Đảm bảo bằng chứng được tạo ra trong cùng một chu kỳ thực thi và không bị lỗi thời.

## 4. Các Mức độ Đảm bảo (Assurance Levels)
*   **L0 (NONE)**: Không có bằng chứng, chỉ có tuyên bố. Bị cấm cho mọi hành động ghi (write).
*   **L1 (CLAIM_WITH_LOG)**: Tuyên bố kèm theo log thô. Chỉ dùng cho các thao tác đọc hoặc debug.
*   **L2 (VERIFIED_BY_TOOL)**: Tuyên bố được xác thực bởi một công cụ độc lập (ví dụ: `grep`, `sha256sum`).
*   **L3 (DETERMINISTIC_PROOF)**: Tuyên bố có bằng chứng toán học hoặc logic không thể chối cãi (ví dụ: git diff sạch, validator pass).

## 5. Ràng buộc Thực thi
*   Không có hành động merge, promote hoặc release nào được phép thực hiện nếu mức độ đảm bảo dưới **L3**.
*   Các phát hiện mâu thuẫn (Contradiction Detection) phải được ghi lại vĩnh viễn trong `decision_trace.py`.
*   Việc làm yếu (weakening) các bài kiểm tra để đạt trạng thái "Green" bị coi là vi phạm nghiêm trọng chính sách AERG.

---
*Tài liệu này là một phần của source of truth quản trị dự án P2P. Mọi thay đổi phải được Owner phê duyệt thông qua quy trình intake chính thức.*
