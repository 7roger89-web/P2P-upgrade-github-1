"""Focused tests for the generic public-web capture runtime (Issue #241).

Covers the acceptance surface: the normalized capture contract, single-URL
capture over both a plain-HTTP transport (loopback fixture) and an
executor-native text transport, bounded pagination plans, discovered-link
follow-up with provenance, checkpoint/resume metadata, determinism, honest
null HTTP metadata, fail-closed behaviour for unauthorized/out-of-scope/
unbounded/enumeration-shaped plans, unchanged router/quorum/registry, and
installed-runtime projection parity. Fully offline: the only network use is a
local loopback HTTP fixture; no live external site is contacted here (the
bounded live multi-site proof lives in
``evidence/p2p-web-capture-runtime-01/``).
"""

from __future__ import annotations

import hashlib
import http.server
import importlib.util
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
PACKAGE_RELEASE = REPO_ROOT / "scripts" / "package_release.py"
sys.path.insert(0, str(SYSTEM_ROOT))

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


class _LoopbackHandler(http.server.BaseHTTPRequestHandler):
    payload = b"<html><body>congbao-fixture</body></html>"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path != "/page.html":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(self.payload)))
        self.end_headers()
        self.wfile.write(self.payload)

    def log_message(self, *args) -> None:  # silence stderr noise
        pass


class LoopbackHttpFixture:
    def __init__(self) -> None:
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _LoopbackHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


class P2PWebCaptureRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.loopback = LoopbackHttpFixture()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.loopback.stop()

    # -- GENERIC_CAPTURE_CONTRACT -------------------------------------------

    def test_01_generic_capture_contract_is_complete_and_deterministic(self) -> None:
        scope = make_scope()
        result = runtime.TransportResult(
            requested_url="https://example.test/web/guest/van-ban",
            content="Xin chao",
            transport_kind=runtime.EXECUTOR_TEXT,
            representation=runtime.TEXT_CAPTURE,
            executor="TEST_EXECUTOR",
            retrieved_at="2026-09-23T02:20:00Z",
            final_url="https://example.test/web/guest/van-ban",
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

    def test_03_single_url_capture_over_plain_http_loopback(self) -> None:
        scope = make_scope(
            scope_id="LOOPBACK",
            allowed_host="127.0.0.1",
            allowed_path_prefixes=("/",),
        )
        url = f"{self.loopback.base_url}/page.html"
        adapter = runtime.PlainHttpTransport(timeout_seconds=5.0)
        capture = runtime.capture_with_policy(url, scope, [adapter], authorized=True)
        record = capture.record
        self.assertEqual(record.transport_kind, runtime.PLAIN_HTTP)
        self.assertEqual(record.representation, runtime.RAW_BYTES)
        self.assertEqual(record.http_status, 200)  # observed, not invented
        self.assertIn("text/html", record.content_type or "")
        self.assertEqual(record.final_url, url)
        self.assertEqual(capture.content, _LoopbackHandler.payload)
        self.assertEqual(
            record.sha256, hashlib.sha256(_LoopbackHandler.payload).hexdigest()
        )
        # Fail closed without explicit live authorization.
        with self.assertRaises(runtime.CaptureTransportError) as context:
            runtime.capture_with_policy(url, scope, [adapter], authorized=False)
        self.assertIn("NO_AVAILABLE_TRANSPORT_FOR_URL", str(context.exception))
        with self.assertRaises(runtime.CaptureAuthorizationError):
            adapter.fetch(url, authorized=False)

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
            "https://example.test/web/guest/van-ban", scope, [adapter]
        )
        self.assertEqual(calls, ["https://example.test/web/guest/van-ban"])
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
        scope = make_scope(
            scope_id="LOOPBACK", allowed_host="127.0.0.1", allowed_path_prefixes=("/",)
        )
        url = f"{self.loopback.base_url}/page.html"
        plain = runtime.PlainHttpTransport(timeout_seconds=5.0)
        executor_calls: list[str] = []
        executor = runtime.ExecutorTextTransport(
            executor_name="EXEC",
            fetch_callable=lambda u: (executor_calls.append(u), {"content": "text"})[1],
        )
        # Adapters supplied out of order: policy still tries plain HTTP first.
        capture = runtime.capture_with_policy(
            url, scope, [executor, plain], authorized=True
        )
        self.assertEqual(capture.record.transport_kind, runtime.PLAIN_HTTP)
        self.assertEqual(executor_calls, [])  # cheaper lane worked; no escalation

        # Without authorization, plain HTTP yields to the executor text lane.
        capture = runtime.capture_with_policy(url, scope, [executor, plain])
        self.assertEqual(capture.record.transport_kind, runtime.EXECUTOR_TEXT)

        # The browser lane stays optional: missing entirely is fine, and an
        # unprovided browser adapter fails closed instead of launching one.
        browser = runtime.ExecutorBrowserTransport()
        with self.assertRaises(runtime.CaptureTransportError) as context:
            browser.fetch("https://example.test/web/guest/van-ban")
        self.assertIn("BROWSER_ADAPTER_NOT_PROVIDED", str(context.exception))
        with self.assertRaises(runtime.CaptureTransportError):
            runtime.capture_with_policy(
                "https://example.test/web/guest/van-ban", scope, [browser]
            )

        # An executor-provided browser document normalizes as BROWSER_DOCUMENT.
        provided = runtime.ExecutorBrowserTransport(
            executor_name="EXEC_BROWSER",
            render_callable=lambda u: {"content": "<html>rendered</html>", "url": u},
        )
        capture = runtime.capture_with_policy(
            "https://example.test/web/guest/van-ban", make_scope(), [provided]
        )
        self.assertEqual(capture.record.representation, runtime.BROWSER_DOCUMENT)
        self.assertEqual(capture.record.transport_kind, runtime.EXECUTOR_BROWSER)

    # -- BOUNDED_PAGINATION_PLAN ---------------------------------------------

    def test_06_bounded_pagination_plan_is_explicit_and_deterministic(self) -> None:
        scope = make_scope()
        seed = "https://example.test/web/guest/van-ban"
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
        seed = "https://example.test/web/guest/van-ban"
        page2 = "https://example.test/web/guest/van-ban?delta=10&cur=2"
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
                    requested_url="https://example.test/web/guest/van-ban",
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
        seed = "https://example.test/web/guest/van-ban"
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
                    requested_url="https://example.test/web/guest/van-ban",
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
            self.assertEqual(
                hashlib.sha256(stored).hexdigest(), record.sha256
            )
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


if __name__ == "__main__":
    unittest.main()
