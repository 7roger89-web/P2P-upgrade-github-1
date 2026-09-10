# ziwei-chart — Independent Research Dossier

UPSTREAM: `ziweiknows/ziwei-chart`
PINNED_SHA: `b172413d85addbe32facd9e20b9179db619f3afb`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo là sản phẩm Ziwei Chart: deterministic chart generation bằng `iztro`, hỗ trợ出生地/真太阳时, annual trends,合盘,人生K线 và AI interpretation tùy chọn. Repo hiện dùng GPLv3+.

Dossier này độc lập với `ziwei-wuandyA` dù hai repo có lịch sử/tính năng gần nhau.

## Candidate value

- Boundary được README mô tả rõ giữa命盘事实 và AI解读.
- Có true-solar-time/location normalization đáng audit.
- Có `knowledge-db/` và knowledge layer riêng.
- Product architecture gần với web thương mại tương lai, nhưng license phải được tôn trọng.

## Local candidate rules

`ZC-001` — Chart facts phải reproducible khi AI bị tắt.

`ZC-002` — 真太阳时 correction phải lưu raw birth time, coordinates/match, correction choice và normalized time.

`ZC-003` — Trend/K-line/compatibility outputs phải phân biệt `DETERMINISTIC_DERIVATION` với `HEURISTIC`.

`ZC-004` — AI explanation không được thay đổi chart facts.

## What to audit

1. Date/location/true-solar normalization.
2. Boundary với `iztro`.
3. `app/src/knowledge-db/` và `knowledge/`.
4. Annual trend,合盘 và人生K线 algorithms.
5. AI prompt + evidence passed to model.

## Validation

Chạy cùng input với AI off/on; phần chart fact phải bất biến. Mọi khác biệt chỉ được ở explanation layer.

## Commercial note

Repo công bố GPLv3+. Không copy code vào sản phẩm proprietary mà phớt lờ nghĩa vụ license. Có thể nghiên cứu kiến trúc/ý tưởng và tự triển khai độc lập nếu phù hợp pháp lý.

## Next bounded task

Audit deterministic boundary + true solar time pipeline trước; không dùng output của repo khác để xác nhận repo này.
