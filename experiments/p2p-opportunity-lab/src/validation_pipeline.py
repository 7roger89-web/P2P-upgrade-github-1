from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.charge_semantics import compare_quotes_guarded
from src.fx_semantics import resolve_fx
from src.percentage_semantics import resolve_percentage_charges


def _blocked_result(
    *,
    context: dict[str, Any],
    audits: list[dict[str, Any]],
    audit_key: str,
    selection_mode: str,
    warning: str,
) -> dict[str, Any]:
    blocked = [audit for audit in audits if audit["status"] == "BLOCKED"]
    return {
        "comparison_basis": {
            "route": None,
            "equipment": None,
            "currency": None,
            "context": deepcopy(context),
            "selection_mode": selection_mode,
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
        audit_key: audits,
        "decision_warning": warning,
    }


def compare_quotes_validated(raw_quotes: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_quotes, list) or len(raw_quotes) < 2:
        raise ValueError("at least two quotes are required")

    fx_resolved_quotes = []
    fx_audit = []
    for raw_quote in raw_quotes:
        resolved, audit = resolve_fx(raw_quote, context)
        fx_resolved_quotes.append(resolved)
        fx_audit.append(audit)

    if any(audit["status"] == "BLOCKED" for audit in fx_audit):
        return _blocked_result(
            context=context,
            audits=fx_audit,
            audit_key="fx_audit",
            selection_mode="FX_GUARD_BLOCKED",
            warning="UNRESOLVED_FX_SEMANTICS",
        )

    percentage_resolved_quotes = []
    percentage_audit = []
    for quote in fx_resolved_quotes:
        resolved, audit = resolve_percentage_charges(quote, context)
        percentage_resolved_quotes.append(resolved)
        percentage_audit.append(audit)

    if any(audit["status"] == "BLOCKED" for audit in percentage_audit):
        result = _blocked_result(
            context=context,
            audits=percentage_audit,
            audit_key="percentage_audit",
            selection_mode="PERCENTAGE_GUARD_BLOCKED",
            warning="UNRESOLVED_PERCENTAGE_SEMANTICS",
        )
        result["fx_audit"] = fx_audit
        return result

    result = compare_quotes_guarded(percentage_resolved_quotes, context)
    result["fx_audit"] = fx_audit
    result["percentage_audit"] = percentage_audit
    result["validated_pipeline"] = True
    if result.get("comparison_basis") is not None:
        result["comparison_basis"]["fx_applied"] = any(audit["conversions"] for audit in fx_audit)
    return result
