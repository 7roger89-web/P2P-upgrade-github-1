#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL, fileURLToPath } from 'node:url';

export const PIN='509fc43001a503d17a37db07bc56e069b1ff1c4f';
export const CEGUI_REPO='soom-lupulus/plum-cg';
const dir=path.dirname(fileURLToPath(import.meta.url));
export const upstream=path.resolve(dir,'../../upstreams/plum-cg');

// CLI fail helper (exits)
function fail(msg,code=2){console.error(msg);process.exit(code)}

// Production validation helpers that THROW (testable)
export function throwValidationError(msg){ throw new Error(msg); }

export function extractYangLinesFromPinnedSource(upstreamPath=upstream){
  const trigramPath=path.join(upstreamPath,'src/trigram.ts');
  if(!fs.existsSync(trigramPath)) throwValidationError(`Pinned trigram source missing: ${trigramPath}`);
  const content=fs.readFileSync(trigramPath,'utf8');
  const regex=/pre_num:\s*(\d+)[\s\S]*?yao_yang_num:\s*(\d+)/g;
  const map={};
  let m;
  while((m=regex.exec(content))!==null){
    const pre=Number(m[1]);
    const yang=Number(m[2]);
    if(!Number.isInteger(pre)||!Number.isInteger(yang)) continue;
    map[pre]=yang;
  }
  const keys=Object.keys(map).map(Number).sort((a,b)=>a-b);
  if(keys.length!==8||keys[0]!==1||keys[7]!==8){
    throwValidationError(`Yang-line extraction failed: expected 8 entries 1..8, got ${JSON.stringify(map)}`);
  }
  for(let i=1;i<=8;i++){
    if(!(i in map)) throwValidationError(`Yang-line extraction missing pre_num ${i}`);
  }
  return {map: Object.freeze({...map}), rawContent: content};
}

export const PREHEAVEN_YANG_LINES_WITNESS=Object.freeze({1:3,2:2,3:2,4:1,5:2,6:1,7:1,8:0});

export function validateWitnessAgainstSourceDerived(derived, witness=PREHEAVEN_YANG_LINES_WITNESS){
  const dKeys=Object.keys(derived).map(Number).sort((a,b)=>a-b);
  const wKeys=Object.keys(witness).map(Number).sort((a,b)=>a-b);
  if(JSON.stringify(dKeys)!==JSON.stringify(wKeys)){
    throwValidationError(`Yang-line witness key mismatch: derived ${JSON.stringify(dKeys)} vs witness ${JSON.stringify(wKeys)}`);
  }
  for(const k of dKeys){
    if(derived[k]!==witness[k]){
      throwValidationError(`Yang-line source mismatch: pre_num ${k} derived ${derived[k]} vs witness ${witness[k]}; source-derived authority is pinned src/trigram.ts`);
    }
  }
}

export function deriveYangLinesFromMap(map, formatString){
  return map[Number(formatString[0])] + map[Number(formatString[1])];
}

// Bounded vocabulary enforcement
export const VALID_SUPPORT_STATUS=new Set(['PINNED_ENGINE_FORMULA_SUPPORT','REPO_DECLARED_METHOD_SUPPORT']);
export const VALID_AUTHORITY_TYPE=new Set(['PINNED_ENGINE_FORMULA_SUPPORT','REPO_DECLARED_METHOD_SUPPORT']);
export const VALID_PAIR={
  'PINNED_ENGINE_FORMULA_SUPPORT':'PINNED_ENGINE_FORMULA_SUPPORT',
  'REPO_DECLARED_METHOD_SUPPORT':'REPO_DECLARED_METHOD_SUPPORT'
};

export function validateEvidenceEntry(entry, upstreamPath=upstream){
  if(entry.repo!==CEGUI_REPO) throwValidationError(`Source validation failed: wrong repo for ${entry.id}: expected ${CEGUI_REPO}, got ${entry.repo}`);
  if(entry.pin!==PIN) throwValidationError(`Source validation failed: wrong pin for ${entry.id}: expected ${PIN}, got ${entry.pin}`);
  if(typeof entry.source_path!=='string'||entry.source_path.length===0) throwValidationError(`Source validation failed: missing source_path for ${entry.id}`);
  if(entry.source_path.includes('..')) throwValidationError(`Source validation failed: path escape '..' in ${entry.id}: ${entry.source_path}`);
  if(path.isAbsolute(entry.source_path)) throwValidationError(`Source validation failed: absolute path not allowed for ${entry.id}: ${entry.source_path}`);
  const resolved=path.resolve(upstreamPath, entry.source_path);
  if(!resolved.startsWith(upstreamPath+path.sep) && resolved!==upstreamPath) throwValidationError(`Source validation failed: path resolves outside upstream for ${entry.id}: ${entry.source_path}`);
  if(!fs.existsSync(resolved)) throwValidationError(`Source validation failed: file not found for ${entry.id}: ${entry.source_path} -> ${resolved}`);
  if(typeof entry.source_anchor!=='string'||entry.source_anchor.length===0) throwValidationError(`Source validation failed: missing source_anchor for ${entry.id}`);
  const fileContent=fs.readFileSync(resolved,'utf8');
  if(!fileContent.includes(entry.source_anchor)) throwValidationError(`Source validation failed: anchor not found for ${entry.id}: expected literal '${entry.source_anchor}' in ${entry.source_path}`);
  if(typeof entry.bounded_supported_claim!=='string'||entry.bounded_supported_claim.trim().length===0) throwValidationError(`Source validation failed: missing bounded_supported_claim for ${entry.id}`);
  if(typeof entry.support_status!=='string'||entry.support_status.length===0) throwValidationError(`Source validation failed: missing support_status for ${entry.id}`);
  if(typeof entry.authority_type!=='string'||entry.authority_type.length===0) throwValidationError(`Source validation failed: missing authority_type for ${entry.id}`);
  // Enforce exact bounded vocabulary
  if(!VALID_SUPPORT_STATUS.has(entry.support_status)) throwValidationError(`Source validation failed: unknown support_status for ${entry.id}: ${entry.support_status}`);
  if(!VALID_AUTHORITY_TYPE.has(entry.authority_type)) throwValidationError(`Source validation failed: unknown authority_type for ${entry.id}: ${entry.authority_type}`);
  const expectedAuthority=VALID_PAIR[entry.support_status];
  if(entry.authority_type!==expectedAuthority) throwValidationError(`Source validation failed: support_status/authority_type mismatch for ${entry.id}: ${entry.support_status} vs ${entry.authority_type}, expected ${expectedAuthority}`);
}

export function validateCoverage(evidence, appliedIds, traceIds){
  const evIds=evidence.map(e=>e.id).sort();
  const appliedSorted=[...appliedIds].sort();
  const traceSorted=[...traceIds].sort();
  if(JSON.stringify(evIds)!==JSON.stringify(appliedSorted)){
    throwValidationError(`Formula trace / evidence exact coverage mismatch: evidenceIds ${JSON.stringify(evIds)} vs applied ${JSON.stringify(appliedSorted)}`);
  }
  if(JSON.stringify(evIds)!==JSON.stringify(traceSorted)){
    throwValidationError(`Formula trace / traceIds coverage mismatch: evidenceIds ${JSON.stringify(evIds)} vs trace ${JSON.stringify(traceSorted)}`);
  }
}

export function makeEvidence({id, support_status, source_path, source_anchor, authority_type, bounded_supported_claim}){
  return {
    id,
    support_status,
    repo: CEGUI_REPO,
    pin: PIN,
    source_path,
    source_anchor,
    authority_type,
    bounded_supported_claim
  };
}

function arg(name){const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:undefined}
function has(name){return process.argv.includes(name)}

async function main(){
  // ---- Pinned upstream SHA check (preserved) ----
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

  // ---- Yang-line authority derived from pinned src/trigram.ts ----
  let SOURCE_DERIVED_YANG_LINES;
  try{
    const extracted=extractYangLinesFromPinnedSource(upstream);
    SOURCE_DERIVED_YANG_LINES=extracted.map;
  }catch(e){ fail(e.message); }

  // Validate witness
  try{
    validateWitnessAgainstSourceDerived(SOURCE_DERIVED_YANG_LINES, PREHEAVEN_YANG_LINES_WITNESS);
  }catch(e){ fail(e.message); }

  function deriveYangLines(formatString){
    return deriveYangLinesFromMap(SOURCE_DERIVED_YANG_LINES, formatString);
  }

  // ---- Argument parsing (preserved) ----
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

  // ---- Formula Evidence (load-bearing) ----
  const baseEvidence=[
    makeEvidence({
      id:'CEGUI_YANG_LINE_COUNT_FROM_TRIGRAM_SOURCE',
      support_status:'PINNED_ENGINE_FORMULA_SUPPORT',
      source_path:'src/trigram.ts',
      source_anchor:'export const trigram_info',
      authority_type:'PINNED_ENGINE_FORMULA_SUPPORT',
      bounded_supported_claim:'pre_num 1..8 maps to yao_yang_num as 1->3,2->2,3->2,4->1,5->2,6->1,7->1,8->0 derived from pinned trigram_info; extraction via pre_num/yao_yang_num regex'
    }),
    makeEvidence({
      id:'CEGUI_ORIGIN_C_FIGURE',
      support_status:'PINNED_ENGINE_FORMULA_SUPPORT',
      source_path:'src/index.ts',
      source_anchor:'export const calcOriginCFigure',
      authority_type:'PINNED_ENGINE_FORMULA_SUPPORT',
      bounded_supported_claim:'ORIGIN_CE = yang*36 + (6-yang)*24 via YANG_C=36,YIN_C=24,YAO_TOTAL=6 per src/index.ts calcOriginCFigure'
    }),
    makeEvidence({
      id:'CEGUI_C_FIGURE',
      support_status:'PINNED_ENGINE_FORMULA_SUPPORT',
      source_path:'src/index.ts',
      source_anchor:'export const calcCFigure',
      authority_type:'PINNED_ENGINE_FORMULA_SUPPORT',
      bounded_supported_claim:'CE = 三五之数 + 错综数 with 上卦动/下卦动 branch: shift>3 uses shift*10*origin + upper*origin + origin + kaleidoscope else shift*origin + lower*10*origin + origin + kaleidoscope; per README 起演策数 and src/index.ts calcCFigure'
    }),
    makeEvidence({
      id:'CEGUI_ORIGIN_G_FIGURE',
      support_status:'PINNED_ENGINE_FORMULA_SUPPORT',
      source_path:'src/index.ts',
      source_anchor:'export const calcOriginGFigure',
      authority_type:'PINNED_ENGINE_FORMULA_SUPPORT',
      bounded_supported_claim:'ORIGIN_GUI = yang*128 + (6-yang)*112 via YANG_G=128,YIN_G=112 per src/index.ts calcOriginGFigure'
    }),
    makeEvidence({
      id:'CEGUI_G_FIGURE',
      support_status:'PINNED_ENGINE_FORMULA_SUPPORT',
      source_path:'src/index.ts',
      source_anchor:'export const calcGFigure',
      authority_type:'PINNED_ENGINE_FORMULA_SUPPORT',
      bounded_supported_claim:'GUI = 三五之数 + 错综数 with 后天卦数 and 上卦动/下卦动 branch per README 起演轨数 and src/index.ts calcGFigure'
    }),
  ];

  const cNumber5Exec=makeEvidence({
    id:'CEGUI_C_NUMBER5_MAPPING',
    support_status:'PINNED_ENGINE_FORMULA_SUPPORT',
    source_path:'src/index.ts',
    source_anchor:'export function getTrigramFromCFigure',
    authority_type:'PINNED_ENGINE_FORMULA_SUPPORT',
    bounded_supported_claim:'CE digit 5 maps to 艮 by default; with mode=1, 阳日->艮 阴日->坤; executable logic in getTrigramFromCFigure per src/index.ts'
  });
  const gNumber5Exec=makeEvidence({
    id:'CEGUI_G_NUMBER5_MAPPING',
    support_status:'PINNED_ENGINE_FORMULA_SUPPORT',
    source_path:'src/index.ts',
    source_anchor:'export function getTrigramFromGFigure',
    authority_type:'PINNED_ENGINE_FORMULA_SUPPORT',
    bounded_supported_claim:'GUI digit 5 maps to 坤 by default; with mode=1, 阳日->艮 阴日->坤; executable logic in getTrigramFromGFigure per src/index.ts'
  });

  const method1RepoCE=makeEvidence({
    id:'CEGUI_C_NUMBER5_MAPPING_REPO_METHOD1',
    support_status:'REPO_DECLARED_METHOD_SUPPORT',
    source_path:'README_Tutorial.md',
    source_anchor:'法一：阳日寄艮，阴日寄坤。',
    authority_type:'REPO_DECLARED_METHOD_SUPPORT',
    bounded_supported_claim:'Repo declares Method1: 阳日寄艮，阴日寄坤 for number-5 mapping; documented in README_Tutorial.md 先天五行数 and 轨数配卦 sections'
  });
  const method2RepoCE=makeEvidence({
    id:'CEGUI_C_NUMBER5_MAPPING_REPO_METHOD2',
    support_status:'REPO_DECLARED_METHOD_SUPPORT',
    source_path:'README_Tutorial.md',
    source_anchor:'法二：策五艮，轨五坤。',
    authority_type:'REPO_DECLARED_METHOD_SUPPORT',
    bounded_supported_claim:'Repo declares Method2: 策五艮，轨五坤 for number-5 mapping; documented in README_Tutorial.md 先天五行数 and 轨数配卦 sections'
  });
  const method1RepoGUI=makeEvidence({
    id:'CEGUI_G_NUMBER5_MAPPING_REPO_METHOD1',
    support_status:'REPO_DECLARED_METHOD_SUPPORT',
    source_path:'README_Tutorial.md',
    source_anchor:'### 轨数配卦',
    authority_type:'REPO_DECLARED_METHOD_SUPPORT',
    bounded_supported_claim:'Repo declares 轨数配卦 section with 法一：阳日寄艮，阴日寄坤 for GUI 5 mapping'
  });
  const method2RepoGUI=makeEvidence({
    id:'CEGUI_G_NUMBER5_MAPPING_REPO_METHOD2',
    support_status:'REPO_DECLARED_METHOD_SUPPORT',
    source_path:'README_Tutorial.md',
    source_anchor:'## 先天五行数',
    authority_type:'REPO_DECLARED_METHOD_SUPPORT',
    bounded_supported_claim:'Repo declares 先天五行数 section with 法二：策五艮，轨五坤 and 轨数配卦 section with same for GUI'
  });

  let appliedEvidence=[...baseEvidence];
  let appliedFormulaIds=baseEvidence.map(e=>e.id);

  if(fiveMethod==='method2'){
    appliedEvidence.push(cNumber5Exec, gNumber5Exec, method2RepoCE, method2RepoGUI);
    appliedFormulaIds.push(cNumber5Exec.id, gNumber5Exec.id, method2RepoCE.id, method2RepoGUI.id);
  }else if(fiveMethod==='method1'){
    appliedEvidence.push(cNumber5Exec, gNumber5Exec, method1RepoCE, method1RepoGUI);
    appliedFormulaIds.push(cNumber5Exec.id, gNumber5Exec.id, method1RepoCE.id, method1RepoGUI.id);
  }

  // ---- Runtime source validation (narrow local validator) ----
  try{
    for(const ev of appliedEvidence){
      validateEvidenceEntry(ev, upstream);
    }
    validateCoverage(appliedEvidence, appliedFormulaIds, appliedFormulaIds);
    if(!fiveMethod){
      const hasNumber5=appliedEvidence.some(e=>e.id.includes('NUMBER5'));
      if(hasNumber5) throwValidationError(`Evidence for unapplied number-5 formula emitted while selection is UNSELECTED_NO_SILENT_NORMALIZATION`);
    }
  }catch(e){
    fail(e.message);
  }

  // ---- Output ----
  const output={
    DOMAIN:'CEGUI',
    ENGINE_PIN:PIN,
    ENGINE_REPO:CEGUI_REPO,
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
      `deriveYangLines(\"${formatString.slice(0,2)}\") => ${derivedYangLines}`,
      `calcOriginCFigure(${derivedYangLines})`,
      `calcCFigure(\"${formatString}\")`,
      `calcOriginGFigure(${derivedYangLines})`,
      `calcGFigure(\"${formatString}\")`
    ],
    FORMULA_TRACE_IDS: appliedFormulaIds,
    APPLIED_FORMULA_IDS: appliedFormulaIds,
    FORMULA_EVIDENCE: appliedEvidence,
    YANG_LINE_AUTHORITY:{
      source_path:'src/trigram.ts',
      source_anchor:'export const trigram_info',
      repo:CEGUI_REPO,
      pin:PIN,
      extraction_method:'narrow regex /pre_num:\\s*(\\d+)[\\s\\S]*?yao_yang_num:\\s*(\\d+)/g over pinned trigram_info',
      source_derived_map: SOURCE_DERIVED_YANG_LINES,
      witness_map: PREHEAVEN_YANG_LINES_WITNESS,
      witness_validation:'PASS_EXACT_MATCH_FAIL_CLOSED_ON_MISMATCH',
      duplicated_table_second_authority_removed:'YES_SOURCE_DERIVED_IS_AUTHORITY_WITNESS_ONLY_REGRESSION'
    },
    NUMBER_5_CONVENTION:{
      STATUS:'EXPLICIT_TWO_METHODS_FROM_PINNED_UPSTREAM',
      SOURCE:'plum-cg README_Tutorial.md + getTrigramFromCFigure/getTrigramFromGFigure',
      METHOD_1:{YANG_DAY:method1Yang,YIN_DAY:method1Yin},
      METHOD_2:method2,
      SELECTED: selectedMapping,
      SELECTION_STATUS:selectedMapping?'EXPLICITLY_SELECTED':'UNSELECTED_NO_SILENT_NORMALIZATION',
      METHOD_1_REPO_DECLARED_SOURCE:{
        repo:CEGUI_REPO,
        pin:PIN,
        source_path:'README_Tutorial.md',
        source_anchor:'法一：阳日寄艮，阴日寄坤。',
        heading_anchors:['## 先天五行数','### 轨数配卦'],
        bounded_claim:'Method1: 阳日寄艮，阴日寄坤'
      },
      METHOD_2_REPO_DECLARED_SOURCE:{
        repo:CEGUI_REPO,
        pin:PIN,
        source_path:'README_Tutorial.md',
        source_anchor:'法二：策五艮，轨五坤。',
        heading_anchors:['## 先天五行数','### 轨数配卦'],
        bounded_claim:'Method2: 策五艮，轨五坤'
      }
    },
    SOURCE_VALIDATION:{
      status:'PASS',
      checked_count: appliedEvidence.length,
      repo_exact: CEGUI_REPO,
      pin_exact: PIN
    },
    PROVENANCE_STATUS:'PINNED_UPSTREAM_FORMULA_AND_CONVENTION',
    HISTORICAL_PRIMARY_SOURCE_VALIDATED:false,
    PREDICTIVE_STATUS:'NOT_APPLICABLE_NOT_TESTED',
    NONCLAIMS:['NO_HISTORICAL_METHOD_WINNER','NO_SILENT_NUMBER_5_NORMALIZATION','HISTORICAL_PRIMARY_SOURCE_VALIDATED=NO','PREDICTIVE_STATUS=NOT_APPLICABLE_NOT_TESTED']
  };

  console.log(JSON.stringify(output,null,2));
}

// Only run main when executed as CLI, not when imported
const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if(isMain){
  await main();
}
