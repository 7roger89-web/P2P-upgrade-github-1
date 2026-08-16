# Supervisor review — P2P-C09 supported generic host identity and route observation boundary

## Verdict

`BLOCKED`

The implementation is locally and package-correct, but
`SUPPORTED_ROUTE_WIDE_HOST_IDENTITY_READY` is not proven. Two real
host-owned workers completed bounded read-only probes without fresh official
identity receipts. The correct terminal result is a host-evidence blocker, not
an inferred identity and not a rerun of C08.

## Independent review scope

Reviewed the current source/config, the C09 plan/evidence/benchmark/actual
status ledgers, the coder handoff, the v18 candidate and extracted package
checks, the existing Execution Ledger, the C07/C08 historical reports, Anvien
graph/impact output, focused/affected/full test results, and the protected
artifact hashes.

Subject runtime hashes:

- Hook: `974aab095fde4d9f758bc93725f99e006d1db7253378b70ccccd22fc66df11fc`
- Live boundary: `719622d9220d29fc27632dcc0247ac4a570483c575586030b67b5f400dc45800`
- Config: `1492e390d06dd57bc6982d38b479b23f9ac556d04276e4e84cc11c046114ec23`
- Candidate v18: `5dd547319a4d5ed0d529017d2514470c81e9456d4c448c7820b4adc9868f02c8`

## Acceptance matrix

| Condition | Independent finding | Decision |
|---|---|---|
| C1-C12 route semantics recovered | Existing frozen observation and router tests preserve the route map; C2/C3 lexical ambiguity is disclosed, not redesigned. | PASS |
| `p2p-uiux` is a skill, not a host profile | Registry/SPEC and package doctor preserve `TYPE=SKILL`; no `p2p-uiux` custom profile exists. | PASS |
| Canonical identity safety | Exactly eight canonical identities remain; denominator is 8 and quorum is 8/8. | PASS |
| Official hook/config boundary | Existing hook/ledger path is reused; matcher is explicit for `default`, canonical eight, and Aesthetica; arbitrary and secret-like values fail closed. | PASS |
| Receipt route/executor separation | Existing live receipt path now records logical route/capability separately from requested/observed host identity, class, session, turn, execution ID, and authority. Historical `/1` C07 receipts remain readable. | PASS |
| Fail-closed behavior | Focused suite covers missing, stale, mismatch, wrong session/turn, unknown, secret, tamper, recursion, and proxy cases. | PASS |
| Normal UI without Aesthetica, real host | Router says `p2p-uiux` primary with `call_aesthetica=false`, but no fresh generic/default official receipt exists. | BLOCKED |
| Accessibility-heavy C7, fresh C09 proof | Historical C07 Aesthetica evidence is valid and preserved, but it is not relabeled as fresh C09 evidence. | BLOCKED / NOT RUN |
| Canonical custom profile, real host | Real `p2p_iris` worker completed, but no fresh matching official receipt exists. | BLOCKED |
| Regression/package/integrity | Full suite 111/111; candidate/lifecycle 2/2; package/doctor/capability/drift gates PASS; protected hashes unchanged. | PASS |
| C08 contamination | No C08 scored trial ran; C08 report and Supervisor report were only inspected. | PASS |

## Live host evidence audit

The current ledger contains 18 valid official host receipts, all
`p2p_aesthetica`. It contains zero current `default` receipts and zero current
`p2p_iris` receipts.

The real probes were:

- `default`: host execution ID
  `019fff22-023e-70b1-adb1-cf3f8a00ce29`, read-only completion, no official
  ledger receipt.
- `p2p_iris`: host execution ID
  `019fff25-73a3-7ab0-9794-b345391ef12c`, read-only completion, no official
  ledger receipt.

The worker reports were not used as identity evidence. The absence is
classified as `HOST_EVIDENCE_CAPTURE_FAILURE`; no synthetic receipt was
promoted and no allow-list expansion was attempted.

## Security and boundary review

- No new router, agent, ledger, provider, permission, network, proxy, or
  recursive-delegation surface was added.
- Receipt and request fields are allow-listed; prompts, assistant text,
  environment maps, tool inputs, and secret-like values are not persisted.
- Scoped secret scans for the changed capability and hook sources PASS. The
  broad inherited development-tree scan still reports the documented existing
  GitHub-token placeholder in duplicated marketplace reference files; no new
  finding is attributable to this change. Extracted candidate runtime secret
  scan PASS.
- `.15`, `.16-r2`, and `.17` remain unchanged. v18 is a new unpromoted
  candidate only.
- No Git repository exists, so no commit or diff claim is accepted.

## Required next action

One external-state decision is required: restore or expose the current
official host `SubagentStart` emission/config path so the already allow-listed
`default` and canonical custom worker types produce fresh receipts containing
matching `agent_type`, `agent_id`, `session_id`, and `turn_id`. Then rerun only
the missing bounded live proofs. Do not infer identity from prose, force
Aesthetica, widen the matcher, or rerun C08.

## Final supervisor decision

The local implementation is ready for a future recheck, but the current Goal
is `BLOCKED` because the mandatory real host identity evidence is absent. No
release approval, promotion, deployment, or publication is authorized by
this review.
