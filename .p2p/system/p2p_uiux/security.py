"""High-confidence secret scanning for package and install surfaces."""

import re
from pathlib import Path


SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    # Documentation commonly uses an all-``x`` placeholder. Keep the scan
    # high-confidence without weakening detection of real GitHub tokens.
    ("github-token", re.compile(r"\bgh[pousr]_(?!x{20,}\b)[A-Za-z0-9_]{20,}\b")),
    ("openai-style-token", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("credential-assignment", re.compile(r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*[\"'][^\"']{16,}[\"']")),
)
TEXT_SUFFIXES = {".py", ".toml", ".json", ".md", ".txt", ".yaml", ".yml", ".ini", ".cfg", ".env"}


def scan_text(text, source="<memory>"):
    findings = []
    for label, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append({"type": label, "source": str(source), "line": line})
    return findings


def scan_tree(root):
    root = Path(root)
    findings = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in {".git", "__pycache__", ".pytest_cache", "dist"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(text, path))
    return findings
