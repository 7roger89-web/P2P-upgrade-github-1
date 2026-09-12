#!/usr/bin/env node
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const runner = path.join(dir, 'run_ziwei_algorithm_compare.mjs');
const r = spawnSync(process.execPath, [runner], { encoding: 'utf8' });
if (r.status !== 0) {
  process.stderr.write(r.stderr);
  process.exit(r.status ?? 1);
}
const packet = JSON.parse(r.stdout);
if (packet.DOMAIN !== 'ZIWEI_DOUSHU') throw new Error('wrong domain');
if (packet.CAPABILITY !== 'IZTRO_DEFAULT_VS_ZHONGZHOU_MECHANICAL_PROFILE_COMPARE') throw new Error('wrong capability');
if (packet.DEFAULT_PROFILE.INPUT.dateStr !== packet.ZHONGZHOU_PROFILE.INPUT.dateStr) throw new Error('profile input drift');
if (packet.DEFAULT_PROFILE.PROFILE_ID !== 'IZTRO_DEFAULT_MECHANICAL_001') throw new Error('default profile id drift');
if (packet.ZHONGZHOU_PROFILE.PROFILE_ID !== 'IZTRO_ZHONGZHOU_MECHANICAL_001') throw new Error('zhongzhou profile id drift');
if (packet.DEFAULT_PROFILE.CONFIG.algorithm !== 'default') throw new Error('default algorithm not explicit');
if (packet.ZHONGZHOU_PROFILE.CONFIG.algorithm !== 'zhongzhou') throw new Error('zhongzhou algorithm not explicit');
for (const p of [packet.DEFAULT_PROFILE, packet.ZHONGZHOU_PROFILE]) {
  if (p.CONFIG.yearDivide !== 'normal' || p.CONFIG.horoscopeDivide !== 'normal' || p.CONFIG.ageDivide !== 'normal' || p.CONFIG.dayDivide !== 'forward') {
    throw new Error('shared mechanical config drift');
  }
  if (p.MECHANICAL_FACTS.palace_count !== 12) throw new Error('invalid palace count');
}
if (packet.ISOLATION !== 'EACH_PROFILE_EXECUTED_IN_A_FRESH_NODE_PROCESS') throw new Error('profile isolation not proven');
if (!(packet.MATERIAL_DIFF_COUNT > 0)) throw new Error('zhongzhou profile produced no material mechanical difference');
if (!Array.isArray(packet.DETERMINISTIC_DIFF.star_location_differences) || packet.DETERMINISTIC_DIFF.star_location_differences.length < 1) {
  throw new Error('expected at least one deterministic star-location/set difference');
}
if (packet.PREDICTIVE_STATUS !== 'NOT_TESTED') throw new Error('predictive status overclaimed');
console.log('ZIWEI_ALGORITHM_COMPARE_TEST=PASS');
