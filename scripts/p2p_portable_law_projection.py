#!/usr/bin/env python3
"""Project P2P remote-executor context into a Git-tracked project.

This helper does not install the P2P runtime and does not mutate Git history.
It writes only deterministic, Git-trackable transport surfaces:

- .p2p/portable/P2P-OPERATIONS-NOTEBOOK.md
- .p2p/portable/P2P-EXPERIENCE-CAPSULE.json
- .p2p/portable/P2P-SKILL-PROJECTION.json
- AGENTS.md (one small managed entrypoint block)
- a bounded repo-native operator-skill projection under .agents/skills/

The canonical notebook and canonical skill sources remain authoritative
whenever reachable.  Portable copies exist only so repo-scoped remote
executors can establish law context and consume explicitly required P2P
operator skills without cross-repository access.
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
EXPERIENCE_CAPSULE_SCHEMA = "p2p-portable-experience-capsule/1"
SHARED_CATALOG_REL = Path(".p2p/system/p2p_capabilities/shared_experience_catalog.json")
PORTABLE_EXPERIENCE_REL = Path(".p2p/portable/P2P-EXPERIENCE-CAPSULE.json")
CANONICAL_EXPERIENCE_SOURCE = (
    "7roger89-web/P2P-upgrade-github-1@main:"
    ".p2p/system/p2p_capabilities/shared_experience_catalog.json"
)
PORTABLE_SKILL_SCHEMA = "p2p-portable-skill-projection/1"
PORTABLE_SKILL_MANIFEST_REL = Path(".p2p/portable/P2P-SKILL-PROJECTION.json")
CANONICAL_SKILL_SOURCE = (
    "7roger89-web/P2P-upgrade-github-1@main:.agents/skills"
)
PORTABLE_SKILL_PREFIXES = ("p2p-",)
PORTABLE_SKILL_EXACT = frozenset({"scope-reality-check"})
REQUIRED_PORTABLE_SKILLS = frozenset({"p2p-scope", "scope-reality-check"})
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


def _is_portable_operator_skill(name: str) -> bool:
    return name in PORTABLE_SKILL_EXACT or any(
        name.startswith(prefix) for prefix in PORTABLE_SKILL_PREFIXES
    )


def _portable_skill_files(package_root: Path) -> dict[Path, str]:
    """Return canonical text files for the bounded repo-native operator skills."""
    skills_root = package_root / ".agents" / "skills"
    if skills_root.is_symlink() or not skills_root.is_dir():
        raise ValueError(f"PORTABLE_SKILL_SOURCE_ROOT_MISSING_OR_INVALID:{skills_root}")

    selected_dirs: list[Path] = []
    for entry in sorted(skills_root.iterdir(), key=lambda item: item.name):
        if entry.is_symlink() or not entry.is_dir():
            continue
        if not _is_portable_operator_skill(entry.name):
            continue
        skill_md = entry / "SKILL.md"
        if skill_md.is_symlink() or not skill_md.is_file():
            raise ValueError(f"PORTABLE_SKILL_ENTRYPOINT_MISSING:{entry.name}")
        selected_dirs.append(entry)

    selected_names = {entry.name for entry in selected_dirs}
    missing = sorted(REQUIRED_PORTABLE_SKILLS - selected_names)
    if missing:
        raise ValueError("PORTABLE_REQUIRED_SKILLS_MISSING:" + ",".join(missing))

    files: dict[Path, str] = {}
    for skill_dir in selected_dirs:
        for source in sorted(skill_dir.rglob("*")):
            if source.is_symlink():
                raise ValueError(f"PORTABLE_SKILL_SOURCE_SYMLINK:{source}")
            if source.is_dir():
                continue
            if not source.is_file():
                raise ValueError(f"PORTABLE_SKILL_SOURCE_INVALID:{source}")
            relative = source.relative_to(package_root)
            try:
                text = source.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    f"PORTABLE_SKILL_SOURCE_NOT_UTF8:{source}"
                ) from exc
            files[relative] = text
    return files


def _portable_skill_manifest_text(
    package_root: Path,
    files: dict[Path, str] | None = None,
) -> str:
    projected = files if files is not None else _portable_skill_files(package_root)
    version = _read_required(package_root / "VERSION", "PACKAGE_VERSION").strip()
    managed_files = {
        relative.as_posix(): _sha256_text(text)
        for relative, text in sorted(
            projected.items(), key=lambda item: item[0].as_posix()
        )
    }
    skill_ids = sorted(
        {
            relative.parts[2]
            for relative in projected
            if len(relative.parts) >= 4
            and relative.parts[0] == ".agents"
            and relative.parts[1] == "skills"
        }
    )
    payload = {
        "schema": PORTABLE_SKILL_SCHEMA,
        "generated": True,
        "canonical_source": CANONICAL_SKILL_SOURCE,
        "package_version": version,
        "authority": "NON_AUTHORITATIVE_SKILL_TRANSPORT",
        "routing_authority": False,
        "permission_effect": "NONE",
        "selection_rule": "canonical p2p-* operator skills plus scope-reality-check",
        "skills": skill_ids,
        "managed_files": managed_files,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def expected_portable_skill_state(package_root: Path) -> tuple[dict[Path, str], str]:
    files = _portable_skill_files(package_root)
    return files, _portable_skill_manifest_text(package_root, files)


def _projection_text(package_root: Path) -> str:
    notebook = _read_required(package_root / SOURCE_REL, "SOURCE_NOTEBOOK")
    if LAW_MARKER not in notebook:
        raise ValueError("SOURCE_NOTEBOOK_MISSING_SUPREME_LAW_MARKER")
    version = _read_required(package_root / "VERSION", "PACKAGE_VERSION").strip()
    source_sha256 = _sha256_text(notebook)
    capsule_text = _experience_capsule_text(package_root)
    capsule_sha256 = _sha256_text(capsule_text)
    _, skill_manifest_text = expected_portable_skill_state(package_root)
    skill_manifest_sha256 = _sha256_text(skill_manifest_text)
    header = (
        "<!--\n"
        "P2P_PORTABLE_LAW_PROJECTION=YES\n"
        f"SCHEMA={SCHEMA}\n"
        f"CANONICAL_SOURCE={CANONICAL_SOURCE}\n"
        f"SOURCE_CONTENT_SHA256={source_sha256}\n"
        f"PORTABLE_EXPERIENCE_CONTENT_SHA256={capsule_sha256}\n"
        f"PORTABLE_SKILL_MANIFEST_SHA256={skill_manifest_sha256}\n"
        f"PACKAGE_VERSION={version}\n"
        "PROJECTION_DO_NOT_EDIT=YES\n"
        "CANONICAL_WINS_WHEN_REACHABLE=YES\n"
        "-->\n\n"
    )
    return header + notebook.lstrip("\ufeff")


def _experience_capsule_text(package_root: Path) -> str:
    catalog_path = package_root / SHARED_CATALOG_REL
    version_path = package_root / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else "unknown"
    records = []
    if catalog_path.is_file() and not catalog_path.is_symlink():
        raw_catalog = catalog_path.read_text(encoding="utf-8")
        catalog_sha256 = _sha256_text(raw_catalog)
        try:
            data = json.loads(raw_catalog)
        except json.JSONDecodeError:
            data = {}
        for rec in data.get("records") or []:
            if not isinstance(rec, dict):
                continue
            if rec.get("state") == "ACTIVE" and str(rec.get("scope", "")).upper() in ("DOMAIN", "CROSS_PROJECT"):
                records.append(rec)
    else:
        raw_catalog = "{}"
        catalog_sha256 = _sha256_text(raw_catalog)

    capsule = {
        "schema": EXPERIENCE_CAPSULE_SCHEMA,
        "generated": True,
        "canonical_source": CANONICAL_EXPERIENCE_SOURCE,
        "source_content_sha256": catalog_sha256,
        "package_version": version,
        "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
        "current_state_wins": True,
        "law_and_task_contract_win": True,
        "permission_effect": "NONE",
        "acceptance_authority": False,
        "records": records,
    }
    return json.dumps(capsule, indent=2, sort_keys=True) + "\n"


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
            "- Every actor must visibly emit its own self-read receipt before first substantive work:",
            "  `LAW_CHECK=PASS | SOURCE=<actual source> | SOURCE_SHA256=<canonical source content sha256>`",
            "  or: `LAW_CHECK=BLOCKED | REASON=<reason>`",
            f"- A portable PASS must bind to the recorded `SOURCE_CONTENT_SHA256` from `{PORTABLE_REL.as_posix()}`. A stale portable copy cannot produce PASS",
            "",
            "### Remote repo-scoped handoff freshness",
            "",
            "- Before delegating to a repo-scoped remote executor that may not reach canonical P2P, the parent Control Tower/prompt writer must fresh-compare this projection's source identity with reachable canonical law.",
            "- If this projection is stale or missing and an authorized repository write path is available, refresh the generated portable notebook and managed AGENTS block before handoff.",
            "- If refresh cannot be performed safely, mark the portable projection stale/missing and hand off a fresh SUPREME_LAW_CAPSULE; the executor must not rely on a known-stale portable copy.",
            "- An authenticated GitHub connector may perform the repository refresh without a local clone; do not add a daemon, registry, GitHub Action, PAT, or new secret solely for projection freshness.",
            "- Parent delegation surfaces target-law freshness receipt before delegation:",
            "  `TARGET_LAW_FRESHNESS=CURRENT | REFRESHED | INLINE | BLOCKED`",
            "  `CANONICAL_LAW_SHA256=<sha256>`",
            "  `TARGET_LAW_SHA256=<sha256>`",
            "",
            "### Experience preflight and auto-reuse contract",
            "",
            "For every non-trivial P2P-managed task, after valid law/task-state preflight and before substantive execution:",
            "",
            "1. Perform bounded ACTIVE experience lookup:",
            "   - When installed runtime is present: run `python .p2p/system/p2p_capabilities/experience_evolution.py --root . retrieve --task-text \"<task>\"`",
            f"   - In a repo-scoped remote clone without installed runtime: read `{PORTABLE_EXPERIENCE_REL.as_posix()}` directly and match task triggers against promoted ACTIVE records",
            "2. Emit observable preflight receipt before substantive execution:",
            "   `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=<id,...>`",
            "   or: `EXPERIENCE_CHECK=NO_MATCH`",
            "   or: `EXPERIENCE_CHECK=UNAVAILABLE`",
            "3. Invariants: max results <= 3; experience is NONAUTHORITATIVE context; current law, active task contract, and fresh project truth always outrank prior experience; experience cannot widen permissions or change acceptance authority.",
            "",
            "### Task-end learning reconciliation contract",
            "",
            "At task reconciliation, distinguish routine progress from reusable corrections:",
            "",
            "- `ROUTINE_SUCCESS` => emit `LEARNING_RECONCILIATION=NONE`; do not manufacture memory.",
            "- `REPEATED_OR_MATERIAL_FAILURE` / `CLEARLY_REUSABLE_CORRECTION` => emit `LEARNING_RECONCILIATION=CANDIDATE` with evidence and trigger conditions, or provide an explicit evidence-based reason why no reusable lesson exists.",
            "- Lifecycle: `CANDIDATE -> VERIFIED -> ACTIVE -> SUPERSEDED | QUARANTINED`. No executor self-promotion into Supreme Law, shared authority, capability, or skill.",
            "",
            "### Repo-native required skill handoff",
            "",
            "- This managed repository carries a bounded canonical operator-skill projection under `.agents/skills/`: every canonical `p2p-*` skill plus `scope-reality-check`. It is transport, not a second router or authority.",
            f"- Source-bound projection metadata lives at `{PORTABLE_SKILL_MANIFEST_REL.as_posix()}`. Do not treat an unlisted or hash-mismatched file as a current projected skill.",
            "- When an execution prompt serializes `REQUIRED_SKILLS=<ids>`, every required skill is mandatory for that turn. Read each exact repo-local `SKILL.md` before substantive task execution and apply each required skill.",
            "- The prompt/handoff must bind exact selected skill IDs to repo-local source paths and SHA-256 hashes. Missing file, unknown required skill, or hash mismatch => `SKILL_CONSUMPTION=LOAD_FAILED` and stop; do not silently substitute another skill.",
            "- Do not preload unselected skills. Deep-load references/assets only from selected skills and only when materially required.",
            "- Required skill guidance cannot widen Owner authority, permissions, mutation authority, release/deploy/promotion authority, or task scope.",
            "- Return one exact `p2p-skill-consumption-receipt/1` covering the complete frozen selected set. A receipt missing one required skill is not acceptance evidence.",
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
            "- report exactly one `P2P_LAW_SOURCE=<actual source>` and never claim a source was read when it was not;",
            "- emit actor-own `LAW_CHECK=PASS | SOURCE=<actual source> | SOURCE_SHA256=<canonical hash>` or `LAW_CHECK=BLOCKED`;",
            "- for non-trivial tasks, perform bounded experience check and emit `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE|NO_MATCH|UNAVAILABLE`;",
            "- at task reconciliation, emit `LEARNING_RECONCILIATION=NONE|CANDIDATE`.",
            "",
            "`OE_GATE`:",
            "- ask exactly `Không bị over engineering chứ?`;",
            "- evaluate `SIMPLER_PATH`, `MATERIAL_PROGRESS`, `NECESSITY`, `CORE_BEFORE_SUPPORT`, and `SMALLER_VERIFIABLE_SLICE`;",
            "- return `OE_VERDICT=DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED` with one concrete reason;",
            "- interpret directionally: SIMPLER_PATH=YES or SMALLER_VERIFIABLE_SLICE=YES means choose the simpler/smaller valid path; MATERIAL_PROGRESS=NO, NECESSITY=NO, or CORE_BEFORE_SUPPORT=NO means reduce/remove/defer; do not treat every negative answer as failure or return a ceremonial PASS.",
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


def expected_project_state(package_root: Path, project: Path) -> tuple[str, str, str]:
    projection = _projection_text(package_root)
    agents_path = project / "AGENTS.md"
    if agents_path.is_symlink():
        raise ValueError(f"AGENTS_SYMLINK_NOT_ALLOWED:{agents_path}")
    existing_agents = agents_path.read_text(encoding="utf-8") if agents_path.is_file() else ""
    agents = _merge_agents(existing_agents)
    capsule = _experience_capsule_text(package_root)
    return projection, agents, capsule


def expected_experience_capsule(package_root: Path) -> str:
    return _experience_capsule_text(package_root)


def project_law(package_root: Path, project: Path, *, check: bool = False) -> dict[str, object]:
    package_root = package_root.resolve()
    project = project.resolve()
    if not project.is_dir():
        raise ValueError(f"PROJECT_NOT_DIRECTORY:{project}")

    _assert_safe_parent(project, PORTABLE_REL)
    _assert_safe_parent(project, PORTABLE_EXPERIENCE_REL)
    _assert_safe_parent(project, PORTABLE_SKILL_MANIFEST_REL)
    portable_path = project / PORTABLE_REL
    if portable_path.is_symlink():
        raise ValueError(f"PROJECTION_SYMLINK_NOT_ALLOWED:{portable_path}")
    if portable_path.exists() and not portable_path.is_file():
        raise ValueError(f"PROJECTION_PATH_NOT_FILE:{portable_path}")

    portable_exp_path = project / PORTABLE_EXPERIENCE_REL
    if portable_exp_path.is_symlink():
        raise ValueError(f"PROJECTION_SYMLINK_NOT_ALLOWED:{portable_exp_path}")
    if portable_exp_path.exists() and not portable_exp_path.is_file():
        raise ValueError(f"PROJECTION_PATH_NOT_FILE:{portable_exp_path}")

    skill_manifest_path = project / PORTABLE_SKILL_MANIFEST_REL
    if skill_manifest_path.is_symlink():
        raise ValueError(f"PROJECTION_SYMLINK_NOT_ALLOWED:{skill_manifest_path}")
    if skill_manifest_path.exists() and not skill_manifest_path.is_file():
        raise ValueError(f"PROJECTION_PATH_NOT_FILE:{skill_manifest_path}")

    expected_skills, expected_skill_manifest = expected_portable_skill_state(
        package_root
    )
    for relative in expected_skills:
        _assert_safe_parent(project, relative)
        target = project / relative
        if target.is_symlink():
            raise ValueError(f"PROJECTION_SYMLINK_NOT_ALLOWED:{target}")
        if target.exists() and not target.is_file():
            raise ValueError(f"PROJECTION_PATH_NOT_FILE:{target}")

    expected_projection, expected_agents, expected_exp = expected_project_state(package_root, project)
    agents_path = project / "AGENTS.md"

    if check:
        projection_ok = portable_path.is_file() and portable_path.read_text(encoding="utf-8") == expected_projection
        agents_ok = agents_path.is_file() and agents_path.read_text(encoding="utf-8") == expected_agents
        exp_ok = portable_exp_path.is_file() and portable_exp_path.read_text(encoding="utf-8") == expected_exp
        skill_manifest_ok = (
            skill_manifest_path.is_file()
            and skill_manifest_path.read_text(encoding="utf-8")
            == expected_skill_manifest
        )
        skill_files_ok = True
        for relative, expected_text in expected_skills.items():
            target = project / relative
            try:
                if not target.is_file() or target.read_text(encoding="utf-8") != expected_text:
                    skill_files_ok = False
                    break
            except (OSError, UnicodeError):
                skill_files_ok = False
                break
        if (
            not projection_ok
            or not agents_ok
            or not exp_ok
            or not skill_manifest_ok
            or not skill_files_ok
        ):
            raise ValueError(
                "PORTABLE_LAW_PROJECTION_STALE_OR_MISSING:"
                f"projection_ok={projection_ok},agents_ok={agents_ok},"
                f"experience_ok={exp_ok},skill_manifest_ok={skill_manifest_ok},"
                f"skill_files_ok={skill_files_ok}"
            )
        return {
            "status": "PASS",
            "mode": "CHECK",
            "schema": SCHEMA,
            "portable_path": PORTABLE_REL.as_posix(),
            "portable_experience_path": PORTABLE_EXPERIENCE_REL.as_posix(),
            "portable_skill_manifest_path": PORTABLE_SKILL_MANIFEST_REL.as_posix(),
            "portable_skill_files_count": len(expected_skills),
            "agents_path": "AGENTS.md",
        }

    portable_path.parent.mkdir(parents=True, exist_ok=True)
    portable_path.write_text(expected_projection, encoding="utf-8", newline="\n")
    portable_exp_path.parent.mkdir(parents=True, exist_ok=True)
    portable_exp_path.write_text(expected_exp, encoding="utf-8", newline="\n")
    skill_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    skill_manifest_path.write_text(
        expected_skill_manifest, encoding="utf-8", newline="\n"
    )
    for relative, expected_text in expected_skills.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(expected_text, encoding="utf-8", newline="\n")
    agents_path.write_text(expected_agents, encoding="utf-8", newline="\n")
    return {
        "status": "PASS",
        "mode": "WRITE",
        "schema": SCHEMA,
        "portable_path": PORTABLE_REL.as_posix(),
        "portable_experience_path": PORTABLE_EXPERIENCE_REL.as_posix(),
        "portable_skill_manifest_path": PORTABLE_SKILL_MANIFEST_REL.as_posix(),
        "portable_skill_files_count": len(expected_skills),
        "agents_path": "AGENTS.md",
        "source_sha256": _sha256_text(_read_required(package_root / SOURCE_REL, "SOURCE_NOTEBOOK")),
        "experience_source_sha256": json.loads(expected_exp).get("source_content_sha256", ""),
        "skill_manifest_sha256": _sha256_text(expected_skill_manifest),
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