#!/usr/bin/env python3
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yijing_corpus import UPSTREAM  # noqa: E402
from yijing_commentary import (  # noqa: E402
    XIAOXIANG_CORRECTIONS,
    load_xiaoxiang_records,
)

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao.data import BAGUA, HEXAGRAMS  # noqa: E402


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


def audit(sections):
    expected_by_name = {rec["name"]: expected_labels(rec) for rec in HEXAGRAMS.values()}
    names = [section["hexagram"] for section in sections]
    by_name = {section["hexagram"]: section["records"] for section in sections}

    issues = {
        "duplicate_sections": sorted({name for name in names if names.count(name) > 1}),
        "missing_sections": sorted(set(expected_by_name) - set(by_name)),
        "extra_sections": sorted(set(by_name) - set(expected_by_name)),
        "missing_yao": [],
        "duplicate_yao": [],
        "unexpected_regular_yao": [],
        "missing_xiaoxiang": [],
        "duplicate_xiaoxiang": [],
    }
    verified = 0

    for name, labels in expected_by_name.items():
        found = {}
        for record in by_name.get(name, []):
            found.setdefault(record["label"], []).append(record)

        for label in sorted(set(found) - set(labels)):
            issues["unexpected_regular_yao"].append({
                "hexagram": name,
                "label": label,
                "count": len(found[label]),
            })

        for position, label in enumerate(labels, start=1):
            records = found.get(label, [])
            if not records:
                issues["missing_yao"].append({"hexagram": name, "position": position, "label": label})
                continue
            if len(records) > 1:
                issues["duplicate_yao"].append({
                    "hexagram": name,
                    "position": position,
                    "label": label,
                    "count": len(records),
                })
                continue
            xiang = records[0]["xiaoxiang_candidates"]
            if not xiang:
                issues["missing_xiaoxiang"].append({"hexagram": name, "position": position, "label": label})
                continue
            if len(xiang) > 1:
                issues["duplicate_xiaoxiang"].append({
                    "hexagram": name,
                    "position": position,
                    "label": label,
                    "count": len(xiang),
                })
                continue
            verified += 1

    return issues, verified


def main():
    raw_sections = load_xiaoxiang_records(apply_corrections=False)
    corrected_sections = load_xiaoxiang_records(apply_corrections=True)
    raw_issues, raw_verified = audit(raw_sections)
    corrected_issues, corrected_verified = audit(corrected_sections)

    expected_raw_label_defects = {
        ("地山谦", "六二"),
        ("地水师", "六四"),
    }
    observed_raw_missing = {
        (item["hexagram"], item["label"])
        for item in raw_issues["missing_yao"]
    }
    observed_raw_unexpected = {
        (item["hexagram"], item["label"])
        for item in raw_issues["unexpected_regular_yao"]
    }

    corrections_applied = []
    for section in corrected_sections:
        for record in section["records"]:
            if "correction" in record:
                corrections_applied.append({
                    "hexagram": section["hexagram"],
                    "label": record["label"],
                    **record["correction"],
                })

    expected_count = 64 * 6
    raw_defects_match = (
        observed_raw_missing == expected_raw_label_defects
        and observed_raw_unexpected == {("地山谦", "六三")}
        and not raw_issues["duplicate_sections"]
        and not raw_issues["missing_sections"]
        and not raw_issues["extra_sections"]
        and not raw_issues["duplicate_yao"]
        and not raw_issues["missing_xiaoxiang"]
        and not raw_issues["duplicate_xiaoxiang"]
    )
    corrected_clean = not any(corrected_issues.values())
    status = "PASS" if (
        raw_defects_match
        and corrected_clean
        and corrected_verified == expected_count
        and len(corrections_applied) == 3
    ) else "FAIL"

    print(json.dumps({
        "DOMAIN": "YIJING_XIAOXIANG_SOURCE_AUDIT",
        "SOURCE_REPO": "Johnson-Jia/liuyao-divination",
        "SOURCE_PIN": "1a5a78b513c0e7b46dfb29f74043bcf978c32a3e",
        "SOURCE_PATH": "docs/易经六十四卦.md",
        "EXPECTED_REGULAR_YAO_COUNT": expected_count,
        "RAW_VERIFIED_YAO_XIAOXIANG_PAIRS": raw_verified,
        "RAW_ISSUES": raw_issues,
        "CORRECTED_VERIFIED_YAO_XIAOXIANG_PAIRS": corrected_verified,
        "CORRECTED_ISSUES": corrected_issues,
        "CORRECTIONS": XIAOXIANG_CORRECTIONS,
        "CORRECTIONS_APPLIED": corrections_applied,
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
