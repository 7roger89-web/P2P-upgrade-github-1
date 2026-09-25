"""Issue #264 slice 1 — PARALLEL_WORKSTREAM_EXECUTION_BY_DEFAULT.

Structural + projection tests proving that controlled parallel workstreams are a
canonical Supreme Law invariant and that the invariant reaches the projected actor paths
(canonical notebook, portable AGENTS block, thin installed entrypoint, root
AGENTS digest) through the EXISTING projector/sync — no new orchestration surface.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO_ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
INSTALL_SOURCE = REPO_ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
ROOT_AGENTS = REPO_ROOT / "AGENTS.md"
SCRIPT_SYNC = REPO_ROOT / "scripts" / "p2p_sync_managed_projects.py"
SCRIPT_PROJ = REPO_ROOT / "scripts" / "p2p_portable_law_projection.py"

for _p in (str(REPO_ROOT / "scripts"), str(REPO_ROOT / ".p2p" / "system")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import p2p_portable_law_projection as projector  # noqa: E402

MARKER = "PARALLEL_WORKSTREAM_EXECUTION_BY_DEFAULT"
ONE_ACTION = "ONE_ACTION_NOW_FOR_BEGINNER != ONE_WORKSTREAM_TOTAL"
EXCLUSIVE_STATE_CLASSES = (
    "high-conflict files/symbols",
    "schema/migration",
    "destructive",
    "secrets/infra",
    "release/deploy state",
    "exclusive contract",
)


def _notebook() -> str:
    return NOTEBOOK.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _supreme_law_section() -> str:
    text = _notebook()
    start = text.index("## 2A. P2P_SUPREME_OPERATING_LAW_V1")
    end = text.index("\n## 3. P2P_BEGINNER_OPERATIONS_UX_V1")
    return text[start:end]


def _invariant_body() -> str:
    section = _supreme_law_section()
    start = section.index(f"### {MARKER}")
    end = section.index("\n### ", start + 4)
    return section[start:end]


def _numbered_item(body: str, number: int) -> str:
    match = re.search(rf"^{number}\. (.*?)(?=^\d+\. |\Z)", body, re.S | re.M)
    assert match, f"item {number} missing"
    return _flat(match.group(1))


def _rule_body(rule_heading: str) -> str:
    text = _notebook()
    start = text.index(rule_heading)
    end = text.index("\n### ", start + 4)
    return _flat(text[start:end])


# 1. canonical Supreme Law carries the invariant --------------------------------


def test_invariant_lives_inside_supreme_law_section_once():
    section = _supreme_law_section()
    assert section.count(f"### {MARKER}") == 1
    # exactly one canonical definition in the whole notebook (no parallel copy)
    assert _notebook().count(f"### {MARKER}") == 1
    body = _invariant_body()
    for line in (
        f"{MARKER}=YES",
        "ONE_WORKSTREAM = ONE_BOUNDED_GOAL -> ONE_BRANCH -> ONE_PR",
        "SAME_REPOSITORY != SERIALIZATION_REASON",
        "SHARED_EXCLUSIVE_STATE => COORDINATE_OR_SERIALIZE",
        "PARALLEL_IMPLEMENTATION != PARALLEL_INTEGRATION",
        "CONTROL_TOWER_OWNS_CROSS_WORKSTREAM_TOPOLOGY=YES",
        ONE_ACTION,
    ):
        assert line in body, line
    assert "not a\nproject-specific convention" in body or "not a project-specific convention" in _flat(body)


# 2. ONE_ACTION_NOW_FOR_BEGINNER != ONE_WORKSTREAM_TOTAL ------------------------


def test_one_action_is_not_one_workstream_in_law_and_rule09():
    item9 = _numbered_item(_invariant_body(), 9)
    assert ONE_ACTION in item9
    assert "immediate action" in item9 and "not the number of lanes" in item9
    rule09 = _rule_body("### RULE 09 — ONE_ACTION_NOW_FOR_BEGINNER")
    assert ONE_ACTION in rule09
    assert "one immediate action" in rule09
    assert "multiple independent Writer or Supervisor lanes at once" in rule09


# 3. disjoint lanes may run concurrently ----------------------------------------


def test_disjoint_lanes_should_run_concurrently():
    body = _invariant_body()
    assert "SHOULD run concurrently" in _numbered_item(body, 1)
    assert "shared-state risk is bounded" in _numbered_item(body, 1)
    item3 = _numbered_item(body, 3)
    assert "disjoint or have bounded overlap" in item3
    assert "verified independently" in item3
    assert "Do not serialize unrelated work merely because it lives in the same repository" in _numbered_item(body, 4)


# 4. conflicting / exclusive state requires coordination ------------------------


def test_exclusive_shared_state_requires_coordination():
    item5 = _numbered_item(_invariant_body(), 5)
    assert item5.startswith("Coordinate or serialize")
    for cls in EXCLUSIVE_STATE_CLASSES:
        assert cls in item5, cls
    item6 = _numbered_item(_invariant_body(), 6)
    assert "integration boundaries" in item6 and "may be ordered" in item6
    assert "does not require serializing implementation" in item6


# 5/6. main advanced -> preserve PR + bounded refresh; no restart/duplicate ---


def test_main_advanced_preserves_pr_and_requires_bounded_refresh():
    body = _invariant_body()
    assert (
        "MAIN_ADVANCED_BY_OTHER_LANE => PRESERVE_BRANCH_AND_PR + FRESH_DETECT + "
        "REFRESH_TO_CURRENT_MAIN + VERIFY_INTEGRATION_DELTA"
    ) in body
    assert (
        "MAIN_ADVANCED_BY_OTHER_LANE != RESTART_WORKSTREAM | DUPLICATE_PR | FULL_UNRELATED_REREVIEW"
    ) in body
    item7 = _numbered_item(body, 7)
    for phrase in (
        "fresh-detect the state change",
        "preserve the existing branch/PR",
        "refresh/reconcile it against current main",
        "integration delta / affected intersection",
        "Do not restart the workstream",
        "create a duplicate PR",
        "repeat unrelated full review solely because main moved",
    ):
        assert phrase in item7, phrase
    item8 = _numbered_item(body, 8)
    assert "Current durable state wins over stale validation receipts" in item8
    assert "valid only for that head and its base/integration context" in item8


def test_one_goal_one_branch_one_pr_preserved():
    assert "1 bounded goal -> 1 branch -> 1 PR" in _notebook()
    item2 = _numbered_item(_invariant_body(), 2)
    assert "`one bounded goal -> one branch -> one PR`" in item2
    assert "one PR mixing several goals" in item2
    rule07 = _rule_body("### RULE 07 — WRITER_BOUNDARY")
    assert MARKER in rule07 and "own explicit workstream/branch/PR identity" in rule07
    rule13 = _rule_body("### RULE 13 — CONTROL_TOWER_STATE_RESPONSIBILITY")
    assert MARKER in rule13 and "cross-workstream topology" in rule13


# no second orchestration system -------------------------------------------------


def test_no_orchestration_infrastructure_and_gates_unchanged():
    body = _flat(_invariant_body())
    item10 = _numbered_item(_invariant_body(), 10)
    for forbidden in (
        "scheduler",
        "queue",
        "distributed lock service",
        "dependency-graph engine",
        "daemon/watcher",
        "registry/database",
        "second router/control plane",
    ):
        assert forbidden in item10, forbidden
    assert "Do not add" in item10
    assert "RULE 11 Owner Gates" in body and "are unchanged by this invariant" in body
    # the harness trigger no longer implies ordinary lanes need new agents
    assert "ordinary concurrent branch/PR lanes are not a harness component" in _flat(_notebook())
    workflows = REPO_ROOT / ".github" / "workflows"
    if workflows.is_dir():
        for wf in workflows.iterdir():
            if wf.is_file():
                text = wf.read_text(encoding="utf-8", errors="replace")
                assert "p2p_sync_managed_projects" not in text, wf
                assert MARKER not in text, wf


def test_assimilation_ledger_tracks_pending_item():
    text = _notebook()
    start = text.index("### 4.3 RULE_ASSIMILATION_LEDGER")
    block = text[start:]
    raw = block[block.index("```json") + len("```json"): block.index("```", block.index("```json") + 7)]
    ledger = json.loads(raw)
    entries = {e["id"]: e for e in ledger["entries"]}
    entry = entries["BACKLOG_L"]
    assert entry["item"] == MARKER
    # Writer must not self-verify; Control Tower flips it after exact head check.
    assert entry["status"] == "PENDING"
    assert any("tests/test_p2p_parallel_workstream_law.py" in ev for ev in entry["evidence"])


# actor consumption paths (projection surfaces) ---------------------------------


def test_portable_agents_block_carries_invariant():
    block = projector._agents_block()
    assert block.count("### Parallel workstreams by default") == 1
    assert MARKER in block
    assert ONE_ACTION in block
    assert "one bounded goal -> one branch -> one PR" in block
    assert "preserve the existing branch/PR" in block
    assert "Do not restart the workstream, open a duplicate PR" in block
    # stays a pointer + digest, not a copy of the full law body
    assert "Informative example" not in block


def test_thin_installed_entrypoint_carries_invariant():
    text = INSTALL_SOURCE.read_text(encoding="utf-8")
    assert text.count(MARKER) == 2  # rule-set list + one universal invariant line
    assert ONE_ACTION in text
    assert "no restart, duplicate PR, or unrelated full re-review" in text
    assert "OWNER_OUTCOME_AND_AUTHORITY_ARE_INVARIANTS" not in text  # still thin


def test_root_agents_digest_carries_invariant():
    text = ROOT_AGENTS.read_text(encoding="utf-8")
    assert MARKER in text
    assert ONE_ACTION in text


# real canonical package -> managed project projection through existing sync ---


def _run_sync(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT_SYNC), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_existing_workspace_sync_refreshes_law_and_experience_together(tmp_path: Path):
    """A managed project projected before this invariant becomes STALE, the
    existing `--workspace` sync refreshes law + AGENTS block + experience capsule
    together, unrelated AGENTS content survives, and a rerun is a no-op."""
    ws = tmp_path / "ws"
    project = ws / "managed-project"
    project.mkdir(parents=True)
    custom = "# Project rules\n\nKeep product-specific rule X.\n"

    # Simulate an older managed projection: current bytes minus the new section.
    projection, agents, capsule = projector.expected_project_state(REPO_ROOT, project)
    old_block_start = agents.index("### Parallel workstreams by default")
    old_block_end = agents.index("### Mandatory prompt serialization contract")
    old_agents = custom + "\n" + agents[:old_block_start] + agents[old_block_end:]
    (project / "AGENTS.md").write_text(old_agents, encoding="utf-8")
    portable_dir = project / ".p2p" / "portable"
    portable_dir.mkdir(parents=True)
    (portable_dir / "P2P-OPERATIONS-NOTEBOOK.md").write_text("stale law\n", encoding="utf-8")
    (portable_dir / "P2P-EXPERIENCE-CAPSULE.json").write_text("{}\n", encoding="utf-8")
    product_file = project / "app.py"
    product_file.write_text("print('product')\n", encoding="utf-8")
    ignored = ws / "not-managed"
    ignored.mkdir()

    check = _run_sync("--workspace", str(ws), "--package-root", str(REPO_ROOT), "--check")
    assert check.returncode == 1, check.stdout + check.stderr
    assert "1 projects" in check.stdout and "STALE=1" in check.stdout

    write = _run_sync("--workspace", str(ws), "--package-root", str(REPO_ROOT), "--write")
    assert write.returncode == 0, write.stdout + write.stderr
    assert "CHANGED=1" in write.stdout

    new_agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep product-specific rule X." in new_agents
    assert new_agents.count(projector.AGENTS_BEGIN) == 1
    assert MARKER in new_agents and ONE_ACTION in new_agents
    law = (portable_dir / "P2P-OPERATIONS-NOTEBOOK.md").read_text(encoding="utf-8")
    assert "P2P_PORTABLE_LAW_PROJECTION=YES" in law
    assert f"### {MARKER}" in law
    exp = json.loads((portable_dir / "P2P-EXPERIENCE-CAPSULE.json").read_text(encoding="utf-8"))
    assert exp["schema"] == projector.EXPERIENCE_CAPSULE_SCHEMA
    assert f"PORTABLE_EXPERIENCE_CONTENT_SHA256={projector._sha256_text(capsule)}" in law
    assert law == projection
    # product code untouched; nothing written into the non-managed sibling
    assert product_file.read_text(encoding="utf-8") == "print('product')\n"
    assert not any(ignored.iterdir())

    again = _run_sync("--workspace", str(ws), "--package-root", str(REPO_ROOT), "--write")
    assert again.returncode == 0
    assert "CHANGED=0" in again.stdout and "CURRENT=1" in again.stdout
