# P2P C38 — Báo cáo Terminal Stage B (First Live Role Proof)

**Tác giả:** P2P Agent (Manus AI) — **Ngày:** 2026-08-18 — **Ngôn ngữ:** Tiếng Việt

## 1. Verdict tổng thể

| Hạng mục | Kết quả |
|---|---|
| **Stage A (auth preflight)** | HOÀN TẤT — Manus: **AUTH_VALID** (key Owner qua API Integration settings); Codex: AUTH_INVALID (HTTP 401, bền vững từ C27/C31); Hermes: AUTH_ABSENT |
| **Stage B (first live role proof)** | **HOÀN TẤT — Independent verifier: VERIFIED, failure_class: NONE** |
| **Stage C (backend thứ hai)** | **BỊ CHẶN — OWNER_AUTH_REQUIRED** (Codex 401 / Hermes absent) → đường **PARTIAL** |
| **State Git** | Branch `p2p-c38-live-role-certification` @ `85ec9b7` (pushed, draft PR [#15](https://github.com/7roger89-web/P2P-upgrade-github-1/pull/15)) |
| **Mutations ngoài evidence dir** | Không có (NON_MUTATING_TASK; NO_MUTATION_OBSERVED) |
| **Secret trong git/repo** | Không có (secret-scan sạch; key lưu ngoài repo, mode 600) |

## 2. Proof live đã thực hiện

Proof đầu tiên chạy trên adapter `manus-rest-api-v2` với role canonical **p2p_iris** (spec hash `1c0ea4d2...`) qua `manus_adapter.py`, ràng buộc bởi `RoleExecutionContract` đầy đủ:

| Trường hợp nghiệm (contract → quan sát) | Giá trị |
|---|---|
| Role / goal / task | p2p_iris / C38 / c38-stage-b-first-live-role-proof |
| Permission profile | (NON_MUTATING_TASK,) — không widens |
| Approved scope | (API_TRANSPORT, SYNTHETIC_TEXT_EXECUTION, NON_MUTATING_TASK) |
| Explicit target / attestation | manus-api-v2 / ATTESTED_MATCH (task id quan sát độc lập) |
| Project binding (tiền lệ C35) | P2P-upgrade-github-1 |
| Acceptance criteria | answer_is_capital_of_vietnam → **"Hà Nội"** = TRUE |
| Execution | SUCCEEDED, stopped, 11s, 0 credit, auth_state_after VALID |

Chạy hai lần để kiểm chứng độ lặp lại: lần 1 (task `E6Y2TNZnGLtyi5gLftvM35`) trả lời "Hanoi"; lần 2 (task `NWnoWkrrJeQiYWZMv8jCS5`, được dùng làm bằng chứng chính) trả lời "Hà Nội". Câu trả lời được **đọc độc lập qua `task.listMessages`** — không tin vào self-claim của adapter (trình tự C35 fail-closed).

## 3. Independent verification

Verifier độc lập `p2p_capabilities.role_verifier` (thẩm quyền INDEPENDENT, schema `p2p-role-execution-verifier/1`) được chạy trên một harness riêng biệt, với `backend_result` tái dựng từ kết quả adapter cộng bằng chứng messages quan sát:

```
{
  "schema": "p2p-role-execution-verifier/1",
  "verdict": "VERIFIED",
  "receipt_role_id": "p2p_iris",
  "receipt_task_id": "c38-stage-b-first-live-role-proof",
  "receipt_goal_id": "C38",
  "reasons": [],
  "failure_class": "NONE",
  "verifier_authority": "INDEPENDENT"
}
```

Tất cả 11 nhóm kiểm tra fail-closed đều qua: role/role-spec hash, goal/task/project/environment/context/request/target bindings, target attestation, backend result (fingerprint khớp, VERIFIED), mutation state (NO_MUTATION_OBSERVED), không widens permission, fingerprint profile khớp, evidence đủ 3 yêu cầu (role_binding, target_attestation, terminal_result), capability scope không cần chứng chỉ (non-mutating synthetic).

## 4. Evidence (đã commit, không chứa secret)

- `docs/p2p-development/research/c38/evidence/c38-stage-b-role-contract.json` — contract đã ký (C37 precedent)
- `docs/p2p-development/research/c38/evidence/c38-stage-b-live-receipt.json` — BackendExecutionResult
- `docs/p2p-development/research/c38/evidence/c38-stage-b-messages-observed.json` — bằng chứng messages quan sát độc lập
- `docs/p2p-development/research/c38/evidence/c38-stage-b-role-receipt.json` — receipt hoàn chỉnh, verifier_result = VERIFIED
- Harness: `docs/p2p-development/research/c38/harness/c38_stage_b_role_proof.py`, `c38_stage_b_independent_verify.py`

## 5. Findings hard trong Stage B

Số lượng: **0 hard finding** đối với bản thân proof. Hai điều chỉnh kiến trúc được ghi nhận minh bạch (không phải lỗi chứng minh): (a) verifier yêu cầu `required_capabilities` là tập con của CERTIFICATION_SCOPES — contract phi-mutation đặt `required_capabilities=()` và dựa vào fail-closed theo scope thay vì capability claim; (b) project binding dùng tiền lệ C35 `P2P-upgrade-github-1` (trống rỗng gây REJECTED do `_check_binding` fail-closed trên chuỗi rỗng).

## 6. Rủi ro còn lại

Giai đoạn sau proof (Stage C/D) bị chặn bởi thiếu backend thứ hai (Codex AUTH_INVALID, Hermes AUTH_ABSENT) — đúng thiết kế: C38 yêu cầu 2 backend cho full certification, nếu không thể thì ứng viên là **PARTIAL** với scope giới hạn. Key Owner hiện lưu ngoài repo (mode 600); sau khi hoàn tất nên khuyến nghị Owner thu hồi key để giữ nguyên tắc "không credential tồn dư".

## 7. Bước tiếp theo (chờ Owner quyết định)

1. **Owner review** PR #15 (draft) — Stage B sẵn sàng để review.
2. **Nếu Owner cung cấp xác thực Codex/Hermes**: thực hiện Stage C (second backend proof), regression, capsule proof, candidate PARTIAL-to-FULL.
3. **Nếu Owner dừng ở đây**: hoàn tất Stage D capsule proof với backend duy nhất hiện có, đóng C38 với ứng viên PARTIAL theo luật (không tạo C39).
