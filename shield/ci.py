"""Narrow GitHub Actions workflow scan via pinned Zizmor 1.29.0. No generic provider registry."""
import argparse
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from shield import zizmor_acquire
from shield.runner import resolve_target_ref


CONTROL_ID = "SHIELD-CI-01"
CONTROL_VERSION = "0.1.0"
PROVIDER = "Zizmor"
VERSION = "1.29.0"
SCOPE = "github_actions_workflow_scan"
EVIDENCE_SCHEMA = "p2p-shield-evidence/1"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_control():
    path = Path(__file__).parent / "controls" / f"{CONTROL_ID}.json"
    data = json.loads(path.read_text())
    if data.get("control_id") != CONTROL_ID or data.get("control_version") != CONTROL_VERSION:
        raise ValueError("CI_CONTROL_ID_VERSION_MISMATCH")
    return data


def _extract_findings(report):
    """Validate report shape and extract raw findings list."""
    if not isinstance(report, list):
        raise ValueError("PROVIDER_REPORT_SHAPE_UNSUPPORTED")
    for item in report:
        if not isinstance(item, dict):
            raise ValueError("PROVIDER_REPORT_NON_OBJECT_FINDING")
        if not isinstance(item.get("ident"), str) or not item.get("ident"):
            raise ValueError("MALFORMED_FINDING_IDENT")
    return report


def _normalize_findings(raw_findings):
    normalized = []
    for finding in raw_findings:
        ident = finding.get("ident", "")
        determinations = finding.get("determinations", {}) if isinstance(finding.get("determinations"), dict) else {}
        severity = determinations.get("severity", "")
        confidence = determinations.get("confidence", "")
        # Find primary location or first
        locations = finding.get("locations", []) if isinstance(finding.get("locations"), list) else []
        primary = None
        for loc in locations:
            try:
                if loc.get("symbolic", {}).get("kind") == "Primary":
                    primary = loc
                    break
            except Exception:
                continue
        if primary is None and locations:
            primary = locations[0]
        file_path = ""
        row = None
        col = None
        if primary:
            try:
                # symbolic.key.Local.verbatim_path
                sym_key = primary.get("symbolic", {}).get("key", {})
                if isinstance(sym_key, dict) and "Local" in sym_key:
                    file_path = sym_key["Local"].get("verbatim_path", "")
                else:
                    file_path = str(sym_key)
            except Exception:
                file_path = ""
            try:
                concrete = primary.get("concrete", {})
                location = concrete.get("location", {})
                start = location.get("start_point", {})
                row = start.get("row")
                col = start.get("column")
                if not isinstance(row, int):
                    row = None
                if not isinstance(col, int):
                    col = None
            except Exception:
                row = None
        entry = dict(audit=ident, file=file_path)
        if severity:
            entry["severity"] = severity
        if confidence:
            entry["confidence"] = confidence
        if row is not None:
            entry["line"] = row
        if col is not None:
            entry["column"] = col
        # url for reference
        url = finding.get("url")
        if isinstance(url, str) and url:
            entry["url"] = url
        normalized.append(entry)
    return normalized


def assess(target, executable, reference):
    target = Path(target).resolve()
    executable = Path(executable).resolve()
    e = dict(
        schema=EVIDENCE_SCHEMA,
        control_id=CONTROL_ID,
        control_version=CONTROL_VERSION,
        provider=PROVIDER,
        provider_version=VERSION,
        provider_source=f"zizmorcore/zizmor@v{VERSION}",
        target=str(target),
        target_ref="UNRESOLVED",
        timestamp=_utc_timestamp(),
        status="BLOCKED",
        scope=SCOPE,
        coverage=["NONE_ESTABLISHED"],
        findings_count=0,
        findings=[],
        limitations=[],
        reason="NOT_ASSESSED",
        artifact_or_reference=reference,
    )
    try:
        m = zizmor_acquire.mapping()
        control = _load_control()
        # limitations from mapping
        e["limitations"] = list(m.get("limitations", []))
        # also record known_exclusions as part of limitations for transparency
        # but keep as separate field? For now append
        # target_ref
        e["target_ref"] = resolve_target_ref(target)
        if not re.fullmatch(r"[0-9a-f]{40,64}", e["target_ref"]):
            raise ValueError("TARGET_REF_UNRESOLVED")
        # Verify executable version (also checks pin)
        try:
            observed = zizmor_acquire.verify_executable(executable)
        except Exception as exc:
            # If verify_executable fails due to missing receipt but version still checkable, try direct version
            # zizmor_acquire.version already raises appropriate error
            raise
        e["provider_version_observed"] = observed
        # Build invocation from mapping
        invocation = m.get("invocation", {})
        detect_argv_templates = invocation.get("detect_argv")
        if not isinstance(detect_argv_templates, list) or not detect_argv_templates:
            raise ValueError("PROVIDER_INVOCATION_MISSING")
        # Substitute placeholders
        argv = []
        for tmpl in detect_argv_templates:
            token = tmpl.replace("{executable}", str(executable)).replace("{target}", str(target))
            # {report} not used for zizmor; leave as is if present (should not be)
            if "{report}" in token:
                raise ValueError("UNRESOLVED_TOKEN_IN_ARGV")
            argv.append(token)
        # Quick check for unresolved tokens
        for token in argv:
            if re.search(r"\{[A-Za-z_][A-Za-z0-9_]*\}", token):
                raise ValueError(f"PROVIDER_ARGV_UNRESOLVED:{token}")
        # Execute provider; cwd = target directory to ensure config discovery consistent with repo root
        cwd = str(target) if target.is_dir() else None
        # Isolate from any GitHub token to ensure offline deterministic run; but not required
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=120)
        diagnostics = dict(provider_exit_code=proc.returncode, provider_stderr_tail=(proc.stderr or "")[-400:], provider_stdout_len=len(proc.stdout or ""))
        e["diagnostics"] = diagnostics
        # Handle no inputs case: exit 3
        if proc.returncode == 3:
            raise ValueError("WORKFLOW_INVENTORY_INDETERMINATE:provider_exit_3_no_workflows_or_no_auditable_inputs")
        # Parse report: zizmor JSON goes to stdout
        stdout = (proc.stdout or "").strip()
        if not stdout:
            # Empty stdout with non-zero? Could be error without JSON
            if proc.returncode != 0:
                raise ValueError(f"PROVIDER_EXECUTION_OR_OUTPUT_FAILURE:empty_stdout_rc={proc.returncode}")
            else:
                # Empty stdout with rc0 but should be [] for no findings; treat as malformed
                raise ValueError("PROVIDER_OUTPUT_EMPTY")
        try:
            report = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"PROVIDER_OUTPUT_MALFORMED:{exc}") from exc
        raw_findings = _extract_findings(report)
        normalized = _normalize_findings(raw_findings)
        # Determine status by findings and exit code
        # Zizmor exit codes: 0 no findings, 11-14 findings by severity, 1 error, 2 arg parse, 3 no inputs
        # We already handled 3
        if proc.returncode == 0:
            if len(raw_findings) == 0:
                # PASS: ensure inventory was actually established
                # If raw_findings 0 but provider completed, we need to ensure workflow files existed
                # The provider would have returned 3 if none; so 0 findings here means at least one workflow was scanned
                e.update(status="PASS", findings_count=0, findings=[], coverage=list(m.get("coverage", [])), reason="WORKFLOW_SCAN_COMPLETED_WITHOUT_FINDINGS")
            else:
                # Non-zero findings but exit 0: should not happen normally but treat as FAIL if findings present
                e.update(status="FAIL", findings_count=len(raw_findings), findings=normalized[:25], coverage=list(m.get("coverage", [])), reason="WORKFLOW_SCAN_COMPLETED_WITH_FINDINGS_RC0")
        elif proc.returncode in (11, 12, 13, 14):
            if len(raw_findings) == 0:
                raise ValueError(f"EXIT_CODE_FINDINGS_MISMATCH:rc={proc.returncode}:findings=0")
            e.update(status="FAIL", findings_count=len(raw_findings), findings=normalized[:25], coverage=list(m.get("coverage", [])), reason="WORKFLOW_SCAN_COMPLETED_WITH_FINDINGS")
        else:
            # Any other exit (1,2 etc) is provider failure => BLOCKED
            raise ValueError(f"PROVIDER_EXIT_UNEXPECTED:rc={proc.returncode}")
        # Verify target hasn't changed during scan
        if resolve_target_ref(target) != e["target_ref"]:
            raise ValueError("TARGET_CHANGED_DURING_SCAN")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as exc:
        # Preserve existing diagnostics if any, else set minimal
        if "diagnostics" not in e:
            e["diagnostics"] = dict(provider_exit_code=None, provider_stderr_tail=str(exc)[:200])
        # Ensure coverage is NONE_ESTABLISHED for BLOCKED
        if e.get("status") != "BLOCKED":
            e["status"] = "BLOCKED"
            e["coverage"] = ["NONE_ESTABLISHED"]
        # Build reason
        base = type(exc).__name__
        msg = str(exc)
        # If exc is ValueError with uppercase token, include it
        if isinstance(exc, ValueError) and msg and msg.split(":")[0].isupper():
            base = base + ":" + msg.split(":")[0]
            # include full msg up to 200 chars
            e["reason"] = f"ASSESSMENT_BLOCKED:{base}:{msg[:200]}"
        else:
            e["reason"] = f"ASSESSMENT_BLOCKED:{base}:{msg[:200]}" if msg else f"ASSESSMENT_BLOCKED:{base}"
        e["findings_count"] = 0
        e["findings"] = []
        # Ensure limitations still declared
        try:
            if not e.get("limitations"):
                m = zizmor_acquire.mapping()
                e["limitations"] = list(m.get("limitations", []))
        except Exception:
            if not e.get("limitations"):
                e["limitations"] = ["No provider assessment completed; no coverage is claimed."]
    return e


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Zizmor workflow assessment")
    p.add_argument("--target", required=True)
    p.add_argument("--executable", required=True)
    p.add_argument("--reference", required=True)
    a = p.parse_args()
    evidence = assess(a.target, a.executable, a.reference)
    print(json.dumps(evidence, indent=2))
    raise SystemExit({"PASS": 0, "FAIL": 1, "BLOCKED": 2}[evidence["status"]])
