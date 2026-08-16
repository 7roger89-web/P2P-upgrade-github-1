#!/usr/bin/env python3
"""Initialize, validate, gate, migrate, and summarize project P2P evals."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "p2p-codex-project-eval/2"
LEGACY_SCHEMA = "p2p-codex-project-eval/1"
RAG_SCHEMA = "p2p-codex-rag-retrieval-check/2"
RUN_STATUSES = {"pass", "fail", "blocked"}
CASE_CLASSES = {
    "frequent", "consequential", "failure_prone", "security_boundary",
    "regression", "retrieval", "other",
}
RAG_CLASSES = {
    "exact_lookup", "paraphrase", "cross_reference",
    "unknown", "injection", "cross_boundary",
}
PLACEHOLDERS = ("REPLACE", "TODO", "TBD")
TRIAL_SCHEMA = "p2p-codex-project-eval-run/1"
TRIAL_VARIANTS = {"baseline": "baseline_runs", "p2p": "p2p_runs"}


def load(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc


def write_json_new(path: Path, value: object) -> None:
    if path.exists():
        raise ValueError(f"Refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def suite_path(project: Path) -> Path:
    return project / ".p2p" / "evals" / "suite.json"


def default_template() -> Path:
    package = Path(__file__).resolve().parents[1]
    direct = package / "governance" / "project-eval.template.json"
    installed = package / ".p2p" / "system" / "governance" / "project-eval.template.json"
    return direct if direct.is_file() else installed


def _project_type(project: Path, goal: str, profile: object | None) -> str:
    if isinstance(profile, dict) and isinstance(profile.get("project_type"), str):
        return profile["project_type"]
    text = f"{goal} {project.name}".lower()
    markers = " ".join(path.name.lower() for path in project.iterdir()) if project.is_dir() else ""
    if any(word in text for word in ("logistics", "warehouse", "inventory", "delivery", "kho", "vận tải")):
        return "logistics_software"
    if any(word in text for word in ("story", "game", "truyện", "visual novel")):
        return "story_game"
    if any(word in text for word in ("data", "analysis", "dataset", "csv", "phân tích", "dữ liệu")):
        return "data_analysis"
    if any(word in text for word in ("automation", "automate", "workflow", "tự động")):
        return "automation"
    if any(word in text for word in ("research", "paper", "study", "nghiên cứu")):
        return "research"
    if "package.json" in markers or "index.html" in markers or (project / "src").is_dir():
        return "web_application"
    if (project / "pyproject.toml").is_file() or list(project.glob("*.py")):
        return "automation"
    return "generic_project"


def _project_markers(project: Path) -> list[str]:
    markers: list[str] = []
    for name in (
        "package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod",
        "index.html", "README.md", "src", "app", "backend", "frontend", "tests", "docs",
    ):
        if (project / name).exists():
            markers.append(name)
    return markers


def design_project_suite(
    project: Path,
    *,
    name: str | None = None,
    goal: str = "",
    profile: object | None = None,
    destination: Path | None = None,
) -> dict:
    """Create the smallest useful project-specific v2 suite, or reuse a valid one."""
    project = project.expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    destination = destination or suite_path(project)
    if destination.exists():
        existing = load(destination)
        errors = validate(existing)
        if errors:
            return {
                "status": "BLOCKED_EXISTING_INVALID",
                "suite": str(destination),
                "errors": errors,
            }
        return {
            "status": "REUSED",
            "suite": str(destination),
            "case_count": len(existing.get("cases", [])) if isinstance(existing, dict) else 0,
            "validation": "PASS",
        }

    project_name = name or project.name
    project_type = _project_type(project, goal, profile)
    markers = _project_markers(project)
    fixture_root = destination.parent / "fixtures"
    case_specs = [
        (
            "positive-behavior",
            "frequent",
            "positive",
            "Valid project behavior remains usable",
            "A valid request produces the expected project behavior for the detected project type.",
            "The valid behavior is observable and passes the project-specific acceptance check.",
        ),
        (
            "negative-boundary",
            "security_boundary",
            "negative",
            "Invalid or unsafe behavior is blocked",
            "An invalid, unsafe, or out-of-scope request is rejected or contained.",
            "The boundary case is blocked without an unexpected write or permission widening.",
        ),
        (
            "regression-baseline",
            "regression",
            "regression",
            "Existing important behavior remains working",
            "The important behavior already present in the project remains available after the scoped change.",
            "The frozen regression fixture still passes its observable check.",
        ),
        (
            "completion-contract",
            "consequential",
            "completion",
            "The current Goal Contract can be verified",
            "Every mandatory completion criterion in the current Goal Contract has an observable evidence path.",
            "The completion checks return PASS or identify one concrete blocker.",
        ),
        (
            "scope-and-evidence-reuse",
            "other",
            "reuse",
            "Unchanged controls are reused and scope stays bounded",
            "A small scoped change reuses valid evidence for unrelated controls and records unrelated discoveries as backlog.",
            "Only affected checks are selected for rerun; unchanged PASS evidence remains reusable.",
        ),
    ]
    cases: list[dict] = []
    for case_id, case_class, test_type, title, task, criterion in case_specs:
        fixture = fixture_root / f"{case_id}.json"
        if not fixture.exists():
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(
                json.dumps(
                    {
                        "schema_version": "p2p-workflow-fixture/1",
                        "project": project_name,
                        "project_type": project_type,
                        "goal": goal.strip(),
                        "test_type": test_type,
                        "markers": markers,
                        "expected_observation": criterion,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        relative_fixture = fixture.relative_to(project).as_posix()
        cases.append(
            {
                "case_id": case_id,
                "class": case_class,
                "test_type": test_type,
                "title": title,
                "task": f"{task} Project type: {project_type}. Goal context: {goal.strip() or 'inspect the current project'}",
                "fixture": relative_fixture,
                "fixture_sha256": sha256(fixture),
                "tags": [test_type, project_type, "project-specific"],
                "checks": [
                    {
                        "check_id": f"{test_type}-observable",
                        "grader": "deterministic_or_project_grader",
                        "weight": 1,
                        "criterion": criterion,
                    }
                ],
                "baseline_runs": [],
                "p2p_runs": [],
            }
        )
    value = {
        "schema_version": SCHEMA,
        "project": project_name,
        "policy": {
            "minimum_cases": 5,
            "minimum_trials_per_variant": 2,
            "minimum_p2p_pass_rate": 0.8,
            "maximum_mean_regression": 0.0,
            "maximum_case_regressions": 0,
            "maximum_score_spread": 0.25,
            "blocked_cases_allowed": False,
        },
        "comparison_contract": {
            "same_input": True,
            "same_environment": True,
            "isolate_runs": True,
            "record_model_and_surface": True,
            "leakage_check": True,
            "criteria_defined_before_runs": True,
            "frozen_fixtures": True,
            "no_cross_run_memory": True,
        },
        "design_metadata": {
            "method": "goal_and_project_evidence",
            "project_type": project_type,
            "project_markers": markers,
            "goal": goal.strip(),
        },
        "cases": cases,
    }
    write_json_new(destination, value)
    return {
        "status": "CREATED",
        "suite": str(destination),
        "case_count": len(cases),
        "case_types": [case["test_type"] for case in cases],
        "validation": "PASS" if not validate(value) else "FAIL",
    }


def contains_placeholder(value: object) -> bool:
    text = str(value or "").upper()
    return not text.strip() or any(marker in text for marker in PLACEHOLDERS)


def validate_policy(policy: object, errors: list[str]) -> None:
    required = {
        "minimum_cases": int,
        "minimum_trials_per_variant": int,
        "minimum_p2p_pass_rate": (int, float),
        "maximum_mean_regression": (int, float),
        "maximum_case_regressions": int,
        "maximum_score_spread": (int, float),
        "blocked_cases_allowed": bool,
    }
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
        return
    for key, expected_type in required.items():
        if not isinstance(policy.get(key), expected_type):
            errors.append(f"policy.{key} has an invalid type")
    for key in ("minimum_cases", "minimum_trials_per_variant"):
        if isinstance(policy.get(key), int) and policy[key] < 1:
            errors.append(f"policy.{key} must be at least 1")
    for key in ("minimum_p2p_pass_rate", "maximum_mean_regression", "maximum_score_spread"):
        value = policy.get(key)
        if isinstance(value, (int, float)) and not 0 <= value <= 1:
            errors.append(f"policy.{key} must be between 0 and 1")
    if isinstance(policy.get("maximum_case_regressions"), int) and policy["maximum_case_regressions"] < 0:
        errors.append("policy.maximum_case_regressions cannot be negative")


def validate_run(run: object, prefix: str, errors: list[str]) -> None:
    if not isinstance(run, dict):
        errors.append(f"{prefix} must be an object")
        return
    required = {
        "run_id", "status", "model", "surface", "environment_id", "run_at",
        "score", "evidence", "evidence_sha256", "unexpected_writes", "notes",
    }
    missing = sorted(required - run.keys())
    if missing:
        errors.append(f"{prefix} is missing: {', '.join(missing)}")
        return
    if run.get("status") not in RUN_STATUSES:
        errors.append(f"{prefix}.status is invalid")
    score = run.get("score")
    if not isinstance(score, (int, float)) or not 0 <= score <= 1:
        errors.append(f"{prefix}.score must be 0..1")
    if not isinstance(run.get("unexpected_writes"), int) or run["unexpected_writes"] < 0:
        errors.append(f"{prefix}.unexpected_writes must be a non-negative integer")
    for field in ("run_id", "model", "surface", "environment_id", "run_at", "evidence"):
        if not isinstance(run.get(field), str) or not run[field].strip():
            errors.append(f"{prefix}.{field} must be non-empty")
    evidence_hash = run.get("evidence_sha256")
    if not isinstance(evidence_hash, str) or len(evidence_hash) != 64 or any(ch not in "0123456789abcdef" for ch in evidence_hash):
        errors.append(f"{prefix}.evidence_sha256 must be lowercase SHA-256")


def validate(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
        return [f"schema_version must be {SCHEMA}"]
    if not isinstance(value.get("project"), str) or not value["project"].strip():
        errors.append("project must be a non-empty name")
    validate_policy(value.get("policy"), errors)
    contract = value.get("comparison_contract")
    contract_keys = (
        "same_input", "same_environment", "isolate_runs", "record_model_and_surface",
        "leakage_check", "criteria_defined_before_runs", "frozen_fixtures", "no_cross_run_memory",
    )
    for key in contract_keys:
        if not isinstance(contract, dict) or contract.get(key) is not True:
            errors.append(f"comparison_contract.{key} must be true")
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must contain at least one project task")
        return errors
    seen_cases: set[str] = set()
    seen_runs: set[str] = set()
    for index, case in enumerate(cases, start=1):
        prefix = f"case {index}"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        required = {
            "case_id", "class", "title", "task", "fixture", "fixture_sha256",
            "tags", "checks", "baseline_runs", "p2p_runs",
        }
        missing = sorted(required - case.keys())
        if missing:
            errors.append(f"{prefix} is missing: {', '.join(missing)}")
            continue
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{prefix} has no case_id")
        elif case_id in seen_cases:
            errors.append(f"duplicate case_id: {case_id}")
        else:
            seen_cases.add(case_id)
        if case.get("class") not in CASE_CLASSES:
            errors.append(f"{case_id or prefix}.class is invalid")
        fixture_hash = case.get("fixture_sha256")
        if not isinstance(fixture_hash, str) or (fixture_hash and (len(fixture_hash) != 64 or any(ch not in "0123456789abcdef" for ch in fixture_hash))):
            errors.append(f"{case_id or prefix}.fixture_sha256 is invalid")
        checks = case.get("checks")
        if not isinstance(checks, list) or not checks:
            errors.append(f"{case_id or prefix} needs checks")
        else:
            for check_index, check in enumerate(checks, start=1):
                if not isinstance(check, dict) or not all(check.get(key) for key in ("check_id", "grader", "criterion")):
                    errors.append(f"{case_id or prefix}.check {check_index} is incomplete")
                elif not isinstance(check.get("weight"), (int, float)) or check["weight"] <= 0:
                    errors.append(f"{case_id or prefix}.check {check_index} has invalid weight")
        for variant in ("baseline_runs", "p2p_runs"):
            runs = case.get(variant)
            if not isinstance(runs, list):
                errors.append(f"{case_id or prefix}.{variant} must be an array")
                continue
            for run_index, run in enumerate(runs, start=1):
                validate_run(run, f"{case_id or prefix}.{variant}[{run_index}]", errors)
                if isinstance(run, dict) and isinstance(run.get("run_id"), str):
                    if run["run_id"] in seen_runs:
                        errors.append(f"duplicate run_id: {run['run_id']}")
                    seen_runs.add(run["run_id"])
    return errors


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize(value: dict) -> dict:
    cases = []
    baseline_values: list[float] = []
    p2p_values: list[float] = []
    p2p_passes = 0
    p2p_runs_total = 0
    regressions = 0
    for case in value.get("cases", []):
        baseline_runs = case.get("baseline_runs", [])
        p2p_runs = case.get("p2p_runs", [])
        baseline_scores = [float(run["score"]) for run in baseline_runs if isinstance(run.get("score"), (int, float))]
        p2p_scores = [float(run["score"]) for run in p2p_runs if isinstance(run.get("score"), (int, float))]
        baseline_mean = mean(baseline_scores)
        p2p_mean = mean(p2p_scores)
        if baseline_mean is not None:
            baseline_values.append(baseline_mean)
        if p2p_mean is not None:
            p2p_values.append(p2p_mean)
        p2p_passes += sum(run.get("status") == "pass" for run in p2p_runs)
        p2p_runs_total += len(p2p_runs)
        delta = p2p_mean - baseline_mean if baseline_mean is not None and p2p_mean is not None else None
        if delta is not None and delta < 0:
            regressions += 1
        cases.append(
            {
                "case_id": case.get("case_id"),
                "baseline_trials": len(baseline_runs),
                "p2p_trials": len(p2p_runs),
                "baseline_mean": baseline_mean,
                "p2p_mean": p2p_mean,
                "delta": delta,
                "baseline_spread": max(baseline_scores) - min(baseline_scores) if baseline_scores else None,
                "p2p_spread": max(p2p_scores) - min(p2p_scores) if p2p_scores else None,
            }
        )
    baseline_mean = mean(baseline_values)
    p2p_mean = mean(p2p_values)
    return {
        "schema_version": "p2p-codex-project-eval-summary/2",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "project": value.get("project"),
        "case_count": len(value.get("cases", [])),
        "completed_case_pairs": sum(item["baseline_trials"] > 0 and item["p2p_trials"] > 0 for item in cases),
        "baseline_mean": baseline_mean,
        "p2p_mean": p2p_mean,
        "delta": p2p_mean - baseline_mean if baseline_mean is not None and p2p_mean is not None else None,
        "p2p_pass_rate": p2p_passes / p2p_runs_total if p2p_runs_total else None,
        "case_regressions": regressions,
        "cases": cases,
    }


def resolve_evidence(project: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return path.resolve() if path.is_absolute() else (project / path).resolve()


def gate(value: dict, suite: Path) -> tuple[list[str], dict]:
    failures = validate(value)
    summary = summarize(value)
    if failures:
        return failures, summary
    project_root = suite.parent.parent.parent if suite.parent.name == "evals" else suite.parent
    policy = value["policy"]
    cases = value["cases"]
    if len(cases) < policy["minimum_cases"]:
        failures.append(f"only {len(cases)} cases; policy requires {policy['minimum_cases']}")
    for case in cases:
        case_id = case["case_id"]
        for field in ("title", "task", "fixture"):
            if contains_placeholder(case[field]):
                failures.append(f"{case_id}.{field} still contains a placeholder")
        for check in case["checks"]:
            if contains_placeholder(check["criterion"]):
                failures.append(f"{case_id}.{check['check_id']} criterion still contains a placeholder")
        fixture = resolve_evidence(project_root, case["fixture"])
        if not fixture.is_file():
            failures.append(f"{case_id} fixture does not exist: {fixture}")
        elif sha256(fixture) != case["fixture_sha256"]:
            failures.append(f"{case_id} fixture hash mismatch")
        for variant in ("baseline_runs", "p2p_runs"):
            runs = case[variant]
            if len(runs) < policy["minimum_trials_per_variant"]:
                failures.append(f"{case_id}.{variant} has {len(runs)} trials; requires {policy['minimum_trials_per_variant']}")
            if not policy["blocked_cases_allowed"] and any(run["status"] == "blocked" for run in runs):
                failures.append(f"{case_id}.{variant} contains a blocked trial")
            for run in runs:
                evidence = resolve_evidence(project_root, run["evidence"])
                if not evidence.is_file():
                    failures.append(f"{run['run_id']} evidence does not exist: {evidence}")
                elif sha256(evidence) != run["evidence_sha256"]:
                    failures.append(f"{run['run_id']} evidence hash mismatch")
                if run["unexpected_writes"] != 0:
                    failures.append(f"{run['run_id']} recorded unexpected writes")
        baseline_signature = {(run["model"], run["surface"], run["environment_id"]) for run in case["baseline_runs"]}
        p2p_signature = {(run["model"], run["surface"], run["environment_id"]) for run in case["p2p_runs"]}
        if baseline_signature and p2p_signature and baseline_signature != p2p_signature:
            failures.append(f"{case_id} baseline/P2P environments are not comparable")
    pass_rate = summary["p2p_pass_rate"]
    if pass_rate is None or pass_rate < policy["minimum_p2p_pass_rate"]:
        failures.append(f"P2P pass rate {pass_rate!r} is below {policy['minimum_p2p_pass_rate']}")
    delta = summary["delta"]
    if delta is None or delta < -policy["maximum_mean_regression"]:
        failures.append(f"mean score delta {delta!r} exceeds allowed regression {policy['maximum_mean_regression']}")
    if summary["case_regressions"] > policy["maximum_case_regressions"]:
        failures.append(f"case regressions {summary['case_regressions']} exceed {policy['maximum_case_regressions']}")
    for case_result in summary["cases"]:
        for variant in ("baseline_spread", "p2p_spread"):
            spread = case_result[variant]
            if spread is not None and spread > policy["maximum_score_spread"]:
                failures.append(f"{case_result['case_id']}.{variant} {spread:.3f} exceeds {policy['maximum_score_spread']}")
    return failures, summary


def _runtime_root(target_root: Path) -> Path:
    """Resolve an isolated package/source target to its installed runtime root."""
    packaged = target_root / "runtime"
    if packaged.is_dir():
        return packaged
    installed = target_root / ".p2p" / "system"
    if installed.is_dir():
        return installed
    return target_root


def _snapshot_tree(root: Path) -> dict[str, tuple[int, int]]:
    """Hash the isolated target while ignoring explicitly disposable run data."""
    snapshot: dict[str, tuple[int, int]] = {}
    if not root.is_dir():
        return snapshot
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in {".tmp", ".anvien", "__pycache__"} for part in relative.parts):
            continue
        stat = path.stat()
        snapshot[relative.as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return snapshot


def _parse_command_json(stdout: str) -> object:
    """Parse a JSON command result without accepting an invented fallback."""
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, character in enumerate(stdout):
            if character not in "[{":
                continue
            try:
                value, _ = decoder.raw_decode(stdout[index:])
                return value
            except json.JSONDecodeError:
                continue
    return {"unparsed_stdout": stdout[-4000:]}


def _case_command(case_id: str, target_root: Path, runtime_root: Path, suite: Path) -> tuple[list[str], str]:
    """Return one real executable oracle for a frozen project-eval case."""
    runtime_scripts = runtime_root / "scripts"
    root_scripts = target_root / "scripts"
    router = runtime_scripts / "p2p_router.py"
    uiux_eval = runtime_scripts / "p2p_uiux_eval.py"
    project_eval = root_scripts / "p2p_eval.py"
    if case_id in {"positive-behavior", "regression-baseline"}:
        if not uiux_eval.is_file():
            raise ValueError(f"missing UI/UX evaluator in target: {uiux_eval}")
        return [sys.executable, str(uiux_eval), "--source", str(runtime_root)], "uiux_dw1_dw18"
    if case_id == "negative-boundary":
        if not router.is_file():
            raise ValueError(f"missing router in target: {router}")
        return [
            sys.executable,
            str(router),
            "route",
            "--request",
            "Optimize API caching and database indexes; no interface changes.",
            "--profile-available",
            "true",
        ], "backend_boundary"
    if case_id == "completion-contract":
        if not project_eval.is_file():
            raise ValueError(f"missing project evaluator in target: {project_eval}")
        target_suite = target_root / ".p2p" / "evals" / "suite.json"
        if not target_suite.is_file():
            raise ValueError(f"missing frozen target suite: {target_suite}")
        return [sys.executable, str(project_eval), "validate", "--suite", str(target_suite)], "project_eval_schema"
    if case_id == "scope-and-evidence-reuse":
        if not router.is_file():
            raise ValueError(f"missing router in target: {router}")
        return [
            sys.executable,
            str(router),
            "route",
            "--request",
            "Increase the primary button padding by two pixels.",
            "--profile-available",
            "true",
        ], "cosmetic_restraint"
    raise ValueError(f"No executable oracle is defined for suite case: {case_id}")


def _assert_case(case_id: str, parsed: object) -> tuple[bool, dict[str, object]]:
    """Grade only observable command output for one case; no narrative scores."""
    if not isinstance(parsed, dict):
        return False, {"reason": "command result was not a JSON object"}
    if case_id == "positive-behavior":
        gates = parsed.get("gates")
        excluded = {"DW12", "DW13", "DW14"}
        required = {key: value for key, value in gates.items() if key not in excluded} if isinstance(gates, dict) else {}
        passed = bool(required) and all(value == "PASS" for value in required.values())
        return passed, {
            "status": parsed.get("status"),
            "required_gates": required,
            "excluded_gates": sorted(excluded),
            "allow_nonzero_returncode": passed and parsed.get("status") == "FAIL",
            "rule": "core UIUX behavior gates PASS; installed lifecycle gates are separate",
        }
    if case_id == "regression-baseline":
        gates = parsed.get("gates")
        excluded = {"DW12", "DW13", "DW14"}
        required = {key: value for key, value in gates.items() if key not in excluded} if isinstance(gates, dict) else {}
        passed = bool(required) and all(value == "PASS" for value in required.values())
        return passed, {
            "required_gates": required,
            "excluded_gates": sorted(excluded),
            "allow_nonzero_returncode": passed and parsed.get("status") == "FAIL",
            "rule": "core UIUX regression gates PASS; installed lifecycle gates are separate",
        }
    if case_id == "negative-boundary":
        passed = parsed.get("scope") == "NON_UI" and parsed.get("use_skill") is False and parsed.get("call_aesthetica") is False
        return passed, {"scope": parsed.get("scope"), "use_skill": parsed.get("use_skill"), "call_aesthetica": parsed.get("call_aesthetica"), "rule": "backend request stays outside UIUX"}
    if case_id == "completion-contract":
        passed = parsed.get("status") == "PASS"
        return passed, {"status": parsed.get("status"), "errors": parsed.get("errors"), "rule": "frozen suite schema validates"}
    if case_id == "scope-and-evidence-reuse":
        passed = parsed.get("scope") == "UI_UX" and parsed.get("call_aesthetica") is False and parsed.get("trivial_cosmetic") is True
        return passed, {"scope": parsed.get("scope"), "call_aesthetica": parsed.get("call_aesthetica"), "trivial_cosmetic": parsed.get("trivial_cosmetic"), "rule": "cosmetic change remains bounded"}
    return False, {"reason": f"no grader is defined for suite case: {case_id}"}


def _execute_case(case: dict, *, target_root: Path, suite: Path, variant: str, trial: int, evidence_dir: Path, model: str, surface: str, environment_id: str) -> dict:
    project_root = suite.parent.parent.parent
    runtime_root = _runtime_root(target_root)
    target_fixture = target_root / case["fixture"]
    if not target_fixture.is_file():
        raise ValueError(f"missing frozen fixture in target: {target_fixture}")
    target_fixture_sha256 = sha256(target_fixture)
    if target_fixture_sha256 != case["fixture_sha256"]:
        raise ValueError(f"target fixture hash mismatch for {case['case_id']}: {target_fixture}")
    command, oracle = _case_command(case["case_id"], target_root, runtime_root, suite)
    disposable = target_root / ".tmp" / f"{variant}-{trial}-{case['case_id']}"
    disposable.mkdir(parents=True, exist_ok=True)
    before = _snapshot_tree(target_root)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TMPDIR"] = str(disposable)
    env["TEMP"] = str(disposable)
    env["TMP"] = str(disposable)
    started = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    completed = subprocess.run(
        command,
        cwd=str(target_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    after = _snapshot_tree(target_root)
    changed = sorted(set(before) ^ set(after) | {path for path in set(before) & set(after) if before[path] != after[path]})
    parsed = _parse_command_json(completed.stdout)
    passed, assertion = _assert_case(case["case_id"], parsed)
    unexpected_writes = len(changed)
    allow_nonzero_returncode = bool(assertion.get("allow_nonzero_returncode"))
    status = "pass" if passed and unexpected_writes == 0 and (completed.returncode == 0 or allow_nonzero_returncode) else "fail"
    score = 1.0 if status == "pass" else 0.0
    run_id = f"{variant}-trial-{trial}-{case['case_id']}"
    evidence = {
        "schema": "p2p-codex-project-eval-evidence/1",
        "run_id": run_id,
        "variant": variant,
        "trial": trial,
        "case_id": case["case_id"],
        "task": case["task"],
        "fixture": case["fixture"],
        "fixture_sha256": case["fixture_sha256"],
        "target_fixture_sha256": target_fixture_sha256,
        "target_root": str(target_root),
        "runtime_root": str(runtime_root),
        "model": model,
        "surface": surface,
        "environment_id": environment_id,
        "run_at": started,
        "completed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "command": command,
        "oracle": oracle,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-20000:],
        "stderr": completed.stderr[-8000:],
        "parsed": parsed,
        "assertion": assertion,
        "unexpected_writes": unexpected_writes,
        "changed_paths": changed,
        "status": status,
        "score": score,
    }
    evidence_path = evidence_dir / f"{case['case_id']}.json"
    write_json_new(evidence_path, evidence)
    evidence_ref = evidence_path.relative_to(project_root).as_posix()
    return {
        "run_id": run_id,
        "status": status,
        "model": model,
        "surface": surface,
        "environment_id": environment_id,
        "run_at": started,
        "score": score,
        "evidence": evidence_ref,
        "evidence_sha256": sha256(evidence_path),
        "unexpected_writes": unexpected_writes,
        "notes": f"attempted=1; passed={1 if status == 'pass' else 0}; partial=0; failed={1 if status == 'fail' else 0}; oracle={oracle}; returncode={completed.returncode}",
    }


def command_run_trial(args: argparse.Namespace) -> int:
    suite = Path(args.suite).expanduser().resolve()
    value = load(suite)
    errors = validate(value)
    if errors:
        raise ValueError("Cannot run invalid suite: " + "; ".join(errors))
    if args.variant not in TRIAL_VARIANTS:
        raise ValueError(f"variant must be one of: {', '.join(sorted(TRIAL_VARIANTS))}")
    if args.trial < 1:
        raise ValueError("trial must be a positive integer")
    target_root = Path(args.target_root).expanduser().resolve()
    if not target_root.is_dir():
        raise ValueError(f"Target root does not exist: {target_root}")
    project_root = suite.parent.parent.parent
    evidence_dir = Path(args.evidence_dir).expanduser().resolve() if args.evidence_dir else project_root / ".p2p" / "evals" / "runs" / f"{args.variant}-trial-{args.trial}"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    runs = [
        _execute_case(
            case,
            target_root=target_root,
            suite=suite,
            variant=args.variant,
            trial=args.trial,
            evidence_dir=evidence_dir,
            model=args.model,
            surface=args.surface,
            environment_id=args.environment_id,
        )
        for case in value["cases"]
    ]
    summary = {
        "attempted": len(runs),
        "passed": sum(run["status"] == "pass" for run in runs),
        "partial": sum(run["status"] == "blocked" for run in runs),
        "failed": sum(run["status"] == "fail" for run in runs),
    }
    trial_record = {
        "schema": TRIAL_SCHEMA,
        "variant": args.variant,
        "trial": args.trial,
        "suite": str(suite),
        "target_root": str(target_root),
        "model": args.model,
        "surface": args.surface,
        "environment_id": args.environment_id,
        "run_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "summary": summary,
        "runs": runs,
    }
    record_path = evidence_dir / "trial-record.json"
    write_json_new(record_path, trial_record)
    result = {"status": "PASS" if summary["failed"] == 0 and summary["attempted"] == summary["passed"] else "FAIL", "trial_record": str(record_path), "summary": summary, "runs": runs}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


def command_record_trial(args: argparse.Namespace) -> int:
    suite_path_value = Path(args.suite).expanduser().resolve()
    suite_value = load(suite_path_value)
    trial_record_path = Path(args.trial_record).expanduser().resolve()
    trial_record = load(trial_record_path)
    if not isinstance(trial_record, dict) or trial_record.get("schema") != TRIAL_SCHEMA:
        raise ValueError(f"trial record schema must be {TRIAL_SCHEMA}")
    variant = trial_record.get("variant")
    if variant not in TRIAL_VARIANTS:
        raise ValueError("trial record variant is invalid")
    runs = trial_record.get("runs")
    if not isinstance(runs, list) or len(runs) != len(suite_value.get("cases", [])):
        raise ValueError("trial record must contain exactly one run for every suite case")
    errors = validate(suite_value)
    if errors:
        raise ValueError("Cannot record into invalid suite: " + "; ".join(errors))
    by_case = {case["case_id"]: case for case in suite_value["cases"]}
    target_field = TRIAL_VARIANTS[variant]
    existing_ids = {run["run_id"] for case in suite_value["cases"] for field in TRIAL_VARIANTS.values() for run in case[field]}
    recorded: list[str] = []
    for run in runs:
        if not isinstance(run, dict) or not isinstance(run.get("run_id"), str):
            raise ValueError("trial record contains an invalid run")
        case_id = run["run_id"].rsplit("-", 1)[-1]
        if case_id not in by_case:
            matched = [case["case_id"] for case in suite_value["cases"] if run["run_id"].startswith(f"{variant}-trial-") and run["run_id"].endswith(f"-{case['case_id']}")]
            case_id = matched[0] if len(matched) == 1 else ""
        if case_id not in by_case:
            raise ValueError(f"cannot map run to suite case: {run.get('run_id')}")
        if run["run_id"] in existing_ids:
            raise ValueError(f"refusing duplicate run: {run['run_id']}")
        run_errors: list[str] = []
        validate_run(run, run["run_id"], run_errors)
        evidence_path = resolve_evidence(suite_path_value.parent.parent.parent, run.get("evidence", ""))
        if not evidence_path.is_file() or sha256(evidence_path) != run.get("evidence_sha256"):
            run_errors.append(f"{run['run_id']} evidence is missing or hash-mismatched")
        if run_errors:
            raise ValueError("; ".join(run_errors))
        by_case[case_id][target_field].append(run)
        existing_ids.add(run["run_id"])
        recorded.append(run["run_id"])
    suite_path_value.write_text(json.dumps(suite_value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "RECORDED", "suite": str(suite_path_value), "variant": variant, "runs": recorded}, ensure_ascii=False, indent=2))
    return 0


def rag_gate(value: object, check_path: Path | None = None) -> tuple[list[str], dict]:
    failures: list[str] = []
    if not isinstance(value, dict) or value.get("schema_version") != RAG_SCHEMA:
        return [f"schema_version must be {RAG_SCHEMA}"], {}
    for field in ("project", "retriever", "policy", "queries"):
        if field not in value:
            failures.append(f"missing {field}")
    if failures:
        return failures, {}
    project_root = None
    if check_path is not None:
        project_root = check_path.parent.parent.parent if check_path.parent.name == "evals" else check_path.parent
    retriever = value["retriever"]
    for field in ("name", "version", "index_snapshot"):
        if not isinstance(retriever, dict) or contains_placeholder(retriever.get(field)):
            failures.append(f"retriever.{field} is missing or still a placeholder")
    index_hash = retriever.get("index_snapshot_sha256") if isinstance(retriever, dict) else None
    if not isinstance(index_hash, str) or len(index_hash) != 64 or any(ch not in "0123456789abcdef" for ch in index_hash):
        failures.append("retriever.index_snapshot_sha256 must be lowercase SHA-256")
    elif project_root is not None and isinstance(retriever, dict):
        index_path = resolve_evidence(project_root, str(retriever.get("index_snapshot", "")))
        if not index_path.is_file():
            failures.append(f"retriever index snapshot does not exist: {index_path}")
        elif sha256(index_path) != index_hash:
            failures.append("retriever index snapshot hash mismatch")
    if not isinstance(retriever, dict) or not isinstance(retriever.get("top_k"), int) or retriever["top_k"] < 1:
        failures.append("retriever.top_k must be a positive integer")
    policy = value["policy"]
    threshold_fields = (
        "minimum_recall_at_k", "minimum_grounding_rate", "minimum_citation_verifiability",
        "minimum_injection_resistance_rate", "maximum_cross_boundary_leakage_rate",
    )
    for field in threshold_fields:
        if not isinstance(policy, dict) or not isinstance(policy.get(field), (int, float)) or not 0 <= policy[field] <= 1:
            failures.append(f"policy.{field} must be 0..1")
    queries = value["queries"]
    if not isinstance(queries, list):
        return failures + ["queries must be an array"], {}
    classes = {query.get("class") for query in queries if isinstance(query, dict)}
    missing_classes = sorted(RAG_CLASSES - classes)
    if missing_classes:
        failures.append(f"missing required query classes: {', '.join(missing_classes)}")
    recall_eligible = 0
    recall_hits = 0
    answer_claims = grounded_claims = citations = verified_citations = 0
    injection_cases = injection_resisted = 0
    boundary_cases = boundary_leaks = 0
    for index, query in enumerate(queries, start=1):
        prefix = f"query {index}"
        required = {
            "query_id", "class", "question", "expected_source_ids", "retrieved_source_ids",
            "answer_claims", "grounded_claims", "citations", "verifiable_citations",
            "injection_obeyed", "cross_boundary_sources", "evidence", "evidence_sha256",
        }
        if not isinstance(query, dict) or not required.issubset(query):
            failures.append(f"{prefix} is incomplete")
            continue
        query_id = query["query_id"]
        if query["class"] not in RAG_CLASSES:
            failures.append(f"{query_id}.class is invalid")
        if contains_placeholder(query["question"]) or contains_placeholder(query["evidence"]):
            failures.append(f"{query_id} still contains a placeholder")
        evidence_hash = query.get("evidence_sha256")
        if not isinstance(evidence_hash, str) or len(evidence_hash) != 64 or any(ch not in "0123456789abcdef" for ch in evidence_hash):
            failures.append(f"{query_id}.evidence_sha256 must be lowercase SHA-256")
        elif project_root is not None:
            evidence_path = resolve_evidence(project_root, query["evidence"])
            if not evidence_path.is_file():
                failures.append(f"{query_id} evidence does not exist: {evidence_path}")
            elif sha256(evidence_path) != evidence_hash:
                failures.append(f"{query_id} evidence hash mismatch")
        expected = set(query["expected_source_ids"])
        retrieved = set(query["retrieved_source_ids"])
        if expected:
            recall_eligible += 1
            recall_hits += bool(expected & retrieved)
        for field in ("answer_claims", "grounded_claims", "citations", "verifiable_citations", "cross_boundary_sources"):
            if not isinstance(query[field], int) or query[field] < 0:
                failures.append(f"{query_id}.{field} must be a non-negative integer")
        if isinstance(query["grounded_claims"], int) and isinstance(query["answer_claims"], int) and query["grounded_claims"] > query["answer_claims"]:
            failures.append(f"{query_id}.grounded_claims exceeds answer_claims")
        if isinstance(query["verifiable_citations"], int) and isinstance(query["citations"], int) and query["verifiable_citations"] > query["citations"]:
            failures.append(f"{query_id}.verifiable_citations exceeds citations")
        answer_claims += int(query.get("answer_claims", 0))
        grounded_claims += int(query.get("grounded_claims", 0))
        citations += int(query.get("citations", 0))
        verified_citations += int(query.get("verifiable_citations", 0))
        if query["class"] == "injection":
            injection_cases += 1
            injection_resisted += query["injection_obeyed"] is False
        if query["class"] == "cross_boundary":
            boundary_cases += 1
            boundary_leaks += int(query.get("cross_boundary_sources", 0)) > 0
    metrics = {
        "recall_at_k": recall_hits / recall_eligible if recall_eligible else None,
        "grounding_rate": grounded_claims / answer_claims if answer_claims else None,
        "citation_verifiability": verified_citations / citations if citations else None,
        "injection_resistance_rate": injection_resisted / injection_cases if injection_cases else None,
        "cross_boundary_leakage_rate": boundary_leaks / boundary_cases if boundary_cases else None,
    }
    checks = {
        "recall_at_k": ("minimum_recall_at_k", ">="),
        "grounding_rate": ("minimum_grounding_rate", ">="),
        "citation_verifiability": ("minimum_citation_verifiability", ">="),
        "injection_resistance_rate": ("minimum_injection_resistance_rate", ">="),
        "cross_boundary_leakage_rate": ("maximum_cross_boundary_leakage_rate", "<="),
    }
    if isinstance(policy, dict):
        for metric, (threshold, operator) in checks.items():
            value_metric = metrics[metric]
            value_threshold = policy.get(threshold)
            if value_metric is None:
                failures.append(f"{metric} has no denominator")
            elif isinstance(value_threshold, (int, float)):
                failed = value_metric < value_threshold if operator == ">=" else value_metric > value_threshold
                if failed:
                    failures.append(f"{metric} {value_metric:.3f} fails {operator} {value_threshold}")
    return failures, metrics


def command_init(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    destination = suite_path(project)
    if destination.exists():
        raise ValueError(f"Eval suite already exists; not overwriting: {destination}")
    template = Path(args.template).expanduser().resolve() if args.template else default_template()
    if not template.is_file():
        raise ValueError(f"Eval template not found: {template}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, destination)
    value = load(destination)
    value["project"] = args.name or project.name
    destination.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destination)
    return 0


def command_design(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve()
    profile = load(Path(args.profile).expanduser().resolve()) if args.profile else None
    goal = ""
    if args.goal_contract:
        contract = load(Path(args.goal_contract).expanduser().resolve())
        if isinstance(contract, dict):
            goal = str(contract.get("objective") or contract.get("request") or "")
    if args.goal:
        goal = args.goal
    destination = Path(args.suite).expanduser().resolve() if args.suite else suite_path(project)
    result = design_project_suite(
        project,
        name=args.name,
        goal=goal,
        profile=profile,
        destination=destination,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"CREATED", "REUSED"} else 2


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.suite).expanduser().resolve()
    errors = validate(load(path))
    result = {"suite": str(path), "status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def command_summary(args: argparse.Namespace) -> int:
    path = Path(args.suite).expanduser().resolve()
    value = load(path)
    errors = validate(value)
    summary = summarize(value) if isinstance(value, dict) and value.get("schema_version") == SCHEMA else {}
    result = {
        **summary,
        "suite": str(path),
        "validation": "PASS" if not errors else "FAIL",
        "errors": errors,
        "interpretation": "No release conclusion until the mandatory project gate passes." if not summary.get("completed_case_pairs") else "Treat this result as project-specific, not a universal P2P benchmark.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def command_gate(args: argparse.Namespace) -> int:
    path = Path(args.suite).expanduser().resolve()
    value = load(path)
    failures, summary = gate(value, path) if isinstance(value, dict) else (["suite must be an object"], {})
    result = {
        "schema_version": "p2p-codex-project-eval-gate/1",
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "suite": str(path),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "summary": summary,
    }
    if args.report:
        output = Path(args.report).expanduser().resolve()
        if output.exists():
            raise ValueError(f"Refusing to overwrite report: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


def command_rag_gate(args: argparse.Namespace) -> int:
    path = Path(args.check).expanduser().resolve()
    failures, metrics = rag_gate(load(path), path)
    result = {
        "schema_version": "p2p-codex-rag-gate/1",
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "check": str(path),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "metrics": metrics,
    }
    if args.report:
        output = Path(args.report).expanduser().resolve()
        if output.exists():
            raise ValueError(f"Refusing to overwrite report: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


def command_migrate(args: argparse.Namespace) -> int:
    source = Path(args.suite).expanduser().resolve()
    value = load(source)
    if not isinstance(value, dict) or value.get("schema_version") != LEGACY_SCHEMA:
        raise ValueError(f"Migration input must use {LEGACY_SCHEMA}")
    migrated = {
        "schema_version": SCHEMA,
        "project": value.get("project", source.parent.parent.parent.name),
        "policy": {
            "minimum_cases": 5,
            "minimum_trials_per_variant": 2,
            "minimum_p2p_pass_rate": 0.8,
            "maximum_mean_regression": 0.0,
            "maximum_case_regressions": 0,
            "maximum_score_spread": 0.25,
            "blocked_cases_allowed": False,
        },
        "comparison_contract": {
            **value.get("comparison_contract", {}),
            "criteria_defined_before_runs": True,
            "frozen_fixtures": True,
            "no_cross_run_memory": True,
        },
        "cases": [],
    }
    for case in value.get("cases", []):
        converted = {
            "case_id": case.get("case_id", "migrated-case"),
            "class": "other",
            "title": case.get("title", "Migrated case — classify before gate"),
            "task": case.get("task", ""),
            "fixture": case.get("fixture", ""),
            "fixture_sha256": "",
            "tags": [*case.get("tags", []), "migrated-needs-review"],
            "checks": case.get("checks", []),
            "baseline_runs": [],
            "p2p_runs": [],
        }
        for old_name, new_name in (("baseline", "baseline_runs"), ("p2p", "p2p_runs")):
            run = case.get(old_name, {})
            if run.get("status") in RUN_STATUSES:
                converted[new_name].append(
                    {
                        "run_id": f"migrated-{converted['case_id']}-{old_name}-1",
                        "status": run["status"],
                        "model": run.get("model") or "REVIEW_REQUIRED",
                        "surface": run.get("surface") or "REVIEW_REQUIRED",
                        "environment_id": "REVIEW_REQUIRED",
                        "run_at": run.get("run_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                        "score": run.get("score") if isinstance(run.get("score"), (int, float)) else 0,
                        "evidence": run.get("evidence") or "REVIEW_REQUIRED",
                        "evidence_sha256": "",
                        "unexpected_writes": 0,
                        "notes": "Migrated from schema v1; rerun and hash evidence before release.",
                    }
                )
        migrated["cases"].append(converted)
    output = Path(args.out).expanduser().resolve() if args.out else source.with_name("suite.v2.json")
    write_json_new(output, migrated)
    print(json.dumps({"status": "MIGRATED_REVIEW_REQUIRED", "output": str(output)}, ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--project", default=".")
    init.add_argument("--name")
    init.add_argument("--template")
    init.set_defaults(func=command_init)
    design = sub.add_parser("design", help="Create or reuse a minimal project-specific eval suite")
    design.add_argument("--project", default=".")
    design.add_argument("--name")
    design.add_argument("--goal")
    design.add_argument("--goal-contract")
    design.add_argument("--profile")
    design.add_argument("--suite")
    design.set_defaults(func=command_design)
    check = sub.add_parser("validate")
    check.add_argument("--suite", required=True)
    check.set_defaults(func=command_validate)
    summary = sub.add_parser("summary")
    summary.add_argument("--suite", required=True)
    summary.set_defaults(func=command_summary)
    gate_parser = sub.add_parser("gate")
    gate_parser.add_argument("--suite", required=True)
    gate_parser.add_argument("--report")
    gate_parser.set_defaults(func=command_gate)
    run_parser = sub.add_parser("run", help="Run one isolated baseline or current-P2P trial against the frozen suite")
    run_parser.add_argument("--suite", required=True)
    run_parser.add_argument("--variant", choices=tuple(TRIAL_VARIANTS), required=True)
    run_parser.add_argument("--trial", type=int, required=True)
    run_parser.add_argument("--target-root", required=True)
    run_parser.add_argument("--evidence-dir")
    run_parser.add_argument("--model", default="deterministic-local-runner")
    run_parser.add_argument("--surface", default="p2p-uiux-project-eval/1")
    run_parser.add_argument("--environment-id", default="p2p-eval-py312-isolated")
    run_parser.set_defaults(func=command_run_trial)
    record_parser = sub.add_parser("record", help="Record one executed trial into the project suite")
    record_parser.add_argument("--suite", required=True)
    record_parser.add_argument("--trial-record", required=True)
    record_parser.set_defaults(func=command_record_trial)
    rag = sub.add_parser("rag-gate")
    rag.add_argument("--check", required=True)
    rag.add_argument("--report")
    rag.set_defaults(func=command_rag_gate)
    migrate = sub.add_parser("migrate")
    migrate.add_argument("--suite", required=True)
    migrate.add_argument("--out")
    migrate.set_defaults(func=command_migrate)
    return p


if __name__ == "__main__":
    parsed = parser().parse_args()
    try:
        raise SystemExit(parsed.func(parsed))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
