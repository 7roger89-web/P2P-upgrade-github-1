# meihua-divination-skill — Independent Research Dossier

UPSTREAM: `Fyrgo8/meihua-divination-skill`
PINNED_SHA: `d70d73ad620afe39d1555a0386680790cfd09227`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo là một skill giải quẻ Mai Hoa theo workflow 9 bước, nhấn mạnh 体用、生克、旺衰、动爻、变卦、互卦、外应、错综 và bản nghĩa quẻ trước khi áp vào câu hỏi.

## Candidate value

- Workflow đọc quẻ rõ, dễ audit từng bước.
- Có `references/workflow.md`, output contracts, evals và input normalizer.
- Có self-check chống lẫn 六爻纳甲.

## Local candidate rules

`MDS-001` — Candidate order: 体用 → 生克 → 旺衰 → 动爻 → 变卦 → 互卦 → 外应 → 错综.

`MDS-002` — Phải tách 本卦/互卦/变卦 bản nghĩa khỏi application vào câu hỏi.

`MDS-003` — 外应 không được fabricate khi người dùng không cung cấp.

`MDS-004` — Rule của repo bắt chốt nhị phân ngay cả khi evidence yếu bị **REJECTED trong dossier này**. Thiếu evidence được phép `DO_NOT_CLAIM`.

## What to audit

1. `references/workflow.md` — source của từng bước.
2. `references/output-contracts.md` — phân biệt format với doctrine.
3. `evals/` — tiêu chí đang đo correctness hay chỉ format adherence.
4. Source cho 体用/卦气/外应/错综.

## Validation

Mỗi reading phải giữ chain:

```text
INPUT -> CAST FACTS -> LOCAL RULE -> SOURCE -> APPLICATION -> CLAIM
```

Không dùng rule từ repo Lục Hào hoặc repo Mai Hoa khác để vá khoảng trống.

## Next bounded task

Bóc 9 bước thành 9 candidate rule độc lập và tìm provenance cho từng bước.
