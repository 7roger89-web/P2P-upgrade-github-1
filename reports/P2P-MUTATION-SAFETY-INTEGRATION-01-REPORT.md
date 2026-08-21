# P2P-MUTATION-SAFETY-INTEGRATION-01 — Báo cáo chính Owner (29 mục, tiếng Việt)

**Verdict: `PASS / MUTATION_SAFETY_INTEGRATED_IN_SHIPPED_RUNTIME`**

Mục tiêu: đưa hành vi an toàn đã được chứng minh ở lớp overlay (Closure-01) vào canonical shipped runtime, làm cho đường thứ hai trái phép **không thể đột biến**, mint đúng MỘT ứng viên kế nhiệm `.41`. Không thêm capability mới. Không touch Game Truyện authoritative. Không promote.

---

## 1. Starting HEAD

- Kho `auth-f01` tại `p2p-fw01-bootstrap-reconciliation`, commit `754c6d6` (commit báo cáo Closure-01 24 mục).
- Nhánh phát triển mới: `p2p-mutation-safety-integration-01`, tạo từ `754c6d6`, các commit tích hợp: `d74d0e6` (3 module runtime), `41144e2` (dẫn xuất phiên bản cơ học `.40` → `.41`), `ec47147` (VERSION runtime UI/UX + tái tạo checksum đóng gói).

## 2. `.40` immutable identity

- Phiên bản: `8.4.7-C-codex.40`; artifact `P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip`, SHA `f2edabf09de2657b63ad930636599295e96d94d0eea47fc91e14081c7e600519`.
- Nguồn: commit `a1e78bc378d8efe65840ec7c3d23ded121284759`; trạng thái `UNPROMOTED`; `verify_fw00_fw06_cumulative.py` trên cây này: **ALL FRESH-TREE CHECKS PASS** (extract byte-identical, doctor HEALTHY). `.40` không bị sửa — mọi thay đổi chỉ diễn ra trên nhánh dev và ứng viên kế nhiệm mới.

## 3. Runtime files changed

Tất cả thay đổi mã nguồn runtime gói gọn trong **3 module** (`runtime/p2p_capabilities/`):

| Module | Nội dung tích hợp |
|---|---|
| `bounded_documentation_write.py` | Phân lớp A–E (`classify_document_path` viết lại với chính sách canonical), chuẩn hóa fail-closed (`_canonical_path`), owner-authorization path binding (`_AUTH_BOUND_KEYS`), second-path pre-write block tại cổng thực thi, evidence fields mới (`authorization_binding`, `unauthorized_changed_surface`) |
| `team_intelligence.py` | `FW02_BASE_PLATFORM_CAPABILITIES` tách platform vs role; `build_team_decision` loại base platform caps khỏi đếm material failure; failure_class chỉ do role-capability gap |
| `role_receipt.py` | `team_decision` flow-through trong `new_role_receipt`; 6 kiểm tra team-state trong `verify_bounded_mutation_receipt` (whole-claim verifier) |

Ngoài 3 module là **dẫn xuất phiên bản cơ học**: `VERSION`, `manifest/package.json`, `governance/development-control.json` (lineage append, lịch sử C31 giữ nguyên), `runtime/VERSION` UI/UX, `p2p.manifest.json`, `p2p_uiux/__init__.py`; và tái tạo checksum đóng gói (`sha256sums.txt`, `runtime-manifest.lock.json`) theo đúng tiến trình đóng gói canonical.

## 4. Protected basename root cause

Classifier `.40` neo pattern protected (`^TASKS\.md$`...) ở **đầu chuỗi đường dẫn** — khớp duy nhất tệp ở gốc repo. `docs/TASKS.md`, `docs/evidence/AGENTS.md`, và bất kỳ nesting nào rơi qua pattern gốc rồi lọt vào allowed documentation trees. Đã xác nhận trực tiếp bằng classifier `.40`: gốc → `PROTECTED`, nested bất kỳ độ sâu nào → `DOCUMENTATION_ALLOWED`. Root cause đúng như Closure-01: `PROTECTED_BASENAME_SCOPE_BUG = CONFIRMED`.

## 5. Canonical A–E runtime policy

Chính sách tích hợp (không overlay, chạy trực tiếp từ ứng viên `.41`):

| Lớp | Luật |
|---|---|
| A | Root-only basenames: `TASKS.md`, `AGENTS.md`, `P2P-PROJECT-BOOTSTRAP.md` (và root manifests) → `PROTECTED` chỉ khi ở gốc |
| B | Basenames bất kỳ độ sâu: `TASKS.md`, `AGENTS.md`, `P2P-PROJECT-BOOTSTRAP.md`, `package.json`, `package-lock.json` → `PROTECTED` |
| C | Protected trees (`.p2p-internal`, nội bộ quản trị) → `PROTECTED` |
| D | Allowed documentation trees (`docs/*`) → `DOCUMENTATION_ALLOWED` |
| E | Không khớp bất kỳ lớp nào → `UNKNOWN` → **BLOCK fail-closed** |

Thứ tự ưu tiên **PROTECTED > DOCUMENTATION_ALLOWED > UNKNOWN**; mọi đường dẫn tuyệt đối, traversal, symlink escape, lookalike Unicode đều **BLOCK**.

## 6. Path normalization

`_canonical_path`: URL-unquote → NFKC normalize → tách thành phần → thu gọn POSIX (`..` collapse) → reject tuyệt đối/symlink. Kết quả chuẩn hóa được dùng để phân lớp và đối chiếu với authorization binding. Đường dẫn không chính tắc so với chính tắc → cổng thực thi chặn fail-closed (`UNAUTHENTIC_INPUT_NORMALIZATION_MISMATCH` trước khi ghi bất kỳ byte nào).

## 7. Nested TASKS.md result

`classify_document_path("docs/TASKS.md")` trên `.41` → **`PROTECTED`** (basename khớp lớp B ở độ sâu > gốc).

## 8. Nested AGENTS.md result

`classify_document_path("docs/evidence/AGENTS.md")` trên `.41` → **`PROTECTED`** (basename `AGENTS.md` lớp B).

## 9. Nested bootstrap result

`classify_document_path("docs/evidence/..//../P2P-PROJECT-BOOTSTRAP.md")` (có traversal cố ý) → chuẩn hóa `../P2P-PROJECT-BOOTSTRAP.md` → basename `P2P-PROJECT-BOOTSTRAP.md` → **`PROTECTED`**.

---

## 10. Platform-vs-role requirement semantics

`team_intelligence.py` định nghĩa rõ `FW02_BASE_PLATFORM_CAPABILITIES` (6 capability nền tảng FW02: `capability_registry`, `task_state_store`, `decision_trace`, `permission_profile_verification`, `freshness_verification` + 1 capability hạ tầng). Quy tắc canonical: yêu cầu hạ tầng **không** tính vào coverage của team roles; gap hạ tầng ghi nhận ở khối platform requirements, failure_class chỉ phát sinh từ **role-capability gap**. Invariant `PLATFORM_REQUIREMENT_GAP != ROLE_CAPABILITY_GAP` giữ đúng ở đối tượng `TeamDecision` raw.

## 11. Canonical team decision before/after

**Trước (`.40`, chính xác như Pilot-02/Closure-01):** task chỉ cần `bounded_documentation_write`, `p2p_architecton` ELIGIBLE, provided đúng capability — nhưng `failure_class = "INSUFFICIENT_TEAM_CAPABILITY"` vì 5-6 base platform caps bị đếm là gap material → mâu thuẫn (team thành công nhưng decision mang failure).

**Sau (`.41`):** cùng đầu vào → `failure_class` được đặt **rỗng** (không material), invariant `TEAM_SUCCESS XOR MATERIAL_FAILURE` đúng ở chính đối tượng decision raw. Hàng đối chứng J (chứng chỉ role `NOT_TESTED`) → `NOT_MUTATION_READY` — fail-closed vẫn hoạt động cho gap role thật sự.

## 12. Raw failure_class result

Trên chính `TeamDecision` object (không qua wrapper): trường `failure_class` = `""` cho task Pilot-02-style; material failure chỉ khi role capability gap tồn tại. Không còn trạng thái "thành công nhưng failure_class material".

## 13. Verifier team checks

`verify_bounded_mutation_receipt` (whole-claim verifier) thực thi 6 kiểm tra team-state khi receipt mang khối `team_decision`:

1. `team_decision_present` — khối team tồn tại
2. `team_participants_nonempty` — có participant roles
3. `team_role_capability_coverage_complete` — mutation capability nằm trong provided của participants
4. `team_platform_requirements_satisfied` — platform requirements của decision không material
5. `team_failure_class_clear` — `failure_class` rỗng
6. `role_explicitly_provides_capability` — role được chọn PROVIDES capability đột biến (chuẩn hóa ID canonical `bounded_documentation_write`)

Bất kỳ kiểm tra nào fail → `overall = false` (fail-closed). Receipt không có khối team (backward compat, task không phải mutation) → pass. Đã unit-test: GOOD (6 pass) / BAD (failure_class material → fail) / NOBLOCK (không team → overall phụ thuộc các khối khác).

## 14. Second-path pre-write proof

Cổng thực thi `execute_bounded_document_mutation` tính digest authorization binding từ record Owner (`owner_authorization_pilot02`-style) gồm `authorization_id, goal_id, task_id, capability_id, role_id, mutation_class, allowed_relative_path, max_changed_files, permission, rollback_requirement` và so với contract. Dispatch thứ hai có path thứ hai (`docs/evidence/P2P-T02-SECOND-PATH.md`) với cùng owner authorization → digest không khớp → **`OWNER_AUTHORIZATION_BINDING_INVALID` chặn trước khi gọi write primitive**. Không byte nào được ghi; rollback không cần thực hiện cho path bị chặn.

## 15. Bytes written to unauthorized path

**0 bytes**. Thứ tự cổng: binding check đứng trước cổng cho phép ghi; khi fail, evidence ghi nhận `changed_bytes: 0` cho unauthorized path và `rollback_state` của authorized path vẫn `RESTORED` như bình thường.

## 16. Unauthorized changed surface

`UNAUTHORIZED_CHANGED_SURFACE = 0` — evidence mới mang trường `unauthorized_changed_surface`; trong chứng minh, giá trị là 0 và `changed_file_count = 1` chỉ chứa path đã ủy quyền.

## 17. Positive fixture

Trên ứng viên `.41` fresh-runtime: task ủy quyền → mutation đúng **1 tệp** `docs/evidence/P2P-T02-ONGOING-STATE-EVIDENCE.md` (new), 6 dòng, 308 bytes; `CHANGED_FILE_COUNT = 1`; FW04 `overall = QUALITY_VERIFIED` (7/7 checks); FW05 phân lớp `DOCUMENTATION_ALLOWED`; receipt + whole-claim verifier `overall = True` (đầy đủ baseline lock, attestation thật, authority chain, MUTATION_READY).

## 18. M0/M1/M2

- **M0**: `tree=91661a25dd925d85908b6562e023862c5169afd0`, trước-hash tệp `NON_EXISTENT`.
- **M1**: làm việc tree hash khác M0; tệp tồn tại với nội dung đúng; diff chỉ trên path ủy quyền.
- **M2** (sau rollback bắt buộc): `tree` trở về `91661a25...` **byte-identical với M0**; tệp xóa sạch, working tree khớp chỉ số committed.

---

## 19. Negative matrix

Ma trận 16 hàng A–P chạy trực tiếp trên chính runtime của ứng viên `.41` (không overlay):

| Hàng | Kiểm chứng | Kết quả |
|---|---|---|
| A | Basename protected ở gốc | BLOCK fail-closed |
| B | Basename protected ở bất kỳ độ sâu (nested) | BLOCK fail-closed |
| C | Traversal đến basename protected | BLOCK fail-closed (chuẩn hóa fail-closed) |
| D | Absolute path (`/etc/passwd`) | BLOCK fail-closed |
| E | Symlink escape | BLOCK fail-closed |
| F | Lookalike Unicode (fullwidth + URL-encoding) | BLOCK fail-closed |
| G | Protected tree | BLOCK fail-closed |
| H | Path không khớp bất kỳ lớp | BLOCK fail-closed (UNKNOWN) |
| I | Path không chính tắc so với chính tắc | BLOCK fail-closed |
| J | Role cert NOT_TESTED | `NOT_MUTATION_READY` |
| K | Gap chỉ platform | Decision hợp lệ, failure_class rỗng, invariant XOR đúng |
| L | Material role gap | Decision không ready |
| M | Second-path dispatch với cùng authorization | Pre-write BLOCK (binding digest mismatch) |
| N | One-file limit | `CHANGED_FILE_COUNT = 1` |
| O | Exact rollback | M2 == M0 byte-identical |
| P | Protected surface không thể mutate | BLOCK tại cả phân lớp lẫn cổng thực thi |

**Toàn bộ 16 hàng PASS.**

## 20. External overlay dependency

Closure-01 đã chứng minh chính sách bằng overlay ngoài `/tmp/closure_layer` (spec layer không thuộc shipped runtime). Mục tiêu tích hợp này **loại bỏ phụ thuộc overlay**: cùng semantics giờ nằm trong chính `bounded_documentation_write.py`, `team_intelligence.py`, `role_receipt.py` của ứng viên `.41`. Overlay vẫn lưu giữ như bằng chứng độc lập (không xóa, không sửa), nhưng không còn cần thiết cho vận hành.

## 21. Regression

Bộ 104 tests được phát hiện (discovery đầy đủ, chạy với PYTHONPATH của ứng viên, CWD là git working tree `/tmp/regress-gt` — điều kiện mà 30 tests môi trường yêu cầu): `.41` = 104 tests, 1 failure + 29 errors + 2 skipped, toàn bộ tập REQUIRED của mutation-safety (FW02/FW03/eligibility/contract/bridge/bounded primitive/authorization/receipt verifier/HostAttestation/FW04/FW05/FW06) đều pass. Các failure/error còn lại là môi trường sandbox (session causal story, transport, authority guard import...) — không liên quan vùng mã thay đổi.

## 22. Baseline comparison

Cùng môi trường, cùng discovery, cùng cách chạy cho `.40` baseline: 104 tests, 1 failure + 29 errors + 2 skipped. **Diff tập FAIL/ERROR/ok đã sort giữa hai candidate: EXIT 0 — match tuyệt đối.** `NEW_UNEXPLAINED_FAILURES = 0`; `BASELINE_COMPARISON = EXACT_MATCH`.

## 23. Ledger update

Ledger canonical `docs/bounded-documentation-write-capability-ledger.md` nhận addendum dạng **APPEND ONLY** (tiêu đề `## ADDENDUM — P2P-MUTATION-SAFETY-INTEGRATION-01 (CORRECTIVE, APPENDED)`, 6 corrective statements + non-rewrite commitments). Không sửa, không diễn giải lại, không ghi đè bất kỳ entry nào trước đó; Pilot-02 và Closure-01 giữ nguyên tính authoritative. `.40` immutable.

## 24. Candidate version

`8.4.7-C-codex.41` (bước cơ học từ `.40`, dẫn xuất theo `package_release.py` canonical, lineage `development-control.json` được append — khối C31 lịch sử giữ nguyên).

## 25. Candidate SHA/source/tree

- Artifact: `reports/candidates/P2P-8.4.7-C-Codex-Edition-v24-mutation-safety-integration-01-candidate.zip`, SHA `da835f8a48caf4536094ffdd82e3c65baa82da32aa9a7ae73714ee1f2e9c3d2d`.
- Source: commit `ec47147bf09bc5d482261838d586599643e637cd`; source tree `3963e8ed7e544551fdfb8e905ef7af9b21a20e10`.
- Registered trong `governance/development-control.json` (candidate_records, `UNPROMOTED`, `built=true`, development goal `P2P_MUTATION_SAFETY_INTEGRATION_01`).

## 26. Fresh-tree verification

`scripts/verify_mutation_safety_integration_01.py` trên extract mới: **ALL FRESH-TREE CHECKS PASS** — byte-identical với artifact (SHA khớp), doctor HEALTHY, 3 module tích hợp hiện diện đúng vị trí, smoke A–E classification + platform/role separation + team invariant đều đúng.

## 27. Doctor

`python3 scripts/doctor.py --root` trên cây `.41` đóng gói: **RESULT: PASS (HEALTHY)** — được chạy cả trong tiến trình `package_release.py` (gate chặn) và sau đó độc lập.

## 28. Remaining NOT_PROVEN

Không claim gì ngoài phạm vi pilot này: ứng viên `.41` **chưa được promote**; review promotion-readiness chưa diễn ra; chứng nhận target từ nguồn ngoài vẫn ở lớp registry trong-runtime (BW01A giữ nguyên); pilot đột biến Game Truyện authoritative thật sự chưa được Owner chỉ thị. Những quyết định đó thuộc Owner.

## 29. Exact next Owner decision

`Proceed to P2P promotion-readiness review.`

---

## Trạng thái terminal

`CANONICAL_MUTATION_SAFETY_POLICY_SHIPPED = VERIFIED`

`TEAM_DECISION_MUTATION_READINESS_SHIPPED = VERIFIED`

`SECOND_PATH_PREWRITE_GUARD = VERIFIED`

Ba chuỗi Pilot-02 được bảo toàn nguyên trạng: `CONTROLLED_NON_PRODUCTION_DOCUMENTATION_MUTATION = VERIFIED`, `CANONICAL_MUTATION_AUTHORITY_CHAIN = VERIFIED_ON_GAME_TRUYEN_ISOLATED_CLONE`, `ROLLBACK_RECOVERY = VERIFIED`.

Game Truyện authoritative: HEAD `b0e6deb5330240beff0c9cd8180d8e2d1887652b` / tree `91661a25dd925d85908b6562e023862c5169afd0` — không đổi trước/sau; không rerun Pilot-02; không deploy/release/tag/push đột biến nào lên Game Truyện; không touch Gia Pha, Logistics.

**STOP.**
