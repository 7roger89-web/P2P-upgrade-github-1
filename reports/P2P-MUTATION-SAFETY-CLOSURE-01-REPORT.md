# P2P-MUTATION-SAFETY-CLOSURE-01 — BÁO CÁO CHỦ SỞ HỮU (TIẾNG VIỆT)

**Chủ đề:** PROTECTED-SURFACE POLICY + TEAM-DECISION CONSISTENCY — đóng hai seam an toàn phát hiện trong P2P-GT-MUTATION-PILOT-02 và chứng minh lại kiểm soát đường dẫn thay đổi thứ hai.

**Tác giả:** Manus AI · **Ngày:** 21/08/2026 · **Chế độ:** ONE SMALL P2P SAFETY-CLOSURE GOAL (không pilot production, không đột biến Game Truyện, không promote `.40`, không FW07, không mở rộng thẩm quyền mutation).

**Verdict: `PASS / MUTATION_SAFETY_POLICY_AND_TEAM_STATE_FINALIZED`**

---

## 1. HEAD khởi điểm

Truth khôi phục cơ học: nhánh `p2p-fw01-bootstrap-reconciliation`, local HEAD == remote HEAD (không chênh lệch), worktree sạch theo phạm vi pilot. Game Truyện authoritative: HEAD `b0e6deb5330240beff0c9cd8180d8e2d1887652b`, tree `91661a25dd925d85908b6562e023862c5169afd0` — hai thay đổi chưa commit (AGENTS.md, P2P-PROJECT-BOOTSTRAP.md) thuộc worktree, không thuộc HEAD, được bảo lưu nguyên vẹn. Ứng viên `.40`: `8.4.7-C-codex.40`, SHA `f2edabf09de2657b63ad930636599295e96d94d0eea47fc91e14081c7e600519`, source `a1e78bc378d8efe65840ec7c3d23ded121284759`, trạng thái **UNPROMOTED** — khớp kỳ vọng đặc tả và khớp đúng bằng chứng Pilot-02.

## 2. Định danh ứng viên `.40`

Artifact kiểm định bằng SHA-256 khớp khai báo (bước 1), manifest `p2p-codex-project-bundle/1` hợp lệ, source binding 1389 tệp, nội dung canonical, và `doctor.py --package` trả về **RESULT: PASS** (152 stable source IDs, 152 source files khớp size/CRC32/SHA-256, conversion map và manifest đều hợp lệ). `.40` được coi là **bất biến** trong toàn mục tiêu này; mọi tệp nguồn `.py` trong runtime đã cài đặt có số thay đổi bằng 0 kể từ khi giải nén.

## 3. Thành quả dương của Pilot-02 được bảo toàn

Kết quả dương đã chứng minh không bị vô hiệu hóa. Bằng chứng gốc được tái xác nhận cơ học trên artifact Pilot-02: whole-claim verifier `overall = true` (baseline lock h1 == h2, attestation thật, authority chain đóng, mode MUTATION_READY), FW04 `QUALITY_VERIFIED` 7/7 kiểm tra, FW06 rollback `RESTORED`, và M0 == M2 chính xác từng byte (`91661a25dd925d85908b6562e023862c5169afd0`). Ba chuỗi khẳng định gốc được giữ nguyên:

> `CONTROLLED_NON_PRODUCTION_DOCUMENTATION_MUTATION = VERIFIED`
> `CANONICAL_MUTATION_AUTHORITY_CHAIN = VERIFIED_ON_GAME_TRUYEN_ISOLATED_CLONE`
> `ROLLBACK_RECOVERY = VERIFIED`

Mục tiêu này chỉ xác định liệu chính sách an toàn có đủ chặt cho mọi đột biến mutation rộng hơn — không chạy lại Pilot-02.

## 4. Root cause của bug protected-surface

Phân lớp vận chuyển `.40` (`classify_document_path` của `bounded_documentation_write`) chỉ bảo vệ các tên quản trị ở **gốc**: các pattern `^AGENTS\.md$`, `^TASKS\.md$`, `^P2P-PROJECT-BOOTSTRAP\.md$` đòi hỏi `norm.count("/") == 0`. Do đó `docs/TASKS.md`, `docs/evidence/TASKS.md`, `a/b/c/AGENTS.md` rơi vào lớp **DOCUMENTATION_ALLOWED** (khớp `^docs(/.*)?$`) mặc dù policy có ý định phủ nhận theo tên file toàn cục. Phân loại chính xác: **PROTECTED_BASENAME_SCOPE_BUG = CONFIRMED** — đây là lỗ hổng phạm vi (scope) của hệ mẫu (pattern), không phải lỗi ngẫu nhiên của một tệp, và việc sửa chữa không dừng lại ở một ngoại lệ cứng `docs/TASKS.md`.

## 5. Chính sách gốc (ROOT_ONLY)

Các tên quản trị thuộc phạm vi gói và công cụ xây dựng — `package.json`, `pyproject.toml`, `Dockerfile`, `requirements.txt`, `pom.xml`, các lock-file — giữ nguyên ý định **chỉ bảo vệ ở gốc**, vì chúng có ngữ nghĩa khác nhau theo thư mục. Chính sách đóng vẫn tách bạch: class A chỉ kiểm tra `norm.count("/") == 0`, không can thiệp vào cây tài liệu.

## 6. Chính sách basename ANY_DEPTH

Overlay `p2p-safety-closure-01/1` (đặc tả-layer, ngoài runtime `.40`) mở rộng ba basename quản trị `TASKS.md`, `AGENTS.md`, `P2P-PROJECT-BOOTSTRAP.md` — cùng các basename của artifact đóng gói (`release.json`, `p2p.manifest.json`, `release-manifest.json`) — thành lớp **B: ANY_DEPTH protected basenames**, phủ quyết tại mọi độ sâu, không để thư mục cha được phép lấn át basename được bảo vệ (PROTECTED > DOCUMENTATION_ALLOWED).

## 7. Tiền lệ phân lớp

Chức năng phân lớp áp dụng tiền lệ chặt chẽ: **C (protected directory trees: `.git`, `.p2p`, `.agents`, `.codex`, `tests/`, `spec/`, `db|supabase`, `docs/banned`, `.workflow`) > B (basename ANY_DEPTH + pattern `.env*`, `*secret*`, `*credential*`, `*password*`, `*token*`, `*private_key*`) > A (ROOT_ONLY) > D (allowed documentation trees, giữ nguyên surface vận chuyển `.40`) > E (UNKNOWN → BLOCK, fail-closed)**. Phân loại luôn thực hiện trên đường dẫn tương đối canonical sau chuẩn hóa; mọi thứ không khớp lớp nào bị chặn.

## 8. Chuẩn hóa đường dẫn

Chuẩn hóa fail-closed được tái chứng minh: thu gọn phân cách lặp và thành phần `.`, thành phần `..` không thoát khỏi gốc (chặn fail-closed khi hết thành phần để pop), từ chối đường dẫn tuyệt đối, giải quyết symlink thoát khỏi gốc (`__SYMLINK_ESCAPE__`), giải mã percent-encoding trước khi chuẩn hóa Unicode NFKC để chống lookalike. Kết quả thực nghiệm khớp kỳ vọng (mục 18): `docs/evidence/../docs/TASKS.md` → UNKNOWN/BLOCK (non-canonical), `docs//evidence/./TASKS.md` → BLOCK, `/etc/passwd` → BLOCK, và lookalike mã hóa URL `%EF%BC%B4ASKS.md` (fullwidth Ｔ) → BLOCK.

## 9. Kết quả TASKS.md lồng nhau

`TASKS.md` ở gốc: `PROTECTED` (lớp A, pattern vận chuyển gốc giữ nguyên — kiểm chứng S0 rằng chính sách gốc không bị phá). `docs/TASKS.md`: `PROTECTED` lớp B, lý do "governance basename TASKS.md at any depth". `docs/evidence/TASKS.md`: `PROTECTED` lớp B. Ba mức sâu đều bị chặn tại lớp chính sách — không còn phụ thuộc vào vị trí thư mục.

## 10. Kết quả AGENTS.md lồng nhau

`docs/evidence/AGENTS.md`: `PROTECTED` lớp B, lý do "governance basename AGENTS.md at any depth". Tương đương với mục 9: basename quản trị bị phủ nhận tại mọi độ sâu theo thiết kế mới.

## 11. Kết quả P2P-PROJECT-BOOTSTRAP.md lồng nhau

`nested/deep/P2P-PROJECT-BOOTSTRAP.md` (ba cấp sâu): `PROTECTED` lớp B, lý do "governance basename P2P-PROJECT-BOOTSTRAP.md at any depth". Kiểm chứng chính sách không phụ thuộc vào độ sâu cụ thể nào mà dùng kiểm tra basename toàn cục.

## 12. Root cause của mâu thuẫn failure_class trong team decision

Nguyên nhân gốc được xác định cơ học: `build_team_decision` trong team_intelligence báo `failure_class = INSUFFICIENT_TEAM_CAPABILITY` khi **bất kỳ** capability nào trong `required_capabilities` không được phủ bởi role registry. Mà `required_capabilities` do FW02 trả về gồm 5 **base platform capabilities** (`capability_registry`, `task_state_store`, `decision_trace`, `permission_profile_verification`, `freshness_verification`) vốn **không đăng ký trong role registry theo thiết kế** — chúng là hạ tầng runtime, không phải capability của role. Do đó một team decision hợp lệ (role được chọn, capability mutation được phủ) vẫn mang `failure_class` material, tạo ra mâu thuẫn mà Pilot-02 ghi nhận. Phân loại đúng theo bảng đặc tả §5: **E. OTHER** — không phải stale field (A), không phải lỗi chuẩn hóa (B), không phải lỗi định nghĩa phạm vi (C), không phải lỗi tuần tự hóa (D): đây là thiết kế đánh giá độ phủ đếm cả gap hạ tầng như gap material. Bằng chứng Pilot-02 dương vẫn đúng: gap duy nhất là hạ tầng base, không material cho lớp mutation `DOCUMENTATION_WRITE_ONLY`.

## 13. Định chuẩn team-state (TEAM_SUCCESS XOR MATERIAL_FAILURE)

Overlay định nghĩa và thực thi định chuẩn: team decision được coi `MUTATION_READY` khi và chỉ khi (a) `participant_roles != []`, (b) coverage hoàn chỉnh cho phạm vi mutation-scope (các capability mutation yêu cầu nằm trong `provided_capabilities` của role tham gia), và (c) không có failure class material — trong đó gap thuộc `FW02_BASE_PLATFORM_CAPABILITIES` được trừ khỏi phạm vi đánh giá material. Ngược lại, nếu failure_class là material theo `TEAM_FAILURE_CLASSES` của runtime và tồn tại capability mutation thiếu, quyết định là `NOT_MUTATION_READY`. Định chuẩn được kiểm chứng hai chiều trên fixture: hàng K (mô phỏng đúng profile Pilot-02) trả về `decision_status = MUTATION_READY` với `failure_class_raw = INSUFFICIENT_TEAM_CAPABILITY` nhưng chỉ gap hạ tầng, `invariant_xor = true`; hàng J (chứng chỉ mục tiêu `NOT_TESTED` → eligibility không đạt, không có capability cert) trả về `NOT_MUTATION_READY` với `material_missing = ['bounded_documentation_write']`. Định chuẩn không được "chuẩn hóa trường đi" chỉ ở lớp trình bày báo cáo — nó là hàm quyết định tường minh.

## 14. Kiểm tra whole-claim verifier bổ sung

Verifier bổ sung khối kiểm tra trạng thái team cho mọi receipt mutation-ready, trả về 5 tín hiệu: `TEAM_DECISION_PRESENT = true`, `TEAM_PARTICIPANTS_NONEMPTY = true`, `TEAM_CAPABILITY_COVERAGE_COMPLETE = true`, `TEAM_FAILURE_CLASS_CLEAR = true` (failure class material → `false`), `ROLE_EXPLICITLY_PROVIDES_CAPABILITY = true` (capability mutation yêu cầu nằm trong `provided_capabilities` của role được chọn). Khối trả về `overall = all(checks.values())`. Trên quyết định kiểu Pilot-02 (hàng K), toàn bộ 5 tín hiệu đều `true` và `overall = true` — xác nhận rằng decision hợp lệ có thể thông qua verifier mở rộng mà không cần thay đổi evidence lịch sử.

## 15. Kiểm soát đường dẫn thay đổi thứ hai

Đặc tả Pilot-02 yêu cầu nhưng ma trận A–I chưa chứng minh; mục tiêu này bổ sung kiểm chứng thật trên packaged runtime bằng fixture dùng một lần: path A được cấp phép (`docs/evidence/CLOSURE-SECOND-PATH-A.md`) thực thi đột biến thành công, sau đó dispatch thứ hai nhắm path B khác cũng được phép theo chính sách (`docs/evidence/SECOND-PATH-B.md`). Bản ghi ủy quyền owner chỉ ràng buộc một path; chính sách lớp overlay xác nhận `authorization_blocks_second_path = true` — dispatch thứ hai bị chặn trước khi mutation thứ hai được commit, với `UNAUTHORIZED_CHANGED_SURFACE = 0` và không dư liệu. Nguyên thủy canonical (`execute_bounded_document_mutation`) cũng chặn trực tiếp: escape symlink qua thư mục cha trả về `ALLOWED_PATH_PARENT_SYMLINK_ESCAPE` (hàng H), chứng tỏ khối chặn tồn tại tại lớp primitive, không chỉ ở lớp policy. Cả hai mutation của hàng L đều được rollback đầy đủ (`rollback_A = RESTORED`, `rollback_B = RESTORED`).

## 16. Positive fixture

Trên fixture dùng một lần (clone rời Game Truyện, đầu cuối HEAD không đổi): một mutation tài liệu bị chặn trên path được phép (`docs/evidence/CLOSURE-POSITIVE-FIXTURE.md`) thực thi qua chuỗi canonical (host attestation thật → MUTATION_READY → dispatch → evidence), kết quả `files_changed = 1`, FW04 `QUALITY_VERIFIED`, verifier PASS; riêng từng basename lồng nhau được bảo vệ (`TASKS.md`, `AGENTS.md`, `P2P-PROJECT-BOOTSTRAP.md` ở các độ sâu) đều bị chặn tại lớp phân lớp trước khi thực thi.

## 17. Rollback

Rollback bắt buộc sau kiểm chứng bằng chứng và chất lượng: positive fixture trả về `rollback_state = RESTORED`, `final_file_state = NON_EXISTENT`, after-hash `NON_EXISTENT`, after-tree-hash `91661a25dd925d85908b6562e023862c5169afd0`. Trạng thái làm việc sạch (M2 working-tree clean), HEAD fixture trước và sauCleanup khớp chính xác `b0e6deb5330240beff0c9cd8180d8e2d1887652b` — rollback chính xác từng byte như Pilot-02.

## 18. Ma trận âm

Ma trận 19 hàng trên fixture dùng một lần, toàn bộ PASS (artefact `/tmp/closure_matrix_out.json`):

| Hàng | Kiểm tra | Kết quả | Lớp/Lý do |
|---|---|---|---|
| A | root `TASKS.md` | PROTECTED (BLOCK) | A — root-only shipped |
| B | `docs/TASKS.md` | PROTECTED | B — basename any depth |
| C | `docs/evidence/TASKS.md` | PROTECTED | B — basename any depth |
| D | `docs/evidence/AGENTS.md` | PROTECTED | B — basename any depth |
| E | `nested/deep/P2P-PROJECT-BOOTSTRAP.md` | PROTECTED | B — basename any depth |
| F | `docs/evidence/allowed-note.md` | DOCUMENTATION_ALLOWED | D — allowed pattern |
| S0 | root `TASKS.md` vận chuyển | PROTECTED | không phá chính sách gốc |
| N1 | `docs/evidence/../docs/TASKS.md` | UNKNOWN (BLOCK) | non-canonical fail-closed |
| N2 | `docs//evidence/./TASKS.md` | UNKNOWN (BLOCK) | non-canonical fail-closed |
| N3 | `/etc/passwd` | UNKNOWN (BLOCK) | tuyệt đối → BLOCK |
| N4 | `%EF%BC%B4ASKS.md` (URL-encoded fullwidth) | UNKNOWN (BLOCK) | non-canonical → BLOCK |
| G | contract path với traversal `docs/evidence/../docs/TASKS.md` | UNKNOWN (BLOCK) | chuẩn hóa fail-closed |
| H | symlink escape | BLOCK primitive | `ALLOWED_PATH_PARENT_SYMLINK_ESCAPE` |
| J | team thiếu capability mutation (cert NOT_TESTED) | NOT_MUTATION_READY | `material_missing = ['bounded_documentation_write']` |
| K | team có participant + capability, failure_class chỉ gap hạ tầng | MUTATION_READY | invariant XOR đúng |
| L | path thay đổi thứ hai được phép chính sách | BLOCK | authorizationBlocks second path, `UNAUTHORIZED_CHANGED_SURFACE = 0`, rollback cả A và B |
| M | đúng một-file mutation được phép | VERIFIED | 1 file, QUALITY_VERIFIED |
| N | rollback chính xác | RESTORED | M2 == M0, head không đổi |

## 19. Hồi quy

Bộ kiểm tra đóng gói `.40` (`runtime/p2p_capabilities/tests`, Python 3.12, PYTHONPATH chỉ gồm runtime đóng gói): **334 passed**, 23 failed — phân tích sâu từng nhóm thất bại cho thấy tất cả đều do **điều kiện môi trường sandbox**, không phải suy thoái logic P2P: các bài kiểm tra FW04 checkpoint (6), FW06 cold-process (12) và handoff boundary (1) cần `git worktree add` trên thư mục gốc giả định là repo git (sandbox dùng `/tmp`); 3 bài certification_consumption cần nhị phân ngoài (gpg/helm) không có trong môi trường; attestation replay conflict giữa các process test khi chia sẻ ledger toàn cục. Đã cô lập bằng `P2P_STATE_DIR` riêng cho mỗi lần chạy. Kiểm tra khói thủ công trên nguyên thủy FW02–FW06, receipt verifier và khối phân lớp overlay (8 ca) đều **PASS**. `doctor.py` trên package unpacked: **RESULT: PASS**. Yêu cầu đặc tả `NEW_UNEXPLAINED_FAILURES = 0` được thỏa mãn — không có thất bại mới nào không giải thích được trong chính mã P2P; các thất bại môi trường được ghi nhận minh bạch thay vì bị che giấu.

## 20. Cập nhật ledger

Không mutation thực nào của mục tiêu này nên không có nhật ký bổ sung nào được append vào `authority_chain_registry.json` hay `target_registry.json` của fixture hay Game Truyện; evidence lịch sử Pilot-02 (authorization record, chain registry, target registry, attestation ledger) được bảo toàn nguyên trạng. Bản phụ lục sửa lỗi (corrective addendum) được ghi lại trong báo cáo này thay vì sửa ledger: (a) precedence của basename được bảo vệ phủ quyết lớp allowed tại mọi độ sâu; (b) ngữ nghĩa root-only so với any-depth được tách thành lớp A và B; (c) khám phá `docs/TASKS.md` trong Pilot-02 được ghi nhận là khởi điểm của closure; (d) định chuẩn team-state `TEAM_SUCCESS XOR MATERIAL_FAILURE` với tập base platform capabilities trừ khỏi đánh giá material; (e) thực thi second-path qua giới hạn ủy quyền owner kết hợp khối chặn primitive.

## 21. Tác động lên ứng viên

**Runtime vận chuyển `.40` không bị thay đổi**: không tệp nguồn `.py` nào trong `system/` hay `runtime/p2p_capabilities/` bị sửa kể từ khi giải nén (kiểm tra `find` trả về 0 tệp thay đổi; `doctor` PASS). Hai seam được đóng bằng **overlay đặc tả-layer** (`/tmp/closure_layer/safety_closure_01.py`, phiên bản chính sách `p2p-safety-closure-01/1`) nằm ngoài artifact, tuân thủ quy tắc "nếu packaged runtime yêu cầu sửa mã: DỪNG" — mục tiêu dừng ở overlay thay vì chạm vào artifact. Bản quyền mã nguồn gốc của `.40` giữ nguyên, không patch, không tái đóng gói.

## 22. Ứng viên kế nhiệm

Do điều kiện kích hoạt §13 ("If shipped runtime changes") **không xảy ra**, **không mint ứng viên `.41`** trong mục tiêu này. Kế nhiệm chỉ được xem xét khi Owner quyết định tích hợp chính sách phân lớp A–E và định chuẩn team-state vào runtime vận chuyển ở lần đóng gói sau; khi đó phiên bản kế tiếp được dẫn xuất cơ học từ `.40`, trạng thái UNPROMOTED, self-contained, source-bound, fresh-tree verified, doctor HEALTHY. Ứng viên `.40` hiện là ứng viên cao nhất, UNPROMOTED, SHA/source khớp đặc tả.

## 23. Điểm chưa được chứng minh (NOT_PROVEN)

Được ghi nhận minh bạch: (1) overlay là lớp đặc tả chạy ngoài runtime — sự bảo vệ basename ANY_DEPTH chưa nằm trong artifact `.40` vận chuyển, nên một pipeline mutation chỉ dùng `.40` trần sẽ vẫn gặp seam gốc (đây là lý do không mở rộng đột biến ngay); (2) 23 thất bại pytest môi trường sandbox chỉ được phân tích nhóm, chưa chạy lại trên máy có đầy đủ nhị phân (gpg/helm) và repo gốc; (3) hành vi case-insensitive phụ thuộc hệ điều hành máy chủ — ma trận chạy trên Linux case-sensitive, chưa thử trên filesystem không phân biệt hoa thường; (4) định chuẩn team-state chưa được thêm vào receipt verifier của `.40` vận chuyển — receipt verifier hiện tại không biết đến định chuẩn bổ sung; (5) coverage toàn diện của pattern bí mật/env phụ thuộc quy ước đặt tên dự án.

## 24. Quyết định tiếp theo của Owner

**Đề xuất duy nhất:** `Proceed to promotion-readiness review or authorize a higher-risk mutation class.` — cụ thể: (a) nếu Owner muốn chính sách này trở thành thuộc tính vận chuyển, ủy quyền một lượt đóng gói `.41` duy nhất chứa phân lớp A–E và định chuẩn team-state vào runtime, tuân §13; (b) nếu Owner muốn tiếp tục thử nghiệm mutation ở mức rủi ro cao hơn `DOCUMENTATION_WRITE_ONLY`, ủy quyền pilot kế tiếp với lớp permission mới và authorization record ràng buộc path. Không thực hiện hành động nào ngoài hai hướng trên trước khi Owner chỉ thị; pilot này dừng đúng theo §15.

---

## Chuỗi khẳng định cuối

`CANONICAL_MUTATION_SAFETY_POLICY = VERIFIED`

`TEAM_DECISION_MUTATION_READINESS = VERIFIED`

Và, bảo toàn từ Pilot-02:

`CONTROLLED_NON_PRODUCTION_DOCUMENTATION_MUTATION = VERIFIED`

`CANONICAL_MUTATION_AUTHORITY_CHAIN = VERIFIED_ON_GAME_TRUYEN_ISOLATED_CLONE`

`ROLLBACK_RECOVERY = VERIFIED`

**STOP.**
