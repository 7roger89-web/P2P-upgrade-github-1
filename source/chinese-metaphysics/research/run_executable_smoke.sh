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
grep -Fq '"TUAN_TEXT": "' <<<"$YIJING_OUT"
grep -Fq '"DAXIANG_TEXT": "' <<<"$YIJING_OUT"
grep -Fq '"CHANGED_HEXAGRAM": "地水师"' <<<"$YIJING_OUT"
grep -Fq '"CHANGED_TUAN_TEXT": "' <<<"$YIJING_OUT"
grep -Fq '"CHANGED_DAXIANG_TEXT": "' <<<"$YIJING_OUT"
grep -Fq '"TRANSFORMATION_RULE": "FLIP_MOVING_LINES_BOTTOM_TO_TOP_THEN_MAP_TRIGRAMS"' <<<"$YIJING_OUT"

# Exercise one of the two verified source-label overlays through the public
# runtime, not merely through the audit helper.
YIJING_LABEL_OUT="$(python "$ROOT/source/chinese-metaphysics/research/yijing/run_yijing_capability.py" \
  --hexagram 解)"
grep -Fq '"NORMALIZED_HEXAGRAM": "雷水解"' <<<"$YIJING_LABEL_OUT"
grep -Fq '"TUAN_TEXT": "解，險以動，動而免乎險，解。' <<<"$YIJING_LABEL_OUT"
grep -Fq '"DAXIANG_TEXT": "雷雨作，解；君子以赦過宥罪。"' <<<"$YIJING_LABEL_OUT"
echo 'YIJING_LIVE_INPUT_SMOKE=PASS'

# Mechanical cross-lane assembly only: Meihua casts; Yi Jing supplies the
# source-grounded textual evidence. Doctrine and provenance remain separate.
MEIHUA_YIJING_OUT="$(python "$ROOT/source/chinese-metaphysics/research/run_meihua_yijing_evidence.py" --numbers 7 4 11)"
grep -Fq '"DOMAIN": "MEIHUA_YIJING_EVIDENCE"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"CASTING_MODE": "NUMBER_CASTING"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"MEIHUA_UPPER_TRIGRAM_RAW": "艮 ☶"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"MEIHUA_LOWER_TRIGRAM_RAW": "震 ☳"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"CANONICAL_UPPER_TRIGRAM": "艮"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"CANONICAL_LOWER_TRIGRAM": "震"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"MEIHUA_MAIN_HEXAGRAM_REPORTED": "山雷頤"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"YIJING_MAIN_HEXAGRAM_CANONICAL": "山雷颐"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"MAIN_HEXAGRAM_MAPPED_FROM_TRIGRAM_STRUCTURE": "PASS"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"MOVING_LINE_MATCHES_SELECTED_YAO": "PASS"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"SELECTED_YAO_TEXT_PRESENT": "PASS"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"SELECTED_XIAOXIANG_PRESENT": "PASS"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"PROVENANCE_POLICY": "MECHANICAL_CROSS_LANE_BRIDGE_KEEP_SOURCE_PACKETS_INDEPENDENT"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"INTERPRETATION_STATUS": "NOT_PERFORMED"' <<<"$MEIHUA_YIJING_OUT"
echo 'MEIHUA_YIJING_EVIDENCE_BRIDGE_SMOKE=PASS'

# Same bridge, second already-supported Meihua input mode. This proves the
# assembly is not accidentally hard-wired to number casting while preserving
# the upstream time-casting semantics unchanged.
MEIHUA_YIJING_TIME_OUT="$(python "$ROOT/source/chinese-metaphysics/research/run_meihua_yijing_evidence.py" \
  --lunar-year 2024 --month 8 --day 15 --hour 10)"
grep -Fq '"DOMAIN": "MEIHUA_YIJING_EVIDENCE"' <<<"$MEIHUA_YIJING_TIME_OUT"
grep -Fq '"CASTING_MODE": "TRADITIONAL_TIME_CASTING"' <<<"$MEIHUA_YIJING_TIME_OUT"
grep -Fq '"lunar_year": 2024' <<<"$MEIHUA_YIJING_TIME_OUT"
grep -Fq '"MAIN_HEXAGRAM_MAPPED_FROM_TRIGRAM_STRUCTURE": "PASS"' <<<"$MEIHUA_YIJING_TIME_OUT"
grep -Fq '"MOVING_LINE_MATCHES_SELECTED_YAO": "PASS"' <<<"$MEIHUA_YIJING_TIME_OUT"
grep -Fq '"SELECTED_YAO_TEXT_PRESENT": "PASS"' <<<"$MEIHUA_YIJING_TIME_OUT"
grep -Fq '"SELECTED_XIAOXIANG_PRESENT": "PASS"' <<<"$MEIHUA_YIJING_TIME_OUT"
grep -Fq '"INTERPRETATION_STATUS": "NOT_PERFORMED"' <<<"$MEIHUA_YIJING_TIME_OUT"
echo 'MEIHUA_YIJING_TIME_EVIDENCE_BRIDGE_SMOKE=PASS'

echo 'CHINESE_METAPHYSICS_LIVE_INPUT_ROAD_SMOKE=PASS'
