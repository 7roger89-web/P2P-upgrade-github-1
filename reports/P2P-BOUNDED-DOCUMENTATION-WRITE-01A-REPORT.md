# BÁO CÁO CHỦ SỞ HỮU — P2P-BOUNDED-DOCUMENTATION-WRITE-01A

**CHUỖI QUYỀN ĐỘT BIẾN: ROLE × TARGET × HOST — KHÉP KÍN TOÀN BỘ (AUTHORITY-CHAIN CLOSURE)**

Tác giả: Manus AI · Ngày: 21/08/2026 · Chế độ: một mục tiêu khép kín bounded P2P nhỏ, KHÔNG phải Framework-07.

Verdict cuối: **PASS / BOUNDED_MUTATION_AUTHORITY_CHAIN_READY**

---

## 27 mục báo cáo (đã đủ 27)

**Mục 1 — HEAD khởi điểm.** HEAD khởi điểm được khôi phục cơ học và xác minh: `294b4fb` (nhánh `p2p-fw01-bootstrap-reconciliation`, LOCAL == REMOTE, worktree sạch). Ứng viên `.38` tại trạng thái khởi điểm là `UNPROMOTED`, SHA `d062ec5c4f8d2cb264c0b405de5236850d53d04757e264d871cf12395b0ec253`, source-bound `a6d2c33`/`1ff1b54c` — khớp hoàn toàn với kết quả của P2P-BOUNDED-DOCUMENTATION-WRITE-01; không có đột biến nào trên `.38`.

**Mục 2 — Trạng thái .38.** `.38` được tuyên bố **bất biến** và được giữ nguyên đúng như vậy: không sửa, không đóng gói lại, không thúc đẩy. Nó vẫn là bản ghi `UNPROMOTED` trong `governance/development-control.json` và artifact zip của nó không chạm vào. Mọi thay đổi runtime mới đều nằm trên nền commit kế thừa và được đóng gói vào ứng viên kế nhiệm duy nhất `.39`.

**Mục 3 — Vai chính tắc được chọn chính xác.** Vai tối thiểu phù hợp được chọn bằng kiểm tra cơ học trên cả 8 vai chính tắc (dựng role spec, so `AUTHORITY`/approval boundary với bề mặt tài liệu đột biến): **`p2p_architecton`**. `p2p_iris` bị loại trừ đúng ràng buộc của Chủ sở hữu. Không vai đọc-chỉ nào đáp ứng tiêu chí, và `architecton` là vai nhẹ nhất có boundary `protected-architecture-change` cùng tư cách quorum member.

**Mục 4 — Vì sao vai đó.** Lý do chọn `p2p_architecton` là tam chứng cơ học: (i) nó là vai duy nhất có approval boundary về thay đổi kiến trúc được bảo vệ — khớp ngữ nghĩa với đột biến tài liệu kiến trúc/tài liệu dự án; (ii) nó có tư cách thành viên quorum — khớp mô hình 8 vai quorum của Council; (iii) không vai nào nhẹ hơn mà vẫn hỗ trợ đột biến theo `AUTHORITY` hiện có. Việc thêm quyền đột biến vào một vai nặng hơn sẽ vi phạm nguyên tắc quyền tối thiểu; thêm vào vai đọc-chỉ sẽ mở quyền cho đúng loại vai cần cấm.

**Mục 5 — Liên kết PROVIDES của vai.** Liên kết hai chiều được đóng vào registry: (i) bản ghi registry của `p2p_architecton` trong `capabilities.json` được thêm `bounded_documentation_write` vào `REQUIRES` (vá tối thiểu 3 dòng, không tái-tuần-tự-hóa toàn bộ file — diff được xác minh); (ii) bản ghi registry của capability `bounded_documentation_write` mang trường `EXECUTION_SCOPE: DOCUMENTATION_MUTATION_BOUNDED` làm nguồn chính tắc. Verifier kiểm tra cả hai chiều: role-provides-capability và capability-scope-mapping.

**Mục 6 — Chứng nhận subject-bound.** Mô-đun mới `authority_chain_registry.py` lưu trữ ledger chứng nhận append-only tại `.p2p/state/authority_chain_registry.json` (đường dẫn theo `P2P_STATE_DIR`, cách ly từng fixture test). Hai loại bản ghi: `ROLE_MUTATION_CERTIFICATION` (gắn chính xác `role_id = p2p_architecton`, `capability_id`, scope `DOCUMENTATION_MUTATION_BOUNDED`, `permission_grant = WRITE_BOUNDED`, **`owner_authorization_id` trùng khớp tuyệt đối** với evidence, có expiry) và `BACKEND_MUTATION_CERTIFICATION` (gắn `target_id`, adapter, scope, trạng thái `MUTATION_TARGET_LIVE`). Chứng nhận khác scope bị từ chối append ngay ở tầng lưu — scope-locked bằng thiết kế.

**Mục 7 — Ánh xạ capability→execution-scope.** Ánh xạ tường minh fail-closed: registry `EXECUTION_SCOPE` của capability được ưu tiên làm nguồn chính tắc; ánh xạ module `CAPABILITY_EXECUTION_SCOPE_MAP` trong `backend_contract.py` chỉ là fallback khi capability vắng bóng khỏi bề mặt registry; capability không có ánh xạ nào → **BLOCK cứng** ngay tầng đánh giá eligibility. Trong BW01A, `evaluate_role_target_eligibility` ưu tiên registry và không bao giờ suy diễn scope từ tên capability.

**Mục 8 — Target được chọn.** Target đánh giá là target fixture kiểu `p2p-manus-orchestration` trên fixture Git dùng một lần mới (`ISOLATED_NON_PRODUCTION`, repo disposable tạo bằng `git init`, baseline tree `0310e5484dc8cf7cd1fbb02cfb4c67176d260f94`). Đây là level chứng nhận target duy nhất đúng phạm vi goal — target production thật vẫn NOT_PROVEN (mục 26).

**Mục 9 — Chứng nhận đột biến target.** Target fixture nhận `BACKEND_MUTATION_CERTIFICATION` với scope `DOCUMENTATION_MUTATION_BOUNDED`, trạng thái `MUTATION_TARGET_LIVE`, adapter-id đồng nhất với HostAttestation, và expiry tính từ `lifetime_days > 0`. Verifier kiểm tra chứng nhận hiện hành (`target_certification_current`) và phạm vi đúng target (`execution_scope_certified_for_target`); hết hạn → chuỗi quyền mở ngay cả khi mutation evidence hoàn hảo.

**Mục 10 — Quyền WRITE_BOUNDED.** `WRITE_BOUNDED` giữ nguyên thứ bậc `READ < WRITE_BOUNDED < WRITE` trong `PERMISSION_ORDER` (BW01), và bây giờ được **gắn chủ thể**: chứng nhận vai chỉ chấp nhận `WRITE_BOUNDED` làm `permission_grant`; grant `WRITE` trực tiếp bị `ValueError` ngay tầng chứng nhận, và receipt có class `WRITE` sẽ trượt khối evidence. Quyền đột biến không còn là grant mở cho mọi vai — nó chảy qua chứng nhận subject-bound duy nhất.

**Mục 11 — Ủy quyền Owner.** Mỗi chứng nhận vai mang `owner_authorization_id` và verifier yêu cầu nó trùng khớp byte-cho-byte với `evidence.owner_authorization_id` của mutation receipt (`owner_authorization_bound`). Id trống/khác → chuỗi quyền mở. Đây là khóa nối chữ ký Owner vào cả chứng nhận lẫn evidence, thay vì chỉ evidence như BW01.

**Mục 12 — HostAttestation thật.** Yêu cầu mới fail-closed tại `execute_bounded_document_mutation`: chế độ `mutation_authority_mode == PRODUCTION` bắt buộc một `HostAttestationRecord` thật do `make_canonical_host_attestation` tạo (có `run_id`, `dispatch_id`, `execution_contract_digest` thực) — id dẫn xuất từ cặp thực thi bị giới hạn cứng vào `TEST_ONLY` và không bao giờ đến được dispatch mutation-ready. `role_bridge.dispatch()` nhận `execute_bounded_write_host_attestation` và không xây dựng receipt mutation-ready khi không có. Receipt mang khối attestation thật (fingerprint, ledger state, replay conflict flag).

**Mục 13 — Trạng thái replay.** Attestation thật được kiểm replay qua `attestation_ledger_self_observed` và `attestation_replay_conflict`: replay conflict → `replay_conflict_detected = True`, chuỗi quyền mở (hàng tiêu cực L đã chứng minh). Ledger replay nằm trong `host_attestation` module hiện có, không thay đổi ngữ nghĩa BW01.

**Mục 14 — RoleExecutionContract.** Contract thực thi giữ nguyên 4 trường đột biến của BW01 (`possible_mutation`, `application_mutation`, `changed_file_count`, `changed_line_count`) và `constraint_fingerprint` SHA-256 bất biến với mọi thay đổi ràng buộc; BW01A chỉ bổ sung khối dispatch backend vào receipt (qua kwarg `backend` mới của `new_role_receipt`) và ba trường định danh thực thi `run_id`/`dispatch_id`/`role_execution_contract_digest` để verifier ràng buộc attestation với contract.

**Mục 15 — Dispatch.** Đường dispatch bounded trong `role_bridge.dispatch()` được khép kín hai chiều: (i) mutation-ready chỉ xây dựng khi có HostAttestation thật (kwarg mới, fail-closed khi vắng); (ii) receipt mang khối attestation thật được gắn sau evidence đột biến trên mọi đường có mutation. Đường READ_ONLY không bị ảnh hưởng (`receipt_attestation = None`, verifier trung lập không crash).

**Mục 16 — Receipt đột biến.** Verifier toàn-claim mới `verify_bounded_mutation_receipt` với `_g1_authority_chain_check` kiểm tra cơ học 9 liên kết trên cùng một receipt: role-selected, spec khớp registry, role-provides-capability, capability-scope-mapping-valid, execution-scope-certified-for-target, subject-bound-to-role, certification-current, attestation-real-and-matches-evidence, owner-authorization-bound; kết quả tổng hợp `authority_chain.overall` độc lập với nhánh evidence đột biến — evidence hoàn hảo nhưng chuỗi quyền mở vẫn trả về `overall = False`.

**Mục 17 — Fixture dương M0/M1/M2.** Chu trình sống đầy đủ trên fixture Git dùng một lần mới: **M0** — cây baseline sạch (tree `0310e548…`), chứng nhận target + vai + attestation thật được đăng ký, eligibility `eligible == True`; **M1** — đột biến 38 byte vào 1 file tài liệu (`docs/…`), evidence `changed_file_count == 1`, `dispatch_consistent`, receipt toàn-claim PASS (authority_chain.overall = True, overall = True); **M2** — rollback khôi phục byte gốc, cây trả về đúng baseline (`FINAL_TREE_HASH == PRE_MUTATION`), và kịch bản crash-giữa-chừng cho quyết định retry `MUTATION_UNVERIFIED_NO_REWRITE` đúng thiết kế.

**Mục 18 — Chất lượng FW04.** `evaluate_bounded_document_mutation_quality` được gọi trong chu trình M1 và tất cả các tiêu chí chất lượng (delta hash, lớp đột biến chính tắc, byte dương, đường dẫn chính tắc) đều PASS; chất lượng không được tính nếu chuỗi quyền mở — nó là lá cờ cuối, không phải lá cờ đầu.

**Mục 19 — Tầm nhìn Owner FW05.** `build_bounded_mutation_owner_summary` vẫn được phát trong receipt (FW05 không bị suy yếu); Owner thấy đúng 1 file, 38 byte, đường dẫn tài liệu, trạng thái rollback REQUIRED và chuỗi quyền đã đóng — trước khi quyết định pilot thật.

**Mục 20 — Phục hồi FW06.** Lease FW06 (`max_parallelism = 1`) và marker ngắt quãng giữa write-verify được giữ nguyên; crash-giữa-chừng trả `MUTATION_UNVERIFIED_NO_REWRITE` thay vì retry ngầm; rollback không bao giờ best-effort (thất bại → raise).

**Mục 21 — Ma trận tiêu cực.** Ma trận tiêu cực đầy đủ **A–O** (15 hàng) trên fixture Git dùng một lần, mỗi hàng phá đúng một liên kết của chuỗi quyền và mọi hàng đều fail-closed đúng thiết kế:

| Hàng | Liên kết bị phá | Kết quả fail-closed |
|---|---|---|
| A | Không chứng nhận target | `authority_chain.overall = False` |
| B | Chứng nhận target hết hạn | `target_certification_current = False` |
| C | Target chứng nhận sai adapter | `execution_scope_certified_for_target = False` |
| D | Không chứng nhận vai | `subject_bound = False` |
| E | Vai khác giữ chứng nhận | `subject_bound = False` |
| F | `owner_authorization_id` sai | `subject_bound = False` |
| G | Scope khác (kiến tạo bất khả — layer khóa scope) | chuỗi mở vì vắng chứng nhận hợp lệ |
| H | Grant `WRITE` thay `WRITE_BOUNDED` | `ValueError` tầng chứng nhận + evidence mismatch |
| I | Vắng khối attestation | `attestation_present = False`, failure cứng |
| J | Fingerprint attestation tổng hợp | `host_identity_real = False` |
| K | Fingerprint ≠ neo evidence | `attestation_matches_evidence = False` |
| L | Replay conflict | `replay_conflict_detected = True` |
| M | Drift cây baseline (h1 ≠ h2) | `h1_equals_h2 = False`, không identity-locked |
| N | Registry vai ngừng PROVIDES | `role_provides_capability = False` |
| O | Capability mất EXECUTION_SCOPE | `capability_scope_mapping_valid = False`, BLOCK cứng |

**Mục 22 — Hồi quy đầy đủ.** Bộ 335 test PASS (309 hồi quy + 26 test BW01A mới, bao gồm 3 chu trình dương, crash-retry, 15 hàng tiêu cực, scope-mapping, role-selection); framework 78/78; dev-control validate PASS (cặp .38→.39 liên tục UNPROMOTED); verifier fresh-tree `.39` ALL PASS (doctor --package, manifest-checksum, hiện diện BW01A gồm authority verifier); gitleaks chỉ 3 false-positive đã biết từ trước, **NEW_UNEXPLAINED_FAILURES = 0**.

**Mục 23 — Cập nhật sổ cái.** Sổ cái kiến trúc bền vững `docs/bounded-documentation-write-capability-ledger.md` được bổ sung phụ lục A (v1.1.0): ngữ nghĩa 4 liên kết, provenance commit `587e81a`, bảng ma trận A–O, và hạn chế đã biết (ledger không chữ ký mật mã, scope-locked, pilot thật chưa thực hiện).

**Mục 24 — Ảnh hưởng ứng viên.** `.38` bất biến không đổi. Runtime thay đổi 7 module + 2 file mới (`authority_chain_registry.py`, bộ test 26 case), 1489 dòng thêm / 16 dòng sửa, tất cả cộng tính — không module nào bị gỡ hoặc suy yếu. Do `DECLARED_CANDIDATE_RUNTIME == EXECUTED_RUNTIME` bắt buộc, ứng viên đóng gói phải được xây lại từ HEAD mới.

**Mục 25 — Ứng viên kế nhiệm duy nhất.** Đã đúc chính xác MỘT ứng viên kế nhiệm: **`8.4.7-C-codex.39`** — `a21d8122a29146970889499dd74ad1fe0eb7be51491f7481cce62132ce82ed69`, trạng thái **UNPROMOTED**, source-bound commit `587e81a306e62ac9661c11f826c7ddc5c298eac1` / tree `980b19b5fbc209deca5bac99894a7ebdd0ace0ff`, bản ghi governance mới với `lineage_anchor_note` giải thích đầy đủ lý do xây lại, và fresh-tree verifier ALL PASS. Chuỗi tích lũy `.35/.36/.37/.38/.39` tuân quy tắc GATE-01B mở rộng (mỗi bản ghi ghim đúng một artifact SHA, liên tục, tất cả UNPROMOTED) — không có ứng viên thứ hai nào được tạo.

**Mục 26 — Các mục còn NOT_PROVEN.** (i) Chứng nhận target đột biến trên host Git production thật — mới chứng nhận ở level fixture; (ii) Tích hợp chữ ký Owner production (authorization id hiện là fixture); (iii) Quyết định promotion Council 8/8 — không chạy theo yêu cầu; (iv) Binding adapter-id target tới host thật ở production — fixture-level; (v) Rollback chỉ được chứng minh ở fixture, không trên Game Truyện thật; (vi) Phi vụ đột biến Game Truyện lần hai **không được thực hiện** trong goal này. Không đột biến nào xảy ra trên Game Truyện chính quyền (ZERO mutation), Gia Phả (ZERO), Logistics (DO_NOT_INSTALL_YET).

**Mục 27 — Quyết định tiếp theo của Chủ sở hữu.**

```
CANONICAL_BOUNDED_MUTATION_AUTHORITY_CHAIN = VERIFIED
```

Next Owner decision: **Approve or reject Game Truyện isolated documentation mutation pilot 02 using the new candidate.**

Sau đó DỪNG.

---

*Báo cáo này là mục tiêu khép kín duy nhất; primitive BW01 không bị thiết kế lại; không cánh cổng fail-closed hiện có nào bị suy yếu.*
