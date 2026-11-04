from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

BEHAVIOR_STATUSES = {
    "CONTACTED",
    "OPTED_IN",
    "SUBMITTED",
    "COMPLETED",
    "REPEAT_REQUEST",
    "DECLINED",
    "NO_RESPONSE",
    "TRUST_ISSUE",
    "WTP_SIGNAL",
    "PAID",
}


def summarize_observations(
    observations: Iterable[dict[str, Any]],
    *,
    target_contacts: int,
    submission_success: int,
    repeat_or_wtp_success: int,
) -> dict[str, Any]:
    rows = list(observations)
    if target_contacts < 1 or submission_success < 1 or repeat_or_wtp_success < 1:
        raise ValueError("thresholds must be positive")

    seen_participants = set()
    counts = defaultdict(int)
    per_participant: dict[str, set[str]] = defaultdict(set)
    observed_money_evidence = []

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("observation must be an object")
        participant_id = str(row.get("participant_id") or "").strip()
        status = row.get("status")
        if not participant_id:
            raise ValueError("participant_id is required")
        if status not in BEHAVIOR_STATUSES:
            raise ValueError(f"invalid status: {status!r}")

        seen_participants.add(participant_id)
        per_participant[participant_id].add(status)
        counts[status] += 1

        if status == "WTP_SIGNAL":
            amount = row.get("wtp_amount")
            if amount is None:
                raise ValueError("WTP_SIGNAL requires explicit wtp_amount")
            observed_money_evidence.append({
                "class": "OBSERVED",
                "signal": "WILLINGNESS_TO_PAY",
                "source": str(row.get("source") or f"participant:{participant_id}"),
                "note": str(
                    row.get("note")
                    or f"{participant_id} explicitly stated willingness to pay {amount} {row.get('wtp_currency') or ''}"
                ).strip(),
            })
        elif status == "PAID":
            amount = row.get("wtp_amount")
            observed_money_evidence.append({
                "class": "OBSERVED",
                "signal": "PAYMENT",
                "source": str(row.get("source") or f"participant:{participant_id}"),
                "note": str(
                    row.get("note")
                    or f"{participant_id} completed an observed paid validation transaction"
                    + (f" of {amount} {row.get('wtp_currency') or ''}" if amount is not None else "")
                ),
            })

    contacted = sum(
        1
        for statuses in per_participant.values()
        if "CONTACTED" in statuses or statuses & (BEHAVIOR_STATUSES - {"NO_RESPONSE"})
    )
    submitted = sum(
        1
        for statuses in per_participant.values()
        if statuses & {"SUBMITTED", "COMPLETED", "REPEAT_REQUEST", "WTP_SIGNAL", "PAID"}
    )
    completed = sum(
        1
        for statuses in per_participant.values()
        if statuses & {"COMPLETED", "REPEAT_REQUEST", "WTP_SIGNAL", "PAID"}
    )
    repeat_or_wtp = sum(
        1
        for statuses in per_participant.values()
        if statuses & {"REPEAT_REQUEST", "WTP_SIGNAL", "PAID"}
    )
    declined = sum(1 for statuses in per_participant.values() if "DECLINED" in statuses)
    trust_issues = sum(1 for statuses in per_participant.values() if "TRUST_ISSUE" in statuses)

    success_threshold_reached = (
        submitted >= submission_success
        and repeat_or_wtp >= repeat_or_wtp_success
    )

    terminal_contacted = contacted >= target_contacts
    failure_threshold_reached = (
        terminal_contacted
        and submitted < submission_success
        and repeat_or_wtp < repeat_or_wtp_success
    )

    if success_threshold_reached or failure_threshold_reached:
        status = "COMPLETED"
    elif rows:
        status = "RUNNING"
    else:
        status = "NOT_STARTED"

    return {
        "status": status,
        "source_class": "OBSERVED",
        "participants_seen": len(seen_participants),
        "contacted": contacted,
        "submitted": submitted,
        "completed": completed,
        "repeat_or_wtp": repeat_or_wtp,
        "declined": declined,
        "trust_issues": trust_issues,
        "success_threshold_reached": success_threshold_reached,
        "failure_threshold_reached": failure_threshold_reached,
        "money_evidence": observed_money_evidence,
    }
