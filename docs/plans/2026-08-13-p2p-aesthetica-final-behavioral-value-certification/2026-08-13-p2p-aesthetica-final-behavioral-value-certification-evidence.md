# P2P AESTHETICA — Final Behavioral Value Certification Evidence Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-p2p-aesthetica-final-behavioral-value-certification/2026-08-13-p2p-aesthetica-final-behavioral-value-certification-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-aesthetica-final-behavioral-value-certification/2026-08-13-p2p-aesthetica-final-behavioral-value-certification-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-aesthetica-final-behavioral-value-certification/2026-08-13-p2p-aesthetica-final-behavioral-value-certification-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-aesthetica-final-behavioral-value-certification/2026-08-13-p2p-aesthetica-final-behavioral-value-certification-actual-status.md`

## Evidence Rules

- Evidence is current for the exact development source and host state observed on `2026-08-13`.
- A report or profile is not runtime proof by itself; app-server events and exact host configuration are required for identity claims.
- Persistent trust must be proven without a session-only override.
- No A/B value claim may be made from this blocked P0 run.
- No user project, release ZIP, v5 artifact, or production source was edited for this Goal.
- IDs are stable and phase-scoped.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1` — Repository rules: `AGENTS.md` requires development-source-only work, exact canonical eight, optional/noncanonical Aesthetica, persistent state discipline, temporary roots inside the repo, and no user-project/release mutation.
- `E0-P0A-SRC2` — Exact project exists at `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`; `VERSION` reports `8.4.7-C-codex.9`; project-local `.codex\config.toml` declares `[agents] enabled = true` and `max_concurrent_threads_per_session = 8`.
- `E0-P0A-PROFILE1` — Project-local `.codex\agents` contains the eight canonical profiles and `p2p-aesthetica.toml`. Profile presence is recorded only as a source fact, not as discovery or identity proof.
- `E0-P0A-TRUST1` — Read-only `C:\Users\Admin\.codex\config.toml` inspection found `[projects.'d:\\ai\\p2p_dev'] trust_level = "trusted"` but no exact entry for `d:\\ai\\p2p_dev\\p2p-8.4.6-c-codex-edition-v4`.
- `E0-P0A-HOST1` — A newly spawned `codex app-server --stdio` session, started with the exact project as `cwd`, returned `config/read` with the project layer named for the exact `.codex` folder but `disabledReason`: `To load project-local config, hooks, and exec policies, add d:\\ai\\p2p_dev\\p2p-8.4.6-c-codex-edition-v4 as a trusted project in C:\\Users\\Admin\\.codex\\config.toml.`
- `E0-P0A-HOST2` — The same `config/read` response shows the project layer's `agents.enabled=true` and `max_concurrent_threads_per_session=8`, but the layer is disabled; therefore active project-local agents are not proven.
- `E0-P0A-GATE1` — P0 decision: BLOCKED. Persistent trust smoke failed for the exact project; no child thread, A/B scenario, blinded review, value score, fallback test, or regression claim was run for this Goal.
- `E0-P0A-SEC1` — Targeted secret-pattern scan over the newly created plan/evidence/supervisor files returned no credential/key/token matches. Generic scan terms occur only as requirements; no beginner-facing export was produced.
- `E0-P0A-TRUST2` — On the resumed Goal turn at `2026-08-13 12:17:07 +07:00`, a fresh app-server `config/read` still returned no exact project trust entry; only the parent `d:\\ai\\p2p_dev` entry was trusted.
- `E0-P0A-HOST3` — The fresh response still reports the exact project-local `.codex` layer as disabled with the same explicit instruction to add `d:\\ai\\p2p_dev\\p2p-8.4.6-c-codex-edition-v4` to persistent Codex trust. The project-local declaration still says agents enabled, but active agents remain unproven.
- `E0-P0A-GATE2` — The same blocker repeated on a fresh resumed check. No real child, A/B scenario, blinded review, value score, fallback, consistency, or regression execution was started.
- `E0-P0A-TRUST3` — On the third consecutive Goal-turn smoke, a fresh app-server again resolved `exact_project_trust=null` while the parent `d:\\ai\\p2p_dev` remained trusted.
- `E0-P0A-HOST4` — The third fresh `config/read` again returned the same disabled project-layer reason and the declared-but-inactive `agents.enabled=true` state.
- `E0-P0A-GATE3` — The exact persistent-trust blocker has repeated across three consecutive Goal turns; the Goal is now eligible for the strict BLOCKED stop rule. No downstream behavior was run.
- `E0-P0A-ANV1` — `anvien analyze --force` initially reported the source is not a Git repository. The permitted retry `anvien analyze --force --skip-git` succeeded and produced a current graph at `.anvien\graph.json` (`scanned=212`, `parsed_code=22`, `failed=0`). This is repository mapping evidence only and does not alter the trust verdict.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`, `P1-C`

- Not run. P1 requires exact persistent trust PASS in a new session. The P0 host response explicitly disabled the project-local config layer.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`, `P2-C`

- Not run. No behavioral certification or regression execution may proceed under the Goal's STOP RULE after a P0 trust failure.

## Closure Evidence

- No production source, release artifact, v5 artifact, App Game Truyen, Logistics, or user project was modified.
- Certification result for this run: `BLOCKED at Phase 0 — persistent exact-project trust is missing`.
- Owner action required before resumption: persistently trust the exact development folder `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4` in Codex, then start a new Codex session and rerun the exact trust smoke.
- No commit was created by this blocked run.

## E3 — Current behavioral certification refresh

The previous E0–E2 entries preserve the historical blocked attempt. The current session completed the Goal after exact project trust was active.

- `E3-SCENARIOS` — ten frozen S1–S10 scenarios; scenario SHA-256 `6e0e82e764d74d8a6b7e601a1a058fbde80618ff49d7ba59a584a72fdbea403b`.
- `E3-RUBRIC` — frozen Q1–Q15 rubric; rubric SHA-256 `d076615c1ebdc5d6b177218ac1b2cd04a13ec53cb8eb4952a66f10fefabee79b`.
- `E3-RAW` — raw A/B evidence SHA-256 `fb3360eb8ee48e3e819878a4c88304486847d5d0855b80631f0bef5ca23553b5`.
- `E3-BLIND` — blind packet SHA-256 `731f71fffc3650a51c555d6481c0398d2ffd439cba2f8909774f9bf97bc0c440`; reviewer had no A/B labels, raw evidence, or private map.
- `E3-REVIEW` — independent review completed; private map decoded only after scoring.
- `E3-RECEIPTS` — nine official B receipts matched exact child IDs, `p2p_aesthetica`, and `codex_official_hook`.
- `E3-DECODED` — S5 `+0.40 MODERATE`, S7 `+0.67 MODERATE`; S1/S3 LOW; S2/S4/S6/S8/S9 NEGATIVE; S10 NOT_APPLICABLE.
- `E3-FALLBACK` — unavailable profile fallback PASS; no simulation.
- `E3-CANONICAL` — approved `.14` artifact unchanged; SHA exact; canonical eight and quorum 8/8 preserved.
- `E3-REGRESSION` — 47 relevant tests PASS; targeted secret scan PASS.

Closure: `PASS` with selective conditional value. No runtime routing policy was changed.
