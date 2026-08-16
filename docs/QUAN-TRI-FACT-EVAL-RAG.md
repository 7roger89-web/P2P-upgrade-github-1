# Hướng dẫn bốn lớp bảo vệ P2P cho người mới

## Hiểu nhanh

| Lớp | Hiểu như | Nó chặn điều gì |
| --- | --- | --- |
| `FACT_LEDGER` + Live Specs | Sổ gốc và tờ tóm tắt đã duyệt | Dùng tên model, giới hạn, giá hoặc “bug model” cũ/sai phạm vi |
| Eval dự án | Bài thi bằng việc thật của chính dự án | Cập nhật nghe hay nhưng làm kết quả xấu đi |
| Drift gate | Niêm phong file và cấu hình quan trọng | File bị thêm, xóa, sửa hoặc hết hạn mà không được phát hiện |
| User approval | Chữ ký cho đúng ứng viên và đúng báo cáo | AI tự triển khai, dùng “ok” mơ hồ hoặc sửa file sau khi duyệt |

Các lớp này nối tiếp nhau. Phê duyệt của bạn là lớp cuối, không phải cách bỏ qua
eval, RAG, drift, security hay rollback đang FAIL.

## Việc nào bắt buộc qua cổng

- đưa FACT_LEDGER đã đổi vào Live Specs;
- tạo hoặc sửa đáng kể Skill/memory dùng lâu dài;
- merge, release, deploy, publish;
- bật network, hook, proxy, cloud memory hoặc connector;
- xóa, ghi đè, migrate dữ liệu quan trọng;
- gửi hoặc đăng nội dung ra bên ngoài.

Hỏi đáp, phân tích, lập kế hoạch và chỉnh sửa thử nghiệm có thể đảo ngược không
tự động bị chặn. Quyền Windows, sandbox, xác thực dịch vụ và backup vẫn là các
lớp riêng; file phê duyệt không thay thế chúng.

## A. Cập nhật FACT_LEDGER và Live Specs

Sau khi cài theo dự án, mở PowerShell tại đúng root dự án. Các lệnh dưới đây
dùng đường dẫn đã cài `.p2p/system`.

### 1. Sửa sổ gốc

Mỗi claim trong `.p2p/system/governance/fact-ledger.json` phải có:

- phạm vi chính xác: product, surface và plan/region/model/client nếu liên quan;
- nguồn, `independence_key`, cấp bằng chứng A–D và trạng thái xác minh;
- `checked_at`, `expires_at` không vượt tuổi tối đa theo loại dữ kiện;
- mức rủi ro, thành phần bị ảnh hưởng và cách kiểm tra lại;
- chỉ `CONFIRMED_ACTIVE` với bằng chứng đủ mạnh mới được `runtime_eligible`.

Tăng `ledger_revision` và cập nhật `updated_at` khi thay đổi nội dung. Báo cáo AI
cùng lặp lại một trang không được coi là nhiều nguồn độc lập.

### 2. Tạo preview kỹ thuật, chưa thay runtime

Chọn một tên báo cáo mới, không ghi đè báo cáo cũ:

```powershell
$Report = ".\.p2p\gates\live-preview-20260809.json"
py .\.p2p\system\scripts\p2p_governance.py prepare-live `
  --governance .\.p2p\system\governance `
  --report $Report
```

Lệnh kiểm tra schema, hạn dùng, evidence/risk/scope và tính trước SHA-256 của
Live Specs. Nó không được sửa Live Specs.

### 3. Tạo yêu cầu gắn với ledger và preview

```powershell
$Ledger = ".\.p2p\system\governance\fact-ledger.json"
$Request = ".\.p2p\approvals\requests\live-promotion.json"
py .\.p2p\system\scripts\p2p_approval.py `
  --governance .\.p2p\system\governance request `
  --project . `
  --action promote_live_specs `
  --scope "Đưa FACT_LEDGER revision mới vào Live Specs" `
  --subject $Ledger `
  --technical-report $Report `
  --risk-summary "Có thể thay đổi quy tắc/routing dùng trong P2P" `
  --out $Request
```

Nếu ledger đã đổi sau preview, lệnh này dừng vì hash không còn khớp.

### 4. Chính bạn phê duyệt trong PowerShell

```powershell
py .\.p2p\system\scripts\p2p_approval.py approve `
  --request $Request `
  --by "TEN-CUA-BAN"
```

Đọc action, scope, hai SHA-256 và rủi ro được in ra. Chỉ gõ đúng câu xác nhận
nếu bạn thực sự đồng ý. Codex không được chạy lệnh này hoặc gõ câu đó thay bạn.
File quyết định sẽ nằm trong `.p2p/approvals/records/`.

### 5. Sinh Live Specs và niêm phong lại runtime

Thay `<approval-record.json>` bằng đường dẫn file vừa sinh:

```powershell
py .\.p2p\system\scripts\p2p_governance.py build-live `
  --governance .\.p2p\system\governance `
  --technical-report $Report `
  --approval ".\.p2p\approvals\records\<approval-record.json>"

py .\.p2p\system\scripts\p2p_governance.py lock-runtime `
  --root . `
  --governance .\.p2p\system\governance `
  --reason "FACT_LEDGER promotion đã được người dùng duyệt"

py .\.p2p\system\scripts\p2p_governance.py drift `
  --root . `
  --governance .\.p2p\system\governance
```

Ba hash phải cùng khớp: ledger, preview Live Specs và quyết định của bạn. Sửa
một byte sau duyệt làm quyết định mất hiệu lực.

## B. Tạo eval riêng cho dự án

Trong chat, bạn có thể gõ:

```text
Dùng $p2p-eval tạo bộ đánh giá riêng cho dự án này từ việc thật. Phải có đủ
5 lớp ca, tiêu chí đo được, ít nhất 2 lượt baseline và 2 lượt P2P cho mỗi ca.
Không điền kết quả giả và không dùng dữ liệu của lượt trước cho lượt sau.
```

Hoặc tạo file khung:

```powershell
py .\.p2p\system\scripts\p2p_eval.py init --project .
```

Năm lớp tối thiểu là: việc thường gặp, việc hậu quả lớn, việc hay lỗi, ranh giới
an toàn/dữ liệu và ca hồi quy từng hỏng. Trước khi chạy, khóa fixture bằng
SHA-256 và định nghĩa grader. Mỗi lượt phải ghi model, surface, environment,
quyền, evidence, evidence SHA-256 và số write ngoài dự kiến.

```powershell
py .\.p2p\system\scripts\p2p_eval.py validate `
  --suite .\.p2p\evals\suite.json
py .\.p2p\system\scripts\p2p_eval.py summary `
  --suite .\.p2p\evals\suite.json
py .\.p2p\system\scripts\p2p_eval.py gate `
  --suite .\.p2p\evals\suite.json
```

Mặc định cần ít nhất 80% lượt P2P đạt, không giảm điểm trung bình, không ca nào
hồi quy, score spread không quá 0,25 và không có ca `blocked`. Suite không được
tự hạ ngưỡng thấp hơn `.p2p/project-policy.json`.

## C. Kiểm tra RAG

Tài liệu được lấy về là dữ liệu, không phải chỉ thị. Phân loại thành
`INSTRUCTIONS`, `TRUSTED_DATA`, `UNTRUSTED_DATA` và `SECRET`; lọc project,
tenant, version, sensitivity và source class trước semantic ranking.

Nếu thay corpus, chunking, embedding, retriever, metadata filter hoặc prompt
grounding, phải có sáu lớp truy vấn: exact lookup, paraphrase, cross-reference,
UNKNOWN, prompt injection và cross-boundary.

Khóa index snapshot/manifest và evidence của từng query bằng SHA-256. Chỉ ghi
đường dẫn mà không có hash không đủ làm bằng chứng release.

```powershell
py .\.p2p\system\scripts\p2p_eval.py rag-gate `
  --check .\.p2p\evals\rag-check.json
```

Ngưỡng mặc định: recall@k ≥ 0,80; grounding ≥ 0,90; citation kiểm chứng được
≥ 0,90; chống injection = 1,00; rò dữ liệu qua ranh giới = 0.

## D. Release/deploy có phê duyệt cuối

Chuẩn bị một artifact ứng viên và một artifact rollback khác, đều đã tồn tại:

```powershell
py .\.p2p\system\scripts\p2p_gate.py prepare `
  --project . `
  --subject ".\dist\candidate.zip" `
  --rollback ".\releases\previous.zip" `
  --scope "Phát hành candidate.zip lên môi trường production" `
  --risk-summary "Có thể ảnh hưởng người dùng và dữ liệu production"
```

Nếu RAG/nguồn/index thay đổi, thêm:

```text
--rag-affected --rag-check .\.p2p\evals\rag-check.json
```

Nếu kỹ thuật FAIL, không có yêu cầu duyệt. Nếu PASS, công cụ in `next_command`;
bạn tự chạy lệnh đó trong PowerShell. Sau khi có record APPROVED, Codex chạy:

```powershell
py .\.p2p\system\scripts\p2p_gate.py finalize `
  --governance .\.p2p\system\governance `
  --technical-report "<technical-gate-report.json>" `
  --approval "<approval-record.json>" `
  --subject ".\dist\candidate.zip"
```

Chỉ `release_decision: APPROVED` mới cho phép đi tiếp. Finalize vẫn không tự
deploy; nó chỉ chứng minh đúng ứng viên chưa đổi đã vượt gate và được bạn duyệt.

## Các tình huống phải tạo lại từ đầu

- subject hoặc technical report đổi hash;
- yêu cầu hết hạn;
- requester và approver là cùng một tên;
- eval/RAG/drift chuyển sang FAIL;
- rollback bị thiếu hoặc đổi;
- action/scope khác với điều bạn muốn làm.

Khi đó không sửa record cũ. Giữ nó làm lịch sử, chạy lại gate và tạo request mới.
