# MEIHUA_FIRST_CAPABILITY_001

TASK_ID: CHINESE_METAPHYSICS_LARGE_GOAL_01
DOMAIN: MEIHUA_YISHU
STATUS: MILESTONE_C_REACHED_WITH_CLASSICAL_RETROSPECTIVE_CASE
ENGINE_CHANGED: NO

## Casting-mode lock

CASTING_MODE = TRADITIONAL_TIME_CASTING

Classical source:
《梅花易数·卷一·年月日時起例》
Wikisource:
https://zh.wikisource.org/wiki/梅花易數/卷一

Classical rule:
- year + month + day -> upper trigram, mod 8
- year + month + day + traditional shichen -> lower trigram, mod 8
- total -> moving line, mod 6

This mode uses the traditional 12 two-hour branches.
It is NOT the repo's modern second-level time extension.

MODERN_SECOND_LEVEL_EXTENSION:
allowed only under its own explicit casting-mode ID; not silently mixed here.

## Reproducible classical fixture

Use the classical 观梅 example:
- 辰年 = 5
- 十二月 = 12
- 十七日 = 17
- 申时 = 9

CALCULATION:
upper total = 5 + 12 + 17 = 34
34 mod 8 = 2 -> 兑

lower total = 34 + 9 = 43
43 mod 8 = 3 -> 离

moving line:
43 mod 6 = 1

RESULT:
- 主卦 = 泽火革
- 动爻 = 初爻
- 变卦 = 泽山咸
- 互卦 components = 乾 / 巽

These reproduce the classical example.

## 体用 lock

Classical method:
moving trigram = 用
static trigram = 体

The moving line is in the lower trigram:
- lower 离火 = 用
- upper 兑金 = 体

## Source-grounded structural reading

Classical sources:
- 《梅花易数·卷二·体用总诀》
- 《梅花易数·卷三·体用生克之诀》

Wikisource:
https://zh.wikisource.org/zh-hant/梅花易數/卷二
https://zh.wikisource.org/zh-hant/梅花易數/卷三

Rule trace:
- 用克体 -> adverse/pressuring relation.
- 变卦生体 -> later/final relation has support.
- mutual/changed layers are subordinate structural evidence rather than free-form story generators.

APPLICATION:
- 离火克兑金 -> `INITIAL_RELATION = USE_CONTROLS_BODY`
- changed lower trigram 艮土 generates 兑金 -> `LATER_RELATION = CHANGE_GENERATES_BODY`

BOUNDED_OUTPUT:
`INITIAL_PRESSURE_WITH_LATER_SUPPORT`

This is a structural traditional-method reading, not a prediction of a person's actual future.

## 外应 rule

No external sign is accepted unless provided in raw input.
`EXTERNAL_SIGN_MISSING -> DO_NOT_FABRICATE`

## Negative predictive evidence preserved

Upstream: muyen/meihua-yishu
Existing experiment report:
https://github.com/muyen/meihua-yishu/blob/main/experiments/prediction-validation/FINAL-REPORT.md

Its tested operationalization did not show a predictive advantage and reported approximately chance-level performance for the Meihua agent against stronger baselines.

This remains NEGATIVE_EVIDENCE.
It does not invalidate every historical Meihua method, but it forbids us from claiming predictive validation for this capability.

## Three-axis verdict

ENGINEERING/CONSTRUCTION = PASS for the reproduced classical arithmetic
PROVENANCE = GOOD for the bounded Wikisource classical transcription, exact historical edition still separately auditable
PREDICTIVE = NEGATIVE/NOT_ESTABLISHED for the tested modern operationalization
