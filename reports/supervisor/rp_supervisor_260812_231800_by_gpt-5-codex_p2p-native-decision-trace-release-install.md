# Supervisor Acceptance — P2P Native Decision Trace Release / Install Integration

- Date: `2026-08-12`
- Verdict: `PASS`
- Scope: actual `.5` artifact, package doctor, PowerShell/POSIX install, upgrade, post-upgrade runtime, same-version reinstall, boundary, regression, and release evidence.

## Independent source-of-truth checks

- Final artifact: `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v5.zip`.
- Final SHA-256: `f88dbf706c4ac85a8aadf38960923cdc8e4ba6e415b83f3f1726692fb3ad8dda`.
- Final inventory: `397` content files and `399` ZIP members.
- Baseline `.4` SHA-256 remains `1d1d00913b215e513a2441f194125b96e9e7999a0659ae713d3e10d2de4dcccb`.
- Actual extracted package doctor, package drift, package secret scan, installed doctor, and installed Decision Trace doctor all PASS.
- Full regression rerun: `48/48` tests, `OK`.

## Lifecycle acceptance

- Fresh PowerShell install provisions the runtime automatically and its installer doctor validates Decision Trace, the existing ledger, canonical `8/8`, optional Aesthetica, and zero external dependencies.
- POSIX installer also runs on the available Bash/WSL host; fresh install and a real POSIX runtime capture/doctor pass.
- Upgrade from `.4` is classified correctly; protected project hashes and legacy execution-ledger bytes remain unchanged, while the old system state is retained in the installer backup.
- Legacy history is not backfilled; a legacy query returns `UNKNOWN` with no invented native trace.
- A legitimate post-upgrade material decision appends one native trace after the preserved legacy prefix.
- Same-version reinstall is `SAME_VERSION_REINSTALL`; ledger bytes, trace count, protected state, capability declarations, and backup count remain unchanged.

## Runtime and governance acceptance

- Runtime certification passes materiality/routine behavior, approval evidence, fact/evidence/source links, contradiction, supersession, temporal reconstruction, reverse artifact lookup, redaction, integrity mutation detection, missing-reference honesty, deterministic JSON/Markdown export, and idempotent append.
- UI/UX DW1–DW18 and Capability Foundation regression pass.
- Canonical identities remain exactly eight with denominator `8` and full quorum `8/8`; `p2p_aesthetica` remains `SUPPORTING / OPTIONAL DOMAIN SPECIALIST` and noncanonical.
- Aesthetica evidence reaches `PROFILE_RESOLVES` / `AGENT_EXECUTION_NOT_PROVEN` / `IDENTITY_NOT_VERIFIED`; no identity is simulated.
- Beginner WHY works without a Decision ID, with `integrity_status=VERIFIED`; two missing policy references remain surfaced as `MISSING_REFERENCE` rather than hidden or falsely verified.

## Boundary and next action

- No App Game Truyện, Logistics, user project, user home, public publication, external provider, graph/RDF/MCP, or developer-only evaluator payload entered the release ZIP.
- Exactly one evidence-backed next Goal is recommended: normalize installed workflow policy-reference paths for Native Decision Trace, based on the two honest `MISSING_REFERENCE` results in the fresh WHY report. It is not implemented in this Goal.

Evidence source: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.tmp\release-certification-20260812-230500\supervisor-audit.json`.
