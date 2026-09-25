# P2P Web/Browser Reverse Evidence Foundation

## Goal

Give P2P a truthful, reusable route for public-website forensics and public
archive reconstruction without adding a second router, a second registry, a
crawler platform, an auto-installer, an MCP control plane, or implicit live
target interaction.

Task: `P2P_WEB_REVERSE_FOUNDATION_01` (Issue #224).
Fresh baseline: `e46089a9fc44ac86936c78d4d98c887ec0158ba2`.

## Reconciliation first: why new IDs were necessary

Fresh read of the canonical law, the capability registry, the SEC01
security/reverse foundation, the Reverse-Skill safe-adoption bridge, the
project-fit provisioning merged in #214, and the research-adoption ledger found
**no** web/browser reverse route: the registry carried Android/mobile/binary
reverse contracts only. Prior public-site prompts therefore had to be described
with an informal label instead of a real P2P route.

Every existing SEC01 security/reverse capability was reconciled before anything
was added (`EXISTING_ROUTE_RECONCILIATION` in the reference bridge). Each one
remains authoritative inside its own scope and is explicitly recorded as *not
sufficient* for a web/browser route, for example:

| Existing capability | Existing scope | Not sufficient for |
| --- | --- | --- |
| `security.mobile.static.assess` | local mobile artifact static assessment | live web document/network evidence |
| `android.network.inspect` | authorized Android device/emulator traffic inspection | browser document/network evidence |
| `android.runtime.instrument` | authorized Android runtime instrumentation | browser JavaScript runtime tracing |
| `reverse.identify` | local binary/managed/archive artifact identification | web endpoint discovery |
| `reverse.decompile.managed` | local managed-code decompilation | browser JavaScript runtime tracing |
| `reverse.semantic_reconstruct` | local artifact semantic reconstruction | public archive/index reconstruction |

The existing Reverse-Skill bridge is **unchanged**. Its pin still equals current
upstream HEAD, so no drift is claimed:

- `zhaoxuya520/reverse-skill@7e2097fd90d25c2f976f6eba26d6c00aa88051df` — MIT,
  pin status `CURRENT_UPSTREAM_HEAD_AT_VERIFICATION`.

## What P2P adds

Four capability declarations, one per evidence source, so that first-line
browser evidence is never confused with deeper runtime reverse work or with
public reconstruction:

| Capability ID | Evidence source role | Truth source |
| --- | --- | --- |
| `web.browser.evidence` | first-line document and network truth | live or captured page document plus observed network requests |
| `web.js.reverse` | deep runtime/source tracing, only when first-line evidence is insufficient | runtime function/source and bundle tracing |
| `web.endpoint.discovery` | client-bundle, static-asset and bounded headless discovery | client bundles, static assets, bounded headless crawl |
| `web.public.reconstruction` | public archive/index reconstruction | public archive, index and search sources |

Plus one data-only post-route reference bridge:

`.p2p/system/p2p_capabilities/web_reverse_reference.py`

The bridge exposes exact upstream provenance, each license boundary, the family
order, escalation preconditions, and explicit `False` flags for bootstrap,
auto-install, MCP registration, browser runtime, network runtime, credential
use, vendoring and external execution. It does **not** accept arbitrary task
text, invoke the P2P router, invoke an upstream router, execute a subprocess,
launch a browser, install software, touch the network, register an MCP server,
or authorize a target.

## Exact upstream provenance (verified 2026-09-21)

| Repository | Pin (equals HEAD at verification) | License | Position |
| --- | --- | --- | --- |
| `ChromeDevTools/chrome-devtools-mcp` | `61780c7498a447771127d1fd3b2454fc4ae4ba28` | Apache-2.0 | declared candidate for `web.browser.evidence` |
| `vmoranv/jshookmcp` | `33983e58cddc998af88a2ed46484364e5425cc86` | AGPL-3.0 | optional external backend for `web.js.reverse` |
| `projectdiscovery/katana` | `c1de26dbe69764a92dfa9a142eb64035e5d05a9d` | MIT | declared candidate for `web.endpoint.discovery` |
| `BishopFox/jsluice` | `0ddfab153e060a9eeaded4d8669233f7c071e7e4` | MIT | subordinate parser reference under endpoint discovery |
| `xnl-h4ck3r/waymore` | `4e02de512fd6b110be92dc8bffb3002edfebcb6c` | MIT | declared candidate for `web.public.reconstruction` |
| `Mouseww/anything-analyzer` | `1da6b5c9acc024e987d41e4b9c88676ffea0da0c` | Apache-2.0 | deferred alternative traffic stack — not adopted |
| `Reqable/reqable-mcp-server` | `2df174f982e9ab481a457ab96e065aac22829a51` | no SPDX license exposed | reference only — adoption prohibited until resolved |

## License boundaries

- MIT and Apache-2.0 candidates: `PERMISSIVE_REFERENCE_ONLY_NOT_VENDORED_NOT_INSTALLED_IN_THIS_TASK`.
- `vmoranv/jshookmcp` is **AGPL-3.0**: recorded as a copyleft external backend
  that is not vendored, not linked, not redistributed with P2P, and not usable
  without a separate Owner activation and AGPL compliance review. Only an
  out-of-tree operator-run backend is contemplated; no covered work enters this
  repository.
- `Reqable/reqable-mcp-server` exposes **no SPDX license**: registered in the
  non-adopted register and the reference lookup fails closed
  (`NON_ADOPTED_UPSTREAM`).
- Two parallel traffic stacks are never adopted by default; the second one is
  deferred rather than added.

## Execution-class and authority boundary

Any live page, browser, crawl or archive retrieval is external target
interaction. Under the existing SEC01 contract the truthful ceiling is
`ACTIVE_TEST_AUTHORIZED`, which the existing control plane blocks by default
without explicit target authorization and a controlled test environment; local
already-captured artifacts stay at the `ANALYSIS_LOCAL` floor. No new execution
class was invented, and no bounded local class is claimed for external
interaction (`UNTRUTHFUL_EXECUTION_CLASS` fails closed).

This task therefore enables **no** runtime: the declarations are
`STATUS=DISCOVERED`, `install_mode=DISABLED`, `execution_status=NOT_EXECUTED`,
with `browser_runtime`, `network_runtime`, `credentials` and `vendor_snapshot`
all `false`.

## What P2P explicitly rejects

- a second router, second registry, second control plane, daemon, browser farm,
  crawler service, or traffic database;
- auto-installing any browser, Node, Go, crawler, hooking backend, analyzer or
  MCP server, and any global MCP configuration write;
- credentials, cookies, subscription tokens, or authenticated private sessions;
- bypass/exploit semantics, unbounded target interaction, or exploit chains;
- bulk-vendoring upstream repositories, and vendoring AGPL-3.0 covered work;
- treating any external tool or page content as P2P authority or as a
  permission grant.

## Projection parity

`.p2p/system/p2p_capabilities/` is projected into installed projects as one
payload, so the new module and the updated registry travel together; the
capability registry was already part of `FOUNDATION_RUNTIME_FILES`, and the new
module is now a required packaged foundation module
(`FOUNDATION_RUNTIME_MODULES`). `tests/test_p2p_web_reverse_reference.py`
projects the real payload with `scripts/package_release.py` and proves the
projected registry and module are byte-identical to the source and still load
with the canonical 8/8 quorum.

## Acceptance contract

`tests/test_p2p_web_reverse_reference.py` proves:

1. no duplicate router/registry/control plane (single router, unchanged
   canonical identities and 8/8 quorum);
2. the route is expressible by the existing P2P router without a fake project
   label (a real capability is selected; scope stays `NON_UI`);
3. first-line browser evidence is distinguished from deep JS reverse, endpoint
   discovery and public/archive reconstruction;
4. upstream provenance is exact and license-aware, including the AGPL and
   no-SPDX boundaries;
5. no auto-install, MCP registration, browser/network runtime or credential use
   is granted;
6. unknown or non-adopted lookups and untruthful declarations fail closed;
7. focused tests pass;
8. installed-runtime projection keeps parity.

## Blast radius and verification

- Focused: `tests/test_p2p_web_reverse_reference.py` (12 tests) plus the two
  directly related SEC01 acceptance modules
  (`tests/test_p2p_reverse_skill_reference.py`,
  `tests/test_p2p_sec01_security_reverse_apkid.py`) — 27 tests pass.
- Registry blast radius: every test module that loads
  `p2p_capabilities/capabilities.json` was run before and after the change. The
  failing set is identical to the pre-change baseline (22 pre-existing failing
  IDs, driven by stale count/origin-main assertions and vendor-hash fixtures);
  no new failure was introduced.
- Package-release blast radius (`scripts/package_release.py` gained the required
  foundation module): all 15 modules that import it were run before and after.
  Failing set identical to baseline (11 failures / 22 errors, same IDs).
- The earlier task-scoped change-set guard in
  `tests/test_p2p_frontend_upstream_intake_01.py` was reconciled with explicitly
  commented, bounded entries for this task's surfaces; that module is green (41
  tests). Its sensitivity to the unrelated tracked test-state file
  `.p2p/system/.p2p/state/adapter_registry.json` is pre-existing: the same guard
  fails identically on an unmodified tree once other tests have run in the same
  process.

## Promotion boundary

This task creates an integration candidate only. It does not authorize release,
deployment, dependency installation, MCP registration, browser/network
activation, live target interaction, or any offensive action. A future
public-site task must still declare its own explicit target scope and
authorization before any live interaction.

## Deferred / next actions

- A separate bounded task may define an anonymous public-read retrieval class if
  public read-only fetching genuinely needs a lower gate than
  `ACTIVE_TEST_AUTHORIZED`. It was **not** created here to avoid weakening the
  existing fail-closed contract.
- Runtime adapters, browser backends, crawl budgets and archive backends remain
  unimplemented by design (`CORE_BEFORE_SUPPORT`).
