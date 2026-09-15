# P2P FCC FREE-LANE ADOPTION NOTE — 2026-09-15

Status: `SOURCE_ADAPTER_CANDIDATE_UNPROMOTED`

## Source truth

- Upstream: `Alishahryar1/free-claude-code`
- Upstream commit inspected: `22d9d19f5e7a1b31f7d8fccff6fef77cbb19357f`
- Upstream package version at that commit: `6.2.28`
- License: MIT
- P2P base main for this slice: `fc63c4a593da3f9fa7d9b1bb30c3e1ba2bfe63e7`

Upstream FCC exposes multiple coding harness launchers (`fcc-claude`,
`fcc-codex`, `fcc-hermes`, etc.), maps Claude Code to its local proxy through
`ANTHROPIC_BASE_URL`, supports a model catalog across many providers, and owns
its own ordered model-fallback behavior. Provider free tiers and quotas are
controlled by those providers and can change.

## Decision

P2P does **not** adopt FCC's `ModelRouter` as another P2P router.

The existing P2P authority remains:

```text
P2P task / role / capability decision
        -> existing single P2P routing + explicit backend registry
        -> explicit adapter_id = fcc-claude-cli
        -> fcc-claude
        -> FCC proxy/model routing/fallback
        -> configured upstream provider/model
```

This preserves the existing invariant `REGISTRY != ROUTER` and avoids two
independent P2P routing authorities.

## First bounded slice

Implemented adapter:

`.p2p/system/p2p_capabilities/fcc_claude_adapter.py`

Properties:

- reuses the C34 `BackendAdapterIdentity`, `AdapterHealthState`, and
  `BackendExecutionResult` contracts;
- executes only foreground Claude Code print mode through `fcc-claude`;
- pins `--permission-mode plan`, `--no-session-persistence`, `--max-turns`, and
  a hard process timeout;
- never passes Claude Code permission-bypass flags;
- accepts an explicit per-task `model` through the existing C34 target profile;
- treats `provider` as a requested/evidence hint only because FCC, not P2P,
  owns the serving provider and fallback chain;
- does not mutate FCC's global configuration;
- records actual provider/model/fallback as `UNKNOWN` unless independently
  observed from execution evidence;
- records `free_tier_guaranteed=false` even when a model name contains
  `free`, because provider policy/quota can change and fallback may consume a
  different provider's usage;
- does not claim code mutation, test execution, Git write, browser, database,
  or long-horizon certification.

## Why FREE_LANE is a lane intent, not a router

`FREE_LANE` means P2P may explicitly choose an FCC target profile whose
requested model is currently free/local/zero-marginal-cost according to fresh
provider state. It is not a permanent model list and not a zero-cost guarantee.

The first representative profile can therefore be shaped as:

```python
{
    "adapter_id": "fcc-claude-cli",
    "model": "open_router/openrouter/free",
    "provider": "open_router",  # evidence hint, not a routing command
    "max_turns": 25,
    "timeout_seconds": 300,
}
```

The adapter passes `model` to Claude Code but deliberately does not invent a
`--provider` argument. FCC remains responsible for translating that model into
its configured provider runtime.

## Fallback boundary

FCC upstream can retry and fall back to its next configured model. That is
valuable availability behavior, but P2P must not silently equate a requested
model with the model/provider that actually served the request.

For this slice:

```text
REQUESTED_MODEL = KNOWN when target profile pins it
REQUESTED_PROVIDER_HINT = optional
ACTUAL_PROVIDER = UNKNOWN unless observed
ACTUAL_MODEL = UNKNOWN unless observed
FALLBACK_OBSERVED = UNKNOWN unless observed
FREE_TIER_GUARANTEED = false
```

A later slice may consume FCC's existing request/fallback trace evidence to
bind requested primary -> fallback event -> actual serving target. That work is
not required for this adapter to provide honest bounded non-mutating execution.

## Acceptance for this slice

1. Existing P2P router is unchanged.
2. Existing C34 backend bridge is unchanged.
3. FCC adapter can be explicitly registered in the existing
   `BackendAdapterRegistry`.
4. Deterministic tests prove command safety, C34 bridge compatibility,
   fail-closed unknown failures, timeout normalization, evidence prompt
   redaction, and non-fabrication of provider/model/cost truth.
5. No provider credentials, live quota, install, release, promotion, or
   deployment is required or implied.

## Promotion boundary

`SOURCE_ADAPTER_CANDIDATE_UNPROMOTED` means exactly that. A green source PR does
not certify a live FCC installation, live free quota, provider auth, model
quality, mutation capability, or a packaged P2P release. Those require
representative evidence and the normal P2P release/promotion gates.
