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
| DONE (historical) | C30 | C30 Composable Execution Target Foundation + provider-neutral intake — PASS (machinery only) 2026-08-17, candidate sealed 94b09b59; chuẩn hóa historical DONE trong FRAMEWORK-00 closure normalization. |
| PLANNED | C31 | Hoàn tất live host certification trước cross-host continuation — bị chặn: LIVE_HOST_EVIDENCE_UNAVAILABLE (C27/C31) |
| NOT_PROVEN | LIVE_COUNCIL_8_OF_8 | Hội đồng 8/8 thật chưa chứng minh (C43) |

## Dòng framework (FRAMEWORK-00..06)

| ID | Tên | Trạng thái |
| --- | --- | --- |
| FRAMEWORK-00 | **Product Memory Foundation** — reconciliation C43, product architecture, master roadmap, research intake ledger, capability & skill map, governance sync, validation, closure, terminal report | IN_PROGRESS (goal này) |
| FRAMEWORK-01 | **Autonomous Project Operating Loop** — vòng vận hành tự động: P2P tự khôi phục project truth và tiếp tục mục tiêu mà không cần briefing lại | NOT_STARTED — đã ĐỊNH NGHỊA (scope, acceptance bar, stop rule), chưa thực thi |
| FRAMEWORK-02 | Thực thi mục tiêu được phê duyệt tại FRAMEWORK-01 (phạm vi theo phê duyệt) | NOT_STARTED |
| FRAMEWORK-03 | Pilot mở rộng (dự án thứ 3 hoặc ngôn ngữ/framework khác) + **Council Full Certification** — LIVE_COUNCIL_8_OF_8 qua fan-out tự động, chứng nhận thật 8/8 vai trò | NOT_STARTED |
| FRAMEWORK-04 | Release gates tái kiểm tra + re-promotion sau thay đổi runtime | NOT_STARTED |
| FRAMEWORK-05 | Quality & Evidence learning layer (học từ bằng chứng các pilot để cải thiện validation) | NOT_STARTED |
| FRAMEWORK-06 | Review tổng thể sản phẩm + beginner experience audit trước giai đoạn phát hành rộng | NOT_STARTED |

## FRAMEWORK-01 — Định nghĩa mục tiêu tiếp theo (dừng trước thực thi)

Chuẩn hóa closure FRAMEWORK-00 theo chỉ thị Owner (2026-08-19): FRAMEWORK-01 có **duy nhất một mục tiêu** — **AUTONOMOUS PROJECT OPERATING LOOP**: vòng vận hành cho phép P2P khôi phục project truth bền vững và tiếp tục mục tiêu đang dở mà không cần briefing lại từ đầu. C30 là historical DONE (không phải lựa chọn FRAMEWORK-01); chứng nhận đầy đủ LIVE_COUNCIL_8_OF_8 thuộc scope FRAMEWORK-03, không phải FRAMEWORK-01.

Scope đề xuất (định nghĩa, không thực thi):

- Khôi phục trạng thái mục tiêu dở (goal/task state, candidate, roadmap position) từ governance/evidence — không phải từ transcript.
- Decision-intent parsing từ một câu của Owner ("Tiếp tục hoàn thiện dự án.") → trạng thái mục tiêu tiếp theo.
- Mỗi goal vẫn dừng ở terminal report; không tự khởi chạy goal sau; Owner phê duyệt trước mỗi thực thi.

Acceptance bar dự kiến: project truth phục hồi đúng (HEAD, roadmap, evidence), loop parse→resume deterministically, không runtime change trong giai đoạn định nghĩa, validator + regression sạch.

Stop rule: định nghĩa xong → terminal report → STOP; việc thực thi chỉ bắt đầu khi Owner ra lệnh "chạy FRAMEWORK-01".

## Stop rule

Giống mọi goal trước: STOP sau mỗi mục tiêu, chờ chỉ thị Owner. Không merge, không promotion, không release, không deploy trong goal này.
