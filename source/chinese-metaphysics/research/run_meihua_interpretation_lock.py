#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRIDGE = HERE / "run_meihua_yijing_evidence.py"
SCHEMA = "MEIHUA_INTERPRETATION_LOCK_V1"


def fail(message, code=1):
    print(message, file=sys.stderr)
    raise SystemExit(code)


def run_json(command, label):
    proc = subprocess.run(command, text=True, capture_output=True)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit={proc.returncode}"
        fail(f"{label} failed: {detail}", proc.returncode or 1)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        fail(f"{label} returned invalid JSON: {exc}")


def canonical_sha256(value):
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_bridge_command(args):
    command = [sys.executable, str(BRIDGE)]
    if args.numbers is not None:
        command.extend(["--numbers", *[str(x) for x in args.numbers]])
    for flag, value in (
        ("--lunar-year", args.lunar_year),
        ("--month", args.month),
        ("--day", args.day),
        ("--hour", args.hour),
    ):
        if value is not None:
            command.extend([flag, str(value)])
    return command


def main():
    parser = argparse.ArgumentParser(
        description="Seal one Meihua interpretation/evidence packet before any outcome is supplied"
    )
    parser.add_argument("--question", required=True, help="Exact question text to bind into the lock")
    parser.add_argument("--numbers", nargs="+", type=int)
    parser.add_argument("--lunar-year", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--day", type=int)
    parser.add_argument("--hour", type=int)
    args = parser.parse_args()

    question = args.question.strip()
    if not question:
        fail("Question must not be empty", 2)

    evidence = run_json(build_bridge_command(args), "Meihua evidence bridge")
    if evidence.get("DOMAIN") != "MEIHUA_YIJING_EVIDENCE":
        fail("Unexpected evidence packet domain")

    structural = evidence.get("STRUCTURAL_READING") or {}
    if structural.get("STATUS") != "SOURCE_GROUNDED_STRUCTURAL_READING":
        fail("Cannot seal a classified interpretation lock from unclassified structural evidence")

    evidence_hash = canonical_sha256(evidence)
    lock_material = {
        "SCHEMA": SCHEMA,
        "QUESTION": question,
        "CASTING_MODE": evidence.get("CASTING_MODE"),
        "CASTING_INPUT": evidence.get("INPUT"),
        "STRUCTURAL_READING": structural,
        "YIJING_FACTS": {
            "MAIN_HEXAGRAM": (evidence.get("YIJING_EVIDENCE") or {}).get("NORMALIZED_HEXAGRAM"),
            "MOVING_LINE": (evidence.get("BRIDGE") or {}).get("MOVING_LINE"),
            "CHANGED_HEXAGRAM": (evidence.get("YIJING_EVIDENCE") or {}).get("CHANGED_HEXAGRAM"),
        },
        "EVIDENCE_SHA256": evidence_hash,
    }
    lock_hash = canonical_sha256(lock_material)

    packet = {
        **lock_material,
        "LOCK_SHA256": lock_hash,
        "LOCK_STATUS": "SEALED_BEFORE_OUTCOME",
        "OUTCOME_STATUS": "NOT_ACCEPTED_BY_LOCK_COMMAND",
        "SCORING_STATUS": "NOT_PERFORMED",
        "PREDICTIVE_STATUS": "NOT_ESTABLISHED",
        "EVIDENCE_PACKET": evidence,
        "NONCLAIMS": [
            "ENGINEERING_LOCK_FIXTURE_IS_NOT_PREDICTIVE_EVIDENCE",
            "NO_OUTCOME_WAS_AVAILABLE_TO_THIS_COMMAND",
            "NO_POST_OUTCOME_EDIT_IS_VALID_WITHOUT_CHANGING_LOCK_SHA256",
            "NO_PREDICTIVE_ACCURACY_CLAIM",
        ],
    }
    print(json.dumps(packet, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
