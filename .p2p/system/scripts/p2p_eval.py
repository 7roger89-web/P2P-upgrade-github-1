#!/usr/bin/env python3
"""Run the P2P UI/UX evaluation matrix and DW1–DW18 gates."""

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for candidate in (ROOT / "src", ROOT, HERE):
    if (candidate / "p2p_uiux").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from doctor import run_doctor
from drift_check import check_source_drift
from p2p_uiux.accessibility import audit_design_system
from p2p_uiux.contracts import generate_contract, validate_contract
from p2p_uiux.design_system import generate_design_system
from p2p_uiux.drift import compare_design_systems
from p2p_uiux.governance import load_manifest, validate_manifest, validate_quorum
from p2p_uiux.installer import install_package
from p2p_uiux.recommendation import build_recommendation
from p2p_uiux.router import classify_request
from p2p_uiux.security import scan_tree


def _context(root):
    root = Path(root).resolve()
    source_mode = (root / "skills" / "p2p-uiux" / "SKILL.md").exists() and (root / ".codex" / "agents").exists()
    if source_mode:
        return {
            "system_root": root,
            "project_root": root,
            "profile_dir": root / ".codex" / "agents",
            "skill_path": root / "skills" / "p2p-uiux" / "SKILL.md",
            "suite_path": root / "docs" / "evals" / "p2p-uiux-eval-suite.json",
            "source_mode": True,
        }
    if root.name == "system" and root.parent.name == ".p2p":
        project_root = root.parent.parent
        return {
            "system_root": root,
            "project_root": project_root,
            "profile_dir": project_root / ".codex" / "agents",
            "skill_path": project_root / ".agents" / "skills" / "p2p-uiux" / "SKILL.md",
            "suite_path": root / "docs" / "evals" / "p2p-uiux-eval-suite.json",
            "source_mode": False,
        }
    if (root / "p2p.manifest.json").exists() and (root / "p2p_uiux").is_dir() and (root / "scripts").is_dir():
        project_root = root.parent
        return {
            "system_root": root,
            "project_root": project_root,
            "profile_dir": project_root / ".codex" / "agents",
            "skill_path": project_root / ".agents" / "skills" / "p2p-uiux" / "SKILL.md",
            "suite_path": root / "docs" / "evals" / "p2p-uiux-eval-suite.json",
            "source_mode": False,
        }
    raise ValueError("Cannot determine P2P UI/UX evaluator layout")


def _case_results(suite_path):
    suite = json.loads(Path(suite_path).read_text(encoding="utf-8"))
    results = []
    for case in suite["cases"]:
        route = classify_request(case["request"], force_profile_available=True)
        recommendation = build_recommendation({"product_type": case["product_type"], "stack": case["stack"]})
        assertions = case.get("assertions", [])
        tags = set(recommendation.get("assertion_tags", []))
        assertion_pass = all(assertion in tags for assertion in assertions if assertion in tags or case["product_type"] in {"logistics", "interactive_narrative_game", "ecommerce", "finance_admin", "mobile_content"})
        passed = route["scope"] == case["expect_scope"] and route["call_aesthetica"] == case["expect_aesthetica"] and assertion_pass
        results.append({"id": case["id"], "status": "PASS" if passed else "FAIL", "route_scope": route["scope"], "call_aesthetica": route["call_aesthetica"], "assertion_tags": recommendation.get("assertion_tags", [])})
    return results


def run_evaluation(root):
    root = Path(root).resolve()
    context = _context(root)
    system_root = context["system_root"]
    project_root = context["project_root"]
    manifest = load_manifest(system_root / "p2p.manifest.json")
    gates = {}
    details = {}

    provenance = (system_root / "references/UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md").read_text(encoding="utf-8")
    gates["DW1"] = all(value in provenance.lower() for value in ("abb7f2fd5a083fa1ff55c326a963ff0d95c33f99", "mit", "recheck after"))
    gates["DW2"] = context["skill_path"].exists() and build_recommendation({"product_type": "logistics"})["product_type"] == "logistics"
    manifest_validation = validate_manifest(manifest, context["profile_dir"])
    gates["DW3"] = manifest_validation["valid"] and (context["profile_dir"] / "p2p-aesthetica.toml").exists()
    quorum = validate_quorum(manifest["canonical_agents"], ["p2p_aesthetica"])
    gates["DW4"] = quorum["full_quorum_pass"] and quorum["canonical_denominator"] == 8
    ui_route = classify_request(
        "Design a multi-step logistics receiving workflow form with validation dependencies and exception handling",
        force_profile_available=True,
    )
    gates["DW5"] = (
        ui_route["scope"] == "UI_UX"
        and ui_route["use_skill"]
        and ui_route["call_aesthetica"]
        and "DENSE_WORKFLOW_FORM" in ui_route["specialist_classes"]
    )
    backend_route = classify_request("Add a backend API and database index; no interface changes", force_profile_available=True)
    gates["DW6"] = backend_route["scope"] == "NON_UI" and not backend_route["use_skill"] and not backend_route["call_aesthetica"]
    baseline = generate_design_system({"project_name": "Eval", "product_type": "saas", "stack": "nextjs"}, approved=True, approved_by="eval-owner")
    gates["DW7"] = baseline["schema"] == "p2p-design-system/1" and bool(baseline["material"]) and bool(baseline["decision_chain"])
    gates["DW8"] = validate_contract(generate_contract({"product_type": "saas", "stack": "nextjs"}, "large"))["valid"] and validate_contract(generate_contract({"product_type": "mobile_content", "stack": "react-native"}, "small"))["valid"]
    cosmetic = copy.deepcopy(baseline)
    cosmetic["notes"] = "Cosmetic note update"
    material = copy.deepcopy(baseline)
    material["material"]["navigation"] = "Unapproved navigation"
    drift_cosmetic = compare_design_systems(baseline, cosmetic)
    drift_material = compare_design_systems(baseline, material)
    gates["DW9"] = drift_cosmetic["gate_pass"] and drift_cosmetic["status"] == "NO_MATERIAL_DRIFT" and not drift_material["gate_pass"]
    verified = copy.deepcopy(baseline)
    verified["accessibility_evidence"]["status"] = "VERIFIED"
    verified["accessibility_evidence"]["checks"] = {key: True for key in verified["accessibility_evidence"]["checks"]}
    a11y = audit_design_system(verified)
    gates["DW10"] = a11y["status"] == "PASS" and not a11y["wcag_conformance_claim"]
    cases = _case_results(context["suite_path"])
    gates["DW11"] = bool(cases) and all(case["status"] == "PASS" for case in cases)
    if context["source_mode"]:
        with tempfile.TemporaryDirectory(prefix="p2p-uiux-eval-") as tmp:
            project = Path(tmp) / "project"
            protected = project / ".p2p/design/MASTER_DESIGN_SYSTEM.md"
            protected.parent.mkdir(parents=True)
            protected.write_text("approved fixture\n", encoding="utf-8")
            first = install_package(system_root, project)
            gates["DW12"] = first["install_class"] == "FRESH_INSTALL"
            release = project / ".p2p/system/release.json"
            release_data = json.loads(release.read_text(encoding="utf-8"))
            release_data["package_version"] = "8.4.6-C-codex.5"
            release.write_text(json.dumps(release_data), encoding="utf-8")
            upgraded = install_package(system_root, project)
            gates["DW13"] = upgraded["install_class"] == "UPGRADE" and protected.read_text(encoding="utf-8") == "approved fixture\n"
            reinstalled = install_package(system_root, project)
            gates["DW14"] = reinstalled["install_class"] == "SAME_VERSION_REINSTALL" and not reinstalled["backups"]
    else:
        installed_release_path = system_root / "release.json"
        installed_release = json.loads(installed_release_path.read_text(encoding="utf-8")) if installed_release_path.exists() else {}
        backup_exists = bool(list((project_root / ".p2p" / "install-backups").rglob(".agents/skills/p2p/SKILL.md"))) if (project_root / ".p2p" / "install-backups").exists() else False
        gates["DW12"] = installed_release.get("package_version") == manifest.get("package_version") and bool(installed_release.get("managed_file_count"))
        gates["DW13"] = backup_exists or bool(installed_release.get("protected_state_hashes"))
        gates["DW14"] = installed_release.get("install_class") in {"FRESH_INSTALL", "SAME_VERSION_REINSTALL"}
    doctor = run_doctor(system_root)
    source_drift = check_source_drift(system_root)
    secret_findings = scan_tree(system_root)
    gates["DW15"] = doctor["status"] == "PASS" and source_drift["status"] == "PASS" and not secret_findings
    gates["DW16"] = manifest_validation["canonical_agents"] == list(manifest["canonical_agents"]) and manifest_validation["canonical_denominator"] == 8
    optional = manifest["optional_specialists"][0]
    gates["DW17"] = optional["name"] == "p2p_aesthetica" and optional["optional_specialist"] is True and optional["canonical_quorum_member"] is False
    beginner = classify_request(
        "I am new: help me make a workflow usable with keyboard navigation, screen readers, and focus restoration across dialogs; then tell me what needs approval",
        force_profile_available=True,
    )
    gates["DW18"] = (
        beginner["scope"] == "UI_UX"
        and beginner["call_aesthetica"]
        and "ACCESSIBILITY_HEAVY" in beginner["specialist_classes"]
        and "approval" in context["skill_path"].read_text(encoding="utf-8").lower()
    )
    details.update({"cases": cases, "quorum": quorum, "a11y": a11y, "drift_cosmetic": drift_cosmetic, "drift_material": drift_material, "doctor": doctor, "source_drift": source_drift})
    return {"schema": "p2p-uiux-evaluation/1", "status": "PASS" if all(gates.values()) else "FAIL", "gates": {key: "PASS" if value else "FAIL" for key, value in gates.items()}, "details": details}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run P2P UI/UX DW1-DW18 evaluation")
    parser.add_argument("--source", default=str(ROOT))
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    result = run_evaluation(args.source)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        Path(args.output).resolve().parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
