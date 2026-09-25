"""Evidence gate for admitting a new native/runtime language on a measured hot path.

This module does not benchmark, execute shell commands, install toolchains, or mutate a
project. It turns task-specific performance evidence into a deterministic technical
verdict under POLYGLOT_BY_EVIDENCE_V1.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "p2p-performance-language-admission/1"

CPU_BOTTLENECK = "CPU_ALGORITHM"
NON_CPU_BOTTLENECKS = {
    "DB",
    "NETWORK",
    "IO",
    "SERIALIZATION",
    "EXTERNAL_SERVICE",
    "MEMORY",
}
VALID_BOTTLENECKS = {CPU_BOTTLENECK, *NON_CPU_BOTTLENECKS, "UNKNOWN"}

VERDICTS = {
    "KEEP_CURRENT_STACK",
    "FIX_NON_CPU_BOTTLENECK",
    "OPTIMIZE_CURRENT_STACK_FIRST",
    "RUN_BOUNDED_NATIVE_SPIKE",
    "ADOPT_BOUNDED_NATIVE_COMPONENT",
    "REJECT_NATIVE_SPIKE",
    "INSUFFICIENT_EVIDENCE",
}

_TRIGGER_TERMS = (
    "slow",
    "chậm",
    "latency",
    "throughput",
    "performance",
    "hiệu năng",
    "batch",
    "scale",
    "cpu",
    "parser",
    "parsing",
    "indexing",
    "benchmark",
    "profiling",
    "hot path",
)


def performance_signal(task_text: str) -> bool:
    """Return a cheap task-text hint only; never treat it as performance proof."""
    lowered = str(task_text or "").lower()
    return any(term in lowered for term in _TRIGGER_TERMS)


def _measurement(value: object) -> tuple[str, float] | None:
    if not isinstance(value, Mapping):
        return None
    metric = str(value.get("metric") or "").strip()
    number = value.get("value")
    if not metric or isinstance(number, bool) or not isinstance(number, (int, float)):
        return None
    return metric, float(number)


def _target(value: object) -> tuple[str, str, float] | None:
    if not isinstance(value, Mapping):
        return None
    metric = str(value.get("metric") or "").strip()
    operator = str(value.get("operator") or "").strip()
    number = value.get("value")
    if operator not in {"<", "<=", ">", ">=", "=="}:
        return None
    if not metric or isinstance(number, bool) or not isinstance(number, (int, float)):
        return None
    return metric, operator, float(number)


def _meets(target: tuple[str, str, float], measurement: object) -> bool | None:
    observed = _measurement(measurement)
    if observed is None or observed[0] != target[0]:
        return None
    _, operator, expected = target
    actual = observed[1]
    return {
        "<": actual < expected,
        "<=": actual <= expected,
        ">": actual > expected,
        ">=": actual >= expected,
        "==": actual == expected,
    }[operator]


def _nonempty(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return bool(value)
    return True


def evaluate_performance_language_admission(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Classify whether a bounded native/Rust spike is technically justified.

    Expected packet fields use the durable P2P uppercase convention. The function
    deliberately returns INSUFFICIENT_EVIDENCE instead of inventing thresholds.
    """

    scenario = str(packet.get("SCENARIO") or "").strip()
    current_stack = str(packet.get("CURRENT_STACK") or "").strip()
    target = _target(packet.get("ACCEPTANCE_TARGET"))
    baseline = packet.get("BASELINE")
    bottleneck = str(packet.get("BOTTLENECK") or "UNKNOWN").strip().upper()
    hot_path = str(packet.get("HOT_PATH") or "").strip()
    hot_path_share = packet.get("HOT_PATH_SHARE")
    optimized = packet.get("CURRENT_STACK_OPTIMIZED")
    current_result = packet.get("CURRENT_STACK_RESULT")
    spike = packet.get("NATIVE_SPIKE")

    reasons: list[str] = []

    def receipt(verdict: str, *codes: str, native_candidate: bool = False) -> dict[str, Any]:
        reasons.extend(codes)
        return {
            "schema": SCHEMA,
            "SCENARIO": scenario,
            "CURRENT_STACK": current_stack,
            "BOTTLENECK": bottleneck,
            "VERDICT": verdict,
            "NATIVE_CANDIDATE": native_candidate,
            "REASON_CODES": reasons,
            "PERMISSION_EFFECT": "NONE",
        }

    if not scenario or not current_stack:
        return receipt("INSUFFICIENT_EVIDENCE", "MISSING_SCENARIO_OR_CURRENT_STACK")
    if target is None:
        return receipt("INSUFFICIENT_EVIDENCE", "MISSING_OR_INVALID_ACCEPTANCE_TARGET")
    if _measurement(baseline) is None:
        return receipt("INSUFFICIENT_EVIDENCE", "MISSING_OR_INVALID_BASELINE")

    baseline_meets = _meets(target, baseline)
    if baseline_meets is None:
        return receipt("INSUFFICIENT_EVIDENCE", "BASELINE_METRIC_DOES_NOT_MATCH_TARGET")
    if baseline_meets:
        return receipt("KEEP_CURRENT_STACK", "BASELINE_ALREADY_MEETS_ACCEPTANCE")

    if bottleneck not in VALID_BOTTLENECKS or bottleneck == "UNKNOWN":
        return receipt("INSUFFICIENT_EVIDENCE", "BOTTLENECK_NOT_ESTABLISHED")
    if bottleneck in NON_CPU_BOTTLENECKS:
        return receipt("FIX_NON_CPU_BOTTLENECK", f"BOTTLENECK_{bottleneck}")

    if not hot_path:
        return receipt("INSUFFICIENT_EVIDENCE", "CPU_BOTTLENECK_WITHOUT_HOT_PATH")
    if isinstance(hot_path_share, bool) or not isinstance(hot_path_share, (int, float)):
        return receipt("INSUFFICIENT_EVIDENCE", "HOT_PATH_SHARE_NOT_MEASURED")
    share = float(hot_path_share)
    if not (0.0 < share <= 1.0):
        return receipt("INSUFFICIENT_EVIDENCE", "HOT_PATH_SHARE_OUT_OF_RANGE")

    if optimized is not True:
        return receipt("OPTIMIZE_CURRENT_STACK_FIRST", "CURRENT_STACK_NOT_CREDIBLY_OPTIMIZED")

    current_meets = _meets(target, current_result)
    if current_meets is None:
        return receipt("INSUFFICIENT_EVIDENCE", "MISSING_OPTIMIZED_CURRENT_STACK_MEASUREMENT")
    if current_meets:
        return receipt("KEEP_CURRENT_STACK", "OPTIMIZED_CURRENT_STACK_MEETS_ACCEPTANCE")

    if not isinstance(spike, Mapping) or spike.get("performed") is not True:
        return receipt(
            "RUN_BOUNDED_NATIVE_SPIKE",
            "MEASURED_CPU_HOT_PATH_STILL_MISSES_ACCEPTANCE",
            native_candidate=True,
        )
    if spike.get("same_workload") is not True:
        return receipt("INSUFFICIENT_EVIDENCE", "NATIVE_SPIKE_NOT_SAME_WORKLOAD")

    spike_meets = _meets(target, spike.get("result"))
    if spike_meets is None:
        return receipt("INSUFFICIENT_EVIDENCE", "MISSING_OR_INCOMPARABLE_NATIVE_SPIKE_RESULT")
    if not spike_meets:
        return receipt("REJECT_NATIVE_SPIKE", "NATIVE_SPIKE_MISSES_ACCEPTANCE")

    if not _nonempty(packet.get("SMALLEST_BOUNDARY")):
        return receipt("INSUFFICIENT_EVIDENCE", "MISSING_SMALLEST_BOUNDARY", native_candidate=True)
    if not _nonempty(packet.get("OPERATIONS_COST")):
        return receipt("INSUFFICIENT_EVIDENCE", "MISSING_OPERATIONS_COST", native_candidate=True)
    if not _nonempty(packet.get("ROLLBACK_PATH")):
        return receipt("INSUFFICIENT_EVIDENCE", "MISSING_ROLLBACK_PATH", native_candidate=True)

    return receipt(
        "ADOPT_BOUNDED_NATIVE_COMPONENT",
        "NATIVE_SPIKE_MEETS_ACCEPTANCE_WITH_BOUNDED_REVERSIBLE_INTEGRATION",
        native_candidate=True,
    )


def _load_packet(args: argparse.Namespace) -> Mapping[str, Any]:
    if args.json:
        value = json.loads(args.json)
    else:
        value = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("input packet must be a JSON object")
    return value


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P2P performance/language evidence gate")
    sub = parser.add_subparsers(dest="command", required=True)

    detect = sub.add_parser("detect", help="cheap task-text hint; not evidence")
    detect.add_argument("--task-text", required=True)

    evaluate = sub.add_parser("evaluate", help="evaluate a structured evidence packet")
    source = evaluate.add_mutually_exclusive_group(required=True)
    source.add_argument("--json")
    source.add_argument("--file")

    args = parser.parse_args(argv)
    if args.command == "detect":
        print(json.dumps({"PERFORMANCE_SIGNAL": performance_signal(args.task_text), "PROOF": False}))
        return 0
    try:
        receipt = evaluate_performance_language_admission(_load_packet(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema": SCHEMA, "VERDICT": "INSUFFICIENT_EVIDENCE", "ERROR": str(exc), "PERMISSION_EFFECT": "NONE"}))
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
