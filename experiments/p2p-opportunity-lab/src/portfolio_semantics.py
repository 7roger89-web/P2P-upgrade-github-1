from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal
from typing import Any

from src.charge_semantics import prepare_quote
from src.concierge_engine import canonical_charge_code, canonical_equipment, normalize_quote, price_quote

OFFER_BASES = {"PER_CONTAINER", "INCLUDED"}
SHARED_BASES = {"PER_SHIPMENT", "PER_BL", "INCLUDED"}
COVERAGE_RESOLUTION_STATUSES = {"INCLUDED", "NOT_APPLICABLE"}


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().split())


def _enum(value: Any) -> str:
    return "_".join(str(value or "").strip().upper().replace("-", " ").split())


def _parse_date(value: Any, field: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be ISO date YYYY-MM-DD")


def _requirements(context: dict[str, Any]) -> dict[str, int]:
    raw = context.get("equipment_requirements")
    if not isinstance(raw, dict) or not raw:
        raise ValueError("equipment_requirements must be a non-empty object")
    result: dict[str, int] = {}
    for equipment, quantity in raw.items():
        canonical = canonical_equipment(equipment)
        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            raise ValueError(f"invalid equipment quantity for {equipment!r}")
        if qty <= 0:
            raise ValueError(f"equipment quantity must be positive for {equipment!r}")
        result[canonical] = result.get(canonical, 0) + qty
    return result


def _basis(charge: dict[str, Any]) -> str:
    return _enum(charge.get("basis")) or "UNKNOWN"


def _validate_bases(charges: list[dict[str, Any]], allowed: set[str], kind: str) -> list[str]:
    errors = []
    for index, charge in enumerate(charges, start=1):
        basis = _basis(charge)
        if basis not in allowed:
            errors.append(f"{kind} line {index}: unsupported basis {basis}")
    return errors


def _validity_errors(record: dict[str, Any], context: dict[str, Any], prefix: str) -> list[str]:
    as_of = _parse_date(context.get("as_of_date"), "context.as_of_date")
    if as_of is None:
        return []
    try:
        valid_from = _parse_date(record.get("valid_from"), f"{prefix}.valid_from")
        valid_to = _parse_date(record.get("valid_to"), f"{prefix}.valid_to")
    except ValueError:
        return ["INVALID_VALIDITY_DATE"]
    errors = []
    if valid_from is not None and as_of < valid_from:
        errors.append("NOT_YET_VALID")
    if valid_to is not None and as_of > valid_to:
        errors.append("EXPIRED")
    return errors


def _coverage_codes(prepared_quote: dict[str, Any]) -> set[str]:
    codes = set()
    for charge in prepared_quote.get("charges", []):
        code = canonical_charge_code(charge.get("name") or charge.get("code"))
        if code != "UNKNOWN":
            codes.add(code)
    return codes


def _coverage_resolution(
    context: dict[str, Any],
    quote_set_id: str,
    bucket: str,
    code: str,
) -> dict[str, str] | None:
    all_resolutions = context.get("portfolio_coverage_resolutions")
    if not isinstance(all_resolutions, dict):
        return None
    provider_resolutions = all_resolutions.get(quote_set_id)
    if not isinstance(provider_resolutions, dict):
        return None
    bucket_resolutions = provider_resolutions.get(bucket)
    if not isinstance(bucket_resolutions, dict):
        return None
    resolution = bucket_resolutions.get(code)
    if not isinstance(resolution, dict):
        return None
    status = _enum(resolution.get("status"))
    source_ref = str(resolution.get("source_ref") or "").strip()
    if status not in COVERAGE_RESOLUTION_STATUSES or not source_ref:
        return None
    return {"status": status, "source_ref": source_ref}


def _condition_guard(priced: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    unresolved = [condition for condition in normalized.get("conditions", []) if not condition["resolved"]]
    resolved = [condition for condition in normalized.get("conditions", []) if condition["resolved"]]
    if unresolved:
        priced["complete"] = False
        priced["warnings"] = sorted(set(
            priced.get("warnings", [])
            + [f"unresolved commercial term: {condition['text'] or 'missing term text'}" for condition in unresolved]
        ))
    priced["unresolved_conditions"] = unresolved
    priced["resolved_conditions"] = resolved
    return priced


def _prepare_group(
    *,
    quote_id: str,
    provider: str,
    currency: str,
    route: dict[str, Any],
    equipment: str,
    charges: list[dict[str, Any]],
    conditions: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = {
        "quote_id": quote_id,
        "provider": provider,
        "currency": currency,
        "route": route,
        "equipment": equipment,
        "charges": deepcopy(charges),
        "conditions": deepcopy(conditions),
    }
    return prepare_quote(raw)


def _price_prepared(prepared: dict[str, Any], semantic_audit: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if semantic_audit["status"] == "BLOCKED":
        return {
            "quote_id": prepared.get("quote_id"),
            "complete": False,
            "total": "0",
            "semantic_audit": semantic_audit,
            "warnings": sorted({item["type"] for item in semantic_audit["errors"]}),
        }
    if not prepared.get("charges"):
        return {
            "quote_id": prepared.get("quote_id"),
            "complete": False,
            "total": "0",
            "semantic_audit": semantic_audit,
            "warnings": ["no selected/effective charges"],
        }
    normalized = normalize_quote(prepared)
    priced = price_quote(normalized, context)
    priced["semantic_audit"] = semantic_audit
    return _condition_guard(priced, normalized)


def _zero_shared(quote_set_id: str, conditions: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved = []
    resolved = []
    for condition in conditions:
        if not isinstance(condition, dict):
            unresolved.append({"text": "invalid condition", "source_ref": "", "resolved": False})
            continue
        text = str(condition.get("text") or "").strip()
        source_ref = str(condition.get("source_ref") or "").strip()
        requested = bool(condition.get("resolved"))
        resolution_source_ref = str(condition.get("resolution_source_ref") or "").strip()
        normalized = {
            "text": text,
            "source_ref": source_ref,
            "resolved": bool(text and source_ref and requested and resolution_source_ref),
            "resolution_source_ref": resolution_source_ref,
            "resolution_note": str(condition.get("resolution_note") or "").strip(),
        }
        (resolved if normalized["resolved"] else unresolved).append(normalized)
    return {
        "quote_id": f"{quote_set_id}::SHARED",
        "currency": None,
        "total": "0",
        "complete": not unresolved,
        "warnings": [] if not unresolved else [f"unresolved commercial term: {x['text'] or 'missing term text'}" for x in unresolved],
        "audit": [],
        "semantic_audit": {
            "quote_id": f"{quote_set_id}::SHARED",
            "status": "READY",
            "errors": [],
            "duplicate_groups": [],
            "bundle_overlaps": [],
            "bundles": [],
            "optional_excluded": [],
            "transformed_charge_count": 0,
        },
        "unresolved_conditions": unresolved,
        "resolved_conditions": resolved,
    }


def compare_fcl_portfolios(provider_sets: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(provider_sets, list) or len(provider_sets) < 2:
        raise ValueError("at least two provider quote sets are required")

    requirements = _requirements(context)
    target_route = context.get("route") if isinstance(context.get("route"), dict) else {}
    target_origin = _clean(target_route.get("origin"))
    target_destination = _clean(target_route.get("destination"))
    target_currency = _clean(context.get("currency"))
    if not target_origin or not target_destination or len(target_currency) != 3:
        raise ValueError("context requires route.origin, route.destination, and 3-letter currency")

    excluded = []
    candidates = []

    # Pass 1: structural, validity and semantic preparation. No ranking yet.
    for index, provider_set in enumerate(provider_sets, start=1):
        provider = str(provider_set.get("provider") or f"provider-{index}").strip()
        quote_set_id = str(provider_set.get("quote_set_id") or provider).strip()
        currency = _clean(provider_set.get("currency"))
        route = provider_set.get("route") if isinstance(provider_set.get("route"), dict) else {}
        origin = _clean(route.get("origin"))
        destination = _clean(route.get("destination"))

        reasons = _validity_errors(provider_set, context, quote_set_id)
        if (origin, destination) != (target_origin, target_destination):
            reasons.append("ROUTE_MISMATCH")
        if currency != target_currency:
            reasons.append("CURRENCY_MISMATCH")

        offers = provider_set.get("offers")
        if not isinstance(offers, list) or not offers:
            reasons.append("MISSING_OFFERS")
            offers = []

        by_equipment: dict[str, list[dict[str, Any]]] = {}
        for offer in offers:
            if not isinstance(offer, dict):
                reasons.append("INVALID_OFFER")
                continue
            equipment = canonical_equipment(offer.get("equipment"))
            by_equipment.setdefault(equipment, []).append(offer)

        selected: dict[str, dict[str, Any]] = {}
        for equipment in requirements:
            matches = by_equipment.get(equipment, [])
            if not matches:
                reasons.append(f"MISSING_EQUIPMENT:{equipment}")
            elif len(matches) > 1:
                reasons.append(f"AMBIGUOUS_EQUIPMENT_OFFER:{equipment}")
            else:
                selected[equipment] = matches[0]

        shared_charges = provider_set.get("shared_charges") or []
        shared_conditions = provider_set.get("conditions") or []
        if not isinstance(shared_charges, list):
            shared_charges = []
            reasons.append("INVALID_SHARED_CHARGES")
        if not isinstance(shared_conditions, list):
            shared_conditions = []
            reasons.append("INVALID_CONDITIONS")
        reasons.extend(_validate_bases(shared_charges, SHARED_BASES, "shared"))

        prepared_offers: dict[str, dict[str, Any]] = {}
        offer_audits: dict[str, dict[str, Any]] = {}
        coverage_by_equipment: dict[str, set[str]] = {}

        for equipment, offer in selected.items():
            offer_id = str(offer.get("offer_id") or equipment)
            offer_validity = _validity_errors(offer, context, f"{quote_set_id}::{offer_id}")
            reasons.extend([f"{equipment}:{reason}" for reason in offer_validity])

            offer_charges = offer.get("charges") or []
            offer_conditions = offer.get("conditions") or []
            if not isinstance(offer_charges, list):
                reasons.append(f"{equipment}:INVALID_CHARGES")
                continue
            if not isinstance(offer_conditions, list):
                reasons.append(f"{equipment}:INVALID_CONDITIONS")
                continue
            reasons.extend(_validate_bases(offer_charges, OFFER_BASES, f"{equipment} offer"))

            prepared, semantic_audit = _prepare_group(
                quote_id=f"{quote_set_id}::{offer_id}",
                provider=provider,
                currency=currency,
                route=route,
                equipment=equipment,
                charges=offer_charges,
                conditions=shared_conditions + offer_conditions,
            )
            prepared_offers[equipment] = prepared
            offer_audits[equipment] = semantic_audit
            coverage_by_equipment[equipment] = _coverage_codes(prepared)
            if semantic_audit["status"] == "BLOCKED":
                for error in semantic_audit["errors"]:
                    reasons.append(f"{equipment}:SEMANTIC:{error['type']}")
            if not prepared.get("charges"):
                reasons.append(f"{equipment}:NO_SELECTED_CHARGES")

        prepared_shared = None
        shared_audit = None
        shared_codes: set[str] = set()
        if shared_charges:
            prepared_shared, shared_audit = _prepare_group(
                quote_id=f"{quote_set_id}::SHARED",
                provider=provider,
                currency=currency,
                route=route,
                equipment="PORTFOLIO",
                charges=shared_charges,
                conditions=shared_conditions,
            )
            shared_codes = _coverage_codes(prepared_shared)
            if shared_audit["status"] == "BLOCKED":
                for error in shared_audit["errors"]:
                    reasons.append(f"SHARED:SEMANTIC:{error['type']}")

        if reasons:
            excluded.append({"quote_set_id": quote_set_id, "provider": provider, "reasons": sorted(set(reasons))})
            continue

        candidates.append({
            "quote_set_id": quote_set_id,
            "provider": provider,
            "currency": currency,
            "route": route,
            "shared_conditions": shared_conditions,
            "prepared_offers": prepared_offers,
            "offer_audits": offer_audits,
            "coverage_by_equipment": coverage_by_equipment,
            "prepared_shared": prepared_shared,
            "shared_audit": shared_audit,
            "shared_codes": shared_codes,
        })

    # Pass 2: establish apples-to-apples coverage across structurally valid providers.
    required_coverage: dict[str, set[str]] = {equipment: set() for equipment in requirements}
    required_coverage["SHARED"] = set()
    for candidate in candidates:
        for equipment in requirements:
            required_coverage[equipment].update(candidate["coverage_by_equipment"].get(equipment, set()))
        required_coverage["SHARED"].update(candidate["shared_codes"])

    coverage_matrix = []
    coverage_valid_candidates = []
    for candidate in candidates:
        quote_set_id = candidate["quote_set_id"]
        provider_gaps = []
        bucket_rows = []
        for bucket in list(requirements) + ["SHARED"]:
            present = candidate["shared_codes"] if bucket == "SHARED" else candidate["coverage_by_equipment"].get(bucket, set())
            missing = sorted(required_coverage[bucket] - present)
            unresolved = []
            resolved = []
            for code in missing:
                resolution = _coverage_resolution(context, quote_set_id, bucket, code)
                if resolution is None:
                    unresolved.append(code)
                    provider_gaps.append(f"COVERAGE_GAP:{bucket}:{code}")
                else:
                    resolved.append({"code": code, **resolution})
            bucket_rows.append({
                "bucket": bucket,
                "present_codes": sorted(present),
                "required_codes": sorted(required_coverage[bucket]),
                "missing_codes": missing,
                "unresolved_missing_codes": unresolved,
                "resolved_missing_codes": resolved,
            })

        coverage_matrix.append({
            "quote_set_id": quote_set_id,
            "provider": candidate["provider"],
            "buckets": bucket_rows,
        })
        if provider_gaps:
            excluded.append({
                "quote_set_id": quote_set_id,
                "provider": candidate["provider"],
                "reasons": sorted(set(provider_gaps)),
            })
        else:
            coverage_valid_candidates.append(candidate)

    # Pass 3: only complete, coverage-aligned providers may be priced/ranked.
    results = []
    for candidate in coverage_valid_candidates:
        quote_set_id = candidate["quote_set_id"]
        provider = candidate["provider"]
        reasons = []
        offer_breakdown = []
        portfolio_total = Decimal("0")

        for equipment, quantity in requirements.items():
            priced = _price_prepared(
                candidate["prepared_offers"][equipment],
                candidate["offer_audits"][equipment],
                {"containers": quantity, "shipments": 1, "bl_count": 1},
            )
            if not priced["complete"]:
                reasons.append(f"{equipment}:INCOMPLETE_OFFER")
            else:
                portfolio_total += Decimal(priced["total"])
            offer_breakdown.append({
                "equipment": equipment,
                "quantity": quantity,
                "priced": priced,
            })

        if candidate["prepared_shared"] is None:
            shared_priced = _zero_shared(quote_set_id, candidate["shared_conditions"])
        else:
            shared_priced = _price_prepared(
                candidate["prepared_shared"],
                candidate["shared_audit"],
                {
                    "containers": sum(requirements.values()),
                    "shipments": int(context.get("shipments", 1)),
                    "bl_count": int(context.get("bl_count", 1)),
                },
            )
        if not shared_priced["complete"]:
            reasons.append("INCOMPLETE_SHARED_CHARGES")
        else:
            portfolio_total += Decimal(shared_priced["total"])

        if reasons:
            excluded.append({
                "quote_set_id": quote_set_id,
                "provider": provider,
                "reasons": sorted(set(reasons)),
                "offer_breakdown": offer_breakdown,
                "shared_priced": shared_priced,
            })
            continue

        results.append({
            "quote_set_id": quote_set_id,
            "provider": provider,
            "currency": candidate["currency"],
            "total": str(portfolio_total),
            "offer_breakdown": offer_breakdown,
            "shared_priced": shared_priced,
        })

    results.sort(key=lambda item: Decimal(item["total"]))
    ranking = [
        {
            "rank": rank,
            "quote_set_id": item["quote_set_id"],
            "provider": item["provider"],
            "total": item["total"],
            "currency": item["currency"],
        }
        for rank, item in enumerate(results, start=1)
    ]

    return {
        "requirements": requirements,
        "route": {"origin": target_origin, "destination": target_destination},
        "currency": target_currency,
        "required_coverage": {bucket: sorted(codes) for bucket, codes in required_coverage.items()},
        "coverage_matrix": coverage_matrix,
        "portfolios": results,
        "ranking": ranking,
        "excluded": excluded,
        "decision_warning": None if len(ranking) >= 2 else "INSUFFICIENT_COMPLETE_PROVIDER_PORTFOLIOS",
    }
