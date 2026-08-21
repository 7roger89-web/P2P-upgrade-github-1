# P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01A — Final Owner Report

**Goal ID:** P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01A (corrective hardening của PLANNER-01)
**Phạm vi:** governance/roadmap-only — không sửa runtime, không sửa artifact `.41`, không promote mới, không implement mục roadmap, không mutate dự án, không mint `.42`
**Author:** Manus AI
**Ngày:** 2026-08-21 (UTC)
**Baseline chính thức tại thời điểm bắt đầu:** `8.4.7-C-codex.41` (PROMOTED_VERIFIED, SHA `da835f8a...`)

---

## 1. Trạng thái recovery truth trước hardening

Khôi phục truth bằng chứng tại thời điểm bắt đầu: kho `auth-f01` sạch, LOCAL==REMOTE, HEAD tại `696f9b0` (nhánh `p2p-roadmap-aware-development-planner-01`); baseline chính thức `8.4.7-C-codex.41` PROMOTED_VERIFIED, byte artifact recomputed khớp `da835f8a48caf4536094ffdd82e3c65baa82da32aa9a7ae73714ee1f2e9c3d2d`; các nguồn canonical được tiêu thụ trực tiếp: `governance/development-control.json`, `governance/p2p-development-roadmap.json`, `governance/research-adoption-ledger.json`, `docs/p2p-development/capability-ledger/capability-index.json` — `ROADMAP_MANUAL_REENTRY_REQUIRED = NO`.

## 2. Danh tính planner old (PLANNER-01) và evidence cũ

Planner v1: `scripts/p2p_roadmap_planner.py` SHA `b0a0b92c71001c96b4815ac59f7ff14e35466421842b910b03bcd173816bd157`; run evidence `reports/planner/P2P-PLANNER-RUN-01.json` SHA `4096428e...` (verdict PLANNER-01: `PASS / P2P_ROADMAP_AWARE_DEVELOPMENT_PLANNER_VERIFIED`, 18/18 tests). Báo cáo `P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01-REPORT.md` (nhánh `p2p-roadmap-aware-development-planner-01`, commit `696f9b0`) được **giữ nguyên làm lịch sử** — không bị viết lại; 01A là corrective hardening, không phủ nhận lịch sử.

## 3. Reproduce cơ học — Bug 1: coverage pass-open

Fixed fixture với coverage gap thật (mục roadmap có `source_research_ids` không tồn tại trong ledger): planner v1 vẫn emit `RECOMMENDED_NEXT_GOAL`, không có trường `PLAN_COMPLETE`, exit 0. Ba claim trước đây của PLANNER-01 sai trên fixture này: (1) "PLANNER RECOMMENDS ONLY IF COVERED", (2) "UNKNOWN_REFERENCE_PASS_OPEN = 0", (3) "ROADMAP_COVERAGE_FALSE_NEGATIVE = 0" — cả ba bị bác bỏ cơ học: **`ROADMAP_COVERAGE_PASS_OPEN_BUG = CONFIRMED`**.

## 4. Audit ngữ nghĩa coverage — SELECTED/PLANNED/PARTIAL

Audited ledger vocabulary: `LEDGER_MATERIAL_STATUSES` được mã hóa tường minh — `SELECTED`, `PLANNED`, `PARTIAL` dịch thành trạng thái bao phủ hợp lệ (vật liệu nghiên cứu hiện diện), `REJECTED`/`UNKNOWN`/`DEFERRED` không bao giờ thỏa mãn coverage; `UNKNOWN_SOURCE` → gap fail-closed. Không dùng heuristic tự động; translation bảng tường minh, kiểm tra được.

## 5. Phân giải anomaly C09/C27 — Bug 3

Planner v1 dịch `status BLOCKED not in deterministic vocab` → `UNKNOWN` cho `RM-C09` (event evidence unavailable) và `RM-C27` (live-host evidence unavailable): **`KNOWN_BLOCKED_MISCLASSIFIED_UNKNOWN > 0`** (2 mục). 01A phân loại mới tường minh: `BLOCKED_BY_EXTERNAL_EVIDENCE` cho cả hai (lý do `EVENT_EVIDENCE_UNAVAILABLE`, `LIVE_HOST_EVIDENCE_UNAVAILABLE`); `BLOCKED_BY_DEPENDENCY` khi phụ thuộc item chưa hoàn thành; `OWNER_DEFERRED` (C08). `UNKNOWN` chỉ dành cho status không nằm trong vocabulary và trigger fail-closed — không còn dùng làm lớp phân loại khối bình thường.

## 6. Bug 4 — dependency-necessity weight không được dùng

Audited `WEIGHTS`: `dependency_necessity: 2.0` khai báo nhưng `rank_items()` v1 không đọc. **`DEPENDENCY_NECESSITY_WEIGHT_UNUSED = CONFIRMED`** (2.0 khai báo, 0.0 thực dụng).

## 7. Fix v2 — fail-closed coverage + PLAN_COMPLETE

Planner v2 (`VERSION=2`): `build_plan` yêu cầu **đồng thời** `coverage_gap = FALSE` **và** tồn tại ≥1 mục `READY_NOW` → `PLAN_COMPLETE`, mới emit `RECOMMENDED_NEXT_GOAL`; ngược lại `RECOMMENDED_NEXT_GOAL = null`, `PLANNING_STATUS ∈ {"BLOCKED / ROADMAP_COVERAGE_GAP", "NO_EXECUTABLE_GOAL"}`, `PLAN_COMPLETE = false`. Unknown status bất kỳ đâu trong input → `PlannerError` + exit ≠ 0.

## 8. Fix v2 — classification đúng + dependency-necessity thật

Classification: blocked items → `BLOCKED_BY_EXTERNAL_EVIDENCE`/`BLOCKED_BY_DEPENDENCY`/`OWNER_DEFERRED`; `PARTIAL` ledger dependency → `READY_NOW` (với disclosure); `UNKNOWN` chỉ fail-closed. Dependency-necessity factor mới (chuẩn hóa 0–1): tỉ lệ blocked-dependents, bonus terminal-prerequisite (cho goal đứng trước Z2P/LARGE-GOAL hoặc ≥2 dependents), độ sâu cạnh blocking; nhân weight 2.0 thực dụng. Công thức 5 yếu tố: `SCORE = 3.0·owner_value + 2.0·dependency_necessity + 1.5·safety_maturity + 1.0·evidence_gap + 1.5·architectural_leverage`.

## 9. Fix v2 — score decomposition + WHY evidence-bound + beginner view

Mỗi mục có `SCORE_BREAKDOWN` (formula + weights + contributions từng yếu tố, tổng khớp `total`). `WHY_THIS_GOAL` giờ trích dẫn **text bền trong goal** ("durable text: ...") + contribution từng yếu tố; claim chung chung "blocks/leverages higher-strategic-value" bị loại bỏ. Beginner view tiếng Việt (7 câu) **bound vào goal được chọn**: tiêu đề, owner_value, `project_impact`, `promotion_required`, dependency/blocker list của chính mục đó — khác selection khác view.

## 10. Rerun chính tắc trên roadmap hiện tại

Rerun v2 trên truth canonical sau reconciliation (mục 11): `PLANNING_STATUS = PLANNING_COMPLETE`, `PLAN_COMPLETE = true`, `RECOMMENDED_NEXT_GOAL = RM-PRIORITY-CONTEXT` (score 16.4559; decomposition: 9.0 + 1.7059 + 3.0 + 0.5 + 2.25 = 16.4559). `EXECUTABLE` (READY_NOW): CONTEXT, RELEASE-LIFECYCLE, PLANNER, DRIFT-SWEEP, ORCA-EXT, CODE-MUTATION (6 mục). `STRATEGIC` top-5: CONTEXT 16.4559, DESIGN 13.5, Z2P 12.75, RELEASE-LIFECYCLE 12.0, C09 9.5441. C09 xếp cao hơn v1 nhờ necessity factor — ranking reactivity thật.

## 11. Corrective reconciliation — 2 provenance record mới (append-only)

Run v2 fail-closed phát hiện 2 dangling `source_research_ids`: `RM-PRIORITY-CODE-MUTATION → 'Pilot-02'`, `RM-PRIORITY-RELEASE-LIFECYCLE → 'C43'` — không tồn tại trong ledger (id chuẩn `RA-EXT-*`). Reconciliation chính tắc (intake rule "OWNER_SELECTED_CAPABILITY → DURABLE_ROADMAP_RECORD"): ledger 26 → 28 bản ghi, bổ sung `RA-EXT-027` (Pilot-02: `VERIFIED` — 3 claim Pilot-02; ladder base cho code mutation) và `RA-EXT-028` (C43 install evidence pack: `PARTIAL` — evidence tồn tại, live-role identity reconciliation chưa giải quyết theo `c43-reconciliation.json`). Roadmap item source ids sửa về id chuẩn kèm `reconciliation_note_01a`; **không mục nào khác bị chạm**.

## 12. Bộ test 01A — 35/35 PASS

Harness `scripts/p2p_planner_01a_test.py`, fixture repo cô lập + planner chạy subprocess trên output thật: **A** coverage gap fail-closed (v1 pass-open bị đóng — không recommendation dù có 6 mục READY_NOW); **B** omitted record phản xạ; **C** C09/C27 `BLOCKED_BY_EXTERNAL_EVIDENCE`, không UNKNOWN, `UNKNOWN_STATUS_ITEMS = []`; **D** unknown status → exit ≠ 0, message gọi tên status; **E** C09/Z2P không bao giờ `EXECUTABLE`; **F/G** necessity factor tăng khi thêm blocked-dependents, giảm khi gỡ; **H** deterministic 2 run identical truth → output identical; **I** hash drift: roadmap bytes đổi → hash trong plan đổi, plan cũ không khớp truth mới; **J** beginner view thay theo goal được chọn (title/impact/promotion của chính mục); **K** decomposition sum = total, WHY cites durable text, generic claim loại; **L** zero execution / zero project mutation (watch c43 evidence pack: before == after; output chỉ tại `--output`).

## 13. Zero auto-execution + zero project mutation (không đổi)

Giữ nguyên invariant PLANNER-01: `AUTO_EXECUTION_ATTEMPTS = 0`, `PROJECT_MUTATION_ATTEMPTS = 0`, `PLANNER_SELECTION_DOES_NOT_AUTO_EXECUTE = true` — kiểm chứng lại trong test L và canonical run: output là file plan JSON, không chạm runtime/artifact/dự án.

## 14. Verdict 01A duy nhất

**`PASS / P2P_ROADMAP_PLANNER_FAIL_CLOSED_SEMANTICS_FINALIZED`**

## 15. Canonical statements

`PLANNER_VERSION = 2` | `ROADMAP_COVERAGE_PASS_OPEN_BUG = CONFIRMED → CLOSED` | `SELECTED_PLANNED_PARTIAL_SEMANTICS = EXPLICIT` | `KNOWN_BLOCKED_MISCLASSIFIED_UNKNOWN = FIXED` (C09/C27 → BLOCKED_BY_EXTERNAL_EVIDENCE) | `DEPENDENCY_NECESSITY_WEIGHT = IMPLEMENTED` | `SCORE_DECOMPOSITION = EXACT` | `WHY_THIS_GOAL = EVIDENCE_BOUND` | `BEGINNER_VIEW_BOUND_TO_SELECTED = VERIFIED` | `FAIL_CLOSED_TESTS = 35/35` | `ROADMAP_COVERAGE_FALSE_NEGATIVE = 0` | `BASELINE_DRIFT = ABSENT` | `NEW_SECRET_FINDINGS = 0`.

## 16. Disclosure trung thực

Claim 174 faculties (NUI) vẫn `PROVENANCE_NOT_RECOVERED / NOT_PROVEN`; multi-host Council `NOT_PROVEN`; planner vẫn governance-side — goal choice trong runtime loop (charter §6) chưa tích hợp, `KNOWN_GAP` không đổi; `RM-Z2P` vẫn BLOCKED (không phải SUPPORTED); C08/OFFLINE_STILL_RESEARCH là `UNKNOWN` provenance — không REJECTED; reconciliation note được ghi công khai trên roadmap + ledger.

## 17. Boundary sản phẩm (không đổi, nhắc lại)

Support: bounded documentation write (isolated, non-production); planner chính tắc governance-side; team-state invariant; second-path prewrite block; FW00–FW06. Condition: live role execution (fresh host probe). Not-proven: production mutation trên project authoritative, multi-host Council, code/db/deploy mutation. Forbidden: "fully autonomous production coding system".

## 18. Phạm vi correction

01A **chỉ** touch: `scripts/p2p_roadmap_planner.py` (v1→v2, SHA `a0e32c45...`), `scripts/p2p_planner_01a_test.py` (mới), `reports/planner/P2P-PLANNER-RUN-02.json` (mới), `governance/research-adoption-ledger.json` (+2 bản ghi), `governance/p2p-development-roadmap.json` (2 mục, ids chuẩn hóa), `docs/p2p-development/capability-ledger/capability-index.json` (1 note), `governance/development-control.json` (+1 provenance). Artifact `.41` byte không đổi; Game Truyện HEAD/tree `b0e6deb5`/`91661a25` không đổi; 0 đột biến GT/GP/Logistics; không public release; không pin upgrade.

## 19. Validation cuối

`scripts/rail_consolidation_validator.py` sau 01A: **`ALL GOVERNANCE CONSOLIDATION CHECKS PASS`** (fail-closed vocabulary); ledger 28 bản ghi (SHIPPED 14 / VERIFIED 5 / PARTIAL 6 / DEFERRED 1 / REJECTED 1 / UNKNOWN 1); roadmap 18 families / 13 items; capabilities 169 (PLANNED 38); `NEW_SECRET_FINDINGS = 0`; `BASELINE_DRIFT = ABSENT`; `DANGLING = 0`.

## 20. Trạng thái terminal

`PROMOTION_PERFORMED = NO (baseline .41 unchanged)` | `PROJECT_AUTO_UPGRADE = NO` | `PRODUCTION_MUTATION_AUTHORIZATION = NO` | `NEW_PROMOTION = NO` | `RUNTIME_MODIFIED = NO` | `COUNCIL_RERUN = NO`.

## 21. Cam kết tuân thủ

Không tự implement mục đầu tiên; không approve goal; không upgrade pin; không public release; không mutation dự án; không rewrite lịch sử C31/C36; không mint `.42`; không rerun Council 8/8.

## 22. Next Owner decision chính xác

> **Approve or reject the corrected planner-recommended next P2P development Goal (RM-PRIORITY-CONTEXT).**

## 23. STOP

Sau khi đọc quyết định Owner trên, dừng mọi phát triển tiếp theo cho đến khi Owner chỉ thị rõ.
