#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const runner = path.join(dir, 'run_ziwei_capability.mjs');
const xqrUpstream = path.resolve(dir, '../../upstreams/xu-quanren');
const EXPECTED_XQR_PIN = '7b8364bbd79a11e852899893ac5749a83be62836';
const EXPECTED_XQR_REPO = 'ZhangZangQian/xu-quanren';

function run(args) {
  const r = spawnSync(process.execPath, [runner, ...args], { encoding: 'utf8' });
  if (r.status !== 0) {
    process.stderr.write(r.stderr);
    process.exit(r.status ?? 1);
  }
  return JSON.parse(r.stdout);
}

function extractSourceLiuWai(paipanPath) {
  const content = fs.readFileSync(paipanPath, 'utf8');
  const match = /LIU_WAI\s*=\s*\[([^\]]+)\]/.exec(content);
  if (!match) throw new Error('Cannot extract LIU_WAI from scripts/paipan.py');
  return match[1].split(',').map((s) => s.trim().replace(/^['"]|['"]$/g, '')).filter(Boolean);
}

function validateRuleProvenance(ruleTrace, ruleEvidence, upstreamDir = xqrUpstream, expectedPin = EXPECTED_XQR_PIN) {
  if (!Array.isArray(ruleTrace) || ruleTrace.length === 0) {
    throw new Error('RULE_TRACE must be a non-empty array');
  }
  if (!Array.isArray(ruleEvidence) || ruleEvidence.length === 0) {
    throw new Error('RULE_EVIDENCE must be a non-empty array');
  }
  const evidenceMap = new Map();
  for (const ev of ruleEvidence) {
    if (!ev?.rule_id) throw new Error('Evidence entry missing rule_id');
    evidenceMap.set(ev.rule_id, ev);
  }
  for (const ruleId of ruleTrace) {
    const ev = evidenceMap.get(ruleId);
    if (!ev) throw new Error(`Missing RULE_EVIDENCE for claimed rule: ${ruleId}`);
    if (ev.support_status !== 'DIRECT_SOURCE_SUPPORT') {
      throw new Error(`Rule ${ruleId} support_status is not DIRECT_SOURCE_SUPPORT: ${ev.support_status}`);
    }
    if (ev.repo !== EXPECTED_XQR_REPO) {
      throw new Error(`Rule ${ruleId} repo mismatch: expected ${EXPECTED_XQR_REPO}, got ${ev.repo}`);
    }
    if (ev.pin !== expectedPin) {
      throw new Error(`Rule ${ruleId} pin mismatch: expected ${expectedPin}, got ${ev.pin}`);
    }
    if (!ev.source_path) {
      throw new Error(`Rule ${ruleId} missing source_path`);
    }
    const fullPath = path.join(upstreamDir, ev.source_path);
    if (!fs.existsSync(fullPath)) {
      throw new Error(`Rule ${ruleId} source_path file not found: ${fullPath}`);
    }
    const content = fs.readFileSync(fullPath, 'utf8');
    if (!ev.source_anchor || !content.includes(ev.source_anchor)) {
      throw new Error(`Rule ${ruleId} source_anchor not found in ${ev.source_path}: ${ev.source_anchor}`);
    }
    if (!ev.supported_claim || typeof ev.supported_claim !== 'string') {
      throw new Error(`Rule ${ruleId} missing supported_claim paraphrase`);
    }

    // Specific dual-source verification for R2
    if (ruleId === 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER') {
      // 1. Interpretive source
      if (!ev.interpretive_source) {
        throw new Error('XQR_R2 missing interpretive_source');
      }
      if (ev.interpretive_source.repo !== EXPECTED_XQR_REPO || ev.interpretive_source.pin !== expectedPin) {
        throw new Error('XQR_R2 interpretive_source repo/pin mismatch');
      }
      const interpPath = path.join(upstreamDir, ev.interpretive_source.source_path);
      if (!fs.existsSync(interpPath)) {
        throw new Error(`XQR_R2 interpretive_source file not found: ${interpPath}`);
      }
      const interpContent = fs.readFileSync(interpPath, 'utf8');
      if (!ev.interpretive_source.source_anchor || !interpContent.includes(ev.interpretive_source.source_anchor)) {
        throw new Error(`XQR_R2 interpretive_source anchor not found: ${ev.interpretive_source.source_anchor}`);
      }

      // 2. Classification source
      if (!ev.classification_source) {
        throw new Error('XQR_R2 missing classification_source');
      }
      if (ev.classification_source.repo !== EXPECTED_XQR_REPO || ev.classification_source.pin !== expectedPin) {
        throw new Error('XQR_R2 classification_source repo/pin mismatch');
      }
      const classPath = path.join(upstreamDir, ev.classification_source.source_path);
      if (!fs.existsSync(classPath)) {
        throw new Error(`XQR_R2 classification_source file not found: ${classPath}`);
      }
      const classContent = fs.readFileSync(classPath, 'utf8');
      if (!ev.classification_source.source_anchor || !classContent.includes(ev.classification_source.source_anchor)) {
        throw new Error(`XQR_R2 classification_source anchor not found: ${ev.classification_source.source_anchor}`);
      }

      // 3. Mechanically verify that canonical set is exactly equal to the source-derived set
      const sourceDerivedSet = extractSourceLiuWai(classPath);
      if (sourceDerivedSet.length !== 6) {
        throw new Error(`Source-derived LIU_WAI must have exactly 6 entries, got: ${sourceDerivedSet.length}`);
      }
      if (JSON.stringify(ev.canonical_six_outer) !== JSON.stringify(sourceDerivedSet)) {
        throw new Error(`canonical_six_outer does not match source-derived set from ${classPath}: expected ${JSON.stringify(sourceDerivedSet)}, got ${JSON.stringify(ev.canonical_six_outer)}`);
      }
      if (JSON.stringify(ev.classification_source.canonical_set) !== JSON.stringify(sourceDerivedSet)) {
        throw new Error('classification_source.canonical_set does not match source-derived set');
      }
      if (ev.canonical_count !== 6) {
        throw new Error(`canonical_count must be 6, got: ${ev.canonical_count}`);
      }

      // 4. 交友 must NOT be a seventh doctrinal palace
      if (ev.canonical_six_outer.includes('交友')) {
        throw new Error('交友 must not be in canonical_six_outer (it is an adapter compatibility alias only)');
      }
      if (ev.alias_policy !== 'ADAPTER_NAME_NORMALIZATION') {
        throw new Error(`Invalid alias_policy: ${ev.alias_policy}`);
      }
      if (ev.adapter_normalization?.seventh_doctrinal_palace !== false) {
        throw new Error('seventh_doctrinal_palace must be false');
      }
    }
  }
  return true;
}

// 1. Fixture test
const fixture = run(['--fixture', 'default']);
if (fixture.DOMAIN !== 'ZIWEI_DOUSHU') throw new Error('wrong domain');
if (fixture.BIRTH_YEAR_MUTAGEN['忌'] !== '天同') throw new Error('wrong fixture Geng 忌');
if (fixture.STRUCTURAL_OUTPUT !== 'OUTER/LOSS_INDICATOR') throw new Error('wrong bounded XQR output');
if (fixture.PROVENANCE_STATUS !== 'DIRECT_SOURCE_BOUND') throw new Error('wrong provenance status');
if (!fixture.RULE_TRACE.includes('XQR_R1_PALACE_BEFORE_STAR')) throw new Error('missing XQR_R1 in RULE_TRACE');
if (!fixture.RULE_TRACE.includes('XQR_R2_BIRTH_YEAR_JI_SIX_OUTER')) throw new Error('missing XQR_R2 in RULE_TRACE');

// Load-bearing provenance validation on live fixture output
validateRuleProvenance(fixture.RULE_TRACE, fixture.RULE_EVIDENCE);

// 2. Negative mutation proofs (must reject invalid identity)
// Mutation A: wrong pin
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  mutated[0].pin = '0000000000000000000000000000000000000000';
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: wrong pin was silently accepted');
}

// Mutation B: wrong source path
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  mutated[0].source_path = 'NONEXISTENT_SOURCE_FILE.md';
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: wrong source_path was silently accepted');
}

// Mutation C: wrong source anchor
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  mutated[0].source_anchor = '### NONEXISTENT_SECTION_HEADING';
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: wrong source_anchor was silently accepted');
}

// Mutation D: missing rule evidence for a claimed rule
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE)).filter(
    (ev) => ev.rule_id !== 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER'
  );
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: missing rule evidence was silently accepted');
}

// Mutation E: non-direct support status
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  mutated[0].support_status = 'INSUFFICIENT_SOURCE_SUPPORT';
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: unsupported status was silently accepted');
}

// Mutation F1: R2 classification source with wrong pin
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  const r2 = mutated.find((ev) => ev.rule_id === 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER');
  r2.classification_source.pin = 'badpin0000000000000000000000000000000000';
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: classification_source wrong pin was silently accepted');
}

// Mutation F2: R2 classification source with wrong path
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  const r2 = mutated.find((ev) => ev.rule_id === 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER');
  r2.classification_source.source_path = 'scripts/nonexistent_paipan.py';
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: classification_source wrong path was silently accepted');
}

// Mutation F3: R2 classification source with wrong anchor
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  const r2 = mutated.find((ev) => ev.rule_id === 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER');
  r2.classification_source.source_anchor = 'NONEXISTENT_CONSTANT';
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: classification_source wrong anchor was silently accepted');
}

// Mutation F4: R2 missing classification source
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  const r2 = mutated.find((ev) => ev.rule_id === 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER');
  delete r2.classification_source;
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: missing classification_source was silently accepted');
}

// Mutation F5: R2 attempting to add a 7th doctrinal palace to canonical set
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  const r2 = mutated.find((ev) => ev.rule_id === 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER');
  r2.canonical_six_outer = [...r2.canonical_six_outer, '交友'];
  r2.canonical_count = 7;
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: 7th doctrinal palace was silently accepted');
}

// Mutation F6: R2 with a 6-element set that replaces a canonical palace (keeping count=6)
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  const r2 = mutated.find((ev) => ev.rule_id === 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER');
  // Replace '仆役' with '疾厄' (an inner palace) while count remains 6
  r2.canonical_six_outer = ['子女', '夫妻', '兄弟', '疾厄', '父母', '迁移'];
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: wrong 6-element canonical set was silently accepted');
}

// Mutation F7: R2 classification_source.canonical_set divergence from source authority
{
  let failed = false;
  const mutated = JSON.parse(JSON.stringify(fixture.RULE_EVIDENCE));
  const r2 = mutated.find((ev) => ev.rule_id === 'XQR_R2_BIRTH_YEAR_JI_SIX_OUTER');
  r2.classification_source.canonical_set = ['子女', '夫妻', '兄弟', '疾厄', '父母', '迁移'];
  try {
    validateRuleProvenance(fixture.RULE_TRACE, mutated);
  } catch {
    failed = true;
  }
  if (!failed) throw new Error('Negative proof failed: divergent classification_source.canonical_set was silently accepted');
}

// 3. Custom input test
const custom = run(['--date', '2011-10-18', '--time-index', '4', '--gender', 'female']);
if (custom.INPUT_MODE !== 'CUSTOM' || custom.INPUT.dateStr !== '2011-10-18') throw new Error('custom input not honored');
if (custom.CHART_FACTS.palace_count !== 12 || Object.keys(custom.BIRTH_YEAR_MUTAGEN).length < 4) throw new Error('custom chart facts incomplete');
if (custom.PROVENANCE_STATUS !== 'DIRECT_SOURCE_BOUND') throw new Error('custom provenance status drift');
validateRuleProvenance(custom.RULE_TRACE, custom.RULE_EVIDENCE);

console.log('ZIWEI_CAPABILITY_TEST=PASS');
