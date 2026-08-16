#!/usr/bin/env python3
"""Verify the GitHub-ready zip contains nothing excluded."""
import zipfile
from pathlib import Path

OUT = Path("/home/ubuntu/p2p/P2P-8.4.6-C-Codex-Edition-v4-github-ready.zip")

BAD = [
    "__pycache__", ".anvien", ".p2p/state", ".p2p/edge-runs", ".p2p/install-backups",
    ".p2p/evals/runs", ".p2p/gates", ".p2p/approvals", ".p2p/usage.json",
    ".p2p/project-profile.json", ".tmp", "NOTES-classification", "package_for_github",
    "scan_secrets", ".pyc", ".coverage",
]

with zipfile.ZipFile(OUT) as zf:
    names = zf.namelist()
    total = 0
    leaks = []
    sizes = {}
    for n in names:
        total += 1
        rel = n.split("/", 1)[1] if "/" in n else n
        if any(rel.startswith(b) or b in rel.split("/") for b in BAD):
            leaks.append(n)
        top = rel.split("/")[0]
        sizes[top] = sizes.get(top, rel)  # placeholder
    print(f"total entries: {total}")
    print(f"leaks: {len(leaks)}")
    for l in leaks[:20]:
        print("  LEAK:", l)
    # size by top dir
    from collections import Counter
    c = Counter()
    for n in names:
        c[n.split("/", 1)[1].split("/")[0]] += 1
    print("\nentries by top dir:")
    for k, v in sorted(c.items()):
        print(f"  {k}: {v}")
    # check key files exist
    for must in [
        "P2P-8.4.6-C-Codex-Edition-v4/VERSION",
        "P2P-8.4.6-C-Codex-Edition-v4/governance/development-control.json",
        "P2P-8.4.6-C-Codex-Edition-v4/.p2p/system/scripts/p2p_uiux.py",
        "P2P-8.4.6-C-Codex-Edition-v4/.gitignore",
        "P2P-8.4.6-C-Codex-Edition-v4/tests/test_p2p_task_targeted_context.py",
        "P2P-8.4.6-C-Codex-Edition-v4/AGENTS.md",
        "P2P-8.4.6-C-Codex-Edition-v4/source/supplemental/H\u01b0\u1edbng d\u1eabn ph\u1ea7n 1.docx",
    ]:
        print("OK  " if must in names else "MISS", must)
