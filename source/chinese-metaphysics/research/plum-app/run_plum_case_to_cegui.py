#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from run_plum_case_to_meihua import load_case, verify_plum_pin

SCRIPT_DIR = Path(__file__).resolve().parent
CEGUI_RUNNER = SCRIPT_DIR.parent / 'plum-cg' / 'run_cegui_capability.mjs'


def fail(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def run_cegui(format_string: str):
    # Pinned plum-app UI calls getTrigramFromCFigure/GFigure without mode,
    # which is plum-cg's documented method 2: 策五艮，轨五坤. Select that
    # explicitly so the adapter preserves product behavior without hiding the
    # convention choice.
    r = subprocess.run(
        [
            'node',
            str(CEGUI_RUNNER),
            '--format-string',
            format_string,
            '--five-method',
            'method2',
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        fail('Pinned CEGUI adapter rejected transported plum-app case', r.returncode)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        fail(f'CEGUI adapter emitted invalid JSON: {exc}', 1)


def cegui_fact_fingerprint(packet):
    stable = {
        'format_string': packet['INPUT']['format_string'],
        'original_ce': packet['ORIGINAL_CE'],
        'ce_number': packet['CE_NUMBER'],
        'original_gui': packet['ORIGINAL_GUI'],
        'gui_number': packet['GUI_NUMBER'],
        'number_5_method': packet['NUMBER_5_CONVENTION']['SELECTED']['METHOD_ID'],
        'ce_trigrams': packet['NUMBER_5_CONVENTION']['SELECTED']['CE_TRIGRAMS'],
        'gui_trigrams': packet['NUMBER_5_CONVENTION']['SELECTED']['GUI_TRIGRAMS'],
    }
    raw = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True, help='JSON record shaped like pinned plum-app d_case fields')
    a = p.parse_args()

    verify_plum_pin()
    case_payload, (upper_num, lower_num) = load_case(a.input)
    format_string = f'{upper_num}{lower_num}{case_payload["shift_yao"]}'
    packet = run_cegui(format_string)

    if packet['INPUT']['format_string'] != format_string:
        fail('CEGUI format-string transport mismatch', 1)
    selected = packet['NUMBER_5_CONVENTION']['SELECTED']
    if not selected or selected['METHOD_ID'] != 'METHOD_2_CE5_GEN_GUI5_KUN':
        fail('CEGUI product convention drift: expected explicit method2', 1)

    hindsight_fields = ['prediction', 'result', 'correct', 'rethink']
    hindsight_present = [k for k in hindsight_fields if case_payload.get(k) not in (None, '')]

    out = {
        'DOMAIN': 'CEGUI',
        'CAPABILITY': 'PLUM_APP_CASE_TO_PINNED_CE​GUI_PIPELINE'.replace('\u200b', ''),
        'SOURCE_CASE_FACTS': {
            'problem': case_payload['problem'],
            'origin_trigram': case_payload['origin_trigram'],
            'shift_yao': case_payload['shift_yao'],
            'category': case_payload.get('category'),
            'd_time': case_payload.get('d_time'),
            'gz_time': case_payload.get('gz_time'),
        },
        'TRANSPORT': {
            'upper_preheaven_number': upper_num,
            'lower_preheaven_number': lower_num,
            'moving_line': case_payload['shift_yao'],
            'format_string': format_string,
            'formula': 'upper_pre_num + lower_pre_num + shift_yao',
            'source_behavior': 'pinned plum-app TableBody.vue',
        },
        'CEGUI_PACKET': packet,
        'CEGUI_FACT_FINGERPRINT': cegui_fact_fingerprint(packet),
        'PRODUCT_NUMBER_5_CONVENTION': 'METHOD_2_CE5_GEN_GUI5_KUN',
        'PRODUCT_CONVENTION_REASON': 'pinned plum-app calls plum-cg mapping functions without mode; adapter selects the equivalent method2 explicitly',
        'HINDSIGHT_FIELDS_PRESENT': hindsight_present,
        'HINDSIGHT_ISOLATION': 'prediction/result/correct/rethink are excluded from CEGUI input and CEGUI fingerprint',
        'FINAL_PREDICTION': 'NOT_EMITTED',
        'PREDICTIVE_STATUS': 'NOT_APPLICABLE_NOT_TESTED',
        'NONCLAIMS': [
            'NO_HISTORICAL_NUMBER_5_METHOD_WINNER',
            'NO_HINDSIGHT_FIELD_FEEDBACK_INTO_ENGINE',
            'NO_FREE_TEXT_GANZHI_INFERENCE',
            'NO_DATABASE_OR_UI',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
