# P2P-340-P1-SKILL-ECONOMY — Báo cáo thử nghiệm & sửa lỗi (Issue #62 / Big Goal #340)

- **Task**: P2P-340-P1-SKILL-ECONOMY (tracking #62, big goal #340)
- **Base main**: `3434f2e702913d5bc08cd61a94b14038f16e2553`
- **Branch**: `arena/c40ab006-p2p-upgrade-github-1`
- **Ngày**: 2026-10-09
- **Machine evidence**: `evidence/p2p-340-p1-skill-economy-01-experiment.json`
- **Effectiveness claim**: `PILOT_ONLY` / `CONSUMPTION_ONLY` — xem mục 5.

## 1. Tóm tắt bằng lời thường (RULE 21)

Hệ thống chọn skill và Skill Consumption Wire hoạt động đúng: skill chỉ được load khi
được chọn, micro-task không tốn thêm byte skill nào, handoff fail-closed khi skill yêu cầu
không tồn tại. Một skill thật (`p2p-eval`) đã được dùng và có receipt hợp lệ khớp hash mà
Owner giao (đã tự kiểm chứng, không kế thừa receipt). Tuy nhiên mình phát hiện một lỗi
thật: metadata hash của một vendor skill trong registry bị stale khiến skill đó không
load được (fail-closed `VENDOR_SNAPSHOT_HASH_MISMATCH`) và làm hỏng 2 bộ test trên
fresh clone. Đã sửa tối thiểu (6 dòng metadata + 7 giá trị hardcode trong test), thêm
1 test hồi quy trọng tâm, có draft PR. Không có bằng chứng đo được rằng skill làm tăng
chất lượng đầu ra (thiếu môi trường chạy nhiều trial cô lập) nên báo trung thực
`PILOT_ONLY`, không bịa số.

## 2. Xác minh nguồn skill (không kế thừa receipt của người giao)

- Owner giao `SELECTED_REPO_SKILL=p2p-eval`, `SKILL_SHA256=c9bdea75...858f64`.
- Tự tính: `sha256(.agents/skills/p2p-eval/SKILL.md)` = `c9bdea750d2fa389a9ef0c9767cbaa245c5275462a3b5a8846afa3f52d858f64` → **khớp**.
- Đọc và áp dụng skill `p2p-eval` (`.agents/skills/p2p-eval/SKILL.md`) cho phần thử nghiệm:
  schema v2, ≥2 trial cô lập mỗi variant, không bịa số liệu. Môi trường Arena một phiên
  duy nhất không thể chạy 2 trial cô lập cùng model cho mỗi variant → không đủ điều kiện
  chứng nhận hiệu quả đầy đủ → báo `PILOT_ONLY` (theo đúng hướng dẫn của skill và đề bài).

## 3. Đã thử gì (thử nghiệm có giới hạn)

### E1 — Ma trận chọn skill theo loại task (đúng ma trận A–E của #62)
Chạy `prepare_skill_handoff`/`select_skills_for_task` thật trên repo, mỗi task chạy 2 tay:
tay có selector và tay ép `NO_MATCH` (không skill). Số liệu trong JSON evidence.

| Task | Kết quả có selector | Skill được chọn | Skill bytes | Tay không skill | Nhận xét |
|---|---|---|---|---|---|
| A: sửa typo nhỏ | `NO_MATCH` | — | **0 B** | `NO_MATCH`, 0 B | Lazy loading đúng: micro-task không load skill |
| B: viết hàm nhỏ + test | `NO_MATCH` | — | **0 B** | 0 B | `coder` là repo-native → chỉ explicit (`@coder` mới chọn được, 16,369 B, hash khớp) |
| C: sửa plan hiện có | `NO_MATCH` | — | **0 B** | 0 B | `planner` là repo-native, explicit-only |
| D: lập kế hoạch module mới | `PASS` | `p2p-uiux` | 9,497 B | 0 B | Chọn 1 skill duy nhất, hash khớp disk; chưa phải `p2p-scope` (thiếu từ ngữ "goal/checkpoint") |
| E: refactor kiến trúc lớn | `NO_MATCH` | — | **0 B** | 0 B | `System-Architect` là repo-native explicit-only; auto-select an toàn (không preload) |
| D2: goal lớn tiếng Việt | `PASS` | `p2p-uiux` | 9,497 B | 0 B | Như trên |
| E-en: refactor (English) | `NO_MATCH` | — | 0 B | 0 B | Như trên |
| B + `@coder` (explicit) | `PASS` | `coder` | 16,369 B | — | Repo-native skill qua đúng 1 wire, hash khớp disk |

- Mọi hash trong handoff đều được kiểm chứng lại độc lập với file trên disk: **đều khớp**.
- `PERMISSION_WIDENED=NO`, `SINGLE_ROUTER_REUSED=YES` ở mọi tay.
- Quan sát (không phải bug): với task nhỏ/vừa, selector tự động thường trả `NO_MATCH`
  vì các skill repo-native (`coder`, `planner`, `System-Architect`) chỉ explicit-invocation.
  Đây là đúng thiết kế "AVAILABLE != LOADED != SELECTED", nhưng là điểm cần Owner biết:
  muốn dùng các skill đó phải gọi tên (`@coder`), trình viết prompt phải serialize đúng.

### E2 — Tiêu thụ skill thật end-to-end (skill `p2p-eval` do Owner chọn)
- `prepare_skill_handoff(host=ARENA, required_skills=["p2p-eval"])` → `SKILL_CHECK=PASS`,
  đường dẫn `.agents/skills/p2p-eval/SKILL.md`, frozen hash khớp disk và khớp hash Owner giao.
- Receipt `p2p-skill-consumption-receipt/1` do executor trả → `validate_consumption_receipt`
  → **valid**. Receipt giả mạo (`CONSUMED_BUT_UNVERIFIED`) → **invalid** (`SKILL_NOT_CONSUMED`).
- `assess_skill_effectiveness` (Quality Intelligence) với evidence tiêu thụ nhưng **không có
  baseline so sánh** → `CONSUMPTION_ONLY`, `effectiveness_claim_supported=false`,
  note `SKILL_CONSUMED != SKILL_EFFECTIVE`. → Hệ thống không tự nhận mình "skill hiệu quả"
  khi chưa có bằng chứng so sánh. Đúng chuẩn.

### E3 — Tấn công / fail-closed (adversarial)
- `required_skills=["skill-khong-ton-tai-xyz"]` → `BLOCKED`, `REQUIRED_SKILL_NOT_FOUND`,
  không load body skill nào.
- 4 required skills → `BLOCKED`, `REQUIRED_SKILL_SET_LIMIT_EXCEEDED` (đúng MAX=3).
- Host không hỗ trợ (`MANUS`) → `BLOCKED`, `HOST_NOT_SUPPORTED_V1`.

### E4 — Thử nghiệm A/B dùng/không dùng skill trên CÙNG một task (có giới hạn)
Task thật: "viết test hồi quy trọng tâm bảo vệ lỗi stale vendor snapshot hash".
- **Tay không skill** (arm 1): viết test trực tiếp, 0 byte skill. Kết quả: test viết một lần
  là đúng — FAIL đúng chỗ trước khi sửa (chứng minh nó bảo vệ bug), PASS sau khi sửa.
  Số lần sửa lại: 0.
- **Tay có skill** (arm 2): dùng wire chọn `@coder` (16,369 B, hash khớp), đọc và đối chiếu
  sản phẩm với rule của skill (surgical fix, test trước/sau fix, cập nhật stale test cùng
  batch, log vào `.tmp/`). Kết quả: sản phẩm đã tuân thủ, không cần sửa thêm.
- **Chất lượng đầu ra**: cả hai tay đều đạt (test pass, guard đúng). **Khác biệt đo được
  duy nhất là chi phí context**: 0 B vs 16,369 B và thời gian đọc/áp dụng skill.
- Trung thực: đây là pilot một phiên duy nhất (cùng model, tuần tự, có thể có hiệu ứng
  thứ tự) → **PILOT_ONLY**, không khẳng định skill làm tăng chất lượng đầu ra.
- Token/chi phí/quota: host Arena không expose số liệu này → **UNKNOWN** (không bịa).

## 4. Lỗi thật phát hiện được và sửa tối thiểu

**Lỗi**: `visual.gpt_image_2_style_library` (DISCOVERED vendor skill) có snapshot trong
repo **byte-identical với upstream** `freestylefly/awesome-gpt-image-2` tại commit pin
`9a7b2e9c39f816d6c699c2a133e11b6d8bfdc464` (đã tải tarball từ codeload.github.com và tự
hash lại từng file: SKILL.md, agents/openai.yaml, references/style-library.md, LICENSE
khớp upstream; `docs/disclaimer.md` chỉ khác CRLF→LF do bước vendor). Nhưng trong
`capabilities.json`, `snapshot_sha256` và `source_files[].sha256` bị stale (5/5 file),
trong khi `canonical_sha256` và `entrypoint_sha256` lại đúng. Hậu quả:
`load_vendor_skill` fail-closed `VENDOR_SNAPSHOT_HASH_MISMATCH` → skill trong kho không
thể tiêu thụ, và 2 bộ test bị ERROR trên fresh clone.

**Sửa tối thiểu** (đúng 6 dòng metadata + 7 giá trị test hardcode + 1 test mới):
1. `.p2p/system/p2p_capabilities/capabilities.json` — `snapshot_sha256` →
   `de9598c1e2a06a3de14b405d28abcb496e058d34d4e876342ad22f8f50761ecb` (tree hash thật),
   5 `source_files[].sha256` → đúng bằng `canonical_sha256` đã được ghi nhận sẵn.
2. `tests/test_p2p_visual_vendor_integration.py` — `EXPECTED_SNAPSHOT_HASH` và
   `EXPECTED_SOURCE_HASHES` (6 giá trị stale) → giá trị thật.
3. `tests/test_p2p_host_skill_projection.py` — `EXPECTED_VENDOR_HASHES` (1 giá trị) → giá trị thật.
4. Test trọng tâm mới `tests/test_p2p_vendor_snapshot_integrity.py` (4 test): mọi vendor
   skill có khai báo per-file snapshot phải khớp tree hash + `sha256 == canonical_sha256`
   == byte thật; load được qua `load_vendor_skill`; entrypoint khớp hash khai báo; và
   snapshot bị can thiệp phải fail-closed (test trong thư mục tạm cô lập).

Không đụng vào `capability_intelligence.py` (PR #339 đang mở). Không tạo router/registry/DB mới.

## 5. Có cải thiện không? (trung thực)

- **Hệ thống tiêu thụ skill**: CÓ cải thiện sau sửa — một skill từ khoang (stockroom) trước
  không load được giờ load được, fail-closed vẫn giữ nguyên khi hash thật sự lệch.
- **Hiệu quả của việc dùng skill (`p2p-eval`, `@coder`)**: **PILOT_ONLY / INCONCLUSIVE**.
  Bằng chứng tiêu thụ (consumption) đầy đủ: handoff PASS, hash khớp, receipt hợp lệ.
  Nhưng không có cặp baseline/assisted cô lập (cần ≥2 trial mỗi variant, cùng model/surface,
  theo đúng `p2p-eval`) nên không khẳng định skill làm tăng chất lượng. Quality Intelligence
  cũng tự trả `CONSUMPTION_ONLY` — nhất quán.
- **Chi phí**: micro-task tốn thêm 0 B nhờ lazy loading (đo được). Task D tốn 9,497 B cho
  1 skill duy nhất. Token/quota: UNKNOWN (host không expose).

## 6. Kiểm thử (trước → sau)

| Suite | Trước (main sạch) | Sau sửa |
|---|---|---|
| `tests.test_p2p_skill_consumption_wire` (51) | OK | **OK** |
| `tests.test_p2p_vendor_snapshot_integrity` (mới, 4) | — (mới viết) | **OK** (trước sửa: FAIL/ERROR đúng chỗ → chứng minh guard) |
| `tests.test_p2p_host_skill_projection` (30) | ERROR setUpClass (hash mismatch) | 29/30 OK; còn 1 FAIL `test_25` (xem mục 7) |
| `tests.test_p2p_manus_skill_package` (8) | ERROR setUpClass | 7/8 OK; còn 1 FAIL `test_03` (xem mục 7) |
| `tests.test_p2p_vendor_skill_integration` (23) | 1 FAIL `test_15` | **OK** |
| `tests.test_p2p_visual_vendor_integration` (10) | 5 FAIL + 3 ERROR | 4 FAIL còn lại (mục 7); các test hash (`test_03/04/09/10`) đã xanh |
| `tests.test_p2p_game_asset_forge_01` (9) | OK | **OK** |
| CI slice: `test_capability_intelligence.py` (26) | OK | **OK** |
| CI slice: `test_quality_intelligence.py` (44) | OK | **OK** |
| CI slice: `test_aerg*.py` (32) | OK | **OK** |

## 7. Tồn đọng / blocker (KHÔNG sửa trong PR này — đã có owner riêng)

1. **Stale structural assertions (issue #277)**: `capability_count 65 != 80`
   (`test_p2p_visual_vendor_integration.test_01`, `test_p2p_game_toolchain_02a.test_02`);
   routing matrix cũ (`test_05` 3 case — router đã chọn thêm `ui.game_hud`/`ui.motion`);
   `test_p2p_game_toolchain_02a.test_01` cần commit `1b456fe9` (sandbox lịch sử git
   đã squash nên fail — environmental). Big goal #340 P0 đã định hướng: test-only repair, PR riêng.
2. **Cùng bug class (stale tree hash) ở vendor skill khác**: 10 skill `game.mengto.*` và
   `game.majid.threejs_qa_release` có `snapshot_sha256` không khớp tree thật
   (`load_vendor_skill` fail-closed; `test_p2p_game_toolchain_02a.test_03` FAIL).
   Chưa được verify với upstream từng file như đã làm cho visual skill → cần điều tra riêng,
   không thể copy đáp án.
3. **Unmasked stale tests**: `test_p2p_host_skill_projection.test_25` và
   `test_p2p_manus_skill_package.test_03` trước đây ẩn sau setUpClass ERROR; giờ hiện ra:
   kỳ vọng READY khi deep-load script **chưa khai báo** (`assets/compose_canvas.js` không có
   trong `script_entrypoints`), trong khi runtime đúng là `BLOCKED/CONTEXT_EXPANSION_UNAUTHORIZED`.
   Test đặc tả cũ, cần #277 hoặc workstream host-projection.
4. **`tests.test_p2p_project_eval.test_current_suite_has_real_recorded_trial_pairs`** cần
   `.p2p/evals/suite.json` (đang gitignore) → ERROR trên fresh clone. Có thể cần skip-guard
   hoặc chạy sau `p2p_eval.py init`; đề xuất riêng.
5. **Môi trường**: `scripts/p2p_development_control.py validate` báo
   `AUTHORITY_ANCHOR_COMMIT_MISSING` và C43 validator có 6 FAIL — đều pre-existing trên main
   sạch (đã stash kiểm chứng), do lịch sử git squash + thiếu `jsonschema` + drift ledger thuộc
   workstream khác.

## 8. Bước tiếp theo

1. Owner/Supervisor review draft PR (exact-head test, focused suite như mục 6).
2. Mở issue riêng (hoặc dùng #277) cho: stale count/routing assertions, mengto/majid stale
   tree hashes (cần verify upstream), unmasked deep-load tests, skip-guard cho eval suite test.
3. Nếu muốn chứng nhận hiệu quả skill đầy đủ: chạy `p2p_eval.py init/design` rồi ít nhất
   2 trial cô lập mỗi variant cho ≥5 case theo schema v2 — cần môi trường có thể lặp trial
   (ngân sách/host phù hợp), hiện tại PILOT_ONLY.

## 9. ReturnPacket

```text
TASK=P2P-340-P1-SKILL-ECONOMY
SKILL_CHECK=PASS (p2p-eval, sha256 c9bdea75...858f64, tự verify khớp disk & khớp Owner)
SKILL_CONSUMPTION=CONSUMED (receipt p2p-skill-consumption-receipt/1 hợp lệ; tamper receipt bị từ chối)
EFFECTIVENESS=PILOT_ONLY (CONSUMPTION_ONLY — thiếu baseline trial cô lập; không bịa số)
E1: micro-task 0 B skill; D chọn đúng 1 skill (9,497 B); repo-native skill chỉ qua @explicit
E3: fail-closed đúng (unknown required / >3 required / unsupported host)
BUG_FOUND=YES — stale snapshot_sha256 + source_files[].sha256 của visual.gpt_image_2_style_library
FIX=MINIMAL (6 dòng capabilities.json + 7 giá trị test + 1 test file mới 4 test)
TESTS: wire 51 OK; vendor_skill_integration 23 OK; CI slice (capability/quality/aerg) OK;
      host_skill_projection 29/30; manus 7/8; visual_vendor 6/10 (còn stale assertions #277)
PRE_EXISTING_NOT_FIXED: #277 stale count/routing, mengto/majid stale tree hash,
      2 unmasked deep-load tests, eval suite.json gitignored, env git-history/jsonschema
PR=DRAFT (xem link ở commit) — KHÔNG merge/deploy
BLOCKER=chờ review; chứng nhận hiệu quả đầy đủ cần môi trường chạy nhiều trial cô lập
NEXT=xem mục 8
```
