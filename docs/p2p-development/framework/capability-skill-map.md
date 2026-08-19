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
| Vai trò & hội đồng | Machinery quorum VERIFIED; chứng nhận 8/8 thật NOT_PROVEN | Xem ma trận 8 vai trò bên dưới |
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


## Ma trận 8 vai trò chuẩn tắc: ACTIVE / CERTIFIED / LIVE_CERTIFIED

Ma trận này loại bỏ mâu thuẫn chữ (1/8 vs 6/8) bằng ba cột nghĩa rõ, đo theo bằng chứng trong kho. Không vai trò nào "thất bại" — mọi trạng thái là bằng chứng hiện có, không suy diễn vượt ngoài bằng chứng.

| Vai trò | ACTIVE (runtime nạp) | CERTIFIED (chứng nhận qua lifecycle goal) | LIVE_CERTIFIED (CERTIFIED + biên lai thực thi thật) |
| --- | --- | --- | --- |
| p2p_iris | ACTIVE (gói runtime `.p2p/system` + C43 install) | CERTIFIED (C38 live role certification receipt) | LIVE_CERTIFIED (C38: chứng nhận + thực thi thật qua goal C38) |
| p2p_datos | ACTIVE | NOT_CERTIFIED | NOT_LIVE_CERTIFIED (C43 smoke-test: thực thi 1 vòng giới hạn nhưng dispatch không ràng buộc vai trò — 2A reconciliation → verification UNKNOWN) |
| p2p_tecton | ACTIVE | NOT_CERTIFIED | NOT_LIVE_CERTIFIED |
| p2p_axiom | ACTIVE | NOT_CERTIFIED | NOT_LIVE_CERTIFIED (receipt C43 ROLE_ID=p2p_axiom là chuỗi cứng viết tay — 2A reconciliation) |
| p2p_vector | ACTIVE | NOT_CERTIFIED | NOT_LIVE_CERTIFIED |
| p2p_anon | ACTIVE | NOT_CERTIFIED | NOT_LIVE_CERTIFIED |
| p2p_architecton | ACTIVE | NOT_CERTIFIED | NOT_LIVE_CERTIFIED |
| p2p_helios | ACTIVE | NOT_CERTIFIED | NOT_LIVE_CERTIFIED |

**Đọc đúng mẫu số:**
- **CERTIFIED: 1/8** (p2p_iris, qua C38). Dòng "6/8 chưa chứng nhận" trước đây tính cùng một sự thật nhưng theo mẫu số ngược (7/8 NOT_CERTIFIED ≈ "6/8 chưa chứng nhận" khi loại biên lai smoke); ma trận trên dùng mẫu số thống nhất 8 và bỏ cả hai cách viết mập mờ.
- **LIVE_CERTIFIED: 1/8** (p2p_iris). Live smoke C43 KHÔNG tính live certification vì dispatch không ràng buộc vai trò (2A: LIVE_EXECUTED_ROLE = UNBOUND, verification UNKNOWN).
- **LIVE_COUNCIL_8_OF_8 (8 vai trò × fan-out tự động): NOT_PROVEN.** Đây là mục tiêu tiếp theo cần chứng minh thật, thuộc scope FRAMEWORK-03.

**Nolane UI Intelligence (NUI):** nguyên tắc Design Intelligence của NUI vẫn ADAPTED theo bằng chứng kho hiện có (C13 beginner design intelligence lineage + pilot beginner). Tuyên bố bên ngoài "174 NUI faculties" được machinery phân loại **PROVENANCE_NOT_RECOVERED / NOT_PROVEN** (không có artifact kho nào tái hiện con số này) — không phải REJECTED, không phải accepted-as-fact.

## Nguyên tắc liên kết

- Skill Codex Edition nạp theo nhu cầu; metadata trước, SKILL.md sau khi cần.
- Trạng thái khả năng sống trong Ledger; mục tiêu sống trong governance; quyền sự thật sống trong fact-ledger/live-specs.
- Map này là tài liệu tham chiếu; không điều khiển runtime.
