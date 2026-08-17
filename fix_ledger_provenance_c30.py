#!/usr/bin/env python3
"""Fix ledger provenance defects from C30 records (cp09, cp18).

- cp09: OWNER_ACCEPTED_PROPOSAL records must have a notes/body statement that
  implementation is NOT claimed.
- cp18: records born from ARCHITECTURE_INVARIANT origin_type must cite the
  charter (or upstream source) in an origin_refs/notes field matching
  case-insensitive 'charter'/'invariant'/'AI-handoff'.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "docs/p2p-development/capability-ledger/capability-index.json"
CHARTER_REF = "docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md"

data = json.loads(LEDGER.read_text(encoding="utf-8"))

DISCLAIMER = ("Recorded intent only — implementation is not claimed; runtime work "
              "requires a later goal with its own evidence contract.")

FIXED = []
for c in data["capabilities"]:
    origin = (c.get("origin_type") or "").upper()

    if origin == "OWNER_ACCEPTED_PROPOSAL":
        notes = c.get("notes") or ""
        low = notes.lower()
        if not ("not" in low or "intent" in low or "planned" in low):
            c["notes"] = (notes.rstrip() + " " + DISCLAIMER).strip()
            FIXED.append(f"{c['capability_id']}: notes disclaimer added")
        elif CHARTER_REF not in c.get("origin_refs", []):
            c.setdefault("origin_refs", []).append(CHARTER_REF)
            FIXED.append(f"{c['capability_id']}: charter origin_ref added")

    if origin == "ARCHITECTURE_INVARIANT":
        refs = " ".join(c.get("origin_refs", [])) + " " + (c.get("notes") or "")
        low = refs.lower()
        if not ("charter" in low or "invariant" in low or "ai-handoff" in low):
            if CHARTER_REF not in c["origin_refs"]:
                c["origin_refs"].append(CHARTER_REF)
            FIXED.append(f"{c['capability_id']}: charter reference added "
                         f"(origin {origin})")

LEDGER.write_text(
    json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("\n".join(FIXED) or "nothing to fix")
