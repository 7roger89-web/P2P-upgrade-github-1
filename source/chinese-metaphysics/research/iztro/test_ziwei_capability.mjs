#!/usr/bin/env node
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const dir = path.dirname(fileURLToPath(import.meta.url));
const runner = path.join(dir, 'run_ziwei_capability.mjs');
function run(args) {
  const r = spawnSync(process.execPath, [runner, ...args], { encoding: 'utf8' });
  if (r.status !== 0) { process.stderr.write(r.stderr); process.exit(r.status ?? 1); }
  return JSON.parse(r.stdout);
}
const fixture = run(['--fixture', 'default']);
if (fixture.DOMAIN !== 'ZIWEI_DOUSHU') throw new Error('wrong domain');
if (fixture.BIRTH_YEAR_MUTAGEN['忌'] !== '天同') throw new Error('wrong fixture Geng 忌');
if (fixture.STRUCTURAL_OUTPUT !== 'OUTER/LOSS_INDICATOR') throw new Error('wrong bounded XQR output');
const custom = run(['--date', '2011-10-18', '--time-index', '4', '--gender', 'female']);
if (custom.INPUT_MODE !== 'CUSTOM' || custom.INPUT.dateStr !== '2011-10-18') throw new Error('custom input not honored');
if (custom.CHART_FACTS.palace_count !== 12 || Object.keys(custom.BIRTH_YEAR_MUTAGEN).length < 4) throw new Error('custom chart facts incomplete');
console.log('ZIWEI_CAPABILITY_TEST=PASS');
