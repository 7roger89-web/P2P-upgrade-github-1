"""C30 Phase-1: recover durable state baseline before any C30 change."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
G = ROOT / "governance" / "development-control.json"
L = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"
g = json.load(open(G))
l = json.load(open(L))

print("=== roadmap keys ===")
rm = g["roadmap"]
print("roadmap type:", type(rm).__name__)
if isinstance(rm, dict):
    items = rm.get("items") or rm
else:
    items = rm
if isinstance(items, dict):
    for i in list(items)[-4:]:
        print(items[i].get("id") or i, items[i].get("status"))
else:
    for i in items[-4:]:
        print(i.get("id"), i.get("status"))
for k in ("current", "likely_next"):
    print(k, ":", rm.get(k))
print("=== current_development ===")
cd = g["current_development"]
if isinstance(cd, dict):
    for k, v in cd.items():
        if k not in ("source_version",):
            print(" ", k, "=", json.dumps(v)[:120])
print("=== candidate_records (tail 3) ===")
cr = g.get("candidate_records", [])
for c in cr[-3:]:
    print(" ", c.get("development_goal"), c.get("candidate_sha256", "")[:10], c.get("promotion_status"), c.get("candidate_version"))
print("n candidates:", len(cr))
print("=== ledger ===")
caps = l.get("capabilities") or l
print("record count:", len(caps))
print("sample keys:", list(caps[0].keys()))
print("=== existing concepts scan (research-relevant) ===")
concepts = [
    "EXECUTION", "HARNESS", "PROVIDER", "MODEL", "PROTOCOL", "TOOL", "WORKSPACE",
    "ENVIRONMENT", "AUTH", "PERMISSION", "FRESHNESS", "EFFECTIVE", "ELIGIB",
    "BACKEND", "DRIFT", "DIAGNOS", "AUTOMATED", "AUTOPILOT", "PLANNER", "VERIFY",
    "FALLBACK", "QUIESCE", "DRAIN", "HEALTH", "ISOLATION", "HEADLESS", "TOKEN",
    "REPO_MAP", "PROJECT_MAP", "CONTEXT", "GITHUB", "BROWSER", "TASK_REQUIREMENT",
]
ids = [c.get("capability_id", c.get("id")) for c in caps]
for c in concepts:
    hits = [x for x in ids if c in x]
    if hits:
        print(f"  {c}: {hits}")
print("=== families ===")
fams = l.get("families", {})
if isinstance(fams, dict):
    for k in list(fams):
        print(" ", k, "|", json.dumps(fams[k])[:80])
