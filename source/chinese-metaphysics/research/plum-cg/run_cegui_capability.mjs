#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL, fileURLToPath } from 'node:url';
const PIN='509fc43001a503d17a37db07bc56e069b1ff1c4f';
const dir=path.dirname(fileURLToPath(import.meta.url));
const upstream=path.resolve(dir,'../../upstreams/plum-cg');
function fail(msg,code=2){console.error(msg);process.exit(code)}
if(!fs.existsSync(upstream)) fail(`Pinned upstream missing: ${upstream}`);
let head; try{head=execFileSync('git',['-C',upstream,'rev-parse','HEAD'],{encoding:'utf8'}).trim()}catch{fail(`Cannot verify pinned upstream: ${upstream}`)}
if(head!==PIN) fail(`Pinned upstream SHA mismatch: expected ${PIN}, got ${head}`);
const fixture=process.argv.includes('--fixture')?process.argv[process.argv.indexOf('--fixture')+1]:'zhen-4';
if(fixture!=='zhen-4') fail(`Unknown fixture: ${fixture}`);
const entry=path.join(upstream,'dist','index.esm.js'); if(!fs.existsSync(entry)) fail(`Pinned upstream build missing: ${entry}`);
const mod=await import(pathToFileURL(entry).href);
for(const n of ['calcOriginCFigure','calcCFigure','calcOriginGFigure','calcGFigure']) if(typeof mod[n]!=='function') fail(`Pinned plum-cg API missing: ${n}`);
const originalC=mod.calcOriginCFigure(2); const c=mod.calcCFigure('444'); const originalG=mod.calcOriginGFigure(2); const g=mod.calcGFigure('444');
if(originalC!==168||c!==7572||originalG!==704||g!==30986) fail(`CEGUI fixture drift: ${JSON.stringify({originalC,c,originalG,g})}`,1);
console.log(JSON.stringify({DOMAIN:'CEGUI',ENGINE_PIN:PIN,INPUT:{main_hexagram:'震为雷',moving_line:4,format_string:'444',yang_lines:2,yin_lines:4},CONVENTION_ID:'PREHEAVEN_ZHEN_4_AFTERHEAVEN_ZHEN_3',ORIGINAL_CE:originalC,CE_NUMBER:c,ORIGINAL_GUI:originalG,GUI_NUMBER:g,FORMULA_TRACE:['calcOriginCFigure(2)','calcCFigure("444")','calcOriginGFigure(2)','calcGFigure("444")'],NUMBER_5_CONVENTION:'EXPLICIT_UNRESOLVED_VARIANT',PROVENANCE_STATUS:'PARTIAL_GOOD',PREDICTIVE_STATUS:'NOT_APPLICABLE_NOT_TESTED'},null,2));
