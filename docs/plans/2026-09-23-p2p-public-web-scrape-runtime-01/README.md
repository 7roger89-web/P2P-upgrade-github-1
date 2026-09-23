# P2P Generic Public-Web Capture Runtime — Issue #241

Task: `P2P_PUBLIC_WEB_SCRAPE_RUNTIME_01` (Issue #241), repair round
`P2P_PUBLIC_WEB_SCRAPE_RUNTIME_01_REPAIR_02` (Supervisor review comment
#5790818568 / Control Tower correction #5790906508).
Fresh baseline: `83ff252e0c7c28d5e5eb583ed8d648d037af596f` (main).
Law source fresh-read: `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`
(`P2P_SUPREME_OPERATING_LAW_V1`, canonical in development source) plus the
repository-root `AGENTS.md` digest.

## Goal

Add the missing RUNTIME/CAPTURE seam under the Issue #224 web capability
family and prove it on materially different public websites — without a
second router, a second registry, a crawler platform, a browser farm, a
database/queue/scheduler, a scraping DSL, or any ChatGPT Work dependency.

## What was added (and what was NOT)

| Added | Deliberately not added |
| --- | --- |
| `.p2p/system/p2p_capabilities/web_capture_runtime.py` — one generic capture contract + thin transport adapters + bounded plans + checkpoint/resume | no new capability IDs (the four `web.*` IDs from #224 are reused unchanged) |
| `tests/test_p2p_web_capture_runtime.py` — 36 focused offline tests (fully mocked transport boundary; no sockets, no live sites) | no changes to `capabilities.json`, the router, quorum, `security_contract.py`, or `web_reverse_reference.py` |
| `evidence/p2p-web-capture-runtime-01/` — bounded live multi-site proof (10 stored captures, deterministic manifest, honest blockers) | no full crawl, no attachment downloads, no ID enumeration, no browser lane activation |
| one line in `scripts/package_release.py` (`FOUNDATION_RUNTIME_MODULES`) to keep installed-project projection parity | no MCP registration, no installs, no vendoring |
| `.github/workflows/web-capture-runtime-focused.yml` — focused PR acceptance mirroring the #224 workflow | no research-adoption ledger changes (no new external upstream was adopted) |

## Generic capture contract

`CaptureRecord` preserves, where observable: `requested_url`, `final_url`,
`retrieved_at`, `source_host`, `transport_kind`, `http_status`,
`content_type`, `representation` (`RAW_BYTES|TEXT_CAPTURE|BROWSER_DOCUMENT|
NETWORK_RESPONSE`), `byte_count`, `char_count`, `sha256`, `capture_scope`,
`parent_capture`, `discovered_from`, `executor` — plus a deterministic
`capture_id`. Unknown values stay `null`; HTTP metadata is never fabricated
(all live captures in this proof carry `http_status=null`,
`content_type=null` because the executor text surface does not expose them).

## Transport policy (cheapest working transport first)

1. `PlainHttpTransport` — stdlib urllib GET; gated by the EXISTING SEC01
   decision (`security_contract.authorize_security_execution(ACTIVE_TEST_AUTHORIZED, ...)`,
   which requires `target_authorized=True` AND `controlled_test_environment=True`
   per call — there is no ad-hoc single boolean); public-only target
   validation plus a fail-closed `socket.getaddrinfo` check that every
   resolved address is globally routable before any external I/O; no
   cookies/credentials, no proxies (environment proxies disabled, never
   rotated), default TLS verification never weakened, bounded reads. In this
   Arena sandbox direct egress to the target hosts is blocked, so this lane is
   proven offline through a mocked public transport boundary in tests (fake
   public DNS answers + fake opener), never through a loopback/private
   production bypass.
2. `ExecutorTextTransport` — executor-native public text fetch (Arena
   `fetch_page`). Used for the entire live proof. Unobserved HTTP metadata
   stays null.
3. `ExecutorBrowserTransport` — OPTIONAL adapter slot. The runtime never
   launches a browser. browser-use/jev-ultrafast and Browser Harness remain
   optional external references only; the known dead-end Arena browser
   configuration (no Chrome/Chromium, Browser Use Cloud auth missing,
   `api.browser-use.com` unreachable) was NOT retried.

ChatGPT Work is not used and is not a dependency anywhere in this seam.

## Bounded navigation + fail-closed guards

Plans are data: `SINGLE_URL`, `PAGE_RANGE`, `DISCOVERED_LINKS`,
`ATTACHMENT_DISCOVERY`, hard-capped at `MAX_PLAN_CAPTURES=64` steps.
The runtime never generates URLs from numeric ranges; every non-seed step
must replay an explicitly discovered URL and carries `discovered_from`
capture provenance. When the discovery capture text is supplied, each step
URL is verified to appear literally inside it — fabricated/hidden record-ID
enumeration fails closed (`URL_NOT_PRESENT_IN_DISCOVERY_CAPTURE`).
Out-of-scope hosts/paths, credential-bearing URLs, non-http(s) schemes,
malformed/ambiguous hosts, out-of-scope redirects, unauthorized live
interaction, and missing browser providers all fail closed. Public-target-only
validation rejects `localhost`-shaped names and every literal address that is
not globally routable (loopback, RFC1918, link-local, unspecified, multicast,
reserved, CGNAT, documentation, IPv6 site-local) via stdlib `ipaddress`. One
runtime-wide capture-size ceiling (`MAX_CAPTURE_BYTES`) is enforced centrally
in `normalize_capture` for all four transport kinds, so plain HTTP, executor
text, executor browser, and recorded results share the same bound. Checkpoint/resume metadata (`plan_id`,
completed/blocked step maps, `pending_steps`, `resume_plan`) is
byte-deterministic.

## Source-specific boundary

The runtime owns fetch/capture normalization, provenance, hashing, bounded
plans, and checkpointing. VIMDA/VBPL/Công Báo parsing and all legal/business
semantics stay in the consuming projects. The proof demonstrates this: the
only site-specific parser in the evidence (VBPL concatenated-sitemap
splitting) lives in `evidence/p2p-web-capture-runtime-01/build_manifest.py`,
outside the runtime module.

## Multi-site proof summary (2026-09-23, Arena `fetch_page` transport)

Evidence: `evidence/p2p-web-capture-runtime-01/` (`EVIDENCE-NOTES.md`,
`captures/`, `manifest.json`, sha256 `8d61146c06273b56331d4aa538f6be04c0976ec46034ebde5376309fc02ffcda`
printed by the deterministic rebuild; see manifest for full detail). 16
successful live page fetches; no crawl; no attachment downloads; robots
`Disallow: /api/` (VBPL) respected.

| Site | Flow proven | Verdict |
| --- | --- | --- |
| Công Báo (`congbao.chinhphu.vn`) | home index → discovered agency listing (`chinh-phu-c1.htm`) → record HTML (`nghi-dinh-so-347-2026-nd-cp-470418.htm`) → explicit official DOCX+PDF attachment URLs (`g7.cdnchinhphu.vn`, discovered, not downloaded) + Công báo issue relation links (516-47465.htm, 470418/68388.htm) | **PASS** |
| VIMDA (`vimda.moh.gov.vn`, Liferay) | listing capture (record rows + record links with stable `hoSoId`/`vanBanId` IDs) → pagination discovery (`cur=2` next, `cur=12020` last, 120.198 results) → bounded 2-page plan; record/detail capture **BLOCKED**: the Arena fetch proxy mis-signs query-string URLs and then degraded session-wide (5 logged attempts); checkpoint records the blocked steps | **PARTIAL** |
| VBPL (`vbpl.vn`) | robots.txt → sitemap.xml → sitemap/0.xml + sitemap/1.xml (chunk 0) → 4 document URLs (slug+UUID identities) parsed project-side → document detail captured as loader shell; body/relation links are JS-gated behind the robots-disallowed `/api/` surface, browser lane unavailable (known dead-end config, not retried) | **PARTIAL** |

Two materially different sites (Công Báo SSR record→attachment chain;
VBPL sitemap→detail chain; plus the VIMDA listing/pagination chain) carry
real runtime proof under the same normalized contract — acceptance for
Issue #241 allows `PASS|PARTIAL` per site with honest classification.

## Tests

```
python3 -m unittest -v tests.test_p2p_web_capture_runtime      # 36 tests
python3 -m unittest tests.test_p2p_web_reverse_reference \
    tests.test_p2p_reverse_skill_reference \
    tests.test_p2p_sec01_security_reverse_apkid                # #224 surface unchanged
python3 evidence/p2p-web-capture-runtime-01/build_manifest.py  # deterministic manifest
```

Coverage maps to the acceptance fields: `GENERIC_CAPTURE_CONTRACT`,
`SINGLE_URL_CAPTURE` (mocked public plain-HTTP boundary + executor text),
per-transport SEC01 authorization facts (target authorized and controlled
environment, each alone insufficient, for plain HTTP / executor text /
executor browser, plus the policy entry point and proof that the existing
`authorize_security_execution` is reused), public-only literal-host and DNS
guards, the runtime-wide capture-size ceiling for every transport kind,
`BOUNDED_PAGINATION_PLAN`, `DISCOVERED_LINK_FOLLOWUP`,
`CHECKPOINT_RESUME_METADATA`, determinism, null-not-fabricated metadata,
fail-closed unbounded/enumeration plans, unchanged router / registry / 8/8
quorum, and projection parity.

## OE gate

`Không bị over engineering chứ?` → **DO_IT**, and re-asked for the repair
round → **DO_IT**: the repair added no new module, no new capability ID, no
second router/registry/risk classifier, no dependency, and no DNS or SSRF
framework — it reuses the existing SEC01 authority function, stdlib
`ipaddress`/`socket.getaddrinfo`, and the existing normalization step. One
module (~750 lines with
docs), one test file, one evidence directory, one workflow; everything else
reused. No crawler platform, no new capability IDs, no second router/
registry; the browser lane is a slot, not an implementation; the live proof
is 16 fetches, not a crawl.
