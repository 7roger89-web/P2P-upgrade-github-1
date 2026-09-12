#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / 'run_plum_case_to_cegui.py'
DIRECT = HERE.parent / 'plum-cg' / 'run_cegui_capability.mjs'


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


def run_direct(format_string):
    r = subprocess.run(
        ['node', str(DIRECT), '--format-string', format_string, '--five-method', 'method2'],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    return json.loads(r.stdout)


base = {
    'problem': 'product CEGUI assembly fixture',
    'origin_trigram': '泽火革',
    'mid_trigram': '',
    'final_trigram': '泽山咸',
    'shift_yao': 1,
    'd_time': 'fixture-time-preserved-only',
    'gz_time': 'fixture-ganzhi-not-parsed',
    'category': 1,
    'prediction': 'known prediction must stay outside mechanical input',
    'result': 'known result must stay outside mechanical input',
    'correct': 1,
    'rethink': 'retrospective explanation must stay outside mechanical input',
}

assembled = run_case(base)
direct = run_direct('231')
assert assembled['DOMAIN'] == 'CEGUI'
assert assembled['CAPABILITY'] == 'PLUM_APP_CASE_TO_PINNED_CEGUI_PIPELINE'
assert assembled['TRANSPORT']['upper_preheaven_number'] == 2
assert assembled['TRANSPORT']['lower_preheaven_number'] == 3
assert assembled['TRANSPORT']['moving_line'] == 1
assert assembled['TRANSPORT']['format_string'] == '231'
assert assembled['CEGUI_PACKET']['CE_NUMBER'] == direct['CE_NUMBER']
assert assembled['CEGUI_PACKET']['GUI_NUMBER'] == direct['GUI_NUMBER']
assert assembled['CEGUI_PACKET']['ORIGINAL_CE'] == direct['ORIGINAL_CE']
assert assembled['CEGUI_PACKET']['ORIGINAL_GUI'] == direct['ORIGINAL_GUI']
assert assembled['CEGUI_PACKET']['NUMBER_5_CONVENTION']['SELECTED'] == direct['NUMBER_5_CONVENTION']['SELECTED']
assert assembled['PRODUCT_NUMBER_5_CONVENTION'] == 'METHOD_2_CE5_GEN_GUI5_KUN'
assert assembled['FINAL_PREDICTION'] == 'NOT_EMITTED'

changed = deepcopy(base)
changed['prediction'] = 'different prediction after reveal'
changed['result'] = 'different outcome after reveal'
changed['correct'] = 0
changed['rethink'] = 'different retrospective rewrite'
second = run_case(changed)
assert second['CEGUI_FACT_FINGERPRINT'] == assembled['CEGUI_FACT_FINGERPRINT']
assert second['CEGUI_PACKET']['CE_NUMBER'] == assembled['CEGUI_PACKET']['CE_NUMBER']
assert second['CEGUI_PACKET']['GUI_NUMBER'] == assembled['CEGUI_PACKET']['GUI_NUMBER']

pure = deepcopy(base)
pure['origin_trigram'] = '乾为天'
pure['shift_yao'] = 6
pure_out = run_case(pure)
assert pure_out['TRANSPORT']['format_string'] == '116'

print('PLUM_APP_CASE_CEGUI_ASSEMBLY_TEST=PASS')
