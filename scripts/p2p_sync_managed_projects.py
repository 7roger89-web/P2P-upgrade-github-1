#!/usr/bin/env python3
"""Batch sync for P2P-managed remote-executor projections.

Smallest useful wrapper around the existing portable projector. Reuses
p2p_portable_law_projection.project_law(), expected_project_state(), and the
bounded repo-native operator-skill projection.

- Recognizes P2P-managed repos from existing durable markers (AGENTS.md
  P2P block and/or .p2p/portable), not a new registry/database.
- --check: read-only CURRENT|STALE|BLOCKED per project.
- --write: update only stale managed law/experience/skill projection files.
- Refuses symlink/unsafe paths via existing projector safety.
- Skips/BLOCKs dirty/conflicting managed surfaces rather than overwrite owner work.
- Emits human + JSON summary, idempotent second write = zero changes.
- No daemon, watcher, registry, DB, scheduler, GitHub Action, second control plane.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (str(REPO_ROOT), str(REPO_ROOT / "scripts"), str(REPO_ROOT / ".p2p" / "system")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import p2p_portable_law_projection as projector  # noqa: E402

PORTABLE_REL = projector.PORTABLE_REL
PORTABLE_EXPERIENCE_REL = getattr(projector, "PORTABLE_EXPERIENCE_REL", Path(".p2p/portable/P2P-EXPERIENCE-CAPSULE.json"))
PORTABLE_SKILL_MANIFEST_REL = getattr(
    projector,
    "PORTABLE_SKILL_MANIFEST_REL",
    Path(".p2p/portable/P2P-SKILL-PROJECTION.json"),
)
AGENTS_BEGIN_PORTABLE = projector.AGENTS_BEGIN
AGENTS_BEGIN_CODEX = "<!-- BEGIN P2P CODEX -->"


def _is_p2p_managed_dir(path: Path) -> bool:
    """Heuristic: P2P-managed if AGENTS.md has P2P block or .p2p/portable exists."""
    try:
        if not path.is_dir() or path.is_symlink():
            return False
        agents = path / "AGENTS.md"
        if agents.is_file() and not agents.is_symlink():
            try:
                text = agents.read_text(encoding="utf-8")
                if AGENTS_BEGIN_PORTABLE in text or AGENTS_BEGIN_CODEX in text:
                    return True
            except (OSError, UnicodeError):
                pass
        portable = path / PORTABLE_REL
        if portable.is_file() or (path / ".p2p" / "portable").is_dir():
            return True
        # also check .p2p/system marker for installed projects
        if (path / ".p2p" / "system").is_dir():
            return True
    except OSError:
        return False
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
        projector._assert_safe_parent(project_resolved, PORTABLE_SKILL_MANIFEST_REL)
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
        expected_skills, expected_skill_manifest = (
            projector.expected_portable_skill_state(package_root)
        )
        for relative in expected_skills:
            projector._assert_safe_parent(project_resolved, relative)
    except (ValueError, OSError, UnicodeError) as exc:
        return {
            "project": str(project),
            "resolved": str(project_resolved),
            "status": "BLOCKED",
            "reason": str(exc),
        }

    portable_path = project_resolved / PORTABLE_REL
    portable_exp_path = project_resolved / PORTABLE_EXPERIENCE_REL
    portable_skill_manifest_path = project_resolved / PORTABLE_SKILL_MANIFEST_REL
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
    try:
        skill_manifest_ok = (
            portable_skill_manifest_path.is_file()
            and portable_skill_manifest_path.read_text(encoding="utf-8")
            == expected_skill_manifest
        )
    except (OSError, UnicodeError):
        skill_manifest_ok = False
    payload_verification = projector.verify_portable_skill_manifest_payload(
        project_resolved
    )
    skill_payload_ok = bool(payload_verification["ok"])
    skill_files_ok = True
    for relative, expected_text in expected_skills.items():
        target = project_resolved / relative
        try:
            if not target.is_file() or target.read_text(encoding="utf-8") != expected_text:
                skill_files_ok = False
                break
        except (OSError, UnicodeError):
            skill_files_ok = False
            break
    skills_ok = skill_manifest_ok and skill_payload_ok and skill_files_ok

    if proj_ok and agents_ok and exp_ok and skills_ok:
        return {
            "project": str(project),
            "resolved": str(project_resolved),
            "status": "CURRENT",
            "portable_ok": proj_ok,
            "agents_ok": agents_ok,
            "experience_ok": exp_ok,
            "skills_ok": skills_ok,
            "skill_manifest_ok": skill_manifest_ok,
            "skill_payload_ok": skill_payload_ok,
            "skill_payload_mismatches": payload_verification["mismatches"],
            "skill_files_ok": skill_files_ok,
            "projected_skill_files": len(expected_skills),
        }
    else:
        return {
            "project": str(project),
            "resolved": str(project_resolved),
            "status": "STALE",
            "portable_ok": proj_ok,
            "agents_ok": agents_ok,
            "experience_ok": exp_ok,
            "skills_ok": skills_ok,
            "skill_manifest_ok": skill_manifest_ok,
            "skill_payload_ok": skill_payload_ok,
            "skill_payload_mismatches": payload_verification["mismatches"],
            "skill_files_ok": skill_files_ok,
            "projected_skill_files": len(expected_skills),
        }


def _write_project(package_root: Path, project: Path) -> dict:
    """Attempt to update stale project, respecting dirty check."""
    # First, check dirty before any overwrite attempt
    try:
        project_resolved = project.resolve()
    except OSError:
        project_resolved = project
    if project_resolved.is_dir() and (project_resolved / ".git").exists():
        managed_paths = [
            Path("AGENTS.md"),
            PORTABLE_REL,
            PORTABLE_EXPERIENCE_REL,
            PORTABLE_SKILL_MANIFEST_REL,
        ]
        try:
            expected_skills, _ = projector.expected_portable_skill_state(package_root)
            managed_paths.extend(expected_skills.keys())
        except (ValueError, OSError, UnicodeError):
            pass
        dirty = _is_git_dirty(project_resolved, managed_paths)
        if dirty:
            return {
                "project": str(project),
                "resolved": str(project_resolved),
                "status": "BLOCKED",
                "reason": f"DIRTY_WORKTREE:{project_resolved}:managed law/experience/skill projection has uncommitted changes",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Workspace root containing P2P-managed repos (shallow discovery)")
    parser.add_argument("--project", type=Path, action="append", default=[], help="Explicit project path (repeatable)")
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
    args = parser.parse_args(argv)

    # Default to check if neither specified
    mode_check = not args.write
    if args.check and args.write:
        parser.error("--check and --write are mutually exclusive")

    package_root = args.package_root.resolve()
    if not package_root.is_dir():
        print(f"PACKAGE_ROOT_NOT_DIRECTORY:{package_root}", file=sys.stderr)
        return 2

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

    summary = {
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
