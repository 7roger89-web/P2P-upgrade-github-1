# 02 — RULE REGISTRY SEED

REGISTRY_VERSION: `0.1`
STATUS: `PROVISIONAL`

Không entry mệnh lý nào dưới đây được hiểu là `ACTIVE_VERIFIED` chỉ vì repo upstream có triển khai nó.

## Project rules

### OPS-CM-001 — Freeze construction before reasoning

- `STATUS`: ACTIVE_PROJECT
- `RULE`: Lập quẻ/lập bàn/vận hạn phải freeze trước khi luận.
- `CONFLICTS_WITH`: sửa chart/quẻ sau khi thấy outcome để tăng độ khớp.

### OPS-CM-002 — Method lock

- `STATUS`: ACTIVE_PROJECT
- `RULE`: mỗi run khóa một METHOD_LANE; không vay rule ngoài lane nếu không có explicit bridge rule.

### OPS-CM-003 — Provenance chain

- `STATUS`: ACTIVE_PROJECT
- `RULE`: mọi claim phải tái dựng được `INPUT → RULE → SOURCE → APPLICATION → CLAIM`.

### OPS-CM-004 — Prediction lock

- `STATUS`: ACTIVE_PROJECT
- `RULE`: case test phải freeze prediction trước outcome; sau outcome không sửa prediction cũ.

### OPS-CM-005 — Insufficient evidence

- `STATUS`: ACTIVE_PROJECT
- `RULE`: thiếu source/application hợp lệ → `UNSUPPORTED=INSUFFICIENT_SOURCE_SUPPORT` → `DO_NOT_CLAIM`.

### OPS-CM-006 — Separate calculation from interpretation

- `STATUS`: ACTIVE_PROJECT
- `RULE`: deterministic engine chỉ xuất construction facts/conventions; reasoning layer không được sửa construction để cứu interpretation.
- `ADOPTED_FROM_ARCHITECTURE`: `Johnson-Jia/liuyao-divination` separation of 排盘 vs 解读.

---

## 梅花 candidate rules

### MH-CAND-001 — Structured reading order

- `STATUS`: UPSTREAM_IMPLEMENTED_UNVERIFIED
- `SOURCE`: `Fyrgo8/meihua-divination-skill@d70d73a:SKILL.md`
- `METHOD`: MH-COMMON
- `RULE`: 体用 → 生克 → 旺衰 → 动爻 → 变卦 → 互卦 → 外应 → 错综.
- `NEEDS`: classical/modern-school provenance for each edge in the sequence.

### MH-CAND-002 — External sign as secondary validator

- `STATUS`: UPSTREAM_IMPLEMENTED_UNVERIFIED
- `SOURCE`: `Fyrgo8/meihua-divination-skill@d70d73a:SKILL.md`
- `METHOD`: MH-COMMON
- `RULE`: 外应 không được tự động ghi đè toàn bộ structural reading.
- `PROJECT_NOTE`: nếu user không cung cấp external sign, không được fabricate.

### MH-CG-CAND-001 — 策轨 deterministic calculation

- `STATUS`: UPSTREAM_IMPLEMENTED_UNVERIFIED
- `SOURCE`: `soom-lupulus/plum-cg@509fc43:README.md + code`
- `METHOD`: MH-CEGUI
- `RULE`: engine tính 策数、轨数、元策、元轨 và mapping sang 卦/五行 từ input đã định.
- `DISPUTE`: mapping số 5 có variant; convention phải freeze.
- `NEEDS`: source provenance cho thuật toán, không chỉ unit tests.

### MH-REJECT-001 — Forced binary verdict under weak evidence

- `STATUS`: REJECTED
- `SOURCE`: `Fyrgo8/meihua-divination-skill@d70d73a:SKILL.md`
- `REASON`: xung đột `OPS-CM-005`; dự án không buộc phán có/không khi source/evidence không đủ.

---

## 六爻 candidate rules

### LY-CAND-001 — 用神-centered reasoning

- `STATUS`: UPSTREAM_IMPLEMENTED_UNVERIFIED
- `SOURCE`: `Johnson-Jia/liuyao-divination@1a5a78b:skill/liuyao-divination/SKILL.md`
- `METHOD`: LY-NAJIA
- `RULE`: sau khi freeze 卦盘, chọn 用神 rồi xét 旺衰/世爻/动静空破/化变合墓 trước综合和应期.
- `NEEDS`: provenance tách theo từng rule nhỏ.

### LY-CAND-002 — Mechanical board fields

- `STATUS`: DECLARED_CONVENTION_CANDIDATE
- `SOURCE`: cùng repo trên
- `METHOD`: LY-NAJIA
- `FIELDS`: 主卦、变卦、世应、六亲、纳甲、六神、月建、日辰、空亡、动变.
- `PROJECT_USE`: schema kiểm construction, không phải predictive rule.

### LY-MULTI-001 — Topic isolation for 一卦多断

- `STATUS`: ACTIVE_PROJECT
- `METHOD`: LY-MULTI
- `RULE`: mỗi topic có `TOPIC_ID + USE_GOD_BINDING + ACTIVE_RULE_IDS + CLAIM`; không copy kết luận giữa topic nếu thiếu bridge rule.
- `NOTE`: đây là protocol chống leakage/hindsight, không phải tuyên bố rằng cổ thư dạy đúng format này.

### LY-MULTI-CAND-002 — 变六亲/飞宫/分爻

- `STATUS`: PENDING_SOURCE
- `METHOD`: LY-MULTI
- `RULE`: placeholder cho các kỹ pháp mở rộng một quẻ nhiều việc.
- `NEEDS`: tác giả, edition, chapter/page, preconditions, exceptions và cases.

---

## 紫微 / 飞星 candidate rules

### ZW-CAL-001 — Iztro as calculation candidate

- `STATUS`: DECLARED_CONVENTION_CANDIDATE
- `SOURCE`: `SylarLong/iztro@2c7ef9b`
- `METHOD`: ZW-FEIXING
- `CAPABILITY`: 十二宫, 星曜, 四化, 运限 và cung-to-cung flying transformation queries.
- `LIMIT`: engine capability không chứng minh interpretation correctness.

### ZW-FX-CAND-001 — Palace-stem flying transformation path

- `STATUS`: UPSTREAM_IMPLEMENTED_UNVERIFIED
- `SOURCE`: `Linden-TR/ziwei-doushu-skill@a842dd6:references/sihua.md`; `SylarLong/iztro` API/docs.
- `METHOD`: ZW-FEIXING
- `RULE`: khóa source palace/stem → 四化 star → destination palace; path có thể tiếp tục nếu school đã khóa cho phép.
- `NEEDS`: school-specific source và bảng 四化 provenance.

### ZW-FX-CAND-002 — Self-transformation is distinct from flying to another palace

- `STATUS`: UPSTREAM_IMPLEMENTED_UNVERIFIED
- `SOURCE`: `SylarLong/iztro` API/docs + `Linden-TR/.../sihua.md`
- `METHOD`: ZW-FEIXING
- `RULE`: 自化 phải được ghi thành relation type riêng, không đồng nhất với飞入他宫.
- `NEEDS`: definition theo từng school.

### ZW-HELUO-CAND-001 — 一六/二七/三八/四九 pairing

- `STATUS`: PENDING_SOURCE
- `SOURCE`: `ZhangZangQian/xu-quanren@7b8364b:work.md` (modern upstream claim)
- `METHOD`: ZW-XQR; chưa được gán cho ZW-HELUO-FWR.
- `RULE`: repo ghi 河洛理数 pairing 一六、二七、三八、四九、五十.
- `NEEDS`: primary attribution và cách application thực tế.

### ZW-XQR-CAND-001 — 宫优先于星

- `STATUS`: UPSTREAM_IMPLEMENTED_UNVERIFIED
- `SOURCE`: `ZhangZangQian/xu-quanren@7b8364b:work.md`
- `METHOD`: ZW-XQR
- `RULE`: repo đặt宫职 trước象/星 trong reading workflow.
- `NEEDS`: xác minh attribution tới 许铨仁 và original context.

### ZW-XQR-CAND-002 — 生年为体 / 飞宫为用 hierarchy

- `STATUS`: UPSTREAM_IMPLEMENTED_UNVERIFIED
- `SOURCE`: cùng repo trên
- `METHOD`: ZW-XQR
- `RULE`: repo ưu tiên 生年四化 trước飞宫 và yêu cầu层次由用归体.
- `NEEDS`: primary source + exceptions.

### ZW-REJECT-001 — Unsourced numeric “energy percentage”

- `STATUS`: REJECTED_PENDING_EVIDENCE
- `SOURCE`: `Linden-TR/ziwei-doushu-skill@a842dd6:references/sihua.md`
- `CLAIM`: repo nêu chênh lệch khoảng 30% trong một mô tả tự hóa.
- `REASON`: không thấy calibration/source trong evidence pass hiện tại; không dùng con số này để luận.

---

## Promotion rule

Candidate chỉ được nâng thành `ACTIVE_VERIFIED` theo chuỗi:

```text
PENDING/UPSTREAM_CANDIDATE
→ locate source
→ verify edition/layer
→ capture context
→ extract atomic rule
→ define preconditions/exceptions/conflicts
→ implement application logic without adding meaning
→ review
→ blind-case evaluation
→ ACTIVE_VERIFIED
```

Không sửa một rule chỉ để cứu một case.
