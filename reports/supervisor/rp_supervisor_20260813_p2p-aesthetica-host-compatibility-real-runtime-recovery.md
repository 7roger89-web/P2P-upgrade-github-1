# Supervisor Acceptance - P2P Aesthetica Host Compatibility and Real Runtime Recovery

- Date: `2026-08-13`
- Review mode: independent zero-trust review of source, package, install evidence, host metadata, regression outputs, and QA report
- Verdict: `PASS`
- Scope: only the P2P development source and disposable package/install fixtures

## Source and schema review

The final source profile uses the official standalone custom-agent fields
documented by OpenAI: `name`, `description`, `developer_instructions`, and
read-only `sandbox_mode` ([custom-agent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents)). Unknown P2P classification fields were removed from the host TOML and remain in the P2P manifest. Readiness is fail-closed: profile resolution is not execution identity.

The Windows probes used the supported native `elevated` and `unelevated` modes
([Windows sandbox modes](https://learn.chatgpt.com/docs/windows/windows-sandbox)); no
`danger-full-access`, arbitrary trust edit, or sandbox bypass was used.

## Artifact and lifecycle review

- Baseline `.6` and v5 hashes match their verified values and remain unchanged.
- Final v9 artifact is `8.4.7-C-codex.9`, `2,370,637` bytes,
  SHA-256 `d17ba240cb754d1c7349f8f6273f4785dc778e16c395bf49166e904899f84420`.
- Package verify has `397` content files and `398` checksum entries.
- Package doctor, foundation doctor, UI/UX doctor, governance/quorum, drift,
  and secret checks pass.
- Fresh install, upgrade, and same-version reinstall pass `2/2`.
- The `.8` stale PowerShell doctor finding was surfaced and corrected before
  accepting v9; no failed candidate is presented as final.

## Real runtime identity review

Two independent native read-only child executions are proven by host metadata,
not by prompt wording:

1. Unelevated: child `019ff95f-e1ad-7663-9c48-976d6be2b277`,
   `source.subAgent.thread_spawn.agent_role = p2p_aesthetica`,
   `agentRole = p2p_aesthetica`, nickname `Descartes`.
2. Elevated: child `019ff961-0871-7c11-aeef-35347d6de440`,
   `source.subAgent.thread_spawn.agent_role = p2p_aesthetica`,
   `agentRole = p2p_aesthetica`, nickname `Nietzsche`.

Both children completed bounded accessibility recommendations under read-only,
network-disabled execution. No child changed files, invoked shell/network, or
expanded into backend, database, architecture, permission, or quorum work.

## Governance and regression review

- Canonical identities remain exactly the eight required names.
- Canonical count is `8`; denominator is `8`; full quorum is `8/8`.
- Aesthetica is optional/supporting and excluded from the denominator.
- Backend/API/database routing returns `call_aesthetica=false`.
- Invalid legacy profile is `PROFILE_INVALID`; invalid Decision Trace policy
  reference remains `MISSING_REFERENCE`.
- Full unittest suite is `50/50`; DT1–DT24 is `24/24`.
- Secret scan is empty; no private reasoning or unnecessary developer paths are
  exposed in the tested outputs.

## Acceptance decision

`PASS`. HC1–HC18 are satisfied. The final v9 package is acceptable for the
P2P development release path. No App Game Truyen, Logistics, real user project,
v5 artifact, or verified `.6` artifact was modified. Exactly one residual-risk
recommendation: persist trust for the exact P2P development/project root before
normal host sessions if that user security decision remains unrecorded.
