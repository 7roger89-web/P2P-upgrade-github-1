# Kiến trúc bản Codex

| Lớp | Vị trí | Vai trò |
| --- | --- | --- |
| Project instructions | `AGENTS.md` | Quy tắc tối thiểu áp dụng cho dự án |
| Skills | `.agents/skills/` | 23 Skill được nạp theo nhu cầu; có `$p2p-idea`, `$p2p-eval`, `$p2p-approval` và `$p2p-uiux` |
| Custom agents | `.codex/agents/` | 8 hồ sơ QUORUM thật |
| Config | `.codex/config.toml` | Bật subagent và giới hạn tám thread |
| State | `.p2p/state/` | ATLAS/CAPSULE tùy chọn, không tự tạo |
| Governance | `governance/` hoặc `.p2p/system/governance/` | FACT_LEDGER, Live Specs, policy eval/RAG/drift/approval và manifest runtime |
| Project evals | `.p2p/evals/` | Bài kiểm tra thật, riêng cho từng dự án |
| Approval records | `.p2p/approvals/` | Yêu cầu và quyết định gắn với đúng hash; không dùng “yes” chung chung |
| Gate reports | `.p2p/gates/` | Bằng chứng kỹ thuật và quyết định cuối cho release/deploy |
| Source snapshot | `source/8.4.6-C/` | 152 file nguyên bản |
| Supplemental sources | `source/supplemental/` | Bốn snapshot do người dùng cung cấp; tách khỏi baseline |
| External-source manifest | `manifest/external-sources.json` | URL, ngày kiểm tra, hash, phạm vi và quy tắc cập nhật nguồn sống |
| Conversion manifest | `manifest/` | Truy vết source → runtime |
| Workbook | `mapping/` | Bản đồ dành cho người và AI |
| Experimental | `experimental/` | PXPIPE nguyên bản, mặc định tắt |

Đường dọc bắt buộc là: nguồn → FACT_LEDGER → phê duyệt promotion → Live Specs
sinh tự động → runtime → eval/RAG bị ảnh hưởng → drift → rollback → yêu cầu phê
duyệt cuối gắn hash → kiểm tra lại hash → release/deploy. Runtime không giữ bản
sao riêng của model ID, giới hạn, giá hoặc “bug model”. Phê duyệt không thể biến
một gate kỹ thuật FAIL thành PASS.

## Vì sao không nạp cả 152 file vào prompt

Giữ đủ file không có nghĩa là nạp đồng thời. Codex chỉ nhận metadata Skill trước,
sau đó đọc `SKILL.md` và reference cần thiết. Cách này giữ kiến thức đầy đủ nhưng
tránh làm loãng ngữ cảnh.

## Tám agent

IRIS lập bản đồ vấn đề; TECTON thiết kế; AXIOM phản biện; VECTOR tối ưu; DATOS
kiểm chứng; ANON phân tích an toàn; ARCHITECTON tích hợp; HELIOS tổng hợp cho
người dùng. Full QUORUM chỉ hợp lệ khi tám thread thật đã chạy.

## Nguồn sống và nguồn snapshot

Con số 152/152 chỉ áp dụng cho ZIP phát hành 8.4.6-C. Tài liệu Google được xem
là nguồn sống: gói giữ liên kết và chỉ mục, không chép toàn văn. File catalog
người dùng cung cấp được giữ đúng byte cùng SHA-256 để lần cập nhật sau AI biết
đâu là nguồn cũ, đâu là nội dung mới.
