# 01 — ANALYSIS PROTOCOL

STATUS: `ACTIVE_PROJECT_V0.1`
PURPOSE: luận giải có provenance, khóa phương pháp, tách mechanical calculation khỏi reasoning, và kiểm nghiệm outcome-blind.

## 1. Năm điều kiện của “luận đúng”

1. **Construction correctness** — quẻ/bàn/vận hạn phải được lập đúng theo convention đã khai báo.
2. **Method consistency** — mỗi claim thuộc một lane/phái xác định; không vá rule từ hệ khác khi thiếu căn cứ.
3. **Source provenance** — biết rule đến từ repo, nguyên thư, tác giả hay lớp chú giải nào.
4. **Reproducibility** — người khác có thể tái dựng `INPUT → RULE → APPLICATION → CLAIM`.
5. **Epistemic honesty** — thiếu căn cứ thì ghi thiếu căn cứ; không buộc model phải phán cho đủ câu.

## 2. Pipeline bắt buộc

```text
GATE 0 INPUT LOCK
  → GATE 1 CONSTRUCTION FREEZE
  → GATE 2 METHOD LOCK
  → GATE 3 RULE SELECTION
  → GATE 4 APPLICATION + CLAIM CARDS
  → GATE 5 PREDICTION LOCK
  → OUTCOME REVEAL (nếu là case test)
  → SCORE + FAILURE ANALYSIS
```

### GATE 0 — INPUT LOCK

Ghi đúng dữ liệu người dùng cung cấp, độ chính xác và phần thiếu. Không sửa input sau khi thấy outcome để cứu lời đoán.

### GATE 1 — CONSTRUCTION FREEZE

Engine/deterministic code chỉ làm phần cơ học. Output phải có `CONSTRUCTION_VERSION`, `ENGINE`, `PINNED_SHA_OR_VERSION`, `CONVENTIONS`, `UNCERTAINTIES`.

Nếu hai convention hợp lý cho kết quả khác nhau, tạo hai branches trước outcome. Không chọn branch theo đời thật đã biết.

### GATE 2 — METHOD LOCK

Mỗi lần luận chỉ chọn một lane chính:

- `MH-COMMON`: 梅花易数 thông dụng.
- `MH-CEGUI`: 皇极梅花 / 策轨.
- `LY-NAJIA`: 六爻纳甲.
- `LY-MULTI`: 一卦多断, nhưng mỗi topic là một sub-analysis có binding riêng.
- `ZW-FEIXING`: 紫微斗数飞星.
- `ZW-HELUO-FWR`: 河洛 / 方外人, chỉ kích hoạt khi primary/authorized sources đủ.
- `ZW-XQR`: 许铨仁/飞宫 reconstruction, lane riêng.

Không dùng “综合紫微” hoặc “综合易学” như METHOD nếu không có rule hợp nhất đã xác minh.

### GATE 3 — RULE SELECTION

Chỉ dùng rule `ACTIVE_VERIFIED`, `ACTIVE_PROJECT`, hoặc rule candidate khi output ghi rõ `UNVERIFIED` và mục đích là nghiên cứu chứ không phải authority.

Bắt buộc khai báo:

```text
ALLOWED_RULE_IDS:
EXCLUDED_RULE_IDS:
SCHOOL_OR_LANE:
SOURCE_LAYER_LIMIT:
```

### GATE 4 — CLAIM CARD

Mỗi claim phải có:

```text
CLAIM_ID:
CLAIM:
METHOD:
RULE_ID:
SOURCE:
SOURCE_LAYER:
TEXTUAL_BASIS:
APPLICATION:
INFERENCE:
ALTERNATIVE_INTERPRETATIONS:
TEXTUAL_CONFIDENCE:
INTERPRETIVE_CONFIDENCE:
PREDICTIVE_EVIDENCE:
UNSUPPORTED:
FALSIFICATION_CRITERION:
```

`HIGH_TEXTUAL` không đồng nghĩa `HIGH_PREDICTIVE`.

Nếu thiếu source hoặc application hợp lệ:

```text
UNSUPPORTED = INSUFFICIENT_SOURCE_SUPPORT
ACTION = DO_NOT_CLAIM
```

### GATE 5 — PREDICTION LOCK

Trong case test, lưu prediction trước khi mở outcome. Sau outcome chỉ được chấm và phân tích lỗi, không sửa prediction cũ.

---

# 3. Lane MH-COMMON — 梅花易数

## Mechanical freeze

Ghi:
- cách 起卦;
- input raw;
- 本卦;
- 动爻;
- 互卦;
- 变卦;
- 错卦/综卦 nếu lane dùng;
- convention 体/用;
- time context nếu dùng 旺衰/卦气;
- external signs nếu người dùng thực sự cung cấp.

Không tự bịa 外应. Không coi “không được cung cấp” là “không có”.

## Reading sequence candidate

Repo `meihua-divination-skill` triển khai chuỗi:

```text
体用 → 生克 → 旺衰 → 动爻 → 变卦 → 互卦 → 外应 → 错综
```

Trong dự án này chuỗi trên chỉ là `UPSTREAM_IMPLEMENTED_UNVERIFIED` cho tới khi từng rule được đối chiếu nguồn.

Nguyên tắc dự án bổ sung:
- không lấy tên quẻ như một nhãn “cát/hung” duy nhất;
- tách bản nghĩa của quẻ, tượng của thượng/hạ quái, và application vào câu hỏi;
- 外应 chỉ được dùng khi có input thật và phải ghi trọng số/role của nó;
- không ép kết luận nhị phân nếu evidence không đủ.

## MH-CEGUI isolation

`plum-cg` tính 策数/轨数 từ 主卦 + 动爻 và có xử lý variant số 5. Đây là **calculation lane riêng**. Không lén đưa 策轨 vào MH-COMMON nếu METHOD_LOCK không cho phép.

---

# 4. Lane LY-NAJIA — 六爻纳甲

## Mechanical layer

Candidate engine phải freeze tối thiểu:
- 主卦/变卦;
- 世/应;
- 六亲;
- 纳甲;
- 六神 nếu method dùng;
- 月建/日辰;
- 旬空;
- 动爻/变爻;
- các trạng thái deterministic mà engine tuyên bố tính.

Repo `liuyao-divination` có kiến trúc rất đáng giữ: **先排准卦盘，再做解读**. Dự án nhận kiến trúc separation này như `ACTIVE_PROJECT`, nhưng các mệnh lý rule bên trong vẫn phải audit provenance.

## Reasoning sequence candidate

```text
取用神
→ 用神旺衰
→ 世爻状态
→ 动静 / 空破
→ 化变
→ 合墓
→ 综合定性
→ 应期
```

Không cho một keyword đơn lẻ như 空、破、墓 hoặc 暗动 tự động tạo event claim.

---

# 5. Lane LY-MULTI — 一卦多断

Một quẻ nhiều việc không có nghĩa là một kết luận tổng quát được copy sang mọi chủ đề.

Mỗi topic phải có record riêng:

```text
TOPIC_ID:
QUESTION:
OBJECT_OF_INQUIRY:
USE_GOD_BINDING:
PALACE_OR_LINE_BINDING_IF_METHOD_USES:
ACTIVE_RULE_IDS:
APPLICATION:
CLAIM:
CONFIDENCE:
```

Sau khi `TOPIC_1` đã luận, không được dùng outcome hoặc lời giải của `TOPIC_1` làm evidence cho `TOPIC_2` nếu method không có bridge rule.

Kỹ pháp như 变六亲、飞宫、分爻 phải nằm ở rule riêng với source riêng. Chưa có provenance thì giữ `PENDING_SOURCE`.

---

# 6. Lane ZW-FEIXING — 紫微斗数飞星

## Mechanical freeze

Ghi:
- birth input + timezone/convention;
- 十二宫;
- 星曜 placements;
- palace stems/branches;
- 生年四化 theo **bảng của school đã khóa**;
- 大限/流年/流月... nếu dùng;
- 宫干飞化 path;
- 自化 nếu engine hỗ trợ và định nghĩa đã khóa.

`iztro` phù hợp làm candidate calculation layer vì nó tách chart/运限/四化/宫位飞化 thành dữ liệu truy vấn được. Việc engine trả đúng data không tự động chứng minh interpretation.

## Reasoning order v0.1

```text
命盘骨架
→ METHOD/SCHOOL LOCK
→ 生年四化
→ topic palace(s)
→ 宫干飞化 path
→ self-transformation layer (nếu school dùng)
→ 大限
→ 流年
→ claim cards
```

Mỗi path phải ghi rõ source palace, stem, transformed star, destination palace và layer thời gian.

Không trộn bảng 四化 khác phái trong cùng một run.

---

# 7. Lane ZW-HELUO-FWR — 河洛 / 方外人

Lane này hiện **không được active để phán authority**.

Lý do: hiện mới có forum/discovery evidence và các repo hiện đại nhắc 河洛. Chưa có primary/authorized corpus đủ để tái dựng rule của 方外人 một cách có provenance.

Các khái niệm như 一六共宗、同步断诀、气数位、体用/宫位关系 phải ở `PENDING_SOURCE` cho tới khi có edition/scan/source layer rõ.

Không dùng `xu-quanren` để lấp khoảng trống rồi gọi đó là 方外人法.

---

# 8. Lane ZW-XQR — 许铨仁 / 飞宫 reconstruction

`xu-quanren/work.md` đưa ra một hệ thống riêng: 宫优先于星, 生年优先于飞宫, 体优先于用, 飞宫八大理则, 宫位二分法 và 河洛配对.

Dự án giữ lane này **riêng biệt** vì đây là modern-system reconstruction. Từng claim phải xác minh nó là lời/tác phẩm của 许铨仁, phần diễn giải của repo, hay synthesis của tác giả repo.

Không nâng các câu kiểu “必见凶象” thành fact/predictive truth nếu chưa qua blind evaluation.

---

# 9. Conflict policy

1. `meihua-divination-skill` yêu cầu chốt yes/no ngay cả khi evidence yếu. **Project policy REJECT** yêu cầu này. Evidence yếu được phép `UNRESOLVED/DO_NOT_CLAIM`.
2. `ziwei-doushu-skill` tự mô tả multi-school integration. Dự án chỉ dùng nó để discovery. Khi luận thật, school phải lock; không tự blend 中州 + 三合 + 飞星 + 钦天 + 河洛.
3. Mọi con số định lượng kiểu “30% năng lượng”, “★★★★★ strength” phải có source/calibration. Nếu không, không dùng như rule.
4. Rule cổ/modern có cùng tên nhưng khác định nghĩa phải có ID khác nhau.

# 10. Sensitive claims

Không dùng các hệ này như chẩn đoán y khoa, tư vấn pháp lý/tài chính, hoặc bằng chứng chắc chắn cho chết, ung thư, tai nạn, ngoại tình, phá sản hay hành vi của người thứ ba.

Nếu nguồn truyền thống có mệnh đề loại này, ghi `TRADITIONAL_DOCTRINE`, source và uncertainty; không nâng thành fact cá nhân.
