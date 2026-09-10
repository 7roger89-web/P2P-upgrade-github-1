# 00 — CHINESE METAPHYSICS SOURCE MAP

STATUS: `PROVISIONAL_UPSTREAM_CONSTRAINED`
SCOPE: 易经 / 梅花易数 / 皇极梅花策轨 / 六爻纳甲 / 一卦多断 / 紫微斗数 / 飞星 / 河洛 / 四化

## 1. Mục tiêu

File này xác định **nguồn nào dùng để làm gì**. Việc một repo có code, README đẹp hoặc nhiều sao không làm cho nội dung mệnh lý của nó tự động trở thành cổ pháp đã được xác minh.

Ba loại giá trị phải tách riêng:

1. `CONSTRUCTION_VALIDITY`: engine có lập quẻ/lập bàn đúng theo convention đã khai báo không.
2. `METHOD_FIDELITY`: chuỗi luận có trung thành với đúng phương pháp/trường phái đã khóa không.
3. `PREDICTIVE_VALIDITY`: kết luận có dự báo được outcome chưa biết hay không.

Chứng minh được 1 không tự động chứng minh 2 hoặc 3.

## 2. Tầng nguồn

- `PROJECT_PROTOCOL`: quy tắc do dự án đặt để chống hindsight/hallucination. Không phải cổ pháp.
- `UPSTREAM_CODE`: hành vi thực tế của code tại pinned commit.
- `UPSTREAM_METHOD_CLAIM`: README/SKILL/reference do tác giả repo mô tả. Chưa phải authority cổ điển.
- `MODERN_SCHOOL_PRIMARY`: tài liệu do chính tác giả/đại diện trường phái hiện đại công bố, cần xác minh edition/provenance.
- `CLASSICAL_PRIMARY`: nguyên thư/bản scan/bản chép đã đối chiếu lớp văn bản.
- `ACADEMIC_SECONDARY`: nghiên cứu học thuật dùng để định lịch sử, attribution, dị bản, tranh luận.
- `FORUM_DISCOVERY`: diễn đàn/blog/video chỉ dùng tìm đầu mối hoặc tranh luận; không làm authority cuối.

## 3. Trạng thái rule

- `ACTIVE_PROJECT`: quy tắc vận hành của corpus.
- `DECLARED_CONVENTION`: convention tính toán được chọn và khóa.
- `UPSTREAM_IMPLEMENTED_UNVERIFIED`: repo thực sự đang triển khai rule, nhưng chưa xác minh rule đó từ nguồn gốc được tuyên bố.
- `PENDING_SOURCE`: đã thấy mệnh đề, chưa đủ provenance để dùng như rule authority.
- `ACTIVE_VERIFIED`: có evidence đủ mạnh, precondition/exception/conflict rõ và đã review.
- `DISPUTED`: có dị bản hoặc trường phái đối lập.
- `REJECTED`: attribution sai, không được nguồn hỗ trợ, hoặc xung đột với policy dự án.

## 4. Upstream map v0.1

| Upstream | Vai trò hiện tại | Source layer | Trạng thái sử dụng |
|---|---|---|---|
| `upstreams/plum-app` | App ghi case; ghép 梅花 + 策轨 + 纳甲 | UPSTREAM_CODE / METHOD_CLAIM | reference only; không mặc định các hệ tương thích |
| `upstreams/plum-cg` | Engine deterministic cho 策数/轨数 | UPSTREAM_CODE | candidate calculation engine |
| `upstreams/meihua-yishu` | casting + 体用 + 主/互/变 + 错/综 | UPSTREAM_CODE / METHOD_CLAIM | research reference |
| `upstreams/meihua-divination-skill` | workflow luận Mai Hoa 9 bước | UPSTREAM_METHOD_CLAIM | workflow candidate; một số policy bị loại |
| `upstreams/yinyo-liuyao` | rule/case corpus Lục Hào | UPSTREAM_METHOD_CLAIM | cần audit rule provenance |
| `upstreams/liuyao-divination` | engine + workflow 纳甲/用神/旺衰 | UPSTREAM_CODE / METHOD_CLAIM | ưu tiên nghiên cứu separation mechanical/reasoning |
| `upstreams/iztro` | engine lập Tử Vi, vận hạn, 四化, 飞化 | UPSTREAM_CODE | candidate calculation layer |
| `upstreams/ziwei-doushu-skill` | Zhongzhou + 三合 + 飞星 + 钦天 + 河洛 | UPSTREAM_METHOD_CLAIM | discovery/reference; không được trộn school mặc định |
| `upstreams/ziwei-wuandyA` | Tử Vi app/reference | UPSTREAM_CODE / METHOD_CLAIM | audit later |
| `upstreams/ziwei-chart` | chart/application reference | UPSTREAM_CODE | audit later |
| `upstreams/xu-quanren` | modern 飞宫/四化/河洛 reconstruction | UPSTREAM_METHOD_CLAIM | lane riêng; không đồng nhất với 方外人河洛 |

## 5. Source gaps quan trọng

### Mai Hoa / 易

Cần tìm và đối chiếu nguyên thư/dị bản cho:
- 《梅花易数》;
- 《皇极梅花》/策轨法 attribution và edition;
- nguồn của các quy tắc 体用、卦气、外应、应期.

### 六爻 / 一卦多断

Cần tách:
- 《增删卜易》;
- 《卜筮正宗》;
- 《易隐》;
- các giáo trình hiện đại về 一卦多断、变六亲、飞宫、分爻.

Không mặc định “一卦多断” là một kỹ pháp cổ thống nhất qua mọi thế hệ.

### 紫微飞星 / 河洛

Cần tìm nguồn primary/authorized cho:
- 方外人（曾国雄）;
- 河洛紫微斗数;
- 同步断诀;
- 宫干四化飞渡;
- các bảng 四化 theo từng phái;
- 自化 / 向心 / 离心 và cách định nghĩa theo từng hệ;
- 大限/流年 chồng tầng.

`xu-quanren` là một lane hiện đại riêng. Không dùng nó để chứng minh “方外人 nói như vậy”.

## 6. Nguyên tắc provenance

Mỗi evidence sau này phải có tối thiểu:

```text
EVIDENCE_ID:
SOURCE_ID:
TITLE:
AUTHOR_OR_ATTRIBUTION:
EDITION:
CHAPTER_OR_LOCATOR:
SOURCE_LAYER:
SHORT_TEXTUAL_BASIS:
CONTEXT:
COLLATION_STATUS:
SUPPORTED_RULE_IDS:
LIMITATIONS:
```

Không có source/locator hợp lệ thì rule không được lên `ACTIVE_VERIFIED`.
