# Reverse-Skill bounded bridge — 2026-09-15

## Decision

`OE_VERDICT=DO_IT`.

Adopt Reverse-Skill only as a **subordinate security/reverse methodology selector**
behind the existing P2P capability router and security execution policy. Do not
vendor/fork the project, do not import its global instruction files as P2P
authority, and do not expose its bootstrap/MCP/authorization surfaces through
this integration.

This is the smallest useful slice because P2P already has:

- one canonical capability router in `p2p_capabilities/routing.py`;
- security/reverse execution classes and fail-closed authorization in
  `security_contract.py`;
- the APKiD local adapter as the established security-tool boundary pattern;
- runtime packaging that copies the existing `p2p_capabilities` package.

A second router, risk engine, installer, task ledger, or control plane would
duplicate authority without improving the bounded outcome.

## Fresh upstream evidence

Reviewed public upstream:

- repository: `zhaoxuya520/reverse-skill`
- branch observed: `main`
- exact commit: `7e2097fd90d25c2f976f6eba26d6c00aa88051df`
- commit date: 2026-09-03
- commit subject: `docs: record issue and PR security integration`

Relevant reviewed surfaces at that commit:

- `skills/config/routing.json` — upstream routing SSoT;
- `skills/scripts/master-route.sh` — POSIX client-neutral route entry;
- `skills/scripts/master-route.ps1` — Windows route entry;
- `RULES.md` / `AGENTS.md` — upstream operational instructions;
- `case-init` / `case-guard` — upstream authorization/scope mechanism;
- `bootstrap-reverse.*` / `bootstrap-manifest.json` — upstream tool bootstrap
  mechanism.

The upstream hot path intentionally continues from routing into case
initialization, skill execution and missing-tool bootstrap. P2P does **not**
inherit that authority. External content and upstream instructions remain data
under P2P governance.

## Implemented boundary

`.p2p/system/p2p_capabilities/reverse_skill_bridge.py` exposes only the pinned
`master-route` entrypoint.

Call order:

```text
P2P canonical capability router
  -> P2P security execution policy
  -> ReverseSkillBridge (ANALYSIS_LOCAL)
  -> pinned reverse-skill master-route
  -> non-authoritative PRIMARY methodology advice
```

The bridge:

1. requires a caller-provided local Reverse-Skill checkout;
2. verifies `git rev-parse HEAD` equals the exact reviewed commit;
3. rejects tracked worktree drift before executing upstream code;
4. verifies required router files and `routing.json` structure;
5. runs only `master-route.sh` or `master-route.ps1`;
6. places `route-scope.md` outside both the target project and upstream checkout;
7. validates returned skill references stay inside the pinned upstream tree;
8. redacts the task text from the returned command evidence;
9. labels the result non-authoritative and preserves P2P router authority.

On Windows the bridge invokes PowerShell with `-NoProfile -File` and does not
add `-ExecutionPolicy Bypass`; host execution policy remains in force.

## Explicitly unavailable through this bridge

The bridge has no API for:

- `bootstrap-reverse.*` or any automatic tool installation;
- MCP registration;
- upstream `case-init` authorization grants;
- `--force` authorization bypass;
- network target action;
- exploit/persistence/credential/EDR action;
- mutation of the caller project;
- mutation of the Reverse-Skill checkout;
- promotion of upstream output into P2P authority.

If a later task needs an active security action, the existing P2P execution
classes remain authoritative:

- `SAFE_READONLY`
- `ANALYSIS_LOCAL`
- `ACTIVE_TEST_AUTHORIZED`
- `OFFENSIVE_HIGH_RISK`
- `DESTRUCTIVE_OR_INTRUSIVE`

Active/offensive work still requires the existing authorization gates;
destructive/intrusive work remains denied by default.

## Runtime usage

The bridge is stdlib-only and lives inside the already-packaged
`p2p_capabilities` directory. It can also be called directly:

```text
python -m p2p_capabilities.reverse_skill_bridge \
  --upstream-root <PINNED_LOCAL_REVERSE_SKILL_CHECKOUT> \
  --project-root <CALLER_PROJECT> \
  --artifact-dir <OUTSIDE_PROJECT_EVIDENCE_DIR> \
  --hint "<SECURITY_OR_REVERSE_TASK>"
```

No automatic download is added. If the pinned checkout or required local shell
is absent, the bridge fails honestly as unavailable. A future supported
dependency-acquisition path should be added only if real usage proves it is
needed and after a separate supply-chain review.

## Acceptance

Focused deterministic tests prove:

- exact upstream commit mismatch fails closed;
- tracked worktree drift fails closed;
- route output is non-authoritative and subordinate to P2P;
- no bootstrap/case-init/MCP/permission-grant surface is invoked;
- route artifacts cannot be written into the target project;
- upstream skill path escape is rejected;
- Windows invocation does not bypass host execution policy.

The security/reverse CI lane also reruns the existing APKiD security foundation
tests so the new bridge cannot silently weaken the prior execution-class and
single-router invariants.

## Nonclaims

This slice does not claim:

- Reverse-Skill itself is independently security-certified;
- every Reverse-Skill skill/tool is safe or installed;
- P2P can execute all Reverse-Skill workflows;
- active pentesting is authorized by methodology routing;
- upstream `PRIMARY` output is P2P routing truth;
- deployment/promotion has occurred.
