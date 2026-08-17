#!/usr/bin/env python3
"""Detect all cycles in the ledger dependency graph."""
from __future__ import annotations
import json

by = {
    c["capability_id"]: c.get("dependencies", [])
    for c in json.load(open("docs/p2p-development/capability-ledger/capability-index.json"))["capabilities"]
}

def find_cycles(cid, stack, path):
    if cid in path:
        cut = path.index(cid)
        yield path[cut:] + [cid]
        return
    if cid not in by or cid in stack:
        return
    stack.add(cid)
    path.append(cid)
    for d in by[cid]:
        yield from find_cycles(d, stack, path)
    path.pop()
    stack.discard(cid)

seen = set()
reported = 0
for cid in sorted(by):
    for cyc in find_cycles(cid, set(), []):
        key = frozenset(cyc)
        if key in seen:
            continue
        seen.add(key)
        print("CYCLE:", " -> ".join(cyc))
        reported += 1
print(f"total distinct cycles: {reported}")
