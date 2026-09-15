#!/usr/bin/env python3
import re
from pathlib import Path

from yijing_corpus import (  # noqa: E402
    CLAIM_OVERLAY,
    CLAIM_RAW,
    CORPUS_REPO,
    PIN,
    REFERENCE_STATUS_NONE,
    REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED,
    SUPPORT_STATUS_OVERLAY,
    SUPPORT_STATUS_RAW,
    YijingTextEvidenceError,
    CORRECTIONS as CORPUS_CORRECTIONS,
    UPSTREAM,
    resolve_upstream_source_path,
    verify_pin,
)

DOC = UPSTREAM / "docs" / "易经六十四卦.md"
COMMENTARY_SOURCE_PATH = "docs/易经六十四卦.md"
COMMENTARY_OVERLAY_POLICY = "READ_TIME_PROVENANCE_OVERLAY_VENDOR_UNMODIFIED"

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
# The raw_* / relabeled_to / restored_xiaoxiang / reassigned_xiaoxiang_to keys
# are machine-checkable overlay descriptors: the loader enforces them against
# the pinned markdown and the selected-text evidence validator re-proves them
# against the raw records, so packet evidence cannot drift from loader truth.
XIAOXIANG_CORRECTIONS = {
    "地山谦": {
        "sources": CORPUS_CORRECTIONS["地山谦"]["sources"],
        "reason": CORPUS_CORRECTIONS["地山谦"]["reason"],
        "policy": "RELABEL_RAW_LINE_FOR_COMMENTARY_ALIGNMENT",
        "raw_line_label": "六三",
        "raw_yao_text_prefixes": ["嗚謙", "呜谦"],
        "relabeled_to": "六二",
    },
    "地水师": {
        "sources": CORPUS_CORRECTIONS["地水师"]["sources"],
        "reason": (
            "Pinned markdown omits 六四 and attaches the 六四 Xiaoxiang "
            "‘左次，无咎，未失常也。’ under the 六三 block."
        ),
        "policy": "RESTORE_SIX_THREE_XIAOXIANG_AND_REASSIGN_RAW_SIX_FOUR_XIAOXIANG",
        "raw_line_label": "六三",
        "raw_yao_text_prefix": "師或輿",
        "raw_misattached_xiaoxiang_prefix": "左次",
        "restored_xiaoxiang": {"六三": "師或輿尸，凶，大無功也。"},
        "reassigned_xiaoxiang_to": "六四",
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
            correction = XIAOXIANG_CORRECTIONS[name]
            if any(item["label"] == correction["relabeled_to"] for item in records):
                raise RuntimeError("Xiaoxiang correction precondition drift for 地山谦: 六二 already exists")
            candidates = [
                item for item in records
                if item["raw_label"] == correction["raw_line_label"]
                and any(item["yao_text"].startswith(p) for p in correction["raw_yao_text_prefixes"])
            ]
            if len(candidates) != 1:
                raise RuntimeError(
                    "Xiaoxiang correction precondition drift for 地山谦: "
                    f"expected one mislabeled 嗚謙 line, found {len(candidates)}"
                )
            candidates[0]["label"] = correction["relabeled_to"]
            candidates[0]["correction"] = {
                "action": f"RELABEL {correction['raw_line_label']} -> {correction['relabeled_to']}",
                "reason": correction["reason"],
                "sources": correction["sources"],
            }

        if apply_corrections and name == "地水师":
            correction = XIAOXIANG_CORRECTIONS[name]
            if any(item["label"] == correction["reassigned_xiaoxiang_to"] for item in records):
                raise RuntimeError("Xiaoxiang correction precondition drift for 地水师: 六四 already exists")
            candidates = [
                item for item in records
                if item["raw_label"] == correction["raw_line_label"]
                and item["yao_text"].startswith(correction["raw_yao_text_prefix"])
            ]
            if len(candidates) != 1:
                raise RuntimeError(
                    "Xiaoxiang correction precondition drift for 地水师: "
                    f"expected one 六三 師或輿 line, found {len(candidates)}"
                )
            six_three = candidates[0]
            if (
                len(six_three["xiaoxiang_candidates"]) != 1
                or not six_three["xiaoxiang_candidates"][0].startswith(
                    correction["raw_misattached_xiaoxiang_prefix"]
                )
            ):
                raise RuntimeError(
                    "Xiaoxiang correction precondition drift for 地水师: "
                    "expected the misattached 左次 Xiaoxiang under 六三"
                )
            raw_six_four_xiaoxiang = six_three["xiaoxiang_candidates"][0]
            six_three["xiaoxiang_candidates"] = [correction["restored_xiaoxiang"]["六三"]]
            six_three["correction"] = {
                "action": f"RESTORE {correction['raw_line_label']} XIAOXIANG",
                "reason": correction["reason"],
                "sources": correction["sources"],
            }
            records.append({
                "raw_label": None,
                "label": correction["reassigned_xiaoxiang_to"],
                "yao_text": CORPUS_CORRECTIONS[name]["set"]["六四"],
                "xiaoxiang_candidates": [raw_six_four_xiaoxiang],
                "correction": {
                    "action": (
                        f"REASSIGN RAW {correction['raw_misattached_xiaoxiang_prefix']} "
                        f"XIAOXIANG TO {correction['reassigned_xiaoxiang_to']}"
                    ),
                    "reason": correction["reason"],
                    "sources": correction["sources"],
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
        "repo": CORPUS_REPO,
        "pin": PIN,
        "path": COMMENTARY_SOURCE_PATH,
        "label_overlay": LABEL_CORRECTIONS,
        "xiaoxiang_overlay": XIAOXIANG_CORRECTIONS,
        "policy": COMMENTARY_OVERLAY_POLICY,
        "scope": "HEXAGRAM_LEVEL_TUAN_DAXIANG_384_REGULAR_XIAOXIANG_AND_QIAN_KUN_SPECIAL_LINES",
    }


# ---------------------------------------------------------------------------
# Selected-text evidence: per-field provenance for commentary-bound emissions
# (Tuan, Daxiang, line Xiaoxiang, special-line Xiaoxiang). Locators resolve
# mechanically against the pinned RAW markdown via the existing loaders; Yao
# text and Xiaoxiang provenance stay independent (different pinned files).
# ---------------------------------------------------------------------------

HUMAN_BLOCK = "人间道"
MARKER_LOCATOR_PREFIX_LEN = 12

_EVIDENCE_CACHE = {}


def _cached(key, producer):
    if key not in _EVIDENCE_CACHE:
        _EVIDENCE_CACHE[key] = producer()
    return _EVIDENCE_CACHE[key]


def _raw_sections_cached():
    return _cached("raw_sections", lambda: load_sections(apply_label_corrections=False))


def _raw_xiaoxiang_cached():
    return _cached("raw_xiaoxiang", lambda: load_xiaoxiang_records(apply_corrections=False))


def _special_cached():
    return _cached("special", load_special_xiaoxiang)


def _resolve_raw_marker(locator):
    """Resolve a hexagram-level marker locator against the pinned RAW markdown.

    raw_marker_label is the label the pinned vendor file actually carries; the
    解/睽 Tuan passages are therefore located under 象, never claimed as raw 彖.
    """
    hexagram = locator.get("hexagram")
    sections = [s for s in _raw_sections_cached() if s["hexagram"] == hexagram]
    if len(sections) != 1:
        raise YijingTextEvidenceError(
            f"Commentary locator section not unique for {hexagram!r}: {len(sections)}"
        )
    markers = [
        m for m in sections[0]["markers"]
        if m["raw_label"] == locator.get("raw_marker_label")
    ]
    prefix = locator.get("raw_text_prefix")
    if prefix is not None:
        markers = [m for m in markers if m["text"].startswith(prefix)]
    if len(markers) != 1:
        raise YijingTextEvidenceError(
            f"Commentary marker locator is not unique: {locator!r} -> {len(markers)} markers"
        )
    return markers[0]["text"]


def _raw_xiaoxiang_records(hexagram):
    sections = [s for s in _raw_xiaoxiang_cached() if s["hexagram"] == hexagram]
    if len(sections) != 1:
        raise YijingTextEvidenceError(
            f"Xiaoxiang locator section not unique for {hexagram!r}: {len(sections)}"
        )
    return sections[0]["records"]


def _match_raw_xiaoxiang_line(records, locator):
    """Find the one raw line record a Xiaoxiang locator points at."""
    label = locator.get("raw_line_label")
    matches = [r for r in records if r["raw_label"] == label]
    prefixes = locator.get("raw_yao_text_prefixes")
    if prefixes is not None:
        matches = [
            r for r in matches
            if any(r["yao_text"].startswith(p) for p in prefixes)
        ]
    prefix = locator.get("raw_yao_text_prefix")
    if prefix is not None:
        matches = [r for r in matches if r["yao_text"].startswith(prefix)]
    if len(matches) != 1:
        raise YijingTextEvidenceError(
            f"Xiaoxiang line locator is not unique: {locator!r} -> {len(matches)} records"
        )
    return matches[0]


def xiaoxiang_overlay_kind(hexagram, label):
    """Classify which existing read-time overlay (if any) produced this Xiaoxiang."""
    correction = XIAOXIANG_CORRECTIONS.get(hexagram)
    if not correction:
        return None, None
    if correction.get("relabeled_to") == label:
        return "RELABEL", correction
    if label in correction.get("restored_xiaoxiang", {}):
        return "RESTORE", correction
    if correction.get("reassigned_xiaoxiang_to") == label:
        return "REASSIGN", correction
    return None, None


def xiaoxiang_overlay_action(kind, correction, label):
    if kind == "RELABEL":
        return f"RELABEL {correction['raw_line_label']} -> {label}"
    if kind == "RESTORE":
        return f"RESTORE {correction['raw_line_label']} XIAOXIANG"
    return (
        f"REASSIGN RAW {correction['raw_misattached_xiaoxiang_prefix']} "
        f"XIAOXIANG TO {label}"
    )


def _commentary_evidence_common(field, hexagram, line_label, locator):
    return {
        "field": field,
        "hexagram": hexagram,
        "line_label": line_label,
        "repo": CORPUS_REPO,
        "pin": PIN,
        "source_path": COMMENTARY_SOURCE_PATH,
        "source_locator": locator,
    }


def _raw_entry_tail(locator):
    return {
        "support_status": SUPPORT_STATUS_RAW,
        "overlay_applied": False,
        "overlay_id": None,
        "overlay_policy": None,
        "bounded_supported_claim": CLAIM_RAW,
        "external_reference_status": REFERENCE_STATUS_NONE,
    }


def marker_evidence(hexagram, text, field):
    """Tuan/Daxiang evidence. Only the 解/睽 hexagram-level Tuan passages go
    through the existing label overlay; Daxiang is always raw."""
    implied_label = "彖" if field in {"TUAN_TEXT", "CHANGED_TUAN_TEXT"} else "象"
    correction = LABEL_CORRECTIONS.get(hexagram) if implied_label == "彖" else None
    if correction:
        locator = {
            "hexagram": hexagram,
            "block": HUMAN_BLOCK,
            "raw_marker_label": correction["raw_label"],
            "raw_text_prefix": correction["expected_text_prefix"],
            "corrected_marker_label": correction["corrected_label"],
        }
        entry = _commentary_evidence_common(field, hexagram, None, locator)
        entry.update({
            "support_status": SUPPORT_STATUS_OVERLAY,
            "overlay_applied": True,
            "overlay_id": f"YIJING_COMMENTARY_LABEL_OVERLAY:{hexagram}:{correction['corrected_label']}",
            "overlay_action": f"RELABEL {correction['raw_label']} -> {correction['corrected_label']}",
            "overlay_reason": correction["reason"],
            "overlay_policy": COMMENTARY_OVERLAY_POLICY,
            "overlay_precondition_passed": True,
            "raw_source_state": {
                "raw_marker_label": correction["raw_label"],
                "corrected_marker_label": correction["corrected_label"],
            },
            "bounded_supported_claim": CLAIM_OVERLAY,
            "external_references": list(correction["sources"]),
            "external_reference_status": REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED,
        })
        return entry
    locator = {
        "hexagram": hexagram,
        "block": HUMAN_BLOCK,
        "raw_marker_label": implied_label,
        "raw_text_prefix": text[:MARKER_LOCATOR_PREFIX_LEN],
    }
    entry = _commentary_evidence_common(field, hexagram, None, locator)
    entry.update(_raw_entry_tail(locator))
    return entry


def tuan_evidence(hexagram, text, field="TUAN_TEXT"):
    return marker_evidence(hexagram, text, field)


def daxiang_evidence(hexagram, text, field="DAXIANG_TEXT"):
    return marker_evidence(hexagram, text, field)


def xiaoxiang_evidence(hexagram, label, text, field="SELECTED_YAO[].xiaoxiang"):
    """Line Xiaoxiang evidence, independent from the corpus yao-text evidence."""
    kind, correction = xiaoxiang_overlay_kind(hexagram, label)
    if not kind:
        locator = {
            "hexagram": hexagram,
            "block": HUMAN_BLOCK,
            "raw_line_label": label,
            "raw_marker_label": "象",
        }
        entry = _commentary_evidence_common(field, hexagram, label, locator)
        entry.update(_raw_entry_tail(locator))
        return entry
    if kind == "RELABEL":
        locator = {
            "hexagram": hexagram,
            "block": HUMAN_BLOCK,
            "raw_line_label": correction["raw_line_label"],
            "raw_yao_text_prefixes": list(correction["raw_yao_text_prefixes"]),
            "raw_marker_label": "象",
        }
        raw_source_state = {
            "raw_line_label": correction["raw_line_label"],
            "raw_yao_text_prefixes": list(correction["raw_yao_text_prefixes"]),
            "raw_xiaoxiang": text,
        }
    else:
        locator = {
            "hexagram": hexagram,
            "block": HUMAN_BLOCK,
            "raw_line_label": correction["raw_line_label"],
            "raw_yao_text_prefix": correction["raw_yao_text_prefix"],
            "raw_marker_label": "象",
        }
        if kind == "RESTORE":
            raw_record = _match_raw_xiaoxiang_line(_raw_xiaoxiang_records(hexagram), locator)
            raw_source_state = {
                "raw_line_label": correction["raw_line_label"],
                "raw_misattached_xiaoxiang": raw_record["xiaoxiang_candidates"][0],
                "restored_xiaoxiang": text,
            }
        else:
            raw_source_state = {
                "raw_line_label": correction["raw_line_label"],
                "raw_xiaoxiang": text,
            }
    entry = _commentary_evidence_common(field, hexagram, label, locator)
    entry.update({
        "support_status": SUPPORT_STATUS_OVERLAY,
        "overlay_applied": True,
        "overlay_id": f"YIJING_XIAOXIANG_READ_TIME_OVERLAY:{hexagram}:{label}",
        "overlay_action": xiaoxiang_overlay_action(kind, correction, label),
        "overlay_reason": correction["reason"],
        "overlay_policy": COMMENTARY_OVERLAY_POLICY,
        "overlay_precondition_passed": True,
        "raw_source_state": raw_source_state,
        "bounded_supported_claim": CLAIM_OVERLAY,
        "external_references": list(correction["sources"]),
        "external_reference_status": REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED,
    })
    return entry


def special_xiaoxiang_evidence(hexagram, label, text):
    """用九/用六 Xiaoxiang evidence; no overlay exists for special lines."""
    locator = {
        "hexagram": hexagram,
        "block": HUMAN_BLOCK,
        "special_line_label": label,
    }
    entry = _commentary_evidence_common("SPECIAL_YAO_CANDIDATE.xiaoxiang", hexagram, label, locator)
    entry.update(_raw_entry_tail(locator))
    return entry


def _validate_evidence_common(entry, source_path):
    if not isinstance(entry, dict):
        raise YijingTextEvidenceError(f"Evidence entry must be a dict: {entry!r}")
    if entry.get("repo") != CORPUS_REPO:
        raise YijingTextEvidenceError(f"Evidence repo mismatch: {entry.get('repo')!r}")
    if entry.get("pin") != PIN:
        raise YijingTextEvidenceError(f"Evidence pin mismatch: {entry.get('pin')!r}")
    if entry.get("source_path") != source_path:
        raise YijingTextEvidenceError(
            f"Evidence source path is not the sanctioned pinned surface "
            f"{source_path!r}: {entry.get('source_path')!r}"
        )
    resolve_upstream_source_path(entry["source_path"])
    overlay_applied = entry.get("overlay_applied")
    if overlay_applied not in (True, False):
        raise YijingTextEvidenceError(
            f"Evidence overlay_applied must be boolean: {overlay_applied!r}"
        )
    if overlay_applied and entry.get("support_status") != SUPPORT_STATUS_OVERLAY:
        raise YijingTextEvidenceError(
            f"Overlay evidence must claim {SUPPORT_STATUS_OVERLAY}: "
            f"{entry.get('support_status')!r}"
        )
    if not overlay_applied and entry.get("support_status") != SUPPORT_STATUS_RAW:
        raise YijingTextEvidenceError(
            f"Raw evidence must claim {SUPPORT_STATUS_RAW}: {entry.get('support_status')!r}"
        )
    return overlay_applied


def _reject_overlay_fields_on_raw(entry):
    if entry.get("overlay_id") is not None or entry.get("overlay_policy") is not None:
        raise YijingTextEvidenceError("Raw evidence must not carry overlay identity")
    if entry.get("bounded_supported_claim") != CLAIM_RAW:
        raise YijingTextEvidenceError(
            f"Raw evidence claim mismatch: {entry.get('bounded_supported_claim')!r}"
        )
    if entry.get("external_reference_status") != REFERENCE_STATUS_NONE:
        raise YijingTextEvidenceError(
            "Raw evidence must not cite external references: "
            f"{entry.get('external_reference_status')!r}"
        )


def validate_marker_evidence(entry, emitted_text):
    """Fail-closed validation for Tuan/Daxiang evidence entries."""
    overlay_applied = _validate_evidence_common(entry, COMMENTARY_SOURCE_PATH)
    locator = entry.get("source_locator")
    if not isinstance(locator, dict) or locator.get("block") != HUMAN_BLOCK:
        raise YijingTextEvidenceError(
            f"Marker evidence locator must target the {HUMAN_BLOCK} block: {locator!r}"
        )
    if locator.get("hexagram") != entry.get("hexagram"):
        raise YijingTextEvidenceError(
            f"Marker evidence locator does not match its hexagram: {locator!r}"
        )
    if not overlay_applied:
        _reject_overlay_fields_on_raw(entry)
        if locator.get("raw_marker_label") not in {"彖", "象"}:
            raise YijingTextEvidenceError(
                f"Raw marker locator label invalid: {locator.get('raw_marker_label')!r}"
            )
        resolved = _resolve_raw_marker(locator)
        if resolved != emitted_text:
            raise YijingTextEvidenceError(
                f"Raw commentary value mismatch at {locator!r}: "
                f"pinned={resolved!r}, emitted={emitted_text!r}"
            )
        return True

    implied_label = "彖" if entry.get("field") in {"TUAN_TEXT", "CHANGED_TUAN_TEXT"} else "象"
    hexagram = entry.get("hexagram")
    correction = LABEL_CORRECTIONS.get(hexagram)
    if not correction or correction.get("corrected_label") != implied_label:
        raise YijingTextEvidenceError(
            f"No commentary label overlay supports {entry.get('field')!r} for {hexagram!r}"
        )
    if (
        locator.get("raw_marker_label") != correction["raw_label"]
        or locator.get("raw_text_prefix") != correction["expected_text_prefix"]
        or locator.get("corrected_marker_label") != implied_label
    ):
        raise YijingTextEvidenceError(
            f"Label overlay locator mismatch for {hexagram}: {locator!r}"
        )
    if entry.get("overlay_id") != f"YIJING_COMMENTARY_LABEL_OVERLAY:{hexagram}:{implied_label}":
        raise YijingTextEvidenceError(
            f"Label overlay identity mismatch: {entry.get('overlay_id')!r}"
        )
    if entry.get("overlay_action") != f"RELABEL {correction['raw_label']} -> {implied_label}":
        raise YijingTextEvidenceError(
            f"Label overlay action mismatch: {entry.get('overlay_action')!r}"
        )
    if entry.get("overlay_reason") != correction["reason"]:
        raise YijingTextEvidenceError(
            f"Label overlay reason mismatch: {entry.get('overlay_reason')!r}"
        )
    if entry.get("overlay_policy") != COMMENTARY_OVERLAY_POLICY:
        raise YijingTextEvidenceError(
            f"Label overlay policy mismatch: {entry.get('overlay_policy')!r}"
        )
    if entry.get("overlay_precondition_passed") is not True:
        raise YijingTextEvidenceError("Label overlay preconditions not asserted as passed")
    if entry.get("raw_source_state") != {
        "raw_marker_label": correction["raw_label"],
        "corrected_marker_label": implied_label,
    }:
        raise YijingTextEvidenceError(
            f"Label overlay raw source state mismatch: {entry.get('raw_source_state')!r}"
        )
    # Re-prove the overlay preconditions against the pinned raw markdown now:
    # exactly one raw 象-labeled marker carries the Tuan passage prefix.
    resolved = _resolve_raw_marker(locator)
    if resolved != emitted_text:
        raise YijingTextEvidenceError(
            f"Overlay commentary value mismatch for {hexagram}: "
            f"pinned raw marker text={resolved!r}, emitted={emitted_text!r}"
        )
    if entry.get("external_references") != list(correction["sources"]):
        raise YijingTextEvidenceError(
            f"External reference pointers mismatch for {hexagram} {entry.get('field')!r}"
        )
    if entry.get("external_reference_status") != REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED:
        raise YijingTextEvidenceError(
            "External references must remain "
            f"{REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED}, not "
            f"{entry.get('external_reference_status')!r}"
        )
    if entry.get("bounded_supported_claim") != CLAIM_OVERLAY:
        raise YijingTextEvidenceError(
            f"Overlay evidence claim mismatch: {entry.get('bounded_supported_claim')!r}"
        )
    return True


def validate_xiaoxiang_evidence(entry, emitted_text):
    """Fail-closed validation for line Xiaoxiang evidence entries."""
    overlay_applied = _validate_evidence_common(entry, COMMENTARY_SOURCE_PATH)
    locator = entry.get("source_locator")
    hexagram = entry.get("hexagram")
    label = entry.get("line_label")
    if not isinstance(locator, dict) or locator.get("block") != HUMAN_BLOCK:
        raise YijingTextEvidenceError(
            f"Xiaoxiang evidence locator must target the {HUMAN_BLOCK} block: {locator!r}"
        )
    if locator.get("hexagram") != hexagram:
        raise YijingTextEvidenceError(
            f"Xiaoxiang evidence locator does not match its hexagram: {locator!r}"
        )
    if not overlay_applied:
        _reject_overlay_fields_on_raw(entry)
        if locator.get("raw_line_label") != label or locator.get("raw_marker_label") != "象":
            raise YijingTextEvidenceError(
                f"Raw Xiaoxiang locator mismatch for {hexagram} {label!r}: {locator!r}"
            )
        records = [
            r for r in _raw_xiaoxiang_records(hexagram) if r["raw_label"] == label
        ]
        if len(records) != 1 or records[0]["xiaoxiang_candidates"] != [emitted_text]:
            raise YijingTextEvidenceError(
                f"Raw Xiaoxiang value mismatch for {hexagram} {label!r}"
            )
        return True

    kind, correction = xiaoxiang_overlay_kind(hexagram, label)
    if not kind:
        raise YijingTextEvidenceError(
            f"No Xiaoxiang read-time overlay defines {hexagram!r} {label!r}"
        )
    if kind == "RELABEL":
        expected_locator = {
            "hexagram": hexagram,
            "block": HUMAN_BLOCK,
            "raw_line_label": correction["raw_line_label"],
            "raw_yao_text_prefixes": list(correction["raw_yao_text_prefixes"]),
            "raw_marker_label": "象",
        }
    else:
        expected_locator = {
            "hexagram": hexagram,
            "block": HUMAN_BLOCK,
            "raw_line_label": correction["raw_line_label"],
            "raw_yao_text_prefix": correction["raw_yao_text_prefix"],
            "raw_marker_label": "象",
        }
    if locator != expected_locator:
        raise YijingTextEvidenceError(
            f"Xiaoxiang overlay locator mismatch for {hexagram} {label!r}: {locator!r}"
        )
    if entry.get("overlay_id") != f"YIJING_XIAOXIANG_READ_TIME_OVERLAY:{hexagram}:{label}":
        raise YijingTextEvidenceError(
            f"Xiaoxiang overlay identity missing or wrong: {entry.get('overlay_id')!r}"
        )
    if entry.get("overlay_action") != xiaoxiang_overlay_action(kind, correction, label):
        raise YijingTextEvidenceError(
            f"Xiaoxiang overlay action mismatch: {entry.get('overlay_action')!r}"
        )
    if entry.get("overlay_reason") != correction["reason"]:
        raise YijingTextEvidenceError(
            f"Xiaoxiang overlay reason mismatch: {entry.get('overlay_reason')!r}"
        )
    if entry.get("overlay_policy") != COMMENTARY_OVERLAY_POLICY:
        raise YijingTextEvidenceError(
            f"Xiaoxiang overlay policy mismatch: {entry.get('overlay_policy')!r}"
        )
    if entry.get("overlay_precondition_passed") is not True:
        raise YijingTextEvidenceError("Xiaoxiang overlay preconditions not asserted as passed")
    raw_record = _match_raw_xiaoxiang_line(_raw_xiaoxiang_records(hexagram), locator)
    raw_candidates = raw_record["xiaoxiang_candidates"]
    if len(raw_candidates) != 1:
        raise YijingTextEvidenceError(
            f"Raw Xiaoxiang defect state not uniquely resolvable for {hexagram}: {raw_candidates!r}"
        )
    raw_candidate = raw_candidates[0]
    raw_state = entry.get("raw_source_state")
    if kind == "RELABEL":
        # The pinned Xiaoxiang text itself is unchanged; only the line label was.
        if raw_candidate != emitted_text:
            raise YijingTextEvidenceError(
                f"Relabel overlay result mismatch for {hexagram} {label!r}: "
                f"raw={raw_candidate!r}, emitted={emitted_text!r}"
            )
        expected_state = {
            "raw_line_label": correction["raw_line_label"],
            "raw_yao_text_prefixes": list(correction["raw_yao_text_prefixes"]),
            "raw_xiaoxiang": emitted_text,
        }
    elif kind == "RESTORE":
        if not raw_candidate.startswith(correction["raw_misattached_xiaoxiang_prefix"]):
            raise YijingTextEvidenceError(
                f"Restore overlay precondition drift for {hexagram}: raw under "
                f"{correction['raw_line_label']} is {raw_candidate!r}"
            )
        if emitted_text != correction["restored_xiaoxiang"][label] or emitted_text == raw_candidate:
            raise YijingTextEvidenceError(
                f"Restore overlay result mismatch for {hexagram} {label!r}: "
                f"emitted={emitted_text!r}"
            )
        expected_state = {
            "raw_line_label": correction["raw_line_label"],
            "raw_misattached_xiaoxiang": raw_candidate,
            "restored_xiaoxiang": emitted_text,
        }
    else:  # REASSIGN
        if raw_candidate != emitted_text:
            raise YijingTextEvidenceError(
                f"Reassign overlay result mismatch for {hexagram} {label!r}: "
                f"raw={raw_candidate!r}, emitted={emitted_text!r}"
            )
        expected_state = {
            "raw_line_label": correction["raw_line_label"],
            "raw_xiaoxiang": emitted_text,
        }
    if raw_state != expected_state:
        raise YijingTextEvidenceError(
            f"Xiaoxiang overlay raw source state mismatch for {hexagram} {label!r}: "
            f"{raw_state!r}"
        )
    if entry.get("external_references") != list(correction["sources"]):
        raise YijingTextEvidenceError(
            f"External reference pointers mismatch for {hexagram} {label!r}"
        )
    if entry.get("external_reference_status") != REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED:
        raise YijingTextEvidenceError(
            "External references must remain "
            f"{REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED}, not "
            f"{entry.get('external_reference_status')!r}"
        )
    if entry.get("bounded_supported_claim") != CLAIM_OVERLAY:
        raise YijingTextEvidenceError(
            f"Overlay evidence claim mismatch: {entry.get('bounded_supported_claim')!r}"
        )
    return True


def validate_special_xiaoxiang_evidence(entry, emitted_text):
    """Fail-closed validation for 用九/用六 Xiaoxiang evidence entries."""
    overlay_applied = _validate_evidence_common(entry, COMMENTARY_SOURCE_PATH)
    if overlay_applied:
        raise YijingTextEvidenceError("No read-time overlay exists for special-line Xiaoxiang")
    locator = entry.get("source_locator")
    hexagram = entry.get("hexagram")
    label = entry.get("line_label")
    if not isinstance(locator, dict) or locator.get("block") != HUMAN_BLOCK:
        raise YijingTextEvidenceError(
            f"Special Xiaoxiang locator must target the {HUMAN_BLOCK} block: {locator!r}"
        )
    if locator.get("hexagram") != hexagram:
        raise YijingTextEvidenceError(
            f"Special Xiaoxiang locator does not match its hexagram: {locator!r}"
        )
    _reject_overlay_fields_on_raw(entry)
    special = _special_cached().get(hexagram)
    if not special or special["label"] != label or locator.get("special_line_label") != label:
        raise YijingTextEvidenceError(
            f"Special Xiaoxiang locator does not resolve for {hexagram!r} {label!r}"
        )
    if special["xiaoxiang"] != emitted_text:
        raise YijingTextEvidenceError(
            f"Raw special Xiaoxiang value mismatch for {hexagram} {label!r}"
        )
    return True
