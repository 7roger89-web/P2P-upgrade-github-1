#!/usr/bin/env python3
"""Dump C31 evidence file fields for the terminal report."""
import json

e = json.load(open("evidence/c31_live_probe.json", encoding="utf-8"))
print("TOP KEYS:", sorted(e.keys()))
for k, v in e.items():
    if k != "probes":
        print(f"{k} = {json.dumps(v)[:200]}")
print("---PROBES---")
for i, p in enumerate(e.get("probes", [])):
    print(f"probe {i}:", json.dumps(p)[:400])
print("---LEDGER C31-RELATED---")
l = json.load(open("docs/p2p-development/capability-ledger/capability-index.json", encoding="utf-8"))
caps = l["capabilities"]
first = caps[0]
print("record field names:", list(first.keys()))
for c in caps:
    cid = c.get("capability_id") or c.get("id") or ""
    refs = str(c.get("origin_refs", ""))
    if "C31" in cid or "C31" in refs:
        print(cid, "|", c.get("status"), "|", c.get("family"))
