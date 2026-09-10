# Chinese Metaphysics Upstreams

Purpose: preserve external upstream repositories for later independent research on 易经, 梅花易数, 六爻/纳甲, 一卦多断, 紫微斗数, 飞星, 河洛, 四化 and related methods.

These are Git submodules pinned to explicit upstream commits. They are references, not P2P-owned code and not evidence that any metaphysical claim is correct.

## Research isolation

**Mỗi upstream được nghiên cứu độc lập.** Hồ sơ nằm tại `research/<repo-name>/RESEARCH.md`. Không có methodology/rule registry/casebook chung ở giai đoạn này, nhằm tránh trộn rule và attribution giữa các repo/phái.

## Pinned upstreams

| Local path | Upstream | Branch | Pinned commit |
|---|---|---|---|
| `upstreams/plum-app` | `soom-lupulus/plum-app` | `master` | `5965bdc8e9ca69a3cc7e96be6f1cc585d5032814` |
| `upstreams/plum-cg` | `soom-lupulus/plum-cg` | `main` | `509fc43001a503d17a37db07bc56e069b1ff1c4f` |
| `upstreams/yinyo-liuyao` | `xiaoshiyilangzhao1996-droid/yinyo-liuyao` | `main` | `1f67eea0ce5a2c49e6851e4eedce507f9c044dd9` |
| `upstreams/liuyao-divination` | `Johnson-Jia/liuyao-divination` | `main` | `1a5a78b513c0e7b46dfb29f74043bcf978c32a3e` |
| `upstreams/meihua-yishu` | `muyen/meihua-yishu` | `main` | `8a9a5e0f482dd225bfe4a1c52c2ae5546228607a` |
| `upstreams/meihua-divination-skill` | `Fyrgo8/meihua-divination-skill` | `main` | `d70d73ad620afe39d1555a0386680790cfd09227` |
| `upstreams/iztro` | `SylarLong/iztro` | `main` | `2c7ef9be669df7b19d1799f4dce335fed3794f78` |
| `upstreams/ziwei-doushu-skill` | `Linden-TR/ziwei-doushu-skill` | `master` | `a842dd65dabdc4ce42ec9688b88ae876858a9977` |
| `upstreams/ziwei-wuandyA` | `wuandyA/ziwei` | `main` | `4531626403a0c645f1e538a9ed145ffec8799420` |
| `upstreams/ziwei-chart` | `ziweiknows/ziwei-chart` (redirected from `ruijayfeng/ziwei`) | `main` | `b172413d85addbe32facd9e20b9179db619f3afb` |
| `upstreams/xu-quanren` | `ZhangZangQian/xu-quanren` | `main` | `7b8364bbd79a11e852899893ac5749a83be62836` |

## Unresolved entries from discovery

- `TiongHaiTing/zi-wei-ai`: GitHub returned 404 on 2026-09-11. Not added.
- `Aquarian-Age/zwds`: GitHub returned 404 on 2026-09-11. Not added.

## Clone/init

```bash
git submodule update --init --recursive source/chinese-metaphysics/upstreams
```

Before any commercial reuse, audit each upstream license independently. A submodule reference does not grant P2P additional rights.
