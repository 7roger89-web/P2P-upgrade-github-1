#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL, fileURLToPath } from 'node:url';
const PIN='509fc43001a503d17a37db07bc56e069b1ff1c4f';
const dir=path.dirname(fileURLToPath(import.meta.url));
const upstream=path.resolve(dir,'../../upstreams/plum-cg');
function fail(msg,code=2){console.error(msg);process.exit(code)}
function arg(name){const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:undefined}
function has(name){return process.argv.includes(name)}
if(!fs.existsSync(upstream)) fail(`Pinned upstream missing: ${upstream}`);
let head;try{head=execFileSync('git',['-C',upstream,'rev-parse','HEAD'],{encoding:'utf8'}).trim()}catch{fail(`Cannot verify pinned upstream: ${upstream}`)}
if(head!==PIN) fail(`Pinned upstream SHA mismatch: expected ${PIN}, got ${head}`);
const entry=path.join(upstream,'dist','index.esm.js');if(!fs.existsSync(entry)) fail(`Pinned upstream build missing: ${entry}`);
const mod=await import(pathToFileURL(entry).href);
for(const n of ['calcOriginCFigure','calcCFigure','calcOriginGFigure','calcGFigure']) if(typeof mod[n]!=='function') fail(`Pinned plum-cg API missing: ${n}`);
const fixture=arg('--fixture');const customRequested=has('--format-string')||has('--yang-lines');
if(fixture&&customRequested) fail('Use either --fixture or custom --format-string/--yang-lines, not both');
let formatString,yangLines,inputMode,conventionId;
if(fixture){
  if(fixture!=='zhen-4') fail(`Unknown fixture: ${fixture}`);
  formatString='444';yangLines=2;inputMode='FIXTURE';conventionId='PREHEAVEN_ZHEN_4_AFTERHEAVEN_ZHEN_3';
}else{
  formatString=arg('--format-string');const rawYang=arg('--yang-lines');
  if(!formatString||rawYang===undefined) fail('Custom usage: --format-string XYZ --yang-lines 0..6');
  if(!/^[1-8][1-8][1-6]$/.test(formatString)) fail(`Invalid --format-string: ${formatString}`);
  yangLines=Number(rawYang);if(!Number.isInteger(yangLines)||yangLines<0||yangLines>6) fail(`Invalid --yang-lines: ${rawYang}`);
  inputMode='CUSTOM';conventionId='EXPLICIT_FORMAT_STRING_INPUT';
}
let originalC,c,originalG,g;
try{originalC=mod.calcOriginCFigure(yangLines);c=mod.calcCFigure(formatString);originalG=mod.calcOriginGFigure(yangLines);g=mod.calcGFigure(formatString)}catch(err){fail(`plum-cg rejected input: ${err?.message??err}`,1)}
if(inputMode==='FIXTURE'&&(originalC!==168||c!==7572||originalG!==704||g!==30986)) fail(`CEGUI fixture drift: ${JSON.stringify({originalC,c,originalG,g})}`,1);
console.log(JSON.stringify({DOMAIN:'CEGUI',ENGINE_PIN:PIN,INPUT_MODE:inputMode,INPUT:{format_string:formatString,yang_lines:yangLines},CONVENTION_ID:conventionId,ORIGINAL_CE:originalC,CE_NUMBER:c,ORIGINAL_GUI:originalG,GUI_NUMBER:g,FORMULA_TRACE:[`calcOriginCFigure(${yangLines})`,`calcCFigure("${formatString}")`,`calcOriginGFigure(${yangLines})`,`calcGFigure("${formatString}")`],NUMBER_5_CONVENTION:'EXPLICIT_UNRESOLVED_VARIANT',PROVENANCE_STATUS:'PARTIAL_GOOD',PREDICTIVE_STATUS:'NOT_APPLICABLE_NOT_TESTED'},null,2));
