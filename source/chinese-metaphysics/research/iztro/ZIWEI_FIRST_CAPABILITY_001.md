# ZIWEI_FIRST_CAPABILITY_001

TASK_ID: CHINESE_METAPHYSICS_LARGE_GOAL_01
DOMAIN: ZIWEI_DOUSHU
STATUS: MILESTONE_A_REACHED_WITH_PARTIAL_PROVENANCE
ENGINE_CHANGED: NO

## Deterministic packet reused

ENGINE: SylarLong/iztro
PIN: 2c7ef9be669df7b19d1799f4dce335fed3794f78
INPUT_ROLE: REUSED_ENGINEERING_FIXTURE
INPUT:
- solar date: 2010-10-18
- timeIndex: 4
- gender: female

PROFILE_ID: IZTRO_DEFAULT_001
GENG_SIHUA:
- 禄 = 太阳
- 权 = 武曲
- 科 = 太阴
- 忌 = 天同

Previously proven facts:
- same chart skeleton remains stable under profile switching;
- this profile places:
  - 太阳 / 太阴 in 疾厄
  - 武曲 in 迁移
  - 天同 in 仆役
- therefore the birth-year 忌 for this explicit profile is 天同 in 仆役.

## Interpretation lane

LANE_ID: XQR_REPO_DECLARED_6OUT_001
DECLARED_METHOD: 许铨仁 / modern 飞宫 reconstruction
SOURCE_STATUS: REPO_DERIVED + SPECIALIST_TRANSCRIPT_CORROBORATION
PRIMARY_AUTHORIZED_METHOD_VERIFIED: NO

### Rule trace

R1
- repo source: ZhangZangQian/xu-quanren `work.md`
- wording: 宫优先于星；生年优先于飞宫；生年四化为体
- role: order of interpretation
- status: REPO_DERIVED

R2
- repo source: same `work.md`
- wording: 忌入六内主得，忌入六外主失
- status: REPO_DERIVED

R3
- specialist transcript: 许铨仁高级班文字整理第33集
- URL: https://www.ziweicn.com/yiyuxinshu/baijiazatan/4244.html
- lists 六内 = 命、财帛、疾厄、官禄、田宅、福德
- lists 六外 = 兄弟、夫妻、子女、迁移、交友、父母
- reports 财官化忌入六内主得、入六外主凶主失
- status: SPECIALIST_SECONDARY_TRANSCRIPT; not authorized primary edition

### Application

1. Deterministic fact: birth-year 忌 = 天同.
2. Deterministic fact: 天同 is in 仆役.
3. Method normalization for this lane only: 仆役 ≈ 交友.
4. Source-defined palace class: 交友 belongs to 六外.
5. XQR lane structural tag:
   `BIRTH_YEAR_JI_TARGET_CLASS = SIX_OUTER`
6. Bounded method output:
   `XQR_STRUCTURAL_TAG = OUTER/LOSS_INDICATOR`

## Non-claims

This packet does NOT claim:
- the person will lose friends;
- a specific relationship event;
- health, wealth, career, marriage, or timing;
- predictive validity;
- that XQR is historically the same as Fang Wairen/He Luo;
- that the iztro default Geng table is XQR's unique table.

This is a reproducible METHOD_APPLICATION packet, not a natal prediction.

## Three-axis verdict

ENGINEERING = PASS (reuses previously executed deterministic probe)
PROVENANCE = PARTIAL
PREDICTIVE = NOT_TESTED

## Why this reaches the first Ziwei milestone

It demonstrates:
INPUT
→ deterministic chart facts
→ explicit PROFILE_ID
→ one declared method lane
→ RULE_TRACE
→ a source-bounded structural interpretation tag
→ uncertainty and non-claims.

No universal Ziwei method was created.
