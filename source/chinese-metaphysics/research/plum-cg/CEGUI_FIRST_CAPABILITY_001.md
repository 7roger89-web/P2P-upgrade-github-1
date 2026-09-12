# CEGUI_FIRST_CAPABILITY_001

TASK_ID: CHINESE_METAPHYSICS_LARGE_GOAL_01
DOMAIN: CEGUI / 皇极梅花策轨
STATUS: MILESTONE_D_REACHED
ENGINE_CHANGED: NO

## Engine baseline

UPSTREAM: soom-lupulus/plum-cg
PIN: 509fc43001a503d17a37db07bc56e069b1ff1c4f
ROLE: deterministic calculation candidate

Existing audit evidence (pin unchanged):
- 8 test files
- 39/39 tests PASS
- typecheck PASS
- build PASS

No whole-matrix rerun was performed.

## Historical/formula witnesses

1. 《钦定古今图书集成·理学汇编·学行典》第021卷,
   section reproducing 《皇极经世心易发微》:
   https://zh.wikisource.org/zh-hans/钦定古今圖書集成/理學彙編/學行典/第021卷

   Gives:
   - 阳爻 = 36 策
   - 阴爻 = 24 策
   - 阳爻 = 128 轨
   - 阴爻 = 112 轨
   - 先天八卦正数
   - 后天八卦正数
   - upper/lower-moving calculation rule.

2. Modern formula restatement used only to make arithmetic explicit:
   `神数演义第二版` (secondary/unverified PDF copy)
   gives:
   upper-moving:
   策数 = 身数*爻数*10 + 身数*上卦先天数 + 身数 + 上卦数 + 下卦数 + 爻数
   轨数 = 身数*爻数*10 + 身数*上卦后天数 + 身数 + 上卦数 + 下卦数 + 爻数

## Independent recomputation packet

INPUT:
- 主卦 = 震为雷
- 动爻 = 4
- upper trigram = 震
- lower trigram = 震
- yang lines = 2
- yin lines = 4

CONVENTION_ID:
- 先天震 = 4
- 后天震 = 3

### Original 策 body

2*36 + 4*24
= 72 + 96
= 168

### 策数

168*4*10
+ 168*4
+ 168
+ 4 + 4 + 4
= 6720 + 672 + 168 + 12
= 7572

RESULT:
`策数 = 07572`

This matches the plum-cg README example/table tradition for 震为雷四爻.

### Original 轨 body

2*128 + 4*112
= 256 + 448
= 704

### 轨数

704*4*10
+ 704*3
+ 704
+ 3 + 3 + 4
= 28160 + 2112 + 704 + 10
= 30986

RESULT:
`轨数 = 30986`

This matches the published table witness for 震为雷四爻.

## Formula trace packet

INPUT
→ yin/yang line count
→ 原策 / 原轨
→ moving-trigram branch (upper)
→ explicit trigram-number convention
→ multiplication terms
→ additive terms
→ final number

No interpretation bridge is added.

## Known variant: number 5

The repo explicitly states that number 5 mapping to 艮/坤 is disputed and supports an optional compatibility convention.

Historical transcriptions also expose variant wording around:
- 先天生成数 5/10 and 艮/坤
- 后天 `五寄艮 / 十寄坤`

Therefore:
`NUMBER_5_MAPPING = EXPLICIT_CONVENTION_REQUIRED`

No universal normalization is selected.

## Verdict

ENGINEERING = PASS
FORMULA_REPRODUCTION = PASS
PROVENANCE = PARTIAL_GOOD:
historical textual witness exists, but exact genealogy from historical formula to repo implementation remains to be audited file-by-file once repository access returns.
PREDICTIVE = NOT_APPLICABLE / NOT_TESTED

This milestone intentionally stops at deterministic calculation.
