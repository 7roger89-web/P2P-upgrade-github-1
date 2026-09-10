# ziwei-wuandyA — Independent Research Dossier

UPSTREAM: `wuandyA/ziwei`
PINNED_SHA: `4531626403a0c645f1e538a9ed145ffec8799420`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo là web app 紫微斗数 + AI. README nói phần排盘 dựa trên `iztro` và中州派安星法; sản phẩm còn có年度运势、双人合盘、四化互飞、人生K线 và knowledge/LLM layer.

Dossier này nghiên cứu **sản phẩm và logic riêng của repo**, không nhập rule của dependency `iztro` hoặc repo Tử Vi khác vào đây ngoài việc ghi rõ dependency.

## Candidate value

- Ví dụ thực tế về pipeline `deterministic chart -> knowledge -> LLM interpretation`.
- UI/UX của chart, annual trend, compatibility và share cards.
- `fortune-score.ts` là điểm cần audit mạnh vì biến mệnh lý thành định lượng/K-line.

## Local candidate rules

`ZWA-001` — Dữ liệu do `iztro` trả về phải phân biệt với rule/score do repo tự thêm.

`ZWA-002` — AI prompt/knowledge content là interpretation layer, không phải chart fact.

`ZWA-003` — Mọi “score”, K-line hoặc 100-year trend phải có công thức, source và calibration; nếu không chỉ là `PRODUCT_HEURISTIC`.

`ZWA-004` — 四化互飞 trong合盘 phải audit input binding và rule source riêng.

## What to audit

1. `app/src/lib/astro.ts` — boundary với iztro.
2. `app/src/lib/fortune-score.ts` — công thức định lượng.
3. `app/src/knowledge/` — nguồn và school của nội dung.
4. LLM prompt/adapter và cách fact được truyền vào model.
5. Annual fortune + compatibility logic.

## Validation

```text
IZTRO FACTS -> REPO-DERIVED FEATURES -> KNOWLEDGE/PROMPT -> AI CLAIM
```

Phải biết chính xác claim xuất hiện ở lớp nào.

## Commercial note

README ghi MIT; vẫn audit LICENSE/dependencies/knowledge content trước commercial reuse.

## Next bounded task

Audit `astro.ts + fortune-score.ts + knowledge/` và phân loại `FACT / RULE / HEURISTIC / PROMPT`.
