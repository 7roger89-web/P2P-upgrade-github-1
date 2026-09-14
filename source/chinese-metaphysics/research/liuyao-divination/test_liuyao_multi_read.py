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


JOHNSON_PIN = '1a5a78b513c0e7b46dfb29f74043bcf978c32a3e'
YINYO_PIN = '1f67eea0ce5a2c49e6851e4eedce507f9c044dd9'

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
    # visible case must NOT have missing resolution
    assert 'missing_yongshen_resolution' not in lens, f"visible lens {lens['lens']} should not have missing resolution"

custom = run([
    '--hexagram', '地泽临', '--moving', '2', '--month', '未', '--day', '辛卯',
    '--lenses', '妻财,官鬼',
])
assert custom['INPUT_MODE'] == 'CUSTOM'
assert custom['BOARD_FINGERPRINT_SHA256'] == fixture['BOARD_FINGERPRINT_SHA256']
assert [x['lens'] for x in custom['LENSES']] == ['妻财', '官鬼']

# --- REAL MISSING-YONGSHEN REGRESSION CASE ---
# Discovered via engine scan: 地天泰, moving [1], month 寅, day 甲子, lens 父母 has no visible yongshen
# main_qin = 妻财,官鬼,兄弟,兄弟,妻财,子孙 -> 父母 missing
# changed_qin = 兄弟 -> still missing
# month 寅 wood = 官鬼 for palace 土, day 子 water = 妻财 for palace 土 -> no day/month match
# => should be FUSHEN_LOOKUP_REQUIRED with full source trace, no fabrication
# Correction A requires outer status = VISIBLE_YONGSHEN_MISSING (neutral), nested carries precise resolution

missing = run([
    '--hexagram', '地天泰', '--moving', '1', '--month', '寅', '--day', '甲子',
    '--lenses', '父母',
])
assert missing['MECHANICAL_BOARD']['hexagram'] == '地天泰'
assert missing['MECHANICAL_BOARD']['palace'] == '坤'
assert missing['MECHANICAL_BOARD']['palace_wx'] == '土'
assert len(missing['LENSES']) == 1
ml = missing['LENSES'][0]
assert ml['lens'] == '父母'
assert ml['visible_yongshen_count'] == 0
assert ml['visible_yongshen_positions'] == []
# CORRECTION A: outer must be neutral
assert ml['status'] == 'VISIBLE_YONGSHEN_MISSING', f"outer status must be neutral VISIBLE_YONGSHEN_MISSING, got {ml['status']}"
assert 'missing_yongshen_resolution' in ml
res = ml['missing_yongshen_resolution']
assert res['status'] == 'FUSHEN_LOOKUP_REQUIRED'
assert res['fabricated_fusheng_position'] is False
# Correction B: no feishen position claimed
assert res.get('feishen_position_identified') is False
assert res.get('fusheng_position_computed') is False
# ensure no field named feishen_position or fusheng_position with actual coords
for k in res.keys():
    lk = k.lower()
    if 'feishen' in lk and 'position' in lk and 'not' not in lk and 'identified' not in lk:
        raise AssertionError(f"should not claim feishen position field {k}")
    if 'fusheng' in lk and 'position' in lk and 'computed' not in lk and 'fabricated' not in lk:
        # allow fabricated flag, but not actual position
        if isinstance(res[k], (list, dict, int)):
            raise AssertionError(f"should not have fusheng position {k}")
# checked facts
assert res['checked_facts']['main_qin'] == ['妻财', '官鬼', '兄弟', '兄弟', '妻财', '子孙']
assert res['checked_facts']['changed_qin'] == ['兄弟']
assert res['checked_facts']['changed_yongshen_positions'] == []
assert res['checked_facts']['month']['zhi'] == '寅'
assert res['checked_facts']['month']['qin'] == '官鬼'
assert res['checked_facts']['month']['match'] is False
assert res['checked_facts']['day']['gz'] == '甲子'
assert res['checked_facts']['day']['zhi'] == '子'
assert res['checked_facts']['day']['qin'] == '妻财'
assert res['checked_facts']['day']['match'] is False
assert res['checked_facts']['palace'] == '坤'
assert res['checked_facts']['palace_wx'] == '土'
# every mechanical claim traceable to board field/helper
assert 'lines[].qin' in res['checked_facts']['board_facts_used']
assert 'liuqin helper' in res['checked_facts']['board_facts_used']
# source refs
assert res['source_refs']['Johnson-Jia']['repo'] == 'Johnson-Jia/liuyao-divination'
assert res['source_refs']['Johnson-Jia']['pin'] == JOHNSON_PIN
assert res['source_refs']['Johnson-Jia']['path'] == 'references/02-用神取用.md'
assert res['source_refs']['Johnson-Jia']['section'] == '用神不上卦（伏神）'
assert res['source_refs']['Yinyo']['repo'] == 'xiaoshiyilangzhao1996-droid/yinyo-liuyao'
assert res['source_refs']['Yinyo']['pin'] == YINYO_PIN
assert res['source_refs']['Yinyo']['path'] == 'SKILL.md'
assert res['source_refs']['Yinyo']['section'] == '4.3 用神不现 -> 伏神取用规则'
# rule trace must mention both sources and must NOT claim main_qin as feishen
assert any('YINYO_L1' in x for x in res['rule_trace'])
assert any('JOHNSON_FUSHEN_DEF' in x for x in res['rule_trace'])
assert any('NO_FABRICATION' in x for x in res['rule_trace'])
# Correction B: wording must be factual, not main_qin==feishen
for tr in res['rule_trace']:
    # should not contain pattern "main (fei)" or "main_qin as feishen" in old form
    if 'check main (fei)' in tr.lower():
        raise AssertionError(f"rule_trace still claims main as feishen: {tr}")
    if 'FEI_BIAN_CHECK' in tr and 'main_qin and changed_qin' in tr and 'VISIBLE_MAIN' not in ''.join(res['rule_trace']):
        # old wording detected, require new wording
        pass
assert any('VISIBLE_MAIN_LINES_ALREADY_CHECKED' in x for x in res['rule_trace'])
assert any('CHANGED_LINES_CHECK' in x for x in res['rule_trace'])
assert any('FEISHEN_POSITION_NOT_IDENTIFIED' in x for x in res['rule_trace'])
assert any('FUSHEN_POSITION_NOT_COMPUTED' in x for x in res['rule_trace'])
# automation boundary must contain both
assert 'FUSHEN_POSITION_NOT_COMPUTED' in res['automation_boundary']
assert 'FEISHEN_POSITION_NOT_IDENTIFIED' in res['automation_boundary']
assert 'MECHANICAL_FACT' in res['mechanical_vs_method_vs_judgment']
assert 'METHOD_RULE' in res['mechanical_vs_method_vs_judgment']
assert 'INTERPRETIVE_JUDGMENT' in res['mechanical_vs_method_vs_judgment']
assert 'FEISHEN_POSITION_NOT_IDENTIFIED' in res['mechanical_vs_method_vs_judgment']
assert 'FUSHEN_POSITION_NOT_COMPUTED' in res['mechanical_vs_method_vs_judgment']

# multi-lens invariant for missing case: changing lens must not change fingerprint
multi_missing = run([
    '--hexagram', '地天泰', '--moving', '1', '--month', '寅', '--day', '甲子',
    '--lenses', '父母,兄弟,妻财',
])
# fingerprint must be same as single missing
assert multi_missing['BOARD_FINGERPRINT_SHA256'] == missing['BOARD_FINGERPRINT_SHA256']
by = {x['lens']: x for x in multi_missing['LENSES']}
assert by['父母']['visible_yongshen_count'] == 0
assert by['兄弟']['visible_yongshen_count'] == 2
assert by['妻财']['visible_yongshen_count'] == 2
# visible lenses should not have missing resolution, missing one should
assert 'missing_yongshen_resolution' in by['父母']
assert 'missing_yongshen_resolution' not in by['兄弟']
# outer statuses
assert by['父母']['status'] == 'VISIBLE_YONGSHEN_MISSING'
assert by['兄弟']['status'] == 'VISIBLE_YONGSHEN_FOUND'

# additional gate branches: DAY_MONTH and BIAN - Correction A requires outer neutral + nested precise
# case: 地山谦 辰 甲子 妻财 -> BIAN_YAO_YONGSHEN_PRESENT (month=父母, day=子孙, changed=妻财)
bian_case = run([
    '--hexagram', '地山谦', '--moving', '1', '--month', '辰', '--day', '甲子',
    '--lenses', '妻财',
])
assert bian_case['LENSES'][0]['visible_yongshen_count'] == 0
assert bian_case['LENSES'][0]['status'] == 'VISIBLE_YONGSHEN_MISSING'
assert bian_case['LENSES'][0]['missing_yongshen_resolution']['status'] == 'BIAN_YAO_YONGSHEN_PRESENT'
assert bian_case['LENSES'][0]['missing_yongshen_resolution']['checked_facts']['changed_yongshen_positions'] == [1]
# must NOT simultaneously claim FUSHEN_REQUIRED at outer when bian candidate exists
assert 'FUSHEN' not in bian_case['LENSES'][0]['status']
assert bian_case['LENSES'][0]['missing_yongshen_resolution']['status'] != 'FUSHEN_LOOKUP_REQUIRED'

# case: 地天泰 巳 甲子 父母 -> DAY_MONTH_SUBSTITUTION_CANDIDATE (month 巳 fire = 父母)
daymonth_case = run([
    '--hexagram', '地天泰', '--moving', '1', '--month', '巳', '--day', '甲子',
    '--lenses', '父母',
])
assert daymonth_case['LENSES'][0]['visible_yongshen_count'] == 0
assert daymonth_case['LENSES'][0]['status'] == 'VISIBLE_YONGSHEN_MISSING'
assert daymonth_case['LENSES'][0]['missing_yongshen_resolution']['status'] == 'DAY_MONTH_SUBSTITUTION_CANDIDATE'
assert daymonth_case['LENSES'][0]['missing_yongshen_resolution']['checked_facts']['month']['match'] is True
assert 'FUSHEN' not in daymonth_case['LENSES'][0]['status']

# true unresolved case already tested above (FUSHEN)
assert missing['LENSES'][0]['status'] == 'VISIBLE_YONGSHEN_MISSING'
assert missing['LENSES'][0]['missing_yongshen_resolution']['status'] == 'FUSHEN_LOOKUP_REQUIRED'

# upstream integrity
assert fixture['ENGINE_PIN'] == JOHNSON_PIN
assert fixture['YINYO_PIN'] == YINYO_PIN
assert missing['ENGINE_PIN'] == JOHNSON_PIN
assert missing['YINYO_PIN'] == YINYO_PIN

# visible case regression: fingerprint unchanged from known canonical
assert fixture['BOARD_FINGERPRINT_SHA256'] == '7708076da186d63f5730b2b41054316f7dbf94801da331ef52af20acb1befcf6'

print('LIUYAO_MULTI_READ_TEST=PASS')
print('MISSING_YONGSHEN_GATE=PASS')
print('OUTER_STATUS_CONTRADICTION_FIXED=YES')
print('REAL_MISSING_CASE=地天泰|1|寅|甲子|父母|FUSHEN_LOOKUP_REQUIRED')
