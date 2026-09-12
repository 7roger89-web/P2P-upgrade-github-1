# plum-cg — Independent Research Dossier

UPSTREAM: `soom-lupulus/plum-cg`
PINNED_SHA: `509fc43001a503d17a37db07bc56e069b1ff1c4f`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo tự mô tả là công cụ tính toán cho 梅花策轨法 từ 主卦 + 动爻, gồm 策数、轨数、元策、元轨 và mapping sang 卦/五行. Repo cũng công khai việc tồn tại dị biệt ở quy tắc số 5 phối 艮/坤 và cho phép chọn convention.

## Candidate value

- Engine deterministic nhỏ, dễ kiểm thử độc lập.
- Có tutorial, source TypeScript và unit tests để đối chiếu ba lớp: mô tả → code → output.
- Dị biệt convention được biểu diễn rõ thay vì giấu đi.

## Local candidate rules

`PCG-001` — Freeze input 主卦 + 动爻 trước tính toán.

`PCG-002` — Freeze convention của mapping số 5 trước khi sinh output.

`PCG-003` — Unit test chỉ chứng minh code nhất quán với expected output, chưa chứng minh thuật toán đúng nguồn cổ.

`PCG-004` — Không đưa output 策轨 sang hệ Mai Hoa khác nếu dossier này chưa chứng minh bridge rule.

## What to audit

1. `README_Tutorial.md`: attribution và công thức.
2. `src/`: triển khai từng công thức.
3. `test/`: coverage, edge case, expected values.
4. Tìm primary/authorized source của 策轨法 và các dị bản.

## Validation

```text
RAW INPUT -> CONVENTION -> FORMULA -> INTERMEDIATE VALUES -> FINAL VALUES
```

Mỗi sample phải tái tính được bằng tay hoặc implementation độc lập.

## Next bounded task

Lập bảng `formula -> code location -> test -> source citation`; chưa luận đoán, chỉ xác minh engine.
