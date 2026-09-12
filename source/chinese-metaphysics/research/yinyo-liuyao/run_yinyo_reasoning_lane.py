#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

YINYO_PIN = '1f67eea0ce5a2c49e6851e4eedce507f9c044dd9'
SCRIPT_DIR = Path(__file__).resolve().parent
LAB_ROOT = SCRIPT_DIR.parent
YINYO_UPSTREAM = (LAB_ROOT / '../../upstreams/yinyo-liuyao').resolve()
MULTI_READ = LAB_ROOT / 'liuyao-divination' / 'run_liuyao_multi_read.py'


def fail(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def verify_yinyo_pin():
    if not YINYO_UPSTREAM.exists():
        fail(f'Pinned upstream missing: {YINYO_UPSTREAM}')
    try:
        head = subprocess.check_output(
            ['git', '-C', str(YINYO_UPSTREAM), 'rev-parse', 'HEAD'], text=True
        ).strip()
    except Exception:
        fail(f'Cannot verify pinned upstream: {YINYO_UPSTREAM}')
    if head != YINYO_PIN:
        fail(f'Pinned upstream SHA mismatch: expected {YINYO_PIN}, got {head}')


def run_board(args):
    cmd = [sys.executable, str(MULTI_READ)]
    if args.fixture:
        cmd += ['--fixture', args.fixture]
    else:
        cmd += [
            '--hexagram', args.hexagram,
            '--moving', args.moving,
            '--month', args.month,
            '--day', args.day,
        ]
    # One lens is enough to force the existing multi-read invariant check while
    # preserving a single mechanical board packet for this reasoning lane.
    cmd += ['--lenses', '妻财']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        fail(f'Invalid Liuyao packet: {exc}', 1)


def compact_line(line):
    return {
        'position': line['position'],
        'qin': line['qin'],
        'zhi': line['zhi'],
        'is_world': line['is_world'],
        'is_response': line['is_response'],
        'is_moving': line['is_moving'],
    }


def pattern_packet(rule_id, source_anchor, matches, note):
    return {
        'rule_id': rule_id,
        'source': f'xiaoshiyilangzhao1996-droid/yinyo-liuyao@{YINYO_PIN}:docs/rules.md#{source_anchor}',
        'status': 'PRESENT' if matches else 'ABSENT',
        'matches': matches,
        'interpretation_boundary': note,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixture')
    p.add_argument('--hexagram')
    p.add_argument('--moving')
    p.add_argument('--month')
    p.add_argument('--day')
    a = p.parse_args()

    custom = any([a.hexagram, a.moving, a.month, a.day])
    if a.fixture and custom:
        fail('Use either --fixture or custom board arguments, not both')
    if a.fixture:
        if a.fixture != 'canonical-01':
            fail(f'Unknown fixture: {a.fixture}')
    elif not all([a.hexagram, a.moving, a.month, a.day]):
        fail('Custom usage: --hexagram NAME --moving 1[,2] --month ZHI --day GANZHI')

    verify_yinyo_pin()
    board_packet = run_board(a)
    if board_packet.get('INVARIANTS', {}).get('ONE_MECHANICAL_BOARD') != 'YES':
        fail('Upstream Liuyao board invariant missing', 1)

    lines = board_packet['MECHANICAL_BOARD']['lines']

    xunkong = [compact_line(x) for x in lines if x.get('void')]
    yuepo = [compact_line(x) for x in lines if x.get('month_break')]
    jintui = [
        {**compact_line(x), 'jin_tui': x.get('jin_tui')}
        for x in lines if x.get('jin_tui')
    ]

    patterns = [
        pattern_packet(
            'YINYO_L3_XUNKONG', '旬空真空假空冲空实空', xunkong,
            'STRUCTURAL_FLAG_ONLY__DO_NOT_EQUATE_VOID_WITH_USELESS',
        ),
        pattern_packet(
            'YINYO_L3_YUEPO', '月破真破假破出破', yuepo,
            'STRUCTURAL_FLAG_ONLY__DO_NOT_EQUATE_MONTH_BREAK_WITH_PERMANENT_FAILURE',
        ),
        pattern_packet(
            'YINYO_L3_JINTUI', '进神退神', jintui,
            'DIRECTIONAL_MODIFIER_ONLY__GOOD_BAD_DEPENDS_ON_SUBJECT_AND_YONGSHEN_CHAIN',
        ),
    ]

    out = {
        'DOMAIN': 'LIUYAO',
        'CAPABILITY': 'ISOLATED_YINYO_STRUCTURAL_REASONING_LANE',
        'MECHANICAL_ENGINE_PIN': board_packet['ENGINE_PIN'],
        'REASONING_SOURCE_PIN': YINYO_PIN,
        'REUSE_SCOPE': 'RESEARCH_REFERENCE_ONLY',
        'BOARD_FINGERPRINT_SHA256': board_packet['BOARD_FINGERPRINT_SHA256'],
        'RAW_CAST': board_packet['RAW_CAST'],
        'PATTERNS': patterns,
        'RULE_ORDER_BOUNDARY': 'MAIN_YONGSHEN_OUTCOME_FIRST__SPECIAL_PATTERNS_ARE_MODIFIERS',
        'FINAL_VERDICT': 'NOT_EMITTED',
        'PROVENANCE_STATUS': 'REPO_LOCAL_RULE_CORPUS__CLASSICAL_LOCATOR_NOT_YET_FULLY_AUDITED',
        'PREDICTIVE_STATUS': 'NOT_TESTED',
        'NONCLAIMS': [
            'NO_NEW_BOARD_ENGINE',
            'NO_CLASSICAL_PROVENANCE_PROMOTION',
            'NO_BLIND_PREDICTIVE_VALIDATION',
            'NO_GOOD_BAD_FROM_PATTERN_LABEL_ALONE',
            'NO_CROSS_REPO_RULE_NORMALIZATION',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
