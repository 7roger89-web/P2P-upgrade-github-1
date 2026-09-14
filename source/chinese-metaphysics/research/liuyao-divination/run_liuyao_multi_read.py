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
from liuyao.data import DIZHI_WUXING, HEXAGRAMS  # noqa: E402


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


def _johnson_unique_hexagram_records():
    """
    Johnson's HEXAGRAMS is an index keyed by BOTH full name and single-char alias
    (128 keys -> 64 unique records). Dedupe by record name so a structural scan
    counts each hexagram once. No new mapping is introduced: every record here is
    Johnson's own dict object from Johnson's own data.py.
    """
    unique = {}
    for rec in HEXAGRAMS.values():
        unique[rec['name']] = rec
    return list(unique.values())


def _pure_palace_record(palace):
    """
    Derive 本宫八纯卦 (palace head / 首卦) from EXISTING Johnson HEXAGRAMS data.

    Structural proof required by Johnson's own record shape
    (name, alias, upper, lower, palace, palace_wx, world):
        record.palace == P  AND  record.upper == P  AND  record.lower == P

    No handwritten {"乾": "乾为天", ...} map, no string concatenation.
    Returns (record_or_None, selection_proof). Fails closed (record None) unless
    EXACTLY ONE record satisfies the condition.
    """
    records = _johnson_unique_hexagram_records()
    hits = [
        r for r in records
        if r['palace'] == palace and r['upper'] == palace and r['lower'] == palace
    ]
    proof = {
        'source': 'Johnson-Jia/liuyao-divination src/liuyao/data.py HEXAGRAMS',
        'pin': PIN,
        'condition': 'record.palace == P AND record.upper == P AND record.lower == P',
        'records_scanned': len(records),
        'index_keys_scanned': len(HEXAGRAMS),
        'palace': palace,
        'hits': [r['name'] for r in hits],
        'hit_count': len(hits),
        'unique': len(hits) == 1,
        'handwritten_palace_map_used': False,
    }
    return (hits[0] if len(hits) == 1 else None), proof


def _fushen_placement(board, lens):
    """
    JOHNSON-NATIVE FUSHEN PLACEMENT (mechanical position only).

    Runs ONLY when the nested missing-yongshen gate has already resolved to
    FUSHEN_LOOKUP_REQUIRED. Source rule (Johnson references/02-用神取用.md 四):
        在本宫八纯卦（首卦）中找到该六亲所在之爻，即为伏神
        飞神 = 主卦上承载伏神的那个爻

    Nothing here is computed by hand:
      - 本宫八纯卦 comes from Johnson HEXAGRAMS via a structural scan;
      - the pure-palace board comes from Johnson cast_board() with the minimal
        legal moving-line input ([] -> static board);
      - the 伏神 candidates are the pure board's own lines whose qin == lens;
      - the 飞神 is the MAIN board's own line at the confirmed candidate position.

    All candidates are preserved; none is arbitrarily selected. No strength,
    生克, 旺衰, 得出, or good/bad judgment is produced here.
    """
    pure_rec, proof = _pure_palace_record(board.palace)
    if pure_rec is None:
        # FAIL CLOSED: do not guess a palace head.
        return {
            'status': 'SOURCE_DATA_INCONSISTENT_PURE_PALACE',
            'pure_palace_hexagram': None,
            'pure_palace_unique': False,
            'pure_palace_selection': proof,
            'pure_palace_board_built': False,
            'candidates': [],
            'candidate_count': 0,
            'position_source': 'NONE_PURE_PALACE_NOT_UNIQUELY_DERIVABLE_FROM_JOHNSON_DATA',
            'fail_closed': True,
            'judgment_emitted': False,
        }

    pure_name = pure_rec['name']
    try:
        # Minimal legal moving-line input verified against real cast_board contract:
        # moving=[] is accepted and yields a static board (changed_hexagram == itself).
        pure_board = cast_board(pure_name, [], board.month_zhi, board.day_gz, lens)
    except Exception as exc:
        return {
            'status': 'SOURCE_DATA_INCONSISTENT_PURE_PALACE_BOARD',
            'pure_palace_hexagram': pure_name,
            'pure_palace_unique': True,
            'pure_palace_selection': proof,
            'pure_palace_board_built': False,
            'candidates': [],
            'candidate_count': 0,
            'position_source': f'NONE_JOHNSON_CAST_BOARD_REJECTED_PURE_PALACE:{exc}',
            'fail_closed': True,
            'judgment_emitted': False,
        }

    # 伏神 candidates = Johnson-generated pure-palace lines carrying the requested qin.
    candidates = [
        {
            'position': ln.position,
            'gan': ln.gan,
            'zhi': ln.zhi,
            'wx': ln.wx,
            'qin': ln.qin,
        }
        for ln in pure_board.lines
        if ln.qin == lens
    ]

    if not candidates:
        # FAIL CLOSED: explicit source/data inconsistency, no fabricated position.
        return {
            'status': 'SOURCE_DATA_INCONSISTENT_NO_FUSHEN_CANDIDATE',
            'pure_palace_hexagram': pure_name,
            'pure_palace_unique': True,
            'pure_palace_selection': proof,
            'pure_palace_board_built': True,
            'pure_palace_board_qin': [ln.qin for ln in pure_board.lines],
            'candidates': [],
            'candidate_count': 0,
            'position_source': 'NONE_REQUESTED_QIN_ABSENT_FROM_JOHNSON_PURE_PALACE_BOARD',
            'fail_closed': True,
            'judgment_emitted': False,
        }

    return {
        'status': 'FUSHEN_PLACEMENT_IDENTIFIED',
        'pure_palace_hexagram': pure_name,
        'pure_palace_unique': True,
        'pure_palace_selection': proof,
        'pure_palace_board_built': True,
        'pure_palace_board_qin': [ln.qin for ln in pure_board.lines],
        'pure_palace_board_source': {
            'engine': 'Johnson-Jia/liuyao-divination cast_board()',
            'pin': PIN,
            'call': {
                'hexagram': pure_name,
                'moving': [],
                'month_zhi': board.month_zhi,
                'day_gz': board.day_gz,
                'yongshen_qin': lens,
            },
            'manual_line_calculation': False,
        },
        'candidates': candidates,
        'candidate_count': len(candidates),
        'all_candidates_preserved': True,
        'arbitrary_selection_made': False,
        'position_source': (
            'Johnson cast_board() pure-palace board lines where line.qin == requested lens '
            f'(pure_palace_hexagram={pure_name}; Johnson-Jia/liuyao-divination@{PIN} '
            'references/02-用神取用.md 四、用神不上卦（伏神）)'
        ),
        'fail_closed': False,
        'judgment_emitted': False,
    }


def _feishen_placement(board, fushen):
    """
    飞神 = the MAIN-board line at the SAME position as a confirmed 伏神 candidate.

    Legitimate ONLY because the fushen position has already been mechanically
    established by Johnson. Emits existing main-board mechanical facts only.
    Not a global relabeling of all main lines, and no 生克 / suppression judgment.
    """
    if fushen.get('status') != 'FUSHEN_PLACEMENT_IDENTIFIED':
        return {
            'status': 'FEISHEN_POSITION_NOT_IDENTIFIED',
            'candidates': [],
            'candidate_count': 0,
            'position_source': 'NONE_FUSHEN_POSITION_NOT_ESTABLISHED',
            'judgment_emitted': False,
        }

    main_by_pos = {ln.position: ln for ln in board.lines}
    candidates = []
    for cand in fushen['candidates']:
        ln = main_by_pos.get(cand['position'])
        if ln is None:
            continue
        candidates.append({
            'position': ln.position,
            'gan': ln.gan,
            'zhi': ln.zhi,
            'wx': ln.wx,
            'qin': ln.qin,
            'state': ln.state,
            'void': ln.void,
            'month_break': ln.month_break,
            'day_break': ln.day_break,
            'is_moving': ln.is_moving,
            'fushen_position': cand['position'],
        })

    if not candidates:
        return {
            'status': 'SOURCE_DATA_INCONSISTENT_NO_FEISHEN_LINE',
            'candidates': [],
            'candidate_count': 0,
            'position_source': 'NONE_MAIN_BOARD_LINE_AT_CONFIRMED_FUSHEN_POSITION_MISSING',
            'fail_closed': True,
            'judgment_emitted': False,
        }

    return {
        'status': 'FEISHEN_POSITION_IDENTIFIED',
        'candidates': candidates,
        'candidate_count': len(candidates),
        'position_source': (
            'main-board line at the SAME position as the Johnson-established fushen '
            'candidate position (Johnson-Jia/liuyao-divination@' + PIN + ' '
            'references/02-用神取用.md: 飞神 = 主卦上承载伏神的那个爻)'
        ),
        'derived_from_confirmed_fushen_position': True,
        'all_main_lines_called_feishen': False,
        'judgment_emitted': False,
    }


def _missing_yongshen_resolution(board, lens):
    """
    Source-grounded missing-yongshen decision gate.
    Uses only mechanical facts already available from the Johnson-Jia board
    plus the existing liuqin helper. No fushen position is fabricated.

    Rule order from pinned sources:
    - Yinyo 4.3 L1: 先看日月可否代用 -> "凡用神不现，即以日月为用神"
      => DAY_MONTH_SUBSTITUTION_CANDIDATE (unchanged; no palace-head lookup)
    - Yinyo 4.3 L3: 飞爻变爻俱无用神方寻伏 -> original text "飞爻变爻俱无用神者，始寻伏神"
      checked as VISIBLE_MAIN_LINES_ALREADY_CHECKED (main qin) + CHANGED_LINES_CHECK (bian qin)
      => BIAN_YAO_YONGSHEN_PRESENT (unchanged; no palace-head lookup)
    - Johnson 02 用神不上卦（伏神）: 在本宫八纯卦（首卦）中找到该六亲所在之爻，即为伏神；
      飞神 = 主卦上承载伏神的那个爻
      => the previously terminal FUSHEN_LOOKUP_REQUIRED advances to JOHNSON-NATIVE
         placement: the palace head is derived structurally from Johnson HEXAGRAMS
         (record.palace == P AND record.upper == P AND record.lower == P), the
         pure-palace board is produced by Johnson cast_board(), the fushen
         candidates are the pure board lines whose qin == the requested lens, and
         the feishen is the main board line at the confirmed candidate position.

    PLACEMENT ONLY. No fushen strength, 得出, 飞神生克伏神, 旺衰, 吉凶 or 应期
    judgment is produced here.
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
    # Otherwise: palace-head fushen placement (Johnson-native), advancing the
    #            previously terminal FUSHEN_LOOKUP_REQUIRED.
    fushen_placement = None
    feishen_placement = None
    gate_status_before_placement = None
    if month_match or day_match:
        status = 'DAY_MONTH_SUBSTITUTION_CANDIDATE'
    elif changed_positions:
        status = 'BIAN_YAO_YONGSHEN_PRESENT'
    else:
        # ONLY this branch may invoke the palace-head lookup. The DAY_MONTH and
        # BIAN branches above must remain unchanged and never build a pure board.
        gate_status_before_placement = 'FUSHEN_LOOKUP_REQUIRED'
        fushen_placement = _fushen_placement(board, lens)
        feishen_placement = _feishen_placement(board, fushen_placement)
        status = fushen_placement['status']

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

    # DAY_MONTH_SUBSTITUTION_CANDIDATE and BIAN_YAO_YONGSHEN_PRESENT keep their
    # pre-existing trace wording verbatim: those branches do not advance in this slice.
    rule_trace = [
        'YINYO_L1_DAY_MONTH_AS_YONGSHEN:凡用神不现即以日月为用神 -> check month_qin/day_qin==lens (MECHANICAL_FACT)',
        'YINYO_L3_QUOTE:飞爻变爻俱无用神者，始寻伏神 -> METHOD_RULE original text',
        'IMPLEMENTATION_INTERPRETATION_L3:VISIBLE_MAIN_LINES_ALREADY_CHECKED=main_qin checked (no visible yongshen) + CHANGED_LINES_CHECK=changed_qin checked; FEISHEN_POSITION_NOT_IDENTIFIED because palace-head hidden fusheng placement not computed in this slice',
        'JOHNSON_FUSHEN_DEF:在本宫八纯卦中找到该六亲所在之爻即为伏神，飞神=主卦上承载伏神的那个爻，引擎目前以显用神为主伏神需手工详参 -> FUSHEN_POSITION_NOT_COMPUTED; FEISHEN_POSITION_NOT_IDENTIFIED; automation stops before palace-head lookup',
        'NO_FABRICATION:伏神position/飞神position/palace-head algorithm NOT invented; FUSHEN_POSITION_NOT_COMPUTED; FEISHEN_POSITION_NOT_IDENTIFIED',
    ]

    automation_boundary = 'VISIBLE_CHECK_DONE+DAY_MONTH_CHECK_DONE+CHANGED_LINES_CHECK_DONE; FUSHEN_POSITION_NOT_COMPUTED; FEISHEN_POSITION_NOT_IDENTIFIED; RETURN_FUSHEN_LOOKUP_REQUIRED_IF_UNRESOLVED'

    mechanical_vs_method_vs_judgment = 'MECHANICAL_FACT=board lines/month/day/palace/liuqin (Johnson-Jia); METHOD_RULE=Yinyo L1+L3 + Johnson fusheng definition (pinned text); IMPLEMENTATION_INTERPRETATION=VISIBLE_MAIN_LINES_ALREADY_CHECKED+CHANGED_LINES_CHECK+DAY_MONTH_CHECK then FUSHEN_LOOKUP_REQUIRED_IF_UNRESOLVED; INTERPRETIVE_JUDGMENT=NONE (no good/bad verdict, no yingqi); FEISHEN_POSITION_NOT_IDENTIFIED; FUSHEN_POSITION_NOT_COMPUTED'

    if fushen_placement is not None:
        # Palace-head lookup ran (FUSHEN_LOOKUP_REQUIRED branch only).
        pure_name = fushen_placement['pure_palace_hexagram']
        cand_pos = [c['position'] for c in fushen_placement['candidates']]
        rule_trace = [
            'YINYO_L1_DAY_MONTH_AS_YONGSHEN:凡用神不现即以日月为用神 -> check month_qin/day_qin==lens (MECHANICAL_FACT)',
            'YINYO_L3_QUOTE:飞爻变爻俱无用神者，始寻伏神 -> METHOD_RULE original text',
            'IMPLEMENTATION_INTERPRETATION_L3:VISIBLE_MAIN_LINES_ALREADY_CHECKED=main_qin checked (no visible yongshen) + CHANGED_LINES_CHECK=changed_qin checked; both empty -> FUSHEN_LOOKUP_REQUIRED reached, palace-head lookup now permitted',
            'JOHNSON_FUSHEN_DEF:在本宫八纯卦（首卦）中找到该六亲所在之爻即为伏神，飞神=主卦上承载伏神的那个爻 -> METHOD_RULE pinned text (references/02-用神取用.md 四)',
            f'JOHNSON_PURE_PALACE_DERIVATION:本宫八纯卦 selected structurally from Johnson HEXAGRAMS by palace==P AND upper==P AND lower==P (P={board.palace}) -> {pure_name}; unique={fushen_placement["pure_palace_unique"]}; hits={fushen_placement["pure_palace_selection"]["hits"]}; NO handwritten palace map (MECHANICAL_FACT)',
            f'JOHNSON_PURE_PALACE_BOARD:cast_board({pure_name}, moving=[], month_zhi={board.month_zhi}, day_gz={board.day_gz}, yongshen_qin={lens}) -> pure board built by Johnson engine, NO manual line calculation (MECHANICAL_FACT)',
            f'FUSHEN_POSITION_COMPUTED:伏神 candidates = pure-palace lines with qin=={lens} -> positions {cand_pos}; all candidates preserved, none arbitrarily selected (MECHANICAL_FACT)',
            f'FEISHEN_POSITION_IDENTIFIED:飞神 = main-board ({board.hexagram}) line(s) at confirmed fushen position(s) {cand_pos}; identified ONLY because the fushen position is now mechanically established; not a global relabeling of all main lines (MECHANICAL_FACT)',
            'NO_FABRICATION:伏神position/飞神position/palace-head all derived from Johnson HEXAGRAMS + Johnson cast_board; 纳甲/六亲/八宫 tables NOT duplicated; NO separate fushen doctrine implemented',
            'AUTOMATION_STOPS_AT_PLACEMENT:NO 伏神得出判断, NO 飞神生克伏神, NO 日月生扶伏神, NO 旺衰, NO 空破利害, NO 吉凶, NO 应期, NO prediction (INTERPRETIVE_JUDGMENT=NONE)',
        ]
        automation_boundary = (
            'VISIBLE_CHECK_DONE+DAY_MONTH_CHECK_DONE+CHANGED_LINES_CHECK_DONE; '
            'PURE_PALACE_DERIVED_FROM_JOHNSON_HEXAGRAMS; '
            'PURE_PALACE_BOARD_BUILT_BY_JOHNSON_CAST_BOARD; '
            'FUSHEN_POSITION_COMPUTED; FEISHEN_POSITION_IDENTIFIED; '
            'STOP_AFTER_MECHANICAL_PLACEMENT; '
            'DEFERRED=伏神得出+飞神生克伏神+日月生扶伏神+伏神旺衰+飞神空破利害+吉凶+应期+PREDICTION+BLIND_VALIDATION'
        )
        mechanical_vs_method_vs_judgment = (
            'MECHANICAL_FACT=board lines/month/day/palace/liuqin + Johnson HEXAGRAMS palace-head record '
            '+ Johnson cast_board pure-palace board lines (Johnson-Jia); '
            'METHOD_RULE=Yinyo L1+L3 + Johnson 伏神/飞神 definition (references/02-用神取用.md 四, pinned text); '
            'IMPLEMENTATION_INTERPRETATION=VISIBLE+DAY_MONTH+CHANGED checks then structural palace-head scan '
            '(palace==upper==lower) then qin==lens scan on the Johnson-built pure board, feishen=main line at same position; '
            'INTERPRETIVE_JUDGMENT=NONE (no 得出/生克/旺衰/吉凶/应期 verdict); '
            'FUSHEN_PLACEMENT_IDENTIFIED != FUSHEN_EFFECTIVE; FEISHEN_POSITION_IDENTIFIED != FEISHEN_SUPPRESSES_FUSHEN'
        )

    return {
        'status': status,
        'gate_status_before_placement': gate_status_before_placement,
        'checked_facts': checked_facts,
        'source_refs': source_refs,
        'rule_trace': rule_trace,
        'automation_boundary': automation_boundary,
        'mechanical_vs_method_vs_judgment': mechanical_vs_method_vs_judgment,
        'fabricated_fusheng_position': False,
        'fushen_placement': fushen_placement,
        'feishen_placement': feishen_placement,
        'fushen_position_computed': bool(
            fushen_placement and fushen_placement['status'] == 'FUSHEN_PLACEMENT_IDENTIFIED'
        ),
        'feishen_position_identified': bool(
            feishen_placement and feishen_placement['status'] == 'FEISHEN_POSITION_IDENTIFIED'
        ),
        'fushen_effectiveness': 'NOT_ASSESSED',
        'good_bad_judgment': 'NOT_EMITTED',
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
            'NO_FUSHEN_STRENGTH_OR_DECHU_JUDGMENT',
            'NO_FEISHEN_SHENGKE_FUSHEN_JUDGMENT',
            'NO_RIYUE_SHENGFU_FUSHEN_JUDGMENT',
            'NO_FUSHEN_WANGSHUAI',
            'NO_YINGQI',
            'FUSHEN_PLACEMENT_IDENTIFIED != FUSHEN_EFFECTIVE',
            'FEISHEN_POSITION_IDENTIFIED != FEISHEN_SUPPRESSES_FUSHEN',
            'MECHANICAL_PLACEMENT != GOOD_BAD_JUDGMENT',
            'ENGINEERING_PASS != METHOD_VALIDITY',
        ],
        'MISSING_YONGSHEN_GATE': 'SOURCE_GROUNDED_MECHANICAL_FACTS_PLUS_YINYO_L1_L3_PLUS_JOHNSON_DEF__JOHNSON_NATIVE_FUSHEN_PLACEMENT_WHEN_LOOKUP_REQUIRED',
        'FUSHEN_PLACEMENT_SOURCE': {
            'PURE_PALACE_LOOKUP': 'Johnson-Jia/liuyao-divination src/liuyao/data.py HEXAGRAMS structural scan (record.palace == P AND record.upper == P AND record.lower == P)',
            'PURE_PALACE_BOARD': 'Johnson-Jia/liuyao-divination cast_board() with minimal legal moving input []',
            'FUSHEN_CANDIDATES': 'pure-palace board lines where line.qin == requested lens',
            'FEISHEN_CANDIDATES': 'main board line at the confirmed fushen candidate position',
            'HARDCODED_PALACE_MAP': 'NO',
            'MANUAL_NAJIA': 'NO',
            'MANUAL_LIUQIN': 'NO',
            'SEPARATE_FUSHEN_DOCTRINE': 'NO',
            'PIN': PIN,
        },
        'AUTOMATION_BOUNDARY': 'STOPS_AT_MECHANICAL_FUSHEN_FEISHEN_PLACEMENT',
        'DEFERRED_NOT_IMPLEMENTED': [
            '伏神得出判断',
            '飞神生克伏神 judgment',
            '日月生扶伏神 judgment',
            '伏神旺衰',
            '飞神空破是否利于伏神',
            '吉凶',
            '应期',
            'prediction',
            'blind validation',
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
