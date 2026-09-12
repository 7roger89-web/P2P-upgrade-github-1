# GENG_SIHUA_PROVENANCE_002


**TASK_ID:** `ZIWEI_GENG_SIHUA_PROVENANCE_002`  
**DOMAIN:** `ZIWEI_DOUSHU`  
**SCOPE:** source-only provenance; one heavenly stem (`庚`); no engine changes; no interpretation; no prediction.  
**RESEARCH_VERDICT:** `PASS_WITH_OPEN_PROVENANCE_CONFLICT`  
**REPO_WRITE_STATUS:** `BLOCKED_BY_GITHUB_CONNECTOR_DISABLED`

## 1. Bounded conclusion

The prior binary `A vs B` model is insufficient. At least five distinct 庚 Tứ Hóa rows are attested in the evidence set:

| Variant | Short form | 化禄 | 化权 | 化科 | 化忌 |
|---|---|---|---|---|---|
| A | 陽武陰同 | 太陽 | 武曲 | 太陰 | 天同 |
| B | 陽武同相 | 太陽 | 武曲 | 天同 | 天相 |
| C | 陽武同陰 | 太陽 | 武曲 | 天同 | 太陰 |
| D | 陽武府同 | 太陽 | 武曲 | 天府 | 天同 |
| E | 陽武府相 | 太陽 | 武曲 | 天府 | 天相 |

These are **confirmed as observed/reported variants**, not confirmed as equally old, equally authoritative, or mutually exclusive historical school standards.

Safe research model:

```text
CONVENTION_ID
+ SOURCE/EDITION
+ ATTRIBUTION
+ SOURCE_QUALITY
+ CONFLICT_STATUS
```

not:

```text
SCHOOL_NAME -> ONE UNIVERSAL TABLE
```

## 2. Source-quality ladder

- `P0_PRIMARY_EDITION_SCAN` — identifiable historical edition scan/facsimile; claim must be checked on the actual relevant page.
- `P1_AUTHOR_OR_AUTHORIZED_SOURCE` — author publication, recognized authorized edition/publisher, or institutional archive with reliable bibliographic identity.
- `P2_ACADEMIC_SECONDARY` — academic paper/scholarly publication explicitly reporting a table or school attribution.
- `P3_SCHOOL_OR_SPECIALIST_SECONDARY` — traceable specialist/school publication, not primary.
- `P4_MODERN_WEB_SUMMARY` — modern blog/wiki/app/repo summary.
- `P5_UNVERIFIED_REPOST` — unattributed, user-uploaded, provenance-poor or unauthorized copy/repost.

Source quality and content confidence are separate. A P5 scan-like copy may strongly suggest what a book page says, but it does not become P1 merely because the page looks authentic.

## 3. Academic secondary evidence

### 3.1 Institutional identity

Internal PDF title: `命理統計學方法論`  
Institutional bibliographic title: `命理學量化研究之模型與方法論`  
Authors: 林聖軒 (Sheng-Hsuan Lin), 孫保羅 (BaoLuo Sun)  
Context: 第七屆《中華傳統術數文化學術研討會》, Taipei, 2018-03-31; institutional record labels it an oral report / conference paper.

Institutional records:
- https://stat.nycu.edu.tw/zh_tw/research/con_paper/%E5%91%BD%E7%90%86%E5%AD%B8%E9%87%8F%E5%8C%96%E7%A0%94%E7%A9%B6%E4%B9%8B%E6%A8%A1%E5%9E%8B%E8%88%87%E6%96%B9%E6%B3%95%E8%AB%96-58660032
- https://shenghsuanlin.web.nycu.edu.tw/2020/02/27/632/

**Locator:** official PDF page 6/12, §參、一「預測因子的定義與測量」, paragraph beginning `在紫微斗數中雖有不同派別…`.

The paper reports:
- `占驗派` 庚 = **B** `陽武同相`.
- `中州派` 庚 = **A** `陽武陰同`.

**Source quality:** `P2_ACADEMIC_SECONDARY`  
**Direct or reported:** `REPORTED_SCHOOL_ATTRIBUTION`  
**Evidence status:** `CONFIRMED_ACADEMIC_REPORT`

It does **not** perform primary textual-lineage arbitration for those school tables.

## 4. 王亭之 evidence

### 4.1 Bibliographic identity

`王亭之談星：紫微斗數星曜總談` is bibliographically identifiable:
- 王亭之
- 博益出版集團
- cataloged 1991 edition
- ISBN 9621703867 / 9789621703866.

`斗數零談` is also identifiable as a 王亭之 publication and part of the `斗數四書`.

Useful bibliographic records:
- https://books.google.com/books/about/%E7%8E%8B%E4%BA%AD%E4%B9%8B%E8%AB%87%E6%98%9F.html?id=TANf661r8hoC
- https://www.chinyuan.com.tw/all_book/more?id=475

### 4.2 Exact four-transformations discussion located

The strongest content-specific text found is an **unauthorized/user-uploaded copy** of `斗數零談`, around printed pages **201–206**, under sections including `挾火而化之迷` and `關於四化的討論`.

Because the host is unauthorized, classify the exact text source as `P5_UNVERIFIED_REPOST`.

The apparent book text reports:
- 王亭之's `中州派` = **D** `陽武府同`.
- `依《全書》` = **C** `陽武同陰`.
- `依《全集》` = **A** `陽武陰同`.
- a Qing-era `鐵板神數` report = **B** `陽武同相`, followed by an argument that `相` itself may be a copying/printing error for `陰`.
- modern reposts of related 王亭之 prose also report teacher-mentioned **E** `陽武府相` as a possibility kept under doubt.

Current safe status:

```text
WANG_TINGZHI_ATTRIBUTION_STATUS =
D (陽武府同) reported as Wang-Tingzhi Zhongzhou convention;
exact text copy quality = P5;
authorized edition page verification = OPEN.
```

For E:

```text
E = REPORTED_WANG_TEACHER_ALTERNATIVE
Wang-specific source quality = P4/P5
```

## 5. 《紫微斗數全書》 provenance

### 5.1 P0 archival target located

Japan National Archives Digital Archive identifies:

`新鋟希夷陳先生紫微斗數全書`

- call number `子060-0001`
- old collection `紅葉山文庫`
- 陳搏（宋） / 潘希尹（明）
- Ming printed edition
- 2 volumes
- public image viewer.

Catalog/viewer:
- https://www.digital.archives.go.jp/img/1078787
- https://www.digital.archives.go.jp/img/4468520

This is a `P0_PRIMARY_EDITION_SCAN` **target**, but the exact `安祿權科忌` image page was not successfully inspected in this slice because the image viewer was not accessible to the current web fetcher.

### 5.2 Academic bibliographic corroboration

陳昭吟, `道經中署名羅洪先之著作考辨`, 《成大中文學報》75 (2021), pp.33–74, identifies:
- `新鋟希夷陳先生紫微斗數全書`, 葆和堂葉梓行, Japan National Archives.
- `新刊希夷陳先生紫微斗數全集`, 金陵益軒唐謙梓, Toyo Bunko.

Source:
- https://www.airitilibrary.com/Article/Detail/P20170720001-202112-202202230007-202202230007-33-74

**Quality:** `P2_ACADEMIC_SECONDARY` for edition history/bibliography.

### 5.3 Authorized facsimile publisher comparison

心一堂's 2017 facsimile:
`紫微斗數全書（明末清初木刻真本）`, ISBN `9789888266944`

Publisher:
- https://publish.sunyata.hk/product/973.html

The publisher says its edition combines two 虛白廬 late-Ming/early-Qing 文光堂 woodblock exemplars (`敦化堂刊本`, `繼述堂刊本`). Its explicit comparison reports:
- early/good woodblock: **C** `庚日武同陰`;
- Republican lithographic `《全書》`: **A** `庚日武陰同`, described as a textual error.

**Quality:** `P1_AUTHOR_OR_AUTHORIZED_SOURCE` for the publisher's edition-comparison claim.  
**Limitation:** the exact facsimile row page itself was not directly inspected here.

### 5.4 Modern transcription conflict

Modern online transcriptions disagree:
- Wikisource `紫微斗數全書/卷二` currently gives **A**.
- 識典古籍, despite presenting a `新鋟希夷陳先生紫微斗數全書` transcription, currently gives **B**.

These are conflict indicators, not primary-edition proof. Classify as `P4` unless their exact image-to-text provenance is established.

### 5.5 Current Full Book conclusion

```text
FULL_BOOK_CLAIM =
《紫微斗數全書》 cannot safely be mapped to one universal 庚 row without edition/version qualification.

Strongest current edition-specific report:
late-Ming/early-Qing 文光堂 good woodblock -> C (陽武同陰)
Republican lithographic 《全書》 -> A (陽武陰同), reported as a textual error.

P0 archive scan exists, exact relevant line still unverified.
```


## 6. 《紫微斗數全集》 provenance

### 6.1 Identified primary-edition target

The 2021 academic textual-history paper identifies:

`新刊希夷陳先生紫微斗數全集`
- printer/publisher line: `金陵益軒唐謙梓`
- held by Toyo Bunko (東洋文庫).

This supplies a reliable bibliographic target, but the exact 庚 row in that holding was not directly inspected.

### 6.2 Current row reports

Evidence remains conflicting.

**Variant A reports**
- a DestinyNet transcription of `定祿權科忌四化訣` gives A `庚日武陰同`;
- modern published/product sources explicitly say they use the `紫微斗數全集` table and give A;
- the apparent `斗數零談` text attributes `《全集》` to A.

**Variant B report**
- a reproduced specialist/newspaper research article `紫微斗數話乾坤` reports `《全集》` as B `日武同相`, while also reporting internal inconsistencies in `《全書》`.

None of those row-specific sources is the exact Toyo Bunko page.

### 6.3 Current Complete Collection conclusion

```text
COMPLETE_COLLECTION_CLAIM =
《紫微斗數全集》 is NOT row-verified at P0 in this slice.
A has several reports and is the more frequently encountered attribution in this bounded evidence set.
B is also explicitly reported by a traceable specialist-secondary line.
No majority vote is used.
Conflict remains open until the identified primary/authorized edition page is inspected.
```

```text
COMPLETE_COLLECTION_SOURCE_QUALITY =
P1/P2 for bibliographic identity of the edition/holding;
P3-P5 for current row-specific reports;
P0 exact row verification = OPEN.
```

## 7. 陸斌兆 attribution

Bibliographic record:

`紫微斗數講義（一）：如何排命盤`
- author: 陸斌兆
- publisher: 時報文化
- publication: 1987-03-15
- ISBN13: 9789571300290

A specialist article in 《新玄機》 magazine, `撲朔迷離的講義上集` by 傲天行, says it displays a page from the typeset `陸斌兆紫微斗數講義` alongside an oil-printed manuscript and states that 庚 year uses **太陰化科**, i.e. **Variant A**.

Sources:
- https://www.sanmin.com.tw/product/index/000088186
- https://fengshui-magazine.com.hk/No.232-Oct16/A10.htm

**Source quality for row attribution:** `P3_SCHOOL_OR_SPECIALIST_SECONDARY`

```text
LU_BINZHAO_ATTRIBUTION_STATUS =
PRINTED_LECTURE_REPORTED_A;
DIRECT_AUTHORIZED_PAGE_NOT_INSPECTED;
ORAL_LINEAGE_DIFFERENCE_HAS_BEEN_REPORTED_ELSEWHERE_AND_IS_NOT_RESOLVED.
```

Safe product label:

`REPORTED_LU_BINZHAO_PRINTED_CONVENTION`

not `LU_BINZHAO_UNIVERSAL_LINEAGE`.

## 8. Variant provenance matrix

| VARIANT_ID | SHORT_FORM | 禄 | 权 | 科 | 忌 | CLAIMED_SOURCE_OR_SCHOOL | SOURCE_TITLE / AUTHOR | EDITION / LOCATOR | SOURCE_QUALITY | DIRECT_OR_REPORTED | EVIDENCE_STATUS | CONTRADICTIONS | SAFE_PRODUCT_LABEL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 陽武陰同 | 太陽 | 武曲 | 太陰 | 天同 | iztro default | `SylarLong/iztro` pinned code | `src/data/heavenlyStems.ts`, prior pin `2c7ef9b…` | P4 modern code/upstream-declared | direct code convention | CONFIRMED_CONVENTION | historical source attribution under-specified | `IZTRO_DEFAULT_CONVENTION` |
| A | 陽武陰同 | 太陽 | 武曲 | 太陰 | 天同 | 中州派 | 林聖軒、孫保羅 | official NYCU PDF page 6/12 | P2 | reported | CONFIRMED_ACADEMIC_REPORT | conflicts with Wang-attributed Zhongzhou D | `REPORTED_NYCU_ZHONGZHOU_CONVENTION` |
| A | 陽武陰同 | 太陽 | 武曲 | 太陰 | 天同 | 陸斌兆 printed lecture | `紫微斗數講義`; specialist article | typeset/oil-print page described | P3 | reported from printed page | SUPPORTED | oral-lineage caveat remains | `REPORTED_LU_BINZHAO_PRINTED_CONVENTION` |
| A | 陽武陰同 | 太陽 | 武曲 | 太陰 | 天同 | Republican lithographic `全書` | 心一堂 facsimile publisher | edition-comparison description | P1 | publisher reports later variant/error | STRONG_EDITION_SPECIFIC_REPORT | early woodblock reported C | `REPUBLICAN_QUANSHU_PRINTING_VARIANT` |
| A | 陽武陰同 | 太陽 | 武曲 | 太陰 | 天同 | `全集` | multiple modern/specialist reports | exact P0 page not inspected | P3-P5 | reported | PROVISIONAL | specialist source also reports B | `REPORTED_QUANJI_VARIANT_A` |
| B | 陽武同相 | 太陽 | 武曲 | 天同 | 天相 | 占驗派 | 林聖軒、孫保羅 | official NYCU PDF page 6/12 | P2 | reported | CONFIRMED_ACADEMIC_REPORT | primary school source absent | `REPORTED_ZHANYAN_CONVENTION` |
| B | 陽武同相 | 太陽 | 武曲 | 天同 | 天相 | Linden multi-school synthesis | `ziwei-doushu-skill` pinned reference | `references/sihua.md`, prior pin `a842dd6…` | P4 / repo-derived | direct repo table | CONFIRMED_REPO_CONVENTION | does not prove one school | `LINDEN_MULTI_SCHOOL_CONVENTION` |
| B | 陽武同相 | 太陽 | 武曲 | 天同 | 天相 | old `鐵板神數` report | apparent 王亭之 `斗數零談` text | pp.203–206 in unauthorized copy | P5 | reported by Wang in apparent book text | REPORTED | same apparent text argues `相` may be textual error | `REPORTED_TIEBAN_VARIANT` |
| B | 陽武同相 | 太陽 | 武曲 | 天同 | 天相 | `全集` | specialist/newspaper reproduction | `紫微斗數話乾坤`, §四化 | P3/P5 copy chain | reported | CONFLICTING_REPORT | A also reported for `全集` | `REPORTED_QUANJI_VARIANT_B` |
| C | 陽武同陰 | 太陽 | 武曲 | 天同 | 太陰 | early/good `全書` woodblock | 心一堂 facsimile publisher | late-Ming/early-Qing 文光堂 (`敦化堂`,`繼述堂`) | P1 | publisher reports from facsimile bases | STRONG_EDITION_SPECIFIC_REPORT | later lithograph A; web transcriptions A/B | `QUANSHU_EARLY_WOODBLOCK_REPORTED_VARIANT` |
| C | 陽武同陰 | 太陽 | 武曲 | 天同 | 太陰 | 王亭之 reported `依全書`; 世傳 | apparent `斗數零談` text | pp.203–206 | P5 | reported | CORROBORATIVE_ONLY | exact authorized page absent | `REPORTED_WANG_QUANSHU_VARIANT` |
| D | 陽武府同 | 太陽 | 武曲 | 天府 | 天同 | 王亭之 Zhongzhou | apparent `斗數零談` text | pp.203–204, `關於四化的討論` | P5 exact copy; bibliographic identity strong | apparent direct author text, unauthorized host | HIGH_CONTENT_CONFIDENCE_LOW_SOURCE_CLASS | NYCU P2 says Zhongzhou=A | `REPORTED_WANG_TINGZHI_ZHONGZHOU_CONVENTION` |
| E | 陽武府相 | 太陽 | 武曲 | 天府 | 天相 | Wang teacher-reported alternative | modern reproduction attributed to 王亭之 | no authorized page located | P4-P5 | reported | WEAK_WANG_ATTRIBUTION | not established as Zhongzhou standard | `REPORTED_WANG_TEACHER_ALTERNATIVE` |
| E | 陽武府相 | 太陽 | 武曲 | 天府 | 天相 | 潘子漁 published convention | `紫微斗數研究`, 潘子漁 | publisher/book TOC says `庚年四化 陽武府相` | P1/P3 depending catalog host | direct published TOC convention | CONFIRMED_MODERN_PUBLISHED_VARIANT | lineage before author unresolved | `PAN_ZIYU_PUBLISHED_CONVENTION` |

## 9. Critical Zhongzhou attribution conflict

Fresh evidence preserves, rather than resolves:

```text
NYCU academic secondary (P2):
中州派 -> A (陽武陰同)

Wang Tingzhi-attributed book text
(exact content source P5; bibliographic identity independently strong):
中州派 -> D (陽武府同)
```

Possible explanations include different Zhongzhou lineages, secondary-source simplification/error, terminology drift, edition/time variation, or later reconstruction. None is proven here.

Therefore:

```text
ATTRIBUTION_CONFLICT=OPEN
ZHONGZHOU_ATTRIBUTION_STATUS=CONFLICTED_A_VS_D
```

A future product must not expose a bare `中州派` dropdown that silently chooses A or D.

Safer labels now:
- `REPORTED_NYCU_ZHONGZHOU_CONVENTION`
- `REPORTED_WANG_TINGZHI_ZHONGZHOU_CONVENTION`

## 10. iztro declared-source discrepancy

Existing pinned iztro evidence established:
1. built-in 庚 row = **A**;
2. its source comment says the **default star-placement algorithm** is based on `《紫微斗數全書》`.

That source comment does not explicitly establish that every Tứ Hóa row was copied from one identified `《全書》` edition.

Fresh external evidence says:
- authorized facsimile publisher: early/good 文光堂 `《全書》` -> **C**;
- later Republican lithographic `《全書》` -> **A**, described as a textual error.

Therefore:

```text
IZTRO_DECLARED_SOURCE_CLAIM =
default star-placement algorithm based on 《紫微斗數全書》;
built-in Geng row = A.

EXTERNAL_TEXTUAL_ATTRIBUTION =
identified early/good Full Book tradition is reported as C,
while a later lithographic Full Book tradition has A.

IZTRO_SOURCE_ATTRIBUTION_STATUS =
CONFLICT_REQUIRES_PRIMARY_EDITION_CHECK
```

No iztro documentation or code is rewritten by this task.

## 11. Primary-source status

Precise statement:

```text
PRIMARY_SOURCE_FOUND =
YES — identifiable archival primary scan targets were located.
NO — the exact relevant Geng Tứ Hóa line was not directly inspected in those P0 images during this slice.
```

### P0/P1 targets located

1. **Japan National Archives**
   - `新鋟希夷陳先生紫微斗數全書`
   - call no. `子060-0001`
   - Ming printed edition
   - public image viewer
   - exact Tứ Hóa page still to inspect.

2. **Toyo Bunko**
   - `新刊希夷陳先生紫微斗數全集`
   - `金陵益軒唐謙梓`
   - holding identified by 2021 academic textual-history article
   - exact Tứ Hóa page still to inspect.

3. **心一堂 facsimile**
   - 2017 `紫微斗數全書（明末清初木刻真本）`
   - based on two 虛白廬 文光堂 woodblock exemplars
   - publisher gives explicit C-vs-A edition comparison
   - exact facsimile row page not directly inspected here.


## 12. Product consequence

### Allowed now

A future website may:
- offer an explicit **convention ID**;
- show the exact four-star row;
- show `SOURCE_QUALITY`;
- show edition/source metadata;
- show school attribution only with evidence level;
- display `school attribution disputed` where conflicts remain;
- preserve multiple variants without winner logic.

### Not allowed yet

Do not expose bare authoritative labels such as:
- `中州派` -> one table
- `古法标准`
- `中州正统`
- `唯一正确`
- `紫微斗數全書标准表`
- `紫微斗數全集唯一表`

Safe product contract:

```text
PROFILE_ID
+ CONVENTION_ROW
+ SOURCE/EDITION
+ ATTRIBUTION_STATUS
+ SOURCE_QUALITY
```

## 13. What was previously assumed wrong

The prior engineering model treated the active fork as essentially:

```text
A vs B
```

That was enough to prove *engine configurability*, but not provenance.

Fresh source work shows:
- at least five observed variants;
- `《全書》` has edition/transcription instability;
- `《全集》` row reports conflict;
- `中州派` attribution conflicts between an academic secondary source and Wang-related material;
- `陸斌兆` printed material and reported oral lineage should not be silently treated as identical;
- a website UI saying `古籍原典` is not enough to establish P0 provenance.

## 14. Overengineering gate

**“Không bị over engineering chứ?”**

1. **Simpler path?** Yes: pick the most common table. It fails the accuracy goal because source/edition and school labels demonstrably conflict.
2. **Meaningful provenance information?** Yes: five variants, edition-specific `全書` divergence, `全集` conflict, Zhongzhou conflict, and primary scan targets are now explicit.
3. **Necessary for correct multi-school product?** Yes. Otherwise the UI can silently mislabel one convention as an entire school.
4. **Core accuracy or support infrastructure?** Core source accuracy.
5. **Smaller independently verifiable slice?** This is already one stem (`庚`) and one topic (Tứ Hóa provenance).
6. **Drift risk into all Ziwei schools?** Controlled. No other stems, doctrines, interpretations or engine code were researched/changed.

`OVERENGINEERING_GATE=PASS / DO_IT`

## 15. First unresolved gap

`FIRST_UNRESOLVED_GAP`:

Direct page-level P0/P1 verification of the exact 庚 line in:

1. Japan National Archives Ming `新鋟希夷陳先生紫微斗數全書`;
2. identified Toyo Bunko `新刊希夷陳先生紫微斗數全集`;
3. an authorized edition/page of 王亭之 `斗數零談` for Zhongzhou D.

## 16. Next smallest slice

```text
TASK_ID=ZIWEI_GENG_PRIMARY_PAGE_003

Only inspect and record the exact relevant page/line from the three already-identified primary/authorized targets.

No new schools.
No new stems.
No engine changes.
No interpretation.
No majority vote.
```

## 17. Mutation status

- `ENGINE_CHANGED=NO`
- `PREDICTIVE_CLAIM_ADDED=NO`
- `INTERPRETATION_ADDED=NO`
- `WINNER_SELECTED=NO`
- `MAJORITY_VOTE_USED=NO`

The GitHub connector became disabled mid-session. Therefore this artifact was **not** committed to PR #98 in this turn.

Intended repo destination:

`source/chinese-metaphysics/research/iztro/GENG_SIHUA_PROVENANCE_002.md`

The local handoff artifact is complete and ready to push once repository access is restored.

## 18. Source index

### Institutional / academic
- NYCU publication record: https://stat.nycu.edu.tw/zh_tw/research/con_paper/%E5%91%BD%E7%90%86%E5%AD%B8%E9%87%8F%E5%8C%96%E7%A0%94%E7%A9%B6%E4%B9%8B%E6%A8%A1%E5%9E%8B%E8%88%87%E6%96%B9%E6%B3%95%E8%AB%96-58660032
- NYCU author page/PDF entry: https://shenghsuanlin.web.nycu.edu.tw/2020/02/27/632/
- Airiti, 陳昭吟 2021: https://www.airitilibrary.com/Article/Detail/P20170720001-202112-202202230007-202202230007-33-74

### Historical edition / facsimile
- Japan National Archives catalog/viewer: https://www.digital.archives.go.jp/img/1078787
- Japan National Archives volume viewer: https://www.digital.archives.go.jp/img/4468520
- 心一堂 facsimile publisher: https://publish.sunyata.hk/product/973.html

### Wang Tingzhi
- Google Books `王亭之談星`: https://books.google.com/books/about/%E7%8E%8B%E4%BA%AD%E4%B9%8B%E8%AB%87%E6%98%9F.html?id=TANf661r8hoC
- `斗數零談` bibliographic retailer: https://www.chinyuan.com.tw/all_book/more?id=475
- unauthorized/user-uploaded apparent `斗數零談` copy used only as P5 discovery evidence: Scribd document ID `871559757`
- modern repost used only as P4/P5 corroboration: https://www.getit01.com/p201805312492552/

### Lu Binzhao
- Sanmin bibliographic record: https://www.sanmin.com.tw/product/index/000088186
- 《新玄機》 specialist article: https://fengshui-magazine.com.hk/No.232-Oct16/A10.htm

### Modern transcription/conflict indicators
- Wikisource `紫微斗數全書/卷二`: https://zh.wikisource.org/zh-hant/%E7%B4%AB%E5%BE%AE%E6%96%97%E6%95%B8%E5%85%A8%E6%9B%B8/%E5%8D%B7%E4%BA%8C
- 識典古籍 transcription: https://www.shidianguji.com/zh/book/SDZJ0170/chapter/1jvzooy7dkbhh
- DestinyNet `紫微斗數全集` transcription/discussion: https://destiny.to/ubbthreads/topic/122653

### Variant E independent modern publication
- 武陵/modern book listing for 潘子漁, `紫微斗數研究`, with TOC line `庚年四化 陽武府相`.
