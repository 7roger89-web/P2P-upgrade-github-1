#!/usr/bin/env node
import path from 'node:path';import{spawnSync}from'node:child_process';import{fileURLToPath}from'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));const runner=path.join(dir,'run_cegui_capability.mjs');
function run(args){const r=spawnSync(process.execPath,[runner,...args],{encoding:'utf8'});if(r.status!==0){process.stderr.write(r.stderr);process.exit(r.status??1)}return JSON.parse(r.stdout)}
const fixture=run(['--fixture','zhen-4']);if(fixture.DOMAIN!=='CEGUI'||fixture.ORIGINAL_CE!==168||fixture.CE_NUMBER!==7572||fixture.ORIGINAL_GUI!==704||fixture.GUI_NUMBER!==30986)throw new Error('CEGUI fixture mismatch');
const custom=run(['--format-string','444','--yang-lines','2']);if(custom.INPUT_MODE!=='CUSTOM'||custom.CE_NUMBER!==7572||custom.GUI_NUMBER!==30986)throw new Error('CEGUI custom input mismatch');
console.log('CEGUI_CAPABILITY_TEST=PASS');
