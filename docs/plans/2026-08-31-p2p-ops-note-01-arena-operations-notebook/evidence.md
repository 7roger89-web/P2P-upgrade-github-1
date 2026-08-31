# P2P-OPERATIONS-NOTEBOOK-ARENA-01 — Arena Operations Notebook Evidence

## Metadata

- Date: `2026-08-31`
- Workstream: `P2P-OPERATIONS-NOTEBOOK-ARENA-01`
- Role: `WRITER` (Arena Agent Mode, bounded one-goal / one-branch / one-PR unit)
- Fresh main: `c1481ef7450113d6f7980fb2360991626200c9e6`
  tree `6c8321bbe089e1c37d552fcce8d139cf51096378` (merge of PR #35,
  fetched before any edit)
- Mode: operations-memory / install-inheritance change only; no runtime
  mutation, no promotion, no merge.

## E1 — Fresh-state inspection (no duplicate framework)

- No existing `P2P_OPERATIONS_NOTEBOOK`, `OPERATIONS_NOTEBOOK`, or
  `RULE_ASSIMILATION*` artifact existed anywhere in the repository or in
  open PRs/issues.
- Existing Arena-adjacent authority surfaces (referenced, not duplicated):
  - `docs/ARENA_AGENT_MODE_PROTOCOL.md` — canonical Arena session contract
    (sections 1-10: execution unit, lifecycle, rotation, prompt routing,
    projection policy).
  - `docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md` — durable
    Control Tower return/rotation contract (CT01).
  - `AGENTS.md` "Prompt and effort efficiency" section (merged via PR #27,
    P2P-PROMPT-EFFICIENCY-POLICY-01) and "P2P CODEX" entrypoint block
    projected by `install.sh` / `install.ps1` into every installed project.
  - `governance/project-adoption-lifecycle.md` and
    `docs/p2p-development/P2P-PROJECT-BOOTSTRAP.md` — projection-only
    adoption and the installed-project entry contract.
- Decision: no existing artifact served as a beginner-safe operations
  notebook for all executors (Control Tower, Arena Writer/Supervisor, Codex,
  Manus, beginner), so exactly ONE new canonical file was created:
  `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` (adjacent to the Control
  Tower handoff authority surface). No parallel framework was created.

## E2 — Canonical artifact delivered

- `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` (NEW) contains:
  - single canonical authority declaration + authority shape (notebook ->
    Control Tower guidance -> Arena Writer/Supervisor -> installed-project
    entrypoint);
  - install inheritance law `P2P_INSTALL =>
    P2P_OPERATIONS_NOTEBOOK_ACTIVE_BY_DEFAULT`;
  - `P2P_BEGINNER_OPERATIONS_UX_V1` rules 01-14;
  - `RULE_ASSIMILATION_GATE_V1` (PENDING -> VERIFIED / MISSED semantics,
    conditions A/B/C) with machine-readable `RULE_ASSIMILATION_LEDGER`;
  - truthful `ASSIMILATION_BACKLOG` reconciliation for items A-G.

## E3 — Install inheritance proof

The existing installation surface already projects the package `AGENTS.md`
into every installed project as the `<!-- BEGIN P2P CODEX -->` entrypoint
block (`install.sh` / `install.ps1`; entry contract documented in
`P2P-PROJECT-BOOTSTRAP.md`). The notebook digest was added to that block
(`AGENTS.md` "P2P_OPERATIONS_NOTEBOOK" section), so no installer change was
needed. Proof (exact installer merge semantics simulated on a temp project):

```
PASS notebook digest section present
PASS inherit law declared
PASS notebook canonical path referenced
PASS RULE 01..14 digest present
PASS assimilation gate declared
PASS owner content preserved
PASS single P2P block
INSTALL_INHERITANCE_PROVEN=YES
```

Release projection: `scripts/package_release.py` `DOC_FILES` now includes
`docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`, so the full canonical
notebook travels with release packages (candidate manifest
`documentation_files` derives from `DOC_FILES` automatically).

## E4 — Arena / Control Tower linkage

- `docs/ARENA_AGENT_MODE_PROTOCOL.md`: new section 11 (P2P operations
  notebook discovery) + notebook added to the fresh-session bootstrap order
  (section 8).
- `docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md`: notebook row
  added to "Discovery and operator paths" + Arena boundary note.
- Installed-project entrypoint: `AGENTS.md` digest (E3).

## E5 — Assimilation backlog reconciliation (truthful)

| Item | Status | Evidence |
| --- | --- | --- |
| A Beginner-safe routing | VERIFIED | notebook RULE 01-03/09; ARENA_AGENT_MODE_PROTOCOL.md §6 |
| B Arena continuity | VERIFIED | notebook RULE 04-06; ARENA_AGENT_MODE_PROTOCOL.md §1-4 |
| C Beginner return contract | VERIFIED | notebook RULE 09-10; CONTROL-TOWER-SESSION-HANDOFF.md |
| D Prompt/ceremony efficiency | VERIFIED | AGENTS.md (PR #27); orchestration_policy.py; notebook RULE 12/14 |
| E Control Tower session handoff | VERIFIED (referenced, not recreated) | CONTROL-TOWER-SESSION-HANDOFF.md + control_tower_handoff.py + tests |
| F Quick prompt / Arena prompt-builder | PENDING (truthful: not canonical) | no artifact; nearest surface control_tower_handoff.build_execution_prompt |
| G Lightweight orchestration/context integration (C18/C19) | VERIFIED (canonical runtime referenced; no new wiring) | orchestration_policy.py, context*.py + their tests; roadmap C18/C19 DONE |

The machine-readable `RULE_ASSIMILATION_LEDGER` (notebook §4.3) is the
durable record; the previous "we will add this later" promises are now
tracked, and this task's ReturnPacket reports `RULE_ASSIMILATED=YES` for
items A-E and G (F stays PENDING under the gate).

## E6 — Focused verification

- `tests/test_p2p_operations_notebook.py` (NEW, 9 structural checks): PASS.
- Focused regression on touched surfaces: `test_p2p_beginner_routing`,
  `test_p2p_orientation_packaging`, `test_p2p_eff01_execution_efficiency`,
  `test_p2p_orientation` (24 tests): OK.
- Control Tower / projection surfaces untouched by edits:
  `test_p2p_control_tower_session_handoff`, `test_p2p_control_tower_durable`,
  `test_p2p_projection_bundle` (54 tests): OK.
- `scripts/package_release.py` compiles; `DOC_FILES` extension validated by
  `test_p2p_operations_notebook` and `test_p2p_orientation_packaging`.
- Scope guards honored: no img2threejs runtime, no PR37, no Game Truyện /
  Logistics / Gia Phả product code, no new orchestrator/scheduler/memory
  framework, no installer rewrite, no merge/promotion/release/deploy.

## FILES_CHANGED

- `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` (NEW — canonical)
- `AGENTS.md` (install-inherited digest section)
- `docs/ARENA_AGENT_MODE_PROTOCOL.md` (§8 bootstrap order + §11 discovery)
- `docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md` (linkage)
- `scripts/package_release.py` (DOC_FILES include)
- `tests/test_p2p_operations_notebook.py` (NEW — structural validation)
- `docs/plans/2026-08-31-p2p-ops-note-01-arena-operations-notebook/evidence.md` (this file)

---

## REANCHOR (2026-08-31, second delta on the same PR)

The initial implementation above started from `c1481ef7...` (fresh main at
that time). PR #37 merged afterward, so the PR38 branch was reanchored onto
current canonical main via a normal non-destructive merge (no force push, no
history rewrite, no new PR, no cherry-pick, operations commit preserved):

```text
REANCHORED_FINAL_BASE=cbf26b4d5380656743eddbbdc55c4924cd09ce36
REANCHORED_FINAL_BASE_TREE=d75d33a83488c99d168b5ade9b2f319ef3477ab2
REANCHORED_HEAD_BEFORE_RULE15=cecc2cb14cfbd563b0dc47f3551b22d69577e4bf
REANCHORED_HEAD_BEFORE_RULE15_TREE=9d599eaddcdb423e37ed9ab035056b8b571f3736
PR37_RUNTIME_DIFF=ZERO (img2threejs userdata files inherited unchanged)
UNEXPECTED_FILES=0 (diff vs fresh main = only the original 7 notebook paths)
```

## BACKLOG_H — Arena task completion dialog (assimilated on the same PR)

The Owner accepted one additional beginner-operating rule after the original
implementation: the Arena completion dialog ("Was this task successful?" —
Yes / No / Keep working). Under `RULE_ASSIMILATION_GATE_V1` this accepted
rule was assimilated into the open PR38 before closure:

```text
BACKLOG_H_ARENA_COMPLETION_DIALOG=VERIFIED
RULE 15 — ARENA_TASK_COMPLETION_DIALOG — docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md
Arena linkage — docs/ARENA_AGENT_MODE_PROTOCOL.md section 11 (completion-dialog handling)
Focused test — tests/test_p2p_operations_notebook.py (RULE 15 semantics)
```

The historical facts of the first edit (starting from `c1481ef7...`) are
preserved above and are not rewritten as though the first edit started from
the reanchored base.

## REAL INSTALLED PROJECT NOTEBOOK INHERITANCE (CT blocker fix)

Control Tower identified a focused install-inheritance blocker: the installed
`AGENTS.md` digest claimed rules 01-15 but enumerated only RULE 01-14, and the
full canonical notebook was shipped in the release package but not copied into
every installed project tree. This violated the Owner practical requirement
that an installed project can actually discover and follow the canonical
rules. Fixed on the same PR38 (no new PR).

```text
REAL_INSTALLED_PROJECT_NOTEBOOK_INHERITANCE=PASS
INSTALLED_NOTEBOOK_PATH=.p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md
INSTALLED_RULES_01_15_DISCOVERABLE=YES
```

Mechanism (existing package copy structure, no new installer):

- `install.sh` now creates `$system_destination/docs` and copies
  `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` to
  `.p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md`; fails closed (`exit 2`) if the
  canonical notebook is missing from a package that claims this feature.
- `install.ps1` does the equivalent:
  `docs\p2p-development\P2P-OPERATIONS-NOTEBOOK.md` ->
  `$SystemDestination\docs\P2P-OPERATIONS-NOTEBOOK.md`; fails closed (`throw`)
  if missing.
- `AGENTS.md` digest now points the installed project at the local installed
  notebook (`.p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md`) so it never depends
  on access to the original development repo, and adds a concise RULE 15
  digest entry so the digest enumerates RULE 01-15.
- Release projection unchanged: `scripts/package_release.py` `DOC_FILES`
  already ships the full notebook (single release artifact, no duplicate).

Focused simulation (temp project, exact installer merge semantics):

```text
PASS installed notebook at .p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md
PASS installed notebook contains RULE_ASSIMILATION_GATE_V1
PASS installed notebook contains RULE 15 — ARENA_TASK_COMPLETION_DIALOG
PASS installed AGENTS.md references .p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md
PASS installed AGENTS.md digest enumerates RULE 01-15 (15 bullets, incl. RULE 15)
PASS owner/project pre-existing AGENTS content preserved
PASS single P2P block; no second notebook/framework
REAL_INSTALLED_PROJECT_NOTEBOOK_INHERITANCE=PASS
```

Focused tests: `tests/test_p2p_operations_notebook.py` extended to 19 checks
(A-H: release contains full notebook; install.sh path; install.ps1 path;
installed AGENTS local reference; digest RULE 01-15 incl. RULE 15; installed
notebook contains gate + RULE 15; owner content preserved; no second
framework). 19/19 PASS. Related focused suites (beginner_routing,
orientation_packaging, eff01, orientation, control_tower_session_handoff,
control_tower_durable): OK.
