#!/usr/bin/env python3
import copy
import json
import subprocess
import sys
from pathlib import Path

PIN = "1a5a78b513c0e7b46dfb29f74043bcf978c32a3e"
HERE = Path(__file__).resolve().parent
UPSTREAM = (HERE / "../../upstreams/liuyao-divination").resolve()

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
        "repo": "Johnson-Jia/liuyao-divination",
        "pin": PIN,
        "path": "data/zhouyi.json",
        "overlay": CORRECTIONS,
        "policy": "READ_TIME_OVERLAY_VENDOR_UNMODIFIED",
    }
