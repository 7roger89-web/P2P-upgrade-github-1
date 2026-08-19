#!/usr/bin/env python3
"""Build expiring Live Specs from FACT_LEDGER and enforce release drift gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

from p2p_approval import validate_policy as validate_approval_policy
from p2p_approval import validate_record as validate_approval_record


LEDGER_SCHEMA = "p2p-codex-fact-ledger/2"
LIVE_SCHEMA = "p2p-codex-live-specs/2"
LOCK_SCHEMA = "p2p-codex-live-specs-lock/3"
LIVE_PREVIEW_SCHEMA = "p2p-codex-live-preview-report/1"
RUNTIME_LOCK_SCHEMA = "p2p-codex-runtime-manifest-lock/1"
EVIDENCE_LEVELS = {"A", "B", "C", "D"}
SOURCE_TYPES = {"official", "benchmark", "reproducible_issue", "community", "legacy"}
ROUTE_ACTIONS = {"block", "warn", "prefer", "monitor", "ignore"}
VERIFICATION_STATUSES = {
    "CONFIRMED_ACTIVE", "NOT_RECHECKED", "NO_EVIDENCE_OF_FIX", "DISPUTED", "RETIRED"
}


class GovernanceError(ValueError):
    pass


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceError(f"Cannot read JSON {path}: {exc}") from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise GovernanceError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise GovernanceError(f"{field} is not an ISO date: {value!r}") from exc


def lifecycle(claim: dict, as_of: date, expiring_window: int) -> str:
    expiry = parse_date(claim.get("expires_at"), f"{claim.get('claim_id')}.expires_at")
    if as_of > expiry:
        return "stale"
    if (expiry - as_of).days <= expiring_window:
        return "expiring"
    return "current"


def validate_ledger(ledger: object, governance_dir: Path) -> list[str]:
    if not isinstance(ledger, dict) or ledger.get("schema_version") != LEDGER_SCHEMA:
        raise GovernanceError(f"FACT_LEDGER schema must be {LEDGER_SCHEMA}")
    revision = ledger.get("ledger_revision")
    updated_at = parse_date(ledger.get("updated_at"), "FACT_LEDGER.updated_at")
    change_control = ledger.get("change_control")
    policy = ledger.get("expiry_policy")
    claims = ledger.get("claims")
    if not isinstance(revision, int) or revision < 1:
        raise GovernanceError("FACT_LEDGER needs a positive ledger_revision")
    if not isinstance(change_control, dict):
        raise GovernanceError("FACT_LEDGER needs change_control")
    if (
        change_control.get("promotion_requires_user_approval") is not True
        or change_control.get("approval_action") != "promote_live_specs"
        or change_control.get("approval_policy") != "approval-policy.json"
        or change_control.get("generated_target") != "live-specs.json"
    ):
        raise GovernanceError("FACT_LEDGER change_control cannot weaken approval or generated-target rules")
    if not isinstance(policy, dict) or not isinstance(claims, list):
        raise GovernanceError("FACT_LEDGER needs expiry_policy and claims")
    window = policy.get("expiring_window_days")
    runtime_levels = policy.get("runtime_evidence_levels")
    max_age = policy.get("max_age_days_by_kind")
    if not isinstance(window, int) or window < 1:
        raise GovernanceError("expiring_window_days must be a positive integer")
    if not isinstance(runtime_levels, list) or not set(runtime_levels).issubset(EVIDENCE_LEVELS):
        raise GovernanceError("runtime_evidence_levels contains an invalid level")
    if not isinstance(max_age, dict) or not max_age:
        raise GovernanceError("expiry_policy.max_age_days_by_kind is required")
    for kind, days in max_age.items():
        if not isinstance(kind, str) or not isinstance(days, int) or days < 1:
            raise GovernanceError("expiry_policy.max_age_days_by_kind contains an invalid row")
    required = {
        "claim_id", "kind", "claim", "value", "scope", "source_url",
        "source_type", "evidence_level", "checked_at", "expires_at",
        "verification_status", "route_action", "runtime_eligible",
        "independence_key", "provenance_note", "risk_tier",
        "affected_components", "verification_method",
    }
    seen: set[str] = set()
    warnings: list[str] = []
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict) or not required.issubset(claim):
            raise GovernanceError(f"claim row {index} is missing required fields")
        claim_id = claim["claim_id"]
        if not isinstance(claim_id, str) or not re.fullmatch(r"P2P-FACT-[0-9]{4}", claim_id):
            raise GovernanceError(f"claim row {index} has invalid claim_id")
        if claim_id in seen:
            raise GovernanceError(f"duplicate claim_id: {claim_id}")
        seen.add(claim_id)
        if claim["source_type"] not in SOURCE_TYPES or claim["evidence_level"] not in EVIDENCE_LEVELS:
            raise GovernanceError(f"{claim_id} has invalid source/evidence classification")
        if claim["route_action"] not in ROUTE_ACTIONS or not isinstance(claim["runtime_eligible"], bool):
            raise GovernanceError(f"{claim_id} has invalid route_action/runtime_eligible")
        if claim["verification_status"] not in VERIFICATION_STATUSES:
            raise GovernanceError(f"{claim_id} has an invalid verification_status")
        if not isinstance(claim["independence_key"], str) or not claim["independence_key"].strip():
            raise GovernanceError(f"{claim_id} has no evidence independence key")
        checked = parse_date(claim["checked_at"], f"{claim_id}.checked_at")
        expires = parse_date(claim["expires_at"], f"{claim_id}.expires_at")
        if checked > updated_at:
            raise GovernanceError(f"{claim_id} was checked after FACT_LEDGER.updated_at")
        if expires < checked:
            raise GovernanceError(f"{claim_id} expires before it was checked")
        kind_limit = max_age.get(claim["kind"])
        if not isinstance(kind_limit, int):
            raise GovernanceError(f"{claim_id}: no maximum age is defined for kind {claim['kind']}")
        if (expires - checked).days > kind_limit:
            raise GovernanceError(f"{claim_id}: expiry exceeds the {kind_limit}-day limit for {claim['kind']}")
        if claim["risk_tier"] not in {"low", "medium", "high", "critical"}:
            raise GovernanceError(f"{claim_id}: invalid risk_tier")
        if not isinstance(claim["affected_components"], list) or not claim["affected_components"]:
            raise GovernanceError(f"{claim_id}: affected_components must be a non-empty list")
        if not isinstance(claim["verification_method"], str) or not claim["verification_method"].strip():
            raise GovernanceError(f"{claim_id}: verification_method is required")
        if claim["evidence_level"] == "A" and claim["source_type"] != "official":
            raise GovernanceError(f"{claim_id}: evidence A is reserved for official sources")
        if claim["route_action"] == "block" and not (
            claim["evidence_level"] == "A" and claim["source_type"] == "official"
        ):
            raise GovernanceError(f"{claim_id}: block requires official evidence level A")
        if claim["runtime_eligible"] and claim["evidence_level"] not in set(runtime_levels):
            raise GovernanceError(f"{claim_id}: runtime claim has a disallowed evidence level")
        if claim["runtime_eligible"] and claim["verification_status"] != "CONFIRMED_ACTIVE":
            raise GovernanceError(f"{claim_id}: runtime claim is not CONFIRMED_ACTIVE")
        source = str(claim["source_url"])
        if not source.startswith(("https://", "http://")):
            package_root = governance_dir.parent
            if not (package_root / source).exists():
                warnings.append(f"{claim_id}: preserved source path is not present in this installation")
    return warnings


def build_live(ledger: dict, ledger_digest: str, generated_on: date) -> dict:
    policy = ledger["expiry_policy"]
    window = int(policy["expiring_window_days"])
    levels = set(policy["runtime_evidence_levels"])
    facts = []
    for claim in ledger["claims"]:
        state = lifecycle(claim, generated_on, window)
        if (
            not claim["runtime_eligible"]
            or claim["verification_status"] != "CONFIRMED_ACTIVE"
            or claim["evidence_level"] not in levels
            or state == "stale"
        ):
            continue
        facts.append(
            {
                "claim_id": claim["claim_id"],
                "kind": claim["kind"],
                "claim": claim["claim"],
                "value": claim["value"],
                "scope": claim["scope"],
                "evidence_level": claim["evidence_level"],
                "verification_status": claim["verification_status"],
                "checked_at": claim["checked_at"],
                "expires_at": claim["expires_at"],
                "lifecycle": state,
                "route_action": claim["route_action"],
                "source_url": claim["source_url"],
                "risk_tier": claim["risk_tier"],
                "affected_components": claim["affected_components"],
            }
        )
    facts.sort(key=lambda item: item["claim_id"])
    return {
        "schema_version": LIVE_SCHEMA,
        "ledger_revision": ledger["ledger_revision"],
        "generated_on": generated_on.isoformat(),
        "source_ledger_sha256": ledger_digest,
        "rules": {
            "stale_claims_are_excluded": True,
            "block_requires_official_evidence_A": True,
            "unknown_or_unlisted_claims_require_verification": True,
        },
        "facts": facts,
    }


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def live_preview_report(ledger: dict, ledger_path: Path, governance: Path, generated_on: date) -> tuple[dict, dict]:
    warnings = validate_ledger(ledger, governance)
    ledger_digest = sha256(ledger_path)
    live = build_live(ledger, ledger_digest, generated_on)
    report = {
        "schema_version": LIVE_PREVIEW_SCHEMA,
        "created_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "status": "PASS",
        "action": "promote_live_specs",
        "subject": str(ledger_path),
        "subject_sha256": ledger_digest,
        "ledger_revision": ledger["ledger_revision"],
        "generated_on": generated_on.isoformat(),
        "claim_count": len(ledger["claims"]),
        "runtime_fact_count": len(live["facts"]),
        "candidate_live_sha256": hashlib.sha256(canonical_json_bytes(live)).hexdigest(),
        "warnings": warnings,
    }
    return report, live


def command_prepare_live(args: argparse.Namespace) -> int:
    governance = Path(args.governance).expanduser().resolve()
    ledger_path = governance / "fact-ledger.json"
    ledger = load_json(ledger_path)
    generated_on = parse_date(args.as_of, "--as-of") if args.as_of else date.today()
    report, _ = live_preview_report(ledger, ledger_path, governance, generated_on)
    output = Path(args.report).expanduser().resolve()
    if output.exists():
        raise GovernanceError(f"Refusing to overwrite technical report: {output}")
    write_json_atomic(output, report)
    print(
        json.dumps(
            {
                "status": "PASS_TECHNICAL_PREVIEW_USER_APPROVAL_REQUIRED",
                "report": str(output),
                "subject": str(ledger_path),
                "subject_sha256": report["subject_sha256"],
                "candidate_live_sha256": report["candidate_live_sha256"],
                "runtime_facts": report["runtime_fact_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def runtime_manifest(root: Path, governance: Path) -> dict:
    policy = load_json(governance / "drift-policy.json")
    if not isinstance(policy, dict) or policy.get("schema_version") != "p2p-codex-drift-policy/2":
        raise GovernanceError("Invalid drift-policy.json")
    package_mode = governance.resolve() == (root / "governance").resolve()
    path_key = "package_protected_paths" if package_mode else "installed_protected_paths"
    protected_paths = policy.get(path_key)
    if not isinstance(protected_paths, list) or not protected_paths:
        raise GovernanceError(f"drift-policy.json has no {path_key}")
    excluded = [str(item).replace("\\", "/") for item in policy.get("runtime_lock_excluded_fragments", [])]
    files: dict[str, str] = {}
    for relative in protected_paths:
        base = root / str(relative)
        if not base.exists():
            continue
        candidates = [base] if base.is_file() else sorted(path for path in base.rglob("*") if path.is_file())
        for path in candidates:
            normalized = "/" + path.relative_to(root).as_posix()
            if path.is_symlink() or any(fragment in normalized for fragment in excluded):
                continue
            files[path.relative_to(root).as_posix()] = sha256(path)
    virtual: dict[str, str] = {}
    instructions = root / "AGENTS.md"
    if not instructions.is_file():
        alternate = root / ".codex" / "AGENTS.md"
        instructions = alternate if alternate.is_file() else instructions
    if instructions.is_file():
        text = instructions.read_text(encoding="utf-8", errors="replace")
        begin = "<!-- BEGIN P2P CODEX -->"
        end = "<!-- END P2P CODEX -->"
        if begin in text and end in text:
            block = text.split(begin, 1)[1].split(end, 1)[0].strip()
        else:
            block = text.strip()
        virtual["P2P_INSTRUCTIONS_BLOCK"] = sha256_text(block)
    config = root / ".codex" / "config.toml"
    if config.is_file():
        text = config.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?ms)^\s*\[agents\]\s*$.*?(?=^\s*\[|\Z)", text)
        if match:
            virtual["CODEX_AGENTS_CONFIG_SECTION"] = sha256_text(match.group(0).strip())
    return {
        "schema_version": RUNTIME_LOCK_SCHEMA,
        "root_mode": "package" if package_mode else "installed",
        "protected_files": dict(sorted(files.items())),
        "virtual_hashes": dict(sorted(virtual.items())),
    }


def command_lock_runtime(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    governance = Path(args.governance).expanduser().resolve()
    value = runtime_manifest(root, governance)
    value["generated_at"] = datetime.now().astimezone().replace(microsecond=0).isoformat()
    value["reason"] = args.reason
    write_json_atomic(governance / "runtime-manifest.lock.json", value)
    print(
        json.dumps(
            {
                "status": "PASS",
                "protected_files": len(value["protected_files"]),
                "virtual_hashes": len(value["virtual_hashes"]),
                "lock": str(governance / "runtime-manifest.lock.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def verify_runtime_manifest(root: Path, governance: Path) -> list[str]:
    lock_path = governance / "runtime-manifest.lock.json"
    if not lock_path.is_file():
        return ["runtime-manifest.lock.json is missing"]
    lock = load_json(lock_path)
    if not isinstance(lock, dict) or lock.get("schema_version") != RUNTIME_LOCK_SCHEMA:
        return ["runtime-manifest.lock.json has the wrong schema"]
    current = runtime_manifest(root, governance)
    failures: list[str] = []
    locked_files = lock.get("protected_files")
    locked_virtual = lock.get("virtual_hashes")
    if not isinstance(locked_files, dict) or not isinstance(locked_virtual, dict):
        return ["runtime-manifest.lock.json is incomplete"]
    current_files = current["protected_files"]
    missing = sorted(set(locked_files) - set(current_files))
    added = sorted(set(current_files) - set(locked_files))
    changed = sorted(path for path in set(locked_files) & set(current_files) if locked_files[path] != current_files[path])
    if missing:
        failures.append("protected runtime files removed: " + ", ".join(missing[:8]))
    if added:
        failures.append("unlocked runtime files added: " + ", ".join(added[:8]))
    if changed:
        failures.append("protected runtime files changed: " + ", ".join(changed[:8]))
    if locked_virtual != current["virtual_hashes"]:
        names = sorted(set(locked_virtual) | set(current["virtual_hashes"]))
        changed_virtual = [name for name in names if locked_virtual.get(name) != current["virtual_hashes"].get(name)]
        failures.append("protected runtime configuration changed: " + ", ".join(changed_virtual))
    return failures


def command_build(args: argparse.Namespace) -> int:
    governance = Path(args.governance).expanduser().resolve()
    ledger_path = governance / "fact-ledger.json"
    ledger = load_json(ledger_path)
    generated_on = parse_date(args.as_of, "--as-of") if args.as_of else date.today()
    report_path = Path(args.technical_report).expanduser().resolve()
    if not report_path.is_file():
        raise GovernanceError("build-live requires the PASS technical preview report")
    report = load_json(report_path)
    expected_report, live = live_preview_report(ledger, ledger_path, governance, generated_on)
    ledger_digest = expected_report["subject_sha256"]
    if not isinstance(report, dict) or report.get("schema_version") != LIVE_PREVIEW_SCHEMA:
        raise GovernanceError("Live Specs technical report has the wrong schema")
    for key in (
        "status", "action", "subject_sha256", "ledger_revision", "generated_on",
        "claim_count", "runtime_fact_count", "candidate_live_sha256", "warnings",
    ):
        if report.get(key) != expected_report.get(key):
            raise GovernanceError(f"Live Specs technical report no longer matches: {key}")
    if not args.approval:
        raise GovernanceError("build-live requires an explicit user approval record")
    approval_path = Path(args.approval).expanduser().resolve()
    approval = load_json(approval_path)
    approval_policy = validate_approval_policy(load_json(governance / "approval-policy.json"))
    approval_errors = validate_approval_record(
        approval,
        approval_policy,
        expected_action="promote_live_specs",
        expected_subject_sha256=ledger_digest,
        expected_technical_report_sha256=sha256(report_path),
    )
    if approval_errors:
        raise GovernanceError("FACT_LEDGER approval failed: " + "; ".join(approval_errors))
    live_path = governance / "live-specs.json"
    write_json_atomic(live_path, live)
    lock = {
        "schema_version": LOCK_SCHEMA,
        "ledger_revision": ledger["ledger_revision"],
        "generated_on": generated_on.isoformat(),
        "ledger_sha256": ledger_digest,
        "target_sha256": {"live-specs.json": sha256(live_path)},
        "claim_count": len(ledger["claims"]),
        "runtime_fact_count": len(live["facts"]),
        "technical_report": report_path.relative_to(governance).as_posix()
        if report_path.is_relative_to(governance)
        else str(report_path),
        "technical_report_sha256": sha256(report_path),
        "approval_record": approval_path.relative_to(governance).as_posix()
        if approval_path.is_relative_to(governance)
        else str(approval_path),
        "approval_sha256": sha256(approval_path),
    }
    write_json_atomic(governance / "live-specs.lock.json", lock)
    result = {
        "ok": True,
        "generated_on": generated_on.isoformat(),
        "runtime_facts": len(live["facts"]),
        "warnings": expected_report["warnings"],
        "technical_report_sha256": sha256(report_path),
        "approval_sha256": sha256(approval_path),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def scan_volatile(
    root: Path,
    governance: Path,
    claims_by_id: dict[str, dict],
    as_of: date,
    expiring_window: int,
    scoped_references: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    policy = load_json(governance / "drift-policy.json")
    if not isinstance(policy, dict) or policy.get("schema_version") != "p2p-codex-drift-policy/2":
        raise GovernanceError("Invalid drift-policy.json")
    patterns = [re.compile(item) for item in policy.get("volatile_patterns", [])]
    excluded = [str(item).replace("\\", "/") for item in policy.get("excluded_path_fragments", [])]
    live_marker = str(policy.get("live_fact_marker", "FACT_REF:"))
    historical_marker = str(policy.get("historical_marker", "HISTORICAL_ONLY:"))
    scoped_paths = policy.get("scoped_volatile_paths", {})
    if not isinstance(scoped_paths, dict):
        raise GovernanceError("Invalid scoped_volatile_paths in drift-policy.json")
    findings: list[dict[str, object]] = []
    for relative in policy.get("active_scan_paths", []):
        base = root / str(relative)
        if not base.exists():
            continue
        files = [base] if base.is_file() else sorted(path for path in base.rglob("*") if path.is_file())
        for path in files:
            normalized = "/" + path.relative_to(root).as_posix()
            if any(fragment in normalized for fragment in excluded):
                continue
            if path.suffix.lower() not in {".md", ".txt", ".yaml", ".yml", ".json"}:
                continue
            relative_path = path.relative_to(root).as_posix()
            scope = scoped_paths.get(relative_path)
            if scope is None:
                # Prefix scope: a scoped entry ending in '/' classifies every
                # file beneath it (host-project docs tree), so host project
                # evidence is classified instead of flagged as unledgered.
                normalized = "/" + relative_path
                for scoped_path, scoped_scope in sorted(
                    scoped_paths.items(), key=lambda item: -len(item[0])
                ):
                    if scoped_path.endswith("/") and normalized.startswith(
                        "/" + scoped_path
                    ):
                        scope = scoped_scope
                        break
            for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                matches = sorted({match.group(0) for pattern in patterns for match in pattern.finditer(line)})
                if historical_marker in line:
                    continue
                if matches and isinstance(scope, dict):
                    if scoped_references is not None:
                        scoped_references.append(
                            {
                                "path": relative_path,
                                "line": number,
                                "matches": matches,
                                "classification": scope.get("classification"),
                                "status": scope.get("status"),
                                "reason": scope.get("reason"),
                            }
                        )
                    continue
                if live_marker in line:
                    references = sorted(set(re.findall(r"P2P-FACT-[0-9]{4}", line)))
                    if not references:
                        findings.append(
                            {
                                "path": path.relative_to(root).as_posix(),
                                "line": number,
                                "matches": matches,
                                "reason": "FACT_REF has no claim ID",
                            }
                        )
                        continue
                    invalid = []
                    for claim_id in references:
                        claim = claims_by_id.get(claim_id)
                        if claim is None:
                            invalid.append(f"{claim_id}:missing")
                        elif not claim.get("runtime_eligible"):
                            invalid.append(f"{claim_id}:not-runtime-eligible")
                        elif lifecycle(claim, as_of, expiring_window) == "stale":
                            invalid.append(f"{claim_id}:expired")
                    if invalid:
                        findings.append(
                            {
                                "path": path.relative_to(root).as_posix(),
                                "line": number,
                                "matches": references,
                                "reason": ", ".join(invalid),
                            }
                        )
                    continue
                if matches:
                    findings.append(
                        {
                            "path": path.relative_to(root).as_posix(),
                            "line": number,
                            "matches": matches,
                            "reason": "volatile claim has no valid FACT_REF",
                        }
                    )
    return findings


def command_drift(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    governance = Path(args.governance).expanduser().resolve()
    as_of = parse_date(args.as_of, "--as-of") if args.as_of else date.today()
    failures: list[str] = []
    warnings: list[str] = []
    findings: list[dict[str, object]] = []
    scoped_references: list[dict[str, object]] = []
    try:
        ledger_path = governance / "fact-ledger.json"
        ledger = load_json(ledger_path)
        warnings.extend(validate_ledger(ledger, governance))
        lock = load_json(governance / "live-specs.lock.json")
        live = load_json(governance / "live-specs.json")
        if not isinstance(lock, dict) or lock.get("schema_version") != LOCK_SCHEMA:
            failures.append("live-specs.lock.json is missing or has the wrong schema")
        if not isinstance(live, dict) or live.get("schema_version") != LIVE_SCHEMA:
            failures.append("live-specs.json is missing or has the wrong schema")
        ledger_digest = sha256(ledger_path)
        if isinstance(lock, dict) and lock.get("ledger_sha256") != ledger_digest:
            failures.append("FACT_LEDGER changed without rebuilding Live Specs")
        if isinstance(lock, dict) and lock.get("ledger_revision") != ledger.get("ledger_revision"):
            failures.append("Live Specs lock revision does not match FACT_LEDGER")
        if isinstance(live, dict) and live.get("ledger_revision") != ledger.get("ledger_revision"):
            failures.append("Live Specs revision does not match FACT_LEDGER")
        live_path = governance / "live-specs.json"
        expected_live_hash = lock.get("target_sha256", {}).get("live-specs.json") if isinstance(lock, dict) else None
        if not live_path.is_file() or sha256(live_path) != expected_live_hash:
            failures.append("Live Specs hash does not match its generated lock")
        window = int(ledger["expiry_policy"]["expiring_window_days"])
        if isinstance(live, dict) and live.get("schema_version") == LIVE_SCHEMA:
            generated_on = parse_date(live.get("generated_on"), "live-specs.generated_on")
            expected_live = build_live(ledger, ledger_digest, generated_on)
            if live != expected_live:
                failures.append("Live Specs content is not the deterministic projection of FACT_LEDGER")
            if generated_on > as_of:
                failures.append("Live Specs generation date is later than the drift-gate date")
            if isinstance(lock, dict):
                if lock.get("generated_on") != live.get("generated_on"):
                    failures.append("Live Specs and lock generation dates do not match")
                if lock.get("claim_count") != len(ledger["claims"]):
                    failures.append("Live Specs lock claim count does not match FACT_LEDGER")
                if lock.get("runtime_fact_count") != len(live.get("facts", [])):
                    failures.append("Live Specs lock runtime count does not match Live Specs")
        if isinstance(lock, dict):
            report_hash: str | None = None
            report_reference = lock.get("technical_report")
            if not isinstance(report_reference, str) or not report_reference:
                failures.append("Live Specs lock has no technical preview report")
            else:
                report_path = Path(report_reference)
                if not report_path.is_absolute():
                    report_path = governance / report_path
                if not report_path.is_file():
                    failures.append("Live Specs technical preview report is missing")
                else:
                    report_hash = sha256(report_path)
                    if lock.get("technical_report_sha256") != report_hash:
                        failures.append("Live Specs technical preview report hash mismatch")
                    report = load_json(report_path)
                    expected_report, _ = live_preview_report(
                        ledger,
                        ledger_path,
                        governance,
                        parse_date(lock.get("generated_on"), "live-specs.lock.generated_on"),
                    )
                    if not isinstance(report, dict) or report.get("schema_version") != LIVE_PREVIEW_SCHEMA:
                        failures.append("Live Specs technical preview report has the wrong schema")
                    else:
                        for key in (
                            "status", "action", "subject_sha256", "ledger_revision",
                            "generated_on", "claim_count", "runtime_fact_count",
                            "candidate_live_sha256",
                        ):
                            if report.get(key) != expected_report.get(key):
                                failures.append(f"Live Specs technical preview drifted: {key}")
            approval_reference = lock.get("approval_record")
            if not isinstance(approval_reference, str) or not approval_reference:
                failures.append("Live Specs lock has no user-approval record")
            else:
                approval_path = Path(approval_reference)
                if not approval_path.is_absolute():
                    approval_path = governance / approval_path
                if not approval_path.is_file():
                    failures.append("Live Specs approval record is missing")
                else:
                    if lock.get("approval_sha256") != sha256(approval_path):
                        failures.append("Live Specs approval record hash mismatch")
                    approval_policy = validate_approval_policy(load_json(governance / "approval-policy.json"))
                    approval_errors = validate_approval_record(
                        load_json(approval_path),
                        approval_policy,
                        expected_action="promote_live_specs",
                        expected_subject_sha256=ledger_digest,
                        expected_technical_report_sha256=report_hash,
                        provenance_only=True,
                    )
                    failures.extend(f"Live Specs approval: {item}" for item in approval_errors)
        for claim in ledger["claims"]:
            if claim["runtime_eligible"] and lifecycle(claim, as_of, window) == "stale":
                failures.append(f"runtime claim expired: {claim['claim_id']} on {claim['expires_at']}")
        claims_by_id = {claim["claim_id"]: claim for claim in ledger["claims"]}
        findings = scan_volatile(root, governance, claims_by_id, as_of, window, scoped_references)
        if findings:
            preview = ", ".join(f"{item['path']}:{item['line']}" for item in findings[:8])
            failures.append(f"unledgered volatile claims found in active runtime: {preview}")
        failures.extend(verify_runtime_manifest(root, governance))
    except GovernanceError as exc:
        failures.append(str(exc))
        findings = []
    result = {
        "schema_version": "p2p-codex-drift-report/1",
        "checked_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "as_of": as_of.isoformat(),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "warnings": warnings,
        "volatile_findings": findings,
        "scoped_volatile_references": scoped_references,
    }
    if args.report:
        write_json_atomic(Path(args.report).expanduser().resolve(), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    preview = sub.add_parser("prepare-live", help="Validate FACT_LEDGER and create a hash-bound Live Specs technical preview")
    preview.add_argument("--governance", default=str(Path(__file__).resolve().parents[1] / "governance"))
    preview.add_argument("--as-of", help="ISO date; defaults to today")
    preview.add_argument("--report", required=True, help="New JSON technical-report path")
    preview.set_defaults(func=command_prepare_live)
    build = sub.add_parser("build-live", help="Generate compact Live Specs after matching technical preview and user approval")
    build.add_argument("--governance", default=str(Path(__file__).resolve().parents[1] / "governance"))
    build.add_argument("--as-of", help="ISO date; defaults to today")
    build.add_argument("--technical-report", required=True, help="PASS preview report matching FACT_LEDGER and candidate Live Specs")
    build.add_argument("--approval", required=True, help="Approved promote_live_specs record matching FACT_LEDGER and technical report")
    build.set_defaults(func=command_build)
    lock_runtime = sub.add_parser("lock-runtime", help="Hash all protected P2P runtime files and configuration blocks")
    lock_runtime.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    lock_runtime.add_argument("--governance", default=str(Path(__file__).resolve().parents[1] / "governance"))
    lock_runtime.add_argument("--reason", required=True)
    lock_runtime.set_defaults(func=command_lock_runtime)
    drift = sub.add_parser("drift", help="Run expiry, synchronization, and active-runtime drift gates")
    drift.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    drift.add_argument("--governance", default=str(Path(__file__).resolve().parents[1] / "governance"))
    drift.add_argument("--as-of", help="ISO date; defaults to today")
    drift.add_argument("--report", help="Optional JSON report path")
    drift.set_defaults(func=command_drift)
    return p


if __name__ == "__main__":
    parsed = parser().parse_args()
    try:
        raise SystemExit(parsed.func(parsed))
    except GovernanceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
