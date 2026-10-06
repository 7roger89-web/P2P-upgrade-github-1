from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


def _currency(value: Any) -> str:
    return str(value or "").strip().upper()


def _decimal(value: Any, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} must be numeric")


def _iso_date(value: Any, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be ISO date YYYY-MM-DD")


def _rate_table(context: dict[str, Any]) -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    raw_rates = context.get("fx_rates")
    if raw_rates in (None, []):
        return {}, []
    if not isinstance(raw_rates, list):
        raise ValueError("context.fx_rates must be an array")

    comparison_date = None
    if context.get("as_of_date") not in (None, ""):
        comparison_date = _iso_date(context.get("as_of_date"), "context.as_of_date")

    table: dict[tuple[str, str], dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_rates, start=1):
        if not isinstance(raw, dict):
            errors.append({"type": "INVALID_FX_RATE", "rate_index": index})
            continue
        source = _currency(raw.get("from"))
        target = _currency(raw.get("to"))
        source_ref = str(raw.get("source_ref") or "").strip()
        as_of_raw = raw.get("as_of_date")
        try:
            rate = _decimal(raw.get("rate"), f"fx_rates[{index}].rate")
        except ValueError as exc:
            errors.append({"type": "INVALID_FX_RATE", "rate_index": index, "reason": str(exc)})
            continue
        if len(source) != 3 or len(target) != 3 or source == target or rate <= 0:
            errors.append({"type": "INVALID_FX_RATE", "rate_index": index, "from": source, "to": target})
            continue
        if not source_ref:
            errors.append({"type": "FX_SOURCE_REQUIRED", "rate_index": index, "from": source, "to": target})
            continue
        try:
            rate_date = _iso_date(as_of_raw, f"fx_rates[{index}].as_of_date")
        except ValueError as exc:
            errors.append({"type": "FX_DATE_REQUIRED", "rate_index": index, "reason": str(exc)})
            continue
        if comparison_date is not None and rate_date > comparison_date:
            errors.append({
                "type": "FX_RATE_FROM_FUTURE",
                "rate_index": index,
                "from": source,
                "to": target,
                "rate_date": rate_date.isoformat(),
                "comparison_date": comparison_date.isoformat(),
            })
            continue
        key = (source, target)
        if key in table:
            errors.append({"type": "AMBIGUOUS_FX_RATE", "from": source, "to": target})
            continue
        table[key] = {
            "from": source,
            "to": target,
            "rate": rate,
            "source_ref": source_ref,
            "as_of_date": rate_date.isoformat(),
        }
    return table, errors


def resolve_fx(raw_quote: dict[str, Any], context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(raw_quote, dict):
        raise ValueError("quote must be an object")
    quote = deepcopy(raw_quote)
    quote_id = str(quote.get("quote_id") or "<missing>")
    target_currency = _currency(quote.get("currency"))
    if len(target_currency) != 3:
        raise ValueError("quote currency must be a 3-letter code")

    charges = quote.get("charges")
    if not isinstance(charges, list) or not charges:
        raise ValueError("at least one charge is required")

    table, rate_errors = _rate_table(context)
    errors = list(rate_errors)
    conversions: list[dict[str, Any]] = []

    for index, charge in enumerate(charges, start=1):
        if not isinstance(charge, dict):
            continue

        optional = charge.get("optional") is True
        selected = charge.get("selected")
        if optional and selected is not True:
            # Optional selection semantics run later. Do not force FX for an
            # unselected or still-ambiguous add-on.
            continue

        source_currency = _currency(charge.get("currency")) or target_currency
        if source_currency == target_currency:
            continue

        if charge.get("included") is True or str(charge.get("basis") or "").strip().upper() == "INCLUDED":
            continue

        if charge.get("percentage_rate") is not None and charge.get("amount") in (None, ""):
            errors.append({
                "type": "PERCENTAGE_OUTPUT_CURRENCY_UNSUPPORTED",
                "line": index,
                "from": source_currency,
                "to": target_currency,
            })
            continue

        rate = table.get((source_currency, target_currency))
        if rate is None:
            errors.append({
                "type": "FX_RATE_REQUIRED",
                "line": index,
                "from": source_currency,
                "to": target_currency,
            })
            continue

        amount = charge.get("amount")
        minimum = charge.get("minimum_amount")
        try:
            converted_amount = None if amount in (None, "") else _decimal(amount, f"charge {index} amount") * rate["rate"]
            converted_minimum = None if minimum in (None, "") else _decimal(minimum, f"charge {index} minimum_amount") * rate["rate"]
        except ValueError as exc:
            errors.append({"type": "FX_CONVERSION_FAILED", "line": index, "reason": str(exc)})
            continue

        original = {
            "currency": source_currency,
            "amount": amount,
            "minimum_amount": minimum,
        }
        charge["currency"] = target_currency
        if converted_amount is not None:
            charge["amount"] = str(converted_amount)
        if converted_minimum is not None:
            charge["minimum_amount"] = str(converted_minimum)
        charge["fx_original"] = original
        charge["fx_rate_source_ref"] = rate["source_ref"]
        charge["fx_rate_as_of_date"] = rate["as_of_date"]

        conversions.append({
            "line": index,
            "line_id": str(charge.get("line_id") or "").strip() or None,
            "from": source_currency,
            "to": target_currency,
            "rate": str(rate["rate"]),
            "source_ref": rate["source_ref"],
            "rate_as_of_date": rate["as_of_date"],
            "original_amount": None if amount in (None, "") else str(amount),
            "converted_amount": None if converted_amount is None else str(converted_amount),
            "original_minimum_amount": None if minimum in (None, "") else str(minimum),
            "converted_minimum_amount": None if converted_minimum is None else str(converted_minimum),
        })

    return quote, {
        "quote_id": quote_id,
        "status": "BLOCKED" if errors else "READY",
        "errors": errors,
        "conversions": conversions,
        "target_currency": target_currency,
    }
