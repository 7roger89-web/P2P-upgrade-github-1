"""Structural validation for a ``document.marker.convert`` result bundle.

V1 execution model is INTERACTIVE_COLAB: the Owner runs
``marker_convert_colab.ipynb`` in Google Colab, downloads one ZIP, and this
module validates that ZIP offline. Pure stdlib, no network, no Marker/Torch.

Bundle contract (``p2p-document-marker-convert-bundle/1``)::

    source/original.pdf
    output/document.md
    output/images/*          (optional)
    manifest.json
    quality.json
    page_flags.json
    run.json

Deliberate non-goals: this module does not convert PDFs, does not judge
Markdown semantic quality, and does not verify diagram meaning. Page flags are
accepted only as observable evidence (booleans + counts), and pages flagged
``needs_visual_qa`` are surfaced for a human, never auto-resolved.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

BUNDLE_SCHEMA = "p2p-document-marker-convert-bundle/1"
CAPABILITY_ID = "document.marker.convert"

SOURCE_PATH = "source/original.pdf"
MARKDOWN_PATH = "output/document.md"
IMAGES_PREFIX = "output/images/"
MANIFEST_PATH = "manifest.json"
QUALITY_PATH = "quality.json"
PAGE_FLAGS_PATH = "page_flags.json"
RUN_PATH = "run.json"

REQUIRED_MEMBERS = (SOURCE_PATH, MARKDOWN_PATH, MANIFEST_PATH, QUALITY_PATH, PAGE_FLAGS_PATH, RUN_PATH)
JSON_MEMBERS = (MANIFEST_PATH, QUALITY_PATH, PAGE_FLAGS_PATH, RUN_PATH)

REQUIRED_MANIFEST_KEYS = (
    "schema",
    "capability_id",
    "created_at",
    "source",
    "marker",
    "environment",
    "sampling",
    "ocr_used",
    "vlm_used",
    "outputs",
)
REQUIRED_SOURCE_KEYS = ("original_filename", "stored_path", "sha256", "size_bytes", "page_count")
REQUIRED_SAMPLING_KEYS = ("full_conversion", "sample_pages", "rule")
REQUIRED_PAGE_FLAG_KEYS = (
    "page",
    "has_images",
    "possible_diagram",
    "possible_table",
    "ocr_used",
    "needs_visual_qa",
)

# Only OUR pipeline metadata is scanned (the four JSON files). document.md is
# user content and is intentionally not scanned here.
_SECRET_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\"private_key\"\s*:"),
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class MarkerBundleError(ValueError):
    """Raised when a bundle violates the V1 contract. Message is a stable code."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json(zf: zipfile.ZipFile, member: str) -> Any:
    try:
        parsed = json.loads(zf.read(member).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MarkerBundleError(f"JSON_INVALID:{member}") from exc
    if not isinstance(parsed, dict):
        raise MarkerBundleError(f"JSON_ROOT_INVALID:{member}")
    return parsed


def _require_keys(obj: dict[str, Any], keys: tuple[str, ...], where: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise MarkerBundleError(f"MISSING_KEYS:{where}:{','.join(missing)}")


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def validate_bundle(path: str | Path) -> dict[str, Any]:
    """Validate a bundle ZIP. Returns a summary dict or raises MarkerBundleError."""
    path = Path(path)
    if not path.is_file():
        raise MarkerBundleError("BUNDLE_NOT_FOUND")
    if not zipfile.is_zipfile(path):
        raise MarkerBundleError("BUNDLE_NOT_ZIP")

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        for name in names:
            if name.startswith("/") or ".." in Path(name).parts:
                raise MarkerBundleError(f"UNSAFE_MEMBER_PATH:{name}")
        missing = [m for m in REQUIRED_MEMBERS if m not in names]
        if missing:
            raise MarkerBundleError(f"MISSING_MEMBERS:{','.join(missing)}")

        # --- source preservation ---------------------------------------
        source_bytes = zf.read(SOURCE_PATH)
        if not source_bytes.startswith(b"%PDF-"):
            raise MarkerBundleError("SOURCE_NOT_PDF")
        source_sha = sha256_bytes(source_bytes)

        # --- markdown --------------------------------------------------
        markdown_bytes = zf.read(MARKDOWN_PATH)
        if not markdown_bytes.strip():
            raise MarkerBundleError("MARKDOWN_EMPTY")

        # --- JSON parse + secret scan of our own metadata --------------
        docs = {m: _load_json(zf, m) for m in JSON_MEMBERS}
        for member in JSON_MEMBERS:
            raw = zf.read(member).decode("utf-8", errors="replace")
            for pattern in _SECRET_PATTERNS:
                if pattern.search(raw):
                    raise MarkerBundleError(f"SECRET_LIKE_MATERIAL:{member}")

        manifest = docs[MANIFEST_PATH]
        _require_keys(manifest, REQUIRED_MANIFEST_KEYS, "manifest")
        if manifest["schema"] != BUNDLE_SCHEMA:
            raise MarkerBundleError("MANIFEST_SCHEMA_MISMATCH")
        if manifest["capability_id"] != CAPABILITY_ID:
            raise MarkerBundleError("MANIFEST_CAPABILITY_MISMATCH")

        source = manifest["source"]
        if not isinstance(source, dict):
            raise MarkerBundleError("MANIFEST_SOURCE_INVALID")
        _require_keys(source, REQUIRED_SOURCE_KEYS, "manifest.source")
        if source["stored_path"] != SOURCE_PATH:
            raise MarkerBundleError("SOURCE_PATH_MISMATCH")
        if not (isinstance(source["sha256"], str) and _SHA256_RE.match(source["sha256"])):
            raise MarkerBundleError("SOURCE_SHA256_MALFORMED")
        if source["sha256"] != source_sha:
            raise MarkerBundleError("SOURCE_SHA256_MISMATCH")
        if source["size_bytes"] != len(source_bytes):
            raise MarkerBundleError("SOURCE_SIZE_MISMATCH")
        page_count = source["page_count"]
        if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
            raise MarkerBundleError("SOURCE_PAGE_COUNT_INVALID")

        marker = manifest["marker"]
        if not isinstance(marker, dict) or not str(marker.get("version", "")).strip():
            raise MarkerBundleError("MARKER_VERSION_MISSING")
        if not isinstance(manifest["environment"], dict):
            raise MarkerBundleError("ENVIRONMENT_INVALID")
        if not _is_bool(manifest["ocr_used"]) or not _is_bool(manifest["vlm_used"]):
            raise MarkerBundleError("OCR_VLM_FLAGS_NOT_BOOL")

        sampling = manifest["sampling"]
        if not isinstance(sampling, dict):
            raise MarkerBundleError("SAMPLING_INVALID")
        _require_keys(sampling, REQUIRED_SAMPLING_KEYS, "manifest.sampling")
        if not _is_bool(sampling["full_conversion"]):
            raise MarkerBundleError("SAMPLING_FULL_CONVERSION_NOT_BOOL")
        sample_pages = sampling["sample_pages"]
        if not isinstance(sample_pages, list) or not sample_pages:
            raise MarkerBundleError("SAMPLING_PAGES_EMPTY")
        for p in sample_pages:
            if not isinstance(p, int) or isinstance(p, bool) or p < 1 or p > page_count:
                raise MarkerBundleError("SAMPLING_PAGE_OUT_OF_RANGE")
        if sampling["full_conversion"] and len(set(sample_pages)) != page_count:
            raise MarkerBundleError("SAMPLING_FULL_BUT_PARTIAL_PAGES")

        # --- outputs: every referenced file exists and hashes match ------
        outputs = manifest["outputs"]
        if not isinstance(outputs, list) or not outputs:
            raise MarkerBundleError("OUTPUTS_EMPTY")
        referenced: set[str] = set()
        for entry in outputs:
            if not isinstance(entry, dict) or "path" not in entry or "sha256" not in entry:
                raise MarkerBundleError("OUTPUT_ENTRY_INVALID")
            out_path = entry["path"]
            if out_path not in names:
                raise MarkerBundleError(f"OUTPUT_MISSING:{out_path}")
            if not (out_path == MARKDOWN_PATH or out_path.startswith(IMAGES_PREFIX)):
                raise MarkerBundleError(f"OUTPUT_PATH_OUTSIDE_CONTRACT:{out_path}")
            data = zf.read(out_path)
            if sha256_bytes(data) != entry["sha256"]:
                raise MarkerBundleError(f"OUTPUT_SHA256_MISMATCH:{out_path}")
            if "size_bytes" in entry and entry["size_bytes"] != len(data):
                raise MarkerBundleError(f"OUTPUT_SIZE_MISMATCH:{out_path}")
            referenced.add(out_path)
        if MARKDOWN_PATH not in referenced:
            raise MarkerBundleError("MARKDOWN_NOT_IN_MANIFEST")
        unreferenced_images = sorted(
            n for n in names if n.startswith(IMAGES_PREFIX) and not n.endswith("/") and n not in referenced
        )
        if unreferenced_images:
            raise MarkerBundleError(f"IMAGE_NOT_IN_MANIFEST:{unreferenced_images[0]}")

        # --- page flags: observable evidence only ------------------------
        flags_doc = docs[PAGE_FLAGS_PATH]
        pages = flags_doc.get("pages")
        if not isinstance(pages, list) or not pages:
            raise MarkerBundleError("PAGE_FLAGS_EMPTY")
        seen_pages: set[int] = set()
        for entry in pages:
            if not isinstance(entry, dict):
                raise MarkerBundleError("PAGE_FLAG_ENTRY_INVALID")
            _require_keys(entry, REQUIRED_PAGE_FLAG_KEYS, "page_flags.pages[]")
            page_no = entry["page"]
            if not isinstance(page_no, int) or isinstance(page_no, bool) or page_no < 1 or page_no > page_count:
                raise MarkerBundleError("PAGE_FLAG_PAGE_OUT_OF_RANGE")
            if page_no in seen_pages:
                raise MarkerBundleError("PAGE_FLAG_PAGE_DUPLICATE")
            seen_pages.add(page_no)
            for key in REQUIRED_PAGE_FLAG_KEYS[1:]:
                if not _is_bool(entry[key]):
                    raise MarkerBundleError(f"PAGE_FLAG_NOT_BOOL:{key}")
        if manifest["ocr_used"] != any(e["ocr_used"] for e in pages):
            raise MarkerBundleError("OCR_USED_INCONSISTENT")

        # --- quality + run ------------------------------------------------
        quality = docs[QUALITY_PATH]
        if quality.get("markdown_nonempty") is not True:
            raise MarkerBundleError("QUALITY_MARKDOWN_NONEMPTY_NOT_TRUE")
        run = docs[RUN_PATH]
        if run.get("status") != "PASS":
            raise MarkerBundleError("RUN_STATUS_NOT_PASS")
        if run.get("paid_spend", 0) != 0:
            raise MarkerBundleError("RUN_PAID_SPEND_NONZERO")

    return {
        "bundle": str(path),
        "schema": BUNDLE_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "source_sha256": source_sha,
        "source_page_count": page_count,
        "full_conversion": sampling["full_conversion"],
        "sample_pages": list(sample_pages),
        "ocr_used": manifest["ocr_used"],
        "vlm_used": manifest["vlm_used"],
        "markdown_bytes": len(markdown_bytes),
        "image_count": sum(1 for p in referenced if p.startswith(IMAGES_PREFIX)),
        "pages_needing_visual_qa": sorted(e["page"] for e in pages if e["needs_visual_qa"]),
        "gpu_used": bool(run.get("gpu_used", False)),
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: python -m p2p_capabilities.marker_bundle_validator <bundle.zip>", file=sys.stderr)
        return 2
    try:
        summary = validate_bundle(args[0])
    except MarkerBundleError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", **summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
