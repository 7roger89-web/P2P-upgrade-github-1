# liuyao-divination — Independent Research Dossier

UPSTREAM: `Johnson-Jia/liuyao-divination`
PINNED_SHA: `1a5a78b513c0e7b46dfb29f74043bcf978c32a3e`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo tách rõ **排盘 mechanical layer** và **解读 reasoning layer**. Candidate workflow hiện thấy trong repo là: 排盘 → 取用神 → 旺衰 → 世爻 → 动静/空破 → 化变/合墓 → 综合 → 应期.

## Candidate value

- Kiến trúc separation rất phù hợp để chống AI tự sửa bàn.
- Có engine và reference riêng cho các rule 六爻.
- Có case report để kiểm reasoning chain.

## Local candidate rules

`LD-001` — Board phải freeze trước interpretation.

`LD-002` — 取用神 là quyết định reasoning, phải ghi lý do và rule nguồn.

`LD-003` — 暗动、日破、空亡、墓库、进退神... là các rule độc lập; không gom thành một nhãn “xấu/tốt”.

`LD-004` — 应期 phải truy được về điều kiện kích hoạt cụ thể, không đoán ngày tùy hứng.

## What to audit

1. Engine `src/paipan.py` và constants.
2. `references/01-装卦排盘.md` đến các reference về 旺衰/空破/化变/四神/反伏.
3. Các ví dụ có reasoning chain.
4. Source attribution của từng rule.

## Validation

```text
RAW CAST -> BOARD FREEZE -> 用神 -> RULE APPLICATIONS
-> CLAIM -> 应期 -> BLIND OUTCOME
```

Construction error và interpretation error phải chấm riêng.

## Next bounded task

Chạy audit độc lập phần 排盘 trước; chỉ khi board layer đủ ổn mới audit reasoning.
