# Báo cáo chủ sở hữu cuối kỳ — P2P-MUTATION-READINESS-GATE-01

**Ngày:** 2026-08-20 (UTC+7)
**Nhánh:** `p2p-fw01-bootstrap-reconciliation` · **HEAD mới:** `ceb0e13a65463d9c6c691cbdf002881136e39c8a`
**Tác vụ:** Đóng các khe hở toàn vẹn bằng chứng (evidence-integrity seams) tìm thấy trong lần dispatch chuẩn mực READ_ONLY đã xác minh thành công (CLOSURE-01), chứng minh lại một lần thực thi READ_ONLY chuẩn mực FRESH trên bản sao Game Truyện cô lập, chạy hồi quy đầy đủ và ma trận phủ định, phát hành MỘT gói candidate lũy kế kế nhiệm UNPROMOTED, và trình bày báo cáo terminal 29 mục bằng tiếng Việt.
**Khối lệnh tuyệt đối:** KHÔNG khởi động mutation pilot, KHÔNG promote/release bất kỳ candidate nào, KHÔNG chạm Gia Phả (zero mutation), KHÔNG chạm Logistics (DO_NOT_INSTALL_YET), KHÔNG deploy, KHÔNG chạy lại Council 8/8, KHÔNG phục sinh C36 lịch sử, KHÔNG bắt đầu Framework-07.

---

## Phán quyết terminal (verdict)

> **PASS / MUTATION_EVIDENCE_CHAIN_READY_FOR_OWNER_GATE**
>
> `MUTATION_EVIDENCE_CHAIN_READY = YES`
>
> **DỪNG.** KHÔNG tự động khởi động mutation pilot.

---

## Mục 1. Starting HEAD

- HEAD khởi điểm của nhánh: `0bc22b1` — commit "P2P-CAPABILITY-DISPATCH-CLOSURE-01: final owner report (Vietnamese, 27 items)" — điểm kết thúc của CLOSURE-01 với biên lai READ_ONLY chuẩn mực đã xác minh (`CANONICAL_REAL_READ_ONLY_ROLE_DISPATCH = VERIFIED`).
- HEAD sau khi hoàn tất GATE-01: `ceb0e13a65463d9c6c691cbdf002881136e39c8a` (đã push lên remote `origin` của nhánh `p2p-fw01-bootstrap-reconciliation`; tiến trình `0bc22b1..ceb0e13`, 15 tệp, 2000 dòng thêm, 22 dòng sửa).

## Mục 2. Current cumulative candidate / version / SHA

- Gói candidate lũy kế hiện hành **trước** GATE-01: `P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip`, SHA `.35` = `11370b57ec98b3cd50be35fe8ad6693c564d04696a95987c6560a5037fca8ca2` — **giữ nguyên trạng thái UNPROMOTED**, không bị sửa đổi.
- Gói candidate lũy kế **kế nhiệm** sau GATE-01 (runtime đã thay đổi với các sửa E1–E7): `P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip`, SHA = `14a80d497ce6aa64014781f2fdb1bb4296a2f93dd5c873dd722855869a0cd014` — **UNPROMOTED**, 20 698 844 byte, kiểm tra sanity governance PASS, hồ sơ governance record `.35` được mint và xác minh fresh-tree TOÀN BỘ PASS. Không có delta candidate, không có gói thứ hai.

## Mục 3. Fingerprint contradiction root cause

Mâu thuẫn giữa fingerprint trên hợp đồng dispatch và fingerprint trên biên lai trong CLOSURE-01 đã được **phân loại có bằng chứng** thành **CASE C: RECEIPT_NORMALIZATION_BUG** (không phải CASE A — giả mạo hợp đồng, cũng không phải CASE B — lệch ngữ nghĩa trường):

| Bằng chứng | Giá trị |
|---|---|
| Fingerprint dispatch (trên hợp đồng gốc, bao gồm `{goal,task,objective,workspace=/tmp/gt-iso-closure,target}`) | `dbb71556...` — đã tái tạo byte-exact |
| Fingerprint trên biên lai (hợp đồng được **xây lại lần thứ hai** trong tiến trình con của biên lai, với `provenance_record`/`acceptance_criteria` khác) | `2167fc33...` |
| Tồn tại khớp nối chéo miền contract↔dispatch↔receipt | **KHÔNG** — mỗi điểm tự băm một tập trường riêng |

Kết luận: không có bằng chứng giả mạo; lỗi nằm ở **chuẩn hóa biên lai** — hợp đồng trong biên lai được rebuild với miền trường khác miền fingerprint duy nhất của dispatch, nên hai "dấu vân tay của cùng một nhiệm vụ" khác nhau một cách hợp lệ nhưng làm mất khả năng liên kết bằng chứng. GATE-01 khép kín khe này bằng một **miền fingerprint hợp nhất** duy nhất (mục 5).

## Mục 4. Identity-chain design

Module mới `p2p_evidence_chain.py` (sơ đồ `p2p-execution-identity-chain/1`) định nghĩa **mỗi thực thi một chuỗi định danh bất biến**: `run_id → dispatch_id → execution_id → receipt_id`, mỗi id được dẫn xuất xác định (deterministic) từ id trước đó + tải trọng 6 trường (schema, role_id, goal_id, task_id, contract digest, request fingerprint). Đặc tính đã kiểm chứng: cùng đầu vào luôn cho cùng id (kiểm thử `test_deterministic_identity`); nhiệm vụ khác thì id khác (kiểm thử `test_different_task_different_ids`); `verify_identity_chain` kiểm tra từng khâu (run_derivation, dispatch_derivation, execution_derivation, contract_to_dispatch_binding, receipt_derivation). Chuỗi còn mang kèm `source_commit`, `project_commit`, `run_sequence` và `attestation_fingerprint` để gắn bằng chứng máy chủ và độ tươi vào cùng một cấu trúc.

## Mục 5. Contract → dispatch binding

Khe hợp đồng↔dispatch được khép bằng `contract_request_fingerprint(contract)`: **MỘT miền fingerprint hợp nhất** — digest hợp đồng được tính đúng một lần, rồi được ghi vào hợp đồng, vào dispatch (`role_execution_contract_digest`), vào chuỗi định danh, và vào biên lai. Trong lần chứng minh lại GATE-01, digest hợp đồng `d5ee804976666a5ef8e0b713012e61c2a4d59d99dc5df35050346fc84f5894ab` xuất hiện **đồng nhất** trên cả ba bề mặt. Hợp đồng được **xây duy nhất MỘT lần** rồi lưu snapshot (`contract_snapshot.json`); mọi bề mặt sau đó đọc lại từ snapshot, không rebuild — loại bỏ hoàn toàn nguyên nhân gốc của CASE C. Ma trận phủ định case A chứng minh: hợp đồng bị giả mạo dẫn đến digest khác và biên lai lai (hybrid) không còn xác minh được (`overall=False`).

## Mục 6. Timestamp changes

Trước GATE-01: thời điểm trên biên lai có thể là placeholder (`""`, `"UNKNOWN"`, `"0000-01-01T00:00:00Z"`). Từ GATE-01 (`role_receipt.py`, marker `# GATE01-MUTATION-READY-RECEIPT`):

- `build_mutation_ready_receipt` **từ chối trực tiếp** timestamp rỗng/UNKNOWN bằng `RoleReceiptError("PLACEHOLDER_TIMESTAMP_REJECTED")`.
- Từ chối vòng đời **không đơn điệu** (`started_at > completed_at`) bằng `RoleReceiptError("NON_MONOTONIC_LIFECYCLE")`.
- Biên lai chuẩn mực GATE-01 mang UTC thực: `started_at = 2026-08-20T09:28:40Z`, `completed_at = 2026-08-20T09:28:40Z` (UTC thực, `started_at ≤ completed_at`), và `lifecycle_timestamps_monotonic = True` trong kết quả xác minh.
- Thời gian chỉ làm bằng chứng vòng đời, **không tham gia vào định danh** (id chuỗi và receipt_id không băm timestamp).

## Mục 7. Freshness source binding

Trước GATE-01: binding độ tươi trên biên lai là "BOUND" không điều kiện, không ràng buộc với chứng chỉ nguồn. Từ GATE-01 (marker `# GATE01-SOURCE-BOUND-REGISTRY` trong `quality_intelligence.py` + `_g1_registry_freshness_binding` trong `role_receipt.py`):

- Sổ đăng ký nguồn-bound mới: `.p2p/state/source_registry.json`, khóa bởi `(capability_id, subject, source_repository_id, source_commit, project_commit)`; mỗi chứng chỉ có `expiry_seconds` (mặc định 7 ngày — **thất bại kín tuần**).
- Biên lai chỉ mint `binding_status = "BOUND"` khi `source_bound_status` trả về `CURRENT_EXACT_REVISION`; mọi trạng thái khác mint `NOT_BOUND:<STATUS>` và verifier fail-closes toàn chuỗi (`freshness_source_bound = False`).
- Đã kiểm chứng: commit nguồn cũ → NOT_BOUND:STALE_SOURCE_COMMIT_BLOCKED; commit dự án cũ → NOT_BOUND:STALE_PROJECT_COMMIT_BLOCKED; chứng chỉ tuyệt chủng → CERTIFICATION_EXPIRED_BLOCKED; không có chứng chỉ → NO_REGISTRY_BIND. Kiểm thử case E và F của ma trận phủ định đều BLOCK.
- Ma trận E12: đường may seam gọi `evaluate_source_bound_role_eligibility` khi git HEAD + tree phân giải 40-hex tại gốc vòng lặp, kẻo rơi về seam cũ của closure.

## Mục 8. Certification subject

Chủ thể chứng chỉ trong lần chứng minh lại GATE-01: `non_mutating_project_analysis` (đúng chủ thể — năng lực được chứng nhận trùng với năng lực yêu cầu, không phải vai trò `p2p_iris` như bản ghi cũ của closure). Đường may subject được kiểm chứng fail-closed: chứng chỉ có subject khác (`gate01-read-only-canonical-reproof-001`) khiến kết quả là `NO_SOURCE_BOUND_RECORD → NOT_ELIGIBLE` (case G của ma trận phủ định). Không còn trạng thái `WRONG_SUBJECT_BLOCKED` chết — mã đã tái cấu trúc để kiểm tra subject trước bộ lọc, và kiểm thử tương ứng khớp hành vi fail-closed thực tế.

## Mục 9. Certification capability

Năng lực được chứng nhận: `non_mutating_project_analysis` (FW04), được chứng nhận với kết quả `CERTIFIED`, eval `gate01-hardening-01` / `C35-rc1`, evidence_version `0.1.0`, pointer bằng chứng `/home/ubuntu/fw01_work/pilot_gt_evidence.md`. Tính sẵn sàng của vai trò được đánh giá qua `evaluate_source_bound_role_eligibility` với `all_source_bounds_current = True` khi cả hai commit khớp chính xác (kiểm thử `test_fresh_source_bound_eligible`). Ma trận phủ định case H chứng minh: năng lực sai (`code_read`) → `NO_SOURCE_BOUND_RECORD → NOT_ELIGIBLE`.

## Mục 10. Current adapter

Adapter mục tiêu thực thi: `p2p-manus-orchestration` (đã đăng ký trong `adapter_registry.json` với `provider=manus`, `model=manus-models`, `harness=manus-fw00-fw06-candidate`, `live_certified=True`). Biên lai ghi `target_id = p2p-manus-orchestration`; adapter này mang chứng chỉ năng lực `NON_MUTATING_TASK` trạng thái `LIVE_CERTIFIED_FOR_CAPABILITY` — đủ điều kiện cho envelope READ_ONLY. Không thay đổi adapter giữa các lần chạy.

## Mục 11. Current host

Máy chủ thực thi thực: **Linux 6.1.102 x86_64**, hostname `87cd0e940adf` (máy ảo sandbox Manus). Định danh máy vendor-trung lập được mint xác định trong `machine_host_identity()` và `canonical_machine_identity()` (uname system/release/machine + hostname), và được đóng gói vào bằng chứng máy chủ trên mỗi attestation.

## Mục 12. HostAttestation

Module `host_attestation.py` (marker `# GATE01-CANONICAL-HOST-ATTESTATION`) cung cấp `make_canonical_host_attestation` với by-line `manus / manus-models / manus-fw00-fw06-candidate`:

- Bản ghi sử dụng được **ghi vào ledger TRƯỚC khi trả về** (`canonical_attestation_ledger.jsonl` — self-observation); `is_canonical_attestation_replayed(fp)` trả về `True` ngay sau lần phát đầu tiên và phát hiện tái sử dụng ở mọi lần sau.
- Biên lai GATE-01: `attestation_fingerprint = e17214758d65f952512c5ef7dd4655fbf2170d293259e29a7c4b6c261e38477f`, `host_execution_identity = host-7e72dcad9de354188d06324fe0d030f1584342a2d12ed2d63366a266`, `host_kind = generic-real` (máy thật, không synthetic), `attested_at = 2026-08-20T09:28:40Z` (UTC thực).
- Ma trận phủ định case I: thiếu attestation → `overall=False`; case J: tái dùng fingerprint attestation ngoài chính sách → replay phát hiện ngay. Kiểm thử `test_attestation_replay_detected` PASS.

## Mục 13. New execution ID

```
execution_id = f965343f5913d8e026e2fd8c116e7764340849811cf77824a6f33a3db393e4d5
```
(Chuỗi định danh `p2p-execution-identity-chain/1` — mới, duy nhất cho thực thi `gate01-read-only-canonical-reproof-001`; không trùng bất kỳ id nào của CLOSURE-01.)

## Mục 14. New dispatch ID

```
dispatch_id = 54efdd2a600052fb78cfc4703e7d0f27b275f2a3fbc14763f3df861709b5a085
```
(khác hẳn dispatch `dbb71556...` của closure — nhiệm vụ, hợp đồng và chuỗi đều mới.)

## Mục 15. New receipt ID

```
role_receipt_id = f7a46a12793c73041144be3eff0b1b0d61d89d816860018f3e7233cc2e2cf856
```
(6 trường thống nhất: schema + execution_id + contract_digest + request_fingerprint + attestation_fingerprint + outcome; sơ đồ `p2p-gate01-read-only-receipt/1` trên biên lai GATE-01.)

## Mục 16. Project revision binding

Biên lai GATE-01 gắn **đôi commit hiện thực**: `source_commit = 0bc22b15233e85f1e48993a6d1aac06e6fe6fffe` (HEAD kho `auth-f01` tại thời điểm chạy) và `project_commit = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b` (tree có theo dõi của bản sao Game Truyện cô lập `/tmp/gt-iso-gate01` tại thời điểm chạy — trùng trạng thái baseline của CLOSURE-01). Sổ nguồn-bound chứng nhận đúng cặp này (`CURRENT_EXACT_REVISION`), và mọi drift của cặp commit đều làm `binding_status = NOT_BOUND` — chuỗi thất bại kín.

## Mục 17. Receipt timestamps

Biên lai GATE-01: `started_at = 2026-08-20T09:28:40Z`, `completed_at = 2026-08-20T09:28:40Z` — UTC thật lấy từ máy tại thời điểm chạy (không placeholder), `started_at ≤ completed_at` (đơn điệu), `execution_status = SUCCEEDED`, `verification_status = VERIFIED`. Verifier báo `lifecycle_timestamps_monotonic = True`.

## Mục 18. Verifier result

`verify_mutation_ready_receipt` trên biên lai GATE-01: **overall = True** với cả năm bề mặt xác minh PASS:

| Bề mặt | Kết quả |
|---|---|
| run_derivation | expected == recorded — verified: True |
| dispatch_derivation | expected == recorded — verified: True |
| execution_derivation | expected == recorded — verified: True |
| contract_to_dispatch_binding | verified: True |
| receipt_derivation | expected == recorded — verified: True |
| lifecycle_timestamps_monotonic | True |
| freshness_source_bound | True |
| **overall** | **True** |

(Vòng chứng minh lại đã dừng cứng — hard stop — khi verifier fail; biên lai cuối được ghi ở `/home/ubuntu/fw01_work/pilot_gt_receipts/gate01_receipt.json`.)

## Mục 19. Replay tests

Replay/duplicate control được chứng minh fail-closed trên bề mặt GATE-01: tái dùng fingerprint attestation sau lần phát đầu → `is_canonical_attestation_replayed = True` (case J, kiểm thử `test_attestation_replay_detected`); receipt_id được **tái dẫn xuất xác định** từ các trường khai báo (`fp_att == role_receipt_id`, case K); định danh chuỗi determinism — cùng đầu vào cho cùng id, chuỗi lai hybrid digest không xác minh được (case B, `overall=False`). Ma trận phủ định: A = BLOCK, B = BLOCK, I = BLOCK, J = BLOCK, K = BLOCK.

## Mục 20. Drift tests

Ba kiểm chứng drift: (1) **tree drift** — thêm file sentinel vào bản sao rồi xóa → tree hash thay đổi, drift phát hiện (YES); khôi phục về baseline → tree trở lại đúng baseline (commit sẵn sàng 91661a25 của HEAD `b0e6deb`); (2) **drift commit nguồn** — repo `auth-f01` tiến từ `0bc22b1` → `ceb0e13`, chứng chỉ nguồn-bound tương ứng cập nhật đúng commit mới; (3) **H1/H2** — trước/sau thực thi READ_ONLY: `TREE_UNCHANGED = True` (xem mục 21), tức không có drift nào do chính lần thực thi.

## Mục 21. H1/H2

- `H1 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b` (tree có theo dõi của bản sao cô lập TRƯỚC thực thi — giữ nguyên baseline so với CLOSURE-01).
- `H2 = c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b` (SAU thực thi).
- `H1 == H2: True` — `TREE_UNCHANGED = True` — **zero mutation** trong toàn bộ lần chứng minh lại.

## Mục 22. Application mutation

**Không có mutation ứng dụng nào xảy ra.** Lần chứng minh lại là READ_ONLY thuần (FW02/FW03 profile READ; permission gate `READ_ONLY pre-established; task profile READ; valid`). H1 == H2 xác nhận zero byte thay đổi trên tree theo dõi; không chạm Gia Phả, không chạm Logistics, không tạo file ứng dụng mới nào trong dự án Game Truyện.

## Mục 23. New tests

Bộ kiểm thử mới `p2p_capabilities/tests/test_p2p_gate01_evidence.py` — **23 kiểm thử**, toàn bộ PASS, gồm 5 nhóm: identity-chain determinism + cross-domain fingerprint binding (4); source-bound eligibility drift/subject/capability/recertify (7); lifecycle timestamps placeholder/monotonic/real-UTC (3); canonical host attestation identity + replay (2); ma trận phủ định thu gọn (A, B, C, D, I + baseline correct chain) (7). Tất cả dùng lại thiết bị hồi quy hiện có (FW03 registry, adapter bridge, backend), không invent lại bề mặt đã có.

## Mục 24. Regression

| Khối | Kết quả |
|---|---|
| Hồi quy baseline + GATE-01 (`unittest discover`) | **263/263 PASS** (240 baseline + 23 GATE-01), 41,6 giây |
| Validator framework (`validate_p2p_development_framework.py`) | **78/78 PASS**, 0 fail |
| Development control (`p2p_development_control.py validate`) | PASS — `governance/development-control.json` |
| Quét bí mật (gitleaks 8.21.2, 7 tệp mới/sửa, `--no-git`) | **RC=0 tất cả** — zero leaks |
| Ma trận phủ định A–L trên bản sao cô lập | **10 × BLOCK + L = VERIFIED, MATRIX_PASS = True** |
| `NEW_UNEXPLAINED_FAILURES` | **0** |

## Mục 25. Candidate impact

Runtime đã thay đổi (6 tệp mới/sửa: `p2p_evidence_chain.py` MỚI; `quality_intelligence.py`, `role_eligibility.py`, `host_attestation.py`, `role_receipt.py`, `p2p_fw01_loop.py` append; 1 bộ kiểm thử MỚI) → theo chính sách candidate, **màu gói được xây lại từ cây tươi** thành một gói lũy kế kế nhiệm duy nhất, SHA `14a80d49...0cd014`, giữ nhãn phiên bản cũ, trạng thái **UNPROMOTED**. Gói .35 trước (`11370b57...8ca2`) không bị chạm, vẫn UNPROMOTED. Không phát hành delta candidate; governance record .35 được mint lại với SHA mới và xác minh fresh-tree PASS (extract-byte-identical + manifest-checksum; doctor full gate set; FW05/FW06 present; lease + decision-ID determinism trong tiến trình cô lập).

## Mục 26. Candidate version/SHA if minted

> Đã mint: `P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip`
> SHA-256: **`14a80d497ce6aa64014781f2fdb1bb4296a2f93dd5c873dd722855869a0cd014`**
> Vị trí: `reports/candidates/` · Trạng thái: **UNPROMOTED** · governance record: `FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE .35 — GOVERNANCE SANITY PASS`

## Mục 27. MUTATION_EVIDENCE_CHAIN_READY

> **`MUTATION_EVIDENCE_CHAIN_READY = YES`**
>
> Chuỗi bằng chứng thực thi (định danh, độ tươi theo nguồn, bằng chứng máy chủ, vòng đời thời gian thực) đã đủ chặt để P2P biết chắc một thao tác CÓ xảy ra hay KHÔNG: dispatch `54efdd2a...`, execution `f965343f...`, receipt `f7a46a12...`, attestation `e1721475...` — tất cả ràng buộc chéo miền qua MỘT miền fingerprint hợp nhất, fail-closed trong mọi hướng phủ định đã kiểm thử (A–L).

## Mục 28. Remaining NOT_PROVEN

Các khoản chưa được chứng minh — được giữ nguyên theo khối lệnh, KHÔNG phải thất bại: (a) KHÔNG mutation pilot nào đã được thực thi — khả năng viết vẫn chưa được thử nghiệm trên sản phẩm; (b) KHÔNG promote/release candidate — gói .35 kế nhiệm vẫn UNPROMOTED; (c) KHÔNG chạy lại Council 8/8 (C36) — lịch sử C36 không phục sinh; (d) Framework-07 chưa khởi động; (e) adapter mục tiêu vẫn là đăng ký tường minh cục bộ — chứng nhận adapter trên môi trường mục tiêu khác chưa được chứng minh; (f) expiry 7 ngày của chứng chỉ nguồn-bound chưa trải qua chu kỳ hết hạn thực; (g) bằng chứng này được tạo trên sandbox cô lập — chưa được tái chứng minh trên máy người sở hữu.

## Mục 29. Exact next Owner decision

Quyết định chủ sở hữu tiếp theo chính xác là:

> **"Approve or reject ONE low-risk non-production mutation pilot on isolated Game Truyện."**

Đã **dừng** theo chỉ thị — KHÔNG khởi động mutation pilot tự động. Việc tiếp theo hoàn toàn thuộc về Chủ sở hữu.

---

## Phụ lục — bằng chứng chính

| Tệp bằng chứng | Nội dung |
|---|---|
| `/home/ubuntu/fw01_work/pilot_gt_receipts/gate01_receipt.json` | Biên lai chuẩn mực READ_ONLY GATE-01 (verifier overall=True) |
| `/tmp/gt-iso-gate01/.p2p/state/identity_chain_snapshot.json` | Chuỗi định danh (run/dispatch/execution/receipt ids) |
| `/tmp/gt-iso-gate01/.p2p/state/canonical_attestation_ledger.jsonl` | Ledger sử dụng attestation (hệ tệp state clone) |
| `/tmp/gt-iso-gate01/.p2p/state/source_registry.json` | Sổ đăng ký chứng chỉ nguồn-bound (CURRENT_EXACT_REVISION) |
| `/home/ubuntu/fw01_work/pilot_gt_receipts/gate01-inspection-artifact.json` | Sản phẩm kiểm tra READ_ONLY thực (task T02 dẫn xuất thật từ TASKS.md) |
| `/home/ubuntu/fw01_work/gate01_plan.md` | Nhật ký thiết kế và tiến trình GATE-01 |
| Commit nhánh `ceb0e13` | Chứa toàn bộ sửa E1–E7 + bộ kiểm thử 23 |

*Chấm dứt báo cáo — P2P-MUTATION-READINESS-GATE-01 · PASS / MUTATION_EVIDENCE_CHAIN_READY_FOR_OWNER_GATE · MUTATION_EVIDENCE_CHAIN_READY = YES · DỪNG.*
