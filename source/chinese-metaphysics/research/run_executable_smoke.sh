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
grep -Fq '"METHOD_SCOPE": "MEIHUA_TI_YONG_WUXING_RELATION_ONLY"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"STATUS": "ENGINE_SOURCE_BOUND_STRUCTURAL_READING"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"CLASSICAL_TEXT_GROUNDED": false' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"SIGNAL_ENGINE_VOCAB_VALIDATED": true' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"PROVENANCE_POLICY": "MECHANICAL_CROSS_LANE_BRIDGE_KEEP_SOURCE_PACKETS_INDEPENDENT;NO_CLASSICAL_TEXT_GROUNDING_OVERCLAIM"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"INTERPRETATION_STATUS": "BOUNDED_STRUCTURAL_METHOD_ONLY"' <<<"$MEIHUA_YIJING_OUT"
grep -Fq '"PREDICTIVE_STATUS": "NOT_ESTABLISHED_NEGATIVE_EVIDENCE_PRESERVED"' <<<"$MEIHUA_YIJING_OUT"
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
grep -Fq '"INTERPRETATION_STATUS": "BOUNDED_STRUCTURAL_METHOD_ONLY"' <<<"$MEIHUA_YIJING_TIME_OUT"
echo 'MEIHUA_YIJING_TIME_EVIDENCE_BRIDGE_SMOKE=PASS'

# Classical-equivalent live time input: 2024 is a 辰 year, 15:00 is 申时.
# With month 12/day 17 it reproduces the locked 观梅 arithmetic and therefore
# gives a known source-grounded 体用 relation: 用克体 -> PRESSURE_ON_BODY.
MEIHUA_YIJING_CLASSICAL_OUT="$(python "$ROOT/source/chinese-metaphysics/research/run_meihua_yijing_evidence.py" \
  --lunar-year 2024 --month 12 --day 17 --hour 15)"
grep -Fq '"CASTING_MODE": "TRADITIONAL_TIME_CASTING"' <<<"$MEIHUA_YIJING_CLASSICAL_OUT"
grep -Fq '"MEIHUA_MAIN_HEXAGRAM_REPORTED": "泽火革"' <<<"$MEIHUA_YIJING_CLASSICAL_OUT"
grep -Fq '"INITIAL_SIGNAL": "PRESSURE_ON_BODY"' <<<"$MEIHUA_YIJING_CLASSICAL_OUT"
grep -Fq '"RULE_POLICY": "NORMALIZE_EXISTING_PINNED_ENGINE_RELATION; ENGLISH_LABELS_ARE_ADAPTER_NOT_DOCTRINE"' <<<"$MEIHUA_YIJING_CLASSICAL_OUT"
grep -Fq '"INTERPRETATION_STATUS": "BOUNDED_STRUCTURAL_METHOD_ONLY"' <<<"$MEIHUA_YIJING_CLASSICAL_OUT"
grep -Fq '"PREDICTIVE_STATUS": "NOT_ESTABLISHED_NEGATIVE_EVIDENCE_PRESERVED"' <<<"$MEIHUA_YIJING_CLASSICAL_OUT"
echo 'MEIHUA_STRUCTURAL_READING_CLASSICAL_SMOKE=PASS'

# Anti-hindsight engineering fixture. Seal the exact question + casting input +
# evidence packet before any outcome can be supplied. Run twice to prove the
# canonical SHA-256 lock is deterministic. This fixture is NOT predictive evidence.
MEIHUA_LOCK_ONE="$(python "$ROOT/source/chinese-metaphysics/research/run_meihua_interpretation_lock.py" \
  --question 'ENGINEERING_FIXTURE_DO_NOT_SCORE' --lunar-year 2024 --month 12 --day 17 --hour 15)"
MEIHUA_LOCK_TWO="$(python "$ROOT/source/chinese-metaphysics/research/run_meihua_interpretation_lock.py" \
  --question 'ENGINEERING_FIXTURE_DO_NOT_SCORE' --lunar-year 2024 --month 12 --day 17 --hour 15)"
grep -Fq '"SCHEMA": "MEIHUA_INTERPRETATION_LOCK_V1"' <<<"$MEIHUA_LOCK_ONE"
grep -Fq '"LOCK_STATUS": "SEALED_BEFORE_OUTCOME"' <<<"$MEIHUA_LOCK_ONE"
grep -Fq '"OUTCOME_STATUS": "NOT_ACCEPTED_BY_LOCK_COMMAND"' <<<"$MEIHUA_LOCK_ONE"
grep -Fq '"INITIAL_SIGNAL": "PRESSURE_ON_BODY"' <<<"$MEIHUA_LOCK_ONE"
grep -Fq '"ENGINEERING_LOCK_FIXTURE_IS_NOT_PREDICTIVE_EVIDENCE"' <<<"$MEIHUA_LOCK_ONE"
LOCK_HASH_ONE="$(python -c 'import json,sys; print(json.load(sys.stdin)["LOCK_SHA256"])' <<<"$MEIHUA_LOCK_ONE")"
LOCK_HASH_TWO="$(python -c 'import json,sys; print(json.load(sys.stdin)["LOCK_SHA256"])' <<<"$MEIHUA_LOCK_TWO")"
[[ "$LOCK_HASH_ONE" =~ ^[0-9a-f]{64}$ ]]
test "$LOCK_HASH_ONE" = "$LOCK_HASH_TWO"
echo 'MEIHUA_INTERPRETATION_LOCK_SMOKE=PASS'

# Outcome reveal engineering fixture. The genuine lock must verify, while a
# post-lock question mutation must fail before any outcome can be attached.
MEIHUA_LOCK_FILE="$(mktemp)"
MEIHUA_TAMPERED_LOCK_FILE="$(mktemp)"
trap 'rm -f "$MEIHUA_LOCK_FILE" "$MEIHUA_TAMPERED_LOCK_FILE"' EXIT
printf '%s\n' "$MEIHUA_LOCK_ONE" >"$MEIHUA_LOCK_FILE"
MEIHUA_REVEAL_OUT="$(python "$ROOT/source/chinese-metaphysics/research/run_meihua_outcome_reveal.py" \
  --lock-file "$MEIHUA_LOCK_FILE" --outcome 'ENGINEERING_FIXTURE_OUTCOME_DO_NOT_SCORE')"
grep -Fq '"SCHEMA": "MEIHUA_OUTCOME_REVEAL_V1"' <<<"$MEIHUA_REVEAL_OUT"
grep -Fq '"LOCK_VERIFICATION": "PASS"' <<<"$MEIHUA_REVEAL_OUT"
grep -Fq '"EVIDENCE_VERIFICATION": "PASS"' <<<"$MEIHUA_REVEAL_OUT"
grep -Fq '"REVEAL_STATUS": "LOCK_VERIFIED_OUTCOME_ATTACHED"' <<<"$MEIHUA_REVEAL_OUT"
grep -Fq '"SCORING_STATUS": "NOT_PERFORMED"' <<<"$MEIHUA_REVEAL_OUT"
grep -Fq '"ENGINEERING_REVEAL_FIXTURE_IS_NOT_PREDICTIVE_EVIDENCE"' <<<"$MEIHUA_REVEAL_OUT"
python - "$MEIHUA_LOCK_FILE" "$MEIHUA_TAMPERED_LOCK_FILE" <<'PY'
import json
import sys
src, dst = sys.argv[1], sys.argv[2]
with open(src, 'r', encoding='utf-8') as handle:
    packet = json.load(handle)
packet['QUESTION'] = 'POST_LOCK_TAMPER_ATTEMPT'
with open(dst, 'w', encoding='utf-8') as handle:
    json.dump(packet, handle, ensure_ascii=False, indent=2)
PY
if python "$ROOT/source/chinese-metaphysics/research/run_meihua_outcome_reveal.py" \
  --lock-file "$MEIHUA_TAMPERED_LOCK_FILE" --outcome 'ENGINEERING_FIXTURE_OUTCOME_DO_NOT_SCORE' >/dev/null 2>&1; then
  echo 'Tampered lock unexpectedly passed reveal verification' >&2
  exit 1
fi
echo 'MEIHUA_OUTCOME_REVEAL_TAMPER_GUARD_SMOKE=PASS'
echo 'MEIHUA_OUTCOME_REVEAL_SMOKE=PASS'

# Prediction claim engineering fixture. The claim is explicitly declared,
# never inferred from PRESSURE_ON_BODY, and its exact-match rule is sealed
# before outcome. This fixture remains engineering evidence only.
MEIHUA_CLAIM_ONE="$(python "$ROOT/source/chinese-metaphysics/research/run_meihua_prediction_claim_lock.py" \
  --lock-file "$MEIHUA_LOCK_FILE" --outcome-labels OUTCOME_A OUTCOME_B --predicted-label OUTCOME_A)"
MEIHUA_CLAIM_TWO="$(python "$ROOT/source/chinese-metaphysics/research/run_meihua_prediction_claim_lock.py" \
  --lock-file "$MEIHUA_LOCK_FILE" --outcome-labels OUTCOME_B OUTCOME_A --predicted-label OUTCOME_A)"
grep -Fq '"SCHEMA": "MEIHUA_PREDICTION_CLAIM_LOCK_V1"' <<<"$MEIHUA_CLAIM_ONE"
grep -Fq '"OUTCOME_LABEL_SET": [' <<<"$MEIHUA_CLAIM_ONE"
grep -Fq '"PREDICTED_LABEL": "OUTCOME_A"' <<<"$MEIHUA_CLAIM_ONE"
grep -Fq '"SCORING_RULE": "EXACT_LABEL_MATCH"' <<<"$MEIHUA_CLAIM_ONE"
grep -Fq '"CLAIM_STATUS": "SEALED_BEFORE_OUTCOME"' <<<"$MEIHUA_CLAIM_ONE"
grep -Fq '"SCORING_STATUS": "RULE_LOCKED_NOT_PERFORMED"' <<<"$MEIHUA_CLAIM_ONE"
grep -Fq '"PREDICTED_LABEL_IS_EXPLICITLY_DECLARED_NOT_INFERRED_FROM_STRUCTURAL_SIGNAL"' <<<"$MEIHUA_CLAIM_ONE"
CLAIM_HASH_ONE="$(python -c 'import json,sys; print(json.load(sys.stdin)["CLAIM_SHA256"])' <<<"$MEIHUA_CLAIM_ONE")"
CLAIM_HASH_TWO="$(python -c 'import json,sys; print(json.load(sys.stdin)["CLAIM_SHA256"])' <<<"$MEIHUA_CLAIM_TWO")"
[[ "$CLAIM_HASH_ONE" =~ ^[0-9a-f]{64}$ ]]
test "$CLAIM_HASH_ONE" = "$CLAIM_HASH_TWO"
if python "$ROOT/source/chinese-metaphysics/research/run_meihua_prediction_claim_lock.py" \
  --lock-file "$MEIHUA_LOCK_FILE" --outcome-labels OUTCOME_A OUTCOME_B --predicted-label OUTCOME_C >/dev/null 2>&1; then
  echo 'Prediction label outside locked outcome set unexpectedly passed' >&2
  exit 1
fi
echo 'MEIHUA_PREDICTION_CLAIM_LOCK_SMOKE=PASS'

echo 'CHINESE_METAPHYSICS_LIVE_INPUT_ROAD_SMOKE=PASS'
