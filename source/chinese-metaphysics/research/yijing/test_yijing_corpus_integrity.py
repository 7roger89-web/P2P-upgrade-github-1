#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yijing_corpus import PIN, UPSTREAM, load_corrected_corpus, load_raw_corpus  # noqa: E402

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao.data import BAGUA, HEXAGRAMS  # noqa: E402

records = {rec["name"]: rec for rec in HEXAGRAMS.values()}
pos_names = ["初", "二", "三", "四", "五", "上"]


def audit(corpus):
    issues = []
    expected_names = set(records)
    actual_names = set(corpus)
    if len(expected_names) != 64:
        issues.append(("ENGINE_HEXAGRAM_COUNT", len(expected_names)))
    if len(actual_names) != 64:
        issues.append(("CORPUS_HEXAGRAM_COUNT", len(actual_names)))
    for name in sorted(expected_names - actual_names):
        issues.append(("MISSING_HEXAGRAM", name))
    for name in sorted(actual_names - expected_names):
        issues.append(("EXTRA_HEXAGRAM", name))

    for name in sorted(expected_names & actual_names):
        rec = records[name]
        entry = corpus[name]
        if not str(entry.get("gua_ci", "")).strip():
            issues.append(("EMPTY_GUA_CI", name))
        bits = BAGUA[rec["lower"]]["yao"] + BAGUA[rec["upper"]]["yao"]
        expected_labels = []
        for i, bit in enumerate(bits):
            stem = "九" if bit else "六"
            label = f"初{stem}" if i == 0 else (f"上{stem}" if i == 5 else f"{stem}{pos_names[i]}")
            expected_labels.append(label)
        yao = entry.get("yao", {})
        actual_core = {k for k in yao if k not in {"用九", "用六"}}
        for label in expected_labels:
            if label not in actual_core:
                issues.append(("MISSING_YAO_LABEL", name, label))
            elif not str(yao[label]).strip():
                issues.append(("EMPTY_YAO_TEXT", name, label))
        for label in sorted(actual_core - set(expected_labels)):
            issues.append(("UNEXPECTED_YAO_LABEL", name, label))

    for name, special in [("乾为天", "用九"), ("坤为地", "用六")]:
        if special not in corpus.get(name, {}).get("yao", {}):
            issues.append(("MISSING_SPECIAL_YAO", name, special))
    return issues


raw_issues = audit(load_raw_corpus())
expected_raw = {
    ("MISSING_YAO_LABEL", "地山谦", "六二"),
    ("UNEXPECTED_YAO_LABEL", "地山谦", "六三"),
    ("MISSING_YAO_LABEL", "地水师", "六四"),
}
assert set(raw_issues) == expected_raw, raw_issues

corrected = load_corrected_corpus()
corrected_issues = audit(corrected)
assert corrected_issues == [], corrected_issues
assert corrected["地山谦"]["yao"]["六二"] == "鸣谦，贞吉。"
assert "六三" not in corrected["地山谦"]["yao"]
assert corrected["地水师"]["yao"]["六四"] == "师左次，无咎。"

runner = HERE / "run_yijing_capability.py"

def run(args):
    r = subprocess.run([sys.executable, str(runner), *args], capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout)

qian = run(["--hexagram", "谦", "--moving", "2,3"])
assert qian["DOMAIN"] == "YIJING"
assert qian["NORMALIZED_HEXAGRAM"] == "地山谦"
assert [x["label"] for x in qian["SELECTED_YAO"]] == ["六二", "九三"]
assert qian["SELECTED_YAO"][0]["text"] == "鸣谦，贞吉。"
assert qian["INTERPRETATION_STATUS"] == "NOT_PERFORMED"

shi = run(["--hexagram", "师", "--moving", "4"])
assert shi["NORMALIZED_HEXAGRAM"] == "地水师"
assert shi["SELECTED_YAO"][0] == {"position": 4, "label": "六四", "text": "师左次，无咎。"}

bad = subprocess.run([sys.executable, str(runner), "--hexagram", "师", "--moving", "7"], capture_output=True, text=True)
assert bad.returncode != 0

print(json.dumps({
    "DOMAIN": "YIJING_CORPUS_AUDIT",
    "SOURCE_PIN": PIN,
    "RAW_KNOWN_ISSUE_COUNT": len(raw_issues),
    "CORRECTED_ISSUE_COUNT": len(corrected_issues),
    "YIJING_LOOKUP": "PASS",
    "STATUS": "PASS",
    "NONCLAIMS": ["STRUCTURAL_INTEGRITY_ONLY", "NO_TEXTUAL_CRITICAL_EDITION_CLAIM", "NO_INTERPRETATION_ACCURACY_CLAIM"],
}, ensure_ascii=False, indent=2))
