#!/usr/bin/env python3
"""Load-bearing negative tests for Meihua provenance truthfulness.

These tests MUST fail closed on:
  - wrong engine pin
  - wrong source path
  - wrong source anchor/function locator
  - missing evidence for an applied rule
  - rule evidence present for a rule not in RULE_TRACE
  - unsupported relation prefix being promoted to a structural signal
  - claiming CLASSICAL_TEXT_GROUNDED without sufficient classical evidence
"""
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_meihua_capability.py"
BRIDGE_RUNNER = HERE.parent / "run_meihua_yijing_evidence.py"
LOCK_RUNNER = HERE.parent / "run_meihua_interpretation_lock.py"
UPSTREAM = (HERE.parent.parent / "upstreams" / "meihua-yishu").resolve()
PIN = "8a9a5e0f482dd225bfe4a1c52c2ae5546228607a"


def run_json(args, cwd=None):
    r = subprocess.run(
        [sys.executable, str(RUNNER), *args], capture_output=True, text=True, cwd=cwd
    )
    return r.returncode, r.stdout, r.stderr


def run_python(script, args, expect_fail=False, cwd=None):
    r = subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True, cwd=cwd
    )
    if expect_fail:
        assert r.returncode != 0, f"Expected failure from {script} {args}, got exit=0"
        return r.stderr + r.stdout
    assert r.returncode == 0, f"{script} {args} failed: {r.stderr}"
    return json.loads(r.stdout)


def load_runner_module():
    spec = importlib.util.spec_from_file_location("rmc", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_number():
    return run_python(RUNNER, ["--numbers", "7", "4", "11"])


# ---- Positive baseline first ----
base = run_number()
assert base["ENGINE_PIN"] == PIN
assert base["PROVENANCE_STATUS"] == "PINNED_ENGINE_SOURCE_BOUND_SELECTED_SLICE"
assert base["CLASSICAL_TEXT_GROUNDED"] is False
assert base["ENGINE_REPO"] == "muyen/meihua-yishu"
assert base["RUNTIME_NETWORK_DEPENDENCY"] is False
assert base["PREDICTIVE_STATUS"] == "NOT_ESTABLISHED_NEGATIVE_EVIDENCE_PRESERVED"
for ev in base["RULE_EVIDENCE"]:
    assert ev["pin"] == PIN
    assert ev["support_status"] in {
        "DIRECT_ENGINE_SOURCE_SUPPORT",
        "REPO_DECLARED_METHOD_SUPPORT",
        "INSUFFICIENT_SOURCE_SUPPORT",
    }
    assert ev["source_path"], f"missing source_path for {ev['rule_id']}"
    assert ev["bounded_supported_claim"], f"missing claim for {ev['rule_id']}"

# RULE_EVIDENCE must exactly cover RULE_TRACE and nothing else
trace_set = set(base["RULE_TRACE"])
evidence_ids = {ev["rule_id"] for ev in base["RULE_EVIDENCE"]}
assert trace_set == evidence_ids, f"trace/evidence mismatch: {trace_set ^ evidence_ids}"

# Every applied rule must have load-bearing evidence (fail closed for missing)
rmc = load_runner_module()
for rid in base["RULE_TRACE"]:
    assert rid in rmc.RULE_EVIDENCE_CATALOG, f"Missing evidence catalog entry for {rid}"

print("POSITIVE_BASELINE=PASS")


# ---- Helper: call production validator on a mutated copy of the catalog ----
TEST_RULE = base["RULE_TRACE"][0]  # a rule that IS applied in the baseline cast


def _mutated_catalog(**overrides):
    """Return a deep copy of the canonical catalog with one applied entry mutated."""
    cat = copy.deepcopy(rmc.RULE_EVIDENCE_CATALOG)
    rule_id = overrides.pop("_rule", TEST_RULE)
    cat[rule_id].update(overrides)
    return cat


def _expect_validation_rejects(catalog, rule_ids, label):
    try:
        rmc.rule_evidence_for(list(rule_ids), catalog=catalog)
    except SystemExit as e:
        assert e.code == 3, f"{label}: expected exit code 3, got {e.code}"
        return
    raise AssertionError(f"{label}: production validator unexpectedly accepted invalid evidence")


# ---- Startup submodule pin guard is retained AND evidence validator rejects wrong pin ----
src = RUNNER.read_text()
assert "if head != PIN:" in src, "runner no longer performs strict pin verification"
_mut = _mutated_catalog(pin="0000000000000000000000000000000000000000")
_expect_validation_rejects(_mut, base["RULE_TRACE"], "WRONG_PIN")
print("WRONG_PIN_MUTATION_TEST=PASS")

# ---- Wrong repo ----
_mut = _mutated_catalog(repo="not/muyen-meihua-yishu")
_expect_validation_rejects(_mut, base["RULE_TRACE"], "WRONG_REPO")
print("WRONG_REPO_MUTATION_TEST=PASS")

# ---- Wrong source path (non-existent relative path) ----
_mut = _mutated_catalog(source_path="does/not/exist.py")
_expect_validation_rejects(_mut, base["RULE_TRACE"], "WRONG_PATH")
print("WRONG_PATH_MUTATION_TEST=PASS")

# ---- Path traversal / escape pinned root ----
_mut = _mutated_catalog(source_path="../../../etc/passwd")
_expect_validation_rejects(_mut, base["RULE_TRACE"], "PATH_ESCAPE")
print("PATH_ESCAPE_MUTATION_TEST=PASS")

# ---- Wrong source anchor (literal locator not present) ----
_mut = _mutated_catalog(source_anchor="def definitely_not_real_function_xyz(")
_expect_validation_rejects(_mut, base["RULE_TRACE"], "WRONG_ANCHOR")
print("WRONG_ANCHOR_MUTATION_TEST=PASS")

# ---- Missing bounded_supported_claim ----
_mut = _mutated_catalog(bounded_supported_claim="")
_expect_validation_rejects(_mut, base["RULE_TRACE"], "MISSING_CLAIM")
print("MISSING_CLAIM_MUTATION_TEST=PASS")

# ---- Method reference path/anchor validation (REPO_DECLARED_METHOD_SUPPORT) ----
# Use a rule that IS applied in this cast and HAS a method_reference.
_method_rule = next(
    (r for r in base["RULE_TRACE"] if rmc.RULE_EVIDENCE_CATALOG[r].get("method_reference")),
    None,
)
assert _method_rule is not None, "no applied rule carries a method_reference"
_mut = copy.deepcopy(rmc.RULE_EVIDENCE_CATALOG)
_mut[_method_rule]["method_reference"]["source_path"] = "does/not/exist.md"
_expect_validation_rejects(_mut, base["RULE_TRACE"], "METHOD_REF_WRONG_PATH")
_mut = copy.deepcopy(rmc.RULE_EVIDENCE_CATALOG)
_mut[_method_rule]["method_reference"]["source_anchor"] = "### NO_SUCH_HEADING_XYZ"
_expect_validation_rejects(_mut, base["RULE_TRACE"], "METHOD_REF_WRONG_ANCHOR")
print("METHOD_REFERENCE_VALIDATION_TEST=PASS")

# ---- Negative: missing evidence for an applied rule ----
# Catalog is missing a rule_id that is in RULE_TRACE.
_missing_cat = copy.deepcopy(rmc.RULE_EVIDENCE_CATALOG)
del _missing_cat["MEIHUA_NUMBER_CAST_UPPER_LOWER"]
_expect_validation_rejects(_missing_cat, base["RULE_TRACE"], "MISSING_RULE_EVIDENCE")
print("MISSING_RULE_EVIDENCE_MUTATION_TEST=PASS")

# ---- Negative: extra evidence emitted for a rule NOT in RULE_TRACE ----
# The production rule_evidence_for only iterates the applied rule_ids, but
# fail-closed requires that the emitted RULE_EVIDENCE.rule_id list exactly
# matches RULE_TRACE (this is also enforced in the out{} assembly). Assert
# both: if caller-supplied trace contains a rule not in catalog -> fail (above);
# if a trace omits a catalog rule, that catalog rule is not emitted (no leak).
out_ids = [e["rule_id"] for e in base["RULE_EVIDENCE"]]
assert out_ids == base["RULE_TRACE"], "emitted evidence leaks rule ids outside RULE_TRACE"
# Also exercise via validator: passing a trace with an extra fake id must fail.
try:
    rmc.rule_evidence_for(base["RULE_TRACE"] + ["RULE_NOT_IN_CATALOG"])
except SystemExit as e:
    assert e.code == 3
else:
    raise AssertionError("validator must fail when RULE_TRACE references an unknown rule")
print("UNAPPLIED_RULE_EVIDENCE_MUTATION_TEST=PASS")


# ---- Negative: unsupported relation prefix rejected at the bridge ----
# Import the bridge module and confirm classify_ti_yong_relation returns
# UNCLASSIFIED for fabricated/gibberish relation text.
spec = importlib.util.spec_from_file_location(
    "rmye", BRIDGE_RUNNER
)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
assert bridge.classify_ti_yong_relation("fake_relation_XYZ") == "UNCLASSIFIED"
# Sanity check: every engine-produced relation does map.
spec_mc = importlib.util.spec_from_file_location(
    "_mc_for_test", UPSTREAM / "scripts" / "meihua_calc.py"
)
mc = importlib.util.module_from_spec(spec_mc)
spec_mc.loader.exec_module(mc)
for ti in ["金", "木", "水", "火", "土"]:
    for yong in ["金", "木", "水", "火", "土"]:
        rel = mc.analyze_wuxing(ti, yong)
        sig = bridge.classify_ti_yong_relation(rel)
        assert sig != "UNCLASSIFIED", f"Engine relation not classified: {rel}"
print("UNKNOWN_RELATION_SIGNAL_NEGATIVE_TEST=PASS")


# ---- Negative: overclaimed CLASSICAL_TEXT_GROUNDED rejected by bridge ----
# Bridge refuses to seal on an unexpected (i.e. classical-grounded) Meihua
# provenance status. We verify the acceptance check string is present.
bridge_src = BRIDGE_RUNNER.read_text()
assert "PINNED_ENGINE_SOURCE_BOUND_SELECTED_SLICE" in bridge_src
assert "Refusing to seal a bridge on an unexpected Meihua provenance status" in bridge_src
# Lock refuses non engine-bound status.
lock_src = LOCK_RUNNER.read_text()
assert "ENGINE_SOURCE_BOUND_STRUCTURAL_READING" in lock_src
# Also make sure the old overclaim labels no longer appear in runner/bridge/lock
# output contracts (as a structural guard).
runner_src = RUNNER.read_text()
assert "CLASSICAL_TEXT_GROUNDED_SELECTED_SLICE" not in runner_src, "old overclaim still in runner"
assert "SOURCE_GROUNDED_STRUCTURAL_READING" not in bridge_src, "old overclaim still in bridge"
print("OVERCLAIMED_CLASSICAL_STATUS_NEGATIVE_TEST=PASS")


# ---- Mechanical regressions: number casting ----
num = run_python(RUNNER, ["--numbers", "7", "4", "11"])
assert num["MAIN_HEXAGRAM"] == "山雷頤"
assert num["MOVING_LINE"] == 4
assert num["MUTUAL_HEXAGRAM"] == "坤為地"
assert num["CHANGED_HEXAGRAM"] == "火雷噬嗑"
assert num["TI_YONG_RELATION"].startswith("體克用")
assert num["CASTING_MODE"] == "NUMBER_CASTING"
assert num["BODY_USE"]["體卦"].startswith("震")
assert num["BODY_USE"]["用卦"].startswith("艮")
print("NUMBER_CAST_MECHANICS_UNCHANGED=PASS")


# ---- Mechanical regressions: time casting ----
tm = run_python(RUNNER, ["--lunar-year", "2024", "--month", "12", "--day", "8", "--hour", "14"])
assert tm["CASTING_MODE"] == "TRADITIONAL_TIME_CASTING"
assert tm["ARITHMETIC"]
assert tm["UPPER_TRIGRAM"] and tm["LOWER_TRIGRAM"]
assert tm["MOVING_LINE"] in (1, 2, 3, 4, 5, 6)
assert tm["MAIN_HEXAGRAM"] and tm["CHANGED_HEXAGRAM"] and tm["MUTUAL_HEXAGRAM"]
assert tm["TI_YONG_RELATION"]
# traditional casting must NOT mention the modern second-level formula
arith_text = json.dumps(tm["ARITHMETIC"], ensure_ascii=False)
assert "分" not in arith_text and "秒" not in arith_text, "modern second-level leak into traditional cast"
print("TIME_CAST_MECHANICS_UNCHANGED=PASS")


# ---- Bridge regression ----
br = run_python(BRIDGE_RUNNER, ["--numbers", "7", "4", "11"])
assert br["BRIDGE_ASSERTIONS"]["MOVING_LINE_MATCHES_SELECTED_YAO"] == "PASS"
assert br["BRIDGE_ASSERTIONS"]["SELECTED_YAO_TEXT_PRESENT"] == "PASS"
assert br["BRIDGE_ASSERTIONS"]["SELECTED_XIAOXIANG_PRESENT"] == "PASS"
TAUTOLOGICAL_BRIDGE_ASSERTION_REMOVED=True

# Real structural invariant: canonical upper/lower trigrams (extracted via the
# bridge's canonical_trigram helper) map through the Yi Jing HEXAGRAM_BY_TRIGRAMS
# table to the EXACT YIJING_MAIN_HEXAGRAM_CANONICAL emitted by the bridge, and
# the Meihua moving line matches the selected Yao position. This uses the
# bridge's own canonicalization/table — no new algorithm, no display-name
# equality.
spec_b = importlib.util.spec_from_file_location("_bridge_test_", BRIDGE_RUNNER)
bridge_test = importlib.util.module_from_spec(spec_b)
# main() is guarded by `if __name__ == "__main__":`, so exec_module is safe
# under a different module __name__ without touching argparse.
spec_b.loader.exec_module(bridge_test)

upper_raw = br["BRIDGE"]["MEIHUA_UPPER_TRIGRAM_RAW"]
lower_raw = br["BRIDGE"]["MEIHUA_LOWER_TRIGRAM_RAW"]
upper_can = bridge_test.canonical_trigram(upper_raw)
lower_can = bridge_test.canonical_trigram(lower_raw)
expected_main = bridge_test.yijing_runtime.HEXAGRAM_BY_TRIGRAMS.get((upper_can, lower_can))
assert expected_main == br["BRIDGE"]["YIJING_MAIN_HEXAGRAM_CANONICAL"], (
    f"Structural bridge drift: ({upper_can},{lower_can}) -> {expected_main!r}, "
    f"bridge emitted {br['BRIDGE']['YIJING_MAIN_HEXAGRAM_CANONICAL']!r}"
)
selected = br["YIJING_EVIDENCE"]["SELECTED_YAO"]
assert len(selected) == 1 and selected[0]["position"] == br["BRIDGE"]["MOVING_LINE"]
STRUCTURAL_BRIDGE_INVARIANT_TEST = True
print("STRUCTURAL_BRIDGE_INVARIANT=PASS")
assert br["STRUCTURAL_READING"]["CLASSICAL_TEXT_GROUNDED"] is False
assert br["STRUCTURAL_READING"]["RUNTIME_NETWORK_DEPENDENCY"] is False
print("MEIHUA_YIJING_BRIDGE_UNCHANGED=PASS")


# ---- Lock semantic regression ----
lk = run_python(LOCK_RUNNER, ["--question", "provenance test", "--numbers", "7", "4", "11"])
assert lk["LOCK_STATUS"] == "SEALED_BEFORE_OUTCOME"
assert lk["OUTCOME_STATUS"] == "NOT_ACCEPTED_BY_LOCK_COMMAND"
assert lk["SCORING_STATUS"] == "NOT_PERFORMED"
assert lk["PREDICTIVE_STATUS"] == "NOT_ESTABLISHED_NEGATIVE_EVIDENCE_PRESERVED"
print("INTERPRETATION_LOCK_SEMANTICS_UNCHANGED=PASS")


# ---- Determinism ----
lk2 = run_python(LOCK_RUNNER, ["--question", "provenance test", "--numbers", "7", "4", "11"])
assert lk["LOCK_SHA256"] == lk2["LOCK_SHA256"], "lock hash is not deterministic"
print("LOCK_HASH_DETERMINISTIC=PASS")


print("ALL_PROVENANCE_TRUTHFULNESS_TESTS=PASS")
