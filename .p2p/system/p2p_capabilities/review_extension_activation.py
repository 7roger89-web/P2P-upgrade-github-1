"""State-aware activation decision for the optional OpenCodeReview scaffold.

This is deliberately not a router. It activates only when either:

- the task text already contains an explicit review-coverage failure signal; or
- durable/runtime evidence shows a material review gap, such as a large diff or
  a recent failed/blocked Control Tower session.

A generic request to ``review code`` remains insufficient on its own. The
returned guidance never grants authority, permission, acceptance, or promotion.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA = "p2p-review-extension-activation/2"
ACTIVATION = "OPTIONAL_EXTENSION_AFTER_DOCUMENTED_OR_RUNTIME_REVIEW_GAP"
CLASSIFICATION = "NON_AUTHORITATIVE_REVIEW_SCAFFOLD"
LARGE_DIFF_FILE_THRESHOLD = 20
LEDGER_RELATIVE_PATH = Path(".p2p/state/execution-ledger.jsonl")

_REVIEW_GAP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("LARGE_COMPLEX_DIFF", re.compile(r"\b(?:large|complex|huge|very large)\s+(?:code\s+)?diff\b", re.I)),
    ("MISSED_FILE", re.compile(r"\b(?:missed|omitted|skipped|forgot(?:ten)?)\s+(?:changed\s+)?files?\b", re.I)),
    ("COVERAGE_GAP", re.compile(r"\b(?:review\s+)?coverage\s+(?:gap|uncertainty|incomplete|unknown)\b", re.I)),
    ("REPEATED_REPAIR", re.compile(r"\b(?:repeated|second|third|another)\s+(?:review\s+)?repair(?:\s+round)?\b|\brepair\s+round\s*[2-9]\b", re.I)),
    ("ALL_CHANGED_FILES", re.compile(r"\breview\s+all\s+changed\s+files\b", re.I)),
    ("LINE_TARGETING_GAP", re.compile(r"\b(?:line|comment)\s+(?:anchoring|targeting)\s+(?:gap|uncertainty|wrong|incorrect)\b", re.I)),
    ("RULE_TARGETING_GAP", re.compile(r"\brule\s+(?:matching|targeting|resolution)\s+(?:gap|uncertainty|wrong|incorrect)\b", re.I)),
)
_FAILURE_STATES = frozenset({"FAILED", "BLOCKED"})
_HASH40 = re.compile(r"^[0-9a-fA-F]{40}$")


def _run_git(root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode:
        return None
    return result.stdout.strip()


def _discover_root(explicit_root: str | Path | None = None) -> Path | None:
    candidates: list[Path] = []
    if explicit_root not in (None, "", "UNKNOWN"):
        candidates.append(Path(explicit_root).expanduser())
    env_root = os.environ.get("P2P_PROJECT_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser())
    candidates.append(Path.cwd())

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        top = _run_git(resolved, ["rev-parse", "--show-toplevel"])
        if top:
            return Path(top).resolve()
        for parent in (resolved, *resolved.parents):
            if (parent / ".git").exists():
                return parent
    return None


def _iter_recent_ledger_events(root: Path, limit: int = 80) -> Iterable[Mapping[str, Any]]:
    path = root / LEDGER_RELATIVE_PATH
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except OSError:
        return ()
    events: list[Mapping[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(value, Mapping):
            events.append(value)
    return tuple(events)


def _latest_base_sha(events: Iterable[Mapping[str, Any]]) -> str | None:
    for event in reversed(tuple(events)):
        for key in ("CANONICAL_BASE_SHA", "canonical_base_sha", "BASE_SHA", "base_sha"):
            raw = event.get(key)
            if isinstance(raw, str) and _HASH40.fullmatch(raw.strip()):
                return raw.strip().lower()
    return None


def _recent_failure(events: Iterable[Mapping[str, Any]]) -> bool:
    for event in reversed(tuple(events)):
        state = event.get("SESSION_STATE") or event.get("session_state") or event.get("terminal_verdict")
        if isinstance(state, str):
            normalized = state.strip().upper().replace("-", "_")
            if normalized in _FAILURE_STATES:
                return True
            if normalized in {"COMPLETED", "READY", "WAITING_OWNER_GATE", "ABORTED", "ACTIVE"}:
                return False
    return False


def _fallback_base(root: Path) -> str | None:
    for ref in ("origin/main", "main"):
        base = _run_git(root, ["merge-base", "HEAD", ref])
        if base and _HASH40.fullmatch(base):
            return base.lower()
    return None


def _changed_files(root: Path, base_sha: str | None) -> tuple[str, ...]:
    paths: set[str] = set()
    if base_sha and _HASH40.fullmatch(base_sha):
        committed = _run_git(root, ["diff", "--name-only", f"{base_sha}...HEAD", "--"])
        if committed:
            paths.update(line.strip() for line in committed.splitlines() if line.strip())
    working = _run_git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if working:
        for line in working.splitlines():
            payload = line[3:].strip() if len(line) >= 4 else ""
            if " -> " in payload:
                payload = payload.split(" -> ", 1)[1]
            if payload:
                paths.add(payload)
    return tuple(sorted(paths))


def runtime_review_evidence(root: str | Path | None = None) -> dict[str, Any]:
    repo = _discover_root(root)
    if repo is None:
        return {
            "repo_root": None,
            "signals": [],
            "changed_file_count": 0,
            "recent_failed_or_blocked": False,
            "base_sha": None,
            "read_only": True,
        }

    events = tuple(_iter_recent_ledger_events(repo))
    base_sha = _latest_base_sha(events) or _fallback_base(repo)
    changed = _changed_files(repo, base_sha)
    signals: list[str] = []
    failed = _recent_failure(events)
    if failed:
        signals.append("RECENT_FAILED_OR_BLOCKED_SESSION")
    if len(changed) >= LARGE_DIFF_FILE_THRESHOLD:
        signals.append("LARGE_DIFF_RUNTIME")

    return {
        "repo_root": repo.as_posix(),
        "signals": signals,
        "changed_file_count": len(changed),
        "changed_files": list(changed),
        "recent_failed_or_blocked": failed,
        "base_sha": base_sha,
        "read_only": True,
    }


def review_gap_decision(
    task_text: str,
    *,
    root: str | Path | None = None,
    runtime_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    task = " ".join(str(task_text or "").split())
    matched: list[str] = []
    for code, pattern in _REVIEW_GAP_PATTERNS:
        if pattern.search(task):
            matched.append(code)

    runtime = dict(runtime_evidence) if isinstance(runtime_evidence, Mapping) else runtime_review_evidence(root)
    raw_runtime_signals = runtime.get("signals")
    if isinstance(raw_runtime_signals, (list, tuple)):
        for signal in raw_runtime_signals:
            normalized = str(signal).strip().upper()
            if normalized and normalized not in matched:
                matched.append(normalized)

    active = bool(matched)
    return {
        "schema": SCHEMA,
        "decision": "USE_OCR_DELEGATION" if active else "NO_REVIEW_GAP",
        "activation_policy": ACTIVATION,
        "classification": CLASSIFICATION,
        "matched_signals": matched,
        "runtime_evidence": runtime,
        "authority": "NONE",
        "permission_effect": "NONE",
        "acceptance_authority": False,
        "native_review_still_required": True,
        "shield_and_acceptance_replay_still_required": True,
    }


def render_review_guidance(
    task_text: str,
    *,
    root: str | Path | None = None,
    runtime_evidence: Mapping[str, Any] | None = None,
) -> str:
    decision = review_gap_decision(task_text, root=root, runtime_evidence=runtime_evidence)
    if decision["decision"] != "USE_OCR_DELEGATION":
        return ""
    signals = ",".join(decision["matched_signals"])
    return (
        "OPEN_CODE_REVIEW_DELEGATION=USE_IF_AVAILABLE; "
        f"GAP={signals}; OCR>=1.12.4 delegation only: preview JSON -> rule JSON -> "
        "host agent accounts every (path,status) as REVIEWED or SKIPPED_WITH_REASON; "
        "OCR finding is NONAUTHORITATIVE; OCR unavailable => NATIVE_REVIEW_FALLBACK, never PASS-by-absence; "
        "Shield/native-code-impact/tests/task acceptance still required."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--task-text", required=True)
    args = parser.parse_args(argv)
    decision = review_gap_decision(args.task_text, root=args.root)
    decision["guidance"] = render_review_guidance(
        args.task_text,
        runtime_evidence=decision.get("runtime_evidence"),
    )
    print(json.dumps(decision, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
