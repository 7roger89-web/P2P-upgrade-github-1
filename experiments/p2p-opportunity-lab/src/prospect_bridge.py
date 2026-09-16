from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

SIGNAL_TO_MARKET_SIGNAL = {
    "EXPLICIT_DEMAND": "DEMAND",
    "PAIN": "PAIN",
    "WORKAROUND": "WORKAROUND",
    "SWITCHING": "DEMAND",
    "TIMING": "TIMING",
}

DISALLOWED_ENRICHMENT_FIELDS = {
    "private_email",
    "personal_phone",
    "home_address",
    "sensitive_traits",
    "data_broker_record",
}

WEIGHTS = {
    "pain_strength": 25,
    "product_fit": 25,
    "timing": 20,
    "public_reachability": 15,
    "evidence_quality": 15,
}


@dataclass(frozen=True)
class ProspectResult:
    stage: str
    score: int
    market_evidence: dict[str, Any] | None
    outreach: dict[str, Any] | None
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "score": self.score,
            "market_evidence": self.market_evidence,
            "outreach": self.outreach,
            "reasons": list(self.reasons),
        }


def _is_public_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _score(dimensions: dict[str, Any]) -> int:
    total = 0.0
    for key, weight in WEIGHTS.items():
        value = dimensions.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{key} must be numeric")
        if value < 0 or value > 5:
            raise ValueError(f"{key} must be between 0 and 5")
        total += (float(value) / 5.0) * weight
    return round(total)


def qualify_public_prospect(record: dict[str, Any]) -> ProspectResult:
    """Qualify one upstream-style first-customer prospect for Opportunity Lab.

    The bridge deliberately does not convert a public pain/demand signal into a
    PAYMENT or WILLINGNESS_TO_PAY signal. Outreach remains a draft only.
    """
    if not isinstance(record, dict):
        raise ValueError("prospect must be an object")

    forbidden = sorted(DISALLOWED_ENRICHMENT_FIELDS.intersection(record))
    if forbidden:
        raise ValueError(f"private_or_sensitive_enrichment_forbidden: {','.join(forbidden)}")

    source_url = record.get("source_url")
    signal_type = record.get("signal_type")
    evidence_class = record.get("evidence_class")
    signal_text = record.get("signal_text")

    if not _is_public_http_url(source_url):
        return ProspectResult(
            "REJECT",
            0,
            None,
            None,
            ("meaningful_public_source_required",),
        )

    if signal_type not in SIGNAL_TO_MARKET_SIGNAL or not signal_text:
        return ProspectResult(
            "REJECT",
            0,
            None,
            None,
            ("public_pain_need_or_timing_signal_required",),
        )

    if evidence_class not in {"OBSERVED", "USER_SAID"}:
        return ProspectResult(
            "REJECT",
            0,
            None,
            None,
            ("primary_prospect_requires_direct_evidence",),
        )

    dimensions = record.get("score_dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("score_dimensions must be an object")
    score = _score(dimensions)

    if score >= 80:
        stage = "PRIMARY_STRONG"
    elif score >= 65:
        stage = "PRIMARY_VALIDATE"
    elif score >= 50:
        stage = "SECONDARY"
    else:
        stage = "REJECT"

    market_evidence = None
    if stage != "REJECT":
        market_evidence = {
            "class": evidence_class,
            "signal": SIGNAL_TO_MARKET_SIGNAL[signal_type],
            "direction": "SUPPORTS",
            "source": source_url,
            "note": str(signal_text),
            "prospect_stage": stage,
            "prospect_score": score,
        }

    outreach = None
    if stage.startswith("PRIMARY"):
        opener = record.get("outreach_opener")
        channel = record.get("public_channel")
        outreach = {
            "mode": "DRAFT_ONLY",
            "public_channel": channel if isinstance(channel, str) else None,
            "opener": opener if isinstance(opener, str) else None,
            "send_authorized": False,
        }

    return ProspectResult(
        stage,
        score,
        market_evidence,
        outreach,
        ("public_signal_qualified",) if stage != "REJECT" else ("score_below_primary_floor",),
    )
