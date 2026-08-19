# Capability & Skill Map — P2P

Chuẩn tắc (canonical) của P2P. Máy đọc file JSON kèm theo (`capability-skill-map.json`); file này là bản đọc dễ hiểu.

## Bốn lớp kỹ năng có thật trong kho

| Lớp | Vị trí | Số lượng | Vai trò |
| --- | --- | --- | --- |
| Codex Edition skills | `.agents/skills/` | 63 thư mục (89 file `SKILL.md`) | Đơn vị kỹ năng nạp theo nhu cầu, gồm 17 skill P2P nền tảng và ~46 skill công nghệ/kỹ thuật/thiết kế |
| P2P system modules | `.p2p/system/p2p_capabilities/` | 54 module | Runtime di động (provider-neutral): vai trò & hội đồng, chọn lựa thích nghi, thực thi giới hạn, failover, bối cảnh, trạng thái |
| Repo scripts | `scripts/` | 23 script | Máy quản trị: validator, goal closure, release gates, install/doctor, certification |
| Canonical council roles | `governance/development-control.json` | 8 vai trò (p2p_iris, p2p_tecton, p2p_axiom, p2p_vector, p2p_datos, p2p_anon, p2p_architecton, p2p_helios) | Hội đồng 8/8; quorum chuẩn tắc 8/8, mẫu số 8 |

## Trạng thái trưởng thành theo nhóm kỹ năng (maturity audit)

Bảng dưới suy ra từ Capability Ledger (158 khả năng, 12 nhóm, trạng thái phân bổ: 61 VERIFIED_IMPLEMENTED, 41 FOUNDATION_READY, 7 PARTIAL, 29 PLANNED, 4 DEFERRED, 15 REJECTED, 1 UNKNOWN) cộng với bằng chứng thực thi thật.

| Nhóm kỹ năng | Trạng thái ledger | Bằng chứng thực |
| --- | --- | --- |
| Vai trò & hội đồng | Hỗn hợp: machinery quorum VERIFIED; chứng nhận 8/8 thật NOT_PROVEN | C35 cổng quorum 8/8 (xác định), C38 chứng nhận p2p_iris thật, C43 smoke p2p_datos |
| Chọn lựa hội đồng thích nghi | VERIFIED_IMPLEMENTED (xác định) | C43 phân loại SINGLE_ROLE/SMALL_REVIEW_SET/FULL_COUNCIL_REQUIRED + bounded live smoke |
| Thực thi | VERIFIED (giới hạn foreground; live thực hiện theo nhà cung cấp) | C12/C15/C17 thực thi giới hạn; C38–C43 thực thi Manus thật |
| Failover & an toàn | VERIFIED_IMPLEMENTED | C39 bốn bằng chứng thật (chọn bình thường, drift chọn lại, liên tục capsule, fail-closed) |
| Bối cảnh | VERIFIED (manifest/envelope/cache xác định; recovery thật) | C36 evidence-bound context; C40 fresh-process recovery trên cả 2 pilot |
| Trạng thái & bằng chứng | VERIFIED_IMPLEMENTED | C10/C11 evidence authority + task state qua mọi milestone |
| Cài đặt & phát hành | VERIFIED_IMPLEMENTED | C40 gói + install/upgrade/rollback/doctor; C43 cài sản xuất Game Truyện + Gia Phả |
| Beginner | VERIFIED_IMPLEMENTED | C13 design intelligence; chu trình beginner xác nhận qua pilot sản xuất |
| Host discovery/selection | VERIFIED (nền chính sách) | C21; C28 onboarding; C30 PLANNED |
| RAG | PARTIAL | Không có hệ thống RAG — NOT_APPLICABLE theo release gates C42 |
| Evals | PARTIAL | Bộ eval UI/UX có nhưng chưa từng chạy với kết quả thật (tiết lộ C42) |

## Khoảng trống mở

1. **LIVE_COUNCIL_8_OF_8 = NOT_PROVEN** — hội đồng đầy đủ 8/8 qua fan-out tự động chưa chứng minh (chỉ 1 vai trò × 1 vòng).
2. Không có hệ thống RAG (theo thiết kế hiện tại).
3. Project evals chưa có kết quả thử nghiệm đã ghi nhận.
4. 6/8 vai trò hội đồng chưa được chứng nhận trực tiếp (chỉ p2p_iris đủ; p2p_datos mới dừng ở smoke-test giới hạn).

## Nguyên tắc liên kết

- Skill Codex Edition nạp theo nhu cầu; metadata trước, SKILL.md sau khi cần.
- Trạng thái khả năng sống trong Ledger; mục tiêu sống trong governance; quyền sự thật sống trong fact-ledger/live-specs.
- Map này là tài liệu tham chiếu; không điều khiển runtime.
