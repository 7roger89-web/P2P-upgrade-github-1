#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yijing_corpus import PIN, UPSTREAM, load_corrected_corpus, load_raw_corpus  # noqa: E402
from yijing_commentary import load_corrected_xiaoxiang, load_special_xiaoxiang  # noqa: E402

sys.path.insert(0, str(UPSTREAM / "src"))
from liuyao import cast_board  # noqa: E402
from liuyao.data import BAGUA, HEXAGRAMS  # noqa: E402
from run_yijing_capability import changed_hexagram_name  # noqa: E402

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

xiaoxiang = load_corrected_xiaoxiang()
assert len(xiaoxiang) == 64
assert sum(len(lines) for lines in xiaoxiang.values()) == 64 * 6
assert xiaoxiang["地山谦"]["六二"].startswith("鳴謙貞吉")
assert xiaoxiang["地水师"]["六三"] == "師或輿尸，凶，大無功也。"
assert xiaoxiang["地水师"]["六四"].startswith("左次")
assert "志行正也" in xiaoxiang["水雷屯"]["初九"]
assert "大得民也" in xiaoxiang["水雷屯"]["初九"]
assert xiaoxiang["乾为天"]["上九"].startswith("“亢龍有悔”")
assert "用九" not in xiaoxiang["乾为天"]

special = load_special_xiaoxiang()
assert set(special) == {"乾为天", "坤为地"}
assert special["乾为天"]["label"] == "用九"
assert special["乾为天"]["source_yao_text"] == "見群龍無首，吉。"
assert "天德不可爲首" in special["乾为天"]["xiaoxiang"]
assert special["坤为地"]["label"] == "用六"
assert special["坤为地"]["source_yao_text"] == "利永貞。"
assert "以大終也" in special["坤为地"]["xiaoxiang"]

# Mechanical equivalence: every one-line transformation across all 64 hexagrams
# must match the pinned upstream's public cast_board() result. The oracle's month/day
# are irrelevant to hexagram transformation but valid inputs to its broader Liuyao API.
transform_oracle_cases = 0
for name, rec in sorted(records.items()):
    for pos in range(1, 7):
        expected = cast_board(name, pos, "子", "甲子").changed_hexagram
        actual = changed_hexagram_name(rec, [pos])
        assert actual == expected, (name, pos, actual, expected)
        transform_oracle_cases += 1
assert transform_oracle_cases == 64 * 6

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
assert qian["SELECTED_YAO"][0]["xiaoxiang"].startswith("鳴謙貞吉")
assert qian["SELECTED_YAO"][1]["xiaoxiang"].startswith("勞謙君子")
assert qian["CHANGED_HEXAGRAM"] == "地水师"
assert qian["CHANGED_UPPER_TRIGRAM"] == "坤"
assert qian["CHANGED_LOWER_TRIGRAM"] == "坎"
assert qian["CHANGED_GUA_CI"] == corrected["地水师"]["gua_ci"]
assert qian["TRANSFORMATION_RULE"] == "FLIP_MOVING_LINES_BOTTOM_TO_TOP_THEN_MAP_TRIGRAMS"
assert qian["INTERPRETATION_STATUS"] == "NOT_PERFORMED"
assert qian["SPECIAL_YAO_CANDIDATE"] is None

static_qian = run(["--hexagram", "谦"])
assert static_qian["CHANGED_HEXAGRAM"] is None
assert static_qian["CHANGED_GUA_CI"] is None
assert static_qian["SPECIAL_YAO_CANDIDATE"] is None

shi = run(["--hexagram", "师", "--moving", "4"])
assert shi["NORMALIZED_HEXAGRAM"] == "地水师"
assert shi["SELECTED_YAO"][0] == {
    "position": 4,
    "label": "六四",
    "text": "师左次，无咎。",
    "xiaoxiang": xiaoxiang["地水师"]["六四"],
}

tun = run(["--hexagram", "屯", "--moving", "1"])
assert "志行正也" in tun["SELECTED_YAO"][0]["xiaoxiang"]
assert "大得民也" in tun["SELECTED_YAO"][0]["xiaoxiang"]

qian_all = run(["--hexagram", "乾", "--moving", "1,2,3,4,5,6"])
assert qian_all["CHANGED_HEXAGRAM"] == "坤为地"
assert qian_all["SPECIAL_YAO_CANDIDATE"] == {
    "label": "用九",
    "text": "见群龙无首，吉。",
    "xiaoxiang": special["乾为天"]["xiaoxiang"],
    "exposure_condition": "ALL_SIX_REGULAR_LINES_LISTED_AS_MOVING",
    "interpretive_priority": "NOT_ASSERTED",
}

kun_all = run(["--hexagram", "坤", "--moving", "6,5,4,3,2,1"])
assert kun_all["CHANGED_HEXAGRAM"] == "乾为天"
assert kun_all["SPECIAL_YAO_CANDIDATE"] == {
    "label": "用六",
    "text": "利永贞。",
    "xiaoxiang": special["坤为地"]["xiaoxiang"],
    "exposure_condition": "ALL_SIX_REGULAR_LINES_LISTED_AS_MOVING",
    "interpretive_priority": "NOT_ASSERTED",
}

qian_partial = run(["--hexagram", "乾", "--moving", "1,2,3,4,5"])
assert qian_partial["SPECIAL_YAO_CANDIDATE"] is None

bad = subprocess.run([sys.executable, str(runner), "--hexagram", "师", "--moving", "7"], capture_output=True, text=True)
assert bad.returncode != 0

print(json.dumps({
    "DOMAIN": "YIJING_CORPUS_AUDIT",
    "SOURCE_PIN": PIN,
    "RAW_KNOWN_ISSUE_COUNT": len(raw_issues),
    "CORRECTED_ISSUE_COUNT": len(corrected_issues),
    "YIJING_LOOKUP": "PASS",
    "YIJING_XIAOXIANG_COUNT": sum(len(lines) for lines in xiaoxiang.values()),
    "YIJING_XIAOXIANG": "PASS",
    "YIJING_SPECIAL_YAO_COUNT": len(special),
    "YIJING_SPECIAL_YAO": "PASS",
    "YIJING_TRANSFORM_ORACLE_CASES": transform_oracle_cases,
    "YIJING_TRANSFORM": "PASS",
    "STATUS": "PASS",
    "NONCLAIMS": [
        "STRUCTURAL_INTEGRITY_ONLY",
        "NO_SPECIAL_YAO_PRIORITY_RULE",
        "NO_TEXTUAL_CRITICAL_EDITION_CLAIM",
        "NO_INTERPRETATION_ACCURACY_CLAIM",
    ],
}, ensure_ascii=False, indent=2))
