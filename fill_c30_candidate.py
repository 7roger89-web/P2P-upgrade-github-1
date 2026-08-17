#!/usr/bin/env python3
"""Fill the C30 candidate record, ledger packaging record, and provenance
into governance/development-control.json and the capability ledger.
Idempotent: reruns are safe.
"""
import datetime
import json
import pathlib

ROOT = pathlib.Path('/home/ubuntu/p2p')
GOV = ROOT.joinpath('governance', 'development-control.json')
LEDGER = ROOT.joinpath(
    'docs/p2p-development/capability-ledger/capability-index.json')
LABEL = ("P2P-8.4.7-C-Codex-Edition-v24-"
         "c30-composable-execution-target-foundation-candidate-v1.zip")
SHA = ("94b09b596dab04a8bff5042c44753fed96881c89658d3db4e7be09fe034017b7")
NOW = datetime.datetime.now(
    datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def main() -> None:
    gov = json.loads(GOV.read_text(encoding='utf-8'))

    # 1. candidate record
    recs = gov.setdefault('candidate_records', [])
    if not any(r.get('candidate_id') == 'C30' for r in recs):
        recs.append({
            'candidate_id': 'C30',
            'development_goal': 'C30',
            'candidate_version': '8.4.7-C-codex.24',
            'candidate_label': LABEL,
            'candidate_sha256': SHA,
            'embedded_version': '8.4.7-C-codex.24',
            'based_on_official_version': '8.4.7-C-codex.19',
            'based_on_official_sha256':
                '3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8',
            'artifact_path': f'reports/candidates/{LABEL}',
            'promotion_status': 'UNPROMOTED',
            'lineage_status': 'verify PASS; full lineage verify pending owner '
                              'action (codex login / Manus connector)',
            'package_verify_evidence': 'status PASS, embedded '
                                       '8.4.7-C-codex.24, official baseline '
                                       '8.4.7-C-codex.19',
            'evidence_refs': [
                'scripts/package_release.py build on staged source: RC 0',
                'scripts/package_release.py verify on extracted candidate: '
                'status PASS, embedded 8.4.7-C-codex.24, official baseline '
                '8.4.7-C-codex.19',
                'docs/p2p-development/reports/P2P-C30-terminal-report.md',
            ],
        })
        print('governance + C30 candidate record (UNPROMOTED)')
    else:
        print('C30 candidate record already present')
    GOV.write_text(json.dumps(gov, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')

    # 2. Ledger packaging record
    d = json.loads(LEDGER.read_text(encoding='utf-8'))
    caps = d['capabilities']
    cap_id = 'C30_COMPOSABLE_EXECUTION_TARGET_PACKAGING'
    if not any(c.get('capability_id') == cap_id for c in caps):
        caps.append({
            'capability_id': cap_id,
            'title': 'C30 self-packaging: the composable ExecutionTarget '
                     'foundation (provider-neutral architecture, eligibility '
                     'evaluation, fingerprint/drift, backend registry) passed '
                     'its own candidate policy and produced the C30 candidate',
            'status': 'FOUNDATION_READY',
            'family': 'TRUTH_AND_GOVERNANCE',
            'origin_type': 'IMPLEMENTATION_GOAL',
            'beginner_value':
                'Execution is described as a composition of neutral parts '
                '(Harness + Provider + Model + Protocol + ToolSet + Workspace '
                '+ Environment + Auth + Permission + Freshness). No single AI '
                'vendor is hard-coded, so the beginner can swap providers '
                'without rewriting the project.',
            'principle': 'PROVIDER_NEUTRAL_COMPOSABLE_EXECUTION',
            'origin_refs': [
                'docs/p2p-development/reports/P2P-C30-terminal-report.md',
                f'reports/candidates/{LABEL}',
                'scripts/package_release.py build+verify PASS (embedded '
                '8.4.7-C-codex.24)',
            ],
            'dependencies': [
                'GOAL_CANDIDATE_RELEASE_PROMOTION_LIFECYCLE',
                'DETERMINISTIC_CANDIDATE_REQUIREMENT_POLICY',
                'GOAL_CLOSURE_INTEGRITY_CHECK',
            ],
            'freshness': 'from_governance_record',
            'implementation_refs': [
                'scripts/p2p_execution_target.py',
                'docs/p2p-development/research/'
                'execution-target-pattern-research.md',
                f'reports/candidates/{LABEL}',
            ],
        })
        print('ledger +', cap_id)
    else:
        print('ledger record already present')
    LEDGER.write_text(json.dumps(d, indent=1, ensure_ascii=False) + '\n',
                      encoding='utf-8')

    # 2b. current_development semantic sync for C30
    gov = json.loads(GOV.read_text(encoding='utf-8'))
    cd = gov.get('current_development', {})
    cd.update({
        'development_goal': 'C30',
        'status': 'CANDIDATE_UNPROMOTED',
        'source_version_status': 'CANDIDATE_UNPROMOTED',
        'candidate_id': 'C30',
        'candidate_label': LABEL,
        'candidate_sha256': SHA,
        'candidate_path': f'reports/candidates/{LABEL}',
        'owner_action_required':
            'C30 terminal PASS (provider-neutral execution foundation + '
            'durable research intake); candidates remain UNPROMOTED; C27 '
            'reopen needs one Owner action outside chat (codex login or '
            'Manus API connector); no goal auto-started.',
    })
    print('current_development synced to C30')

    # 3. Provenance entry
    prov = gov.setdefault('provenance', [])
    entry = {
        'change_id': 'C30-PACKAGING',
        'goal': 'C30',
        'timestamp': NOW,
        'description': 'C30 terminal PASS + governance/runtime/release changes; '
                       'deterministic candidate policy self-applied: C30 '
                       'candidate built (RC 0), verified (PASS, embedded '
                       '8.4.7-C-codex.24), SHA-256 recorded; UNPROMOTED.',
        'artifact_refs': [f'reports/candidates/{LABEL}'],
        'origin_refs': [
            'docs/p2p-development/reports/P2P-C30-terminal-report.md',
            'scripts/package_release.py build+verify',
        ],
    }
    if not any(p.get('change_id') == entry['change_id'] for p in prov):
        prov.append(entry)
        print('provenance + C30-PACKAGING')
    else:
        print('provenance entry already present')
    GOV.write_text(json.dumps(gov, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print('SHA:', SHA)


if __name__ == '__main__':
    main()
