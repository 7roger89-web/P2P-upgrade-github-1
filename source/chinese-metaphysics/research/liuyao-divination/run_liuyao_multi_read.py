#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PIN = '1a5a78b513c0e7b46dfb29f74043bcf978c32a3e'
SCRIPT_DIR = Path(__file__).resolve().parent
UPSTREAM = (SCRIPT_DIR / '../../upstreams/liuyao-divination').resolve()
ALLOWED_LENSES = ('父母', '兄弟', '子孙', '妻财', '官鬼')


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

sys.path.insert(0, str(UPSTREAM / 'src'))
from liuyao import cast_board  # noqa: E402


def parse_moving(text):
    try:
        values = [int(x.strip()) for x in text.split(',') if x.strip()]
    except ValueError:
        fail(f'Invalid --moving: {text}')
    if not values or any(x < 1 or x > 6 for x in values) or len(set(values)) != len(values):
        fail(f'Invalid --moving: {text}')
    return values


def parse_lenses(text):
    values = [x.strip() for x in text.split(',') if x.strip()]
    if not values:
        fail('At least one lens is required')
    if len(set(values)) != len(values):
        fail('Duplicate lenses are not allowed')
    invalid = [x for x in values if x not in ALLOWED_LENSES]
    if invalid:
        fail(f'Unsupported lens: {invalid[0]}')
    return values


def line_mechanics(ln):
    return {
        'position': ln.position,
        'yin_yang': ln.yin_yang,
        'gan': ln.gan,
        'zhi': ln.zhi,
        'qin': ln.qin,
        'shen': ln.shen,
        'is_world': ln.is_world,
        'is_response': ln.is_response,
        'is_moving': ln.is_moving,
        'change_gan': ln.change_gan,
        'change_zhi': ln.change_zhi,
        'change_qin': ln.change_qin,
        'state': ln.state,
        'prosperous': ln.prosperous,
        'void': ln.void,
        'month_break': ln.month_break,
        'day_strike': ln.day_strike,
        'dark_move': ln.dark_move,
        'day_break': ln.day_break,
        'jin_tui': ln.jin_tui,
        'in_grave': ln.in_grave,
    }


def mechanical_packet(board):
    return {
        'hexagram': board.hexagram,
        'changed_hexagram': board.changed_hexagram,
        'palace': board.palace,
        'palace_wx': board.palace_wx,
        'world_pos': board.world_pos,
        'response_pos': board.response_pos,
        'month_zhi': board.month_zhi,
        'day_gz': board.day_gz,
        'xunkong': list(board.xunkong),
        'lines': [line_mechanics(x) for x in board.lines],
    }


def packet_sha(packet):
    raw = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def lens_packet(board, lens):
    return {
        'lens': lens,
        'visible_yongshen_positions': [x.position for x in board.yongshen_lines],
        'visible_yongshen_count': len(board.yongshen_lines),
        'yongshen_wx': board.yongshen_wx,
        'status': 'VISIBLE_YONGSHEN_FOUND' if board.yongshen_lines else 'VISIBLE_YONGSHEN_MISSING_FUSHEN_REQUIRES_SEPARATE_ANALYSIS',
        'role_facts': [
            {
                'position': x.position,
                'qin': x.qin,
                'zhi': x.zhi,
                'role': x.role,
                'effective': x.effective,
                'effective_reason': x.effective_reason,
                'state': x.state,
                'is_moving': x.is_moving,
                'dark_move': x.dark_move,
                'day_break': x.day_break,
            }
            for x in board.lines
            if x.role is not None
        ],
        'structural_output': 'LENS_FACTS_ONLY_NO_CROSS_LENS_SYNTHESIS',
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixture')
    p.add_argument('--hexagram')
    p.add_argument('--moving')
    p.add_argument('--month')
    p.add_argument('--day')
    p.add_argument('--lenses', default='妻财,官鬼,父母,子孙,兄弟')
    a = p.parse_args()

    custom = any([a.hexagram, a.moving, a.month, a.day])
    if a.fixture and custom:
        fail('Use either --fixture or custom board arguments, not both')
    if a.fixture:
        if a.fixture != 'canonical-01':
            fail(f'Unknown fixture: {a.fixture}')
        raw = {'hexagram': '地泽临', 'moving': [2], 'month_zhi': '未', 'day_gz': '辛卯'}
        input_mode = 'FIXTURE'
    else:
        if not all([a.hexagram, a.moving, a.month, a.day]):
            fail('Custom usage: --hexagram NAME --moving 1[,2] --month ZHI --day GANZHI [--lenses 妻财,官鬼,...]')
        raw = {
            'hexagram': a.hexagram,
            'moving': parse_moving(a.moving),
            'month_zhi': a.month,
            'day_gz': a.day,
        }
        input_mode = 'CUSTOM'

    lenses = parse_lenses(a.lenses)
    try:
        base_board = cast_board(raw['hexagram'], raw['moving'], raw['month_zhi'], raw['day_gz'], None)
    except Exception as exc:
        fail(f'liuyao rejected input: {exc}', 1)

    mechanics = mechanical_packet(base_board)
    fingerprint = packet_sha(mechanics)
    outputs = []

    for lens in lenses:
        try:
            board = cast_board(raw['hexagram'], raw['moving'], raw['month_zhi'], raw['day_gz'], lens)
        except Exception as exc:
            fail(f'liuyao rejected lens {lens}: {exc}', 1)
        current_mechanics = mechanical_packet(board)
        current_fingerprint = packet_sha(current_mechanics)
        if current_fingerprint != fingerprint:
            fail(f'Mechanical board changed across lens {lens}', 1)
        outputs.append(lens_packet(board, lens))

    out = {
        'DOMAIN': 'LIUYAO',
        'ENGINE_PIN': PIN,
        'CAPABILITY': 'ONE_HEXAGRAM_MULTIPLE_LENSES',
        'INPUT_MODE': input_mode,
        'RAW_CAST': raw,
        'BOARD_FINGERPRINT_SHA256': fingerprint,
        'MECHANICAL_BOARD': mechanics,
        'LENSES': outputs,
        'METHOD_SOURCE': 'Johnson-Jia/liuyao-divination references/02-用神取用.md',
        'INVARIANTS': {
            'ONE_MECHANICAL_BOARD': 'YES',
            'LENS_CHANGES_BOARD': 'NO',
            'CROSS_LENS_SYNTHESIS': 'NO',
            'WINNER_OR_MAJORITY': 'NO',
        },
        'PROVENANCE_STATUS': 'PINNED_UPSTREAM_METHOD_REFERENCE',
        'PREDICTIVE_STATUS': 'NOT_TESTED',
        'NONCLAIMS': [
            'NO_ONE_HEXAGRAM_PREDICTIVE_VALIDATION',
            'NO_FUSHEN_AUTOMATION',
            'NO_CROSS_TOPIC_CONCLUSION',
            'NO_FORCED_GOOD_BAD_VERDICT',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
