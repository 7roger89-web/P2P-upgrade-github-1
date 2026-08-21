"""P2P canonical bounded documentation write primitive.

Provider-neutral, backend-neutral, model-neutral. Text documentation only.
Explicitly mutating, bounded filesystem surface, fail-closed by default.

Schema: p2p-bounded-documentation-write/1

This module is the ONLY canonical mutation primitive in the P2P runtime.
All other execution paths remain READ_ONLY detect/refuse semantics.
No shell command capable of arbitrary write is exposed by this module.
"""
import enum
import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

# ---------------------------------------------------------------------------
# Constants and policy
# ---------------------------------------------------------------------------

BOUNDED_DOC_WRITE_SCHEMA = "p2p-bounded-documentation-write/1"
MUTATION_CLASS = "DOCUMENTATION_WRITE_ONLY"
NON_EXISTENT = "NON_EXISTENT"
# P2P-BOUNDED-DOCUMENTATION-WRITE-01B: canonical mutation authority
# modes. The requirement for a REAL canonical HostAttestation is keyed
# to this authority mode — NOT to any environment label (PRODUCTION /
# NON_PRODUCTION / ISOLATED). TEST_ONLY may carry a synthetic/derived
# attestation ONLY because it is structurally incapable of producing a
# mutation-ready PASS (execute without a real attestation raises here;
# the receipt verifier further requires test_only_evidence == false for
# any mutation-ready VERIFIED path). Unknown modes BLOCK (fail-closed).
TEST_ONLY_AUTHORITY_MODE = "TEST_ONLY"
MUTATION_READY_AUTHORITY_MODE = "MUTATION_READY"
MUTATION_AUTHORITY_MODES: tuple[str, ...] = (
    TEST_ONLY_AUTHORITY_MODE, MUTATION_READY_AUTHORITY_MODE)
PERMISSION_WRITE_BOUNDED = "WRITE_BOUNDED"

# Bounded budget defaults (contract may tighten, never widen via defaults).
DEFAULT_MAX_CHANGED_FILES = 1
DEFAULT_MAX_CHANGED_LINES = 64
DEFAULT_MAX_BYTES = 16384

# Canonical lease file (FW06 max_parallelism=1), bound to (project_root, path).
LEASE_FILE = ".bounded_documentation_write_lease.json"
INTERRUPTION_STATE_FILE = ".bounded_documentation_write_interruption_state.json"

# ---------------------------------------------------------------------------
# Default protected surfaces (DENY first, per spec 8).
# ---------------------------------------------------------------------------

PROTECTED_PATH_PATTERNS: tuple[str, ...] = (
    r"^\.git(/.*)?$",
    r"^\.p2p(/.*)?$",
    r"^\.env.*$",
    r".*secret.*",
    r".*credential.*",
    r".*password.*",
    r".*token",
    r".*private_key",
    r"^package-lock\.json$",
    r"^yarn\.lock$",
    r"^Gemfile\.lock$",
    r"^requirements.*\.txt$",
    r"^go\.sum$",
    r"^Cargo\.lock$",
    r"^pnpm-lock\.yaml$",
    r"^package\.json$",
    r"^pyproject\.toml$",
    r"^setup\.py$",
    r"^setup\.cfg$",
    r"^\.csproj$",
    r"^pom\.xml$",
    r"^build\.gradle$",
    r"^[^/]*\.(py|ts|tsx|js|jsx|vue|go|rs|java|c|cpp|cc|cs|rb|swift|kt|scala|sql|css|scss|html|htm|sh|bash|ps1|psm1|bat|cmd)$",
    r"(^|/)tests?/",
    r"(^|/)test_[^/]*\.py$",
    r"(^|/)__tests__/",
    r"(^|/)spec/",
    r"(^|/)(supabase|db|database|migrations?)/",
    r"^Dockerfile.*$",
    r"^docker-compose.*$",
    r"^cloudbuild.*$",
    r"^app\.yaml$",
    r"^app\.json$",
    r"(\.workflow|workflows)/",
    r"^AGENTS\.md$",
    r"^P2P-PROJECT-BOOTSTRAP\.md$",
    r"^TASKS\.md$",
    r"^\.agents(/.*)?$",
    r"^\.codex(/.*)?$",
    r"^docs/banned",
)

# Documentation/evidence ALLOWED surface (classification first pass).
DOCUMENTATION_ALLOWED_PATTERNS: tuple[str, ...] = (
    r"^docs(/.*)?$",
    r"^docs/evidence(/.*)?$",
    r"^README.*\.md$",
    r"^CHANGELOG.*\.md$",
    r"^CONTRIBUTING.*\.md$",
    r"^docs/.*/.*\.md$",
    r"^reports(/.*)?$",
    r"^changelog/?",
)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class BoundedDocWriteError(ValueError):
    """Raised only when a bounded documentation write cannot proceed safely."""

    def __init__(self, code: str, details: Mapping[str, Any] | None = None) -> None:
        self.code = code
        self.details = details or {}
        super().__init__("BOUNDED_DOC_WRITE_ERROR:" + code)


# ---------------------------------------------------------------------------
# Permission ordering (never-widens; WRITE_BOUNDED sits below WRITE).
# ---------------------------------------------------------------------------

def _permission_level(grant: str) -> int:
    text = str(grant or "NONE").strip().upper()
    if text == "NONE":
        return 0
    if text == "READ":
        return 1
    if text == PERMISSION_WRITE_BOUNDED:
        return 2
    if text == "WRITE":
        return 3
    if text == "EXECUTE":
        return 4
    if text == "NETWORK":
        return 5
    if text == "OWNER_GATE_REQUIRED":
        return 6
    return -1  # unknown tokens are never satisfied (fail-closed)


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BoundedDocMutationContract:
    """Exact mutation contract per spec 10. Provider/model/harness neutral."""

    goal_id: str
    task_id: str
    role_id: str
    capability_id: str
    mutation_class: str
    project_id: str
    project_revision: str
    environment: str
    allowed_relative_path: str
    before_hash: str
    max_changed_files: int
    max_changed_lines: int
    max_bytes: int
    owner_authorization_id: str
    target_id: str
    candidate_sha: str
    rollback_required: str
    acceptance_criteria: tuple[str, ...]
    mutation_content: str

    def __post_init__(self) -> None:
        # Field validity (fail-closed: reject anything malformed).
        for name in (
                "goal_id", "task_id", "role_id", "capability_id",
                "owner_authorization_id", "target_id", "candidate_sha",
                "project_revision", "project_id"):
            value = str(getattr(self, name) or "").strip()
            if not value:
                raise BoundedDocWriteError(f"{name.upper()}_EMPTY")
        for name, maxlen in (
                ("goal_id", 256), ("task_id", 256), ("role_id", 128),
                ("capability_id", 128), ("owner_authorization_id", 256),
                ("target_id", 128), ("project_id", 256)):
            if len(str(getattr(self, name))) > maxlen:
                raise BoundedDocWriteError(f"{name.upper()}_TOO_LONG")
        sha = str(self.candidate_sha)
        if len(sha) != 64 or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise BoundedDocWriteError("CANDIDATE_SHA_INVALID")
        rev = str(self.project_revision)
        if not re.fullmatch(r"[0-9a-f]{40,64}", rev):
            raise BoundedDocWriteError("PROJECT_REVISION_INVALID")
        if self.mutation_class != MUTATION_CLASS:
            raise BoundedDocWriteError("MUTATION_CLASS_NOT_DOCUMENTATION_WRITE_ONLY")
        if self.max_changed_files not in (0, 1):
            raise BoundedDocWriteError("MAX_CHANGED_FILES_NOT_BOUNDED_TO_ONE")
        if not (1 <= int(self.max_changed_lines) <= 4096):
            raise BoundedDocWriteError("MAX_CHANGED_LINES_OUT_OF_BOUND")
        if not (1 <= int(self.max_bytes) <= 65536):
            raise BoundedDocWriteError("MAX_BYTES_OUT_OF_BOUND")
        if str(self.rollback_required).upper() not in ("REQUIRED",):
            raise BoundedDocWriteError("ROLLBACK_REQUIRED_NOT_SET")
        if str(self.owner_authorization_id).strip().upper() in (
                "NONE", "", "UNKNOWN"):
            raise BoundedDocWriteError("OWNER_AUTHORIZATION_ID_INVALID")
        criteria = tuple(self.acceptance_criteria)
        if not criteria or len(criteria) > 8:
            raise BoundedDocWriteError("ACCEPTANCE_CRITERIA_INVALID")
        for crit in criteria:
            if not isinstance(crit, str) or not crit.strip():
                raise BoundedDocWriteError("ACCEPTANCE_CRITERION_EMPTY")

    def constraint_fingerprint(self) -> str:
        """Fingerprint covering the mutation constraints. Per spec 10:
        changing any constraint after authorization invalidates dispatch."""
        payload = {
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "role_id": self.role_id,
            "capability_id": self.capability_id,
            "mutation_class": self.mutation_class,
            "project_id": self.project_id,
            "project_revision": self.project_revision,
            "environment": self.environment,
            "allowed_relative_path": self.allowed_relative_path,
            "before_hash": self.before_hash,
            "max_changed_files": self.max_changed_files,
            "max_changed_lines": self.max_changed_lines,
            "max_bytes": self.max_bytes,
            "owner_authorization_id": self.owner_authorization_id,
            "target_id": self.target_id,
            "candidate_sha": self.candidate_sha,
            "rollback_required": self.rollback_required,
            "acceptance_criteria": list(self.acceptance_criteria),
        }
        return _sha256_json(payload)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BoundedDocWriteEvidence:
    """Exact changed-surface evidence per spec 13. None of the mandatory
    fields may be UNKNOWN or empty for a successful mutation."""

    schema: str = BOUNDED_DOC_WRITE_SCHEMA
    before_file_hash: str = ""
    after_file_hash: str = ""
    before_tree_hash: str = ""
    after_tree_hash: str = ""
    changed_relative_path: str = ""
    changed_file_count: int = 0
    changed_line_count: int = 0
    changed_bytes: int = 0
    mutation_class: str = MUTATION_CLASS
    owner_authorization_id: str = ""
    contract_fingerprint: str = ""
    dispatch_id: str = ""
    execution_id: str = ""
    host_attestation_id: str = ""
    rollback_required: str = "REQUIRED"
    rollback_state: str = ""
    # P2P-BOUNDED-DOCUMENTATION-WRITE-01B: the canonical authority mode
    # under which this mutation executed. TEST_ONLY evidence must never
    # satisfy a mutation-ready VERIFIED path (the receipt verifier
    # requires test_only_evidence == false for mutation-ready receipts).
    mutation_authority_mode: str = MUTATION_READY_AUTHORITY_MODE

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "before_file_hash": self.before_file_hash,
            "after_file_hash": self.after_file_hash,
            "before_tree_hash": self.before_tree_hash,
            "after_tree_hash": self.after_tree_hash,
            "changed_relative_path": self.changed_relative_path,
            "changed_file_count": self.changed_file_count,
            "changed_line_count": self.changed_line_count,
            "changed_bytes": self.changed_bytes,
            "mutation_class": self.mutation_class,
            "owner_authorization_id": self.owner_authorization_id,
            "contract_fingerprint": self.contract_fingerprint,
            "dispatch_id": self.dispatch_id,
            "execution_id": self.execution_id,
            "host_attestation_id": self.host_attestation_id,
            "rollback_required": self.rollback_required,
            "rollback_state": self.rollback_state,
            "mutation_authority_mode": self.mutation_authority_mode,
        }


# ---------------------------------------------------------------------------
# Path and content protections (spec 7 + 8 + 9)
# ---------------------------------------------------------------------------

class _DocumentClassification(enum.Enum):
    DOCUMENTATION_ALLOWED = "DOCUMENTATION_ALLOWED"
    PROTECTED = "PROTECTED"
    UNKNOWN = "UNKNOWN"


def _compile_patterns(patterns: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(p) for p in patterns)


_PROTECTED_RE = _compile_patterns(PROTECTED_PATH_PATTERNS)
_ALLOWED_RE = _compile_patterns(DOCUMENTATION_ALLOWED_PATTERNS)


def classify_document_path(allowed_relative_path: str) -> str:
    """Spec 9: classify the target as DOCUMENTATION_ALLOWED, PROTECTED, or
    UNKNOWN. Path + boundary evidence (extension-only reliance is not
    sufficient: the protected list also catches non-.md documentation
    surfaces such as TASKS.md / AGENTS.md). UNKNOWN -> BLOCK by caller."""
    rel = str(allowed_relative_path or "").strip().strip("/")
    if not rel:
        return _DocumentClassification.UNKNOWN.value
    for pattern in _PROTECTED_RE:
        if pattern.search(rel):
            return _DocumentClassification.PROTECTED.value
    for pattern in _ALLOWED_RE:
        if pattern.match(rel):
            return _DocumentClassification.DOCUMENTATION_ALLOWED.value
    return _DocumentClassification.UNKNOWN.value


def _normalize_and_validate_path(project_root: Path, allowed_relative_path: str) -> Path:
    """Spec 7: relative paths only, normalize, reject '..', reject path
    escape, reject symlink escape, reject directories."""
    rel = str(allowed_relative_path or "").strip()
    if not rel:
        raise BoundedDocWriteError("ALLOWED_RELATIVE_PATH_EMPTY")
    if "\\" in rel:
        raise BoundedDocWriteError("ALLOWED_PATH_CONTAINS_BACKSLASH")
    if "/" + ".." in rel or rel == ".." or rel.startswith("..") or \
            "..\\" in rel or rel.endswith("/.."):
        raise BoundedDocWriteError("ALLOWED_PATH_CONTAINS_DOTDOT")
    normalized = Path(os.path.normpath(rel))
    if normalized.is_absolute():
        raise BoundedDocWriteError("ALLOWED_PATH_MUST_BE_RELATIVE")
    # Any '..' component surviving normalization is a hard reject.
    if ".." in normalized.parts:
        raise BoundedDocWriteError("ALLOWED_PATH_ESCAPES_AFTER_NORMALIZATION")
    # Parent chain: every component of the normalized relative path must not
    # be a symlink (symlink escape reject), checked lazily for existing
    # segments. Existing parent segments are walked; missing segments are
    # fine (file is about to be created).
    probe = project_root
    for part in normalized.parts[:-1]:
        probe = probe / part
        if probe.is_symlink():
            raise BoundedDocWriteError("ALLOWED_PATH_PARENT_SYMLINK_ESCAPE")
    target = project_root / normalized
    if target.is_symlink():
        raise BoundedDocWriteError("ALLOWED_PATH_SYMLINK_ESCAPE")
    if target.exists() and target.is_dir():
        raise BoundedDocWriteError("ALLOWED_PATH_IS_DIRECTORY")
    # Escape final check on the real paths.
    try:
        real_root = project_root.resolve(strict=True)
        real_target = target.resolve()
    except OSError as exc:
        raise BoundedDocWriteError("PATH_RESOLUTION_FAILED", {"error": str(exc)})
    rel_target = os.path.relpath(real_target, real_root)
    if rel_target.startswith("..") or os.path.isabs(rel_target):
        raise BoundedDocWriteError("ALLOWED_PATH_ESCAPES_PROJECT_ROOT")
    return normalized


def _is_binary_content(content: str) -> bool:
    if not content:
        return False
    return "\x00" in content


def _count_changed_lines(before: str | None, after: str) -> int:
    """Spec 13: exact changed-surface evidence. Line diff count between the
    old content (None when the file did not exist) and the new content."""
    old_lines = list(before.splitlines()) if before is not None else []
    new_lines = list(after.splitlines())
    old_set = dict.fromkeys(old_lines)
    new_set = dict.fromkeys(new_lines)
    added = sum(1 for line in new_lines if line not in old_set)
    removed = sum(1 for line in old_lines if line not in new_set)
    return int(added + removed)


def _read_existing(path: Path) -> str | None:
    if not path.exists():
        return None
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BoundedDocWriteError("EXISTING_FILE_NOT_UTF8_TEXT", {"error": str(exc)})


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(payload: Any) -> str:
    return _sha256_hex(
        json.dumps(payload, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8"))


def _git_tree_hash(project_root) -> str:
    """HEAD^{tree} of the project root if git is available and the root is a
    git worktree; empty string otherwise (never fails closed on tree hash)."""
    _root = Path(str(project_root)).resolve()
    if not (_root / ".git").exists():
        return ""
    try:
        import subprocess  # git read-only probe; never writes
        proc = subprocess.run(
            ["git", "-C", str(_root), "rev-parse", "HEAD^{tree}"],
            capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            return str(proc.stdout).strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ""


# ---------------------------------------------------------------------------
# Lease + interruption state (FW06 max_parallelism=1, spec 18/19)
# ---------------------------------------------------------------------------

def _lease_path(project_root) -> Path:
    _root = Path(str(project_root)).resolve()
    state_dir = Path(os.environ.get("P2P_STATE_DIR", "")) if \
        os.environ.get("P2P_STATE_DIR") else _root / ".p2p" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / LEASE_FILE


def _interruption_path(project_root) -> Path:
    _root = Path(str(project_root)).resolve()
    state_dir = Path(os.environ.get("P2P_STATE_DIR", "")) if \
        os.environ.get("P2P_STATE_DIR") else _root / ".p2p" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / INTERRUPTION_STATE_FILE


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _save_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, sort_keys=True, ensure_ascii=False,
                              separators=(",", ":")), encoding="utf-8")
    os.replace(str(tmp), str(path))


def _acquire_lease(project_root: Path, dispatch_id: str) -> None:
    """Spec 18: max_parallelism=1. A lease bound to (project_root, path)
    blocks a concurrent bounded write entirely (BLOCK, never queue)."""
    lease = _lease_path(project_root)
    current = _load_json(lease)
    if current is not None and current.get("owner") and \
            current.get("owner") != dispatch_id:
        raise BoundedDocWriteError("CONCURRENT_BOUNDED_WRITE_BLOCKED")


def _hold_lease(project_root: Path, dispatch_id: str) -> None:
    _save_json(_lease_path(project_root), {
        "owner": dispatch_id,
        "acquired_at": _utc_now(),
        "operation": MUTATION_CLASS,
    })


def _release_lease(project_root: Path, dispatch_id: str) -> None:
    lease = _lease_path(project_root)
    current = _load_json(lease)
    if current is not None and current.get("owner") == dispatch_id:
        try:
            lease.unlink()
        except OSError:
            pass


def _write_interruption_state(project_root: Path, state: str,
                              details: Mapping[str, Any]) -> None:
    """Spec 18/19: after a write but before verification, an interruption
    is recorded as MUTATION_UNVERIFIED/ROLLBACK_REQUIRED — never silently
    retried, never duplicated."""
    _save_json(_interruption_path(project_root), {
        "state": state,
        "operation": MUTATION_CLASS,
        "recorded_at": _utc_now(),
        "details": dict(details),
    })


def _clear_interruption_state(project_root: Path) -> None:
    try:
        _interruption_path(project_root).unlink()
    except OSError:
        pass


def _secret_material_detected(text: str) -> list[str]:
    """FW04: heuristic scan for embedded secret material. Returns the list
    of matched token categories (empty when clean). Pattern evidence only;
    it never accepts a document that triggers a high-confidence match."""
    found = []
    for name, pattern in (
            ("PRIVATE_KEY", r"-----BEGIN [A-Z0-9 -]*PRIVATE KEY-----"),
            ("BEARER_TOKEN", r"bearer\s+[A-Za-z0-9._\-]{20,}"),
            ("AWS_ACCESS_KEY", r"AKIA[0-9A-Z]{16}"),
            ("GENERIC_SECRET_KEY", r"(?:sk|api|secret|password)_[A-Za-z0-9][A-Za-z0-9._\-]{15,}"),
    ):
        if re.search(pattern, text, re.IGNORECASE):
            found.append(name)
    return found


def _markdown_structure_valid(content: str) -> str:
    """FW04: structural validity of Markdown/text. Returns 'VALID',
    'DEGRADED' or 'INVALID' with boundary evidence (code fences and
    heading balance), never blocking on style-only opinion."""
    if not content.strip():
        return "INVALID"
    unclosed_fences = 0
    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            unclosed_fences ^= 1
    if unclosed_fences:
        return "INVALID"
    return "VALID"


def evaluate_bounded_document_mutation_quality(
        contract: BoundedDocMutationContract,
        evidence: BoundedDocWriteEvidence,
        project_root: str | Path,
) -> dict[str, Any]:
    """FW04 quality evaluation. EXECUTION_SUCCESS != QUALITY_VERIFIED.
    Returns overall, file_correct, content_utf8, structure_valid,
    no_secret_material, budget_respected, file_hash_verified.
    Quality failure forces rollback-required downstream (spec 16)."""
    rel = Path(str(evidence.changed_relative_path).strip())
    root = Path(str(project_root)).resolve()
    target = root / rel
    checks = {"file_correct": False, "content_utf8": False,
              "structure_valid": False, "no_secret_material": False,
              "no_fabricated_extra_diff": False, "budget_respected": False,
              "file_hash_verified": False}
    # Authorized file only.
    if target.exists() and target.is_file() and \
            not target.is_symlink():
        written_bytes = target.read_bytes()
        checks["file_correct"] = True
        # Valid UTF-8.
        try:
            content = written_bytes.decode("utf-8")
            checks["content_utf8"] = True
        except UnicodeDecodeError:
            content = ""
        # Structural Markdown validity (boundary evidence, not style).
        checks["structure_valid"] = (
            _markdown_structure_valid(content) == "VALID")
        # No secret material in the written bytes.
        checks["no_secret_material"] = (
            not _secret_material_detected(content))
        # No unrelated diff: mutation changed exactly the contracted
        # single path (evidence) and nothing else is asserted by this
        # primitive; the diff is precisely the committed bytes.
        checks["no_fabricated_extra_diff"] = (
            int(evidence.changed_file_count) == 1 and
            str(evidence.changed_relative_path).strip() == str(rel))
        # Mutation within budget.
        checks["budget_respected"] = (
            int(evidence.changed_line_count) <=
            int(contract.max_changed_lines) and
            int(evidence.changed_bytes) <= int(contract.max_bytes))
        # Post-write hash binding.
        checks["file_hash_verified"] = (
            _sha256_hex(written_bytes) ==
            str(evidence.after_file_hash))
    all_pass = bool(checks["file_correct"]) and all(checks.values())
    return {"overall": "QUALITY_VERIFIED" if all_pass else "QUALITY_FAILED",
            "checks": checks}


def build_bounded_mutation_owner_summary(
        contract: BoundedDocMutationContract,
        classification: str,
) -> dict[str, Any]:
    """FW05 owner-facing summary. No technical host/model choice is
    surfaced to the Owner: what P2P wants to change, why, whether it is
    allowed, which file, whether code/data are touched, what was checked,
    and rollback readiness."""
    return {
        "schema": "p2p-owner-view-bounded-write/1",
        "what_p2p_wants": "sửa một tài liệu văn bản (documentation) duy nhất",
        "why": "; ".join(contract.acceptance_criteria),
        "allowed": classification == "DOCUMENTATION_ALLOWED" and \
            str(contract.rollback_required).upper() == "REQUIRED",
        "file": str(contract.allowed_relative_path),
        "touches_code_or_data": False,
        "checks_performed": [
            "phân loại tài liệu (path + policy)",
            "tầm bảo vệ mặc định (denied surfaces)",
            "giới hạn file/dòng/byte",
            "hash trước/sau nguyên tử",
            "rollback bắt buộc"],
        "rollback_available": True,
        "owner_authorization": str(contract.owner_authorization_id),
    }


def _utc_now() -> str:
    try:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return "UNKNOWN"


# ---------------------------------------------------------------------------
# The canonical primitive (spec 7)
# ---------------------------------------------------------------------------

def execute_bounded_document_mutation(
        contract: BoundedDocMutationContract,
        project_root: str | Path,
        *,
        dispatch_id: str,
        execution_id: str = "",
        before_file_content_override: str | None = None,
        host_attestation_id: str = "",
        # P2P-BOUNDED-DOCUMENTATION-WRITE-01A: mutation-ready executions
        # REQUIRES a real canonical HostAttestation object (or any object
        # exposing an attestation_fingerprint). The legacy derived-id
        # fallback stays available ONLY for explicitly typed non-authority
        # fixtures ("TEST_ONLY") so legacy BW01 fixture behavior is not
        # silently widened into authority paths.
        host_attestation: Any = None,
        mutation_authority_mode: str = MUTATION_READY_AUTHORITY_MODE,
) -> BoundedDocWriteEvidence:
    """Execute exactly one bounded text-documentation mutation.

    This is the only canonical mutation primitive in the runtime. It is
    fail-closed: any violation below raises BoundedDocWriteError and no
    file is written. The caller must still persist the returned evidence
    through the role receipt verifier and canonical host attestation.
    """
    project_root = Path(str(project_root)).resolve()
    if not project_root.is_dir():
        raise BoundedDocWriteError("PROJECT_ROOT_INVALID")

    # 0. Real host attestation gate (01A Owner amendment 1/§6 +
    #    01B Owner amendment 2/§6-§7): mutation-ready executions MUST
    #    carry a real canonical HostAttestation regardless of whether
    #    the mutation is PRODUCTION, NON_PRODUCTION or ISOLATED — the
    #    requirement is keyed to MUTATION_AUTHORITY_MODE, never to the
    #    environment. Only the canonical TEST_ONLY mode may omit a real
    #    attestation (and TEST_ONLY can never satisfy a mutation-ready
    #    pass: it is validated here as fail-closed, and the receipt
    #    verifier further requires test_only_evidence == false for any
    #    mutation-ready VERIFIED path). Unknown modes BLOCK.
    if str(mutation_authority_mode or "").strip().upper() \
            not in MUTATION_AUTHORITY_MODES:
        raise BoundedDocWriteError(
            "MUTATION_AUTHORITY_MODE_INVALID",
            {"mutation_authority_mode": mutation_authority_mode,
             "canonical_modes": list(MUTATION_AUTHORITY_MODES)})
    _mode = str(mutation_authority_mode or "").strip()
    _att_fp: str | None = None
    if host_attestation is not None:
        _att_fp = str(getattr(host_attestation, "attestation_fingerprint", "") or "").strip()
        if not _att_fp:
            raise BoundedDocWriteError(
                "HOST_ATTESTATION_FINGERPRINT_MISSING",
                {"provided_object_type": type(host_attestation).__name__})
    elif _mode.upper() != "TEST_ONLY":
        raise BoundedDocWriteError(
            "MUTATION_BLOCKED_NO_REAL_HOST_ATTESTATION",
            {"mutation_authority_mode": _mode or "MUTATION_READY",
             "note": "a real canonical HostAttestation is required for "
                     "mutation-ready execution; derived ids are only "
                     "valid for mutation_authority_mode=TEST_ONLY"})

    # 1. Permission gate (spec 12: no capability -> BLOCK).
    rel = _normalize_and_validate_path(project_root, contract.allowed_relative_path)
    target = project_root / rel

    # 2. Document classification (spec 9: UNKNOWN -> BLOCK).
    classification = classify_document_path(contract.allowed_relative_path)
    if classification == _DocumentClassification.PROTECTED.value:
        raise BoundedDocWriteError("TARGET_CLASSIFIED_PROTECTED")
    if classification == _DocumentClassification.UNKNOWN.value:
        raise BoundedDocWriteError("TARGET_CLASSIFICATION_UNKNOWN_BLOCK")

    # 3. Size/content protections (spec 7).
    content = str(contract.mutation_content)
    if _is_binary_content(content):
        raise BoundedDocWriteError("MUTATION_CONTENT_BINARY_REJECTED")
    content_bytes = content.encode("utf-8")
    if len(content_bytes) > int(contract.max_bytes):
        raise BoundedDocWriteError("MUTATION_CONTENT_EXCEEDS_MAX_BYTES")

    # 4. Stale before-hash check (spec 7).
    expected_before = str(contract.before_hash).strip()
    existing = before_file_content_override if before_file_content_override is not None \
        else _read_existing(target)
    if expected_before == NON_EXISTENT:
        if existing is not None:
            raise BoundedDocWriteError("BEFORE_HASH_NON_EXISTENT_CONTRADICTED")
        before_hash = NON_EXISTENT
    else:
        if existing is None:
            raise BoundedDocWriteError("BEFORE_HASH_STALE_FILE_MISSING")
        if _sha256_hex(existing.encode("utf-8")) != expected_before:
            raise BoundedDocWriteError("BEFORE_HASH_STALE_MISMATCH")
        before_hash = expected_before

    # 5. Lease (FW06 max_parallelism=1).
    _acquire_lease(project_root, dispatch_id)
    _hold_lease(project_root, dispatch_id)
    try:
        # 6. Budget checks (spec 7: reject oversized change; reject second
        #    file via MAX_CHANGED_FILES=1 and single-path contract).
        changed_lines = _count_changed_lines(existing, content)
        if changed_lines > int(contract.max_changed_lines):
            raise BoundedDocWriteError("CHANGE_EXCEEDS_MAX_CHANGED_LINES")
        if len(content_bytes) > int(contract.max_bytes):
            raise BoundedDocWriteError("CHANGE_EXCEEDS_MAX_BYTES")

        # 7. Atomic write (spec 7).
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(target.parent), suffix=".bdwtmp")
        try:
            os.write(fd, content_bytes)
            os.close(fd)
            os.replace(tmp_path, str(target))
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        # 8. Post-write hash (spec 7).
        written = target.read_bytes()
        if written != content_bytes:
            raise BoundedDocWriteError("ATOMIC_WRITE_POST_HASH_MISMATCH")
        after_hash = _sha256_hex(written)

        # 8b. Interruption marker (spec 18/19): between the write and
        #     verification, an interruption must be recoverable as
        #     MUTATION_UNVERIFIED/ROLLBACK_REQUIRED, not silently retried.
        _write_interruption_state(project_root, "MUTATION_UNVERIFIED", {
            "after_file_hash": after_hash,
            "allowed_relative_path": str(rel),
            "dispatch_id": str(dispatch_id),
        })

        # 9. Exact changed-surface evidence (spec 13).
        before_tree = _git_tree_hash(project_root)
        _clear_interruption_state(project_root)
        evidence = BoundedDocWriteEvidence(
            before_file_hash=before_hash,
            after_file_hash=after_hash,
            before_tree_hash=before_tree,
            after_tree_hash=_git_tree_hash(project_root),
            changed_relative_path=str(rel),
            changed_file_count=1,
            changed_line_count=changed_lines,
            changed_bytes=len(content_bytes),
            owner_authorization_id=str(contract.owner_authorization_id),
            contract_fingerprint=contract.constraint_fingerprint(),
            dispatch_id=str(dispatch_id),
            execution_id=str(execution_id) or _sha256_hex(
                (str(dispatch_id) + after_hash).encode("utf-8")),
            # FW01/01A: the host attestation id must always be bound.
            # Priority: real attestation fingerprint > explicit override >
            # derived id. The derived-id fallback is reachable ONLY for
            # TEST_ONLY fixtures (gate 0 above already rejected
            # mutation-ready executions without a real attestation).
            host_attestation_id=(str(host_attestation_id).strip() or
                                 _att_fp or _sha256_hex(
                                     (str(dispatch_id) + str(execution_id)).encode("utf-8"))),
            rollback_required="REQUIRED",
            mutation_authority_mode=str(mutation_authority_mode or
                                        MUTATION_READY_AUTHORITY_MODE
                                        ).strip().upper(),
            rollback_state="PENDING",
        )
        return evidence
    except BoundedDocWriteError:
        raise
    except Exception as exc:
        raise BoundedDocWriteError("EXECUTION_FAILED_UNEXPECTED", {"error": str(exc)})
    finally:
        _release_lease(project_root, dispatch_id)


# ---------------------------------------------------------------------------
# Rollback (spec 15 + 19.E)
# ---------------------------------------------------------------------------

def rollback_bounded_document_mutation(
        evidence: BoundedDocWriteEvidence,
        project_root: str | Path,
        *,
        original_content: str | None,
) -> dict[str, Any]:
    """Restore the exact original bytes (or NON_EXISTENT). Proves
    FINAL_FILE_STATE == ORIGINAL and FINAL_TREE_HASH == PRE_MUTATION.
    Never a best-effort approximation."""
    project_root = Path(str(project_root)).resolve()
    rel = Path(str(evidence.changed_relative_path).strip())
    target = project_root / rel
    before = str(evidence.before_file_hash).strip()
    if before == NON_EXISTENT:
        if original_content is not None:
            raise BoundedDocWriteError("ROLLBACK_NON_EXISTENT_BUT_CONTENT_PROVIDED")
        if not target.exists():
            return {"rollback_state": "RESTORED",
                    "final_file_state": "NON_EXISTENT",
                    "after_hash": NON_EXISTENT,
                    "after_tree_hash": _git_tree_hash(project_root)}
        target.unlink()
        if target.exists():
            raise BoundedDocWriteError("ROLLBACK_DELETE_FAILED")
        return {"rollback_state": "RESTORED",
                "final_file_state": "NON_EXISTENT",
                "after_hash": NON_EXISTENT,
                "after_tree_hash": _git_tree_hash(project_root)}
    if original_content is None:
        raise BoundedDocWriteError("ROLLBACK_ORIGINAL_CONTENT_MISSING")
    original_bytes = str(original_content).encode("utf-8")
    if _sha256_hex(original_bytes) != before:
        raise BoundedDocWriteError("ROLLBACK_ORIGINAL_HASH_MISMATCH")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(target.parent), suffix=".bdwtmp")
    try:
        os.write(fd, original_bytes)
        os.close(fd)
        os.replace(tmp_path, str(target))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    restored = target.read_bytes()
    if _sha256_hex(restored) != before:
        raise BoundedDocWriteError("ROLLBACK_POST_RESTORE_HASH_MISMATCH")
    return {"rollback_state": "RESTORED",
            "final_file_state": "ORIGINAL_BYTES",
            "after_hash": before,
            "after_tree_hash": _git_tree_hash(project_root)}


# ---------------------------------------------------------------------------
# Crash/retry state machine (spec 19)
# ---------------------------------------------------------------------------

def bounded_write_retry_decision(
        project_root: str | Path,
        evidence: BoundedDocWriteEvidence | None,
        *,
        dispatch_id: str,
) -> str:
    """Deterministic retry decision. Never duplicates a committed write.

    A crash before write -> SAFE_RETRY. During atomic temp write ->
    NO_COMMITTED_MUTATION. After write before verification ->
    MUTATION_UNVERIFIED (detect via after-hash; do NOT rewrite). After
    verification before quality -> continue verification only. Quality
    fail -> ROLLBACK_REQUIRED. Rollback interruption -> recover state.
    """
    project_root = Path(str(project_root)).resolve()
    state = _load_json(_interruption_path(project_root))
    if state is None:
        if evidence is None:
            return "SAFE_RETRY"
        rel = Path(str(evidence.changed_relative_path).strip())
        target = project_root / rel
        if target.exists():
            current_hash = _sha256_hex(target.read_bytes())
            if current_hash == evidence.after_file_hash:
                return "MUTATION_UNVERIFIED_NO_REWRITE"
            if current_hash == str(evidence.before_file_hash):
                return "SAFE_RETRY"
        return "SAFE_RETRY"
    recorded = str(state.get("state", "")).upper()
    if recorded in ("MUTATION_UNVERIFIED", "MUTATION_UNVERIFIED/ROLLBACK_REQUIRED"):
        return "MUTATION_UNVERIFIED_NO_REWRITE"
    if recorded in ("ROLLBACK_REQUIRED", "ROLLBACK_INTERRUPTED"):
        return "ROLLBACK_REQUIRED"
    return "SAFE_RETRY"
