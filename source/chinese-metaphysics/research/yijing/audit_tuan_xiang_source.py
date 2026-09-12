#!/usr/bin/env python3
import json
import sys

from yijing_corpus import UPSTREAM

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao.data import HEXAGRAMS  # noqa: E402

from yijing_commentary import (  # noqa: E402
    LABEL_CORRECTIONS,
    PIN,
    load_sections,
)

expected_names = {rec["name"] for rec in HEXAGRAMS.values()}


def summarize(sections):
    actual_names = [x["hexagram"] for x in sections]
    name_set = set(actual_names)
    duplicate_sections = sorted({name for name in actual_names if actual_names.count(name) > 1})
    missing_sections = sorted(expected_names - name_set)
    extra_sections = sorted(name_set - expected_names)

    missing_tuan = []
    missing_daxiang = []
    duplicate_tuan = []
    duplicate_daxiang = []
    empty_tuan = []
    empty_daxiang = []
    section_report = []

    for section in sections:
        name = section["hexagram"]
        tuan = [x["text"] for x in section["markers"] if x["label"] == "彖"]
        daxiang = [x["text"] for x in section["markers"] if x["label"] == "象"]

        if len(tuan) == 0:
            missing_tuan.append(name)
        elif len(tuan) > 1:
            duplicate_tuan.append({"hexagram": name, "count": len(tuan)})
        if len(daxiang) == 0:
            missing_daxiang.append(name)
        elif len(daxiang) > 1:
            duplicate_daxiang.append({"hexagram": name, "count": len(daxiang)})

        if len(tuan) == 1 and not tuan[0]:
            empty_tuan.append(name)
        if len(daxiang) == 1 and not daxiang[0]:
            empty_daxiang.append(name)

        section_report.append({
            "hexagram": name,
            "tuan_main_count": len(tuan),
            "daxiang_main_count": len(daxiang),
        })

    issues = {
        "duplicate_sections": duplicate_sections,
        "missing_sections": missing_sections,
        "extra_sections": extra_sections,
        "missing_tuan": sorted(missing_tuan),
        "missing_daxiang": sorted(missing_daxiang),
        "duplicate_tuan": sorted(duplicate_tuan, key=lambda x: x["hexagram"]),
        "duplicate_daxiang": sorted(duplicate_daxiang, key=lambda x: x["hexagram"]),
        "empty_tuan": sorted(empty_tuan),
        "empty_daxiang": sorted(empty_daxiang),
    }

    return {
        "section_count": len(sections),
        "unique_section_count": len(name_set),
        "tuan_main_count": sum(1 for x in section_report if x["tuan_main_count"] == 1),
        "daxiang_main_count": sum(1 for x in section_report if x["daxiang_main_count"] == 1),
        "issues": issues,
    }


raw = summarize(load_sections(apply_label_corrections=False))
corrected = summarize(load_sections(apply_label_corrections=True))

expected_defects = sorted(LABEL_CORRECTIONS)
expected_raw_issues = {
    "duplicate_sections": [],
    "missing_sections": [],
    "extra_sections": [],
    "missing_tuan": expected_defects,
    "missing_daxiang": [],
    "duplicate_tuan": [],
    "duplicate_daxiang": [{"hexagram": name, "count": 2} for name in expected_defects],
    "empty_tuan": [],
    "empty_daxiang": [],
}
clean_issues = {key: [] for key in expected_raw_issues}

status = "PASS" if (
    raw["section_count"] == 64
    and raw["unique_section_count"] == 64
    and raw["issues"] == expected_raw_issues
    and corrected["section_count"] == 64
    and corrected["unique_section_count"] == 64
    and corrected["tuan_main_count"] == 64
    and corrected["daxiang_main_count"] == 64
    and corrected["issues"] == clean_issues
) else "FAIL"

result = {
    "DOMAIN": "YIJING_TUAN_XIANG_SOURCE_AUDIT",
    "SOURCE_REPO": "Johnson-Jia/liuyao-divination",
    "SOURCE_PIN": PIN,
    "SOURCE_PATH": "docs/易经六十四卦.md",
    "EXPECTED_HEXAGRAM_COUNT": len(expected_names),
    "RAW": {
        "HEXAGRAM_SECTION_COUNT": raw["section_count"],
        "UNIQUE_SECTION_COUNT": raw["unique_section_count"],
        "TUAN_MAIN_COUNT": raw["tuan_main_count"],
        "DAXIANG_MAIN_COUNT": raw["daxiang_main_count"],
        "ISSUES": raw["issues"],
    },
    "LABEL_CORRECTIONS": LABEL_CORRECTIONS,
    "CORRECTED": {
        "HEXAGRAM_SECTION_COUNT": corrected["section_count"],
        "UNIQUE_SECTION_COUNT": corrected["unique_section_count"],
        "TUAN_MAIN_COUNT": corrected["tuan_main_count"],
        "DAXIANG_MAIN_COUNT": corrected["daxiang_main_count"],
        "ISSUES": corrected["issues"],
    },
    "STATUS": status,
    "NONCLAIMS": [
        "TUAN_AND_HEXAGRAM_LEVEL_DAXIANG_ONLY",
        "NO_TEN_WINGS_COMPLETENESS_CLAIM",
        "NO_TEXTUAL_CRITICAL_EDITION_CLAIM",
        "NO_INTERPRETATION_ACCURACY_CLAIM",
    ],
}
print(json.dumps(result, ensure_ascii=False, indent=2))
if status != "PASS":
    raise SystemExit(1)
