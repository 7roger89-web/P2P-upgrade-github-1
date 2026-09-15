#!/usr/bin/env node
import path from 'node:path';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const dir=path.dirname(fileURLToPath(import.meta.url));
const runner=path.join(dir,'run_cegui_capability.mjs');
const upstream=path.resolve(dir,'../../upstreams/plum-cg');

const PIN='509fc43001a503d17a37db07bc56e069b1ff1c4f';
const REPO='soom-lupulus/plum-cg';

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

// ---- Import production validators (real production logic) ----
const prod = await import(pathToFileURL(runner).href);

// Verify production validators are testable
if(typeof prod.validateEvidenceEntry!=='function') throw new Error('PRODUCTION_EVIDENCE_VALIDATOR not testable');
if(typeof prod.validateCoverage!=='function') throw new Error('PRODUCTION_COVERAGE_VALIDATOR not testable');
if(typeof prod.validateWitnessAgainstSourceDerived!=='function') throw new Error('PRODUCTION_YANG_WITNESS_VALIDATOR not testable');

// ---- Provenance 05 checks ----

const expectedYangMap={1:3,2:2,3:2,4:1,5:2,6:1,7:1,8:0};

function assertYangAuthority(packet){
  const ya=packet.YANG_LINE_AUTHORITY;
  if(!ya) throw new Error('Missing YANG_LINE_AUTHORITY');
  if(ya.repo!==REPO) throw new Error('YANG_LINE_AUTHORITY repo mismatch');
  if(ya.pin!==PIN) throw new Error('YANG_LINE_AUTHORITY pin mismatch');
  if(ya.source_path!=='src/trigram.ts') throw new Error('YANG_LINE_AUTHORITY source_path mismatch');
  if(ya.source_anchor!=='export const trigram_info') throw new Error('YANG_LINE_AUTHORITY anchor mismatch');
  if(JSON.stringify(ya.source_derived_map)!==JSON.stringify(expectedYangMap)) throw new Error(`YANG_LINE_AUTHORITY derived map mismatch: ${JSON.stringify(ya.source_derived_map)}`);
  if(JSON.stringify(ya.witness_map)!==JSON.stringify(expectedYangMap)) throw new Error('YANG_LINE_AUTHORITY witness map mismatch');
  if(ya.witness_validation!=='PASS_EXACT_MATCH_FAIL_CLOSED_ON_MISMATCH') throw new Error('witness validation status mismatch');
  if(!ya.duplicated_table_second_authority_removed.includes('YES')) throw new Error('duplicated table second authority not marked removed');
  const trigramContent=fs.readFileSync(path.join(upstream,'src/trigram.ts'),'utf8');
  if(!trigramContent.includes(ya.source_anchor)) throw new Error('trigram anchor not literally present');
  const regex=/pre_num:\s*(\d+)[\s\S]*?yao_yang_num:\s*(\d+)/g;
  const derived={};
  let m;
  while((m=regex.exec(trigramContent))!==null){
    derived[Number(m[1])]=Number(m[2]);
  }
  if(JSON.stringify(derived)!==JSON.stringify(expectedYangMap)) throw new Error('source-derived yang map from file does not match expected');
  // Use production yang validator
  prod.validateWitnessAgainstSourceDerived(ya.source_derived_map, ya.witness_map);
}
assertYangAuthority(fixture);
assertYangAuthority(method2);
assertYangAuthority(method1Yin);

function assertProvenancePacket(packet, expectSelected){
  if(!packet.FORMULA_EVIDENCE||!Array.isArray(packet.FORMULA_EVIDENCE)) throw new Error('Missing FORMULA_EVIDENCE');
  if(!packet.APPLIED_FORMULA_IDS||!Array.isArray(packet.APPLIED_FORMULA_IDS)) throw new Error('Missing APPLIED_FORMULA_IDS');
  if(!packet.FORMULA_TRACE_IDS||!Array.isArray(packet.FORMULA_TRACE_IDS)) throw new Error('Missing FORMULA_TRACE_IDS');
  if(!packet.SOURCE_VALIDATION||packet.SOURCE_VALIDATION.status!=='PASS') throw new Error('SOURCE_VALIDATION not PASS');
  if(packet.PROVENANCE_STATUS!=='PINNED_UPSTREAM_FORMULA_AND_CONVENTION') throw new Error(`PROVENANCE_STATUS mismatch: ${packet.PROVENANCE_STATUS}`);
  if(packet.HISTORICAL_PRIMARY_SOURCE_VALIDATED!==false) throw new Error('HISTORICAL_PRIMARY_SOURCE_VALIDATED must be false');
  if(packet.PREDICTIVE_STATUS!=='NOT_APPLICABLE_NOT_TESTED') throw new Error('PREDICTIVE_STATUS mismatch');
  if(!packet.NONCLAIMS.includes('NO_HISTORICAL_METHOD_WINNER')) throw new Error('NONCLAIMS missing NO_HISTORICAL_METHOD_WINNER');
  if(!packet.NONCLAIMS.includes('NO_SILENT_NUMBER_5_NORMALIZATION')) throw new Error('NONCLAIMS missing NO_SILENT_NUMBER_5_NORMALIZATION');

  // Exact coverage using production coverage validator
  prod.validateCoverage(packet.FORMULA_EVIDENCE, packet.APPLIED_FORMULA_IDS, packet.FORMULA_TRACE_IDS);

  // Validate each evidence entry using production validator
  for(const ev of packet.FORMULA_EVIDENCE){
    prod.validateEvidenceEntry(ev, upstream);
  }

  const baseIds=['CEGUI_YANG_LINE_COUNT_FROM_TRIGRAM_SOURCE','CEGUI_ORIGIN_C_FIGURE','CEGUI_C_FIGURE','CEGUI_ORIGIN_G_FIGURE','CEGUI_G_FIGURE'];
  for(const bid of baseIds){
    if(!packet.APPLIED_FORMULA_IDS.includes(bid)) throw new Error(`Missing base formula ${bid}`);
  }

  if(!expectSelected){
    const hasNum5=packet.FORMULA_EVIDENCE.some(e=>e.id.includes('NUMBER5'));
    if(hasNum5) throw new Error('Unselected packet must not contain NUMBER5 evidence');
    if(packet.APPLIED_FORMULA_IDS.length!==5) throw new Error(`Unselected should have 5 applied IDs, got ${packet.APPLIED_FORMULA_IDS.length}`);
  }else{
    if(!packet.APPLIED_FORMULA_IDS.includes('CEGUI_C_NUMBER5_MAPPING')) throw new Error('Selected packet missing CEGUI_C_NUMBER5_MAPPING');
    if(!packet.APPLIED_FORMULA_IDS.includes('CEGUI_G_NUMBER5_MAPPING')) throw new Error('Selected packet missing CEGUI_G_NUMBER5_MAPPING');
    if(expectSelected==='method2'){
      if(!packet.APPLIED_FORMULA_IDS.includes('CEGUI_C_NUMBER5_MAPPING_REPO_METHOD2')) throw new Error('method2 missing repo method2 CE');
      if(!packet.APPLIED_FORMULA_IDS.includes('CEGUI_G_NUMBER5_MAPPING_REPO_METHOD2')) throw new Error('method2 missing repo method2 GUI');
      if(packet.APPLIED_FORMULA_IDS.includes('CEGUI_C_NUMBER5_MAPPING_REPO_METHOD1')) throw new Error('method2 should not contain method1 repo evidence');
    }else if(expectSelected==='method1'){
      if(!packet.APPLIED_FORMULA_IDS.includes('CEGUI_C_NUMBER5_MAPPING_REPO_METHOD1')) throw new Error('method1 missing repo method1 CE');
      if(!packet.APPLIED_FORMULA_IDS.includes('CEGUI_G_NUMBER5_MAPPING_REPO_METHOD1')) throw new Error('method1 missing repo method1 GUI');
      if(packet.APPLIED_FORMULA_IDS.includes('CEGUI_C_NUMBER5_MAPPING_REPO_METHOD2')) throw new Error('method1 should not contain method2 repo evidence');
    }
  }

  const originC=packet.FORMULA_EVIDENCE.find(e=>e.id==='CEGUI_ORIGIN_C_FIGURE');
  if(originC.source_path!=='src/index.ts'||originC.source_anchor!=='export const calcOriginCFigure') throw new Error('ORIGIN_C evidence source mismatch');
  const cFig=packet.FORMULA_EVIDENCE.find(e=>e.id==='CEGUI_C_FIGURE');
  if(cFig.source_anchor!=='export const calcCFigure') throw new Error('C_FIGURE anchor mismatch');
  const originG=packet.FORMULA_EVIDENCE.find(e=>e.id==='CEGUI_ORIGIN_G_FIGURE');
  if(originG.source_anchor!=='export const calcOriginGFigure') throw new Error('ORIGIN_G anchor mismatch');
  const gFig=packet.FORMULA_EVIDENCE.find(e=>e.id==='CEGUI_G_FIGURE');
  if(gFig.source_anchor!=='export const calcGFigure') throw new Error('G_FIGURE anchor mismatch');

  const m1=packet.NUMBER_5_CONVENTION.METHOD_1_REPO_DECLARED_SOURCE;
  const m2=packet.NUMBER_5_CONVENTION.METHOD_2_REPO_DECLARED_SOURCE;
  if(!m1||m1.source_path!=='README_Tutorial.md'||!m1.source_anchor.includes('法一')) throw new Error('METHOD1 repo declared source mismatch');
  if(!m2||m2.source_path!=='README_Tutorial.md'||!m2.source_anchor.includes('法二')) throw new Error('METHOD2 repo declared source mismatch');
  const readme=fs.readFileSync(path.join(upstream,'README_Tutorial.md'),'utf8');
  if(!readme.includes(m1.source_anchor)) throw new Error(`METHOD1 anchor not found in README: ${m1.source_anchor}`);
  if(!readme.includes(m2.source_anchor)) throw new Error(`METHOD2 anchor not found in README: ${m2.source_anchor}`);
  if(!readme.includes('## 先天五行数')) throw new Error('README missing ## 先天五行数');
  if(!readme.includes('### 轨数配卦')) throw new Error('README missing ### 轨数配卦');
  if(!readme.includes('## 起演策数')) throw new Error('README missing ## 起演策数');
  if(!readme.includes('## 起演轨数')) throw new Error('README missing ## 起演轨数');
}

assertProvenancePacket(fixture, null);
assertProvenancePacket(customDerived, null);
assertProvenancePacket(method2, 'method2');
assertProvenancePacket(method1Yin, 'method1');

const method1Yang=run(['--format-string','444','--five-method','method1','--day-stem','yang']);
assertProvenancePacket(method1Yang, 'method1');

// ---- Load-bearing negative tests using REAL production validators ----

function testMutation(name, fn){
  try{
    fn();
    throw new Error(`Mutation test ${name} did not fail as expected`);
  }catch(e){
    if(e.message.startsWith(`Mutation test ${name} did not fail`)) throw e;
    // Expected: production validator threw
  }
}

// Wrong repo
testMutation('WRONG_REPO', ()=>{
  const bad={...fixture.FORMULA_EVIDENCE[0], repo:'wrong/repo'};
  prod.validateEvidenceEntry(bad, upstream);
});

// Wrong pin
testMutation('WRONG_PIN', ()=>{
  const bad={...fixture.FORMULA_EVIDENCE[0], pin:'0000000000000000000000000000000000000000'};
  prod.validateEvidenceEntry(bad, upstream);
});

// Wrong source path
testMutation('WRONG_PATH', ()=>{
  const bad={...fixture.FORMULA_EVIDENCE[0], source_path:'src/nonexistent.ts'};
  prod.validateEvidenceEntry(bad, upstream);
});

// Path escape
testMutation('PATH_ESCAPE', ()=>{
  const bad={...fixture.FORMULA_EVIDENCE[0], source_path:'../../etc/passwd'};
  prod.validateEvidenceEntry(bad, upstream);
});

// Wrong anchor
testMutation('WRONG_ANCHOR', ()=>{
  const bad={...fixture.FORMULA_EVIDENCE[0], source_anchor:'THIS_ANCHOR_DOES_NOT_EXIST_IN_FILE'};
  prod.validateEvidenceEntry(bad, upstream);
});

// Missing bounded claim
testMutation('MISSING_CLAIM', ()=>{
  const bad={...fixture.FORMULA_EVIDENCE[0], bounded_supported_claim:''};
  prod.validateEvidenceEntry(bad, upstream);
});

// Wrong support_status
testMutation('WRONG_SUPPORT_STATUS', ()=>{
  const bad={...fixture.FORMULA_EVIDENCE[0], support_status:'UNKNOWN_STATUS'};
  prod.validateEvidenceEntry(bad, upstream);
});

// Wrong authority_type
testMutation('WRONG_AUTHORITY_TYPE', ()=>{
  const bad={...fixture.FORMULA_EVIDENCE[0], authority_type:'UNKNOWN_AUTHORITY'};
  prod.validateEvidenceEntry(bad, upstream);
});

// Support/authority mismatch
testMutation('SUPPORT_AUTHORITY_MISMATCH', ()=>{
  const bad={...fixture.FORMULA_EVIDENCE[0], support_status:'PINNED_ENGINE_FORMULA_SUPPORT', authority_type:'REPO_DECLARED_METHOD_SUPPORT'};
  prod.validateEvidenceEntry(bad, upstream);
});

// Missing formula evidence for an applied formula -> production coverage validator must reject
testMutation('MISSING_FORMULA_EVIDENCE', ()=>{
  const packet=JSON.parse(JSON.stringify(fixture));
  const truncatedEvidence=packet.FORMULA_EVIDENCE.slice(1);
  prod.validateCoverage(truncatedEvidence, packet.APPLIED_FORMULA_IDS, packet.APPLIED_FORMULA_IDS);
});

// Evidence for unapplied formula -> production coverage validator must reject
testMutation('UNAPPLIED_FORMULA_EVIDENCE', ()=>{
  const packet=JSON.parse(JSON.stringify(fixture));
  const extendedEvidence=[...packet.FORMULA_EVIDENCE, {
    id:'CEGUI_C_NUMBER5_MAPPING',
    support_status:'PINNED_ENGINE_FORMULA_SUPPORT',
    repo:REPO,
    pin:PIN,
    source_path:'src/index.ts',
    source_anchor:'export function getTrigramFromCFigure',
    authority_type:'PINNED_ENGINE_FORMULA_SUPPORT',
    bounded_supported_claim:'fake'
  }];
  prod.validateCoverage(extendedEvidence, packet.APPLIED_FORMULA_IDS, packet.APPLIED_FORMULA_IDS);
});

// Source-derived trigram/yang table mismatch - use production yang validator with mutated witness
testMutation('YANG_LINE_SOURCE_MISMATCH', ()=>{
  const witnessMutated={1:3,2:2,3:2,4:1,5:2,6:1,7:1,8:1}; // 8 keys, one wrong value (8:0->1)
  prod.validateWitnessAgainstSourceDerived(expectedYangMap, witnessMutated);
});

// Wrong number-5 source locator - executable anchor wrong
testMutation('NUMBER5_LOCATOR_NEGATIVE', ()=>{
  const bad={
    id:'CEGUI_C_NUMBER5_MAPPING',
    support_status:'PINNED_ENGINE_FORMULA_SUPPORT',
    repo:REPO,
    pin:PIN,
    source_path:'src/index.ts',
    source_anchor:'export function getTrigramFromCFigure_WRONG',
    authority_type:'PINNED_ENGINE_FORMULA_SUPPORT',
    bounded_supported_claim:'CE 5 mapping'
  };
  prod.validateEvidenceEntry(bad, upstream);
});

// Wrong number-5 repo locator
testMutation('NUMBER5_REPO_LOCATOR', ()=>{
  const bad={
    id:'CEGUI_C_NUMBER5_MAPPING_REPO_METHOD2',
    support_status:'REPO_DECLARED_METHOD_SUPPORT',
    repo:REPO,
    pin:PIN,
    source_path:'README_Tutorial.md',
    source_anchor:'法二：不存在的映射',
    authority_type:'REPO_DECLARED_METHOD_SUPPORT',
    bounded_supported_claim:'fake'
  };
  prod.validateEvidenceEntry(bad, upstream);
});

console.log('CEGUI_CAPABILITY_TEST=PASS');
console.log('CEGUI_PROVENANCE_05_TEST=PASS');
console.log('WRONG_REPO_MUTATION_TEST=PASS');
console.log('WRONG_PIN_MUTATION_TEST=PASS');
console.log('WRONG_PATH_MUTATION_TEST=PASS');
console.log('PATH_ESCAPE_MUTATION_TEST=PASS');
console.log('WRONG_ANCHOR_MUTATION_TEST=PASS');
console.log('MISSING_CLAIM_MUTATION_TEST=PASS');
console.log('WRONG_SUPPORT_STATUS_MUTATION_TEST=PASS');
console.log('WRONG_AUTHORITY_TYPE_MUTATION_TEST=PASS');
console.log('SUPPORT_AUTHORITY_MISMATCH_MUTATION_TEST=PASS');
console.log('MISSING_FORMULA_EVIDENCE_TEST=PASS');
console.log('UNAPPLIED_FORMULA_EVIDENCE_TEST=PASS');
console.log('YANG_LINE_SOURCE_MISMATCH_TEST=PASS');
console.log('NUMBER5_LOCATOR_NEGATIVE_TEST=PASS');
console.log('PRODUCTION_EVIDENCE_VALIDATOR_TESTABLE=YES');
console.log('PRODUCTION_COVERAGE_VALIDATOR_TESTABLE=YES');
console.log('PRODUCTION_YANG_WITNESS_VALIDATOR_TESTABLE=YES');
console.log('SUPPORT_STATUS_VOCAB_ENFORCED=YES');
console.log('AUTHORITY_TYPE_VOCAB_ENFORCED=YES');
console.log('SUPPORT_AUTHORITY_PAIR_ENFORCED=YES');
console.log('ALL_NEGATIVE_TESTS_USE_PRODUCTION_VALIDATION=YES');
