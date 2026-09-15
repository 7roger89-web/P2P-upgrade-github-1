"""Read-only complete-working-tree evidence against an exact Git baseline.

Runtime core shared by source-repository and installed-project CLIs. It never
mutates the repository/index and never reads file contents. Results support
verification but are not acceptance authority by themselves.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "p2p-complete-worktree-evidence/1"
_GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")


class WorktreeEvidenceError(RuntimeError):
    pass


def _run_git(root: Path, args: list[str], *, allow_nonzero: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode and not allow_nonzero:
        message = (result.stderr or result.stdout).strip()
        raise WorktreeEvidenceError(f"GIT_COMMAND_FAILED:{args[0]}:{message}")
    return result


def _root(value: str | Path) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise WorktreeEvidenceError("ROOT_NOT_DIRECTORY")
    inside = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
    if inside.stdout.strip() != "true":
        raise WorktreeEvidenceError("ROOT_NOT_GIT_WORKTREE")
    return root


def _baseline(root: Path, value: str) -> str:
    text = str(value or "").strip().lower()
    if not _GIT_OID_RE.fullmatch(text):
        raise WorktreeEvidenceError("BASELINE_MUST_BE_FULL_GIT_COMMIT_OID")
    resolved = _run_git(root, ["rev-parse", "--verify", f"{text}^{{commit}}"])
    if resolved.stdout.strip().lower() != text:
        raise WorktreeEvidenceError("BASELINE_COMMIT_NOT_EXACT")
    return text


def _nul_paths(text: str) -> tuple[str, ...]:
    return tuple(item for item in text.split("\0") if item)


def _tracked_changed(root: Path, baseline: str) -> tuple[str, ...]:
    # One revision is load-bearing: compare complete working tree vs baseline,
    # not baseline..HEAD which would miss staged/unstaged changes.
    result = _run_git(root, ["diff", "--name-only", "-z", baseline, "--"])
    return tuple(sorted(set(_nul_paths(result.stdout))))


def _untracked(root: Path) -> tuple[str, ...]:
    result = _run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    return tuple(sorted(set(_nul_paths(result.stdout))))


def complete_worktree_summary(root: str | Path, baseline: str) -> dict[str, Any]:
    repo = _root(root)
    base = _baseline(repo, baseline)
    head = _run_git(repo, ["rev-parse", "HEAD"]).stdout.strip().lower()
    tracked = _tracked_changed(repo, base)
    untracked = _untracked(repo)
    changed = tuple(sorted(set(tracked) | set(untracked)))
    status = _run_git(repo, ["status", "--porcelain=v1", "--untracked-files=all"]).stdout
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "root": str(repo),
        "baseline_commit": base,
        "head_commit": head,
        "tracked_changed_files": list(tracked),
        "untracked_files": list(untracked),
        "changed_files": list(changed),
        "changed_file_count": len(changed),
        "clean_vs_baseline": len(changed) == 0,
        "working_tree_clean_now": not bool(status.strip()),
        "comparison_semantics": "COMPLETE_WORKTREE_VS_SINGLE_BASELINE_COMMIT",
        "includes_committed_after_baseline": True,
        "includes_staged": True,
        "includes_unstaged": True,
        "includes_deleted_tracked": True,
        "includes_untracked": True,
        "file_contents_read": False,
        "repository_mutated": False,
        "acceptance_authority": False,
    }


def _relative_path(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise WorktreeEvidenceError("PATH_REQUIRED")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise WorktreeEvidenceError("PATH_MUST_BE_PROJECT_RELATIVE")
    normalized = path.as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized or normalized == ".":
        raise WorktreeEvidenceError("PATH_REQUIRED")
    return normalized


def deliverable_evidence(root: str | Path, baseline: str, path: str) -> dict[str, Any]:
    repo = _root(root)
    base = _baseline(repo, baseline)
    relative = _relative_path(path)
    tracked = set(_tracked_changed(repo, base))
    untracked = set(_untracked(repo))
    target = repo / relative
    present_on_disk = target.exists() or target.is_symlink()
    tracked_now = _run_git(
        repo, ["ls-files", "--error-unmatch", "--", relative], allow_nonzero=True
    ).returncode == 0

    if relative in untracked:
        state = "UNTRACKED_NEW"
        present = True
        produced = True
    elif relative in tracked:
        if present_on_disk:
            state = "CHANGED_VS_BASELINE"
            present = True
        else:
            state = "DELETED_VS_BASELINE"
            present = False
        produced = True
    elif present_on_disk or tracked_now:
        state = "EXISTS_UNCHANGED"
        present = present_on_disk
        produced = False
    else:
        state = "MISSING"
        present = False
        produced = False

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "baseline_commit": base,
        "path": relative,
        "state": state,
        "present": present,
        "produced_or_changed_since_baseline": produced,
        "file_contents_read": False,
        "repository_mutated": False,
        "acceptance_authority": False,
    }
