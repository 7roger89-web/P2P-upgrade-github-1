# AI next steps

- Inventory gate: PASS
- Baseline reconciled: 152/152
- New release reconciled: 1383/1383
- Modified: 0
- Added: 1383
- Removed: 152
- Renamed/moved: 0

Read every modified and added file in full. Review removed capabilities and all
renames. Update the Excel master and append release history. Then review volatile
claims in FACT_LEDGER, create the deterministic technical preview, obtain
approval for both the exact ledger and preview hashes, rebuild and lock Live
Specs, rerun affected project evals and RAG retrieval checks, rebuild
the protected-runtime manifest, run drift, preserve a rollback artifact, and run
the package doctor. Then create a technical gate report, request final user
approval bound to both the report hash and unchanged candidate hash, and run the
final gate. Update release-gates.json with evidence for each gate. Do not claim
that the Codex runtime was ported: this report is inventory and change detection
only. Stop if inventory is not PASS. Approval cannot override any NOT_STARTED or
FAIL gate, and any candidate change invalidates the approval.
