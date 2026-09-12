#!/usr/bin/env node
import path from 'node:path'; import { spawnSync } from 'node:child_process'; import { fileURLToPath } from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url)); const r=spawnSync(process.execPath,[path.join(dir,'run_cegui_capability.mjs'),'--fixture','zhen-4'],{encoding:'utf8'});
if(r.status!==0){process.stderr.write(r.stderr);process.exit(r.status??1)} const o=JSON.parse(r.stdout);
if(o.DOMAIN!=='CEGUI'||o.ORIGINAL_CE!==168||o.CE_NUMBER!==7572||o.ORIGINAL_GUI!==704||o.GUI_NUMBER!==30986) throw new Error('CEGUI fixture mismatch');
console.log('CEGUI_CAPABILITY_TEST=PASS');
