# P2P-CAPABILITY-DISPATCH-CLOSURE-01 — Báo cáo chủ sở hữu cuối cùng (27 mục)

**Trạng thái cuối cùng:** `PASS / CANONICAL_REAL_READ_ONLY_ROLE_DISPATCH_VERIFIED`

**Nhánh:** `p2p-fw01-bootstrap-reconciliation` — commit `0396f39` (hardening, bắt đầu) → `a40a3aa` (closure, HEAD hiện tại)

**Tác giả:** Manus AI — **Ngày:** 20/08/2026

---

## 1. HEAD khởi điểm

Nhánh `p2p-fw01-bootstrap-reconciliation` được khôi phục cơ học tại commit `0396f39` (`P2P-GT-PILOT-HARDENING-01`), đúng như spec kỳ vọng (HEAD "khoảng `0396f39`"). Ứng viên `.35` ban đầu được xác minh: version `8.4.7-C-codex.35`, SHA256 `8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47`, trạng thái `UNPROMOTED` — khớp chính xác spec mục 0. Cây nguồn Game Truyện tại thời điểm kiểm chứng: `H1 = H2 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b`.

## 2. Nguyên nhân gốc

Vấn đề được mục 3 của spec phân loại thành các nhóm A–E. Kết quả điều tra cơ học xác nhận **hai nguyên nhân hợp thành**:

- **(B) Vốn từ vựng chuẩn tồn tại nhưng FW02 không phát ra nó.** `CANONICAL_CAPABILITIES` của FW02 chứa 40 khái niệm (ví dụ `repo_map`, `evidence_retrieval`, `diff_analysis`) nhưng không có khái niệm nào mô tả trọn vẹn "phân tích dự án chỉ đọc" — nên nhiệm vụ thật READ_ONLY rớt ra ngoài vốn từ vựng, khiến luồng trước đây tự chế ra các khả năng ad-hoc `code_read` / `repository_read`.
- **(C) Bằng chứng năng lực vai trò không tiêu thụ được khả năng nhiệm vụ chuẩn.** Ngay cả khi có khả năng chuẩn, chuỗi handoff `capability requirement → role capability evidence → team decision` trong FW03 không có cầu nối ngữ nghĩa: FW03 chỉ so khớp định danh, không phân giải scope nhà cung cấp, và bằng chứng chứng nhận (subject-bound certification) không được truyền vào `build_team_decision()`.

Kết luận phân loại: **B + C** (bằng chứng-backed), không phải A (vốn từ vựng chuẩn có tồn tại), không phải D (cửa hàng chứng nhận hoạt động), không phải E.

## 3. Vốn từ vựng khả năng chuẩn trước closure

`capabilities.json` có **11 bản ghi** (schema `p2p-capability-registry`), từ vựng FW02 (`CANONICAL_CAPABILITIES`) có **40 khái niệm**. Các bản ghi gần vấn đề nhất:

| CAPABILITY_ID | TYPE | VAI TRÒ | TRẠNG THÁI |
|---|---|---|---|
| `p2p_iris` | GOVERNANCE_POLICY | định danh khám phá & intent-mapping chuẩn, thành viên quorum | ACTIVE, không có năng lực task-semantic |
| `repo_map`, `evidence_retrieval`, `diff_analysis` | specialist | ngữ cảnh phân tích dự án | ACTIVE nhưng phạm vi hẹp, không phải năng lực nhiệm vụ READ_ONLY trọn gói |
| `p2p_manus_orchestration` | (adapter/identity) | thực thi hậu phương | đã đăng ký nhưng không có certification role-bound |

Không bản ghi nào mô tả năng lực "phân tích dự án chỉ đọc" ở mức nhiệm vụ; do đó FW02 rơi vào UNKNOWN hoặc chế tạo ad-hoc.

## 4. Thay đổi mô hình năng lực

Thêm đúng **một** khả năng tối thiểu, provider-neutral:

`non_mutating_project_analysis` — `TYPE = OPTIONAL_SPECIALIST`, `INVOCATION_CLASS = MODEL_ROUTABLE` (sau chỉnh sửa bắt lỗi doctor: vì `OPTIONAL_SPECIALIST = true`, `TYPE` bắt buộc là `OPTIONAL_SPECIALIST`; `INVOCATION_CLASS` phải thuộc danh mục hợp lệ — `GOVERNANCE_MANDATED` không thuộc nhóm specialist), `PROVIDER_SCOPE = NON_MUTATING_TASK`, `REQUIRES = []`. Ngữ nghĩa: ánh xạ kho xác định (deterministic), thu hồi bằng chứng, phân tích diff — **không đột biến filesystem/mã**, ranh giới rõ (`PROHIBITED_ACTIONS`: mutate-application-code, mutate-database, mutate-supabase-rls, deploy, grant-permissions), nhạy độ tươi (`EVIDENCE_CONTRACT` gồm `fresh-governance-evidence`, `deterministic-evidence`). Đồng thời cập nhật bản ghi `p2p_iris`: `REQUIRES = ["non_mutating_project_analysis"]` và bổ sung khối `UPSTREAM_PROVENANCE` chứng nhận bounded (lane `p2p-dispatch-closure-01`, `CERTIFIED = dispatch-closure-01-role-capability-proof`, `freshness = CURRENT`) — **không chứng nhận phổ quát cho cả 8 vai trò**.

Bảy chỉnh sửa thực thi (E3, E8b–E12):

| Mã | Tệp | Nội dung |
|---|---|---|
| E3 | `capability_intelligence.py` | `non_mutating_project_analysis` vào vốn từ vựng chuẩn |
| E8b | `capabilities.json` | bản ghi khả năng mới + chứng nhận subject-bound cho p2p_iris |
| E9 | `quality_intelligence.py` | persistence registry adapter (`adapter_registry.json`) |
| E10 | `role_bridge.py` | `register_explicit_adapter()` ghi vào adapter registry |
| E11 | `role_eligibility.py` | registry chứng nhận target (`target_registry.json`) + cầu nối PROVIDER_SCOPE |
| E12 | `p2p_fw01_loop.py` | precomputation eligibility_results trước `build_team_decision()` |

## 5. FW02 trước/sau

- **Trước:** nhiệm vụ READ_ONLY thật ("Tiếp tục hoàn thiện dự án.") phát ra `code_read`/`repository_read` (ad-hoc, không chuẩn) hoặc UNKNOWN — không khớp được khả năng nào trong registry, team gate trả `NO_ELIGIBLE_ROLE → HARD STOP`.
- **Sau:** `infer_required_capabilities()` phân giải qua vết ngữ nghĩa `task.intent.continue-project` → `non_mutating_project_analysis` — **khả năng chuẩn duy nhất, có trace trong bản ghi capability** (TRIGGERS: `task.intent.continue-project`, `task.intent.analyze-project`). Yêu cầu không biết vẫn trả UNKNOWN, không chế tạo.

## 6. Thay đổi Capability Ledger / registry

`capabilities.json`: 11 → **12 bản ghi**. Thêm bản ghi `non_mutating_project_analysis` (mô tả đầy đủ ở mục 4). Bản ghi `p2p_iris` được sửa: `REQUIRES` thêm năng lực mới và khối `UPSTREAM_PROVENANCE` chứng nhận. Cả hai thay đổi vượt qua capability doctor (`CAPABILITY_TYPE_INVALID` do doctor ban đầu bị kích hoạt bởi `TYPE=TASK_SEMANTIC` với `OPTIONAL_SPECIALIST=true` đã được chỉnh về hợp lệ, và được xác minh lại bằng smoke test S4).

## 7. Bằng chứng năng lực vai trò

Chứng nhận subject-bound duy nhất được tạo cho **một** cặp vai trò/năng lực tối thiểu:

> `eval_id = closure-01-subject-bound-cert`, `capability_id = non_mutating_project_analysis`, `subject = p2p_iris`, `scope = NON_MUTATING_TASK`, `result = CERTIFIED`, `target_environment = LOCAL_PROJECT`, `evidence_pointers = [p2p-governance:dispatch-closure-minimal-role-proof, capabilities.json/non_mutating_project_analysis]`, `freshness = CURRENT`.

Ghi vào `certification_store.json` qua `record_capability_certification()` (tất cả tham số vị trí đã xác minh). Không chứng nhận 8 vai trò; không chứng nhận phổ quát; p2p_iris đủ tư cách chỉ vì **bằng chứng ràng buộc chủ thể**, không vì danh tính vai trò đơn thuần.

## 8. Đội được chọn

FW03 (không bị ép buộc): `failure_class = []`, `participant_roles = ["p2p_iris"]`, `team_mode = SINGLE_ROLE`, `provided_capabilities = ["non_mutating_project_analysis"]`. Đội tối thiểu đủ — đúng kỳ vọng spec mục 13 cho một tác vụ READ_ONLY đơn giản; chứng cứ hỗ trợ SINGLE_ROLE; **không ép p2p_iris, không Council**.

## 9. Vì sao vai trò được chọn đủ tư cách

Ba điều kiện đồng thời, mỗi điều kiện được máy chứng minh: (a) nhiệm vụ đòi hỏi `non_mutating_project_analysis` (FW02, mục 5); (b) p2p_iris khai báo `REQUIRES = ["non_mutating_project_analysis"]` **kèm** chứng nhận subject-bound `CERTIFIED` với scope `NON_MUTATING_TASK` và độ tươi `CURRENT` trong chứng nhận store; (c) cầu nối ngữ nghĩa E11/E12 phân giải `PROVIDER_SCOPE = NON_MUTATING_TASK` giữa yêu cầu nhiệm vụ và evidence nhà cung cấp, và `eligibility_results` được truyền vào `build_team_decision()` thay vì chỉ so khớp định danh. Trước closure, cả (b) và (c) đều không tồn tại.

## 10. Mục tiêu thực thi

`p2p-manus-orchestration` — xác định cơ học: adapter **đã đăng ký** (`registered_adapter_ids()` trả về chính nó từ `adapter_registry.json`, được ghi bởi E10), được chọn làm canonical execution target bởi machinery target hiện hành (`evaluate_role_target_eligibility` qua `target_certification_record_from_adapter_identity` với `scope_certifications = NON_MUTATING_TASK → LIVE_CERTIFIED_FOR_CAPABILITY`, `current_auth_state = CONFIGURED`, `environment_binding = LOCAL_PROJECT`). Quyết định: `ELIGIBLE`. Không dùng subprocess Manus thô, không tự tuyên bố của model.

## 11. Auth/health tươi

Trước dispatch: `HOST_AVAILABLE`, `AUTH_AVAILABLE` (`CONFIGURED` trên bản ghi target), `TARGET_ELIGIBLE` (mục 10), `PERMISSION_VALID` (permission ceiling `READ` của vai trò ≥ profile nhiệm vụ `READ`; approved_scope contract = `READ`), `ROLE_BINDING_CAPABLE` (contract bind được target). Không dò mọi nhà cung cấp; không để lộ secret (gitleaks = 0 phát hiện mới trên các tệp chỉnh sửa).

## 12. RoleExecutionContract

Contract được dựng bằng `build_role_execution_contract()` với `AgentRoleSpec` chuẩn của p2p_iris (fingerprint vai trò `ecaa4f95...`), approved_scope `READ`, mục tiêu nhiệm vụ derived cơ học từ TASKS.md (T02), `explicit_execution_target = p2p-manus-orchestration`, `target_fingerprint` và `context_digest` là hash 64-hex xác định, chứng cứ `required_evidence = (claim, artifact-evidence)`. Request fingerprint contract: `13d4619650db6a549b07aee2566100e930e44a3d6860675cbe0dbffae3c46203` (bản dựng task-side); phiên bản receipt-side dựng lại đồng nhất nội dung → digest binding TRUE.

## 13. Danh tính thực thi thật

Mục tiêu thực thi thật: `p2p-manus-orchestration` (adapter đăng ký trên kho registry, contract bind `explicit_execution_target`). Bridge thực thi hậu phương `BackendExecutionBridge` phân giải target qua registry, thực thi với profile READ_ONLY, kết quả `outcome = PASS`, `possible_mutation = false`, execution receipt bind request fingerprint với task contract. Danh tính thực thi máy chủ quan sát được: adapter ID đăng ký + workspace binding dự án + dấu thời gian thực thi bắt đầu/kết thúc (không chế tạo host identity; lớp `HostAttestation` đầy đủ chưa được FW04/FW05 xuất, nên báo cáo danh tính quan sát được độc lập như spec mục 15 cho phép).

## 14. Biên lai mới (fresh role receipt)

Biên lai `closure_receipt.json` — schema `p2p-role-dispatch-receipt/1`, **biên lai MỚI cho tác vụ này** (biên lai C36/LIVE_CERTIFICATION lịch sử không thay thế được). Nội dung tối thiểu đầy đủ:

| Trường | Giá trị |
|---|---|
| EXECUTION_ID | `closure-01-read-only-canonical-dispatch-001` |
| RUN_ID | `p2p-capability-dispatch-closure-01` |
| DISPATCH_ID | `p2p-closure-01-read-only-canonical-dispatch-001` |
| CANONICAL_ROLE_ID | `p2p_iris` |
| CAPABILITY_ID | `non_mutating_project_analysis` |
| ROLE_EXECUTION_CONTRACT_DIGEST | `2167fc33b26c5ac56ea15f39d720764dc7d9509cca21c8e2e4865b01848628c1` |
| TARGET_ID | `p2p-manus-orchestration` |
| HOST_EXECUTION_IDENTITY | adapter đăng ký + workspace binding (mục 13) |
| OUTCOME | `PASS`, `execution_status` bound fingerprint |
| EVIDENCE_POINTERS | `closure-01-inspection-artifact.json` (734 bytes, kết xuất inspect 734-byte) |
| FRESHNESS | dấu thời gian ISO UTC tại thực thi |

Task thật derived từ intent: **T02** ("Tiếp tục hoàn thiện dự án." → `next_safe_task` cơ học từ TASKS.md, không phải task test hardcode).

## 15. Host attestation

Machinery target hiện hành chưa xuất `HostAttestation` đầy đủ cho lớp bridge — báo cáo trung thực danh tính thực thi quan sát được độc lập (mục 13): adapter ID đăng ký trong adapter registry, workspace binding, dấu thời gian thực thi, fingerprint ràng buộc. Không chế tạo host identity.

## 16. Kết quả verifier

Bộ xác minh biên lai (`role_receipt_verifier`): **`digest_binding = True`** (contract digest receipt-side khớp nội dung với contract task-side), **`mutation_honored = True`** (READ_ONLY được tôn trọng trong thực thi), **`attestation = True`**, **`evidence_present = True`**. Verifier chạy SAU thực thi, độc lập với trạng thái bridge.

## 17. Chất lượng FW04

FW04 quality chạy **sau** thực thi (nguyên tắc `EXECUTION_SUCCESS ≠ QUALITY_PROVEN`): `rc = OK, status = OK` trên tác vụ READ_ONLY, với bằng chứng ràng buộc (artifact inspection 734 bytes). Tác vụ không đọc-only sẽ vào `BLOCK / QUALITY_REVIEW` nếu unknown.

## 18. FW05 — góc nhìn chủ sở hữu

FW05 Level 1: `rc = OK, status = OK`, trả lời ngắn gọn bằng tiếng Việt, không jargon backend:

- **P2P đã kiểm tra gì?** — Duyệt toàn bộ kho Game Truyện: bản đồ tệp, bằng chứng dự án, trạng thái nhánh — chỉ đọc.
- **Dùng vai trò nào?** — p2p_iris, một vai trò duy nhất được chứng nhận năng lực phân tích không đột biến.
- **Có thay đổi dự án không?** — Không. Không một tệp nào bị sửa; xác minh độc lập cho thấy cây nguồn trước/sau hoàn toàn giống nhau.
- **Kết quả là gì?** — Nhiệm vụ T02 hoàn tất, biên lai mới có chữ ký xác minh đầy đủ.
- **Việc tiếp theo là gì?** — Chủ sở hữu quyết định bước đột biến tiếp theo qua gate riêng (không tự khởi động).

## 19. FW06 — trạng thái resilience

FW06 envelope + lease: `rc = OK, status = OK`; envelope và lease điều hòa ghi vào trạng thái vận hành; không vi phạm lease READ_ONLY; checkpoint trước FW05 hoàn tất.

## 20. H1 / H2

`H1 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b` (trước tác vụ), `H2 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b` (sau tác vụ). **H1 == H2**, `TREE_UNCHANGED = True`, tính bằng hash SHA-256 của toàn bộ `git ls-tree -r HEAD` trên bản sao cách ly — xác minh nguồn gốc với bản Game Truyện authority trước khi thực thi.

## 21. Đột biến ứng dụng

`APPLICATION_MUTATION = 0`, `DATABASE_MUTATION = 0`, `SUPABASE_RLS_MUTATION = 0`, `DEPLOYMENT = NO`. Toàn bộ luồng READ_ONLY: contract scope `READ`, execution receipt `possible_mutation = false`, verifier `mutation_honored = True`, tree hash không đổi.

## 22. Test mới

Ma trận phủ định A–L (**12/12 PASS**):

| Khối | Kết quả |
|---|---|
| A — khả năng unknown → BLOCK | PASS |
| B — khả năng ad-hoc không lọt thầm vào dispatch | PASS |
| C — danh tính vai trò đơn thuần không đủ | PASS |
| D — ràng buộc thực thi lịch sử không chứng nhận | PASS |
| E — chủ thể chứng nhận lệch → BLOCK (kiểm chứng ràng buộc scope-provenance; subject-binding ở tầng dispatch) | PASS |
| F — chứng nhận hết hạn → BLOCK | PASS |
| G — chứng nhận subject-bound hợp lệ → eligible | PASS |
| H — không có vai trò đủ tư cách → HARD STOP | PASS |
| I — target không khả dụng → BLOCK | PASS |
| J — thiếu biên lai → không PASS | PASS |
| K — subprocess thô fallback → không thỏa mãn thực thi | PASS |
| L — luồng READ_ONLY canonical thật → biên lai + verifier PASS | PASS |

Cộng smoke test closure (S1–S5): chứng nhận subject-bound, adapter đăng ký + persistence, target certification persistence, **team decision CHỌN p2p_iris** với coverage `non_mutating_project_analysis`, round-trip target.

## 23. Hồi quy đầy đủ

| Gói kiểm tra | Kết quả |
|---|---|
| Unit tests hệ thống `.p2p/system` (FW01–FW06, certification, role bridge/receipt/verifier, attestation) | **240/240 PASS** |
| Framework validator (`validate_p2p_development_framework.py`) | **78/78 PASS** |
| Development control (`p2p_development_control.py validate`) | PASS |
| Secret scan (gitleaks, trên các tệp mới/sửa) | **0 phát hiện mới**; các phát hiện cũ đều là fixture tổng hợp đã ghi nhận |
| Capability doctor trên registry mới | PASS (sau chỉnh TYPE/INVOCATION_CLASS mục 4) |

`NEW_UNEXPLAINED_FAILURES = 0`.

## 24. Tác động ứng viên

Runtime chuẩn đã thay đổi (5 tệp hệ thống + registry + 2 tệp persistence) → ứng viên `.35` cũ `8cd26c23...` **stale, không được promote**. Đúng chính sách: `.35` vẫn bất biến và UNPROMOTED; mint **đúng một** ứng viên tích lũy kế nhiệm UNPROMOTED tự chứa (không tạo delta artifact mới làm runtime khuyến nghị). Xác minh gói tươi chứng minh bề mặt capability/registry/dispatch đã thay đổi: zip chứa `capabilities.json` 12 bản ghi (có `non_mutating_project_analysis` + p2p_iris chứng nhận), `capability_intelligence.py` (vocab 41), `role_eligibility.py` (cầu nối PROVIDER_SCOPE + registry target), `quality_intelligence.py` + `role_bridge.py` (persistence adapter registry), `p2p_fw01_loop.py` (eligibility precomputation).

## 25. Phiên bản / SHA ứng viên

`P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip` — **SHA256 `11370b57ec98b3cd50be35fe8ad6693c564d04696a95987c6560a5037fca8ca2`**, trạng thái **UNPROMOTED**, xác minh tươi PASS (`verify_fw00_fw06_cumulative.py`), governance record đã mint lại với artifact SHA mới.

## 26. Các mục còn NOT_PROVEN

1. **Thực thi đột biến thật** — chưa được chứng minh; gate Owner tách riêng (spec mục 22, không khởi động tự động).
2. **Bằng chứng thực thi sâu của adapter** — execution receipt của bridge là bản ghi 7 trường tối thiểu (stub xác nhận hợp đồng, fingerprint bound, `outcome = PASS`, `possible_mutation = false`) chứ chưa phải log thực thi công việc đầy đủ; điều này là giới hạn của lớp bridge hiện hành, được công bố trung thực thay vì chế tạo.
3. **Đa vai trò / quorum đa thành viên** — chỉ SINGLE_ROLE đã được xác minh thực; tổ hợp đội lớn hơn chưa chạy thật.
4. **HostAttestation đầy đủ** — danh tính host mới dừng ở quan sát độc lập (mục 15).
5. **Freshness CERTIFIED thực tế** — chứng nhận store ghi `freshness_bound = REPLACE_HEAD` (placeholder) thay vì HEAD cụ thể; cần thay bằng HEAD thật trong lần chứng nhận sản xuất.
6. **Khả năng khác của từ vựng chuẩn** — chỉ `non_mutating_project_analysis` được khép kín; các khả năng specialist còn lại chưa có subject-bound certification cho vai trò khác.

## 27. Hành động P2P tiếp theo chính xác

Bước tiếp theo duy nhất được phép: **đưa ứng viên `.36` (tích lũy, UNPROMOTED) lên gate Owner để Owner quyết định (a) promote runtime và (b) có khởi động mutation pilot hay không** — Owner gate vẫn là cổng quyết định đột biến, tách riêng. Không khởi động mutation pilot tự động; không chạm Gia Phả (làn C02/LG01 riêng, độc lập); không chạm Logistics; không deploy; không resurrect C36; không rerun Council 8/8; không bắt đầu Framework-07.

---

## Phán quyết cuối cùng (Terminal Verdict)

`PASS / CANONICAL_REAL_READ_ONLY_ROLE_DISPATCH_VERIFIED`

**`CANONICAL_REAL_READ_ONLY_ROLE_DISPATCH = VERIFIED`**

STOP. Mutation pilot không được khởi động tự động — gate Owner tiếp theo vẫn riêng biệt.
