# Product Architecture — P2P (Chuẩn tắc)

File chuẩn tắc của kiến trúc sản phẩm P2P. Máy đọc; người đọc dễ hiểu. Đây là bản tổng hợp xác định từ các bằng chứng C01–C43, không thay đổi runtime.

**Nguồn suy diễn:** `governance/development-control.json` (architectural_invariants, roadmap), `docs/p2p-development/capability-ledger/capability-index.json`, terminal reports C08–C43, `docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md`. Khi có mâu thuẫn, các nguồn chuẩn tắc gốc được ưu tiên.

## Nguyên tắc bắc kim (North Star)

> Người dùng không kỹ thuật nói một câu — "Tiếp tục hoàn thiện dự án" — và P2P làm phần còn lại một cách an toàn, có thể kiểm chứng, có thể quay lại.

## POLYGLOT_BY_EVIDENCE_V1 — Hybrid theo bằng chứng

P2P không trung thành với một ngôn ngữ và cũng không tự động tăng số ngôn ngữ vì AI có thể viết chúng. **Existing stack is the default.** Một ngôn ngữ/runtime mới chỉ được thêm khi nó giải quyết một capability hoặc bottleneck thật với lợi ích vật chất lớn hơn complexity vận hành.

Quy tắc mặc định:

- Web UI mới có thể ưu tiên Next.js/TypeScript khi phù hợp với product surface, nhưng không rewrite một UI đang hoạt động chỉ để đổi framework.
- Python được ưu tiên khi ecosystem hiện có phù hợp với AI/data/research/business orchestration hoặc khi project đã có Python authority.
- Rust/C++/native code chỉ được đưa vào hot path đã đo; không coi tốc độ lý thuyết là bằng chứng.
- Trước khi quy lỗi cho Python hoặc framework, kiểm tra database, network, storage/document I/O, serialization, external API/process và thuật toán.
- Nếu thêm native component, giữ boundary nhỏ, typed/stable, benchmark trước-sau và có rollback/removal path. Không rewrite toàn hệ thống để tối ưu một đoạn nóng.
- Một ngôn ngữ đủ thì dùng một. Polyglot là hệ quả của capability cần thiết, không phải KPI kiến trúc.
- Coding-agent capability không tự cấp lý do thêm runtime, microservice, queue, daemon, database hoặc framework.

Mọi đề xuất thêm ngôn ngữ/runtime phải có tối thiểu: `MEASURED_NEED`, `WHY_CURRENT_STACK_INSUFFICIENT`, `SMALLEST_BOUNDARY`, `BEFORE_AFTER_ACCEPTANCE`, `OPERATIONS_COST`, và `ROLLBACK_PATH`. Thiếu bằng chứng vật chất => `DEFER_UNTIL_NEEDED`.


## RF01 — Development framework boundary

RF01 is a noncanonical development-plane projection on sealed `.74`; it is
not a runtime architecture change and does not replace the governance JSON,
FACT_LEDGER/Live Specs, task state, execution ledger, approval policy, or
release gates. Official canonical baseline remains `.19`; `.74` is sealed and
UNPROMOTED. CPT01-R2 is preserved as `HOST_CAPABILITY_BLOCKED` with
`EXTERNAL_HOST_CAPABILITY_LIMITATION`.

The product fast loop is:

`Business/Owner Outcome → Minimum Product Truth → Product/UX Synthesis →
Interactive Prototype → Owner Review → Visual/Product Reference Lock → Real
Implementation → Targeted Tests → Human Outcome Test`.

The assurance/release loop is separate:

`Risk-Proportional Hardening → Independent Verification → Release`.

### DesignArena như bề mặt thay thế được trong product fast loop

Khi chọn DesignArena cho frontend/sản phẩm, route theo bounded outcome thay vì mặc định chọn Full-Stack:

- Web Apps: mặc định cho app shell và vertical slice frontend không cần persistence.
- UI Component: chỉ dùng khi một widget khó đáng một trận thiết kế riêng.
- Data Visualization: dùng cho timeline, comparison matrix, lineage hoặc vùng phân tích dày.
- Image-to-App: chỉ dùng khi đã có visual reference thắng và fidelity rebuild có giá trị.
- Full-Stack: dùng khi database/auth/storage là acceptance thật; không để Supabase template tự biến thành product architecture.
- DesignArena không bao gồm Arena AI Agent Mode. Khi đã chốt winner, Control Tower rời DesignArena và chọn executor tích hợp riêng phù hợp với repo/runtime.

Cẩm nang chi tiết: `docs/p2p-development/DESIGNARENA-EXECUTION-PLAYBOOK.md`.

DesignArena vẫn là executor/tool surface. Nó không thay thế kiến trúc dự án, task authority, P2P routing, evidence, Owner Gates hay release authority. Capability chính thức mới hơn của DesignArena luôn thắng snapshot cũ.

The product state model is `IDEA → PROTOTYPE → OWNER TRUTH → IMPLEMENTATION →
SYSTEM TRUTH → VERIFICATION → RELEASE TRUTH`. OXP is a read-only projection
over canonical/system truth and answers doing, finished, next, blocked, need
to decide, safe to do nothing, and safe-to-execute questions. It never writes
state or grants authority. Human acceptance is an observable outcome where
possible; “Owner can determine the item needing attention within 30 seconds”
is an example, not a fabricated result.

Assurance is proportional to risk: preview/focused check for low risk,
targeted functional checks for normal risk, stronger persistence/data checks
for durable state, and independent verification plus Owner approval for auth,
migration, destructive, canonical, or release claims. One capable agent is
the default execution unit; a second verifier is added only when risk or
independence requires it. No new memory graph, vector DB, daemon,
orchestration platform, autonomous promotion, or unbounded subagent system is
introduced by this projection.

Required report disclaimer: `Implemented against sealed .74 NONCANONICAL DEVELOPMENT BASE. Official canonical baseline remains .19. Release/promotion authority remains deferred due to external GitHub private repository host-protection limitation.`

## Các bất biến kiến trúc (19 điều, đã chốt từ C25)

Được giữ nguyên trong `governance/development-control.json → architectural_invariants`. Tóm tắt: đường dẫn dọc bắt buộc (nguồn → FACT_LEDGER → phê duyệt promotion → Live Specs → runtime → eval/RAG bị ảnh hưởng → drift → rollback → phê duyệt cuối gắn hash → kiểm tra lại hash → release/deploy); phê duyệt không thể biến gate FAIL thành PASS; runtime không giữ bản sao riêng của model ID/giá/bug; evidence có authority (FRESH_EXECUTION_CAPSULE_RECOVERY, ROLE_QUORUM); session death phải phục hồi được; mọi cài đặt giữ owner-gate và rollback.

## Năm lớp kiến trúc

| Lớp | Vị trí | Nội dung | Bằng chứng mốc |
| --- | --- | --- | --- |
| 1. Truth & Governance | `governance/`, `docs/p2p-development/capability-ledger/` | FACT_LEDGER, Live Specs, development-control, approvals, ledger khả năng | C10, C16, C25, C26 |
| 2. Durable State & Recovery | `.p2p/system/p2p_capabilities/task_state.py`, capsule | Trạng thái nhiệm vụ sống sót qua phiên; capsule phục hồi tiến trình mới; ATLAS | C11, C18, C21, C40 fresh-process recovery |
| 3. Context & Knowledge | `context_*.py`, manifest/envelope/cache, RAG boundaries | Bối cảnh có authority, DELIVERED ≠ READ, cache-aware reuse | C19, C36 |
| 4. Roles, Council & Execution | `role_*.py`, `selection_*.py`, `routing.py`, execution, failover, host, backends | 8 vai trò chuẩn tắc; quorum 8/8; chọn lựa thích nghi (SINGLE_ROLE/SMALL_REVIEW_SET/FULL_COUNCIL_REQUIRED); thực thi giới hạn; failover fail-closed | C35, C37, C38, C39 |
| 5. Beginner Surface & Skills | `beginner.py`, `.agents/skills/` (63 skill), `p2p_install_release.py` | Câu lệnh một dòng; gói cài đặt + install/upgrade/rollback/doctor | C13, C35, C40, C43 |

## Mô hình dữ liệu chính

- **Task State** (`task_state.py`): trạng thái nhiệm vụ bền vững, được capsule đóng gói.
- **Evidence** (`evidence.py`): bằng chứng có authority; `DELIVERED != READ` (C36).
- **Approval records** (`.p2p/approvals/` hoặc `governance/approvals/`): quyết định gắn với hash gói chính xác; không chấp nhận "yes" chung chung.
- **Gate reports** (`.p2p/gates/` hoặc `docs/p2p-development/research/release-gates-20260818/`): quyết định release/deploy cuối.
- **Package**: gói cài đặt bất biến, định danh bằng SHA-256 (hiện tại: `e7f62384…`, release `c40-promoted-pilot-release-draft`).

## Mô hình cài đặt (production model)

1. Gói phát hành bất biến (hash-bound) trên GitHub Releases.
2. Owner chỉ thị cài vào dự án X.
3. Máy tạo snapshot an toàn (canonical truth + tree fingerprint) trước khi chạm.
4. Cài bằng `p2p_install_release.py install` với collision owner-gate (fail-closed, rename-backup audit).
5. Post-install doctor HEALTHY; rollback readiness đã chứng minh (rollback fingerprint khớp nguồn).
6. Activation: người dùng nói "Tiếp tục hoàn thiện dự án" → P2P đề xuất task tiếp theo an toàn (read-only prompt design).
7. Rollback bất cứ lúc nào: "rollback dự án X" → quay về đúng trạng thái trước cài, vân tay khớp tuyệt đối.

## Biên giới an toàn

- **Không chạm dự án nào ngoài chỉ thị Owner** (Logistics = DO_NOT_INSTALL_YET).
- **Không tự promotion/release/deploy** — mọi promotion yêu cầu Owner chỉ thị ràng buộc hash.
- **Hội đồng**: `HISTORICAL_SINGLE_HOST_LIVE_COUNCIL_8_OF_8=TRUE`; `CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN=FALSE` / `NOT_PROVEN`; C43 chỉ là bounded one-role smoke và không nâng cấp current Council proof.
- **RAG**: không tồn tại theo thiết kế hiện tại (NOT_APPLICABLE).
- **Evals**: chưa có kết quả thử nghiệm ghi nhận (disclosed).

## Kế thừa Codex Edition

Kiến trúc Codex Edition (152 file nguồn `source/8.4.6-C/`, 8 hồ sơ agent QUORUM, 89 skill) được bảo tồn nguyên trạng; P2P runtime không phụ thuộc vào nó nhưng đóng gói nó trong gói cài đặt để các dự án hưởng lợi.
