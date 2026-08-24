#!/usr/bin/env python3
"""Deterministic updater for the P2P managed README orientation block.

The README remains a projection.  The caller supplies the managed content;
this module never invents authority, promotion, approval, or host state.
Only the marked slice is replaceable.  Ambiguous markers fail closed.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

BEGIN_MARKER = "<!-- P2P:BEGIN ORIENTATION -->"
END_MARKER = "<!-- P2P:END ORIENTATION -->"


class OrientationError(ValueError):
    """Raised when a README cannot be updated without risking owner text."""


@dataclass(frozen=True)
class UpdateResult:
    """Observable result of one managed-block update."""

    path: str
    changed: bool
    created: bool


def _marker_positions(document: str) -> tuple[list[int], list[int]]:
    begins: list[int] = []
    ends: list[int] = []
    offset = 0
    while True:
        position = document.find(BEGIN_MARKER, offset)
        if position < 0:
            break
        begins.append(position)
        offset = position + len(BEGIN_MARKER)
    offset = 0
    while True:
        position = document.find(END_MARKER, offset)
        if position < 0:
            break
        ends.append(position)
        offset = position + len(END_MARKER)
    return begins, ends


def _normalise_managed_content(content: str) -> str:
    if BEGIN_MARKER in content or END_MARKER in content:
        raise OrientationError(
            "managed content must not contain orientation markers; "
            "the updater owns those markers"
        )
    if "\x00" in content:
        raise OrientationError("managed content contains a NUL byte")
    return content.replace("\r\n", "\n").replace("\r", "\n").strip("\n")


def render_managed_block(content: str) -> str:
    """Render one canonical marker block from explicit content."""

    normalised = _normalise_managed_content(content)
    if not normalised:
        raise OrientationError("managed content must not be empty")
    return f"{BEGIN_MARKER}\n{normalised}\n{END_MARKER}"


def replace_managed_block(document: str, content: str) -> str:
    """Replace or append the managed block while preserving all other text.

    Existing bytes outside the returned marker slice are not normalised.  The
    caller can therefore preserve LF/CRLF owner content and any surrounding
    Markdown exactly.
    """

    managed = render_managed_block(content)
    begins, ends = _marker_positions(document)
    if not begins and not ends:
        if not document:
            return managed + "\n"
        separator = "" if document.endswith(("\n", "\r")) else "\n"
        return document + separator + managed + "\n"
    if len(begins) != 1 or len(ends) != 1:
        raise OrientationError(
            "README must contain exactly one begin marker and one end marker"
        )
    begin = begins[0]
    end = ends[0]
    if begin > end:
        raise OrientationError("orientation end marker precedes begin marker")
    end_after_marker = end + len(END_MARKER)
    return document[:begin] + managed + document[end_after_marker:]


def extract_managed_block(document: str) -> str | None:
    """Return the complete managed block, or ``None`` when it is absent."""

    begins, ends = _marker_positions(document)
    if not begins and not ends:
        return None
    if len(begins) != 1 or len(ends) != 1 or begins[0] > ends[0]:
        raise OrientationError("README contains ambiguous orientation markers")
    end_after_marker = ends[0] + len(END_MARKER)
    return document[begins[0]:end_after_marker]


def _read_utf8(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OrientationError(f"README is not valid UTF-8: {path}") from exc


def update_readme(readme_path: Path, managed_content: str) -> UpdateResult:
    """Update one explicitly selected README path, without implicit fallback."""

    existed = readme_path.exists()
    original = _read_utf8(readme_path) if existed else ""
    updated = replace_managed_block(original, managed_content)
    changed = updated != original
    if changed:
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        readme_path.write_bytes(updated.encode("utf-8"))
    return UpdateResult(
        path=str(readme_path),
        changed=changed,
        created=not existed,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    update = subparsers.add_parser(
        "update", help="replace the managed block in one explicit README"
    )
    update.add_argument("--readme", type=Path, required=True)
    update.add_argument("--content-file", type=Path, required=True)
    inspect = subparsers.add_parser(
        "inspect", help="inspect marker state without changing the README"
    )
    inspect.add_argument("--readme", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "update":
            content = _read_utf8(args.content_file)
            result = update_readme(args.readme, content)
            print(json.dumps(asdict(result), sort_keys=True))
            return 0
        document = _read_utf8(args.readme)
        block = extract_managed_block(document)
        print(json.dumps({"path": str(args.readme), "present": block is not None}))
        return 0
    except (OSError, OrientationError) as exc:
        print(f"p2p_orientation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
