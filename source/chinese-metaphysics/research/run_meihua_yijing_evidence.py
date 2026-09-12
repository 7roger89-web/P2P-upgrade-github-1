#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEIHUA_RUNNER = HERE / "meihua-yishu" / "run_meihua_capability.py"
YIJING_DIR = HERE / "yijing"
YIJING_RUNNER = YIJING_DIR / "run_yijing_capability.py"

sys.path.insert(0, str(YIJING_DIR))
import run_yijing_capability as yijing_runtime  # noqa: E402

TRIGRAM_NORMALIZATION = {
    "離": "离",
    "兌": "兑",
}


def fail(message, code=1):
    print(message, file=sys.stderr)
    raise SystemExit(code)


def run_json(command, label):
    proc = subprocess.run(command, text=True, capture_output=True)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit={proc.returncode}"
        fail(f"{label} failed: {detail}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        fail(f"{label} returned invalid JSON: {exc}")


def canonical_trigram(name):
    # Meihua reports display labels such as "艮 ☶". The Yi Jing runtime keys
    # by the trigram name only, so strip the decorative symbol before the small
    # traditional/simplified normalization needed for 離/兌.
    token = str(name or "").strip().split()[0] if str(name or "").strip() else ""
    return TRIGRAM_NORMALIZATION.get(token, token)


def main():
    parser = argparse.ArgumentParser(
        description="Mechanical bridge: Meihua number casting -> source-grounded Yi Jing evidence"
    )
    parser.add_argument("--numbers", nargs="+", type=int, required=True, help="Two or three Meihua casting numbers")
    args = parser.parse_args()

    if len(args.numbers) not in (2, 3):
        fail("Number casting usage: --numbers N1 N2 [N3]", 2)

    meihua = run_json(
        [sys.executable, str(MEIHUA_RUNNER), "--numbers", *[str(x) for x in args.numbers]],
        "Meihua casting",
    )
    if meihua.get("DOMAIN") != "MEIHUA_YISHU" or meihua.get("CASTING_MODE") != "NUMBER_CASTING":
        fail("Unexpected Meihua packet contract")

    upper = canonical_trigram(meihua.get("UPPER_TRIGRAM"))
    lower = canonical_trigram(meihua.get("LOWER_TRIGRAM"))
    moving = meihua.get("MOVING_LINE")
    if upper not in yijing_runtime.BAGUA or lower not in yijing_runtime.BAGUA:
        fail(f"Cannot bridge Meihua trigrams into Yi Jing: upper={upper!r}, lower={lower!r}")
    if not isinstance(moving, int) or not 1 <= moving <= 6:
        fail(f"Invalid Meihua moving line: {moving!r}")

    canonical_main = yijing_runtime.HEXAGRAM_BY_TRIGRAMS.get((upper, lower))
    if not canonical_main:
        fail(f"No Yi Jing hexagram for Meihua structure: upper={upper}, lower={lower}")

    yijing = run_json(
        [
            sys.executable,
            str(YIJING_RUNNER),
            "--hexagram",
            canonical_main,
            "--moving",
            str(moving),
        ],
        "Yi Jing evidence lookup",
    )
    if yijing.get("DOMAIN") != "YIJING":
        fail("Unexpected Yi Jing packet contract")
    if yijing.get("NORMALIZED_HEXAGRAM") != canonical_main:
        fail(
            f"Yi Jing canonical bridge drift: expected {canonical_main}, got {yijing.get('NORMALIZED_HEXAGRAM')}"
        )

    selected = yijing.get("SELECTED_YAO") or []
    if len(selected) != 1 or selected[0].get("position") != moving:
        fail(f"Yi Jing selected-line bridge drift for moving line {moving}")
    if not selected[0].get("text") or not selected[0].get("xiaoxiang"):
        fail("Yi Jing selected line is missing Yao or Xiaoxiang evidence")

    packet = {
        "DOMAIN": "MEIHUA_YIJING_EVIDENCE",
        "CAPABILITY": "MEIHUA_NUMBER_CAST_TO_SOURCE_GROUNDED_YIJING_EVIDENCE",
        "INPUT": {"numbers": args.numbers},
        "BRIDGE": {
            "MEIHUA_UPPER_TRIGRAM_RAW": meihua.get("UPPER_TRIGRAM"),
            "MEIHUA_LOWER_TRIGRAM_RAW": meihua.get("LOWER_TRIGRAM"),
            "CANONICAL_UPPER_TRIGRAM": upper,
            "CANONICAL_LOWER_TRIGRAM": lower,
            "MEIHUA_MAIN_HEXAGRAM_REPORTED": meihua.get("MAIN_HEXAGRAM"),
            "YIJING_MAIN_HEXAGRAM_CANONICAL": canonical_main,
            "MOVING_LINE": moving,
            "MEIHUA_CHANGED_HEXAGRAM_REPORTED": meihua.get("CHANGED_HEXAGRAM"),
            "YIJING_CHANGED_HEXAGRAM_STRUCTURAL": yijing.get("CHANGED_HEXAGRAM"),
            "NAME_BRIDGE_POLICY": "TRIGRAM_STRUCTURE_NOT_FULL_TRADITIONAL_SIMPLIFIED_TEXT_CONVERSION",
        },
        "MEIHUA_PACKET": meihua,
        "YIJING_EVIDENCE": yijing,
        "BRIDGE_ASSERTIONS": {
            "MAIN_HEXAGRAM_MAPPED_FROM_TRIGRAM_STRUCTURE": "PASS",
            "MOVING_LINE_MATCHES_SELECTED_YAO": "PASS",
            "SELECTED_YAO_TEXT_PRESENT": "PASS",
            "SELECTED_XIAOXIANG_PRESENT": "PASS",
        },
        "PROVENANCE_POLICY": "MECHANICAL_CROSS_LANE_BRIDGE_KEEP_SOURCE_PACKETS_INDEPENDENT",
        "INTERPRETATION_STATUS": "NOT_PERFORMED",
        "PREDICTIVE_STATUS": "NOT_ESTABLISHED",
        "NONCLAIMS": [
            "NO_CROSS_REPO_DOCTRINE_MERGE",
            "NO_DIVINATION_JUDGMENT",
            "NO_FULL_TRADITIONAL_SIMPLIFIED_NAME_EQUIVALENCE_CLAIM",
            "NO_PREDICTIVE_VALIDITY_CLAIM",
        ],
    }
    print(json.dumps(packet, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
