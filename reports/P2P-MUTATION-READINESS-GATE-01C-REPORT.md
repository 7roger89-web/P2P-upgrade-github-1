# BÁO CÁO CUỐI GATE-01C — ĐÓNG KHỚP NGUỒN GỐC TRƯỚC ĐỘT BIẾN (FINAL PRE-MUTATION PROVENANCE CLOSURE)

**Nhánh:** `p2p-fw01-bootstrap-reconciliation` · **Ngày:** 2026-08-20 (UTC) · **Tác giả:** Manus AI
**Bối cảnh:** GATE-01B đã kết thúc với kết quả PASS nhưng để lại bốn lỗ hổng ngữ nghĩa: (1) bản khai candidate chưa được buộc vào biên lai thô, (2) `source_repository_id` chưa ổn định — không rỗng, (3) mâu thuẫn định danh runtime `EXECUTED_RUNTIME != DECLARED_CANDIDATE_RUNTIME` (bản runtime thực thi 4063c4 khác byte với bản runtime khai báo .36 fe090e8), (4) ngữ nghĩa phát lại (replay) của attestation còn mơ hồ giữa "tự quan sát" và "xung đột phát lại". GATE-01C khép toàn bộ bốn lỗ hổng này, mint đúng MỘT candidate kế nhiệm .37, chứng minh READ_ONLY bằng bản runtime **cài từ artifact** trên bản sao Game Truyện cô lập, và xác minh toàn-claim 17 trường.

---

## 1. FINAL HEAD

```
04e91df519a787fe15c24991f1d064bd7e0d41e7  (HEAD, remote origin đã đồng bộ)
HEAD^{tree} = 4107563421d5f388fa6f344b87a6ce590eb06a46
```

Worktree sạch, `LOCAL HEAD == REMOTE HEAD`, không có thay đổi cục bộ chưa đẩy.

## 2. IMPLEMENTATION COMMIT (commit triển khai GATE-01C)

```
d1a88fceac3eb3877eb9d7b642babc53fca1195b
```

Commit này chứa toàn bộ thay đổi runtime: buộc định danh candidate vào biên lai, trường `source_repository_id` ổn định, tách ngữ nghĩa replay (self-observation vs conflict), trình thẩm định toàn-claim 17 trường, và cập nhật bộ kiểm thử tương ứng. Cây mã tại commit: `61b4be97b25f28ca5502f6f0e6d31243c55ee823`.

## 3. REPORT COMMIT (commit báo cáo này)

```
04e91df519a787fe15c24991f1d064bd7e0d41e7
```

Report này được gửi kèm commit cuối của nhánh, cùng các commit GATE-01C trung gian: `d1a88fc` (runtime binding), `3bc4d5c` (candidate .37, governance, verify script), `04e91df` (regression fixes, khôi phục hồ sơ .36, gitleaks baseline không đổi).

## 4. CANDIDATE VERSION

`8.4.7-C-codex.37` — candidate kế nhiệm duy nhất, `UNPROMOTED`, `candidate_id = FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE`. Chỉ có đúng MỘT cặp UNPROMOTED liên tiếp (.36 → .37) tồn tại trong `governance/development-control.json`; hồ sơ .35 được giữ nguyên để bảo toàn lịch sử, và hồ sơ .36 bị vượt qua (superseded) đã được khôi phục kèm artifact gốc để không xóa lịch sử.

## 5. CANDIDATE SHA

| Hạng mục | Giá trị |
|---|---|
| `candidate_sha256` (khai báo trong governance) | `4aafdcd383b1002842df2465cfd3ce5f4bb3d9d792ce75ad5000771e629640f7` |
| SHA-256 quan sát trực tiếp trên byte artifact zip | `4aafdcd383b1002842df2465cfd3ce5f4bb3d9d792ce75ad5000771e629640f7` |
| Artifact | `reports/candidates/P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip` |

Khai báo == byte thực tế. Trình thẩm định xác minh độc lập: `candidate_artifact_bytes: true`, `candidate_artifact_observed_sha256` khớp.

## 6. CANDIDATE SOURCE COMMIT / TREE (khai báo của .37)

| Hạng mục | Giá trị |
|---|---|
| `source_commit` | `d1a88fceac3eb3877eb9d7b642babc53fca1195b` |
| `source_tree_hash` | `61b4be97b25f28ca5502f6f0e6d31243c55ee823` |

Đây chính là commit triển khai GATE-01C — candidate được xây từ đúng cây mã mà runtime bên trong nó thể hiện.

## 7. EXECUTED SOURCE COMMIT / TREE (runtime thực thi trong proof)

| Hạng mục | Giá trị |
|---|---|
| Runtime thực thi (`freshness.source_commit`) | `d1a88fceac3eb3877eb9d7b642babc53fca1195b` |
| Runtime thực thi (`freshness.source_tree_hash`) | `61b4be97b25f28ca5502f6f0e6d31243c55ee823` |
| Dự án mục tiêu (`freshness.project_commit`, cây HEAD tại thời điểm proof) | `c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b` |

Kết quả từ §4 (GATE-01B): tại GATE-01B, ba bản byte `role_receipt.py` của .36 (780a1bb5), HEAD (562b8bbe) và 4063c4 (1a175b85) là **ba bản khác nhau** — `EXECUTED_RUNTIME != DECLARED_CANDIDATE_RUNTIME`. GATE-01C đã khắc phục bằng cách mint .37 từ runtime của đúng commit `d1a88fc`; tại proof, `EXECUTED_RUNTIME == DECLARED_CANDIDATE_RUNTIME` xác nhận byte-đối-byte: trình thẩm định trả về `source_commit_exact: true`, `source_tree_exact: true`, `runtime_manifest_exact: true`. Lỗ hổng 4063c4 vs fe090e8 **đóng**.

## 8. SOURCE REPOSITORY ID

```
repo-p2p-auth-f01-ea2457ef68ab457e5a436f044d1fee64e78fd38c97485adb
```

Định danh ổn định được tạo bởi `canonical_source_repository_id()` (SHA-256 của repo handle + commit root + remote URL). Giá trị khai báo trong biên lai khớp chính xác giá trị tái phái sinh tại thời điểm thẩm định (`source_repository_id_consistent: true`), không rỗng, không phải đường dẫn thô. Lỗ hổng liên kết kho mã nguồn **đóng**.

## 9. INSTALLED RUNTIME MANIFEST DIGEST

```
4d0627d92e602184462515035406b51235912f5e9d16e37f02f903fa7dddffbd
```

Được tái phái sinh tại thời điểm build và tại thời điểm thẩm định từ cùng một file `governance/runtime-manifest.lock.json` trên cùng bề mặt cài đặt (`runtime_manifest_exact: true`).

## 10. CANDIDATE RUNTIME MANIFEST DIGEST

```
4d0627d92e602184462515035406b51235912f5e9d16e37f02f903fa7dddffbd
```

Giống hệt mục 9 — bản runtime bên trong artifact .37 thể hiện chính xác bề mặt manifest đã khai báo. Candidate, runtime và biên lai cùng chỉ ra **một byte duy nhất**.

## 11. RECEIPT CANDIDATE BINDING

Khối `candidate` được buộc trực tiếp vào biên lai thô tại thời điểm build (không phải hậu bổ sung):

| Trường | Giá trị kiểm chứng |
|---|---|
| `candidate_version` | `8.4.7-C-codex.37` (khớp governance) |
| `candidate_id` | `FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE` |
| `candidate_sha256` | `4aafdc...640f7` == byte artifact thực tế |
| `candidate_artifact` | đường dẫn artifact trong dự án |
| `source_commit` / `source_tree_hash` | khớp runtime thực thi (mục 7) |
| `runtime_manifest_digest` | khớp mục 9/10 |
| `candidate_governance_record` | `true` (khớp record UNPROMOTED mới nhất cùng id) |
| `receipt_to_candidate_binding` | `true` |

Hỗ trợ: `canonical_source_repository_id()` phái sinh định danh kho ổn định, được lưu vào biên lai.

## 12. TARGET ELIGIBILITY

`eligible: true`, `status: "CURRENT_EXACT_REVISION"`, `all_source_bounds_current: true`, `embedded_target_consistent: true`. Khả năng `non_mutating_project_analysis` có chứng chỉ nguồn ràng buộc hợp lệ, hiện hành, khớp đúng bản revision đang thực thi trên mục tiêu `p2p-manus-orchestration`.

## 13. SOURCE FRESHNESS

`freshness_source_bound: true`. Nguồn ràng buộc được đánh giá tại thời điểm thẩm định từ registry chứng chỉ nguồn (bắt buộc `CERTIFIED`, khớp subject `p2p_iris`, khớp `source_commit` hiện hành, không hết hạn, khớp `project_commit` đúng cây dự án). Nguồn trôi (stale commit/tree) → BLOCK như đã chứng minh trong ma trận âm (mục 19, trường hợp E, F, I).

## 14. REPLAY SELF-OBSERVATION

Ngữ nghĩa replay đã được tách làm hai trường độc lập. Tại proof: `attestation_ledger_self_observed: true` — vân tay attestation được ghi vào sổ cái chính tắc đúng một lần tại thời điểm phát hành, bởi chính host thật (`host_identity_real: true`, `host_kind: "generic-real"`), `attestation_present: true`, `attestation_binds_ids: true`.

## 15. REPLAY CONFLICT

`replay_conflict_detected: false`. Vân tay chưa từng tồn tại trong sổ cái trước lần phát hành này. Cờ kế thừa `attestation_replay_detected` (ngữ nghĩa GATE-01B, "đã từng được ghi") vẫn hiển thị `true` vì bản thân lần tự quan sát được ghi; hai trường này được phân tách rõ: **tự quan sát lần đầu = cho phép, sử dụng lần hai = xung đột BLOCK**. Trường hợp G ma trận âm xác nhận sao chép vân tay → conflict, và trường hợp H xác nhận phát hành tươi một lần → VERIFIED. Lỗ hổng ngữ nghĩa replay **đóng**.

## 16. RECEIPT / VERIFIER RESULT (toàn-claim 17 trường)

Biên lai `p2p-role-receipt/1`, `receipt_id = 5c664121e17076538122ecc16cb6e3bf7bece7bf2c1688cb91be1c053a46e476`, `run_id = 55a52119a75c3a940cfd60a8b06bd3d302b28419408519b3c7ce9c15f1af3c9d`, `attestation_fingerprint = a39b20dbb1e180b91ad31fd641ddde1d4d46b34e64e8901e4ff5464fb49a6145`.

Trình thẩm định toàn-claim trả về `overall: True` với toàn bộ 17 trường của đặc tả §6: `TARGET_ELIGIBLE`, `SOURCE_BOUND`, `SOURCE_REPOSITORY_ID` (không rỗng, nhất quán), `SOURCE_COMMIT`, `SOURCE_TREE`, `CANDIDATE_VERSION`, `CANDIDATE_SHA`, `CANDIDATE_MANIFEST`, `EXECUTED_RUNTIME_MANIFEST`, `RECEIPT_TO_CANDIDATE_BINDING`, `CONTRACT_TO_DISPATCH`, `DISPATCH_TO_RECEIPT`, `RECEIPT_IDENTITY`, `HOST_ATTESTATION_VALID`, `REPLAY_CONFLICT = false`, `TIMESTAMPS` (monotonic), `EVIDENCE_EXISTS`, `H1 == H2`, `APPLICATION_MUTATION = 0`.

## 17. H1 / H2

```
H1 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b
H2 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b
H1 == H2: true
```

Bản sao cô lập `/tmp/gt-iso-gate01c` được tạo tươi từ `cert/game-truyen` (HEAD `b0e6deb…` tại thời điểm proof), runtime được cài **từ artifact zip .37** (giải nén `system/` vào `.p2p/system/`, tuyệt đối không dùng PYTHONPATH phát triển), baseline H1 chụp sau khi cài đặt, H2 tái phái sinh từ cùng bề mặt đã cài. Cây bề mặt không đột biến trong toàn bộ phiên READ_ONLY.

## 18. APPLICATION MUTATION

`dispatch_possible_mutation: false`, `dispatch_changed_surface: []`, `application_mutation: 0`. Không có một byte nào của Game Truyện bị thay đổi; không chạm Gia Phả (zero mutation), không chạm Logistics (`DO_NOT_INSTALL_YET`), không triển khai, không khởi động Framework-07, không thiết kế lại FW00–FW06, không đổi ngữ nghĩa capability/team.

## 19. REGRESSION

| Hạng mục | Kết quả |
|---|---|
| Bộ kiểm thử toàn runtime (`unittest discover`, `.p2p/system`) | **263/263 PASS** (baseline 240 + 23 gate01 evidence) |
| Validator framework | **78/78 PASS** |
| `p2p_development_control.py validate` | **PASS** (kèm khôi phục hồ sơ .36 + artifact gốc, tail lineage `.35 → .36 → .37` hợp lệ) |
| Trình thẩm định artifact `.37` (fresh-tree) | **ALL FRESH-TREE CHECKS PASS** |
| Secret scan (gitleaks 8.21.2, `--no-git`) | 0 lỗ hổng mới — 2 cảnh báo false-positive có sẵn từ baseline, không đổi |
| Ma trận âm A–J (`closure_06c_gate01c_negative.py`, runtime cài từ artifact) | A (thiếu SHA) BLOCK · B (SHA sai) BLOCK · C (manifest lệch) BLOCK · D (repo id rỗng) BLOCK · E (source commit sai) BLOCK · F (source tree sai) BLOCK · G (xung đột phát lại) BLOCK · H (tự quan sát tươi) **VERIFIED** · I (không đủ tư cách) BLOCK · J (chuỗi READ_ONLY sạch) **VERIFIED** — `GATE01C_NEGATIVE_MATRIX=PASS` |
| Proof READ_ONLY (`closure_05c_gate01c.py`, runtime cài từ artifact) | `overall: True`, 17/17 trường |
| `NEW_UNEXPLAINED_FAILURES` | **0** |

## 20. MUTATION_EVIDENCE_CHAIN_READY

```
MUTATION_EVIDENCE_CHAIN_READY = YES
```

Candidate, nguồn, runtime thực thi và biên lai đều chỉ ra chính xác cùng một tập byte; định danh kho nguồn ổn định và không rỗng; ngữ nghĩa replay được tách bạch không mơ hồ; trình thẩm định toàn-claim 17 trường xác nhận toàn bộ chuỗi trên bản runtime cài từ artifact trong môi trường cô lập; toàn bộ kiểm tra hồi quy đạt; không có lỗi bất thường chưa giải thích.

## 21. EXACT OWNER ACTION

**Verdict cuối:**

```
PASS / MUTATION_EVIDENCE_PROVENANCE_FINALIZED
```

Hành động tiếp theo duy nhất và chính xác:

```
OWNER MAY APPROVE ONE LOW-RISK NON-PRODUCTION MUTATION PILOT ON ISOLATED GAME TRUYỆN.
```

Dừng ở đây. Không tự động khởi chạy pilot, không quảng bá/nhánh phát hành candidate, không chạm Gia Phả, không chạm Logistics, không triển khai.

---

*Báo cáo này thay thế GATE-01B-REPORT làm tài liệu chứng cứ cuối cùng cho phiên bản hiện hành của chuỗi chứng cứ P2P. Biên lai proof gốc được lưu tại `pilot_gt_receipts/gate01c_receipt_debug.json` và đầu ra thẩm định đầy đủ tại `pilot_gt_receipts/gate01c_verifier_full.json`; trình điều khiển proof tại `closure_05c_gate01c.py` và ma trận âm tại `closure_06c_gate01c_negative.py` (dưới thư mục làm việc của dự án).*
