# Proposed acceptance change for Issue #333

Status: PROPOSED. Not Owner-approved. Not independently validated.
This document does not complete Issue #333 and does not change Supreme Law.

## Original acceptance remains unresolved

Issue #333 required `GENERIC_EXACT_REPO_READ` when current C21 discovery
evidence proves a non-Arena/non-Codex host can actually read the target
repository, plus one real generic canary that returns an exact consumption
receipt.

PR #334 still fail-closes that lane:

`HOST_TRUSTED_REPO_READ_OBSERVATION_UNAVAILABLE`

No trusted external-actor repository-read observation producer is available.
Original B1 therefore remains `BLOCKED`. A C20/C21 record, local hash, or
caller-authored provenance label is not that producer.

## Narrower proposed slice

Add a distinct, non-authorizing capability:

- name: `PROMPT_ONLY`
- host mode: `GENERIC_PROMPT_ONLY`
- operation: `PREPARE` only

This capability may:

- select at most three repo-native skills through the existing router
- freeze exact `SKILL.md` paths and SHA-256 hashes
- emit one copyable delegated-work prompt
- require the recipient to read/apply those skills and return
  `p2p-skill-consumption-receipt/1`

This capability must not:

- change the meaning of `GENERIC_EXACT_REPO_READ`
- attest that the recipient already read the files
- start an executor or Control Tower session
- authorize remote mutation or automatic generic execution
- reuse `SKILL_CHECK=PASS` as execution authorization
- promote a self-reported receipt into trusted external-actor evidence

Prepared state is explicit:

```text
SOURCE_VALIDATION=PASS|NO_MATCH|BLOCKED
RECIPIENT_CONSUMPTION=UNVERIFIED|NOT_REQUIRED|NOT_ATTESTED
EXECUTION_AUTHORIZED=NO
EXTERNAL_ACTOR_READ=NOT_VERIFIED
```

A structurally matching returned receipt is `SELF_REPORTED` only.

## Merge boundary

`MERGE=NO` while original Issue #333 acceptance is unresolved, and while this
narrowed acceptance has not been explicitly approved and independently
validated. No release, deploy, or promotion.
