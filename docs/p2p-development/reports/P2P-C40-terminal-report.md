# P2P-C40 — TERMINAL REPORT

**GOAL_ID:** P2P-C40

GOAL_TERMINAL_STATUS: PARTIAL/INSTALLABLE_PACKAGE_VERIFIED_PILOT_INCOMPLETE

**GOAL_BASE_COMMIT:** `e826327` (C39 terminal HEAD; regression baseline `8b751f6`)

CANDIDATE_REQUIRED: YES (deterministic; runtime_changed=True, governance_changed=True)

**CANDIDATE_SHA256:** e7f62384c8e51ef9c32e903688126642521d9570b648602fcf530aab25cbdc56

**CANDIDATE_LABEL:** P2P-8.4.7-C-Codex-Edition-v24-c40-project-usable-release-pilot-candidate-v1.zip

**ROADMAP_STATUS:** roadmap.items chứa mục `C40 — DONE`; `roadmap.current = C40/DONE`

**DEVELOPMENT_CONTROL_STATUS:** `current_development` UNTOUCHED — retained as C31/BLOCKED_TERMINAL historical snapshot — explained semantics per C35R/C38 precedent; closure machine CONSISTENT, 0 hard findings

**CAPABILITY_LEDGER_SYNC:** gói cài đặt chứa toàn bộ capability ledger (9 profiles + `.p2p/system` đầy đủ); cài đặt pilot khớp 1382/1382 mục footprint

**CANDIDATE_STATUS:** MINTED — exactly 1, UNPROMOTED

**SUPERVISOR_VERDICT:** CONSISTENT (0 hard, 1 explained)

**PROMOTION_STATUS:** UNPROMOTED — Owner Promotion Gate chưa được Owner ra quyết định

---

## 1. Tóm tắt cho Owner (tiếng Việt, đơn giản)

C40 đã hoàn tất ở lane **PARTIAL / INSTALLABLE_PACKAGE_VERIFIED_PILOT_INCOMPLETE** — lane được hợp đồng §30 định nghĩa sẵn cho đúng trạng thái này. Lần đầu tiên, P2P có một **gói cài đặt dạng chung (generic installable package) hoàn chỉnh, an toàn, deterministic và kiểm chứng được**, đã được **cài đặt và chạy thật trên pilot Game Truyện cô lập** (bản sao kho 7roger89-web/game-truyen-github, nhánh `p2p-c40-pilot`, KHÔNG merge vào dự án chính). Phạm vi bằng chứng của C40 dừng đúng ở đây: gói cài đặt dạng chung đã được kiểm chứng chất lượng (manifest + 1382 footprint hash khớp tuyệt đối, determinism), nhưng pilot Game Truyện **chưa hoàn tất hợp đồng rollback dự án pilot** (§20 PILOT_PROJECT_ROLLBACK — chưa chứng minh pilot quay về đúng `PILOT_SOURCE_REVISION` bằng fingerprint nguồn), nên chưa đạt full PASS bar.

Chủ dự án là người mới bắt đầu, không biết kỹ thuật — C40 chứng minh rằng việc dùng P2P chỉ cần **một câu tiếng Việt đơn giản** ("Tiếp tục hoàn thiện dự án"). P2P đã tự đọc 3 tài liệu của dự án (PROJECT_BRIEF, TASKS.md, WORLD.md), tự chọn backend qua cổng an toàn failover (đúng máy C39 vừa được chứng nhận), gửi nhiệm vụ, và trả về việc cần làm tiếp theo **T14A — NPC tuần tra phản ứng ở tick kế tiếp**, khớp chính xác file TASKS.md thật của dự án. Câu trả lời được **xác nhận độc lập** bằng cách đọc trực tiếp API Manus (không tin vào "lời tự khai" của hệ thống).

Các điểm an toàn chính:

- Khi cài đặt gặp **file trùng tên với file dự án** (AGENTS.md), P2P **không ghi đè âm thầm**: file dự án được sao lưu nguyên vẹn với mã hash, đường dẫn khôi phục được ghi lại — mọi thứ có thể đảo ngược.
- P2P có thể **nâng cấp và rollback**: cài bản cũ 19 → nâng lên bản mới → rollback về đúng bản cũ → cài lại bản mới, sau mỗi bước hệ thống tự kiểm tra sức khỏe (doctor) đều HEALTHY.
- Toàn bộ **file dự án Game Truyện không thay đổi một byte nào** trong suốt quá trình (1382 mục đã kiểm tra hash).
- Không có lỗi test mới nào do C40 gây ra (NEW_UNEXPLAINED_FAILURES = 0); quét bí mật sạch; không merge/promotion/release/deploy.

## 2. Mục tiêu và phạm vi C40

C40 — Project-Usable Release & Pilot Installation: biến toàn bộ hệ P2P (runtime `.p2p/system`, capability ledger, agent profiles, governance subset cài đặt được, scripts cài đặt) thành **một gói zip cài đặt được, deterministic, có manifest + footprint hash đầy đủ**, với chuỗi máy **install / upgrade / rollback / doctor** sử dụng được (single machine interface `scripts/p2p_install_release.py`), chứng minh trên dự án thật qua pilot Game Truyện.

Bắt đầu từ starting truth C39 đã xác minh: HEAD remote `e826327`, terminal C39 `PASS / GOVERNED_LIVE_FAILOVER_READY`, candidate C39 SHA khớp governance (evidence `c40-starting-truth-verification.json`).

## 3. Thiết kế gói cài đặt (REUSE > CREATE)

Pipeline "release chính thức" (`package_release.build` → `install.sh`) bị chặn fail-closed từ C35 do dòng phát triển 8.4.7-C-codex.24 chưa được promotion về baseline chính thức 19 — đây là **fail-closed có chủ đích**, không tìm đường vòng. C40 **tái sử dụng** chính machinery candidate-mint đã được kiểm chứng qua C33/C35/C37/C39 (mẫu gói đã có manifest, footprint hash, determinism), **bổ sung** layout cài đặt đầy đủ: `runtime/` (toàn bộ `.p2p/system`, 1350 file), `.codex/agents/` (9 agent profiles), `governance/` (tập con cài đặt được — approval/drift/fact-ledger/live-specs/…; KHÔNG nhúng `development-control.json` trạng thái phát triển), `scripts/` (máy cài đặt mới), VERSION/manifest/release.json.

Khóa thiết kế: **determinism đóng gói** — build lại 2 lần cho cùng một SHA (`e7f62384…`; bằng chứng `c40-package-build.json`); **footprint hash** 1382 mục khớp tuyệt đối nguồn đã commit (`c40-package-verify-evidence.json`); **không nhúng secret** (quét sạch).

Máy cài đặt mới `scripts/p2p_install_release.py` (REUSE+EXTEND trên convention `update_from_release.py`/`doctor.py`/`install.sh`):

- `install`: FRESH_INSTALL / LEGACY_SYSTEM_UPGRADE / SAME_VERSION_REINSTALL (idempotent); **collision policy** `owner-gate` (dừng, mặc định) hoặc `rename-backup` (sao lưu + hash + ghi receipt) — không bao giờ ghi đè âm thầm.
- `upgrade`: yêu cầu snapshot trước nâng cấp; giữ `release.json` phiên bản cũ để rollback biết đường về.
- `rollback`: khôi phục từ snapshot; trên FRESH_INSTALL (không có trạng thái cũ) được chứng minh là no-op đúng semantics — không có gì để khôi phục.
- `doctor`: kiểm tra phiên bản, marker, footprint, capability eligibility, upgrade/rollback status.

## 4. Bằng chứng (Proofs)

| Proof | Kết quả | Bằng chứng |
|---|---|---|
| Xây gói: determinism 2 lần cùng SHA, 1382/1382 hash khớp | PASS | `c40-package-build.json`, `c40-package-verify.json`, `c40-package-verify-evidence.json` |
| FRESH_INSTALL trên fixture sạch (1371 file quản lý) | PASS | `p2p-state/c40-install-evidence.json` (backup `/home/ubuntu/p2p-c40-evidence-backup`) |
| SAME_VERSION_REINSTALL idempotent (không nhân bản file) | PASS | `c40-install-evidence.json` |
| Va chạm file dự án AGENTS.md → backup rename, hash bảo toàn, receipt | PASS — COLLISIONS_BACKED_UP | `c40-install-collision.json` |
| Upgrade: bản cũ 19 (MARKER_MISSING) → 24 → rollback về đúng 19 → cài lại 24; doctor HEALTHY mọi bước | PASS | `c40-upgrade-proof.json` |
| Pilot: cài vào kho Game Truyện thật (nhánh cô lập `p2p-c40-pilot`, collision rename-backup) | PASS — 1380 file quản lý | pilot evidence + backup `p2p-state/` |
| **Pilot task qua chính P2P đã cài**: capsule 3 tài liệu dự án, gate RETRY_SAME_TARGET, 1 nhiệm vụ Manus bounded, SUCCEEDED | PASS — answer "T-next: T14A — NPC tuần tra phản ứng…" khớp TASKS.md thật | `c40-pilot-dispatch.json`, `c40-pilot-observation.json`, `c40-messages-dTCyg9pA7h6V9YXYwuMHAR.json` (task `dTCyg9pA7h6V9YXYwuMHAR`) |
| **Fresh-process recovery**: tiến trình mới hoàn toàn (không transcript, không bộ nhớ) đọc JSON trạng thái bền vững → capsule → task mới `ZQVbWT43P6vmVPh78i2bSg` → trả về cùng T14A + nêu rõ khôi phục "từ capsule JSON bền vững (không transcript)" | PASS | `c40-fresh-process-dispatch.json`, `c40-fresh-process-observation.json`, `c40-messages-ZQVbWT43P6vmVPh78i2bSg.json` |
| Pilot upgrade proof (trong dự án pilot): cài bản 23 → upgrade 24 → rollback 23 → cài lại 24; file dự án byte-identical xuyên suốt | PASS — `project_files_unchanged_throughout: true` | `c40-pilot-upgrade-proof.json` (backup `/home/ubuntu/p2p-c40-evidence-backup/p2p-development/`) |
| Unsafe post-dispatch fail-closed (deterministic, không backend) — kế thừa C39 Proof 4 | PASS — `STOP_FAIL_CLOSED`/`REVERIFY_REQUIRED` | C39 evidence `c39-proof4-postdispatch.json` |
| **PILOT_PROJECT_ROLLBACK** (hợp đồng §20: pilot quay về đúng `PILOT_SOURCE_REVISION`, fingerprint nguồn khôi phục, không mutation ẩn) | **CHƯA CHỨNG MINH** — bằng chứng rollback chỉ ở cấp gói/fixture (c40-upgrade-proof.json, c40-pilot-upgrade-proof.json), không phải git rollback của pilot về pre-install revision; pilot hiện vẫn giữ trạng thái đã cài P2P | — (evidence hiện có không đủ; cần bước riêng, không thực hiện trong C40, không thay đổi evidence) |

Hợp đồng §30 định nghĩa lane **PARTIAL / INSTALLABLE_PACKAGE_VERIFIED_PILOT_INCOMPLETE** cho đúng trường hợp này (gói cài đặt đã kiểm chứng nhưng pilot chưa hoàn tất mọi hạng mục) — C40 dùng lane đó thay vì ép PASS.

Lưu ý semantics: quan sát độc lập (đọc `task.listMessages` trực tiếp qua API) được làm cho MỌI nhiệm vụ — không tin self-claim.

## 5. Regression & Framework Validator

- Framework validator: **75/75 PASS, 0 failed** (bộ check mở rộng hơn mốc 71 của C38; V21/V19 khớp vì báo cáo mới nhất C40 mang đủ trường + `package_verify_evidence` trong governance record — đã xác minh từ code rằng các check này chỉ xét báo cáo mới nhất và record, không che lỗi lịch sử).
- Regression differential (baseline `8b751f6`, qua worktree): hiện tại 44 lỗi vs baseline 46 lỗi → **NEW_UNEXPLAINED_FAILURES = 0**; 2 test đã cố định do V21 giờ hợp lệ (`test_cp48_framework_validator_runs_clean`, `test_lh35_c25_c26_framework_valid`).
- `test_fresh_clone_recovery` tạm hỏng do approved set C34 stale khi C38/C39/C40 thêm artifact — mở rộng approved set theo đúng tiền lệ C34/C35R/C36/C37/C39 (không thay đổi bất kỳ kiểm tra nào).
- Secret scan (`sk-` dài 40+, `AIzaS` 30+): **CLEAN, 0 match**.
- Failover boundary test suite: 104/104 PASS (không đổi hành vi so với C39 — `e826327`).

## 13. CANDIDATE POLICY (đường máy chính xác)

`ChangeSignals.detect(C40 diff, base e826327)`: runtime_changed = TRUE (`scripts/p2p_install_release.py` + evidence/harness là docs, không tính) → `candidate_policy(PASS, None, signals) = YES` (deterministic). Mint đúng **1 candidate UNPROMOTED**: `P2P-8.4.7-C-Codex-Edition-v24-c40-project-usable-release-pilot-candidate-v1.zip`, SHA `e7f62384…` (evidence `c40-candidate-policy.json`). CLASSIFICATION: `CASE_A_RUNTIME_CHANGE_PATH` (tương đương tiền lệ C36).

## 14. GOAL CLOSURE MACHINE

`goal_closure_verdict` (canonical, qua `load_governance` + `terminal_from_report`, tại thời điểm report vẫn khai báo PASS): **CONSISTENT** — 0 hard findings; 1 finding `CURRENT_DEVELOPMENT_SEMANTICS` ở mức `explained` (C31/BLOCKED_TERMINAL vs `roadmap.current = C40` — tiền lệ C35R/C38/C39: vị trí phát triển trực tiếp vs snapshot lịch sử, đúng semantics); ROADMAP_ITEM_EXISTS ok; PASS_WITH_DONE_ROADMAP ok; PASS_CURRENT_IS_DONE ok; CANDIDATE_REQUIRED_PRESENT ok; CANDIDATE_SHA_IMPLIES_ARTIFACT ok; CANDIDATE_VERIFY_EVIDENCE ok; cả 5 CLAIM_BOUNDARY PASS (ROUTER/CONTEXT_CONTROLLER/AUTH_ACTION/SECOND_EXECUTOR/BACKGROUND_AUTONOMY — không đưa vào).

Sau chuẩn hóa verdict về lane PARTIAL: máy closure (`p2p_goal_closure.py`) chỉ chấp nhận trạng thái canonical PASS/BLOCKED/FAIL cho candidate policy nên không thể chạy lại trực tiếp với verdict PARTIAL; chuẩn hóa lane bằng ghi đè evidence PARTIAL-lane (`c40-goal-closure.json` — 16 findings, 14 ok, 2 explained-not-ok) tái khẳng định toàn bộ kiểm tra tất định từ lần chạy máy cuối (`e77e745`, CONSISTENT) vẫn hợp lệ vì chuẩn hóa chỉ đổi verdict lane + wording scope, không đổi runtime/governance/evidence: CANDIDATE_REQUIRED_PRESENT ok; CANDIDATE_SHA_IMPLIES_ARTIFACT ok; CANDIDATE_VERIFY_EVIDENCE ok; CANDIDATE_UNPROMOTED_UNTIL_APPROVAL ok; cả 5 CLAIM_BOUNDARY PASS; kiểm tra PARTIAL-lane: `PARTIAL_LANE_GOVERNANCE_VERDICT` ok (governance verdict khớp report), `PARTIAL_LANE_SCOPE_WORDING` ok (phạm vi đúng bằng chứng); gap `PILOT_PROJECT_ROLLBACK` (contract §20) = explained-not-ok, là lý do duy nhất của lane PARTIAL.

Governance (sửa tối thiểu, idempotent): roadmap + mục C40 DONE, `roadmap.current = C40/DONE`, `candidate_records` + C40 UNPROMOTED (với `package_verify_evidence`); `current_development` KHÔNG đổi.

## 15. PROJECT-USE ASSESSMENT (kế thừa C39; pilot đã thực hiện)

- **Game Truyện**: PILOT_ONLY — pilot cô lập đã cài và chạy thật một nhiệm vụ; package install/upgrade/rollback được kiểm chứng trên fixture; PILOT_PROJECT_ROLLBACK (§20) chưa chứng minh — bước pilot chưa hoàn tất; KHÔNG merge vào nhánh chính dự án, KHÔNG cài lên production.
- **Gia Phả**: PILOT_ONLY — chưa cài; chưa đủ điều kiện pilot (không có repo/identifity dự án được Owner xác nhận trong C40).
- **Logistics**: DO_NOT_INSTALL_YET — dữ liệu tài chính; chưa cài, chưa pilot.

Thứ tự pilot giữ nguyên: Game Truyện → Gia Phả → Logistics.

## 16. TERMINAL VERDICTS & BOUNDS

`C40_TERMINAL = PARTIAL / INSTALLABLE_PACKAGE_VERIFIED_PILOT_INCOMPLETE` · `VALIDATOR = 75/75` · `REGRESSION = NEW_UNEXPLAINED_FAILURES=0` · `SECRET_SCAN = CLEAN` · `CANDIDATE = MINTED (1, UNPROMOTED)` · `PROMOTION = OWNER_GATE (Owner decision = PILOT_EXTEND; PARTIAL không cho phép promote)` · `CLOSURE = CONSISTENT trước chuẩn hóa; PARTIAL-lane closure normalization sau chuẩn hóa (16 findings, 14 ok, 2 explained: CURRENT_DEVELOPMENT_SEMANTICS + PILOT_PROJECT_ROLLBACK_GAP)` · `NO_MERGE_NO_RELEASE_NO_DEPLOY` · `PILOT_BRANCH_ONLY (không merge vào dự án Game Truyện)`.

## 17. KHUYẾN NGHỊ SAU C40 — OWNER PROMOTION GATE

C40 yêu cầu Owner quyết định về **promotion của candidate C40** (nâng gói cài đặt từ UNPROMOTED → PROMOTED_VERIFIED để dùng rộng hơn trên các dự án khác):

- `PROMOTE_NOW` — không khả dụng hợp lệ ở lane PARTIAL: promotion chỉ có nghĩa sau khi pilot hoàn tất đầy đủ (bao gồm PILOT_PROJECT_ROLLBACK).
- `PILOT_EXTEND` — hoàn tất pilot Game Truyện đang còn dở (PILOT_PROJECT_ROLLBACK) rồi pilot thêm Gia Phả trước (theo thứ tự pilot đã cam kết); candidate vẫn UNPROMOTED.
- `HOLD` — giữ nguyên UNPROMOTED, pilot dở dang ở trạng thái hiện tại.

**Kết quả Owner decision trong phiên chuẩn hóa này: PILOT_EXTEND.**

C40 không tự quyết định. Không merge, không promotion, không release, không deploy nào được thực hiện trong C40.

**Khuyến nghị kỹ thuật cho Owner (câu tiếp theo nếu PROMOTE_NOW):** `P2P-C41 — MULTI-PROJECT PILOT (Gia Phả) & PROMOTION EVIDENCE PACK`, tiếp nối chuỗi sau khi Owner xác nhận.
