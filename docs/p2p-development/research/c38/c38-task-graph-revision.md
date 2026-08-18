# C38 Task-Graph Revision — Stage D trước Stage C

**Ngày:** 2026-08-18 · **Ngành:** `p2p-c38-live-role-certification` · **Git start HEAD:** `2a371777438c88867138203e0b0bcc04283d8bed`

## Task graph đã sửa đổi

| Node | Trạng thái | Ghi chú |
|---|---|---|
| A. AUTH PREFLIGHT | DONE | Manus AUTH_VALID (key Owner); Codex AUTH_INVALID (HTTP 401 bền vững từ C27/C31); Hermes AUTH_ABSENT |
| B. FIRST LIVE ROLE PROOF / MANUS | **VERIFIED** | p2p_iris × manus-rest-api-v2; independent verifier verdict VERIFIED, failure_class NONE |
| **D. FRESH-SESSION / CONTINUATION-CAPSULE PROOF** | **NEXT** | Không phụ thuộc logic vào Backend B |
| C. SECOND BACKEND PROOF | OWNER_AUTH_REQUIRED sau Stage D | Codex/Hermes cần xác thực của Owner |

## Lý do sửa đổi

```
INDEPENDENT_SAFE_WORK_REMAINS_WHILE_BACKEND_B_AUTH_IS_BLOCKED
```

Stage D (fresh-session / capsule recovery) **không** phụ thuộc vào Backend B về mặt logic: nó chỉ cần một backend duy nhất đã xác thực (Manus) để tạo execution mới nhận capsule từ durable state. Backend A đã VERIFIED, trong khi Backend B vẫn OWNER_AUTH_REQUIRED — do đó thứ tự thực thi hợp lý là thực hiện D trước C. Đây **không phải** mở rộng phạm vi (không scope expansion): tổng số node proof không thay đổi, chỉ thứ tự tối ưu khi có nút bị chặn auth.

## Tính đúng đắn

Không có node nào bị bỏ; không có node mới nào được thêm; checkpoint Stage B (commit `85ec9b7`) và Stage-B terminal report (`2a37177`) vẫn là nền tảng xác thực.
