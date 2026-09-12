#!/usr/bin/env node
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const runner = path.join(dir, 'run_ziwei_multilane.mjs');

function run(args) {
  const r = spawnSync(process.execPath, [runner, ...args], { encoding: 'utf8' });
  if (r.status !== 0) {
    process.stderr.write(r.stderr);
    process.exit(r.status ?? 1);
  }
  return JSON.parse(r.stdout);
}

const fixture = run(['--fixture', 'default']);
if (fixture.DOMAIN !== 'ZIWEI_DOUSHU') throw new Error('wrong domain');
if (fixture.CAPABILITY !== 'SCHOOL_ISOLATED_MULTILANE') throw new Error('wrong capability');
if (fixture.WINNER !== null || fixture.MAJORITY_VOTE !== null || fixture.SYNTHESIZED_SCHOOL_OUTPUT !== null) throw new Error('school lanes were improperly resolved');
if (fixture.LANES.XQR.LANE_ID !== 'XQR_REPO_DECLARED_6OUT_001') throw new Error('XQR lane missing');
if (fixture.LANES.QINTIAN.LANE_ID !== 'QINTIAN_REPO_DECLARED_001') throw new Error('Qintian lane missing');
if (fixture.LANES.QINTIAN.NATAL_MUTAGEN_ROLE !== '体') throw new Error('Qintian natal mutagen role drift');
if (fixture.LANES.QINTIAN.NATAL_JI.palace_group !== 'SIX_OUTER') throw new Error('fixture Qintian palace grouping drift');
if (!fixture.LANES.QINTIAN.NONCLAIMS.includes('NO_FINANCIAL_CAREER_HEALTH_OR_RELATIONSHIP_ADVICE')) throw new Error('Qintian safety boundary missing');

const custom = run(['--date', '2011-10-18', '--time-index', '4', '--gender', 'female']);
if (custom.INPUT_MODE !== 'CUSTOM') throw new Error('custom input path missing');
if (custom.COMPARISON_POLICY !== 'SIDE_BY_SIDE_ONLY') throw new Error('comparison policy drift');
if (custom.LANES.QINTIAN.SOURCE.pin !== 'ce449c0a190df09ebe2c14be8aecaac4f7cbf194') throw new Error('Qintian pin drift');

console.log('ZIWEI_MULTILANE_TEST=PASS');
