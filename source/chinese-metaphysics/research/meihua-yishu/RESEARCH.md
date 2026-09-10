# meihua-yishu — Independent Research Dossier

UPSTREAM: `muyen/meihua-yishu`
PINNED_SHA: `8a9a5e0f482dd225bfe4a1c52c2ae5546228607a`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo cung cấp một hệ Mai Hoa khá rộng: nhiều cách 起卦, 体用, 五行生克, 卦德, 主/互/变/错/综, 卦气, 十应/外应, 应期, 18 loại chuyên đoán và case studies. Repo cũng có `meihua_calc.py` cho phần tính toán.

## Điểm đặc biệt phải giữ riêng

Repo tự công bố một prediction-validation report và nói việc tính 吉/凶 trực tiếp từ 五行生克 chỉ ở mức gần coin-flip trong thử nghiệm của chính họ. Đây là evidence nội bộ đáng kiểm, không phải kết luận khoa học chung.

Repo còn có **second-level time casting** và tự ghi đây là modern extension; phải tách khỏi cách truyền thống dùng 时辰.

## Local candidate rules

`MY-001` — Traditional casting convention và modern second-level extension phải là hai mode khác nhau.

`MY-002` — 体用、生克、卦德、互变错综、外应、应期 phải audit như các lớp riêng; không coi toàn bộ là một rule.

`MY-003` — Report prediction-validation phải kiểm dataset, leakage, scoring và baseline trước khi dùng.

`MY-004` — Không biến 卦名 hay 五行关系 thành điểm số xác suất nếu repo không có calibration hợp lệ.

## What to audit

1. `scripts/meihua_calc.py`.
2. `references/64gua.md`, `yaoci.md`, `zhouyi-zhuan.md`.
3. `hexagram-relationships.md`, `ying-guides.md`, `yingqi-calc.md`.
4. `18-divinations.md` và case studies.
5. `experiments/prediction-validation/FINAL-REPORT.md`.

## Validation

Tách ba claim: `CASTING_CORRECT`, `METHOD_SOURCE_CORRECT`, `PREDICTION_SUPPORTED`. Không cho claim thứ nhất kéo theo hai claim sau.

## Commercial note

Repo dùng `CC BY-NC-SA 4.0`; không tái sử dụng material này trong sản phẩm thương mại nếu chưa có quyền phù hợp.

## Next bounded task

Audit prediction-validation report và casting conventions trước khi đụng phần interpretation.
