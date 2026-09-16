"""Native Git-diff -> Code-Impact Evidence adapter.

This module makes the existing P2P Code-Impact Evidence Contract usable on a
real worktree. It is deliberately native-first and read-only with respect to
the target repository:

- changed files come from ``worktree_evidence.complete_worktree_summary``;
- Python import impact uses the existing ``quality_intelligence`` AST logic;
- baseline and current import graphs are conservatively unioned so deleted or
  renamed Python modules do not silently erase their former dependents;
- symbol changes compare baseline Git blobs with current file contents;
- unsupported code-language changes are surfaced as a residual native gap,
  not guessed away.

The adapter may create a temporary directory outside the repository to
reconstruct the baseline Python tree for deterministic AST analysis. It never
writes into the target repository, never stages/commits, and never starts a
service. External code-intelligence tooling remains optional and may only be
considered when this native evidence reports a concrete residual gap.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping

from p2p_capabilities import quality_intelligence as qi
from p2p_capabilities.worktree_evidence import (
    WorktreeEvidenceError,
    complete_worktree_summary,
)

SCHEMA = "p2p-native-code-impact-evidence/1"

# Code-like extensions where Python AST cannot establish full structural
# impact. Config/docs/data extensions are intentionally not listed here: they
# can matter to acceptance, but they are outside this code-graph contract and
# must be verified by their own evidence lanes.
UNSUPPORTED_CODE_EXTENSIONS = frozenset(
    {
        ".c",
        ".cc",
        ".cpp",
        ".cs",
        ".go",
        ".h",
        ".hpp",
        ".java",
        ".js",
        ".jsx",
        ".kt",
        ".kts",
        ".php",
        ".rb",
        ".rs",
        ".scala",
        ".sh",
        ".swift",
        ".ts",
        ".tsx",
    }
)


class NativeCodeImpactError(RuntimeError):
    """Fail-closed error for native worktree impact evidence."""


def _run_git(root: Path, args: list[str], *, allow_nonzero: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode and not allow_nonzero:
        message = (result.stderr or result.stdout).strip()
        raise NativeCodeImpactError(f"GIT_COMMAND_FAILED:{args[0]}:{message}")
    return result


def _git_text(root: Path, ref: str, relative_path: str) -> str:
    result = _run_git(root, ["show", f"{ref}:{relative_path}"], allow_nonzero=True)
    if result.returncode:
        return ""
    return result.stdout


def _baseline_python_paths(root: Path, baseline: str) -> tuple[str, ...]:
    result = _run_git(root, ["ls-tree", "-r", "--name-only", "-z", baseline, "--"])
    return tuple(
        sorted(
            path
            for path in result.stdout.split("\0")
            if path and Path(path).suffix.lower() == ".py"
        )
    )


def _baseline_import_graph(root: Path, baseline: str) -> dict[str, tuple[str, ...]]:
    """Reconstruct baseline Python tree in temp storage and reuse native AST logic."""
    paths = _baseline_python_paths(root, baseline)
    if not paths:
        return {}

    with tempfile.TemporaryDirectory(prefix="p2p-native-impact-") as temp_dir:
        snapshot = Path(temp_dir)
        for relative in paths:
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_git_text(root, baseline, relative), encoding="utf-8")
        return qi._import_map(snapshot)  # same native parser/semantics as current tree


def _merge_graphs(*graphs: Mapping[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    merged: dict[str, set[str]] = {}
    for graph in graphs:
        for module, dependencies in graph.items():
            merged.setdefault(module, set()).update(dependencies)
    return {module: tuple(sorted(deps)) for module, deps in sorted(merged.items())}


def _symbol_changes(root: Path, baseline: str, python_paths: tuple[str, ...]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for relative in python_paths:
        before = _git_text(root, baseline, relative)
        target = root / relative
        try:
            after = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
        except OSError:
            after = ""
        record = qi.SymbolChange.changed_symbols(relative, before, after)
        changes.append({"path": record.path, "symbols": list(record.symbols)})
    return changes


def _unsupported_code_files(changed_files: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            path
            for path in changed_files
            if Path(path).suffix.lower() in UNSUPPORTED_CODE_EXTENSIONS
        )
    )


def native_code_impact_summary(root: str | Path, baseline: str) -> dict[str, Any]:
    repo = Path(root).expanduser().resolve()
    worktree = complete_worktree_summary(repo, baseline)
    changed_files = tuple(str(path) for path in worktree["changed_files"])
    python_changed = tuple(
        sorted(path for path in changed_files if Path(path).suffix.lower() == ".py")
    )
    unsupported_code = _unsupported_code_files(changed_files)

    if not python_changed and not unsupported_code:
        return {
            "schema": SCHEMA,
            "status": "NOT_APPLICABLE",
            "native_scope_status": "NOT_APPLICABLE",
            "baseline_commit": worktree["baseline_commit"],
            "head_commit": worktree["head_commit"],
            "changed_files": list(changed_files),
            "python_changed_files": [],
            "unsupported_code_files": [],
            "impact": None,
            "changed_symbols": [],
            "external_extension_recommended": False,
            "native_gap_reason": None,
            "repository_mutated": False,
            "acceptance_authority": False,
        }

    current_graph = qi._import_map(repo)
    baseline_graph = _baseline_import_graph(repo, worktree["baseline_commit"])
    combined_graph = _merge_graphs(baseline_graph, current_graph)

    impact: dict[str, Any] | None = None
    if python_changed:
        impact = qi.affected_surface(
            changed_paths=python_changed,
            import_graph=combined_graph,
            analysis_complete=True,
        )
        impact["changed_symbols"] = _symbol_changes(
            repo,
            worktree["baseline_commit"],
            python_changed,
        )

    gap_reasons: list[str] = []
    if unsupported_code:
        gap_reasons.append(
            "native Python AST does not establish structural impact for: "
            + ", ".join(unsupported_code)
        )
    if python_changed and (impact is None or impact.get("impact_unknown")):
        gap_reasons.append("native Python impact analysis is incomplete or unknown")

    scope_status = "PARTIAL" if gap_reasons else "FULL"
    status = "PARTIAL" if gap_reasons else "PASS"

    return {
        "schema": SCHEMA,
        "status": status,
        "native_scope_status": scope_status,
        "baseline_commit": worktree["baseline_commit"],
        "head_commit": worktree["head_commit"],
        "changed_files": list(changed_files),
        "python_changed_files": list(python_changed),
        "unsupported_code_files": list(unsupported_code),
        "impact": impact,
        "changed_symbols": (impact or {}).get("changed_symbols", []),
        "external_extension_recommended": bool(gap_reasons),
        "native_gap_reason": "; ".join(gap_reasons) if gap_reasons else None,
        "graph_semantics": "BASELINE_UNION_CURRENT_NATIVE_AST",
        "baseline_graph_module_count": len(baseline_graph),
        "current_graph_module_count": len(current_graph),
        "combined_graph_module_count": len(combined_graph),
        "repository_mutated": False,
        "acceptance_authority": False,
    }


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--baseline", required=True)
    args = parser.parse_args()

    try:
        result = native_code_impact_summary(args.root, args.baseline)
    except (OSError, WorktreeEvidenceError, NativeCodeImpactError) as exc:
        _print({"schema": SCHEMA, "status": "BLOCKED", "error": str(exc)})
        return 2
    _print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
