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
LEGACY_PREFLIGHT_HEADING = "## P2P law preflight"
LEGACY_PREFLIGHT_REQUIRED_MARKERS = (
    "7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md",
    ".p2p/portable/P2P-OPERATIONS-NOTEBOOK.md",
    "P2P_LAW_SOURCE=",
)



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
            f"1. If the active canonical law at `{CANONICAL_SOURCE}` has already been successfully reached in this actor/session, read it; canonical wins.",
            f"2. In a repo-scoped remote clone with a valid portable projection, read `{PORTABLE_REL.as_posix()}` directly; do not probe canonical solely to prove cross-repository unavailability.",
            "3. `TARGET_REPO_AUTH != CANONICAL_CROSS_REPO_REACHABILITY`. Authentication to the target repository is not evidence that the private canonical repository is reachable.",
            "4. The project copy is a generated transport projection, never a new law authority. Do not edit it by hand.",
            "5. `TASK_BRANCH != LAW_AUTHORITY` and `TARGET_PROJECT != LAW_SOURCE` remain mandatory.",
            "6. Never claim the canonical repository was read when only the portable projection was read.",
            "7. If neither canonical, installed, nor portable law context is available, use the explicit P2P `SUPREME_LAW_CAPSULE`; otherwise stop at `LAW_CONTEXT_BLOCKED`.",
            "",
            "### Actor separation and self-law preflight",
            "",
            "Every actor (Control Tower, prompt writer, executor, reviewer, supervisor, tool session) must establish its own valid Supreme Law context before substantive work. A law context valid for one actor does not satisfy another actor's preflight.",
            "",
            "- `PARENT_SELF_LAW_PREFLIGHT != EXECUTOR_LAW_PREFLIGHT`",
            "- `EXECUTOR_P2P_LAW_SOURCE` cannot satisfy a parent/prompt-writer/control-tower preflight",
            "- `CONTROL_TOWER_SELF_LAW_RECEIPT=PASS` (when serialized by Control Tower) proves only the parent Control Tower's own preflight; it never proves executor preflight and never substitutes for `P2P_LAW_PREFLIGHT`",
            "- No actor may fake, infer, or copy another actor's receipt/source. Only an actually performed read counts",
            "- If no valid law source can be established for the current actor, stop at `LAW_CONTEXT_BLOCKED`",
            "",
            "### Remote repo-scoped handoff freshness",
            "",
            "- Before delegating to a repo-scoped remote executor that may not reach canonical P2P, the parent Control Tower/prompt writer must fresh-compare this projection's source identity with reachable canonical law.",
            "- If this projection is stale or missing and an authorized repository write path is available, refresh the generated portable notebook and managed AGENTS block before handoff.",
            "- If refresh cannot be performed safely, mark the portable projection stale/missing and hand off a fresh SUPREME_LAW_CAPSULE; the executor must not rely on a known-stale portable copy.",
            "- An authenticated GitHub connector may perform the repository refresh without a local clone; do not add a daemon, registry, GitHub Action, PAT, or new secret solely for projection freshness.",
            "",
            "### Mandatory prompt serialization contract",
            "",
            "Every P2P-generated operational prompt handed to an executor must explicitly serialize both gates below; they must not be left implicit or assumed from chat memory:",
            "",
            "### Arena new-chat title-first UX",
            "",
            "For Arena `NEW_CHAT`, apply `ARENA_CHAT_TITLE_FIRST_LINE_V1`: the first nonblank prompt line is a concise human-readable title, normally `<PROJECT> — <bounded task/outcome>`, with distinguishing words front-loaded. Do not start with `GỬI CHO:`, `DESTINATION=`, `TASK_ID=`, a code fence, or a generic `P2P` prefix. Put routing metadata immediately after the title and set `CHAT_TITLE` to that exact first-line title. For `SAME_CHAT`, preserve the exact existing chat title.",
            "",
            "`P2P_LAW_PREFLIGHT`:",
            "- tell the executor to read repository-root `AGENTS.md` before substantive work;",
            "- use canonical when it is already successfully reachable; otherwise follow installed > valid portable > inline capsule > blocked;",
            "- for a repo-scoped clone with valid portable law, do not make a cross-repo probe solely to trigger fallback;",
            "- report exactly one `P2P_LAW_SOURCE=<actual source>` and never claim a source was read when it was not.",
            "",
            "`OE_GATE`:",
            "- ask exactly `Không bị over engineering chứ?`;",
            "- evaluate `SIMPLER_PATH`, `MATERIAL_PROGRESS`, `NECESSITY`, `CORE_BEFORE_SUPPORT`, and `SMALLER_VERIFIABLE_SLICE`;",
            "- return `OE_VERDICT=DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED` with one concrete reason;",
            "- if the answer is weak or negative, reduce/remove/defer the step instead of returning a ceremonial PASS.",
            "",
            "### Native long-running goal bridge",
            "",
            "For a clear long-running task on a host that supports native `/goal`, use native `/goal` only as a session continuation primitive; canonical P2P GoalPlan/TaskPlan, task state, evidence, and verifier remain authoritative.",
            "",
            "- Prefer `.p2p/system/p2p_capabilities/native_goal_bridge.py` when an installed P2P runtime is present.",
            "- After durable GoalPlan/TaskPlan exists and before the first substantive execution turn for that goal, run `.p2p/system/p2p_capabilities/native_goal_activation.py` when installed and use its decision automatically; do not ask the Owner whether `/goal` should be used.",
            "- `ACTIVATE_NATIVE_GOAL` means invoke the returned host-native command once unless the same goal is already active in the current host session. `NORMAL_P2P_PATH` means continue normally. Helper `BLOCKED` means fail closed on the state/control-plane issue; never synthesize a goal condition.",
            "- Auto-activation is intentionally narrow: Goal status must be `APPROVED` or `IN_PROGRESS`, TaskPlan lifecycle must be `ACTIVE`, the canonical plan must contain at least two tasks, and at least one task must remain non-terminal. If the helper is absent but authoritative durable state is readable, apply exactly this same rule directly; do not invent another detector or state machine.",
            "- Choose `claude_code` or `codex_cli` from the current executor identity, never by asking the Owner. Claude Code may be identified from stable in-session markers; do not treat `CODEX_HOME` alone as proof of a Codex session.",
            "- If installed runtime is absent in a fresh clone, derive the `/goal` completion condition directly from the active P2P goal/task contract. Do not create a second roadmap, state machine, memory authority, router, ledger, daemon, or scheduler.",
            "- Do not conflate host semantics: only claim automatic continuation/evaluator behavior that is documented or directly verified for that host. In particular, do not assume Codex CLI has Claude Code's evaluator semantics.",
            "- Recovery remains failure-class adaptive. Never introduce a fixed retry-count hard stop such as `three strikes => BLOCKED`.",
            "- Before completion, compare against the original baseline across the complete worktree: committed-after-baseline, staged, unstaged, deleted tracked, and untracked files. Prefer `.p2p/system/p2p_capabilities/worktree_evidence.py` when installed; otherwise use equivalent read-only Git inspection.",
            "- Before claiming done, replay the original task contract and re-check acceptance requirements/evidence. Host-native `/goal` evaluation and executor self-report are never P2P acceptance authority.",
            "- If the host has no native `/goal`, continue with the normal P2P execution path; do not add a substitute control plane just to imitate `/goal`.",
            "",
            "This serialization requirement applies to NEW_CHAT and SAME_CHAT execution prompts, including Arena, Codex, Manus, reviewers, supervisors, and other delegated executors. It does not require repeating the whole law body in every prompt.",
            "",
            AGENTS_END,
        )
    )


def _strip_recognized_legacy_preflight(existing: str) -> str:
    """Remove a known standalone legacy P2P law-preflight section.

    Older project bootstraps sometimes placed an unmanaged P2P law preflight
    section before the generated portable block. When that stale section says
    to probe canonical first, a repo-scoped executor may manufacture a
    cross-repository 404 before reaching the current managed instructions.
    Migrate only the exact P2P-shaped section identified by the heading plus
    all required markers; preserve everything else verbatim.
    """
    start = existing.find(LEGACY_PREFLIGHT_HEADING)
    if start < 0:
        return existing
    line_start = existing.rfind("\n", 0, start) + 1
    if line_start != start:
        return existing
    next_heading = existing.find("\n## ", start + len(LEGACY_PREFLIGHT_HEADING))
    end = len(existing) if next_heading < 0 else next_heading + 1
    section = existing[start:end]
    if not all(marker in section for marker in LEGACY_PREFLIGHT_REQUIRED_MARKERS):
        return existing

    prefix = existing[:start].rstrip()
    suffix = existing[end:].lstrip("\n")
    if prefix and suffix:
        return prefix + "\n\n" + suffix
    if prefix:
        return prefix + "\n"
    return suffix


def _merge_agents(existing: str) -> str:
    existing = _strip_recognized_legacy_preflight(existing)
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