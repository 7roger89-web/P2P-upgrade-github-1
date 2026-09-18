"""Foreground P2P Control Tower coordinator.

Control Tower coordinates durable task state, bounded delegation, evidence
reconciliation, and the next safe action. It is not the law authority, the
executor, a second router, or a second truth store.

The runtime prompt keeps exactly the nine canonical Supreme-Law capsule entries.
Operational guidance (project preflight, OE, GitHub handling, prompt-authoring)
and verified experience are task-scoped context, not extra Supreme Laws.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
for candidate in (str(REPO_ROOT), str(SYSTEM_ROOT), str(REPO_ROOT / "scripts")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

# Importing the package executes legacy compatibility projections that append
# operational guidance to control_tower_handoff.SUPREME_LAW_CAPSULE. For the
# canonical foreground Control Tower CLI we immediately restore the pristine
# nine-law capsule. Those appended texts remain available in installed/project
# instructions; they are not independent Supreme Laws and must not ride in every
# executor prompt.
from p2p_capabilities import control_tower_handoff as _handoff  # noqa: E402

_CANONICAL_LAW_IDENTIFIERS = (
    "OWNER_OUTCOME_AND_AUTHORITY_ARE_INVARIANTS",
    "SIMPLEST_USEFUL_PATH_TO_COMPLETION",
    "REAL_STATE_AND_EVIDENCE_OVERRIDE_ASSUMPTIONS",
    "RECOVER_ADAPTIVELY; DO_NOT_ENTER_SPECULATIVE_FIX_LOOPS",
    "PRESERVE_CONTINUITY_AND_STOP",
    "PROMPT_DESTINATION_AND_PLAN_STATE_ARE_EXPLICIT",
    "ANALYTICAL_AUTONOMY_AND_DELEGATION_ALIGNMENT",
    "TASK_CONTRACT_AND_ACCEPTANCE_FIDELITY",
    "EXECUTOR_INPUT_FORMAT_AND_ARTIFACT_TRANSPORT_FIDELITY",
)
_law_lines = tuple(line for line in _handoff.SUPREME_LAW_CAPSULE.splitlines() if line.strip())
if len(_law_lines) < 9 or any(
    identifier not in _law_lines[index]
    for index, identifier in enumerate(_CANONICAL_LAW_IDENTIFIERS)
):
    raise RuntimeError("CONTROL_TOWER_CANONICAL_SUPREME_LAW_CAPSULE_INVALID")
_handoff.SUPREME_LAW_CAPSULE = "\n".join(_law_lines[:9])

from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    UNKNOWN,
    BindingError,
    ControlTower,
    ControlTowerHandoffError,
    SessionBinding,
    build_execution_prompt,
    new_session_id,
    render_snapshot,
)
from p2p_capabilities.experience_evolution import (  # noqa: E402
    ExperienceEvolutionError,
    activation_summary,
)
from p2p_capabilities.review_extension_activation import render_review_guidance  # noqa: E402


CONTEXT_MARKER = "CONTROL_TOWER_CONTEXT:"
SELF_LAW_RECEIPT_MARKER = "CONTROL_TOWER_SELF_LAW_RECEIPT="
LAW_RECEIPT_SCHEMA = "p2p-control-tower-self-law-receipt/1"
LAW_MARKER = "P2P_SUPREME_OPERATING_LAW_V1"
NO_WORK_MARKER = "NO_SUBSTANTIVE_WORK_BEFORE_VALID_LAW_CONTEXT = YES"
CANONICAL_NOTEBOOK_REL = Path("docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md")
INSTALLED_NOTEBOOK_REL = Path(".p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md")
PORTABLE_NOTEBOOK_REL = Path(".p2p/portable/P2P-OPERATIONS-NOTEBOOK.md")
PORTABLE_PROJECTION_MARKER = "P2P_PORTABLE_LAW_PROJECTION=YES"
CANONICAL_REPO_SLUG = "7roger89-web/p2p-upgrade-github-1"
PORTABLE_CANONICAL_SOURCE = (
    "7roger89-web/P2P-upgrade-github-1@main:"
    "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_ACTIVE_EXPERIENCES = 3
PROMPT_GUARD_CHARS = 8192
MIN_CONTEXT_BUDGET = 380
MAX_PRIMARY_RISK_WRAPPER_CHARS = 360
CONTROL_TOWER_FLOW = (
    "OUTCOME>SELF_LAW_RECEIPT>FRESH_STATE>ONE_LAW>TASK_CONTRACT>"
    "SELECT_EXISTING_CAPABILITY_OR_HOST>BOUNDED_CONTEXT>EXECUTE>EVIDENCE>"
    "RECONCILE>DONE|NEXT|BLOCKED|OWNER_GATE"
)
_GITHUB_TASK = re.compile(r"\b(github|pull request|\bpr\b|merge|branch|commit|repository|repo|head sha)\b", re.I)
_PROMPT_TASK = re.compile(r"\b(prompt|instruction|delegate|delegation|handoff|executor prompt|rewrite prompt)\b", re.I)


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve() if args.root else REPO_ROOT


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_law_text(
    text: str,
    *,
    source_type: str,
    source: str,
    portable: bool = False,
    source_revision: str = UNKNOWN,
) -> dict[str, Any]:
    if not text.strip():
        raise BindingError(f"LAW_CONTEXT_EMPTY:{source_type}:{source}")
    required = (LAW_MARKER, NO_WORK_MARKER, *_CANONICAL_LAW_IDENTIFIERS)
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise BindingError(
            f"LAW_CONTEXT_CONTRACT_INCOMPLETE:{source_type}:{','.join(missing[:3])}"
        )

    content_sha256 = _sha256_text(text)
    if portable:
        header_end = text.find("-->\n\n")
        if not text.startswith("<!--\n") or header_end < 0:
            raise BindingError("PORTABLE_LAW_HEADER_INVALID")
        header = text[: header_end + 3]
        body = text[header_end + 5 :]
        fields: dict[str, str] = {}
        for line in header.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            fields[key.strip()] = value.strip()
        if fields.get("P2P_PORTABLE_LAW_PROJECTION") != "YES":
            raise BindingError("PORTABLE_LAW_PROJECTION_MARKER_INVALID")
        if fields.get("CANONICAL_SOURCE") != PORTABLE_CANONICAL_SOURCE:
            raise BindingError("PORTABLE_LAW_CANONICAL_SOURCE_INVALID")
        expected_sha = fields.get("SOURCE_CONTENT_SHA256", "").lower()
        if not _SHA256_RE.fullmatch(expected_sha):
            raise BindingError("PORTABLE_LAW_SOURCE_SHA256_INVALID")
        if _sha256_text(body) != expected_sha:
            raise BindingError("PORTABLE_LAW_CONTENT_HASH_MISMATCH")
        if fields.get("PROJECTION_DO_NOT_EDIT") != "YES":
            raise BindingError("PORTABLE_LAW_EDIT_GUARD_INVALID")
        if fields.get("CANONICAL_WINS_WHEN_REACHABLE") != "YES":
            raise BindingError("PORTABLE_LAW_PRECEDENCE_INVALID")

    return {
        "schema": LAW_RECEIPT_SCHEMA,
        "status": "PASS",
        "actor": "CONTROL_TOWER_SELF",
        "source_type": source_type,
        "source": source,
        "source_revision": source_revision,
        "content_sha256": content_sha256,
        "supreme_law_marker": LAW_MARKER,
        "no_substantive_work_marker": True,
        "executor_receipt_substitute": False,
        "model_or_session_reset_requires_reread": True,
        "authority_effect": "NONE",
        "mutated": False,
    }


def _read_law_text(path: Path, *, source_type: str, portable: bool = False) -> dict[str, Any] | None:
    """Read and validate one law source; never infer a read from a marker alone."""

    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise BindingError(f"LAW_CONTEXT_INVALID_PATH:{source_type}:{path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise BindingError(f"LAW_CONTEXT_UNREADABLE:{source_type}:{path}") from exc
    return _validate_law_text(
        text,
        source_type=source_type,
        source=path.as_posix(),
        portable=portable,
    )


def _run_git(package: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(package), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode:
        return None
    return result.stdout.strip()


def _normalize_github_repo(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().replace("\\", "/")
    lowered = normalized.lower()
    if lowered.startswith("git@github.com:"):
        slug = normalized.split(":", 1)[1]
    elif "github.com/" in lowered:
        index = lowered.find("github.com/") + len("github.com/")
        slug = normalized[index:]
    else:
        return None
    slug = slug.split("?", 1)[0].split("#", 1)[0].strip("/")
    if slug.lower().endswith(".git"):
        slug = slug[:-4]
    parts = slug.split("/")
    if len(parts) < 2:
        return None
    return "/".join(parts[:2]).lower()


def _checkout_root(package: Path) -> Path | None:
    top = _run_git(package, "rev-parse", "--show-toplevel")
    if not top:
        return None
    try:
        resolved = Path(top).resolve()
        return resolved if resolved == package.resolve() else None
    except OSError:
        return None


def _is_canonical_checkout(package: Path) -> bool:
    if _checkout_root(package) is None:
        return False
    origin = _run_git(package, "remote", "get-url", "origin")
    return _normalize_github_repo(origin) == CANONICAL_REPO_SLUG


def _read_canonical_main_ref(package: Path) -> dict[str, Any]:
    """Read Supreme Law from canonical main Git object, never task working tree."""

    checked_refs: list[str] = []
    for ref in ("refs/remotes/origin/main", "refs/heads/main"):
        revision = _run_git(package, "rev-parse", "--verify", f"{ref}^{{commit}}")
        if not revision:
            continue
        checked_refs.append(ref)
        text = _run_git(package, "show", f"{ref}:{CANONICAL_NOTEBOOK_REL.as_posix()}")
        if text is None:
            raise BindingError(f"CANONICAL_MAIN_LAW_UNREADABLE:{ref}")
        receipt = _validate_law_text(
            text + ("\n" if text and not text.endswith("\n") else ""),
            source_type="CANONICAL_MAIN_REF",
            source=f"git:{ref}:{CANONICAL_NOTEBOOK_REL.as_posix()}",
            source_revision=revision,
        )
        receipt["task_branch_law_authority"] = False
        return receipt
    raise BindingError(
        "LAW_CONTEXT_BLOCKED:CANONICAL_MAIN_REF_UNAVAILABLE:"
        + (",".join(checked_refs) if checked_refs else "NO_MAIN_REF")
    )


def _inline_capsule_receipt() -> dict[str, Any]:
    lines = tuple(line for line in _handoff.SUPREME_LAW_CAPSULE.splitlines() if line.strip())
    if len(lines) != 9 or any(
        identifier not in lines[index]
        for index, identifier in enumerate(_CANONICAL_LAW_IDENTIFIERS)
    ):
        raise BindingError("INLINE_SUPREME_LAW_CAPSULE_INVALID")
    text = "\n".join(lines)
    return {
        "schema": LAW_RECEIPT_SCHEMA,
        "status": "PASS",
        "actor": "CONTROL_TOWER_SELF",
        "source_type": "INLINE_SUPREME_LAW_CAPSULE",
        "source": "p2p_capabilities.control_tower_handoff:SUPREME_LAW_CAPSULE",
        "source_revision": UNKNOWN,
        "content_sha256": _sha256_text(text),
        "supreme_law_marker": LAW_MARKER,
        "no_substantive_work_marker": True,
        "executor_receipt_substitute": False,
        "model_or_session_reset_requires_reread": True,
        "authority_effect": "NONE",
        "mutated": False,
        "capsule_fallback": True,
    }


def _establish_control_tower_law_context(
    root: Path,
    *,
    package_root: Path | None = None,
) -> dict[str, Any]:
    """Establish the Control Tower actor's own law receipt before CT reasoning.

    A task/executor claim cannot satisfy this function. In the canonical source
    checkout the only canonical file authority is main's Git object. The current
    task branch/working tree is execution state and can never select its own law.
    """

    project_root = root.expanduser().resolve()
    package = (package_root or REPO_ROOT).expanduser().resolve()

    if _is_canonical_checkout(package):
        # Strict by design: a canonical checkout must prove canonical main. Never
        # downgrade to a task-branch working-tree law or branch-edited projection.
        return _read_canonical_main_ref(package)

    package_source = package / CANONICAL_NOTEBOOK_REL
    installed = project_root / INSTALLED_NOTEBOOK_REL
    portable = project_root / PORTABLE_NOTEBOOK_REL

    # A release archive may carry the canonical notebook as a local freshness
    # witness for generated projections. It is not itself an extra authority
    # tier. A non-canonical Git checkout is never allowed to impersonate that
    # release witness merely by carrying a file at the canonical path.
    packaged_sha: str | None = None
    if _checkout_root(package) is None:
        try:
            package_receipt = _read_law_text(package_source, source_type="PACKAGED_FRESHNESS_WITNESS")
        except BindingError:
            package_receipt = None
        if package_receipt is not None:
            packaged_sha = str(package_receipt.get("content_sha256") or "")

    rejected: list[str] = []
    for path, source_type, portable_source in (
        (installed, "INSTALLED_PROJECTION", False),
        (portable, "PORTABLE_PROJECTION", True),
    ):
        try:
            receipt = _read_law_text(path, source_type=source_type, portable=portable_source)
        except BindingError as exc:
            rejected.append(f"{source_type}:{exc}")
            continue
        if receipt is None:
            continue
        if packaged_sha and source_type == "INSTALLED_PROJECTION":
            if receipt.get("content_sha256") != packaged_sha:
                rejected.append("INSTALLED_PROJECTION:KNOWN_STALE_VS_PACKAGE")
                continue
        if packaged_sha and source_type == "PORTABLE_PROJECTION":
            portable_text = path.read_text(encoding="utf-8")
            header_end = portable_text.find("-->\n\n")
            header = portable_text[: header_end + 3] if header_end >= 0 else ""
            match = re.search(r"(?m)^SOURCE_CONTENT_SHA256=([0-9a-fA-F]{64})$", header)
            if match and match.group(1).lower() != packaged_sha:
                rejected.append("PORTABLE_PROJECTION:KNOWN_STALE_VS_PACKAGE")
                continue
        return receipt

    try:
        return _inline_capsule_receipt()
    except BindingError as exc:
        rejected.append(f"INLINE_CAPSULE:{exc}")
    reason = ";".join(rejected[:4]) if rejected else "NO_VALID_SOURCE"
    raise BindingError(f"LAW_CONTEXT_BLOCKED:CONTROL_TOWER_SELF_READ_REQUIRED:{reason}")


def _law_receipt_line(receipt: Mapping[str, Any]) -> str:
    if receipt.get("status") != "PASS" or receipt.get("actor") != "CONTROL_TOWER_SELF":
        raise BindingError("CONTROL_TOWER_SELF_LAW_RECEIPT_INVALID")
    source_type = _compact_text(receipt.get("source_type"), 64)
    source = _compact_text(receipt.get("source"), 180)
    sha256 = str(receipt.get("content_sha256") or "").lower()
    if not _SHA256_RE.fullmatch(sha256):
        raise BindingError("CONTROL_TOWER_SELF_LAW_RECEIPT_SHA256_INVALID")
    return (
        f"{SELF_LAW_RECEIPT_MARKER}PASS; ACTOR=CONTROL_TOWER_SELF; "
        f"SOURCE_TYPE={source_type}; SOURCE={source}; SHA256={sha256}; "
        "EXECUTOR_RECEIPT_SUBSTITUTE=NO; AUTHORITY_EFFECT=NONE"
    )


def _experience_summary(root: Path, task_text: str) -> dict[str, Any]:
    """Retrieve bounded ACTIVE experience without making it execution authority."""

    try:
        return activation_summary(root, task_text, max_results=MAX_ACTIVE_EXPERIENCES)
    except (ExperienceEvolutionError, OSError):
        return {
            "schema": "p2p-experience-evolution/1",
            "decision": "UNAVAILABLE",
            "experiences": [],
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "current_state_wins": True,
            "law_and_task_contract_win": True,
            "permission_effect": "NONE",
            "acceptance_authority": False,
            "mutated": False,
        }


def _compact_text(value: Any, limit: int) -> str:
    normalized = " ".join(str(value or "").split())
    if limit <= 0:
        return ""
    if len(normalized) <= limit:
        return normalized
    if limit == 1:
        return "…"
    return normalized[: limit - 1].rstrip() + "…"


def _append_if_fits(parts: list[str], value: str, max_chars: int) -> bool:
    candidate = "\n".join((*parts, value))
    if len(candidate) > max_chars:
        return False
    parts.append(value)
    return True


def _render_context_block(
    summary: Mapping[str, Any],
    task_text: str,
    *,
    max_chars: int,
    law_receipt: Mapping[str, Any] | None = None,
) -> str:
    """Render mandatory runtime gates plus trigger-scoped guidance and experience.

    Priority (highest first):
      mandatory governance / self-law receipt
      -> mandatory execution gates (P2P_LAW_PREFLIGHT, OE_GATE, review gap when triggered)
      -> PRIMARY_RISK_WRAPPER when matching ACTIVE experience exists
      -> bounded experience refs/metadata
      -> optional task-scoped guidance only if space remains
    """

    mandatory = [
        CONTEXT_MARKER,
        "LAW_AUTHORITY=ONE; Supreme Law=canonical 9-law capsule; projections/fallbacks/subordinate profiles are not independent laws.",
        f"CONTROL_TOWER_FLOW={CONTROL_TOWER_FLOW}",
    ]
    if law_receipt is not None:
        mandatory.append(_law_receipt_line(law_receipt))
    mandatory.extend(
        (
            # Shortened but semantically equivalent to preserve budget for PRIMARY_RISK_WRAPPER.
            # Keeps executor-receipt != CT self-read invariant while fitting tight budgets.
            "P2P_LAW_PREFLIGHT=read AGENTS.md; resolve canonical>installed>portable>inline; report P2P_LAW_SOURCE; no fake read; executor receipt != Control Tower self-read.",
            "REMOTE_PROJECTION_GATE=repo-scoped handoff: fresh-compare target portable hash to canonical; stale/missing=>refresh via authorized repo path or INLINE_CAPSULE; never delegate stale portable.",
            "OE_GATE=Không bị over engineering chứ? Check SIMPLER_PATH,MATERIAL_PROGRESS,NECESSITY,CORE_BEFORE_SUPPORT,SMALLER_VERIFIABLE_SLICE; return DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED.",
        )
    )
    block = "\n".join(mandatory)
    if len(block) > max_chars:
        return ""
    parts = list(mandatory)

    task = str(task_text or "")

    # Mandatory execution gate: review gap delegation is fail-closed when triggered.
    review_guidance = render_review_guidance(task)
    if review_guidance and not _append_if_fits(parts, review_guidance, max_chars):
        return ""

    # Bounded ACTIVE experience retrieval (read-only)
    experiences = summary.get("experiences")
    active_items = [
        item
        for item in (experiences[:MAX_ACTIVE_EXPERIENCES] if isinstance(experiences, list) else [])
        if isinstance(item, Mapping)
    ]

    decision = _compact_text(summary.get("decision", "UNAVAILABLE"), 32)
    # Shortened but still contains XP= and NONAUTHORITATIVE required by tests.
    exp_line = f"EXPERIENCE=XP={decision}; MAX={MAX_ACTIVE_EXPERIENCES}; NONAUTHORITATIVE; law/task/state win."

    # High-priority safety context: PRIMARY_RISK_WRAPPER before optional guidance
    # and before bounded refs/metadata, so optional guidance cannot evict it.
    if active_items:
        primary = active_items[0]
        risk_source = primary.get("correction") or primary.get("lesson")
        prefix = "PRIMARY_RISK_WRAPPER="
        refs = ",".join(_compact_text(item.get("experience_id") or UNKNOWN, 80) for item in active_items)
        refs_line = f"ACTIVE_EXPERIENCE_REFS={refs}"

        # Reserve space for exp + refs + risk minimal to ensure all high-priority pieces fit.
        used = len("\n".join(parts))
        # Need: \n + risk_line + \n + exp_line + \n + refs_line
        # risk_line = prefix + risk_content (at least 32)
        min_needed = 1 + len(prefix) + 32 + 1 + len(exp_line) + 1 + len(refs_line)
        if len("\n".join(parts)) + min_needed > max_chars:
            # Even minimal risk + exp + refs does not fit after mandatory => fail closed.
            return ""

        remaining_for_risk = max_chars - (used + 1 + len(exp_line) + 1 + len(refs_line) + 1 + len(prefix))
        # remaining_for_risk is budget for risk_content only
        risk_budget = min(remaining_for_risk, MAX_PRIMARY_RISK_WRAPPER_CHARS)
        if risk_budget < 32:
            return ""
        risk = _compact_text(risk_source, risk_budget)
        if not risk:
            return ""
        # Now append in priority order: risk, exp, refs
        _append_if_fits(parts, prefix + risk, max_chars)
        _append_if_fits(parts, exp_line, max_chars)
        _append_if_fits(parts, refs_line, max_chars)
    else:
        # No active experience: only exp line, then optional guidance if space.
        _append_if_fits(parts, exp_line, max_chars)
        if _GITHUB_TASK.search(task):
            _append_if_fits(
                parts,
                "GITHUB_GUIDANCE=EXECUTOR_GITHUB_ACCESS != OWNER_GITHUB_CONNECTOR_STATUS; direct repo/PR/HEAD evidence wins; do not infer account breakage from one unavailable session.",
                max_chars,
            )
        if _PROMPT_TASK.search(task):
            _append_if_fits(
                parts,
                "PROMPT_AUTHORING_DISCIPLINE_V1=classify PROMPT_INPUT_MATURITY as READY_PROMPT|PARTIAL_DRAFT|CLEAR_SIMPLE_REQUEST|AMBIGUOUS_HIGH_IMPACT; CLARIFICATION_DISCIPLINE=no re-ask/interview loop; DESTINATION_RESOLUTION from durable state; CAPABILITY_OVER_FOLKLORE; PROPORTIONAL_PROMPT_COMPLEXITY; NO_PRIVATE_CHAIN_OF_THOUGHT_REQUEST; REVISION_CONTINUITY; OUTPUT_SURFACE_FIDELITY; PROMPT_AUTHORING_STOP.",
                max_chars,
            )
        return "\n".join(parts)

    # Optional task-scoped guidance only if space remains (lowest priority)
    if _GITHUB_TASK.search(task):
        _append_if_fits(
            parts,
            "GITHUB_GUIDANCE=EXECUTOR_GITHUB_ACCESS != OWNER_GITHUB_CONNECTOR_STATUS; direct repo/PR/HEAD evidence wins; do not infer account breakage from one unavailable session.",
            max_chars,
        )
    if _PROMPT_TASK.search(task):
        _append_if_fits(
            parts,
            "PROMPT_AUTHORING_DISCIPLINE_V1=classify PROMPT_INPUT_MATURITY as READY_PROMPT|PARTIAL_DRAFT|CLEAR_SIMPLE_REQUEST|AMBIGUOUS_HIGH_IMPACT; CLARIFICATION_DISCIPLINE=no re-ask/interview loop; DESTINATION_RESOLUTION from durable state; CAPABILITY_OVER_FOLKLORE; PROPORTIONAL_PROMPT_COMPLEXITY; NO_PRIVATE_CHAIN_OF_THOUGHT_REQUEST; REVISION_CONTINUITY; OUTPUT_SURFACE_FIDELITY; PROMPT_AUTHORING_STOP.",
            max_chars,
        )

    return "\n".join(parts)


def _contextual_task_for_session(
    root: Path,
    binding: SessionBinding,
    task_text: str,
    *,
    worktree: str = UNKNOWN,
    branch: str = UNKNOWN,
    canonical_base_sha: str = UNKNOWN,
    canonical_base_tree: str = UNKNOWN,
    acceptance_criteria: Sequence[str] = (),
    law_receipt: Mapping[str, Any] | None = None,
) -> str:
    """Fit runtime guidance + relevant experience into the exact prompt budget."""

    task = str(task_text or "").strip()
    if not task:
        raise BindingError("CONTROL_TOWER_TASK_REQUIRED")
    if CONTEXT_MARKER in task or SELF_LAW_RECEIPT_MARKER in task:
        raise BindingError("CONTROL_TOWER_RESERVED_CONTEXT_IN_TASK")

    receipt = law_receipt or _establish_control_tower_law_context(root)
    base_prompt = build_execution_prompt(
        binding,
        task,
        worktree=worktree,
        branch=branch,
        canonical_base_sha=canonical_base_sha,
        canonical_base_tree=canonical_base_tree,
        acceptance_criteria=acceptance_criteria,
    )
    remaining = PROMPT_GUARD_CHARS - len(base_prompt) - 2
    if remaining < MIN_CONTEXT_BUDGET:
        raise BindingError(
            f"CONTROL_TOWER_PROMPT_BUDGET_EXHAUSTED:base={len(base_prompt)}:remaining={remaining}"
        )

    block = _render_context_block(
        _experience_summary(root, task),
        task,
        max_chars=remaining,
        law_receipt=receipt,
    )
    if not block:
        raise BindingError("CONTROL_TOWER_REQUIRED_CONTEXT_DID_NOT_FIT")
    contextual = f"{task}\n\n{block}"

    final_prompt = build_execution_prompt(
        binding,
        contextual,
        worktree=worktree,
        branch=branch,
        canonical_base_sha=canonical_base_sha,
        canonical_base_tree=canonical_base_tree,
        acceptance_criteria=acceptance_criteria,
    )
    if len(final_prompt) > PROMPT_GUARD_CHARS:
        raise BindingError(f"CONTROL_TOWER_FINAL_PROMPT_TOO_LARGE:{len(final_prompt)}")
    return contextual


def _extract_task_text(prompt: str) -> str:
    start_marker = "\nTASK:\n"
    end_marker = "\nACCEPTANCE_CRITERIA:\n"
    start = prompt.find(start_marker)
    if start < 0:
        raise BindingError("CONTROL_TOWER_TASK_SECTION_MISSING")
    start += len(start_marker)
    end = prompt.find(end_marker, start)
    if end < 0:
        raise BindingError("CONTROL_TOWER_ACCEPTANCE_SECTION_MISSING")
    task = prompt[start:end].strip()
    if not task:
        raise BindingError("CONTROL_TOWER_TASK_SECTION_EMPTY")
    return task


def _print_result(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return
    receipt = result.get("control_tower_self_law_receipt")
    if isinstance(receipt, Mapping):
        print("CONTROL TOWER SELF LAW RECEIPT")
        print(_law_receipt_line(receipt))
    snapshot = result.get("snapshot")
    if isinstance(snapshot, dict):
        print(render_snapshot(snapshot))
    recommendation = result.get("recommendation")
    if isinstance(recommendation, dict):
        print("\nEXACT CHAT NAME")
        print(recommendation.get("CHAT_NAME", UNKNOWN))
        print("\nREADY-TO-PASTE PROMPT")
        print(recommendation.get("PROMPT", ""))
    reconciliation = result.get("reconciliation")
    if reconciliation is not None:
        print("\nINGEST RECONCILIATION")
        print(json.dumps(reconciliation, ensure_ascii=False, sort_keys=True, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Coordinate durable P2P task state, assemble bounded runtime/experience context, "
            "start executor sessions, and reconcile their evidence."
        )
    )
    parser.add_argument("--root", help="project root; defaults to the repository containing this script")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    parser.add_argument("--current-canonical-base-sha", default=UNKNOWN)
    parser.add_argument("--current-canonical-base-tree", default=UNKNOWN)
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="register a bounded session and print its context-assembled prompt")
    start.add_argument("--host", required=True)
    start.add_argument("--goal-id", required=True)
    start.add_argument("--goal", required=True)
    start.add_argument("--task-id", default=UNKNOWN)
    start.add_argument("--session-id")
    start.add_argument("--canonical-base-sha", default=UNKNOWN)
    start.add_argument("--canonical-base-tree", default=UNKNOWN)
    start.add_argument("--worktree", default=UNKNOWN)
    start.add_argument("--branch", default=UNKNOWN)
    start.add_argument("--acceptance-criterion", action="append", default=[])
    start.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)

    snapshot = sub.add_parser("snapshot", help="show the reconciled Control Tower projection")
    snapshot.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)

    ingest = sub.add_parser("ingest", help="ingest a complete executor response from a UTF-8 text file")
    ingest.add_argument("--response-file", required=True)
    ingest.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)

    next_session = sub.add_parser(
        "next",
        help="derive and register the next safe task-state session with bounded context assembly",
    )
    next_session.add_argument("--host", required=True)
    next_session.add_argument("--session-id")
    next_session.add_argument("--worktree", default=UNKNOWN)
    next_session.add_argument("--branch", default=UNKNOWN)
    next_session.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)
    return parser


def _start_next_with_context(
    tower: ControlTower,
    root: Path,
    host: str,
    *,
    session_id: str | None,
    worktree: str,
    branch: str,
    law_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    planned = tower.recommend_next_session(
        host,
        session_id=session_id,
        worktree=worktree,
        branch=branch,
    )
    if planned.get("status") != "PASS":
        return planned
    if planned.get("idempotent"):
        return tower.start_next_session(
            host,
            session_id=session_id,
            worktree=worktree,
            branch=branch,
        )
    binding_mapping = planned.get("binding")
    recommendation = planned.get("recommendation")
    if not isinstance(binding_mapping, Mapping) or not isinstance(recommendation, Mapping):
        raise BindingError("CONTROL_TOWER_NEXT_RECOMMENDATION_INVALID")
    prompt = recommendation.get("PROMPT")
    if not isinstance(prompt, str):
        raise BindingError("CONTROL_TOWER_NEXT_PROMPT_INVALID")
    binding = SessionBinding.from_mapping(binding_mapping)
    task_id = str(planned.get("task_id", UNKNOWN))
    criteria = tuple(planned.get("acceptance_criteria") or ())
    result = tower.start_session(
        binding,
        task_id=task_id,
        task_prompt=_contextual_task_for_session(
            root,
            binding,
            _extract_task_text(prompt),
            worktree=worktree,
            branch=branch,
            acceptance_criteria=criteria,
            law_receipt=law_receipt,
        ),
        worktree=worktree,
        branch=branch,
        acceptance_criteria=criteria,
    )
    result.update(
        {
            "source": (Path(".p2p") / "state" / "task-state.json").as_posix(),
            "task_id": planned.get("task_id", UNKNOWN),
            "plan_hash": planned.get("plan_hash", UNKNOWN),
        }
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = _root(args)
        # Supreme Law self-preflight is deliberately before ControlTower construction,
        # fresh-state projection, prompt planning, or any other substantive CT action.
        law_receipt = _establish_control_tower_law_context(root)
        tower = ControlTower(
            root,
            current_canonical_base_sha=args.current_canonical_base_sha,
            current_canonical_base_tree=args.current_canonical_base_tree,
        )
        if args.command == "start":
            binding = SessionBinding(
                session_id=args.session_id or new_session_id(args.host, args.goal_id, args.task_id),
                host=args.host,
                goal_id=args.goal_id,
                goal=args.goal,
            )
            criteria = tuple(args.acceptance_criterion)
            result = tower.start_session(
                binding,
                task_id=args.task_id,
                task_prompt=_contextual_task_for_session(
                    root,
                    binding,
                    args.goal,
                    worktree=args.worktree,
                    branch=args.branch,
                    canonical_base_sha=args.canonical_base_sha,
                    canonical_base_tree=args.canonical_base_tree,
                    acceptance_criteria=criteria,
                    law_receipt=law_receipt,
                ),
                canonical_base_sha=args.canonical_base_sha,
                canonical_base_tree=args.canonical_base_tree,
                worktree=args.worktree,
                branch=args.branch,
                acceptance_criteria=criteria,
            )
        elif args.command == "snapshot":
            result = {"status": "PASS", "snapshot": tower.snapshot()}
        elif args.command == "ingest":
            response_path = Path(args.response_file).expanduser().resolve()
            result = tower.ingest_response(
                response_path.read_text(encoding="utf-8"),
                current_canonical_base_sha=args.current_canonical_base_sha,
                current_canonical_base_tree=args.current_canonical_base_tree,
            )
        elif args.command == "next":
            result = _start_next_with_context(
                tower,
                root,
                args.host,
                session_id=args.session_id,
                worktree=args.worktree,
                branch=args.branch,
                law_receipt=law_receipt,
            )
        else:  # pragma: no cover - argparse constrains this branch.
            raise BindingError(f"UNSUPPORTED_COMMAND:{args.command}")
        if not isinstance(result, dict):
            raise BindingError("CONTROL_TOWER_RESULT_MUST_BE_OBJECT")
        result["control_tower_self_law_receipt"] = dict(law_receipt)
        _print_result(result, as_json=args.as_json)
        return 0
    except (ControlTowerHandoffError, OSError, UnicodeError) as exc:
        print(f"CONTROL_TOWER_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())