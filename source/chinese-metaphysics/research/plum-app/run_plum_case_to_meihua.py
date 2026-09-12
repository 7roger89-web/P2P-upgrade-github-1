#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PLUM_APP_PIN = '5965bdc8e9ca69a3cc7e96be6f1cc585d5032814'
SCRIPT_DIR = Path(__file__).resolve().parent
PLUM_UPSTREAM = (SCRIPT_DIR / '../../upstreams/plum-app').resolve()
MEIHUA_BRIDGE = SCRIPT_DIR.parent / 'meihua-divination-skill' / 'run_normalized_meihua_case.py'

TRIGRAM_NAME_TO_NUM = {
    '乾': 1,
    '兑': 2, '兌': 2,
    '离': 3, '離': 3,
    '震': 4,
    '巽': 5,
    '坎': 6,
    '艮': 7,
    '坤': 8,
}
NATURE_TO_NUM = {
    '天': 1,
    '泽': 2, '澤': 2,
    '火': 3,
    '雷': 4,
    '风': 5, '風': 5,
    '水': 6,
    '山': 7,
    '地': 8,
}
NUM_TO_FYRGO_NAME = {1: '乾', 2: '兑', 3: '离', 4: '震', 5: '巽', 6: '坎', 7: '艮', 8: '坤'}


def fail(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def verify_plum_pin():
    if not PLUM_UPSTREAM.exists():
        fail(f'Pinned plum-app upstream missing: {PLUM_UPSTREAM}')
    try:
        head = subprocess.check_output(['git', '-C', str(PLUM_UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip()
    except Exception:
        fail(f'Cannot verify pinned plum-app upstream: {PLUM_UPSTREAM}')
    if head != PLUM_APP_PIN:
        fail(f'Pinned plum-app SHA mismatch: expected {PLUM_APP_PIN}, got {head}')


def parse_hexagram_name(value: str):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('hexagram name must be a non-empty string')
    name = value.strip()
    if len(name) < 2:
        raise ValueError(f'cannot parse hexagram name: {name}')

    # plum-app explicitly treats the eight pure hexagrams specially because
    # their display names are 乾为天 / 兑为泽 / ... rather than two nature chars.
    if len(name) >= 3 and name[1] in ('为', '為'):
        num = TRIGRAM_NAME_TO_NUM.get(name[0])
        if num is None:
            raise ValueError(f'unknown pure-hexagram trigram: {name}')
        return num, num

    upper = NATURE_TO_NUM.get(name[0])
    lower = NATURE_TO_NUM.get(name[1])
    if upper is None or lower is None:
        raise ValueError(f'cannot derive upper/lower trigrams from hexagram name: {name}')
    return upper, lower


def load_case(path: str):
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as exc:
        fail(f'Cannot read plum-app case JSON: {exc}', 1)
    if not isinstance(payload, dict):
        fail('plum-app case input must be a JSON object', 1)
    problem = payload.get('problem')
    if not isinstance(problem, str) or not problem.strip():
        fail('plum-app case field problem is required', 1)
    shift = payload.get('shift_yao')
    if not isinstance(shift, int) or not 1 <= shift <= 6:
        fail('plum-app case field shift_yao must be integer 1..6', 1)
    try:
        pair = parse_hexagram_name(payload.get('origin_trigram'))
    except ValueError as exc:
        fail(f'Invalid plum-app origin_trigram: {exc}', 1)
    return payload, pair


def run_bridge(case_payload, pair):
    outside = case_payload.get('outside_react')
    if outside is None or outside == '':
        signs = []
    elif isinstance(outside, str):
        signs = [outside]
    else:
        fail('plum-app case outside_react must be a string when present', 1)

    bridge_input = {
        'question_context': case_payload['problem'].strip(),
        'upper_trigram': NUM_TO_FYRGO_NAME[pair[0]],
        'lower_trigram': NUM_TO_FYRGO_NAME[pair[1]],
        'moving_line': case_payload['shift_yao'],
        'month_branch': '',
        'day_branch': '',
        'external_signs': signs,
        'notes': 'transported from pinned plum-app case record; time branches are not inferred from free-text fields',
    }

    tmp = tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.json', delete=False)
    try:
        with tmp:
            json.dump(bridge_input, tmp, ensure_ascii=False)
        r = subprocess.run(
            [sys.executable, str(MEIHUA_BRIDGE), '--input', tmp.name],
            capture_output=True,
            text=True,
        )
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    if r.returncode:
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        fail('Meihua normalized-case bridge rejected transported plum-app case', r.returncode)
    try:
        return bridge_input, json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        fail(f'Meihua bridge emitted invalid JSON: {exc}', 1)


def pair_from_output(name, label):
    try:
        return parse_hexagram_name(name)
    except ValueError as exc:
        fail(f'Cannot verify {label}: {exc}', 1)


def optional_case_consistency(case_payload, field, actual_name):
    expected = case_payload.get(field)
    if expected is None or expected == '':
        return 'NOT_PROVIDED'
    try:
        expected_pair = parse_hexagram_name(expected)
    except ValueError as exc:
        fail(f'Invalid plum-app {field}: {exc}', 1)
    actual_pair = pair_from_output(actual_name, field)
    if expected_pair != actual_pair:
        fail(f'plum-app {field} disagrees with pinned analyzer: stored={expected}, computed={actual_name}', 1)
    return 'MATCHED_PINNED_ANALYZER'


def engine_fact_fingerprint(packet):
    stable = {
        'main': packet['MAIN_HEXAGRAM'],
        'mutual': packet['MUTUAL_HEXAGRAM'],
        'changed': packet['CHANGED_HEXAGRAM'],
        'moving_line': packet['MOVING_LINE'],
        'body_use': packet['BODY_USE'],
    }
    raw = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True, help='JSON record shaped like pinned plum-app d_case fields')
    a = p.parse_args()

    verify_plum_pin()
    case_payload, origin_pair = load_case(a.input)
    bridge_input, packet = run_bridge(case_payload, origin_pair)

    computed_origin_pair = pair_from_output(packet['MAIN_HEXAGRAM'], 'MAIN_HEXAGRAM')
    if origin_pair != computed_origin_pair:
        fail(
            f'plum-app origin_trigram disagrees with pinned analyzer: stored={case_payload["origin_trigram"]}, computed={packet["MAIN_HEXAGRAM"]}',
            1,
        )

    mid_status = optional_case_consistency(case_payload, 'mid_trigram', packet['MUTUAL_HEXAGRAM'])
    final_status = optional_case_consistency(case_payload, 'final_trigram', packet['CHANGED_HEXAGRAM'])

    hindsight_fields = ['prediction', 'result', 'correct', 'rethink']
    hindsight_present = [k for k in hindsight_fields if case_payload.get(k) not in (None, '')]

    out = {
        'DOMAIN': 'MEIHUA_YISHU',
        'CAPABILITY': 'PLUM_APP_CASE_TO_PINNED_MEIHUA_PIPELINE',
        'PLUM_APP_PIN': PLUM_APP_PIN,
        'SOURCE_CASE_FACTS': {
            'problem': case_payload['problem'],
            'origin_trigram': case_payload['origin_trigram'],
            'mid_trigram': case_payload.get('mid_trigram'),
            'final_trigram': case_payload.get('final_trigram'),
            'shift_yao': case_payload['shift_yao'],
            'd_time': case_payload.get('d_time'),
            'gz_time': case_payload.get('gz_time'),
            'solarTerm': case_payload.get('solarTerm'),
            'category': case_payload.get('category'),
            'outside_react': case_payload.get('outside_react'),
        },
        'ENGINE_INPUT': bridge_input,
        'ANALYSIS_PACKET': packet,
        'ENGINE_FACT_FINGERPRINT': engine_fact_fingerprint(packet),
        'CASE_INTEGRITY': {
            'origin_trigram': 'MATCHED_PINNED_ANALYZER',
            'mid_trigram': mid_status,
            'final_trigram': final_status,
        },
        'HINDSIGHT_FIELDS_PRESENT': hindsight_present,
        'HINDSIGHT_ISOLATION': 'prediction/result/correct/rethink are excluded from engine input and engine fingerprint',
        'TIME_CONTEXT_POLICY': 'd_time/gz_time/solarTerm are preserved as source facts but not parsed into month/day branches in this slice',
        'FINAL_PREDICTION': 'NOT_EMITTED',
        'PREDICTIVE_STATUS': 'NOT_TESTED',
        'NONCLAIMS': [
            'NO_DATABASE_OR_UI',
            'NO_HINDSIGHT_FIELD_FEEDBACK_INTO_ENGINE',
            'NO_FREE_TEXT_TIME_INFERENCE',
            'NO_PREDICTIVE_ACCURACY_CLAIM',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
