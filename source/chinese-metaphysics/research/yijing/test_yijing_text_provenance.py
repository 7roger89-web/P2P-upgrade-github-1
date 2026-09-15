#!/usr/bin/env python3
"""Selected-text provenance: representative cases + load-bearing negative tests.

Every positive case proves truthful per-field provenance for text actually
emitted by run_yijing_capability.py. Every negative test mutates an in-memory
copy of a real production packet and must be rejected by the SAME production
validator the capability runs before emitting a packet
(run_yijing_capability.validate_text_evidence_packet, backed by the module
validators in yijing_corpus/yijing_commentary). No committed constants, pins,
upstream bytes, or source files are mutated; external URLs are never fetched.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yijing_corpus import (  # noqa: E402
    CLAIM_RAW,
    CORPUS_SOURCE_PATH,
    CORRECTIONS,
    PIN,
    REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED,
    SUPPORT_STATUS_OVERLAY,
    SUPPORT_STATUS_RAW,
    YijingTextEvidenceError,
    load_raw_corpus,
)
from yijing_commentary import COMMENTARY_SOURCE_PATH  # noqa: E402
from run_yijing_capability import (  # noqa: E402
    gua_ci_evidence,
    special_xiaoxiang_evidence,
    validate_text_evidence_packet,
)

runner = HERE / "run_yijing_capability.py"

checks = []
negative = []


def check(name, condition):
    if not condition:
        raise AssertionError(f"FAILED: {name}")
    checks.append(name)


def expect_reject(packet, label):
    """The production validator must reject this mutated packet copy."""
    try:
        validate_text_evidence_packet(packet)
    except (SystemExit, YijingTextEvidenceError) as exc:
        if getattr(exc, "code", 1) == 0:
            raise AssertionError(f"{label}: rejected with exit code 0")
        negative.append(label)
        return
    raise AssertionError(f"{label}: production validator accepted invalid evidence")


def run(*args):
    result = subprocess.run([sys.executable, str(runner), *args], capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def ev(packet, field, label=None):
    for entry in packet["TEXT_EVIDENCE"]:
        if entry["field"] == field and entry.get("line_label") == label:
            return entry
    raise AssertionError(f"no evidence entry for {field} {label}")


def only_fields(packet, field, label=None, keep=False):
    kept = [
        e for e in packet["TEXT_EVIDENCE"]
        if (e["field"] == field and (label is None or e.get("line_label") == label))
    ]
    if keep:
        return kept
    return [e for e in packet["TEXT_EVIDENCE"] if e not in kept]


# ===========================================================================
# Representative case A: normal uncorrected hexagram (屯 moving 1).
# Raw pinned evidence for gua, yao, Xiaoxiang, Tuan, Daxiang.
# ===========================================================================
tun = run("--hexagram", "屯", "--moving", "1")
check("NORMAL_UNCORRECTED_PACKET", tun["NORMALIZED_HEXAGRAM"] == "水雷屯")
check("NORMAL_GUA_CI_RAW", (
    ev(tun, "GUA_CI")["support_status"] == SUPPORT_STATUS_RAW
    and ev(tun, "GUA_CI")["source_locator"] == {"hexagram": "水雷屯", "field": "gua_ci"}
    and ev(tun, "GUA_CI")["source_path"] == CORPUS_SOURCE_PATH
))
check("NORMAL_YAO_TEXT_RAW", (
    ev(tun, "SELECTED_YAO[].text", "初九")["support_status"] == SUPPORT_STATUS_RAW
    and ev(tun, "SELECTED_YAO[].text", "初九")["overlay_applied"] is False
    and ev(tun, "SELECTED_YAO[].text", "初九")["source_locator"] == {
        "hexagram": "水雷屯", "field": "yao", "label": "初九"}
))
check("NORMAL_XIAOXIANG_RAW_INDEPENDENT_SOURCE", (
    ev(tun, "SELECTED_YAO[].xiaoxiang", "初九")["support_status"] == SUPPORT_STATUS_RAW
    and ev(tun, "SELECTED_YAO[].xiaoxiang", "初九")["source_path"] == COMMENTARY_SOURCE_PATH
    and ev(tun, "SELECTED_YAO[].xiaoxiang", "初九")["source_locator"] == {
        "hexagram": "水雷屯", "block": "人间道", "raw_line_label": "初九", "raw_marker_label": "象"}
))
check("NORMAL_TUAN_RAW", ev(tun, "TUAN_TEXT")["support_status"] == SUPPORT_STATUS_RAW)
check("NORMAL_DAXIANG_RAW", ev(tun, "DAXIANG_TEXT")["support_status"] == SUPPORT_STATUS_RAW)
check("NORMAL_NO_EXTERNAL_REFS", (
    ev(tun, "GUA_CI")["external_reference_status"] == "NONE"
    and ev(tun, "TUAN_TEXT")["external_reference_status"] == "NONE"
))
check("NORMAL_COVERAGE_EXACT", tun["TEXT_EVIDENCE_COVERAGE"] == {
    "PRESENT_SOURCE_BOUND_TEXT_FIELDS": 8,
    "TEXT_EVIDENCE_FIELDS": 8,
    "EXACT_COVERAGE": True,
})
check("NORMAL_CHANGED_EVIDENCE_BOUND_TO_CHANGED_HEX", (
    {e["hexagram"] for e in only_fields(tun, "CHANGED_GUA_CI", keep=True)
     + only_fields(tun, "CHANGED_TUAN_TEXT", keep=True)
     + only_fields(tun, "CHANGED_DAXIANG_TEXT", keep=True)}
    == {tun["CHANGED_HEXAGRAM"]}
))

# ===========================================================================
# Representative case B: corrected Yao (地山谦 moving 2).
# Corrected text AND corrected Xiaoxiang must both be marked overlay, with the
# raw defect distinguishable and URLs reference-only.
# ===========================================================================
q2 = run("--hexagram", "谦", "--moving", "2")
q2_text = ev(q2, "SELECTED_YAO[].text", "六二")
q2_xiaoxiang = ev(q2, "SELECTED_YAO[].xiaoxiang", "六二")
check("QIAN2_TEXT_MARKED_OVERLAY", (
    q2_text["support_status"] == SUPPORT_STATUS_OVERLAY and q2_text["overlay_applied"] is True
))
check("QIAN2_TEXT_OVERLAY_IDENTITY", (
    q2_text["overlay_id"] == "YIJING_CORPUS_READ_TIME_OVERLAY:地山谦:六二"
    and q2_text["overlay_action"] == "REMOVE_RAW_LABEL 六三; SET 六二"
    and q2_text["overlay_precondition_passed"] is True
))
check("QIAN2_TEXT_RAW_DEFECT_DISTINGUISHABLE", (
    q2_text["raw_source_state"] == {"raw_label": "六三", "raw_text": "呜谦，贞吉。"}
    and q2_text["source_path"] == CORPUS_SOURCE_PATH
))
check("QIAN2_XIAOXIANG_MARKED_OVERLAY", (
    q2_xiaoxiang["support_status"] == SUPPORT_STATUS_OVERLAY
    and q2_xiaoxiang["overlay_id"] == "YIJING_XIAOXIANG_READ_TIME_OVERLAY:地山谦:六二"
    and q2_xiaoxiang["raw_source_state"]["raw_line_label"] == "六三"
))
check("QIAN2_YAO_AND_XIAOXIANG_INDEPENDENT_PROVENANCE", (
    q2_text["source_path"] == CORPUS_SOURCE_PATH
    and q2_xiaoxiang["source_path"] == COMMENTARY_SOURCE_PATH
    and q2_text["overlay_id"] != q2_xiaoxiang["overlay_id"]
    and q2_text["overlay_action"] != q2_xiaoxiang["overlay_action"]
))
check("QIAN2_URLS_REFERENCE_POINTER_ONLY", (
    q2_text["external_reference_status"] == REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED
    and q2_xiaoxiang["external_reference_status"] == REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED
    and q2_text["external_references"] == CORRECTIONS["地山谦"]["sources"]
))
check("QIAN2_CORRECTED_TEXT_UNCHANGED", q2["SELECTED_YAO"][0]["text"] == "鸣谦，贞吉。")
check("QIAN2_UNCORRECTED_FIELDS_STAY_RAW", (
    ev(q2, "GUA_CI")["support_status"] == SUPPORT_STATUS_RAW
    and ev(q2, "TUAN_TEXT")["support_status"] == SUPPORT_STATUS_RAW
    and ev(q2, "DAXIANG_TEXT")["support_status"] == SUPPORT_STATUS_RAW
))

# ===========================================================================
# Representative case C: corrected 师 (地水师 moving 4).
# The restored 六四 Yao text and the reassigned 六四 Xiaoxiang are overlay-
# derived and must say so; raw defect = missing line / misattached Xiang.
# ===========================================================================
shi = run("--hexagram", "师", "--moving", "4")
shi_text = ev(shi, "SELECTED_YAO[].text", "六四")
shi_xiaoxiang = ev(shi, "SELECTED_YAO[].xiaoxiang", "六四")
check("SHI4_TEXT_OVERLAY_RAW_LINE_MISSING", (
    shi_text["support_status"] == SUPPORT_STATUS_OVERLAY
    and shi_text["overlay_action"] == "SET 六四"
    and shi_text["raw_source_state"] == {"raw_label": "六四", "raw_text": None}
))
check("SHI4_XIAOXIANG_REASSIGN_TRUTHFUL", (
    shi_xiaoxiang["support_status"] == SUPPORT_STATUS_OVERLAY
    and shi_xiaoxiang["overlay_action"] == "REASSIGN RAW 左次 XIAOXIANG TO 六四"
    and shi_xiaoxiang["raw_source_state"]["raw_xiaoxiang"] == shi["SELECTED_YAO"][0]["xiaoxiang"]
    and shi["SELECTED_YAO"][0]["xiaoxiang"].startswith("左次")
))
check("SHI4_URLS_REFERENCE_POINTER_ONLY", (
    shi_text["external_reference_status"] == REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED
    and shi_xiaoxiang["external_references"] == CORRECTIONS["地水师"]["sources"]
))

# ===========================================================================
# Representative case D: commentary label overlay (雷水解).
# The emitted Tuan must be marked overlay-derived because the pinned marker
# is 象; it must NOT claim the raw marker was already correctly labelled.
# ===========================================================================
jie = run("--hexagram", "解")
jie_tuan = ev(jie, "TUAN_TEXT")
check("JIE_TUAN_MARKED_OVERLAY", (
    jie_tuan["support_status"] == SUPPORT_STATUS_OVERLAY
    and jie_tuan["overlay_id"] == "YIJING_COMMENTARY_LABEL_OVERLAY:雷水解:彖"
    and jie_tuan["overlay_action"] == "RELABEL 象 -> 彖"
))
check("JIE_TUAN_DOES_NOT_CLAIM_RAW_LABEL_WAS_CORRECT", (
    jie_tuan["source_locator"]["raw_marker_label"] == "象"
    and jie_tuan["raw_source_state"]["raw_marker_label"] == "象"
    and jie_tuan["source_locator"]["corrected_marker_label"] == "彖"
))
check("JIE_DAXIANG_STAYS_RAW", ev(jie, "DAXIANG_TEXT")["overlay_applied"] is False)
check("JIE_COVERAGE_EXACT", jie["TEXT_EVIDENCE_COVERAGE"] == {
    "PRESENT_SOURCE_BOUND_TEXT_FIELDS": 3,
    "TEXT_EVIDENCE_FIELDS": 3,
    "EXACT_COVERAGE": True,
})

# ===========================================================================
# Representative case E: special line (乾/坤 all six moving).
# Special-candidate text + Xiaoxiang evidence appears only when the candidate
# exists, and never for partial casts or static packets.
# ===========================================================================
q6 = run("--hexagram", "乾", "--moving", "1,2,3,4,5,6")
check("QIAN6_SPECIAL_TEXT_EVIDENCE_RAW_CORPUS", (
    ev(q6, "SPECIAL_YAO_CANDIDATE.text", "用九")["support_status"] == SUPPORT_STATUS_RAW
    and ev(q6, "SPECIAL_YAO_CANDIDATE.text", "用九")["source_locator"] == {
        "hexagram": "乾为天", "field": "yao", "label": "用九"}
))
check("QIAN6_SPECIAL_XIAOXIANG_EVIDENCE_RAW_COMMENTARY", (
    ev(q6, "SPECIAL_YAO_CANDIDATE.xiaoxiang", "用九")["support_status"] == SUPPORT_STATUS_RAW
    and ev(q6, "SPECIAL_YAO_CANDIDATE.xiaoxiang", "用九")["source_path"] == COMMENTARY_SOURCE_PATH
))
check("QIAN6_PRIORITY_BOUNDARY_PRESERVED", (
    q6["SPECIAL_YAO_CANDIDATE"]["interpretive_priority"] == "NOT_ASSERTED"
    and q6["SPECIAL_YAO_CANDIDATE"]["exposure_condition"] == "ALL_SIX_REGULAR_LINES_LISTED_AS_MOVING"
))
check("QIAN6_COVERAGE_20", q6["TEXT_EVIDENCE_COVERAGE"]["PRESENT_SOURCE_BOUND_TEXT_FIELDS"] == 20)
kun6 = run("--hexagram", "坤", "--moving", "6,5,4,3,2,1")
check("KUN6_SPECIAL_YONGLIU_EVIDENCE", (
    ev(kun6, "SPECIAL_YAO_CANDIDATE.text", "用六")["support_status"] == SUPPORT_STATUS_RAW
    and ev(kun6, "SPECIAL_YAO_CANDIDATE.xiaoxiang", "用六")["source_path"] == COMMENTARY_SOURCE_PATH
))
q5 = run("--hexagram", "乾", "--moving", "1,2,3,4,5")
check("QIAN5_NO_SPECIAL_EVIDENCE_WHEN_NO_CANDIDATE", (
    q5["SPECIAL_YAO_CANDIDATE"] is None
    and not [e for e in q5["TEXT_EVIDENCE"] if e["field"].startswith("SPECIAL_YAO_CANDIDATE")]
))
static_qian = run("--hexagram", "谦")
check("STATIC_NO_CHANGED_OR_SPECIAL_EVIDENCE", (
    static_qian["CHANGED_HEXAGRAM"] is None
    and static_qian["SPECIAL_YAO_CANDIDATE"] is None
    and sorted(e["field"] for e in static_qian["TEXT_EVIDENCE"])
    == ["DAXIANG_TEXT", "GUA_CI", "TUAN_TEXT"]
))

# ===========================================================================
# Representative case F: changed hexagram (谦 moving 2,3 -> 地水师).
# Changed Gua/Tuan/Daxiang evidence must exist, be bound to the changed
# hexagram only, and disappear for static packets.
# ===========================================================================
q23 = run("--hexagram", "谦", "--moving", "2,3")
changed_entries = [
    e for e in q23["TEXT_EVIDENCE"] if e["field"].startswith("CHANGED_")
]
check("QIAN23_CHANGED_EVIDENCE_EXACT_SET", (
    sorted(e["field"] for e in changed_entries)
    == ["CHANGED_DAXIANG_TEXT", "CHANGED_GUA_CI", "CHANGED_TUAN_TEXT"]
))
check("QIAN23_CHANGED_BOUND_TO_CHANGED_HEXAGRAM", (
    {e["hexagram"] for e in changed_entries} == {q23["CHANGED_HEXAGRAM"]} == {"地水师"}
))
check("QIAN23_CHANGED_TEXTS_MATCH_PACKET", (
    ev(q23, "CHANGED_GUA_CI")["hexagram"] == "地水师"
    and q23["CHANGED_GUA_CI"] is not None
    and q23["CHANGED_TUAN_TEXT"] is not None
    and q23["CHANGED_DAXIANG_TEXT"] is not None
))
check("QIAN23_CHANGED_FIELDS_RAW", (
    all(e["support_status"] == SUPPORT_STATUS_RAW for e in changed_entries)
))
check("QIAN23_MIXED_LINE_STATUSES", (
    ev(q23, "SELECTED_YAO[].text", "六二")["support_status"] == SUPPORT_STATUS_OVERLAY
    and ev(q23, "SELECTED_YAO[].text", "九三")["support_status"] == SUPPORT_STATUS_RAW
    and ev(q23, "SELECTED_YAO[].xiaoxiang", "六二")["support_status"] == SUPPORT_STATUS_OVERLAY
    and ev(q23, "SELECTED_YAO[].xiaoxiang", "九三")["support_status"] == SUPPORT_STATUS_RAW
))
check("QIAN23_COVERAGE_10", q23["TEXT_EVIDENCE_COVERAGE"] == {
    "PRESENT_SOURCE_BOUND_TEXT_FIELDS": 10,
    "TEXT_EVIDENCE_FIELDS": 10,
    "EXACT_COVERAGE": True,
})
check("INTERPRETATION_BOUNDARIES_PRESERVED", (
    q23["TEXTUAL_CRITICAL_EDITION_STATUS"] == "NOT_ESTABLISHED"
    and q23["INTERPRETATION_STATUS"] == "NOT_PERFORMED"
    and q23["SPECIAL_YAO_CANDIDATE"] is None
    and "NO_HISTORICAL_PRIMARY_SOURCE_VALIDATION" in q23["NONCLAIMS"]
))

# ===========================================================================
# Load-bearing negative tests. Same production validator the runtime uses.
# ===========================================================================

# 1. Wrong repo (corpus surface and commentary surface).
p = copy.deepcopy(tun)
ev(p, "GUA_CI")["repo"] = "Johnson-Jia/not-the-pinned-repo"
expect_reject(p, "WRONG_REPO_NEGATIVE_TEST(corpus)")
p = copy.deepcopy(tun)
ev(p, "TUAN_TEXT")["repo"] = "someone-else/liuyao-divination"
expect_reject(p, "WRONG_REPO_NEGATIVE_TEST(commentary)")

# 2. Wrong pin.
p = copy.deepcopy(tun)
ev(p, "GUA_CI")["pin"] = "0" * 40
expect_reject(p, "WRONG_PIN_NEGATIVE_TEST(raw)")
p = copy.deepcopy(q2)
ev(p, "SELECTED_YAO[].text", "六二")["pin"] = PIN[:-1] + "0"
expect_reject(p, "WRONG_PIN_NEGATIVE_TEST(overlay)")

# 3. Wrong source path (cross-surface confusion).
p = copy.deepcopy(tun)
ev(p, "GUA_CI")["source_path"] = COMMENTARY_SOURCE_PATH
expect_reject(p, "WRONG_PATH_NEGATIVE_TEST(corpus_claims_markdown)")
p = copy.deepcopy(tun)
ev(p, "SELECTED_YAO[].xiaoxiang", "初九")["source_path"] = CORPUS_SOURCE_PATH
expect_reject(p, "WRONG_PATH_NEGATIVE_TEST(xiaoxiang_claims_json)")

# 4. Path escape.
for bad_path in ["../../../outside/zhouyi.json", "data/../../evil.json", "/etc/passwd"]:
    p = copy.deepcopy(tun)
    ev(p, "GUA_CI")["source_path"] = bad_path
    expect_reject(p, f"PATH_ESCAPE_NEGATIVE_TEST({bad_path})")

# 5. Wrong logical locator.
p = copy.deepcopy(tun)
ev(p, "GUA_CI")["source_locator"]["hexagram"] = "坤为地"
expect_reject(p, "WRONG_LOCATOR_NEGATIVE_TEST(gua_ci_hexagram)")
p = copy.deepcopy(tun)
ev(p, "SELECTED_YAO[].text", "初九")["source_locator"]["label"] = "六二"
expect_reject(p, "WRONG_LOCATOR_NEGATIVE_TEST(yao_label)")
p = copy.deepcopy(tun)
ev(p, "TUAN_TEXT")["source_locator"]["raw_marker_label"] = "象"
expect_reject(p, "WRONG_LOCATOR_NEGATIVE_TEST(tuan_marker)")
p = copy.deepcopy(tun)
ev(p, "SELECTED_YAO[].xiaoxiang", "初九")["source_locator"]["raw_line_label"] = "六二"
expect_reject(p, "WRONG_LOCATOR_NEGATIVE_TEST(xiaoxiang_line)")

# 6. Raw source value mismatch (emitted text tampered; evidence can't support it).
p = copy.deepcopy(tun)
p["GUA_CI"] = "tampered，不实之辞。"
expect_reject(p, "RAW_VALUE_MISMATCH_NEGATIVE_TEST(gua_ci)")
p = copy.deepcopy(tun)
p["SELECTED_YAO"][0]["text"] = "tampered"
expect_reject(p, "RAW_VALUE_MISMATCH_NEGATIVE_TEST(yao_text)")
p = copy.deepcopy(tun)
p["TUAN_TEXT"] = "tampered"
expect_reject(p, "RAW_VALUE_MISMATCH_NEGATIVE_TEST(tuan)")

# 6b. Locator role/line binding (PROVENANCE_IDENTITY != TEXT_EQUALITY_ONLY).
# Each mutation keeps the RESOLVED value plausible by pointing the locator at a
# different real line and copying that line's true pinned text into the packet,
# so plain text equality would pass; only role binding can reject these.
raw_corpus = load_raw_corpus()

# A. Selected yao claims 初九 but the locator names 六二 (plausible value).
p = copy.deepcopy(tun)
ev(p, "SELECTED_YAO[].text", "初九")["source_locator"]["label"] = "六二"
p["SELECTED_YAO"][0]["text"] = raw_corpus["水雷屯"]["yao"]["六二"]
expect_reject(p, "WRONG_YAO_LINE_LOCATOR_NEGATIVE_TEST")

# B. Special yao claims 用九 but the locator names 上九 (plausible value).
p = copy.deepcopy(q6)
ev(p, "SPECIAL_YAO_CANDIDATE.text", "用九")["source_locator"]["label"] = "上九"
p["SPECIAL_YAO_CANDIDATE"]["text"] = raw_corpus["乾为天"]["yao"]["上九"]
expect_reject(p, "WRONG_SPECIAL_LINE_LOCATOR_NEGATIVE_TEST")

# C. Gua-ci evidence whose locator targets a yao line (plausible value).
p = copy.deepcopy(tun)
ev(p, "GUA_CI")["source_locator"] = {"hexagram": "水雷屯", "field": "yao", "label": "初九"}
p["GUA_CI"] = raw_corpus["水雷屯"]["yao"]["初九"]
expect_reject(p, "GUA_AS_YAO_LOCATOR_NEGATIVE_TEST")

# D. Hexagram-level gua evidence carrying a line label.
p = copy.deepcopy(tun)
ev(p, "GUA_CI")["line_label"] = "初九"
expect_reject(p, "GUA_WITH_LINE_LABEL_NEGATIVE_TEST(gua_ci)")
p = copy.deepcopy(q23)
ev(p, "CHANGED_GUA_CI")["line_label"] = "六三"
expect_reject(p, "GUA_WITH_LINE_LABEL_NEGATIVE_TEST(changed_gua_ci)")

# 7. Missing evidence for an emitted GUA_CI.
p = copy.deepcopy(tun)
p["TEXT_EVIDENCE"] = only_fields(p, "GUA_CI")
expect_reject(p, "MISSING_GUA_EVIDENCE_TEST")

# 8. Missing evidence for one SELECTED_YAO text among several lines.
p = copy.deepcopy(q23)
p["TEXT_EVIDENCE"] = [
    e for e in p["TEXT_EVIDENCE"]
    if not (e["field"] == "SELECTED_YAO[].text" and e["line_label"] == "九三")
]
expect_reject(p, "MISSING_YAO_EVIDENCE_TEST")

# 9. Missing Xiaoxiang evidence while the text evidence is present.
p = copy.deepcopy(q23)
p["TEXT_EVIDENCE"] = [
    e for e in p["TEXT_EVIDENCE"]
    if not (e["field"] == "SELECTED_YAO[].xiaoxiang" and e["line_label"] == "六二")
]
expect_reject(p, "MISSING_XIAOXIANG_EVIDENCE_TEST")

# 10. Extra evidence for an absent changed hexagram (static packet).
p = copy.deepcopy(static_qian)
p["TEXT_EVIDENCE"].append(gua_ci_evidence("地风升", field="CHANGED_GUA_CI"))
expect_reject(p, "EXTRA_CHANGED_EVIDENCE_TEST")

# 10b. Extra special evidence when no special candidate was emitted.
p = copy.deepcopy(q5)
p["TEXT_EVIDENCE"].append(
    special_xiaoxiang_evidence("乾为天", "用九", q6["SPECIAL_YAO_CANDIDATE"]["xiaoxiang"])
)
expect_reject(p, "EXTRA_SPECIAL_EVIDENCE_NEGATIVE_TEST")

# 11. Overlay-required text falsely marked as unmodified upstream.
p = copy.deepcopy(q2)
ev(p, "SELECTED_YAO[].text", "六二").update({
    "support_status": SUPPORT_STATUS_RAW,
    "overlay_applied": False,
    "overlay_id": None,
    "overlay_policy": None,
    "overlay_action": None,
    "overlay_reason": None,
    "overlay_precondition_passed": None,
    "raw_source_state": None,
    "bounded_supported_claim": CLAIM_RAW,
    "external_references": None,
    "external_reference_status": "NONE",
    "source_locator": {"hexagram": "地山谦", "field": "yao", "label": "六二"},
})
expect_reject(p, "OVERLAY_AS_RAW_NEGATIVE_TEST(yao_text)")
p = copy.deepcopy(q2)
ev(p, "SELECTED_YAO[].xiaoxiang", "六二").update({
    "support_status": SUPPORT_STATUS_RAW,
    "overlay_applied": False,
    "overlay_id": None,
    "overlay_policy": None,
    "overlay_action": None,
    "overlay_reason": None,
    "overlay_precondition_passed": None,
    "raw_source_state": None,
    "bounded_supported_claim": CLAIM_RAW,
    "external_references": None,
    "external_reference_status": "NONE",
    "source_locator": {
        "hexagram": "地山谦", "block": "人间道",
        "raw_line_label": "六二", "raw_marker_label": "象",
    },
})
expect_reject(p, "OVERLAY_AS_RAW_NEGATIVE_TEST(xiaoxiang)")

# 12. Unmodified text falsely marked as overlay.
p = copy.deepcopy(tun)
ev(p, "SELECTED_YAO[].text", "初九")["overlay_applied"] = True
expect_reject(p, "RAW_AS_OVERLAY_NEGATIVE_TEST(corpus)")
p = copy.deepcopy(tun)
ev(p, "TUAN_TEXT")["overlay_applied"] = True
expect_reject(p, "RAW_AS_OVERLAY_NEGATIVE_TEST(commentary)")

# 13. Missing overlay identity.
p = copy.deepcopy(q2)
ev(p, "SELECTED_YAO[].text", "六二")["overlay_id"] = None
expect_reject(p, "MISSING_OVERLAY_ID_NEGATIVE_TEST(yao_text)")
p = copy.deepcopy(shi)
ev(p, "SELECTED_YAO[].xiaoxiang", "六四")["overlay_id"] = None
expect_reject(p, "MISSING_OVERLAY_ID_NEGATIVE_TEST(xiaoxiang)")
p = copy.deepcopy(jie)
ev(p, "TUAN_TEXT")["overlay_id"] = None
expect_reject(p, "MISSING_OVERLAY_ID_NEGATIVE_TEST(label_overlay)")

# 14. Incorrect overlay result (emitted value is not the overlay result).
p = copy.deepcopy(q2)
p["SELECTED_YAO"][0]["text"] = "呜谦，贞吉。"
expect_reject(p, "WRONG_OVERLAY_RESULT_NEGATIVE_TEST(raw_defect_text_as_emitted)")
p = copy.deepcopy(shi)
p["SELECTED_YAO"][0]["text"] = "师右次，无咎。"
expect_reject(p, "WRONG_OVERLAY_RESULT_NEGATIVE_TEST(shi_invented_text)")
p = copy.deepcopy(shi)
p["SELECTED_YAO"][0]["xiaoxiang"] = "大無功也。"
expect_reject(p, "WRONG_OVERLAY_RESULT_NEGATIVE_TEST(xiaoxiang)")

# 15. External pointer promoted to verified authority.
for bad_status in [
    "VERIFIED_PRIMARY_SOURCE_AUTHORITY",
    "TEXTUAL_CRITICAL_EDITION_VALIDATED",
    "HISTORICAL_PRIMARY_SOURCE",
    "RUNTIME_VERIFIED_REMOTE",
]:
    p = copy.deepcopy(q2)
    ev(p, "SELECTED_YAO[].text", "六二")["external_reference_status"] = bad_status
    expect_reject(p, f"EXTERNAL_POINTER_AUTHORITY_NEGATIVE_TEST({bad_status})")
p = copy.deepcopy(jie)
ev(p, "TUAN_TEXT")["external_reference_status"] = "VERIFIED_PRIMARY_SOURCE_AUTHORITY"
expect_reject(p, "EXTERNAL_POINTER_AUTHORITY_NEGATIVE_TEST(label_overlay)")

# Extra: duplicate evidence entries are rejected.
p = copy.deepcopy(tun)
p["TEXT_EVIDENCE"].append(copy.deepcopy(ev(tun, "GUA_CI")))
expect_reject(p, "DUPLICATE_EVIDENCE_NEGATIVE_TEST")

# Extra: whole-packet evidence removal.
p = copy.deepcopy(tun)
p["TEXT_EVIDENCE"] = []
expect_reject(p, "EMPTY_EVIDENCE_NEGATIVE_TEST")

print(json.dumps({
    "DOMAIN": "YIJING_SELECTED_TEXT_PROVENANCE_AUDIT",
    "SOURCE_REPO": "Johnson-Jia/liuyao-divination",
    "SOURCE_PIN": PIN,
    "POSITIVE_CHECKS_PASSED": len(checks),
    "NEGATIVE_TESTS_REJECTED_BY_PRODUCTION_VALIDATOR": len(negative),
    "STATUS": "PASS",
    "NONCLAIMS": [
        "STRUCTURAL_PROVENANCE_ONLY",
        "NO_HISTORICAL_PRIMARY_SOURCE_VALIDATION",
        "NO_TEXTUAL_CRITICAL_EDITION_CLAIM",
        "NO_EXTERNAL_REFERENCE_RUNTIME_VERIFICATION",
        "NO_SPECIAL_YAO_PRIORITY_RULE",
        "NO_DIVINATION_JUDGMENT",
    ],
}, ensure_ascii=False, indent=2))
