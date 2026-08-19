# Master Roadmap — P2P

File chuẩn tắc tổng hợp hai dòng thời gian: dòng goal C01–C43 đã hoàn tất/bị chặn, và dòng framework FRAMEWORK-00..06 đang bắt đầu. Máy đọc; người đọc dễ hiểu.

**Nguồn suy diễn:** `governance/development-control.json` (roadmap, research_decisions, pr_lineage), `docs/p2p-development/capability-ledger/capability-index.json`, terminal reports C08–C43. Khi có mâu thuẫn, `governance/development-control.json` là chuẩn tắc.

## Dòng timeline goal (C01–C43) — trạng thái hiện tại

| Trạng thái | Mục | Ghi chú |
| --- | --- | --- |
| DONE | C10–C21, C25, C26, C28, C35–C40 | Nền: evidence authority, task state, thực thi giới hạn, design intelligence, delegation, host discovery, onboarding, provider-neutral runtime (C35), context (C36), selection (C37), live role certification (C38), failover (C39), release + pilot install (C40) |
| DONE | PROMOTED (quản trị) | C40 candidate `e7f62384…` PROMOTED 2026-08-18; release gates chạy đủ → `release_decision = PASS_WITH_DISCLOSURES`; release xuất bản `c40-promoted-pilot-release-draft` |
| DONE (ngoài goal chain) | C43 production installs | Cài sản xuất Game Truyện + Gia Phả (2026-08-18): install/doctor/activation/rollback/council audit/smoke — bằng chứng trong `docs/p2p-development/research/c43/evidence/` |
| BLOCKED | C09, C27 | C09 EVENT_EVIDENCE_UNAVAILABLE; C27 LIVE_HOST_EVIDENCE_UNAVAILABLE (môi trường host thật thiếu key) |
| DEFERRED | C08 | Controlled continuation — defer |
| PLANNED | C30, C31 | C30 Composable Execution Target Foundation + provider-neutral intake (no router, no autonomy, no real execution); C31 hoàn tất live host certification trước cross-host continuation |
| NOT_PROVEN | LIVE_COUNCIL_8_OF_8 | Hội đồng 8/8 thật chưa chứng minh (C43) |

## Dòng framework (FRAMEWORK-00..06)

| ID | Tên | Trạng thái |
| --- | --- | --- |
| FRAMEWORK-00 | **Product Memory Foundation** — reconciliation C43, product architecture, master roadmap, research intake ledger, capability & skill map, governance sync, validation, closure, terminal report | IN_PROGRESS (goal này) |
| FRAMEWORK-01 | **Definition of Next Goal** — Owner phê duyệt mục tiêu tiếp theo (đề xuất: hoàn tất LIVE_COUNCIL_8_OF_8 certification trên hội đồng 8/8 thật, hoặc C30 execution-target foundation) | NOT_STARTED — chỉ định nghĩa, không thực thi |
| FRAMEWORK-02 | Thực thi mục tiêu được phê duyệt tại FRAMEWORK-01 (phạm vi theo phê duyệt) | NOT_STARTED |
| FRAMEWORK-03 | Pilot mở rộng theo mục tiêu FRAMEWORK-02 (dự án thứ 3, hoặc ngôn ngữ/framework khác) | NOT_STARTED |
| FRAMEWORK-04 | Release gates tái kiểm tra + re-promotion sau thay đổi runtime | NOT_STARTED |
| FRAMEWORK-05 | Council full certification (8/8 qua fan-out tự động, chứng nhận thật) | NOT_STARTED |
| FRAMEWORK-06 | Review tổng thể sản phẩm + beginner experience audit trước giai đoạn phát hành rộng | NOT_STARTED |

## FRAMEWORK-01 — Định nghĩa mục tiêu tiếp theo (dừng trước thực thi)

Theo mục 32 của chỉ thị Owner, FRAMEWORK-01 chỉ được ĐỊNH NGHỊA tại đây, không thực thi. Hai ứng viên đề xuất cho Owner lựa chọn (quyết định thuộc Owner):

1. **LIVE_COUNCIL_8_OF_8 certification** — chứng nhận hội đồng 8/8 thật qua fan-out tự động, đóng khoảng trống NOT_PROVEN còn lại duy nhất của chuỗi production install.
2. **C30 Composable Execution Target Foundation** — mô hình ExecutionTarget composition + intake provider-neutral, không router/không autonomy/không thực thi thật.

Owner quyết định khi nói "chạy FRAMEWORK-01" và chỉ rõ ứng viên (hoặc mục tiêu khác).

## Stop rule

Giống mọi goal trước: STOP sau mỗi mục tiêu, chờ chỉ thị Owner. Không merge, không promotion, không release, không deploy trong goal này.
