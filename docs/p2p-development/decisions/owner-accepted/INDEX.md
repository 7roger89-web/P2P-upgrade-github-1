# INDEX — Owner-accepted decision artifacts (P2P-OWNER-CAPABILITY-INTAKE-STRICT-BINDING-01)

This index is the single authoritative registry of Owner-accepted decision documents archived under `docs/p2p-development/decisions/owner-accepted/`. It was created by **P2P-OWNER-CAPABILITY-INTAKE-STRICT-BINDING-01** to make the chat-only capture boundary mechanically auditable: any accepted-decision artifact that is not present in this index (and in the corresponding durable ledger records) is `PROVENANCE_NOT_RECOVERED`, never silently assumed.

| # | Artifact | Archived at | Intake record | Adoption record | Capability | Roadmap enumeration | SHA-256 (content) |
|---|----------|-------------|---------------|-----------------|------------|---------------------|--------------------|
| 1 | P2P_Contextual_Rule_Intelligence_Update_2026-08-21.md | docs/p2p-development/decisions/owner-accepted/ | RI-007 (PRI-01); RI-008 (INTAKE-CLOSURE-01) | RA-EXT-029 (binds RI-008); RA-EXT-030 (binds RI-007, PARTIAL) | CONTEXTUAL_RULE_INTELLIGENCE | RM-PRIORITY-CONTEXT canonical_capability_ids + composition entry (mode B_explicit_composition) | *(recomputed at verification time — see verification note)* |

**Verification note.** The per-file SHA-256 digest is not pinned into this Markdown index (a Markdown file cannot safely host binary-safe hashes). The authoritative content hash is recomputed mechanically at verification time by reading the archived bytes directly. Current recomputation:

```
7c1cc7597dd65b343a35f007b4c30f4acb08515bee5a4dd6e2155158ac37b96d  P2P_Contextual_Rule_Intelligence_Update_2026-08-21.md
```

**Boundary claim.** The presence of an archived artifact here proves durable capture of the decision text; it does NOT prove automatic live capture of future chat decisions:

`CHAT_ONLY_OWNER_DECISION_AUTO_CAPTURE = NOT_PROVEN`

The index must be updated manually (or by a governed, Owner-visible process) whenever a new accepted decision is archived. No process in this repository silently intakes Owner chat decisions without an explicit intake record.
