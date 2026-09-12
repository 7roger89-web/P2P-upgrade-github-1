#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yijing_corpus import UPSTREAM, load_corrected_corpus, source_metadata  # noqa: E402

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao.data import BAGUA, find_hexagram  # noqa: E402


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


def main():
    p = argparse.ArgumentParser(description="Source-grounded Yi Jing gua/yao text lookup")
    p.add_argument("--hexagram", required=True, help="Full name or upstream alias, e.g. 地山谦 or 谦")
    p.add_argument("--moving", help="Optional line positions, e.g. 2 or 2,3")
    a = p.parse_args()

    rec = find_hexagram(a.hexagram)
    if not rec:
        fail(f"Unknown hexagram: {a.hexagram}")
    positions = parse_positions(a.moving)
    corpus = load_corrected_corpus()
    name = rec["name"]
    entry = corpus.get(name)
    if not entry:
        fail(f"Yi Jing corpus missing normalized hexagram: {name}", 1)

    selected = []
    for pos in positions:
        label = yao_label(rec, pos)
        text = entry.get("yao", {}).get(label)
        if not text:
            fail(f"Yi Jing corpus missing {name} {label}", 1)
        selected.append({"position": pos, "label": label, "text": text})

    print(json.dumps({
        "DOMAIN": "YIJING",
        "CAPABILITY": "SOURCE_GROUNDED_GUA_YAO_TEXT_LOOKUP",
        "INPUT": {"hexagram": a.hexagram, "moving": positions},
        "NORMALIZED_HEXAGRAM": name,
        "UPPER_TRIGRAM": rec["upper"],
        "LOWER_TRIGRAM": rec["lower"],
        "GUA_CI": entry["gua_ci"],
        "SELECTED_YAO": selected,
        "SOURCE": source_metadata(),
        "STRUCTURAL_INTEGRITY": "VERIFIED_BY_64_HEXAGRAM_LINE_PATTERN_AUDIT",
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
