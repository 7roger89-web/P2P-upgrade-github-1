#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { resolveTimeBasis } from './time_basis.mjs';

const PIN = '2c7ef9be669df7b19d1799f4dce335fed3794f78';
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const upstream = path.resolve(scriptDir, '../../upstreams/iztro');

function fail(msg, code = 2) { console.error(msg); process.exit(code); }
function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : undefined; }
function has(name) { return process.argv.includes(name); }
function formatDate({ year, month, day }) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}
function parseDate(dateStr) {
  const match = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(dateStr ?? '');
  if (!match) fail(`Invalid --date: ${dateStr}`);
  return { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) };
}

if (!fs.existsSync(upstream)) fail(`Pinned upstream missing: ${upstream}`);
let head;
try { head = execFileSync('git', ['-C', upstream, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); }
catch { fail(`Cannot verify pinned upstream: ${upstream}`); }
if (head !== PIN) fail(`Pinned upstream SHA mismatch: expected ${PIN}, got ${head}`);

const XQR_PIN = '7b8364bbd79a11e852899893ac5749a83be62836';
const XQR_REPO = 'ZhangZangQian/xu-quanren';
const xqrUpstream = path.resolve(scriptDir, '../../upstreams/xu-quanren');

if (!fs.existsSync(xqrUpstream)) fail(`Pinned xu-quanren upstream missing: ${xqrUpstream}`);
let xqrHead;
try { xqrHead = execFileSync('git', ['-C', xqrUpstream, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); }
catch { fail(`Cannot verify pinned xu-quanren upstream: ${xqrUpstream}`); }
if (xqrHead !== XQR_PIN) fail(`Pinned xu-quanren upstream SHA mismatch: expected ${XQR_PIN}, got ${xqrHead}`);

const XQR_RULE_EVIDENCE = [
  {
    rule_id: 'XQR_R1_PALACE_BEFORE_STAR',
    support_status: 'DIRECT_SOURCE_SUPPORT',
    repo: XQR_REPO,
    pin: XQR_PIN,
    source_repo: XQR_REPO,
    source_pin: XQR_PIN,
    source_path: 'SKILL.md',
    source_anchor: '### 优先级法则（四条铁律）',
    supported_claim: 'Evaluates palace scope prior to taking mutagen phenomena and star properties (先定宫职范畴，再取象，最后合星).',
  },
  {
    rule_id: 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER',
    support_status: 'DIRECT_SOURCE_SUPPORT',
    repo: XQR_REPO,
    pin: XQR_PIN,
    source_repo: XQR_REPO,
    source_pin: XQR_PIN,
    source_path: 'SKILL.md',
    source_anchor: '### 解读法则',
    supported_claim: 'Classifies mutagen placement by palace inner/outer boundary where Ji entering six outer palaces indicates loss/dispersion (忌入六内主得，忌入六外主失; 六内/六外分得失聚散).',
  },
];

for (const ev of XQR_RULE_EVIDENCE) {
  const fullPath = path.join(xqrUpstream, ev.source_path);
  if (!fs.existsSync(fullPath)) fail(`XQR source path missing: ${fullPath}`);
  const content = fs.readFileSync(fullPath, 'utf8');
  if (!content.includes(ev.source_anchor)) fail(`XQR source anchor missing: ${ev.source_anchor}`);
}

const builtEntry = path.join(upstream, 'lib', 'index.js');
if (!fs.existsSync(builtEntry)) fail(`Pinned upstream build missing: ${builtEntry}`);
const require = createRequire(import.meta.url);
const { astro } = require(builtEntry);
if (!astro?.withOptions) fail('Pinned iztro API missing: astro.withOptions');

const fixture = arg('--fixture');
const rawClockRequested = has('--civil-hour') || has('--civil-minute') || has('--longitude') || has('--utc-offset') || has('--time-basis');
const customRequested = has('--date') || has('--time-index') || has('--gender') || rawClockRequested;
if (fixture && customRequested) fail('Use either --fixture or custom birth input, not both');
const algorithm = arg('--algorithm') ?? 'default';
if (!['default', 'zhongzhou'].includes(algorithm)) fail(`Invalid --algorithm: ${algorithm}`);

let input;
let sourceInput;
let timeBasis;
let inputMode;
if (fixture) {
  if (fixture !== 'default') fail(`Unknown fixture: ${fixture}`);
  input = { dateStr: '2010-10-18', timeIndex: 4, gender: 'female' };
  sourceInput = { ...input };
  timeBasis = {
    basis: 'FIXTURE_EXPLICIT_IZTRO_TIME_INDEX',
    correction_minutes: 0,
    time_index: 4,
    crossed_date: false,
  };
  inputMode = 'FIXTURE';
} else {
  const dateStr = arg('--date');
  const gender = arg('--gender');
  const timeIndexRaw = arg('--time-index');
  const civilHourRaw = arg('--civil-hour');
  const civilMinuteRaw = arg('--civil-minute');
  const requestedBasis = arg('--time-basis') ?? 'civil';
  const longitudeRaw = arg('--longitude');
  const utcOffsetRaw = arg('--utc-offset');

  if (!dateStr || !gender) {
    fail('Custom usage requires --date YYYY-MM-DD and --gender male|female plus either --time-index or --civil-hour');
  }
  if (!['male', 'female'].includes(gender)) fail(`Invalid --gender: ${gender}`);
  const dateParts = parseDate(dateStr);
  const hasTimeIndex = timeIndexRaw !== undefined;
  const hasCivilHour = civilHourRaw !== undefined;
  if (hasTimeIndex === hasCivilHour) fail('Choose exactly one time input: --time-index OR --civil-hour');

  if (hasTimeIndex) {
    if (rawClockRequested) fail('Do not combine --time-index with civil-clock/time-basis flags; --time-index is already resolved');
    const timeIndex = Number(timeIndexRaw);
    if (!Number.isInteger(timeIndex) || timeIndex < 0 || timeIndex > 12) fail(`Invalid --time-index: ${timeIndexRaw}`);
    input = { dateStr, timeIndex, gender };
    sourceInput = { ...input };
    timeBasis = {
      basis: 'EXPLICIT_IZTRO_TIME_INDEX',
      correction_minutes: 0,
      time_index: timeIndex,
      crossed_date: false,
    };
  } else {
    const civilHour = Number(civilHourRaw);
    const civilMinute = civilMinuteRaw === undefined ? 0 : Number(civilMinuteRaw);
    if (!Number.isInteger(civilHour) || civilHour < 0 || civilHour > 23) fail(`Invalid --civil-hour: ${civilHourRaw}`);
    if (!Number.isInteger(civilMinute) || civilMinute < 0 || civilMinute > 59) fail(`Invalid --civil-minute: ${civilMinuteRaw}`);
    if (!['civil', 'true-solar'].includes(requestedBasis)) fail(`Invalid --time-basis: ${requestedBasis}`);
    if (requestedBasis === 'civil' && (longitudeRaw !== undefined || utcOffsetRaw !== undefined)) {
      fail('--longitude/--utc-offset are only valid with --time-basis true-solar');
    }
    const longitude = longitudeRaw === undefined ? undefined : Number(longitudeRaw);
    const utcOffset = utcOffsetRaw === undefined ? undefined : Number(utcOffsetRaw);
    try {
      timeBasis = resolveTimeBasis({
        ...dateParts,
        hour: civilHour,
        minute: civilMinute,
        basis: requestedBasis,
        longitude,
        utcOffset,
      });
    } catch (err) {
      fail(`Time-basis resolution failed: ${err?.message ?? err}`);
    }
    input = {
      dateStr: formatDate(timeBasis.corrected),
      timeIndex: timeBasis.time_index,
      gender,
    };
    sourceInput = {
      dateStr,
      civilHour,
      civilMinute,
      gender,
      requestedTimeBasis: requestedBasis,
      longitude: longitude ?? null,
      utcOffset: utcOffset ?? null,
    };
  }
  inputMode = 'CUSTOM';
}

const profileConfig = {
  yearDivide: 'normal',
  horoscopeDivide: 'normal',
  ageDivide: 'normal',
  dayDivide: 'forward',
  algorithm,
};

let chart;
try {
  chart = astro.withOptions({
    type: 'solar',
    dateStr: input.dateStr,
    timeIndex: input.timeIndex,
    gender: input.gender,
    config: profileConfig,
  });
} catch (err) { fail(`iztro rejected input/profile: ${err?.message ?? err}`, 1); }

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

if (inputMode === 'FIXTURE' && algorithm === 'default') {
  const expected = { '禄': '太阳', '权': '武曲', '科': '太阴', '忌': '天同' };
  for (const [k, v] of Object.entries(expected)) if (mutagen[k] !== v) fail(`Unexpected Geng mutagen ${k}: expected ${v}, got ${mutagen[k]}`, 1);
  if (structuralOutput !== 'OUTER/LOSS_INDICATOR') fail(`XQR bounded lane fixture drift: ${jiStar} palace=${jiPalace}`, 1);
}

console.log(JSON.stringify({
  DOMAIN: 'ZIWEI_DOUSHU', ENGINE_PIN: PIN, INPUT_MODE: inputMode,
  SOURCE_INPUT: sourceInput,
  INPUT: input,
  TIME_BASIS: timeBasis,
  PROFILE_ID: algorithm === 'zhongzhou' ? 'IZTRO_ZHONGZHOU_MECHANICAL_001' : 'IZTRO_DEFAULT_001',
  PROFILE_CONFIG: profileConfig,
  CHART_FACTS: {
    five_elements_class: chart.fiveElementsClass,
    palace_count: palaces.length,
    palace_names: palaces.map((p) => p.name),
    soul: chart.soul,
    body: chart.body,
    earthly_branch_of_soul_palace: chart.earthlyBranchOfSoulPalace,
    earthly_branch_of_body_palace: chart.earthlyBranchOfBodyPalace,
  },
  BIRTH_YEAR_MUTAGEN: mutagen,
  METHOD_LANE: 'XQR_REPO_DECLARED_6OUT_001',
  RULE_TRACE: ['XQR_R1_PALACE_BEFORE_STAR', 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER'],
  RULE_EVIDENCE: XQR_RULE_EVIDENCE,
  TARGET_STAR: jiStar, TARGET_PALACE: jiPalace, BIRTH_YEAR_JI_TARGET_CLASS: targetClass,
  STRUCTURAL_OUTPUT: structuralOutput, PROVENANCE_STATUS: 'DIRECT_SOURCE_BOUND', PREDICTIVE_STATUS: 'NOT_TESTED',
  NONCLAIMS: [
    'NO_NATAL_EVENT_PREDICTION',
    'NO_UNIVERSAL_ZIWEI_METHOD',
    'NO_SCHOOL_WINNER',
    'TRUE_SOLAR_TIME_DOES_NOT_INFER_LONGITUDE_OR_UTC_OFFSET',
  ]
}, null, 2));
