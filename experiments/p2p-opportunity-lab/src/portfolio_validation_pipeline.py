from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

from src.concierge_engine import canonical_equipment
from src.percentage_semantics import resolve_percentage_charges
from src.portfolio_semantics import compare_fcl_portfolios


def _requirements(context: dict[str, Any]) -> dict[str, int]:
    raw = context.get("equipment_requirements")
    if not isinstance(raw, dict) or not raw:
        raise ValueError("equipment_requirements must be a non-empty object")
    result: dict[str, int] = {}
    for raw_equipment, raw_quantity in raw.items():
        equipment = canonical_equipment(raw_equipment)
        try:
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            raise ValueError(f"invalid equipment quantity for {raw_equipment!r}")
        if quantity <= 0:
            raise ValueError(f"equipment quantity must be positive for {raw_equipment!r}")
        result[equipment] = result.get(equipment, 0) + quantity
    return result


def _pseudo_quote(
    *,
    quote_id: str,
    currency: str,
    charges: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "quote_id": quote_id,
        "currency": currency,
        "charges": deepcopy(charges),
    }


def _rebase_offer_percentages(
    resolved_charges: list[dict[str, Any]],
    audit: dict[str, Any],
    quantity: int,
) -> list[dict[str, Any]]:
    if quantity <= 0:
        raise ValueError("equipment quantity must be positive")

    resolved_totals = {
        item["line_id"]: Decimal(item["resolved_total"])
        for item in audit.get("resolutions", [])
    }
    result = deepcopy(resolved_charges)
    for charge in result:
        line_id = str(charge.get("line_id") or "").strip()
        if line_id not in resolved_totals:
            continue
        charge["amount"] = str(resolved_totals[line_id] / Decimal(quantity))
        charge["basis"] = "PER_CONTAINER"
        existing_note = str(charge.get("note") or "").strip()
        suffix = f"portfolio rebased across {quantity} x {canonical_equipment(charge.get('equipment') or '')}".strip()
        charge["note"] = f"{existing_note}; {suffix}" if existing_note else suffix
    return result


def _blocked_sentinel(provider_set: dict[str, Any]) -> dict[str, Any]:
    sentinel = deepcopy(provider_set)
    sentinel["offers"] = []
    sentinel["shared_charges"] = []
    return sentinel


def compare_fcl_portfolios_validated(
    provider_sets: list[dict[str, Any]],
    context: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(provider_sets, list) or len(provider_sets) < 2:
        raise ValueError("at least two provider quote sets are required")

    requirements = _requirements(context)
    resolved_sets: list[dict[str, Any]] = []
    percentage_audit: list[dict[str, Any]] = []
    blocked_provider_ids: set[str] = set()
    blocked_reasons: dict[str, list[str]] = {}

    for index, raw_provider_set in enumerate(provider_sets, start=1):
        if not isinstance(raw_provider_set, dict):
            raise ValueError(f"provider quote set {index} must be an object")

        provider_set = deepcopy(raw_provider_set)
        provider = str(provider_set.get("provider") or f"provider-{index}").strip()
        quote_set_id = str(provider_set.get("quote_set_id") or provider).strip()
        currency = str(provider_set.get("currency") or "").strip().upper()
        provider_audit = {
            "quote_set_id": quote_set_id,
            "provider": provider,
            "status": "READY",
            "offers": [],
            "shared": None,
            "errors": [],
        }

        offers = provider_set.get("offers")
        if isinstance(offers, list):
            for offer_index, offer in enumerate(offers, start=1):
                if not isinstance(offer, dict):
                    continue
                equipment = canonical_equipment(offer.get("equipment"))
                quantity = requirements.get(equipment)
                if quantity is None:
                    continue
                charges = offer.get("charges")
                if not isinstance(charges, list) or not charges:
                    continue

                offer_id = str(offer.get("offer_id") or equipment)
                resolved, audit = resolve_percentage_charges(
                    _pseudo_quote(
                        quote_id=f"{quote_set_id}::{offer_id}",
                        currency=currency,
                        charges=charges,
                    ),
                    {
                        "containers": quantity,
                        "shipments": 1,
                        "bl_count": 1,
                        "weight_kg": context.get("weight_kg", 0),
                        "cbm": context.get("cbm", 0),
                    },
                )
                provider_audit["offers"].append({
                    "offer_id": offer_id,
                    "equipment": equipment,
                    "quantity": quantity,
                    "audit": audit,
                })
                if audit["status"] == "BLOCKED":
                    provider_audit["status"] = "BLOCKED"
                    provider_audit["errors"].extend(
                        f"{equipment}:PERCENTAGE:{item['type']}" for item in audit["errors"]
                    )
                    continue

                offer["charges"] = _rebase_offer_percentages(
                    resolved["charges"],
                    audit,
                    quantity,
                )

        shared_charges = provider_set.get("shared_charges")
        if isinstance(shared_charges, list) and shared_charges:
            resolved, audit = resolve_percentage_charges(
                _pseudo_quote(
                    quote_id=f"{quote_set_id}::SHARED",
                    currency=currency,
                    charges=shared_charges,
                ),
                {
                    "containers": sum(requirements.values()),
                    "shipments": int(context.get("shipments", 1)),
                    "bl_count": int(context.get("bl_count", 1)),
                    "weight_kg": context.get("weight_kg", 0),
                    "cbm": context.get("cbm", 0),
                },
            )
            provider_audit["shared"] = audit
            if audit["status"] == "BLOCKED":
                provider_audit["status"] = "BLOCKED"
                provider_audit["errors"].extend(
                    f"SHARED:PERCENTAGE:{item['type']}" for item in audit["errors"]
                )
            else:
                provider_set["shared_charges"] = resolved["charges"]

        percentage_audit.append(provider_audit)
        if provider_audit["status"] == "BLOCKED":
            blocked_provider_ids.add(quote_set_id)
            blocked_reasons[quote_set_id] = sorted(set(provider_audit["errors"]))
            resolved_sets.append(_blocked_sentinel(provider_set))
        else:
            resolved_sets.append(provider_set)

    result = compare_fcl_portfolios(resolved_sets, context)

    for row in result.get("excluded", []):
        quote_set_id = row.get("quote_set_id")
        if quote_set_id in blocked_provider_ids:
            existing = set(row.get("reasons", []))
            existing.discard("MISSING_OFFERS")
            existing.update(blocked_reasons.get(quote_set_id, []))
            row["reasons"] = sorted(existing)

    result["percentage_audit"] = percentage_audit
    result["validated_portfolio_pipeline"] = True
    return result
