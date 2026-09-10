# Chinese Metaphysics — Per-Repository Research

RULE: `ONE_UPSTREAM_REPO = ONE_INDEPENDENT_RESEARCH_DOSSIER`

Không dùng repo A để lấp khoảng trống của repo B. Cùng một thuật ngữ (`四化`, `河洛`, `飞宫`, `体用`, `旺衰`, ...) vẫn là repo-local cho tới khi có task provenance comparison riêng.

## Audit evidence

Full isolated matrix audit completed successfully on 2026-09-11:

- Workflow: `.github/workflows/chinese-metaphysics-upstream-audit.yml`
- Clean run ID: `34520570058`
- Result: `11/11 jobs SUCCESS`
- Each upstream was checked at its pinned SHA with a repo-appropriate contract: unit/build tests for executable engines; structure/helper tests for documentation/skill repos.
- `SUCCESS` means only that the declared technical/structural contract passed. It does **not** establish historical provenance or predictive validity.

## Dossiers

Each directory contains `RESEARCH.md` plus `AUDIT_2026-09-11.md`:

- `plum-app/`
- `plum-cg/`
- `yinyo-liuyao/`
- `liuyao-divination/`
- `meihua-yishu/`
- `meihua-divination-skill/`
- `iztro/`
- `ziwei-doushu-skill/`
- `ziwei-wuandyA/`
- `ziwei-chart/`
- `xu-quanren/`

## Three independent questions

Every dossier must distinguish:

1. `ENGINEERING`: code/build/test/structure có nhất quán không?
2. `PROVENANCE`: rule/method có truy được đúng source/school không?
3. `PREDICTIVE`: có evidence outcome-hidden/out-of-sample không?

A pass on one axis never promotes another axis.

## Quantitative-output rule

A deterministic score, K-line, percentage, confidence number or energy value is not automatically a calibrated measurement. If a repo assigns hand-picked weights or thresholds without empirical calibration and source provenance, classify that output as `PRODUCT_HEURISTIC`, not objective predictive evidence.

## Current high-value contradictions / warnings

- `xu-quanren` uses 庚四化 `太阳/武曲/太阴/天同`; the inspected Linden/iztro convention uses `太阳/武曲/天同/天相`. Treat this as a school/convention fork requiring primary-source arbitration.
- `yinyo-liuyao` structurally confirms 120 rule IDs, but the current packaged corpus audit found 128 unique `Gxxx` IDs rather than independently proving the advertised 412 cases. Its pressure tests expose known outcomes and are retrospective regression, not blind predictive tests.
- `muyen/meihua-yishu` is the only upstream in this pass with a substantial explicit predictive experiment; its tested operationalization performed around chance and the repo reports that negative result.
- `wuandyA/ziwei` and `ziweiknows/ziwei-chart` include deterministic-looking 0–100 fortune/K-line scoring built from hand-selected weights; classify these scores as product heuristics until calibrated.

This index is navigation only. It is not a shared rule registry or merged methodology.
