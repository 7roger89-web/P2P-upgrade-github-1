from __future__ import annotations

from copy import deepcopy
from datetime import date
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
        minimum_amount = _decimal(charge.get("minimum_amount"))
        if minimum_amount is not None and minimum_amount < 0:
            raise ValueError(f"charge {index} minimum_amount cannot be negative")
        if included and minimum_amount is not None:
            raise ValueError(f"charge {index} cannot be INCLUDED and have minimum_amount")
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
            "minimum_amount": None if minimum_amount is None else str(minimum_amount),
            "currency": charge_currency,
            "basis": "INCLUDED" if included else basis,
            "included": included,
            "uncertain": uncertain,
            "source_ref": source_ref,
            "note": str(charge.get("note") or "").strip(),
        })

    raw_conditions = raw.get("conditions") or []
    if not isinstance(raw_conditions, list):
        raise ValueError("conditions must be an array")

    normalized_conditions = []
    for index, condition in enumerate(raw_conditions, start=1):
        if not isinstance(condition, dict):
            raise ValueError(f"condition {index} must be an object")
        text = str(condition.get("text") or "").strip()
        source_ref = str(condition.get("source_ref") or "").strip()
        requested_resolved = bool(condition.get("resolved"))
        resolution_source_ref = str(condition.get("resolution_source_ref") or "").strip()
        effective_resolved = bool(text and source_ref and requested_resolved and resolution_source_ref)
        normalized_conditions.append({
            "text": text,
            "source_ref": source_ref,
            "resolved": effective_resolved,
            "resolution_source_ref": resolution_source_ref,
            "resolution_note": str(condition.get("resolution_note") or "").strip(),
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
        "conditions": normalized_conditions,
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
        minimum_amount = _decimal(charge.get("minimum_amount"))
        multiplier = _basis_multiplier(charge["basis"], context)
        if amount is None or multiplier is None:
            complete = False
            warnings.append(f"{charge['code']}: cannot price basis {charge['basis']}")
            continue

        raw_contribution = amount * multiplier
        contribution = raw_contribution
        minimum_applied = False
        if minimum_amount is not None and raw_contribution < minimum_amount:
            contribution = minimum_amount
            minimum_applied = True
        total += contribution
        audit.append({
            "code": charge["code"],
            "amount": str(amount),
            "basis": charge["basis"],
            "multiplier": str(multiplier),
            "raw_contribution": str(raw_contribution),
            "minimum_amount": None if minimum_amount is None else str(minimum_amount),
            "minimum_applied": minimum_applied,
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


def _parse_iso_date(value: Any, field_name: str) -> date | None:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be ISO date YYYY-MM-DD")


def _validity_reasons(quote: dict[str, Any], context: dict[str, Any]) -> list[str]:
    as_of_raw = context.get("as_of_date")
    if as_of_raw in (None, ""):
        return []
    as_of = _parse_iso_date(as_of_raw, "context.as_of_date")
    reasons = []
    try:
        valid_from = _parse_iso_date(quote.get("valid_from"), f"{quote['quote_id']}.valid_from")
        valid_to = _parse_iso_date(quote.get("valid_to"), f"{quote['quote_id']}.valid_to")
    except ValueError:
        return ["INVALID_VALIDITY_DATE"]

    if valid_from is not None and as_of < valid_from:
        reasons.append("NOT_YET_VALID")
    if valid_to is not None and as_of > valid_to:
        reasons.append("EXPIRED")
    return reasons


COVERAGE_RESOLUTION_STATUSES = {"INCLUDED", "NOT_APPLICABLE"}


def _charge_code_set(quote: dict[str, Any]) -> set[str]:
    return {charge["code"] for charge in quote["charges"] if charge["code"] != "UNKNOWN"}


def _coverage_resolution(
    quote_id: str,
    code: str,
    context: dict[str, Any],
) -> dict[str, Any] | None:
    all_resolutions = context.get("coverage_resolutions")
    if not isinstance(all_resolutions, dict):
        return None
    quote_resolutions = all_resolutions.get(quote_id)
    if not isinstance(quote_resolutions, dict):
        return None
    resolution = quote_resolutions.get(code)
    if not isinstance(resolution, dict):
        return None

    status = _enum(resolution.get("status"))
    source_ref = str(resolution.get("source_ref") or "").strip()
    if status not in COVERAGE_RESOLUTION_STATUSES or not source_ref:
        return None
    return {"status": status, "source_ref": source_ref}


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
        reasons.extend(_validity_reasons(quote, context))
        if reasons:
            excluded.append({"quote_id": quote["quote_id"], "reasons": reasons})
        else:
            comparable_group.append(quote)

    required_codes: set[str] = set()
    for quote in comparable_group:
        required_codes.update(_charge_code_set(quote))

    priced = []
    coverage_matrix = []
    for quote in comparable_group:
        priced_quote = price_quote(quote, context)
        unresolved_conditions = [
            condition for condition in quote.get("conditions", [])
            if not condition["resolved"]
        ]
        resolved_conditions = [
            condition for condition in quote.get("conditions", [])
            if condition["resolved"]
        ]
        if unresolved_conditions:
            priced_quote["complete"] = False
            priced_quote["warnings"] = sorted(set(
                priced_quote["warnings"]
                + [
                    f"unresolved commercial term: {condition['text'] or 'missing term text'}"
                    for condition in unresolved_conditions
                ]
            ))
        priced_quote["unresolved_conditions"] = unresolved_conditions
        priced_quote["resolved_conditions"] = resolved_conditions

        present_codes = _charge_code_set(quote)
        missing_codes = sorted(required_codes - present_codes)
        unresolved = []
        resolved = []

        for code in missing_codes:
            resolution = _coverage_resolution(quote["quote_id"], code, context)
            if resolution is None:
                unresolved.append(code)
            else:
                resolved.append({"code": code, **resolution})

        if unresolved:
            priced_quote["complete"] = False
            priced_quote["warnings"] = sorted(set(
                priced_quote["warnings"]
                + [f"coverage gap: unresolved missing charge {code}" for code in unresolved]
            ))

        priced_quote["coverage_gaps"] = unresolved
        priced_quote["coverage_resolutions"] = resolved
        priced.append(priced_quote)
        coverage_matrix.append({
            "quote_id": quote["quote_id"],
            "present_codes": sorted(present_codes),
            "missing_codes": missing_codes,
            "unresolved_missing_codes": unresolved,
            "resolved_missing_codes": [item["code"] for item in resolved],
        })

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
            "as_of_date": context.get("as_of_date"),
            "fx_applied": False,
        },
        "required_charge_codes": sorted(required_codes),
        "coverage_matrix": coverage_matrix,
        "priced_quotes": priced,
        "ranking": ranking,
        "excluded": excluded,
        "decision_warning": None if len(rankable) >= 2 else "INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES",
    }
