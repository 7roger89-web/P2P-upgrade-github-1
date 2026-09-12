#!/usr/bin/env python3
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

PIN = '8a9a5e0f482dd225bfe4a1c52c2ae5546228607a'
SCRIPT_DIR = Path(__file__).resolve().parent
UPSTREAM = (SCRIPT_DIR / '../../upstreams/meihua-yishu').resolve()


def fail(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


if not UPSTREAM.exists():
    fail(f'Pinned upstream missing: {UPSTREAM}')
try:
    head = subprocess.check_output(['git', '-C', str(UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip()
except Exception:
    fail(f'Cannot verify pinned upstream: {UPSTREAM}')
if head != PIN:
    fail(f'Pinned upstream SHA mismatch: expected {PIN}, got {head}')

module_path = UPSTREAM / 'scripts/meihua_calc.py'
spec = importlib.util.spec_from_file_location('pinned_meihua_calc', module_path)
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)


def simp(s):
    return str(s).replace('澤', '泽').replace('變', '变').replace('體', '体')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixture')
    p.add_argument('--lunar-year', type=int)
    p.add_argument('--month', type=int)
    p.add_argument('--day', type=int)
    p.add_argument('--hour', type=int)
    p.add_argument('--numbers', nargs='+', type=int)
    a = p.parse_args()

    time_custom = any(x is not None for x in [a.lunar_year, a.month, a.day, a.hour])
    number_custom = a.numbers is not None
    selected_modes = int(bool(a.fixture)) + int(time_custom) + int(number_custom)
    if selected_modes != 1:
        fail('Choose exactly one: --fixture guanmei, lunar time arguments, or --numbers N1 N2 [N3]')

    if a.fixture:
        if a.fixture != 'guanmei':
            fail(f'Unknown fixture: {a.fixture}')
        year_num, month, day, shichen = 5, 12, 17, 9
        upper_sum = year_num + month + day
        lower_sum = upper_sum + shichen
        moving_sum = lower_sum
        upper = mc.num_to_gua(upper_sum)
        lower = mc.num_to_gua(lower_sum)
        moving = mc.num_to_yao(moving_sum)
        result = mc._analyze_hexagram(upper, lower, moving, None)
        input_mode = 'FIXTURE'
        casting_mode = 'TRADITIONAL_TIME_CASTING'
        input_packet = {'year_branch_number': 5, 'month': 12, 'day': 17, 'shichen_number': 9}
        arithmetic = {'upper_total': upper_sum, 'lower_total': lower_sum, 'moving_total': moving_sum}
        rule_trace = [
            'MEIHUA_TRADITIONAL_TIME_CAST',
            'MEIHUA_TI_YONG_MOVING_TRIGRAM_AS_USE',
            'MEIHUA_WUXING_SHENG_KE',
        ]
    elif number_custom:
        if len(a.numbers) not in (2, 3):
            fail('Number casting usage: --numbers N1 N2 [N3]')
        try:
            result = mc.qigua_by_numbers(*a.numbers)
        except Exception as exc:
            fail(f'meihua-yishu rejected number input: {exc}', 1)
        moving = result['本卦']['動爻位']
        input_mode = 'CUSTOM'
        casting_mode = 'NUMBER_CASTING'
        input_packet = {'numbers': a.numbers}
        arithmetic = result.get('計算過程', {})
        rule_trace = [
            'MEIHUA_NUMBER_CAST_UPPER_LOWER',
            'MEIHUA_NUMBER_CAST_MOVING_FROM_TOTAL',
            'MEIHUA_TI_YONG_MOVING_TRIGRAM_AS_USE',
            'MEIHUA_WUXING_SHENG_KE',
        ]
    else:
        if None in [a.lunar_year, a.month, a.day, a.hour]:
            fail('Time casting usage: --lunar-year YYYY --month M --day D --hour 0..23')
        if not (1 <= a.month <= 12 and 1 <= a.day <= 30 and 0 <= a.hour <= 23):
            fail('Invalid lunar date/time range')
        try:
            result = mc.qigua_by_time(a.lunar_year, a.month, a.day, a.hour)
        except Exception as exc:
            fail(f'meihua-yishu rejected input: {exc}', 1)
        moving = result['本卦']['動爻位']
        input_mode = 'CUSTOM'
        casting_mode = 'TRADITIONAL_TIME_CASTING'
        input_packet = {
            'lunar_year': a.lunar_year,
            'month': a.month,
            'day': a.day,
            'hour': a.hour,
        }
        arithmetic = result.get('計算過程', {})
        rule_trace = [
            'MEIHUA_TRADITIONAL_TIME_CAST',
            'MEIHUA_TI_YONG_MOVING_TRIGRAM_AS_USE',
            'MEIHUA_WUXING_SHENG_KE',
        ]

    main_name = simp(result['本卦']['名稱'])
    changed_name = simp(result['變卦']['名稱'])
    relation = result['體用']['生克關係']

    if input_mode == 'FIXTURE':
        if (main_name, moving, changed_name) != ('泽火革', 1, '泽山咸'):
            fail(f'Classical fixture drift: {(main_name, moving, changed_name)}', 1)
        if not relation.startswith('用克體'):
            fail(f'Unexpected initial 体用 relation: {relation}', 1)
        structural = 'INITIAL_PRESSURE_WITH_LATER_SUPPORT'
    else:
        structural = 'TI_YONG_RELATION_REPORTED_ONLY'

    out = {
        'DOMAIN': 'MEIHUA_YISHU',
        'ENGINE_PIN': PIN,
        'INPUT_MODE': input_mode,
        'CASTING_MODE': casting_mode,
        'INPUT': input_packet,
        'ARITHMETIC': arithmetic,
        'UPPER_TRIGRAM': result['本卦']['上卦'],
        'LOWER_TRIGRAM': result['本卦']['下卦'],
        'MOVING_LINE': moving,
        'MAIN_HEXAGRAM': main_name,
        'MUTUAL_HEXAGRAM': simp(result['互卦']['名稱']),
        'CHANGED_HEXAGRAM': changed_name,
        'BODY_USE': result['體用'],
        'TI_YONG_RELATION': relation,
        'RULE_TRACE': rule_trace,
        'STRUCTURAL_OUTPUT': structural,
        'SEASON_CONTEXT_STATUS': 'PRESENT' if '卦氣旺衰' in result else 'ABSENT_NOT_INFERRED',
        'EXTERNAL_SIGN_STATUS': 'MISSING_DO_NOT_FABRICATE',
        'PROVENANCE_STATUS': 'CLASSICAL_TEXT_GROUNDED_SELECTED_SLICE',
        'PREDICTIVE_STATUS': 'NOT_ESTABLISHED_NEGATIVE_EVIDENCE_PRESERVED',
        'NONCLAIMS': [
            'NO_PERSONAL_FUTURE_PREDICTION',
            'NO_EXTERNAL_SIGN_INVENTION',
            'NO_CASTING_MODE_EQUIVALENCE_CLAIM',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
