# P2P-OWNER-SELECTED-CAPABILITY-INTAKE-CLOSURE-01 — Báo cáo Owner (27 mục, tiếng Việt)

**Tác giả:** Manus AI | **Ngày:** 2026-08-21 | **Phạm vi:** governance/intake + planner coverage — **không** implement Context Intelligence, **không** sửa runtime/artifact `.41`, **không** mint `.42`, **không** promote mới, **không** mutate dự án.

## 1. Tình trạng baseline chính thức khôi phục
Baseline chính thức: `8.4.7-C-codex.41` @ `da835f8a...` (PROMOTED_VERIFIED, approval `P2P-APR-20260821T035410Z-c41-official-baseline-promotion`). Kho auth-f01 trên nhánh `p2p-roadmap-aware-development-planner-01a`, LOCAL == REMOTE, sạch. Planner bind hash baseline và refuse nếu drift (`BASELINE IDENTITY MISMATCH`).

## 2. Case missed-intake được reproduce cơ học
`CONTEXTUAL_RULE_INTELLIGENCE / Domain Policy Packs` (CRI) — Owner đã ACCEPTED trong một cuộc hội thoại trước đó — **không tồn tại bất kỳ record nào** trong: research-adoption-ledger, research-intake-ledger, capability-index, roadmap, development-control (grep toàn repo = 0 hits, ngoại trừ decision doc chat-archived). Đây là **bằng chứng của absence thực tế**, không phải absence of evidence.

## 3. Kiến trúc intake được xác định (không tạo duplicate)
Ba nguồn tiếp nhận đã tồn tại: research-intake-ledger (decisions), capability ledger (registry), roadmap (goals). Kiến trúc chọn: **intake record → adoption record (research-adoption-ledger) → capability record → enumerated vào roadmap item hiện có (RM-PRIORITY-CONTEXT)**. Không tạo capability mục riêng; không tạo roadmap mục riêng; không touch runtime.

## 4. Intake contract chính tắc (`governance/intake-contract.json`)
Schema `p2p-intake-contract/1` với yêu cầu atomic: idempotent, append-only, fail-closed; mỗi intake ACCEPTED phải có adoption record khớp (bằng `intake_record` id hoặc token-overlap ≥ 2 với `source_name`); bảng alias `capability_family_alias_table` (CONTEXT_AND_KNOWLEDGE ↔ CONTEXT_AND_RETRIEVAL); policy `capability_to_roadmap_enumeration_policy` (option A: thêm vào `source_research_ids` của mục hiện có; option B: liệt kê vào `canonical_capability_ids`; option C: defer note tường minh). Contract được planner hash-bind.

## 5. Reconciliation chính tắc của CRI (append-only)
`RI-007` (intake) → `RA-EXT-029` (ledger, status `PLANNED`, intake_record `RI-007`, canonical_capability_ids `["CRI"]`, roadmap_relation `composition`) → capability `CRI` (`OWNER_ACCEPTED_PROPOSAL`, family `CONTEXT_AND_KNOWLEDGE`) → enumerated vào `RM-PRIORITY-CONTEXT` (source_research_ids + family umbrella). Lịch sử không chạm; chỉ thêm.

## 6. Reconciliation multi-AI caps (3 Owner-accepted proposals)
Ba capability `OWNER_ACCEPTED_PROPOSAL` phát sinh từ decision docs được đưa vào umbrella family các mục roadmap PLANNED (`CONTEXT_AND_RETRIEVAL`, `RECOVERY_AND_CONTINUATION`, `MULTI_AI_SYSTEMS`) — thỏa mãn gate G2 qua family alias; `SAFE_QUIESCE_AND_DRAIN` xác định là **registry inventory** (`origin_type = RECOVERED_LEGACY`), bị loại khỏi gate một cách tường minh.

## 7. Planner v3 — 4 gate coverage mới
G1 `RESEARCH_TO_ROADMAP_REVERSE_COVERAGE` (material ledger records phải được roadmap cite/compose/defer/exclude); G2 `CAPABILITY_TO_ROADMAP_COVERAGE` (chỉ gate future-work capabilities: OWNER_ACCEPTED_PROPOSAL hoặc được adoption material cite, với alias resolution + defer/reject note); G3 `ORPHAN_OWNER_DECISION_DETECTION` (ACCEPTED intake không có adoption = orphan); G4 forward check giữ nguyên. `UNKNOWN` ledger status **never satisfies** coverage.

## 8. Bộ test 01B: 12/12 PASS
A accepted-intake orphan detection; B material adoption without capability/roadmap; C reverse coverage (material research without roadmap); D **exact missed-intake failure mode** (`PLANNING_STATUS = BLOCKED / ROADMAP_COVERAGE_GAP`, `PLAN_COMPLETE=false`, `RECOMMENDED=null`); E reactivity — hoàn thành intake cycle clears gap, restore plan; F registry-inventory caps excluded; G family alias umbrella (thêm alias resolution vào planner); H defer note satisfies; I option-B enumeration; J zero write (trước == sau); K deterministic + hash drift invalidates stale plan; L v3 hash binding intake contract + intake ledger SHAs.

## 9. Bug discovery và fix chính tắc (v2 → v3)
Alias resolution chưa hiện diện trong v2 (`capability_family_alias_table` được contract khai báo nhưng planner không tiêu thụ) — được **phát hiện bởi test G** và fix trong v3. Không bug nào khác của v2 bị lộ; 35/35 tests 01A vẫn giữ nguyên.

## 10. Rerun canonical (không hardcoded winner)
Run `P2P-PLANNER-RUN-03.json`: `ROADMAP_COVERAGE_GAP = false`, `ORPHAN_OWNER_DECISIONS = []`, `PLANNING_STATUS = PLANNING_COMPLETE`, `RECOMMENDED_NEXT_GOAL = RM-PRIORITY-CONTEXT` (score 16.4559 = 9.0 + 1.7059 + 3.0 + 0.5 + 2.25), 6 mục READY_NOW, 6 EXECUTABLE, `PLANNER_SELECTION_DOES_NOT_AUTO_EXECUTE = true`, beginner view 7 câu tiếng Việt bound vào goal được chọn.

## 11. Kết quả required Owner decision
`REQUIRED_OWNER_DECISION = "Approve or reject the planner-recommended next P2P development Goal."` — unchanged semantics; goal được đề xuất vẫn `RM-PRIORITY-CONTEXT` (không hardcoded; reactivity tests chứng minh ranking thay đổi khi input thay đổi).

## 12. Disclosure trung thực
Planner vẫn governance-side — execution loop trong runtime (charter §6) chưa tích hợp (known gap giữ nguyên). CRI adoption `PARTIAL` evidence: live-role reconciliation chưa giải quyết (capability tồn tại trong plan; chứng minh thực thi live còn lại là `NOT_PROVEN` nếu Owner quyết định triển khai). Claim 174 faculties (NUI) `PROVENANCE_NOT_RECOVERED`. Multi-host Council `NOT_PROVEN`. Artifact `.41` bytes không đổi.

## 13. Validator cuối
`VALIDATION: ALL GOVERNANCE CONSOLIDATION CHECKS PASS` — `DANGLING_DEPENDENCIES = 0`, `DUPLICATE_CANONICAL_CAPABILITIES = 0`, `ROADMAP_UNKNOWN_REFERENCES = 0`, `NEW_SECRET_FINDINGS = 0`, `BASELINE_DRIFT = ABSENT`. Ledger: 29 records; roadmap: 18 families / 13 items; capabilities: 170 (PLANNED 39).

## 14. Zero mutation trên dự án
Game Truyện HEAD/tree `b0e6deb5`/`91661a25` không đổi (verified trước/sau toàn task); Gia Phả, Logistics không chạm; không pin upgrade; không public release; không production mutation.

## 15. Anomaly `.40` giữ nguyên phân giải
Approval C40 pilot có subject SHA khác `.40` cumulative — không phải baseline promotion; `V40_WAS_NEVER_OFFICIAL_BASELINE = VERIFIED` (từ P2P-PROMOTE-41-01); không tái xét.

## 16. Atomic intake — bằng chứng fail-closed
Test D reproduce đúng failure mode CRI: với chỉ intake ACCEPTED và chưa adoption, planner refuse với `RECOMMENDED=null` và gap report; Owner không thể "quên" accepted decision mà planner im lặng bỏ qua.

## 17. Forward-reference check (G4)
Roadmap items cite research ids vắng khỏi ledger vẫn bị phát hiện (giữ từ 01A) — cả hai chiều phủ hết.

## 18. Capability→roadmap coverage — semantics material-intent
Chỉ gate capabilities có future work intent thật (OWNER_ACCEPTED_PROPOSAL hoặc adoption material cite); registry inventory (`RECOVERED_LEGACY`, `PROJECT_LEARNING` với notes inventory-only) bị loại tường minh vào `registry_entries_excluded_from_gate` — tránh false-positive flood.

## 19. Hash binding v3
6 SHA-256 bind: roadmap, research-adoption-ledger, capability-index, development-control, intake-contract, research-intake-ledger + baseline version/artifact; timestamp UTC. Plan stale sau drift bị phát hiện cơ học (test K).

## 20. Beginner-first view (7 câu, tiếng Việt)
Được bound vào goal được chọn: RM-PRIORITY-CONTEXT — Content Intelligence completeness (symbol-aware retrieval, token-bounded maps, adaptive context budget, CRI/Domain Policy Packs); risks: NONE; promotion: NO; blocked items liệt kê đúng (DESIGN/Z2P/C09/C27/MULTIHOST); deferred (C08/LARGE-GOAL); Owner decision yêu cầu.

## 21. KHÔNG được tuyên bố
Planner **không** auto-execute; **không** viết code; **không** mutate dự án; **không** approve goal; recommendation ≠ approval; `RM-PRIORITY-CONTEXT` vẫn `PLANNED`, chưa được Owner phê duyệt thực hiện.

## 22. Verdict duy nhất

`PASS / P2P_OWNER_SELECTED_CAPABILITY_INTAKE_CLOSED_VERIFIED`

```
OWNER_ACCEPTED_CAPABILITY_INTAKE = CLOSED
INTAKE_CONTRACT = CANONICAL
PLANNER_COVERAGE_GATE_V3 = VERIFIED (12/12 negative tests)
MISSD_INTAKE_FAILURE_MODE = REPRODUCED_AND_CLOSED
BASELINE_DRIFT = ABSENT
NEW_SECRET_FINDINGS = 0
```

## 23. Deliverables
1. `governance/intake-contract.json` + docs companion — intake contract chính tắc.
2. `scripts/p2p_roadmap_planner.py` VERSION=3 — v3 gates G1–G4 + alias resolution + hash binding intake.
3. `scripts/p2p_planner_01b_test.py` — 12/12 PASS negative/reaction tests.
4. `reports/planner/P2P-PLANNER-RUN-03.json` — canonical run evidence.
5. Durable records: ledger RA-EXT-029 (CRI), capability CRI, roadmap source_research_ids (option A), capability-index note, provenance_log entry.
6. Báo cáo 27 mục này.

## 24. Cam kết tuân thủ
Không sửa runtime; không sửa artifact `.41`; không promote; không mint `.42`; không re-run Council; không rewrite lịch sử C31/C36; append-only reconciliation; LOCAL == REMOTE.

## 25. Giới hạn môi trường
Planner chạy trong sandbox Ubuntu 24.04 Python 3.12; dependency-necessity graph thuần JSON (không cần git/worktree live); không thử nghiệm trên host live — không ảnh hưởng đến `UNKNOWN_NOT_PROBED` host state (khai báo từ readiness review).

## 26. Impact dự án
0 file đột biến trên GT/GP/Logistics; chỉ governance files thay đổi (charter-adjacent invariant giữ nguyên — 01B không thêm invariant mới vào charter vì gate changes là behavior của planner, không phải architectural invariant mới).

## 27. Quyết định Owner chính xác tiếp theo

> Approve or reject the planner-recommended next P2P development Goal (RM-PRIORITY-CONTEXT).

Sau Owner decision: nếu approve → P2P sẽ thực hiện Context Intelligence completion theo scope Owner phê duyệt (READ_ONLY goal, không production mutation); nếu reject → planner rerun với owner-value override hoặc Owner chỉ định goal khác.

---
*Báo cáo này chỉ đọc bằng chứng; promotion baseline chính thức vẫn là `8.4.7-C-codex.41`.*
