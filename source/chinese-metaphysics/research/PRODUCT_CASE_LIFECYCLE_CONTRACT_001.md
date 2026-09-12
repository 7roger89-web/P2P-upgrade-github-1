# PRODUCT_CASE_LIFECYCLE_CONTRACT_001

TASK_ID: CHINESE_METAPHYSICS_LARGE_GOAL_01
STATUS: CONTRACT_ONLY
WEBSITE_BUILT: NO

## Minimal prediction lifecycle

Purpose:
prevent hindsight edits before any future blind/outcome validation.

### Prediction lock record

```json
{
  "case_id": "...",
  "domain": "...",
  "profile_id": "...",
  "method_lane": "...",
  "deterministic_packet_ref": "...",
  "rule_trace_refs": ["..."],
  "prediction_payload": {},
  "locked_at": "ISO-8601",
  "canonicalization": "JSON canonical form v1",
  "sha256": "..."
}
```

Lock hash:
`SHA256(canonical_json(prediction_payload + profile_id + method_lane + deterministic_packet_ref + rule_trace_refs))`

### Outcome record

Outcome is a separate record created after the lock:

```json
{
  "case_id": "...",
  "prediction_sha256": "...",
  "revealed_at": "...",
  "outcome_payload": {},
  "outcome_source": "...",
  "outcome_precision": "..."
}
```

### Rethink record

Any reinterpretation after reveal must be a new append-only record referencing:
- original prediction hash;
- outcome hash/ref;
- new analysis version;
- reason for change.

The original prediction is never overwritten.

## Product boundary

Allowed now:
- explicit domain;
- explicit calculation/convention profile;
- declared method lane;
- provenance level;
- rule trace;
- conflict/nonclaim fields;
- prediction lock hash.

Not built now:
- database;
- website;
- profile registry service;
- universal resolver;
- scoring dashboard.

This is a contract, not infrastructure.
