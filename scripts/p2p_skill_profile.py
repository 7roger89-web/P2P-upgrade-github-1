#!/usr/bin/env python3
"""Select the smallest packaged P2P skill profile that fits a target project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = "p2p-capability-profile/1"

PROFILE_AUTO = "AUTO"
PROFILE_ALL = "ALL"
PROFILE_CORE = "CORE"
PROFILE_FRONTEND_GENERIC = "FRONTEND_GENERIC"
PROFILE_FRONTEND_REACT = "FRONTEND_REACT"
PROFILES = (
    PROFILE_ALL,
    PROFILE_CORE,
    PROFILE_FRONTEND_GENERIC,
    PROFILE_FRONTEND_REACT,
)

FRONTEND_GENERIC_SKILLS = frozenset(
    {
        "frontend-design",
        "frontend-development",
        "baseline-ui",
    }
)
FRONTEND_REACT_SKILLS = frozenset(
    {
        "react-best-practices",
        "composition-patterns",
        "frontend-code-review",
        "react-doctor",
    }
)
FRONTEND_SPECIALIST_SKILLS = FRONTEND_GENERIC_SKILLS | FRONTEND_REACT_SKILLS

REACT_PACKAGES = frozenset(
    {
        "react",
        "react-dom",
        "next",
        "@remix-run/react",
        "gatsby",
    }
)
GENERIC_FRONTEND_PACKAGES = frozenset(
    {
        "vue",
        "svelte",
        "@angular/core",
        "astro",
        "preact",
        "solid-js",
        "vite",
        "@vitejs/plugin-vue",
        "@vitejs/plugin-react",
    }
)
PYTHON_FRONTEND_MARKERS = (
    "streamlit",
    "gradio",
    "dash",
    "nicegui",
    "reflex",
    "panel",
)


def _package_names(root: Path) -> set[str]:
    package_json = root / "package.json"
    if not package_json.is_file():
        return set()
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    if not isinstance(payload, dict):
        return set()
    names: set[str] = set()
    for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        values = payload.get(field)
        if isinstance(values, dict):
            names.update(str(name) for name in values)
    return names


def _python_dependency_text(root: Path) -> str:
    candidates = (
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "Pipfile",
        "poetry.lock",
        "uv.lock",
    )
    chunks: list[str] = []
    for name in candidates:
        path = root / name
        if not path.is_file():
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace").lower())
        except OSError:
            continue
    return "\n".join(chunks)


def detect_profile(root: Path) -> tuple[str, list[str]]:
    """Return (profile, evidence) using deterministic project-local markers."""
    root = root.resolve()
    package_names = _package_names(root)

    react_hits = sorted(package_names & REACT_PACKAGES)
    next_configs = sorted(path.name for path in root.glob("next.config.*") if path.is_file())
    if react_hits or next_configs:
        evidence = [f"package:{name}" for name in react_hits]
        evidence.extend(f"file:{name}" for name in next_configs)
        return PROFILE_FRONTEND_REACT, evidence

    generic_hits = sorted(package_names & GENERIC_FRONTEND_PACKAGES)
    generic_files: list[str] = []
    for relative in (
        "index.html",
        "streamlit_app.py",
        "angular.json",
        "svelte.config.js",
        "svelte.config.ts",
        "astro.config.js",
        "astro.config.mjs",
        "astro.config.ts",
    ):
        if (root / relative).is_file():
            generic_files.append(relative)
    generic_files.extend(
        path.name for path in sorted(root.glob("vite.config.*")) if path.is_file()
    )
    python_text = _python_dependency_text(root)
    python_hits = sorted(
        marker for marker in PYTHON_FRONTEND_MARKERS if marker in python_text
    )
    if generic_hits or generic_files or python_hits:
        evidence = [f"package:{name}" for name in generic_hits]
        evidence.extend(f"file:{name}" for name in generic_files)
        evidence.extend(f"python:{name}" for name in python_hits)
        return PROFILE_FRONTEND_GENERIC, evidence

    return PROFILE_CORE, ["no-supported-frontend-marker"]


def available_skills(skills_dir: Path) -> set[str]:
    if not skills_dir.is_dir():
        raise ValueError(f"skills directory does not exist: {skills_dir}")
    return {
        path.name
        for path in skills_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def expected_skills_for_profile(
    all_skills: Iterable[str],
    profile: str,
) -> set[str]:
    skills = set(all_skills)
    if profile == PROFILE_ALL:
        return skills
    if profile not in PROFILES:
        raise ValueError(f"unsupported capability profile: {profile}")
    selected = skills - FRONTEND_SPECIALIST_SKILLS
    if profile in {PROFILE_FRONTEND_GENERIC, PROFILE_FRONTEND_REACT}:
        selected.update(FRONTEND_GENERIC_SKILLS & skills)
    if profile == PROFILE_FRONTEND_REACT:
        selected.update(FRONTEND_REACT_SKILLS & skills)
    return selected


def build_receipt(
    root: Path,
    skills_dir: Path,
    *,
    requested_profile: str = PROFILE_AUTO,
) -> dict[str, object]:
    if requested_profile == PROFILE_AUTO:
        profile, evidence = detect_profile(root)
    else:
        profile = requested_profile
        evidence = ["explicit-installer-scope"] if profile == PROFILE_ALL else ["explicit-profile"]
    all_skills = available_skills(skills_dir)
    selected = expected_skills_for_profile(all_skills, profile)
    return {
        "schema_version": SCHEMA_VERSION,
        "profile": profile,
        "detection_evidence": evidence,
        "selected_skills": sorted(selected),
        "excluded_pack_skills": sorted(all_skills - selected),
        "preserve_existing_unselected_skills": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--skills-dir", type=Path, required=True)
    parser.add_argument(
        "--profile",
        choices=(PROFILE_AUTO,) + PROFILES,
        default=PROFILE_AUTO,
    )
    parser.add_argument(
        "--format",
        choices=("json", "lines", "profile"),
        default="json",
    )
    args = parser.parse_args()

    receipt = build_receipt(
        args.root,
        args.skills_dir,
        requested_profile=args.profile,
    )
    if args.format == "json":
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.format == "lines":
        for skill in receipt["selected_skills"]:
            print(skill)
    else:
        print(receipt["profile"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
