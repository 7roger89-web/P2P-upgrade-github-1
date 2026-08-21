# P2P-FRAMEWORK-05 — BÁO CÁO CHỦNG TỪ CHẤM DỨT (Tiếng Việt)

**Goal ID:** P2P-FRAMEWORK-05 — OWNER EXPERIENCE & DECISION TRACE
**Ngày hoàn tất:** 20/08/2026 (GMT+7)
**Trạng thái:** DỪNG TẠI `OWNER_FW05_CLOSURE_GATE` — KHÔNG tự động bắt đầu FW06
**Verdict:** `PASS / FW05_OWNER_EXPERIENCE_DECISION_TRACE_READY`

---

## 1. HEAD khởi điểm

Branch `p2p-fw01-bootstrap-reconciliation`, HEAD cục bộ = HEAD remote tại `d092f7ffe33c62c65775faeb619a9cf895e23d88` — commit "P2P-FW04 QUALITY STOP hardening". Worktree sạch, không có tệp chưa commit. Candidate mới nhất tại thời điểm bắt đầu: `8.4.7-C-codex.32` (UNPROMOTED, SHA256 `5985e0e5...cc376f6`) với lineage anchor `.31`.

## 2. HEAD/remote cuối cùng

HEAD cục bộ = remote tại `5f10c02` — commit "P2P-FRAMEWORK-05 OWNER EXPERIENCE & DECISION TRACE" (7 tệp, +2817/−10 dòng), đã push thành công lên `origin/p2p-fw01-bootstrap-reconciliation`. Không force-push, không viết lại lịch sử.

## 3. FW05 làm gì (ngôn ngữ thường)

FW05 **không phải** một orchestrator mới. FW01 vẫn là vòng lặp vận hành duy nhất. FW05 là một **lớp giao diện "chỉ-đọc + ghi quyết định"** dành cho Owner (người không lập trình): đọc trạng thái bền vững hiện có (checkpoint FW01, decision ledger, goal ledger, certification store) và trình bày/ghi nhận quyết định của Owner theo hợp đồng có cấu trúc. Owner được hỏi **ít hơn** nhưng mỗi câu hỏi quan trọng được trình bày **rõ hơn và an toàn hơn**: đúng người, đúng phạm vi, đúng bằng chứng, không bao giờ nhầm "xem trạng thái" với "tiếp tục chạy" hay "cho phép phá hủy".

## 4. Mô hình Decision Trace

Mỗi bước có ý nghĩa quyết định trong vòng lặp FW01 được ghi thành một **bản ghi quyết định bền vững** (append-only, JSONL) với 15 trường hợp đồng: `DECISION_ID`, `GOAL_ID`, `TASK_ID`, `DECISION_TYPE`, `TIMESTAMP`, `INPUT_FACTS`, `APPLIED_POLICY_OR_RULE`, `SELECTED_ACTION`, `MATERIAL_ALTERNATIVES`, `REJECTED_ALTERNATIVES_WITH_REASON`, `EVIDENCE_POINTERS`, `EVIDENCE_VERSION`, `UNKNOWN_OR_GAPS`, `OWNER_DECISION_REQUIRED`, `DECISION_STATUS`, `SCOPE`. Mỗi bản ghi trỏ đến bằng chứng (checkpoint, ledger, hash goal-state) thay vì kể lại "suy nghĩ".

## 5. Vì sao không phải chain-of-thought

Bản ghi chỉ lưu **sự thật quyết định có thể kiểm chứng**: các phương án đã xem xét, phương án bị loại và lý do, quy tắc áp dụng, con trỏ bằng chứng. Không có trường nào lưu lý luận riêng, scratchpad, hay transcript trò chuyện. Module `make_decision_record` còn **chủ động từ chối** (fail-closed) bất kỳ input nào chứa từ ngữ thuộc về private reasoning/chain-of-thought — kiểm chứng bằng test C3 trong ma trận và kiểm tra 3 của supervisor.

## 6. Mô hình Owner Inbox

Inbox là tệp append-only `.p2p/state/owner-inbox.jsonl`, mỗi mục chứa: `DECISION_ID`, `CATEGORY`, `TITLE`, `PLAIN_LANGUAGE_QUESTION`, `WHY_OWNER_IS_NEEDED`, `OPTIONS`, `RECOMMENDED_OPTION`, `CONSEQUENCES`, `BLOCKING_SCOPE`, `EVIDENCE_VERSION`, `CREATED_AT`, `STATUS`, `RESOLUTION`. Câu hỏi được viết bằng ngôn ngữ thường (tiếng Việt), giải thích tại sao Owner cần quyết định và hậu quả của từng lựa chọn — không lộ chi tiết kỹ thuật nội bộ.

## 7. Danh mục Owner Gate chính hãng

Inbox chỉ chứa quyết định thuộc về Owner: hành động **phá hủy dữ liệu**, **phát hành/promotion**, **yêu cầu quyền hạn/tài khoản/mật khẩu**, **câu hỏi sản phẩm tính phí** (ví dụ: thêm tính năng premium), và **dừng chất lượng thuộc trách nhiệm Owner** (QUALITY_REVIEW mà Owner sở hữu việc cung cấp bằng chứng). Kỹ thuật viên (hệ thống) không tự quyết những việc này.

## 8. Câu hỏi kỹ thuật được tự xử lý (không làm phiền Owner)

Lựa chọn model/backend, lựa chọn skill, cỡ team, vai trò, runner, context/pattern, và retry/recovery thông thường được phân loại `TECHNICALLY_RESOLVABLE` — **không tạo mục Inbox**, tiếp tục vận hành an toàn. Kiểm chứng: test B (tiếp tục an toàn không nhắc Owner) và kiểm tra 5 supervisor (routing kỹ thuật không lọt vào câu hỏi Owner).

## 9. Hành vi dedup quyết định

`DECISION_ID` là **hàm băm định danh ổn định** (goal + task + loại quyết định + phạm vi + phiên bản bằng chứng). Cùng nguyên nhân chặn + cùng phạm vi + cùng phiên bản bằng chứng → **duy nhất 1 mục chưa giải quyết**. Gọi lại nhiều lần không tạo mục trùng (test K/L), restart process không tạo mục trùng (test L), restart lạnh giữa hai process khác nhau **vẫn thấy cùng một Decision ID** (test M).

## 10. Hợp đồng Owner Answer

Owner trả lời bằng **hợp đồng có cấu trúc**: đáp án phải chỉ đích danh `DECISION_ID` (hoặc lựa chọn duy nhất khớp khi chỉ có 1 mục mở), lựa chọn phải thuộc danh sách OPTIONS, phiên bản bằng chứng phải khớp. Đáp án hợp lệ được ghi thành bản ghi quyết định bền vững với `SCOPE` + `PROVENANCE` (hash đáp án, thời điểm, nguồn); phiên bản thô (transcript) **không bao giờ** trở thành sự thật bền vững (`raw_transcript_stored = False`).

## 11. Hành vi phạm vi phê duyệt

Mọi phê duyệt của Owner đều hẹp: **ONE_TIME** (một lần), nhắm **đúng 1 task/quyết định**, `auto_grants_nothing` — không tự động cấp quyền nào khác, không lan sang task/tệp/quyết định khác. Chứng minh trong test N/P và kiểm tra 8 supervisor.

## 12. Hành vi đáp án sai/hết hạn

Đáp án có option không tồn tại → **FAILED/INVALID_OPTION**. Đáp án có `DECISION_ID` đúng nhưng phiên bản bằng chứng sai → **FAILED/STALE_VERSION**. Đáp án cho mục đã giải quyết → **FAILED/ALREADY_RESOLVED**. Mục đã giải quyết **không bị hỏi lại** (test S/T). Mọi trường hợp fail-closed: hệ thống dừng và chờ, không tự diễn giải.

## 13. Progressive disclosure L1/L2/L3

Ba mức trình bày **cùng một nguồn sự thật bền vững**: L1 (tóm tắt ngôn ngữ thường cho người mới bắt đầu), L2 (chi tiết lý do, phương án, hậu quả), L3 (bằng chứng đầy đủ: con trỏ ledger, checkpoint, hash goal-state). Xem nhiều lần ở bất kỳ mức nào đều **read-only, idempotent** — mở trạng thái không kích hoạt thực thi. Kiểm chứng test W (L1/L2/L3 từ cùng một truth cho cùng một quyết định).

## 14. Project status view

`project_status_snapshot` trình bày: mục tiêu hiện tại, blocker nếu có, hành động an toàn tiếp theo, số quyết định Owner đang mở, số task đã thực thi/kiểm chứng/hoàn tất, và phân biệt Goal Pass vs Promotion. Được dùng cả trong hook info-only của FW01 (mọi điểm thoát của `step()` đều đính kèm trường `fw05_owner_experience` — không ảnh hưởng luồng điều khiển).

## 15. Trình bày Goal Pass vs Promotion

Khác biệt được nói **rõ ràng bằng văn bản**: "Mục tiêu đã hoàn tất và kiểm chứng, nhưng candidate vẫn chưa được phê duyệt phát hành." Goal Pass (mục tiêuDone + evidence) **không phải** Promotion (candidate UNPROMOTED chưa có quyết định Owner). Kiểm chứng test X: goal DONE, candidate .33 UNPROMOTED → `goal_passed=True`, `candidate_promoted=False`.

## 16. Trình bày QUALITY_REVIEW

Dừng chất lượng FW04 được chuyển vào trải nghiệm Owner: checkpoint `BLOCKED/QUALITY_REVIEW` bền vững, bản ghi trace `QUALITY_GATE`, và — khi thuộc trách nhiệm Owner — đúng **1 mục Inbox** với câu hỏi thường. Restart lạnh vẫn thấy cùng blocker + cùng next-safe-action `QUALITY_REVIEW:<task>`. Kiểm chứng test H/I/J và kiểm tra 10 supervisor.

## 17. Hành vi chất lượng xử lý được bằng kỹ thuật

Khi bằng chứng thiếu có thể bổ sung bằng **đường kiểm chứng kỹ thuật an toàn hiện có**, quyết định được định tuyến `TECHNICALLY_RESOLVABLE` — **không ngắt Owner**, tiếp tục vận hành. Chỉ khi Owner là chủ thể của việc cung cấp bằng chứng thì mới tạo mục Inbox (test I/J).

## 18. Chứng minh phục hồi cold-process

Chứng minh bằng **ranh giới subprocess thật** (hai process Python hoàn toàn tách biệt, không chia sẻ globals/mock): Process A viết trạng thái chặn (QUALITY_REVIEW/Owner Gate) và thoát; Process B import framework từ đầu, phục hồi đúng trạng thái, tạo ra **cùng một Decision ID**, không thực thi lại task đã xong, không tiến sang task khác, và trình bày đúng câu hỏi cho Owner. (test M/N; kiểm tra 11, 12 supervisor.)

## 19. Chứng minh decision resume

Luồng đầy đủ: task đến Owner Gate → mục Inbox được lưu → process kết thúc → Owner trả lời (ghi hợp đồng) → process mới khởi động → FW01 tiếp tục đúng trạng thái, mục chuyển `RESOLVED` với provenance đầy đủ, task không chạy lại. (test U/V; kiểm tra 12, 13 supervisor.)

## 20. Chứng minh không thực thi trùng lặp

Sau resume, hai lần xem trạng thái bởi hai subprocess độc lập đều báo **đúng 1 lần thực thi** của task (không thành 2). Resume dedup dựa trên **event ledger thật** — không có mutation trạng thái task record.

## 21. Shadow eval GT (READ-ONLY)

Bộ cây `/home/ubuntu/fw01_work/cert/game-truyen` được hash toàn bộ tệp trước và sau khi chạy mọi thao tác view FW05 (status snapshot, render L3). **Hash khớp hoàn toàn — byte-identical.** (Kiểm tra 15 supervisor: PASS.)

## 22. Shadow eval GP (READ-ONLY)

Bộ cây `/home/ubuntu/fw01_work/cert/gia-pha` tương tự: hash trước = hash sau. **Không có bất kỳ thao tác nào của FW05 chạm vào GT/GP.** Không sửa Game Truyện, Gia Phả, Logistics, Supabase/RLS hay deployment.

## 23. Bộ test FW05 mới

`test_fw05_owner_experience.py` — **29 test PASS**, phủ toàn bộ ma trận A–Z theo spec §32 (A–T: routing/dedup/contract/fail-closed; U–Z: resume/no-dup/progressive disclosure/Goal Pass vs Promotion/evidence-not-CoT/regression-intact) + 2 lớp test ranh giới subprocess thật (cold-process boundary, decision resume) + shadow eval READ-ONLY GT/GP.

## 24. Full regression

Toàn bộ: `python3 -m unittest discover` trên `.p2p/system` → **203/203 PASS** (174 test FW01–FW04 cũ + 29 FW05 mới), `NEW_UNEXPLAINED_FAILURES = 0`, không làm yếu test nào trước đó. Bộ FW04 quality-stop (6 test) và certification-consumption (9 test) nguyên vẹn.

## 25. Validator / control

`scripts/validate_p2p_development_framework.py`: **78/78 PASS**, 0 fail. Governance record `.33` tuân thủ `required_candidate_fields` của `lineage_contract`.

## 26. Secret scan

`gitleaks detect --no-git` trên cả 6 tệp thay đổi (module, test, hook FW01, supervisor, mint script, governance): **0 findings mỗi tệp**. (Lưu ý: quét toàn bộ repo không-git cho 67 finding thuộc baseline có từ trước — không phát sinh từ FW05; riêng các tệp FW05 không có finding nào.)

## 27. Independent supervisor

`scripts/fw05_supervisor.py` chạy trên **đường dẫn mã nguồn/state/thực thi thật** (không dựa trên tuyên bố): **16/16 PASS** — bao gồm: FW01 là loop duy nhất; FW05 không thể thực thi/chọn quyền; trace là bằng chứng không CoT; Inbox chỉ chứa quyết định Owner chính hãng; routing kỹ thuật không lọt ra ngoài; stable ID dedup qua process boundary; transcript không phải sự thật bền vững; phạm vi hẹp ONE_TIME; stale fail-closed; QUALITY_REVIEW bền vững; cold-process recovery thật; resume an toàn; không thực thi trùng lặp; Goal Pass ≠ Promotion; view read-only; không mutation dự án.

## 28. Tệp runtime thay đổi

| Tệp | Thay đổi |
|---|---|
| `.p2p/system/p2p_capabilities/fw05_owner_experience.py` | MỚI (~1.500 dòng): toàn bộ bề mặt FW05 |
| `.p2p/system/p2p_capabilities/tests/test_fw05_owner_experience.py` | MỚI: 29 test ma trận A–Z + subprocess boundary |
| `.p2p/system/p2p_capabilities/p2p_fw01_loop.py` | Hook info-only: đính kèm trường `fw05_owner_experience` vào kết quả `step()` tại mọi điểm thoát — **không đổi luồng điều khiển** |
| `scripts/fw05_supervisor.py` | MỚI: supervisor độc lập 16 kiểm tra |
| `scripts/mint_fw05_candidate.py` | MỚI: máy mint candidate .33 |

## 29. Tệp governance thay đổi

`governance/development-control.json`: **thêm đúng 1 record** candidate `8.4.7-C-codex.33` (UNPROMOTED, lineage anchor `.32`). Không sửa Development Charter, Capability Ledger hay roadmap (không cần thiết theo §41 — không có LIVE evidence từ fixture).

## 30. Candidate policy

Policy canonical: runtime changed (FW01 step() output được làm giàu + module/inbox mới) → **YES** → mint đúng **1** candidate UNPROMOTED kế nhiệm. Không ghi đè `.32`/`.31`/`.30` trở về trước. Không promotion, không release, không tag.

## 31. Candidate SHA và trạng thái

`8.4.7-C-codex.33`, `fw05-owner-experience-decision-trace`, **UNPROMOTED**.
Zip: `reports/candidates/fw05-owner-experience-decision-trace-candidate.zip`
SHA256: `a4c3161b711a1c9dae6870401f8135e0e77b445c7703ac7fa0ed9c983a06bbb9`
(deterministic: mtime cố định 2010-01-01, thứ tự tệp đã sắp xếp, DEFLATED 9; chứa module, test, hook FW01, supervisor + record governance.)

## 32. `.32` được giữ nguyên?

**CÓ.** `8.4.7-C-codex.32` (FW04 QUALITY STOP hardening, SHA `5985e0e5...cc376f6`) vẫn **UNPROMOTED**, nguyên bản, không sửa đổi — cùng `.31`/`.30` và các record trước đó.

## 33. Mutation dự án / Supabase / deploy

**Không có.** GT/GP byte-identical (mục 21–22), không chạm Logistics, Supabase/RLS, deployment, Council 8/8, không cài RepoWise. Không có web frontend sản xuất, không DB sản xuất, không daemon, không dịch vụ thông báo — chỉ CLI/text facade như §42 cho phép.

## 34. Hạn chế còn lại NOT_PROVEN

Theo tinh thần "không claim LIVE evidence từ fixture xác định": (a) các view FW05 mới được kiểm chứng bằng subprocess thật và shadow eval trên cây GT/GP, nhưng **chưa ai dùng thật end-to-end trong phiên tương tác phi-lập-trình-viên** (chưa có session Owner thật mở Inbox và trả lời); (b) các câu hỏi Owner trong test dùng dữ liệu mô phỏng (fixture) — đúng chuẩn fail-closed nhưng không thay thế bằng chứng vận hành sống; (c) tích hợp với các bề mặt CLI/beginner-status cũ (`p2p_decision_runtime.py render_beginner_status`) giữ nguyên API hiện có, chưa tái cấu trúc lớn — Owner kinh nghiệm vẫn qua 3 bề mặt riêng (status, inbox, decision).

## 35. Hành động Owner tiếp theo (chính xác)

Xét duyệt hoặc không xét duyệt candidate **`8.4.7-C-codex.33`** (SHA `a4c3161b...3a06bbb9`). Để tiếp tục vận hành: không cần Owner — hệ thống đã sẵn sàng với FW05 ACTIVE. Nếu Owner muốn mở Inbox/demo trong session tới, chỉ cần yêu cầu "xem hộp quyết định" — chỉ đọc, không kích hoạt thực thi.

## 36. Framework tiếp theo được khuyến nghị

`P2P-FRAMEWORK-06 — PRODUCTION AUTONOMY & RESILIENCE` — nhưng **KHÔNG tự động bắt đầu**. Session dừng tại `OWNER_FW05_CLOSURE_GATE` theo yêu cầu.

---

## TERMINAL VERDICT

`PASS / FW05_OWNER_EXPERIENCE_DECISION_TRACE_READY`

**DỪNG tại `OWNER_FW05_CLOSURE_GATE`. Không khởi động FRAMEWORK-06.**

### Chấp nhận cơ học (§43)

| # | Yêu cầu chấp nhận | Kết quả |
|---|---|---|
| 1 | Structured Decision Trace tồn tại | PASS — 15 trường hợp đồng, JSONL append-only |
| 2 | Không lưu private chain-of-thought | PASS — test C3 + kiểm tra 3 supervisor |
| 3 | Owner Decision Inbox bền vững | PASS — `.p2p/state/owner-inbox.jsonl` |
| 4 | Owner Gate chính hãng được phân loại | PASS — test B/C/D/E |
| 5 | Câu hỏi kỹ thuật không tới Owner | PASS — test A/F/G/H |
| 6 | Identity quyết định ổn định, dedup | PASS — test K/L/M |
| 7 | Đáp án Owner là bản ghi phạm vi, không transcript | PASS — test O/P + kiểm tra 7, 8 |
| 8 | Đáp án sai/hết hạn fail-closed | PASS — test Q/R/S + kiểm tra 9 |
| 9 | Progressive disclosure hoạt động | PASS — test W |
| 10 | Project status hoạt động | PASS — test X + hook FW01 |
| 11 | Goal Pass vs Promotion chính xác | PASS — test X + kiểm tra 14 |
| 12 | QUALITY_REVIEW tích hợp Owner Experience | PASS — test H/I/J + kiểm tra 10 |
| 13 | Chất lượng xử lý kỹ thuật không ngắt Owner | PASS — test I + kiểm tra 5 |
| 14 | Cold-process Owner Gate recovery VERIFIED | PASS — subprocess boundary thật |
| 15 | Decision resume VERIFIED | PASS — subprocess boundary thật |
| 16 | Không thực thi trùng lặp | PASS — test V + kiểm tra 13 |
| 17 | GT shadow READ_ONLY PASS | PASS — byte-identical |
| 18 | GP shadow READ_ONLY PASS | PASS — byte-identical |
| 19 | Regression FW01–FW04 PASS | PASS — 203/203 |
| 20 | NEW_UNEXPLAINED_FAILURES = 0 | PASS |
| 21 | Independent supervisor PASS | PASS — 16/16 |
