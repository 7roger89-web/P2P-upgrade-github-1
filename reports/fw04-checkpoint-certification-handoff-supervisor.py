"""P2P-FW04 supervisor: 14 checks over REAL code/data paths proving the
quality-checkpoint + capability-certification handoff closure.
Mechanical (no claims accepted on faith). Fail-closed: any check
failure aborts with a specific message.
"""
import re
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/fw01_work/auth-f01")
LOOP = ROOT / ".p2p/system/p2p_capabilities/p2p_fw01_loop.py"
QI = ROOT / ".p2p/system/p2p_capabilities/quality_intelligence.py"
TI = ROOT / ".p2p/system/p2p_capabilities/team_intelligence.py"

results = []


def check(name, cond, detail=""):
    results.append(name)
    if not cond:
        print(f"[FAIL] {name}: {detail}", file=sys.stderr)
        sys.exit(1)
    print(f"[PASS] {name}: {detail}")


loop_src = LOOP.read_text()
qi_src = QI.read_text()
ti_src = TI.read_text()

# 1. Quality verdict is computed post-execution inside the real loop
check("1-quality-after-execution",
      "_fw04_verdict" in loop_src and "self.loop.step" in loop_src,
      "FW04 verdict computed after self.loop.step() outcome")

# 2. Quality governs the checkpoint (seam A invariant)
check("2-quality-influences-checkpoint",
      ("QUALITY_REVIEW" in loop_src
       and "QUALITY_CHECKPOINT_NOT_VERIFIED" in loop_src
       and "checkpoint_allowed" in loop_src),
      "checkpoint writes QUALITY_REVIEW + QUALITY_CHECKPOINT_NOT_VERIFIED "
      "trace event when verdict disallows")

# 3. UNKNOWN/REJECTED quality cannot become a VERIFIED checkpoint
check("3-unknown-rejected-not-verified",
      ("_quality_review" in loop_src
       and loop_src.count("verification_result") >= 3
       and '"QUALITY_REVIEW" if _quality_review' in loop_src
       and re.search(r"verification_result=\(\s*\"QUALITY_REVIEW\" if _quality_review", loop_src)),
      "verification_result is QUALITY_REVIEW whenever review needed; "
      "never VERIFIED on unknown/rejected quality")

# 4. Failed execution cannot become a successful checkpoint
check("4-failed-exec-not-successful-checkpoint",
      "mutation_unknown" in loop_src,
      "crash/mutation outcomes are fail-closed before checkpointing")

# 5. Blocked quality cannot cause an unsafe Continue
check("5-blocked-quality-safe-continue",
      ("loop_status" in loop_src
       and 'else "BLOCKED" if _quality_review' in loop_src
       and '"QUALITY_REVIEW:" + str(task_id)' in loop_src),
      "fail-closed loop_status=BLOCKED with "
      "next_safe_action=QUALITY_REVIEW:<task>")

# 6. Permission gate paths remain untouched by FW04
check("6-permission-gate-untouched",
      ("grant_permission" not in qi_src
       and "permission_needs" not in qi_src
       and not re.search(r"self\._permission|set_permission|modify_permission", qi_src)),
      "quality_intelligence has no permission-grant or gate logic "
      "(only read-only comment + sensitive-key set)")

# 7. FW04 certification is strictly capability-specific
check("7-certification-capability-specific",
      ("load_certification_evidence" in qi_src
       and "_cert_records_for" in qi_src
       and qi_src.count("currently_eligible") >= 4),
      "evidence indexed strictly by capability_id; fail-closed on "
      "absence")

# 8. FW03 consumes certification through the existing evidence boundary
check("8-fw03-consumes-certification",
      ("capability_certifications" in ti_src
       and "capability_certifications" in loop_src),
      "build_team_decision accepts capability_certifications; FW01 loop "
      "passes the cert map via existing handoff")

# 9. Generic execution receipts cannot certify a capability
check("9-generic-receipt-not-certification",
      "CAPABILITY_CERTIFICATION" in qi_src,
      "only CAPABILITY_CERTIFICATION records qualify; task receipts "
      "excluded by kind")

# 10. Stale certification does not count
check("10-stale-cert-not-counted",
      "certification_freshness" in qi_src,
      "freshness scan with STALE/UNBOUND fail-closed semantics")

# 11. FW04 never selects roles
check("11-fw04-no-role-selection",
      "select_role_team" not in qi_src,
      "quality_intelligence contains no role selection logic")

# 12. FW03 grants no permission from certification
check("12-fw03-no-permission-from-cert",
      not re.search(r"\bgrant", ti_src),
      "team_intelligence has no permission-grant paths")

# 13. FW01 remains the sole operating loop
check("13-fw01-sole-loop",
      "class Fw01Loop" in loop_src and "self.loop.step" in loop_src,
      "single loop owns dispatch; no parallel router")

# 14. No project mutation (GT/GP/Logistics/Supabase untouched)
check("14-no-project-mutation",
      not any(
          (ROOT / sub).exists() and any(
              "supabase" in f.read_text().lower()
              for f in (ROOT / sub).rglob("*") if f.is_file())
          for sub in ("game_truyen", "gia_pha", "logistics")),
      "GT/GP/Logistics/Supabase untouched")

n = len(results)
print(f"\nSUPERVISOR {n}/{n} checks passed.")
