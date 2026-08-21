# P2P-BOUNDED-DOCUMENTATION-WRITE-01 — Báo cáo cuối cùng cho Owner

**Goal:** Thêm năng lực ghi tài liệu có giới hạn (bounded documentation write) nhỏ nhất, trung lập nhà cung cấp, thất bại theo hướng đóng (fail-closed) vào runtime P2P — khép kín đường nối (seam) đã được chứng minh trong P2P-GT-MUTATION-PILOT-01 (`BLOCKED / NO_CANONICAL_DOCUMENTATION_MUTATION_CAPABILITY`).

**Không thực hiện:** phi vụ đột biến Game Truyện thật; đột biến Gia Phả; Logistics (DO_NOT_INSTALL_YET); không deploy, không promote/phát hành, không chạy lại Hội đồng 8/8, không phục sinh C36, không chạm vào ứng viên .37 (bất biến lịch sử).

---

## 1. HEAD khởi điểm

Bắt đầu từ `HEAD = f758d635c461419be3147a1efbc10e4f961f74d7` trên nhánh `p2p-fw01-bootstrap-reconciliation` (LOCAL == REMOTE, worktree sạch). Ứng viên trước đó là `.37` (sha `4aafdcd383b1002842df2465cfd3ce5f4bb3d9d792ce75ad5000771e629640f7`, UNPROMOTED, nguồn `d1a88fc`/`61b4be97`). HEAD hiện tại sau toàn bộ công việc: `7a8d03b` (sau 3 commit BW01: `a6d2c33` thực thi, `8a4ffd1` ứng viên .38, `7a8d03b` sổ cái kiến trúc).

## 2. Blocker đã xác nhận

Trên gói ứng viên .37 được đóng gói nguyên bản, đã xác nhận lại `DOCUMENTATION_WRITE_CAPABILITY_GAP = CONFIRMED`: runtime không có năng lực đột biến tài liệu chính tắc nào — đúng theo vết seam `BLOCKED / NO_CANONICAL_DOCUMENTATION_MUTATION_CAPABILITY` từ phi vụ P2P-GT-MUTATION-PILOT-01. Đây là blocker duy nhất được khép kín trong goal này.

## 3. Capability ID

ID chính tắc mới: **`bounded_documentation_write`** (registry `capabilities.json`, TYPE=`TASK_CAPABILITY`, INVOCATION_CLASS=`HOST_PRIMITIVE`, TRUST_LEVEL=`HOST_CODE`, STATUS=`ACTIVE`). Primitive gốc đặt tại `.p2p/system/p2p_capabilities/bounded_documentation_write.py`.

## 4. Capability semantics

Năng lực thực hiện **đúng một (exactly one)** đột biến tài liệu văn bản UTF-8 có giới hạn, trong một workspace bị cô lập/không phải production được Owner ủy quyền tường minh, thông qua primitive chính tắc `execute_bounded_document_mutation`. Tuyệt đối không có WRITE hệ tệp chung (không delete, không rename, không shell-arbitrary-write). Mọi trục không xác định — phân loại đường dẫn lạ, bề mặt được bảo vệ, before_hash lỗi thời, thiếu ủy quyền Owner, vượt ngân sách, nội dung nhị phân, ghi không nguyên tử — đều bắn `BoundedDocWriteError` và **không file nào được ghi** (fail-closed).

## 5. Provider scope

`PROVIDER_SCOPE = BOUNDED_DOCUMENTATION_TASK` — hoàn toàn trung lập nhà cung cấp (model/backend): không yêu cầu nhà cung cấp nào, không kích hoạt trigger đột biến code, không thuộc quorum 8/8 chính tắc. `CANONICAL_QUORUM_MEMBER = false`, `OPTIONAL_SPECIALIST = false`.

## 6. Dependency-vs-provision semantics

`bounded_documentation_write` **phụ thuộc vào** (REQUIRES): `non_mutating_project_analysis`. Nó **cung cấp** (PROVIDES): `bounded_documentation_write`. Các điểm ngữ cảnh: `document_classification`, `bounded_write_primitive`, `rollback_contract`. Không năng lực nào khác được mở rộng quyền; tất cả 8 quorum chính tắc giữ nguyên không thay đổi.

## 7. Selected role

Năng lực chỉ được phép gọi trong vai có grant **`WRITE_BOUNDED`** — vai được thêm vào `PERMISSION_GRANTS` trong `role_contract.py`, gắn qua `role_bridge.dispatch()` bằng callback `execute_bounded_write` cùng `owner_mutation_envelope`. Vai read-only và vai trần (ceiling) chỉ có READ/WRITE cũ không tự động thỏa `WRITE_BOUNDED`.

## 8. Subject-bound certification

Phạm vi chứng nhận mới `DOCUMENTATION_MUTATION_BOUNDED` đã được thêm vào `CERTIFICATION_SCOPES` trong `backend_contract.py` (opt-in, không thay đổi chứng nhận mặc định của bất kỳ vai nào). Chứng nhận đột biến ràng buộc theo đối tượng: mỗi hợp đồng đột biến chỉ cho đúng một đường dẫn tương đối, được ràng buộc hash, và bằng chứng đột biến được liên kết danh tính với dispatch/execution/attestation.

## 9. FW02 inference

`capability_intelligence.py` được mở rộng: `CANONICAL_CAPABILITIES` bao phủ năng lực mới (coverage đầy đủ cho mọi `CAPABILITY_ID`), và `infer_required_capabilities` chấp nhận kwarg `owner_mutation_envelope` để suy ra `bounded_documentation_write` khi và chỉ khi ý định task là đột biến tài liệu có phong bì Owner; nếu không khớp, năng lực không bao giờ được suy ra.

## 10. Permission model

`role_eligibility.py`: `PERMISSION_ORDER = (NONE, READ, WRITE_BOUNDED, WRITE, EXECUTE, NETWORK)` — **WRITE_BOUNDED đứng chặt chẽ giữa READ và WRITE**: vai chỉ có WRITE_BOUNDED không bao giờ thỏa trần WRITE; vai read-only không được cấp WRITE_BOUNDED. Các marker read-only tiếp tục chỉ khớp READ.

## 11. Protected surfaces

`classify_document_path` — fail-closed trên mọi lớp: chỉ `DOCUMENTATION_ALLOWED` cho `docs/**`, `README*`, `CHANGELOG*`, `CONTRIBUTING*`, `reports/**/*.md`; mọi thứ khác là `PROTECTED` (`.git/**`, `.p2p/**`, `.env*`, secrets, lockfiles, manifests, `AGENTS.md`, `TASKS.md`, migration, test, code) hoặc `UNKNOWN` → BLOCK. Symlink, đường dẫn tuyệt đối, traversal `..`, ghi ngoài project root đều bắn lỗi trước bất kỳ I/O nào.

## 12. Safe-write primitive

`bounded_documentation_write.py` (848 dòng): `BoundedDocMutationContract` (frozen, xác thực fail-closed), `BoundedDocWriteEvidence`, `classify_document_path`, `execute_bounded_document_mutation` (ghi nguyên tử rồi mới xác thực hash), `evaluate_bounded_document_mutation_quality` (FW04), `build_bounded_mutation_owner_summary` (FW05), trạng thái lease/interruption (FW06), hằng `NON_EXISTENT` cho tài liệu mới tạo.

## 13. Path/symlink protections

Trước khi mở file: phân loại bề mặt → từ chối nếu không `DOCUMENTATION_ALLOWED`; từ chối symlink; từ chối đường dẫn tuyệt đối/traversal; kiểm tra `project_root` là tiền tố thực (resolve); kiểm tra binary bằng phát hiện null-byte + heuristic nội dung nhị phân. Mọi điểm từ chối đều trả `BoundedDocWriteError` với mã lỗi tường minh (`TARGET_CLASSIFIED_PROTECTED`, `TARGET_IS_BINARY`, `TARGET_OUTSIDE_ROOT`, …).

## 14. Mutation contract

`BoundedDocMutationContract`: `mutation_class == DOCUMENTATION_WRITE_ONLY`; `max_changed_files == 1`; một `allowed_relative_path` duy nhất; `before_hash` là digest 40–64 hex hoặc sentinel `NON_EXISTENT` (tạo mới tài liệu — được kiểm chứng chống file đang tồn tại); `max_changed_lines`, `max_bytes`; `rollback_required == REQUIRED`; `owner_authorization_id` không tầm thường; `candidate_sha` hex64; `constraint_fingerprint()` = SHA-256 toàn trường ràng buộc (thay đổi bất kỳ giới hạn nào → fingerprint khác).

## 15. Target certification

Trước ghi: file mục tiêu được chứng nhận tươi — `before_hash` phải khớp nội dung hiện thời trên đĩa (`BEFORE_HASH_STALE_MISMATCH` nếu lệch), và trường hợp `NON_EXISTENT` phải khớp với file không tồn tại thật (`BEFORE_HASH_NON_EXISTENT_CONTRADICTED` nếu file đã có). Sau ghi: `after_file_hash` khớp byte-for-byte với nội dung đã ghi; `after_tree_hash` xác minh trạng thái cây.

## 16. HostAttestation implications

Sổ tái phát (replay ledger) của `host_attestation` đã được nối vào bằng chứng: `BoundedDocWriteEvidence.host_attestation_id` không bao giờ trống — khi không có HostAttestation tại thời điểm thực thi (fixture cô lập), nó được suy ra định danh từ cặp dispatch/execution bằng SHA-256, để trình xác minh không bao giờ rơi vào nhánh thất bại-mở. Bằng chứng đột biến phải khớp ledger attestation và khóa hash cây (tree-hash binding) trong nhánh bounded của verifier toàn-claim.

## 17. Mutation receipt

`role_receipt.py`: biên lai mới nhận `mutation_evidence`, hàm `_g1_validate_mutation_evidence` xác thực lược đồ/định danh/rollback; `_g1_mutation_state_check` được mở rộng nhánh bounded (đếm `application_mutation` từ bằng chứng = 1, kiểm `dispatch_consistent_with_bounded_evidence`); trình xác minh toàn-claim đặc cách `dispatch_ok` và `mutation_zero` cho biên lai bounded: `mutation_zero` đòi hash bằng nhau VÀ `application_mutation == 1` VÀ tính nhất quán dispatch-bằng chứng; `dispatch_ok` đòi `possible_mutation=True` trên đúng một bề mặt thay đổi khớp bằng chứng.

## 18. Rollback contract

`rollback_bounded_document_mutation`: khôi phục đúng byte gốc cho file đã tồn tại, hoặc xóa file mới tạo (trường hợp `NON_EXISTENT`), chứng minh `FINAL_FILE_STATE == ORIGINAL` và `FINAL_TREE_HASH == PRE_MUTATION`; lỗi rollback bắn ngoại lệ, không bao giờ "cố gắng tốt nhất". `rollback_required == REQUIRED` trong mọi hợp đồng và trong mọi bằng chứng.

## 19. Crash/retry behavior

FW06: lease cho phép tối đa 1 đột biến song song (`max_parallelism = 1`); đánh dấu gián đoạn (interruption marker) giữa ghi và xác minh để trạng thái vỡ giữa chừng phục hồi thành `MUTATION_UNVERIFIED / ROLLBACK_REQUIRED` thay vì thử lại thầm lặng; `bounded_write_retry_decision` quyết định retry chỉ khi an toàn, `recover_after_crash` của fw06 nhận diện trạng thái mutation chưa xác minh.

## 20. Negative matrix

Bộ test tiêu cực phủ ma trận (tất cả PASS): phân loại đường dẫn bị bảo vệ/unknown/traversal/tuyệt đối/symlink; hash trước lỗi thời; sentinel `NON_EXISTENT` mâu thuẫn; nội dung nhị phân; vượt ngân sách dòng/byte; rào chắn Markdown mở; vật liệu bí mật trong nội dung (`no_secret_material` FAILED → `QUALITY_FAILED`); ủy quyền Owner trống/không hợp lệ; fingerprint thay đổi; thiếu trường hợp đồng; rollback thất bại; không ghi khi ngoại lệ; biên lai bounded vi phạm hash/định danh/count không nhất quán.

## 21. Positive fixture M0/M1/M2

Chu kỳ sống M0/M1/M2 được chứng minh trên repo fixture cô lập bỏ được: **M0** — cây trước đột biến; **M1** — ghi tài liệu đúng ràng buộc (đúng 1 file, đúng đường dẫn, đúng giới hạn, hash khớp); **M2** — rollback về đúng byte gốc, `FINAL_TREE_HASH == PRE_MUTATION`. Bằng chứng: `changed_file_count == 1`, `changed_relative_path` đúng hợp đồng, không thay đổi nào ngoài bề mặt được hợp đồng hóa, biên lai bounded vượt xác minh toàn-claim.

## 22. FW04 quality

`evaluate_bounded_document_mutation_quality`: 7 kiểm — `file_correct`, `content_utf8`, `structure_valid` (cân bằng fence Markdown, bằng chứng biên không phải ý kiến phong cách), `no_secret_material`, `no_fabricated_extra_diff`, `budget_respected`, `file_hash_verified`. Kết quả `QUALITY_VERIFIED`/`QUALITY_FAILED`; thất bại chất lượng buộc rollback-required phía sau (spec 16). `EXECUTION_SUCCESS != QUALITY_VERIFIED`.

## 23. FW05 owner view

`build_bounded_mutation_owner_summary`: bản tóm tắt hướng Owner (không lộ lựa chọn kỹ thuật host/model): file nào sẽ đổi, lý do, có yêu cầu rollback hay không, tóm tắt bằng tiếng Việt khi ngữ cảnh yêu cầu. Quyết định Owner đi qua `fw05.make_decision_record` với `decision_type = OWNER_GATE`.

## 24. FW06 resilience

Năng lực dùng hệ thống resilience fw06: lease song song-1, trạng thái `MUTATION_UNVERIFIED`, phục hồi sau crash, đánh dấu quiesce. Các kiểm fw06 trong bộ test baseline không bị thay đổi hành vi.

## 25. Full regression

Toàn bộ regression: 46 test BW01 mới — 46/46 PASS; bộ suite năng lực đầy đủ — 309 test PASS (263 baseline + 23 gate01 + 46 BW01, khớp kỳ vọng phát hiện); `validate_p2p_development_framework.py` — 78/78 PASS, 0 lỗi; `p2p_development_control.py validate` — PASS; fresh-tree verifier ứng viên — 4/4 ALL PASS; doctor `--package` — HEALTHY (gồm `foundation-runtime` PASS với quorum 8/8 giữ nguyên); gitleaks — đúng 2 false-positive tiền-tồn tại (NORMALIZED_C15_RECEIPT, `sk-1234567890abcdef` test fixture), **NEW_UNEXPLAINED_FAILURES = 0**. Không có kiểm nào bị loại bỏ hoặc làm yếu.

## 26. Durable ledger/governance updates

Đã thêm sổ cái kiến trúc bền vững `docs/bounded-documentation-write-capability-ledger.md` (STATUS/SEMANTICS/PROVENANCE/DEPENDENCIES/PERMISSION BOUNDARY/EVIDENCE REQUIREMENTS/ROLLBACK REQUIREMENT/KNOWN LIMITATIONS). Governance `development-control.json`: dòng ứng viên được mở rộng quy tắc dòng `.35/.36/.37/.38` (mỗi record ghim đúng một artifact SHA, tất cả UNPROMOTED, liên tục); script mint/verify được cập nhật tương ứng. Không có record lịch sử nào bị sửa.

## 27. Previous candidate preserved

Ứng viên `.37` bất biến: sha `4aafdcd383b1002842df2465cfd3ce5f4bb3d9d792ce75ad5000771e629640f7`, UNPROMOTED, source `d1a88fceac3eb3877eb9d7b642babc53fca1195b`/tree `61b4be97b25f28ca5502f6f0e6d31243c55ee823` — **không bị thay đổi, không bị sửa, không bị xóa**.

## 28. Successor candidate version/SHA

Ứng viên kế nhiệm duy nhất, UNPROMOTED, đã ghim nguồn-byte:
- **Phiên bản:** `8.4.7-C-codex.38`
- **Artifact SHA-256:** `d062ec5c4f8d2cb264c0b405de5236850d53d04757e264d871cf12395b0ec253`
- **Source commit:** `a6d2c33e62f91fd7a05d511085750945a5c25973` / **tree:** `1ff1b54cca35a9aa44f7c2df62166487d0188d89`
- **Fresh-tree verified:** ALL PASS · **Doctor:** HEALTHY · Dòng `.35→.36→.37→.38` consecutive UNPROMOTED đạt quy tắc.

## 29. Remaining NOT_PROVEN

1. Phi vụ đột biến tài liệu Game Truyện **thật** trên ứng viên .38 chưa được thực hiện (Owner gate).
2. Hành vi trong workspace có sẵn dữ liệu lớn/nhiều file tài liệu cạnh tranh lease chưa được tải thực.
3. Tích hợp chuỗi hợp đồng nhiều file (multi-envelope) chỉ được suy ra từ chuỗi đơn file, chưa chạy chuỗi thật.
4. Git `HEAD^{tree}` không đổi theo thiết kế — đột biến chỉ được chứng nhận bằng hash file/cây cục bộ, chưa được chứng nhận trên lịch sử git thật của Game Truyện.

## 30. Exact next Owner decision

**Approve or reject a second isolated Game Truyện documentation mutation pilot using the new candidate.**

---

## Verdict

**`PASS / BOUNDED_DOCUMENTATION_WRITE_CAPABILITY_READY`**

**`CANONICAL_BOUNDED_DOCUMENTATION_WRITE = READY`**

Không thực hiện phi vụ đột biến Game Truyện; không deploy; không promote. Nhiệm vụ dừng ở đây.
