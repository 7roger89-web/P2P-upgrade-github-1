"""Compose scoped evidence, never a system-security verdict.

Input evidence is trusted assessment output, not a signed attestation. Caller
must supply the expected target/ref from the assessment session, not from input.
Missing/invalid evidence takes precedence over FAIL; valid FAIL over BLOCKED.
"""
import argparse
import json
from pathlib import Path
import re
from datetime import datetime

PROFILE = json.loads((Path(__file__).parent / 'profiles/SHIELD-BASE.json').read_text())


def evaluate(records, target, target_ref):
    result = dict(profile_id=PROFILE['profile_id'], profile_version=PROFILE['profile_version'],
                  target=str(target), target_ref=target_ref, PROFILE_REQUIREMENTS_STATUS='BLOCKED',
                  SYSTEM_SECURITY_VERDICT='NOT_EVALUATED', reason='INVALID_OR_MISSING_REQUIRED_EVIDENCE')
    try:
        if not re.fullmatch('[0-9a-f]{40,64}', target_ref) or not isinstance(records, list):
            return result
        expected = {(cid, scope): rule['control_version'] for cid, rule in PROFILE['required_controls'].items()
                    for scope in rule['required_scopes']}
        seen, statuses = set(), []
        for e in records:
            key = (e['control_id'], e['scope'])
            if key not in expected or key in seen:
                return result
            seen.add(key)
            if (e['schema'] != 'p2p-shield-evidence/1' or e['control_version'] != expected[key]
                    or e['target'] != str(target) or e['target_ref'] != target_ref
                    or e['status'] not in ('PASS', 'FAIL', 'BLOCKED')):
                return result
            for field in ('provider', 'provider_version', 'provider_source', 'reason', 'artifact_or_reference'):
                if not isinstance(e[field], str) or not e[field]:
                    return result
            stamp = datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00'))
            if stamp.tzinfo is None or not isinstance(e['limitations'], list):
                return result
            if not isinstance(e['coverage'], list) or not e['coverage']:
                return result
            count = e['findings_count']
            if type(count) is not int or count < 0:
                return result
            if e['status'] != 'BLOCKED' and 'NONE_ESTABLISHED' in e['coverage']:
                return result
            if (e['status'] == 'PASS' and count != 0) or (e['status'] == 'FAIL' and count < 1):
                return result
            statuses.append(e['status'])
        if seen != set(expected):
            return result
        result['PROFILE_REQUIREMENTS_STATUS'] = ('FAIL' if 'FAIL' in statuses else
                                                  'BLOCKED' if 'BLOCKED' in statuses else 'PASS')
        result['reason'] = 'REQUIRED_SCOPED_EVIDENCE_COMPOSED_ONLY'
    except (KeyError, TypeError, ValueError, AttributeError):
        pass
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--target', required=True)
    p.add_argument('--target-ref', required=True)
    p.add_argument('evidence', nargs='+')
    a = p.parse_args()
    try:
        records = [json.loads(Path(f).read_text()) for f in a.evidence]
    except (OSError, ValueError):
        records = []
    result = evaluate(records, a.target, a.target_ref)
    print(json.dumps(result, indent=2))
    raise SystemExit({'PASS': 0, 'FAIL': 1, 'BLOCKED': 2}[result['PROFILE_REQUIREMENTS_STATUS']])
