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
CONTROL_VERSION = "0.2.0"
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
        applicability={
            "basis": "NOT_ESTABLISHED",
            "path": ".github/workflows",
            "workflow_count": None,
        },
    )
    try:
        m = zizmor_acquire.mapping()
        control = _load_control()
        e["limitations"] = list(m.get("limitations", []))
        e["target_ref"] = resolve_target_ref(target)
        if not re.fullmatch(r"[0-9a-f]{40,64}", e["target_ref"]):
            raise ValueError("TARGET_REF_UNRESOLVED")

        # Establish applicability from the immutable target shape before provider execution.
        github_root = target / ".github"
        workflows_root = github_root / "workflows"
        if github_root.is_symlink():
            raise ValueError("WORKFLOW_INVENTORY_INDETERMINATE:github_root_symlink")
        if workflows_root.exists() and (workflows_root.is_symlink() or not workflows_root.is_dir()
                or not workflows_root.resolve().is_relative_to(target)):
            raise ValueError("WORKFLOW_INVENTORY_INDETERMINATE:workflows_root_not_regular_directory")
        workflow_files = []
        if workflows_root.is_dir():
            for pattern in ("*.yml", "*.yaml"):
                for candidate in workflows_root.glob(pattern):
                    if candidate.is_symlink() or not candidate.is_file():
                        raise ValueError("WORKFLOW_INVENTORY_INDETERMINATE:workflow_not_regular_file")
                    workflow_files.append(candidate)
        if not workflow_files:
            e.update(
                status="NOT_APPLICABLE",
                findings_count=0,
                findings=[],
                coverage=["NOT_APPLICABLE_BY_TARGET_SHAPE"],
                reason="TARGET_SHAPE_HAS_NO_GITHUB_ACTIONS_WORKFLOWS",
                applicability={
                    "basis": "DETERMINISTIC_EMPTY_WORKFLOW_INVENTORY",
                    "path": ".github/workflows",
                    "workflow_count": 0,
                },
            )
            return e
        e["applicability"] = {
            "basis": "WORKFLOW_INVENTORY_PRESENT",
            "path": ".github/workflows",
            "workflow_count": len(workflow_files),
        }

        observed = zizmor_acquire.verify_executable(executable)
        e["provider_version_observed"] = observed
        invocation = m.get("invocation", {})
        detect_argv_templates = invocation.get("detect_argv")
        if not isinstance(detect_argv_templates, list) or not detect_argv_templates:
            raise ValueError("PROVIDER_INVOCATION_MISSING")
        argv = []
        for tmpl in detect_argv_templates:
            token = tmpl.replace("{executable}", str(executable)).replace("{target}", str(target))
            if "{report}" in token:
                raise ValueError("UNRESOLVED_TOKEN_IN_ARGV")
            argv.append(token)
        for token in argv:
            if re.search(r"\{[A-Za-z_][A-Za-z0-9_]*\}", token):
                raise ValueError(f"PROVIDER_ARGV_UNRESOLVED:{token}")
        cwd = str(target) if target.is_dir() else None
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=120)
        diagnostics = dict(
            provider_exit_code=proc.returncode,
            provider_stderr_tail=(proc.stderr or "")[-400:],
            provider_stdout_len=len(proc.stdout or ""),
        )
        e["diagnostics"] = diagnostics
        if proc.returncode == 3:
            raise ValueError("WORKFLOW_INVENTORY_INDETERMINATE:provider_exit_3_no_workflows_or_no_auditable_inputs")
        stdout = (proc.stdout or "").strip()
        if not stdout:
            if proc.returncode != 0:
                raise ValueError(f"PROVIDER_EXECUTION_OR_OUTPUT_FAILURE:empty_stdout_rc={proc.returncode}")
            raise ValueError("PROVIDER_OUTPUT_EMPTY")
        try:
            report = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"PROVIDER_OUTPUT_MALFORMED:{exc}") from exc
        raw_findings = _extract_findings(report)
        normalized = _normalize_findings(raw_findings)
        if proc.returncode == 0:
            if len(raw_findings) == 0:
                e.update(
                    status="PASS",
                    findings_count=0,
                    findings=[],
                    coverage=list(m.get("coverage", [])),
                    reason="WORKFLOW_SCAN_COMPLETED_WITHOUT_FINDINGS",
                )
            else:
                e.update(
                    status="FAIL",
                    findings_count=len(raw_findings),
                    findings=normalized[:25],
                    coverage=list(m.get("coverage", [])),
                    reason="WORKFLOW_SCAN_COMPLETED_WITH_FINDINGS_RC0",
                )
        elif proc.returncode in (11, 12, 13, 14):
            if len(raw_findings) == 0:
                raise ValueError(f"EXIT_CODE_FINDINGS_MISMATCH:rc={proc.returncode}:findings=0")
            e.update(
                status="FAIL",
                findings_count=len(raw_findings),
                findings=normalized[:25],
                coverage=list(m.get("coverage", [])),
                reason="WORKFLOW_SCAN_COMPLETED_WITH_FINDINGS",
            )
        else:
            raise ValueError(f"PROVIDER_EXIT_UNEXPECTED:rc={proc.returncode}")
        if resolve_target_ref(target) != e["target_ref"]:
            raise ValueError("TARGET_CHANGED_DURING_SCAN")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as exc:
        if "diagnostics" not in e:
            e["diagnostics"] = dict(provider_exit_code=None, provider_stderr_tail=str(exc)[:200])
        if e.get("status") != "BLOCKED":
            e["status"] = "BLOCKED"
            e["coverage"] = ["NONE_ESTABLISHED"]
        base = type(exc).__name__
        msg = str(exc)
        if isinstance(exc, ValueError) and msg and msg.split(":")[0].isupper():
            base = base + ":" + msg.split(":")[0]
            e["reason"] = f"ASSESSMENT_BLOCKED:{base}:{msg[:200]}"
        else:
            e["reason"] = f"ASSESSMENT_BLOCKED:{base}:{msg[:200]}" if msg else f"ASSESSMENT_BLOCKED:{base}"
        e["findings_count"] = 0
        e["findings"] = []
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
    raise SystemExit({"PASS": 0, "NOT_APPLICABLE": 0, "FAIL": 1, "BLOCKED": 2}[evidence["status"]])
