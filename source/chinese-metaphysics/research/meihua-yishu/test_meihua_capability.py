#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

p = Path(__file__).with_name('run_meihua_capability.py')


def run(args):
    r = subprocess.run([sys.executable, str(p), *args], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    return json.loads(r.stdout)


fixture = run(['--fixture', 'guanmei'])
assert fixture['DOMAIN'] == 'MEIHUA_YISHU'
assert fixture['MAIN_HEXAGRAM'] == '泽火革'
assert fixture['CHANGED_HEXAGRAM'] == '泽山咸'
assert fixture['MOVING_LINE'] == 1
assert fixture['CASTING_MODE'] == 'TRADITIONAL_TIME_CASTING'
assert fixture['EXTERNAL_SIGN_STATUS'] == 'MISSING_DO_NOT_FABRICATE'

time_cast = run(['--lunar-year', '2024', '--month', '12', '--day', '8', '--hour', '14'])
assert time_cast['INPUT_MODE'] == 'CUSTOM'
assert time_cast['CASTING_MODE'] == 'TRADITIONAL_TIME_CASTING'
assert time_cast['MAIN_HEXAGRAM'] and time_cast['CHANGED_HEXAGRAM']
assert time_cast['STRUCTURAL_OUTPUT'] == 'TI_YONG_RELATION_REPORTED_ONLY'

number_cast = run(['--numbers', '7', '4', '11'])
assert number_cast['INPUT_MODE'] == 'CUSTOM'
assert number_cast['CASTING_MODE'] == 'NUMBER_CASTING'
assert number_cast['INPUT']['numbers'] == [7, 4, 11]
assert number_cast['MAIN_HEXAGRAM'] == '山雷頤'
assert number_cast['MOVING_LINE'] == 4
assert number_cast['STRUCTURAL_OUTPUT'] == 'TI_YONG_RELATION_REPORTED_ONLY'
assert number_cast['SEASON_CONTEXT_STATUS'] == 'ABSENT_NOT_INFERRED'
assert 'MEIHUA_NUMBER_CAST_MOVING_FROM_TOTAL' in number_cast['RULE_TRACE']

print('MEIHUA_CAPABILITY_TEST=PASS')
