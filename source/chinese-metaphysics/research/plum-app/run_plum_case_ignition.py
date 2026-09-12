#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MEIHUA = SCRIPT_DIR / 'run_plum_case_to_meihua.py'
CEGUI = SCRIPT_DIR / 'run_plum_case_to_cegui.py'


def fail(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def run_json(script: Path, input_path: str):
    r = subprocess.run(
        [sys.executable, str(script), '--input', input_path],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        fail(f'Assembly component failed: {script.name}', r.returncode)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        fail(f'Assembly component emitted invalid JSON ({script.name}): {exc}', 1)


def assembly_fingerprint(meihua, cegui):
    stable = {
        'origin_trigram': meihua['SOURCE_CASE_FACTS']['origin_trigram'],
        'shift_yao': meihua['SOURCE_CASE_FACTS']['shift_yao'],
        'meihua_engine_fingerprint': meihua['ENGINE_FACT_FINGERPRINT'],
        'cegui_fact_fingerprint': cegui['CEGUI_FACT_FINGERPRINT'],
    }
    raw = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True, help='One plum-app-style case JSON record')
    a = p.parse_args()

    input_path = str(Path(a.input).resolve())
    meihua = run_json(MEIHUA, input_path)
    cegui = run_json(CEGUI, input_path)

    meihua_source = meihua['SOURCE_CASE_FACTS']
    cegui_source = cegui['SOURCE_CASE_FACTS']
    if meihua_source['origin_trigram'] != cegui_source['origin_trigram']:
        fail('Assembly source mismatch: origin_trigram differs between components', 1)
    if meihua_source['shift_yao'] != cegui_source['shift_yao']:
        fail('Assembly source mismatch: shift_yao differs between components', 1)

    hindsight_meihua = set(meihua.get('HINDSIGHT_FIELDS_PRESENT', []))
    hindsight_cegui = set(cegui.get('HINDSIGHT_FIELDS_PRESENT', []))
    if hindsight_meihua != hindsight_cegui:
        fail('Assembly hindsight metadata mismatch between components', 1)

    out = {
        'PRODUCT_SHELL': 'PLUM_APP_CASE',
        'CAPABILITY': 'ONE_CASE_DUAL_ENGINE_IGNITION',
        'SOURCE_CASE': {
            'problem': meihua_source['problem'],
            'origin_trigram': meihua_source['origin_trigram'],
            'shift_yao': meihua_source['shift_yao'],
        },
        'COMPONENTS': {
            'MEIHUA': meihua,
            'CEGUI': cegui,
        },
        'ASSEMBLY_FINGERPRINT': assembly_fingerprint(meihua, cegui),
        'HINDSIGHT_FIELDS_PRESENT': sorted(hindsight_meihua),
        'HINDSIGHT_ISOLATION': 'Both deterministic component fingerprints exclude prediction/result/correct/rethink',
        'ASSEMBLY_STATUS': 'MECHANICAL_PIPELINES_READY',
        'FINAL_PREDICTION': 'NOT_EMITTED',
        'PREDICTIVE_STATUS': 'NOT_ESTABLISHED',
        'NONCLAIMS': [
            'NO_CROSS_METHOD_SYNTHESIS',
            'NO_MAJORITY_VOTE',
            'NO_PREDICTIVE_ACCURACY_CLAIM',
            'NO_GENERIC_ROUTER_OR_PLUGIN_FRAMEWORK',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
