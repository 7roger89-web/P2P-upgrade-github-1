#!/usr/bin/env python3
import copy
import json
import subprocess
import sys
from pathlib import Path

PIN = "1a5a78b513c0e7b46dfb29f74043bcf978c32a3e"
HERE = Path(__file__).resolve().parent
UPSTREAM = (HERE / "../../upstreams/liuyao-divination").resolve()

CORPUS_REPO = "Johnson-Jia/liuyao-divination"
CORPUS_SOURCE_PATH = "data/zhouyi.json"
CORPUS_OVERLAY_POLICY = "READ_TIME_OVERLAY_VENDOR_UNMODIFIED"

# Selected-text provenance vocabulary. These statuses distinguish pinned
# upstream bytes from P2P read-time overlays and keep external URLs as
# unverified reference pointers. They establish no critical edition.
SUPPORT_STATUS_RAW = "PINNED_UPSTREAM_TEXT_UNMODIFIED"
SUPPORT_STATUS_OVERLAY = "P2P_READ_TIME_OVERLAY"
REFERENCE_STATUS_NONE = "NONE"
REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED = "REFERENCE_POINTER_ONLY_UNVERIFIED"
CLAIM_RAW = "EMITTED_TEXT_EQUALS_PINNED_UPSTREAM_VALUE_AT_LOCATOR"
CLAIM_OVERLAY = "EMITTED_TEXT_EQUALS_P2P_READ_TIME_OVERLAY_RESULT_OVER_PINNED_UPSTREAM"


class YijingTextEvidenceError(RuntimeError):
    """A selected-text evidence entry failed fail-closed production validation."""


CORRECTIONS = {
    "地山谦": {
        "remove": {"六三": "呜谦，贞吉。"},
        "set": {"六二": "鸣谦，贞吉。"},
        "sources": [
            "https://zh.wikisource.org/zh-hant/周易正義/02謙",
            "https://ctext.org/wiki.pl?chapter=116177&if=gb",
        ],
        "reason": "Pinned JSON mislabels the second yin line as 六三 and OCRs 鸣 as 呜.",
    },
    "地水师": {
        "set": {"六四": "师左次，无咎。"},
        "sources": [
            "https://zh.wikisource.org/wiki/周易正義/02師",
            "https://ctext.org/wiki.pl?chapter=206625&if=gb",
        ],
        "reason": "Pinned JSON omits the fourth yin line.",
    },
}


def verify_pin():
    if not UPSTREAM.exists():
        raise RuntimeError(f"Pinned upstream missing: {UPSTREAM}")
    head = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    if head != PIN:
        raise RuntimeError(f"Pinned upstream SHA mismatch: expected {PIN}, got {head}")


def load_raw_corpus():
    verify_pin()
    return json.loads((UPSTREAM / "data" / "zhouyi.json").read_text(encoding="utf-8"))


def load_corrected_corpus():
    corpus = copy.deepcopy(load_raw_corpus())
    for hexagram, patch in CORRECTIONS.items():
        yao = corpus[hexagram]["yao"]
        for label, expected_text in patch.get("remove", {}).items():
            actual = yao.get(label)
            if actual != expected_text:
                raise RuntimeError(
                    f"Upstream correction precondition drift for {hexagram} {label}: "
                    f"expected {expected_text!r}, got {actual!r}"
                )
            del yao[label]
        for label, text in patch.get("set", {}).items():
            if label in yao and yao[label] != text:
                raise RuntimeError(
                    f"Refusing to overwrite unexpected upstream text for {hexagram} {label}: {yao[label]!r}"
                )
            yao[label] = text
    return corpus


def source_metadata():
    return {
        "repo": CORPUS_REPO,
        "pin": PIN,
        "path": CORPUS_SOURCE_PATH,
        "overlay": CORRECTIONS,
        "policy": CORPUS_OVERLAY_POLICY,
    }


# ---------------------------------------------------------------------------
# Selected-text evidence: per-field provenance for corpus-bound emissions.
# Locators are resolved mechanically against the pinned RAW loaded JSON; the
# vendor file is never modified (READ_TIME_OVERLAY_VENDOR_UNMODIFIED).
# ---------------------------------------------------------------------------

_RAW_CORPUS_CACHE = None


def _raw_corpus_cached():
    global _RAW_CORPUS_CACHE
    if _RAW_CORPUS_CACHE is None:
        _RAW_CORPUS_CACHE = load_raw_corpus()
    return _RAW_CORPUS_CACHE


def resolve_upstream_source_path(source_path):
    """Prove a pinned-upstream relative path exists and cannot escape upstream."""
    candidate = (UPSTREAM / source_path).resolve()
    try:
        candidate.relative_to(UPSTREAM)
    except ValueError:
        raise YijingTextEvidenceError(
            f"Source path escapes pinned upstream: {source_path!r}"
        )
    if not candidate.is_file():
        raise YijingTextEvidenceError(f"Pinned source file missing: {source_path!r}")
    return candidate


def resolve_corpus_locator(locator):
    """Resolve {hexagram, field[, label]} against the pinned RAW corpus bytes."""
    if not isinstance(locator, dict):
        raise YijingTextEvidenceError(f"Corpus locator must be a dict: {locator!r}")
    hexagram = locator.get("hexagram")
    field = locator.get("field")
    raw = _raw_corpus_cached()
    if hexagram not in raw:
        raise YijingTextEvidenceError(
            f"Corpus locator hexagram not in pinned source: {hexagram!r}"
        )
    if field == "gua_ci":
        return raw[hexagram].get("gua_ci")
    if field == "yao":
        return raw[hexagram].get("yao", {}).get(locator.get("label"))
    raise YijingTextEvidenceError(f"Unknown corpus locator field: {field!r}")


def corpus_overlay_id(hexagram, label):
    return f"YIJING_CORPUS_READ_TIME_OVERLAY:{hexagram}:{label}"


def corpus_overlay_action(hexagram):
    patch = CORRECTIONS.get(hexagram)
    if not patch:
        raise YijingTextEvidenceError(
            f"No corpus read-time overlay is defined for {hexagram!r}"
        )
    parts = [f"REMOVE_RAW_LABEL {label}" for label in patch.get("remove", {})]
    parts += [f"SET {label}" for label in patch.get("set", {})]
    return "; ".join(parts)


def corpus_overlay_result(hexagram, label):
    patch = CORRECTIONS.get(hexagram)
    if not patch or label not in patch.get("set", {}):
        raise YijingTextEvidenceError(
            f"No corpus read-time overlay defines a result for {hexagram!r} {label!r}"
        )
    return patch["set"][label]


def _corpus_evidence_common(field, hexagram, line_label, locator):
    return {
        "field": field,
        "hexagram": hexagram,
        "line_label": line_label,
        "repo": CORPUS_REPO,
        "pin": PIN,
        "source_path": CORPUS_SOURCE_PATH,
        "source_locator": locator,
    }


def gua_ci_evidence(hexagram, field="GUA_CI"):
    """Gua-ci text is always raw pinned corpus; no overlay touches gua_ci."""
    locator = {"hexagram": hexagram, "field": "gua_ci"}
    entry = _corpus_evidence_common(field, hexagram, None, locator)
    entry.update({
        "support_status": SUPPORT_STATUS_RAW,
        "overlay_applied": False,
        "overlay_id": None,
        "overlay_policy": None,
        "bounded_supported_claim": CLAIM_RAW,
        "external_reference_status": REFERENCE_STATUS_NONE,
    })
    return entry


def yao_text_evidence(hexagram, label, field="SELECTED_YAO[].text"):
    """Yao text evidence: raw pinned value, or the existing read-time overlay
    identity when (and only when) this exact line is overlay-corrected."""
    locator = {"hexagram": hexagram, "field": "yao", "label": label}
    entry = _corpus_evidence_common(field, hexagram, label, locator)
    patch = CORRECTIONS.get(hexagram)
    if patch and label in patch.get("set", {}):
        removes = patch.get("remove", {})
        if removes:
            raw_label = next(iter(removes))
            raw_text = removes[raw_label]
        else:
            raw_label, raw_text = label, None
        entry.update({
            "support_status": SUPPORT_STATUS_OVERLAY,
            "overlay_applied": True,
            "overlay_id": corpus_overlay_id(hexagram, label),
            "overlay_action": corpus_overlay_action(hexagram),
            "overlay_reason": patch["reason"],
            "overlay_policy": CORPUS_OVERLAY_POLICY,
            "overlay_precondition_passed": True,
            "raw_source_state": {"raw_label": raw_label, "raw_text": raw_text},
            "bounded_supported_claim": CLAIM_OVERLAY,
            "external_references": list(patch["sources"]),
            "external_reference_status": REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED,
        })
        return entry
    entry.update({
        "support_status": SUPPORT_STATUS_RAW,
        "overlay_applied": False,
        "overlay_id": None,
        "overlay_policy": None,
        "bounded_supported_claim": CLAIM_RAW,
        "external_reference_status": REFERENCE_STATUS_NONE,
    })
    return entry


def validate_corpus_evidence(entry, emitted_text):
    """Fail closed unless this entry truthfully supports emitted_text from the
    pinned raw corpus at data/zhouyi.json, or from its declared read-time overlay."""
    if not isinstance(entry, dict):
        raise YijingTextEvidenceError("Corpus evidence entry must be a dict")
    if entry.get("repo") != CORPUS_REPO:
        raise YijingTextEvidenceError(
            f"Corpus evidence repo mismatch: {entry.get('repo')!r}"
        )
    if entry.get("pin") != PIN:
        raise YijingTextEvidenceError(f"Corpus evidence pin mismatch: {entry.get('pin')!r}")
    if entry.get("source_path") != CORPUS_SOURCE_PATH:
        raise YijingTextEvidenceError(
            "Corpus evidence source path is not the sanctioned pinned corpus "
            f"surface {CORPUS_SOURCE_PATH!r}: {entry.get('source_path')!r}"
        )
    resolve_upstream_source_path(entry["source_path"])
    overlay_applied = entry.get("overlay_applied")
    if overlay_applied not in (True, False):
        raise YijingTextEvidenceError(
            f"Corpus evidence overlay_applied must be boolean: {overlay_applied!r}"
        )
    locator = entry.get("source_locator")
    if not isinstance(locator, dict) or locator.get("hexagram") != entry.get("hexagram"):
        raise YijingTextEvidenceError(
            f"Corpus evidence locator does not match its hexagram: {locator!r}"
        )
    raw = _raw_corpus_cached()

    if not overlay_applied:
        if entry.get("support_status") != SUPPORT_STATUS_RAW:
            raise YijingTextEvidenceError(
                f"Unoverlayed corpus evidence must claim {SUPPORT_STATUS_RAW}: "
                f"{entry.get('support_status')!r}"
            )
        if entry.get("overlay_id") is not None or entry.get("overlay_policy") is not None:
            raise YijingTextEvidenceError(
                "Raw corpus evidence must not carry overlay identity"
            )
        if entry.get("bounded_supported_claim") != CLAIM_RAW:
            raise YijingTextEvidenceError(
                f"Raw corpus evidence claim mismatch: {entry.get('bounded_supported_claim')!r}"
            )
        if entry.get("external_reference_status") != REFERENCE_STATUS_NONE:
            raise YijingTextEvidenceError(
                "Raw corpus evidence must not cite external references: "
                f"{entry.get('external_reference_status')!r}"
            )
        resolved = resolve_corpus_locator(locator)
        if resolved != emitted_text:
            raise YijingTextEvidenceError(
                f"Raw corpus value mismatch at {locator!r}: pinned={resolved!r}, emitted={emitted_text!r}"
            )
        return True

    # Overlay path: the claim is that emitted_text equals the existing overlay
    # result applied over the pinned raw defect state, nothing more.
    if entry.get("support_status") != SUPPORT_STATUS_OVERLAY:
        raise YijingTextEvidenceError(
            f"Overlay corpus evidence must claim {SUPPORT_STATUS_OVERLAY}: "
            f"{entry.get('support_status')!r}"
        )
    hexagram = entry["hexagram"]
    label = locator.get("label")
    if locator.get("field") != "yao":
        raise YijingTextEvidenceError(
            f"Corpus read-time overlays cover yao fields only: {locator!r}"
        )
    patch = CORRECTIONS.get(hexagram)
    if not patch or label not in patch.get("set", {}):
        raise YijingTextEvidenceError(
            f"No corpus read-time overlay defines {hexagram!r} {label!r}"
        )
    if entry.get("overlay_id") != corpus_overlay_id(hexagram, label):
        raise YijingTextEvidenceError(
            f"Corpus overlay identity mismatch: {entry.get('overlay_id')!r}"
        )
    if entry.get("overlay_action") != corpus_overlay_action(hexagram):
        raise YijingTextEvidenceError(
            f"Corpus overlay action mismatch: {entry.get('overlay_action')!r}"
        )
    if entry.get("overlay_reason") != patch["reason"]:
        raise YijingTextEvidenceError(
            f"Corpus overlay reason mismatch: {entry.get('overlay_reason')!r}"
        )
    if entry.get("overlay_policy") != CORPUS_OVERLAY_POLICY:
        raise YijingTextEvidenceError(
            f"Corpus overlay policy mismatch: {entry.get('overlay_policy')!r}"
        )
    if entry.get("overlay_precondition_passed") is not True:
        raise YijingTextEvidenceError("Corpus overlay preconditions not asserted as passed")
    # Re-prove the overlay preconditions against the pinned raw bytes now.
    raw_yao = raw[hexagram]["yao"]
    for raw_label, defect_text in patch.get("remove", {}).items():
        if raw_yao.get(raw_label) != defect_text:
            raise YijingTextEvidenceError(
                f"Corpus overlay precondition drift for {hexagram} {raw_label}: "
                f"expected {defect_text!r}, got {raw_yao.get(raw_label)!r}"
            )
    if label in raw_yao:
        raise YijingTextEvidenceError(
            f"Pinned raw source already contains {hexagram} {label}; "
            "read-time overlay claim is invalid"
        )
    if emitted_text != patch["set"][label]:
        raise YijingTextEvidenceError(
            f"Emitted text is not the declared overlay result for {hexagram} {label}: "
            f"expected {patch['set'][label]!r}, got {emitted_text!r}"
        )
    raw_state = entry.get("raw_source_state")
    removes = patch.get("remove", {})
    if not isinstance(raw_state, dict):
        raise YijingTextEvidenceError(
            f"Overlay corpus evidence requires a raw_source_state dict: {raw_state!r}"
        )
    if removes:
        raw_label = next(iter(removes))
        if raw_state.get("raw_label") != raw_label or raw_state.get("raw_text") != removes[raw_label]:
            raise YijingTextEvidenceError(
                f"Raw defect state mismatch for {hexagram} {label}: {raw_state!r}"
            )
    else:
        if raw_state.get("raw_label") != label or raw_state.get("raw_text") is not None:
            raise YijingTextEvidenceError(
                f"Raw defect state mismatch for {hexagram} {label}: {raw_state!r}"
            )
    if entry.get("external_references") != list(patch["sources"]):
        raise YijingTextEvidenceError(
            f"External reference pointers mismatch for {hexagram} {label}"
        )
    if entry.get("external_reference_status") != REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED:
        raise YijingTextEvidenceError(
            "External references must remain "
            f"{REFERENCE_STATUS_POINTER_ONLY_UNVERIFIED}, not "
            f"{entry.get('external_reference_status')!r}"
        )
    if entry.get("bounded_supported_claim") != CLAIM_OVERLAY:
        raise YijingTextEvidenceError(
            f"Overlay corpus evidence claim mismatch: {entry.get('bounded_supported_claim')!r}"
        )
    return True
