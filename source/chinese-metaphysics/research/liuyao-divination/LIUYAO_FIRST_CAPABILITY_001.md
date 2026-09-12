# LIUYAO_FIRST_CAPABILITY_001

TASK_ID: CHINESE_METAPHYSICS_LARGE_GOAL_01
DOMAIN: LIUYAO
STATUS: MILESTONE_B_REACHED_WITH_RETROSPECTIVE_FIXTURE
ENGINE_CHANGED: NO

## Engine baseline

UPSTREAM: Johnson-Jia/liuyao-divination
PIN: 1a5a78b513c0e7b46dfb29f74043bcf978c32a3e
ROLE: mechanical board construction + separate reasoning layer
PRIOR_ENGINEERING_EVIDENCE: 23/23 pytest PASS from existing audit; not rerun because pin unchanged.

## Frozen canonical fixture

QUESTION_CONTEXT:
repo example: male asks whether a family-introduced partner is beneficial / "旺自己"

RAW:
- 主卦 = 地泽临
- 动爻 = 二爻
- 月建 = 未
- 日 = 辛卯
- 变卦 = 地雷复

### Board packet facts

Classical cross-check for 地泽临 from 《卜筮正宗》:
top → bottom:
6. 子孙 癸酉金
5. 妻财 癸亥水 — 应
4. 兄弟 癸丑土
3. 兄弟 丁丑土
2. 官鬼 丁卯木 — 世 — moving
1. 父母 丁巳火

Changing line 2 gives 地雷复 lower-trigram line:
- 丁卯 → 庚寅
- repo classifies this as 化退.

Repo canonical test additionally freezes:
- 妻财亥水 = 用神 at line 5
- 子孙酉金 = 暗动, not 日破
- 世爻丁卯 = 入未墓 and 化退为庚寅
- 旬空 = 午未
- no actual board line falls into void

## Source-grounded reasoning path

### Step 1 — 取用神

SOURCE:
《增删卜易》, 用神/婚姻 material.
Accessible text:
https://daizhige.org/易藏/术数/增删卜易.html

Relevant doctrine:
- male self-question concerning wife/partner uses 妻财 as 用神.

APPLICATION:
- board has 妻财亥水 at line 5.
- select it as 用神 for this bounded question.

STATUS:
CLASSICAL_TEXT_TRANSCRIPTION; edition-level primary scan not separately verified here.

### Step 2 — 元神 relation

《增删卜易》 defines 元神 as the element that generates 用神.
- 用神 = 水
- 金生水
- therefore 子孙酉金 is an 元神 candidate.

### Step 3 — 暗动 versus 日破

SOURCE:
《增删卜易·暗动章第二十二》
same accessible transcription.

Rule:
- 静爻旺相，日辰冲之 = 暗动
- 静爻休囚，日辰冲之 = 破

APPLICATION:
- 酉 is hit by 卯 day.
- under the canonical fixture it is month-supported and is classified by the engine as 暗动.
- therefore this support line is active rather than discarded as a day-break.

### Step 4 — subject-side constraint

Frozen engine facts:
- 世爻 丁卯
- 入未墓
- moving line changes to 庚寅
- repo classifies 卯→寅 as 化退.

This is kept as a structural constraint, not converted into a deterministic real-world event.

## Bounded interpretation

Traditional-rule synthesis for this fixture:

- partner-sign / 用神 = 妻财亥水 is present;
- its generating support (酉金) is structurally activated as 暗动 rather than broken;
- the subject-side 世爻 simultaneously carries a retreat/constraint pattern in the engine's method.

SAFE_OUTPUT:
`SUPPORT_EXISTS_BUT_SELF_SIDE_CONSTRAINT_PRESENT`

DO_NOT_FORCE_BINARY:
This packet deliberately does not upgrade that structure into an unconditional "旺 / 不旺" verdict without additional source-traced rules.

## Error separation

CONSTRUCTION_ERROR:
wrong hexagram, 纳甲, 六亲, 世应, void, moving transformation, month/day relation.

REASONING_ERROR:
wrong 用神, wrong strength judgment, wrong rule application, over-interpretation.

Interpretation may never rewrite BOARD_PACKET.

## Evidence status

ENGINEERING = PASS (existing pinned audit)
PROVENANCE = PARTIAL_TO_GOOD for selected classical rules; edition-level primary verification still open
PREDICTIVE = NOT_TESTED

The fixture is retrospective/golden-case evidence, not blind prediction.
