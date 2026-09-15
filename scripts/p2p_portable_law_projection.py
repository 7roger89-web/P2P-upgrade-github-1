#!/usr/bin/env python3
"""Project P2P Supreme Law into a Git-tracked project for remote executors.

This helper does not install the P2P runtime and does not mutate Git state.
It only writes two project files that are safe to commit:

- .p2p/portable/P2P-OPERATIONS-NOTEBOOK.md
- AGENTS.md (a small managed entrypoint block)

The canonical notebook remains the authority whenever it is reachable.  The
portable copy is transport for remote/fresh-clone executors that cannot read
the private P2P source repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "p2p-portable-law-projection/1"
LAW_MARKER = "P2P_SUPREME_OPERATING_LAW_V1"
SOURCE_REL = Path("docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md")
PORTABLE_REL = Path(".p2p/portable/P2P-OPERATIONS-NOTEBOOK.md")
CANONICAL_SOURCE = (
    "7roger89-web/P2P-upgrade-github-1@main:"
    "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md"
)
AGENTS_BEGIN = "<!-- BEGIN P2P PORTABLE LAW -->"
AGENTS_END = "<!-- END P2P PORTABLE LAW -->"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_required(path: Path, label: str) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label}_MISSING_OR_INVALID:{path}")
    value = path.read_text(encoding="utf-8")
    if not value.strip():
        raise ValueError(f"{label}_EMPTY:{path}")
    return value


def _assert_safe_parent(project: Path, relative: Path) -> None:
    current = project
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"PROJECTION_PARENT_SYMLINK:{current}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"PROJECTION_PARENT_NOT_DIRECTORY:{current}")


def _projection_text(package_root: Path) -> str:
    notebook = _read_required(package_root / SOURCE_REL, "SOURCE_NOTEBOOK")
    if LAW_MARKER not in notebook:
        raise ValueError("SOURCE_NOTEBOOK_MISSING_SUPREME_LAW_MARKER")
    version = _read_required(package_root / "VERSION", "PACKAGE_VERSION").strip()
    source_sha256 = _sha256_text(notebook)
    header = (
        "<!--\n"
        "P2P_PORTABLE_LAW_PROJECTION=YES\n"
        f"SCHEMA={SCHEMA}\n"
        f"CANONICAL_SOURCE={CANONICAL_SOURCE}\n"
        f"SOURCE_CONTENT_SHA256={source_sha256}\n"
        f"PACKAGE_VERSION={version}\n"
        "PROJECTION_DO_NOT_EDIT=YES\n"
        "CANONICAL_WINS_WHEN_REACHABLE=YES\n"
        "-->\n\n"
    )
    return header + notebook.lstrip("\ufeff")


def _agents_block() -> str:
    return "\n".join(
        (
            AGENTS_BEGIN,
            "## P2P portable Supreme Law entrypoint",
            "",
            "Before substantive P2P-managed analysis, planning, prompt writing, implementation, review, testing, or release work:",
            "",
            f"1. Prefer the active canonical law at `{CANONICAL_SOURCE}` when it is actually reachable.",
            f"2. If canonical cross-repository access is unavailable, read `{PORTABLE_REL.as_posix()}` before substantive work.",
            "3. The project copy is a generated transport projection, never a new law authority. Do not edit it by hand.",
            "4. `TASK_BRANCH != LAW_AUTHORITY` and `TARGET_PROJECT != LAW_SOURCE` remain mandatory.",
            "5. Never claim the canonical repository was read when only the portable projection was read.",
            "6. If neither canonical nor portable law context is available, use the explicit P2P `SUPREME_LAW_CAPSULE`; otherwise stop at `LAW_CONTEXT_BLOCKED`.",
            "",
            "### Mandatory prompt serialization contract",
            "",
            "Every P2P-generated operational prompt handed to an executor must explicitly serialize both gates below; they must not be left implicit or assumed from chat memory:",
            "",
            "`P2P_LAW_PREFLIGHT`:",
            "- tell the executor to read repository-root `AGENTS.md` before substantive work;",
            "- establish the valid law source using canonical > installed > portable > inline capsule > blocked;",
            "- report exactly one `P2P_LAW_SOURCE=<actual source>` and never claim a source was read when it was not.",
            "",
            "`OE_GATE`:",
            "- ask exactly `Không bị over engineering chứ?`;",
            "- evaluate `SIMPLER_PATH`, `MATERIAL_PROGRESS`, `NECESSITY`, `CORE_BEFORE_SUPPORT`, and `SMALLER_VERIFIABLE_SLICE`;",
            "- return `OE_VERDICT=DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED` with one concrete reason;",
            "- if the answer is weak or negative, reduce/remove/defer the step instead of returning a ceremonial PASS.",
            "",
            "This serialization requirement applies to NEW_CHAT and SAME_CHAT execution prompts, including Arena, Codex, Manus, reviewers, supervisors, and other delegated executors. It does not require repeating the whole law body in every prompt.",
            "",
            AGENTS_END,
        )
    )


def _merge_agents(existing: str) -> str:
    block = _agents_block()
    start = existing.find(AGENTS_BEGIN)
    end = existing.find(AGENTS_END)
    if (start >= 0) != (end >= 0):
        raise ValueError("AGENTS_PORTABLE_LAW_MARKERS_INCOMPLETE")
    if start >= 0:
        if end < start:
            raise ValueError("AGENTS_PORTABLE_LAW_MARKERS_INVALID")
        end += len(AGENTS_END)
        prefix = existing[:start].rstrip()
        separator = "\n\n" if prefix else ""
        return prefix + separator + block + existing[end:]
    if existing.strip():
        return existing.rstrip() + "\n\n" + block + "\n"
    return block + "\n"


def expected_project_state(package_root: Path, project: Path) -> tuple[str, str]:
    projection = _projection_text(package_root)
    agents_path = project / "AGENTS.md"
    if agents_path.is_symlink():
        raise ValueError(f"AGENTS_SYMLINK_NOT_ALLOWED:{agents_path}")
    existing_agents = agents_path.read_text(encoding="utf-8") if agents_path.is_file() else ""
    agents = _merge_agents(existing_agents)
    return projection, agents


def project_law(package_root: Path, project: Path, *, check: bool = False) -> dict[str, object]:
    package_root = package_root.resolve()
    project = project.resolve()
    if not project.is_dir():
        raise ValueError(f"PROJECT_NOT_DIRECTORY:{project}")

    _assert_safe_parent(project, PORTABLE_REL)
    portable_path = project / PORTABLE_REL
    if portable_path.is_symlink():
        raise ValueError(f"PROJECTION_SYMLINK_NOT_ALLOWED:{portable_path}")
    if portable_path.exists() and not portable_path.is_file():
        raise ValueError(f"PROJECTION_PATH_NOT_FILE:{portable_path}")

    expected_projection, expected_agents = expected_project_state(package_root, project)
    agents_path = project / "AGENTS.md"

    if check:
        projection_ok = portable_path.is_file() and portable_path.read_text(encoding="utf-8") == expected_projection
        agents_ok = agents_path.is_file() and agents_path.read_text(encoding="utf-8") == expected_agents
        if not projection_ok or not agents_ok:
            raise ValueError(
                "PORTABLE_LAW_PROJECTION_STALE_OR_MISSING:"
                f"projection_ok={projection_ok},agents_ok={agents_ok}"
            )
        return {
            "status": "PASS",
            "mode": "CHECK",
            "schema": SCHEMA,
            "portable_path": PORTABLE_REL.as_posix(),
            "agents_path": "AGENTS.md",
        }

    portable_path.parent.mkdir(parents=True, exist_ok=True)
    portable_path.write_text(expected_projection, encoding="utf-8", newline="\n")
    agents_path.write_text(expected_agents, encoding="utf-8", newline="\n")
    return {
        "status": "PASS",
        "mode": "WRITE",
        "schema": SCHEMA,
        "portable_path": PORTABLE_REL.as_posix(),
        "agents_path": "AGENTS.md",
        "source_sha256": _sha256_text(_read_required(package_root / SOURCE_REL, "SOURCE_NOTEBOOK")),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Target project root")
    parser.add_argument(
        "--package-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="P2P source/release package root (default: repository root containing this script)",
    )
    parser.add_argument("--check", action="store_true", help="Verify projection without writing")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = project_law(Path(args.package_root), Path(args.project), check=args.check)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
