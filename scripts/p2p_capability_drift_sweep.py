#!/usr/bin/env python3
"""p2p_capability_drift_sweep.py - deterministic full-index capability drift
revalidation sweep (roadmap item RM-PRIORITY-DRIFT-SWEEP, Issue #293).

Purpose
-------
Account for EVERY record of the canonical capability index
(`docs/p2p-development/capability-ledger/capability-index.json`) with exactly
one explicit current-evidence classification:

``VERIFIED_AT_EVIDENCE_TIME``
    current exact-tree repository evidence is sufficient to verify the bounded
    claim the record makes now.
``UNKNOWN_NOT_PROBED``
    the record's current eligibility cannot be freshly proven from authorized
    evidence now: either it asserts live/provider/host eligibility that was not
    freshly probed, or its declared current-tree anchors do not resolve.

Guarantees
----------
* read-only: never mutates the capability index, roadmap, ledger, or any other
  canonical input;
* fail-closed: malformed/unsupported records abort the sweep with exit code 2
  instead of emitting a partial classification set;
* deterministic apart from the explicit ``generated_at`` / repository identity
  fields;
* no network access, no credential request, no probe, no background work;
* reuses existing canonical inputs and the existing ``runtime/`` ->
  ``.p2p/system/`` path-remap convention. It is sweep evidence only: NOT a
  second capability registry, NOT a second evidence store, NOT a new framework
  layer, and it never rewrites capability statuses.

Exit codes: 0 sweep produced, 2 usage/input error (fail-closed).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SWEEP_SCHEMA = "p2p-capability-drift-sweep/1"
SWEEP_ENGINE = "scripts/p2p_capability_drift_sweep.py"
CAPABILITY_INDEX_REL = "docs/p2p-development/capability-ledger/capability-index.json"
DRIFT_POLICY_REL = "governance/drift-policy.json"
ROADMAP_REL = "governance/p2p-development-roadmap.json"

VERIFIED = "VERIFIED_AT_EVIDENCE_TIME"
UNKNOWN = "UNKNOWN_NOT_PROBED"
CLASSIFICATIONS = (VERIFIED, UNKNOWN)

# Statuses whose records make a current implementation/readiness claim.
IMPLEMENTATION_CLAIM_STATUSES = ("VERIFIED_IMPLEMENTED", "FOUNDATION_READY", "PARTIAL")

# Ref resolution classes.
RESOLVED = "RESOLVED_IN_TREE"
RESOLVED_REMAP = "RESOLVED_IN_TREE_REMAP"
RESOLVED_BASENAME = "RESOLVED_IN_TREE_BASENAME_MATCH"
RESOLVED_DIRECTORY = "RESOLVED_IN_TREE_DIRECTORY"
NOT_CURRENT_TREE_NON_DURABLE = "NOT_CURRENT_TREE_NON_DURABLE"
ABSENT = "ABSENT_IN_TREE"
NON_PATH = "NON_PATH_REFERENCE"
RESOLVED_CLASSES = (RESOLVED, RESOLVED_REMAP, RESOLVED_BASENAME, RESOLVED_DIRECTORY)
NON_TREE_CLASSES = (NOT_CURRENT_TREE_NON_DURABLE,)

# Explicit live-lineage declarations carried by a record itself.
LIVE_DECLARATION_FIELDS = (
    "historical_single_host_live_council_8_of_8",
    "current_lineage_full_council_live_proven",
    "current_lineage_full_council_status",
)
# Evidence anchors that are live-probe/live-certification artifacts: their
# freshness cannot be re-proven from the repository alone.
LIVE_ARTIFACT_RE = re.compile(r"(?i)(live[-_]?probe|live[-_]?cert|auth[-_]?probe|attestation)")
# Declared subject tokens for records about external hosts/providers/live execution.
LIVE_SUBJECT_RE = re.compile(
    r"(?i)(?:^|[_.\s])(LIVE|HOST|PROVIDER|ADAPTER|BACKEND|MANUS|HERMES|COUNCIL|ATTESTATION|"
    r"EXECUTION_TARGET|C27|C34)(?:$|[_.\s])"
)
# A record ASSERTS current external eligibility only when it says so explicitly.
# Generic mentions of "certification" as a practice are not assertions.
ELIGIBILITY_ASSERTION_RE = re.compile(
    r"(?i)(được chứng nhận|đã chứng nhận|\bis certified\b|\bare certified\b|"
    r"currently eligible|current auth state\s*[:=]\s*AUTHENTICATED)"
)
# An explicit disclaimer means the record is already honest: no mutation needed.
DISCLAIMER_RE = re.compile(
    r"(?i)(NOT_CERTIFIED|NOT_PROVEN|UNKNOWN_NOT_PROBED|CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN=FALSE|"
    r"remains? unknown|live[_\s-]?(host|adapter)[_\s-]?certification\s+(is\s+)?still\s+not\s+verified)"
)
# Documented packaged-runtime remap already used by the release/source-binding flow.
PATH_ALIASES = (("runtime/", ".p2p/system/"),)
_PATH_EXT_RE = re.compile(
    r"\.(?:json|md|py|txt|sh|ps1|toml|yml|yaml|zip|html|ts|js|jsonl|log|csv|cfg|ini)$",
    re.IGNORECASE,
)
CLAIM_TEXT_FIELDS = ("name", "title", "beginner_value", "principle", "notes", "next_condition",
                     "known_gaps", "known_gap")


class SweepError(RuntimeError):
    """Fail-closed sweep input/record error."""


# --------------------------------------------------------------------------- tree


class TreeIndex:
    """Current-tree evidence index: tracked files plus a non-durable oracle."""

    def __init__(self, tracked=(), ignored=()):
        self.tracked = frozenset(tracked)
        self.ignored = frozenset(ignored)
        self._by_basename = {}
        for path in sorted(self.tracked):
            self._by_basename.setdefault(path.rsplit("/", 1)[-1], []).append(path)

    @classmethod
    def from_repo(cls, root: Path):
        try:
            raw = subprocess.run(
                ["git", "ls-files", "-z"],
                cwd=str(root), capture_output=True, check=True,
            ).stdout.decode("utf-8", "replace")
        except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
            raise SweepError(f"cannot read current tree index: {exc}") from exc
        return cls(tracked=[p for p in raw.split("\0") if p])

    def exists(self, rel_path: str) -> bool:
        return rel_path in self.tracked

    def basename_hits(self, rel_path: str):
        return tuple(self._by_basename.get(rel_path.rsplit("/", 1)[-1], ()))

    def directory_exists(self, rel_dir: str) -> bool:
        prefix = rel_dir.rstrip("/") + "/"
        return any(path.startswith(prefix) for path in self.tracked)

    def is_non_durable(self, rel_path: str) -> bool:
        """True when a path is declared local/volatile state (never tree evidence)."""
        for prefix in self.ignored:
            root = prefix.rstrip("/")
            if rel_path == root or rel_path.startswith(root + "/"):
                return True
        return False


def _git_output(root: Path, args):
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, check=False)


def git_identity(root: Path) -> dict:
    head = _git_output(root, ["rev-parse", "HEAD"])
    tree = _git_output(root, ["rev-parse", "HEAD^{tree}"])
    branch = _git_output(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if head.returncode != 0 or tree.returncode != 0:
        raise SweepError("cannot resolve repository HEAD/tree")
    return {
        "head": head.stdout.strip(),
        "tree": tree.stdout.strip(),
        "branch": branch.stdout.strip() if branch.returncode == 0 else "",
    }


def is_git_ignored(root: Path, rel_path: str) -> bool:
    """True when the path is git-ignored, i.e. local/volatile state, never tree evidence."""
    return _git_output(root, ["check-ignore", "-q", "--", rel_path]).returncode == 0


# ----------------------------------------------------------------------- records


@dataclass
class RefResolution:
    ref: str
    resolution: str
    resolved_path: str = ""
    note: str = ""

    def as_dict(self) -> dict:
        out = {"ref": self.ref, "resolution": self.resolution}
        if self.resolved_path:
            out["resolved_path"] = self.resolved_path
        if self.note:
            out["note"] = self.note
        return out


def _path_candidate(raw: str, tree: TreeIndex) -> str:
    """Extract a path-like token from a declared reference, if there is one.

    A token counts as path-like only when it has a file extension, an explicit
    ``./`` / ``../`` prefix, a trailing slash, or matches a tracked directory.
    Provenance labels that merely contain slashes (``RA-EXT-021/022/019/023``,
    ``role_bridge/role_receipt/role_verifier``) stay non-path references.
    """
    text = raw.strip()
    if not text:
        return ""
    text = re.sub(r"\s*\((?:[^()]*)\)\s*$", "", text).strip()
    token = text.split(" ", 1)[0].split(";", 1)[0].strip().rstrip(".,:")
    if not token:
        return ""
    token = token.lstrip("/") if token.startswith("/") else token
    if (_PATH_EXT_RE.search(token) or token.startswith(("./", "../"))
            or token.endswith("/") or tree.directory_exists(token)):
        return token
    return ""


def resolve_ref(tree: TreeIndex, raw: str, *, root: Path | None = None) -> RefResolution:
    candidate = _path_candidate(raw, tree)
    if not candidate:
        return RefResolution(raw, NON_PATH, note="reference carries no filesystem token")

    if candidate.endswith("/") or tree.directory_exists(candidate):
        if tree.directory_exists(candidate):
            return RefResolution(raw, RESOLVED_DIRECTORY, candidate)
        if tree.is_non_durable(candidate) or (root is not None and (
                is_git_ignored(root, candidate) or is_git_ignored(root, candidate.rstrip("/")))):
            return RefResolution(raw, NOT_CURRENT_TREE_NON_DURABLE, candidate,
                                 "git-ignored runtime/temporary state is never current-tree evidence")
        return RefResolution(raw, ABSENT, candidate)

    for path, note in _alias_candidates(candidate):
        if tree.exists(path):
            return RefResolution(raw, RESOLVED if path == candidate else RESOLVED_REMAP, path, note)
    hits = tree.basename_hits(candidate)
    if len(hits) == 1 and hits[0] != candidate:
        # The declared directory is not authoritative; a unique basename match
        # in the current tree still resolves the referenced artifact.
        return RefResolution(raw, RESOLVED_BASENAME, hits[0],
                             "unique basename match outside the declared path")
    if tree.is_non_durable(candidate) or (root is not None and is_git_ignored(root, candidate)):
        return RefResolution(raw, NOT_CURRENT_TREE_NON_DURABLE, candidate,
                             "git-ignored runtime/temporary state is never current-tree evidence")
    return RefResolution(raw, ABSENT, candidate)


def _alias_candidates(candidate: str):
    yield candidate, ""
    for src, dst in PATH_ALIASES:
        if candidate.startswith(src):
            yield dst + candidate[len(src):], f"documented {src} -> {dst} remap"


def declared_implementation_refs(record: dict):
    """Declared implementation anchors plus a legacy-shape marker.

    Canonical field is ``implementation_refs``. Some recovered legacy records
    declare artifacts only under ``first_implementation.artifacts``; that legacy
    shape is read (never silently rewritten) and reported as a structural finding.
    """
    refs = record.get("implementation_refs")
    if isinstance(refs, list) and refs:
        return list(refs), False
    legacy = record.get("first_implementation")
    if isinstance(legacy, dict):
        artifacts = legacy.get("artifacts")
        if isinstance(artifacts, list) and artifacts:
            return list(artifacts), True
    return list(refs or []), False


def _claim_text(record: dict) -> str:
    parts = []
    for name in CLAIM_TEXT_FIELDS:
        value = record.get(name)
        if isinstance(value, str) and value:
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(v) for v in value if isinstance(v, str))
    return " | ".join(parts)


def classify_record(record: dict, tree: TreeIndex, *, root: Path | None = None) -> dict:
    """Classify one capability record against current exact-tree evidence."""
    capability_id = record.get("capability_id")
    if not isinstance(capability_id, str) or not capability_id.strip():
        raise SweepError("capability record without a usable capability_id")
    status = record.get("status")
    if not isinstance(status, str) or not status.strip():
        raise SweepError(f"{capability_id}: capability record without a status")

    impl_refs, legacy_impl_shape = declared_implementation_refs(record)
    ev_refs = list(record.get("evidence_refs") or [])
    org_refs = list(record.get("origin_refs") or [])
    impl_res = [resolve_ref(tree, r, root=root) for r in impl_refs]
    ev_res = [resolve_ref(tree, r, root=root) for r in ev_refs]
    org_res = [resolve_ref(tree, r, root=root) for r in org_refs]
    all_res = impl_res + ev_res + org_res

    in_tree_impl = [r for r in impl_res if r.resolution in RESOLVED_CLASSES]
    in_tree_ev = [r for r in ev_res if r.resolution in RESOLVED_CLASSES]
    in_tree_org = [r for r in org_res if r.resolution in RESOLVED_CLASSES]
    absent_impl = [r for r in impl_res if r.resolution == ABSENT]
    absent_ev = [r for r in ev_res if r.resolution == ABSENT]
    absent_org = [r for r in org_res if r.resolution == ABSENT]
    non_durable = [r for r in all_res if r.resolution in NON_TREE_CLASSES]

    text = _claim_text(record)
    declared_live = [f for f in LIVE_DECLARATION_FIELDS if f in record]
    live_subject = LIVE_SUBJECT_RE.search(f"{capability_id} {record.get('name', '') or ''}") is not None
    live_artifact_anchor = any(LIVE_ARTIFACT_RE.search(r.resolved_path or r.ref) for r in ev_res)
    path_impl = [r for r in impl_res if r.resolution != NON_PATH]
    path_ev = [r for r in ev_res if r.resolution != NON_PATH]

    live_basis = []
    if declared_live:
        live_basis.append("DECLARED_LIVE_LINEAGE_FIELDS:" + ",".join(sorted(declared_live)))
    if live_artifact_anchor:
        live_basis.append("LIVE_PROBE_OR_CERTIFICATION_EVIDENCE_ANCHOR")
    if live_subject:
        live_basis.append("EXTERNAL_HOST_OR_PROVIDER_SUBJECT")
    if path_impl and all(r.resolution in NON_TREE_CLASSES for r in path_impl):
        live_basis.append("IMPLEMENTATION_ANCHOR_IS_NON_DURABLE_STATE")
    if path_ev and not in_tree_ev and all(r.resolution in NON_TREE_CLASSES for r in path_ev):
        live_basis.append("ONLY_EVIDENCE_ANCHORS_ARE_NON_DURABLE_STATE")

    live_dependency = bool(live_basis)

    disclaimer = DISCLAIMER_RE.search(text) is not None
    assertion = ELIGIBILITY_ASSERTION_RE.search(text)
    assertion_basis = assertion.group(0) if assertion else ""
    current_eligibility_claim = bool(
        record.get("current_lineage_full_council_live_proven") is True
        or (assertion is not None and not disclaimer)
    )

    structural = []
    if legacy_impl_shape:
        structural.append("LEGACY_NESTED_IMPLEMENTATION_SHAPE(first_implementation.artifacts)")
    for required in ("name", "family", "beginner_value", "principle", "origin_type", "dependencies"):
        if required not in record:
            structural.append(f"MISSING_FIELD:{required}")

    reason = ""
    claim_scope = "RECORD_AND_PROVENANCE"
    implementation_eligibility = "NOT_CLAIMED"
    if status in IMPLEMENTATION_CLAIM_STATUSES:
        implementation_eligibility = "NOT_PROBED"
        claim_scope = "STATIC_IMPLEMENTATION"
        no_in_tree_anchor = not (in_tree_impl or in_tree_ev)
        if current_eligibility_claim:
            classification, reason = UNKNOWN, "LIVE_ELIGIBILITY_NOT_FRESHLY_PROVABLE"
            claim_scope = "LIVE_DEPENDENT_ELIGIBILITY"
        elif no_in_tree_anchor and live_dependency:
            classification, reason = UNKNOWN, "LIVE_ELIGIBILITY_NOT_FRESHLY_PROVABLE"
            claim_scope = "LIVE_DEPENDENT_ELIGIBILITY"
        elif absent_impl:
            classification = UNKNOWN
            reason = "DECLARED_IMPLEMENTATION_ANCHOR_ABSENT_IN_TREE"
        elif ev_refs and not in_tree_ev:
            classification = UNKNOWN
            reason = "NO_CURRENT_TREE_EVIDENCE_ANCHOR"
        elif in_tree_impl:
            classification = VERIFIED
            reason = "IMPLEMENTATION_ANCHOR_RESOLVES_IN_CURRENT_TREE"
            implementation_eligibility = "STATICALLY_SUPPORTED"
        elif impl_res and not path_impl:
            classification = VERIFIED
            reason = "PROSE_IMPLEMENTATION_ANCHOR_RESOLVES_VIA_CURRENT_TREE_EVIDENCE"
            implementation_eligibility = "EVIDENCE_SUPPORTED"
        elif not impl_res and in_tree_ev:
            classification = VERIFIED
            reason = "EVIDENCE_ANCHOR_RESOLVES_IMPLEMENTATION_NOT_DECLARED"
            implementation_eligibility = "EVIDENCE_SUPPORTED"
        elif not impl_res:
            classification = UNKNOWN
            reason = "NO_DECLARED_IMPLEMENTATION_ANCHOR"
        elif path_impl and all(r.resolution in NON_TREE_CLASSES for r in path_impl):
            classification = UNKNOWN
            reason = "DECLARED_IMPLEMENTATION_ANCHOR_IS_NON_DURABLE_STATE"
        else:
            classification = UNKNOWN
            reason = "DECLARED_ANCHORS_UNRESOLVED_IN_CURRENT_TREE"
    else:
        if (absent_impl or absent_ev or absent_org) and not (in_tree_impl or in_tree_ev or in_tree_org):
            classification = UNKNOWN
            reason = "DECLARED_PROVENANCE_ANCHOR_ABSENT_IN_TREE"
        else:
            classification = VERIFIED
            reason = "RECORD_AND_PROVENANCE_PRESENT_IMPLEMENTATION_NOT_CLAIMED"

    stale = bool(status in IMPLEMENTATION_CLAIM_STATUSES and (absent_impl or absent_ev))
    # A record that already discloses its unresolved pointer in its own text has
    # been reconciled: history stays, and the stale pointer is no longer
    # presented as current evidence.
    stale_anchors = absent_impl + absent_ev
    disclosed = bool(stale_anchors) and all(
        (r.resolved_path or r.ref).rsplit("/", 1)[-1] in text for r in stale_anchors)
    if stale:
        stale_action = ("DISCLOSED_IN_RECORD_HISTORY_PRESERVED" if disclosed
                        else "PENDING_RECONCILIATION")
    else:
        stale_action = "NONE_REQUIRED"
    return {
        "capability_id": capability_id,
        "family": record.get("family", ""),
        "original_status": status,
        "current_classification": classification,
        "claim_scope": claim_scope,
        "implementation_eligibility": implementation_eligibility,
        "live_dependency": live_dependency,
        "live_dependency_basis": live_basis,
        "current_eligibility_claim": current_eligibility_claim,
        "eligibility_assertion_present": assertion is not None,
        "current_eligibility_claim_basis": assertion_basis,
        "explicit_disclaimer_present": disclaimer,
        "reason": reason,
        "evidence_refs": [r.resolved_path for r in in_tree_impl + in_tree_ev if r.resolved_path],
        "unresolved_refs": [r.as_dict() for r in all_res if r.resolution in (ABSENT, NOT_CURRENT_TREE_NON_DURABLE)],
        "ref_resolution": {
            "implementation": [r.as_dict() for r in impl_res],
            "evidence": [r.as_dict() for r in ev_res],
            "origin": [r.as_dict() for r in org_res],
        },
        "stale_claim": stale,
        "stale_claim_disclosed_in_record": disclosed,
        "stale_claim_action": stale_action,
        "structural_findings": structural,
        "declared_freshness": record.get("freshness", ""),
    }


# ------------------------------------------------------------------------- sweep


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_sweep(root: Path, *, generated_at: str | None = None) -> dict:
    tree = TreeIndex.from_repo(root)
    index_path = root / CAPABILITY_INDEX_REL
    policy_path = root / DRIFT_POLICY_REL
    if not index_path.is_file():
        raise SweepError(f"capability index not found: {CAPABILITY_INDEX_REL}")
    if not policy_path.is_file():
        raise SweepError(f"drift policy not found: {DRIFT_POLICY_REL}")

    index = json.loads(index_path.read_text(encoding="utf-8"))
    vocabulary = list(index.get("status_vocabulary") or [])
    records = index.get("capabilities")
    if not isinstance(records, list) or not records:
        raise SweepError("capability index carries no capabilities list")

    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise SweepError("capability record is not an object")
        capability_id = record.get("capability_id")
        if capability_id in seen:
            raise SweepError(f"duplicate capability_id: {capability_id}")
        seen.add(capability_id)
        status = record.get("status")
        if vocabulary and status not in vocabulary:
            raise SweepError(
                f"{capability_id}: status {status!r} is outside the declared status vocabulary")

    entries = [classify_record(record, tree, root=root) for record in records]
    if len(entries) != len(records):  # defensive: full coverage is mandatory
        raise SweepError("sweep did not cover every capability record")

    by_classification = {name: 0 for name in CLASSIFICATIONS}
    by_status: dict = {}
    for entry in entries:
        by_classification[entry["current_classification"]] += 1
        by_status[entry["original_status"]] = by_status.get(entry["original_status"], 0) + 1

    stale_claims = [
        {
            "capability_id": e["capability_id"],
            "original_status": e["original_status"],
            "declared_freshness": e["declared_freshness"],
            "unresolved_refs": e["unresolved_refs"],
            "action": e["stale_claim_action"],
        }
        for e in entries if e["stale_claim"]
    ]
    structural_findings = [
        {"capability_id": e["capability_id"], "findings": e["structural_findings"]}
        for e in entries if e["structural_findings"]
    ]

    return {
        "schema": SWEEP_SCHEMA,
        "generated_at": generated_at or _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": SWEEP_ENGINE,
        "swept_repository": git_identity(root),
        "binding_note": (
            "The durable binding of this sweep is inputs.capability_index.sha256 plus the "
            "per-record content; swept_repository.head/tree identify the commit the tree was "
            "read at, which is necessarily the parent of the commit that stores this artifact."
        ),
        "inputs": {
            "capability_index": {
                "path": CAPABILITY_INDEX_REL,
                "sha256": _sha256_file(index_path),
                "record_count": len(entries),
            },
            "drift_policy": {"path": DRIFT_POLICY_REL, "sha256": _sha256_file(policy_path)},
            "roadmap": {
                "path": ROADMAP_REL,
                "sha256": _sha256_file(root / ROADMAP_REL) if (root / ROADMAP_REL).is_file() else "",
            },
        },
        "classification_vocabulary": list(CLASSIFICATIONS),
        "probe_policy": {
            "live_probes_run": 0,
            "live_probes_skipped": (
                "no fresh, authorized, proportionate live/provider/host probe was performed; "
                "live-dependent eligibility stays UNKNOWN_NOT_PROBED and historical "
                "certification stays historical"
            ),
        },
        "counts": {
            "total_records": len(entries),
            "capability_index_records": len(records),
            "by_classification": by_classification,
            "by_original_status": dict(sorted(by_status.items())),
            "live_dependency": sum(1 for e in entries if e["live_dependency"]),
            "current_eligibility_claims": sum(1 for e in entries if e["current_eligibility_claim"]),
            "stale_claims": len(stale_claims),
            "stale_claims_disclosed_in_record": sum(
                1 for e in entries if e["stale_claim"] and e["stale_claim_disclosed_in_record"]),
            "stale_claims_pending_reconciliation": sum(
                1 for e in entries if e["stale_claim"] and not e["stale_claim_disclosed_in_record"]),
            "records_with_structural_findings": len(structural_findings),
        },
        "records": entries,
        "stale_claims": stale_claims,
        "structural_findings": structural_findings,
    }


# ------------------------------------------------------------------------ report


def render_report(sweep: dict) -> str:
    counts = sweep["counts"]
    by_class = counts["by_classification"]
    index = sweep["inputs"]["capability_index"]
    lines = [
        "# P2P Capability Drift Revalidation Sweep - evidence report",
        "",
        f"- Sweep schema: `{sweep['schema']}` (generated {sweep['generated_at']})",
        f"- Swept tree: `{sweep['swept_repository']['head']}` / tree "
        f"`{sweep['swept_repository']['tree']}` (branch `{sweep['swept_repository']['branch']}`)",
        f"- Capability index: `{index['path']}` sha256 `{index['sha256']}`",
        f"- Drift policy sha256: `{sweep['inputs']['drift_policy']['sha256']}`",
        "",
        "## Totals",
        "",
        f"- total capability records accounted for: **{counts['total_records']}** "
        f"(capability index: {counts['capability_index_records']})",
        f"- VERIFIED_AT_EVIDENCE_TIME: **{by_class.get(VERIFIED, 0)}**",
        f"- UNKNOWN_NOT_PROBED: **{by_class.get(UNKNOWN, 0)}**",
        f"- live-dependent records (flag only, never infer eligibility): {counts['live_dependency']}",
        f"- records asserting current external eligibility: {counts['current_eligibility_claims']}",
        f"- stale claims found: {counts['stale_claims']} "
        f"(disclosed in-record: {counts['stale_claims_disclosed_in_record']}; "
        f"pending reconciliation: {counts['stale_claims_pending_reconciliation']})",
        f"- live probes run: {sweep['probe_policy']['live_probes_run']}",
        "",
        "## Classification semantics",
        "",
        "`VERIFIED_AT_EVIDENCE_TIME` means current exact-tree repository evidence is",
        "sufficient to verify the bounded claim the record makes *now*. For records whose",
        "status is PLANNED/DEFERRED/REJECTED/UNKNOWN the verified claim is only that the",
        "record and its provenance exist and that no implementation or runtime eligibility",
        "is being asserted. `implementation_eligibility` distinguishes that explicitly:",
        "`STATICALLY_SUPPORTED` (current source/contract resolves) versus `NOT_CLAIMED`",
        "(record/provenance only) versus `NOT_PROBED`.",
        "",
        "`UNKNOWN_NOT_PROBED` means current eligibility cannot be freshly proven from",
        "authorized evidence now (unre-probed live/provider/host dependence, or declared",
        "anchors that do not resolve in the current tree). Historical certification stays",
        "historical and is never promoted to current eligibility.",
        "",
        "`live_dependency=yes` marks records that concern volatile external state; it is",
        "an information flag and never implies current eligibility.",
        "",
        "## Records by original status",
        "",
        "| status | records |",
        "| --- | --- |",
    ]
    for status, count in counts["by_original_status"].items():
        lines.append(f"| {status} | {count} |")

    unknown = [e for e in sweep["records"] if e["current_classification"] == UNKNOWN]
    lines += ["", f"## UNKNOWN_NOT_PROBED records ({len(unknown)})", "",
              "| capability_id | status | reason | live | disclaimer |",
              "| --- | --- | --- | --- | --- |"]
    for entry in unknown:
        lines.append(
            f"| {entry['capability_id']} | {entry['original_status']} | {entry['reason']} | "
            f"{'yes' if entry['live_dependency'] else 'no'} | "
            f"{'yes' if entry['explicit_disclaimer_present'] else 'no'} |")

    expired = [e for e in sweep["records"]
               if e["eligibility_assertion_present"] and e["explicit_disclaimer_present"]]
    lines += ["", f"## Current-eligibility claims expired or corrected ({len(expired)})", ""]
    if expired:
        for entry in expired:
            lines.append(
                f"- **{entry['capability_id']}** ({entry['original_status']}, "
                f"`{entry['current_classification']}`): asserted `{entry['current_eligibility_claim_basis']}` "
                "and now carries an explicit historical/UNKNOWN_NOT_PROBED disclaimer, so the "
                "historical certification is retained as history and is not current eligibility.")
    else:
        lines.append("No record still presents a historical certification as current eligibility.")

    lines += ["", f"## Stale claims found ({len(sweep['stale_claims'])})", ""]
    if sweep["stale_claims"]:
        for stale in sweep["stale_claims"]:
            refs = ", ".join(f"`{r['ref']}` ({r['resolution']})" for r in stale["unresolved_refs"])
            lines.append(f"- **{stale['capability_id']}** ({stale['original_status']}, declared "
                         f"freshness `{stale['declared_freshness']}`, action "
                         f"`{stale['action']}`): {refs}")
    else:
        lines.append("No implementation-claiming record depends on an absent current-tree anchor.")

    lines += ["", f"## Structural findings ({len(sweep['structural_findings'])})", ""]
    if sweep["structural_findings"]:
        for finding in sweep["structural_findings"]:
            lines.append(f"- **{finding['capability_id']}**: {', '.join(finding['findings'])}")
    else:
        lines.append("None.")

    lines += ["", "## Requires later Owner decision", ""]
    decisions = []
    if unknown:
        decisions.append(
            "UNKNOWN_NOT_PROBED records keep their honest state. Converting any of them to "
            "VERIFIED requires new authorized evidence (a fresh live probe, or a resolvable "
            "current-tree anchor for an implementation claim); this sweep must not manufacture it.")
    if sweep["structural_findings"]:
        decisions.append(
            "Records with structural findings do not satisfy the capability-ledger schema "
            "(missing required fields and/or the legacy nested implementation shape). "
            "Normalising them is a separate bounded change and was deliberately not performed "
            "by this read-only sweep.")
    lines += [f"- {d}" for d in decisions] if decisions else ["- None."]
    lines += ["", f"Machine-readable sweep: `{index['path'].rsplit('/', 1)[0]}/capability-drift-sweep.json`", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- cli


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: current directory)")
    parser.add_argument("--artifact", help="write the machine-readable sweep JSON to this path")
    parser.add_argument("--report", help="write the human evidence report to this path")
    parser.add_argument("--generated-at", help="override generated_at (determinism/tests)")
    parser.add_argument("--summary", action="store_true", help="print a compact summary")
    args = parser.parse_args(argv)

    root = Path(args.repo).resolve()
    try:
        sweep = build_sweep(root, generated_at=args.generated_at)
    except SweepError as exc:
        print(f"SWEEP_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2

    if args.artifact:
        out = Path(args.artifact)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(sweep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.report:
        rep = Path(args.report)
        rep.parent.mkdir(parents=True, exist_ok=True)
        rep.write_text(render_report(sweep), encoding="utf-8")

    summary = {
        "total_records": sweep["counts"]["total_records"],
        "capability_index_records": sweep["counts"]["capability_index_records"],
        "by_classification": sweep["counts"]["by_classification"],
        "live_dependency": sweep["counts"]["live_dependency"],
        "current_eligibility_claims": sweep["counts"]["current_eligibility_claims"],
        "stale_claims": sweep["counts"]["stale_claims"],
        "stale_claims_pending_reconciliation": sweep["counts"]["stale_claims_pending_reconciliation"],
        "structural_findings": sweep["counts"]["records_with_structural_findings"],
        "capability_index_sha256": sweep["inputs"]["capability_index"]["sha256"],
    }
    if args.summary or not args.artifact:
        print(json.dumps(summary, indent=2))
    if sweep["counts"]["total_records"] != sweep["counts"]["capability_index_records"]:
        print("SWEEP_FAIL_CLOSED: record count mismatch", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
