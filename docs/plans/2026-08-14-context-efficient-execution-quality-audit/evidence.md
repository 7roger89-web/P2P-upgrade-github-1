# Context-Efficient Execution & Quality Audit — Foundation for Durable Orchestration Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/plan.md`
- Evidence: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/evidence.md`
- Benchmark: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/benchmark.md`
- Actual status: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/actual-status.md`

## Evidence Rules

- Evidence is source- or command-backed and preserves PASS, FAIL, BLOCKED, and
  UNKNOWN honestly.
- Contract bytes are deterministic serialization proxies, never token/cost
  claims.
- Existing unrelated eval results are not reused for this audit.
- No evidence is allowed to grant permissions or promote a fact into runtime.
- Worker quality is UNKNOWN when no worker/provider executed.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-BASE1`: `VERSION` and `.p2p/system/VERSION` both read
  `8.4.7-C-codex.15`.
- `E0-P0A-BASE2`: official ZIP SHA-256 matched the supplied
  `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- `E0-P0A-BASE3`: official artifact was read-only; no `.16` candidate was
  created and no release command was run.
- `E0-P0A-GRAPH1`: Anvien refresh completed with 266 files scanned, 27 parsed,
  10,439 graph nodes, 11,861 relationships, and 27 unresolved file-level
  references; `scripts/p2p_workflow.py` was marked high-risk by file-detail.
- `E0-P0A-GRAPH2`: file-detail and upstream impact were run for
  `scripts/p2p_workflow.py`; the high blast-radius warning was preserved and
  no edit was made.
- `E0-P0A-SPEC1`: full relevant capability, context-pointer, execution/
  evidence, trust, routing, optional specialist, provider, and Decision Trace
  specs were read. `docs/SPEC/SPEC-MAP.md` is absent in this checkout.
- `E0-P0A-WORKFLOW1`: `scripts/p2p_workflow.py goal` created/reused the bounded
  audit Goal state but its linter classified the combined request as
  `SEPARATE GOALS`; no autonomous implementation began.
- `E0-P0A-WORKFLOW2`: `scripts/p2p_workflow.py bootstrap` returned BLOCKED
  because it invoked the installed UI/UX `p2p_eval.py design` interface, which
  does not accept that subcommand. The portable helper does accept it.
- `E0-P0A-GIT1`: `git status --short` could not run because this workspace has
  no Git repository; commit/diff evidence is unavailable.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

### Current execution flow

`E1-P1A-FLOW1`: Goal contract is built by `build_goal_contract()` with a fixed
generic five-criterion shape, current-state assumptions, constraints,
out-of-scope, selected-agent metadata, and terminal rules.

`E1-P1A-FLOW2`: routing is split. `select_agents()` chooses a smallest named
role/tier but only records metadata; it does not start a child agent. The
capability routing module separately computes readiness and route classes but
is not called by `run_workflow()` as a unified preflight.

`E1-P1A-FLOW3`: `write_capsule()` emits `p2p-capsule/2` as a continuation index
with objective, state, blockers, reusable evidence, progress, and artifact
references. Large content remains in referenced authoritative artifacts.

`E1-P1A-FLOW4`: `ContextPointer` and `resolve_context()` support metadata-first
relevance/scope/freshness filtering and mark `content_grants_permissions` as
false, but do not load source sections or bind the result to a worker context.

`E1-P1A-FLOW5`: `run_workflow()` snapshots all non-excluded files by SHA-256,
computes changed files, bootstraps project state, invokes eval design,
validates criteria, and writes reports/status/capsule/ledger. This is exact
P2P state/fingerprint telemetry, not host model telemetry.

`E1-P1A-FLOW6`: evidence uses trusted-evidence scoped fingerprints and expiry
to reuse unchanged PASS controls. The current audit project has no valid
task-specific PASS evidence to reuse.

`E1-P1A-FLOW7`: evidence and no-progress modules provide explicit claim/evidence
statuses, independent done checks, and bounded escalation after repeated
unchanged failure; they do not implement a retry worker loop.

`E1-P1A-FLOW8`: Decision Trace is a projection over the Execution Ledger,
sanitizes secrets/private reasoning, preserves refs/authority/approval, and
passed DT1–DT24. It is not a second memory store and does not receive a
Knowledge Delta from a worker.

### Context-waste forensics

- `E1-P1B-WASTE1` — project facts are repeated between Goal Contract,
  project profile, status, and governance references. Classification:
  `MINOR_WASTE` for explicit metadata duplication; some repetition is
  `EXPECTED_CONTEXT` for independent integrity checks.
- `E1-P1B-WASTE2` — repeated large instructions in worker prompts:
  `UNKNOWN`; the current workflow does not expose worker prompt execution.
- `E1-P1B-WASTE3` — whole files instead of sections:
  `UNKNOWN`/structural risk. Pointer resolution is metadata-only and no
  section-read counter exists.
- `E1-P1B-WASTE4` — raw logs returned to coordinator:
  `UNKNOWN` for workers; current trace output is sanitized and compact, but
  historical host receipt records exist in the ledger and must not be treated
  as active task context.
- `E1-P1B-WASTE5` — repeated evidence: scoped fingerprints and reuse are
  present, so the observed path is `EXPECTED_CONTEXT`; duplicate retrieval
  count remains `UNKNOWN`.
- `E1-P1B-WASTE6` — duplicated worker findings: `UNKNOWN`; no worker return
  contract is wired into the current workflow.
- `E1-P1B-WASTE7` — unnecessary specialists: selected roles are metadata-only
  in this runtime. The capability router can list every non-NOT_APPLICABLE
  capability, so invocation waste is a `MATERIAL_WASTE` risk but actual calls
  are `UNKNOWN`.
- `E1-P1B-WASTE8` — retries when optional capability is unavailable:
  `EXPECTED_CONTEXT` in the tested AESTHETICA route (`NOT_APPLICABLE`, no
  simulation); end-to-end workflow retry behavior is `UNKNOWN`.
- `E1-P1B-WASTE9` — unchanged retrieval repeats: `UNKNOWN`; no retrieval
  cache/ledger counter is present.
- `E1-P1B-WASTE10` — re-explaining settled decisions: `UNKNOWN`; references
  are used, but no duplicate-decision metric exists.
- `E1-P1B-WASTE11` — copying context between independent tasks:
  `UNKNOWN`; no worker/task handoff implementation is present.
- `E1-P1B-WASTE12` — historical material treated as active context:
  `UNKNOWN` end-to-end. Workflow snapshots exclude state prefixes and capsules
  reference state rather than copying it; any host-side reuse is not visible.

### Telemetry authority

`E1-P1B-TELEM1`: `EXACT_P2P_TELEMETRY` is available for project file SHA-256
snapshots, scoped fingerprints, ledger event records, goal/capsule state, and
Decision Trace validation. Historical ledger inspection found 14
`host_subagent_identity_receipt` records, but none is a current audit worker
execution proof.

`E1-P1B-TELEM2`: `DETERMINISTIC_PROXY` is available for serialized explicit
context bytes, serialized Knowledge Delta bytes, context-pointer count, file
inventory, and artifact size. These do not translate to tokens.

`E1-P1B-TELEM3`: `EXACT_HOST_TELEMETRY` was not exposed for model input,
cached input, output, provider cost, host tool output, child calls, or model
wall time.

`E1-P1B-TELEM4`: provider/child/tool execution counts, duplicate retrievals,
worker return bytes, retry cost, and repair-loop cost are `UNAVAILABLE` /
`UNKNOWN`; no such authoritative fields exist in the current runtime path.

`E1-P1B-TELEM5`: `elapsed_ms` in the beginner certification harness is a
command-harness timing field only. It is not model/provider wall time and was
not used as an efficiency result.

### Contract findings

`E1-P1B-CONTRACT1`: current Capsule is useful and pointer-oriented but lacks
explicit fields for scope, protected areas, relevant facts/decisions,
interfaces, invariants, dependencies, regression boundary, escalation,
return format, and resume pointer.

`E1-P1B-CONTRACT2`: no first-class `KNOWLEDGE_DELTA` schema is present. The
candidate is safe only as a compact projection over existing authority files;
it must not become a second memory store or hide incomplete evidence.

`E1-P1B-CONTRACT3`: readiness and trust contracts correctly preserve
`UNKNOWN`, stale, unavailable, and no-authority outcomes; the main workflow
does not combine capabilities, fallback, permission envelope, and budgets
into one preflight object.

`E1-P1B-CONTRACT4`: protected action policy separates broad intent from
approval; retrieved/model output cannot grant tools or permission. A task-
scoped READ/WRITE/LOG/PERSIST/EGRESS vector is not currently explicit.

`E1-P1B-CONTRACT5`: DIRECT/GUIDED/DELEGATED_BOUNDED is a useful internal
classification, but only DIRECT-like workflow execution is present; selected
agent lists are not proof of delegation.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-BENCH1`: frozen fixture bundle contains C1–C12 and has SHA-256
  `978f29fe493be5ce6e2d2b0fbd820945880df6303fb561f74bbe36127eeac166`.
- `E2-P2A-BENCH2`: corrected lowercase fixture SHA-256 is
  `978f29fe493be5ce6e2d2b0fbd820945880df6303fb561f74bbe36127eeac166`.
- `E2-P2A-BENCH3`: 48 contract-proxy trials were recorded: 12 scenarios × 2
  trials × conditions A/B. Both conditions used the same synthetic fixture,
  isolated environment, and zero unexpected writes.
- `E2-P2A-BENCH4`: p2p-eval v2 `validate` and `gate` both PASS for
  `.p2p/evals/2026-08-14-context-efficiency-ab-proxy-suite.json`; suite hash
  is `d2f47a9447645fc8495498d031df8a20f6253319eb0ae73417327ee34e64d0d3`.
- `E2-P2A-BENCH5`: deterministic proxy totals were A 122,260 serialized
  context bytes versus B 109,110, delta −13,150 bytes (−10.76%); B returned
  12,042 serialized Knowledge Delta bytes. No token/cost claim follows.
- `E2-P2A-BENCH6`: per-scenario proxy deltas were C1 −1,560; C2 −901;
  C3 −78; C4 −558; C5 −318; C6 −885; C7 −457; C8 −501; C9 −547;
  C10 −424; C11 +5; C12 −351 bytes.
- `E2-P2B-QUALITY1`: Q1–Q12 are `UNKNOWN` for all 48 trials because no real
  worker/provider executed.
- `E2-P2B-QUALITY2`: independent blinded quality review and real acceptance
  comparison are `NOT_AVAILABLE`; non-inferiority is `INSUFFICIENT_EVIDENCE`.
- `E2-P2B-BLOCK1`: candidate B is an in-memory contract shape, not a runtime
  implementation; promoting it would violate audit-first scope.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-TEST1`: `python -m unittest discover -s tests -p 'test_*.py'` —
  76/76 PASS.
- `E3-P3A-TEST2`: `p2p_decision_trace_eval.py --root .` — DT1–DT24 PASS;
  canonical denominator 8, full quorum 8/8; protected hashes unchanged.
- `E3-P3A-TEST3`: `p2p_governance.py drift --root . --governance governance`
  — PASS, no active volatile findings.
- `E3-P3A-TEST4`: foundation capability doctor with `--source .p2p/system` —
  PASS; trust boundary denies tools/permissions, optional AESTHETICA is
  resolved but not executable/identity-verified, providers remain not
  installed and core usable.
- `E3-P3A-TEST5`: `p2p_eval.py validate` and `gate` on the audit suite —
  PASS. The existing `.p2p/evals/suite.json` also passes but belongs to a
  different project and is not used as audit proof.
- `E3-P3A-TEST6`: beginner certification — harness PASS,
  `CERTIFIED_WITH_LIMITATIONS`; it is not a token benchmark.
- `E3-P3A-TEST7`: `scripts/doctor.py --package .` — FAIL because the current
  development checkout lacks the expected root UI/UX and foundation runtime
  payload paths. This failure is reported, not repaired.
- `E3-P3A-SECURITY1`: secret scan of `.p2p/system` — PASS.
- `E3-P3A-SECURITY2`: secret scan of `scripts` — PASS.
- `E3-P3A-SECURITY3`: whole-repository secret scan — FAIL on five
  high-confidence `GITHUB_TOKEN` example references in plugin-marketplace
  documentation and temporary preserved source snapshots. These are existing
  documentation examples, not newly created secrets; no source was edited to
  suppress the finding.
- `E3-P3A-SECURITY4`: no network, hooks, proxy, external provider, or package
  installation was enabled.
- `E3-P3B-CANON1`: native Decision Trace and capability doctor both report the
  exact canonical identities `p2p_iris`, `p2p_tecton`, `p2p_axiom`,
  `p2p_vector`, `p2p_datos`, `p2p_anon`, `p2p_architecton`, and `p2p_helios`.
- `E3-P3B-CANON2`: canonical denominator is exactly `8`; full quorum is
  exactly `8/8`; `p2p_aesthetica` is supporting/optional and not counted.
- `E3-P3B-BASELINE1`: no official release ZIP, VERSION, or protected runtime
  baseline file was edited.
- `E3-P3B-BASELINE2`: no `.16` version, candidate artifact, release gate, or
  deployment was produced.
- `E3-P3B-BASELINE3`: no user project, App Game Truyện, or Logistics path was
  touched by the audit fixtures or proxy benchmark.

## E4 - Closure Evidence

Matching plan item(s): `P4-A`

- `E4-P4A-REPORT1`: no P2P runtime source, official artifact, AESTHETICA
  profile, or user project was modified. Audit fixtures, suite, evidence, and
  planner records are the only intentional new artifacts.
- `E4-P4A-REPORT2`: no `.16` release candidate was created because quality
  non-inferiority and host telemetry were not established.
- `E4-P4A-SUPERVISOR1`: independent supervisor report
  `reports/supervisor/rp_supervisor_260814_013646_by_gpt-5-codex_context-efficiency-audit.md`
  gives exactly one verdict: `REJECT`.
- `E4-P4A-SUPERVISOR2`: supervisor confirms final terminal state is `BLOCKED`,
  not PASS; the exact blocker is unavailable real worker/provider execution
  and authoritative host telemetry needed for CE14–CE16.
- `E4-P4A-REPORT3`: final Anvien `detect-changes --scope all --json` returned
  `Git diff failed: exit status 129`; the workspace has no Git repository, so
  no commit/diff claim is made. No implementation slice was committed.
