#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const PIN = '2c7ef9be669df7b19d1799f4dce335fed3794f78';
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const upstream = path.resolve(scriptDir, '../../upstreams/iztro');

function fail(msg, code = 2) { console.error(msg); process.exit(code); }
function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : undefined; }
function has(name) { return process.argv.includes(name); }

if (!fs.existsSync(upstream)) fail(`Pinned upstream missing: ${upstream}`);
let head;
try { head = execFileSync('git', ['-C', upstream, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); }
catch { fail(`Cannot verify pinned upstream: ${upstream}`); }
if (head !== PIN) fail(`Pinned upstream SHA mismatch: expected ${PIN}, got ${head}`);

const builtEntry = path.join(upstream, 'lib', 'index.js');
if (!fs.existsSync(builtEntry)) fail(`Pinned upstream build missing: ${builtEntry}`);
const require = createRequire(import.meta.url);
const { astro } = require(builtEntry);
if (!astro?.bySolar) fail('Pinned iztro API missing: astro.bySolar');

const fixture = arg('--fixture');
const customRequested = has('--date') || has('--time-index') || has('--gender');
if (fixture && customRequested) fail('Use either --fixture or custom --date/--time-index/--gender, not both');

let input;
let inputMode;
if (fixture) {
  if (fixture !== 'default') fail(`Unknown fixture: ${fixture}`);
  input = { dateStr: '2010-10-18', timeIndex: 4, gender: 'female' };
  inputMode = 'FIXTURE';
} else {
  const dateStr = arg('--date');
  const timeIndexRaw = arg('--time-index');
  const gender = arg('--gender');
  if (!dateStr || timeIndexRaw === undefined || !gender) fail('Custom usage: --date YYYY-MM-DD --time-index 0..12 --gender male|female');
  if (!/^\d{4}-\d{1,2}-\d{1,2}$/.test(dateStr)) fail(`Invalid --date: ${dateStr}`);
  const timeIndex = Number(timeIndexRaw);
  if (!Number.isInteger(timeIndex) || timeIndex < 0 || timeIndex > 12) fail(`Invalid --time-index: ${timeIndexRaw}`);
  if (!['male', 'female'].includes(gender)) fail(`Invalid --gender: ${gender}`);
  input = { dateStr, timeIndex, gender };
  inputMode = 'CUSTOM';
}

let chart;
try { chart = astro.bySolar(input.dateStr, input.timeIndex, input.gender); }
catch (err) { fail(`iztro rejected input: ${err?.message ?? err}`, 1); }

const palaces = chart.palaces ?? [];
const mutagen = {};
const starPalace = new Map();
for (const palace of palaces) {
  for (const star of [...(palace.majorStars ?? []), ...(palace.minorStars ?? [])]) {
    if (star?.mutagen) mutagen[star.mutagen] = star.name;
    if (star?.name) starPalace.set(star.name, palace.name);
  }
}
const jiStar = mutagen['忌'] ?? null;
const jiPalace = jiStar ? (starPalace.get(jiStar) ?? null) : null;
const sixOuter = new Set(['兄弟', '夫妻', '子女', '迁移', '仆役', '交友', '父母']);
const targetClass = jiPalace ? (sixOuter.has(jiPalace) ? 'SIX_OUTER' : 'NOT_SIX_OUTER') : 'NO_JI_TARGET';
const structuralOutput = targetClass === 'SIX_OUTER' ? 'OUTER/LOSS_INDICATOR' : targetClass;

if (inputMode === 'FIXTURE') {
  const expected = { '禄': '太阳', '权': '武曲', '科': '太阴', '忌': '天同' };
  for (const [k, v] of Object.entries(expected)) if (mutagen[k] !== v) fail(`Unexpected Geng mutagen ${k}: expected ${v}, got ${mutagen[k]}`, 1);
  if (structuralOutput !== 'OUTER/LOSS_INDICATOR') fail(`XQR bounded lane fixture drift: ${jiStar} palace=${jiPalace}`, 1);
}

console.log(JSON.stringify({
  DOMAIN: 'ZIWEI_DOUSHU', ENGINE_PIN: PIN, INPUT_MODE: inputMode, INPUT: input,
  PROFILE_ID: 'IZTRO_DEFAULT_001',
  CHART_FACTS: { five_elements_class: chart.fiveElementsClass, palace_count: palaces.length, palace_names: palaces.map((p) => p.name) },
  BIRTH_YEAR_MUTAGEN: mutagen,
  METHOD_LANE: 'XQR_REPO_DECLARED_6OUT_001',
  RULE_TRACE: ['XQR_R1_PALACE_BEFORE_STAR', 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER'],
  TARGET_STAR: jiStar, TARGET_PALACE: jiPalace, BIRTH_YEAR_JI_TARGET_CLASS: targetClass,
  STRUCTURAL_OUTPUT: structuralOutput, PROVENANCE_STATUS: 'PARTIAL', PREDICTIVE_STATUS: 'NOT_TESTED',
  NONCLAIMS: ['NO_NATAL_EVENT_PREDICTION', 'NO_UNIVERSAL_ZIWEI_METHOD', 'NO_SCHOOL_WINNER']
}, null, 2));
