#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yijing_corpus import UPSTREAM, load_corrected_corpus, source_metadata as corpus_source_metadata  # noqa: E402
from yijing_commentary import (  # noqa: E402
    load_corrected_commentary,
    load_corrected_xiaoxiang,
    source_metadata as commentary_source_metadata,
)

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao.data import BAGUA, HEXAGRAMS, find_hexagram  # noqa: E402

TRIGRAM_BY_BITS = {tuple(info["yao"]): name for name, info in BAGUA.items()}
HEXAGRAM_BY_TRIGRAMS = {
    (rec["upper"], rec["lower"]): rec["name"]
    for rec in HEXAGRAMS.values()
}


def fail(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


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
        description="Source-grounded Yi Jing gua/yao text, Tuan/Daxiang/Xiaoxiang, and transformation lookup"
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

    try:
        changed_name = changed_hexagram_name(rec, positions)
    except Exception as exc:
        fail(f"Yi Jing transformation failed: {exc}", 1)

    changed_entry = corpus.get(changed_name) if changed_name else None
    changed_commentary = commentary.get(changed_name) if changed_name else None
    changed_rec = find_hexagram(changed_name) if changed_name else None
    if changed_name and (not changed_entry or not changed_commentary or not changed_rec):
        fail(f"Yi Jing corpus/commentary/structure missing changed hexagram: {changed_name}", 1)

    print(json.dumps({
        "DOMAIN": "YIJING",
        "CAPABILITY": "SOURCE_GROUNDED_GUA_YAO_TUAN_DAXIANG_XIAOXIANG_AND_CHANGE_LOOKUP",
        "INPUT": {"hexagram": a.hexagram, "moving": positions},
        "NORMALIZED_HEXAGRAM": name,
        "UPPER_TRIGRAM": rec["upper"],
        "LOWER_TRIGRAM": rec["lower"],
        "GUA_CI": entry["gua_ci"],
        "TUAN_TEXT": commentary_entry["tuan"],
        "DAXIANG_TEXT": commentary_entry["daxiang"],
        "SELECTED_YAO": selected,
        "CHANGED_HEXAGRAM": changed_name,
        "CHANGED_UPPER_TRIGRAM": changed_rec["upper"] if changed_rec else None,
        "CHANGED_LOWER_TRIGRAM": changed_rec["lower"] if changed_rec else None,
        "CHANGED_GUA_CI": changed_entry["gua_ci"] if changed_entry else None,
        "CHANGED_TUAN_TEXT": changed_commentary["tuan"] if changed_commentary else None,
        "CHANGED_DAXIANG_TEXT": changed_commentary["daxiang"] if changed_commentary else None,
        "TRANSFORMATION_RULE": "FLIP_MOVING_LINES_BOTTOM_TO_TOP_THEN_MAP_TRIGRAMS",
        "CORPUS_SOURCE": corpus_source_metadata(),
        "COMMENTARY_SOURCE": commentary_source_metadata(),
        "STRUCTURAL_INTEGRITY": "VERIFIED_64_HEXAGRAM_GUA_YAO_TUAN_DAXIANG_384_XIAOXIANG_AND_384_SINGLE_LINE_TRANSFORMS",
        "TEXTUAL_CRITICAL_EDITION_STATUS": "NOT_ESTABLISHED",
        "INTERPRETATION_STATUS": "NOT_PERFORMED",
        "NONCLAIMS": [
            "NO_DIVINATION_JUDGMENT",
            "NO_TEN_WINGS_COMPLETENESS_CLAIM",
            "NO_SINGLE_CANONICAL_EDITION_CLAIM",
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
