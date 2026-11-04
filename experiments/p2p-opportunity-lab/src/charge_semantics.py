from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.concierge_engine import canonical_charge_code, compare_quotes

SUPPORTED_SCOPES = {"UNSPECIFIED", "ORIGIN", "MAIN", "DESTINATION", "OTHER"}


def _enum(value: Any) -> str:
    return "_".join(str(value or "").strip().upper().replace("-", " ").split())


def canonical_scope(value: Any) -> str:
    scope = _enum(value) or "UNSPECIFIED"
    if scope not in SUPPORTED_SCOPES:
        raise ValueError(f"unsupported charge scope: {value!r}")
    return scope


def scoped_code(code: Any, scope: Any) -> str:
    canonical = canonical_charge_code(code)
    canonical_scope_value = canonical_scope(scope)
    if canonical_scope_value == "UNSPECIFIED":
        return canonical
    return f"{canonical_scope_value}::{canonical}"


def _canonical_component_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        raise ValueError("bundle_includes must be an array")
    result: list[str] = []
    for raw in values:
        code = canonical_charge_code(raw)
        if code == "UNKNOWN":
            raise ValueError("bundle_includes cannot contain an empty/unknown charge")
        if code not in result:
            result.append(code)
    if not result:
        raise ValueError("bundle_includes cannot be empty")
    return result


def prepare_quote(raw_quote: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(raw_quote, dict):
        raise ValueError("quote must be an object")

    quote = deepcopy(raw_quote)
    quote_id = str(quote.get("quote_id") or "").strip() or "<missing>"
    quote_currency = str(quote.get("currency") or "").strip().upper()
    charges = quote.get("charges")
    if not isinstance(charges, list) or not charges:
        raise ValueError("at least one charge is required")

    errors: list[dict[str, Any]] = []
    transformed: list[dict[str, Any]] = []
    bundles: list[dict[str, Any]] = []
    explicit_priced: list[dict[str, Any]] = []
    optional_excluded: list[dict[str, Any]] = []
    duplicate_index: dict[tuple[str, str, str, str], list[int]] = {}

    for index, raw_charge in enumerate(charges, start=1):
        if not isinstance(raw_charge, dict):
            errors.append({"type": "INVALID_CHARGE", "line": index})
            continue

        charge = deepcopy(raw_charge)
        try:
            scope = canonical_scope(charge.get("scope"))
        except ValueError:
            errors.append({
                "type": "INVALID_SCOPE",
                "line": index,
                "value": charge.get("scope"),
            })
            continue

        code = canonical_charge_code(charge.get("name") or charge.get("code"))
        basis = _enum(charge.get("basis")) or "UNKNOWN"
        currency = str(charge.get("currency") or quote_currency).strip().upper()
        included = bool(charge.get("included")) or basis == "INCLUDED"
        source_ref = str(charge.get("source_ref") or "").strip()

        optional = bool(charge.get("optional"))
        if optional:
            selected = charge.get("selected")
            if not isinstance(selected, bool):
                errors.append({"type": "OPTIONAL_SELECTION_REQUIRED", "line": index})
                continue
            if not selected:
                optional_excluded.append({
                    "line": index,
                    "scope": scope,
                    "code": code,
                    "source_ref": source_ref,
                })
                continue

        bundle_values = charge.get("bundle_includes")
        if bundle_values is not None:
            try:
                components = _canonical_component_list(bundle_values)
            except ValueError as exc:
                errors.append({"type": "INVALID_BUNDLE", "line": index, "reason": str(exc)})
                continue

            primary = canonical_charge_code(charge.get("bundle_primary_code") or components[0])
            if primary not in components:
                errors.append({
                    "type": "INVALID_BUNDLE_PRIMARY",
                    "line": index,
                    "primary": primary,
                    "components": components,
                })
                continue
            if included:
                errors.append({"type": "BUNDLE_CANNOT_BE_INCLUDED", "line": index})
                continue
            if not source_ref:
                errors.append({"type": "BUNDLE_MISSING_SOURCE", "line": index})
                continue

            bundles.append({
                "line": index,
                "scope": scope,
                "components": components,
                "primary": primary,
                "source_ref": source_ref,
            })

            priced = deepcopy(charge)
            priced["name"] = scoped_code(primary, scope)
            priced["scope"] = scope
            priced.pop("bundle_includes", None)
            priced.pop("bundle_primary_code", None)
            transformed.append(priced)

            for component in components:
                if component == primary:
                    continue
                transformed.append({
                    "name": scoped_code(component, scope),
                    "included": True,
                    "basis": "INCLUDED",
                    "scope": scope,
                    "source_ref": source_ref,
                    "note": f"coverage derived from bundle line {index}",
                })
            continue

        transformed_charge = deepcopy(charge)
        transformed_charge["name"] = scoped_code(code, scope)
        transformed_charge["scope"] = scope
        transformed.append(transformed_charge)

        if not included:
            explicit = {
                "line": index,
                "scope": scope,
                "code": code,
                "basis": basis,
                "currency": currency,
                "source_ref": source_ref,
            }
            explicit_priced.append(explicit)
            key = (scope, code, basis, currency)
            duplicate_index.setdefault(key, []).append(index)

    duplicates = [
        {
            "scope": key[0],
            "code": key[1],
            "basis": key[2],
            "currency": key[3],
            "lines": lines,
        }
        for key, lines in duplicate_index.items()
        if len(lines) > 1
    ]
    for duplicate in duplicates:
        errors.append({"type": "DUPLICATE_PRICED_CHARGE", **duplicate})

    overlaps: list[dict[str, Any]] = []
    for bundle in bundles:
        for explicit in explicit_priced:
            if explicit["scope"] == bundle["scope"] and explicit["code"] in bundle["components"]:
                overlap = {
                    "bundle_line": bundle["line"],
                    "component_line": explicit["line"],
                    "scope": bundle["scope"],
                    "code": explicit["code"],
                }
                overlaps.append(overlap)
                errors.append({"type": "BUNDLE_COMPONENT_DOUBLE_COUNT_RISK", **overlap})

    quote["charges"] = transformed
    audit = {
        "quote_id": quote_id,
        "status": "BLOCKED" if errors else "READY",
        "errors": errors,
        "duplicate_groups": duplicates,
        "bundle_overlaps": overlaps,
        "bundles": bundles,
        "optional_excluded": optional_excluded,
        "transformed_charge_count": len(transformed),
    }
    return quote, audit


def prepare_quote_set(raw_quotes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(raw_quotes, list) or len(raw_quotes) < 2:
        raise ValueError("at least two quotes are required")
    prepared = []
    audits = []
    for raw_quote in raw_quotes:
        quote, audit = prepare_quote(raw_quote)
        prepared.append(quote)
        audits.append(audit)
    return prepared, audits


def compare_quotes_guarded(raw_quotes: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    prepared, audits = prepare_quote_set(raw_quotes)
    blocked = [audit for audit in audits if audit["status"] == "BLOCKED"]
    if blocked:
        return {
            "comparison_basis": {
                "route": None,
                "equipment": None,
                "currency": None,
                "context": deepcopy(context),
                "selection_mode": "SEMANTIC_GUARD_BLOCKED",
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
            "semantic_audit": audits,
            "decision_warning": "UNRESOLVED_CHARGE_SEMANTICS",
        }

    result = compare_quotes(prepared, context)
    result["semantic_audit"] = audits
    result["guarded_semantics"] = True
    return result
