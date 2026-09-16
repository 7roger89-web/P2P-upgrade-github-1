from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.charge_semantics import compare_quotes_guarded
from src.percentage_semantics import resolve_percentage_charges


def compare_quotes_validated(raw_quotes: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_quotes, list) or len(raw_quotes) < 2:
        raise ValueError("at least two quotes are required")

    resolved_quotes = []
    percentage_audit = []
    blocked = []

    for raw_quote in raw_quotes:
        resolved, audit = resolve_percentage_charges(raw_quote, context)
        resolved_quotes.append(resolved)
        percentage_audit.append(audit)
        if audit["status"] == "BLOCKED":
            blocked.append(audit)

    if blocked:
        return {
            "comparison_basis": {
                "route": None,
                "equipment": None,
                "currency": None,
                "context": deepcopy(context),
                "selection_mode": "PERCENTAGE_GUARD_BLOCKED",
                "fx_applied": False,
            },
            "comparison_groups": [],
            "route_alias_audit": [],
            "required_charge_codes": [],
            "coverage_matrix": [],
            "priced_quotes": [],
            "ranking": [],
            "excluded": [
                {
                    "quote_id": audit["quote_id"],
                    "reasons": sorted({item["type"] for item in audit["errors"]}),
                }
                for audit in blocked
            ],
            "percentage_audit": percentage_audit,
            "decision_warning": "UNRESOLVED_PERCENTAGE_SEMANTICS",
        }

    result = compare_quotes_guarded(resolved_quotes, context)
    result["percentage_audit"] = percentage_audit
    result["validated_pipeline"] = True
    return result
