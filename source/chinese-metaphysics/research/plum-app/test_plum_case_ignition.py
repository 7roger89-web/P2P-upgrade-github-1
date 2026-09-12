#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
IGNITION = HERE / 'run_plum_case_ignition.py'
MEIHUA = HERE / 'run_plum_case_to_meihua.py'
CEGUI = HERE / 'run_plum_case_to_cegui.py'


def write_case(payload):
    f = tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.json', delete=False)
    with f:
        json.dump(payload, f, ensure_ascii=False)
    return f.name


def run_script(script, path):
    r = subprocess.run([sys.executable, str(script), '--input', path], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    return json.loads(r.stdout)


def run_case(payload):
    path = write_case(payload)
    try:
        ignition = run_script(IGNITION, path)
        meihua = run_script(MEIHUA, path)
        cegui = run_script(CEGUI, path)
    finally:
        Path(path).unlink(missing_ok=True)
    return ignition, meihua, cegui


base = {
    'problem': 'one-key product case fixture',
    'origin_trigram': '泽火革',
    'mid_trigram': '',
    'final_trigram': '泽山咸',
    'shift_yao': 1,
    'd_time': 'fixture-time-preserved-only',
    'gz_time': 'fixture-ganzhi-not-parsed',
    'category': 1,
    'outside_react': '',
    'prediction': 'historical prediction excluded from mechanics',
    'result': 'historical outcome excluded from mechanics',
    'correct': 1,
    'rethink': 'retrospective note excluded from mechanics',
}

ignition, meihua, cegui = run_case(base)
assert ignition['PRODUCT_SHELL'] == 'PLUM_APP_CASE'
assert ignition['CAPABILITY'] == 'ONE_CASE_DUAL_ENGINE_IGNITION'
assert ignition['ASSEMBLY_STATUS'] == 'MECHANICAL_PIPELINES_READY'
assert ignition['SOURCE_CASE']['origin_trigram'] == '泽火革'
assert ignition['SOURCE_CASE']['shift_yao'] == 1
assert ignition['COMPONENTS']['MEIHUA']['ENGINE_FACT_FINGERPRINT'] == meihua['ENGINE_FACT_FINGERPRINT']
assert ignition['COMPONENTS']['CEGUI']['CEGUI_FACT_FINGERPRINT'] == cegui['CEGUI_FACT_FINGERPRINT']
assert ignition['COMPONENTS']['MEIHUA']['ANALYSIS_PACKET']['MAIN_HEXAGRAM'] == '泽火革'
assert ignition['COMPONENTS']['MEIHUA']['ANALYSIS_PACKET']['CHANGED_HEXAGRAM'] == '泽山咸'
assert ignition['COMPONENTS']['CEGUI']['TRANSPORT']['format_string'] == '231'
assert ignition['FINAL_PREDICTION'] == 'NOT_EMITTED'

changed = deepcopy(base)
changed['prediction'] = 'changed after reveal'
changed['result'] = 'changed outcome text'
changed['correct'] = 0
changed['rethink'] = 'changed retrospective explanation'
second, _, _ = run_case(changed)
assert second['ASSEMBLY_FINGERPRINT'] == ignition['ASSEMBLY_FINGERPRINT']
assert second['COMPONENTS']['MEIHUA']['ENGINE_FACT_FINGERPRINT'] == ignition['COMPONENTS']['MEIHUA']['ENGINE_FACT_FINGERPRINT']
assert second['COMPONENTS']['CEGUI']['CEGUI_FACT_FINGERPRINT'] == ignition['COMPONENTS']['CEGUI']['CEGUI_FACT_FINGERPRINT']

print('PLUM_APP_CASE_IGNITION_TEST=PASS')
