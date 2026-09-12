"""Runtime-only Git metadata fixtures, real pinned providers, durable log evidence."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from shield.osv_acquire import acquire
from shield.dependency import assess
from shield.profile import evaluate
from shield.runner import assess as secret, resolve_target_ref


def emit(label, record):
    text = label + '\n```json\n' + json.dumps(record, indent=2) + '\n```\n'
    print(text, flush=True)
    annotation = json.dumps(record, separators=(',', ':')).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    if 'git_history_scan' not in label and 'worktree_scan' not in label:
        print('::notice title=' + label + '::' + annotation, flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write(text)


def main():
    reference = os.environ.get('EVIDENCE_REFERENCE', 'local-runtime-test')
    failures = []
    with tempfile.TemporaryDirectory(prefix='shield-base-') as tmp:
        root = Path(tmp)
        binary = root / 'missing-osv'
        try:
            binary, receipt = acquire(root / 'provider')
            emit('OSV_ACQUISITION=VERIFIED', receipt)
        except Exception as exc:
            emit('OSV_ACQUISITION=BLOCKED', {'reason': type(exc).__name__})
            failures.append('OSV_ACQUISITION_BLOCKED')
        for label, requirement, expected in [('pass', 'idna==3.15', 'PASS'),
                                                ('fail', 'Django==1.11.29', 'FAIL')]:
            repo = root / label
            repo.mkdir()
            (repo / 'requirements.txt').write_text(requirement + '\n')
            for args in [('init', '-q'), ('add', '.'), ('-c', 'user.name=Shield Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'metadata only')]:
                subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)
            records = []
            for scope in ('git_history_scan', 'worktree_scan'):
                e = secret(shield_dir=Path('shield').resolve(), control_id='SHIELD-SECRET-01', scan_mode=scope,
                           target=repo, executable=os.environ['GITLEAKS_EXECUTABLE'], provider_mapping=None,
                           timeout=120, reference=reference)
                emit(label + ':' + scope, e)
                records.append(e)
            d = assess(repo, binary, ['requirements.txt'], reference)
            emit(label + ':dependency', d)
            result = evaluate(records + [d], repo, resolve_target_ref(repo))
            emit(label + ':profile', result)
            if d['status'] != expected or result['PROFILE_REQUIREMENTS_STATUS'] != expected:
                failures.append(label + '_UNPROVEN')
            if label == 'fail':
                # Django SQL injection advisory affecting 1.11.29 (metadata only).
                expected_id = 'GHSA-8x94-hmjh-97hq'
                ids = [f['vulnerability_id'] for f in d['findings']]
                emit('EXPECTED_VULNERABILITY', {'id': expected_id, 'observed': expected_id in ids})
                if expected_id not in ids:
                    failures.append('EXPECTED_VULNERABILITY_NOT_OBSERVED')
            if label == 'pass':
                blocked = assess(repo, root / 'absent-provider', ['requirements.txt'], reference)
                emit('unavailable:dependency', blocked)
                for name, evidence in [('unavailable', records + [blocked]), ('missing', records)]:
                    result = evaluate(evidence, repo, resolve_target_ref(repo))
                    emit(name + ':profile', result)
                    if result['PROFILE_REQUIREMENTS_STATUS'] != 'BLOCKED':
                        failures.append(name + '_BLOCKED_UNPROVEN')
        emit('SLICE2_ACCEPTANCE', {'result': 'BLOCKED' if failures else 'PASS', 'unproven': failures,
                                   'SYSTEM_SECURITY_VERDICT': 'NOT_EVALUATED'})
    return 2 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
