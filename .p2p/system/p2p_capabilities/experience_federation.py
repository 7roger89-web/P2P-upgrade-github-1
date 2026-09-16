"""Cross-project experience federation for P2P.

This module closes two bounded gaps without creating another memory database,
router, or control plane:

1. project-local ACTIVE experience may be proposed for DOMAIN/CROSS_PROJECT
   promotion only with independent scope evidence;
2. promoted experience is carried by one small package catalog and hydrated
   into the existing project execution ledger, where the existing
   experience_evolution runtime remains the only active-experience lifecycle;
3. only repeated, procedural, cross-project experience with stable
   input/output/procedure metadata may produce a SKILL_CANDIDATE. A candidate
   never mutates the skill registry and never becomes eligible/active by itself.

The catalog is a curated distribution projection, not raw task memory and not
acceptance authority. Project-only experience stays in the project execution
ledger and is never copied into the shared catalog.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .experience_evolution import (
    ExperienceEvolutionError,
    activate_verified,
    create_candidate,
    derive_experiences,
    verify_candidate,
)

SCHEMA = "p2p-experience-federation/1"
CATALOG_SCHEMA = "p2p-shared-experience-catalog/1"
PROMOTION_SCHEMA = "p2p-experience-promotion-proposal/1"
SKILL_CANDIDATE_SCHEMA = "p2p-experience-skill-candidate/1"
CATALOG_FILENAME = "shared_experience_catalog.json"
SCOPES = ("PROJECT_ONLY", "DOMAIN", "CROSS_PROJECT")
PROMOTABLE_SCOPES = ("DOMAIN", "CROSS_PROJECT")
MAX_CATALOG_RECORDS = 512
MAX_PROCEDURE_STEPS = 24
MAX_IO_ITEMS = 24
_SECRET_RE = re.compile(
    r"(?i)(?:api[_-]?key|password|token|secret|authorization|private[_-]?key)"
    r"\s*[:=]\s*[^\s,;]+|(?:sk|ghp|github_pat|xox[bp])-[A-Za-z0-9_-]{12,}"
)


class ExperienceFederationError(ValueError):
    """Fail-closed federation contract error."""


def _clean(value: object, limit: int = 4096) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if _SECRET_RE.search(text):
        raise ExperienceFederationError("SECRET_LIKE_VALUE_REJECTED")
    return text[:limit]


def _sequence(values: Iterable[object] | None, *, limit: int, item_limit: int = 512) -> list[str]:
    out: list[str] = []
    for raw in values or ():
        item = _clean(raw, item_limit)
        if item and item not in out:
            out.append(item)
        if len(out) >= limit:
            break
    return out


def _stable(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def default_catalog_path() -> Path:
    return Path(__file__).with_name(CATALOG_FILENAME)


def _empty_catalog() -> dict[str, Any]:
    return {
        "schema": CATALOG_SCHEMA,
        "catalog_role": "CURATED_PROMOTED_EXPERIENCE_DISTRIBUTION",
        "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
        "records": [],
    }


def load_catalog(path: str | Path | None = None) -> dict[str, Any]:
    catalog_path = Path(path) if path else default_catalog_path()
    if not catalog_path.is_file():
        return _empty_catalog()
    try:
        value = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExperienceFederationError("SHARED_EXPERIENCE_CATALOG_INVALID") from exc
    if not isinstance(value, Mapping) or value.get("schema") != CATALOG_SCHEMA:
        raise ExperienceFederationError("SHARED_EXPERIENCE_CATALOG_SCHEMA_INVALID")
    records = value.get("records")
    if not isinstance(records, list) or len(records) > MAX_CATALOG_RECORDS:
        raise ExperienceFederationError("SHARED_EXPERIENCE_CATALOG_RECORDS_INVALID")
    for record in records:
        _validate_catalog_record(record)
    return dict(value)


def _write_catalog(path: str | Path, catalog: Mapping[str, object]) -> None:
    catalog_path = Path(path)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(catalog), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    temp = catalog_path.with_suffix(catalog_path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(catalog_path)


def _scope_evidence(items: Iterable[Mapping[str, object]], source_project: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    external_projects: set[str] = set()
    for raw in items:
        if not isinstance(raw, Mapping):
            raise ExperienceFederationError("SCOPE_EVIDENCE_ITEM_INVALID")
        project = _clean(raw.get("project"), 256)
        ref = _clean(raw.get("ref"), 1024)
        verdict = _clean(raw.get("verdict", "PROVEN"), 32).upper()
        if not project or not ref or verdict not in {"PROVEN", "PASS", "VERIFIED"}:
            continue
        if project != source_project:
            external_projects.add(project)
        out.append({"project": project, "ref": ref, "verdict": verdict})
    if not out:
        raise ExperienceFederationError("SCOPE_EVIDENCE_REQUIRED")
    if not external_projects:
        raise ExperienceFederationError("OUT_OF_PROJECT_SCOPE_PROOF_REQUIRED")
    return out


def _verification_evidence(exp: Mapping[str, object]) -> list[dict[str, str]]:
    raw = exp.get("verification_evidence") or ()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ExperienceFederationError("SOURCE_VERIFICATION_EVIDENCE_INVALID")
    out: list[dict[str, str]] = []
    roles: set[str] = set()
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        kind = _clean(item.get("kind"), 96).upper()
        ref = _clean(item.get("ref"), 1024)
        role = _clean(item.get("role"), 96).upper()
        verdict = _clean(item.get("verdict", "PROVEN"), 32).upper()
        if kind and ref and verdict in {"PROVEN", "PASS", "VERIFIED"}:
            out.append({"kind": kind, "ref": ref, "role": role, "verdict": verdict})
            if role:
                roles.add(role)
    required = {"BEHAVIOR_PROOF", "REGRESSION_PROOF", "CHALLENGE_PROOF"}
    if not required.issubset(roles):
        raise ExperienceFederationError("SOURCE_EXPERIENCE_NOT_FULLY_VERIFIED")
    return out


def _source_evidence(exp: Mapping[str, object]) -> list[dict[str, str]]:
    raw = exp.get("evidence") or ()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ExperienceFederationError("SOURCE_EVIDENCE_INVALID")
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        kind = _clean(item.get("kind"), 96).upper()
        ref = _clean(item.get("ref"), 1024)
        role = _clean(item.get("role"), 96).upper()
        verdict = _clean(item.get("verdict", "PROVEN"), 32).upper()
        if kind and ref and verdict in {"PROVEN", "PASS", "VERIFIED"}:
            out.append({"kind": kind, "ref": ref, "role": role, "verdict": verdict})
    if not out:
        raise ExperienceFederationError("SOURCE_EVIDENCE_REQUIRED")
    return out


def build_promotion_proposal(
    project_root: str | Path,
    experience_id: str,
    *,
    source_project: str,
    scope: str,
    scope_evidence: Iterable[Mapping[str, object]],
    domain: str = "",
    procedure: Iterable[object] = (),
    inputs: Iterable[object] = (),
    outputs: Iterable[object] = (),
) -> dict[str, Any]:
    source_project = _clean(source_project, 256)
    scope = _clean(scope, 32).upper()
    domain = _clean(domain, 128).lower()
    if scope not in SCOPES:
        raise ExperienceFederationError("EXPERIENCE_SCOPE_INVALID")
    states = derive_experiences(project_root)
    exp = states.get(_clean(experience_id, 128))
    if not exp or exp.get("state") != "ACTIVE":
        raise ExperienceFederationError("PROMOTION_REQUIRES_ACTIVE_LOCAL_EXPERIENCE")
    if scope == "PROJECT_ONLY":
        return {
            "schema": PROMOTION_SCHEMA,
            "status": "KEEP_LOCAL",
            "scope": scope,
            "source_project": source_project,
            "source_experience_id": experience_id,
            "promotable": False,
        }
    if scope == "DOMAIN" and not domain:
        raise ExperienceFederationError("DOMAIN_SCOPE_REQUIRES_DOMAIN")
    scope_proof = _scope_evidence(scope_evidence, source_project)
    verification = _verification_evidence(exp)
    evidence = _source_evidence(exp)
    procedure_steps = _sequence(procedure, limit=MAX_PROCEDURE_STEPS)
    input_items = _sequence(inputs, limit=MAX_IO_ITEMS)
    output_items = _sequence(outputs, limit=MAX_IO_ITEMS)
    projects = sorted({source_project, *(item["project"] for item in scope_proof)})
    proposal = {
        "schema": PROMOTION_SCHEMA,
        "status": "PROMOTION_CANDIDATE",
        "scope": scope,
        "domain": domain,
        "source_project": source_project,
        "source_projects_proven": projects,
        "source_experience_id": _clean(experience_id, 128),
        "source_task_id": _clean(exp.get("source_task_id"), 256),
        "source_revision": _clean(exp.get("source_revision"), 256),
        "kind": _clean(exp.get("kind"), 32).upper(),
        "trigger_tokens": _sequence(exp.get("trigger_tokens") or (), limit=24, item_limit=128),
        "lesson": _clean(exp.get("lesson")),
        "correction": _clean(exp.get("correction")),
        "failure_class": _clean(exp.get("failure_class"), 256),
        "outcome": _clean(exp.get("outcome"), 128).upper(),
        "evidence": evidence,
        "verification_evidence": verification,
        "scope_evidence": scope_proof,
        "procedure": procedure_steps,
        "inputs": input_items,
        "outputs": output_items,
        "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
        "permission_effect": "NONE",
        "acceptance_authority": False,
    }
    proposal["proposal_id"] = "prom-" + hashlib.sha256(_stable(proposal).encode("utf-8")).hexdigest()[:24]
    proposal["skill_candidate_eligible"] = bool(
        scope == "CROSS_PROJECT"
        and proposal["kind"] == "PROCEDURAL"
        and len(projects) >= 2
        and len(procedure_steps) >= 2
        and input_items
        and output_items
    )
    return proposal


def _record_id(proposal: Mapping[str, object]) -> str:
    identity = {
        "scope": proposal.get("scope"),
        "domain": proposal.get("domain", ""),
        "kind": proposal.get("kind"),
        "trigger_tokens": proposal.get("trigger_tokens"),
        "lesson": proposal.get("lesson"),
        "correction": proposal.get("correction"),
    }
    return "shared-exp-" + hashlib.sha256(_stable(identity).encode("utf-8")).hexdigest()[:24]


def _validate_catalog_record(record: object) -> None:
    if not isinstance(record, Mapping):
        raise ExperienceFederationError("SHARED_EXPERIENCE_RECORD_INVALID")
    scope = _clean(record.get("scope"), 32).upper()
    if scope not in PROMOTABLE_SCOPES:
        raise ExperienceFederationError("SHARED_EXPERIENCE_RECORD_SCOPE_INVALID")
    if scope == "DOMAIN" and not _clean(record.get("domain"), 128):
        raise ExperienceFederationError("SHARED_EXPERIENCE_RECORD_DOMAIN_REQUIRED")
    if not _clean(record.get("record_id"), 128):
        raise ExperienceFederationError("SHARED_EXPERIENCE_RECORD_ID_REQUIRED")
    if record.get("state") != "ACTIVE":
        raise ExperienceFederationError("SHARED_EXPERIENCE_RECORD_NOT_ACTIVE")
    if not _clean(record.get("lesson")):
        raise ExperienceFederationError("SHARED_EXPERIENCE_RECORD_LESSON_REQUIRED")
    _scope_evidence(record.get("scope_evidence") or (), _clean(record.get("source_project"), 256))


def apply_promotion(
    proposal: Mapping[str, object],
    *,
    catalog_path: str | Path | None = None,
) -> dict[str, Any]:
    if not isinstance(proposal, Mapping) or proposal.get("schema") != PROMOTION_SCHEMA:
        raise ExperienceFederationError("PROMOTION_PROPOSAL_SCHEMA_INVALID")
    if proposal.get("status") != "PROMOTION_CANDIDATE" or proposal.get("scope") not in PROMOTABLE_SCOPES:
        raise ExperienceFederationError("PROMOTION_PROPOSAL_NOT_PROMOTABLE")
    source_project = _clean(proposal.get("source_project"), 256)
    _scope_evidence(proposal.get("scope_evidence") or (), source_project)
    if not proposal.get("verification_evidence") or not proposal.get("evidence"):
        raise ExperienceFederationError("PROMOTION_PROPOSAL_EVIDENCE_REQUIRED")
    record_id = _record_id(proposal)
    record = {
        "record_id": record_id,
        "state": "ACTIVE",
        "scope": _clean(proposal.get("scope"), 32).upper(),
        "domain": _clean(proposal.get("domain"), 128).lower(),
        "source_project": source_project,
        "source_projects_proven": list(proposal.get("source_projects_proven") or ()),
        "source_experience_id": _clean(proposal.get("source_experience_id"), 128),
        "source_task_id": _clean(proposal.get("source_task_id"), 256),
        "source_revision": _clean(proposal.get("source_revision"), 256),
        "kind": _clean(proposal.get("kind"), 32).upper(),
        "trigger_tokens": _sequence(proposal.get("trigger_tokens") or (), limit=24, item_limit=128),
        "lesson": _clean(proposal.get("lesson")),
        "correction": _clean(proposal.get("correction")),
        "failure_class": _clean(proposal.get("failure_class"), 256),
        "outcome": _clean(proposal.get("outcome"), 128).upper(),
        "evidence": list(proposal.get("evidence") or ()),
        "verification_evidence": list(proposal.get("verification_evidence") or ()),
        "scope_evidence": list(proposal.get("scope_evidence") or ()),
        "procedure": _sequence(proposal.get("procedure") or (), limit=MAX_PROCEDURE_STEPS),
        "inputs": _sequence(proposal.get("inputs") or (), limit=MAX_IO_ITEMS),
        "outputs": _sequence(proposal.get("outputs") or (), limit=MAX_IO_ITEMS),
        "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
        "permission_effect": "NONE",
        "acceptance_authority": False,
        "skill_candidate_eligible": bool(proposal.get("skill_candidate_eligible")),
    }
    _validate_catalog_record(record)
    path = Path(catalog_path) if catalog_path else default_catalog_path()
    catalog = load_catalog(path)
    records = list(catalog.get("records") or ())
    existing = next((item for item in records if item.get("record_id") == record_id), None)
    if existing is not None:
        if _stable(existing) != _stable(record):
            raise ExperienceFederationError("SHARED_EXPERIENCE_RECORD_CONFLICT")
        return {"status": "EXISTS", **record}
    if len(records) >= MAX_CATALOG_RECORDS:
        raise ExperienceFederationError("SHARED_EXPERIENCE_CATALOG_FULL")
    records.append(record)
    records.sort(key=lambda item: str(item.get("record_id")))
    catalog["records"] = records
    _write_catalog(path, catalog)
    return {"status": "PROMOTED", **record}


def _sync_record(root: str | Path, record: Mapping[str, object]) -> str:
    source_task_id = _clean(record.get("source_task_id"), 256) or "shared-experience-sync"
    source_eid = _clean(record.get("source_experience_id"), 128)
    existing = derive_experiences(root).get(source_eid) if source_eid else None
    if existing and existing.get("state") in {"QUARANTINED", "SUPERSEDED"}:
        return str(existing.get("state"))
    created = create_candidate(
        root,
        task_id=source_task_id,
        kind=_clean(record.get("kind"), 32),
        trigger_tokens=record.get("trigger_tokens") or (),
        lesson=_clean(record.get("lesson")),
        evidence=record.get("evidence") or (),
        outcome=_clean(record.get("outcome"), 128) or "REUSABLE_CORRECTION",
        failure_class=_clean(record.get("failure_class"), 256),
        correction=_clean(record.get("correction")),
        source_revision=_clean(record.get("source_revision"), 256),
    )
    eid = created.get("experience_id")
    if not isinstance(eid, str):
        raise ExperienceFederationError("SYNC_EXPERIENCE_ID_MISSING")
    state = derive_experiences(root).get(eid, {}).get("state")
    if state == "CANDIDATE":
        verify_candidate(
            root,
            eid,
            task_id=source_task_id,
            verification_evidence=record.get("verification_evidence") or (),
        )
        state = "VERIFIED"
    if state == "VERIFIED":
        activate_verified(root, eid, task_id=source_task_id)
        state = "ACTIVE"
    if state == "ACTIVE":
        return "ACTIVE"
    if state in {"QUARANTINED", "SUPERSEDED"}:
        return str(state)
    raise ExperienceFederationError(f"SYNC_UNEXPECTED_EXPERIENCE_STATE:{state}")


def sync_shared_catalog(
    project_root: str | Path,
    *,
    domain: str = "",
    catalog_path: str | Path | None = None,
) -> dict[str, Any]:
    domain = _clean(domain, 128).lower()
    catalog = load_catalog(catalog_path)
    selected: list[Mapping[str, object]] = []
    for record in catalog.get("records") or ():
        if record.get("scope") == "CROSS_PROJECT":
            selected.append(record)
        elif record.get("scope") == "DOMAIN" and domain and record.get("domain") == domain:
            selected.append(record)
    counts = {"ACTIVE": 0, "QUARANTINED": 0, "SUPERSEDED": 0}
    for record in selected:
        outcome = _sync_record(project_root, record)
        counts[outcome] = counts.get(outcome, 0) + 1
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "selected": len(selected),
        "domain": domain,
        "counts": counts,
        "catalog_authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
        "current_state_wins": True,
        "permission_effect": "NONE",
    }


def build_skill_candidate(record: Mapping[str, object]) -> dict[str, Any]:
    _validate_catalog_record(record)
    if record.get("scope") != "CROSS_PROJECT":
        raise ExperienceFederationError("SKILL_CANDIDATE_REQUIRES_CROSS_PROJECT_EXPERIENCE")
    if record.get("kind") != "PROCEDURAL":
        raise ExperienceFederationError("SKILL_CANDIDATE_REQUIRES_PROCEDURAL_EXPERIENCE")
    projects = {str(item) for item in (record.get("source_projects_proven") or ()) if str(item)}
    procedure = _sequence(record.get("procedure") or (), limit=MAX_PROCEDURE_STEPS)
    inputs = _sequence(record.get("inputs") or (), limit=MAX_IO_ITEMS)
    outputs = _sequence(record.get("outputs") or (), limit=MAX_IO_ITEMS)
    if len(projects) < 2:
        raise ExperienceFederationError("SKILL_CANDIDATE_REQUIRES_MULTI_PROJECT_PROOF")
    if len(procedure) < 2 or not inputs or not outputs:
        raise ExperienceFederationError("SKILL_CANDIDATE_REQUIRES_STABLE_IO_AND_PROCEDURE")
    seed = {
        "record_id": record.get("record_id"),
        "lesson": record.get("lesson"),
        "procedure": procedure,
        "inputs": inputs,
        "outputs": outputs,
    }
    candidate_id = "skill-candidate-" + hashlib.sha256(_stable(seed).encode("utf-8")).hexdigest()[:24]
    return {
        "schema": SKILL_CANDIDATE_SCHEMA,
        "status": "CANDIDATE",
        "candidate_id": candidate_id,
        "source_shared_experience_id": record.get("record_id"),
        "trigger_tokens": list(record.get("trigger_tokens") or ()),
        "purpose": record.get("lesson"),
        "procedure": procedure,
        "inputs": inputs,
        "outputs": outputs,
        "evidence": list(record.get("verification_evidence") or ()) + list(record.get("scope_evidence") or ()),
        "activation_authority": "NONE",
        "registry_mutation": "NO",
        "skill_file_created": "NO",
        "must_pass_existing_skill_eligibility": True,
        "must_receive_activation_receipt_when_activated": True,
    }


def skill_candidate_from_catalog(
    record_id: str,
    *,
    catalog_path: str | Path | None = None,
) -> dict[str, Any]:
    catalog = load_catalog(catalog_path)
    record = next((item for item in catalog.get("records") or () if item.get("record_id") == record_id), None)
    if record is None:
        raise ExperienceFederationError("SHARED_EXPERIENCE_RECORD_NOT_FOUND")
    return build_skill_candidate(record)


def _read_json(path: str | Path) -> Mapping[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ExperienceFederationError("JSON_OBJECT_REQUIRED")
    return value


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync")
    sync.add_argument("--root", default=".")
    sync.add_argument("--domain", default="")
    sync.add_argument("--catalog")

    apply_cmd = sub.add_parser("apply")
    apply_cmd.add_argument("--proposal-file", required=True)
    apply_cmd.add_argument("--catalog")

    skill = sub.add_parser("skill-candidate")
    skill.add_argument("--record-id", required=True)
    skill.add_argument("--catalog")

    args = parser.parse_args(argv)
    try:
        if args.command == "sync":
            result = sync_shared_catalog(args.root, domain=args.domain, catalog_path=args.catalog)
        elif args.command == "apply":
            result = apply_promotion(_read_json(args.proposal_file), catalog_path=args.catalog)
        else:
            result = skill_candidate_from_catalog(args.record_id, catalog_path=args.catalog)
    except (ExperienceFederationError, ExperienceEvolutionError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
