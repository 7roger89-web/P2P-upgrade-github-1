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
if (!fs.existsSync(upstream)) fail(`Pinned upstream missing: ${upstream}`);
let head;
try { head = execFileSync('git', ['-C', upstream, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); }
catch { fail(`Cannot verify pinned upstream: ${upstream}`); }
if (head !== PIN) fail(`Pinned upstream SHA mismatch: expected ${PIN}, got ${head}`);

const fixture = process.argv.includes('--fixture') ? process.argv[process.argv.indexOf('--fixture') + 1] : 'default';
if (fixture !== 'default') fail(`Unknown fixture: ${fixture}`);

const builtEntry = path.join(upstream, 'lib', 'index.js');
if (!fs.existsSync(builtEntry)) fail(`Pinned upstream build missing: ${builtEntry}`);
const require = createRequire(import.meta.url);
const { astro } = require(builtEntry);
if (!astro?.bySolar) fail('Pinned iztro API missing: astro.bySolar');

const input = { dateStr: '2010-10-18', timeIndex: 4, gender: 'female' };
const chart = astro.bySolar(input.dateStr, input.timeIndex, input.gender);
const palaces = chart.palaces ?? [];
const mutagen = {};
let tiantongPalace = null;
for (const palace of palaces) {
  for (const star of [...(palace.majorStars ?? []), ...(palace.minorStars ?? [])]) {
    if (star?.mutagen) mutagen[star.mutagen] = star.name;
    if (star?.name === '天同') tiantongPalace = palace.name;
  }
}
const expected = { '禄': '太阳', '权': '武曲', '科': '太阴', '忌': '天同' };
for (const [k, v] of Object.entries(expected)) {
  if (mutagen[k] !== v) fail(`Unexpected Geng mutagen ${k}: expected ${v}, got ${mutagen[k]}`, 1);
}
const sixOuter = new Set(['兄弟', '夫妻', '子女', '迁移', '仆役', '交友', '父母']);
if (!tiantongPalace) fail('Cannot locate 天同 in actual chart output', 1);
const targetClass = sixOuter.has(tiantongPalace) ? 'SIX_OUTER' : 'NOT_SIX_OUTER';
const structuralOutput = targetClass === 'SIX_OUTER' ? 'OUTER/LOSS_INDICATOR' : 'UNEXPECTED_TARGET_CLASS';
if (structuralOutput !== 'OUTER/LOSS_INDICATOR') fail(`XQR bounded lane fixture drift: 天同 palace=${tiantongPalace}`, 1);

console.log(JSON.stringify({
  DOMAIN: 'ZIWEI_DOUSHU',
  ENGINE_PIN: PIN,
  INPUT: input,
  PROFILE_ID: 'IZTRO_DEFAULT_001',
  FIVE_ELEMENTS_CLASS: chart.fiveElementsClass,
  GENG_SIHUA: mutagen,
  METHOD_LANE: 'XQR_REPO_DECLARED_6OUT_001',
  RULE_TRACE: ['XQR_R1_PALACE_BEFORE_STAR', 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER'],
  TARGET_STAR: '天同',
  TARGET_PALACE: tiantongPalace,
  BIRTH_YEAR_JI_TARGET_CLASS: targetClass,
  STRUCTURAL_OUTPUT: structuralOutput,
  PROVENANCE_STATUS: 'PARTIAL',
  PREDICTIVE_STATUS: 'NOT_TESTED',
  NONCLAIMS: ['NO_NATAL_EVENT_PREDICTION', 'NO_UNIVERSAL_ZIWEI_METHOD', 'NO_SCHOOL_WINNER']
}, null, 2));
