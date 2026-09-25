"""Issue #264 slice 2 — GitHub-first one-command managed-project sync.

Deterministic tests over a fake GitHub provider boundary (no network), plus the
inline SUPREME_LAW_CAPSULE fallback consumption proof.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "scripts"), str(REPO_ROOT / ".p2p" / "system"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import p2p_portable_law_projection as projector  # noqa: E402
import p2p_sync_managed_projects as sync  # noqa: E402

SCRIPT_SYNC = REPO_ROOT / "scripts" / "p2p_sync_managed_projects.py"
OWNER = "acme"
CUSTOM_AGENTS = "# Project rules\n\nProject-specific rule X must survive.\n"
PARALLEL = "PARALLEL_WORKSTREAM_EXECUTION_BY_DEFAULT"
ONE_ACTION = "ONE_ACTION_NOW_FOR_BEGINNER != ONE_WORKSTREAM_TOTAL"


# ---------------------------------------------------------------------------
# Fake GitHub provider (same interface as GhCliGitHub)
# ---------------------------------------------------------------------------


class FakeGitHub:
    def __init__(self, repos: dict, *, scope: str = "AUTHENTICATED_USER", unavailable: bool = False):
        self.snapshots: dict[str, dict[str, str]] = {}
        self.symlinks: dict[str, set[str]] = {}
        self.refs: dict[str, dict[str, str]] = {}
        self.meta: dict[str, sync.RepoRef] = {}
        self.prs: dict[str, list[dict]] = {}
        self.fail_reads: set[str] = set()
        self.writes: list[tuple] = []
        self.scope = scope
        self.unavailable = unavailable
        for name, spec in repos.items():
            self.meta[name] = sync.RepoRef(name, "main", spec.get("archived", False))
            self.symlinks[name] = set(spec.get("symlinks", ()))
            self.refs[name] = {"main": self._snap(spec["files"])}
            self.prs[name] = []

    def _snap(self, files: dict[str, str]) -> str:
        blob = json.dumps(sorted(files.items())).encode("utf-8")
        sha = hashlib.sha1(blob).hexdigest()
        self.snapshots[sha] = dict(files)
        return sha

    def _guard(self, repo: str) -> None:
        if repo in self.fail_reads:
            raise sync.GitHubError("GH_API_403:fake", 403)

    # provider interface -------------------------------------------------
    def discover(self, owner: str) -> sync.Discovery:
        if self.unavailable:
            raise sync.GitHubUnavailable("GITHUB_AUTH_UNAVAILABLE")
        repos = tuple(sorted(self.meta.values(), key=lambda r: r.full_name.lower()))
        return sync.Discovery(repos, self.scope, self.scope in sync.SCOPE_COMPLETE)

    def branch_head(self, repo, branch):
        self._guard(repo)
        return self.refs[repo].get(branch)

    def list_dir(self, repo, ref, path):
        self._guard(repo)
        files = self.snapshots[ref]
        prefix = f"{path}/" if path else ""
        out: dict[str, str] = {}
        for full in files:
            if not full.startswith(prefix):
                continue
            rest = full[len(prefix):]
            head, _, tail = rest.partition("/")
            candidate = prefix + head
            if candidate in self.symlinks[repo]:
                out[head] = "symlink"
            else:
                out[head] = "dir" if tail else "file"
        return out or None

    def read_text(self, repo, ref, path):
        self._guard(repo)
        return self.snapshots[ref].get(path)

    def changed_paths(self, repo, base, head):
        a, b = self.snapshots[base], self.snapshots[head]
        return sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))

    def commit_files(self, repo, base_sha, branch, files, message):
        self.writes.append(("commit", repo, branch, tuple(sorted(files))))
        new = dict(self.snapshots[base_sha])
        new.update(files)
        sha = self._snap(new)
        self.refs[repo][branch] = sha
        return sha

    def find_open_pr(self, repo, base, branch):
        for pr in self.prs[repo]:
            if pr["base"] == base and pr["head"] == branch and pr["open"]:
                return pr["url"]
        return None

    def create_pr(self, repo, base, branch, title, body):
        self.writes.append(("pr", repo, branch))
        url = f"https://github.test/{repo}/pull/{len(self.prs[repo]) + 1}"
        self.prs[repo].append({"base": base, "head": branch, "url": url, "open": True, "body": body})
        return url

    # helpers ---------------------------------------------------------------
    def merge_sync(self, repo: str) -> None:
        self.refs[repo]["main"] = self.refs[repo][sync.SYNC_BRANCH]

    def main_files(self, repo: str) -> dict[str, str]:
        return self.snapshots[self.refs[repo]["main"]]

    def branch_files(self, repo: str, branch: str) -> dict[str, str]:
        return self.snapshots[self.refs[repo][branch]]


def _expected(agents: str | None) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        if agents is not None:
            (root / "AGENTS.md").write_text(agents, encoding="utf-8")
        proj, ag, exp = projector.expected_project_state(REPO_ROOT, root)
    return {"AGENTS.md": ag, sync.GENERATED_PATHS[1]: proj, sync.GENERATED_PATHS[2]: exp}


def _fixture_repos() -> dict:
    current_files = {**_expected(CUSTOM_AGENTS), "src/app.py": "print('current')\n"}
    stale_agents = CUSTOM_AGENTS + "\n<!-- BEGIN P2P CODEX -->\nold installed block\n<!-- END P2P CODEX -->\n"
    return {
        f"{OWNER}/alpha-stale": {"files": {"AGENTS.md": stale_agents, "src/app.py": "print('alpha')\n"}},
        f"{OWNER}/beta-current": {"files": current_files},
        f"{OWNER}/gamma-unrelated": {"files": {"README.md": "# not p2p\n", "AGENTS.md": "# plain agents\n"}},
        f"{OWNER}/delta-installed": {"files": {".p2p/system/marker.txt": "x\n", "main.go": "package main\n"}},
        sync.CANONICAL_SOURCE_REPO: {"files": {"AGENTS.md": "<!-- BEGIN P2P CODEX -->\n", ".p2p/system/a": "1"}},
    }


def _run(fake: FakeGitHub, *, write: bool) -> dict:
    return sync.run_github_sync(fake, REPO_ROOT, OWNER, write=write)


def _by_repo(summary: dict) -> dict[str, dict]:
    return {r["repo"]: r for r in summary["repos"]}


# ---------------------------------------------------------------------------
# Discovery / classification
# ---------------------------------------------------------------------------


def test_discovery_selects_only_p2p_managed_repos_and_skips_source():
    fake = FakeGitHub(_fixture_repos())
    summary = _run(fake, write=False)
    repos = _by_repo(summary)
    assert summary["discovered"] == 5
    assert summary["managed"] == 3
    assert (summary["current"], summary["stale"], summary["blocked"], summary["updated"]) == (1, 2, 0, 0)
    assert repos[f"{OWNER}/gamma-unrelated"]["status"] == "UNMANAGED"
    assert repos[sync.CANONICAL_SOURCE_REPO]["status"] == "SOURCE"
    assert repos[f"{OWNER}/delta-installed"]["status"] == "STALE"  # .p2p/system marker
    assert repos[f"{OWNER}/beta-current"]["status"] == "CURRENT"
    assert fake.writes == []  # --check is read-only
    assert summary["discovery_complete"] is True


def test_shared_marker_semantics_local_and_remote():
    assert sync._markers_indicate_managed("<!-- BEGIN P2P CODEX -->", [])
    assert sync._markers_indicate_managed(projector.AGENTS_BEGIN, [])
    assert sync._markers_indicate_managed(None, ["portable"])
    assert sync._markers_indicate_managed(None, ["system"])
    assert not sync._markers_indicate_managed("# plain", ["evals", "vendor"])
    src = SCRIPT_SYNC.read_text(encoding="utf-8")
    # both the local and the GitHub path route through the same predicate
    assert src.count("_markers_indicate_managed(") >= 3


# ---------------------------------------------------------------------------
# Write mode: exact generated scope, preservation, SYNC_GENERATED != MERGED
# ---------------------------------------------------------------------------


def test_write_generates_sync_pr_with_exact_scope_and_preserves_content():
    fake = FakeGitHub(_fixture_repos())
    main_before = {name: dict(fake.main_files(name)) for name in fake.meta}
    summary = _run(fake, write=True)
    repos = _by_repo(summary)

    alpha = repos[f"{OWNER}/alpha-stale"]
    assert alpha["status"] == "STALE" and alpha["action"] == "SYNC_GENERATED"
    assert alpha["merged_to_main"] is False
    assert alpha["sync_branch"] == sync.SYNC_BRANCH
    assert set(alpha["remote_changed_paths"]) <= set(sync.GENERATED_PATHS)
    assert set(alpha["remote_changed_paths"]) == set(sync.GENERATED_PATHS)  # law + experience + AGENTS together

    branch = fake.branch_files(f"{OWNER}/alpha-stale", sync.SYNC_BRANCH)
    assert CUSTOM_AGENTS.strip() in branch["AGENTS.md"]
    assert "old installed block" in branch["AGENTS.md"]  # unrelated block preserved verbatim
    assert branch["AGENTS.md"].count(projector.AGENTS_BEGIN) == 1
    assert PARALLEL in branch["AGENTS.md"]
    assert branch["src/app.py"] == "print('alpha')\n"  # product file untouched
    assert f"### {PARALLEL}" in branch[sync.GENERATED_PATHS[1]]
    assert json.loads(branch[sync.GENERATED_PATHS[2]])["schema"] == projector.EXPERIENCE_CAPSULE_SCHEMA

    # every commit only ever carried generated paths
    for kind, *rest in fake.writes:
        if kind == "commit":
            assert set(rest[2]) <= set(sync.GENERATED_PATHS)
    # CURRENT / UNMANAGED / SOURCE never written; default branches never mutated
    written = {w[1] for w in fake.writes}
    assert written == {f"{OWNER}/alpha-stale", f"{OWNER}/delta-installed"}
    for name in fake.meta:
        assert fake.main_files(name) == main_before[name]
    # SYNC_GENERATED != MERGED_TO_MAIN
    assert summary["updated"] == 2 and summary["sync_generated"] == 2
    assert summary["merged_to_main_verified"] == 1  # only the genuinely CURRENT repo
    assert summary["stale"] == 2
    pr_body = fake.prs[f"{OWNER}/alpha-stale"][0]["body"]
    assert "SYNC_GENERATED != MERGED_TO_MAIN" in pr_body
    assert summary["canonical_law_sha256"] in pr_body


def test_second_identical_run_is_zero_change_then_merge_makes_current():
    fake = FakeGitHub(_fixture_repos())
    _run(fake, write=True)
    writes_after_first = list(fake.writes)
    second = _run(fake, write=True)
    assert second["changed"] == 0 and second["updated"] == 0
    assert fake.writes == writes_after_first
    assert _by_repo(second)[f"{OWNER}/alpha-stale"]["action"] == "ALREADY_GENERATED"
    assert second["sync_generated"] == 2 and second["merged_to_main_verified"] == 1

    fake.merge_sync(f"{OWNER}/alpha-stale")
    third = _run(fake, write=True)
    assert _by_repo(third)[f"{OWNER}/alpha-stale"]["status"] == "CURRENT"
    assert third["merged_to_main_verified"] == 2 and third["changed"] == 0


def test_counts_and_output_are_deterministic():
    a = _run(FakeGitHub(_fixture_repos()), write=True)
    b = _run(FakeGitHub(_fixture_repos()), write=True)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert [r["repo"] for r in a["repos"]] == sorted((r["repo"] for r in a["repos"]), key=str.lower)


# ---------------------------------------------------------------------------
# BLOCKED stays visible; fail closed
# ---------------------------------------------------------------------------


def test_blocked_repos_remain_visible():
    repos = _fixture_repos()
    repos[f"{OWNER}/eps-symlink"] = {
        "files": {"AGENTS.md": "<!-- BEGIN P2P CODEX -->\n", ".p2p/portable/P2P-OPERATIONS-NOTEBOOK.md": "x"},
        "symlinks": {".p2p/portable"},
    }
    repos[f"{OWNER}/zeta-archived"] = {"files": {".p2p/system/m": "1"}, "archived": True}
    repos[f"{OWNER}/eta-unreadable"] = {"files": {"AGENTS.md": "<!-- BEGIN P2P CODEX -->\n"}}
    repos[f"{OWNER}/theta-foreign"] = {"files": {".p2p/system/m": "1", "app.js": "1"}}
    fake = FakeGitHub(repos)
    fake.fail_reads.add(f"{OWNER}/eta-unreadable")
    # someone pushed a product change onto the deterministic sync branch
    theta = f"{OWNER}/theta-foreign"
    fake.refs[theta][sync.SYNC_BRANCH] = fake._snap({".p2p/system/m": "1", "app.js": "HACK"})

    summary = _run(fake, write=True)
    by = _by_repo(summary)
    assert summary["blocked_repos"] == sorted(
        [f"{OWNER}/eps-symlink", f"{OWNER}/eta-unreadable", f"{OWNER}/theta-foreign", f"{OWNER}/zeta-archived"]
    )
    assert summary["blocked"] == 4
    assert by[f"{OWNER}/eps-symlink"]["reason"] == "PORTABLE_DIR_NOT_REGULAR_DIRECTORY"
    assert by[f"{OWNER}/zeta-archived"]["reason"] == "ARCHIVED_READ_ONLY"
    assert by[f"{OWNER}/eta-unreadable"]["reason"].startswith("READ_FAILED")
    assert by[theta]["reason"].startswith("SYNC_BRANCH_HAS_FOREIGN_CHANGES:app.js")
    assert fake.branch_files(theta, sync.SYNC_BRANCH)["app.js"] == "HACK"  # never overwritten
    blocked_names = set(summary["blocked_repos"])
    assert not any(w[1] in blocked_names for w in fake.writes)

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = sync.main(["--github-owner", OWNER, "--write"], github=fake)
    assert code == 2
    assert f"BLOCKED_REPOS={','.join(summary['blocked_repos'])}" in out.getvalue()


def test_auth_unavailable_fails_closed_without_false_update():
    fake = FakeGitHub(_fixture_repos(), unavailable=True)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = sync.main(["--github-owner", OWNER, "--write"], github=fake)
    text = out.getvalue()
    assert code == 2
    assert "GITHUB_ACCESS=UNAVAILABLE" in text
    assert "UPDATED=0" in text and "CHANGED=0" in text
    assert "OWNER_GITHUB_CONNECTOR_STATUS=NOT_PROVEN_BROKEN" in text
    assert fake.writes == []


def test_gh_cli_missing_is_unavailable_not_success():
    def runner(args, stdin):
        raise FileNotFoundError("gh")

    summary = sync.run_github_sync(sync.GhCliGitHub(runner), REPO_ROOT, OWNER, write=True)
    assert summary["github_access"] == "UNAVAILABLE"
    assert summary["reason"] == "GH_CLI_NOT_INSTALLED"
    assert summary["updated"] == 0


def test_selected_repo_scope_never_masquerades_as_full_owner_discovery():
    fake = FakeGitHub(_fixture_repos(), scope="INSTALLATION_SELECTED")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = sync.main(["--github-owner", OWNER, "--check"], github=fake)
    text = out.getvalue()
    assert code == 3
    assert "DISCOVERY_SCOPE=INSTALLATION_SELECTED" in text
    assert "DISCOVERY_COMPLETE=NO" in text
    assert "LIVE_BROAD_ROLLOUT=BLOCKED_EXECUTOR_SINGLE_REPO_SCOPE" in text


def test_gh_installation_selected_scope_is_incomplete_and_user_scope_complete():
    calls: list[list[str]] = []

    def make_runner(install_ok: bool):
        def runner(args, stdin):
            calls.append(list(args))
            path = args[-1]
            if args[:3] == ["gh", "auth", "status"]:
                return subprocess.CompletedProcess(args, 0, b"", b"")
            if "/installation/repositories" in path:
                if install_ok:
                    body = {"repository_selection": "selected", "repositories": [
                        {"full_name": f"{OWNER}/one", "default_branch": "main", "archived": False},
                        {"full_name": "other/foreign", "default_branch": "main"}]}
                    return subprocess.CompletedProcess(args, 0, json.dumps(body).encode(), b"")
                return subprocess.CompletedProcess(args, 1, b"{}", b"gh: Forbidden (HTTP 403)")
            if path == "/user":
                return subprocess.CompletedProcess(args, 0, json.dumps({"login": OWNER}).encode(), b"")
            if path.startswith("/user/repos"):
                body = [{"full_name": f"{OWNER}/b"}, {"full_name": f"{OWNER}/a", "default_branch": "dev"}]
                return subprocess.CompletedProcess(args, 0, json.dumps(body).encode(), b"")
            raise AssertionError(args)
        return runner

    d1 = sync.GhCliGitHub(make_runner(True)).discover(OWNER)
    assert (d1.scope, d1.complete) == ("INSTALLATION_SELECTED", False)
    assert [r.full_name for r in d1.repos] == [f"{OWNER}/one"]  # other owners filtered
    d2 = sync.GhCliGitHub(make_runner(False)).discover(OWNER)
    assert (d2.scope, d2.complete) == ("AUTHENTICATED_USER", True)
    assert [(r.full_name, r.default_branch) for r in d2.repos] == [(f"{OWNER}/a", "dev"), (f"{OWNER}/b", "main")]
    flat = " ".join(" ".join(c) for c in calls).lower()
    assert "token" not in flat and "authorization" not in flat


# ---------------------------------------------------------------------------
# No token input; exact commit construction; no infrastructure added
# ---------------------------------------------------------------------------


def test_no_token_or_secret_cli_parameter():
    options = [opt for action in sync.build_parser()._actions for opt in action.option_strings]
    assert "--github-owner" in options
    for opt in options:
        assert not re.search(r"token|pat\b|secret|password|credential|auth", opt, re.I), opt
    help_text = subprocess.run(
        [sys.executable, str(SCRIPT_SYNC), "--help"], capture_output=True, text=True, check=False
    ).stdout
    assert "--github-owner" in help_text and "--token" not in help_text


def test_gh_commit_files_builds_single_commit_with_only_given_paths():
    requests: list[tuple[list[str], dict | None]] = []

    def runner(args, stdin):
        body = json.loads(stdin) if stdin else None
        requests.append((list(args), body))
        path = args[4]
        method = args[3]
        if path.endswith("/git/commits/base123"):
            out = {"tree": {"sha": "tree0"}}
        elif path.endswith("/git/trees"):
            out = {"sha": "tree1"}
        elif path.endswith("/git/commits") and method == "POST":
            out = {"sha": "commit1"}
        elif "/git/ref/heads/" in path:
            return subprocess.CompletedProcess(args, 1, b"{}", b"gh: Not Found (HTTP 404)")
        elif path.endswith("/git/refs"):
            out = {"ref": "ok"}
        else:
            raise AssertionError(args)
        return subprocess.CompletedProcess(args, 0, json.dumps(out).encode(), b"")

    files = {"AGENTS.md": "a\n", ".p2p/portable/P2P-EXPERIENCE-CAPSULE.json": "{}\n"}
    sha = sync.GhCliGitHub(runner).commit_files(f"{OWNER}/r", "base123", sync.SYNC_BRANCH, files, "msg")
    assert sha == "commit1"
    tree_body = next(b for a, b in requests if a[4].endswith("/git/trees"))
    assert tree_body["base_tree"] == "tree0"
    assert sorted(e["path"] for e in tree_body["tree"]) == sorted(files)
    commit_body = next(b for a, b in requests if a[4].endswith("/git/commits") and a[3] == "POST")
    assert commit_body["parents"] == ["base123"]
    ref_body = next(b for a, b in requests if a[4].endswith("/git/refs"))
    assert ref_body == {"ref": f"refs/heads/{sync.SYNC_BRANCH}", "sha": "commit1"}
    assert all(a[:2] == ["gh", "api"] for a, _ in requests)
    # never targets the default branch ref
    assert not any("heads/main" in a[4] for a, _ in requests)


def test_no_daemon_watcher_registry_database_or_github_action():
    src = SCRIPT_SYNC.read_text(encoding="utf-8")
    for forbidden in ("import threading", "import sched", "import sqlite3", "watchdog", "import asyncio",
                      "time.sleep", "import time", "import schedule", "while True:\n        time"):
        assert forbidden not in src, forbidden
    assert "--token" not in src and "GH_TOKEN" not in src and "GITHUB_TOKEN" not in src
    workflows = REPO_ROOT / ".github" / "workflows"
    if workflows.is_dir():
        for wf in workflows.iterdir():
            if wf.is_file():
                assert "p2p_sync_managed_projects" not in wf.read_text(encoding="utf-8", errors="replace"), wf
    assert not list(REPO_ROOT.glob("**/*managed*registry*"))


# ---------------------------------------------------------------------------
# Local --workspace compatibility (existing behaviour + identity lines)
# ---------------------------------------------------------------------------


def test_local_workspace_mode_still_works_with_identity_output(tmp_path: Path):
    ws = tmp_path / "ws"
    proj = ws / "proj"
    proj.mkdir(parents=True)
    (proj / "AGENTS.md").write_text(CUSTOM_AGENTS + "<!-- BEGIN P2P CODEX -->\nx\n<!-- END P2P CODEX -->\n",
                                    encoding="utf-8")
    run = lambda *a: subprocess.run(  # noqa: E731
        [sys.executable, str(SCRIPT_SYNC), "--workspace", str(ws), "--package-root", str(REPO_ROOT), *a],
        capture_output=True, text=True, check=False, timeout=120,
    )
    first = run("--write")
    assert first.returncode == 0 and "CHANGED=1" in first.stdout
    ident = sync.canonical_identity(REPO_ROOT)
    assert f"CANONICAL_LAW_SHA256={ident['canonical_law_sha256']}" in first.stdout
    assert f"PORTABLE_EXPERIENCE_SHA256={ident['portable_experience_sha256']}" in first.stdout
    assert "Project-specific rule X must survive." in (proj / "AGENTS.md").read_text(encoding="utf-8")
    second = run("--write")
    assert "CHANGED=0" in second.stdout and "CURRENT=1" in second.stdout


def test_github_owner_cannot_mix_with_local_targets(tmp_path: Path):
    with pytest.raises(SystemExit):
        sync.main(["--github-owner", OWNER, "--workspace", str(tmp_path)])


# ---------------------------------------------------------------------------
# Inline SUPREME_LAW_CAPSULE fallback carries the invariant; still nine laws
# ---------------------------------------------------------------------------


def test_inline_only_fallback_prompt_carries_parallel_invariant_with_nine_laws():
    import p2p_control_tower as control_tower
    from p2p_capabilities.control_tower_handoff import SessionBinding, build_execution_prompt

    with tempfile.TemporaryDirectory() as project_dir, tempfile.TemporaryDirectory() as package_dir:
        project = Path(project_dir)
        receipt = control_tower._establish_control_tower_law_context(project, package_root=Path(package_dir))
        assert receipt["source_type"] == "INLINE_SUPREME_LAW_CAPSULE"  # canonical/installed/portable absent
        binding = SessionBinding(
            session_id="session-inline-only-issue-264-0123456789ab", host="ARENA", goal_id="G-264", goal="Bounded task"
        )
        contextual = control_tower._contextual_task_for_session(
            project, binding, "Implement one bounded change.", law_receipt=receipt
        )
        prompt = build_execution_prompt(binding, contextual)

    assert PARALLEL in prompt
    assert ONE_ACTION in prompt
    capsule = control_tower._handoff.SUPREME_LAW_CAPSULE
    lines = [line for line in capsule.splitlines() if line.strip()]
    assert len(lines) == 9  # exactly nine numbered canonical laws, no tenth entry
    for index, identifier in enumerate(control_tower._CANONICAL_LAW_IDENTIFIERS, start=1):
        assert lines[index - 1].startswith(f"{index}. {identifier}")
    law5 = lines[4]
    assert PARALLEL in law5 and ONE_ACTION in law5
    assert "checkpoint" in law5 and "stop once proven" in law5  # continuity semantics kept
    assert capsule.count(PARALLEL) == 1
