#!/usr/bin/env python3
"""Build the normalized multi-site capture manifest for Issue #241 evidence.

This script is EVIDENCE-LAYER tooling, not part of the generic runtime. It:

1. replays the stored executor capture texts (Arena ``fetch_page`` results,
   2026-09-23) through the generic runtime contract in
   ``.p2p/system/p2p_capabilities/web_capture_runtime.py``;
2. demonstrates the source-specific boundary: the only site-specific parsing
   (VBPL concatenated-sitemap splitting, Công Báo fragment cleanup) lives
   HERE, never in the runtime;
3. emits deterministic bounded plans, discovery records, checkpoint/resume
   metadata and honest site-proof classifications into ``manifest.json``.

Run offline from a repository checkout:

    python3 evidence/p2p-web-capture-runtime-01/build_manifest.py

The output is byte-deterministic: rebuilding prints the same sha256.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EVIDENCE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVIDENCE_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / ".p2p" / "system"))

from p2p_capabilities import web_capture_runtime as runtime  # noqa: E402

CAPTURES_DIR = EVIDENCE_DIR / "captures"
EXECUTOR = "ARENA_FETCH_PAGE"
RETRIEVED_AT = "2026-09-23"  # date precision; exact clocks not retained
TRANSPORT_BLOCKED_REASON = (
    "EXECUTOR_TRANSPORT_BLOCKED:ARENA_FETCH_PAGE_PROXY_SIGNATURE_FAILURES_ON_QUERY_URLS"
    "_THEN_SESSION_WIDE_DEGRADATION_2026-09-23"
)

# ---------------------------------------------------------------------------
# Explicit public target scopes (one per site; attachment host is separate).
# ---------------------------------------------------------------------------

VIMDA_URL = "https://vimda.moh.gov.vn/web/guest/van-ban-cong-bo"
VBPL_DOC_URL = (
    "https://vbpl.vn/van-ban/chi-tiet/luat-phat-trien-do-thi-so-18-2026-qh16"
    "--deec8480-b58b-11f1-bea2-5d13f4b83b24"
)
CONGBAO_HOME_URL = "https://congbao.chinhphu.vn/"
CONGBAO_C1_URL = "https://congbao.chinhphu.vn/van-ban-dang-cong-bao/chinh-phu-c1.htm"
CONGBAO_RECORD_URL = (
    "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-347-2026-nd-cp-470418.htm"
)

SCOPE_VIMDA = runtime.CaptureScope(
    scope_id="VIMDA-VAN-BAN-CONG-BO",
    allowed_host="vimda.moh.gov.vn",
    allowed_path_prefixes=("/web/guest/van-ban-cong-bo",),
    task_authority="ISSUE-241-BOUNDED-MULTI-SITE-PROOF",
)
SCOPE_VBPL = runtime.CaptureScope(
    scope_id="VBPL-PUBLIC-PORTAL",
    allowed_host="vbpl.vn",
    allowed_path_prefixes=("/",),
    task_authority="ISSUE-241-BOUNDED-MULTI-SITE-PROOF",
)
SCOPE_CONGBAO = runtime.CaptureScope(
    scope_id="CONGBAO-CHINHPHU",
    allowed_host="congbao.chinhphu.vn",
    allowed_path_prefixes=("/",),
    task_authority="ISSUE-241-BOUNDED-MULTI-SITE-PROOF",
)
SCOPE_CONGBAO_CDN = runtime.CaptureScope(
    scope_id="CONGBAO-CDN-ATTACHMENTS",
    allowed_host="g7.cdnchinhphu.vn",
    allowed_path_prefixes=("/api/download/",),
    task_authority="ISSUE-241-BOUNDED-MULTI-SITE-PROOF",
)

# ---------------------------------------------------------------------------
# Stored capture registry (dependency-ordered for provenance links).
# ---------------------------------------------------------------------------

CAPTURE_ENTRIES = (
    {
        "key": "vbpl_robots",
        "file": "vbpl-robots.txt",
        "url": "https://vbpl.vn/robots.txt",
        "scope": SCOPE_VBPL,
        "completeness": "FULL",
        "chunk": {"index": 0, "total": 1},
        "discovered_from": None,
        "notes": (),
    },
    {
        "key": "vbpl_sitemap_index",
        "file": "vbpl-sitemap-index.txt",
        "url": "https://vbpl.vn/sitemap.xml",
        "scope": SCOPE_VBPL,
        "completeness": "FULL",
        "chunk": {"index": 0, "total": 1},
        "discovered_from": "vbpl_robots",  # Sitemap: line in robots.txt
        "notes": (),
    },
    {
        "key": "vbpl_sitemap_0",
        "file": "vbpl-sitemap-0.txt",
        "url": "https://vbpl.vn/sitemap/0.xml",
        "scope": SCOPE_VBPL,
        "completeness": "FULL",
        "chunk": {"index": 0, "total": 1},
        "discovered_from": "vbpl_sitemap_index",
        "notes": (),
    },
    {
        "key": "vbpl_sitemap_1_c0",
        "file": "vbpl-sitemap-1.chunk0-of-133.excerpt.txt",
        "url": "https://vbpl.vn/sitemap/1.xml",
        "scope": SCOPE_VBPL,
        "completeness": "EXCERPT_OF_CHUNK_0_OF_133",
        "chunk": {"index": 0, "total": 133},
        "discovered_from": "vbpl_sitemap_index",
        "notes": ("EXCERPT_FIRST_4_SITEMAP_ENTRIES",),
    },
    {
        "key": "vbpl_doc_detail",
        "file": "vbpl-doc-detail-luat-18-2026-qh16.chunk0-of-2.excerpt.md",
        "url": VBPL_DOC_URL,
        "scope": SCOPE_VBPL,
        "completeness": "EXCERPT_OF_CHUNK_0_OF_2",
        "chunk": {"index": 0, "total": 2},
        "discovered_from": "vbpl_sitemap_1_c0",
        "notes": ("DOCUMENT_BODY_JS_GATED_TEXT_TRANSPORT_LOADER_SHELL_ONLY",),
        "extra_meta": {
            "executor_reported_title": "Luật 18/2026/QH16 của Quốc hội | CSDL quốc gia về pháp luật",
        },
    },
    {
        "key": "vimda_listing_c1",
        "file": "vimda-listing.chunk1-of-7.excerpt.md",
        "url": VIMDA_URL,
        "scope": SCOPE_VIMDA,
        "completeness": "EXCERPT_OF_CHUNK_1_OF_7",
        "chunk": {"index": 1, "total": 7},
        "discovered_from": None,
        "notes": ("SEED_EXPLICIT_TARGET",),
        "extra_meta": {"chunk_group": "vimda-listing-p1-2026-09-23"},
    },
    {
        "key": "vimda_listing_c6",
        "file": "vimda-listing.chunk6-of-7.excerpt.md",
        "url": VIMDA_URL,
        "scope": SCOPE_VIMDA,
        "completeness": "EXCERPT_OF_CHUNK_6_OF_7",
        "chunk": {"index": 6, "total": 7},
        "discovered_from": None,
        "notes": ("SEED_EXPLICIT_TARGET_SAME_FETCH_AS_vimda_listing_c1",),
        "extra_meta": {"chunk_group": "vimda-listing-p1-2026-09-23"},
    },
    {
        "key": "congbao_home_c3",
        "file": "congbao-home.chunk3-of-5.excerpt.md",
        "url": CONGBAO_HOME_URL,
        "scope": SCOPE_CONGBAO,
        "completeness": "EXCERPT_OF_CHUNK_3_OF_5",
        "chunk": {"index": 3, "total": 5},
        "discovered_from": None,
        "notes": ("SEED_EXPLICIT_TARGET",),
        "extra_meta": {"executor_reported_title": "Công báo điện tử Nước CHXHCN Việt Nam"},
    },
    {
        "key": "congbao_c1_listing_c4",
        "file": "congbao-chinhphu-c1.chunk4-of-10.excerpt.md",
        "url": CONGBAO_C1_URL,
        "scope": SCOPE_CONGBAO,
        "completeness": "EXCERPT_OF_CHUNK_4_OF_10",
        "chunk": {"index": 4, "total": 10},
        "discovered_from": "congbao_home_c3",
        "notes": (),
        "extra_meta": {"executor_reported_title": "Văn bản ban hành bởi Chính phủ"},
    },
    {
        "key": "congbao_record_347_c0",
        "file": "congbao-record-nghi-dinh-so-347-2026-nd-cp.chunk0-of-5.excerpt.md",
        "url": CONGBAO_RECORD_URL,
        "scope": SCOPE_CONGBAO,
        "completeness": "EXCERPT_OF_CHUNK_0_OF_5",
        "chunk": {"index": 0, "total": 5},
        "discovered_from": "congbao_c1_listing_c4",
        "notes": (),
    },
)


def build_records() -> tuple[dict[str, runtime.CaptureRecord], dict[str, str]]:
    records: dict[str, runtime.CaptureRecord] = {}
    texts: dict[str, str] = {}
    for entry in CAPTURE_ENTRIES:
        text = (CAPTURES_DIR / entry["file"]).read_text(encoding="utf-8")
        texts[entry["key"]] = text
        discovered_from = None
        if entry["discovered_from"]:
            discovered_from = records[entry["discovered_from"]].capture_id
        executor_meta = {
            "executor_surface": "arena_fetch_page_markdown_text",
            "original_transport_kind": "EXECUTOR_TEXT",
            "capture_completeness": entry["completeness"],
            "executor_chunk_index": entry["chunk"]["index"],
            "executor_total_chunks": entry["chunk"]["total"],
            "retrieved_at_precision": "DATE",
        }
        executor_meta.update(entry.get("extra_meta", {}))
        result = runtime.TransportResult(
            requested_url=entry["url"],
            content=text,
            transport_kind=runtime.EXECUTOR_TEXT,
            representation=runtime.TEXT_CAPTURE,
            executor=EXECUTOR,
            retrieved_at=RETRIEVED_AT,
            final_url=entry["url"],
            http_status=None,  # not exposed by the executor surface; never fabricated
            content_type=None,
            executor_meta=executor_meta,
        )
        records[entry["key"]] = runtime.normalize_capture(
            result,
            entry["scope"],
            parent_capture=discovered_from,
            discovered_from=discovered_from,
            content_path=f"captures/{entry['file']}",
            notes=entry["notes"] + ("NORMALIZED_FROM_RECORDED_EXECUTOR_RESULT",),
        )
    return records, texts


# ---------------------------------------------------------------------------
# PROJECT-OWNED source-specific parsing (deliberately OUTSIDE the runtime).
# ---------------------------------------------------------------------------


def parse_vbpl_sitemap_text(text: str) -> tuple[str, ...]:
    """VBPL-specific: split executor-flattened sitemap entries back into locs.

    The VBPL sitemap text concatenates <loc><lastmod><changefreq><priority>
    without separators. This parser is VBPL source semantics and lives in the
    evidence/project layer, never in the generic runtime.
    """

    locs: list[str] = []
    for part in re.split(r"(?=https://vbpl\.vn/)", text):
        part = part.strip()
        if not part:
            continue
        match = re.match(
            r"^(https://vbpl\.vn/.*?)(\d{4}-\d{2}-\d{2})?"
            r"(daily|monthly|weekly|yearly|never|always)?([01](?:\.\d)?)?$",
            part,
            re.S,
        )
        if match:
            locs.append(match.group(1))
    return tuple(dict.fromkeys(locs))


def strip_fragments(urls: tuple[str, ...]) -> tuple[str, ...]:
    """Công Báo-side normalization: drop #fragments, keep order, de-dupe."""

    cleaned = []
    for url in urls:
        base = url.split("#", 1)[0]
        if base and base not in cleaned:
            cleaned.append(base)
    return tuple(cleaned)


# ---------------------------------------------------------------------------
# Manifest assembly
# ---------------------------------------------------------------------------


def build_manifest() -> dict:
    records, texts = build_records()

    # ---- discoveries (generic mechanics + caller-owned patterns) ----------
    vimda_record_links = runtime.select_urls(
        runtime.extract_urls(texts["vimda_listing_c1"]),
        include_hosts=["vimda.moh.gov.vn"],
        include_pattern=r"hoSoId=",
    )
    vimda_pagination_links = runtime.select_urls(
        runtime.extract_urls(texts["vimda_listing_c6"]),
        include_hosts=["vimda.moh.gov.vn"],
        include_pattern=r"_cur=\d+",
    )
    vbpl_sub_sitemaps = parse_vbpl_sitemap_text(texts["vbpl_sitemap_index"])
    vbpl_section_links = parse_vbpl_sitemap_text(texts["vbpl_sitemap_0"])
    vbpl_document_links = tuple(
        url for url in parse_vbpl_sitemap_text(texts["vbpl_sitemap_1_c0"])
        if "/van-ban/chi-tiet/" in url
    )
    vbpl_observed_assets = runtime.select_urls(
        runtime.extract_urls(texts["vbpl_doc_detail"]),
        exclude_pattern=r"vbpl\.vn",
    )
    congbao_agency_links = runtime.select_urls(
        runtime.extract_urls(texts["congbao_home_c3"]),
        include_hosts=["congbao.chinhphu.vn"],
        include_path_prefixes=["/van-ban-dang-cong-bao/"],
    )
    congbao_record_links = tuple(
        url
        for url in strip_fragments(
            runtime.select_urls(
                runtime.extract_urls(texts["congbao_c1_listing_c4"]),
                include_hosts=["congbao.chinhphu.vn"],
                include_path_prefixes=["/van-ban/"],
            )
        )
        if url != CONGBAO_C1_URL
    )
    congbao_issue_links = runtime.select_urls(
        runtime.extract_urls(texts["congbao_c1_listing_c4"])
        + runtime.extract_urls(texts["congbao_record_347_c0"]),
        include_hosts=["congbao.chinhphu.vn"],
        include_path_prefixes=["/cong-bao/"],
    )
    congbao_issue_record_variant_links = runtime.select_urls(
        runtime.extract_urls(texts["congbao_record_347_c0"]),
        include_hosts=["congbao.chinhphu.vn"],
        include_pattern=r"/van-ban/[^/#]+/\d+\.htm",
    )
    congbao_attachment_links = runtime.select_urls(
        runtime.extract_urls(texts["congbao_record_347_c0"])
        + runtime.extract_urls(texts["congbao_c1_listing_c4"]),
        include_hosts=["g7.cdnchinhphu.vn"],
        include_path_prefixes=["/api/download/"],
    )

    # ---- bounded plans + checkpoints ---------------------------------------
    plans = []

    vimda_next_page_url = next(
        url for url in vimda_pagination_links if url.endswith("_cur=2")
    )
    plan_vimda_pages = runtime.page_range_plan(
        [VIMDA_URL, vimda_next_page_url],
        SCOPE_VIMDA,
        discovered_from=records["vimda_listing_c6"].capture_id,
        discovery_text=texts["vimda_listing_c6"],
        max_captures=2,
        notes=(
            "BOUNDED_SAMPLE: site advertises 120.198 results / cur=12020 last page;"
            " plan stops at 2 pages",
        ),
    )
    ckpt_vimda_pages = runtime.build_checkpoint(
        plan_vimda_pages,
        captured={0: records["vimda_listing_c1"].capture_id},
        blocked={1: TRANSPORT_BLOCKED_REASON},
    )
    plans.append(
        {
            "plan": plan_vimda_pages.to_dict(),
            "checkpoint": ckpt_vimda_pages.to_dict(),
            "pending_steps": [s.to_dict() for s in runtime.pending_steps(plan_vimda_pages, ckpt_vimda_pages)],
            "resume_metadata": runtime.resume_plan(plan_vimda_pages, ckpt_vimda_pages).to_dict(),
        }
    )

    plan_vimda_record = runtime.discovered_links_plan(
        [vimda_record_links[0]],
        SCOPE_VIMDA,
        discovered_from=records["vimda_listing_c1"].capture_id,
        discovery_text=texts["vimda_listing_c1"],
        max_captures=1,
        notes=("BOUNDED_SAMPLE: 1 of 2 discovered record links planned",),
    )
    ckpt_vimda_record = runtime.build_checkpoint(
        plan_vimda_record, blocked={0: TRANSPORT_BLOCKED_REASON}
    )
    plans.append(
        {
            "plan": plan_vimda_record.to_dict(),
            "checkpoint": ckpt_vimda_record.to_dict(),
            "pending_steps": [
                s.to_dict()
                for s in runtime.pending_steps(plan_vimda_record, ckpt_vimda_record)
            ],
        }
    )

    plan_vbpl_doc = runtime.discovered_links_plan(
        [VBPL_DOC_URL],
        SCOPE_VBPL,
        discovered_from=records["vbpl_sitemap_1_c0"].capture_id,
        discovery_text=texts["vbpl_sitemap_1_c0"],
        max_captures=1,
    )
    ckpt_vbpl_doc = runtime.build_checkpoint(
        plan_vbpl_doc, captured={0: records["vbpl_doc_detail"].capture_id}
    )
    plans.append(
        {
            "plan": plan_vbpl_doc.to_dict(),
            "checkpoint": ckpt_vbpl_doc.to_dict(),
            "pending_steps": [],
        }
    )

    plan_congbao_listing = runtime.discovered_links_plan(
        [CONGBAO_C1_URL],
        SCOPE_CONGBAO,
        discovered_from=records["congbao_home_c3"].capture_id,
        discovery_text=texts["congbao_home_c3"],
        max_captures=1,
    )
    ckpt_congbao_listing = runtime.build_checkpoint(
        plan_congbao_listing,
        captured={0: records["congbao_c1_listing_c4"].capture_id},
    )
    plans.append(
        {
            "plan": plan_congbao_listing.to_dict(),
            "checkpoint": ckpt_congbao_listing.to_dict(),
            "pending_steps": [],
        }
    )

    plan_congbao_record = runtime.discovered_links_plan(
        [CONGBAO_RECORD_URL],
        SCOPE_CONGBAO,
        discovered_from=records["congbao_c1_listing_c4"].capture_id,
        discovery_text=texts["congbao_c1_listing_c4"],
        max_captures=1,
    )
    ckpt_congbao_record = runtime.build_checkpoint(
        plan_congbao_record,
        captured={0: records["congbao_record_347_c0"].capture_id},
    )
    plans.append(
        {
            "plan": plan_congbao_record.to_dict(),
            "checkpoint": ckpt_congbao_record.to_dict(),
            "pending_steps": [],
        }
    )

    plan_congbao_attachments = runtime.discovered_links_plan(
        list(congbao_attachment_links),
        SCOPE_CONGBAO_CDN,
        discovered_from=records["congbao_record_347_c0"].capture_id,
        discovery_text=texts["congbao_record_347_c0"],
        step_kind="ATTACHMENT",
        max_captures=2,
        notes=(
            "DISCOVERED_NOT_DOWNLOADED: bounded proof records explicit official"
            " attachment URLs only; no bulk/large-file download performed",
        ),
    )
    ckpt_congbao_attachments = runtime.build_checkpoint(plan_congbao_attachments)
    plans.append(
        {
            "plan": plan_congbao_attachments.to_dict(),
            "checkpoint": ckpt_congbao_attachments.to_dict(),
            "pending_steps": [
                s.to_dict()
                for s in runtime.pending_steps(
                    plan_congbao_attachments, ckpt_congbao_attachments
                )
            ],
        }
    )

    # ---- assemble ----------------------------------------------------------
    return {
        "schema": runtime.WEB_CAPTURE_RUNTIME_SCHEMA,
        "task_id": "P2P_PUBLIC_WEB_SCRAPE_RUNTIME_01",
        "issue": 241,
        "generated_by": "evidence/p2p-web-capture-runtime-01/build_manifest.py",
        "generated_at": RETRIEVED_AT,
        "determinism": "BYTE_DETERMINISTIC_REBUILD (no wall-clock inputs)",
        "executor": EXECUTOR,
        "retrieved_session_window_utc_approx": "2026-09-23T02:11Z/2026-09-23T02:58Z",
        "related_capability_ids": list(runtime.RELATED_CAPABILITY_IDS),
        "new_capability_ids_created": [],
        "transport_log": {
            "policy_order": list(runtime.TRANSPORT_POLICY_ORDER),
            "lanes": {
                "PLAIN_HTTP": "UNAVAILABLE_IN_ARENA_SANDBOX: egress restricted to allowlisted hosts (api.github.com reachable; vbpl.vn TLS handshake blocked). Exercised offline in tests via loopback fixture.",
                "EXECUTOR_TEXT": "USED: Arena native public fetch_page markdown text surface; http_status/content_type unobserved -> null.",
                "EXECUTOR_BROWSER": "NOT_PROVIDED: optional lane only; known dead-end browser configuration from Issue #241 deliberately not retried.",
            },
            "successful_live_page_fetches": 16,
            "failed_transport_attempts": 12,
            "failed_transport_attempt_breakdown": {
                "vimda_query_url_signature_failures": 5,
                "post_degradation_control_failures": 3,
                "operator_malformed_proxy_url_fetches": 4,
            },
        },
        "scopes": {
            "VIMDA": SCOPE_VIMDA.to_dict(),
            "VBPL": SCOPE_VBPL.to_dict(),
            "CONGBAO": SCOPE_CONGBAO.to_dict(),
            "CONGBAO_CDN": SCOPE_CONGBAO_CDN.to_dict(),
        },
        "captures": [
            records[entry["key"]].to_dict() for entry in CAPTURE_ENTRIES
        ],
        "discoveries": {
            "mechanism": "runtime.extract_urls/select_urls (generic) + caller-provided include patterns (project-owned semantics)",
            "vimda": {
                "record_detail_links": list(vimda_record_links),
                "pagination_links": list(vimda_pagination_links),
                "pagination_last_page_observed": [
                    url for url in vimda_pagination_links if "cur=12020" in url
                ],
                "result_count_text_observed": "Hiển thị 1 - 10 of 120.198 kết quả.",
                "attachment_links": [],
                "attachment_note": "NOT_OBSERVED_IN_STORED_CHUNKS: 'Văn bản công bố' column empty in stored listing rows; record detail page (attachment/history surface) BLOCKED by transport degradation.",
                "caller_include_pattern": "hoSoId= / _cur=\\d+",
            },
            "vbpl": {
                "sub_sitemaps": list(vbpl_sub_sitemaps),
                "section_links": list(vbpl_section_links),
                "document_links_from_sitemap_1_excerpt": list(vbpl_document_links),
                "relation_links_from_document_detail": [],
                "relation_note": "JS_GATED_BODY: document detail body/relation links are rendered client-side; only loader shell + consent text observable via text transport. robots.txt Disallow:/api/ respected (API surface not touched).",
                "observed_third_party_assets": list(vbpl_observed_assets),
                "source_specific_parser": "parse_vbpl_sitemap_text() in THIS evidence build script (project layer), not in the runtime",
            },
            "congbao": {
                "agency_listing_links_from_home": list(congbao_agency_links),
                "record_links_from_listing": list(congbao_record_links),
                "issue_links": list(congbao_issue_links),
                "issue_record_variant_links": list(congbao_issue_record_variant_links),
                "official_attachment_links_discovered": list(congbao_attachment_links),
                "attachments_downloaded": False,
                "caller_include_patterns": "/van-ban-dang-cong-bao/ , /van-ban/ , /cong-bao/ , g7.cdnchinhphu.vn/api/download/",
            },
        },
        "plans_and_checkpoints": plans,
        "site_proofs": {
            "VIMDA_PROOF": {
                "verdict": "PARTIAL",
                "listing_index_capture": "PASS (stored chunk excerpts 1/7 and 6/7, marked EXCERPT)",
                "pagination_discovery": "PASS (cur=2 next-page and cur=12020 last-page links discovered verbatim; bounded 2-page plan built)",
                "record_detail_capture": "BLOCKED (Arena fetch proxy fails query-string URLs; session-wide proxy degradation afterwards; 5 attempts logged)",
                "attachment_history_url_discovery": "NOT_REACHED (requires record detail page)",
                "no_crawl_no_enumeration": True,
            },
            "VBPL_PROOF": {
                "verdict": "PARTIAL",
                "sitemap_index_capture": "PASS (robots.txt -> sitemap.xml -> sitemap/0.xml full + sitemap/1.xml chunk-0 excerpt)",
                "document_detail_capture": "PASS_AS_TEXT_TRANSPORT_SHELL (loader shell captured; document body JS-gated)",
                "document_url_discovery": "PASS (4 chi-tiet URLs incl. UUID-slug identities parsed from stored sitemap excerpt by PROJECT-OWNED parser)",
                "relation_followup_links": "NOT_EXPOSED_VIA_TEXT_TRANSPORT (JS-gated; /api/ disallowed by robots and respected)",
                "browser_lane": "NOT_AVAILABLE_KNOWN_DEAD_END_CONFIGURATION_NOT_RETRIED",
            },
            "CONGBAO_PROOF": {
                "verdict": "PASS",
                "index_capture": "PASS (home chunk 3/5 excerpt)",
                "record_html_capture": "PASS (agency listing chunk 4/10 excerpt -> record page chunk 0/5 excerpt, full provenance chain)",
                "explicit_official_attachment_discovery": "PASS (DOCX + PDF stream URLs on g7.cdnchinhphu.vn discovered from BOTH listing and record captures; not downloaded)",
                "relation_links": "PASS (Công báo issue links 516-47465.htm and 470418/68388.htm discovered)",
            },
        },
        "safety": {
            "PUBLIC_UNAUTHENTICATED_CONTENT_ONLY": True,
            "CREDENTIALS_OR_COOKIES_USED": False,
            "LOGIN_WAF_CAPTCHA_BYPASS": False,
            "TLS_WEAKENED": False,
            "PROXY_ROTATION": False,
            "ID_BRUTE_FORCE": False,
            "FULL_CRAWL_PERFORMED": False,
            "ATTACHMENTS_DOWNLOADED": False,
            "ROBOTS_DISALLOWED_SURFACES_TOUCHED": False,
            "SERVER_REDACTED_DATA_REPRESENTED_AS_ORIGIN_TRUTH": False,
            "RAW_EVIDENCE_VS_DERIVED_TEXT_VS_INTERPRETATION_SEPARATED": True,
        },
        "boundary": {
            "SOURCE_SPECIFIC_PARSERS_OUTSIDE_RUNTIME": True,
            "runtime_owns": [
                "fetch/capture normalization",
                "provenance (parent_capture/discovered_from)",
                "sha256 hashing",
                "bounded navigation plans",
                "checkpoint/resume metadata",
            ],
            "projects_own": [
                "VIMDA parser",
                "VBPL parser (see parse_vbpl_sitemap_text in this evidence script)",
                "Công Báo attachment semantics",
                "legal interpretation and business semantics",
            ],
            "chatgpt_work_required": False,
            "browser_required_for_all_sites": False,
            "second_router_created": False,
            "second_registry_created": False,
        },
    }


def main() -> None:
    manifest = build_manifest()
    digest = runtime.write_canonical_json(EVIDENCE_DIR / "manifest.json", manifest)
    print(f"manifest.json sha256={digest}")
    print(f"captures={len(manifest['captures'])} plans={len(manifest['plans_and_checkpoints'])}")


if __name__ == "__main__":
    main()
