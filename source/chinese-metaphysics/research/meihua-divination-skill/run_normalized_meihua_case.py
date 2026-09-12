#!/usr/bin/env python3
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

NORMALIZER_PIN = 'd70d73ad620afe39d1555a0386680790cfd09227'
CALCULATOR_PIN = '8a9a5e0f482dd225bfe4a1c52c2ae5546228607a'
SCRIPT_DIR = Path(__file__).resolve().parent
NORMALIZER_UPSTREAM = (SCRIPT_DIR / '../../upstreams/meihua-divination-skill').resolve()
CALCULATOR_UPSTREAM = (SCRIPT_DIR / '../../upstreams/meihua-yishu').resolve()
NORMALIZER = NORMALIZER_UPSTREAM / 'scripts' / 'normalize_case_input.py'


def fail(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def verify_pin(path: Path, pin: str):
    if not path.exists():
        fail(f'Pinned upstream missing: {path}')
    try:
        head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    except Exception:
        fail(f'Cannot verify pinned upstream: {path}')
    if head != pin:
        fail(f'Pinned upstream SHA mismatch: expected {pin}, got {head}')


def load_calculator():
    module_path = CALCULATOR_UPSTREAM / 'scripts' / 'meihua_calc.py'
    spec = importlib.util.spec_from_file_location('pinned_meihua_calc_bridge', module_path)
    if spec is None or spec.loader is None:
        fail(f'Cannot load pinned calculator: {module_path}', 1)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_input(input_path: str):
    r = subprocess.run(
        [sys.executable, str(NORMALIZER), '--input', input_path, '--format', 'json'],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        fail(f'Normalizer emitted invalid JSON: {exc}', 1)


def simp(value):
    return str(value).replace('澤', '泽').replace('變', '变').replace('體', '体')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True, help='Structured case JSON accepted by pinned Fyrgo8 normalizer')
    a = p.parse_args()

    verify_pin(NORMALIZER_UPSTREAM, NORMALIZER_PIN)
    verify_pin(CALCULATOR_UPSTREAM, CALCULATOR_PIN)
    normalized = normalize_input(a.input)

    moving_lines = normalized['moving_lines']
    if len(moving_lines) != 1:
        fail(
            f'Current pinned Meihua analyzer bridge requires exactly one moving line; got {moving_lines}',
            1,
        )

    mc = load_calculator()
    month_branch = normalized['month_branch'] or None
    try:
        result = mc._analyze_hexagram(
            normalized['upper_trigram'],
            normalized['lower_trigram'],
            moving_lines[0],
            month_branch,
        )
    except Exception as exc:
        fail(f'Pinned meihua-yishu analyzer rejected normalized case: {exc}', 1)

    signs = normalized['external_signs']
    out = {
        'DOMAIN': 'MEIHUA_YISHU',
        'CAPABILITY': 'PINNED_NORMALIZED_CASE_TO_ANALYSIS_PACKET',
        'NORMALIZER_PIN': NORMALIZER_PIN,
        'CALCULATOR_PIN': CALCULATOR_PIN,
        'NORMALIZED_INPUT': normalized,
        'MAIN_HEXAGRAM': simp(result['本卦']['名稱']),
        'MUTUAL_HEXAGRAM': simp(result['互卦']['名稱']),
        'CHANGED_HEXAGRAM': simp(result['變卦']['名稱']),
        'MOVING_LINE': moving_lines[0],
        'BODY_USE': result['體用'],
        'SEASON_CONTEXT_STATUS': 'PRESENT' if month_branch else 'ABSENT_NOT_INFERRED',
        'EXTERNAL_SIGNS': signs,
        'EXTERNAL_SIGN_STATUS': 'PRESENT_NOT_INTERPRETED' if signs else 'MISSING_DO_NOT_FABRICATE',
        'TRANSPORT_BOUNDARY': 'FYRGO_NORMALIZES_INPUT__MUYEN_COMPUTES_HEXAGRAM_FACTS__NO_DOCTRINE_MERGE',
        'FINAL_PREDICTION': 'NOT_EMITTED',
        'PROVENANCE_STATUS': 'TWO_PIN_ENGINEERING_COMPOSITION__DOCTRINES_REMAIN_REPO_LOCAL',
        'PREDICTIVE_STATUS': 'NOT_TESTED',
        'NONCLAIMS': [
            'NO_MULTI_MOVING_LINE_SILENT_COERCION',
            'NO_EXTERNAL_SIGN_FABRICATION',
            'NO_CROSS_REPO_DOCTRINE_NORMALIZATION',
            'NO_PREDICTIVE_ACCURACY_CLAIM',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
