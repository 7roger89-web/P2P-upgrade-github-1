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

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'yijing'))
import run_plum_case_ignition as ignition_module  # noqa: E402
import run_yijing_capability as yijing_runtime  # noqa: E402


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
assert ignition['CAPABILITY'] == 'ONE_CASE_MEIHUA_YIJING_CEGUI_IGNITION'
assert ignition['ASSEMBLY_STATUS'] == 'MECHANICAL_PIPELINES_READY'
assert ignition['SOURCE_CASE']['origin_trigram'] == '泽火革'
assert ignition['SOURCE_CASE']['shift_yao'] == 1
assert ignition['COMPONENTS']['MEIHUA']['ENGINE_FACT_FINGERPRINT'] == meihua['ENGINE_FACT_FINGERPRINT']
assert ignition['COMPONENTS']['CEGUI']['CEGUI_FACT_FINGERPRINT'] == cegui['CEGUI_FACT_FINGERPRINT']
assert ignition['COMPONENTS']['MEIHUA']['ANALYSIS_PACKET']['MAIN_HEXAGRAM'] == '泽火革'
assert ignition['COMPONENTS']['MEIHUA']['ANALYSIS_PACKET']['CHANGED_HEXAGRAM'] == '泽山咸'
assert ignition['COMPONENTS']['CEGUI']['TRANSPORT']['format_string'] == '231'

# --- A: one plum-app case yields MEIHUA + YIJING + CEGUI in one packet -------
assert list(ignition['COMPONENTS']) == ['MEIHUA', 'YIJING', 'CEGUI']
yijing_component = ignition['COMPONENTS']['YIJING']
evidence = yijing_component['YIJING_EVIDENCE']
bridge = yijing_component['BRIDGE']
meihua_packet = ignition['COMPONENTS']['MEIHUA']['ANALYSIS_PACKET']
assert yijing_component['DOMAIN'] == 'YIJING'
assert evidence['DOMAIN'] == 'YIJING'
assert evidence['CAPABILITY'].startswith('SOURCE_GROUNDED_GUA_YAO_TUAN_DAXIANG_XIAOXIANG')
assert evidence['GUA_CI'] and evidence['TUAN_TEXT'] and evidence['DAXIANG_TEXT']

# --- B: hexagram selected from Meihua trigram STRUCTURE, not display names ---
assert bridge['NAME_BRIDGE_POLICY'] == (
    'TRIGRAM_STRUCTURE_NOT_FULL_TRADITIONAL_SIMPLIFIED_TEXT_CONVERSION'
)
assert bridge['DISPLAY_NAME_EQUALITY_USED'] is False
# the structure actually consumed is the Meihua normalized trigram pair
assert bridge['CANONICAL_UPPER_TRIGRAM'] == meihua_packet['NORMALIZED_INPUT']['upper_trigram'] == '兑'
assert bridge['CANONICAL_LOWER_TRIGRAM'] == meihua_packet['NORMALIZED_INPUT']['lower_trigram'] == '离'
# and the existing runtime table maps that structure to the canonical hexagram
assert yijing_runtime.HEXAGRAM_BY_TRIGRAMS[('兑', '离')] == '泽火革'
assert bridge['YIJING_MAIN_HEXAGRAM_CANONICAL'] == '泽火革'
assert evidence['INPUT']['hexagram'] == '泽火革'
assert evidence['NORMALIZED_HEXAGRAM'] == '泽火革'
# the runtime independently reports the same structure back
assert (evidence['UPPER_TRIGRAM'], evidence['LOWER_TRIGRAM']) == ('兑', '离')
# negative control: the traditional display spelling of the same structure is
# not a key, so display-name equality would have silently failed
assert ('兌', '離') not in yijing_runtime.HEXAGRAM_BY_TRIGRAMS
# in-packet witness that Meihua display names do carry traditional variants the
# Yi Jing corpus spells differently, i.e. name equality is genuinely fragile here
assert meihua_packet['MUTUAL_HEXAGRAM'] == '天風姤'
assert yijing_runtime.HEXAGRAM_BY_TRIGRAMS[('乾', '巽')] == '天风姤' != meihua_packet['MUTUAL_HEXAGRAM']

# --- C: Yi Jing selected moving line equals the Meihua moving line -----------
assert bridge['MOVING_LINE'] == meihua_packet['MOVING_LINE'] == base['shift_yao'] == 1
assert evidence['INPUT']['moving'] == [1]
selected = evidence['SELECTED_YAO']
assert len(selected) == 1
assert selected[0]['position'] == meihua_packet['MOVING_LINE']
assert yijing_component['BRIDGE_ASSERTIONS']['MOVING_LINE_MATCHES_SELECTED_YAO'] == 'PASS'

# --- D + E: selected 爻 text and 小象 are present -----------------------------
assert selected[0]['label'] == '初九'
assert isinstance(selected[0]['text'], str) and selected[0]['text'].strip()
assert isinstance(selected[0]['xiaoxiang'], str) and selected[0]['xiaoxiang'].strip()
assert yijing_component['BRIDGE_ASSERTIONS']['SELECTED_YAO_TEXT_PRESENT'] == 'PASS'
assert yijing_component['BRIDGE_ASSERTIONS']['SELECTED_XIAOXIANG_PRESENT'] == 'PASS'

# --- F: changed-hexagram evidence is returned --------------------------------
assert evidence['CHANGED_HEXAGRAM'] and evidence['CHANGED_GUA_CI']
assert evidence['CHANGED_UPPER_TRIGRAM'] and evidence['CHANGED_LOWER_TRIGRAM']
assert bridge['YIJING_CHANGED_HEXAGRAM_STRUCTURAL'] == evidence['CHANGED_HEXAGRAM']
assert bridge['MEIHUA_CHANGED_HEXAGRAM_REPORTED'] == meihua_packet['CHANGED_HEXAGRAM']
assert yijing_component['BRIDGE_ASSERTIONS']['CHANGED_HEXAGRAM_EVIDENCE_PRESENT'] == 'PASS'

# --- assembly fingerprint really covers the new Yi Jing component ------------
assert yijing_component['YIJING_EVIDENCE_FINGERPRINT']
mutated = deepcopy(yijing_component)
mutated['YIJING_EVIDENCE_FINGERPRINT'] = '0' * 64
assert ignition_module.assembly_fingerprint(
    ignition['COMPONENTS']['MEIHUA'], mutated, ignition['COMPONENTS']['CEGUI']
) != ignition['ASSEMBLY_FINGERPRINT']

# --- H + I: no prediction, no predictive claim -------------------------------
assert ignition['FINAL_PREDICTION'] == 'NOT_EMITTED'
assert ignition['PREDICTIVE_STATUS'] == 'NOT_ESTABLISHED'
assert yijing_component['FINAL_PREDICTION'] == 'NOT_EMITTED'
assert yijing_component['PREDICTIVE_STATUS'] == 'NOT_ESTABLISHED'
assert yijing_component['INTERPRETATION_STATUS'] == 'NOT_PERFORMED'
assert 'MEIHUA_PLUS_YIJING_PLUS_CEGUI_IS_NOT_CONSENSUS' in ignition['NONCLAIMS']
assert 'NO_MAJORITY_VOTE' in ignition['NONCLAIMS']
assert 'YIJING_TEXT_PRESENT_IS_NOT_PREDICTIVE_VALIDITY' in ignition['NONCLAIMS']

# --- G: hindsight fields have zero influence ---------------------------------
assert ignition['HINDSIGHT_FIELDS_PRESENT'] == ['correct', 'prediction', 'result', 'rethink']
assert yijing_component['HINDSIGHT_FIELDS_PRESENT'] == ignition['HINDSIGHT_FIELDS_PRESENT']

changed = deepcopy(base)
changed['prediction'] = 'changed after reveal'
changed['result'] = 'changed outcome text'
changed['correct'] = 0
changed['rethink'] = 'changed retrospective explanation'
second, _, _ = run_case(changed)
assert second['ASSEMBLY_FINGERPRINT'] == ignition['ASSEMBLY_FINGERPRINT']
assert second['COMPONENTS']['MEIHUA']['ENGINE_FACT_FINGERPRINT'] == ignition['COMPONENTS']['MEIHUA']['ENGINE_FACT_FINGERPRINT']
assert second['COMPONENTS']['CEGUI']['CEGUI_FACT_FINGERPRINT'] == ignition['COMPONENTS']['CEGUI']['CEGUI_FACT_FINGERPRINT']
assert second['COMPONENTS']['YIJING']['YIJING_EVIDENCE_FINGERPRINT'] == yijing_component['YIJING_EVIDENCE_FINGERPRINT']
assert second['COMPONENTS']['YIJING']['YIJING_EVIDENCE'] == evidence
assert second['COMPONENTS']['YIJING']['BRIDGE'] == bridge

print('PLUM_APP_CASE_IGNITION_TEST=PASS')
