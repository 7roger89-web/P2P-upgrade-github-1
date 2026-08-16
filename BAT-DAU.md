# Bắt đầu sử dụng P2P cho Codex

Full release revision: `8.4.7-C-codex.9`.

Đây là bản chuyển đổi P2P 8.4.6-C dành cho Codex, full release `8.4.7-C-codex.6`. Gói giữ nguyên toàn bộ 152 file
gốc để kiểm tra, đồng thời có 23 Skill Codex, tám hồ sơ canonical và specialist UI/UX tùy chọn
bắt buộc cho những việc có hậu quả lâu dài.

## Quy trình bình thường cho người mới

1. Cài hoặc gắn P2P vào dự án.
2. Mở đúng thư mục dự án trong Codex.
3. Nói bằng ngôn ngữ tự nhiên, ví dụ: `Hoàn thiện dự án này giúp tôi và chỉ dừng khi thực sự xong.`

P2P tự chọn đường đi trực tiếp, lập kế hoạch trước hoặc tạo Goal; tự tạo các trạng thái
cần thiết, chọn nhóm agent nhỏ phù hợp, kiểm tra kết quả và dừng ở `PASS`, `BLOCKED` hoặc
`REJECT`. Bạn không cần tự gọi agent, eval, ledger hay gate.

## Cách dễ nhất: cài vào một dự án

1. Giải nén gói này ra một thư mục riêng.
2. Mở PowerShell trong thư mục vừa giải nén.
3. Chạy:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Scope Project -ProjectPath "<PROJECT_PATH>"
```

4. Mở thư mục `<PROJECT_PATH>` bằng Codex và đánh dấu dự án là đáng tin cậy
   nếu Codex hỏi.
5. Mở một chat mới trong dự án. Nếu bạn mới chỉ có ý tưởng, gõ:

```text
Dùng $p2p-idea cho ý tưởng này: [viết ý tưởng bằng lời bình thường].
Tôi là người mới. Nếu thiếu dữ kiện, chỉ hỏi tối đa 3 câu quan trọng nhất,
sau đó đề xuất lựa chọn phù hợp nhất, nêu mức tin cậy và bước thử đầu tiên.
```

Ví dụ:

```text
Dùng $p2p-idea cho ý tưởng: tôi muốn tìm khách có nhu cầu vận chuyển hàng từ
Trung Quốc về Việt Nam. Tôi là người mới và chưa biết bắt đầu từ đâu.
```

Skill sẽ không đoán rằng một phương án chắc chắn tốt nhất. Nó phân biệt dữ kiện,
giả định và điều chưa biết; khi cần dữ liệu hiện hành, nó phải kiểm chứng nguồn.
Sau khi đã chọn hướng, gõ:

```text
Dùng $p2p-scope để biến lựa chọn vừa chốt thành kế hoạch triển khai từng bước
cho dự án đang mở. Hãy giải thích như cho người mới.
```

## Kiểm tra sau cài đặt

```powershell
powershell -ExecutionPolicy Bypass -File .\doctor.ps1 -Root "<PROJECT_PATH>"
```

Kết quả cần có:

- 23 Skill, gồm `p2p-uiux`;
- FACT_LEDGER, Live Specs và khóa đồng bộ;
- 8 agent TOML;
- `agents.enabled = true`;
- giới hạn tám thread;
- policy, runtime lock và các helper bảo vệ không bị thiếu hoặc sửa lệch.

Doctor có thể báo `WARN release-readiness`. Đây không phải lỗi cài đặt. Nó có
nghĩa là dự án này chưa có bài thi thật nên chưa được release/deploy; hỏi đáp,
lập kế hoạch, viết code và dùng các Skill P2P thông thường vẫn hoạt động.

Để kiểm tra P2P có thật sự giúp dự án của bạn, gõ:

```text
Dùng $p2p-eval tạo bộ đánh giá riêng từ 5 tác vụ thật của dự án này.
```

Mỗi ca phải có ít nhất hai lượt baseline và hai lượt P2P trên cùng fixture đã
khóa. Không điền kết quả giả chỉ để cổng chuyển sang màu xanh.

Để bàn giao đúng loại phiên, gõ `$p2p-capsule profile task`, `brainstorm`,
`research` hoặc `incident`. Xem giải thích tại
`docs/QUAN-TRI-FACT-EVAL-RAG.md`. Bản phân tích lỗ hổng xuyên suốt hệ thống nằm tại
`docs/PHAN-TICH-CHIEU-NGANG-DOC.md`.

Nếu `$p2p-idea` chưa xuất hiện ngay trong danh sách Skill, hãy mở lại trang
Skills hoặc bắt đầu một chat mới trong đúng dự án đã cài.

## `$` và `@` khác nhau thế nào

- Dùng `$p2p-idea`, `$p2p-eval`, `$p2p-approval` để gọi một **Skill/workflow**.
- Dùng `@p2p_iris`, `@p2p_tecton`... chỉ khi muốn gọi trực tiếp một **agent** và
  giao diện Codex hỗ trợ danh sách agent.
- Muốn chạy cả tám agent thật, dùng `$p2p-quorum full`; không cần gõ tám dấu `@`.

## Khi nào Codex bắt buộc phải dừng chờ bạn

Các việc sau không được thực hiện chỉ vì AI đã đề xuất: đưa FACT_LEDGER mới vào
Live Specs; tạo/sửa Skill hoặc memory dùng lâu dài; merge, release, deploy hoặc
publish; bật network/hook/proxy/cloud/connectors; xóa/sửa dữ liệu khó khôi phục;
gửi nội dung ra bên ngoài.

Thứ tự bắt buộc là:

1. khóa đúng file/thư mục ứng viên bằng SHA-256;
2. eval dự án PASS;
3. nếu có RAG, retrieval gate PASS;
4. drift gate PASS và có bản rollback;
5. Codex tạo yêu cầu phê duyệt gắn với đúng hash;
6. chính bạn mở PowerShell và xác nhận tương tác;
7. Codex kiểm tra lại hash rồi mới được thực hiện.

Bạn có thể gõ trong chat:

```text
Dùng $p2p-approval để chuẩn bị cổng bảo vệ cho thay đổi này. Chỉ tạo yêu cầu
phê duyệt sau khi eval, drift và rollback đều PASS; không được tự phê duyệt.
```

Đọc hướng dẫn từng lệnh tại `docs/QUAN-TRI-FACT-EVAL-RAG.md`. Phê duyệt này là
lớp kiểm soát quy trình và nhật ký; nó không thay thế quyền Windows, sandbox,
mật khẩu, xác thực dịch vụ hoặc backup.

## Dùng tám agent thật

```text
Dùng $p2p-quorum full để phân tích [nhiệm vụ]. Phải chạy đủ 8 subagent thật và cho tôi xem execution ledger.
```

Trong Codex CLI, dùng `/agent` để xem các thread. Nếu giao diện không hiển thị
tám thread riêng thì không được coi là full QUORUM thật.

## Cài cho mọi dự án của tài khoản Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Scope User
```

Cài theo dự án an toàn và dễ kiểm soát hơn cho người mới. Chỉ dùng `User` khi
bạn muốn P2P xuất hiện trong mọi dự án.
