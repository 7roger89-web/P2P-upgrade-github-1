from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "p2p_portable_law_projection.py"


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

    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "<!-- BEGIN P2P PORTABLE LAW -->" in agents
    assert ".p2p/portable/P2P-OPERATIONS-NOTEBOOK.md" in agents
    assert "TASK_BRANCH != LAW_AUTHORITY" in agents


def test_projection_is_idempotent_and_checkable(tmp_path: Path) -> None:
    package = _package(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Existing project rules\n", encoding="utf-8")

    first = _run(package, project)
    second = _run(package, project)
    check = _run(package, project, "--check")

    assert first.returncode == 0
    assert second.returncode == 0
    assert check.returncode == 0, check.stderr + check.stdout
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.count("<!-- BEGIN P2P PORTABLE LAW -->") == 1
    assert agents.startswith("# Existing project rules")


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
