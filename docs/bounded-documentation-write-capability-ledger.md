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

---

# PHỤ LỤC B — P2P-BOUNDED-DOCUMENTATION-WRITE-01B (Hiệu chỉnh ngữ nghĩa vai/host)

**Ledger version:** 1.2.0 · schema `p2p-bounded-documentation-write-ledger/1`
**Goal closed:** `P2P-BOUNDED-DOCUMENTATION-WRITE-01B` (khép hai seam ngữ nghĩa còn lại sau BW01A).

## B.1. PROVENANCE

| Item | Value |
|---|---|
| Implementation commit | `a1e78bc378d8efe65840ec7c3d23ded121284759` |
| Implementation tree | `3bb25bff45941045123ac9ab426cb24ad62149ff` |
| Carrying candidate | `8.4.7-C-codex.40` — `f2edabf09de2657b63ad930636599295e96d94d0eea47fc91e14081c7e600519` (UNPROMOTED, fresh-tree verified) |
| Predecessor candidate | `8.4.7-C-codex.39` — `a21d8122a29146970889499dd74ad1fe0eb7be51491f7481cce62132ce82ed69` (immutable, UNPROMOTED, untouched) |
| Test evidence | `tests/test_bounded_role_host_semantics.py` — 22 tests (dương M0/M1/M2 + ma trận tiêu cực A–N) trên fixture Git dùng một lần; hồi quy 357 tests PASS; framework 78/78; dev-control PASS; gitleaks 0 leak mới |

## B.2. SEMANTIC CORRECTION 1 — REQUIRES/PROVIDES CONFLATION (CLOSED)

Seam đã được chứng minh: registry role không có trường `PROVIDES` nào; checker quyền
đọc `REQUIRES` như "provides"; FW03 `role_capability_evidence` kết hợp `CAPABILITY_ID + REQUIRES`
thành tập năng lực do vai cung cấp. Sửa fail-closed:

1. **Trường `PROVIDES` tường minh** trên role record (`capabilities.json`). Vai
   `p2p_architecton` ghi `PROVIDES: ["bounded_documentation_write"]` — đây là nguồn ngữ nghĩa
   chính tắc duy nhất cho "vai cung cấp gì".
2. `team_intelligence.role_capability_evidence` giờ chỉ phát ra evidence row cho các
   năng lực nằm trong `PROVIDES`; row không tồn tại khi vai không tuyên bố cung cấp —
   `REQUIRES` **không bao giờ** được thăng cấp vào bề mặt provided (role chỉ dùng năng lực
   khi một vai khác cung cấp + chính sách cho phép).
3. `build_team_decision` PROVIDE-set tính từ evidence rows (từng dòng PROVIDES), không còn
   cộng gộp từ REQUIRES.
4. Checker toàn-claim (`_g1_authority_chain_check`) thêm bước
   `role_explicitly_provides_capability`: fail nếu vai được chọn không có `PROVIDES` chứa
   năng lực đột biến — kể cả khi REQUIRES liệt kê.
5. Fixture FW03 (test suite + production registry) được hòa hợp về ngữ nghĩa tường minh;
   41/41 test FW03 PASS sau hòa hợp.

**ROLE_PROVISION_SEMANTIC_CONFLATION = RESOLVED.** Chon vai tối thiểu được đánh giá lại
thuần túy trên PROVIDES: `p2p_architecton` vẫn là vai tối thiểu phù hợp (cung cấp
`bounded_documentation_write`; 7 vai còn lại không tuyên bố cung cấp).

## B.3. SEMANTIC CORRECTION 2 — AUTHORITY MODE SEMANTICS (CLOSED)

1. **Hằng số chính tắc** `MUTATION_AUTHORITY_MODES = ("MUTATION_READY", "TEST_ONLY")` trong
   `bounded_documentation_write.py`; đầu vào không chính tắc → lỗi fail-closed.
2. Cổng thực thi khóa theo **authority mode** (không theo nhãn môi trường):
   - `MUTATION_READY` → HostAttestation **thật bắt buộc** + `rollback_required="REQUIRED"`;
     derived ID chỉ chấp nhận trong nhánh `TEST_ONLY` (bằng chứng đánh dấu `test_only_evidence=true`).
   - `TEST_ONLY` → **không bao giờ escalade**: thực thi chỉ khi evidence mang
     `test_only_evidence=true` và không có HostAttestation thật; mọi receipt mang mode này bị
     verifier đánh `mutation_authority_mode_is_mutation_ready=false`.
3. Evidence mang `mutation_authority_mode`; role_bridge dispatch chuyền mode chính tắc;
   receipt mang khối `authority` (mode + test_only_evidence + attestation fingerprint).
4. Verifier thêm các bước: `mutation_authority_mode_is_canonical`,
   `mutation_authority_mode_is_mutation_ready`, `test_only_evidence` — tất cả fail-closed.

**TEST_ONLY_NEVER_ESCALATES = VERIFIED** (ma trận tiêu cực BW01B rows kiểm chứng từng liên kết).

## B.4. KNOWN REMAINING LIMITS

1. Chứng nhận target đột biến vẫn là lớp registry trong-runtime (chưa có nguồn chứng nhận
   bên ngoài được xác thực); giữ nguyên trạng thái BW01A.
2. Pilot đột biến Game Truyện thật thứ hai vẫn **chưa thực hiện** — vẫn là quyết định Owner
   trên ứng viên .40.



## ADDENDUM — P2P-MUTATION-SAFETY-INTEGRATION-01 (CORRECTIVE, APPENDED)

This addendum is appended to the canonical bounded-documentation-write ledger. It does
not modify, reinterpret, or overwrite any prior ledger entry. Pilot-02 entries and the
Closure-01 evidence remain authoritative history.

### Corrective statements

1. Candidate `.40` (version `8.4.7-C-codex.40`, artifact SHA
   `f2edabf09de2657b63ad930636599295e96d94d0eea47fc91e14081c7e600519`,
   source `a1e78bc378d8efe65840ec7c3d23ded121284759`) shipped the original
   protected-basename classifier. Its protected-surface patterns were anchored to the
   beginning of the path string, so `TASKS.md`, `AGENTS.md`, and
   `P2P-PROJECT-BOOTSTRAP.md` were protected **only at the repository root**. Nested
   files such as `docs/TASKS.md` fell through to the allowed-documentation trees. The
   seam was recorded as `PROTECTED_BASENAME_SCOPE_BUG = CONFIRMED` by
   P2P-MUTATION-SAFETY-CLOSURE-01 and remains an accurate description of `.40`.

2. The P2P-MUTATION-SAFETY-CLOSURE-01 goal proved the intended policy (A–E path
   classification with fail-closed canonical normalization, and the team-state
   `TEAM_SUCCESS XOR MATERIAL_FAILURE` invariant) through an **external** spec-layer
   overlay and a 19-row negative matrix. The overlay was never part of the shipped
   runtime; those semantics existed only in `/tmp/closure_layer` during Closure-01.

3. P2P-MUTATION-SAFETY-INTEGRATION-01 moves those already-proven semantics into the
   canonical shipped runtime (candidate `.41`, version `8.4.7-C-codex.41`, artifact SHA
   `da835f8a48caf4536094ffdd82e3c65baa82da32aa9a7ae73714ee1f2e9c3d2d`,
   source `ec47147bf09bc5d482261838d586599643e637cd`). Changes are confined to
   `bounded_documentation_write.py` (A–E classification, fail-closed normalization,
   authorization binding, second-path guard), `team_intelligence.py` (platform/role
   separation, invariant), and `role_receipt.py` (team block flow-through, six team
   checks), plus mechanical version derivation to `.41`.

4. Platform runtime requirements and role capabilities are distinct by explicit schema
   (`FW02_BASE_PLATFORM_CAPABILITIES`). Platform requirement gaps (for example
   `capability_registry`, `task_state_store`, `decision_trace`,
   `permission_profile_verification`, `freshness_verification`) are infrastructure
   states, **not** role capability gaps. The invariant
   `PLATFORM_REQUIREMENT_GAP != ROLE_CAPABILITY_GAP` holds at the canonical decision
   object.

5. A mutation-ready canonical team object never carries a material `failure_class`.
   `TEAM_SUCCESS XOR MATERIAL_FAILURE` is enforced on the raw canonical `TeamDecision`
   object by `build_team_decision` and independently re-verified by the whole-claim
   verifier through six team checks; any material failure sets verifier
   `overall = false`.

6. The second unauthorized path is blocked **before any write primitive invocation**:
   the canonical Owner authorization binds `authorization_id, goal_id, task_id,
   capability_id, role_id, mutation_class, allowed_relative_path, max_changed_files,
   permission, rollback_requirement` into an authorization binding digest; a dispatch
   whose contract does not match that digest is rejected with
   `OWNER_AUTHORIZATION_BINDING_INVALID` at the execute gate, before bytes are written.
   `SECOND_PATH_PREWRITE_BLOCK = VERIFIED`: zero bytes written to the unauthorized
   path, zero changed files contributed, `UNAUTHORIZED_CHANGED_SURFACE = 0`.

### Non-rewrite commitments

- Pilot-02 history (`CONTROLLED_NON_PRODUCTION_DOCUMENTATION_MUTATION = VERIFIED`,
  `CANONICAL_MUTATION_AUTHORITY_CHAIN = VERIFIED_ON_GAME_TRUYEN_ISOLATED_CLONE`,
  `ROLLBACK_RECOVERY = VERIFIED`) is preserved unchanged.
- Closure-01 findings are preserved unchanged; the closure overlay remains an
  independent proof artifact and is no longer required, because the same semantics
  now ship in the candidate runtime.
- `.40` remains immutable and unchanged.
