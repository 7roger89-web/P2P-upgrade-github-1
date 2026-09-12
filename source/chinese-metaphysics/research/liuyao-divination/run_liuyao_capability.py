#!/usr/bin/env python3
import argparse, json, subprocess, sys
from pathlib import Path

PIN = '1a5a78b513c0e7b46dfb29f74043bcf978c32a3e'
SCRIPT_DIR = Path(__file__).resolve().parent
UPSTREAM = (SCRIPT_DIR / '../../upstreams/liuyao-divination').resolve()

def fail(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)

if not UPSTREAM.exists(): fail(f'Pinned upstream missing: {UPSTREAM}')
try: head = subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'], text=True).strip()
except Exception: fail(f'Cannot verify pinned upstream: {UPSTREAM}')
if head != PIN: fail(f'Pinned upstream SHA mismatch: expected {PIN}, got {head}')
sys.path.insert(0, str(UPSTREAM / 'src'))
from liuyao import cast_board  # noqa: E402

def line_packet(ln):
    return {
        'position': ln.position, 'yin_yang': ln.yin_yang, 'gan': ln.gan, 'zhi': ln.zhi,
        'qin': ln.qin, 'shen': ln.shen, 'is_world': ln.is_world, 'is_response': ln.is_response,
        'is_moving': ln.is_moving, 'change_gan': ln.change_gan, 'change_zhi': ln.change_zhi,
        'change_qin': ln.change_qin, 'dark_move': ln.dark_move, 'day_break': ln.day_break,
        'void': ln.void, 'state': ln.state, 'jin_tui': ln.jin_tui, 'in_grave': ln.in_grave,
        'role': ln.role,
    }

def parse_moving(text):
    try: values = [int(x.strip()) for x in text.split(',') if x.strip()]
    except ValueError: fail(f'Invalid --moving: {text}')
    if not values or any(x < 1 or x > 6 for x in values) or len(set(values)) != len(values): fail(f'Invalid --moving: {text}')
    return values

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixture'); p.add_argument('--hexagram'); p.add_argument('--moving')
    p.add_argument('--month'); p.add_argument('--day'); p.add_argument('--yongshen')
    a = p.parse_args()
    custom = any([a.hexagram, a.moving, a.month, a.day, a.yongshen])
    if a.fixture and custom: fail('Use either --fixture or custom Liuyao arguments, not both')
    if a.fixture:
        if a.fixture != 'canonical-01': fail(f'Unknown fixture: {a.fixture}')
        raw = {'hexagram':'地泽临','moving':[2],'month_zhi':'未','day_gz':'辛卯','yongshen_qin':'妻财'}
        mode = 'FIXTURE'
    else:
        if not all([a.hexagram, a.moving, a.month, a.day]):
            fail('Custom usage: --hexagram NAME --moving 1[,2] --month ZHI --day GANZHI [--yongshen QIN]')
        raw = {'hexagram':a.hexagram,'moving':parse_moving(a.moving),'month_zhi':a.month,'day_gz':a.day,'yongshen_qin':a.yongshen}
        mode = 'CUSTOM'
    try: board = cast_board(raw['hexagram'], raw['moving'], raw['month_zhi'], raw['day_gz'], raw['yongshen_qin'])
    except Exception as exc: fail(f'liuyao rejected input: {exc}', 1)

    if mode == 'FIXTURE':
        if board.hexagram != '地泽临' or board.changed_hexagram != '地雷复': fail('Canonical hexagram fixture drift',1)
        l2, l5, l6 = board.line(2), board.line(5), board.line(6)
        if not (l2.is_world and l2.is_moving and l2.change_zhi == '寅' and l2.jin_tui == '化退神'): fail('World-line fixture drift',1)
        if not (l5.qin == '妻财' and l5.is_response): fail('Yongshen fixture drift',1)
        if not (l6.zhi == '酉' and l6.dark_move and not l6.day_break): fail('Dark-move fixture drift',1)
        structural = 'SUPPORT_EXISTS_BUT_SELF_SIDE_CONSTRAINT_PRESENT'
        predictive = 'NOT_TESTED_RETROSPECTIVE_ONLY'
    else:
        structural = 'BOARD_AND_SELECTED_RULE_FACTS_ONLY'
        predictive = 'NOT_TESTED'

    out = {
        'DOMAIN':'LIUYAO','ENGINE_PIN':PIN,'INPUT_MODE':mode,'RAW_CAST':raw,
        'BOARD_FROZEN':'YES','BOARD_PACKET':{'hexagram':board.hexagram,'changed_hexagram':board.changed_hexagram,'world_pos':board.world_pos,'response_pos':board.response_pos,'xunkong':board.xunkong,'lines':[line_packet(x) for x in board.lines]},
        'YONGSHEN':{'qin':raw['yongshen_qin'],'positions':[x.position for x in board.yongshen_lines] if raw['yongshen_qin'] else []},
        'RULE_TRACE':['UPSTREAM_CAST_BOARD','SELECTED_ZSBU_RULE_FACTS'],
        'STRUCTURAL_OUTPUT':structural,
        'ERROR_BOUNDARY':{'CONSTRUCTION_ERROR':'SEPARATE','REASONING_ERROR':'SEPARATE'},
        'PROVENANCE_STATUS':'PARTIAL_TO_GOOD_SELECTED_RULES','PREDICTIVE_STATUS':predictive,
        'NONCLAIMS':['NO_BLIND_VALIDATION','NO_FORCED_BINARY_WANG_VERDICT']}
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
