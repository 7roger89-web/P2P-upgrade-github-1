# Cách sử dụng

## Ba Skill chính

| Câu bạn gõ | Tác dụng |
| --- | --- |
| `$p2p-idea <ý tưởng>` | Hỏi tối đa ba câu quan trọng, so sánh lựa chọn và đề xuất bước thử đầu tiên |
| `$p2p <nhiệm vụ>` | Phân loại nhiệm vụ và chọn workflow phù hợp |
| `$p2p-quorum full <nhiệm vụ>` | Chạy tám agent thật và tổng hợp một kết luận |

## Cách nhận gợi ý sát ý tưởng hơn

Hãy cho `$p2p-idea` biết điều bạn đã có, điều bạn chưa biết và giới hạn thực tế.
Bạn không cần dùng thuật ngữ kỹ thuật. Mẫu ngắn:

```text
Dùng $p2p-idea cho ý tưởng: [ý tưởng của tôi].
Người hưởng lợi/khách hàng: [nếu biết].
Tôi đang có: [thời gian, tiền, kỹ năng, dữ liệu hoặc công cụ].
Điều không được làm: [nếu có].
Tôi là người mới; chỉ hỏi tối đa 3 câu làm thay đổi quyết định.
```

Kết quả tốt phải có: phương án chính, lý do phù hợp, giả định, mức tin cậy,
điều gì có thể làm đổi kết luận, và một thử nghiệm nhỏ có tiêu chí dừng/tiếp tục.
“Phù hợp nhất hiện tại” không phải lời bảo đảm; độ chính xác tăng lên khi bạn
đưa phản hồi thật từ bước thử quay lại chat.

## Các workflow tương thích P2P cũ

| Skill | Dùng khi |
| --- | --- |
| `$p2p-scope` | Công việc lớn, nhiều bước |
| `$p2p-explore` | Cần nhiều ý tưởng hoặc phương án |
| `$p2p-atlas` | Theo dõi mục tiêu, tiến độ và blocker |
| `$p2p-capsule` | Bàn giao sang chat khác |
| `$p2p-chain` | Chạy một chuỗi vai trò agent cụ thể |
| `$p2p-feedback` | Ghi nhận điểm tốt, lỗi và cách sửa |
| `$p2p-metrics` | Xem chỉ số tiến độ/chỉnh sửa |
| `$p2p-eval` | Tạo hoặc chạy bộ đánh giá riêng cho dự án |
| `$p2p-approval` | Giải thích, chuẩn bị và kiểm tra cổng phê duyệt bắt buộc |
| `$p2p-karpathy` | Chỉnh code tối thiểu, không lan phạm vi |
| `$p2p-teacher` | Học P2P từ cơ bản |
| `$p2p-download` | Nhận và kiểm chứng release P2P mới |
| `$p2p-pxpipe` | Kiểm toán PXPIPE; mặc định không bật |

`$p2p-approval` không được tự bấm duyệt thay bạn. Sau khi các gate kỹ thuật
PASS, Skill chỉ đưa đường dẫn yêu cầu và đúng lệnh PowerShell để bạn tự xác nhận.

## Nhớ nhanh: `$` gọi Skill, `@` gọi agent

- Gõ `$p2p-idea` hoặc `Dùng $p2p-idea...` để gọi workflow.
- Gõ `@p2p_iris` khi muốn giao trực tiếp một việc cho IRIS và host có hỗ trợ.
- Gõ `$p2p-quorum full` để coordinator chạy tám agent thật và xuất ledger.

Tên thư mục nằm trên ổ D không tự kết nối với Codex. Bạn phải mở đúng thư mục
dự án trong Codex; Skill/agent phải nằm dưới `.agents/skills` và `.codex/agents`
của chính root đó (hoặc được cài ở phạm vi người dùng).

## Cách gọi tương thích bản P2P cũ

- `Q:` → `$p2p quorum`;
- `AUTO:` → chất lượng là ưu tiên, vẫn kiểm chứng dữ kiện hiện hành;
- `MANUAL:` → AI hỏi bạn chọn đánh đổi quan trọng;
- `MAX:` → đầu ra đầy đủ với bằng chứng và kiểm tra, không phải suy luận ẩn;
- `full ui menu` → menu Codex và bản đồ các lệnh tương thích;
- `/debug` → `$p2p debug`.

## Skill độc lập

- `$bb4pda`: tạo BBCode cho diễn đàn 4PDA.
- `$notebook-pack`: tạo bộ nguồn RAG hoàn chỉnh.
- `$rag-prep`: chuẩn hóa tài liệu trước khi đưa vào RAG.
- `$rag-grounding`: tạo prompt trả lời bám nguồn và có trích dẫn.
- `$rag-router`: chọn môi trường và chiến lược RAG.

RAG skill chỉ chuẩn bị, định tuyến và kiểm tra retrieval. Nó không tự biến một
thư mục thành vector database. Đọc `docs/QUAN-TRI-FACT-EVAL-RAG.md` khi cần triển
khai RAG thật hoặc cập nhật model/giới hạn/bug.

## Áp dụng cho một dự án thật

Sau khi cài P2P vào dự án, hãy mô tả mục tiêu, file liên quan, điều không được
thay đổi và tiêu chí hoàn tất. Ví dụ:

```text
Dùng $p2p-scope cho dự án này.
Mục tiêu: xây website giới thiệu dịch vụ logistics.
Không được thay đổi hệ thống đăng nhập hiện có.
Hoàn tất khi trang chạy được, responsive và kiểm thử chính đều đạt.
```

P2P không tự kết nối với một thư mục chỉ vì thư mục nằm ở ổ D. Codex phải mở
đúng thư mục dự án hoặc được cung cấp đường dẫn/file.
