#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / 'run_plum_case_to_meihua.py'


def write_case(payload):
    f = tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.json', delete=False)
    with f:
        json.dump(payload, f, ensure_ascii=False)
    return f.name


def run_case(payload):
    path = write_case(payload)
    try:
        r = subprocess.run([sys.executable, str(RUNNER), '--input', path], capture_output=True, text=True)
    finally:
        Path(path).unlink(missing_ok=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    return json.loads(r.stdout)


def run_fail(payload):
    path = write_case(payload)
    try:
        r = subprocess.run([sys.executable, str(RUNNER), '--input', path], capture_output=True, text=True)
    finally:
        Path(path).unlink(missing_ok=True)
    if r.returncode == 0:
        raise AssertionError('Expected failure but runner succeeded')
    return r


base = {
    'problem': 'product case assembly fixture',
    'origin_trigram': '泽火革',
    'mid_trigram': '',
    'final_trigram': '泽山咸',
    'shift_yao': 1,
    'd_time': 'fixture-time-preserved-only',
    'gz_time': 'fixture-ganzhi-not-parsed',
    'solarTerm': 'fixture-solar-term-not-parsed',
    'category': 1,
    'outside_react': '',
    'prediction': 'old prediction must not influence engine facts',
    'result': 'known outcome must not influence engine facts',
    'correct': 1,
    'rethink': 'post-outcome rethink must remain isolated',
}

first = run_case(base)
assert first['DOMAIN'] == 'MEIHUA_YISHU'
assert first['CAPABILITY'] == 'PLUM_APP_CASE_TO_PINNED_MEIHUA_PIPELINE'
assert first['ENGINE_INPUT']['upper_trigram'] == '兑'
assert first['ENGINE_INPUT']['lower_trigram'] == '离'
assert first['ENGINE_INPUT']['moving_line'] == 1
assert first['ANALYSIS_PACKET']['MAIN_HEXAGRAM'] == '泽火革'
assert first['ANALYSIS_PACKET']['CHANGED_HEXAGRAM'] == '泽山咸'
assert first['CASE_INTEGRITY']['origin_trigram'] == 'MATCHED_PINNED_ANALYZER'
assert first['CASE_INTEGRITY']['final_trigram'] == 'MATCHED_PINNED_ANALYZER'
assert set(first['HINDSIGHT_FIELDS_PRESENT']) == {'prediction', 'result', 'correct', 'rethink'}
assert first['FINAL_PREDICTION'] == 'NOT_EMITTED'

# Hindsight fields may change after reveal, but the deterministic engine facts
# must remain byte-equivalent at the declared fingerprint boundary.
changed_hindsight = deepcopy(base)
changed_hindsight['prediction'] = 'completely different old prediction'
changed_hindsight['result'] = 'completely different known outcome'
changed_hindsight['correct'] = 0
changed_hindsight['rethink'] = 'completely different retrospective explanation'
second = run_case(changed_hindsight)
assert second['ENGINE_FACT_FINGERPRINT'] == first['ENGINE_FACT_FINGERPRINT']
assert second['ANALYSIS_PACKET']['MAIN_HEXAGRAM'] == first['ANALYSIS_PACKET']['MAIN_HEXAGRAM']
assert second['ANALYSIS_PACKET']['CHANGED_HEXAGRAM'] == first['ANALYSIS_PACKET']['CHANGED_HEXAGRAM']

bad_final = deepcopy(base)
bad_final['final_trigram'] = '乾为天'
r = run_fail(bad_final)
assert 'final_trigram disagrees with pinned analyzer' in r.stderr

bad_origin = deepcopy(base)
bad_origin['origin_trigram'] = 'not-a-hexagram'
r = run_fail(bad_origin)
assert 'Invalid plum-app origin_trigram' in r.stderr

print('PLUM_APP_CASE_MEIHUA_ASSEMBLY_TEST=PASS')
