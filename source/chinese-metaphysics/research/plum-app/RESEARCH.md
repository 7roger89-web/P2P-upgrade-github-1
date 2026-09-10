# plum-app — Independent Research Dossier

UPSTREAM: `soom-lupulus/plum-app`
PINNED_SHA: `5965bdc8e9ca69a3cc7e96be6f1cc585d5032814`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo tự mô tả là mobile PWA để lập/quản lý case, gồm 梅花排盘, 爻辞, 策轨数, 六爻纳甲 và một số 神煞. Vai trò nghiên cứu hiện tại là **case/product architecture**, không phải authority để khẳng định các hệ trên có thể tự động trộn vào một phép luận duy nhất.

## Candidate value

- Cách lưu một lần khởi quẻ và dữ liệu dẫn xuất.
- Cách hiển thị nhiều lớp dữ liệu cho người nghiên cứu.
- Cách ghi case/outcome để hậu kiểm.
- UX mobile cho người dùng chuyên môn.

## Local rules

`PA-001` — Mọi module 梅花/策轨/纳甲/神煞 phải được nhận diện riêng khi audit.

`PA-002` — Claim “các mô hình không xung đột” của README chỉ là `UPSTREAM_CLAIM`, chưa phải rule được xác minh.

`PA-003` — Case record chỉ là evidence tốt khi biết input, thời điểm prediction, outcome và có chống hindsight.

## What to audit

1. `apps/backend`: schema/model cho quẻ và case.
2. `apps/frontend`: dữ liệu nào được tính, dữ liệu nào do người dùng nhập.
3. Quan hệ giữa 梅花, 策轨, 纳甲 trong code: song song hay thực sự hợp nhất.
4. Cách lưu outcome và lịch sử chỉnh sửa.

## Validation

```text
INPUT -> STORED CASE -> COMPUTED FIELDS -> INTERPRETATION FIELDS -> OUTCOME
```

Không lấy case đã biết kết quả để chứng minh predictive validity.

## Commercial note

README ghi MIT cho repo. Trước tái sử dụng thương mại vẫn phải audit LICENSE thật, dependency, dữ liệu văn bản và nội dung 爻辞/giải thích đi kèm.

## Next bounded task

Inventory data model + case lifecycle. Không nghiên cứu phương pháp repo khác trong dossier này.
