#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

# Fixture smoke: preserve the accepted bounded regression surfaces.
node "$ROOT/source/chinese-metaphysics/research/iztro/run_ziwei_capability.mjs" --fixture default | grep -q '"DOMAIN": "ZIWEI_DOUSHU"'
python "$ROOT/source/chinese-metaphysics/research/liuyao-divination/run_liuyao_capability.py" --fixture canonical-01 | grep -q '"DOMAIN": "LIUYAO"'
python "$ROOT/source/chinese-metaphysics/research/meihua-yishu/run_meihua_capability.py" --fixture guanmei | grep -q '"DOMAIN": "MEIHUA_YISHU"'
node "$ROOT/source/chinese-metaphysics/research/plum-cg/run_cegui_capability.mjs" --fixture zhen-4 | grep -q '"DOMAIN": "CEGUI"'
echo 'CHINESE_METAPHYSICS_EXECUTABLE_FIXTURE_SMOKE=PASS'

# Live-input road smoke: prove all four active domains still accept non-fixture
# input in one checkout. Outputs remain independent; there is no routing,
# voting, shared doctrine, or cross-domain synthesis here.
ZIWEI_OUT="$(node "$ROOT/source/chinese-metaphysics/research/iztro/run_ziwei_capability.mjs" \
  --date 1990-01-01 --civil-hour 12 --civil-minute 0 --gender female \
  --time-basis true-solar --longitude 104.08 --utc-offset 8 --algorithm zhongzhou)"
printf '%s' "$ZIWEI_OUT" | grep -q '"INPUT_MODE": "CUSTOM"'
printf '%s' "$ZIWEI_OUT" | grep -q '"basis": "TRUE_SOLAR_TIME"'
printf '%s' "$ZIWEI_OUT" | grep -q '"PROFILE_ID": "IZTRO_ZHONGZHOU_MECHANICAL_001"'

LIUYAO_OUT="$(python "$ROOT/source/chinese-metaphysics/research/liuyao-divination/run_liuyao_capability.py" \
  --hexagram 雷水解 --moving 3 --month 申 --day 甲子 --yongshen 官鬼)"
printf '%s' "$LIUYAO_OUT" | grep -q '"INPUT_MODE": "CUSTOM"'
printf '%s' "$LIUYAO_OUT" | grep -q '"BOARD_FROZEN": "YES"'
printf '%s' "$LIUYAO_OUT" | grep -q '"hexagram": "雷水解"'

MEIHUA_OUT="$(python "$ROOT/source/chinese-metaphysics/research/meihua-yishu/run_meihua_capability.py" --numbers 7 4 11)"
printf '%s' "$MEIHUA_OUT" | grep -q '"INPUT_MODE": "CUSTOM"'
printf '%s' "$MEIHUA_OUT" | grep -q '"CASTING_MODE": "NUMBER_CASTING"'
printf '%s' "$MEIHUA_OUT" | grep -q '"MAIN_HEXAGRAM": "山雷颐"'

CEGUI_OUT="$(node "$ROOT/source/chinese-metaphysics/research/plum-cg/run_cegui_capability.mjs" \
  --format-string 444 --five-method method2)"
printf '%s' "$CEGUI_OUT" | grep -q '"INPUT_MODE": "CUSTOM"'
printf '%s' "$CEGUI_OUT" | grep -q '"METHOD_ID": "METHOD_2_CE5_GEN_GUI5_KUN"'
printf '%s' "$CEGUI_OUT" | grep -q '"SELECTION_STATUS": "EXPLICITLY_SELECTED"'

echo 'CHINESE_METAPHYSICS_LIVE_INPUT_ROAD_SMOKE=PASS'
