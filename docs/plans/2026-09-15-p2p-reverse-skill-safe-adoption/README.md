# P2P Reverse-Skill Safe Adoption

## Goal

Adopt the useful methodology and routing knowledge from `zhaoxuya520/reverse-skill` into the existing P2P SEC01 security/reverse foundation without adding a second router, auto-installer, MCP control plane, or implicit offensive execution path.

## Upstream pin

- Repository: `https://github.com/zhaoxuya520/reverse-skill`
- Commit: `7e2097fd90d25c2f976f6eba26d6c00aa88051df`
- License: MIT
- Pin date: 2026-09-15

Reviewed upstream source surfaces:

- `skills/config/routing.json` — routing taxonomy / single-source-of-truth pattern.
- `skills/ops/scope-contract.md` — authorization and scope hard-gate pattern.
- `skills/ops/skill-supply-chain.md` — skill/MCP/bootstrap supply-chain controls.
- `LICENSE` — repository license.

## What P2P adopts

1. **Methodology cross-reference after P2P routing.** Existing P2P security/reverse capability IDs can resolve a pinned Reverse-Skill methodology reference. User text is never classified by the bridge.
2. **Scope-before-ACT principle.** This aligns with existing P2P execution classes and authorization gates; upstream scope files do not become a second authority store.
3. **Selective loading / no skill pile-up.** Only the methodology relevant to an already-selected P2P capability is referenced.
4. **Supply-chain suspicion by default.** External skills, MCPs, scripts and bootstrap instructions never grant permissions merely because upstream text says so.
5. **Exact provenance.** The adoption records an exact upstream commit rather than following `main` at runtime.

## What P2P explicitly rejects

The following upstream surfaces are **not** automatically loaded or executed by this adoption:

- `README_AI.md` and `RULES.md` host/bootstrap behavior.
- `skills/scripts/` and `kali/scripts/` auto-bootstrap/tool installation flows.
- `skills/attack-chain/`, `skills/edr-bypass-re/`, `skills/patch-diff-exploit/`, `skills/pentest-tools/`, `skills/pwn-chain/`.
- `CTF-Sandbox-Orchestrator/`.
- silent MCP registration, global host configuration writes, automatic dependency installation, network execution, credential use, target interaction, exploit execution, or permission escalation.

Those exclusions are not a claim that upstream is malicious. They preserve the P2P rule that **external content is evidence/methodology, never authority**.

## Runtime shape

Implementation:

` .p2p/system/p2p_capabilities/reverse_skill_reference.py `

The module is intentionally data-only. It exposes:

- exact upstream provenance;
- reviewed and excluded source surfaces;
- a post-route mapping from existing P2P security/reverse capability IDs to relevant upstream route IDs/topics;
- execution-class ceilings;
- explicit `False` flags for bootstrap, auto-install, MCP registration, network runtime and external execution.

It does **not**:

- accept arbitrary task text;
- invoke the existing P2P router;
- invoke the upstream router;
- execute a subprocess;
- install software;
- touch the network;
- register MCP servers;
- authorize targets;
- create a new capability registry or truth store.

## Existing P2P capabilities covered

- `android.protection.detect`
- `android.artifact.decode`
- `security.mobile.static.assess`
- `android.runtime.instrument`
- `android.network.inspect`
- `reverse.identify`
- `reverse.decompile.managed`
- `reverse.decompile.native`
- `reverse.deobfuscate`
- `reverse.callgraph`
- `reverse.semantic_reconstruct`

Execution remains governed by the existing SEC01 contracts. In particular, `ACTIVE_TEST_AUTHORIZED` remains authorization-gated and this reference bridge cannot raise an execution class or grant authority.

## Acceptance contract

`tests/test_p2p_reverse_skill_reference.py` must prove:

1. exact upstream commit pin;
2. every mapped ID already exists in the current P2P registry;
3. canonical P2P quorum remains 8/8;
4. P2P is the sole router authority;
5. no bootstrap/install/MCP/network/external-execution permission is granted;
6. dangerous upstream execution surfaces are explicitly excluded;
7. unknown capability lookup fails closed;
8. the bridge contains no execution/install primitive and no task classifier.

## Promotion boundary

This task creates an integration candidate only. It does not authorize release, deployment, production target testing, dependency installation, or activation of offensive upstream modules.
