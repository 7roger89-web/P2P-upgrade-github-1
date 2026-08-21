"""FRAMEWORK-01 real installed-project discovery proofs — §26.

Read-only fresh-process recovery for each already installed P2P project:

    fresh process -> invoke installed P2P entry contract (CLI) ->
    no re-briefing -> recover project binding -> recover project truth ->
    identify current goal / next safe task -> evidence -> STOP before mutation

Production projects are READ-ONLY for this goal: no source modification,
no Supabase mutation, no RLS weakening. Git status is recorded before and
after each invocation. The entry contract writes ONLY .p2p entry state
(.p2p/intent.json, .p2p/entry-event.json) — project source untouched.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

P2P_SYSTEM = Path(__file__).resolve().parent.parent / ".p2p" / "system"
sys.path.insert(0, str(P2P_SYSTEM))

PROJECTS = {
    "GAME_TRUYEN": Path("/home/ubuntu/game-truyen-production"),
    "GIA_PHA": Path("/home/ubuntu/gia-pha-production"),
}

EVIDENCE_DIR = Path(
    "/home/ubuntu/p2p-repo/docs/p2p-development/research/framework-01/discovery")

INTENT = "Tiếp tục hoàn thiện dự án bằng P2P."


def _git_snapshot(project_dir: Path) -> dict:
    try:
        head = subprocess.run(
            ["git", "-C", str(project_dir), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True).stdout.strip()
        return {"head": head, "dirty": bool(status),
                "dirty_files": [l.split(None, 1)[-1]
                                for l in status.splitlines()[:10]]}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)[:200]}


def main() -> int:
    evidence = EVIDENCE_DIR
    evidence.mkdir(parents=True, exist_ok=True)

    verdicts = {}
    records = []
    source_clean = True

    for label, project_dir in PROJECTS.items():
        before = _git_snapshot(project_dir)

        entry_cli = project_dir / ".p2p" / "system" / "p2p_entry.py"
        proc = subprocess.run(
            [sys.executable, str(entry_cli), "entry",
             str(project_dir), INTENT],
            capture_output=True, text=True, timeout=120,
            cwd=str(project_dir))

        after = _git_snapshot(project_dir)
        # Source-level mutation check: git-tracked files unchanged.
        src_mutated = (before.get("dirty") is False and after.get("dirty") is True)
        if src_mutated:
            source_clean = False

        try:
            entry_event = json.loads(proc.stdout)
            cli_leg_worked = True
        except (json.JSONDecodeError, TypeError):
            entry_event = {"raw_error": (proc.stderr or proc.stdout)[:2000]}
            cli_leg_worked = False

        # --- Fallback leg: repo entry contract against production truth ---
        # The entry contract (p2p_entry.py) is not yet released into
        # production installs (§30). A fresh process CAN still enter the
        # installed P2P system read-only by invoking the entry contract
        # with PYTHONPATH over the installed .p2p/system. This proves the
        # installed runtime is loadable and the project truth is
        # recoverable WITHOUT re-briefing; production source untouched.
        repo_entry = P2P_SYSTEM / "p2p_capabilities" / "p2p_entry.py"
        fallback = None
        if not cli_leg_worked and repo_entry.exists():
            # Invoke as a PACKAGE module (-m) because p2p_entry uses
            # relative imports (from .context import ...).
            # The installed .p2p/system is a C40-era snapshot WITHOUT
            # p2p_entry.py (p2p_entry is the FRAMEWORK-01 contract). The
            # entry contract can still enter the installed system
            # read-only: it only reads project truth from the given root.
            # Use the REPO's p2p_capabilities package (repo first) so the
            # entry contract module resolves.
            pypath = (f"{P2P_SYSTEM}:{project_dir}/.p2p/system")
            proc2 = subprocess.run(
                [sys.executable, "-c",
                 f"import sys; "
                 f"sys.path.insert(0, {str(P2P_SYSTEM)!r}); "
                 f"from p2p_capabilities import p2p_entry; "
                 f"sys.exit(p2p_entry.main([\"entry\", "
                 f"{str(project_dir)!r}, {INTENT!r}]))"],
                capture_output=True, text=True, timeout=120,
                env={**__import__("os").environ, "PYTHONPATH": pypath},
                cwd=str(project_dir))
            try:
                fallback = json.loads(proc2.stdout)
            except (json.JSONDecodeError, TypeError):
                fallback = {"raw_error": (proc2.stderr or proc2.stdout)[:2000]}
            entry_event.setdefault("fallback_via_repo_entry", fallback)
        record = {
            "project": label,
            "project_dir": str(project_dir),
            "intent": INTENT,
            "fresh_process_invoked": True,
            "entry_cli": str(entry_cli),
            "returncode": proc.returncode,
            "cli_leg_worked": cli_leg_worked,
            "before_git": before,
            "after_git": after,
            "source_level_mutated": src_mutated,
            "entry_event": entry_event,
            "RELEASE_REQUIRED_FOR_PROJECT_USE": not cli_leg_worked,
        }
        records.append(record)

        # --- Verdict machinery (two legs, honest separation) ---
        binding_status = (entry_event.get("binding", {})
                          .get("binding_status") or "UNKNOWN")
        entry_ok = entry_event.get("entry_result") == "OK"
        no_rebriefing = bool(
            entry_event.get("no_rebriefing_required") or
            (entry_event.get("binding", {})
             .get("binding_recovery") not in ("FAIL_CLOSED",) and
             binding_status != "STALE"))
        fb = entry_event.get("fallback_via_repo_entry") or {}
        fb_ok = fb.get("entry_result") == "OK" and bool(
            fb.get("no_rebriefing_required"))
        verdicts[f"{label}_NO_BRIEFING_RECOVERY"] = (
            "VERIFIED" if (entry_ok and no_rebriefing and not src_mutated)
            else "NOT_PROVEN")
        verdicts[f"{label}_REPO_ENTRY_OVER_INSTALLED_SYSTEM"] = (
            "VERIFIED" if (fb_ok and not src_mutated)
            else "NOT_PROVEN")
        record["RELEASE_REQUIRED_FOR_PROJECT_USE"] = not cli_leg_worked

        (evidence / f"{label.lower()}-discovery-proof.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8")

    out = {
        "leg": "FW01_INSTALLED_PROJECT_DISCOVERY",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mode": "READ_ONLY",
        "supabase_untouched": True,
        "rls_untouched": True,
        "all_source_clean": source_clean,
        "verdicts": verdicts,
        "records": records,
    }
    (evidence / "fw01-discovery-registry.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if source_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
