# yinyo-liuyao — Independent Research Dossier

UPSTREAM: `xiaoshiyilangzhao1996-droid/yinyo-liuyao`
PINNED_SHA: `1f67eea0ce5a2c49e6851e4eedce507f9c044dd9`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo tuyên bố là engine 六爻 theo 《增删卜易》/野鹤老人, gồm 120 rule, 412 卦例, 64卦纳甲表 và pipeline L0–L5 từ input đến kết luận.

## Candidate value

- Corpus rule + case đủ lớn để audit phương pháp.
- Có cấu trúc tách rules, reference, examples, divination types và pressure tests.
- Có thể dùng để kiểm xem một rule được dùng nhất quán qua nhiều case hay không.

## Local candidate rules

`YL-001` — Mỗi rule trong repo phải có locator tới 《增删卜易》 hoặc được hạ xuống `REPO_DERIVED`.

`YL-002` — “335 case regression pass” là evidence về self-consistency của repo, không tự động là predictive validation.

`YL-003` — Case gốc, rule trích xuất và lời diễn giải của repo phải được lưu thành ba lớp khác nhau.

`YL-004` — Không dùng style “野鹤表达DNA” làm evidence cho correctness.

## What to audit

1. `docs/rules.md`: inventory 120 rule.
2. `docs/examples.md`: map rule ↔ case.
3. `docs/reference.md`: 纳甲/世应/六亲 constants và provenance.
4. `subskills/pressure-tests.md`: test đang kiểm logic gì.
5. Đối chiếu nguyên văn 《增删卜易》 theo chapter/page/edition.

## Validation

```text
RULE_ID -> REPO WORDING -> CLASSICAL LOCATOR -> PRECONDITION
-> CASE APPLICATION -> EXPECTED CLAIM -> COUNTEREXAMPLE
```

Không sửa rule sau khi biết outcome của blind case.

## Next bounded task

Trích inventory 120 rule và chọn 10 rule lõi để kiểm provenance trước, không audit 120 rule một lúc.
