# P2P local state schema

Store state under `<project>/.p2p/state/`. Do not commit it unless the user explicitly wants
shared project state. Every persistent format has a schema/version so future P2P updates can
migrate it instead of guessing.

## atlas.json

```json
{
  "goal": "",
  "steps": [{"name": "", "status": "pending", "check": ""}],
  "current": "",
  "next": "",
  "blockers": [],
  "updated_at": "ISO-8601"
}
```

## metrics.json

```json
{
  "tasks": 0,
  "completed_steps": 0,
  "corrections": 0,
  "ratings": [],
  "notes": [],
  "updated_at": "ISO-8601"
}
```

## capsules/*.md — p2p-capsule/2

Every capsule records `Schema`, `Profile`, `Saved`, project goal/current/next/blockers, and one
profile-specific body:

- `task`: objective, progress, decisions, constraints, verified evidence, artifacts, blockers,
  next action;
- `brainstorm`: original seed, promising options, valuable wording/voice, rejected options and
  why, unresolved tensions, next experiment;
- `research`: question, source/claim IDs, confirmed facts, inferences, disputes, unknowns,
  retrieval gaps, next query;
- `incident`: impact, timeline, current state, evidence, hypotheses, actions/owners, rollback,
  next checkpoint.

Never include credentials, hidden chain-of-thought, or raw private records when a scoped summary
is sufficient. Preserve exact wording only when it is the brainstorm artifact itself.

## evals

Project eval state lives separately under `<project>/.p2p/evals/` and follows
`p2p-codex-project-eval/2`. Keep at least two isolated trials per variant, hash frozen fixtures
and evidence, and do not mix session ratings with paired eval results.

## project workflow state

The reusable normal-operation workflow stores these additional project-local
artifacts under `.p2p/`:

- `project-profile.json` — `p2p-project-profile/1`; project type, evidence
  markers, authoritative governance references, initialization decisions, and
  a project snapshot.
- `state/goal-contract.json` and `state/goals/*.json` — `p2p-goal-contract/1`;
  objective, unknowns, measurable criteria, constraints, protected actions,
  verification oracles, eligibility class, mandatory/supporting/optional/out-of-scope
  work items, work type, exploration policy, mutation records, work guard,
  out-of-scope boundary, and terminal rules.
- `state/project-status.json` — `p2p-project-status/1`; current goal,
  milestones, trusted baseline, latest eval/drift/approval state, blockers,
  eligibility/linter/work-type state, exploration and mutation state,
  ledger/report references, and one next action.
- `state/trusted-evidence.json` — `p2p-trusted-evidence/1`; PASS control,
  scoped protected-input fingerprint, expiry, evidence reference, and
  provenance. Reuse is valid only when the fingerprint is unchanged and the
  evidence is not expired.
- `state/execution-ledger.jsonl` — `p2p-execution-event/1`; append-only
  workflow events for goal, bootstrap/reuse, agent selection, affected checks,
  evidence reuse, verification, and terminal state.
- `state/reports/*.json` and matching `.md` — detailed audit evidence and the
  compact beginner-facing report. The report references the authoritative
  artifacts rather than copying their full contents.

These are orchestration records, not replacement FACT, Live Specs, Drift,
Approval, RAG, or project-eval systems. Valid project policy, eval suites, and
evidence are preserved and reused.

## approvals and gates

Pending requests live under `<project>/.p2p/approvals/requests/`; decisions live under
`records/`; technical/final gate reports live under `<project>/.p2p/gates/`. Do not commit them
unless the user explicitly wants shared audit state. An agent may create a request, but must not
perform the interactive approval step. Every protected request uses schema
`p2p-codex-approval-record/2` and has both a subject SHA-256 and a PASS technical-report
SHA-256. A subject/report change or expired request requires a new record; never edit history.
