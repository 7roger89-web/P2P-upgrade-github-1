#!/usr/bin/env node
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const dir=path.dirname(fileURLToPath(import.meta.url));
const runner=path.join(dir,'run_cegui_capability.mjs');

function run(args){
  const r=spawnSync(process.execPath,[runner,...args],{encoding:'utf8'});
  if(r.status!==0){process.stderr.write(r.stderr);process.exit(r.status??1)}
  return JSON.parse(r.stdout);
}
function runFail(args){
  const r=spawnSync(process.execPath,[runner,...args],{encoding:'utf8'});
  if(r.status===0) throw new Error(`Expected failure: ${args.join(' ')}`);
  return r;
}

const fixture=run(['--fixture','zhen-4']);
if(fixture.DOMAIN!=='CEGUI'||fixture.ORIGINAL_CE!==168||fixture.CE_NUMBER!==7572||fixture.ORIGINAL_GUI!==704||fixture.GUI_NUMBER!==30986) throw new Error('CEGUI fixture mismatch');
if(fixture.INPUT.yang_lines_derived!==2) throw new Error('fixture yang-line derivation mismatch');
if(fixture.NUMBER_5_CONVENTION.SELECTION_STATUS!=='UNSELECTED_NO_SILENT_NORMALIZATION') throw new Error('number-5 default must remain unselected');
if(JSON.stringify(fixture.NUMBER_5_CONVENTION.METHOD_2.CE_TRIGRAMS)!==JSON.stringify(['离','艮','离','离'])) throw new Error('method2 CE mapping mismatch');
if(JSON.stringify(fixture.NUMBER_5_CONVENTION.METHOD_1.YIN_DAY.CE_TRIGRAMS)!==JSON.stringify(['离','坤','离','离'])) throw new Error('method1 yin CE mapping mismatch');

const customDerived=run(['--format-string','444']);
if(customDerived.INPUT_MODE!=='CUSTOM'||customDerived.INPUT.yang_lines_derived!==2||customDerived.CE_NUMBER!==7572||customDerived.GUI_NUMBER!==30986) throw new Error('CEGUI derived custom input mismatch');

const customCompat=run(['--format-string','444','--yang-lines','2']);
if(customCompat.INPUT.yang_lines_supplied_for_compatibility!==2) throw new Error('compatible --yang-lines not recorded');

const mismatch=runFail(['--format-string','111','--yang-lines','0']);
if(!mismatch.stderr.includes('--yang-lines mismatch')) throw new Error('mismatched yang-lines must be rejected explicitly');

const method1Yin=run(['--format-string','444','--five-method','method1','--day-stem','yin']);
if(method1Yin.NUMBER_5_CONVENTION.SELECTION_STATUS!=='EXPLICITLY_SELECTED') throw new Error('method1 selection missing');
if(method1Yin.NUMBER_5_CONVENTION.SELECTED.METHOD_ID!=='METHOD_1_DAY_STEM_YIN') throw new Error('method1 yin selection mismatch');
if(JSON.stringify(method1Yin.NUMBER_5_CONVENTION.SELECTED.CE_TRIGRAMS)!==JSON.stringify(['离','坤','离','离'])) throw new Error('method1 yin selected CE mapping mismatch');

const method2=run(['--format-string','444','--five-method','method2']);
if(method2.NUMBER_5_CONVENTION.SELECTED.METHOD_ID!=='METHOD_2_CE5_GEN_GUI5_KUN') throw new Error('method2 selection mismatch');
if(JSON.stringify(method2.NUMBER_5_CONVENTION.SELECTED.CE_TRIGRAMS)!==JSON.stringify(['离','艮','离','离'])) throw new Error('method2 selected CE mapping mismatch');

console.log('CEGUI_CAPABILITY_TEST=PASS');
