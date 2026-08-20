# P2P-FRAMEWORK-04: Quality, Evidence & Learning
# Read-only intelligence surface. Pure functions; no execution, no permission,
# no routing. FW01 remains the sole operating loop. FW04 verifies AFTER
# execution and does not replace the FW01 checkpoint / Continue Gate.
#
# Invariants added by FW04:
#   ROLE_EXECUTION_BINDING != ROLE_CAPABILITY_CERTIFICATION
#   TEST_PASS != TASK_QUALITY_PROVEN
#   CHANGED_FILES != FULL_AFFECTED_SURFACE
#   OBSERVED_OUTCOME != DURABLE_LEARNING
#   LEARNING_CANDIDATE != CANONICAL_TRUTH

from __future__ import annotations

import ast
import dataclasses
import enum
import hashlib
import json
import os
import pathlib
import re
from typing import Any, Dict, List, Optional, Tuple

REGISTRY_DIR = pathlib.Path(__file__).parent
_GOVERNANCE_DIR = pathlib.Path(__file__).resolve().parents[3] / "governance"

# ---------------------------------------------------------------------------
# Canonical vocabularies
# ---------------------------------------------------------------------------

QUALITY_STATUSES = ("QUALITY_VERIFIED", "QUALITY_PARTIAL", "QUALITY_UNKNOWN", "QUALITY_REJECTED")

RISK_CLASSES = ("LOW", "MODERATE", "CROSS_SUBSYSTEM", "SECURITY_DATABASE_PERMISSION", "ARCHITECTURE")

COST_CLASSES = ("CHEAP", "MODERATE", "EXPENSIVE")

MUTATION_CLASSES = ("READ_ONLY", "CONTENT_EDIT", "CODE_EDIT", "CROSS_SUBSYSTEM_EDIT",
                    "SCHEMA_OR_PERMISSION_BOUNDARY", "GENERATED_FILE_EDIT")

EVIDENCE_CLASSES = ("UNKNOWN", "DECLARED", "VERIFIED", "CERTIFIED", "LIVE_CERTIFIED")

FAILURE_CLASSES = (
    "MISSING_REQUIRED_EVIDENCE", "EVAL_NOT_AVAILABLE", "EVAL_FAILED", "IMPACT_UNKNOWN",
    "AFFECTED_SURFACE_INCOMPLETE", "STALE_EVIDENCE", "CERTIFICATION_SCOPE_MISMATCH",
    "INDEPENDENT_VERIFIER_UNAVAILABLE", "QUALITY_CONFLICT", "QUALITY_UNKNOWN",
    "POST_EXECUTION_MUTATION_AMBIGUITY",
)

CONFIDENCE_CLASSES = ("WEAK", "MODERATE", "STRONG")

PROMOTION_REQUIREMENTS = ("OWNER_CONFIRMATION", "REPEATED_EVIDENCE", "CONFLICT_FREE",
                          "GOVERNED_ACCEPTANCE")


class ProjectType(enum.Enum):
    """Evidence-backed project classification (not free text)."""
    GENEALOGY = "genealogy"                 # data integrity, authz boundaries, Supabase/RLS
    GAME_OR_WEB = "game_or_web"             # behavioral/UI/route/state tests
    PYTHON_LIBRARY = "python_library"       # unit/API/typing/package
    UNKNOWN = "unknown"

PROJECT_TYPE_EVIDENCE_MARKERS = {
    ProjectType.GENEALOGY: ("supabase", "rls", "gia_pha", "genealogy", ".env.local"),
    ProjectType.GAME_OR_WEB: ("src/pages", "src/App.", "index.html", "playwright", "ui/", "components/"),
    ProjectType.PYTHON_LIBRARY: ("setup.py", "setup.cfg", "pyproject.toml", "tests/", "__init__.py"),
}


def classify_project_type(project_root: Any) -> ProjectType:
    """Evidence-based project-type classification from the project profile.

    UNKNOWN is the fail-closed default and does NOT imply any single type's
    evals are satisfied. Callers that need type-specific evals must see the
    type-specific evidence themselves.
    """
    root = pathlib.Path(str(project_root))
    scores = {t: 0 for t in ProjectType if t is not ProjectType.UNKNOWN}
    if root.exists():
        seen = {p.relative_to(root) for p in root.glob("**/*")}
        names = " ".join(str(s) for s in seen)
        for t, markers in PROJECT_TYPE_EVIDENCE_MARKERS.items():
            scores[t] = sum(1 for m in markers if m in names)
    best = max(scores, key=lambda t: scores[t]) if scores else ProjectType.UNKNOWN
    return best if (best is not None and scores.get(best, 0) > 0) else ProjectType.UNKNOWN


# ---------------------------------------------------------------------------
# Eval registry — evidence-backed records, NOT a router
# ---------------------------------------------------------------------------

REQUIRED_EVAL_RECORD_FIELDS = (
    "eval_id", "what", "scope", "input", "expected_signal", "reliability",
    "dependencies", "cost_class", "mutation_class", "evidence_output",
    "failure_semantics",
)


def _registry_path() -> pathlib.Path:
    return REGISTRY_DIR / "eval_registry.json"


def load_eval_registry() -> List[Dict[str, Any]]:
    """Load the evidence-backed eval registry. Never executes anything."""
    p = _registry_path()
    if not p.exists():
        return []
    with open(p) as f:
        payload = json.load(f)
    records = payload.get("evals", [])
    for rec in records:
        missing = [k for k in REQUIRED_EVAL_RECORD_FIELDS if k not in rec]
        if missing:
            raise ValueError(f"eval record {rec.get('eval_id')!r} missing {missing}")
    return records


def get_eval_by_id(eval_id: str) -> Optional[Dict[str, Any]]:
    for rec in load_eval_registry():
        if rec["eval_id"] == eval_id:
            return rec
    return None


def deterministic_evals(registry: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Evals whose EXPECTED_SIGNAL is fully deterministically observable.
    Deterministic-first: prefer these whenever they can answer the question.
    """
    return [r for r in (registry or load_eval_registry())
            if r.get("reliability", "").upper() in ("DETERMINISTIC",)]


def model_judgment_evals(registry: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Evals relying on model judgment are INFERRED/REVIEW_JUDGMENT, never FACT."""
    return [r for r in (registry or load_eval_registry())
            if r.get("reliability", "").upper() in ("INFERRED", "REVIEW_JUDGMENT")]


# ---------------------------------------------------------------------------
# Evidence pointer / freshness binding to repository truth
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class EvidencePointer:
    """Any cached evidence bound to repository truth so stale evidence cannot
    silently count as current. UNKNOWN or STALE remain fail-closed where
    required."""
    pointer: str
    source_commit: str
    indexed_commit: Optional[str] = None
    index_version: Optional[str] = None
    generated_at: Optional[str] = None

    def is_stale(self, current_source_commit: str) -> bool:
        if self.source_commit != current_source_commit:
            return True
        if self.indexed_commit is not None and self.indexed_commit != current_source_commit:
            return True
        return False

    def status(self, current_source_commit: str) -> str:
        if not self.source_commit:
            return "UNKNOWN"
        if self.is_stale(current_source_commit):
            return "STALE"
        return "CURRENT"


def git_source_commit(project_root: Any) -> str:
    """Read-ONLY git source-commit fingerprint. Never mutates."""
    import subprocess
    try:
        return subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


# ---------------------------------------------------------------------------
# Code-impact evidence contract (native, deterministic, AST-only)
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class SymbolChange:
    path: str
    symbols: Tuple[str, ...] = ()

    @staticmethod
    def changed_symbols(path: str, old_text: str, new_text: str) -> "SymbolChange":
        """Top-level symbol names present in new_text and absent from old_text,
        plus top-level names whose body changed. Evidence, not claims."""
        def top_names(src: str) -> Dict[str, str]:
            try:
                tree = ast.parse(src)
            except SyntaxError:
                return {}
            names = {}
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names[node.name] = ast.dump(node)
            return names
        before, after = top_names(old_text), top_names(new_text)
        changed = {n for n in set(before) | set(after) if before.get(n) != after.get(n)}
        return SymbolChange(path=path, symbols=tuple(sorted(changed)))


def _import_map(project_root: Any, paths: Tuple[str, ...] = ()) -> Dict[str, Tuple[str, ...]]:
    """Native deterministic import graph (stdlib ast only; no heavy index).
    Maps each local python file -> the set of local modules it imports."""
    root = pathlib.Path(str(project_root))
    files = tuple(p for p in paths) if paths else tuple(
        root.glob("**/*.py"))
    by_relname = {}
    for f in files:
        try:
            rel = pathlib.Path(f).relative_to(root)
        except ValueError:
            continue
        by_relname[str(rel.with_suffix("")).replace(os.sep, "/")] = f

    def _resolve_module(mod_name: str) -> Optional[str]:
        """Map a dotted import name to a file key: exact module path first,
        then progressive trailing paths (src.core -> 'src/core'). The first
        component alone is never enough for packages and is a false-positive
        risk, so it is only used when the exact path exists."""
        dotted = mod_name.replace(".", "/")
        if dotted in by_relname:
            return dotted
        # try __init__ package form (mod/name -> name/__init__)
        for rel in by_relname:
            if rel.replace("/", ".").endswith("." + mod_name) or rel == dotted:
                return rel
        return None

    graph = {}
    for rel, full in by_relname.items():
        try:
            src = full.read_text(errors="replace")
            tree = ast.parse(src)
        except (OSError, SyntaxError):
            continue
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    key = _resolve_module(alias.name)
                    if key is not None and key != rel:
                        deps.append(key)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    key = _resolve_module(node.module)
                    if key is not None and key != rel:
                        deps.append(key)
        graph[rel] = tuple(sorted(set(deps)))
    return graph


def reverse_dependents(import_graph: Dict[str, Tuple[str, ...]]) -> Dict[str, Tuple[str, ...]]:
    """Direct transitive-free reverse dependents (one hop) with provenance."""
    rev: Dict[str, List[str]] = {}
    for mod, deps in import_graph.items():
        for d in deps:
            rev.setdefault(d, []).append(mod)
    return {k: tuple(sorted(v)) for k, v in rev.items()}


def affected_surface(changed_paths: Tuple[str, ...],
                     import_graph: Optional[Dict[str, Tuple[str, ...]]] = None,
                     project_root: Optional[Any] = None,
                     analysis_complete: bool = True) -> Dict[str, Any]:
    """CHANGED_FILES != FULL_AFFECTED_SURFACE. Returns an evidence contract:
    changed_files, changed_symbols (when source texts available),
    direct_dependents, tests_affected, and UNKNOWN_IMPACT classification.

    If impact cannot be established, IMPACT_UNKNOWN applies and callers MUST
    NOT claim 'no regression'.
    """
    changed = tuple(sorted(str(p) for p in changed_paths))
    graph = import_graph
    if graph is None and project_root is not None and analysis_complete:
        try:
            graph = _import_map(pathlib.Path(str(project_root)))
        except OSError:
            graph = {}
            analysis_complete = False
    if graph is None:
        analysis_complete = False

    dependents: Dict[str, Tuple[str, ...]] = {}
    tests_affected: Tuple[str, ...] = ()
    if graph is not None:
        rev = reverse_dependents(graph)
        changed_keys = {c if c in rev else c.replace(os.sep, "/").replace(".py", "")
                        for c in changed}
        dependents = {c: rev.get(c, ()) for c in changed_keys if c in rev}
        changed_mods = {p.replace(os.sep, "/").replace(".py", "") for p in changed}
        # Affected surface includes direct dependents AND one deterministic
        # transitive hop over the same AST evidence: CHANGED_FILES != affected.
        transitives: List[str] = []
        for mods in dependents.values():
            for m in mods:
                transitives.extend(rev.get(m, ()))
        direct_deps = set()
        for mods in dependents.values():
            direct_deps.update(mods)
        affected_mods = changed_mods | direct_deps | set(transitives)
        tests_affected = tuple(sorted(
            m for m, deps in graph.items()
            if ("test" in m and set(deps) & affected_mods)))

    return {
        "changed_files": changed,
        "changed_symbols": [],  # requires old/new texts; see record_symbol_changes
        "direct_dependents": dependents,
        "tests_affected": tests_affected,
        "analysis_complete": analysis_complete,
        "impact_unknown": not analysis_complete or len(graph or {}) == 0,
    }


def record_symbol_changes(project_root: Any, changes: Tuple[SymbolChange, ...]
                          ) -> Dict[str, Any]:
    """Attach per-file changed-symbol evidence to an impact contract."""
    return {"changed_symbols": [
        {"path": sc.path, "symbols": list(sc.symbols)} for sc in changes]}


# ---------------------------------------------------------------------------
# Quality Contract — per-task, derived from evidence
# ---------------------------------------------------------------------------

MINIMAL_QUALITY_CONTRACT_FIELDS = (
    "task_ref", "quality_requirements", "required_verification",
    "required_evidence", "risk_class", "affected_surface_requirements",
    "project_evals_required", "independent_review_required",
    "fail_closed_conditions",
)


def _risk_class(mutation_class: str, requirements: Tuple[str, ...] = ()) -> str:
    if mutation_class in ("SCHEMA_OR_PERMISSION_BOUNDARY",):
        return "SECURITY_DATABASE_PERMISSION"
    if mutation_class == "CROSS_SUBSYSTEM_EDIT":
        return "CROSS_SUBSYSTEM"
    sensitive = {"authorization", "permission", "rls", "supabase", "schema", "database"}
    if any(s in (r or "").lower() for r in requirements for s in sensitive):
        return "SECURITY_DATABASE_PERMISSION"
    return "LOW"


def build_quality_contract(task_ref: str,
                           acceptance_requirements: Tuple[str, ...] = (),
                           project_root: Optional[Any] = None,
                           required_capabilities: Tuple[str, ...] = (),
                           mutation_class: str = "READ_ONLY",
                           independent_review_required: bool = False
                           ) -> Dict[str, Any]:
    """Compact per-task Quality Contract derived from evidence. No manual
    Owner selection of technical evals: eval choice follows from the risk
    class and project type evidence."""
    project_type = classify_project_type(project_root) if project_root else ProjectType.UNKNOWN
    risk_class = _risk_class(mutation_class, acceptance_requirements)

    registry = load_eval_registry()
    required_evals = [r["eval_id"] for r in registry if _eval_required_for(
        r, risk_class, mutation_class, project_type, required_capabilities)]
    optional_evals = [r["eval_id"] for r in registry if not _eval_required_for(
        r, risk_class, mutation_class, project_type, required_capabilities)
        and r.get("cost_class", "CHEAP") != "EXPENSIVE"]

    fail_closed = ["MISSING_REQUIRED_EVIDENCE", "EVAL_FAILED", "IMPACT_UNKNOWN",
                   "STALE_EVIDENCE", "CERTIFICATION_SCOPE_MISMATCH"]

    contract = {
        "task_ref": task_ref,
        "quality_requirements": tuple(acceptance_requirements),
        "required_verification": tuple(required_evals),
        "required_evidence": tuple(required_capabilities),
        "risk_class": risk_class,
        "affected_surface_requirements": "KNOWN_BEFORE_VERDICT",
        "project_evals_required": project_type is not ProjectType.UNKNOWN,
        "independent_review_required": bool(independent_review_required
            or risk_class == "SECURITY_DATABASE_PERMISSION"),
        "fail_closed_conditions": tuple(fail_closed),
        "project_type": project_type.value,
        "optional_evals": tuple(optional_evals),
        "mutation_class": mutation_class,
    }
    for field in MINIMAL_QUALITY_CONTRACT_FIELDS:
        if field not in contract:
            raise ValueError(f"quality contract missing field {field}")
    return contract


def _eval_required_for(record: Dict[str, Any], risk_class: str,
                       mutation_class: str, project_type: ProjectType,
                       required_capabilities: Tuple[str, ...]) -> bool:
    """Match an eval record to a task by evidence: mutation class allowance,
    risk class allowance, and capability scope. Cheap tests first; expensive
    ones only where risk justifies the cost (adaptive verification)."""
    if not record.get("mutation_class") or mutation_class not in record["mutation_class"]:
        return False
    eval_risk = set(record.get("risk_class", []))
    if eval_risk and risk_class not in eval_risk:
        return False
    caps = set(record.get("capability_scope", []))
    if caps and not set(required_capabilities or ()).intersection(caps):
        return False
    return True


# ---------------------------------------------------------------------------
# Capability certification — scope-exact, freshness-aware
# ---------------------------------------------------------------------------

_STATE_DIR = REGISTRY_DIR.parents[1] / "state"
CERTIFICATION_STORE_PATH = _STATE_DIR / "certification_store.json"


def _cert_store() -> Dict[str, Any]:
    if not CERTIFICATION_STORE_PATH.exists():
        return {"records": []}
    with open(CERTIFICATION_STORE_PATH) as f:
        return json.load(f)


def load_certification_records() -> List[Dict[str, Any]]:
    return list(_cert_store().get("records", []))


REQUIRED_CERT_FIELDS = ("eval_id", "eval_version", "capability_id", "subject",
                        "timestamp", "result", "evidence_pointers",
                        "freshness_bound")


def record_capability_certification(eval_id: str,
                                    eval_version: str,
                                    capability_id: str,
                                    subject: str,
                                    result: str,
                                    evidence_pointers: Tuple[str, ...] = (),
                                    target_environment: Optional[str] = None,
                                    timestamp: Optional[str] = None,
                                    freshness_bound: Optional[str] = None
                                    ) -> Dict[str, Any]:
    """Capability-specific certification entry. A generic execution receipt
    (e.g. 'What is the capital of Vietnam?') MUST NOT satisfy a claim such as
    security_audit, database safety, UI design, or architecture review.
    Certified scope is exactly the evaluated capability:
    CERTIFICATION_SCOPE_EXACTNESS."""
    explicit = {"eval_id": eval_id, "eval_version": eval_version,
                "capability_id": capability_id, "subject": subject,
                "timestamp": timestamp, "result": result,
                "evidence_pointers": evidence_pointers}
    for field in REQUIRED_CERT_FIELDS:
        if field == "freshness_bound":
            continue
        if field in ("evidence_pointers",):
            if not isinstance(explicit.get(field), (tuple, list)):
                raise ValueError(f"capability certification missing {field}")
            continue
        if explicit.get(field) in (None, ""):
            raise ValueError(f"capability certification missing {field}")
    entry = {
        "eval_id": eval_id,
        "eval_version": eval_version,
        "capability_id": capability_id,
        "subject": subject,
        "target_environment": target_environment,
        "timestamp": timestamp or _utc_now(),
        "result": result,
        "evidence_pointers": tuple(evidence_pointers),
        "freshness_bound": freshness_bound or "",
        "kind": "CAPABILITY_CERTIFICATION",
    }
    store = _cert_store()
    store["records"].append(entry)
    CERTIFICATION_STORE_PATH.write_text(json.dumps(store, indent=2) + "\n")
    return entry


def record_execution_binding(role_id: str,
                             receipt_pointer: str,
                             capability_scope: Tuple[str, ...] = (),
                             timestamp: Optional[str] = None) -> Dict[str, Any]:
    """ROLE EXECUTION BINDING: 'this role identity really executed'.
    This is identity/execution evidence only, scoped to what it actually
    proved. It does NOT certify any capability.
    CANONICAL_ROLE_REAL_EXECUTION_BINDING / EXACT_8_OF_8_ROLE_BINDING /
    SINGLE_HOST_LIVE_COUNCIL live-evidence records belong to the governance
    record of record and are referenced here by pointer, never rewritten."""
    entry = {
        "role_id": role_id,
        "receipt_pointer": receipt_pointer,
        "capability_scope": tuple(capability_scope),
        "timestamp": timestamp or _utc_now(),
        "kind": "ROLE_EXECUTION_BINDING",
    }
    store = _cert_store()
    store["records"].append(entry)
    CERTIFICATION_STORE_PATH.write_text(json.dumps(store, indent=2) + "\n")
    return entry


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def certification_tier(capability_id: str,
                       subject: Optional[str] = None) -> str:
    """Mechanical tier from evidence records. No free-text self-claim may move
    DECLARED -> CERTIFIED: only EVAL-scoped CERTIFIED/LIVE_CERTIFIED results
    move the tier."""
    tier = "UNKNOWN"
    for rec in load_certification_records():
        if rec.get("capability_id") != capability_id:
            continue
        if subject is not None and rec.get("subject") != subject:
            continue
        kind = rec.get("kind")
        result = (rec.get("result") or "").upper()
        if kind == "CAPABILITY_CERTIFICATION":
            if result == "CERTIFIED":
                tier = "CERTIFIED"
            elif result == "VERIFIED":
                if tier not in ("CERTIFIED",):
                    tier = "VERIFIED"
        elif kind == "ROLE_EXECUTION_BINDING":
            # execution binding supports identity evidence only within scope
            if rec.get("capability_scope") and capability_id in rec["capability_scope"]:
                if result == "LIVE_CERTIFIED" and tier not in ("CERTIFIED",):
                    tier = "LIVE_CERTIFIED"
    return tier


def certification_freshness(capability_id: str,
                            current_source_commit: str,
                            reference_pointers: Tuple[str, ...] = ()) -> str:
    """CURRENT_ELIGIBILITY separated from CERTIFIED_AT. A role may remain
    historically certified while current auth/target is unavailable.
    Unknown or stale -> fail-closed INELIGIBLE, never silently current."""
    if not current_source_commit:
        return "UNKNOWN_STALE"
    store = _cert_store()
    for rec in reversed(store.get("records", [])):
        if rec.get("capability_id") == capability_id:
            bound = rec.get("freshness_bound") or ""
            # No freshness bound -> currency cannot be proven -> fail closed.
            if not bound:
                return "UNBOUND"
            ep = EvidencePointer(pointer="self",
                                 source_commit=bound,
                                 indexed_commit=bound)
            return "CURRENT" if ep.status(current_source_commit) == "CURRENT" else "STALE"
    return "NO_RECORD"


def current_eligibility(capability_id: str,
                        current_source_commit: str,
                        require_evidence_class: str = "VERIFIED") -> Dict[str, Any]:
    """D. CURRENT ELIGIBILITY: 'it can safely execute X now on this target'.
    Certified != currently eligible. Missing freshness evidence fails closed."""
    tier = certification_tier(capability_id)
    tier_ok = _tier_meets(tier, require_evidence_class)
    fresh = certification_freshness(capability_id, current_source_commit)
    eligible = tier_ok and fresh == "CURRENT"
    return {
        "capability_id": capability_id,
        "tier": tier,
        "freshness": fresh,
        "currently_eligible": eligible,
        "fail_closed_on_unknown": not eligible,
    }


# ---------------------------------------------------------------------------
# Capability certification evidence provider (FW03 consumption boundary).
# FW04 produces governed evidence; FW03 reads it at its existing evidence
# boundary. FW04 never selects roles; FW01 remains sole operator.
# ---------------------------------------------------------------------------

def _cert_records_for(capability_id: str) -> Tuple[Dict[str, Any], ...]:
    """Certification records for EXACTLY this capability (scope exactness):
    subject may vary (different candidates/environments), but the
    capability_id is fixed. Role execution bindings without this
    capability in scope are NOT returned."""
    out: List[Dict[str, Any]] = []
    for rec in load_certification_records():
        if str(rec.get("capability_id", "")).lower() \
                != str(capability_id).lower():
            continue
        out.append({
            "kind": rec.get("kind"),
            "subject": rec.get("subject", ""),
            "eval_id": rec.get("eval_id", ""),
            "eval_version": rec.get("eval_version", ""),
            "result": rec.get("result", ""),
            "freshness_bound": rec.get("freshness_bound", ""),
            "evidence_pointers": tuple(rec.get("evidence_pointers", ())),
        })
    return tuple(out)


def load_certification_evidence(
        required_capabilities: Iterable[str],
        current_source_commit: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Certification evidence map (FW03 input). Capability-specific only:
    X certification never satisfies Y. Missing tier/current eligibility
    fails closed (currently_eligible=False); callers MUST NOT treat an
    absent key as 'eligible'."""
    commit = current_source_commit if current_source_commit else ""
    if not commit:
        commit = git_source_commit(pathlib.Path.cwd())
    out: Dict[str, Dict[str, Any]] = {}
    for cap in required_capabilities:
        cap = str(cap)
        if not cap:
            continue
        tier = certification_tier(cap)
        fresh = certification_freshness(cap, commit) if commit else "UNKNOWN_STALE"
        elig = current_eligibility(cap, commit)
        out[cap] = {
            "capability_id": cap,
            "tier": tier,
            "freshness": fresh,
            "currently_eligible": bool(elig.get("currently_eligible", False)),
            "certification_records": _cert_records_for(cap),
            # P2P-FW04 QUALITY STOP — subject binding: which canonical
            # registry roles this certification evidence may legally
            # extend. A certification NEVER attaches to the role that
            # happens to need it; it attaches to the subject it names.
            "certified_roles": _certified_roles_for(cap),
        }
    return out


def _canonical_role_ids(registry_records: Iterable[Any]) -> Set[str]:
    """Canonical registry role ids (from build_team_decision's registry
    records). The subject of a certification must exactly equal one of
    these ids to extend that role's coverage (subject binding).
    Non-role subjects (environment, host, arbitrary string) count for
    NOTHING."""
    ids: Set[str] = set()
    for r in registry_records:
        rec = r if isinstance(r, Mapping) else {}
        if (rec.get("kind") or "") == "ROLE" and rec.get("id"):
            ids.add(str(rec["id"]))
    return ids


def _certified_roles_for(capability_id: str) -> Tuple[str, ...]:
    """Role ids this certification evidence names as subject (subject
    binding). Only CERTIFIED-result records count; subject binding is
    computed HERE so the FW03 boundary stays evidence-only. Currency is
    the consumer's job via currently_eligible — but a record whose
    freshness_bound is unbound is excluded here too, because an unbound
    certification can never attest about any role (fail closed on
    UNKNOWN_STALE/UNBOUND/NO_RECORD)."""
    matched: List[str] = []
    for rec in load_certification_records():
        if str(rec.get("capability_id", "")).lower() \
                != str(capability_id).lower():
            continue
        # CERTIFIED result only: VERIFIED/DECLARED/passing-receipt noise
        # never binds a role.
        if str(rec.get("result", "")).upper() != "CERTIFIED":
            continue
        # Unbound freshness = currency unprovable = no attestation:
        # fail closed, never bind any role from this record.
        if not str(rec.get("freshness_bound", "")).strip():
            continue
        subject = str(rec.get("subject", "")).strip()
        if subject:
            matched.append(subject)
    return tuple(sorted(set(matched)))


def _tier_meets(tier: str, required: str) -> bool:
    order = ["UNKNOWN", "DECLARED", "VERIFIED", "CERTIFIED", "LIVE_CERTIFIED"]
    if tier not in order or required not in order:
        return False
    return order.index(tier) >= order.index(required)


# ---------------------------------------------------------------------------
# Quality verdict — independent from execution success
# ---------------------------------------------------------------------------

QUALITY_VERDICT = {
    "QUALITY_VERIFIED": 0, "QUALITY_PARTIAL": 1,
    "QUALITY_UNKNOWN": 2, "QUALITY_REJECTED": 3,
}


def build_quality_verdict(execution_status: str,
                          required_eval_results: Dict[str, str],
                          optional_eval_results: Optional[Dict[str, str]] = None,
                          impact_known: bool = True,
                          required_evidence_present: bool = True,
                          declared_required_evals: Optional[Dict[str, Any]] = None,
                          independent_verifier_result: Optional[str] = None,
                          independent_required: bool = False
                          ) -> Dict[str, Any]:
    """Structured outcome. Unknown quality must not become PASS: an execution
    SUCCESS with quality_status QUALITY_UNKNOWN must NOT checkpoint as fully
    verified."""
    failures: List[str] = []
    if not impact_known:
        failures.append("IMPACT_UNKNOWN")
    if not required_evidence_present:
        failures.append("MISSING_REQUIRED_EVIDENCE")
    declared = declared_required_evals if declared_required_evals is not None \
        else (required_eval_results or {})
    for eid in (declared or {}):
        result = (required_eval_results or {}).get(eid)
        if result is None:
            failures.append("MISSING_REQUIRED_EVIDENCE")
            break
        status = (result or "").upper()
        if status.startswith("FAIL") or status in ("REJECTED", "EVAL_FAILED"):
            failures.append("EVAL_FAILED")
            break
        if status in ("NOT_AVAILABLE", "EVAL_NOT_AVAILABLE"):
            failures.append("EVAL_NOT_AVAILABLE")
    if independent_required and not independent_verifier_result:
        failures.append("INDEPENDENT_VERIFIER_UNAVAILABLE")

    if "EVAL_FAILED" in failures or "MISSING_REQUIRED_EVIDENCE" in failures:
        status = "QUALITY_REJECTED"
    elif failures:
        # Missing required independent verification and unanalyzed impact both
        # remain UNKNOWN: partial verification is never granted on missing
        # required evidence, only on honest unavailability of optional evals.
        unknown_causes = ("IMPACT_UNKNOWN", "INDEPENDENT_VERIFIER_UNAVAILABLE",
                          "EVAL_NOT_AVAILABLE")
        status = "QUALITY_UNKNOWN" if any(c in failures for c in unknown_causes) \
            else "QUALITY_PARTIAL"
    else:
        status = "QUALITY_VERIFIED"
    return {
        "execution_status": execution_status,
        "quality_status": status,
        "quality_failures": tuple(failures),
        "checkpoint_allowed": (execution_status == "SUCCESS"
                               and status == "QUALITY_VERIFIED"),
        "note": "EXECUTION_SUCCESS != QUALITY_PROVEN",
    }


# ---------------------------------------------------------------------------
# Independent verification
# ---------------------------------------------------------------------------

def verify_independence(executor_identity: str,
                        verifier_identity: str,
                        executor_evidence: str,
                        verifier_evidence: str) -> Dict[str, Any]:
    """The verifier must be meaningfully independent per available evidence.
    The same claim twice does NOT count as independent (no duplicate verifier
    double-counting)."""
    same_identity = executor_identity == verifier_identity
    same_evidence = executor_evidence == verifier_evidence
    independent = not (same_identity or same_evidence)
    return {
        "executor": executor_identity,
        "verifier": verifier_identity,
        "is_independent": independent,
        "reject_reason": "SAME_CLAIM_OR_IDENTITY" if not independent else None,
    }


# ---------------------------------------------------------------------------
# Learning candidates — evidence, not chat memory
# ---------------------------------------------------------------------------

LEARNING_STORE_PATH = _STATE_DIR / "learning_candidates.jsonl"


def _load_candidates() -> List[Dict[str, Any]]:
    if not LEARNING_STORE_PATH.exists():
        return []
    out = []
    for line in LEARNING_STORE_PATH.read_text().splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _append_candidate(c: Dict[str, Any]) -> None:
    with open(LEARNING_STORE_PATH, "a") as f:
        f.write(json.dumps(c, sort_keys=True) + "\n")


def add_learning_candidate(subject: str,
                           proposed_learning: str,
                           evidence_pointers: Tuple[str, ...] = (),
                           scope: str = "PROJECT_SCOPED",
                           observation_count: int = 1,
                           conflicts: Tuple[str, ...] = (),
                           confidence_class: str = "WEAK",
                           promotion_requirement: str = "OWNER_CONFIRMATION"
                           ) -> Dict[str, Any]:
    """TRANSCRIPT != STATE: a chat statement cannot become canonical truth.
    Owner corrections become project-scoped candidates, never universal
    policy, until governed acceptance. One observation never auto-promotes;
    conflicting learning stays unresolved."""
    if observation_count < 1:
        raise ValueError("observation_count must be >= 1")
    existing = _load_candidates()
    conflict = tuple(c2["subject"] for c2 in existing
                     if c2.get("subject") == subject and c2.get("state") != "REJECTED"
                     and c2.get("proposed_learning") != proposed_learning)
    all_conflicts = tuple(sorted(set(conflicts) | set(conflict)))
    cand = {
        "subject": subject,
        "proposed_learning": proposed_learning,
        "evidence_pointers": tuple(evidence_pointers),
        "scope": scope,
        "observation_count": observation_count,
        "conflicts": all_conflicts,
        "freshness": _utc_now(),
        "confidence_class": confidence_class,
        "promotion_requirement": promotion_requirement,
        "state": "CONFLICT" if all_conflicts else "CANDIDATE",
    }
    _append_candidate(cand)
    return cand


def learning_promotion_policy(candidate: Dict[str, Any],
                              governing_facts: Tuple[str, ...] = ()
                              ) -> Dict[str, Any]:
    """OBSERVATION -> EVIDENCE -> CANDIDATE -> CONFLICT CHECK ->
    REPEATABILITY/CONFIDENCE -> GOVERNED ACCEPTANCE -> DURABLE RULE.
    Auto-promotion is forbidden; the honest answer is always CANDIDATE until
    owner-governed acceptance for durable rules."""
    repeatable = candidate.get("observation_count", 0) >= 3
    conflict_free = not candidate.get("conflicts")
    return {
        "subject": candidate["subject"],
        "repeatable": repeatable,
        "conflict_free": conflict_free,
        "auto_promoted": False,
        "promotion_allowed_only_via": "GOVERNED_ACCEPTANCE",
        "state": ("RESOLVED_CANDIDATE" if repeatable and conflict_free
                  else "UNRESOLVED_CONFLICT" if not conflict_free
                  else "CANDIDATE"),
    }


def transcript_must_not_become_state(transcript_statement: str,
                                     proposed_canonical_update: Any) -> Dict[str, Any]:
    """Enforce TRANSCRIPT != STATE: transcript alone cannot become canonical
    project state."""
    return {
        "transcript_statement": transcript_statement,
        "canonical_update_applied": False,
        "reason": "TRANSCRIPT_NOT_STATE",
        "learning_candidate_created_instead": True,
    }


# ---------------------------------------------------------------------------
# Shadow evaluation (READ-ONLY) contract
# ---------------------------------------------------------------------------

def shadow_eval_scope_allowed(mutation_class: str) -> bool:
    """READ-ONLY shadow evaluation must never mutate owner projects."""
    return mutation_class in ("READ_ONLY", "ANALYSIS_ONLY")




# P2P-CLOSURE-01 - persisted adapter registry (runtime state, write-only
# additive ledger; latest entry per adapter_id wins at read time).
_P2P_ADAPTER_REGISTRY_SENTINEL = True
ADAPTER_REGISTRY_PATH = pathlib.Path(os.environ.get(
    "P2P_STATE_DIR", "") or str(
        pathlib.Path(__file__).resolve().parents[1] / ".p2p" / "state")) / \
    "adapter_registry.json"


def _p2p_adapter_registry() -> list:
    try:
        if ADAPTER_REGISTRY_PATH.exists():
            return list(json.loads(ADAPTER_REGISTRY_PATH.read_text())
                        or [])
    except Exception:
        pass
    return []


def append_adapter_registration(adapter_id: str, provider: str,
                                model: str, harness: str,
                                live_certified: bool = False,
                                current_auth_state: str = "READ",
                                attestation_summary: str = "") -> None:
    entry = {"adapter_id": str(adapter_id),
             "provider": str(provider),
             "model": str(model),
             "harness": str(harness),
             "live_certified": bool(live_certified),
             "current_auth_state": str(current_auth_state),
             "attestation_summary": str(attestation_summary)[:500],
             "registered_at": _utc_now()}
    records = _p2p_adapter_registry()
    records.append(entry)
    ADAPTER_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    ADAPTER_REGISTRY_PATH.write_text(json.dumps(records, indent=2)
                                     + "\n")


def registered_adapter_ids() -> tuple:
    seen = {}
    for rec in _p2p_adapter_registry():
        aid = str(rec.get("adapter_id", ""))
        if not aid or aid == "unregistered":
            continue
        if str(rec.get("status", "registered")) in ("revoked",
                                                     "retired"):
            seen.pop(aid, None)
            continue
        seen[aid] = None
    return tuple(sorted(seen))


def latest_adapter_record(adapter_id: str):
    out = None
    for rec in _p2p_adapter_registry():
        if str(rec.get("adapter_id", "")) == str(adapter_id):
            out = dict(rec)
    return out
