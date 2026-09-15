#!/usr/bin/env node
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const runner = path.join(dir, 'run_ziwei_multilane.mjs');
const EXPECTED_XQR_PIN = '7b8364bbd79a11e852899893ac5749a83be62836';
const EXPECTED_QINTIAN_PIN = 'ce449c0a190df09ebe2c14be8aecaac4f7cbf194';

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
if (fixture.PROFILE_ID !== 'IZTRO_DEFAULT_001') throw new Error('default profile drift');
if (fixture.WINNER !== null || fixture.MAJORITY_VOTE !== null || fixture.SYNTHESIZED_SCHOOL_OUTPUT !== null) throw new Error('school lanes were improperly resolved');
if (fixture.LANES.XQR.LANE_ID !== 'XQR_REPO_DECLARED_6OUT_001') throw new Error('XQR lane missing');
if (fixture.LANES.XQR.SOURCE.repo !== 'ZhangZangQian/xu-quanren') throw new Error('XQR repo drift');
if (fixture.LANES.XQR.SOURCE.pin !== EXPECTED_XQR_PIN) throw new Error('XQR pin drift');
if (fixture.LANES.XQR.provenance_status !== 'DIRECT_SOURCE_BOUND') throw new Error('XQR provenance status drift');
if (!Array.isArray(fixture.LANES.XQR.rule_evidence) || fixture.LANES.XQR.rule_evidence.length !== 2) throw new Error('XQR rule evidence missing');
for (const ev of fixture.LANES.XQR.rule_evidence) {
  if (ev.repo !== 'ZhangZangQian/xu-quanren' || ev.pin !== EXPECTED_XQR_PIN || ev.support_status !== 'DIRECT_SOURCE_SUPPORT') {
    throw new Error(`XQR rule evidence drift for ${ev.rule_id}`);
  }
}

if (fixture.LANES.QINTIAN.LANE_ID !== 'QINTIAN_REPO_DECLARED_001') throw new Error('Qintian lane missing');
if (fixture.LANES.QINTIAN.SOURCE.pin !== EXPECTED_QINTIAN_PIN) throw new Error('Qintian pin drift');
if (fixture.LANES.QINTIAN.NATAL_MUTAGEN_ROLE !== '体') throw new Error('Qintian natal mutagen role drift');
if (fixture.LANES.QINTIAN.NATAL_JI.palace_group !== 'SIX_OUTER') throw new Error('fixture Qintian palace grouping drift');
if (!fixture.LANES.QINTIAN.NONCLAIMS.includes('NO_FINANCIAL_CAREER_HEALTH_OR_RELATIONSHIP_ADVICE')) throw new Error('Qintian safety boundary missing');

const custom = run(['--date', '2011-10-18', '--time-index', '4', '--gender', 'female']);
if (custom.INPUT_MODE !== 'CUSTOM') throw new Error('custom input path missing');
if (custom.COMPARISON_POLICY !== 'SIDE_BY_SIDE_ONLY') throw new Error('comparison policy drift');
if (custom.LANES.XQR.SOURCE.pin !== EXPECTED_XQR_PIN) throw new Error('XQR pin drift under custom input');
if (custom.LANES.QINTIAN.SOURCE.pin !== EXPECTED_QINTIAN_PIN) throw new Error('Qintian pin drift');

const zhongzhou = run(['--fixture', 'default', '--algorithm', 'zhongzhou']);
if (zhongzhou.PROFILE_ID !== 'IZTRO_ZHONGZHOU_MECHANICAL_001') throw new Error('Zhongzhou profile not propagated');
if (zhongzhou.LANES.XQR.LANE_ID !== 'XQR_REPO_DECLARED_6OUT_001' || zhongzhou.LANES.QINTIAN.LANE_ID !== 'QINTIAN_REPO_DECLARED_001') throw new Error('method lanes missing under Zhongzhou profile');
if (zhongzhou.LANES.XQR.SOURCE.pin !== EXPECTED_XQR_PIN) throw new Error('XQR pin changed across profile');
if (zhongzhou.LANES.XQR.SOURCE.repo !== fixture.LANES.XQR.SOURCE.repo) throw new Error('XQR repo changed across profile');
if (zhongzhou.WINNER !== null || zhongzhou.MAJORITY_VOTE !== null || zhongzhou.SYNTHESIZED_SCHOOL_OUTPUT !== null) throw new Error('Zhongzhou profile caused improper school resolution');
if (zhongzhou.INPUT.dateStr !== fixture.INPUT.dateStr || zhongzhou.INPUT.timeIndex !== fixture.INPUT.timeIndex || zhongzhou.INPUT.gender !== fixture.INPUT.gender) throw new Error('Zhongzhou profile changed birth input');
if (zhongzhou.DETERMINISTIC_CHART_FACTS.palace_count !== 12) throw new Error('Zhongzhou chart packet incomplete');

console.log('ZIWEI_MULTILANE_TEST=PASS');
