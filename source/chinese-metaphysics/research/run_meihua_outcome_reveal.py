#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_meihua_interpretation_lock import SCHEMA as LOCK_SCHEMA, canonical_sha256  # noqa: E402

REVEAL_SCHEMA = "MEIHUA_OUTCOME_REVEAL_V1"


def fail(message, code=1):
    print(message, file=sys.stderr)
    raise SystemExit(code)


def load_json(path):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read lock packet: {exc}", 2)


def lock_material(lock):
    return {
        "SCHEMA": lock.get("SCHEMA"),
        "QUESTION": lock.get("QUESTION"),
        "CASTING_MODE": lock.get("CASTING_MODE"),
        "CASTING_INPUT": lock.get("CASTING_INPUT"),
        "STRUCTURAL_READING": lock.get("STRUCTURAL_READING"),
        "YIJING_FACTS": lock.get("YIJING_FACTS"),
        "EVIDENCE_SHA256": lock.get("EVIDENCE_SHA256"),
    }


def verify_lock(lock):
    if lock.get("SCHEMA") != LOCK_SCHEMA:
        fail(f"Unsupported lock schema: {lock.get('SCHEMA')!r}")
    provided = lock.get("LOCK_SHA256")
    if not isinstance(provided, str) or len(provided) != 64:
        fail("Lock packet is missing a valid LOCK_SHA256")
    expected = canonical_sha256(lock_material(lock))
    if provided != expected:
        fail("LOCK_SHA256 mismatch: lock packet was modified after sealing")

    evidence = lock.get("EVIDENCE_PACKET")
    if not isinstance(evidence, dict):
        fail("Lock packet is missing EVIDENCE_PACKET")
    evidence_hash = canonical_sha256(evidence)
    if evidence_hash != lock.get("EVIDENCE_SHA256"):
        fail("EVIDENCE_SHA256 mismatch: evidence packet was modified after sealing")
    return provided, evidence_hash


def main():
    parser = argparse.ArgumentParser(
        description="Verify one sealed Meihua interpretation lock, then attach an outcome without scoring it"
    )
    parser.add_argument("--lock-file", required=True, help="JSON output from run_meihua_interpretation_lock.py")
    parser.add_argument("--outcome", required=True, help="Exact outcome text revealed after the lock existed")
    args = parser.parse_args()

    outcome = args.outcome.strip()
    if not outcome:
        fail("Outcome must not be empty", 2)

    lock = load_json(args.lock_file)
    lock_hash, evidence_hash = verify_lock(lock)
    outcome_hash = canonical_sha256({"OUTCOME": outcome})

    packet = {
        "SCHEMA": REVEAL_SCHEMA,
        "LOCK_SHA256": lock_hash,
        "LOCK_VERIFICATION": "PASS",
        "EVIDENCE_SHA256": evidence_hash,
        "EVIDENCE_VERIFICATION": "PASS",
        "QUESTION": lock.get("QUESTION"),
        "LOCKED_CASTING_MODE": lock.get("CASTING_MODE"),
        "LOCKED_CASTING_INPUT": lock.get("CASTING_INPUT"),
        "LOCKED_STRUCTURAL_READING": lock.get("STRUCTURAL_READING"),
        "LOCKED_YIJING_FACTS": lock.get("YIJING_FACTS"),
        "OUTCOME": outcome,
        "OUTCOME_SHA256": outcome_hash,
        "REVEAL_STATUS": "LOCK_VERIFIED_OUTCOME_ATTACHED",
        "SCORING_STATUS": "NOT_PERFORMED",
        "PREDICTIVE_STATUS": "NOT_ESTABLISHED",
        "NONCLAIMS": [
            "ENGINEERING_REVEAL_FIXTURE_IS_NOT_PREDICTIVE_EVIDENCE",
            "OUTCOME_ATTACHMENT_DOES_NOT_IMPLY_CORRECTNESS",
            "NO_AUTOMATIC_MATCHING_OR_SCORING",
            "NO_PREDICTIVE_ACCURACY_CLAIM",
        ],
    }
    print(json.dumps(packet, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
