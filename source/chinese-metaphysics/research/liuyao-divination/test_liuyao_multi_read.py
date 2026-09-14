#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

runner = Path(__file__).with_name('run_liuyao_multi_read.py')

# Import the runner as a module so the palace-head derivation and the
# multi-candidate preservation path can be probed directly against Johnson data.
# Module import only re-runs the pin verification; main() stays guarded.
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location('run_liuyao_multi_read', runner)
mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(mod)


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
# => the gate reaches FUSHEN_LOOKUP_REQUIRED, which this slice advances to
#    JOHNSON-NATIVE FUSHEN PLACEMENT (no fabrication: Johnson data + Johnson engine)
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
assert res['status'] == 'FUSHEN_PLACEMENT_IDENTIFIED'
# no position is fabricated: everything is derived from Johnson data + Johnson engine
assert res['fabricated_fusheng_position'] is False
assert res['fushen_position_computed'] is True
assert res['feishen_position_identified'] is True
# placement stops at mechanics: no strength / judgment is assessed or emitted
assert res['fushen_effectiveness'] == 'NOT_ASSESSED'
assert res['good_bad_judgment'] == 'NOT_EMITTED'

fu = res['fushen_placement']
fei = res['feishen_placement']
assert fu is not None and fei is not None
assert fu['status'] == 'FUSHEN_PLACEMENT_IDENTIFIED'
assert fu['fail_closed'] is False
assert fu['judgment_emitted'] is False

# --- E: pure-palace hexagram derived from Johnson HEXAGRAMS, not a new mapping ---
sel = fu['pure_palace_selection']
assert sel['source'] == 'Johnson-Jia/liuyao-divination src/liuyao/data.py HEXAGRAMS'
assert sel['pin'] == JOHNSON_PIN
assert sel['condition'] == 'record.palace == P AND record.upper == P AND record.lower == P'
assert sel['records_scanned'] == 64          # Johnson holds all 64 hexagrams
assert sel['index_keys_scanned'] == 128      # full name + single-char alias keys
assert sel['palace'] == missing['MECHANICAL_BOARD']['palace']
assert sel['hit_count'] == 1                 # exactly one palace head, structurally proven
assert sel['unique'] is True
assert sel['handwritten_palace_map_used'] is False
assert fu['pure_palace_unique'] is True
assert fu['pure_palace_hexagram'] == sel['hits'][0]

# --- F: pure-palace board produced by Johnson cast_board(), no manual lines ---
pbs = fu['pure_palace_board_source']
assert pbs['engine'] == 'Johnson-Jia/liuyao-divination cast_board()'
assert pbs['pin'] == JOHNSON_PIN
assert pbs['manual_line_calculation'] is False
assert pbs['call']['hexagram'] == fu['pure_palace_hexagram']
assert pbs['call']['moving'] == []           # minimal legal moving-line input
assert pbs['call']['month_zhi'] == missing['MECHANICAL_BOARD']['month_zhi']
assert pbs['call']['day_gz'] == missing['MECHANICAL_BOARD']['day_gz']
assert pbs['call']['yongshen_qin'] == '父母'

# --- G: fushen facts come from that Johnson-generated pure board ---
# Cross-checked by re-deriving the palace head and re-casting with Johnson itself,
# so the expected position is computed by Johnson, never hard-coded from the prompt.
_palace = missing['MECHANICAL_BOARD']['palace']
_rec, _proof = mod._pure_palace_record(_palace)
_pure = mod.cast_board(_rec['name'], [], missing['MECHANICAL_BOARD']['month_zhi'],
                       missing['MECHANICAL_BOARD']['day_gz'], '父母')
_expected = [
    {'position': l.position, 'gan': l.gan, 'zhi': l.zhi, 'wx': l.wx, 'qin': l.qin}
    for l in _pure.lines if l.qin == '父母'
]
assert fu['candidates'] == _expected
assert fu['pure_palace_board_qin'] == [l.qin for l in _pure.lines]
assert fu['candidate_count'] == len(_expected) >= 1
assert fu['all_candidates_preserved'] is True
assert fu['arbitrary_selection_made'] is False
# only fields Johnson's Line actually supports are emitted (no invented field)
for c in fu['candidates']:
    assert set(c.keys()) == {'position', 'gan', 'zhi', 'wx', 'qin'}
    assert c['qin'] == '父母'
assert 'Johnson cast_board()' in fu['position_source']
assert 'references/02-用神取用.md' in fu['position_source']
assert JOHNSON_PIN in fu['position_source']

# --- H: feishen is ONLY the main-board line at the confirmed fushen position ---
assert fei['status'] == 'FEISHEN_POSITION_IDENTIFIED'
assert fei['derived_from_confirmed_fushen_position'] is True
assert fei['all_main_lines_called_feishen'] is False
assert fei['judgment_emitted'] is False
assert fei['candidate_count'] == fu['candidate_count']
assert [c['position'] for c in fei['candidates']] == [c['position'] for c in fu['candidates']]
_main = {l['position']: l for l in missing['MECHANICAL_BOARD']['lines']}
for c in fei['candidates']:
    m = _main[c['position']]
    assert c['gan'] == m['gan']
    assert c['zhi'] == m['zhi']
    assert c['qin'] == m['qin']
    assert c['state'] == m['state']
    assert c['void'] == m['void']
    assert c['month_break'] == m['month_break']
    assert c['day_break'] == m['day_break']
    assert c['is_moving'] == m['is_moving']
    assert c['fushen_position'] == c['position']
    assert set(c.keys()) == {
        'position', 'gan', 'zhi', 'wx', 'qin', 'state', 'void',
        'month_break', 'day_break', 'is_moving', 'fushen_position',
    }
assert '飞神 = 主卦上承载伏神的那个爻' in fei['position_source']

# --- I: no fushen/feishen good-bad judgment vocabulary anywhere in the placement ---
_JUDGMENT_WORDS = ('得出', '旺相有力', '吉', '凶', '应期', '压制', '生扶伏神', 'EFFECTIVE', 'AUSPICIOUS', 'STRONG')
_blob = json.dumps({'fu': fu, 'fei': fei}, ensure_ascii=False)
for w in _JUDGMENT_WORDS:
    assert w not in _blob, f'judgment vocabulary leaked into placement: {w}'
assert missing['AUTOMATION_BOUNDARY'] == 'STOPS_AT_MECHANICAL_FUSHEN_FEISHEN_PLACEMENT'
for deferred in ('伏神得出判断', '飞神生克伏神 judgment', '日月生扶伏神 judgment', '伏神旺衰', '吉凶', '应期', 'prediction', 'blind validation'):
    assert deferred in missing['DEFERRED_NOT_IMPLEMENTED']
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
# rule trace must mention both sources and the Johnson-native placement chain
assert any('YINYO_L1' in x for x in res['rule_trace'])
assert any('JOHNSON_FUSHEN_DEF' in x for x in res['rule_trace'])
assert any('NO_FABRICATION' in x for x in res['rule_trace'])
# wording must stay factual: main lines are NOT globally relabeled as feishen
for tr in res['rule_trace']:
    if 'check main (fei)' in tr.lower():
        raise AssertionError(f"rule_trace still claims main as feishen: {tr}")
assert any('VISIBLE_MAIN_LINES_ALREADY_CHECKED' in x for x in res['rule_trace'])
assert any('CHANGED_LINES_CHECK' in x for x in res['rule_trace'])
assert any('JOHNSON_PURE_PALACE_DERIVATION' in x for x in res['rule_trace'])
assert any('JOHNSON_PURE_PALACE_BOARD' in x for x in res['rule_trace'])
assert any('FUSHEN_POSITION_COMPUTED' in x for x in res['rule_trace'])
assert any('FEISHEN_POSITION_IDENTIFIED' in x for x in res['rule_trace'])
assert any('AUTOMATION_STOPS_AT_PLACEMENT' in x for x in res['rule_trace'])
# the placement branch must no longer claim the old not-computed wording
assert not any('FUSHEN_POSITION_NOT_COMPUTED' in x for x in res['rule_trace'])
assert 'FUSHEN_POSITION_COMPUTED' in res['automation_boundary']
assert 'FEISHEN_POSITION_IDENTIFIED' in res['automation_boundary']
assert 'STOP_AFTER_MECHANICAL_PLACEMENT' in res['automation_boundary']
assert 'DEFERRED=' in res['automation_boundary']
assert 'MECHANICAL_FACT' in res['mechanical_vs_method_vs_judgment']
assert 'METHOD_RULE' in res['mechanical_vs_method_vs_judgment']
assert 'INTERPRETIVE_JUDGMENT=NONE' in res['mechanical_vs_method_vs_judgment']
assert 'FUSHEN_PLACEMENT_IDENTIFIED != FUSHEN_EFFECTIVE' in res['mechanical_vs_method_vs_judgment']
assert 'FEISHEN_POSITION_IDENTIFIED != FEISHEN_SUPPRESSES_FUSHEN' in res['mechanical_vs_method_vs_judgment']

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

# the previously terminal FUSHEN_LOOKUP_REQUIRED now advances to placement
assert missing['LENSES'][0]['status'] == 'VISIBLE_YONGSHEN_MISSING'
assert missing['LENSES'][0]['missing_yongshen_resolution']['status'] == 'FUSHEN_PLACEMENT_IDENTIFIED'
assert missing['LENSES'][0]['missing_yongshen_resolution']['gate_status_before_placement'] == 'FUSHEN_LOOKUP_REQUIRED'

# upstream integrity
assert fixture['ENGINE_PIN'] == JOHNSON_PIN
assert fixture['YINYO_PIN'] == YINYO_PIN
assert missing['ENGINE_PIN'] == JOHNSON_PIN
assert missing['YINYO_PIN'] == YINYO_PIN

# visible case regression: fingerprint unchanged from known canonical
assert fixture['BOARD_FINGERPRINT_SHA256'] == '7708076da186d63f5730b2b41054316f7dbf94801da331ef52af20acb1befcf6'

# =====================================================================
# JOHNSON-NATIVE FUSHEN PLACEMENT — STRUCTURAL PROOFS
# =====================================================================

# --- E (general): every palace head is uniquely derivable from Johnson HEXAGRAMS ---
# Cross-checked against Johnson's own find_hexagram() alias route, so the expected
# name comes from Johnson twice rather than from a hand-written map in this test.
EXPECTED_PALACES = ('乾', '兑', '离', '震', '巽', '坎', '艮', '坤')
# mod's import already put the pinned Johnson src on sys.path
from liuyao.data import find_hexagram as _johnson_find_hexagram  # noqa: E402
for _p in EXPECTED_PALACES:
    _rec, _proof = mod._pure_palace_record(_p)
    assert _rec is not None, f'palace head not derivable for {_p}'
    assert _proof['unique'] is True and _proof['hit_count'] == 1
    assert _proof['records_scanned'] == 64
    assert _proof['handwritten_palace_map_used'] is False
    assert _rec['palace'] == _p == _rec['upper'] == _rec['lower']
    assert _rec['world'] == 6                      # 八纯卦 = 六世, per Johnson data
    assert _rec['name'] == _johnson_find_hexagram(_p)['name']   # Johnson agrees with itself
    # Johnson can build the pure board with the minimal legal moving input
    _b = mod.cast_board(_rec['name'], [], '寅', '甲子', None)
    assert _b.hexagram == _rec['name']
    assert _b.palace == _p
    assert _b.changed_hexagram == _rec['name']     # static board: no moving line
    assert _b.moving_lines == []
    assert len(_b.lines) == 6 and all(l.qin for l in _b.lines)

# --- fail closed: an underivable palace head must never be guessed ---
_bad, _badproof = mod._pure_palace_record('不存在的宫')
assert _bad is None
assert _badproof['unique'] is False and _badproof['hit_count'] == 0

_real_hexagrams = mod.HEXAGRAMS
_real_cast_board = mod.cast_board
_gate_board = mod.cast_board('地天泰', [1], '寅', '甲子', '父母')


def _assert_fail_closed_propagates(res, expected_status):
    """
    INTEGRATION-level proof (this is what was missing before).

    A non-None fail-closed helper packet is NOT success. This asserts the failure
    propagates correctly THROUGH _missing_yongshen_resolution(): the real source
    failure status is preserved and no successful-placement wording is emitted.
    Probes may simulate a source failure; production code stays Johnson-native.
    """
    # the ACTUAL failure status is preserved, never replaced by a success status
    assert res['status'] == expected_status
    assert res['status'] != 'FUSHEN_PLACEMENT_IDENTIFIED'
    assert res['gate_status_before_placement'] == 'FUSHEN_LOOKUP_REQUIRED'
    # required flags stay factual
    assert res['fushen_position_computed'] is False
    assert res['feishen_position_identified'] is False
    assert res['fabricated_fusheng_position'] is False
    # no position leaked from either helper
    assert res['fushen_placement']['candidates'] == []
    assert res['feishen_placement']['candidates'] == []

    blob = json.dumps({
        'trace': res['rule_trace'],
        'boundary': res['automation_boundary'],
        'classification': res['mechanical_vs_method_vs_judgment'],
    }, ensure_ascii=False)

    # NO success claim may appear anywhere in trace / boundary / classification
    for forbidden in (
        'FUSHEN_POSITION_COMPUTED',
        'FEISHEN_POSITION_IDENTIFIED',
        'STOP_AFTER_MECHANICAL_PLACEMENT',
        'PURE_PALACE_DERIVED_FROM_JOHNSON_HEXAGRAMS',
        'PURE_PALACE_BOARD_BUILT_BY_JOHNSON_CAST_BOARD',
        'JOHNSON_PURE_PALACE_DERIVATION',
        'JOHNSON_PURE_PALACE_BOARD',
    ):
        assert forbidden not in blob, f'fail-closed output still claims {forbidden}'

    # automation boundary must explicitly say fail closed and name the real failure
    ab = res['automation_boundary']
    assert 'PLACEMENT_FAIL_CLOSED' in ab
    assert 'FUSHEN_POSITION_NOT_COMPUTED' in ab
    assert 'FEISHEN_POSITION_NOT_IDENTIFIED' in ab
    assert f'FUSHEN_FAILURE_STATUS={expected_status}' in ab
    assert 'NO_PALACE_HEAD_OR_POSITION_GUESSED' in ab
    # rule trace carries the same real failure status, plus the no-guessing guarantee
    assert any('PLACEMENT_FAIL_CLOSED' in x and expected_status in x for x in res['rule_trace'])
    assert any('NO_GUESSING' in x for x in res['rule_trace'])
    assert any('NO_FABRICATION' in x for x in res['rule_trace'])

    # judgment remains NONE and the slice still stops at placement
    assert 'INTERPRETIVE_JUDGMENT=NONE' in res['mechanical_vs_method_vs_judgment']
    assert res['fushen_effectiveness'] == 'NOT_ASSESSED'
    assert res['good_bad_judgment'] == 'NOT_EMITTED'
    assert res['fushen_placement']['judgment_emitted'] is False
    assert res['feishen_placement']['judgment_emitted'] is False



# (1) ambiguous palace head -> SOURCE_DATA_INCONSISTENT_PURE_PALACE, no candidates
try:
    _dup = dict(_real_hexagrams)
    _dup['坤为地#shadow'] = {
        'name': '坤为地#shadow', 'alias': '坤#shadow',
        'upper': '坤', 'lower': '坤', 'palace': '坤', 'palace_wx': '土', 'world': 6,
    }
    mod.HEXAGRAMS = _dup
    _amb, _ambproof = mod._pure_palace_record('坤')
    assert _amb is None and _ambproof['unique'] is False and _ambproof['hit_count'] == 2
    _r = mod._fushen_placement(_gate_board, '父母')
    assert _r['status'] == 'SOURCE_DATA_INCONSISTENT_PURE_PALACE'
    assert _r['fail_closed'] is True
    assert _r['candidates'] == [] and _r['candidate_count'] == 0
    assert _r['pure_palace_hexagram'] is None
    assert _r['pure_palace_board_built'] is False
    assert _r['judgment_emitted'] is False
    assert mod._feishen_placement(_gate_board, _r)['status'] == 'FEISHEN_POSITION_NOT_IDENTIFIED'
    _assert_fail_closed_propagates(
        mod._missing_yongshen_resolution(_gate_board, '父母'),
        'SOURCE_DATA_INCONSISTENT_PURE_PALACE',
    )
finally:
    mod.HEXAGRAMS = _real_hexagrams

# (2) Johnson rejects the pure-palace cast -> SOURCE_DATA_INCONSISTENT_PURE_PALACE_BOARD
def _rejecting_cast_board(*a, **k):
    raise ValueError('probe: engine rejected pure palace')


try:
    mod.cast_board = _rejecting_cast_board
    _r = mod._fushen_placement(_gate_board, '父母')
    assert _r['status'] == 'SOURCE_DATA_INCONSISTENT_PURE_PALACE_BOARD'
    assert _r['fail_closed'] is True
    assert _r['pure_palace_hexagram'] == '坤为地'   # head was still uniquely derived
    assert _r['pure_palace_board_built'] is False
    assert _r['candidates'] == [] and _r['candidate_count'] == 0
    assert _r['position_source'].startswith('NONE_JOHNSON_CAST_BOARD_REJECTED_PURE_PALACE')
    assert mod._feishen_placement(_gate_board, _r)['status'] == 'FEISHEN_POSITION_NOT_IDENTIFIED'
    _assert_fail_closed_propagates(
        mod._missing_yongshen_resolution(_gate_board, '父母'),
        'SOURCE_DATA_INCONSISTENT_PURE_PALACE_BOARD',
    )
finally:
    mod.cast_board = _real_cast_board


# (3) requested qin absent from the pure board -> SOURCE_DATA_INCONSISTENT_NO_FUSHEN_CANDIDATE
# Unreachable at this pin (all 6 pure boards carry every qin), probed with a stub board.
class _StubLine:
    def __init__(self, position, qin):
        self.position, self.qin = position, qin


class _StubBoard:
    def __init__(self, base):
        self.palace, self.month_zhi, self.day_gz = base.palace, base.month_zhi, base.day_gz
        self.hexagram = base.hexagram
        self.lines = [_StubLine(i, '官鬼') for i in range(1, 7)]


try:
    mod.cast_board = lambda *a, **k: _StubBoard(_gate_board)
    _r = mod._fushen_placement(_gate_board, '父母')
    assert _r['status'] == 'SOURCE_DATA_INCONSISTENT_NO_FUSHEN_CANDIDATE'
    assert _r['fail_closed'] is True
    assert _r['pure_palace_board_built'] is True
    assert _r['candidates'] == [] and _r['candidate_count'] == 0
    assert _r['pure_palace_board_qin'] == ['官鬼'] * 6
    assert _r['position_source'] == 'NONE_REQUESTED_QIN_ABSENT_FROM_JOHNSON_PURE_PALACE_BOARD'
    assert mod._feishen_placement(_gate_board, _r)['status'] == 'FEISHEN_POSITION_NOT_IDENTIFIED'
    _assert_fail_closed_propagates(
        mod._missing_yongshen_resolution(_gate_board, '父母'),
        'SOURCE_DATA_INCONSISTENT_NO_FUSHEN_CANDIDATE',
    )
finally:
    mod.cast_board = _real_cast_board

# restored: the real gate still places normally after the fail-closed probes
# restored: the real gate still places normally after the fail-closed probes
assert mod._fushen_placement(_gate_board, '父母')['status'] == 'FUSHEN_PLACEMENT_IDENTIFIED'

# --- INTEGRATION: success wording appears ONLY on the genuine success path ---
_ok = mod._missing_yongshen_resolution(_gate_board, '父母')
assert _ok['status'] == 'FUSHEN_PLACEMENT_IDENTIFIED'
assert _ok['fushen_position_computed'] is True
assert _ok['feishen_position_identified'] is True
assert any('FUSHEN_POSITION_COMPUTED' in x for x in _ok['rule_trace'])
assert any('FEISHEN_POSITION_IDENTIFIED' in x for x in _ok['rule_trace'])
assert 'STOP_AFTER_MECHANICAL_PLACEMENT' in _ok['automation_boundary']
assert 'PLACEMENT_FAIL_CLOSED' not in _ok['automation_boundary']
assert _ok['fushen_placement']['candidate_count'] >= 1
assert _ok['feishen_placement']['candidate_count'] == _ok['fushen_placement']['candidate_count']

# --- multi-candidate path: ALL candidates preserved, none arbitrarily selected ---
# Verified over Johnson's full space (64 hexagrams x all moving subsets x 5 lenses):
# 1728 gate-reachable lookups, every one single-candidate, zero multi-candidate and
# zero zero-candidate. So this path is exercised by a direct function probe on a lens
# the palace head carries twice (坤为地 -> 兄弟 at positions 1 and 4), not by a
# fabricated board. No gate-reachable multi-candidate case exists at this pin.
_probe_board = mod.cast_board('地天泰', [1], '寅', '甲子', None)
assert _probe_board.palace == '坤'
_multi = mod._fushen_placement(_probe_board, '兄弟')
assert _multi['status'] == 'FUSHEN_PLACEMENT_IDENTIFIED'
assert _multi['pure_palace_hexagram'] == '坤为地'
assert _multi['candidate_count'] == 2
assert [c['position'] for c in _multi['candidates']] == [1, 4]
assert _multi['all_candidates_preserved'] is True
assert _multi['arbitrary_selection_made'] is False
_multi_fei = mod._feishen_placement(_probe_board, _multi)
assert _multi_fei['status'] == 'FEISHEN_POSITION_IDENTIFIED'
assert [c['position'] for c in _multi_fei['candidates']] == [1, 4]
assert _multi_fei['all_main_lines_called_feishen'] is False

# --- feishen is NOT identified unless a fushen position was established ---
_no_fei = mod._feishen_placement(_probe_board, {'status': 'SOURCE_DATA_INCONSISTENT_NO_FUSHEN_CANDIDATE', 'candidates': []})
assert _no_fei['status'] == 'FEISHEN_POSITION_NOT_IDENTIFIED'
assert _no_fei['candidate_count'] == 0
assert _no_fei['judgment_emitted'] is False

# --- B/C: DAY_MONTH and BIAN branches never invoke palace-head lookup ---
for _res in (
    daymonth_case['LENSES'][0]['missing_yongshen_resolution'],
    bian_case['LENSES'][0]['missing_yongshen_resolution'],
):
    assert _res['fushen_placement'] is None
    assert _res['feishen_placement'] is None
    assert _res['gate_status_before_placement'] is None
    assert _res['fushen_position_computed'] is False
    assert _res['feishen_position_identified'] is False
    assert _res['fabricated_fusheng_position'] is False
    # their pre-existing wording is untouched by this slice
    assert 'FUSHEN_POSITION_NOT_COMPUTED' in _res['automation_boundary']
    assert 'FEISHEN_POSITION_NOT_IDENTIFIED' in _res['automation_boundary']
    assert 'RETURN_FUSHEN_LOOKUP_REQUIRED_IF_UNRESOLVED' in _res['automation_boundary']
    assert any('FUSHEN_POSITION_NOT_COMPUTED' in x for x in _res['rule_trace'])
    assert not any('JOHNSON_PURE_PALACE_DERIVATION' in x for x in _res['rule_trace'])

# --- A/J: visible-yongshen behaviour and the frozen main-board fingerprint ---
# Same board under a lens that resolves to placement and lenses that stay visible
# must share one identical mechanical fingerprint.
_mix = run([
    '--hexagram', '地天泰', '--moving', '1', '--month', '寅', '--day', '甲子',
    '--lenses', '父母,妻财,官鬼,兄弟,子孙',
])
assert _mix['BOARD_FINGERPRINT_SHA256'] == missing['BOARD_FINGERPRINT_SHA256']
assert _mix['INVARIANTS']['ONE_MECHANICAL_BOARD'] == 'YES'
assert _mix['INVARIANTS']['LENS_CHANGES_BOARD'] == 'NO'
assert _mix['MECHANICAL_BOARD'] == missing['MECHANICAL_BOARD']
_bylens = {x['lens']: x for x in _mix['LENSES']}
assert _bylens['父母']['status'] == 'VISIBLE_YONGSHEN_MISSING'
assert _bylens['父母']['missing_yongshen_resolution']['status'] == 'FUSHEN_PLACEMENT_IDENTIFIED'
for _L in ('妻财', '官鬼', '兄弟', '子孙'):
    assert _bylens[_L]['status'] == 'VISIBLE_YONGSHEN_FOUND'
    assert 'missing_yongshen_resolution' not in _bylens[_L], f'{_L} is visible; no missing gate'
# the placement lens does not perturb another lens' placement facts
assert _bylens['父母']['missing_yongshen_resolution']['fushen_placement']['candidates'] == \
    res['fushen_placement']['candidates']

# --- K: pins unchanged ---
assert _mix['ENGINE_PIN'] == JOHNSON_PIN
assert _mix['YINYO_PIN'] == YINYO_PIN
assert mod.PIN == JOHNSON_PIN
assert mod.YINYO_PIN == YINYO_PIN
assert _mix['FUSHEN_PLACEMENT_SOURCE']['PIN'] == JOHNSON_PIN
assert _mix['FUSHEN_PLACEMENT_SOURCE']['HARDCODED_PALACE_MAP'] == 'NO'
assert _mix['FUSHEN_PLACEMENT_SOURCE']['MANUAL_NAJIA'] == 'NO'
assert _mix['FUSHEN_PLACEMENT_SOURCE']['MANUAL_LIUQIN'] == 'NO'
assert _mix['FUSHEN_PLACEMENT_SOURCE']['SEPARATE_FUSHEN_DOCTRINE'] == 'NO'

print('LIUYAO_MULTI_READ_TEST=PASS')
print('MISSING_YONGSHEN_GATE=PASS')
print('OUTER_STATUS_CONTRADICTION_FIXED=YES')
print('JOHNSON_NATIVE_FUSHEN_PLACEMENT=PASS')
print('REAL_MISSING_CASE=地天泰|1|寅|甲子|父母|FUSHEN_LOOKUP_REQUIRED->FUSHEN_PLACEMENT_IDENTIFIED')
print('FUSHEN_STOPS_AT_PLACEMENT=YES')
print('GOOD_BAD_JUDGMENT=NOT_EMITTED')
