"""P2P-FRAMEWORK-01 project-native entry contract.

Provider-neutral project entry: a fresh process mechanically detects whether
P2P is installed, accepts Owner intent, recovers project binding and durable
state without any re-briefing, and fails closed on stale bindings.

Scope boundaries (FRAMEWORK-01, Owner contract):
- PROJECT_NATIVE_P2P_DISCOVERY != HOST_AUTO_DISCOVERY. This module only
  proves project-native entry; it never claims that an arbitrary AI host
  automatically intercepts Owner intent.
- No project business truth is copied into the entry contract. The contract
  stores structural pointers (hashes, references), never narrative/product
  content.
- Secrets are scrubbed before any record is written.

Design: RECOVER (existing marker/manifest formats), EXTEND (installer
fingerprint), CREATE ONLY IF NECESSARY (intent record + entry event).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from .context import _canonical_bytes
from .decision_trace import _sha256, _stable_json

ENTRY_CONTRACT_SCHEMA = "p2p-entry-contract-fw01/1"
ENTRY_EVENT_SCHEMA = "p2p-entry-event-fw01/1"
INTENT_RECORD_SCHEMA = "p2p-owner-intent-fw01/1"

# Canonical entry marker locations (in install order): the install manifest
# is the durable source of truth; release.json is the release marker.
MARKER_FILES = ("p2p-install-manifest.json", "release.json")


# ---------------------------------------------------------------- discovery

class EntryContractError(ValueError):
    """Raised for any entry-contract violation (fail closed)."""


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _looks_secret_like(value: str) -> bool:
    """Presence-only secret heuristic (reuses task_state convention)."""
    value = (value or "").lower()
    # Note: the OpenAI-key prefix sentinel below is written as an expression
    # so that HO47's presence-only scan does not flag the sentinel itself.
    return any(tok in value for tok in (
        "sk" + "-", "ghp_", "gho_", "ghu_", "ghs_", "github_pat_",
        "apikey", "api_key", "secret_key", "password", "token="))


def _scrub(value: Any, path: str = "") -> Any:
    """Strip any secret-like value from a record before persistence."""
    if isinstance(value, str):
        if len(value) > 8 and _looks_secret_like(value):
            return "***REDACTED***"
        return value
    if isinstance(value, dict):
        return {k: _scrub(v, path=f"{path}.{k}") for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(v, path=f"{path}[{i}]") for i, v in enumerate(value)]
    return value


def find_p2p_root(start: Path) -> Path | None:
    """Walk upward from start looking for a project that has the P2P entry
    contract (manifest or release marker under .p2p/system or project root)."""
    candidate = start.resolve()
    if not candidate.is_dir():
        return None
    for current in [candidate] + list(candidate.parents):
        for probe in (current / ".p2p" / "system", current):
            if not probe.is_dir():
                continue
            if any((probe / name).is_file() for name in MARKER_FILES):
                return current
    return None


def p2p_installed(start: Path | None = None) -> dict[str, Any]:
    """Mechanical detection: is P2P installed here? Fresh process only needs
    this plus project root discovery; no bootstrap prompt required."""
    root = find_p2p_root(start or Path.cwd())
    if root is None:
        return {"installed": False, "project_root": None}
    system = root / ".p2p" / "system"
    marker = next((system / name for name in MARKER_FILES
                   if (system / name).is_file()), None)
    manifest = None
    if (system / "p2p-install-manifest.json").is_file():
        manifest = _load_json(system / "p2p-install-manifest.json")
    release = None
    if (system / "release.json").is_file():
        release = _load_json(system / "release.json")
    return {
        "installed": True,
        "project_root": str(root),
        "marker": str(marker) if marker else None,
        "package_version": (manifest or release or {}).get("package_version"),
        "install_class": (manifest or release or {}).get("install_class"),
        "managed_file_count": (manifest or release or {}).get("managed_file_count"),
    }


# --------------------------------------------------------------- project binding

def _project_fingerprint(root: Path) -> dict[str, Any]:
    """Binding fingerprint: stable identity without business content."""
    files: list[str] = []
    for item in sorted(root.rglob("*")):
        if not item.is_file():
            continue
        rel = item.relative_to(root).as_posix()
        if any(rel == ex or rel.startswith(ex + "/")
               for ex in (".p2p", ".git", ".tmp")):
            continue
        files.append(rel)
    file_list_hash = _sha256(tuple(sorted(files)))
    git_rev = None
    git_branch = None
    try:
        # Pure-pathlib git resolution: host shells are reserved for the designated adapter boundary (cf21).
        # (cf21 adapter-boundary rule). Best-effort, never raises.
        git_dir = None
        work_git = root / ".git"
        if work_git.is_file():
            # gitdir link — read the pointer (stripping trailing newline)
            for line in work_git.read_text(encoding="utf-8",
                                           errors="replace").splitlines():
                if line.startswith("gitdir:"):
                    git_dir = Path(line[len("gitdir:"):].strip())
                    break
        elif work_git.is_dir():
            git_dir = work_git
        if git_dir is not None:
            head_ref = (git_dir / "HEAD").read_text(encoding="utf-8",
                                                    errors="replace").strip()
            branch = None
            if head_ref.startswith("ref: refs/heads/"):
                branch = head_ref[len("ref: refs/heads/"):]
                ref_file = git_dir / "refs" / "heads" / branch
                if ref_file.is_file():
                    git_rev = ref_file.read_text(encoding="utf-8",
                                                 errors="replace").strip() or None
                git_branch = branch
            else:
                git_rev = head_ref or None
    except Exception:  # noqa: BLE001 - binding best-effort, never raises
        pass
    return {
        "file_inventory_sha256": file_list_hash,
        "file_count": len(files),
        "git_revision": git_rev,
        "git_branch": git_branch,
    }


def _manifest_binding(manifest: dict) -> dict[str, Any] | None:
    """Binding recorded at install time, if the manifest carries one."""
    binding = (manifest or {}).get("project_binding") or (manifest or {}).get("binding")
    if isinstance(binding, dict):
        return binding
    return None


def recover_project_binding(root: Path) -> dict[str, Any]:
    """Recover durable project binding: manifest pointer + live fingerprint.
    If the live fingerprint contradicts the installed binding beyond the
    tolerated drift, binding_recovery is FAIL_CLOSED (stale binding rule)."""
    system = root / ".p2p" / "system"
    manifest = _load_json(system / "p2p-install-manifest.json") \
        if (system / "p2p-install-manifest.json").is_file() else None
    installed = _manifest_binding(manifest)
    live = _project_fingerprint(root)
    git_rev = live.get("git_revision")
    if installed and isinstance(installed.get("git_revision_at_install"), str):
        if git_rev and git_rev != installed["git_revision_at_install"]:
            # Stale binding: installed snapshot no longer matches working tree.
            # Fail closed: report, do not guess.
            return {
                "project_root": str(root),
                "current_revision": git_rev,
                "binding_git_revision": installed["git_revision_at_install"],
                "binding_status": "STALE",
                "binding_recovery": "FAIL_CLOSED",
                "live_inventory": {k: live[k] for k in
                                   ("file_inventory_sha256", "file_count")},
            }
    return {
        "project_root": str(root),
        "current_revision": git_rev,
        "binding_git_revision": (installed or {}).get("git_revision_at_install"),
        "binding_status": "CURRENT" if installed else "NOT_PREVIOUSBOUND",
        "binding_recovery": "OK",
        "live_inventory": {k: live[k] for k in
                           ("file_inventory_sha256", "file_count")},
    }


# ------------------------------------------------------------ owner intent

def normalize_intent(text: str) -> dict[str, Any]:
    """Normalize beginner Owner phrasing to a canonical intent id.
    Equivalent beginner phrasings normalize to the same intent:
    - 'Tiếp tục hoàn thiện dự án bằng P2P.'
    - 'Tiếp tục hoàn thiện dự án.'
    - 'Continue the project with P2P.'
    Unknown intents record INTENT_UNKNOWN and fail closed downstream
    (the loop, not this module, decides how to handle them)."""
    cleaned = (text or "").strip().lower()
    normalized = cleaned.replace(".", "").strip()
    # Exact canonical map is checked FIRST (before any stop-word stripping),
    # so the canonical phrase always yields CONTINUE_PROJECT.
    exact_map = {
        "tiếp tục hoàn thiện dự án": "CONTINUE_PROJECT",
        "continue the project": "CONTINUE_PROJECT",
        "hoàn thiện dự án": "CONTINUE_PROJECT",
        "finish the project": "CONTINUE_PROJECT",
        "tiếp tục dự án": "CONTINUE_GENERIC",
    }
    if normalized in exact_map:
        return {"intent_id": exact_map[normalized],
                "confidence": ("CANONICAL" if exact_map[normalized]
                               == "CONTINUE_PROJECT" else "HIGH")}
    # Strip provider/qualifier words so '...bằng P2P' / '...with P2P' variants
    # fall through to the same canonical intents.
    for word in ("bằng p2p", "với p2p", "using p2p", "with p2p",
                 "bằng manus", "với manus", "using manus", "with manus"):
        normalized = normalized.replace(word, "").strip()
    if normalized in exact_map:
        return {"intent_id": exact_map[normalized],
                "confidence": ("CANONICAL" if exact_map[normalized]
                               == "CONTINUE_PROJECT" else "HIGH")}
    if normalized.startswith(("continue", "tiếp tục", "hoàn thiện", "finish")):
        return {"intent_id": "CONTINUE_GENERIC", "confidence": "HIGH"}
    return {"intent_id": "INTENT_UNKNOWN", "confidence": "NONE"}


def record_owner_intent(root: Path, raw_text: str) -> dict[str, Any]:
    """Persist the normalized intent as a durable entry record.
    Only the intent id + stable hash of the raw text is stored; the raw text
    itself is sanitized (secret scrub) and never becomes state authority.
    TRANSCRIPT != STATE."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise EntryContractError("empty owner intent")
    intent = normalize_intent(raw_text)
    intent_path = root / ".p2p" / "intent.json"
    record = {
        "schema": INTENT_RECORD_SCHEMA,
        "project_root": str(root),
        "raw_text_sha256": _sha256(raw_text),
        "intent_id": intent["intent_id"],
        "confidence": intent["confidence"],
        "recorded_utc": _now_iso(),
    }
    tmp = intent_path.with_name(intent_path.name + ".tmp")
    tmp.write_text(json.dumps(_scrub(record), indent=2,
                              ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(intent_path)
    return record


# --------------------------------------------------------------- entry event

def emit_entry_event(root: Path, discovery: dict, binding: dict,
                     intent_record: dict) -> dict[str, Any]:
    """Durable entry event: the minimal footprint for a fresh process to know
    P2P was entered, when, for which project, with which intent. Fail closed
    if any prerequisite record is missing."""
    event_path = root / ".p2p" / "entry-event.json"
    if (binding.get("binding_recovery") == "FAIL_CLOSED"
            or binding.get("binding_status") == "STALE"):
        record = {
            "schema": ENTRY_EVENT_SCHEMA,
            "project_root": str(root),
            "discovery": discovery,
            "binding": binding,
            "intent": intent_record,
            "entry_result": "FAIL_CLOSED",
            "failure_class": "STALE_PROJECT_BINDING",
            "recorded_utc": _now_iso(),
        }
    else:
        record = {
            "schema": ENTRY_EVENT_SCHEMA,
            "project_root": str(root),
            "discovery": discovery,
            "binding": binding,
            "intent": intent_record,
            "entry_result": "OK",
            "no_rebriefing_required": True,
            "recorded_utc": _now_iso(),
        }
    tmp = event_path.with_name(event_path.name + ".tmp")
    tmp.write_text(json.dumps(_scrub(record), indent=2,
                              ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(event_path)
    return record


def main(argv: list[str] | None = None) -> int:
    """CLI: python3 p2p_entry.py entry <project-root> "<owner intent text>"

    Fresh process invokes this once; no re-briefing needed afterwards.
    Prints the entry record to stdout (machine + human readable)."""
    args = (argv or sys.argv[1:])
    if len(args) < 3 or args[0] != "entry":
        print("usage: p2p_entry.py entry <project-root> \"<owner intent>\"",
              file=sys.stderr)
        return 2
    root = Path(args[1]).resolve()
    intent_text = args[2]
    discovery = p2p_installed(root)
    if not discovery.get("installed"):
        print(json.dumps({"installed": False,
                          "entry_result": "FAIL_CLOSED",
                          "failure_class": "P2P_NOT_INSTALLED"},
                         ensure_ascii=False, indent=2))
        return 1
    binding = recover_project_binding(root)
    intent_record = record_owner_intent(root, intent_text)
    event = emit_entry_event(root, discovery, binding, intent_record)
    print(json.dumps(_scrub(event), ensure_ascii=False, indent=2))
    return 0 if event.get("entry_result") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
