# Chinese Metaphysics — Per-Repository Research

RULE: `ONE_UPSTREAM_REPO = ONE_INDEPENDENT_RESEARCH_DOSSIER`

Không dùng repo A để lấp khoảng trống của repo B. Cùng một thuật ngữ (`四化`, `河洛`, `飞宫`, `体用`, `旺衰`, ...) vẫn là repo-local cho tới khi có task provenance comparison riêng.

## Audit evidence

Full isolated matrix audit completed successfully on 2026-09-11:

- Workflow: `.github/workflows/chinese-metaphysics-upstream-audit.yml`
- Run ID: `34520570058`
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

This index is navigation only. It is not a shared rule registry or merged methodology.
