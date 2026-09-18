#!/usr/bin/env python3
"""Validate a P2P Codex package or an installed project/user root."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tomllib
import types
import zlib
from pathlib import Path

EXPECTED_SKILLS = {
    "bb4pda",
    "notebook-pack",
    "p2p",
    "p2p-uiux",
    "p2p-atlas",
    "p2p-approval",
    "p2p-capsule",
    "p2p-chain",
    "p2p-download",
    "p2p-eval",
    "p2p-explore",
    "p2p-feedback",
    "p2p-idea",
    "p2p-karpathy",
    "p2p-metrics",
    "p2p-pxpipe",
    "p2p-quorum",
    "p2p-scope",
    "p2p-teacher",
    "pxpipe",
    "rag-grounding",
    "rag-prep",
    "rag-router",
    # P2P_FRONTEND_UPSTREAM_INTAKE_01: first curated frontend capability pack.
    # Mirrors RELEASE_SKILLS in scripts/package_release.py.
    "frontend-design",
    "frontend-development",
    "react-best-practices",
    "composition-patterns",
    "frontend-code-review",
    "baseline-ui",
    "react-doctor",
}

# Install-directory -> additional accepted SKILL.md frontmatter `name` values.
# Vendored upstream skills keep their authoritative upstream frontmatter name
# (byte-identical intake); the install directory is P2P's stable path. The
# frontend-development alias is a pre-existing P2P identity (frontmatter
# `frontend-dev-guidelines`), preserved, not introduced, by this task.
SKILL_NAME_ALIASES = {
    "react-best-practices": {"vercel-react-best-practices"},
    "composition-patterns": {"vercel-composition-patterns"},
    "frontend-development": {"frontend-dev-guidelines"},
}

EXPECTED_AGENTS = {
    "p2p_anon",
    "p2p_architecton",
    "p2p_axiom",
    "p2p_datos",
    "p2p_helios",
    "p2p_iris",
    "p2p_tecton",
    "p2p_vector",
}
EXPECTED_OPTIONAL_AGENTS = {"p2p_aesthetica"}
DOCTOR_ROLES = ("auto", "development", "portable", "installed")

BASELINE_ZIP_SHA256 = "cafa5bbfa48048a9f2e6c54f6cfc329d2b25b34ea764809175dbae0e8f233fd8"
SUPPLEMENTAL_CATALOG_SHA256 = "90d1cd03d15667b5aa8ec12ded6245fe84f5aacd9de478f09f5777301e829341"


class Report:
    def __init__(self) -> None:
        self.items: list[dict[str, str]] = []

    def add(self, level: str, check: str, message: str) -> None:
        self.items.append({"level": level, "check": check, "message": message})

    def pass_(self, check: str, message: str) -> None:
        self.add("PASS", check, message)

    def fail(self, check: str, message: str) -> None:
        self.add("FAIL", check, message)

    def warn(self, check: str, message: str) -> None:
        self.add("WARN", check, message)

    @property
    def failed(self) -> bool:
        return any(item["level"] == "FAIL" for item in self.items)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_skill(path: Path) -> tuple[str | None, str | None]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None, None
    header = text[4:end]
    name_match = re.search(r"(?m)^name:\s*([^\n]+)$", header)
    description_match = re.search(r"(?m)^description:\s*(.*)$", header)
    return (
        name_match.group(1).strip().strip('"\'') if name_match else None,
        description_match.group(1).strip() if description_match else None,
    )


def find_layout(root: Path) -> tuple[Path, Path, Path, Path | None]:
    skills = root / ".agents" / "skills"
    agents = root / ".codex" / "agents"
    config = root / ".codex" / "config.toml"
    instructions = root / "AGENTS.md"
    if not skills.exists() and (root / ".agents" / "skills").exists():
        skills = root / ".agents" / "skills"
    if not instructions.exists():
        candidate = root / ".codex" / "AGENTS.md"
        instructions = candidate if candidate.exists() else instructions
    return skills, agents, config, instructions if instructions.exists() else None


def infer_role(root: Path) -> str:
    """Identify the filesystem contract without treating roles as interchangeable."""
    if (root / "runtime").is_dir() and (root / "release-manifest.json").is_file():
        return "portable"
    if (
        (root / "governance").is_dir()
        and (root / "manifest" / "package.json").is_file()
        and (root / "scripts" / "package_release.py").is_file()
    ):
        return "development"
    if (root / ".p2p" / "system").is_dir():
        return "installed"
    return "unknown"


def check_skills(root: Path, report: Report) -> None:
    skills, _, _, _ = find_layout(root)
    if not skills.is_dir():
        report.fail("skills-dir", f"Missing skills directory: {skills}")
        return
    found = {path.name for path in skills.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
    missing = EXPECTED_SKILLS - found
    extra = found - EXPECTED_SKILLS
    if missing:
        report.fail("skills-count", f"Missing skills: {', '.join(sorted(missing))}")
    else:
        report.pass_("skills-count", f"All {len(EXPECTED_SKILLS)} expected skills are present")
    if extra:
        report.warn("skills-extra", f"Additional skills are present: {', '.join(sorted(extra))}")
    for name in sorted(EXPECTED_SKILLS & found):
        actual, description = parse_skill(skills / name / "SKILL.md")
        accepted = {name} | SKILL_NAME_ALIASES.get(name, set())
        if actual not in accepted:
            report.fail(f"skill:{name}", f"Frontmatter name is {actual!r}")
        elif description is None:
            report.fail(f"skill:{name}", "Frontmatter description is missing")


def check_agents(root: Path, report: Report) -> None:
    _, agents, _, _ = find_layout(root)
    if not agents.is_dir():
        report.fail("agents-dir", f"Missing custom-agent directory: {agents}")
        return
    names: dict[str, str] = {}
    for path in sorted(agents.glob("p2p-*.toml")):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            report.fail(f"agent:{path.name}", f"Invalid TOML: {exc}")
            continue
        if path.name == "p2p-aesthetica.toml" or data.get("name") == "p2p_aesthetica":
            required_fields = ("name", "description", "developer_instructions", "sandbox_mode")
        else:
            required_fields = ("name", "description", "developer_instructions")
        missing = [key for key in required_fields if not data.get(key)]
        if missing:
            report.fail(f"agent:{path.name}", f"Missing fields: {', '.join(missing)}")
            continue
        names[str(data["name"])] = path.name
        if data.get("sandbox_mode") != "read-only":
            report.warn(f"agent:{path.name}:sandbox", "Agent is not configured read-only")
    missing_names = EXPECTED_AGENTS - names.keys()
    if missing_names:
        report.fail("agents-count", f"Missing agent names: {', '.join(sorted(missing_names))}")
    else:
        report.pass_("agents-count", "All eight custom P2P agent profiles parse correctly")
    missing_optional = EXPECTED_OPTIONAL_AGENTS - names.keys()
    if missing_optional:
        report.fail("optional-agents", f"Missing optional specialist profiles: {', '.join(sorted(missing_optional))}")
    else:
        report.pass_("optional-agents", "The real optional Aesthetica profile is present and separate from the canonical set")


def check_config(root: Path, report: Report) -> None:
    _, _, config, _ = find_layout(root)
    if not config.is_file():
        report.fail("config", f"Missing config: {config}")
        return
    try:
        data = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        report.fail("config", f"Invalid TOML: {exc}")
        return
    agents = data.get("agents", {})
    if agents.get("enabled", True) is not True:
        report.fail("config-agents-enabled", "agents.enabled is not true")
    else:
        report.pass_("config-agents-enabled", "Multi-agent tools are enabled")
    limit = agents.get("max_concurrent_threads_per_session", agents.get("max_threads"))
    if not isinstance(limit, int) or limit < 8:
        report.fail("config-agent-limit", f"Agent thread limit is {limit!r}; expected at least 8")
    else:
        report.pass_("config-agent-limit", f"Agent thread limit is {limit}")


def check_instructions(root: Path, report: Report) -> None:
    _, _, _, instructions = find_layout(root)
    if instructions is None:
        report.warn("instructions", "No AGENTS.md was found; skills still work, but project safeguards may not load")
        return
    text = instructions.read_text(encoding="utf-8", errors="replace")
    if "P2P" in text and "QUORUM" in text:
        report.pass_("instructions", f"P2P guidance found in {instructions}")
    else:
        report.warn("instructions", f"{instructions} exists but does not contain the P2P guidance block")


def _decode_helper_stream(value: bytes | str | None, stream_name: str) -> tuple[str, str | None]:
    """Decode a governance helper stream strictly at the process boundary."""
    if value is None:
        return "", None
    if isinstance(value, str):
        return value, None
    try:
        return value.decode("utf-8"), None
    except UnicodeDecodeError as exc:
        return "", f"{stream_name} is not valid UTF-8 at byte {exc.start}: {exc.reason}"


def check_governance(root: Path, report: Report, package_mode: bool) -> None:
    if package_mode:
        governance = root / "governance"
        helper = root / "scripts" / "p2p_governance.py"
    else:
        governance = root / ".p2p" / "system" / "governance"
        helper = root / ".p2p" / "system" / "scripts" / "p2p_governance.py"
    required = {
        "fact-ledger.json",
        "fact-ledger.schema.json",
        "live-specs.json",
        "live-specs.lock.json",
        "live-specs-preview-report.json",
        "drift-policy.json",
        "eval-suite.schema.json",
        "project-eval.template.json",
        "rag-retrieval-check.template.json",
        "rag-retrieval-check.schema.json",
        "approval-policy.json",
        "approval-record.schema.json",
        "project-policy.template.json",
        "release-gates.schema.json",
        "runtime-manifest.lock.json",
    }
    missing = sorted(name for name in required if not (governance / name).is_file())
    if missing:
        report.fail("governance-files", f"Missing governance files: {', '.join(missing)}")
        return
    if not helper.is_file():
        report.fail("governance-helper", f"Missing drift helper: {helper}")
        return
    helper_env = os.environ.copy()
    helper_env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    result = subprocess.run(
        [
            sys.executable,
            str(helper),
            "drift",
            "--root",
            str(root),
            "--governance",
            str(governance),
        ],
        capture_output=True,
        text=False,
        env=helper_env,
        check=False,
    )
    stdout, stdout_error = _decode_helper_stream(result.stdout, "governance helper stdout")
    stderr, stderr_error = _decode_helper_stream(result.stderr, "governance helper stderr")
    decode_errors = [error for error in (stdout_error, stderr_error) if error]
    if decode_errors:
        report.fail("governance-drift", "; ".join(decode_errors))
        return
    if result.returncode == 0:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            report.fail("governance-drift", f"governance helper returned malformed JSON: {exc.msg}")
            return
        if not isinstance(payload, dict) or payload.get("schema_version") != "p2p-codex-drift-report/1" or payload.get("status") != "PASS":
            report.fail("governance-drift", "governance helper returned malformed success output")
            return
        report.pass_("governance-drift", "FACT_LEDGER approval, generated Live Specs, expiry, protected-runtime lock, and active-runtime drift gates pass")
    else:
        detail = (stdout or stderr or "governance helper returned nonzero without UTF-8 output").strip().replace("\n", " ")
        report.fail("governance-drift", detail[:800])

    helper_root = root / "scripts" if package_mode else root / ".p2p" / "system" / "scripts"
    for name in ("p2p_approval.py", "p2p_eval.py", "p2p_gate.py", "p2p_governance.py", "p2p_safe_installer.py", "p2p_workflow.py"):
        if (helper_root / name).is_file():
            report.pass_(f"helper:{name}", f"Protection helper exists: {name}")
        else:
            report.fail(f"helper:{name}", f"Missing protection helper: {helper_root / name}")

    if package_mode:
        policy_path = governance / "project-policy.template.json"
        eval_path = governance / "project-eval.template.json"
        if policy_path.is_file() and eval_path.is_file():
            report.pass_("project-guard-templates", "Project policy and eval v2 templates are present")
    else:
        policy_path = root / ".p2p" / "project-policy.json"
        if policy_path.is_file():
            report.pass_("project-policy", "Mandatory project protection policy is installed")
        else:
            report.fail("project-policy", f"Missing project protection policy: {policy_path}")
        eval_path = root / ".p2p" / "evals" / "suite.json"
        if not eval_path.is_file():
            report.warn("release-readiness", "BLOCKED until a real project eval suite is created and passes; ordinary P2P use remains available")
        else:
            result = subprocess.run(
                [sys.executable, str(helper_root / "p2p_eval.py"), "gate", "--suite", str(eval_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                report.pass_("release-readiness", "Project eval gate passes; final release still requires rollback, drift, and user approval")
            else:
                report.warn("release-readiness", "BLOCKED because the project eval gate is not PASS")


def check_uiux_payload(root: Path, report: Report) -> None:
    runtime = root / "runtime"
    required = (
        "VERSION",
        "p2p.manifest.json",
        "references/UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md",
        "docs/evals/p2p-uiux-eval-suite.json",
        "p2p_uiux/__init__.py",
        "scripts/p2p_uiux.py",
        "scripts/p2p_router.py",
        "scripts/p2p_uiux_governance.py",
        "scripts/p2p_uiux_eval.py",
        "scripts/p2p_uiux_eval_impl.py",
        "scripts/p2p_uiux_doctor.py",
        "scripts/p2p_uiux_drift_check.py",
        "scripts/p2p_uiux_secret_scan.py",
    )
    missing = [relative for relative in required if not (runtime / relative).is_file()]
    if missing:
        report.fail("uiux-runtime-payload", f"Missing UI/UX runtime payload paths: {', '.join(missing)}")
        return
    try:
        runtime_manifest = json.loads((runtime / "p2p.manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.fail("uiux-runtime-manifest", f"Invalid runtime manifest: {exc}")
        return
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if runtime_manifest.get("package_version") != version:
        report.fail("uiux-runtime-version", "Runtime capability version does not match full release VERSION")
    else:
        report.pass_("uiux-runtime-version", f"UI/UX runtime payload is bound to full release {version}")
    foundation_meta = runtime_manifest.get("capability_foundation")
    if not isinstance(foundation_meta, dict) or foundation_meta.get("canonical_denominator") != 8 or foundation_meta.get("full_quorum") != "8/8":
        report.fail("foundation-runtime-manifest", "Capability Foundation metadata is missing or changes the canonical quorum contract")
    else:
        report.pass_("foundation-runtime-manifest", "Capability Foundation metadata preserves canonical 8/8 and optional-provider independence")
    provenance = (runtime / "references/UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md").read_text(encoding="utf-8").lower()
    if "abb7f2fd5a083fa1ff55c326a963ff0d95c33f99" not in provenance or "mit" not in provenance:
        report.fail("uiux-provenance", "Pinned UI/UX upstream provenance is missing or incomplete")
    else:
        report.pass_("uiux-provenance", "Pinned UI/UX provenance and MIT attribution are present")
    report.pass_("uiux-runtime-payload", "Full release contains the UI/UX runtime payload and evaluator suite")


def _foundation_required_paths(base: Path) -> tuple[str, ...]:
    return (
        "p2p_capabilities/__init__.py",
        "p2p_capabilities/beginner.py",
        "p2p_capabilities/context.py",
        "p2p_capabilities/domain.py",
        "p2p_capabilities/evidence.py",
        "p2p_capabilities/foreground_execution.py",
        "p2p_capabilities/bounded_delegation.py",
        "p2p_capabilities/parallel_execution.py",
        "p2p_capabilities/isolation.py",
        "p2p_capabilities/model.py",
        "p2p_capabilities/providers.py",
        "p2p_capabilities/routing.py",
        "p2p_capabilities/skill_standard.py",
        "p2p_capabilities/specialist.py",
        "p2p_capabilities/trust.py",
        "p2p_capabilities/decision_trace.py",
        "p2p_capabilities/project_pin.py",
        "p2p_capabilities/project_context.py",
        "p2p_capabilities/project_map.py",
        "p2p_capabilities/capabilities.json",
        "scripts/p2p_capability_doctor.py",
        "scripts/p2p_decision_trace.py",
    )


def _run_foundation_doctor(source: Path, profile_root: Path) -> tuple[bool, str]:
    doctor = source / "scripts" / "p2p_capability_doctor.py"
    result = subprocess.run(
        [
            sys.executable,
            str(doctor),
            "--source",
            str(source),
            "--profile-root",
            str(profile_root),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    detail = (result.stdout or result.stderr).strip().replace("\n", " ")
    return result.returncode == 0, detail[:1000]


def _run_decision_trace_doctor(source: Path, project_root: Path) -> tuple[bool, str]:
    doctor = source / "scripts" / "p2p_decision_trace.py"
    result = subprocess.run(
        [sys.executable, str(doctor), "--project", str(project_root), "doctor", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    detail = (result.stdout or result.stderr).strip().replace("\n", " ")
    if result.returncode:
        return False, detail[:1000]
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, "Decision Trace doctor did not return JSON"
    if not isinstance(payload, dict):
        return False, "Decision Trace doctor returned a non-object payload"
    if payload.get("status") not in {"PASS", "NOT_INITIALIZED"}:
        return False, detail[:1000]
    if payload.get("canonical_denominator") != 8 or payload.get("full_quorum") != "8/8":
        return False, "Decision Trace doctor changed the canonical 8/8 governance contract"
    if payload.get("aesthetica_canonical") is not False:
        return False, "Decision Trace doctor changed Aesthetica canonical classification"
    if payload.get("external_dependencies") != []:
        return False, "Decision Trace runtime declares external dependencies"
    return True, f"Decision Trace doctor PASS; trace_count={payload.get('trace_count', 0)}"


def check_decision_trace_payload(root: Path, report: Report, *, installed: bool) -> None:
    source = root / ".p2p" / "system" if installed else root / "runtime"
    required = (
        "p2p_capabilities/decision_trace.py",
        "scripts/p2p_decision_trace.py",
    )
    missing = [relative for relative in required if not (source / relative).is_file()]
    check_prefix = "installed-decision-trace" if installed else "decision-trace"
    if missing:
        report.fail(f"{check_prefix}-runtime-payload", f"Missing Decision Trace runtime paths: {', '.join(missing)}")
        return
    try:
        runtime_manifest = json.loads((source / "p2p.manifest.json").read_text(encoding="utf-8"))
        version = (source / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, json.JSONDecodeError) as exc:
        report.fail(f"{check_prefix}-manifest", f"Invalid Decision Trace runtime metadata: {exc}")
        return
    metadata = runtime_manifest.get("decision_trace")
    if (
        not isinstance(metadata, dict)
        or metadata.get("schema") != "p2p-decision-trace/1"
        or metadata.get("implementation") != "P2P_NATIVE"
        or metadata.get("runtime") != "p2p_capabilities/decision_trace.py"
        or metadata.get("cli") != "scripts/p2p_decision_trace.py"
        or metadata.get("storage") != ".p2p/state/execution-ledger.jsonl"
        or metadata.get("external_dependencies_required") is not False
    ):
        report.fail(f"{check_prefix}-manifest", "Decision Trace manifest metadata is missing or changes the native runtime contract")
    elif runtime_manifest.get("package_version") != version:
        report.fail(f"{check_prefix}-version", "Decision Trace runtime version does not match its manifest")
    else:
        report.pass_(f"{check_prefix}-manifest", f"Native Decision Trace is bound to runtime {version} and the existing execution ledger")
    ok, detail = _run_decision_trace_doctor(source, root)
    if ok:
        report.pass_(f"{check_prefix}-doctor", detail)
    else:
        report.fail(f"{check_prefix}-doctor", detail or "Decision Trace doctor failed")


def check_foundation_payload(root: Path, report: Report) -> None:
    runtime = root / "runtime"
    required = _foundation_required_paths(runtime)
    missing = [relative for relative in required if not (runtime / relative).is_file()]
    if missing:
        report.fail("foundation-runtime-payload", f"Missing capability foundation payload paths: {', '.join(missing)}")
        return
    ok, detail = _run_foundation_doctor(runtime, root / ".codex" / "agents")
    if ok:
        report.pass_("foundation-runtime", "Capability Foundation payload validates with canonical 8/8, optional specialist, trust, beginner, readiness, and provider gates")
    else:
        report.fail("foundation-runtime", detail or "Capability Foundation doctor failed")
    check_decision_trace_payload(root, report, installed=False)


def check_installed_foundation(root: Path, report: Report) -> None:
    system = root / ".p2p" / "system"
    required = _foundation_required_paths(system)
    missing = [relative for relative in required if not (system / relative).is_file()]
    if missing:
        report.fail("installed-foundation-payload", f"Missing installed capability foundation paths: {', '.join(missing)}")
        return
    ok, detail = _run_foundation_doctor(system, root / ".codex" / "agents")
    if ok:
        report.pass_("installed-foundation", "Installed Capability Foundation validates with canonical 8/8 and optional-provider independence")
    else:
        report.fail("installed-foundation", detail or "Installed Capability Foundation doctor failed")
    check_decision_trace_payload(root, report, installed=True)


def _load_installed_project_pin(system: Path):
    """Load the installed project-pin validator with real package context.

    ``project_pin.py`` uses package-relative imports, so loading it as a
    top-level module raises ``attempted relative import with no known parent
    package``.  Bind it to a doctor-private package alias whose ``__path__`` is
    the installed runtime directory only, so relative imports resolve against
    ``<target>/.p2p/system/p2p_capabilities`` and can never be satisfied by the
    P2P source checkout, another ``p2p_capabilities`` earlier on PYTHONPATH, or
    a module of that name cached from a previous root.
    """

    package_dir = system / "p2p_capabilities"
    module_path = package_dir / "project_pin.py"
    package_name = "p2p_installed_p2p_capabilities"
    for cached in [
        name
        for name in sys.modules
        if name == package_name or name.startswith(f"{package_name}.")
    ]:
        del sys.modules[cached]
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_dir)]
    package.__package__ = package_name
    sys.modules[package_name] = package
    spec = importlib.util.spec_from_file_location(f"{package_name}.project_pin", module_path)
    if spec is None or spec.loader is None:
        return None, module_path
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, module_path


def check_project_pin(root: Path, report: Report) -> None:
    """Validate the installed project binding through the canonical runtime."""

    system = root / ".p2p" / "system"
    module_path = system / "p2p_capabilities" / "project_pin.py"
    if not module_path.is_file():
        report.fail("project-pin", f"Missing canonical project-pin validator: {module_path}")
        return
    try:
        module, expected_path = _load_installed_project_pin(system)
    except Exception as exc:
        report.fail("project-pin", str(exc))
        return
    if module is None:
        report.fail("project-pin", "Could not load canonical project-pin validator")
        return
    loaded = getattr(module, "__file__", "")
    if not loaded or Path(loaded).resolve() != expected_path.resolve():
        report.fail(
            "project-pin",
            f"project-pin validator did not resolve from the installed runtime: {loaded or '<unknown>'}",
        )
        return
    try:
        result = module.validate_pin(root, metadata_root=system)
    except Exception as exc:
        report.fail("project-pin", str(exc))
        return
    report.pass_("project-pin", f"Project pin is verified for {result['candidate_version']} and the installed source binding")


def _load_package_release_contract(root: Path):
    package_release = root / "scripts" / "package_release.py"
    if not package_release.is_file():
        return None
    spec = importlib.util.spec_from_file_location("p2p_package_release_contract", package_release)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_development(root: Path, report: Report) -> None:
    """Validate the development checkout using its source-owned runtime paths."""
    check_governance(root, report, package_mode=True)
    package_manifest = root / "manifest" / "package.json"
    version_path = root / "VERSION"
    if not package_manifest.is_file() or not version_path.is_file():
        report.fail("development-package-metadata", "Development checkout is missing VERSION or manifest/package.json")
    else:
        try:
            manifest = json.loads(package_manifest.read_text(encoding="utf-8"))
            version = version_path.read_text(encoding="utf-8").strip()
        except (OSError, json.JSONDecodeError) as exc:
            report.fail("development-package-metadata", f"Invalid development package metadata: {exc}")
        else:
            if manifest.get("version") != version:
                report.fail("development-package-metadata", "VERSION and manifest/package.json differ")
            else:
                report.pass_("development-package-metadata", f"Development source metadata is bound to {version}")

    package_release = _load_package_release_contract(root)
    if package_release is None:
        report.fail("development-package-contract", "Cannot load scripts/package_release.py for source-owned runtime validation")
    else:
        try:
            package_release.validate_uiux_runtime(root)
            package_release.validate_foundation_runtime(root)
        except (OSError, ValueError, RuntimeError) as exc:
            report.fail("development-runtime-contract", str(exc))
        else:
            report.pass_("development-runtime-contract", "Development runtime source satisfies the package builder's UI/UX and Capability Foundation contracts")

    runtime = root / ".p2p" / "system"
    uiux_doctor = runtime / "scripts" / "doctor.py"
    if not uiux_doctor.is_file():
        report.fail("development-uiux-runtime", f"Missing development UI/UX doctor: {uiux_doctor}")
    else:
        result = subprocess.run(
            [sys.executable, str(uiux_doctor), "--source", str(runtime)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            report.pass_("development-uiux-runtime", "Development UI/UX runtime doctor passes against .p2p/system")
        else:
            detail = (result.stdout or result.stderr).strip().replace("\n", " ")
            report.fail("development-uiux-runtime", detail[:800] or "Development UI/UX runtime doctor failed")
    check_installed_foundation(root, report)


def check_package(root: Path, report: Report) -> None:
    check_uiux_payload(root, report)
    check_foundation_payload(root, report)
    source = root / "source" / "8.4.6-C"
    if not source.is_dir():
        report.fail("source", f"Missing baseline source snapshot: {source}")
    else:
        files = [path for path in source.rglob("*") if path.is_file()]
        if len(files) == 152:
            report.pass_("source-count", "Baseline source inventory is 152/152")
        else:
            report.fail("source-count", f"Baseline source contains {len(files)} files, expected 152")
    original_zip = root / "source" / "releases" / "8.4.6-C-original.zip"
    if not original_zip.is_file():
        report.fail("source-zip", f"Missing original release ZIP: {original_zip}")
    else:
        actual = sha256(original_zip)
        if actual == BASELINE_ZIP_SHA256:
            report.pass_("source-zip", "Original release ZIP SHA-256 matches baseline")
        else:
            report.fail("source-zip", f"ZIP SHA-256 mismatch: {actual}")
    catalog = root / "source" / "supplemental" / "P2P-overview-architecture-catalog.ru.txt"
    if not catalog.is_file():
        report.fail("supplemental-catalog", f"Missing supplemental catalog: {catalog}")
    else:
        expected_hash = SUPPLEMENTAL_CATALOG_SHA256
        checksum_path = root / "governance" / "supplemental-checksums.json"
        if checksum_path.is_file():
            try:
                checksums = json.loads(checksum_path.read_text(encoding="utf-8"))
                valid_record = (
                    isinstance(checksums, dict)
                    and checksums.get("schema_version") == "p2p-release-supplemental-checksums/1"
                    and checksums.get("subject")
                    == "source/supplemental/P2P-overview-architecture-catalog.ru.txt"
                    and isinstance(checksums.get("sha256"), str)
                    and len(checksums["sha256"]) == 64
                )
                if not valid_record:
                    report.fail("supplemental-catalog", "Supplemental checksum record has the wrong schema")
                else:
                    expected_hash = checksums["sha256"]
            except (OSError, json.JSONDecodeError):
                report.fail("supplemental-catalog", "Supplemental checksum record is unreadable")
        if sha256(catalog) != expected_hash:
            report.fail("supplemental-catalog", "Supplemental catalog SHA-256 mismatch")
        else:
            report.pass_("supplemental-catalog", "User-supplied catalog snapshot matches its locked SHA-256")
    external_manifest = root / "manifest" / "external-sources.json"
    if not external_manifest.is_file():
        report.fail("external-sources", f"Missing {external_manifest}")
    else:
        try:
            external_data = json.loads(external_manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.fail("external-sources", f"Invalid external-source manifest: {exc}")
        else:
            external_items = external_data.get("sources", []) if isinstance(external_data, dict) else []
            expected_external_ids = {f"P2P-EXT-{index:04d}" for index in range(1, 6)}
            actual_external_ids = {str(item.get("source_id", "")) for item in external_items if isinstance(item, dict)}
            if (
                external_data.get("schema_version") != "p2p-codex-external-sources/1"
                or actual_external_ids != expected_external_ids
            ):
                report.fail("external-sources", "External-source schema or IDs are incomplete")
            else:
                mismatches = []
                for item in external_items:
                    stored_path = item.get("stored_path")
                    expected_hash = item.get("sha256")
                    if not stored_path:
                        continue
                    stored_file = root / str(stored_path)
                    if not stored_file.is_file():
                        mismatches.append(f"{item.get('source_id')}:missing")
                    elif expected_hash and sha256(stored_file) != expected_hash:
                        mismatches.append(f"{item.get('source_id')}:hash")
                if mismatches:
                    report.fail("external-sources", f"Supplemental snapshot mismatches: {', '.join(mismatches)}")
                else:
                    report.pass_("external-sources", "Five external sources are identified; four stored snapshots match")
    inventory = root / "manifest" / "source-inventory.json"
    conversion = root / "manifest" / "conversion-map.csv"
    inventory_items: list[dict] = []
    if inventory.is_file():
        try:
            items = json.loads(inventory.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.fail("source-manifest", f"Invalid source manifest: {exc}")
        else:
            if isinstance(items, list) and len(items) == 152:
                report.pass_("source-manifest", "Machine inventory contains 152 records")
                inventory_items = items
            else:
                report.fail("source-manifest", "Machine inventory does not contain 152 records")
    else:
        report.fail("source-manifest", f"Missing {inventory}")
    if inventory_items:
        bad_inventory: list[str] = []
        expected_ids = {f"P2P-FILE-{index:04d}" for index in range(1, 153)}
        actual_ids = {str(item.get("stable_id", "")) for item in inventory_items}
        if actual_ids != expected_ids:
            report.fail("source-stable-ids", "Stable IDs are not exactly P2P-FILE-0001 through P2P-FILE-0152")
        else:
            report.pass_("source-stable-ids", "All 152 stable source IDs are present")
        for item in inventory_items:
            snapshot = root / str(item.get("source_snapshot_path", ""))
            if not snapshot.is_file():
                bad_inventory.append(f"{item.get('stable_id')}:missing")
                continue
            data = snapshot.read_bytes()
            actual_crc = f"{zlib.crc32(data) & 0xFFFFFFFF:08X}"
            if (
                len(data) != item.get("size")
                or actual_crc != item.get("crc32")
                or hashlib.sha256(data).hexdigest() != item.get("sha256")
            ):
                bad_inventory.append(f"{item.get('stable_id')}:hash")
        if bad_inventory:
            report.fail("source-hashes", f"Source inventory mismatches: {', '.join(bad_inventory[:8])}")
        else:
            report.pass_("source-hashes", "All 152 source files match size, CRC32, and SHA-256")
    if conversion.is_file():
        try:
            with conversion.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
        except (OSError, csv.Error) as exc:
            report.fail("conversion-map", f"Invalid conversion map: {exc}")
            rows = []
        if len(rows) == 152:
            report.pass_("conversion-map", "Conversion map contains 152 source rows")
            missing_targets = []
            for row in rows:
                target = row.get("actual_codex_target", "").strip()
                if target and not (root / target).is_file():
                    missing_targets.append(f"{row.get('stable_id')}:{target}")
            if missing_targets:
                report.fail("conversion-targets", f"Mapped Codex targets are missing: {', '.join(missing_targets[:8])}")
            else:
                report.pass_("conversion-targets", "Every declared Codex runtime target exists")
        else:
            report.fail("conversion-map", f"Conversion map has {len(rows)} data rows")
    else:
        report.fail("conversion-map", f"Missing {conversion}")
    package_manifest = root / "manifest" / "package.json"
    if not package_manifest.is_file():
        report.fail("package-manifest", f"Missing {package_manifest}")
    else:
        try:
            data = json.loads(package_manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.fail("package-manifest", f"Invalid package manifest: {exc}")
        else:
            if data.get("schema_version") == "p2p-codex-project-bundle/1":
                report.pass_("package-manifest", "Package manifest schema is valid")
            else:
                report.fail("package-manifest", "Unexpected package manifest schema")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", help="Path to the unpacked P2P Codex package")
    parser.add_argument("--root", help="Installed project root or user home")
    parser.add_argument("--role", choices=DOCTOR_ROLES, default="auto", help="Filesystem contract to validate")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()
    if bool(args.package) == bool(args.root):
        parser.error("provide exactly one of --package or --root")
    root = Path(args.package or args.root).expanduser().resolve()
    report = Report()
    detected_role = infer_role(root)
    role = ("portable" if args.package else detected_role) if args.role == "auto" else args.role
    if not root.is_dir():
        report.fail("root", f"Directory does not exist: {root}")
    elif detected_role == "unknown":
        report.fail("role", f"Could not identify a supported P2P filesystem role for {root}")
    elif role != detected_role:
        report.fail("role", f"Requested role {role!r} does not match detected role {detected_role!r} for {root}")
    else:
        check_skills(root, report)
        check_agents(root, report)
        check_config(root, report)
        check_instructions(root, report)
        if role == "portable":
            check_package(root, report)
        elif role == "development":
            check_development(root, report)
        elif role == "installed":
            check_governance(root, report, package_mode=False)
            check_installed_foundation(root, report)
            check_project_pin(root, report)
    if args.strict and any(item["level"] == "WARN" for item in report.items):
        report.fail("strict-warnings", "Strict Doctor rejects WARN results; complete project-owned eval/context setup first")
    if args.json:
        print(json.dumps({"root": str(root), "role": role, "detected_role": detected_role, "ok": not report.failed, "checks": report.items}, ensure_ascii=False, indent=2))
    else:
        for item in report.items:
            print(f"[{item['level']}] {item['check']}: {item['message']}")
        print("RESULT:", "PASS" if not report.failed else "FAIL")
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
