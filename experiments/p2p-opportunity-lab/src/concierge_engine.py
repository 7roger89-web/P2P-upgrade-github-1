from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any

SUPPORTED_BASES = {
    "PER_SHIPMENT",
    "PER_CONTAINER",
    "PER_BL",
    "PER_KG",
    "PER_CBM",
    "INCLUDED",
    "UNKNOWN",
}

CHARGE_ALIASES = {
    "OCEAN FREIGHT": "FREIGHT",
    "SEA FREIGHT": "FREIGHT",
    "BASE FREIGHT": "FREIGHT",
    "FREIGHT": "FREIGHT",
    "THC": "THC",
    "TERMINAL HANDLING": "THC",
    "TERMINAL HANDLING CHARGE": "THC",
    "DOC": "DOC",
    "DOCUMENT": "DOC",
    "DOCUMENTATION": "DOC",
    "DOCUMENTATION FEE": "DOC",
    "BILL OF LADING": "BL",
    "BL FEE": "BL",
    "BAF": "BAF",
    "CAF": "CAF",
    "PSS": "PSS",
    "ISPS": "ISPS",
    "D/O": "DO",
    "DELIVERY ORDER": "DO",
}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().replace("_", " ").split())


def _enum(value: Any) -> str:
    return "_".join(str(value or "").strip().upper().replace("-", " ").split())


def canonical_charge_code(name: Any) -> str:
    cleaned = _clean_text(name)
    if not cleaned:
        return "UNKNOWN"
    return CHARGE_ALIASES.get(cleaned, cleaned.replace(" ", "_"))


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"invalid money/quantity value: {value!r}")


def normalize_quote(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("quote must be an object")

    quote_id = str(raw.get("quote_id") or "").strip()
    if not quote_id:
        raise ValueError("quote_id is required")

    currency = _clean_text(raw.get("currency"))
    if len(currency) != 3:
        raise ValueError("quote currency must be a 3-letter code")

    route = raw.get("route") if isinstance(raw.get("route"), dict) else {}
    equipment = _clean_text(raw.get("equipment")) or "UNKNOWN"
    charges = raw.get("charges")
    if not isinstance(charges, list) or not charges:
        raise ValueError("at least one charge is required")

    normalized_charges = []
    for index, charge in enumerate(charges, start=1):
        if not isinstance(charge, dict):
            raise ValueError(f"charge {index} must be an object")

        basis = _enum(charge.get("basis")) or "UNKNOWN"
        if basis not in SUPPORTED_BASES:
            basis = "UNKNOWN"

        included = bool(charge.get("included")) or basis == "INCLUDED"
        amount = _decimal(charge.get("amount"))
        charge_currency = _clean_text(charge.get("currency")) or currency

        uncertain = bool(charge.get("uncertain"))
        if not included and amount is None:
            uncertain = True
        if charge_currency != currency:
            uncertain = True

        source_ref = str(charge.get("source_ref") or "").strip()
        if not source_ref:
            uncertain = True

        normalized_charges.append({
            "code": canonical_charge_code(charge.get("name") or charge.get("code")),
            "raw_name": str(charge.get("name") or charge.get("code") or "").strip(),
            "amount": None if amount is None else str(amount),
            "currency": charge_currency,
            "basis": "INCLUDED" if included else basis,
            "included": included,
            "uncertain": uncertain,
            "source_ref": source_ref,
            "note": str(charge.get("note") or "").strip(),
        })

    return {
        "quote_id": quote_id,
        "provider": str(raw.get("provider") or "").strip(),
        "currency": currency,
        "route": {
            "origin": _clean_text(route.get("origin")),
            "destination": _clean_text(route.get("destination")),
        },
        "equipment": equipment,
        "valid_from": raw.get("valid_from"),
        "valid_to": raw.get("valid_to"),
        "charges": normalized_charges,
        "source": deepcopy(raw.get("source") or {}),
    }


def _basis_multiplier(basis: str, context: dict[str, Any]) -> Decimal | None:
    if basis == "INCLUDED":
        return Decimal("0")
    mapping = {
        "PER_SHIPMENT": "shipments",
        "PER_CONTAINER": "containers",
        "PER_BL": "bl_count",
        "PER_KG": "weight_kg",
        "PER_CBM": "cbm",
    }
    key = mapping.get(basis)
    if not key:
        return None
    value = _decimal(context.get(key))
    if value is None or value < 0:
        return None
    return value


def price_quote(quote: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    total = Decimal("0")
    warnings: list[str] = []
    audit: list[dict[str, Any]] = []
    complete = True

    for charge in quote["charges"]:
        if charge["included"]:
            audit.append({
                "code": charge["code"],
                "contribution": "0",
                "source_ref": charge["source_ref"],
                "status": "INCLUDED",
            })
            continue

        if charge["currency"] != quote["currency"]:
            complete = False
            warnings.append(f"{charge['code']}: cross-currency charge requires explicit FX")
            continue

        if charge["uncertain"]:
            complete = False
            warnings.append(f"{charge['code']}: uncertain extraction/provenance")

        amount = _decimal(charge["amount"])
        multiplier = _basis_multiplier(charge["basis"], context)
        if amount is None or multiplier is None:
            complete = False
            warnings.append(f"{charge['code']}: cannot price basis {charge['basis']}")
            continue

        contribution = amount * multiplier
        total += contribution
        audit.append({
            "code": charge["code"],
            "amount": str(amount),
            "basis": charge["basis"],
            "multiplier": str(multiplier),
            "contribution": str(contribution),
            "source_ref": charge["source_ref"],
            "status": "UNCERTAIN" if charge["uncertain"] else "PRICED",
        })

    return {
        "quote_id": quote["quote_id"],
        "currency": quote["currency"],
        "total": str(total),
        "complete": complete,
        "warnings": sorted(set(warnings)),
        "audit": audit,
    }


def compare_quotes(raw_quotes: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_quotes, list) or len(raw_quotes) < 2:
        raise ValueError("at least two quotes are required")

    quotes = [normalize_quote(q) for q in raw_quotes]
    baseline = quotes[0]
    comparable_group = []
    excluded = []

    for quote in quotes:
        reasons = []
        if quote["route"] != baseline["route"]:
            reasons.append("ROUTE_MISMATCH")
        if quote["equipment"] != baseline["equipment"]:
            reasons.append("EQUIPMENT_MISMATCH")
        if quote["currency"] != baseline["currency"]:
            reasons.append("CURRENCY_MISMATCH")
        if reasons:
            excluded.append({"quote_id": quote["quote_id"], "reasons": reasons})
        else:
            comparable_group.append(quote)

    priced = [price_quote(q, context) for q in comparable_group]
    rankable = [p for p in priced if p["complete"]]
    rankable.sort(key=lambda x: Decimal(x["total"]))

    ranking = [
        {"rank": index, "quote_id": item["quote_id"], "total": item["total"], "currency": item["currency"]}
        for index, item in enumerate(rankable, start=1)
    ]

    return {
        "comparison_basis": {
            "route": baseline["route"],
            "equipment": baseline["equipment"],
            "currency": baseline["currency"],
            "context": deepcopy(context),
            "fx_applied": False,
        },
        "priced_quotes": priced,
        "ranking": ranking,
        "excluded": excluded,
        "decision_warning": None if len(rankable) >= 2 else "INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES",
    }
