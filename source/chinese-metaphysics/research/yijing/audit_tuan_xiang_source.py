#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

PIN = "1a5a78b513c0e7b46dfb29f74043bcf978c32a3e"
HERE = Path(__file__).resolve().parent
UPSTREAM = (HERE / "../../upstreams/liuyao-divination").resolve()
DOC = UPSTREAM / "docs" / "易经六十四卦.md"


def fail(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)


if not UPSTREAM.exists():
    fail(f"Pinned upstream missing: {UPSTREAM}")
head = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
if head != PIN:
    fail(f"Pinned upstream SHA mismatch: expected {PIN}, got {head}")
if not DOC.exists():
    fail(f"Pinned Yi Jing source missing: {DOC}")

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao.data import HEXAGRAMS  # noqa: E402

expected_names = {rec["name"] for rec in HEXAGRAMS.values()}
text = DOC.read_text(encoding="utf-8")
heading_re = re.compile(r"^##\s+《([^》]+)》[^\n]*$", re.MULTILINE)
matches = list(heading_re.finditer(text))

sections = []
for i, match in enumerate(matches):
    start = match.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
    sections.append((match.group(1).strip(), text[start:end]))

actual_names = [name for name, _ in sections]
name_set = set(actual_names)
duplicate_sections = sorted({name for name in actual_names if actual_names.count(name) > 1})
missing_sections = sorted(expected_names - name_set)
extra_sections = sorted(name_set - expected_names)

# Only non-indented bullets count as hexagram-level 彖 / 大象. Line-level 小象
# in the pinned document are indented and are deliberately excluded here.
tuan_re = re.compile(r"^-\s+[^\n]*《彖》曰[：:][^\n]*$", re.MULTILINE)
daxiang_re = re.compile(r"^-\s+[^\n]*《象》曰[：:][^\n]*$", re.MULTILINE)

missing_tuan = []
missing_daxiang = []
duplicate_tuan = []
duplicate_daxiang = []
empty_tuan = []
empty_daxiang = []
section_report = []

for name, body in sections:
    tuan = tuan_re.findall(body)
    daxiang = daxiang_re.findall(body)
    if len(tuan) == 0:
        missing_tuan.append(name)
    elif len(tuan) > 1:
        duplicate_tuan.append({"hexagram": name, "count": len(tuan)})
    if len(daxiang) == 0:
        missing_daxiang.append(name)
    elif len(daxiang) > 1:
        duplicate_daxiang.append({"hexagram": name, "count": len(daxiang)})

    def payload(line):
        if not line:
            return ""
        parts = re.split(r"曰[：:]", line, maxsplit=1)
        return parts[1].strip() if len(parts) == 2 else ""

    if len(tuan) == 1 and not payload(tuan[0]):
        empty_tuan.append(name)
    if len(daxiang) == 1 and not payload(daxiang[0]):
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
    "missing_tuan": missing_tuan,
    "missing_daxiang": missing_daxiang,
    "duplicate_tuan": duplicate_tuan,
    "duplicate_daxiang": duplicate_daxiang,
    "empty_tuan": empty_tuan,
    "empty_daxiang": empty_daxiang,
}
status = "PASS" if (
    len(sections) == 64
    and len(name_set) == 64
    and not any(issues.values())
) else "FAIL"

result = {
    "DOMAIN": "YIJING_TUAN_XIANG_SOURCE_AUDIT",
    "SOURCE_REPO": "Johnson-Jia/liuyao-divination",
    "SOURCE_PIN": PIN,
    "SOURCE_PATH": "docs/易经六十四卦.md",
    "HEXAGRAM_SECTION_COUNT": len(sections),
    "UNIQUE_SECTION_COUNT": len(name_set),
    "EXPECTED_HEXAGRAM_COUNT": len(expected_names),
    "TUAN_MAIN_COUNT": sum(1 for x in section_report if x["tuan_main_count"] == 1),
    "DAXIANG_MAIN_COUNT": sum(1 for x in section_report if x["daxiang_main_count"] == 1),
    "ISSUES": issues,
    "STATUS": status,
    "NONCLAIMS": [
        "COVERAGE_AND_STRUCTURE_AUDIT_ONLY",
        "NO_TEN_WINGS_COMPLETENESS_CLAIM",
        "NO_TEXTUAL_CRITICAL_EDITION_CLAIM",
        "NO_RUNTIME_EXTRACTION_YET",
        "NO_INTERPRETATION_ACCURACY_CLAIM",
    ],
}
print(json.dumps(result, ensure_ascii=False, indent=2))
if status != "PASS":
    raise SystemExit(1)
