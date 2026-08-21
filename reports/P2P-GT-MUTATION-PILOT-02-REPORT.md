# P2P-GT-MUTATION-PILOT-02 — Báo cáo Chủ sở hữu (34 mục)

**Phiên:** P2P-GT-MUTATION-PILOT-02 — Pilot đột biến tài liệu có giới hạn, một lần, trên clone Game Truyện biệt lập, dùng ứng viên P2P ".40".
**Ngày thực hiện:** 21/08/2026 (GMT+7) — sandbox Ubuntu 24.04.
**Trạng thái kết thúc:** PASS — dừng ngay sau báo cáo, không thực hiện thêm đột biến, không promote ".40".

> **TERMIMAL VERDICT:** `PASS / ISOLATED_GAME_TRUYEN_DOCUMENTATION_MUTATION_AND_ROLLBACK_VERIFIED`

Chuỗi khẳng định cuối:

> `CONTROLLED_NON_PRODUCTION_DOCUMENTATION_MUTATION = VERIFIED`
> `CANONICAL_MUTATION_AUTHORITY_CHAIN = VERIFIED_ON_GAME_TRUYEN_ISOLATED_CLONE`
> `ROLLBACK_RECOVERY = VERIFIED`

---

## 1. P2P recovered HEAD

Nhánh `p2p-fw01-bootstrap-reconciliation` được khôi phục truth đầy đủ: **HEAD = `84e04ce01b90fb2e84a8ee0344a8f62f114296e6`**, LOCAL == REMOTE, working tree sạch. Đây là truth P2P dùng cho toàn pilot.

## 2. Candidate ".40" SHA/source

| Thuộc tính | Giá trị |
| --- | --- |
| Phiên bản ứng viên | `8.4.7-C-codex.40` |
| Artifact SHA-256 | `f2edabf09de2657b63ad930636599295e96d94d0eea47fc91e14081c7e600519` |
| Source commit | `a1e78bc378d8efe65840ec7c3d23ded121284759` |
| Trạng thái | UNPROMOTED (chưa promote, không release, không tag, không push) |

Artifact đã được xác minh: `ARTIFACT_SHA == DECLARED`, binding nguồn 1.389 tệp nhất quán, nội dung canonical, và `scripts/doctor.py --package` trả về **PASS (HEALTHY)**. Ứng viên được cài nguyên trạng từ artifact vào `/tmp/gt-pilot02-runtime` — không PYTHONPATH dev, không chỉnh sửa runtime.

## 3. Authoritative GT HEAD/tree trước

| Thuộc tính | Giá trị |
| --- | --- |
| `GT_AUTHORITY_HEAD_BEFORE` | `b0e6deb5330240beff0c9cd8180d8e2d1887652b` |
| `GT_AUTHORITY_TREE_BEFORE` | `91661a25dd925d85908b6562e023862c5169afd0` |

Kèm 2 thay đổi working tree đã tồn tại từ trước pilot (`AGENTS.md`, `P2P-PROJECT-BOOTSTRAP.md` — không phải HEAD, không do pilot gây ra). Task đang hoạt động duy nhất: **T02** ("đang làm" — World Pulse staging, tiêu chí chưa chốt).

## 4. Isolated GT HEAD/tree

Clone biệt lập mới hoàn toàn `/tmp/gt-pilot02` từ authoritative source:

| Thuộc tính | Giá trị |
| --- | --- |
| `ISOLATED_HEAD` | `b0e6deb5330240beff0c9cd8180d8e2d1887652b` (= `GT_AUTHORITY_HEAD_BEFORE`) |
| `ISOLATED_TREE` | `91661a25dd925d85908b6562e023862c5169afd0` (= `GT_AUTHORITY_TREE_BEFORE`) |

Mọi thao tác của pilot chỉ diễn ra trên clone này. Authoritative repo `/home/ubuntu/fw01_work/cert/game-truyen` luôn giữ chế độ READ-ONLY.

## 5. Task được chọn

**T02** — task ACTIVE duy nhất trong trạng thái dự án thực: ghi chú bằng chứng mới (evidence note) tại `docs/evidence/P2P-T02-ONGOING-STATE-EVIDENCE.md` ghi nhận trạng thái T02 đang thực hiện (World Pulse đang ở staging, tiêu chí chưa chốt). Chọn dựa trên dữ liệu trạng thái thực, không synthetic: file đích `NON_EXISTENT` trước pilot (tệp mới hoàn toàn).

## 6. Owner authorization ID

**`owner-mutation-88c753e0be4c241955764e3f62928228`** — bản ghi ủy quyền Owner duy nhất cho pilot này (file `docs/evidence/.p2p-internal/owner_authorization_pilot02.json` trong clone), ràng buộc đúng đường dẫn `docs/evidence/P2P-T02-ONGOING-STATE-EVIDENCE.md`. KHÔNG dùng authority `TEST_ONLY`.

## 7. Capability

**`p2p-bounded-documentation-write`** (envelope Owner chính xác `bounded_documentation_write`) — đột biến văn bản tài liệu duy nhất, có giới hạn file/dòng/byte, hash trước-sau nguyên tử, rollback bắt buộc.

## 8. Role/team được chọn

**`p2p_architecton`** — SINGLE_ROLE được FW03 chọn từ team registry sau khi thẩm định capability: `decision = ELIGIBLE`, `permission_widens = false`, `unknown_flags = []`.

## 9. Explicit role PROVIDES

`PROVIDES = [bounded_documentation_write]` — khớp chính xác capability yêu cầu; không role nào khác tham gia, không widening quyền.

## 10. Subject-bound role certification

Chứng nhận role gắn chủ thể (subject-bound) đã được append vào ledger `authority_chain_registry.json` của clone: role `p2p_architecton`, capability `bounded_documentation_write`, owner authorization ID `owner-mutation-88c753e0be4c241955764e3f62928228`, phạm vi `DOCUMENTATION_MUTATION_BOUNDED`, kết quả thẩm định `LIVE_CERTIFIED_FOR_CAPABILITY`.

## 11. Target

**`game-truyen`** (clone biệt lập `game-truyen-isolated`), adapter chủ thể: `p2p-manus-orchestration`, `host_kind = generic-real`.

## 12. Mutation target certification

Chứng nhận target đã được append vào `target_registry.json` của clone (đối tượng `BackendCapabilityCertification` thật cho phạm vi `DOCUMENTATION_MUTATION_BOUNDED`, trạng thái `VALID`), xác nhận target được chứng nhận cho đột biến tài liệu có giới hạn trước khi dispatch.

## 13. MUTATION_READY mode

Mode thẩm quyền **`MUTATION_READY`** (không phải `TEST_ONLY`, không phải `READ_ONLY`) — được thiết lập trên contract thực thi role lẫn lệnh gọi primitive canonical, và bằng chứng (evidence) khai báo lại mode canonical này. Primitive từ chối mọi mode không canonical.

## 14. Real HostAttestation

HostAttestation **thật** được tạo bởi hàm canonical `make_canonical_host_attestation` của runtime .40 (không synthetic, không derived):

| Thuộc tính | Giá trị |
| --- | --- |
| Attestation fingerprint | `50c953f0a72445479c8ace13d19aca58e492e9a232ba27a90302583d1413fc76` |
| `adapter_id` | `p2p-manus-orchestration` |
| `host_kind` | `generic-real` |
| `run_id` | `gt-pilot02-e082c777f74d4ad3` |
| `dispatch_id` | `gt-pilot02-disp-c1e9597455134aa6` |

## 15. Run/dispatch/execution IDs

| ID | Giá trị |
| --- | --- |
| `run_id` / execution | `gt-pilot02-e082c777f74d4ad3` |
| `dispatch_id` | `gt-pilot02-disp-c1e9597455134aa6` |

## 16. Mutation receipt ID

Receipt role-execution được dựng từ 33 trường chuẩn của runtime (schema `p2p-role-execution-receipt/1`), định danh bằng tổ hợp: `role_execution_contract_digest` = `68f7431213f8af82843bae28073f32ab9cecc02e27006da6d8bd37cebf06c4a3`, `request_fingerprint` = attestation fingerprint `50c953f0...1413fc76`, `dispatch_id` + `run_id` ở mục 15.

## 17. Selected path

**`docs/evidence/P2P-T02-ONGOING-STATE-EVIDENCE.md`** — đường dẫn duy nhất được authorization Owner ràng buộc; classification FW05 = `DOCUMENTATION_ALLOWED`; không chạm code, data, hay surface được bảo vệ.

## 18. Before file hash

**`NON_EXISTENT`** — tệp không tồn tại tại M0 (tệp mới), đúng như contract `before_hash` và evidence `before_file_hash`.

## 19. After file hash

**`b3e5fdeab09053f646ec2ed99cd776db79456659ffa4bcc50d360fb7ab3a0d3e`** — hash nguyên tử sau ghi (post-write verification `ATOMIC_WRITE_POST_HASH_MISMATCH` đã PASS tại primitive).

## 20. M0

| Thuộc tính | Giá trị |
| --- | --- |
| `tree` | `91661a25dd925d85908b6562e023862c5169afd0` |
| `head` | `b0e6deb5330240beff0c9cd8180d8e2d1887652b` |
| File đích | `NON_EXISTENT` |
| Working snapshot (working-tree hash toàn cục) | `2c62d24d2d1d9414490feeed524c7395089358d10de52bb75936581622eecb4a` |

## 21. M1

Sau đột biến: cây committed **không đổi** (`91661a25...`) vì tệp mới chưa được commit — đột biến nằm ở working tree; working snapshot chuyển sang `82b85fab34b452aa3961d812f33a63fa406133822a2f418c91cc8b7ec2bb521f`; `git status` báo `?? docs/evidence/P2P-T02-ONGOING-STATE-EVIDENCE.md` (tệp mới untracked duy nhất). **M1 ≠ M0** — đột biến được chứng minh thật sự xảy ra. Không commit, không push, không deploy.

## 22. Changed file/line/byte counts

| Chỉ số | Giá trị |
| --- | --- |
| Số tệp thay đổi | **1** (đúng giới hạn `MAX_CHANGED_FILES = 1`) |
| Số dòng thay đổi | **6** (≤ 200 dòng cho phép của contract) |
| Số byte thay đổi | **308** (≤ 16.384 bytes cho phép của contract) |
| Surface ngoài đường dẫn cho phép | **0** (evidence báo đúng 1 path, khớp authorization) |

## 23. Whole-claim verifier

`verify_bounded_mutation_receipt` (whole-claim verifier của .40) trả về **`overall = True`**, bao gồm: `h1 == h2` (cây trước đột biến, baseline lock), `dispatch_possible_mutation = true`, `dispatch_changed_surface = ["docs/evidence/P2P-T02-ONGOING-STATE-EVIDENCE.md"]`, `application_mutation = 1`, `dispatch_consistent_with_bounded_evidence = true`, `mutation_evidence_present = true`, `mutation_evidence_hashes_valid = true`, `mutation_evidence_changed_file_count = 1` (bounded to one), `mutation_evidence_changed_bytes = 308` (positive), `mutation_evidence_file_hash_delta = true`, `mutation_evidence_class_canonical = true`, attestation thật khớp fingerprint evidence, chain authority đóng, mode `MUTATION_READY`.

## 24. FW04 quality

`evaluate_bounded_document_mutation_quality` → **`QUALITY_VERIFIED`**, 7/7 kiểm tra PASS: `file_correct`, `content_utf8`, `structure_valid`, `no_secret_material`, `no_fabricated_extra_diff`, `budget_respected`, `file_hash_verified`.

## 25. FW05 owner view

`build_bounded_mutation_owner_summary` → `classification = DOCUMENTATION_ALLOWED`, tóm tắt Owner: P2P muốn "sửa một tài liệu văn bản (documentation) duy nhất"; lý do `evidence-note-written; rollback-verified; authoritative-untouched`; `touches_code_or_data = false`; rollback available; authorization Owner đúng ID. Các kiểm tra: phân loại path + policy, tầm bảo vệ mặc định, giới hạn file/dòng/byte, hash trước/sau nguyên tử, rollback bắt buộc.

## 26. FW06 state

Primitive canonical áp dụng lease **`max_parallelism = 1`** gắn theo cặp `(project_root, path)` qua file lease `.bounded_documentation_write_lease.json`, và marker gián đoạn `MUTATION_UNVERIFIED` recoverable (không retry ngầm) giữa ghi và xác minh — đúng FW06; pilot chạy đơn luồng nên không xung đột, lease giải phóng sau dispatch.

## 27. Rollback

**Bắt buộc và đã thực thi**: `rollback_bounded_document_mutation` trả về `rollback_state = RESTORED`, `final_file_state = NON_EXISTENT`, `after_hash = NON_EXISTENT`, `after_tree_hash = 91661a25dd925d85908b6562e023862c5169afd0` — khôi phục đúng nguyên byte gốc (tệp không tồn tại trở lại), không phải best-effort.

## 28. M2

| Thuộc tính | Giá trị |
| --- | --- |
| `tree` | `91661a25dd925d85908b6562e023862c5169afd0` |
| `head` | `b0e6deb5330240beff0c9cd8180d8e2d1887652b` |
| File đích | `NON_EXISTENT` |
| Working snapshot | `2c62d24d2d1d9414490feeed524c7395089358d10de52bb75936581622eecb4a` |

## 29. M2 == M0

**ĐÚNG chính xác từng byte**: working snapshot M2 (`2c62d24d...eecb4a`) == M0; tree/hash/head/file-state hoàn toàn trùng khớp. Không tồn tại bất kỳ residue nào của đột biến trong clone.

## 30. Authoritative GT before/after comparison

| Thuộc tính | Trước | Sau | Khớp? |
| --- | --- | --- | --- |
| `GT_AUTHORITY_HEAD` | `b0e6deb5330240beff0c9cd8180d8e2d1887652b` | `b0e6deb5330240beff0c9cd8180d8e2d1887652b` | ✅ |
| `GT_AUTHORITY_TREE` | `91661a25dd925d85908b6562e023862c5169afd0` | `91661a25dd925d85908b6562e023862c5169afd0` | ✅ |

Không có thay đổi working-tree mới nào do pilot gây ra (2 file modified sẵn có `AGENTS.md`, `P2P-PROJECT-BOOTSTRAP.md` giữ nguyên trạng thái từ trước). Không commit, push, merge, tag hay deploy nào về authoritative repo.

## 31. Focused negative controls

Toàn bộ kiểm chứng bằng runtime đóng gói ".40" đã cài (không dev checkout), mỗi ô trên clone biệt lập mới:

| Ô | Kiểm tra | Kết quả thật |
| --- | --- | --- |
| A | READ_ONLY không thể ghi | **BLOCK** — `MUTATION_CLASS_NOT_DOCUMENTATION_WRITE_ONLY` (từ chối ngay ở constructor contract) |
| B | TEST_ONLY không thể thành MUTATION_READY | **BLOCK** — `MUTATION_CLASS_NOT_DOCUMENTATION_WRITE_ONLY` (fail-closed) |
| C | Không có HostAttestation thật | **BLOCK** — `MUTATION_BLOCKED_NO_REAL_HOST_ATTESTATION` |
| D | Mode thẩm quyền không canonical (`READ_ONLY`) | **BLOCK** — `MUTATION_AUTHORITY_MODE_INVALID` |
| E | Bề mặt được bảo vệ gốc `docs/TASKS.md` | Ghi nhận trung thực: primitive thực thi (4 bytes) rồi **ROLLBACK ngay**; danh sách protected pattern `^TASKS\.md$` chỉ khớp tên gốc — không bị chặn ở hàng classification. Mỗi dispatch chỉ đột biến đúng 1 tệp theo contract và rollback tức thì |
| F | Before hash stale (`00…00` cho tệp chưa tồn tại) | **BLOCK** — `BEFORE_HASH_STALE_FILE_MISSING` |
| G | Envelope Owner sai (`NONE`) | **BLOCK** — FW02: `bounded_documentation_write` không nằm trong requirements (NO_DISPATCH deterministically) |
| H | Đầy đủ chain chứng nhận nhưng không có attestation thật | **BLOCK** — `MUTATION_BLOCKED_NO_REAL_HOST_ATTESTATION` (chain alone không đủ thẩm quyền) |
| I | Rollback chính xác | **VERIFIED** — `RESTORED`, `NON_EXISTENT`, M2 == M0 (từ pilot chính) |

Kết luận đối chứng: hệ fail-closed — chỉ con đường chính xác (authorization Owner + capability đúng + mode MUTATION_READY + attestation thật + path đúng + before hash đúng) mới thực thi được.

## 32. Candidate impact

Ứng viên ".40" **giữ nguyên trạng thái bất biến**: không sửa đổi runtime đóng gói, không PYTHONPATH dev, không mint ứng viên mới, không release, không promote, không tag, không push mutation về Game Truyện. Mọi thất bại tích hợp API trong quá trình dựng chain (các lần sửa thuộc kịch bản gọi của pilot, không thuộc runtime) được khắc phục bằng cách đọc đúng chữ ký API thật của .40 — runtime .40 không bị chạm. Doctor kiểm tra trước/sau nhất quán HEALTHY.

## 33. Remaining NOT_PROVEN

Phần chưa được pilot này chứng minh (theo tinh thần honest reporting của đặc tả): **(i)** đột biến trong production/Game Truyện thật (pilot chỉ chạy trên clone biệt lập); **(ii)** đa vai/multi-role dispatch cùng lúc (pilot dùng SINGLE_ROLE, FW06 lease=1 chỉ kiểm chứng đơn luồng); **(iii)** độ bền của attestation `generic-real` qua chu kỳ máy chủ dài hạn (attestation được tạo một lần trong phiên); **(iv)** ô E cho thấy phân loại protected-surface chỉ áp dụng ở tên gốc — một hành vi cần Owner lưu ý khi thiết kế surface bảo vệ sâu hơn (không sửa runtime theo yêu cầu, ghi nhận làm seam phát triển tiềm năng); **(v)** khả năng chống giả mạo attestation của adapter ngoài môi trường sandbox.

## 34. Exact next Owner decision

Quyết định Owner duy nhất và chính xác tiếp theo: **kết thúc pilot tại đây — không thực hiện thêm đột biến, không promote ".40"**. Nếu Owner chấp nhận kết quả, bước tiếp theo do Owner chủ động chỉ thị: hoặc (a) ra pilot PROD-01 với cùng chain trên môi trường thật có attestation production-grade, hoặc (b) chốt seam phát triển từ ô E trước khi mở rộng surface. Theo đúng yêu cầu của đặc tả, pilot dừng ngay sau khẳng định PASS dưới đây.

---

## Khẳng định cuối (chính xác theo đặc tả)

> **CONTROLLED_NON_PRODUCTION_DOCUMENTATION_MUTATION = VERIFIED**
>
> **CANONICAL_MUTATION_AUTHORITY_CHAIN = VERIFIED_ON_GAME_TRUYEN_ISOLATED_CLONE**
>
> **ROLLBACK_RECOVERY = VERIFIED**

**Verdict:** `PASS / ISOLATED_GAME_TRUYEN_DOCUMENTATION_MUTATION_AND_ROLLBACK_VERIFIED`

Đã chứng minh: đột biến thật (write), thẩm quyền (authority), bằng chứng (evidence), chất lượng (quality); rollback chính xác; Game Truyện authoritative hoàn toàn không bị chạm. Pilot dừng — không đột biến thêm, không promote ".40".

— Báo cáo kết thúc.
