#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yijing_corpus import (  # noqa: E402
    PIN,
    UPSTREAM,
    YijingTextEvidenceError,
    gua_ci_evidence,
    load_corrected_corpus,
    source_metadata as corpus_source_metadata,
    yao_text_evidence,
    validate_corpus_evidence,
)
from yijing_commentary import (  # noqa: E402
    daxiang_evidence,
    load_corrected_commentary,
    load_corrected_xiaoxiang,
    load_special_xiaoxiang,
    source_metadata as commentary_source_metadata,
    special_xiaoxiang_evidence,
    tuan_evidence,
    validate_marker_evidence,
    validate_special_xiaoxiang_evidence,
    validate_xiaoxiang_evidence,
    xiaoxiang_evidence,
)

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao.data import BAGUA, HEXAGRAMS, find_hexagram  # noqa: E402

TRIGRAM_BY_BITS = {tuple(info["yao"]): name for name, info in BAGUA.items()}
HEXAGRAM_BY_TRIGRAMS = {
    (rec["upper"], rec["lower"]): rec["name"]
    for rec in HEXAGRAMS.values()
}
ALL_SIX = {1, 2, 3, 4, 5, 6}
SPECIAL_LABEL_BY_HEXAGRAM = {"乾为天": "用九", "坤为地": "用六"}


def fail(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


# ---------------------------------------------------------------------------
# Selected-text evidence: exact-coverage, fail-closed validation of the packet.
# Every textual field actually emitted must carry truthful per-field provenance;
# evidence for absent fields is rejected, and missing evidence fails the run.
# ---------------------------------------------------------------------------

def _required_text_evidence(packet):
    name = packet["NORMALIZED_HEXAGRAM"]
    required = {
        ("GUA_CI", name, None),
        ("TUAN_TEXT", name, None),
        ("DAXIANG_TEXT", name, None),
    }
    for sel in packet["SELECTED_YAO"]:
        required.add(("SELECTED_YAO[].text", name, sel["label"]))
        required.add(("SELECTED_YAO[].xiaoxiang", name, sel["label"]))
    special = packet["SPECIAL_YAO_CANDIDATE"]
    if special:
        required.add(("SPECIAL_YAO_CANDIDATE.text", name, special["label"]))
        required.add(("SPECIAL_YAO_CANDIDATE.xiaoxiang", name, special["label"]))
    changed = packet["CHANGED_HEXAGRAM"]
    if changed:
        required.add(("CHANGED_GUA_CI", changed, None))
        required.add(("CHANGED_TUAN_TEXT", changed, None))
        required.add(("CHANGED_DAXIANG_TEXT", changed, None))
    return required


def _selected_yao(packet, label):
    matches = [s for s in packet["SELECTED_YAO"] if s["label"] == label]
    if len(matches) != 1:
        fail(f"Expected exactly one SELECTED_YAO entry for {label!r}, found {len(matches)}")
    return matches[0]


def _emitted_text_and_kind(packet, key):
    field, _hexagram, label = key
    if field == "GUA_CI":
        return packet["GUA_CI"], "corpus"
    if field == "CHANGED_GUA_CI":
        return packet["CHANGED_GUA_CI"], "corpus"
    if field == "TUAN_TEXT":
        return packet["TUAN_TEXT"], "marker"
    if field == "DAXIANG_TEXT":
        return packet["DAXIANG_TEXT"], "marker"
    if field == "CHANGED_TUAN_TEXT":
        return packet["CHANGED_TUAN_TEXT"], "marker"
    if field == "CHANGED_DAXIANG_TEXT":
        return packet["CHANGED_DAXIANG_TEXT"], "marker"
    if field == "SELECTED_YAO[].text":
        return _selected_yao(packet, label)["text"], "corpus"
    if field == "SELECTED_YAO[].xiaoxiang":
        return _selected_yao(packet, label)["xiaoxiang"], "xiaoxiang"
    if field == "SPECIAL_YAO_CANDIDATE.text":
        return packet["SPECIAL_YAO_CANDIDATE"]["text"], "corpus"
    if field == "SPECIAL_YAO_CANDIDATE.xiaoxiang":
        return packet["SPECIAL_YAO_CANDIDATE"]["xiaoxiang"], "special_xiaoxiang"
    fail(f"Unknown text evidence field: {field!r}")


def validate_text_evidence_packet(packet):
    """Production seam: reject any packet whose TEXT_EVIDENCE is missing,
    extra, duplicated, or not truthful against the pinned raw sources."""
    evidence = packet.get("TEXT_EVIDENCE")
    if not isinstance(evidence, list) or not evidence:
        fail("TEXT_EVIDENCE must be a non-empty list")
    required = _required_text_evidence(packet)
    seen = set()
    for entry in evidence:
        if not isinstance(entry, dict):
            fail(f"TEXT_EVIDENCE entries must be dicts: {entry!r}")
        key = (entry.get("field"), entry.get("hexagram"), entry.get("line_label"))
        if key not in required:
            fail(f"Text evidence for a field absent from this packet: {key!r}")
        if key in seen:
            fail(f"Duplicate text evidence for: {key!r}")
        seen.add(key)
        emitted, kind = _emitted_text_and_kind(packet, key)
        try:
            if kind == "corpus":
                validate_corpus_evidence(entry, emitted)
            elif kind == "marker":
                validate_marker_evidence(entry, emitted)
            elif kind == "xiaoxiang":
                validate_xiaoxiang_evidence(entry, emitted)
            else:
                validate_special_xiaoxiang_evidence(entry, emitted)
        except YijingTextEvidenceError as exc:
            fail(
                f"Text evidence rejected for {key[0]} {key[1]} {key[2]}: {exc}", 1
            )
    missing = sorted(required - seen)
    if missing:
        fail(f"Missing text evidence for emitted fields: {missing}", 1)
    return True


def parse_positions(text):
    if text is None:
        return []
    try:
        out = [int(x.strip()) for x in text.split(",") if x.strip()]
    except ValueError:
        fail(f"Invalid --moving: {text}")
    if not out or any(x < 1 or x > 6 for x in out) or len(out) != len(set(out)):
        fail(f"Invalid --moving: {text}")
    return out


def yao_label(rec, position):
    bits = BAGUA[rec["lower"]]["yao"] + BAGUA[rec["upper"]]["yao"]
    stem = "九" if bits[position - 1] else "六"
    if position == 1:
        return f"初{stem}"
    if position == 6:
        return f"上{stem}"
    return f"{stem}{['', '', '二', '三', '四', '五'][position]}"


def changed_hexagram_name(rec, positions):
    """Flip moving lines bottom-to-top and map the resulting trigrams to one of the 64 hexagrams."""
    if not positions:
        return None
    bits = list(BAGUA[rec["lower"]]["yao"] + BAGUA[rec["upper"]]["yao"])
    for pos in positions:
        bits[pos - 1] = 1 - bits[pos - 1]
    changed_lower = TRIGRAM_BY_BITS[tuple(bits[:3])]
    changed_upper = TRIGRAM_BY_BITS[tuple(bits[3:])]
    name = HEXAGRAM_BY_TRIGRAMS.get((changed_upper, changed_lower))
    if not name:
        raise RuntimeError(
            f"Cannot map transformed trigrams to hexagram: upper={changed_upper}, lower={changed_lower}"
        )
    return name


def main():
    p = argparse.ArgumentParser(
        description="Source-grounded Yi Jing gua/yao text, Tuan/Daxiang/Xiaoxiang, special-line candidates, and transformation lookup"
    )
    p.add_argument("--hexagram", required=True, help="Full name or upstream alias, e.g. 地山谦 or 谦")
    p.add_argument("--moving", help="Optional line positions, e.g. 2 or 2,3")
    a = p.parse_args()

    rec = find_hexagram(a.hexagram)
    if not rec:
        fail(f"Unknown hexagram: {a.hexagram}")
    positions = parse_positions(a.moving)

    corpus = load_corrected_corpus()
    commentary = load_corrected_commentary()
    xiaoxiang = load_corrected_xiaoxiang()
    special_xiaoxiang = load_special_xiaoxiang()
    name = rec["name"]
    entry = corpus.get(name)
    commentary_entry = commentary.get(name)
    xiaoxiang_entry = xiaoxiang.get(name)
    if not entry:
        fail(f"Yi Jing corpus missing normalized hexagram: {name}", 1)
    if not commentary_entry:
        fail(f"Yi Jing commentary missing normalized hexagram: {name}", 1)
    if not xiaoxiang_entry:
        fail(f"Yi Jing Xiaoxiang missing normalized hexagram: {name}", 1)

    selected = []
    for pos in positions:
        label = yao_label(rec, pos)
        text = entry.get("yao", {}).get(label)
        line_xiaoxiang = xiaoxiang_entry.get(label)
        if not text:
            fail(f"Yi Jing corpus missing {name} {label}", 1)
        if not line_xiaoxiang:
            fail(f"Yi Jing Xiaoxiang missing {name} {label}", 1)
        selected.append({
            "position": pos,
            "label": label,
            "text": text,
            "xiaoxiang": line_xiaoxiang,
        })

    special_candidate = None
    special_label = SPECIAL_LABEL_BY_HEXAGRAM.get(name)
    if special_label and len(positions) == 6 and set(positions) == ALL_SIX:
        special_record = special_xiaoxiang.get(name)
        special_text = entry.get("yao", {}).get(special_label)
        if not special_record or special_record.get("label") != special_label or not special_text:
            fail(f"Yi Jing special-line source missing {name} {special_label}", 1)
        special_candidate = {
            "label": special_label,
            "text": special_text,
            "xiaoxiang": special_record["xiaoxiang"],
            "exposure_condition": "ALL_SIX_REGULAR_LINES_LISTED_AS_MOVING",
            "interpretive_priority": "NOT_ASSERTED",
        }

    try:
        changed_name = changed_hexagram_name(rec, positions)
    except Exception as exc:
        fail(f"Yi Jing transformation failed: {exc}", 1)

    changed_entry = corpus.get(changed_name) if changed_name else None
    changed_commentary = commentary.get(changed_name) if changed_name else None
    changed_rec = find_hexagram(changed_name) if changed_name else None
    if changed_name and (not changed_entry or not changed_commentary or not changed_rec):
        fail(f"Yi Jing corpus/commentary/structure missing changed hexagram: {changed_name}", 1)

    # Per-field text evidence: entries exist only for fields this packet
    # actually emits. Yao text (data/zhouyi.json) and Xiaoxiang
    # (docs/易经六十四卦.md) keep independent provenance surfaces.
    text_evidence = [
        gua_ci_evidence(name),
        tuan_evidence(name, commentary_entry["tuan"]),
        daxiang_evidence(name, commentary_entry["daxiang"]),
    ]
    for sel in selected:
        text_evidence.append(yao_text_evidence(name, sel["label"]))
        text_evidence.append(xiaoxiang_evidence(name, sel["label"], sel["xiaoxiang"]))
    if special_candidate:
        text_evidence.append(
            yao_text_evidence(name, special_label, field="SPECIAL_YAO_CANDIDATE.text")
        )
        text_evidence.append(
            special_xiaoxiang_evidence(name, special_label, special_candidate["xiaoxiang"])
        )
    if changed_name:
        text_evidence.extend([
            gua_ci_evidence(changed_name, field="CHANGED_GUA_CI"),
            tuan_evidence(changed_name, changed_commentary["tuan"], field="CHANGED_TUAN_TEXT"),
            daxiang_evidence(changed_name, changed_commentary["daxiang"], field="CHANGED_DAXIANG_TEXT"),
        ])

    packet = {
        "DOMAIN": "YIJING",
        "DOMAIN": "YIJING",
        "CAPABILITY": "SOURCE_GROUNDED_GUA_YAO_TUAN_DAXIANG_XIAOXIANG_SPECIAL_YAO_CANDIDATE_AND_CHANGE_LOOKUP",
        "INPUT": {"hexagram": a.hexagram, "moving": positions},
        "NORMALIZED_HEXAGRAM": name,
        "UPPER_TRIGRAM": rec["upper"],
        "LOWER_TRIGRAM": rec["lower"],
        "GUA_CI": entry["gua_ci"],
        "TUAN_TEXT": commentary_entry["tuan"],
        "DAXIANG_TEXT": commentary_entry["daxiang"],
        "SELECTED_YAO": selected,
        "SPECIAL_YAO_CANDIDATE": special_candidate,
        "CHANGED_HEXAGRAM": changed_name,
        "CHANGED_UPPER_TRIGRAM": changed_rec["upper"] if changed_rec else None,
        "CHANGED_LOWER_TRIGRAM": changed_rec["lower"] if changed_rec else None,
        "CHANGED_GUA_CI": changed_entry["gua_ci"] if changed_entry else None,
        "CHANGED_TUAN_TEXT": changed_commentary["tuan"] if changed_commentary else None,
        "CHANGED_DAXIANG_TEXT": changed_commentary["daxiang"] if changed_commentary else None,
        "TEXT_EVIDENCE": text_evidence,
        "TRANSFORMATION_EVIDENCE": {
            "structure_repo": "Johnson-Jia/liuyao-divination",
            "structure_pin": PIN,
            "structure_source_path": "src/liuyao/data.py",
            "structure_symbols": ["BAGUA", "HEXAGRAMS", "find_hexagram"],
            "p2p_implementation": "run_yijing_capability.changed_hexagram_name",
            "rule": "FLIP_MOVING_LINES_BOTTOM_TO_TOP_THEN_MAP_TRIGRAMS",
            "mechanical_verification": "VERIFIED_AGAINST_384_UPSTREAM_CAST_BOARD_SINGLE_LINE_CASES",
        },
        "TRANSFORMATION_RULE": "FLIP_MOVING_LINES_BOTTOM_TO_TOP_THEN_MAP_TRIGRAMS",
        "CORPUS_SOURCE": corpus_source_metadata(),
        "COMMENTARY_SOURCE": commentary_source_metadata(),
        "STRUCTURAL_INTEGRITY": "VERIFIED_64_HEXAGRAM_GUA_YAO_TUAN_DAXIANG_384_XIAOXIANG_2_SPECIAL_YAO_AND_384_SINGLE_LINE_TRANSFORMS",
        "TEXTUAL_CRITICAL_EDITION_STATUS": "NOT_ESTABLISHED",
        "INTERPRETATION_STATUS": "NOT_PERFORMED",
        "NONCLAIMS": [
            "NO_DIVINATION_JUDGMENT",
            "NO_SPECIAL_YAO_PRIORITY_RULE",
            "NO_TEN_WINGS_COMPLETENESS_CLAIM",
            "NO_SINGLE_CANONICAL_EDITION_CLAIM",
            "NO_HISTORICAL_PRIMARY_SOURCE_VALIDATION",
        ],
    }

    # Fail closed: the packet is not emitted unless its evidence is exactly
    # covering and independently re-proven against the pinned raw sources.
    try:
        validate_text_evidence_packet(packet)
    except YijingTextEvidenceError as exc:
        fail(f"Text evidence validation failed: {exc}", 1)
    packet["TEXT_EVIDENCE_COVERAGE"] = {
        "PRESENT_SOURCE_BOUND_TEXT_FIELDS": len(_required_text_evidence(packet)),
        "TEXT_EVIDENCE_FIELDS": len(packet["TEXT_EVIDENCE"]),
        "EXACT_COVERAGE": True,
    }

    print(json.dumps(packet, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
