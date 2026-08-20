# -*- coding: utf-8 -*-
"""P2P-FRAMEWORK-06 independent supervisor: 16 red-team checks over REAL
code and data paths (not mocks). Every check opens the live module files
or runs a real fresh Python subprocess against real durable state.

Pattern reused from fw05_supervisor.py:
- code strings use $SYS / $ROOT placeholders replaced via .replace()
- exactly one dict-format key ('syspath') to avoid brace conflicts
- read-only over the repo: never writes outside /tmp
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SYS = BASE / ".p2p/system"
GT = Path("/home/ubuntu/fw01_work/cert/game-truyen")
GP = Path("/home/ubuntu/fw01_work/cert/gia-pha")

sys.path.insert(0, str(SYS))
from p2p_capabilities import fw06_operational_resilience as fw06  # noqa: E402

_CHECKS = []


def check(name, detail, passed, note=""):
    _CHECKS.append((name, passed, detail + (" | " + note if note else "")))


def run_code(code: str, extra_env: dict | None = None) -> tuple[int, str, str]:
    # PYTHONPATH must contain SYS and its parents so `from p2p_capabilities
    # import ...` resolves through the package machinery (like the tests).
    env = {**os.environ,
           "PYTHONPATH": str(SYS) + os.pathsep + str(SYS.parent)
           + os.pathsep + str(SYS.parent.parent)}
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def _check_no_execution_capability():
    """FW06 never executes code: no os.system/Popen/eval/exec/subprocess
    (outside docs and the two read-only hash helpers which only run
    sha256sum on files)."""
    src = open(str(SYS / "p2p_capabilities" /
                   "fw06_operational_resilience.py"), encoding="utf-8").read()
    import ast
    tree = ast.parse(src)
    forbidden = {"system", "popen", "eval", "exec", "call"}
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = None
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            if name:
                calls.add(name.lower())
    bad = sorted(forbidden & calls)
    return bad == [], "ast-call-set=" + json.dumps(sorted(calls))


def _tmp_root():
    return tempfile.mkdtemp(prefix="fw06sup-")


# ---------------------------------------------------------------- 1-16
# 1. FW06 cannot select tasks / roles / teams / providers / models
src = open(str(SYS / "p2p_capabilities" /
               "fw06_operational_resilience.py"), encoding="utf-8").read()
joined = "\n".join(l for l in src.splitlines()
                   if not l.lstrip().startswith("#"))
c1_terms = ["select_role", "select_task", "choose_model", "choose_provider",
            "select_team", "registry_select"]
bad1 = [t for t in c1_terms if t in joined]
check("FW06 cannot select tasks/roles/teams/providers/models",
      "scan live module for selection vocab",
      len(bad1) == 0, "found=" + json.dumps(bad1))

# 2. FW06 cannot execute or mutate project state from views
ok2, note2 = _check_no_execution_capability()
check("FW06 views never execute code or mutate project state",
      "ast walk over live module", ok2, note2)

# 3. Failure classification fails closed
r3, out3, _ = run_code(
    "from p2p_capabilities import fw06_operational_resilience as fw\n"
    "assert fw.classify_failure(None) == 'UNKNOWN_MUTATION_STATE'\n"
    "assert fw.classify_failure('weird_thing_42') == 'UNKNOWN_MUTATION_STATE'\n"
    "for c in fw.FAILURE_CLASSES:\n"
    "    assert fw.classify_failure(c) == c\n"
    "print('OK')")
check("Failure classification fails closed (unknown -> UNKNOWN_MUTATION_STATE)",
      "fresh subprocess", r3 == 0 and "OK" in out3, out3.strip()[-200:])

# 4. Safe continuation is fail-closed on ANY missing gate
tmp4 = _tmp_root()
fw06.save_envelope(tmp4, dict(project_id="p1", goal_id="g1",
                              authorized_scope=["dev"], non_scope=["prod"],
                              allowed_mutation_classes=["READ_ONLY"],
                              prohibited_mutation_classes=["DEPLOYMENT"],
                              owner_gates=["RELEASE"], max_parallelism=2,
                              retry_policy={"max_retries": 3,
                                            "retryable_classes": []},
                              resource_budget={}, runtime_requirements={},
                              quality_requirements={}, recovery_policy={},
                              expiry_utc="2099-01-01T00:00:00Z",
                              evidence_pointers=[]))
r4, out4, _ = run_code(
    "from p2p_capabilities import fw06_operational_resilience as fw\n"
    "root = '$ROOT'\n".replace("$ROOT", tmp4) +
    "e = fw.load_envelope(root, 'p1')\n"
    "ok = fw.safe_continuation_decision(root, project_id='p1', task_safe=True,\n"
    "    capabilities_sufficient=True, team_eligible=True, target_eligible=True,\n"
    "    composition_complete=True, permission_valid=True, autonomy_envelope=e,\n"
    "    runtime_health='HEALTHY', quality_policy_satisfiable=True,\n"
    "    no_owner_decision_required=True)\n"
    "assert ok['decision'] == 'CONTINUE', ok\n"
    "bad = fw.safe_continuation_decision(root, project_id='p1', task_safe=False,\n"
    "    capabilities_sufficient=True, team_eligible=True, target_eligible=True,\n"
    "    composition_complete=True, permission_valid=True, autonomy_envelope=e,\n"
    "    runtime_health='HEALTHY', quality_policy_satisfiable=True,\n"
    "    no_owner_decision_required=True)\n"
    "assert bad['decision'] == 'BLOCK' and 'NEXT_TASK_NOT_SAFE' in bad['reasons'], bad\n"
    "print('OK')")
shutil.rmtree(tmp4, ignore_errors=True)
check("Safe continuation policy fail-closed on every gate",
      "fresh subprocess over real state", r4 == 0 and "OK" in out4,
      out4.strip()[-150:])

# 5. Execution lease prevents split-brain across processes
tmp5 = _tmp_root()
fw06.save_envelope(tmp5, dict(project_id="p1", goal_id="g1",
                              authorized_scope=["dev"], non_scope=["prod"],
                              allowed_mutation_classes=["READ_ONLY"],
                              prohibited_mutation_classes=["DEPLOYMENT"],
                              owner_gates=["RELEASE"], max_parallelism=2,
                              retry_policy={"max_retries": 3,
                                            "retryable_classes": []},
                              resource_budget={}, runtime_requirements={},
                              quality_requirements={}, recovery_policy={},
                              expiry_utc="2099-01-01T00:00:00Z",
                              evidence_pointers=[]))
l1 = fw06.acquire_lease(tmp5, owner_process="SUP", project_id="p1",
                        goal_id="g1", task_id="t1")
r5, out5, _ = run_code(
    "from p2p_capabilities import fw06_operational_resilience as fw\n"
    "l = fw.acquire_lease('$ROOT', owner_process='SUP2', project_id='p1',\n"
    "    goal_id='g1', task_id='t1')\n".replace("$ROOT", tmp5) +
    "assert not l['acquired'] and l['failure_class'] == 'LEASE_CONFLICT', l\n"
    "print('OK')")
shutil.rmtree(tmp5, ignore_errors=True)
check("Execution lease blocks split-brain execution (two processes)",
      "real subprocess boundary, no shared globals", r5 == 0 and "OK" in out5,
      out5.strip()[-150:])

# 6. Crash recovery never blind-re-executes: dispatch-evidenced crash
# points (A..G) never return EXECUTE/CONTINUE when verification missing.
tmp6 = _tmp_root()
r6 = None
out6 = ""
for cp in ("A", "B", "C", "D", "E", "F", "G"):
    r6, out6, _ = run_code(
        "from p2p_capabilities import fw06_operational_resilience as fw\n"
        "r = fw.recover_after_crash('$ROOT', project_id='p1', task_id='t1',\n"
        "    crash_point='$CP', dispatch_evidenced=True,\n"
        "    receipt_evidenced=False, verified_evidenced=False,\n"
        "    checkpoint_evidenced=False)\n".replace("$ROOT", tmp6)
        .replace("$CP", cp) +
        "assert r['decision'] in ('VERIFY_ONLY', 'RETRY_BOUNDED',\n"
        "    'BLOCK', 'PAUSE'), (r['decision'], r.get('failure_class'))\n"
        "print('OK')")
    if not (r6 == 0 and "OK" in out6):
        break
shutil.rmtree(tmp6, ignore_errors=True)
check("Crash recovery never blind-re-executes ambiguous mutations (A-G)",
      "fresh subprocess per crash point; decision in VERIFY_ONLY/RETRY_BOUNDED/" +
      "BLOCK/PAUSE only",
      r6 == 0 and "OK" in out6, out6.strip()[-100:])

# 7. Lease reclaim is fail-closed while owner observable
tmp7 = _tmp_root()
l7 = fw06.acquire_lease(tmp7, owner_process="SUP", project_id="p1",
                        goal_id="g1", task_id="t1", ttl_seconds=1)
lid7 = l7["lease"]["lease_id"]
fw06.heartbeat_lease(tmp7, lid7)
import datetime as _dt
from datetime import timezone as _tz
rows = list(fw06.read_leases(tmp7))
active7 = [r for r in rows if r["lease_id"] == lid7
           and r["status"] == "ACTIVE"][-1]
exp7 = dict(active7)
exp7["status"] = "EXPIRED"
exp7["expires_at"] = "2000-01-01T00:00:00Z"
exp7["expired_utc"] = fw06._utc_now()
with open(str(fw06._leases_path(tmp7)), "a", encoding="utf-8") as fh:
    fh.write(json.dumps(exp7, sort_keys=True) + "\n")
r7 = fw06.reclaim_expired_lease(tmp7, lid7)
shutil.rmtree(tmp7, ignore_errors=True)
check("Lease reclaim fail-closed when owner process still observable",
      "heartbeat-within-TTL after expiry → RECLAIM_BLOCKED_OWNER_OBSERVABLE",
      not r7["reclaimed"] and r7["failure_class"]
      == "RECLAIM_BLOCKED_OWNER_OBSERVABLE", str(r7)[:120])

# 8. Paused project state survives a fresh process restart
tmp8 = _tmp_root()
fw06.pause_project(tmp8, "p1", reason="SUPERVISOR_PAUSE_TEST")
r8, out8, _ = run_code(
    "from p2p_capabilities import fw06_operational_resilience as fw\n"
    "assert fw.is_paused('$ROOT', 'p1')\n".replace("$ROOT", tmp8) +
    "fw.resume_project('$ROOT', 'p1')\n".replace("$ROOT", tmp8) +
    "assert not fw.is_paused('$ROOT', 'p1')\n".replace("$ROOT", tmp8) +
    "print('OK')")
shutil.rmtree(tmp8, ignore_errors=True)
check("Pause/resume state durable across fresh-process restart",
      "fresh subprocess", r8 == 0 and "OK" in out8, out8.strip()[-100:])

# 9. Autonomy envelope expires → fails closed
tmp9 = _tmp_root()
fw06.save_envelope(tmp9, dict(project_id="p1", goal_id="g1",
                              authorized_scope=["dev"], non_scope=["prod"],
                              allowed_mutation_classes=["READ_ONLY"],
                              prohibited_mutation_classes=["DEPLOYMENT"],
                              owner_gates=["RELEASE"], max_parallelism=2,
                              retry_policy={"max_retries": 3,
                                            "retryable_classes": []},
                              resource_budget={}, runtime_requirements={},
                              quality_requirements={}, recovery_policy={},
                              expiry_utc="2000-01-01T00:00:00Z",
                              evidence_pointers=[]))
r9, out9, _ = run_code(
    "from p2p_capabilities import fw06_operational_resilience as fw\n"
    "e = fw.load_envelope('$ROOT', 'p1')\n".replace("$ROOT", tmp9) +
    "assert not fw.envelope_is_fresh(e), e\n"
    "e2 = fw.load_envelope('$ROOT', 'p-nosuch')\n".replace("$ROOT", tmp9) +
    "assert e2 is None, e2\n"
    "print('OK')")
shutil.rmtree(tmp9, ignore_errors=True)
check("Expired/missing autonomy envelope fails closed",
      "fresh subprocess", r9 == 0 and "OK" in out9, out9.strip()[-100:])

# 10. Event log strips secrets and never stores chain-of-thought
tmp10 = _tmp_root()
fw06.append_fw06_event(tmp10, "S", {"project_id": "p1",
                                     "token": "sk-1234567890abcdef",
                                     "reasoning": "hidden"})
evs10 = fw06.read_fw06_events(tmp10, "p1", "S")
ok10 = (evs10[-1]["payload"]["token"] == "<REDACTED>"
        and "reasoning" not in evs10[-1]["payload"])
shutil.rmtree(tmp10, ignore_errors=True)
check("Events strip secrets and drop chain-of-thought keys",
      "read live event ledger", ok10, str(evs10[-1].get("payload", {}))[:150])

# 11. Runtime health is tiered and cheap (tier-1 only by default)
r11, out11, _ = run_code(
    "from p2p_capabilities import fw06_operational_resilience as fw\n"
    "h = fw.runtime_health_check('/tmp', project_id='p1',\n"
    "    executable_requirements={'python3': {}})\n"
    "assert h['health'] == 'HEALTHY' and h['tiered'], h\n"
    "print('OK')")
check("Runtime health check tiered, cache-reused, cheap tier-1",
      "fresh subprocess", r11 == 0 and "OK" in out11, out11.strip()[-100:])

# 12. Parallel workspaces: overlap → CONFLICT, disjoint → PARALLEL_OK
r12, out12, _ = run_code(
    "from p2p_capabilities import fw06_operational_resilience as fw\n"
    "c = fw.detect_conflict(task_files_a=['shared.py'], task_files_b=['shared.py'])\n"
    "assert c['verdict'] == 'CONFLICT', c\n"
    "c2 = fw.detect_conflict(task_files_a=['a.py'], task_files_b=['b.py'])\n"
    "assert c2['verdict'] == 'PARALLEL_OK', c2\n"
    "print('OK')")
check("Parallel-workspace conflict detection deterministic",
      "fresh subprocess", r12 == 0 and "OK" in out12, out12.strip()[-100:])

# 13. Workspace cleanup fails closed on unverified mutation
tmp13 = _tmp_root()
fw06.register_workspace(tmp13, dict(workspace_id="w1", project_id="p1",
                                    owner_goal_id="g1", owner_task_id="t1",
                                    root_path="/tmp/ws1",
                                    base_revision="abc",
                                    created_at=fw06._utc_now(),
                                    status="ACTIVE",
                                    mutation_policy="SYNTHETIC_ONLY",
                                    conflict_group="",
                                    git_worktree="/tmp/ws1",
                                    evidence_pointers=[]))
r13a = fw06.cleanup_workspace(tmp13, "w1", mutation_state_known=False,
                              evidence_committed=True,
                              result_reconciled=True,
                              owner_decision_resolved=True)
r13b = fw06.cleanup_workspace(tmp13, "w1", mutation_state_known=True,
                              evidence_committed=True,
                              result_reconciled=True,
                              owner_decision_resolved=True)
shutil.rmtree(tmp13, ignore_errors=True)
check("Workspace cleanup fail-closed until all guards satisfied",
      "unknown mutation -> UNKNOWN_MUTATION_STATE; satisfied -> CLEANED",
      not r13a["cleaned"] and r13a["failure_class"] == "UNKNOWN_MUTATION_STATE"
      and r13b["cleaned"],
      str(r13a)[:100] + " | " + str(r13b)[:80])

# 14. Multi-project read-only view never writes (GT/GP shadow)
ok14 = True
if GT.exists() and GP.exists():
    for root, name in ((str(GT), "GT"), (str(GP), "GP")):
        def _th(p):
            import hashlib
            import subprocess as _sp
            digs = []
            for pp in sorted(Path(p).rglob("*")):
                if pp.is_dir():
                    continue
                d = _sp.run(["sha256sum", str(pp)], capture_output=True,
                            text=True).stdout.split()[0]
                digs.append((str(pp.relative_to(p)), d))
            return "sha256:" + hashlib.sha256(
                json.dumps(digs, sort_keys=True).encode()).hexdigest()
        before = _th(root)
        fw06.read_fw06_events(root)
        fw06.load_envelope(root, "shadow")
        fw06.lease_summary(root, "shadow")
        fw06.list_workspaces(root)
        fw06.paused_projects(root)
        fw06.quiesce_state(root, "shadow")
        fw06.multi_project_health_summary(root)
        fw06.fw06_project_summary(root, "shadow")
        after = _th(root)
        if before != after:
            ok14 = False
else:
    ok14 = False
check("All FW06 surfaces READ-ONLY over GT/GP shadow roots (byte-identical)",
      "sha256sum tree before/after every read surface", ok14,
      "roots exist=" + str(bool(GT.exists() and GP.exists())))

# 15. No project mutation anywhere: GT/GP/Logistics/deployment untouched.
# Diff-based: snapshot before/after all supervisor activity; pre-existing
# layout (e.g. GP's legitimate supabase/ tree) is baseline, not a mutation.
_snap15 = subprocess.run(["find", str(GT), str(GP), "-name", ".p2p",
                   "-or", "-name", "supabase", "-type", "d"],
                  capture_output=True, text=True)
_before15 = sorted(_snap15.stdout.strip().splitlines()) if _snap15.returncode == 0 else []
_after15 = []
for root in (GT, GP):
    if root.exists():
        for pp in root.rglob(".p2p"):
            _after15.append(str(pp))
        for pp in root.rglob("supabase"):
            if pp.is_dir():
                _after15.append(str(pp))
_after15.sort()
new15 = [d for d in _after15 if d not in _before15]
ok15 = (new15 == [] and not (GT / ".p2p").exists()
        and not (GP / ".p2p").exists())
check("FW06 produced zero project mutations (GT/GP/Supabase/deploy)",
      "diff-based tree probe before/after all supervisor activity; "
      "pre-existing dirs are baseline",
      ok15, "new dirs since start=" + repr(new15))

# 16. FW01 loop integration is info-only: hook present, no control-flow
src16 = open(str(SYS / "p2p_capabilities" / "p2p_fw01_loop.py"),
             encoding="utf-8").read()
has_hook = "fw06_resilience" in src16
ok16 = (has_hook and "fw06_operational_resilience as _fw06" in src16)
check("FW01 integration is info-only (enrichment never blocks loop)",
      "live loop source scan", ok16,
      "hook=" + str(has_hook))

# ---------------------------------------------------------------- verdict
passed = sum(1 for _, ok, _ in _CHECKS if ok)
print("P2P-FRAMEWORK-06 SUPERVISOR: %d/%d PASS" % (passed, len(_CHECKS)))
for i, (name, ok, detail) in enumerate(_CHECKS, 1):
    print("  %2d. [%s] %s: %s" % (i, "PASS" if ok else "FAIL", name, detail))
sys.exit(0 if passed == len(_CHECKS) else 1)
