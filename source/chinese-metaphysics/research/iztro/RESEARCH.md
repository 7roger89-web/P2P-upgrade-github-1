# iztro — Independent Research Dossier

UPSTREAM: `SylarLong/iztro`
PINNED_SHA: `2c7ef9be669df7b19d1799f4dce335fed3794f78`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo là thư viện lập 紫微斗数 và truy vấn dữ liệu lá số. Giá trị chính trong dossier này là **deterministic calculation/data layer**, không phải authority luận đoán.

## Candidate value

- Lập 十二宫 và星曜 placements bằng code.
- Dữ liệu 四化 và运限 có thể truy vấn.
- Có API/logic phục vụ quan hệ cung và飞化.
- Phù hợp để freeze chart trước khi AI reasoning.

## Local candidate rules

`IZ-001` — Output engine là `CHART_FACT` theo convention của iztro, không tự biến thành interpretation.

`IZ-002` — Mọi cấu hình/phái ảnh hưởng 安星 hoặc 四化 phải được freeze và ghi rõ.

`IZ-003` — 宫位飞化 query chỉ chứng minh đường dữ liệu engine trả về; ý nghĩa cát/hung cần source riêng.

`IZ-004` — Version/pinned SHA phải đi cùng mọi test case để tránh drift.

## What to audit

1. Cấu hình school/defaults của engine.
2. Tables/constants cho stars và 四化.
3. Horoscope layers: 大限、流年、流月、流日、流时.
4. API cho palace-to-palace transformations và self-transformation nếu có.
5. Unit tests cho edge cases ngày giờ, leap month, timezone/convention.

## Validation

```text
BIRTH INPUT -> NORMALIZATION -> CONFIG -> CHART FACTS
-> FOUR-TRANSFORMATION FACTS -> TIME-LAYER FACTS
```

So sánh deterministic outputs với các reference chart độc lập trước khi dùng làm nền luận.

## Next bounded task

Audit chart construction + configuration surface. Chưa nghiên cứu lời luận Tử Vi trong dossier này.
