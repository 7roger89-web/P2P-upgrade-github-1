#!/usr/bin/env python3
import re
from pathlib import Path

from yijing_corpus import CORRECTIONS as CORPUS_CORRECTIONS, PIN, UPSTREAM, verify_pin

DOC = UPSTREAM / "docs" / "易经六十四卦.md"

# The pinned markdown mislabels the Tuan marker as Xiang in exactly these two
# sections. Keep vendor bytes untouched and reclassify only under strict text
# preconditions so upstream drift fails loudly.
LABEL_CORRECTIONS = {
    "雷水解": {
        "raw_label": "象",
        "corrected_label": "彖",
        "expected_text_prefix": "解，險以動，動而免乎險，解。",
        "sources": [
            "https://zh.wikisource.org/zh-hant/周易正義/04解",
            "https://ctext.org/book-of-changes/jie2/zh",
        ],
        "reason": "Pinned markdown labels the hexagram-level Tuan passage as 《象》.",
    },
    "火泽睽": {
        "raw_label": "象",
        "corrected_label": "彖",
        "expected_text_prefix": "睽，火動而上，澤動而下，二女同居，其志不同行。",
        "sources": [
            "https://zh.wikisource.org/wiki/周易正義/04睽",
            "https://ctext.org/book-of-changes/kui1/zh",
        ],
        "reason": "Pinned markdown labels the hexagram-level Tuan passage as 《象》.",
    },
}

SECTION_RE = re.compile(r"^##\s+《([^》]+)》[^\n]*$", re.MULTILINE)
MARKER_RE = re.compile(r"《([彖象])》曰[：:]?")
TAG_RE = re.compile(r"<[^>]+>")
YAO_RE = re.compile(r"^(初[九六]|[九六][二三四五]|上[九六])[：:](.*)$")
SPECIAL_YAO_RE = re.compile(r"^(用九|用六)[：:](.*)$")

# These are not new divination rules. They are read-time repairs for two source
# defects already proven in the pinned Zhouyi corpus and independently sourced.
XIAOXIANG_CORRECTIONS = {
    "地山谦": {
        "sources": CORPUS_CORRECTIONS["地山谦"]["sources"],
        "reason": CORPUS_CORRECTIONS["地山谦"]["reason"],
        "policy": "RELABEL_RAW_LINE_FOR_COMMENTARY_ALIGNMENT",
    },
    "地水师": {
        "sources": CORPUS_CORRECTIONS["地水师"]["sources"],
        "reason": (
            "Pinned markdown omits 六四 and attaches the 六四 Xiaoxiang "
            "‘左次，无咎，未失常也。’ under the 六三 block."
        ),
        "policy": "RESTORE_SIX_THREE_XIAOXIANG_AND_REASSIGN_RAW_SIX_FOUR_XIAOXIANG",
    },
}


def _clean_fragment(text):
    return TAG_RE.sub("", text).strip()


def _strip_bullet(text):
    return re.sub(r"^\s*-\s+", "", text)


def _indent_width(line):
    prefix = line[: len(line) - len(line.lstrip(" \t"))]
    return sum(4 if ch == "\t" else 1 for ch in prefix)


def _classical_marker_text(lines, index, stop=None):
    """Read an inline marker payload or its direct green child bullets only."""
    line = lines[index]
    marker = MARKER_RE.search(line)
    if not marker:
        return None

    payload = _clean_fragment(line[marker.end() :])
    if payload:
        return payload

    end = len(lines) if stop is None else stop
    base_indent = _indent_width(line)
    children = []
    for j in range(index + 1, end):
        child = lines[j]
        if not re.match(r"^\s*-\s+", child):
            continue
        if 'color="#00b050"' not in child:
            continue
        cleaned = _clean_fragment(_strip_bullet(child))
        if not cleaned or "《象》曰" in cleaned or "《彖》曰" in cleaned:
            continue
        indent = _indent_width(child)
        if indent > base_indent:
            children.append((indent, cleaned))

    if not children:
        return ""
    direct_indent = min(indent for indent, _ in children)
    return "".join(text for indent, text in children if indent == direct_indent).strip()


def _human_lines(lines):
    start = None
    for i, line in enumerate(lines):
        if line.startswith("### 人间道"):
            start = i + 1
            break
    if start is None:
        return []
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("### "):
            end = i
            break
    return lines[start:end]


def _section_bodies():
    verify_pin()
    if not DOC.exists():
        raise RuntimeError(f"Pinned Yi Jing commentary source missing: {DOC}")

    text = DOC.read_text(encoding="utf-8")
    matches = list(SECTION_RE.finditer(text))
    sections = []
    for i, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((name, text[start:end].splitlines()))
    return sections


def _top_level_red_indices(lines):
    return [
        idx for idx, line in enumerate(lines)
        if line.startswith("- <font") and 'color="#ff0000"' in line
    ]


def _xiang_candidates_in_block(lines, start, stop):
    xiang = []
    for j in range(start + 1, stop):
        if "《象》曰" not in lines[j]:
            continue
        text = _classical_marker_text(lines, j, stop)
        if text:
            xiang.append(text)
    return xiang


def load_sections(apply_label_corrections=True):
    """Hexagram-level Tuan and Daxiang records from the 人间道 block."""
    sections = []
    for name, raw_lines in _section_bodies():
        lines = _human_lines(raw_lines)
        markers = []

        for idx, line in enumerate(lines):
            if not line.startswith("- "):
                continue
            marker = MARKER_RE.search(line)
            if not marker:
                continue
            label = marker.group(1)
            marker_text = _classical_marker_text(lines, idx)
            markers.append({
                "raw_label": label,
                "label": label,
                "text": marker_text or "",
            })

        if apply_label_corrections and name in LABEL_CORRECTIONS:
            correction = LABEL_CORRECTIONS[name]
            candidates = [
                item
                for item in markers
                if item["raw_label"] == correction["raw_label"]
                and item["text"].startswith(correction["expected_text_prefix"])
            ]
            if len(candidates) != 1:
                raise RuntimeError(
                    f"Commentary label correction precondition drift for {name}: "
                    f"expected one {correction['raw_label']} marker starting "
                    f"{correction['expected_text_prefix']!r}, found {len(candidates)}"
                )
            candidates[0]["label"] = correction["corrected_label"]
            candidates[0]["correction"] = {
                "reason": correction["reason"],
                "sources": correction["sources"],
            }

        sections.append({"hexagram": name, "markers": markers})
    return sections


def load_xiaoxiang_records(apply_corrections=True):
    """Line-level Xiaoxiang records; six regular lines only, excluding 用九/用六."""
    sections = []

    for name, raw_lines in _section_bodies():
        lines = _human_lines(raw_lines)
        top_level_red = _top_level_red_indices(lines)
        yao_indices = []
        for idx in top_level_red:
            match = YAO_RE.match(_clean_fragment(_strip_bullet(lines[idx])))
            if not match:
                continue
            yao_indices.append((idx, match.group(1), match.group(2).strip()))

        records = []
        for idx, label, yao_text in yao_indices:
            stop = next((red_idx for red_idx in top_level_red if red_idx > idx), len(lines))
            records.append({
                "raw_label": label,
                "label": label,
                "yao_text": yao_text,
                "xiaoxiang_candidates": _xiang_candidates_in_block(lines, idx, stop),
            })

        if apply_corrections and name == "地山谦":
            if any(item["label"] == "六二" for item in records):
                raise RuntimeError("Xiaoxiang correction precondition drift for 地山谦: 六二 already exists")
            candidates = [
                item for item in records
                if item["raw_label"] == "六三"
                and (item["yao_text"].startswith("嗚謙") or item["yao_text"].startswith("呜谦"))
            ]
            if len(candidates) != 1:
                raise RuntimeError(
                    "Xiaoxiang correction precondition drift for 地山谦: "
                    f"expected one mislabeled 嗚謙 line, found {len(candidates)}"
                )
            candidates[0]["label"] = "六二"
            candidates[0]["correction"] = {
                "action": "RELABEL 六三 -> 六二",
                "reason": XIAOXIANG_CORRECTIONS[name]["reason"],
                "sources": XIAOXIANG_CORRECTIONS[name]["sources"],
            }

        if apply_corrections and name == "地水师":
            if any(item["label"] == "六四" for item in records):
                raise RuntimeError("Xiaoxiang correction precondition drift for 地水师: 六四 already exists")
            candidates = [
                item for item in records
                if item["raw_label"] == "六三" and item["yao_text"].startswith("師或輿")
            ]
            if len(candidates) != 1:
                raise RuntimeError(
                    "Xiaoxiang correction precondition drift for 地水师: "
                    f"expected one 六三 師或輿 line, found {len(candidates)}"
                )
            six_three = candidates[0]
            if len(six_three["xiaoxiang_candidates"]) != 1 or not six_three["xiaoxiang_candidates"][0].startswith("左次"):
                raise RuntimeError(
                    "Xiaoxiang correction precondition drift for 地水师: "
                    "expected the misattached 左次 Xiaoxiang under 六三"
                )
            raw_six_four_xiaoxiang = six_three["xiaoxiang_candidates"][0]
            six_three["xiaoxiang_candidates"] = ["師或輿尸，凶，大無功也。"]
            six_three["correction"] = {
                "action": "RESTORE 六三 XIAOXIANG",
                "reason": XIAOXIANG_CORRECTIONS[name]["reason"],
                "sources": XIAOXIANG_CORRECTIONS[name]["sources"],
            }
            records.append({
                "raw_label": None,
                "label": "六四",
                "yao_text": CORPUS_CORRECTIONS[name]["set"]["六四"],
                "xiaoxiang_candidates": [raw_six_four_xiaoxiang],
                "correction": {
                    "action": "REASSIGN RAW 左次 XIAOXIANG TO 六四",
                    "reason": XIAOXIANG_CORRECTIONS[name]["reason"],
                    "sources": XIAOXIANG_CORRECTIONS[name]["sources"],
                },
            })

        sections.append({"hexagram": name, "records": records})

    return sections


def load_special_xiaoxiang():
    """Return the two source-present special lines: 乾用九 and 坤用六."""
    expected = {"乾为天": "用九", "坤为地": "用六"}
    special = {}

    for name, raw_lines in _section_bodies():
        if name not in expected:
            continue
        lines = _human_lines(raw_lines)
        top_level_red = _top_level_red_indices(lines)
        candidates = []
        for idx in top_level_red:
            match = SPECIAL_YAO_RE.match(_clean_fragment(_strip_bullet(lines[idx])))
            if not match:
                continue
            stop = next((red_idx for red_idx in top_level_red if red_idx > idx), len(lines))
            candidates.append({
                "label": match.group(1),
                "source_yao_text": match.group(2).strip(),
                "xiaoxiang_candidates": _xiang_candidates_in_block(lines, idx, stop),
            })

        wanted = expected[name]
        candidates = [item for item in candidates if item["label"] == wanted]
        if len(candidates) != 1:
            raise RuntimeError(
                f"Yi Jing special-line structure invalid for {name} {wanted}: records={len(candidates)}"
            )
        record = candidates[0]
        if len(record["xiaoxiang_candidates"]) != 1 or not record["xiaoxiang_candidates"][0]:
            raise RuntimeError(
                f"Yi Jing special-line Xiaoxiang invalid for {name} {wanted}: "
                f"candidates={len(record['xiaoxiang_candidates'])}"
            )
        special[name] = {
            "label": wanted,
            "source_yao_text": record["source_yao_text"],
            "xiaoxiang": record["xiaoxiang_candidates"][0],
        }

    if set(special) != set(expected):
        raise RuntimeError(
            f"Yi Jing special-line coverage invalid: expected={sorted(expected)}, got={sorted(special)}"
        )
    return special


def load_corrected_commentary():
    corpus = {}
    for section in load_sections(apply_label_corrections=True):
        name = section["hexagram"]
        tuan = [x["text"] for x in section["markers"] if x["label"] == "彖"]
        daxiang = [x["text"] for x in section["markers"] if x["label"] == "象"]
        if len(tuan) != 1 or len(daxiang) != 1 or not tuan[0] or not daxiang[0]:
            raise RuntimeError(
                f"Yi Jing commentary structure invalid for {name}: "
                f"tuan={len(tuan)}, daxiang={len(daxiang)}"
            )
        corpus[name] = {"tuan": tuan[0], "daxiang": daxiang[0]}
    return corpus


def load_corrected_xiaoxiang():
    corpus = {}
    for section in load_xiaoxiang_records(apply_corrections=True):
        name = section["hexagram"]
        lines = {}
        for record in section["records"]:
            label = record["label"]
            candidates = record["xiaoxiang_candidates"]
            if label in lines:
                raise RuntimeError(f"Duplicate Yi Jing Xiaoxiang label for {name} {label}")
            if len(candidates) != 1 or not candidates[0]:
                raise RuntimeError(
                    f"Yi Jing Xiaoxiang structure invalid for {name} {label}: "
                    f"candidates={len(candidates)}"
                )
            lines[label] = candidates[0]
        corpus[name] = lines
    return corpus


def source_metadata():
    return {
        "repo": "Johnson-Jia/liuyao-divination",
        "pin": PIN,
        "path": "docs/易经六十四卦.md",
        "label_overlay": LABEL_CORRECTIONS,
        "xiaoxiang_overlay": XIAOXIANG_CORRECTIONS,
        "policy": "READ_TIME_PROVENANCE_OVERLAY_VENDOR_UNMODIFIED",
        "scope": "HEXAGRAM_LEVEL_TUAN_DAXIANG_384_REGULAR_XIAOXIANG_AND_QIAN_KUN_SPECIAL_LINES",
    }
