#!/usr/bin/env python3
"""Fresh DT1-DT24 behavioral certification for the native decision trace."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import decision_trace as trace  # noqa: E402


EVAL_SCHEMA = "p2p-decision-trace-eval/1"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fixture(root: Path, *, with_governance: bool = False) -> Path:
    (root / ".p2p/state/reports").mkdir(parents=True, exist_ok=True)
    (root / ".p2p/state/goal-contract.json").write_text("{}\n", encoding="utf-8")
    (root / ".p2p/state/project-status.json").write_text("{}\n", encoding="utf-8")
    (root / ".p2p/state/reports/result.json").write_text("{}\n", encoding="utf-8")
    if with_governance:
        _write_json(
            root / "governance/fact-ledger.json",
            {
                "claims": [
                    {
                        "claim_id": "P2P-FACT-TEST1",
                        "checked_at": "2026-08-01",
                        "expires_at": "2099-01-01",
                        "source_url": "https://example.invalid/fact",
                    }
                ]
            },
        )
    return root


def _record(root: Path, decision_id: str, decision_type: str = "ARCHITECTURE", **kwargs: Any) -> dict[str, object]:
    value = trace.make_trace(
        decision_id=decision_id,
        goal_id="goal-test",
        decision_type=decision_type,
        outcome=kwargs.pop("outcome", "selected bounded option"),
        decision_basis=kwargs.pop("decision_basis", {"summary": "Use the existing governed local state"}),
        **kwargs,
    )
    trace.append_trace(root, value)
    return value


def _case(case_id: str, name: str, fn: Callable[[], tuple[bool, str]]) -> dict[str, object]:
    try:
        passed, note = fn()
        return {"case_id": case_id, "name": name, "status": "PASS" if passed else "FAIL", "notes": note}
    except Exception as exc:
        return {"case_id": case_id, "name": name, "status": "FAIL", "notes": f"{type(exc).__name__}: {exc}"}


def run_evaluation(repo_root: Path = REPO_ROOT) -> dict[str, object]:
    repo_root = repo_root.resolve()
    baseline_files = sorted((repo_root / "reports/QA").glob("*beginner-lifecycle-certification.json"))
    baseline_gap = False
    if baseline_files:
        try:
            baseline = json.loads(baseline_files[-1].read_text(encoding="utf-8"))
            baseline_gap = "single native decision trace is not present" in json.dumps(baseline, ensure_ascii=False).lower()
        except (OSError, UnicodeError, json.JSONDecodeError):
            baseline_gap = False

    with tempfile.TemporaryDirectory(prefix="p2p-decision-trace-eval-") as raw:
        temp = Path(raw)
        cases: list[dict[str, object]] = []
        before_hashes = {name: _hash(repo_root / name) for name in ("VERSION", "AGENTS.md") if (repo_root / name).is_file()}

        def dt1() -> tuple[bool, str]:
            return baseline_gap, "historical certification records distributed WHY evidence without a native trace"

        def dt2() -> tuple[bool, str]:
            value = trace.make_trace(decision_id="D2", decision_type="ARCHITECTURE", outcome="native", decision_basis={"summary": "bounded"})
            return trace.validate_trace(value)["valid"], "minimal record validates"

        def dt3() -> tuple[bool, str]:
            project = _fixture(temp / "dt3")
            _record(project, "D3")
            result = trace.query_trace(project, decision_id="D3")
            return result["decision_ids"] == ["D3"], "decision reconstructs from the existing ledger"

        def dt4() -> tuple[bool, str]:
            project = _fixture(temp / "dt4", with_governance=True)
            _record(project, "D4", fact_refs=["P2P-FACT-TEST1"], evidence_refs=[".p2p/state/reports/result.json"], source_refs=["https://example.invalid/fact"])
            result = trace.query_trace(project, decision_id="D4")
            statuses = [entry["STATUS"] for group in result["results"][0]["links"].values() for entry in group]
            return result["status"] == "PASS" and statuses.count("PRESENT") >= 3, "fact, evidence, and source links resolve"

        def dt5() -> tuple[bool, str]:
            try:
                trace.make_trace(decision_id="D5", decision_type="SECURITY", outcome="x", decision_basis={"summary": "x"}, owner_approval_ref=True)
            except trace.DecisionTraceError:
                return True, "bare approval boolean is rejected"
            return False, "bare approval boolean was accepted"

        def dt6() -> tuple[bool, str]:
            project = _fixture(temp / "dt6", with_governance=True)
            fact_path = project / "governance/fact-ledger.json"
            before = _hash(fact_path)
            _record(project, "D6", policy_refs=["approval-policy.json"])
            return before == _hash(fact_path), "governance links do not mutate FACT_LEDGER"

        def dt7() -> tuple[bool, str]:
            categories = set(trace.DECISION_TYPES) - {"OTHER_MATERIAL"}
            return all(trace.materiality("material decision", category)["material"] for category in categories), "all material categories capture explicitly"

        def dt8() -> tuple[bool, str]:
            project = _fixture(temp / "dt8")
            result = trace.capture_material_decision(project, request="run the unit tests", goal_id="G8", run_id="R8", workflow_status="PASS", outcome="tests pass")
            return result["captured"] is False and result["status"] == "NOT_MATERIAL", "routine activity creates no trace"

        def dt9() -> tuple[bool, str]:
            project = _fixture(temp / "dt9")
            _record(project, "D9A")
            _record(project, "D9B", decision_type="SECURITY", contradicts=["D9A"])
            _record(project, "D9C", relationship="SUPPORTS", supports=["D9A"])
            contradiction = trace.query_trace(project, decision_id="D9A")["status"] == "CONTRADICTED"
            support = trace.query_trace(project, decision_id="D9C")["results"][0]["trace"]["RELATIONSHIP"] == "SUPPORTS"
            unknown = trace.make_trace(decision_id="D9D", decision_type="OTHER_MATERIAL", outcome="x", decision_basis={"summary": "x"})["RELATIONSHIP"] == "UNKNOWN"
            return contradiction and support and unknown, "SUPPORTS, CONTRADICTS, and UNKNOWN relationships remain explicit"

        def dt10() -> tuple[bool, str]:
            project = _fixture(temp / "dt10")
            _record(project, "D10A")
            _record(project, "D10B", supersedes=["D10A"])
            result = trace.query_trace(project, decision_id="D10A")
            return result["results"][0]["superseding_decisions"] == ["D10B"], "supersession is explicit and old record remains"

        def dt11() -> tuple[bool, str]:
            project = _fixture(temp / "dt11", with_governance=True)
            value = trace.make_trace(decision_id="D11", decision_type="DATA", created_at="2026-07-01T00:00:00+00:00", outcome="x", decision_basis={"summary": "x"}, fact_refs=["P2P-FACT-TEST1"])
            trace.append_trace(project, value)
            result = trace.query_trace(project, decision_id="D11")
            return result["status"] == "PARTIAL" and result["results"][0]["temporal_reconstruction"]["issues"], "decision creation and reference freshness are distinguished"

        def dt12() -> tuple[bool, str]:
            project = _fixture(temp / "dt12")
            _record(project, "D12", source_refs=["missing-source"])
            result = trace.query_trace(project, decision_id="D12")
            return result["status"] == "PARTIAL" and any(item["STATUS"] == "MISSING_REFERENCE" for item in result["results"][0]["links"]["SOURCE_REFS"]), "missing reference is explicit"

        def dt13() -> tuple[bool, str]:
            project = _fixture(temp / "dt13", with_governance=True)
            fact = json.loads((project / "governance/fact-ledger.json").read_text(encoding="utf-8"))
            fact["claims"][0]["expires_at"] = "2020-01-01"
            _write_json(project / "governance/fact-ledger.json", fact)
            _record(project, "D13", fact_refs=["P2P-FACT-TEST1"])
            result = trace.query_trace(project, decision_id="D13")
            return result["status"] == "PARTIAL" and result["results"][0]["links"]["FACT_REFS"][0]["STATUS"] == "STALE", "stale reference is not silently rewritten"

        def dt14() -> tuple[bool, str]:
            project = _fixture(temp / "dt14")
            _record(project, "D14")
            why = trace.query_trace(project, decision_id="D14")["beginner_why"]
            return "P2P chọn cách này vì" in why, "beginner WHY is plain language"

        def dt15() -> tuple[bool, str]:
            value = trace.make_trace(decision_id="D15", decision_type="SECURITY", outcome="safe", decision_basis={"summary": "password=topsecret; chain_of_thought must not persist"})
            serialized = json.dumps(value, ensure_ascii=False).lower()
            return value["REDACTION_STATE"]["status"] == "REDACTED" and "topsecret" not in serialized and "chain_of_thought" not in serialized, "secrets and private reasoning are redacted"

        def dt16() -> tuple[bool, str]:
            value = trace.make_trace(decision_id="D16", decision_type="ARCHITECTURE", outcome="safe", decision_basis={"summary": "safe"})
            tampered = copy.deepcopy(value)
            tampered["OUTCOME"] = "changed"
            return trace.validate_trace(tampered)["valid"] is False, "payload checksum detects tampering"

        def dt17() -> tuple[bool, str]:
            return len(trace.CANONICAL_IDENTITIES) == 8 and len(set(trace.CANONICAL_IDENTITIES)) == 8 and trace.CANONICAL_DENOMINATOR == 8, "canonical identity set and denominator remain exact"

        def dt18() -> tuple[bool, str]:
            try:
                trace.make_trace(decision_id="D18", decision_type="DESIGN", outcome="x", decision_basis={"summary": "x"}, supporting_specialist_refs=[{"identity": "p2p_aesthetica", "ref": "profile"}])
            except trace.DecisionTraceError:
                return True, "unverified Aesthetica cannot be fabricated"
            return False, "unverified Aesthetica was accepted"

        def dt19() -> tuple[bool, str]:
            project = temp / "dt19"
            project.mkdir()
            result = trace.query_trace(project)
            return result["status"] == "NOT_INITIALIZED" and not (project / ".p2p/state/execution-ledger.jsonl").exists(), "projects without trace history continue safely"

        def dt20() -> tuple[bool, str]:
            project = _fixture(temp / "dt20")
            ledger = project / ".p2p/state/execution-ledger.jsonl"
            ledger.write_text('{"event":"decision_trace_record","trace":{"DECISION_ID":"bad"}}\n', encoding="utf-8")
            result = trace.query_trace(project)
            return result["status"] in {"UNKNOWN", "PARTIAL"} and trace.doctor(project)["status"] == "PARTIAL", "invalid legacy trace is diagnosed without taking P2P unavailable"

        def dt21() -> tuple[bool, str]:
            project = _fixture(temp / "dt21")
            _record(project, "D21", created_at="2026-01-01T00:00:00+00:00")
            first = trace.export_trace(project, output=project / "one.json", fmt="json", decision_id="D21")
            second = trace.export_trace(project, output=project / "two.json", fmt="json", decision_id="D21")
            return _hash(Path(first["output"])) == _hash(Path(second["output"])), "JSON export is deterministic"

        def dt22() -> tuple[bool, str]:
            project = _fixture(temp / "dt22")
            _record(project, "D22")
            result = trace.export_trace(project, output=project / "trace.md", fmt="markdown", decision_id="D22")
            text = Path(result["output"]).read_text(encoding="utf-8")
            return text.startswith("# P2P Decision Trace Export") and "Beginner WHY" in text, "Markdown export is readable and safe"

        def dt23() -> tuple[bool, str]:
            result = trace.doctor(temp)
            return result["external_dependencies"] == [], "native trace reports no external dependency"

        def dt24() -> tuple[bool, str]:
            completed = subprocess.run(
                [sys.executable, "-m", "unittest", "tests.test_p2p_capability_foundation", "tests.test_p2p_workflow"],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                check=False,
            )
            return completed.returncode == 0, "existing foundation/workflow regression suite passed" if completed.returncode == 0 else completed.stdout[-800:]

        definitions = [
            ("DT1", "baseline gap", dt1), ("DT2", "minimal schema", dt2), ("DT3", "deterministic reconstruction", dt3),
            ("DT4", "fact evidence source links", dt4), ("DT5", "approval evidence", dt5), ("DT6", "governance references", dt6),
            ("DT7", "material categories", dt7), ("DT8", "routine no spam", dt8), ("DT9", "contradiction", dt9),
            ("DT10", "supersession", dt10), ("DT11", "temporal reconstruction", dt11), ("DT12", "missing reference", dt12),
            ("DT13", "stale reference", dt13), ("DT14", "beginner WHY", dt14), ("DT15", "redaction", dt15),
            ("DT16", "integrity", dt16), ("DT17", "canonical eight", dt17), ("DT18", "Aesthetica separation", dt18),
            ("DT19", "backward compatibility", dt19), ("DT20", "invalid trace resilience", dt20), ("DT21", "JSON export", dt21),
            ("DT22", "Markdown export", dt22), ("DT23", "external dependency boundary", dt23), ("DT24", "existing regression", dt24),
        ]
        cases = [_case(case_id, name, fn) for case_id, name, fn in definitions]
        after_hashes = {name: _hash(repo_root / name) for name in before_hashes if (repo_root / name).is_file()}
        all_pass = all(item["status"] == "PASS" for item in cases)
        return {
            "schema": EVAL_SCHEMA,
            "evaluated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "status": "PASS" if all_pass else "BLOCKED",
            "cases": cases,
            "case_count": len(cases),
            "pass_count": sum(item["status"] == "PASS" for item in cases),
            "baseline_gap_confirmed": baseline_gap,
            "environment_isolation": {"protected_hashes_unchanged": before_hashes == after_hashes, "temporary_root": str(temp)},
            "canonical_safety": {"identities": list(trace.CANONICAL_IDENTITIES), "denominator": trace.CANONICAL_DENOMINATOR, "full_quorum": "8/8", "aesthetica_canonical": False},
            "external_dependencies": [],
        }


def render_report(result: dict[str, object]) -> str:
    lines = ["# P2P Native Decision Trace Evaluation", "", f"- Status: `{result.get('status')}`", f"- Cases: `{result.get('pass_count')}/{result.get('case_count')}`", ""]
    for item in result.get("cases", []):
        lines.append(f"- `{item.get('case_id')}` {item.get('status')}: {item.get('name')} — {item.get('notes')}")
    lines.extend(["", "## Safety", "", json.dumps(result.get("canonical_safety", {}), ensure_ascii=False, indent=2, sort_keys=True), ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    args = parser.parse_args(argv)
    result = run_evaluation(Path(args.root))
    if args.json_out:
        _write_json(Path(args.json_out).expanduser().resolve(), result)
    if args.markdown_out:
        path = Path(args.markdown_out).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
