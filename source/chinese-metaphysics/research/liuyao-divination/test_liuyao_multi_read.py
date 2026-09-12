#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

runner = Path(__file__).with_name('run_liuyao_multi_read.py')


def run(args):
    r = subprocess.run([sys.executable, str(runner), *args], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    return json.loads(r.stdout)


fixture = run(['--fixture', 'canonical-01', '--lenses', '妻财,官鬼,父母,子孙,兄弟'])
assert fixture['DOMAIN'] == 'LIUYAO'
assert fixture['CAPABILITY'] == 'ONE_HEXAGRAM_MULTIPLE_LENSES'
assert fixture['INVARIANTS']['ONE_MECHANICAL_BOARD'] == 'YES'
assert fixture['INVARIANTS']['LENS_CHANGES_BOARD'] == 'NO'
assert fixture['INVARIANTS']['CROSS_LENS_SYNTHESIS'] == 'NO'
assert fixture['MECHANICAL_BOARD']['hexagram'] == '地泽临'
assert fixture['MECHANICAL_BOARD']['changed_hexagram'] == '地雷复'
assert len(fixture['LENSES']) == 5

by_lens = {x['lens']: x for x in fixture['LENSES']}
assert by_lens['妻财']['visible_yongshen_positions'] == [5]
assert by_lens['官鬼']['visible_yongshen_positions'] == [2]
assert by_lens['父母']['visible_yongshen_positions'] == [1]
assert by_lens['子孙']['visible_yongshen_positions'] == [6]
assert by_lens['兄弟']['visible_yongshen_positions'] == [3, 4]
for lens in fixture['LENSES']:
    assert lens['structural_output'] == 'LENS_FACTS_ONLY_NO_CROSS_LENS_SYNTHESIS'

custom = run([
    '--hexagram', '地泽临', '--moving', '2', '--month', '未', '--day', '辛卯',
    '--lenses', '妻财,官鬼',
])
assert custom['INPUT_MODE'] == 'CUSTOM'
assert custom['BOARD_FINGERPRINT_SHA256'] == fixture['BOARD_FINGERPRINT_SHA256']
assert [x['lens'] for x in custom['LENSES']] == ['妻财', '官鬼']

print('LIUYAO_MULTI_READ_TEST=PASS')
