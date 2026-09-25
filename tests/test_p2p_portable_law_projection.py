from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "p2p_portable_law_projection.py"
CANONICAL_NOTEBOOK = REPO_ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
PACKAGE_RELEASE = REPO_ROOT / "scripts" / "package_release.py"


def _package(tmp_path: Path) -> Path:
    root = tmp_path / "package"
    notebook = root / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
    notebook.parent.mkdir(parents=True)
    notebook.write_text(
        "# P2P_OPERATIONS_NOTEBOOK\n\n## P2P_SUPREME_OPERATING_LAW_V1\n\nLAW\n",
        encoding="utf-8",
    )
    (root / "VERSION").write_text("9.9.9-test\n", encoding="utf-8")
    return root


def _run(package: Path, project: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(project),
            "--package-root",
            str(package),
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_writes_git_trackable_portable_projection_without_runtime_install(tmp_path: Path) -> None:
    package = _package(tmp_path)
    project = tmp_path / "project"
    project.mkdir()

    result = _run(package, project)

    assert result.returncode == 0, result.stderr + result.stdout
    projected = project / ".p2p" / "portable" / "P2P-OPERATIONS-NOTEBOOK.md"
    assert projected.is_file()
    text = projected.read_text(encoding="utf-8")
    assert "P2P_PORTABLE_LAW_PROJECTION=YES" in text
    assert "P2P_SUPREME_OPERATING_LAW_V1" in text
    assert "PROJECTION_DO_NOT_EDIT=YES" in text
    assert not (project / ".p2p" / "system").exists()

    capsule = project / ".p2p" / "portable" / "P2P-EXPERIENCE-CAPSULE.json"
    assert capsule.is_file()
    capsule_text = capsule.read_text(encoding="utf-8")
    assert "p2p-portable-experience-capsule/1" in capsule_text
    assert "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE" in capsule_text

    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "<!-- BEGIN P2P PORTABLE LAW -->" in agents
    assert ".p2p/portable/P2P-OPERATIONS-NOTEBOOK.md" in agents
    assert "TASK_BRANCH != LAW_AUTHORITY" in agents
    assert "LAW_CHECK=PASS" in agents
    assert "EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE" in agents
    assert "LEARNING_RECONCILIATION=" in agents
    assert "### Native long-running goal bridge" in agents
    assert ".p2p/system/p2p_capabilities/native_goal_bridge.py" in agents
    assert ".p2p/system/p2p_capabilities/native_goal_activation.py" in agents
    assert "ACTIVATE_NATIVE_GOAL" in agents
    assert "NORMAL_P2P_PATH" in agents
    assert "Goal status must be `APPROVED` or `IN_PROGRESS`" in agents
    assert ".p2p/system/p2p_capabilities/worktree_evidence.py" in agents
    assert "committed-after-baseline" in agents
    assert "executor self-report are never P2P acceptance authority" in agents
    assert "Never introduce a fixed retry-count hard stop" in agents
    assert "do not assume Codex CLI has Claude Code's evaluator semantics" in agents


def test_projection_is_byte_idempotent_for_empty_project(tmp_path: Path) -> None:
    package = _package(tmp_path)
    project = tmp_path / "project"
    project.mkdir()

    first = _run(package, project)
    assert first.returncode == 0
    first_agents = (project / "AGENTS.md").read_bytes()
    first_projection = (project / ".p2p" / "portable" / "P2P-OPERATIONS-NOTEBOOK.md").read_bytes()
    first_capsule = (project / ".p2p" / "portable" / "P2P-EXPERIENCE-CAPSULE.json").read_bytes()

    second = _run(package, project)
    assert second.returncode == 0

    assert (project / "AGENTS.md").read_bytes() == first_agents
    assert (project / ".p2p" / "portable" / "P2P-OPERATIONS-NOTEBOOK.md").read_bytes() == first_projection
    assert (project / ".p2p" / "portable" / "P2P-EXPERIENCE-CAPSULE.json").read_bytes() == first_capsule


def test_projection_preserves_existing_agents_and_is_checkable(tmp_path: Path) -> None:
    package = _package(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Existing project rules\n", encoding="utf-8")

    first = _run(package, project)
    assert first.returncode == 0
    first_agents = (project / "AGENTS.md").read_bytes()

    second = _run(package, project)
    check = _run(package, project, "--check")

    assert second.returncode == 0
    assert check.returncode == 0, check.stderr + check.stdout
    assert (project / "AGENTS.md").read_bytes() == first_agents
    agents = first_agents.decode("utf-8")
    assert agents.count("<!-- BEGIN P2P PORTABLE LAW -->") == 1
    assert agents.count("### Native long-running goal bridge") == 1
    assert agents.startswith("# Existing project rules")



def test_projection_migrates_recognized_legacy_preflight_without_touching_project_rules(tmp_path: Path) -> None:
    package = _package(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    legacy = """# AGENTS.md

## P2P law preflight

Before substantive work:

1. Prefer canonical authenticated law:
   `7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`
2. If canonical cross-repo access is unavailable, read:
   `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`
3. Report:
   `P2P_LAW_SOURCE=CANONICAL_AUTHENTICATED|LOCAL_PORTABLE|LAW_CONTEXT_BLOCKED`

## Repository role

Keep this project-specific instruction.
"""
    (project / "AGENTS.md").write_text(legacy, encoding="utf-8")

    first = _run(package, project)
    assert first.returncode == 0, first.stderr + first.stdout
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")

    assert "## P2P law preflight" not in agents
    assert "Prefer canonical authenticated law" not in agents
    assert agents.count("<!-- BEGIN P2P PORTABLE LAW -->") == 1
    assert "do not probe canonical solely" in agents
    assert "## Repository role" in agents
    assert "Keep this project-specific instruction." in agents

    second = _run(package, project)
    assert second.returncode == 0
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == agents


def test_projection_preserves_unrecognized_similar_project_section(tmp_path: Path) -> None:
    package = _package(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    custom = """# AGENTS.md

## P2P law preflight

This is a project-specific note without portable-law markers.

## Repository role

Keep me.
"""
    (project / "AGENTS.md").write_text(custom, encoding="utf-8")

    result = _run(package, project)
    assert result.returncode == 0, result.stderr + result.stdout
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")

    assert "This is a project-specific note without portable-law markers." in agents
    assert agents.count("<!-- BEGIN P2P PORTABLE LAW -->") == 1

def test_check_fails_closed_after_projection_drift(tmp_path: Path) -> None:
    package = _package(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    assert _run(package, project).returncode == 0

    projected = project / ".p2p" / "portable" / "P2P-OPERATIONS-NOTEBOOK.md"
    projected.write_text(projected.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8")

    check = _run(package, project, "--check")

    assert check.returncode == 2
    assert "PORTABLE_LAW_PROJECTION_STALE_OR_MISSING" in check.stdout


def test_canonical_law_and_release_package_recognize_portable_projection() -> None:
    notebook = CANONICAL_NOTEBOOK.read_text(encoding="utf-8")
    package_release = PACKAGE_RELEASE.read_text(encoding="utf-8")

    assert ".p2p/portable/P2P-OPERATIONS-NOTEBOOK.md" in notebook
    assert "P2P_PORTABLE_LAW_PROJECTION=YES" in notebook
    assert "generated portable project projection" in notebook
    assert '"docs/p2p-development/P2P-PORTABLE-LAW-PROJECTION.md"' in package_release
    assert '"scripts/p2p_portable_law_projection.py"' in package_release


def test_check_fails_closed_after_experience_capsule_drift(tmp_path: Path) -> None:
    package = _package(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    assert _run(package, project).returncode == 0

    capsule = project / ".p2p" / "portable" / "P2P-EXPERIENCE-CAPSULE.json"
    capsule.write_text(capsule.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8")

    check = _run(package, project, "--check")

    assert check.returncode == 2
    assert "PORTABLE_LAW_PROJECTION_STALE_OR_MISSING" in check.stdout


def test_actor_law_receipt_and_experience_capsule(tmp_path: Path) -> None:
    package = _package(tmp_path)
    project = tmp_path / "project_receipt"
    project.mkdir()
    res = _run(package, project)
    assert res.returncode == 0

    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "LAW_CHECK=PASS" in agents
    assert "PARENT_SELF_LAW_PREFLIGHT != EXECUTOR_LAW_PREFLIGHT" in agents
    assert "EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE" in agents
    assert "LEARNING_RECONCILIATION=" in agents

    notebook = (project / ".p2p" / "portable" / "P2P-OPERATIONS-NOTEBOOK.md").read_text(encoding="utf-8")
    assert "PORTABLE_EXPERIENCE_CONTENT_SHA256=" in notebook

    capsule = project / ".p2p" / "portable" / "P2P-EXPERIENCE-CAPSULE.json"
    assert capsule.is_file()
    data = json.loads(capsule.read_text(encoding="utf-8"))
    assert data["schema"] == "p2p-portable-experience-capsule/1"
    assert data["generated"] is True
    assert data["authority"] == "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE"


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        test_writes_git_trackable_portable_projection_without_runtime_install(base / "1")
        test_projection_is_byte_idempotent_for_empty_project(base / "2")
        test_projection_preserves_existing_agents_and_is_checkable(base / "3")
        test_projection_migrates_recognized_legacy_preflight_without_touching_project_rules(base / "4")
        test_projection_preserves_unrecognized_similar_project_section(base / "5")
        test_check_fails_closed_after_projection_drift(base / "6")
        test_check_fails_closed_after_experience_capsule_drift(base / "7")
        test_actor_law_receipt_and_experience_capsule(base / "8")
        test_canonical_law_and_release_package_recognize_portable_projection()
    print("ALL PORTABLE LAW PROJECTION TESTS PASS")
