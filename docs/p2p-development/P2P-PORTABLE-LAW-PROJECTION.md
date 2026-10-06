# P2P portable law projection

Status: `CANDIDATE_UNPROMOTED`

This document defines the transport mechanism for carrying the existing P2P operations notebook into a P2P-managed repository that may be cloned by a remote executor without cross-repository access to the private canonical P2P repository.

It is **not** a second operations notebook and it does not create a second law authority. The canonical law remains:

`7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`

## Problem

A remote executor such as an Arena fresh workspace may be able to clone the target project but may not be authorized to read the private P2P source repository. A machine-local installation at `.p2p/system/` also does not automatically travel with a Git clone.

Therefore a target project can have valid durable project state while the executor starts without a readable P2P law context.

## Minimal mechanism

Use:

```text
python scripts/p2p_portable_law_projection.py <TARGET_PROJECT_ROOT>
```

The projector writes one deterministic Git-trackable transport bundle:

```text
AGENTS.md
.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md
.p2p/portable/P2P-EXPERIENCE-CAPSULE.json
.p2p/portable/P2P-SKILL-PROJECTION.json
.agents/skills/<bounded projected operator skills and required shared support>
```

It deliberately does **not** write `.p2p/system`, runtime state, approvals, gates, credentials, Git commits, deployment configuration, a second router, or a second authority.

The portable notebook contains the full source notebook plus generated provenance metadata including the source content SHA-256 and package version. The `AGENTS.md` block tells remote executors where to read it when canonical cross-repository access is unavailable.

## Authority and precedence

The projected copy is transport, not authority.

```text
reachable active canonical notebook
    > up-to-date installed projection, when present
    > generated portable project projection
    > explicit SUPREME_LAW_CAPSULE
    > LAW_CONTEXT_BLOCKED
```

`TASK_BRANCH != LAW_AUTHORITY` and `TARGET_PROJECT != LAW_SOURCE` remain mandatory.

When canonical access is already available in the current actor/session, compare against canonical and canonical wins. A repo-scoped remote executor with a valid generated portable projection does not need to probe another private repository merely to prove canonical is unavailable. `TARGET_REPO_AUTH != CANONICAL_CROSS_REPO_REACHABILITY`. In that case it reads the portable projection directly and reports `P2P_LAW_SOURCE=LOCAL_PORTABLE`. An installed executor may still use its valid installed projection according to the normal precedence. Never claim a source was read when it was not.

## Future project provisioning rule

For every newly created or newly adopted **P2P-managed repository that will be executed from fresh remote clones**, project provisioning should create the portable projection before substantive executor work and commit the two generated artifacts as part of the project bootstrap change.

Do not copy the notebook manually. Regenerate it from the P2P package/source using the projector so provenance and the managed `AGENTS.md` entrypoint stay consistent.

When the canonical notebook changes, refresh the projection with the same command. The operation is idempotent and replaces only the managed P2P portable-law block inside `AGENTS.md` while preserving unrelated project instructions.

For legacy repositories created before the managed portable-law block existed,
the projector also migrates a recognized standalone `## P2P law preflight`
section when that section carries the canonical P2P notebook path, portable
projection path, and `P2P_LAW_SOURCE=` marker. This prevents a stale
"probe canonical first" instruction from running before the current managed
block. Similar project-specific sections that do not carry all of those P2P
markers are preserved.

### Refresh policy: JIT by default

A canonical law, experience, or skill change does **not** require an immediate
fleet-wide mutation. The default operational path is just-in-time refresh of
the target repository immediately before a repo-scoped handoff that needs its
portable projection:

```text
python scripts/p2p_sync_managed_projects.py \
  --project <TARGET_PROJECT_ROOT> \
  --write
```

Read-only fleet surveying remains available without mutation:

```text
python scripts/p2p_sync_managed_projects.py \
  --workspace <WORKSPACE_ROOT> \
  --check
```

A workspace-wide write is exceptional and must be explicitly opted into:

```text
python scripts/p2p_sync_managed_projects.py \
  --workspace <WORKSPACE_ROOT> \
  --write \
  --full-fleet
```

The projector is component-aware at write time: it still computes and verifies
the complete expected transport bundle, including skill payload hashes, but it
rewrites only generated artifacts whose content is stale. A law-only change
therefore does not rewrite unchanged skill payloads merely to prove that they
remain current.

Use full-fleet writes only for changes that genuinely require immediate
cross-project propagation, such as an incompatible bootstrap or security
boundary change, or when the Owner explicitly requests fleet convergence.

### GitHub-only / repo-scoped workflow

A local clone is not required when the Owner operates projects directly on
GitHub and the current Control Tower has an authenticated GitHub connector with
repository write access.

Before delegating work to Arena or another repo-scoped executor that may not
reach the private P2P source repository:

1. fresh-read the canonical notebook and establish its content SHA-256;
2. read the target repository's `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`
   header and managed `AGENTS.md` block;
3. if missing or stale, generate the exact projector-equivalent artifacts from
   the current canonical notebook and update them through the authorized
   repository path, preferably on a bounded branch/PR;
4. verify the target projection records the fresh canonical source identity;
5. only then hand off work that expects `P2P_LAW_SOURCE=LOCAL_PORTABLE`.

The repo-scoped executor should then read repository-root `AGENTS.md` and the
valid local portable projection directly. It must not issue a `gh`/API request
to the private canonical repository solely to manufacture a 404 before using
that already-prepared fallback. A canonical source that is already proven
reachable in the executor's own session still wins.

If repository write access is unavailable, do not use the stale projection.
Carry a fresh inline capsule for that handoff instead. Do not provision a new
PAT, GitHub Action, watcher, registry, daemon, or service solely for this
operation.

## Verification

Read-only verification:

```text
python scripts/p2p_portable_law_projection.py <TARGET_PROJECT_ROOT> --check
```

`--check` returns PASS only when both the portable notebook and the managed `AGENTS.md` block match what the current P2P package would generate. Drift or a missing artifact fails closed.

## Acceptance

The capability is sufficient when all of the following are true:

1. A clean target project receives the portable notebook and the managed `AGENTS.md` entrypoint.
2. The projector never creates `.p2p/system` or project runtime state.
3. Re-running projection is idempotent.
4. `--check` detects a modified or stale projection.
5. A remote executor that cannot read the canonical P2P repository can discover and read the local projected notebook from the target repository.

No service, registry, database, background sync process, or separate governance framework is required for this capability.
