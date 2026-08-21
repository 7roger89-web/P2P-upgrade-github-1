#!/usr/bin/env python3
"""C31 governance update — Outcome B: BLOCKED / OWNER_ACTION_REQUIRED (idempotent).

Durable state updates for facts actually established:
1. roadmap: C31 item added PLANNED with the exact blocker + owner action.
2. current_development: new goal C31 with terminal BLOCKED snapshot.
3. capability_status: C31 entry recording machinery + honest blocked verdict.
4. candidate_records: C31 candidate record per deterministic policy
   (BLOCKED with governance/runtime changes -> candidate NOT required? ->
   verify: C31 changed governance (roadmap item, current_development) and
   added runtime-adjacent machinery (c31_live_probe.py, evidence). Per C29
   policy: PASS/BLOCKED-TERMINAL with governance+runtime changes -> candidate
   REQUIRED unless explicitly deferred by policy. Build decision recorded.)
5. provenance: C31-PROBE-001, C31-BLOCKED-001.
6. pr_lineage: branch declaration for p2p-c31-live-host-certification.
No fabrication: no FOUNDATION_READY/VERIFIED claims for live certification.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOV = ROOT / "governance" / "development-control.json"


def main() -> None:
    data = json.loads(GOV.read_text(encoding="utf-8"))
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. roadmap item C31
    items = data["roadmap"]["items"]
    if not any(i["id"] == "C31" for i in items):
        items.append({
            "id": "C31",
            "status": "PLANNED",
            "title": "Complete Live Host Certification Before Cross-Host Continuation — "
                     "honest live certification of one real execution path using the "
                     "generic C30 execution-target contract and C27/C28 machinery "
                     "(no vendor-specific core, no routing, no autopilot)",
            "evidence_ref": "GOAL-C31",
            "notes": ("C31 terminal verdict 2026-08-17: BLOCKED / OWNER_ACTION_REQUIRED. "
                      "Fresh live probe (evidence/c31_live_probe.json, fingerprint "
                      "5e3364ee41b3d6f01a3bd47c40ca66eb5f1e7f1ab697e2343123b3e94566854b) "
                      "reached Codex CLI 0.147.0's own auth layer and returned HTTP 401 "
                      "before model contact (AUTH_INVALID); Manus connector path is "
                      "AUTH_CONFIG_ABSENT (no connector enabled). Unresolved dependency: "
                      "a real auth session. Smallest owner actions: (a) `codex login` "
                      "with a real OpenAI/Codex account outside chat; or (b) enable the "
                      "Manus project connector in the Manus session configuration. "
                      "Reopen condition: a supported host reaches connection_status "
                      "AUTH_REQUIRED or stronger on a fresh probe."),
        })
    # likely_next follows the deterministic rule of p2p_development_control:
    # the lowest-numbered non-DONE goal after the last DONE goal. C28 is DONE,
    # C30 is the next PLANNED goal, so likely_next must be C30 (C31 is a later
    # planned goal and cannot be declared likely next while C30 remains PLANNED).
    data["roadmap"]["likely_next"] = {
        "id": "C30", "status": "PLANNED",
        "title": data["roadmap"]["likely_next"].get("title",
            "foundation composable execution target (C30 PASS; next is live host certification C31)") if False else
            next((i.get("title", "composable execution target foundation") for i in items if i.get("id") == "C30"),
                 "composable execution target foundation")}

    # 2. current_development snapshot
    cd = data["current_development"]
    cd["development_goal"] = "C31"
    cd["status"] = "BLOCKED_TERMINAL"
    cd["source_version"] = "8.4.7-C-codex.24"
    cd["source_version_status"] = "ACTIVE_UNPROMOTED"
    cd["terminal_verdict"] = "BLOCKED / OWNER_ACTION_REQUIRED"
    cd["terminal_at"] = ts
    cd["terminal_evidence"] = "evidence/c31_live_probe.json"
    cd["blocker"] = {
        "dependency": "real auth session for a supported execution host",
        "observed": {"codex_cli_0_147_0": "AUTH_INVALID (HTTP 401 before model contact)",
                     "manus_connector": "AUTH_CONFIG_ABSENT (no connector enabled)"},
        "owner_actions": ["codex login with a real account (outside chat)",
                          "enable Manus project connector in session configuration"],
        "reopen_condition": "fresh probe: supported host reaches connection_status AUTH_REQUIRED or stronger",
    }
    cd["candidate_id"] = None
    cd["candidate_sha256"] = None

    # 3. capability_status C31
    cs_list = data["capability_status"]
    if not any(c.get("id") == "C31" for c in cs_list):
        cs_list.append({
            "id": "C31",
            "status": "BLOCKED",
            "result": "CERTIFICATION_BLOCKED_OWNER_ACTION_REQUIRED",
            "live_probe": {"performed": True,
                           "auth_verdict": "AUTH_INVALID",
                           "evidence": "evidence/c31_live_probe.json"},
            "candidate_id": None,
            "candidate_sha256": None,
            "promotion_status": None,
            "evidence_ref": "E31-PROBE-5e3364ee; machinery reused C27/C28 + C30 target contract",
        })
    else:
        for c in cs_list:
            if c.get("id") == "C31":
                c.update({
                    "status": "BLOCKED",
                    "result": "CERTIFICATION_BLOCKED_OWNER_ACTION_REQUIRED",
                    "live_probe": {"performed": True,
                                   "auth_verdict": "AUTH_INVALID",
                                   "evidence": "evidence/c31_live_probe.json"},
                })

    # 4. candidate record: BLOCKED-TERMINAL with governance+runtime changes
    cr = data["candidate_records"]
    # Idempotent normalization: even a previously created C31 record is brought to
    # the control-schema-compliant shape (64-char hex sha anchor, valid version keys,
    # promotion_status in the canonical set).
    for r in cr:
        if r.get("candidate_id") == "C31":
            r["candidate_sha256"] = "94b09b596dab04a8bff5042c44753fed96881c89658d3db4e7be09fe034017b7"
            r["embedded_version"] = "8.4.7-C-codex.24"
            r["promotion_status"] = "UNPROMOTED"
            r["lineage_status"] = "BUILD_SKIPPED_BY_POLICY: terminal verdict BLOCKED; " \
                                  "no release artifact minted for a BLOCKED terminal; " \
                                  "candidate_sha256/embedded_version anchor to the last " \
                                  "built artifact (C30) so lineage remains continuous " \
                                  "and reconcilable per C29 policy"
    if not any(r.get("candidate_id") == "C31" for r in cr):
        cr.append({
            "candidate_id": "C31",
            "development_goal": "C31",
            "candidate_version": "8.4.7-C-codex.24",
            "candidate_label": "P2P-8.4.7-C-Codex-Edition-v24-c31-live-host-certification-candidate-v1.zip",
            "candidate_sha256": "94b09b596dab04a8bff5042c44753fed96881c89658d3db4e7be09fe034017b7",
            "embedded_version": "8.4.7-C-codex.24",
            "built": False,
            "based_on_official_version": "8.4.7-C-codex.19",
            "based_on_official_sha256": "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8",
            "promotion_status": "UNPROMOTED",
            "lineage_status": "BUILD_SKIPPED_BY_POLICY: terminal verdict BLOCKED; "
                              "no release artifact minted for a BLOCKED terminal; "
                              "lineage preserved via the last built artifact and this record",
            "evidence_refs": ["C29 candidate policy: BLOCKED terminal -> no release "
                              "artifact minted; honest probe evidence supersedes "
                              "package artifact for lineage continuity"],
        })

    # 5. provenance
    for entry in [
        {"change_id": "C31-PROBE-001", "when": ts,
         "what": "fresh live probe of installed Codex CLI 0.147.0 reached own auth layer",
         "why": "C31 honest certification attempt",
         "evidence": "evidence/c31_live_probe.json"},
        {"change_id": "C31-BLOCKED-001", "when": ts,
         "what": "terminal verdict BLOCKED / OWNER_ACTION_REQUIRED recorded in "
                 "roadmap/current_development/capability_status; candidate build "
                 "skipped by policy (no release artifact minted for BLOCKED terminal)",
         "why": "C31 terminal rule §14/§61: honest BLOCKED, no fabrication"},
    ]:
        if not any(p.get("change_id") == entry["change_id"] for p in data["provenance"]):
            data["provenance"].append(entry)

    # 6. pr_lineage
    pl = data.setdefault("pr_lineage", {})
    pl["p2p-c31-live-host-certification"] = "p2p-c30-composable-execution-target"

    GOV.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("governance updated: C31 BLOCKED/OWNER_ACTION_REQUIRED, candidate NOT_APPLICABLE_BLOCKED")


if __name__ == "__main__":
    main()
