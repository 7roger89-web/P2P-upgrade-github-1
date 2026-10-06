from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any

SUPPORTED_BASES = {"PER_SHIPMENT", "PER_CONTAINER", "PER_BL", "PER_KG", "PER_CBM", "INCLUDED"}


def _decimal(value: Any, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} must be numeric")


def _basis(value: Any) -> str:
    return "_".join(str(value or "").strip().upper().replace("-", " ").split())


def _multiplier(basis: str, context: dict[str, Any]) -> Decimal:
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
    if key is None:
        raise ValueError(f"unsupported percentage base basis {basis}")
    value = _decimal(context.get(key), f"context.{key}")
    if value < 0:
        raise ValueError(f"context.{key} cannot be negative")
    return value


def _line_contribution(charge: dict[str, Any], quote_currency: str, context: dict[str, Any]) -> Decimal:
    if charge.get("percentage_rate") is not None:
        raise ValueError("percentage charge cannot be used as another percentage base")
    if charge.get("bundle_includes") is not None:
        raise ValueError("bundled charge cannot be used as percentage base before bundle resolution")
    if charge.get("optional") is True and charge.get("selected") is not True:
        raise ValueError("unselected/ambiguous optional charge cannot be used as percentage base")

    basis = _basis(charge.get("basis"))
    if basis not in SUPPORTED_BASES:
        raise ValueError(f"unsupported percentage base basis {basis}")
    if charge.get("included") or basis == "INCLUDED":
        return Decimal("0")

    currency = str(charge.get("currency") or quote_currency).strip().upper()
    if currency != quote_currency:
        raise ValueError("percentage base requires same-currency lines; explicit FX is not supported")

    amount = _decimal(charge.get("amount"), "base charge amount")
    contribution = amount * _multiplier(basis, context)
    minimum = charge.get("minimum_amount")
    if minimum not in (None, ""):
        floor = _decimal(minimum, "base charge minimum_amount")
        if floor < 0:
            raise ValueError("base charge minimum_amount cannot be negative")
        if contribution < floor:
            contribution = floor
    if not str(charge.get("source_ref") or "").strip():
        raise ValueError("percentage base line requires source_ref")
    return contribution


def resolve_percentage_charges(raw_quote: dict[str, Any], context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(raw_quote, dict):
        raise ValueError("quote must be an object")
    quote = deepcopy(raw_quote)
    charges = quote.get("charges")
    if not isinstance(charges, list) or not charges:
        raise ValueError("at least one charge is required")

    quote_id = str(quote.get("quote_id") or "<missing>")
    quote_currency = str(quote.get("currency") or "").strip().upper()
    errors: list[dict[str, Any]] = []
    resolutions: list[dict[str, Any]] = []
    deferred_optional: list[dict[str, Any]] = []

    line_index: dict[str, dict[str, Any]] = {}
    for charge in charges:
        if not isinstance(charge, dict):
            continue
        line_id = str(charge.get("line_id") or "").strip()
        if line_id:
            if line_id in line_index:
                errors.append({"type": "DUPLICATE_LINE_ID", "line_id": line_id})
            else:
                line_index[line_id] = charge

    shipments = _decimal(context.get("shipments", 1), "context.shipments")
    if shipments <= 0:
        raise ValueError("context.shipments must be positive for percentage resolution")

    transformed = []
    for index, charge in enumerate(charges, start=1):
        if not isinstance(charge, dict):
            transformed.append(charge)
            continue

        rate_value = charge.get("percentage_rate")
        if rate_value is None:
            transformed.append(deepcopy(charge))
            continue

        if charge.get("optional") is True and charge.get("selected") is not True:
            transformed.append(deepcopy(charge))
            deferred_optional.append({
                "line": index,
                "line_id": str(charge.get("line_id") or "").strip() or None,
                "selected": charge.get("selected"),
                "reason": "optional selection is handled by the downstream charge-semantics guard",
            })
            continue

        line_id = str(charge.get("line_id") or "").strip()
        source_ref = str(charge.get("source_ref") or "").strip()
        refs = charge.get("percentage_of_line_ids")
        if not line_id:
            errors.append({"type": "PERCENTAGE_LINE_ID_REQUIRED", "line": index})
            transformed.append(deepcopy(charge))
            continue
        if not source_ref:
            errors.append({"type": "PERCENTAGE_SOURCE_REQUIRED", "line": index, "line_id": line_id})
            transformed.append(deepcopy(charge))
            continue
        if charge.get("amount") not in (None, ""):
            errors.append({"type": "PERCENTAGE_AMOUNT_CONFLICT", "line": index, "line_id": line_id})
            transformed.append(deepcopy(charge))
            continue
        if not isinstance(refs, list) or not refs:
            errors.append({"type": "PERCENTAGE_BASE_REQUIRED", "line": index, "line_id": line_id})
            transformed.append(deepcopy(charge))
            continue

        try:
            rate = _decimal(rate_value, "percentage_rate")
            if rate < 0:
                raise ValueError("percentage_rate cannot be negative")
            base_total = Decimal("0")
            normalized_refs = []
            for raw_ref in refs:
                ref = str(raw_ref or "").strip()
                if not ref or ref not in line_index:
                    raise ValueError(f"unknown percentage base line_id {ref!r}")
                if ref == line_id:
                    raise ValueError("percentage charge cannot reference itself")
                base_total += _line_contribution(line_index[ref], quote_currency, context)
                normalized_refs.append(ref)
            resolved_total = base_total * rate / Decimal("100")
        except ValueError as exc:
            errors.append({
                "type": "PERCENTAGE_RESOLUTION_FAILED",
                "line": index,
                "line_id": line_id,
                "reason": str(exc),
            })
            transformed.append(deepcopy(charge))
            continue

        resolved = deepcopy(charge)
        resolved["amount"] = str(resolved_total / shipments)
        resolved["basis"] = "PER_SHIPMENT"
        resolved["note"] = (
            (str(resolved.get("note") or "").strip() + " ").strip()
            + f"resolved {rate}% of lines {','.join(normalized_refs)}; total={resolved_total}"
        ).strip()
        resolved.pop("percentage_rate", None)
        resolved.pop("percentage_of_line_ids", None)
        transformed.append(resolved)
        resolutions.append({
            "line_id": line_id,
            "rate_percent": str(rate),
            "base_line_ids": normalized_refs,
            "base_total": str(base_total),
            "resolved_total": str(resolved_total),
            "source_ref": source_ref,
        })

    quote["charges"] = transformed
    return quote, {
        "quote_id": quote_id,
        "status": "BLOCKED" if errors else "READY",
        "errors": errors,
        "resolutions": resolutions,
        "deferred_optional": deferred_optional,
    }
