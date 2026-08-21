# BÁO CÁO CHỦ SỞ HỮU — P2P-BOUNDED-DOCUMENTATION-WRITE-01B

**Chủ đề:** Khép kín hai seam ngữ nghĩa cuối — ROLE PROVISION SEMANTICS + MUTATION-READY HOST AUTHORITY FINALIZATION
**Ngày:** 2026-08-21 (múi giờ GMT+7) · **Tác giả:** Manus AI
**Báo cáo:** 25 mục theo yêu cầu §19

---

## 1. Starting HEAD

Khôi phục trạng thái thật bắt đầu từ HEAD `0496e4c` trên nhánh `p2p-fw01-bootstrap-reconciliation`, với LOCAL == REMOTE và worktree sạch. HEAD trước khi triển khai chính là trạng thái `.39` (mã nguồn `587e81a`), khớp hoàn toàn với kỳ vọng của spec.

## 2. Trạng thái ứng viên `.39`

`.39` được xác minh **UNPROMOTED**, SHA `a21d8122a29146970889499dd74ad1fe0eb7be51491f7481cce62132ce82ed69`, nguồn `587e81a306e62ac96611f826c7ddc5c298eac1`, tree `980b19b`. Đây là ứng viên bất biến: không được ghi đè, không được xây lại, không bị chạm trong toàn bộ goal này.

## 3. Ngữ nghĩa REQUIRES

Kiểm tra cơ học registry + mã xác nhận: `REQUIRES` là **ROLE_DEPENDENCY** — tập năng lực/điều kiện tiên quyết mà vai *cần* để thực hiện nhiệm vụ (provenance, quyền được phép dùng). REQUIRES **không bao giờ** được thăng cấp thành bề mặt cung cấp của vai.

## 4. Ngữ nghĩa PROVIDES

`PROVIDES` là cơ chế cung cấp tường minh tối thiểu được đưa vào: tập năng lực nhiệm vụ mà vai *được phép thỏa mãn khi được chứng nhận*. Một vai không có `PROVIDES` cho năng lực X thì không cung cấp X — bất kể tên vai, REQUIRES, văn bản AUTHORITY, tư cách quorum hay backend capability. Thiếu/không rõ PROVIDES → fail-closed: **vai không cung cấp năng lực đó**.

## 5. Conflation có tồn tại hay không

Kiểm tra thực tế: registry role không chứa bất kỳ trường `PROVIDES` nào; checker quyền `_g1_authority_chain_check` đọc `REQUIRES` làm "provides"; FW03 `role_capability_evidence` kết hợp `CAPABILITY_ID + REQUIRES` thành tập năng lực do vai cung cấp; trong khi báo cáo/sổ cái BW01A tuyên bố "p2p_architecton PROVIDES bounded_documentation_write" còn triển khai chỉ ghi `REQUIRES: [bounded_documentation_write]`.

> **`ROLE_PROVISION_SEMANTIC_CONFLATION = CONFIRMED`** — với bằng chứng registry + checker + FW03 nêu trên.

## 6. Hiệu chỉnh lược đồ/thời gian chạy

Hiệu chỉnh fail-closed, không thiết kế lại BW01, không mở rộng quyền đột biến: (a) `capabilities.json` — vai `p2p_architecton` thêm `PROVIDES: ["bounded_documentation_write"]` (bằng chứng tối thiểu, không chạm vai/record khác); (b) `team_intelligence.py` — `role_capability_evidence` chỉ phát evidence row cho năng lực trong PROVIDES, `build_team_decision` tính PROVIDE-set từ các row PROVIDES; (c) `role_receipt.py` — bước mới `role_explicitly_provides_capability` trong chuỗi quyền; (d) `bounded_documentation_write.py` — hằng số chính tắc `MUTATION_AUTHORITY_MODES`, validation fail-closed, evidence mang `mutation_authority_mode`; (e) `role_bridge.py` — dispatch chuyền mode chính tắc, bắt HostAttestation thật cho MUTATION_READY; (f) fixture FW03 hòa hợp về ngữ nghĩa tường minh (41/41 PASS).

## 7. Vai chính tắc được chọn

**SELECTED_CANONICAL_ROLE_ID = `p2p_architecton`** — được đánh giá lại hoàn toàn cơ học trên toàn bộ 8 vai chính tắc, không giả định kết quả cũ, không loại trừ iris theo ý chí trước đó.

## 8. Bằng chứng chọn vai

Quét `PROVIDES` trên registry: chỉ `p2p_architecton` tuyên bố cung cấp `bounded_documentation_write`; 7 vai còn lại (gồm `p2p_iris`) không có PROVIDES cho năng lực này → không cung cấp. Kiến thức chứng nhận subject-bound, chứng nhận target đột biến và HostAttestation thật đều ràng buộc về architecton; boundary quyền WRITE_BOUNDED được cấp qua role contract; nguyên tắc minimum-privilege xác nhận architecton là vai duy nhất và tối thiểu đủ điều kiện.

## 9. PROVIDES tường minh của vai

Registry record architecton: `PROVIDES: ["bounded_documentation_write"]` — duy nhất một năng lực, bằng chứng-backed, đúng lượng tối thiểu. Không tự động copy REQUIRES → PROVIDES; các vai/record khác không đổi.

## 10. Chứng nhận subject-bound

Chứng nhận theo sau PROVIDES (chứng nhận không thể "sản xuất" provision): ROLE_CAPABILITY_CERTIFICATION + BACKEND_CERTIFICATION trong ledger `authority_chain_registry`, với subject = ROLE_ID/ADAPTER_ID, scope `DOCUMENTATION_MUTATION_BOUNDED`, quyền `WRITE_BOUNDED`, OWNER_AUTHORIZATION_ID, và kiểm freshness/lifetime. Hàng J (role cert hết hạn) và hàng K (target cert hết hạn) trong ma trận đều → BLOCK.

## 11. Ánh xạ capability → execution scope

Registry-backed và nguyên vẹn: `bounded_documentation_write → DOCUMENTATION_MUTATION_BOUNDED` qua trường `EXECUTION_SCOPE` của record registry + `CAPABILITY_EXECUTION_SCOPE_MAP` trong `backend_contract.py`; ánh xạ registry ưu tiên module map; mapping không rõ → **BLOCK cứng** (hàng I ma trận xác nhận). Không suy diễn từ chuỗi ký tự.

## 12. Target

Target thật trong proof: adapter `p2p-manus-orchestration` trên host fixture biệt lập (disposable Git fixture `/tmp/bw01b-*`), môi trường ISOLATED_NON_PRODUCTION — vẫn mutation-ready hợp lệ vì có chứng nhận đột biến và HostAttestation thật. Hàng H: target cert READ_ONLY → BLOCK.

## 13. Chứng nhận target mutation

Chứng nhận mutation target mới cho `DOCUMENTATION_MUTATION_BOUNDED`, ràng buộc đúng adapter thật, host thật, môi trường biệt lập, quyền WRITE_BOUNDED, bằng chứng tươi (lifetime_days=90, not-after tươi). READ_ONLY_CERTIFICATION != MUTATION_CERTIFICATION được duy trì.

## 14. Các mode quyền đột biến

Hằng số chính tắc `MUTATION_AUTHORITY_MODES = ("MUTATION_READY", "TEST_ONLY")` trong `bounded_documentation_write.py`; đầu vào không chính tắc → lỗi fail-closed. Mode được mang trong evidence, khối `authority` của receipt, và kiểm bởi verifier (`mutation_authority_mode_is_canonical`, `mutation_authority_mode_is_mutation_ready`, `test_only_evidence`).

## 15. Yêu cầu HostAttestation thật

Yêu cầu khóa theo **authority mode**, không theo môi trường: mọi thực thi MUTATION_READY (kể cả ISOLATED_NON_PRODUCTION) đòi hỏi đối tượng HostAttestation thật đầy đủ — HOST_KIND, HOST_EXECUTION_IDENTITY, ADAPTER_ID, TARGET_ID, RUN_ID, DISPATCH_ID, EXECUTION_ID, CONTRACT_DIGEST, WORKSPACE, CANDIDATE_SHA, ATTESTED_AT, ATTESTATION_FINGERPRINT. Derived ID không rỗng là chưa đủ; không có attestation → BLOCK. Hàng E/F/G ma trận đều → BLOCK.

## 16. Hành vi TEST_ONLY

`TEST_ONLY` không bao giờ escalade: evidence derived/synthetic chỉ chấp nhận khi `test_only_evidence=true`, và không thể thỏa `MUTATION_READY` / `OWNER_AUTHORIZED_MUTATION` / `REAL_MUTATION_VERIFIED` dù bất kỳ đầu vào nào. `TEST_ONLY_ATTESTATION != MUTATION_AUTHORITY_ATTESTATION` được đảm bảo cấu trúc — mọi nỗ lực tái sử dụng evidence TEST_ONLY cho dispatch mutation-ready → BLOCK.

## 17. Chứng minh dương M0/M1/M2

Trên fixture Git dùng một lần (đường nối full canonical path: Owner fixture authorization → FW02 → primitive → FW03 → PROVIDES tường minh → role cert subject-bound → target mutation cert → WRITE_BOUNDED → RoleExecutionContract → MUTATION_READY → HostAttestation thật → dispatch chính tắc → đúng một đột biến tài liệu → receipt → whole-claim verifier → FW04 QUALITY_VERIFIED → FW05 → FW06 → rollback): **M0 → M1 != M0 → một file thay đổi → VERIFIED → rollback → M2 == M0**.

## 18. Receipt/verifier

`verify_bounded_mutation_receipt` + `_g1_authority_chain_check` kiểm 9 liên kết chuỗi quyền (role_selected, role_explicitly_provides_capability, subject_bound, scope_mapping, target_cert_current, authority_mode chính tắc & MUTATION_READY, real_host_attestation, attestation_matches_evidence, contract/dispatch binding) và bảng 16 cờ whole-claim gồm `CHANGED_FILE_COUNT = 1`, `UNAUTHORIZED_CHANGED_SURFACE = 0`, `QUALITY_VERIFIED`. Bất kỳ cờ nào false/unknown → overall = false.

## 19. Ma trận tiêu cực

14 hàng A–N đều thực thi đúng kỳ vọng: A REQUIRES-only → BLOCK; B PROVIDES không có cert → BLOCK; C có cert nhưng vai không PROVIDES → BLOCK; D tên vai gợi ý năng lực → BLOCK; E TEST_ONLY attestation cho mutation-ready → BLOCK; F NON_PRODUCTION không có attestation thật → BLOCK; G attestation tổng hợp → BLOCK; H cert READ_ONLY → BLOCK; I scope sai → BLOCK; J role cert hết hạn → BLOCK; K target cert hết hạn → BLOCK; L Owner authorization lệch → BLOCK; M chuỗi đầy đủ → VERIFIED; N rollback chính xác → VERIFIED.

## 20. Hồi quy

BW01 (46) + BW01A (26) + BW01B (22) + toàn bộ suite = **357 tests PASS**, 0 thất bại; framework validator 78/78; development-control PASS; doctor HEALTHY trên cây tươi; secret scan (gitleaks) 0 leak mới; **NEW_UNEXPLAINED_FAILURES = 0**. FW03 hòa hợp PROVIDES tường minh: 41/41 PASS.

## 21. Hiệu chỉnh sổ cái

Sổ cái kiến trúc được cập nhật bằng **Phụ lục B** (version 1.2.0) — dạng addendum/provenance, không xóa chữ lịch sử. Phụ lục tuyên bố tường minh: `ROLE_DEPENDENCY != ROLE_PROVIDED_CAPABILITY` và `REAL HOST ATTESTATION IS REQUIRED FOR ANY MUTATION_READY EXECUTION, INCLUDING ISOLATED NON-PRODUCTION PILOTS`; mọi ngôn ngữ "REQUIRES nghĩa là PROVIDES" và "production-only real HostAttestation" được sửa.

## 22. Tác động ứng viên

Thời gian chạy được đóng gói thay đổi → cần ứng viên kế nhiệm. `.39` vẫn bất biến (UNPROMOTED, không chạm); `.38` không đổi; chỉ `.40` mới được đúc. Không deploy, không promote/release.

## 23. Ứng viên kế nhiệm

Ứng viên tích lũy kế nhiệm DUY NHẤT: **`8.4.7-C-codex.40`** — SHA `f2edabf09de2657b63ad930636599295e96d94d0eea47fc91e14081c7e600519`, UNPROMOTED, self-contained, source-bound `a1e78bc378d8efe65840ec7c3d23ded121284759` (tree `3bb25bff`), fresh-tree verified (extract + doctor + presence FW05/FW06/BW01/BW01A/BW01B + smoke, ALL PASS), doctor HEALTHY. Dòng dõi `.35.. .40` liên tiếp, tất cả UNPROMOTED, mỗi record ghim đúng một artifact SHA.

## 24. Các NOT_PROVEN còn lại

1. Chứng nhận registry vẫn là lớp tự khẳng định trong runtime — chưa có cơ quan chứng nhận bên ngoài được xác thực.
2. Pilot đột biến Game Truyện thật thứ hai chưa thực hiện — vẫn là quyết định Owner.
3. Nhánh derived-ID TEST_ONLY còn tồn tại nhưng chỉ khả dụng trong mode TEST_ONLY (fail-closed cấu trúc, không escalade).

## 25. Quyết định Owner tiếp theo chính xác

**Approve or reject Game Truyện isolated documentation mutation pilot 02 using the new candidate.**

---

## VERDICT

**`PASS / BOUNDED_MUTATION_ROLE_HOST_SEMANTICS_FINALIZED`**

```
CANONICAL_BOUNDED_MUTATION_ROLE_HOST_SEMANTICS = VERIFIED
```

Next Owner decision: *Approve or reject Game Truyện isolated documentation mutation pilot 02 using the new candidate.* — DỪNG tại đây.
