# P2P-CAPABILITY-RESEARCH-CONSOLIDATION-01 — Báo cáo Owner cuối (35 mục)

**Goal:** Hợp nhất nghiên cứu tích lũy và các khả năng đã chọn của P2P thành chân lý roadmap bền vững chính tắc (canonical). P2P không được quên các khả năng đã chọn vì một phiên chat kết thúc. Lập kế hoạch phát triển tương lai phải bắt đầu từ chân lý kho lưu trữ bền vững, không phải từ bộ nhớ trợ lý.

**Giới hạn đã tuân thủ:** chỉ đọc/governance-only — không sửa execution/mutation runtime, không sửa artifact `.41`, không promote phiên bản mới, không Zero-to-Project implementation. Phạm vi thay đổi đúng theo §25: `governance`, `roadmap`, `charter`, capability/research ledgers, task/goal planning metadata, validation scripts, reports.

**Nhánh:** `p2p-research-roadmap-consolidation-01` · Commit `2d5e667` · 8 files, 4888 insertions.

---

## 1. Official baseline đã khôi phục

| Hạng mục | Giá trị |
| --- | --- |
| Official baseline | `8.4.7-C-codex.41` |
| Artifact SHA-256 | `da835f8a48caf4536094ffdd82e3c65baa82da32aa9a7ae73714ee1f2e9c3d2d` |
| Promotion status | `PROMOTED_VERIFIED` (P2P-PROMOTE-41-01, approval `P2P-APR-20260821T035410Z-c41-official-baseline-promotion`) |
| Baseline trước | `8.4.7-C-codex.19` |

Xác minh bằng chứng cơ học: `development-control.json` đọc lại khớp tuyệt đối; artifact ZIP được extract lại SHA khớp; baseline không bị thay đổi trong suốt goal (`BASELINE_DRIFT = ABSENT`).

## 2. Repo / branch / HEAD

- Kho: `auth-f01` (GitHub `7roger89-web/P2P-upgrade-github-1`), nhánh mới `p2p-research-roadmap-consolidation-01`, HEAD `2d5e667`, LOCAL==REMOTE, đẩy thành công.
- GT (game-truyen): không chạm — HEAD/tree không đổi.

## 3. Nguồn / bản ghi đã khảo sát

`development-control.json` (architectural_invariants, roadmap 43 items, research_decisions, superlearn_principles, research_intake_ledger, canonical_capability_set), `capability-index.json` (159 bản ghi), `P2P-DEVELOPMENT-CHARTER.md`, `master-roadmap.md`, `current-roadmap.md`, `fact-leader/live-specs`, research-intake-ledger (RI-003), reports (C11–C43, FW01–FW06, Closure-01, Integration-01, Pilot-02, Promotion-Readiness-Review-01, Promote-41-01), `drift-policy.json`, `docs/p2p-development/framework/capability-skill-map.md`, seed inventory A–Z từ spec.

## 4. Tổng nguồn nghiên cứu đã reconcile

**26 bản ghi chính tắc** trong Research Adoption Ledger (`RA-EXT-001…RA-EXT-026`): 26 chủ đề từ seed A–Z (ngoại vi + nội bộ + Owner idea), mỗi bản ghi có provenance_status, selected/rejected ideas, p2p_translation, family, evidence_pointers.

## 5. Selected ideas count

**23 chủ đề được chọn ở mức độ nào đó** (SHIPPED 14 + VERIFIED 4 + PARTIAL 5). Riêng 26 chủ đề là phạm vi đã được Owner chọn/đối chiếu; trong đó 3 chủ đề vẫn ở mức "nguyên tắc được chọn nhưng chưa hoàn chỉnh" (PARTIAL).

## 6. Rejected ideas count

**1 nguồn bị từ chối hoàn toàn** (RA-EXT-007 Anvien — license/provenance không tương thích) + **sổ đăng ký rejected patterns gồm 21 mẫu vĩnh viễn** (Z-register, RA-EXT-026) được bảo tồn trong charter §7 và capability ledger với status REJECTED + lý do bảo tồn.

## 7. Implemented count

Các ý tưởng được chuyển thành IMPLEMENTED tại mức bản ghi nghiên cứu: 14 bản ghi SHIPPED (implemented và đã phát hành vào artifact/charter) + 4 VERIFIED (implemented + verified) — tổng **18 chủ đề đã implement xong ở mức đã được kiểm chứng hoặc phát hành**; 5 PARTIAL đã implement phần lõi.

## 8. Shipped count

**14** (RA-EXT-001, 002, 004, 006, 008, 011, 013, 014, 015, 016, 017, 018, 019, 020).

## 9. Verified count

**4** (RA-EXT-003 role-vs-skill, 022 beginner-first North Star, 025 provider-neutral control plane, 026 rejected-pattern register).

## 10. Planned count

**10 capability records PLANNED mới** trong capability-index (169 tổng) + **10 roadmap items PLANNED mới** trong development-roadmap.json (Z2P, Large-Goal completion, Context completion, Planner, Design composition, Code mutation, Orca extension, Multi-host Council, Drift sweep, Release lifecycle). Số bản ghi PLANNED hiện có trong capability-index: 39 (kế thừa lịch sử; chỉ 10 bản ghi mới được tạo và validate trong goal này).

## 11. Partial count

**5** (RA-EXT-009 NUI, 010 Visual Commander, 021 Large Goal, 023 decision trace, 024 drift watch).

## 12. Deferred count

**1** (RA-EXT-005 Semantica — DEFERRED theo quyết định Owner trước đó, ghi nhận không viết lại).

## 13. Unknown / chưa giải quyết

**1** (RA-EXT-012 Electron/desktop-control: không có bằng chứng chọn lựa bền vững — classified `UNKNOWN`, không được ngầm coi là đã chọn). Ngoài ra 1 claim được phân loại `PROVENANCE_NOT_RECOVERED / NOT_PROVEN` (RA-EXT-009 con số "174 faculties" — máy không tìm được artifact kho lưu trữ; không phải evidence of absence, không bị ghi REJECTED).

## 14. Capability families

**18 families** chính tắc trong development-roadmap.json: Owner Intent & Project Formation, Project Truth & Durable State, Research/Fact/Live-Spec Intelligence, Context & Retrieval, Goal Design Intelligence, Skills & Knowledge, Role/Team/Council, Execution Target/Provider/Model, Workspace/Session/Worktree Isolation, Large-Goal Autonomous Execution, Quality/Evidence/Evaluation, Owner Experience/Decision Trace, Safety/Authority/Permissions, Mutation Capability Ladder, Resilience/Recovery/Failover, UI/UX/Visual Intelligence, Obsolescence/Capability Drift, Release/Install/Project Lifecycle.

## 15. Major deduplications

Các chủ đề trùng lặp được hợp nhất về một canonical duy nhất, ví dụ: (a) ba nguồn skill-patterns A/C/M → một family `SKILLS_AND_KNOWLEDGE` với một nguyên tắc adoption duy nhất; (b) UI-UX Pro Max + NUI + Visual Commander (H/I/J) → một family `UI_UX_VISUAL_INTELLIGENCE`/`GOAL_DESIGN_INTELLIGENCE` chung; (c) Orca + Claude Code session + worktree (K/L/M/O) → `WORKSPACE_SESSION_ISOLATION` + `EXECUTION_AND_ORCHESTRATION`; (d) Manus + Hermes + Codex (N/O/P) → `MULTI_AI_INTEROPERABILITY` với identity ladder; (e) context research + token efficiency (R/S) → `CONTEXT_AND_RETRIEVAL`; (f) Large Goal + decision trace (U/W) → hai families liên kết (execution + experience); (g) drift watch (Y) + C35 provider-neutral → `OBSOLESCENCE_DRIFT` + `MULTI_AI_INTEROPERABILITY` tách bạch. Capability-index trước/giờ (159→169) đã đối chiếu không trùng id/tên (`DUPLICATE_CANONICAL_CAPABILITIES = 0`).

## 16. External sources mapped to cùng canonical capability

| Nguồn | Canonical capability |
| --- | --- |
| Agent Skills + awesome-cursor-rules-mdc + Matt Skills | `SKILLS_AND_LEARNING` family (FW02 skill intelligence) |
| UI-UX Pro Max + NUI + Visual Commander 4 | `GOAL_DESIGN_INTELLIGENCE` / C13-C14 design lineage |
| Claude Code session mgmt + Orca isolation + worktrees | `WORKSPACE_SESSION_ISOLATION` + `EXECUTION_AND_ORCHESTRATION` (C11/FW06) |
| Manus + Hermes + Codex | `MULTI_AI_INTEROPERABILITY` + identity ladder (C35/C36/C37/C38) |
| Context research + token-efficiency research | `CONTEXT_AND_RETRIEVAL` (C19, 35 mục) |
| Karpathy-style engineering + token research | `CONTEXT_AND_RETRIEVAL` + invariants DETERMINISTIC_FIRST/PROGRESSIVE_DISCLOSURE |
| Brigade typed-lifecycle + Superlearn principles + Orca lifecycle | `EXECUTION_AND_ORCHESTRATION` + invariants DETERMINISTIC_FIRST |
| C36/C38 live-cert evidence hosts | `MULTI_AI_INTEROPERABILITY` + live-cert lanes |

## 17. NUI status

RA-EXT-009: nguyên tắc design cognition registry **ADAPTED** (đã dùng làm nguồn của C13 beginner design-intelligence); claim cụ thể "174 canonical faculties" = **`PROVENANCE_NOT_RECOVERED / NOT_PROVEN`** theo cơ chế RI-003 — không có artifact kho lưu trữ ngoài tái hiện claim; theo quy tắc máy (`UNKNOWN_IS_NOT_SUPPORTED`) không được coi SUPPORTED, nhưng cũng **không được ghi REJECTED** (không phải evidence of absence). Invariant `faculties-are-not-agents` đã chặn pattern nguy hiểm (`174_NUI_FACULTIES_AS_AGENTS` REJECTED vĩnh viễn). Trạng thái terminal trong ledger: PARTIAL.

## 18. Visual Commander status

RA-EXT-010: ý tưởng đọc hiểu ý định thị giác, từ vựng style, visual recipes, đặc tả thị giác dày — **đã đăng ký làm đầu vào design-intelligence** (không phải router/agent độc lập). Trạng thái PARTIAL: đã góp vào C13 lineage và framework/capability-skill-map; composition hoàn chỉnh với aesthetics + NUI là mục PLANNED (RM-PRIORITY-DESIGN). Nguyên tắc composition bất biến: P2P là sole orchestrator; VC là cognition/skill/recipe provider.

## 19. Orca status

RA-EXT-011: subset có chọn lọc **đã ship** — C17 bounded parallel foreground execution (DONE) + FW06 lease/interruption (max_parallelism=1 mặc định, bounded fanout). Các pattern bị từ chối được chốt làm invariant: `UNBOUNDED_SWARM`, `NO_SWARM_FOR_ITS_OWN_SAKE`, không mở rộng permission tự động. Phần mở rộng candidate-compare/evaluate là mục PLANNED (RM-PRIORITY-ORCA-EXT), phụ thuộc C08.

## 20. Cursor rules MDC status

RA-EXT-013: awesome-cursor-rules-mdc/rules-mdc — **patterns được chọn, nguồn không vendored**. Bài học tải rule có phạm vi, mỗi bộ rule có provenance riêng, tránh preload toàn bộ → đã chuyển thành invariant chống `FULL_CONTEXT_PRELOAD` (trong never-reintroduce list, charter §7) và vào family `SKILLS_AND_KNOWLEDGE`. Không có bản ghi "chưa giải quyết" nào còn treo.

## 21. Context intelligence status

RA-EXT-019: lõi **đã ship** (C19 task-targeted retrieval DONE, family CONTEXT_AND_KNOWLEDGE 35 mục — family lớn nhất). Ba mảnh còn thiếu được ghi PLANNED: symbol-aware retrieval, token-bounded project/repo maps, adaptive context budget — gộp thành capability record `CONTEXT_INTELLIGENCE_COMPLETENESS` (PLANNED, không phụ thuộc mục bị block, có thể bắt đầu ngay).

## 22. Large Goal status

RA-EXT-021: lõi **đã ship** — C12 bounded foreground execution + C15 bounded delegation (cả hai DONE). Mảnh còn thiếu: full adaptive goal-graph automation (checkpoint/resume + continuation không hỏi sau mỗi tác vụ) — ghi PLANNED (`LARGE_GOAL_COMPLETENESS`), phụ thuộc C08 (được Owner chủ động DEFERRED trước đó, lý do ghi nhận nguyên trạng). Large Goal = bounded autonomous progression, không phải unbounded autonomy (`NO_UNBOUNDED_BACKGROUND_AUTONOMY`).

## 23. Provider-neutral execution status

RA-EXT-025: **VERIFIED** — C35 provider-neutral runtime PROMOTED_VERIFIED trong baseline .41; identity ladder đầy đủ (ROLE≠SKILL, BACKEND≠PROVIDER, PROVIDER≠MODEL, MODEL≠TOOLSET, REGISTRY≠ROUTER); adapters chỉ nằm trong adapter modules. Chạy ngược validator trên artifact .41 runtime: không lock-in, không provider hardcoded trong core.

## 24. Zero-to-Project status

RA-EXT-021/022/019/023 → capability record `ZERO_TO_PROJECT_INTENT_COMPILER` = **PLANNED, chưa implement** (đúng chỉ thị spec §9: DO NOT implement Zero-to-Project trong goal này). Compose FW00–FW06 primitives sẵn có; không tạo orchestrator cạnh tranh. Bar định nghĩa-phase: không thay đổi runtime. Điều kiện trước: Large-Goal completion + Context Intelligence completion.

## 25. Mutation ladder

| Mức | Trạng thái bằng chứng |
| --- | --- |
| READ_ONLY | STRONGLY_EVIDENCED (không đột biến trên GT/GP/Logistics xuyên suốt toàn bộ lifecycle) |
| BOUNDED_DOCUMENTATION_WRITE | VERIFIED isolated/non-production (Pilot-02: mutation có kiểm soát, chuỗi authority verified, rollback M2==M0 byte-identical) |
| DOCUMENTATION_WRITE → BOUNDED_CODE_CHANGE → MULTI_FILE_CODE_CHANGE → DEPENDENCY_CHANGE → DATABASE_CHANGE → DEPLOYMENT | **KHÔNG tuyên bố SUPPORTED** — mỗi mức tương lai cần primitive + receipt + rollback + Owner policy riêng. Mức BOUNDED_CODE_CHANGE đã có roadmap record PLANNED (RM-PRIORITY-CODE-MUTATION, priority 6). |

## 26. Obsolescence / drift status

RA-EXT-024: chính sách **đã ship** (`drift-policy.json`, invariant `DRIFT_FAIL_CLOSED`, ngữ nghĩa `CERTIFIED != CURRENTLY_ELIGIBLE`); cơ chế `CAPABILITY_DRIFT_REVALIDATION_SWEEP` PLANNED — chưa sweep toàn bộ capabilities; auth/host hiện tại vẫn `UNKNOWN_NOT_PROBED` sau các lần chuyển host.

## 27. Rejected patterns

21 patterns vĩnh viễn trong rejected register (charter §7 + capability ledger REJECTED với lý do bảo tồn): TASK_AS_AGENT, SECOND_TASK_TRUTH_STORE, SECOND_EXECUTOR, COMPETING_ROUTER, UNBOUNDED_SWARM, FULL_CONTEXT_PRELOAD, FULL_CHAT_AS_PROJECT_STATE, BLIND_RETRY, HOST_OUTPUT_AS_FINAL_EVIDENCE, AUTO_PROMOTION_AFTER_GOAL_PASS, 174_NUI_FACULTIES_AS_AGENTS, HOSTS_AS_CANONICAL_AGENTS, PROVIDER_HARDCODE_IN_CORE, BACKGROUND_DAEMON_WITHOUT_SEPARATE_GOAL + permission bypass, auto-approve-all, dependency-chain autonomy, scraping as core, GitHub Actions control plane, single-vendor lockin, AI self-report as evidence. Goal tương lai chạm bất kỳ pattern nào phải mở lại minh bạch với Owner approval.

## 28. Roadmap coverage gate

Invariant mới chính tắc (`ROADMAP_COVERAGE_GAP_DETECTED` + `OWNER_SELECTED_CAPABILITY_RECORDED`): mọi đề xuất roadmap lớn hoặc Goal phát triển lớn bắt buộc reconcile với research-adoption-ledger + development-roadmap; nếu bản ghi SELECTED/PLANNED/PARTIAL liên quan vật chất bị bỏ sót không lý do → surfaced `ROADMAP_COVERAGE_GAP`. Deferral được phép — WHY phải được ghi.

## 29. Runtime roadmap-reader status

Trung thực: runtime hiện tại **không tự động tiêu thụ roadmap** khi chọn Goal phát triển tiếp (goal choice theo heuristic charter §6 + chỉ thị Owner). Trạng thái tuyên bố: **`ROADMAP_AWARE_DEVELOPMENT_PLANNER = PLANNED` (không phải VERIFIED)** — capability record mới `ROADMAP_AWARE_DEVELOPMENT_PLANNER_PLANNED` đã thêm, read-only, không bao giờ ghi đè Owner Gates.

## 30. Capability Ledger update

`capability-index.json`: 159 → **169** capability records. 10 bản ghi PLANNED mới (append-and-reconcile; không bản ghi hiện có bị sửa/xóa): ZERO_TO_PROJECT_INTENT_COMPILER, LARGE_GOAL_COMPLETENESS, CONTEXT_INTELLIGENCE_COMPLETENESS, ROADMAP_AWARE_DEVELOPMENT_PLANNER_PLANNED, GOAL_DESIGN_INTELLIGENCE_COMPOSITION, BOUNDED_CODE_MUTATION_PRIMITIVE, ORCA_BOUNDED_CANDIDATE_FANOUT, MULTIHOST_COUNCIL_CERTIFICATION, CAPABILITY_DRIFT_REVALIDATION_SWEEP, RELEASE_INSTALL_LIFECYCLE_HARDENING. Từ vựng status mở rộng; last_reviewed + review_notes thêm. Dedup check: `DUPLICATE_CANONICAL_CAPABILITIES = 0`.

## 31. Development Charter update

`P2P-DEVELOPMENT-CHARTER.md` (bản chiếu human-readable của invariants chính tắc): header bổ sung 2 nguồn chính tắc mới (research-adoption-ledger.json + p2p-development-roadmap.json); §3 bổ sung 6 hàng invariant mới trong projection table (ROADMAP_IS_LIVING_TRUTH, OWNER_SELECTED_CAPABILITY_RECORDED, RESEARCH_PROVENANCE_NOT_AUTHORITY, SELECTIVE_ADOPTION, ROADMAP_COVERAGE_GAP_DETECTED, roadmap-reader honesty); §6 thêm coverage-gate; §7 thêm cross-reference rejected register đầy đủ. Nguồn chính tắc vẫn là `governance/development-control.json` (architectural_invariants không bị viết lại; consolidation ghi vào `canonical_source_index` + `consolidation_records`).

## 32. Validation results

`scripts/rail_consolidation_validator.py` (fail-closed):

| Hằng số | Kết quả |
| --- | --- |
| DANGLING_DEPENDENCIES | **0** |
| DUPLICATE_CANONICAL_CAPABILITIES | **0** |
| ROADMAP_UNKNOWN_REFERENCES | **0** |
| NEW_SECRET_FINDINGS | **0** |
| BASELINE_DRIFT | **ABSENT** |
| Ledger/roadmap baseline SHA | khớp `.41` tuyệt đối |

```
VALIDATION: ALL GOVERNANCE CONSOLIDATION CHECKS PASS (fail-closed vocabulary)
```

## 33. Files changed (8)

| File | Loại |
| --- | --- |
| `governance/research-adoption-ledger.json` | MỚI — canonical machine-readable |
| `docs/RESEARCH-ADOPTION-LEDGER.md` | MỚI — human projection |
| `governance/p2p-development-roadmap.json` | MỚI — canonical machine-readable |
| `docs/P2P-DEVELOPMENT-ROADMAP.md` | MỚI — human projection + beginner-first view |
| `docs/p2p-development/capability-ledger/capability-index.json` | SỬA — +10 PLANNED records |
| `docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md` | SỬA — invariants projection mới |
| `governance/development-control.json` | SỬA — canonical_source_index + consolidation_records |
| `scripts/rail_consolidation_validator.py` | MỚI — validation governance |

**Không chạm:** runtime, artifact .41 ZIP (byte không đổi), GT/Gia Phả/Logistics, approval records, promotion status (.41 giữ nguyên PROMOTED_VERIFIED, không mint .42).

## 34. Next 5–10 roadmap priorities (cơ học, theo nguyên tắc xếp hạng)

Nguyên tắc xếp hạng: **Owner value + dependency necessity + safety maturity + evidence gap + architectural leverage** — không theo độ mới, không theo Owner recency, không theo "oldest idea first".

| # | Priority | Tại sao vị trí này |
| --- | --- | --- |
| 1 | RM-Z2P Zero-to-Project (Intent Compiler) | Giá trị Owner cao nhất (North Star trực tiếp); compose FW00–FW06; không tạo orchestrator cạnh tranh |
| 2 | RM-PRIORITY-LARGE-GOAL Large-Goal completion | Điều kiện tiếp tục của #1; lõi C12/C15 đã DONE |
| 3 | RM-PRIORITY-CONTEXT Context Intelligence completion | Read-only; nâng mọi goal sau; evidence gap còn lại của family lớn nhất; **không phụ thuộc mục bị block** |
| 4 | RM-PRIORITY-PLANNER Roadmap-aware planner | Máy hóa coverage gate; read-only |
| 5 | RM-PRIORITY-DESIGN Goal design/visual composition | C14 nền tảng đã PROMOTED_VERIFIED; provenance NUI một phần chấp nhận được |
| 6 | RM-PRIORITY-CODE-MUTATION Bounded code mutation | Mức 2 của ladder; cần authority/evidence/rollback riêng |
| 7 | RM-PRIORITY-ORCA-EXT Candidate fanout | Nâng chất lượng quyết định; chờ C08 |
| 8 | RM-PRIORITY-MULTIHOST-COUNCIL | Bằng chứng host bị block (C09/C27) — không thể xếp cao hơn |
| 9 | RM-PRIORITY-DRIFT-SWEEP Drift revalidation | Read-only, làm sạch claim lỗi thời |
| 10 | RM-PRIORITY-RELEASE-LIFECYCLE Release/install hardening | Cần trước khi Z2P chạm dự án chính thức |

## 35. Exact next Owner decision

**Goal tiếp theo được đề xuất cơ học: RM-PRIORITY-CONTEXT — Context Intelligence completion** (symbol-aware retrieval + token-bounded project/repo maps + adaptive context budget), vì:

1. **Tại sao đứng đầu trong các mục sẵn sàng:** RM-Z2P (#1) có giá trị cao nhất nhưng điều kiện trước của nó (Large-Goal completion + Context completion) chưa thỏa mãn; trong các mục không bị block, Context completion có đòn bẩy kiến trúc cao nhất — nó nâng chất lượng và chi phí của mọi goal sau, kể cả Zero-to-Project. RM-PRIORITY-PLANNER (#4) phụ thuộc phần nào vào Context completion để hoạt động hiệu quả.
2. **Composes các nghiên cứu/capability đã chọn:** RA-EXT-019 (context research), RA-EXT-004 (engineering discipline DETERMINISTIC_FIRST/PROGRESSIVE_DISCLOSURE), C19 lõi đã DONE, family CONTEXT_AND_KNOWLEDGE 35 mục.
3. **Prerequisites đã thỏa:** không có dependency trên mục bị block; invariant DETERMINISTIC_FIRST + PROGRESSIVE_DISCLOSURE đã ship; validation không phát hiện thiếu phụ thuộc (`DANGLING_DEPENDENCIES = 0`).
4. **NOT_PROVEN còn lại:** symbol-aware retrieval trên repository thật, token-bounded maps, adaptive context budget — chưa có bằng chứng verified trên repo thực; đây chính là scope của goal đề xuất.

> **Approve or reject the recommended next P2P development Goal.**

**STOP** — không tự implement, không implement Zero-to-Project, không promote mới.

---

## TERMINAL VERDICT

`PASS_WITH_DISCLOSURES / P2P_CANONICAL_RESEARCH_AND_ROADMAP_CONSOLIDATED`

**Disclosures:** (1) claim 174 faculties (NUI) = `PROVENANCE_NOT_RECOVERED / NOT_PROVEN`; (2) 1 nguồn = UNKNOWN (Electron); (3) 1 nguồn REJECTED (Anvien); (4) multi-host Council = NOT_PROVEN; (5) runtime roadmap-reader = PLANNED, không VERIFIED; (6) 5 bản ghi PARTIAL chưa hoàn chỉnh theo thiết kế.

```
RESEARCH_ADOPTION_LEDGER = CANONICAL
P2P_DEVELOPMENT_ROADMAP = CANONICAL
OWNER_SELECTED_CAPABILITIES_DURABLY_RECORDED = VERIFIED
ROADMAP_AWARE_DEVELOPMENT_PLANNER = PLANNED
```
