#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

PIN = "1a5a78b513c0e7b46dfb29f74043bcf978c32a3e"
HERE = Path(__file__).resolve().parent
UPSTREAM = (HERE / "../../upstreams/liuyao-divination").resolve()


def fail(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)


if not UPSTREAM.exists():
    fail(f"Pinned upstream missing: {UPSTREAM}")
head = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
if head != PIN:
    fail(f"Pinned upstream SHA mismatch: expected {PIN}, got {head}")

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao.data import BAGUA, HEXAGRAMS  # noqa: E402

corpus = json.loads((UPSTREAM / "data" / "zhouyi.json").read_text(encoding="utf-8"))
records = {rec["name"]: rec for rec in HEXAGRAMS.values()}
expected_names = set(records)
actual_names = set(corpus)
issues = []

if len(expected_names) != 64:
    issues.append({"type": "ENGINE_HEXAGRAM_COUNT", "expected": 64, "actual": len(expected_names)})
if len(actual_names) != 64:
    issues.append({"type": "CORPUS_HEXAGRAM_COUNT", "expected": 64, "actual": len(actual_names)})
for name in sorted(expected_names - actual_names):
    issues.append({"type": "MISSING_HEXAGRAM", "hexagram": name})
for name in sorted(actual_names - expected_names):
    issues.append({"type": "EXTRA_HEXAGRAM", "hexagram": name})

pos_names = ["初", "二", "三", "四", "五", "上"]
for name in sorted(expected_names & actual_names):
    rec = records[name]
    entry = corpus[name]
    if not str(entry.get("gua_ci", "")).strip():
        issues.append({"type": "EMPTY_GUA_CI", "hexagram": name})

    bits = BAGUA[rec["lower"]]["yao"] + BAGUA[rec["upper"]]["yao"]
    expected_labels = []
    for i, bit in enumerate(bits):
        stem = "九" if bit else "六"
        if i == 0:
            label = f"初{stem}"
        elif i == 5:
            label = f"上{stem}"
        else:
            label = f"{stem}{pos_names[i]}"
        expected_labels.append(label)

    yao = entry.get("yao", {})
    actual_core = {k for k in yao if k not in {"用九", "用六"}}
    for label in expected_labels:
        if label not in actual_core:
            issues.append({"type": "MISSING_YAO_LABEL", "hexagram": name, "label": label})
        elif not str(yao[label]).strip():
            issues.append({"type": "EMPTY_YAO_TEXT", "hexagram": name, "label": label})
    for label in sorted(actual_core - set(expected_labels)):
        issues.append({"type": "UNEXPECTED_YAO_LABEL", "hexagram": name, "label": label})

for name, special in [("乾为天", "用九"), ("坤为地", "用六")]:
    if special not in corpus.get(name, {}).get("yao", {}):
        issues.append({"type": "MISSING_SPECIAL_YAO", "hexagram": name, "label": special})

result = {
    "DOMAIN": "YIJING_CORPUS_AUDIT",
    "SOURCE_REPO": "Johnson-Jia/liuyao-divination",
    "SOURCE_PIN": PIN,
    "SOURCE_PATH": "data/zhouyi.json",
    "ENGINE_HEXAGRAM_COUNT": len(expected_names),
    "CORPUS_HEXAGRAM_COUNT": len(actual_names),
    "ISSUE_COUNT": len(issues),
    "ISSUES": issues,
    "STATUS": "PASS" if not issues else "FAIL",
    "NONCLAIMS": [
        "STRUCTURAL_INTEGRITY_ONLY",
        "NO_TEXTUAL_CRITICAL_EDITION_CLAIM",
        "NO_INTERPRETATION_ACCURACY_CLAIM",
    ],
}
print(json.dumps(result, ensure_ascii=False, indent=2))
if issues:
    raise SystemExit(1)
