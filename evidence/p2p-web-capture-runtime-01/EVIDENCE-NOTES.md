# Evidence notes — P2P_PUBLIC_WEB_SCRAPE_RUNTIME_01 (Issue #241)

Bounded live proof of the generic public-web capture runtime
(`.p2p/system/p2p_capabilities/web_capture_runtime.py`) across three
materially different public Vietnamese government sites, executed from an
Arena session on **2026-09-23** (~02:11–02:55 UTC window).

## What was captured, and how

- **Transport used:** `EXECUTOR_TEXT` — Arena's native public `fetch_page`
  text surface (markdown representation of each public page). No browser was
  launched, no ChatGPT Work was used, no credentials/cookies were sent.
- **Plain HTTP lane:** unavailable in this sandbox — outbound TLS to the
  target hosts is blocked by the sandbox egress policy (only allowlisted
  hosts such as `api.github.com` are reachable directly). The runtime's
  `PlainHttpTransport` is exercised offline against a loopback fixture in
  `tests/test_p2p_web_capture_runtime.py` instead.
- **Browser lane:** not provided (optional by design). The known dead-end
  Arena configuration from Issue #241 (no local Chrome/Chromium, Browser Use
  Cloud auth missing, `api.browser-use.com` unreachable) was deliberately NOT
  retried.
- `http_status` / `content_type` are **null** in every live capture record:
  the executor text surface does not expose them and they are never
  fabricated.

## Capture fidelity (honest representation)

- Files named `*.excerpt.*` are **verbatim excerpts** of the executor text
  result (a prefix of one executor chunk), not the whole page. The manifest
  records `capture_completeness` (`FULL`, `CHUNK_i_OF_n`, or
  `EXCERPT_OF_CHUNK_i_OF_n`) per capture. `byte_count` / `char_count` /
  `sha256` always describe the **stored bytes** of the file, so hashes are
  reproducible from this directory via `build_manifest.py`.
- Content lines are copied verbatim from the executor results, including
  markdown escapes (`\_`, `\-`) and long URLs. Runs of blank lines were
  normalized when copying; no content line, URL, or field was altered.
- `retrieved_at` is recorded at **date precision** (`2026-09-23`); exact
  per-request clock values were not retained by the session.

## Bounded sample — what was deliberately NOT done

- No full crawl: 16 successful live page fetches total across 3 sites; the
  VIMDA listing alone advertises 120,198 records / 12,020 pages, of which
  exactly one page was captured and one more was *planned* (bounded
  `max_captures=2`) but never fetched.
- No attachment downloads: the Công Báo DOCX/PDF URLs were **discovered and
  recorded**, never downloaded.
- No record-ID enumeration: every follow-up URL in the manifest was
  literally discovered inside a stored capture (the runtime's discovery
  verification enforces this).
- `vbpl.vn/robots.txt` disallows `/api/` and `/Pages/`; those surfaces were
  not touched.

## Transport degradation during the session (honest blocker record)

Partway through the session the Arena `fetch_page` proxy began returning
`SignatureDoesNotMatch` errors for every URL (verified with a control
re-fetch of the previously successful `https://vbpl.vn/robots.txt`). Before
degradation, URLs carrying query strings (Liferay portlet URLs) already
failed consistently while query-less URLs succeeded. Consequences recorded
in the manifest checkpoint as `BLOCKED` steps:

- VIMDA record/detail capture (`...hoSoId=781012...`) — 5 attempts (one
  after the evidence build as a final retry), all failed at the proxy layer
  (the site itself was reachable for query-less URLs earlier in the session);
- VIMDA page-2 pagination capture (`...cur=2`) — not attempted after the
  proxy degraded; the discovered link and bounded plan are recorded.

Neither failure is a runtime-contract failure: the same normalized capture
contract, plans, and checkpoint metadata were produced for all three sites
from real captures.

## Source-specific boundary

The VBPL sitemap uses concatenated `<loc>/<lastmod>/<changefreq>/<priority>`
text after executor flattening. Splitting it back into document URLs is
**VBPL-specific parsing** and lives in `build_manifest.py` (evidence layer,
standing in for the consuming project, e.g. VNLAW) — not in the generic
runtime. The runtime only provided generic mechanics: URL extraction,
caller-pattern selection, scope checks, provenance verification, plans, and
checkpointing.
