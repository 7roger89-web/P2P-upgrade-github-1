#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PIN = '1a5a78b513c0e7b46dfb29f74043bcf978c32a3e'
YINYO_PIN = '1f67eea0ce5a2c49e6851e4eedce507f9c044dd9'
SCRIPT_DIR = Path(__file__).resolve().parent
UPSTREAM = (SCRIPT_DIR / '../../upstreams/liuyao-divination').resolve()
YINYO_UPSTREAM = (SCRIPT_DIR / '../../upstreams/yinyo-liuyao').resolve()
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

if not YINYO_UPSTREAM.exists():
    fail(f'Pinned yinyo upstream missing: {YINYO_UPSTREAM}')
try:
    y_head = subprocess.check_output(['git', '-C', str(YINYO_UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip()
except Exception:
    fail(f'Cannot verify pinned yinyo upstream: {YINYO_UPSTREAM}')
if y_head != YINYO_PIN:
    fail(f'Pinned yinyo upstream SHA mismatch: expected {YINYO_PIN}, got {y_head}')

sys.path.insert(0, str(UPSTREAM / 'src'))
from liuyao import cast_board  # noqa: E402
from liuyao.wuxing import liuqin  # noqa: E402
from liuyao.data import DIZHI_WUXING  # noqa: E402


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


def _missing_yongshen_resolution(board, lens):
    """
    Source-grounded missing-yongshen decision gate.
    Uses only mechanical facts already available from Johnson-Jia board
    plus existing liuqin helper. No fusheng position is fabricated.
    No feishen position is identified because palace-head hidden placement
    has not been computed in this slice.

    Rule order from pinned sources:
    - Yinyo 4.3 L1: 先看日月可否代用 -> "凡用神不现，即以日月为用神"
    - Yinyo 4.3 L3: 飞爻变爻俱无用神方寻伏 -> original text "飞爻变爻俱无用神者，始寻伏神"
      In this slice we check: VISIBLE_MAIN_LINES_ALREADY_CHECKED (main qin) + CHANGED_LINES_CHECK (bian qin)
      FEISHEN_POSITION_NOT_IDENTIFIED because hidden fusheng placement not computed
    - Johnson 02 用神不上卦（伏神）: 在本宫八纯卦中找到该六亲所在之爻，即为伏神
      飞神=主卦上承载伏神的那个爻; 引擎目前以显用神为主，伏神需手工详参
      FUSHEN_POSITION_NOT_COMPUTED in this slice
    """
    main_qin = [ln.qin for ln in board.lines]
    changed_qin = [ln.change_qin for ln in board.lines if ln.is_moving and ln.change_qin]
    changed_positions = [ln.position for ln in board.lines if ln.is_moving and ln.change_qin == lens]

    # month/day mechanical facts
    month_zhi = board.month_zhi
    month_wx = getattr(board, 'month_wx', None)
    # fallback if month_wx missing: derive from DIZHI_WUXING
    if month_wx is None:
        month_wx = DIZHI_WUXING.get(month_zhi)

    day_gz = board.day_gz
    day_zhi = getattr(board, 'day_zhi', None)
    if day_zhi is None:
        # day_gz like 甲子 -> last char is zhi
        day_zhi = day_gz[-1] if day_gz else None
    day_wx = getattr(board, 'day_wx', None)
    if day_wx is None and day_zhi:
        day_wx = DIZHI_WUXING.get(day_zhi)

    palace = board.palace
    palace_wx = board.palace_wx

    # compute month_qin / day_qin via existing liuqin helper (mechanically available)
    try:
        month_qin = liuqin(month_wx, palace_wx) if month_wx and palace_wx else None
    except Exception:
        month_qin = None
    try:
        day_qin = liuqin(day_wx, palace_wx) if day_wx and palace_wx else None
    except Exception:
        day_qin = None

    month_match = (month_qin == lens)
    day_match = (day_qin == lens)

    # Determine status using source-supported order
    # L1: day/month substitution candidate
    # L3: bian yao has yongshen
    # Otherwise: FUSHEN_LOOKUP_REQUIRED (terminal, no fabrication)
    if month_match or day_match:
        status = 'DAY_MONTH_SUBSTITUTION_CANDIDATE'
    elif changed_positions:
        status = 'BIAN_YAO_YONGSHEN_PRESENT'
    else:
        status = 'FUSHEN_LOOKUP_REQUIRED'

    checked_facts = {
        'main_qin': main_qin,
        'changed_qin': changed_qin,
        'changed_yongshen_positions': changed_positions,
        'month': {
            'zhi': month_zhi,
            'wx': month_wx,
            'qin': month_qin,
            'match': month_match,
        },
        'day': {
            'gz': day_gz,
            'zhi': day_zhi,
            'wx': day_wx,
            'qin': day_qin,
            'match': day_match,
        },
        'palace': palace,
        'palace_wx': palace_wx,
        'visible_count': 0,
        'board_facts_used': [
            'lines[].qin',
            'lines[].change_qin (moving)',
            'month_zhi/month_wx',
            'day_gz/day_zhi/day_wx',
            'palace/palace_wx',
            'liuqin helper',
        ],
    }

    source_refs = {
        'Johnson-Jia': {
            'repo': 'Johnson-Jia/liuyao-divination',
            'pin': PIN,
            'path': 'references/02-用神取用.md',
            'section': '用神不上卦（伏神）',
        },
        'Yinyo': {
            'repo': 'xiaoshiyilangzhao1996-droid/yinyo-liuyao',
            'pin': YINYO_PIN,
            'path': 'SKILL.md',
            'section': '4.3 用神不现 -> 伏神取用规则',
        },
    }

    rule_trace = [
        'YINYO_L1_DAY_MONTH_AS_YONGSHEN:凡用神不现即以日月为用神 -> check month_qin/day_qin==lens (MECHANICAL_FACT)',
        'YINYO_L3_QUOTE:飞爻变爻俱无用神者，始寻伏神 -> METHOD_RULE original text',
        'IMPLEMENTATION_INTERPRETATION_L3:VISIBLE_MAIN_LINES_ALREADY_CHECKED=main_qin checked (no visible yongshen) + CHANGED_LINES_CHECK=changed_qin checked; FEISHEN_POSITION_NOT_IDENTIFIED because palace-head hidden fusheng placement not computed in this slice',
        'JOHNSON_FUSHEN_DEF:在本宫八纯卦中找到该六亲所在之爻即为伏神，飞神=主卦上承载伏神的那个爻，引擎目前以显用神为主伏神需手工详参 -> FUSHEN_POSITION_NOT_COMPUTED; FEISHEN_POSITION_NOT_IDENTIFIED; automation stops before palace-head lookup',
        'NO_FABRICATION:伏神position/飞神position/palace-head algorithm NOT invented; FUSHEN_POSITION_NOT_COMPUTED; FEISHEN_POSITION_NOT_IDENTIFIED',
    ]

    automation_boundary = 'VISIBLE_CHECK_DONE+DAY_MONTH_CHECK_DONE+CHANGED_LINES_CHECK_DONE; FUSHEN_POSITION_NOT_COMPUTED; FEISHEN_POSITION_NOT_IDENTIFIED; RETURN_FUSHEN_LOOKUP_REQUIRED_IF_UNRESOLVED'

    return {
        'status': status,
        'checked_facts': checked_facts,
        'source_refs': source_refs,
        'rule_trace': rule_trace,
        'automation_boundary': automation_boundary,
        'mechanical_vs_method_vs_judgment': 'MECHANICAL_FACT=board lines/month/day/palace/liuqin (Johnson-Jia); METHOD_RULE=Yinyo L1+L3 + Johnson fusheng definition (pinned text); IMPLEMENTATION_INTERPRETATION=VISIBLE_MAIN_LINES_ALREADY_CHECKED+CHANGED_LINES_CHECK+DAY_MONTH_CHECK then FUSHEN_LOOKUP_REQUIRED_IF_UNRESOLVED; INTERPRETIVE_JUDGMENT=NONE (no good/bad verdict, no yingqi); FEISHEN_POSITION_NOT_IDENTIFIED; FUSHEN_POSITION_NOT_COMPUTED',
        'fabricated_fusheng_position': False,
        'feishen_position_identified': False,
        'fusheng_position_computed': False,
    }


def lens_packet(board, lens):
    visible_positions = [x.position for x in board.yongshen_lines]
    visible_count = len(board.yongshen_lines)
    base = {
        'lens': lens,
        'visible_yongshen_positions': visible_positions,
        'visible_yongshen_count': visible_count,
        'yongshen_wx': board.yongshen_wx,
        # Correction A: outer status must be neutral, nested resolution carries precise state
        'status': 'VISIBLE_YONGSHEN_FOUND' if board.yongshen_lines else 'VISIBLE_YONGSHEN_MISSING',
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
    if visible_count == 0:
        base['missing_yongshen_resolution'] = _missing_yongshen_resolution(board, lens)
    return base


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
        'YINYO_PIN': YINYO_PIN,
        'CAPABILITY': 'ONE_HEXAGRAM_MULTIPLE_LENSES',
        'INPUT_MODE': input_mode,
        'RAW_CAST': raw,
        'BOARD_FINGERPRINT_SHA256': fingerprint,
        'MECHANICAL_BOARD': mechanics,
        'LENSES': outputs,
        'METHOD_SOURCE': 'Johnson-Jia/liuyao-divination references/02-用神取用.md + yinyo-liuyao SKILL.md 4.3',
        'METHOD_SOURCE_DETAIL': {
            'Johnson-Jia': {
                'repo': 'Johnson-Jia/liuyao-divination',
                'pin': PIN,
                'path': 'references/02-用神取用.md',
                'section': '用神不上卦（伏神）',
            },
            'Yinyo': {
                'repo': 'xiaoshiyilangzhao1996-droid/yinyo-liuyao',
                'pin': YINYO_PIN,
                'path': 'SKILL.md',
                'section': '4.3 用神不现 -> 伏神取用规则',
            },
        },
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
            'NO_FUSHEN_AUTOMATION_FULL',
            'NO_CROSS_TOPIC_CONCLUSION',
            'NO_FORCED_GOOD_BAD_VERDICT',
            'NO_FABRICATED_FUSHEN_POSITION',
        ],
        'MISSING_YONGSHEN_GATE': 'SOURCE_GROUNDED_MECHANICAL_FACTS_PLUS_YINYO_L1_L3_PLUS_JOHNSON_DEF__FUSHEN_LOOKUP_REQUIRED_IF_UNRESOLVED',
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
