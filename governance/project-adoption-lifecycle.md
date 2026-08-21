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

# Hợp đồng Project Pin (§5)

Mọi dự án sử dụng P2P phải chứa một tệp `.p2p/project-pin.json` với cấu trúc sau:

```json
{
  "project_fingerprint": "SHA-256 của gốc dự án",
  "p2p_official_version": "8.4.7-C-codex.46",
  "p2p_artifact_sha256": "2901adca...",
  "install_timestamp_utc": "ISO-8601",
  "installation_mode": "PORTABLE_VIRTUAL_ENV",
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
  "compatibility_state": "VERIFIED_COMPATIBLE"
}
```

**Lưu ý:** Hợp đồng này là trung lập với provider (Provider-neutral). Manus chỉ là một trong các ExecutionTarget có thể chọn.
