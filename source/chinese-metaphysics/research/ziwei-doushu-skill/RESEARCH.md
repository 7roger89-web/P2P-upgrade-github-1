# ziwei-doushu-skill — Independent Research Dossier

UPSTREAM: `Linden-TR/ziwei-doushu-skill`
PINNED_SHA: `a842dd65dabdc4ce42ec9688b88ae876858a9977`
STATUS: `INDEPENDENT_RESEARCH`

## Repo scope

Repo tự mô tả là skill 紫微斗数 đa phái: 中州 làm chính, kết hợp 三合、飞星、钦天四化、河洛; dùng `@mingai/mcp` cho phần công cụ.

Dossier này nghiên cứu **chính repo đó** và cách nó tích hợp các phái. Không dùng kết luận của dossier này như đại diện cho bất kỳ phái riêng nào nếu chưa có provenance.

## Candidate value

- Có flow `命盘骨架 → 星系 → 逐宫 → 四化追踪 → 大限 → 格局 → 徵验`.
- `references/sihua.md` chứa nhiều rule 飞星/四化 để bóc và kiểm nguồn.
- Có `gongwei.md`, `pattern-library.md`, `zhengyan.md` cho audit theo module.

## Local candidate rules

`ZDS-001` — Mỗi claim phải ghi nó được repo gắn với 中州/三合/飞星/钦天/河洛 hay synthesis của tác giả repo.

`ZDS-002` — Multi-school integration là đặc tính của repo, không phải bằng chứng các phái vốn đồng nhất.

`ZDS-003` — Các chain như 禄转禄、忌转忌 phải có source và điều kiện dừng rõ trước khi dùng.

`ZDS-004` — Con số định lượng kiểu “khoảng 30% năng lượng” không có calibration/source thì `REJECTED_PENDING_EVIDENCE`.

## What to audit

1. `references/sihua.md` từng rule một.
2. `references/gongwei.md` và 河洛 claims.
3. `references/zhengyan.md`: provenance của “empirical signals”.
4. `pattern-library.md`: source và break/rescue logic.
5. Contract thật với `@mingai/mcp` để biết phần nào do tool tính.

## Validation

Mỗi rule giữ tag `DECLARED_SCHOOL`, `SOURCE_LOCATOR`, `REPO_SYNTHESIS`, `CONFLICTS`. Không có locator thì không nâng authority.

## Next bounded task

Lập provenance matrix cho `references/sihua.md`; không nghiên cứu repo Tử Vi khác trong dossier này.
