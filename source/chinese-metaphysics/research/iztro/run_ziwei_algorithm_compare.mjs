#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const PIN = '2c7ef9be669df7b19d1799f4dce335fed3794f78';
const scriptPath = fileURLToPath(import.meta.url);
const scriptDir = path.dirname(scriptPath);
const upstream = path.resolve(scriptDir, '../../upstreams/iztro');

function fail(msg, code = 2) { console.error(msg); process.exit(code); }
function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : undefined; }
function has(name) { return process.argv.includes(name); }

function parseInput() {
  const dateStr = arg('--date') ?? '2010-10-18';
  const timeIndexRaw = arg('--time-index') ?? '4';
  const gender = arg('--gender') ?? 'female';
  if (!/^\d{4}-\d{1,2}-\d{1,2}$/.test(dateStr)) fail(`Invalid --date: ${dateStr}`);
  const timeIndex = Number(timeIndexRaw);
  if (!Number.isInteger(timeIndex) || timeIndex < 0 || timeIndex > 12) fail(`Invalid --time-index: ${timeIndexRaw}`);
  if (!['male', 'female'].includes(gender)) fail(`Invalid --gender: ${gender}`);
  return { dateStr, timeIndex, gender };
}

function verifyUpstream() {
  if (!fs.existsSync(upstream)) fail(`Pinned upstream missing: ${upstream}`);
  let head;
  try { head = execFileSync('git', ['-C', upstream, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); }
  catch { fail(`Cannot verify pinned upstream: ${upstream}`); }
  if (head !== PIN) fail(`Pinned upstream SHA mismatch: expected ${PIN}, got ${head}`);
  const builtEntry = path.join(upstream, 'lib', 'index.js');
  if (!fs.existsSync(builtEntry)) fail(`Pinned upstream build missing: ${builtEntry}`);
  return builtEntry;
}

function mechanicalPacket(chart, algorithm, input) {
  const starLocations = {};
  for (const palace of chart.palaces ?? []) {
    for (const star of [...(palace.majorStars ?? []), ...(palace.minorStars ?? []), ...(palace.adjectiveStars ?? [])]) {
      if (!star?.name) continue;
      (starLocations[star.name] ??= []).push(palace.name);
    }
  }
  for (const locations of Object.values(starLocations)) locations.sort();
  return {
    DOMAIN: 'ZIWEI_DOUSHU',
    ENGINE_PIN: PIN,
    INPUT: input,
    PROFILE_ID: algorithm === 'zhongzhou' ? 'IZTRO_ZHONGZHOU_MECHANICAL_001' : 'IZTRO_DEFAULT_MECHANICAL_001',
    CONFIG: {
      yearDivide: 'normal',
      horoscopeDivide: 'normal',
      ageDivide: 'normal',
      dayDivide: 'forward',
      algorithm,
    },
    MECHANICAL_FACTS: {
      soul: chart.soul,
      body: chart.body,
      earthly_branch_of_soul_palace: chart.earthlyBranchOfSoulPalace,
      earthly_branch_of_body_palace: chart.earthlyBranchOfBodyPalace,
      five_elements_class: chart.fiveElementsClass,
      palace_count: (chart.palaces ?? []).length,
      palace_names: (chart.palaces ?? []).map((p) => p.name),
      star_locations: starLocations,
    },
    PROVENANCE_STATUS: 'PINNED_IZTRO_DECLARED_ALGORITHM',
    PREDICTIVE_STATUS: 'NOT_TESTED',
    NONCLAIMS: ['NO_SCHOOL_ACCURACY_WINNER', 'NO_NATAL_INTERPRETATION', 'NO_PREDICTIVE_CLAIM'],
  };
}

if (has('--single-profile')) {
  const algorithm = arg('--single-profile');
  if (!['default', 'zhongzhou'].includes(algorithm)) fail(`Invalid --single-profile: ${algorithm}`);
  const input = parseInput();
  const builtEntry = verifyUpstream();
  const require = createRequire(import.meta.url);
  const { astro } = require(builtEntry);
  if (!astro?.withOptions) fail('Pinned iztro API missing: astro.withOptions');
  let chart;
  try {
    chart = astro.withOptions({
      type: 'solar',
      dateStr: input.dateStr,
      timeIndex: input.timeIndex,
      gender: input.gender,
      config: {
        yearDivide: 'normal',
        horoscopeDivide: 'normal',
        ageDivide: 'normal',
        dayDivide: 'forward',
        algorithm,
      },
    });
  } catch (err) {
    fail(`iztro rejected ${algorithm} profile: ${err?.message ?? err}`, 1);
  }
  console.log(JSON.stringify(mechanicalPacket(chart, algorithm, input), null, 2));
  process.exit(0);
}

const input = parseInput();
function runProfile(algorithm) {
  const r = spawnSync(process.execPath, [scriptPath, '--single-profile', algorithm, '--date', input.dateStr, '--time-index', String(input.timeIndex), '--gender', input.gender], { encoding: 'utf8' });
  if (r.status !== 0) {
    if (r.stderr) process.stderr.write(r.stderr);
    fail(`${algorithm} profile execution failed`, r.status ?? 1);
  }
  return JSON.parse(r.stdout);
}

const defaultProfile = runProfile('default');
const zhongzhouProfile = runProfile('zhongzhou');
const d = defaultProfile.MECHANICAL_FACTS;
const z = zhongzhouProfile.MECHANICAL_FACTS;

const allStars = new Set([...Object.keys(d.star_locations), ...Object.keys(z.star_locations)]);
const starDiffs = [];
for (const star of [...allStars].sort()) {
  const a = d.star_locations[star] ?? [];
  const b = z.star_locations[star] ?? [];
  if (JSON.stringify(a) !== JSON.stringify(b)) starDiffs.push({ star, default: a, zhongzhou: b });
}

const diff = {
  soul_changed: d.soul !== z.soul,
  body_changed: d.body !== z.body,
  soul_palace_branch_changed: d.earthly_branch_of_soul_palace !== z.earthly_branch_of_soul_palace,
  body_palace_branch_changed: d.earthly_branch_of_body_palace !== z.earthly_branch_of_body_palace,
  five_elements_class_changed: d.five_elements_class !== z.five_elements_class,
  palace_names_changed: JSON.stringify(d.palace_names) !== JSON.stringify(z.palace_names),
  star_location_differences: starDiffs,
};
const materialDiffCount = Number(diff.soul_changed) + Number(diff.body_changed) + Number(diff.soul_palace_branch_changed) + Number(diff.body_palace_branch_changed) + Number(diff.five_elements_class_changed) + Number(diff.palace_names_changed) + starDiffs.length;

console.log(JSON.stringify({
  DOMAIN: 'ZIWEI_DOUSHU',
  CAPABILITY: 'IZTRO_DEFAULT_VS_ZHONGZHOU_MECHANICAL_PROFILE_COMPARE',
  INPUT: input,
  DEFAULT_PROFILE: defaultProfile,
  ZHONGZHOU_PROFILE: zhongzhouProfile,
  DETERMINISTIC_DIFF: diff,
  MATERIAL_DIFF_COUNT: materialDiffCount,
  ISOLATION: 'EACH_PROFILE_EXECUTED_IN_A_FRESH_NODE_PROCESS',
  PROVENANCE_STATUS: 'PINNED_IZTRO_PUBLIC_API_AND_DECLARED_ALGORITHM',
  PREDICTIVE_STATUS: 'NOT_TESTED',
  NONCLAIMS: ['NO_SCHOOL_WINNER', 'NO_INTERPRETATION_MERGE', 'NO_TRUE_SOLAR_TIME_CLAIM'],
}, null, 2));
