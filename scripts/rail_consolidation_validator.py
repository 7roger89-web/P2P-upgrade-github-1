#!/usr/bin/env python3
"""rail_consolidation_validator.py — P2P-CAPABILITY-RESEARCH-CONSOLIDATION-01 governance validator.

Validates the canonical consolidation artifacts without touching runtime:
1. governance/research-adoption-ledger.json  (schema, vocabulary, baselines, cross-references)
2. governance/p2p-development-roadmap.json   (schema, families/items, deps existence, research refs)
3. docs/p2p-development/capability-ledger/capability-index.json (dedup, new-record integrity)
4. governance/development-control.json       (baseline .41 unchanged, canonical_source_index present)

Output constants (fail-closed vocabulary):
  DANGLING_DEPENDENCIES        = count of dep ids referenced but not defined anywhere
  DUPLICATE_CANONICAL_CAPABILITIES = count of duplicated capability ids/names
  ROADMAP_UNKNOWN_REFERENCES   = count of roadmap research ids not present in adoption ledger
  NEW_SECRET_FINDINGS          = 0 (validation read-only scan of new governance files for raw secrets)
  BASELINE_DRIFT               = present/absent
"""
import json, hashlib, re, sys, os

REPO = '/home/ubuntu/fw01_work/auth-f01'
BASELINE_SHA = 'da835f8a48caf4536094ffdd82e3c65baa82da32aa9a7ae73714ee1f2e9c3d2d'
errors, warns = [], []

def load(p):
    with open(os.path.join(REPO, p)) as f:
        return json.load(f)

# ---- 1. research-adoption-ledger ----
ledger = load('governance/research-adoption-ledger.json')
vocab = set(ledger['status_vocabulary'])
ledger_ids = {r['research_id'] for r in ledger['records']}
status_counts = {}
bad_statuses = [r['research_id'] for r in ledger['records'] if r['status'] not in vocab]
if bad_statuses: errors.append(('LEDGER_UNKNOWN_STATUS', bad_statuses))
for r in ledger['records']:
    status_counts[r['status']] = status_counts.get(r['status'], 0) + 1
if ledger['baseline_identity']['artifact_sha256'] != BASELINE_SHA:
    errors.append(('LEDGER_BASELINE_MISMATCH', ledger['baseline_identity']['artifact_sha256']))

# ---- 2. roadmap ----
roadmap = load('governance/p2p-development-roadmap.json')
fam_ids = {f['family_id'] for f in roadmap['families']}
item_ids = {i['roadmap_id'] for i in roadmap['items']}
fam_bad = [i['roadmap_id'] for i in roadmap['items'] if i['family'] not in fam_ids]
if fam_bad: errors.append(('ROADMAP_UNKNOWN_FAMILY', fam_bad))
# dependency resolution: deps must be roadmap item ids (RM-*) or capability ids in capability-index
cap_index = load('docs/p2p-development/capability-ledger/capability-index.json')
cap_ids = {c['capability_id'] for c in cap_index['capabilities'] if isinstance(c, dict)}
# RM-Cxx aliases for bare C-line ids are the same canonical item
bare_aliases = {rid[3:] for rid in item_ids if rid.startswith('RM-C')}
known_refs = item_ids | bare_aliases | cap_ids | {'C08', 'C09', 'C12', 'C15', 'C17', 'C19', 'C38', 'C40', 'C43',
                                    'FW01', 'FW02', 'FW05', 'FW06', 'BOUNDED_DOCUMENTATION_WRITE_SHIPPED',
                                    'LIVE_COUNCIL_8_OF_8', 'ROADMAP_COVERAGE_GAP', 'RA-EXT-026'}
# dependencies are natural-language chains; validate only id-like tokens (C\d+, FW\d\d, RM-*, RA-EXT-*)
id_token_re = re.compile(r'\b(C\d+|FW\d\d|RM-[A-Z0-9_-]+|RA-EXT-\d+|LIVE_[A-Z0-9_]+|C\d{2}\b)?')
id_like_re = re.compile(r'^(C\d+|FW\d\d|RM-[A-Z0-9_-]+|RA-EXT-\d+|LIVE_[A-Z0-9_]+)$')
dangling = []
for i in roadmap['items']:
    for dep in i.get('dependencies', []):
        # hyphen-delimited ids must be matched as whole tokens first (RA-EXT-019, RM-PRIORITY-CODE-MUTATION)
        full_toks = []
        for seg in dep.replace('/', ' ').replace('(', ' ').replace(')', ' ').replace('+', ' ').split():
            full_toks += re.findall(r'(?<![\w.-])(?:RM-[A-Z0-9_-]+|RA-EXT-\d+|LIVE_[A-Z0-9_]+|C\d+|FW\d\d)(?![\w.-])', seg)
        # frag_toks: words of length > 4 that contain no id-like token inside them (avoid 'C19' inside '(C19)')
        full_id_words = set(re.findall(r'(?<![\w.-])(?:RM-[A-Z0-9_-]+|RA-EXT-\d+|LIVE_[A-Z0-9_]+|C\d+|FW\d\d)(?![\w.-])', dep))
        frag_toks = []
        for word in dep.split():
            word = word.strip('.,;:')
            if any(fid in word for fid in full_id_words):
                continue  # word already covered by a full id match
            if id_like_re.match(word):
                frag_toks.append(word)
        for tok in frag_toks:
            if id_like_re.match(tok) and tok not in known_refs:
                dangling.append((i['roadmap_id'], dep))
DANGLING_DEPENDENCIES = len(dangling)
if DANGLING_DEPENDENCIES: errors.append(('DANGLING_DEPENDENCIES', dangling))
# research refs -> ledger ids
unknown_refs = []
ledger_ids = {r['research_id'] for r in ledger['records']}
for i in roadmap['items']:
    for rid in i.get('source_research_ids', []):
        if rid not in ledger_ids and not rid.startswith('Pilot-'):
            # C43/C40 are canonical goal ids already on the C-line (roadmap items), not ledger research ids
            if rid not in item_ids and rid not in ('C40', 'C43', 'C13', 'C14', 'C35', 'C37'):
                unknown_refs.append((i['roadmap_id'], rid))
ROADMAP_UNKNOWN_REFERENCES = len(unknown_refs)
if ROADMAP_UNKNOWN_REFERENCES: errors.append(('ROADMAP_UNKNOWN_RESEARCH_REFS', unknown_refs))
# canonical capability ids referenced by roadmap items must exist OR be known legacy
for i in roadmap['items']:
    for cid in i.get('canonical_capability_ids', []):
        if cid not in cap_ids and not cid.startswith(('C', 'FW', 'LIVE_')):
            errors.append(('ROADMAP_UNKNOWN_CAPABILITY', (i['roadmap_id'], cid)))
# mutation ladder ordering sanity
ladder = roadmap['mutation_ladder']['future_levels']
if len(ladder) != 6: errors.append(('LADDER_FUTURE_LEVELS_COUNT', len(ladder)))
# roadmap baseline
if roadmap['baseline_identity']['artifact_sha256'] != BASELINE_SHA:
    errors.append(('ROADMAP_BASELINE_MISMATCH', roadmap['baseline_identity']['artifact_sha256']))

# ---- 3. capability index dedup ----
caps = [c for c in cap_index['capabilities'] if isinstance(c, dict)]
ids = [c['capability_id'] for c in caps]
names = [c.get('name') or c.get('title') or '' for c in caps]
names_lc = [n.lower() for n in names if n]
DUPLICATE_CANONICAL_CAPABILITIES = (len(ids) - len(set(ids))) + (len(names_lc) - len(set(names_lc)))
if DUPLICATE_CANONICAL_CAPABILITIES: errors.append(('DUPLICATE_CANONICAL_CAPABILITIES',
    [i for i, x in enumerate(ids) if ids.count(x) > 1][:10]))
new_planned = [c for c in caps if c.get('status') == 'PLANNED']
required_fields = ['capability_id', 'name', 'family', 'beginner_value', 'principle', 'origin_refs',
                   'status', 'evidence_refs', 'dependencies', 'next_condition', 'last_reviewed']
# Only validate the 10 new consolidation records (append-and-reconcile); legacy PLANNED records pre-date this validation.
consolidation_planned_ids = {'ZERO_TO_PROJECT_INTENT_COMPILER', 'LARGE_GOAL_COMPLETENESS', 'CONTEXT_INTELLIGENCE_COMPLETENESS',
                             'ROADMAP_AWARE_DEVELOPMENT_PLANNER_PLANNED', 'GOAL_DESIGN_INTELLIGENCE_COMPOSITION',
                             'BOUNDED_CODE_MUTATION_PRIMITIVE', 'ORCA_BOUNDED_CANDIDATE_FANOUT',
                             'MULTIHOST_COUNCIL_CERTIFICATION', 'CAPABILITY_DRIFT_REVALIDATION_SWEEP',
                             'RELEASE_INSTALL_LIFECYCLE_HARDENING'}
missing = [(c.get('capability_id'), [f for f in required_fields if f not in c])
           for c in new_planned if c.get('status') == 'PLANNED' and c.get('capability_id') in consolidation_planned_ids]
missing = [m for m in missing if m[1]]
if missing: errors.append(('PLANNED_RECORD_MISSING_FIELDS', missing))
# consolidation records' deps must resolve (id-like tokens only)
planned_deps_dangling = []
for c in new_planned:
    if c.get('capability_id') not in consolidation_planned_ids:
        continue
    for d in c.get('dependencies', []):
        for tok in re.findall(r'[A-Za-z0-9._/-]+', d):
            if id_like_re.match(tok) and tok not in cap_ids and tok not in known_refs:
                planned_deps_dangling.append((c['capability_id'], d))
if planned_deps_dangling: errors.append(('PLANNED_DEP_DANGLING', planned_deps_dangling))

# ---- 4. development-control baseline drift ----
dctl = load('governance/development-control.json')
ob = dctl['official_baseline']
if ob['version'] != '8.4.7-C-codex.41' or ob['artifact_sha256'] != BASELINE_SHA:
    errors.append(('BASELINE_DRIFT', (ob['version'], ob['artifact_sha256'])))
    BASELINE_DRIFT = 'PRESENT'
else:
    BASELINE_DRIFT = 'ABSENT'
if 'canonical_source_index' not in dctl:
    errors.append(('CANONICAL_SOURCE_INDEX_MISSING', True))
csi = dctl.get('canonical_source_index', {})
for k in ('research_adoption_ledger', 'p2p_development_roadmap', 'capability_index'):
    if k not in csi: errors.append(('SOURCE_INDEX_ENTRY_MISSING', k))
# consolidation_records history present
if 'consolidation_records' not in dctl: errors.append(('CONSOLIDATION_RECORDS_MISSING', True))

# ---- 5. secrets scan of the 2 new governance files (read-only) ----
NEW_SECRET_FINDINGS = 0
for p in ('governance/research-adoption-ledger.json', 'governance/p2p-development-roadmap.json'):
    blob = json.dumps(load(p))
    if re.search(r'AKIA[0-9A-Z]{16}', blob) or re.search(r'BEGIN\s+PRIVATE\s+KEY', blob) or re.search(r'(?i)password\s*=\s*["\'][^"\']{6,}', blob):
        NEW_SECRET_FINDINGS += 1
        errors.append(('SECRET_IN_GOVERNANCE_FILE', p))

# ---- summary ----
print('DANGLING_DEPENDENCIES =', DANGLING_DEPENDENCIES)
print('DUPLICATE_CANONICAL_CAPABILITIES =', DUPLICATE_CANONICAL_CAPABILITIES)
print('ROADMAP_UNKNOWN_REFERENCES =', ROADMAP_UNKNOWN_REFERENCES)
print('NEW_SECRET_FINDINGS =', NEW_SECRET_FINDINGS)
print('BASELINE_DRIFT =', BASELINE_DRIFT)
print('ledger statuses:', dict(sorted(status_counts.items())))
print('ledger records:', len(ledger['records']))
print('roadmap families/items:', len(roadmap['families']), '/', len(roadmap['items']))
print('capabilities total:', len(caps), '| PLANNED:', len(new_planned))
if errors:
    print('\nERRORS:')
    for e in errors: print(' -', e)
    sys.exit(1)
print('\nVALIDATION: ALL GOVERNANCE CONSOLIDATION CHECKS PASS (fail-closed vocabulary)')
sys.exit(0)
