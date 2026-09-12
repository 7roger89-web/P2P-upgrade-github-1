#!/usr/bin/env python3
"""Static contract check for the thin P2P installed-agent entry point."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THIN = ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
INSTALL_PS1 = ROOT / "install.ps1"
INSTALL_SH = ROOT / "install.sh"
MANIFEST = ROOT / ".agents" / "skills" / ".agents-skill-manifest.json"
MAX_THIN_BYTES = 9_000


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def require_all(errors: list[str], text: str, phrases: list[str], subject: str) -> None:
    for phrase in phrases:
        if phrase not in text:
            fail(errors, f"{subject}: missing required phrase: {phrase!r}")


def main() -> int:
    errors: list[str] = []

    for path in (THIN, INSTALL_PS1, INSTALL_SH, MANIFEST):
        if not path.is_file():
            fail(errors, f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    thin = THIN.read_text(encoding="utf-8")
    ps1 = INSTALL_PS1.read_text(encoding="utf-8")
    sh = INSTALL_SH.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")

    thin_bytes = len(thin.encode("utf-8"))
    if thin_bytes > MAX_THIN_BYTES:
        fail(
            errors,
            f"thin instruction block is {thin_bytes} bytes; cap is {MAX_THIN_BYTES}",
        )

    require_all(
        errors,
        thin,
        [
            "P2P_SUPREME_OPERATING_LAW_V1",
            "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md",
            "TASK_BRANCH != LAW_AUTHORITY",
            "TARGET_PROJECT != LAW_SOURCE",
            "LAW_CONTEXT_BLOCKED",
            "Evidence comes before",
            "stop when acceptance evidence is sufficient",
            "## Owner gates",
            "merge or promotion",
            "production deployment or release",
            "destructive or hard-to-reverse",
            "secrets/credentials",
            "paid spending",
            "infrastructure",
            "hard rollback",
            "## Progressive disclosure",
            ".agents/skills/p2p/SKILL.md",
            ".agents/skills/p2p-idea/SKILL.md",
            ".agents/skills/p2p-uiux/SKILL.md",
            ".agents/skills/p2p-quorum/SKILL.md",
            "Verification is proportional",
            "Không bị over engineering chứ?",
            "Có cách đơn giản hơn đạt cùng mục tiêu không?",
            "Bước này có tạo thêm thông tin, capability, hoặc tiến triển đáng kể không?",
            "Nếu bỏ bước này, điều kiện thành công có thực sự bị thiếu không?",
            "Chúng ta đang giải capability chính hay đang tối ưu hạ tầng phụ trước capability?",
            "slice nhỏ hơn nhưng vẫn kiểm chứng độc lập",
            "Before delegating to another model or executor",
        ],
        "P2P-AGENTS-INSTALL.md",
    )

    forbidden_thin = [
        "<!-- anvien:start -->",
        "# Anvien - Code Intelligence",
        "## Skill Selection Guide",
        "## Real-agent QUORUM",
    ]
    for phrase in forbidden_thin:
        if phrase in thin:
            fail(errors, f"thin entry point contains deferred/generated material: {phrase!r}")

    thin_rel_posix = "docs/p2p-development/P2P-AGENTS-INSTALL.md"
    thin_rel_windows = "docs\\p2p-development\\P2P-AGENTS-INSTALL.md"
    if thin_rel_windows not in ps1:
        fail(errors, "install.ps1 does not inject the thin instruction source")
    if thin_rel_posix not in sh:
        fail(errors, "install.sh does not inject the thin instruction source")

    if 'Join-Path $PackageRoot "AGENTS.md"' in ps1:
        fail(errors, "install.ps1 still injects the full package AGENTS.md")
    if '"$package_root/AGENTS.md"' in sh:
        fail(errors, "install.sh still injects the full package AGENTS.md")

    require_all(
        errors,
        ps1,
        ['<!-- BEGIN P2P CODEX -->', '<!-- END P2P CODEX -->'],
        "install.ps1",
    )
    require_all(
        errors,
        sh,
        ['<!-- BEGIN P2P CODEX -->', '<!-- END P2P CODEX -->'],
        "install.sh",
    )

    if '"managedBy": "anvien"' not in manifest:
        fail(errors, "skill mirror ownership is no longer explicitly managed by Anvien")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("P2P_INSTRUCTION_CONTRACT=PASS")
    print(f"THIN_INSTRUCTION_BYTES={thin_bytes}")
    print("INSTALLER_SOURCE=docs/p2p-development/P2P-AGENTS-INSTALL.md")
    print("SKILL_MIRROR_OWNERSHIP=ANVIEN_MANAGED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
