# Bounded Documentation Write Capability Ledger

**Module:** `.p2p/system/p2p_capabilities/bounded_documentation_write.py`
**STATUS:** `READY` — canonical primitive implemented, schema-admitted, verifier-bound,
package-shipped in candidate `8.4.7-C-codex.38` (UNPROMOTED).
**Goal closed:** `P2P-BOUNDED-DOCUMENTATION-WRITE-01` (closes the seam proven by
`P2P-GT-MUTATION-PILOT-01`: `BLOCKED / NO_CANONICAL_DOCUMENTATION_MUTATION_CAPABILITY`).
**Ledger version:** 1.0.0 · schema `p2p-bounded-documentation-write-ledger/1`

## 1. SEMANTICS

The runtime ships exactly ONE canonical documentation-mutation primitive:
`execute_bounded_document_mutation(contract, project_root, dispatch_id, ...)`.
It performs **exactly one** bounded UTF-8 text-document write inside an explicitly
authorized isolated/non-production workspace. It is fail-closed on every axis:
unknown path classification, protected surfaces, stale `before_hash`, missing
Owner authorization, budget overrun, binary content, non-atomic write, or any
unexpected exception raise `BoundedDocWriteError` and **no file is ever written**.
There is no generic filesystem WRITE, no delete, no rename, no shell write path.
The primitive additionally produces deterministic changed-surface evidence
(`BoundedDocWriteEvidence`), FW04 quality verdict, FW05 owner summary, and
lease/interruption state (FW06).

**Canonical class:** `DOCUMENTATION_WRITE_ONLY`. A mutation with
`changed_bytes == 0` is not accepted as proof; `before_file_hash` must be either
a real digest or the sentinel `NON_EXISTENT` (first creation of a document).

## 2. PROVENANCE

| Item | Value |
|---|---|
| Implementation commit | `a6d2c33e62f91fd7a05d511085750945a5c25973` |
| Implementation tree | `1ff1b54cca35a9aa44f7c2df62166487d0188d89` |
| Carrying candidate | `8.4.7-C-codex.38` — `d062ec5c4f8d2cb264c0b405de5236850d53d04757e264d871cf12395b0ec253` (UNPROMOTED) |
| Predecessor candidate | `8.4.7-C-codex.37` — `4aafdcd383b1002842df2465cfd3ce5f4bb3d9d792ce75ad5000771e629640f7` (immutable, UNPROMOTED, untouched) |
| Schema admission | `TASK_CAPABILITY` added to `CAPABILITY_CLASSES`; `HOST_PRIMITIVE` added to `INVOCATION_CLASSES` in `model.py` (fail-closed enums) |
| Test evidence | `tests/test_bounded_documentation_write.py` — 46 tests, all PASS; full capability suite 309 tests PASS; framework validation 78/78; fresh-tree verifier ALL PASS; doctor HEALTHY |

## 3. DEPENDENCIES

`bounded_documentation_write` depends on: `capabilities.json` registry entry,
`capability_intelligence` (FW02 owner-mutation envelope inference), `role_contract`
(`WRITE_BOUNDED` grant + 4 mutation fields), `role_eligibility`
(`PERMISSION_ORDER: … READ, WRITE_BOUNDED, WRITE, …`), `backend_contract`
(`DOCUMENTATION_MUTATION_BOUNDED` certification scope), `role_bridge` (dispatch
bounded path), `role_receipt` (whole-claim verifier bounded branch),
`host_attestation` (canonical replay ledger), `fw04/fw05/fw06` modules.
None of these were removed or weakened; only additive extensions were made.

## 4. PERMISSION BOUNDARY

`WRITE_BOUNDED` ranks strictly between `READ` and `WRITE`: a role holding only
`WRITE_BOUNDED` never satisfies a `WRITE` ceiling; read-only roles are never
granted `WRITE_BOUNDED`. The capability is `HOST_PRIMITIVE` invoked only inside
an owner-signed mutation envelope (`OWNER_AUTHORIZATION_ID` required, invalid
values block). Certified scope `DOCUMENTATION_MUTATION_BOUNDED` is opt-in:
default role/backend certification stays mutation-free.

## 5. PROTECTED SURFACES (fail-closed classification)

`classify_document_path` returns `DOCUMENTATION_ALLOWED` only for documentation
surfaces (`docs/**`, `README*`, `CHANGELOG*`, `CONTRIBUTING*`, `reports/**/*.md`);
everything else returns `PROTECTED` (`.git/**`, `.p2p/**`, `.env*`, secrets,
lockfiles, manifests, `AGENTS.md`, `TASKS.md`, migrations, tests, code) or
`UNKNOWN` (blocked). Symlinks, absolute paths, traversal (`..`) and writes
escaping the project root raise `BoundedDocWriteError` before any I/O.

## 6. MUTATION CONTRACT

`BoundedDocMutationContract` (frozen, fail-closed validation): `mutation_class
== DOCUMENTATION_WRITE_ONLY`; `max_changed_files == 1`; single
`allowed_relative_path`; `before_hash` (digest or `NON_EXISTENT`) verified against
the live file (stale → `BEFORE_HASH_STALE_MISMATCH`; nonexistent contradicted
→ `BEFORE_HASH_NON_EXISTENT_CONTRADICTED`); `max_changed_lines`, `max_bytes`;
`rollback_required == REQUIRED`; `owner_authorization_id` non-trivial;
`candidate_sha` 64-char hex; `acceptance_criteria`; `mutation_content` (UTF-8,
binary rejected). `constraint_fingerprint()` is a SHA-256 over all constraint
fields (stable, sensitive to any bound change).

## 7. EVIDENCE REQUIREMENTS

`BoundedDocWriteEvidence`: schema `p2p-bounded-documentation-write/1`, exact
`before/after_file_hash` + `before/after_tree_hash`, `changed_relative_path`,
`changed_file_count == 1`, positive `changed_line_count`/`changed_bytes`,
`mutation_class`, `owner_authorization_id`, `contract_fingerprint`,
`dispatch_id`, `execution_id`, `host_attestation_id` (derived from the
execution pair when no attestation exists at execution time — never empty,
so the verifier's identity-binding check never fails open),
`rollback_required == REQUIRED`, `rollback_state`.

The whole-claim verifier (`role_receipt`) bounded branch mechanically checks:
schema, hash validity (40–64 hex or `NON_EXISTENT` before-fields), exactly-one
file, positive bytes, hash delta, canonical class, identity binding, rollback
required; dispatch must report `possible_mutation=True` with the identical
single changed surface (`dispatch_consistent_with_bounded_evidence`);
`application_mutation` is counted from evidence (1), never from the backend
dispatch. Whole-claim dispatch_ok requires this plus the attestation replay
ledger and tree-hash binding.

## 8. ROLLBACK REQUIREMENT

`rollback_bounded_document_mutation(evidence, project_root, original_content)`
restores exact original bytes (existing file) or removes the created file
(`NON_EXISTENT`), proving `FINAL_FILE_STATE == ORIGINAL` and
`FINAL_TREE_HASH == PRE_MUTATION`. Rollback failure raises; never best-effort.
FW06 lease (`max_parallelism = 1`) plus an interruption marker between write
and verification make mid-crash states recoverable as
`MUTATION_UNVERIFIED/ROLLBACK_REQUIRED` instead of silent retry.

## 9. KNOWN LIMITATIONS

1. Working-tree primitive: the mutation is written to the working tree and
   untracked files; the git `HEAD^{tree}` hash is unchanged by design —
   content-level before/after file hashes carry the mutation delta
   (evidence, not repository history mutation).
2. First-mutation sentinel: `NON_EXISTENT` is accepted only for `before_*`
   fields; verifier requires real digests for `after_*`.
3. Fixture proven only in `ISOLATED_NON_PRODUCTION` fixtures; the real
   Game Truyện documentation mutation pilot is NOT executed in this goal and
   remains gated behind the second Owner decision.
4. One file per execution; multi-file documentation envelopes require chained
   single-file executions, each with its own contract and evidence.

---

# ADDENDUM A — AUTHORITY-CHAIN CLOSURE (P2P-BOUNDED-DOCUMENTATION-WRITE-01A)

**Module:** `.p2p/system/p2p_capabilities/authority_chain_registry.py`
**Extends:** `bounded_documentation_write` (ledger above), `role_eligibility`,
`role_bridge`, `role_receipt`, `backend_contract`
**STATUS:** `READY` — authority-chain closure implemented, schema-admitted,
verifier-bound, package-shipped in candidate `8.4.7-C-codex.39` (UNPROMOTED).
**Goal closed:** `P2P-BOUNDED-DOCUMENTATION-WRITE-01A` (closes the seam proven by
`P2P-BOUNDED-DOCUMENTATION-WRITE-01`: the bounded primitive existed but the
role×target×host mutation authority chain never closed — role grant was broad,
no subject-bound certification, no canonical scope mapping, and a derived
attestation ID was accepted for mutation-ready execution).
**Ledger version:** 1.1.0 · schema `p2p-authority-chain-ledger/1`

## A1. SEMANTICS

A bounded documentation mutation is now valid **only when all four authority
links close over the same identity**: (1) the selected role is the minimum
canonical role whose registry semantics support bounded mutation write
(`p2p_architecton`, with `bounded_documentation_write` added to its `REQUIRES`;
`p2p_iris` excluded per Owner constraint); (2) the capability carries an
explicit `EXECUTION_SCOPE: DOCUMENTATION_MUTATION_BOUNDED` in the registry
(`CAPABILITY_EXECUTION_SCOPE_MAP` in `backend_contract` is the fail-closed
module fallback when the registry record is absent — unknown capability → hard
BLOCK); (3) the backend target holds a current LIVE certification for that
exact scope (`authority_chain_registry` ledger, kind
`BACKEND_MUTATION_CERTIFICATION`, status `MUTATION_TARGET_LIVE`); (4) the
selected role holds a subject-bound certification naming the SAME role id,
capability, scope and canonical grant `WRITE_BOUNDED`, bound to the exact
`owner_authorization_id` (kind `ROLE_MUTATION_CERTIFICATION`). The executing
host attestation must be **real**: `execute_bounded_document_mutation` requires
a `HostAttestationRecord` produced by `make_canonical_host_attestation` for
`mutation_authority_mode == PRODUCTION`; derived/fallback IDs are confined to
`TEST_ONLY` and can never reach a mutation-ready dispatch. The whole-claim
verifier (`verify_bounded_mutation_receipt`, `_g1_authority_chain_check`)
re-checks every link mechanically; any broken link fails `authority_chain.overall`
and `overall`, independent of the mutation-evidence branch.

## A2. PROVENANCE

| Item | Value |
|---|---|
| Implementation commit | `587e81a306e62ac9661c11f826c7ddc5c298eac1` |
| Implementation tree | `980b19b5fbc209deca5bac99894a7ebdd0ace0ff` |
| Carrying candidate | `8.4.7-C-codex.39` — `a21d8122a29146970889499dd74ad1fe0eb7be51491f7481cce62132ce82ed69` (UNPROMOTED) |
| Predecessor candidate | `8.4.7-C-codex.38` — `d062ec5c4f8d2cb264c0b405de5236850d53d04757e264d871cf12395b0ec253` (immutable, UNPROMOTED, untouched) |
| Test evidence | `tests/test_bounded_mutation_authority_chain.py` — 26 tests PASS (M0/M1/M2 positive lifecycle, crash-retry, 15-case negative matrix A-O, scope-mapping, role-selection) |

## A3. FAIL-CLOSED SURFACES PROVEN (negative matrix A-O, fresh disposable Git fixture)

| Row | Broken link | Verifier result |
|---|---|---|
| A | No target certification | `authority_chain.overall = False` |
| B | Expired target certification | `target_certification_current = False` |
| C | Target certified for different adapter | `execution_scope_certified_for_target = False` |
| D | No role certification | `target_certification_subject_bound_to_role = False` |
| E | Wrong role holds the certification | `target_certification_subject_bound_to_role = False` |
| F | Wrong owner authorization id | `target_certification_subject_bound_to_role = False` |
| G | Different scope claimed (impossible by construction — scope-locked certification layer; absence closes the chain) | `target_certification_subject_bound_to_role = False` |
| H | Non-canonical grant (`WRITE`) | `ValueError` at certification append; receipt mutation class mismatch fails evidence check |
| I | Missing attestation block | `attestation_present = False`, hard failure |
| J | Synthetic attestation fingerprint | `host_identity_real = False` |
| K | Attestation fingerprint ≠ evidence anchor | `attestation_matches_evidence = False` |
| L | Replay-conflicted attestation | `replay_conflict_detected = True` |
| M | Tree baseline drift (h1 ≠ h2) | `h1_equals_h2 = False`, not identity-locked |
| N | Role registry no longer provides capability | `role_provides_capability = False` |
| O | Capability stripped of EXECUTION_SCOPE | `capability_scope_mapping_valid = False`, hard BLOCK |

## A4. LIMITATIONS (addendum to §9 above)

1. The certification ledger is a fresh append-only JSON store
   (`.p2p/state/authority_chain_registry.json`, path governed by
   `P2P_STATE_DIR`); it is test-isolated by environment variable and carries no
   cryptographic signatures — trust derives from the execution-side
   attestation binding and the whole-claim verifier, not the ledger itself.
2. Scope-locked by design: the certification layer refuses any scope other
   than `DOCUMENTATION_MUTATION_BOUNDED`; this makes row-G-style "wrong scope"
   failures structural rather than data-driven.
3. Unchanged from §9: working-tree primitive, `NON_EXISTENT` sentinel rules,
   and the real Game Truyện documentation mutation pilot remain
   NOT executed, gated behind the second Owner decision.
