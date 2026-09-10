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

The projector writes only two Git-trackable project artifacts:

```text
AGENTS.md
.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md
```

It deliberately does **not** write `.p2p/system`, runtime code, state, approvals, gates, credentials, Git commits, or deployment configuration.

The portable notebook contains the full source notebook plus generated provenance metadata including the source content SHA-256 and package version. The `AGENTS.md` block tells remote executors where to read it when canonical cross-repository access is unavailable.

## Authority and precedence

The projected copy is transport, not authority.

```text
reachable active canonical notebook
    > generated portable project projection
    > explicit SUPREME_LAW_CAPSULE
    > LAW_CONTEXT_BLOCKED
```

`TASK_BRANCH != LAW_AUTHORITY` and `TARGET_PROJECT != LAW_SOURCE` remain mandatory.

When canonical access is available, compare against canonical and canonical wins. When canonical access is unavailable, the executor may use the generated portable projection and must report that it read the projection, not falsely claim it read the canonical repository.

## Future project provisioning rule

For every newly created or newly adopted **P2P-managed repository that will be executed from fresh remote clones**, project provisioning should create the portable projection before substantive executor work and commit the two generated artifacts as part of the project bootstrap change.

Do not copy the notebook manually. Regenerate it from the P2P package/source using the projector so provenance and the managed `AGENTS.md` entrypoint stay consistent.

When the canonical notebook changes, refresh the projection with the same command. The operation is idempotent and replaces only the managed P2P portable-law block inside `AGENTS.md` while preserving unrelated project instructions.

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
