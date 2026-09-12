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
let head;
try{head=execFileSync('git',['-C',upstream,'rev-parse','HEAD'],{encoding:'utf8'}).trim()}
catch{fail(`Cannot verify pinned upstream: ${upstream}`)}
if(head!==PIN) fail(`Pinned upstream SHA mismatch: expected ${PIN}, got ${head}`);

const entry=path.join(upstream,'dist','index.esm.js');
if(!fs.existsSync(entry)) fail(`Pinned upstream build missing: ${entry}`);
const mod=await import(pathToFileURL(entry).href);
for(const n of [
  'calcOriginCFigure','calcCFigure','calcOriginGFigure','calcGFigure',
  'getTrigramFromCFigure','getTrigramFromGFigure'
]) if(typeof mod[n]!=='function') fail(`Pinned plum-cg API missing: ${n}`);

// Exact mechanical fact from pinned upstream src/trigram.ts:
// pre_num -> number of yang lines in that trigram.
const PREHEAVEN_YANG_LINES=Object.freeze({1:3,2:2,3:2,4:1,5:2,6:1,7:1,8:0});
function deriveYangLines(formatString){
  return PREHEAVEN_YANG_LINES[Number(formatString[0])] + PREHEAVEN_YANG_LINES[Number(formatString[1])];
}

const fixture=arg('--fixture');
const customRequested=has('--format-string')||has('--yang-lines');
const fiveMethod=arg('--five-method');
const dayStem=arg('--day-stem');

if(fixture&&customRequested) fail('Use either --fixture or custom --format-string, not both');
if(fiveMethod!==undefined && !['method1','method2'].includes(fiveMethod)) fail(`Invalid --five-method: ${fiveMethod}`);
if(dayStem!==undefined && !['yang','yin'].includes(dayStem)) fail(`Invalid --day-stem: ${dayStem}`);
if(fiveMethod==='method1' && dayStem===undefined) fail('--five-method method1 requires --day-stem yang|yin');
if(fiveMethod!=='method1' && dayStem!==undefined) fail('--day-stem is only valid with --five-method method1');

let formatString,inputMode,conventionId;
if(fixture){
  if(fixture!=='zhen-4') fail(`Unknown fixture: ${fixture}`);
  formatString='444';inputMode='FIXTURE';conventionId='PREHEAVEN_ZHEN_4_AFTERHEAVEN_ZHEN_3';
}else{
  formatString=arg('--format-string');
  if(!formatString) fail('Custom usage: --format-string XYZ [--yang-lines 0..6] [--five-method method1 --day-stem yang|yin | --five-method method2]');
  if(!/^[1-8][1-8][1-6]$/.test(formatString)) fail(`Invalid --format-string: ${formatString}`);
  inputMode='CUSTOM';conventionId='EXPLICIT_FORMAT_STRING_INPUT';
}

const derivedYangLines=deriveYangLines(formatString);
const suppliedYangRaw=arg('--yang-lines');
if(suppliedYangRaw!==undefined){
  const suppliedYang=Number(suppliedYangRaw);
  if(!Number.isInteger(suppliedYang)||suppliedYang<0||suppliedYang>6) fail(`Invalid --yang-lines: ${suppliedYangRaw}`);
  if(suppliedYang!==derivedYangLines) fail(`--yang-lines mismatch: format ${formatString} implies ${derivedYangLines}, got ${suppliedYang}`);
}

let originalC,c,originalG,g;
try{
  originalC=mod.calcOriginCFigure(derivedYangLines);
  c=mod.calcCFigure(formatString);
  originalG=mod.calcOriginGFigure(derivedYangLines);
  g=mod.calcGFigure(formatString);
}catch(err){fail(`plum-cg rejected input: ${err?.message??err}`,1)}

if(inputMode==='FIXTURE'&&(originalC!==168||c!==7572||originalG!==704||g!==30986)){
  fail(`CEGUI fixture drift: ${JSON.stringify({originalC,c,originalG,g})}`,1);
}

const method2={
  METHOD_ID:'METHOD_2_CE5_GEN_GUI5_KUN',
  DESCRIPTION:'法二：策五艮，轨五坤',
  CE_TRIGRAMS:mod.getTrigramFromCFigure(c),
  GUI_TRIGRAMS:mod.getTrigramFromGFigure(g),
};
const method1Yang={
  METHOD_ID:'METHOD_1_DAY_STEM_YANG',
  DESCRIPTION:'法一：阳日寄艮',
  CE_TRIGRAMS:mod.getTrigramFromCFigure(c,1,true),
  GUI_TRIGRAMS:mod.getTrigramFromGFigure(g,1,true),
};
const method1Yin={
  METHOD_ID:'METHOD_1_DAY_STEM_YIN',
  DESCRIPTION:'法一：阴日寄坤',
  CE_TRIGRAMS:mod.getTrigramFromCFigure(c,1,false),
  GUI_TRIGRAMS:mod.getTrigramFromGFigure(g,1,false),
};

let selectedMapping=null;
if(fiveMethod==='method2') selectedMapping=method2;
if(fiveMethod==='method1') selectedMapping=dayStem==='yang'?method1Yang:method1Yin;

console.log(JSON.stringify({
  DOMAIN:'CEGUI',
  ENGINE_PIN:PIN,
  INPUT_MODE:inputMode,
  INPUT:{
    format_string:formatString,
    yang_lines_derived:derivedYangLines,
    yang_lines_supplied_for_compatibility:suppliedYangRaw===undefined?null:Number(suppliedYangRaw),
  },
  CONVENTION_ID:conventionId,
  ORIGINAL_CE:originalC,
  CE_NUMBER:c,
  ORIGINAL_GUI:originalG,
  GUI_NUMBER:g,
  FORMULA_TRACE:[
    `deriveYangLines("${formatString.slice(0,2)}") => ${derivedYangLines}`,
    `calcOriginCFigure(${derivedYangLines})`,
    `calcCFigure("${formatString}")`,
    `calcOriginGFigure(${derivedYangLines})`,
    `calcGFigure("${formatString}")`
  ],
  NUMBER_5_CONVENTION:{
    STATUS:'EXPLICIT_TWO_METHODS_FROM_PINNED_UPSTREAM',
    SOURCE:'plum-cg README_Tutorial.md + getTrigramFromCFigure/getTrigramFromGFigure',
    METHOD_1:{YANG_DAY:method1Yang,YIN_DAY:method1Yin},
    METHOD_2:method2,
    SELECTED: selectedMapping,
    SELECTION_STATUS:selectedMapping?'EXPLICITLY_SELECTED':'UNSELECTED_NO_SILENT_NORMALIZATION',
  },
  PROVENANCE_STATUS:'PINNED_UPSTREAM_FORMULA_AND_CONVENTION',
  PREDICTIVE_STATUS:'NOT_APPLICABLE_NOT_TESTED',
  NONCLAIMS:['NO_HISTORICAL_METHOD_WINNER','NO_SILENT_NUMBER_5_NORMALIZATION']
},null,2));
