#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

# Fixture smoke: preserve the accepted bounded regression surfaces.
ZIWEI_FIXTURE="$(node "$ROOT/source/chinese-metaphysics/research/iztro/run_ziwei_capability.mjs" --fixture default)"
grep -Fq '"DOMAIN": "ZIWEI_DOUSHU"' <<<"$ZIWEI_FIXTURE"
LIUYAO_FIXTURE="$(python "$ROOT/source/chinese-metaphysics/research/liuyao-divination/run_liuyao_capability.py" --fixture canonical-01)"
grep -Fq '"DOMAIN": "LIUYAO"' <<<"$LIUYAO_FIXTURE"
MEIHUA_FIXTURE="$(python "$ROOT/source/chinese-metaphysics/research/meihua-yishu/run_meihua_capability.py" --fixture guanmei)"
grep -Fq '"DOMAIN": "MEIHUA_YISHU"' <<<"$MEIHUA_FIXTURE"
CEGUI_FIXTURE="$(node "$ROOT/source/chinese-metaphysics/research/plum-cg/run_cegui_capability.mjs" --fixture zhen-4)"
grep -Fq '"DOMAIN": "CEGUI"' <<<"$CEGUI_FIXTURE"
echo 'CHINESE_METAPHYSICS_EXECUTABLE_FIXTURE_SMOKE=PASS'

# Live-input road smoke: prove all five active domains still accept non-fixture
# input in one checkout. Outputs remain independent; there is no routing,
# voting, shared doctrine, or cross-domain synthesis here.
ZIWEI_OUT="$(node "$ROOT/source/chinese-metaphysics/research/iztro/run_ziwei_capability.mjs" \
  --date 1990-01-01 --civil-hour 12 --civil-minute 0 --gender female \
  --time-basis true-solar --longitude 104.08 --utc-offset 8 --algorithm zhongzhou)"
grep -Fq '"INPUT_MODE": "CUSTOM"' <<<"$ZIWEI_OUT"
grep -Fq '"basis": "TRUE_SOLAR_TIME"' <<<"$ZIWEI_OUT"
grep -Fq '"PROFILE_ID": "IZTRO_ZHONGZHOU_MECHANICAL_001"' <<<"$ZIWEI_OUT"
echo 'ZIWEI_LIVE_INPUT_SMOKE=PASS'

LIUYAO_OUT="$(python "$ROOT/source/chinese-metaphysics/research/liuyao-divination/run_liuyao_capability.py" \
  --hexagram 雷水解 --moving 3 --month 申 --day 甲子 --yongshen 官鬼)"
grep -Fq '"INPUT_MODE": "CUSTOM"' <<<"$LIUYAO_OUT"
grep -Fq '"BOARD_FROZEN": "YES"' <<<"$LIUYAO_OUT"
grep -Fq '"hexagram": "雷水解"' <<<"$LIUYAO_OUT"
echo 'LIUYAO_LIVE_INPUT_SMOKE=PASS'

MEIHUA_OUT="$(python "$ROOT/source/chinese-metaphysics/research/meihua-yishu/run_meihua_capability.py" --numbers 7 4 11)"
grep -Fq '"INPUT_MODE": "CUSTOM"' <<<"$MEIHUA_OUT"
grep -Fq '"CASTING_MODE": "NUMBER_CASTING"' <<<"$MEIHUA_OUT"
grep -Fq '"MAIN_HEXAGRAM": "山雷頤"' <<<"$MEIHUA_OUT"
echo 'MEIHUA_LIVE_INPUT_SMOKE=PASS'

CEGUI_OUT="$(node "$ROOT/source/chinese-metaphysics/research/plum-cg/run_cegui_capability.mjs" \
  --format-string 444 --five-method method2)"
grep -Fq '"INPUT_MODE": "CUSTOM"' <<<"$CEGUI_OUT"
grep -Fq '"METHOD_ID": "METHOD_2_CE5_GEN_GUI5_KUN"' <<<"$CEGUI_OUT"
grep -Fq '"SELECTION_STATUS": "EXPLICITLY_SELECTED"' <<<"$CEGUI_OUT"
echo 'CEGUI_LIVE_INPUT_SMOKE=PASS'

YIJING_OUT="$(python "$ROOT/source/chinese-metaphysics/research/yijing/run_yijing_capability.py" \
  --hexagram 谦 --moving 2,3)"
grep -Fq '"DOMAIN": "YIJING"' <<<"$YIJING_OUT"
grep -Fq '"NORMALIZED_HEXAGRAM": "地山谦"' <<<"$YIJING_OUT"
grep -Fq '"label": "六二"' <<<"$YIJING_OUT"
grep -Fq '"text": "鸣谦，贞吉。"' <<<"$YIJING_OUT"
grep -Fq '"CHANGED_HEXAGRAM": "地水师"' <<<"$YIJING_OUT"
grep -Fq '"TRANSFORMATION_RULE": "FLIP_MOVING_LINES_BOTTOM_TO_TOP_THEN_MAP_TRIGRAMS"' <<<"$YIJING_OUT"
echo 'YIJING_LIVE_INPUT_SMOKE=PASS'

echo 'CHINESE_METAPHYSICS_LIVE_INPUT_ROAD_SMOKE=PASS'
