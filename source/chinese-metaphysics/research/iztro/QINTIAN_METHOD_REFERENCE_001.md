# QINTIAN_METHOD_REFERENCE_001

Status: `ACTIVE_REFERENCE / RESEARCH_REFERENCE_ONLY`

## Source

- Repository: `qianye-wuyu/qintian-sihua`
- Pinned commit: `ce449c0a190df09ebe2c14be8aecaac4f7cbf194`
- Declared method: `钦天四化`
- Declared source boundary: distilled from 许铨仁《钦天四化紫微斗数基础》, with some items explicitly supplemented from other traced sources.
- License: **no explicit root LICENSE found at the pinned commit**. Do not vendor or assume commercial reuse rights.

## What this integration uses

Only a small structural subset is activated in `run_ziwei_multilane.mjs`:

1. The repo declares the method order `宫 → 象/四化 → 星`, rather than reading stars in isolation.
2. It declares `生年四化` as the natal/static `体` layer and `飞宫四化` as a dynamic `用` layer.
3. Its verified supplement classifies six inner palaces as 命、财帛、疾厄、官禄、田宅、福德 and six outer palaces as 兄弟、夫妻、子女、迁移、交友/奴仆、父母.
4. Its 化忌 chapter explicitly warns that 化忌 is context-dependent and must not be reduced to `忌 = 凶`.

## What this integration deliberately does NOT use

The current deterministic chart packet exposes natal mutagens and palace placement, but not the full 飞宫/self-transform context required by the declared method. Therefore the lane only emits:

`NATAL_JI location → six-inner/six-outer structural classification → PARTIAL_INPUT`

It does **not** emit the repo's financial, career, marriage, health, timing, or other life advice. Those claims are not promoted by this integration and have no predictive validation here.

## School isolation contract

The same deterministic iztro chart packet may be consumed by multiple method lanes, but their rules remain isolated:

`DETERMINISTIC_CHART_FACTS → METHOD_LANE → SCHOOL/METHOD-TAGGED OUTPUT`

Current lanes:

- `XQR_REPO_DECLARED_6OUT_001`
- `QINTIAN_REPO_DECLARED_001`

Hard invariants:

- side-by-side only;
- no majority vote;
- no winner;
- no automatic conflict resolver;
- no shared master Sihua table;
- no cross-lane rule blending;
- unverified source/license status stays explicit.

## Verdict axes

- ENGINEERING: pending focused runtime test on the integration branch.
- PROVENANCE: PARTIAL. The repo and exact pin are identified; its declared source is recorded, but this artifact does not independently elevate the distilled rules to primary-source status.
- PREDICTIVE: NOT_TESTED.

## Reopen conditions

Reopen or downgrade this lane if the pinned source no longer supports the recorded method statements, if primary/authorized evidence contradicts the attribution, or if future implementation starts using 飞宫/self-transform conclusions without the corresponding deterministic inputs.
