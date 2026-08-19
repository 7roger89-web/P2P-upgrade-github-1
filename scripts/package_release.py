#!/usr/bin/env python3
"""Build and verify a clean, reusable P2P Codex release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from p2p_development_control import (
        ControlError,
        load_control,
        validate_control,
        validate_lineage_for_build,
        version_is_at_least,
    )
except ModuleNotFoundError:
    scripts_root = Path(__file__).resolve().parent
    if str(scripts_root) not in sys.path:
        sys.path.insert(0, str(scripts_root))
    from p2p_development_control import (
        ControlError,
        load_control,
        validate_control,
        validate_lineage_for_build,
        version_is_at_least,
    )


SCHEMA = "p2p-codex-release-manifest/1"
CHECKSUM_NAME = "RELEASE-SHA256SUMS.txt"
MANIFEST_NAME = "release-manifest.json"
FORBIDDEN_FRAGMENTS = (
    "/.tmp/",
    "/reports/",
    "/docs/plans/",
    "/experimental/",
    "/.p2p/",
    "/__pycache__/",
)
ROOT_FILES = (
    "VERSION",
    "AGENTS.md",
    "BAT-DAU.md",
    "NOTICE.md",
    "RELEASE-NOTES.md",
    "install.ps1",
    "install.sh",
    "doctor.ps1",
)
DOC_FILES = (
    "docs/AI-HANDOFF.md",
    "docs/CAP-NHAT.md",
    "docs/KIEN-TRUC.md",
    "docs/PHAN-TICH-CHIEU-NGANG-DOC.md",
    "docs/QUAN-TRI-FACT-EVAL-RAG.md",
    "docs/SU-DUNG.md",
)
SCRIPT_FILES = (
    "scripts/doctor.py",
    "scripts/p2p_approval.py",
    "scripts/p2p_decision_trace.py",
    "scripts/p2p_eval.py",
    "scripts/p2p_gate.py",
    "scripts/p2p_governance.py",
    "scripts/p2p_foreground_execution.py",
    "scripts/p2p_delegation.py",
    "scripts/p2p_parallel.py",
    "scripts/p2p_development_control.py",
    "scripts/p2p_task_state.py",
    "scripts/p2p_workflow.py",
    "scripts/package.ps1",
    "scripts/package.sh",
    "scripts/package_release.py",
    "scripts/update_from_release.py",
)
DIRECTORIES = (
    ".agents/skills",
    ".codex/agents",
    "docs/SPEC",
    "docs/decisions",
    "governance",
    "manifest",
    "mapping",
    "source",
)
UIUX_RUNTIME_SCRIPT_MAP = (
    ("p2p_uiux.py", "p2p_uiux.py"),
    ("p2p_router.py", "p2p_router.py"),
    ("p2p_governance.py", "p2p_uiux_governance.py"),
    ("p2p_uiux_eval.py", "p2p_uiux_eval.py"),
    ("p2p_eval.py", "p2p_uiux_eval_impl.py"),
    ("doctor.py", "p2p_uiux_doctor.py"),
    ("drift_check.py", "p2p_uiux_drift_check.py"),
    ("secret_scan.py", "p2p_uiux_secret_scan.py"),
)
UIUX_RUNTIME_FILES = (
    "VERSION",
    "p2p.manifest.json",
    "references/UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md",
    "docs/evals/p2p-uiux-eval-suite.json",
)
FOUNDATION_RUNTIME_MODULES = (
    "__init__.py",
    "beginner.py",
    "context.py",
    "domain.py",
    "evidence.py",
    "foreground_execution.py",
    "bounded_delegation.py",
    "parallel_execution.py",
    "orchestration_policy.py",
    "isolation.py",
    "model.py",
    "providers.py",
    "routing.py",
    "skill_standard.py",
    "specialist.py",
    "task_state.py",
    "trust.py",
    "decision_trace.py",
)
FOUNDATION_RUNTIME_FILES = ("p2p_capabilities/capabilities.json",)
FOUNDATION_RUNTIME_SCRIPTS = (
    "p2p_capability_doctor.py",
    "p2p_decision_trace.py",
    "p2p_host_identity_hook.py",
)
RELEASE_SKILLS = (
    "bb4pda",
    "notebook-pack",
    "p2p",
    "p2p-uiux",
    "p2p-atlas",
    "p2p-approval",
    "p2p-capsule",
    "p2p-chain",
    "p2p-download",
    "p2p-eval",
    "p2p-explore",
    "p2p-feedback",
    "p2p-idea",
    "p2p-karpathy",
    "p2p-metrics",
    "p2p-pxpipe",
    "p2p-quorum",
    "p2p-scope",
    "p2p-teacher",
    "pxpipe",
    "rag-grounding",
    "rag-prep",
    "rag-router",
)
COPYTREE_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object JSON: {path}")
    return value


def package_version(root: Path) -> str:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError("VERSION is empty")
    manifest = load_json(root / "manifest" / "package.json")
    if manifest.get("version") != version:
        raise ValueError("VERSION and manifest/package.json version differ")
    return version


def selected_paths(root: Path) -> list[str]:
    paths: list[str] = list(ROOT_FILES) + list(DOC_FILES) + list(SCRIPT_FILES)
    paths.extend((f"{directory}/" for directory in DIRECTORIES))
    paths.append(".codex/config.toml")
    missing = [relative for relative in paths if not (root / relative.rstrip("/")).exists()]
    if missing:
        raise ValueError("Required release paths are missing: " + ", ".join(missing))
    validate_uiux_runtime(root)
    return paths


def validate_uiux_runtime(root: Path) -> Path:
    runtime_source = root / ".p2p" / "system"
    missing = [relative for relative in UIUX_RUNTIME_FILES if not (runtime_source / relative).is_file()]
    missing.extend(
        f"scripts/{source_name}"
        for source_name, _ in UIUX_RUNTIME_SCRIPT_MAP
        if not (runtime_source / "scripts" / source_name).is_file()
    )
    if not (runtime_source / "p2p_uiux").is_dir():
        missing.append("p2p_uiux/")
    if missing:
        raise ValueError("Required installed UI/UX runtime paths are missing: " + ", ".join(missing))
    return runtime_source


def validate_foundation_runtime(root: Path) -> Path:
    runtime_source = root / ".p2p" / "system"
    foundation = runtime_source / "p2p_capabilities"
    missing = [relative for relative in FOUNDATION_RUNTIME_FILES if not (runtime_source / relative).is_file()]
    missing.extend(
        f"p2p_capabilities/{name}"
        for name in FOUNDATION_RUNTIME_MODULES
        if not (foundation / name).is_file()
    )
    missing.extend(
        f"scripts/{name}"
        for name in FOUNDATION_RUNTIME_SCRIPTS
        if not (runtime_source / "scripts" / name).is_file()
    )
    if missing:
        raise ValueError("Required capability foundation runtime paths are missing: " + ", ".join(missing))
    return runtime_source


def copy_uiux_runtime(root: Path, stage: Path) -> None:
    runtime_source = validate_uiux_runtime(root)
    runtime = stage / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    for relative in UIUX_RUNTIME_FILES:
        source = runtime_source / relative
        target = runtime / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def copy_foundation_runtime(root: Path, stage: Path) -> None:
    runtime_source = validate_foundation_runtime(root)
    runtime = stage / "runtime"
    shutil.copytree(
        runtime_source / "p2p_capabilities",
        runtime / "p2p_capabilities",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    for script_name in FOUNDATION_RUNTIME_SCRIPTS:
        source = runtime_source / "scripts" / script_name
        target = runtime / "scripts" / script_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copytree(
        runtime_source / "p2p_uiux",
        runtime / "p2p_uiux",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    for source_name, output_name in UIUX_RUNTIME_SCRIPT_MAP:
        source = runtime_source / "scripts" / source_name
        target = runtime / "scripts" / output_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def copy_selected(root: Path, stage: Path) -> list[str]:
    paths = selected_paths(root)
    for relative in paths:
        source = root / relative.rstrip("/")
        target = stage / relative.rstrip("/")
        if relative == ".agents/skills/":
            target.mkdir(parents=True, exist_ok=True)
            for name in RELEASE_SKILLS:
                skill_source = source / name
                if not skill_source.is_dir():
                    raise ValueError(f"Required release skill is missing: {name}")
                shutil.copytree(skill_source, target / name, ignore=COPYTREE_IGNORE)
            continue
        if source.is_dir():
            shutil.copytree(source, target, symlinks=True, ignore=COPYTREE_IGNORE)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    copy_uiux_runtime(root, stage)
    copy_foundation_runtime(root, stage)
    return paths + ["runtime/"]


def iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())


def relative_files(root: Path) -> list[str]:
    return [path.relative_to(root).as_posix() for path in iter_files(root)]


def assert_clean_paths(root: Path) -> None:
    forbidden = []
    for relative in relative_files(root):
        normalized = "/" + relative
        if any(fragment in normalized for fragment in FORBIDDEN_FRAGMENTS) or relative.endswith((".pyc", ".pyo")):
            forbidden.append(relative)
    if forbidden:
        raise ValueError("Forbidden development/transient paths in release: " + ", ".join(forbidden[:12]))


def regenerate_source_checksums(root: Path) -> None:
    """Refresh the existing canonical checksum list without self-hashing it."""
    checksum_path = root / "manifest" / "sha256sums.txt"
    paths = selected_paths(root)
    files: list[Path] = []
    for relative in paths:
        source = root / relative.rstrip("/")
        if source.is_file() and relative != "manifest/sha256sums.txt":
            files.append(source)
        elif source.is_dir():
            files.extend(path for path in iter_files(source) if path != checksum_path)
    lines = [f"{sha256(path)}  {path.relative_to(root).as_posix()}" for path in sorted(set(files))]
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def refresh_runtime_lock(root: Path) -> None:
    command = [
        sys.executable,
        str(root / "scripts" / "p2p_governance.py"),
        "lock-runtime",
        "--root",
        str(root),
        "--governance",
        str(root / "governance"),
        "--reason",
        "Release package build",
    ]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, capture_output=True, text=True, check=False, env=environment)
    if result.returncode:
        raise RuntimeError((result.stdout or result.stderr).strip() or "runtime lock failed")


def write_release_metadata(stage: Path, version: str, selected: list[str]) -> None:
    content_files = relative_files(stage)
    if MANIFEST_NAME in content_files or CHECKSUM_NAME in content_files:
        raise ValueError("Release metadata names collide with selected source files")
    package_manifest = load_json(stage / "manifest" / "package.json")
    manifest = {
        "schema_version": SCHEMA,
        "package_name": package_manifest.get("name", "P2P Codex Edition"),
        "package_version": version,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "selected_roots": selected,
        "excluded_fragments": list(FORBIDDEN_FRAGMENTS),
        "file_count": len(content_files),
        "files": [
            {
                "path": relative,
                "size": (stage / relative).stat().st_size,
                "sha256": sha256(stage / relative),
            }
            for relative in content_files
        ],
    }
    (stage / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checksum_paths = content_files + [MANIFEST_NAME]
    checksum_lines = [f"{sha256(stage / relative)}  {relative}" for relative in checksum_paths]
    (stage / CHECKSUM_NAME).write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")


def verify_stage(stage: Path) -> dict[str, object]:
    assert_clean_paths(stage)
    manifest = load_json(stage / MANIFEST_NAME)
    if manifest.get("schema_version") != SCHEMA:
        raise ValueError("release-manifest.json has the wrong schema")
    listed = manifest.get("files")
    if not isinstance(listed, list):
        raise ValueError("release-manifest.json files is not a list")
    expected = {str(item.get("path")) for item in listed if isinstance(item, dict)}
    actual = set(relative_files(stage)) - {MANIFEST_NAME, CHECKSUM_NAME}
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"release inventory mismatch; missing={missing[:8]}, extra={extra[:8]}")
    for item in listed:
        if not isinstance(item, dict):
            raise ValueError("release manifest contains a non-object file entry")
        path = stage / str(item["path"])
        if path.stat().st_size != int(item["size"]) or sha256(path) != item["sha256"]:
            raise ValueError(f"release manifest hash mismatch: {item['path']}")
    checksum_lines = (stage / CHECKSUM_NAME).read_text(encoding="utf-8").splitlines()
    checksum_map = {}
    for line in checksum_lines:
        digest, separator, relative = line.partition("  ")
        if not separator or len(digest) != 64:
            raise ValueError(f"invalid release checksum line: {line}")
        checksum_map[relative] = digest
    checksum_expected = expected | {MANIFEST_NAME}
    if set(checksum_map) != checksum_expected:
        raise ValueError("release checksum inventory does not match release manifest")
    for relative, digest in checksum_map.items():
        if sha256(stage / relative) != digest:
            raise ValueError(f"release checksum mismatch: {relative}")
    package_manifest = load_json(stage / "manifest" / "package.json")
    if package_manifest.get("version") != manifest.get("package_version"):
        raise ValueError("release package manifest version mismatch")
    development_control = None
    control_path = stage / "governance" / "development-control.json"
    if control_path.is_file():
        try:
            control = load_control(control_path)
            development_control = validate_control(control)
        except ControlError as exc:
            raise ValueError(f"embedded development-control validation failed [{exc.code}]: {exc.message}") from exc
        embedded_version = str(manifest.get("package_version"))
        if not version_is_at_least(embedded_version):
            raise ValueError("embedded development-control package version is below the promoted baseline")
        current = control.get("current_development")
        if not isinstance(current, dict) or current.get("source_version") != embedded_version:
            raise ValueError("embedded development-control source version does not match the package")
    result = {
        "status": "PASS",
        "package_version": manifest.get("package_version"),
        "file_count": len(expected),
        "checksum_count": len(checksum_map),
    }
    if development_control is not None:
        result["development_control"] = development_control
    return result


def run_gate(stage: Path, script: str, args: list[str]) -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, str(stage / "scripts" / script), *args],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    if result.returncode:
        raise RuntimeError(f"{script} failed:\n{result.stdout}\n{result.stderr}")


def build(root: Path, output: Path) -> dict[str, object]:
    root = root.resolve()
    output = output.resolve()
    if output.exists():
        raise ValueError(f"Output already exists; choose another path to preserve history: {output}")
    version = package_version(root)
    lineage = validate_lineage_for_build(root, version)
    selected = selected_paths(root)
    refresh_runtime_lock(root)
    regenerate_source_checksums(root)
    stage_parent = root / ".tmp"
    stage_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="p2p-release-stage-", dir=str(stage_parent)))
    try:
        selected = copy_selected(root, stage)
        refresh_runtime_lock(stage)
        write_release_metadata(stage, version, selected)
        verification = verify_stage(stage)
        run_gate(stage, "doctor.py", ["--package", str(stage)])
        run_gate(stage, "p2p_governance.py", ["drift", "--root", str(stage), "--governance", str(stage / "governance")])
        verification = verify_stage(stage)
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in iter_files(stage):
                info = zipfile.ZipInfo(path.relative_to(stage).as_posix(), date_time=(2010, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return {
        "status": "PASS",
        "package_version": version,
        "artifact": str(output),
        "artifact_sha256": sha256(output),
        "artifact_size": output.stat().st_size,
        "lineage": lineage,
        "content": verification,
    }


def artifact_name(version: str) -> str:
    match = re.fullmatch(r"(?P<release>.+)-codex\.(?P<revision>\d+)", version)
    if not match:
        raise ValueError(f"Cannot derive release artifact name from VERSION: {version}")
    return f"P2P-{match.group('release')}-Codex-Edition-v{match.group('revision')}.zip"


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output")
    parser.add_argument("--package", help="Extracted package root for verify")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="Build a clean release ZIP")
    sub.add_parser("verify", help="Verify an extracted release package")
    return parser


def main(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if args.command == "build":
        if args.output:
            output = Path(args.output).expanduser().resolve()
        else:
            version = package_version(root)
            output = root.parent / artifact_name(version)
        result = build(root, output)
    else:
        package = Path(args.package or root).expanduser().resolve()
        result = verify_stage(package)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main(parser().parse_args()))
    except (ControlError, OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

