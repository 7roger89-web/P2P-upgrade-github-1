#!/usr/bin/env node
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const dir = path.dirname(fileURLToPath(import.meta.url));
const r = spawnSync(process.execPath, [path.join(dir, 'run_ziwei_capability.mjs'), '--fixture', 'default'], { encoding: 'utf8' });
if (r.status !== 0) { process.stderr.write(r.stderr); process.exit(r.status ?? 1); }
const out = JSON.parse(r.stdout);
if (out.DOMAIN !== 'ZIWEI_DOUSHU') throw new Error('wrong domain');
if (out.GENG_SIHUA['忌'] !== '天同') throw new Error('wrong Geng 忌');
if (out.STRUCTURAL_OUTPUT !== 'OUTER/LOSS_INDICATOR') throw new Error('wrong bounded XQR output');
console.log('ZIWEI_CAPABILITY_TEST=PASS');
