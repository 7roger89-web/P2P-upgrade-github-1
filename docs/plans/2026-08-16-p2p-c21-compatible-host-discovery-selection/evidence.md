# Evidence — P2P-C21

## E0 Recovery

`E0-P0A-SRC1` xác nhận `HostCapabilityProfile` của C20 giữ nguyên capability states `SUPPORTED`, `UNSUPPORTED`, `UNKNOWN` cùng môi trường và metadata provider/model trung tính. `E0-P0A-SRC2` xác nhận `PortableExecutionRequest` đã có required capabilities, permission needs/grants, context refs, verification expectations, identity requirement và expected environment. `E0-P0A-SRC3` xác nhận `evaluate_host_preflight` là hard-gate authority cho một profile. `E0-P0A-SRC4` xác nhận selector C20 cũ chỉ xử lý một host hoặc trả về nhiều-host chưa phân giải, nên thiếu policy chọn host.

`E0-P0A-INT1` ghi nhận C18/C19 đã xuất ra các yêu cầu trừu tượng trong portable request seam; `E0-P0A-DT1` ghi nhận Decision Trace hiện hữu là authority cho structured reason records. `E0-P0A-GAP1`, `E0-P0A-GAP2` và `E0-P0A-GAP3` lần lượt xác định discovery provenance/freshness, availability states và minimum-sufficient selection là các khoảng trống trước C21.

## E1 Implementation

`E1-P1-C21-SOURCE` xác nhận module `.p2p/system/p2p_capabilities/host_selection.py` bổ sung `HostRequirementProfile`, `HostDiscoveryRecord`, `HostCandidate`, `HostSelectionDecision`, `HostSelector`, discovery filtering, availability freshness, deterministic hard gates, stable tie-break, portable handoff và safe reselection mà không tạo executor, router provider/model, launcher, daemon hoặc remote bridge.

`E1-P1-C21-PACKAGE-SEAM` xác nhận package runtime manifest đã đưa `host_executor.py` và `host_selection.py` vào foundation runtime. Public exports C21 được nối vào `p2p_capabilities/__init__.py`.

## E2 Validation

`E2-P2-C21-HS1-HS30` là focused suite 30/30 PASS, bao phủ exact host, excess capability, missing/unknown capability, permission safety, local/cloud authority, identity, current host, handoff, tie-break, no-compatible-host, stale/unknown availability, non-authoritative cost, reselection, context, abstract reasoning, secret boundary, future host, Manus-like/Codex-like fixtures, parallel cap, project binding, owner local-only policy và beginner path.

`E2-P2-C20-C21-INTEGRATION` là C20 compatibility suite plus C21 suite, 56/56 PASS. `E2-P2-DEVELOPMENT-CONTROL` là governance-focused suite 21/21 PASS sau khi validator hỗ trợ C21 và các historical fixtures được cập nhật đúng. `E2-P2-FULL-REGRESSION-330` là full unittest discovery 330/330 PASS trong 163.657 giây sau toàn bộ thay đổi cuối.

`E2-P2-GOVERNANCE` xác nhận `python scripts/p2p_development_control.py validate` PASS; C08 vẫn DEFERRED, C09 vẫn BLOCKED/EVENT_EVIDENCE_UNAVAILABLE, canonical denominator vẫn 8 và quorum vẫn 8/8. `E2-P2-DOCTOR` xác nhận doctor trên package extracted PASS với role portable và toàn bộ filesystem/runtime/source/package checks PASS.

## E3 Package and lineage

`E3-P3-C21-PACKAGE` xác nhận candidate v2 build PASS với embedded version `8.4.7-C-codex.21`, artifact size `2,547,618` bytes, file count `415`, checksum count `416`, SHA-256 `bcf5589d91bbfb18fbc572ff40f685b4d7cb6ab3819449148648801144896730`, official baseline `8.4.7-C-codex.19` và official baseline SHA-256 `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.

`E3-P3-C21-PACKAGE-VERIFY` xác nhận candidate v2 được giải nén vào `.tmp/c21-package-verify-v2` và verify độc lập PASS. Candidate v1 vẫn là artifact lịch sử bất biến; candidate v2 là artifact C21 được durable governance bind tới.

## E4 Graph and lifecycle

`E4-P4-ANALYZE` xác nhận Anvien refresh sau thay đổi: scanned 421 files, parsed_code 50, failed 0, graph nodes 17,334, relationships 20,137. `E4-P4-DETECT-CHANGES-BLOCKER` ghi nhận `anvien detect-changes --repo p2p-c19 --scope all` không thể hoàn tất vì source directory không có `.git`; công cụ trả `Git diff failed: exit status 129`. Vì vậy không tạo được commit hash hoặc clean Git worktree evidence.

## Supervisor basis

`E5-P4-SUPERVISOR` kiểm tra authority reuse C20, no-second-router, deterministic gates, UNKNOWN capability/availability, permission/environment safety, minimum sufficient selection, tie-break, no automatic routing, no Manus certification, package/lineage and regression evidence. Technical claim is supported; repository lifecycle commit evidence remains unavailable because the supplied directory is a release/source package without `.git`.
