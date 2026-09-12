#!/usr/bin/env python3
import re
from pathlib import Path

from yijing_corpus import PIN, UPSTREAM, verify_pin

DOC = UPSTREAM / "docs" / "易经六十四卦.md"

# The pinned markdown mislabels the Tuan marker as Xiang in exactly these two
# sections. We keep the vendor source untouched and reclassify the marker only
# when the expected classical text is still present, so upstream drift fails
# loudly instead of being overwritten silently.
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


def _clean_fragment(text):
    return TAG_RE.sub("", text).strip()


def _classical_marker_text(lines, index):
    line = lines[index]
    marker = MARKER_RE.search(line)
    if not marker:
        return None

    payload = _clean_fragment(line[marker.end():])
    pieces = [payload] if payload else []

    # Some sections put only "《彖》曰：" on the top-level bullet and split the
    # classical passage across one-indent green bullets. Collect those direct
    # children only; two-indent explanatory prose and later line-level 小象 are
    # deliberately excluded.
    j = index + 1
    while j < len(lines) and not lines[j].startswith("- "):
        child = lines[j]
        if re.match(r"^(?:\t| {1,4})-\s+<font\b", child):
            cleaned = _clean_fragment(re.sub(r"^[\t ]+-\s+", "", child))
            if cleaned and "《象》曰" not in cleaned and "《彖》曰" not in cleaned:
                pieces.append(cleaned)
        j += 1

    return "".join(pieces).strip()


def load_sections(apply_label_corrections=True):
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
        lines = text[start:end].splitlines()
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


def source_metadata():
    return {
        "repo": "Johnson-Jia/liuyao-divination",
        "pin": PIN,
        "path": "docs/易经六十四卦.md",
        "label_overlay": LABEL_CORRECTIONS,
        "policy": "READ_TIME_LABEL_OVERLAY_VENDOR_UNMODIFIED",
        "scope": "HEXAGRAM_LEVEL_TUAN_AND_DAXIANG_ONLY",
    }
