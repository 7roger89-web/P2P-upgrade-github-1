#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_meihua_interpretation_lock import SCHEMA as INTERPRETATION_LOCK_SCHEMA, canonical_sha256  # noqa: E402

SCHEMA = "MEIHUA_PREDICTION_CLAIM_LOCK_V1"


def fail(message, code=1):
    print(message, file=sys.stderr)
    raise SystemExit(code)


def load_json(path):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read interpretation lock: {exc}", 2)


def interpretation_lock_material(lock):
    return {
        "SCHEMA": lock.get("SCHEMA"),
        "QUESTION": lock.get("QUESTION"),
        "CASTING_MODE": lock.get("CASTING_MODE"),
        "CASTING_INPUT": lock.get("CASTING_INPUT"),
        "STRUCTURAL_READING": lock.get("STRUCTURAL_READING"),
        "YIJING_FACTS": lock.get("YIJING_FACTS"),
        "EVIDENCE_SHA256": lock.get("EVIDENCE_SHA256"),
    }


def verify_interpretation_lock(lock):
    if lock.get("SCHEMA") != INTERPRETATION_LOCK_SCHEMA:
        fail(f"Unsupported interpretation lock schema: {lock.get('SCHEMA')!r}")
    provided = lock.get("LOCK_SHA256")
    if not isinstance(provided, str) or len(provided) != 64:
        fail("Interpretation lock is missing a valid LOCK_SHA256")
    expected = canonical_sha256(interpretation_lock_material(lock))
    if provided != expected:
        fail("LOCK_SHA256 mismatch: interpretation lock was modified after sealing")
    evidence = lock.get("EVIDENCE_PACKET")
    if not isinstance(evidence, dict):
        fail("Interpretation lock is missing EVIDENCE_PACKET")
    if canonical_sha256(evidence) != lock.get("EVIDENCE_SHA256"):
        fail("EVIDENCE_SHA256 mismatch: evidence packet was modified after sealing")
    return provided


def normalize_labels(labels):
    cleaned = [str(label).strip() for label in labels]
    if any(not label for label in cleaned):
        fail("Outcome labels must not be empty", 2)
    unique = sorted(set(cleaned))
    if len(unique) < 2:
        fail("Categorical claim requires at least two unique outcome labels", 2)
    if len(unique) != len(cleaned):
        fail("Outcome labels must be unique", 2)
    return unique


def main():
    parser = argparse.ArgumentParser(
        description="Seal one explicit categorical prediction claim before any outcome is supplied"
    )
    parser.add_argument("--lock-file", required=True, help="JSON output from run_meihua_interpretation_lock.py")
    parser.add_argument("--outcome-labels", nargs="+", required=True, help="Closed set of allowed outcome labels")
    parser.add_argument("--predicted-label", required=True, help="One predeclared label from the allowed set")
    args = parser.parse_args()

    lock = load_json(args.lock_file)
    interpretation_lock_sha = verify_interpretation_lock(lock)
    labels = normalize_labels(args.outcome_labels)
    predicted = args.predicted_label.strip()
    if predicted not in labels:
        fail("Predicted label must be one of the declared outcome labels", 2)

    claim_material = {
        "SCHEMA": SCHEMA,
        "INTERPRETATION_LOCK_SHA256": interpretation_lock_sha,
        "QUESTION": lock.get("QUESTION"),
        "OUTCOME_LABEL_SET": labels,
        "PREDICTED_LABEL": predicted,
        "SCORING_RULE": "EXACT_LABEL_MATCH",
        "LABEL_MATCH_POLICY": "EXACT_CASE_SENSITIVE_STRING_MATCH",
    }
    claim_sha = canonical_sha256(claim_material)

    packet = {
        **claim_material,
        "CLAIM_SHA256": claim_sha,
        "CLAIM_STATUS": "SEALED_BEFORE_OUTCOME",
        "OUTCOME_STATUS": "NOT_ACCEPTED_BY_CLAIM_LOCK_COMMAND",
        "SCORING_STATUS": "RULE_LOCKED_NOT_PERFORMED",
        "PREDICTIVE_STATUS": "NOT_ESTABLISHED",
        "INTERPRETATION_LOCK": lock,
        "NONCLAIMS": [
            "ENGINEERING_CLAIM_FIXTURE_IS_NOT_PREDICTIVE_EVIDENCE",
            "PREDICTED_LABEL_IS_EXPLICITLY_DECLARED_NOT_INFERRED_FROM_STRUCTURAL_SIGNAL",
            "NO_OUTCOME_WAS_AVAILABLE_TO_THIS_COMMAND",
            "NO_SCORE_WAS_COMPUTED",
            "NO_PREDICTIVE_ACCURACY_CLAIM",
        ],
    }
    print(json.dumps(packet, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
