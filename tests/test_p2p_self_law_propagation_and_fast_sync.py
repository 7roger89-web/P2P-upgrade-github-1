"""Tests for self-law actor separation propagation and batch sync."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PROJ = REPO_ROOT / "scripts" / "p2p_portable_law_projection.py"
SCRIPT_SYNC = REPO_ROOT / "scripts" / "p2p_sync_managed_projects.py"
INSTALL_SOURCE = REPO_ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"


def _package(tmp_path: Path, law_body: str = "LAW v1") -> Path:
    root = tmp_path / "package"
    notebook = root / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
    notebook.parent.mkdir(parents=True, exist_ok=True)
    notebook.write_text(
        f"# P2P_OPERATIONS_NOTEBOOK\n\n## P2P_SUPREME_OPERATING_LAW_V1\n\n{law_body}\n",
        encoding="utf-8",
    )
    (root / "VERSION").write_text("9.9.9-test\n", encoding="utf-8")

    skills_root = root / ".agents" / "skills"
    for name in ("p2p-scope", "scope-reality-check", "generic-skill"):
        skill_dir = skills_root / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\n---\n\n# {name}\n",
            encoding="utf-8",
        )

    p2p_support = skills_root / "p2p"
    (p2p_support / "references").mkdir(parents=True, exist_ok=True)
    (p2p_support / "scripts").mkdir(parents=True, exist_ok=True)
    for name in ("codex-adaptation.md", "modes.md", "rag-safety.md"):
        (p2p_support / "references" / name).write_text(
            f"# {name}\n", encoding="utf-8"
        )
    (p2p_support / "scripts" / "p2p_state.py").write_text(
        "# portable state helper fixture\n", encoding="utf-8"
    )
    return root


def _run_proj(package: Path, project: Path, *extra: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT_PROJ), str(project), "--package-root", str(package), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def _run_sync(*args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT_SYNC), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_thin_installer_contains_actor_separation():
    text = INSTALL_SOURCE.read_text(encoding="utf-8")
    assert "PARENT_SELF_LAW_PREFLIGHT != EXECUTOR_LAW_PREFLIGHT" in text
    assert "EXECUTOR_P2P_LAW_SOURCE" in text
    assert "CONTROL_TOWER_SELF_LAW_RECEIPT=PASS" in text
    assert "LAW_CONTEXT_BLOCKED" in text
    assert "Remote repo-scoped handoff freshness" in text
    assert "known-stale portable copy" in text
    assert "TARGET_REPO_AUTH != CANONICAL_CROSS_REPO_REACHABILITY" in text
    assert "Do not issue a cross-repository" in text
    assert "P2P_LAW_SOURCE=LOCAL_PORTABLE" in text
    # must remain thin: not copy full law body
    assert "OWNER_OUTCOME_AND_AUTHORITY_ARE_INVARIANTS" not in text
    print("thin installer actor separation: PASS")


def test_portable_agents_block_contains_actor_separation():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import p2p_portable_law_projection as proj

    block = proj._agents_block()
    assert "PARENT_SELF_LAW_PREFLIGHT != EXECUTOR_LAW_PREFLIGHT" in block
    assert "EXECUTOR_P2P_LAW_SOURCE" in block
    assert "CONTROL_TOWER_SELF_LAW_RECEIPT=PASS" in block
    assert "LAW_CONTEXT_BLOCKED" in block
    assert "TASK_BRANCH != LAW_AUTHORITY" in block
    assert "Remote repo-scoped handoff freshness" in block
    assert "known-stale portable copy" in block
    assert "authenticated GitHub connector" in block
    assert "TARGET_REPO_AUTH != CANONICAL_CROSS_REPO_REACHABILITY" in block
    assert "do not probe canonical solely" in block
    assert "P2P_LAW_SOURCE=<actual source>" in block
    assert "### Repo-native required skill handoff" in block
    assert "REQUIRED_SKILLS=<ids>" in block
    assert "p2p-skill-consumption-receipt/1" in block
    print("portable block actor separation: PASS")


def test_projector_idempotent_and_preserves_content(tmp_path: Path):
    package = _package(tmp_path, law_body="LAW v1")
    project = tmp_path / "project"
    project.mkdir()
    (project / "AGENTS.md").write_text("# My Project Specific Rules\n\nCustom content\n", encoding="utf-8")

    r1 = _run_proj(package, project)
    assert r1.returncode == 0, r1.stdout + r1.stderr
    agents1 = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "# My Project Specific Rules" in agents1
    assert "PARENT_SELF_LAW_PREFLIGHT" in agents1

    r2 = _run_proj(package, project)
    assert r2.returncode == 0
    agents2 = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert agents1 == agents2

    # second run no content change
    print("projector idempotent and preserves project-specific: PASS")


def test_batch_check_detects_current_stale(tmp_path: Path):
    package = _package(tmp_path, law_body="LAW v1")
    ws = tmp_path / "ws"
    ws.mkdir()
    proj_a = ws / "projA"
    proj_a.mkdir()
    _run_proj(package, proj_a)

    # update package to v2 -> projA becomes stale
    (package / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md").write_text(
        "# P2P_OPERATIONS_NOTEBOOK\n\n## P2P_SUPREME_OPERATING_LAW_V1\n\nLAW v2\n", encoding="utf-8"
    )
    proj_b = ws / "projB"
    proj_b.mkdir()
    _run_proj(package, proj_b)

    result = _run_sync("--project", str(proj_a), "--project", str(proj_b), "--package-root", str(package), "--check")
    assert "STALE" in result.stdout
    assert "CURRENT" in result.stdout
    print("batch --check detects CURRENT/STALE: PASS")


def test_batch_write_updates_only_stale(tmp_path: Path):
    package = _package(tmp_path, law_body="LAW v1")
    ws = tmp_path / "ws"
    ws.mkdir()
    proj_a = ws / "projA"
    proj_a.mkdir()
    _run_proj(package, proj_a)
    (package / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md").write_text(
        "# P2P_OPERATIONS_NOTEBOOK\n\n## P2P_SUPREME_OPERATING_LAW_V1\n\nLAW v2\n", encoding="utf-8"
    )
    proj_b = ws / "projB"
    proj_b.mkdir()
    _run_proj(package, proj_b)

    result = _run_sync("--project", str(proj_a), "--project", str(proj_b), "--package-root", str(package), "--write")
    assert "CHANGED=1" in result.stdout
    assert result.returncode == 0

    # second write no-op
    result2 = _run_sync("--project", str(proj_a), "--project", str(proj_b), "--package-root", str(package), "--write")
    assert "CHANGED=0" in result2.stdout
    print("batch --write updates only stale and second is no-op: PASS")


def test_workspace_write_requires_full_fleet_opt_in(tmp_path: Path):
    package = _package(tmp_path, law_body="LAW v1")
    ws = tmp_path / "ws"
    ws.mkdir()
    project = ws / "projA"
    project.mkdir()
    assert _run_proj(package, project).returncode == 0

    (package / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md").write_text(
        "# P2P_OPERATIONS_NOTEBOOK\n\n## P2P_SUPREME_OPERATING_LAW_V1\n\nLAW v2\n",
        encoding="utf-8",
    )

    blocked = _run_sync(
        "--workspace",
        str(ws),
        "--package-root",
        str(package),
        "--write",
    )
    assert blocked.returncode == 2
    assert "FULL_FLEET_WRITE_REQUIRES_EXPLICIT_OPT_IN" in blocked.stderr

    still_stale = _run_sync(
        "--project",
        str(project),
        "--package-root",
        str(package),
        "--check",
    )
    assert still_stale.returncode == 1
    assert "STALE" in still_stale.stdout

    allowed = _run_sync(
        "--workspace",
        str(ws),
        "--package-root",
        str(package),
        "--write",
        "--full-fleet",
    )
    assert allowed.returncode == 0
    assert "CHANGED=1" in allowed.stdout
    print("workspace mutation requires explicit full-fleet opt-in: PASS")



def test_batch_check_and_write_track_projected_skill_drift(tmp_path: Path):
    package = _package(tmp_path, law_body="LAW v1")
    project = tmp_path / "skill-project"
    project.mkdir()
    assert _run_proj(package, project).returncode == 0

    source_skill = package / ".agents" / "skills" / "p2p-scope" / "SKILL.md"
    source_skill.write_text(
        source_skill.read_text(encoding="utf-8") + "\nSOURCE v2\n",
        encoding="utf-8",
    )

    check = _run_sync(
        "--project",
        str(project),
        "--package-root",
        str(package),
        "--check",
    )
    assert check.returncode == 1
    assert "STALE" in check.stdout

    write = _run_sync(
        "--project",
        str(project),
        "--package-root",
        str(package),
        "--write",
    )
    assert write.returncode == 0
    assert "CHANGED=1" in write.stdout
    projected = project / ".agents" / "skills" / "p2p-scope" / "SKILL.md"
    assert projected.read_text(encoding="utf-8") == source_skill.read_text(
        encoding="utf-8"
    )

    second = _run_sync(
        "--project",
        str(project),
        "--package-root",
        str(package),
        "--write",
    )
    assert "CHANGED=0" in second.stdout
    print("batch skill drift check/write/idempotence: PASS")


def test_batch_write_migrates_legacy_preflight(tmp_path: Path):
    package = _package(tmp_path, law_body="LAW v1")
    project = tmp_path / "legacy-project"
    project.mkdir()
    legacy = """# AGENTS.md

## P2P law preflight

1. Prefer canonical:
   `7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`
2. Portable:
   `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`
3. `P2P_LAW_SOURCE=CANONICAL_AUTHENTICATED|LOCAL_PORTABLE|LAW_CONTEXT_BLOCKED`

## Repository role

Project-specific role remains.
"""
    (project / "AGENTS.md").write_text(legacy, encoding="utf-8")
    _run_proj(package, project)

    # Re-introduce the legacy section to simulate an older managed repository.
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    managed_start = agents.index("<!-- BEGIN P2P PORTABLE LAW -->")
    (project / "AGENTS.md").write_text(
        legacy.rstrip() + "\n\n" + agents[managed_start:],
        encoding="utf-8",
    )

    result = _run_sync("--project", str(project), "--package-root", str(package), "--write")
    assert result.returncode == 0
    assert "CHANGED=1" in result.stdout
    migrated = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## P2P law preflight" not in migrated
    assert migrated.count("<!-- BEGIN P2P PORTABLE LAW -->") == 1
    assert "Project-specific role remains." in migrated
    print("batch legacy-preflight migration: PASS")

def test_dirty_and_unsafe_blocked(tmp_path: Path):
    package = _package(tmp_path)
    ws = tmp_path / "ws"
    ws.mkdir()

    # dirty repo
    proj_c = ws / "projC"
    proj_c.mkdir()
    _run_proj(package, proj_c)
    subprocess.run(["git", "init", "-b", "main"], cwd=str(proj_c), capture_output=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=str(proj_c), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(proj_c), capture_output=True)
    subprocess.run(["git", "add", "."], cwd=str(proj_c), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(proj_c), capture_output=True)
    (proj_c / "AGENTS.md").write_text((proj_c / "AGENTS.md").read_text() + "\nDIRTY\n", encoding="utf-8")

    result = _run_sync("--project", str(proj_c), "--package-root", str(package), "--write")
    assert "BLOCKED" in result.stdout
    print("dirty BLOCKED: PASS")

    # dirty projected skill
    subprocess.run(
        ["git", "-C", str(proj_c), "checkout", "--", "AGENTS.md"],
        capture_output=True,
    )
    projected_skill = proj_c / ".agents" / "skills" / "p2p-scope" / "SKILL.md"
    projected_skill.write_text(
        projected_skill.read_text(encoding="utf-8") + "\nDIRTY SKILL\n",
        encoding="utf-8",
    )
    result_skill = _run_sync(
        "--project", str(proj_c), "--package-root", str(package), "--write"
    )
    assert "BLOCKED" in result_skill.stdout
    print("dirty projected skill BLOCKED: PASS")

    # symlink unsafe
    proj_d = ws / "projD"
    proj_d.mkdir()
    (proj_d / ".p2p").mkdir(parents=True)
    (proj_d / ".p2p" / "portable").symlink_to("/tmp")

    result2 = _run_sync("--project", str(proj_d), "--package-root", str(package), "--check")
    assert "BLOCKED" in result2.stdout
    print("symlink BLOCKED: PASS")


def test_no_new_authority_or_registry():
    # Ensure batch sync does not create new authority files
    sync_text = SCRIPT_SYNC.read_text(encoding="utf-8")
    assert "P2P_PORTABLE_LAW_PROJECTION=YES" not in sync_text or "project_law" in sync_text  # reuses projector
    assert "PACKAGED_LAW_SOURCE" not in sync_text
    assert "registry" not in sync_text.lower() or "not a new registry" in sync_text.lower()
    # Check that it reuses expected_project_state and project_law
    assert "expected_project_state" in sync_text
    assert "project_law" in sync_text
    print("no new authority/registry: PASS")


if __name__ == "__main__":
    import pathlib

    # Run with pytest tmp_path simulation
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_thin_installer_contains_actor_separation()
        test_portable_agents_block_contains_actor_separation()
        test_projector_idempotent_and_preserves_content(tmp_path / "t1")
        test_batch_check_detects_current_stale(tmp_path / "t2")
        test_batch_write_updates_only_stale(tmp_path / "t3")
        test_workspace_write_requires_full_fleet_opt_in(tmp_path / "t3fleet")
        test_batch_check_and_write_track_projected_skill_drift(tmp_path / "t3a")
        test_batch_write_migrates_legacy_preflight(tmp_path / "t3b")
        test_dirty_and_unsafe_blocked(tmp_path / "t4")
        test_no_new_authority_or_registry()
    print("ALL TESTS PASS")
