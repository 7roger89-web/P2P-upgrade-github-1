#!/usr/bin/env python3
"""Batch sync for P2P-managed project portable law projections.

Smallest useful wrapper around existing portable projector. Reuses
p2p_portable_law_projection.project_law() / expected_project_state().

- Recognizes P2P-managed repos from existing durable markers (AGENTS.md
  P2P block and/or .p2p/portable), not a new registry/database.
- --check: read-only CURRENT|STALE|BLOCKED per project.
- --write: update only stale managed projection files.
- Refuses symlink/unsafe paths via existing projector safety.
- Skips/BLOCKs dirty/conflicting repos rather than overwrite owner work.
- Emits human + JSON summary, idempotent second write = zero changes.
- No daemon, watcher, registry, DB, scheduler, GitHub Action, second control plane.

GitHub-first mode (Issue #264): ``--github-owner <owner> [--check|--write]``
discovers repositories through the ALREADY-AUTHENTICATED ``gh`` CLI (no token
flag, no secret input), detects P2P-managed repos from the same durable markers,
computes expected bytes with the same projector, and in ``--write`` mode commits
ONLY the three generated transport files to one deterministic sync branch/PR per
stale repo. ``SYNC_GENERATED != MERGED_TO_MAIN``: a repo is CURRENT only when
its default branch is verified to contain the fresh projection. Merge stays
under the existing Rule 11 / validated auto-merge governance.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Protocol, Sequence
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (str(REPO_ROOT), str(REPO_ROOT / "scripts"), str(REPO_ROOT / ".p2p" / "system")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import p2p_portable_law_projection as projector  # noqa: E402

PORTABLE_REL = projector.PORTABLE_REL
PORTABLE_EXPERIENCE_REL = getattr(projector, "PORTABLE_EXPERIENCE_REL", Path(".p2p/portable/P2P-EXPERIENCE-CAPSULE.json"))
AGENTS_BEGIN_PORTABLE = projector.AGENTS_BEGIN
AGENTS_BEGIN_CODEX = "<!-- BEGIN P2P CODEX -->"


MANAGED_P2P_DIR_MARKERS = ("portable", "system")


def _markers_indicate_managed(agents_text: str | None, p2p_entry_names: Iterable[str]) -> bool:
    """Durable P2P marker semantics shared by local and GitHub discovery.

    Managed when AGENTS.md carries a P2P block, or `.p2p/portable` (generated
    transport) or `.p2p/system` (installed runtime) exists. No registry.
    """
    if agents_text and (AGENTS_BEGIN_PORTABLE in agents_text or AGENTS_BEGIN_CODEX in agents_text):
        return True
    names = set(p2p_entry_names)
    return any(marker in names for marker in MANAGED_P2P_DIR_MARKERS)


def _is_p2p_managed_dir(path: Path) -> bool:
    """Heuristic: P2P-managed if AGENTS.md has P2P block or .p2p/portable exists."""
    try:
        if not path.is_dir() or path.is_symlink():
            return False
        agents = path / "AGENTS.md"
        text: str | None = None
        if agents.is_file() and not agents.is_symlink():
            try:
                text = agents.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                text = None
        present = [name for name in MANAGED_P2P_DIR_MARKERS if (path / ".p2p" / name).is_dir()]
        if (path / PORTABLE_REL).is_file() and "portable" not in present:
            present.append("portable")
        return _markers_indicate_managed(text, present)
    except OSError:
        return False


def _discover_workspace(workspace: Path) -> list[Path]:
    """Shallow discovery: immediate children that look P2P-managed."""
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError(f"WORKSPACE_NOT_DIRECTORY:{workspace}")
    if workspace.is_symlink():
        raise ValueError(f"WORKSPACE_SYMLINK_NOT_ALLOWED:{workspace}")
    projects: list[Path] = []
    try:
        for child in workspace.iterdir():
            try:
                if child.is_dir() and not child.is_symlink():
                    if _is_p2p_managed_dir(child):
                        projects.append(child)
            except OSError:
                continue
    except OSError as exc:
        raise ValueError(f"WORKSPACE_READ_FAILED:{workspace}:{exc}") from exc
    return sorted(projects)


def _is_git_dirty(project: Path, rel_paths: Iterable[Path]) -> bool:
    """Check if relevant files are dirty in git. If not a git repo, treat as not dirty."""
    git_dir = project / ".git"
    if not git_dir.exists():
        # not a git repo, no dirty check
        return False
    # run git status --porcelain for specific paths
    try:
        # Use --untracked-files=no to only check tracked changes? But we want to detect any dirty.
        # We'll check status for the specific files.
        result = subprocess.run(
            ["git", "-C", str(project), "status", "--porcelain", "--", *[p.as_posix() for p in rel_paths]],
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
        if result.returncode != 0:
            # If git fails, treat as blocked rather than overwrite
            return True
        return bool(result.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return True


def _check_project(package_root: Path, project: Path) -> dict:
    """Return dict with status CURRENT|STALE|BLOCKED and details."""
    project_resolved = project.resolve()
    # safety: refuse symlink project itself
    if project.is_symlink() or project_resolved.is_symlink():
        return {
            "project": str(project),
            "resolved": str(project_resolved),
            "status": "BLOCKED",
            "reason": f"PROJECT_SYMLINK_NOT_ALLOWED:{project}",
        }
    if not project_resolved.is_dir():
        return {
            "project": str(project),
            "resolved": str(project_resolved),
            "status": "BLOCKED",
            "reason": f"PROJECT_NOT_DIRECTORY:{project_resolved}",
        }
    # check parent symlink safety via projector helper
    try:
        # This will raise if parent symlink unsafe
        projector._assert_safe_parent(project_resolved, PORTABLE_REL)
        projector._assert_safe_parent(project_resolved, PORTABLE_EXPERIENCE_REL)
    except ValueError as exc:
        return {
            "project": str(project),
            "resolved": str(project_resolved),
            "status": "BLOCKED",
            "reason": str(exc),
        }

    try:
        state = projector.expected_project_state(package_root, project_resolved)
        expected_proj = state[0]
        expected_agents = state[1]
        expected_exp = state[2] if len(state) > 2 else ""
    except (ValueError, OSError, UnicodeError) as exc:
        return {
            "project": str(project),
            "resolved": str(project_resolved),
            "status": "BLOCKED",
            "reason": str(exc),
        }

    portable_path = project_resolved / PORTABLE_REL
    portable_exp_path = project_resolved / PORTABLE_EXPERIENCE_REL
    agents_path = project_resolved / "AGENTS.md"

    try:
        proj_ok = portable_path.is_file() and portable_path.read_text(encoding="utf-8") == expected_proj
    except (OSError, UnicodeError):
        proj_ok = False
    try:
        agents_ok = agents_path.is_file() and agents_path.read_text(encoding="utf-8") == expected_agents
    except (OSError, UnicodeError):
        agents_ok = False
    try:
        exp_ok = (not expected_exp) or (portable_exp_path.is_file() and portable_exp_path.read_text(encoding="utf-8") == expected_exp)
    except (OSError, UnicodeError):
        exp_ok = False

    if proj_ok and agents_ok and exp_ok:
        return {
            "project": str(project),
            "resolved": str(project_resolved),
            "status": "CURRENT",
            "portable_ok": proj_ok,
            "agents_ok": agents_ok,
            "experience_ok": exp_ok,
        }
    else:
        return {
            "project": str(project),
            "resolved": str(project_resolved),
            "status": "STALE",
            "portable_ok": proj_ok,
            "agents_ok": agents_ok,
            "experience_ok": exp_ok,
        }


def _write_project(package_root: Path, project: Path) -> dict:
    """Attempt to update stale project, respecting dirty check."""
    # First, check dirty before any overwrite attempt
    try:
        project_resolved = project.resolve()
    except OSError:
        project_resolved = project
    if project_resolved.is_dir() and (project_resolved / ".git").exists():
        dirty = _is_git_dirty(project_resolved, [Path("AGENTS.md"), PORTABLE_REL, PORTABLE_EXPERIENCE_REL])
        if dirty:
            return {
                "project": str(project),
                "resolved": str(project_resolved),
                "status": "BLOCKED",
                "reason": f"DIRTY_WORKTREE:{project_resolved}:AGENTS.md or {PORTABLE_REL} has uncommitted changes",
                "action": "SKIP_DIRTY",
            }

    check = _check_project(package_root, project)
    if check["status"] == "CURRENT":
        check["action"] = "SKIP_CURRENT"
        return check
    if check["status"] == "BLOCKED":
        check["action"] = "SKIP_BLOCKED"
        return check

    project_resolved = Path(check["resolved"])
    # Attempt write via projector
    try:
        result = projector.project_law(package_root, project_resolved, check=False)
    except (ValueError, OSError, UnicodeError) as exc:
        return {
            "project": check["project"],
            "resolved": check["resolved"],
            "status": "BLOCKED",
            "reason": str(exc),
            "action": "WRITE_FAILED",
        }

    # Verify now current
    after = _check_project(package_root, project_resolved)
    if after["status"] == "CURRENT":
        after["action"] = "UPDATED"
        after["write_result"] = result
        return after
    else:
        after["action"] = "WRITE_BUT_STILL_STALE"
        after["write_result"] = result
        return after


# ---------------------------------------------------------------------------
# Canonical identity (shared by local and GitHub output)
# ---------------------------------------------------------------------------


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_identity(package_root: Path) -> dict[str, str]:
    """CANONICAL_LAW_SHA256 / PORTABLE_EXPERIENCE_SHA256 from the projector sources."""
    law_text = projector._read_required(package_root / projector.SOURCE_REL, "SOURCE_NOTEBOOK")
    capsule_text = projector.expected_experience_capsule(package_root)
    return {
        "canonical_law_sha256": _sha256_text(law_text),
        "portable_experience_sha256": _sha256_text(capsule_text),
    }


# ---------------------------------------------------------------------------
# GitHub-first mode (Issue #264). Provider boundary + orchestration-free loop.
# ---------------------------------------------------------------------------

GENERATED_PATHS = ("AGENTS.md", PORTABLE_REL.as_posix(), PORTABLE_EXPERIENCE_REL.as_posix())
SYNC_BRANCH = "p2p/portable-law-sync"
CANONICAL_SOURCE_REPO = projector.CANONICAL_SOURCE.split("@", 1)[0]
SCOPE_COMPLETE = {"AUTHENTICATED_USER", "INSTALLATION_ALL"}


class GitHubUnavailable(RuntimeError):
    """Authenticated GitHub access cannot be established (fail closed)."""


class GitHubError(RuntimeError):
    """A single GitHub request failed; the affected repo is BLOCKED."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class RepoRef:
    full_name: str
    default_branch: str
    archived: bool = False


@dataclass(frozen=True)
class Discovery:
    repos: tuple[RepoRef, ...]
    scope: str  # AUTHENTICATED_USER | INSTALLATION_ALL | INSTALLATION_SELECTED
    complete: bool


class GitHubProvider(Protocol):
    def discover(self, owner: str) -> Discovery: ...
    def branch_head(self, repo: str, branch: str) -> str | None: ...
    def list_dir(self, repo: str, ref: str, path: str) -> dict[str, str] | None: ...
    def read_text(self, repo: str, ref: str, path: str) -> str | None: ...
    def changed_paths(self, repo: str, base: str, head: str) -> list[str]: ...
    def commit_files(self, repo: str, base_sha: str, branch: str, files: Mapping[str, str], message: str) -> str: ...
    def find_open_pr(self, repo: str, base: str, branch: str) -> str | None: ...
    def create_pr(self, repo: str, base: str, branch: str, title: str, body: str) -> str: ...


Runner = Callable[[Sequence[str], bytes | None], "subprocess.CompletedProcess[bytes]"]


def _default_runner(args: Sequence[str], stdin: bytes | None) -> "subprocess.CompletedProcess[bytes]":
    return subprocess.run(list(args), input=stdin, capture_output=True, check=False, timeout=60)


class GhCliGitHub:
    """GitHub provider over the already-authenticated `gh` CLI.

    Never accepts, prints, or stores a token; `gh` owns credentials.
    """

    def __init__(self, runner: Runner | None = None):
        self._run = runner or _default_runner

    def _call(self, method: str, path: str, body: Mapping | None = None, *, raw: bool = False) -> bytes:
        args = ["gh", "api", "-X", method, path]
        if raw:
            args[2:2] = ["-H", "Accept: application/vnd.github.raw"]
        stdin = None
        if body is not None:
            args += ["--input", "-"]
            stdin = json.dumps(body).encode("utf-8")
        try:
            proc = self._run(args, stdin)
        except FileNotFoundError as exc:
            raise GitHubUnavailable("GH_CLI_NOT_INSTALLED") from exc
        except (OSError, subprocess.SubprocessError) as exc:
            raise GitHubError(f"GH_CALL_FAILED:{type(exc).__name__}") from exc
        if proc.returncode != 0:
            err = (proc.stderr or b"").decode("utf-8", "replace")
            match = re.search(r"HTTP (\d{3})", err)
            status = int(match.group(1)) if match else None
            raise GitHubError(f"GH_API_{status or 'ERROR'}:{method} {path}", status)
        return proc.stdout or b""

    def _json(self, method: str, path: str, body: Mapping | None = None):
        out = self._call(method, path, body)
        return json.loads(out.decode("utf-8")) if out.strip() else {}

    def discover(self, owner: str) -> Discovery:
        try:
            proc = self._run(["gh", "auth", "status"], None)
        except FileNotFoundError as exc:
            raise GitHubUnavailable("GH_CLI_NOT_INSTALLED") from exc
        except (OSError, subprocess.SubprocessError) as exc:
            raise GitHubUnavailable(f"GH_AUTH_STATUS_FAILED:{type(exc).__name__}") from exc
        if proc.returncode != 0:
            raise GitHubUnavailable("GITHUB_AUTH_UNAVAILABLE")
        owner_l = owner.lower()

        def _refs(items) -> list[RepoRef]:
            return [
                RepoRef(r["full_name"], r.get("default_branch") or "main", bool(r.get("archived")))
                for r in items
                if str(r.get("full_name", "")).split("/")[0].lower() == owner_l
            ]

        # GitHub App installation token (e.g. cloud agents): scope is explicit.
        try:
            repos: list[RepoRef] = []
            selection = "selected"
            page = 1
            while True:
                data = self._json("GET", f"/installation/repositories?per_page=100&page={page}")
                selection = str(data.get("repository_selection") or "selected")
                batch = data.get("repositories") or []
                repos += _refs(batch)
                if len(batch) < 100:
                    break
                page += 1
            scope = "INSTALLATION_ALL" if selection == "all" else "INSTALLATION_SELECTED"
            return Discovery(tuple(sorted(repos, key=lambda r: r.full_name.lower())), scope, scope in SCOPE_COMPLETE)
        except GitHubError as exc:
            if exc.status not in (401, 403, 404):
                raise GitHubUnavailable(f"GITHUB_DISCOVERY_FAILED:{exc}") from exc
        # Authenticated user token: list every repo the user can see for owner.
        try:
            login = str(self._json("GET", "/user").get("login") or "")
        except GitHubError as exc:
            raise GitHubUnavailable(f"GITHUB_IDENTITY_UNAVAILABLE:{exc}") from exc
        if login.lower() == owner_l:
            base = "/user/repos?affiliation=owner&per_page=100"
        else:
            base = f"/orgs/{quote(owner)}/repos?type=all&per_page=100"
        repos = []
        page = 1
        try:
            while True:
                batch = self._json("GET", f"{base}&page={page}")
                repos += _refs(batch)
                if len(batch) < 100:
                    break
                page += 1
        except GitHubError as exc:
            raise GitHubUnavailable(f"GITHUB_OWNER_LISTING_UNAVAILABLE:{exc}") from exc
        return Discovery(tuple(sorted(repos, key=lambda r: r.full_name.lower())), "AUTHENTICATED_USER", True)

    def branch_head(self, repo: str, branch: str) -> str | None:
        try:
            return str(self._json("GET", f"repos/{repo}/git/ref/heads/{branch}")["object"]["sha"])
        except GitHubError as exc:
            if exc.status == 404:
                return None
            raise

    def list_dir(self, repo: str, ref: str, path: str) -> dict[str, str] | None:
        suffix = f"/{quote(path)}" if path else ""
        try:
            data = self._json("GET", f"repos/{repo}/contents{suffix}?ref={quote(ref, safe='')}")
        except GitHubError as exc:
            if exc.status == 404:
                return None
            raise
        if not isinstance(data, list):
            return {"": str(data.get("type", "file"))}
        return {str(item["name"]): str(item["type"]) for item in data}

    def read_text(self, repo: str, ref: str, path: str) -> str | None:
        try:
            out = self._call("GET", f"repos/{repo}/contents/{quote(path)}?ref={quote(ref, safe='')}", raw=True)
        except GitHubError as exc:
            if exc.status == 404:
                return None
            raise
        return out.decode("utf-8")

    def changed_paths(self, repo: str, base: str, head: str) -> list[str]:
        data = self._json("GET", f"repos/{repo}/compare/{quote(base, safe='')}...{quote(head, safe='')}")
        return sorted(str(f["filename"]) for f in data.get("files") or [])

    def commit_files(self, repo: str, base_sha: str, branch: str, files: Mapping[str, str], message: str) -> str:
        base_tree = self._json("GET", f"repos/{repo}/git/commits/{base_sha}")["tree"]["sha"]
        tree = self._json(
            "POST",
            f"repos/{repo}/git/trees",
            {
                "base_tree": base_tree,
                "tree": [
                    {"path": path, "mode": "100644", "type": "blob", "content": files[path]}
                    for path in sorted(files)
                ],
            },
        )["sha"]
        commit = self._json(
            "POST", f"repos/{repo}/git/commits", {"message": message, "tree": tree, "parents": [base_sha]}
        )["sha"]
        if self.branch_head(repo, branch) is None:
            self._json("POST", f"repos/{repo}/git/refs", {"ref": f"refs/heads/{branch}", "sha": commit})
        else:
            self._json("PATCH", f"repos/{repo}/git/refs/heads/{branch}", {"sha": commit, "force": True})
        return str(commit)

    def find_open_pr(self, repo: str, base: str, branch: str) -> str | None:
        owner = repo.split("/")[0]
        data = self._json(
            "GET", f"repos/{repo}/pulls?state=open&base={quote(base)}&head={quote(owner + ':' + branch, safe='')}"
        )
        return str(data[0]["html_url"]) if data else None

    def create_pr(self, repo: str, base: str, branch: str, title: str, body: str) -> str:
        data = self._json("POST", f"repos/{repo}/pulls", {"title": title, "head": branch, "base": base, "body": body})
        return str(data["html_url"])


def _remote_blocked(repo: RepoRef, reason: str, **extra) -> dict:
    return {"repo": repo.full_name, "status": "BLOCKED", "reason": reason, **extra}


def _remote_symlink_guard(gh: GitHubProvider, repo: str, head: str, root: Mapping[str, str]) -> str | None:
    """Mirror local symlink protection on the generated surfaces."""
    if root.get("AGENTS.md") not in (None, "file"):
        return "AGENTS_NOT_REGULAR_FILE"
    if root.get(".p2p") not in (None, "dir"):
        return "P2P_DIR_NOT_REGULAR_DIRECTORY"
    if root.get(".p2p") == "dir":
        p2p = gh.list_dir(repo, head, ".p2p") or {}
        if p2p.get("portable") not in (None, "dir"):
            return "PORTABLE_DIR_NOT_REGULAR_DIRECTORY"
        if p2p.get("portable") == "dir":
            portable = gh.list_dir(repo, head, ".p2p/portable") or {}
            for rel in GENERATED_PATHS[1:]:
                if portable.get(Path(rel).name) not in (None, "file"):
                    return f"GENERATED_PATH_NOT_REGULAR_FILE:{rel}"
    return None


def _sync_pr_body(identity: Mapping[str, str], changed: Sequence[str]) -> str:
    return "\n".join(
        (
            "Generated by `scripts/p2p_sync_managed_projects.py --github-owner` (P2P Issue #264).",
            "",
            "Refreshes ONLY the generated P2P transport surfaces from the canonical P2P source:",
            *[f"- `{path}`" for path in changed],
            "",
            f"CANONICAL_LAW_SHA256={identity['canonical_law_sha256']}",
            f"PORTABLE_EXPERIENCE_SHA256={identity['portable_experience_sha256']}",
            "",
            "Project-specific AGENTS.md content outside the managed P2P block is preserved byte-for-byte.",
            "No product/app file is touched. `SYNC_GENERATED != MERGED_TO_MAIN`: merge follows the",
            "repository's existing Rule 11 / validated-merge governance; this PR is not self-merged.",
        )
    )


def sync_github_repo(
    gh: GitHubProvider, package_root: Path, repo: RepoRef, *, write: bool, identity: Mapping[str, str]
) -> dict:
    """Classify one discovered repo and, in write mode, generate its sync branch/PR."""
    name = repo.full_name
    if name.lower() == CANONICAL_SOURCE_REPO.lower():
        return {"repo": name, "status": "SOURCE", "action": "SKIP_CANONICAL_SOURCE"}
    try:
        head = gh.branch_head(name, repo.default_branch)
        if head is None:
            root = None
        else:
            root = gh.list_dir(name, head, "")
        if not root:
            return {"repo": name, "status": "UNMANAGED", "action": "SKIP_EMPTY_OR_UNREADABLE_ROOT"}
        agents_text = gh.read_text(name, head, "AGENTS.md") if root.get("AGENTS.md") == "file" else None
        p2p_entries = (gh.list_dir(name, head, ".p2p") or {}) if root.get(".p2p") == "dir" else {}
        if root.get(".p2p") not in (None, "dir"):
            p2p_entries = {"portable": "symlink"}  # treat as managed; guard below blocks
        if not _markers_indicate_managed(agents_text, p2p_entries):
            return {"repo": name, "status": "UNMANAGED", "action": "SKIP_UNMANAGED"}
        unsafe = _remote_symlink_guard(gh, name, head, root)
        if unsafe:
            return _remote_blocked(repo, unsafe, managed=True)
        current = {"AGENTS.md": agents_text}
        for rel in GENERATED_PATHS[1:]:
            current[rel] = gh.read_text(name, head, rel)
    except GitHubError as exc:
        return _remote_blocked(repo, f"READ_FAILED:{exc}")

    # Expected bytes: materialize the three surfaces and reuse local projector logic.
    try:
        with tempfile.TemporaryDirectory(prefix="p2p-gh-sync-") as tmp:
            tmp_path = Path(tmp)
            for rel, text in current.items():
                if text is not None:
                    target = tmp_path / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text, encoding="utf-8", newline="")
            check = _check_project(package_root, tmp_path)
            if check["status"] == "BLOCKED":
                return _remote_blocked(repo, check.get("reason", "PROJECTOR_BLOCKED"), managed=True)
            expected_proj, expected_agents, expected_exp = projector.expected_project_state(package_root, tmp_path)
    except (ValueError, OSError, UnicodeError) as exc:
        return _remote_blocked(repo, f"PROJECTOR_FAILED:{exc}", managed=True)

    expected = {"AGENTS.md": expected_agents, GENERATED_PATHS[1]: expected_proj, GENERATED_PATHS[2]: expected_exp}
    changed = sorted(rel for rel in GENERATED_PATHS if current.get(rel) != expected[rel])
    base = {"repo": name, "managed": True, "default_branch": repo.default_branch, "default_head": head}
    if check["status"] == "CURRENT" and not changed:
        return {**base, "status": "CURRENT", "action": "SKIP_CURRENT", "merged_to_main": True}
    result = {**base, "status": "STALE", "stale_paths": changed, "merged_to_main": False}
    if not write:
        return {**result, "action": "CHECK_ONLY"}
    if repo.archived:
        return {**result, "status": "BLOCKED", "reason": "ARCHIVED_READ_ONLY", "action": "SKIP_BLOCKED"}

    try:
        branch_head = gh.branch_head(name, SYNC_BRANCH)
        if branch_head is not None:
            foreign = [p for p in gh.changed_paths(name, head, branch_head) if p not in GENERATED_PATHS]
            if foreign:
                return {**result, "status": "BLOCKED", "reason": f"SYNC_BRANCH_HAS_FOREIGN_CHANGES:{','.join(foreign)}",
                        "action": "SKIP_BLOCKED"}
            already = all(gh.read_text(name, branch_head, rel) == expected[rel] for rel in GENERATED_PATHS)
        else:
            already = False
        wrote = False
        if not already:
            branch_head = gh.commit_files(
                name,
                head,
                SYNC_BRANCH,
                {rel: expected[rel] for rel in changed},
                f"P2P: refresh portable law projection ({identity['canonical_law_sha256'][:12]})",
            )
            wrote = True
        pr_url = gh.find_open_pr(name, repo.default_branch, SYNC_BRANCH)
        if pr_url is None:
            pr_url = gh.create_pr(
                name, repo.default_branch, SYNC_BRANCH,
                "P2P: refresh portable Supreme Law + experience projection",
                _sync_pr_body(identity, changed),
            )
            wrote = True
        # Verify remote reality before claiming anything.
        scope = gh.changed_paths(name, head, branch_head)
        if any(p not in GENERATED_PATHS for p in scope):
            return {**result, "status": "BLOCKED", "reason": f"REMOTE_SCOPE_VIOLATION:{','.join(scope)}",
                    "action": "VERIFY_FAILED"}
        if not all(gh.read_text(name, branch_head, rel) == expected[rel] for rel in GENERATED_PATHS):
            return {**result, "status": "BLOCKED", "reason": "REMOTE_READBACK_MISMATCH", "action": "VERIFY_FAILED"}
    except GitHubError as exc:
        return {**result, "status": "BLOCKED", "reason": f"WRITE_FAILED:{exc}", "action": "WRITE_FAILED"}
    return {
        **result,
        "action": "SYNC_GENERATED" if wrote else "ALREADY_GENERATED",
        "sync_branch": SYNC_BRANCH,
        "sync_head": branch_head,
        "sync_pr": pr_url,
        "remote_changed_paths": scope,
    }


def run_github_sync(gh: GitHubProvider, package_root: Path, owner: str, *, write: bool) -> dict:
    identity = canonical_identity(package_root)
    summary: dict = {
        "mode": "WRITE" if write else "CHECK",
        "transport": "GITHUB",
        "github_owner": owner,
        **identity,
        "sync_generated_is_not_merged_to_main": True,
    }
    try:
        discovery = gh.discover(owner)
    except GitHubUnavailable as exc:
        summary.update(
            github_access="UNAVAILABLE", reason=str(exc), discovery_scope="NONE", discovery_complete=False,
            discovered=0, managed=0, current=0, stale=0, updated=0, blocked=0, blocked_repos=[], changed=0,
            sync_generated=0, merged_to_main_verified=0, repos=[],
            owner_github_connector_status="NOT_PROVEN_BROKEN",
        )
        return summary
    results = [sync_github_repo(gh, package_root, repo, write=write, identity=identity) for repo in discovery.repos]
    managed = [r for r in results if r.get("managed")]
    summary.update(
        github_access="WORKING",
        discovery_scope=discovery.scope,
        discovery_complete=discovery.complete,
        discovered=len(results),
        managed=len(managed),
        current=sum(r["status"] == "CURRENT" for r in results),
        stale=sum(r["status"] == "STALE" for r in results),
        updated=sum(r.get("action") == "SYNC_GENERATED" for r in results),
        blocked=sum(r["status"] == "BLOCKED" for r in results),
        blocked_repos=sorted(r["repo"] for r in results if r["status"] == "BLOCKED"),
        changed=sum(r.get("action") == "SYNC_GENERATED" for r in results),
        sync_generated=sum(r.get("action") in ("SYNC_GENERATED", "ALREADY_GENERATED") for r in results),
        merged_to_main_verified=sum(r["status"] == "CURRENT" for r in results),
        repos=results,
    )
    if not discovery.complete:
        summary["live_broad_rollout"] = "BLOCKED_EXECUTOR_SINGLE_REPO_SCOPE"
    return summary


def _print_github_summary(summary: Mapping) -> None:
    print(
        f"P2P sync (GitHub): OWNER={summary['github_owner']} MODE={summary['mode']} "
        f"GITHUB_ACCESS={summary['github_access']} DISCOVERY_SCOPE={summary['discovery_scope']} "
        f"DISCOVERY_COMPLETE={'YES' if summary['discovery_complete'] else 'NO'}"
    )
    for key in ("discovered", "managed", "current", "stale", "updated", "blocked"):
        print(f"{key.upper()}={summary[key]}")
    print(f"BLOCKED_REPOS={','.join(summary['blocked_repos'])}")
    print(f"CHANGED={summary['changed']}")
    print(f"SYNC_GENERATED={summary['sync_generated']}")
    print(f"MERGED_TO_MAIN_VERIFIED={summary['merged_to_main_verified']}")
    print(f"CANONICAL_LAW_SHA256={summary['canonical_law_sha256']}")
    print(f"PORTABLE_EXPERIENCE_SHA256={summary['portable_experience_sha256']}")
    print("SYNC_GENERATED != MERGED_TO_MAIN")
    if summary.get("reason"):
        print(f"REASON={summary['reason']}")
        print("OWNER_GITHUB_CONNECTOR_STATUS=NOT_PROVEN_BROKEN")
    if summary.get("live_broad_rollout"):
        print(f"LIVE_BROAD_ROLLOUT={summary['live_broad_rollout']}")
    for r in summary["repos"]:
        line = f"  {r['repo']}: {r['status']}"
        if r.get("action"):
            line += f" ({r['action']})"
        if r.get("reason"):
            line += f" - {str(r['reason'])[:160]}"
        if r.get("sync_pr"):
            line += f" -> {r['sync_pr']}"
        print(line)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", type=Path, help="Workspace root containing P2P-managed repos (shallow discovery)")
    parser.add_argument("--project", type=Path, action="append", default=[], help="Explicit project path (repeatable)")
    parser.add_argument(
        "--github-owner",
        help="GitHub owner/org: discover repos via existing `gh` authentication (no token input)",
    )
    parser.add_argument(
        "--package-root",
        type=Path,
        default=REPO_ROOT,
        help="P2P source/release package root (default: repo root)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Read-only check (default)")
    group.add_argument("--write", action="store_true", help="Update stale projections")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary to stdout")
    return parser


def main(argv: list[str] | None = None, *, github: GitHubProvider | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Default to check if neither specified
    mode_check = not args.write
    if args.check and args.write:
        parser.error("--check and --write are mutually exclusive")
    if args.github_owner and (args.workspace or args.project):
        parser.error("--github-owner cannot be combined with --workspace/--project")

    package_root = args.package_root.resolve()
    if not package_root.is_dir():
        print(f"PACKAGE_ROOT_NOT_DIRECTORY:{package_root}", file=sys.stderr)
        return 2

    if args.github_owner:
        try:
            summary = run_github_sync(github or GhCliGitHub(), package_root, args.github_owner, write=not mode_check)
        except (ValueError, OSError, UnicodeError) as exc:
            print(f"CANONICAL_SOURCE_ERROR:{exc}", file=sys.stderr)
            return 2
        _print_github_summary(summary)
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
        if summary["github_access"] != "WORKING":
            return 2
        if summary["blocked"]:
            return 2
        if not summary["discovery_complete"]:
            return 3
        if mode_check and summary["stale"]:
            return 1
        return 0

    projects: list[Path] = []
    if args.workspace:
        try:
            discovered = _discover_workspace(args.workspace)
            projects.extend(discovered)
        except ValueError as exc:
            print(f"WORKSPACE_ERROR:{exc}", file=sys.stderr)
            return 2

    for p in args.project:
        projects.append(p)

    # Deduplicate by resolved path
    seen: set[str] = set()
    uniq_projects: list[Path] = []
    for p in projects:
        try:
            resolved = p.resolve()
            key = str(resolved)
            if key not in seen:
                seen.add(key)
                uniq_projects.append(p)
        except OSError:
            uniq_projects.append(p)

    if not uniq_projects:
        print("NO_PROJECTS_FOUND: provide --project or --workspace with P2P-managed repos", file=sys.stderr)
        return 2

    results: list[dict] = []
    for proj in uniq_projects:
        if mode_check:
            res = _check_project(package_root, proj)
            res["mode"] = "CHECK"
        else:
            res = _write_project(package_root, proj)
            res["mode"] = "WRITE"
        results.append(res)

    current = sum(1 for r in results if r.get("status") == "CURRENT")
    stale = sum(1 for r in results if r.get("status") == "STALE")
    blocked = sum(1 for r in results if r.get("status") == "BLOCKED")
    changed = sum(1 for r in results if r.get("action") == "UPDATED")

    # Human summary
    print(f"P2P sync: {len(results)} projects | CURRENT={current} STALE={stale} BLOCKED={blocked} CHANGED={changed} MODE={'CHECK' if mode_check else 'WRITE'}")
    for r in results:
        proj_name = Path(r.get("resolved") or r.get("project")).name or r.get("project")
        status = r.get("status")
        action = r.get("action", "")
        reason = r.get("reason", "")
        line = f"  {proj_name}: {status}"
        if action:
            line += f" ({action})"
        if reason and status == "BLOCKED":
            line += f" - {reason[:120]}"
        print(line)

    try:
        identity = canonical_identity(package_root)
    except (ValueError, OSError, UnicodeError):
        identity = {"canonical_law_sha256": "UNKNOWN", "portable_experience_sha256": "UNKNOWN"}
    print(f"CANONICAL_LAW_SHA256={identity['canonical_law_sha256']}")
    print(f"PORTABLE_EXPERIENCE_SHA256={identity['portable_experience_sha256']}")

    summary = {
        **identity,
        "mode": "CHECK" if mode_check else "WRITE",
        "total": len(results),
        "current": current,
        "stale": stale,
        "blocked": blocked,
        "changed": changed,
        "projects": results,
        "package_root": str(package_root),
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))

    # Exit code: 0 if all current or all updated, 1 if stale found in check mode, 2 if blocked
    if blocked:
        return 2 if mode_check else 0  # in write mode, blocked is not fatal but report
    if mode_check and stale:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
