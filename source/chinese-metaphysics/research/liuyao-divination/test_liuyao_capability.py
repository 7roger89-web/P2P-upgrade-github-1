#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
p = Path(__file__).with_name('run_liuyao_capability.py')
def run(args):
    r = subprocess.run([sys.executable, str(p), *args], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr); raise SystemExit(r.returncode)
    return json.loads(r.stdout)
fixture = run(['--fixture', 'canonical-01'])
assert fixture['DOMAIN'] == 'LIUYAO'
assert fixture['BOARD_PACKET']['changed_hexagram'] == '地雷复'
assert fixture['STRUCTURAL_OUTPUT'] == 'SUPPORT_EXISTS_BUT_SELF_SIDE_CONSTRAINT_PRESENT'
custom = run(['--hexagram', '地泽临', '--moving', '2', '--month', '未', '--day', '辛卯', '--yongshen', '妻财'])
assert custom['INPUT_MODE'] == 'CUSTOM'
assert custom['BOARD_PACKET']['hexagram'] == '地泽临'
assert custom['BOARD_FROZEN'] == 'YES'
assert custom['STRUCTURAL_OUTPUT'] == 'BOARD_AND_SELECTED_RULE_FACTS_ONLY'
print('LIUYAO_CAPABILITY_TEST=PASS')
