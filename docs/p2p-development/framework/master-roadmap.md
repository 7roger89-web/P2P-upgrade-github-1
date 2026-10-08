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
| BLOCKED (historical) | C31 | Verdict BLOCKED / OWNER_ACTION_REQUIRED bảo tồn; blocker Codex bị supercede tại evidence time 2026-08-19T08:55:00Z (lane c36-real-host-binding 8/8 VERIFIED); CURRENT_AUTH_STATE = UNKNOWN_NOT_PROBED |
| HISTORICAL_CERTIFIED (single host) | LIVE_COUNCIL_8_OF_8 | HISTORICAL_ONLY: chứng minh thật 8/8 vai trò trên 1 host Codex @ 8a1ad30; `HISTORICAL_SINGLE_HOST_LIVE_COUNCIL_8_OF_8=TRUE`; `CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN=FALSE`; current status `NOT_PROVEN`; MULTIHOST = NOT_PROVEN |

## Dòng framework (FRAMEWORK-00..06)

| ID | Tên | Trạng thái |
| --- | --- | --- |
| FRAMEWORK-00 | **Product Memory Foundation** — reconciliation C43, product architecture, master roadmap, research intake ledger, capability & skill map, governance sync, validation, closure, terminal report | IN_PROGRESS (goal này) |
| FRAMEWORK-01 | **Autonomous Project Operating Loop** (DONE — PASS / AUTONOMOUS_PROJECT_OPERATING_LOOP_READY; FW01_V2_DEFAULT_BRANCH_DURABILITY_COMPLETE; v1 eb396dc1 + v2 2a42e815 released) | DONE |
| FRAMEWORK-02 | **Project & Capability Intelligence** — DONE, PASS / PROJECT_CAPABILITY_INTELLIGENCE_READY; lớp trí tuệ năng lực trong FW01 (task → năng lực bắt buộc → nguồn đa dạng → coverage fail-closed → decision trace), shadow eval GT+GP PASS, không orchestrator cạnh tranh | DONE |
| FRAMEWORK-03 | Pilot mở rộng + **Council Full Certification** — third-project pilot đã PASS trên `child-learning-lab`; current-lineage `LIVE_COUNCIL_8_OF_8` vẫn `NOT_PROVEN` | IN_PROGRESS — PILOT_PASS / COUNCIL_NOT_PROVEN |
| FRAMEWORK-04 | Release gates tái kiểm tra + re-promotion sau thay đổi runtime | NOT_STARTED |
| FRAMEWORK-05 | Quality & Evidence learning layer (học từ bằng chứng các pilot để cải thiện validation) | NOT_STARTED |
| FRAMEWORK-06 | Review tổng thể sản phẩm + beginner experience audit trước giai đoạn phát hành rộng | NOT_STARTED |

## RF01 — README-first development plane (historical/reconciled)

RF01 không còn là development-plane đang hoạt động. Fresh governance hiện ghi
`CLOSED_VERIFIED_NO_PROMOTION`: RF01 đã được independent verification, C43
reconciliation đã đóng, và AERG đã có current GitHub-runner fail-closed evidence.

Authority vẫn giữ nguyên:
- `.19` là official promoted artifact baseline;
- `.74` là sealed/unpromoted historical reference, không còn là current promotion target;
- promotion vẫn `allowed=false`; mọi promotion tương lai cần fresh current-main candidate,
  independent evidence và Owner gate riêng.

Product fast loop / assurance loop của RF01 vẫn là framework đã được bảo tồn, nhưng
không còn là "next goal". Sau reconciliation, product lane hợp lệ chuyển sang
FRAMEWORK-03. Third-project pilot của FRAMEWORK-03 đã PASS trên
`7roger89-web/child-learning-lab`; phần Council Full Certification của current
lineage vẫn `NOT_PROVEN`.

Required report boundary: không được dùng RF01 history, sealed `.74`, hoặc
historical Council proof để suy diễn promotion/release/current Council certification.

## FRAMEWORK-01 — Định nghĩa mục tiêu tiếp theo (dừng trước thực thi)

Chuẩn hóa closure FRAMEWORK-00 theo chỉ thị Owner (2026-08-19): FRAMEWORK-01 có **duy nhất một mục tiêu** — **AUTONOMOUS PROJECT OPERATING LOOP**: vòng vận hành cho phép P2P khôi phục project truth bền vững và tiếp tục mục tiêu đang dở mà không cần briefing lại từ đầu. C30 là historical DONE (không phải lựa chọn FRAMEWORK-01); chứng nhận đầy đủ LIVE_COUNCIL_8_OF_8 thuộc scope FRAMEWORK-03, không phải FRAMEWORK-01.

Scope đề xuất (định nghĩa, không thực thi):

- Khôi phục trạng thái mục tiêu dở (goal/task state, candidate, roadmap position) từ governance/evidence — không phải từ transcript.
- Decision-intent parsing từ một câu của Owner ("Tiếp tục hoàn thiện dự án.") → trạng thái mục tiêu tiếp theo.
- Mỗi goal vẫn dừng ở terminal report; không tự khởi chạy goal sau; Owner phê duyệt trước mỗi thực thi.

Acceptance bar dự kiến: project truth phục hồi đúng (HEAD, roadmap, evidence), loop parse→resume deterministically, không runtime change trong giai đoạn định nghĩa, validator + regression sạch.

Stop rule: định nghĩa xong → terminal report → STOP; việc thực thi chỉ bắt đầu khi Owner ra lệnh "chạy FRAMEWORK-01".

## FRAMEWORK-02 — Định nghĩa mục tiêu tiếp theo (dừng trước thực thi)

Chuẩn hóa closure FRAMEWORK-01 theo chỉ thị Owner (2026-08-19): FRAMEWORK-02 có
**duy nhất một mục tiêu** — **PROJECT & CAPABILITY INTELLIGENCE**: tầng trí tuệ
năng lực chuẩn tắc — project truth → profile năng lực dự án; task → tập năng lực
bắt buộc; năng lực đến từ nhiều nguồn (skill chỉ là một nguồn); selection giới
hạn; coverage/eligibility/freshness fail-closed; context retrieval có mục tiêu;
decision trace cấu trúc; FW01 consume qua coverage gate; GT/GP shadow eval
read-only PASS.

Scope đề xuất (đã thực thi và chứng minh, theo phê duyệt Owner):
- Hợp đồng năng lực + nguồn năng lực (module/capabilities.json/skill/harness/auth/tooling/owner).
- Skill intelligence đọc skill manifest và evidence bound (không keyword hallucination).
- Bounded skill selection (IRRELEVANT loại bỏ), capability coverage đánh giá tường minh.
- FW01 loop hook sau role selection, trước permission revalidation — fail-closed, không nới quyền.
- Decision trace lưu per-step; beginner output vẫn đơn giản.

Acceptance bar (20 mục, §36): đã chứng minh cơ học toàn bộ.

Stop rule: terminal report → STOP; việc thực thi FRAMEWORK-03 chỉ bắt đầu khi
Owner ra lệnh "chạy FRAMEWORK-03".

## FRAMEWORK-03 — trạng thái hiện tại

FRAMEWORK-03 có hai vế độc lập và không được nhập nhằng:

1. **Real third-project pilot — PASS.**
   - Target: `7roger89-web/child-learning-lab` (JavaScript/browser).
   - Product task: Issue #35 / PR #36, Companion Interaction Pilot V0.2.
   - Repaired head `a0fb67a...` được independent Supervisor PASS tại comment
     `5979999065`.
   - Durable project truth được reconciliation qua PR #41 và stable-identity
     correction qua PR #43; evidence anchor `7a6e534e...`.
   - Boundary giữ nguyên: `CHILD_ENGAGEMENT_PASS=NOT_CLAIMED`,
     `CHILD_SPEAKBACK_PASS=NOT_CLAIMED`, next product gate ở target project là
     real-child observation.
   - Pilot này **không** được dùng để claim V1 skill-consumption receipt: product
     execution gốc diễn ra trước contract receipt hiện hành.

2. **Current-lineage Council Full Certification — NOT_PROVEN.**
   - Historical single-host live Council 8/8 vẫn chỉ là historical evidence.
   - `CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN=FALSE`.
   - Reconciliation host quan sát ngày 2026-10-08 không expose 8 thread/subagent độc lập; theo P2P QUORUM:
     `QUORUM_STATUS=UNAVAILABLE_IN_THIS_HOST` tại evidence time.
   - Không mô phỏng tám vai trong một response và không dùng research-agent khác loại
     làm giả Council receipt.
   - Next condition: chạy trên live host có 8 worker độc lập + per-role receipts.

FW03 runtime machinery không được tạo trong slice này: `team_intelligence.py` và
FW01 integration đã tồn tại từ historical implementation commit `93963d38...`.
Slice hiện tại chỉ reconciliation truth/evidence; không sửa runtime, không mint
candidate, không promotion/release/deploy và không bắt đầu FRAMEWORK-04.

Progress report: `docs/p2p-development/reports/P2P-FRAMEWORK-03-progress-report.md`.

## Stop rule

Giống mọi goal trước: STOP sau mỗi mục tiêu, chờ chỉ thị Owner. Không merge, không promotion, không release, không deploy trong goal này.
