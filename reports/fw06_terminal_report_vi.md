# P2P-FRAMEWORK-06 — PRODUCTION AUTONOMY & RESILIENCE
## Báo cáo khép kín (Terminal Report) — 42 mục, tiếng Việt

**Ngày:** 2026-08-20 (GMT+7) | **Nhánh:** `p2p-fw01-bootstrap-reconciliation`
**Trạng thái:** PASS / `FW06_PRODUCTION_AUTONOMY_RESILIENCE_READY` — DỪNG tại `OWNER_FW06_CLOSURE_GATE`
**Người nhận:** Owner | **Ngôn ngữ chủ đạo:** Việt Nam | **Verdict:** PASS / FW06_PRODUCTION_AUTONOMY_RESILIENCE_READY

---

### 1. Starting Git truth (sự thật Git khởi điểm)

Khởi điểm chứng thực trước khi bắt đầu FW06 (quy trình phục hồi sự thật bắt buộc): nhánh `p2p-fw01-bootstrap-reconciliation`, HEAD local = HEAD remote = `ea5970d` (P2P-FW05 closure addendum). Worktree sạch, 0 tệp chưa commit. Candidate `.33` (FW05) UNPROMOTED, SHA256 `a4c3161b711a1c9dae6870401f8135e0e77b445c7703ac7fa0ed9c983a06bbb9` khớp governance record và zip artifact. Baseline regression tại khởi điểm: **203/203 PASS**. Không có drift runtime: 7 tệp runtime FW01–FW05 byte-identical so với commit `5f10c02` (FW05 implementation commit).

### 2. Final HEAD/remote

HEAD cuối = HEAD remote = `21df4a3d7abae37556a874da1f19f6f24be5dbed`. Worktree sạch. Lịch sử first-parent từ FW04 (d092f7f) → FW05 (5f10c02, 83de0a6) → reconciliation (ea5970d) → FW06 (21df4a3). Không force-push, không rewrite lịch sử.

### 3. FW06 plain-language capability (khả năng theo ngôn ngữ thường)

FW06 KHÔNG phải orchestrator mới. Nó là một **lớp hợp đồng vận hành giới hạn** (bounded runtime-contract layer) đặt trên mặt phẳng điều khiển P2P hiện có. Nói đơn giản: hệ thống giờ biết "khi nào an toàn để tiếp tục — và khi nào PHẢI dừng". Trước mỗi bước tự động, vòng lặp FW01 (vẫn là vòng lặp duy nhất) kiểm tra một phong bì ủy quyền (Autonomy Envelope) và một chính sách tiếp tục an toàn; nếu thiếu bằng chứng, thiếu phép, hoặc trạng thái thất bại không nhận diện được, hệ thống dừng lại an toàn thay vì đoán mò. Nếu tiến trình bị crash, FW06 phân tích bằng chứng tại điểm thất bại và quyết định theo danh sách giới hạn (thử lại có giới hạn / chỉ kiểm chứng / chặn / tạm dừng) — **không bao giờ thực hiện lại mù** một thao tác chưa được xác nhận hoàn tất.

### 4. Autonomy Envelope

Được triển khai trong `fw06_operational_resilience.py` với cấu trúc xác định: `project_id`, `goal_id`, `authorized_scope` (phạm vi được phép, vd. `dev`), `non_scope` (không được phép, vd. `prod`), `allowed_mutation_classes` (vd. `READ_ONLY`, `TEST_ONLY`), `owner_gates`, `max_parallelism`, `retry_policy` (số lần thử, backoff), `resource_budget`, `quality_requirements`, `recovery_policy` và `expires_at`. **Fresh-only enforcement:** phong bì đã hết hạn hoặc vắng mặt → fail-closed (`VALIDATION_FAILED`). Envelope được lưu bền vững tại `.p2p/state/fw06-envelope-*.json` và kiểm chứng tại mọi gate, không chỉ khi tạo.

### 5. Safe continuation policy (chính sách tiếp tục an toàn)

`safe_continuation_decision()` quyết định gate-by-gate, mọi gate đều fail-closed: nếu bất kỳ điều kiện nào không thể xác nhận, kết quả là `CONTINUATION_BLOCKED` kèm failure class. Không có đường "tiếp tục mặc định" khi thiếu bằng chứng.

### 6. Crash recovery

`recover_after_crash()` phân tích bằng chứng tại điểm thất bại (dispatch evidence, verification evidence, mutation-class evidence, idempotency key, completion record). Matrix A–G (7 điểm crash — A: chưa dispatch; B: dispatched chưa verify; C: verified chưa hoàn tất; D: hoàn tất chưa ghi evidence; E: evidence bị mất; F: checkpoint mâu thuẫn; G: không xác định) — **mọi trường hợp đều trả về `RETRY_BOUNDED`/`VERIFY_ONLY`/`BLOCK`/`PAUSE`; không trường hợp nào cho phép thực hiện lại mù**. Được chứng minh cơ học bằng 7 ca lạnh (fresh subprocess thật, không chia sẻ Python globals) — mục 24.

### 7. Session-death recovery

Cùng cơ chế với crash recovery: tiến trình chết giữa chừng được thu hồi qua lease hết hạn + heartbeat TTL. Thu hồi phong bế fail-closed khi tiến trình chủ vẫn quan sát được (`RECLAIM_BLOCKED_OWNER_OBSERVABLE`) — đã chứng minh bằng subprocess thật.

### 8. Ambiguous mutation behavior (hành vi khi mutation mơ hồ)

Phân loại thất bại fail-closed: trạng thái mutation không nhận diện được → `UNKNOWN_MUTATION_STATE` → mọi gate chặn (`CONTINUATION_BLOCKED` / `CLEANUP_BLOCKED`). Không suy đoán; Owner được trình bày bằng chứng mơ hồ để quyết định.

### 9. Retry policy (chính sách thử lại)

`bounded retry` — số lần thử và backoff do Owner cấu hình trong envelope; không có retry không giới hạn. Sau khi cạn số lần → `RETRY_EXHAUSTED` → chuyển cho Owner (không tự động leo thang).

### 10. Retry vs failover

**FAILOVER != RETRY**: failover chỉ xảy ra khi có quyết định thất bại có bằng chứng và chuyển hướng sang backend thay thế đã ủy quyền trong `authorized_scope`; retry chỉ thử lại chính thao tác đó. Failover deterministic — cùng đầu vào bằng chứng luôn cho cùng quyết định (đã kiểm chứng bằng test).

### 11. Quiesce/drain

Lifecycle ENTER → DRAIN → VERIFY: `quiesce_enter()` chặn công việc mới, `quiesce_drain()` chờ inflight hoàn tất, `quiesce_verify_no_inflight()` chỉ xác nhận khi không còn việc đang chạy. Với checkpoint đã hòa hợp: cho phép; với checkpoint bị chặn: fail-closed `QUIESCE_BLOCKED`.

### 12. Hot-swap

Không tuyên bố hot-swap. Không có cơ chế thay nóng backend/role khi đang chạy; mọi thay đổi cấu hình đi qua envelope mới (Owner) + quiesce/drain tuần tự. Được khai báo trung thực trong module docstring.

### 13. Runtime health

Kiểm tra sức khỏe phân tầng (tiered): tier-1 rẻ, có cache (mặc định chỉ tier-1); `runtime_health_check()` trả về `health` + `tiered=True`. Cheap-by-default — không phát sinh chi phí lớn khi chạy thường xuyên.

### 14. Workspace ownership

`register_workspace()` cấp quyền sở hữu workspace cho task (project + goal + task id); các thao tác trên workspace (cleanup) kiểm tra owner trước — không ai khác được dọn workspace mình không sở hữu.

### 15. Parallel worktree behavior (hành vi worktree song song)

`max_parallelism` trong envelope giới hạn worktree đồng thời; mỗi workspace có định danh stable, được dọn sạch sau khi hoàn tất/không hoạt động (`cleanup_workspace()` có guards fail-closed).

### 16. Conflict handling

`detect_conflict()` xác định hai tập tệp song song có va chạm hay không — cùng tệp → `CONFLICT`; tệp rời nhau → `PARALLEL_OK`. **Deterministic**: cùng đầu vào luôn cùng kết quả (bằng chứng test). Cleanup workspace fail-closed đến khi mọi guard đạt.

### 17. Lease/split-brain

Execution lease append-only (JSONL), mỗi lease có `expires_at` + heartbeat. Hai tiến trình thật đồng thời cố giành cùng lease → **chỉ một thành công, tiến trình kia bị chặn `LEASE_CONFLICT`** (đường biên subprocess thật, không dùng globals chung). Release = dòng RELEASED mới (append-only); acquire tính effective status (dòng cuối thắng). Reclaim hết hạn fail-closed khi owner observable.

### 18. Pause/resume

`pause_project()` / `resume_project()` lưu trạng thái bền vững tại `.p2p/state/fw06-pause-*.json`; fresh process khác đọc lại và tiếp tục đúng — đã chứng minh bằng subprocess lạnh. Trạng thái pause hỏng/không đọc được → fail-closed (không tự mở khóa).

### 19. Multi-project isolation

Mỗi project có envelope, lease, pause, quiesce, workspace riêng (namespace theo `project_id`); các view đa-project liệt kê theo project, không cross-leak.

### 20. Multi-project Owner view

`multi_project_health_summary()`, `discover_projects()`, `fw06_project_summary()` — tất cả **read-only**, không tạo thư mục state trên root dự án (đường dẫn read dùng `mkdirs=False`; đã kiểm chứng bằng ast walk + shadow eval byte-identical trên GT/GP).

### 21. Resource/backpressure

Envelope mang `resource_budget`; vượt ngân sách → gate chặn (backpressure fail-closed). Không có tự động mở rộng vượt ngân sách Owner.

### 22. Quality preservation (bảo toàn chất lượng)

`quality_requirements` trong envelope: nếu checkpoint chất lượng (FW04) không đạt/missing → `QUALITY_NOT_SATISFIED` → chặn tiếp tục. FW04 QUALITY_REVIEW stop và chứng nhận subject-bound không bị suy yếu (regression bao phủ, mục 31).

### 23. Owner Gate preservation

FW06 **không** tạo Owner Gate mới, không tự phê duyệt; mọi quyết định thuộc Owner vẫn đi qua Owner Inbox của FW05 (đã chứng minh bằng hook info-only — mục 16 của supervisor FW06: hook tồn tại, không chặn vòng lặp).

### 24. Cold-process tests (kiểm thử cold-process)

Suite FW06: **37 ca PASS**, trong đó mọi ca recovery/lease/pause chạy qua **subprocess Python thật, fresh interpreter**, chỉ giao tiếp qua trạng thái bền vững trên disk — không chia sẻ globals/mocks. Matrix crash A–G đầy đủ.

### 25. Two-process lease test (kiểm thử lease hai tiến trình)

Ca hai tiến trình thật đồng thời giành cùng lease: 1 thắng, 1 bị `LEASE_CONFLICT`; release-then-reacquire đúng (effective status); reclaim hết hạn fail-closed khi owner observable — tất cả qua đường biên subprocess.

### 26. Failover tests (kiểm thử failover)

Failover deterministic (cùng evidence → cùng quyết định) + phân biệt FAILOVER != RETRY; failover chỉ qua backend ủy quyền trong scope; không có đường fallback tự do. Đã kiểm chứng trong suite 37 ca.

### 27. GT shadow eval (shadow READ-ONLY trên Game Truyện)

`/home/ubuntu/fw01_work/cert/game-truyen` được quét bởi toàn bộ read surfaces FW06; tree hash SHA256 (toàn tệp) trước/sau là **byte-identical**; thư mục `.p2p` trong GT sau khi hoàn tất: **không tồn tại** (read-only facade đã được sửa để không tạo thư mục state — `mkdirs=False`).

### 28. GP shadow eval (shadow READ-ONLY trên Gia Phả)

Tương tự GT trên `/home/ubuntu/fw01_work/cert/gia-pha`: byte-identical trước/sau, không có `.p2p` mới. Thư mục `supabase/` có sẵn từ trước của GP được xử lý đúng (baseline, không phải mutation — probe diff-based).

### 29. Logistics safety (an toàn Logistics)

Kiểm tra cây Logistics sau toàn bộ hoạt động supervisor + suite: 0 tệp mới, 0 thay đổi. Dự án GT/GP/Logistics không bị chạm — được ghi nhận trung thực.

### 30. New FW06 tests (kiểm thử FW06 mới)

`test_fw06_operational_resilience.py`: **37 ca PASS** — chaos matrix A–G (cold-process), two-process lease + reclaim, pause/resume durability, fail-closed negatives (unknown mutation → UNKNOWN_MUTATION_STATE, cleanup guard, envelope hết hạn, stale answer), deterministic failover + conflict detection, tiered runtime health, worktree parallel proof, GT/GP read-only shadow byte-identical.

### 31. Full regression (hồi quy toàn bộ)

Chạy chuẩn (cd `.p2p/system`, discover `-s p2p_capabilities/tests -p "test_*.py"`): **240/240 PASS** = 174 cũ + 29 FW05 + 37 FW06. `NEW_UNEXPLAINED_FAILURES = 0`. Suite Seam-A/B, checkpoint, certification, FW01–FW05 toàn bộ không suy thoái.

### 32. Validator/control (kiểm định + quản trị)

Framework validator `scripts/validate_p2p_development_framework.py`: **78/78 PASS, 0 failed**. Governance: record `.34` đúng schema `lineage_contract`, anchor `.33` đúng SHA, `UNPROMOTED`, không trùng, không ghi đè lịch sử.

### 33. Secret/security scan (quét bí mật/bảo mật)

`gitleaks detect --no-git` trên 7 tệp thay đổi của FW06: **0 findings**. Sự kiện event log tự động loại bỏ token (pattern `_looks_secret_like` từ task_state, giá trị → `<REDACTED>`) và bỏ mọi khóa chain-of-thought (đã kiểm chứng bằng test + supervisor check 10).

### 34. Independent supervisor (giám sát độc lập)

`scripts/fw06_supervisor.py` — **16/16 PASS** trên đường dẫn mã/dữ liệu thật (không mock): (1) FW06 không chọn task/role/team/provider/model; (2) views không thực thi mã (ast walk — tập call cho phép giới hạn, `run`/`which` chỉ trong health check của môi trường); (3) failure classification fail-closed; (4) safe continuation fail-closed mọi gate; (5) lease chặn split-brain hai tiến trình thật; (6) crash A–G không blind re-execution; (7) reclaim blocked khi owner observable; (8) pause/resume bền vững qua fresh process; (9) envelope hết hạn fail-closed; (10) event strip secrets + CoT keys; (11) runtime health tiered/cheap; (12) conflict detection deterministic; (13) cleanup fail-closed; (14) mọi surface READ-ONLY GT/GP byte-identical; (15) zero mutation diff-based; (16) FW01 hook info-only.

### 35. Runtime/governance files changed (tệp runtime/quản trị thay đổi)

7 tệp: `fw06_operational_resilience.py` (mới, module chính), `tests/test_fw06_operational_resilience.py` (mới, 37 ca), `p2p_fw01_loop.py` (thêm hook info-only `fw06_resilience` — không đổi luồng), `scripts/fw06_supervisor.py` (mới), `scripts/mint_fw06_candidate.py` (mới, chỉ mint record), `governance/development-control.json` (thêm record .34), `reports/candidates/fw06-operational-resilience-candidate.zip` (mới, artifact).

### 36. Production readiness levels actually proven (mức sẵn sàng production thực chứng)

Được chứng minh: `FOUNDATION_READY`, `DETERMINISTICALLY_VERIFIED`, `PROCESS_RECOVERY_VERIFIED`, `MULTI_PROCESS_VERIFIED` (cold-process + two-process lease qua subprocess thật), `READ_ONLY_FACADE_VERIFIED` (GT/GP byte-identical, ast walk), `FAIL_CLOSED_VERIFIED` (mọi gate), `GOVERNANCE_BINDINGS_VERIFIED` (candidate SHA khớp bytes, anchor chain `.33`).

### 37. Remaining NOT_PROVEN (chưa được chứng minh)

**Trung thực khai báo:** `LIVE_SINGLE_PROJECT_VERIFIED` và `LIVE_MULTI_PROJECT_VERIFIED` KHÔNG được tuyên bố — mọi bằng chứng dự án dùng fixture tổng hợp (`/tmp` synthetic roots); không có live run qua nhiều phiên thực sự; hot-swap không tồn tại (khai báo §12); backpressure thực trên tải thật chưa chứng minh; khả năng chịu lỗi hạ tầng bên ngoài (network/S3) không thuộc phạm vi.

### 38. Candidate policy

Chính sách candidate: **YES** — runtime behavior thay đổi (FW01 `step()` output được làm giàu bằng trường `fw06_resilience`; state bền vững mới `.p2p/state/fw06-*`; module mới tiêu thụ tại các điểm quyết định). Candidate `.34` được mint theo đúng chính sách, UNPROMOTED, chờ Owner xét duyệt.

### 39. Candidate SHA/status nếu minted

Candidate: `8.4.7-C-codex.34`, nhãn `fw06-operational-resilience`. ZIP: `reports/candidates/fw06-operational-resilience-candidate.zip`, **SHA256 = `607e722d22db519aeee9f803814432fcd13e73157db7e6d6d4e5afcbebeca7fa`** (đã xác minh khớp governance record). Trạng thái: **UNPROMOTED**.

### 40. `.33` preserved? (`.33` được giữ nguyên?)

**Có.** `.33` (FW05) giữ nguyên: UNPROMOTED, SHA `a4c3161b...3a06bbb9`, record không sửa đổi, làm lineage anchor đúng cho `.34`. `.32` và toàn bộ lịch sử cũng không chạm.

### 41. Project/Supabase/deploy mutation

GT: 0 thay đổi (không `.p2p` mới). GP: 0 thay đổi mới (thư mục `supabase/` pre-existing là baseline; probe diff-based xác nhận `new dirs since start=[]`). Logistics: 0. Supabase/RLS: 0 thao tác. Deployment: **KHÔNG** deploy. RepoWise: không cài/không tích hợp. Council rerun: 0. Force-push/rewrite: 0.

### 42. Exact next Owner action (hành động Owner tiếp theo chính xác)

Xét duyệt (hoặc từ chối) candidate `8.4.7-C-codex.34` — đây là hành động duy nhất được khuyến nghị. Nếu Owner duyệt: promote `.34` theo chính sách promotion hiện có (không tự thực hiện). Framework khuyến nghị tiếp theo khi Owner cho phép: `P2P-FRAMEWORK-07`. **Tôi đã dừng tại `OWNER_FW06_CLOSURE_GATE` và không tự động bắt đầu FW07.**

---

## Verdict

**`PASS / FW06_PRODUCTION_AUTONOMY_RESILIENCE_READY`**

FW06 đã đạt trạng thái khép kín: khả năng đã triển khai, đã kiểm chứng cơ học (240/240 regression, 37 ca FW06 mới, supervisor 16/16, GT/GP READ-ONLY byte-identical, 0 mutation, 0 secret, validator 78/78), candidate `.34` UNPROMOTED đã mint với SHA khớp governance. Tự chủ được giới hạn chặt bằng evidence, permission và chính sách Owner — hệ thống biết khi nào an toàn để tiếp tục và khi nào PHẢI dừng.
