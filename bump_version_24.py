#!/usr/bin/env python3
"""Bump all runtime version surfaces from .23 to .24 for the C30 candidate."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
OLD = "8.4.7-C-codex.23"
NEW = "8.4.7-C-codex.24"

targets = [
    ("VERSION", None),
    (".p2p/system/VERSION", None),
    ("manifest/package.json", "version"),
    (".p2p/system/p2p.manifest.json", "package_version"),
    (".p2p/system/p2p_uiux/__init__.py", None),
]

for rel, field in targets:
    path = ROOT.joinpath(rel)
    text = path.read_text()
    if NEW in text:
        print(f"skip (already {NEW}): {rel}")
        continue
    if field:
        payload = json.loads(text)
        payload[field] = NEW
        out = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        out = text.replace(OLD, NEW)
    path.write_text(out)
    print(f"bumped {rel} -> {NEW}")
