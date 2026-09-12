#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yijing_corpus import UPSTREAM, verify_pin  # noqa: E402

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao.data import BAGUA, HEXAGRAMS  # noqa: E402

DOC = UPSTREAM / "docs" / "易经六十四卦.md"
SECTION_RE = re.compile(r"^##\s+《([^》]+)》[^\n]*$", re.MULTILINE)
TAG_RE = re.compile(r"<[^>]+>")
YAO_RE = re.compile(r"^(初[九六]|[九六][二三四五]|上[九六])[：:](.*)$")
XIANG_RE = re.compile(r"《象》曰[：:]?(.*)$")


def clean(text):
    return TAG_RE.sub("", text).strip()


def clean_bullet(text):
    return clean(re.sub(r"^\s*-\s+", "", text))


def expected_labels(rec):
    bits = BAGUA[rec["lower"]]["yao"] + BAGUA[rec["upper"]]["yao"]
    labels = []
    nums = {2: "二", 3: "三", 4: "四", 5: "五"}
    for position, bit in enumerate(bits, start=1):
        stem = "九" if bit else "六"
        if position == 1:
            labels.append(f"初{stem}")
        elif position == 6:
            labels.append(f"上{stem}")
        else:
            labels.append(f"{stem}{nums[position]}")
    return labels


def extract_xiaoxiang(lines, yao_index):
    found = []
    for j in range(yao_index + 1, len(lines)):
        line = lines[j]
        # A new top-level red-font bullet starts the next yao/use-line block.
        if line.startswith("- <font") and 'color="#ff0000"' in line:
            break
        if "《象》曰" not in line:
            continue
        match = XIANG_RE.search(clean(line))
        if not match:
            continue
        payload = match.group(1).strip()
        if payload:
            found.append(payload)
    return found


def main():
    verify_pin()
    if not DOC.exists():
        raise RuntimeError(f"Pinned Yi Jing source missing: {DOC}")

    text = DOC.read_text(encoding="utf-8")
    headings = list(SECTION_RE.finditer(text))
    sections = {}
    duplicate_sections = []
    for i, heading in enumerate(headings):
        name = heading.group(1).strip()
        body = text[heading.end() : headings[i + 1].start() if i + 1 < len(headings) else len(text)]
        if name in sections:
            duplicate_sections.append(name)
        sections[name] = body.splitlines()

    expected_by_name = {rec["name"]: expected_labels(rec) for rec in HEXAGRAMS.values()}
    missing_sections = sorted(set(expected_by_name) - set(sections))
    extra_sections = sorted(set(sections) - set(expected_by_name))

    missing_yao = []
    duplicate_yao = []
    unexpected_regular_yao = []
    missing_xiaoxiang = []
    duplicate_xiaoxiang = []
    records = []

    for name, labels in expected_by_name.items():
        lines = sections.get(name, [])
        found = {}
        for idx, line in enumerate(lines):
            if not line.startswith("- <font") or 'color="#ff0000"' not in line:
                continue
            match = YAO_RE.match(clean_bullet(line))
            if not match:
                continue
            label = match.group(1)
            found.setdefault(label, []).append(idx)

        for label in sorted(set(found) - set(labels)):
            unexpected_regular_yao.append({"hexagram": name, "label": label, "count": len(found[label])})

        for position, label in enumerate(labels, start=1):
            indices = found.get(label, [])
            if not indices:
                missing_yao.append({"hexagram": name, "position": position, "label": label})
                continue
            if len(indices) > 1:
                duplicate_yao.append({"hexagram": name, "position": position, "label": label, "count": len(indices)})
                continue

            xiang = extract_xiaoxiang(lines, indices[0])
            if not xiang:
                missing_xiaoxiang.append({"hexagram": name, "position": position, "label": label})
                continue
            if len(xiang) > 1:
                duplicate_xiaoxiang.append({"hexagram": name, "position": position, "label": label, "count": len(xiang)})
                continue
            records.append({
                "hexagram": name,
                "position": position,
                "label": label,
                "xiaoxiang": xiang[0],
            })

    issues = {
        "duplicate_sections": sorted(set(duplicate_sections)),
        "missing_sections": missing_sections,
        "extra_sections": extra_sections,
        "missing_yao": missing_yao,
        "duplicate_yao": duplicate_yao,
        "unexpected_regular_yao": unexpected_regular_yao,
        "missing_xiaoxiang": missing_xiaoxiang,
        "duplicate_xiaoxiang": duplicate_xiaoxiang,
    }
    expected_count = 64 * 6
    status = "PASS" if (
        len(headings) == 64
        and len(expected_by_name) == 64
        and len(records) == expected_count
        and not any(issues.values())
    ) else "FAIL"

    print(json.dumps({
        "DOMAIN": "YIJING_XIAOXIANG_SOURCE_AUDIT",
        "SOURCE_REPO": "Johnson-Jia/liuyao-divination",
        "SOURCE_PIN": "1a5a78b513c0e7b46dfb29f74043bcf978c32a3e",
        "SOURCE_PATH": "docs/易经六十四卦.md",
        "HEXAGRAM_SECTION_COUNT": len(headings),
        "EXPECTED_REGULAR_YAO_COUNT": expected_count,
        "VERIFIED_YAO_XIAOXIANG_PAIRS": len(records),
        "ISSUES": issues,
        "STATUS": status,
        "NONCLAIMS": [
            "SIX_REGULAR_LINES_PER_HEXAGRAM_ONLY",
            "EXCLUDES_QIAN_YONGJIU_AND_KUN_YONGLIU",
            "NO_FULL_TEN_WINGS_COMPLETENESS_CLAIM",
            "NO_TEXTUAL_CRITICAL_EDITION_CLAIM",
            "NO_DIVINATION_INTERPRETATION_CLAIM",
        ],
    }, ensure_ascii=False, indent=2))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
