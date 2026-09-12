#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / 'run_yinyo_reasoning_lane.py'
MULTI = HERE.parent / 'liuyao-divination' / 'run_liuyao_multi_read.py'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    return json.loads(r.stdout)


lane = run([sys.executable, str(RUNNER), '--fixture', 'canonical-01'])
base = run([sys.executable, str(MULTI), '--fixture', 'canonical-01', '--lenses', '妻财'])

assert lane['DOMAIN'] == 'LIUYAO'
assert lane['CAPABILITY'] == 'ISOLATED_YINYO_STRUCTURAL_REASONING_LANE'
assert lane['BOARD_FINGERPRINT_SHA256'] == base['BOARD_FINGERPRINT_SHA256']
assert lane['FINAL_VERDICT'] == 'NOT_EMITTED'
assert lane['PREDICTIVE_STATUS'] == 'NOT_TESTED'

patterns = {x['rule_id']: x for x in lane['PATTERNS']}
assert set(patterns) == {'YINYO_L3_XUNKONG', 'YINYO_L3_YUEPO', 'YINYO_L3_JINTUI'}
assert patterns['YINYO_L3_JINTUI']['status'] == 'PRESENT'
assert any(x['position'] == 2 and x['jin_tui'] == '化退神' for x in patterns['YINYO_L3_JINTUI']['matches'])
assert 'GOOD_BAD_DEPENDS_ON_SUBJECT_AND_YONGSHEN_CHAIN' in patterns['YINYO_L3_JINTUI']['interpretation_boundary']
assert 'NO_NEW_BOARD_ENGINE' in lane['NONCLAIMS']
assert 'NO_CROSS_REPO_RULE_NORMALIZATION' in lane['NONCLAIMS']

custom = run([
    sys.executable, str(RUNNER),
    '--hexagram', '地泽临', '--moving', '2', '--month', '未', '--day', '辛卯'
])
assert custom['BOARD_FINGERPRINT_SHA256'] == lane['BOARD_FINGERPRINT_SHA256']

print('YINYO_REASONING_LANE_TEST=PASS')
