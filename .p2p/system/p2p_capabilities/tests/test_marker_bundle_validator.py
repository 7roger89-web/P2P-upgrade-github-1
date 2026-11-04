"""document.marker.convert — focused static tests.

  BUNDLE_CONTRACT_TESTED=YES   (synthetic in-repo bundle, stdlib only)
  NOTEBOOK_STATIC_CHECKED=YES  (JSON/nbformat, syntax, fail-closed + no-secret invariants)
  REAL_COLAB_MARKER_RUN=NO     (Marker/Surya/GPU execution is Owner-side interactive Colab)
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from p2p_capabilities import marker_bundle_validator as v  # noqa: E402

CAP_DIR = Path(__file__).resolve().parent.parent
NOTEBOOK = CAP_DIR / "marker_convert_colab.ipynb"
REPO_ROOT = CAP_DIR.parent.parent.parent
EXTERNAL_SOURCES = REPO_ROOT / "manifest" / "external-sources.json"

MINI_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def make_bundle(**overrides):
    """Build a valid bundle in memory; overrides mutate members before zipping."""
    md = b"# Title\n\nHello world.\n"
    img = b"\x89PNG\r\n\x1a\nfake"
    files = {
        "source/original.pdf": MINI_PDF,
        "output/document.md": md,
        "output/images/_page_0_Figure_1.png": img,
    }
    manifest = {
        "schema": v.BUNDLE_SCHEMA,
        "capability_id": v.CAPABILITY_ID,
        "created_at": "2026-09-07T00:00:00+00:00",
        "source": {
            "original_filename": "sample.pdf",
            "stored_path": "source/original.pdf",
            "sha256": _sha(MINI_PDF),
            "size_bytes": len(MINI_PDF),
            "page_count": 1,
        },
        "marker": {"version": "1.x-test"},
        "environment": {"runtime": "test", "gpu": "none"},
        "sampling": {"full_conversion": True, "sample_pages": [1], "rule": "FULL_UNDER_LIMIT"},
        "ocr_used": False,
        "vlm_used": False,
        "outputs": [
            {"path": "output/document.md", "sha256": _sha(md), "size_bytes": len(md)},
            {"path": "output/images/_page_0_Figure_1.png", "sha256": _sha(img), "size_bytes": len(img)},
        ],
    }
    page_flags = {
        "pages": [
            {
                "page": 1,
                "has_images": True,
                "possible_diagram": False,
                "possible_table": False,
                "ocr_used": False,
                "needs_visual_qa": True,
            }
        ]
    }
    docs = {
        "manifest.json": manifest,
        "quality.json": {"markdown_nonempty": True},
        "page_flags.json": page_flags,
        "run.json": {"status": "PASS", "paid_spend": 0, "gpu_used": True},
    }
    for key, fn in overrides.items():
        if key in docs:
            fn(docs[key])
        else:
            files[key] = fn(files.get(key))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            if data is not None:
                zf.writestr(name, data)
        for name, obj in docs.items():
            zf.writestr(name, json.dumps(obj))
    return buf.getvalue()


class BundleValidatorTests(unittest.TestCase):
    def _run(self, data: bytes):
        with TemporaryDirectory() as td:
            p = Path(td) / "b.zip"
            p.write_bytes(data)
            return v.validate_bundle(p)

    def _expect(self, code: str, data: bytes):
        with self.assertRaises(v.MarkerBundleError) as ctx:
            self._run(data)
        self.assertTrue(str(ctx.exception).startswith(code), f"{ctx.exception} !~ {code}")

    def test_valid_bundle_passes_with_summary(self):
        s = self._run(make_bundle())
        self.assertEqual(s["source_sha256"], _sha(MINI_PDF))
        self.assertEqual(s["image_count"], 1)
        self.assertEqual(s["pages_needing_visual_qa"], [1])
        self.assertTrue(s["full_conversion"])
        self.assertFalse(s["ocr_used"])

    def test_missing_required_member(self):
        self._expect("MISSING_MEMBERS", make_bundle(**{"output/document.md": lambda _: None}))

    def test_source_hash_mismatch(self):
        def tamper(m):
            m["source"]["sha256"] = "0" * 64
        self._expect("SOURCE_SHA256_MISMATCH", make_bundle(**{"manifest.json": tamper}))

    def test_source_replaced_is_detected(self):
        self._expect("SOURCE_SHA256_MISMATCH", make_bundle(**{"source/original.pdf": lambda _: MINI_PDF + b"x"}))

    def test_markdown_empty(self):
        self._expect("MARKDOWN_EMPTY", make_bundle(**{"output/document.md": lambda _: b"  \n"}))

    def test_output_hash_mismatch(self):
        self._expect("OUTPUT_SHA256_MISMATCH", make_bundle(**{"output/document.md": lambda _: b"# changed\n"}))

    def test_manifest_references_missing_output(self):
        def add(m):
            m["outputs"].append({"path": "output/images/ghost.png", "sha256": "0" * 64})
        self._expect("OUTPUT_MISSING", make_bundle(**{"manifest.json": add}))

    def test_unreferenced_image_rejected(self):
        self._expect("IMAGE_NOT_IN_MANIFEST", make_bundle(**{"output/images/extra.png": lambda _: b"x"}))

    def test_invalid_json(self):
        data = make_bundle()
        buf = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(data)) as src, zipfile.ZipFile(buf, "w") as dst:
            for n in src.namelist():
                dst.writestr(n, b"{not json" if n == "quality.json" else src.read(n))
        self._expect("JSON_INVALID:quality.json", buf.getvalue())

    def test_page_flag_out_of_range(self):
        def bad(pf):
            pf["pages"][0]["page"] = 2
        self._expect("PAGE_FLAG_PAGE_OUT_OF_RANGE", make_bundle(**{"page_flags.json": bad}))

    def test_page_flag_non_bool_rejected(self):
        def bad(pf):
            pf["pages"][0]["possible_diagram"] = "maybe"
        self._expect("PAGE_FLAG_NOT_BOOL", make_bundle(**{"page_flags.json": bad}))

    def test_ocr_flag_consistency(self):
        def bad(m):
            m["ocr_used"] = True
        self._expect("OCR_USED_INCONSISTENT", make_bundle(**{"manifest.json": bad}))

    def test_sample_page_out_of_range(self):
        def bad(m):
            m["sampling"]["sample_pages"] = [1, 5]
        self._expect("SAMPLING_PAGE_OUT_OF_RANGE", make_bundle(**{"manifest.json": bad}))

    def test_secret_like_metadata_rejected(self):
        def leak(r):
            r["token"] = "ghp_" + "A" * 36
        self._expect("SECRET_LIKE_MATERIAL:run.json", make_bundle(**{"run.json": leak}))

    def test_paid_spend_rejected(self):
        def paid(r):
            r["paid_spend"] = 1
        self._expect("RUN_PAID_SPEND_NONZERO", make_bundle(**{"run.json": paid}))

    def test_cli(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "b.zip"
            p.write_bytes(make_bundle())
            self.assertEqual(v.main([str(p)]), 0)
            p.write_bytes(b"nope")
            self.assertEqual(v.main([str(p)]), 1)


class NotebookStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cls.code = [
            "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
            for c in cls.nb["cells"]
            if c["cell_type"] == "code"
        ]
        cls.all_src = "\n".join(cls.code)

    def test_nbformat_and_gpu_metadata(self):
        self.assertEqual(self.nb["nbformat"], 4)
        self.assertEqual(self.nb["metadata"].get("accelerator"), "GPU")
        self.assertGreaterEqual(len(self.code), 6)

    def test_every_code_cell_is_valid_python(self):
        for i, src in enumerate(self.code):
            ast.parse("\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("!", "%"))))

    def test_gpu_fail_closed_before_install(self):
        gpu_idx = next(i for i, s in enumerate(self.code) if "GPU_UNAVAILABLE" in s)
        install_idx = next(i for i, s in enumerate(self.code) if "marker-pdf" in s and "pip" in s)
        self.assertLess(gpu_idx, install_idx)
        self.assertIn('raise SystemExit("GPU_UNAVAILABLE")', self.code[gpu_idx])
        self.assertIn("will NOT request a paid upgrade", self.code[gpu_idx])

    def test_no_credentials_or_forbidden_surfaces(self):
        for forbidden in (
            "drive.mount",
            "userdata.get",
            "GITHUB_TOKEN",
            "ghp_",
            "service_account",
            "openai",
            "anthropic",
            "gemini",
            "GOOGLE_API_KEY",
            "requests.post",
        ):
            self.assertNotIn(forbidden, self.all_src, forbidden)
        self.assertIn('"use_llm": False', self.all_src)
        self.assertIn('"vlm_used": False', self.all_src)

    def test_source_preservation_and_bundle_contract(self):
        self.assertIn('WORK / "source" / "original.pdf"', self.all_src)
        self.assertIn("hashlib.sha256(SOURCE_BYTES)", self.all_src)
        for member in v.REQUIRED_MEMBERS:
            self.assertIn(Path(member).name, self.all_src, member)
        self.assertIn(v.BUNDLE_SCHEMA, self.all_src)
        self.assertIn(v.CAPABILITY_ID, self.all_src)
        for key in v.REQUIRED_PAGE_FLAG_KEYS:
            self.assertIn(f'"{key}"', self.all_src, key)

    def test_sample_first_policy_and_ocr_gating(self):
        self.assertIn("FULL_CONVERSION_MAX_PAGES", self.all_src)
        self.assertIn("def sample_pages", self.all_src)
        self.assertIn('"disable_ocr": not OCR_REQUIRED', self.all_src)
        self.assertIn('"force_ocr": False', self.all_src)


class RegistrationTests(unittest.TestCase):
    def test_external_sources_registers_capability(self):
        data = json.loads(EXTERNAL_SOURCES.read_text(encoding="utf-8"))
        entries = [c for c in data["candidate_sources"] if c.get("capability_id") == v.CAPABILITY_ID]
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertTrue((REPO_ROOT / e["stored_path"]).is_file(), e["stored_path"])
        self.assertTrue((REPO_ROOT / e["validator_path"]).is_file(), e["validator_path"])
        self.assertEqual(e["execution_model"], "INTERACTIVE_COLAB")
        self.assertFalse(e["credentials"])
        self.assertEqual(e["paid_resources"], False)


if __name__ == "__main__":
    unittest.main()
