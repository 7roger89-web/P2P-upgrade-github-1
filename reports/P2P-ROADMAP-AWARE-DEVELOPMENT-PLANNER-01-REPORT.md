# P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01 — Báo cáo Owner cuối

**Spec:** P2P-ROADMAP-AWARE-DEVELOPMENT-PLANNER-01 · **Baseline chính thức:** `8.4.7-C-codex.41` (PROMOTED_VERIFIED) · **Ngày:** 2026-08-21 · **Phạm vi:** governance-only — không sửa runtime, không sửa artifact `.41`, không promote mới, không implement các mục roadmap, không mutate dự án.

---

## Mục 1 — Khôi phục chân lý baseline trước khi bắt đầu

Baseline chính thức khôi phục từ `development-control.json`: `8.4.7-C-codex.41`, artifact SHA `da835f8a48caf4536094ffdd82e3c65baa82da32aa9a7ae73714ee1f2e9c3d2d` (recomputed byte-thật, MATCH), promotion `P2P-APR-20260821T035410Z-c41-official-baseline-promotion`, previous baseline `.19` không bị viết lại. Kho `auth-f01` tại HEAD `b9b04ba`, nhánh `p2p-research-roadmap-consolidation-01`, `LOCAL == REMOTE`, working tree sạch trước khi task bắt đầu. `BASELINE_IDENTITY = VERIFIED`.

## Mục 2 — Danh tính planner và vị trí cài đặt

Planner cài đặt tại `scripts/p2p_roadmap_planner.py` (script governance-side, đọc-only, không thay đổi runtime, không nằm trong artifact `.41`). Bộ test tại `scripts/p2p_planner_test.py`. Evidence run tại `reports/planner/P2P-PLANNER-RUN-01.json` (SHA đầu `4096428e...`). Planner là thành phần chính tắc đọc các nguồn canonical **trước khi** chọn Goal — đúng nghĩa "roadmap-aware", không phải orchestrator thứ hai.

## Mục 3 — Tuân thủ quyền lực chính tắc (authority precedence)

Thứ tự được mã hóa trong `AUTHORITY_ORDER` của kết quả run: (1) baseline chính thức / trạng thái lịch sử C-line → `development-control.json`; (2) tổ chức future roadmap item/family → `p2p-development-roadmap.json`; (3) research adoption/provenance → `research-adoption-ledger.json`; (4) capability existence → `capability-index.json`; (5) Owner intent hiện tại → input model; (6) external research → provenance ONLY, không bao giờ là authority. Hai canonical authority xung đột (ví dụ C08: DONE ở dctl nhưng PLANNED ở roadmap.json) bị phát hiện fail-closed (`AUTHORITY CONFLICT` → refuse, test T9 PASS).

## Mục 4 — Input contract đầy đủ

Mọi trường của `PLANNING_INPUT_MODEL` được nạp trực tiếp từ file canonical JSON — không ghi chép tay, không transcription vào prompt. Kiểm chứng bằng `ROADMAP_MANUAL_REENTRY_REQUIRED = NO` (test T14 PASS). Các trường: OFFICIAL_BASELINE, OWNER_CURRENT_INTENT, RESEARCH_ADOPTION_RECORDS, ROADMAP_ITEMS, CAPABILITY_RECORDS, CURRENT_EVIDENCE, DEPENDENCIES, BLOCKERS, STATUS, PRIORITY, OWNER_VALUE, SAFETY_MATURITY, EVIDENCE_GAPS, ARCHITECTURAL_LEVERAGE, PROJECT_IMPACT, MUTATION_RISK/PROMOTION_REQUIREMENT, NOT_PROVEN, DEFER_REASON, AUTHORITY_ORDER, HASHES.

## Mục 5 — Coverage gate (ROADMAP_COVERAGE_GAP)

Gate kiểm tra: mọi hướng được Owner chọn không có durable record → `OWNER_SELECTED_CAPABILITY_RECORD_MISSING`; mọi `source_research_ids` roadmap trỏ đến ledger vắng → `SOURCE_RESEARCH_ID_MISSING_FROM_LEDGER`. Run chính tắc: `ROADMAP_COVERAGE_GAP = FALSE`, 0 gap. Phản ứng test: bỏ record RA-EXT-019 khỏi ledger → gap phát hiện (T5 PASS); Owner override id không tồn tại → gap phát hiện (T16 PASS). `ROADMAP_COVERAGE_FALSE_NEGATIVE = 0`.

## Mục 6 — Đồ thị dependency theo lớp

Phân lớp cơ học từng item với lý do: `DONE_SHIPPED_VERIFIED` / `BLOCKED_BY_DEPENDENCY` / `BLOCKED_BY_EXTERNAL_EVIDENCE` / `OWNER_DEFERRED` / `NOT_YET_SAFE` / `SUPERSEDED` / `UNKNOWN` / `READY_NOW`. Đặc biệt: dependency resolution theo id (alias `C08 ↔ RM-C08`) và truyền trễ — `RM-PRIORITY-LARGE-GOAL` tự động phân lớp `OWNER_DEFERRED` vì phụ thuộc `RM-C08` (explicit Owner deferral); `RM-Z2P` tự động `BLOCKED_BY_DEPENDENCY` vì LARGE-GOAL chưa DONE. Kết quả run chính tắc:

| Lớp | Items |
|---|---|
| READY_NOW | RM-PRIORITY-CONTEXT, RM-PRIORITY-RELEASE-LIFECYCLE, RM-PRIORITY-PLANNER, RM-PRIORITY-DRIFT-SWEEP, RM-PRIORITY-ORCA-EXT, RM-PRIORITY-CODE-MUTATION |
| BLOCKED_BY_DEPENDENCY | RM-PRIORITY-DESIGN (NUI 174-faculty provenance), RM-Z2P (qua LARGE-GOAL) |
| BLOCKED_BY_EXTERNAL_EVIDENCE | RM-PRIORITY-MULTIHOST-COUNCIL (C09/C27 LIVE_HOST_EVIDENCE_UNAVAILABLE) |
| OWNER_DEFERRED | RM-C08, RM-PRIORITY-LARGE-GOAL (lan truyền) |

`DANGLING_DEPENDENCIES = 0` (khớp consolidation validator).

## Mục 7 — Ranking xác định, không hardcoded winner

Công thức `SCORE = 3.0·owner_value_bucket + 1.5·safety_maturity + 1.0·evidence_gap + 1.5·architectural_leverage`, tie-break theo id — xác định tuyệt đối cho truth input giống nhau. Không có item nào được gán trước; winner là kết quả tính toán trên roadmap hiện tại (tất cả items PLANNED; không item nào DONE). Run hai lần cùng truth → ranking giống hệt (T0 PASS); thêm item READY giá trị cao → ranking đổi (T2 PASS); thêm item BLOCKED giá trị cao → recommendation không đổi (T1 PASS).

## Mục 8 — Kết quả thực thi chính tắc trên roadmap hiện tại

| Field | Giá trị |
|---|---|
| STRATEGIC_PRIORITY top-5 | RM-PRIORITY-CONTEXT (14.75), RM-PRIORITY-DESIGN (13.5), RM-Z2P (12.75), RM-PRIORITY-RELEASE-LIFECYCLE (12.0), RM-C09 (8.25) |
| NEXT_EXECUTABLE_GOALS | CONTEXT, RELEASE-LIFECYCLE, PLANNER, DRIFT-SWEEP, ORCA-EXT, CODE-MUTATION |
| RECOMMENDED_NEXT_GOAL | **RM-PRIORITY-CONTEXT** |
| WHY_THIS_GOAL | score cao nhất trong READY_NOW; `mutation_risk_class=READ_ONLY`; `project_impact=NONE`; `promotion_required=NO`; chặn/khai thác các mục giá trị cao hơn phía dưới |
| WHY_NOT_HIGHER | RM-PRIORITY-DESIGN: STRATEGIC #2 nhưng BLOCKED_BY_DEPENDENCY (NUI provenance chưa recovered); RM-Z2P: BLOCKED_BY_DEPENDENCY (LARGE-GOAL chưa DONE) |
| REQUIRED_OWNER_DECISION | `Approve or reject the planner-recommended next P2P development Goal.` |

Trùng khớp với khuyến nghị phân tích cơ học trước đó nhưng **không phải hardcoded** — được chứng minh bằng reactivity tests (thay truth → output đổi đúng hành vi).

## Mục 9 — Beginner-first view

Bản chiếu 7 câu hỏi Owner bằng tiếng Việt, tự động sinh (`beginner_owner_view_vn`): P2P muốn làm gì tiếp (RM-PRIORITY-CONTEXT), tại sao, việc quan trọng hơn nào chưa làm được ngay (DESIGN, MULTIHOST), gì đang bị block, gì Owner đã hoãn (C08), có đụng project/code/data thật không (**KHÔNG**), Owner cần quyết định gì. Test T13 PASS — đủ 7 câu hỏi.

## Mục 10 — Fail-closed đầy đủ

Không bao giờ trả recommendation khi truth không đủ: unknown status → refuse exit 1 (T6 PASS); thiếu capability ledger → refuse (T7 PASS); baseline identity mismatch → refuse (T8 PASS); authority conflict → refuse (T9 PASS). `UNKNOWN_REFERENCE_PASS_OPEN = 0` — không reference nào "im lặng bỏ qua".

## Mục 11 — Hash binding và ROADMAP_DRIFT_INVALIDATES_PLAN

Mỗi plan bind SHA-256 của 4 nguồn canonical + baseline identity + timestamp. Thay đổi byte roadmap → hash plan khác (T10 PASS). Plan cũ không thể sống sót sau drift.

## Mục 12 — PLANNER_SELECTION ≠ GOAL_EXECUTION

Planner chỉ **đề xuất**; không tự thực thi, không tự chạy Goal, không override Owner Gate. `PLANNER_SELECTION_DOES_NOT_AUTO_EXECUTE = true`. Việc "chọn Goal" và việc "thực thi Goal" tách nhau — Owner phải approve từng bước.

## Mục 13 — Không auto-execution attempt

Kiểm chứng cơ học: đo mtime toàn bộ repo trước/sau planner run → `AUTO_EXECUTION_ATTEMPTS = 0` (T11 PASS). Planner không viết bất kỳ file nào của repo trong quá trình đọc.

## Mục 14 — Không đột biến dự án

Planner không chứa đường dẫn hay logic mutate Game Truyện, Gia Phả, Logistics (T12 PASS — kiểm tra source structural, loại trừ câu beginner-view khai báo "không mutate"). Fixture tests chạy trên thư mục tạm hoàn toàn tách biệt với dự án thật. `PROJECT_MUTATION_ATTEMPTS = 0`.

## Mục 15 — Tự áp dụng (self-application)

Planner đọc file JSON canonical trực tiếp — chính nó là minh chứng "chân lý được tiêu thụ trước khi chọn Goal" (spec §21-1). `ROADMAP_MANUAL_REENTRY_REQUIRED = NO`. Không vòng lặp: planner không đọc chính output của nó; nó đọc nguồn governance đã tồn tại.

## Mục 16 — C36 identity preserved

Kiểm tra C36 audit: không roadmap item nào khai báo lại canonical C36; `LIVE_CERTIFICATION_RECORD` (làn riêng, host-binding riêng) giữ nguyên; không đổi tên hay gộp. Test T15 PASS. Lịch sử C31/C36 không được viết lại.

## Mục 17 — Validation đầy đủ (bộ test chính tắc)

`scripts/p2p_planner_test.py`: **18/18 PASS** — T0 ranking xác định; T1–T5 phản ứng A–E; T6–T9 fail-closed (unknown status, missing ledger, baseline mismatch, authority conflict); T10 hash drift; T11 zero auto-execution; T12 no project mutation paths; T13 beginner view completeness; T14 self-application; T15 C36 audit; T16 coverage false-negative = 0; T17 dangling deps = 0. Tất cả fixture disposable tại `/tmp/planner01-fixture-*`, không chạm file chính tắc.

## Mục 18 — Reactivity tests A–H (ánh xạ)

A blocked-high-item-added → recommendation giữ đúng (T1); B ready-high-item-added → ranking đổi (T2); C dependency-blocked → dependent mất executable (T3); D Owner-defer → không tự phản kích hoạt (T4); E omitted-selected-record → coverage gap (T5); F unknown-status → fail-closed (T6); G missing-source → fail-closed (T7); H baseline-drift → hash plan đổi (T10). Đủ ánh xạ A–H yêu cầu spec.

## Mục 19 — Cập nhật durable records

Capability record `ROADMAP_AWARE_DEVELOPMENT_PLANNER_PLANNED` → status **VERIFIED** (evidence refs hash-bound vào 2 script + run evidence; known_gaps khai báo trung thực về scope governance-side). Charter invariant `MACHINE_READABLE_ROADMAP_MACHINE_READABLE_NOT_AUTOMATIC` → `MACHINE_READABLE_ROADMAP_VERIFIED` với mô tả scope. Research ledger RA-EXT-022 (VERIFIED) thêm ghi chú tiêu thụ cơ học. `development-control.json` thêm provenance record `PLANNER-01`. Không mục nào khác bị sửa.

## Mục 20 — Validator chạy lại sau cập nhật

`rail_consolidation_validator.py` sau update: `ALL GOVERNANCE CONSOLIDATION CHECKS PASS` — `DANGLING_DEPENDENCIES=0`, `DUPLICATE_CANONICAL_CAPABILITIES=0`, `ROADMAP_UNKNOWN_REFERENCES=0`, `NEW_SECRET_FINDINGS=0`, `BASELINE_DRIFT=ABSENT`; 26 ledger records, 169 capabilities.

## Mục 21 — Trạng thái terminal goal

`ROADMAP_AWARE_DEVELOPMENT_PLANNER = VERIFIED` — tiêu thụ chân lý roadmap cơ học đã được chứng minh bằng đọc file trực tiếp và 18/18 tests. Không cần candidate/` .42` (planner là governance-side, không thay đổi runtime → không trigger promotion pipeline).

## Mục 22 — Khai báo trung thực NOT_PROVEN / NOT_VERIFIED

Planner là script governance-side; **runtime execution-loop goal choice (charter §6 heuristic) CHƯA tích hợp** với planner — đây là known_gap khai báo trong capability record, không che giấu. Planner không tự chạy định kỳ; mỗi run cần Owner invocation. Không có evidence về hành vi trong "production P2P loop" — chỉ evidence cơ học trên fixture và repo thật.

## Mục 23 — Sản phẩm có được tuyên bố

SUPPORTED: machine-readable canonical roadmap consumption (đọc máy trực tiếp); coverage gate fail-closed; dependency graph cơ học với deferred propagation; deterministic ranking; hash binding; beginner-first VN view; Planner-selection separation; reactivity A–H; no auto-execution; no project mutation. CONDITIONAL: recommendation chỉ hợp lệ khi các nguồn canonical chưa drift (hash-bound kiểm tra).

## Mục 24 — Tuyên bố bị cấm

KHÔNG tuyên bố: "planner tự chạy trong runtime loop", "Goal tiếp theo đã được tự động thực thi", "P2P tự chọn và tự làm Goal", "không cần Owner approval". Khuyến nghị RM-PRIORITY-CONTEXT là **đề xuất**, Owner quyết định.

## Mục 25 — Phạm vi promotion (không áp dụng)

Task này không tạo candidate, không promotion, không thay đổi baseline — baseline `.41` byte không đổi (`BASELINE_DRIFT=ABSENT`). Artifact `.41` không bị sửa.

## Mục 26 — Impact dự án

0 đột biến trên Game Truyện, Gia Phả, Logistics. Không pin upgrade. Không public release. Không production mutation. Các dự án hoàn toàn không được chạm.

## Mục 27 — Disclosure

(1) Planner governance-side, chưa tích hợp runtime execution loop; (2) ranking weights là lựa chọn thiết kế cơ học (xác định nhưng không phải "chân lý duy nhất" — Owner có thể điều chỉnh); (3) owner_value_bucket heuristic từ text durable — không thay thế Owner intent rõ ràng; (4) recommended goal = RM-PRIORITY-CONTEXT chỉ là đề xuất; (5) không re-run Council 8/8 — không yêu cầu bởi spec.

## Mục 28 — Verdict cuối

**`PASS / P2P_ROADMAP_AWARE_DEVELOPMENT_PLANNER_VERIFIED`**

```
ROADMAP_AWARE_DEVELOPMENT_PLANNER = VERIFIED
DETERMINISTIC_RANKING = VERIFIED
FAIL_CLOSED = VERIFIED (UNKNOWN_REFERENCE_PASS_OPEN = 0)
AUTO_EXECUTION_ATTEMPTS = 0
PROJECT_MUTATION_ATTEMPTS = 0
ROADMAP_COVERAGE_FALSE_NEGATIVE = 0
BASELINE_DRIFT = ABSENT
RECOMMENDED_NEXT_GOAL = RM-PRIORITY-CONTEXT (owner-approved pending)
```

**Quyết định Owner chính xác tiếp theo:**

> Approve or reject the planner-recommended next P2P development Goal (RM-PRIORITY-CONTEXT).

Sau đó **STOP** — không tự approve, không tự implement RM-PRIORITY-CONTEXT, không mint `.42`, không rerun Council.
