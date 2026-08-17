#!/usr/bin/env python3
"""Append the §3f C31 section to current-roadmap.md (idempotent, append-only)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROADMAP = ROOT / "docs/p2p-development/current-roadmap.md"

SECTION = """
### 3f. C31 live host certification — honest BLOCKED (2026-08-17)

C31 attempted to close the highest-priority evidence gap left after C30: an honest **live** certification of one real execution path using the generic C30 execution-target contract and the existing C27/C28 machinery (no parallel certification system, no vendor-specific core). The environment was inspected from observable evidence only: Codex CLI 0.147.0 is installed; the sandbox `OPENAI_API_KEY` is a Manus proxy credential; **no** Manus project connector is enabled; Claude/Gemini/Cursor/Copilot are absent (confirming C27 evidence). A fresh, non-destructive, zero-model-contact probe (`evidence/c31_live_probe.json`, fingerprint `5e3364ee…854b`) reached Codex's own auth layer and returned **HTTP 401 Unauthorized before model contact** — verdict `AUTH_INVALID`. The Manus connector path is `AUTH_CONFIG_ABSENT`. Terminal verdict: **BLOCKED / OWNER_ACTION_REQUIRED**. The smallest owner actions are a real `codex login` (outside chat, no secrets in chat) or enabling the Manus project connector in session configuration; certification reopens only when a fresh probe returns `AUTH_REQUIRED` or stronger on a supported host. Per the honesty boundary, no live certification record was fabricated: ledger and governance carry only the honest BLOCKED state, and no candidate release artifact was minted (`NOT_APPLICABLE_BLOCKED`). `AUTHENTICATED != CERTIFIED`; `UNKNOWN != SUPPORTED`; `GOAL PASS != PROMOTION`.
"""


def main() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    marker = "### 3f. C31 live host certification"
    if marker in text:
        print("C31 section already present; nothing to do")
        return
    text = text.rstrip() + "\n" + SECTION
    ROADMAP.write_text(text, encoding="utf-8")
    print("§3f C31 section appended")


if __name__ == "__main__":
    main()
