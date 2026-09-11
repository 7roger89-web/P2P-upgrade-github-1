#!/usr/bin/env python3
"""Prove the SHIELD-SECRET-01 vertical slice against its pinned provider.

The harness creates throwaway Git fixtures in one temporary directory, assesses
every acceptance case through ``shield.runner``, checks the evidence contract on
each record, and prints one slice verdict. Fixture token values are assembled at
runtime from an obviously invalid placeholder, so no live or credential-like
secret is committed to P2P or kept on disk after the run.

Exit codes: ``0`` every case matched its expected Shield status and every
evidence record carried the full control evidence contract; ``1`` an acceptance
expectation failed; ``2`` the harness could not run far enough to judge.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Sequence

if __package__ in (None, ""):  # allow direct execution: python3 shield/acceptance.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shield.runner import (  # noqa: E402
    SHIELD_DIR,
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_PASS,
    Blocked,
    assess,
    load_control,
)

WORK_PREFIX = "p2p-shield-slice1-"
# The pinned provider's token shape, assembled at runtime so that no
# credential-like literal is stored in source. The result is an invalid
# placeholder value and is never a live credential.
FAKE_TOKEN_VALUE = "ghp_" + "FAKE" * 9
CLEAN_MARKER = "P2P_SHIELD_CLEAN_FIXTURE"
LEAK_FILE = "config/service-settings.env"

GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "P2P Shield Fixture",
    "GIT_AUTHOR_EMAIL": "p2p-shield-fixture@example.invalid",
    "GIT_COMMITTER_NAME": "P2P Shield Fixture",
    "GIT_COMMITTER_EMAIL": "p2p-shield-fixture@example.invalid",
}

CLEAN_FILES = {
    "README.md": (
        f"# {CLEAN_MARKER}\n\n"
        "Throwaway clean target for Shield acceptance. It contains no credential\n"
        "material and is deleted after the run.\n"
    ),
    "src/service.py": (
        '"""Fixture service with only harmless literal values."""\n\n'
        "SERVICE_NAME = 'p2p-shield-fixture'\n"
        "TIMEOUT_SECONDS = 30\n\n\n"
        "def readiness() -> dict[str, str]:\n"
        "    return {'status': 'ready'}\n"
    ),
    LEAK_FILE: "SERVICE_NAME=p2p-shield-fixture\nSERVICE_TIMEOUT_SECONDS=30\n",
}

LEAKED_FILES = {
    "README.md": (
        f"# {CLEAN_MARKER}-LEAK\n\n"
        "Throwaway failing target for Shield acceptance. The token value in\n"
        f"{LEAK_FILE} is an invalid test placeholder, never a live credential.\n"
    ),
    LEAK_FILE: (
        "# P2P SHIELD ACCEPTANCE FIXTURE - INVALID PLACEHOLDER VALUE, NOT A CREDENTIAL\n"
        f"SERVICE_NAME=p2p-shield-fixture\nSERVICE_TOKEN={FAKE_TOKEN_VALUE}\n"
    ),
}


class Case:
    """One acceptance expectation for one scope against one generated fixture."""

    def __init__(
        self,
        name: str,
        scan_mode: str,
        target_key: str,
        expected_status: str,
        *,
        executable_key: str = "pinned",
        expected_finding_file: str | None = None,
    ) -> None:
        self.name = name
        self.scan_mode = scan_mode
        self.target_key = target_key
        self.expected_status = expected_status
        self.executable_key = executable_key
        self.expected_finding_file = expected_finding_file


CASES = (
    Case("pass_clean_history", "git_history_scan", "clean", STATUS_PASS),
    Case("pass_clean_worktree", "worktree_scan", "clean", STATUS_PASS),
    Case(
        "fail_leaked_history",
        "git_history_scan",
        "leaked",
        STATUS_FAIL,
        expected_finding_file=LEAK_FILE,
    ),
    Case(
        "fail_leaked_worktree",
        "worktree_scan",
        "leaked",
        STATUS_FAIL,
        expected_finding_file=LEAK_FILE,
    ),
    # Deterministic harness BLOCKED proof: the required provider cannot run.
    Case(
        "blocked_unavailable_provider",
        "git_history_scan",
        "clean",
        STATUS_BLOCKED,
        executable_key="absent",
    ),
    # Fail-closed proof: a provider error must never be read as a clean result.
    Case("blocked_target_not_a_repository", "git_history_scan", "plain_directory", STATUS_BLOCKED),
)

CONTRACT_EVIDENCE_FIELDS = ("scope", "status", "coverage", "reason")


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, **GIT_IDENTITY},
    )


def _write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _make_repo(root: Path, name: str, files: dict[str, str]) -> Path:
    repo = root / name
    repo.mkdir(parents=True)
    _run_git(repo, "init", "-q", "--initial-branch=main")
    _write_files(repo, files)
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", "p2p shield acceptance fixture")
    return repo


def build_fixtures(work_dir: Path) -> dict[str, Path]:
    plain_directory = work_dir / "not-a-repository"
    plain_directory.mkdir(parents=True)
    _write_files(plain_directory, {"README.md": f"# {CLEAN_MARKER}-NONGIT\n"})
    return {
        "clean": _make_repo(work_dir, "clean-target", CLEAN_FILES),
        "leaked": _make_repo(work_dir, "leaked-target", LEAKED_FILES),
        "plain_directory": plain_directory,
        "absent": work_dir / "provider-dir" / "gitleaks-is-not-installed-here",
    }


def check_contract(evidence: dict[str, Any], contract_fields: Sequence[str]) -> list[str]:
    problems = []
    for field in tuple(contract_fields) + CONTRACT_EVIDENCE_FIELDS:
        if field not in evidence or evidence[field] in (None, ""):
            problems.append(f"EVIDENCE_FIELD_MISSING:{field}")
    if evidence.get("status") not in (STATUS_PASS, STATUS_FAIL, STATUS_BLOCKED):
        problems.append(f"EVIDENCE_STATUS_UNSUPPORTED:{evidence.get('status')}")
    if not isinstance(evidence.get("findings_count"), int) or evidence["findings_count"] < 0:
        problems.append("EVIDENCE_FINDINGS_COUNT_INVALID")
    if not evidence.get("limitations"):
        problems.append("EVIDENCE_LIMITATIONS_EMPTY")
    return problems


def run_cases(
    *,
    cases: Sequence[Case],
    fixtures: dict[str, Path],
    provider_executable: str,
    control_id: str,
    shield_dir: Path,
    evidence_dir: Path,
    reference: str,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    contract_fields = load_control(shield_dir, control_id)[0]["evidence_fields"]
    records: list[dict[str, Any]] = []
    problems: list[str] = []
    for case in cases:
        executable = provider_executable
        if case.executable_key != "pinned":
            executable = str(fixtures[case.executable_key])
        evidence = assess(
            shield_dir=shield_dir,
            control_id=control_id,
            scan_mode=case.scan_mode,
            target=fixtures[case.target_key],
            executable=executable,
            provider_mapping=None,
            timeout=timeout,
            reference=reference,
        )
        serialised = json.dumps(evidence, indent=2, sort_keys=True)
        evidence_path = evidence_dir / f"slice1-{case.name}.json"
        evidence_path.write_text(serialised + "\n", encoding="utf-8")
        print(f"----- EVIDENCE {case.name} ({case.scan_mode}) -----")
        print(serialised)
        record = {
            "case": case.name,
            "scan_mode": case.scan_mode,
            "expected_status": case.expected_status,
            "observed_status": evidence.get("status"),
            "findings_count": evidence.get("findings_count"),
            "reason": evidence.get("reason"),
            "provider_version": evidence.get("provider_version"),
            "evidence_file": str(evidence_path),
        }
        if evidence.get("status") != case.expected_status:
            problems.append(
                f"CASE_STATUS_MISMATCH:{case.name}:expected={case.expected_status}"
                f":observed={evidence.get('status')}:reason={evidence.get('reason')}"
            )
        contract_problems = check_contract(evidence, contract_fields)
        if contract_problems:
            problems.extend(f"{case.name}:{problem}" for problem in contract_problems)
        if case.expected_finding_file is not None and not any(
            str(finding.get("file", "")).endswith(case.expected_finding_file)
            for finding in evidence.get("findings", [])
        ):
            problems.append(
                f"CASE_FINDING_SOURCE_UNEXPECTED:{case.name}:expected_file={case.expected_finding_file}"
            )
        if _contains_secret_value(evidence):
            problems.append(f"EVIDENCE_LEAKED_PROVIDER_SECRET_VALUE:{case.name}")
        record["status_match"] = evidence.get("status") == case.expected_status
        record["contract_problems"] = contract_problems
        records.append(record)
    return records, problems


def _contains_secret_value(evidence: dict[str, Any]) -> bool:
    """Guard the acceptance harness itself: evidence must not carry the value."""
    return FAKE_TOKEN_VALUE in json.dumps(evidence)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--executable", required=True, help="Pinned provider executable path")
    parser.add_argument("--control", default="SHIELD-SECRET-01")
    parser.add_argument("--shield-dir", default=str(SHIELD_DIR))
    parser.add_argument("--work-dir", default=None, help="Base directory for throwaway fixtures")
    parser.add_argument(
        "--evidence-dir",
        default=None,
        help="Where to write evidence records (defaults to <work-dir>/shield-evidence)",
    )
    parser.add_argument(
        "--evidence-reference",
        default="UNREFERENCED",
        help="Durable reference stored in each evidence record",
    )
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove the generated fixture work directory when this run created it",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    started = time.monotonic()
    created_base = args.work_dir is None
    base_dir = (
        Path(tempfile.mkdtemp(prefix=WORK_PREFIX))
        if created_base
        else Path(args.work_dir).resolve()
    )
    base_dir.mkdir(parents=True, exist_ok=True)
    work_dir = Path(tempfile.mkdtemp(prefix="fixtures-", dir=base_dir))
    evidence_dir = (
        Path(args.evidence_dir).resolve() if args.evidence_dir else base_dir / "shield-evidence"
    )
    print("P2P_SHIELD_SLICE=P2P_SHIELD_V0_1_SECRET_CONTROL_VERTICAL_SLICE")
    print(f"CONTROL={args.control} WORK_DIR={work_dir} EVIDENCE_DIR={evidence_dir}")
    verdict_code = 2
    try:
        try:
            fixtures = build_fixtures(work_dir)
            records, problems = run_cases(
                cases=CASES,
                fixtures=fixtures,
                provider_executable=args.executable,
                control_id=args.control,
                shield_dir=Path(args.shield_dir).resolve(),
                evidence_dir=evidence_dir,
                reference=args.evidence_reference,
                timeout=args.timeout_seconds,
            )
        except Blocked as exc:
            print(f"ACCEPTANCE_HARNESS_BLOCKED:{exc.reason}")
            print("SLICE_VERDICT=BLOCKED")
            return 2
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip().splitlines()
            print(f"ACCEPTANCE_FIXTURE_BUILD_FAILED:{exc.cmd[0]}:{detail[-1] if detail else exc}")
            print("SLICE_VERDICT=BLOCKED")
            return 2
        for record in records:
            print("CASE " + json.dumps(record, sort_keys=True))
        print(f"ACCEPTANCE_CASES={len(records)}")
        print(f"ACCEPTANCE_SECONDS={time.monotonic() - started:.1f}")
        if problems:
            # When no case ever completed, the provider never produced a
            # reliable assessment: that is a BLOCKED slice, not an evaluated
            # PASS/FAIL outcome.
            provider_never_completed = bool(records) and all(
                record["observed_status"] == STATUS_BLOCKED for record in records
            )
            print("ACCEPTANCE_PROBLEMS:")
            for problem in problems:
                print(f"  - {problem}")
            if provider_never_completed:
                print("SLICE_VERDICT=BLOCKED PROVIDER_NEVER_COMPLETED=YES")
                verdict_code = 2
            else:
                print("SLICE_VERDICT=FAIL")
                verdict_code = 1
        else:
            print(
                "SLICE_VERDICT=PASS EVIDENCE_CONTRACT_PROVEN=YES "
                "PASS_CASE_PROVEN=YES FAIL_CASE_PROVEN=YES BLOCKED_CASE_PROVEN=YES"
            )
            verdict_code = 0
    finally:
        if args.cleanup and created_base:
            shutil.rmtree(base_dir, ignore_errors=True)
    return verdict_code


if __name__ == "__main__":
    raise SystemExit(main())
