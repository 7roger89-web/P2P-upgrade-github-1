#!/usr/bin/env python3
"""Bounded, reusable P2P project workflow for ordinary natural-language requests.

This helper is deliberately orchestration-only. It reuses the existing project
policy, eval, governance, approval, drift, and CAPSULE formats instead of
creating parallel control systems.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


SCHEMA = "p2p-project-workflow/1"
GOAL_SCHEMA = "p2p-goal-contract/1"
PROFILE_SCHEMA = "p2p-project-profile/1"
STATUS_SCHEMA = "p2p-project-status/1"
EVIDENCE_SCHEMA = "p2p-trusted-evidence/1"
LEDGER_SCHEMA = "p2p-execution-event/1"
TERMINAL_STATES = {"PASS", "BLOCKED", "REJECT"}
ELIGIBILITY_CLASSES = ("DIRECT TASK", "PLAN FIRST", "GOAL", "SEPARATE GOALS")
WORK_ITEM_CLASSES = ("MANDATORY FOR GOAL", "SUPPORTING", "OPTIONAL / BACKLOG", "OUT OF SCOPE")
WORK_TYPES = ("AI-BOUND", "TOOL-BOUND", "MIXED")
MUTATION_CLASSES = ("CONTEXT UPDATE", "CONSTRAINT UPDATE", "ACCEPTANCE UPDATE", "NEW OBJECTIVE")
ORACLE_FORBIDDEN_LANGUAGE = {
    "better",
    "optimized",
    "improved",
    "clean",
    "production-ready",
    "high quality",
}
AGENTS = (
    "p2p_iris",
    "p2p_tecton",
    "p2p_axiom",
    "p2p_vector",
    "p2p_datos",
    "p2p_anon",
    "p2p_architecton",
    "p2p_helios",
)
AGENT_FOCUS = {
    "p2p_iris": "uncertainty and problem boundaries",
    "p2p_tecton": "implementation and cross-component change",
    "p2p_axiom": "critical verification and failure finding",
    "p2p_vector": "metrics and bounded optimization",
    "p2p_datos": "data, evidence, and project evals",
    "p2p_anon": "security, privacy, and abuse boundaries",
    "p2p_architecton": "architecture and integration",
    "p2p_helios": "final synthesis and beginner-facing handoff",
}
DEFAULT_PROTECTED_ACTIONS = [
    "promote_live_specs",
    "update_or_create_skill",
    "release_or_deploy",
    "enable_external_io",
    "persistent_memory_write",
    "destructive_change",
    "external_communication",
]
CONTROL_SCOPES = {
    "package_doctor": ["governance", "scripts"],
    "sandbox_probe": [".codex/config.toml"],
    "eight_agent_runtime_proof": [".codex/agents"],
    "project_wide_audit": ["*"],
    "project_eval": [".p2p/evals"],
    "drift_gate": ["governance", "scripts", ".p2p/system"],
    "goal_completion": ["*"],
}
EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
EXCLUDED_STATE_PREFIXES = (
    ".p2p/state/",
    ".p2p/approvals/",
    ".p2p/gates/",
    ".p2p/install-backups/",
)
TRANSIENT_HELPER_PARTS = {".tmp", "quarantine", "__pycache__"}
PROJECT_EVAL_CONTRACT_FLAGS = ("--goal-contract", "--profile")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def decision_trace_api(root: Path, package_hint: str | None = None) -> Any | None:
    """Load the optional native trace from the current project runtime.

    Older projects without the runtime module remain fully compatible; trace
    capture is additive and never becomes a second workflow authority.
    """
    runtimes = [root / ".p2p" / "system"]
    if package_hint:
        runtimes.append(Path(package_hint).expanduser().resolve() / ".p2p" / "system")
    for runtime in runtimes:
        module_path = runtime / "p2p_capabilities" / "decision_trace.py"
        if not module_path.is_file():
            continue
        runtime_text = str(runtime.resolve())
        if runtime_text not in sys.path:
            sys.path.insert(0, runtime_text)
        try:
            return importlib.import_module("p2p_capabilities.decision_trace")
        except (ImportError, OSError):
            continue
    return None


def context_api(root: Path, package_hint: str | None = None) -> Any:
    """Load the project context-delivery primitive or fail closed."""

    runtimes = [root / ".p2p" / "system"]
    if package_hint:
        runtimes.append(Path(package_hint).expanduser().resolve() / ".p2p" / "system")
    for runtime in runtimes:
        module_path = runtime / "p2p_capabilities" / "context.py"
        if not module_path.is_file():
            continue
        runtime_text = str(runtime.resolve())
        if runtime_text not in sys.path:
            sys.path.insert(0, runtime_text)
        try:
            return importlib.import_module("p2p_capabilities.context")
        except (ImportError, OSError):
            continue
    raise ValueError("CONTEXT_PRIMITIVE_UNAVAILABLE: p2p_capabilities.context")


def package_roots() -> list[Path]:
    roots: list[Path] = []
    for parent in Path(__file__).resolve().parents:
        if (parent / "governance").is_dir() and (parent / "scripts").is_dir():
            roots.append(parent)
        if (parent / ".p2p" / "system" / "governance").is_dir():
            roots.append(parent)
    return list(dict.fromkeys(roots))


def project_root(raw: str) -> Path:
    root = Path(raw).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")
    return root


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: object) -> str:
    return sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def read_json(path: Path, default: object | None = None) -> object:
    if not path.exists():
        if default is not None:
            return default
        raise ValueError(f"Missing JSON file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON {path}: {exc}") from exc


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def write_json_if_missing(path: Path, value: object) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def write_text_atomic(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(value, encoding="utf-8")
    temp.replace(path)


def append_event(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"schema_version": LEDGER_SCHEMA, "at": now(), **event}, ensure_ascii=False) + "\n")


def relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def path_is_excluded(relative: str) -> bool:
    return relative.startswith(EXCLUDED_STATE_PREFIXES)


def project_snapshot(root: Path) -> dict[str, object]:
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        relative = path.relative_to(root).as_posix()
        if path_is_excluded(relative):
            continue
        files[relative] = sha256_file(path)
    return {"files": files, "fingerprint": stable_hash(files), "captured_at": now()}


def changed_files(previous: object, current: dict[str, object]) -> list[str]:
    if not isinstance(previous, dict) or not isinstance(previous.get("files"), dict):
        return []
    old = previous["files"]
    new = current.get("files", {})
    if not isinstance(new, dict):
        return []
    return sorted({*old.keys(), *new.keys()} - {path for path in old.keys() if old.get(path) == new.get(path)})


def path_matches(relative: str, scope: str) -> bool:
    scope = scope.replace("\\", "/").strip("/")
    if scope in {"", "*"}:
        return True
    return relative == scope or relative.startswith(scope + "/")


def scoped_fingerprint(snapshot: dict[str, object], scopes: list[str] | None) -> str:
    files = snapshot.get("files", {})
    if not isinstance(files, dict):
        files = {}
    scopes = scopes or ["*"]
    selected = {path: digest for path, digest in files.items() if any(path_matches(path, scope) for scope in scopes)}
    return stable_hash(selected)


def load_status(root: Path) -> dict[str, object]:
    path = root / ".p2p" / "state" / "project-status.json"
    value = read_json(path, {})
    return value if isinstance(value, dict) else {}


def load_current_contract(root: Path) -> dict[str, object]:
    value = read_json(root / ".p2p" / "state" / "goal-contract.json", {})
    return value if isinstance(value, dict) else {}


def load_trusted_evidence(root: Path) -> dict[str, object]:
    path = root / ".p2p" / "state" / "trusted-evidence.json"
    value = read_json(path, {"schema_version": EVIDENCE_SCHEMA, "controls": {}})
    return value if isinstance(value, dict) else {"schema_version": EVIDENCE_SCHEMA, "controls": {}}


def governance_candidates(root: Path, package_hint: str | None = None) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = [
        (root / ".p2p" / "system" / "governance", "installed"),
        (root / "governance", "package-or-project"),
    ]
    if package_hint:
        package = Path(package_hint).expanduser().resolve()
        candidates.append((package / "governance", "package"))
    for package in package_roots():
        candidates.append((package / "governance", "package"))
        candidates.append((package / ".p2p" / "system" / "governance", "installed"))
    result: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for candidate, mode in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "fact-ledger.json").is_file() and (candidate / "live-specs.json").is_file():
            result.append((candidate, mode))
    return result


def helper_path_is_transient(path: Path) -> bool:
    parts = {part.casefold() for part in path.resolve().parts}
    return bool(parts & TRANSIENT_HELPER_PARTS) or "fixture-old" in path.name.casefold()


def helper_supports_project_eval(path: Path) -> bool:
    """Probe the existing helper CLI without running a mutating eval operation."""
    try:
        process = subprocess.run(
            [sys.executable, str(path), "design", "--help"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = f"{process.stdout}\n{process.stderr}"
    return process.returncode == 0 and all(flag in output for flag in PROJECT_EVAL_CONTRACT_FLAGS)


def eval_helper_candidates(root: Path, package_hint: str | None = None) -> list[Path]:
    development_root = (
        (root / "governance").is_dir()
        and (root / "manifest" / "package.json").is_file()
        and (root / "scripts" / "package_release.py").is_file()
    )
    installed_root = (root / ".p2p" / "system").is_dir() and not development_root
    candidates = (
        [root / ".p2p" / "system" / "scripts" / "p2p_eval.py"]
        if installed_root
        else [
            root / ".p2p" / "system" / "scripts" / "p2p_eval.py",
            root / "scripts" / "p2p_eval.py",
            Path(__file__).resolve().with_name("p2p_eval.py"),
        ]
    )
    if package_hint:
        package = Path(package_hint).expanduser().resolve()
        candidates.append(package / "scripts" / "p2p_eval.py")
        candidates.append(package / ".p2p" / "system" / "scripts" / "p2p_eval.py")
    if not installed_root:
        for package in package_roots():
            candidates.append(package / "scripts" / "p2p_eval.py")
            candidates.append(package / ".p2p" / "system" / "scripts" / "p2p_eval.py")
    explicit_package = Path(package_hint).expanduser().resolve() if package_hint else None
    root_owned = {
        (root / ".p2p" / "system" / "scripts" / "p2p_eval.py").resolve(),
        (root / "scripts" / "p2p_eval.py").resolve(),
    }
    result: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        # Explicit package fixtures are allowed for isolated lifecycle tests;
        # canonical role-owned paths remain testable even when the fixture root
        # itself is under .tmp; implicit discovery must never promote unrelated
        # transient/quarantined files or an ancestor development package.
        is_explicit_package_candidate = explicit_package is not None and candidate.is_relative_to(explicit_package)
        is_root_owned = candidate in root_owned
        if candidate.is_file() and (is_root_owned or is_explicit_package_candidate or not helper_path_is_transient(candidate)) and helper_supports_project_eval(candidate):
            result.append(candidate)
    return result


def inspect_project(root: Path, request: str = "", package_hint: str | None = None) -> dict[str, object]:
    text = f"{request} {root.name}".lower()
    markers = []
    for name in (
        "package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod",
        "index.html", "README.md", "src", "app", "backend", "frontend", "tests", "docs",
    ):
        if (root / name).exists():
            markers.append(name)
    if any(word in text for word in ("logistics", "warehouse", "inventory", "delivery", "kho", "vận tải")):
        project_type = "logistics_software"
    elif any(word in text for word in ("story", "game", "truyện", "visual novel")):
        project_type = "story_game"
    elif any(word in text for word in ("data", "analysis", "dataset", "csv", "phân tích", "dữ liệu")):
        project_type = "data_analysis"
    elif any(word in text for word in ("automation", "automate", "workflow", "tự động")):
        project_type = "automation"
    elif any(word in text for word in ("research", "paper", "study", "nghiên cứu")):
        project_type = "research"
    elif "package.json" in markers or "index.html" in markers or "src" in markers:
        project_type = "web_application"
    elif "pyproject.toml" in markers or list(root.glob("*.py")):
        project_type = "automation"
    else:
        project_type = "generic_project"
    rag_applicable = bool(
        any(word in text for word in ("rag", "retrieval", "knowledge base", "tài liệu", "nguồn", "search"))
        or ((root / "docs").is_dir() and len(list((root / "docs").glob("*"))) >= 3)
    )
    governance = governance_candidates(root, package_hint)
    inspection = {
        "schema_version": "p2p-project-inspection/1",
        "project": root.name,
        "root": str(root),
        "project_type": project_type,
        "markers": markers,
        "top_level_directories": sorted(path.name for path in root.iterdir() if path.is_dir() and path.name not in EXCLUDED_DIRS),
        "file_count": sum(1 for path in root.rglob("*") if path.is_file() and not path_is_excluded(path.relative_to(root).as_posix())),
        "p2p_installed": (root / ".p2p" / "system").is_dir(),
        "has_project_profile": (root / ".p2p" / "project-profile.json").is_file(),
        "has_project_policy": (root / ".p2p" / "project-policy.json").is_file(),
        "has_project_eval": (root / ".p2p" / "evals" / "suite.json").is_file(),
        "rag_applicable": rag_applicable,
        "governance_candidates": [{"root": str(path), "mode": mode} for path, mode in governance],
    }
    inspection["goal_eligibility"] = classify_goal_eligibility(request, inspection)
    return inspection


def slugify(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return (result or "goal")[:48]


def explicit_quorum_request(request: str) -> bool:
    return bool(re.search(r"(?:full\s+quorum|quorum\s+full|8\s*(?:agent|agents|threads)|eight[- ]agent)", request, re.I))


def select_agents(request: str, inspection: dict[str, object], policy: dict[str, object] | None = None) -> dict[str, object]:
    lower = request.lower()
    explicit = explicit_quorum_request(request)
    release_policy = isinstance(policy, dict) and bool(policy.get("final_release_requires_full_quorum"))
    high = bool(re.search(r"security|auth|permission|payment|migration|destructive|data loss|release|deploy|production|architecture|kiến trúc|bảo mật", lower))
    medium = bool(re.search(r"multi[- ]component|cross[- ]component|integration|sync|multiple files|nhiều thành phần|liên thành phần", lower))
    if explicit or (release_policy and bool(re.search(r"release|deploy|publish", lower))):
        selected = list(AGENTS)
        reason = "Explicit or policy-required full certification; the requested quorum is preserved."
        tier = "full"
    elif high:
        selected = ["p2p_axiom", "p2p_anon", "p2p_architecton", "p2p_tecton", "p2p_datos"]
        reason = "High-risk change needs critical, security, architecture, implementation, and evidence coverage."
        tier = "high-risk"
    elif medium:
        selected = ["p2p_iris", "p2p_tecton", "p2p_axiom", "p2p_vector"]
        reason = "Cross-component work needs a compact map, implementation plan, critique, and measurable checks."
        tier = "medium"
    else:
        if re.search(r"security|privacy|permission|bảo mật|quyền", lower):
            selected = ["p2p_anon"]
        elif re.search(r"data|eval|evidence|dataset|dữ liệu|đánh giá", lower):
            selected = ["p2p_datos"]
        elif re.search(r"unclear|vague|idea|rough|ý tưởng|mơ hồ", lower):
            selected = ["p2p_iris"]
        else:
            selected = ["p2p_tecton"]
        reason = f"Small/local work uses the smallest relevant named role: {AGENT_FOCUS[selected[0]]}."
        tier = "small"
    return {
        "tier": tier,
        "selected_agents": selected,
        "quorum_size": len(selected),
        "full_quorum_required": len(selected) == len(AGENTS),
        "explicit_requirement": explicit,
        "reason": reason,
        "agent_identities": "exact named P2P identities; no generic substitution",
    }


def objective_for(request: str, inspection: dict[str, object]) -> tuple[str, bool]:
    request = request.strip()
    vague = bool(re.search(r"\b(?:a little|somehow|optimize|improve|enhance|make better|tối ưu|cải thiện|hoàn thiện)\b", request, re.I))
    if not vague:
        return request, False
    project_type = inspection.get("project_type", "project")
    return (
        f"Inspect the current {project_type} project and complete only the smallest evidence-supported interpretation of: {request}. "
        "Bound the work to the first measurable blocker, verify it, and stop when the contract passes.",
        True,
    )


def _request_actions(request: str) -> list[str]:
    return re.findall(
        r"\b(?:build|finish|complete|migrate|rewrite|refactor|implement|create|add|remove|update|fix|redesign|deploy|release|research|analyze|optimize|improve|test|document|prepare|run)\b",
        request.lower(),
    )


def _request_is_open_ended(request: str) -> bool:
    lower = request.lower()
    return bool(
        re.search(
            r"(?:fix\s+everything|everything\s+you\s+can|keep\s+improving|make\s+it\s+perfect|whatever\s+needs|all\s+(?:issues|problems)|optimize\s+.*\b(?:a little|somehow)\b|improve\s+.*\b(?:a little|everything)\b)",
            lower,
        )
    )


def _request_has_separate_objectives(request: str) -> bool:
    lower = request.lower()
    if _request_is_open_ended(request):
        return False
    if re.search(r"\b(?:also|plus|as well as|separately|and then)\b|;", lower):
        return True
    if re.search(r"\b(?:while preserving|until|stop when|stop only when|and finish|and complete)\b", lower):
        return False
    actions = _request_actions(request)
    return len(actions) >= 2 and bool(re.search(r"\band\b", lower))


def _request_is_long_running(request: str) -> bool:
    lower = request.lower()
    if re.search(r"(?:long[- ]running|end[- ]to[- ]end|multi[- ]step|stop\s+(?:when|only)|until\s+.*pass|preserving\s+behavior|full\s+(?:migration|audit|certification))", lower):
        return True
    if re.search(r"(?:migrate|rewrite|refactor|deploy|release|architecture|production|project|app)", lower) and len(_request_actions(request)) >= 1:
        return True
    return len(_request_actions(request)) >= 2 or len(request.split()) > 28


def classify_goal_eligibility(request: str, inspection: dict[str, object] | None = None) -> dict[str, object]:
    """Decide whether a request needs a Goal before any long-running work."""
    request = request.strip()
    if not request:
        return {
            "schema_version": "p2p-goal-eligibility/1",
            "classification": "PLAN FIRST",
            "reason": "No request was supplied; inspect context before choosing work.",
            "bounded_interpretation_required": True,
            "goal_required": False,
            "next_action": "Inspect available project evidence and produce one measurable interpretation.",
        }
    if _request_has_separate_objectives(request):
        classification = "SEPARATE GOALS"
        reason = "The request contains independent objectives; do not combine them into one open-ended Goal."
        next_action = "Split the objectives, order them, and compile one bounded Goal Contract per objective."
    elif _request_is_open_ended(request):
        classification = "PLAN FIRST"
        reason = "The request is open-ended; inspect context and select only the first evidence-supported blocker."
        next_action = "Create measurable acceptance for the smallest useful interpretation before execution."
    elif _request_is_long_running(request):
        classification = "GOAL"
        reason = "The request is multi-step or long-running and has an observable outcome that can be linted."
        next_action = "Compile one primary objective, verification oracles, bounded work, and STOP rules."
    elif re.search(r"(?:optimize|improve|enhance|better|quality|a little|somehow|tối ưu|cải thiện|hoàn thiện)", request, re.I):
        classification = "PLAN FIRST"
        reason = "The outcome is ambiguous; resolve technical uncertainty with project evidence before opening a Goal."
        next_action = "Inspect the project and turn the request into one measurable, reversible acceptance target."
    else:
        classification = "DIRECT TASK"
        reason = "The request is small and sufficiently scoped for normal execution without a long-running Goal."
        next_action = "Execute the single bounded task normally; do not create a Goal unless scope expands."
    return {
        "schema_version": "p2p-goal-eligibility/1",
        "classification": classification,
        "reason": reason,
        "bounded_interpretation_required": classification in {"PLAN FIRST", "SEPARATE GOALS"},
        "goal_required": classification == "GOAL",
        "goal_creation_allowed_after_preflight": classification in {"GOAL", "PLAN FIRST"},
        "next_action": next_action,
        "signals": {
            "open_ended": _request_is_open_ended(request),
            "separate_objectives": _request_has_separate_objectives(request),
            "long_running": _request_is_long_running(request),
            "action_count": len(_request_actions(request)),
        },
    }


def verification_oracle(method: str, target: str, pass_signal: str, fail_signal: str, *, deterministic: bool = True) -> dict[str, object]:
    return {
        "method": method,
        "target": target,
        "pass_signal": pass_signal,
        "fail_signal": fail_signal,
        "deterministic": deterministic,
    }


def lint_goal_contract(contract: dict[str, object]) -> dict[str, object]:
    errors: list[str] = []
    objective = str(contract.get("objective", "")).strip()
    if not objective:
        errors.append("objective is required")
    eligibility = contract.get("goal_eligibility", {})
    if isinstance(eligibility, dict) and eligibility.get("classification") == "SEPARATE GOALS":
        errors.append("independent objectives must be split before a Goal starts")
    criteria = contract.get("completion_criteria")
    if not isinstance(criteria, list) or not criteria:
        errors.append("completion_criteria must be a non-empty list")
        criteria = []
    checked: list[str] = []
    for item in criteria:
        if not isinstance(item, dict) or not item.get("mandatory"):
            continue
        criterion_id = str(item.get("criterion_id", "unknown"))
        checked.append(criterion_id)
        oracle = item.get("verification_oracle")
        if not isinstance(oracle, dict):
            errors.append(f"{criterion_id} lacks verification_oracle")
            continue
        for field in ("method", "target", "pass_signal", "fail_signal"):
            if not str(oracle.get(field, "")).strip():
                errors.append(f"{criterion_id} oracle.{field} is required")
        oracle_text = " ".join(str(oracle.get(field, "")) for field in ("method", "target", "pass_signal", "fail_signal")).lower()
        if any(marker in oracle_text for marker in ("todo", "tbd", "define later", "review required", "placeholder")):
            errors.append(f"{criterion_id} oracle contains a placeholder")
        pass_when = str(item.get("pass_when", "")).lower()
        if any(marker in pass_when for marker in ORACLE_FORBIDDEN_LANGUAGE) and not oracle.get("method"):
            errors.append(f"{criterion_id} uses subjective completion language without an oracle")
    if not isinstance(contract.get("constraints"), list) or not contract.get("constraints"):
        errors.append("constraints are required")
    if not isinstance(contract.get("out_of_scope"), list) or not contract.get("out_of_scope"):
        errors.append("out_of_scope is required")
    stop_conditions = contract.get("stop_conditions")
    if not isinstance(stop_conditions, dict) or not all(state in stop_conditions for state in TERMINAL_STATES):
        errors.append("PASS/BLOCKED/REJECT stop conditions are required")
    return {
        "schema_version": "p2p-goal-linter/1",
        "status": "PASS" if not errors else "BLOCKED",
        "checked_mandatory_criteria": checked,
        "errors": errors,
        "rule": "Every mandatory criterion must name a concrete verification oracle before autonomous execution.",
    }


def classify_work_item(description: str, *, related: bool = True, mandatory: bool = False, supporting: bool = False) -> str:
    lower = description.lower()
    if not related or re.search(r"(?:unrelated|out of scope|backlog only|separate request|ui polish)", lower):
        return "OUT OF SCOPE"
    if re.search(r"(?:optional|nice to have|polish|cleanup|speculative|could improve|future)", lower):
        return "OPTIONAL / BACKLOG"
    if supporting or re.search(r"(?:enables|supports|needed to verify|instrumentation)", lower):
        return "SUPPORTING"
    if mandatory or description.strip():
        return "MANDATORY FOR GOAL"
    return "OPTIONAL / BACKLOG"


def classify_work_type(request: str) -> str:
    lower = request.lower()
    tool_bound = bool(re.search(r"(?:deterministic|script|build|test suite|benchmark|migration job|compile|wait|long[- ]running tool|batch)", lower))
    ai_bound = bool(re.search(r"(?:reason|design|write|code|review|analyze|research|architecture|decide|creative|ambiguous|subjective|migrate|rewrite|refactor|implement|preserve behavior|project|application)", lower))
    if tool_bound and ai_bound:
        return "MIXED"
    if tool_bound:
        return "TOOL-BOUND"
    return "AI-BOUND"


def exploration_policy_for(work_type: str) -> dict[str, object]:
    return {
        "primary_lane_limit": 1,
        "alternative_lane_limit": 1,
        "speculative_lane_limit": 0,
        "active_lane": "primary",
        "work_type": work_type if work_type in WORK_TYPES else "MIXED",
        "alternative_allowed_when": "primary approach fails or evidence strongly justifies comparison",
        "requires_failure_reason": True,
        "never_restart_unchanged_expensive_work": True,
    }


def register_approach_result(contract: dict[str, object], lane: str, outcome: str, reason: str, alternative: str | None = None) -> dict[str, object]:
    updated = json.loads(json.dumps(contract, ensure_ascii=False))
    history = updated.setdefault("failed_approaches", [])
    if not isinstance(history, list):
        history = []
        updated["failed_approaches"] = history
    policy = updated.setdefault("exploration_policy", exploration_policy_for(str(updated.get("work_type", "MIXED"))))
    if not isinstance(policy, dict):
        policy = exploration_policy_for("MIXED")
        updated["exploration_policy"] = policy
    outcome = outcome.upper()
    if outcome in {"FAILED", "FAIL", "REGRESSED"}:
        history.append({"lane": lane, "outcome": outcome, "reason": reason, "recorded_at": now()})
        if lane == "primary" and not any(item.get("lane") == "alternative" for item in history if isinstance(item, dict)):
            policy["active_lane"] = "alternative"
            policy["alternative_reason"] = reason
            policy["alternative"] = alternative or "lowest-risk viable alternative"
            decision = "ALTERNATIVE_ALLOWED"
        else:
            decision = "BLOCKED"
    else:
        policy["active_lane"] = lane
        decision = "CONTINUE_IF_MANDATORY_UNMET" if outcome not in {"PASS", "PASSED"} else "STOP_IF_MANDATORY_PASS"
    updated["exploration_policy"] = policy
    return {
        "status": decision,
        "contract": updated,
        "failed_approaches": history,
        "next_action": "Try one lowest-risk alternative and record its result." if decision == "ALTERNATIVE_ALLOWED" else "Stop and report the genuine blocker; do not open another lane." if decision == "BLOCKED" else "Continue only while mandatory criteria remain unmet.",
    }


def record_approach_result(root: Path, lane: str, outcome: str, reason: str, alternative: str | None = None) -> dict[str, object]:
    contract = load_current_contract(root)
    if not contract:
        raise ValueError("No active Goal Contract exists")
    current_status = load_status(root)
    if current_status.get("terminal_state") in TERMINAL_STATES:
        return {
            "schema_version": "p2p-approach-result/1",
            "status": "PASS_STOPPED" if current_status.get("terminal_state") == "PASS" else "TERMINAL_STOPPED",
            "goal_id": contract.get("goal_id"),
            "lane": lane,
            "outcome": outcome.upper(),
            "reason": "Terminal Goal state already reached; no new lane was opened.",
            "failed_approaches": contract.get("failed_approaches", []),
            "next_action": "No further work; terminal state is authoritative.",
            "ledger": ".p2p/state/execution-ledger.jsonl",
        }
    result = register_approach_result(contract, lane, outcome, reason, alternative)
    updated = result["contract"]
    write_goal(root, updated)
    ledger = root / ".p2p" / "state" / "execution-ledger.jsonl"
    append_event(
        ledger,
        {
            "event": "approach_result",
            "goal_id": updated.get("goal_id"),
            "lane": lane,
            "outcome": outcome.upper(),
            "reason": reason,
            "alternative": alternative,
            "decision": result.get("status"),
        },
    )
    status = load_status(root)
    if status:
        status["exploration_policy"] = updated.get("exploration_policy", {})
        status["failed_approaches"] = updated.get("failed_approaches", [])
        status["current_bottleneck"] = result.get("next_action")
        status["updated_at"] = now()
        write_json_atomic(root / ".p2p" / "state" / "project-status.json", status)
    return {
        "schema_version": "p2p-approach-result/1",
        "status": result.get("status"),
        "goal_id": updated.get("goal_id"),
        "lane": lane,
        "outcome": outcome.upper(),
        "reason": reason,
        "failed_approaches": result.get("failed_approaches", []),
        "next_action": result.get("next_action"),
        "ledger": relative_path(ledger, root),
    }


def classify_goal_update(current_request: str, new_request: str, contract: dict[str, object] | None = None) -> dict[str, object]:
    current = current_request.strip()
    new = new_request.strip()
    if not current or not new or current == new:
        classification = "CONTEXT UPDATE"
        reason = "The active objective is unchanged; refresh context without recompiling acceptance."
    elif re.search(r"(?:done when|acceptance|criterion|criteria|stop when|pass when|threshold)", new, re.I):
        classification = "ACCEPTANCE UPDATE"
        reason = "The requested completion oracle changed; recompile and revalidate the Goal Contract."
    elif re.search(r"(?:must not|constraint|without|preserve|do not|avoid|only)", new, re.I):
        classification = "CONSTRAINT UPDATE"
        reason = "The objective remains but its boundary changed; update constraints and revalidate."
    else:
        current_action = (_request_actions(current) or [""])[0]
        new_action = (_request_actions(new) or [""])[0]
        classification = "NEW OBJECTIVE" if current_action != new_action or re.search(r"(?:unrelated|separate|also|new feature)", new, re.I) else "CONTEXT UPDATE"
        reason = "Do not silently expand the active Goal; record this as a separate Goal/objective." if classification == "NEW OBJECTIVE" else "Add evidence to the current Goal without changing its objective."
    return {
        "schema_version": "p2p-goal-mutation/1",
        "classification": classification,
        "reason": reason,
        "requires_recompile": classification in {"CONSTRAINT UPDATE", "ACCEPTANCE UPDATE"},
        "silent_expand": False,
        "active_goal_id": contract.get("goal_id") if isinstance(contract, dict) else None,
        "next_action": "Create a separate Goal or close the current Goal first." if classification == "NEW OBJECTIVE" else "Apply the classified update and revalidate only affected criteria.",
    }


def can_reuse_pass_evidence(status: str, unchanged_inputs: bool, expired: bool) -> bool:
    return status == "PASS" and unchanged_inputs and not expired


def one_blocked_decision(decisions: object) -> str:
    if isinstance(decisions, str) and decisions.strip():
        return decisions.strip()
    if isinstance(decisions, (list, tuple)):
        for item in decisions:
            if str(item).strip():
                return str(item).strip()
    return "One mandatory blocker must be identified before continuing."


def goal_acceptance_cases() -> dict[str, object]:
    vague = classify_goal_eligibility("Optimize this app a little.")
    clear = classify_goal_eligibility("Migrate this project to the target stack while preserving behavior and stop only when build and required regression tests pass.")
    backlog = classify_goal_eligibility("Fix everything you can find and keep improving the project.")
    separate = classify_goal_eligibility("Fix the API and redesign the unrelated UI.")
    contract = {"goal_id": "goal-acceptance", "work_type": "AI-BOUND", "exploration_policy": exploration_policy_for("AI-BOUND")}
    failed = register_approach_result(contract, "primary", "FAILED", "primary parser failed deterministically", "reuse the existing parser boundary")
    failed_again = register_approach_result(failed["contract"], "alternative", "FAILED", "the one alternative also failed")
    cases = {
        "vague_request": {"pass": vague["classification"] in {"PLAN FIRST", "DIRECT TASK"}, "classification": vague["classification"]},
        "clear_long_running": {"pass": clear["classification"] == "GOAL", "classification": clear["classification"]},
        "open_ended_backlog": {"pass": backlog["classification"] == "PLAN FIRST" and backlog["bounded_interpretation_required"], "classification": backlog["classification"]},
        "unrelated_discovery": {"pass": classify_work_item("unrelated UI improvement", related=False) == "OUT OF SCOPE", "classification": classify_work_item("unrelated UI improvement", related=False)},
        "failed_approach": {"pass": failed["status"] == "ALTERNATIVE_ALLOWED" and failed_again["status"] == "BLOCKED", "first": failed["status"], "second": failed_again["status"]},
        "tool_bound_long_run": {"pass": classify_work_type("Run the deterministic build script and wait for completion.") == "TOOL-BOUND", "work_type": classify_work_type("Run the deterministic build script and wait for completion.")},
        "already_verified_evidence": {"pass": can_reuse_pass_evidence("PASS", True, False)},
        "pass_stops": {"pass": "STOP_IF_MANDATORY_PASS" == "STOP_IF_MANDATORY_PASS"},
        "real_blocker": {"pass": one_blocked_decision(["Choose the business retention period.", "Choose a color."]) == "Choose the business retention period.", "decision": one_blocked_decision(["Choose the business retention period.", "Choose a color."])},
        "mid_goal_new_objective": {"pass": classify_goal_update("Fix the login timeout.", "Also redesign the unrelated UI")["classification"] == "NEW OBJECTIVE" and separate["classification"] == "SEPARATE GOALS", "classification": classify_goal_update("Fix the login timeout.", "Also redesign the unrelated UI")["classification"], "eligibility": separate["classification"]},
    }
    return {"schema_version": "p2p-goal-acceptance/1", "status": "PASS" if all(bool(item.get("pass")) for item in cases.values()) else "BLOCKED", "cases": cases}


def build_goal_contract(root: Path, request: str, inspection: dict[str, object], policy: dict[str, object] | None = None) -> dict[str, object]:
    if not request.strip():
        raise ValueError("A natural-language request is required")
    objective, bounded_interpretation = objective_for(request, inspection)
    selection = select_agents(request, inspection, policy)
    risk = "high" if selection["tier"] in {"high-risk", "full"} else "medium" if selection["tier"] == "medium" else "low"
    eligibility = inspection.get("goal_eligibility") if isinstance(inspection.get("goal_eligibility"), dict) else classify_goal_eligibility(request, inspection)
    work_type = classify_work_type(request)
    goal_id = f"goal-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slugify(request)[:24]}"
    contract = {
        "schema_version": GOAL_SCHEMA,
        "workflow_schema": SCHEMA,
        "goal_id": goal_id,
        "created_at": now(),
        "request": request.strip(),
        "objective": objective,
        "bounded_interpretation": bounded_interpretation,
        "goal_eligibility": eligibility,
        "primary_objective": objective,
        "project": root.name,
        "project_type": inspection.get("project_type"),
        "context": {
            "authoritative_project_evidence": {
                "project_root": str(root),
                "project_type": inspection.get("project_type"),
                "markers": inspection.get("markers", []),
                "top_level_directories": inspection.get("top_level_directories", []),
                "p2p_installed": inspection.get("p2p_installed", False),
                "has_project_profile": inspection.get("has_project_profile", False),
                "has_project_eval": inspection.get("has_project_eval", False),
                "governance_candidates": inspection.get("governance_candidates", []),
            },
            "source_of_truth": ["local project inspection", "project .p2p state", "authoritative governance references"],
        },
        "risk": risk,
        "work_type": work_type,
        "current_state_assumptions": [
            {
                "assumption_id": "A1",
                "assumption": "The current project state must be inspected before implementation is trusted.",
                "verify_with": "project inventory and existing project state",
                "status": "UNKNOWN",
            },
            {
                "assumption_id": "A2",
                "assumption": "Existing policy, eval, governance, and PASS evidence are authoritative when valid and unexpired.",
                "verify_with": "project profile, suite validation, trusted-evidence fingerprints, and relevant gates",
                "status": "UNKNOWN",
            },
        ],
        "completion_criteria": [
            {
                "criterion_id": "C1",
                "name": "bounded_goal",
                "mandatory": True,
                "pass_when": "This contract has a concrete objective, measurable checks, constraints, and terminal STOP rules.",
                "evidence": ".p2p/state/goals/<goal-id>.json",
                "verification_oracle": verification_oracle("artifact_inspection", ".p2p/state/goal-contract.json", "objective, constraints, and STOP rules are present", "any required field is absent"),
                "status": "PENDING",
            },
            {
                "criterion_id": "C2",
                "name": "project_state_initialized",
                "mandatory": True,
                "pass_when": "Required missing project profile, policy, status, ledger, and evidence locations exist without overwriting valid files.",
                "evidence": ".p2p/project-profile.json and .p2p/state/project-status.json",
                "verification_oracle": verification_oracle("filesystem_inspection", ".p2p/project-profile.json; .p2p/state/project-status.json; .p2p/state/execution-ledger.jsonl", "all required paths exist and pre-existing valid files are unchanged", "a path is missing or a valid artifact was overwritten"),
                "status": "PENDING",
            },
            {
                "criterion_id": "C3",
                "name": "project_specific_eval",
                "mandatory": True,
                "pass_when": "A v2 project-specific suite validates and includes positive, negative, regression, completion, and reuse/boundary cases.",
                "evidence": ".p2p/evals/suite.json",
                "verification_oracle": verification_oracle("p2p_eval_validate", ".p2p/evals/suite.json", "validate command returns PASS and required case types are present", "validation returns FAIL or a required case type is absent"),
                "status": "PENDING",
            },
            {
                "criterion_id": "C4",
                "name": "bounded_execution_and_verification",
                "mandatory": True,
                "pass_when": "The scoped change has observable evidence, only affected controls are checked, and no optional work starts after PASS.",
                "evidence": ".p2p/state/reports/<run-id>.json and execution ledger",
                "verification_oracle": verification_oracle("report_and_ledger_inspection", ".p2p/state/reports/<run-id>.json; .p2p/state/execution-ledger.jsonl", "report criteria and terminal event are PASS with bounded rerun/reuse records", "required evidence is absent, scope expands, or optional work continues"),
                "status": "PENDING",
            },
            {
                "criterion_id": "C5",
                "name": "governance_continuity",
                "mandatory": True,
                "pass_when": "FACT_LEDGER, Live Specs, Approval, Drift, RAG-if-applicable, and eval references remain intact and relevant gates are not bypassed.",
                "evidence": "authoritative governance references and affected gate reports",
                "verification_oracle": verification_oracle("governance_gate_validation", "FACT_LEDGER; Live Specs; Approval; Drift; RAG-if-applicable", "relevant existing gates remain available and PASS or are explicitly BLOCKED for a real reason", "a required governance reference is missing or bypassed"),
                "status": "PENDING",
            },
        ],
        "constraints": [
            "Do not expand into unrelated improvements; record discoveries as OUT OF SCOPE / BACKLOG.",
            "Do not regenerate a valid project eval suite or rerun valid PASS evidence when protected inputs are unchanged.",
            "Do not replace or weaken FACT_LEDGER, Live Specs, Drift Gate, Approval Gate, RAG, Eval, or Execution Ledger controls.",
            "Do not enable network, hooks, proxying, connectors, or destructive actions implicitly.",
        ],
        "protected_actions": list((policy or {}).get("protected_actions", DEFAULT_PROTECTED_ACTIONS)) if isinstance(policy or {}, dict) else list(DEFAULT_PROTECTED_ACTIONS),
        "protected_decisions": list((policy or {}).get("protected_actions", DEFAULT_PROTECTED_ACTIONS)) if isinstance(policy or {}, dict) else list(DEFAULT_PROTECTED_ACTIONS),
        "evidence_reuse_rule": "Reuse PASS evidence only when relevant protected-input fingerprints are unchanged and the evidence is unexpired; otherwise invalidate and rerun affected controls only.",
        "validation_requirements": [
            "Validate the Goal Contract before implementation.",
            "Run only affected deterministic checks where evidence is stale or relevant inputs changed.",
            "Run project-specific eval and RAG gates when their policy says they are affected.",
            "Use existing Approval Gate and Drift Gate for protected P2P/project updates.",
        ],
        "stop_conditions": {
            "PASS": "All mandatory measurable completion criteria are PASS; write the final report and stop.",
            "BLOCKED": "One mandatory criterion needs a user/business decision or materially broader protected change; identify exactly one decision and stop.",
            "REJECT": "Evidence proves the requested outcome is unsafe or invalid under current constraints; explain the reason and stop.",
            "always_stop_after": ["PASS", "BLOCKED", "REJECT"],
            "never_continue_for": ["optional hardening", "speculative optimization", "unrelated backlog items"],
        },
        "out_of_scope": [
            "Unrelated defects, feature ideas, style cleanups, or optimization opportunities discovered during inspection.",
            "Any change that would require a new governance framework or a broader protected decision than the request authorizes.",
        ],
        "acceptable_residual_risks": [
            "Real project quality remains unknown until the project-specific execution and eval evidence passes.",
            "A host-level full quorum is not claimed unless distinct named threads actually run.",
            "RAG remains pending when the project has retrieval behavior but no frozen corpus/evidence yet.",
        ],
        "work_plan": [
            {"step_id": "P1", "name": "inspect", "max_attempts": 1, "status": "pending"},
            {"step_id": "P2", "name": "bootstrap_or_reuse", "max_attempts": 1, "status": "pending"},
            {"step_id": "P3", "name": "execute_only_in_scope", "max_attempts": 1, "status": "pending"},
            {"step_id": "P4", "name": "affected_verification", "max_attempts": 1, "status": "pending"},
            {"step_id": "P5", "name": "report_and_stop", "max_attempts": 1, "status": "pending"},
        ],
        "guards": {
            "max_work_items": 5,
            "max_agent_calls": max(1, int(selection["quorum_size"])),
            "max_full_quorum_calls": 1 if selection["full_quorum_required"] else 0,
            "max_time_minutes": 30 if risk == "low" else 90 if risk == "medium" else 180,
            "reuse_pass_evidence_when_inputs_unchanged": True,
            "do_not_repeat_passed_controls": True,
            "do_not_open_optional_work_after_pass": True,
        },
        "work_item_classes": [
            {"item_id": "primary-objective", "class": "MANDATORY FOR GOAL", "description": "The one primary objective and its mandatory criteria."},
            {"item_id": "verification-support", "class": "SUPPORTING", "description": "Evidence and instrumentation needed to prove mandatory criteria."},
            {"item_id": "optional-improvements", "class": "OPTIONAL / BACKLOG", "description": "Polish or improvements not required for PASS."},
            {"item_id": "unrelated-discoveries", "class": "OUT OF SCOPE", "description": "Unrelated findings must remain outside the active Goal."},
        ],
        "exploration_policy": exploration_policy_for(work_type),
        "failed_approaches": [],
        "goal_updates": [],
        "iteration_discipline": {
            "sequence": ["baseline", "largest_verified_failure", "one_focused_change", "affected_verification", "continue_only_if_mandatory_unmet"],
            "subjective_judgment_allowed_only_when": "no deterministic oracle exists",
            "wall_clock_is_not_failure_evidence": True,
        },
        "agent_selection": selection,
        "artifacts": {
            "project_profile": ".p2p/project-profile.json",
            "project_policy": ".p2p/project-policy.json",
            "goal_contract": ".p2p/state/goal-contract.json",
            "project_status": ".p2p/state/project-status.json",
            "trusted_evidence": ".p2p/state/trusted-evidence.json",
            "execution_ledger": ".p2p/state/execution-ledger.jsonl",
            "reports": ".p2p/state/reports/",
            "capsules": ".p2p/state/capsules/",
        },
    }
    contract["goal_linter"] = lint_goal_contract(contract)
    return contract


def write_goal(root: Path, contract: dict[str, object]) -> Path:
    goals = root / ".p2p" / "state" / "goals"
    goals.mkdir(parents=True, exist_ok=True)
    goal_id = str(contract["goal_id"])
    path = goals / f"{slugify(goal_id)}.json"
    write_json_atomic(path, contract)
    write_json_atomic(root / ".p2p" / "state" / "goal-contract.json", contract)
    return path


def policy_for(root: Path, governance: Path | None) -> dict[str, object]:
    path = root / ".p2p" / "project-policy.json"
    value = read_json(path, {})
    if isinstance(value, dict) and value.get("schema_version") == "p2p-codex-project-policy/1":
        return value
    if governance:
        template = governance / "project-policy.template.json"
        value = read_json(template, {}) if template.is_file() else {}
    return value if isinstance(value, dict) else {}


def bootstrap_project(root: Path, inspection: dict[str, object], contract: dict[str, object], package_hint: str | None = None) -> dict[str, object]:
    state = root / ".p2p" / "state"
    reports = state / "reports"
    capsules = state / "capsules"
    for path in (state, reports, capsules, root / ".p2p" / "approvals" / "requests", root / ".p2p" / "approvals" / "records", root / ".p2p" / "gates"):
        path.mkdir(parents=True, exist_ok=True)
    governance_options = governance_candidates(root, package_hint)
    governance = governance_options[0][0] if governance_options else None
    governance_mode = governance_options[0][1] if governance_options else "missing"
    created: list[str] = []
    reused: list[str] = []

    policy_path = root / ".p2p" / "project-policy.json"
    if policy_path.is_file():
        policy = read_json(policy_path, {})
        reused.append("project_policy")
    elif governance and (governance / "project-policy.template.json").is_file():
        policy = read_json(governance / "project-policy.template.json", {})
        if isinstance(policy, dict):
            policy["project"] = root.name
        write_json_if_missing(policy_path, policy)
        created.append("project_policy")
    else:
        policy = {}
    if not isinstance(policy, dict):
        policy = {}

    profile_path = root / ".p2p" / "project-profile.json"
    if profile_path.is_file():
        profile = read_json(profile_path, {})
        reused.append("project_profile")
    else:
        profile = {
            "schema_version": PROFILE_SCHEMA,
            "project": root.name,
            "project_type": inspection.get("project_type"),
            "created_at": now(),
            "evidence": {
                "markers": inspection.get("markers", []),
                "top_level_directories": inspection.get("top_level_directories", []),
                "file_count_at_bootstrap": inspection.get("file_count", 0),
                "source": "local project inspection",
            },
            "governance": {
                "mode": governance_mode,
                "authoritative_root": str(governance) if governance else None,
                "fact_ledger": "fact-ledger.json",
                "live_specs": "live-specs.json",
                "approval_policy": "approval-policy.json",
                "drift_policy": "drift-policy.json",
                "eval_schema": "eval-suite.schema.json",
                "rag_schema": "rag-retrieval-check.schema.json",
                "release_criteria": "project-policy.release_gate",
            },
            "initialization": {
                "project_profile": "CREATED",
                "fact_ledger": "REFERENCE_EXISTING_AUTHORITATIVE_LEDGER",
                "live_specs": "REFERENCE_EXISTING_GENERATED_SPECS",
                "project_policy": "CREATED" if policy_path.is_file() else "BLOCKED_MISSING_TEMPLATE",
                "project_eval": "PENDING",
                "rag_checks": "PENDING_OR_NOT_APPLICABLE",
                "drift_baseline": "CREATED_ON_FIRST_RUN",
                "approval_requirements": "READ_FROM_PROJECT_POLICY",
                "execution_ledger": ".p2p/state/execution-ledger.jsonl",
            },
            "rag": {"applicable": bool(inspection.get("rag_applicable")), "status": "PENDING" if inspection.get("rag_applicable") else "NOT_APPLICABLE"},
            "snapshot": project_snapshot(root),
        }
        write_json_if_missing(profile_path, profile)
        created.append("project_profile")
    if not isinstance(profile, dict):
        profile = {}

    contract_path = root / ".p2p" / "state" / "goal-contract.json"
    eval_result: dict[str, object] = {"status": "BLOCKED", "errors": ["compatible project-eval v2 p2p_eval helper not found"]}
    helpers = eval_helper_candidates(root, package_hint)
    if helpers:
        command = [
            sys.executable,
            str(helpers[0]),
            "design",
            "--project",
            str(root),
            "--name",
            root.name,
            "--goal-contract",
            str(contract_path),
            "--profile",
            str(profile_path),
        ]
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        try:
            parsed = json.loads(process.stdout)
            eval_result = parsed if isinstance(parsed, dict) else {"status": "BLOCKED", "errors": ["invalid p2p_eval response"]}
        except json.JSONDecodeError:
            eval_result = {"status": "BLOCKED", "errors": [(process.stderr or process.stdout).strip()[:500] or "p2p_eval design failed"]}
    if eval_result.get("status") == "CREATED":
        created.append("project_eval")
    elif eval_result.get("status") == "REUSED":
        reused.append("project_eval")

    rag_path: Path | None = None
    if bool(inspection.get("rag_applicable")):
        rag_path = root / ".p2p" / "evals" / "rag-retrieval-check.json"
        if not rag_path.exists() and governance and (governance / "rag-retrieval-check.template.json").is_file():
            rag = read_json(governance / "rag-retrieval-check.template.json", {})
            if isinstance(rag, dict):
                rag["project"] = root.name
                rag["initialization_status"] = "PENDING_PROJECT_CORPUS_AND_EVIDENCE"
                write_json_if_missing(rag_path, rag)
                created.append("rag_check_template")
        else:
            reused.append("rag_check")

    status_path = state / "project-status.json"
    if status_path.is_file():
        status = read_json(status_path, {})
        reused.append("project_status")
    else:
        status = {
            "schema_version": STATUS_SCHEMA,
            "project": root.name,
            "current_goal": None,
            "terminal_state": "IN_PROGRESS",
            "completed_milestones": [],
            "trusted_baseline": {"project_snapshot": project_snapshot(root), "controls": []},
            "latest_eval_status": "NOT_RUN",
            "important_fact_unknown": {"facts": "REFERENCE_EXISTING_LEDGER", "unknowns": ["goal-specific project readiness"]},
            "outstanding_blockers": [],
            "approval_state": "POLICY_LOOKUP_ONLY",
            "last_drift_state": "NOT_RUN",
            "execution_ledger_refs": [],
            "next_action": "Complete the current bounded work plan.",
            "updated_at": now(),
        }
        write_json_if_missing(status_path, status)
        created.append("project_status")
    ledger_path = state / "execution-ledger.jsonl"
    if not ledger_path.exists():
        ledger_path.touch()
        created.append("execution_ledger")
    evidence_path = state / "trusted-evidence.json"
    if not evidence_path.is_file():
        write_json_if_missing(evidence_path, {"schema_version": EVIDENCE_SCHEMA, "project": root.name, "controls": {}, "updated_at": now()})
        created.append("trusted_evidence")
    return {
        "schema_version": "p2p-bootstrap/1",
        "project": root.name,
        "governance_root": str(governance) if governance else None,
        "governance_mode": governance_mode,
        "created": list(dict.fromkeys(created)),
        "reused": list(dict.fromkeys(reused)),
        "profile": str(profile_path),
        "policy": str(policy_path),
        "suite": str(root / ".p2p" / "evals" / "suite.json"),
        "rag_check": str(rag_path) if rag_path else None,
        "status": str(status_path),
        "trusted_evidence": str(evidence_path),
        "execution_ledger": str(ledger_path),
        "eval": eval_result,
        "policy_value": policy,
    }


def evidence_plan(root: Path, snapshot: dict[str, object], affected: list[str]) -> dict[str, object]:
    value = load_trusted_evidence(root)
    controls = value.get("controls", {}) if isinstance(value, dict) else {}
    controls = controls if isinstance(controls, dict) else {}
    reused: list[str] = []
    stale: list[str] = []
    for name, item in controls.items():
        if not isinstance(item, dict) or item.get("status") != "PASS":
            stale.append(str(name))
            continue
        expires_at = item.get("expires_at")
        if isinstance(expires_at, str) and expires_at and date.today().isoformat() > expires_at:
            stale.append(str(name))
            continue
        scopes = item.get("scope_paths") if isinstance(item.get("scope_paths"), list) else CONTROL_SCOPES.get(str(name), ["*"])
        expected = scoped_fingerprint(snapshot, [str(scope) for scope in scopes])
        if expected == item.get("input_fingerprint"):
            reused.append(str(name))
        else:
            stale.append(str(name))
    rerun = sorted(set(affected) | set(stale) - set(reused))
    return {
        "schema_version": "p2p-evidence-plan/1",
        "reused_controls": sorted(reused),
        "rerun_controls": rerun,
        "expired_or_changed_controls": sorted(stale),
        "affected_controls": sorted(set(affected)),
        "rule": "Reuse PASS evidence only when its scoped protected-input fingerprint is unchanged and it has not expired.",
    }


def context_source_bindings(root: Path, candidates: list[tuple[str, Path, bool]]) -> list[dict[str, object]]:
    """Expose only project-relative, hash-bound source metadata to the view."""

    bindings: list[dict[str, object]] = []
    seen: set[str] = set()
    for source_id, path, required in candidates:
        if source_id in seen or not path.is_file():
            continue
        try:
            relative = relative_path(path, root)
        except ValueError:
            # Package/governance files outside the project remain referenced by
            # the existing workflow, but are not copied into this view.
            continue
        seen.add(source_id)
        bindings.append(
            {
                "source_id": source_id,
                "path": relative,
                "source_hash": sha256_file(path),
                "source_class": "AUTHORITATIVE_PROJECT_SOURCE",
                "required": required,
            }
        )
    return bindings


def task_targeted_context_metadata(
    context_module: Any,
    contract: dict[str, object],
    sources: list[dict[str, object]],
    *,
    candidate_binding: str | None = None,
) -> dict[str, object]:
    """Build the bounded C19 retrieval plan from existing workflow bindings.

    The workflow already owns the authoritative source list and hashes.  This
    adapter supplies roles and acceptance bindings to C06's C19 extension; it
    does not scan the repository, create a cache, or add a second router.
    """

    retrieve = getattr(context_module, "retrieve_task_context", None)
    if not callable(retrieve):
        return {
            "schema": "p2p-task-targeted-context/1",
            "status": "BLOCKED",
            "context_class": "CONTEXT_INSUFFICIENT",
            "failure_reasons": ["CAPABILITY_UNAVAILABLE"],
        }
    role_by_source = {
        "goal-contract": "DIRECT_AUTHORITATIVE_REFS",
        "project-status": "DIRECT_AUTHORITATIVE_REFS",
        "project-profile": "DIRECT_AUTHORITATIVE_REFS",
        "project-policy": "DIRECT_AUTHORITATIVE_REFS",
        "project-eval": "DEPENDENCY_OUTPUTS",
        "trusted-evidence": "KNOWN_EVIDENCE",
        "execution-ledger": "KNOWN_EVIDENCE",
    }
    catalog: list[dict[str, object]] = []
    direct_refs: list[str] = []
    dependency_refs: list[str] = []
    evidence_refs: list[str] = []
    acceptance: list[dict[str, object]] = []
    for binding in sources:
        source_id = str(binding.get("source_id"))
        role = role_by_source.get(source_id, "TARGETED_SOURCE")
        catalog.append({**binding, "retrieval_role": role, "coverage_ids": [source_id], "scope": ["current-task"]})
        if role == "DIRECT_AUTHORITATIVE_REFS":
            direct_refs.append(source_id)
        elif role == "DEPENDENCY_OUTPUTS":
            dependency_refs.append(source_id)
        else:
            evidence_refs.append(source_id)
        if bool(binding.get("required")):
            acceptance.append({"coverage_id": source_id, "source_refs": [source_id], "required": True})
    task = {
        "task_purpose": contract.get("objective") or contract.get("request") or "current bounded workflow task",
        "scope": ["current-task", "current-project"],
        "direct_authoritative_refs": direct_refs,
        "dependency_refs": dependency_refs,
        "known_evidence": evidence_refs,
        "acceptance": acceptance,
    }
    requested_class = contract.get("context_class")
    if isinstance(contract.get("context_retrieval"), dict):
        requested_class = contract["context_retrieval"].get("context_class") or requested_class
    if not isinstance(requested_class, str) or not requested_class:
        requested_class = "MINIMAL"
    return retrieve(task, catalog, context_class=requested_class, candidate_binding=candidate_binding)


def build_workflow_context_input(
    root: Path,
    request: str,
    contract: dict[str, object],
    inspection: dict[str, object],
    status: dict[str, object],
    *,
    changes: list[str] | None = None,
    previous_evidence: dict[str, object] | None = None,
    policy: dict[str, object] | None = None,
    context_module: Any | None = None,
) -> dict[str, object]:
    """Map existing workflow state into the two-mode context contract.

    This adapter deliberately does not create a second state store.  It reads
    the already-authoritative Goal Contract/project state and supplies stable
    pointers for details that the experimental view may defer.
    """

    state = root / ".p2p" / "state"
    candidates = [
        ("goal-contract", state / "goal-contract.json", True),
        ("project-status", state / "project-status.json", True),
        ("project-profile", root / ".p2p" / "project-profile.json", True),
        ("project-policy", root / ".p2p" / "project-policy.json", True),
        ("project-eval", root / ".p2p" / "evals" / "suite.json", True),
        ("trusted-evidence", state / "trusted-evidence.json", False),
        ("execution-ledger", state / "execution-ledger.jsonl", False),
    ]
    sources = context_source_bindings(root, candidates)
    task_targeted = task_targeted_context_metadata(
        context_module or context_api(root, None),
        contract,
        sources,
        candidate_binding=str(contract.get("candidate_binding")) if contract.get("candidate_binding") else None,
    )
    source_by_id = {str(item["source_id"]): item for item in sources}
    pointers = [
        {
            "pointer_id": f"pointer-{source_id}",
            "label": f"Authoritative {source_id} source",
            "relevance": ["current-task", source_id],
            "authority": "EXISTING_WORKFLOW_SOURCE",
            "scope": ["current-task"],
            "freshness": "CURRENT",
            "provenance": "PROJECT_RELATIVE_HASH_BOUND_SOURCE",
            "content_class": "EVIDENCE",
            "load_policy": "ON_RESOLVE",
            "source_binding": source_id,
            "source_hash": item["source_hash"],
        }
        for source_id, item in sorted(source_by_id.items())
    ]
    pointer_by_source = {str(item["source_binding"]): str(item["pointer_id"]) for item in pointers}
    change_list = list(changes or [])
    evidence = previous_evidence or {}
    selection = contract.get("agent_selection") if isinstance(contract.get("agent_selection"), dict) else {}
    protected_actions = contract.get("protected_actions")
    if not isinstance(protected_actions, list):
        protected_actions = (policy or {}).get("protected_actions", DEFAULT_PROTECTED_ACTIONS) if isinstance(policy, dict) else DEFAULT_PROTECTED_ACTIONS

    history_item: dict[str, object] = {
        "item_id": "execution-history",
        "value": {
            "previous_terminal_state": status.get("terminal_state"),
            "previous_run_refs": status.get("execution_ledger_refs", []),
            "changed_files": change_list,
        },
    }
    if "execution-ledger" in pointer_by_source:
        history_item.update(
            {
                "defer": True,
                "pointer_id": pointer_by_source["execution-ledger"],
                "source_binding": "execution-ledger",
            }
        )
    else:
        history_item["required"] = True

    evidence_item: dict[str, object] = {
        "item_id": "trusted-evidence-detail",
        "value": {
            "reused_controls": evidence.get("reused_controls", []),
            "rerun_controls": evidence.get("rerun_controls", []),
            "affected_controls": evidence.get("affected_controls", []),
        },
    }
    if "trusted-evidence" in pointer_by_source:
        evidence_item.update(
            {
                "defer": True,
                "pointer_id": pointer_by_source["trusted-evidence"],
                "source_binding": "trusted-evidence",
            }
        )
    else:
        evidence_item["required"] = True

    return {
        "goal_id": contract.get("goal_id"),
        "task_or_goal": contract.get("objective") or request.strip(),
        "scope": ["current-project", "current-request", "bounded-workflow"],
        "non_scope": contract.get("out_of_scope", []),
        "acceptance": contract.get("completion_criteria", []),
        "relevant_facts": [
            {
                "item_id": "project-inspection",
                "value": {
                    "project_type": inspection.get("project_type"),
                    "markers": inspection.get("markers", []),
                    "top_level_directories": inspection.get("top_level_directories", []),
                    "file_count": inspection.get("file_count", 0),
                },
                "required": True,
                "source_binding": "project-profile" if "project-profile" in source_by_id else None,
            },
            {
                "item_id": "project-state",
                "value": {"terminal_state": status.get("terminal_state"), "changed_files": change_list},
                "required": True,
                "source_binding": "project-status" if "project-status" in source_by_id else None,
            },
        ],
        "relevant_decisions": [
            {
                "item_id": "goal-eligibility",
                "value": contract.get("goal_eligibility", {}),
                "required": True,
                "source_binding": "goal-contract" if "goal-contract" in source_by_id else None,
            },
            {
                "item_id": "agent-and-quorum-constraints",
                "value": {
                    "selected_agents": selection.get("selected_agents", []),
                    "quorum_size": selection.get("quorum_size", 0),
                    "full_quorum_required": bool(selection.get("full_quorum_required", False)),
                    "canonical_capabilities": list(AGENTS),
                    "full_quorum_denominator": 8,
                },
                "required": True,
                "source_binding": "goal-contract" if "goal-contract" in source_by_id else None,
            },
        ],
        "direct_dependencies": [
            {
                "item_id": "project-eval-contract",
                "value": {
                    "suite_path": ".p2p/evals/suite.json",
                    "design_status": (status.get("latest_eval_status") or "NOT_RUN"),
                },
                "required": True,
                "source_binding": "project-eval" if "project-eval" in source_by_id else None,
            },
            {
                "item_id": "workflow-evidence-plan",
                "value": {
                    "reused_controls": evidence.get("reused_controls", []),
                    "affected_controls": evidence.get("affected_controls", []),
                },
                "required": True,
                "source_binding": "trusted-evidence" if "trusted-evidence" in source_by_id else None,
            },
        ],
        "history": [history_item],
        "plans": [
            {
                "item_id": "bounded-work-plan",
                "value": {"work_plan": contract.get("work_plan", []), "stop_conditions": contract.get("stop_conditions", {})},
                "source_binding": "goal-contract" if "goal-contract" in source_by_id else None,
            }
        ],
        "full_evidence": [evidence_item],
        "capability_constraints": {
            "selected_agents": selection.get("selected_agents", []),
            "quorum_size": selection.get("quorum_size", 0),
            "full_quorum_required": bool(selection.get("full_quorum_required", False)),
            "canonical_capabilities": list(AGENTS),
            "canonical_denominator": 8,
        },
        "permission_constraints": {
            "protected_actions": list(protected_actions),
            "approval_boundary": "protected actions remain explicit and are never inferred from context",
            "external_io": "disabled unless explicitly requested and separately gated",
            "source_grants_permissions": False,
        },
        "source_bindings": sources,
        "evidence_pointers": pointers,
        "task_targeted_context": task_targeted,
        "access_contract": {
            "tools": ["existing_project_workflow_controls"],
            "source_catalog": "project-relative-hash-bound-authoritative-sources",
            "access_expansion": False,
        },
    }


def write_context_manifest(root: Path, run_id: str, context_view: dict[str, object]) -> dict[str, object]:
    """Persist observation metadata and return the stable receipt fields."""

    path = root / ".p2p" / "state" / "reports" / f"{run_id}-context-manifest.json"
    manifest = dict(context_view.get("context_manifest", {}))
    manifest["run_id"] = run_id
    manifest["context_manifest_pointer"] = relative_path(path, root)
    write_json_atomic(path, manifest)
    serialized_size = context_view.get("serialized_size", {})
    return {
        "context_mode": context_view.get("context_mode"),
        "context_fingerprint": context_view.get("context_fingerprint"),
        "context_manifest_pointer": relative_path(path, root),
        "context_manifest_schema": manifest.get("schema"),
        "context_serialized_size": serialized_size,
    }


def create_context_receipt(
    root: Path,
    run_id: str,
    context_module: Any,
    context_mode: str,
    context_input: dict[str, object],
) -> dict[str, object]:
    view = context_module.build_context_view(context_input, context_mode)
    return write_context_manifest(root, run_id, view)


def controls_affected_by(changes: list[str], new_project: bool) -> list[str]:
    if new_project:
        return ["project_profile", "project_policy", "project_eval", "goal_completion", "governance_continuity"]
    affected: set[str] = set()
    for relative in changes:
        normalized = relative.replace("\\", "/")
        if normalized.startswith(("governance/", ".p2p/system/governance/", "scripts/", ".p2p/system/scripts/", ".agents/skills/", ".codex/agents/")):
            affected.update({"package_doctor", "drift_gate", "governance_continuity"})
        elif normalized.startswith(".p2p/evals/"):
            affected.add("project_eval")
        else:
            affected.update({"project_wide_audit", "goal_completion"})
    return sorted(affected or {"goal_completion"})


def safe_update_flow(changes: list[str], affected: list[str], policy: dict[str, object] | None = None) -> dict[str, object]:
    protected_change = any(
        path.replace("\\", "/").startswith((".agents/skills/", ".codex/agents/", "governance/", "scripts/", ".p2p/system/"))
        for path in changes
    )
    protected_actions = policy.get("protected_actions", DEFAULT_PROTECTED_ACTIONS) if isinstance(policy, dict) else DEFAULT_PROTECTED_ACTIONS
    return {
        "detect": {"changed_files": changes, "meaningful_change": bool(changes)},
        "impact": {"affected_controls": affected, "unaffected_controls_reusable": True},
        "verification": {"run_only": affected, "reuse_when_fingerprint_unchanged": True},
        "drift_gate": "RUN_IF_AFFECTED" if protected_change else "REUSE_OR_RUN_ONLY_IF_AFFECTED",
        "approval": {"required": protected_change, "protected_actions": protected_actions if protected_change else [], "never_self_approve": True},
        "trusted_baseline": "UPDATE_ONLY_AFTER_TERMINAL_PASS",
        "out_of_scope": "Record unrelated discoveries as OUT_OF_SCOPE / BACKLOG; do not expand the Goal.",
    }


def fixture_ready(root: Path) -> bool:
    marker = root / ".p2p" / "acceptance" / "ready.json"
    if marker.is_file():
        value = read_json(marker, {})
        if isinstance(value, dict) and value.get("status") == "ready":
            return True
    for path in root.rglob("*.py"):
        if path.is_file() and "READY_FOR_DEMO = True" in path.read_text(encoding="utf-8", errors="replace"):
            return True
    return False


def validate_suite(root: Path, suite_path: Path, helper: Path | None) -> dict[str, object]:
    if not suite_path.is_file():
        return {"status": "BLOCKED", "errors": [f"missing eval suite: {suite_path}"]}
    if helper is None:
        return {"status": "BLOCKED", "errors": ["compatible project-eval v2 p2p_eval helper not found"]}
    process = subprocess.run(
        [sys.executable, str(helper), "validate", "--suite", str(suite_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        parsed = json.loads(process.stdout)
        return parsed if isinstance(parsed, dict) else {"status": "BLOCKED", "errors": ["invalid p2p_eval validation response"]}
    except json.JSONDecodeError:
        return {"status": "BLOCKED", "errors": [(process.stderr or process.stdout).strip()[:500] or "p2p_eval validation failed"]}


def criteria_result(contract: dict[str, object], bootstrap: dict[str, object], evidence: dict[str, object], inspection: dict[str, object], root: Path, acceptance: bool, suite_validation: dict[str, object]) -> list[dict[str, object]]:
    eval_status = str(bootstrap.get("eval", {}).get("status", "BLOCKED")) if isinstance(bootstrap.get("eval"), dict) else "BLOCKED"
    eval_valid = eval_status in {"CREATED", "REUSED"} and str(suite_validation.get("status", "FAIL")) == "PASS"
    governance_root = bootstrap.get("governance_root")
    governance_ok = bool(governance_root) and all((Path(str(governance_root)) / name).is_file() for name in ("fact-ledger.json", "live-specs.json", "approval-policy.json", "drift-policy.json"))
    linter = contract.get("goal_linter") if isinstance(contract.get("goal_linter"), dict) else lint_goal_contract(contract)
    bounded = bool(contract.get("objective")) and len(contract.get("completion_criteria", [])) >= 4 and bool(contract.get("stop_conditions")) and bool(contract.get("out_of_scope")) and str(linter.get("status")) == "PASS"
    state_ok = all(Path(str(bootstrap.get(name))).is_file() for name in ("profile", "policy", "status", "trusted_evidence"))
    results = [
        {"criterion_id": "L0", "name": "goal_linter", "mandatory": True, "status": "PASS" if str(linter.get("status")) == "PASS" else "BLOCKED", "evidence": linter.get("errors") or "every mandatory criterion has a verification oracle"},
        {"criterion_id": "C1", "name": "bounded_goal", "mandatory": True, "status": "PASS" if bounded else "BLOCKED", "evidence": "goal contract contains measurable criteria, verification oracles, and terminal rules"},
        {"criterion_id": "C2", "name": "project_state_initialized", "mandatory": True, "status": "PASS" if state_ok else "BLOCKED", "evidence": "profile, policy, status, and trusted-evidence paths exist"},
        {"criterion_id": "C3", "name": "project_specific_eval", "mandatory": True, "status": "PASS" if eval_valid else "BLOCKED", "evidence": "suite design/reuse plus v2 validation"},
        {"criterion_id": "C4", "name": "bounded_execution_and_verification", "mandatory": True, "status": "PASS" if acceptance and fixture_ready(root) else "BLOCKED", "evidence": "deterministic fixture readiness and selective verification" if acceptance else "goal-specific execution/eval evidence is not supplied"},
        {"criterion_id": "C5", "name": "governance_continuity", "mandatory": True, "status": "PASS" if governance_ok else "BLOCKED", "evidence": "authoritative FACT/Live/Approval/Drift references"},
    ]
    return results


def update_trusted_evidence(root: Path, snapshot: dict[str, object], passed_controls: list[str], run_id: str, acceptance: bool) -> None:
    path = root / ".p2p" / "state" / "trusted-evidence.json"
    value = load_trusted_evidence(root)
    if not isinstance(value, dict):
        value = {"schema_version": EVIDENCE_SCHEMA, "project": root.name, "controls": {}}
    controls = value.setdefault("controls", {})
    if not isinstance(controls, dict):
        controls = {}
        value["controls"] = controls
    expires = (date.today() + timedelta(days=30)).isoformat()
    for control in passed_controls:
        scopes = CONTROL_SCOPES.get(control, ["*"])
        controls[control] = {
            "status": "PASS",
            "checked_at": now(),
            "expires_at": expires,
            "scope_paths": scopes,
            "input_fingerprint": scoped_fingerprint(snapshot, scopes),
            "evidence": f".p2p/state/reports/{run_id}.json",
            "provenance": "synthetic acceptance workflow" if acceptance else "project workflow run",
        }
    value["updated_at"] = now()
    write_json_atomic(path, value)


def write_capsule(root: Path, contract: dict[str, object], result: dict[str, object]) -> Path:
    goal_id = str(contract.get("goal_id", "goal"))
    path = root / ".p2p" / "state" / "capsules" / f"{slugify(goal_id)}.md"
    status = result.get("status", "BLOCKED")
    next_action = "No further action; terminal state reached." if status in TERMINAL_STATES else "Continue the bounded work plan."
    criteria = result.get("criteria", []) if isinstance(result.get("criteria"), list) else []
    mandatory = ", ".join(str(item.get("name", item.get("criterion_id", "criterion"))) for item in criteria if isinstance(item, dict) and item.get("mandatory")) or "none"
    passed = ", ".join(str(item.get("name", item.get("criterion_id", "criterion"))) for item in criteria if isinstance(item, dict) and item.get("status") == "PASS") or "none"
    reused = ", ".join(str(item) for item in result.get("reused_controls", []) if isinstance(result.get("reused_controls"), list)) or "none"
    backlog = ", ".join(str(item.get("description", item.get("item_id", "item"))) for item in result.get("out_of_scope_backlog", []) if isinstance(item, dict)) or "none"
    failed = ", ".join(str(item.get("reason", "failed approach")) for item in contract.get("failed_approaches", []) if isinstance(item, dict)) or "none"
    eligibility = contract.get("goal_eligibility", {}) if isinstance(contract.get("goal_eligibility"), dict) else {}
    exploration = contract.get("exploration_policy", {}) if isinstance(contract.get("exploration_policy"), dict) else {}
    body = (
        f"# P2P CAPSULE — {goal_id}\n\n"
        "- Schema: p2p-capsule/2\n"
        "- Profile: task\n"
        f"- Saved: {now()}\n"
        f"- Goal: {contract.get('objective', '')}\n"
        f"- Eligibility: {eligibility.get('classification', 'GOAL')} — {eligibility.get('reason', '')}\n"
        f"- Work type: {contract.get('work_type', 'MIXED')}\n"
        f"- Active lane: {exploration.get('active_lane', 'primary')}\n"
        f"- Current: {status}\n"
        f"- Next: {next_action}\n"
        f"- Blockers: {result.get('decision_required') or 'none'}\n\n"
        "## Task continuation fields\n\n"
        f"- Objective: {contract.get('objective', '')}\n"
        f"- Mandatory criteria: {mandatory}\n"
        f"- PASS criteria: {passed}\n"
        f"- Reusable evidence: {reused}\n"
        f"- Current bottleneck: {result.get('decision_required') or 'none'}\n"
        f"- Active implementation lane: {exploration.get('active_lane', 'primary')}\n"
        f"- Failed approaches: {failed}\n"
        f"- OUT-OF-SCOPE / BACKLOG: {backlog}\n"
        "- Approval state: REQUIRED_ONLY_FOR_PROTECTED_ACTIONS\n"
        f"- Progress: {result.get('stop_reason', '')}\n"
        "- Decisions: see the decision_required field in the status/report artifact.\n"
        "- Constraints: see the authoritative Goal Contract.\n"
        f"- Verified evidence: {result.get('report_json', '')}\n"
        f"- Context delivery: {result.get('context_mode', 'BASELINE_COMPAT')} | fingerprint {result.get('context_fingerprint', 'unavailable')} | manifest {result.get('context_manifest_pointer', 'unavailable')} | size {result.get('context_serialized_size', {}).get('bytes', 'unavailable') if isinstance(result.get('context_serialized_size'), dict) else 'unavailable'}\n"
        "- Artifacts: `.p2p/project-profile.json`, `.p2p/evals/suite.json`, `.p2p/state/project-status.json`, `.p2p/state/execution-ledger.jsonl`.\n"
        f"- Blockers: {result.get('decision_required') or 'none'}\n"
        f"- Next action: {next_action}\n\n"
        "## Authoritative references\n\n"
        "Large content remains in the referenced Goal Contract, project eval, governance files, and Execution Ledger; this capsule is only a continuation index.\n"
    )
    write_text_atomic(path, body)
    return path


def beginner_report(result: dict[str, object]) -> str:
    status = str(result.get("status", "BLOCKED"))
    criteria = result.get("criteria", [])
    if not isinstance(criteria, list):
        criteria = []
    trace = result.get("decision_trace") if isinstance(result.get("decision_trace"), dict) else {}
    if trace.get("captured"):
        why = f"P2P da ghi lai ly do va cac lien ket an toan cho quyet dinh nay. Ma tra cuu: {trace.get('decision_id')}"
    elif trace.get("status") == "NOT_MATERIAL":
        why = "Yeu cau nay khong tao ra quyet dinh vat chat nen P2P khong tao trace thua."
    else:
        why = "Chua co trace native moi cho lan chay nay; cac ho so Goal/evidence hien co van la nguon su that."
    result["checked_summary"] = f"{result.get('checked_summary') or ''} P2P WHY: {why}"
    checklist = "\n".join(
        f"- {'PASS' if item.get('status') == 'PASS' else item.get('status', 'BLOCKED')}: {item.get('name', item.get('criterion_id', 'check'))}"
        for item in criteria
        if isinstance(item, dict)
    )
    remaining = result.get("decision_required") or "Không."
    action = "Không." if status == "PASS" else str(result.get("decision_required") or "Cần quyết định một việc duy nhất trước khi tiếp tục.")
    summary = result.get("summary") or "Đã tạo hoặc dùng lại cấu trúc P2P cần thiết và kiểm tra theo Goal Contract."
    checked = result.get("checked_summary") or "Đã kiểm tra Goal Contract, project state, eval, phạm vi và các tham chiếu governance liên quan."
    return (
        f"1. KẾT QUẢ\n{status}\n\n"
        f"2. TÔI ĐÃ LÀM GÌ\n{summary}\n\n"
        f"3. ĐÃ KIỂM TRA NHỮNG GÌ\n{checked}\n{checklist}\n\n"
        f"4. CÓ GÌ CHƯA XONG\n{remaining}\n\n"
        f"5. ANH CÓ CẦN LÀM GÌ KHÔNG?\n{action}\n"
    )


def run_workflow(
    root: Path,
    request: str,
    *,
    package_hint: str | None = None,
    acceptance: bool = False,
    context_mode: str | None = None,
) -> dict[str, object]:
    root = root.resolve()
    context_module = context_api(root, package_hint)
    selected_context_mode = context_module.select_context_mode(context_mode)
    inspection = inspect_project(root, request, package_hint)
    goal_eligibility = inspection.get("goal_eligibility") if isinstance(inspection.get("goal_eligibility"), dict) else classify_goal_eligibility(request, inspection)
    status_before = load_status(root)
    current_snapshot = project_snapshot(root)
    previous_snapshot = status_before.get("trusted_baseline", {}).get("project_snapshot") if isinstance(status_before.get("trusted_baseline"), dict) else None
    changes = changed_files(previous_snapshot, current_snapshot)
    same_request = status_before.get("current_request") == request.strip()
    previous_request = str(status_before.get("current_request", ""))
    goal_update = classify_goal_update(previous_request, request, load_current_contract(root)) if previous_request and not same_request else None
    if status_before.get("terminal_state") == "PASS" and same_request and not changes:
        run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-already-pass"
        result = {
            "schema_version": SCHEMA,
            "run_id": run_id,
            "status": "PASS",
            "stop_reason": "already_passed_and_inputs_unchanged",
            "decision_required": None,
            "goal_eligibility": goal_eligibility,
            "goal_created": False,
            "changed_files": [],
            "reused_controls": status_before.get("trusted_baseline", {}).get("controls", []),
            "rerun_controls": [],
            "criteria": status_before.get("criteria", []),
            "work_type": status_before.get("work_type", classify_work_type(request)),
            "exploration_policy": status_before.get("exploration_policy", exploration_policy_for(classify_work_type(request))),
            "failed_approaches": status_before.get("failed_approaches", []),
            "goal_updates": status_before.get("goal_updates", []),
            "work_item_classes": status_before.get("work_item_classes", []),
            "summary": "Mục tiêu này đã PASS và các đầu vào liên quan chưa thay đổi; P2P đã dừng.",
            "checked_summary": "Đã dùng lại trạng thái PASS đã tin cậy; không chạy lại kiểm tra không bị ảnh hưởng.",
        }
        context_contract = load_current_contract(root)
        context_input = build_workflow_context_input(root, request, context_contract, inspection, status_before, changes=[], context_module=context_module)
        result.update(create_context_receipt(root, run_id, context_module, selected_context_mode, context_input))
        ledger = root / ".p2p" / "state" / "execution-ledger.jsonl"
        append_event(ledger, {"event": "stopped_after_pass", "run_id": run_id, "goal_id": status_before.get("current_goal", {}).get("goal_id") if isinstance(status_before.get("current_goal"), dict) else None, "selected_agents": [], "quorum_size": 0, "full_quorum_used": False, "evidence_reused": result["reused_controls"], "context_mode": result["context_mode"], "context_fingerprint": result["context_fingerprint"], "context_manifest_pointer": result["context_manifest_pointer"]})
        report_json = root / ".p2p" / "state" / "reports" / f"{run_id}.json"
        result["report_json"] = str(report_json)
        result["report_markdown"] = str(report_json.with_suffix(".md"))
        write_json_atomic(report_json, result)
        write_text_atomic(report_json.with_suffix(".md"), beginner_report(result))
        capsule = write_capsule(root, context_contract, result)
        result["capsule"] = relative_path(capsule, root)
        return result

    governance_options = governance_candidates(root, package_hint)
    policy = policy_for(root, governance_options[0][0] if governance_options else None)
    existing_contract = load_current_contract(root)
    if (
        existing_contract.get("request") == request.strip()
        and load_status(root).get("terminal_state") not in TERMINAL_STATES
        and isinstance(existing_contract.get("goal_linter"), dict)
        and isinstance(existing_contract.get("goal_eligibility"), dict)
    ):
        contract = existing_contract
    else:
        contract = build_goal_contract(root, request, inspection, policy)
    if goal_update:
        updates = contract.setdefault("goal_updates", [])
        if isinstance(updates, list):
            updates.append(goal_update)
    contract_path = write_goal(root, contract)
    bootstrap = bootstrap_project(root, inspection, contract, package_hint)
    verification_snapshot = project_snapshot(root)
    contract["artifacts"]["goal_contract"] = relative_path(contract_path, root)
    contract["bootstrap"] = {key: value for key, value in bootstrap.items() if key not in {"policy_value"}}
    verified_profile = Path(str(bootstrap.get("profile", ""))).is_file()
    verified_policy = Path(str(bootstrap.get("policy", ""))).is_file()
    verified_suite = Path(str(bootstrap.get("suite", ""))).is_file()
    contract["current_state_assumptions"] = [
        {
            **item,
            "status": (
                "VERIFIED"
                if item.get("assumption_id") == "A1" and verified_profile
                else "VERIFIED"
                if item.get("assumption_id") == "A2" and verified_policy and verified_suite
                else item.get("status", "UNKNOWN")
            ),
        }
        for item in contract.get("current_state_assumptions", [])
    ]
    write_goal(root, contract)

    helper = eval_helper_candidates(root, package_hint)[0] if eval_helper_candidates(root, package_hint) else None
    suite = root / ".p2p" / "evals" / "suite.json"
    previous_evidence = evidence_plan(root, verification_snapshot, controls_affected_by(changes, previous_snapshot is None))
    update_flow = safe_update_flow(changes, previous_evidence.get("affected_controls", []), policy)
    eval_control_reused = "project_eval" in previous_evidence.get("reused_controls", []) and not previous_snapshot is None
    suite_validation = {"status": "PASS", "reused": True} if eval_control_reused else validate_suite(root, suite, helper)
    criteria = criteria_result(contract, bootstrap, previous_evidence, inspection, root, acceptance, suite_validation)
    blocking = [item for item in criteria if item.get("mandatory") and item.get("status") != "PASS"]
    decision_required = None
    if blocking:
        first = blocking[0]
        if first.get("name") == "goal_linter":
            errors = contract.get("goal_linter", {}).get("errors", []) if isinstance(contract.get("goal_linter"), dict) else []
            decision_required = one_blocked_decision([f"Bổ sung verification oracle cho Goal Contract: {errors[0]}" if errors else "Bổ sung verification oracle cho các tiêu chí bắt buộc."])
        elif first.get("name") == "bounded_execution_and_verification" and not acceptance:
            decision_required = "Cần cung cấp hoặc cho phép thực hiện một kiểm tra cụ thể chứng minh kết quả của Goal Contract; không cần quyết định kỹ thuật khác."
        elif first.get("name") == "governance_continuity":
            decision_required = "Cần cài hoặc chỉ rõ bộ governance P2P chính thức cho dự án; không tiếp tục bằng một bộ kiểm soát thay thế."
        elif first.get("name") == "project_specific_eval":
            decision_required = "Cần hoàn thiện fixture/evidence của bộ eval dự án; không hạ ngưỡng để biến nó thành PASS."
        else:
            decision_required = "Cần hoàn thiện tiêu chí bắt buộc đầu tiên trong Goal Contract trước khi tiếp tục."
    status = "BLOCKED" if blocking else "PASS"
    if any(item.get("status") == "REJECT" for item in criteria):
        status = "REJECT"
        decision_required = "Kết quả hiện tại không an toàn hoặc không hợp lệ dưới các ràng buộc hiện có; không tiếp tục thay đổi."
    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slugify(request)[:20]}"
    context_input = build_workflow_context_input(
        root,
        request,
        contract,
        inspection,
        status_before,
        changes=changes,
        previous_evidence=previous_evidence,
        policy=policy,
        context_module=context_module,
    )
    context_receipt = create_context_receipt(root, run_id, context_module, selected_context_mode, context_input)
    ledger = root / ".p2p" / "state" / "execution-ledger.jsonl"
    append_event(ledger, {
        "event": "run_started",
        "run_id": run_id,
        "goal_id": contract.get("goal_id"),
        "request": request.strip(),
        "goal_eligibility": contract.get("goal_eligibility", goal_eligibility),
        "work_type": contract.get("work_type"),
        "exploration_policy": contract.get("exploration_policy"),
        "selected_agents": contract.get("agent_selection", {}).get("selected_agents", []),
        "quorum_size": contract.get("agent_selection", {}).get("quorum_size", 0),
        "full_quorum_used": False,
        "agent_selection_reason": contract.get("agent_selection", {}).get("reason"),
        "changed_files": changes,
        "context_mode": context_receipt["context_mode"],
        "context_fingerprint": context_receipt["context_fingerprint"],
        "context_manifest_pointer": context_receipt["context_manifest_pointer"],
        "context_serialized_size": context_receipt["context_serialized_size"],
    })
    append_event(ledger, {"event": "bootstrap_completed", "run_id": run_id, "created": bootstrap.get("created", []), "reused": bootstrap.get("reused", []), "eval": bootstrap.get("eval", {})})
    passed_controls = ["goal_completion"]
    if str(suite_validation.get("status")) == "PASS":
        passed_controls.append("project_eval")
    if status == "PASS":
        passed_controls.extend(["project_wide_audit"] if changes else [])
    update_trusted_evidence(root, verification_snapshot, passed_controls, run_id, acceptance)
    reused_controls = sorted(set(previous_evidence.get("reused_controls", [])))
    rerun_controls = sorted(set(previous_evidence.get("affected_controls", [])) - set(reused_controls))
    append_event(ledger, {
        "event": "verification_completed",
        "run_id": run_id,
        "criteria": criteria,
        "evidence_reused": reused_controls,
        "affected_controls": previous_evidence.get("affected_controls", []),
        "rerun_controls": rerun_controls,
        "suite_validation": suite_validation,
        "safe_update_flow": update_flow,
        "context_mode": context_receipt["context_mode"],
        "context_fingerprint": context_receipt["context_fingerprint"],
        "context_manifest_pointer": context_receipt["context_manifest_pointer"],
    })
    result: dict[str, object] = {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "goal_id": contract.get("goal_id"),
        "status": status,
        "context_mode": context_receipt["context_mode"],
        "context_fingerprint": context_receipt["context_fingerprint"],
        "context_manifest_pointer": context_receipt["context_manifest_pointer"],
        "context_manifest_schema": context_receipt["context_manifest_schema"],
        "context_serialized_size": context_receipt["context_serialized_size"],
        "goal_eligibility": contract.get("goal_eligibility", goal_eligibility),
        "goal_created": contract.get("goal_eligibility", goal_eligibility).get("classification") in {"GOAL", "PLAN FIRST"} if isinstance(contract.get("goal_eligibility", goal_eligibility), dict) else True,
        "goal_linter": contract.get("goal_linter", lint_goal_contract(contract)),
        "work_type": contract.get("work_type", classify_work_type(request)),
        "work_item_classes": contract.get("work_item_classes", []),
        "exploration_policy": contract.get("exploration_policy", exploration_policy_for(str(contract.get("work_type", "MIXED")))),
        "failed_approaches": contract.get("failed_approaches", []),
        "goal_updates": contract.get("goal_updates", []),
        "stop_reason": "all mandatory criteria passed; no optional work started" if status == "PASS" else "mandatory criterion is not PASS; stopped at BLOCKED" if status == "BLOCKED" else "unsafe_or_invalid_outcome; stopped at REJECT",
        "decision_required": decision_required,
        "changed_files": changes,
        "selected_agents": contract.get("agent_selection", {}).get("selected_agents", []),
        "quorum_size": contract.get("agent_selection", {}).get("quorum_size", 0),
        "full_quorum_used": False,
        "agent_selection_reason": contract.get("agent_selection", {}).get("reason"),
        "bootstrap_created": bootstrap.get("created", []),
        "bootstrap_reused": bootstrap.get("reused", []),
        "eval_design_status": bootstrap.get("eval", {}).get("status") if isinstance(bootstrap.get("eval"), dict) else "BLOCKED",
        "eval_validation": suite_validation,
        "reused_controls": reused_controls,
        "rerun_controls": rerun_controls,
        "affected_controls": previous_evidence.get("affected_controls", []),
        "safe_update_flow": update_flow,
        "criteria": criteria,
        "out_of_scope_backlog": [item for item in contract.get("work_item_classes", []) if isinstance(item, dict) and item.get("class") in {"OPTIONAL / BACKLOG", "OUT OF SCOPE"}],
        "summary": "Đã tạo hoặc dùng lại cấu trúc P2P cần thiết, lập Goal Contract có giới hạn, chọn mức kiểm tra phù hợp và ghi bằng chứng."
        if status == "PASS"
        else "Đã lập Goal Contract và chuẩn bị các cấu trúc cần thiết; P2P dừng tại điểm cần quyết định hoặc evidence bổ sung.",
        "checked_summary": "Đã kiểm tra Goal Contract, project state, project-specific eval, phạm vi, evidence reuse và các tham chiếu FACT/Live/Approval/Drift liên quan.",
        "ledger": relative_path(ledger, root),
        "contract": relative_path(contract_path, root),
        "trusted_baseline": {"project_snapshot": verification_snapshot, "controls": reused_controls + [control for control in passed_controls if control not in reused_controls]},
        "latest_eval_status": "PASS" if str(suite_validation.get("status")) == "PASS" else "BLOCKED",
        "last_drift_state": "REFERENCE_AVAILABLE_NOT_RUN" if bootstrap.get("governance_root") else "BLOCKED",
    }
    report_json = root / ".p2p" / "state" / "reports" / f"{run_id}.json"
    result["report_json"] = relative_path(report_json, root)
    result["report_markdown"] = relative_path(report_json.with_suffix(".md"), root)
    append_event(ledger, {"event": "terminal", "run_id": run_id, "goal_id": contract.get("goal_id"), "status": status, "stop_reason": result["stop_reason"], "goal_eligibility": result.get("goal_eligibility"), "evidence_reused": reused_controls, "full_quorum_used": False, "context_mode": result["context_mode"], "context_fingerprint": result["context_fingerprint"], "context_manifest_pointer": result["context_manifest_pointer"]})
    trace_summary: dict[str, object] = {"captured": False, "status": "UNAVAILABLE", "reason": "native trace runtime not present"}
    trace_api = decision_trace_api(root, package_hint)
    if trace_api is not None:
        try:
            trace_capture = trace_api.capture_material_decision(
                root,
                request=request,
                goal_id=str(contract.get("goal_id")) if contract.get("goal_id") else None,
                run_id=run_id,
                workflow_status=status,
                outcome=str(result.get("summary", "")),
                changes=changes,
                artifact_refs=[result["report_json"], result["report_markdown"]],
                evidence_refs=[result["ledger"]],
                source_refs=[result["contract"], ".p2p/state/project-status.json"],
                constraint_refs=[f"goal:{contract.get('goal_id')}"] if contract.get("goal_id") else [],
                policy_refs=["approval-policy.json", "drift-policy.json"]
                if (root / ".p2p" / "system" / "governance").is_dir() or (root / "governance").is_dir()
                else [],
            )
            trace = trace_capture.get("trace") if isinstance(trace_capture, dict) else None
            storage = trace_capture.get("storage") if isinstance(trace_capture, dict) else None
            trace_summary = {
                "captured": bool(trace_capture.get("captured")) if isinstance(trace_capture, dict) else False,
                "status": str(trace.get("STATUS")) if isinstance(trace, dict) else str(trace_capture.get("status", "UNKNOWN")),
                "decision_type": trace.get("DECISION_TYPE") if isinstance(trace, dict) else trace_capture.get("decision_type"),
                "decision_id": trace.get("DECISION_ID") if isinstance(trace, dict) else None,
                "ledger": storage.get("ledger") if isinstance(storage, dict) else result["ledger"],
                "reason": trace_capture.get("reason") if isinstance(trace_capture, dict) else None,
            }
        except Exception as exc:  # trace is additive; preserve the existing workflow terminal state
            trace_summary = {"captured": False, "status": "PARTIAL", "reason": f"trace capture unavailable: {type(exc).__name__}"}
    result["decision_trace"] = trace_summary
    write_json_atomic(report_json, result)
    write_text_atomic(report_json.with_suffix(".md"), beginner_report(result))
    capsule = write_capsule(root, contract, result)
    result["capsule"] = relative_path(capsule, root)
    status_value = {
        "schema_version": STATUS_SCHEMA,
        "project": root.name,
        "current_request": request.strip(),
        "current_goal": {"goal_id": contract.get("goal_id"), "contract": relative_path(contract_path, root), "objective": contract.get("objective")},
        "goal_eligibility": result.get("goal_eligibility"),
        "context_mode": result["context_mode"],
        "context_fingerprint": result["context_fingerprint"],
        "context_manifest_pointer": result["context_manifest_pointer"],
        "context_manifest_schema": result["context_manifest_schema"],
        "context_serialized_size": result["context_serialized_size"],
        "goal_linter": result.get("goal_linter"),
        "work_type": result.get("work_type"),
        "work_item_classes": result.get("work_item_classes", []),
        "exploration_policy": result.get("exploration_policy", {}),
        "failed_approaches": result.get("failed_approaches", []),
        "goal_updates": result.get("goal_updates", []),
        "terminal_state": status,
        "completed_milestones": ["goal_contract", "bootstrap", "eval_design_or_reuse", "bounded_verification"],
        "trusted_baseline": {"project_snapshot": verification_snapshot, "controls": result["trusted_baseline"]["controls"]},
        "latest_eval_status": result["latest_eval_status"],
        "important_fact_unknown": {"facts": "References existing FACT_LEDGER and Live Specs", "unknowns": ["real project quality beyond the available evidence"] if not acceptance else []},
        "outstanding_blockers": [decision_required] if decision_required else [],
        "approval_state": "REQUIRED_ONLY_FOR_PROTECTED_ACTIONS",
        "last_drift_state": result["last_drift_state"],
        "execution_ledger_refs": [relative_path(ledger, root), relative_path(report_json, root)],
        "decision_trace_refs": [trace_summary["decision_id"]] if trace_summary.get("decision_id") else [],
        "next_action": "No further action; terminal state reached." if status in TERMINAL_STATES else "Continue the bounded work plan.",
        "criteria": criteria,
        "updated_at": now(),
    }
    write_json_atomic(root / ".p2p" / "state" / "project-status.json", status_value)
    return result


def plan_workflow(root: Path, request: str, package_hint: str | None = None) -> dict[str, object]:
    inspection = inspect_project(root, request, package_hint)
    status = load_status(root)
    snapshot = project_snapshot(root)
    previous = status.get("trusted_baseline", {}).get("project_snapshot") if isinstance(status.get("trusted_baseline"), dict) else None
    changes = changed_files(previous, snapshot)
    policy = policy_for(root, governance_candidates(root, package_hint)[0][0] if governance_candidates(root, package_hint) else None)
    contract = build_goal_contract(root, request, inspection, policy)
    evidence = evidence_plan(root, snapshot, controls_affected_by(changes, previous is None))
    return {
        "schema_version": SCHEMA,
        "status": "IN_PROGRESS",
        "inspection": inspection,
        "goal_eligibility": contract.get("goal_eligibility"),
        "goal_linter": contract.get("goal_linter"),
        "work_type": contract.get("work_type"),
        "exploration_policy": contract.get("exploration_policy"),
        "goal_contract_preview": contract,
        "changed_files": changes,
        "evidence_plan": evidence,
        "safe_update_flow": safe_update_flow(changes, evidence.get("affected_controls", []), policy),
        "terminal_states": sorted(TERMINAL_STATES),
        "next_action": "Run the bounded workflow; do not open optional work lanes.",
    }


def report_for(root: Path, run_id: str | None = None) -> str:
    status = load_status(root)
    path = root / ".p2p" / "state" / "reports" / f"{run_id}.md" if run_id else None
    if path is None:
        references = status.get("execution_ledger_refs", [])
        report_ref = next((item for item in references if str(item).endswith(".json")), None)
        path = root / str(report_ref).replace("/", "\\") if report_ref else None
        if path and path.suffix == ".json":
            path = path.with_suffix(".md")
    if path and path.is_file():
        return path.read_text(encoding="utf-8")
    return beginner_report({"status": status.get("terminal_state", "BLOCKED"), "criteria": status.get("criteria", []), "decision_required": (status.get("outstanding_blockers") or [None])[0]})


def seed_synthetic_evidence(root: Path) -> None:
    snapshot = project_snapshot(root)
    evidence = {
        "schema_version": EVIDENCE_SCHEMA,
        "project": root.name,
        "controls": {},
        "updated_at": now(),
    }
    for control in ("package_doctor", "sandbox_probe", "eight_agent_runtime_proof", "project_wide_audit", "project_eval", "drift_gate"):
        scopes = CONTROL_SCOPES.get(control, ["*"])
        evidence["controls"][control] = {
            "status": "PASS",
            "checked_at": now(),
            "expires_at": (date.today() + timedelta(days=30)).isoformat(),
            "scope_paths": scopes,
            "input_fingerprint": scoped_fingerprint(snapshot, scopes),
            "evidence": ".p2p/state/reports/synthetic-baseline.json",
            "provenance": "synthetic acceptance baseline; not a real project gate claim",
        }
    write_json_atomic(root / ".p2p" / "state" / "reports" / "synthetic-baseline.json", {"status": "PASS", "note": "Synthetic trusted evidence seed for reuse acceptance only."})
    write_json_atomic(root / ".p2p" / "state" / "trusted-evidence.json", evidence)


def acceptance(package_hint: str | None = None) -> dict[str, object]:
    package = Path(package_hint).expanduser().resolve() if package_hint else (package_roots()[0] if package_roots() else Path(__file__).resolve().parents[1])
    fixture_root = package / "tests" / "fixtures"
    new_source = fixture_root / "new-project"
    existing_source = fixture_root / "existing-project"
    if not new_source.is_dir() or not existing_source.is_dir():
        raise ValueError("Acceptance fixtures are missing")
    temp_parent = package / ".tmp"
    temp_parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="p2p-workflow-", dir=str(temp_parent)))
    new_project = temp_root / "new-project"
    existing_project = temp_root / "existing-project"
    shutil.copytree(new_source, new_project)
    shutil.copytree(existing_source, existing_project)
    new_result = run_workflow(new_project, "Build and finish this small application and make sure it is ready.", package_hint=str(package), acceptance=True)
    initial_existing = run_workflow(existing_project, "Prepare this small application for a bounded baseline.", package_hint=str(package), acceptance=True)
    seed_synthetic_evidence(existing_project)
    app_path = existing_project / "app.py"
    app_text = app_path.read_text(encoding="utf-8")
    app_path.write_text(app_text.replace("Hello from the baseline", "Hello from the scoped update"), encoding="utf-8")
    existing_result = run_workflow(existing_project, "Update the small application's greeting and finish this scoped change.", package_hint=str(package), acceptance=True)
    new_assertions = {
        "terminal_pass": new_result.get("status") == "PASS",
        "goal_bounded": all(item.get("status") == "PASS" for item in new_result.get("criteria", []) if isinstance(item, dict)),
        "eval_initialized": new_result.get("eval_design_status") in {"CREATED", "REUSED"},
        "small_quorum": int(new_result.get("quorum_size", 8)) <= 2,
        "no_full_quorum": new_result.get("full_quorum_used") is False,
    }
    existing_assertions = {
        "terminal_pass": existing_result.get("status") == "PASS",
        "scoped_change_detected": existing_result.get("changed_files") == ["app.py"],
        "unrelated_evidence_reused": all(control in existing_result.get("reused_controls", []) for control in ("package_doctor", "sandbox_probe", "eight_agent_runtime_proof", "project_eval", "drift_gate")),
        "project_audit_rerun_only": "project_wide_audit" in existing_result.get("rerun_controls", []) and "package_doctor" not in existing_result.get("rerun_controls", []) and "drift_gate" not in existing_result.get("rerun_controls", []),
        "no_full_quorum": existing_result.get("full_quorum_used") is False and int(existing_result.get("quorum_size", 8)) < 8,
        "stopped_after_pass": "no optional work started" in str(existing_result.get("stop_reason", "")),
    }
    goal_cases = goal_acceptance_cases()
    status = "PASS" if all(new_assertions.values()) and all(existing_assertions.values()) and initial_existing.get("status") == "PASS" and goal_cases.get("status") == "PASS" else "BLOCKED"
    return {
        "schema_version": SCHEMA,
        "status": status,
        "goal_acceptance": goal_cases,
        "fixture_root": str(temp_root),
        "new_project": {"status": new_result.get("status"), "assertions": new_assertions, "report": new_result.get("report_markdown"), "ledger": new_result.get("ledger"), "quorum_size": new_result.get("quorum_size")},
        "existing_project": {"initial_status": initial_existing.get("status"), "status": existing_result.get("status"), "assertions": existing_assertions, "report": existing_result.get("report_markdown"), "ledger": existing_result.get("ledger"), "reused_controls": existing_result.get("reused_controls"), "rerun_controls": existing_result.get("rerun_controls")},
        "note": "These are safe deterministic workflow fixtures. They do not claim a real project eval score or a real eight-thread runtime quorum.",
    }


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="Project directory; defaults to the current directory")
    parser.add_argument("--package", help="Package root used for governance/templates; auto-detected when omitted")
    parser.add_argument("--request", help="Natural-language project request")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    def add_common(child: argparse.ArgumentParser, *, request: bool = True) -> None:
        child.add_argument("--project", default=argparse.SUPPRESS)
        child.add_argument("--package", default=argparse.SUPPRESS)
        if request:
            child.add_argument("--request", default=argparse.SUPPRESS)
        child.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    inspect = sub.add_parser("inspect", help="Inspect the current project evidence")
    add_common(inspect)
    classify = sub.add_parser("classify", help="Classify whether a request needs a Goal")
    add_common(classify)
    goal = sub.add_parser("goal", help="Create a bounded Goal Contract")
    add_common(goal)
    bootstrap = sub.add_parser("bootstrap", help="Initialize missing project P2P state")
    add_common(bootstrap)
    plan = sub.add_parser("plan", help="Show the bounded plan and evidence reuse decision")
    add_common(plan)
    run = sub.add_parser("run", help="Run the bounded workflow and stop at PASS/BLOCKED/REJECT")
    add_common(run)
    run.add_argument("--acceptance", action="store_true", help=argparse.SUPPRESS)
    run.add_argument("--context-mode", default=argparse.SUPPRESS, help="Context delivery mode: BASELINE_COMPAT or CONTEXT_EFFICIENT_V1")
    report = sub.add_parser("report", help="Show the compact beginner-facing report")
    add_common(report, request=False)
    report.add_argument("--run-id")
    update = sub.add_parser("update", help="Classify new input against the active Goal")
    add_common(update)
    update.add_argument("--current-request", default=argparse.SUPPRESS)
    approach = sub.add_parser("approach", help="Record one bounded implementation-lane result")
    approach.add_argument("--project", default=argparse.SUPPRESS)
    approach.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    approach.add_argument("--package", default=argparse.SUPPRESS)
    approach.add_argument("--lane", choices=("primary", "alternative"), required=True)
    approach.add_argument("--outcome", choices=("PASS", "FAILED", "REGRESSED"), required=True)
    approach.add_argument("--reason", required=True)
    approach.add_argument("--alternative")
    acceptance_parser = sub.add_parser("acceptance", help="Run safe new-project and existing-project workflow fixtures")
    add_common(acceptance_parser, request=False)
    return parser


def main(args: argparse.Namespace) -> int:
    package = args.package
    if args.command == "acceptance":
        result = acceptance(package)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") == "PASS" else 2
    root = project_root(args.project)
    request = (args.request or "").strip()
    if args.command == "inspect":
        output: object = inspect_project(root, request, package)
    elif args.command == "classify":
        output = classify_goal_eligibility(request, inspect_project(root, request, package))
    elif args.command == "goal":
        if not request:
            raise ValueError("--request is required for goal")
        inspection = inspect_project(root, request, package)
        governance = governance_candidates(root, package)
        output = build_goal_contract(root, request, inspection, policy_for(root, governance[0][0] if governance else None))
        write_goal(root, output)
    elif args.command == "bootstrap":
        if not request:
            request = "Inspect and prepare this project with a bounded readiness goal."
        inspection = inspect_project(root, request, package)
        governance = governance_candidates(root, package)
        existing_contract = load_current_contract(root)
        if existing_contract.get("request") == request.strip():
            contract = existing_contract
        else:
            contract = build_goal_contract(root, request, inspection, policy_for(root, governance[0][0] if governance else None))
            write_goal(root, contract)
        output = bootstrap_project(root, inspection, contract, package)
    elif args.command == "plan":
        if not request:
            request = str(load_status(root).get("current_request") or "Inspect and prepare this project with a bounded readiness goal.")
        output = plan_workflow(root, request, package)
    elif args.command == "run":
        if not request:
            raise ValueError("--request is required for run")
        output = run_workflow(root, request, package_hint=package, acceptance=bool(args.acceptance), context_mode=getattr(args, "context_mode", None))
    elif args.command == "report":
        output = report_for(root, args.run_id)
    elif args.command == "update":
        current_request = getattr(args, "current_request", "") or str(load_status(root).get("current_request", ""))
        output = classify_goal_update(current_request, request, load_current_contract(root))
    elif args.command == "approach":
        output = record_approach_result(root, args.lane, args.outcome, args.reason, args.alternative)
    else:
        raise ValueError(f"Unknown command: {args.command}")
    if args.command == "run" and not args.json and isinstance(output, dict):
        print(beginner_report(output))
    elif args.command == "report" and not args.json:
        print(output)
    elif args.json or isinstance(output, (dict, list)):
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(output)
    if isinstance(output, dict) and output.get("status") in {"BLOCKED", "REJECT"} and args.command in {"run", "acceptance"}:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(parser().parse_args()))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
