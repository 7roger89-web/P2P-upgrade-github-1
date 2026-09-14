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


# Reuse the already-proven Meihua -> Yi Jing name-bridge policy and the already
# wired Yi Jing runtime instead of re-deriving a text-normalization framework
# or a second bridge here.
try:
    sys.path.insert(0, str(SCRIPT_DIR.parent))
    import run_meihua_yijing_evidence as yijing_bridge  # noqa: E402
except Exception as exc:
    fail(f'Cannot load existing Meihua->Yi Jing bridge policy: {exc}', 1)

YIJING_RUNTIME = yijing_bridge.yijing_runtime
YIJING_RUNNER = yijing_bridge.YIJING_RUNNER
canonical_trigram = yijing_bridge.canonical_trigram
NAME_BRIDGE_POLICY = 'TRIGRAM_STRUCTURE_NOT_FULL_TRADITIONAL_SIMPLIFIED_TEXT_CONVERSION'


def run_json(command, label):
    r = subprocess.run(command, capture_output=True, text=True)
    if r.returncode:
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        fail(f'Assembly component failed: {label}', r.returncode)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        fail(f'Assembly component emitted invalid JSON ({label}): {exc}', 1)


def yijing_evidence_fingerprint(evidence):
    # Stable deterministic Yi Jing fields only. Retrospective plum-app fields
    # (prediction/result/correct/rethink) never reach the Yi Jing runtime input,
    # so they cannot reach this fingerprint.
    stable = {
        'normalized_main_hexagram': evidence['NORMALIZED_HEXAGRAM'],
        'selected_moving_line_evidence': evidence['SELECTED_YAO'],
        'changed_hexagram': evidence['CHANGED_HEXAGRAM'],
    }
    raw = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def build_yijing_component(meihua, hindsight_present):
    """Attach the existing source-grounded Yi Jing runtime to the already-computed
    Meihua structure.

    The canonical Yi Jing hexagram is selected from the Meihua normalized upper +
    lower trigram structure, never from hexagram display-name equality: Meihua
    display names can carry traditional variants (for example 天風姤) that the
    Yi Jing corpus spells differently (天风姤).
    """
    packet = meihua['ANALYSIS_PACKET']
    normalized = packet['NORMALIZED_INPUT']
    moving = packet['MOVING_LINE']

    upper_raw = normalized['upper_trigram']
    lower_raw = normalized['lower_trigram']
    upper = canonical_trigram(upper_raw)
    lower = canonical_trigram(lower_raw)
    if upper not in YIJING_RUNTIME.BAGUA or lower not in YIJING_RUNTIME.BAGUA:
        fail(f'Cannot bridge Meihua trigram structure into Yi Jing: upper={upper_raw!r}, lower={lower_raw!r}', 1)
    if not isinstance(moving, int) or not 1 <= moving <= 6:
        fail(f'Invalid Meihua moving line for Yi Jing bridge: {moving!r}', 1)

    canonical_main = YIJING_RUNTIME.HEXAGRAM_BY_TRIGRAMS.get((upper, lower))
    if not canonical_main:
        fail(f'No canonical Yi Jing hexagram for Meihua trigram structure: upper={upper}, lower={lower}', 1)

    evidence = run_json(
        [sys.executable, str(YIJING_RUNNER), '--hexagram', canonical_main, '--moving', str(moving)],
        'run_yijing_capability.py',
    )
    if evidence.get('DOMAIN') != 'YIJING':
        fail('Unexpected Yi Jing packet contract', 1)
    if evidence.get('NORMALIZED_HEXAGRAM') != canonical_main:
        fail(
            f'Yi Jing canonical bridge drift: expected {canonical_main}, '
            f'got {evidence.get("NORMALIZED_HEXAGRAM")}',
            1,
        )

    selected = evidence.get('SELECTED_YAO') or []
    if len(selected) != 1 or selected[0].get('position') != moving:
        fail(f'Yi Jing selected-line bridge drift for Meihua moving line {moving}', 1)
    if not selected[0].get('text'):
        fail(f'Yi Jing selected line is missing 爻 text evidence: {canonical_main} line {moving}', 1)
    if not selected[0].get('xiaoxiang'):
        fail(f'Yi Jing selected line is missing 小象 evidence: {canonical_main} line {moving}', 1)
    if not evidence.get('CHANGED_HEXAGRAM'):
        fail(f'Yi Jing changed-hexagram evidence missing for {canonical_main} line {moving}', 1)

    return {
        'DOMAIN': 'YIJING',
        'CAPABILITY': 'PLUM_APP_MEIHUA_STRUCTURE_TO_SOURCE_GROUNDED_YIJING_EVIDENCE',
        'BRIDGE': {
            'MEIHUA_UPPER_TRIGRAM_RAW': upper_raw,
            'MEIHUA_LOWER_TRIGRAM_RAW': lower_raw,
            'CANONICAL_UPPER_TRIGRAM': upper,
            'CANONICAL_LOWER_TRIGRAM': lower,
            'MEIHUA_MAIN_HEXAGRAM_REPORTED': packet['MAIN_HEXAGRAM'],
            'YIJING_MAIN_HEXAGRAM_CANONICAL': canonical_main,
            'MOVING_LINE': moving,
            'MEIHUA_CHANGED_HEXAGRAM_REPORTED': packet['CHANGED_HEXAGRAM'],
            'YIJING_CHANGED_HEXAGRAM_STRUCTURAL': evidence['CHANGED_HEXAGRAM'],
            'NAME_BRIDGE_POLICY': NAME_BRIDGE_POLICY,
            'DISPLAY_NAME_EQUALITY_USED': False,
        },
        'YIJING_EVIDENCE': evidence,
        'YIJING_EVIDENCE_FINGERPRINT': yijing_evidence_fingerprint(evidence),
        'BRIDGE_ASSERTIONS': {
            'MAIN_HEXAGRAM_MAPPED_FROM_TRIGRAM_STRUCTURE': 'PASS',
            'MOVING_LINE_MATCHES_SELECTED_YAO': 'PASS',
            'SELECTED_YAO_TEXT_PRESENT': 'PASS',
            'SELECTED_XIAOXIANG_PRESENT': 'PASS',
            'CHANGED_HEXAGRAM_EVIDENCE_PRESENT': 'PASS',
        },
        'HINDSIGHT_FIELDS_PRESENT': hindsight_present,
        'HINDSIGHT_ISOLATION': (
            'Yi Jing input is only the canonical hexagram from Meihua trigram structure plus the '
            'Meihua moving line; prediction/result/correct/rethink are excluded from Yi Jing '
            'evidence and from the Yi Jing evidence fingerprint'
        ),
        'PROVENANCE_POLICY': 'MECHANICAL_CROSS_LANE_BRIDGE_KEEP_SOURCE_PACKETS_INDEPENDENT',
        'INTERPRETATION_STATUS': 'NOT_PERFORMED',
        'FINAL_PREDICTION': 'NOT_EMITTED',
        'PREDICTIVE_STATUS': 'NOT_ESTABLISHED',
        'NONCLAIMS': [
            'NO_CROSS_REPO_DOCTRINE_MERGE',
            'NO_FULL_TRADITIONAL_SIMPLIFIED_NAME_EQUIVALENCE_CLAIM',
            'YIJING_TEXT_PRESENT_IS_NOT_PREDICTIVE_VALIDITY',
            'NO_DIVINATION_JUDGMENT',
        ],
    }


def assembly_fingerprint(meihua, yijing, cegui):
    stable = {
        'origin_trigram': meihua['SOURCE_CASE_FACTS']['origin_trigram'],
        'shift_yao': meihua['SOURCE_CASE_FACTS']['shift_yao'],
        'meihua_engine_fingerprint': meihua['ENGINE_FACT_FINGERPRINT'],
        'yijing_evidence_fingerprint': yijing['YIJING_EVIDENCE_FINGERPRINT'],
        'cegui_fact_fingerprint': cegui['CEGUI_FACT_FINGERPRINT'],
    }
    raw = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True, help='One plum-app-style case JSON record')
    a = p.parse_args()

    input_path = str(Path(a.input).resolve())
    meihua = run_json([sys.executable, str(MEIHUA), '--input', input_path], MEIHUA.name)
    cegui = run_json([sys.executable, str(CEGUI), '--input', input_path], CEGUI.name)

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
    hindsight_present = sorted(hindsight_meihua)

    yijing = build_yijing_component(meihua, hindsight_present)
    if yijing['BRIDGE']['MOVING_LINE'] != meihua_source['shift_yao']:
        fail('Assembly source mismatch: Yi Jing moving line differs from plum-app shift_yao', 1)

    out = {
        'PRODUCT_SHELL': 'PLUM_APP_CASE',
        'CAPABILITY': 'ONE_CASE_MEIHUA_YIJING_CEGUI_IGNITION',
        'SOURCE_CASE': {
            'problem': meihua_source['problem'],
            'origin_trigram': meihua_source['origin_trigram'],
            'shift_yao': meihua_source['shift_yao'],
        },
        'COMPONENTS': {
            'MEIHUA': meihua,
            'YIJING': yijing,
            'CEGUI': cegui,
        },
        'ASSEMBLY_FINGERPRINT': assembly_fingerprint(meihua, yijing, cegui),
        'HINDSIGHT_FIELDS_PRESENT': hindsight_present,
        'HINDSIGHT_ISOLATION': (
            'All three deterministic component fingerprints (Meihua engine, Yi Jing evidence, '
            'CEGUI facts) and the assembly fingerprint exclude prediction/result/correct/rethink'
        ),
        'ASSEMBLY_STATUS': 'MECHANICAL_PIPELINES_READY',
        'FINAL_PREDICTION': 'NOT_EMITTED',
        'PREDICTIVE_STATUS': 'NOT_ESTABLISHED',
        'NONCLAIMS': [
            'NO_CROSS_METHOD_SYNTHESIS',
            'MEIHUA_PLUS_YIJING_PLUS_CEGUI_IS_NOT_CONSENSUS',
            'NO_MAJORITY_VOTE',
            'NO_PREDICTIVE_ACCURACY_CLAIM',
            'YIJING_TEXT_PRESENT_IS_NOT_PREDICTIVE_VALIDITY',
            'NO_FULL_TRADITIONAL_SIMPLIFIED_NAME_EQUIVALENCE_CLAIM',
            'NO_GENERIC_ROUTER_OR_PLUGIN_FRAMEWORK',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
