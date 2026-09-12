#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
node "$ROOT/source/chinese-metaphysics/research/iztro/run_ziwei_capability.mjs" --fixture default | grep -q '"DOMAIN": "ZIWEI_DOUSHU"'
python "$ROOT/source/chinese-metaphysics/research/liuyao-divination/run_liuyao_capability.py" --fixture canonical-01 | grep -q '"DOMAIN": "LIUYAO"'
python "$ROOT/source/chinese-metaphysics/research/meihua-yishu/run_meihua_capability.py" --fixture guanmei | grep -q '"DOMAIN": "MEIHUA_YISHU"'
node "$ROOT/source/chinese-metaphysics/research/plum-cg/run_cegui_capability.mjs" --fixture zhen-4 | grep -q '"DOMAIN": "CEGUI"'
echo 'CHINESE_METAPHYSICS_EXECUTABLE_SMOKE=PASS'
