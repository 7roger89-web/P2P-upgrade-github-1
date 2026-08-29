# Vòng đời Adoption Dự án P2P (§4)

Tài liệu này định nghĩa các trạng thái rời rạc và hữu hạn của một dự án trong hệ sinh thái P2P.

| Trạng thái | Định nghĩa | Ranh giới |
|:---|:---|:---|
| **OFFICIAL_P2P_BASELINE** | Có một Baseline P2P chính thức được phê duyệt. | Chỉ tồn tại trong repo P2P. |
| **PROJECT_COMPATIBILITY_DISCOVERY** | Dự án được quét để xác định khả năng tương thích. | Không thay đổi dự án. |
| **INSTALL_PLAN** | Một kế hoạch cài đặt cụ thể được tạo ra. | Chỉ là dữ liệu kế hoạch. |
| **SAFE_INSTALL** | Các tệp P2P được sao chép vào dự án. | Thay đổi tệp nhưng chưa kích hoạt. |
| **PROJECT_P2P_PIN** | Dự án được liên kết (pin) với một phiên bản P2P cụ thể. | **Durable binding** được tạo ra. |
| **DOCTOR** | Kiểm tra sức khỏe sau cài đặt. | Xác nhận tính sẵn sàng kỹ thuật. |
| **EXECUTION_TARGET_DISCOVERY** | Tìm kiếm các host thực thi khả dụng (Manus, v.v.). | Kết nối mạng/API. |
| **LIVE_HOST_CERTIFICATION** | Xác minh host thực thi có thể chạy P2P. | Chứng chỉ host được cấp. |
| **TASK_DISPATCH** | Một nhiệm vụ thực tế được gửi đi. | Thực thi tác vụ. |
| **RECEIPT** | Kết quả nhiệm vụ được nhận về. | Dữ liệu kết quả. |
| **VERIFY** | Kết quả được xác minh độc lập. | Bằng chứng nghiệm thu. |
| **CHECKPOINT** | Trạng thái dự án được lưu lại bền vững. | Cập nhật ledger dự án. |

## Nhánh Projection-only và Arena Agent Mode

Adoption projection-only là một nhánh riêng, không thay thế đường cài đặt
`PACKAGED_PROJECT`/`p2p-project-pin/1` ở trên:

```text
PROJECTION_PLAN
  -> CONTROLLED_MATERIALIZATION
  -> PROJECTION_ONLY_PIN
  -> PROJECTION_VERIFY
```

Luồng canonical cho dự án áp dụng Arena là:

```text
P2P CANONICAL SOURCE
  -> SELECTIVE PROJECT PROJECTION
  -> APPLICABLE GITHUB PROJECT
```

Nguồn đầy đủ là `docs/ARENA_AGENT_MODE_PROTOCOL.md`. Dự án chỉ nhận phần
Arena ngắn, vận hành được và đã được khai báo trong plan hiện có; plan, hash
nội dung, ownership và `p2p-project-projection-binding/1` pin là bằng chứng
projection. Không duy trì bản sao thủ công khác nghĩa. Các target phải là
project-scoped `.agents`, `.claude`, `.gemini`, `.cursor` hoặc `.github`; path
user/global, registry thứ hai, router thứ hai và generic protocol materializer
đều nằm ngoài hợp đồng này.

Với Codex, target family hiện có là
`.agents/skills/<capability_id>/SKILL.md` cùng metadata do plan khai báo.
Việc mapping/projection không tự chứng nhận host runtime, không cài runtime
P2P, và không tạo quyền GitHub. Nếu dự án chưa có một selected plan phù hợp,
không được tuyên bố Arena protocol đã được projected.

# Hợp đồng Project Pin — packaged runtime (§5)

Đường cài đặt `PACKAGED_PROJECT` phải chứa một tệp `.p2p/project-pin.json`
theo hợp đồng `p2p-project-pin/1` với cấu trúc sau. Nhánh projection-only dùng
`p2p-project-pin/2` và các binding đã nêu ở trên; không được lẫn hai lifecycle.

```json
{
  "project_fingerprint": "SHA-256 của gốc dự án",
  "schema": "p2p-project-pin/1",
  "p2p_official_baseline_version": "<official baseline from candidate metadata>",
  "p2p_official_baseline_sha256": "<64-hex official baseline SHA-256>",
  "p2p_candidate_version": "<installed unpromoted candidate>",
  "p2p_candidate_artifact_sha256": "<64-hex exact archive SHA-256>",
  "install_timestamp_utc": "ISO-8601",
  "installation_mode": "PACKAGED_PROJECT",
  "permission_envelope": {
    "file_read": "PROJECT_ROOT",
    "file_write": "PROJECT_LOCAL_P2P_STATE",
    "network": "EXECUTION_TARGET_ONLY"
  },
  "execution_target_requirements": {
    "min_roles": 8,
    "certified_only": true
  },
  "rollback_source": ".p2p/backups/pre-install-snapshot.tar.gz",
  "doctor_result": "HEALTHY",
  "verification_status": "VERIFIED",
  "candidate_vs_official": "UNPROMOTED_SUCCESSOR_CANDIDATE",
  "source_binding_status": "VERIFIED",
  "source_commit": "<40-hex source commit>",
  "source_tree": "<40-hex source tree>",
  "compatibility_state": "VERIFIED_COMPATIBLE"
}
```

**Lưu ý:** Hợp đồng này là trung lập với provider (Provider-neutral). Manus chỉ là một trong các ExecutionTarget có thể chọn.
