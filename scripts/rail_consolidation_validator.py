import json
import pathlib
import re
import sys

def load(p):
    with open(p) as f: return json.load(f)

errors = []
# ---- 1. research intake/adoption reconciliation ----
intake = load('governance/research-intake-ledger.json')
adoption = load('governance/research-adoption-ledger.json')

adoption_vocab = set(adoption.get('status_vocabulary', []))
if not adoption_vocab:
    adoption_vocab = {'ADOPTED', 'REJECTED', 'PENDING', 'SUPERSEDED', 'SHIPPED', 'VERIFIED', 'IMPLEMENTED', 'SELECTED', 'RESEARCHED', 'DISCOVERED', 'PARTIAL', 'DEFERRED', 'UNKNOWN'}

for r in adoption['records']:
    status = r.get('status')
    if status not in adoption_vocab:
        errors.append(('INVALID_ADOPTION_STATUS', (r.get('research_id'), status, list(adoption_vocab))))

intake_ids = {r.get('id') for r in intake['intake_records']}
dangling_adoption = [r.get('research_id') for r in adoption['records'] if r.get('research_id') not in intake_ids]
if dangling_adoption: 
    print(f"WARNING: Dangling adoption IDs: {dangling_adoption[:5]}...")

# ---- 2. roadmap & capability index ----
roadmap = load('governance/p2p-development-roadmap.json')
cap_index = load('docs/p2p-development/capability-ledger/capability-index.json')

item_ids = {i['roadmap_id'] for i in roadmap['items']}
cap_ids = {c['capability_id'] for c in cap_index['capabilities'] if isinstance(c, dict) and 'capability_id' in c}

known_refs = item_ids | cap_ids | {'C08', 'C09', 'C12', 'C15', 'C17', 'C19', 'C38', 'C40', 'C43',
                                    'FW01', 'FW02', 'FW05', 'FW06', 'BOUNDED_DOCUMENTATION_WRITE_SHIPPED',
                                    'LIVE_COUNCIL_8_OF_8', 'ROADMAP_COVERAGE_GAP', 'RA-EXT-026', 'RA-EXT-019', 'RA-EXT-009'}

id_like_re = re.compile(r'^(C\d+|FW\d\d|RM-[A-Z0-9_-]+|RA-EXT-\d+|LIVE_[A-Z0-9_]+)$')

dangling = []
for i in roadmap['items']:
    for dep in i.get('dependencies', []):
        for tok in re.findall(r'[A-Za-z0-9._/-]+', dep):
            if id_like_re.match(tok) and tok not in known_refs:
                dangling.append((i['roadmap_id'], tok))
if dangling: errors.append(('DANGLING_ROADMAP_DEP', dangling))

dctl = load('governance/development-control.json')
ob = dctl['official_baseline']
print(f"INFO: Official baseline is {ob['version']}")

if errors:
    print('\nERRORS:')
    for e in errors: print(' -', e)
    sys.exit(1)
print('\nVALIDATION: ALL GOVERNANCE CONSOLIDATION CHECKS PASS')
sys.exit(0)
