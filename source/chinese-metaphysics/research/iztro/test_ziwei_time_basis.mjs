#!/usr/bin/env node
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolveTimeBasis } from './time_basis.mjs';

const dir = path.dirname(fileURLToPath(import.meta.url));
const runner = path.join(dir, 'run_ziwei_capability.mjs');
const multilaneRunner = path.join(dir, 'run_ziwei_multilane.mjs');

function run(command, args) {
  const r = spawnSync(process.execPath, [command, ...args], { encoding: 'utf8' });
  if (r.status !== 0) {
    process.stderr.write(r.stderr);
    process.exit(r.status ?? 1);
  }
  return JSON.parse(r.stdout);
}

function runFail(command, args) {
  const r = spawnSync(process.execPath, [command, ...args], { encoding: 'utf8' });
  if (r.status === 0) throw new Error(`Expected failure: ${args.join(' ')}`);
  return r;
}

// Cross-check qualitative fixtures published by pinned ziweiknows/ziwei-chart.
// The calculation here is independent and NOAA-grounded; no GPL implementation
// code is copied or imported.
const chengdu = resolveTimeBasis({
  year: 1990, month: 1, day: 1, hour: 12, minute: 0,
  basis: 'true-solar', longitude: 104.08, utcOffset: 8,
});
if (!(chengdu.correction_minutes < -60 && chengdu.time_index === 5)) {
  throw new Error(`Chengdu reference behavior drift: ${JSON.stringify(chengdu)}`);
}

const beijing = resolveTimeBasis({
  year: 1990, month: 1, day: 1, hour: 12, minute: 0,
  basis: 'true-solar', longitude: 116.4, utcOffset: 8,
});
if (beijing.time_index !== 6) throw new Error(`Beijing reference behavior drift: ${JSON.stringify(beijing)}`);

const urumqi = resolveTimeBasis({
  year: 1990, month: 1, day: 1, hour: 2, minute: 0,
  basis: 'true-solar', longitude: 87.62, utcOffset: 8,
});
if (!urumqi.crossed_date || urumqi.corrected.year !== 1989 || urumqi.corrected.month !== 12
    || urumqi.corrected.day !== 31 || urumqi.time_index !== 12) {
  throw new Error(`Urumqi date-boundary behavior drift: ${JSON.stringify(urumqi)}`);
}

// A non-China time zone must not inherit the upstream's fixed 120E assumption.
// 105E is exactly the standard meridian for UTC+7, so longitude/time-zone
// correction is zero; only equation-of-time remains.
const utc7StandardMeridian = resolveTimeBasis({
  year: 1990, month: 1, day: 1, hour: 12, minute: 0,
  basis: 'true-solar', longitude: 105, utcOffset: 7,
});
if (Math.abs(utc7StandardMeridian.longitude_timezone_minutes) > 1e-9) {
  throw new Error(`UTC+7 standard-meridian correction must be zero: ${JSON.stringify(utc7StandardMeridian)}`);
}

const civilArgs = [
  '--date', '1990-01-01', '--civil-hour', '12', '--civil-minute', '0',
  '--gender', 'female', '--time-basis', 'civil', '--algorithm', 'default',
];
const solarArgs = [
  '--date', '1990-01-01', '--civil-hour', '12', '--civil-minute', '0',
  '--gender', 'female', '--time-basis', 'true-solar', '--longitude', '104.08', '--utc-offset', '8',
  '--algorithm', 'default',
];
const civil = run(runner, civilArgs);
const solar = run(runner, solarArgs);
if (civil.TIME_BASIS.basis !== 'CIVIL_TIME' || civil.INPUT.timeIndex !== 6) throw new Error('civil clock path drift');
if (solar.TIME_BASIS.basis !== 'TRUE_SOLAR_TIME' || solar.INPUT.timeIndex !== 5) throw new Error('true-solar path did not reach iztro');
if (solar.TIME_BASIS.source.authority !== 'NOAA_GML_GENERAL_SOLAR_POSITION_CALCULATIONS') throw new Error('time-basis provenance missing');
if (solar.PROFILE_ID !== civil.PROFILE_ID) throw new Error('time basis silently changed algorithm profile');
const civilFingerprint = JSON.stringify([civil.CHART_FACTS, civil.TARGET_PALACE]);
const solarFingerprint = JSON.stringify([solar.CHART_FACTS, solar.TARGET_PALACE]);
if (civilFingerprint === solarFingerprint) throw new Error('boundary-crossing time correction did not materially change chart facts');

const multilane = run(multilaneRunner, solarArgs);
if (multilane.TIME_BASIS.basis !== 'TRUE_SOLAR_TIME' || multilane.INPUT.timeIndex !== 5) throw new Error('multilane lost resolved time basis');
if (!multilane.LANES.XQR || !multilane.LANES.QINTIAN) throw new Error('method lanes missing after time-basis resolution');
if (multilane.WINNER !== null || multilane.MAJORITY_VOTE !== null) throw new Error('time-basis slice introduced school resolution');

const missingLongitude = runFail(runner, [
  '--date', '1990-01-01', '--civil-hour', '12', '--gender', 'female',
  '--time-basis', 'true-solar', '--utc-offset', '8',
]);
if (!missingLongitude.stderr.includes('TRUE_SOLAR requires --longitude')) throw new Error('missing longitude did not fail clearly');

const legacy = run(runner, ['--date', '2011-10-18', '--time-index', '4', '--gender', 'female']);
if (legacy.TIME_BASIS.basis !== 'EXPLICIT_IZTRO_TIME_INDEX' || legacy.INPUT.timeIndex !== 4) throw new Error('legacy explicit time-index path regressed');

console.log('ZIWEI_TIME_BASIS_TEST=PASS');
