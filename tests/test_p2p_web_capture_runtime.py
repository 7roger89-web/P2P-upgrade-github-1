"""Focused tests for the generic public-web capture runtime (Issue #241).

Covers the post-repair acceptance surface: the normalized capture contract, all
three live transport gates over the EXISTING SEC01 decision
(``authorize_security_execution(ACTIVE_TEST_AUTHORIZED, ...)``), the
public-target-only URL/scope guard, the fail-closed plain-HTTP resolved-address
guard, the runtime-wide capture-size ceiling for every transport kind, bounded
pagination plans, discovered-link follow-up with provenance, checkpoint/resume
metadata, determinism, honest null HTTP metadata, fail-closed
unauthorized/out-of-scope/unbounded/enumeration-shaped plans, unchanged
router/quorum/registry, and installed-runtime projection parity.

Fully offline: no live external site is contacted and no real socket is opened.
The plain-HTTP lane is exercised through a mocked transport boundary — a fake
``socket.getaddrinfo`` returning globally routable addresses plus a fake
``urllib`` opener — so production validation can stay public-only with no
loopback/private bypass knob (the bounded live multi-site proof lives in
``evidence/p2p-web-capture-runtime-01/``).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
PACKAGE_RELEASE = REPO_ROOT / "scripts" / "package_release.py"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import security_contract as security_contract  # noqa: E402
from p2p_capabilities import web_capture_runtime as runtime  # noqa: E402
from p2p_capabilities.model import CANONICAL_IDENTITIES, load_registry  # noqa: E402

spec = importlib.util.spec_from_file_location("p2p_package_release_capture", PACKAGE_RELEASE)
assert spec and spec.loader
package_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package_release)

EXISTING_WEB_IDS = (
    "web.browser.evidence",
    "web.js.reverse",
    "web.endpoint.discovery",
    "web.public.reconstruction",
)

REQUIRED_CONTRACT_FIELDS = (
    "requested_url",
    "final_url",
    "retrieved_at",
    "source_host",
    "transport_kind",
    "http_status",
    "content_type",
    "representation",
    "byte_count",
    "char_count",
    "sha256",
    "capture_scope",
    "parent_capture",
    "discovered_from",
    "executor",
)

FIXTURE_LISTING_MARKDOWN = """\
| 1 | H29.19-260917-180154 | [Cong bo tieu chuan](https://example.test/web/guest/van-ban?p_p_id=portlet&hoSoId=781012&jspPage=%2Fxemhoso.jsp) |
| 2 | H29.19-260921-180015 | [Cong bo tieu chuan A](https://example.test/web/guest/van-ban?p_p_id=portlet&hoSoId=783001&jspPage=%2Fxemhoso.jsp) |
- [Tiep theo](https://example.test/web/guest/van-ban?delta=10&cur=2)
- [Cuoi cung](https://example.test/web/guest/van-ban?delta=10&cur=12020)
- [Attachment](https://cdn.example.test/api/download/stream?file_name=2026_516.docx)
- [Elsewhere](https://other.test/not-in-scope)
"""

# Fake but genuinely globally routable addresses (example.com A/AAAA records).
# They are only ever returned by a mocked resolver; no packet is sent.
PUBLIC_DNS_IPV4 = "93.184.216.34"
PUBLIC_DNS_IPV6 = "2606:2800:220:1:248:1893:25c8:1946"
PUBLIC_URL = "https://example.test/web/guest/van-ban"
PUBLIC_PAYLOAD = b"<html><body>congbao-fixture</body></html>"
NON_PUBLIC_IPV4 = (
    "127.0.0.1",
    "127.127.127.127",
    "10.0.0.5",
    "10.255.255.254",
    "172.16.4.4",
    "192.168.1.10",
    "169.254.1.1",
    "169.254.169.254",
    "0.0.0.0",
    "224.0.0.1",
    "239.255.255.250",
    "240.0.0.1",
    "255.255.255.255",
    "100.64.0.1",
    "192.0.2.7",
    "198.51.100.7",
    "203.0.113.9",
)
NON_PUBLIC_IPV6 = (
    "::1",
    "::",
    "::ffff:127.0.0.1",
    "fe80::1",
    "fc00::1",
    "fd12:3456::1",
    "ff02::1",
    "2001:db8::1",
)
NON_PUBLIC_HOSTNAMES = (
    "localhost",
    "LOCALHOST",
    "localhost.localdomain",
    "ip6-localhost",
    "app.localhost",
    "deep.nested.localhost.",
)


def target_url(address_or_host: str, path: str = "/web/guest/x") -> str:
    """Build an http URL for a literal address or hostname (IPv6 gets brackets)."""

    host = f"[{address_or_host}]" if ":" in address_or_host else address_or_host
    return f"http://{host}{path}"


def make_scope(**overrides):
    kwargs = {
        "scope_id": "TEST-SCOPE",
        "allowed_host": "example.test",
        "allowed_path_prefixes": ("/web/guest/",),
        "task_authority": "TEST-AUTHORITY",
        "allowed_schemes": ("https", "http"),
    }
    kwargs.update(overrides)
    return runtime.CaptureScope(**kwargs)


def fake_getaddrinfo(addresses):
    """Return a ``socket.getaddrinfo``-shaped callable for the given addresses."""

    def _getaddrinfo(host, port, *args, **kwargs):
        infos = []
        for address in addresses:
            family = socket.AF_INET6 if ":" in address else socket.AF_INET
            sockaddr = (address, 0, 0, 0) if family == socket.AF_INET6 else (address, 0)
            infos.append((family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr))
        return infos

    return _getaddrinfo


class _FakeResponse:
    """Minimal ``http.client.HTTPResponse`` stand-in (context manager aware)."""

    def __init__(self, payload, *, status, content_type, url):
        self._payload = payload
        self.status = status
        self.headers = {"Content-Type": content_type}
        self._url = url

    def read(self, amount=None):
        if amount is None:
            return self._payload
        return self._payload[:amount]

    def geturl(self):
        return self._url

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeOpener:
    """Records requests instead of performing any external I/O."""

    def __init__(self, response):
        self.response = response
        self.requests: list[str] = []
        self.opened = 0

    def open(self, request, timeout=None):  # noqa: ARG002 - mirrors urllib API
        self.requests.append(getattr(request, "full_url", str(request)))
        self.opened += 1
        return self.response


class FakePublicHttpBoundary:
    """Mocked plain-HTTP transport boundary: fake public DNS + fake opener.

    Patches only the two I/O seams the runtime actually uses
    (``socket.getaddrinfo`` and ``urllib.request.build_opener``), so the
    public-only production validation is exercised unmodified.
    """

    def __init__(
        self,
        payload: bytes = PUBLIC_PAYLOAD,
        *,
        status: int = 200,
        content_type: str = "text/html; charset=utf-8",
        addresses=(PUBLIC_DNS_IPV4, PUBLIC_DNS_IPV6),
        dns_error: Exception | None = None,
        url: str = PUBLIC_URL,
    ) -> None:
        self.payload = payload
        self.response = _FakeResponse(
            payload, status=status, content_type=content_type, url=url
        )
        self.opener = _FakeOpener(self.response)
        self.addresses = tuple(addresses)
        self.dns_error = dns_error
        self.resolved_hosts: list[str] = []
        self._patches: list[mock._patch] = []

    def _getaddrinfo(self, host, port, *args, **kwargs):  # noqa: ARG002
        self.resolved_hosts.append(host)
        if self.dns_error is not None:
            raise self.dns_error
        return fake_getaddrinfo(self.addresses)(host, port, *args, **kwargs)

    def __enter__(self):
        self._patches = [
            mock.patch.object(runtime.socket, "getaddrinfo", side_effect=self._getaddrinfo),
            mock.patch.object(
                runtime.urllib.request, "build_opener", return_value=self.opener
            ),
        ]
        for patch in self._patches:
            patch.start()
        return self

    def __exit__(self, *exc_info):
        for patch in reversed(self._patches):
            patch.stop()
        return False


class P2PWebCaptureRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)

    # -- GENERIC_CAPTURE_CONTRACT -------------------------------------------

    def test_01_generic_capture_contract_is_complete_and_deterministic(self) -> None:
        scope = make_scope()
        result = runtime.TransportResult(
            requested_url=PUBLIC_URL,
            content="Xin chao",
            transport_kind=runtime.EXECUTOR_TEXT,
            representation=runtime.TEXT_CAPTURE,
            executor="TEST_EXECUTOR",
            retrieved_at="2026-09-23T02:20:00Z",
            final_url=PUBLIC_URL,
        )
        record = runtime.normalize_capture(result, scope)
        payload = record.to_dict()
        for field_name in REQUIRED_CONTRACT_FIELDS:
            self.assertIn(field_name, payload)
        self.assertEqual(payload["representation"], "TEXT_CAPTURE")
        self.assertEqual(payload["byte_count"], len("Xin chao".encode("utf-8")))
        self.assertEqual(payload["char_count"], len("Xin chao"))
        self.assertEqual(
            payload["sha256"], hashlib.sha256("Xin chao".encode("utf-8")).hexdigest()
        )
        self.assertEqual(payload["source_host"], "example.test")
        # Unobserved HTTP metadata stays null; it is never fabricated.
        self.assertIsNone(payload["http_status"])
        self.assertIsNone(payload["content_type"])
        self.assertIsNone(payload["parent_capture"])
        self.assertIsNone(payload["discovered_from"])
        # Deterministic identity: same inputs -> same capture id and record.
        record_again = runtime.normalize_capture(result, scope)
        self.assertEqual(record_again.capture_id, record.capture_id)
        self.assertEqual(record_again.to_dict(), payload)

    def test_02_bytes_and_text_counts_never_fabricate_char_count(self) -> None:
        scope = make_scope()
        binary = runtime.TransportResult(
            requested_url="https://example.test/web/guest/file.bin",
            content=b"\xff\xfe\x00\x01binary",
            transport_kind=runtime.PLAIN_HTTP,
            representation=runtime.RAW_BYTES,
            executor="TEST_EXECUTOR",
            http_status=200,
            content_type="application/octet-stream",
        )
        record = runtime.normalize_capture(binary, scope)
        self.assertEqual(record.byte_count, 10)
        self.assertIsNone(record.char_count)  # not utf-8 decodable -> unobserved
        self.assertEqual(record.http_status, 200)
        self.assertEqual(record.content_type, "application/octet-stream")

    # -- SINGLE_URL_CAPTURE ---------------------------------------------------

    def test_03_single_url_capture_over_plain_http_public_boundary(self) -> None:
        scope = make_scope()
        adapter = runtime.PlainHttpTransport(timeout_seconds=5.0)
        with FakePublicHttpBoundary() as boundary:
            capture = runtime.capture_with_policy(
                PUBLIC_URL,
                scope,
                [adapter],
                target_authorized=True,
                controlled_test_environment=True,
            )
        record = capture.record
        self.assertEqual(record.transport_kind, runtime.PLAIN_HTTP)
        self.assertEqual(record.representation, runtime.RAW_BYTES)
        self.assertEqual(record.http_status, 200)  # observed, not invented
        self.assertIn("text/html", record.content_type or "")
        self.assertEqual(record.final_url, PUBLIC_URL)
        self.assertEqual(capture.content, PUBLIC_PAYLOAD)
        self.assertEqual(record.sha256, hashlib.sha256(PUBLIC_PAYLOAD).hexdigest())
        # The mocked boundary is the only thing that ran: the public DNS guard
        # resolved the host and the fake opener received exactly one GET.
        self.assertEqual(boundary.resolved_hosts, ["example.test"])
        self.assertEqual(boundary.opener.requests, [PUBLIC_URL])
        self.assertEqual(boundary.opener.opened, 1)

    def test_04_single_url_capture_over_executor_text_transport(self) -> None:
        scope = make_scope()
        calls: list[str] = []

        def executor_fetch(url: str):
            calls.append(url)
            return {
                "content": "# Trang chu\nNoi dung cong khai",
                "url": url,
                "executor_meta": {"executor_chunk_index": 0, "executor_total_chunks": 1},
            }

        adapter = runtime.ExecutorTextTransport(
            executor_name="TEST_ARENA_FETCH_PAGE", fetch_callable=executor_fetch
        )
        capture = runtime.capture_with_policy(
            PUBLIC_URL,
            scope,
            [adapter],
            target_authorized=True,
            controlled_test_environment=True,
        )
        self.assertEqual(calls, [PUBLIC_URL])
        record = capture.record
        self.assertEqual(record.transport_kind, runtime.EXECUTOR_TEXT)
        self.assertEqual(record.representation, runtime.TEXT_CAPTURE)
        self.assertEqual(record.executor, "TEST_ARENA_FETCH_PAGE")
        self.assertIsNone(record.http_status)
        self.assertIsNone(record.content_type)
        self.assertEqual(capture.text, "# Trang chu\nNoi dung cong khai")

    def test_05_transport_policy_is_cheapest_first_and_browser_optional(self) -> None:
        self.assertEqual(
            runtime.TRANSPORT_POLICY_ORDER,
            (runtime.PLAIN_HTTP, runtime.EXECUTOR_TEXT, runtime.EXECUTOR_BROWSER),
        )
        scope = make_scope()
        plain = runtime.PlainHttpTransport(timeout_seconds=5.0)
        executor_calls: list[str] = []
        executor = runtime.ExecutorTextTransport(
            executor_name="EXEC",
            fetch_callable=lambda u: (executor_calls.append(u), {"content": "text"})[1],
        )
        # Adapters supplied out of order: policy still tries plain HTTP first.
        with FakePublicHttpBoundary() as boundary:
            capture = runtime.capture_with_policy(
                PUBLIC_URL,
                scope,
                [executor, plain],
                target_authorized=True,
                controlled_test_environment=True,
            )
        self.assertEqual(capture.record.transport_kind, runtime.PLAIN_HTTP)
        self.assertEqual(boundary.opener.opened, 1)
        self.assertEqual(executor_calls, [])  # cheaper lane worked; no escalation

        # A plain-HTTP lane that fails its public-target guard yields to the
        # next (cheaper-first) lane: the resolved address is non-public, so no
        # external I/O happens and the executor text lane captures instead.
        with FakePublicHttpBoundary(addresses=("10.0.0.5",)) as private_boundary:
            capture = runtime.capture_with_policy(
                PUBLIC_URL,
                scope,
                [executor, plain],
                target_authorized=True,
                controlled_test_environment=True,
            )
        self.assertEqual(capture.record.transport_kind, runtime.EXECUTOR_TEXT)
        self.assertEqual(private_boundary.opener.opened, 0)  # fail closed, no I/O
        self.assertEqual(executor_calls, [PUBLIC_URL])

        # The browser lane stays optional: missing entirely is fine, and an
        # unprovided browser adapter fails closed instead of launching one.
        browser = runtime.ExecutorBrowserTransport()
        with self.assertRaises(runtime.CaptureTransportError) as context:
            browser.fetch(
                PUBLIC_URL, target_authorized=True, controlled_test_environment=True
            )
        self.assertIn("BROWSER_ADAPTER_NOT_PROVIDED", str(context.exception))
        with self.assertRaises(runtime.CaptureTransportError):
            runtime.capture_with_policy(
                PUBLIC_URL,
                scope,
                [browser],
                target_authorized=True,
                controlled_test_environment=True,
            )

        # An executor-provided browser document normalizes as BROWSER_DOCUMENT.
        provided = runtime.ExecutorBrowserTransport(
            executor_name="EXEC_BROWSER",
            render_callable=lambda u: {"content": "<html>rendered</html>", "url": u},
        )
        capture = runtime.capture_with_policy(
            PUBLIC_URL,
            scope,
            [provided],
            target_authorized=True,
            controlled_test_environment=True,
        )
        self.assertEqual(capture.record.representation, runtime.BROWSER_DOCUMENT)
        self.assertEqual(capture.record.transport_kind, runtime.EXECUTOR_BROWSER)

    # -- BOUNDED_PAGINATION_PLAN ---------------------------------------------

    def test_06_bounded_pagination_plan_is_explicit_and_deterministic(self) -> None:
        scope = make_scope()
        seed = PUBLIC_URL
        page2 = "https://example.test/web/guest/van-ban?delta=10&cur=2"
        last = "https://example.test/web/guest/van-ban?delta=10&cur=12020"
        listing_capture_id = "cap-listing"
        plan = runtime.page_range_plan(
            [seed, page2, last],
            scope,
            discovered_from=listing_capture_id,
            discovery_text=FIXTURE_LISTING_MARKDOWN,
            max_captures=3,
        )
        self.assertEqual(plan.plan_kind, runtime.PAGE_RANGE)
        self.assertEqual(len(plan.steps), 3)
        self.assertEqual(plan.steps[0].step_kind, "SEED")
        self.assertEqual(plan.steps[1].step_kind, "PAGINATION")
        self.assertEqual(plan.steps[1].discovered_from, listing_capture_id)
        # Deterministic planning metadata.
        again = runtime.page_range_plan(
            [seed, page2, last],
            scope,
            discovered_from=listing_capture_id,
            discovery_text=FIXTURE_LISTING_MARKDOWN,
            max_captures=3,
        )
        self.assertEqual(again.plan_id, plan.plan_id)
        self.assertEqual(again.to_dict(), plan.to_dict())
        # A bounded plan against a huge listing stops at max_captures.
        self.assertLessEqual(plan.max_captures, runtime.MAX_PLAN_CAPTURES)

    def test_07_unbounded_and_unprovenanced_plans_fail_closed(self) -> None:
        scope = make_scope()
        seed = PUBLIC_URL
        # Too many steps for the hard cap -> unbounded crawl rejected.
        many = [f"https://example.test/web/guest/van-ban?cur={i}" for i in range(2, 70)]
        with self.assertRaises(runtime.CapturePlanError):
            runtime.discovered_links_plan(
                [seed] + many,
                scope,
                discovered_from="cap-x",
                max_captures=runtime.MAX_PLAN_CAPTURES + 1,
            )
        # Fabricated pagination value not present in the discovery capture.
        with self.assertRaises(runtime.CapturePlanError) as context:
            runtime.page_range_plan(
                [seed, "https://example.test/web/guest/van-ban?delta=10&cur=777"],
                scope,
                discovered_from="cap-listing",
                discovery_text=FIXTURE_LISTING_MARKDOWN,
            )
        self.assertIn("URL_NOT_PRESENT_IN_DISCOVERY_CAPTURE", str(context.exception))
        # Non-seed step without discovery provenance -> rejected (this is the
        # structural guard against hidden numeric record-ID enumeration).
        with self.assertRaises(runtime.CapturePlanError) as context:
            runtime.CapturePlan(
                plan_kind=runtime.DISCOVERED_LINKS,
                scope=scope,
                steps=(
                    runtime.PlanStep(step_index=0, url=seed, step_kind="SEED"),
                    runtime.PlanStep(
                        step_index=1,
                        url="https://example.test/web/guest/van-ban?hoSoId=999999",
                        step_kind="RECORD_FOLLOWUP",
                    ),
                ),
                max_captures=2,
            )
        self.assertIn("NON_SEED_STEP_REQUIRES_DISCOVERY_PROVENANCE", str(context.exception))
        # Record-ID brute force shape: consecutive fabricated IDs never appear
        # in any captured page, so discovery verification rejects them.
        brute = [
            f"https://example.test/web/guest/van-ban?p_p_id=portlet&hoSoId={780000 + i}"
            for i in range(10)
        ]
        with self.assertRaises(runtime.CapturePlanError):
            runtime.discovered_links_plan(
                brute, scope, discovered_from="cap-listing", discovery_text="no urls here"
            )

    def test_08_scope_and_url_safety_fail_closed(self) -> None:
        scope = make_scope()
        # Out-of-scope host or path is rejected at plan build time.
        with self.assertRaises(runtime.CaptureScopeError):
            runtime.discovered_links_plan(
                ["https://other.test/not-in-scope"], scope, discovered_from="cap-x"
            )
        with self.assertRaises(runtime.CaptureScopeError):
            runtime.single_url_plan("https://example.test/private/area", scope)
        # Credentials in URLs, bad schemes, and empty scopes fail closed.
        with self.assertRaises(runtime.CaptureScopeError):
            runtime.validate_public_url("https://user:pass@example.test/web/guest/x")
        with self.assertRaises(runtime.CaptureScopeError):
            runtime.validate_public_url("file:///etc/passwd")
        with self.assertRaises(runtime.CaptureScopeError):
            runtime.CaptureScope(
                scope_id="S",
                allowed_host="example.test",
                allowed_path_prefixes=("/web/",),
                task_authority="",
            )
        with self.assertRaises(runtime.CaptureScopeError):
            runtime.CaptureScope(
                scope_id="S",
                allowed_host="example.test",
                allowed_path_prefixes=(),
                task_authority="A",
            )
        # Out-of-scope captures cannot be normalized even if a transport
        # somehow returned them.
        with self.assertRaises(runtime.CaptureScopeError):
            runtime.normalize_capture(
                runtime.TransportResult(
                    requested_url="https://other.test/x",
                    content="x",
                    transport_kind=runtime.EXECUTOR_TEXT,
                    representation=runtime.TEXT_CAPTURE,
                    executor="E",
                ),
                scope,
            )
        # An out-of-scope redirect fails closed as well.
        with self.assertRaises(runtime.CaptureScopeError):
            runtime.normalize_capture(
                runtime.TransportResult(
                    requested_url=PUBLIC_URL,
                    content="x",
                    transport_kind=runtime.PLAIN_HTTP,
                    representation=runtime.RAW_BYTES,
                    executor="E",
                    final_url="https://example.test/private/redirected",
                ),
                scope,
            )

    # -- DISCOVERED_LINK_FOLLOWUP ---------------------------------------------

    def test_09_discovered_link_followup_keeps_provenance_chain(self) -> None:
        scope = make_scope()
        urls = runtime.extract_urls(FIXTURE_LISTING_MARKDOWN)
        record_urls = runtime.select_urls(urls, include_pattern=r"hoSoId=")
        self.assertEqual(len(record_urls), 2)
        pagination_urls = runtime.select_urls(urls, include_pattern=r"cur=\d+")
        self.assertEqual(len(pagination_urls), 2)
        attachment_urls = runtime.select_urls(urls, include_hosts=["cdn.example.test"])
        self.assertEqual(len(attachment_urls), 1)
        # Determinism: extraction and selection are stable and sorted.
        self.assertEqual(urls, tuple(sorted(set(urls))))
        self.assertEqual(runtime.extract_urls(FIXTURE_LISTING_MARKDOWN), urls)

        listing_id = "cap-listing"
        plan = runtime.discovered_links_plan(
            record_urls[:1],
            scope,
            discovered_from=listing_id,
            discovery_text=FIXTURE_LISTING_MARKDOWN,
        )
        self.assertEqual(plan.plan_kind, runtime.DISCOVERED_LINKS)
        record_result = runtime.TransportResult(
            requested_url=plan.steps[0].url,
            content="record detail",
            transport_kind=runtime.EXECUTOR_TEXT,
            representation=runtime.TEXT_CAPTURE,
            executor="E",
            retrieved_at="2026-09-23",
        )
        record = runtime.normalize_capture(
            record_result, scope, parent_capture=listing_id, discovered_from=listing_id
        )
        self.assertEqual(record.parent_capture, listing_id)
        self.assertEqual(record.discovered_from, listing_id)
        # Attachment discovery plan uses the ATTACHMENT step kind.
        attachment_scope = make_scope(
            scope_id="CDN", allowed_host="cdn.example.test", allowed_path_prefixes=("/api/",)
        )
        attachment_plan = runtime.discovered_links_plan(
            attachment_urls,
            attachment_scope,
            discovered_from=listing_id,
            step_kind="ATTACHMENT",
        )
        self.assertEqual(attachment_plan.plan_kind, runtime.ATTACHMENT_DISCOVERY)
        self.assertEqual(attachment_plan.steps[0].step_kind, "ATTACHMENT")

    # -- CHECKPOINT_RESUME_METADATA -------------------------------------------

    def test_10_checkpoint_resume_metadata_is_deterministic(self) -> None:
        scope = make_scope()
        seed = PUBLIC_URL
        page2 = "https://example.test/web/guest/van-ban?delta=10&cur=2"
        plan = runtime.page_range_plan(
            [seed, page2], scope, discovered_from="cap-listing", max_captures=2
        )
        checkpoint = runtime.build_checkpoint(
            plan, captured={0: "cap-seed"}, blocked={1: "TRANSPORT_QUERY_URL_BLOCKED"}
        )
        payload = checkpoint.to_dict()
        self.assertEqual(payload["plan_id"], plan.plan_id)
        self.assertEqual(payload["completed"], {"0": "cap-seed"})
        self.assertEqual(payload["blocked"], {"1": "TRANSPORT_QUERY_URL_BLOCKED"})
        # Determinism: rebuilding the same checkpoint yields identical metadata.
        again = runtime.build_checkpoint(
            plan, captured={0: "cap-seed"}, blocked={1: "TRANSPORT_QUERY_URL_BLOCKED"}
        )
        self.assertEqual(again.to_dict(), payload)
        # Round trip through JSON keeps the checkpoint usable.
        restored = runtime.CheckpointState.from_dict(
            json.loads(json.dumps(payload, sort_keys=True))
        )
        self.assertEqual(restored.to_dict(), payload)
        # Pending/resume only replays unfinished steps, still bounded.
        pending = runtime.pending_steps(plan, checkpoint)
        self.assertEqual([step.step_index for step in pending], [1])
        resumed = runtime.resume_plan(plan, checkpoint)
        self.assertEqual(len(resumed.steps), 1)
        self.assertLessEqual(resumed.max_captures, runtime.MAX_PLAN_CAPTURES)
        # A mismatched checkpoint cannot drive another plan.
        other = runtime.single_url_plan(seed, scope)
        with self.assertRaises(runtime.CapturePlanError):
            runtime.pending_steps(other, checkpoint)
        with self.assertRaises(runtime.CapturePlanError):
            runtime.build_checkpoint(plan, captured={7: "cap-ghost"})
        with self.assertRaises(runtime.CapturePlanError):
            runtime.build_checkpoint(plan, captured={0: "a"}, blocked={0: "b"})

    # -- evidence writer -------------------------------------------------------

    def test_11_evidence_writer_persists_exact_bytes_and_canonical_json(self) -> None:
        scope = make_scope()
        capture = runtime.Capture(
            record=runtime.normalize_capture(
                runtime.TransportResult(
                    requested_url=PUBLIC_URL,
                    content="Noi dung",
                    transport_kind=runtime.EXECUTOR_TEXT,
                    representation=runtime.TEXT_CAPTURE,
                    executor="E",
                ),
                scope,
            ),
            content="Noi dung".encode("utf-8"),
            text="Noi dung",
        )
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "captures"
            record = runtime.write_capture(directory, capture, extension=".md")
            stored = (directory / Path(record.content_path or "")).read_bytes()
            self.assertEqual(stored, capture.content)
            self.assertEqual(hashlib.sha256(stored).hexdigest(), record.sha256)
            manifest = Path(tmp) / "manifest.json"
            digest_first = runtime.write_canonical_json(
                manifest, {"captures": [record.to_dict()]}
            )
            digest_second = runtime.write_canonical_json(
                manifest, {"captures": [record.to_dict()]}
            )
            self.assertEqual(digest_first, digest_second)  # deterministic output

    # -- no second router / registry / capability ------------------------------

    def test_12_runtime_creates_no_router_registry_or_new_capability(self) -> None:
        registry_ids = set(self.registry["identities"])
        for capability_id in EXISTING_WEB_IDS:
            self.assertIn(capability_id, registry_ids)
        self.assertNotIn("web.public.capture", registry_ids)
        self.assertNotIn("web.scrape.runtime", registry_ids)
        self.assertEqual(self.registry["canonical_identities"], list(CANONICAL_IDENTITIES))
        self.assertEqual(self.registry["full_quorum"], "8/8")
        # The runtime reuses the existing family ids instead of adding new ones.
        self.assertEqual(runtime.RELATED_CAPABILITY_IDS, EXISTING_WEB_IDS)
        source = Path(runtime.__file__).read_text(encoding="utf-8")
        for marker in (
            "classify_capabilities(",
            "task_text",
            "from .routing import",
            "p2p_uiux",
            "capabilities.json",
        ):
            self.assertNotIn(marker, source)
        # The repair must not have added a second authorization model either:
        # the SEC01 function is imported (reused), never reimplemented.
        self.assertIn("authorize_security_execution(", source)
        for forbidden in (
            "def authorize_security_execution",
            "class SecurityDecision",
            "risk_classifier",
        ):
            self.assertNotIn(forbidden, source)
        router_source = (SYSTEM_ROOT / "p2p_uiux" / "router.py").read_text(encoding="utf-8")
        self.assertNotIn("web_capture_runtime", router_source)

    def test_13_installed_runtime_projection_keeps_parity(self) -> None:
        self.assertIn(
            "web_capture_runtime.py", package_release.FOUNDATION_RUNTIME_MODULES
        )
        source_module = (
            SYSTEM_ROOT / "p2p_capabilities" / "web_capture_runtime.py"
        ).read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp) / "stage"
            stage.mkdir()
            package_release.copy_foundation_runtime(REPO_ROOT, stage)
            projected = stage / "runtime" / "p2p_capabilities" / "web_capture_runtime.py"
            self.assertEqual(projected.read_bytes(), source_module)

    # -- BLOCKER A: SEC01 authorization for every live transport --------------

    def test_14_plain_http_blocked_when_target_authorized_false(self) -> None:
        adapter = runtime.PlainHttpTransport(timeout_seconds=5.0)
        with FakePublicHttpBoundary() as boundary:
            with self.assertRaises(runtime.CaptureAuthorizationError) as context:
                adapter.fetch(
                    PUBLIC_URL,
                    target_authorized=False,
                    controlled_test_environment=True,
                )
        self.assertIn("TARGET_AUTHORIZATION_REQUIRED", str(context.exception))
        with FakePublicHttpBoundary() as boundary_2:
            with self.assertRaises(runtime.CaptureAuthorizationError):
                runtime.capture_with_policy(
                    PUBLIC_URL,
                    make_scope(),
                    [adapter],
                    target_authorized=False,
                    controlled_test_environment=True,
                )
        # Fail closed BEFORE any external I/O: no resolution, no HTTP request.
        self.assertEqual(boundary.resolved_hosts, [])
        self.assertEqual(boundary.opener.requests, [])
        self.assertEqual(boundary_2.opener.opened, 0)

    def test_15_plain_http_blocked_when_controlled_test_environment_false(self) -> None:
        adapter = runtime.PlainHttpTransport(timeout_seconds=5.0)
        with FakePublicHttpBoundary() as boundary:
            with self.assertRaises(runtime.CaptureAuthorizationError) as context:
                adapter.fetch(
                    PUBLIC_URL,
                    target_authorized=True,
                    controlled_test_environment=False,
                )
        self.assertIn("CONTROLLED_TEST_ENVIRONMENT_REQUIRED", str(context.exception))
        with FakePublicHttpBoundary() as boundary_2:
            with self.assertRaises(runtime.CaptureAuthorizationError):
                runtime.capture_with_policy(
                    PUBLIC_URL,
                    make_scope(),
                    [adapter],
                    target_authorized=True,
                    controlled_test_environment=False,
                )
        self.assertEqual(boundary.resolved_hosts, [])
        self.assertEqual(boundary_2.opener.opened, 0)

    def test_16_executor_text_blocked_when_target_authorized_false(self) -> None:
        calls: list[str] = []
        adapter = runtime.ExecutorTextTransport(
            executor_name="EXEC",
            fetch_callable=lambda u: (calls.append(u), {"content": "text"})[1],
        )
        with self.assertRaises(runtime.CaptureAuthorizationError) as context:
            adapter.fetch(PUBLIC_URL, target_authorized=False, controlled_test_environment=True)
        self.assertIn("TARGET_AUTHORIZATION_REQUIRED", str(context.exception))
        with self.assertRaises(runtime.CaptureAuthorizationError):
            runtime.capture_with_policy(
                PUBLIC_URL,
                make_scope(),
                [adapter],
                target_authorized=False,
                controlled_test_environment=True,
            )
        self.assertEqual(calls, [])  # the executor was never invoked

    def test_17_executor_text_blocked_when_controlled_test_environment_false(self) -> None:
        calls: list[str] = []
        adapter = runtime.ExecutorTextTransport(
            executor_name="EXEC",
            fetch_callable=lambda u: (calls.append(u), {"content": "text"})[1],
        )
        with self.assertRaises(runtime.CaptureAuthorizationError) as context:
            adapter.fetch(PUBLIC_URL, target_authorized=True, controlled_test_environment=False)
        self.assertIn("CONTROLLED_TEST_ENVIRONMENT_REQUIRED", str(context.exception))
        with self.assertRaises(runtime.CaptureAuthorizationError):
            runtime.capture_with_policy(
                PUBLIC_URL,
                make_scope(),
                [adapter],
                target_authorized=True,
                controlled_test_environment=False,
            )
        self.assertEqual(calls, [])

    def test_18_executor_browser_blocked_when_target_authorized_false(self) -> None:
        renders: list[str] = []
        adapter = runtime.ExecutorBrowserTransport(
            executor_name="EXEC_BROWSER",
            render_callable=lambda u: (renders.append(u), {"content": "<html/>"})[1],
        )
        with self.assertRaises(runtime.CaptureAuthorizationError) as context:
            adapter.fetch(PUBLIC_URL, target_authorized=False, controlled_test_environment=True)
        self.assertIn("TARGET_AUTHORIZATION_REQUIRED", str(context.exception))
        with self.assertRaises(runtime.CaptureAuthorizationError):
            runtime.capture_with_policy(
                PUBLIC_URL,
                make_scope(),
                [adapter],
                target_authorized=False,
                controlled_test_environment=True,
            )
        self.assertEqual(renders, [])  # the browser surface was never driven

    def test_19_executor_browser_blocked_when_controlled_test_environment_false(self) -> None:
        renders: list[str] = []
        adapter = runtime.ExecutorBrowserTransport(
            executor_name="EXEC_BROWSER",
            render_callable=lambda u: (renders.append(u), {"content": "<html/>"})[1],
        )
        with self.assertRaises(runtime.CaptureAuthorizationError) as context:
            adapter.fetch(PUBLIC_URL, target_authorized=True, controlled_test_environment=False)
        self.assertIn("CONTROLLED_TEST_ENVIRONMENT_REQUIRED", str(context.exception))
        with self.assertRaises(runtime.CaptureAuthorizationError):
            runtime.capture_with_policy(
                PUBLIC_URL,
                make_scope(),
                [adapter],
                target_authorized=True,
                controlled_test_environment=False,
            )
        self.assertEqual(renders, [])

    def test_20_both_authorization_facts_allow_adapter_execution(self) -> None:
        scope = make_scope()
        facts = {"target_authorized": True, "controlled_test_environment": True}
        with FakePublicHttpBoundary() as boundary:
            plain = runtime.PlainHttpTransport(timeout_seconds=5.0).fetch(PUBLIC_URL, **facts)
        self.assertEqual(plain.transport_kind, runtime.PLAIN_HTTP)
        self.assertEqual(boundary.opener.opened, 1)

        text = runtime.ExecutorTextTransport(
            executor_name="EXEC", fetch_callable=lambda u: {"content": "text"}
        ).fetch(PUBLIC_URL, **facts)
        self.assertEqual(text.transport_kind, runtime.EXECUTOR_TEXT)

        browser = runtime.ExecutorBrowserTransport(
            executor_name="EXEC_BROWSER",
            render_callable=lambda u: {"content": "<html>rendered</html>"},
        ).fetch(PUBLIC_URL, **facts)
        self.assertEqual(browser.transport_kind, runtime.EXECUTOR_BROWSER)

        # And the policy orchestrator also captures when both facts are true.
        capture = runtime.capture_with_policy(PUBLIC_URL, scope, [
            runtime.ExecutorTextTransport(
                executor_name="EXEC", fetch_callable=lambda u: {"content": "policy"}
            )
        ], **facts)
        self.assertEqual(capture.record.transport_kind, runtime.EXECUTOR_TEXT)
        self.assertEqual(capture.text, "policy")

    def test_21_capture_with_policy_cannot_bypass_authorization_gate(self) -> None:
        calls: list[str] = []
        adapter = runtime.ExecutorTextTransport(
            executor_name="EXEC",
            fetch_callable=lambda u: (calls.append(u), {"content": "text"})[1],
        )
        scope = make_scope()
        # No facts at all.
        with self.assertRaises(runtime.CaptureAuthorizationError):
            runtime.capture_with_policy(PUBLIC_URL, scope, [adapter])
        # Only one of the two required SEC01 facts.
        for facts in (
            {"target_authorized": True},
            {"controlled_test_environment": True},
        ):
            with self.assertRaises(runtime.CaptureAuthorizationError):
                runtime.capture_with_policy(PUBLIC_URL, scope, [adapter], **facts)
        self.assertEqual(calls, [])
        # The old ad-hoc single authorization boolean no longer exists on any
        # live transport, so it cannot be used as a shortcut.
        for live_adapter in (
            runtime.PlainHttpTransport(),
            adapter,
            runtime.ExecutorBrowserTransport(
                executor_name="B", render_callable=lambda u: {"content": "<html/>"}
            ),
        ):
            with self.assertRaises(TypeError):
                live_adapter.fetch(PUBLIC_URL, authorized=True)

    def test_22_existing_sec01_authorize_security_execution_is_reused(self) -> None:
        # The runtime reuses the existing SEC01 function object directly.
        self.assertIs(
            runtime.authorize_security_execution,
            security_contract.authorize_security_execution,
        )
        self.assertEqual(runtime.LIVE_CAPTURE_EXECUTION_CLASS, "ACTIVE_TEST_AUTHORIZED")
        real_decision = security_contract.authorize_security_execution
        spy = mock.Mock(side_effect=real_decision)
        with mock.patch.object(runtime, "authorize_security_execution", spy):
            adapter = runtime.ExecutorTextTransport(
                executor_name="EXEC", fetch_callable=lambda u: {"content": "text"}
            )
            adapter.fetch(PUBLIC_URL, target_authorized=True, controlled_test_environment=True)
        spy.assert_called_once_with(
            "ACTIVE_TEST_AUTHORIZED",
            target_authorized=True,
            controlled_test_environment=True,
        )
        # And the SEC01 semantics themselves are what gate the transports.
        allowed = real_decision(
            security_contract.ACTIVE_TEST_AUTHORIZED,
            target_authorized=True,
            controlled_test_environment=True,
        )
        self.assertIs(allowed["allowed"], True)
        for facts, reason in (
            ({"target_authorized": True}, "CONTROLLED_TEST_ENVIRONMENT_REQUIRED"),
            ({"controlled_test_environment": True}, "TARGET_AUTHORIZATION_REQUIRED"),
            ({}, "TARGET_AUTHORIZATION_REQUIRED"),
        ):
            decision = real_decision(
                security_contract.ACTIVE_TEST_AUTHORIZED,
                target_authorized=facts.get("target_authorized", False),
                controlled_test_environment=facts.get("controlled_test_environment", False),
            )
            self.assertIs(decision["allowed"], False)
            self.assertIn(reason, decision["reason_codes"])
            with self.assertRaises(runtime.CaptureAuthorizationError) as context:
                runtime.require_live_capture_authorization(
                    target_authorized=facts.get("target_authorized", False),
                    controlled_test_environment=facts.get("controlled_test_environment", False),
                )
            self.assertIn(reason, str(context.exception))
        self.assertEqual(
            runtime.require_live_capture_authorization(
                target_authorized=True, controlled_test_environment=True
            )["execution_class"],
            "ACTIVE_TEST_AUTHORIZED",
        )

    # -- BLOCKER B: public targets only ---------------------------------------

    def test_23_localhost_shaped_hosts_rejected(self) -> None:
        for host in NON_PUBLIC_HOSTNAMES:
            with self.subTest(host=host):
                with self.assertRaises(runtime.CaptureScopeError) as context:
                    runtime.validate_public_url(target_url(host))
                self.assertIn("NON_PUBLIC_TARGET_HOST_REJECTED", str(context.exception))
                with self.assertRaises(runtime.CaptureScopeError):
                    make_scope(allowed_host=host)

    def test_24_loopback_literal_addresses_rejected(self) -> None:
        for address in ("127.0.0.1", "127.0.0.0", "127.255.255.255", "::1", "::ffff:127.0.0.1"):
            with self.subTest(address=address):
                with self.assertRaises(runtime.CaptureScopeError):
                    runtime.validate_public_url(target_url(address))
                with self.assertRaises(runtime.CaptureScopeError):
                    make_scope(allowed_host=address)

    def test_25_private_and_link_local_networks_rejected(self) -> None:
        for address in ("10.0.0.5", "10.255.255.254", "172.16.4.4", "192.168.1.10",
                        "169.254.1.1", "169.254.169.254", "fc00::1", "fd12:3456::1", "fe80::1"):
            with self.subTest(address=address):
                with self.assertRaises(runtime.CaptureScopeError):
                    runtime.validate_public_url(target_url(address))
                with self.assertRaises(runtime.CaptureScopeError):
                    make_scope(allowed_host=address)

    def test_26_unspecified_multicast_reserved_and_non_global_rejected(self) -> None:
        for address in NON_PUBLIC_IPV4 + NON_PUBLIC_IPV6:
            with self.subTest(address=address):
                with self.assertRaises(runtime.CaptureScopeError):
                    runtime.validate_public_url(target_url(address))

    def test_27_ambiguous_or_malformed_host_shapes_fail_closed(self) -> None:
        # Unbracketed IPv6 authorities are ambiguous (urlsplit would report
        # ``fd12`` as the host), so they are rejected rather than guessed at.
        for url in (
            "https://fd12:3456::1/web/guest/x",
            "https://fd12::1/web/guest/x",
            "https://2001:4860:4860::8888/web/guest/x",
        ):
            with self.subTest(url=url):
                with self.assertRaises(runtime.CaptureScopeError) as context:
                    runtime.validate_public_url(url)
                self.assertIn("INVALID_HOST_SYNTAX", str(context.exception))
        # Bracketed IPv4, non-numeric ports, and other malformed shapes.
        for url, marker in (
            ("http://[93.184.216.34]/web/guest/x", "INVALID_URL_SYNTAX"),
            ("https://example.test:abc/web/guest/x", "INVALID_PORT"),
            ("https:///web/guest/x", "EMPTY_HOST"),
            ("https://", "EMPTY_HOST"),
        ):
            with self.subTest(url=url):
                with self.assertRaises(runtime.CaptureScopeError) as context:
                    runtime.validate_public_url(url)
                self.assertIn(marker, str(context.exception))
        # Bracketed public IPv6 literals remain valid.
        bracketed = f"https://[{PUBLIC_DNS_IPV6}]/web/guest/x"
        self.assertEqual(runtime.validate_public_url(bracketed), bracketed)

    def test_27b_capture_scope_host_must_be_public(self) -> None:
        # The production scope path cannot authorize loopback/private targets:
        # the loopback bypass is gone and no bypass flag was added.
        for host in ("127.0.0.1", "localhost", "10.1.2.3", "::1", "169.254.10.10"):
            with self.subTest(host=host):
                with self.assertRaises(runtime.CaptureScopeError):
                    runtime.CaptureScope(
                        scope_id="BYPASS_ATTEMPT",
                        allowed_host=host,
                        allowed_path_prefixes=("/",),
                        task_authority="A",
                        allowed_schemes=("http",),
                    )
        source = Path(runtime.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "allow_private",
            "test_mode",
            "skip_public_validation",
            "allow_loopback",
        ):
            self.assertNotIn(forbidden, source)
        # Public hosts still work normally.
        public_scope = make_scope(allowed_host="example.test")
        self.assertTrue(public_scope.allows(PUBLIC_URL))
        self.assertEqual(runtime.validate_public_url(PUBLIC_URL), PUBLIC_URL)

    def test_28_plain_http_rejects_non_public_dns_resolution(self) -> None:
        adapter = runtime.PlainHttpTransport(timeout_seconds=5.0)
        facts = {"target_authorized": True, "controlled_test_environment": True}
        for addresses in (
            ("10.0.0.5",),                    # RFC1918
            ("192.168.1.10",),
            ("169.254.169.254",),              # cloud metadata / link-local
            ("::1",),                          # IPv6 loopback
            ("fe80::1",),                      # IPv6 link-local
            ("0.0.0.0",),                      # unspecified
            ("224.0.0.1",),                    # multicast (is_global on some stdlibs)
            ("ff02::1",),                      # IPv6 multicast
            ("240.0.0.1",),                    # reserved
            ("fec0::1",),                      # IPv6 site-local
            (PUBLIC_DNS_IPV4, "10.0.0.5"),     # mixed public + private
        ):
            with self.subTest(addresses=addresses):
                with FakePublicHttpBoundary(addresses=addresses) as boundary:
                    with self.assertRaises(runtime.CaptureTransportError) as context:
                        adapter.fetch(PUBLIC_URL, **facts)
                self.assertIn("NON_PUBLIC_TARGET_RESOLVED", str(context.exception))
                self.assertEqual(boundary.opener.opened, 0)  # no external I/O
        # DNS failure and empty answers fail closed as well.
        with FakePublicHttpBoundary(dns_error=socket.gaierror("no such host")) as failing:
            with self.assertRaises(runtime.CaptureTransportError) as context:
                adapter.fetch(PUBLIC_URL, **facts)
        self.assertIn("DNS_RESOLUTION_FAILED", str(context.exception))
        self.assertEqual(failing.opener.opened, 0)
        with FakePublicHttpBoundary(addresses=()) as empty:
            with self.assertRaises(runtime.CaptureTransportError) as context:
                adapter.fetch(PUBLIC_URL, **facts)
        self.assertIn("DNS_RESOLUTION_EMPTY", str(context.exception))
        self.assertEqual(empty.opener.opened, 0)
        # The guard is public-address only: an in-scope non-public URL never
        # even reaches resolution.
        with self.assertRaises(runtime.CaptureScopeError):
            adapter.fetch("http://127.0.0.1/web/guest/x", **facts)

    def test_29_plain_http_accepts_mocked_global_dns_target(self) -> None:
        adapter = runtime.PlainHttpTransport(timeout_seconds=5.0)
        with FakePublicHttpBoundary() as boundary:
            result = adapter.fetch(
                PUBLIC_URL, target_authorized=True, controlled_test_environment=True
            )
            self.assertEqual(
                runtime.require_public_resolved_host(PUBLIC_URL),
                tuple(sorted({PUBLIC_DNS_IPV4, PUBLIC_DNS_IPV6})),
            )
        self.assertEqual(result.final_url, PUBLIC_URL)
        self.assertEqual(result.http_status, 200)
        self.assertEqual(result.content, PUBLIC_PAYLOAD)
        # Two resolutions: the explicit guard call above plus the transport's
        # own pre-I/O check. Both are mocked; no packet leaves the test.
        self.assertEqual(set(boundary.resolved_hosts), {"example.test"})
        self.assertEqual(len(boundary.resolved_hosts), 2)
        self.assertEqual(boundary.opener.opened, 1)
        # The mocked resolver is what made this possible; the same mock points
        # a non-global address at the same host, and that fails closed.
        with FakePublicHttpBoundary(addresses=("127.0.0.1",)) as loopback_alias:
            with self.assertRaises(runtime.CaptureTransportError):
                adapter.fetch(
                    PUBLIC_URL, target_authorized=True, controlled_test_environment=True
                )
        self.assertEqual(loopback_alias.opener.opened, 0)

    # -- BLOCKER C: one runtime-wide capture-size ceiling ---------------------

    def test_30_oversized_plain_http_rejected(self) -> None:
        oversized = b"y" * (runtime.MAX_CAPTURE_BYTES + 1)
        adapter = runtime.PlainHttpTransport(timeout_seconds=5.0)
        facts = {"target_authorized": True, "controlled_test_environment": True}
        with FakePublicHttpBoundary(payload=oversized) as boundary:
            with self.assertRaises(runtime.CaptureTransportError) as context:
                adapter.fetch(PUBLIC_URL, **facts)
        self.assertIn(runtime.CAPTURE_SIZE_LIMIT_EXCEEDED, str(context.exception))
        self.assertEqual(boundary.opener.opened, 1)  # read was bounded, then refused
        # The central ceiling also refuses an oversized plain-HTTP result that
        # bypassed the adapter's own read bound.
        with self.assertRaises(runtime.CaptureTransportError) as context:
            runtime.normalize_capture(
                runtime.TransportResult(
                    requested_url=PUBLIC_URL,
                    content=oversized,
                    transport_kind=runtime.PLAIN_HTTP,
                    representation=runtime.RAW_BYTES,
                    executor="E",
                ),
                make_scope(),
            )
        self.assertIn(runtime.CAPTURE_SIZE_LIMIT_EXCEEDED, str(context.exception))

    def test_31_oversized_executor_text_rejected(self) -> None:
        oversized = "z" * (runtime.MAX_CAPTURE_BYTES + 1)
        adapter = runtime.ExecutorTextTransport(
            executor_name="EXEC", fetch_callable=lambda u: {"content": oversized}
        )
        result = adapter.fetch(
            PUBLIC_URL, target_authorized=True, controlled_test_environment=True
        )
        with self.assertRaises(runtime.CaptureTransportError) as context:
            runtime.normalize_capture(result, make_scope())
        self.assertIn(runtime.CAPTURE_SIZE_LIMIT_EXCEEDED, str(context.exception))
        # ...and the policy path cannot normalize it either.
        with self.assertRaises(runtime.CaptureTransportError) as policy_context:
            runtime.capture_with_policy(
                PUBLIC_URL,
                make_scope(),
                [adapter],
                target_authorized=True,
                controlled_test_environment=True,
            )
        self.assertIn(runtime.CAPTURE_SIZE_LIMIT_EXCEEDED, str(policy_context.exception))

    def test_32_oversized_executor_browser_rejected(self) -> None:
        oversized = b"w" * (runtime.MAX_CAPTURE_BYTES + 1)
        adapter = runtime.ExecutorBrowserTransport(
            executor_name="EXEC_BROWSER", render_callable=lambda u: {"content": oversized}
        )
        result = adapter.fetch(
            PUBLIC_URL, target_authorized=True, controlled_test_environment=True
        )
        with self.assertRaises(runtime.CaptureTransportError) as context:
            runtime.normalize_capture(result, make_scope())
        self.assertIn(runtime.CAPTURE_SIZE_LIMIT_EXCEEDED, str(context.exception))
        with self.assertRaises(runtime.CaptureTransportError) as policy_context:
            runtime.capture_with_policy(
                PUBLIC_URL,
                make_scope(),
                [adapter],
                target_authorized=True,
                controlled_test_environment=True,
            )
        self.assertIn(runtime.CAPTURE_SIZE_LIMIT_EXCEEDED, str(policy_context.exception))

    def test_33_oversized_recorded_result_rejected(self) -> None:
        for content in (
            b"r" * (runtime.MAX_CAPTURE_BYTES + 1),
            "r" * (runtime.MAX_CAPTURE_BYTES + 1),
        ):
            with self.subTest(kind=type(content).__name__):
                with self.assertRaises(runtime.CaptureTransportError) as context:
                    runtime.normalize_capture(
                        runtime.TransportResult(
                            requested_url=PUBLIC_URL,
                            content=content,
                            transport_kind=runtime.RECORDED_RESULT,
                            representation=runtime.TEXT_CAPTURE,
                            executor="RECORDED",
                        ),
                        make_scope(),
                    )
                self.assertIn(runtime.CAPTURE_SIZE_LIMIT_EXCEEDED, str(context.exception))

    def test_34_small_payload_stays_deterministic_and_ceiling_is_inclusive(self) -> None:
        scope = make_scope()
        small = "Noi dung cong khai nho"
        result = runtime.TransportResult(
            requested_url=PUBLIC_URL,
            content=small,
            transport_kind=runtime.EXECUTOR_TEXT,
            representation=runtime.TEXT_CAPTURE,
            executor="EXEC",
        )
        first = runtime.normalize_capture(result, scope)
        second = runtime.normalize_capture(result, scope)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.byte_count, len(small.encode("utf-8")))
        self.assertEqual(first.char_count, len(small))
        # Exactly at the ceiling is accepted; one byte over is refused.
        at_limit = runtime.normalize_capture(
            runtime.TransportResult(
                requested_url=PUBLIC_URL,
                content=b"a" * runtime.MAX_CAPTURE_BYTES,
                transport_kind=runtime.PLAIN_HTTP,
                representation=runtime.RAW_BYTES,
                executor="E",
            ),
            scope,
        )
        self.assertEqual(at_limit.byte_count, runtime.MAX_CAPTURE_BYTES)
        with self.assertRaises(runtime.CaptureTransportError) as context:
            runtime.normalize_capture(
                runtime.TransportResult(
                    requested_url=PUBLIC_URL,
                    content=b"a" * (runtime.MAX_CAPTURE_BYTES + 1),
                    transport_kind=runtime.PLAIN_HTTP,
                    representation=runtime.RAW_BYTES,
                    executor="E",
                ),
                scope,
            )
        self.assertIn(runtime.CAPTURE_SIZE_LIMIT_EXCEEDED, str(context.exception))

    def test_35_public_literal_hosts_are_accepted_by_validation(self) -> None:
        # Public literal addresses and public DNS names remain usable; only
        # non-public targets fail closed.
        for url in (
            f"https://{PUBLIC_DNS_IPV4}/web/guest/x",
            f"https://[{PUBLIC_DNS_IPV6}]/web/guest/x",
            PUBLIC_URL,
        ):
            with self.subTest(url=url):
                self.assertEqual(runtime.validate_public_url(url), url)
                self.assertTrue(runtime._host_is_public_literal(
                    runtime.urllib.parse.urlsplit(url).hostname or ""
                ))
        for address in NON_PUBLIC_IPV4 + NON_PUBLIC_IPV6:
            self.assertFalse(runtime._host_is_public_literal(address))


if __name__ == "__main__":
    unittest.main()
