#!/usr/bin/env python3
"""C31 ledger reconciliation — honest Outcome B (BLOCKED) additions.

Rules honored:
- Only record facts actually established (fresh probe result, machinery reuse).
- Do NOT mark live certification FOUNDATION_READY/VERIFIED.
- Extend/reuse existing machinery records (REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY,
  SECURE_HOST_CONNECTION_ONBOARDING, C28_CANDIDATE_PACKAGING_AND_C29_CLOSURE_RECONCILIATION,
  COMPOSABLE_EXECUTION_TARGET) via evidence_refs + next_condition, not parallel records.
- Provenance required (provenance_notes cite governance + evidence file).
- No cycles: C31 records depend ON existing FOUNDATION_READY records only.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"

PROBE_FINGERPRINT = "5e3364ee41b3d6f01a3bd47c40ca66eb5f1e7f1ab697e2343123b3e94566854b"
EVIDENCE = "evidence/c31_live_probe.json"


def new_record(capability_id: str, **kw) -> dict:
    base = {
        "capability_id": capability_id,
        "name": kw.get("name", capability_id.replace("_", " ").title()),
        "family": kw.get("family", "HOST_CERTIFICATION"),
        "beginner_value": kw.get("beginner_value", ""),
        "principle": kw.get("principle", "HONEST_CERTIFICATION_BOUNDARY"),
        "origin_refs": kw.get("origin_refs", []),
        "status": kw.get("status", "BLOCKED"),
        "implementation_refs": kw.get("implementation_refs", []),
        "evidence_refs": kw.get("evidence_refs", []),
        "dependencies": kw.get("dependencies", []),
        "known_gaps": kw.get("known_gaps", []),
        "do_not_duplicate_with": kw.get("do_not_duplicate_with", []),
        "next_condition": kw.get("next_condition", ""),
        "last_reviewed": "2026-08-17",
        "freshness": "verified_against_filesystem",
        "notes": kw.get("notes", ""),
        "provenance_notes": kw.get("provenance_notes", ""),
        "origin_type": kw.get("origin_type", "DIRECT_IMPLEMENTATION"),
    }
    return base


def main() -> None:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    caps = {c["capability_id"]: c for c in data["capabilities"]}

    def upsert(rec: dict) -> None:
        cid = rec["capability_id"]
        if cid in caps:
            caps[cid].update(rec)
        else:
            data["capabilities"].append(rec)

    common = dict(
        beginner_value=(
            "The Owner never has to understand probes or receipts; the system reports "
            "an honest one-word certification status and the smallest real action."),
        evidence_refs=[EVIDENCE],
        last_reviewed="2026-08-17",
        freshness="verified_against_filesystem",
    )

    # 1. Fresh honest probe of the installed host (Codex CLI 0.147.0)
    upsert(new_record(
        "C31_LIVE_AUTH_PROBE_FRESH_EVIDENCE",
        family="MULTI_AI_INTEROPERABILITY",
        principle="PRESENT_NOT_VALID",
        status="PARTIAL",
        name="C31 Fresh Live Auth Probe (Honest Negative Evidence)",
        beginner_value=(
            "P2P honestly re-tested the already-installed Codex tool with a live probe "
            "and reported the true result: it cannot sign in by itself yet."),
        origin_refs=["governance/development-control.json (provenance C31-PROBE-001)",
                     "scripts/p2p_live_certification.py",
                     "c31_live_probe.py",
                     "docs/p2p-development/research/execution-target-pattern-research.md"],
        implementation_refs=["c31_live_probe.py", "scripts/p2p_live_certification.py"],
        evidence_refs=[EVIDENCE, "E27-PROBE-1f71d9b55eb78d8e"],
        dependencies=["REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY",
                      "SECURE_HOST_CONNECTION_ONBOARDING"],
        origin_type="PROJECT_LEARNING",
        known_gaps=[],
        do_not_duplicate_with=["REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY"],
        next_condition=(
            "Re-open only when a fresh probe against a supported host returns "
            "connection_status AUTH_REQUIRED or stronger (owner action: codex login, "
            "or enable the Manus project connector)."),
        notes=(
            "Fresh probe 2026-08-17: Codex CLI 0.147.0 reached its own auth layer "
            "(wss://api.openai.com/v1/responses) and returned HTTP 401 Unauthorized "
            "before model contact; verdict AUTH_INVALID. Confirms the immutable C27 "
            "fact with fresh evidence. Manus connector path: AUTH_CONFIG_ABSENT "
            "(no connector enabled in session configuration). No model call, no "
            "mutation, ephemeral session, no secrets stored."),
        provenance_notes=(
            "Directly implemented in C31. Evidence: " + EVIDENCE + " (fingerprint "
            + PROBE_FINGERPRINT + "). Extends the deterministic probe surface of "
            "scripts/p2p_live_certification.py and the CODEX_CLI_0_147_0_LINUX adapter "
            "of scripts/p2p_secure_onboarding.py. Upstream research: C27 terminal "
            "report E27-PROBE-1f71d9b55eb78d8e."),
    ))

    # 2. C30 target contract exercised as intake path (extend COMPOSABLE_EXECUTION_TARGET)
    upsert(new_record(
        "C31_EXECUTION_TARGET_AS_CERTIFICATION_INTAKE",
        family="MULTI_AI_INTEROPERABILITY",
        principle="UNKNOWN_NOT_SUPPORTED",
        status="PLANNED",
        name="C31 Execution-Target Contract as Certification Intake",
        beginner_value=(
            "Once a host can sign in, P2P will describe it through one neutral "
            "profile (harness + provider + model + protocol + tools) instead of "
            "hard-coded brand logic."),
        origin_refs=["governance/development-control.json (provenance C31-BLOCKED-001)",
                     "scripts/p2p_execution_target.py",
                     "docs/p2p-development/research/execution-target-pattern-research.md"],
        implementation_refs=["scripts/p2p_execution_target.py"],
        evidence_refs=[EVIDENCE],
        dependencies=["COMPOSABLE_EXECUTION_TARGET", "HARNESS_AUTH_PROFILE",
                      "MODEL_PROVIDER_AUTH_PROFILE"],
        known_gaps=["No live host yet certified; profile population remains planned."],
        do_not_duplicate_with=["COMPOSABLE_EXECUTION_TARGET",
                               "REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY"],
        next_condition=(
            "Populate ExecutionTarget profile from real probe evidence once a host "
            "reaches AUTH_REQUIRED or stronger; produce target_fingerprint and record "
            "it in the live spec."),
        notes=(
            "C31 intended (planned, not yet implemented) to exercise the C30 "
            "provider-neutral contract as the intake surface for certification "
            "(harness=CODEX_CLI_0_147_0_LINUX, transport=openai-completion-ws). "
            "No router, no autopilot, no vendor-specific core. Implementation is "
            "not claimed; blocked by owner auth action."),
        origin_type="OWNER_ACCEPTED_PROPOSAL",
        provenance_notes=(
            "Planned in C31 on top of the C30 durable research artifact "
            "(execution-target-pattern-research.md). Reuses COMPOSABLE_EXECUTION_TARGET "
            "machinery; no code copied from third-party repositories."),
    ))

    # 3. Owner-action dependency made durable
    upsert(new_record(
        "C31_OWNER_AUTH_ACTION_DEPENDENCY",
        family="RECOVERY_AND_CONTINUATION",
        principle="OWNER_ACTION_IRREDUCIBLE",
        status="PLANNED",
        name="C31 Irreducible Owner Auth Action",
        beginner_value=(
            "The only thing the Owner must do is one sign-in (`codex login`) or "
            "toggle one setting (Manus connector). Everything else stays automated."),
        origin_refs=[            "governance/development-control.json (provenance C31-BLOCKED-001)"],
        implementation_refs=[],
        evidence_refs=[EVIDENCE],
        dependencies=["SECURE_HOST_CONNECTION_ONBOARDING"],
        origin_type="PROJECT_LEARNING",
        known_gaps=[
            "Sandbox proxy OPENAI_API_KEY does not authenticate against Codex's own "
            "transport (HTTP 401 before model contact).",
            "No Manus project connector enabled; no MANUS_PROJECT_CONNECTOR credential "
            "in environment; api.manus.im returns 404."],
        do_not_duplicate_with=["SECURE_HOST_CONNECTION_ONBOARDING"],
        next_condition=(
            "Owner performs `codex login` (real OpenAI/Codex account, outside chat) "
            "or enables the Manus project connector; fresh probe then re-evaluates."),
        notes=(
            "Terminal blocker for C31: BLOCKED / OWNER_ACTION_REQUIRED (CODEX_AUTH). "
            "Smallest actions identified by adapter safe_owner_action fields. Secrets "
            "never pasted into chat; no unofficial browser automation substituted."),
        provenance_notes=(
            "Directly established in C31 probe loop. Governance: development-control "
            "current_development.blocker. Extends the safe_owner_action contract of "
            "scripts/p2p_secure_onboarding.py adapters."),
    ))

    # 4. Extend existing machinery record with C31 evidence (next_condition refresh)
    mach = caps.get("REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY")
    if mach:
        mach["next_condition"] = (
            "Awaiting owner auth action (codex login or Manus connector enable); "
            "fresh probe evidence now stored at " + EVIDENCE)
        mach["evidence_refs"] = list(dict.fromkeys(
            mach.get("evidence_refs", []) + [EVIDENCE]))
        mach["last_reviewed"] = "2026-08-17"

    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    n = len(data["capabilities"])
    print(f"ledger now {n} records; C31 additions upserted (ESTABLISHED_HONESTLY/PLANNED/BLOCKED, no FOUNDATION_READY fabrication)")


if __name__ == "__main__":
    main()
