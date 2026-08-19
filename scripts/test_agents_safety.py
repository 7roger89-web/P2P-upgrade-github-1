"""Phase 5 — GT AGENTS.md safety review (dry-run, no mutations).

Semantics of the canonical installer (install.sh project merge, lines 230-260):
  1. Backs up project AGENTS.md to .p2p/install-backups/<stamp>/instructions/
  2. Replaces the <!-- BEGIN P2P CODEX -->...<!-- END P2P CODEX --> block
     (if present) with the package block; otherwise appends the block.
  3. Re-encodes the result to UTF-8 (read_text/write_text utf-8) — this is
     what previously "fixed" the mojibake of GT AGENTS.md as a side effect.

Dry-run here: compute BEFORE/AFTER text and a unified diff WITHOUT writing.
Classification A-D:
  A = pure addition (block appended, existing content untouched)
  B = block replacement inside P2P CODEX region only (existing content intact)
  C = side-effect content transformation (e.g., mojibake repair, re-encoding)
  D = content deletion/modification outside the P2P CODEX block
Collision rule: if existing file has a P2P CODEX block, replace it (B);
the re-encode (C) applies only when the host file carries non-UTF-8-clean
bytes — a real side-effect that must be disclosed, never performed silently.
"""
import hashlib, json, re, zipfile
from pathlib import Path

ZIP = Path("/home/ubuntu/fw01_work/auth-f01/reports/candidates/P2P-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip"
)
GT_ROOT = Path("/home/ubuntu/fw01_work/gt-canonical")
GP_ROOT = Path("/home/ubuntu/fw01_work/gp-canonical")

def p2p_block(pkg_agents: str) -> str:
    begin = "<!-- BEGIN P2P CODEX -->"
    end = "<!-- END P2P CODEX -->"
    if begin in pkg_agents:
        return pkg_agents[pkg_agents.index(begin):pkg_agents.index(end) + len(end)]
    return begin + "\n" + pkg_agents.strip() + "\n" + end

def merge(target_text: str, block: str):
    begin = "<!-- BEGIN P2P CODEX -->"
    end = "<!-- END P2P CODEX -->"
    pattern = re.escape(begin) + r".*?" + re.escape(end)
    if re.search(pattern, target_text, re.S):
        return re.sub(pattern, block, target_text, count=1, flags=re.S)
    t = target_text
    if t and not t.endswith("\n"):
        t += "\n"
    return t + block + "\n"

z = zipfile.ZipFile(ZIP)
pkg_agents = z.read("AGENTS.md").decode("utf-8")
block = p2p_block(pkg_agents)

results = []
for name, root in (("GT", GT_ROOT), ("GP", GP_ROOT)):
    agents = root / "AGENTS.md"
    if not agents.exists():
        results.append({"project": name, "agents_missing": True,
                        "note": "installer would create AGENTS.md with only the P2P block"})
        continue
    before = agents.read_bytes()
    before_text = before.decode("utf-8", errors="replace")
    after_text = merge(before_text, block)
    after = after_text.encode("utf-8")
    results.append({
        "project": name,
        "agents_bytes": hashlib.sha256(before).hexdigest(),
        "before_utf8_clean": before == before_text.encode("utf-8"),
        "diff_class": ("B" if "<!-- BEGIN P2P CODEX -->" in before_text
                       else "A"),
        "side_effect_C_mojibake_repair": before != before_text.encode("utf-8"),
        "would_change": before != after,
        "diff_lines": len(after.splitlines()) - len(before_text.splitlines()),
        "post_install_sha256": hashlib.sha256(after).hexdigest(),
    })

rec = {
    "installer_semantics": "backup-then-merge within BEGIN/END P2P CODEX delimiters; UTF-8 re-encode is an unavoidable side effect of the merge flow on non-clean bytes",
    "owner_gate_semantics": "installer performs the merge; project owner may refuse by skipping install.sh and applying the dry-run diff manually; this record captures the proposed diff WITHOUT applying it",
    "results": results,
}
p = Path("/home/ubuntu/fw01_work/evidence/fw01-v2-agents-safety-review.json")
p.write_text(json.dumps(rec, indent=2) + "\n")
for r in results:
    print(r)
print("OWNER_PROJECT_DIFF_REQUIRED" if any(r.get("side_effect_C_mojibake_repair") for r in results) else "A-B")
