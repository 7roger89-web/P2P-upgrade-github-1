#!/usr/bin/env node
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const QINTIAN_SOURCE = {
  repo: 'qianye-wuyu/qintian-sihua',
  pin: 'ce449c0a190df09ebe2c14be8aecaac4f7cbf194',
  methodology: 'references/methodology-overview.md',
  huaJi: 'references/08-hua-ji.md',
  supplements: 'references/verified-supplements.md',
  license: 'NO_EXPLICIT_LICENSE_FOUND',
  useBoundary: 'RESEARCH_REFERENCE_ONLY',
};

const dir = path.dirname(fileURLToPath(import.meta.url));
const baseRunner = path.join(dir, 'run_ziwei_capability.mjs');
const base = spawnSync(process.execPath, [baseRunner, ...process.argv.slice(2)], { encoding: 'utf8' });
if (base.status !== 0) {
  process.stderr.write(base.stderr);
  process.exit(base.status ?? 1);
}
const chart = JSON.parse(base.stdout);

function normalizePalace(name) {
  if (!name) return null;
  const stripped = String(name).replace(/宫$/u, '');
  return stripped === '仆役' ? '交友' : stripped;
}

const sixInner = new Set(['命', '财帛', '疾厄', '官禄', '田宅', '福德']);
const sixOuter = new Set(['兄弟', '夫妻', '子女', '迁移', '交友', '父母']);
const jiPalace = normalizePalace(chart.TARGET_PALACE);
let qintianGroup = 'UNCLASSIFIED';
if (sixInner.has(jiPalace)) qintianGroup = 'SIX_INNER';
if (sixOuter.has(jiPalace)) qintianGroup = 'SIX_OUTER';

const qintianLane = {
  LANE_ID: 'QINTIAN_REPO_DECLARED_001',
  DECLARED_METHOD: '钦天四化',
  SOURCE: QINTIAN_SOURCE,
  METHOD_ORDER: ['PALACE', 'SYMBOL_MUTAGEN', 'STAR'],
  NATAL_MUTAGEN_ROLE: '体',
  NATAL_JI: {
    star: chart.TARGET_STAR,
    palace: chart.TARGET_PALACE,
    palace_group: qintianGroup,
  },
  STRUCTURAL_OBSERVATION: qintianGroup === 'UNCLASSIFIED' ? 'PALACE_GROUP_UNRESOLVED' : `NATAL_JI_IN_${qintianGroup}`,
  INTERPRETATION_READINESS: 'PARTIAL_INPUT',
  MISSING_FOR_FULL_METHOD: ['FLYING_TRANSFORMATIONS', 'SELF_TRANSFORMATIONS', 'PALACE_STEM_CONTEXT'],
  NONCLAIMS: [
    'NATAL_JI_ALONE_DOES_NOT_PROVE_GOOD_OR_BAD',
    'NO_FINANCIAL_CAREER_HEALTH_OR_RELATIONSHIP_ADVICE',
    'NO_PREDICTIVE_VALIDATION',
    'NO_LICENSE_FOR_VENDORING_THIS_REFERENCE',
  ],
};

const xqrLane = {
  LANE_ID: chart.METHOD_LANE,
  SOURCE: {
    repo: 'ZhangZangQian/xu-quanren',
    status: 'EXISTING_AUDITED_REFERENCE',
  },
  target_star: chart.TARGET_STAR,
  target_palace: chart.TARGET_PALACE,
  target_class: chart.BIRTH_YEAR_JI_TARGET_CLASS,
  structural_output: chart.STRUCTURAL_OUTPUT,
  provenance_status: chart.PROVENANCE_STATUS,
  predictive_status: chart.PREDICTIVE_STATUS,
};

console.log(JSON.stringify({
  DOMAIN: 'ZIWEI_DOUSHU',
  CAPABILITY: 'SCHOOL_ISOLATED_MULTILANE',
  INPUT: chart.INPUT,
  INPUT_MODE: chart.INPUT_MODE,
  ENGINE_PIN: chart.ENGINE_PIN,
  PROFILE_ID: chart.PROFILE_ID,
  DETERMINISTIC_CHART_FACTS: chart.CHART_FACTS,
  BIRTH_YEAR_MUTAGEN: chart.BIRTH_YEAR_MUTAGEN,
  LANES: {
    XQR: xqrLane,
    QINTIAN: qintianLane,
  },
  COMPARISON_POLICY: 'SIDE_BY_SIDE_ONLY',
  WINNER: null,
  MAJORITY_VOTE: null,
  SYNTHESIZED_SCHOOL_OUTPUT: null,
  NONCLAIMS: ['NO_SCHOOL_MERGE', 'NO_SCHOOL_WINNER', 'NO_PREDICTIVE_ACCURACY_CLAIM'],
}, null, 2));
