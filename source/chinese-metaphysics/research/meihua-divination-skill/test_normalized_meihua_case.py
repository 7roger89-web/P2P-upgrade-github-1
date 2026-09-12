#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / 'run_normalized_meihua_case.py'
BASE_RUNNER = HERE.parent / 'meihua-yishu' / 'run_meihua_capability.py'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    return json.loads(r.stdout)


def run_fail(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        raise AssertionError(f'Expected failure: {cmd}')
    return r


def write_case(payload):
    f = tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.json', delete=False)
    with f:
        json.dump(payload, f, ensure_ascii=False)
    return f.name


case_path = write_case({
    'question_context': 'engineering equivalence fixture',
    'upper_trigram': 'dui',
    'lower_trigram': 'li',
    'moving_line': 1,
    'month_branch': '',
    'day_branch': '',
    'external_signs': [],
    'notes': 'aliases should normalize without changing cast facts',
})
bridge = run([sys.executable, str(RUNNER), '--input', case_path])
baseline = run([sys.executable, str(BASE_RUNNER), '--fixture', 'guanmei'])
# Public-oracle path only: 2 -> 兌, 3 -> 離, and 2+3+2=7 -> moving line 1.
# This is NOT used by runtime transport; it independently cross-checks the
# pinned private analyzer on an equivalent mechanical hexagram.
public_oracle = run([sys.executable, str(BASE_RUNNER), '--numbers', '2', '3', '2'])

assert bridge['DOMAIN'] == 'MEIHUA_YISHU'
assert bridge['CAPABILITY'] == 'PINNED_NORMALIZED_CASE_TO_ANALYSIS_PACKET'
assert bridge['CALCULATOR_SURFACE'] == '_analyze_hexagram'
assert bridge['CALCULATOR_SURFACE_KIND'] == 'PINNED_PRIVATE_FUNCTION_WITH_SIGNATURE_GUARD'
assert 'upper_gua' in bridge['CALCULATOR_SURFACE_SIGNATURE']
assert 'lower_gua' in bridge['CALCULATOR_SURFACE_SIGNATURE']
assert 'dong_yao' in bridge['CALCULATOR_SURFACE_SIGNATURE']
assert 'season' in bridge['CALCULATOR_SURFACE_SIGNATURE']
assert bridge['NORMALIZED_INPUT']['upper_trigram'] == '兑'
assert bridge['NORMALIZED_INPUT']['lower_trigram'] == '离'
assert bridge['NORMALIZED_INPUT']['moving_lines'] == [1]
assert bridge['ANALYZER_INPUT']['upper_trigram_number'] == 2
assert bridge['ANALYZER_INPUT']['lower_trigram_number'] == 3
assert bridge['MAIN_HEXAGRAM'] == baseline['MAIN_HEXAGRAM'] == '泽火革'
assert bridge['CHANGED_HEXAGRAM'] == baseline['CHANGED_HEXAGRAM'] == '泽山咸'
assert bridge['MOVING_LINE'] == baseline['MOVING_LINE'] == 1
assert bridge['EXTERNAL_SIGN_STATUS'] == 'MISSING_DO_NOT_FABRICATE'
assert bridge['FINAL_PREDICTION'] == 'NOT_EMITTED'

assert public_oracle['CASTING_MODE'] == 'NUMBER_CASTING'
assert public_oracle['MAIN_HEXAGRAM'] == bridge['MAIN_HEXAGRAM']
assert public_oracle['MUTUAL_HEXAGRAM'] == bridge['MUTUAL_HEXAGRAM']
assert public_oracle['CHANGED_HEXAGRAM'] == bridge['CHANGED_HEXAGRAM']
assert public_oracle['MOVING_LINE'] == bridge['MOVING_LINE']
assert public_oracle['TI_YONG_RELATION'] == bridge['BODY_USE']['生克關係']

multi_path = write_case({
    'question_context': 'must not silently coerce multiple moving lines',
    'upper_trigram': '兑',
    'lower_trigram': '离',
    'moving_lines': [1, 2],
})
multi = run_fail([sys.executable, str(RUNNER), '--input', multi_path])
assert 'requires exactly one moving line' in multi.stderr

bad_alias_path = write_case({
    'question_context': 'bad alias',
    'upper_trigram': 'not-a-trigram',
    'lower_trigram': 'li',
    'moving_line': 1,
})
bad = run_fail([sys.executable, str(RUNNER), '--input', bad_alias_path])
assert 'Normalization failed' in bad.stderr

print('MEIHUA_NORMALIZED_CASE_TEST=PASS')
