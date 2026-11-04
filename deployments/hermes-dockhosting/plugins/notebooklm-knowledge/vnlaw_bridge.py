"""Read-only VNLAW cross-check for NotebookLM operational research.

This module calls the already-deployed VNLAW verified-only HTTP boundary.
It never uses discovery scope and never synthesizes legal conclusions.
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

VNLAW_API_URL_ENV = "VNLAW_API_URL"
VNLAW_API_TOKEN_ENV = "VNLAW_API_TOKEN"
DEFAULT_VNLAW_API_URL = "https://vnlaw-production.up.railway.app"
DEFAULT_TOP_K = 5
MAX_TOP_K = 10
MAX_TEXT_CHARS = 900
MAX_GUIDANCE_EXCERPT_CHARS = 700


class VNLAWConfigError(RuntimeError):
    pass


class VNLAWServiceError(RuntimeError):
    pass


def _today_vietnam() -> str:
    tz = _dt.timezone(_dt.timedelta(hours=7))
    return _dt.datetime.now(tz).date().isoformat()


def _validate_date(value: str | None) -> str:
    if value is None or not str(value).strip():
        return _today_vietnam()
    text = str(value).strip()
    try:
        parsed = _dt.date.fromisoformat(text)
    except ValueError as exc:
        raise VNLAWConfigError("as_of_date must be YYYY-MM-DD") from exc
    if parsed.isoformat() != text:
        raise VNLAWConfigError("as_of_date must be YYYY-MM-DD")
    return text


def _service_config() -> tuple[str, str]:
    base = os.environ.get(VNLAW_API_URL_ENV, DEFAULT_VNLAW_API_URL).strip().rstrip("/")
    token = os.environ.get(VNLAW_API_TOKEN_ENV, "").strip()
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme != "https" or not parsed.netloc:
        raise VNLAWConfigError("VNLAW_API_URL must be an absolute HTTPS URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise VNLAWConfigError("VNLAW_API_URL must not contain credentials/query/fragment")
    if not token:
        raise VNLAWConfigError("VNLAW_API_TOKEN is not configured")
    return base, token


def _clip(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _project_verified_hit(hit: Any) -> dict[str, Any]:
    if not isinstance(hit, dict):
        raise VNLAWServiceError("VNLAW returned an invalid authority hit")
    chunk = hit.get("chunk")
    if not isinstance(chunk, dict):
        raise VNLAWServiceError("VNLAW authority hit is missing chunk")
    return {
        "authority_tier": hit.get("authority_tier"),
        "rank": hit.get("rank"),
        "document_number": chunk.get("document_number"),
        "provision_id": chunk.get("provision_id"),
        "version_id": chunk.get("version_id"),
        "breadcrumb": chunk.get("breadcrumb"),
        "text": _clip(chunk.get("text"), MAX_TEXT_CHARS),
        "force": chunk.get("force"),
        "valid_from": chunk.get("valid_from"),
        "valid_to": chunk.get("valid_to"),
        "source_url": chunk.get("source_url"),
        "source_locator": chunk.get("source_locator"),
        "dossier_anchor": hit.get("dossier_anchor"),
        "matched_terms": list(hit.get("matched_terms") or []),
    }


def _project_guidance_hit(hit: Any) -> dict[str, Any]:
    if not isinstance(hit, dict):
        raise VNLAWServiceError("VNLAW returned an invalid guidance hit")
    return {
        "authority_tier": hit.get("authority_tier"),
        "document_number": hit.get("document_number"),
        "document_kind": hit.get("document_kind"),
        "title": hit.get("title"),
        "issuer": hit.get("issuer"),
        "issued_on": hit.get("issued_on"),
        "official_url": hit.get("official_url"),
        "evidence_locator": hit.get("evidence_locator"),
        "evidence_excerpt": _clip(
            hit.get("evidence_excerpt"), MAX_GUIDANCE_EXCERPT_CHARS
        ),
        "matched_terms": list(hit.get("matched_terms") or []),
    }


def _post_verified_query_sync(
    query: str,
    as_of_date: str,
    top_k: int,
) -> dict[str, Any]:
    base, token = _service_config()
    body = json.dumps(
        {
            "query": query,
            "as_of_date": as_of_date,
            "top_k": top_k,
            "scope": "verified",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        base + "/verified-query",
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(2_000_000)
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise VNLAWServiceError("VNLAW authentication failed") from None
        raise VNLAWServiceError(f"VNLAW HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise VNLAWServiceError(f"VNLAW transport failed: {type(exc).__name__}") from None

    if status != 200:
        raise VNLAWServiceError(f"VNLAW HTTP {status}")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise VNLAWServiceError("VNLAW returned invalid JSON") from None
    if not isinstance(payload, dict):
        raise VNLAWServiceError("VNLAW returned an invalid response")

    groups = ("legal_hits", "technical_hits", "guidance_hits", "dossier_anchors")
    if any(not isinstance(payload.get(name), list) for name in groups):
        raise VNLAWServiceError("VNLAW response is missing verified authority groups")

    legal = [_project_verified_hit(x) for x in payload["legal_hits"][:top_k]]
    technical = [_project_verified_hit(x) for x in payload["technical_hits"][:top_k]]
    guidance = [_project_guidance_hit(x) for x in payload["guidance_hits"][:top_k]]
    anchors = [str(x) for x in payload["dossier_anchors"] if str(x).strip()]

    found = bool(legal or technical or guidance)
    return {
        "status": "VERIFIED_EVIDENCE_FOUND" if found else "NO_VERIFIED_EVIDENCE",
        "query": str(payload.get("query") or query),
        "as_of_date": str(payload.get("as_of_date") or as_of_date),
        "legal_hits": legal,
        "technical_hits": technical,
        "guidance_hits": guidance,
        "dossier_anchors": anchors,
        "verified_authority_evidence": found,
        "synthesis": False,
        "scope_notice": (
            "VNLAW only reports material inside its bounded verified corpus. "
            "No hit means 'not verified here', not 'legally false' or 'not regulated'."
        ),
    }


async def cross_check(
    question: str,
    *,
    as_of_date: str | None = None,
    source_titles: list[str] | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    """Cross-check one NotebookLM question against verified-only VNLAW.

    Missing configuration is returned as a bounded status so NotebookLM research
    still works while production secrets are being wired.
    """
    question = " ".join(str(question or "").split())
    if not question:
        return {
            "status": "SKIPPED_EMPTY_QUERY",
            "verified_authority_evidence": False,
            "synthesis": False,
        }

    try:
        date_value = _validate_date(as_of_date)
        bounded_top_k = max(1, min(int(top_k), MAX_TOP_K))
        _service_config()
    except (VNLAWConfigError, ValueError, TypeError) as exc:
        return {
            "status": "CONFIG_MISSING",
            "error": str(exc),
            "verified_authority_evidence": False,
            "synthesis": False,
        }

    unique_titles: list[str] = []
    for title in source_titles or []:
        value = " ".join(str(title or "").split())
        if value and value not in unique_titles:
            unique_titles.append(value)
        if len(unique_titles) >= 6:
            break

    retrieval_query = question
    if unique_titles:
        retrieval_query += " | Tài liệu NotebookLM: " + "; ".join(unique_titles)

    try:
        return await asyncio.to_thread(
            _post_verified_query_sync,
            retrieval_query,
            date_value,
            bounded_top_k,
        )
    except VNLAWServiceError as exc:
        return {
            "status": "SERVICE_ERROR",
            "error": str(exc),
            "verified_authority_evidence": False,
            "synthesis": False,
        }
