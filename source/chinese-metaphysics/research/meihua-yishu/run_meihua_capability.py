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


UPSTREAM_REPO = 'muyen/meihua-yishu'
ENGINE_SOURCE_PATH = 'scripts/meihua_calc.py'
EXPECTED_AUTHORITY_TYPE = 'MECHANICAL_AUTHORITY'
DIRECT_SUPPORT_STATUS = 'DIRECT_ENGINE_SOURCE_SUPPORT'
METHOD_REF_STATUS = 'REPO_DECLARED_METHOD_SUPPORT'


def _resolve_upstream_path(rel_path, label):
    """Resolve a relative path inside the pinned upstream; fail closed on escape."""
    if not isinstance(rel_path, str) or not rel_path:
        fail(f'Rule evidence {label}: source_path must be a non-empty string', 3)
    if '..' in Path(rel_path).parts:
        fail(f'Rule evidence {label}: source_path contains "..": {rel_path!r}', 3)
    if Path(rel_path).is_absolute():
        fail(f'Rule evidence {label}: source_path must be relative: {rel_path!r}', 3)
    candidate = (UPSTREAM / rel_path).resolve()
    try:
        candidate.relative_to(UPSTREAM.resolve())
    except ValueError:
        fail(f'Rule evidence {label}: source_path escapes pinned upstream: {rel_path!r}', 3)
    if not candidate.is_file():
        fail(f'Rule evidence {label}: source file does not exist in pinned upstream: {rel_path}', 3)
    return candidate


def _read_upstream_text(rel_path, label):
    resolved = _resolve_upstream_path(rel_path, label)
    try:
        return resolved.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return resolved.read_text(encoding='utf-8', errors='replace')


def _validate_source_entry(entry, label):
    """Validate a single evidence entry (top-level or method_reference)."""
    status = entry.get('support_status')
    path = entry.get('source_path')
    anchor = entry.get('source_anchor')
    claim = entry.get('bounded_supported_claim')

    if status not in (DIRECT_SUPPORT_STATUS, METHOD_REF_STATUS):
        fail(f'Rule evidence {label}: unknown support_status {status!r}', 3)
    resolved = _resolve_upstream_path(path, label)
    if not isinstance(anchor, str) or not anchor:
        fail(f'Rule evidence {label}: source_anchor must be a non-empty string', 3)
    if not isinstance(claim, str) or not claim.strip():
        fail(f'Rule evidence {label}: bounded_supported_claim must be non-empty', 3)
    text = _read_upstream_text(path, label)
    if anchor not in text:
        fail(
            f'Rule evidence {label}: source_anchor {anchor!r} not found in '
            f'pinned file {path} (resolved={resolved})',
            3,
        )
    return True


def _validate_rule_evidence(rule_ids, catalog):
    """Production validator: every applied rule must have load-bearing evidence,
    evidence must not leak unapplied rules, and every entry's source identity
    and literal locator must resolve inside the pinned upstream."""
    trace_set = set(rule_ids)
    catalog_ids = set(catalog.keys())
    missing = trace_set - catalog_ids
    if missing:
        fail(f'Rule evidence missing for applied rule(s): {sorted(missing)}', 3)
    extra = {rid for rid in trace_set if False}  # no-op; extra is checked per-evidence below
    evidence = []
    for rid in rule_ids:
        entry = catalog[rid]
        label = f'rule_id={rid}'
        # Top-level must be DIRECT_ENGINE_SOURCE_SUPPORT with exact engine pin/repo.
        if entry.get('support_status') != DIRECT_SUPPORT_STATUS:
            fail(f'{label}: top-level support_status must be {DIRECT_SUPPORT_STATUS!r}', 3)
        if entry.get('repo') != UPSTREAM_REPO:
            fail(f'{label}: repo must be {UPSTREAM_REPO!r}, got {entry.get("repo")!r}', 3)
        if entry.get('pin') != PIN:
            fail(f'{label}: pin must be {PIN!r}, got {entry.get("pin")!r}', 3)
        if entry.get('authority_type') != EXPECTED_AUTHORITY_TYPE:
            fail(
                f'{label}: authority_type must be {EXPECTED_AUTHORITY_TYPE!r}, '
                f'got {entry.get("authority_type")!r}',
                3,
            )
        _validate_source_entry(entry, label)
        method_ref = entry.get('method_reference')
        out_entry = {'rule_id': rid, **entry}
        if method_ref is not None:
            if not isinstance(method_ref, dict):
                fail(f'{label}: method_reference must be a dict when present', 3)
            if method_ref.get('support_status') != METHOD_REF_STATUS:
                fail(f'{label}: method_reference.support_status must be {METHOD_REF_STATUS!r}', 3)
            _validate_source_entry(method_ref, f'{label} method_reference')
        evidence.append(out_entry)
    # Extra evidence (catalog entries not triggered by this cast) must NOT be emitted.
    unapplied = catalog_ids - trace_set
    # We do not iterate unapplied into the output, but to be fail-closed we also
    # refuse if any applied entry's id is invalid (already enforced above).
    return evidence, sorted(unapplied)


RULE_EVIDENCE_CATALOG = {
    'MEIHUA_TRADITIONAL_TIME_CAST': {
        'support_status': DIRECT_SUPPORT_STATUS,
        'repo': UPSTREAM_REPO,
        'pin': PIN,
        'source_path': ENGINE_SOURCE_PATH,
        'source_anchor': 'def qigua_by_time(',
        'authority_type': EXPECTED_AUTHORITY_TYPE,
        'bounded_supported_claim': (
            'Pinned qigua_by_time computes upper=(year+month+day) mod 8, '
            'lower=(upper+shichen) mod 8, moving=lower mod 6 via lunar year-branch numbers; '
            'it delegates to num_to_gua/num_to_yao/_analyze_hexagram.'
        ),
    },
    'MEIHUA_NUMBER_CAST_UPPER_LOWER': {
        'support_status': DIRECT_SUPPORT_STATUS,
        'repo': UPSTREAM_REPO,
        'pin': PIN,
        'source_path': ENGINE_SOURCE_PATH,
        'source_anchor': 'def qigua_by_numbers(',
        'authority_type': EXPECTED_AUTHORITY_TYPE,
        'bounded_supported_claim': (
            'Pinned qigua_by_numbers maps first number to upper trigram and second '
            'number to lower trigram via num_to_gua (remainder mod 8; 0 => 8).'
        ),
    },
    'MEIHUA_NUMBER_CAST_MOVING_FROM_TOTAL': {
        'support_status': DIRECT_SUPPORT_STATUS,
        'repo': UPSTREAM_REPO,
        'pin': PIN,
        'source_path': ENGINE_SOURCE_PATH,
        'source_anchor': 'def qigua_by_numbers(',
        'authority_type': EXPECTED_AUTHORITY_TYPE,
        'bounded_supported_claim': (
            'Pinned qigua_by_numbers derives moving line from the sum of all supplied '
            'numbers via num_to_yao (remainder mod 6; 0 => 6).'
        ),
    },
    'MEIHUA_TI_YONG_MOVING_TRIGRAM_AS_USE': {
        'support_status': DIRECT_SUPPORT_STATUS,
        'repo': UPSTREAM_REPO,
        'pin': PIN,
        'source_path': ENGINE_SOURCE_PATH,
        'source_anchor': 'def _analyze_hexagram(',
        'authority_type': EXPECTED_AUTHORITY_TYPE,
        'bounded_supported_claim': (
            'Pinned _analyze_hexagram assigns body/use by moving-line position: if moving '
            'line is in the upper trigram (positions 4-6) then lower=体 and upper=用; '
            'otherwise upper=体 and lower=用 (i.e. the moving trigram becomes 用).'
        ),
        'method_reference': {
            'support_status': METHOD_REF_STATUS,
            'source_path': 'README.zh-TW.md',
            'source_anchor': '### 體用論',
            'bounded_supported_claim': (
                'Pinned README.zh-TW §體用論 defines 體卦 as 主體/自己/問卦者 and 用卦 as '
                '客體/事情/外在環境; the README declares the method but does not contain '
                'the full classical 體用總訣 text.'
            ),
        },
    },
    'MEIHUA_WUXING_SHENG_KE': {
        'support_status': DIRECT_SUPPORT_STATUS,
        'repo': UPSTREAM_REPO,
        'pin': PIN,
        'source_path': ENGINE_SOURCE_PATH,
        'source_anchor': 'def analyze_wuxing(',
        'authority_type': EXPECTED_AUTHORITY_TYPE,
        'bounded_supported_claim': (
            'Pinned analyze_wuxing deterministically returns one of five traditional-script '
            'relations: 比和, 用生體, 體生用, 體克用, 用克體 (with parenthetical valence tag), '
            'using WUXING_SHENG / WUXING_KE tables.'
        ),
        'method_reference': {
            'support_status': METHOD_REF_STATUS,
            'source_path': 'README.zh-TW.md',
            'source_anchor': '| 用生體 | 大吉 | 有進益之喜，外力相助 |',
            'bounded_supported_claim': (
                'Pinned README §體用論 five-row table lists the same five 體/用 生克 '
                'prefixes the engine produces (用生體/體克用/體用比和/用克體/體生用); '
                'this is repo-declared method support, not historical validation.'
            ),
        },
    },
}

CLASSICAL_REFERENCE_POINTERS = [
    {
        'work': '梅花易数·卷一·年月日時起例',
        'url': 'https://zh.wikisource.org/wiki/梅花易數/卷一',
        'status': 'REFERENCE_POINTER_ONLY_UNVERIFIED',
        'note': 'External URL only; text not vendored or verified inside source boundary.',
    },
    {
        'work': '梅花易数·卷二·体用总诀',
        'url': 'https://zh.wikisource.org/zh-hant/梅花易數/卷二',
        'status': 'REFERENCE_POINTER_ONLY_UNVERIFIED',
        'note': 'External URL only; text not vendored or verified inside source boundary.',
    },
    {
        'work': '梅花易数·卷三·体用生克之诀',
        'url': 'https://zh.wikisource.org/zh-hant/梅花易數/卷三',
        'status': 'REFERENCE_POINTER_ONLY_UNVERIFIED',
        'note': 'External URL only; text not vendored or verified inside source boundary.',
    },
]


def rule_evidence_for(rule_ids, catalog=None):
    """Validate and emit rule evidence for exactly the applied rule_ids.

    Fail closed if any applied rule is missing from the catalog, if any catalog
    entry fails source-identity/path/anchor validation, or if the catalog drifts
    from the expected repo/pin/authority. This is production validation, not
    a test-only assertion.
    """
    if catalog is None:
        catalog = RULE_EVIDENCE_CATALOG
    trace_set = set(rule_ids)
    if len(trace_set) != len(rule_ids):
        dups = [r for r in rule_ids if rule_ids.count(r) > 1]
        fail(f'Duplicate rule_id in RULE_TRACE: {sorted(set(dups))}', 3)
    evidence, unapplied = _validate_rule_evidence(list(trace_set), catalog)
    # Re-order to match the applied trace order for deterministic output.
    by_id = {e['rule_id']: e for e in evidence}
    ordered = [by_id[rid] for rid in rule_ids]
    return ordered, unapplied


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

    rule_evidence, _unapplied = rule_evidence_for(rule_trace)
    # Production invariant: RULE_EVIDENCE ids exactly equal RULE_TRACE ids.
    evidence_ids = [e['rule_id'] for e in rule_evidence]
    if evidence_ids != rule_trace:
        fail('RULE_EVIDENCE does not exactly cover RULE_TRACE', 3)

    out = {
        'DOMAIN': 'MEIHUA_YISHU',
        'ENGINE_REPO': UPSTREAM_REPO,
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
        'RULE_EVIDENCE': rule_evidence,
        'STRUCTURAL_OUTPUT': structural,
        'SEASON_CONTEXT_STATUS': 'PRESENT' if '卦氣旺衰' in result else 'ABSENT_NOT_INFERRED',
        'EXTERNAL_SIGN_STATUS': 'MISSING_DO_NOT_FABRICATE',
        'PROVENANCE_STATUS': 'PINNED_ENGINE_SOURCE_BOUND_SELECTED_SLICE',
        'CLASSICAL_TEXT_GROUNDED': False,
        'CLASSICAL_REFERENCE_POINTERS': CLASSICAL_REFERENCE_POINTERS,
        'RUNTIME_NETWORK_DEPENDENCY': False,
        'ENGINE_AUTHORITY_NOTE': (
            'Output values (trigrams, moving line, hexagrams, 體/用, 五行 relation) are '
            'computed by the pinned meihua-yishu engine; no second engine exists in P2P.'
        ),
        'PREDICTIVE_STATUS': 'NOT_ESTABLISHED_NEGATIVE_EVIDENCE_PRESERVED',
        'NONCLAIMS': [
            'NO_PERSONAL_FUTURE_PREDICTION',
            'NO_EXTERNAL_SIGN_INVENTION',
            'NO_CASTING_MODE_EQUIVALENCE_CLAIM',
            'NO_CLASSICAL_TEXT_GROUNDING_CLAIM',
            'NO_PREDICTIVE_VALIDITY_CLAIM',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
