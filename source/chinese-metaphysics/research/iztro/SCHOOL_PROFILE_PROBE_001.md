# ZIWEI_SCHOOL_PROFILE_001 — deterministic Tứ Hóa convention fork

STATUS: `ENGINEERING_PASS / PROVENANCE_PARTIAL / PREDICTIVE_NOT_TESTED`
DOMAIN: `ZIWEI_DOUSHU`
TASK_ID: `ZIWEI_SCHOOL_PROFILE_001`

## Bounded claim

This probe proves only the following capability:

```text
SAME INPUT
+ SAME IZTRO PIN
+ SAME CHART CONSTRUCTION
+ ONLY 庚 TỨ HÓA CONVENTION CHANGED
=> SAME CHART SKELETON
+ DIFFERENT, EXPLICIT TỨ HÓA OUTPUT
```

It does **not** prove which convention is historically correct, which school owns either table, or whether either convention has predictive validity.

## Fresh task state

- P2P research repo: `7roger89-web/P2P-upgrade-github-1`
- Reused branch: `research/chinese-metaphysics-upstreams-01`
- Reused PR: `#98`
- PR head before probe: `5380780c1a90e809f7ebcd4f36a84eeaec3c32e0`
- Main observed before probe: `96b6c1492f1ebdb0bd4c0729b58be22d1bd89a3f`
- Whole 11-repo audit was **not rerun**. Existing run `34520570058` remains prior evidence only.

## Law preflight

Canonical law source read before mutation:

`7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`

`TASK_BRANCH != LAW_AUTHORITY` was preserved.

## Calculation engine

- Upstream: `SylarLong/iztro`
- Pin: `2c7ef9be669df7b19d1799f4dce335fed3794f78`
- Role: `ZIWEI_DETERMINISTIC_CALCULATION_LAYER`

### Relevant iztro implementation evidence

1. `src/data/heavenlyStems.ts`
   - declares Tứ Hóa order as `[禄, 权, 科, 忌]`;
   - default 庚 row is `[太阳, 武曲, 太阴, 天同]`.
2. `src/utils/index.ts`
   - `getTargetMutagens()` uses an explicit configured table when present;
   - otherwise it falls back to the default `heavenlyStems[stem].mutagen` table.
3. `src/astro/astro.ts`
   - `astro.config({ mutagens: ... })` is the existing upstream configuration mechanism.
4. `src/__tests__/astro/plugin.test.ts`
   - upstream itself exercises an override `庚: [太阳, 武曲, 天同, 天相]`.

The upstream source comments say the `default` **star-placement algorithm** is based on 《紫微斗数全书》. This probe did not establish that the default 庚 Tứ Hóa row itself is textually sourced from that primary text. Therefore no primary-source upgrade is made here.

## Input fixture

`INPUT_ROLE=REUSED_UPSTREAM_ENGINEERING_FIXTURE`

The fixture is reused from iztro's pinned plugin test rather than using Owner personal data.

```json
{
  "type": "solar",
  "dateStr": "2010-10-18",
  "timeIndex": 4,
  "gender": "female"
}
```

2010 exercises a 庚 birth-year mapping in the pinned engine.

## Profile A

- `PROFILE_ID=IZTRO_DEFAULT_001`
- `DOMAIN=ZIWEI_DOUSHU`
- `UPSTREAM=SylarLong/iztro`
- `PINNED_SHA=2c7ef9be669df7b19d1799f4dce335fed3794f78`
- `SOURCE_FILE=src/data/heavenlyStems.ts`
- `SOURCE_LOCATOR=gengHeavenly.mutagen; file header states order [禄,权,科,忌]`
- `DECLARED_SCHOOL=IZTRO_DEFAULT_CONVENTION`
- `SCHOOL_ATTRIBUTION=UNVERIFIED`
- `SOURCE_CLASS=UPSTREAM_DECLARED`
- `PROVENANCE_STATUS=UPSTREAM_TABLE_VERIFIED / PRIMARY_SOURCE_UNVERIFIED`
- `CALCULATION_ENGINE=iztro@2c7ef9b...`

Configured/default 庚 table:

```text
化禄=太阳
化权=武曲
化科=太阴
化忌=天同
```

Observed output:

```text
禄=太阳
权=武曲
科=太阴
忌=天同
```

Three-axis verdict:

- `ENGINEERING=PASS`
- `PROVENANCE=PARTIAL`
- `PREDICTIVE=NOT_TESTED`

`CLAIM_PROVED`: pinned iztro deterministically reproduces its default 庚 mapping on the reused fixture.

`CLAIM_NOT_PROVED`: that this mapping is uniquely correct, universal, or belongs to a particular historical school; predictive accuracy.

## Profile B

- `PROFILE_ID=IZTRO_OVERRIDE_LINDEN_TABLE_001`
- `DOMAIN=ZIWEI_DOUSHU`
- `RULE_SOURCE_UPSTREAM=Linden-TR/ziwei-doushu-skill`
- `RULE_SOURCE_PIN=a842dd65dabdc4ce42ec9688b88ae876858a9977`
- `SOURCE_FILE=references/sihua.md`
- `SOURCE_LOCATOR=生年天干四化表 / 庚 row`
- `DECLARED_SCHOOL=MULTI_SCHOOL_SYNTHESIS`
- `SCHOOL_ATTRIBUTION=UNVERIFIED_BEYOND_MULTI_SCHOOL_SYNTHESIS`
- `SOURCE_CLASS=REPO_DERIVED`
- `PROVENANCE_STATUS=REPO_DERIVED_PENDING_PRIMARY_SOURCE`
- `CALCULATION_ENGINE=SylarLong/iztro@2c7ef9b...`

The pinned Linden source explicitly says its Four Transformations material synthesizes `钦天四化、飞星四化、三合四化各流派技法`. That statement does not identify the 庚 row as uniquely belonging to 中州, 三合, 飞星, 钦天, or another single historical school.

Configured 庚 table:

```text
化禄=太阳
化权=武曲
化科=天同
化忌=天相
```

Observed output:

```text
禄=太阳
权=武曲
科=天同
忌=天相
```

Three-axis verdict:

- `ENGINEERING=PASS`
- `PROVENANCE=PARTIAL`
- `PREDICTIVE=NOT_TESTED`

`CLAIM_PROVED`: pinned iztro can apply the exact pinned Linden row as an explicit override and deterministically produces the expected transformed stars.

`CLAIM_NOT_PROVED`: that the Linden row belongs uniquely to any one named school; that it is historically authoritative; predictive accuracy.

## Same-chart comparison

Both runs produced:

- `fiveElementsClass=木三局`;
- byte-equivalent normalized palace/star skeleton in the comparison process;
- identical palace order and major/minor-star placements.

Normalized skeleton used for the explicit comparison:

```text
财帛: 贪狼 | 右弼
子女: 天机,巨门 | 地劫
夫妻: 紫微,天相 | -
兄弟: 天梁 | 火星
命宫: 七杀 | 文昌
父母: - | 天钺,地空,铃星,陀罗
福德: 廉贞 | 文曲,禄存,天马
田宅: - | 擎羊
官禄: 破军 | -
仆役: 天同 | -
迁移: 武曲,天府 | 左辅
疾厄: 太阳,太阴 | 天魁
```

Result:

- `CHART_SKELETON_SAME=YES`
- `PROFILE_OUTPUT_DIFF_PROVEN=YES`
- `PROFILE_CONTAMINATION_PREVENTED=YES`

## Process isolation

The two profiles were executed in **two separate fresh Node processes** after one build of the same pinned iztro checkout:

1. Profile A process loaded iztro with no mutagen override.
2. Profile B process loaded iztro fresh, then applied only `astro.config({ mutagens: { 庚: [...] } })`.
3. A third process compared the serialized outputs and asserted the bounded claim.

No config-state manager, registry, plugin framework, or universal profile resolver was introduced.

## Execution evidence

Targeted temporary GitHub Actions run:

- workflow run: `34686343756`
- job: `103533868752`
- conclusion: `SUCCESS`
- iztro checkout HEAD asserted equal to the pinned SHA.

The compare step asserted all of the following and exited successfully:

```text
CHART_SKELETON_SAME=YES
PROFILE_OUTPUT_DIFF_PROVEN=YES
PROFILE_CONTAMINATION_PREVENTED=YES
PROFILE_A_OBSERVED={"禄":"太阳","权":"武曲","科":"太阴","忌":"天同"}
PROFILE_B_OBSERVED={"禄":"太阳","权":"武曲","科":"天同","忌":"天相"}
```

The temporary workflow is execution scaffolding only and is removed after evidence capture; it is not a new project framework.

## Explicit non-claims

- `FALSE_SCHOOL_ATTRIBUTION_ADDED=NO`
- `WINNER_OR_MAJORITY_LOGIC_ADDED=NO`
- `PREDICTIVE_CLAIM_ADDED=NO`
- `UNIVERSAL_ZIWEI_ENGINE_CREATED=NO`
- `MASTER_SIHUA_TABLE_CREATED=NO`
- `INTERPRETATION_IMPLEMENTED=NO`

## Overengineering gate

“Không bị over engineering chứ?”

1. Simpler path with same proof? No: merely citing two tables would not prove one engine can isolate and reproduce both profiles on the same chart.
2. Meaningful progress? Yes: this establishes the smallest deterministic school-profile capability needed by a future multi-school product.
3. If omitted, is a success condition missing? Yes: no runtime proof of convention isolation.
4. Core or supporting infrastructure? Core deterministic capability.
5. Smaller independently verifiable slice? This is already one engine + one stem + one fixture + one convention fork.
6. Risk of drifting into universal Ziwei research/framework? Controlled: no interpretation or resolver was added.

`OVERENGINEERING_GATE=PASS / DO_IT`

## First unresolved provenance gap

`FIRST_UNRESOLVED_PROVENANCE_GAP`: primary-source attribution of each 庚 table, especially whether either row can be assigned uniquely to a named historical school. The current repo-level evidence is insufficient for that claim.

## Next smallest slice

Perform a **source-only provenance arbitration** for the two 庚 rows: locate primary/authorized textual evidence and record exact edition/locator and school attribution, without changing engine behavior or choosing a winner unless the source actually warrants it.
