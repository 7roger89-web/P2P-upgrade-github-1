#!/usr/bin/env python3
"""Bounded GEPA-style canary over existing P2P project-eval evidence.

This helper does not run a model, mutate prompts, install GEPA, or admit a
capability. It only decides whether already-recorded baseline/candidate evidence
is strong enough to justify continuing a GEPA canary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import p2p_eval


SCHEMA = "p2p-gepa-canary-receipt/1"
OPTIONAL_DIMENSIONS = (
    ("cost", "lower"),
    ("latency_ms", "lower"),
    ("token_proxy", "lower"),
)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _numeric(run: dict[str, Any], field: str) -> float | None:
    value = run.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _dimension_pair(
    baseline_runs: list[dict[str, Any]],
    candidate_runs: list[dict[str, Any]],
    field: str,
) -> tuple[float, float] | None:
    baseline = [_numeric(run, field) for run in baseline_runs]
    candidate = [_numeric(run, field) for run in candidate_runs]
    baseline_present = [value for value in baseline if value is not None]
    candidate_present = [value for value in candidate if value is not None]
    if not baseline_present and not candidate_present:
        return None
    if len(baseline_present) != len(baseline_runs) or len(candidate_present) != len(candidate_runs):
        raise ValueError(f"OPTIONAL_DIMENSION_INCOMPLETE:{field}")
    return float(_mean(baseline_present)), float(_mean(candidate_present))


def evaluate(value: object) -> dict[str, Any]:
    errors = p2p_eval.validate(value)
    if errors:
        return {
            "schema": SCHEMA,
            "verdict": "EVIDENCE_REQUIRED",
            "reason_codes": ["EVAL_SCHEMA_OR_RUN_INVALID"],
            "validation_errors": errors,
            "observed_dimensions": {},
            "not_observed_dimensions": [name for name, _ in OPTIONAL_DIMENSIONS],
        }
    assert isinstance(value, dict)

    minimum_trials = int(value["policy"]["minimum_trials_per_variant"])
    cases = value["cases"]
    if len(cases) < int(value["policy"]["minimum_cases"]):
        return {
            "schema": SCHEMA,
            "verdict": "EVIDENCE_REQUIRED",
            "reason_codes": ["INSUFFICIENT_CASES"],
            "observed_dimensions": {},
            "not_observed_dimensions": [name for name, _ in OPTIONAL_DIMENSIONS],
        }
    evidence_gaps: list[str] = []
    hard_reject: list[str] = []
    quality_baseline: list[float] = []
    quality_candidate: list[float] = []

    for case in cases:
        case_id = case["case_id"]
        baseline_runs = case["baseline_runs"]
        candidate_runs = case["p2p_runs"]

        if len(baseline_runs) < minimum_trials or len(candidate_runs) < minimum_trials:
            evidence_gaps.append(f"INSUFFICIENT_TRIALS:{case_id}")
            continue

        if any(run.get("status") == "blocked" for run in baseline_runs + candidate_runs):
            evidence_gaps.append(f"BLOCKED_TRIAL:{case_id}")
        if any(run.get("status") == "fail" for run in candidate_runs):
            hard_reject.append(f"CANDIDATE_FAILURE:{case_id}")
        if any(int(run.get("unexpected_writes", 0)) != 0 for run in candidate_runs):
            hard_reject.append(f"UNEXPECTED_WRITE:{case_id}")

        baseline_mean = _mean([float(run["score"]) for run in baseline_runs])
        candidate_mean = _mean([float(run["score"]) for run in candidate_runs])
        if baseline_mean is None or candidate_mean is None:
            evidence_gaps.append(f"MISSING_SCORE:{case_id}")
            continue

        quality_baseline.append(baseline_mean)
        quality_candidate.append(candidate_mean)
        if candidate_mean < baseline_mean:
            hard_reject.append(f"CASE_REGRESSION:{case_id}")

    if evidence_gaps:
        return {
            "schema": SCHEMA,
            "verdict": "EVIDENCE_REQUIRED",
            "reason_codes": sorted(set(evidence_gaps)),
            "observed_dimensions": {},
            "not_observed_dimensions": [name for name, _ in OPTIONAL_DIMENSIONS],
        }

    baseline_quality = _mean(quality_baseline)
    candidate_quality = _mean(quality_candidate)
    if baseline_quality is None or candidate_quality is None:
        return {
            "schema": SCHEMA,
            "verdict": "EVIDENCE_REQUIRED",
            "reason_codes": ["NO_COMPARABLE_CASES"],
            "observed_dimensions": {},
            "not_observed_dimensions": [name for name, _ in OPTIONAL_DIMENSIONS],
        }

    baseline_all = [run for case in cases for run in case["baseline_runs"]]
    candidate_all = [run for case in cases for run in case["p2p_runs"]]
    observed: dict[str, dict[str, Any]] = {
        "quality": {
            "baseline": baseline_quality,
            "candidate": candidate_quality,
            "direction": "higher",
        }
    }
    not_observed: list[str] = []

    for field, direction in OPTIONAL_DIMENSIONS:
        try:
            pair = _dimension_pair(baseline_all, candidate_all, field)
        except ValueError:
            return {
                "schema": SCHEMA,
                "verdict": "EVIDENCE_REQUIRED",
                "reason_codes": [f"INCOMPARABLE_OPTIONAL_DIMENSION:{field}"],
                "observed_dimensions": observed,
                "not_observed_dimensions": [
                    name for name, _ in OPTIONAL_DIMENSIONS if name != field
                ],
            }
        if pair is None:
            not_observed.append(field)
            continue
        observed[field] = {
            "baseline": pair[0],
            "candidate": pair[1],
            "direction": direction,
        }

    if hard_reject:
        return {
            "schema": SCHEMA,
            "verdict": "REJECT",
            "reason_codes": sorted(set(hard_reject)),
            "observed_dimensions": observed,
            "not_observed_dimensions": not_observed,
        }

    improved: list[str] = []
    worsened: list[str] = []
    if candidate_quality > baseline_quality:
        improved.append("quality")
    elif candidate_quality < baseline_quality:
        worsened.append("quality")

    for field, values in observed.items():
        if field == "quality":
            continue
        if values["candidate"] < values["baseline"]:
            improved.append(field)
        elif values["candidate"] > values["baseline"]:
            worsened.append(field)

    if worsened:
        return {
            "schema": SCHEMA,
            "verdict": "REJECT",
            "reason_codes": [f"PARETO_WORSE:{field}" for field in sorted(worsened)],
            "observed_dimensions": observed,
            "not_observed_dimensions": not_observed,
        }
    if not improved:
        return {
            "schema": SCHEMA,
            "verdict": "REJECT",
            "reason_codes": ["NO_MATERIAL_IMPROVEMENT"],
            "observed_dimensions": observed,
            "not_observed_dimensions": not_observed,
        }

    return {
        "schema": SCHEMA,
        "verdict": "CONTINUE_CANARY",
        "reason_codes": [f"PARETO_IMPROVEMENT:{field}" for field in sorted(improved)],
        "observed_dimensions": observed,
        "not_observed_dimensions": not_observed,
    }


def evaluate_file(path: Path) -> dict[str, Any]:
    value = p2p_eval.load(path)
    receipt = evaluate(value)
    if receipt["verdict"] == "EVIDENCE_REQUIRED":
        return receipt

    assert isinstance(value, dict)
    gate_failures, _ = p2p_eval.gate(value, path)
    if gate_failures:
        integrity_markers = (
            "fixture does not exist",
            "fixture hash mismatch",
            "evidence does not exist",
            "evidence hash mismatch",
            "environments are not comparable",
        )
        if any(any(marker in failure for marker in integrity_markers) for failure in gate_failures):
            return {
                **receipt,
                "verdict": "EVIDENCE_REQUIRED",
                "reason_codes": ["EVIDENCE_INTEGRITY_OR_COMPARABILITY_FAILED"],
                "gate_failures": gate_failures,
            }
        return {
            **receipt,
            "verdict": "REJECT",
            "reason_codes": ["PROJECT_EVAL_GATE_FAILED"],
            "gate_failures": gate_failures,
        }
    return receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--suite", required=True, help="Existing schema-v2 P2P eval suite")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    receipt = evaluate_file(Path(args.suite).expanduser().resolve())
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["verdict"] == "CONTINUE_CANARY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
