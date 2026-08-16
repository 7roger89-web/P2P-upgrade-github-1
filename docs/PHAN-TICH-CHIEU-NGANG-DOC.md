# Phân tích P2P theo chiều ngang và chiều dọc

## Cách đọc bản phân tích này

- **Chiều ngang**: cùng một rủi ro đi qua nhiều thành phần: fact, prompt, RAG, agent, state,
  eval, update và tài liệu.
- **Chiều dọc**: theo dõi một công việc từ đầu vào đến retrieval, suy luận, hành động,
  bằng chứng, bàn giao, phát hành và rollback.

Mục đích là tìm lỗ hổng giữa các bộ phận, không chỉ kiểm tra từng file riêng lẻ.

## Ma trận chiều ngang

| Trục | Lỗ hổng dễ bị bỏ qua | Kiểm soát trong codex.4 |
| --- | --- | --- |
| Dữ kiện sống | Tên model, giới hạn, giá hoặc lỗi bị chép cứng | FACT_LEDGER có scope, nguồn, evidence, status, check/expiry và route |
| Độc lập bằng chứng | Nhiều AI nhắc lại cùng một trang bị coi là nhiều phiếu | `independence_key`; báo cáo AI là đường tìm, không phải phiếu bầu |
| Đồng bộ | Sinh file mới nhưng runtime vẫn đọc bản cũ | Live Specs sinh xác định, khóa hash, đếm claim và gate drift |
| Trạng thái | “Không thấy bản vá” bị hiểu là “bug còn hoạt động” | Tách `NOT_RECHECKED`, `NO_EVIDENCE_OF_FIX`, `DISPUTED`, `CONFIRMED_ACTIVE`, `RETIRED` |
| Eval | Lấy benchmark chung thay cho việc thật hoặc để hai lượt rò đáp án | Suite riêng dự án, fixture khóa, paired baseline/P2P, cô lập và ghi surface/model/ngày |
| RAG | Prompt trả lời hay che retrieval kém | Đo expected/retrieved source ID, recall, grounding, citation và injection resistance |
| Ranh giới | Văn bản trong tài liệu chiếm quyền chỉ thị | Tách INSTRUCTIONS, TRUSTED_DATA, UNTRUSTED_DATA, SECRET; filter trước xếp hạng |
| State | Một schema CAPSULE làm mất ý tưởng hoặc bằng chứng sự cố | Bốn profile: task, brainstorm, research, incident |
| QUORUM | Tám thread nhân bản dữ liệu nhạy cảm và quyền của phiên cha | Redaction, bằng chứng tối thiểu, ghi parent permission và thread ledger |
| Khám phá skill | Skill có trên đĩa nhưng không hiện trong danh sách rút gọn | `$p2p` là router chính; doctor kiểm tra file thật, không suy từ menu |
| Cập nhật | Inventory PASS bị nhầm là port thành công | Gate riêng cho semantic review, ledger, Live Specs, eval, RAG, drift, rollback và doctor |
| Phê duyệt | AI tự coi “ok” cũ, im lặng hoặc thay đổi file sau duyệt là được phép | Duyệt sau gate kỹ thuật, tách requester/approver, khóa subject/report SHA-256, hết hạn và vô hiệu khi drift |
| Policy | Một suite tự hạ ngưỡng để đạt PASS | Project policy là mức sàn; suite/RAG chỉ được giữ hoặc siết chặt |
| Thử nghiệm | Mã nén/heuristic cũ có mâu thuẫn nhưng vẫn được gọi | PXPIPE được giữ nguyên để audit nhưng bị tắt trong runtime |

## Chuỗi chiều dọc

1. **Intake** — chốt mục tiêu, phạm vi, quyền, dữ liệu nhạy cảm và điều kiện dừng.
2. **Authority** — xác định chỉ thị nào có quyền; nội dung tìm được chỉ là dữ liệu.
3. **Source** — gán source ID, phiên bản/hash, trust, sensitivity, project/tenant và validity.
4. **Retrieval** — lọc ranh giới trước, sau đó mới semantic ranking; ghi raw retrieved IDs.
5. **Reasoning** — tách FACT, INFERENCE, USER_ASSUMPTION, DISPUTED và UNKNOWN.
6. **Action** — quyền dùng tool không được sinh ra từ prompt hay tài liệu; hành động rủi ro cần gate riêng.
7. **Evidence** — lưu artifact/kiểm thử/citation có thể kiểm tra, không dùng chain-of-thought.
8. **State** — ghi CAPSULE đúng loại phiên; session metrics không thay thế eval.
9. **Technical gate** — eval, RAG nếu bị ảnh hưởng, drift, security và rollback phải PASS.
10. **User decision** — tạo yêu cầu chỉ sau bước 9, gắn với hash và để người dùng tự quyết định.
11. **Recheck** — tính lại hash ngay trước hành động; thay đổi một byte là mất hiệu lực.
12. **Rollback** — giữ gói cũ, hash, backup và lịch sử; sau khôi phục phải chạy doctor lại.

## Những giới hạn còn cố ý để mở

- Khung eval đã sẵn sàng nhưng chưa có kết quả cho dự án của người dùng.
- Khung retrieval đã sẵn sàng nhưng chưa chạy trên corpus/index thật.
- Tám TOML là đầy đủ về cấu trúc; một QUORUM thật vẫn phải được host chứng minh bằng tám
  thread/ID. Prompt không thể tự tạo khả năng host.
- Dữ kiện Live Specs phải được kiểm tra lại trước ngày hết hạn; cổng drift sẽ chặn sau hạn.
